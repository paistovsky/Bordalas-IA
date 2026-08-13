from src.telemetry.dashboard_state import (
    _select_recovery_subset,
    build_dashboard_solvency_plans,
    compact_safe_debt_recovery_plan,
)


def source(name, amount, player_id):
    return {
        "kind": "COMPUTER_OFFER",
        "amount": amount,
        "player_ids": [player_id],
        "player_names": [name],
    }


def raw_plan(tier, sources, playable=11, sporting_tier=None):
    return {
        "tier": tier,
        "sporting_tier": sporting_tier or tier,
        "sources": sources,
        "playable_count": playable,
        "missing": 11 - playable,
        "lineup_complete": playable == 11,
        "formation_after": "4-4-2",
        "lineup_score_after": 500.0,
        "lineup_score_loss": 10.0,
        "lineup_score_loss_percent": 4.9,
    }


def test_subset():
    picked = _select_recovery_subset(
        [
            source("A", 4_106_500, 1),
            source("B", 4_102_300, 2),
            source("C", 1_944_900, 3),
            source("D", 754_000, 4),
        ],
        4_651_032,
    )
    assert sum(x["amount"] for x in picked) == 4_856_300


def test_compact():
    p = compact_safe_debt_recovery_plan(
        raw_plan(
            "A",
            [
                source("Uno", 3_000_000, 1),
                source("Dos", 2_000_000, 2),
            ],
        ),
        balance=-4_651_032,
        deficit=4_651_032,
        plan_kind="A_NO_XI",
    )
    assert p["post_balance"] == 348_968
    assert p["restores_solvency"] is True


def test_three_plans_without_manager_offers():
    state = {
        "balance": -4_651_032,
        "solvency": {
            "balance": -4_651_032,
            "safe_liquidity_portfolio": {
                "policy": "SAFE_DEBT_WITH_SPORTING_B1_FOR_TRADING",
                "tier_a": raw_plan(
                    "A",
                    [source("A1", 3_000_000, 1), source("A2", 2_000_000, 2)],
                ),
                "trading_safe": raw_plan(
                    "B",
                    [source("B1", 4_106_500, 3), source("B2", 754_000, 4)],
                    sporting_tier="B1",
                ),
                "tier_b": raw_plan(
                    "B",
                    [source("B3", 3_500_000, 6), source("B4", 1_300_000, 7)],
                    sporting_tier="B2",
                ),
                "tier_c": raw_plan(
                    "C",
                    [source("Emergency", 5_100_001, 5)],
                    playable=10,
                ),
            },
        },
    }
    plans = build_dashboard_solvency_plans(state)
    assert plans["source"] == "SAFE_DEBT_V10"
    assert plans["a"] and plans["b"] and plans["c"]
    assert all(x["restores_solvency"] for x in [plans["a"], plans["b"], plans["c"]])


def test_positive_no_recovery():
    plans = build_dashboard_solvency_plans({
        "balance": 1,
        "solvency": {"balance": 1, "safe_liquidity_portfolio": {}},
    })
    assert plans["available"] is False


def main():
    tests = [test_subset, test_compact, test_three_plans_without_manager_offers, test_positive_no_recovery]
    for fn in tests:
        fn()
        print("OK ", fn.__name__)
    print("DASHBOARD SOLVENCY PLANS V10.7.2: 4/4 OK")


if __name__ == "__main__":
    main()
