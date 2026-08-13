from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import requests

PHOTO_CACHE = Path("data") / "dashboard_player_photo_cache.json"
MAPPING_CACHE = Path("data") / "player_mapping_cache.json"

API_BASE = "https://v3.football.api-sports.io"
BIWENGER_CDN_BASE = "https://cdn.biwenger.com"

PLAYER_ALIASES = {
    "jutgla": "Ferran Jutgla",
    "ferran jutgla": "Ferran Jutgla",
    "alvaro fidalgo": "Alvaro Fidalgo",
    "valentin gomez": "Valentin Gomez",
    "javi hernandez": "Javi Hernandez",
    "jonny castro": "Jonny Castro",
    "gabriel suazo": "Gabriel Suazo",
    "gustavo puerta": "Gustavo Puerta",
    "ximo navarro": "Ximo Navarro",
    "olasagasti": "Jon Olasagasti",
    "dituro": "Matias Dituro",
    "yamal": "Lamine Yamal",
}

def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default

def repair_mojibake(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    candidates = [text]
    for encoding in ("latin1", "cp1252"):
        try:
            candidates.append(text.encode(encoding).decode("utf-8"))
        except Exception:
            pass
    def badness(s: str) -> int:
        return sum(s.count(marker) for marker in ("Ã", "Â", "â", "�"))
    return min(candidates, key=badness)

def display_name(value: Any) -> str:
    return repair_mojibake(value).strip()

def normalize_name(value: Any) -> str:
    text = unicodedata.normalize("NFKD", display_name(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9 ]+", " ", text)
    return " ".join(text.lower().split())

def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}

def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def load_photo_cache() -> dict:
    payload = load_json(PHOTO_CACHE)
    if not isinstance(payload.get("players"), dict):
        payload = {"version": 3, "players": {}}
    return payload

def load_mapping_cache() -> dict:
    payload = load_json(MAPPING_CACHE)
    for key in ("mappings", "players", "data"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            return nested
    return payload

def mapping_external_id(mapping_cache: dict, biwenger_id: int) -> int | None:
    entry = mapping_cache.get(str(biwenger_id)) or mapping_cache.get(biwenger_id) or {}
    if not isinstance(entry, dict):
        return None
    value = entry.get("external_id") or entry.get("api_football_id") or entry.get("api_id")
    value = safe_int(value)
    return value if value > 0 else None

def biwenger_photo_url(icon_hero: str | None) -> str | None:
    if not icon_hero:
        return None
    value = str(icon_hero).strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"{BIWENGER_CDN_BASE}/{value.lstrip('/')}"

def api_photo_url(external_id: int | None) -> str | None:
    if not external_id:
        return None
    return f"https://media.api-sports.io/football/players/{external_id}.png"

def request_api_players(search: str) -> list[dict]:
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        return []
    try:
        response = requests.get(
            f"{API_BASE}/players",
            headers={"x-apisports-key": api_key},
            params={"search": search},
            timeout=6,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []
    rows = payload.get("response") or []
    return rows if isinstance(rows, list) else []

def candidate_score(target_name: str, player: dict) -> float:
    candidate_name = normalize_name(player.get("name"))
    firstname = normalize_name(player.get("firstname"))
    lastname = normalize_name(player.get("lastname"))
    if not candidate_name:
        return -1
    if candidate_name == target_name:
        return 100.0
    target_tokens = set(target_name.split())
    candidate_tokens = set(candidate_name.split())
    score = len(target_tokens & candidate_tokens) * 22.0
    if target_name in candidate_name or candidate_name in target_name:
        score += 30.0
    if lastname and lastname in target_tokens:
        score += 18.0
    if firstname and firstname in target_tokens:
        score += 10.0
    return score

def resolve_api_player(player_name: str) -> dict:
    clean = normalize_name(player_name)
    if not clean:
        return {}
    query_name = PLAYER_ALIASES.get(clean, display_name(player_name))
    parts = query_name.split()
    attempts = []
    for query in (query_name, parts[-1] if parts else "", parts[0] if parts else ""):
        query = query.strip()
        if len(query) >= 3 and query not in attempts:
            attempts.append(query)
    best_player = None
    best_score = -1.0
    target = normalize_name(query_name)
    for query in attempts:
        for row in request_api_players(query):
            player = row.get("player") if isinstance(row, dict) else None
            if not isinstance(player, dict):
                continue
            score = candidate_score(target, player)
            if score > best_score:
                best_score = score
                best_player = player
        if best_score >= 95:
            break
    if not best_player or best_score < 40:
        return {}
    external_id = safe_int(best_player.get("id"))
    if external_id <= 0:
        return {}
    return {
        "api_football_id": external_id,
        "api_name": best_player.get("name"),
        "photo_url": best_player.get("photo") or api_photo_url(external_id),
        "match_score": round(best_score, 1),
        "source": "API_FOOTBALL",
    }

def iter_catalog_players(snapshot: dict) -> list[dict]:
    raw = snapshot.get("catalog", {}).get("data", {}).get("players", {}) or {}
    if isinstance(raw, list):
        return [p for p in raw if isinstance(p, dict)]
    if isinstance(raw, dict):
        return [v for v in raw.values() if isinstance(v, dict)]
    return []

def build_player_photo_lookup(snapshot: dict) -> dict[int, dict]:
    photo_cache = load_photo_cache()
    cache_players = photo_cache.setdefault("players", {})
    mapping_cache = load_mapping_cache()

    my_team = snapshot.get("my_team", []) or []
    all_players = list(my_team) + iter_catalog_players(snapshot)

    by_id: dict[int, dict] = {}
    for player in all_players:
        if not isinstance(player, dict):
            continue
        player_id = safe_int(player.get("id"))
        if player_id <= 0:
            continue
        existing = by_id.setdefault(player_id, {})
        existing.update({k: v for k, v in player.items() if v not in (None, "")})

    target_ids = {
        safe_int(player.get("id"))
        for player in my_team
        if isinstance(player, dict)
    }

    result: dict[int, dict] = {}
    cache_changed = False

    for player_id in target_ids:
        if player_id <= 0:
            continue

        player = by_id.get(player_id, {})
        fixed_name = display_name(player.get("name") or f"Player {player_id}")

        icon_hero = player.get("iconHero") or player.get("icon_hero")
        biwenger_url = biwenger_photo_url(icon_hero)

        cached = cache_players.get(str(player_id))
        if not isinstance(cached, dict):
            cached = {}

        external_id = safe_int(cached.get("api_football_id")) or mapping_external_id(mapping_cache, player_id)
        api_url = cached.get("api_photo_url") or api_photo_url(external_id)

        if not biwenger_url and not api_url:
            resolved = resolve_api_player(fixed_name)
            if resolved:
                external_id = resolved.get("api_football_id")
                api_url = resolved.get("photo_url")
                cache_players[str(player_id)] = {
                    "biwenger_id": player_id,
                    "biwenger_name": fixed_name,
                    "api_football_id": external_id,
                    "api_name": resolved.get("api_name"),
                    "api_photo_url": api_url,
                    "match_score": resolved.get("match_score"),
                    "source": resolved.get("source"),
                }
                cache_changed = True

        photo_url = biwenger_url or api_url

        result[player_id] = {
            "name": fixed_name,
            "icon_hero": icon_hero,
            "biwenger_photo_url": biwenger_url,
            "api_football_id": external_id or None,
            "api_photo_url": api_url,
            "photo_url": photo_url,
            "photo_source": "BIWENGER" if biwenger_url else "API_FOOTBALL" if api_url else "FALLBACK",
        }

    if cache_changed:
        photo_cache["version"] = 3
        save_json(PHOTO_CACHE, photo_cache)

    return result
