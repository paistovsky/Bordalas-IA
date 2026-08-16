from __future__ import annotations

"""
Velocidad de precio por jugador, medida sobre varios dias.

POR QUE NO BASTA EL INCREMENTO DE AYER

    Medido el 16/08/2026 sobre 80 snapshots: para predecir lo que
    hace el precio en los tres dias siguientes, la velocidad de
    los tres dias anteriores explica un R2 de 0,674 y el
    incremento de ayer un 0,659. Un solo dia es ruidoso.

    La diferencia es modesta, y por eso el incremento de ayer
    sigue valiendo de respaldo cuando no hay historial. Lo que no
    vale es no decir cual de los dos se ha usado.
"""

from src.analysis.market_trend_engine import (
    analyze_player_trend,
)

from src.analysis.price_history_engine import (
    build_price_history_index,
)


# Sin un minimo de registros la velocidad es una recta entre dos
# puntos y no mide nada.
MIN_RECORDS = 3


# El ciclo lo pide dos veces -motor de pujas y telemetria- y
# analizar 572 historiales no hace falta repetirlo.
_CACHE: dict = {}


def build_velocity_lookup(
    directory: str | None = None,
) -> dict:
    """
    {player_id: porcentaje diario} con los jugadores que tienen
    historial suficiente.

    Nunca lanza: sin historial devuelve un diccionario vacio y
    quien llame se queda con el incremento de ayer.
    """

    clave = directory or "__default__"

    if clave in _CACHE:
        return _CACHE[clave]

    try:
        indice = (
            build_price_history_index(directory)
            if directory
            else build_price_history_index()
        )

    except Exception:
        return {}

    velocidades = {}

    for player_id, historial in (indice or {}).items():

        try:
            analisis = analyze_player_trend(historial)

        except Exception:
            continue

        if not analisis.get("available"):
            continue

        if int(analisis.get("records", 0) or 0) < MIN_RECORDS:
            continue

        velocidad = analisis.get("velocity") or {}

        if not velocidad.get("available"):
            continue

        porcentaje = velocidad.get("percent_per_day")

        if porcentaje is None:
            continue

        try:
            velocidades[int(player_id)] = float(porcentaje)

        except (TypeError, ValueError):
            continue

    _CACHE[clave] = velocidades

    return velocidades
