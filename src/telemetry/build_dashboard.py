from src.telemetry.dashboard_state import (
    build_dashboard_state,
    save_dashboard_state,
)


def main() -> None:
    print()
    print("=" * 78)
    print("BORDALAS IA - SALA DE OPERACIONES - TELEMETRIA V0.1")
    print("=" * 78)

    state = build_dashboard_state()
    path = save_dashboard_state(state)

    rivals = (
        state.get("rival_intelligence", {})
        .get("managers", [])
        or []
    )

    lineup = state.get("lineup", {}) or {}

    print(f"Archivo:       {path}")
    print(f"Rivales:       {len(rivals)} managers")
    print(f"XI:            {lineup.get('playable', 0)}/11")
    print(
        "Ledger rival: "
        f"{state.get('rival_intelligence', {}).get('ledger_status')}"
    )
    print(
        "Decision:      "
        f"{state.get('decision', {}).get('label')}"
    )
    print()
    print("# DASHBOARD TELEMETRY V0.1: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()
