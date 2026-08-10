import json
from pathlib import Path


CACHE_FILE = Path("data/player_mapping_cache.json")


def load_mapping_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}

    with open(
        CACHE_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_mapping_cache(
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


def get_cached_mapping(
    biwenger_player_id: int,
) -> dict | None:

    cache = load_mapping_cache()

    return cache.get(
        str(biwenger_player_id)
    )


def set_cached_mapping(
    biwenger_player_id: int,
    mapping: dict,
) -> None:

    cache = load_mapping_cache()

    cache[
        str(biwenger_player_id)
    ] = mapping

    save_mapping_cache(
        cache
    )