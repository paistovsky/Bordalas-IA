from src.analysis.fixture_analyzer import (
    get_current_round_id,
    get_team_fixture,
)
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    current_round = get_current_round_id(
        snapshot
    )

    market = snapshot["market"]

    catalog = (
        snapshot["catalog"]
        ["data"]
        ["players"]
    )

    sales = market.get("sales", [])

    print()
    print("=" * 80)
    print("BORDALÁS IA - FIXTURE ANALYZER v2")
    print("=" * 80)

    print()
    print(f"Snapshot:       {snapshot_file}")
    print(f"Jornada actual: {current_round}")
    print()

    for index, sale in enumerate(
        sales,
        start=1,
    ):
        player_id = str(
            sale["player"]["id"]
        )

        player = catalog.get(player_id)

        if player is None:
            continue

        team_id = player["teamID"]

        fixture = get_team_fixture(
            snapshot,
            team_id,
            current_round_only=True,
        )

        print(
            f"{index:>2}. "
            f"{player['name']:<20}"
        )

        if (
            fixture is None
            or not fixture.get(
                "has_current_round_game",
                False,
            )
        ):
            print(
                "    ⚠ SIN PARTIDO "
                "EN LA JORNADA ACTUAL"
            )
            print("-" * 80)
            continue

        print(
            f"    "
            f"{fixture['team_name']}"
            f" vs "
            f"{fixture['rival_name']}"
        )

        print(
            f"    Localía: "
            f"{fixture['side']}"
        )

        print(
            f"    Rating: "
            f"{fixture['rating']}"
        )

        print(
            f"    Form: "
            f"{fixture['form']}"
        )

        print(
            f"    Standings: "
            f"{fixture['standings']}"
        )

        print(
            f"    Home/Away: "
            f"{fixture['home_away']}"
        )

        print(
            f"    Goal diff: "
            f"{fixture['goal_diff']}"
        )

        print("-" * 80)


if __name__ == "__main__":
    main()