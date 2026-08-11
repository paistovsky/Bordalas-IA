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
    candidates = result.get("candidates", []) or []

    offer_board = (
        state.get(
            "offer_decisions",
            {},
        )
        or {}
    )

    offer_candidates = [
        item
        for item in candidates
        if item.get("type")
        == "OFFER_DECISION_INTELLIGENCE"
    ]

    legacy_recovery = [
        item
        for item in candidates
        if item.get("action")
        == "ACCEPT_RECOVERY_OFFER"
    ]

    solvency_guarantee = [
        item
        for item in candidates
        if item.get("type")
        == "SOLVENCY_GUARANTEE"
    ]

    print()
    print("=" * 118)
    print("          BORDALAS IA - OFFER AUTHORITY SEPARATION V1 - OBSERVER")
    print("=" * 118)
    print()

    print(f"Snapshot:                    {snapshot_file}")
    print(f"Ofertas evaluadas:           {offer_board.get('offer_count', 0)}")
    print(f"Legacy ACCEPT_RECOVERY:      {len(legacy_recovery)}")
    print(f"Solvency guarantee:          {len(solvency_guarantee)}")
    print()

    print("## OFFER INTELLIGENCE")
    print()

    if not offer_candidates:
        print("NINGUNA")
    else:
        item = offer_candidates[0]
        data = item.get("data", {}) or {}
        counts = data.get("summary_counts", {}) or {}

        print(
            f"type={item.get('type')} "
            f"priority={item.get('priority')} "
            f"action={item.get('action')} "
            f"executable={item.get('executable')}"
        )

        print(
            f"protections={counts.get('PROTECTIONS', 0)} "
            f"reserves={counts.get('SOLVENCY_RESERVES', 0)} "
            f"good={counts.get('GOOD_OFFERS', 0)} "
            f"hold={counts.get('HOLD_OFFERS', 0)} "
            f"actionable={counts.get('ACTIONABLE', 0)}"
        )

    print()
    print("## TOP PRIORIDADES")
    print()

    for index, item in enumerate(candidates[:8], start=1):
        print(
            f"{index}. "
            f"{str(item.get('type')):<30} "
            f"{int(item.get('priority', 0)):>4} "
            f"{item.get('action')} "
            f"exec={item.get('executable')}"
        )

    print()
    print("## SAFETY")
    print()

    if legacy_recovery:
        raise SystemExit(
            "ERROR: sigue existiendo ACCEPT_RECOVERY_OFFER legacy."
        )

    if offer_board.get("offer_count", 0) > 0 and not offer_candidates:
        raise SystemExit(
            "ERROR: hay ofertas pero falta OFFER_DECISION_INTELLIGENCE."
        )

    for item in offer_candidates:
        if item.get("action") != "MONITOR_OFFERS":
            raise SystemExit(
                "ERROR: protecciones/holds no deben convertirse "
                "en accion global."
            )

        if item.get("executable"):
            raise SystemExit(
                "ERROR: Offer Decision Intelligence sigue Observer."
            )

    # Si hay saldo negativo y el recovery clásico es posible,
    # debe quedar como garantía informativa, no aceptación directa.
    liquidity = state.get("liquidity", {}) or {}
    recovery = liquidity.get("recovery", {}) or {}
    balance = int(state.get("balance", 0) or 0)

    if (
        balance < 0
        and recovery.get("possible", False)
        and recovery.get("selected")
        and not solvency_guarantee
    ):
        raise SystemExit(
            "ERROR: falta SOLVENCY_GUARANTEE para un plan financiable."
        )

    print("OFFER AUTHORITY SEPARATION V1 OBSERVER: OK")
    print("=" * 118)


if __name__ == "__main__":
    main()
