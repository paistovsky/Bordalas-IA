from src.analysis.bid_engine import calculate_bid_recommendations


# Por ahora mantenemos un colchón del 20 % del saldo.
# Más adelante esto será configurable.
CASH_RESERVE_PERCENT = 0.20


def build_market_plan(snapshot: dict) -> dict:
    recommendations = calculate_bid_recommendations(snapshot)

    balance = snapshot["market"]["status"]["balance"]

    cash_reserve = int(balance * CASH_RESERVE_PERCENT)
    available_budget = balance - cash_reserve

    selected_bids = []
    rejected_bids = []

    committed = 0

    # El Bid Engine ya devuelve los jugadores ordenados
    # por puntuación.
    for player in recommendations:

        if player["action"] != "PUJAR":
            continue

        bid = player["suggested_bid"]

        if committed + bid <= available_budget:
            selected_bids.append(player)
            committed += bid

        else:
            rejected = {
                **player,
                "planner_reason": "Presupuesto insuficiente",
            }

            rejected_bids.append(rejected)

    remaining_budget = available_budget - committed

    return {
        "balance": balance,
        "cash_reserve": cash_reserve,
        "available_budget": available_budget,
        "committed": committed,
        "remaining_budget": remaining_budget,
        "selected_bids": selected_bids,
        "rejected_bids": rejected_bids,
    }