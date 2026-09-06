"""
¿Paga TENER? El retrotest que decide.

LA PREGUNTA (14/09/2026)

    Pepe sabe valorar dos cosas: comprar para mejorar el once y
    comprar para revender al Computer. Lo que no sabe valorar es
    TENER.

    Y ahi esta el hueco. Amatucci se rechazo, entre otras cosas,
    porque "como especulacion rinde un 1,3 %, por debajo del 3 %
    que exige la casa". Pero ese 1,3 % es la prima de reventa
    inmediata. Amatucci sube un 1,098 % CADA DIA y lleva 19 dias
    seguidos haciendolo: cruza el 3 % en menos de tres dias.

    Si tener paga, hay 5.350.683 EUR durmiendo al 0 %.

LA UNICA PREGUNTA QUE IMPORTA

    Si el dia D compro un jugador cuyo precio sube a una tasa `r`
    con una racha de `n` dias, y lo vendo `m` dias despues,
    ¿cuanto gano de verdad?

DE DONDE SALEN LOS DATOS, Y HASTA DONDE LLEGAN

    `data/autopilot/price_history.json`. La regla de la casa es
    no medir el ESTADO contra `data/` porque miente sobre el hoy.
    Un HISTORICO es otra cosa: no pretende ser el estado actual,
    pretende ser lo que paso, y lo que paso no caduca.

    Lo que hay, medido y no supuesto:

        573 jugadores, 554 de ellos con la serie completa
        6 dias: del 12/08/2026 al 17/08/2026
        5 transiciones diarias por jugador

    De ahi salen dos limitaciones que NO se tapan:

        - los horizontes de 7 y 10 dias no se pueden medir. Esas
          celdas salen VACIAS y dicen que estan vacias.
        - la racha maxima observable es de 5 dias, asi que el
          tramo "mas de 7 dias" tampoco existe.

    Un retrotest con celdas rellenadas a ojo es peor que no
    tenerlo.

QUE ES EL RENDIMIENTO AQUI

    `(precio[i+m] - precio[i]) / precio[i]`

    Comprar al precio del dia i y vender m dias despues. Sin
    prima de reventa, sin puntos, sin nada mas: solo la rampa.

    Es a proposito. La prima del Computer se mide contra el
    precio del momento, asi que si el precio esta subiendo parte
    de esa prima YA ES la rampa. Sumarlas seria contar el mismo
    euro dos veces.
"""

from __future__ import annotations

import json
import statistics

from datetime import datetime
from pathlib import Path


STORE = Path("data") / "autopilot" / "price_history.json"


# Los tramos que pide el encargo, mas el de los que caen, que
# hace falta para la cola de ventas y que esconderlo seria
# enseñar solo la mitad buena.
RATE_BUCKETS = (
    ("CAE", None, 0.0),
    ("0-0,25 %", 0.0, 0.0025),
    ("0,25-0,5 %", 0.0025, 0.005),
    ("0,5-1 %", 0.005, 0.01),
    ("> 1 %", 0.01, None),
)

STREAK_BUCKETS = (
    ("1 dia", 1, 1),
    ("2 dias", 2, 2),
    ("3-7 dias", 3, 7),
    ("> 7 dias", 8, None),
)

# Los que pide el encargo, mas el 4: es el horizonte mas largo
# que la ventana de seis dias permite medir, y dejarlo fuera
# seria tirar el unico dato que hay mas alla del tercer dia.
HORIZONS = (1, 2, 3, 4, 5, 7, 10)


# Por debajo de esto una celda no dice nada y se marca como
# insuficiente en vez de publicar una mediana de cuatro casos.
MIN_SAMPLE = 30


def _load(path: Path | None = None) -> dict:
    try:
        return json.loads(
            (path or STORE).read_text(encoding="utf-8")
        )
    except Exception:                               # noqa: BLE001
        return {}


