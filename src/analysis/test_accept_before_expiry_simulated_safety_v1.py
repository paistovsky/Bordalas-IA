from __future__ import annotations

import copy
from datetime import timedelta

from src.analysis.accept_before_expiry_safety_engine import (
    build_accept_before_expiry_safety_board,
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


TARGET_GUARANTEE_SURPLUS = 1_000_000
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

    market = (
        snapshot.setdefault(
            "market",
            {},
        )
    )

    status = (
        market.setdefault(
            "status",
            {},
        )
    )

    status[
        "balance"
    ] = int(
        balance
    )


def resolve_raw_offer_id(
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

    expiry = (
        now_utc()
        + timedelta(
            hours=
                hours_from_now,
        )
    )

    expiry_ts = int(
        expiry.timestamp()
    )

    changed = 0

    offers = (
        snapshot.get(
            "market",
            {},
        ).get(
            "offers",
            [],
        )
        or []
    )

    for raw_offer in offers:

        offer_id = (
            resolve_raw_offer_id(
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

    if guaranteed_recovery <= (
        SAFE_LIQUIDITY_BUFFER
        + TARGET_GUARANTEE_SURPLUS
    ):

        raise SystemExit(
            "ERROR: no existe suficiente liquidez para "
            "construir la simulacion."
        )

    # Queremos que el snapshot simulado siga GARANTIZADO,
    # pero solo con 1M de margen.
    target_debt = (
        guaranteed_recovery
        - SAFE_LIQUIDITY_BUFFER
        - TARGET_GUARANTEE_SURPLUS
    )

    simulated = copy.deepcopy(
        original
    )

    set_balance(
        snapshot=
            simulated,

        balance=
            -target_debt,
    )

    pressured_solvency = (
        build_solvency_state(
            simulated
        )
    )

    pressured_guarantee = (
        pressured_solvency.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    reservations = (
        pressured_solvency.get(
            "solvency_reservations",
            {},
        )
        or {}
    )

    reserved_ids = {
        int(
            offer_id
        )
        for offer_id in (
            reservations.get(
                "reserved_offer_ids",
                [],
            )
            or []
        )
        if offer_id is not None
    }

    if not reserved_ids:

        raise SystemExit(
            "ERROR: la simulacion no genero SOLVENCY_RESERVED."
        )

    # Primero probamos un escenario crítico pero NO urgente.
    watch_board = (
        build_accept_before_expiry_safety_board(
            simulated
        )
    )

    critical_watch = [
        cluster
        for cluster in watch_board.get(
            "watch_clusters",
            [],
        )
    ]

    # Después hacemos caducar las reservas críticas en 2h.
    urgent_snapshot = copy.deepcopy(
        simulated
    )

    changed = (
        set_offer_expiry(
            snapshot=
                urgent_snapshot,

            offer_ids=
                reserved_ids,

            hours_from_now=
                URGENT_EXPIRY_HOURS,
        )
    )

    urgent_board = (
        build_accept_before_expiry_safety_board(
            urgent_snapshot
        )
    )

    urgent_clusters = (
        urgent_board.get(
            "urgent_clusters",
            [],
        )
        or []
    )

    print()
    print("=" * 126)
    print(
        "          BORDALAS IA - ACCEPT BEFORE EXPIRY SIMULATED SAFETY V1"
    )
    print("=" * 126)
    print()

    print(
        f"Snapshot original:           "
        f"{snapshot_file}"
    )

    print(
        f"Guaranteed recovery:         "
        f"{guaranteed_recovery:,.0f} EUR"
    )

    print(
        f"Saldo simulado:              "
        f"{-target_debt:,.0f} EUR"
    )

    print(
        f"Surplus simulado actual:     "
        f"{safe_int(pressured_guarantee.get('guarantee_surplus')):,.0f} EUR"
    )

    print(
        f"Reservas simuladas:          "
        f"{len(reserved_ids)}"
    )

    print()
    print(
        "## ESCENARIO CRITICO NO URGENTE"
    )
    print()

    print(
        f"Clusters watch:              "
        f"{len(critical_watch)}"
    )

    for cluster in critical_watch:

        loss = (
            cluster.get(
                "loss_simulation",
                {},
            )
            or {}
        )

        print(
            f"{', '.join(cluster.get('player_names', []))}"
        )

        print(
            f"  Restan:                    "
            f"{cluster.get('hours_to_effective_deadline')} h"
        )

        print(
            f"  Estado tras perder cluster:"
            f" {loss.get('state_after_loss')}"
        )

        print(
            f"  Surplus tras perdida:      "
            f"{safe_int(loss.get('surplus_after_loss')):,.0f} EUR"
        )

        print(
            f"  Decision:                  "
            f"{cluster.get('action')}"
        )

    print()
    print(
        "## ESCENARIO CRITICO URGENTE"
    )
    print()

    print(
        f"Ofertas con expiry forzado:  "
        f"{changed}"
    )

    print(
        f"Clusters urgentes:           "
        f"{len(urgent_clusters)}"
    )

    for cluster in urgent_clusters:

        loss = (
            cluster.get(
                "loss_simulation",
                {},
            )
            or {}
        )

        print(
            f"{', '.join(cluster.get('player_names', []))}"
        )

        print(
            f"  Restan:                    "
            f"{cluster.get('hours_to_effective_deadline')} h"
        )

        print(
            f"  Estado tras perder cluster:"
            f" {loss.get('state_after_loss')}"
        )

        print(
            f"  Surplus tras perdida:      "
            f"{safe_int(loss.get('surplus_after_loss')):,.0f} EUR"
        )

        print(
            f"  Decision:                  "
            f"{cluster.get('action')}"
        )

    print()
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    if not pressured_guarantee.get(
        "guaranteed",
        False,
    ):

        errors.append(
            "El escenario base simulado no parte de GUARANTEED."
        )

    if (
        safe_int(
            pressured_guarantee.get(
                "guarantee_surplus"
            )
        )
        != TARGET_GUARANTEE_SURPLUS
    ):

        errors.append(
            "El surplus simulado no coincide con el objetivo."
        )

    if not critical_watch:

        errors.append(
            "No se genero ACCEPT_CLUSTER_WATCH "
            "en el escenario crítico no urgente."
        )

    if changed != len(
        reserved_ids
    ):

        errors.append(
            "No se modificó la caducidad de todas las reservas."
        )

    if not urgent_clusters:

        errors.append(
            "No se genero ACCEPT_CLUSTER_BEFORE_EXPIRY "
            "en el escenario urgente."
        )

    for cluster in urgent_clusters:

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
                "Cluster urgente fuera del margen de 6h."
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
                "Cluster urgente mantiene garantía tras perderlo."
            )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT BEFORE EXPIRY SIMULATED SAFETY: FAILED"
        )

    print(
        "# ACCEPT BEFORE EXPIRY SIMULATED SAFETY V1: OK"
    )

    print("=" * 126)


if __name__ == "__main__":
    main()
