from __future__ import annotations

from src.intelligence.jornada_perfecta_adapter import (
    STATUS_BENCH,
    STATUS_DOUBT,
    STATUS_OUT,
    STATUS_PROBABLE,
    STATUS_STARTER,
    STATUS_UNKNOWN,
    build_jornada_perfecta_lookup,
    get_jornada_perfecta_player_signal,
)


# ============================================================
# PESOS
# ============================================================


BASE_ADJUSTMENTS = {
    STATUS_STARTER:
        240.0,

    STATUS_PROBABLE:
        120.0,

    STATUS_DOUBT:
        -120.0,

    STATUS_BENCH:
        -320.0,

    STATUS_OUT:
        -1000.0,

    STATUS_UNKNOWN:
        0.0,
}


# ============================================================
# FRESHNESS
# ============================================================


def calculate_freshness_factor(
    age_hours: float | None,
) -> float:

    if age_hours is None:
        return 0.50

    if age_hours <= 6:
        return 1.00

    if age_hours <= 12:
        return 0.85

    if age_hours <= 24:
        return 0.60

    if age_hours <= 48:
        return 0.30

    return 0.10


# ============================================================
# ANALISIS DE SEÑAL
# ============================================================


def evaluate_lineup_signal(
    signal: dict,
) -> dict:

    status = (
        signal.get(
            "status",
            STATUS_UNKNOWN,
        )
    )

    confidence = float(
        signal.get(
            "confidence",
            0,
        )
        or 0
    )

    confidence_ratio = (
        max(
            0.0,
            min(
                confidence,
                100.0,
            ),
        )
        / 100.0
    )

    freshness_factor = (
        calculate_freshness_factor(
            signal.get(
                "age_hours"
            )
        )
    )

    base_adjustment = float(
        BASE_ADJUSTMENTS.get(
            status,
            0.0,
        )
    )

    effective_confidence = (
        confidence_ratio
        * freshness_factor
    )

    score_adjustment = (
        base_adjustment
        * effective_confidence
    )

    # ========================================================
    # BLOQUEO EXTERNO
    # ========================================================
    #
    # Solo NO_CONVOCADO muy fiable y fresco bloquea.
    #
    # SUPLENTE nunca es bloqueo absoluto.
    # ========================================================

    external_block = bool(
        status == STATUS_OUT
        and confidence >= 85
        and freshness_factor >= 0.85
    )

    return {
        **signal,

        "freshness_factor":
            round(
                freshness_factor,
                2,
            ),

        "effective_confidence":
            round(
                effective_confidence
                * 100,
                1,
            ),

        "base_adjustment":
            base_adjustment,

        "score_adjustment":
            round(
                score_adjustment,
                2,
            ),

        "external_block":
            external_block,
    }


# ============================================================
# BOARD
# ============================================================


def build_lineup_intelligence(
    snapshot: dict,
) -> dict:

    lookup = (
        build_jornada_perfecta_lookup()
    )

    data = (
        lookup[
            "data"
        ]
    )

    player_lookup = {}

    matched = 0

    for player in snapshot.get(
        "my_team",
        [],
    ):

        player_id = int(
            player[
                "id"
            ]
        )

        raw_signal = (
            get_jornada_perfecta_player_signal(
                player=
                    player,

                lookup=
                    lookup,
            )
        )

        evaluated = (
            evaluate_lineup_signal(
                raw_signal
            )
        )

        if evaluated.get(
            "matched",
            False,
        ):

            matched += 1

        player_lookup[
            player_id
        ] = evaluated

    if not data.get(
        "available",
        False,
    ):

        source_state = (
            "NOT_CONNECTED"
        )

    elif matched == 0:

        source_state = (
            "CONNECTED_NO_MATCHES"
        )

    else:

        source_state = (
            "JORNADA_PERFECTA"
        )

    return {
        "source_state":
            source_state,

        "source":
            data.get(
                "source",
                "JORNADA_PERFECTA",
            ),

        "available":
            data.get(
                "available",
                False,
            ),

        "updated_at":
            data.get(
                "updated_at"
            ),

        "age_hours":
            data.get(
                "age_hours"
            ),

        "round":
            data.get(
                "round"
            ),

        "matched_players":
            matched,

        "team_players":
            len(
                snapshot.get(
                    "my_team",
                    [],
                )
            ),

        "lookup":
            player_lookup,
    }