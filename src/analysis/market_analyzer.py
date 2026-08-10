import json
from pathlib import Path


def load_snapshot(filename: str) -> dict:
    path = Path(filename)

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_latest_snapshot(directory: str = "data") -> str:
    data_dir = Path(directory)

    snapshots = sorted(
        data_dir.glob("snapshot_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not snapshots:
        raise FileNotFoundError(
            "No se ha encontrado ningún snapshot en data/"
        )

    return str(snapshots[0])


def analyze_market(snapshot: dict) -> list[dict]:
    market = snapshot["market"]
    catalog = snapshot["catalog"]["data"]["players"]

    analyzed = []

    for sale in market.get("sales", []):
        player_id = str(sale["player"]["id"])

        player = catalog.get(player_id)

        if not player:
            continue

        market_price = sale["price"]
        player_price = player["price"]

        points = player.get("points", 0) or 0
        last_season_points = player.get("pointsLastSeason")

        price_difference = market_price - player_price

        # Diferencia porcentual respecto al precio oficial
        if player_price > 0:
            price_difference_percent = (
                price_difference / player_price
            ) * 100
        else:
            price_difference_percent = 0

        # Puntos de la temporada anterior por millón de euros
        if market_price > 0 and last_season_points:
            points_per_million = (
                last_season_points
                / (market_price / 1_000_000)
            )
        else:
            points_per_million = 0

        # ---------------------------------------------------------
        # PUNTUACIÓN DE OPORTUNIDAD
        # ---------------------------------------------------------

        opportunity_score = 0

        # Muchos puntos históricos = positivo
        if last_season_points:
            if last_season_points >= 200:
                opportunity_score += 40
            elif last_season_points >= 150:
                opportunity_score += 30
            elif last_season_points >= 100:
                opportunity_score += 20
            elif last_season_points >= 50:
                opportunity_score += 10

        # Comprar por debajo del precio oficial = positivo
        if price_difference_percent <= -15:
            opportunity_score += 30
        elif price_difference_percent <= -10:
            opportunity_score += 25
        elif price_difference_percent <= -5:
            opportunity_score += 15
        elif price_difference_percent < 0:
            opportunity_score += 5

        # Buena relación puntos/precio
        if points_per_million >= 30:
            opportunity_score += 30
        elif points_per_million >= 25:
            opportunity_score += 25
        elif points_per_million >= 20:
            opportunity_score += 20
        elif points_per_million >= 15:
            opportunity_score += 10

        # ---------------------------------------------------------
        # RECOMENDACIÓN
        # ---------------------------------------------------------

        if opportunity_score >= 70:
            recommendation = "MUY INTERESANTE"
        elif opportunity_score >= 50:
            recommendation = "INTERESANTE"
        elif opportunity_score >= 30:
            recommendation = "VIGILAR"
        else:
            recommendation = "NO PRIORITARIO"

        analyzed.append(
            {
                "id": player["id"],
                "name": player["name"],
                "team_id": player["teamID"],
                "position": player["position"],
                "alt_positions": player.get(
                    "altPositions", []
                ),

                "market_price": market_price,
                "player_price": player_price,
                "price_difference": price_difference,
                "price_difference_percent":
                    price_difference_percent,

                "points": points,
                "points_last_season":
                    last_season_points,

                "points_per_million":
                    points_per_million,

                "price_increment": player.get(
                    "priceIncrement", 0
                ),

                "status": player.get("status"),

                "market_until": sale.get("until"),
                "extended": sale.get(
                    "extended", False
                ),

                "opportunity_score":
                    opportunity_score,

                "recommendation":
                    recommendation,
            }
        )

    # Ordenamos por oportunidad
    analyzed.sort(
        key=lambda player:
            player["opportunity_score"],
        reverse=True,
    )

    return analyzed