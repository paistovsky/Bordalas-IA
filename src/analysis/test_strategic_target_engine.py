from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.strategic_target_engine import (
    POSITION_NAMES,
    build_strategic_target_board,
)


def print_player(
    index: int,
    player: dict,
) -> None:

    print(
        f"{index:>2}. "
        f"{player['name']:<22}"
    )

    print(
        f"    Estado: "
        f"{player['ownership_state']}"
    )

    print(
        f"    "
        f"{POSITION_NAMES[player['position']]:<16}"
        f"Valor: "
        f"{player['price']:>11,} €   "
        f"Pts 25/26: "
        f"{player['points_last_season']:>3}"
    )

    print(
        f"    Strategic: "
        f"{player['strategic_score']:>5.1f}/100   "
        f"{player['strategic_classification']}"
    )

    print(
        f"    Tactical:  "
        f"{player['tactical_score']:>5.1f}/100   "
        f"{player['tactical_classification']}"
    )

    print(
        f"    Puntos/M€: "
        f"{player['points_per_million']:>6.1f}   "
        f"Tendencia: "
        f"{player['price_increment']:>+9,} €"
    )

    print(
        "    "
        f"Quality "
        f"{player['absolute_quality_score']:>2}"
        f" | "
        f"Efficiency "
        f"{player['strategic_efficiency_score']:>2}"
        f" | "
        f"Premium "
        f"{player['premium_asset_score']:>2}"
        f" | "
        f"Momentum "
        f"{player['momentum_score']:>+3}"
    )

    print(
        "    "
        f"Need "
        f"{player['squad_need_bonus']:>2}"
        f" | "
        f"Market "
        f"{player['market_bonus']:>2}"
        f" | "
        f"Affordable "
        f"{player['affordability_bonus']:>2}"
    )

    if not player[
        "availability"
    ][
        "available"
    ]:

        print(
            "    "
            f"⚠ "
            f"{player['availability']['label']}: "
            f"{player['availability']['status_info']}"
        )

    print(
        "-" * 90
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    strategic_targets = (
        build_strategic_target_board(
            snapshot,
            limit=25,
            sort_by="strategic",
        )
    )

    tactical_targets = (
        build_strategic_target_board(
            snapshot,
            limit=25,
            sort_by="tactical",
        )
    )

    print()
    print("=" * 90)
    print(
        "          BORDALÁS IA - STRATEGIC TARGET BOARD"
    )
    print("=" * 90)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print("=" * 90)
    print(
        "TOP 25 - ESTRATEGIA DE TEMPORADA"
    )
    print("=" * 90)
    print()

    for index, player in enumerate(
        strategic_targets,
        start=1,
    ):
        print_player(
            index,
            player,
        )

    print()
    print("=" * 90)
    print(
        "TOP 25 - PRIORIDAD TÁCTICA ACTUAL"
    )
    print("=" * 90)
    print()

    for index, player in enumerate(
        tactical_targets,
        start=1,
    ):
        print_player(
            index,
            player,
        )


if __name__ == "__main__":
    main()