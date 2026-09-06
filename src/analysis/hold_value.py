"""
La cuarta via: TENER.

EL HUECO (14/09/2026)

    Pepe sabia valorar tres cosas -mejorar el once, especular a
    corto y revenderle al Computer- y las tres se cobran el mismo
    dia. Ninguna valoraba quedarse el activo montado en la rampa.

    Por eso Amatucci se rechazo con un "rinde un 1,3 %": ese 1,3 %
    es la prima de reventa INMEDIATA. Amatucci sube un 1,098 %
    cada dia y llevaba 19 seguidos.

LO QUE DICE EL RETROTEST, Y ES LO QUE MANDA

    Sobre 5.577 operaciones reconstruidas del almacen de precios
    (554 jugadores, 12-17/08/2026), comprando a la tasa de un dia
    y vendiendo `m` dias despues:

        tasa > 1 %/dia, racha 1 dia, m=3   mediana +4,47 %   5 % en perdida
        tasa 0,5-1 %,   racha 1 dia, m=3   mediana +1,25 %  12 % en perdida
        tasa 0,25-0,5 %,racha 1 dia, m=3   mediana +0,41 %  22 % en perdida
        cae,            racha 1 dia, m=3   mediana -4,76 %  95 % en perdida

    Tener paga, y paga MUCHO en el tramo de arriba. Tambien dice
    que la racha larga rinde menos que la corta, que es lo mismo
    que ya se habia medido el 07/09: la continuacion hace pico el
    segundo dia y cae el tercero.

LA FORMULA, TAL COMO LA PIDIO EL ENCARGO

        ganancia = precio x tasa_diaria x horizonte
        hold_value = precio + ganancia x confianza x (1 - margen)

    Tres condiciones, y las tres son deliberadas:

    1. EL HORIZONTE SALE DEL RETROTEST, no de una intuicion. Es
       el `m` que maximiza la mediana entre los que suben.

    2. LA CONFIANZA SE DESCUENTA DE LA GANANCIA, NO DEL CAPITAL.
       Esa leccion costo una noche entera el 09/09: descontando
       el principal, cualquier confianza por debajo de 1 apagaba
       la via entera. El principal no esta en riesgo — si la
       apuesta falla sigues teniendo un jugador que vale
       aproximadamente lo que pagaste.

    3. PROHIBIDO SUMARLE LA PRIMA DE REVENTA. El +1,72 % del
       Computer esta medido contra el precio de mercado DE ESE
       MOMENTO; si el precio esta subiendo, parte de esa prima YA
       ES la rampa. Sumarlas es contar el mismo euro dos veces.
       Hay guardia: `test_no_contar_dos_veces_v1`.

ES UNA OPERACION DE CARTERA, NO UN FICHAJE

    Entra por el bolsillo de especular y se le exige el liston de
    especular. La regla del 13/09 -el bolsillo, el liston y el
    valor salen todos de la misma via- se respeta sin excepcion.

LA FORMULA ES CONSERVADORA, Y SE SABE CUANTO

    Extrapolar linealmente la tasa de Amatucci da 3,33 % a tres
    dias. La mediana REALIZADA de su tramo en el retrotest es
    +4,47 %. O sea que la formula se queda corta en un tercio.

    Se deja asi a proposito: preferimos equivocarnos por debajo.
"""

from __future__ import annotations

from src.analysis.route_confidence import (
    streak_confidence,
    value_with_confidence_on_gain,
)


ROUTE = "HOLD"

INTENT = "SPECULATION"


# El horizonte sale del retrotest: es el `m` que maximiza la
# mediana entre los que suben. Con la ventana de seis dias que
# hay, el mayor medible es 4 y la mediana crece hasta ahi
# (+0,805 / +1,314 / +2,011 / +2,336 %).
#
# Se usa 3 y no 4 a proposito: en m=4 solo cabe una ventana por
# jugador -la muestra baja de 474 a 242- y la tasa de perdida
# sube del 15,2 % al 17,4 % sin que la mediana mejore lo
# suficiente. El dia que el almacen tenga mas dias, esto se
# vuelve a medir.
DEFAULT_HORIZON_DAYS = 3


# El mismo margen que exige el resto de la casa.
MARGIN = 0.25


