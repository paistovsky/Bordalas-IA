from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

LALIGA_STANDINGS_URL = "https://www.laliga.com/laliga-easports/clasificacion"

CACHE_DIR = Path("data") / "league_center"
LALIGA_CACHE_FILE = CACHE_DIR / "laliga_standings.json"
LALIGA_CACHE_TTL_SECONDS = 6 * 60 * 60

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
}


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def normalize_text(value: str | None) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _catalog_players(catalog: dict) -> list[dict]:
    raw = catalog.get("data", {}).get("players", {}) or {}

    if isinstance(raw, dict):
        return [v for v in raw.values() if isinstance(v, dict)]

    if isinstance(raw, list):
        return [v for v in raw if isinstance(v, dict)]

    return []


def biwenger_team_logo(team_id: int | None) -> str | None:
    if not team_id:
        return None

    return f"https://cdn.biwenger.com/i/t/{int(team_id)}.png"


def _catalog_index(catalog: dict) -> dict[int, dict]:
    return {
        safe_int(player.get("id")): player
        for player in _catalog_players(catalog)
        if safe_int(player.get("id")) > 0
    }


def _profile_index(profiles: list[dict]) -> dict[int, dict]:
    result = {}

    for profile in profiles or []:
        user_id = safe_int(profile.get("id"))

        if user_id > 0:
            result[user_id] = profile

    return result


def _event_icon_index(events: list[dict]) -> dict[int, str]:
    result: dict[int, str] = {}

    def remember(user) -> None:
        # Algunos eventos del tabl?n pueden traer "to"/"from"
        # como string, id suelto o None en lugar de un objeto user.
        # Para telemetr?a de iconos simplemente los ignoramos.
        if not isinstance(user, dict):
            return

        user_id = safe_int(user.get("id"))
        icon = user.get("icon")

        if user_id > 0 and icon:
            result[user_id] = str(icon)

    for event in events or []:
        remember(event.get("author"))
        content = event.get("content")

        if not isinstance(content, list):
            continue

        for operation in content:
            remember(operation.get("to"))
            remember(operation.get("from"))

            for bid in operation.get("bids", []) or []:
                remember(bid.get("user"))

    return result


def build_fantasy_standings(
    *,
    rival_intelligence: dict,
    profiles: list[dict],
    events: list[dict],
) -> list[dict]:

    profile_index = _profile_index(profiles)
    event_icons = _event_icon_index(events)

    managers = list(rival_intelligence.get("managers", []) or [])

    managers.sort(
        key=lambda item: (
            -safe_int(item.get("points")),
            -safe_int(item.get("net_worth")),
            str(item.get("name", "")),
        )
    )

    rows = []

    for rank, manager in enumerate(managers, start=1):
        user_id = safe_int(manager.get("user_id"))
        profile = profile_index.get(user_id, {}) or {}

        rows.append({
            "rank": rank,
            "user_id": user_id,
            "name": manager.get("name", "?"),
            "points": safe_int(manager.get("points")),
            "balance": safe_int(manager.get("balance")),
            "roster_value": safe_int(manager.get("roster_value")),
            "net_worth": safe_int(manager.get("net_worth")),
            "is_us": manager.get("threat_level") == "US",
            "icon": profile.get("icon") or event_icons.get(user_id),
        })

    return rows


def _owner_index(rival_intelligence: dict) -> dict[int, dict]:
    result = {}

    for manager in rival_intelligence.get("managers", []) or []:
        for player in manager.get("roster", []) or []:
            player_id = safe_int(player.get("id"))

            if player_id <= 0:
                continue

            result[player_id] = {
                "name": manager.get("name", "?"),
                "is_us": manager.get("threat_level") == "US",
            }

    return result


def build_top_players(
    *,
    catalog: dict,
    rival_intelligence: dict,
    limit: int = 10,
) -> list[dict]:

    owners = _owner_index(rival_intelligence)
    players = _catalog_players(catalog)

    players.sort(
        key=lambda player: (
            -safe_float(player.get("points")),
            -safe_float(player.get("pointsLastSeason")),
            -safe_int(player.get("price")),
            str(player.get("name", "")),
        )
    )

    rows = []

    for player in players[:limit]:
        player_id = safe_int(player.get("id"))

        rows.append({
            "rank": len(rows) + 1,
            "id": player_id,
            "name": player.get("name", "?"),
            "points": safe_float(player.get("points")),
            "points_last_season": safe_float(player.get("pointsLastSeason")),
            "price": safe_int(player.get("price")),
            "price_increment": safe_int(player.get("priceIncrement")),
            "owner": owners.get(
                player_id,
                {"name": "Computer / libre", "is_us": False},
            ),
        })

    return rows


