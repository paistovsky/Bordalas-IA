"""
El freno de mano: una posicion especulativa que se gira, se
vende.

POR QUE EXISTE

    Es lo que hace aceptable el acelerador. Comprar rachas
    funciona -el que sube sigue subiendo el 85,1 % de las veces-
    pero toda racha se acaba, y sin regla de salida comprar
    rachas es comprar techos tarde o temprano.

    La misma medicion que justifica entrar justifica salir:

        90,7 %  de los que bajaron ayer bajan hoy
         0,5 %  de los que bajaron baten al mercado

    No hace falta adivinar cuando termina una racha. Basta con
    reaccionar el dia que se gira, porque el giro avisa: a partir
    de ahi la caida es lo mas persistente que hay en este
    mercado.

A QUIEN SE LE APLICA, Y A QUIEN NO

    SOLO a las posiciones abiertas como SPECULATION en el libro
    de posiciones. Un jugador del once que baja de precio no es
    una posicion girada: es un futbolista que se compro por
    puntos, y esa via no la toca este modulo.

    Es una distincion que importa. Sin ella, la primera semana
    mala de precios propondria vender media plantilla.

LO QUE NO HACE: VENDER SOLO

    Aqui se PUNTUA, no se ejecuta. Pepe no vende por iniciativa
    propia salvo para generar liquidez, y esa decision es del
    dueño y esta escrita en `sale_intent`:

        "Vender mal no es como comprar mal. Una compra mala
         cuesta dinero y se corrige; una venta mala te deja SIN
         el jugador, y en un fantasy no se recupera."

    Asi que esta regla actua PRIORIZANDO: el dia que haya que
    soltar a alguien, la posicion girada va primero. Cambiar eso
    -que Pepe publique por su cuenta- seria una decision del
    dueño, no de esta noche.

UNA PROPIEDAD QUE SALE SOLA, Y ES BUENA

    El apunte son 60 puntos, justo el corte de VENDER. Pero
    `analyze_sales` resta 15 por estar en el once, asi que una
    posicion girada que ADEMAS esta jugando se queda en 45:
    CONSIDERAR VENTA, no VENDER.

    No esta programado como caso especial: sale de sumar las dos
    reglas, y es exactamente lo que uno querria. Si esta dando
    puntos, no se malvende por una racha de precio.
"""

from __future__ import annotations

import json

from pathlib import Path


# Los 60 puntos son el corte de VENDER de `analyze_sales`. Una
# posicion girada llega ahi por si sola: es el sentido de la
# regla.
EXIT_SCORE = 60


# Solo cuentan las posiciones que de verdad tenemos. Una puja
# pendiente no es una posicion girada: todavia no es nuestra.
HELD_STATUSES = frozenset(
    {
        "OPEN",
        "HELD",
        "ACTIVE",
        "WON",
        "FILLED",
    }
)

SPECULATIVE_STRATEGIES = frozenset(
    {
        "SPECULATION",
        "TRADING",
    }
)


LEDGER_PATH = (
    Path("data")
    / "trading"
    / "position_ledger.json"
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_speculative_positions(
    ledger: dict | None = None,
    path: Path | None = None,
) -> dict:
    """
    `{player_id: posicion}` de lo que tenemos comprado para
    revender.

    Nunca lanza. Sin libro de posiciones devuelve vacio, y sin
    posiciones esta regla no hace nada — que es lo correcto y no
    un fallo.
    """

    try:
        if ledger is None:
            ruta = path or LEDGER_PATH

            if not ruta.exists():
                return {}

            ledger = json.loads(ruta.read_text(encoding="utf-8-sig"))

        posiciones = {}

        for fila in (ledger or {}).get("positions") or []:

            if not isinstance(fila, dict):
                continue

            estrategia = str(fila.get("strategy") or "").upper()
            estado = str(fila.get("status") or "").upper()

            if estrategia not in SPECULATIVE_STRATEGIES:
                continue

            if estado not in HELD_STATUSES:
                continue

            player_id = safe_int(fila.get("player_id"))

            if player_id:
                posiciones[player_id] = fila

        return posiciones

    except Exception:                               # noqa: BLE001
        return {}


def evaluate_exit(
    player_id,
    positions: dict | None,
    rates: dict | None,
) -> dict | None:
    """
    ¿Hay que soltar a este jugador porque su posicion se ha
    girado?

    Devuelve None cuando no aplica: o no es una posicion
    especulativa nuestra, o no se ha girado, o no hay ritmo
    observado con que saberlo.
    """

    identificador = safe_int(player_id)

    posicion = (positions or {}).get(identificador)

    if not posicion:
        return None

    señal = (rates or {}).get(identificador)

    if not señal:
        # SIN RITMO NO SE VENDE TAMPOCO
        #
        #     La simetria importa: si sin dato no se compra,
        #     sin dato tampoco se vende. Vender a ciegas por si
        #     acaso es la version cara del mismo error.
        return None

    ritmo = safe_float(señal.get("rate_percent_per_day"))

    if ritmo is None or ritmo >= 0:
        return None

    entrada = safe_int(posicion.get("entry_price")) or safe_int(
        posicion.get("bid_amount")
    )

    return {
        "score": EXIT_SCORE,
        "player_id": identificador,
        "player_name": posicion.get("player_name"),
        "position_id": posicion.get("position_id"),
        "strategy": posicion.get("strategy"),
        "entry_price": entrada or None,
        "rate_percent_per_day": ritmo,
        "trend_days": señal.get("trend_days"),
        "reason": (
            f"Posicion especulativa girada: entro para revender y "
            f"el precio viene bajando ({ritmo:+.2f} %/dia). De los "
            f"que bajan, el 90,7 % sigue bajando y solo el 0,5 % "
            f"bate al mercado: cuanto antes se suelte, menos "
            f"cuesta."
        ),
    }
