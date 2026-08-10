from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.restructuring_roster_impact_engine import (
    build_restructuring_roster_impact_plan,
    POSITION_NAMES,
)


def money(
    value: int,
) -> str:

    return f"{value:,.0f} €"


def shortage_text(
    shortages: dict,
) -> str:

    parts = []

    for position in (
        1,
        2,
        3,
        4,
    ):

        missing = int(
            shortages.get(
                position,
                0,
            )
            or 0
        )

        if missing <= 0:
            continue

        parts.append(
            f"{POSITION_NAMES[position]} {missing}"
        )

    if not parts:
        return "NINGUNO"

    return ", ".join(
        parts
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    plan = (
        build_restructuring_roster_impact_plan(
            snapshot
        )
    )

    print()
    print("=" * 105)
    print(
        "              BORDALÁS IA - POST CANCELLATION ROSTER IMPACT"
    )
    print("=" * 105)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    if not plan.get(
        "active"
    ):

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
    print("=" * 105)
    print(
        "OBJETIVO"
    )
    print("=" * 105)

    print()
    print(
        f"Franchise:              "
        f"{target['name']}"
    )

    print(
        f"Capital a desbloquear:  "
        f"{money(plan['required_unlock'])}"
    )

    print()
    print("=" * 105)
    print(
        "SITUACIÓN DEL XI"
    )
    print("=" * 105)

    print()
    print(
        f"Con partido ahora:      "
        f"{plan['current_playable_count']}/11"
    )

    print(
        f"Huecos actuales:        "
        f"{shortage_text(plan['current_shortages'])}"
    )

    baseline = (
        plan[
            "baseline_coverage"
        ]
    )

    print()
    print(
        f"Cobertura máxima con "
        f"todas las pujas:       "
        f"+{baseline['covered']}"
    )

    print(
        f"XI potencial:           "
        f"{min(11, plan['current_playable_count'] + baseline['covered'])}/11"
    )

    print(
        f"Huecos restantes:       "
        f"{shortage_text(baseline['remaining_shortages'])}"
    )

    if baseline[
        "assignments"
    ]:

        print()
        print(
            "Refuerzos que cubrirían huecos:"
        )

        for assignment in baseline[
            "assignments"
        ]:

            print(
                f"   "
                f"{assignment['player_name']:<22}"
                f"→ "
                f"{POSITION_NAMES[assignment['position']]}"
            )

    print()
    print("=" * 105)
    print(
        "MEJORES ALTERNATIVAS DE CANCELACIÓN"
    )
    print("=" * 105)

    alternatives = (
        plan[
            "alternatives"
        ]
    )

    if not alternatives:

        print()
        print(
            "No existen alternativas."
        )

    for index, option in enumerate(
        alternatives[:10],
        start=1,
    ):

        print()
        print(
            f"{index}. CANCELAR"
        )

        for player in option[
            "players"
        ]:

            print(
                f"   - "
                f"{player['name']:<22}"
                f"{money(player['bid_amount']):>15}"
            )

        print()
        print(
            f"   Desbloquea:          "
            f"{money(option['unlocked'])}"
        )

        print(
            f"   Exceso:              "
            f"{money(option['excess'])}"
        )

        print(
            f"   XI potencial:        "
            f"{option['projected_playable_count']}/11"
        )

        print(
            f"   Cobertura perdida:   "
            f"{option['coverage_loss']}"
        )

        print(
            f"   Huecos restantes:    "
            f"{shortage_text(option['remaining_shortages'])}"
        )

        print(
            f"   Daño roster:         "
            f"{option['roster_damage']:.2f}"
        )

        print(
            f"   Score TOTAL:         "
            f"{option['total_score']:.2f}"
        )

        print(
            "-" * 105
        )

    print()
    print("=" * 105)
    print(
        "DECISIÓN"
    )
    print("=" * 105)

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

    best = (
        plan[
            "best_combination"
        ]
    )

    if best is not None:

        print()
        print(
            "COMBINACIÓN RECOMENDADA:"
        )

        for player in best[
            "players"
        ]:

            print(
                f"- {player['name']}"
            )

        print()
        print(
            f"XI potencial después: "
            f"{best['projected_playable_count']}/11"
        )

        print(
            f"Huecos pendientes: "
            f"{shortage_text(best['remaining_shortages'])}"
        )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()