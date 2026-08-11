from __future__ import annotations

import copy

from src.actions.autopilot_executor import (
    execute_autopilot_decision,
)

from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


def safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def main() -> None:

    snapshot_file = get_latest_snapshot()
    original = load_snapshot(
        snapshot_file
    )

    real_board = (
        build_speculation_board(
            original
        )
    )

    real_budget = (
        real_board.get(
            "budget",
            {},
        )
        or {}
    )

    print()
    print("=" * 126)
    print(
        "              BORDALAS IA - SPECULATION LIVE V1 - INTEGRAL DRY TEST"
    )
    print("=" * 126)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print()
    print("## ESTADO REAL")
    print()

    print(
        f"Budget enabled:              "
        f"{real_budget.get('enabled')}"
    )

    print(
        f"Budget mode:                 "
        f"{real_budget.get('mode')}"
    )

    print(
        f"Balance:                     "
        f"{safe_int(real_budget.get('balance')):,.0f} EUR"
    )

    print(
        f"Executable buys:             "
        f"{len(real_board.get('executable_buys', []) or [])}"
    )

    # ========================================================
    # TEST REAL SI YA HAY CANDIDATO
    # ========================================================

    real_result = (
        build_global_decision(
            original
        )
    )

    real_spec_candidate = next(
        (
            item
            for item in (
                real_result.get(
                    "candidates",
                    [],
                )
                or []
            )
            if item.get(
                "action"
            )
            == "BUY_SPECULATION"
        ),
        None,
    )

    if real_spec_candidate:

        dry = (
            execute_autopilot_decision(
                decision=
                    real_spec_candidate,

                execute=
                    False,
            )
        )

        print()
        print("## CANDIDATO REAL")
        print()

        player = (
            (
                real_spec_candidate.get(
                    "data",
                    {},
                )
                or {}
            ).get(
                "player",
                {},
            )
            or {}
        )

        print(
            f"Jugador:                     "
            f"{player.get('name')}"
        )

        print(
            f"Score:                       "
            f"{player.get('speculation_score')}"
        )

        print(
            f"Executable:                  "
            f"{real_spec_candidate.get('executable')}"
        )

        print(
            f"DRY status:                  "
            f"{dry.get('status')}"
        )

        print(
            f"Write performed:             "
            f"{dry.get('write_performed')}"
        )

    else:

        print()
        print("## CANDIDATO REAL")
        print()
        print(
            "No existe BUY_SPECULATION ejecutable "
            "en el estado real actual."
        )

    # ========================================================
    # SAFETY: saldo negativo nunca ejecuta V1 LIVE
    # ========================================================

    negative = copy.deepcopy(
        original
    )

    negative.setdefault(
        "market",
        {},
    ).setdefault(
        "status",
        {},
    )["balance"] = -1_000_000

    negative_result = (
        build_global_decision(
            negative
        )
    )

    negative_spec = next(
        (
            item
            for item in (
                negative_result.get(
                    "candidates",
                    [],
                )
                or []
            )
            if item.get(
                "action"
            )
            == "BUY_SPECULATION"
        ),
        None,
    )

    print()
    print("## SAFETY SALDO NEGATIVO")
    print()

    print(
        f"BUY_SPECULATION candidate:   "
        f"{bool(negative_spec)}"
    )

    print()
    print("## SAFETY ASSERTIONS")
    print()

    errors = []

    if real_spec_candidate:

        if not real_spec_candidate.get(
            "executable",
            False,
        ):
            errors.append(
                "BUY_SPECULATION real no esta executable=True."
            )

        if dry.get(
            "status"
        ) != "DRY_RUN":
            errors.append(
                "Executor no devolvio DRY_RUN."
            )

        if dry.get(
            "write_performed",
            False,
        ):
            errors.append(
                "El test realizo una escritura real."
            )

    if negative_spec is not None:
        errors.append(
            "V1 LIVE genero BUY_SPECULATION con saldo negativo."
        )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "SPECULATION LIVE V1: FAILED"
        )

    print(
        "# SPECULATION LIVE V1 INTEGRAL DRY TEST: OK"
    )

    print("=" * 126)


if __name__ == "__main__":
    main()
