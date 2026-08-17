"""
Probabilidad de ser titular y jerarquia, para CUALQUIER jugador.

POR QUE EXISTE

    Toda la inteligencia de titularidad estaba cableada a la
    plantilla propia. Para valorar un fichaje no habia nada.

    Asi que la valoracion comparaba puntos de la temporada pasada
    a pelo, y el 16/08/2026 propuso pujar 1.236.001 EUR por Andres
    Castrin -97 puntos el ano pasado, pronostico SUPLENTE- para
    sustituir a Yeray -24 puntos, pronostico TITULAR-. "Suma 73
    puntos" es cierto en la hoja de calculo y falso en el campo:
    un suplente no puntua.

QUE CAMBIO EL 17/08/2026

    Una sola fuente: FutbolFantasy. Se retiran Jornada Perfecta y
    el consenso multifuente.

    El consenso no funcionaba. Con cobertura 1 topaba todo en
    74/26 y las etiquetas dejaban de significar nada: un 92 % de
    una fuente y un 25 % de otra salian como "UNCERTAIN 58 %", que
    no es un acuerdo, es el promedio de dos cosas que no se pueden
    promediar. Y con JP el mercado quedaba cubierto a medias y con
    la mitad de los SUPLENTE deducidos por ausencia, que muchas
    veces solo significaba que el nombre no emparejo.

    De FF sale ademas la JERARQUIA -Dios, Clave, Importante,
    Rotacion, Revulsivo, Reserva, Descarte-, que es lo que de
    verdad hace falta para fichar: el porcentaje dice quien juega
    ESTE sabado y cambia cada semana; la jerarquia dice que es un
    jugador en su equipo y aguanta la temporada. Una compra dura
    meses y no se decide con un dato de siete dias.

LO QUE NO HACE

    No inventa. Un jugador del que no hay senal devuelve None, no
    un 50 % de relleno. Una jerarquia sin definir es None, no
    "Descarte". Quien decida que hacer con la ausencia de dato que
    lo decida sabiendo que no hay dato.
"""

from __future__ import annotations

import json

from pathlib import Path


BOARD_FILE = Path(
    "data/intelligence/futbolfantasy_board.json"
)


# Umbrales de voto. Los mismos que usa el resto del sistema,
# repetidos aqui a proposito para no importar el modulo pesado de
# scraping desde la ruta de valoracion.
STARTER_VOTE = 67.0
BENCH_VOTE = 40.0


_CACHE: dict | None = None
_CACHE_KEY: tuple | None = None


def reset_starter_lookup_cache() -> None:
    global _CACHE, _CACHE_KEY
    _CACHE = None
    _CACHE_KEY = None


def _files_key() -> tuple:
    """
    Firma del fichero del que sale todo esto.

    La cache va atada a ella y no a "ya lo lei una vez". Dentro de
    un ciclo el refresco de inteligencia REESCRIBE el tablero, y
    valorar con la version anterior seria decidir con el
    pronostico de la jornada de antes sin enterarse.
    """

    try:
        estado = BOARD_FILE.stat()
        return (str(BOARD_FILE), estado.st_mtime_ns, estado.st_size)

    except OSError:
        return (str(BOARD_FILE), None, None)


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


def build_starter_lookup(board: dict | None = None) -> dict:
    """
    `{player_id: {"probability", "consensus", "coverage",
      "source", "scope", "team", "hierarchy", "availability"}}`.

    Sin consenso y sin topes: la probabilidad es la que publica
    FutbolFantasy, tal cual.
    """

    if board is None:
        board = _load(BOARD_FILE) or {}

    lookup: dict[int, dict] = {}

    for row in ((board or {}).get("players") or []):

        if not isinstance(row, dict):
            continue

        player_id = row.get("player_id")
        probabilidad = row.get("starter_probability")

        if player_id is None or probabilidad is None:
            continue

        disponibilidad = row.get("availability") or {}
        jerarquia = row.get("hierarchy") or None

        lookup[int(player_id)] = {
            "probability": float(probabilidad),

            "consensus": (
                row.get("consensus")
                or vote_label(float(probabilidad))
            ),

            "coverage": int(row.get("source_coverage") or 1),
            "source": row.get("source") or "FUTBOLFANTASY",

            "scope": row.get("scope") or "ROSTER",
            "team": row.get("team"),

            # La jerarquia viaja entera -valor, etiqueta y si es
            # de nivel franquicia- para que quien valore no tenga
            # que traducir numeros a mano.
            "hierarchy": jerarquia,
            "hierarchy_value": (
                jerarquia.get("value") if jerarquia else None
            ),
            "hierarchy_label": (
                jerarquia.get("label") if jerarquia else None
            ),
            "franchise": bool(
                jerarquia.get("franchise") if jerarquia else False
            ),

            "availability": disponibilidad,
            "status": disponibilidad.get("label"),
            "can_play": disponibilidad.get("can_play"),

            # El parte de baja, cuando lo hay: cuantas jornadas se
            # pierde y con que fundamento. Es lo que separa una
            # gripe de un cruzado, que con solo el % son el mismo
            # 0 %.
            "absence": row.get("absence"),

            # La jornada del tablero viaja con cada jugador para
            # que quien valore sepa contra cuantas jornadas
            # restantes mide una ausencia, sin tener que ir a
            # buscarla a otro sitio.
            "matchday": (board or {}).get("matchday"),

            "next_match": row.get("next_match") or {},
            "team_context": row.get("team_context") or {},
            "minutes": row.get("minutes"),

            # FF publica un pronostico leido, no deducido por
            # ausencia. Se deja el campo por compatibilidad con
            # quien lo imprimia, siempre en False.
            "inferred": False,
            "parser_role": (row.get("match") or {}).get("method"),
        }

    return lookup


def get_starter_lookup() -> dict:
    """
    Se relee cuando cambia el tablero, no una vez por proceso.
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

    con_jerarquia = sum(
        1
        for value in lookup.values()
        if value.get("hierarchy_value")
    )

    return {
        "available": bool(lookup),
        "players": len(lookup),
        "market_players": del_mercado,
        "roster_players": len(lookup) - del_mercado,
        "with_hierarchy": con_jerarquia,
        "franchise": sum(
            1
            for value in lookup.values()
            if value.get("franchise")
        ),
        "source": "FUTBOLFANTASY",
    }
