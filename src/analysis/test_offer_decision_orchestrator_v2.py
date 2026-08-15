from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    result = build_global_decision(snapshot)
    state = result["state"]

    board = (
        state.get(
            "offer_decisions",
            {},
        )
        or {}
    )

    candidates = [
        item
        for item in result.get(
            "candidates",
            [],
        )
        if item.get("type")
        == "OFFER_DECISION_INTELLIGENCE"
    ]

    print()
    print("=" * 115)
    print("              BORDALAS IA - OFFER DECISION ORCHESTRATOR V2 - OBSERVER")
    print("=" * 115)
    print()

    print(f"Snapshot:                    {snapshot_file}")
    print(f"Ofertas evaluadas:           {board.get('offer_count', 0)}")
    print(f"HOLD_SOLVENCY_RESERVED:      {len(board.get('hold_solvency_reserved', []))}")
    print(f"NEVER_SELL:                  {len(board.get('never_sell', []))}")
    print(f"REROLL_CANDIDATE:            {len(board.get('reroll_candidates', []))}")
    print(f"ACCEPT_FOR_SOLVENCY:         {len(board.get('accept_for_solvency', []))}")
    print()

    print("## CANDIDATO ORCHESTRATOR")
    print()

    if not candidates:
        print("NINGUNO")
    else:
        for item in candidates:
            top_list = (
                item.get(
                    "data",
                    {},
                )
                # "top_offer_decision" no la produce nadie: el
                # candidato transporta el board entero en
                # data["offer_decisions"], y build_offer_decision_board
                # ya ordena decisions por decision_priority, asi
                # que decisions[0] ES el top.
                .get(
                    "offer_decisions",
                    {},
                )
                .get(
                    "decisions",
                    [],
                )[:1]
            )

            top = top_list[0] if top_list else {}

            print(
                f"type={item.get('type')} "
                f"priority={item.get('priority')} "
                f"action={item.get('action')} "
                f"executable={item.get('executable')}"
            )

            print(
                f"top={top.get('player_name')} "
                f"decision={top.get('decision')} "
                f"automatic={top.get('automatic')}"
            )

    print()
    print("## SAFETY")
    print()

    incoming_count = int(
        (
            state.get(
                "offers",
                {},
            )
            or {}
        ).get(
            "incoming_count",
            0,
        )
        or 0
    )

    offer_count = int(
        board.get(
            "offer_count",
            0,
        )
        or 0
    )

    if incoming_count != offer_count:
        raise SystemExit(
            "ERROR: state['offer_decisions'] no coincide con "
            f"las ofertas incoming: incoming={incoming_count}, "
            f"evaluadas={offer_count}."
        )

    if offer_count > 0 and not candidates:
        raise SystemExit(
            "ERROR: hay ofertas evaluadas pero no candidato Observer."
        )

    if candidates:
        top_from_candidate = (
            candidates[0]
            .get(
                "data",
                {},
            )
            .get(
                "offer_decisions",
                {},
            )
            .get(
                "decisions",
                [],
            )
        )

        top_from_candidate = (
            top_from_candidate[0]
            if top_from_candidate
            else {}
        )

        board_decisions = (
            board.get(
                "decisions",
                [],
            )
            or []
        )

        if not board_decisions:
            raise SystemExit(
                "ERROR: candidato Orchestrator contiene una decisión "
                "pero state['offer_decisions'] está vacío."
            )

        if (
            top_from_candidate.get("offer_id")
            !=
            board_decisions[0].get("offer_id")
        ):
            raise SystemExit(
                "ERROR: el top del candidato no coincide con "
                "state['offer_decisions']."
            )

    for item in candidates:
        if item.get("executable"):
            raise SystemExit(
                "ERROR: Offer Decision V2 no debe ser ejecutable."
            )

        if item.get("executor") is not None:
            raise SystemExit(
                "ERROR: Offer Decision V2 Observer no debe tener executor."
            )

    for decision in board.get(
        "decisions",
        [],
    ):
        if decision.get("automatic"):
            raise SystemExit(
                "ERROR: decision V2 marcada como automatica."
            )

    print("OFFER DECISION ORCHESTRATOR V2 OBSERVER: OK")
    print("=" * 115)


if __name__ == "__main__":
    main()
