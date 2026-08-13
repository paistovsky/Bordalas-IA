from __future__ import annotations

from src.analysis.intelligent_bid_engine import (
    build_market_bid_authority,
    build_market_seller_lookup,
    calculate_intelligent_bids,
)
from src.analysis.solvency_engine import build_t15_solvency_forecast

from src.analysis.exact_price_policy import (
    exact_euro,
    floor_euro,
)


MIN_TRADING_SCORE = 72.0
DEFAULT_REQUIRED_ROI = 0.10
HIGH_CONVICTION_REQUIRED_ROI = 0.08
LOW_CONVICTION_REQUIRED_ROI = 0.12
MAX_EXPECTED_UPSIDE = 0.30


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default




def _player_id(player: dict) -> int:
    return _safe_int(player.get("id"))


def _player_price(player: dict) -> int:
    return max(
        _safe_int(player.get("price")),
        _safe_int(player.get("market_price")),
        _safe_int(player.get("player_price")),
    )


def _history_confidence(player: dict) -> float:
    raw = player.get("history_confidence", {}) or {}
    if isinstance(raw, dict):
        return _safe_float(raw.get("confidence"))
    return _safe_float(raw)


def _jp_score(player: dict) -> float:
    signal = player.get("external_signal", {}) or {}
    score = signal.get("jp_market_score")
    if score is None:
        return 50.0
    return _safe_float(score, 50.0)


def _intelligent_score(intel: dict | None, player: dict) -> float:
    if intel:
        value = intel.get("intelligent_score")
        if value is not None:
            return _safe_float(value)
    return _safe_float(player.get("tactical_score"), 50.0)


def calculate_trading_score(player: dict, intel: dict | None) -> float:
    """
    V10.3: score de trading, no score de XI.

    La señal principal sigue siendo Speculation Engine. Intelligent Bid
    aporta calidad contextual; histórico y Jornada Perfecta actúan como
    confirmación, nunca como sustituto de la tendencia interna.
    """
    speculation = _safe_float(player.get("speculation_score"))
    intelligent = _intelligent_score(intel, player)
    history = _history_confidence(player)
    jp = _jp_score(player)

    score = (
        speculation * 0.65
        + intelligent * 0.20
        + history * 0.10
        + jp * 0.05
    )
    return round(max(0.0, min(score, 100.0)), 1)


def estimate_expected_upside_percent(player: dict) -> float:
    """
    Estimación prudente para poder convertir la tesis especulativa en un
    máximo racional de puja. No pretende predecir el precio exacto.

    Nunca se usa como garantía de solvencia: Safe Debt solo reconoce
    liquidez recuperable de la plantilla/ofertas actuales.
    """
    speculation = _safe_float(player.get("speculation_score"))
    history = _history_confidence(player)
    increment_pct = max(_safe_float(player.get("price_increment_percent")), 0.0)
    jp = _jp_score(player)

    upside = 0.05
    upside += max(speculation - 72.0, 0.0) * 0.004
    upside += min(increment_pct, 8.0) * 0.005
    upside += (history / 100.0) * 0.04
    upside += max(jp - 50.0, 0.0) * 0.001

    return round(min(upside, MAX_EXPECTED_UPSIDE), 4)


def required_roi_for_score(trading_score: float) -> float:
    if trading_score >= 88:
        return HIGH_CONVICTION_REQUIRED_ROI
    if trading_score >= 80:
        return DEFAULT_REQUIRED_ROI
    return LOW_CONVICTION_REQUIRED_ROI


