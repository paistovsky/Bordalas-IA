from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta


OBSERVER_ONLY = True

FRANCHISE_NEVER_SELL_THRESHOLD = 70.0
DIRECT_RIVAL_THREAT_THRESHOLD = 60.0
VERY_HIGH_RIVAL_THREAT_THRESHOLD = 80.0
POINTS_GAP_DIRECT_THRESHOLD = 50

# Ventana real de refresco de Computer en hora local.
# El ultimo ciclo util es el refresh de 05:00-07:00 del mismo dia
# en que empieza la jornada.
COMPUTER_REFRESH_START_HOUR = 5
COMPUTER_REFRESH_END_HOUR = 7

# Una oferta excepcional puede justificar asumir un hueco temporal
# en el XI. No es una autorizacion LIVE: V1.2 sigue siendo observer.
CRAZY_OFFER_MIN_MARKET_MULTIPLIER = 1.75

ROUND_TO = 10_000


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


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


def round_money(value: float | int) -> int:
    return int(
        round(
            float(value) / ROUND_TO
        )
        * ROUND_TO
    )


# ============================================================
# RIVAL
# ============================================================


def build_manager_lookup(
    rival_intelligence: dict | None,
) -> dict[int, dict]:

    intelligence = rival_intelligence or {}
    managers = intelligence.get("managers", []) or []

    result: dict[int, dict] = {}

    for manager in managers:

        user_id = safe_int(
            manager.get(
                "user_id"
            )
        )

        if user_id > 0:
            result[user_id] = manager

    return result


def find_our_manager(
    rival_intelligence: dict | None,
) -> dict | None:

    intelligence = rival_intelligence or {}

    for manager in intelligence.get(
        "managers",
        [],
    ) or []:

        if manager.get(
            "threat_level"
        ) == "US":

            return manager

    return None


def classify_rival_context(
    *,
    rival_user_id: int | None,
    rival_intelligence: dict | None,
) -> dict:
    """
    Rival directo dinamico:
    - threat_score >= 60, o
    - distancia de puntos <= 50 cuando la clasificacion ya discrimina.
    """

    rival_user_id = safe_int(
        rival_user_id
    )

    empty = {
        "available":
            False,

        "user_id":
            (
                rival_user_id
                if rival_user_id > 0
                else None
            ),

        "name":
            None,

        "threat_score":
            0.0,

        "threat_level":
            "UNKNOWN",

        "points":
            0,

        "points_gap":
            None,

        "direct_rival":
            False,

        "balance":
            0,

        "maximum_bid":
            0,

        "roster_value":
            0,

        "market_activity":
            "UNKNOWN",

        "profile":
            "UNKNOWN",
    }

    if rival_user_id <= 0:
        return empty

    lookup = (
        build_manager_lookup(
            rival_intelligence
        )
    )

    rival = lookup.get(
        rival_user_id
    )

    if rival is None:
        return empty

    threat_score = safe_float(
        rival.get(
            "threat_score"
        )
    )

    rival_points = safe_int(
        rival.get(
            "points"
        )
    )

    our_manager = (
        find_our_manager(
            rival_intelligence
        )
    )

    points_gap = None
    points_direct = False

    if our_manager is not None:

        ranking_active = bool(
            our_manager.get(
                "points_rank"
            )
            is not None
            or
            rival.get(
                "points_rank"
            )
            is not None
        )

        if ranking_active:

            our_points = safe_int(
                our_manager.get(
                    "points"
                )
            )

            points_gap = abs(
                our_points
                - rival_points
            )

            points_direct = (
                points_gap
                <= POINTS_GAP_DIRECT_THRESHOLD
            )

    direct_rival = bool(
        threat_score
        >= DIRECT_RIVAL_THREAT_THRESHOLD
        or
        points_direct
    )

    return {
        "available":
            True,

        "user_id":
            rival_user_id,

        "name":
            rival.get(
                "name"
            ),

        "threat_score":
            round(
                threat_score,
                1,
            ),

        "threat_level":
            str(
                rival.get(
                    "threat_level"
                )
                or
                "UNKNOWN"
            ),

        "points":
            rival_points,

        "points_gap":
            points_gap,

        "direct_rival":
            direct_rival,

        "balance":
            safe_int(
                rival.get(
                    "balance"
                )
            ),

        "maximum_bid":
            safe_int(
                rival.get(
                    "maximum_bid"
                )
            ),

        "roster_value":
            safe_int(
                rival.get(
                    "roster_value"
                )
            ),

        "market_activity":
            rival.get(
                "market_activity",
                "UNKNOWN",
            ),

        "profile":
            rival.get(
                "profile",
                "UNKNOWN",
            ),
    }


