from copy import deepcopy
from datetime import datetime, timedelta, timezone

from src.analysis.position_manager_shadow_v106 import (
    build_position_manager_shadow,
    evaluate_open_position,
    persist_shadow_decisions,
)


NOW = datetime(2026, 8, 13, 19, 0, tzinfo=timezone.utc)


def position(
    *,
    entry=1_000_000,
    current=1_000_000,
    target=1_250_000,
    opened_days=1,
    starting=False,
):
    return {
        "position_id": "P-1",
        "player_id": 1,
        "player_name": "Jugador Test",
        "status": "OPEN_POSITION",
        "strategy": "SPECULATION",
        "entry_price": entry,
        "current_value": current,
        "expected_exit_value_at_bid": target,
        "opened_at": (NOW - timedelta(days=opened_days)).isoformat(),
        "thesis_source": "LIVE_DECISION_EXACT",
        "events": [],
    }


def spec(
    *,
    score=70,
    trend_score=50,
    increment=0,
    action="HOLD",
    acceleration="STEADY_UP",
    risk="BAJO",
    history=85,
):
    return {
        "id": 1,
        "speculation_score": score,
        "speculation_action": action,
        "trend_score": trend_score,
        "trend": "UP" if increment > 0 else "DOWN" if increment < 0 else "NEUTRAL",
        "price_increment": increment,
        "price_increment_percent": 0,
        "acceleration_state": acceleration,
        "availability_risk": {
            "risk": risk,
        },
        "history_confidence": {
            "confidence": history,
        },
    }


def sporting(*, score=10, starting=False):
    return {
        "player_id": 1,
        "starting_xi": starting,
        "sporting_protection_score": score,
        "sporting_sale_risk": (
            "HIGH" if score >= 70 else
            "MEDIUM" if score >= 40 else
            "LOW"
        ),
    }


def capital(*, phase="NORMAL", balance=2_000_000, t15=4_000_000):
    return {
        "phase": phase,
        "balance": balance,
        "projected_t15_after_buffer_before_trading": t15,
    }


def reinvestment(
    *,
    roi=0,
    score=0,
    shortfall=0,
    name=None,
):
    best = None
    if name:
        best = {
            "player_id": 99,
            "name": name,
            "bid": 1_000_000,
            "expected_roi_percent": roi,
            "expected_profit": 200_000,
            "trading_score": score,
            "speculation_score": 90,
            "capital_shortfall": shortfall,
        }

    return {
        "best_alternative": best,
        "remaining_trading_budget": 0,
        "candidate_count": 1 if best else 0,
    }


def test_strong_winner_is_held():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_300_000,
            target=1_600_000,
        ),
        speculation=spec(
            score=90,
            trend_score=75,
            increment=80_000,
            action="HOLD_SPECULATION",
            acceleration="ACCELERATING_UP",
        ),
        sporting=sporting(score=10),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "HOLD"
    assert result["decision_basis"] == "HOLD_WINNER"


def test_take_profit_when_target_reached_and_fading():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_260_000,
            target=1_250_000,
        ),
        speculation=spec(
            trend_score=47,
            increment=-20_000,
            action="WATCH_SELL",
            acceleration="DECELERATING_UP",
        ),
        sporting=sporting(score=5),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "TAKE_PROFIT"


def test_cut_loss_when_loss_and_downtrend():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=850_000,
            target=1_250_000,
        ),
        speculation=spec(
            trend_score=32,
            increment=-60_000,
            action="SELL_SPECULATION",
            acceleration="ACCELERATING_DOWN",
        ),
        sporting=sporting(score=5),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "CUT_LOSS"


def test_recovery_is_held():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=930_000,
            target=1_250_000,
        ),
        speculation=spec(
            trend_score=62,
            increment=40_000,
            action="HOLD_SPECULATION",
            acceleration="ACCELERATING_UP",
        ),
        sporting=sporting(score=10),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "HOLD"
    assert result["decision_basis"] in {"HOLD_RECOVERY", "NO_EXIT_EDGE"}


def test_rotate_idle_position_to_superior_opportunity():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_010_000,
            target=1_050_000,
            opened_days=8,
        ),
        speculation=spec(
            trend_score=48,
            increment=0,
            action="HOLD",
            acceleration="STEADY_DOWN",
        ),
        sporting=sporting(score=0),
        reinvestment=reinvestment(
            roi=28,
            score=88,
            shortfall=500_000,
            name="Oportunidad Superior",
        ),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "ROTATE_CAPITAL"
    assert result["decision_basis"] == "SUPERIOR_REINVESTMENT"


