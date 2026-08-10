from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.strategic_decision_gate import (
    build_strategic_decision,
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

    result = (
        build_strategic_decision(
            snapshot
        )
    )

    deadline = (
        result[
            "deadline"
        ]
    )

    calendar = (
        deadline[
            "calendar"
        ]
    )

    print()
    print("=" * 90)
    print(
        "          BORDALÁS IA - TEMPORAL STRATEGIC GATE"
    )
    print("=" * 90)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        f"FASE:              "
        f"{result['phase']}"
    )

    print(
        f"XI con partido:     "
        f"{deadline['playable_count']}/11"
    )

    print(
        f"Huecos:             "
        f"{deadline['missing_playable']}"
    )

    print(
        f"Deadline XI:        "
        f"{calendar['time_to_lineup_lock']}"
    )

    print(
        f"Riesgo XI:          "
        f"{deadline['lineup_risk']}"
    )

    future = (
        deadline[
            "future_market_opportunities"
        ]
    )

    print(
        f"Mercados restantes: "
        f"{future['cycles']} "
        f"({future['level']})"
    )

    print()

    if result[
        "premium_active"
    ]:

        player = (
            result[
                "premium_target"
            ]
        )

        print(
            "OBJETIVO FRANCHISE"
        )

        print(
            "-" * 90
        )

        print()
        print(
            f"Jugador:           "
            f"{player['name']}"
        )

        print(
            f"Strategic:         "
            f"{result['strategic_score']}/100"
        )

        print(
            f"Franchise:         "
            f"{result['franchise_score']}/100"
        )

        print(
            f"Clasificación:     "
            f"{result['franchise_classification']}"
        )

        print(
            f"Valor:             "
            f"{money(player['price'])}"
        )

        print()

        print(
            f"Validación:        "
            f"{result['premium_validation']}"
        )

        print()

        print(
            f"Ventaja inicial:   "
            f"{result['difference']:+.2f}"
        )

        adjustments = (
            result[
                "adjustments"
            ]
        )

        print(
            f"Tiempo/calendario: "
            f"{adjustments['time']:+.2f}"
        )

        print(
            f"Mercados futuros:  "
            f"{adjustments['future_markets']:+.2f}"
        )

        print(
            f"Presión ventas:    "
            f"{adjustments['sale_pressure']:+.2f}"
        )

        print(
            f"Bonus Franchise:   "
            f"{adjustments['franchise']:+.2f}"
        )

        print()

        print(
            f"VENTA NECESARIA:   "
            f"{money(result['minimum_sale_needed'])}"
        )

        print(
            f"Presión de venta:  "
            f"{result['sale_pressure_percent']:.1f}%"
        )

        print()

        print(
            f"VENTAJA AJUSTADA:  "
            f"{result['effective_difference']:+.2f}"
        )

    else:

        print(
            "No existe un objetivo Franchise "
            "accionable."
        )

        print()

        print(
            f"Validación: "
            f"{result.get('premium_validation')}"
        )

    print()
    print("=" * 90)
    print(
        "DECISIÓN"
    )
    print("=" * 90)

    print()
    print(
        result[
            "decision"
        ]
    )

    print()
    print(
        result[
            "reason"
        ]
    )

    if deadline[
        "hard_safety_mode"
    ]:

        print()
        print(
            "HARD SAFETY MODE"
        )

        print(
            "Bordalás IA no permitirá estrategias "
            "que comprometan XI o solvencia."
        )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()