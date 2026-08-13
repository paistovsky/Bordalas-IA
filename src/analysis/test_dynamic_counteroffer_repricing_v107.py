from src.analysis.dynamic_counteroffer_repricing_v107 import (
    build_incoming_offer_lookup,
    build_repricing_board,
    empty_state,
    evaluate_counteroffer,
    exact_competitive_sell_price,
    find_active_outgoing_counteroffers,
    update_shadow_state,
)


def snapshot_with_counter(
    *,
    counter_amount=1_200_000,
    market_value=1_200_000,
):
    return {
        "league": {
            "user": {
                "id": 100,
                "name": "Pepe",
            }
        },
        "market": {
            "offers": [
                {
                    "id": 10,
                    "type": "purchase",
                    "amount": 900_000,
                    "status": "waiting",
                    "from": {
                        "id": 200,
                        "name": "Pollo17",
                    },
                    "to": {
                        "id": 100,
                        "name": "Pepe",
                    },
                    "requestedPlayers": [1],
                },
                {
                    "id": 11,
                    "type": "counterOffer",
                    "amount": counter_amount,
                    "status": "waiting",
                    "created": 1_000,
                    "until": 999_999_999_9,
                    "from": {
                        "id": 100,
                        "name": "Pepe",
                    },
                    "to": {
                        "id": 200,
                        "name": "Pollo17",
                    },
                    "requestedPlayers": [1],
                },
            ]
        },
        "catalog": {
            "data": {
                "players": {
                    "1": {
                        "id": 1,
                        "name": "Ximo Navarro",
                        "price": market_value,
                    }
                }
            }
        },
    }


def competitive_board(
    *,
    decision="COUNTER_OFFER",
    our_sale_cost=40.0,
    competitive=10.0,
    temporal=5.0,
    sporting=4.0,
    solvency=0.0,
    increment=0,
):
    return {
        "decisions": [
            {
                "offer_id": 10,
                "player_id": 1,
                "player_name": "Ximo Navarro",
                "counterparty_type": "MANAGER",
                "counterparty_id": 200,
                "counterparty_name": "Pollo17",
                "authoritative_decision": decision,
                "competitive_observer": {
                    "decision": decision,
                    "our_sale_cost_score": our_sale_cost,
                    "competitive_premium_percent": competitive,
                    "temporal_premium_percent": temporal,
                    "sporting_premium_percent": sporting,
                    "solvency_discount_percent": solvency,
                    "speculation_score": 75,
                    "rival_reinforcement_score": 80,
                    "rival": {
                        "threat_score": 85,
                        "direct_rival": True,
                    },
                    "replacement": {
                        "replacement_risk_score": 60,
                        "replacement_risk_level": "HIGH",
                    },
                },
            }
        ],
        "speculation": {
            "owned": [
                {
                    "id": 1,
                    "price_increment": increment,
                }
            ]
        },
    }


def test_detects_active_counteroffer():
    snapshot = snapshot_with_counter()
    counters = find_active_outgoing_counteroffers(snapshot)
    assert len(counters) == 1
    assert counters[0]["player_id"] == 1
    assert counters[0]["rival_user_id"] == 200
    assert counters[0]["current_counter_amount"] == 1_200_000


def test_pairs_original_incoming_offer():
    snapshot = snapshot_with_counter()
    lookup = build_incoming_offer_lookup(snapshot)
    assert lookup[(1, 200)]["id"] == 10


def test_exact_price_has_no_10k_rounding():
    result = exact_competitive_sell_price(
        market_value=1_234_567,
        our_sale_cost_score=41.3,
        price_increment=25_001,
        competitive_premium_percent=11.25,
        temporal_premium_percent=4.75,
        sporting_premium_percent=6.2,
        solvency_discount_percent=1.1,
    )
    assert result["available"] is True
    # Lo importante: no debe forzarse a 0/5/10k.
    assert result["strategic_sell_price_exact"] % 5_000 != 0
    assert result["strategic_sell_price_exact"] % 10_000 != 0


