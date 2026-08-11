from __future__ import annotations

import copy

from src.actions.autopilot_executor import (
    execute_autopilot_decision,
)

from src.analysis.computer_offer_reroll_engine import (
    build_computer_offer_reroll_board,
)

from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


FORCED_PREMIUM_PERCENT = -10.0


def safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(
            value
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def choose_simulation_offer(
    board: dict,
) -> dict | None:
    """
    Elige una oferta Computer apropiada para simular:
    - exactamente un jugador;
    - no Franchise/protegido;
    - no SOLVENCY_RESERVED.

    Preferimos una oferta que ya tenga reroll_safe=True.
    """
    candidates = []

    for offer in board.get(
        "offers",
        [],
    ) or []:

        player_ids = (
            offer.get(
                "player_ids",
                [],
            )
            or []
        )

        if len(player_ids) != 1:
            continue

        if offer.get(
            "franchise_protected",
            False,
        ):
            continue

        if offer.get(
            "solvency_reserved",
            False,
        ):
            continue

        candidates.append(
            offer
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            bool(
                item.get(
                    "reroll_safe",
                    False,
                )
            ),
            safe_int(
                item.get(
                    "market_value"
                )
            ),
        ),
        reverse=True,
    )

    return candidates[0]


def mutate_offer_amount(
    snapshot: dict,
    offer_id: int,
    new_amount: int,
) -> bool:
    """
    Modifica SOLO la copia en memoria del snapshot.
    No escribe archivos ni toca Biwenger.
    """

    offers = (
        snapshot.get(
            "market",
            {},
        ).get(
            "offers",
            [],
        )
        or []
    )

    for offer in offers:

        current_id = (
            offer.get(
                "id"
            )
        )

        if current_id is None:
            current_id = (
                offer.get(
                    "offer_id"
                )
            )

        try:
            current_id = int(
                current_id
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if current_id != int(
            offer_id
        ):
            continue

        offer[
            "amount"
        ] = int(
            new_amount
        )

        return True

    return False


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    original = (
        load_snapshot(
            snapshot_file
        )
    )

    original_board = (
        build_computer_offer_reroll_board(
            snapshot=
                original,

            persist_history=
                False,
        )
    )

    target = (
        choose_simulation_offer(
            original_board
        )
    )

    print()
    print("=" * 120)
    print(
        "             BORDALAS IA - COMPUTER REROLL SIMULATED LIVE CHAIN V1"
    )
    print("=" * 120)
    print()

    print(
        f"Snapshot original:           "
        f"{snapshot_file}"
    )

    if target is None:

        raise SystemExit(
            "ERROR: no existe una oferta Computer no reservada "
            "apta para la simulacion."
        )

    offer_id = safe_int(
        target.get(
            "offer_id"
        )
    )

    market_value = safe_int(
        target.get(
            "market_value"
        )
    )

    players = (
        target.get(
            "players",
            [],
        )
        or []
    )

    player_name = (
        players[0].get(
            "name",
            "?",
        )
        if players
        else "?"
    )

    if offer_id <= 0:

        raise SystemExit(
            "ERROR: oferta elegida sin offer_id valido."
        )

    if market_value <= 0:

        raise SystemExit(
            "ERROR: oferta elegida sin market_value valido."
        )

    simulated_amount = int(
        market_value
        * (
            1.0
            + (
                FORCED_PREMIUM_PERCENT
                / 100.0
            )
        )
    )

    simulated = copy.deepcopy(
        original
    )

    changed = (
        mutate_offer_amount(
            snapshot=
                simulated,

            offer_id=
                offer_id,

            new_amount=
                simulated_amount,
        )
    )

    if not changed:

        raise SystemExit(
            "ERROR: no se encontro la oferta raw dentro de "
            "snapshot['market']['offers']."
        )

    print(
        f"Jugador simulado:            "
        f"{player_name}"
    )

    print(
        f"Offer ID:                    "
        f"{offer_id}"
    )

    print(
        f"Valor mercado:               "
        f"{market_value:,.0f} EUR"
    )

    print(
        f"Oferta original:             "
        f"{safe_int(target.get('amount')):,.0f} EUR"
    )

    print(
        f"Oferta simulada:             "
        f"{simulated_amount:,.0f} EUR"
    )

    print(
        f"Premium forzado:             "
        f"{FORCED_PREMIUM_PERCENT:+.2f}%"
    )

    print()
    print(
        "## REROLL ENGINE SIMULADO"
    )
    print()

    simulated_board = (
        build_computer_offer_reroll_board(
            snapshot=
                simulated,

            persist_history=
                False,
        )
    )

    simulated_offer = next(
        (
            offer

            for offer
            in simulated_board.get(
                "offers",
                [],
            )

            if safe_int(
                offer.get(
                    "offer_id"
                )
            )
            == offer_id
        ),
        None,
    )

    if simulated_offer is None:

        raise SystemExit(
            "ERROR: la oferta simulada desaparecio del board."
        )

    print(
        f"Quality:                     "
        f"{simulated_offer.get('quality')}"
    )

    print(
        f"Reroll safe:                 "
        f"{simulated_offer.get('reroll_safe')}"
    )

    print(
        f"Replacement cycle:           "
        f"{simulated_offer.get('replacement_cycle_available')}"
    )

    print(
        f"Guarantee after reroll:      "
        f"{(
            simulated_offer.get(
                'simulation',
                {},
            )
            or {}
        ).get('guaranteed_after_reroll')}"
    )

    print(
        f"Decision:                    "
        f"{simulated_offer.get('action')}"
    )

    print()
    print(
        "## ORCHESTRATOR SIMULADO"
    )
    print()

    global_state = (
        build_global_decision(
            simulated
        )
    )

    reroll_candidates = [
        item

        for item
        in global_state.get(
            "candidates",
            [],
        )

        if item.get(
            "action"
        )
        == "REROLL_COMPUTER_OFFER"
    ]

    if not reroll_candidates:

        raise SystemExit(
            "ERROR: el Orchestrator no genero "
            "REROLL_COMPUTER_OFFER."
        )

    reroll_decision = (
        reroll_candidates[
            0
        ]
    )

    decision = (
        global_state.get(
            "decision",
            {},
        )
        or {}
    )

    print(
        f"Candidato type:              "
        f"{reroll_decision.get('type')}"
    )

    print(
        f"Prioridad:                   "
        f"{reroll_decision.get('priority')}"
    )

    print(
        f"Action:                      "
        f"{reroll_decision.get('action')}"
    )

    print(
        f"Executable:                  "
        f"{reroll_decision.get('executable')}"
    )

    print(
        f"Global action:               "
        f"{decision.get('action')}"
    )

    print(
        f"Global priority:             "
        f"{decision.get('priority')}"
    )

    print()
    print(
        "## EXECUTOR DRY RUN"
    )
    print()

    # IMPORTANTE:
    # execute=False. Nunca toca Biwenger.
    execution = (
        execute_autopilot_decision(
            decision=
                reroll_decision,

            execute=
                False,
        )
    )

    print(
        f"Status:                      "
        f"{execution.get('status')}"
    )

    print(
        f"Write performed:             "
        f"{execution.get('write_performed')}"
    )

    print(
        f"Success:                     "
        f"{execution.get('success')}"
    )

    print()
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    if (
        simulated_offer.get(
            "action"
        )
        != "REROLL_CANDIDATE"
    ):

        errors.append(
            "Reroll Engine no clasifico la oferta simulada "
            "como REROLL_CANDIDATE."
        )

    if not simulated_offer.get(
        "reroll_safe",
        False,
    ):

        errors.append(
            "REROLL_CANDIDATE no es reroll_safe."
        )

    if not simulated_offer.get(
        "replacement_cycle_available",
        False,
    ):

        errors.append(
            "No existe ciclo Computer seguro de reemplazo."
        )

    simulation = (
        simulated_offer.get(
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
            "SOLVENCY_GUARANTEE no queda cubierta."
        )

    if (
        reroll_decision.get(
            "action"
        )
        != "REROLL_COMPUTER_OFFER"
    ):

        errors.append(
            "El Orchestrator no tradujo a "
            "REROLL_COMPUTER_OFFER."
        )

    if not reroll_decision.get(
        "executable",
        False,
    ):

        errors.append(
            "REROLL_COMPUTER_OFFER no es executable=True."
        )

    if (
        decision.get(
            "action"
        )
        != "REROLL_COMPUTER_OFFER"
    ):

        errors.append(
            "Reroll no gano la decision global."
        )

    if (
        execution.get(
            "status"
        )
        != "DRY_RUN"
    ):

        errors.append(
            "Executor con execute=False no devolvio DRY_RUN."
        )

    if execution.get(
        "write_performed",
        False,
    ):

        errors.append(
            "El test realizo una escritura real."
        )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "COMPUTER REROLL SIMULATED LIVE CHAIN: FAILED"
        )

    print(
        "# COMPUTER REROLL SIMULATED LIVE CHAIN: OK"
    )

    print("=" * 120)


if __name__ == "__main__":
    main()
