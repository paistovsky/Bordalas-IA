from src.analysis.price_history_engine import (
    build_price_history_index,
    collapse_duplicate_prices,
)


# ======================================================
# CONFIGURACIÓN
# ======================================================


SECONDS_PER_DAY = (
    24 * 60 * 60
)


# ======================================================
# UTILIDADES
# ======================================================


def percent_change(
    old: int,
    new: int,
) -> float:

    if old <= 0:
        return 0.0

    return (
        (new - old)
        / old
    ) * 100


def find_record_before(
    history: list[dict],
    target_timestamp: int,
) -> dict | None:
    """
    Devuelve el registro más reciente anterior
    o igual al timestamp objetivo.
    """

    candidate = None

    for record in history:

        if (
            record[
                "timestamp"
            ]
            <= target_timestamp
        ):

            candidate = record

        else:
            break

    return candidate


# ======================================================
# CAMBIO POR VENTANA
# ======================================================


def calculate_window_change(
    history: list[dict],
    days: int,
) -> dict:

    if not history:

        return {
            "available":
                False,

            "days":
                days,

            "change":
                0,

            "change_percent":
                0.0,
        }

    latest = (
        history[
            -1
        ]
    )

    target_timestamp = (
        latest[
            "timestamp"
        ]
        - days
        * SECONDS_PER_DAY
    )

    old = (
        find_record_before(
            history,
            target_timestamp,
        )
    )

    if old is None:

        return {
            "available":
                False,

            "days":
                days,

            "change":
                0,

            "change_percent":
                0.0,
        }

    change = (
        latest[
            "price"
        ]
        - old[
            "price"
        ]
    )

    return {
        "available":
            True,

        "days":
            days,

        "start_price":
            old[
                "price"
            ],

        "end_price":
            latest[
                "price"
            ],

        "change":
            change,

        "change_percent":
            round(
                percent_change(
                    old[
                        "price"
                    ],
                    latest[
                        "price"
                    ],
                ),
                2,
            ),
    }


# ======================================================
# VELOCIDAD
# ======================================================


def calculate_velocity(
    history: list[dict],
) -> dict:

    if len(
        history
    ) < 2:

        return {
            "available":
                False,

            "value_per_day":
                0.0,

            "percent_per_day":
                0.0,
        }

    first = (
        history[
            0
        ]
    )

    latest = (
        history[
            -1
        ]
    )

    seconds = (
        latest[
            "timestamp"
        ]
        - first[
            "timestamp"
        ]
    )

    if seconds <= 0:

        return {
            "available":
                False,

            "value_per_day":
                0.0,

            "percent_per_day":
                0.0,
        }

    days = (
        seconds
        / SECONDS_PER_DAY
    )

    value_change = (
        latest[
            "price"
        ]
        - first[
            "price"
        ]
    )

    value_per_day = (
        value_change
        / days
    )

    percent_total = (
        percent_change(
            first[
                "price"
            ],
            latest[
                "price"
            ],
        )
    )

    return {
        "available":
            True,

        "value_per_day":
            round(
                value_per_day,
                0,
            ),

        "percent_per_day":
            round(
                percent_total
                / days,
                2,
            ),
    }


# ======================================================
# ACELERACIÓN
# ======================================================


def calculate_acceleration(
    history: list[dict],
) -> dict:
    """
    Compara los dos últimos cambios de precio.

    Ejemplo:

        +40k
        +80k

    → acelerando

        +100k
        +30k

    → desacelerando
    """

    if len(
        history
    ) < 3:

        return {
            "available":
                False,

            "previous_change":
                0,

            "latest_change":
                0,

            "acceleration":
                0,

            "state":
                "INSUFFICIENT_HISTORY",
        }

    a = history[
        -3
    ]

    b = history[
        -2
    ]

    c = history[
        -1
    ]

    previous_change = (
        b[
            "price"
        ]
        - a[
            "price"
        ]
    )

    latest_change = (
        c[
            "price"
        ]
        - b[
            "price"
        ]
    )

    acceleration = (
        latest_change
        - previous_change
    )

    # ==================================================
    # ESTADO
    # ==================================================

    if (
        latest_change > 0
        and acceleration > 0
    ):

        state = (
            "ACCELERATING_UP"
        )

    elif (
        latest_change > 0
        and acceleration < 0
    ):

        state = (
            "DECELERATING_UP"
        )

    elif (
        latest_change < 0
        and acceleration < 0
    ):

        state = (
            "ACCELERATING_DOWN"
        )

    elif (
        latest_change < 0
        and acceleration > 0
    ):

        state = (
            "DECELERATING_DOWN"
        )

    elif latest_change > 0:

        state = (
            "STEADY_UP"
        )

    elif latest_change < 0:

        state = (
            "STEADY_DOWN"
        )

    else:

        state = (
            "FLAT"
        )

    return {
        "available":
            True,

        "previous_change":
            previous_change,

        "latest_change":
            latest_change,

        "acceleration":
            acceleration,

        "state":
            state,
    }


# ======================================================
# TREND SCORE
# ======================================================


