from src.analysis.write_transport_validation_v109 import (
    select_counter_candidate,
    select_exit_candidate,
)


def test_exit_selects_real_exit():
    board = {
        "actionable": [
            {
                "player_id": 1,
                "action": "TAKE_PROFIT",
                "priority": 85,
            },
            {
                "player_id": 2,
                "action": "CUT_LOSS",
                "priority": 90,
            },
        ]
    }
    assert select_exit_candidate(board)["player_id"] == 2


def test_no_hold_as_exit():
    board = {
        "actionable": [
            {
                "player_id": 1,
                "action": "HOLD",
                "priority": 999,
            }
        ]
    }
    assert select_exit_candidate(board) is None


def test_counter_selects_raise_only():
    board = {
        "actions": [
            {
                "action": "KEEP_COUNTER",
                "incoming_offer_id": 1,
                "recommended_counter": 1_500_000,
                "urgency_score": 100,
            },
            {
                "action": "RAISE_COUNTER",
                "incoming_offer_id": 2,
                "recommended_counter": 1_463_718,
                "urgency_score": 50,
                "raise_by": 263_718,
            },
        ]
    }
    result = select_counter_candidate(board)
    assert result["incoming_offer_id"] == 2
    assert result["recommended_counter"] == 1_463_718


def test_counter_requires_incoming_offer_id():
    board = {
        "actions": [
            {
                "action": "RAISE_COUNTER",
                "incoming_offer_id": None,
                "recommended_counter": 1_463_718,
                "urgency_score": 99,
            }
        ]
    }
    assert select_counter_candidate(board) is None


def main():
    tests = [
        test_exit_selects_real_exit,
        test_no_hold_as_exit,
        test_counter_selects_raise_only,
        test_counter_requires_incoming_offer_id,
    ]

    for fn in tests:
        fn()
        print("OK ", fn.__name__)

    print("WRITE TRANSPORT VALIDATION V10.9: 4/4 OK")


if __name__ == "__main__":
    main()
