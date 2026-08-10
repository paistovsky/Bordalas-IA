from __future__ import annotations

from src.analysis.lineup_engine import (
    build_lineup,
    prepare_players,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.presentation.lineup_renderer import (
    print_lineup_field,
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

    players = (
        prepare_players(
            snapshot
        )
    )

    lineup = (
        build_lineup(
            snapshot
        )
    )

    print()
    print("=" * 100)
    print(
        "                    BORDALAS IA - LINEUP V2"
    )
    print("=" * 100)
    print()

    print(
        f"Snapshot:              "
        f"{snapshot_file}"
    )

    print(
        f"Formacion:             "
        f"{lineup.get('formation_name')}"
    )

    print(
        f"XI valido:             "
        f"{lineup.get('playable_count')}/11"
    )

    print(
        f"Fixtures visibles:     "
        f"{lineup.get('visible_fixture_count')}/11"
    )

    print(
        f"Score total:           "
        f"{lineup.get('lineup_score'):.2f}"
    )

    print()

    yamal = next(
        (
            player

            for player in players

            if player.get(
                "name"
            )
            == "Yamal"
        ),
        None,
    )

    print(
        "YAMAL"
    )

    print(
        "-" * 100
    )

    if yamal is None:

        print(
            "No encontrado."
        )

    else:

        print(
            f"Disponible:            "
            f"{'SI' if yamal.get('is_available') else 'NO'}"
        )

        print(
            f"Automatic lineup:      "
            f"{'SI' if yamal.get('automatic_lineup') else 'NO'}"
        )

        print(
            f"Fixture visible:       "
            f"{'SI' if yamal.get('has_visible_current_fixture') else 'NO'}"
        )

        print(
            f"Score base:            "
            f"{yamal.get('base_lineup_score'):.2f}"
        )

        print(
            f"Ajuste externo:        "
            f"{yamal.get('external_lineup_adjustment'):.2f}"
        )

        print(
            f"Score final:           "
            f"{yamal.get('lineup_score'):.2f}"
        )

        selected_ids = {
            int(
                player[
                    "id"
                ]
            )

            for player in lineup.get(
                "selected",
                [],
            )
        }

        print(
            f"En XI:                 "
            f"{'SI' if int(yamal['id']) in selected_ids else 'NO'}"
        )

    print()
    print_lineup_field(
        lineup
    )

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()
