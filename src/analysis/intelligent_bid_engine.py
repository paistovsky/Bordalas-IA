from src.analysis.bid_engine import (
    calculate_bid_recommendations,
)

from src.intelligence.external_status import (
    get_external_player_status,
)


MAX_EXTERNAL_CHECKS = 5


def calculate_intelligent_bids(
    snapshot: dict,
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
        # ACCIÓN FINAL
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