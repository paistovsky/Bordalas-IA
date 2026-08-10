from src.analysis.lineup_engine import build_lineup
from src.analysis.team_analyzer import analyze_team


MIN_POSITION_COUNTS = {
    1: 1,  # Portero
    2: 4,  # Defensas
    3: 3,  # Centrocampistas
    4: 3,  # Delanteros
}


def analyze_sales(snapshot: dict) -> list[dict]:
    team = snapshot["my_team"]

    lineup = build_lineup(snapshot)
    team_analysis = analyze_team(snapshot)

    selected_ids = {
        player["id"]
        for player in lineup["selected"]
    }

    results = []

    for player in team:
        player_id = player["id"]
        position = player["position"]

        price = player.get("price", 0) or 0
        price_increment = player.get("priceIncrement", 0) or 0
        last_points = player.get("pointsLastSeason", 0) or 0

        position_count = (
            team_analysis["positions"]
            [position]
            ["count"]
        )

        in_lineup = (
            player_id
            in selected_ids
        )

        sale_score = 0
        reasons = []

        # --------------------------------------------------
        # NO ENTRA EN EL XI
        # --------------------------------------------------

        if not in_lineup:
            sale_score += 20
            reasons.append(
                "No entra en el XI actual"
            )

        # --------------------------------------------------
        # RENDIMIENTO HISTÓRICO
        # --------------------------------------------------

        if last_points < 50:
            sale_score += 25
            reasons.append(
                "Bajo rendimiento histórico"
            )

        elif last_points < 100:
            sale_score += 10
            reasons.append(
                "Rendimiento histórico limitado"
            )

        # --------------------------------------------------
        # TENDENCIA DE PRECIO
        # --------------------------------------------------

        if price_increment <= -100_000:
            sale_score += 25
            reasons.append(
                "Caída fuerte de valor"
            )

        elif price_increment < 0:
            sale_score += 10
            reasons.append(
                "Valor de mercado bajando"
            )

        # --------------------------------------------------
        # EXCESO DE JUGADORES EN POSICIÓN
        # --------------------------------------------------

        minimum_required = (
            MIN_POSITION_COUNTS[
                position
            ]
        )

        surplus = (
            position_count
            - minimum_required
        )

        if surplus >= 2:
            sale_score += 15
            reasons.append(
                "Hay margen en esta posición"
            )

        elif surplus >= 1:
            sale_score += 5

        # --------------------------------------------------
        # ACTIVO DE BAJO IMPACTO
        # --------------------------------------------------

        if (
            price <= 300_000
            and last_points < 50
        ):
            sale_score += 10
            reasons.append(
                "Activo de poco impacto deportivo"
            )

        # --------------------------------------------------
        # PENALIZACIÓN POR SER IMPORTANTE
        # --------------------------------------------------

        if in_lineup:
            sale_score -= 15

        sale_score = max(
            sale_score,
            0,
        )

        # --------------------------------------------------
        # CLASIFICACIÓN
        # --------------------------------------------------

        if sale_score >= 60:
            recommendation = "VENDER"

        elif sale_score >= 40:
            recommendation = "CONSIDERAR VENTA"

        elif sale_score >= 20:
            recommendation = "VIGILAR"

        else:
            recommendation = "MANTENER"

        results.append(
            {
                "id":
                    player_id,

                "name":
                    player["name"],

                "position":
                    position,

                "price":
                    price,

                "price_increment":
                    price_increment,

                "points_last_season":
                    last_points,

                "in_lineup":
                    in_lineup,

                "position_count":
                    position_count,

                "minimum_required":
                    minimum_required,

                "sale_score":
                    sale_score,

                "recommendation":
                    recommendation,

                "reasons":
                    reasons,
            }
        )

    results.sort(
        key=lambda player:
            player["sale_score"],
        reverse=True,
    )

    return results