from src.analysis.lineup_engine import build_lineup
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


POSITION_NAMES = {
    1: "PORTERO",
    2: "DEFENSA",
    3: "CENTROCAMPISTA",
    4: "DELANTERO",
}


snapshot_file = get_latest_snapshot()
snapshot = load_snapshot(snapshot_file)

result = build_lineup(snapshot)


print()
print("=" * 80)
print("           BORDALÁS IA - LINEUP ENGINE v2")
print("=" * 80)

print()
print(f"Snapshot: {snapshot_file}")

print()
print(
    f"Jugadores alineados: "
    f"{result['total_selected']}/11"
)

print(
    f"Con partido:         "
    f"{result['playable_count']}/11"
)

print(
    f"Sin partido:         "
    f"{result['unavailable_count']}/11"
)


for position_id in [
    1,
    2,
    3,
    4,
]:

    print()
    print(
        POSITION_NAMES[position_id]
    )
    print("-" * 80)

    players = [
        player
        for player in result["selected"]
        if player[
            "lineup_position"
        ] == position_id
    ]

    for player in players:

        game = (
            "✅ PARTIDO"
            # has_game se renombro a counts_for_round.
            if player.get("counts_for_round", True)
            else "⚠ SIN PARTIDO"
        )

        positions = (
            player[
                "eligible_positions"
            ]
        )

        multi_position = ""

        if len(positions) > 1:
            multi_position = (
                f" MultiPos:{positions}"
            )

        print(
            f"{player['name']:<22}"
            f"{game:<18}"
            f"{multi_position}"
        )


print()
print("=" * 80)
print("NECESIDADES URGENTES PARA LA JORNADA")
print("=" * 80)

total_shortages = 0

for position_id, missing in (
    result[
        "matchday_shortages"
    ].items()
):

    total_shortages += missing

    print(
        f"{POSITION_NAMES[position_id]:<18}"
        f"{missing}"
    )


print()
print("-" * 80)

if total_shortages == 0:

    print(
        "✅ Puedes presentar un once "
        "completo con partido."
    )

else:

    print(
        f"⚠ Faltan {total_shortages} "
        "jugadores con partido para "
        "tener un XI completo."
    )

print()
print("=" * 80)