def build_market_feed(
    *,
    events: list[dict],
    catalog: dict,
    limit: int = 30,
) -> list[dict]:

    catalog_index = _catalog_index(catalog)
    rows = []

    ordered = sorted(
        events or [],
        key=lambda event: safe_int(event.get("date")),
        reverse=True,
    )

    for event in ordered:
        event_type = event.get("type")

        if event_type not in {"market", "transfer"}:
            continue

        content = event.get("content")

        if not isinstance(content, list):
            continue

        event_date = safe_int(event.get("date"))

        for operation in content:
            player_id = safe_int(operation.get("player"))
            player = catalog_index.get(player_id, {}) or {}
            player_name = player.get("name") or f"Jugador {player_id}"
            amount = safe_int(operation.get("amount"))
            current_price = safe_int(player.get("price"))

            if event_type == "market":
                buyer = operation.get("to", {}) or {}

                if not buyer:
                    continue

                rows.append({
                    "timestamp": event_date,
                    "type": "BUY_FROM_COMPUTER",
                    "player_id": player_id,
                    "player_name": player_name,
                    "amount": amount,
                    "current_price": current_price,
                    "buyer": buyer.get("name", "?"),
                    "seller": "Computer",
                })

            else:
                seller = operation.get("from", {}) or {}
                buyer = operation.get("to", {}) or {}

                if not seller:
                    continue

                rows.append({
                    "timestamp": event_date,
                    "type": "USER_TRANSFER" if buyer else "SELL_TO_COMPUTER",
                    "player_id": player_id,
                    "player_name": player_name,
                    "amount": amount,
                    "current_price": current_price,
                    "buyer": buyer.get("name", "?") if buyer else "Computer",
                    "seller": seller.get("name", "?"),
                })

            if len(rows) >= limit:
                return rows

    return rows


