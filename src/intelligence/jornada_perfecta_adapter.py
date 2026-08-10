from __future__ import annotations

import json
import unicodedata

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


# ============================================================
# CONFIGURACION
# ============================================================


DATA_DIRECTORY = (
    Path("data")
    / "intelligence"
)

DATA_FILE = (
    DATA_DIRECTORY
    / "jornada_perfecta_lineups.json"
)


# ============================================================
# ESTADOS NORMALIZADOS
# ============================================================


STATUS_UNKNOWN = "UNKNOWN"
STATUS_STARTER = "TITULAR"
STATUS_PROBABLE = "PROBABLE"
STATUS_DOUBT = "DUDA"
STATUS_BENCH = "SUPLENTE"
STATUS_OUT = "NO_CONVOCADO"


VALID_STATUSES = {
    STATUS_UNKNOWN,
    STATUS_STARTER,
    STATUS_PROBABLE,
    STATUS_DOUBT,
    STATUS_BENCH,
    STATUS_OUT,
}


STATUS_ALIASES = {
    # TITULAR
    "titular":
        STATUS_STARTER,

    "starter":
        STATUS_STARTER,

    "titular probable":
        STATUS_STARTER,

    "probable titular":
        STATUS_STARTER,

    "fijo":
        STATUS_STARTER,

    # PROBABLE
    "probable":
        STATUS_PROBABLE,

    "posible titular":
        STATUS_PROBABLE,

    "likely":
        STATUS_PROBABLE,

    # DUDA
    "duda":
        STATUS_DOUBT,

    "doubt":
        STATUS_DOUBT,

    "dudoso":
        STATUS_DOUBT,

    "doubtful":
        STATUS_DOUBT,

    # SUPLENTE
    "suplente":
        STATUS_BENCH,

    "bench":
        STATUS_BENCH,

    "suplente probable":
        STATUS_BENCH,

    # NO CONVOCADO
    "no convocado":
        STATUS_OUT,

    "fuera":
        STATUS_OUT,

    "out":
        STATUS_OUT,

    "descartado":
        STATUS_OUT,

    # UNKNOWN
    "unknown":
        STATUS_UNKNOWN,

    "desconocido":
        STATUS_UNKNOWN,
}


# ============================================================
# CACHE
# ============================================================


_CACHE = {
    "mtime":
        None,

    "data":
        None,
}


def clear_jornada_perfecta_cache() -> None:

    _CACHE[
        "mtime"
    ] = None

    _CACHE[
        "data"
    ] = None


# ============================================================
# UTILIDADES
# ============================================================


def normalize_text(
    value: str | None,
) -> str:

    if value is None:
        return ""

    value = str(
        value
    ).strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character

        for character in value

        if not unicodedata.combining(
            character
        )
    )

    value = " ".join(
        value.split()
    )

    return value


def normalize_status(
    value: str | None,
) -> str:

    if not value:
        return STATUS_UNKNOWN

    normalized = (
        normalize_text(
            value
        )
    )

    if normalized in STATUS_ALIASES:

        return (
            STATUS_ALIASES[
                normalized
            ]
        )

    upper = (
        str(
            value
        )
        .strip()
        .upper()
    )

    if upper in VALID_STATUSES:

        return upper

    return STATUS_UNKNOWN


