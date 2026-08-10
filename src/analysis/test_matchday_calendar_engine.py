from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.analysis.matchday_calendar_engine import (
    refresh_dynamic_calendar,
)


MADRID_TZ = ZoneInfo(
    "Europe/Madrid"
)


def format_dt(
    value: str | None,
) -> str:

    if not value:
        return "DESCONOCIDO"

    parsed = (
        datetime.fromisoformat(
            value
        )
    )

    return (
        parsed.astimezone(
            MADRID_TZ
        ).strftime(
            "%d/%m/%Y %H:%M"
        )
    )


def format_seconds(
    value: int | None,
) -> str:

    if value is None:
        return "DESCONOCIDO"

    if value <= 0:
        return "0m"

    days, remainder = divmod(
        value,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes = (
        remainder
        // 60
    )

    parts = []

    if days:
        parts.append(
            f"{days}d"
        )

    if hours:
        parts.append(
            f"{hours}h"
        )

    parts.append(
        f"{minutes}m"
    )

    return " ".join(
        parts
    )


def main() -> None:

    state = (
        refresh_dynamic_calendar(
            force=True
        )
    )

    first_match = (
        state.get(
            "first_match"
        )
        or {}
    )

    print()
    print("=" * 100)
    print(
        "             BORDALAS IA - DYNAMIC MATCHDAY CALENDAR"
    )
    print("=" * 100)
    print()

    print(
        f"Fuente:               "
        f"{state.get('source')}"
    )

    print(
        f"Refresco:              "
        f"{'SI' if state.get('refresh_performed') else 'NO'}"
    )

    print(
        f"Error refresco:        "
        f"{state.get('refresh_error') or 'NINGUNO'}"
    )

    print()

    print(
        f"Jornada objetivo:      "
        f"{state.get('target_matchday')}"
    )

    print(
        f"Siguiente jornada:     "
        f"{state.get('next_matchday')}"
    )

    print(
        f"Fase:                  "
        f"{state.get('phase')}"
    )

    print()

    print(
        f"Primer partido:        "
        f"{first_match.get('home', '?')} "
        f"- "
        f"{first_match.get('away', '?')}"
    )

    print(
        f"Inicio:                "
        f"{format_dt(state.get('first_kickoff'))}"
    )

    print(
        f"Safety deadline:       "
        f"{format_dt(state.get('safety_deadline'))}"
    )

    print(
        f"Deadline real:         "
        f"{format_dt(state.get('real_deadline'))}"
    )

    print(
        f"Desbloqueo siguiente:  "
        f"{format_dt(state.get('next_round_unlock'))}"
    )

    print()

    print(
        f"Tiempo al deadline:    "
        f"{format_seconds(state.get('seconds_to_deadline'))}"
    )

    print()

    changes = (
        state.get(
            "changes_detected",
            [],
        )
        or []
    )

    print(
        f"Cambios calendario:    "
        f"{len(changes)}"
    )

    for change in changes[
        :10
    ]:

        print(
            "  - "
            f"{change.get('type')} | "
            f"J{change.get('matchday')} | "
            f"{change.get('home')} - "
            f"{change.get('away')}"
        )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
