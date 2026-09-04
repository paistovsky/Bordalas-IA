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


# ============================================================
# LA JORNADA QUE SE ESTA JUGANDO  (05/09/2026)
# ============================================================
#
#     El 04/09 se tapo la mitad de este agujero: el proveedor ya
#     no SIRVE un tablero de otra jornada cuando FutbolFantasy
#     falla. Pero esta es la otra mitad, y es la que decide: aqui
#     se lee el fichero del disco directamente, y hasta hoy no se
#     miraba de que jornada era.
#
#     El propio `board_stamps` lo decia por escrito -"`matchday`
#     es el guardarrail contra usar datos de una jornada en otra,
#     que es justo el fallo del 16/08/2026"- y lo unico que hacia
#     era publicarlo. Lo cargaba; no lo aplicaba.
#
#     Quien sabe en que jornada estamos son los dos procesos que
#     entran: el ciclo -que ya la calcula para bajar el tablero- y
#     la telemetria. Cada uno la deja dicha aqui.
#
#     SIN SABERLA NO SE RECHAZA NADA. Es a proposito: rechazar
#     contra una expectativa que no tenemos seria inventarse un
#     motivo. Sin expectativa, esto se comporta exactamente como
#     ayer.
_EXPECTED_MATCHDAY: int | None = None


def set_expected_matchday(matchday) -> None:
    """La jornada contra la que hay que validar el tablero."""

    global _EXPECTED_MATCHDAY

    try:
        _EXPECTED_MATCHDAY = (
            int(matchday) if matchday is not None else None
        )

    except (TypeError, ValueError):
        _EXPECTED_MATCHDAY = None

    reset_starter_lookup_cache()


def expected_matchday() -> int | None:
    return _EXPECTED_MATCHDAY


def board_rejection(board: dict | None) -> dict | None:
    """
    ¿Hay que tirar este tablero? Y si si, por que, con palabras
    que pueda leer el dueño en la pantalla.

    Devuelve None cuando el tablero vale.
    """

    esperada = _EXPECTED_MATCHDAY

    if esperada is None:
        return None

    if not board:
        return None

    del_tablero = (board or {}).get("matchday")

    try:
        misma = (
            del_tablero is not None
            and int(del_tablero) == esperada
        )

    except (TypeError, ValueError):
        misma = False

    if misma:
        return None

    if del_tablero is None:
        return {
            "rejected": True,
            "board_matchday": None,
            "expected_matchday": esperada,
            "reason": (
                f"El tablero de titularidad no dice de que jornada "
                f"es y estamos en la {esperada}: no se usa ningun "
                f"pronostico hasta que se refresque."
            ),
        }

    return {
        "rejected": True,
        "board_matchday": del_tablero,
        "expected_matchday": esperada,
        "reason": (
            f"El tablero es de la jornada {del_tablero} y estamos "
            f"en la {esperada}: sin pronosticos hasta que se "
            f"refresque."
        ),
    }


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

    firma = []

    # Las correcciones manuales entran en la firma. Si no, editar
    # el fichero no tendria efecto hasta que FF reescribiese el
    # tablero: la correccion estaria puesta y no se aplicaria, que
    # es la peor de las dos mentiras posibles.
    from src.intelligence.correcciones_jerarquia import (
        ARCHIVO as CORRECCIONES_FILE,
    )

    for fichero in (BOARD_FILE, CORRECCIONES_FILE):

        try:
            estado = fichero.stat()
            firma.append(
                (str(fichero), estado.st_mtime_ns, estado.st_size)
            )

        except OSError:
            firma.append((str(fichero), None, None))

    # La jornada esperada entra en la firma. Si cambia sin que
    # cambie el fichero -y pasa: el tablero se queda rancio
    # mientras el calendario avanza- la respuesta correcta es otra
    # y la cache tiene que soltarla.
    firma.append(("matchday", _EXPECTED_MATCHDAY, None))

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


def build_starter_lookup(board: dict | None = None) -> dict:
    """
    `{player_id: {"probability", "consensus", "coverage",
      "source", "scope", "team", "hierarchy", "availability"}}`.

    Sin consenso y sin topes: la probabilidad es la que publica
    FutbolFantasy, tal cual.
    """

    if board is None:
        board = _load(BOARD_FILE) or {}

    # EL TABLERO DE OTRA JORNADA NO SE SIRVE (05/09/2026)
    #
    #     Se devuelve el lookup vacio, que es el mismo estado que
    #     cuando no hay tablero: nadie recibe pronostico, el XI se
    #     elige por valor y puntos, y la regla del once bloquea
    #     los fichajes. Pepe se queda quieto.
    #
    #     Quedarse quieto es lo correcto -alinear con el
    #     pronostico de la semana pasada costo dinero el
    #     16/08/2026- pero quedarse quieto EN SILENCIO no lo es:
    #     el dueño se pasaria dias preguntandose por que no hace
    #     nada. Por eso el motivo sale por `board_stamps()` y de
    #     ahi al dashboard.
    if board_rejection(board):
        return {}

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

    # ========================================================
    # CUANDO FF SE EQUIVOCA DE ESCALON (22/08/2026)
    # ========================================================
    #
    # Se aplica AQUI y en ningun otro sitio a proposito: este es
    # el unico punto por el que pasan el once, el tablero de
    # fichajes, el plan de deuda y la pantalla. Corregir en varios
    # sitios seria garantizar que un dia dos de ellos digan cosas
    # distintas del mismo jugador.
    #
    # Cada ficha tocada queda marcada con `hierarchy_source` en
    # MANUAL y la correccion entera colgando. Si falla, se sigue
    # con lo que dice FF: una correccion que no se puede leer no
    # puede tumbar el ciclo.
    try:
        from src.intelligence.correcciones_jerarquia import (
            apply_corrections,
        )

        apply_corrections(lookup)

    except Exception:
        pass

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


def board_stamps() -> dict:
    """
    Los sellos de raiz del tablero: cache, jornada y generado.

    POR QUE EXISTE

        `build_starter_lookup` devuelve solo {player_id: senal}, asi
        que los sellos de la raiz del JSON se quedaban por el camino y
        el dashboard los pintaba como "None". El sello que mas importa
        es `matchday`: es el guardarrail contra usar datos de una
        jornada en otra, que es justo el fallo del 16/08/2026.

        Devuelve siempre las tres claves. Si el tablero no se puede
        leer, valen None y la pantalla ensena "?" en vez de mentir.
    """

    board = _load(BOARD_FILE) or {}

    rechazo = board_rejection(board)

    cache = dict(board.get("cache") or {})

    # EL MOTIVO VIAJA POR DONDE YA MIRA LA PANTALLA
    #
    #     `compact_lineup` publica `starter_source_error` desde
    #     `cache.error`. Escribirlo aqui es lo que convierte
    #     "Pepe no hace nada" en "Pepe no hace nada porque el
    #     tablero es de la jornada 3". Y se pisa el error que
    #     hubiera: el de la jornada manda, porque es el que
    #     explica que no hay NI UN pronostico.
    if rechazo:
        cache["status"] = "REJECTED_WRONG_MATCHDAY"
        cache["error"] = rechazo["reason"]

    return {
        "cache": cache,
        "matchday": board.get("matchday"),
        "updated_at": board.get("updated_at"),

        # Explicito, para que la pantalla no tenga que adivinarlo
        # leyendo un texto.
        "rejected": bool(rechazo),
        "rejection_reason": (rechazo or {}).get("reason"),
        "expected_matchday": _EXPECTED_MATCHDAY,
    }


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
