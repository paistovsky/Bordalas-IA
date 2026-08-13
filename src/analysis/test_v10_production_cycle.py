from pathlib import Path
import tempfile

from src.v10_production_cycle import (
    counter_repricing_due,
    write_attempt_used,
)


def test_legacy_write_blocks_second_write():
    cycle = {
        "execution": {
            "write_performed": True,
            "success": True,
        },
        "competitive_execution": {
            "write_performed": False,
        },
    }
    assert write_attempt_used(cycle) is True


def test_competitive_write_blocks_second_write():
    cycle = {
        "execution": {
            "write_performed": False,
        },
        "competitive_execution": {
            "write_performed": True,
            "success": True,
        },
    }
    assert write_attempt_used(cycle) is True


def test_no_write_leaves_v10_buy_slot_free():
    cycle = {
        "execution": {
            "write_performed": False,
        },
        "competitive_execution": {
            "write_performed": False,
        },
    }
    assert write_attempt_used(cycle) is False


def test_counter_runs_when_state_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "missing.json"
        assert counter_repricing_due(
            path,
            now=10_000,
        ) is True


def main():
    tests = [
        test_legacy_write_blocks_second_write,
        test_competitive_write_blocks_second_write,
        test_no_write_leaves_v10_buy_slot_free,
        test_counter_runs_when_state_missing,
    ]
    for fn in tests:
        fn()
        print("OK ", fn.__name__)
    print("V10.8 PRODUCTION COORDINATOR: 4/4 OK")


if __name__ == "__main__":
    main()
