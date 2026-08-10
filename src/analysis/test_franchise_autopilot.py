from src.actions.franchise_autopilot import (
    build_franchise_autopilot_state,
    print_autopilot_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)


def main() -> None:

    print()
    print("=" * 90)
    print(
        "          BORDALÁS IA - FRANCHISE AUTOPILOT TEST"
    )
    print("=" * 90)

    # ==================================================
    # REFRESH OBLIGATORIO
    # ==================================================
    #
    # El Autopilot nunca debe decidir utilizando
    # un snapshot anterior a una operación real.
    #
    # Por ejemplo:
    #
    # snapshot
    # -> pujar Yamal
    # -> ese snapshot NO contiene todavía la puja
    #
    # Por eso refrescamos siempre antes de evaluar
    # el estado autónomo.
    # ==================================================

    print()
    print(
        "Actualizando Biwenger..."
    )
    print()

    collect_league_snapshot()

    # ==================================================
    # CARGAR SNAPSHOT NUEVO
    # ==================================================

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()
    print(
        "Calculando estado autónomo..."
    )

    # ==================================================
    # AUTOPILOT
    # ==================================================

    state = (
        build_franchise_autopilot_state(
            snapshot
        )
    )

    print_autopilot_state(
        state
    )

    # ==================================================
    # DRY RUN
    # ==================================================

    print()
    print(
        "MODO DRY-RUN"
    )

    print(
        "No se ha modificado Biwenger."
    )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()