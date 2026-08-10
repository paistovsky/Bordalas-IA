from src.analysis.recommendation_engine import generate_recommendations


def calculate_bid_recommendations(snapshot: dict) -> list[dict]:
    recommendations = generate_recommendations(snapshot)

    balance = snapshot["market"]["status"]["balance"]
    maximum_bid = snapshot["market"]["status"]["maximumBid"]

    results = []

    for player in recommendations:
        market_price = player["market_price"]
        player_price = player["player_price"]
        final_score = player["final_score"]
        price_increment = player.get("price_increment", 0) or 0

        # --------------------------------------------------
        # PRIMA SEGÚN INTERÉS
        # --------------------------------------------------

        if final_score >= 80:
            premium = 0.08

        elif final_score >= 75:
            premium = 0.06

        elif final_score >= 65:
            premium = 0.04

        elif final_score >= 55:
            premium = 0.02

        else:
            premium = 0.00

        # --------------------------------------------------
        # PEQUEÑO BONUS SI EL JUGADOR ESTÁ SUBIENDO
        # --------------------------------------------------

        trend_bonus = 0

        if price_increment >= 100_000:
            trend_bonus = 0.02

        elif price_increment > 0:
            trend_bonus = 0.01

        # --------------------------------------------------
        # PRECIO BASE
        # --------------------------------------------------

        base_price = max(
            market_price,
            player_price,
        )

        suggested_bid = int(
            base_price * (1 + premium + trend_bonus)
        )

        # Redondeamos a bloques de 10.000 €
        suggested_bid = (
            round(suggested_bid / 10_000)
            * 10_000
        )

        # --------------------------------------------------
        # PROTECCIÓN DE PRESUPUESTO
        # --------------------------------------------------

        # En esta primera versión no queremos dedicar más
        # del 45% de nuestro saldo a un único jugador.
        budget_limit = int(balance * 0.45)

        affordable = (
            suggested_bid <= maximum_bid
            and suggested_bid <= budget_limit
        )

        # --------------------------------------------------
        # DECISIÓN
        # --------------------------------------------------

        if final_score < 55:
            action = "NO PUJAR"
            suggested_bid = 0

        elif not affordable:
            action = "DEMASIADO CARO"

        else:
            action = "PUJAR"

        results.append(
            {
                **player,

                "premium_percent": premium * 100,

                "trend_bonus_percent":
                    trend_bonus * 100,

                "suggested_bid": suggested_bid,

                "budget_limit": budget_limit,

                "affordable": affordable,

                "action": action,
            }
        )

    return results