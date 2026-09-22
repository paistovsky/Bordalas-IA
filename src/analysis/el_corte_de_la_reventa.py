"""
Cerrar la reventa sin cerrar la compra para quedarse.

QUE PASO (21/09/2026)

    El reset de las 07:00 compro SEIS por 2.566.406 EUR, todas
    de modo cartera. La caja paso de +2.410.033 a -156.373 y la
    plantilla de 15 a 21 fichas: CERO fichas libres. Cinco de
    las seis son suplentes de 150.000-230.000 que el propio
    motor etiqueta "Es Reserva en su equipo: no va a puntuar".

    Se apago con `BORDALAS_SIN_SUBASTA=1`, y la frase que
    publica dice "no se puja nada".

POR QUE NO VALE ESE INTERRUPTOR

    `BORDALAS_SIN_SUBASTA` tiene UN lector -`_sin_subasta` en
    `la_subasta`- y cierra UNA funcion: `plan_del_reset`. Eso
    apaga la subasta del reset entera, y la subasta del reset
    solo sabe hacer modo cartera.

    Lo que NO apaga: el carril de la rendija -que puja todo el
    dia y tiene su propio interruptor, `RENDIJA_APAGADA`- ni el
    tablero de fichajes.

    Asi que "no se puja nada" es verdad DE ESA FUNCION y falso
    del sistema. Ver el informe del 22/09.

QUE HACE ESTE MODULO

    Un corte que mira LA VIA DEL CANDIDATO, no el camino de
    codigo por el que llega la puja:

        REVENDER   comprar para revenderselo al Computer
        QUEDARSE   comprar para que juegue

    Con el interruptor puesto se cierra la primera y se deja
    abierta la segunda.

POR QUE POR CANDIDATO Y NO POR CAMINO (medido)

    Cortar el carril entero habria parado las DIEZ pujas por
    Maffeo del 18/09 -y la foto de ese dia clasifica a Maffeo
    `via: "QUEDARSE"`, valor de fichaje 1.992.831 sobre un
    precio de 1.660.000-. Una compra de plantilla parada es el
    corte mal hecho.

EL VOCABULARIO NO ES NUEVO (doctrina 33 y 84)

    "Para quedarse" ya estaba escrito en dos sitios y este
    modulo no escribe un tercero: usa
    `los_dos_techos.INTENCIONES_DE_QUEDARSE` para el `intent` y
    `deployment.SIGNING_ROUTES` para la `route`. Hay guardia de
    que no se separen.

    Y NO existia ningun interruptor que hiciera esto:
    `BORDALAS_CESTA_SOLO_EL_SUELO` acota la cesta por PRECIO
    -debajo de 1.500.000-, que es otra cosa.

EL INTERRUPTOR

    `BORDALAS_SIN_REVENTA=1`. APAGADO de fabrica: sin el, este
    modulo no cambia ni una puja.

NO LEE EL MUNDO

    Ni disco, ni red, ni reloj. Solo el entorno, que es lo que
    ES el interruptor. Forma fija. Nunca lanza.
"""

from __future__ import annotations


# EL VOCABULARIO, DE DONDE YA VIVIA.
from src.analysis.los_dos_techos import (                    # noqa: E402
    INTENCIONES_DE_QUEDARSE,
)
from src.analysis.deployment import SIGNING_ROUTES           # noqa: E402


ENV = "BORDALAS_SIN_REVENTA"


# Los `modo` de `la_subasta` que son una reventa POR
# CONSTRUCCION: se compra al precio y un pelo para que el
# Computer lo recompre con prima. No es una opinion sobre el
# jugador, es lo que la cuenta hace.
#
# `UN_DISPARO` NO esta aqui a proposito: ese modo no dice por que
# se compra, asi que no decide la via el solo. Guardia:
# `test_el_corte_usa_el_vocabulario_que_ya_existe`.
MODOS_DE_REVENTA = frozenset({"CARTERA"})


QUEDARSE = "QUEDARSE"

REVENDER = "REVENDER"


