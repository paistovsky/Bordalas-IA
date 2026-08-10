import json
from datetime import datetime
from pathlib import Path

from src.biwenger.client import BiwengerClient


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def collect_league_snapshot() -> None:
    client = BiwengerClient()

    print("Iniciando sesión...")
    client.login()

    print("Seleccionando liga...")
    league = client.select_league()

    print("Obteniendo información de la jornada...")
    rounds = client.session.get(
        f"{client.BASE_URL}/rounds/league"
    )
    rounds.raise_for_status()
    rounds_data = rounds.json()

    print("Obteniendo mercado...")
    market = client.get_market()

    print("Obteniendo plantilla...")
    team = client.get_my_team()

    print("Obteniendo catálogo de jugadores...")
    catalog_response = client.session.get(
        f"{client.BASE_URL}/competitions/la-liga/data",
        params={
            "lang": "es",
            "score": 5,
        },
    )
    catalog_response.raise_for_status()
    catalog = catalog_response.json()

    snapshot = {
        "timestamp": datetime.now().isoformat(),

        "league": league,

        "rounds": rounds_data,

        "market": market,

        "my_team": team,

        "catalog": catalog,
    }

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = DATA_DIR / f"snapshot_{timestamp}.json"

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            snapshot,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # --------------------------------------------------
    # RESUMEN
    # --------------------------------------------------

    round_id = (
        rounds_data
        .get("data", {})
        .get("round", {})
        .get("id", "desconocida")
    )

    sales = market.get("sales", [])

    balance = (
        market
        .get("status", {})
        .get("balance", 0)
    )

    maximum_bid = (
        market
        .get("status", {})
        .get("maximumBid", 0)
    )

    catalog_players = (
        catalog
        .get("data", {})
        .get("players", {})
    )

    print()
    print("=" * 60)
    print("BORDALÁS IA - SNAPSHOT GUARDADO")
    print("=" * 60)
    print()
    print(f"Jornada:          {round_id}")
    print(f"Plantilla:        {len(team)} jugadores")
    print(f"Mercado:          {len(sales)} jugadores")
    print(f"Catálogo:         {len(catalog_players)} jugadores")
    print(f"Saldo:            {balance:,} €")
    print(f"Puja máxima:      {maximum_bid:,} €")
    print()
    print(f"Archivo: {filename}")