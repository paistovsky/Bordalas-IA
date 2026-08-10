import json

from src.actions.action_plan import (
    build_action_plan,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


def print_request(
    request: dict,
) -> None:

    print()
    print("-" * 80)

    print(
        f"OPERACIÓN: "
        f"{request.get('operation')}"
    )

    if (
        request.get("status")
        == "NOT_IMPLEMENTED"
    ):

        print(
            "ESTADO: NO IMPLEMENTADA"
        )

        print(
            f"Motivo: "
            f"{request.get('reason')}"
        )

        print(
            f"Player ID: "
            f"{request.get('player_id')}"
        )

        return

    print(
        f"Método: "
        f"{request['method']}"
    )

    print(
        f"URL: "
        f"{request['url']}"
    )

    print()
    print("PAYLOAD")

    print(
        json.dumps(
            request["json"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        "EXECUTE: FALSE"
    )


def find_market_seller(
    snapshot: dict,
    player_id: int,
) -> int | None:

    sales = (
        snapshot["market"]
        .get("sales", [])
    )

    for sale in sales:

        sale_player_id = (
            sale
            .get("player", {})
            .get("id")
        )

        if sale_player_id != player_id:
            continue

        user = sale.get("user")

        if not user:
            return None

        return user.get("id")

    return None


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    plan = build_action_plan(
        snapshot
    )

    print()
    print("=" * 80)
    print(
        "       BORDALÁS IA - WRITE CLIENT DRY-RUN"
    )
    print("=" * 80)

    print()
    print(
        "ESTE TEST NO ENVÍA POST NI PUT."
    )

    print(
        "Solo construye las peticiones."
    )

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    writer = BiwengerWriteClient()

    # ==================================================
    # PUJAS
    # ==================================================

    print()
    print("=" * 80)
    print("PUJAS")
    print("=" * 80)

    for bid in plan["bids"]:

        seller_user_id = (
            find_market_seller(
                snapshot,
                bid["player_id"],
            )
        )

        request = (
            writer.build_bid_request(
                player_id=bid[
                    "player_id"
                ],
                amount=bid[
                    "amount"
                ],
                seller_user_id=
                    seller_user_id,
            )
        )

        print()
        print(
            f"Jugador: "
            f"{bid['player_name']}"
        )

        print(
            f"Vendedor ID: "
            f"{seller_user_id}"
        )

        print_request(
            request
        )

    # ==================================================
    # VENTAS
    # ==================================================

    print()
    print("=" * 80)
    print("VENTAS")
    print("=" * 80)

    all_sales = (
        plan["mandatory_sales"]
        + plan["optional_sales"]
    )

    if not all_sales:

        print()
        print("Ninguna.")

    for sale in all_sales:

        request = (
            writer.build_sale_request(
                player_id=sale[
                    "player_id"
                ],
                price=sale[
                    "estimated_value"
                ],
            )
        )

        print()
        print(
            f"Jugador: "
            f"{sale['player_name']}"
        )

        print_request(
            request
        )

    # ==================================================
    # ALINEACIÓN
    # ==================================================

    print()
    print("=" * 80)
    print("ALINEACIÓN")
    print("=" * 80)

    player_ids = [
        player["player_id"]
        for player in plan["lineup"]
    ]

    lineup_request = (
        writer.build_lineup_request(
            player_ids=player_ids,
            formation="4-3-3",
        )
    )

    print_request(
        lineup_request
    )

    print()
    print("=" * 80)
    print(
        "NINGUNA PETICIÓN DE ESCRITURA "
        "HA SIDO ENVIADA."
    )
    print("=" * 80)


if __name__ == "__main__":
    main()