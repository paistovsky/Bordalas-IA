import json
import tempfile

from pathlib import Path
from unittest.mock import patch

import src.telemetry.dashboard_state as dashboard_state


def _record(timestamp, phase, action, *, write, status, success=True):
    return {
        "timestamp": timestamp,
        "log_phase": phase,
        "decision_action": "MONITOR_SOLVENCY",
        "execution": {
            "action": action,
            "status": status,
            "write_performed": write,
            "success": success,
            "http_status": 200 if write else None,
            "reason": "Prueba de telemetria.",
        },
    }


def test_pre_and_post_write_are_one_verified_activity():
    records = [
        _record(
            "2026-08-14T20:08:02",
            "PRE_ACTION",
            "REROLL_COMPUTER_OFFER",
            write=True,
            status="OFFER_REROLLED",
        ),
        _record(
            "2026-08-14T20:08:52",
            "POST_ACTION",
            "REROLL_COMPUTER_OFFER",
            write=True,
            status="OFFER_REROLLED",
        ),
        _record(
            "2026-08-14T20:09:10",
            "PRE_ACTION",
            "MONITOR_SOLVENCY",
            write=False,
            status="NOT_EXECUTABLE",
        ),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "autopilot_log.jsonl"
        path.write_text(
            "\n".join(json.dumps(item) for item in records) + "\n",
            encoding="utf-8",
        )

        with patch.object(dashboard_state, "AUTOPILOT_LOG", path):
            activity = dashboard_state.load_activity_feed()

    writes = [item for item in activity if item["write_performed"]]
    assert len(activity) == 2
    assert len(writes) == 1
    assert writes[0]["action"] == "REROLL_COMPUTER_OFFER"
    assert writes[0]["verified_post_action"] is True
    assert writes[0]["started_at"] == "2026-08-14T20:08:02"


def test_cycle_status_preserves_real_autopilot_action():
    cycle, last_execution = dashboard_state.build_execution_telemetry(
        activity=[],
        cycle_status={
            "version": "V10.13",
            "timestamp": "2026-08-14T20:10:00+00:00",
            "write_used": True,
            "action_taken": "REROLL_COMPUTER_OFFER",
            "execution": {
                "source": "AUTOPILOT",
                "action": "REROLL_COMPUTER_OFFER",
                "status": "OFFER_REROLLED",
                "write_performed": True,
                "success": True,
                "http_status": 200,
            },
            "snapshot_policy": {
                "legacy_post_write": True,
                "v10_post_write": False,
            },
        },
    )

    assert cycle["action"] == "REROLL_COMPUTER_OFFER"
    assert cycle["label"] == "Pedir nueva oferta a Computer"
    assert cycle["post_write_verified"] is True
    assert last_execution["source"] == "AUTOPILOT"
    assert last_execution["verified_post_action"] is True


def test_old_cycle_status_falls_back_to_verified_history():
    history = {
        "timestamp": "2026-08-14T20:08:52",
        "action": "REROLL_COMPUTER_OFFER",
        "label": "Pedir nueva oferta a Computer",
        "write_performed": True,
        "success": True,
        "status": "OFFER_REROLLED",
        "verified_post_action": True,
    }
    cycle, last_execution = dashboard_state.build_execution_telemetry(
        activity=[history],
        cycle_status={
            "version": "V10.12",
            "write_used": True,
            "action_taken": None,
        },
    )

    assert cycle["action"] is None
    assert last_execution is history


def main():
    tests = [
        test_pre_and_post_write_are_one_verified_activity,
        test_cycle_status_preserves_real_autopilot_action,
        test_old_cycle_status_falls_back_to_verified_history,
    ]
    for test in tests:
        test()
        print("OK ", test.__name__)
    print("DASHBOARD EXECUTION TELEMETRY V12.1: 3/3 OK")


if __name__ == "__main__":
    main()
