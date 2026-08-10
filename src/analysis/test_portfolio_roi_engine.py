from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.portfolio_roi_engine import (
    build_portfolio_roi_board,
)


def money(
    value,
) -> str:

    if value is None:

        return (
            "DESCONOCIDO"
        )

    return (
        f"{value:,.0f} €"
    )


def percent(
    value,
) -> str:

    if value is None:

        return (
            "DESCONOCIDO"
        )

    return (
        f"{value:+.2f}%"
    )


def print_position(
    player: dict,
) -> None:

    print()
    print(
        f"{player['name']:<24}"
        f"{money(player['current_price']):>15}"
    )

    print(
        f"   Compra:       "
        f"{money(player['acquisition_price'])}"
    )

    print(
        f"   Fuente:       "
        f"{player['acquisition_source']}"
    )

    print(
        f"   Confianza:    "
        f"{player['acquisition_confidence']}%"
    )

    print(
        f"   Beneficio:    "
        f"{money(player['profit'])}"
    )

    print(
        f"   ROI:          "
        f"{percent(player['roi_percent'])}"
    )

    print(
        f"   Variación:    "
        f"{money(player['price_increment'])}"
    )

    print(
        f"   Speculation:  "
        f"{player['speculation_score']}"
    )

    print(
        f"   Trend:        "
        f"{player['trend_score']} "
        f"({player['trend']})"
    )

    confidence = (
        player.get(
            "history_confidence",
            {},
        )
        or {}
    )

    print(
        f"   Histórico:    "
        f"{confidence.get('confidence', 0)}% "
        f"({confidence.get('label', 'NO_HISTORY')})"
    )

    print(
        f"   Aceleración:  "
        f"{player['acceleration_state']}"
    )

    print(
        f"   Decisión:     "
        f"{player['portfolio_action']}"
    )

    print(
        f"   Prioridad:    "
        f"{player['portfolio_priority']}"
    )

    print(
        f"   Motivo:       "
        f"{player['portfolio_reason']}"
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
        build_portfolio_roi_board(
            snapshot
        )
    )

    print()
    print("=" * 105)
    print(
        "                    BORDALÁS IA - PORTFOLIO / ROI ENGINE"
    )
    print("=" * 105)

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()
    print("=" * 105)
    print(
        "COBERTURA DE PRECIOS DE ADQUISICIÓN"
    )
    print("=" * 105)

    print()

    print(
        f"Compras conocidas:       "
        f"{board['known_count']}"
    )

    print(
        f"Compras desconocidas:    "
        f"{board['unknown_count']}"
    )

    print(
        f"Coste conocido:          "
        f"{money(board['total_known_cost'])}"
    )

    print(
        f"Valor conocido actual:   "
        f"{money(board['total_known_value'])}"
    )

    print(
        f"Beneficio conocido:      "
        f"{money(board['total_known_profit'])}"
    )

    print(
        f"ROI cartera conocida:    "
        f"{percent(board['portfolio_roi_percent'])}"
    )

    print()
    print("=" * 105)
    print(
        "POSICIONES CON PRECIO DE COMPRA CONOCIDO"
    )
    print("=" * 105)

    if not board[
        "known"
    ]:

        print()
        print(
            "Todavía no existen adquisiciones cuyo "
            "precio pueda reconstruirse con certeza."
        )

    for player in board[
        "known"
    ]:

        print_position(
            player
        )

    print()
    print("=" * 105)
    print(
        "SALIDAS / VIGILANCIA"
    )
    print("=" * 105)

    if not board[
        "exits"
    ]:

        print()
        print(
            "Ninguna."
        )

    for player in board[
        "exits"
    ]:

        print_position(
            player
        )

    print()
    print("=" * 105)
    print(
        "MANTENER"
    )
    print("=" * 105)

    for player in board[
        "holds"
    ][
        :15
    ]:

        print_position(
            player
        )

    print()
    print("=" * 105)
    print(
        "IMPORTANTE"
    )
    print("=" * 105)

    print()

    print(
        "PREHISTORY significa que el jugador ya estaba "
        "en plantilla cuando comenzó nuestro histórico."
    )

    print(
        "Bordalás IA NO inventará su precio de compra."
    )

    print()

    print(
        "Las nuevas adquisiciones podrán quedar registradas "
        "automáticamente al relacionar la puja previa con "
        "la aparición posterior del jugador en plantilla."
    )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()