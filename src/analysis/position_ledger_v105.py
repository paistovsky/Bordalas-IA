from __future__ import annotations

import argparse
import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEDGER_VERSION = "V10.5"
DEFAULT_LEDGER_PATH = Path("data/trading/position_ledger.json")

PENDING_STATUSES = {
    "BID_PENDING",
    "BID_PENDING_UNCONFIRMED",
}
OPEN_STATUSES = {
    "OPEN_POSITION",
    "OPEN_POSITION_MISSING_REVIEW",
}
TERMINAL_STATUSES = {
    "LOST",
    "CLOSED",
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_id(offer: dict, key: str) -> int | None:
    actor = offer.get(key)
    if isinstance(actor, dict):
        actor_id = _safe_int(actor.get("id"))
        return actor_id or None

    for field in (
        f"{key}ID",
        f"{key}_id",
        f"{key}Id",
    ):
        actor_id = _safe_int(offer.get(field))
        if actor_id:
            return actor_id

    return None


def _requested_player_ids(offer: dict) -> list[int]:
    result: list[int] = []

    player = offer.get("player")
    if isinstance(player, dict):
        player_id = _safe_int(player.get("id"))
        if player_id:
            result.append(player_id)
    elif isinstance(player, int):
        result.append(player)

    requested = offer.get("requestedPlayers") or []
    if isinstance(requested, (int, dict)):
        requested = [requested]

    if isinstance(requested, list):
        for item in requested:
            if isinstance(item, dict):
                player_id = _safe_int(item.get("id"))
            else:
                player_id = _safe_int(item)
            if player_id:
                result.append(player_id)

    # Deduplicar conservando orden.
    seen = set()
    unique = []
    for player_id in result:
        if player_id not in seen:
            unique.append(player_id)
            seen.add(player_id)
    return unique


def _event(
    event_type: str,
    *,
    detail: str = "",
    at: str | None = None,
    data: dict | None = None,
) -> dict:
    return {
        "type": event_type,
        "at": at or _now_iso(),
        "detail": detail,
        "data": data or {},
    }


def empty_ledger() -> dict:
    return {
        "version": LEDGER_VERSION,
        "updated_at": _now_iso(),
        "positions": [],
        "realized": {
            "closed_positions": 0,
            "profit_eur": 0,
        },
    }


def load_ledger(path: Path | str = DEFAULT_LEDGER_PATH) -> dict:
    path = Path(path)
    if not path.exists():
        return empty_ledger()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raise RuntimeError(
            f"Ledger ilegible o corrupto: {path}"
        )

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Formato de ledger invalido: {path}"
        )

    payload.setdefault("version", LEDGER_VERSION)
    payload.setdefault("positions", [])
    payload.setdefault(
        "realized",
        {
            "closed_positions": 0,
            "profit_eur": 0,
        },
    )
    return payload


