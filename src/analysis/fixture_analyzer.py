def get_current_round_id(snapshot: dict) -> int | None:
    return (
        snapshot
        .get("rounds", {})
        .get("data", {})
        .get("round", {})
        .get("id")
    )


def get_team(snapshot: dict, team_id: int) -> dict | None:
    teams = snapshot["catalog"]["data"]["teams"]

    return teams.get(str(team_id))


def get_team_name(snapshot: dict, team_id: int) -> str:
    team = get_team(snapshot, team_id)

    if not team:
        return f"Equipo {team_id}"

    return team.get("name", f"Equipo {team_id}")


def get_team_fixture(
    snapshot: dict,
    team_id: int,
    current_round_only: bool = True,
) -> dict | None:

    team = get_team(snapshot, team_id)

    if not team:
        return None

    games = team.get("nextGames", [])

    if not games:
        return None

    current_round_id = get_current_round_id(snapshot)

    selected_game = None

    if current_round_only and current_round_id is not None:
        for game in games:
            if (
                game.get("round", {}).get("id")
                == current_round_id
            ):
                selected_game = game
                break
    else:
        selected_game = games[0]

    if selected_game is None:
        return {
            "has_current_round_game": False,
            "current_round_id": current_round_id,
            "team_id": team_id,
            "team_name": get_team_name(
                snapshot,
                team_id,
            ),
        }

    home = selected_game.get("home", {})
    away = selected_game.get("away", {})

    if home.get("id") == team_id:
        side = "home"
        our_data = home
        rival_data = away

    elif away.get("id") == team_id:
        side = "away"
        our_data = away
        rival_data = home

    else:
        return None

    rival_id = rival_data.get("id")

    difficulty = our_data.get(
        "difficulty",
        {},
    )

    return {
        "has_current_round_game": True,

        "match_id": selected_game.get("id"),
        "round_id": (
            selected_game
            .get("round", {})
            .get("id")
        ),

        "date": selected_game.get("date"),

        "side": side,

        "team_id": team_id,
        "team_name": get_team_name(
            snapshot,
            team_id,
        ),

        "rival_id": rival_id,
        "rival_name": get_team_name(
            snapshot,
            rival_id,
        ),

        "rating": difficulty.get("rating"),
        "form": difficulty.get("form"),
        "standings": difficulty.get("standings"),
        "home_away": difficulty.get("homeAway"),
        "goal_diff": difficulty.get("goalDiff"),
    }