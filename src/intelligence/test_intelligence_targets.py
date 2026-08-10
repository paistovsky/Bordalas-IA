from src.analysis.bid_engine import (
    calculate_bid_recommendations,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.intelligence.bulk_player_mapper import (
    map_player,
)


def print_mapping(
    mapping: dict,
) -> None:

    print(
        f"   Biwenger:      "
        f"{mapping.get('biwenger_name')}"
    )

    print(
        f"   Club:          "
        f"{mapping.get('biwenger_team')}"
    )

    print(
        f"   Externo:       "
        f"{mapping.get('external_name')}"
    )

    print(
        f"   External ID:   "
        f"{mapping.get('external_id')}"
    )

    print(
        f"   Confianza:     "
        f"{mapping.get('confidence', 0):.2f}"
    )

    print(
        f"   Nivel:         "
        f"{mapping.get('confidence_level')}"
    )

    print(
        f"   Uso automático:"
        f" "
        f"{'SÍ' if mapping.get('safe_for_automatic_use') else 'NO'}"
    )

    print(
        f"   Caché:         "
        f"{'SÍ' if mapping.get('from_cache') else 'NO'}"
    )


def main() -> None:

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(
        snapshot_file
    )

    print()
    print("=" * 80)
    print(
        "       BORDALÁS IA - INTELLIGENCE TARGETS"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    # ==================================================
    # MI PLANTILLA
    # ==================================================

    print()
    print("=" * 80)
    print("MI PLANTILLA")
    print("=" * 80)

    team = snapshot["my_team"]

    for index, player in enumerate(
        team,
        start=1,
    ):

        print()
        print(
            f"{index}. {player['name']}"
        )

        try:
            mapping = map_player(
                snapshot,
                player,
            )

            print_mapping(
                mapping
            )

        except Exception as error:

            print(
                f"   ERROR: "
                f"{type(error).__name__}: "
                f"{error}"
            )

        print("-" * 80)

    # ==================================================
    # MERCADO RELEVANTE
    # ==================================================

    print()
    print("=" * 80)
    print("CANDIDATOS DEL MERCADO")
    print("=" * 80)

    recommendations = (
        calculate_bid_recommendations(
            snapshot
        )
    )

    candidates = [
        player
        for player in recommendations
        if player["action"] == "PUJAR"
    ]

    print()
    print(
        f"Candidatos a puja: "
        f"{len(candidates)}"
    )

    for index, player in enumerate(
        candidates,
        start=1,
    ):

        print()
        print(
            f"{index}. {player['name']}"
        )

        print(
            f"   Score:         "
            f"{player['final_score']}/100"
        )

        print(
            f"   Puja sugerida: "
            f"{player['suggested_bid']:,} €"
        )

        try:
            mapping = map_player(
                snapshot,
                player,
            )

            print_mapping(
                mapping
            )

        except Exception as error:

            print(
                f"   ERROR: "
                f"{type(error).__name__}: "
                f"{error}"
            )

        print("-" * 80)


if __name__ == "__main__":
    main()