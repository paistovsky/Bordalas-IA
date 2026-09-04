"""
Quien lanza los penaltis. Apagado desde el 04/09/2026.

NO HA FUNCIONADO NUNCA

    `penalty_kickers.json`: 39 de 39 jugadores con `role:
    UNKNOWN`, `bonus: 0.0`. El `PRIMARY_BONUS = 8.0` que ordena
    el XI no se ha aplicado jamas, ni una vez, desde que se
    escribio.

POR QUE, EXACTAMENTE

    El plan de API-Football es Free, y la cadena esta cortada en
    dos sitios distintos por la misma razon:

    1. LA IDENTIDAD SE BUSCA EN 2024.

       `search_player` consulta con `PLAYER_LOOKUP_SEASON = 2024`
       -y el comentario dice por que: "el plan Free permite
       consultar jugadores ahi"-. Quien llego a LaLiga despues de
       2024 no aparece. En la cache de emparejamiento son 21 de
       44 con `external_id: null`: Gustavo Puerta, Valentin
       Gomez, Gabriel Suazo, Alvaro Fidalgo, Bayindir, Mangala...
       Todos fichajes posteriores. Son los 33 registros con
       `mapping_safe: false`.

    2. LAS ESTADISTICAS SE PIDEN DE 2026.

       Y para los 6 que SI emparejaron bien, la llamada de
       estadisticas pide `season = CURRENT_SEASON = 2026`, que el
       plan Free rechaza con todas las letras:

           "Free plans do not have access to this season,
            try from 2022 to 2024."

       Esos 6 errores estan escritos en el propio fichero.

    O sea: no es un fallo de emparejamiento que se pueda afinar.
    Con este plan no hay temporada en la que las dos mitades se
    puedan hacer a la vez. La identidad solo se resuelve en 2024
    y la estadistica de 2026 no se sirve.

POR QUE APAGADO Y NO ARREGLADO

    El arreglo aparente -pedir las estadisticas de 2024- seria
    peor que no tener el dato: pondria un +8 en el XI de 2026 por
    penaltis lanzados hace dos temporadas, y para casi la mitad
    de la plantilla no habria dato en absoluto. Un bonus de 8
    puntos ordena el once. No se alimenta con evidencia de otra
    temporada.

    Y ademas cuesta: 6 llamadas diarias a un endpoint que siempre
    responde el mismo error, cada 24 h, contra una cuota Free.

    Asi que se apaga. El resultado es identico al de hoy -bonus
    0.0 para todos, que es lo que lleva saliendo desde el primer
    dia- pero sin gastar cuota y diciendo la verdad sobre por que.

COMO SE VUELVE A ENCENDER

    Con un plan de pago que sirva la temporada en curso: poner
    `PENALTY_INTELLIGENCE_ENABLED=1` en el entorno, o el flag a
    True. La maquinaria entera -mapeo, extraccion, roles y
    bonus- se queda intacta y probada a proposito, para que
    encender sea una linea y no una reconstruccion.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from src.intelligence.api_football import CURRENT_SEASON, api_get
from src.intelligence.bulk_player_mapper import map_player

CACHE_FILE = Path("data") / "intelligence" / "penalty_kickers.json"
CACHE_TTL_SECONDS = 24 * 60 * 60

PRIMARY_BONUS = 8.0
SECONDARY_BONUS = 3.0
UNKNOWN_BONUS = 0.0


# El interruptor. False mientras el plan de API-Football sea Free:
# ver la explicacion entera arriba.
PENALTY_INTELLIGENCE_ENABLED = (
    os.getenv("PENALTY_INTELLIGENCE_ENABLED", "").strip().lower()
    in {"1", "true", "si", "sí", "yes"}
)


DISABLED_REASON = (
    "Penalty Intelligence apagado el 04/09/2026: el plan Free de "
    "API-Football resuelve identidades solo hasta 2024 y no sirve "
    "estadisticas de la temporada en curso, asi que la señal salio "
    "UNKNOWN en 39 de 39 jugadores desde el primer dia. Se apaga "
    "para no gastar cuota en una llamada que siempre falla. Bonus "
    "0.0, igual que hasta hoy."
)


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {"players": {}}

    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"players": {}}


def _save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _cached_player(cache: dict, biwenger_id: int) -> dict | None:
    raw = (cache.get("players", {}) or {}).get(str(biwenger_id))

    if not isinstance(raw, dict):
        return None

    fetched_at = int(raw.get("fetched_at_unix", 0) or 0)

    if fetched_at <= 0:
        return None

    if int(time.time()) - fetched_at > CACHE_TTL_SECONDS:
        return None

    return raw


def _role_from_taken(taken: int) -> tuple[str, float, str]:
    if taken >= 2:
        return (
            "PRIMARY_EVIDENCE",
            PRIMARY_BONUS,
            "Ha lanzado al menos 2 penaltis en la temporada consultada.",
        )

    if taken == 1:
        return (
            "SECONDARY_EVIDENCE",
            SECONDARY_BONUS,
            "Ha lanzado 1 penalti en la temporada consultada.",
        )

    return (
        "UNKNOWN",
        UNKNOWN_BONUS,
        "Sin evidencia suficiente de lanzamientos de penalti.",
    )


def _extract_penalty_stats(response: list[dict]) -> dict:
    scored = 0
    missed = 0
    appearances = 0

    for record in response or []:
        for stats in (record.get("statistics", []) or []):
            penalty = stats.get("penalty", {}) or {}
            games = stats.get("games", {}) or {}

            scored += int(penalty.get("scored", 0) or 0)
            missed += int(penalty.get("missed", 0) or 0)
            appearances += int(games.get("appearences", 0) or 0)

    return {
        "taken": scored + missed,
        "scored": scored,
        "missed": missed,
        "appearances": appearances,
    }


def get_penalty_context(snapshot: dict, player: dict) -> dict:
    """
    Señal conservadora y fail-open.
    Nunca bloquea a Pepe ni fuerza una titularidad.
    Si API-Football o el mapping fallan, bonus = 0.
    """

    biwenger_id = int(player["id"])

    # APAGADO: ni red, ni disco, ni cuota. Y la misma forma de
    # respuesta de siempre, para que quien la lea no note nada
    # distinto de lo que ya venia leyendo.
    if not PENALTY_INTELLIGENCE_ENABLED:
        return {
            "biwenger_id": biwenger_id,
            "player_name": player.get("name"),
            "season": CURRENT_SEASON,
            "role": "UNKNOWN",
            "bonus": UNKNOWN_BONUS,
            "taken": 0,
            "scored": 0,
            "missed": 0,
            "external_id": None,
            "mapping_safe": False,
            "available": False,
            "enabled": False,
            "reason": DISABLED_REASON,
            "error": None,
            "fetched_at_unix": None,
            "from_cache": False,
        }

    cache = _load_cache()
    cached = _cached_player(cache, biwenger_id)

    if cached is not None:
        return {**cached, "from_cache": True}

    base = {
        "biwenger_id": biwenger_id,
        "player_name": player.get("name"),
        "season": CURRENT_SEASON,
        "role": "UNKNOWN",
        "bonus": UNKNOWN_BONUS,
        "taken": 0,
        "scored": 0,
        "missed": 0,
        "external_id": None,
        "mapping_safe": False,
        "available": False,
        "enabled": True,
        "reason": "Sin evidencia externa.",
        "error": None,
        "fetched_at_unix": int(time.time()),
        "from_cache": False,
    }

    try:
        mapping = map_player(snapshot, player)

        base["mapping_safe"] = bool(
            mapping.get("safe_for_automatic_use", False)
        )

        external_id = mapping.get("external_id")
        base["external_id"] = external_id

        if not base["mapping_safe"] or external_id is None:
            base["reason"] = (
                "Mapping API-Football no validado; no se aplica bonus."
            )
            cache.setdefault("players", {})[str(biwenger_id)] = base
            _save_cache(cache)
            return base

        data = api_get(
            "players",
            params={
                "id": int(external_id),
                "league": 140,
                "season": int(CURRENT_SEASON),
            },
        )

        stats = _extract_penalty_stats(data.get("response", []))
        role, bonus, reason = _role_from_taken(stats["taken"])

        base.update(
            {
                **stats,
                "role": role,
                "bonus": float(bonus),
                "available": True,
                "reason": reason,
            }
        )

    except Exception as error:
        base["error"] = f"{type(error).__name__}: {error}"
        base["reason"] = (
            "Penalty Intelligence no disponible; Pepe continúa con bonus 0."
        )

    cache.setdefault("players", {})[str(biwenger_id)] = base
    _save_cache(cache)

    return base
