"""
No se compra para revender a quien no consta que vaya a jugar.

UNA REGLA, Y SALE DE LA MEDICION (22/09/2026)

    Emparejando cada compra con su venta en el tablon de los ocho
    managers —115 viajes cerrados, 09/08 a 21/09— el P&L de un
    viaje se parte en tres trozos exactos:

                              nosotros      Pollo17     Luismi_Haz
        prima de entrada     -1.036.806   -4.449.076   -1.552.006
        MOVIMIENTO DEL MERCADO -310.000  +10.690.000   +7.860.000
        prima del Computer   +1.097.413   +6.831.400   +2.221.000
        ---------------------------------------------------------
        total                  -249.393  +13.072.324   +8.528.994
        (n)                          22           43           23

    La prima del Computer casi nos cubre la de entrada. Lo que
    nos separa de ellos ES EL MOVIMIENTO DEL MERCADO, y nada mas.

    Y EL MERCADO SOLO SE MUEVE SI EL JUGADOR JUEGA. Sobre los 91
    viajes de Pollo17 y Luismi_Haz, partidos por lo que el
    jugador hizo mientras lo tenian:

        puntos/partido dentro   n    verde   ROI med   mercado movio
        [0, 2)                   3    100 %    5,21 %     +29,63 %
        [2, 4)                  25    100 %    4,67 %      +3,48 %
        [4, 6)                  12    100 %   12,56 %     +12,31 %
        [6, ...)                 5     80 %    9,44 %      +2,40 %
        HABIA PARTIDO Y NO JUGO  6     33 %   -2,03 %      +0,00 %
        no hubo partido         19     79 %    2,77 %      -0,47 %

    UNA SOLA FILA PIERDE DINERO, y es la del que no jugo. Para
    ese, el mercado se movio CERO: se le paga la prima de entrada
    y no hay nada que la pague.

LA SEÑAL QUE SI SE SABE EL DIA DE LA COMPRA

    "Cuantos puntos hara" no se sabe al comprar. "Si jugo el
    ultimo partido de su equipo" si, y separa igual:

                                    n   verde   ROI med          P&L
        ellos, jugo el ultimo      49    96 %    5,06 %  +17.998.428
        ellos, NO jugo el ultimo    4    50 %    1,06 %     +336.600
        nosotros, jugo el ultimo    5    40 %   -2,57 %     -310.396
        nosotros, NO jugo           12    58 %    0,55 %     -475.115

    Sobre NUESTRA temporada, no comprar a los que no habian
    jugado el ultimo partido nos habria quitado doce viajes que
    en conjunto perdieron 475.115 EUR: el P&L de la temporada
    pasa de +92.375 a +567.490. Seis veces.

EL UMBRAL NO ES NUEVO, Y AHORA TIENE SU MEDICION

    `MIN_STARTER_PERCENT = 40` ya existe en `deployment` y lo usa
    `roster_fill_veto` para la via de plantilla. Doctrina 84: no
    se escribe otro.

    Doctrina 90 dice que un numero que recibes tambien necesita
    su medicion, y ese no la tenia. Medido el 22/09 sobre los 142
    del tablero de FutbolFantasy cruzados con quien jugo de
    verdad (n=114 cruzables):

        corte   acierta   de los que pasan, jugaron   pasan
         10 %     82 %                        82 %     105
         30 %     81 %                        84 %      96
         40 %     81 %                        89 %      84
         50 %     77 %                        92 %      74
         60 %     67 %                        95 %      56

    El 40 esta en la meseta del acierto y es donde la pureza da
    el salto (84 % -> 89 %). Subirlo compra pureza pagando
    acierto y volumen.

LA REGLA NO SE ESCRIBE DOS VECES

    La pregunta "¿va a jugar?" ya esta contestada en
    `deployment.roster_fill_veto`, con sus cuatro patas: sin
    pronostico no se ficha a ciegas, por debajo del 40 % no, un
    descarte de su equipo no, y el que no puede jugar tampoco.

    Este modulo NO la reescribe: la llama. Lo unico que aporta es
    APLICARSELA A LA REVENTA, que hoy no la mira.

EL INTERRUPTOR

    `BORDALAS_REVENTA_SOLO_SI_JUEGA=1`. APAGADO de fabrica: sin
    el, este modulo no frena ni una puja.

LO QUE NO ARREGLA, DICHO AQUI

    Cinco de nuestros nueve fallos los para; los otros cuatro
    —Djene, Zubeldia, Kiko Femenia y Maffeo— SI jugaron. Esos
    cuatro perdieron por otra cosa, medida en el informe: se
    compraron con una prima de entrada del +4 % al +10 % y con el
    precio ya cayendo.

NO LEE EL MUNDO

    Ni disco, ni red, ni reloj. Solo el entorno, que es lo que ES
    el interruptor. Forma fija. Nunca lanza.
"""

