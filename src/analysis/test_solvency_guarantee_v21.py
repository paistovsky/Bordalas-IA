from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)


def money(value) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)
    state = build_solvency_state(snapshot)

    guarantee = state["solvency_guarantee"]
    reservations = state["solvency_reservations"]
    safe_debt = state["max_safe_debt"]

    print()
    print("=" * 100)
    print("                    BORDALAS IA - SOLVENCY GUARANTEE V2.1")
    print("=" * 100)
    print()

    print(f"Snapshot:                    {snapshot_file}")
    print(f"Saldo:                       {money(state['balance'])}")
    print(f"Estado garantia:             {guarantee['state']}")
    print(f"Garantia T-15:               {'SI' if guarantee['guaranteed'] else 'NO'}")

    print()
    print("## FUENTE UNICA DE VERDAD")
    print(f"Deuda actual:                {money(guarantee['current_debt'])}")
    print(f"Buffer obligatorio:          {money(guarantee['safety_buffer'])}")
    print(f"Recuperacion requerida:      {money(guarantee['required_recovery'])}")
    print(f"SECURED_LIQUIDITY:           {money(guarantee['secured_liquidity'])}")
    print(f"EXPECTED_LIQUIDITY:          {money(guarantee['expected_liquidity'])}")
    print(f"Liquidez conservadora total: {money(guarantee['guaranteed_recovery'])}")
    print(f"Margen garantia:             {money(guarantee['guarantee_surplus'])}")

    print()
    print("## SOLVENCY RESERVED")
    print(f"Expected usado (sin 2o cut): {money(reservations['expected_credit'])}")
    print(f"Secured necesario:           {money(reservations.get('secured_needed', 0))}")
    print(f"Importe reservado:           {money(reservations['reserved_total'])}")
    print(f"Cobertura coherente:         {'SI' if reservations['covered'] else 'NO'}")

    for offer in reservations.get("reserved", []):
        names = ", ".join(
            player.get("name", "?")
            for player in offer.get("players", [])
        )
        print(f"RESERVED | {names:<24} {money(offer.get('amount', 0)):>16}")

    print()
    print("## MAX SAFE DEBT")
    print(f"Deuda total maxima segura:   {money(safe_debt['max_total_debt'])}")
    print(f"Margen deuda adicional:      {money(safe_debt['additional_debt_headroom'])}")
    print(f"Ventana deuda abierta:       {'SI' if safe_debt['debt_window_open'] else 'NO'}")
    print(f"Deuda temporal permitida:    {'SI' if state['temporary_debt'].get('allowed') else 'NO'}")

    coherent = (
        guarantee["guaranteed"]
        == reservations["covered"]
    )

    print()
    print(f"COHERENCIA GUARANTEE/RESERVE: {'OK' if coherent else 'ERROR'}")

    if not coherent:
        raise SystemExit(
            "ERROR: SOLVENCY_GUARANTEE y SOLVENCY_RESERVED discrepan."
        )

    if (
        safe_debt["additional_debt_headroom"] > 0
        and not guarantee["guaranteed"]
    ):
        raise SystemExit(
            "ERROR: hay margen de deuda sin garantia de solvencia."
        )

    print("=" * 100)


if __name__ == "__main__":
    main()
