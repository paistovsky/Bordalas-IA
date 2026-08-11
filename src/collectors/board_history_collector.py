from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from src.biwenger.client import BiwengerClient


DATA_DIR = Path("data") / "rival_intelligence"
BOARD_FILE = DATA_DIR / "board_events.json"
BOARD_RAW_FILE = DATA_DIR / "board_latest_raw.json"
BOARD_LIMIT = 1000


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def stable_event_id(
    event: dict,
) -> str:
    canonical = json.dumps(
        event,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:24]


def fetch_board(
    client: BiwengerClient,
    limit: int = BOARD_LIMIT,
) -> list[dict]:

    if client.league_id is None:
        raise RuntimeError(
            "La liga debe estar seleccionada."
        )

    response = client.session.get(
        (
            f"{client.BASE_URL}/league/"
            f"{client.league_id}/board"
        ),
        params={
            "limit": int(limit),
        },
        timeout=30,
    )

    response.raise_for_status()

    body = response.json()

    if body.get("status") != 200:
        raise RuntimeError(
            f"Respuesta inesperada del tablón: {body}"
        )

    data = body.get("data", [])

    if not isinstance(data, list):
        raise RuntimeError(
            "El tablón no devolvió una lista de eventos."
        )

    return data


def fetch_league_users(
    client: BiwengerClient,
) -> list[dict]:

    response = client.session.get(
        f"{client.BASE_URL}/league",
        timeout=30,
    )

    response.raise_for_status()

    body = response.json()

    if body.get("status") != 200:
        raise RuntimeError(
            f"Respuesta inesperada de /league: {body}"
        )

    return (
        body.get("data", {})
        .get("users", [])
        or []
    )


def fetch_user_profile(
    client: BiwengerClient,
    user_id: int,
) -> dict:
    """
    Perfil público del manager:
    puntos + plantilla + owner metadata.
    """

    response = client.session.get(
        f"{client.BASE_URL}/user/{int(user_id)}",
        params={
            "fields": "*,players(id,owner)",
        },
        timeout=30,
    )

    response.raise_for_status()

    body = response.json()

    if body.get("status") != 200:
        raise RuntimeError(
            f"Respuesta inesperada de user/{user_id}: {body}"
        )

    return body.get("data", {}) or {}