from __future__ import annotations


from src.analysis.deployment import (                        # noqa: E402
    MIN_HIERARCHY_VALUE,
    MIN_STARTER_PERCENT,
    roster_fill_veto,
)


ENV = "BORDALAS_REVENTA_SOLO_SI_JUEGA"


def activa() -> bool:
    """Si la regla manda. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        # Un interruptor que no se puede leer no frena nada solo.
        return False


def _señal(fila: dict) -> dict:
    """
    La fila del tablero, con la forma que pide `roster_fill_veto`.

    El tablero publica los campos planos -`starter_probability`,
    `hierarchy_value`- y el veto los espera anidados. Aqui se
    traducen y no se inventa ninguno: lo que no venga se queda a
    `None`, que es "no consta" y el veto ya sabe que hacer con
    eso (doctrina 103).
    """

    fila = fila if isinstance(fila, dict) else {}

    anidada = fila.get("starter")

    if isinstance(anidada, dict) and anidada:
        base = dict(anidada)
    else:
        base = {}

    base.setdefault("probability", fila.get("starter_probability"))
    base.setdefault("hierarchy_value", fila.get("hierarchy_value"))
    base.setdefault("hierarchy_label", fila.get("hierarchy_label"))
    base.setdefault("availability", fila.get("availability"))

    return base


def por_que_no(fila: dict) -> str | None:
    """
    Por que este candidato NO se compra para revender.

    `None` significa que se puede. Nunca lanza: una regla que
    revienta no puede frenar una puja que el resto aprobo.
    """

    try:
        return roster_fill_veto(_señal(fila))

    except Exception:                               # noqa: BLE001
        return None


def mira_si_va_a_jugar(candidatos: list | None) -> dict:
    """
    Parte la lista en los que siguen y los que frena la regla.

    Forma fija. Nunca lanza. Con el interruptor apagado devuelve
    la lista entera en `siguen` y `frenados` vacio: el
    comportamiento de antes del 22/09, al detalle.
    """

    salida = {
        "available": False,
        "activa": False,
        "siguen": list(candidatos or []),
        "frenados": [],
        "interruptor": ENV,
        "min_starter_percent": MIN_STARTER_PERCENT,
        "min_hierarchy_value": MIN_HIERARCHY_VALUE,
        "reason": None,
    }

    try:
        manda = activa()

        if not manda:
            return {
                **salida,
                "available": True,
                "reason": (
                    f"La regla esta apagada ({ENV} sin poner): "
                    f"pasan los {len(candidatos or [])}."
                ),
            }

        siguen = []
        frenados = []

        for fila in (candidatos or []):

            if not isinstance(fila, dict):
                continue

            motivo = por_que_no(fila)

            if motivo:
                frenados.append(
                    {
                        "id": fila.get("id") or fila.get("player_id"),
                        "name": (
                            fila.get("name")
                            or fila.get("player_name")
                        ),
                        "starter_probability": fila.get(
                            "starter_probability"
                        ),
                        "hierarchy_value": fila.get(
                            "hierarchy_value"
                        ),
                        "reason": motivo,
                    }
                )

            else:
                siguen.append(fila)

        return {
            **salida,
            "available": True,
            "activa": True,
            "siguen": siguen,
            "frenados": frenados,
            "reason": (
                f"{ENV} puesto: {len(frenados)} frenada(s) por no "
                f"constar que vayan a jugar, {len(siguen)} siguen. "
                f"El mercado no se mueve para quien no juega, y el "
                f"movimiento del mercado es de donde sale el "
                f"beneficio de un viaje."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo mirar la regla de compra: "
                f"{type(error).__name__}: {error}"
            ),
        }
