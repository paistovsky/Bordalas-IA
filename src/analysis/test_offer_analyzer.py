from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)


def money(
    value: int,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def print_offer(
    offer: dict,
) -> None:

    names = [
        player[
            "name"
        ]

        for player
        in offer[
            "players"
        ]
    ]

    player_text = (
        ", ".join(
            names
        )
        if names
        else "DESCONOCIDO"
    )

    counterparty = (
        offer[
            "counterparty"
        ]
    )

    print()
    print(
        f"Offer ID:      "
        f"{offer['offer_id']}"
    )

    print(
        f"Jugador:       "
        f"{player_text}"
    )

    print(
        f"Dirección:     "
        f"{offer['direction']}"
    )

    print(
        f"Contraparte:   "
        f"{counterparty['type']} "
        f"- {counterparty['name']}"
    )

    print(
        f"Importe:       "
        f"{money(offer['amount'])}"
    )

    print(
        f"Valor mercado: "
        f"{money(offer['market_value'])}"
    )

    print(
        f"Diferencia:    "
        f"{money(offer['premium_amount'])} "
        f"({offer['premium_percent']:+.1f}%)"
    )

    print(
        f"Estado:        "
        f"{offer['status']}"
    )

    print(
        f"Decisión:      "
        f"{offer['decision']['decision']}"
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    board = (
        build_offer_board(
            snapshot
        )
    )

    print()
    print("=" * 90)
    print(
        "               BORDALÁS IA - OFFER ANALYZER"
    )
    print("=" * 90)

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    print()
    print(
        f"Mi user ID:          "
        f"{board['my_user_id']}"
    )

    liquidity = (
        board[
            "liquidity"
        ]
    )

    print(
        f"Saldo actual:        "
        f"{money(liquidity['balance'])}"
    )

    print(
        f"Presión liquidez:    "
        f"{liquidity['level']}"
    )

    print()
    print(
        f"Ofertas salientes:   "
        f"{board['outgoing_count']}"
    )

    print(
        f"Ofertas recibidas:   "
        f"{board['incoming_count']}"
    )

    print(
        f"Ofertas desconocidas:"
        f" {board['unknown_count']}"
    )

    print()
    print("=" * 90)
    print(
        "PUJAS SALIENTES"
    )
    print("=" * 90)

    if not board[
        "outgoing"
    ]:

        print()
        print(
            "Ninguna."
        )

    for offer in board[
        "outgoing"
    ]:

        print_offer(
            offer
        )

    print()
    print("=" * 90)
    print(
        "OFERTAS RECIBIDAS"
    )
    print("=" * 90)

    if not board[
        "incoming"
    ]:

        print()
        print(
            "Ninguna oferta recibida detectada."
        )

    for offer in board[
        "incoming"
    ]:

        print_offer(
            offer
        )

    if board[
        "unknown"
    ]:

        print()
        print("=" * 90)
        print(
            "OFERTAS SIN CLASIFICAR"
        )
        print("=" * 90)

        for offer in board[
            "unknown"
        ]:

            print_offer(
                offer
            )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()