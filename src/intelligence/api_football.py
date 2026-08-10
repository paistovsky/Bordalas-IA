import os
import unicodedata

import requests
from dotenv import load_dotenv


BASE_URL = "https://v3.football.api-sports.io"

LALIGA_ID = 140

# Temporada real de Bordalás IA
CURRENT_SEASON = 2026

# Temporada antigua usada únicamente para resolver IDs
# porque el plan Free permite consultar jugadores ahí.
PLAYER_LOOKUP_SEASON = 2024


def get_api_key() -> str:
    load_dotenv()

    api_key = os.getenv("API_FOOTBALL_KEY")

    if not api_key:
        raise RuntimeError(
            "No se ha encontrado API_FOOTBALL_KEY en .env"
        )

    return api_key


def get_headers() -> dict:
    return {
        "x-apisports-key": get_api_key(),
    }


def api_get(
    endpoint: str,
    params: dict | None = None,
) -> dict:

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=get_headers(),
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    errors = data.get("errors")

    if errors:
        raise RuntimeError(
            f"API-Football error: {errors}"
        )

    return data


def normalize_name(name: str) -> str:
    text = unicodedata.normalize(
        "NFKD",
        name,
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    return text.lower().strip()


def search_player(
    player_name: str,
) -> list[dict]:

    search_name = normalize_name(
        player_name
    )

    data = api_get(
        "players",
        params={
            "search": search_name,
            "league": LALIGA_ID,
            "season": PLAYER_LOOKUP_SEASON,
        },
    )

    return data.get(
        "response",
        [],
    )