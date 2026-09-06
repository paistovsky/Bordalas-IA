"""
Quien es bueno, medido en puntos y no en etiquetas.

LA REGLA 6, QUE ES EL TECHO DE TODO LO DEMAS

    La vara con la que se elige el once es
    jerarquia x probabilidad de ser titular. Y la mitad de
    "calidad" no es una medicion: es una escalera decretada a
    partir de una etiqueta de FutbolFantasy.

        Dios 1,00 · Clave 0,92 · Importante 0,80 · Rotacion 0,62
        Revulsivo 0,50 · Reserva 0,38 · Descarte 0,25

    Ni un punto que un futbolista haya marcado de verdad entra
    ahi. Y la vara entera explica el 20 % de la varianza.

LAS DOS COSAS QUE EL ENCARGO NO DEJA NEGOCIAR

    1. PUNTOS POR PARTIDO JUGADO, no por jornada.

       "Un suplente que hace 6 en veinte minutos no es malo: es
        uno que juega poco, y de eso se encarga la otra mitad de
        la formula. Mezclarlas es contarlo dos veces."

       El catalogo trae `playedHome` y `playedAway`: partidos, no
       jornadas. Es exactamente el denominador que hace falta.

    2. LA TEMPORADA PASADA Y ESTA NO PESAN IGUAL.

       Esta temporada son tres o cuatro partidos: un doblete
       convierte a un suplente en Dios. La pasada son 38, pero es
       de otro año, otro equipo y otra forma.

       Se combinan encogiendo hacia la pasada segun la muestra de
       esta:

           peso_de_esta = partidos / (partidos + K)

       Con K = 5 partidos. El criterio, escrito como pide la
       regla 18: a los 5 partidos las dos mitades pesan igual, y
       5 es lo que tarda un titular en jugarlos -algo mas de un
       mes-. Antes de eso manda lo que ya sabiamos; despues,
       manda lo que esta pasando.

LA ETIQUETA NO SE TIRA: SE DEGRADA A SUPLENTE

    Donde no hay partidos jugados -un recien llegado, uno con
    minutos ridiculos- sigue mandando la jerarquia, y la ficha
    dice CUAL de las dos la esta valorando. Nunca las dos a la
    vez.

Y SI NO MEJORA, NO SE ENCIENDE

    "Publica el antes y el despues del 20 %. Si no mejora, no la
     enciendas: significaria que el problema no es la calidad, y
     saberlo vale mas que encenderla."

    Por eso este modulo MIDE y publica. Encenderlo es otra
    decision, y hoy no esta encendido en el motor.
"""

from __future__ import annotations

import os
import statistics


# ============================================================
# ENCENDIDA EL 22/09/2026
# ============================================================
#
#     19,1 % -> 23,5 % de varianza explicada, medido sin
#     circularidad. Modesto, pero la direccion es la que
#     cualquiera esperaria -los puntos que un jugador ha hecho
#     predicen mejor que una etiqueta- y la temporada corre.
#
#     Se apaga con una linea y vuelve la escalera de siempre:
#
#         BORDALAS_CALIDAD_ETIQUETA=1
DISABLE_ENV = "BORDALAS_CALIDAD_ETIQUETA"


# Para el contrafactual del marcador, sin tocar el entorno.
_FORZAR_ETIQUETA = False


# LA REFERENCIA QUE LLEVA PUNTOS A LA ESCALA DE LA VARA
#
#     La escalera de la etiqueta va de 0,25 a 1,00. La calidad
#     medida va en puntos por partido, de 0 a 13. Mezclarlas sin
#     traducir reventaria la ordenacion.
#
#     La referencia es el p95 de los 419 jugadores con calidad
#     medida: 6,0 puntos por partido. Con eso, el 95 % del
#     catalogo cae por debajo de 1,00, que es donde vivia la
#     escalera.
#
#     NO se recorta arriba a proposito: un jugador que puntua el
#     doble que un p95 es el doble de bueno, y la escalera vieja
#     no podia decirlo porque su techo era Dios.
REFERENCIA_PUNTOS_PARTIDO = 6.0


