from src.analysis.bid_restructuring_engine import (
    build_bid_restructuring_plan,
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
        build_bid_restructuring_plan(
            snapshot
        )
    )

    print()
    print("=" * 100)
    print(
        "           BORDALÁS IA - BID RESTRUCTURING / TEMPORARY DEBT"
    )
    print("=" * 100)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    if not plan.get(
        "active"
    ):

        print()
        print(
            plan.get(
                "reason",
                "No existe plan activo.",
            )
        )

        print()
        print("=" * 100)

        return

    target = (
        plan[
            "target"
        ]
    )

    economy = (
        plan[
            "economy"
        ]
    )

    # ==================================================
    # OBJETIVO
    # ==================================================

    print()
    print("=" * 100)
    print(
        "OBJETIVO FRANCHISE"
    )
    print("=" * 100)

    print()

    print(
        f"Jugador:                 "
        f"{target['name']}"
    )

    print(
        f"Franchise:               "
        f"{target['franchise_score']}/100"
    )

    print(
        f"Strategic:               "
        f"{target['strategic_score']}/100"
    )

    print(
        f"Valor mercado:           "
        f"{money(target['price'])}"
    )

    # ==================================================
    # CAPACIDAD DE COMPRA
    # ==================================================

    print()
    print("=" * 100)
    print(
        "CAPACIDAD DE COMPRA"
    )
    print("=" * 100)

    print()

    print(
        f"Saldo actual:             "
        f"{money(economy['balance'])}"
    )

    print(
        f"Puja máxima actual:       "
        f"{money(economy['maximum_bid'])}"
    )

    print(
        f"Pujas comprometidas:      "
        f"{money(economy['active_commitment'])}"
    )

    print(
        f"Capacidad total observada:"
        f" {money(economy['observed_total_bid_capacity'])}"
    )

    print()

    print(
        f"Puja objetivo Franchise:  "
        f"{money(economy['target_bid'])}"
    )

    print(
        f"CAPITAL A DESBLOQUEAR:    "
        f"{money(economy['required_unlock'])}"
    )

    # ==================================================
    # DEUDA PROYECTADA
    # ==================================================

    print()
    print("=" * 100)
    print(
        "DEUDA TEMPORAL SI GANAMOS"
    )
    print("=" * 100)

    print()

    print(
        f"Saldo proyectado:         "
        f"{money(economy['projected_balance_if_won'])}"
    )

    print(
        f"Deuda proyectada:         "
        f"{money(economy['projected_debt_if_won'])}"
    )

    print(
        f"Liquidez recuperable:     "
        f"{money(plan['recoverable_cash'])}"
    )

    print(
        f"Deuda cubierta:           "
        f"{'SÍ' if plan['debt_theoretically_covered'] else 'NO'}"
    )

    coverage_ratio = (
        plan.get(
            "debt_coverage_ratio"
        )
    )

    if coverage_ratio is None:

        coverage_text = (
            "NO APLICA"
        )

    else:

        coverage_text = (
            f"{coverage_ratio:.2f}x"
        )

    print(
        f"Ratio cobertura:          "
        f"{coverage_text}"
    )

    # ==================================================
    # CONTEXTO DE SOLVENCIA
    # ==================================================

    solvency = (
        plan[
            "solvency"
        ]
    )

    deadline = (
        solvency[
            "deadline"
        ]
    )

    calendar = (
        deadline[
            "calendar"
        ]
    )

    print()
    print(
        f"Riesgo solvencia actual:  "
        f"{solvency['risk']}"
    )

    print(
        f"Deadline XI:              "
        f"{calendar['time_to_lineup_lock']}"
    )

    print(
        f"Riesgo XI:                "
        f"{deadline['lineup_risk']}"
    )

    print(
        f"Hard Safety:              "
        f"{'SÍ' if solvency['hard_safety']['active'] else 'NO'}"
    )

    # ==================================================
    # PUJAS ACTIVAS
    # ==================================================

    print()
    print("=" * 100)
    print(
        "PUJAS ACTIVAS"
    )
    print("=" * 100)

    active_bids = (
        plan[
            "active_bids"
        ]
    )

    if not active_bids:

        print()
        print(
            "No hay pujas activas cancelables."
        )

    for player in active_bids:

        print()

        print(
            f"{player['name']:<22}"
            f"{money(player['bid_amount']):>15}"
        )

        print(
            f"   Offer ID:    "
            f"{player.get('offer_id')}"
        )

        print(
            f"   Strategic:   "
            f"{player['strategic_score']:>5.1f}   "
            f"Franchise: "
            f"{player['franchise_score']:>5.1f}   "
            f"Tactical: "
            f"{player['tactical_score']:>5.1f}"
        )

        print(
            f"   Need bonus:  "
            f"{player['squad_need_bonus']:>5.1f}   "
            f"Keep: "
            f"{player['keep_score']:>6.2f}   "
            f"Cancel cost: "
            f"{player['cancel_cost']:>7.3f}"
        )

    # ==================================================
    # CANCELACIÓN ÓPTIMA
    # ==================================================

    print()
    print("=" * 100)
    print(
        "CANCELACIÓN ÓPTIMA"
    )
    print("=" * 100)

    combination = (
        plan.get(
            "best_combination"
        )
    )

    required_unlock = (
        economy[
            "required_unlock"
        ]
    )

    if required_unlock <= 0:

        print()
        print(
            "No es necesario cancelar ninguna puja."
        )

    elif combination is None:

        print()
        print(
            "No existe una combinación suficiente "
            "para desbloquear la capacidad necesaria."
        )

    elif not combination[
        "players"
    ]:

        print()
        print(
            "No es necesario cancelar ninguna puja."
        )

    else:

        print()
        print(
            "CANCELAR:"
        )
        print()

        for player in combination[
            "players"
        ]:

            print(
                f"- "
                f"{player['name']:<22}"
                f"{money(player['bid_amount']):>15}"
                f"   "
                f"Keep {player['keep_score']:.2f}"
            )

        print()

        print(
            f"Capital desbloqueado:    "
            f"{money(combination['unlocked'])}"
        )

        print(
            f"Capital necesario:       "
            f"{money(required_unlock)}"
        )

        print(
            f"Exceso desbloqueado:     "
            f"{money(combination['excess'])}"
        )

        print()

        print(
            f"Daño base:               "
            f"{combination['base_damage']:.2f}"
        )

        print(
            f"Daño posiciones:         "
            f"{combination['position_damage']:.2f}"
        )

        print(
            f"Score optimización:      "
            f"{combination['optimization_score']:.2f}"
        )

    # ==================================================
    # INTERPRETACIÓN
    # ==================================================

    print()
    print("=" * 100)
    print(
        "INTERPRETACIÓN ECONÓMICA"
    )
    print("=" * 100)

    print()
    print(
        "CAPITAL A DESBLOQUEAR"
    )
    print(
        "→ capacidad de puja que debemos recuperar "
        "cancelando ofertas."
    )

    print()
    print(
        "DEUDA PROYECTADA"
    )
    print(
        "→ saldo negativo que podríamos tener si "
        "ganamos al Franchise."
    )

    print()
    print(
        "LIQUIDEZ RECUPERABLE"
    )
    print(
        "→ patrimonio potencialmente vendible para "
        "volver a saldo >= 0 antes de jornada."
    )

    # ==================================================
    # DECISIÓN
    # ==================================================

    print()
    print("=" * 100)
    print(
        "DECISIÓN"
    )
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