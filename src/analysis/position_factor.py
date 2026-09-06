"""
La vara mide distinto segun la linea, y ahora se corrige.

LO QUE SE MIDIO (17/09/2026)

    `weekly_expected_value` no predice puntos: ordena el once, de
    0 a 1, con jerarquia x probabilidad de ser titular. Es una
    vara comun para las cuatro posiciones.

    Sobre las siete plantillas de la liga, con la MISMA marca de
    esa vara, cada linea entrega esto por jornada:

        Medio       8,51 puntos por unidad de vara   (n=29)
        Delantero   8,44                             (n=18)
        Portero     6,92                             (n= 7)
        Defensa     5,82                             (n=27)

    Un medio entrega 1,46 veces lo que un defensa con la misma
    marca. La vara los trata como iguales, asi que el motor,
    obediente, alinea defensas: el once salia 5-4-1.

    Y el precio, medido: 8 puntos sentados en una sola jornada,
    cuando la temporada se decide por 13.

POR QUE SE APLICA Y NO SE OBSERVA

    Decision del dueño, 18/09: no es una corazonada esperando
    datos, son datos que confirman lo esperable —en un fantasy con
    esta puntuacion, el que ataca puntua mas que el que defiende—.
    La temporada corre y esperar a acumular muestra cuesta mas que
    equivocarse y volver atras.

    Pero se aplica CON RED: cada jornada se publican los puntos
    del once que se alineo, los del que habria elegido la vara
    vieja y los del mejor once posible. En tres jornadas se ve, no
    se discute.

LA MUESTRA ES CORTA Y HAY QUE DECIRLO

    Tres jornadas. El factor del delantero se apoya en 18
    jugadores; el ilustrativo de la franja 65-80 %, en 8. Ocho.
    Eso no se esconde: viaja con el numero, aqui y en pantalla.

EL PORTERO NO LLEVA FACTOR

    n=7, por debajo de la muestra minima de 10 que exige el
    modulo que los midio. Medido salia 0,93, y no se aplica: una
    linea que no llega al minimo no se corrige. Se queda en 1,000
    y se dice.

COMO SE APAGA

    Una variable de entorno, sin tocar codigo:

        BORDALAS_VARA_PLANA=1

    Con eso vuelve la vara de siempre, identica, y el motor
    ordena como el 17/09.
"""

from __future__ import annotations

import os


# ============================================================
# LOS FACTORES
# ============================================================
#
# Congelados a proposito, no recalculados en cada ciclo.
#
#     Un factor que se recalcula solo cambia el once sin que
#     nadie lo haya decidido, y ademas seria circular: el motor
#     se corregiria con una medida hecha sobre plantillas que el
#     propio motor ayuda a formar.
#
#     Al recalcularlos el 18/09 sobre una foto nueva salian
#     1,147 / 1,137 / 0,785: se mueven en la tercera cifra. Esa
#     estabilidad es la razon de poder congelarlos.
FACTORS = {
    1: 1.000,   # Portero    - n=7, no llega a la muestra minima
    2: 0.787,   # Defensa
    3: 1.147,   # Medio
    4: 1.139,   # Delantero
}


# La procedencia de cada numero, para que viaje pegada a el.
# `players` son fichas distintas; `observations` son pares
# jugador-jornada, que es lo que de verdad hay detras.
PROVENANCE = {
    1: {
        "name": "Portero",
        "players": 7,
        "observations": 21,
        "measured_factor": 0.932,
        "applied": False,
        "note": (
            "Solo 7 porteros llegan al minimo de vara: por debajo "
            "de los 10 que exige la medicion. Se mide y no se "
            "aplica."
        ),
    },
    2: {
        "name": "Defensa",
        "players": 27,
        "observations": 81,
        "measured_factor": 0.787,
        "applied": True,
        "note": None,
    },
    3: {
        "name": "Medio",
        "players": 29,
        "observations": 87,
        "measured_factor": 1.147,
        "applied": True,
        "note": None,
    },
    4: {
        "name": "Delantero",
        "players": 18,
        "observations": 54,
        "measured_factor": 1.139,
        "applied": True,
        "note": (
            "La muestra mas corta de las tres que se aplican: 18 "
            "fichas. El dato ilustrativo de la franja 65-80 % se "
            "apoya en 8."
        ),
    },
}


