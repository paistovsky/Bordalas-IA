from src.biwenger.client import BiwengerClient


PLAYER_ID = 34479  # Pépé


def inspect_season(
    client: BiwengerClient,
    season: int,
) -> None:

    print()
    print("=" * 70)
    print(f"TEMPORADA {season}")
    print("=" * 70)

    response = client.session.get(
        f"{client.BASE_URL}/competitions/la-liga/data",
        params={
            "lang": "es",
            "score": 5,
            "season": season,
        },
    )

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        print(response.text[:1000])
        return

    data = response.json()

    players = (
        data
        .get("data", {})
        .get("players", {})
    )

    player = players.get(str(PLAYER_ID))

    if not player:
        print("Jugador no encontrado en esta temporada.")
        return

    print()
    print("Jugador:", player.get("name"))
    print("Precio:", player.get("price"))
    print("Puntos:", player.get("points"))
    print(
        "Puntos temporada anterior:",
        player.get("pointsLastSeason"),
    )
    print(
        "Partidos casa:",
        player.get("playedHome"),
    )
    print(
        "Partidos fuera:",
        player.get("playedAway"),
    )
    print(
        "Puntos casa:",
        player.get("pointsHome"),
    )
    print(
        "Puntos fuera:",
        player.get("pointsAway"),
    )
    print(
        "Estado:",
        player.get("status"),
    )
    print(
        "Fitness:",
        player.get("fitness"),
    )

    print()
    print("DATOS COMPLETOS:")
    print(player)


def main() -> None:

    client = BiwengerClient()

    print("Conectando con Biwenger...")
    client.login()
    client.select_league()

    print("Conexión correcta.")

    inspect_season(client, 2026)
    inspect_season(client, 2025)
    inspect_season(client, 2024)


if __name__ == "__main__":
    main()