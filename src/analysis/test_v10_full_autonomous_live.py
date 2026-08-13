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


def main():
    tests = [
        test_best_exit_ignores_hold,
        test_best_raise_requires_original_offer,
        test_best_raise_keeps_exact_euro,
    ]
    for fn in tests:
        fn()
        print("OK ", fn.__name__)
    print("V10.10 FULL AUTONOMOUS LIVE: 3/3 OK")


if __name__ == "__main__":
    main()
