from datetime import datetime, timedelta, timezone

from src.actions.autopilot_executor import (
    validate_temporal_write_gate,
)
from src.analysis.decision_orchestrator import (
    PRIORITY,
    calculate_accept_expiry_priority,
)
from src.analysis.matchday_calendar_engine import (
    classify_phase,
)
from src.autopilot import select_live_decision


def test_monitor_does_not_hide_executable_solvency_action():
    monitor = {
        "action": "MONITOR_SOLVENCY",
        "priority": PRIORITY["EMERGENCY_SOLVENCY"],
        "executable": False,
    }
    accept = {
        "action": "ACCEPT_CLUSTER_BEFORE_EXPIRY",
        "priority": PRIORITY["EMERGENCY_SOLVENCY"] + 10,
        "executable": True,
    }

    selected = select_live_decision(
        {
            "decision": monitor,
            "action_decision": accept,
        }
    )

    assert selected is accept


def test_negative_urgent_solvency_beats_xi_and_market():
    priority = calculate_accept_expiry_priority(
        balance=-4_651_032,
        phase="HIGH_ATTENTION",
    )

    assert priority > PRIORITY["EMERGENCY_LINEUP"]
    assert priority > PRIORITY["LINEUP_UPDATE_EMERGENCY"]
    assert priority > PRIORITY["COMPUTER_OFFER_REROLL_WATCH"]


def test_positive_balance_keeps_normal_offer_priority():
    priority = calculate_accept_expiry_priority(
        balance=1,
        phase="HIGH_ATTENTION",
    )

    assert priority == PRIORITY["ACCEPT_EXPIRY_URGENT"]


def test_t15_is_a_lock_not_an_execution_window():
    deadline = datetime(
        2026,
        8,
        15,
        19,
        15,
        tzinfo=timezone(timedelta(hours=2)),
    )
    target = {
        "first_kickoff": (
            deadline + timedelta(minutes=15)
        ).isoformat(),
        "real_deadline": deadline.isoformat(),
        "safety_deadline": (
            deadline - timedelta(minutes=75)
        ).isoformat(),
    }

    assert classify_phase(
        target,
        deadline - timedelta(hours=6),
        False,
    ) == "HIGH_ATTENTION"

    assert classify_phase(
        target,
        deadline - timedelta(minutes=45),
        False,
    ) == "HARD_SAFETY"

    assert classify_phase(
        target,
        deadline,
        False,
    ) == "ROUND_LOCKED"


def test_accept_is_allowed_during_hard_safety():
    decision = {
        "action": "ACCEPT_CLUSTER_BEFORE_EXPIRY",
        "executable": True,
        "temporal_gate": {
            "phase": "HARD_SAFETY",
            "operations_locked": False,
            "hard_safety_mode": True,
        },
    }

    assert validate_temporal_write_gate(decision) is None


def main():
    tests = [
        test_monitor_does_not_hide_executable_solvency_action,
        test_negative_urgent_solvency_beats_xi_and_market,
        test_positive_balance_keeps_normal_offer_priority,
        test_t15_is_a_lock_not_an_execution_window,
        test_accept_is_allowed_during_hard_safety,
    ]

    for test in tests:
        test()
        print("OK ", test.__name__)

    print("LIVE SOLVENCY AUTHORITY V11.5: 5/5 OK")


if __name__ == "__main__":
    main()
