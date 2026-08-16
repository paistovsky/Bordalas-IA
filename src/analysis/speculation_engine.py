from src.intelligence.jornada_perfecta_market_intelligence import (
    intelligence_by_biwenger_id,
    refresh_jp_market_intelligence,
)

from src.analysis.market_trend_engine import (
    build_market_trend_board,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.analysis.bid_exposure_engine import (
    apply_exposure_to_budget,
    build_bid_exposure,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ======================================================
# CONFIGURACIÃƒâ€œN
# ======================================================


MAX_SPECULATION_BUDGET_PERCENT = 0.15
MAX_SINGLE_SPECULATION_PERCENT = 0.40

# Cuando el saldo es negativo no usamos todo el margen de
# MAX_SAFE_DEBT. Conservamos parte como colchon adicional.
MAX_DEBT_SPECULATION_PERCENT = 0.60

# Evita micro-operaciones irrelevantes.
MIN_SPECULATION_BUDGET = 150_000

BUY_THRESHOLD = 72
WATCH_THRESHOLD = 55
HOLD_THRESHOLD = 55
SELL_THRESHOLD = 35

FRANCHISE_THRESHOLD = 70

# Jornada Perfecta Market Intelligence no sustituye a nuestras
# señales internas: las confirma/corrige.
JP_MARKET_NEUTRAL_SCORE = 50.0
JP_MARKET_MAX_ADJUSTMENT = 14.0
JP_MARKET_WEIGHT = 0.38


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
# CONFIANZA HISTÃƒâ€œRICA
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
    jp_lookup: dict[int, dict] | None = None,
) -> dict:
    """
    Señal externa V4 basada en Jornada Perfecta Market Intelligence.

    El jp_market_score (0..100) se centra en 50:
        50 -> ajuste 0
        >50 -> bonus
        <50 -> penalizacion

    El ajuste esta capado para que JP ayude a decidir, pero no
    pueda sobreescribir por sí sola momentum, solvencia o riesgo.
    """
    if not jp_lookup:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "sources": [],
            "status": "NOT_CONNECTED",
            "jp_market_score": None,
            "jp_action": None,
        }

    player_id = player.get("id")

    try:
        player_id = int(player_id)
    except (TypeError, ValueError):
        player_id = None

    if player_id is None:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "sources": ["JORNADA_PERFECTA_MARKET"],
            "status": "NO_PLAYER_ID",
            "jp_market_score": None,
            "jp_action": None,
        }

    jp = jp_lookup.get(player_id)

    if jp is None:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "sources": ["JORNADA_PERFECTA_MARKET"],
            "status": "NO_MATCH",
            "jp_market_score": None,
            "jp_action": None,
        }

    jp_score = float(
        jp.get("jp_market_score", JP_MARKET_NEUTRAL_SCORE)
        or JP_MARKET_NEUTRAL_SCORE
    )

    centered = jp_score - JP_MARKET_NEUTRAL_SCORE

    adjustment = centered * JP_MARKET_WEIGHT
    adjustment = max(
        -JP_MARKET_MAX_ADJUSTMENT,
        min(
            JP_MARKET_MAX_ADJUSTMENT,
            adjustment,
        ),
    )

    # Señales de disponibilidad/caída reciente reducen confianza.
    availability_score = float(
        jp.get("availability_score", 100)
        or 0
    )

    confidence = 100.0

    if availability_score < 50:
        confidence = 75.0

    if jp.get("outlier"):
        confidence = min(
            confidence,
            70.0,
        )

    return {
        "score": round(adjustment, 2),
        "confidence": round(confidence, 1),
        "sources": ["JORNADA_PERFECTA_MARKET"],
        "status": "CONNECTED",
        "jp_market_score": round(jp_score, 2),
        "jp_action": jp.get("intelligence_action"),
        "jp_market_score_raw": jp.get("market_score"),
        "jp_tip": jp.get("tip"),
        "jp_tip_desc": jp.get("tip_desc"),
        "jp_editorial_score": jp.get("editorial_score"),
        "jp_editorial": jp.get("latest_relevant_editorial"),
        "jp_daily_returns_pct": jp.get("daily_returns_pct"),
        "jp_returns_pct": jp.get("returns_pct"),
        "jp_outlier": jp.get("outlier", False),
        "jp_outlier_reasons": jp.get("outlier_reasons", []),
        "jp_availability_score": jp.get("availability_score"),
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
# COMPONENTE HISTÃƒâ€œRICO
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
    jp_lookup: dict[int, dict] | None = None,
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
            player,
            jp_lookup=jp_lookup,
        )
    )

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
# DECISIÃƒâ€œN
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
        # histÃƒÂ³rico para justificar riesgo.
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
        # con una simple fotografÃƒÂ­a.
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
    jp_lookup: dict[int, dict] | None = None,
) -> dict:

    analysis = (
        calculate_speculation_score(
            player=
                player,

            trend=
                trend,

            jp_lookup=
                jp_lookup,
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
    """
    Presupuesto especulativo V3.

    Ya NO aplica:
        balance < 0 -> bloqueo absoluto.

    Con saldo negativo solo permite especular si:
    - SOLVENCY_GUARANTEE esta garantizada;
    - MAX_SAFE_DEBT deja margen adicional;
    - la ventana temporal de deuda sigue abierta;
    - no estamos en Hard Safety;
    - no hay puja Franchise activa.

    Incluso entonces solo usa una fraccion del headroom.
    """

    status = get_market_status(
        snapshot
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

    guarantee = (
        solvency.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    safe_debt = (
        solvency.get(
            "max_safe_debt",
            {},
        )
        or {}
    )

    temporary_debt = (
        solvency.get(
            "temporary_debt",
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
            "enabled": False,
            "total_budget": 0,
            "single_operation_limit": 0,
            "reason": (
                "Existe una puja Franchise activa "
                f"por {player['name']}. "
                "La especulacion queda congelada "
                "hasta la resolucion del mercado."
            ),
            "blocked_by": "FRANCHISE_ACTIVE_BID",
            "balance": balance,
            "mode": "BLOCKED",
        }

    # ==================================================
    # HARD SAFETY
    # ==================================================

    if hard_safety.get(
        "active",
        False,
    ):

        return {
            "enabled": False,
            "total_budget": 0,
            "single_operation_limit": 0,
            "reason": "Hard Safety activo.",
            "blocked_by": "HARD_SAFETY",
            "balance": balance,
            "mode": "BLOCKED",
        }

    # ==================================================
    # SALDO NEGATIVO: DEUDA CONTROLADA
    # ==================================================

    if balance < 0:

        guaranteed = bool(
            guarantee.get(
                "guaranteed",
                False,
            )
        )

        headroom = int(
            safe_debt.get(
                "additional_debt_headroom",
                0,
            )
            or 0
        )

        debt_window_open = bool(
            safe_debt.get(
                "debt_window_open",
                False,
            )
        )

        debt_allowed = bool(
            temporary_debt.get(
                "allowed",
                False,
            )
        )

        if not guaranteed:

            return {
                "enabled": False,
                "total_budget": 0,
                "single_operation_limit": 0,
                "reason": (
                    "Saldo negativo y SOLVENCY_GUARANTEE "
                    "no esta garantizada."
                ),
                "blocked_by": "SOLVENCY_NOT_GUARANTEED",
                "balance": balance,
                "mode": "DEBT",
                "safe_debt_headroom": headroom,
            }

        if (
            not debt_window_open
            or not debt_allowed
        ):

            return {
                "enabled": False,
                "total_budget": 0,
                "single_operation_limit": 0,
                "reason": (
                    "Existe garantia de solvencia, pero "
                    "la ventana temporal no permite nueva deuda."
                ),
                "blocked_by": "DEBT_WINDOW_CLOSED",
                "balance": balance,
                "mode": "DEBT",
                "safe_debt_headroom": headroom,
            }

        if headroom <= 0:

            return {
                "enabled": False,
                "total_budget": 0,
                "single_operation_limit": 0,
                "reason": (
                    "MAX_SAFE_DEBT no deja margen "
                    "para deuda especulativa adicional."
                ),
                "blocked_by": "NO_SAFE_DEBT_HEADROOM",
                "balance": balance,
                "mode": "DEBT",
                "safe_debt_headroom": 0,
            }

        total_budget = int(
            headroom
            * MAX_DEBT_SPECULATION_PERCENT
        )

        gross_budget = total_budget

        # Nunca superar la capacidad real de puja de Biwenger.
        if maximum_bid > 0:
            total_budget = min(
                total_budget,
                maximum_bid,
            )

        single_limit = int(
            total_budget
            * MAX_SINGLE_SPECULATION_PERCENT
        )

        if total_budget < MIN_SPECULATION_BUDGET:

            return {
                "enabled": False,
                "total_budget": 0,
                "single_operation_limit": 0,
                "raw_authorized_budget": total_budget,
                "reason": (
                    "Hay margen de deuda segura, pero es "
                    "demasiado pequeno para una operacion "
                    "especulativa relevante."
                ),
                "blocked_by": "LOW_SAFE_DEBT_HEADROOM",
                "balance": balance,
                "mode": "DEBT",
                "safe_debt_headroom": headroom,
            }

        return {
            "enabled": True,
            "total_budget": total_budget,
            "gross_budget": gross_budget,
            "maximum_bid": maximum_bid,
            "single_operation_limit": single_limit,
            "reason": (
                "Saldo negativo permitido: SOLVENCY_GUARANTEE "
                "esta cubierta y existe margen dentro de "
                "MAX_SAFE_DEBT."
            ),
            "blocked_by": None,
            "balance": balance,
            "mode": "DEBT",
            "safe_debt_headroom": headroom,
            "guarantee_state": guarantee.get(
                "state"
            ),
        }

    # ==================================================
    # SALDO POSITIVO
    # ==================================================

    usable_capital = min(
        max(balance, 0),
        maximum_bid,
    )

    cash_budget = int(
        usable_capital
        * MAX_SPECULATION_BUDGET_PERCENT
    )

    # El acantilado.
    #
    # Esta rama solo miraba la caja. Con saldo +239.968 y
    # 10.719.800 de margen de deuda seguro, el presupuesto salia
    # 35.995 y la especulacion quedaba bloqueada por
    # LOW_LIQUIDITY. Con saldo -1 EUR, la rama de deuda daba
    # 6.431.880.
    #
    # Un euro de diferencia en el saldo cambiaba el presupuesto en
    # seis millones y medio, y en la direccion equivocada: tener
    # dinero salia peor que no tenerlo.
    #
    # El margen de deuda no depende del signo del saldo. Se
    # calcula como max_total_debt - current_debt, y con saldo
    # positivo current_debt es cero, asi que no hay doble conteo:
    # son dos bolsillos distintos. Lo que si es un techo real es
    # maximumBid, y se respeta abajo.
    #
    # Las condiciones para usar deuda son EXACTAMENTE las mismas
    # que exige la rama de saldo negativo. No se relaja nada.

    guaranteed = bool(
        guarantee.get(
            "guaranteed",
            False,
        )
    )

    headroom = int(
        safe_debt.get(
            "additional_debt_headroom",
            0,
        )
        or 0
    )

    debt_window_open = bool(
        safe_debt.get(
            "debt_window_open",
            False,
        )
    )

    debt_allowed = bool(
        temporary_debt.get(
            "allowed",
            False,
        )
    )

    debt_usable = bool(
        guaranteed
        and debt_window_open
        and debt_allowed
        and headroom > 0
    )

    debt_budget = (
        int(headroom * MAX_DEBT_SPECULATION_PERCENT)
        if debt_usable
        else 0
    )

    if not debt_usable:

        if not guaranteed:
            debt_reason = "SOLVENCY_GUARANTEE no esta garantizada."

        elif not debt_window_open:
            debt_reason = "La ventana de deuda segura esta cerrada."

        elif not debt_allowed:
            debt_reason = "La ventana temporal no permite nueva deuda."

        else:
            debt_reason = "MAX_SAFE_DEBT no deja margen adicional."

    else:
        debt_reason = None

    total_budget = cash_budget + debt_budget

    # Presupuesto bruto: lo que autoriza nuestro modelo antes de
    # chocar con el techo de Biwenger. Se conserva porque el
    # contador de exposicion lo necesita: maximum_bid YA viene
    # descontado de las pujas vivas y restarlas otra vez seria
    # contarlas dos veces.
    gross_budget = total_budget

    # Nunca superar la capacidad real de puja de Biwenger.
    if maximum_bid > 0:
        total_budget = min(
            total_budget,
            maximum_bid,
        )

    single_limit = int(
        total_budget
        * MAX_SINGLE_SPECULATION_PERCENT
    )

    if total_budget < MIN_SPECULATION_BUDGET:

        return {
            "enabled": False,
            "total_budget": 0,
            "single_operation_limit": 0,
            "raw_authorized_budget": total_budget,
            "cash_budget": cash_budget,
            "debt_budget": debt_budget,
            "safe_debt_headroom": headroom,
            "debt_unavailable_reason": debt_reason,
            "reason": (
                "No existe capacidad suficiente "
                "para especulacion actualmente."
                + (
                    f" El margen de deuda tampoco esta "
                    f"disponible: {debt_reason}"
                    if debt_reason
                    else ""
                )
            ),
            "blocked_by": "LOW_LIQUIDITY",
            "balance": balance,
            "mode": "CASH",
        }

    return {
        "enabled": True,
        "total_budget": total_budget,
        "gross_budget": gross_budget,
        "maximum_bid": maximum_bid,
        "single_operation_limit": single_limit,
        "cash_budget": cash_budget,
        "debt_budget": debt_budget,
        "safe_debt_headroom": headroom,
        "debt_unavailable_reason": debt_reason,
        "reason": (
            "Existe margen de liquidez para "
            "operaciones especulativas."
            + (
                f" Incluye {debt_budget:,} EUR de deuda "
                f"segura dentro de MAX_SAFE_DEBT."
                if debt_budget > 0
                else ""
            )
        ).replace(",", "."),
        "blocked_by": None,
        "balance": balance,
        "mode": (
            "CASH_AND_DEBT"
            if debt_budget > 0
            else "CASH"
        ),
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
    # JORNADA PERFECTA MARKET INTELLIGENCE
    # ==================================================

    jp_payload = (
        refresh_jp_market_intelligence(
            force_provider_refresh=False,
        )
    )

    jp_lookup = (
        intelligence_by_biwenger_id(
            jp_payload
        )
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

    # Descontar lo ya comprometido en pujas vivas de ciclos
    # anteriores. Sin esto, cada ciclo cree tener el presupuesto
    # entero y se pueden acumular mas compromisos de los que hay
    # dinero para pagar.
    bid_exposure = build_bid_exposure(snapshot)

    budget = apply_exposure_to_budget(
        budget,
        bid_exposure,
    )

    # ==================================================
    # PLAYERS
    # ==================================================

    analyzed = []

    jp_matches = 0

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

        analyzed_player = (
            analyze_speculation_player(
                player=
                    player,

                trend=
                    trend,

                jp_lookup=
                    jp_lookup,
            )
        )

        if (
            analyzed_player
            .get(
                "external_signal",
                {},
            )
            .get(
                "status"
            )
            == "CONNECTED"
        ):
            jp_matches += 1

        analyzed.append(
            analyzed_player
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
            (
                player
                .get(
                    "external_signal",
                    {},
                )
                .get(
                    "jp_market_score"
                )
                or 0
            ),
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

        # Lo que queda, no lo que habia.
        #
        # Una puja de un ciclo anterior sigue viva y sigue sin
        # descontar saldo, asi que sin esto cada ciclo volvia a
        # partir del presupuesto entero.
        remaining_budget = int(
            budget.get(
                "available_budget",
                budget["total_budget"],
            )
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

        "bid_exposure":
            bid_exposure,

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

        "jp_market_intelligence": {
            "provider_status":
                jp_payload.get(
                    "provider_status"
                ),

            "updated_at":
                jp_payload.get(
                    "updated_at"
                ),

            "age_hours":
                jp_payload.get(
                    "age_hours"
                ),

            "players":
                jp_payload.get(
                    "player_count",
                    0,
                ),

            "matched_strategic_players":
                jp_matches,

            "lookup_size":
                len(
                    jp_lookup
                ),
        },
    }

