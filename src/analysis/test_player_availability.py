from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.player_availability import (
    analyze_player_availability,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    print()
    print("=" * 80)
    print(
        "       BORDALÁS IA - PLAYER AVAILABILITY"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()

    for player in snapshot[
        "my_team"
    ]:

        availability = (
            analyze_player_availability(
                player
            )
        )

        print(
            f"{player['name']:<22}"
            f"{availability['label']:<14}"
            f"Status: "
            f"{availability['status']:<12}"
            f"Risk: "
            f"{availability['risk']:>3}/100"
        )

        if availability[
            "status_info"
        ]:

            print(
                "   "
                f"{availability['status_info']}"
            )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()