from pprint import pprint

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def main() -> None:
    snapshot_file = get_latest_snapshot()

    print()
    print("=" * 70)
    print("       BORDALÁS IA - CONTEXTO DE COMPETICIÓN")
    print("=" * 70)
    print()
    print(f"Snapshot: {snapshot_file}")

    snapshot = load_snapshot(snapshot_file)

    competition = snapshot["catalog"]["data"]

    print()
    print("TEMPORADA")
    print("-" * 70)
    pprint(competition.get("season"))

    print()
    print("ACTIVE EVENTS")
    print("-" * 70)
    pprint(competition.get("activeEvents"))

    teams = competition.get("teams", {})

    print()
    print("EQUIPOS")
    print("-" * 70)
    print("Tipo:", type(teams).__name__)
    print("Número:", len(teams))

    print()
    print("PRIMEROS 3 EQUIPOS")
    print("-" * 70)

    if isinstance(teams, dict):
        for key, team in list(teams.items())[:3]:
            print()
            print("ID/clave:", key)
            pprint(team)

    elif isinstance(teams, list):
        for team in teams[:3]:
            print()
            pprint(team)


if __name__ == "__main__":
    main()