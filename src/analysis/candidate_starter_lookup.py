"""
Probabilidad de ser titular, para CUALQUIER jugador, no solo los
nuestros.

POR QUE EXISTE

    Toda la inteligencia de titularidad que tiene Bordalas -tres
    fuentes, consenso, votos- estaba cableada a la plantilla
    propia. Para valorar un fichaje no habia nada.

    Asi que la valoracion comparaba puntos de la temporada pasada
    a pelo, y el 16/08/2026 propuso pujar 1.236.001 EUR por Andres
    Castrin -97 puntos el ano pasado, pronostico SUPLENTE- para
    sustituir a Yeray -24 puntos, pronostico TITULAR-. "Suma 73
    puntos" es cierto en la hoja de calculo y falso en el campo:
    un suplente no puntua.

DE DONDE SALE CADA COSA

    - De nuestros jugadores, del tablero multifuente
      (`starter_multisource_v1124.json`): tres fuentes y consenso.
      Es el dato bueno y no se toca.

    - De los del mercado, de las senales de Jornada Perfecta
      (`jornada_perfecta_lineups.json`), que desde la extension de
      identidad del proveedor tambien los cubren. Una sola fuente,
      y aqui se dice que es una sola.

LO QUE NO HACE

    No inventa. Un jugador del que no hay senal devuelve None, no
    un 50 % de relleno. Quien decida que hacer con la ausencia de
    dato que lo decida sabiendo que no hay dato.
"""

from __future__ import annotations

import json

from pathlib import Path


BOARD_FILE = Path(
    "data/intelligence/starter_multisource_v1124.json"
)

JP_FILE = Path(
    "data/intelligence/jornada_perfecta_lineups.json"
)


# Umbrales de voto. Los mismos que usa el consenso multifuente,
# repetidos aqui a proposito para no importar el modulo pesado de
# scraping desde la ruta de valoracion.
STARTER_VOTE = 67.0
BENCH_VOTE = 40.0

# Prior por estado de Jornada Perfecta, ponderado por la confianza
# que la propia pagina publica. Identico a `jp_probability`.
JP_PRIOR = {
    "TITULAR": 94.0,
    "PROBABLE": 76.0,
    "DUDA": 50.0,
    "SUPLENTE": 24.0,
    "NO_CONVOCADO": 1.0,
}


_CACHE: dict | None = None
_CACHE_KEY: tuple | None = None


def reset_starter_lookup_cache() -> None:
    global _CACHE, _CACHE_KEY
    _CACHE = None
    _CACHE_KEY = None


def _files_key() -> tuple:
    """
    Firma de los dos ficheros de los que sale todo esto.

    La cache va atada a ella y no a "ya lo lei una vez". Dentro de
    un ciclo el refresco de inteligencia REESCRIBE estos ficheros,
    y valorar con la version anterior seria decidir con el
    pronostico de la jornada de antes sin enterarse.
    """

    firma = []

    for path in (BOARD_FILE, JP_FILE):
        try:
            estado = path.stat()
            firma.append((str(path), estado.st_mtime_ns, estado.st_size))
        except OSError:
            firma.append((str(path), None, None))

    return tuple(firma)


def _load(path: Path) -> dict | None:
    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return None


def vote_label(probability: float | None) -> str | None:

    if probability is None:
        return None

    if probability >= STARTER_VOTE:
        return "STARTER"

    if probability <= BENCH_VOTE:
        return "BENCH"

    return "UNCERTAIN"


def jp_row_probability(row: dict) -> float | None:
    """
    Misma formula que el tablero multifuente: el prior del estado,
    acercado al 50 % en la medida en que la pagina no esta segura.
    """

    prior = JP_PRIOR.get(
        str(row.get("status") or "UNKNOWN").upper()
    )

    if prior is None:
        return None

    try:
        confianza = float(row.get("confidence") or 0)
    except (TypeError, ValueError):
        confianza = 0.0

    confianza = max(0.0, min(confianza, 100.0))

    return round(
        50.0 + (prior - 50.0) * (confianza / 100.0),
        1,
    )


def build_starter_lookup(
    board: dict | None = None,
    jp: dict | None = None,
) -> dict:
    """
    `{player_id: {"probability", "consensus", "coverage",
      "source"}}`.

    El tablero multifuente pisa a Jornada Perfecta cuando los dos
    tienen al jugador: tres fuentes valen mas que una.
    """

    if board is None:
        board = _load(BOARD_FILE) or {}

    if jp is None:
        jp = _load(JP_FILE) or {}

    lookup: dict[int, dict] = {}

    # ------------------------------------------------------
    # Una fuente: Jornada Perfecta. Cubre mercado y plantilla.
    # ------------------------------------------------------

    for row in ((jp or {}).get("players") or []):

        if not isinstance(row, dict):
            continue

        player_id = row.get("biwenger_id")

        if player_id is None:
            continue

        probabilidad = jp_row_probability(row)

        if probabilidad is None:
            continue

        # De donde sale el SUPLENTE importa. Uno leido de la
        # alineacion publicada es un dato; uno deducido de "no
        # aparece en el once de su equipo" es una suposicion
        # prudente que a veces solo significa que el nombre no
        # emparejo. Hay que poder distinguirlos al mirarlo.
        rol = row.get("jp_parser_role")

        lookup[int(player_id)] = {
            "probability": probabilidad,
            "consensus": vote_label(probabilidad),
            "coverage": 1,
            "source": "JORNADA_PERFECTA",
            "status": row.get("status"),
            "inferred": rol == "TEAM_ABSENCE_CONSERVATIVE",
            "parser_role": rol,
            "scope": row.get("identity_scope") or "ROSTER",
        }

    # ------------------------------------------------------
    # Tres fuentes: el tablero. Solo plantilla, y manda.
    # ------------------------------------------------------

    for row in ((board or {}).get("players") or []):

        if not isinstance(row, dict):
            continue

        player_id = row.get("player_id")
        probabilidad = row.get("starter_probability")

        if player_id is None or probabilidad is None:
            continue

        lookup[int(player_id)] = {
            "probability": float(probabilidad),
            "consensus": row.get("consensus"),
            "coverage": int(row.get("source_coverage") or 0),
            "source": "MULTISOURCE",
            "status": None,
            "inferred": False,
            "parser_role": None,
            "scope": "ROSTER",
        }

    return lookup


def get_starter_lookup() -> dict:
    """
    Se relee cuando cambia alguno de los dos ficheros, no una vez
    por proceso.
    """

    global _CACHE, _CACHE_KEY

    clave = _files_key()

    if _CACHE is None or _CACHE_KEY != clave:
        _CACHE = build_starter_lookup()
        _CACHE_KEY = clave

    return _CACHE


def describe_lookup(lookup: dict | None = None) -> dict:

    if lookup is None:
        lookup = get_starter_lookup()

    del_mercado = sum(
        1
        for value in lookup.values()
        if value.get("scope") == "MARKET"
    )

    return {
        "available": bool(lookup),
        "players": len(lookup),
        "market_players": del_mercado,
        "roster_players": len(lookup) - del_mercado,
        "multisource": sum(
            1
            for value in lookup.values()
            if value.get("source") == "MULTISOURCE"
        ),
    }
