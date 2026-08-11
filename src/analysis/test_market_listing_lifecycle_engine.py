from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.market_listing_lifecycle_engine import (
    build_market_listing_lifecycle_board,
)


def fmt_dt(
    value,
) -> str:

    if value is None:
        return "DESCONOCIDO"

    try:
        return value.strftime(
            "%d/%m/%Y %H:%M"
        )

    except AttributeError:
        return str(
            value
        )


def money(
    value,
) -> str:

    return (
        f"{int(value or 0):,.0f} EUR"
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
        build_market_listing_lifecycle_board(
            snapshot
        )
    )

    cycles = (
        board[
            "computer_cycles"
        ]
    )

    next_cycle = (
        cycles.get(
            "next_safe_cycle"
        )
        or {}
    )

    print()
    print("=" * 120)
    print(
        "                 BORDALAS IA - MARKET LISTING LIFECYCLE ENGINE V1"
    )
    print("=" * 120)
    print()

    print(
        f"Snapshot:                     "
        f"{snapshot_file}"
    )

    print(
        f"Publicaciones propias:        "
        f"{board['listing_count']}"
    )

    print(
        f"Renovacion requerida:         "
        f"{board['renew_required_count']}"
    )

    print(
        f"Caducidad <= 12h:             "
        f"{board['expiry_warning_count']}"
    )

    print(
        f"Siguiente ciclo Computer:     "
        f"{fmt_dt(next_cycle.get('cycle_start'))}"
        f" - "
        f"{fmt_dt(next_cycle.get('cycle_end'))}"
    )

    print()

    print(
        "## PUBLICACIONES"
    )

    print()

    for player in board[
        "players"
    ]:

        print(
            f"{str(player.get('name') or '?'):<24} "
            f"{money(player.get('listed_price')):>15} "
            f"publicado={fmt_dt(player.get('listed_at'))} "
            f"caduca={fmt_dt(player.get('expires_at'))} "
            f"restan={player.get('hours_to_expiry')}h "
            f"next_cycle={'SI' if player.get('survives_next_cycle_end') else 'NO'} "
            f"{player.get('action')}"
        )

    print()
    print(
        "## RENOVAR"
    )
    print()

    if not board[
        "renew_required"
    ]:

        print(
            "NINGUNO"
        )

    else:

        for player in board[
            "renew_required"
        ]:

            print(
                f"{str(player.get('name') or '?'):<24} "
                f"caduca={fmt_dt(player.get('expires_at'))} "
                f"precio={money(player.get('listed_price'))} "
                f"-> RENEW_MARKET_LISTING"
            )

    print()
    print(
        "## JAVI HERNANDEZ"
    )
    print()

    javi = next(
        (
            player

            for player
            in board[
                "players"
            ]

            if int(
                player.get(
                    "player_id",
                    0,
                )
                or 0
            )
            == 25322
        ),
        None,
    )

    if javi is None:

        print(
            "Javi Hernandez no aparece actualmente publicado."
        )

    else:

        print(
            f"Publicado:                    "
            f"{fmt_dt(javi.get('listed_at'))}"
        )

        print(
            f"Caduca:                       "
            f"{fmt_dt(javi.get('expires_at'))}"
        )

        print(
            f"Duracion listing:             "
            f"{javi.get('listing_duration_hours')} h"
        )

        print(
            f"Horas restantes:              "
            f"{javi.get('hours_to_expiry')} h"
        )

        print(
            f"Llega al siguiente Computer:  "
            f"{'SI' if javi.get('survives_next_cycle_end') else 'NO'}"
        )

        print(
            f"Renovar:                      "
            f"{'SI' if javi.get('renew_required') else 'NO'}"
        )

        print(
            f"Decision:                     "
            f"{javi.get('action')}"
        )

    print()
    print(
        "## SAFETY"
    )
    print()

    if board[
        "listing_count"
    ] < 1:

        raise SystemExit(
            "ERROR: no se detectaron publicaciones propias."
        )

    for player in board[
        "renew_required"
    ]:

        if player.get(
            "survives_next_cycle_end"
        ):

            raise SystemExit(
                "ERROR: se solicita renovar una publicacion "
                "que ya sobrevive al siguiente ciclo."
            )

    print(
        "MARKET LISTING LIFECYCLE V1: OK"
    )

    print("=" * 120)


if __name__ == "__main__":
    main()
