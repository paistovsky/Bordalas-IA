from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.team_analyzer import analyze_team


# Antes apuntaba a un snapshot del 09/08 que ya no
# existe: el test fallaba por un fichero borrado, no
# por el motor que pretende comprobar.
SNAPSHOT = get_latest_snapshot()


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