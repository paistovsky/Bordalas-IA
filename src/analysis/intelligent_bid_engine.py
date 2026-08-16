from src.analysis.competitive_transaction_engine import (
    evaluate_purchase_from_rival,
    extract_seller_user_id,
)

from src.analysis.bid_engine import (
    calculate_bid_recommendations,
)

from src.intelligence.external_status import (
    get_external_player_status,
)

from src.analysis.exact_price_policy import (
    apply_ratio_exact,
)

from src.analysis.bid_exposure_engine import (
    get_own_user_id,
)

from src.analysis.acquisition_valuation import (
    build_valuation_context,
    value_candidate,
)

from src.analysis.historical_price_lookup import (
    build_historical_price_lookup,
)

from src.analysis.rival_bid_model import (
    build_bid_model,
    optimal_bid,
)


MAX_EXTERNAL_CHECKS = 5


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default




def build_market_bid_authority(
    snapshot: dict,
    player: dict,
    legacy_intel: dict | None = None,
    *,
    trading_score: float | None = None,
    seller_lookup: dict[int, dict] | None = None,
) -> dict:
    """
    V10.4E - BID AUTHORITY + EXACT EURO PRICING.

    El Intelligent Bid legacy era deliberadamente conservador: si la logica
    base no proponia puja, el observer competitivo nunca creaba una compra
    desde cero. Eso es correcto para LIVE legacy, pero dejaba a Market Trader
    sin precio precisamente en oportunidades especulativas nuevas.

    Esta funcion NO cambia calculate_intelligent_bids() ni activa escrituras.
    Crea una autoridad de precio para Market Trader usando importes exactos al euro:

    - parte del precio fresco de mercado;
    - no redondea a múltiplos de 10.000 ni añade ruido cosmético;
    - reutiliza cualquier puja Intelligent Bid legacy si existe;
    - puede crear una puja desde cero si legacy_suggested == 0;
    - prima conviccion, momentum y venta por rival de forma moderada;
    - respeta maximumBid de Biwenger;
    - nunca permite comprar un jugador propio;
    - NO decide el maximo economico final: Market Trader aplica despues el
      techo de ROI/max_rational_bid.
    """
    legacy_intel = legacy_intel or {}

    player_id = _safe_int(player.get("id"))
    price = max(
        _safe_int(player.get("price")),
        _safe_int(player.get("market_price")),
        _safe_int(player.get("player_price")),
    )

    own_ids = {
        _safe_int(item.get("id"))
        for item in (snapshot.get("my_team", []) or [])
        if _safe_int(item.get("id")) > 0
    }

    if player_id > 0 and player_id in own_ids:
        return {
            "allowed": False,
            "source": "BLOCK_OWN_PLAYER",
            "authority_bid": 0,
            "legacy_bid": _safe_int(legacy_intel.get("suggested_bid")),
            "synthetic_bid": 0,
            "premium_percent": 0.0,
            "confidence": "BLOCKED",
            "seller_user_id": None,
            "reason": "Jugador ya perteneciente a Pepe: Bid Authority no puede crear una compra.",
        }

    speculation = _safe_float(player.get("speculation_score"))
    increment_pct = max(_safe_float(player.get("price_increment_percent")), 0.0)
    score = _safe_float(trading_score)
    if score <= 0:
        score = _safe_float(legacy_intel.get("intelligent_score"), 50.0)

    # Conviccion V10: primas deliberadamente pequenas. El margen economico
    # lo protege despues max_rational_bid, no esta funcion.
    conviction_premium = 0.0
    if score >= 88:
        conviction_premium = 0.030
    elif score >= 80:
        conviction_premium = 0.020
    elif score >= 72:
        conviction_premium = 0.010

    speculation_premium = 0.0
    if speculation >= 90:
        speculation_premium = 0.010
    elif speculation >= 84:
        speculation_premium = 0.005

    momentum_premium = 0.0
    if increment_pct >= 5.0:
        momentum_premium = 0.010
    elif increment_pct > 0:
        momentum_premium = 0.005

    if seller_lookup is None:
        seller_lookup = build_market_seller_lookup(snapshot)

    sale_info = seller_lookup.get(player_id, {}) or {}
    seller_user_id = (
        sale_info.get("seller_user_id")
        or legacy_intel.get("seller_user_id")
    )

    # Si vende un rival real, dejamos un margen minimo adicional para no
    # comportarnos como si fuese una oferta Computer. No asumimos una guerra
    # de pujas ni inventamos rivales interesados: solo +0.5%.
    rival_listing_premium = 0.005 if seller_user_id is not None else 0.0

    premium = min(
        conviction_premium
        + speculation_premium
        + momentum_premium
        + rival_listing_premium,
        0.060,
    )

    synthetic_bid = apply_ratio_exact(price, premium) if price > 0 else 0
    legacy_bid = _safe_int(legacy_intel.get("suggested_bid"))

    if legacy_bid > 0:
        authority_bid = max(price, legacy_bid, synthetic_bid)
        source = "HYBRID_LEGACY_PLUS_V10"
    else:
        authority_bid = max(price, synthetic_bid)
        source = "V10_CREATED_FROM_ZERO"

    maximum_bid = _safe_int(
        (snapshot.get("market", {}) or {}).get("status", {}).get("maximumBid")
    )
    if maximum_bid > 0:
        authority_bid = min(authority_bid, maximum_bid)

    if score >= 84 and speculation >= 84:
        confidence = "HIGH"
    elif score >= 72 and speculation >= 78:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    if legacy_bid <= 0:
        reason = (
            "Intelligent Bid legacy no proponia puja; V10.3.1 crea precio desde cero "
            "con conviccion/momentum. Market Trader aplicara despues el maximo racional ROI."
        )
    else:
        reason = (
            "Puja legacy disponible; V10.3.1 combina Intelligent Bid con conviccion de trading. "
            "Market Trader mantiene la ultima palabra mediante maximo racional ROI."
        )

    return {
        "allowed": authority_bid > 0,
        "source": source,
        "authority_bid": authority_bid,
        "legacy_bid": legacy_bid,
        "synthetic_bid": synthetic_bid,
        "premium_percent": round(premium * 100.0, 2),
        "confidence": confidence,
        "seller_user_id": seller_user_id,
        "maximum_bid": maximum_bid or None,
        "reason": reason,
        "components": {
            "conviction_percent": round(conviction_premium * 100.0, 2),
            "speculation_percent": round(speculation_premium * 100.0, 2),
            "momentum_percent": round(momentum_premium * 100.0, 2),
            "rival_listing_percent": round(rival_listing_premium * 100.0, 2),
        },
    }


