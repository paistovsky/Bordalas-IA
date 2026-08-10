from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.roster_planner import (
    build_roster_plan,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    plan = build_roster_plan(
        snapshot
    )

    print()
    print("=" * 80)
    print(
        "          BORDALÁS IA - ROSTER PLANNER"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        f"Saldo actual:          "
        f"{plan['balance']:>12,} €"
    )

    print(
        f"Reserva deseada:       "
        f"{plan['cash_reserve']:>12,} €"
    )

    print()
    print("COMPRAS PROPUESTAS")
    print("-" * 80)

    for player in (
        plan[
            "selected_purchases"
        ]
    ):

        print(
            f"{player['name']:<22}"
            f"{player['suggested_bid']:>12,} €"
            f"   Score "
            f"{player['intelligent_score']:>3}/100"
        )

    print()
    print(
        f"Coste compras:         "
        f"{plan['purchase_cost']:>12,} €"
    )

    print()
    print(
        f"Déficit de liquidez:   "
        f"{plan['liquidity_shortfall']:>12,} €"
    )

    print()
    print("VENTAS NECESARIAS")
    print("-" * 80)

    if not plan[
        "recommended_sales"
    ]:
        print(
            "Ninguna venta necesaria "
            "para financiar el plan."
        )

    else:

        for player in (
            plan[
                "recommended_sales"
            ]
        ):

            print(
                f"{player['name']:<22}"
                f"{player['price']:>12,} €"
                f"   Sale score "
                f"{player['sale_score']:>3}/100"
            )

    print()
    print("VENTAS OPCIONALES")
    print("-" * 80)

    if not plan[
        "optional_sales"
    ]:
        print(
            "Ninguna venta opcional "
            "prioritaria."
        )

    else:

        for player in (
            plan[
                "optional_sales"
            ][:5]
        ):

            print(
                f"{player['name']:<22}"
                f"{player['price']:>12,} €"
                f"   Sale score "
                f"{player['sale_score']:>3}/100"
            )

            for reason in (
                player["reasons"]
            ):
                print(
                    f"   - {reason}"
                )

    print()
    print(
        f"Saldo proyectado:      "
        f"{plan['projected_balance']:>12,} €"
    )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()