def load_series(path: Path | None = None) -> dict:
    """
    `{player_id: [precio_dia_0, precio_dia_1, ...]}`.

    Un precio por DIA. Si un dia tiene varias muestras se queda
    la ultima, que es la que vale cuando el mercado ya cerro.
    """

    almacen = _load(path)

    series = {}

    for player_id, ficha in (almacen.get("players") or {}).items():

        if not isinstance(ficha, dict):
            continue

        marcas = ficha.get("t") or []
        precios = ficha.get("p") or []

        if len(marcas) != len(precios) or len(precios) < 2:
            continue

        por_dia = {}

        for marca, precio in zip(marcas, precios):

            try:
                dia = datetime.fromtimestamp(marca).date()
                valor = int(precio)

            except (TypeError, ValueError, OSError):
                continue

            if valor > 0:
                por_dia[dia] = valor

        if len(por_dia) < 2:
            continue

        series[int(player_id)] = [
            por_dia[dia] for dia in sorted(por_dia)
        ]

    return series


def daily_rate(precios: list, i: int):
    """
    La tasa del dia `i`: cuanto se movio respecto al dia anterior.
    """

    if i <= 0 or i >= len(precios):
        return None

    anterior = precios[i - 1]

    if anterior <= 0:
        return None

    return (precios[i] - anterior) / anterior


def streak(precios: list, i: int) -> int:
    """
    Cuantos dias seguidos lleva moviendose en la misma direccion,
    contando el dia `i`.

    Es la misma definicion que usa FutbolFantasy en su columna
    `Tend`: dias consecutivos subiendo o bajando.
    """

    tasa = daily_rate(precios, i)

    if tasa is None or tasa == 0:
        return 0

    signo = 1 if tasa > 0 else -1
    dias = 1
    j = i - 1

    while j >= 1:

        anterior = daily_rate(precios, j)

        if anterior is None or anterior == 0:
            break

        if (1 if anterior > 0 else -1) != signo:
            break

        dias += 1
        j -= 1

    return dias


def _bucket(valor, buckets):
    for nombre, minimo, maximo in buckets:

        if minimo is not None and valor < minimo:
            continue

        if maximo is not None and valor >= maximo:
            continue

        return nombre

    return None


def _rate_bucket(tasa):
    if tasa is None:
        return None

    if tasa < 0:
        return "CAE"

    for nombre, minimo, maximo in RATE_BUCKETS[1:]:

        if maximo is None:
            if tasa >= minimo:
                return nombre
            continue

        if minimo <= tasa < maximo:
            return nombre

    return None


def _streak_bucket(dias: int):
    if dias <= 0:
        return None

    for nombre, minimo, maximo in STREAK_BUCKETS:

        if maximo is None:
            if dias >= minimo:
                return nombre
            continue

        if minimo <= dias <= maximo:
            return nombre

    return None


def build_operations(series: dict) -> list:
    """
    Todas las compras posibles del historico, con su resultado.

    Una operacion por (jugador, dia de compra, horizonte). El dia
    de compra tiene que tener tasa y racha conocidas, asi que
    nunca es el primero de la serie.
    """

    operaciones = []

    for player_id, precios in series.items():

        for i in range(1, len(precios)):

            tasa = daily_rate(precios, i)

            if tasa is None:
                continue

            racha = streak(precios, i)

            compra = precios[i]

            if compra <= 0:
                continue

            for m in HORIZONS:

                if i + m >= len(precios):
                    continue

                venta = precios[i + m]

                operaciones.append(
                    {
                        "player_id": player_id,
                        "day_index": i,
                        "rate": tasa,
                        "rate_bucket": _rate_bucket(tasa),
                        "streak": racha,
                        "streak_bucket": _streak_bucket(racha),
                        "horizon": m,
                        "buy": compra,
                        "sell": venta,
                        "return": (venta - compra) / compra,
                    }
                )

    return operaciones