def build_sporting_safe_capital(solvency: dict) -> dict:
    solvency = solvency or {}
    balance = _safe_int(solvency.get("balance"))
    guarantee = solvency.get("solvency_guarantee", {}) or {}
    safe_debt = solvency.get("max_safe_debt", {}) or {}
    temporary_debt = solvency.get("temporary_debt", {}) or {}
    deadline = solvency.get("deadline", {}) or {}
    hard_safety = solvency.get("hard_safety", {}) or {}
    portfolio = solvency.get("safe_liquidity_portfolio", {}) or {}

    recovery = _safe_int(
        portfolio.get("trading_safe_total", portfolio.get("usable_total", 0))
    )
    safety_buffer = _safe_int(guarantee.get("safety_buffer", 500_000))

    debt_window_open = bool(safe_debt.get("debt_window_open", False))
    debt_allowed = bool(temporary_debt.get("allowed", False))
    operations_locked = bool(deadline.get("operations_locked", False))
    hard_safety_active = bool(
        hard_safety.get("active", False)
        or deadline.get("hard_safety_mode", False)
        or str(deadline.get("phase", "")) in {"HARD_SAFETY", "FINALIZATION"}
    )

    cash_capacity = max(balance, 0)
    t15_capacity = max(balance + recovery - safety_buffer, 0)

    can_use_debt = bool(
        debt_window_open
        and debt_allowed
        and not operations_locked
        and not hard_safety_active
    )

    deployable = t15_capacity if can_use_debt else cash_capacity
    if balance < 0 and not can_use_debt:
        deployable = 0

    projected_t15_after_buffer = balance + recovery - safety_buffer

    return {
        "balance": balance,
        "trading_safe_recovery": recovery,
        "safety_buffer": safety_buffer,
        "cash_capacity": cash_capacity,
        "projected_t15_after_buffer_before_trading": projected_t15_after_buffer,
        "sporting_safe_spend_capacity": max(_safe_int(deployable), 0),
        "can_use_temporary_debt": can_use_debt,
        "debt_window_open": debt_window_open,
        "temporary_debt_allowed": debt_allowed,
        "operations_locked": operations_locked,
        "hard_safety_active": hard_safety_active,
        "phase": deadline.get("phase"),
        "portfolio": portfolio,
    }


def _build_bid_quote(
    *,
    player: dict,
    intel: dict | None,
    maximum_bid: int,
    snapshot: dict,
    seller_lookup: dict[int, dict],
) -> dict:
    price = _player_price(player)
    trading_score = calculate_trading_score(player, intel)
    upside = estimate_expected_upside_percent(player)
    required_roi = required_roi_for_score(trading_score)

    expected_exit = exact_euro(price * (1.0 + upside))
    rational_raw = (
        expected_exit / (1.0 + required_roi)
        if expected_exit > 0
        else 0
    )
    max_rational = floor_euro(rational_raw)

    competitive_cap = _safe_int(
        (intel or {}).get("competitive_strategic_max_price")
    )
    if competitive_cap > 0:
        max_rational = min(max_rational, competitive_cap)

    if maximum_bid > 0:
        max_rational = min(max_rational, maximum_bid)

    legacy_suggested = _safe_int((intel or {}).get("suggested_bid"))

    authority = build_market_bid_authority(
        snapshot,
        player,
        intel,
        trading_score=trading_score,
        seller_lookup=seller_lookup,
    )
    authority_bid = _safe_int(authority.get("authority_bid"))
    target_bid = authority_bid

    # V10.3.1: Bid Authority propone el precio incluso si legacy=0.
    # Market Trader conserva la ultima palabra con el techo de ROI.
    recommended = min(target_bid, max_rational) if max_rational > 0 else 0
    if recommended < price and max_rational >= price:
        recommended = price

    expected_profit = max(expected_exit - recommended, 0) if recommended > 0 else 0
    expected_roi = (
        (expected_profit / recommended) * 100.0
        if recommended > 0
        else 0.0
    )

    return {
        "price": price,
        "trading_score": trading_score,
        "intelligent_score": round(_intelligent_score(intel, player), 1),
        "legacy_intelligent_bid": legacy_suggested,
        "bid_authority_source": authority.get("source"),
        "bid_authority_bid": authority_bid,
        "bid_authority_synthetic_bid": _safe_int(authority.get("synthetic_bid")),
        "bid_authority_premium_percent": _safe_float(authority.get("premium_percent")),
        "bid_authority_confidence": authority.get("confidence"),
        "bid_authority_reason": authority.get("reason"),
        "bid_authority_allowed": bool(authority.get("allowed", False)),
        "bid_authority_components": authority.get("components", {}) or {},
        "target_bid": _safe_int(target_bid),
        "recommended_bid": recommended,
        "max_rational_bid": max_rational,
        "expected_upside_percent": round(upside * 100.0, 1),
        "expected_exit_value": expected_exit,
        "required_roi_percent": round(required_roi * 100.0, 1),
        "expected_profit": expected_profit,
        "expected_roi_percent": round(expected_roi, 1),
        "history_confidence": round(_history_confidence(player), 1),
        "jp_market_score": round(_jp_score(player), 1),
        "price_increment_percent": round(
            _safe_float(player.get("price_increment_percent")), 2
        ),
        "competitive_max_price": competitive_cap or None,
    }


