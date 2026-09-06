"""
¿La vara con la que se elige el once mide igual en las cuatro
posiciones?

LA SOSPECHA DEL DUEÑO (17/09/2026)

    "El once salio 5-4-1, con el suelo de delanteros en 2, y
    Pablo Duran con un 70 % de titularidad estaba en el banquillo
    mientras defensas con ese mismo 70 % jugaban."

    Si el motor infravalora sistematicamente a los delanteros,
    alinea defensas, y eso cuesta puntos cada jornada sin que
    nadie lo note.

QUE ES `weekly_expected_value` Y QUE NO ES

    No es una prediccion de puntos. Su propio docstring lo dice:
    "es una vara comun para ordenar el once", de 0 a 1, que sale
    de jerarquia x probabilidad de ser titular.

    Asi que "error medio en puntos" no se puede calcular: no hay
    puntos que restar. Lo que SI se puede medir, y es la pregunta
    de verdad, es esta:

        con la MISMA marca de la vara, ¿cuantos puntos entrega
        un delantero y cuantos un defensa?

    Si la vara fuese neutra, el cociente seria el mismo en las
    cuatro posiciones. Si no lo es, la vara esta ordenando mal el
    once y hay un sesgo con nombre y con numero.

DE DONDE SALE LA MUESTRA

    De las plantillas de los siete managers de la liga: unos cien
    jugadores con posicion, puntos de temporada y su valor
    semanal ya calculado por el motor.

    Es transversal, no historica: los puntos son del acumulado de
    la temporada y la plantilla es la de HOY. Un jugador fichado
    ayer trae puntos que hizo en otro equipo. Eso ensancha el
    ruido, no lo sesga hacia ninguna posicion, pero se dice.

ESTE MODULO NO CORRIGE NADA

    Publica el factor que HARIA FALTA para igualar las cuatro
    posiciones. No lo aplica. La decision es del dueño, y la
    muestra de hoy -tres jornadas- no da para tocar el motor con
    ella.
"""

from __future__ import annotations

import statistics


POSICIONES = {
    1: "Portero",
    2: "Defensa",
    3: "Medio",
    4: "Delantero",
}


# Por debajo de esto el motor ni se plantea alinearlo, asi que
# meterlo en la cuenta mide un banquillo que nunca compite.
VALOR_MINIMO = 0.30


# Con menos de esto en una posicion, el cociente es una anecdota.
# Se publica el dato y se dice que no da para proponer factor.
MUESTRA_MINIMA = 10


# LA FRANJA DEL CASO DEL DUEÑO
#
#     "Pablo Duran con un 70 % en el banquillo mientras defensas
#     con ese mismo 70 % jugaban." Se mide justo ahi, porque es
#     donde la vara empata a dos jugadores y el motor tiene que
#     desempatar.
FRANJA_EMPATE = (65.0, 80.0)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _muestra(status: dict | None) -> tuple[list, int]:
    """Un jugador por ficha de la liga, con lo que hace falta."""

    estado = status or {}

    jornadas = safe_int(
        (estado.get("race") or {}).get("matchdays_played")
    )

    filas = []

    if jornadas <= 0:
        return filas, 0

    for manager in (
        (estado.get("rival_squads") or {}).get("managers") or []
    ):
        for jugador in (manager.get("players") or []):

            valor = safe_float(
                jugador.get("weekly_expected_value")
            )

            posicion = safe_int(jugador.get("position"))
            puntos = jugador.get("points")

            if valor is None or posicion not in POSICIONES:
                continue

            if puntos is None:
                continue

            filas.append({
                "name": jugador.get("name"),
                "manager": manager.get("name"),
                "position": posicion,
                "expected": valor,
                "points_per_matchday": safe_int(puntos) / jornadas,
                "starter_probability": safe_float(
                    jugador.get("starter_probability")
                ),
            })

    return filas, jornadas


