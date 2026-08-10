from src.analysis.market_analyzer import (
    analyze_market,
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.player_context import (
    enrich_players_context,
)


snapshot_file = get_latest_snapshot()
snapshot = load_snapshot(snapshot_file)

players = analyze_market(snapshot)

players = enrich_players_context(
    snapshot,
    players,
)


print()
print("=" * 80)
print("             BORDALÁS IA - PLAYER CONTEXT")
print("=" * 80)

print()
print(f"Snapshot: {snapshot_file}")

print()


for player in players:

    print(player["name"].upper())

    print(
        f"Precio:           "
        f"{player['market_price']:>10,} €"
    )

    print(
        f"Score mercado:    "
        f"{player['opportunity_score']:>3}/100"
    )

    print(
        f"Jornada actual:   "
        f"{player['matchday_status']}"
    )

    if player["has_current_round_game"]:

        side = (
            "LOCAL"
            if player["fixture_side"] == "home"
            else "VISITANTE"
        )

        print(
            f"Rival:            "
            f"{player['fixture_rival_name']}"
        )

        print(
            f"Condición:        {side}"
        )

        print(
            f"Rating Biwenger:  "
            f"{player['fixture_rating']}"
        )

    print("-" * 80)