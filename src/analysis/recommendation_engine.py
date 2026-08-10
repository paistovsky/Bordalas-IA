from src.analysis.lineup_engine import build_lineup
from src.analysis.market_analyzer import analyze_market
from src.analysis.player_context import enrich_players_context
from src.analysis.team_analyzer import analyze_team


TARGET_COUNTS = {
    1: 2,  # Porteros
    2: 5,  # Defensas
    3: 5,  # Centrocampistas
    4: 4,  # Delanteros
}


def calculate_position_need(
    team_analysis: dict,
) -> dict[int, int]:
    needs = {}

    for position_id, target in TARGET_COUNTS.items():
        current = (
            team_analysis["positions"]
            [position_id]
            ["count"]
        )

        missing = max(
            target - current,
            0,
        )

        if missing >= 2:
            needs[position_id] = 25
        elif missing == 1:
            needs[position_id] = 15
        else:
            needs[position_id] = 0

    return needs


def calculate_matchday_need(
    snapshot: dict,
) -> dict[int, int]:
    lineup = build_lineup(snapshot)

    shortages = lineup[
        "matchday_shortages"
    ]

    needs = {}

    for position_id, missing in shortages.items():

        if missing >= 2:
            needs[position_id] = 30

        elif missing == 1:
            needs[position_id] = 25

        else:
            needs[position_id] = 0

    return needs


def generate_recommendations(
    snapshot: dict,
) -> list[dict]:

    market_players = analyze_market(
        snapshot
    )

    market_players = enrich_players_context(
        snapshot,
        market_players,
    )

    team = analyze_team(snapshot)

    position_needs = (
        calculate_position_need(
            team
        )
    )

    matchday_needs = (
        calculate_matchday_need(
            snapshot
        )
    )

    recommendations = []

    for player in market_players:

        position = player["position"]

        market_score = (
            player["opportunity_score"]
        )

        structural_need_score = (
            position_needs.get(
                position,
                0,
            )
        )

        matchday_need_score = 0

        if player[
            "has_current_round_game"
        ]:
            matchday_need_score = (
                matchday_needs.get(
                    position,
                    0,
                )
            )

        final_score = min(
            market_score
            + structural_need_score
            + matchday_need_score,
            100,
        )

        if final_score >= 80:
            decision = "PRIORIDAD MUY ALTA"

        elif final_score >= 70:
            decision = "PRIORIDAD ALTA"

        elif final_score >= 55:
            decision = "INTERESANTE"

        elif final_score >= 35:
            decision = "VIGILAR"

        else:
            decision = "DESCARTAR"

        recommendations.append(
            {
                **player,

                "structural_need_score":
                    structural_need_score,

                "matchday_need_score":
                    matchday_need_score,

                "final_score":
                    final_score,

                "decision":
                    decision,
            }
        )

    recommendations.sort(
        key=lambda player:
            player["final_score"],
        reverse=True,
    )

    return recommendations