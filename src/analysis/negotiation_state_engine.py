from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


OBSERVER_ONLY = True

DEFAULT_STATE_PATH = Path(
    "data/competitive_negotiations/state.json"
)

WAITING_RIVAL = "WAITING_RIVAL"
OPEN = "OPEN"
CLOSED = "CLOSED"


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def utcnow_iso() -> str:
    return (
        datetime.utcnow()
        .replace(microsecond=0)
        .isoformat()
        + "Z"
    )


def negotiation_key(
    *,
    offer_id: int | None,
    player_id: int | None,
    rival_user_id: int | None,
) -> str:
    offer_id = safe_int(
        offer_id
    )

    player_id = safe_int(
        player_id
    )

    rival_user_id = safe_int(
        rival_user_id
    )

    if offer_id > 0:
        return f"offer:{offer_id}"

    return (
        f"player:{player_id}"
        f":rival:{rival_user_id}"
    )


def empty_state() -> dict:
    return {
        "version":
            1,

        "observer_only":
            OBSERVER_ONLY,

        "negotiations":
            {},
    }


def load_negotiation_state(
    path: str | Path = DEFAULT_STATE_PATH,
) -> dict:

    path = Path(
        path
    )

    if not path.exists():
        return empty_state()

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return empty_state()

    if not isinstance(
        data,
        dict,
    ):
        return empty_state()

    data.setdefault(
        "version",
        1,
    )

    data.setdefault(
        "observer_only",
        OBSERVER_ONLY,
    )

    data.setdefault(
        "negotiations",
        {},
    )

    return data


