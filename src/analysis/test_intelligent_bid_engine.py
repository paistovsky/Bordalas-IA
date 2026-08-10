from src.analysis.intelligent_bid_engine import (
    calculate_intelligent_bids,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    results = (
        calculate_intelligent_bids(
            snapshot
        )
    )

    print()
    print("=" * 80)
    print(
        "       BORDALÁS IA - INTELLIGENT BID ENGINE"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()

    for player in results[:10]:

        print(
            player["name"].upper()
        )

        print(
            f"Score base:       "
            f"{player['base_score']:>3}/100"
        )

        print(
            f"Riesgo externo:   "
            f"-{player['external_risk']:>2}"
        )

        print(
            f"Score inteligente:"
            f" "
            f"{player['intelligent_score']:>3}/100"
        )

        status = player.get(
            "external_status"
        )

        if status:

            print(
                f"Estado externo:   "
                f"{status.get('status')}"
            )

            print(
                f"Datos en caché:   "
                f"{'SÍ' if status.get('external_from_cache') else 'NO'}"
            )

        if player[
            "suggested_bid"
        ]:

            print(
                f"Puja:             "
                f"{player['suggested_bid']:>10,} €"
            )

        print(
            f">>> {player['action']}"
        )

        print("-" * 80)


if __name__ == "__main__":
    main()