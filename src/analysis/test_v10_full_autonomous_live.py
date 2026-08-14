import tempfile

from pathlib import Path
from unittest.mock import patch

import src.v10_full_autonomous_live as coordinator

from src.v10_full_autonomous_live import (
    _best_exit,
    _best_raise,
)


def test_best_exit_ignores_hold():
    board = {
        "actionable": [
            {"action": "HOLD", "player_id": 1, "priority": 999},
            {"action": "TAKE_PROFIT", "player_id": 2, "priority": 80},
        ]
    }
    assert _best_exit(board)["player_id"] == 2


def test_best_raise_requires_original_offer():
    board = {
        "actions": [
            {
                "action": "RAISE_COUNTER",
                "incoming_offer_id": None,
                "recommended_counter": 1234567,
                "urgency_score": 100,
            }
        ]
    }
    assert _best_raise(board) is None


def test_best_raise_keeps_exact_euro():
    board = {
        "actions": [
            {
                "action": "RAISE_COUNTER",
                "incoming_offer_id": 9,
                "recommended_counter": 1463718,
                "urgency_score": 50,
                "raise_by": 1001,
            }
        ]
    }
    item = _best_raise(board)
    assert item["recommended_counter"] == 1463718


def test_full_cycle_reuses_initial_snapshot():
    cycle = {
        "execution": {"write_performed": False},
        "competitive_execution": {"write_performed": False},
        "post_action": None,
    }

    with tempfile.TemporaryDirectory() as tmp:
        with (
            patch.object(
                coordinator,
                "STATUS_PATH",
                Path(tmp) / "status.json",
            ),
            patch.object(
                coordinator,
                "run_cycle",
                return_value=cycle,
            ),
            patch.object(
                coordinator,
                "build_controlled_run",
                return_value={"writes_biwenger": False},
            ) as buy,
            patch.object(
                coordinator,
                "print_controlled_buy",
            ),
            patch.object(
                coordinator,
                "sync_position_manager",
                return_value={"board": {}},
            ) as position,
            patch.object(
                coordinator,
                "print_position_manager",
            ),
            patch.object(
                coordinator,
                "sync_counter_repricing",
                return_value={"board": {}},
            ) as counter,
            patch.object(
                coordinator,
                "print_counter_repricing",
            ),
            patch.object(
                coordinator,
                "refresh_snapshot",
            ) as refresh,
        ):
            payload = coordinator.run_full_autonomous_cycle()

    buy.assert_called_once_with(
        refresh=False,
        execute_live=True,
        live_confirmation="BORDALAS",
    )
    position.assert_called_once_with(refresh=False)
    counter.assert_called_once_with(refresh=False)
    refresh.assert_not_called()
    assert payload["snapshot_policy"]["maximum_full_reads"] == 2


def test_full_cycle_reports_autopilot_write():
    execution = {
        "action": "REROLL_COMPUTER_OFFER",
        "status": "OFFER_REROLLED",
        "write_performed": True,
        "success": True,
        "http_status": 200,
        "reason": "Oferta Computer rechazada tras revalidacion fresca.",
    }
    cycle = {
        "execution": execution,
        "competitive_execution": {"write_performed": False},
        "post_action": {"snapshot_file": "post.json"},
    }

    with tempfile.TemporaryDirectory() as tmp:
        with (
            patch.object(
                coordinator,
                "STATUS_PATH",
                Path(tmp) / "status.json",
            ),
            patch.object(
                coordinator,
                "run_cycle",
                return_value=cycle,
            ),
            patch.object(
                coordinator,
                "build_controlled_run",
            ) as buy,
            patch.object(
                coordinator,
                "sync_position_manager",
                return_value={"board": {}},
            ),
            patch.object(
                coordinator,
                "print_position_manager",
            ),
            patch.object(
                coordinator,
                "sync_counter_repricing",
                return_value={"board": {}},
            ),
            patch.object(
                coordinator,
                "print_counter_repricing",
            ),
        ):
            payload = coordinator.run_full_autonomous_cycle()

    buy.assert_not_called()
    assert payload["action_taken"] == "REROLL_COMPUTER_OFFER"
    assert payload["execution"]["source"] == "AUTOPILOT"
    assert payload["execution"]["status"] == "OFFER_REROLLED"
    assert payload["execution"]["write_performed"] is True
    assert payload["execution"]["success"] is True


def main():
    tests = [
        test_best_exit_ignores_hold,
        test_best_raise_requires_original_offer,
        test_best_raise_keeps_exact_euro,
        test_full_cycle_reuses_initial_snapshot,
        test_full_cycle_reports_autopilot_write,
    ]
    for fn in tests:
        fn()
        print("OK ", fn.__name__)
    print("V10.13 FULL AUTONOMOUS LIVE: 5/5 OK")


if __name__ == "__main__":
    main()
