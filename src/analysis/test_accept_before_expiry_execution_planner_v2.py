from __future__ import annotations

import copy
from datetime import timedelta

from src.analysis.accept_before_expiry_execution_planner import (
    build_accept_before_expiry_execution_plan,
)

from src.analysis.computer_offer_reroll_engine import (
    now_utc,
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
    )[
        "balance"
    ] = int(balance)


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
            or
            offer_id not in offer_ids
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

    original_solvency = build_solvency_state(
        original
    )

    guaranteed_recovery = safe_int(
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

    plan = (
        build_accept_before_expiry_execution_plan(
            snapshot=simulated,
            offer_ids=reserved_ids,
        )
    )

    print()
    print("=" * 128)
    print(
        "        BORDALAS IA - ACCEPT BEFORE EXPIRY EXECUTION PLANNER V2 - MULTI ACCEPT OBSERVER"
    )
    print("=" * 128)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print(
        f"Reservas simuladas:          "
        f"{len(reserved_ids)}"
    )

    print(
        f"Expiries modificados:        "
        f"{changed}"
    )

    print(
        f"Planner status:              "
        f"{plan.get('status')}"
    )

    print(
        f"Ready:                       "
        f"{plan.get('ready')}"
    )

    print(
        f"Combinaciones evaluadas:     "
        f"{plan.get('evaluated_combinations', 0)}"
    )

    print(
        f"Aceptaciones minimas:        "
        f"{plan.get('required_accept_count')}"
    )

    print()
    print(
        "## PLAN GANADOR"
    )
    print()

    selected = (
        plan.get(
            "selected_offers",
            [],
        )
        or []
    )

    if not selected:

        print(
            "NINGUN PLAN SEGURO."
        )

    for index, item in enumerate(
        selected,
        start=1,
    ):

        print(
            f"{index}. "
            f"{', '.join(item.get('player_names', [])):<24} "
            f"{item.get('amount', 0):>12,.0f} EUR "
            f"damage={item.get('damage_score'):>8.2f}"
        )

    selected_plan = (
        plan.get(
            "selected_plan",
            {},
        )
        or {}
    )

    simulation = (
        selected_plan.get(
            "simulation",
            {},
        )
        or {}
    )

    print()
    print(
        f"Total vendido:               "
        f"{selected_plan.get('total_amount', 0):,.0f} EUR"
    )

    print(
        f"Damage total:                "
        f"{selected_plan.get('total_damage')}"
    )

    print(
        f"Estado final simulado:       "
        f"{simulation.get('state_after')}"
    )

    print(
        f"Surplus final:               "
        f"{safe_int(simulation.get('surplus_after')):,.0f} EUR"
    )

    first_offer = (
        plan.get(
            "first_offer"
        )
        or {}
    )

    print()
    print(
        "## PRIMERA ESCRITURA PROPUESTA"
    )
    print()

    if first_offer:

        print(
            f"Jugador:                     "
            f"{', '.join(first_offer.get('player_names', []))}"
        )

        print(
            f"Offer ID:                    "
            f"{first_offer.get('offer_id')}"
        )

        print(
            f"Importe:                     "
            f"{first_offer.get('amount', 0):,.0f} EUR"
        )

        print(
            f"Damage:                      "
            f"{first_offer.get('damage_score')}"
        )

    else:

        print(
            "NINGUNA"
        )

    print()
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    if changed != len(
        reserved_ids
    ):

        errors.append(
            "No se modificaron todas las expiraciones simuladas."
        )

    if not plan.get(
        "ready",
        False,
    ):

        errors.append(
            "No se encontro un plan multi-accept seguro."
        )

    if not selected:

        errors.append(
            "Planner READY sin ofertas seleccionadas."
        )

    if any(
        item.get(
            "protected",
            False,
        )
        for item in selected
    ):

        errors.append(
            "El plan contiene un jugador protegido."
        )

    if not first_offer:

        errors.append(
            "No existe primera escritura propuesta."
        )

    if selected_plan:

        if not simulation.get(
            "guaranteed_after",
            False,
        ):

            errors.append(
                "El plan ganador no mantiene SOLVENCY_GUARANTEE."
            )

        if (
            selected_plan.get(
                "count"
            )
            != len(
                selected
            )
        ):

            errors.append(
                "Cardinalidad inconsistente en el plan."
            )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT BEFORE EXPIRY EXECUTION PLANNER V2: FAILED"
        )

    print(
        "# ACCEPT BEFORE EXPIRY EXECUTION PLANNER V2 MULTI ACCEPT OBSERVER: OK"
    )

    print("=" * 128)


if __name__ == "__main__":
    main()
