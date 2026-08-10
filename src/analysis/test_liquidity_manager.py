from src.analysis.liquidity_manager import (
    build_liquidity_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def money(
    value,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    state = (
        build_liquidity_state(
            snapshot
        )
    )

    print()
    print("=" * 105)
    print(
        "                      BORDALÁS IA - LIQUIDITY MANAGER"
    )
    print("=" * 105)

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()

    print(
        f"Saldo actual:          "
        f"{money(state['balance'])}"
    )

    print(
        f"Plantilla:             "
        f"{len(state['roster'])}"
    )

    print(
        f"Ya publicados:         "
        f"{state['listing_count']}"
    )

    print(
        f"Pendientes de publicar:"
        f" {state['to_list_count']}"
    )

    print(
        f"Ofertas recibidas:     "
        f"{state['incoming_offer_count']}"
    )

    # ========================================================
    # PLANTILLA
    # ========================================================

    print()
    print("=" * 105)
    print(
        "ESTADO DE LIQUIDEZ DE PLANTILLA"
    )
    print("=" * 105)

    for player in state[
        "roster"
    ]:

        print()

        print(
            f"{player['name']:<24}"
            f"{money(player['market_value']):>15}"
        )

        print(
            f"   Sale score:       "
            f"{player['sale_score']:.0f}/100"
        )

        print(
            f"   Protección:       "
            f"{player['protection']}"
        )

        print(
            f"   Protection score: "
            f"{player['protection_score']:.2f}"
        )

        print(
            f"   En XI:            "
            f"{'SÍ' if player['in_lineup'] else 'NO'}"
        )

        print(
            f"   Franchise:        "
            f"{player['franchise_score']:.0f}/100"
        )

        print(
            f"   Publicado:        "
            f"{'SÍ' if player['currently_listed'] else 'NO'}"
        )

        if (
            player[
                "currently_listed"
            ]
            and
            player[
                "current_listing"
            ]
        ):

            print(
                f"   Precio actual:    "
                f"{money(player['current_listing']['price'])}"
            )

        print(
            f"   Precio propuesto: "
            f"{money(player['listing_price'])}"
        )

        print(
            f"   Estrategia:       "
            f"{player['listing_strategy']}"
        )

        print(
            f"   Acción:           "
            f"{player['listing_action']}"
        )

    # ========================================================
    # PUBLICAR
    # ========================================================

    print()
    print("=" * 105)
    print(
        "PUBLICACIONES NECESARIAS"
    )
    print("=" * 105)

    if not state[
        "to_list"
    ]:

        print()
        print(
            "Toda la plantilla ya dispone de "
            "publicación activa."
        )

    for player in state[
        "to_list"
    ]:

        print()

        print(
            f"- {player['name']:<24}"
            f"{money(player['listing_price']):>15}   "
            f"{player['protection']}"
        )

    # ========================================================
    # OFERTAS
    # ========================================================

    print()
    print("=" * 105)
    print(
        "OFERTAS DE LIQUIDEZ DISPONIBLES"
    )
    print("=" * 105)

    if not state[
        "incoming_offers"
    ]:

        print()
        print(
            "No hay ofertas recibidas utilizables todavía."
        )

    for offer in state[
        "incoming_offers"
    ]:

        print()

        print(
            f"{offer['player_name']:<24}"
            f"{money(offer['amount']):>15}"
        )

        print(
            f"   Valor mercado: "
            f"{money(offer['market_value'])}"
        )

        print(
            f"   Diferencia:    "
            f"{money(offer['delta'])} "
            f"({offer['delta_percent']:+.2f}%)"
        )

        print(
            f"   Sale score:    "
            f"{offer['sale_score']:.0f}"
        )

        print(
            f"   Protección:    "
            f"{offer['protection']}"
        )

        print(
            f"   Daño venta:    "
            f"{offer['sell_damage']:.2f}"
        )

    # ========================================================
    # RECOVERY
    # ========================================================

    recovery = (
        state[
            "recovery"
        ]
    )

    print()
    print("=" * 105)
    print(
        "PLAN DE RECUPERACIÓN DE SOLVENCIA"
    )
    print("=" * 105)

    print()

    if not recovery[
        "needed"
    ]:

        print(
            "No es necesario recuperar solvencia."
        )

    else:

        print(
            f"Déficit actual:        "
            f"{money(recovery['deficit'])}"
        )

        print(
            f"Plan financiable:      "
            f"{'SÍ' if recovery['possible'] else 'NO'}"
        )

        if recovery[
            "possible"
        ]:

            print(
                f"Ingreso seleccionado:  "
                f"{money(recovery['recovered'])}"
            )

            print(
                f"Exceso:                "
                f"{money(recovery['excess'])}"
            )

            print()

            print(
                "OFERTAS A UTILIZAR:"
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

        else:

            print(
                f"Liquidez de ofertas:   "
                f"{money(recovery.get('potential', 0))}"
            )

            print()

            print(
                "Todavía necesitamos generar o recibir "
                "más ofertas antes de poder sanear."
            )

    print()
    print("=" * 105)

    print()
    print(
        "MODO: ANÁLISIS"
    )

    print(
        "No se ha modificado Biwenger."
    )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()