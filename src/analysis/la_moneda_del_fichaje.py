"""
Cada via cobra en su moneda: el comerciante en la del mercado, el que
se queda en la de la liga.

LO QUE CIERRA CUATRO DIAS (22/09/2026)

    `xi_upgrade_value` multiplica los puntos por `tarifa`, que es
    la MEDIANA DE `price / pointsLastSeason` DEL CATALOGO ENTERO:
    lo que el MERCADO COBRA por un punto. Unos 18.300 EUR.

    Y despues le resta un 10 % de margen. O sea que el techo de
    un fichaje es el 90 % de la mediana del propio mercado, y por
    construccion solo puede comprar en la mitad barata menos ese
    10 %.

        Que casi nadie pase no es un hallazgo sobre el mercado:
        es lo que la formula hace.

    Medido sobre las dos fotos con valor de fichaje calculado:

        el motor paga   9.040 a 17.923 EUR por punto esperado
        el mercado pide 13.719 a 66.769

    Solo dos bajaron del techo —Maffeo a 13.719 y Cabrera a
    15.916— y son exactamente los dos que acepto.

LA OTRA MONEDA, QUE YA ESTABA MEDIDA

    `caja_de_la_liga.EUROS_POR_PUNTO = 30.000`, del reparto del
    `leagueReset` del 09/08, despejado del saldo real y cuadrado
    AL EURO sobre 24 dias. Es lo que un punto NOS PAGA.

    Y `los_dos_techos` lleva escrito desde el 12/09 que son dos
    monedas distintas: "el techo del que se queda: otra moneda
    entera". Lo que faltaba era usarla.

QUE HACE ESTE MODULO, EXACTAMENTE

    Una cosa: decir a que precio se paga un punto SEGUN PARA QUE
    SE COMPRA EL JUGADOR.

        comprar para REVENDER   tarifa del mercado   se lo vendes
                                                     al mercado
        comprar para QUEDARSE   30.000 EUR           te lo quedas
                                                     y te paga la
                                                     liga

    NO es un factor de correccion y no toca la formula: cambia
    UN factor de una multiplicacion que ya existe. El margen, la
    confianza, el calendario, los vetos de jerarquia y el suelo
    de titularidad siguen exactamente donde estaban.

Y EL TECHO DEL COMERCIANTE NO SE TOCA

    La reventa lo sigue usando y es el correcto para ella: si lo
    vas a vender al Computer, lo que vale es lo que el Computer
    paga. Aqui solo se le quita el trabajo que no era suyo.

LA TERCERA PREGUNTA DE LA MISMA CADENA

    `plan_del_reset` ya encadena dos filtros:

        `la_regla_de_compra`       ¿va a jugar?    -> el JUGADOR
        `el_corte_de_la_reventa`   ¿es reventa?    -> la OPERACION

    La moneda es la tercera: ¿PARA QUE lo compro? Y se contesta
    con el mismo vocabulario, sin escribir uno nuevo (doctrina
    33 y 84): `deployment.SIGNING_ROUTES` y
    `los_dos_techos.INTENCIONES_DE_QUEDARSE`.

EL INTERRUPTOR

    `BORDALAS_LA_MONEDA_DE_LA_LIGA=1`. APAGADO de fabrica: sin
    el, la tarifa es la de siempre y no cambia ni un euro.

NO LEE EL MUNDO

    Ni disco, ni red, ni reloj. Solo el entorno, que es lo que ES
    el interruptor. Forma fija. Nunca lanza.
"""

from __future__ import annotations


from src.analysis.caja_de_la_liga import EUROS_POR_PUNTO      # noqa: E402
from src.analysis.deployment import SIGNING_ROUTES            # noqa: E402
from src.analysis.los_dos_techos import (                     # noqa: E402
    INTENCIONES_DE_QUEDARSE,
)


ENV = "BORDALAS_LA_MONEDA_DE_LA_LIGA"


# Lo que un punto NOS PAGA. No se escribe aqui: se importa de
# donde se midio (doctrina 33).
MONEDA_DE_LA_LIGA = EUROS_POR_PUNTO


def activa() -> bool:
    """Si cada via cobra en su moneda. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def es_para_quedarse(intent=None, route=None) -> bool:
    """
    Si esta compra es para quedarse el jugador.

    El mismo vocabulario que usa el corte de la reventa: la
    `route` de fichaje manda, y el `intent` despues.
    """

    try:
        via = str(route or "").strip().upper()

        if via and via in SIGNING_ROUTES:
            return True

        proposito = str(intent or "").strip().upper()

        return bool(
            proposito and proposito in INTENCIONES_DE_QUEDARSE
        )

    except Exception:                               # noqa: BLE001
        return False


def tarifa_del_punto(
    tarifa_del_mercado,
    intent=None,
    route=None,
) -> dict:
    """
    Lo que vale un punto para ESTA compra.

    `tarifa_del_mercado` es la que ya calcula
    `calibrate_points_market`: se recibe, no se lee.

    Forma fija. Nunca lanza. Con el interruptor quitado devuelve
    la del mercado, tal cual, sin mirar nada mas.
    """

    try:
        mercado = int(tarifa_del_mercado or 0)

    except (TypeError, ValueError):
        mercado = 0

    salida = {
        "tarifa": mercado,
        "activa": False,
        "para_quedarse": None,
        "moneda": "MERCADO",
        "tarifa_del_mercado": mercado,
        "moneda_de_la_liga": MONEDA_DE_LA_LIGA,
        "interruptor": ENV,
        "reason": None,
    }

    try:
        if not activa():
            return {
                **salida,
                "reason": (
                    f"Un punto se paga a la tarifa del mercado "
                    f"({mercado}) para todo ({ENV} sin poner)."
                ),
            }

        quedarse = es_para_quedarse(intent=intent, route=route)

        if not quedarse:
            return {
                **salida,
                "activa": True,
                "para_quedarse": False,
                "reason": (
                    f"Se compra para REVENDER: un punto vale lo "
                    f"que el mercado cobra por el ({mercado} EUR), "
                    f"porque es al mercado a quien se le vende."
                ),
            }

        return {
            **salida,
            "tarifa": MONEDA_DE_LA_LIGA,
            "activa": True,
            "para_quedarse": True,
            "moneda": "LIGA",
            "reason": (
                f"Se compra para QUEDARSE: un punto vale lo que "
                f"la liga paga por el ({MONEDA_DE_LA_LIGA} EUR, "
                f"medido en el reparto del leagueReset y cuadrado "
                f"al euro sobre 24 dias), no lo que el mercado "
                f"cobra ({mercado})."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        # Una moneda que revienta no puede cambiar un precio: se
        # queda la de siempre.
        return {
            **salida,
            "reason": (
                f"No se pudo mirar la moneda: "
                f"{type(error).__name__}: {error}"
            ),
        }
