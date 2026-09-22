"""
La prioridad de pujar depende del minuto, no es un numero fijo.

LA TESIS DEL DUEÑO (22/09/2026)

    "Una accion que solo sirve en una franja tiene que ganar en
    esa franja y perder fuera. Una prioridad fija no puede
    expresar eso."

    Hoy `BUY_SPECULATION` vale 400 SIEMPRE. Con eso pierde contra
    cobrar ofertas (650), caducidad urgente (680), renovar
    urgente (690) y publicar por solvencia (500) — y gana a
    renovar no urgente (350) a cualquier hora, incluso a las
    cuatro de la tarde, cuando la puja no corre ninguna prisa.

    Las dos mitades estan mal, y estan mal en direcciones
    contrarias.

LO QUE SE PIERDE SI CADA UNA ESPERA UNA VUELTA

    renovar con margen     nada: la publicacion vive 48 h y sube
                           sola a 690 a menos de 3 h del final.
    cobrar una oferta      normalmente nada: la oferta vive hasta
                           su caducidad, y la caducidad tiene su
                           propia prioridad.
    publicar               un dia de escaparate de los 48 h.
    PUJAR EN LA VENTANA    EL JUGADOR. El reset se resuelve a las
                           07:00 y no vuelve: la puja que no se
                           hace hoy no se hace.

    Por eso el numero tiene que moverse con el reloj.

QUE PROPONE ESTE MODULO

        dentro de la ventana   justo por DEBAJO del once
        fuera de la ventana    justo por DEBAJO de renovar

    LOS DOS NUMEROS SALEN DE LA TABLA QUE YA EXISTE, no de la
    cabeza de nadie (doctrina 84):

        dentro = PRIORITY["LINEUP_LOW"] - 1          = 699
        fuera  = PRIORITY["MARKET_LISTING_RENEW"] - 1 = 349

    699 es el mayor numero que sigue estando por debajo de TODO
    lo que protege el once (700 a 1000) y por encima de todos los
    tramites (690, 680, 670, 650, 550, 500). 349 es el mayor que
    sigue perdiendo contra renovar (350) y publicar (500).

LO QUE NO SE TOCA, Y ESTA DICHO

    EL ONCE GANA SIEMPRE, dentro y fuera de la ventana. Y tambien
    ganan el cierre de jornada (2000), la emergencia de solvencia
    (1100), la barandilla dura (1040) y las fases con el reloj
    encima (960 a 1010). No es una concesion: es que en esas
    fases `plan_del_reset` ya se niega a pujar por su cuenta —el
    reloj de solvencia manda antes que la ventana— asi que
    subirla ahi no cambiaria nada y abriria una puerta por gusto.

LA VENTANA NO SE REDEFINE AQUI

    Se pregunta a `la_subasta.ventana_abierta`, que es donde vive
    y donde estan escritos los 135 minutos y el porque. Un
    segundo sitio que dijera "ventana" seria un segundo sitio que
    olvidar (doctrina 33).

EL INTERRUPTOR

    `BORDALAS_PUJAR_EN_LA_VENTANA=1`. APAGADO de fabrica: sin el,
    la prioridad de la puja es el 400 fijo de siempre.

Y LO QUE ESTO NO ARREGLA, PORQUE NO ESTABA ROTO

    La subasta del reset —la que pone las tres pujas de las
    04:45— NO pasa por esta cola. Corre antes de la puerta de una
    escritura por vuelta y no consume el cupo: medido, 4
    escrituras en una sola vuelta el 18/09. Lo que arregla esto
    es `BUY_SPECULATION`, que es OTRA puja: la del tablero de
    fichajes, que si compite.

NO LEE EL MUNDO

    Ni disco, ni red, ni reloj: los segundos al reset entran por
    la puerta. Solo mira el entorno, que es lo que ES el
    interruptor. Forma fija. Nunca lanza.
"""

from __future__ import annotations


from src.analysis.decision_orchestrator import PRIORITY     # noqa: E402
from src.analysis.la_subasta import ventana_abierta         # noqa: E402


ENV = "BORDALAS_PUJAR_EN_LA_VENTANA"


# Justo por debajo de lo mas bajo que protege el once.
EN_LA_VENTANA = PRIORITY["LINEUP_LOW"] - 1

# Justo por debajo de renovar una publicacion sin prisa.
FUERA_DE_LA_VENTANA = PRIORITY["MARKET_LISTING_RENEW"] - 1

# La de hoy, fija, para poder comparar sin leerla de dos sitios.
LA_DE_HOY = PRIORITY["SPECULATION_BUY"]


def activa() -> bool:
    """Si la prioridad de pujar se mueve con el reloj. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def prioridad_de_la_puja(seconds_to_reset=None) -> dict:
    """
    Cuanto vale pujar en este minuto.

    `seconds_to_reset` lo publica `market_clock`. NO se lee el
    reloj aqui: se recibe. Sin el no se sabe si la ventana esta
    abierta, y entonces NO se sube nada —"no lo sabemos" no es
    "estamos dentro" (doctrina 103)—.

    Forma fija. Nunca lanza.
    """

    salida = {
        "prioridad": LA_DE_HOY,
        "activa": False,
        "en_la_ventana": None,
        "interruptor": ENV,
        "seconds_to_reset": seconds_to_reset,
        "fija": LA_DE_HOY,
        "reason": None,
    }

    try:
        manda = activa()

        ventana = ventana_abierta(seconds_to_reset)

        abierta = bool(ventana.get("abierta"))

        if not manda:
            return {
                **salida,
                "en_la_ventana": abierta,
                "reason": (
                    f"La prioridad de pujar es fija ({ENV} sin "
                    f"poner): {LA_DE_HOY}, dentro y fuera de la "
                    f"ventana."
                ),
            }

        if seconds_to_reset is None:
            return {
                **salida,
                "activa": True,
                "en_la_ventana": None,
                "reason": (
                    f"{ENV} puesto, pero el reloj del mercado no "
                    f"sabe cuando es el reset. No saber si "
                    f"estamos en la ventana no es estar dentro: "
                    f"se queda en {LA_DE_HOY}."
                ),
            }

        return {
            **salida,
            "prioridad": (
                EN_LA_VENTANA if abierta else FUERA_DE_LA_VENTANA
            ),
            "activa": True,
            "en_la_ventana": abierta,
            "reason": (
                (
                    f"Quedan {ventana.get('minutes_to_reset')} min "
                    f"para el reset: la puja vale {EN_LA_VENTANA}, "
                    f"justo por debajo del once. Lo que no se puje "
                    f"hoy no se puja: el reset se resuelve y no "
                    f"vuelve."
                )
                if abierta
                else (
                    f"Fuera de la ventana: la puja vale "
                    f"{FUERA_DE_LA_VENTANA}, por debajo de renovar "
                    f"({PRIORITY['MARKET_LISTING_RENEW']}) y de "
                    f"publicar ({PRIORITY['SOLVENCY_NORMAL']}). "
                    f"Esperar una vuelta no le cuesta nada."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo mirar la hora de pujar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def gana_la_puja(
    seconds_to_reset,
    prioridad_del_rival: int,
) -> bool:
    """
    Si con este reloj la puja le gana a un candidato de esa
    prioridad. Para poder afirmarlo sin reimplementar el orden.
    """

    try:
        return (
            prioridad_de_la_puja(seconds_to_reset)["prioridad"]
            > int(prioridad_del_rival)
        )

    except Exception:                               # noqa: BLE001
        return False
