"""
Que la puja deje de ser adivinable.

EL CASO (13/09/2026)

    El dueño, literal:

        "Pollo se llevo a Natan por 7 euros. Eso es que sabe que
         Pepe puja a 0 o a 5 clavaos. Hay que randomizar eso."

    Nuestra sombra valoro a Natan en 3.010.000 EUR. Pollo pago
    3.010.007. Siete euros.

POR QUE ES POSIBLE ADIVINARNOS

    `candidate_bids` construye el conjunto de importes asi:

        importes = {precio + 1}
        for factor, _ in curva:
            importes.add(int(precio * factor) + 1)
        importes.add(techo)

    Y la curva de primas se PUBLICA en el propio `status.json`,
    en `acquisition.premium_model.curve`:

        1.0, 1.0052, 1.0259, 1.0411, 1.0695, 1.2027, 1.2449

    El precio de mercado lo ve toda la liga. Con esos dos datos y
    una calculadora, cualquiera enumera nuestro conjunto de pujas
    candidatas. No hace falta leernos el codigo: basta con
    calcular el mismo valor razonable y ponerse unos euros
    encima.

ESTO NO ES UNA ACUSACION, Y NO SE ESCRIBE COMO SI LO FUERA

    El libro de pujas tiene UNA sola puja registrada. Con n=1 no
    se demuestra que nadie nos este leyendo: los siete euros
    pueden ser casualidad, o dos valoraciones que coinciden.

    Esto se hace porque el seguro cuesta el 0,25 % de la
    operacion y el incendio cuesta perder cada subasta por siete
    euros. No porque lo sepamos. En el codigo y en la pantalla no
    hay ninguna teoria sobre Pollo, y no debe haberla.

LA MATEMATICA NO SE TOCA

    `optimal_bid` decide igual que siempre: el EV, el techo, el
    rendimiento minimo de especulacion y las guardias que
    dependen de ellos -incluida la leccion de Soler- se quedan
    donde estan.

    Esto es la ULTIMA capa. Se aplica sobre el importe que ya
    eligio el motor, en la ruta del ejecutor, despues de decidir.

REPRODUCIBLE DENTRO DEL CICLO, IMPREDECIBLE FUERA

    Nada de `random` sin semilla. La semilla es un hash de
    jugador, fecha, jornada y sal.

    El motivo es concreto: si el ciclo se reintenta, o si dos
    modulos preguntan por el mismo objetivo, el importe tiene que
    salir IDENTICO. Si no, acabariamos con dos pujas distintas
    por el mismo jugador, que es exactamente lo que
    `test_bid_deduplication_v1` existe para impedir.

LA SAL

    Se lee de `BORDALAS_BID_SALT`. Si no esta, se usa la
    constante de este modulo y todo sigue funcionando: degradar,
    nunca romper.

    PERO UNA SAL EN EL CODIGO ES UNA SAL QUE NO PROTEGE. Si este
    repositorio es publico, cualquiera puede leer `DEFAULT_SALT`
    y volver a enumerar nuestras pujas, esta vez con un paso mas.

    La sal de verdad tiene que vivir en los secrets de GitHub y
    llegar por entorno.

    Ponerla es tarea del dueño. Aqui solo esta el hueco.
"""

from __future__ import annotations

import hashlib
import os

from datetime import date


# El desvio maximo es el 0,5 % del precio, acotado entre mil y
# cincuenta mil euros. En un jugador de 3.000.000 son 15.000 de
# tope y 7.500 de media: el 0,25 % de la operacion.
JITTER_PERCENT = 0.005

MIN_JITTER = 1_000
MAX_JITTER = 50_000


# La variable de entorno donde vive la sal de verdad.
SALT_ENV = "BORDALAS_BID_SALT"

# El respaldo. Sirve para que el modulo funcione sin configurar
# nada, y NO sirve para protegerse de quien lea el repositorio.
DEFAULT_SALT = "bordalas-2026-sal-por-defecto"


# Un importe que acaba en 0000 o en 5000 es "clavado". Es la
# frase del dueño hecha constante.
ROUND_MODULUS = 10_000
ROUND_REMAINDERS = (0, 5_000)

# Lo que se le suma a un importe clavado para dejar de serlo.
DEROUND_MIN = 1
DEROUND_MAX = 999


def salt() -> str:
    """
    La sal en uso. Nunca vacia.
    """

    del_entorno = os.environ.get(SALT_ENV, "").strip()

    return del_entorno or DEFAULT_SALT


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def jitter_ceiling(price) -> int:
    """
    El tope del desvio para este precio: `J`.
    """

    precio = safe_int(price)

    if precio <= 0:
        return MIN_JITTER

    return max(
        MIN_JITTER,
        min(MAX_JITTER, int(precio * JITTER_PERCENT)),
    )