def test_market_catches_old_counter_and_pepe_raises():
    snapshot = snapshot_with_counter(
        counter_amount=1_200_000,
        market_value=1_200_000,
    )
    state = empty_state()
    state["negotiations"]["1:200"] = {
        "first_market_value": 900_000,
        "last_market_value": 1_150_000,
    }

    board = build_repricing_board(
        snapshot,
        offer_decision_board=competitive_board(
            increment=60_000,
        ),
        state=state,
        hours_to_deadline=36,
        now_epoch=2_000,
    )

    action = board["actions"][0]

    assert action["action"] == "RAISE_COUNTER"
    assert action["market_caught_counter"] is True
    assert action["fresh_minimum"] > 1_200_000
    assert action["recommended_counter"] == action["fresh_minimum"]
    assert action["raise_by"] > 0
    assert action["market_drift_since_first_seen"] == 300_000
    assert action["market_drift_since_last_check"] == 50_000


def test_never_lowers_counter():
    snapshot = snapshot_with_counter(
        counter_amount=2_000_123,
        market_value=1_000_000,
    )

    board = build_repricing_board(
        snapshot,
        offer_decision_board=competitive_board(
            our_sale_cost=10,
            competitive=2,
            temporal=1,
            sporting=0,
        ),
        state=empty_state(),
        hours_to_deadline=100,
    )

    action = board["actions"][0]

    assert action["action"] == "KEEP_COUNTER"
    assert action["recommended_counter"] == 2_000_123
    assert action["raise_by"] == 0


def test_never_sell_cancels_counter_shadow():
    snapshot = snapshot_with_counter()

    board = build_repricing_board(
        snapshot,
        offer_decision_board=competitive_board(
            decision="NEVER_SELL",
        ),
        state=empty_state(),
    )

    action = board["actions"][0]

    assert action["action"] == "CANCEL_COUNTER"
    assert action["priority"] == 100


def test_missing_context_blocks_instead_of_guessing():
    snapshot = snapshot_with_counter()

    board = build_repricing_board(
        snapshot,
        offer_decision_board={
            "decisions": [],
            "speculation": {
                "owned": [],
            },
        },
        state=empty_state(),
    )

    action = board["actions"][0]

    assert action["action"] == "REVIEW_BLOCK"
    assert action["fresh_minimum"] is None


def test_state_tracks_first_and_last_market():
    snapshot = snapshot_with_counter(
        counter_amount=1_200_000,
        market_value=1_250_000,
    )

    board = build_repricing_board(
        snapshot,
        offer_decision_board=competitive_board(),
        state=empty_state(),
    )

    state = empty_state()
    first = update_shadow_state(
        state,
        board,
    )

    assert first["first_seen"] == 1
    record = state["negotiations"]["1:200"]
    assert record["first_market_value"] == 1_250_000
    assert record["last_market_value"] == 1_250_000

    board["actions"][0]["market_value"] = 1_300_000
    second = update_shadow_state(
        state,
        board,
    )

    assert second["first_seen"] == 0
    assert record["first_market_value"] == 1_250_000
    assert record["last_market_value"] == 1_300_000


def main():
    tests = [
        test_detects_active_counteroffer,
        test_pairs_original_incoming_offer,
        test_exact_price_has_no_10k_rounding,
        test_market_catches_old_counter_and_pepe_raises,
        test_never_lowers_counter,
        test_never_sell_cancels_counter_shadow,
        test_missing_context_blocks_instead_of_guessing,
        test_state_tracks_first_and_last_market,
    ]

    for fn in tests:
        fn()
        print("OK ", fn.__name__)

    print("DYNAMIC COUNTEROFFER REPRICING V10.7 SHADOW: 8/8 OK")


if __name__ == "__main__":
    main()
