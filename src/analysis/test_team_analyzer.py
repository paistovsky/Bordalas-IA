from src.analysis.market_analyzer import load_snapshot
from src.analysis.team_analyzer import analyze_team


SNAPSHOT = "data/snapshot_20260809_130856.json"


print()
print("=" * 70)
print("             BORDALÁS IA - TEAM ANALYZER")
print("=" * 70)

snapshot = load_snapshot(SNAPSHOT)

result = analyze_team(snapshot)

print()
print(f"Jugadores totales: {result['total_players']}")
print(f"Valor plantilla:   {result['total_value']:,} €")

print()
print("DISTRIBUCIÓN DE PLANTILLA")
print("-" * 70)

for position_id, info in result["positions"].items():

    print()
    print(
        f"{info['name']:<16}"
        f" Jugadores: {info['count']:<2}"
        f" Valor: {info['value']:>10,} €"
        f" Puntos 25/26: {info['points_last_season']:>4}"
    )

    for player in info["players"]:
        print(
            f"   - {player['name']:<20}"
            f"{player['price']:>10,} €"
        )