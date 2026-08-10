from datetime import datetime

from src.analysis.deadline_engine import (
    build_deadline_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def format_timestamp(
    timestamp: int | None,
) -> str:

    if timestamp is None:
        return "DESCONOCIDO"

    return datetime.fromtimestamp(
        timestamp
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    state = (
        build_deadline_state(
            snapshot
        )
    )

    calendar = (
        state[
            "calendar"
        ]
    )

    print()
    print("=" * 90)
    print(
        "              BORDALÁS IA - DEADLINE ENGINE"
    )
    print("=" * 90)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print("=" * 90)
    print("JORNADA")
    print("=" * 90)

    print()
    print(
        f"Round ID:                  "
        f"{calendar['current_round_id']}"
    )

    print(
        f"Partidos detectados:       "
        f"{calendar['round_game_count']}"
    )

    print(
        f"Primer partido:            "
        f"{format_timestamp(calendar['first_game'])}"
    )

    print(
        f"Deadline alineación:       "
        f"{format_timestamp(calendar['lineup_deadline'])}"
    )

    print(
        f"Tiempo hasta primer partido:"
        f" {calendar['time_to_first_game']}"
    )

    print(
        f"Tiempo hasta bloqueo XI:   "
        f"{calendar['time_to_lineup_lock']}"
    )

    print()
    print("=" * 90)
    print("RIESGO")
    print("=" * 90)

    print()
    print(
        f"Jugadores con partido:     "
        f"{state['playable_count']}/11"
    )

    print(
        f"Huecos actuales:           "
        f"{state['missing_playable']}"
    )

    print(
        f"Riesgo temporal:           "
        f"{state['time_risk']}"
    )

    print(
        f"Riesgo de XI:              "
        f"{state['lineup_risk']}"
    )

    print(
        f"Presión completar XI:      "
        f"{state['lineup_pressure_score']}/100"
    )

    print(
        f"Libertad estrategia premium:"
        f" +{state['premium_freedom_bonus']}"
    )

    print(
        f"Safety mode:               "
        f"{'SÍ' if state['hard_safety_mode'] else 'NO'}"
    )

    print()
    print("=" * 90)
    print("MERCADOS FUTUROS")
    print("=" * 90)

    future = (
        state[
            "future_market_opportunities"
        ]
    )

    print()
    print(
        f"Ciclos aproximados antes XI:"
        f" {future['cycles']}"
    )

    print(
        f"Oportunidades restantes:    "
        f"{future['level']}"
    )

    print()
    print("=" * 90)
    print("CIERRES DE MERCADO MÁS PRÓXIMOS")
    print("=" * 90)

    deadlines = (
        calendar[
            "market_deadlines"
        ]
    )

    if not deadlines:

        print()
        print(
            "No se encontraron deadlines."
        )

    for item in deadlines[:10]:

        seller = (
            item[
                "seller"
            ]
        )

        if seller is None:
            origin = "MÁQUINA"

        elif isinstance(
            seller,
            dict,
        ):
            origin = (
                seller.get(
                    "name"
                )
                or
                f"MANAGER {seller.get('id')}"
            )

        else:
            origin = str(
                seller
            )

        print()
        print(
            f"{item['player_name']}"
        )

        print(
            f"   Precio:   "
            f"{item['price']:,} €"
        )

        print(
            f"   Origen:   "
            f"{origin}"
        )

        print(
            f"   Cierra:   "
            f"{format_timestamp(item['until'])}"
        )

        print(
            f"   Queda:    "
            f"{item['time_remaining']}"
        )

    anomalies = (
        calendar[
            "round_anomalies"
        ]
    )

    print()
    print("=" * 90)
    print("JORNADAS ESPECIALES / APLAZADAS")
    print("=" * 90)

    if not anomalies:

        print()
        print(
            "No detectadas."
        )

    else:

        for anomaly in anomalies:

            print()
            print(
                f"{anomaly['name']} "
                f"(ID {anomaly['id']})"
            )

            print(
                f"   Estado: "
                f"{anomaly['status']}"
            )

            print(
                f"   Parte:  "
                f"{anomaly['part']}"
            )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()