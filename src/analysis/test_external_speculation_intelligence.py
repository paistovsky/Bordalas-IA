from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)

from src.intelligence.speculation_intelligence import (
    build_external_speculation_board,
)


def print_result(
    item: dict,
) -> None:

    signal = (
        item[
            "signal"
        ]
    )

    print()
    print(
        f"{item['name']}"
    )

    print(
        f"   Datos externos: "
        f"{'SÍ' if item['available'] else 'NO'}"
    )

    print(
        f"   Estado:         "
        f"{signal['status']}"
    )

    print(
        f"   Clasificación:  "
        f"{signal['classification']}"
    )

    print(
        f"   Risk score:     "
        f"{signal['risk_score']}/100"
    )

    print(
        f"   Ajuste spec:    "
        f"{signal['score']:+.1f}"
    )

    print(
        f"   Confianza:      "
        f"{signal['confidence']}%"
    )

    print(
        f"   Bloqueo auto:   "
        f"{'SÍ' if signal['automatic_block'] else 'NO'}"
    )

    alerts = (
        signal.get(
            "alerts",
            []
        )
        or []
    )

    if alerts:

        print(
            "   Alertas:"
        )

        for alert in alerts:

            print(
                f"      - {alert}"
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

    print()
    print("=" * 105)
    print(
        "              BORDALÁS IA - EXTERNAL SPECULATION INTELLIGENCE V1"
    )
    print("=" * 105)

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()
    print(
        "Construyendo shortlist interna..."
    )

    speculation_board = (
        build_speculation_board(
            snapshot
        )
    )

    print()
    print(
        "Consultando inteligencia externa..."
    )

    print(
        "Solo se consultarán jugadores relevantes."
    )

    external = (
        build_external_speculation_board(
            snapshot=
                snapshot,

            speculation_board=
                speculation_board,
        )
    )

    print()
    print("=" * 105)
    print(
        "RESUMEN"
    )
    print("=" * 105)

    print()

    print(
        f"Jugadores analizados:      "
        f"{external['shortlist_count']}"
    )

    print(
        f"Bloqueados:                 "
        f"{external['blocked_count']}"
    )

    print(
        f"Advertencias:               "
        f"{external['warning_count']}"
    )

    print(
        f"Sin riesgo externo:         "
        f"{external['clean_count']}"
    )

    print(
        f"Sin datos externos fiables: "
        f"{external['unavailable_count']}"
    )

    print()
    print("=" * 105)
    print(
        "RESULTADOS"
    )
    print("=" * 105)

    for item in external[
        "results"
    ]:

        print_result(
            item
        )

    print()
    print("=" * 105)
    print(
        "BLOQUEOS AUTOMÁTICOS"
    )
    print("=" * 105)

    if not external[
        "blocked"
    ]:

        print()
        print(
            "Ninguno."
        )

    for item in external[
        "blocked"
    ]:

        print_result(
            item
        )

    print()
    print("=" * 105)
    print(
        "NOTA"
    )
    print("=" * 105)

    print()

    print(
        "External Intelligence v1 utiliza actualmente "
        "API-Football para bajas/sanciones y traspasos."
    )

    print()

    print(
        "La ausencia de riesgo externo NO genera "
        "un bonus especulativo positivo."
    )

    print(
        "Solo las señales negativas pueden reducir "
        "o bloquear una operación."
    )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()