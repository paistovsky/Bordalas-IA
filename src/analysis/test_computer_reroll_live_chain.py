from __future__ import annotations

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.computer_offer_reroll_engine import (
    build_computer_offer_reroll_board,
)


def main() -> None:

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    board = build_computer_offer_reroll_board(
        snapshot=snapshot,
        persist_history=False,
    )

    global_state = build_global_decision(
        snapshot
    )

    decision = global_state.get(
        "decision",
        {},
    )

    candidates = global_state.get(
        "candidates",
        [],
    )

    reroll_candidates = board.get(
        "reroll_candidates",
        [],
    )

    orchestrator_rerolls = [
        item
        for item in candidates
        if item.get("action")
        in {
            "REROLL_COMPUTER_OFFER",
            "REROLL_CANDIDATE",
        }
    ]

    print()
    print(
        "Snapshot:".ljust(30),
        snapshot_file,
    )

    print(
        "Ofertas Computer:".ljust(30),
        board.get("offer_count", 0),
    )

    print(
        "Reroll candidates:".ljust(30),
        len(reroll_candidates),
    )

    print(
        "Candidatos Orchestrator:".ljust(30),
        len(orchestrator_rerolls),
    )

    print()
    print("## REROLL ENGINE")
    print()

    if not reroll_candidates:

        print(
            "No existe actualmente ninguna oferta "
            "Computer autorizada para reroll."
        )

    for offer in reroll_candidates:

        players = ", ".join(
            player.get("name", "?")
            for player in offer.get(
                "players",
                [],
            )
        )

        print(
            f"{players:25} "
            f"offer={offer.get('offer_id')} "
            f"amount={offer.get('amount')} "
            f"premium={offer.get('premium_percent')}% "
            f"safe={offer.get('reroll_safe')} "
            f"action={offer.get('action')}"
        )

    print()
    print("## ORCHESTRATOR")
    print()

    if not orchestrator_rerolls:

        print(
            "No existe candidato de reroll "
            "en el Orchestrator."
        )

    for item in orchestrator_rerolls:

        offer = (
            item.get(
                "data",
                {},
            )
            .get(
                "offer",
                {},
            )
        )

        players = ", ".join(
            player.get("name", "?")
            for player in offer.get(
                "players",
                [],
            )
        )

        print(
            f"type={item.get('type')} "
            f"priority={item.get('priority')} "
            f"action={item.get('action')} "
            f"executable={item.get('executable')}"
        )

        print(
            f"player={players} "
            f"offer={offer.get('offer_id')} "
            f"reroll_safe={offer.get('reroll_safe')}"
        )

    print()
    print("## DECISION GLOBAL")
    print()

    print(
        f"type={decision.get('type')} "
        f"priority={decision.get('priority')} "
        f"action={decision.get('action')} "
        f"executable={decision.get('executable')}"
    )

    print()
    print("## SAFETY")
    print()

    errors = []

    for offer in reroll_candidates:

        if not offer.get(
            "reroll_safe",
            False,
        ):
            errors.append(
                "Existe REROLL_CANDIDATE "
                "con reroll_safe=False."
            )

        if not offer.get(
            "replacement_cycle_available",
            False,
        ):
            errors.append(
                "Existe REROLL_CANDIDATE "
                "sin ciclo Computer de reemplazo."
            )

        simulation = (
            offer.get(
                "simulation",
                {},
            )
            or {}
        )

        if not simulation.get(
            "guaranteed_after_reroll",
            False,
        ):
            errors.append(
                "Existe REROLL_CANDIDATE "
                "sin SOLVENCY_GUARANTEE."
            )

    for candidate in orchestrator_rerolls:

        if (
            candidate.get("action")
            == "REROLL_COMPUTER_OFFER"
            and
            not candidate.get(
                "executable",
                False,
            )
        ):
            errors.append(
                "REROLL_COMPUTER_OFFER "
                "no esta marcado executable."
            )

        offer = (
            candidate.get(
                "data",
                {},
            )
            .get(
                "offer",
                {},
            )
        )

        if (
            candidate.get("action")
            == "REROLL_COMPUTER_OFFER"
            and
            not offer.get(
                "reroll_safe",
                False,
            )
        ):
            errors.append(
                "Orchestrator intenta ejecutar "
                "un reroll no seguro."
            )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "COMPUTER REROLL LIVE CHAIN: FAILED"
        )

    print(
        "# COMPUTER REROLL LIVE CHAIN: OK"
    )


if __name__ == "__main__":
    main()