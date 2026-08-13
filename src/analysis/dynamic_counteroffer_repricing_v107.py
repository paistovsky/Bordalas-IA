from __future__ import annotations

import argparse
import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.analysis.exact_price_policy import exact_euro


VERSION = "V10.7.1"
MODE = "SHADOW"
WRITES_BIWENGER = False

DEFAULT_STATE_PATH = Path(
    "data/trading/counteroffer_repricing_state.json"
)

ACTIVE_STATUSES = {
    "waiting",
    "pending",
    "active",
}

ACTION_PRIORITY = {
    "CANCEL_COUNTER": 100,
    "RAISE_COUNTER": 90,
    "KEEP_COUNTER": 20,
    "REVIEW_BLOCK": 10,
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


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_id(offer: dict, key: str) -> int | None:
    actor = offer.get(key)

    if isinstance(actor, dict):
        actor_id = _safe_int(actor.get("id"))
        return actor_id or None

    if isinstance(actor, int):
        return actor or None

    for field in (
        f"{key}ID",
        f"{key}_id",
        f"{key}Id",
    ):
        actor_id = _safe_int(offer.get(field))
        if actor_id:
            return actor_id

    return None


def _actor_name(offer: dict, key: str) -> str | None:
    actor = offer.get(key)
    if isinstance(actor, dict):
        return actor.get("name")
    return None


def _requested_player_ids(offer: dict) -> list[int]:
    result: list[int] = []

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

    player = offer.get("player")
    if isinstance(player, dict):
        player_id = _safe_int(player.get("id"))
        if player_id:
            result.append(player_id)
    elif isinstance(player, int):
        result.append(player)

    unique = []
    seen = set()

    for player_id in result:
        if player_id not in seen:
            unique.append(player_id)
            seen.add(player_id)

    return unique


def _catalog_lookup(snapshot: dict) -> dict[int, dict]:
    raw = (
        (snapshot.get("catalog", {}) or {})
        .get("data", {})
        .get("players", {})
        or {}
    )

    iterable = (
        raw.values()
        if isinstance(raw, dict)
        else raw
    )

    result = {}

    for player in iterable or []:
        player_id = _safe_int(player.get("id"))
        if player_id:
            result[player_id] = player

    return result


def _own_user_id(snapshot: dict) -> int:
    return _safe_int(
        (
            (snapshot.get("league", {}) or {})
            .get("user", {})
            or {}
        ).get("id")
    )


def _hours_until(until: Any, now_epoch: int | None = None) -> float | None:
    until_ts = _safe_int(until)
    if until_ts <= 0:
        return None

    now_epoch = int(now_epoch or time.time())

    return round(
        max((until_ts - now_epoch) / 3600.0, 0.0),
        2,
    )


def _pct_delta(new_value: int, old_value: int) -> float | None:
    if old_value <= 0:
        return None

    return round(
        ((new_value - old_value) / old_value) * 100.0,
        2,
    )


def empty_state() -> dict:
    return {
        "version": VERSION,
        "updated_at": _now_iso(),
        "negotiations": {},
    }


def load_state(
    path: Path | str = DEFAULT_STATE_PATH,
) -> dict:
    path = Path(path)

    if not path.exists():
        return empty_state()

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Estado V10.7 ilegible: {path}: {error}"
        )

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Estado V10.7 invalido: {path}"
        )

    payload.setdefault("version", VERSION)
    payload.setdefault("negotiations", {})

    return payload


