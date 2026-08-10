import argparse
import sys
import time

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


# ============================================================
# CONFIGURACIÓN
# ============================================================


REQUEST_DELAY_SECONDS = 0.30


# ============================================================
# UTILIDADES
# ============================================================


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


# ============================================================
# PRESENTACIÓN
# ============================================================


def print_plan(
    state: dict,
) -> None:

    print()
    print("=" * 100)
    print(
        "                  BORDALÁS IA - LIQUIDITY MAINTENANCE"
    )
    print("=" * 100)

    print()

    print(
        f"Saldo:                "
        f"{money(state['balance'])}"
    )

    print(
        f"Plantilla:            "
        f"{len(state['roster'])}"
    )

    print(
        f"Ya publicados:        "
        f"{state['listing_count']}"
    )

    print(
        f"Pendientes:           "
        f"{state['to_list_count']}"
    )

    print(
        f"Ofertas recibidas:    "
        f"{state['incoming_offer_count']}"
    )

    print()

    print("-" * 100)
    print(
        "JUGADORES A PUBLICAR"
    )
    print("-" * 100)

    if not state[
        "to_list"
    ]:

        print()
        print(
            "Toda la plantilla ya está publicada."
        )

        return

    for player in state[
        "to_list"
    ]:

        print()

        print(
            f"{player['name']:<24}"
            f"{money(player['listing_price']):>15}"
            f"   {player['protection']}"
        )

        if player[
            "protection"
        ] == "NEVER_AUTO_SELL":

            print(
                "   PROTEGIDO: se publica únicamente "
                "para generar liquidez/ofertas."
            )


# ============================================================
# EJECUCIÓN
# ============================================================


def execute_listing_plan(
    state: dict,
    execute: bool,
) -> dict:

    pending = (
        state[
            "to_list"
        ]
    )

    if not pending:

        return {
            "attempted":
                0,

            "success":
                0,

            "failed":
                0,

            "results":
                [],
        }

    # ========================================================
    # DRY RUN
    # ========================================================

    if not execute:

        return {
            "attempted":
                len(
                    pending
                ),

            "success":
                0,

            "failed":
                0,

            "results": [
                {
                    "player_id":
                        player[
                            "id"
                        ],

                    "name":
                        player[
                            "name"
                        ],

                    "price":
                        player[
                            "listing_price"
                        ],

                    "status":
                        "DRY_RUN",
                }

                for player in pending
            ],
        }

    # ========================================================
    # LIVE
    # ========================================================

    writer = (
        BiwengerWriteClient()
    )

    results = []

    success_count = 0
    failed_count = 0

    for index, player in enumerate(
        pending,
        start=1,
    ):

        player_id = int(
            player[
                "id"
            ]
        )

        price = int(
            player[
                "listing_price"
            ]
        )

        print()
        print(
            f"[{index}/{len(pending)}] "
            f"Publicando {player['name']} "
            f"por {money(price)}..."
        )

        try:

            result = (
                writer.list_player_for_sale(
                    player_id=
                        player_id,

                    price=
                        price,

                    execute=
                        True,
                )
            )

            success = bool(
                result.get(
                    "success",
                    False,
                )
            )

            if success:

                success_count += 1

                print(
                    f"   OK - HTTP "
                    f"{result.get('http_status')}"
                )

                status = (
                    "LISTED"
                )

            else:

                failed_count += 1

                print(
                    f"   ERROR - HTTP "
                    f"{result.get('http_status')}"
                )

                status = (
                    "FAILED"
                )

            results.append(
                {
                    "player_id":
                        player_id,

                    "name":
                        player[
                            "name"
                        ],

                    "price":
                        price,

                    "status":
                        status,

                    "response":
                        result,
                }
            )

        except Exception as error:

            failed_count += 1

            print(
                f"   ERROR: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            results.append(
                {
                    "player_id":
                        player_id,

                    "name":
                        player[
                            "name"
                        ],

                    "price":
                        price,

                    "status":
                        "ERROR",

                    "error":
                        (
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                }
            )

        # Pequeña separación para no lanzar todas
        # las peticiones simultáneamente.
        time.sleep(
            REQUEST_DELAY_SECONDS
        )

    return {
        "attempted":
            len(
                pending
            ),

        "success":
            success_count,

        "failed":
            failed_count,

        "results":
            results,
    }


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    parser = (
        argparse.ArgumentParser(
            description=(
                "Bordalás IA - "
                "Liquidity Maintenance"
            )
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Publica realmente los jugadores "
            "pendientes."
        ),
    )

    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help=(
            "Utiliza el último snapshot "
            "sin refrescar Biwenger."
        ),
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

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()
    print(
        "Calculando estado de liquidez..."
    )

    state = (
        build_liquidity_state(
            snapshot
        )
    )

    print_plan(
        state
    )

    # ========================================================
    # MODE
    # ========================================================

    print()

    if args.live:

        print(
            "*** MODO LIVE ***"
        )

        print(
            "Los jugadores pendientes serán "
            "publicados realmente en Biwenger."
        )

        print()

        print(
            "IMPORTANTE:"
        )

        print(
            "Publicar NO significa aceptar "
            "ninguna oferta."
        )

    else:

        print(
            "MODO DRY-RUN"
        )

        print(
            "No se modificará Biwenger."
        )

    # ========================================================
    # EXECUTE
    # ========================================================

    execution = (
        execute_listing_plan(
            state=
                state,

            execute=
                args.live,
        )
    )

    print()
    print("=" * 100)
    print(
        "RESULTADO"
    )
    print("=" * 100)

    print()

    print(
        f"Intentados:  "
        f"{execution['attempted']}"
    )

    print(
        f"Correctos:   "
        f"{execution['success']}"
    )

    print(
        f"Fallidos:    "
        f"{execution['failed']}"
    )

    # ========================================================
    # REFRESH POST-LIVE
    # ========================================================

    if args.live:

        print()
        print(
            "Verificando estado real..."
        )

        try:

            (
                new_snapshot_file,
                new_snapshot,
            ) = refresh_snapshot()

            new_state = (
                build_liquidity_state(
                    new_snapshot
                )
            )

            print()
            print(
                f"Snapshot nuevo:        "
                f"{new_snapshot_file}"
            )

            print(
                f"Publicados ahora:      "
                f"{new_state['listing_count']}"
            )

            print(
                f"Pendientes ahora:      "
                f"{new_state['to_list_count']}"
            )

            print(
                f"Ofertas recibidas:     "
                f"{new_state['incoming_offer_count']}"
            )

            recovery = (
                new_state[
                    "recovery"
                ]
            )

            if recovery[
                "needed"
            ]:

                print(
                    f"Déficit:               "
                    f"{money(recovery['deficit'])}"
                )

                print(
                    f"Recuperación posible:  "
                    f"{'SÍ' if recovery['possible'] else 'NO'}"
                )

        except Exception as error:

            print()
            print(
                "No se pudo verificar el estado "
                "posterior."
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()