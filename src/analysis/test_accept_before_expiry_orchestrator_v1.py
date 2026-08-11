from __future__ import annotations

import copy
from datetime import timedelta

from src.analysis.accept_before_expiry_safety_engine import (
    build_accept_before_expiry_safety_board,
)

from src.analysis.computer_offer_reroll_engine import (
    now_utc,
)

from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.solvency_engine import (
    SAFE_LIQUIDITY_BUFFER,
    build_solvency_state,
)


TARGET_SURPLUS = 1_000_000
URGENT_EXPIRY_HOURS = 2.0


def safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(
            value
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def set_balance(
    snapshot: dict,
    balance: int,
) -> None:

    status = (
        snapshot.setdefault(
            "market",
            {},
        ).setdefault(
            "status",
            {},
        )
    )

    status["balance"] = int(
        balance
    )


def resolve_offer_id(
    raw_offer: dict,
) -> int | None:

    for key in (
        "id",
        "offer_id",
    ):
        value = raw_offer.get(
            key
        )

        if value is None:
            continue

        try:
            return int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


def set_offer_expiry(
    snapshot: dict,
    offer_ids: set[int],
    hours_from_now: float,
) -> int:

    expiry_ts = int(
        (
            now_utc()
            + timedelta(
                hours=
                    hours_from_now,
            )
        ).timestamp()
    )

    changed = 0

    for raw_offer in (
        snapshot.get(
            "market",
            {},
        ).get(
            "offers",
            [],
        )
        or []
    ):

        offer_id = (
            resolve_offer_id(
                raw_offer
            )
        )

        if (
            offer_id is None
            or
            offer_id not in offer_ids
        ):
            continue

        raw_offer[
            "until"
        ] = expiry_ts

        changed += 1

    return changed


def find_candidate(
    result: dict,
    candidate_type: str,
) -> dict | None:

    return next(
        (
            item
            for item in result.get(
                "candidates",
                [],
            )
            if item.get(
                "type"
            )
            == candidate_type
        ),
        None,
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    original = (
        load_snapshot(
            snapshot_file
        )
    )

    print()
    print("=" * 128)
    print(
        "          BORDALAS IA - ACCEPT BEFORE EXPIRY ORCHESTRATOR V1 - OBSERVER"
    )
    print("=" * 128)
    print()

    # ========================================================
    # ESTADO REAL
    # ========================================================

    real_result = (
        build_global_decision(
            original
        )
    )

    real_state = (
        real_result.get(
            "state",
            {},
        )
        or {}
    )

    real_board = (
        real_state.get(
            "accept_expiry_safety",
            {},
        )
        or {}
    )

    direct_real_board = (
        build_accept_before_expiry_safety_board(
            original
        )
    )

    real_watch = (
        find_candidate(
            real_result,
            "ACCEPT_BEFORE_EXPIRY_WATCH",
        )
    )

    real_urgent = (
        find_candidate(
            real_result,
            "ACCEPT_BEFORE_EXPIRY_SAFETY",
        )
    )

    print(
        "## ESTADO REAL"
    )
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print(
        f"SOLVENCY_RESERVED:           "
        f"{real_board.get('reserved_count', 0)}"
    )

    print(
        f"Clusters de caducidad:       "
        f"{real_board.get('cluster_count', 0)}"
    )

    print(
        f"Clusters seguros:            "
        f"{real_board.get('safe_cluster_count', 0)}"
    )

    print(
        f"Clusters watch:              "
        f"{real_board.get('watch_cluster_count', 0)}"
    )

    print(
        f"Clusters urgentes:           "
        f"{real_board.get('urgent_cluster_count', 0)}"
    )

    print(
        f"Candidato watch:             "
        f"{bool(real_watch)}"
    )

    print(
        f"Candidato urgente:           "
        f"{bool(real_urgent)}"
    )

    # ========================================================
    # SIMULACION WATCH
    # ========================================================

    original_solvency = (
        build_solvency_state(
            original
        )
    )

    guaranteed_recovery = (
        safe_int(
            (
                original_solvency.get(
                    "solvency_guarantee",
                    {},
                )
                or {}
            ).get(
                "guaranteed_recovery"
            )
        )
    )

    target_debt = (
        guaranteed_recovery
        - SAFE_LIQUIDITY_BUFFER
        - TARGET_SURPLUS
    )

    watch_snapshot = (
        copy.deepcopy(
            original
        )
    )

    set_balance(
        watch_snapshot,
        -target_debt,
    )

    watch_result = (
        build_global_decision(
            watch_snapshot
        )
    )

    watch_candidate = (
        find_candidate(
            watch_result,
            "ACCEPT_BEFORE_EXPIRY_WATCH",
        )
    )

    print()
    print(
        "## SIMULACION WATCH"
    )
    print()

    if watch_candidate:

        cluster = (
            watch_candidate.get(
                "data",
                {},
            ).get(
                "cluster",
                {},
            )
            or {}
        )

        print(
            f"Type:                        "
            f"{watch_candidate.get('type')}"
        )

        print(
            f"Priority:                    "
            f"{watch_candidate.get('priority')}"
        )

        print(
            f"Action:                      "
            f"{watch_candidate.get('action')}"
        )

        print(
            f"Executable:                  "
            f"{watch_candidate.get('executable')}"
        )

        print(
            f"Players:                     "
            f"{', '.join(cluster.get('player_names', []))}"
        )

        print(
            f"Restan:                      "
            f"{cluster.get('hours_to_effective_deadline')} h"
        )

    else:

        print(
            "NO CANDIDATO WATCH"
        )

    # ========================================================
    # SIMULACION URGENTE
    # ========================================================

    urgent_snapshot = (
        copy.deepcopy(
            watch_snapshot
        )
    )

    watch_solvency = (
        build_solvency_state(
            watch_snapshot
        )
    )

    reserved_ids = {
        int(
            offer_id
        )
        for offer_id in (
            (
                watch_solvency.get(
                    "solvency_reservations",
                    {},
                )
                or {}
            ).get(
                "reserved_offer_ids",
                [],
            )
            or []
        )
        if offer_id is not None
    }

    changed = (
        set_offer_expiry(
            urgent_snapshot,
            reserved_ids,
            URGENT_EXPIRY_HOURS,
        )
    )

    urgent_result = (
        build_global_decision(
            urgent_snapshot
        )
    )

    urgent_candidate = (
        find_candidate(
            urgent_result,
            "ACCEPT_BEFORE_EXPIRY_SAFETY",
        )
    )

    print()
    print(
        "## SIMULACION URGENTE"
    )
    print()

    print(
        f"Ofertas modificadas:         "
        f"{changed}"
    )

    if urgent_candidate:

        cluster = (
            urgent_candidate.get(
                "data",
                {},
            ).get(
                "cluster",
                {},
            )
            or {}
        )

        print(
            f"Type:                        "
            f"{urgent_candidate.get('type')}"
        )

        print(
            f"Priority:                    "
            f"{urgent_candidate.get('priority')}"
        )

        print(
            f"Action:                      "
            f"{urgent_candidate.get('action')}"
        )

        print(
            f"Executable:                  "
            f"{urgent_candidate.get('executable')}"
        )

        print(
            f"Players:                     "
            f"{', '.join(cluster.get('player_names', []))}"
        )

        print(
            f"Restan:                      "
            f"{cluster.get('hours_to_effective_deadline')} h"
        )

        print(
            f"Global action:               "
            f"{(
                urgent_result.get(
                    'decision',
                    {},
                )
                or {}
            ).get('action')}"
        )

        print(
            f"Global priority:             "
            f"{(
                urgent_result.get(
                    'decision',
                    {},
                )
                or {}
            ).get('priority')}"
        )

    else:

        print(
            "NO CANDIDATO URGENTE"
        )

    # ========================================================
    # SAFETY
    # ========================================================

    print()
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    if (
        real_board.get("reserved_count", 0)
        != direct_real_board.get("reserved_count", 0)
    ):
        errors.append(
            "state['accept_expiry_safety'] no coincide con el board directo."
        )

    if (
        real_board.get("cluster_count", 0)
        != direct_real_board.get("cluster_count", 0)
    ):
        errors.append(
            "El número de clusters en state no coincide con el motor directo."
        )

    if (
        real_board.get("safe_cluster_count", 0)
        != direct_real_board.get("safe_cluster_count", 0)
    ):
        errors.append(
            "Los clusters seguros en state no coinciden con el motor directo."
        )

    if real_watch is not None:
        errors.append(
            "El estado real actual no debería tener WATCH crítico."
        )

    if real_urgent is not None:
        errors.append(
            "El estado real actual no debería tener aceptación urgente."
        )

    if watch_candidate is None:
        errors.append(
            "La simulación crítica no generó WATCH."
        )
    else:
        if watch_candidate.get(
            "executable"
        ):
            errors.append(
                "WATCH no debe ser executable."
            )

        if watch_candidate.get(
            "action"
        ) != "WATCH_CRITICAL_EXPIRY_CLUSTER":
            errors.append(
                "Action WATCH inesperada."
            )

    if urgent_candidate is None:
        errors.append(
            "La simulación urgente no generó candidato."
        )
    else:
        if urgent_candidate.get(
            "executable"
        ):
            errors.append(
                "Accept-Before-Expiry sigue Observer: executable debe ser False."
            )

        if urgent_candidate.get(
            "action"
        ) != "ACCEPT_CLUSTER_BEFORE_EXPIRY":
            errors.append(
                "Action urgente inesperada."
            )

        global_decision = (
            urgent_result.get(
                "decision",
                {},
            )
            or {}
        )

        if global_decision.get(
            "action"
        ) != "ACCEPT_CLUSTER_BEFORE_EXPIRY":
            errors.append(
                "La urgencia de expiración no ganó la decisión global."
            )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT BEFORE EXPIRY ORCHESTRATOR: FAILED"
        )

    print(
        "# ACCEPT BEFORE EXPIRY ORCHESTRATOR V1 OBSERVER: OK"
    )

    print("=" * 128)


if __name__ == "__main__":
    main()
