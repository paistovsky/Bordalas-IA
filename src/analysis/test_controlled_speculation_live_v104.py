from src.analysis.controlled_speculation_live import evaluate_controlled_live_gate


def opportunity(**overrides):
    item = {
        "id": 1,
        "name": "Trader",
        "decision": "BUY_SHADOW",
        "speculation_score": 90.0,
        "trading_score": 75.0,
        "expected_roi_percent": 18.0,
        "bid_authority_allowed": True,
        "recommended_bid": 1_100_000,
        "price": 1_050_000,
        "max_rational_bid": 1_200_000,
        "projected_t15_after_buffer": 2_000_000,
    }
    item.update(overrides)
    return item


def trader(item, **capital_overrides):
    capital = {
        "balance": -2_000_000,
        "can_use_temporary_debt": True,
        "operations_locked": False,
        "hard_safety_active": False,
        "phase": "NORMAL",
    }
    capital.update(capital_overrides)
    return {"opportunities": [item], "capital": capital}


def test_happy_path_passes():
    result = evaluate_controlled_live_gate(trader(opportunity()))
    assert result["ready"] is True
    assert result["selected"]["name"] == "Trader"


def test_low_roi_is_blocked():
    result = evaluate_controlled_live_gate(trader(opportunity(expected_roi_percent=14.9)))
    assert result["ready"] is False
    assert "roi<15%" in result["rejected"][0]["live_gate_reasons"]


def test_no_price_edge_is_blocked():
    result = evaluate_controlled_live_gate(
        trader(opportunity(price=1_250_000, max_rational_bid=1_200_000))
    )
    assert result["ready"] is False
    assert "no_price_edge" in result["rejected"][0]["live_gate_reasons"]


def test_hard_safety_is_blocked():
    result = evaluate_controlled_live_gate(
        trader(opportunity(), hard_safety_active=True, phase="HARD_SAFETY")
    )
    assert result["ready"] is False


def test_negative_without_safe_debt_is_blocked():
    result = evaluate_controlled_live_gate(
        trader(opportunity(), can_use_temporary_debt=False)
    )
    assert result["ready"] is False
    assert "negative_balance_without_safe_debt" in result["rejected"][0]["live_gate_reasons"]


def test_pass_price_from_market_trader_cannot_go_live():
    result = evaluate_controlled_live_gate(
        trader(opportunity(decision="PASS_PRICE"))
    )
    assert result["ready"] is False
    assert "market_trader=PASS_PRICE" in result["rejected"][0]["live_gate_reasons"]


def main():
    tests = [
        test_happy_path_passes,
        test_low_roi_is_blocked,
        test_no_price_edge_is_blocked,
        test_hard_safety_is_blocked,
        test_negative_without_safe_debt_is_blocked,
        test_pass_price_from_market_trader_cannot_go_live,
    ]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print("CONTROLLED SPECULATION LIVE CHECK V10.4A: OK")


if __name__ == "__main__":
    main()
