from __future__ import annotations

import json
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import requests
from bs4 import BeautifulSoup


CACHE_PATH = Path("data/intelligence/starter_multisource_v112.json")
TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
}

FF_TEAM_SLUGS = {
    "alaves": "alaves",
    "athletic": "athletic",
    "athletic club": "athletic",
    "atletico": "atletico",
    "atletico madrid": "atletico",
    "barcelona": "barcelona",
    "betis": "betis",
    "real betis": "betis",
    "celta": "celta",
    "celta vigo": "celta",
    "deportivo": "deportivo",
    "deportivo la coruna": "deportivo",
    "elche": "elche",
    "espanyol": "espanyol",
    "getafe": "getafe",
    "levante": "levante",
    "malaga": "malaga",
    "osasuna": "osasuna",
    "racing santander": "racing",
    "rayo": "rayo",
    "rayo vallecano": "rayo",
    "real madrid": "real-madrid",
    "real sociedad": "real-sociedad",
    "sevilla": "sevilla",
    "valencia": "valencia",
    "villarreal": "villarreal",
}


def normalize(value: str | None) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def player_name(player: dict) -> str:
    return str(
        player.get("name")
        or player.get("slug")
        or player.get("fullName")
        or ""
    ).strip()


def team_name(player: dict) -> str:
    team = player.get("team") or {}
    if isinstance(team, dict):
        return str(team.get("name") or team.get("slug") or "").strip()
    return str(player.get("teamName") or "").strip()


def fetch(url: str) -> str:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def nearest_percentage(text: str, name: str, radius: int = 240) -> float | None:
    ntext = normalize(text)
    nname = normalize(name)
    pos = ntext.find(nname)
    if pos < 0:
        return None

    raw_pos = text.lower().find(name.lower())
    if raw_pos < 0:
        raw_pos = max(0, pos)

    window = text[max(0, raw_pos - radius): raw_pos + len(name) + radius]
    values = []
    for match in re.finditer(r"(\d{1,3}(?:[.,]\d+)?)\s*%", window):
        try:
            value = float(match.group(1).replace(",", "."))
        except ValueError:
            continue
        if 0 <= value <= 100:
            values.append((abs(match.start() - radius), value))
    if not values:
        return None
    values.sort()
    return values[0][1]


def ff_signal(player: dict) -> dict | None:
    team = normalize(team_name(player))
    slug = FF_TEAM_SLUGS.get(team)
    if not slug:
        return None

    url = f"https://www.futbolfantasy.com/laliga/equipos/{slug}"
    try:
        html = fetch(url)
    except Exception as exc:
        return {
            "source": "FUTBOLFANTASY",
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
            "url": url,
        }

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    name = player_name(player)

    probability = nearest_percentage(text, name)
    if probability is None:
        # Fallback: player visible on team page but no percentage parseable.
        if normalize(name) in normalize(text):
            return {
                "source": "FUTBOLFANTASY",
                "available": True,
                "matched": True,
                "probability": None,
                "status": "UNKNOWN",
                "method": "PLAYER_PRESENT_NO_PERCENT",
                "url": url,
            }
        return {
            "source": "FUTBOLFANTASY",
            "available": True,
            "matched": False,
            "probability": None,
            "status": "UNKNOWN",
            "method": "NO_PLAYER_MATCH",
            "url": url,
        }

    status = (
        "TITULAR" if probability >= 67
        else "SUPLENTE" if probability <= 40
        else "DUDA"
    )
    return {
        "source": "FUTBOLFANTASY",
        "available": True,
        "matched": True,
        "probability": round(probability, 1),
        "status": status,
        "method": "EXPLICIT_PERCENT",
        "url": url,
    }


def discover_af_team_urls() -> dict[str, str]:
    urls = {}
    candidates = [
        "https://www.analiticafantasy.com/alineaciones-probables/la-liga/temporada-2026/jornada-1",
        "https://www.analiticafantasy.com/",
    ]

    for page in candidates:
        try:
            html = fetch(page)
        except Exception:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = str(a.get("href") or "")
            if "/equipo/" not in href:
                continue
            if href.startswith("/"):
                href = "https://www.analiticafantasy.com" + href
            label = normalize(a.get_text(" ", strip=True))
            if label:
                urls[label] = href.split("?")[0]
    return urls


def best_team_url(team: str, discovered: dict[str, str]) -> str | None:
    target = normalize(team)
    if not target:
        return None

    best = None
    best_ratio = 0.0
    for label, url in discovered.items():
        ratio = SequenceMatcher(None, target, label).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = url

    if best_ratio < 0.55:
        return None

    if not best.endswith("/once-tipo"):
        best = best.rstrip("/") + "/once-tipo"
    return best