def _stats(retornos: list) -> dict:
    """
    Lo que hay que mirar de un grupo de operaciones.

    Con menos de `MIN_SAMPLE` no se publica mediana: se dice que
    la muestra no llega. Una mediana de cuatro casos parece un
    dato y no lo es.
    """

    n = len(retornos)

    if n == 0:
        return {
            "n": 0,
            "enough": False,
            "reason": "Sin operaciones en el historico.",
        }

    if n < MIN_SAMPLE:
        return {
            "n": n,
            "enough": False,
            "reason": (
                f"Solo {n} operaciones; hacen falta {MIN_SAMPLE} "
                f"para publicar una mediana."
            ),
        }

    ordenados = sorted(retornos)

    def percentil(q):
        return ordenados[
            min(int(q * (n - 1)), n - 1)
        ]

    perdidas = sum(1 for r in retornos if r < 0)

    return {
        "n": n,
        "enough": True,
        "median": statistics.median(ordenados),
        "p25": percentil(0.25),
        "p75": percentil(0.75),
        "mean": statistics.fmean(ordenados),
        "loss_rate": perdidas / n,
        "reason": None,
    }


def backtest(path: Path | None = None) -> dict:
    """
    La tabla entera. Nunca lanza.
    """

    try:
        series = load_series(path)

        if not series:
            return {
                "available": False,
                "reason": (
                    "No hay historico de precios que recorrer."
                ),
                "cells": {},
            }

        operaciones = build_operations(series)

        dias = max(len(p) for p in series.values())

        celdas = {}

        for _, tramo_tasa in enumerate(
            [b[0] for b in RATE_BUCKETS]
        ):
            for tramo_racha in [b[0] for b in STREAK_BUCKETS]:
                for m in HORIZONS:

                    grupo = [
                        o["return"]
                        for o in operaciones
                        if o["rate_bucket"] == tramo_tasa
                        and o["streak_bucket"] == tramo_racha
                        and o["horizon"] == m
                    ]

                    celdas[f"{tramo_tasa}|{tramo_racha}|{m}"] = {
                        "rate_bucket": tramo_tasa,
                        "streak_bucket": tramo_racha,
                        "horizon": m,
                        **_stats(grupo),
                    }

        # Y el resumen por horizonte para los que SUBEN, que es la
        # via TENER: de ahi sale el `m` que se usaria.
        por_horizonte = {}

        for m in HORIZONS:

            grupo = [
                o["return"]
                for o in operaciones
                if o["horizon"] == m and o["rate"] > 0
            ]

            por_horizonte[m] = _stats(grupo)

        return {
            "available": True,
            "reason": None,

            "players": len(series),
            "days": dias,
            "operations": len(operaciones),
            "min_sample": MIN_SAMPLE,

            "window": _window(path),

            "cells": celdas,
            "by_horizon_rising": por_horizonte,

            "horizons": list(HORIZONS),
            "rate_buckets": [b[0] for b in RATE_BUCKETS],
            "streak_buckets": [b[0] for b in STREAK_BUCKETS],
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"El retrotest no pudo correr: "
                f"{type(error).__name__}: {error}"
            ),
            "cells": {},
        }


def _window(path: Path | None = None) -> dict:
    almacen = _load(path)

    marcas = [
        t
        for ficha in (almacen.get("players") or {}).values()
        if isinstance(ficha, dict)
        for t in (ficha.get("t") or [])
    ]

    if not marcas:
        return {"from": None, "to": None, "days": 0}

    desde = datetime.fromtimestamp(min(marcas)).date()
    hasta = datetime.fromtimestamp(max(marcas)).date()

    return {
        "from": desde.isoformat(),
        "to": hasta.isoformat(),
        "days": (hasta - desde).days + 1,
    }


def best_horizon(resultado: dict):
    """
    El `m` que maximiza la mediana entre los que suben.

    No el que da el numero mas bonito: el que maximiza la
    mediana, y solo entre las celdas con muestra suficiente.
    """

    candidatos = [
        (m, datos["median"])
        for m, datos in (
            (resultado or {}).get("by_horizon_rising") or {}
        ).items()
        if datos.get("enough")
    ]

    if not candidatos:
        return None

    return max(candidatos, key=lambda par: par[1])[0]
