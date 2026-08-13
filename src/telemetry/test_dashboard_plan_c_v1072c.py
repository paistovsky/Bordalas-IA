from src.telemetry.dashboard_state import (
    _select_recovery_subset,
    build_dashboard_solvency_plans,
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


def signature(plan):
    return tuple(sorted(plan.get("player_ids", []) or []))


def test_selector_prefers_non_overlapping_plan():
    sources = [
        source("A", 4_102_300, 1),
        source("B", 754_000, 2),
        source("C", 3_426_500, 3),
        source("D", 1_944_900, 4),
    ]

    picked = _select_recovery_subset(
        sources,
        4_651_032,
        avoid_player_ids={1, 2},
    )

    ids = {
        pid
        for item in picked
        for pid in item["player_ids"]
    }

    assert ids == {3, 4}


def test_three_plans_are_distinct_when_liquidity_allows():
    pool = [
        source("Etta", 4_102_300, 1),
        source("Bayindir", 754_000, 2),
        source("Gustavo", 3_426_500, 3),
        source("Yeray", 1_944_900, 4),
        source("Jutgla", 4_106_500, 5),
        source("Valentin", 600_000, 6),
        source("Dituro", 3_479_700, 7),
        source("Fidalgo", 1_200_000, 8),
    ]

    state = {
        "balance": -4_651_032,
        "solvency": {
            "balance": -4_651_032,
            "safe_liquidity_portfolio": {
                "policy": "SAFE_DEBT_WITH_SPORTING_B1_FOR_TRADING",
                "tier_a": raw_plan("A", pool),
                "trading_safe": raw_plan(
                    "B", pool, sporting_tier="B1"
                ),
                "tier_b": raw_plan(
                    "B", pool, sporting_tier="B2"
                ),
                "tier_c": raw_plan(
                    "C", pool, playable=10
                ),
            },
        },
    }

    plans = build_dashboard_solvency_plans(state)

    assert plans["a"]
    assert plans["b"]
    assert plans["c"]

    sigs = {
        signature(plans["a"]),
        signature(plans["b"]),
        signature(plans["c"]),
    }

    assert len(sigs) == 3
    assert all(
        plan["restores_solvency"]
        for plan in [
            plans["a"],
            plans["b"],
            plans["c"],
        ]
    )


def test_c_can_use_b2_fallback_if_tier_c_repeats():
    a_sources = [
        source("A1", 3_000_000, 1),
        source("A2", 2_000_000, 2),
    ]
    b_sources = [
        source("B1", 3_500_000, 3),
        source("B2", 1_300_000, 4),
        source("B3", 3_600_000, 5),
        source("B4", 1_100_000, 6),
    ]

    state = {
        "balance": -4_651_032,
        "solvency": {
            "balance": -4_651_032,
            "safe_liquidity_portfolio": {
                "tier_a": raw_plan("A", a_sources),
                "trading_safe": raw_plan(
                    "B", b_sources[:2], sporting_tier="B1"
                ),
                "tier_b": raw_plan(
                    "B", b_sources, sporting_tier="B2"
                ),
                # Tier C solo repite B1.
                "tier_c": raw_plan(
                    "C", b_sources[:2], playable=10
                ),
            },
        },
    }

    plans = build_dashboard_solvency_plans(state)

    assert plans["c"]
    assert plans["c"]["plan_kind"] == "C_FALLBACK_B2_DISTINCT"
    assert signature(plans["c"]) != signature(plans["b"])


def test_positive_balance_has_no_plans():
    plans = build_dashboard_solvency_plans({
        "balance": 1,
        "solvency": {
            "balance": 1,
            "safe_liquidity_portfolio": {},
        },
    })

    assert plans["a"] is None
    assert plans["b"] is None
    assert plans["c"] is None


def main():
    tests = [
        test_selector_prefers_non_overlapping_plan,
        test_three_plans_are_distinct_when_liquidity_allows,
        test_c_can_use_b2_fallback_if_tier_c_repeats,
        test_positive_balance_has_no_plans,
    ]

    for fn in tests:
        fn()
        print("OK ", fn.__name__)

    print("DASHBOARD PLAN C DISTINCT V10.7.2C: 4/4 OK")


if __name__ == "__main__":
    main()