def save_ledger(
    ledger: dict,
    path: Path | str = DEFAULT_LEDGER_PATH,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = deepcopy(ledger)
    payload["version"] = LEDGER_VERSION
    payload["updated_at"] = _now_iso()

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _position_key(
    *,
    player_id: int,
    offer_id: int | None,
) -> str:
    if offer_id:
        return f"BID-{offer_id}"
    return f"PLAYER-{player_id}"


def _find_position(
    ledger: dict,
    *,
    offer_id: int | None = None,
    player_id: int | None = None,
    statuses: set[str] | None = None,
) -> dict | None:
    for position in ledger.get("positions", []):
        if statuses and str(position.get("status")) not in statuses:
            continue

        if offer_id and _safe_int(position.get("offer_id")) == int(offer_id):
            return position

        if player_id and _safe_int(position.get("player_id")) == int(player_id):
            return position

    return None


def _market_sale_lookup(snapshot: dict) -> dict[int, dict]:
    lookup = {}
    for sale in (snapshot.get("market", {}) or {}).get("sales", []) or []:
        player = sale.get("player") or {}
        player_id = _safe_int(
            player.get("id") if isinstance(player, dict) else None
        )
        if player_id:
            lookup[player_id] = sale
    return lookup


def _trader_lookup(trader: dict | None) -> dict[int, dict]:
    lookup = {}
    for item in (trader or {}).get("opportunities", []) or []:
        player_id = _safe_int(item.get("id"))
        if player_id:
            lookup[player_id] = item
    return lookup


def _squad_lookup(snapshot: dict) -> dict[int, dict]:
    lookup = {}
    for player in snapshot.get("my_team", []) or []:
        player_id = _safe_int(player.get("id"))
        if player_id:
            lookup[player_id] = player
    return lookup


def _own_user_id(snapshot: dict) -> int:
    league = snapshot.get("league", {}) or {}
    user = league.get("user", {}) or {}
    return _safe_int(user.get("id"))


def _active_outgoing_offers(snapshot: dict) -> list[dict]:
    own_id = _own_user_id(snapshot)
    if not own_id:
        return []

    result = []
    offers = (snapshot.get("market", {}) or {}).get("offers", []) or []

    for offer in offers:
        if str(offer.get("type") or "") != "purchase":
            continue

        if str(offer.get("status") or "waiting") not in {
            "waiting",
            "pending",
            "active",
        }:
            continue

        from_id = _actor_id(offer, "from")
        if from_id != own_id:
            continue

        if not _requested_player_ids(offer):
            continue

        result.append(offer)

    return result


def _active_offer_by_player(snapshot: dict) -> dict[int, dict]:
    lookup = {}
    for offer in _active_outgoing_offers(snapshot):
        for player_id in _requested_player_ids(offer):
            lookup[player_id] = offer
    return lookup


def _append_event_once(
    position: dict,
    event_type: str,
    *,
    detail: str,
    data: dict | None = None,
) -> bool:
    events = position.setdefault("events", [])
    if events and str(events[-1].get("type")) == event_type:
        if str(events[-1].get("detail")) == detail:
            return False

    events.append(
        _event(
            event_type,
            detail=detail,
            data=data,
        )
    )
    return True


def build_position_from_verified_bid(
    result: dict,
) -> dict:
    execution = result.get("execution", {}) or {}
    api_response = execution.get("api_response", {}) or {}
    api_data = api_response.get("data", {}) if isinstance(api_response, dict) else {}

    gate = result.get("gate", {}) or {}
    selected = gate.get("selected", {}) or {}
    fresh = result.get("fresh_reprice", {}) or {}
    preflight = result.get("preflight", {}) or {}

    player_id = _safe_int(
        execution.get("player_id")
        or selected.get("id")
    )
    offer_id = _safe_int(api_data.get("id")) or None
    bid_amount = _safe_int(
        execution.get("amount")
        or fresh.get("fresh_recommended_bid")
    )

    expected_exit = _safe_int(
        fresh.get("expected_exit_value")
        or selected.get("expected_exit_value")
    )
    expected_profit = max(expected_exit - bid_amount, 0) if bid_amount else 0
    expected_roi = (
        (expected_profit / bid_amount) * 100.0
        if bid_amount
        else 0.0
    )

    return {
        "position_id": _position_key(
            player_id=player_id,
            offer_id=offer_id,
        ),
        "player_id": player_id,
        "player_name": selected.get("name") or f"Jugador {player_id}",
        "strategy": "SPECULATION",
        "origin": "CONTROLLED_LIVE",
        "status": "BID_PENDING",
        "offer_id": offer_id,
        "seller_id": _safe_int(preflight.get("seller_id")) or None,
        "seller": preflight.get("seller"),
        "bid_amount": bid_amount,
        "entry_price": None,
        "bid_created_epoch": _safe_int(api_data.get("created")) or None,
        "bid_until_epoch": _safe_int(api_data.get("until")) or None,
        "snapshot_player_value": _safe_int(
            fresh.get("fresh_biwenger_minimum_bid")
            or selected.get("price")
        ),
        "listing_price_at_bid": _safe_int(
            fresh.get("fresh_listing_price")
            or preflight.get("current_price")
        ),
        "speculation_score_at_bid": round(
            _safe_float(selected.get("speculation_score")),
            2,
        ),
        "trading_score_at_bid": round(
            _safe_float(selected.get("trading_score")),
            2,
        ),
        "max_rational_bid_at_bid": _safe_int(
            fresh.get("max_rational_bid")
            or selected.get("max_rational_bid")
        ),
        "expected_exit_value_at_bid": expected_exit,
        "expected_profit_at_bid": expected_profit,
        "expected_roi_at_bid_percent": round(expected_roi, 2),
        "t15_after_bid": _safe_int(
            fresh.get("fresh_projected_t15_after_buffer")
        ),
        "current_value": _safe_int(
            fresh.get("fresh_biwenger_minimum_bid")
            or selected.get("price")
        ),
        "unrealized_profit": None,
        "unrealized_roi_percent": None,
        "opened_at": None,
        "closed_at": None,
        "realized_profit": None,
        "realized_roi_percent": None,
        "thesis_source": "LIVE_DECISION_EXACT",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "events": [
            _event(
                "BID_SENT",
                detail=(
                    f"Puja especulativa enviada y verificada por "
                    f"{bid_amount} EUR."
                ),
                data={
                    "offer_id": offer_id,
                    "expected_exit_value": expected_exit,
                    "expected_roi_percent": round(expected_roi, 2),
                },
            )
        ],
    }


def upsert_position(
    ledger: dict,
    position: dict,
) -> tuple[dict, bool]:
    offer_id = _safe_int(position.get("offer_id")) or None
    player_id = _safe_int(position.get("player_id"))

    existing = _find_position(
        ledger,
        offer_id=offer_id,
        player_id=player_id,
        statuses=PENDING_STATUSES | OPEN_STATUSES,
    )

    if existing is None:
        ledger.setdefault("positions", []).append(position)
        return position, True

    # Nunca reescribir la historia original con una reconstrucción posterior.
    if existing.get("origin") == "CONTROLLED_LIVE":
        return existing, False

    preserved_events = existing.get("events", []) or []
    existing.update(position)
    existing["events"] = preserved_events + [
        e for e in (position.get("events") or [])
        if e not in preserved_events
    ]
    existing["updated_at"] = _now_iso()
    return existing, False


def record_verified_bid(
    result: dict,
    *,
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
) -> dict:
    if str(result.get("status")) != "LIVE_BID_SENT_AND_VERIFIED":
        return {
            "registered": False,
            "reason": "transaction_not_verified",
        }

    position = build_position_from_verified_bid(result)
    ledger = load_ledger(ledger_path)
    stored, created = upsert_position(ledger, position)
    save_ledger(ledger, ledger_path)

    return {
        "registered": True,
        "created": created,
        "position_id": stored.get("position_id"),
        "player_id": stored.get("player_id"),
        "status": stored.get("status"),
        "ledger_path": str(ledger_path),
    }


def bootstrap_active_bids(
    ledger: dict,
    snapshot: dict,
    trader: dict | None = None,
) -> dict:
    trader_by_player = _trader_lookup(trader)
    sales = _market_sale_lookup(snapshot)

    created = 0
    reused = 0
    imported = []

    for offer in _active_outgoing_offers(snapshot):
        offer_id = _safe_int(offer.get("id")) or None

        for player_id in _requested_player_ids(offer):
            existing = _find_position(
                ledger,
                offer_id=offer_id,
                player_id=player_id,
                statuses=PENDING_STATUSES | OPEN_STATUSES,
            )
            if existing is not None:
                reused += 1
                continue

            opportunity = trader_by_player.get(player_id, {}) or {}
            sale = sales.get(player_id, {}) or {}
            player = sale.get("player", {}) or {}

            bid_amount = _safe_int(offer.get("amount"))
            expected_exit = _safe_int(
                opportunity.get("expected_exit_value")
            )
            expected_profit = (
                max(expected_exit - bid_amount, 0)
                if expected_exit and bid_amount
                else 0
            )
            expected_roi = (
                expected_profit / bid_amount * 100.0
                if expected_profit and bid_amount
                else 0.0
            )

            seller_id = _actor_id(offer, "to")
            seller_obj = offer.get("to")
            seller_name = (
                seller_obj.get("name")
                if isinstance(seller_obj, dict)
                else None
            )

            position = {
                "position_id": _position_key(
                    player_id=player_id,
                    offer_id=offer_id,
                ),
                "player_id": player_id,
                "player_name": (
                    opportunity.get("name")
                    or player.get("name")
                    or f"Jugador {player_id}"
                ),
                "strategy": (
                    "SPECULATION"
                    if opportunity
                    else "ACTIVE_BID"
                ),
                "origin": "BOOTSTRAP_ACTIVE_BID",
                "status": "BID_PENDING",
                "offer_id": offer_id,
                "seller_id": seller_id,
                "seller": seller_name,
                "bid_amount": bid_amount,
                "entry_price": None,
                "bid_created_epoch": _safe_int(offer.get("created")) or None,
                "bid_until_epoch": _safe_int(offer.get("until")) or None,
                "snapshot_player_value": _safe_int(
                    opportunity.get("price")
                    or player.get("price")
                ),
                "listing_price_at_bid": _safe_int(sale.get("price")),
                "speculation_score_at_bid": round(
                    _safe_float(opportunity.get("speculation_score")),
                    2,
                ),
                "trading_score_at_bid": round(
                    _safe_float(opportunity.get("trading_score")),
                    2,
                ),
                "max_rational_bid_at_bid": _safe_int(
                    opportunity.get("max_rational_bid")
                ),
                "expected_exit_value_at_bid": expected_exit,
                "expected_profit_at_bid": expected_profit,
                "expected_roi_at_bid_percent": round(expected_roi, 2),
                "t15_after_bid": _safe_int(
                    opportunity.get("projected_t15_after_buffer")
                ),
                "current_value": _safe_int(
                    opportunity.get("price")
                    or player.get("price")
                ),
                "unrealized_profit": None,
                "unrealized_roi_percent": None,
                "opened_at": None,
                "closed_at": None,
                "realized_profit": None,
                "realized_roi_percent": None,
                "thesis_source": (
                    "CURRENT_RECONSTRUCTION"
                    if opportunity
                    else "UNKNOWN_ACTIVE_BID"
                ),
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "events": [
                    _event(
                        "BID_IMPORTED",
                        detail=(
                            "Oferta activa existente adoptada por V10.5. "
                            "La tesis es una reconstruccion actual, no una "
                            "reescritura del instante original."
                        ),
                        data={
                            "offer_id": offer_id,
                            "bid_amount": bid_amount,
                        },
                    )
                ],
            }

            ledger.setdefault("positions", []).append(position)
            created += 1
            imported.append(position.get("position_id"))

    return {
        "created": created,
        "reused": reused,
        "imported": imported,
    }


def reconcile_positions(
    ledger: dict,
    snapshot: dict,
    *,
    now_epoch: int | None = None,
) -> dict:
    now_epoch = int(now_epoch or time.time())
    squad = _squad_lookup(snapshot)
    active_by_player = _active_offer_by_player(snapshot)

    changes = []

    for position in ledger.get("positions", []) or []:
        status = str(position.get("status") or "")
        if status in TERMINAL_STATUSES:
            continue

        player_id = _safe_int(position.get("player_id"))
        if not player_id:
            continue

        squad_player = squad.get(player_id)
        active_offer = active_by_player.get(player_id)

        if status in PENDING_STATUSES:
            if squad_player is not None:
                old = status
                position["status"] = "OPEN_POSITION"
                position["entry_price"] = _safe_int(
                    position.get("bid_amount")
                )
                position["opened_at"] = _now_iso()
                position["current_value"] = _safe_int(
                    squad_player.get("price")
                )
                entry = _safe_int(position.get("entry_price"))
                current = _safe_int(position.get("current_value"))
                position["unrealized_profit"] = current - entry
                position["unrealized_roi_percent"] = round(
                    ((current - entry) / entry) * 100.0
                    if entry
                    else 0.0,
                    2,
                )
                _append_event_once(
                    position,
                    "BID_WON",
                    detail=(
                        f"Jugador detectado en plantilla. Entrada "
                        f"registrada por {entry} EUR."
                    ),
                )
                changes.append(
                    {
                        "player_id": player_id,
                        "from": old,
                        "to": "OPEN_POSITION",
                    }
                )

            elif active_offer is not None:
                old = status
                position["status"] = "BID_PENDING"

                # Conservar siempre el importe REAL de la oferta viva.
                active_amount = _safe_int(active_offer.get("amount"))
                if active_amount:
                    position["bid_amount"] = active_amount

                active_offer_id = _safe_int(active_offer.get("id"))
                if active_offer_id:
                    position["offer_id"] = active_offer_id
                    position["position_id"] = _position_key(
                        player_id=player_id,
                        offer_id=active_offer_id,
                    )

                if old != "BID_PENDING":
                    changes.append(
                        {
                            "player_id": player_id,
                            "from": old,
                            "to": "BID_PENDING",
                        }
                    )

            else:
                until = _safe_int(position.get("bid_until_epoch"))
                old = status
                if until and now_epoch >= until:
                    position["status"] = "LOST"
                    _append_event_once(
                        position,
                        "BID_LOST",
                        detail=(
                            "La oferta ya no esta activa, el jugador no "
                            "esta en plantilla y el plazo registrado ha expirado."
                        ),
                    )
                    changes.append(
                        {
                            "player_id": player_id,
                            "from": old,
                            "to": "LOST",
                        }
                    )
                else:
                    position["status"] = "BID_PENDING_UNCONFIRMED"
                    if old != "BID_PENDING_UNCONFIRMED":
                        _append_event_once(
                            position,
                            "BID_UNCONFIRMED",
                            detail=(
                                "No aparece como oferta activa, pero aun no "
                                "hay evidencia suficiente para marcarla LOST."
                            ),
                        )
                        changes.append(
                            {
                                "player_id": player_id,
                                "from": old,
                                "to": "BID_PENDING_UNCONFIRMED",
                            }
                        )

        elif status in OPEN_STATUSES:
            if squad_player is not None:
                old = status
                position["status"] = "OPEN_POSITION"
                current = _safe_int(squad_player.get("price"))
                entry = _safe_int(position.get("entry_price"))
                position["current_value"] = current
                position["unrealized_profit"] = (
                    current - entry
                    if entry
                    else None
                )
                position["unrealized_roi_percent"] = (
                    round(
                        ((current - entry) / entry) * 100.0,
                        2,
                    )
                    if entry
                    else None
                )
                if old != "OPEN_POSITION":
                    changes.append(
                        {
                            "player_id": player_id,
                            "from": old,
                            "to": "OPEN_POSITION",
                        }
                    )
            else:
                old = status
                position["status"] = "OPEN_POSITION_MISSING_REVIEW"
                if old != "OPEN_POSITION_MISSING_REVIEW":
                    _append_event_once(
                        position,
                        "POSITION_MISSING",
                        detail=(
                            "La posicion abierta ya no aparece en plantilla. "
                            "V10.5 no inventa un precio de venta; queda pendiente "
                            "de reconciliacion de venta en V10.6."
                        ),
                    )
                    changes.append(
                        {
                            "player_id": player_id,
                            "from": old,
                            "to": "OPEN_POSITION_MISSING_REVIEW",
                        }
                    )

        position["updated_at"] = _now_iso()

    return {
        "changes": changes,
        "change_count": len(changes),
    }


def ledger_summary(ledger: dict) -> dict:
    positions = ledger.get("positions", []) or []

    counts = {}
    for position in positions:
        status = str(position.get("status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1

    open_positions = [
        p for p in positions
        if str(p.get("status")) == "OPEN_POSITION"
    ]
    unrealized_profit = sum(
        _safe_int(p.get("unrealized_profit"))
        for p in open_positions
    )

    return {
        "total_positions": len(positions),
        "counts": counts,
        "open_unrealized_profit": unrealized_profit,
        "realized_profit": _safe_int(
            (ledger.get("realized", {}) or {}).get("profit_eur")
        ),
    }


def sync_position_ledger_snapshot(
    snapshot: dict,
    trader: dict | None = None,
    *,
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
    now_epoch: int | None = None,
) -> dict:
    ledger = load_ledger(ledger_path)

    bootstrap = bootstrap_active_bids(
        ledger,
        snapshot,
        trader,
    )
    reconciliation = reconcile_positions(
        ledger,
        snapshot,
        now_epoch=now_epoch,
    )

    save_ledger(ledger, ledger_path)

    return {
        "ok": True,
        "ledger_path": str(ledger_path),
        "bootstrap": bootstrap,
        "reconciliation": reconciliation,
        "summary": ledger_summary(ledger),
    }


def print_ledger(
    ledger: dict,
    *,
    path: Path | str = DEFAULT_LEDGER_PATH,
) -> None:
    summary = ledger_summary(ledger)

    print("\n" + "=" * 92)
    print("BORDALAS IA - V10.5 POSITION LEDGER")
    print("=" * 92)
    print(f"Archivo:                     {path}")
    print(f"Posiciones registradas:      {summary['total_positions']}")
    print(f"P&L no realizado:            {summary['open_unrealized_profit']:,} EUR")
    print(f"P&L realizado:               {summary['realized_profit']:,} EUR")

    positions = ledger.get("positions", []) or []
    if not positions:
        print("\nSin posiciones registradas.")
    else:
        print("\nPOSICIONES")
        print("-" * 92)
        for position in positions:
            bid = _safe_int(position.get("bid_amount"))
            entry = position.get("entry_price")
            current = position.get("current_value")
            print(
                f"{position.get('player_name')} | "
                f"{position.get('status')} | "
                f"bid={bid:,} EUR | "
                f"entry={entry if entry is not None else '-'} | "
                f"value={current if current is not None else '-'} | "
                f"strategy={position.get('strategy')}"
            )

    print("=" * 92)


def _build_current_trader(snapshot: dict) -> dict:
    # Imports perezosos para que los tests del ledger no dependan de red/API.
    from src.analysis.decision_orchestrator import build_global_decision
    from src.analysis.market_trader_shadow import build_market_trader_shadow

    decision_result = build_global_decision(snapshot)
    return build_market_trader_shadow(
        snapshot,
        decision_result=decision_result,
    )


def sync_current(
    *,
    refresh: bool = True,
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
) -> dict:
    if refresh:
        from src.collectors.league_collector import collect_league_snapshot
        collect_league_snapshot()

    from src.analysis.market_analyzer import get_latest_snapshot, load_snapshot

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)
    trader = _build_current_trader(snapshot)

    result = sync_position_ledger_snapshot(
        snapshot,
        trader,
        ledger_path=ledger_path,
    )
    result["snapshot_file"] = snapshot_file
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sync-current",
        action="store_true",
        help=(
            "Refresca Biwenger, adopta ofertas salientes activas y "
            "reconcilia BID_PENDING/WON/LOST. CERO escrituras Biwenger."
        ),
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Muestra el ledger actual.",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Usa el ultimo snapshot local para --sync-current.",
    )
    parser.add_argument(
        "--ledger-path",
        default=str(DEFAULT_LEDGER_PATH),
        help="Ruta alternativa del ledger (tests/depuracion).",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)

    if args.sync_current:
        result = sync_current(
            refresh=not args.no_refresh,
            ledger_path=ledger_path,
        )
        print("\nSYNC V10.5")
        print("-" * 92)
        print(f"Snapshot:                    {result.get('snapshot_file')}")
        print(f"Ofertas adoptadas:           {result['bootstrap']['created']}")
        print(f"Cambios de estado:           {result['reconciliation']['change_count']}")
        print(f"Escrituras Biwenger:         NO")

    ledger = load_ledger(ledger_path)
    if args.show or args.sync_current or not (args.show or args.sync_current):
        print_ledger(
            ledger,
            path=ledger_path,
        )


if __name__ == "__main__":
    main()
