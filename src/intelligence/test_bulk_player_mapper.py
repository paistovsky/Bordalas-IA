from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.intelligence.bulk_player_mapper import (
    map_player,
)


def main():
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    team = snapshot["my_team"]

    print()
    print("=" * 80)
    print("          BORDALÁS IA - BULK PLAYER MAPPER v2")
    print("=" * 80)

    print()
    print(f"Snapshot: {snapshot_file}")
    print()

    for index, player in enumerate(
        team[:5],
        start=1,
    ):

        print(
            f"{index}. {player['name']}"
        )

        mapping = map_player(
            snapshot,
            player,
        )

        print(
            f"   Club Biwenger: "
            f"{mapping.get('biwenger_team')}"
        )

        print(
            f"   Nombre externo: "
            f"{mapping.get('external_name')}"
        )

        print(
            f"   External ID: "
            f"{mapping.get('external_id')}"
        )

        print(
            f"   Confianza: "
            f"{mapping.get('confidence', 0):.2f}"
        )

        print(
            f"   Nivel: "
            f"{mapping.get('confidence_level')}"
        )

        print(
            f"   Uso automático: "
            f"{'SÍ' if mapping.get('safe_for_automatic_use') else 'NO'}"
        )

        print(
            f"   Caché: "
            f"{'SÍ' if mapping.get('from_cache') else 'NO'}"
        )

        print("-" * 80)


if __name__ == "__main__":
    main()