from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.portfolio_optimizer import optimize_portfolio


snapshot_file = get_latest_snapshot()

print()
print("=" * 75)
print("           BORDALÁS IA - PORTFOLIO OPTIMIZER")
print("=" * 75)

print()
print(f"Snapshot utilizado: {snapshot_file}")

snapshot = load_snapshot(snapshot_file)

result = optimize_portfolio(snapshot)

print()
print(f"Saldo:                 {result['balance']:>12,} €")
print(f"Reserva:               {result['cash_reserve']:>12,} €")
print(f"Presupuesto operativo: {result['available_budget']:>12,} €")

print()
print("COMBINACIÓN ÓPTIMA")
print("-" * 75)

if not result["selected"]:
    print("No se ha encontrado ninguna combinación válida.")

for player in result["selected"]:

    print(
        f"{player['name']:<22}"
        f"{player['suggested_bid']:>12,} €"
        f"   Score {player['final_score']:>3}/100"
    )

print()
print("-" * 75)

print(
    f"Coste total:           "
    f"{result['total_cost']:>12,} €"
)

print(
    f"Presupuesto restante:  "
    f"{result['remaining_budget']:>12,} €"
)

print(
    f"Portfolio score:       "
    f"{result['portfolio_score']:.2f}"
)

if result["rejected"]:

    print()
    print("OTROS CANDIDATOS")
    print("-" * 75)

    for player in result["rejected"]:

        print(
            f"{player['name']:<22}"
            f"{player['suggested_bid']:>12,} €"
            f"   Score {player['final_score']:>3}/100"
        )

print()
print("=" * 75)