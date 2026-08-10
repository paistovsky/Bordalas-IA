from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def money(
    value,
) -> str:

    if value is None:

        return "DESCONOCIDO"

    return (
        f"{value:,.0f} €"
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

    result = (
        build_global_decision(
            snapshot
        )
    )

    decision = (
        result[
            "decision"
        ]
    )

    state = (
        result[
            "state"
        ]
    )

    print()
    print("=" * 105)
    print(
        "                  BORDALÁS IA - GENERAL DECISION ORCHESTRATOR"
    )
    print("=" * 105)

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()
    print("=" * 105)
    print(
        "ESTADO GLOBAL"
    )
    print("=" * 105)

    print()

    print(
        f"Saldo:                  "
        f"{money(state['balance'])}"
    )

    franchise = (
        state[
            "franchise"
        ]
    )

    print(
        f"Franchise state:        "
        f"{franchise.get('state')}"
    )

    target = (
        franchise.get(
            "target"
        )
    )

    if target:

        print(
            f"Franchise target:       "
            f"{target.get('name')}"
        )

    lineup = (
        state[
            "lineup"
        ]
    )

    print(
        f"XI con partido:         "
        f"{lineup['playable_count']}/11"
    )

    print(
        f"Huecos XI:              "
        f"{lineup['missing']}"
    )

    offers = (
        state[
            "offers"
        ]
    )

    print(
        f"Ofertas recibidas:      "
        f"{len(offers.get('incoming', []))}"
    )

    speculation = (
        state[
            "speculation"
        ]
    )

    budget = (
        speculation.get(
            "budget",
            {},
        )
    )

    print(
        f"Speculation activa:     "
        f"{'SÍ' if budget.get('enabled') else 'NO'}"
    )

    print(
        f"Speculation bloqueada:  "
        f"{budget.get('blocked_by')}"
    )

    print()
    print("=" * 105)
    print(
        "DECISIÓN GLOBAL"
    )
    print("=" * 105)

    print()

    print(
        f"Tipo:        "
        f"{decision['type']}"
    )

    print(
        f"Prioridad:   "
        f"{decision['priority']}"
    )

    print(
        f"Acción:      "
        f"{decision['action']}"
    )

    print(
        f"Ejecutable:  "
        f"{'SÍ' if decision['executable'] else 'NO'}"
    )

    print()

    print(
        decision[
            "reason"
        ]
    )

    print()
    print("=" * 105)
    print(
        "COLA DE PRIORIDADES"
    )
    print("=" * 105)

    for index, candidate in enumerate(
        result[
            "candidates"
        ][
            :10
        ],
        start=1,
    ):

        print()

        print(
            f"{index:>2}. "
            f"{candidate['type']:<24}"
            f"{candidate['priority']:>5}   "
            f"{candidate['action']}"
        )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()