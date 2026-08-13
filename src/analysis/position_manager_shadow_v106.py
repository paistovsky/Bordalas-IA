from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analysis.position_ledger_v105 import (
    DEFAULT_LEDGER_PATH,
    load_ledger,
    save_ledger,
)


VERSION = "V10.6"
MODE = "SHADOW"
WRITES_BIWENGER = False

OPEN_STATUS = "OPEN_POSITION"
PENDING_STATUSES = {
    "BID_PENDING",
    "BID_PENDING_UNCONFIRMED",
}

ACTION_PRIORITY = {
    "CUT_LOSS": 90,
    "TAKE_PROFIT": 85,
    "ROTATE_CAPITAL": 75,
    "HOLD": 20,
}

HARD_DEADLINE_PHASES = {
    "HARD_SAFETY",
    "FINALIZATION",
}

HIGH_DEADLINE_PHASES = {
    "HIGH_ATTENTION",
}

DOWN_ACCELERATION = {
    "DECELERATING_UP",
    "STEADY_DOWN",
    "ACCELERATING_DOWN",
}

UP_ACCELERATION = {
    "ACCELERATING_UP",
    "STEADY_UP",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _position_age_days(position: dict, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    opened = _parse_iso(position.get("opened_at"))
    if opened is None:
        return 0.0

    return max((now - opened).total_seconds() / 86400.0, 0.0)


def _roi(entry: int, current: int) -> tuple[int, float]:
    if entry <= 0:
        return 0, 0.0

    profit = current - entry
    roi_percent = (profit / entry) * 100.0
    return profit, round(roi_percent, 2)


def _acceleration_state(speculation: dict) -> str:
    direct = speculation.get("acceleration_state")
    if direct:
        return str(direct)

    trend_data = speculation.get("trend_data", {}) or {}
    acceleration = trend_data.get("acceleration", {}) or {}
    return str(acceleration.get("state") or "INSUFFICIENT_HISTORY")


def classify_market_outlook(
    speculation: dict,
    *,
    roi_percent: float = 0.0,
) -> str:
    action = str(speculation.get("speculation_action") or "")
    availability = speculation.get("availability_risk", {}) or {}
    risk = str(availability.get("risk") or "").upper()

    if action == "SELL_RISK" or risk == "CRITICO":
        return "RISK"

    trend_score = _safe_float(speculation.get("trend_score"), 50.0)
    increment = _safe_int(speculation.get("price_increment"))
    acceleration = _acceleration_state(speculation)

    if trend_score >= 65 and increment > 0 and acceleration not in DOWN_ACCELERATION:
        return "STRONG_UP"

    if trend_score >= 55 and increment > 0:
        if acceleration in DOWN_ACCELERATION:
            return "FADING_UP"
        return "UP"

    if roi_percent < 0 and increment > 0 and trend_score >= 50:
        return "RECOVERY"

    if trend_score < 40 and increment < 0:
        return "STRONG_DOWN"

    if trend_score < 50 and increment < 0:
        return "DOWN"

    if increment > 0 and acceleration in DOWN_ACCELERATION:
        return "FADING_UP"

    return "NEUTRAL"


def build_sporting_contexts(
    snapshot: dict,
    lineup: dict,
) -> dict[int, dict]:
    """
    Heurística rápida de protección deportiva.

    V10.6 NO autoriza ventas. Antes de una futura venta LIVE se deberá
    ejecutar una simulación completa de impacto del XI. Aquí solo evitamos
    tratar un titular crítico como capital indiferenciado.
    """
    selected = lineup.get("selected", []) or []
    selected_ids = {
        _safe_int(player.get("id"))
        for player in selected
        if _safe_int(player.get("id"))
    }

    formation = lineup.get("formation", {}) or {}

    # Reutilizamos la inteligencia ya calculada por Lineup Engine.
    try:
        from src.analysis.lineup_engine import prepare_players

        prepared = prepare_players(
            snapshot,
            lineup_intelligence=lineup.get("lineup_intelligence"),
        )
    except Exception:
        prepared = []

    prepared_lookup = {
        _safe_int(player.get("id")): player
        for player in prepared
        if _safe_int(player.get("id"))
    }

    team = snapshot.get("my_team", []) or []
    contexts: dict[int, dict] = {}

    for raw in team:
        player_id = _safe_int(raw.get("id"))
        if not player_id:
            continue

        position = _safe_int(raw.get("position"))
        prepared_player = prepared_lookup.get(player_id, {}) or {}
        player_score = _safe_float(
            prepared_player.get("lineup_score"),
            0.0,
        )

        usable_same_position = []
        for candidate in prepared:
            candidate_id = _safe_int(candidate.get("id"))
            if not candidate_id:
                continue

            eligible = candidate.get("eligible_positions", []) or []
            if position not in eligible:
                continue

            if not bool(candidate.get("lineup_eligible", True)):
                continue

            if not bool(candidate.get("automatic_lineup", True)):
                continue

            usable_same_position.append(candidate)

        replacements = [
            candidate
            for candidate in usable_same_position
            if _safe_int(candidate.get("id")) != player_id
        ]

        replacement = max(
            replacements,
            key=lambda item: _safe_float(item.get("lineup_score")),
            default=None,
        )

        replacement_score = (
            _safe_float(replacement.get("lineup_score"))
            if replacement
            else None
        )

        replacement_gap = (
            player_score - replacement_score
            if replacement_score is not None
            else None
        )

        required = _safe_int(
            formation.get(position)
            if position in formation
            else formation.get(str(position))
        )
        depth = len(usable_same_position)
        starting = player_id in selected_ids

        protection = 0.0
        reasons = []

        if starting:
            protection += 35
            reasons.append("TITULAR_XI")

        if required > 0:
            if depth <= required:
                protection += 35
                reasons.append("SIN_PROFUNDIDAD_POSICIONAL")
            elif depth == required + 1:
                protection += 20
                reasons.append("PROFUNDIDAD_JUSTA")
            elif depth == required + 2:
                protection += 8

        if replacement_gap is None and starting:
            protection += 20
            reasons.append("SIN_REEMPLAZO_MEDIBLE")
        elif replacement_gap is not None:
            if replacement_gap >= 25:
                protection += 20
                reasons.append("REEMPLAZO_MUY_INFERIOR")
            elif replacement_gap >= 10:
                protection += 12
                reasons.append("REEMPLAZO_INFERIOR")
            elif replacement_gap > 0:
                protection += 5

        protection = _clamp(protection)

        if protection >= 70:
            risk = "HIGH"
        elif protection >= 40:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        contexts[player_id] = {
            "player_id": player_id,
            "starting_xi": starting,
            "position": position,
            "formation_required": required,
            "usable_position_depth": depth,
            "lineup_score": round(player_score, 2),
            "replacement_player_id": (
                _safe_int(replacement.get("id"))
                if replacement
                else None
            ),
            "replacement_name": (
                replacement.get("name")
                if replacement
                else None
            ),
            "replacement_score": (
                round(replacement_score, 2)
                if replacement_score is not None
                else None
            ),
            "replacement_gap": (
                round(replacement_gap, 2)
                if replacement_gap is not None
                else None
            ),
            "sporting_protection_score": round(protection, 1),
            "sporting_sale_risk": risk,
            "reasons": reasons,
            "confidence": "HEURISTIC_SHADOW_NO_SALE_SIMULATION",
        }

    return contexts


def build_reinvestment_context(
    trader: dict,
    ledger: dict,
) -> dict:
    occupied_ids = {
        _safe_int(position.get("player_id"))
        for position in ledger.get("positions", []) or []
        if str(position.get("status") or "") in (
            PENDING_STATUSES | {OPEN_STATUS}
        )
    }

    candidates = []
    for opportunity in trader.get("opportunities", []) or []:
        player_id = _safe_int(opportunity.get("id"))
        if not player_id or player_id in occupied_ids:
            continue

        if str(opportunity.get("decision") or "") != "BUY_SHADOW":
            continue

        bid = _safe_int(opportunity.get("recommended_bid"))
        if bid <= 0:
            continue

        candidates.append(opportunity)

    candidates.sort(
        key=lambda item: (
            _safe_float(item.get("expected_roi_percent")),
            _safe_float(item.get("trading_score")),
            _safe_float(item.get("speculation_score")),
        ),
        reverse=True,
    )

    best = candidates[0] if candidates else None
    remaining_budget = _safe_int(trader.get("remaining_budget"))

    if best:
        best_bid = _safe_int(best.get("recommended_bid"))
        shortfall = max(best_bid - remaining_budget, 0)

        best_summary = {
            "player_id": _safe_int(best.get("id")),
            "name": best.get("name"),
            "bid": best_bid,
            "expected_roi_percent": _safe_float(best.get("expected_roi_percent")),
            "expected_profit": _safe_int(best.get("expected_profit")),
            "trading_score": _safe_float(best.get("trading_score")),
            "speculation_score": _safe_float(best.get("speculation_score")),
            "capital_shortfall": shortfall,
        }
    else:
        best_summary = None

    return {
        "best_alternative": best_summary,
        "remaining_trading_budget": remaining_budget,
        "candidate_count": len(candidates),
    }


def _target_metrics(position: dict, current_value: int) -> dict:
    entry = _safe_int(position.get("entry_price"))
    target = _safe_int(position.get("expected_exit_value_at_bid"))

    if entry <= 0 or target <= entry:
        return {
            "target_value": target,
            "target_progress_percent": None,
            "remaining_upside_percent": None,
            "target_reached": False,
        }

    total_expected_gain = target - entry
    realized_mark_gain = current_value - entry

    progress = (
        realized_mark_gain / total_expected_gain * 100.0
        if total_expected_gain > 0
        else 0.0
    )

    remaining_upside = (
        (target - current_value) / current_value * 100.0
        if current_value > 0
        else 0.0
    )

    return {
        "target_value": target,
        "target_progress_percent": round(progress, 1),
        "remaining_upside_percent": round(remaining_upside, 1),
        "target_reached": current_value >= target,
    }


def _deadline_pressure(capital: dict) -> dict:
    phase = str(capital.get("phase") or "UNKNOWN")
    t15 = _safe_int(
        capital.get("projected_t15_after_buffer_before_trading")
    )
    balance = _safe_int(capital.get("balance"))

    score = 0.0
    emergency = False

    if phase in HARD_DEADLINE_PHASES:
        score += 55
        if t15 < 0 or balance < 0:
            score += 35
            emergency = True
    elif phase in HIGH_DEADLINE_PHASES:
        score += 30
        if t15 < 0:
            score += 35
            emergency = True
        elif t15 < 1_000_000:
            score += 15
    elif phase == "PREPARATION":
        score += 10
        if t15 < 0:
            score += 35
            emergency = True
    elif phase in {"ROUND_LOCKED", "ROUND_TRANSITION_LOCK"}:
        score = 100
        emergency = True
    else:
        if t15 < 0:
            score += 25
            emergency = True

    # Regla del proyecto: saldo negativo por sí solo NO obliga a vender
    # si la solvencia T-15 sigue cubierta.
    if balance < 0 and t15 >= 0 and phase not in HARD_DEADLINE_PHASES:
        score = max(score - 10, 0)

    return {
        "phase": phase,
        "balance": balance,
        "projected_t15_after_buffer": t15,
        "pressure_score": round(_clamp(score), 1),
        "emergency": emergency,
    }


def evaluate_open_position(
    position: dict,
    *,
    speculation: dict | None = None,
    sporting: dict | None = None,
    reinvestment: dict | None = None,
    capital: dict | None = None,
    now: datetime | None = None,
) -> dict:
    speculation = speculation or {}
    sporting = sporting or {}
    reinvestment = reinvestment or {}
    capital = capital or {}

    entry = _safe_int(position.get("entry_price"))
    current = _safe_int(
        position.get("current_value")
        or position.get("snapshot_player_value")
    )

    profit, roi_percent = _roi(entry, current)
    target = _target_metrics(position, current)
    age_days = _position_age_days(position, now=now)
    outlook = classify_market_outlook(
        speculation,
        roi_percent=roi_percent,
    )

    spec_action = str(speculation.get("speculation_action") or "")
    trend_score = _safe_float(speculation.get("trend_score"), 50.0)
    price_increment = _safe_int(speculation.get("price_increment"))
    acceleration = _acceleration_state(speculation)
    sporting_score = _safe_float(
        sporting.get("sporting_protection_score")
    )
    starting_xi = bool(sporting.get("starting_xi", False))

    deadline = _deadline_pressure(capital)
    deadline_score = _safe_float(deadline.get("pressure_score"))

    # ---------------------------------------------------------
    # HOLD PRESSURE
    # ---------------------------------------------------------
    hold_score = sporting_score * 0.55

    if outlook == "STRONG_UP":
        hold_score += 45
    elif outlook == "UP":
        hold_score += 32
    elif outlook == "RECOVERY":
        hold_score += 28
    elif outlook == "FADING_UP":
        hold_score += 15
    elif outlook == "NEUTRAL":
        hold_score += 10

    remaining_upside = target.get("remaining_upside_percent")
    if remaining_upside is not None:
        if remaining_upside >= 15:
            hold_score += 18
        elif remaining_upside >= 8:
            hold_score += 10
        elif remaining_upside <= 2:
            hold_score -= 10

    # ---------------------------------------------------------
    # TAKE PROFIT PRESSURE
    # ---------------------------------------------------------
    take_profit = 0.0

    if roi_percent >= 40:
        take_profit += 60
    elif roi_percent >= 25:
        take_profit += 45
    elif roi_percent >= 15:
        take_profit += 32
    elif roi_percent >= 8:
        take_profit += 15

    progress = target.get("target_progress_percent")
    if target.get("target_reached"):
        take_profit += 35
    elif progress is not None and progress >= 90:
        take_profit += 22
    elif progress is not None and progress >= 75:
        take_profit += 12

    if outlook == "STRONG_DOWN":
        take_profit += 35
    elif outlook == "DOWN":
        take_profit += 25
    elif outlook == "FADING_UP":
        take_profit += 18
    elif outlook == "STRONG_UP":
        take_profit -= 25
    elif outlook == "UP":
        take_profit -= 15

    if roi_percent > 0:
        take_profit += deadline_score * 0.30

    # ---------------------------------------------------------
    # CUT LOSS PRESSURE
    # ---------------------------------------------------------
    cut_loss = 0.0

    if roi_percent <= -20:
        cut_loss += 70
    elif roi_percent <= -12:
        cut_loss += 52
    elif roi_percent <= -7:
        cut_loss += 35
    elif roi_percent < 0:
        cut_loss += 15

    if outlook == "RISK":
        cut_loss += 60
    elif outlook == "STRONG_DOWN":
        cut_loss += 35
    elif outlook == "DOWN":
        cut_loss += 25
    elif outlook == "RECOVERY":
        cut_loss -= 25
    elif outlook in {"UP", "STRONG_UP"}:
        cut_loss -= 20

    if spec_action in {"SELL_SPECULATION", "WATCH_SELL"}:
        cut_loss += 15
    elif spec_action == "SELL_RISK":
        cut_loss += 45

    if roi_percent < 0:
        cut_loss += deadline_score * 0.25

    # ---------------------------------------------------------
    # ROTATION / OPPORTUNITY COST
    # ---------------------------------------------------------
    rotation = 0.0
    best_alt = reinvestment.get("best_alternative") or {}

    alt_roi = _safe_float(best_alt.get("expected_roi_percent"))
    alt_score = _safe_float(best_alt.get("trading_score"))
    alt_shortfall = _safe_int(best_alt.get("capital_shortfall"))

    # La rentabilidad futura de la posición actual no se inventa.
    # Como proxy conservador usamos el upside restante hacia la tesis
    # original, nunca la revalorización pasada.
    current_forward_proxy = max(
        _safe_float(remaining_upside),
        0.0,
    ) if remaining_upside is not None else 0.0

    roi_edge = alt_roi - current_forward_proxy

    if best_alt:
        if roi_edge >= 15:
            rotation += 38
        elif roi_edge >= 8:
            rotation += 28
        elif roi_edge >= 4:
            rotation += 15

        if alt_score >= 85:
            rotation += 18
        elif alt_score >= 78:
            rotation += 12
        elif alt_score >= 72:
            rotation += 7

        if alt_shortfall > 0:
            rotation += 22

    if age_days >= 7 and roi_percent < 5:
        rotation += 22
    elif age_days >= 4 and roi_percent < 3:
        rotation += 14
    elif age_days >= 2 and roi_percent <= 0:
        rotation += 8

    if outlook in {"DOWN", "STRONG_DOWN", "NEUTRAL"}:
        rotation += 10
    elif outlook in {"UP", "STRONG_UP"}:
        rotation -= 12

    rotation += deadline_score * 0.20

    # El XI protege contra rotaciones oportunistas normales.
    # No protege contra una emergencia real de solvencia.
    if not deadline.get("emergency"):
        rotation -= sporting_score * 0.50

    # ---------------------------------------------------------
    # HARD RISK
    # ---------------------------------------------------------
    availability = speculation.get("availability_risk", {}) or {}
    availability_risk = str(availability.get("risk") or "").upper()
    hard_player_risk = (
        spec_action == "SELL_RISK"
        or availability_risk == "CRITICO"
    )

    take_profit = _clamp(take_profit)
    cut_loss = _clamp(cut_loss)
    rotation = _clamp(rotation)
    hold_score = _clamp(hold_score)

    reasons = []
    action = "HOLD"
    decision_basis = "NO_EXIT_EDGE"

    # 1. Riesgo duro del activo.
    if hard_player_risk:
        if profit >= 0:
            action = "TAKE_PROFIT"
            decision_basis = "HARD_PLAYER_RISK_WITH_PROFIT"
        else:
            action = "CUT_LOSS"
            decision_basis = "HARD_PLAYER_RISK_WITH_LOSS"

        reasons.append("Riesgo deportivo/mercado crítico del activo.")

    # 2. Deadline/solvencia. La solvencia vence al XI en emergencia.
    elif deadline.get("emergency") and deadline_score >= 60:
        action = "ROTATE_CAPITAL"
        decision_basis = "SOLVENCY_EMERGENCY"
        reasons.append(
            "La posición debe considerarse fuente de liquidez por presión T-15."
        )

    # 3. Pérdida + deterioro.
    elif cut_loss >= 65 and cut_loss > hold_score + 8:
        action = "CUT_LOSS"
        decision_basis = "LOSS_AND_DETERIORATION"
        reasons.append(
            "La pérdida y el deterioro superan el valor de seguir esperando."
        )

    # 4. Beneficio + agotamiento / objetivo.
    elif take_profit >= 65 and take_profit > hold_score + 5:
        action = "TAKE_PROFIT"
        decision_basis = "PROFIT_HARVEST"
        reasons.append(
            "La plusvalía/avance de tesis compensa más que el upside restante."
        )

    # 5. Coste de oportunidad.
    elif (
        rotation >= 65
        and best_alt
        and rotation > hold_score + 5
    ):
        action = "ROTATE_CAPITAL"
        decision_basis = "SUPERIOR_REINVESTMENT"
        reasons.append(
            "Existe una alternativa comprable con mejor uso esperado del capital."
        )

    else:
        if outlook in {"STRONG_UP", "UP"} and roi_percent >= 0:
            decision_basis = "HOLD_WINNER"
            reasons.append(
                "La posición mantiene momentum positivo; no se corta un ganador."
            )
        elif outlook == "RECOVERY":
            decision_basis = "HOLD_RECOVERY"
            reasons.append(
                "La posición está recuperando valor; no se cristaliza la pérdida todavía."
            )
        elif starting_xi and sporting_score >= 50:
            decision_basis = "HOLD_SPORTING_VALUE"
            reasons.append(
                "El coste deportivo de liberar la posición sigue siendo alto."
            )
        else:
            reasons.append(
                "No existe una ventaja suficiente para cerrar o rotar la posición."
            )

    # Notas explicativas adicionales.
    if target.get("target_reached"):
        reasons.append("La tesis de precio original ya ha alcanzado su objetivo.")

    if best_alt:
        reasons.append(
            "Mejor alternativa: "
            f"{best_alt.get('name')} | ROI esperado "
            f"{alt_roi:.1f}% | edge vs upside restante "
            f"{roi_edge:.1f} pp."
        )

    if starting_xi:
        reasons.append(
            f"Jugador en XI; protección deportiva {sporting_score:.1f}/100."
        )

    if deadline.get("phase"):
        reasons.append(
            f"Fase {deadline.get('phase')} | T-15 tras buffer "
            f"{_safe_int(deadline.get('projected_t15_after_buffer'))} EUR."
        )

    confidence_score = 45.0
    history = speculation.get("history_confidence", {}) or {}
    if isinstance(history, dict):
        confidence_score += _safe_float(history.get("confidence")) * 0.30

    if position.get("thesis_source") == "LIVE_DECISION_EXACT":
        confidence_score += 12
    elif position.get("thesis_source") == "CURRENT_RECONSTRUCTION":
        confidence_score += 5

    if current > 0 and entry > 0:
        confidence_score += 8

    confidence_score = _clamp(confidence_score)

    if confidence_score >= 80:
        confidence = "HIGH"
    elif confidence_score >= 60:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "version": VERSION,
        "mode": MODE,
        "writes_biwenger": WRITES_BIWENGER,
        "position_id": position.get("position_id"),
        "player_id": _safe_int(position.get("player_id")),
        "player_name": position.get("player_name"),
        "status": position.get("status"),
        "action": action,
        "priority": ACTION_PRIORITY[action],
        "decision_basis": decision_basis,
        "confidence": confidence,
        "confidence_score": round(confidence_score, 1),
        "entry_price": entry,
        "current_value": current,
        "profit": profit,
        "roi_percent": roi_percent,
        "position_age_days": round(age_days, 2),
        "target": target,
        "market": {
            "outlook": outlook,
            "speculation_action": spec_action or None,
            "speculation_score": _safe_float(
                speculation.get("speculation_score")
            ),
            "trend_score": trend_score,
            "trend": speculation.get("trend"),
            "price_increment": price_increment,
            "price_increment_percent": _safe_float(
                speculation.get("price_increment_percent")
            ),
            "acceleration_state": acceleration,
            "availability_risk": availability_risk or None,
        },
        "sporting": sporting,
        "reinvestment": {
            **reinvestment,
            "alternative_roi_edge_vs_remaining_upside_pp": round(roi_edge, 1),
        },
        "capital": deadline,
        "scores": {
            "hold": round(hold_score, 1),
            "take_profit": round(take_profit, 1),
            "cut_loss": round(cut_loss, 1),
            "rotate_capital": round(rotation, 1),
        },
        "reasons": reasons,
    }


def build_position_manager_shadow(
    ledger: dict,
    *,
    speculation_board: dict | None = None,
    trader: dict | None = None,
    sporting_contexts: dict[int, dict] | None = None,
    capital: dict | None = None,
    now: datetime | None = None,
) -> dict:
    speculation_board = speculation_board or {}
    trader = trader or {}
    sporting_contexts = sporting_contexts or {}
    capital = capital or trader.get("capital", {}) or {}

    spec_lookup = {
        _safe_int(item.get("id")): item
        for item in speculation_board.get("owned", []) or []
        if _safe_int(item.get("id"))
    }

    reinvestment = build_reinvestment_context(
        trader,
        ledger,
    )

    decisions = []
    pending = []

    for position in ledger.get("positions", []) or []:
        status = str(position.get("status") or "")
        player_id = _safe_int(position.get("player_id"))

        if status in PENDING_STATUSES:
            pending.append({
                "position_id": position.get("position_id"),
                "player_id": player_id,
                "player_name": position.get("player_name"),
                "status": status,
                "bid_amount": _safe_int(position.get("bid_amount")),
                "action": "WAIT_SETTLEMENT",
            })
            continue

        if status != OPEN_STATUS:
            continue

        decisions.append(
            evaluate_open_position(
                position,
                speculation=spec_lookup.get(player_id, {}),
                sporting=sporting_contexts.get(player_id, {}),
                reinvestment=reinvestment,
                capital=capital,
                now=now,
            )
        )

    decisions.sort(
        key=lambda item: (
            _safe_int(item.get("priority")),
            max(
                _safe_float(item.get("scores", {}).get("take_profit")),
                _safe_float(item.get("scores", {}).get("cut_loss")),
                _safe_float(item.get("scores", {}).get("rotate_capital")),
            ),
        ),
        reverse=True,
    )

    actionable = [
        item
        for item in decisions
        if item.get("action") != "HOLD"
    ]

    return {
        "version": VERSION,
        "mode": MODE,
        "writes_biwenger": WRITES_BIWENGER,
        "policy": (
            "ROI_REAL_PLUS_TREND_PLUS_TARGET_PLUS_SPORTING_VALUE_"
            "PLUS_REINVESTMENT_PLUS_T15"
        ),
        "decisions": decisions,
        "actionable": actionable,
        "pending": pending,
        "summary": {
            "open_positions": len(decisions),
            "pending_positions": len(pending),
            "actionable_positions": len(actionable),
            "holds": sum(
                1 for item in decisions
                if item.get("action") == "HOLD"
            ),
            "take_profit": sum(
                1 for item in decisions
                if item.get("action") == "TAKE_PROFIT"
            ),
            "cut_loss": sum(
                1 for item in decisions
                if item.get("action") == "CUT_LOSS"
            ),
            "rotate_capital": sum(
                1 for item in decisions
                if item.get("action") == "ROTATE_CAPITAL"
            ),
        },
    }


def persist_shadow_decisions(
    ledger: dict,
    board: dict,
) -> dict:
    decisions = {
        _safe_int(item.get("player_id")): item
        for item in board.get("decisions", []) or []
        if _safe_int(item.get("player_id"))
    }

    updated = 0
    action_changes = 0

    for position in ledger.get("positions", []) or []:
        if str(position.get("status") or "") != OPEN_STATUS:
            continue

        player_id = _safe_int(position.get("player_id"))
        decision = decisions.get(player_id)
        if not decision:
            continue

        previous = position.get("management_v106", {}) or {}
        previous_action = previous.get("action")
        new_action = decision.get("action")

        position["management_v106"] = {
            "version": VERSION,
            "mode": MODE,
            "last_evaluated_at": _now_iso(),
            "action": new_action,
            "priority": decision.get("priority"),
            "decision_basis": decision.get("decision_basis"),
            "confidence": decision.get("confidence"),
            "profit": decision.get("profit"),
            "roi_percent": decision.get("roi_percent"),
            "market_outlook": (
                decision.get("market", {}) or {}
            ).get("outlook"),
            "sporting_protection_score": (
                decision.get("sporting", {}) or {}
            ).get("sporting_protection_score"),
            "scores": decision.get("scores"),
            "reasons": decision.get("reasons"),
        }
        updated += 1

        if previous_action != new_action:
            events = position.setdefault("events", [])
            events.append({
                "type": "POSITION_MANAGER_SHADOW_ACTION",
                "at": _now_iso(),
                "detail": (
                    f"V10.6 SHADOW: {previous_action or 'NONE'} -> "
                    f"{new_action}."
                ),
                "data": {
                    "decision_basis": decision.get("decision_basis"),
                    "roi_percent": decision.get("roi_percent"),
                },
            })
            action_changes += 1

    return {
        "updated": updated,
        "action_changes": action_changes,
    }


def print_board(board: dict) -> None:
    summary = board.get("summary", {}) or {}

    print("\n" + "=" * 100)
    print("BORDALAS IA - V10.6 POSITION MANAGER SHADOW")
    print("=" * 100)
    print(f"Escrituras Biwenger:         NO")
    print(f"Posiciones abiertas:         {summary.get('open_positions', 0)}")
    print(f"Pujas pendientes:            {summary.get('pending_positions', 0)}")
    print(f"Acciones de salida SHADOW:   {summary.get('actionable_positions', 0)}")

    pending = board.get("pending", []) or []
    if pending:
        print("\nPENDING")
        print("-" * 100)
        for item in pending:
            print(
                f"{item.get('player_name')} | {item.get('status')} | "
                f"bid={_safe_int(item.get('bid_amount')):,} EUR | WAIT_SETTLEMENT"
            )

    decisions = board.get("decisions", []) or []
    if decisions:
        print("\nOPEN POSITIONS")
        print("-" * 100)

        for item in decisions:
            target = item.get("target", {}) or {}
            market = item.get("market", {}) or {}
            sporting = item.get("sporting", {}) or {}
            scores = item.get("scores", {}) or {}
            alt = (
                item.get("reinvestment", {}) or {}
            ).get("best_alternative") or {}

            print(
                f"{item.get('player_name')} | {item.get('action')} | "
                f"ROI={_safe_float(item.get('roi_percent')):+.2f}% | "
                f"P&L={_safe_int(item.get('profit')):+,} EUR | "
                f"outlook={market.get('outlook')} | "
                f"XI={'SI' if sporting.get('starting_xi') else 'NO'}"
            )
            print(
                f"  target={_safe_int(target.get('target_value')):,} | "
                f"progress={target.get('target_progress_percent')}% | "
                f"upside restante={target.get('remaining_upside_percent')}% | "
                f"sporting={_safe_float(sporting.get('sporting_protection_score')):.1f}/100"
            )
            print(
                f"  scores HOLD={_safe_float(scores.get('hold')):.1f} | "
                f"TP={_safe_float(scores.get('take_profit')):.1f} | "
                f"CUT={_safe_float(scores.get('cut_loss')):.1f} | "
                f"ROTATE={_safe_float(scores.get('rotate_capital')):.1f}"
            )

            if alt:
                print(
                    f"  alternativa={alt.get('name')} | "
                    f"ROI esp={_safe_float(alt.get('expected_roi_percent')):.1f}% | "
                    f"bid={_safe_int(alt.get('bid')):,} EUR | "
                    f"shortfall={_safe_int(alt.get('capital_shortfall')):,} EUR"
                )

            print(
                f"  base={item.get('decision_basis')} | "
                f"confianza={item.get('confidence')}"
            )

    if not pending and not decisions:
        print("\nNo hay BID_PENDING ni OPEN_POSITION que gestionar.")

    print("=" * 100)
    print("V10.6: SOLO SHADOW. NO LISTA, VENDE NI ACEPTA OFERTAS.")
    print("=" * 100)


def sync_current(
    *,
    refresh: bool = True,
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
) -> dict:
    # 1) V10.5 mantiene la verdad transaccional del ledger.
    from src.analysis.position_ledger_v105 import sync_current as sync_v105

    ledger_sync = sync_v105(
        refresh=refresh,
        ledger_path=ledger_path,
    )

    # 2) Cargar el snapshot que V10.5 acaba de reconciliar.
    from src.analysis.market_analyzer import load_snapshot

    snapshot = load_snapshot(
        ledger_sync["snapshot_file"]
    )

    # 3) Construir señales actuales. Todo lectura/análisis.
    from src.analysis.decision_orchestrator import build_global_decision
    from src.analysis.lineup_engine import build_lineup
    from src.analysis.market_trader_shadow import build_market_trader_shadow
    from src.analysis.speculation_engine import build_speculation_board

    decision_result = build_global_decision(snapshot)
    trader = build_market_trader_shadow(
        snapshot,
        decision_result=decision_result,
    )
    speculation = build_speculation_board(snapshot)
    lineup = build_lineup(snapshot)

    sporting = build_sporting_contexts(
        snapshot,
        lineup,
    )

    ledger = load_ledger(ledger_path)
    board = build_position_manager_shadow(
        ledger,
        speculation_board=speculation,
        trader=trader,
        sporting_contexts=sporting,
        capital=trader.get("capital", {}) or {},
    )

    persist = persist_shadow_decisions(
        ledger,
        board,
    )
    save_ledger(
        ledger,
        ledger_path,
    )

    return {
        "ok": True,
        "writes_biwenger": False,
        "snapshot_file": ledger_sync.get("snapshot_file"),
        "ledger_sync": ledger_sync,
        "board": board,
        "persist": persist,
        "ledger_path": str(ledger_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sync-current",
        action="store_true",
        help=(
            "Refresca Biwenger, reconcilia V10.5 y evalua las "
            "posiciones V10.6 SHADOW. CERO escrituras Biwenger."
        ),
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Usa el último snapshot local.",
    )
    parser.add_argument(
        "--ledger-path",
        default=str(DEFAULT_LEDGER_PATH),
    )
    args = parser.parse_args()

    if not args.sync_current:
        ledger = load_ledger(args.ledger_path)
        board = build_position_manager_shadow(ledger)
        print_board(board)
        return

    result = sync_current(
        refresh=not args.no_refresh,
        ledger_path=args.ledger_path,
    )

    print("\nSYNC V10.6")
    print("-" * 100)
    print(f"Snapshot:                    {result.get('snapshot_file')}")
    print(f"Ledger:                      {result.get('ledger_path')}")
    print(f"Decisiones persistidas:      {result.get('persist', {}).get('updated', 0)}")
    print(f"Cambios de acción:           {result.get('persist', {}).get('action_changes', 0)}")
    print(f"Escrituras Biwenger:         NO")

    print_board(result["board"])


if __name__ == "__main__":
    main()
