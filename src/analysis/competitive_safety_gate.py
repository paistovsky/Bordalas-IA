from __future__ import annotations

from typing import Any

OBSERVER_ONLY = True
RESPONDING_GATES = {"ALLOW_SINGLE_RESPONSE", "RECALCULATE"}
SUPPORTED_DECISIONS = {
    "COUNTER_OFFER",
    "ACCEPT_NOW",
    "ACCEPT_SACRIFICE_LINEUP",
    "NEVER_SELL",
}


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def evaluate_competitive_safety_gate(
    *,
    offer: dict,
    temporal_gate: dict | None = None,
    current_balance: int | None = None,
) -> dict:
    """V1.8 DRY RUN: decide si una respuesta competitiva podria ejecutarse."""
    temporal_gate = temporal_gate or {}
    negotiation = offer.get("negotiation", {}) or {}
    replacement_detail = offer.get("replacement_detail", {}) or {}

    authority = str(offer.get("decision_authority") or "LEGACY")
    decision = str(
        offer.get("authoritative_decision")
        or offer.get("competitive_decision")
        or "HOLD"
    )
    action_gate = str(negotiation.get("action_gate") or "UNKNOWN")
    should_respond = bool(negotiation.get("should_respond", False))
    rival_amount = safe_int(offer.get("amount"))
    strategic_price = safe_int(offer.get("strategic_sell_price"))
    counter_amount = safe_int(
        offer.get("authoritative_counter_amount")
        or offer.get("counter_amount")
    )
    lineup_after = safe_int(
        replacement_detail.get("post_sale_playable_count")
    )
    missing_after = max(11 - lineup_after, 0)
    protection = str(offer.get("protection") or "")

    def block(status: str, reason: str) -> dict:
        return {
            "observer_only": True,
            "authorized": False,
            "status": status,
            "would_execute": False,
            "decision": decision,
            "reason": reason,
        }

    if authority != "COMPETITIVE":
        return block("BLOCK_AUTHORITY", "Competitive no figura como autoridad.")

    if temporal_gate.get("operations_locked", False):
        return block(
            "BLOCK_TEMPORAL_LOCK",
            f"Operaciones bloqueadas por fase {temporal_gate.get('phase', 'UNKNOWN')}.",
        )

    if protection == "NEVER_AUTO_SELL":
        return block("BLOCK_PROTECTED_PLAYER", "Jugador NEVER_AUTO_SELL.")

    if decision not in SUPPORTED_DECISIONS:
        return block(
            "BLOCK_UNSUPPORTED_DECISION",
            f"Decision competitiva no ejecutable: {decision}.",
        )

    if decision == "NEVER_SELL":
        return block("BLOCK_NEVER_SELL", "Competitive ha decidido no vender.")

    if action_gate not in RESPONDING_GATES or not should_respond:
        return block(
            "BLOCK_NEGOTIATION_STATE",
            f"La negociacion no autoriza respuesta ahora: {action_gate}.",
        )

    if decision == "COUNTER_OFFER":
        if counter_amount <= 0:
            return block("BLOCK_INVALID_COUNTER", "Contraoferta sin importe valido.")
        if strategic_price > 0 and counter_amount < strategic_price:
            return block(
                "BLOCK_COUNTER_BELOW_STRATEGIC",
                "Contraoferta por debajo del precio estrategico vigente.",
            )

    if decision in {"ACCEPT_NOW", "ACCEPT_SACRIFICE_LINEUP"}:
        if rival_amount <= 0:
            return block("BLOCK_INVALID_RIVAL_AMOUNT", "Oferta rival sin importe valido.")
        if (
            decision == "ACCEPT_NOW"
            and strategic_price > 0
            and rival_amount < strategic_price
        ):
            return block(
                "BLOCK_ACCEPT_BELOW_STRATEGIC",
                "Oferta rival por debajo del precio estrategico vigente.",
            )

    # No exigimos 11/11: Pepe puede sacrificar conscientemente un hueco
    # si una oferta extraordinaria lo compensa. Pero exigimos que el motor
    # haya simulado explicitamente el XI postventa.
    if not replacement_detail or lineup_after <= 0:
        return block(
            "BLOCK_MISSING_LINEUP_REVALIDATION",
            "Falta simulacion valida del XI post-operacion.",
        )

    return {
        "observer_only": True,
        "authorized": True,
        "status": "ALLOW_DRY_RUN",
        "would_execute": False,
        "decision": decision,
        "counter_amount": counter_amount if decision == "COUNTER_OFFER" else None,
        "rival_amount": rival_amount,
        "strategic_price": strategic_price,
        "lineup_after": lineup_after,
        "missing_after": missing_after,
        "current_balance": (
            safe_int(current_balance) if current_balance is not None else None
        ),
        "reason": (
            "Barreras V1.8 superadas para una unica respuesta, "
            "pero esta version sigue en DRY RUN."
        ),
    }


def select_single_competitive_action(
    *,
    offers: list[dict],
    temporal_gate: dict | None = None,
    current_balance: int | None = None,
) -> dict:
    """Selecciona como maximo UNA respuesta por ciclo. Nunca escribe."""
    evaluations = []

    for offer in offers:
        result = evaluate_competitive_safety_gate(
            offer=offer,
            temporal_gate=temporal_gate,
            current_balance=current_balance,
        )
        evaluations.append({
            "player_id": offer.get("player_id"),
            "player_name": offer.get("player_name"),
            "rival_name": offer.get("rival_name"),
            "offer_id": offer.get("offer_id"),
            "decision": offer.get("authoritative_decision"),
            "gate": result,
        })

    authorized = [
        item for item in evaluations
        if item.get("gate", {}).get("authorized", False)
    ]

    selected = authorized[0] if authorized else None

    return {
        "observer_only": True,
        "evaluated_count": len(evaluations),
        "authorized_count": len(authorized),
        "selected_count": 1 if selected else 0,
        "selected": selected,
        "evaluations": evaluations,
        "one_action_per_cycle": True,
        "would_execute": False,
    }
