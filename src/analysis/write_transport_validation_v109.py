from __future__ import annotations

import argparse

from src.actions.live_sale_executor import execute_sale_listing
from src.analysis.position_manager_shadow_v106 import (
    sync_current as sync_position_manager,
)
from src.analysis.dynamic_counteroffer_repricing_v107 import (
    sync_current as sync_counter_repricing,
)
from src.biwenger.write_client import BiwengerWriteClient


EXIT_ACTIONS = {
    "TAKE_PROFIT",
    "CUT_LOSS",
    "ROTATE_CAPITAL",
}


def select_exit_candidate(board: dict) -> dict | None:
    candidates = [
        item
        for item in (board.get("actionable", []) or [])
        if item.get("action") in EXIT_ACTIONS
    ]
    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda item: int(item.get("priority") or 0),
        reverse=True,
    )[0]


def select_counter_candidate(board: dict) -> dict | None:
    candidates = [
        item
        for item in (board.get("actions", []) or [])
        if item.get("action") == "RAISE_COUNTER"
        and int(item.get("recommended_counter") or 0) > 0
        and int(item.get("incoming_offer_id") or 0) > 0
    ]
    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda item: (
            float(item.get("urgency_score") or 0),
            int(item.get("raise_by") or 0),
        ),
        reverse=True,
    )[0]


def build_exit_preview(candidate: dict) -> dict:
    player_id = int(candidate.get("player_id") or 0)
    current_value = int(candidate.get("current_value") or 0)

    if player_id <= 0 or current_value <= 0:
        raise RuntimeError("Candidato de salida incompleto.")

    preview = execute_sale_listing(
        player_id=player_id,
        price=current_value,
        execute=False,
    )

    return {
        "kind": "EXIT_LISTING",
        "candidate": candidate,
        "transport": preview,
        "writes_biwenger": False,
    }


def build_counter_preview(candidate: dict) -> dict:
    incoming_offer_id = int(
        candidate.get("incoming_offer_id") or 0
    )
    amount = int(
        candidate.get("recommended_counter") or 0
    )

    if incoming_offer_id <= 0:
        raise RuntimeError(
            "Sin incoming_offer_id no se puede reconstruir "
            "la respuesta a la oferta original."
        )
    if amount <= 0:
        raise RuntimeError("recommended_counter inválido.")

    writer = BiwengerWriteClient()
    preview = writer.counter_offer(
        offer_id=incoming_offer_id,
        amount=amount,
        execute=False,
    )

    return {
        "kind": "COUNTER_REPRICE",
        "candidate": candidate,
        "transport": preview,
        "writes_biwenger": False,
    }


def validate_current() -> dict:
    pm = sync_position_manager(refresh=True)
    cr = sync_counter_repricing(refresh=True)

    exit_candidate = select_exit_candidate(
        pm.get("board", {}) or {}
    )
    counter_candidate = select_counter_candidate(
        cr.get("board", {}) or {}
    )

    return {
        "version": "V10.9",
        "writes_biwenger": False,
        "exit_candidate": exit_candidate,
        "exit_preview": (
            build_exit_preview(exit_candidate)
            if exit_candidate else None
        ),
        "counter_candidate": counter_candidate,
        "counter_preview": (
            build_counter_preview(counter_candidate)
            if counter_candidate else None
        ),
    }


def execute_one(kind: str) -> dict:
    pm = sync_position_manager(refresh=True)
    cr = sync_counter_repricing(refresh=True)

    if kind == "exit":
        candidate = select_exit_candidate(
            pm.get("board", {}) or {}
        )
        if not candidate:
            raise RuntimeError(
                "No existe TAKE_PROFIT/CUT_LOSS/ROTATE_CAPITAL real ahora."
            )

        result = execute_sale_listing(
            player_id=int(candidate["player_id"]),
            price=int(candidate["current_value"]),
            execute=True,
        )

        return {
            "kind": "EXIT_LISTING",
            "candidate": candidate,
            "result": result,
        }

    candidate = select_counter_candidate(
        cr.get("board", {}) or {}
    )
    if not candidate:
        raise RuntimeError(
            "No existe RAISE_COUNTER real ahora."
        )

    writer = BiwengerWriteClient()
    result = writer.counter_offer(
        offer_id=int(candidate["incoming_offer_id"]),
        amount=int(candidate["recommended_counter"]),
        execute=True,
    )

    return {
        "kind": "COUNTER_REPRICE",
        "candidate": candidate,
        "result": result,
    }


def print_validation(result: dict) -> None:
    print("\n" + "=" * 100)
    print("BORDALAS IA - V10.9 WRITE TRANSPORT VALIDATION")
    print("=" * 100)
    print("Escrituras Biwenger: NO")

    exit_candidate = result.get("exit_candidate")
    if exit_candidate:
        transport = result["exit_preview"]["transport"]
        print("\nV10.6 EXIT:")
        print(
            f"{exit_candidate.get('player_name')} | "
            f"{exit_candidate.get('action')} | "
            f"player={exit_candidate.get('player_id')} | "
            f"value={int(exit_candidate.get('current_value') or 0):,}"
        )
        print(
            f"Transport: {transport.get('operation')} "
            f"{transport.get('method')} {transport.get('url')}"
        )
    else:
        print("\nV10.6 EXIT: SIN CANDIDATO REAL AHORA")

    counter_candidate = result.get("counter_candidate")
    if counter_candidate:
        transport = result["counter_preview"]["transport"]
        print("\nV10.7 REPRICE:")
        print(
            f"{counter_candidate.get('player_name')} -> "
            f"{counter_candidate.get('rival_name')} | "
            f"{int(counter_candidate.get('current_counter_amount') or 0):,} "
            f"-> {int(counter_candidate.get('recommended_counter') or 0):,}"
        )
        print(
            f"Transport: {transport.get('operation')} "
            f"{transport.get('method')} {transport.get('url')}"
        )
        print(f"Payload: {transport.get('json')}")
    else:
        print("\nV10.7 REPRICE: SIN RAISE_COUNTER REAL AHORA")

    print("\nCERO escrituras en esta validación.")
    print("=" * 100)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-current", action="store_true")
    parser.add_argument(
        "--execute-one",
        choices=["exit", "counter"],
    )
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()

    if args.validate_current:
        print_validation(validate_current())
        return

    if args.execute_one:
        if args.confirmation != "BORDALAS-V10.9":
            raise RuntimeError(
                "LIVE bloqueado: falta --confirmation BORDALAS-V10.9"
            )

        result = execute_one(args.execute_one)
        print("\nLIVE RESULT")
        print(result)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