# Partidos de esta temporada a los que las dos mitades pesan
# igual. Ver el docstring: es el criterio, no un numero suelto.
K_PARTIDOS = 5


# Con menos de esto no hay medicion que valga: manda la etiqueta.
MINIMO_PARTIDOS = 1


# Una temporada completa, para llevar los puntos del año pasado a
# puntos por partido.
PARTIDOS_TEMPORADA = 38


# La escalera decretada, tal cual esta en el motor. Se importa
# para que no pueda separarse de la de verdad.
def _escalera():
    from src.analysis.lineup_engine import HIERARCHY_MATCH_QUALITY

    return HIERARCHY_MATCH_QUALITY


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


def calidad_activa() -> bool:
    """¿Manda la calidad medida, o la etiqueta de siempre?"""

    if _FORZAR_ETIQUETA:
        return False

    valor = str(os.environ.get(DISABLE_ENV, "")).strip().lower()

    return valor not in ("1", "true", "si", "yes", "on")


class vara_de_etiqueta:
    """
    La escalera de siempre, dentro de este bloque y solo dentro.

    Para calcular "que once habria elegido la vara anterior" sin
    tocar el entorno del proceso ni el once de verdad.
    """

    def __enter__(self):
        global _FORZAR_ETIQUETA
        self._antes = _FORZAR_ETIQUETA
        _FORZAR_ETIQUETA = True
        return self

    def __exit__(self, *_):
        global _FORZAR_ETIQUETA
        _FORZAR_ETIQUETA = self._antes
        return False


def calidad_para_la_vara(ficha: dict) -> float | None:
    """
    La calidad de este jugador en la escala de la vara.

    `None` significa "no hay medicion": quien llame usa la
    etiqueta. Nunca lanza.
    """

    try:
        if not calidad_activa():
            return None

        medida = calidad(ficha)

        if (
            not medida["available"]
            or medida["source"] != "MEDIDA"
            or medida["points_per_match"] is None
        ):
            return None

        return (
            medida["points_per_match"]
            / REFERENCIA_PUNTOS_PARTIDO
        )

    except Exception:                                # noqa: BLE001
        return None


def partidos_jugados(ficha: dict) -> int:
    """
    Partidos, no jornadas. Es el denominador correcto.

    UN CONCEPTO, DOS NOMBRES (22/09/2026)

        Biwenger lo llama `playedHome`/`playedAway`; la plantilla
        publicada, `played_home`/`played_away`. Se entienden los
        dos, igual que `in_lineup` e `is_starter`, y por el mismo
        motivo: el que lee no tiene por que saber de donde viene
        la ficha.
    """

    return (
        safe_int(
            ficha.get("playedHome")
            if ficha.get("playedHome") is not None
            else ficha.get("played_home")
        )
        + safe_int(
            ficha.get("playedAway")
            if ficha.get("playedAway") is not None
            else ficha.get("played_away")
        )
    )


