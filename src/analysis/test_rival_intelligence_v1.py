from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
    save_rival_intelligence,
)
from src.collectors.board_history_collector import (
    collect_board_history,
)


def money(value) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:
    board = collect_board_history()

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    intelligence = build_rival_intelligence(
        events=board.get("events", []),
        users=board.get("users", []),
        catalog=snapshot.get("catalog", {}),
        current_user_id=board.get("current_user_id"),
        own_finances=board.get("own_finances", {}),
    )

    save_rival_intelligence(intelligence)

    validation = intelligence.get("validation", {}) or {}

    print()
    print("=" * 120)
    print("BORDALAS IA - RIVAL INTELLIGENCE V1")
    print("=" * 120)
    print(f"Snapshot:             {snapshot_file}")
    print(f"Eventos API:          {board.get('api_events')}")
    print(f"Eventos era actual:   {board.get('current_era_events')}")
    print(f"Eventos persistidos:  {board.get('persisted_events')}")
    print(f"Eventos nuevos:       {board.get('new_events')}")
    print(f"Saldo inicial liga:   {money(intelligence.get('initial_balance'))}")

    print()
    print("## VALIDACION CONTABLE PEPE")
    print(f"Saldo oficial:        {money(validation.get('official_balance'))}")
    print(f"Saldo ledger:         {money(validation.get('ledger_balance'))}")
    print(f"Diferencia:           {money(validation.get('difference'))}")
    print(f"Ledger status:        {intelligence.get('ledger_status')}")

    print()
    print("## MANAGERS")
    print(
        f"{'MANAGER':<34} {'SALDO':>14} {'INGRESOS':>14} "
        f"{'GASTOS':>14} {'BUY':>4} {'SELL':>5} {'BIDS':>5} {'PERFIL':>11}"
    )
    print("-" * 108)

    for manager in intelligence.get("managers", []) or []:
        sells = (
            manager.get("sales_to_computer", 0)
            + manager.get("user_to_user_sales", 0)
        )
        buys = (
            manager.get("market_buys", 0)
            + manager.get("user_to_user_buys", 0)
        )

        print(
            f"{manager.get('name','?'):<34} "
            f"{money(manager.get('balance')):>14} "
            f"{money(manager.get('income')):>14} "
            f"{money(manager.get('expenses')):>14} "
            f"{buys:>4} "
            f"{sells:>5} "
            f"{manager.get('lost_bids',0):>5} "
            f"{manager.get('profile','?'):>11}"
        )

    print()
    print("## SAFETY ASSERTIONS")

    errors = []

    if not validation.get("available", False):
        errors.append("No se pudo validar la contabilidad de Pepe.")

    if not validation.get("exact", False):
        errors.append("El ledger de Pepe NO cuadra con /finances.")

    if intelligence.get("ledger_status") != "EXACT":
        errors.append("Ledger status distinto de EXACT.")

    if intelligence.get("unknown_types"):
        errors.append("Hay tipos de tablón no clasificados.")

    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit("RIVAL INTELLIGENCE V1: FAILED")

    print("# RIVAL INTELLIGENCE V1: OK")
    print("=" * 120)


if __name__ == "__main__":
    main()
