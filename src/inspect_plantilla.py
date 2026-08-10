import os

import requests
from dotenv import load_dotenv


load_dotenv()


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

username = os.getenv("BIWENGER_USERNAME")
password = os.getenv("BIWENGER_PASSWORD")

LEAGUE_ID = "2165477"
USER_ID = "14175949"


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

print()
print("=" * 60)
print("           BORDALÁS IA")
print("=" * 60)
print()

print("Conectando con Biwenger...")

login_response = requests.post(
    "https://biwenger.as.com/api/v2/auth/login",
    json={
        "email": username,
        "password": password,
    },
)

login_data = login_response.json()

if "token" not in login_data:
    print("ERROR: No se pudo iniciar sesión.")
    raise SystemExit(1)

token = login_data["token"]

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "X-Lang": "es",
    "Authorization": f"Bearer {token}",
    "X-League": LEAGUE_ID,
    "X-User": USER_ID,
}

print("Login correcto.")


# --------------------------------------------------
# OBTENER PLANTILLA
# --------------------------------------------------

response = requests.get(
    "https://biwenger.as.com/api/v2/user?fields=players(id,owner)",
    headers=headers,
)

if response.status_code != 200:
    print("ERROR obteniendo plantilla:", response.status_code)
    raise SystemExit(1)

players_data = response.json()["data"]["players"]

player_ids = [player["id"] for player in players_data]

print(f"Jugadores encontrados: {len(player_ids)}")


# --------------------------------------------------
# OBTENER CATÁLOGO
# --------------------------------------------------

print("Descargando catálogo de LaLiga...")

catalog_response = requests.get(
    "https://biwenger.as.com/api/v2/competitions/la-liga/data?lang=es&score=5",
    headers=headers,
)

if catalog_response.status_code != 200:
    print("ERROR obteniendo catálogo:", catalog_response.status_code)
    raise SystemExit(1)

catalog = catalog_response.json()["data"]["players"]


# --------------------------------------------------
# CONSTRUIR PLANTILLA
# --------------------------------------------------

my_players = []

for player_id in player_ids:

    player = catalog.get(str(player_id))

    if player is None:
        print(f"AVISO: jugador {player_id} no encontrado")
        continue

    my_players.append(player)


# --------------------------------------------------
# MOSTRAR PLANTILLA
# --------------------------------------------------

print()
print("=" * 60)
print("                    MI PLANTILLA")
print("=" * 60)

for player in my_players:

    print(
        f"{player['name']:<20} "
        f"ID: {player['id']:<6} "
        f"Precio: {player['price']:>10,} € "
        f"Puntos: {player['points']:>3}"
    )

print()
print("=" * 60)
print(f"TOTAL JUGADORES: {len(my_players)}")
print("=" * 60)