def fetch_user_profiles(
    client: BiwengerClient,
    users: list[dict],
) -> list[dict]:

    profiles = []

    for user in users:

        user_id = user.get("id")

        if user_id is None:
            continue

        try:
            profiles.append(
                fetch_user_profile(
                    client,
                    int(user_id),
                )
            )

        except Exception as error:
            profiles.append(
                {
                    "id":
                        int(user_id),

                    "name":
                        user.get("name", "?"),

                    "_fetch_error":
                        (
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                }
            )

    return profiles


def fetch_own_finances(
    client: BiwengerClient,
) -> dict:

    if client.user_id is None:
        raise RuntimeError(
            "Usuario no seleccionado."
        )

    response = client.session.get(
        (
            f"{client.BASE_URL}/user/"
            f"{client.user_id}/finances"
        ),
        timeout=30,
    )

    response.raise_for_status()

    body = response.json()

    if body.get("status") != 200:
        raise RuntimeError(
            f"Respuesta inesperada de finances: {body}"
        )

    return body.get("data", {}) or {}


def find_latest_full_reset(
    events: list[dict],
) -> dict | None:

    resets = [
        event
        for event in events
        if (
            event.get("type")
            == "leagueReset"
            and
            (
                event.get(
                    "content",
                    {},
                )
                or {}
            ).get("type")
            == "full"
        )
    ]

    if not resets:
        return None

    return max(
        resets,
        key=lambda item:
            int(
                item.get("date", 0)
                or 0
            ),
    )


def filter_current_league_era(
    events: list[dict],
) -> tuple[
    list[dict],
    dict | None,
]:

    reset = (
        find_latest_full_reset(
            events
        )
    )

    if reset is None:
        return (
            list(events),
            None,
        )

    reset_ts = int(
        reset.get("date", 0)
        or 0
    )

    current = [
        event
        for event in events
        if int(
            event.get("date", 0)
            or 0
        ) >= reset_ts
    ]

    return (
        current,
        reset,
    )


def normalize_board_event(
    event: dict,
) -> dict:

    return {
        "event_id":
            stable_event_id(
                event
            ),

        "date":
            int(
                event.get("date", 0)
                or 0
            ),

        "type":
            event.get("type"),

        "fixed":
            bool(
                event.get(
                    "fixed",
                    False,
                )
            ),

        "title":
            event.get("title"),

        "author":
            event.get("author"),

        "content":
            event.get("content"),
    }


def load_persisted_events() -> list[dict]:

    if not BOARD_FILE.exists():
        return []

    try:
        return json.loads(
            BOARD_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []


def merge_board_events(
    existing: list[dict],
    fresh: list[dict],
) -> tuple[
    list[dict],
    int,
]:

    by_id = {
        str(
            item.get(
                "event_id"
            )
        ):
            item
        for item in existing
        if item.get(
            "event_id"
        )
    }

    before = len(
        by_id
    )

    for item in fresh:
        by_id[
            str(
                item[
                    "event_id"
                ]
            )
        ] = item

    merged = list(
        by_id.values()
    )

    merged.sort(
        key=lambda item: (
            int(
                item.get(
                    "date",
                    0,
                )
                or 0
            ),
            str(
                item.get(
                    "event_id",
                    "",
                )
            ),
        )
    )

    return (
        merged,
        len(by_id)
        - before,
    )


def save_board_history(
    events: list[dict],
    raw_events: list[dict],
) -> None:

    ensure_data_dir()

    BOARD_FILE.write_text(
        json.dumps(
            events,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    BOARD_RAW_FILE.write_text(
        json.dumps(
            raw_events,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def collect_board_history(
    client: BiwengerClient | None = None,
) -> dict:
    """
    Captura:
      - tablón completo disponible,
      - managers,
      - perfiles/plantillas públicas,
      - finances oficiales de Pepe.

    SOLO LECTURA contra Biwenger.
    """

    if client is None:

        client = (
            BiwengerClient()
        )

        client.login()
        client.select_league()

    elif client.league_id is None:

        client.select_league()

    raw_events = (
        fetch_board(
            client
        )
    )

    (
        current_era_raw,
        reset,
    ) = (
        filter_current_league_era(
            raw_events
        )
    )

    normalized = [
        normalize_board_event(
            event
        )
        for event
        in current_era_raw
    ]

    existing = (
        load_persisted_events()
    )

    reset_ts = (
        int(
            reset.get(
                "date",
                0,
            )
            or 0
        )
        if reset
        else None
    )

    if reset_ts is not None:

        existing = [
            item
            for item in existing
            if int(
                item.get(
                    "date",
                    0,
                )
                or 0
            ) >= reset_ts
        ]

    (
        merged,
        added,
    ) = (
        merge_board_events(
            existing=
                existing,

            fresh=
                normalized,
        )
    )

    save_board_history(
        events=
            merged,

        raw_events=
            raw_events,
    )

    users = (
        fetch_league_users(
            client
        )
    )

    profiles = (
        fetch_user_profiles(
            client,
            users,
        )
    )

    finances = (
        fetch_own_finances(
            client
        )
    )

    return {
        "collected_at":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "league_id":
            client.league_id,

        "current_user_id":
            client.user_id,

        "api_events":
            len(
                raw_events
            ),

        "current_era_events":
            len(
                current_era_raw
            ),

        "persisted_events":
            len(
                merged
            ),

        "new_events":
            added,

        "reset":
            (
                normalize_board_event(
                    reset
                )
                if reset
                else None
            ),

        "users":
            users,

        "profiles":
            profiles,

        "own_finances":
            finances,

        "events":
            merged,
    }
