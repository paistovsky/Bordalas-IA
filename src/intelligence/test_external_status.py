from src.analysis.bid_engine import (
    calculate_bid_recommendations,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.intelligence.external_status import (
    get_external_player_status,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    recommendations = (
        calculate_bid_recommendations(
            snapshot
        )
    )

    candidates = [
        player
        for player in recommendations
        if player["action"] == "PUJAR"
    ]

    # Limitamos la prueba a los 5 candidatos
    # más relevantes para ahorrar llamadas.
    candidates = candidates[:5]

    print()
    print("=" * 80)
    print(
        "        BORDALÁS IA - EXTERNAL STATUS"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        f"Jugadores a comprobar: "
        f"{len(candidates)}"
    )

    for index, player in enumerate(
        candidates,
        start=1,
    ):

        print()
        print("=" * 80)

        print(
            f"{index}. "
            f"{player['name'].upper()}"
        )

        print("=" * 80)

        print(
            f"Score Bordalás: "
            f"{player['final_score']}/100"
        )

        print(
            f"Puja sugerida:  "
            f"{player['suggested_bid']:,} €"
        )

        try:

            status = (
                get_external_player_status(
                    snapshot,
                    player,
                )
            )

        except Exception as error:

            print(
                "ERROR GENERAL: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            continue

        mapping = status["mapping"]

        print()
        print(
            f"External ID:    "
            f"{mapping.get('external_id')}"
        )

        print(
            f"Mapping:        "
            f"{mapping.get('confidence_level')}"
        )

        print(
            f"Estado externo: "
            f"{status['status']}"
        )

        print(
            f"Risk score:     "
            f"{status['risk_score']}/100"
        )

        # ----------------------------------------------
        # BAJAS
        # ----------------------------------------------

        sidelined = status.get(
            "sidelined"
        )

        if sidelined:

            print()
            print(
                "Historial bajas: "
                f"{sidelined.get('historical_count', 0)}"
            )

            print(
                "Baja activa:     "
                f"{'SÍ' if sidelined.get('active') else 'NO'}"
            )

            active_events = (
                sidelined.get(
                    "active_events",
                    [],
                )
            )

            for event in active_events:

                print(
                    "  - "
                    f"{event.get('type')} "
                    f"({event.get('start')} "
                    f"→ {event.get('end')})"
                )

        # ----------------------------------------------
        # TRASPASO
        # ----------------------------------------------

        transfers = status.get(
            "transfers"
        )

        if transfers:

            latest = transfers.get(
                "latest"
            )

            if latest:

                print()
                print(
                    "Último traspaso: "
                    f"{latest.get('date')}"
                )

                print(
                    "De:             "
                    f"{transfers.get('team_out')}"
                )

                print(
                    "A:              "
                    f"{transfers.get('team_in')}"
                )

                print(
                    "Reciente:        "
                    f"{'SÍ' if transfers.get('recent') else 'NO'}"
                )

        # ----------------------------------------------
        # ALERTAS
        # ----------------------------------------------

        if status["alerts"]:

            print()
            print("ALERTAS")

            for alert in status[
                "alerts"
            ]:

                print(
                    f"  - {alert}"
                )

        print()


if __name__ == "__main__":
    main()