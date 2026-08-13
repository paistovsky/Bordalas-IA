from datetime import datetime

from src.analysis.dynamic_counteroffer_repricing_v107 import (
    resolve_deadline_context_from_offer_board,
    resolve_hours_to_deadline,
)


def test_reads_real_nested_solvency_deadline():
    board = {
        "liquidity": {
            "solvency": {
                "deadline": {
                    "phase": "PREPARATION",
                    "hours_to_deadline": 27.75,
                    "real_deadline": "2026-08-15T00:45:00",
                }
            }
        }
    }

    context, source = resolve_deadline_context_from_offer_board(board)

    assert source == "OFFER_BOARD_LIQUIDITY_SOLVENCY"
    assert context["phase"] == "PREPARATION"
    assert context["hours_to_deadline"] == 27.75


def test_resolves_hours_from_nested_deadline():
    board = {
        "liquidity": {
            "solvency": {
                "deadline": {
                    "hours_to_deadline": 36.5,
                }
            }
        }
    }

    hours, source, context = resolve_hours_to_deadline(board)

    assert hours == 36.5
    assert source == "OFFER_BOARD_LIQUIDITY_SOLVENCY"
    assert context["hours_to_deadline"] == 36.5


def test_resolves_seconds_from_nested_deadline():
    board = {
        "liquidity": {
            "solvency": {
                "deadline": {
                    "seconds_to_deadline": 12 * 3600,
                }
            }
        }
    }

    hours, source, _ = resolve_hours_to_deadline(board)

    assert hours == 12.0
    assert source == "OFFER_BOARD_LIQUIDITY_SOLVENCY"


def test_legacy_deadline_is_supported():
    board = {
        "liquidity": {
            "deadline": {
                "hours_to_deadline": 48.25,
            }
        }
    }

    hours, source, _ = resolve_hours_to_deadline(board)

    assert hours == 48.25
    assert source == "OFFER_BOARD_LIQUIDITY_LEGACY"


def test_missing_deadline_is_explicit():
    board = {
        "liquidity": {
            "solvency": {}
        }
    }

    hours, source, context = resolve_hours_to_deadline(board)

    assert hours is None
    assert source == "MISSING"
    assert context == {}


def main():
    tests = [
        test_reads_real_nested_solvency_deadline,
        test_resolves_hours_from_nested_deadline,
        test_resolves_seconds_from_nested_deadline,
        test_legacy_deadline_is_supported,
        test_missing_deadline_is_explicit,
    ]

    for fn in tests:
        fn()
        print("OK ", fn.__name__)

    print("DEADLINE CONTEXT V10.7.1: 5/5 OK")


if __name__ == "__main__":
    main()
