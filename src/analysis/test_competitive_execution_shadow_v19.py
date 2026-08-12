from src.analysis.competitive_execution_shadow import (
    build_competitive_shadow_decision,
    execute_competitive_shadow,
)


def make_offer(
    *,
    player_id,
    name,
    gate,
    should_respond,
):
    return {
        "offer_id": player_id + 5000,
        "player_id": player_id,
        "player_name": name,
        "rival_name": "Pollo17",
        "amount": 4_700_000,
        "decision_authority": "COMPETITIVE",
        "authoritative_decision": "COUNTER_OFFER",
        "authoritative_counter_amount": 5_900_000,
        "counter_amount": 5_900_000,
        "strategic_sell_price": 5_900_000,
        "negotiation": {
            "action_gate": gate,
            "should_respond": should_respond,
        },
        "replacement_detail": {
            "post_sale_playable_count": 11,
        },
    }


def main():

    blocked_offers = [
        make_offer(
            player_id=1,
            name="Jutgla",
            gate="NO_ACTION_WAITING_RIVAL",
            should_respond=False,
        )
    ]

    shadow = build_competitive_shadow_decision(
        manager_offers=blocked_offers,
        temporal_gate={
            "phase": "NORMAL",
            "operations_locked": False,
        },
        current_balance=-4_651_032,
    )

    result = execute_competitive_shadow(
        shadow
    )

    print("BLOCKED")
    print(shadow)
    print(result)

    assert shadow["status"] == "NO_COMPETITIVE_ACTION"
    assert result["write_performed"] is False

    allowed_offers = [
        make_offer(
            player_id=1,
            name="Jutgla",
            gate="RECALCULATE",
            should_respond=True,
        )
    ]

    shadow = build_competitive_shadow_decision(
        manager_offers=allowed_offers,
        temporal_gate={
            "phase": "NORMAL",
            "operations_locked": False,
        },
        current_balance=-4_651_032,
    )

    result = execute_competitive_shadow(
        shadow
    )

    print()
    print("ALLOWED BUT SHADOW-BLOCKED")
    print(shadow)
    print(result)

    assert shadow["status"] == "SHADOW_READY"
    assert shadow["would_reach_executor"] is True
    assert result["would_write"] is True
    assert result["write_performed"] is False
    assert result["status"] == "SHADOW_BLOCK_BEFORE_WRITE"

    print()
    print("=" * 92)
    print("COMPETITIVE EXECUTION SHADOW V1.9: OK")
    print("NO SE HA EJECUTADO NINGUNA OPERACION REAL")
    print("=" * 92)


if __name__ == "__main__":
    main()
