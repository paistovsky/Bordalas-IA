from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MADRID_TZ_NAME = "Europe/Madrid"

COMPUTER_CYCLE_START_HOUR = 5
COMPUTER_CYCLE_END_HOUR = 7
COMPUTER_CYCLE_SAFE_MARGIN_MINUTES = 30

# Regla conservadora: para optar al ciclo de la madrugada,
# una NUEVA publicacion debe quedar hecha el dia anterior.
# Dejamos 30 minutos de margen antes de medianoche.
SAFE_LISTING_PREVIOUS_DAY_HOUR = 23
SAFE_LISTING_PREVIOUS_DAY_MINUTE = 30


def get_madrid_timezone():
    try:
        return ZoneInfo(MADRID_TZ_NAME)
    except ZoneInfoNotFoundError:
        return datetime.now().astimezone().tzinfo or timezone.utc


MADRID_TZ = get_madrid_timezone()


def parse_datetime_value(value, default_timezone=MADRID_TZ) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        result = value
    elif isinstance(value, (int, float)):
        try:
            result = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    elif isinstance(value, str):
        clean = value.strip()
        if not clean:
            return None
        if clean.isdigit():
            return parse_datetime_value(int(clean), default_timezone)
        try:
            result = datetime.fromisoformat(clean.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=default_timezone)

    return result.astimezone(MADRID_TZ)


def resolve_real_deadline(deadline: dict, now: datetime | None = None) -> datetime | None:
    now = now or datetime.now(MADRID_TZ)

    candidates = [
        deadline.get("real_deadline"),
        deadline.get("lineup_lock"),
        (deadline.get("calendar", {}) or {}).get("real_deadline"),
        (deadline.get("calendar", {}) or {}).get("lineup_lock"),
    ]

    for candidate in candidates:
        parsed = parse_datetime_value(candidate)
        if parsed is not None:
            return parsed

    seconds = deadline.get("seconds_to_deadline")
    if seconds is None:
        seconds = (
            (deadline.get("calendar", {}) or {})
            .get("seconds_to_lineup_lock")
        )

    if seconds is None:
        return None

    try:
        return now + timedelta(seconds=float(seconds))
    except (TypeError, ValueError):
        return None


def build_cycle_for_date(cycle_date) -> dict:
    cycle_start = datetime(
        cycle_date.year,
        cycle_date.month,
        cycle_date.day,
        COMPUTER_CYCLE_START_HOUR,
        0,
        tzinfo=MADRID_TZ,
    )

    cycle_end = datetime(
        cycle_date.year,
        cycle_date.month,
        cycle_date.day,
        COMPUTER_CYCLE_END_HOUR,
        0,
        tzinfo=MADRID_TZ,
    )

    safe_liquidity_at = cycle_end + timedelta(
        minutes=COMPUTER_CYCLE_SAFE_MARGIN_MINUTES
    )

    previous_day = cycle_date - timedelta(days=1)

    safe_listing_deadline = datetime(
        previous_day.year,
        previous_day.month,
        previous_day.day,
        SAFE_LISTING_PREVIOUS_DAY_HOUR,
        SAFE_LISTING_PREVIOUS_DAY_MINUTE,
        tzinfo=MADRID_TZ,
    )

    return {
        "date": cycle_date.isoformat(),
        "cycle_start": cycle_start,
        "cycle_end": cycle_end,
        "safe_liquidity_at": safe_liquidity_at,
        "safe_listing_deadline": safe_listing_deadline,
        "last_safe_listing_day": previous_day.isoformat(),
    }


def build_computer_cycle_state(
    deadline: dict,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(MADRID_TZ)

    if now.tzinfo is None:
        now = now.replace(tzinfo=MADRID_TZ)

    now = now.astimezone(MADRID_TZ)

    real_deadline = resolve_real_deadline(deadline, now)

    if real_deadline is None:
        return {
            "available": False,
            "now": now,
            "real_deadline": None,
            "safe_cycles": [],
            "safe_cycles_remaining": 0,
            "new_listing_cycles": [],
            "new_listing_cycles_remaining": 0,
            "next_safe_cycle": None,
            "last_safe_cycle": None,
            "last_safe_listing_deadline": None,
            "last_safe_listing_day": None,
            "can_list_for_future_offer": False,
            "reason": "No se conoce el deadline real.",
        }

    real_deadline = real_deadline.astimezone(MADRID_TZ)

    current_date = now.date()
    end_date = real_deadline.date()
    safe_cycles = []

    while current_date <= end_date:
        cycle = build_cycle_for_date(current_date)

        is_before_deadline = (
            cycle["safe_liquidity_at"] <= real_deadline
        )
        is_future_or_active = (
            cycle["cycle_end"] >= now
        )

        if is_before_deadline and is_future_or_active:
            safe_cycles.append(cycle)

        current_date += timedelta(days=1)

    new_listing_cycles = [
        cycle
        for cycle in safe_cycles
        if now <= cycle["safe_listing_deadline"]
    ]

    next_safe_cycle = safe_cycles[0] if safe_cycles else None
    last_safe_cycle = safe_cycles[-1] if safe_cycles else None

    return {
        "available": True,
        "timezone": MADRID_TZ_NAME,
        "now": now,
        "real_deadline": real_deadline,
        "cycle_window": {
            "start_hour": COMPUTER_CYCLE_START_HOUR,
            "end_hour": COMPUTER_CYCLE_END_HOUR,
            "safe_margin_minutes": COMPUTER_CYCLE_SAFE_MARGIN_MINUTES,
        },
        "safe_cycles": safe_cycles,
        "safe_cycles_remaining": len(safe_cycles),
        "new_listing_cycles": new_listing_cycles,
        "new_listing_cycles_remaining": len(new_listing_cycles),
        "next_safe_cycle": next_safe_cycle,
        "last_safe_cycle": last_safe_cycle,
        "last_safe_listing_deadline": (
            last_safe_cycle["safe_listing_deadline"]
            if last_safe_cycle
            else None
        ),
        "last_safe_listing_day": (
            last_safe_cycle["last_safe_listing_day"]
            if last_safe_cycle
            else None
        ),
        "can_list_for_future_offer": bool(new_listing_cycles),
        "reason": (
            "Ciclos Computer calculados dinamicamente "
            "a partir del T-15 real de la jornada."
        ),
    }


def find_first_safe_cycle_for_listing(
    cycle_state: dict,
    listed_at=None,
) -> dict | None:
    if not cycle_state.get("available", False):
        return None

    listed_datetime = parse_datetime_value(listed_at)

    if listed_datetime is None:
        listed_datetime = cycle_state.get("now")

    if listed_datetime is None:
        return None

    for cycle in cycle_state.get("safe_cycles", []):
        if listed_datetime <= cycle["safe_listing_deadline"]:
            return cycle

    return None
