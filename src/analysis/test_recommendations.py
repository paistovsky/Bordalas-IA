from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.recommendation_engine import (
    generate_recommendations,
)


snapshot_file = get_latest_snapshot()
snapshot = load_snapshot(snapshot_file)

results = generate_recommendations(
    snapshot
)


print()
print("=" * 80)
print("         BORDALÁS IA - RECOMENDACIONES v2")
print("=" * 80)

print()
print(
    f"Snapshot: {snapshot_file}"
)

print()


for player in results[:12]:

    print(player["name"].upper())

    print(
        f"Precio mercado:       "
        f"{player['market_price']:>10,} €"
    )

    print(
        f"Score mercado:        "
        f"{player['opportunity_score']:>3}"
    )

    print(
        f"Necesidad plantilla:  "
        f"+{player['structural_need_score']}"
    )

    print(
        f"Urgencia jornada:     "
        f"+{player['matchday_need_score']}"
    )

    print(
        f"Tiene partido:        "
        f"{'SÍ' if player['has_current_round_game'] else 'NO'}"
    )

    print(
        f"SCORE FINAL:          "
        f"{player['final_score']:>3}/100"
    )

    print(
        f">>> {player['decision']}"
    )

    print("-" * 80)