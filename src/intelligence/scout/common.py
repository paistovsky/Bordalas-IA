"""
Lo que comparten los ojeadores: salir a la calle con educacion y
traer las señales con la misma forma.

QUE ES UNA SEÑAL

    Un dato de UNA fuente sobre UN jugador, con su magnitud, su
    horizonte y de donde salio. Nada mas. La sintesis -quien esta
    de acuerdo con quien- se hace despues, en `report.py`, y con
    las señales delante.

LO QUE NO PUBLICA NINGUNA DE LAS CUATRO FUENTES

    Un pronostico.

    Se comprobo el 05/09/2026 abriendo las cuatro. Las cuatro
    paginas se llaman "subidas y bajadas" y las cuatro publican
    lo que YA ha pasado:

      FutbolFantasy   su propia leyenda lo dice: "Dif:
                      Diferencia de valor respecto al mercado del
                      dia anterior" y "Tend: dias consecutivos
                      que ha estado aumentando o bajando".
      Analitica       `subida` y `frenada`, el cambio del ultimo
                      mercado y cuanto se ha frenado.
      Comuniate       el cambio de precio, mas el "pulso" de
                      cuantos usuarios pujan por el.

    NINGUNA publica un porcentaje de confianza.

    Asi que aqui no se inventa uno. `confidence` viaja siempre
    con `confidence_basis` al lado diciendo de donde sale, y
    cuando lo calculamos nosotros lo dice con esas palabras. Una
    confianza inventada seria peor que ninguna: parece medida.

POR QUE SIRVE IGUAL, Y MUCHO

    El problema que hay que resolver es que la revalorizacion
    estimada de Pepe es una CONSTANTE: los 22 candidatos del
    tablero rendian exactamente 0,22 %. Cero poder de
    discriminacion.

    El movimiento observado discrimina. Un jugador que lleva tres
    dias subiendo y otro que lleva tres bajando no son el mismo
    activo, y hoy Pepe los ve iguales.

    Que eso ademas prediga es una apuesta razonable -el precio de
    Biwenger tiene mucha inercia- pero es una apuesta, y por eso
    existe el libro de acierto: en dos semanas se sabra.
"""

from __future__ import annotations

from datetime import datetime, timezone


# La misma cabecera que ya usa el proveedor de FutbolFantasy.
# Educacion basica: identificarse como un navegador normal y no
# como algo que hay que bloquear.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "es-ES,es;q=0.9",
}

TIMEOUT_SECONDS = 25


# Codigos ante los que NO se reintenta nunca. Un 429 es la web
# diciendo "para"; insistir es la forma mas rapida de que nos
# bloqueen para siempre.
DO_NOT_RETRY = (403, 429, 401, 451)


UP = "UP"
DOWN = "DOWN"
FLAT = "FLAT"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(round(float(str(value).replace(",", "."))))
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def direction(value) -> str:
    """UP, DOWN o FLAT. Un cero es FLAT, no una subida de cero."""

    numero = safe_float(value)

    if numero is None:
        return FLAT

    if numero > 0:
        return UP

    if numero < 0:
        return DOWN

    return FLAT


def fetch(session, url: str) -> tuple[str | None, str | None]:
    """
    Baja una pagina. Devuelve `(texto, error)`.

    Nunca lanza y nunca reintenta: quien llame decide, y lo que
    decide siempre es seguir. Un ojeador que tumba el ciclo no es
    un ojeador, es un problema.
    """

    try:
        respuesta = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )

    except Exception as error:                      # noqa: BLE001
        return (None, f"{type(error).__name__}: {error}")

    if respuesta.status_code in DO_NOT_RETRY:
        return (
            None,
            f"HTTP {respuesta.status_code}: la web dice que no. "
            f"Se anota y no se reintenta.",
        )

    if respuesta.status_code != 200:
        return (None, f"HTTP {respuesta.status_code}")

    return (respuesta.text, None)


def signal(
    source: str,
    *,
    direction_: str,
    magnitude_percent=None,
    magnitude_eur=None,
    horizon_days=None,
    confidence=None,
    confidence_basis: str | None = None,
    quote: str = "",
    observed: bool = True,
) -> dict:
    """
    Una señal, con su procedencia pegada.

    `observed=True` significa que el dato es lo que YA paso, no
    un pronostico. Las cuatro fuentes de hoy son observadas, y
    marcarlo es lo que impide que dentro de un mes alguien lea
    esto como una prediccion de la casa.
    """

    return {
        "source": source,
        "direction": direction_,
        "magnitude_percent": (
            round(magnitude_percent, 3)
            if magnitude_percent is not None
            else None
        ),
        "magnitude_eur": (
            safe_int(magnitude_eur)
            if magnitude_eur is not None
            else None
        ),
        "horizon_days": horizon_days,

        # Nunca inventada. Si la fuente no publica una, va None y
        # `confidence_basis` dice por que.
        "confidence": confidence,
        "confidence_basis": confidence_basis,

        # Lo que dijo la fuente, con sus palabras o sus campos.
        # Es lo que permite discutir un fallo dentro de un mes.
        "quote": quote,

        "observed": observed,
        "seen_at": now_iso(),
    }


def source_result(
    source: str,
    *,
    ok: bool,
    records: list | None = None,
    error: str | None = None,
    note: str | None = None,
) -> dict:
    """La respuesta de un ojeador, siempre con la misma forma."""

    return {
        "source": source,
        "ok": bool(ok),
        "records": records or [],
        "error": error,
        "note": note,
        "fetched_at": now_iso(),
    }