def _seed(player_id, fecha, matchday, sufijo: str = "") -> int:
    """
    El hash que hace de semilla.

    `fecha` en ISO. Si no llega, la de hoy: dos ciclos del mismo
    dia dan el mismo importe, y al dia siguiente cambia.
    """

    dia = str(fecha or date.today().isoformat())

    crudo = (
        f"{safe_int(player_id)}:{dia}:{safe_int(matchday)}:"
        f"{salt()}:{sufijo}"
    )

    digest = hashlib.sha256(crudo.encode("utf-8")).digest()

    return int.from_bytes(digest[:8], "big")


def bid_jitter(
    player_id,
    price,
    matchday=None,
    fecha=None,
) -> int:
    """
    El desvio, en euros. Un entero en `[0, J]`.

    Mismo jugador, mismo dia, misma jornada -> mismo numero.
    """

    tope = jitter_ceiling(price)

    return _seed(player_id, fecha, matchday) % (tope + 1)


def _is_round(importe: int) -> bool:
    return (importe % ROUND_MODULUS) in ROUND_REMAINDERS


def _deround(
    importe: int,
    *,
    floor: int,
    ceiling: int,
    player_id,
    matchday,
    fecha,
) -> int:
    """
    Si el importe acaba en 0000 o en 5000, se le quita lo clavado.

    Se suma entre 1 y 999. Si sumar se saliera del techo, se
    resta, y si restar bajase del suelo se deja como esta: los
    limites duros mandan sobre la estetica del numero.
    """

    if not _is_round(importe):
        return importe

    empujon = (
        _seed(player_id, fecha, matchday, sufijo="deround")
        % (DEROUND_MAX - DEROUND_MIN + 1)
    ) + DEROUND_MIN

    if importe + empujon <= ceiling:
        return importe + empujon

    if importe - empujon >= floor:
        return importe - empujon

    return importe


def apply_bid_jitter(
    bid,
    price,
    *,
    ceiling,
    player_id,
    matchday=None,
    fecha=None,
    single_operation_limit=None,
) -> dict:
    """
    El importe final, con su desvio y lo que costo.

    Devuelve las tres cifras para que la pantalla pueda enseñar
    cuanto nos esta costando el seguro:

        `clean`  lo que habria pujado el motor sin esto
        `bid`    lo que se puja de verdad
        `jitter` la diferencia, en euros

    LOS LIMITES DUROS, EN ESTE ORDEN

        nunca por encima del techo,
        nunca por encima del tope por operacion,
        nunca por debajo de `precio + 1`.

    Nunca lanza: si algo va mal devuelve el importe limpio, que
    es exactamente el comportamiento de antes de existir este
    modulo.
    """

    limpio = safe_int(bid)
    precio = safe_int(price)

    try:
        if limpio <= 0 or precio <= 0:
            return _sin_desvio(limpio, "Importe o precio no validos.")

        techo = safe_int(ceiling) or limpio

        if single_operation_limit is not None:
            tope_operacion = safe_int(single_operation_limit)

            if tope_operacion > 0:
                techo = min(techo, tope_operacion)

        suelo = precio + 1

        if techo < suelo:
            return _sin_desvio(
                limpio,
                "El techo no llega ni al minimo: no cabe desvio.",
            )

        desvio = bid_jitter(
            player_id,
            precio,
            matchday=matchday,
            fecha=fecha,
        )

        final = min(limpio + desvio, techo)
        final = max(final, suelo)

        final = _deround(
            final,
            floor=suelo,
            ceiling=techo,
            player_id=player_id,
            matchday=matchday,
            fecha=fecha,
        )

        # Cinturon sobre los tirantes: el deround tambien respeta
        # los limites, pero si algun dia deja de hacerlo, aqui se
        # corta.
        final = max(suelo, min(final, techo))

        return {
            "bid": int(final),
            "clean_bid": int(limpio),
            "jitter": int(final - limpio),
            "jitter_ceiling": jitter_ceiling(precio),
            "applied": bool(final != limpio),
            "salt_from_env": bool(
                os.environ.get(SALT_ENV, "").strip()
            ),
            "reason": (
                f"Desvio de {int(final - limpio):,} EUR sobre "
                f"{limpio:,} para que el importe no se pueda "
                f"enumerar desde la curva de primas publicada."
            ).replace(",", "."),
        }

    except Exception as error:                       # noqa: BLE001
        return _sin_desvio(
            limpio,
            f"{type(error).__name__}: {error}",
        )


def _sin_desvio(importe: int, motivo: str) -> dict:
    return {
        "bid": int(importe),
        "clean_bid": int(importe),
        "jitter": 0,
        "jitter_ceiling": 0,
        "applied": False,
        "salt_from_env": bool(os.environ.get(SALT_ENV, "").strip()),
        "reason": motivo,
    }
