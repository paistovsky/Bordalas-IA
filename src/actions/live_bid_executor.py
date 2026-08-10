from typing import Any

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


def get_sale_for_player(
    market: dict,
    player_id: int,
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

        if sale_player_id == player_id:
            return sale

    return None


def get_seller_id(
    sale: dict,
) -> int | None:

    seller = sale.get("user")

    if seller is None:
        return None

    return seller.get("id")


def get_seller_description(
    sale: dict,
) -> str:

    seller = sale.get("user")

    if seller is None:
        return "MÁQUINA"

    return (
        f"MANAGER: "
        f"{seller.get('name')}"
    )


def find_existing_offer(
    market: dict,
    player_id: int,
) -> dict | None:

    """
    Intenta detectar si ya tenemos una oferta
    activa por el jugador.

    La estructura de offers puede variar, por lo
    que comprobamos varios formatos posibles.
    """

    for offer in market.get(
        "offers",
        [],
    ):

        # Formato player: {id: ...}
        player = offer.get("player")

        if isinstance(
            player,
            dict,
        ):
            if (
                player.get("id")
                == player_id
            ):
                return offer

        # Formato player: 123
        if isinstance(
            player,
            int,
        ):
            if player == player_id:
                return offer

        # Formato requestedPlayers
        requested = offer.get(
            "requestedPlayers",
            [],
        )

        for requested_player in requested:

            if isinstance(
                requested_player,
                int,
            ):
                if (
                    requested_player
                    == player_id
                ):
                    return offer

            elif isinstance(
                requested_player,
                dict,
            ):
                if (
                    requested_player.get(
                        "id"
                    )
                    == player_id
                ):
                    return offer

    return None


def execute_bid(
    player_id: int,
    amount: int,
    expected_seller_id: int | None = None,
    execute: bool = False,
) -> dict[str, Any]:

    writer = BiwengerWriteClient()

    # ==================================================
    # PREFLIGHT: MERCADO FRESCO
    # ==================================================

    market = writer.client.get_market()

    balance = (
        market
        .get("status", {})
        .get("balance", 0)
    )

    maximum_bid = (
        market
        .get("status", {})
        .get("maximumBid", 0)
    )

    sale = get_sale_for_player(
        market,
        player_id,
    )

    if sale is None:
        raise RuntimeError(
            "El jugador ya no está "
            "en el mercado."
        )

    current_price = (
        sale.get("price", 0)
    )

    current_seller_id = (
        get_seller_id(
            sale
        )
    )

    seller_description = (
        get_seller_description(
            sale
        )
    )

    # ==================================================
    # VALIDAR VENDEDOR
    # ==================================================

    if (
        expected_seller_id
        != current_seller_id
    ):
        raise RuntimeError(
            "El vendedor ha cambiado. "
            f"Esperado: {expected_seller_id}, "
            f"actual: {current_seller_id}."
        )

    # ==================================================
    # VALIDAR IMPORTE
    # ==================================================

    if amount <= 0:
        raise RuntimeError(
            "La puja debe ser mayor que 0."
        )

    if amount > maximum_bid:
        raise RuntimeError(
            "La puja supera la puja máxima "
            f"actual ({maximum_bid:,} €)."
        )

    # No permitimos cantidades absurdamente inferiores
    # al precio de salida.
    if amount < current_price:
        raise RuntimeError(
            "La puja es inferior al precio "
            f"actual de mercado ({current_price:,} €)."
        )

    # ==================================================
    # DETECTAR PUJA EXISTENTE
    # ==================================================

    existing_offer = (
        find_existing_offer(
            market,
            player_id,
        )
    )

    if existing_offer is not None:
        raise RuntimeError(
            "Ya existe una oferta activa "
            "por este jugador."
        )

    # ==================================================
    # PREVIEW
    # ==================================================

    preview = writer.place_bid(
        player_id=player_id,
        amount=amount,
        seller_user_id=
            current_seller_id,
        execute=False,
    )

    result = {
        "player_id":
            player_id,

        "amount":
            amount,

        "current_price":
            current_price,

        "balance":
            balance,

        "maximum_bid":
            maximum_bid,

        "seller_id":
            current_seller_id,

        "seller":
            seller_description,

        "preview":
            preview,

        "sent":
            False,

        "success":
            False,
    }

    if not execute:
        return result

    # ==================================================
    # EJECUCIÓN REAL
    # ==================================================

    response = writer.place_bid(
        player_id=player_id,
        amount=amount,
        seller_user_id=
            current_seller_id,
        execute=True,
    )

    result["sent"] = True

    result["http_status"] = (
        response.get(
            "http_status"
        )
    )

    result["api_response"] = (
        response.get(
            "response"
        )
    )

    result["success"] = (
        response.get(
            "success",
            False,
        )
    )

    # ==================================================
    # VERIFICACIÓN POSTERIOR
    # ==================================================

    refreshed_market = (
        writer.client.get_market()
    )

    result["offer_detected_after"] = (
        find_existing_offer(
            refreshed_market,
            player_id,
        )
        is not None
    )

    return result