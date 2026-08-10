from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.intelligence.player_status import (
    build_player_status,
)


snapshot_file = get_latest_snapshot()
snapshot = load_snapshot(snapshot_file)

catalog = (
    snapshot["catalog"]
    ["data"]
    ["players"]
)


print()
print("=" * 80)
print("       BORDALÁS IA - PLAYER INTELLIGENCE")
print("=" * 80)

print()
print(f"Snapshot: {snapshot_file}")
print()


# Probamos con Pépé
player = catalog["34479"]


status = build_player_status(
    player
)


print(player["name"].upper())

print(
    f"Club ID:           "
    f"{status['team_id']}"
)

print(
    f"Estado Biwenger:   "
    f"{status['biwenger_status']}"
)

print(
    f"Fitness:           "
    f"{status['fitness']}"
)

print(
    f"Risk score:        "
    f"{status['risk_score']}/100"
)

print(
    f"Estado IA:         "
    f"{status['status']}"
)

if status["alerts"]:

    print()
    print("ALERTAS")

    for alert in status["alerts"]:
        print(
            f"- {alert}"
        )