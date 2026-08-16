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


# Letras latinas que NFKD no descompone porque no son una letra
# base mas un acento: son caracteres propios.
#
# La o barrada de Sorloth es el caso que nos mordio el 16/08/2026.
NON_DECOMPOSABLE = {
    "\u00f8": "o",   # o barrada  (Sorloth)
    "\u00e6": "ae",
    "\u0153": "oe",
    "\u00f0": "d",
    "\u00fe": "th",
    "\u0142": "l",
    "\u0111": "d",
    "\u00df": "ss",
    "\u0131": "i",
}


def normalize_name(name: str) -> str:
    """
    Deja el nombre como lo acepta API-Football.

    La API rechaza la busqueda entera si el termino trae algo que
    no sea alfanumerico o espacio:

        API-Football error: {'search': 'The Search field may only
        contain alpha-numeric characters and spaces.'}

    NFKD por si solo no bastaba. Descompone los acentos -Angel,
    Oskarsson, Jutgla- pero no las letras que son un caracter
    propio, como la o barrada de Sorloth. En el catalogo del
    16/08/2026 quedaban cinco nombres que la API rechazaba:
    Sorloth, El-Abdellaoui, Etienne Eto'o, Sainz-Maza y
    Kang-in Lee.

    Los guiones se convierten en espacio porque separan palabras
    -"Kang-in Lee" busca mejor como "kang in lee" que como
    "kangin lee"-. Los apostrofos se borran, porque no separan
    nada.
    """

    text = (name or "")

    for original, replacement in NON_DECOMPOSABLE.items():
        text = text.replace(original, replacement)
        text = text.replace(original.upper(), replacement)

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = text.replace("'", "").replace("\u2019", "")

    text = "".join(
        character
        if character.isalnum() or character == " "
        else " "
        for character in text
    )

    return " ".join(text.lower().split())


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