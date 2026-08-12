from __future__ import annotations

from src.analysis.competitive_offer_portfolio_engine import (
    build_current_lineup,
    build_offer_replacement_lookup,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)


def main() -> None:

    from src.analysis.market_analyzer import (
        get_latest_snapshot,
        load_snapshot,
    )

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    board = (
        build_offer_decision_board(
            snapshot=
                snapshot,

            rival_intelligence=
                None,
        )
    )

    lookup = (
        board.get(
            "replacement_lookup",
            {},
        )
        or {}
    )

    print("=" * 110)
    print("BORDALAS IA - V1.5.1 REPLACEMENT VALIDATION")
    print("=" * 110)
    print()
    print(f"Snapshot: {snapshot_file}")

    manager_decisions = [
        item
        for item
        in (
            board.get(
                "decisions",
                [],
            )
            or []
        )
        if item.get(
            "counterparty_type"
        )
        ==
        "MANAGER"
    ]

    if not manager_decisions:

        print()
        print("No hay ofertas de managers en el snapshot actual.")
        print()
        print("# REPLACEMENT VALIDATION V1.5.1: OK")
        return

    for item in manager_decisions:

        detail = (
            lookup.get(
                int(
                    item.get(
                        "player_id",
                        0,
                    )
                    or 0
                ),
                {},
            )
            or {}
        )

        print()
        print("-" * 110)
        print(
            f"{item.get('player_name') or item.get('player_id')}"
        )

        print(
            f"Estado:              "
            f"{detail.get('replacement_status')}"
        )

        print(
            f"Fuente:              "
            f"{detail.get('replacement_source')}"
        )

        print(
            f"XI antes/despues:    "
            f"{detail.get('pre_sale_playable_count')}/11"
            f" -> "
            f"{detail.get('post_sale_playable_count')}/11"
        )

        print(
            f"Formacion:           "
            f"{detail.get('formation_before')}"
            f" -> "
            f"{detail.get('formation_after')}"
        )

        incoming = ", ".join(
            str(
                player.get(
                    "name"
                )
                or
                player.get(
                    "id"
                )
            )

            for player
            in (
                detail.get(
                    "incoming_players",
                    [],
                )
                or []
            )
        )

        print(
            f"Entra:               "
            f"{incoming or 'NINGUNO'}"
        )

        print(
            f"Perdida calidad:     "
            f"{detail.get('quality_loss_score')}"
        )

    print()
    print("# REPLACEMENT VALIDATION V1.5.1: OK")


if __name__ == "__main__":
    main()