def af_signal(player: dict, discovered: dict[str, str]) -> dict | None:
    url = best_team_url(team_name(player), discovered)
    if not url:
        return None

    try:
        html = fetch(url)
    except Exception as exc:
        return {
            "source": "ANALITICA_FANTASY",
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
            "url": url,
        }

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    ntext = normalize(text)
    name = player_name(player)
    nname = normalize(name)

    if nname not in ntext:
        return {
            "source": "ANALITICA_FANTASY",
            "available": True,
            "matched": False,
            "probability": None,
            "status": "UNKNOWN",
            "method": "NO_PLAYER_MATCH",
            "url": url,
        }

    # First try explicit percentages if AF exposes them.
    probability = nearest_percentage(text, name)
    if probability is not None:
        status = (
            "TITULAR" if probability >= 67
            else "SUPLENTE" if probability <= 40
            else "DUDA"
        )
        return {
            "source": "ANALITICA_FANTASY",
            "available": True,
            "matched": True,
            "probability": round(probability, 1),
            "status": status,
            "method": "EXPLICIT_PERCENT",
            "url": url,
        }

    # Once-tipo pages expose Titular/Suplente text even when no percentage.
    raw_pos = ntext.find(nname)
    window = ntext[max(0, raw_pos - 60): raw_pos + len(nname) + 80]
    if "titular" in window:
        return {
            "source": "ANALITICA_FANTASY",
            "available": True,
            "matched": True,
            "probability": 90.0,
            "status": "TITULAR",
            "method": "ROLE_PROXY",
            "url": url,
        }
    if "suplente" in window:
        return {
            "source": "ANALITICA_FANTASY",
            "available": True,
            "matched": True,
            "probability": 35.0,
            "status": "SUPLENTE",
            "method": "ROLE_PROXY",
            "url": url,
        }

    return {
        "source": "ANALITICA_FANTASY",
        "available": True,
        "matched": True,
        "probability": None,
        "status": "UNKNOWN",
        "method": "PLAYER_PRESENT_NO_ROLE",
        "url": url,
    }


def jp_signal(prepared_player: dict) -> dict | None:
    external = prepared_player.get("external_lineup") or {}
    status = str(external.get("status") or "UNKNOWN").upper()
    if status == "UNKNOWN":
        return None

    probability = external.get("probability")
    if probability is None:
        confidence = external.get("effective_confidence")
        if confidence is None:
            confidence = external.get("confidence")
        try:
            confidence = float(confidence or 0)
        except (TypeError, ValueError):
            confidence = 0.0

        baseline = {
            "TITULAR": 94.0,
            "PROBABLE": 76.0,
            "DUDA": 50.0,
            "SUPLENTE": 24.0,
            "NO_CONVOCADO": 1.0,
        }.get(status, 50.0)

        probability = 50.0 + (baseline - 50.0) * (confidence / 100.0)

    return {
        "source": "JORNADA_PERFECTA",
        "available": True,
        "matched": True,
        "probability": round(float(probability), 1),
        "status": status,
        "method": "CURRENT_PROVIDER",
    }


def consensus(signals: list[dict]) -> dict:
    usable = [
        s for s in signals
        if s
        and s.get("available", True)
        and s.get("matched", True)
        and s.get("probability") is not None
    ]

    values = [float(s["probability"]) for s in usable]
    probability = sum(values) / len(values) if values else 50.0

    starter_votes = sum(v >= 67 for v in values)
    bench_votes = sum(v <= 40 for v in values)

    if len(values) >= 2 and starter_votes >= 2:
        label = "STARTER"
    elif len(values) >= 2 and bench_votes >= 2:
        label = "BENCH"
    elif len(values) >= 2:
        label = "MIXED"
    elif len(values) == 1:
        label = "SINGLE_SOURCE"
    else:
        label = "NO_DATA"

    spread = (max(values) - min(values)) if len(values) >= 2 else 0.0

    if len(values) == 3 and spread <= 15:
        confidence = "HIGH"
    elif len(values) >= 2 and spread <= 30:
        confidence = "MEDIUM"
    elif len(values) >= 2:
        confidence = "LOW_CONFLICT"
    elif len(values) == 1:
        confidence = "LOW"
    else:
        confidence = "NONE"

    return {
        "starter_probability": round(probability, 1),
        "expected_minutes": round(max(0.0, min(90.0, probability * 0.90)), 1),
        "source_coverage": len(values),
        "consensus": label,
        "confidence_tier": confidence,
        "spread": round(spread, 1),
        "sources": signals,
    }


def build_board(prepared_players: list[dict]) -> list[dict]:
    discovered = discover_af_team_urls()
    board = []

    for index, player in enumerate(prepared_players):
        signals = []

        jp = jp_signal(player)
        if jp:
            signals.append(jp)

        ff = ff_signal(player)
        if ff:
            signals.append(ff)

        af = af_signal(player, discovered)
        if af:
            signals.append(af)

        result = consensus(signals)
        board.append({
            "player_id": int(player["id"]),
            "player_name": player_name(player),
            "team": team_name(player),
            "position": player.get("position"),
            "legacy_lineup_score": float(player.get("lineup_score") or 0),
            **result,
        })

        # Be polite to third-party sites.
        if index < len(prepared_players) - 1:
            time.sleep(0.15)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(
            {"version": "V11.2", "players": board},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return board
