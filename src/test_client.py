from src.biwenger.client import BiwengerClient


print()
print("=" * 60)
print("              BORDALÁS IA")
print("=" * 60)
print()

client = BiwengerClient()

print("1. Iniciando sesión...")
client.login()
print("   OK")

print("2. Seleccionando liga...")
league = client.select_league()

print(f"   Liga: {league['name']}")
print(f"   ID: {league['id']}")

print("3. Obteniendo plantilla...")
team = client.get_my_team()

print(f"   Jugadores: {len(team)}")

print()

print("4. Plantilla:")

for player in team:
    print(
        f"   {player['name']:<20}"
        f"{player['price']:>12,} €"
        f"   {player['points']:>3} puntos"
    )

print()

print("5. Consultando mercado...")
market = client.get_market()

sales = market.get("sales", [])

print(f"   Jugadores en mercado: {len(sales)}")
print(f"   Saldo: {market['status']['balance']:,} €")
print(f"   Puja máxima: {market['status']['maximumBid']:,} €")

print()
print("=" * 60)
print("        BORDALÁS IA: CLIENTE OK")
print("=" * 60)