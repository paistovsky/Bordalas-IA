from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.sale_price_engine import (
    calculate_sale_price,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    players = analyze_sales(
        snapshot
    )

    print()
    print("=" * 80)
    print(
        "          BORDALÁS IA - SALE PRICE ENGINE"
    )
    print("=" * 80)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()

    for player in players:

        pricing = (
            calculate_sale_price(
                player
            )
        )

        print(
            player["name"].upper()
        )

        print(
            f"Valor Biwenger:    "
            f"{player['price']:>12,} €"
        )

        print(
            f"Sale score:        "
            f"{player['sale_score']:>3}/100"
        )

        print(
            f"En XI:             "
            f"{'SÍ' if player['in_lineup'] else 'NO'}"
        )

        print(
            f"Estrategia:        "
            f"{pricing['strategy']}"
        )

        if not pricing[
            "should_list"
        ]:

            print(
                "Precio recomendado: "
                "NO PONER EN MERCADO"
            )

        else:

            print(
                f"Multiplicador:     "
                f"x{pricing['multiplier']:.2f}"
            )

            print(
                f"Precio recomendado:"
                f" "
                f"{pricing['recommended_price']:>12,} €"
            )

            print(
                f"Prima:             "
                f"{pricing['premium']:>12,} €"
                f" "
                f"({pricing['premium_percent']:+.1f}%)"
            )

        print("-" * 80)


if __name__ == "__main__":
    main()