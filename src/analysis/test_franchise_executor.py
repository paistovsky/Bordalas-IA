from src.actions.franchise_executor import (
    run_franchise_dry_run,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
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

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    run_franchise_dry_run(
        snapshot
    )


if __name__ == "__main__":
    main()