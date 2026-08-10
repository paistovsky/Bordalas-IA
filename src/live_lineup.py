import argparse
import sys

from src.analysis.lineup_monitor import (
    build_lineup_monitor_state,
    save_lineup_monitor_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)

from src.presentation.lineup_renderer import (
    print_lineup_field,
)


# ============================================================
# FORMACION
# ============================================================


def detect_formation(
    lineup: dict,
) -> str:

    counts = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
    }

    for player in lineup.get(
        "selected",
        [],
    ):

        position = int(
            player.get(
                "lineup_position",
                0,
            )
            or 0
        )

        if position in counts:

            counts[
                position
            ] += 1

    return (
        f"{counts[2]}-"
        f"{counts[3]}-"
        f"{counts[4]}"
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    parser = (
        argparse.ArgumentParser(
            description=(
                "Bordalas IA - "
                "Guardar alineacion"
            )
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Envia el XI aunque Lineup Monitor "
            "no detecte cambio relevante."
        ),
    )

    args = (
        parser.parse_args()
    )

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

    selected = (
        lineup.get(
            "selected",
            []
        )
    )

    print()
    print("=" * 100)
    print(
        "                      BORDALAS IA - LIVE LINEUP"
    )
    print("=" * 100)

    print()

    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print(
        f"Monitor:  "
        f"{monitor['action']}"
    )

    print()

    print_lineup_field(
        lineup
    )

    if len(
        selected
    ) != 11:

        print(
            "BLOQUEADO:"
        )

        print(
            "La alineacion no contiene "
            "exactamente 11 jugadores."
        )

        sys.exit(
            1
        )

    formation = (
        detect_formation(
            lineup
        )
    )

    player_ids = [
        int(
            player[
                "id"
            ]
        )

        for player
        in selected
    ]

    should_send = (
        monitor[
            "should_save"
        ]
        or args.force
    )

    # ========================================================
    # SIN CAMBIOS
    # ========================================================

    if (
        not should_send
        and
        not monitor[
            "comparison"
        ][
            "baseline"
        ]
    ):

        print()
        print(
            "NO HAY CAMBIOS RELEVANTES."
        )

        print(
            "No es necesario enviar "
            "una nueva alineacion."
        )

        save_lineup_monitor_state(
            lineup
        )

        return

    # ========================================================
    # BASELINE
    # ========================================================

    if monitor[
        "comparison"
    ][
        "baseline"
    ]:

        print()
        print(
            "No existe linea base previa."
        )

        print(
            "Se utilizara este XI como "
            "estado inicial del monitor."
        )

        if not args.force:

            save_lineup_monitor_state(
                lineup
            )

            print()
            print(
                "BASELINE GUARDADA."
            )

            print(
                "No se ha enviado ninguna "
                "alineacion a Biwenger."
            )

            return

    # ========================================================
    # DRY RUN
    # ========================================================

    if not args.live:

        print()
        print(
            "MODO DRY-RUN"
        )

        print(
            "La alineacion NO sera enviada."
        )

        print()

        print(
            f"Formacion: "
            f"{formation}"
        )

        print(
            f"Player IDs: "
            f"{player_ids}"
        )

        return

    # ========================================================
    # LIVE
    # ========================================================

    print()
    print(
        "*** MODO LIVE ***"
    )

    print(
        "Se enviara una nueva alineacion "
        "a Biwenger."
    )

    writer = (
        BiwengerWriteClient()
    )

    result = (
        writer.save_lineup(
            player_ids=
                player_ids,

            formation=
                formation,

            reserve_ids=
                [],

            execute=
                True,
        )
    )

    print()

    print(
        f"HTTP:   "
        f"{result.get('http_status')}"
    )

    print(
        f"Exito:  "
        f"{'SI' if result.get('success') else 'NO'}"
    )

    if not result.get(
        "success"
    ):

        print()
        print(
            "La alineacion NO se ha "
            "confirmado."
        )

        sys.exit(
            1
        )

    save_lineup_monitor_state(
        lineup
    )

    print()
    print(
        "ALINEACION ENVIADA CORRECTAMENTE."
    )

    print(
        "Estado del monitor actualizado."
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()