def _extract_user_from_sale(sale: dict) -> dict | None:
    """
    Biwenger puede cambiar la forma exacta del propietario.
    Buscamos las estructuras comunes sin asumir una sola.
    """

    object_candidates = [
        sale.get("seller"),
        sale.get("user"),
        sale.get("owner"),
        sale.get("from"),
        (
            sale.get(
                "player",
                {},
            )
            or {}
        ).get("owner"),
        (
            sale.get(
                "player",
                {},
            )
            or {}
        ).get("user"),
    ]

    for candidate in object_candidates:

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        user_id = _safe_int(
            candidate.get(
                "id"
            )
        )

        if user_id > 0:

            return {
                "id":
                    user_id,

                "name":
                    candidate.get(
                        "name"
                    ),
            }

    direct_id_keys = (
        "sellerUserID",
        "seller_user_id",
        "userID",
        "ownerUserID",
    )

    for key in direct_id_keys:

        user_id = _safe_int(
            sale.get(
                key
            )
        )

        if user_id > 0:

            return {
                "id":
                    user_id,

                "name":
                    None,
            }

    return None


def build_market_seller_lookup(
    snapshot: dict,
) -> dict[int, dict]:

    result = {}

    sales = (
        snapshot.get(
            "market",
            {},
        ).get(
            "sales",
            [],
        )
        or []
    )

    for sale in sales:

        player = (
            sale.get(
                "player",
                {},
            )
            or {}
        )

        player_id = _safe_int(
            player.get(
                "id"
            )
        )

        if player_id <= 0:
            continue

        seller = (
            _extract_user_from_sale(
                sale
            )
        )

        result[
            player_id
        ] = {
            "seller":
                seller,

            "seller_user_id":
                (
                    seller.get(
                        "id"
                    )
                    if seller
                    else None
                ),

            "seller_name":
                (
                    seller.get(
                        "name"
                    )
                    if seller
                    else None
                ),

            "raw_sale":
                sale,
        }

    return result


