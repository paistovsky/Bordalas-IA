"""
El once se busca una vez por entrada, no una vez por pregunta.

QUE PASA HOY (24/09/2026)

    La vuelta tarda 78 minutos y el analisis 24 de ellos. Medido en
    el laboratorio (foto del 19/09, plantilla de 19, sin red, n = 1
    vuelta), las cinco etapas del analisis son la misma cosa:

        etapa                            s     build_lineup    en el
        build_cycle_acquisition_board   17,6   n=  9   15,3 s   87 %
        build_global_decision           88,1   n= 51   86,5 s   98 %
        build_sale_intent                1,8   n=  1    1,8 s   99 %
        build_competitive_observer      36,6   n= 22   36,0 s   98 %
        POST build_global_decision      88,1   n= 52   86,5 s   98 %

    135 alineaciones por vuelta con escritura. Y dentro de cada una,
    el 99 % es `search_best_lineup_for_formation`: una busqueda
    EXHAUSTIVA por combinaciones, siete formaciones y a veces dos
    pasadas por formacion. Crece combinatoriamente con la plantilla,
    que es por lo que el YAML decia «0,26 s con 15 fichas y 4,78 s
    con 21».

    Casi todas esas preguntas son LA MISMA: `build_deadline_state`,
    `analyze_sales` y compania piden el once de la misma plantilla,
    con la misma foto, una y otra vez.

QUE HACE ESTO

    Recuerda la respuesta de la busqueda por el CONTENIDO exacto de
    su entrada: los jugadores tal cual llegan (en su orden, con todos
    sus campos), la formacion (en su orden) y si se admiten los
    dudosos. Si la entrada es identica byte a byte, la respuesta es
    la misma, porque la busqueda no lee nada mas: ni disco, ni red,
    ni reloj, ni el entorno.

    No se guarda el once: se guardan los INDICES elegidos y su
    posicion. Al acertar, el once se reconstruye con los jugadores de
    ESTA llamada, `{**jugador, "lineup_position": posicion}`, que es
    exactamente lo que construye la busqueda. Asi el resultado es el
    mismo objeto por objeto, y quien lo modifique despues no ensucia
    a nadie.

    Y no se guarda nada que no se pueda reconstruir: si los ids no
    son unicos, o si la reconstruccion no da lo mismo que la
    busqueda, esa entrada no se recuerda y la proxima vez se busca.

LO QUE AHORRA, MEDIDO

    La misma vuelta de laboratorio, con la memoria puesta (n = 1
    por lado; dos corridas sin ella para ver su propio ruido):

        etapa                           sin      con
        build_cycle_acquisition_board   17,6 s    3,7 s
        build_global_decision           88,1 s    7,2 s
        build_sale_intent                1,8 s    0,0 s
        build_competitive_observer      36,6 s    0,6 s
        POST build_global_decision      88,1 s    1,4 s
                                       ------   ------
                                        232,1 s  12,9 s

    963 busquedas, 48 distintas. Y el POST de verdad —la foto tras
    renovar una publicacion nuestra— no añade ninguna: 92,0 s ->
    1,8 s.

    LO QUE SALE ES LO MISMO. Comparadas campo a campo las salidas
    de las cinco etapas: entre las dos corridas sin memoria, y entre
    cualquiera de ellas y la corrida con memoria, difieren las MISMAS
    familias de campos y solo esas —horas y segundos que dependen del
    reloj (`age_hours`, `hours_to_expiry`, `seconds_to_*`...), textos
    que las llevan dentro y los errores de la red cortada—. Fuera de
    eso, cero diferencias: la decision, cada once y cada candidata.

LO QUE NO HACE

    No cambia la busqueda: `search_best_lineup_for_formation` sigue
    entera, con su orden y sus desempates. No decide nada. No
    persiste entre procesos. No mira la marca de la foto: una foto
    nueva con la misma plantilla acierta, y una con un solo campo
    distinto no.

EL INTERRUPTOR

    `BORDALAS_EL_ONCE_UNA_VEZ=1`. APAGADO de fabrica: sin el, cada
    pregunta busca, como hoy.

LA CLAVE

    `sha256(pickle(entrada))`. Pickle distingue tipos (1 de 1.0, una
    tupla de una lista) y guarda los decimales exactos; lo que no
    sabe serializar no se recuerda. La probabilidad de que dos
    entradas distintas den el mismo resumen es 2^-128.
"""

from __future__ import annotations

import hashlib
import pickle

from collections import OrderedDict


