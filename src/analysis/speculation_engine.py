from src.analysis.market_trend_engine import (
    build_market_trend_board,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ======================================================
# CONFIGURACIÓN
# ======================================================


MAX_SPECULATION_BUDGET_PERCENT = 0.15
MAX_SINGLE_SPECULATION_PERCENT = 0.40

BUY_THRESHOLD = 72
WATCH_THRESHOLD = 55
HOLD_THRESHOLD = 55
SELL_THRESHOLD = 35

FRANCHISE_THRESHOLD = 70


# ======================================================
# UTILIDADES
# ======================================================


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def get_market_status(
    snapshot: dict,
) -> dict:

    return (
        snapshot
        .get(
            "market",
            {},
        )
        .get(
            "status",
            {},
        )
        or {}
    )


# ======================================================
# CONFIANZA HISTÓRICA
# ======================================================


def calculate_history_confidence(
    records: int,
) -> dict:
    """
    La tendencia no vale lo mismo con 1 registro
    que con una semana de datos.

    0      -> 0%
    1      -> 20%
    2      -> 40%
    3-4    -> 65%
    5-7    -> 85%
    8+     -> 100%
    """

    if records <= 0:

        confidence = 0
        label = "NO_HISTORY"

    elif records == 1:

        confidence = 20
        label = "CURRENT_SIGNAL"

    elif records == 2:

        confidence = 40
        label = "EARLY_TREND"

    elif records <= 4:

        confidence = 65
        label = "DEVELOPING_TREND"

    elif records <= 7:

        confidence = 85
        label = "CONFIRMED_TREND"

    else:

        confidence = 100
        label = "STRONG_HISTORY"

    return {
        "confidence":
            confidence,

        "confidence_ratio":
            confidence / 100,

        "label":
            label,
    }


# ======================================================
# MOMENTUM ACTUAL
# ======================================================


def calculate_price_momentum(
    player: dict,
) -> dict:

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    increment = int(
        player.get(
            "price_increment",
            0,
        )
        or 0
    )

    if price <= 0:

        increment_percent = 0.0

    else:

        increment_percent = (
            increment
            / price
        ) * 100

    # ==================================================
    # ABSOLUTO
    # ==================================================

    if increment >= 200_000:
        absolute_score = 30

    elif increment >= 150_000:
        absolute_score = 27

    elif increment >= 100_000:
        absolute_score = 23

    elif increment >= 70_000:
        absolute_score = 19

    elif increment >= 40_000:
        absolute_score = 15

    elif increment >= 20_000:
        absolute_score = 10

    elif increment > 0:
        absolute_score = 5

    elif increment == 0:
        absolute_score = 0

    elif increment <= -150_000:
        absolute_score = -28

    elif increment <= -100_000:
        absolute_score = -23

    elif increment <= -60_000:
        absolute_score = -18

    elif increment <= -30_000:
        absolute_score = -12

    else:
        absolute_score = -7

    # ==================================================
    # RELATIVO
    # ==================================================

    if increment_percent >= 15:
        relative_score = 22

    elif increment_percent >= 10:
        relative_score = 19

    elif increment_percent >= 7:
        relative_score = 16

    elif increment_percent >= 5:
        relative_score = 13

    elif increment_percent >= 3:
        relative_score = 9

    elif increment_percent >= 1:
        relative_score = 5

    elif increment_percent > 0:
        relative_score = 2

    elif increment_percent == 0:
        relative_score = 0

    elif increment_percent <= -10:
        relative_score = -18

    elif increment_percent <= -7:
        relative_score = -14

    elif increment_percent <= -5:
        relative_score = -10

    elif increment_percent <= -3:
        relative_score = -7

    else:
        relative_score = -3

    total = (
        absolute_score
        + relative_score
    )

    return {
        "price_increment":
            increment,

        "price_increment_percent":
            round(
                increment_percent,
                2,
            ),

        "absolute_momentum_score":
            absolute_score,

        "relative_momentum_score":
            relative_score,

        "momentum_score":
            total,
    }


# ======================================================
# OPORTUNIDAD POR PRECIO
# ======================================================


def calculate_price_opportunity(
    player: dict,
) -> float:

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    if price <= 300_000:
        return 16

    if price <= 600_000:
        return 14

    if price <= 1_000_000:
        return 12

    if price <= 2_000_000:
        return 10

    if price <= 4_000_000:
        return 7

    if price <= 7_000_000:
        return 4

    if price <= 12_000_000:
        return 2

    return 0


# ======================================================
# SOPORTE DEPORTIVO
# ======================================================


def calculate_sporting_support(
    player: dict,
) -> float:

    strategic = float(
        player.get(
            "strategic_score",
            0,
        )
        or 0
    )

    tactical = float(
        player.get(
            "tactical_score",
            0,
        )
        or 0
    )

    points = int(
        player.get(
            "points_last_season",
            0,
        )
        or 0
    )

    score = (
        strategic * 0.08
        +
        tactical * 0.04
    )

    if points >= 180:
        score += 7

    elif points >= 140:
        score += 5

    elif points >= 100:
        score += 3

    elif points >= 60:
        score += 1

    return min(
        score,
        15,
    )


# ======================================================
# DISPONIBILIDAD / RIESGO
# ======================================================


def calculate_availability_risk(
    player: dict,
) -> dict:

    availability = (
        player.get(
            "availability",
            {},
        )
        or {}
    )

    available = availability.get(
        "available",
        True,
    )

    automatic_lineup = availability.get(
        "automatic_lineup",
        True,
    )

    label = availability.get(
        "label",
        "OK",
    )

    if not available:

        penalty = -100
        risk = "CRITICO"

    elif not automatic_lineup:

        penalty = -35
        risk = "ALTO"

    else:

        penalty = 0
        risk = "BAJO"

    return {
        "available":
            available,

        "automatic_lineup":
            automatic_lineup,

        "label":
            label,

        "risk":
            risk,

        "penalty":
            penalty,
    }


# ======================================================
# EXTERNAL INTELLIGENCE
# ======================================================


def get_external_speculation_signal(
    player: dict,
) -> dict:
    """
    Interfaz preparada para la siguiente fase.

    Aquí añadiremos:

    - noticias
    - Jornada Perfecta
    - titularidad probable
    - lesiones de compañeros
    - cambios de rol
    - calendario
    - hype fantasy
    """

    return {
        "score":
            0.0,

        "confidence":
            0.0,

        "sources":
            [],

        "status":
            "NOT_CONNECTED",
    }


# ======================================================
# LOOKUP DE TREND
# ======================================================


def build_trend_lookup() -> dict[int, dict]:

    board = (
        build_market_trend_board(
            "data"
        )
    )

    return {
        int(
            item[
                "player_id"
            ]
        ):
            item

        for item in board
    }


# ======================================================
# COMPONENTE HISTÓRICO
# ======================================================


def calculate_historical_component(
    trend: dict | None,
) -> dict:

    if trend is None:

        confidence = (
            calculate_history_confidence(
                0
            )
        )

        return {
            "trend_score":
                50.0,

            "trend":
                "NO_HISTORY",

            "records":
                0,

            "history_confidence":
                confidence,

            "historical_component":
                0.0,

            "acceleration_component":
                0.0,
        }

    records = int(
        trend.get(
            "records",
            0,
        )
        or 0
    )

    confidence = (
        calculate_history_confidence(
            records
        )
    )

    ratio = (
        confidence[
            "confidence_ratio"
        ]
    )

    trend_score = float(
        trend.get(
            "trend_score",
            50,
        )
        or 50
    )

    # Solo premiamos/castigamos la distancia respecto
    # al estado neutral (50).
    historical_component = (
        trend_score
        - 50
    ) * 0.50 * ratio

    acceleration_state = (
        trend
        .get(
            "acceleration",
            {},
        )
        .get(
            "state",
            "INSUFFICIENT_HISTORY",
        )
    )

    acceleration_base = {
        "ACCELERATING_UP":
            10,

        "STEADY_UP":
            6,

        "DECELERATING_UP":
            1,

        "FLAT":
            0,

        "DECELERATING_DOWN":
            -2,

        "STEADY_DOWN":
            -6,

        "ACCELERATING_DOWN":
            -10,

        "INSUFFICIENT_HISTORY":
            0,
    }.get(
        acceleration_state,
        0,
    )

    acceleration_component = (
        acceleration_base
        * ratio
    )

    return {
        "trend_score":
            trend_score,

        "trend":
            trend.get(
                "trend",
                "NO_HISTORY",
            ),

        "records":
            records,

        "history_confidence":
            confidence,

        "historical_component":
            round(
                historical_component,
                2,
            ),

        "acceleration_component":
            round(
                acceleration_component,
                2,
            ),

        "trend_data":
            trend,
    }


# ======================================================
# SCORE ESPECULATIVO V2
# ======================================================


def calculate_speculation_score(
    player: dict,
    trend: dict | None,
) -> dict:

    momentum = (
        calculate_price_momentum(
            player
        )
    )

    price_opportunity = (
        calculate_price_opportunity(
            player
        )
    )

    sporting_support = (
        calculate_sporting_support(
            player
        )
    )

    availability = (
        calculate_availability_risk(
            player
        )
    )

    historical = (
        calculate_historical_component(
            trend
        )
    )

    external = (
        get_external_speculation_signal(
            player
        )
    )

    # ==================================================
    # V2
    # ==================================================
    #
    # El momentum actual ya no puede disparar por sí
    # solo un 100/100.
    #
    # La tendencia histórica aumenta su peso a medida
    # que crece la confianza.
    # ==================================================

    current_component = (
        momentum[
            "momentum_score"
        ]
        * 0.55
    )

    total = (
        32
        + current_component
        + price_opportunity
        + sporting_support
        + historical[
            "historical_component"
        ]
        + historical[
            "acceleration_component"
        ]
        + availability[
            "penalty"
        ]
        + external[
            "score"
        ]
    )

    total = clamp(
        total
    )

    return {
        "speculation_score":
            round(
                total,
                1,
            ),

        **momentum,

        "current_component":
            round(
                current_component,
                2,
            ),

        "price_opportunity_score":
            round(
                price_opportunity,
                1,
            ),

        "sporting_support_score":
            round(
                sporting_support,
                1,
            ),

        "availability_risk":
            availability,

        **historical,

        "external_signal":
            external,
    }


# ======================================================
# FINALIDAD DOMINANTE
# ======================================================


def classify_dominant_role(
    player: dict,
) -> str:

    franchise = float(
        player.get(
            "franchise_score",
            0,
        )
        or 0
    )

    tactical = float(
        player.get(
            "tactical_score",
            0,
        )
        or 0
    )

    ownership = (
        player.get(
            "ownership_state"
        )
    )

    if franchise >= FRANCHISE_THRESHOLD:

        return "FRANCHISE"

    if (
        ownership == "EN_MERCADO"
        and tactical >= 75
    ):

        return "TACTICAL"

    return "SPECULATION"


# ======================================================
# DECISIÓN
# ======================================================


def classify_speculation_action(
    player: dict,
    analysis: dict,
) -> str:

    ownership = (
        player.get(
            "ownership_state"
        )
    )

    score = float(
        analysis[
            "speculation_score"
        ]
    )

    increment = int(
        analysis[
            "price_increment"
        ]
    )

    availability = (
        analysis[
            "availability_risk"
        ]
    )

    history_confidence = int(
        analysis[
            "history_confidence"
        ][
            "confidence"
        ]
    )

    dominant_role = (
        classify_dominant_role(
            player
        )
    )

    # ==================================================
    # FRANCHISE / TACTICAL TIENEN SU PROPIO MOTOR
    # ==================================================

    if (
        ownership != "MI_EQUIPO"
        and dominant_role == "FRANCHISE"
    ):

        return "DEFER_TO_FRANCHISE"

    if (
        ownership != "MI_EQUIPO"
        and dominant_role == "TACTICAL"
    ):

        return "DEFER_TO_TACTICAL"

    # ==================================================
    # JUGADOR NUESTRO
    # ==================================================

    if ownership == "MI_EQUIPO":

        # Lesiones/estados graves no necesitan
        # histórico para justificar riesgo.
        if not availability[
            "available"
        ]:

            return "SELL_RISK"

        if increment < 0:

            if score <= SELL_THRESHOLD:

                return "SELL_SPECULATION"

            return "WATCH_SELL"

        if (
            score >= HOLD_THRESHOLD
            and increment > 0
        ):

            return "HOLD_SPECULATION"

        if score <= SELL_THRESHOLD:

            return "SELL_SPECULATION"

        return "HOLD"

    # ==================================================
    # EN MERCADO
    # ==================================================

    if ownership == "EN_MERCADO":

        if not availability[
            "available"
        ]:

            return "AVOID"

        # No autorizamos compra especulativa fuerte
        # con una simple fotografía.
        if (
            score >= BUY_THRESHOLD
            and history_confidence >= 40
        ):

            return "BUY_SPECULATION"

        if (
            score >= WATCH_THRESHOLD
            and history_confidence >= 20
        ):

            return "WATCH_BUY"

        return "IGNORE"

    # ==================================================
    # FUERA DEL MERCADO
    # ==================================================

    if (
        score >= BUY_THRESHOLD
        and history_confidence >= 40
    ):

        return "WATCHLIST_HIGH"

    if (
        score >= WATCH_THRESHOLD
        and history_confidence >= 20
    ):

        return "WATCHLIST"

    return "IGNORE"


# ======================================================
# ANALIZAR JUGADOR
# ======================================================


def analyze_speculation_player(
    player: dict,
    trend: dict | None,
) -> dict:

    analysis = (
        calculate_speculation_score(
            player=
                player,

            trend=
                trend,
        )
    )

    dominant_role = (
        classify_dominant_role(
            player
        )
    )

    action = (
        classify_speculation_action(
            player,
            analysis,
        )
    )

    return {
        **player,
        **analysis,

        "dominant_role":
            dominant_role,

        "speculation_action":
            action,
    }


# ======================================================
# PUJA FRANCHISE ACTIVA
# ======================================================


def detect_active_franchise_bid(
    snapshot: dict,
    strategic_lookup: dict[int, dict],
) -> dict | None:

    offer_board = (
        build_offer_board(
            snapshot
        )
    )

    for offer in offer_board.get(
        "outgoing",
        [],
    ):

        if offer.get(
            "status"
        ) != "waiting":

            continue

        for player_id in offer.get(
            "player_ids",
            [],
        ):

            player = (
                strategic_lookup.get(
                    int(
                        player_id
                    )
                )
            )

            if player is None:
                continue

            franchise_score = float(
                player.get(
                    "franchise_score",
                    0,
                )
                or 0
            )

            if franchise_score >= FRANCHISE_THRESHOLD:

                return {
                    "offer":
                        offer,

                    "player":
                        player,
                }

    return None


# ======================================================
# PRESUPUESTO ESPECULATIVO
# ======================================================


def calculate_speculation_budget(
    snapshot: dict,
    solvency: dict,
    active_franchise_bid: dict | None,
) -> dict:

    status = (
        get_market_status(
            snapshot
        )
    )

    balance = int(
        status.get(
            "balance",
            0,
        )
        or 0
    )

    maximum_bid = int(
        status.get(
            "maximumBid",
            0,
        )
        or 0
    )

    hard_safety = (
        solvency.get(
            "hard_safety",
            {},
        )
        or {}
    )

    # ==================================================
    # FRANCHISE ACTIVO
    # ==================================================

    if active_franchise_bid is not None:

        player = (
            active_franchise_bid[
                "player"
            ]
        )

        return {
            "enabled":
                False,

            "total_budget":
                0,

            "single_operation_limit":
                0,

            "reason":
                (
                    "Existe una puja Franchise activa "
                    f"por {player['name']}. "
                    "La especulación queda congelada "
                    "hasta la resolución del mercado."
                ),

            "blocked_by":
                "FRANCHISE_ACTIVE_BID",
        }

    # ==================================================
    # HARD SAFETY
    # ==================================================

    if hard_safety.get(
        "active",
        False,
    ):

        return {
            "enabled":
                False,

            "total_budget":
                0,

            "single_operation_limit":
                0,

            "reason":
                "Hard Safety activo.",

            "blocked_by":
                "HARD_SAFETY",
        }

    # ==================================================
    # SALDO NEGATIVO
    # ==================================================

    if balance < 0:

        return {
            "enabled":
                False,

            "total_budget":
                0,

            "single_operation_limit":
                0,

            "reason":
                (
                    "Saldo negativo. La prioridad es "
                    "sanear deuda, no especular."
                ),

            "blocked_by":
                "NEGATIVE_BALANCE",
        }

    usable_capital = min(
        balance,
        maximum_bid,
    )

    total_budget = int(
        usable_capital
        * MAX_SPECULATION_BUDGET_PERCENT
    )

    single_limit = int(
        total_budget
        * MAX_SINGLE_SPECULATION_PERCENT
    )

    if total_budget < 150_000:

        return {
            "enabled":
                False,

            "total_budget":
                0,

            "single_operation_limit":
                0,

            "reason":
                (
                    "No existe capacidad suficiente "
                    "para especulación actualmente."
                ),

            "blocked_by":
                "LOW_LIQUIDITY",
        }

    return {
        "enabled":
            True,

        "total_budget":
            total_budget,

        "single_operation_limit":
            single_limit,

        "reason":
            (
                "Existe margen de liquidez para "
                "operaciones especulativas."
            ),

        "blocked_by":
            None,
    }


# ======================================================
# BOARD COMPLETO V2
# ======================================================


def build_speculation_board(
    snapshot: dict,
) -> dict:

    # ==================================================
    # STRATEGIC BOARD
    # ==================================================

    strategic_board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="strategic",
        )
    )

    strategic_lookup = {
        int(
            player[
                "id"
            ]
        ):
            player

        for player in strategic_board
    }

    # ==================================================
    # TRENDS
    # ==================================================

    trend_lookup = (
        build_trend_lookup()
    )

    # ==================================================
    # SOLVENCY
    # ==================================================

    solvency = (
        build_solvency_state(
            snapshot
        )
    )

    # ==================================================
    # FRANCHISE BID
    # ==================================================

    active_franchise_bid = (
        detect_active_franchise_bid(
            snapshot,
            strategic_lookup,
        )
    )

    # ==================================================
    # PRESUPUESTO
    # ==================================================

    budget = (
        calculate_speculation_budget(
            snapshot=
                snapshot,

            solvency=
                solvency,

            active_franchise_bid=
                active_franchise_bid,
        )
    )

    # ==================================================
    # PLAYERS
    # ==================================================

    analyzed = []

    for player in strategic_board:

        trend = (
            trend_lookup.get(
                int(
                    player[
                        "id"
                    ]
                )
            )
        )

        analyzed.append(
            analyze_speculation_player(
                player=
                    player,

                trend=
                    trend,
            )
        )

    # ==================================================
    # COMPRAS
    # ==================================================

    buy_candidates = [
        player

        for player in analyzed

        if player[
            "speculation_action"
        ]
        in {
            "BUY_SPECULATION",
            "WATCH_BUY",
        }
    ]

    buy_candidates.sort(
        key=lambda player: (
            player[
                "speculation_score"
            ],
            player[
                "history_confidence"
            ][
                "confidence"
            ],
            player[
                "trend_score"
            ],
            player[
                "price_increment_percent"
            ],
        ),
        reverse=True,
    )

    # ==================================================
    # OWNED
    # ==================================================

    owned = [
        player

        for player in analyzed

        if player[
            "ownership_state"
        ]
        == "MI_EQUIPO"
    ]

    hold_candidates = [
        player

        for player in owned

        if player[
            "speculation_action"
        ]
        in {
            "HOLD_SPECULATION",
            "HOLD",
        }
    ]

    hold_candidates.sort(
        key=lambda player:
            player[
                "speculation_score"
            ],
        reverse=True,
    )

    sell_candidates = [
        player

        for player in owned

        if player[
            "speculation_action"
        ]
        in {
            "SELL_SPECULATION",
            "SELL_RISK",
            "WATCH_SELL",
        }
    ]

    sell_candidates.sort(
        key=lambda player: (
            player[
                "speculation_score"
            ],
            player[
                "price_increment"
            ],
        )
    )

    # ==================================================
    # WATCHLIST
    # ==================================================

    watchlist = [
        player

        for player in analyzed

        if player[
            "speculation_action"
        ]
        in {
            "WATCHLIST_HIGH",
            "WATCHLIST",
        }
    ]

    watchlist.sort(
        key=lambda player: (
            player[
                "speculation_score"
            ],
            player[
                "history_confidence"
            ][
                "confidence"
            ],
        ),
        reverse=True,
    )

    # ==================================================
    # EJECUTABLE BUYS
    # ==================================================

    executable_buys = []

    if budget[
        "enabled"
    ]:

        remaining_budget = int(
            budget[
                "total_budget"
            ]
        )

        for player in buy_candidates:

            if player[
                "speculation_action"
            ] != "BUY_SPECULATION":

                continue

            price = int(
                player.get(
                    "price",
                    0,
                )
                or 0
            )

            if price <= 0:
                continue

            if (
                price
                > budget[
                    "single_operation_limit"
                ]
            ):
                continue

            if price > remaining_budget:
                continue

            executable_buys.append(
                player
            )

            remaining_budget -= price

    return {
        "solvency":
            solvency,

        "active_franchise_bid":
            active_franchise_bid,

        "budget":
            budget,

        "players":
            analyzed,

        "buy_candidates":
            buy_candidates,

        "executable_buys":
            executable_buys,

        "owned":
            owned,

        "sell_candidates":
            sell_candidates,

        "hold_candidates":
            hold_candidates,

        "watchlist":
            watchlist,
    }