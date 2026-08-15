from src.analysis.lineup_engine import (
    build_lineup,
)

from src.analysis.price_humanizer import (
    humanize_bid_price,
)

from src.analysis.transaction_planner import (
    simulate_transactions,
)


def build_action_plan(
    snapshot: dict,
) -> dict:

    transaction_plan = (
        simulate_transactions(
            snapshot
        )
    )

    lineup = build_lineup(
        snapshot
    )

    # ==================================================
    # PUJAS
    # ==================================================

    bids = []

    for player in transaction_plan[
        "purchases"
    ]:

        strategic_amount = int(
            player[
                "suggested_bid"
            ]
        )

        market_price = int(
            player.get(
                "market_price",
                player.get(
                    "player_price",
                    0,
                ),
            )
            or 0
        )

        human_amount = (
            humanize_bid_price(
                player_id=
                    player["id"],

                strategic_max=
                    strategic_amount,

                market_price=
                    market_price,

                market_until=
                    player.get(
                        "market_until"
                    ),
            )
        )

        bids.append(
            {
                "type":
                    "BID",

                "player_id":
                    player["id"],

                "player_name":
                    player["name"],

                "amount":
                    human_amount,

                "strategic_amount":
                    strategic_amount,

                "market_price":
                    market_price,

                "score":
                    player[
                        "intelligent_score"
                    ],

                "external_risk":
                    player.get(
                        "external_risk",
                        0,
                    ),
            }
        )

    # ==================================================
    # VENTAS NECESARIAS
    # ==================================================

    mandatory_sales = []

    for player in transaction_plan[
        "mandatory_sales"
    ]:

        mandatory_sales.append(
            {
                "type":
                    "SELL",

                "priority":
                    "MANDATORY",

                "player_id":
                    player["id"],

                "player_name":
                    player["name"],

                "estimated_value":
                    player["price"],

                "sale_score":
                    player["sale_score"],
            }
        )

    # ==================================================
    # VENTAS OPCIONALES
    # ==================================================

    optional_sales = []

    for player in transaction_plan[
        "safe_optional_sales"
    ]:

        optional_sales.append(
            {
                "type":
                    "SELL",

                "priority":
                    "OPTIONAL",

                "player_id":
                    player["id"],

                "player_name":
                    player["name"],

                "estimated_value":
                    player["price"],

                "sale_score":
                    player["sale_score"],

                "reasons":
                    player.get(
                        "reasons",
                        [],
                    ),
            }
        )

    # ==================================================
    # ALINEACIÓN
    # ==================================================

    lineup_actions = []

    for player in lineup[
        "selected"
    ]:

        lineup_actions.append(
            {
                "type":
                    "LINEUP",

                "player_id":
                    player["id"],

                "player_name":
                    player["name"],

                "position":
                    player[
                        "lineup_position"
                    ],

                # El campo se renombro a counts_for_round en
                # prepare_players. Con corchetes esto reventaba;
                # hoy no salta porque nadie importa bordalas.py,
                # que es el unico llamante de build_action_plan.
                "has_game":
                    player.get(
                        "counts_for_round",
                        True,
                    ),

                "lineup_score":
                    player[
                        "lineup_score"
                    ],
            }
        )

    current_balance = (
        snapshot["market"]
        ["status"]
        ["balance"]
    )

    bid_total = sum(
        bid["amount"]
        for bid in bids
    )

    return {
        "mode":
            "DRY_RUN",

        "bids":
            bids,

        "mandatory_sales":
            mandatory_sales,

        "optional_sales":
            optional_sales,

        "lineup":
            lineup_actions,

        "economy": {
            "current_balance":
                current_balance,

            "purchase_cost":
                bid_total,

            # No contamos ventas futuras.
            "projected_balance_if_all_bids_win":
                current_balance
                - bid_total,
        },

        "summary": {
            "bid_count":
                len(bids),

            "mandatory_sale_count":
                len(
                    mandatory_sales
                ),

            "optional_sale_count":
                len(
                    optional_sales
                ),

            "lineup_count":
                len(
                    lineup_actions
                ),
        },
    }