"""
La linea de credito de Biwenger: un numero medido, no deducido.

EL INCIDENTE (10/09/2026)

    El dueno pujo 12.217.000 por Aubameyang. Dos ciclos del
    mismo dia:

        07:52  saldo 3.315.383  maximumBid 15.825.383
               ratio 0,250000   headroom 12.510.000

        09:04  saldo 3.315.383  maximumBid  3.608.383
               ratio 0,005855   headroom    293.000

    Y con el ratio se hundio la capacidad estimada de los SIETE
    managers de la liga, porque el ratio de Pepe se aplicaba a
    todos:

        Pollo17      9.413.772  ->         0
        Luismi_Haz  23.342.594  -> 2.880.828
        Manzagool   11.330.280  ->         0

    Una sola puja del dueno y Pepe cree que Pollo no puede pujar
    y que Luismi tiene 2,9 M en vez de 23,3 M.

LA CAUSA: EL DESPEJE EQUIVOCADO

    Hay una sola ecuacion, y se puede despejar por dos sitios:

        correcto:    comprometido = saldo + plantilla/4 - maximumBid
        produccion:  headroom     = maximumBid - saldo

    La segunda calcula el margen A PARTIR de un `maximumBid` que
    YA trae las pujas descontadas -medido el 16/08-. Asi que el
    margen se traga la puja, el ratio se hunde, y la resta que
    deberia sacar lo comprometido da cero: se anula sola.

    No era un error de cuentas. Era medir la incognita con un
    dato contaminado por la incognita.

POR QUE 0,25 Y NO OTRA COSA

    Medido el 09/09/2026 sobre las 85 fotos de produccion del 12
    al 17/08, que dan 12 estados distintos de (saldo, maximumBid,
    plantilla, comprometido):

        maximumBid == saldo + valor_plantilla/4 - comprometido

        EXACTO AL EURO en los 12 de 12. Con saldo positivo y
        negativo, con plantillas de 15, 16 y 17 fichas, y con
        pujas vivas de 480.000, 984.000, 1.740.001 y 3.126.002
        -numeros con desvio, que un redondeo afortunado no
        salva-.

    Y los jugadores LISTADOS cuentan, a precio de mercado.

    Lo que NO se puede afirmar: como redondea. Todos los precios
    de Biwenger son multiplos de 10.000, asi que el 25 % cae
    siempre exacto y no hay ni un caso que separe "hacia arriba"
    de "hacia abajo". Se usa division entera y se dice.

SI ALGUN DIA CAMBIA, SE AVISA; NO SE ADOPTA EN SILENCIO

    Un `comprometido` NEGATIVO es imposible: nadie puede tener
    comprometido menos de cero. Si sale negativo es que el 0,25
    ya no vale.

    En ese caso se publica la ANOMALIA y se sigue con 0,25 hasta
    que alguien lo vuelva a medir. Nunca al reves: adoptar en
    caliente un ratio deducido de una foto rara es exactamente lo
    que arruino a la liga el 10/09.

UN DATO, UN NOMBRE

    Este numero vive AQUI y en ningun otro sitio. La rama
    `solvencia/ver-las-pujas-del-dueno` tiene su propia copia en
    `pujas_del_dueno.LINEA_DE_CREDITO`; cuando se fusionen, esa
    tiene que pasar a importarse de aqui.

ESTE MODULO NO LEE EL MUNDO

    Ni disco, ni red, ni reloj. Forma fija. Nunca lanza.
"""

from __future__ import annotations


# ============================================================
# EL NUMERO
# ============================================================
#
#     No es un umbral que se pueda ajustar: es una regla de
#     Biwenger, medida. Si se toca, las guardias se ponen rojas.
LINEA_DE_CREDITO = 0.25

ESTADOS_MEDIDOS = 12

FOTOS_MEDIDAS = 85

MEDIDO_EL = "09/09/2026, sobre las fotos del 12-17/08/2026"


# De donde sale el ratio que se publica. Antes solo habia uno
# -deducido en caliente- y no se veia cual era.
MEDIDA = "LINEA_MEDIDA"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _euros(valor) -> str:
    """El separador de miles, APARTE de la frase."""

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"


def headroom_de(
    valor_plantilla,
    linea: float = LINEA_DE_CREDITO,
) -> int:
    """
    El margen de deuda que da Biwenger por esta plantilla.

    NO depende de `maximumBid`, y ese es todo el punto: el
    margen tiene que poder calcularse aunque haya pujas vivas.
    """

    valor = max(0, safe_int(valor_plantilla))

    return int(valor * linea)


def comprometido_de(
    balance,
    maximum_bid,
    valor_plantilla,
    linea: float = LINEA_DE_CREDITO,
) -> dict:
    """
    Cuanto dinero nuestro esta comprometido en pujas vivas.

        comprometido = saldo + headroom - maximumBid

    Con la anomalia publicada si sale negativo. Forma fija.
    """

    vacio = {
        "available": False,
        "committed": 0,
        "headroom": 0,
        "ratio": linea,
        "source": MEDIDA,
        "anomaly": None,
        "reason": None,
    }

    try:
        saldo = safe_int(balance)

        tope = safe_int(maximum_bid)

        valor = safe_int(valor_plantilla)

        if tope <= 0 or valor <= 0:
            return {
                **vacio,
                "reason": (
                    "Sin maximumBid o sin valor de plantilla no "
                    "se puede calcular lo comprometido."
                ),
            }

        margen = headroom_de(valor, linea)

        comprometido = saldo + margen - tope

        # LO IMPOSIBLE SE AVISA, NO SE ADOPTA
        if comprometido < 0:
            return {
                **vacio,
                "available": True,
                "committed": 0,
                "headroom": margen,
                "anomaly": {
                    "kind": "COMPROMETIDO_NEGATIVO",
                    "value": comprometido,

                    # Lo que tendria que valer la linea para que
                    # esta foto cuadrase. Se publica para poder
                    # medirla otra vez, NO para usarla.
                    "implied_ratio": (
                        (tope - saldo) / valor if valor else None
                    ),
                },
                "reason": (
                    f"ANOMALIA: la cuenta da "
                    f"{_euros(comprometido)} EUR comprometidos, "
                    f"que es imposible. La linea medida "
                    f"({linea:.4f}) ya no cuadra con esta foto. "
                    f"Se sigue con {linea:.4f} y se publica el "
                    f"aviso: un ratio nuevo no se adopta en "
                    f"caliente."
                ),
            }

        return {
            "available": True,
            "committed": comprometido,
            "headroom": margen,
            "ratio": linea,
            "source": MEDIDA,
            "anomaly": None,
            "reason": (
                f"{_euros(saldo)} de saldo + {_euros(margen)} de "
                f"margen - {_euros(tope)} de maximumBid = "
                f"{_euros(comprometido)} EUR comprometidos."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular lo comprometido: "
                f"{type(error).__name__}: {error}"
            ),
        }


def capacidad_de(balance, valor_plantilla, linea=LINEA_DE_CREDITO) -> int:
    """
    Con cuanto podria pujar ALGUIEN, por su saldo y su plantilla.

    LA REGLA QUE ESTO ARREGLA

        La capacidad de un rival tiene que salir de SU saldo y SU
        plantilla. Nunca de nuestro `maximumBid`, que baja cada
        vez que nosotros pujamos.

        El 10/09, con una puja del dueno, Pollo17 y Manzagool
        pasaron a "capacidad 0" sin haber hecho nada.
    """

    return max(
        0,
        safe_int(balance) + headroom_de(valor_plantilla, linea),
    )
