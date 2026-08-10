from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.strategic_budget_engine import (
    build_strategic_budget,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    budget = (
        build_strategic_budget(
            snapshot
        )
    )

    print()
    print("=" * 85)
    print(
        "            BORDALÁS IA - STRATEGIC BUDGET ENGINE"
    )
    print("=" * 85)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        f"Modo estratégico:       "
        f"{budget['mode']}"
    )

    print(
        f"Jugadores con partido:  "
        f"{budget['playable_count']}/11"
    )

    print()

    print(
        f"Saldo actual:            "
        f"{budget['balance']:>12,} €"
    )

    print(
        f"Puja máxima Biwenger:    "
        f"{budget['maximum_bid']:>12,} €"
    )

    print(
        f"Comprometido en pujas:   "
        f"{budget['active_bid_commitment']:>12,} €"
    )

    print()
    print(
        f"Reserva emergencia:      "
        f"{budget['emergency_reserve']:>12,} €"
    )

    print(
        f"Reserva premium:         "
        f"{budget['premium_reserve']:>12,} €"
    )

    print(
        f"Reserva total:           "
        f"{budget['total_reserve']:>12,} €"
    )

    print()
    print(
        f"Presupuesto táctico:      "
        f"{budget['tactical_budget']:>12,} €"
    )

    print(
        f"Libre tras pujas activas: "
        f"{budget['free_after_active_bids']:>12,} €"
    )

    print(
        f"NUEVO GASTO SEGURO:      "
        f"{budget['safe_new_spending']:>12,} €"
    )

    print()
    print("=" * 85)
    print("OBJETIVOS PREMIUM")
    print("=" * 85)

    targets = (
        budget[
            "premium_targets"
        ]
    )

    if not targets:

        print()
        print(
            "No hay objetivos premium "
            "identificados."
        )

    for index, player in enumerate(
        targets[:10],
        start=1,
    ):

        print()
        print(
            f"{index}. "
            f"{player['name']}"
        )

        print(
            f"   Strategic: "
            f"{player['strategic_score']}/100"
        )

        print(
            f"   Valor:     "
            f"{player['price']:,} €"
        )

        print(
            f"   Estado:    "
            f"{player['ownership_state']}"
        )

    print()
    print("=" * 85)
    print("PREMIUM DISPONIBLES AHORA")
    print("=" * 85)

    available = (
        budget[
            "premium_in_market"
        ]
    )

    if not available:

        print()
        print(
            "Ninguno."
        )

    else:

        for player in available:

            print()
            print(
                f"⭐ {player['name']}"
            )

            print(
                f"   Valor:      "
                f"{player['price']:,} €"
            )

            print(
                f"   Strategic:  "
                f"{player['strategic_score']}/100"
            )

            print()
            print(
                "   ⚠ OPORTUNIDAD PREMIUM ACTIVA"
            )

            print(
                "   Bordalás IA debe valorar "
                "reestructurar gasto."
            )

    print()
    print("=" * 85)


if __name__ == "__main__":
    main()