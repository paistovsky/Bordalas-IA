from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
    evaluate_projected_debt,
)


def money(
    value: int,
) -> str:

    return f"{value:,.0f} €"


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    state = (
        build_solvency_state(
            snapshot
        )
    )

    deadline = (
        state[
            "deadline"
        ]
    )

    calendar = (
        deadline[
            "calendar"
        ]
    )

    print()
    print("=" * 100)
    print(
        "                    BORDALÁS IA - SOLVENCY ENGINE"
    )
    print("=" * 100)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print("=" * 100)
    print(
        "SOLVENCIA ACTUAL"
    )
    print("=" * 100)

    print()
    print(
        f"Saldo actual:           "
        f"{money(state['balance'])}"
    )

    print(
        f"Saldo negativo:         "
        f"{'SÍ' if state['is_negative'] else 'NO'}"
    )

    print(
        f"Riesgo de solvencia:    "
        f"{state['risk']}"
    )

    print()
    print(
        f"Deadline XI:            "
        f"{calendar['time_to_lineup_lock']}"
    )

    print(
        f"Riesgo XI:              "
        f"{deadline['lineup_risk']}"
    )

    print()
    print("=" * 100)
    print(
        "LIQUIDEZ POTENCIAL"
    )
    print("=" * 100)

    liquidatable = (
        state[
            "liquidatable_assets"
        ]
    )

    print()
    print(
        f"Activos liquidables:    "
        f"{money(liquidatable['total'])}"
    )

    for player in liquidatable[
        "players"
    ]:

        print(
            f"   "
            f"{player['name']:<22}"
            f"{money(player['value']):>15}"
            f"   Sale "
            f"{player['sale_score']:.0f}"
        )

    incoming = (
        state[
            "incoming_offer_liquidity"
        ]
    )

    print()
    print(
        f"Ofertas recibidas:      "
        f"{money(incoming['total'])}"
    )

    print(
        f"Liquidez recuperable:   "
        f"{money(state['recoverable_cash'])}"
    )

    print()
    print("=" * 100)
    print(
        "DEUDA TEMPORAL ACTUAL"
    )
    print("=" * 100)

    temporary = (
        state[
            "temporary_debt"
        ]
    )

    print()
    print(
        f"Permitida:              "
        f"{'SÍ' if temporary['allowed'] else 'NO'}"
    )

    print()
    print(
        temporary[
            "reason"
        ]
    )

    print()
    print("=" * 100)
    print(
        "HARD SAFETY"
    )
    print("=" * 100)

    safety = (
        state[
            "hard_safety"
        ]
    )

    print()
    print(
        f"Activo:                 "
        f"{'SÍ' if safety['active'] else 'NO'}"
    )

    if safety[
        "reasons"
    ]:

        print()

        for reason in safety[
            "reasons"
        ]:

            print(
                f"- {reason}"
            )

    # ==================================================
    # TEST DE DEUDA HIPOTÉTICA
    # ==================================================
    #
    # La cifra es solo para comprobar que el motor
    # sabe evaluar deuda futura de manera independiente.
    # ==================================================

    hypothetical_debt = (
        1_597_600
    )

    projected = (
        evaluate_projected_debt(
            debt=
                hypothetical_debt,

            recoverable_cash=
                state[
                    "recoverable_cash"
                ],

            seconds_to_deadline=
                state[
                    "seconds_to_deadline"
                ],

            lineup_risk=
                state[
                    "lineup_risk"
                ],
        )
    )

    print()
    print("=" * 100)
    print(
        "SIMULACIÓN DE DEUDA"
    )
    print("=" * 100)

    print()
    print(
        f"Deuda hipotética:       "
        f"{money(hypothetical_debt)}"
    )

    print(
        f"Cubierta:               "
        f"{'SÍ' if projected['covered'] else 'NO'}"
    )

    print(
        f"Ratio cobertura:        "
        f"{projected['coverage_ratio']}"
    )

    print(
        f"Permitida:              "
        f"{'SÍ' if projected['allowed'] else 'NO'}"
    )

    print()
    print(
        projected[
            "reason"
        ]
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()