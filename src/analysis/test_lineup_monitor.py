from src.analysis.lineup_monitor import (
    build_lineup_monitor_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.presentation.lineup_renderer import (
    print_lineup_field,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    monitor = (
        build_lineup_monitor_state(
            snapshot=
                snapshot,

            persist=False,
        )
    )

    lineup = (
        monitor[
            "lineup"
        ]
    )

    comparison = (
        monitor[
            "comparison"
        ]
    )

    print()
    print("=" * 100)
    print(
        "                      BORDALAS IA - LINEUP MONITOR"
    )
    print("=" * 100)

    print()

    print(
        f"Snapshot:          "
        f"{snapshot_file}"
    )

    print(
        f"Accion:            "
        f"{monitor['action']}"
    )

    print(
        f"Cambio:            "
        f"{'SI' if comparison['changed'] else 'NO'}"
    )

    print(
        f"Cambio relevante:  "
        f"{'SI' if comparison['significant_change'] else 'NO'}"
    )

    print(
        f"Guardar XI:        "
        f"{'SI' if monitor['should_save'] else 'NO'}"
    )

    print(
        f"Fuente externa:    "
        f"{monitor['external_lineup_source']}"
    )

    print()

    print(
        comparison[
            "reason"
        ]
    )

    if comparison.get(
        "added"
    ):

        print()
        print(
            "ENTRAN:"
        )

        for player in comparison[
            "added"
        ]:

            print(
                f"  - {player['name']}"
            )

    if comparison.get(
        "removed"
    ):

        print()
        print(
            "SALEN:"
        )

        for player in comparison[
            "removed"
        ]:

            print(
                f"  - {player['name']}"
            )

    if comparison.get(
        "state_changes"
    ):

        print()
        print(
            "CAMBIOS DE ESTADO:"
        )

        for change in comparison[
            "state_changes"
        ]:

            print(
                f"  - {change['name']}"
            )

    print_lineup_field(
        lineup
    )

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()