def calidad(ficha: dict, hierarchy_value=None) -> dict:
    """
    Lo que este jugador puntua por partido jugado.

    Forma fija: las mismas claves haya medicion o no.
    """

    salida = {
        "available": False,
        "source": None,
        "points_per_match": None,
        "this_season": None,
        "last_season": None,
        "matches": 0,
        "weight_this": None,
        "hierarchy_quality": None,
        "reason": None,
    }

    try:
        escalera = _escalera()

        escalon = safe_int(
            hierarchy_value
            if hierarchy_value is not None
            else ficha.get("hierarchy_value")
        )

        etiqueta = escalera.get(escalon)

        salida["hierarchy_quality"] = etiqueta

        partidos = partidos_jugados(ficha)
        salida["matches"] = partidos

        pasada = safe_int(
            ficha.get("pointsLastSeason")
            if ficha.get("pointsLastSeason") is not None
            else ficha.get("points_last_season")
        )

        por_partido_pasada = (
            pasada / PARTIDOS_TEMPORADA if pasada else None
        )

        salida["last_season"] = (
            round(por_partido_pasada, 3)
            if por_partido_pasada is not None
            else None
        )

        if partidos < MINIMO_PARTIDOS:

            # LA ETIQUETA, DEGRADADA A SUPLENTE
            #
            #     Sin partidos no hay medicion. Manda la
            #     jerarquia, y la ficha dice que es ella.
            if etiqueta is None:
                return {
                    **salida,
                    "reason": (
                        "Sin partidos jugados y sin escalon "
                        "conocido: no se puede decir si es bueno."
                    ),
                }

            return {
                **salida,
                "available": True,
                "source": "ETIQUETA",
                "points_per_match": None,
                "reason": (
                    f"Sin partidos jugados esta temporada: manda "
                    f"la etiqueta ({etiqueta})."
                ),
            }

        esta = safe_int(ficha.get("points")) / partidos

        salida["this_season"] = round(esta, 3)

        peso = partidos / (partidos + K_PARTIDOS)

        salida["weight_this"] = round(peso, 3)

        if por_partido_pasada is None:
            combinada = esta
            nota = (
                f"Sin temporada anterior: {partidos} partido(s) "
                f"de esta y nada mas."
            )
        else:
            combinada = (
                peso * esta + (1 - peso) * por_partido_pasada
            )
            nota = (
                f"{partidos} partido(s) de esta temporada pesan "
                f"el {round(100 * peso)} %; la pasada, el "
                f"{round(100 * (1 - peso))} %."
            )

        return {
            **salida,
            "available": True,
            "source": "MEDIDA",
            "points_per_match": round(combinada, 3),
            "reason": nota,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo medir: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# ¿MEJORA LA VARA? (el antes y el despues del 20 %)
# ============================================================


def _correlacion(xs, ys) -> float:

    if len(xs) < 3:
        return 0.0

    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)

    numerador = sum((x - mx) * (y - my) for x, y in zip(xs, ys))

    denominador = (
        sum((x - mx) ** 2 for x in xs)
        * sum((y - my) ** 2 for y in ys)
    ) ** 0.5

    return numerador / denominador if denominador else 0.0


