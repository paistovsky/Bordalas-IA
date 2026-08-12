from __future__ import annotations

from typing import Any

from src.analysis.competitive_safety_gate import (
    select_single_competitive_action,
)


OBSERVER_ONLY = True


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def build_competitive_shadow_decision(
    *,
    manager_offers: list[dict],
    temporal_gate: dict | None = None,
    current_balance: int | None = None,
) -> dict:
    """
    V1.9 EXECUTION SHADOW.

    Construye como maximo UNA decision competitiva que podria enviarse al
    executor en el futuro. NO llama al write client. NO modifica Biwenger.
    """

    gate_board = (
        select_single_competitive_action(
            offers=
                manager_offers,

            temporal_gate=
                temporal_gate,

            current_balance=
                current_balance,
        )
    )

    selected = (
        gate_board.get(
            "selected"
        )
    )

    if not selected:

        return {
            "observer_only":
                OBSERVER_ONLY,

            "available":
                True,

            "selected":
                None,

            "shadow_decision":
                None,

            "status":
                "NO_COMPETITIVE_ACTION",

            "would_reach_executor":
                False,

            "would_write":
                False,

            "gate_board":
                gate_board,

            "reason":
                "El Safety Gate no autoriza ninguna respuesta competitiva en este ciclo.",
        }

    gate = (
        selected.get(
            "gate",
            {},
        )
        or {}
    )

    offer_id = selected.get(
        "offer_id"
    )

    player_id = selected.get(
        "player_id"
    )

    decision = str(
        selected.get(
            "decision"
        )
        or
        gate.get(
            "decision"
        )
        or
        "UNKNOWN"
    )

    counter_amount = safe_int(
        gate.get(
            "counter_amount"
        )
    )

    # Formato deliberadamente parecido al executor real,
    # pero sin marcarlo ejecutable de verdad.
    shadow_decision = {
        "type":
            "COMPETITIVE_TRANSACTION",

        "priority":
            900,

        "action":
            decision,

        "executable":
            False,

        "shadow_only":
            True,

        "authority":
            "COMPETITIVE",

        "offer_id":
            offer_id,

        "player_id":
            player_id,

        "data":
            {
                "offer_id":
                    offer_id,

                "player_id":
                    player_id,

                "rival_name":
                    selected.get(
                        "rival_name"
                    ),

                "counter_amount":
                    (
                        counter_amount
                        if counter_amount > 0
                        else None
                    ),

                "gate":
                    gate,
            },

        "reason":
            "Decision competitiva seleccionada por Safety Gate para simulacion de executor.",
    }

    return {
        "observer_only":
            OBSERVER_ONLY,

        "available":
            True,

        "selected":
            selected,

        "shadow_decision":
            shadow_decision,

        "status":
            "SHADOW_READY",

        "would_reach_executor":
            True,

        "would_write":
            False,

        "gate_board":
            gate_board,

        "reason":
            (
                "La decision llegaria a la capa de ejecucion, "
                "pero V1.9 la intercepta antes de cualquier escritura."
            ),
    }


def execute_competitive_shadow(
    shadow: dict,
) -> dict:
    """
    Ultima barrera V1.9.

    Simula la entrada al executor y BLOQUEA siempre antes de BiwengerWriteClient.
    """

    decision = (
        shadow.get(
            "shadow_decision"
        )
        or {}
    )

    if not decision:

        return {
            "action":
                None,

            "status":
                "NO_SHADOW_ACTION",

            "write_performed":
                False,

            "success":
                True,

            "would_write":
                False,

            "reason":
                "No hay accion competitiva autorizada en este ciclo.",
        }

    return {
        "action":
            decision.get(
                "action"
            ),

        "status":
            "SHADOW_BLOCK_BEFORE_WRITE",

        "write_performed":
            False,

        "success":
            True,

        "would_write":
            True,

        "shadow_only":
            True,

        "decision":
            decision,

        "reason":
            (
                "La accion competitiva ha recorrido Authority + Negotiation + "
                "Safety Gate y alcanzaria el executor, pero V1.9 bloquea "
                "deliberadamente antes de BiwengerWriteClient."
            ),
    }
