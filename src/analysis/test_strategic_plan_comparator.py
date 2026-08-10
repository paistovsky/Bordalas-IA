from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.strategic_plan_comparator import (
    compare_strategic_plans,
)


def money(
    value: int,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def print_plan(
    plan: dict,
) -> None:

    print()
    print(
        plan["name"]
    )
    print("-" * 85)

    for player in plan.get(
        "players",
        [],
    ):

        print(
            f"{player['name']:<22}"
            f"Strategic "
            f"{player['strategic_score']:>5.1f}   "
            f"Tactical "
            f"{player['tactical_score']:>5.1f}"
        )

    print()

    print(
        f"Coste estimado:       "
        f"{money(plan['cost'])}"
    )

    print(
        f"Score estratégico:    "
        f"{plan['strategic_score']}"
    )

    print(
        f"Score táctico:         "
        f"{plan['tactical_score']}"
    )

    print(
        f"SCORE COMBINADO:       "
        f"{plan['combined_score']}"
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    comparison = (
        compare_strategic_plans(
            snapshot
        )
    )

    print()
    print("=" * 85)
    print(
        "        BORDALÁS IA - STRATEGIC PLAN COMPARATOR"
    )
    print("=" * 85)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print_plan(
        comparison[
            "current"
        ]
    )

    premium = comparison[
        "premium"
    ]

    if premium.get(
        "available"
    ):

        print_plan(
            premium
        )

        print()
        print(
            f"Venta mínima necesaria: "
            f"{money(premium['minimum_sale_needed'])}"
        )

    print()
    print("=" * 85)
    print("DECISIÓN")
    print("=" * 85)

    print()
    print(
        comparison[
            "recommendation"
        ]
    )

    print()
    print(
        comparison[
            "reason"
        ]
    )

    if "difference" in comparison:

        difference = (
            comparison[
                "difference"
            ]
        )

        print()
        print(
            f"Diferencia Premium - Actual: "
            f"{difference:+.2f}"
        )

    print()
    print("=" * 85)


if __name__ == "__main__":
    main()