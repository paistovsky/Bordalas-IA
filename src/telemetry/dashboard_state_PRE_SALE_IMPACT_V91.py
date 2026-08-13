from __future__ import annotations

import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

from src.analysis.decision_orchestrator import build_global_decision
from src.analysis.market_analyzer import get_latest_snapshot, load_snapshot
from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
    save_rival_intelligence,
)
from src.collectors.board_history_collector import collect_board_history
from src.telemetry.league_center import build_league_center


from src.telemetry.player_photo_resolver import (
    build_player_photo_lookup as build_player_photo_lookup_v3,
    display_name as display_player_name,
)

AUTOPILOT_LOG = Path("data") / "autopilot" / "autopilot_log.jsonl"
COMPETITIVE_LOG = Path("data") / "autopilot" / "competitive_observer_log.jsonl"
DASHBOARD_STATUS = Path("dashboard") / "data" / "status.json"
PLAYER_MAPPING_CACHE = Path("data") / "player_mapping_cache.json"
PLAYER_PHOTO_CACHE = Path("data") / "dashboard_player_photo_cache.json"


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



def load_player_mapping_cache() -> dict:
    if not PLAYER_MAPPING_CACHE.exists():
        return {}

    try:
        payload = json.loads(
            PLAYER_MAPPING_CACHE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}

    if isinstance(payload, dict):
        # Algunas versiones guardan directamente el lookup;
        # otras pueden envolverlo.
        for key in (
            "mappings",
            "players",
            "data",
        ):
            nested = payload.get(key)
            if isinstance(nested, dict):
                return nested

        return payload

    return {}


def get_external_player_id(
    mapping_cache: dict,
    biwenger_id: int,
) -> int | None:
    entry = (
        mapping_cache.get(str(biwenger_id))
        or mapping_cache.get(biwenger_id)
        or {}
    )

    if not isinstance(entry, dict):
        return None

    value = (
        entry.get("external_id")
        or entry.get("api_football_id")
        or entry.get("api_id")
    )

    try:
        value = int(value)
    except (TypeError, ValueError):
        return None

    return value if value > 0 else None


def api_football_photo_url(
    external_id: int | None,
) -> str | None:
    if not external_id:
        return None

    return (
        "https://media.api-sports.io/"
        f"football/players/{external_id}.png"
    )



def _normalize_name(value: str) -> str:
    text = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    )
    text = "".join(
        ch
        for ch in text
        if not unicodedata.combining(ch)
    )
    return " ".join(
        text.lower().strip().split()
    )


def load_dashboard_player_photo_cache() -> dict:
    if not PLAYER_PHOTO_CACHE.exists():
        return {}

    try:
        payload = json.loads(
            PLAYER_PHOTO_CACHE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )


