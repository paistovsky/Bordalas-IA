from __future__ import annotations

from typing import Any

BIWENGER_PLAYER_IMAGE_BASE = (
    "https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/p"
)
BIWENGER_HERO_BASE = "https://cdn.biwenger.com"


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def display_name(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""

    candidates = [text]

    for encoding in ("latin1", "cp1252"):
        try:
            candidates.append(
                text.encode(encoding).decode("utf-8")
            )
        except Exception:
            pass

    def badness(s: str) -> int:
        return sum(
            s.count(marker)
            for marker in ("Ã", "Â", "â", "�")
        )

    return min(candidates, key=badness).strip()


def standard_biwenger_photo_url(
    player_id: int | str | None,
) -> str | None:
    player_id = safe_int(player_id)

    if player_id <= 0:
        return None

    return (
        f"{BIWENGER_PLAYER_IMAGE_BASE}/"
        f"{player_id}.png"
    )


def hero_biwenger_photo_url(
    icon_hero: str | None,
) -> str | None:
    if not icon_hero:
        return None

    value = str(icon_hero).strip()

    if value.startswith("http://") or value.startswith("https://"):
        return value

    return f"{BIWENGER_HERO_BASE}/{value.lstrip('/')}"


def build_player_photo_lookup(
    snapshot: dict,
) -> dict[int, dict]:
    """
    Photo Resolver V4.

    Fuente principal:
      https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/p/{id}.png

    iconHero queda solo como fallback/metadata.

    No usa API-Football.
    No hace llamadas HTTP.
    No consume cuota.
    """

    my_team = snapshot.get("my_team", []) or []

    result: dict[int, dict] = {}

    for player in my_team:
        if not isinstance(player, dict):
            continue

        player_id = safe_int(player.get("id"))

        if player_id <= 0:
            continue

        fixed_name = display_name(
            player.get("name")
            or f"Player {player_id}"
        )

        icon_hero = (
            player.get("iconHero")
            or player.get("icon_hero")
        )

        standard_url = standard_biwenger_photo_url(
            player_id
        )

        hero_url = hero_biwenger_photo_url(
            icon_hero
        )

        result[player_id] = {
            "name": fixed_name,
            "icon_hero": icon_hero,
            "biwenger_photo_url": standard_url,
            "biwenger_hero_url": hero_url,
            "api_football_id": None,
            "api_photo_url": None,
            "photo_url": standard_url or hero_url,
            "photo_source": "BIWENGER",
        }

    return result
