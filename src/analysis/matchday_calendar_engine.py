from __future__ import annotations

import json

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path

from zoneinfo import ZoneInfo

from src.intelligence.laliga_calendar_provider import (
    fetch_dynamic_calendar,
)


MADRID_TZ = ZoneInfo(
    "Europe/Madrid"
)

SEASON_START_YEAR = 2026

DATA_DIRECTORY = (
    Path("data")
    / "calendar"
)

CACHE_FILE = (
    DATA_DIRECTORY
    / "laliga_calendar.json"
)

CHANGE_LOG_FILE = (
    DATA_DIRECTORY
    / "calendar_changes.jsonl"
)


# ============================================================
# CONFIGURACION OPERATIVA
# ============================================================


REAL_DEADLINE_MINUTES = 15
SAFETY_DEADLINE_MINUTES = 90
NEXT_ROUND_UNLOCK_MINUTES = 120


# ============================================================
# UTILIDADES
# ============================================================


def ensure_directory() -> None:

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def now_madrid() -> datetime:

    return datetime.now(
        MADRID_TZ
    )


def parse_datetime(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    try:

        parsed = (
            datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if parsed.tzinfo is None:

        parsed = (
            parsed.replace(
                tzinfo=MADRID_TZ
            )
        )

    return parsed.astimezone(
        MADRID_TZ
    )


def seconds_between(
    now: datetime,
    target: datetime | None,
) -> int | None:

    if target is None:
        return None

    return int(
        (
            target
            - now
        ).total_seconds()
    )


# ============================================================
# CACHE
# ============================================================


def load_calendar_cache() -> dict | None:

    if not CACHE_FILE.exists():
        return None

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


def save_calendar_cache(
    data: dict,
) -> None:

    ensure_directory()

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def append_calendar_changes(
    changes: list[dict],
) -> None:

    if not changes:
        return

    ensure_directory()

    with open(
        CHANGE_LOG_FILE,
        "a",
        encoding="utf-8",
    ) as file:

        for change in changes:

            file.write(
                json.dumps(
                    change,
                    ensure_ascii=False,
                )
            )

            file.write(
                "\n"
            )


# ============================================================
# NORMALIZACION
# ============================================================


def match_key(
    match: dict,
) -> str:

    return (
        f"{int(match['matchday']):02d}|"
        f"{str(match['home']).strip().lower()}|"
        f"{str(match['away']).strip().lower()}"
    )


def build_matchdays(
    matches: list[dict],
) -> list[dict]:

    grouped = {}

    for match in matches:

        matchday = int(
            match[
                "matchday"
            ]
        )

        grouped.setdefault(
            matchday,
            [],
        ).append(
            match
        )

    matchdays = []

    for matchday in sorted(
        grouped
    ):

        games = sorted(
            grouped[
                matchday
            ],
            key=lambda item:
                item[
                    "kickoff"
                ],
        )

        kickoffs = [
            parse_datetime(
                game.get(
                    "kickoff"
                )
            )

            for game in games
        ]

        kickoffs = [
            kickoff

            for kickoff in kickoffs

            if kickoff is not None
        ]

        first_kickoff = (
            min(
                kickoffs
            )
            if kickoffs
            else None
        )

        if first_kickoff is None:

            safety_deadline = None
            real_deadline = None
            next_round_unlock = None

        else:

            safety_deadline = (
                first_kickoff
                - timedelta(
                    minutes=
                        SAFETY_DEADLINE_MINUTES
                )
            )

            real_deadline = (
                first_kickoff
                - timedelta(
                    minutes=
                        REAL_DEADLINE_MINUTES
                )
            )

            next_round_unlock = (
                first_kickoff
                + timedelta(
                    minutes=
                        NEXT_ROUND_UNLOCK_MINUTES
                )
            )

        matchdays.append(
            {
                "matchday":
                    matchday,

                "matches":
                    games,

                "first_match":
                    (
                        {
                            "home":
                                games[
                                    0
                                ][
                                    "home"
                                ],

                            "away":
                                games[
                                    0
                                ][
                                    "away"
                                ],

                            "kickoff":
                                games[
                                    0
                                ][
                                    "kickoff"
                                ],
                        }
                        if games
                        else None
                    ),

                "first_kickoff":
                    (
                        first_kickoff.isoformat()
                        if first_kickoff
                        else None
                    ),

                "safety_deadline":
                    (
                        safety_deadline.isoformat()
                        if safety_deadline
                        else None
                    ),

                "real_deadline":
                    (
                        real_deadline.isoformat()
                        if real_deadline
                        else None
                    ),

                "next_round_unlock":
                    (
                        next_round_unlock.isoformat()
                        if next_round_unlock
                        else None
                    ),
            }
        )

    return matchdays


# ============================================================
# MERGE Y DETECCION DE CAMBIOS
# ============================================================


def merge_with_previous(
    previous_matches: list[dict],
    fresh_matches: list[dict],
) -> list[dict]:
    """
    El refresco puede devolver solo algunas jornadas.
    Conservamos jornadas/partidos conocidos que no hayan sido
    devueltos en este ciclo y reemplazamos por la versión fresca
    cuando existe la misma pareja de equipos/jornada.
    """

    merged = {
        match_key(
            match
        ):
            match

        for match in previous_matches
    }

    for match in fresh_matches:

        merged[
            match_key(
                match
            )
        ] = match

    return sorted(
        merged.values(),
        key=lambda item: (
            int(
                item[
                    "matchday"
                ]
            ),
            item[
                "kickoff"
            ],
        ),
    )


def detect_changes(
    previous_matches: list[dict],
    current_matches: list[dict],
    detected_at: datetime,
) -> list[dict]:

    previous_lookup = {
        match_key(
            match
        ):
            match

        for match in previous_matches
    }

    current_lookup = {
        match_key(
            match
        ):
            match

        for match in current_matches
    }

    changes = []

    for key, current in current_lookup.items():

        previous = (
            previous_lookup.get(
                key
            )
        )

        if previous is None:

            changes.append(
                {
                    "detected_at":
                        detected_at.isoformat(),

                    "type":
                        "MATCH_ADDED",

                    "matchday":
                        current[
                            "matchday"
                        ],

                    "home":
                        current[
                            "home"
                        ],

                    "away":
                        current[
                            "away"
                        ],

                    "new_kickoff":
                        current[
                            "kickoff"
                        ],
                }
            )

            continue

        if (
            previous.get(
                "kickoff"
            )
            !=
            current.get(
                "kickoff"
            )
        ):

            changes.append(
                {
                    "detected_at":
                        detected_at.isoformat(),

                    "type":
                        "KICKOFF_CHANGED",

                    "matchday":
                        current[
                            "matchday"
                        ],

                    "home":
                        current[
                            "home"
                        ],

                    "away":
                        current[
                            "away"
                        ],

                    "old_kickoff":
                        previous.get(
                            "kickoff"
                        ),

                    "new_kickoff":
                        current.get(
                            "kickoff"
                        ),
                }
            )

    return changes


# ============================================================
# FRECUENCIA DE REFRESCO
# ============================================================


def calculate_refresh_interval(
    seconds_to_deadline: int | None,
) -> int:
    """
    Devuelve segundos.
    """

    if seconds_to_deadline is None:

        return (
            6
            * 3600
        )

    if seconds_to_deadline <= (
        48
        * 3600
    ):

        return (
            30
            * 60
        )

    if seconds_to_deadline <= (
        7
        * 24
        * 3600
    ):

        return (
            2
            * 3600
        )

    return (
        6
        * 3600
    )


def cache_age_seconds(
    cache: dict | None,
    now: datetime,
) -> int | None:

    if not cache:
        return None

    fetched_at = (
        parse_datetime(
            cache.get(
                "fetched_at"
            )
        )
    )

    if fetched_at is None:
        return None

    return max(
        int(
            (
                now
                - fetched_at
            ).total_seconds()
        ),
        0,
    )


# ============================================================
# JORNADA OBJETIVO
# ============================================================


def determine_target_matchday(
    matchdays: list[dict],
    now: datetime,
) -> dict:
    """
    Reglas:

    - Antes del primer partido:
        target = jornada N.

    - Desde el primer kickoff hasta +2h:
        target operativo sigue marcado como N,
        pero ROUND_TRANSITION_LOCK bloquea cambios.

    - Pasadas +2h:
        el objetivo pasa a la siguiente jornada disponible.
    """

    for item in matchdays:

        first_kickoff = (
            parse_datetime(
                item.get(
                    "first_kickoff"
                )
            )
        )

        unlock = (
            parse_datetime(
                item.get(
                    "next_round_unlock"
                )
            )
        )

        if first_kickoff is None:
            continue

        if now < first_kickoff:

            return {
                "target":
                    item,

                "transition_from":
                    None,

                "round_transition_lock":
                    False,
            }

        if (
            unlock is not None
            and
            first_kickoff
            <= now
            < unlock
        ):

            return {
                "target":
                    item,

                "transition_from":
                    item[
                        "matchday"
                    ],

                "round_transition_lock":
                    True,
            }

    # Si ya pasaron todas las jornadas conocidas.
    return {
        "target":
            None,

        "transition_from":
            None,

        "round_transition_lock":
            False,
    }


def classify_phase(
    target: dict | None,
    now: datetime,
    transition_lock: bool,
) -> str:

    if target is None:
        return "SEASON_COMPLETE_OR_UNKNOWN"

    if transition_lock:
        return "ROUND_TRANSITION_LOCK"

    first_kickoff = (
        parse_datetime(
            target.get(
                "first_kickoff"
            )
        )
    )

    real_deadline = (
        parse_datetime(
            target.get(
                "real_deadline"
            )
        )
    )

    safety_deadline = (
        parse_datetime(
            target.get(
                "safety_deadline"
            )
        )
    )

    if (
        first_kickoff is None
        or
        real_deadline is None
        or
        safety_deadline is None
    ):

        return "CALENDAR_UNKNOWN"

    # T-15 hasta kickoff: ya consideramos cerrada la jornada.
    if (
        real_deadline
        <= now
        < first_kickoff
    ):

        return "ROUND_LOCKED"

    seconds = int(
        (
            real_deadline
            - now
        ).total_seconds()
    )

    if seconds <= 0:
        return "ROUND_LOCKED"

    hours = (
        seconds
        / 3600
    )

    if now >= safety_deadline:
        return "HARD_SAFETY"

    if hours <= 2:
        return "FINALIZATION"

    if hours <= 12:
        return "HIGH_ATTENTION"

    if hours <= 48:
        return "PREPARATION"

    return "NORMAL"


# ============================================================
# REFRESCO
# ============================================================


def refresh_dynamic_calendar(
    force: bool = False,
    now: datetime | None = None,
) -> dict:

    if now is None:

        now = (
            now_madrid()
        )

    else:

        now = (
            now.astimezone(
                MADRID_TZ
            )
        )

    cache = (
        load_calendar_cache()
    )

    cached_matchdays = (
        cache.get(
            "matchdays",
            [],
        )
        if cache
        else []
    )

    cached_target_state = (
        determine_target_matchday(
            cached_matchdays,
            now,
        )
        if cached_matchdays
        else {
            "target":
                None,
            "transition_from":
                None,
            "round_transition_lock":
                False,
        }
    )

    cached_target = (
        cached_target_state.get(
            "target"
        )
    )

    cached_deadline = (
        parse_datetime(
            cached_target.get(
                "real_deadline"
            )
        )
        if cached_target
        else None
    )

    seconds_to_cached_deadline = (
        seconds_between(
            now,
            cached_deadline,
        )
    )

    refresh_interval = (
        calculate_refresh_interval(
            seconds_to_cached_deadline
        )
    )

    age = (
        cache_age_seconds(
            cache,
            now,
        )
    )

    should_refresh = bool(
        force
        or
        cache is None
        or
        age is None
        or
        age >= refresh_interval
    )

    refresh_error = None
    changes = []

    if should_refresh:

        try:

            result = (
                fetch_dynamic_calendar(
                    season_start_year=
                        SEASON_START_YEAR
                )
            )

            fresh_matches = (
                result[
                    "matches"
                ]
            )

            previous_matches = (
                cache.get(
                    "matches",
                    [],
                )
                if cache
                else []
            )

            merged_matches = (
                merge_with_previous(
                    previous_matches=
                        previous_matches,

                    fresh_matches=
                        fresh_matches,
                )
            )

            changes = (
                detect_changes(
                    previous_matches=
                        previous_matches,

                    current_matches=
                        merged_matches,

                    detected_at=
                        now,
                )
            )

            data = {
                "season":
                    (
                        f"{SEASON_START_YEAR}/"
                        f"{str(SEASON_START_YEAR + 1)[-2:]}"
                    ),

                "source":
                    result[
                        "source"
                    ],

                "source_errors":
                    result.get(
                        "errors",
                        [],
                    ),

                "fetched_at":
                    now.isoformat(),

                "matches":
                    merged_matches,

                "matchdays":
                    build_matchdays(
                        merged_matches
                    ),
            }

            save_calendar_cache(
                data
            )

            append_calendar_changes(
                changes
            )

            cache = data

        except Exception as error:

            refresh_error = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            if cache is None:

                raise

    if cache is None:

        raise RuntimeError(
            "No existe calendario dinamico ni cache valida."
        )

    target_state = (
        determine_target_matchday(
            cache.get(
                "matchdays",
                [],
            ),
            now,
        )
    )

    target = (
        target_state[
            "target"
        ]
    )

    phase = (
        classify_phase(
            target=
                target,

            now=
                now,

            transition_lock=
                target_state[
                    "round_transition_lock"
                ],
        )
    )

    real_deadline = (
        parse_datetime(
            target.get(
                "real_deadline"
            )
        )
        if target
        else None
    )

    first_kickoff = (
        parse_datetime(
            target.get(
                "first_kickoff"
            )
        )
        if target
        else None
    )

    unlock = (
        parse_datetime(
            target.get(
                "next_round_unlock"
            )
        )
        if target
        else None
    )

    next_matchday = None

    if target is not None:

        current_number = int(
            target[
                "matchday"
            ]
        )

        for item in cache.get(
            "matchdays",
            [],
        ):

            if int(
                item[
                    "matchday"
                ]
            ) > current_number:

                next_matchday = (
                    item[
                        "matchday"
                    ]
                )

                break

    return {
        "available":
            target is not None,

        "source":
            cache.get(
                "source"
            ),

        "calendar_fetched_at":
            cache.get(
                "fetched_at"
            ),

        "refresh_performed":
            should_refresh,

        "refresh_error":
            refresh_error,

        "changes_detected":
            changes,

        "target_matchday":
            (
                target.get(
                    "matchday"
                )
                if target
                else None
            ),

        "next_matchday":
            next_matchday,

        "first_match":
            (
                target.get(
                    "first_match"
                )
                if target
                else None
            ),

        "first_kickoff":
            (
                first_kickoff.isoformat()
                if first_kickoff
                else None
            ),

        "safety_deadline":
            (
                target.get(
                    "safety_deadline"
                )
                if target
                else None
            ),

        "real_deadline":
            (
                real_deadline.isoformat()
                if real_deadline
                else None
            ),

        "next_round_unlock":
            (
                unlock.isoformat()
                if unlock
                else None
            ),

        "seconds_to_deadline":
            seconds_between(
                now,
                real_deadline,
            ),

        "seconds_to_first_kickoff":
            seconds_between(
                now,
                first_kickoff,
            ),

        "seconds_to_unlock":
            seconds_between(
                now,
                unlock,
            ),

        "phase":
            phase,

        "round_transition_lock":
            target_state[
                "round_transition_lock"
            ],

        "target":
            target,
    }