def save_state(
    state: dict,
    path: Path | str = DEFAULT_STATE_PATH,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = deepcopy(state)
    payload["version"] = VERSION
    payload["updated_at"] = _now_iso()

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def find_active_outgoing_counteroffers(
    snapshot: dict,
) -> list[dict]:
    own_id = _own_user_id(snapshot)

    if own_id <= 0:
        return []

    result = []

    offers = (
        (snapshot.get("market", {}) or {})
        .get("offers", [])
        or []
    )

    for offer in offers:
        if str(offer.get("type") or "") != "counterOffer":
            continue

        if str(
            offer.get("status") or "waiting"
        ) not in ACTIVE_STATUSES:
            continue

        if _actor_id(offer, "from") != own_id:
            continue

        rival_id = _actor_id(offer, "to")
        if not rival_id:
            continue

        player_ids = _requested_player_ids(offer)
        if not player_ids:
            continue

        for player_id in player_ids:
            result.append({
                "counter_offer_id": _safe_int(offer.get("id")),
                "player_id": player_id,
                "rival_user_id": rival_id,
                "rival_name": _actor_name(offer, "to"),
                "current_counter_amount": _safe_int(
                    offer.get("amount")
                ),
                "created": _safe_int(offer.get("created")) or None,
                "until": _safe_int(offer.get("until")) or None,
                "raw_offer": offer,
            })

    return result


def build_incoming_offer_lookup(
    snapshot: dict,
) -> dict[tuple[int, int], dict]:
    own_id = _own_user_id(snapshot)
    result = {}

    offers = (
        (snapshot.get("market", {}) or {})
        .get("offers", [])
        or []
    )

    for offer in offers:
        if str(offer.get("type") or "") != "purchase":
            continue

        if str(
            offer.get("status") or "waiting"
        ) not in ACTIVE_STATUSES:
            continue

        rival_id = _actor_id(offer, "from")
        to_id = _actor_id(offer, "to")

        if not rival_id or to_id != own_id:
            continue

        for player_id in _requested_player_ids(offer):
            result[(player_id, rival_id)] = offer

    return result


def exact_competitive_sell_price(
    *,
    market_value: int,
    our_sale_cost_score: float,
    price_increment: int,
    competitive_premium_percent: float,
    temporal_premium_percent: float,
    sporting_premium_percent: float,
    solvency_discount_percent: float,
) -> dict:
    """
    Reproduce la lógica económica Competitive, pero sin round_money(10k).

    Precio base:
      market_value
      + coste interno de desprendernos del activo
      + premium de tendencia

    Precio final:
      base
      + daño/amenaza rival
      + coste temporal/deadline
      + coste deportivo
      - descuento de solvencia

    Todo termina al euro exacto.
    """
    market_value = max(_safe_int(market_value), 0)

    if market_value <= 0:
        return {
            "available": False,
            "base_sell_price_exact": 0,
            "strategic_sell_price_exact": 0,
            "internal_premium_percent": 0.0,
            "trend_premium_percent": 0.0,
            "total_adjustment_percent": 0.0,
        }

    cost_score = max(
        min(_safe_float(our_sale_cost_score), 100.0),
        0.0,
    )

    internal_premium_ratio = (
        _decimal(cost_score)
        / Decimal("100")
        * Decimal("0.25")
    )

    trend_premium_ratio = Decimal("0")

    if _safe_int(price_increment) >= 100_000:
        trend_premium_ratio = Decimal("0.04")
    elif _safe_int(price_increment) > 0:
        trend_premium_ratio = Decimal("0.02")

    base = (
        _decimal(market_value)
        * (
            Decimal("1")
            + internal_premium_ratio
            + trend_premium_ratio
        )
    )

    base_exact = exact_euro(base)

    total_adjustment_percent = max(
        _safe_float(competitive_premium_percent)
        + _safe_float(temporal_premium_percent)
        + _safe_float(sporting_premium_percent)
        - _safe_float(solvency_discount_percent),
        0.0,
    )

    strategic = (
        _decimal(base_exact)
        * (
            Decimal("1")
            + _decimal(total_adjustment_percent)
            / Decimal("100")
        )
    )

    strategic_exact = exact_euro(strategic)

    return {
        "available": True,
        "base_sell_price_exact": base_exact,
        "strategic_sell_price_exact": strategic_exact,
        "internal_premium_percent": round(
            float(internal_premium_ratio * Decimal("100")),
            4,
        ),
        "trend_premium_percent": round(
            float(trend_premium_ratio * Decimal("100")),
            4,
        ),
        "total_adjustment_percent": round(
            total_adjustment_percent,
            4,
        ),
    }


def build_decision_lookup(
    offer_decision_board: dict,
) -> dict[tuple[int, int], dict]:
    result = {}

    for decision in (
        offer_decision_board.get("decisions", [])
        or []
    ):
        if (
            str(decision.get("counterparty_type"))
            != "MANAGER"
        ):
            continue

        player_id = _safe_int(
            decision.get("player_id")
        )
        rival_id = _safe_int(
            decision.get("counterparty_id")
        )

        if player_id and rival_id:
            result[(player_id, rival_id)] = decision

    return result


def build_speculation_lookup(
    offer_decision_board: dict,
) -> dict[int, dict]:
    board = (
        offer_decision_board.get("speculation", {})
        or {}
    )

    return {
        _safe_int(item.get("id")): item
        for item in board.get("owned", []) or []
        if _safe_int(item.get("id"))
    }


def _negotiation_key(
    player_id: int,
    rival_user_id: int,
) -> str:
    return f"{int(player_id)}:{int(rival_user_id)}"


def evaluate_counteroffer(
    counter: dict,
    *,
    player: dict | None,
    incoming_offer: dict | None,
    competitive_decision: dict | None,
    speculation: dict | None,
    state_record: dict | None,
    hours_to_deadline: float | None = None,
    now_epoch: int | None = None,
) -> dict:
    player = player or {}
    speculation = speculation or {}
    state_record = state_record or {}

    player_id = _safe_int(counter.get("player_id"))
    rival_id = _safe_int(counter.get("rival_user_id"))
    current_counter = _safe_int(
        counter.get("current_counter_amount")
    )
    market_value = _safe_int(player.get("price"))
    price_increment = _safe_int(
        speculation.get("price_increment")
    )

    first_market_value = _safe_int(
        state_record.get("first_market_value")
    )
    last_market_value = _safe_int(
        state_record.get("last_market_value")
    )

    drift_since_first = (
        market_value - first_market_value
        if first_market_value > 0
        else 0
    )
    drift_since_last = (
        market_value - last_market_value
        if last_market_value > 0
        else 0
    )

    base = {
        "version": VERSION,
        "mode": MODE,
        "writes_biwenger": False,
        "counter_offer_id": _safe_int(
            counter.get("counter_offer_id")
        ),
        "player_id": player_id,
        "player_name": (
            player.get("name")
            or (
                competitive_decision or {}
            ).get("player_name")
            or f"Jugador {player_id}"
        ),
        "rival_user_id": rival_id,
        "rival_name": counter.get("rival_name"),
        "current_counter_amount": current_counter,
        "market_value": market_value,
        "price_increment": price_increment,
        "hours_to_counter_expiry": _hours_until(
            counter.get("until"),
            now_epoch=now_epoch,
        ),
        "hours_to_deadline": (
            round(hours_to_deadline, 2)
            if hours_to_deadline is not None
            else None
        ),
        "incoming_offer_id": (
            _safe_int(
                (incoming_offer or {}).get("id")
            )
            or None
        ),
        "incoming_amount": _safe_int(
            (incoming_offer or {}).get("amount")
        ),
        "market_drift_since_first_seen": drift_since_first,
        "market_drift_since_last_check": drift_since_last,
        "market_drift_since_first_seen_percent": (
            _pct_delta(
                market_value,
                first_market_value,
            )
            if first_market_value > 0
            else None
        ),
    }

    if market_value <= 0:
        return {
            **base,
            "action": "REVIEW_BLOCK",
            "priority": ACTION_PRIORITY["REVIEW_BLOCK"],
            "fresh_minimum": None,
            "raise_by": 0,
            "stale_counteroffer": False,
            "reason": (
                "No existe valor Biwenger fresco fiable para repricing."
            ),
            "components": {},
        }

    if competitive_decision is None:
        return {
            **base,
            "action": "REVIEW_BLOCK",
            "priority": ACTION_PRIORITY["REVIEW_BLOCK"],
            "fresh_minimum": None,
            "raise_by": 0,
            "stale_counteroffer": False,
            "reason": (
                "Existe contraoferta activa, pero no se ha podido "
                "reconstruir su contexto Competitive actual."
            ),
            "components": {},
        }

    competitive = (
        competitive_decision.get(
            "competitive_observer",
            {}
        )
        or {}
    )

    if (
        str(competitive.get("decision"))
        == "NEVER_SELL"
        or str(
            competitive_decision.get(
                "authoritative_decision"
            )
        ) == "NEVER_SELL"
    ):
        return {
            **base,
            "action": "CANCEL_COUNTER",
            "priority": ACTION_PRIORITY["CANCEL_COUNTER"],
            "fresh_minimum": None,
            "raise_by": 0,
            "stale_counteroffer": True,
            "reason": (
                "El jugador ha pasado a NEVER_SELL: mantener una "
                "contraoferta aceptable por el rival ya no es seguro."
            ),
            "components": {
                "competitive_decision": competitive.get("decision"),
            },
        }

    exact = exact_competitive_sell_price(
        market_value=market_value,
        our_sale_cost_score=_safe_float(
            competitive.get("our_sale_cost_score")
        ),
        price_increment=price_increment,
        competitive_premium_percent=_safe_float(
            competitive.get(
                "competitive_premium_percent"
            )
        ),
        temporal_premium_percent=_safe_float(
            competitive.get(
                "temporal_premium_percent"
            )
        ),
        sporting_premium_percent=_safe_float(
            competitive.get(
                "sporting_premium_percent"
            )
        ),
        solvency_discount_percent=_safe_float(
            competitive.get(
                "solvency_discount_percent"
            )
        ),
    )

    fresh_minimum = _safe_int(
        exact.get("strategic_sell_price_exact")
    )

    if fresh_minimum <= 0:
        return {
            **base,
            "action": "REVIEW_BLOCK",
            "priority": ACTION_PRIORITY["REVIEW_BLOCK"],
            "fresh_minimum": None,
            "raise_by": 0,
            "stale_counteroffer": False,
            "reason": (
                "No se ha podido calcular precio estratégico exacto."
            ),
            "components": exact,
        }

    # Regla fundamental del proyecto:
    # una contraoferta viva NO se abarata automáticamente.
    recommended_counter = max(
        current_counter,
        fresh_minimum,
    )

    raise_by = max(
        recommended_counter - current_counter,
        0,
    )

    stale = bool(
        fresh_minimum > current_counter
    )

    current_market_premium = (
        ((current_counter - market_value) / market_value) * 100.0
        if market_value > 0
        else 0.0
    )

    required_market_premium = (
        ((fresh_minimum - market_value) / market_value) * 100.0
        if market_value > 0
        else 0.0
    )

    if stale:
        action = "RAISE_COUNTER"
        reason = (
            "La contraoferta viva ha quedado por debajo del "
            "precio estratégico actualizado."
        )
    else:
        action = "KEEP_COUNTER"
        reason = (
            "La contraoferta actual sigue cubriendo el precio "
            "estratégico actualizado; no se abarata."
        )

    market_caught_counter = bool(
        market_value >= current_counter
        and current_counter > 0
    )

    if market_caught_counter:
        reason += (
            " El valor de mercado ya ha alcanzado/superado la "
            "contraoferta: STALE_COUNTEROFFER crítico."
        )

    underpricing_percent = (
        ((fresh_minimum - current_counter) / current_counter) * 100.0
        if current_counter > 0 and fresh_minimum > current_counter
        else 0.0
    )

    urgency = 0.0

    if stale:
        urgency += min(
            underpricing_percent * 4.0,
            55.0,
        )

    if market_caught_counter:
        urgency += 30.0

    if drift_since_last > 0 and last_market_value > 0:
        drift_pct = (
            drift_since_last
            / last_market_value
            * 100.0
        )
        urgency += min(
            drift_pct * 3.0,
            15.0,
        )

    if (
        hours_to_deadline is not None
        and hours_to_deadline <= 24
    ):
        urgency += 10.0
    if (
        hours_to_deadline is not None
        and hours_to_deadline <= 12
    ):
        urgency += 10.0

    urgency = round(
        max(0.0, min(urgency, 100.0)),
        1,
    )

    replacement = (
        competitive.get("replacement", {})
        or {}
    )
    rival = (
        competitive.get("rival", {})
        or {}
    )

    return {
        **base,
        "action": action,
        "priority": ACTION_PRIORITY[action],
        "recommended_counter": recommended_counter,
        "fresh_minimum": fresh_minimum,
        "raise_by": raise_by,
        "stale_counteroffer": stale,
        "market_caught_counter": market_caught_counter,
        "urgency_score": urgency,
        "current_market_premium_percent": round(
            current_market_premium,
            2,
        ),
        "required_market_premium_percent": round(
            required_market_premium,
            2,
        ),
        "reason": reason,
        "components": {
            **exact,
            "our_sale_cost_score": _safe_float(
                competitive.get("our_sale_cost_score")
            ),
            "competitive_premium_percent": _safe_float(
                competitive.get(
                    "competitive_premium_percent"
                )
            ),
            "temporal_premium_percent": _safe_float(
                competitive.get(
                    "temporal_premium_percent"
                )
            ),
            "sporting_premium_percent": _safe_float(
                competitive.get(
                    "sporting_premium_percent"
                )
            ),
            "solvency_discount_percent": _safe_float(
                competitive.get(
                    "solvency_discount_percent"
                )
            ),
            "speculation_score": _safe_float(
                competitive.get("speculation_score")
            ),
            "rival_reinforcement_score": _safe_float(
                competitive.get(
                    "rival_reinforcement_score"
                )
            ),
            "rival_threat_score": _safe_float(
                rival.get("threat_score")
            ),
            "direct_rival": bool(
                rival.get("direct_rival")
            ),
            "replacement_risk_score": _safe_float(
                replacement.get(
                    "replacement_risk_score"
                )
            ),
            "replacement_risk_level": replacement.get(
                "replacement_risk_level"
            ),
        },
    }


def build_repricing_board(
    snapshot: dict,
    *,
    offer_decision_board: dict,
    state: dict | None = None,
    hours_to_deadline: float | None = None,
    now_epoch: int | None = None,
) -> dict:
    state = state or empty_state()

    counters = find_active_outgoing_counteroffers(
        snapshot
    )
    incoming_lookup = build_incoming_offer_lookup(
        snapshot
    )
    decisions = build_decision_lookup(
        offer_decision_board
    )
    speculation_lookup = build_speculation_lookup(
        offer_decision_board
    )
    catalog = _catalog_lookup(snapshot)

    results = []

    for counter in counters:
        player_id = _safe_int(
            counter.get("player_id")
        )
        rival_id = _safe_int(
            counter.get("rival_user_id")
        )

        key = _negotiation_key(
            player_id,
            rival_id,
        )

        state_record = (
            (state.get("negotiations", {}) or {})
            .get(key, {})
            or {}
        )

        results.append(
            evaluate_counteroffer(
                counter,
                player=catalog.get(player_id),
                incoming_offer=incoming_lookup.get(
                    (player_id, rival_id)
                ),
                competitive_decision=decisions.get(
                    (player_id, rival_id)
                ),
                speculation=speculation_lookup.get(
                    player_id
                ),
                state_record=state_record,
                hours_to_deadline=hours_to_deadline,
                now_epoch=now_epoch,
            )
        )

    results.sort(
        key=lambda item: (
            _safe_int(item.get("priority")),
            _safe_float(item.get("urgency_score")),
            _safe_int(item.get("raise_by")),
        ),
        reverse=True,
    )

    return {
        "version": VERSION,
        "mode": MODE,
        "writes_biwenger": False,
        "counter_count": len(results),
        "actions": results,
        "raise_counter": [
            item
            for item in results
            if item.get("action") == "RAISE_COUNTER"
        ],
        "keep_counter": [
            item
            for item in results
            if item.get("action") == "KEEP_COUNTER"
        ],
        "cancel_counter": [
            item
            for item in results
            if item.get("action") == "CANCEL_COUNTER"
        ],
        "review_block": [
            item
            for item in results
            if item.get("action") == "REVIEW_BLOCK"
        ],
        "top_action": (
            results[0]
            if results
            else None
        ),
    }


def update_shadow_state(
    state: dict,
    board: dict,
) -> dict:
    negotiations = state.setdefault(
        "negotiations",
        {},
    )

    updated = 0
    first_seen = 0

    for action in board.get("actions", []) or []:
        player_id = _safe_int(
            action.get("player_id")
        )
        rival_id = _safe_int(
            action.get("rival_user_id")
        )

        if not player_id or not rival_id:
            continue

        key = _negotiation_key(
            player_id,
            rival_id,
        )

        record = negotiations.get(key)

        if record is None:
            record = {
                "first_seen_at": _now_iso(),
                "first_counter_offer_id": action.get(
                    "counter_offer_id"
                ),
                "initial_counter_amount": action.get(
                    "current_counter_amount"
                ),
                "first_market_value": action.get(
                    "market_value"
                ),
            }
            negotiations[key] = record
            first_seen += 1

        record["last_seen_at"] = _now_iso()
        record["last_counter_offer_id"] = action.get(
            "counter_offer_id"
        )
        record["last_counter_amount"] = action.get(
            "current_counter_amount"
        )
        record["last_market_value"] = action.get(
            "market_value"
        )
        record["last_recommended_counter"] = action.get(
            "recommended_counter"
        )
        record["last_fresh_minimum"] = action.get(
            "fresh_minimum"
        )
        record["last_action"] = action.get(
            "action"
        )
        record["last_urgency_score"] = action.get(
            "urgency_score"
        )
        updated += 1

    state["updated_at"] = _now_iso()

    return {
        "updated": updated,
        "first_seen": first_seen,
    }


def print_board(board: dict) -> None:
    print("\n" + "=" * 108)
    print("BORDALAS IA - V10.7.1 DYNAMIC COUNTEROFFER + DEADLINE FIX SHADOW")
    print("=" * 108)
    print("Escrituras Biwenger:         NO")
    print(f"Contraofertas activas:       {board.get('counter_count', 0)}")
    print(f"RAISE_COUNTER:               {len(board.get('raise_counter', []))}")
    print(f"KEEP_COUNTER:                {len(board.get('keep_counter', []))}")
    print(f"CANCEL_COUNTER:              {len(board.get('cancel_counter', []))}")
    print(f"REVIEW_BLOCK:                {len(board.get('review_block', []))}")

    actions = board.get("actions", []) or []

    if not actions:
        print("\nNo hay contraofertas activas de Pepe a managers.")
    else:
        print("\nREPRICING")
        print("-" * 108)

        for item in actions:
            components = item.get("components", {}) or {}

            print(
                f"{item.get('player_name')} -> "
                f"{item.get('rival_name') or item.get('rival_user_id')} | "
                f"{item.get('action')}"
            )
            print(
                f"  counter actual={_safe_int(item.get('current_counter_amount')):,} EUR | "
                f"mercado={_safe_int(item.get('market_value')):,} EUR | "
                f"mínimo fresco={_safe_int(item.get('fresh_minimum')):,} EUR | "
                f"recomendado={_safe_int(item.get('recommended_counter')):,} EUR"
            )
            print(
                f"  raise={_safe_int(item.get('raise_by')):+,} EUR | "
                f"premium actual={_safe_float(item.get('current_market_premium_percent')):.2f}% | "
                f"premium requerido={_safe_float(item.get('required_market_premium_percent')):.2f}% | "
                f"urgencia={_safe_float(item.get('urgency_score')):.1f}/100"
            )
            print(
                f"  drift 1ª vista={_safe_int(item.get('market_drift_since_first_seen')):+,} EUR | "
                f"última hora/check={_safe_int(item.get('market_drift_since_last_check')):+,} EUR | "
                f"deadline={item.get('hours_to_deadline')}h | "
                f"expira counter={item.get('hours_to_counter_expiry')}h"
            )
            print(
                f"  primas: competitivo={_safe_float(components.get('competitive_premium_percent')):.2f}% | "
                f"deadline/temporal={_safe_float(components.get('temporal_premium_percent')):.2f}% | "
                f"deportivo={_safe_float(components.get('sporting_premium_percent')):.2f}% | "
                f"solvencia=-{_safe_float(components.get('solvency_discount_percent')):.2f}%"
            )
            print(
                f"  daño rival={_safe_float(components.get('rival_reinforcement_score')):.1f}/100 | "
                f"threat={_safe_float(components.get('rival_threat_score')):.1f}/100 | "
                f"directo={'SI' if components.get('direct_rival') else 'NO'}"
            )
            print(
                f"  motivo: {item.get('reason')}"
            )

    print("=" * 108)
    print("V10.7.1: SHADOW. NO MODIFICA, CANCELA NI ENVIA CONTRAOFERTAS.")
    print("=" * 108)



def resolve_deadline_context_from_offer_board(
    offer_decision_board: dict,
) -> tuple[dict, str]:
    """
    V10.7.1

    build_offer_decision_board() expone:
      liquidity -> solvency -> deadline

    V10.7 buscaba por error:
      liquidity -> deadline

    Mantenemos fallbacks por compatibilidad con snapshots/boards antiguos.
    """
    liquidity = (
        offer_decision_board.get("liquidity", {})
        or {}
    )

    solvency = (
        liquidity.get("solvency", {})
        or {}
    )

    nested = (
        solvency.get("deadline", {})
        or {}
    )
    if nested:
        return nested, "OFFER_BOARD_LIQUIDITY_SOLVENCY"

    legacy = (
        liquidity.get("deadline", {})
        or {}
    )
    if legacy:
        return legacy, "OFFER_BOARD_LIQUIDITY_LEGACY"

    return {}, "MISSING"


def resolve_hours_to_deadline(
    offer_decision_board: dict,
    *,
    now=None,
) -> tuple[float | None, str, dict]:
    from src.analysis.competitive_transaction_engine import (
        extract_hours_to_deadline,
    )

    deadline_context, source = (
        resolve_deadline_context_from_offer_board(
            offer_decision_board
        )
    )

    hours = extract_hours_to_deadline(
        deadline_context,
        now=now,
    )

    return hours, source, deadline_context



def _build_current_context(snapshot: dict) -> tuple[dict, float | None]:
    """
    Reutiliza exactamente la inteligencia Competitive ya existente en el
    proyecto, pero sin ejecutar el live executor.
    """
    from src.collectors.board_history_collector import (
        collect_board_history,
    )
    from src.analysis.rival_intelligence_engine import (
        build_rival_intelligence,
    )
    from src.analysis.offer_decision_engine import (
        build_offer_decision_board,
    )
    from src.analysis.negotiation_state_engine import (
        empty_state as empty_negotiation_state,
    )
    from src.analysis.competitive_transaction_engine import (
        extract_hours_to_deadline,
    )

    history = collect_board_history()

    market_status = (
        (snapshot.get("market", {}) or {})
        .get("status", {})
        or {}
    )

    current_user_id = (
        history.get("current_user_id")
        or _own_user_id(snapshot)
    )

    rival_intelligence = build_rival_intelligence(
        events=history.get("events", []) or [],
        users=history.get("users", []) or [],
        profiles=history.get("profiles", []) or [],
        catalog=snapshot.get("catalog", {}) or {},
        current_user_id=current_user_id,
        own_finances=history.get("own_finances", {}) or {},
        own_balance=market_status.get("balance"),
        own_maximum_bid=market_status.get("maximumBid"),
    )

    offer_board = build_offer_decision_board(
        snapshot=snapshot,
        rival_intelligence=rival_intelligence,
        negotiation_state=empty_negotiation_state(),
    )

    hours_to_deadline, deadline_source, deadline_context = (
        resolve_hours_to_deadline(
            offer_board
        )
    )

    # Defensa adicional: la misma fuente de verdad que usa Orchestrator/
    # Solvency. No sustituye silenciosamente datos válidos; solo entra si
    # el board no trae el contexto esperado.
    if hours_to_deadline is None:
        try:
            from src.analysis.solvency_engine import (
                build_solvency_state,
            )

            solvency = build_solvency_state(
                snapshot
            )

            seconds = solvency.get(
                "seconds_to_deadline"
            )

            if seconds is not None:
                hours_to_deadline = max(
                    float(seconds) / 3600.0,
                    0.0,
                )
                deadline_source = (
                    "DIRECT_SOLVENCY_SECONDS_FALLBACK"
                )
                deadline_context = (
                    solvency.get("deadline", {})
                    or {}
                )
            else:
                direct_deadline = (
                    solvency.get("deadline", {})
                    or {}
                )
                direct_hours = extract_hours_to_deadline(
                    direct_deadline
                )
                if direct_hours is not None:
                    hours_to_deadline = direct_hours
                    deadline_source = (
                        "DIRECT_SOLVENCY_DEADLINE_FALLBACK"
                    )
                    deadline_context = direct_deadline

        except Exception:
            # Sigue siendo SHADOW: no ocultamos el None si ambas fuentes
            # fallan. La salida mostrará MISSING para depuración.
            pass

    return (
        offer_board,
        hours_to_deadline,
        deadline_source,
        deadline_context,
    )


def sync_current(
    *,
    refresh: bool = True,
    state_path: Path | str = DEFAULT_STATE_PATH,
) -> dict:
    if refresh:
        from src.collectors.league_collector import (
            collect_league_snapshot,
        )
        collect_league_snapshot()

    from src.analysis.market_analyzer import (
        get_latest_snapshot,
        load_snapshot,
    )

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    (
        offer_board,
        hours_to_deadline,
        deadline_source,
        deadline_context,
    ) = _build_current_context(snapshot)

    state = load_state(state_path)

    board = build_repricing_board(
        snapshot,
        offer_decision_board=offer_board,
        state=state,
        hours_to_deadline=hours_to_deadline,
    )

    state_update = update_shadow_state(
        state,
        board,
    )
    save_state(
        state,
        state_path,
    )

    return {
        "ok": True,
        "writes_biwenger": False,
        "snapshot_file": snapshot_file,
        "state_path": str(state_path),
        "hours_to_deadline": hours_to_deadline,
        "deadline_source": deadline_source,
        "deadline_context": deadline_context,
        "board": board,
        "state_update": state_update,
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sync-current",
        action="store_true",
        help=(
            "Refresca Biwenger y recalcula todas las contraofertas "
            "activas en SHADOW. CERO escrituras Biwenger."
        ),
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
    )
    parser.add_argument(
        "--state-path",
        default=str(DEFAULT_STATE_PATH),
    )

    args = parser.parse_args()

    if not args.sync_current:
        print(
            "Usa --sync-current para leer Biwenger y evaluar "
            "contraofertas activas. CERO escrituras."
        )
        return

    result = sync_current(
        refresh=not args.no_refresh,
        state_path=args.state_path,
    )

    print("\nSYNC V10.7")
    print("-" * 108)
    print(f"Snapshot:                    {result.get('snapshot_file')}")
    print(f"Estado local:                {result.get('state_path')}")
    print(f"Horas a deadline:            {result.get('hours_to_deadline')}")
    print(f"Fuente deadline:             {result.get('deadline_source')}")
    deadline = result.get("deadline_context", {}) or {}
    print(f"Fase deadline:               {deadline.get('phase')}")
    print(f"Real deadline:               {deadline.get('real_deadline')}")
    print(f"Primer kickoff:              {deadline.get('first_kickoff')}")
    print(f"Negociaciones nuevas:        {result.get('state_update', {}).get('first_seen', 0)}")
    print(f"Escrituras Biwenger:         NO")

    print_board(
        result["board"]
    )


if __name__ == "__main__":
    main()
