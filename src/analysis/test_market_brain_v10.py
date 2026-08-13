from src.analysis.decision_orchestrator import (
    build_action_queue,
    build_shadow_speculation_candidate,
)


def fake_solvency() -> dict:
    return {
        "balance": -2_000_000,
        "solvency_guarantee": {
            "state": "GUARANTEED",
            "guaranteed": True,
            "current_debt": 2_000_000,
            "safety_buffer": 500_000,
            "secured_liquidity": 5_000_000,
            "expected_liquidity": 1_000_000,
            "guaranteed_recovery": 6_000_000,
        },
        "max_safe_debt": {
            "additional_debt_headroom": 3_500_000,
            "debt_window_open": True,
            "safe_cycles_remaining": 4,
        },
        "temporary_debt": {
            "allowed": True,
        },
        "hard_safety": {
            "active": False,
        },
        "deadline": {
            "phase": "NORMAL",
            "operations_locked": False,
            "hard_safety_mode": False,
        },
    }


def test_observation_no_longer_hides_first_executable_action() -> None:
    candidates = [
        {
            "action": "MONITOR_OFFERS",
            "priority": 650,
            "executable": False,
        },
        {
            "action": "LIST_FOR_LIQUIDITY",
            "priority": 550,
            "executable": True,
        },
        {
            "action": "BUY_SPECULATION",
            "priority": 400,
            "executable": True,
        },
    ]

    queue = build_action_queue(candidates)

    assert queue[0]["action"] == "LIST_FOR_LIQUIDITY"
    assert queue[1]["action"] == "BUY_SPECULATION"


def test_shadow_queue_can_include_debt_safe_speculation() -> None:
    speculation = {
        "budget": {
            "enabled": True,
            "mode": "DEBT",
            "total_budget": 2_000_000,
            "single_operation_limit": 1_000_000,
        },
        "executable_buys": [
            {
                "id": 123,
                "name": "Jugador Test",
                "price": 800_000,
                "speculation_score": 88,
                "ownership_state": "EN_MERCADO",
            }
        ],
    }

    candidate = build_shadow_speculation_candidate(
        speculation=speculation,
        solvency=fake_solvency(),
        phase="NORMAL",
        hard_safety_mode=False,
        operations_locked=False,
    )

    assert candidate is not None
    assert candidate["action"] == "BUY_SPECULATION"
    assert candidate["executable"] is False
    assert candidate["shadow_executable"] is True
    assert candidate["data"]["t15_purchase_forecast"]["safe"] is True


def test_shadow_speculation_is_blocked_in_hard_safety() -> None:
    speculation = {
        "budget": {
            "enabled": True,
        },
        "executable_buys": [
            {
                "id": 123,
                "name": "Jugador Test",
                "price": 500_000,
            }
        ],
    }

    candidate = build_shadow_speculation_candidate(
        speculation=speculation,
        solvency=fake_solvency(),
        phase="HARD_SAFETY",
        hard_safety_mode=True,
        operations_locked=False,
    )

    assert candidate is None


def main() -> None:
    tests = [
        test_observation_no_longer_hides_first_executable_action,
        test_shadow_queue_can_include_debt_safe_speculation,
        test_shadow_speculation_is_blocked_in_hard_safety,
    ]

    for test in tests:
        test()
        print(f"OK  {test.__name__}")

    print("MARKET BRAIN V10.1: OK")


if __name__ == "__main__":
    main()