def build_market_trader_shadow(
    snapshot: dict,
    *,
    decision_result: dict,
    intelligent_bids: list[dict] | None = None,
) -> dict:
    """
    V10.4E Market Trader - EXACT EURO PRICING.

    - No escribe en Biwenger.
    - No modifica action_decision LIVE.
    - Usa BUY/WATCH del Speculation Engine.
    - Conecta suggested_bid/intelligent_score del Intelligent Bid Engine.
    - Impone un maximo racional basado en margen/ROI exacto al euro.
    - Financia compras solo con Sporting Safe Debt B1.
    - Simula VARIAS compras secuenciales para comprobar rotacion/capital.
    """
    state = decision_result.get("state", {}) or {}
    speculation = state.get("speculation", {}) or {}
    solvency = state.get("solvency", {}) or {}

    capital = build_sporting_safe_capital(solvency)
    status = (snapshot.get("market", {}) or {}).get("status", {}) or {}
    maximum_bid = _safe_int(status.get("maximumBid"))

    if intelligent_bids is None:
        # V10.3 no reactiva API-Football/external_status. La señal externa
        # de trading ya viene de Jornada Perfecta dentro de speculation.
        intelligent_bids = calculate_intelligent_bids(
            snapshot,
            allow_external_checks=False,
        )

    seller_lookup = build_market_seller_lookup(snapshot)

    intel_lookup = {
        _player_id(item): item
        for item in (intelligent_bids or [])
        if _player_id(item) > 0
    }

    legacy_budget = speculation.get("budget", {}) or {}
    legacy_total_budget = _safe_int(legacy_budget.get("total_budget"))
    legacy_single_limit = _safe_int(legacy_budget.get("single_operation_limit"))
    sporting_capacity = _safe_int(capital.get("sporting_safe_spend_capacity"))

    budget_enabled = bool(legacy_budget.get("enabled", False))
    total_budget = (
        min(legacy_total_budget, sporting_capacity)
        if budget_enabled
        else 0
    )
    single_limit = min(
        legacy_single_limit if legacy_single_limit > 0 else total_budget,
        total_budget,
    ) if total_budget > 0 else 0

    candidates = speculation.get("buy_candidates", []) or []
    assessed = []

    for player in candidates:
        player_id = _player_id(player)
        intel = intel_lookup.get(player_id)
        quote = _build_bid_quote(
            player=player,
            intel=intel,
            maximum_bid=maximum_bid,
            snapshot=snapshot,
            seller_lookup=seller_lookup,
        )
        assessed.append({
            "id": player_id,
            "name": player.get("name") or str(player_id),
            "position": player.get("position"),
            "speculation_action": player.get("speculation_action"),
            "speculation_score": _safe_float(player.get("speculation_score")),
            "dominant_role": player.get("dominant_role"),
            **quote,
            "intelligent_action_legacy": (intel or {}).get("action"),
            "intel_external_checks": False,
            "raw_player": player,
        })

    assessed.sort(
        key=lambda item: (
            _safe_float(item.get("trading_score")),
            _safe_float(item.get("expected_roi_percent")),
            _safe_float(item.get("speculation_score")),
        ),
        reverse=True,
    )

    cumulative_spend = 0
    allocation = []
    balance = _safe_int(capital.get("balance"))
    recovery = _safe_int(capital.get("trading_safe_recovery"))
    buffer = _safe_int(capital.get("safety_buffer"))

    for item in assessed:
        decision = "WATCH"
        reason = "Senal todavia insuficiente para compra V10.3."
        bid = _safe_int(item.get("recommended_bid"))
        score = _safe_float(item.get("trading_score"))
        spec_action = str(item.get("speculation_action") or "")

        projected_after = balance - cumulative_spend - bid + recovery - buffer

        if spec_action != "BUY_SPECULATION":
            decision = "WATCH"
            reason = "Speculation Engine no clasifica la posicion como BUY_SPECULATION."
        elif score < MIN_TRADING_SCORE:
            decision = "PASS_SCORE"
            reason = "Trading score por debajo del umbral V10.3."
        elif not item.get("bid_authority_allowed", False):
            decision = "PASS_BID_AUTHORITY"
            reason = "Bid Authority V10.3.1 no autoriza una puja para esta posicion."
        elif bid <= 0 or _safe_int(item.get("max_rational_bid")) < _safe_int(item.get("price")):
            decision = "PASS_MARGIN"
            reason = "No existe precio de entrada compatible con el ROI minimo."
        elif not budget_enabled:
            decision = "PASS_BUDGET"
            reason = str(legacy_budget.get("reason") or "Presupuesto especulativo bloqueado.")
        elif bid > single_limit:
            decision = "PASS_SINGLE_LIMIT"
            reason = "La puja supera el limite de una sola posicion especulativa."
        elif cumulative_spend + bid > total_budget:
            decision = "PASS_PORTFOLIO_BUDGET"
            reason = "La cartera shadow ya ha consumido el presupuesto de trading."
        elif projected_after < 0:
            decision = "PASS_T15"
            reason = "La compra llevaria Sporting Safe Debt por debajo del buffer T-15."
        else:
            decision = "BUY_SHADOW"
            reason = (
                "BUY especulativo con Intelligent Bid limitado por maximo racional "
                "y respaldado por Sporting Safe Debt B1."
            )
            cumulative_spend += bid
            projected_after = balance - cumulative_spend + recovery - buffer

        allocation.append({
            **item,
            "decision": decision,
            "decision_reason": reason,
            "cumulative_spend_after": cumulative_spend,
            "remaining_budget_after": max(total_budget - cumulative_spend, 0),
            "projected_t15_after_buffer": projected_after,
        })

    buys = [item for item in allocation if item.get("decision") == "BUY_SHADOW"]

    return {
        "version": "V10.3.1",
        "mode": "SHADOW",
        "writes_biwenger": False,
        "policy": "SPECULATION_PLUS_BID_AUTHORITY_PLUS_ROI_CAP_PLUS_SPORTING_SAFE_DEBT_B1",
        "capital": capital,
        "legacy_speculation_budget": legacy_budget,
        "trading_budget": {
            "enabled": budget_enabled and total_budget > 0,
            "total_budget": total_budget,
            "single_operation_limit": single_limit,
            "sporting_safe_capacity": sporting_capacity,
            "legacy_total_budget": legacy_total_budget,
        },
        "opportunities": allocation,
        "buy_plan": buys,
        "planned_spend": cumulative_spend,
        "planned_positions": len(buys),
        "remaining_budget": max(total_budget - cumulative_spend, 0),
        "projected_t15_after_plan": balance - cumulative_spend + recovery - buffer,
        "intelligent_bid_external_checks": False,
        "reason": (
            "V10.3.1 simula compras especulativas con Bid Authority. Puede crear "
            "precio desde cero cuando legacy no puja; ROI pone el techo; B1 limita la deuda deportiva."
        ),
    }
