import argparse

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


def money(
    value: int,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def extract_player_id(
    offer: dict,
) -> int | None:

    requested = (
        offer.get(
            "requestedPlayers"
        )
    )

    if requested:

        first = requested[0]

        if isinstance(
            first,
            int,
        ):
            return first

        if isinstance(
            first,
            dict,
        ):
            return first.get(
                "id"
            )

    player = (
        offer.get(
            "player"
        )
    )

    if isinstance(
        player,
        int,
    ):
        return player

    if isinstance(
        player,
        dict,
    ):
        return player.get(
            "id"
        )

    return None


def find_offer_for_player(
    market: dict,
    player_id: int,
) -> dict | None:

    offers = (
        market.get(
            "offers",
            []
        )
    )

    for offer in offers:

        offer_player_id = (
            extract_player_id(
                offer
            )
        )

        if (
            offer_player_id
            == player_id
        ):
            return offer

    return None


def get_player_name(
    catalog: dict,
    player_id: int,
) -> str:

    player = (
        catalog.get(
            str(
                player_id
            )
        )
        or
        catalog.get(
            player_id
        )
    )

    if not player:

        return (
            f"Player {player_id}"
        )

    return (
        player.get(
            "name"
        )
        or
        f"Player {player_id}"
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Retira una puja activa "
            "de Biwenger."
        )
    )

    parser.add_argument(
        "--player-id",
        type=int,
        required=True,
        help=(
            "ID Biwenger del jugador."
        ),
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Ejecuta realmente la "
            "cancelación."
        ),
    )

    args = parser.parse_args()

    print()
    print("=" * 80)
    print(
        "          BORDALÁS IA - CANCEL BID"
    )
    print("=" * 80)

    writer = (
        BiwengerWriteClient()
    )

    # ==================================================
    # ESTADO ACTUAL
    # ==================================================

    market = (
        writer.client.get_market()
    )

    catalog = (
        writer.client.get_player_catalog()
    )

    player_name = (
        get_player_name(
            catalog,
            args.player_id,
        )
    )

    offer = (
        find_offer_for_player(
            market,
            args.player_id,
        )
    )

    print()
    print(
        f"Jugador:    "
        f"{player_name}"
    )

    print(
        f"Player ID:  "
        f"{args.player_id}"
    )

    # ==================================================
    # NO EXISTE PUJA
    # ==================================================

    if offer is None:

        print()
        print(
            "Estado: NO_ACTIVE_BID"
        )

        print()
        print(
            "No existe ninguna puja activa "
            "para este jugador."
        )

        print()
        print("=" * 80)

        return

    offer_id = int(
        offer[
            "id"
        ]
    )

    amount = int(
        offer.get(
            "amount",
            0,
        )
        or 0
    )

    print(
        f"Offer ID:   "
        f"{offer_id}"
    )

    print(
        f"Importe:    "
        f"{money(amount)}"
    )

    # ==================================================
    # CONSTRUIR PETICIÓN
    # ==================================================

    request = (
        writer.build_cancel_bid_request(
            offer_id=
                offer_id,
        )
    )

    print()
    print(
        f"Método:     "
        f"{request['method']}"
    )

    print(
        f"URL:        "
        f"{request['url']}"
    )

    # ==================================================
    # DRY RUN
    # ==================================================

    if not args.live:

        print()
        print(
            "MODO DRY-RUN"
        )

        print(
            "No se retirará ninguna puja."
        )

        print()
        print(
            "Estado: DRY_RUN_OK"
        )

        print()
        print("=" * 80)

        return

    # ==================================================
    # LIVE
    # ==================================================

    print()
    print(
        "*** MODO LIVE ***"
    )

    print(
        "La puja será retirada de Biwenger."
    )

    result = (
        writer.cancel_bid(
            offer_id=
                offer_id,

            execute=True,
        )
    )

    print()
    print(
        f"HTTP:       "
        f"{result.get('http_status')}"
    )

    print(
        f"Éxito API:  "
        f"{'SÍ' if result.get('success') else 'NO'}"
    )

    # ==================================================
    # VERIFICACIÓN
    # ==================================================

    if not result.get(
        "success"
    ):

        print()
        print(
            "Estado: FAILED"
        )

        print()
        print(
            "La API no confirmó correctamente "
            "la cancelación."
        )

        print()
        print("=" * 80)

        return

    refreshed_market = (
        writer.client.get_market()
    )

    remaining_offer = (
        find_offer_for_player(
            refreshed_market,
            args.player_id,
        )
    )

    removed = (
        remaining_offer
        is None
    )

    print(
        f"Puja detectada después: "
        f"{'NO' if removed else 'SÍ'}"
    )

    print()

    if removed:

        new_maximum_bid = (
            refreshed_market
            .get(
                "status",
                {}
            )
            .get(
                "maximumBid"
            )
        )

        print(
            "CANCELACIÓN CONFIRMADA"
        )

        if new_maximum_bid is not None:

            print()
            print(
                f"Nueva puja máxima: "
                f"{money(int(new_maximum_bid))}"
            )

    else:

        print(
            "ATENCIÓN: la API respondió "
            "correctamente, pero la oferta "
            "sigue apareciendo activa."
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()