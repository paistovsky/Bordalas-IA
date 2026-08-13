from __future__ import annotations

from typing import Any

from src.analysis.exact_price_policy import (
    apply_percent_exact,
)


MIN_LIVE_EXPECTED_ROI_PERCENT = 15.0


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def _round_10k(value: float, *, down: bool = False) -> int:
    value = max(float(value or 0.0), 0.0)
    if value <= 0:
        return 0
    if down:
        return int(value // 10_000.0) * 10_000
    return int(round(value / 10_000.0) * 10_000)


def build_fresh_bid_reprice(
    selected: dict,
    preflight: dict,
    capital: dict,
    *,
    min_roi_percent: float = MIN_LIVE_EXPECTED_ROI_PERCENT,
) -> dict:
    """
    V10.4E - PURE fresh repricing with exact-euro pricing. No network, no writes.

    Confirmed by Biwenger LIVE response:
    - sale.price can be below the legal bid floor;
    - the API minimum is the player's official Biwenger value.

    Therefore:
      effective_entry_floor = max(fresh player value, manager listing)

    Bid Authority premium is applied over that effective floor. The result
    is then capped by max_rational and maximumBid and all ROI/T-15 gates are
    recalculated.
    """
    listing_price = _safe_int(preflight.get("current_price"))
    fresh_minimum_bid = _safe_int(preflight.get("minimum_bid"))
    maximum_bid = _safe_int(preflight.get("maximum_bid"))
    max_rational = _safe_int(selected.get("max_rational_bid"))
    expected_exit = _safe_int(selected.get("expected_exit_value"))
    old_bid = _safe_int(selected.get("recommended_bid"))
    snapshot_player_value = _safe_int(selected.get("price"))
    premium_percent = max(
        _safe_float(selected.get("bid_authority_premium_percent")),
        0.0,
    )

    # Fallback only for pure/unit tests or legacy preflight dictionaries.
    # Real V10.4D preflight always provides minimum_bid from the fresh catalog.
    player_value = fresh_minimum_bid or snapshot_player_value
    effective_entry_floor = max(listing_price, player_value)

    blocks: list[str] = []

    if listing_price <= 0:
        blocks.append("fresh_listing_price_invalid")
    if player_value <= 0:
        blocks.append("fresh_biwenger_minimum_invalid")
    if effective_entry_floor <= 0:
        blocks.append("fresh_effective_floor_invalid")
    if max_rational <= 0:
        blocks.append("max_rational_invalid")
    if expected_exit <= 0:
        blocks.append("expected_exit_invalid")
    if maximum_bid > 0 and effective_entry_floor > maximum_bid:
        blocks.append("fresh_floor_above_maximum_bid")
    if max_rational > 0 and effective_entry_floor > max_rational:
        blocks.append("fresh_floor_above_max_rational")

    fresh_authority_bid = 0
    fresh_bid = 0
    expected_profit = 0
    expected_roi = 0.0
    projected_t15 = 0

    if not blocks:
        # V10.4E: importe matemático exacto al euro, sin redondeo
        # cosmético a miles/10.000.
        fresh_authority_bid = apply_percent_exact(
            effective_entry_floor,
            premium_percent,
        )
        fresh_authority_bid = max(
            fresh_authority_bid,
            effective_entry_floor,
        )

        hard_cap = max_rational
        if maximum_bid > 0:
            hard_cap = min(hard_cap, maximum_bid)

        fresh_bid = min(fresh_authority_bid, hard_cap)
        fresh_bid = max(fresh_bid, effective_entry_floor)

        expected_profit = max(expected_exit - fresh_bid, 0)
        expected_roi = (
            (expected_profit / fresh_bid) * 100.0
            if fresh_bid > 0
            else 0.0
        )

        balance = _safe_int(capital.get("balance"))
        recovery = _safe_int(capital.get("trading_safe_recovery"))
        buffer = _safe_int(capital.get("safety_buffer"))
        projected_t15 = balance - fresh_bid + recovery - buffer

        if fresh_bid <= 0:
            blocks.append("fresh_bid_invalid")
        if fresh_bid < effective_entry_floor:
            blocks.append("fresh_bid_below_biwenger_floor")
        if fresh_bid > max_rational:
            blocks.append("fresh_bid_above_max_rational")
        if maximum_bid > 0 and fresh_bid > maximum_bid:
            blocks.append("fresh_bid_above_maximum_bid")
        if expected_roi < float(min_roi_percent):
            blocks.append(f"fresh_roi_below_{float(min_roi_percent):.1f}")
        if projected_t15 < 0:
            blocks.append("fresh_t15_below_buffer")
        if bool(capital.get("operations_locked", False)):
            blocks.append("operations_locked")
        if bool(capital.get("hard_safety_active", False)):
            blocks.append("hard_safety")

    return {
        "version": "V10.4E",
        "allowed": not blocks,
        "blocks": blocks,
        "snapshot_player_value": snapshot_player_value,
        "fresh_biwenger_minimum_bid": player_value,
        "fresh_listing_price": listing_price,
        "effective_entry_floor": effective_entry_floor,
        "old_planned_bid": old_bid,
        "authority_premium_percent": round(premium_percent, 2),
        "fresh_authority_bid": fresh_authority_bid,
        "fresh_recommended_bid": fresh_bid,
        "max_rational_bid": max_rational,
        "fresh_maximum_bid": maximum_bid,
        "expected_exit_value": expected_exit,
        "fresh_expected_profit": expected_profit,
        "fresh_expected_roi_percent": round(expected_roi, 1),
        "fresh_projected_t15_after_buffer": projected_t15,
        "bid_change": fresh_bid - old_bid if fresh_bid > 0 else 0,
        "reason": (
            "Fresh Biwenger minimum/listing floor repriced and all LIVE gates passed."
            if not blocks
            else ", ".join(blocks)
        ),
    }
