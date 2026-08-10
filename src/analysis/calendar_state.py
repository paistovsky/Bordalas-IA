from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


LINEUP_LOCK_MINUTES = 15


# ======================================================
# TIEMPO
# ======================================================


def unix_now() -> int:

    return int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )


def normalize_timestamp(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:
        value = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if value <= 0:
        return None

    return value


def seconds_to_text(
    seconds: int | None,
) -> str:

    if seconds is None:
        return "DESCONOCIDO"

    if seconds <= 0:
        return "CERRADO / INICIADO"

    days, remainder = divmod(
        seconds,
        86_400,
    )

    hours, remainder = divmod(
        remainder,
        3_600,
    )

    minutes, _ = divmod(
        remainder,
        60,
    )

    parts = []

    if days:
        parts.append(
            f"{days}d"
        )

    if hours or days:
        parts.append(
            f"{hours}h"
        )

    parts.append(
        f"{minutes}m"
    )

    return " ".join(
        parts
    )


# ======================================================
# EQUIPOS / FIXTURES
# ======================================================


def get_teams(
    snapshot: dict,
) -> list[dict]:

    teams = (
        snapshot
        .get(
            "catalog",
            {}
        )
        .get(
            "data",
            {}
        )
        .get(
            "teams",
            {}
        )
    )

    if isinstance(
        teams,
        dict,
    ):
        return list(
            teams.values()
        )

    if isinstance(
        teams,
        list,
    ):
        return teams

    return []


def iter_team_games(
    snapshot: dict,
):
    """
    Recorre todos los nextGames del catálogo.

    Un mismo partido aparece normalmente
    en ambos equipos, por lo que eliminamos
    duplicados usando su ID.
    """

    seen_game_ids = set()

    for team in get_teams(
        snapshot
    ):

        for game in team.get(
            "nextGames",
            [],
        ):

            game_id = (
                game.get(
                    "id"
                )
            )

            if (
                game_id is not None
                and
                game_id
                in seen_game_ids
            ):
                continue

            if game_id is not None:
                seen_game_ids.add(
                    game_id
                )

            yield game


def get_future_games(
    snapshot: dict,
    now_ts: int | None = None,
) -> list[dict]:

    if now_ts is None:
        now_ts = unix_now()

    games = []

    for game in iter_team_games(
        snapshot
    ):

        date = normalize_timestamp(
            game.get(
                "date"
            )
        )

        if date is None:
            continue

        # Dejamos un pequeño margen para que
        # un partido recién comenzado no cambie
        # instantáneamente la jornada detectada.
        if date < (
            now_ts
            - 3_600
        ):
            continue

        games.append(
            game
        )

    games.sort(
        key=lambda game:
            normalize_timestamp(
                game.get(
                    "date"
                )
            )
            or 9_999_999_999
    )

    return games


# ======================================================
# JORNADA ACTUAL
# ======================================================


def infer_current_round_from_fixtures(
    snapshot: dict,
    now_ts: int | None = None,
) -> int | None:
    """
    Método principal.

    Detectamos la jornada del primer partido
    futuro que aparece en nextGames.

    Esto evita depender de dónde haya decidido
    Biwenger colocar currentRound en su JSON.
    """

    games = get_future_games(
        snapshot,
        now_ts,
    )

    if not games:
        return None

    earliest_date = normalize_timestamp(
        games[0].get(
            "date"
        )
    )

    if earliest_date is None:
        return None

    # Un mismo round puede tener partidos separados
    # por varios días. Tomamos el round correspondiente
    # al primer partido futuro.
    round_data = (
        games[0].get(
            "round",
            {}
        )
    )

    round_id = (
        round_data.get(
            "id"
        )
    )

    if round_id is None:
        return None

    try:
        return int(
            round_id
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def get_current_round_id(
    snapshot: dict,
    now_ts: int | None = None,
) -> int | None:

    # ==================================================
    # 1. CAMPOS DIRECTOS
    # ==================================================

    possible_paths = [
        snapshot.get(
            "round"
        ),
        snapshot.get(
            "currentRound"
        ),
        snapshot.get(
            "current_round"
        ),
    ]

    for value in possible_paths:

        if isinstance(
            value,
            dict,
        ):
            value = value.get(
                "id"
            )

        if value is None:
            continue

        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            pass

    for key in (
        "round_id",
        "current_round_id",
    ):

        value = snapshot.get(
            key
        )

        if value is None:
            continue

        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            pass

    # ==================================================
    # 2. INFERENCIA POR FIXTURES
    # ==================================================

    inferred = (
        infer_current_round_from_fixtures(
            snapshot,
            now_ts,
        )
    )

    if inferred is not None:
        return inferred

    return None


# ======================================================
# PARTIDOS DE UNA JORNADA
# ======================================================


def get_round_games(
    snapshot: dict,
    round_id: int | None,
) -> list[dict]:

    if round_id is None:
        return []

    result = []

    for game in iter_team_games(
        snapshot
    ):

        game_round = (
            game.get(
                "round",
                {}
            )
        )

        try:
            game_round_id = int(
                game_round.get(
                    "id"
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        if (
            game_round_id
            != round_id
        ):
            continue

        result.append(
            game
        )

    result.sort(
        key=lambda game:
            normalize_timestamp(
                game.get(
                    "date"
                )
            )
            or 9_999_999_999
    )

    return result


def get_first_round_game_timestamp(
    snapshot: dict,
    round_id: int | None = None,
    now_ts: int | None = None,
) -> int | None:

    if round_id is None:

        round_id = (
            get_current_round_id(
                snapshot,
                now_ts,
            )
        )

    games = get_round_games(
        snapshot,
        round_id,
    )

    timestamps = []

    for game in games:

        timestamp = (
            normalize_timestamp(
                game.get(
                    "date"
                )
            )
        )

        if timestamp is not None:
            timestamps.append(
                timestamp
            )

    if not timestamps:
        return None

    return min(
        timestamps
    )


def get_lineup_deadline_timestamp(
    snapshot: dict,
    round_id: int | None = None,
    lock_minutes: int = LINEUP_LOCK_MINUTES,
    now_ts: int | None = None,
) -> int | None:

    first_game = (
        get_first_round_game_timestamp(
            snapshot,
            round_id,
            now_ts,
        )
    )

    if first_game is None:
        return None

    return (
        first_game
        - (
            lock_minutes
            * 60
        )
    )


# ======================================================
# MERCADO
# ======================================================


def get_market_sales(
    snapshot: dict,
) -> list[dict]:

    return (
        snapshot
        .get(
            "market",
            {}
        )
        .get(
            "sales",
            [],
        )
    )


def get_market_deadlines(
    snapshot: dict,
    now_ts: int | None = None,
) -> list[dict]:

    if now_ts is None:
        now_ts = unix_now()

    catalog = (
        snapshot
        .get(
            "catalog",
            {}
        )
        .get(
            "data",
            {}
        )
        .get(
            "players",
            {}
        )
    )

    deadlines = []

    for sale in get_market_sales(
        snapshot
    ):

        player_id = (
            sale
            .get(
                "player",
                {}
            )
            .get(
                "id"
            )
        )

        until = normalize_timestamp(
            sale.get(
                "until"
            )
        )

        if until is None:
            continue

        player = None

        if (
            player_id is not None
            and
            isinstance(
                catalog,
                dict,
            )
        ):

            player = (
                catalog.get(
                    str(
                        player_id
                    )
                )
                or
                catalog.get(
                    player_id
                )
            )

        deadlines.append(
            {
                "player_id":
                    player_id,

                "player_name":
                    (
                        player.get(
                            "name"
                        )
                        if player
                        else str(
                            player_id
                        )
                    ),

                "until":
                    until,

                "seconds_remaining":
                    until
                    - now_ts,

                "time_remaining":
                    seconds_to_text(
                        until
                        - now_ts
                    ),

                "price":
                    int(
                        sale.get(
                            "price",
                            0,
                        )
                        or 0
                    ),

                "seller":
                    sale.get(
                        "user"
                    ),
            }
        )

    deadlines.sort(
        key=lambda item:
            item[
                "until"
            ]
    )

    return deadlines


# ======================================================
# CICLOS DE MERCADO
# ======================================================


def estimate_market_cycles_before_deadline(
    snapshot: dict,
    now_ts: int | None = None,
) -> int | None:
    """
    Estimación conservadora.

    Aproximamos un mercado nuevo por día.
    NO significa que vaya a aparecer un jugador
    útil en cada ciclo.
    """

    if now_ts is None:
        now_ts = unix_now()

    lineup_deadline = (
        get_lineup_deadline_timestamp(
            snapshot,
            now_ts=now_ts,
        )
    )

    if lineup_deadline is None:
        return None

    seconds_remaining = (
        lineup_deadline
        - now_ts
    )

    if seconds_remaining <= 0:
        return 0

    return max(
        int(
            seconds_remaining
            // 86_400
        ),
        0,
    )


# ======================================================
# DETECTOR DE JORNADAS ESPECIALES
# ======================================================


def find_round_lists(
    value: Any,
    results: list[list],
) -> None:
    """
    Busca recursivamente estructuras con
    listas de rounds.

    Biwenger puede mover estos datos dentro
    del snapshot sin que queramos depender
    de una ruta concreta.
    """

    if isinstance(
        value,
        dict,
    ):

        rounds = value.get(
            "rounds"
        )

        if (
            isinstance(
                rounds,
                list,
            )
            and rounds
        ):
            results.append(
                rounds
            )

        for child in value.values():
            find_round_lists(
                child,
                results,
            )

    elif isinstance(
        value,
        list,
    ):

        for child in value:
            find_round_lists(
                child,
                results,
            )


def detect_round_anomalies(
    snapshot: dict,
) -> list[dict]:

    round_lists = []

    find_round_lists(
        snapshot,
        round_lists,
    )

    anomalies = []
    seen = set()

    for rounds in round_lists:

        for round_item in rounds:

            if not isinstance(
                round_item,
                dict,
            ):
                continue

            name = str(
                round_item.get(
                    "name",
                    ""
                )
            ).lower()

            is_split = (
                round_item.get(
                    "part"
                )
                is not None
            )

            postponed_word = (
                "aplazada" in name
                or
                "aplazado" in name
            )

            if not (
                is_split
                or
                postponed_word
            ):
                continue

            identity = (
                round_item.get(
                    "id"
                ),
                round_item.get(
                    "name"
                ),
            )

            if identity in seen:
                continue

            seen.add(
                identity
            )

            anomalies.append(
                {
                    "id":
                        round_item.get(
                            "id"
                        ),

                    "name":
                        round_item.get(
                            "name"
                        ),

                    "part":
                        round_item.get(
                            "part"
                        ),

                    "status":
                        round_item.get(
                            "status"
                        ),

                    "type":
                        "POSTPONED_OR_SPLIT",
                }
            )

    return anomalies


# ======================================================
# ESTADO COMPLETO
# ======================================================


def build_calendar_state(
    snapshot: dict,
    now_ts: int | None = None,
) -> dict:

    if now_ts is None:
        now_ts = unix_now()

    round_id = (
        get_current_round_id(
            snapshot,
            now_ts,
        )
    )

    games = get_round_games(
        snapshot,
        round_id,
    )

    first_game = (
        get_first_round_game_timestamp(
            snapshot,
            round_id,
            now_ts,
        )
    )

    lineup_deadline = (
        get_lineup_deadline_timestamp(
            snapshot,
            round_id,
            now_ts=now_ts,
        )
    )

    seconds_to_first_game = (
        (
            first_game
            - now_ts
        )
        if first_game is not None
        else None
    )

    seconds_to_lineup_lock = (
        (
            lineup_deadline
            - now_ts
        )
        if lineup_deadline
        is not None
        else None
    )

    market_deadlines = (
        get_market_deadlines(
            snapshot,
            now_ts,
        )
    )

    next_market_close = (
        market_deadlines[0]
        if market_deadlines
        else None
    )

    return {
        "now":
            now_ts,

        "current_round_id":
            round_id,

        "round_games":
            games,

        "round_game_count":
            len(
                games
            ),

        "first_game":
            first_game,

        "lineup_deadline":
            lineup_deadline,

        "seconds_to_first_game":
            seconds_to_first_game,

        "seconds_to_lineup_lock":
            seconds_to_lineup_lock,

        "time_to_first_game":
            seconds_to_text(
                seconds_to_first_game
            ),

        "time_to_lineup_lock":
            seconds_to_text(
                seconds_to_lineup_lock
            ),

        "market_deadlines":
            market_deadlines,

        "next_market_close":
            next_market_close,

        "estimated_market_cycles":
            estimate_market_cycles_before_deadline(
                snapshot,
                now_ts,
            ),

        "round_anomalies":
            detect_round_anomalies(
                snapshot
            ),
    }