def test_xi_protection_blocks_marginal_rotation():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_020_000,
            target=1_200_000,
            opened_days=4,
        ),
        speculation=spec(
            trend_score=52,
            increment=5_000,
            action="HOLD",
        ),
        sporting=sporting(
            score=82,
            starting=True,
        ),
        reinvestment=reinvestment(
            roi=22,
            score=80,
            shortfall=300_000,
            name="Alternativa",
        ),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "HOLD"


def test_solvency_emergency_beats_xi_protection():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_100_000,
            target=1_300_000,
        ),
        speculation=spec(
            trend_score=65,
            increment=20_000,
            action="HOLD_SPECULATION",
        ),
        sporting=sporting(
            score=90,
            starting=True,
        ),
        capital=capital(
            phase="HARD_SAFETY",
            balance=-500_000,
            t15=-200_000,
        ),
        now=NOW,
    )
    assert result["action"] == "ROTATE_CAPITAL"
    assert result["decision_basis"] == "SOLVENCY_EMERGENCY"


def test_negative_balance_alone_does_not_force_sale():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_050_000,
            target=1_300_000,
        ),
        speculation=spec(
            trend_score=65,
            increment=25_000,
            action="HOLD_SPECULATION",
        ),
        sporting=sporting(score=20),
        capital=capital(
            phase="PREPARATION",
            balance=-4_000_000,
            t15=8_000_000,
        ),
        now=NOW,
    )
    assert result["action"] == "HOLD"
    assert result["capital"]["emergency"] is False


def test_hard_player_risk_exits_even_with_profit():
    result = evaluate_open_position(
        position(
            entry=1_000_000,
            current=1_080_000,
            target=1_300_000,
        ),
        speculation=spec(
            trend_score=60,
            increment=10_000,
            action="SELL_RISK",
            risk="CRITICO",
        ),
        sporting=sporting(score=80, starting=True),
        capital=capital(),
        now=NOW,
    )
    assert result["action"] == "TAKE_PROFIT"
    assert result["decision_basis"] == "HARD_PLAYER_RISK_WITH_PROFIT"


def test_pending_position_is_wait_settlement():
    ledger = {
        "positions": [
            {
                "position_id": "BID-1",
                "player_id": 1,
                "player_name": "Pendiente",
                "status": "BID_PENDING",
                "bid_amount": 1_390_000,
            }
        ]
    }
    board = build_position_manager_shadow(ledger)
    assert board["summary"]["open_positions"] == 0
    assert board["summary"]["pending_positions"] == 1
    assert board["pending"][0]["action"] == "WAIT_SETTLEMENT"


def test_persist_is_idempotent_for_action_events():
    ledger = {
        "positions": [
            position(
                entry=1_000_000,
                current=1_260_000,
                target=1_250_000,
            )
        ]
    }
    board = build_position_manager_shadow(
        ledger,
        speculation_board={
            "owned": [
                spec(
                    trend_score=45,
                    increment=-20_000,
                    action="WATCH_SELL",
                    acceleration="DECELERATING_UP",
                )
            ]
        },
        sporting_contexts={
            1: sporting(score=5),
        },
        capital=capital(),
        now=NOW,
    )

    first = persist_shadow_decisions(ledger, board)
    second = persist_shadow_decisions(ledger, board)

    events = [
        event
        for event in ledger["positions"][0]["events"]
        if event.get("type") == "POSITION_MANAGER_SHADOW_ACTION"
    ]

    assert first["action_changes"] == 1
    assert second["action_changes"] == 0
    assert len(events) == 1


def main():
    tests = [
        test_strong_winner_is_held,
        test_take_profit_when_target_reached_and_fading,
        test_cut_loss_when_loss_and_downtrend,
        test_recovery_is_held,
        test_rotate_idle_position_to_superior_opportunity,
        test_xi_protection_blocks_marginal_rotation,
        test_solvency_emergency_beats_xi_protection,
        test_negative_balance_alone_does_not_force_sale,
        test_hard_player_risk_exits_even_with_profit,
        test_pending_position_is_wait_settlement,
        test_persist_is_idempotent_for_action_events,
    ]

    for fn in tests:
        fn()
        print("OK ", fn.__name__)

    print("POSITION MANAGER V10.6 SHADOW: 11/11 OK")


if __name__ == "__main__":
    main()
