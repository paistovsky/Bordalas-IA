from __future__ import annotations

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)


def format_dt(value) -> str:
    if value is None:
        return "NINGUNO"

    try:
        return value.strftime(
            "%d/%m/%Y %H:%M"
        )
    except AttributeError:
        return str(value)


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)
    state = build_solvency_state(snapshot)

    cycles = state["computer_cycles"]
    secured = state["secured_liquidity"]
    expected = state["expected_liquidity"]
    reserved = state["solvency_reservations"]
    safe_debt = state["max_safe_debt"]

    print()
    print("=" * 100)
    print(
        "              BORDALAS IA - COMPUTER CYCLE / SOLVENCY V2"
    )
    print("=" * 100)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )
    print(
        f"Saldo:                       "
        f"{state['balance']:,.0f} EUR"
    )
    print(
        f"Fase:                        "
        f"{state['phase']}"
    )
    print(
        f"Deadline T-15:               "
        f"{format_dt(cycles.get('real_deadline'))}"
    )

    print()
    print(
        f"Ciclos Computer seguros:     "
        f"{cycles.get('safe_cycles_remaining')}"
    )
    print(
        f"Ciclos para NUEVA venta:     "
        f"{cycles.get('new_listing_cycles_remaining')}"
    )
    print(
        f"Ultimo ciclo seguro:         "
        f"{format_dt((cycles.get('last_safe_cycle') or {}).get('cycle_end'))}"
    )
    print(
        f"Ultimo dia seguro de lista:  "
        f"{cycles.get('last_safe_listing_day') or 'NINGUNO'}"
    )
    print(
        f"Hora limite operativa lista: "
        f"{format_dt(cycles.get('last_safe_listing_deadline'))}"
    )

    print()
    print("## CICLOS SEGUROS")

    for cycle in cycles.get(
        "safe_cycles",
        [],
    ):
        print(
            "- "
            f"{cycle['date']} | "
            f"Computer "
            f"{format_dt(cycle['cycle_start'])}"
            f"-{cycle['cycle_end'].strftime('%H:%M')} | "
            f"listar antes "
            f"{format_dt(cycle['safe_listing_deadline'])}"
        )

    print()
    print("## LIQUIDEZ")

    print(
        f"Ofertas Computer vigentes:   "
        f"{secured.get('count')}"
    )
    print(
        f"SECURED_LIQUIDITY:           "
        f"{secured.get('secured_total', 0):,.0f} EUR"
    )
    print(
        f"EXPECTED_LIQUIDITY:          "
        f"{expected.get('total', 0):,.0f} EUR"
    )
    print(
        f"Activos esperados:           "
        f"{len(expected.get('players', []))}"
    )

    print()

    for offer in secured.get(
        "offers",
        [],
    ):
        names = ", ".join(
            player.get(
                "name",
                "?"
            )
            for player in offer.get(
                "players",
                [],
            )
        )

        print(
            f"OFERTA | {names:<24} "
            f"{offer.get('amount', 0):>10,.0f} EUR | "
            f"caduca "
            f"{format_dt(offer.get('expires_at'))}"
        )

    print()
    print("## SOLVENCY RESERVED")

    print(
        f"Recuperacion requerida:      "
        f"{reserved.get('required_recovery', 0):,.0f} EUR"
    )
    print(
        f"Credito expected conservador:"
        f" {reserved.get('expected_credit', 0):,.0f} EUR"
    )
    print(
        f"Ofertas reservadas:          "
        f"{len(reserved.get('reserved', []))}"
    )
    print(
        f"Importe reservado:           "
        f"{reserved.get('reserved_total', 0):,.0f} EUR"
    )
    print(
        f"Cobertura reservada:         "
        f"{'SI' if reserved.get('covered') else 'NO'}"
    )

    for offer in reserved.get(
        "reserved",
        [],
    ):
        names = ", ".join(
            player.get(
                "name",
                "?"
            )
            for player in offer.get(
                "players",
                [],
            )
        )

        print(
            f"RESERVED | {names:<22} "
            f"{offer.get('amount', 0):>10,.0f} EUR"
        )

    print()
    print("## MAX SAFE DEBT")

    print(
        f"Deuda actual:                "
        f"{safe_debt.get('current_debt', 0):,.0f} EUR"
    )
    print(
        f"Deuda total maxima segura:   "
        f"{safe_debt.get('max_total_debt', 0):,.0f} EUR"
    )
    print(
        f"Margen deuda adicional:      "
        f"{safe_debt.get('additional_debt_headroom', 0):,.0f} EUR"
    )
    print(
        f"Ventana deuda abierta:       "
        f"{'SI' if safe_debt.get('debt_window_open') else 'NO'}"
    )
    print(
        f"Deuda temporal permitida:    "
        f"{'SI' if state['temporary_debt'].get('allowed') else 'NO'}"
    )
    print(
        f"Motivo:                      "
        f"{state['temporary_debt'].get('reason')}"
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