def sesgo_por_posicion(status: dict | None) -> dict:
    """
    Puntos entregados por unidad de valor esperado, por posicion.

    Nunca lanza.
    """

    try:
        filas, jornadas = _muestra(status)

        if not filas:
            return {
                "available": False,
                "observer_only": True,
                "reason": (
                    "Sin plantillas de la liga o sin jornadas "
                    "jugadas: no hay con que comparar."
                ),
                "rows": [],
            }

        alineables = [
            f
            for f in filas
            if f["expected"] >= VALOR_MINIMO
        ]

        if not alineables:
            return {
                "available": False,
                "observer_only": True,
                "reason": (
                    f"Ningun jugador llega al valor minimo de "
                    f"{VALOR_MINIMO}."
                ),
                "rows": [],
            }

        total_valor = sum(f["expected"] for f in alineables)
        total_puntos = sum(
            f["points_per_matchday"] for f in alineables
        )

        global_ratio = (
            total_puntos / total_valor
            if total_valor
            else None
        )

        filas_posicion = []

        for posicion, nombre in POSICIONES.items():

            grupo = [
                f
                for f in alineables
                if f["position"] == posicion
            ]

            if not grupo:
                continue

            valor = sum(f["expected"] for f in grupo)
            puntos = sum(f["points_per_matchday"] for f in grupo)

            ratio = puntos / valor if valor else None

            filas_posicion.append({
                "position": posicion,
                "name": nombre,
                "n": len(grupo),
                "enough": len(grupo) >= MUESTRA_MINIMA,

                "expected_mean": round(
                    statistics.fmean(
                        f["expected"] for f in grupo
                    ),
                    3,
                ),
                "points_per_matchday_mean": round(
                    statistics.fmean(
                        f["points_per_matchday"] for f in grupo
                    ),
                    2,
                ),
                "points_per_matchday_median": round(
                    statistics.median(
                        f["points_per_matchday"] for f in grupo
                    ),
                    2,
                ),

                # LA CIFRA: puntos entregados por unidad de vara.
                "points_per_expected": (
                    round(ratio, 2) if ratio is not None else None
                ),

                # EL FACTOR QUE HARIA FALTA, QUE NO SE APLICA
                #
                #     Multiplicar el valor semanal de esa
                #     posicion por esto igualaria las cuatro. Es
                #     una propuesta con su numero, no un cambio.
                "proposed_factor": (
                    round(ratio / global_ratio, 3)
                    if ratio is not None and global_ratio
                    else None
                ),
            })

        filas_posicion.sort(
            key=lambda f: f.get("points_per_expected") or 0,
            reverse=True,
        )

        return {
            "available": True,
            "observer_only": True,
            "applied": False,

            "matchdays": jornadas,
            "sample": len(alineables),
            "sample_total": len(filas),
            "minimum_expected": VALOR_MINIMO,
            "minimum_sample": MUESTRA_MINIMA,

            "global_points_per_expected": (
                round(global_ratio, 2)
                if global_ratio is not None
                else None
            ),

            "rows": filas_posicion,
            "tie_band": empate_en_la_franja(alineables),

            "reason": _reason(filas_posicion),

            "caveat": (
                "El valor semanal no predice puntos: ordena el "
                "once. Lo que se mide aqui es cuantos puntos "
                "entrega cada posicion con la misma marca de esa "
                "vara. Muestra transversal de "
                f"{jornadas} jornada(s): sirve para proponer, no "
                "para tocar el motor."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "rows": [],
            "reason": (
                f"No se pudo medir el sesgo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def empate_en_la_franja(alineables: list) -> dict:
    """
    El caso exacto del dueño: mismo porcentaje, distinta posicion.

    Cuando dos jugadores tienen la misma probabilidad de ser
    titulares, la vara los empata y el motor desempata por
    jerarquia. Si en esa franja una posicion entrega mas puntos
    que otra, el desempate esta yendo al lado equivocado.
    """

    desde, hasta = FRANJA_EMPATE

    salida = {
        "from": desde,
        "to": hasta,
        "rows": [],
        "gap_percent": None,
    }

    por_posicion = {}

    for posicion, nombre in POSICIONES.items():

        grupo = [
            f
            for f in alineables
            if f["position"] == posicion
            and f["starter_probability"] is not None
            and desde <= f["starter_probability"] <= hasta
        ]

        if not grupo:
            continue

        media = statistics.fmean(
            f["points_per_matchday"] for f in grupo
        )

        por_posicion[posicion] = media

        salida["rows"].append({
            "position": posicion,
            "name": nombre,
            "n": len(grupo),
            "expected_mean": round(
                statistics.fmean(f["expected"] for f in grupo),
                3,
            ),
            "points_per_matchday_mean": round(media, 2),
            "points_per_matchday_median": round(
                statistics.median(
                    f["points_per_matchday"] for f in grupo
                ),
                2,
            ),
        })

    salida["rows"].sort(
        key=lambda f: f["points_per_matchday_mean"],
        reverse=True,
    )

    delantero = por_posicion.get(4)
    defensa = por_posicion.get(2)

    if delantero and defensa:
        salida["gap_percent"] = round(
            (delantero - defensa) / defensa * 100,
            1,
        )

    return salida


def _reason(filas: list) -> str:

    utiles = [f for f in filas if f.get("enough")]

    if len(utiles) < 2:
        return (
            "Menos de dos posiciones llegan a la muestra minima: "
            "no se puede comparar."
        )

    arriba = utiles[0]
    abajo = utiles[-1]

    if not abajo.get("points_per_expected"):
        return "Sin cociente en la posicion mas baja."

    distancia = round(
        arriba["points_per_expected"]
        / abajo["points_per_expected"],
        2,
    )

    if distancia < 1.15:
        return (
            f"La vara mide parecido en todas las posiciones "
            f"(la mejor entrega {distancia}x lo que la peor). "
            f"No hay sesgo que corregir."
        )

    return (
        f"Con la misma marca de la vara, un {arriba['name'].lower()} "
        f"entrega {distancia}x los puntos que un "
        f"{abajo['name'].lower()}. La vara ordena el once como si "
        f"fueran iguales, asi que empuja hacia "
        f"{abajo['name'].lower()}s. Medido, no corregido."
    )
