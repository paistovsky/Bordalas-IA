"""
Dos techos distintos con el mismo nombre.

SINTOMA (12/09/2026)

    Un solo tope para todos:

        bid_cap:  premium_percent      0,25 %
                  break_even_percent   1,80 %

    Ese 1,80 % es donde deja de ser negocio REVENDERLO al
    Computer. Y se le estaba aplicando tambien al jugador que
    queremos QUEDARNOS.

    Son dos techos distintos y no tienen nada que ver.

EL TECHO DEL COMERCIANTE

    Duro, calculable y pequeño. Se compra para revender al
    Computer, asi que el limite lo pone lo que el Computer paga
    -`computer_premium`- menos el suelo de cobro, que es
    coste + 1 %:

        precio_maximo = precio x (1 + prima_computer) / 1,01

    Por encima de ahi el viaje ya no cubre su propio suelo: se
    estaria comprando una operacion que nosotros mismos
    rechazariamos al venderla.

EL TECHO DEL QUE SE QUEDA

    Otra moneda entera. Los puntos se pagan a 30.000 EUR
    (medido, publicado en `roundFinished`). Un jugador que de dos
    puntos mas por jornada durante lo que queda de liga son unos
    60 puntos = 1.800.000 EUR en premios — y eso ANTES de contar
    lo que suba de precio.

    El techo del comerciante es irrelevante ahi.

LO QUE ESTE MODULO HACE, Y LO QUE NO

    CALCULA LOS DOS Y DICE CUAL SE ESTA APLICANDO. Nada mas. No
    mueve ningun tope, no sube ninguna puja y no toca `bid_cap`.

    La decision de cual aplicar es del dueño, y necesita antes
    los dos numeros delante.

POR QUE IMPORTA, CON LA CURVA DELANTE

    La curva de primas de los rivales, calibrada sobre 67 pujas:

        1,0000  1,0061  1,0229  1,0350  1,0692  1,2109  1,2449

    Con el techo del comerciante (~+1 %) le ganas a dos de siete.
    Hay quien paga +24 %. Contra esos, para FICHAR, hoy no
    competimos nunca.
"""

from __future__ import annotations


# Medido y publicado en `roundFinished`. No se escribe aqui: se
# importa de donde vive (regla 33).
from src.analysis.caja_de_la_liga import (                  # noqa: E402
    EUROS_POR_PUNTO,
)


# El suelo de cobro de un viaje: coste + 1 %. Es el mismo que usa
# `salida_del_viaje` para decidir que oferta se acepta, y por eso
# el techo del comerciante se divide por el.
SUELO_DE_COBRO = 1.01

