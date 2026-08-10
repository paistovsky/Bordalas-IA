from src.analysis.franchise_funding_engine import (
    build_franchise_funding_plan,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
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

    plan = (
        build_franchise_funding_plan(
            snapshot
        )
    )

    print()
    print("=" * 100)
    print(
        "             BORDALÁS IA - FRANCHISE FUNDING / DEBT PLAN"
    )
    print("=" * 100)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    if not plan[
        "active"
    ]:

        print()
        print(
            plan[
                "reason"
            ]
        )
        return

    target = (
        plan[
            "target"
        ]
    )

    print()
    print("OBJETIVO")
    print("-" * 100)
    print()

    print(
        f"Jugador:                 "
        f"{target['name']}"
    )

    print(
        f"Franchise:               "
        f"{target['franchise_score']}/100"
    )

    print()
    print(
        f"Puja objetivo:            "
        f"{money(plan['target_bid'])}"
    )

    print(
        f"Saldo actual:             "
        f"{money(plan['current_balance'])}"
    )

    print(
        f"Saldo proyectado:         "
        f"{money(plan['projected_balance'])}"
    )

    print(
        f"DEUDA TEMPORAL:           "
        f"{money(plan['projected_debt'])}"
    )

    print(
        f"Capital a desbloquear:    "
        f"{money(plan['required_unlock'])}"
    )

    print(
        f"Horas hasta deadline:     "
        f"{plan['hours_to_deadline']}"
    )

    print()
    print("=" * 100)
    print("ACTIVOS LIQUIDABLES")
    print("=" * 100)

    for player in plan[
        "liquidatable_candidates"
    ]:

        print()
        print(
            f"{player['name']:<22}"
            f"{money(player['estimated_liquidity']):>15}"
            f"   Sale "
            f"{player['sale_score']:.0f}"
        )

    liquidity = (
        plan[
            "liquidity_plan"
        ]
    )

    print()
    print("=" * 100)
    print("PLAN PARA SANEAR DEUDA")
    print("=" * 100)
    print()

    if not liquidity[
        "players"
    ]:

        print(
            "No es necesario liquidar activos."
        )

    else:

        for player in liquidity[
            "players"
        ]:

            print(
                f"- "
                f"{player['name']:<22}"
                f"{money(player['estimated_liquidity']):>15}"
            )

        print()
        print(
            f"Liquidez estimada:       "
            f"{money(liquidity['estimated_liquidity'])}"
        )

        print(
            f"Deuda a cubrir:          "
            f"{money(plan['projected_debt'])}"
        )

        print(
            f"Exceso:                  "
            f"{money(liquidity['excess'])}"
        )

        print(
            f"Cobertura suficiente:    "
            f"{'SÍ' if liquidity['covered'] else 'NO'}"
        )

    print()
    print("=" * 100)
    print("DECISIÓN")
    print("=" * 100)
    print()

    print(
        plan[
            "recommendation"
        ]
    )

    print()
    print(
        plan[
            "reason"
        ]
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()