import json
import tempfile
from pathlib import Path

from src.analysis.position_ledger_v105 import (
    bootstrap_active_bids,
    empty_ledger,
    ledger_summary,
    load_ledger,
    reconcile_positions,
    record_verified_bid,
)


def base_snapshot():
    return {
        "league": {
            "user": {
                "id": 14175949,
                "name": "Pepe Bordalás",
            }
        },
        "market": {
            "status": {
                "balance": -4_651_032,
                "maximumBid": 7_203_968,
            },
            "sales": [
                {
                    "price": 1_130_000,
                    "user": {
                        "id": 14151726,
                        "name": "DiosMande a Rodri al Palancas",
                    },
                    "player": {
                        "id": 31468,
                        "name": "Hugo González",
                        "price": 1_350_000,
                    },
                }
            ],
            "offers": [],
        },
        "my_team": [],
    }


def trader():
    return {
        "opportunities": [
            {
                "id": 31468,
                "name": "Hugo González",
                "price": 1_350_000,
                "speculation_score": 89.9,
                "trading_score": 72.8,
                "max_rational_bid": 1_464_285,
                "expected_exit_value": 1_641_600,
                "projected_t15_after_buffer": 7_793_168,
            }
        ]
    }


def active_offer():
    return {
        "id": 4138078754,
        "amount": 1_390_000,
        "created": 1786646356,
        "until": 1786756955,
        "status": "waiting",
        "type": "purchase",
        "from": {
            "id": 14175949,
            "name": "Pepe Bordalás",
        },
        "to": {
            "id": 14151726,
            "name": "DiosMande a Rodri al Palancas",
        },
        "requestedPlayers": [31468],
    }


def verified_result():
    return {
        "status": "LIVE_BID_SENT_AND_VERIFIED",
        "gate": {
            "selected": {
                "id": 31468,
                "name": "Hugo González",
                "price": 1_350_000,
                "speculation_score": 89.9,
                "trading_score": 72.8,
                "max_rational_bid": 1_464_285,
                "expected_exit_value": 1_641_600,
            }
        },
        "preflight": {
            "seller_id": 14151726,
            "seller": "MANAGER: DiosMande a Rodri al Palancas",
            "current_price": 1_130_000,
        },
        "fresh_reprice": {
            "fresh_recommended_bid": 1_390_500,
            "fresh_biwenger_minimum_bid": 1_350_000,
            "fresh_listing_price": 1_130_000,
            "max_rational_bid": 1_464_285,
            "expected_exit_value": 1_641_600,
            "fresh_projected_t15_after_buffer": 7_792_668,
        },
        "execution": {
            "player_id": 31468,
            "amount": 1_390_500,
            "api_response": {
                "status": 200,
                "data": {
                    "id": 999,
                    "created": 1000,
                    "until": 2000,
                },
            },
        },
    }


def test_bootstrap_active_bid():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()

    result = bootstrap_active_bids(
        ledger,
        snapshot,
        trader(),
    )

    assert result["created"] == 1
    assert len(ledger["positions"]) == 1
    position = ledger["positions"][0]
    assert position["player_name"] == "Hugo González"
    assert position["bid_amount"] == 1_390_000
    assert position["status"] == "BID_PENDING"
    assert position["origin"] == "BOOTSTRAP_ACTIVE_BID"


def test_bootstrap_is_idempotent():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()

    bootstrap_active_bids(ledger, snapshot, trader())
    second = bootstrap_active_bids(ledger, snapshot, trader())

    assert len(ledger["positions"]) == 1
    assert second["created"] == 0
    assert second["reused"] == 1


def test_pending_stays_pending_when_offer_active():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()
    bootstrap_active_bids(ledger, snapshot, trader())

    result = reconcile_positions(
        ledger,
        snapshot,
        now_epoch=1_786_650_000,
    )

    assert ledger["positions"][0]["status"] == "BID_PENDING"
    assert result["change_count"] == 0


def test_pending_becomes_open_when_player_enters_squad():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()
    bootstrap_active_bids(ledger, snapshot, trader())

    snapshot["market"]["offers"] = []
    snapshot["my_team"] = [
        {
            "id": 31468,
            "name": "Hugo González",
            "price": 1_430_000,
        }
    ]

    result = reconcile_positions(
        ledger,
        snapshot,
        now_epoch=1_786_650_000,
    )

    p = ledger["positions"][0]
    assert p["status"] == "OPEN_POSITION"
    assert p["entry_price"] == 1_390_000
    assert p["current_value"] == 1_430_000
    assert p["unrealized_profit"] == 40_000
    assert result["change_count"] == 1


def test_pending_unconfirmed_before_expiry():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()
    bootstrap_active_bids(ledger, snapshot, trader())

    snapshot["market"]["offers"] = []
    reconcile_positions(
        ledger,
        snapshot,
        now_epoch=1_786_700_000,
    )

    assert ledger["positions"][0]["status"] == "BID_PENDING_UNCONFIRMED"


def test_pending_lost_after_expiry():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()
    bootstrap_active_bids(ledger, snapshot, trader())

    snapshot["market"]["offers"] = []
    reconcile_positions(
        ledger,
        snapshot,
        now_epoch=1_786_800_000,
    )

    assert ledger["positions"][0]["status"] == "LOST"


def test_record_verified_bid_is_persistent_and_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.json"

        first = record_verified_bid(
            verified_result(),
            ledger_path=path,
        )
        second = record_verified_bid(
            verified_result(),
            ledger_path=path,
        )

        ledger = load_ledger(path)
        assert first["registered"] is True
        assert second["registered"] is True
        assert len(ledger["positions"]) == 1
        p = ledger["positions"][0]
        assert p["origin"] == "CONTROLLED_LIVE"
        assert p["bid_amount"] == 1_390_500


def test_open_position_mark_to_market():
    snapshot = base_snapshot()
    snapshot["market"]["offers"] = [active_offer()]
    ledger = empty_ledger()
    bootstrap_active_bids(ledger, snapshot, trader())

    snapshot["market"]["offers"] = []
    snapshot["my_team"] = [
        {
            "id": 31468,
            "name": "Hugo González",
            "price": 1_500_000,
        }
    ]
    reconcile_positions(
        ledger,
        snapshot,
        now_epoch=1_786_650_000,
    )

    snapshot["my_team"][0]["price"] = 1_550_000
    reconcile_positions(
        ledger,
        snapshot,
        now_epoch=1_786_660_000,
    )

    p = ledger["positions"][0]
    assert p["status"] == "OPEN_POSITION"
    assert p["current_value"] == 1_550_000
    assert p["unrealized_profit"] == 160_000
    assert ledger_summary(ledger)["open_unrealized_profit"] == 160_000


def main():
    tests = [
        test_bootstrap_active_bid,
        test_bootstrap_is_idempotent,
        test_pending_stays_pending_when_offer_active,
        test_pending_becomes_open_when_player_enters_squad,
        test_pending_unconfirmed_before_expiry,
        test_pending_lost_after_expiry,
        test_record_verified_bid_is_persistent_and_idempotent,
        test_open_position_mark_to_market,
    ]

    for fn in tests:
        fn()
        print("OK ", fn.__name__)

    print("POSITION LEDGER V10.5: 8/8 OK")


if __name__ == "__main__":
    main()
