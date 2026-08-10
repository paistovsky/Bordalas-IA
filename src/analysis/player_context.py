from src.analysis.fixture_analyzer import get_team_fixture


def enrich_player_context(
    snapshot: dict,
    player: dict,
) -> dict:

    team_id = player["team_id"]

    fixture = get_team_fixture(
        snapshot,
        team_id,
        current_round_only=True,
    )

    # -----------------------------------------------
    # SIN PARTIDO EN LA JORNADA ACTUAL
    # -----------------------------------------------

    if (
        fixture is None
        or not fixture.get(
            "has_current_round_game",
            False,
        )
    ):
        return {
            **player,

            "has_current_round_game": False,

            "fixture_round": None,
            "fixture_side": None,

            "fixture_rival_id": None,
            "fixture_rival_name": None,

            "fixture_rating": None,

            "matchday_status":
                "SIN PARTIDO ESTA JORNADA",
        }

    # -----------------------------------------------
    # CON PARTIDO
    # -----------------------------------------------

    return {
        **player,

        "has_current_round_game": True,

        "fixture_round":
            fixture.get("round_id"),

        "fixture_side":
            fixture.get("side"),

        "fixture_rival_id":
            fixture.get("rival_id"),

        "fixture_rival_name":
            fixture.get("rival_name"),

        "fixture_rating":
            fixture.get("rating"),

        "matchday_status":
            "PARTIDO DISPONIBLE",
    }


def enrich_players_context(
    snapshot: dict,
    players: list[dict],
) -> list[dict]:

    return [
        enrich_player_context(
            snapshot,
            player,
        )
        for player in players
    ]