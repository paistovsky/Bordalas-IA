from __future__ import annotations

import copy
from datetime import timedelta

from src.actions.autopilot_executor import (
    execute_autopilot_decision,
)

from src.analysis.accept_before_expiry_live_selector import (
    select_emergency_accept_offer,
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
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def resolve_offer_id(
    raw_offer: dict,
) -> int | None:

    for key in ("id", "offer_id"):
        value = raw_offer.get(key)

        if value is None:
            continue

        try:
            return int(value)
        except (TypeError, ValueError):
            continue

    return None


def set_balance(
    snapshot: dict,
    balance: int,
) -> None:

    snapshot.setdefault(
        "market",
        {},
    ).setdefault(
        "status",
        {},
    )["balance"] = int(balance)


def set_offer_expiry(
    snapshot: dict,
    offer_ids: set[int],
    hours_from_now: float,
) -> int:

    expiry_ts = int(
        (
            now_utc()
            + timedelta(
                hours=hours_from_now,
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

        offer_id = resolve_offer_id(
            raw_offer
        )

        if (
            offer_id is None
            or offer_id not in offer_ids
        ):
            continue

        raw_offer["until"] = expiry_ts
        changed += 1

    return changed


def main() -> None:

    snapshot_file = get_latest_snapshot()
    original = load_snapshot(
        snapshot_file
    )

    original_solvency = (
        build_solvency_state(
            original
        )
    )

    original_guarantee = (
        original_solvency.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    guaranteed_recovery = safe_int(
        original_guarantee.get(
            "guaranteed_recovery"
        )
    )

    # --------------------------------------------------------
    # ESTADO REAL: no debe seleccionar venta urgente
    # --------------------------------------------------------

    real_reserved_ids = {
        int(offer_id)
        for offer_id in (
            (
                original_solvency.get(
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

    real_selection = (
        select_emergency_accept_offer(
            snapshot=original,
            offer_ids=real_reserved_ids,
        )
    )

    # --------------------------------------------------------
    # ESCENARIO CRITICO URGENTE
    # --------------------------------------------------------

    target_debt = (
        guaranteed_recovery
        - SAFE_LIQUIDITY_BUFFER
        - TARGET_SURPLUS
    )

    simulated = copy.deepcopy(
        original
    )

    set_balance(
        simulated,
        -target_debt,
    )

    pressured = build_solvency_state(
        simulated
    )

    reserved_ids = {
        int(offer_id)
        for offer_id in (
            (
                pressured.get(
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

    changed = set_offer_expiry(
        snapshot=simulated,
        offer_ids=reserved_ids,
        hours_from_now=URGENT_EXPIRY_HOURS,
    )

    selection = (
        select_emergency_accept_offer(
            snapshot=simulated,
            offer_ids=reserved_ids,
        )
    )

    result = build_global_decision(
        simulated
    )

    decision = (
        result.get(
            "decision",
            {},
        )
        or {}
    )

    # execute=False: nunca toca Biwenger.
    dry_execution = (
        execute_autopilot_decision(
            decision=decision,
            execute=False,
        )
    )

    print()
    print("=" * 126)
    print(
        "              BORDALAS IA - ACCEPT OFFER LIVE V1 - INTEGRAL DRY TEST"
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
        f"Ready:                       "
        f"{real_selection.get('ready')}"
    )

    print(
        f"Status:                      "
        f"{real_selection.get('status')}"
    )

    print()
    print("## SIMULACION URGENTE")
    print()

    print(
        f"Reservas:                    "
        f"{len(reserved_ids)}"
    )

    print(
        f"Expiries modificados:        "
        f"{changed}"
    )

    print(
        f"Selector ready:              "
        f"{selection.get('ready')}"
    )

    print(
        f"Selector status:             "
        f"{selection.get('status')}"
    )

    selected = (
        selection.get(
            "selected",
            {},
        )
        or {}
    )

    print(
        f"Jugador seleccionado:        "
        f"{selected.get('player_name')}"
    )

    print(
        f"Offer ID:                    "
        f"{selected.get('offer_id')}"
    )

    print(
        f"Importe:                     "
        f"{safe_int(selected.get('amount')):,.0f} EUR"
    )

    print(
        f"Damage score:                "
        f"{selected.get('damage_score')}"
    )

    print(
        f"Damage / M:                  "
        f"{selected.get('damage_per_million')}"
    )

    print()
    print("## ORCHESTRATOR")
    print()

    print(
        f"Action:                      "
        f"{decision.get('action')}"
    )

    print(
        f"Priority:                    "
        f"{decision.get('priority')}"
    )

    print(
        f"Executable:                  "
        f"{decision.get('executable')}"
    )

    print()
    print("## EXECUTOR DRY RUN")
    print()

    print(
        f"Status:                      "
        f"{dry_execution.get('status')}"
    )

    print(
        f"Write performed:             "
        f"{dry_execution.get('write_performed')}"
    )

    print()
    print("## SAFETY ASSERTIONS")
    print()

    errors = []

    if real_selection.get(
        "ready",
        False,
    ):
        errors.append(
            "El estado real actual no debe autorizar venta urgente."
        )

    if changed != len(
        reserved_ids
    ):
        errors.append(
            "No se modificaron todas las expiraciones simuladas."
        )

    if not selection.get(
        "ready",
        False,
    ):
        errors.append(
            "El selector no autorizo una venta en escenario urgente."
        )

    if not selected:
        errors.append(
            "Selector READY sin oferta seleccionada."
        )

    offer_decision = (
        selected.get(
            "offer_decision",
            {},
        )
        or {}
    )

    if (
        offer_decision.get("decision") == "NEVER_SELL"
        or
        offer_decision.get("protection") == "NEVER_AUTO_SELL"
    ):
        errors.append(
            "El selector eligio un jugador protegido."
        )

    if decision.get(
        "action"
    ) != "ACCEPT_CLUSTER_BEFORE_EXPIRY":
        errors.append(
            "La urgencia no gano la decision global."
        )

    if not decision.get(
        "executable",
        False,
    ):
        errors.append(
            "Accept-Before-Expiry LIVE no esta executable=True."
        )

    if dry_execution.get(
        "status"
    ) != "DRY_RUN":
        errors.append(
            "El executor no devolvio DRY_RUN."
        )

    if dry_execution.get(
        "write_performed",
        False,
    ):
        errors.append(
            "El test realizo una escritura real."
        )

    missing = (
        select_emergency_accept_offer(
            snapshot=original,
            offer_ids={999999999999},
        )
    )

    if missing.get(
        "ready",
        False,
    ):
        errors.append(
            "Un cluster inexistente fue autorizado."
        )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT OFFER LIVE V1: FAILED"
        )

    print(
        "# ACCEPT OFFER LIVE V1 INTEGRAL DRY TEST: OK"
    )

    print("=" * 126)


if __name__ == "__main__":
    main()
