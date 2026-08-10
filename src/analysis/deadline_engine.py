from __future__ import annotations

from src.analysis.calendar_state import (
    build_calendar_state,
)

from src.analysis.lineup_engine import (
    build_lineup,
)


def classify_time_risk(
    seconds_remaining: int | None,
) -> str:

    if seconds_remaining is None:
        return "DESCONOCIDO"

    if seconds_remaining <= 0:
        return "BLOQUEADO"

    hours = (
        seconds_remaining
        / 3600
    )

    if hours <= 6:
        return "CRITICO"

    if hours <= 24:
        return "MUY_ALTO"

    if hours <= 48:
        return "ALTO"

    if hours <= 120:
        return "MODERADO"

    return "BAJO"


def classify_lineup_risk(
    playable_count: int,
    seconds_remaining: int | None,
) -> str:

    missing = max(
        11
        - playable_count,
        0,
    )

    if missing == 0:
        return "BAJO"

    if seconds_remaining is None:
        return "DESCONOCIDO"

    if seconds_remaining <= 0:
        return "CRITICO"

    hours = (
        seconds_remaining
        / 3600
    )

    # ----------------------------------------------
    # QUEDAN MUCHOS DÍAS
    # ----------------------------------------------

    if hours > 120:

        if missing <= 3:
            return "BAJO"

        return "MODERADO"

    # ----------------------------------------------
    # 2-5 DÍAS
    # ----------------------------------------------

    if hours > 48:

        if missing == 1:
            return "BAJO"

        if missing <= 3:
            return "MODERADO"

        return "ALTO"

    # ----------------------------------------------
    # 24-48H
    # ----------------------------------------------

    if hours > 24:

        if missing == 1:
            return "MODERADO"

        if missing <= 3:
            return "ALTO"

        return "MUY_ALTO"

    # ----------------------------------------------
    # MENOS DE 24H
    # ----------------------------------------------

    if missing >= 1:
        return "CRITICO"

    return "BAJO"


def calculate_lineup_pressure_score(
    playable_count: int,
    seconds_remaining: int | None,
) -> int:

    missing = max(
        11
        - playable_count,
        0,
    )

    if missing == 0:
        return 0

    if seconds_remaining is None:
        return min(
            missing * 15,
            100,
        )

    hours = max(
        seconds_remaining
        / 3600,
        0,
    )

    # Factor tiempo:
    # cuanto más cerca, más pesa cada hueco.
    if hours <= 6:
        time_factor = 30

    elif hours <= 24:
        time_factor = 25

    elif hours <= 48:
        time_factor = 18

    elif hours <= 120:
        time_factor = 10

    else:
        time_factor = 5

    return min(
        missing
        * time_factor,
        100,
    )


def calculate_premium_freedom_bonus(
    playable_count: int,
    seconds_remaining: int | None,
) -> int:
    """
    Cuanto más tiempo queda, más libertad permitimos
    para estrategias premium aunque el XI no esté cerrado.
    """

    if seconds_remaining is None:
        return 0

    hours = (
        seconds_remaining
        / 3600
    )

    missing = max(
        11
        - playable_count,
        0,
    )

    if missing == 0:

        if hours > 48:
            return 12

        return 5

    if hours > 168:
        return 15

    if hours > 120:
        return 12

    if hours > 72:
        return 8

    if hours > 48:
        return 4

    return 0


def calculate_expected_future_market_opportunities(
    calendar: dict,
) -> dict:

    cycles = calendar.get(
        "estimated_market_cycles"
    )

    if cycles is None:

        return {
            "cycles":
                None,

            "level":
                "DESCONOCIDO",
        }

    if cycles >= 5:
        level = "MUCHAS"

    elif cycles >= 3:
        level = "VARIAS"

    elif cycles >= 1:
        level = "POCAS"

    else:
        level = "NINGUNA"

    return {
        "cycles":
            cycles,

        "level":
            level,
    }


def build_deadline_state(
    snapshot: dict,
    now_ts: int | None = None,
) -> dict:

    calendar = (
        build_calendar_state(
            snapshot,
            now_ts,
        )
    )

    lineup = build_lineup(
        snapshot
    )

    playable_count = int(
        lineup[
            "playable_count"
        ]
    )

    missing = max(
        11
        - playable_count,
        0,
    )

    seconds_remaining = (
        calendar[
            "seconds_to_lineup_lock"
        ]
    )

    time_risk = (
        classify_time_risk(
            seconds_remaining
        )
    )

    lineup_risk = (
        classify_lineup_risk(
            playable_count,
            seconds_remaining,
        )
    )

    pressure = (
        calculate_lineup_pressure_score(
            playable_count,
            seconds_remaining,
        )
    )

    premium_freedom = (
        calculate_premium_freedom_bonus(
            playable_count,
            seconds_remaining,
        )
    )

    future_markets = (
        calculate_expected_future_market_opportunities(
            calendar
        )
    )

    hard_safety_mode = (
        time_risk
        in {
            "CRITICO",
            "BLOQUEADO",
        }
    )

    return {
        "calendar":
            calendar,

        "playable_count":
            playable_count,

        "missing_playable":
            missing,

        "time_risk":
            time_risk,

        "lineup_risk":
            lineup_risk,

        "lineup_pressure_score":
            pressure,

        "premium_freedom_bonus":
            premium_freedom,

        "future_market_opportunities":
            future_markets,

        "hard_safety_mode":
            hard_safety_mode,
    }