# Cuantas jornadas quedan es un dato de la liga, no una
# constante: quien llame lo pasa. Sin el, el techo del que se
# queda NO se calcula — un horizonte inventado convierte este
# numero en cualquier cosa.
INTENCIONES_DE_QUEDARSE = frozenset(
    {"XI_UPGRADE", "KEEP", "FICHAR", "STARTER"}
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _euros(valor) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def techo_del_comerciante(
    precio_de_mercado,
    prima_computer_percent=None,
) -> dict:
    """
    Lo maximo que se puede pagar por algo que se va a REVENDER.

    Forma fija. Nunca lanza. Si no se sabe la prima del Computer,
    no se inventa: se devuelve `available: False` y quien llame
    decide (doctrina 36).
    """

    vacio = {
        "available": False,
        "techo": None,
        "techo_percent": None,
        "prima_computer_percent": None,
        "reason": None,
    }

    try:
        precio = safe_int(precio_de_mercado)

        if precio <= 0:
            return {
                **vacio,
                "reason": (
                    "Sin precio de mercado no hay techo que "
                    "calcular."
                ),
            }

        prima = safe_float(prima_computer_percent)

        if prima is None:
            return {
                **vacio,
                "reason": (
                    "Sin la prima medida del Computer no se "
                    "calcula el techo del comerciante: seria "
                    "inventarse el unico numero que lo define."
                ),
            }

        techo = int(precio * (1 + prima / 100.0) / SUELO_DE_COBRO)

        return {
            "available": True,
            "techo": techo,
            "techo_percent": round(
                100 * (techo / precio - 1), 3
            ),
            "prima_computer_percent": prima,
            "reason": (
                f"{_euros(techo)} EUR = {_euros(precio)} x "
                f"(1 + {prima} %) / {SUELO_DE_COBRO}. Por encima, "
                f"la reventa no cubre el suelo de cobro y el "
                f"viaje no se puede cerrar con ganancia."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el techo del comerciante: "
                f"{type(error).__name__}: {error}"
            ),
        }


def techo_del_que_se_queda(
    precio_de_mercado,
    puntos_de_mas_por_jornada=None,
    jornadas_que_quedan=None,
) -> dict:
    """
    Lo que vale quedarse a un jugador, en premios.

    NO es un tope: es lo que la mejora del once paga. Se publica
    para que se vea al lado del otro y se entienda que son dos
    monedas distintas.

    Sin los puntos de mas o sin el horizonte NO se calcula. Los
    dos son datos de la liga; inventar cualquiera de ellos
    convierte este numero en lo que uno quiera que sea.
    """

    vacio = {
        "available": False,
        "premios": None,
        "premios_percent": None,
        "puntos": None,
        "reason": None,
    }

    try:
        precio = safe_int(precio_de_mercado)

        puntos = safe_float(puntos_de_mas_por_jornada)

        jornadas = safe_int(jornadas_que_quedan)

        if precio <= 0:
            return {
                **vacio,
                "reason": "Sin precio no hay con que comparar.",
            }

        if puntos is None or jornadas <= 0:
            return {
                **vacio,
                "reason": (
                    "Sin los puntos de mas por jornada y las "
                    "jornadas que quedan no se calcula: los dos "
                    "son datos de la liga y suponerlos haria "
                    "este numero lo que uno quiera."
                ),
            }

        puntos_totales = puntos * jornadas

        premios = int(puntos_totales * EUROS_POR_PUNTO)

        return {
            "available": True,
            "premios": premios,
            "premios_percent": round(
                100 * premios / precio, 2
            ),
            "puntos": round(puntos_totales, 1),
            "reason": (
                f"{_euros(premios)} EUR en premios = "
                f"{round(puntos_totales, 1)} puntos x "
                f"{_euros(EUROS_POR_PUNTO)} EUR/punto "
                f"({puntos} por jornada durante {jornadas}). "
                f"Son {round(100 * premios / precio, 2)} % del "
                f"precio, y NO cuenta lo que suba de precio."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el techo del que se queda: "
                f"{type(error).__name__}: {error}"
            ),
        }


def los_dos_techos(
    precio_de_mercado,
    *,
    prima_computer_percent=None,
    intent=None,
    tope_aplicado=None,
    puntos_de_mas_por_jornada=None,
    jornadas_que_quedan=None,
) -> dict:
    """
    Los dos, con su nombre, y CUAL SE ESTA APLICANDO HOY.

    Forma fija. Nunca lanza. No decide nada: publica.
    """

    vacio = {
        "available": False,
        "comerciante": {},
        "el_que_se_queda": {},
        "via": None,
        "aplicado": None,
        "aplicado_percent": None,
        "reason": None,
    }

    try:
        precio = safe_int(precio_de_mercado)

        comerciante = techo_del_comerciante(
            precio, prima_computer_percent
        )

        quedarse = techo_del_que_se_queda(
            precio,
            puntos_de_mas_por_jornada,
            jornadas_que_quedan,
        )

        # LA VIA YA SE DECIDE EN OTRO SITIO: aqui solo se lee.
        via = (
            "QUEDARSE"
            if str(intent or "").upper()
            in INTENCIONES_DE_QUEDARSE
            else ("REVENDER" if intent else None)
        )

        aplicado = safe_int(tope_aplicado) or None

        return {
            "available": True,
            "comerciante": comerciante,
            "el_que_se_queda": quedarse,
            "via": via,
            "aplicado": aplicado,
            "aplicado_percent": (
                round(100 * (aplicado / precio - 1), 3)
                if aplicado and precio
                else None
            ),
            "reason": (
                "Dos techos distintos. El del COMERCIANTE lo "
                "pone lo que el Computer paga al recomprar; el "
                "del QUE SE QUEDA lo ponen los premios por "
                "punto, que es otra moneda. "
                + (
                    f"Esta puja va por la via {via}. "
                    if via
                    else "La via de esta puja no consta. "
                )
                + (
                    f"Hoy se aplica {_euros(aplicado)} EUR."
                    if aplicado
                    else "No consta que tope se aplico."
                )
                + " Este modulo NO mueve ningun tope: publica."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudieron calcular los dos techos: "
                f"{type(error).__name__}: {error}"
            ),
        }
