from __future__ import annotations

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.competitive_offer_portfolio_engine import (
    build_current_lineup,
    build_sporting_opportunity_cost,
    classify_replacement_after_sale,
    get_player_name,
    simulate_lineup_without_players,
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

    current = (
        build_current_lineup(
            snapshot
        )
    )

    print()
    print("=" * 96)
    print("BORDALAS IA - SPORTING OPPORTUNITY COST V1.6 - OBSERVER")
    print("=" * 96)
    print(f"Snapshot: {snapshot_file}")
    print(
        "XI actual:",
        current.get("formation_name"),
        "| playable:",
        current.get("playable_count"),
        "| lineup_score:",
        round(
            float(
                current.get(
                    "lineup_score",
                    0.0,
                )
                or 0.0
            ),
            2,
        ),
    )
    print()

    selected = (
        current.get(
            "selected",
            [],
        )
        or []
    )

    rows = []

    for player in selected:

        player_id = int(
            player.get(
                "id"
            )
        )

        simulation = (
            simulate_lineup_without_players(
                snapshot,
                {
                    player_id,
                },
            )
        )

        post = (
            simulation.get(
                "lineup",
                {},
            )
            or {}
        )

        sporting = (
            build_sporting_opportunity_cost(
                current_lineup=
                    current,

                post_lineup=
                    post,
            )
        )

        replacement = (
            classify_replacement_after_sale(
                snapshot=
                    snapshot,

                player_id=
                    player_id,

                current_lineup=
                    current,
            )
        )

        incoming = ", ".join(
            str(
                item.get(
                    "name"
                )
            )
            for item
            in (
                replacement.get(
                    "incoming_players",
                    [],
                )
                or []
            )
        ) or "-"

        rows.append(
            (
                sporting.get(
                    "ranking_cost",
                    0.0,
                ),
                player_id,
                get_player_name(
                    snapshot,
                    player_id,
                ),
                replacement,
                sporting,
                incoming,
            )
        )

    rows.sort(
        key=lambda item:
            item[0]
    )

    for (
        _,
        player_id,
        name,
        replacement,
        sporting,
        incoming,
    ) in rows:

        print("-" * 96)
        print(f"{name} [{player_id}]")
        print(
            "Replacement:",
            replacement.get(
                "replacement_status"
            ),
            "| entra:",
            incoming,
        )
        print(
            "Formacion:",
            replacement.get(
                "formation_before"
            ),
            "->",
            replacement.get(
                "formation_after"
            ),
        )
        print(
            "XI:",
            sporting.get(
                "playable_before"
            ),
            "->",
            sporting.get(
                "playable_after"
            ),
        )
        print(
            "Lineup score:",
            sporting.get(
                "lineup_score_before"
            ),
            "->",
            sporting.get(
                "lineup_score_after"
            ),
        )
        print(
            "Coste deportivo:",
            sporting.get(
                "lineup_score_loss"
            ),
            "|",
            f"{sporting.get('lineup_score_loss_percent')}%",
        )

        assert (
            sporting.get(
                "lineup_score_loss"
            )
            is not None
        )

    print()
    print("=" * 96)
    print("# SPORTING OPPORTUNITY COST V1.6: OK")
    print("# OBSERVER ONLY: NO SE HA EJECUTADO NINGUNA OPERACION")
    print("=" * 96)


if __name__ == "__main__":
    main()
