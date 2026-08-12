from __future__ import annotations

from datetime import datetime

from src.analysis.competitive_transaction_engine import (
    calculate_computer_cycle_window,
    classify_replacement_window,
    evaluate_sale_to_rival,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fake_intelligence() -> dict:
    return {
        "managers": [
            {
                "user_id": 1,
                "name": "Pepe",
                "points": 0,
                "points_rank": None,
                "threat_score": None,
                "threat_level": "US",
            },
            {
                "user_id": 2,
                "name": "Pollo17",
                "points": 0,
                "points_rank": None,
                "threat_score": 60.8,
                "threat_level": "HIGH",
                "balance": 3_523_800,
                "maximum_bid": 15_368_800,
                "roster_value": 70_000_000,
                "market_activity": "VERY_HIGH",
                "profile": "AGGRESSIVE",
            },
        ]
    }


def deadline() -> dict:
    # Viernes 21:00.
    return {
        "first_kickoff": "2026-08-14T21:00:00",
    }


def main() -> None:
    intelligence = fake_intelligence()

    print("=" * 120)
    print("BORDALAS IA - COMPETITIVE TRANSACTIONS V1.2.1 COMPUTER WINDOW")
    print("=" * 120)

    thursday_evening = datetime(2026, 8, 13, 18, 0)
    friday_0400 = datetime(2026, 8, 14, 4, 0)
    friday_0600 = datetime(2026, 8, 14, 6, 0)
    friday_0800 = datetime(2026, 8, 14, 8, 0)

    cycle = calculate_computer_cycle_window(
        deadline_context=deadline(),
        now=thursday_evening,
    )

    assert_true(
        cycle["refresh_start"] == "2026-08-14T05:00:00",
        "El ultimo refresh debe empezar el viernes a las 05:00.",
    )
    assert_true(
        cycle["refresh_end"] == "2026-08-14T07:00:00",
        "El ultimo refresh debe terminar el viernes a las 07:00.",
    )

    before = classify_replacement_window(
        deadline_context=deadline(),
        in_lineup=True,
        replacement_status="NONE",
        now=friday_0400,
    )

    inside = classify_replacement_window(
        deadline_context=deadline(),
        in_lineup=True,
        replacement_status="NONE",
        now=friday_0600,
    )

    after = classify_replacement_window(
        deadline_context=deadline(),
        in_lineup=True,
        replacement_status="NONE",
        now=friday_0800,
    )

    assert_true(
        before["window"] == "TIGHT",
        "A las 04:00 aun queda el ultimo refresh, pero el riesgo debe ser alto.",
    )

    assert_true(
        inside["window"] == "COMPUTER_RESET_WINDOW",
        "Entre 05:00 y 07:00 estamos dentro de la ventana critica.",
    )

    assert_true(
        after["window"] == "LAST_USEFUL_CYCLE_PASSED",
        "A las 08:00 ya debe considerarse pasado el ultimo ciclo util.",
    )

    sale_before = evaluate_sale_to_rival(
        amount=4_300_000,
        market_value=4_120_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        franchise_score=35,
        strategic_score=65,
        sale_score=35,
        speculation_score=57.4,
        in_lineup=True,
        price_increment=20_000,
        current_balance=1_000_000,
        deadline_context=deadline(),
        replacement_status="NONE",
    )

    # evaluate_sale_to_rival usa datetime.now() en operacion real;
    # aqui validamos la ventana de forma aislada y el motor completo
    # con sus guardarrailes ya probados en V1.2.

    print()
    print("VENTANA COMPUTER")
    print(cycle)

    print()
    print("VIERNES 04:00")
    print(before)

    print()
    print("VIERNES 06:00")
    print(inside)

    print()
    print("VIERNES 08:00")
    print(after)

    print()
    print("MOTOR DE VENTA - ESTRUCTURA")
    print(sale_before)

    print()
    print("# COMPETITIVE TRANSACTIONS V1.2.1: OK")


if __name__ == "__main__":
    main()
