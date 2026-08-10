from src.analysis.market_trend_engine import (
    build_market_trend_board,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def money(
    value: int | float,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def percent_text(
    window: dict,
) -> str:

    if not window[
        "available"
    ]:

        return (
            "SIN HISTÓRICO"
        )

    return (
        f"{window['change_percent']:+.2f}% "
        f"({money(window['change'])})"
    )


def print_trend(
    item: dict,
) -> None:

    print()
    print(
        f"{item['name']:<24}"
        f"{money(item['current_price']):>14}"
    )

    print(
        f"   Trend score: "
        f"{item['trend_score']:>5.1f}/100"
    )

    print(
        f"   Tendencia:   "
        f"{item['trend']}"
    )

    print(
        f"   Registros:   "
        f"{item['records']}"
    )

    print(
        f"   Incremento:  "
        f"{money(item['current_increment'])}"
    )

    print(
        f"   Histórico:   "
        f"{item['total_change_percent']:+.2f}% "
        f"({money(item['total_change'])})"
    )

    print(
        f"   1 día:       "
        f"{percent_text(item['change_1d'])}"
    )

    print(
        f"   3 días:      "
        f"{percent_text(item['change_3d'])}"
    )

    print(
        f"   7 días:      "
        f"{percent_text(item['change_7d'])}"
    )

    velocity = (
        item[
            "velocity"
        ]
    )

    if velocity[
        "available"
    ]:

        print(
            f"   Velocidad:   "
            f"{money(velocity['value_per_day'])}/día "
            f"({velocity['percent_per_day']:+.2f}%/día)"
        )

    else:

        print(
            "   Velocidad:   "
            "SIN HISTÓRICO SUFICIENTE"
        )

    acceleration = (
        item[
            "acceleration"
        ]
    )

    print(
        f"   Aceleración: "
        f"{acceleration['state']}"
    )

    if acceleration[
        "available"
    ]:

        print(
            f"                 "
            f"Anterior "
            f"{money(acceleration['previous_change'])} "
            f"→ Último "
            f"{money(acceleration['latest_change'])}"
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
        build_market_trend_board(
            "data"
        )
    )

    catalog = (
        snapshot[
            "catalog"
        ][
            "data"
        ][
            "players"
        ]
    )

    current_ids = {
        int(
            player[
                "id"
            ]
        )
        for player
        in catalog.values()
    }

    board = [
        item
        for item in board
        if item[
            "player_id"
        ]
        in current_ids
    ]

    print()
    print("=" * 105)
    print(
        "                   BORDALÁS IA - MARKET TREND ENGINE"
    )
    print("=" * 105)

    print()
    print(
        f"Último snapshot: "
        f"{snapshot_file}"
    )

    print(
        f"Jugadores con histórico: "
        f"{len(board)}"
    )

    print()
    print("=" * 105)
    print(
        "MAYOR TENDENCIA ALCISTA"
    )
    print("=" * 105)

    for item in board[
        :15
    ]:

        print_trend(
            item
        )

    print()
    print("=" * 105)
    print(
        "MAYOR TENDENCIA BAJISTA"
    )
    print("=" * 105)

    bottom = sorted(
        board,
        key=lambda item: (
            item[
                "trend_score"
            ],
            item[
                "current_increment"
            ],
        ),
    )

    for item in bottom[
        :15
    ]:

        print_trend(
            item
        )

    print()
    print("=" * 105)
    print(
        "NOTA"
    )
    print("=" * 105)

    print()
    print(
        "Al principio habrá poco histórico temporal."
    )

    print(
        "Con cada ejecución horaria de Bordalás IA "
        "el histórico crecerá automáticamente."
    )

    print(
        "Las ventanas de 1, 3 y 7 días aparecerán "
        "cuando existan snapshots suficientemente antiguos."
    )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()