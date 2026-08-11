from __future__ import annotations

import copy
from datetime import timedelta

from src.analysis.accept_before_expiry_safety_engine import (
    revalidate_accept_before_expiry_cluster,
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

    snapshot.setdefault(
        "market",
        {},
    ).setdefault(
        "status",
        {},
    )[
        "balance"
    ] = int(
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


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    original = (
        load_snapshot(
            snapshot_file
        )
    )

    original_solvency = (
        build_solvency_state(
            original
        )
    )

    guarantee = (
        original_solvency.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    guaranteed_recovery = (
        safe_int(
            guarantee.get(
                "guaranteed_recovery"
            )
        )
    )

    # ========================================================
    # CASO REAL: cluster seguro -> NO autorizado
    # ========================================================

    real_reserved_ids = {
        int(
            offer_id
        )
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

    real_validation = (
        revalidate_accept_before_expiry_cluster(
            snapshot=
                original,

            offer_ids=
                real_reserved_ids,
        )
    )

    # ========================================================
    # CASO SIMULADO URGENTE -> autorizado
    # ========================================================

    target_debt = (
        guaranteed_recovery
        - SAFE_LIQUIDITY_BUFFER
        - TARGET_SURPLUS
    )

    simulated = (
        copy.deepcopy(
            original
        )
    )

    set_balance(
        simulated,
        -target_debt,
    )

    pressured = (
        build_solvency_state(
            simulated
        )
    )

    reserved_ids = {
        int(
            offer_id
        )
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

    changed = (
        set_offer_expiry(
            snapshot=
                simulated,

            offer_ids=
                reserved_ids,

            hours_from_now=
                URGENT_EXPIRY_HOURS,
        )
    )

    urgent_validation = (
        revalidate_accept_before_expiry_cluster(
            snapshot=
                simulated,

            offer_ids=
                reserved_ids,
        )
    )

    # ========================================================
    # OFERTA INEXISTENTE -> bloqueada
    # ========================================================

    missing_validation = (
        revalidate_accept_before_expiry_cluster(
            snapshot=
                original,

            offer_ids={
                999999999999,
            },
        )
    )

    print()
    print("=" * 124)
    print(
        "              BORDALAS IA - ACCEPT BEFORE EXPIRY LIVE REVALIDATION V1"
    )
    print("=" * 124)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print()
    print(
        "## ESTADO REAL"
    )
    print()

    print(
        f"Offer IDs:                   "
        f"{sorted(real_reserved_ids)}"
    )

    print(
        f"Authorized:                  "
        f"{real_validation.get('authorized')}"
    )

    print(
        f"Status:                      "
        f"{real_validation.get('status')}"
    )

    print()
    print(
        "## SIMULACION URGENTE"
    )
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
        f"Authorized:                  "
        f"{urgent_validation.get('authorized')}"
    )

    print(
        f"Status:                      "
        f"{urgent_validation.get('status')}"
    )

    cluster = (
        urgent_validation.get(
            "cluster",
            {},
        )
        or {}
    )

    print(
        f"Action:                      "
        f"{cluster.get('action')}"
    )

    print(
        f"Restan:                      "
        f"{cluster.get('hours_to_effective_deadline')} h"
    )

    print()
    print(
        "## OFERTA/CLUSTER INEXISTENTE"
    )
    print()

    print(
        f"Authorized:                  "
        f"{missing_validation.get('authorized')}"
    )

    print(
        f"Status:                      "
        f"{missing_validation.get('status')}"
    )

    print()
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    if real_validation.get(
        "authorized",
        False,
    ):

        errors.append(
            "El cluster real seguro no debe autorizar aceptación."
        )

    if not urgent_validation.get(
        "authorized",
        False,
    ):

        errors.append(
            "El cluster crítico urgente simulado no fue autorizado."
        )

    if urgent_validation.get(
        "status"
    ) != "AUTHORIZED":

        errors.append(
            "La revalidación urgente no devolvió AUTHORIZED."
        )

    if cluster.get(
        "action"
    ) != "ACCEPT_CLUSTER_BEFORE_EXPIRY":

        errors.append(
            "El cluster autorizado no sigue siendo urgente."
        )

    if (
        cluster.get(
            "hours_to_effective_deadline"
        )
        is None
        or
        cluster.get(
            "hours_to_effective_deadline"
        )
        > 6.0
    ):

        errors.append(
            "Cluster autorizado fuera del margen operativo."
        )

    loss = (
        cluster.get(
            "loss_simulation",
            {},
        )
        or {}
    )

    if loss.get(
        "guaranteed_after_loss",
        False,
    ):

        errors.append(
            "Cluster autorizado aunque perderlo mantiene garantía."
        )

    if missing_validation.get(
        "authorized",
        False,
    ):

        errors.append(
            "Cluster inexistente fue autorizado."
        )

    if missing_validation.get(
        "status"
    ) != "CLUSTER_NOT_FOUND":

        errors.append(
            "Cluster inexistente no devolvió CLUSTER_NOT_FOUND."
        )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT BEFORE EXPIRY LIVE REVALIDATION: FAILED"
        )

    print(
        "# ACCEPT BEFORE EXPIRY LIVE REVALIDATION V1: OK"
    )

    print("=" * 124)


if __name__ == "__main__":
    main()