def calculate_trend_score(
    latest: dict,
    change_1d: dict,
    change_3d: dict,
    change_7d: dict,
    acceleration: dict,
) -> float:

    score = 50.0

    current_increment = int(
        latest.get(
            "price_increment",
            0,
        )
        or 0
    )

    # ==================================================
    # MOMENTUM ACTUAL
    # ==================================================

    if current_increment >= 150_000:
        score += 18

    elif current_increment >= 100_000:
        score += 15

    elif current_increment >= 60_000:
        score += 11

    elif current_increment >= 30_000:
        score += 7

    elif current_increment > 0:
        score += 3

    elif current_increment <= -100_000:
        score -= 18

    elif current_increment <= -60_000:
        score -= 13

    elif current_increment <= -30_000:
        score -= 8

    elif current_increment < 0:
        score -= 4

    # ==================================================
    # 1 DÍA
    # ==================================================

    if change_1d[
        "available"
    ]:

        pct = (
            change_1d[
                "change_percent"
            ]
        )

        if pct >= 10:
            score += 12

        elif pct >= 5:
            score += 8

        elif pct >= 2:
            score += 4

        elif pct <= -10:
            score -= 12

        elif pct <= -5:
            score -= 8

        elif pct < 0:
            score -= 4

    # ==================================================
    # 3 DÍAS
    # ==================================================

    if change_3d[
        "available"
    ]:

        pct = (
            change_3d[
                "change_percent"
            ]
        )

        if pct >= 15:
            score += 10

        elif pct >= 8:
            score += 7

        elif pct >= 3:
            score += 4

        elif pct <= -15:
            score -= 10

        elif pct <= -8:
            score -= 7

        elif pct < 0:
            score -= 4

    # ==================================================
    # 7 DÍAS
    # ==================================================

    if change_7d[
        "available"
    ]:

        pct = (
            change_7d[
                "change_percent"
            ]
        )

        if pct >= 20:
            score += 8

        elif pct >= 10:
            score += 5

        elif pct <= -20:
            score -= 8

        elif pct <= -10:
            score -= 5

    # ==================================================
    # ACELERACIÓN
    # ==================================================

    state = (
        acceleration[
            "state"
        ]
    )

    if state == "ACCELERATING_UP":

        score += 12

    elif state == "STEADY_UP":

        score += 7

    elif state == "DECELERATING_UP":

        score += 2

    elif state == "ACCELERATING_DOWN":

        score -= 12

    elif state == "STEADY_DOWN":

        score -= 7

    elif state == "DECELERATING_DOWN":

        score -= 2

    return round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        1,
    )


# ======================================================
# CLASIFICACIÓN
# ======================================================


def classify_trend(
    score: float,
    acceleration_state: str,
) -> str:

    if score >= 85:

        return (
            "STRONG_UPTREND"
        )

    if score >= 70:

        if acceleration_state == (
            "DECELERATING_UP"
        ):

            return (
                "UPTREND_WEAKENING"
            )

        return (
            "UPTREND"
        )

    if score >= 55:

        return (
            "POSITIVE"
        )

    if score >= 45:

        return (
            "NEUTRAL"
        )

    if score >= 30:

        return (
            "NEGATIVE"
        )

    return (
        "STRONG_DOWNTREND"
    )


# ======================================================
# ANALIZAR JUGADOR
# ======================================================


def analyze_player_trend(
    history: list[dict],
) -> dict:

    history = (
        collapse_duplicate_prices(
            history
        )
    )

    if not history:

        return {
            "available":
                False,

            "trend_score":
                50.0,

            "trend":
                "NO_HISTORY",

            "records":
                0,
        }

    latest = (
        history[
            -1
        ]
    )

    change_1d = (
        calculate_window_change(
            history,
            1,
        )
    )

    change_3d = (
        calculate_window_change(
            history,
            3,
        )
    )

    change_7d = (
        calculate_window_change(
            history,
            7,
        )
    )

    velocity = (
        calculate_velocity(
            history
        )
    )

    acceleration = (
        calculate_acceleration(
            history
        )
    )

    score = (
        calculate_trend_score(
            latest=
                latest,

            change_1d=
                change_1d,

            change_3d=
                change_3d,

            change_7d=
                change_7d,

            acceleration=
                acceleration,
        )
    )

    trend = (
        classify_trend(
            score,
            acceleration[
                "state"
            ],
        )
    )

    oldest = (
        history[
            0
        ]
    )

    total_change = (
        latest[
            "price"
        ]
        - oldest[
            "price"
        ]
    )

    total_percent = (
        percent_change(
            oldest[
                "price"
            ],
            latest[
                "price"
            ],
        )
    )

    return {
        "available":
            True,

        "player_id":
            latest[
                "player_id"
            ],

        "name":
            latest[
                "name"
            ],

        "records":
            len(
                history
            ),

        "current_price":
            latest[
                "price"
            ],

        "current_increment":
            latest[
                "price_increment"
            ],

        "first_price":
            oldest[
                "price"
            ],

        "total_change":
            total_change,

        "total_change_percent":
            round(
                total_percent,
                2,
            ),

        "change_1d":
            change_1d,

        "change_3d":
            change_3d,

        "change_7d":
            change_7d,

        "velocity":
            velocity,

        "acceleration":
            acceleration,

        "trend_score":
            score,

        "trend":
            trend,
    }


# ======================================================
# BOARD COMPLETO
# ======================================================


def build_market_trend_board(
    directory: str = "data",
) -> list[dict]:

    index = (
        build_price_history_index(
            directory
        )
    )

    results = []

    for history in index.values():

        result = (
            analyze_player_trend(
                history
            )
        )

        if result[
            "available"
        ]:

            results.append(
                result
            )

    results.sort(
        key=lambda item: (
            item[
                "trend_score"
            ],
            item[
                "current_increment"
            ],
        ),
        reverse=True,
    )

    return results