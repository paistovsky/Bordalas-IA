from src.analysis.exact_price_policy import (
    apply_percent_exact,
    exact_euro,
    floor_euro,
)
from src.analysis.controlled_speculation_repricing import (
    build_fresh_bid_reprice,
)


def selected():
    return {
        "price": 1_350_000,
        "recommended_bid": 1_390_500,
        "max_rational_bid": 1_464_285,
        "expected_exit_value": 1_640_000,
        "bid_authority_premium_percent": 3.0,
    }


def capital():
    return {
        "balance": -4_651_032,
        "trading_safe_recovery": 14_334_200,
        "safety_buffer": 500_000,
        "operations_locked": False,
        "hard_safety_active": False,
    }


def test_exact_percent_no_10k_rounding():
    assert apply_percent_exact(1_350_000, 3.0) == 1_390_500


def test_exact_euro_half_up():
    assert exact_euro("1234567.6") == 1_234_568


def test_rational_cap_floors_only_one_euro():
    assert floor_euro("1464285.714") == 1_464_285


def test_hugo_fresh_reprice_is_exact():
    result = build_fresh_bid_reprice(
        selected(),
        {
            "current_price": 1_130_000,
            "minimum_bid": 1_350_000,
            "maximum_bid": 8_593_968,
        },
        capital(),
    )
    assert result["allowed"] is True
    assert result["effective_entry_floor"] == 1_350_000
    assert result["fresh_authority_bid"] == 1_390_500
    assert result["fresh_recommended_bid"] == 1_390_500
    assert result["fresh_expected_profit"] == 249_500


def test_no_cosmetic_randomness():
    a = apply_percent_exact(2_413_777, 2.35)
    b = apply_percent_exact(2_413_777, 2.35)
    assert a == b
    assert a == 2_470_501


def main():
    tests = [
        test_exact_percent_no_10k_rounding,
        test_exact_euro_half_up,
        test_rational_cap_floors_only_one_euro,
        test_hugo_fresh_reprice_is_exact,
        test_no_cosmetic_randomness,
    ]
    for fn in tests:
        fn()
        print("OK ", fn.__name__)
    print("EXACT EURO PRICING V10.4E: 5/5 OK")


if __name__ == "__main__":
    main()
