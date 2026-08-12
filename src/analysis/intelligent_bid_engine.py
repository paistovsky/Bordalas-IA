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

    external_checks = 0

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

        seller_user_id = (
            extract_seller_user_id(
                player
            )
        )

        competitive_observer = None

        if (
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
