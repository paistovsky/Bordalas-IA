from src.analysis.computer_offer_reroll_engine import (
    build_computer_offer_reroll_board,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def money(
    value,
) -> str:

    return (
        f"{int(value or 0):,.0f} EUR"
    )


def dt(
    value,
) -> str:

    if value is None:
        return "NINGUNO"

    try:

        return value.strftime(
            "%d/%m/%Y %H:%M"
        )

    except AttributeError:

        return str(
            value
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

    board = (
        build_computer_offer_reroll_board(
            snapshot=
                snapshot,

            # Primera prueba: no escribimos historial.
            persist_history=
                False,
        )
    )

    solvency = (
        board[
            "solvency"
        ]
    )

    guarantee = (
        solvency[
            "solvency_guarantee"
        ]
    )

    cycles = (
        solvency[
            "computer_cycles"
        ]
    )

    print()
    print("=" * 118)
    print(
        "                    BORDALAS IA - COMPUTER OFFER REROLL ENGINE V1"
    )
    print("=" * 118)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print(
        f"Saldo:                       "
        f"{money(solvency['balance'])}"
    )

    print(
        f"Garantia T-15:               "
        f"{'SI' if guarantee.get('guaranteed') else 'NO'}"
    )

    print(
        f"Margen garantia:             "
        f"{money(guarantee.get('guarantee_surplus'))}"
    )

    print(
        f"Ciclos Computer seguros:     "
        f"{cycles.get('safe_cycles_remaining')}"
    )

    print(
        f"Ciclos para nueva lista:     "
        f"{cycles.get('new_listing_cycles_remaining')}"
    )

    print(
        f"Ultimo dia lista:            "
        f"{cycles.get('last_safe_listing_day')}"
    )

    print()
    print(
        f"Ofertas Computer:            "
        f"{board['offer_count']}"
    )

    print(
        f"SOLVENCY_RESERVED:           "
        f"{len(board['solvency_reserved'])}"
    )

    print(
        f"Reroll candidatos:           "
        f"{len(board['reroll_candidates'])}"
    )

    print(
        f"Aceptar antes de caducar:    "
        f"{len(board['accept_before_expiry'])}"
    )

    print()

    for offer in board[
        "offers"
    ]:

        player_names = ", ".join(
            player.get(
                "name",
                "?"
            )

            for player
            in offer.get(
                "players",
                [],
            )
        )

        simulation = (
            offer[
                "simulation"
            ]
        )

        replacement = (
            simulation[
                "replacement"
            ]
        )

        print("-" * 118)

        print(
            f"JUGADOR:                     "
            f"{player_names}"
        )

        print(
            f"Oferta Computer:             "
            f"{money(offer.get('amount'))}"
        )

        print(
            f"Valor mercado:               "
            f"{money(offer.get('market_value'))}"
        )

        print(
            f"Premium:                     "
            f"{float(offer.get('premium_percent', 0) or 0):+.2f}%"
        )

        print(
            f"Calidad:                     "
            f"{offer.get('quality')}"
        )

        print(
            f"Caduca en:                   "
            f"{offer.get('hours_to_expiry')} h"
        )

        print(
            f"SOLVENCY_RESERVED:           "
            f"{'SI' if offer.get('solvency_reserved') else 'NO'}"
        )

        print(
            f"Otro ciclo seguro:           "
            f"{'SI' if offer.get('replacement_cycle_available') else 'NO'}"
        )

        cycle = (
            replacement.get(
                "cycle"
            )
            or {}
        )

        print(
            f"Ciclo sustitucion:           "
            f"{dt(cycle.get('cycle_end'))}"
        )

        print(
            f"Liquidez expected sustituta: "
            f"{money(simulation.get('replacement_expected_liquidity'))}"
        )

        print(
            f"Garantia tras reroll:        "
            f"{'SI' if simulation.get('guaranteed_after_reroll') else 'NO'}"
        )

        print(
            f"Margen tras reroll:          "
            f"{money(simulation.get('projected_surplus'))}"
        )

        print(
            f"Rerolls historicos:          "
            f"{offer.get('reroll_count')}"
        )

        print(
            f"Mejor oferta vista:          "
            f"{money(offer.get('best_offer_seen'))}"
        )

        print(
            f"DECISION:                    "
            f"{offer.get('action')}"
        )

        print(
            f"Motivo:                      "
            f"{offer.get('reason')}"
        )

    print()
    print("=" * 118)
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    for offer in board[
        "offers"
    ]:

        if (
            offer.get(
                "can_reroll"
            )
            and
            not offer[
                "simulation"
            ][
                "guaranteed_after_reroll"
            ]
        ):

            raise SystemExit(
                "ERROR: reroll permitido sin garantia T-15."
            )

        if (
            offer.get(
                "solvency_reserved"
            )
            and
            offer.get(
                "action"
            )
            == "REROLL_CANDIDATE"
            and
            not offer[
                "simulation"
            ][
                "guaranteed_after_reroll"
            ]
        ):

            raise SystemExit(
                "ERROR: oferta reservada rerolleable sin cobertura."
            )

    print(
        "COMPUTER OFFER REROLL SAFETY: OK"
    )

    print("=" * 118)


if __name__ == "__main__":
    main()
