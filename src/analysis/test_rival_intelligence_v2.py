from __future__ import annotations

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
    save_rival_intelligence,
)

from src.collectors.board_history_collector import (
    collect_board_history,
)


def money(
    value,
) -> str:

    return (
        f"{int(value or 0):,.0f} EUR"
    )


def main() -> None:

    board = (
        collect_board_history()
    )

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    market_status = (
        snapshot.get(
            "market",
            {},
        ).get(
            "status",
            {},
        )
        or {}
    )

    intelligence = (
        build_rival_intelligence(
            events=
                board.get(
                    "events",
                    [],
                ),

            users=
                board.get(
                    "users",
                    [],
                ),

            profiles=
                board.get(
                    "profiles",
                    [],
                ),

            catalog=
                snapshot.get(
                    "catalog",
                    {},
                ),

            current_user_id=
                board.get(
                    "current_user_id"
                ),

            own_finances=
                board.get(
                    "own_finances",
                    {},
                ),

            own_balance=
                market_status.get(
                    "balance"
                ),

            own_maximum_bid=
                market_status.get(
                    "maximumBid"
                ),
        )
    )

    save_rival_intelligence(
        intelligence
    )

    validation = (
        intelligence.get(
            "validation",
            {},
        )
        or {}
    )

    calibration = (
        intelligence.get(
            "maximum_bid_calibration",
            {},
        )
        or {}
    )

    print()
    print("=" * 150)
    print(
        "                        BORDALAS IA - RIVAL INTELLIGENCE V2"
    )
    print("=" * 150)

    print(
        f"Snapshot:               "
        f"{snapshot_file}"
    )

    print(
        f"Eventos era actual:     "
        f"{board.get('current_era_events')}"
    )

    print(
        f"Managers:               "
        f"{len(intelligence.get('managers', []) or [])}"
    )

    print()
    print("## VALIDACION CONTABLE")
    print()

    print(
        f"Saldo oficial Pepe:     "
        f"{money(validation.get('official_balance'))}"
    )

    print(
        f"Saldo ledger Pepe:      "
        f"{money(validation.get('ledger_balance'))}"
    )

    print(
        f"Diferencia:             "
        f"{money(validation.get('difference'))}"
    )

    print(
        f"Ledger:                 "
        f"{intelligence.get('ledger_status')}"
    )

    print()
    print("## CALIBRACION PUJA MAXIMA")
    print()

    print(
        f"Disponible:             "
        f"{calibration.get('available')}"
    )

    print(
        f"Ratio deuda/plantilla:  "
        f"{float(calibration.get('ratio', 0) or 0):.6f}"
    )

    print(
        f"Puja max oficial Pepe:  "
        f"{money(calibration.get('own_maximum_bid'))}"
    )

    print()
    print("## RIVAL INTELLIGENCE")
    print()

    header = (
        f"{'MANAGER':<32} "
        f"{'PTS':>5} "
        f"{'SALDO':>12} "
        f"{'PLANTILLA':>12} "
        f"{'PATRIMONIO':>12} "
        f"{'PUJA MAX':>12} "
        f"{'BID VISTA':>12} "
        f"{'ACT':>9} "
        f"{'THREAT':>10}"
    )

    print(
        header
    )

    print(
        "-" * len(
            header
        )
    )

    current_user_id = (
        board.get(
            "current_user_id"
        )
    )

    for manager in (
        intelligence.get(
            "managers",
            [],
        )
        or []
    ):

        is_us = (
            int(
                manager.get(
                    "user_id",
                    0,
                )
                or 0
            )
            ==
            int(
                current_user_id
                or 0
            )
        )

        threat = (
            "NOSOTROS"
            if is_us
            else
            (
                f"{float(manager.get('threat_score',0) or 0):.1f} "
                f"{manager.get('threat_level')}"
            )
        )

        print(
            f"{manager.get('name','?'):<32} "
            f"{manager.get('points',0):>5} "
            f"{money(manager.get('balance')):>12} "
            f"{money(manager.get('roster_value')):>12} "
            f"{money(manager.get('net_worth')):>12} "
            f"{money(manager.get('maximum_bid')):>12} "
            f"{money(manager.get('max_observed_bid')):>12} "
            f"{manager.get('market_activity','?'):>9} "
            f"{threat:>10}"
        )

    print()
    print("## TOP ACTIVOS")
    print()

    for manager in (
        intelligence.get(
            "managers",
            [],
        )
        or []
    ):

        assets = ", ".join(
            (
                f"{item.get('name')} "
                f"({money(item.get('value'))})"
            )
            for item
            in (
                manager.get(
                    "top_assets",
                    [],
                )
                or []
            )[
                :3
            ]
        )

        print(
            f"{manager.get('name')}: "
            f"{assets or 'SIN DATOS'}"
        )

    print()
    print("## SAFETY ASSERTIONS")
    print()

    errors = []

    if not validation.get(
        "exact",
        False,
    ):

        errors.append(
            "Ledger de Pepe no cuadra al euro."
        )

    if intelligence.get(
        "ledger_status"
    ) != "EXACT":

        errors.append(
            "Ledger status distinto de EXACT."
        )

    if not calibration.get(
        "available",
        False,
    ):

        errors.append(
            "No se pudo calibrar la puja maxima."
        )

    managers = (
        intelligence.get(
            "managers",
            [],
        )
        or []
    )

    if len(
        managers
    ) != len(
        board.get(
            "users",
            [],
        )
        or []
    ):

        errors.append(
            "Numero de managers incompleto."
        )

    missing_rosters = [
        manager.get(
            "name"
        )
        for manager
        in managers
        if manager.get(
            "roster_count",
            0,
        ) <= 0
    ]

    if missing_rosters:

        errors.append(
            "Plantillas vacias: "
            +
            ", ".join(
                missing_rosters
            )
        )

    pepe = next(
        (
            manager
            for manager
            in managers
            if int(
                manager.get(
                    "user_id",
                    0,
                )
                or 0
            )
            ==
            int(
                current_user_id
                or 0
            )
        ),
        None,
    )

    if pepe is None:

        errors.append(
            "Pepe no aparece."
        )

    else:

        official_max = int(
            market_status.get(
                "maximumBid",
                0,
            )
            or 0
        )

        estimated_max = int(
            pepe.get(
                "maximum_bid",
                0,
            )
            or 0
        )

        if abs(
            official_max
            -
            estimated_max
        ) > 1:

            errors.append(
                "Calibracion maximumBid de Pepe "
                "no reproduce el valor oficial."
            )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "RIVAL INTELLIGENCE V2: FAILED"
        )

    print(
        "# RIVAL INTELLIGENCE V2: OK"
    )

    print(
        "=" * 150
    )


if __name__ == "__main__":
    main()
