from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.premium_opportunity_engine import (
    build_premium_opportunity_plan,
)


def money(value: int) -> str:
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

    plan = (
        build_premium_opportunity_plan(
            snapshot
        )
    )

    print()
    print("=" * 85)
    print(
        "       BORDALÁS IA - PREMIUM OPPORTUNITY ENGINE"
    )
    print("=" * 85)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    if not plan["active"]:

        print()
        print(
            "No existe una oportunidad "
            "premium activa."
        )

        print()
        print("=" * 85)

        return

    player = plan[
        "target"
    ]

    print()
    print(
        "OBJETIVO PREMIUM DETECTADO"
    )

    print()

    print(
        f"Jugador:          "
        f"{player['name']}"
    )

    print(
        f"Strategic score:  "
        f"{player['strategic_score']}/100"
    )

    print(
        f"Nivel oportunidad:"
        f" {plan['opportunity_level']}"
    )

    print()

    print(
        f"Valor mercado:    "
        f"{money(plan['market_price'])}"
    )

    print(
        f"Caja objetivo:    "
        f"{money(plan['required_cash'])}"
    )

    print()

    print(
        f"Saldo:            "
        f"{money(plan['balance'])}"
    )

    print(
        f"Pujas activas:    "
        f"{money(plan['active_commitment'])}"
    )

    print(
        f"Caja libre:       "
        f"{money(plan['free_cash'])}"
    )

    print()

    print(
        f"Capital a liberar:"
        f" {money(plan['recover_needed'])}"
    )

    print()
    print("-" * 85)

    decision = plan[
        "decision"
    ]

    print()
    print(
        f"DECISIÓN: {decision}"
    )

    print()

    if (
        decision
        == "ATACAR_PREMIUM"
    ):

        print(
            "🔥 Hay caja suficiente."
        )

        print(
            "Bordalás IA recomienda "
            "competir por el premium."
        )

    elif (
        decision
        == "REESTRUCTURAR_PUJAS"
    ):

        print(
            "⚠ La oportunidad premium "
            "justifica revisar las "
            "pujas secundarias."
        )

        print()

        print(
            "Objetivo:"
        )

        print(
            "liberar capital de "
            "operaciones menos importantes "
            "antes de renunciar al premium."
        )

    elif (
        decision
        == "NECESITA_VENTAS"
    ):

        print(
            "💰 Ni cancelando todas las "
            "pujas actuales habría caja "
            "suficiente."
        )

        print()

        print(
            "Bordalás IA debe estudiar "
            "ventas adicionales antes "
            "de atacar."
        )

    print()
    print("=" * 85)


if __name__ == "__main__":
    main()