def calculate_intelligent_bids(
    snapshot: dict,
    rival_intelligence: dict | None = None,
    *,
    allow_external_checks: bool = True,
) -> list[dict]:

    base_results = (
        calculate_bid_recommendations(
            snapshot
        )
    )

    results = []

    seller_lookup = (
        build_market_seller_lookup(
            snapshot
        )
    )

    external_checks = 0

    own_player_ids = {
        _safe_int(item.get("id"))
        for item in (snapshot.get("my_team", []) or [])
        if _safe_int(item.get("id")) > 0
    }

    own_user_id = get_own_user_id(snapshot)

    # Contexto de valoracion y retrato de la competencia. Se
    # calculan una vez por ciclo, no una vez por jugador.
    valuation_context = build_valuation_context(snapshot)

    catalog_by_id = {
        _safe_int(item.get("id")): item
        for item in (
            (
                (snapshot.get("catalog") or {}).get("data") or {}
            ).get("players") or {}
        ).values()
        if isinstance(item, dict)
    }

    bid_model = build_bid_model(
        rival_intelligence,
        # Precio DE AQUEL MOMENTO, no el de hoy: los precios
        # suben y dividir entre el actual daba primas por debajo
        # de 1,0, que es imposible en una subasta.
        price_lookup=build_historical_price_lookup(),
        own_user_id=own_user_id,
    )

    for player in base_results:

        base_score = player[
            "final_score"
        ]

        external_risk = 0
        external_status = None

        # Solo gastamos inteligencia externa
        # en jugadores a los que realmente
        # estamos considerando pujar.
        if (
            allow_external_checks
            and player["action"] == "PUJAR"
            and external_checks
            < MAX_EXTERNAL_CHECKS
        ):

            # El estado externo es informacion de apoyo, no una
            # decision. Si falla, la puja debe evaluarse igual.
            #
            # El 16/08/2026 esto tumbo el ciclo entero: la API
            # rechazaba la busqueda de Sorloth por la o barrada y
            # la excepcion subia hasta arriba. El fallo era
            # anterior, pero estaba dormido porque el techo de
            # puja roto hacia que ningun jugador llegase a
            # action == PUJAR y esta rama no se ejecutaba nunca.
            #
            # Arreglar el techo lo desperto. La causa esta
            # corregida en normalize_name; esto es la red por si
            # la API vuelve a cambiar de opinion sobre lo que
            # acepta.
            try:
                external_status = (
                    get_external_player_status(
                        snapshot,
                        player,
                    )
                )

            except Exception as error:
                external_status = {
                    "external_available": False,
                    "error": (
                        f"{type(error).__name__}: {error}"
                    ),
                }

            external_checks += 1

            # Solo penalizamos si los datos externos
            # son suficientemente fiables.
            if (
                external_status.get(
                    "external_available",
                    False,
                )
            ):

                external_risk = (
                    external_status.get(
                        "risk_score",
                        0,
                    )
                )

        intelligent_score = max(
            base_score
            - external_risk,
            0,
        )

        # --------------------------------------------------
        # ACCIÃ“N FINAL
        # --------------------------------------------------

        if external_risk >= 60:

            action = "NO PUJAR"

            suggested_bid = 0

        elif external_risk >= 30:

            action = "REVISAR"

            suggested_bid = (
                player[
                    "suggested_bid"
                ]
            )

        else:

            action = (
                player["action"]
            )

            suggested_bid = (
                player[
                    "suggested_bid"
                ]
            )

        # --------------------------------------------------
        # COMPETITIVE TRANSACTION ENGINE V1 - OBSERVER
        # --------------------------------------------------
        #
        # No modifica action ni suggested_bid actuales.
        # Solo evalua el efecto bilateral cuando conocemos
        # que el vendedor es otro manager.
        # --------------------------------------------------

        market_sale = (
            seller_lookup.get(
                _safe_int(
                    player.get(
                        "id"
                    )
                ),
                {},
            )
            or {}
        )

        seller_user_id = (
            market_sale.get(
                "seller_user_id"
            )
            or
            extract_seller_user_id(
                player
            )
        )

        seller_name = (
            market_sale.get(
                "seller_name"
            )
        )

        player_id = _safe_int(
            player.get("id")
        )

        own_player = (
            player_id in own_player_ids
        )

        competitive_observer = None

        # V1.3.1 - SAFETY GATES.
        # Nunca comprar un jugador propio.
        # Nunca convertir automaticamente una puja legacy de 0 EUR
        # en una nueva compra competitiva.
        if own_player:

            competitive_observer = {
                "observer_only": True,
                "decision": "SKIP_OWN_PLAYER",
                "strategic_max_price": 0,
                "our_counter_amount": None,
                "reasons": [
                    "Jugador ya perteneciente a Pepe: prohibido generar una puja de compra."
                ],
            }

        elif suggested_bid <= 0:

            competitive_observer = {
                "observer_only": True,
                "decision": "SKIP_LEGACY_NO_BID",
                "strategic_max_price": 0,
                "our_counter_amount": None,
                "reasons": [
                    "La logica base no propone puja; el observer competitivo no crea una compra desde cero."
                ],
            }

        elif (
            seller_user_id is not None
            and
            rival_intelligence is not None
        ):

            competitive_observer = (
                evaluate_purchase_from_rival(
                    proposed_price=
                        suggested_bid,

                    market_value=
                        int(
                            player.get(
                                "market_price",
                                player.get(
                                    "player_price",
                                    0,
                                ),
                            )
                            or 0
                        ),

                    rival_user_id=
                        seller_user_id,

                    rival_intelligence=
                        rival_intelligence,

                    player_score=
                        float(
                            player.get(
                                "final_score",
                                0,
                            )
                            or 0
                        ),

                    lineup_need_score=
                        float(
                            player.get(
                                "lineup_need_score",
                                50,
                            )
                            or 50
                        ),

                    speculation_score=
                        float(
                            player.get(
                                "speculation_score",
                                50,
                            )
                            or 50
                        ),
                )
            )

        # --------------------------------------------------
        # VALOR Y PUJA - MERCADO DEL COMPUTER
        # --------------------------------------------------
        #
        # El observer competitivo de arriba solo entra cuando el
        # vendedor es otro manager. Los jugadores del Computer no
        # tienen vendedor, y son justo los que se disputan en
        # subasta a ciegas contra toda la liga: el 16/08/2026 eran
        # 20 de los 53 del mercado.
        #
        # Para esos, la puja salia de una escalera fija de primas
        # sobre el precio -+8/6/4/2 %- que ni miraba lo que el
        # jugador nos aportaba ni si alguien podia disputarnoslo.
        #
        # Ahora son dos preguntas separadas y las dos con datos:
        #
        #   1. Cuanto vale para nosotros. Si mejora el once, lo
        #      que cuestan en el mercado los puntos que suma sobre
        #      el peor de los nuestros en su posicion, mas lo que
        #      recuperemos vendiendo a ese. Si solo es para
        #      revender, la reventa estimada menos el margen.
        #
        #   2. Cuanto pujar. El importe que maximiza
        #      P(ganar) x (valor - puja), con la probabilidad
        #      calibrada con lo que los rivales han hecho de
        #      verdad, no con lo que podrian hacer.
        #
        # Si no vale nada, no se puja. Antes se pujaba igual,
        # porque la escalera siempre daba un numero.

        valuation = None
        bid_plan = None
        promoted_by_value = False

        # Se valora TODO lo que publica el Computer, no solo lo que
        # la escalera de scores marco como pujable.
        #
        # Ese filtro -final_score >= 55- descartaba justo los
        # chollos. El 16/08/2026 dejaba fuera a Copete, 150.000 EUR
        # y 56 puntos la temporada pasada, que es la mejor
        # operacion del mercado: sustituye a Yeray, suma 32 puntos
        # y libera 1,96 M. Su score era 40.
        #
        # El score es una senal mas, no una puerta. La puerta ahora
        # es el valor: si no vale, no se puja, y si vale, se puja
        # aunque el score sea bajo.
        es_mercado_computer = bool(
            market_sale
            and seller_user_id is None
            and not own_player
        )

        if (
            es_mercado_computer
            and rival_intelligence is not None
        ):

            # Del catalogo, no de la recomendacion: aqui estan
            # precio, posicion, puntos del ano pasado, equipo y
            # tendencia. La recomendacion no trae todo eso.
            ficha = catalog_by_id.get(player_id) or {}

            estado = str(ficha.get("status") or "ok").lower()

            legacy_suggested_bid = suggested_bid

            if estado not in {"ok", "unknown"}:

                # Lesionado, sancionado o descartado: no se ficha
                # por barato que salga.
                suggested_bid = 0
                action = "NO PUJAR"

                valuation = {
                    "value": 0,
                    "decision": "NO_DISPONIBLE",
                    "intent": None,
                    "reason": (
                        f"Estado del jugador: {estado}."
                    ),
                }

            elif external_risk >= 60:

                suggested_bid = 0
                action = "NO PUJAR"

                valuation = {
                    "value": 0,
                    "decision": "RIESGO_EXTERNO",
                    "intent": None,
                    "reason": (
                        f"Riesgo externo {external_risk}."
                    ),
                }

            else:

                valuation = value_candidate(
                    ficha or player,
                    valuation_context,
                )

                if valuation.get("value", 0) > 0:

                    bid_plan = optimal_bid(
                        price=_safe_int(
                            ficha.get("price")
                            or player.get("market_price")
                            or player.get("player_price")
                        ),
                        value=valuation["value"],
                        model=bid_model,

                        # La via por la que lo queremos cambia lo
                        # que se le exige: la especulacion tiene
                        # que rendir sobre el capital que
                        # inmoviliza, la mejora del once se paga
                        # en puntos.
                        intent=valuation.get("intent"),
                    )

                    if bid_plan.get("decision") == "BID":
                        suggested_bid = bid_plan["bid"]
                        promoted_by_value = action != "PUJAR"
                        action = "PUJAR"

                    else:
                        suggested_bid = 0
                        action = "NO PUJAR"

                else:
                    suggested_bid = 0
                    action = "NO PUJAR"

        else:
            legacy_suggested_bid = suggested_bid

        results.append(
            {
                **player,

                "valuation":
                    valuation,

                "bid_plan":
                    bid_plan,

                "our_value":
                    (
                        valuation.get("value")
                        if valuation
                        else None
                    ),

                "intent":
                    (
                        valuation.get("intent")
                        if valuation
                        else None
                    ),

                "win_probability":
                    (
                        bid_plan.get("win_probability")
                        if bid_plan
                        else None
                    ),

                "legacy_suggested_bid":
                    legacy_suggested_bid,

                "promoted_by_value":
                    promoted_by_value,

                "base_score":
                    base_score,

                "external_risk":
                    external_risk,

                "intelligent_score":
                    intelligent_score,

                "external_status":
                    external_status,

                "seller_user_id":
                    seller_user_id,

                "seller_name":
                    seller_name,

                "own_player":
                    own_player,

                "market_sale":
                    market_sale,

                "competitive_observer":
                    competitive_observer,

                "competitive_observer_decision":
                    (
                        competitive_observer.get(
                            "decision"
                        )
                        if competitive_observer
                        else None
                    ),

                "competitive_strategic_max_price":
                    (
                        competitive_observer.get(
                            "strategic_max_price"
                        )
                        if competitive_observer
                        else None
                    ),

                "suggested_bid":
                    suggested_bid,

                "action":
                    action,
            }
        )

    results.sort(
        key=lambda player:
            player[
                "intelligent_score"
            ],
        reverse=True,
    )

    return results
