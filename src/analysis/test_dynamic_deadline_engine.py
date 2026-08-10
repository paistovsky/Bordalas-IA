from __future__ import annotations

from datetime import datetime

from src.analysis.deadline_engine import (
    build_deadline_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def fmt_dt(
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
        parsed.strftime(
            "%d/%m/%Y %H:%M"
        )
    )


def fmt_seconds(
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

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    state = (
        build_deadline_state(
            snapshot
        )
    )

    first_match = (
        state.get(
            "first_match"
        )
        or {}
    )

    calendar = (
        state.get(
            "calendar",
            {}
        )
        or {}
    )

    print()
    print("=" * 100)
    print(
        "                 BORDALAS IA - DYNAMIC DEADLINE ENGINE"
    )
    print("=" * 100)
    print()

    print(
        f"Snapshot:              "
        f"{snapshot_file}"
    )

    print()

    print(
        f"Biwenger round ID:     "
        f"{calendar.get('biwenger_round_id')}"
    )

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
        f"{first_match.get('home', '?')} - "
        f"{first_match.get('away', '?')}"
    )

    print(
        f"Inicio:                "
        f"{fmt_dt(state.get('first_kickoff'))}"
    )

    print(
        f"Safety deadline:       "
        f"{fmt_dt(state.get('safety_deadline'))}"
    )

    print(
        f"Deadline real:         "
        f"{fmt_dt(state.get('real_deadline'))}"
    )

    print(
        f"Desbloqueo siguiente:  "
        f"{fmt_dt(state.get('next_round_unlock'))}"
    )

    print(
        f"Tiempo al deadline:    "
        f"{fmt_seconds(state.get('seconds_to_deadline'))}"
    )

    print()

    print(
        f"XI computable:         "
        f"{state.get('playable_count')}/11"
    )

    print(
        f"Huecos:                "
        f"{state.get('missing_playable')}"
    )

    print(
        f"Riesgo tiempo:         "
        f"{state.get('time_risk')}"
    )

    print(
        f"Riesgo XI:             "
        f"{state.get('lineup_risk')}"
    )

    print(
        f"Presion XI:            "
        f"{state.get('lineup_pressure_score')}/100"
    )

    print(
        f"Premium freedom:       "
        f"{state.get('premium_freedom_bonus')}"
    )

    print()

    print(
        f"Hard Safety:           "
        f"{'SI' if state.get('hard_safety_mode') else 'NO'}"
    )

    print(
        f"Operaciones bloqueadas:"
        f" {'SI' if state.get('operations_locked') else 'NO'}"
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
