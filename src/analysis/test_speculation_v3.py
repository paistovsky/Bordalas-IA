from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


def money(value) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    board = build_speculation_board(
        snapshot
    )

    solvency = board["solvency"]
    budget = board["budget"]
    guarantee = solvency.get(
        "solvency_guarantee",
        {},
    )
    safe_debt = solvency.get(
        "max_safe_debt",
        {},
    )

    print()
    print("=" * 100)
    print(
        "                    BORDALAS IA - SPECULATION ENGINE V3"
    )
    print("=" * 100)
    print()

    print(f"Snapshot:                   {snapshot_file}")
    print(f"Saldo:                      {money(solvency['balance'])}")
    print(f"Garantia T-15:              {'SI' if guarantee.get('guaranteed') else 'NO'}")
    print(f"Estado garantia:            {guarantee.get('state')}")
    print(f"MAX_SAFE_DEBT total:        {money(safe_debt.get('max_total_debt'))}")
    print(f"Margen deuda adicional:     {money(safe_debt.get('additional_debt_headroom'))}")

    print()
    print("## PRESUPUESTO ESPECULATIVO")
    print(f"Modo:                       {budget.get('mode')}")
    print(f"Habilitado:                 {'SI' if budget.get('enabled') else 'NO'}")
    print(f"Presupuesto total:          {money(budget.get('total_budget'))}")
    print(f"Limite una operacion:       {money(budget.get('single_operation_limit'))}")
    print(f"Bloqueado por:              {budget.get('blocked_by') or 'NINGUNO'}")
    print(f"Motivo:                     {budget.get('reason')}")

    if budget.get("raw_authorized_budget") is not None:
        print(
            f"Budget teorico por deuda:    "
            f"{money(budget.get('raw_authorized_budget'))}"
        )

    print()
    print("## TOP OPORTUNIDADES")

    candidates = board.get(
        "buy_candidates",
        [],
    )[:10]

    if not candidates:
        print("NINGUNA")
    else:
        for player in candidates:
            print(
                f"{player.get('name', '?'):<24} "
                f"score={player.get('speculation_score', 0):>5} "
                f"precio={money(player.get('price', 0)):>15} "
                f"inc={money(player.get('price_increment', 0)):>13} "
                f"accion={player.get('speculation_action')}"
            )

    print()
    print("## COMPRAS EJECUTABLES POR PRESUPUESTO")

    executable = board.get(
        "executable_buys",
        [],
    )

    if not executable:
        print("NINGUNA")
    else:
        for player in executable:
            print(
                f"{player.get('name', '?'):<24} "
                f"{money(player.get('price', 0))}"
            )

    # Safety assertions.
    if (
        solvency["balance"] < 0
        and budget.get("enabled")
        and not guarantee.get("guaranteed")
    ):
        raise SystemExit(
            "ERROR: especulacion habilitada sin garantia T-15."
        )

    if (
        budget.get("enabled")
        and budget.get("mode") == "DEBT"
        and int(budget.get("total_budget", 0) or 0)
        > int(safe_debt.get("additional_debt_headroom", 0) or 0)
    ):
        raise SystemExit(
            "ERROR: presupuesto supera MAX_SAFE_DEBT."
        )

    print()
    print("SAFETY SPECULATION V3: OK")
    print("=" * 100)


if __name__ == "__main__":
    main()
