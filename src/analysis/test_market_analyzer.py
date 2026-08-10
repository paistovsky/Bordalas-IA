from src.analysis.market_analyzer import (
    load_snapshot,
    analyze_market,
)


SNAPSHOT = "data/snapshot_20260809_130856.json"


print("Cargando snapshot...")

snapshot = load_snapshot(SNAPSHOT)

print("Analizando mercado...")

results = analyze_market(snapshot)

print()
print("=" * 70)
print("BORDALÁS IA - ANÁLISIS DE MERCADO")
print("=" * 70)

print()
print(f"Jugadores analizados: {len(results)}")

print()
print("TOP OPORTUNIDADES")
print("-" * 70)

for player in results[:10]:

    print()
    print(
        f"{player['name']:<20}"
        f" {player['market_price']:>10,} €"
    )

    print(
        f"  Precio Biwenger:     "
        f"{player['player_price']:>10,} €"
    )

    print(
        f"  Diferencia:          "
        f"{player['price_difference']:>10,} € "
        f"({player['price_difference_percent']:+.1f}%)"
    )

    print(
        f"  Puntos 2025/26:      "
        f"{player['points_last_season'] or 0:>5}"
    )

    print(
        f"  Puntos/M€:           "
        f"{player['points_per_million']:.1f}"
    )

    print(
        f"  Score oportunidad:   "
        f"{player['opportunity_score']:>3}/100"
    )

    print(
        f"  >>> {player['recommendation']}"
    )