# Por debajo de esta tasa diaria el retrotest dice que la
# operacion es ruido: el tramo 0-0,25 % no tiene ni muestra
# suficiente, y el 0,25-0,5 % rinde +0,41 % a tres dias con un
# 22 % de operaciones en perdida.
MIN_DAILY_RATE = 0.0025


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def hold_value(
    price,
    rate_percent_per_day=None,
    trend_days=None,
    sources=None,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> dict:
    """
    Lo que vale TENER a este jugador `horizon_days` dias.

    `rate_percent_per_day` en PORCENTAJE, como lo publica el
    freno de mercado (`market_gate.rate_percent_per_day`): 1.098
    son un 1,098 % diario.

    Nunca lanza. Sin tasa o con tasa a la baja devuelve valor
    cero con el motivo, que es lo que hace el resto de vias
    cuando no tienen nada que decir.
    """

    try:
        precio = safe_int(price)

        if precio <= 0:
            return _sin_valor(
                "SIN_PRECIO",
                "El jugador no tiene precio de mercado valido.",
            )

        tasa = safe_float(rate_percent_per_day)

        if tasa is None:
            return _sin_valor(
                "SIN_RITMO",
                (
                    "No hay ritmo medido para este jugador: tener "
                    "no se valora a ciegas."
                ),
            )

        diaria = tasa / 100.0

        if diaria <= 0:
            return _sin_valor(
                "CAE",
                (
                    f"Cae un {abs(tasa):.3f} % al dia. En el "
                    f"retrotest, comprar en rampa bajista pierde "
                    f"el 95 % de las veces."
                ),
            )

        if diaria < MIN_DAILY_RATE:
            return _sin_valor(
                "RITMO_INSUFICIENTE",
                (
                    f"Sube un {tasa:.3f} % al dia. Por debajo del "
                    f"{MIN_DAILY_RATE * 100:.2f} % el retrotest no "
                    f"encuentra ni muestra suficiente ni "
                    f"rendimiento: el tramo de al lado rinde "
                    f"+0,41 % a tres dias con un 22 % de "
                    f"operaciones en perdida."
                ),
            )

        confianza, base = streak_confidence(
            trend_days=trend_days,
            sources=sources,
        )

        # LA GANANCIA, Y SOLO LA GANANCIA
        #
        #     Nada de prima de reventa aqui dentro. Ver el
        #     docstring del modulo y `test_no_contar_dos_veces_v1`.
        ganancia = int(precio * diaria * horizon_days)

        maximo = value_with_confidence_on_gain(
            precio,
            ganancia,
            confianza,
            margin=MARGIN,
        )

        if maximo <= precio:
            return _sin_valor(
                "SIN_MARGEN",
                (
                    f"Con la confianza de la racha ({confianza:.2f}) "
                    f"y el {MARGIN * 100:.0f} % de margen exigido no "
                    f"queda nada por encima del precio."
                ),
            )

        return {
            "route": ROUTE,
            "intent": INTENT,
            "value": maximo,

            "horizon_days": horizon_days,
            "rate_percent_per_day": round(tasa, 3),
            "raw_gain": ganancia,
            "confidence": confianza,
            "confidence_basis": base,

            "decision": "HOLD",
            # El separador de miles se formatea APARTE. Hacerlo
            # sobre la frase entera se come las comas de la prosa,
            # y ya ha pasado dos veces.
            "reason": (
                f"Sube un {tasa:.3f} % al dia. Teniendolo "
                f"{horizon_days} dias son "
                f"{format(ganancia, ',').replace(',', '.')} EUR de "
                f"rampa; con la confianza de la racha "
                f"({confianza:.2f}) y un {MARGIN * 100:.0f} % de "
                f"margen, pagariamos hasta "
                f"{format(maximo, ',').replace(',', '.')} EUR."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _sin_valor(
            "ERROR",
            f"{type(error).__name__}: {error}",
        )


def _sin_valor(decision: str, motivo: str) -> dict:
    return {
        "route": ROUTE,
        "intent": INTENT,
        "value": 0,
        "decision": decision,
        "reason": motivo,
        "horizon_days": DEFAULT_HORIZON_DAYS,
    }
