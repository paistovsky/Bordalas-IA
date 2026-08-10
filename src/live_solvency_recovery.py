import argparse
import sys

from src.analysis.liquidity_manager import (
    build_liquidity_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)


def money(
    value: int | float,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def refresh_snapshot() -> tuple[
    str,
    dict,
]:

    print()
    print(
        "Actualizando Biwenger..."
    )

    print()

    collect_league_snapshot()

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    return (
        snapshot_file,
        snapshot,
    )


def select_next_recovery_offer(
    liquidity_state: dict,
) -> dict | None:
    """
    Selecciona SOLO la primera oferta de la
    combinación óptima calculada por Liquidity Manager.

    Nunca ejecutamos varias ventas sobre el mismo
    snapshot.
    """

    recovery = (
        liquidity_state[
            "recovery"
        ]
    )

    if not recovery[
        "needed"
    ]:

        return None

    if not recovery[
        "possible"
    ]:

        return None

    selected = (
        recovery.get(
            "selected",
            []
        )
    )

    if not selected:

        return None

    return selected[
        0
    ]


def main() -> None:

    parser = (
        argparse.ArgumentParser(
            description=(
                "Bordalás IA - "
                "Solvency Recovery"
            )
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
    )

    parser.add_argument(
        "--no-refresh",
        action="store_true",
    )

    args = (
        parser.parse_args()
    )

    # ========================================================
    # SNAPSHOT
    # ========================================================

    if args.no_refresh:

        snapshot_file = (
            get_latest_snapshot()
        )

        snapshot = (
            load_snapshot(
                snapshot_file
            )
        )

    else:

        (
            snapshot_file,
            snapshot,
        ) = refresh_snapshot()

    state = (
        build_liquidity_state(
            snapshot
        )
    )

    recovery = (
        state[
            "recovery"
        ]
    )

    print()
    print("=" * 100)
    print(
        "                  BORDALÁS IA - SOLVENCY RECOVERY"
    )
    print("=" * 100)

    print()

    print(
        f"Snapshot:             "
        f"{snapshot_file}"
    )

    print(
        f"Saldo actual:         "
        f"{money(state['balance'])}"
    )

    # ========================================================
    # NO HAY DEUDA
    # ========================================================

    if not recovery[
        "needed"
    ]:

        print()
        print(
            "Estado: SOLVENTE"
        )

        print(
            "No es necesaria ninguna venta."
        )

        print()
        print("=" * 100)

        return

    print(
        f"Déficit:              "
        f"{money(recovery['deficit'])}"
    )

    print(
        f"Ofertas disponibles:  "
        f"{state['incoming_offer_count']}"
    )

    print(
        f"Plan financiable:     "
        f"{'SÍ' if recovery['possible'] else 'NO'}"
    )

    # ========================================================
    # NO HAY SUFICIENTES OFERTAS
    # ========================================================

    if not recovery[
        "possible"
    ]:

        print()
        print(
            "Estado: WAIT_FOR_LIQUIDITY"
        )

        print()
        print(
            "Todavía no existen ofertas suficientes "
            "para cubrir el déficit."
        )

        print(
            "No se aceptará ninguna venta parcial "
            "automáticamente."
        )

        print()
        print("=" * 100)

        return

    # ========================================================
    # PLAN
    # ========================================================

    print()
    print(
        f"Ingreso plan:         "
        f"{money(recovery['recovered'])}"
    )

    print(
        f"Exceso previsto:      "
        f"{money(recovery['excess'])}"
    )

    print()

    print(
        "PLAN COMPLETO:"
    )

    for offer in recovery[
        "selected"
    ]:

        print(
            f"   - "
            f"{offer['player_name']:<22}"
            f"{money(offer['amount']):>14}"
            f"   "
            f"{offer['protection']}"
        )

    # ========================================================
    # SOLO UNA OPERACIÓN
    # ========================================================

    next_offer = (
        select_next_recovery_offer(
            state
        )
    )

    if next_offer is None:

        print()
        print(
            "No existe una oferta ejecutable."
        )

        return

    print()
    print("-" * 100)

    print(
        "SIGUIENTE OPERACIÓN"
    )

    print("-" * 100)

    print()

    print(
        f"Jugador:             "
        f"{next_offer['player_name']}"
    )

    print(
        f"Player ID:           "
        f"{next_offer['player_id']}"
    )

    print(
        f"Offer ID:            "
        f"{next_offer['offer_id']}"
    )

    print(
        f"Importe:             "
        f"{money(next_offer['amount'])}"
    )

    print(
        f"Protección:          "
        f"{next_offer['protection']}"
    )

    print(
        f"Daño estimado:       "
        f"{next_offer['sell_damage']:.2f}"
    )

    # ========================================================
    # PROTECCIÓN ABSOLUTA
    # ========================================================

    if next_offer[
        "protection"
    ] == "NEVER_AUTO_SELL":

        print()
        print(
            "OPERACIÓN BLOQUEADA."
        )

        print(
            "El jugador está marcado "
            "NEVER_AUTO_SELL."
        )

        sys.exit(
            1
        )

    # ========================================================
    # DRY RUN
    # ========================================================

    if not args.live:

        print()
        print(
            "MODO DRY-RUN"
        )

        print(
            "No se aceptará ninguna oferta."
        )

        print()
        print("=" * 100)

        return

    # ========================================================
    # LIVE
    # ========================================================

    print()
    print(
        "*** MODO LIVE ***"
    )

    print()

    print(
        "Se aceptará exactamente UNA oferta."
    )

    print(
        "Después será obligatorio refrescar "
        "y recalcular."
    )

    writer = (
        BiwengerWriteClient()
    )

    result = (
        writer.accept_offer(
            offer_id=
                int(
                    next_offer[
                        "offer_id"
                    ]
                ),

            execute=
                True,
        )
    )

    print()
    print(
        f"HTTP:                "
        f"{result.get('http_status')}"
    )

    print(
        f"Éxito:               "
        f"{'SÍ' if result.get('success') else 'NO'}"
    )

    if not result.get(
        "success"
    ):

        print()
        print(
            "La operación no se confirmó."
        )

        print()
        print("=" * 100)

        sys.exit(
            1
        )

    # ========================================================
    # REFRESH OBLIGATORIO
    # ========================================================

    print()
    print(
        "Venta aceptada."
    )

    print(
        "Refrescando estado real..."
    )

    (
        new_snapshot_file,
        new_snapshot,
    ) = refresh_snapshot()

    new_state = (
        build_liquidity_state(
            new_snapshot
        )
    )

    new_recovery = (
        new_state[
            "recovery"
        ]
    )

    print()
    print("-" * 100)

    print(
        "ESTADO POST-OPERACIÓN"
    )

    print("-" * 100)

    print()

    print(
        f"Snapshot:            "
        f"{new_snapshot_file}"
    )

    print(
        f"Saldo nuevo:         "
        f"{money(new_state['balance'])}"
    )

    if new_recovery[
        "needed"
    ]:

        print(
            f"Déficit restante:    "
            f"{money(new_recovery['deficit'])}"
        )

        print(
            f"Plan financiable:    "
            f"{'SÍ' if new_recovery['possible'] else 'NO'}"
        )

        print()
        print(
            "No se ejecutarán más ventas "
            "en esta ejecución."
        )

        print(
            "Vuelve a lanzar el comando para "
            "recalcular la siguiente operación."
        )

    else:

        print()
        print(
            "SOLVENCIA RECUPERADA."
        )

        print(
            "Saldo >= 0."
        )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()