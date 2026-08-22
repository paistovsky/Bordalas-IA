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

    # ==================================================
    # LA ALINEACION DE VERDAD (22/08/2026)
    # ==================================================
    #
    # `rounds/league` trae el once que quedo CONGELADO en una
    # jornada ya jugada. No es el que hay puesto para la que
    # viene, y usarlo para comprobar lo que hay en Biwenger hacia
    # que el cartel de divergencia estuviese rojo para siempre:
    # el dueño tenia su 4-4-2 correcto y se le decia que le
    # faltaba un jugador que compro despues de aquella jornada.
    #
    # Pepe escribe el once con `PUT /user?fields=*,lineup(date)`.
    # Se lee del mismo sitio, que es la unica forma de que
    # read-before-write signifique algo.
    #
    # Si falla no se tumba el ciclo: se queda a None y
    # `live_lineup` devuelve "no se sabe", que es mejor que
    # comparar contra un dato equivocado.
    print("Obteniendo alineación actual...")

    try:
        # `lineup(*)` a secas devolvia el bloque sin la lista de
        # jugadores, y el lector se quedaba en cero: el cartel
        # paso a decir "no hay ningun XI puesto" teniendo uno.
        # Se piden los jugadores explicitamente.
        lineup_response = client.session.get(
            f"{client.BASE_URL}/user",
            params={"fields": "*,lineup(*,players(*))"},
        )
        lineup_response.raise_for_status()
        user_lineup = lineup_response.json()

    except Exception as error:
        print(
            f"  No se pudo leer la alineación actual: "
            f"{type(error).__name__}: {error}"
        )
        user_lineup = None

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

        # El once de la jornada que viene, leido donde se escribe.
        "user_lineup": user_lineup,

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