from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.strategy_planner import build_market_plan


snapshot_file = get_latest_snapshot()

print()
print("=" * 75)
print("              BORDALÁS IA - PLAN DE MERCADO")
print("=" * 75)
print()
print(f"Snapshot utilizado: {snapshot_file}")

snapshot = load_snapshot(snapshot_file)

plan = build_market_plan(snapshot)

print()
print(f"Saldo actual:           {plan['balance']:>12,} €")
print(f"Reserva de seguridad:  {plan['cash_reserve']:>12,} €")
print(f"Presupuesto operativo: {plan['available_budget']:>12,} €")

print()
print("PUJAS SELECCIONADAS")
print("-" * 75)

if not plan["selected_bids"]:
    print("Ninguna.")

for player in plan["selected_bids"]:
    print(
        f"{player['name']:<22}"
        f"{player['suggested_bid']:>12,} €"
        f"   Score {player['final_score']:>3}/100"
    )

print()
print("-" * 75)

print(f"Comprometido:           {plan['committed']:>12,} €")
print(f"Disponible restante:    {plan['remaining_budget']:>12,} €")

if plan["rejected_bids"]:
    print()
    print("PUJAS DESCARTADAS POR PRESUPUESTO")
    print("-" * 75)

    for player in plan["rejected_bids"]:
        print(
            f"{player['name']:<22}"
            f"{player['suggested_bid']:>12,} €"
            f"   {player['planner_reason']}"
        )

print()
print("=" * 75)