def parse_iso_datetime(
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

        if parsed.tzinfo is None:

            parsed = (
                parsed.replace(
                    tzinfo=timezone.utc
                )
            )

        return parsed

    except (
        ValueError,
        TypeError,
    ):

        return None


def calculate_age_hours(
    updated_at: str | None,
) -> float | None:

    parsed = (
        parse_iso_datetime(
            updated_at
        )
    )

    if parsed is None:
        return None

    now = (
        datetime.now(
            timezone.utc
        )
    )

    seconds = (
        now
        - parsed
    ).total_seconds()

    return max(
        seconds / 3600,
        0.0,
    )


# ============================================================
# ESTADOS DE ERROR
# ============================================================


def build_unavailable_state(
    status: str,
    error: str | None = None,
) -> dict:

    return {
        "available":
            False,

        "source":
            "JORNADA_PERFECTA",

        "status":
            status,

        "error":
            error,

        "file":
            str(
                DATA_FILE
            ),

        "updated_at":
            None,

        "age_hours":
            None,

        "round":
            None,

        "players":
            [],
    }


# ============================================================
# ARCHIVO
# ============================================================


def ensure_data_directory() -> None:

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_jornada_perfecta_data() -> dict:
    """
    Lee el datasource normalizado.

    NO realiza scraping ni peticiones HTTP.

    utf-8-sig permite leer tanto UTF-8 normal
    como UTF-8 con BOM, algo habitual en PowerShell.
    """

    if not DATA_FILE.exists():

        return (
            build_unavailable_state(
                "NO_DATA_FILE"
            )
        )

    try:

        mtime = (
            DATA_FILE
            .stat()
            .st_mtime
        )

    except OSError as error:

        return (
            build_unavailable_state(
                "FILE_ERROR",
                str(
                    error
                ),
            )
        )

    if (
        _CACHE[
            "mtime"
        ]
        == mtime

        and
        _CACHE[
            "data"
        ]
        is not None
    ):

        return (
            _CACHE[
                "data"
            ]
        )

    try:

        # IMPORTANTE:
        # utf-8-sig soporta también archivos
        # creados desde Windows PowerShell con BOM.
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:

            raw = (
                json.load(
                    file
                )
            )

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:

        result = (
            build_unavailable_state(
                "INVALID_FILE",
                str(
                    error
                ),
            )
        )

        _CACHE[
            "mtime"
        ] = mtime

        _CACHE[
            "data"
        ] = result

        return result

    if not isinstance(
        raw,
        dict,
    ):

        result = (
            build_unavailable_state(
                "INVALID_ROOT",
                (
                    "El JSON debe contener "
                    "un objeto en la raíz."
                ),
            )
        )

        _CACHE[
            "mtime"
        ] = mtime

        _CACHE[
            "data"
        ] = result

        return result

    players_raw = (
        raw.get(
            "players",
            []
        )
    )

    if not isinstance(
        players_raw,
        list,
    ):

        result = (
            build_unavailable_state(
                "INVALID_PLAYERS",
                (
                    "'players' debe ser "
                    "una lista."
                ),
            )
        )

        _CACHE[
            "mtime"
        ] = mtime

        _CACHE[
            "data"
        ] = result

        return result

    players = []

    for item in players_raw:

        if not isinstance(
            item,
            dict,
        ):

            continue

        confidence = int(
            item.get(
                "confidence",
                0,
            )
            or 0
        )

        confidence = max(
            0,
            min(
                confidence,
                100,
            ),
        )

        player_id = (
            item.get(
                "biwenger_id"
            )
        )

        if player_id is not None:

            try:

                player_id = int(
                    player_id
                )

            except (
                ValueError,
                TypeError,
            ):

                player_id = None

        name = (
            item.get(
                "name"
            )
        )

        players.append(
            {
                "biwenger_id":
                    player_id,

                "name":
                    name,

                "normalized_name":
                    normalize_text(
                        name
                    ),

                "status":
                    normalize_status(
                        item.get(
                            "status"
                        )
                    ),

                "confidence":
                    confidence,

                "note":
                    item.get(
                        "note"
                    ),

                "team":
                    item.get(
                        "team"
                    ),

                "source":
                    item.get(
                        "source",
                        raw.get(
                            "source",
                            "JORNADA_PERFECTA",
                        ),
                    ),
            }
        )

    updated_at = (
        raw.get(
            "updated_at"
        )
    )

    result = {
        "available":
            True,

        "source":
            raw.get(
                "source",
                "JORNADA_PERFECTA",
            ),

        "status":
            "OK",

        "error":
            None,

        "file":
            str(
                DATA_FILE
            ),

        "updated_at":
            updated_at,

        "age_hours":
            calculate_age_hours(
                updated_at
            ),

        "round":
            raw.get(
                "round"
            ),

        "players":
            players,
    }

    _CACHE[
        "mtime"
    ] = mtime

    _CACHE[
        "data"
    ] = result

    return result


# ============================================================
# LOOKUPS
# ============================================================


def build_jornada_perfecta_lookup() -> dict:

    data = (
        load_jornada_perfecta_data()
    )

    by_id = {}

    by_name = {}

    for player in data.get(
        "players",
        [],
    ):

        player_id = (
            player.get(
                "biwenger_id"
            )
        )

        if player_id is not None:

            by_id[
                int(
                    player_id
                )
            ] = player

        normalized_name = (
            player.get(
                "normalized_name"
            )
        )

        if normalized_name:

            by_name[
                normalized_name
            ] = player

    return {
        "data":
            data,

        "by_id":
            by_id,

        "by_name":
            by_name,
    }


# ============================================================
# RESOLVER JUGADOR
# ============================================================


def get_jornada_perfecta_player_signal(
    player: dict,
    lookup: dict | None = None,
) -> dict:

    if lookup is None:

        lookup = (
            build_jornada_perfecta_lookup()
        )

    data = (
        lookup[
            "data"
        ]
    )

    if not data.get(
        "available",
        False,
    ):

        return {
            "available":
                False,

            "matched":
                False,

            "match_method":
                None,

            "status":
                STATUS_UNKNOWN,

            "confidence":
                0,

            "source":
                "JORNADA_PERFECTA",

            "note":
                None,

            "updated_at":
                data.get(
                    "updated_at"
                ),

            "age_hours":
                data.get(
                    "age_hours"
                ),
        }

    player_id = (
        player.get(
            "id"
        )
    )

    if player_id is not None:

        signal = (
            lookup[
                "by_id"
            ].get(
                int(
                    player_id
                )
            )
        )

        if signal is not None:

            return {
                "available":
                    True,

                "matched":
                    True,

                "match_method":
                    "BIWENGER_ID",

                **signal,

                "updated_at":
                    data.get(
                        "updated_at"
                    ),

                "age_hours":
                    data.get(
                        "age_hours"
                    ),
            }

    normalized_name = (
        normalize_text(
            player.get(
                "name"
            )
        )
    )

    signal = (
        lookup[
            "by_name"
        ].get(
            normalized_name
        )
    )

    if signal is not None:

        return {
            "available":
                True,

            "matched":
                True,

            "match_method":
                "NORMALIZED_NAME",

            **signal,

            "updated_at":
                data.get(
                    "updated_at"
                ),

            "age_hours":
                data.get(
                    "age_hours"
                ),
        }

    return {
        "available":
            True,

        "matched":
            False,

        "match_method":
            None,

        "status":
            STATUS_UNKNOWN,

        "confidence":
            0,

        "source":
            data.get(
                "source",
                "JORNADA_PERFECTA",
            ),

        "note":
            None,

        "updated_at":
            data.get(
                "updated_at"
            ),

        "age_hours":
            data.get(
                "age_hours"
            ),
    }