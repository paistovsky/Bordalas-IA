from __future__ import annotations

from src.analysis.fixture_analyzer import get_team_fixture

HOME_BONUS = 5.0
AWAY_BONUS = 0.0
UNKNOWN_BONUS = 0.0


def build_home_away_context(snapshot: dict, player: dict) -> dict:
    team_id = player.get("teamID")

    if team_id is None:
        return {
            "side": "unknown",
            "bonus": UNKNOWN_BONUS,
            "fixture_state": "UNKNOWN",
            "rival_name": None,
            "reason": "Jugador sin teamID.",
        }

    fixture = get_team_fixture(
        snapshot,
        int(team_id),
        current_round_only=True,
    )

    if not fixture:
        return {
            "side": "unknown",
            "bonus": UNKNOWN_BONUS,
            "fixture_state": "NOT_VISIBLE",
            "rival_name": None,
            "reason": "No hay fixture visible para la jornada actual.",
        }

    side = str(fixture.get("side") or "unknown").lower()

    if side == "home":
        bonus = HOME_BONUS
    elif side == "away":
        bonus = AWAY_BONUS
    else:
        bonus = UNKNOWN_BONUS

    return {
        "side": side,
        "bonus": float(bonus),
        "fixture_state": fixture.get("fixture_state"),
        "match_id": fixture.get("match_id"),
        "round_id": fixture.get("round_id"),
        "rival_id": fixture.get("rival_id"),
        "rival_name": fixture.get("rival_name"),
        "reason": (
            "Bonus contextual por jugar como local."
            if side == "home"
            else "Sin bonus de localia."
        ),
    }
