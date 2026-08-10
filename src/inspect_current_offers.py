from pprint import pprint

from src.biwenger.client import BiwengerClient


def main() -> None:
    client = BiwengerClient()

    print()
    print("=" * 80)
    print("          BORDALÁS IA - OFERTAS ACTUALES")
    print("=" * 80)

    print()
    print("Iniciando sesión...")

    client.login()
    client.select_league()

    print("OK")

    print()
    print("Consultando mercado...")

    market = client.get_market()
    catalog = client.get_player_catalog()

    sales = market.get("sales", [])
    offers = market.get("offers", [])

    print()
    print(f"Jugadores en mercado: {len(sales)}")
    print(f"Ofertas/Pujas:        {len(offers)}")

    print()
    print("=" * 80)
    print("PUJAS ACTIVAS")
    print("=" * 80)

    if not offers:
        print()
        print("No aparecen ofertas activas.")
        print()
        print("Estructura completa de market['offers']:")
        pprint(offers)
        return

    for index, offer in enumerate(
        offers,
        start=1,
    ):
        print()
        print("-" * 80)
        print(f"OFERTA {index}")
        print("-" * 80)

        pprint(offer)

        # Intentamos localizar el jugador
        player_id = None

        player_data = offer.get("player")

        if isinstance(player_data, dict):
            player_id = player_data.get("id")

        elif isinstance(player_data, int):
            player_id = player_data

        if player_id is None:
            requested = offer.get(
                "requestedPlayers",
                [],
            )

            if requested:
                first = requested[0]

                if isinstance(first, dict):
                    player_id = first.get("id")

                elif isinstance(first, int):
                    player_id = first

        player = None

        if player_id is not None:
            player = catalog.get(
                str(player_id)
            )

        if player:
            print()
            print(
                f"Jugador detectado: "
                f"{player['name']}"
            )

            print(
                f"Player ID:         "
                f"{player_id}"
            )

        # Buscar quién vende ese jugador
        sale = next(
            (
                sale
                for sale in sales
                if (
                    sale.get("player", {})
                    .get("id")
                    == player_id
                )
            ),
            None,
        )

        if sale:
            seller = sale.get("user")

            print()

            if seller is None:
                print(
                    "Origen:            "
                    "🤖 MÁQUINA"
                )

                print(
                    "Vendedor ID:       None"
                )

            else:
                print(
                    "Origen:            "
                    "👤 MANAGER"
                )

                print(
                    f"Manager:           "
                    f"{seller.get('name')}"
                )

                print(
                    f"Vendedor ID:       "
                    f"{seller.get('id')}"
                )

            print(
                f"Precio de salida:  "
                f"{sale.get('price', 0):,} €"
            )


if __name__ == "__main__":
    main()