from src.analysis.competitive_safety_gate import select_single_competitive_action


def offer(player_id, name, action_gate, should_respond):
    return {
        "offer_id": player_id + 1000,
        "player_id": player_id,
        "player_name": name,
        "rival_name": "Pollo17",
        "amount": 4300000,
        "decision_authority": "COMPETITIVE",
        "authoritative_decision": "COUNTER_OFFER",
        "authoritative_counter_amount": 5670000,
        "counter_amount": 5670000,
        "strategic_sell_price": 5670000,
        "negotiation": {
            "action_gate": action_gate,
            "should_respond": should_respond,
        },
        "replacement_detail": {
            "post_sale_playable_count": 11,
        },
    }


def main():
    waiting = [
        offer(1, "Jutgla", "NO_ACTION_WAITING_RIVAL", False),
        offer(2, "Olasagasti", "NO_ACTION_WAITING_RIVAL", False),
        offer(3, "Ximo Navarro", "NO_ACTION_WAITING_RIVAL", False),
    ]

    board = select_single_competitive_action(
        offers=waiting,
        temporal_gate={"phase": "NORMAL", "operations_locked": False},
        current_balance=-4651032,
    )
    print("WAITING RIVAL")
    print(board)
    assert board["authorized_count"] == 0
    assert board["selected_count"] == 0

    changed = [
        offer(1, "Jutgla", "RECALCULATE", True),
        *waiting[1:],
    ]

    board = select_single_competitive_action(
        offers=changed,
        temporal_gate={"phase": "NORMAL", "operations_locked": False},
        current_balance=-4651032,
    )
    print("\nRIVAL CHANGED OFFER")
    print(board)
    assert board["authorized_count"] == 1
    assert board["selected_count"] == 1
    assert board["selected"]["player_name"] == "Jutgla"
    assert board["would_execute"] is False

    print("\n" + "=" * 88)
    print("COMPETITIVE SAFETY GATE V1.8: OK")
    print("DRY RUN ONLY: NO SE HA EJECUTADO NINGUNA OPERACION")
    print("=" * 88)


if __name__ == "__main__":
    main()
