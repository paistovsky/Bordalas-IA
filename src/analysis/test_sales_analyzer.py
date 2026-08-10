from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.sales_analyzer import analyze_sales


snapshot_file = get_latest_snapshot()
snapshot = load_snapshot(snapshot_file)

results = analyze_sales(snapshot)


print()
print("=" * 80)
print("             BORDALÁS IA - SALES ANALYZER")
print("=" * 80)

print()
print(f"Snapshot: {snapshot_file}")
print()

for player in results:

    print(player["name"].upper())

    print(
        f"Valor:             "
        f"{player['price']:>10,} €"
    )

    print(
        f"Tendencia:         "
        f"{player['price_increment']:>+10,} €"
    )

    print(
        f"Puntos 25/26:      "
        f"{player['points_last_season']:>4}"
    )

    print(
        f"En XI propuesto:    "
        f"{'SÍ' if player['in_lineup'] else 'NO'}"
    )

    print(
        f"Sale score:         "
        f"{player['sale_score']:>3}/100"
    )

    print(
        f">>> {player['recommendation']}"
    )

    if player["reasons"]:
        print("Motivos:")

        for reason in player["reasons"]:
            print(
                f"  - {reason}"
            )

    print("-" * 80)