def comparar_varas(
    fichas: list | None,
    matchdays: int,
) -> dict:
    """
    La vara de hoy contra la vara con calidad medida.

    `fichas` necesitan: `points`, `playedHome`, `playedAway`,
    `pointsLastSeason`, `hierarchy_value`, `starter_probability`.

    Forma fija. No enciende nada.
    """

    vacio = {
        "available": False,
        "sample": 0,
        "matchdays": matchdays,
        "r_old": None,
        "r_new": None,
        "r_new_in_sample": None,
        "variance_old": None,
        "variance_new": None,
        "variance_new_in_sample": None,
        "improves": None,
        "applied": False,
        "measured": 0,
        "by_label": 0,
        "k_matches": K_PARTIDOS,
        "reason": None,
    }

    try:
        from src.analysis.lineup_engine import (
            HIERARCHY_BENCH_APPEARANCE,
            HIERARCHY_UNKNOWN_VALUE,
            weekly_expected_value,
        )

        escalera = _escalera()

        filas = []

        for ficha in (fichas or []):

            if not isinstance(ficha, dict):
                continue

            probabilidad = safe_float(
                ficha.get("starter_probability")
            )

            if probabilidad is None:
                continue

            partidos = partidos_jugados(ficha)

            if matchdays <= 0:
                continue

            rendimiento = safe_int(ficha.get("points")) / matchdays

            vieja = weekly_expected_value(
                ficha.get("hierarchy_value"),
                probabilidad,
            )

            medida = calidad(ficha)

            if not medida["available"]:
                continue

            # La vara nueva: misma participacion, otra calidad.
            escalon = safe_int(ficha.get("hierarchy_value"))

            if escalon not in escalera:
                escalon = HIERARCHY_UNKNOWN_VALUE

            titular = max(0.0, min(1.0, probabilidad / 100.0))

            participacion = (
                titular
                + (1 - titular)
                * HIERARCHY_BENCH_APPEARANCE[escalon]
            )

            if medida["source"] == "MEDIDA":
                calidad_nueva = medida["points_per_match"]
            else:
                # Degradada a la etiqueta, en la misma unidad:
                # la escalera se lleva a puntos por partido con la
                # mediana de los medidos, mas abajo.
                calidad_nueva = None

            filas.append({
                "old": vieja,
                "quality": calidad_nueva,
                "last_season_quality": (
                    medida["last_season"]
                    if medida["last_season"] is not None
                    else 0.0
                ),
                "label_quality": escalera[escalon],
                "participation": participacion,
                "points": rendimiento,
                "source": medida["source"],
                "matches": partidos,
            })

        if len(filas) < 10:
            return {
                **vacio,
                "reason": (
                    f"Solo {len(filas)} fichas con lo necesario: "
                    f"muestra insuficiente para comparar varas."
                ),
            }

        # La escalera, llevada a la unidad de los medidos, para
        # que las dos mitades sean comparables.
        medidos = [
            f["quality"]
            for f in filas
            if f["quality"] is not None
        ]

        escala = (
            statistics.fmean(medidos) if medidos else 1.0
        )

        nuevas = []

        for fila in filas:

            calidad_final = (
                fila["quality"]
                if fila["quality"] is not None
                else fila["label_quality"] * escala
            )

            nuevas.append(fila["participation"] * calidad_final)

        # LA CIFRA HONESTA Y LA CIFRA BONITA (21/09/2026)
        #
        #     La mezcla usa los puntos de ESTA temporada, y aqui
        #     se esta prediciendo... los puntos de esta temporada.
        #     Sale 73 % de varianza explicada y no vale nada: es
        #     el mismo dato en los dos lados de la cuenta.
        #
        #     La unica calidad medida que NO se solapa con lo que
        #     se predice es la de la temporada PASADA. Esa es la
        #     que decide si esto se enciende.
        #
        #     (En produccion la mezcla no seria circular: se
        #     calcularia con lo jugado hasta hoy para elegir el
        #     once de MAÑANA. Pero eso no se puede comprobar con
        #     tres jornadas y sin dejar una fuera, asi que no se
        #     usa para decidir.)
        limpias = [
            f["participation"] * f["last_season_quality"]
            for f in filas
        ]

        viejas = [f["old"] for f in filas]
        puntos = [f["points"] for f in filas]

        r_vieja = _correlacion(viejas, puntos)
        r_nueva = _correlacion(nuevas, puntos)
        r_limpia = _correlacion(limpias, puntos)

        # Manda la limpia.
        mejora = abs(r_limpia) > abs(r_vieja)

        return {
            "available": True,
            "sample": len(filas),
            "matchdays": matchdays,
            "r_old": round(r_vieja, 3),
            "r_new": round(r_limpia, 3),
            "r_new_in_sample": round(r_nueva, 3),
            "variance_old": round(100 * r_vieja ** 2, 1),
            "variance_new": round(100 * r_limpia ** 2, 1),
            "variance_new_in_sample": round(100 * r_nueva ** 2, 1),
            "improves": bool(mejora),
            "applied": False,
            "measured": sum(
                1 for f in filas if f["source"] == "MEDIDA"
            ),
            "by_label": sum(
                1 for f in filas if f["source"] == "ETIQUETA"
            ),
            "k_matches": K_PARTIDOS,
            "reason": (
                f"La vara de hoy explica el "
                f"{round(100 * r_vieja ** 2, 1)} % de la varianza "
                f"(r = {r_vieja:+.3f}). Con calidad medida sin "
                f"solaparse con lo que se predice -solo temporada "
                f"pasada-, el {round(100 * r_limpia ** 2, 1)} % "
                f"(r = {r_limpia:+.3f}), sobre {len(filas)} "
                f"fichas."
                + (
                    f" Mejora en "
                    f"{round(100 * (r_limpia ** 2 - r_vieja ** 2), 1)} "
                    f"puntos de varianza."
                    if mejora
                    else " NO mejora: no se enciende, y eso "
                    "significa que el problema no es la calidad."
                )
                + f" La mezcla con esta temporada da "
                f"{round(100 * r_nueva ** 2, 1)} %, pero es "
                f"circular -usa los mismos puntos que predice- y "
                f"no decide nada."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo comparar: "
                f"{type(error).__name__}: {error}"
            ),
        }