def save_negotiation_state(
    state: dict,
    path: str | Path = DEFAULT_STATE_PATH,
) -> str:

    path = Path(
        path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return str(
        path
    )


def get_negotiation(
    *,
    state: dict,
    key: str,
) -> dict | None:

    negotiations = (
        state.get(
            "negotiations",
            {},
        )
        or {}
    )

    value = negotiations.get(
        key
    )

    if not isinstance(
        value,
        dict,
    ):
        return None

    return deepcopy(
        value
    )


def assess_incoming_offer_event(
    *,
    state: dict,
    offer_id: int | None,
    player_id: int | None,
    rival_user_id: int | None,
    rival_amount: int,
    proposed_decision: str | None,
    proposed_counter_amount: int | None = None,
) -> dict:
    """
    Idempotencia para ofertas rivales.

    La misma oferta, sin cambio del rival, NO genera una nueva respuesta
    aunque Pepe despierte cada 15 minutos.
    """

    key = negotiation_key(
        offer_id=
            offer_id,

        player_id=
            player_id,

        rival_user_id=
            rival_user_id,
    )

    current = (
        get_negotiation(
            state=
                state,

            key=
                key,
        )
    )

    rival_amount = safe_int(
        rival_amount
    )

    proposed_counter_amount = (
        safe_int(
            proposed_counter_amount
        )
        if proposed_counter_amount
        is not None
        else None
    )

    proposed_decision = str(
        proposed_decision
        or
        "HOLD"
    )

    if current is None:

        return {
            "observer_only":
                OBSERVER_ONLY,

            "key":
                key,

            "event":
                "NEW_RIVAL_OFFER",

            "action_gate":
                "ALLOW_SINGLE_RESPONSE",

            "should_respond":
                True,

            "negotiation_round":
                1,

            "rival_amount":
                rival_amount,

            "last_rival_amount":
                None,

            "our_last_counter":
                None,

            "proposed_decision":
                proposed_decision,

            "proposed_counter_amount":
                proposed_counter_amount,

            "status":
                OPEN,

            "reason":
                "Primera vez que Pepe observa esta oferta rival.",
        }

    status = str(
        current.get(
            "status"
        )
        or
        OPEN
    )

    last_rival_amount = safe_int(
        current.get(
            "last_rival_amount"
        )
    )

    our_last_counter = (
        safe_int(
            current.get(
                "our_last_counter"
            )
        )
        if current.get(
            "our_last_counter"
        )
        is not None
        else None
    )

    round_number = max(
        safe_int(
            current.get(
                "negotiation_round"
            ),
            1,
        ),
        1,
    )

    if status == CLOSED:

        return {
            "observer_only":
                OBSERVER_ONLY,

            "key":
                key,

            "event":
                "NEGOTIATION_CLOSED",

            "action_gate":
                "BLOCK",

            "should_respond":
                False,

            "negotiation_round":
                round_number,

            "rival_amount":
                rival_amount,

            "last_rival_amount":
                last_rival_amount,

            "our_last_counter":
                our_last_counter,

            "proposed_decision":
                proposed_decision,

            "proposed_counter_amount":
                proposed_counter_amount,

            "status":
                CLOSED,

            "reason":
                "La negociacion ya esta cerrada.",
        }

    if (
        status == WAITING_RIVAL
        and
        rival_amount == last_rival_amount
    ):

        return {
            "observer_only":
                OBSERVER_ONLY,

            "key":
                key,

            "event":
                "UNCHANGED_RIVAL_OFFER",

            "action_gate":
                "NO_ACTION_WAITING_RIVAL",

            "should_respond":
                False,

            "negotiation_round":
                round_number,

            "rival_amount":
                rival_amount,

            "last_rival_amount":
                last_rival_amount,

            "our_last_counter":
                our_last_counter,

            "proposed_decision":
                proposed_decision,

            "proposed_counter_amount":
                proposed_counter_amount,

            "status":
                WAITING_RIVAL,

            "reason":
                "La oferta rival no ha cambiado desde nuestra ultima respuesta.",
        }

    if rival_amount != last_rival_amount:

        return {
            "observer_only":
                OBSERVER_ONLY,

            "key":
                key,

            "event":
                "RIVAL_CHANGED_OFFER",

            "action_gate":
                "RECALCULATE",

            "should_respond":
                True,

            "negotiation_round":
                round_number
                + 1,

            "rival_amount":
                rival_amount,

            "last_rival_amount":
                last_rival_amount,

            "our_last_counter":
                our_last_counter,

            "proposed_decision":
                proposed_decision,

            "proposed_counter_amount":
                proposed_counter_amount,

            "status":
                OPEN,

            "reason":
                "El rival ha cambiado el precio; Pepe debe recalcular con el contexto actual.",
        }

    return {
        "observer_only":
            OBSERVER_ONLY,

        "key":
            key,

        "event":
            "OPEN_NEGOTIATION",

        "action_gate":
            "ALLOW_SINGLE_RESPONSE",

        "should_respond":
            True,

        "negotiation_round":
            round_number,

        "rival_amount":
            rival_amount,

        "last_rival_amount":
            last_rival_amount,

        "our_last_counter":
            our_last_counter,

        "proposed_decision":
            proposed_decision,

        "proposed_counter_amount":
            proposed_counter_amount,

        "status":
            OPEN,

        "reason":
            "Negociacion abierta y sin bloqueo de idempotencia.",
    }


def apply_observer_response(
    *,
    state: dict,
    assessment: dict,
    player_id: int | None,
    rival_user_id: int | None,
    player_name: str | None = None,
) -> dict:
    """
    Simula la transicion de estado DESPUES de responder.
    No llama a Biwenger.
    """

    updated = deepcopy(
        state
    )

    negotiations = updated.setdefault(
        "negotiations",
        {},
    )

    key = str(
        assessment.get(
            "key"
        )
    )

    decision = str(
        assessment.get(
            "proposed_decision"
        )
        or
        "HOLD"
    )

    if decision == "COUNTER_OFFER":

        next_status = WAITING_RIVAL

        counter_amount = (
            assessment.get(
                "proposed_counter_amount"
            )
        )

        our_last_counter = (
            safe_int(
                counter_amount
            )
            if counter_amount
            is not None
            else None
        )

    elif decision in {
        "ACCEPT_NOW",
        "ACCEPT_SACRIFICE_LINEUP",
        "NEVER_SELL",
    }:

        next_status = CLOSED
        our_last_counter = None

    else:

        next_status = WAITING_RIVAL
        our_last_counter = None

    negotiations[
        key
    ] = {
        "key":
            key,

        "player_id":
            safe_int(
                player_id
            ),

        "player_name":
            player_name,

        "rival_user_id":
            safe_int(
                rival_user_id
            ),

        "last_rival_amount":
            safe_int(
                assessment.get(
                    "rival_amount"
                )
            ),

        "our_last_counter":
            our_last_counter,

        "last_decision":
            decision,

        "negotiation_round":
            max(
                safe_int(
                    assessment.get(
                        "negotiation_round"
                    ),
                    1,
                ),
                1,
            ),

        "status":
            next_status,

        "updated_at":
            utcnow_iso(),
    }

    return updated
