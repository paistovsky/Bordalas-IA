import argparse
import sys

from src.actions.live_sale_executor import (
    execute_sale_listing,
)

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


def find_sale_candidate(
    player_id: int,
) -> dict | None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    sales = analyze_sales(
        snapshot
    )

    for player in sales:
        if player["id"] == player_id:
            return player

    return None


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Bordalás IA - "
            "Publicar jugador en mercado"
        )
    )

    parser.add_argument(
        "--player-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--live",
        action="store_true",
    )

    args = parser.parse_args()

    player = find_sale_candidate(
        args.player_id
    )

    if player is None:
        print(
            "Jugador no encontrado "
            "en la plantilla analizada."
        )
        sys.exit(1)

    pricing = calculate_sale_price(
        player
    )

    print()
    print("=" * 80)
    print(
        "           BORDALÁS IA - SINGLE SALE"
    )
    print("=" * 80)

    print()
    print(
        f"Jugador:      "
        f"{player['name']}"
    )

    print(
        f"Player ID:    "
        f"{player['id']}"
    )

    print(
        f"Valor:        "
        f"{player['price']:,} €"
    )

    print(
        f"Sale score:   "
        f"{player['sale_score']}/100"
    )

    print(
        f"Estrategia:   "
        f"{pricing['strategy']}"
    )

    if not pricing[
        "should_list"
    ]:

        print()
        print(
            "BLOQUEADO:"
        )

        print(
            "Bordalás IA no recomienda "
            "poner este jugador en mercado."
        )

        sys.exit(1)

    recommended_price = (
        pricing[
            "recommended_price"
        ]
    )

    print(
        f"Precio venta: "
        f"{recommended_price:,} €"
    )

    print()

    if args.live:
        print(
            "*** MODO LIVE ***"
        )

        print(
            "El jugador será publicado "
            "en Biwenger."
        )

    else:
        print(
            "MODO DRY-RUN"
        )

        print(
            "No se modificará Biwenger."
        )

    try:
        result = execute_sale_listing(
            player_id=
                args.player_id,

            price=
                recommended_price,

            execute=
                args.live,
        )

    except Exception as error:

        print()
        print(
            "OPERACIÓN BLOQUEADA"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        sys.exit(1)

    print()
    print(
        f"Estado: "
        f"{result['status']}"
    )

    if result[
        "status"
    ] == "ALREADY_LISTED":

        print(
            "El jugador ya está "
            "en el mercado."
        )

        return

    if not args.live:

        print()
        print(
            "DRY-RUN CORRECTO."
        )

        print(
            "No se ha modificado Biwenger."
        )

        return

    print(
        f"HTTP:   "
        f"{result.get('http_status')}"
    )

    print(
        f"Éxito:  "
        f"{'SÍ' if result['success'] else 'NO'}"
    )

    print(
        "Listado detectado después: "
        f"{'SÍ' if result.get('listing_detected_after') else 'NO'}"
    )

    if (
        result["success"]
        and
        result.get(
            "listing_detected_after"
        )
    ):
        print()
        print(
            "✅ JUGADOR PUBLICADO "
            "CORRECTAMENTE"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()