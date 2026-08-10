from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


def money(
    value: int,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    board = (
        build_strategic_target_board(
            snapshot,
            limit=25,
            sort_by="franchise",
        )
    )

    print()
    print("=" * 100)

    print(
        "                   BORDALÁS IA - FRANCHISE ENGINE"
    )

    print("=" * 100)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        "TOP 25 JUGADORES FRANQUICIA"
    )

    print()

    for index, player in enumerate(
        board,
        start=1,
    ):

        print(
            f"{index:>2}. "
            f"{player['name']:<22}"
            f"Franchise "
            f"{player['franchise_score']:>5.1f}/100   "
            f"{player['franchise_classification']:<14}"
        )

        print(
            "    "
            f"Strategic: "
            f"{player['strategic_score']:>5.1f}/100   "
            f"Tactical: "
            f"{player['tactical_score']:>5.1f}/100"
        )

        print(
            "    "
            f"Valor: "
            f"{money(player['price']):>14}   "
            f"Puntos 25/26: "
            f"{player['points_last_season']}"
        )

        print(
            "    "
            f"Pts component: "
            f"{player['franchise_points_score']:<3} | "
            f"Market: "
            f"{player['franchise_market_score']:<3} | "
            f"Confirm: "
            f"{player['franchise_confirmation']:<3} | "
            f"Penalty: "
            f"{player['franchise_production_penalty']:+3}"
        )

        print(
            "    "
            f"Estado: "
            f"{player['ownership_state']}   "
            f"Puede reestructurar: "
            f"{'SÍ' if player['can_trigger_restructure'] else 'NO'}"
        )

        print(
            "-" * 100
        )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()