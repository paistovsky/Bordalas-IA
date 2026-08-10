POSITION_NAMES = {
    1: "Portero",
    2: "Defensa",
    3: "Centrocampista",
    4: "Delantero",
}


def analyze_team(snapshot: dict) -> dict:
    team = snapshot["my_team"]

    positions = {
        1: [],
        2: [],
        3: [],
        4: [],
    }

    total_value = 0

    for player in team:
        position = player.get("position")
        price = player.get("price", 0) or 0

        total_value += price

        if position in positions:
            positions[position].append(player)

    position_summary = {}

    for position_id, players in positions.items():

        value = sum(
            player.get("price", 0) or 0
            for player in players
        )

        last_season_points = sum(
            player.get("pointsLastSeason", 0) or 0
            for player in players
        )

        position_summary[position_id] = {
            "name": POSITION_NAMES[position_id],
            "count": len(players),
            "value": value,
            "points_last_season": last_season_points,
            "players": players,
        }

    return {
        "total_players": len(team),
        "total_value": total_value,
        "positions": position_summary,
    }