# La ventana de la que salio todo.
WINDOW = {
    "matchdays": 3,
    "squads": 7,
    "players": 81,
    "measured_on": "2026-09-17",
    "source": (
        "Plantillas de los siete managers de la liga, puntos de "
        "temporada divididos por jornadas jugadas."
    ),
}


# ============================================================
# EL INTERRUPTOR
# ============================================================
#
# Una linea de entorno y vuelve la vara del 17/09. Si en dos
# jornadas esto empeora, se apaga sin tocar codigo ni desplegar.
DISABLE_ENV = "BORDALAS_VARA_PLANA"


# Para calcular el contrafactual —"que once habria elegido la
# vara vieja"— sin depender del entorno.
_FORZAR_PLANA = False


def factors_active() -> bool:
    """¿Estan puestos los factores ahora mismo?"""

    if _FORZAR_PLANA:
        return False

    valor = str(os.environ.get(DISABLE_ENV, "")).strip().lower()

    return valor not in ("1", "true", "si", "yes", "on")


def factor_for(position, active: bool | None = None) -> float:
    """
    Lo que multiplica la vara de esta posicion.

    Nunca lanza, y ante la duda devuelve 1,0: una posicion que no
    se reconoce se queda como estaba, no se penaliza.
    """

    try:
        if active is None:
            active = factors_active()

        if not active:
            return 1.0

        return FACTORS.get(int(position), 1.0)

    except (TypeError, ValueError):
        return 1.0


class vara_plana:
    """
    La vara vieja, dentro de este bloque y solo dentro.

    Sirve para el contrafactual del bloque 2: se pide al motor el
    once que habria elegido antes, sin tocar el entorno del
    proceso ni el once de verdad.
    """

    def __enter__(self):
        global _FORZAR_PLANA
        self._antes = _FORZAR_PLANA
        _FORZAR_PLANA = True
        return self

    def __exit__(self, *_):
        global _FORZAR_PLANA
        _FORZAR_PLANA = self._antes
        return False


# ============================================================
# LO QUE VE EL TABLERO
# ============================================================


def state() -> dict:
    """
    Los factores, su muestra y como apagarlos.

    Forma fija: las mismas claves esten los factores puestos o no.
    """

    activos = factors_active()

    filas = []

    for posicion, datos in sorted(PROVENANCE.items()):

        filas.append({
            "position": posicion,
            "name": datos["name"],
            "factor": (
                FACTORS.get(posicion, 1.0) if activos else 1.0
            ),
            "measured_factor": datos["measured_factor"],
            "applied": bool(datos["applied"] and activos),
            "players": datos["players"],
            "observations": datos["observations"],
            "note": datos["note"],
        })

    return {
        "available": True,
        "active": activos,
        "rows": filas,
        "window": dict(WINDOW),
        "disable_with": f"{DISABLE_ENV}=1",
        "reason": _reason(activos, filas),
    }


def _reason(activos: bool, filas: list) -> str:

    if not activos:
        return (
            f"Factores por posicion APAGADOS ({DISABLE_ENV}): el "
            f"once se ordena con la vara del 17/09."
        )

    puestos = [f for f in filas if f["applied"]]

    corta = min(
        puestos,
        key=lambda f: f["players"],
        default=None,
    )

    frase = (
        "Factores por posicion puestos: "
        + ", ".join(
            f"{f['name'].lower()} x{f['factor']:.3f}"
            for f in puestos
        )
        + f". Medidos sobre {WINDOW['matchdays']} jornadas y "
        f"{WINDOW['players']} fichas de las {WINDOW['squads']} "
        f"plantillas de la liga."
    )

    if corta is not None:
        frase += (
            f" El mas corto de muestra es el de "
            f"{corta['name'].lower()}: {corta['players']} fichas "
            f"({corta['observations']} observaciones "
            f"jugador-jornada)."
        )

    sin_aplicar = [f for f in filas if not f["applied"]]

    if sin_aplicar:
        frase += (
            " Sin factor: "
            + ", ".join(f["name"].lower() for f in sin_aplicar)
            + "."
        )

    frase += f" Se apagan con {DISABLE_ENV}=1."

    return frase