# ============================================================
# DEADLINE / VENTANA DE REEMPLAZO
# ============================================================


def extract_deadline_datetime(
    deadline_context: dict | None,
) -> datetime | None:
    """
    Intenta recuperar el kickoff/deadline real como datetime local naive.
    Acepta varias estructuras ya usadas por Bordalas IA.
    """

    deadline_context = (
        deadline_context
        or {}
    )

    direct_candidates = [
        deadline_context.get("first_kickoff"),
        deadline_context.get("real_deadline"),
        (
            deadline_context.get(
                "calendar",
                {},
            )
            or {}
        ).get("first_kickoff"),
        (
            deadline_context.get(
                "calendar",
                {},
            )
            or {}
        ).get("real_deadline"),
    ]

    for value in direct_candidates:

        if value is None:
            continue

        if isinstance(value, datetime):
            return value.replace(tzinfo=None)

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(
                    float(value)
                )
            except (
                OSError,
                OverflowError,
                ValueError,
            ):
                pass

        if isinstance(value, str):
            text = value.strip()

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"

            try:
                parsed = datetime.fromisoformat(text)

                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone().replace(
                        tzinfo=None
                    )

                return parsed
            except ValueError:
                pass

    return None


def extract_hours_to_deadline(
    deadline_context: dict | None,
    now: datetime | None = None,
) -> float | None:

    deadline_dt = extract_deadline_datetime(
        deadline_context
    )

    if deadline_dt is not None:

        now = (
            now
            or datetime.now()
        )

        return max(
            (
                deadline_dt
                -
                now.replace(
                    tzinfo=None
                )
            ).total_seconds()
            / 3600.0,
            0.0,
        )

    deadline_context = (
        deadline_context
        or {}
    )

    candidates = [
        deadline_context.get(
            "hours_to_deadline"
        ),
    ]

    seconds_candidates = [
        deadline_context.get(
            "seconds_to_deadline"
        ),
        (
            deadline_context.get(
                "calendar",
                {},
            )
            or {}
        ).get(
            "seconds_to_lineup_lock"
        ),
    ]

    for value in candidates:

        if value is None:
            continue

        try:
            return max(
                float(value),
                0.0,
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

    for value in seconds_candidates:

        if value is None:
            continue

        try:
            return max(
                float(value) / 3600.0,
                0.0,
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

    return None


def calculate_computer_cycle_window(
    *,
    deadline_context: dict | None,
    now: datetime | None = None,
) -> dict:
    """
    El refresh de Computer ocurre cada manana entre 05:00 y 07:00.

    Para la jornada actual:
    - el ultimo ciclo util es la ventana 05:00-07:00 del mismo dia
      del primer kickoff;
    - antes de las 05:00 ese ultimo ciclo sigue pendiente;
    - entre 05:00 y 07:00 estamos dentro de la ventana de reset;
    - despues de las 07:00 se considera pasado.
    """

    now = (
        now
        or datetime.now()
    ).replace(
        tzinfo=None
    )

    kickoff = extract_deadline_datetime(
        deadline_context
    )

    if kickoff is None:

        return {
            "available": False,
            "kickoff": None,
            "refresh_start": None,
            "refresh_end": None,
            "hours_to_refresh_start": None,
            "hours_to_refresh_end": None,
            "cycle_state": "UNKNOWN",
            "last_useful_cycle_passed": False,
        }

    kickoff = kickoff.replace(
        tzinfo=None
    )

    refresh_start = kickoff.replace(
        hour=COMPUTER_REFRESH_START_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )

    refresh_end = kickoff.replace(
        hour=COMPUTER_REFRESH_END_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )

    # Si el kickoff fuese excepcionalmente antes de las 07:00,
    # usamos la ultima ventana completa anterior al kickoff.
    if kickoff <= refresh_start:
        refresh_start -= timedelta(days=1)
        refresh_end -= timedelta(days=1)

    elif kickoff < refresh_end:
        # Jornada dentro de la propia ventana: conservadoramente,
        # el ultimo ciclo seguro es el dia anterior.
        refresh_start -= timedelta(days=1)
        refresh_end -= timedelta(days=1)

    hours_to_start = (
        refresh_start
        -
        now
    ).total_seconds() / 3600.0

    hours_to_end = (
        refresh_end
        -
        now
    ).total_seconds() / 3600.0

    if now < refresh_start:
        cycle_state = "BEFORE_LAST_USEFUL_WINDOW"

    elif refresh_start <= now <= refresh_end:
        cycle_state = "IN_LAST_USEFUL_WINDOW"

    else:
        cycle_state = "LAST_USEFUL_WINDOW_PASSED"

    return {
        "available": True,
        "kickoff": kickoff.isoformat(timespec="seconds"),
        "refresh_start": refresh_start.isoformat(timespec="seconds"),
        "refresh_end": refresh_end.isoformat(timespec="seconds"),
        "hours_to_refresh_start": round(hours_to_start, 2),
        "hours_to_refresh_end": round(hours_to_end, 2),
        "cycle_state": cycle_state,
        "last_useful_cycle_passed": (
            cycle_state
            ==
            "LAST_USEFUL_WINDOW_PASSED"
        ),
    }


def classify_replacement_window(
    *,
    deadline_context: dict | None,
    in_lineup: bool,
    replacement_status: str = "UNKNOWN",
    now: datetime | None = None,
) -> dict:
    """
    Riesgo de reemplazo basado en la ventana real 05:00-07:00
    de Computer del dia del kickoff.
    """

    replacement_status = str(
        replacement_status
        or
        "UNKNOWN"
    ).upper()

    hours_to_deadline = (
        extract_hours_to_deadline(
            deadline_context,
            now=now,
        )
    )

    computer_cycle = (
        calculate_computer_cycle_window(
            deadline_context=
                deadline_context,

            now=
                now,
        )
    )

    if computer_cycle.get(
        "available"
    ):

        cycle_state = (
            computer_cycle[
                "cycle_state"
            ]
        )

        hours_to_refresh_start = safe_float(
            computer_cycle.get(
                "hours_to_refresh_start"
            )
        )

        if cycle_state == "LAST_USEFUL_WINDOW_PASSED":

            base_risk = 95.0
            window = "LAST_USEFUL_CYCLE_PASSED"

        elif cycle_state == "IN_LAST_USEFUL_WINDOW":

            base_risk = 90.0
            window = "COMPUTER_RESET_WINDOW"

        elif hours_to_refresh_start >= 120:

            base_risk = 10.0
            window = "WIDE"

        elif hours_to_refresh_start >= 72:

            base_risk = 20.0
            window = "COMFORTABLE"

        elif hours_to_refresh_start >= 48:

            base_risk = 30.0
            window = "GOOD"

        elif hours_to_refresh_start >= 24:

            base_risk = 45.0
            window = "NARROWING"

        elif hours_to_refresh_start > 0:

            base_risk = 70.0
            window = "TIGHT"

        else:

            base_risk = 90.0
            window = "COMPUTER_RESET_WINDOW"

    else:

        # Fallback si el deadline engine no aporta datetime real.
        base_risk = 50.0
        window = "UNKNOWN"

    replacement_multiplier = {
        "NOT_NEEDED":
            0.10,

        "SECURED":
            0.15,

        "SECURED_BY_BENCH":
            0.15,

        "AVAILABLE":
            0.50,

        "AVAILABLE_ON_MARKET":
            0.50,

        "UNCERTAIN":
            0.85,

        "UNCERTAIN_ON_MARKET":
            0.85,

        "NONE":
            1.10,

        "UNKNOWN":
            0.75,
    }.get(
        replacement_status,
        0.75,
    )

    if not in_lineup:

        replacement_multiplier = min(
            replacement_multiplier,
            0.20,
        )

    risk = clamp(
        base_risk
        * replacement_multiplier
    )

    if risk >= 85:
        level = "CRITICAL"

    elif risk >= 65:
        level = "VERY_HIGH"

    elif risk >= 45:
        level = "HIGH"

    elif risk >= 25:
        level = "MEDIUM"

    else:
        level = "LOW"

    max_temporal_premium = (
        30.0
        if in_lineup
        else 5.0
    )

    temporal_sell_premium_percent = (
        risk
        / 100.0
        * max_temporal_premium
    )

    return {
        "hours_to_deadline":
            (
                round(
                    hours_to_deadline,
                    2,
                )
                if hours_to_deadline
                is not None
                else None
            ),

        "window":
            window,

        "replacement_status":
            replacement_status,

        "replacement_risk_score":
            round(
                risk,
                1,
            ),

        "replacement_risk_level":
            level,

        "temporal_sell_premium_percent":
            round(
                temporal_sell_premium_percent,
                2,
            ),

        "computer_cycle":
            computer_cycle,

        "last_useful_cycle_passed":
            bool(
                computer_cycle.get(
                    "last_useful_cycle_passed",
                    False,
                )
            ),
    }

# ============================================================
# SOLVENCIA PROPIA
# ============================================================


def calculate_solvency_sale_context(
    *,
    current_balance: int | None,
    amount: int,
) -> dict:

    if current_balance is None:

        return {
            "available":
                False,

            "balance":
                None,

            "deficit":
                None,

            "restores_solvency":
                False,

            "solvency_benefit_score":
                0.0,

            "solvency_discount_percent":
                0.0,

            "post_sale_balance":
                None,
        }

    balance = safe_int(
        current_balance
    )

    amount = safe_int(
        amount
    )

    post_sale_balance = (
        balance
        + amount
    )

    if balance >= 0:

        return {
            "available":
                True,

            "balance":
                balance,

            "deficit":
                0,

            "restores_solvency":
                True,

            "solvency_benefit_score":
                0.0,

            "solvency_discount_percent":
                0.0,

            "post_sale_balance":
                post_sale_balance,
        }

    deficit = abs(
        balance
    )

    coverage = (
        amount
        /
        max(
            deficit,
            1,
        )
    )

    benefit_score = clamp(
        coverage
        * 100.0
    )

    restores_solvency = (
        post_sale_balance
        >= 0
    )

    # Como saldo >=0 tiene prioridad absoluta, una venta que resuelve
    # solvencia puede reducir hasta 10 puntos porcentuales el precio
    # estrategico exigido. No elimina el coste competitivo.
    discount = (
        benefit_score
        / 100.0
        * 10.0
    )

    if restores_solvency:
        discount = max(
            discount,
            8.0,
        )

    return {
        "available":
            True,

        "balance":
            balance,

        "deficit":
            deficit,

        "restores_solvency":
            restores_solvency,

        "solvency_benefit_score":
            round(
                benefit_score,
                1,
            ),

        "solvency_discount_percent":
            round(
                min(
                    discount,
                    10.0,
                ),
                2,
            ),

        "post_sale_balance":
            post_sale_balance,
    }


# ============================================================
# VENTA A RIVAL
# ============================================================


def calculate_our_sale_cost_score(
    *,
    franchise_score: float,
    strategic_score: float,
    sale_score: float,
    speculation_score: float,
    in_lineup: bool,
    price_increment: int,
    sporting_cost_score: float = 0.0,
) -> float:
    """
    0..100. Cuanto mas alto, mas caro nos resulta desprendernos del jugador.
    """

    score = 25.0

    score += (
        clamp(
            franchise_score
        )
        * 0.30
    )

    score += (
        clamp(
            strategic_score
        )
        * 0.18
    )

    score += (
        (
            100.0
            -
            clamp(
                sale_score
            )
        )
        * 0.12
    )

    # Valor especulativo futuro explicito.
    score += (
        clamp(
            speculation_score
        )
        * 0.18
    )

    if speculation_score >= 85:
        score += 8.0

    elif speculation_score >= 70:
        score += 4.0

    elif speculation_score <= 30:
        score -= 3.0

    if in_lineup:
        score += 15.0

    # V1.6: coste deportivo real derivado de reconstruir el XI sin el jugador.
    # Hasta 20 puntos adicionales de coste interno.
    score += (
        clamp(
            sporting_cost_score
        )
        * 0.20
    )

    if price_increment >= 100_000:
        score += 8.0

    elif price_increment > 0:
        score += 4.0

    elif price_increment < 0:
        score -= 4.0

    return round(
        clamp(
            score
        ),
        1,
    )


def calculate_rival_reinforcement_score(
    *,
    rival_context: dict,
    player_quality_score: float,
    speculation_score: float,
    in_our_lineup: bool,
) -> float:
    """
    Deportivo + amenaza + potencial especulativo.
    """

    threat = safe_float(
        rival_context.get(
            "threat_score"
        )
    )

    quality = clamp(
        player_quality_score
    )

    speculation = clamp(
        speculation_score
    )

    score = (
        quality
        * 0.45
        +
        threat
        * 0.30
        +
        speculation
        * 0.25
    )

    if speculation >= 85:
        score += 8.0

    elif speculation >= 70:
        score += 4.0

    if rival_context.get(
        "direct_rival"
    ):
        score += 7.0

    if in_our_lineup:
        score += 3.0

    return round(
        clamp(
            score
        ),
        1,
    )


def calculate_base_sell_price(
    *,
    market_value: int,
    our_sale_cost_score: float,
    price_increment: int,
) -> int:

    market_value = max(
        safe_int(
            market_value
        ),
        0,
    )

    if market_value <= 0:
        return 0

    internal_premium = (
        clamp(
            our_sale_cost_score
        )
        /
        100.0
        *
        0.25
    )

    trend_premium = 0.0

    if price_increment >= 100_000:
        trend_premium = 0.04

    elif price_increment > 0:
        trend_premium = 0.02

    return round_money(
        market_value
        *
        (
            1.0
            +
            internal_premium
            +
            trend_premium
        )
    )


def calculate_competitive_sale_premium_percent(
    *,
    rival_context: dict,
    rival_reinforcement_score: float,
) -> float:

    threat = safe_float(
        rival_context.get(
            "threat_score"
        )
    )

    premium = (
        threat
        * 0.10
    )

    premium += (
        clamp(
            rival_reinforcement_score
        )
        * 0.08
    )

    if rival_context.get(
        "direct_rival"
    ):
        premium += 5.0

    if (
        threat
        >= VERY_HIGH_RIVAL_THREAT_THRESHOLD
    ):
        premium += 2.0

    return round(
        min(
            max(
                premium,
                0.0,
            ),
            22.0,
        ),
        2,
    )


def evaluate_sale_to_rival(
    *,
    amount: int,
    market_value: int,
    rival_user_id: int | None,
    rival_intelligence: dict | None,
    franchise_score: float = 0.0,
    strategic_score: float = 0.0,
    sale_score: float = 50.0,
    speculation_score: float = 50.0,
    in_lineup: bool = False,
    price_increment: int = 0,
    current_balance: int | None = None,
    deadline_context: dict | None = None,
    replacement_status: str = "UNKNOWN",
    empty_slot_penalty_points: int | None = None,
    sporting_opportunity_cost: dict | None = None,
) -> dict:
    """
    V1.2 observer.

    Posibles decisiones:
    - NEVER_SELL
    - ACCEPT_NOW
    - ACCEPT_SACRIFICE_LINEUP
    - COUNTER_OFFER
    - HOLD_OFFER

    Importante:
    ACCEPT_SACRIFICE_LINEUP NO ejecuta nada. Solo indica que una
    oferta extraordinaria podria justificar asumir un hueco temporal
    en el XI.
    """

    amount = safe_int(
        amount
    )

    market_value = safe_int(
        market_value
    )

    rival_context = (
        classify_rival_context(
            rival_user_id=
                rival_user_id,

            rival_intelligence=
                rival_intelligence,
        )
    )

    replacement = (
        classify_replacement_window(
            deadline_context=
                deadline_context,

            in_lineup=
                in_lineup,

            replacement_status=
                replacement_status,
        )
    )

    solvency = (
        calculate_solvency_sale_context(
            current_balance=
                current_balance,

            amount=
                amount,
        )
    )

    our_sale_cost_score = (
        calculate_our_sale_cost_score(
            franchise_score=
                franchise_score,

            strategic_score=
                strategic_score,

            sale_score=
                sale_score,

            speculation_score=
                speculation_score,

            in_lineup=
                in_lineup,

            price_increment=
                price_increment,

            sporting_cost_score=
                safe_float(
                    (
                        sporting_opportunity_cost
                        or {}
                    ).get(
                        "sporting_cost_score"
                    )
                ),
        )
    )

    player_quality_score = max(
        clamp(
            franchise_score
        ),
        clamp(
            strategic_score
        ),
        (
            100.0
            -
            clamp(
                sale_score
            )
        ),
    )

    rival_reinforcement_score = (
        calculate_rival_reinforcement_score(
            rival_context=
                rival_context,

            player_quality_score=
                player_quality_score,

            speculation_score=
                speculation_score,

            in_our_lineup=
                in_lineup,
        )
    )

    base_sell_price = (
        calculate_base_sell_price(
            market_value=
                market_value,

            our_sale_cost_score=
                our_sale_cost_score,

            price_increment=
                price_increment,
        )
    )

    competitive_premium_percent = (
        calculate_competitive_sale_premium_percent(
            rival_context=
                rival_context,

            rival_reinforcement_score=
                rival_reinforcement_score,
        )
        if rival_context.get(
            "available"
        )
        else 0.0
    )

    temporal_premium_percent = safe_float(
        replacement.get(
            "temporal_sell_premium_percent"
        )
    )

    sporting_context = (
        sporting_opportunity_cost
        or {}
    )

    sporting_cost_score = safe_float(
        sporting_context.get(
            "sporting_cost_score"
        )
    )

    # Hasta +18% por coste deportivo real. La solvencia sigue teniendo
    # prioridad mediante su descuento, pero ya no ignoramos la caída del XI.
    sporting_premium_percent = round(
        clamp(
            sporting_cost_score
        )
        / 100.0
        * 18.0,
        2,
    )

    solvency_discount_percent = safe_float(
        solvency.get(
            "solvency_discount_percent"
        )
    )

    total_adjustment_percent = (
        competitive_premium_percent
        +
        temporal_premium_percent
        +
        sporting_premium_percent
        -
        solvency_discount_percent
    )

    total_adjustment_percent = max(
        total_adjustment_percent,
        0.0,
    )

    strategic_sell_price = (
        round_money(
            base_sell_price
            *
            (
                1.0
                +
                total_adjustment_percent
                /
                100.0
            )
        )
        if base_sell_price > 0
        else 0
    )

    market_multiplier = (
        amount
        /
        market_value
        if market_value > 0
        else 0.0
    )

    sacrifice_risk = bool(
        in_lineup
        and
        replacement.get(
            "replacement_risk_score",
            0,
        )
        >= 60
        and
        replacement.get(
            "replacement_status"
        )
        not in {
            "SECURED",
            "SECURED_BY_BENCH",
            "NOT_NEEDED",
        }
    )

    crazy_offer = bool(
        market_value > 0
        and
        market_multiplier
        >= CRAZY_OFFER_MIN_MARKET_MULTIPLIER
    )

    reasons: list[str] = []

    if (
        franchise_score
        >= FRANCHISE_NEVER_SELL_THRESHOLD
    ):

        decision = "NEVER_SELL"
        counter_amount = None

        reasons.append(
            "Jugador Franchise/NEVER_SELL: la negociacion queda bloqueada."
        )

    elif market_value <= 0:

        decision = "HOLD_OFFER"
        counter_amount = None

        reasons.append(
            "No existe valor de mercado fiable para fijar un precio estrategico."
        )

    elif (
        sacrifice_risk
        and
        crazy_offer
        and
        amount
        >= strategic_sell_price
    ):

        decision = (
            "ACCEPT_SACRIFICE_LINEUP"
        )

        counter_amount = None

        reasons.append(
            "Oferta extraordinaria: compensa el coste competitivo "
            "y el riesgo de asumir temporalmente un hueco en el XI."
        )

    elif (
        amount
        >= strategic_sell_price
    ):

        decision = "ACCEPT_NOW"
        counter_amount = None

        reasons.append(
            "La oferta alcanza el precio estrategico total."
        )

    else:

        # Cambio V1.2:
        # si existe un precio al que venderiamos, negociamos.
        # No rechazamos simplemente porque el comprador sea peligroso.
        decision = "COUNTER_OFFER"
        counter_amount = (
            strategic_sell_price
        )

        reasons.append(
            "La oferta actual no compensa todos los costes; "
            "Pepe propone el precio estrategico de venta."
        )

    if rival_context.get(
        "direct_rival"
    ):

        reasons.append(
            "Rival directo dinamico: SI."
        )

    if in_lineup:

        reasons.append(
            "El jugador forma parte del XI actual."
        )

    if sacrifice_risk:

        reasons.append(
            "Venderlo puede dejar un hueco competitivo sin reemplazo asegurado."
        )

    if replacement.get(
        "last_useful_cycle_passed"
    ):

        reasons.append(
            "La ultima ventana util de Computer (05:00-07:00) ya se considera pasada."
        )

    if solvency.get(
        "restores_solvency"
    ) and safe_int(
        solvency.get(
            "balance"
        )
    ) < 0:

        reasons.append(
            "La operacion devolveria a Pepe a saldo >= 0."
        )

    if (
        empty_slot_penalty_points
        is None
    ):

        reasons.append(
            "Penalizacion exacta por hueco no hardcodeada: pendiente de validar configuracion de liga."
        )

    else:

        reasons.append(
            f"Penalizacion configurada por hueco: "
            f"{safe_int(empty_slot_penalty_points)} puntos."
        )

    reasons.append(
        f"Threat rival: "
        f"{safe_float(rival_context.get('threat_score')):.1f}/100."
    )

    reasons.append(
        f"Speculation jugador: "
        f"{clamp(speculation_score):.1f}/100."
    )

    reasons.append(
        f"Refuerzo rival estimado: "
        f"{rival_reinforcement_score:.1f}/100."
    )

    reasons.append(
        f"Riesgo reemplazo: "
        f"{safe_float(replacement.get('replacement_risk_score')):.1f}/100 "
        f"({replacement.get('replacement_risk_level')})."
    )

    return {
        "observer_only":
            OBSERVER_ONLY,

        "direction":
            "RIVAL_BUYS_FROM_US",

        "decision":
            decision,

        "amount":
            amount,

        "market_value":
            market_value,

        "market_multiplier":
            round(
                market_multiplier,
                3,
            ),

        "crazy_offer":
            crazy_offer,

        "base_sell_price":
            base_sell_price,

        "competitive_premium_percent":
            competitive_premium_percent,

        "temporal_premium_percent":
            round(
                temporal_premium_percent,
                2,
            ),

        "sporting_premium_percent":
            sporting_premium_percent,

        "sporting_cost_score":
            round(
                sporting_cost_score,
                1,
            ),

        "sporting_opportunity_cost":
            sporting_context,

        "solvency_discount_percent":
            round(
                solvency_discount_percent,
                2,
            ),

        "total_adjustment_percent":
            round(
                total_adjustment_percent,
                2,
            ),

        "strategic_sell_price":
            strategic_sell_price,

        "counter_amount":
            counter_amount,

        "our_sale_cost_score":
            our_sale_cost_score,

        "speculation_score":
            round(
                clamp(
                    speculation_score
                ),
                1,
            ),

        "rival_reinforcement_score":
            rival_reinforcement_score,

        "sacrifice_lineup_risk":
            sacrifice_risk,

        "empty_slot_penalty_points":
            (
                safe_int(
                    empty_slot_penalty_points
                )
                if empty_slot_penalty_points
                is not None
                else None
            ),

        "replacement":
            replacement,

        "solvency":
            solvency,

        "rival":
            rival_context,

        "reasons":
            reasons,
    }


# ============================================================
# COMPRA A RIVAL
# ============================================================


def calculate_purchase_value_score(
    *,
    player_score: float,
    lineup_need_score: float,
    speculation_score: float,
) -> float:

    return round(
        clamp(
            clamp(
                player_score
            )
            * 0.55
            +
            clamp(
                lineup_need_score
            )
            * 0.30
            +
            clamp(
                speculation_score
            )
            * 0.15
        ),
        1,
    )


def calculate_rival_damage_score(
    *,
    rival_context: dict,
    player_score: float,
) -> float:

    threat = safe_float(
        rival_context.get(
            "threat_score"
        )
    )

    score = (
        clamp(
            player_score
        )
        * 0.60
    )

    score += (
        threat
        * 0.25
    )

    if rival_context.get(
        "direct_rival"
    ):
        score += 10.0

    return round(
        clamp(
            score
        ),
        1,
    )


def calculate_liquidity_help_score(
    *,
    price: int,
    rival_context: dict,
) -> float:

    price = max(
        safe_int(
            price
        ),
        0,
    )

    balance = safe_int(
        rival_context.get(
            "balance"
        )
    )

    maximum_bid = max(
        safe_int(
            rival_context.get(
                "maximum_bid"
            )
        ),
        0,
    )

    if price <= 0:
        return 0.0

    score = 0.0

    if balance < 0:

        deficit = abs(
            balance
        )

        score += min(
            price
            /
            max(
                deficit,
                1,
            )
            *
            45.0,
            45.0,
        )

    if maximum_bid > 0:

        score += min(
            price
            /
            maximum_bid
            *
            30.0,
            30.0,
        )

    else:
        score += 10.0

    score += (
        safe_float(
            rival_context.get(
                "threat_score"
            )
        )
        * 0.15
    )

    return round(
        clamp(
            score
        ),
        1,
    )


def calculate_strategic_max_purchase_price(
    *,
    market_value: int,
    purchase_value_score: float,
    rival_damage_score: float,
    liquidity_help_score: float,
) -> int:

    market_value = max(
        safe_int(
            market_value
        ),
        0,
    )

    if market_value <= 0:
        return 0

    own_premium = (
        clamp(
            purchase_value_score
        )
        /
        100.0
        *
        0.20
    )

    damage_premium = (
        clamp(
            rival_damage_score
        )
        /
        100.0
        *
        0.10
    )

    liquidity_penalty = (
        clamp(
            liquidity_help_score
        )
        /
        100.0
        *
        0.12
    )

    multiplier = (
        1.0
        +
        own_premium
        +
        damage_premium
        -
        liquidity_penalty
    )

    multiplier = max(
        0.90,
        min(
            multiplier,
            1.30,
        ),
    )

    return round_money(
        market_value
        *
        multiplier
    )


def evaluate_purchase_from_rival(
    *,
    proposed_price: int,
    market_value: int,
    rival_user_id: int | None,
    rival_intelligence: dict | None,
    player_score: float,
    lineup_need_score: float = 50.0,
    speculation_score: float = 50.0,
    negotiation_round: int = 1,
    our_last_offer: int | None = None,
    is_rival_counter: bool = False,
) -> dict:
    """
    Cada contraoferta rival se recalcula desde cero.
    """

    proposed_price = safe_int(
        proposed_price
    )

    market_value = safe_int(
        market_value
    )

    rival_context = (
        classify_rival_context(
            rival_user_id=
                rival_user_id,

            rival_intelligence=
                rival_intelligence,
        )
    )

    purchase_value_score = (
        calculate_purchase_value_score(
            player_score=
                player_score,

            lineup_need_score=
                lineup_need_score,

            speculation_score=
                speculation_score,
        )
    )

    rival_damage_score = (
        calculate_rival_damage_score(
            rival_context=
                rival_context,

            player_score=
                player_score,
        )
    )

    liquidity_help_score = (
        calculate_liquidity_help_score(
            price=
                proposed_price,

            rival_context=
                rival_context,
        )
    )

    strategic_max_price = (
        calculate_strategic_max_purchase_price(
            market_value=
                market_value,

            purchase_value_score=
                purchase_value_score,

            rival_damage_score=
                rival_damage_score,

            liquidity_help_score=
                liquidity_help_score,
        )
    )

    reasons: list[str] = []

    if market_value <= 0:

        decision = (
            "WALK_AWAY"
            if is_rival_counter
            else
            "NO_OFFER"
        )

        our_counter_amount = None

        reasons.append(
            "Sin valor de mercado fiable no se escala la negociacion."
        )

    elif (
        proposed_price
        <= strategic_max_price
    ):

        if is_rival_counter:

            decision = (
                "ACCEPT_COUNTER"
            )

            our_counter_amount = None

            reasons.append(
                "La contraoferta rival sigue dentro del maximo estrategico recalculado."
            )

        else:

            decision = "OFFER"

            our_counter_amount = (
                proposed_price
            )

            reasons.append(
                "La puja propuesta esta dentro del precio maximo estrategico."
            )

    elif (
        is_rival_counter
        and
        our_last_offer
        is not None
        and
        safe_int(
            our_last_offer
        )
        < strategic_max_price
        and
        safe_int(
            negotiation_round,
            1,
        )
        <= 3
        and
        proposed_price
        <= strategic_max_price
        * 1.15
    ):

        decision = (
            "COUNTER_AGAIN"
        )

        our_counter_amount = (
            strategic_max_price
        )

        reasons.append(
            "Aun queda margen para una ultima contraoferta disciplinada."
        )

    else:

        decision = (
            "WALK_AWAY"
            if is_rival_counter
            else
            "NO_OFFER"
        )

        our_counter_amount = None

        if (
            is_rival_counter
            and
            strategic_max_price > 0
            and
            proposed_price
            >
            strategic_max_price
            * 1.15
        ):

            reasons.append(
                "La contraoferta se aleja mas de un 15% de nuestro maximo estrategico; no se entra en escalada."
            )

        else:

            reasons.append(
                "El precio supera el maximo estrategico; Pepe no persigue al vendedor."
            )

    if rival_context.get(
        "direct_rival"
    ):
        reasons.append(
            "Rival directo dinamico: SI."
        )

    reasons.append(
        f"Valor de compra Pepe: "
        f"{purchase_value_score:.1f}/100."
    )

    reasons.append(
        f"Dano deportivo rival estimado: "
        f"{rival_damage_score:.1f}/100."
    )

    reasons.append(
        f"Ayuda de liquidez al rival: "
        f"{liquidity_help_score:.1f}/100."
    )

    return {
        "observer_only":
            OBSERVER_ONLY,

        "direction":
            "WE_BUY_FROM_RIVAL",

        "decision":
            decision,

        "proposed_price":
            proposed_price,

        "market_value":
            market_value,

        "strategic_max_price":
            strategic_max_price,

        "our_counter_amount":
            our_counter_amount,

        "purchase_value_score":
            purchase_value_score,

        "rival_damage_score":
            rival_damage_score,

        "liquidity_help_score":
            liquidity_help_score,

        "negotiation_round":
            safe_int(
                negotiation_round,
                1,
            ),

        "is_rival_counter":
            bool(
                is_rival_counter
            ),

        "our_last_offer":
            (
                safe_int(
                    our_last_offer
                )
                if our_last_offer
                is not None
                else None
            ),

        "rival":
            rival_context,

        "reasons":
            reasons,
    }


# ============================================================
# HELPERS DE INTEGRACION
# ============================================================


def extract_counterparty_from_offer(
    offer: dict,
) -> dict:

    direct = offer.get(
        "counterparty"
    )

    if isinstance(
        direct,
        dict,
    ):
        return direct

    raw_offer = (
        offer.get(
            "raw_offer",
            {},
        )
        or {}
    )

    nested = raw_offer.get(
        "counterparty"
    )

    if isinstance(
        nested,
        dict,
    ):
        return nested

    return {}


def extract_seller_user_id(
    player: dict,
) -> int | None:

    direct_keys = (
        "seller_user_id",
        "sellerUserID",
        "owner_user_id",
        "ownerUserID",
    )

    for key in direct_keys:

        value = safe_int(
            player.get(
                key
            )
        )

        if value > 0:
            return value

    object_keys = (
        "seller",
        "owner",
        "market_owner",
        "user",
        "from",
    )

    for key in object_keys:

        value = player.get(
            key
        )

        if isinstance(
            value,
            dict,
        ):

            user_id = safe_int(
                value.get(
                    "id"
                )
            )

            if user_id > 0:
                return user_id

    return None
