import argparse
import sys

from src.actions.action_plan import (
    build_action_plan,
)
from src.actions.multi_bid_executor import (
    execute_bid_plan,
)
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.biwenger.write_client import (
    BiwengerWriteClient,
)
from src.actions.live_bid_executor import (
    find_existing_offer,
    get_sale_for_player,
    get_seller_description,
)


def get_current_bid_status(
    bids: list[dict],
) -> list[dict]:
    """
    Consulta Biwenger ahora mismo y genera
    una vista previa del plan.
    """

    writer = BiwengerWriteClient()

    market = writer.client.get_market()

    statuses = []

    for bid in bids:
        player_id = int(
            bid["player_id"]
        )

        sale = get_sale_for_player(
            market,
            player_id,
        )

        existing_offer = (
            find_existing_offer(
                market,
                player_id,
            )
        )

        status = {
            **bid,
            "already_bid":
                existing_offer is not None,
            "in_market":
                sale is not None,
        }

        if sale is not None:
            status["seller"] = (
                get_seller_description(
                    sale
                )
            )

            status["current_price"] = (
                sale.get(
                    "price",
                    0,
                )
            )

        statuses.append(
            status
        )

    return statuses


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Bordalás IA - "
            "Plan de compras"
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Envía realmente las pujas "
            "a Biwenger."
        ),
    )

    args = parser.parse_args()

    print()
    print("=" * 80)
    print(
        "             BORDALÁS IA - LIVE PLAN"
    )
    print("=" * 80)

    # ==================================================
    # SNAPSHOT + PLAN
    # ==================================================

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    plan = build_action_plan(
        snapshot
    )

    bids = plan.get(
        "bids",
        [],
    )

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print(
        f"Pujas propuestas: {len(bids)}"
    )

    if not bids:
        print()
        print(
            "No hay compras recomendadas."
        )
        return

    # ==================================================
    # CONSULTAR ESTADO ACTUAL
    # ==================================================

    print()
    print(
        "Consultando mercado actual..."
    )

    try:
        statuses = (
            get_current_bid_status(
                bids
            )
        )

    except Exception as error:
        print()
        print(
            "No se ha podido consultar "
            "el mercado actual."
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        sys.exit(1)

    print()
    print("## PLAN ACTUAL")
    print()

    for index, item in enumerate(
        statuses,
        start=1,
    ):
        name = item.get(
            "player_name",
            f"ID {item['player_id']}",
        )

        amount = int(
            item["amount"]
        )

        score = item.get(
            "score",
            0,
        )

        print(
            f"{index}. {name}"
        )

        print(
            f"   Puja:      "
            f"{amount:,} €"
        )

        print(
            f"   Score:     "
            f"{score}/100"
        )

        if item["already_bid"]:
            print(
                "   Estado:    "
                "YA PUJADO → OMITIR"
            )

        elif not item["in_market"]:
            print(
                "   Estado:    "
                "FUERA DEL MERCADO → OMITIR"
            )

        else:
            print(
                "   Estado:    "
                "LISTO"
            )

            print(
                f"   Origen:    "
                f"{item.get('seller')}"
            )

            print(
                f"   Precio:    "
                f"{item.get('current_price', 0):,} €"
            )

        print()

    # ==================================================
    # MODO
    # ==================================================

    if not args.live:
        print("=" * 80)
        print()
        print(
            "MODO DRY-RUN"
        )

        print(
            "Ejecutando todos los preflight "
            "sin enviar operaciones..."
        )

    else:
        print("=" * 80)
        print()
        print(
            "*** MODO LIVE ***"
        )

        print(
            "Las pujas válidas serán enviadas "
            "a Biwenger una por una."
        )

    # ==================================================
    # EJECUCIÓN
    # ==================================================

    try:
        result = execute_bid_plan(
            bids=bids,
            execute=args.live,
            stop_on_error=True,
        )

    except Exception as error:
        print()
        print(
            "ERROR GENERAL DEL EJECUTOR"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        sys.exit(1)

    # ==================================================
    # RESULTADOS
    # ==================================================

    print()
    print("=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print()

    for item in result["results"]:
        print(
            f"{item['index']}. "
            f"{item['player_name']}"
        )

        print(
            f"   {item['status']}"
        )

        print(
            f"   {item.get('message', '')}"
        )

        print()

    print("-" * 80)

    if args.live:
        print(
            f"Pujas ejecutadas: "
            f"{result['executed']}"
        )

    print(
        f"Omitidas:         "
        f"{result['skipped']}"
    )

    print(
        f"Errores:          "
        f"{result['failed']}"
    )

    print()

    if not args.live:
        print(
            "NO SE HA MODIFICADO BIWENGER."
        )

    elif result["failed"] == 0:
        print(
            "✅ PLAN DE COMPRAS "
            "EJECUTADO SIN ERRORES."
        )

    else:
        print(
            "⚠ EJECUCIÓN DETENIDA "
            "POR SEGURIDAD."
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()