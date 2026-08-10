from typing import Any

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


def find_my_player(
    team: list[dict],
    player_id: int,
) -> dict | None:

    for player in team:
        if player.get("id") == player_id:
            return player

    return None


def find_existing_sale(
    market: dict,
    player_id: int,
    my_user_id: int,
) -> dict | None:

    for sale in market.get(
        "sales",
        [],
    ):
        sale_player_id = (
            sale
            .get("player", {})
            .get("id")
        )

        if sale_player_id != player_id:
            continue

        seller = sale.get("user")

        if seller is None:
            continue

        if seller.get("id") == my_user_id:
            return sale

    return None


def execute_sale_listing(
    player_id: int,
    price: int,
    execute: bool = False,
) -> dict[str, Any]:

    writer = BiwengerWriteClient()

    # ==================================================
    # DATOS FRESCOS
    # ==================================================

    team = writer.client.get_my_team()
    market = writer.client.get_market()

    player = find_my_player(
        team,
        player_id,
    )

    if player is None:
        raise RuntimeError(
            "El jugador ya no pertenece "
            "a tu plantilla."
        )

    market_value = int(
        player.get("price", 0)
        or 0
    )

    # ==================================================
    # VALIDAR PRECIO
    # ==================================================

    if price < market_value:
        raise RuntimeError(
            "No se permite publicar por debajo "
            "del valor actual de Biwenger."
        )

    # ==================================================
    # ¿YA ESTÁ EN MERCADO?
    # ==================================================

    existing = find_existing_sale(
        market,
        player_id,
        writer.user_id,
    )

    if existing is not None:
        return {
            "player_id":
                player_id,

            "player_name":
                player.get("name"),

            "market_value":
                market_value,

            "price":
                price,

            "status":
                "ALREADY_LISTED",

            "sent":
                False,

            "success":
                True,
        }

    # ==================================================
    # DRY-RUN
    # ==================================================

    preview = (
        writer.list_player_for_sale(
            player_id=player_id,
            price=price,
            execute=False,
        )
    )

    result = {
        "player_id":
            player_id,

        "player_name":
            player.get("name"),

        "market_value":
            market_value,

        "price":
            price,

        "preview":
            preview,

        "status":
            "DRY_RUN_OK",

        "sent":
            False,

        "success":
            False,
    }

    if not execute:
        return result

    # ==================================================
    # LIVE
    # ==================================================

    response = (
        writer.list_player_for_sale(
            player_id=player_id,
            price=price,
            execute=True,
        )
    )

    result["sent"] = True

    result["http_status"] = (
        response.get("http_status")
    )

    result["api_response"] = (
        response.get("response")
    )

    result["success"] = (
        response.get(
            "success",
            False,
        )
    )

    result["status"] = (
        "EXECUTED"
        if result["success"]
        else "FAILED"
    )

    # ==================================================
    # VERIFICACIÓN POSTERIOR
    # ==================================================

    refreshed_market = (
        writer.client.get_market()
    )

    result["listing_detected_after"] = (
        find_existing_sale(
            refreshed_market,
            player_id,
            writer.user_id,
        )
        is not None
    )

    return result