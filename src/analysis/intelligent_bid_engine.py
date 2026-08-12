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


MAX_EXTERNAL_CHECKS = 5

def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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
            player["action"] == "PUJAR"
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
