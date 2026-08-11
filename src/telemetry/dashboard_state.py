from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.analysis.decision_orchestrator import build_global_decision
from src.analysis.market_analyzer import get_latest_snapshot, load_snapshot
from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
    save_rival_intelligence,
)
from src.collectors.board_history_collector import collect_board_history


AUTOPILOT_LOG = Path("data") / "autopilot" / "autopilot_log.jsonl"
DASHBOARD_STATUS = Path("dashboard") / "data" / "status.json"


ACTION_LABELS = {
    "MONITOR_OFFERS": "Vigilar ofertas",
    "NEVER_SELL": "No vender",
    "KEEP_GOOD_OFFER": "Conservar buena oferta",
    "HOLD_SOLVENCY_RESERVED": "Reservar para solvencia",
    "WATCH_SPECULATION": "Vigilar especulación",
    "BUY_SPECULATION": "Comprar para especular",
    "MONITOR_SOLVENCY": "Vigilar solvencia",
    "CONSIDER_PLAYER_EXIT": "Revisar riesgo de plantilla",
    "RENEW_MARKET_LISTING": "Renovar publicación",
    "RENEW_MARKET_LISTING_WATCH": "Vigilar renovación",
    "REROLL_COMPUTER_OFFER": "Pedir nueva oferta a Computer",
    "ACCEPT_CLUSTER_BEFORE_EXPIRY": "Aceptar oferta antes de caducar",
    "WATCH_CRITICAL_EXPIRY_CLUSTER": "Vigilar ofertas críticas",
    "SAVE_LINEUP": "Guardar XI",
    "WAIT": "Esperar",
}

TYPE_LABELS = {
    "OFFER_DECISION_INTELLIGENCE": "Ofertas Computer",
    "PLAYER_RISK_EXIT": "Riesgo de plantilla",
    "SOLVENCY_GUARANTEE": "Solvencia",
    "SPECULATION_WATCH": "Especulación",
    "SPECULATION_BUY": "Especulación",
    "MARKET_LISTING_RENEW": "Publicaciones en venta",
    "COMPUTER_OFFER_REROLL_WATCH": "Ofertas Computer",
    "ACCEPT_BEFORE_EXPIRY_WATCH": "Caducidad de ofertas",
    "ACCEPT_BEFORE_EXPIRY_SAFETY": "Caducidad de ofertas",
    "LINEUP": "Alineación",
    "IDLE": "Sin acciones",
}

STATUS_LABELS = {
    "MONITOR_OFFERS": "VIGILANDO",
    "CONSIDER_PLAYER_EXIT": "REVISANDO",
    "MONITOR_SOLVENCY": "GARANTIZADA",
    "WATCH_SPECULATION": "OPORTUNIDADES",
    "BUY_SPECULATION": "OPORTUNIDAD",
    "WAIT": "EN ESPERA",
}


