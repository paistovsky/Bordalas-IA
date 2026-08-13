from src.analysis.market_trader_shadow import build_market_trader_shadow


def candidate(
    player_id: int,
    name: str,
    price: int,
    score: float,
    *,
    history: int = 85,
    increment_pct: float = 4.0,
    jp: float = 60.0,
    action: str = "BUY_SPECULATION",
) -> dict:
    return {
        "id": player_id,
        "name": name,
        "price": price,
        "position": 3,
        "speculation_action": action,
        "speculation_score": score,
        "dominant_role": "SPECULATION",
        "history_confidence": {"confidence": history},
        "price_increment_percent": increment_pct,
        "external_signal": {"jp_market_score": jp},
    }


def fake_decision_result(players: list[dict]) -> dict:
    return {
        "state": {
            "speculation": {
                "buy_candidates": players,
                "budget": {
                    "enabled": True,
                    "total_budget": 2_400_000,
                    "single_operation_limit": 1_200_000,
                    "mode": "DEBT",
                },
            },
            "solvency": {
                "balance": -1_000_000,
                "solvency_guarantee": {"safety_buffer": 500_000},
                "safe_liquidity_portfolio": {
                    "trading_safe_total": 5_000_000,
                    "trading_safe": {
                        "amount": 5_000_000,
                        "lineup_score_loss_percent": 2.0,
                    },
                    "tier_b": {"amount": 9_000_000},
                    "tier_c": {"amount": 11_000_000},
                },
                "max_safe_debt": {"debt_window_open": True},
                "temporary_debt": {"allowed": True},
                "deadline": {"phase": "NORMAL", "operations_locked": False},
                "hard_safety": {"active": False},
            },
        }
    }


def intel(player_id: int, bid: int, score: float = 80) -> dict:
    return {
        "id": player_id,
        "suggested_bid": bid,
        "intelligent_score": score,
        "action": "DEMASIADO CARO",
        "competitive_strategic_max_price": None,
    }


def test_negative_balance_can_build_multi_buy_shadow_plan_with_b1() -> None:
    players = [
        candidate(1, "Alpha", 800_000, 90),
        candidate(2, "Beta", 700_000, 86),
    ]
    trader = build_market_trader_shadow(
        {"market": {"status": {"maximumBid": 10_000_000}}},
        decision_result=fake_decision_result(players),
        intelligent_bids=[intel(1, 840_000, 82), intel(2, 730_000, 78)],
    )
    assert trader["writes_biwenger"] is False
    assert trader["capital"]["sporting_safe_spend_capacity"] == 3_500_000
    assert trader["planned_positions"] == 2
    assert trader["planned_spend"] > 0
    assert trader["projected_t15_after_plan"] >= 0
    assert all(item["decision"] == "BUY_SHADOW" for item in trader["buy_plan"])


def test_intelligent_bid_is_capped_by_rational_roi_ceiling() -> None:
    player = candidate(1, "Alpha", 800_000, 90)
    trader = build_market_trader_shadow(
        {"market": {"status": {"maximumBid": 10_000_000}}},
        decision_result=fake_decision_result([player]),
        intelligent_bids=[intel(1, 1_200_000, 82)],
    )
    item = trader["opportunities"][0]
    assert item["legacy_intelligent_bid"] == 1_200_000
    assert item["recommended_bid"] <= item["max_rational_bid"]
    assert item["recommended_bid"] < item["legacy_intelligent_bid"]
    assert item["decision"] == "BUY_SHADOW"


def test_low_margin_buy_signal_is_pass_margin_even_if_speculation_says_buy() -> None:
    player = candidate(
        1,
        "Margen Bajo",
        1_000_000,
        72,
        history=40,
        increment_pct=0.0,
        jp=50,
    )
    trader = build_market_trader_shadow(
        {"market": {"status": {"maximumBid": 10_000_000}}},
        decision_result=fake_decision_result([player]),
        intelligent_bids=[intel(1, 1_000_000, 95)],
    )
    item = trader["opportunities"][0]
    assert item["max_rational_bid"] < item["price"]
    assert item["decision"] == "PASS_MARGIN"
    assert item["decision_reason"] == (
        "No existe precio de entrada compatible con el ROI minimo."
    )


def test_hard_safety_blocks_debt_trading() -> None:
    player = candidate(1, "Alpha", 800_000, 90)
    result = fake_decision_result([player])
    result["state"]["solvency"]["hard_safety"] = {"active": True}
    result["state"]["solvency"]["deadline"]["phase"] = "HARD_SAFETY"
    trader = build_market_trader_shadow(
        {"market": {"status": {"maximumBid": 10_000_000}}},
        decision_result=result,
        intelligent_bids=[intel(1, 840_000, 82)],
    )
    assert trader["capital"]["sporting_safe_spend_capacity"] == 0
    assert trader["planned_positions"] == 0


def main() -> None:
    tests = [
        test_negative_balance_can_build_multi_buy_shadow_plan_with_b1,
        test_intelligent_bid_is_capped_by_rational_roi_ceiling,
        test_low_margin_buy_signal_is_pass_margin_even_if_speculation_says_buy,
        test_hard_safety_blocks_debt_trading,
    ]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print("MARKET TRADER CURRENT REGRESSION: 4/4 OK")


if __name__ == "__main__":
    main()
