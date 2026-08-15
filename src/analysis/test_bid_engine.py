from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.bid_engine import calculate_bid_recommendations


# Antes apuntaba a un snapshot del 09/08 que ya no
# existe: el test fallaba por un fichero borrado, no
# por el motor que pretende comprobar.
SNAPSHOT = get_latest_snapshot()

snapshot = load_snapshot(SNAPSHOT)

results = calculate_bid_recommendations(snapshot)

balance = snapshot["market"]["status"]["balance"]
maximum_bid = snapshot["market"]["status"]["maximumBid"]


print()
print("=" * 75)
print("                 BORDALÁS IA - BID ENGINE")
print("=" * 75)

print()
print(f"Saldo:        {balance:,} €")
print(f"Puja máxima: {maximum_bid:,} €")

print()
print("RECOMENDACIONES")
print("=" * 75)


for player in results[:10]:

    print()
    print(player["name"].upper())

    print(
        f"Precio mercado:      "
        f"{player['market_price']:>11,} €"
    )

    print(
        f"Valor Biwenger:      "
        f"{player['player_price']:>11,} €"
    )

    print(
        f"Score final:         "
        f"{player['final_score']:>3}/100"
    )

    print(
        f"Tendencia diaria:    "
        f"{player['price_increment']:>+11,} €"
    )

    if player["suggested_bid"]:

        print(
            f"Puja recomendada:    "
            f"{player['suggested_bid']:>11,} €"
        )

    print()
    print(
        f">>> {player['action']}"
    )

    print("-" * 75)