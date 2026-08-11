from __future__ import annotations

import json
import time
from pathlib import Path

from src.intelligence.api_football import CURRENT_SEASON, api_get
from src.intelligence.bulk_player_mapper import map_player

CACHE_FILE = Path("data") / "intelligence" / "penalty_kickers.json"
CACHE_TTL_SECONDS = 24 * 60 * 60

PRIMARY_BONUS = 8.0
SECONDARY_BONUS = 3.0
UNKNOWN_BONUS = 0.0


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
