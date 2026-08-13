from src.analysis.intelligent_bid_engine import build_market_bid_authority
from src.analysis.market_trader_shadow import build_market_trader_shadow


def candidate(
    player_id: int = 1,
    *,
    name: str = "Hugo Test",
    price: int = 1_350_000,
    speculation_score: float = 90.0,
    increment_pct: float = 4.0,
) -> dict:
    return {
        "id": player_id,
        "name": name,
        "price": price,
        "position": 3,
        "speculation_action": "BUY_SPECULATION",
        "speculation_score": speculation_score,
        "dominant_role": "SPECULATION",
        "history_confidence": {"confidence": 85},
        "price_increment_percent": increment_pct,
        "external_signal": {"jp_market_score": 65},
    }


def snapshot(*, maximum_bid: int = 10_000_000, own: bool = False) -> dict:
    return {
        "market": {
            "status": {
                "maximumBid": maximum_bid,
            },
            "sales": [],
        },
        "my_team": ([{"id": 1, "name": "Hugo Test"}] if own else []),
    }


def legacy_zero(player_id: int = 1, score: float = 55.0) -> dict:
    return {
        "id": player_id,
        "suggested_bid": 0,
        "intelligent_score": score,
        "action": "NO PUJAR",
        "competitive_observer_decision": "SKIP_LEGACY_NO_BID",
        "competitive_strategic_max_price": None,
    }


def decision_result(players: list[dict]) -> dict:
    return {
        "state": {
            "speculation": {
                "buy_candidates": players,
                "budget": {
                    "enabled": True,
                    "total_budget": 3_000_000,
                    "single_operation_limit": 2_000_000,
                    "mode": "DEBT",
                },
            },
            "solvency": {
                "balance": -1_000_000,
                "solvency_guarantee": {"safety_buffer": 500_000},
                "safe_liquidity_portfolio": {
                    "trading_safe_total": 6_000_000,
                    "trading_safe": {
                        "amount": 6_000_000,
                        "lineup_score_loss_percent": 2.0,
                    },
                    "tier_b": {"amount": 8_000_000},
                    "tier_c": {"amount": 10_000_000},
                },
                "max_safe_debt": {"debt_window_open": True},
                "temporary_debt": {"allowed": True},
                "deadline": {"phase": "NORMAL", "operations_locked": False},
                "hard_safety": {"active": False},
            },
        }
    }


def test_bid_authority_creates_bid_from_zero() -> None:
    player = candidate()
    authority = build_market_bid_authority(
        snapshot(),
        player,
        legacy_zero(),
        trading_score=81.0,
    )
    assert authority["allowed"] is True
    assert authority["source"] == "V10_CREATED_FROM_ZERO"
    assert authority["legacy_bid"] == 0
    assert authority["authority_bid"] > player["price"]
    assert authority["premium_percent"] > 0


def test_bid_authority_respects_biwenger_maximum_bid() -> None:
    player = candidate()
    authority = build_market_bid_authority(
        snapshot(maximum_bid=1_380_000),
        player,
        legacy_zero(),
        trading_score=90.0,
    )
    assert authority["authority_bid"] <= 1_380_000


def test_bid_authority_never_bids_for_own_player() -> None:
    player = candidate()
    authority = build_market_bid_authority(
        snapshot(own=True),
        player,
        legacy_zero(),
        trading_score=90.0,
    )
    assert authority["allowed"] is False
    assert authority["authority_bid"] == 0
    assert authority["source"] == "BLOCK_OWN_PLAYER"


def test_market_trader_uses_new_authority_but_roi_remains_final_cap() -> None:
    player = candidate()
    trader = build_market_trader_shadow(
        snapshot(),
        decision_result=decision_result([player]),
        intelligent_bids=[legacy_zero(score=55.0)],
    )
    item = trader["opportunities"][0]
    assert item["legacy_intelligent_bid"] == 0
    assert item["bid_authority_source"] == "V10_CREATED_FROM_ZERO"
    assert item["bid_authority_bid"] > item["price"]
    assert item["recommended_bid"] <= item["max_rational_bid"]
    assert item["decision"] == "BUY_SHADOW"


def test_legacy_bid_is_combined_not_discarded() -> None:
    player = candidate(price=800_000, speculation_score=91.0)
    legacy = {
        "id": 1,
        "suggested_bid": 850_000,
        "intelligent_score": 84,
        "action": "PUJAR",
        "competitive_strategic_max_price": None,
    }
    authority = build_market_bid_authority(
        snapshot(),
        player,
        legacy,
        trading_score=86.0,
    )
    assert authority["source"] == "HYBRID_LEGACY_PLUS_V10"
    assert authority["authority_bid"] >= 850_000


def main() -> None:
    tests = [
        test_bid_authority_creates_bid_from_zero,
        test_bid_authority_respects_biwenger_maximum_bid,
        test_bid_authority_never_bids_for_own_player,
        test_market_trader_uses_new_authority_but_roi_remains_final_cap,
        test_legacy_bid_is_combined_not_discarded,
    ]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print("BID AUTHORITY V10.3.1: OK")


if __name__ == "__main__":
    main()
