from src.analysis.solvency_engine import (
    build_t15_solvency_forecast,
    evaluate_purchase_at_t15,
)


def fake_solvency(
    *,
    balance: int,
    recovery: int,
    buffer: int = 500_000,
    headroom: int,
    debt_allowed: bool = True,
    debt_window_open: bool = True,
    phase: str = "NORMAL",
) -> dict:
    current_debt = max(-balance, 0)

    return {
        "balance": balance,
        "solvency_guarantee": {
            "state": "GUARANTEED",
            "guaranteed": True,
            "current_debt": current_debt,
            "safety_buffer": buffer,
            "secured_liquidity": recovery,
            "expected_liquidity": 0,
            "guaranteed_recovery": recovery,
        },
        "max_safe_debt": {
            "additional_debt_headroom": headroom,
            "debt_window_open": debt_window_open,
            "safe_cycles_remaining": 4,
        },
        "temporary_debt": {
            "allowed": debt_allowed,
        },
        "hard_safety": {
            "active": False,
        },
        "deadline": {
            "phase": phase,
            "operations_locked": False,
            "hard_safety_mode": False,
        },
    }


def test_negative_balance_can_keep_investing_when_t15_is_safe() -> None:
    solvency = fake_solvency(
        balance=-4_000_000,
        recovery=8_000_000,
        headroom=3_500_000,
    )

    forecast = build_t15_solvency_forecast(
        solvency
    )

    assert forecast["projected_t15_balance"] == 4_000_000
    assert forecast["projected_t15_after_buffer"] == 3_500_000
    assert forecast["can_increase_debt"] is True

    purchase = evaluate_purchase_at_t15(
        solvency,
        1_000_000,
    )

    assert purchase["safe"] is True
    assert purchase["balance_after_purchase"] == -5_000_000
    assert purchase["projected_t15_after_buffer"] == 2_500_000


def test_purchase_is_rejected_if_it_consumes_t15_buffer() -> None:
    solvency = fake_solvency(
        balance=-4_000_000,
        recovery=8_000_000,
        headroom=3_500_000,
    )

    purchase = evaluate_purchase_at_t15(
        solvency,
        4_000_000,
    )

    assert purchase["safe"] is False
    assert purchase["projected_t15_after_buffer"] < 0


def test_positive_cash_plus_safe_debt_is_deployable_capital() -> None:
    solvency = fake_solvency(
        balance=2_000_000,
        recovery=3_000_000,
        headroom=2_500_000,
    )

    forecast = build_t15_solvency_forecast(
        solvency
    )

    assert forecast["safe_spend_capacity"] == 4_500_000

    purchase = evaluate_purchase_at_t15(
        solvency,
        4_000_000,
    )

    assert purchase["safe"] is True
    assert purchase["balance_after_purchase"] == -2_000_000


def test_closed_debt_window_blocks_new_debt() -> None:
    solvency = fake_solvency(
        balance=-1_000_000,
        recovery=5_000_000,
        headroom=3_500_000,
        debt_window_open=False,
    )

    purchase = evaluate_purchase_at_t15(
        solvency,
        500_000,
    )

    assert purchase["safe"] is False
    assert purchase["debt_ok"] is False


def main() -> None:
    tests = [
        test_negative_balance_can_keep_investing_when_t15_is_safe,
        test_purchase_is_rejected_if_it_consumes_t15_buffer,
        test_positive_cash_plus_safe_debt_is_deployable_capital,
        test_closed_debt_window_blocks_new_debt,
    ]

    for test in tests:
        test()
        print(f"OK  {test.__name__}")

    print("SOLVENCY FORECAST V10: OK")


if __name__ == "__main__":
    main()