def _load_laliga_cache() -> dict | None:
    if not LALIGA_CACHE_FILE.exists():
        return None

    try:
        return json.loads(
            LALIGA_CACHE_FILE.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return None


def _save_laliga_cache(payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LALIGA_CACHE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _laliga_cache_fresh(payload: dict) -> bool:
    fetched_at = safe_int(payload.get("fetched_at_unix"))

    return (
        fetched_at > 0
        and int(time.time()) - fetched_at < LALIGA_CACHE_TTL_SECONDS
    )


def _absolute_url(value: str | None) -> str | None:
    if not value:
        return None

    value = str(value)

    if value.startswith(("http://", "https://")):
        return value

    if value.startswith("//"):
        return "https:" + value

    if value.startswith("/"):
        return "https://www.laliga.com" + value

    return value


def _row_logo(row) -> str | None:
    image = row.find("img")

    if image is None:
        return None

    for key in ("src", "data-src", "data-lazy-src"):
        value = image.get(key)

        if value:
            return _absolute_url(value)

    srcset = image.get("srcset")

    if srcset:
        first = str(srcset).split(",")[0].strip().split(" ")[0]
        return _absolute_url(first)

    return None


def _numeric(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?\d+", value.strip()))


def _parse_table_rows(soup: BeautifulSoup) -> list[dict]:
    result = []

    for row in soup.find_all("tr"):
        cells = [
            " ".join(cell.stripped_strings)
            for cell in row.find_all(["th", "td"])
        ]

        if len(cells) < 9:
            continue

        position_index = None

        for index, cell in enumerate(cells[:3]):
            if _numeric(cell) and 1 <= safe_int(cell) <= 20:
                position_index = index
                break

        if position_index is None:
            continue

        tail = cells[position_index + 1:]
        numeric_tail = [cell for cell in tail if _numeric(cell)]

        if len(numeric_tail) < 8:
            continue

        team_candidates = [
            cell
            for cell in tail
            if cell and not _numeric(cell)
        ]

        if not team_candidates:
            continue

        team = team_candidates[-1]
        nums = [safe_int(value) for value in numeric_tail[-8:]]

        points, played, win, draw, lose, gf, ga, gd = nums

        result.append({
            "rank": safe_int(cells[position_index]),
            "team": team,
            "logo": _row_logo(row),
            "points": points,
            "played": played,
            "win": win,
            "draw": draw,
            "lose": lose,
            "goals_for": gf,
            "goals_against": ga,
            "goals_diff": gd,
        })

    unique = {}

    for row in result:
        rank = safe_int(row.get("rank"))

        if 1 <= rank <= 20 and rank not in unique:
            unique[rank] = row

    return [unique[key] for key in sorted(unique)]


def _parse_accessible_blocks(soup: BeautifulSoup) -> list[dict]:
    rows = []

    for node in soup.find_all(["li", "div", "article"]):
        text = " ".join(node.stripped_strings)

        if not 12 <= len(text) <= 220:
            continue

        tokens = text.split()

        if not tokens or not _numeric(tokens[0]):
            continue

        rank = safe_int(tokens[0])

        if not 1 <= rank <= 20:
            continue

        numeric_positions = [
            index
            for index, token in enumerate(tokens)
            if _numeric(token)
        ]

        if len(numeric_positions) < 9:
            continue

        stat_tokens = [
            tokens[index]
            for index in numeric_positions[-8:]
        ]

        first_stat_index = numeric_positions[-8]

        if first_stat_index <= 2:
            continue

        # El segundo token suele ser la abreviatura del club.
        team = " ".join(tokens[2:first_stat_index]).strip()

        if not team:
            continue

        points, played, win, draw, lose, gf, ga, gd = [
            safe_int(value)
            for value in stat_tokens
        ]

        rows.append({
            "rank": rank,
            "team": team,
            "logo": _row_logo(node),
            "points": points,
            "played": played,
            "win": win,
            "draw": draw,
            "lose": lose,
            "goals_for": gf,
            "goals_against": ga,
            "goals_diff": gd,
        })

    unique = {}

    for row in rows:
        if row["rank"] not in unique:
            unique[row["rank"]] = row

    return [unique[key] for key in sorted(unique)]


def fetch_laliga_standings() -> dict:
    cache = _load_laliga_cache()

    if cache and _laliga_cache_fresh(cache):
        return {**cache, "cache_status": "FRESH"}

    try:
        response = requests.get(
            LALIGA_STANDINGS_URL,
            headers=DEFAULT_HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        rows = _parse_table_rows(soup)

        if len(rows) != 20:
            fallback = _parse_accessible_blocks(soup)

            if len(fallback) > len(rows):
                rows = fallback

        if len(rows) != 20:
            raise RuntimeError(
                f"LaLiga parser obtuvo {len(rows)} equipos; esperaba 20."
            )

        payload = {
            "available": True,
            "source": "LALIGA_OFFICIAL",
            "source_url": LALIGA_STANDINGS_URL,
            "league_name": "LALIGA EA SPORTS",
            "season": "2026/27",
            "standings": rows,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "fetched_at_unix": int(time.time()),
            "cache_status": "REFRESHED",
            "message": None,
        }

        _save_laliga_cache(payload)

        return payload

    except Exception as error:
        if cache:
            return {
                **cache,
                "cache_status": "STALE_SOURCE_ERROR",
                "refresh_error": f"{type(error).__name__}: {error}",
            }

        return {
            "available": False,
            "source": "LALIGA_OFFICIAL",
            "source_url": LALIGA_STANDINGS_URL,
            "league_name": "LALIGA EA SPORTS",
            "season": "2026/27",
            "standings": [],
            "cache_status": "SOURCE_ERROR",
            "message": "Clasificación real temporalmente no disponible.",
            "refresh_error": f"{type(error).__name__}: {error}",
        }


def enrich_laliga_logos(
    standings: dict,
    snapshot: dict,
) -> dict:

    teams = (
        snapshot.get("catalog", {})
        .get("data", {})
        .get("teams", {})
        or {}
    )

    team_list = [
        team
        for team in teams.values()
        if isinstance(team, dict)
    ]

    for row in standings.get("standings", []) or []:

        target = normalize_text(
            row.get("team")
        )

        best = None

        for team in team_list:

            name = normalize_text(
                team.get("name")
            )

            slug = normalize_text(
                team.get("slug")
            )

            # Match exacto primero.
            if target == name:
                best = team
                break

            # Fallback para diferencias como:
            # FC Barcelona / Barcelona
            # Atl?tico de Madrid / Atl?tico
            if (
                name
                and (
                    name in target
                    or target in name
                    or slug in target
                )
            ):
                best = team

        if best:

            team_id = safe_int(
                best.get("id")
            )

            row["biwenger_team_id"] = team_id
            row["logo"] = biwenger_team_logo(
                team_id
            )

    return standings


def build_league_center(
    *,
    snapshot: dict,
    board: dict,
    rival_intelligence: dict,
) -> dict:

    catalog = snapshot.get("catalog", {}) or {}

    laliga = fetch_laliga_standings()

    laliga = enrich_laliga_logos(
        laliga,
        snapshot,
    )

    return {
        "fantasy_standings": build_fantasy_standings(
            rival_intelligence=rival_intelligence,
            profiles=board.get("profiles", []) or [],
            events=board.get("events", []) or [],
        ),
        "top_players": build_top_players(
            catalog=catalog,
            rival_intelligence=rival_intelligence,
            limit=10,
        ),
        "market_feed": build_market_feed(
            events=board.get("events", []) or [],
            catalog=catalog,
            limit=30,
        ),
        "laliga": laliga,
    }