def cerrada() -> bool:
    """La reventa esta cerrada. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        # Si no se sabe, el corte NO se aplica: un interruptor
        # que no se puede leer no puede cerrar nada solo.
        return False


def via_del_candidato(
    intent=None,
    route=None,
    modo=None,
) -> str | None:
    """
    QUEDARSE, REVENDER o `None` si no consta (doctrina 103).

    El orden importa: la via de fichaje manda sobre el modo. Un
    candidato que el tablero clasifico "para quedarse" sigue
    siendo para quedarse aunque la puja la monte la cesta.
    """

    try:
        via = str(route or "").strip().upper()

        if via and via in SIGNING_ROUTES:
            return QUEDARSE

        proposito = str(intent or "").strip().upper()

        if proposito and proposito in INTENCIONES_DE_QUEDARSE:
            return QUEDARSE

        if proposito or via:
            return REVENDER

        if str(modo or "").strip().upper() in MODOS_DE_REVENTA:
            return REVENDER

        return None

    except Exception:                               # noqa: BLE001
        return None


def corta(
    intent=None,
    route=None,
    modo=None,
    nombre=None,
) -> dict:
    """
    Si hay que frenar esta puja. Forma fija. Nunca lanza.

    `corta` sale True SOLO con el interruptor puesto. Apagado,
    esto devuelve siempre False y el sistema se comporta como
    ayer.

    SIN VIA NO SE ESCRIBE. Con el interruptor puesto, un
    candidato del que no consta la via se frena: es la misma
    regla que ya aplica el carril cuando no puede mirar lo que
    tiene puesto -"el lado seguro de no saber es no escribir"-.
    Y no puede tumbar ninguna compra de plantilla, porque una
    compra de plantilla SI consta.
    """

    vacio = {
        "corta": False,
        "cerrada": False,
        "via": None,
        "interruptor": ENV,
        "reason": None,
    }

    try:
        via = via_del_candidato(
            intent=intent, route=route, modo=modo
        )

        quien = str(nombre or "").strip() or "El candidato"

        if not cerrada():
            return {
                **vacio,
                "via": via,
                "reason": (
                    f"La reventa esta abierta ({ENV} sin poner): "
                    f"no se frena nada."
                ),
            }

        if via == QUEDARSE:
            return {
                **vacio,
                "cerrada": True,
                "via": via,
                "reason": (
                    f"{quien} va por la via QUEDARSE: entra a la "
                    f"plantilla para jugar, no para revenderlo. "
                    f"{ENV} cierra la reventa, no el fichaje."
                ),
            }

        return {
            "corta": True,
            "cerrada": True,
            "via": via,
            "interruptor": ENV,
            "reason": (
                f"{quien} va por la via "
                + (
                    "REVENDER"
                    if via == REVENDER
                    else "que no consta"
                )
                + f". {ENV} puesto: la reventa esta cerrada."
                + (
                    ""
                    if via == REVENDER
                    else " Sin via no se escribe: no saber por "
                    "que se compra no es via libre."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        # Un corte que revienta no puede frenar una puja que el
        # resto del sistema ya aprobo.
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar el corte de la reventa: "
                f"{type(error).__name__}: {error}"
            ),
        }


def separar(candidatos: list | None) -> dict:
    """
    Parte una lista de candidatos en los que siguen y los que
    frena el corte.

    Cada fila puede traer `intent`, `route` y `modo`. Si la fila
    lleva `deployment`, la `route` se busca ahi tambien: es
    donde la escribe el tablero.

    Forma fija. Nunca lanza. Con el interruptor apagado devuelve
    la lista entera en `siguen` y `frenados` vacio.
    """

    salida = {
        "available": False,
        "cerrada": False,
        "siguen": [],
        "frenados": [],
        "interruptor": ENV,
        "reason": None,
    }

    try:
        esta_cerrada = cerrada()

        siguen = []
        frenados = []

        for fila in (candidatos or []):

            if not isinstance(fila, dict):
                continue

            despliegue = fila.get("deployment")

            if not isinstance(despliegue, dict):
                despliegue = {}

            veredicto = corta(
                intent=(
                    fila.get("intent") or despliegue.get("intent")
                ),
                route=(
                    fila.get("route") or despliegue.get("route")
                ),
                modo=fila.get("modo"),
                nombre=fila.get("name") or fila.get("player_name"),
            )

            if veredicto["corta"]:
                frenados.append(
                    {
                        "id": (
                            fila.get("id")
                            or fila.get("player_id")
                        ),
                        "name": (
                            fila.get("name")
                            or fila.get("player_name")
                        ),
                        "via": veredicto["via"],
                        "reason": veredicto["reason"],
                    }
                )

            else:
                siguen.append(fila)

        return {
            "available": True,
            "cerrada": esta_cerrada,
            "siguen": siguen,
            "frenados": frenados,
            "interruptor": ENV,
            "reason": (
                (
                    f"{ENV} puesto: {len(frenados)} frenada(s) "
                    f"por la via, {len(siguen)} siguen."
                )
                if esta_cerrada
                else (
                    f"La reventa esta abierta ({ENV} sin poner): "
                    f"pasan las {len(siguen)}."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "siguen": list(candidatos or []),
            "reason": (
                f"No se pudo separar por via: "
                f"{type(error).__name__}: {error}"
            ),
        }
