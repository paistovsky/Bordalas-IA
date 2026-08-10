from copy import deepcopy

from src.analysis.roster_planner import (
    build_roster_plan,
)


POSITION_NAMES = {
    1: "Portero",
    2: "Defensa",
    3: "Centrocampista",
    4: "Delantero",
}


def get_player_position(
    player: dict,
) -> int | None:

    if "position" in player:
        return player["position"]

    return None


def simulate_transactions(
    snapshot: dict,
) -> dict:

    roster_plan = build_roster_plan(
        snapshot
    )

    current_team = deepcopy(
        snapshot["my_team"]
    )

    purchases = roster_plan[
        "selected_purchases"
    ]

    recommended_sales = roster_plan[
        "recommended_sales"
    ]

    optional_sales = roster_plan[
        "optional_sales"
    ]

    # --------------------------------------------------
    # PLANTILLA ORIGINAL
    # --------------------------------------------------

    original_count = len(
        current_team
    )

    original_ids = {
        player["id"]
        for player in current_team
    }

    # --------------------------------------------------
    # AÑADIR COMPRAS
    # --------------------------------------------------

    projected_team = list(
        current_team
    )

    for player in purchases:

        if player["id"] in original_ids:
            continue

        projected_player = {
            "id":
                player["id"],

            "name":
                player["name"],

            "position":
                player["position"],

            "altPositions":
                player.get(
                    "alt_positions",
                    [],
                ),

            "price":
                player.get(
                    "player_price",
                    player.get(
                        "market_price",
                        0,
                    ),
                ),

            "pointsLastSeason":
                player.get(
                    "points_last_season",
                    0,
                ),

            "priceIncrement":
                player.get(
                    "price_increment",
                    0,
                ),

            "status":
                player.get(
                    "status",
                    "ok",
                ),

            "teamID":
                player.get(
                    "team_id"
                ),
        }

        projected_team.append(
            projected_player
        )

    # --------------------------------------------------
    # VENTAS OBLIGATORIAS
    # --------------------------------------------------

    mandatory_sale_ids = {
        player["id"]
        for player in recommended_sales
    }

    projected_team = [
        player
        for player in projected_team
        if player["id"]
        not in mandatory_sale_ids
    ]

    # --------------------------------------------------
    # DISTRIBUCIÓN PROYECTADA
    # --------------------------------------------------

    position_counts = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
    }

    for player in projected_team:

        position = get_player_position(
            player
        )

        if position in position_counts:
            position_counts[
                position
            ] += 1

    # --------------------------------------------------
    # VENTAS OPCIONALES SEGURAS
    # --------------------------------------------------

    safe_optional_sales = []

    minimum_counts = {
        1: 2,
        2: 4,
        3: 4,
        4: 3,
    }

    simulated_counts = dict(
        position_counts
    )

    for player in optional_sales:

        position = player[
            "position"
        ]

        current_count = (
            simulated_counts.get(
                position,
                0,
            )
        )

        minimum = (
            minimum_counts.get(
                position,
                0,
            )
        )

        if (
            current_count - 1
            >= minimum
        ):

            safe_optional_sales.append(
                player
            )

            simulated_counts[
                position
            ] -= 1

    # --------------------------------------------------
    # SALDO
    # --------------------------------------------------

    optional_sale_income = sum(
        player["price"]
        for player
        in safe_optional_sales
    )

    projected_balance_without_optional = (
        roster_plan[
            "projected_balance"
        ]
    )

    projected_balance_with_optional = (
        projected_balance_without_optional
        + optional_sale_income
    )

    projected_count_before_optional = (
        len(projected_team)
    )

    projected_count_after_optional = (
        projected_count_before_optional
        - len(
            safe_optional_sales
        )
    )

    return {
        "original_count":
            original_count,

        "purchases":
            purchases,

        "mandatory_sales":
            recommended_sales,

        "safe_optional_sales":
            safe_optional_sales,

        "projected_team":
            projected_team,

        "position_counts":
            position_counts,

        "final_position_counts":
            simulated_counts,

        "projected_count_before_optional":
            projected_count_before_optional,

        "projected_count_after_optional":
            projected_count_after_optional,

        "projected_balance_without_optional":
            projected_balance_without_optional,

        "optional_sale_income":
            optional_sale_income,

        "projected_balance_with_optional":
            projected_balance_with_optional,
    }