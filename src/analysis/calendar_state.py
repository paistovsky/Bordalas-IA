from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.analysis.matchday_calendar_engine import (
    refresh_dynamic_calendar,
)


MADRID_TZ = ZoneInfo(
    "Europe/Madrid"
)

AUTOPILOT_CYCLE_SECONDS = (
    30
    * 60
)


# ============================================================
# UTILIDADES
# ============================================================


def get_biwenger_round_id(
    snapshot: dict,
) -> int | None:
    """
    ID tecnico interno de Biwenger.

    IMPORTANTE:
    NO se utiliza para calcular el deadline deportivo.
    """

    return (
        snapshot
        .get(
            "rounds",
            {},
        )
        .get(
            "data",
            {},
        )
        .get(
            "round",
            {},
        )
        .get(
            "id"
        )
    )


def build_now(
    now_ts: int | None = None,
) -> datetime:

    if now_ts is None:

        return datetime.now(
            MADRID_TZ
        )

    return datetime.fromtimestamp(
        now_ts,
        tz=MADRID_TZ,
    )


def positive_seconds(
    value: int | None,
) -> int | None:

    if value is None:
        return None

    return max(
        int(
            value
        ),
        0,
    )


def estimate_market_cycles(
    seconds_to_deadline: int | None,
) -> int | None:
    """
    Estima cuantos ciclos de Autopilot quedan hasta T-15.

    Se mantiene por compatibilidad con motores ya existentes.
    """

    if seconds_to_deadline is None:
        return None

    if seconds_to_deadline <= 0:
        return 0

    return max(
        int(
            seconds_to_deadline
            // AUTOPILOT_CYCLE_SECONDS
        ),
        0,
    )


# ============================================================
# CALENDAR STATE
# ============================================================


def build_calendar_state(
    snapshot: dict,
    now_ts: int | None = None,
) -> dict:
    """
    Estado temporal estrategico de Bordalas IA.

    FUENTE DE VERDAD:
        calendario dinamico real de LaLiga.

    El round interno de Biwenger se conserva unicamente
    como dato tecnico/diagnostico.

    REGLAS:
        T-90 min -> safety deadline.
        T-15 min -> deadline real.
        kickoff  -> comienza jornada.
        kickoff + 2h -> se desbloquea trabajo para J+1.
    """

    now = (
        build_now(
            now_ts
        )
    )

    dynamic = (
        refresh_dynamic_calendar(
            force=False,
            now=now,
        )
    )

    phase = (
        dynamic.get(
            "phase",
            "CALENDAR_UNKNOWN",
        )
    )

    seconds_to_deadline = (
        dynamic.get(
            "seconds_to_deadline"
        )
    )

    seconds_to_first_kickoff = (
        dynamic.get(
            "seconds_to_first_kickoff"
        )
    )

    seconds_to_unlock = (
        dynamic.get(
            "seconds_to_unlock"
        )
    )

    # Calculamos T-90 a partir de T-15.
    # Entre ambos hay 75 minutos.
    if seconds_to_deadline is None:

        seconds_to_safety_deadline = (
            None
        )

    else:

        seconds_to_safety_deadline = (
            int(
                seconds_to_deadline
            )
            - (
                75
                * 60
            )
        )

    round_locked = (
        phase
        in {
            "ROUND_LOCKED",
            "ROUND_TRANSITION_LOCK",
        }
    )

    transition_locked = bool(
        phase
        == "ROUND_TRANSITION_LOCK"
        or
        dynamic.get(
            "round_transition_lock",
            False,
        )
    )

    hard_safety = (
        phase
        in {
            "HARD_SAFETY",
            "ROUND_LOCKED",
            "ROUND_TRANSITION_LOCK",
        }
    )

    return {
        # ----------------------------------------------------
        # IDENTIDAD
        # ----------------------------------------------------

        "now":
            now.isoformat(),

        "timezone":
            "Europe/Madrid",

        "biwenger_round_id":
            get_biwenger_round_id(
                snapshot
            ),

        "target_matchday":
            dynamic.get(
                "target_matchday"
            ),

        "next_matchday":
            dynamic.get(
                "next_matchday"
            ),

        # ----------------------------------------------------
        # CALENDARIO REAL
        # ----------------------------------------------------

        "calendar_source":
            dynamic.get(
                "source"
            ),

        "calendar_fetched_at":
            dynamic.get(
                "calendar_fetched_at"
            ),

        "calendar_refresh_performed":
            dynamic.get(
                "refresh_performed",
                False,
            ),

        "calendar_refresh_error":
            dynamic.get(
                "refresh_error"
            ),

        "calendar_changes":
            dynamic.get(
                "changes_detected",
                [],
            ),

        "first_match":
            dynamic.get(
                "first_match"
            ),

        "first_kickoff":
            dynamic.get(
                "first_kickoff"
            ),

        "safety_deadline":
            dynamic.get(
                "safety_deadline"
            ),

        "real_deadline":
            dynamic.get(
                "real_deadline"
            ),

        "next_round_unlock":
            dynamic.get(
                "next_round_unlock"
            ),

        # ----------------------------------------------------
        # CONTADORES
        # ----------------------------------------------------

        # Compatibilidad:
        # todos los motores antiguos que lean
        # seconds_to_lineup_lock pasan automaticamente
        # a utilizar el deadline real T-15.
        "seconds_to_lineup_lock":
            seconds_to_deadline,

        "seconds_to_deadline":
            seconds_to_deadline,

        "seconds_to_safety_deadline":
            seconds_to_safety_deadline,

        "seconds_to_first_kickoff":
            seconds_to_first_kickoff,

        "seconds_to_next_round_unlock":
            seconds_to_unlock,

        "estimated_market_cycles":
            estimate_market_cycles(
                seconds_to_deadline
            ),

        # ----------------------------------------------------
        # FASE ESTRATEGICA
        # ----------------------------------------------------

        "phase":
            phase,

        "round_locked":
            round_locked,

        "transition_locked":
            transition_locked,

        "hard_safety":
            hard_safety,

        # Cuando esto es True, Bordalas NO debe realizar
        # compras, ventas, cambios de XI ni otras operaciones
        # estrategicas.
        "operations_locked":
            round_locked,

        # ----------------------------------------------------
        # RAW
        # ----------------------------------------------------

        "dynamic_calendar":
            dynamic,
    }