def safe_int(value, default=0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def human_action(action: str | None) -> str:
    if not action:
        return "Sin decisión"
    return ACTION_LABELS.get(action, action.replace("_", " ").title())


def human_candidate(candidate: dict) -> dict:
    action = candidate.get("action")
    candidate_type = candidate.get("type")
    return {
        "type": candidate_type,
        "label": TYPE_LABELS.get(
            candidate_type,
            str(candidate_type or "").replace("_", " ").title(),
        ),
        "action": action,
        "status": STATUS_LABELS.get(
            action,
            human_action(action).upper(),
        ),
        "priority": safe_int(candidate.get("priority")),
        "executable": bool(candidate.get("executable")),
    }


def compact_lineup(lineup_state: dict) -> dict:
    lineup = lineup_state.get("lineup", {}) or {}
    selected = lineup.get("selected", []) or []

    players = []

    for player in selected:
        players.append(
            {
                "id": safe_int(player.get("id")),
                "name": player.get("name", "?"),
                "position": safe_int(
                    player.get(
                        "lineup_position",
                        player.get("position"),
                    )
                ),
                "price": safe_int(player.get("price")),
                "price_increment": safe_int(player.get("priceIncrement")),
                "points": safe_int(player.get("points")),
                # Es un score INTERNO de selección, no puntos fantasy esperados.
                "lineup_score": round(
                    safe_float(player.get("lineup_score")),
                    2,
                ),
                "availability": player.get("availability_label"),
                "jp_status": player.get("external_lineup_status"),
                "jp_confidence": round(
                    safe_float(player.get("external_lineup_confidence")),
                    1,
                ),
            }
        )

    return {
        "formation": lineup.get("formation_name"),
        "playable": safe_int(lineup_state.get("playable_count")),
        "missing": safe_int(lineup_state.get("missing")),
        "score": round(safe_float(lineup.get("score")), 2),
        "players": players,
    }


def compact_rivals(intelligence: dict, current_user_id: int | None) -> list[dict]:
    rows = []

    for manager in intelligence.get("managers", []) or []:
        user_id = safe_int(manager.get("user_id"))
        rows.append(
            {
                "user_id": user_id,
                "name": manager.get("name", "?"),
                "is_us": (
                    current_user_id is not None
                    and user_id == int(current_user_id)
                ),
                "points": safe_int(manager.get("points")),
                "rank": manager.get("points_rank"),
                "balance": safe_int(manager.get("balance")),
                "roster_count": safe_int(manager.get("roster_count")),
                "roster_value": safe_int(manager.get("roster_value")),
                "net_worth": safe_int(manager.get("net_worth")),
                "maximum_bid": safe_int(manager.get("maximum_bid")),
                "maximum_bid_source": manager.get("maximum_bid_source"),
                "max_observed_bid": safe_int(manager.get("max_observed_bid")),
                "lost_bids": safe_int(manager.get("lost_bids")),
                "activity": manager.get("market_activity"),
                "profile": manager.get("profile"),
                "threat_score": manager.get("threat_score"),
                "threat_level": manager.get("threat_level"),
                "top_assets": manager.get("top_assets", [])[:3],
            }
        )

    return rows


def compact_offers(state: dict) -> list[dict]:
    offer_reroll = state.get("offer_reroll", {}) or {}
    offers = []

    for offer in offer_reroll.get("offers", []) or []:
        names = [
            player.get("name", "?")
            for player in offer.get("players", []) or []
        ]
        offers.append(
            {
                "players": names,
                "amount": safe_int(offer.get("amount")),
                "premium_percent": round(
                    safe_float(offer.get("premium_percent")),
                    2,
                ),
                "solvency_reserved": bool(
                    offer.get("solvency_reserved")
                ),
                "action": offer.get("action"),
                "action_label": human_action(offer.get("action")),
                "hours_to_expiry": (
                    round(safe_float(offer.get("hours_to_expiry")), 1)
                    if offer.get("hours_to_expiry") is not None
                    else None
                ),
            }
        )

    return offers


def compact_speculation(state: dict) -> dict:
    speculation = state.get("speculation", {}) or {}
    budget = speculation.get("budget", {}) or {}

    candidates = (
        speculation.get("executable_buys")
        or speculation.get("buy_candidates")
        or []
    )

    compact = []

    for item in candidates[:5]:
        compact.append(
            {
                "name": item.get("name") or item.get("player_name") or "?",
                "score": round(
                    safe_float(
                        item.get(
                            "speculation_score",
                            item.get("score"),
                        )
                    ),
                    1,
                ),
                "price": safe_int(
                    item.get(
                        "price",
                        item.get("market_price"),
                    )
                ),
                "price_increment": safe_int(
                    item.get(
                        "price_increment",
                        item.get("priceIncrement"),
                    )
                ),
                "action": item.get("action"),
            }
        )

    return {
        "enabled": bool(budget.get("enabled")),
        "mode": budget.get("mode"),
        "blocked_by": budget.get("blocked_by"),
        "budget": safe_int(
            budget.get(
                "available_budget",
                budget.get("budget"),
            )
        ),
        "max_operation": safe_int(
            budget.get(
                "max_operation",
                budget.get("max_single_operation"),
            )
        ),
        "candidate_count": len(
            speculation.get("buy_candidates", []) or []
        ),
        "executable_count": len(
            speculation.get("executable_buys", []) or []
        ),
        "candidates": compact,
    }


def compact_listings(state: dict) -> dict:
    lifecycle = state.get("listing_lifecycle", {}) or {}
    return {
        "listing_count": safe_int(lifecycle.get("listing_count")),
        "renew_required_count": safe_int(
            lifecycle.get("renew_required_count")
        ),
        "renew_required": [
            {
                "name": item.get("name"),
                "hours_to_expiry": (
                    round(safe_float(item.get("hours_to_expiry")), 1)
                    if item.get("hours_to_expiry") is not None
                    else None
                ),
                "listed_price": safe_int(item.get("listed_price")),
            }
            for item in lifecycle.get("renew_required", []) or []
        ][:8],
    }


def load_activity_feed(limit: int = 8) -> list[dict]:
    if not AUTOPILOT_LOG.exists():
        return []

    rows = []

    try:
        lines = AUTOPILOT_LOG.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return []

    for line in lines[-limit:][::-1]:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        execution = record.get("execution", {}) or {}
        action = (
            execution.get("action")
            or record.get("decision_action")
            or record.get("action")
        )

        rows.append(
            {
                "timestamp": record.get("timestamp"),
                "phase": record.get("log_phase") or record.get("phase"),
                "action": action,
                "label": human_action(action),
                "write_performed": bool(
                    execution.get("write_performed", False)
                ),
                "success": execution.get("success"),
                "status": execution.get("status"),
            }
        )

    return rows


def build_dashboard_state() -> dict:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    # Observer puro: recalcula, pero no ejecuta.
    result = build_global_decision(snapshot)
    state = result.get("state", {}) or {}
    decision = result.get("decision", {}) or {}

    board = collect_board_history()

    market_status = (
        snapshot.get("market", {})
        .get("status", {})
        or {}
    )

    rival_intelligence = build_rival_intelligence(
        events=board.get("events", []),
        users=board.get("users", []),
        profiles=board.get("profiles", []),
        catalog=snapshot.get("catalog", {}),
        current_user_id=board.get("current_user_id"),
        own_finances=board.get("own_finances", {}),
        own_balance=market_status.get("balance"),
        own_maximum_bid=market_status.get("maximumBid"),
    )

    save_rival_intelligence(rival_intelligence)

    deadline = state.get("deadline", {}) or {}
    temporal_gate = state.get("temporal_gate", {}) or {}
    liquidity = state.get("liquidity", {}) or {}
    recovery = liquidity.get("recovery", {}) or {}
    franchise = state.get("franchise", {}) or {}
    target = franchise.get("target", {}) or {}

    candidates = [
        human_candidate(candidate)
        for candidate in result.get("candidates", [])[:7]
    ]

    dashboard = {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "snapshot": snapshot_file,
            "league_id": board.get("league_id"),
            "current_user_id": board.get("current_user_id"),
            "mode": "LIVE",
            "cycle_minutes": 15,
        },
        "summary": {
            "balance": safe_int(state.get("balance")),
            "maximum_bid": safe_int(market_status.get("maximumBid")),
            "target_matchday": state.get("target_matchday"),
            "phase": state.get("phase"),
            "hours_to_deadline": round(
                safe_float(state.get("hours_to_deadline")),
                2,
            ),
            "lineup_risk": state.get("lineup_risk"),
            "lineup_pressure": safe_int(
                state.get("lineup_pressure_score")
            ),
            "hard_safety": bool(
                temporal_gate.get(
                    "hard_safety_mode",
                    temporal_gate.get("hard_safety", False),
                )
            ),
            "operations_locked": bool(
                temporal_gate.get(
                    "operations_locked",
                    state.get("operations_locked", False),
                )
            ),
        },
        "decision": {
            "type": decision.get("type"),
            "action": decision.get("action"),
            "label": human_action(decision.get("action")),
            "priority": safe_int(decision.get("priority")),
            "executable": bool(decision.get("executable")),
            "reason": decision.get("reason"),
        },
        "solvency": {
            "needed": bool(recovery.get("needed")),
            "possible": recovery.get("possible"),
            "deficit": safe_int(recovery.get("deficit")),
            "incoming_offers": safe_int(
                liquidity.get("incoming_offer_count")
            ),
            "listed": safe_int(liquidity.get("listing_count")),
            "to_list": safe_int(liquidity.get("to_list_count")),
        },
        "franchise": {
            "state": franchise.get("state"),
            "target": target.get("name"),
            "score": target.get("franchise_score"),
            "price": safe_int(
                target.get("price", target.get("market_price"))
            ),
            "price_increment": safe_int(
                target.get(
                    "price_increment",
                    target.get("priceIncrement"),
                )
            ),
        },
        "lineup": compact_lineup(
            state.get("lineup", {}) or {}
        ),
        "rival_intelligence": {
            "ledger_status": rival_intelligence.get("ledger_status"),
            "maximum_bid_calibration": rival_intelligence.get(
                "maximum_bid_calibration"
            ),
            "managers": compact_rivals(
                rival_intelligence,
                board.get("current_user_id"),
            ),
        },
        "offers": compact_offers(state),
        "speculation": compact_speculation(state),
        "listings": compact_listings(state),
        "priorities": candidates,
        "activity": load_activity_feed(),
    }

    return dashboard


def save_dashboard_state(
    state: dict,
    path: Path = DASHBOARD_STATUS,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path
