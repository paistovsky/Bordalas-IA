import json
from datetime import datetime, timedelta
from pathlib import Path


CACHE_FILE = Path(
    "data/external_status_cache.json"
)

CACHE_HOURS = 6


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}

    with open(
        CACHE_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_cache(
    cache: dict,
) -> None:

    CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cache,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_cached_status(
    player_id: int,
) -> dict | None:

    cache = load_cache()

    item = cache.get(
        str(player_id)
    )

    if not item:
        return None

    cached_at = item.get(
        "cached_at"
    )

    if not cached_at:
        return None

    try:
        cache_time = (
            datetime.fromisoformat(
                cached_at
            )
        )

    except ValueError:
        return None

    expiration = (
        cache_time
        + timedelta(
            hours=CACHE_HOURS
        )
    )

    if datetime.now() > expiration:
        return None

    result = item.get(
        "result"
    )

    if result is None:
        return None

    return {
        **result,
        "external_from_cache": True,
    }


def set_cached_status(
    player_id: int,
    result: dict,
) -> None:

    cache = load_cache()

    cache[
        str(player_id)
    ] = {
        "cached_at":
            datetime.now().isoformat(),

        "result":
            result,
    }

    save_cache(
        cache
    )