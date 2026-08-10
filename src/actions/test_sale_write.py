import json

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


PLAYER_ID = 25322
PRICE = 210000


def main() -> None:

    writer = BiwengerWriteClient()

    request = (
        writer.list_player_for_sale(
            player_id=PLAYER_ID,
            price=PRICE,
            execute=False,
        )
    )

    print()
    print("=" * 80)
    print(
        "        BORDALÁS IA - SALE WRITE TEST"
    )
    print("=" * 80)

    print()
    print(
        f"Player ID: {PLAYER_ID}"
    )

    print(
        f"Precio:    {PRICE:,} €"
    )

    print()
    print(
        f"Método:    "
        f"{request['method']}"
    )

    print(
        f"URL:       "
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

    print(
        "No se ha modificado Biwenger."
    )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()