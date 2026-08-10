from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def money(value) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    result = build_global_decision(
        snapshot
    )

    state = result["state"]
    offer_reroll = state["offer_reroll"]

    print()
    print("=" * 110)
    print("              BORDALAS IA - OFFER INTELLIGENCE OBSERVER INTEGRATION")
    print("=" * 110)
    print()

    print(f"Snapshot:                   {snapshot_file}")
    print(f"Ofertas Computer:           {offer_reroll.get('offer_count', 0)}")
    print(
        f"Reroll candidatos:          "
        f"{len(offer_reroll.get('reroll_candidates', []) or [])}"
    )
    print(
        f"Accept-before-expiry watch: "
        f"{len(offer_reroll.get('accept_before_expiry', []) or [])}"
    )

    print()
    print("## OFERTAS")

    for offer in offer_reroll.get("offers", []) or []:
        names = ", ".join(
            player.get("name", "?")
            for player in offer.get("players", [])
        )

        simulation = offer.get("simulation", {}) or {}

        print(
            f"{names:<24} "
            f"{money(offer.get('amount')):>15} "
            f"reserved={'SI' if offer.get('solvency_reserved') else 'NO':<2} "
            f"safe={'SI' if offer.get('reroll_safe') else 'NO':<2} "
            f"margin={money(simulation.get('projected_surplus')):>15} "
            f"{offer.get('action')}"
        )

    print()
    print("## CANDIDATOS ORCHESTRATOR")

    observer_candidates = [
        candidate
        for candidate in result.get("candidates", [])
        if candidate.get("type") in {
            "COMPUTER_OFFER_REROLL_WATCH",
            "COMPUTER_OFFER_EXPIRY_WATCH",
        }
    ]

    if not observer_candidates:
        print("NINGUNO")
    else:
        for candidate in observer_candidates:
            print(
                f"{candidate.get('type'):<32} "
                f"priority={candidate.get('priority')} "
                f"action={candidate.get('action')} "
                f"executable={candidate.get('executable')}"
            )

    print()
    print("## SAFETY")

    for candidate in observer_candidates:
        if candidate.get("executable"):
            raise SystemExit(
                "ERROR: Offer Intelligence observer ha creado una accion ejecutable."
            )

        if candidate.get("executor") is not None:
            raise SystemExit(
                "ERROR: Offer Intelligence observer tiene executor asignado."
            )

    print("OFFER INTELLIGENCE OBSERVER: OK")
    print("=" * 110)


if __name__ == "__main__":
    main()
