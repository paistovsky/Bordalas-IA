from __future__ import annotations

from src.analysis.calendar_state import (
    build_calendar_state,
)

from src.analysis.lineup_engine import (
    build_lineup,
)


# ============================================================
# TIEMPO
# ============================================================


def classify_time_risk(
    seconds_remaining: int | None,
    phase: str | None = None,
) -> str:

    if phase in {
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return "BLOQUEADO"

    if phase == "HARD_SAFETY":

        return "CRITICO"

    if seconds_remaining is None:

        return "DESCONOCIDO"

    if seconds_remaining <= 0:

        return "BLOQUEADO"

    hours = (
        seconds_remaining
        / 3600
    )

    if hours <= 2:
        return "CRITICO"

    if hours <= 12:
        return "MUY_ALTO"

    if hours <= 48:
        return "ALTO"

    if hours <= 120:
        return "MODERADO"

    return "BAJO"


# ============================================================
# RIESGO DEL XI
# ============================================================


def classify_lineup_risk(
    playable_count: int,
    seconds_remaining: int | None,
    phase: str | None = None,
) -> str:

    missing = max(
        11
        - playable_count,
        0,
    )

    if missing == 0:

        if phase in {
            "ROUND_LOCKED",
            "ROUND_TRANSITION_LOCK",
        }:

            return "BLOQUEADO"

        return "BAJO"

    if phase in {
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return "CRITICO"

    if seconds_remaining is None:

        return "DESCONOCIDO"

    if seconds_remaining <= 0:

        return "CRITICO"

    hours = (
        seconds_remaining
        / 3600
    )

    # --------------------------------------------------------
    # MAS DE 5 DIAS
    # --------------------------------------------------------

    if hours > 120:

        if missing <= 3:
            return "BAJO"

        return "MODERADO"

    # --------------------------------------------------------
    # 2-5 DIAS
    # --------------------------------------------------------

    if hours > 48:

        if missing == 1:
            return "BAJO"

        if missing <= 3:
            return "MODERADO"

        return "ALTO"

    # --------------------------------------------------------
    # 12-48H
    # --------------------------------------------------------

    if hours > 12:

        if missing == 1:
            return "MODERADO"

        if missing <= 3:
            return "ALTO"

        return "MUY_ALTO"

    # --------------------------------------------------------
    # MENOS DE 12H
    # --------------------------------------------------------

    return "CRITICO"


# ============================================================
# PRESION DEL XI
# ============================================================


def calculate_lineup_pressure_score(
    playable_count: int,
    seconds_remaining: int | None,
    phase: str | None = None,
) -> int:

    missing = max(
        11
        - playable_count,
        0,
    )

    if missing == 0:
        return 0

    if phase in {
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return 100

    if phase == "HARD_SAFETY":

        return min(
            80
            + missing * 10,
            100,
        )

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

    if hours <= 2:

        time_factor = 35

    elif hours <= 12:

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


# ============================================================
# LIBERTAD PREMIUM
# ============================================================


def calculate_premium_freedom_bonus(
    playable_count: int,
    seconds_remaining: int | None,
    phase: str | None = None,
) -> int:
    """
    Cuanto mas lejos estamos del deadline real,
    mayor libertad para Franchise/premium.

    Durante HARD_SAFETY o locks:
        libertad = 0.
    """

    if phase in {
        "HARD_SAFETY",
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return 0

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


# ============================================================
# OPORTUNIDADES FUTURAS
# ============================================================


def calculate_expected_future_market_opportunities(
    calendar: dict,
) -> dict:

    cycles = (
        calendar.get(
            "estimated_market_cycles"
        )
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


# ============================================================
# DEADLINE STATE
# ============================================================


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

    lineup = (
        build_lineup(
            snapshot
        )
    )

    playable_count = int(
        lineup.get(
            "playable_count",
            0,
        )
        or 0
    )

    missing = max(
        11
        - playable_count,
        0,
    )

    seconds_remaining = (
        calendar.get(
            "seconds_to_lineup_lock"
        )
    )

    phase = (
        calendar.get(
            "phase",
            "CALENDAR_UNKNOWN",
        )
    )

    time_risk = (
        classify_time_risk(
            seconds_remaining,
            phase=phase,
        )
    )

    lineup_risk = (
        classify_lineup_risk(
            playable_count,
            seconds_remaining,
            phase=phase,
        )
    )

    pressure = (
        calculate_lineup_pressure_score(
            playable_count,
            seconds_remaining,
            phase=phase,
        )
    )

    premium_freedom = (
        calculate_premium_freedom_bonus(
            playable_count,
            seconds_remaining,
            phase=phase,
        )
    )

    future_markets = (
        calculate_expected_future_market_opportunities(
            calendar
        )
    )

    hard_safety_mode = bool(
        calendar.get(
            "hard_safety",
            False,
        )
    )

    operations_locked = bool(
        calendar.get(
            "operations_locked",
            False,
        )
    )

    return {
        # ----------------------------------------------------
        # CALENDARIO
        # ----------------------------------------------------

        "calendar":
            calendar,

        "target_matchday":
            calendar.get(
                "target_matchday"
            ),

        "next_matchday":
            calendar.get(
                "next_matchday"
            ),

        "phase":
            phase,

        "first_match":
            calendar.get(
                "first_match"
            ),

        "first_kickoff":
            calendar.get(
                "first_kickoff"
            ),

        "safety_deadline":
            calendar.get(
                "safety_deadline"
            ),

        "real_deadline":
            calendar.get(
                "real_deadline"
            ),

        "next_round_unlock":
            calendar.get(
                "next_round_unlock"
            ),

        "seconds_to_deadline":
            seconds_remaining,

        # ----------------------------------------------------
        # XI
        # ----------------------------------------------------

        "playable_count":
            playable_count,

        "missing_playable":
            missing,

        # ----------------------------------------------------
        # RIESGO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SAFETY
        # ----------------------------------------------------

        "hard_safety_mode":
            hard_safety_mode,

        "operations_locked":
            operations_locked,

        "round_transition_lock":
            bool(
                calendar.get(
                    "transition_locked",
                    False,
                )
            ),
    }