def save_dashboard_player_photo_cache(
    cache: dict,
) -> None:
    try:
        PLAYER_PHOTO_CACHE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        PLAYER_PHOTO_CACHE.write_text(
            json.dumps(
                cache,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def fetch_api_football_player_photo(
    player_name: str,
) -> dict:
    """
    Fallback de telemetría para fotos.
    Se usa únicamente cuando no existe mapping previo.
    El resultado se cachea para no consumir API en cada ciclo.
    """
    api_key = os.getenv(
        "API_FOOTBALL_KEY"
    )

    if not api_key:
        return {}

    name = str(player_name or "").strip()

    if len(name) < 3:
        return {}

    try:
        response = requests.get(
            "https://v3.football.api-sports.io/players",
            headers={
                "x-apisports-key": api_key,
            },
            params={
                "search": name,
            },
            timeout=4,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return {}

    rows = payload.get("response") or []

    if not isinstance(rows, list):
        return {}

    target = _normalize_name(name)
    best = None
    best_score = -1

    for row in rows:
        player = (
            row.get("player")
            if isinstance(row, dict)
            else None
        ) or {}

        candidate_name = (
            player.get("name")
            or ""
        )

        candidate = _normalize_name(
            candidate_name
        )

        if not candidate:
            continue

        score = 0

        if candidate == target:
            score = 100
        elif (
            candidate in target
            or target in candidate
        ):
            score = 70
        else:
            target_tokens = set(
                target.split()
            )
            candidate_tokens = set(
                candidate.split()
            )
            score = len(
                target_tokens
                & candidate_tokens
            ) * 20

        if score > best_score:
            best_score = score
            best = player

    if not best or best_score <= 0:
        return {}

    external_id = safe_int(
        best.get("id")
    )

    photo_url = best.get("photo")

    if not photo_url and external_id:
        photo_url = (
            "https://media.api-sports.io/"
            f"football/players/{external_id}.png"
        )

    return {
        "api_football_id": (
            external_id or None
        ),
        "photo_url": photo_url,
        "api_name": best.get("name"),
    }


def build_player_photo_lookup(
    snapshot: dict,
) -> dict[int, dict]:
    return build_player_photo_lookup_v3(snapshot)

def compact_lineup(
    lineup_state: dict,
    snapshot: dict,
    photo_lookup: dict[int, dict] | None = None,
) -> dict:
    lineup = lineup_state.get("lineup", {}) or {}
    selected = lineup.get("selected", []) or []
    photo_lookup = photo_lookup or {}

    my_team_by_id = {
        safe_int(player.get("id")): player
        for player in snapshot.get("my_team", []) or []
    }

    catalog_players = (
        snapshot.get("catalog", {})
        .get("data", {})
        .get("players", {})
        or {}
    )

    players = []

    for player in selected:
        player_id = safe_int(player.get("id"))

        catalog_source = {}
        if isinstance(catalog_players, dict):
            catalog_source = (
                catalog_players.get(str(player_id))
                or catalog_players.get(player_id)
                or {}
            )

        source = my_team_by_id.get(player_id) or catalog_source or {}
        photo = photo_lookup.get(player_id) or {}

        icon_hero = (
            player.get("iconHero")
            or source.get("iconHero")
            or photo.get("icon_hero")
        )

        raw_name = (
            player.get("name")
            or source.get("name")
            or photo.get("name")
            or "?"
        )

        fixed_name = display_player_name(raw_name)

        price = safe_int(
            player.get(
                "price",
                source.get("price"),
            )
        )

        players.append(
            {
                "id": player_id,
                "name": fixed_name,
                "position": safe_int(
                    player.get(
                        "lineup_position",
                        player.get(
                            "position",
                            source.get("position"),
                        ),
                    )
                ),
                "price": price,
                "price_increment": safe_int(
                    player.get(
                        "priceIncrement",
                        source.get("priceIncrement"),
                    )
                ),
                "points": safe_int(
                    player.get(
                        "points",
                        source.get("points"),
                    )
                ),
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
                "icon_hero": icon_hero,
                "biwenger_photo_url": photo.get("biwenger_photo_url"),
                "api_football_id": photo.get("api_football_id"),
                "api_photo_url": photo.get("api_photo_url"),
                "photo_url": photo.get("photo_url"),
                "photo_source": photo.get("photo_source"),
                "team_id": safe_int(
                    player.get(
                        "teamID",
                        source.get("teamID"),
                    )
                ),
                "number": safe_int(
                    player.get(
                        "number",
                        source.get("number"),
                    )
                ),
            }
        )

    return {
        "formation": lineup.get("formation_name"),
        "playable": safe_int(lineup_state.get("playable_count")),
        "missing": safe_int(lineup_state.get("missing")),
        "score": round(safe_float(lineup.get("score")), 2),
        "total_value": sum(safe_int(item.get("price")) for item in players),
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



def load_latest_jsonl(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    return {}


def compact_portfolio_recommendation(item: dict | None) -> dict | None:
    if not item:
        return None

    sporting = item.get("sporting_opportunity_cost", {}) or {}

    return {
        "player_names": item.get("player_names", []) or [],
        "sold_count": safe_int(item.get("sold_count")),
        "total_amount": safe_int(item.get("total_amount")),
        "post_balance": safe_int(item.get("post_balance")),
        "restores_solvency": bool(item.get("restores_solvency")),
        "playable_count": safe_int(item.get("playable_count")),
        "missing": safe_int(item.get("missing")),
        "lineup_complete": bool(item.get("lineup_complete")),
        "formation_before": item.get("formation_before"),
        "formation_after": item.get("formation_after"),
        "incoming_players": item.get("incoming_players", []) or [],
        "competitive_damage": round(
            safe_float(item.get("competitive_damage")),
            1,
        ),
        "lineup_score_before": round(
            safe_float(
                item.get(
                    "lineup_score_before",
                    sporting.get("lineup_score_before"),
                )
            ),
            2,
        ),
        "lineup_score_after": round(
            safe_float(
                item.get(
                    "lineup_score_after",
                    sporting.get("lineup_score_after"),
                )
            ),
            2,
        ),
        "lineup_score_loss": round(
            safe_float(
                item.get(
                    "lineup_score_loss",
                    sporting.get("lineup_score_loss"),
                )
            ),
            2,
        ),
        "lineup_score_loss_percent": round(
            safe_float(
                item.get(
                    "lineup_score_loss_percent",
                    sporting.get("lineup_score_loss_percent"),
                )
            ),
            2,
        ),
    }


def compact_competitive_offer(item: dict) -> dict:
    negotiation = item.get("negotiation", {}) or {}
    replacement = item.get("replacement_detail", {}) or {}
    sporting = item.get("sporting_opportunity_cost", {}) or {}

    incoming = [
        player.get("name") or str(player.get("id"))
        for player in replacement.get("incoming_players", []) or []
    ]

    return {
        "offer_id": item.get("offer_id"),
        "player_id": safe_int(item.get("player_id")),
        "player_name": item.get("player_name") or "?",
        "rival_name": item.get("rival_name") or "Rival",
        "amount": safe_int(item.get("amount")),
        "decision_authority": item.get("decision_authority"),
        "authoritative_decision": item.get("authoritative_decision"),
        "authoritative_counter_amount": safe_int(
            item.get("authoritative_counter_amount")
            or item.get("counter_amount")
        ),
        "strategic_sell_price": safe_int(item.get("strategic_sell_price")),
        "competitive_premium_percent": round(
            safe_float(item.get("competitive_premium_percent")),
            2,
        ),
        "temporal_premium_percent": round(
            safe_float(item.get("temporal_premium_percent")),
            2,
        ),
        "sporting_premium_percent": round(
            safe_float(item.get("sporting_premium_percent")),
            2,
        ),
        "solvency_discount_percent": round(
            safe_float(item.get("solvency_discount_percent")),
            2,
        ),
        "rival_reinforcement_score": round(
            safe_float(item.get("rival_reinforcement_score")),
            1,
        ),
        "sporting_cost_score": round(
            safe_float(item.get("sporting_cost_score")),
            1,
        ),
        "negotiation_event": negotiation.get("event"),
        "action_gate": negotiation.get("action_gate"),
        "negotiation_round": safe_int(negotiation.get("negotiation_round")),
        "should_respond": bool(negotiation.get("should_respond")),
        "negotiation_status": negotiation.get("status"),
        "replacement_status": (
            replacement.get("replacement_status")
            or (item.get("replacement", {}) or {}).get("replacement_status")
        ),
        "replacement_source": replacement.get("replacement_source"),
        "pre_sale_playable_count": safe_int(
            replacement.get("pre_sale_playable_count")
        ),
        "post_sale_playable_count": safe_int(
            replacement.get("post_sale_playable_count")
        ),
        "formation_before": replacement.get("formation_before"),
        "formation_after": replacement.get("formation_after"),
        "incoming_players": incoming,
        "lineup_score_before": round(
            safe_float(sporting.get("lineup_score_before")),
            2,
        ),
        "lineup_score_after": round(
            safe_float(sporting.get("lineup_score_after")),
            2,
        ),
        "lineup_score_loss": round(
            safe_float(sporting.get("lineup_score_loss")),
            2,
        ),
        "lineup_score_loss_percent": round(
            safe_float(sporting.get("lineup_score_loss_percent")),
            2,
        ),
    }


def load_competitive_dashboard_state() -> dict:
    record = load_latest_jsonl(COMPETITIVE_LOG)

    if not record:
        return {
            "available": False,
            "live_enabled": True,
            "status": "SIN_TELEMETRIA",
            "status_label": "SIN TELEMETRÍA COMPETITIVE",
            "message": "Aún no existe competitive_observer_log.jsonl.",
            "offers": [],
            "portfolio": {},
        }

    offers = [
        compact_competitive_offer(item)
        for item in record.get("manager_offers", []) or []
    ]

    responding = [item for item in offers if item.get("should_respond")]
    waiting = [
        item
        for item in offers
        if item.get("action_gate") == "NO_ACTION_WAITING_RIVAL"
    ]

    if responding:
        status = "ACTIONABLE"
        status_label = "PEPE TIENE RESPUESTA PENDIENTE"
        message = (
            f"{len(responding)} negociación(es) requieren recalcular/responder. "
            "La ejecución real sigue dependiendo del Safety Gate del ciclo."
        )
    elif offers and len(waiting) == len(offers):
        status = "WAITING_RIVAL"
        status_label = "PEPE ESPERANDO AL RIVAL"
        message = "Las ofertas observadas no han cambiado desde la última respuesta."
    elif offers:
        status = "MONITORING"
        status_label = "PEPE VIGILANDO NEGOCIACIONES"
        message = "Competitive V2.0 está siguiendo ofertas activas de managers."
    else:
        status = "IDLE"
        status_label = "SIN OFERTAS DE MANAGERS"
        message = "Competitive V2.0 está activo y no hay negociaciones de managers."

    portfolio = record.get("competitive_portfolio", {}) or {}

    current = (
        (portfolio.get("current", {}) or {}).get("recommended")
        or {}
    )
    strategic = (
        (portfolio.get("strategic", {}) or {}).get("recommended")
        or {}
    )

    return {
        "available": bool(record.get("available", True)),
        "live_enabled": True,
        "source_timestamp": record.get("timestamp"),
        "snapshot": record.get("snapshot"),
        "status": status,
        "status_label": status_label,
        "message": message,
        "offer_count": len(offers),
        "responding_count": len(responding),
        "waiting_count": len(waiting),
        "offers": offers,
        "portfolio": {
            "balance": safe_int(portfolio.get("balance")),
            "deficit": safe_int(portfolio.get("deficit")),
            "current": compact_portfolio_recommendation(current),
            "strategic": compact_portfolio_recommendation(strategic),
        },
        # El log Competitive V2.0 actual persiste ofertas + portfolio, pero no
        # el Safety Gate ni competitive_execution. No inventamos esos datos.
        "safety_gate_persisted": False,
        "execution_persisted": False,
    }


def _normalize_display_text(value) -> str:
    text = str(value or "")
    try:
        repaired = text.encode("latin1").decode("utf-8")
        if repaired:
            return repaired
    except Exception:
        pass
    return text


def load_recent_competitive_closed(
    hours: float = 12.0,
) -> list[dict]:
    """
    Reconstruye cierres recientes comparando manager_offers
    entre snapshots consecutivos del observer.

    Si una oferta existía en N y desaparece en N+1:
    RETIRADA POR RIVAL.
    """
    if not COMPETITIVE_LOG.exists():
        return []

    try:
        raw_lines = COMPETITIVE_LOG.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return []

    records = []

    for line in raw_lines[-500:]:
        try:
            record = json.loads(line)
        except Exception:
            continue

        timestamp = record.get("timestamp")
        manager_offers = (
            record.get("manager_offers")
            or []
        )

        if timestamp and isinstance(
            manager_offers,
            list,
        ):
            records.append(
                (timestamp, manager_offers)
            )

    if len(records) < 2:
        return []

    now = datetime.now()
    closed_by_key = {}

    for index in range(
        1,
        len(records),
    ):
        previous_ts, previous_offers = (
            records[index - 1]
        )
        current_ts, current_offers = (
            records[index]
        )

        previous_map = {}

        for offer in previous_offers:
            player_id = safe_int(
                offer.get("player_id")
            )

            rival_name = (
                _normalize_display_text(
                    offer.get("rival_name")
                    or "Rival"
                )
            )

            if player_id <= 0:
                continue

            previous_map[
                (player_id, rival_name)
            ] = offer

        current_keys = set()

        for offer in current_offers:
            player_id = safe_int(
                offer.get("player_id")
            )

            rival_name = (
                _normalize_display_text(
                    offer.get("rival_name")
                    or "Rival"
                )
            )

            if player_id <= 0:
                continue

            current_keys.add(
                (player_id, rival_name)
            )

        try:
            closed_dt = datetime.fromisoformat(
                str(current_ts)
            )
            age_hours = (
                now - closed_dt
            ).total_seconds() / 3600.0
        except Exception:
            continue

        if not (
            0 <= age_hours <= hours
        ):
            continue

        for key, old_offer in (
            previous_map.items()
        ):
            if key in current_keys:
                continue

            player_id, rival_name = key

            closed_by_key[key] = {
                "player_id": player_id,
                "player_name": (
                    _normalize_display_text(
                        old_offer.get(
                            "player_name"
                        )
                        or "?"
                    )
                ),
                "rival_name": rival_name,
                "amount": safe_int(
                    old_offer.get("amount")
                ),
                "authoritative_counter_amount": (
                    safe_int(
                        old_offer.get(
                            "authoritative_counter_amount"
                        )
                        or old_offer.get(
                            "counter_amount"
                        )
                        or old_offer.get(
                            "strategic_amount"
                        )
                    )
                ),
                "closed_at": current_ts,
                "closed_status": (
                    "RIVAL_WITHDREW"
                ),
                "closed_label": (
                    "RETIRADA POR RIVAL"
                ),
                "previous_snapshot_timestamp": (
                    previous_ts
                ),
            }

    # HARD TELEMETRY SAFETY:
    # anything still present in the latest observer snapshot
    # is ACTIVE and must never be reported as withdrawn/rejected.
    latest_active_keys = set()

    if records:
        _, latest_offers = records[-1]

        for offer in latest_offers:
            player_id = safe_int(
                offer.get("player_id")
            )

            rival_name = (
                _normalize_display_text(
                    offer.get("rival_name")
                    or "Rival"
                )
            )

            if player_id > 0:
                latest_active_keys.add(
                    (player_id, rival_name)
                )

    safe_closed = [
        item
        for key, item in closed_by_key.items()
        if key not in latest_active_keys
    ]

    return sorted(
        safe_closed,
        key=lambda item: (
            item.get("closed_at")
            or ""
        ),
        reverse=True,
    )

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

    league_center = build_league_center(
        snapshot=snapshot,
        board=board,
        rival_intelligence=rival_intelligence,
    )

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

    photo_lookup = build_player_photo_lookup(
        snapshot
    )

    competitive = load_competitive_dashboard_state()

    for offer in competitive.get("offers", []) or []:
        player_id = safe_int(
            offer.get("player_id")
        )
        photo = photo_lookup.get(
            player_id,
            {}
        )
        offer["api_football_id"] = (
            photo.get("api_football_id")
        )
        offer["photo_url"] = (
            photo.get("photo_url")
        )
        offer["icon_hero"] = (
            photo.get("icon_hero")
        )

    recent_closed = load_recent_competitive_closed()
    for closed in recent_closed:
        photo = photo_lookup.get(safe_int(closed.get("player_id")), {})
        closed["photo_url"] = photo.get("photo_url")
        closed["icon_hero"] = photo.get("icon_hero")
    competitive["recent_closed"] = recent_closed

    competitive_status = competitive.get("status")

    if competitive_status == "ACTIONABLE":
        pepe_now = {
            "level": "ACTION",
            "title": "Pepe tiene una respuesta competitiva pendiente",
            "detail": (
                f"{safe_int(competitive.get('responding_count'))} negociación(es) "
                "requieren recalcular y pasar Safety Gate."
            ),
        }
    elif competitive_status == "WAITING_RIVAL":
        recent_closed = (
            competitive.get(
                "recent_closed",
                [],
            )
            or []
        )

        if recent_closed:
            latest_closed = (
                recent_closed[0]
            )

            pepe_now = {
                "level": "WAIT",
                "title": (
                    "Movimiento rival detectado"
                ),
                "detail": (
                    f"{latest_closed.get('rival_name', 'El rival')} "
                    f"retiró su oferta por "
                    f"{latest_closed.get('player_name', 'un jugador')}. "
                    "Bordalás lo ha registrado y mantiene abiertas "
                    "las negociaciones restantes."
                ),
            }
        else:
            pepe_now = {
                "level": "WAIT",
                "title": "Esperar al rival",
                "detail": (
                    "No hay nuevos movimientos desde la última respuesta. "
                    "Bordalás no repetirá contraofertas mientras espera al rival."
                ),
            }

    elif bool(recovery.get("needed")):
        pepe_now = {
            "level": "SOLVENCY",
            "title": "Prioridad: recuperar solvencia",
            "detail": (
                f"Déficit actual de {safe_int(recovery.get('deficit')):,} EUR. "
                "Pepe mantiene el XI válido mientras busca la salida más eficiente."
            ),
        }
    else:
        pepe_now = {
            "level": "OK",
            "title": human_action(decision.get("action")),
            "detail": decision.get("reason") or "Sin urgencias críticas.",
        }

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
        "pepe_now": pepe_now,
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
            state.get("lineup", {}) or {},
            snapshot,
            photo_lookup,
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
        "league_center": league_center,
        "offers": compact_offers(state),
        "speculation": compact_speculation(state),
        "listings": compact_listings(state),
        "priorities": candidates,
        "activity": load_activity_feed(),
        "competitive": competitive,
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
