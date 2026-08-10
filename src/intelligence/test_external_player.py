from src.intelligence.injuries import (
    get_player_sidelined,
)
from src.intelligence.player_mapper import (
    find_external_player,
)
from src.intelligence.transfers import (
    get_player_transfers,
)


PLAYER_NAME = "Pépé"
EXPECTED_TEAM = "Villarreal"


print()
print("=" * 80)
print("       BORDALÁS IA - EXTERNAL PLAYER TEST v2")
print("=" * 80)

print()
print(f"Jugador Biwenger: {PLAYER_NAME}")
print(f"Club esperado:     {EXPECTED_TEAM}")

match = find_external_player(
    PLAYER_NAME,
    EXPECTED_TEAM,
)

if match is None:
    raise SystemExit(
        "No se ha encontrado un match fiable."
    )


print()
print("MATCH ENCONTRADO")
print("-" * 80)

print(
    f"Nombre externo:   "
    f"{match['external_name']}"
)

print(
    f"External ID:      "
    f"{match['external_id']}"
)

print(
    f"Equipos:          "
    f"{match['teams']}"
)

print(
    f"Similitud nombre: "
    f"{match['name_score']:.2f}"
)

print(
    f"Bonus club:       "
    f"{match['team_bonus']:.2f}"
)

print(
    f"Confianza total:  "
    f"{match['total_score']:.2f}"
)


external_id = match[
    "external_id"
]


print()
print("=" * 80)
print("SIDELINED")
print("=" * 80)

sidelined = get_player_sidelined(
    external_id
)

print(
    f"Registros: {len(sidelined)}"
)

for item in sidelined[:10]:
    print(item)


print()
print("=" * 80)
print("TRANSFERS")
print("=" * 80)

transfers = get_player_transfers(
    external_id
)

print(
    f"Registros: {len(transfers)}"
)

for item in transfers[:5]:
    print(item)