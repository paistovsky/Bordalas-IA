from src.analysis.accept_before_expiry_safety_engine import (
    build_accept_before_expiry_safety_board,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def money(
    value,
) -> str:
    return f"{int(value or 0):,.0f} EUR"


def fmt_dt(
    value,
) -> str:
    if value is None:
        return "DESCONOCIDO"

    try:
        return value.strftime(
            "%d/%m/%Y %H:%M"
        )
    except AttributeError:
        return str(
            value
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

    board = (
        build_accept_before_expiry_safety_board(
            snapshot
        )
    )

    print()
    print("=" * 128)
    print(
        "              BORDALAS IA - ACCEPT BEFORE EXPIRY SAFETY V2.1 - CLUSTER OBSERVER"
    )
    print("=" * 128)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print(
        f"SOLVENCY_RESERVED:           "
        f"{board['reserved_count']}"
    )

    print(
        f"Clusters de caducidad:       "
        f"{board['cluster_count']}"
    )

    print(
        f"Clusters seguros:            "
        f"{board['safe_cluster_count']}"
    )

    print(
        f"Clusters watch:              "
        f"{board['watch_cluster_count']}"
    )

    print(
        f"Clusters urgentes:           "
        f"{board['urgent_cluster_count']}"
    )

    print()
    print(
        "## PERDIDA INDIVIDUAL"
    )
    print()

    for item in board[
        "individual"
    ]:

        loss = (
            item.get(
                "loss_simulation",
                {},
            )
            or {}
        )

        print(
            f"{str(item.get('player_name') or '?'):<24} "
            f"{money(item.get('amount')):>15} "
            f"limite={fmt_dt(item.get('effective_deadline'))} "
            f"restan={item.get('hours_to_effective_deadline')}h "
            f"after_loss={loss.get('state_after_loss')} "
            f"surplus={money(loss.get('surplus_after_loss'))}"
        )

    print()
    print(
        "## CLUSTERS DE CADUCIDAD"
    )
    print()

    for index, cluster in enumerate(
        board[
            "clusters"
        ],
        start=1,
    ):

        loss = (
            cluster.get(
                "loss_simulation",
                {},
            )
            or {}
        )

        names = ", ".join(
            cluster.get(
                "player_names",
                [],
            )
        )

        print(
            f"CLUSTER {index}: {names}"
        )

        print(
            f"    Ofertas:                 "
            f"{cluster.get('offer_count')}"
        )

        print(
            f"    Importe total:           "
            f"{money(cluster.get('total_amount'))}"
        )

        print(
            f"    Limite efectivo:         "
            f"{fmt_dt(cluster.get('effective_deadline'))}"
        )

        print(
            f"    Horas restantes:         "
            f"{cluster.get('hours_to_effective_deadline')}"
        )

        print(
            f"    Estado tras perder TODAS:"
            f" {loss.get('state_after_loss')}"
        )

        print(
            f"    Surplus tras perdida:    "
            f"{money(loss.get('surplus_after_loss'))}"
        )

        print(
            f"    Decision:                "
            f"{cluster.get('action')}"
        )

        print(
            f"    Motivo:                  "
            f"{cluster.get('reason')}"
        )

        print()

    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    for cluster in board.get(
        "safe_clusters",
        [],
    ):

        loss = (
            cluster.get(
                "loss_simulation",
                {},
            )
            or {}
        )

        if not loss.get(
            "guaranteed_after_loss",
            False,
        ):

            errors.append(
                "Cluster marcado HOLD aunque perderlo rompe garantía."
            )

    for cluster in (
        board.get(
            "watch_clusters",
            [],
        )
        +
        board.get(
            "urgent_clusters",
            [],
        )
    ):

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
                "Cluster marcado crítico aunque perderlo "
                "mantiene garantía."
            )

    for cluster in board.get(
        "urgent_clusters",
        [],
    ):

        hours = (
            cluster.get(
                "hours_to_effective_deadline"
            )
        )

        if (
            hours is None
            or
            hours > 6.0
        ):

            errors.append(
                "Cluster urgente fuera del margen de 6h."
            )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT BEFORE EXPIRY SAFETY V2.1: FAILED"
        )

    print(
        "# ACCEPT BEFORE EXPIRY SAFETY V2.1 CLUSTER OBSERVER: OK"
    )

    print("=" * 128)


if __name__ == "__main__":
    main()
