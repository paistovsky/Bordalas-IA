from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.transaction_planner import (
    POSITION_NAMES,
    simulate_transactions,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    result = simulate_transactions(
        snapshot
    )

    print()
    print("=" * 80)
    print(
        "        BORDALÁS IA - TRANSACTION PLANNER"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        f"Plantilla actual: "
        f"{result['original_count']} jugadores"
    )

    print()
    print("COMPRAS")
    print("-" * 80)

    for player in result[
        "purchases"
    ]:

        print(
            f"{player['name']:<22}"
            f"{player['suggested_bid']:>12,} €"
        )

    print()
    print("VENTAS NECESARIAS")
    print("-" * 80)

    if not result[
        "mandatory_sales"
    ]:

        print("Ninguna.")

    else:

        for player in result[
            "mandatory_sales"
        ]:

            print(
                f"{player['name']:<22}"
                f"{player['price']:>12,} €"
            )

    print()
    print("VENTAS OPCIONALES SEGURAS")
    print("-" * 80)

    if not result[
        "safe_optional_sales"
    ]:

        print("Ninguna.")

    else:

        for player in result[
            "safe_optional_sales"
        ]:

            print(
                f"{player['name']:<22}"
                f"{player['price']:>12,} €"
                f"   Sale score "
                f"{player['sale_score']:>3}/100"
            )

    print()
    print("PLANTILLA PROYECTADA")
    print("-" * 80)

    print(
        "Antes de ventas opcionales: "
        f"{result['projected_count_before_optional']}"
    )

    print(
        "Después de ventas opcionales: "
        f"{result['projected_count_after_optional']}"
    )

    print()
    print("DISTRIBUCIÓN FINAL")
    print("-" * 80)

    for position_id in [
        1,
        2,
        3,
        4,
    ]:

        print(
            f"{POSITION_NAMES[position_id]:<18}"
            f"{result['final_position_counts'][position_id]}"
        )

    print()
    print("ECONOMÍA")
    print("-" * 80)

    print(
        "Saldo tras compras:       "
        f"{result['projected_balance_without_optional']:>12,} €"
    )

    print(
        "Ingresos ventas opcionales:"
        f"{result['optional_sale_income']:>12,} €"
    )

    print(
        "Saldo final proyectado:   "
        f"{result['projected_balance_with_optional']:>12,} €"
    )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()