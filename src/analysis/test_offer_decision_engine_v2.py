from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)


def money(
    value,
) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    board = (
        build_offer_decision_board(
            snapshot
        )
    )

    print()
    print("=" * 125)
    print("                     BORDALAS IA - OFFER DECISION ENGINE V2 - OBSERVER")
    print("=" * 125)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print(
        f"Ofertas evaluadas:           "
        f"{board['offer_count']}"
    )

    print(
        f"ACCEPT_FOR_SOLVENCY:         "
        f"{len(board['accept_for_solvency'])}"
    )

    print(
        f"HOLD_SOLVENCY_RESERVED:      "
        f"{len(board['hold_solvency_reserved'])}"
    )

    print(
        f"ACCEPT_NOW:                  "
        f"{len(board['accept_now'])}"
    )

    print(
        f"REROLL_CANDIDATE:            "
        f"{len(board['reroll_candidates'])}"
    )

    print(
        f"NEVER_SELL:                  "
        f"{len(board['never_sell'])}"
    )

    print()
    print("## DECISIONES")
    print()

    for item in board[
        "decisions"
    ]:

        print(
            f"{str(item.get('player_name') or '?'):<24} "
            f"{money(item.get('amount')):>15} "
            f"{str(item.get('counterparty_type') or '?'):<8} "
            f"premium={item.get('premium_percent'):>+6.2f}% "
            f"sale={item.get('sale_score'):>5.1f} "
            f"spec={item.get('speculation_score'):>5.1f} "
            f"fr={item.get('franchise_score'):>5.1f} "
            f"econ={item.get('economic_score'):>5.1f} "
            f"-> {item.get('decision')}"
        )

        for reason in item.get(
            "reasons",
            [],
        ):
            print(
                f"    - {reason}"
            )

    print()
    print("## SAFETY")
    print()

    for item in board[
        "decisions"
    ]:

        if item.get(
            "automatic"
        ):
            raise SystemExit(
                "ERROR: V2 Observer ha autorizado una venta automatica."
            )

        if not item.get(
            "observer_only"
        ):
            raise SystemExit(
                "ERROR: una decision no esta marcada como Observer."
            )


        if (
            item.get("decision") == "ACCEPT_FOR_SOLVENCY"
            and
            item.get("reroll_action") != "ACCEPT_BEFORE_EXPIRY"
        ):
            raise SystemExit(
                "ERROR: ACCEPT_FOR_SOLVENCY sin ACCEPT_BEFORE_EXPIRY."
            )

        if (
            item.get("counterparty_type") == "COMPUTER"
            and
            item.get("solvency_reserved")
            and
            item.get("reroll_action") != "ACCEPT_BEFORE_EXPIRY"
            and
            item.get("decision") != "HOLD_SOLVENCY_RESERVED"
        ):
            raise SystemExit(
                "ERROR: oferta SOLVENCY_RESERVED no está protegida "
                "como HOLD_SOLVENCY_RESERVED."
            )

        if (
            item.get("decision") == "REROLL_CANDIDATE"
            and
            item.get("counterparty_type") == "COMPUTER"
            and
            item.get("reroll_action") != "REROLL_CANDIDATE"
        ):
            raise SystemExit(
                "ERROR: V2 contradice al Computer Reroll Engine."
            )

        if (
            item.get(
                "decision"
            )
            == "NEVER_SELL"
            and
            item.get(
                "franchise_score",
                0,
            )
            < 70
            and
            item.get(
                "protection"
            )
            != "NEVER_AUTO_SELL"
        ):
            raise SystemExit(
                "ERROR: NEVER_SELL sin proteccion suficiente."
            )

    print(
        "OFFER DECISION ENGINE V2 OBSERVER: OK"
    )

    print("=" * 125)


if __name__ == "__main__":
    main()
