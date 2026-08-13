from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.autopilot import run_cycle
from src.analysis.controlled_speculation_live import (
    build_controlled_run,
    print_result as print_controlled_buy,
)
from src.analysis.position_manager_shadow_v106 import (
    sync_current as sync_position_manager,
    print_board as print_position_manager,
)
from src.analysis.dynamic_counteroffer_repricing_v107 import (
    sync_current as sync_counter_repricing,
    print_board as print_counter_repricing,
)
from src.actions.live_sale_executor import execute_sale_listing
from src.biwenger.write_client import BiwengerWriteClient


STATUS_PATH = Path("data/trading/v10_full_autonomous_status.json")

EXIT_ACTIONS = {
    "TAKE_PROFIT",
    "CUT_LOSS",
    "ROTATE_CAPITAL",
}


def _write_used(cycle: dict) -> bool:
    legacy = cycle.get("execution", {}) or {}
    competitive = cycle.get("competitive_execution", {}) or {}
    return bool(
        legacy.get("write_performed")
        or competitive.get("write_performed")
    )


def _best_exit(board: dict) -> dict | None:
    items = [
        item
        for item in (board.get("actionable", []) or [])
        if item.get("action") in EXIT_ACTIONS
    ]
    if not items:
        return None
    return sorted(
        items,
        key=lambda x: (
            int(x.get("priority") or 0),
            abs(int(x.get("unrealized_pnl") or 0)),
        ),
        reverse=True,
    )[0]


def _best_raise(board: dict) -> dict | None:
    items = [
        item
        for item in (board.get("actions", []) or [])
        if item.get("action") == "RAISE_COUNTER"
        and int(item.get("incoming_offer_id") or 0) > 0
        and int(item.get("recommended_counter") or 0) > 0
    ]
    if not items:
        return None
    return sorted(
        items,
        key=lambda x: (
            float(x.get("urgency_score") or 0),
            int(x.get("raise_by") or 0),
        ),
        reverse=True,
    )[0]


def run_full_autonomous_cycle() -> dict:
    print("\n" + "=" * 100)
    print("BORDALAS IA - V10.10 FULL AUTONOMOUS LIVE")
    print("=" * 100)

    # 1) Existing production engine first.
    cycle = run_cycle(
        live=True,
        competitive_live=True,
    )

    write_used = _write_used(cycle)
    action_taken = None
    action_result = None

    # 2) If no prior write, allow BUY V10.
    if not write_used:
        buy = build_controlled_run(
            refresh=True,
            execute_live=True,
            live_confirmation="BORDALAS",
        )
        print_controlled_buy(buy)

        if buy.get("writes_biwenger"):
            write_used = True
            action_taken = "BUY_V10"
            action_result = buy

    # 3) Fresh V10.6 decision.
    position = sync_position_manager(refresh=True)
    print_position_manager(position.get("board", {}) or {})

    # 4) Fresh V10.7 decision.
    counter = sync_counter_repricing(refresh=True)
    print_counter_repricing(counter.get("board", {}) or {})

    # 5) If still no write, execute ONE best autonomous action.
    if not write_used:
        counter_candidate = _best_raise(counter.get("board", {}) or {})
        exit_candidate = _best_exit(position.get("board", {}) or {})

        # Counter repricing has priority over exit if both exist because
        # it is time-sensitive and tied to an active rival offer.
        if counter_candidate:
            writer = BiwengerWriteClient()

            offer_id = int(counter_candidate["incoming_offer_id"])
            amount = int(counter_candidate["recommended_counter"])

            action_result = writer.counter_offer(
                offer_id=offer_id,
                amount=amount,
                execute=True,
            )
            write_used = True
            action_taken = "RAISE_COUNTER"

        elif exit_candidate:
            player_id = int(exit_candidate["player_id"])
            price = int(exit_candidate["current_value"])

            action_result = execute_sale_listing(
                player_id=player_id,
                price=price,
                execute=True,
            )
            write_used = bool(action_result.get("sent"))
            action_taken = "EXIT_LISTING"

    payload = {
        "version": "V10.10",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "full_autonomous_live": True,
        "write_used": write_used,
        "action_taken": action_taken,
        "action_result": action_result,
    }

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 100)
    print("V10.10 SUMMARY")
    print("=" * 100)
    print("Full autonomous LIVE: YES")
    print(f"Write used: {'YES' if write_used else 'NO'}")
    print(f"Action: {action_taken or 'NONE'}")
    print("=" * 100)

    return payload


def main() -> None:
    run_full_autonomous_cycle()


if __name__ == "__main__":
    main()
