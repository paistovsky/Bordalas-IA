from __future__ import annotations

from src.actions.autopilot_executor import (
    validate_temporal_write_gate,
)

from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
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

    state = (
        result[
            "state"
        ]
    )

    decision = (
        result[
            "decision"
        ]
    )

    gate = (
        state.get(
            "temporal_gate",
            {},
        )
        or {}
    )

    print()
    print("=" * 100)
    print(
        "                 BORDALAS IA - AUTOPILOT V3 SAFETY TEST"
    )
    print("=" * 100)
    print()

    print(
        f"Snapshot:              "
        f"{snapshot_file}"
    )

    print(
        f"Jornada objetivo:      "
        f"{state.get('target_matchday')}"
    )

    print(
        f"Fase:                  "
        f"{state.get('phase')}"
    )

    print(
        f"Saldo:                 "
        f"{state.get('balance'):,.0f} EUR"
    )

    print(
        f"XI valido:             "
        f"{state.get('lineup', {}).get('playable_count', 0)}/11"
    )

    print(
        f"Operaciones bloqueadas:"
        f" {'SI' if gate.get('operations_locked') else 'NO'}"
    )

    print(
        f"Hard Safety:           "
        f"{'SI' if gate.get('hard_safety_mode') else 'NO'}"
    )

    print()

    print(
        f"Decision:              "
        f"{decision.get('type')}"
    )

    print(
        f"Prioridad:             "
        f"{decision.get('priority')}"
    )

    print(
        f"Accion:                "
        f"{decision.get('action')}"
    )

    print(
        f"Ejecutable:            "
        f"{'SI' if decision.get('executable') else 'NO'}"
    )

    print()

    # ========================================================
    # TEST SINTETICO DE LA SEGUNDA BARRERA
    # ========================================================

    synthetic_locked = {
        "action":
            "SAVE_LINEUP",

        "executable":
            True,

        "temporal_gate": {
            "phase":
                "ROUND_TRANSITION_LOCK",

            "operations_locked":
                True,

            "hard_safety_mode":
                True,
        },
    }

    blocked = (
        validate_temporal_write_gate(
            synthetic_locked
        )
    )

    print(
        "Test executor lock:    "
        f"{blocked.get('status') if blocked else 'FALLO'}"
    )

    if (
        blocked is None
        or
        blocked.get(
            "status"
        )
        != "TEMPORAL_LOCK"
    ):

        raise RuntimeError(
            "La segunda barrera temporal NO esta funcionando."
        )

    synthetic_hard_safety_bad = {
        "action":
            "BUY_SPECULATION",

        "executable":
            True,

        "temporal_gate": {
            "phase":
                "HARD_SAFETY",

            "operations_locked":
                False,

            "hard_safety_mode":
                True,
        },
    }

    blocked_hard = (
        validate_temporal_write_gate(
            synthetic_hard_safety_bad
        )
    )

    print(
        "Test Hard Safety:      "
        f"{blocked_hard.get('status') if blocked_hard else 'FALLO'}"
    )

    if (
        blocked_hard is None
        or
        blocked_hard.get(
            "status"
        )
        != "HARD_SAFETY_BLOCK"
    ):

        raise RuntimeError(
            "La barrera HARD_SAFETY NO esta funcionando."
        )

    print()
    print(
        "SAFETY GATES V3: OK"
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
