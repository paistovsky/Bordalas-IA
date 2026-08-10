from src.analysis.acquisition_engine import (
    build_acquisition_board,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


# ======================================================
# UTILIDADES
# ======================================================


def calculate_roi(
    acquisition_price: int,
    current_price: int,
) -> dict:

    if acquisition_price <= 0:

        return {
            "profit":
                0,

            "roi_percent":
                0.0,
        }

    profit = (
        current_price
        - acquisition_price
    )

    roi = (
        profit
        / acquisition_price
    ) * 100

    return {
        "profit":
            profit,

        "roi_percent":
            round(
                roi,
                2,
            ),
    }


# ======================================================
# ACELERACIÓN
# ======================================================


def get_acceleration_state(
    speculation: dict,
) -> str:

    trend_data = (
        speculation.get(
            "trend_data",
            {},
        )
        or {}
    )

    acceleration = (
        trend_data.get(
            "acceleration",
            {},
        )
        or {}
    )

    return acceleration.get(
        "state",
        "INSUFFICIENT_HISTORY",
    )


# ======================================================
# ESTRATEGIA DE SALIDA
# ======================================================


def classify_roi_action(
    acquisition: dict,
    speculation: dict,
) -> dict:

    speculation_action = (
        speculation.get(
            "speculation_action"
        )
    )

    availability = (
        speculation.get(
            "availability_risk",
            {},
        )
        or {}
    )

    # ==================================================
    # RIESGO DURO
    # ==================================================

    if (
        speculation_action
        == "SELL_RISK"
        or
        availability.get(
            "risk"
        )
        == "CRITICO"
    ):

        return {
            "action":
                "EXIT_RISK",

            "priority":
                100,

            "reason": (
                "Existe un riesgo deportivo crítico. "
                "La protección de capital tiene prioridad."
            ),
        }

    # ==================================================
    # NO CONOCEMOS COMPRA
    # ==================================================

    if not acquisition.get(
        "acquisition_known"
    ):

        if speculation_action in {
            "SELL_SPECULATION",
            "WATCH_SELL",
        }:

            return {
                "action":
                    "WATCH_EXIT_NO_ROI",

                "priority":
                    60,

                "reason": (
                    "La señal de mercado se deteriora, "
                    "pero no conocemos el precio real "
                    "de adquisición."
                ),
            }

        if speculation_action == (
            "HOLD_SPECULATION"
        ):

            return {
                "action":
                    "HOLD_MOMENTUM_NO_ROI",

                "priority":
                    30,

                "reason": (
                    "Momentum positivo, aunque no podemos "
                    "calcular rentabilidad real porque la "
                    "compra es anterior al histórico."
                ),
            }

        return {
            "action":
                "HOLD_NO_ROI",

            "priority":
                20,

            "reason": (
                "No existe precio de adquisición fiable."
            ),
        }

    # ==================================================
    # ROI REAL
    # ==================================================

    acquisition_price = int(
        acquisition[
            "acquisition_price"
        ]
    )

    current_price = int(
        acquisition[
            "current_price"
        ]
    )

    roi = (
        calculate_roi(
            acquisition_price,
            current_price,
        )
    )

    roi_percent = (
        roi[
            "roi_percent"
        ]
    )

    trend_score = float(
        speculation.get(
            "trend_score",
            50,
        )
        or 50
    )

    trend = (
        speculation.get(
            "trend",
            "NEUTRAL",
        )
    )

    increment = int(
        speculation.get(
            "price_increment",
            0,
        )
        or 0
    )

    acceleration = (
        get_acceleration_state(
            speculation
        )
    )

    # ==================================================
    # TAKE PROFIT FUERTE
    # ==================================================

    if (
        roi_percent >= 40
        and
        (
            increment <= 0
            or trend_score < 55
            or acceleration
            in {
                "DECELERATING_UP",
                "STEADY_DOWN",
                "ACCELERATING_DOWN",
            }
        )
    ):

        return {
            "action":
                "TAKE_PROFIT",

            "priority":
                90,

            "reason": (
                "La posición acumula una plusvalía alta "
                "y aparecen señales de agotamiento."
            ),

            **roi,
        }

    # ==================================================
    # GANADOR FUERTE
    # ==================================================

    if (
        roi_percent >= 25
        and
        increment > 0
        and
        trend_score >= 55
    ):

        return {
            "action":
                "HOLD_WINNER",

            "priority":
                30,

            "reason": (
                "Existe una plusvalía importante y "
                "el momentum sigue siendo positivo."
            ),

            **roi,
        }

    # ==================================================
    # BENEFICIO NORMAL
    # ==================================================

    if (
        roi_percent >= 10
        and
        increment > 0
    ):

        return {
            "action":
                "HOLD_PROFIT",

            "priority":
                35,

            "reason": (
                "La posición está en beneficio y "
                "continúa apreciándose."
            ),

            **roi,
        }

    # ==================================================
    # STOP / CUT LOSS
    # ==================================================

    if (
        roi_percent <= -10
        and
        increment < 0
        and
        trend_score < 50
    ):

        return {
            "action":
                "CUT_LOSS",

            "priority":
                85,

            "reason": (
                "La posición acumula pérdida relevante "
                "y la tendencia continúa deteriorándose."
            ),

            **roi,
        }

    # ==================================================
    # RECUPERACIÓN
    # ==================================================

    if (
        roi_percent < 0
        and
        increment > 0
        and
        trend_score >= 50
    ):

        return {
            "action":
                "HOLD_RECOVERY",

            "priority":
                40,

            "reason": (
                "La posición sigue en pérdida, pero "
                "el mercado muestra recuperación."
            ),

            **roi,
        }

    # ==================================================
    # DETERIORO CON BENEFICIO
    # ==================================================

    if (
        roi_percent > 0
        and
        increment < 0
    ):

        return {
            "action":
                "WATCH_TAKE_PROFIT",

            "priority":
                65,

            "reason": (
                "Todavía existe beneficio, pero "
                "el momentum actual es negativo."
            ),

            **roi,
        }

    # ==================================================
    # NEUTRAL
    # ==================================================

    return {
        "action":
            "HOLD",

        "priority":
            20,

        "reason": (
            "No existe una señal suficientemente fuerte "
            "para cerrar la posición."
        ),

        **roi,
    }


# ======================================================
# BOARD
# ======================================================


def build_portfolio_roi_board(
    snapshot: dict,
) -> dict:

    acquisition_board = (
        build_acquisition_board(
            snapshot
        )
    )

    speculation_board = (
        build_speculation_board(
            snapshot
        )
    )

    acquisition_lookup = {
        int(
            item[
                "player_id"
            ]
        ):
            item

        for item in acquisition_board[
            "players"
        ]
    }

    speculation_lookup = {
        int(
            item[
                "id"
            ]
        ):
            item

        for item in speculation_board[
            "owned"
        ]
    }

    positions = []

    for player_id, acquisition in (
        acquisition_lookup.items()
    ):

        speculation = (
            speculation_lookup.get(
                player_id,
                {},
            )
        )

        decision = (
            classify_roi_action(
                acquisition=
                    acquisition,

                speculation=
                    speculation,
            )
        )

        acquisition_price = (
            acquisition.get(
                "acquisition_price"
            )
        )

        current_price = int(
            acquisition.get(
                "current_price",
                0,
            )
            or 0
        )

        if acquisition_price:

            roi = (
                calculate_roi(
                    int(
                        acquisition_price
                    ),
                    current_price,
                )
            )

        else:

            roi = {
                "profit":
                    None,

                "roi_percent":
                    None,
            }

        positions.append(
            {
                "player_id":
                    player_id,

                "name":
                    acquisition.get(
                        "name"
                    ),

                "current_price":
                    current_price,

                "acquisition_known":
                    acquisition.get(
                        "acquisition_known",
                        False,
                    ),

                "acquisition_price":
                    acquisition_price,

                "acquisition_source":
                    acquisition.get(
                        "source"
                    ),

                "acquisition_confidence":
                    acquisition.get(
                        "confidence",
                        0,
                    ),

                "profit":
                    roi[
                        "profit"
                    ],

                "roi_percent":
                    roi[
                        "roi_percent"
                    ],

                "speculation_score":
                    speculation.get(
                        "speculation_score"
                    ),

                "speculation_action":
                    speculation.get(
                        "speculation_action"
                    ),

                "trend_score":
                    speculation.get(
                        "trend_score"
                    ),

                "trend":
                    speculation.get(
                        "trend"
                    ),

                "price_increment":
                    speculation.get(
                        "price_increment",
                        0,
                    ),

                "history_confidence":
                    speculation.get(
                        "history_confidence",
                        {},
                    ),

                "acceleration_state":
                    get_acceleration_state(
                        speculation
                    ),

                "portfolio_action":
                    decision[
                        "action"
                    ],

                "portfolio_priority":
                    decision[
                        "priority"
                    ],

                "portfolio_reason":
                    decision[
                        "reason"
                    ],
            }
        )

    positions.sort(
        key=lambda item: (
            item[
                "portfolio_priority"
            ],
            (
                item[
                    "roi_percent"
                ]
                if item[
                    "roi_percent"
                ]
                is not None
                else -999
            ),
        ),
        reverse=True,
    )

    known = [
        item

        for item in positions

        if item[
            "acquisition_known"
        ]
    ]

    unknown = [
        item

        for item in positions

        if not item[
            "acquisition_known"
        ]
    ]

    exits = [
        item

        for item in positions

        if item[
            "portfolio_action"
        ]
        in {
            "EXIT_RISK",
            "TAKE_PROFIT",
            "CUT_LOSS",
            "WATCH_TAKE_PROFIT",
            "WATCH_EXIT_NO_ROI",
        }
    ]

    holds = [
        item

        for item in positions

        if item[
            "portfolio_action"
        ]
        not in {
            "EXIT_RISK",
            "TAKE_PROFIT",
            "CUT_LOSS",
            "WATCH_TAKE_PROFIT",
            "WATCH_EXIT_NO_ROI",
        }
    ]

    total_known_cost = sum(
        int(
            item[
                "acquisition_price"
            ]
        )

        for item in known

        if item[
            "acquisition_price"
        ]
    )

    total_known_value = sum(
        int(
            item[
                "current_price"
            ]
        )

        for item in known
    )

    if total_known_cost > 0:

        portfolio_roi = (
            (
                total_known_value
                - total_known_cost
            )
            / total_known_cost
        ) * 100

    else:

        portfolio_roi = None

    return {
        "acquisition_board":
            acquisition_board,

        "speculation_board":
            speculation_board,

        "positions":
            positions,

        "known":
            known,

        "unknown":
            unknown,

        "exits":
            exits,

        "holds":
            holds,

        "known_count":
            len(
                known
            ),

        "unknown_count":
            len(
                unknown
            ),

        "total_known_cost":
            total_known_cost,

        "total_known_value":
            total_known_value,

        "total_known_profit":
            (
                total_known_value
                - total_known_cost
            ),

        "portfolio_roi_percent":
            (
                round(
                    portfolio_roi,
                    2,
                )
                if portfolio_roi
                is not None
                else None
            ),
    }