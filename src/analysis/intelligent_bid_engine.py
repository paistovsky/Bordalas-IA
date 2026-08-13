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

            external_status = (
                get_external_player_status(
                    snapshot,
                    player,
                )
            )

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

        results.append(
            {
                **player,

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
