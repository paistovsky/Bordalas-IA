import argparse
import sys

from src.actions.live_bid_executor import (
    execute_bid,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.actions.action_plan import (
    build_action_plan,
)


def find_recommended_bid(
    player_id: int,
) -> dict | None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    plan = build_action_plan(
        snapshot
    )

    for bid in plan["bids"]:

        if (
            bid["player_id"]
            == player_id
        ):
            return bid

    return None


def find_current_seller(
    player_id: int,
) -> int | None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    for sale in snapshot[
        "market"
    ].get(
        "sales",
        [],
    ):

        if (
            sale.get(
                "player",
                {},
            ).get("id")
            != player_id
        ):
            continue

        user = sale.get("user")

        if user is None:
            return None

        return user.get("id")

    raise RuntimeError(
        "Jugador no encontrado "
        "en el snapshot."
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Bordalás IA - "
            "Ejecutor de una única puja"
        )
    )

    parser.add_argument(
        "--player-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--amount",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Envía realmente la puja "
            "a Biwenger."
        ),
    )

    args = parser.parse_args()

    print()
    print("=" * 80)
    print(
        "            BORDALÁS IA - SINGLE BID"
    )
    print("=" * 80)

    # ==================================================
    # VALIDAR CONTRA RECOMENDACIÓN
    # ==================================================

    recommendation = (
        find_recommended_bid(
            args.player_id
        )
    )

    if recommendation is None:

        print()
        print(
            "BLOQUEADO:"
        )

        print(
            "El jugador no forma parte "
            "del plan de compras actual."
        )

        sys.exit(1)

    recommended_amount = (
        recommendation["amount"]
    )

    if (
        args.amount
        > recommended_amount
    ):

        print()
        print(
            "BLOQUEADO:"
        )

        print(
            "El importe supera la puja "
            "recomendada por Bordalás IA."
        )

        print(
            f"Máximo recomendado: "
            f"{recommended_amount:,} €"
        )

        sys.exit(1)

    expected_seller_id = (
        find_current_seller(
            args.player_id
        )
    )

    print()
    print(
        f"Jugador:    "
        f"{recommendation['player_name']}"
    )

    print(
        f"Player ID:  "
        f"{args.player_id}"
    )

    print(
        f"Puja:       "
        f"{args.amount:,} €"
    )

    print(
        f"Score:      "
        f"{recommendation['score']}/100"
    )

    print()

    if args.live:
        print(
            "*** MODO LIVE ***"
        )

        print(
            "La puja será enviada "
            "a Biwenger."
        )

    else:
        print(
            "MODO DRY-RUN"
        )

        print(
            "No se enviará ninguna puja."
        )

    print()

    try:

        result = execute_bid(
            player_id=args.player_id,
            amount=args.amount,
            expected_seller_id=
                expected_seller_id,
            execute=args.live,
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

    print(
        f"Origen:     "
        f"{result['seller']}"
    )

    print(
        f"Precio:     "
        f"{result['current_price']:,} €"
    )

    print(
        f"Saldo:      "
        f"{result['balance']:,} €"
    )

    print(
        f"Puja máxima:"
        f" "
        f"{result['maximum_bid']:,} €"
    )

    if not args.live:

        print()
        print(
            "DRY-RUN CORRECTO."
        )

        print(
            "No se ha modificado Biwenger."
        )

        return

    print()
    print(
        f"HTTP:       "
        f"{result.get('http_status')}"
    )

    print(
        f"Éxito API:  "
        f"{'SÍ' if result['success'] else 'NO'}"
    )

    print(
        f"Oferta detectada después: "
        f"{'SÍ' if result.get('offer_detected_after') else 'NO'}"
    )

    print()

    if (
        result["success"]
        and
        result.get(
            "offer_detected_after"
        )
    ):

        print(
            "✅ PUJA CONFIRMADA"
        )

    else:

        print(
            "⚠ La operación requiere revisión."
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()