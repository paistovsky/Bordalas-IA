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

    lifecycle = state.get(
        "listing_lifecycle",
        {},
    ) or {}

    print()
    print("=" * 110)
    print("             BORDALAS IA - LISTING LIFECYCLE ORCHESTRATOR TEST")
    print("=" * 110)
    print()

    print(f"Snapshot:                  {snapshot_file}")
    print(f"Publicaciones:             {lifecycle.get('listing_count')}")
    print(f"Renovacion requerida:      {lifecycle.get('renew_required_count')}")

    print()
    print("## RENOVACIONES")

    for item in lifecycle.get("renew_required", []) or []:
        print(
            f"{item.get('name'):<24} "
            f"restan={item.get('hours_to_expiry')}h "
            f"precio={item.get('listed_price')} "
            f"action={item.get('action')}"
        )

    print()
    print("## CANDIDATOS")

    candidates = [
        c
        for c in result.get("candidates", [])
        if c.get("type") == "MARKET_LISTING_RENEW"
    ]

    if not candidates:
        print("NINGUNO")
    else:
        for c in candidates:
            print(
                f"type={c.get('type')} "
                f"priority={c.get('priority')} "
                f"action={c.get('action')} "
                f"executable={c.get('executable')}"
            )

    print()
    print("## SAFETY")

    # Feature flag debe seguir apagado en esta fase.
    for c in candidates:
        if c.get("executable"):
            raise SystemExit(
                "ERROR: renovacion LIVE activada antes de validacion."
            )

    print("LISTING LIFECYCLE ORCHESTRATOR: OK")
    print("=" * 110)


if __name__ == "__main__":
    main()
