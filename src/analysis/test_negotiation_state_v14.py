from __future__ import annotations

from src.analysis.negotiation_state_engine import (
    apply_observer_response,
    assess_incoming_offer_event,
    empty_state,
)


def assert_true(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(
            message
        )


def main() -> None:

    state = empty_state()

    first = assess_incoming_offer_event(
        state=
            state,

        offer_id=
            123,

        player_id=
            10,

        rival_user_id=
            2,

        rival_amount=
            4_300_000,

        proposed_decision=
            "COUNTER_OFFER",

        proposed_counter_amount=
            5_480_000,
    )

    assert_true(
        first[
            "should_respond"
        ],
        "La primera oferta debe permitir una respuesta.",
    )

    state = apply_observer_response(
        state=
            state,

        assessment=
            first,

        player_id=
            10,

        rival_user_id=
            2,

        player_name=
            "Jutgla",
    )

    repeat = assess_incoming_offer_event(
        state=
            state,

        offer_id=
            123,

        player_id=
            10,

        rival_user_id=
            2,

        rival_amount=
            4_300_000,

        proposed_decision=
            "COUNTER_OFFER",

        proposed_counter_amount=
            5_500_000,
    )

    assert_true(
        repeat[
            "action_gate"
        ]
        ==
        "NO_ACTION_WAITING_RIVAL",
        "La misma oferta 15 minutos despues no debe generar otra contraoferta.",
    )

    changed = assess_incoming_offer_event(
        state=
            state,

        offer_id=
            123,

        player_id=
            10,

        rival_user_id=
            2,

        rival_amount=
            5_000_000,

        proposed_decision=
            "COUNTER_OFFER",

        proposed_counter_amount=
            5_650_000,
    )

    assert_true(
        changed[
            "action_gate"
        ]
        ==
        "RECALCULATE",
        "Si el rival cambia el precio, Pepe debe recalcular.",
    )

    assert_true(
        changed[
            "negotiation_round"
        ]
        ==
        2,
        "El cambio del rival debe abrir una nueva ronda.",
    )

    print("=" * 110)
    print("BORDALAS IA - NEGOTIATION STATE V1.4")
    print("=" * 110)

    print()
    print("PRIMER EVENTO")
    print(first)

    print()
    print("MISMA OFERTA 15 MIN DESPUES")
    print(repeat)

    print()
    print("RIVAL CAMBIA OFERTA")
    print(changed)

    print()
    print("# NEGOTIATION STATE V1.4: OK")


if __name__ == "__main__":
    main()