ENV = "BORDALAS_EL_ONCE_UNA_VEZ"


# Cuantas busquedas se recuerdan. Una alineacion son como mucho
# catorce (siete formaciones, dos pasadas). Medido en el
# laboratorio (n = 1 vuelta): 963 busquedas, 48 distintas, y el
# POST tras una renovacion no añade ninguna. 512 deja diez veces
# de margen. Cada hueco es una clave de 32 B y unas tuplas cortas.
TOPE = 512


_MEMORIA: "OrderedDict[bytes, tuple]" = OrderedDict()

_CUENTA = {"aciertos": 0, "fallos": 0, "sin_clave": 0}


def activa() -> bool:
    """Si el once se busca una sola vez. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def olvidar() -> None:
    """Vacia la memoria y la cuenta. Para las guardias."""

    _MEMORIA.clear()

    for clave in _CUENTA:
        _CUENTA[clave] = 0


def cuenta() -> dict:
    """Aciertos, fallos y entradas sin clave desde el ultimo `olvidar`."""

    return {**_CUENTA, "recordadas": len(_MEMORIA)}


def linea() -> str | None:
    """
    Lo que ahorro la memoria en este proceso, para el log. `None`
    con el interruptor apagado: apagado, el log es el de hoy.

    POR QUE SE IMPRIME. El laboratorio dice 48 busquedas distintas
    de 963, pero la plantilla de produccion es otra y el laboratorio
    no es produccion (doctrina 112). La primera vuelta con el
    interruptor puesto lo dice aqui. Nunca lanza.
    """

    try:
        if not activa():
            return None

        c = cuenta()

        return (
            f"  El once, una vez: {c['fallos']} busquedas hechas, "
            f"{c['aciertos']} recordadas, {c['sin_clave']} sin clave "
            f"({ENV})."
        )

    except Exception:                               # noqa: BLE001
        return None


def _clave(players, formation, allow_warning_players) -> bytes | None:

    try:
        crudo = pickle.dumps(
            (
                players,
                list(formation.items()),
                bool(allow_warning_players),
            ),
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    except Exception:                               # noqa: BLE001
        return None

    return hashlib.sha256(crudo).digest()


def _reconstruir(players, elegidos) -> list:

    return [
        {
            **players[indice],
            "lineup_position": posicion,
        }
        for indice, posicion in elegidos
    ]


def _indices(players, seleccion) -> tuple | None:
    """
    Donde esta cada elegido en `players`, o None si no se puede
    saber sin ambiguedad.
    """

    try:
        donde = {}

        for indice, jugador in enumerate(players):
            ident = jugador["id"]

            if ident in donde:
                # Dos con el mismo id: no se sabe a cual eligio.
                return None

            donde[ident] = indice

        return tuple(
            (donde[elegido["id"]], elegido["lineup_position"])
            for elegido in seleccion
        )

    except Exception:                               # noqa: BLE001
        return None


def buscar(
    players: list[dict],
    formation: dict[int, int],
    allow_warning_players: bool,
    buscador,
) -> dict:
    """
    La respuesta de `buscador(players, formation,
    allow_warning_players=...)`, buscada o recordada.

    Con el interruptor apagado llama al buscador y ya esta.
    """

    if not activa():
        return buscador(
            players,
            formation,
            allow_warning_players=allow_warning_players,
        )

    clave = _clave(players, formation, allow_warning_players)

    if clave is None:
        _CUENTA["sin_clave"] += 1

        return buscador(
            players,
            formation,
            allow_warning_players=allow_warning_players,
        )

    guardado = _MEMORIA.get(clave)

    if guardado is not None:
        _MEMORIA.move_to_end(clave)
        _CUENTA["aciertos"] += 1

        elegidos, score, filled, complete = guardado

        return {
            "selected": _reconstruir(players, elegidos),
            "score": score,
            "filled": filled,
            "complete": complete,
        }

    _CUENTA["fallos"] += 1

    resultado = buscador(
        players,
        formation,
        allow_warning_players=allow_warning_players,
    )

    elegidos = _indices(players, resultado.get("selected") or [])

    # Solo se recuerda lo que se sabe reconstruir IGUAL.
    if (
        elegidos is not None
        and _reconstruir(players, elegidos) == resultado["selected"]
    ):
        _MEMORIA[clave] = (
            elegidos,
            resultado["score"],
            resultado["filled"],
            resultado["complete"],
        )

        while len(_MEMORIA) > TOPE:
            _MEMORIA.popitem(last=False)

    return resultado
