from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


def money(
    value: int | float,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def print_player(
    player: dict,
) -> None:

    print()
    print(
        f"{player['name']:<24}"
        f"{money(player['price']):>14}"
    )

    print(
        f"   Speculation: "
        f"{player['speculation_score']:>5.1f}/100"
    )

    print(
        f"   Acción:      "
        f"{player['speculation_action']}"
    )

    print(
        f"   Rol:         "
        f"{player['dominant_role']}"
    )

    print(
        f"   Variación:   "
        f"{money(player['price_increment'])} "
        f"({player['price_increment_percent']:+.2f}%)"
    )

    print(
        f"   Momentum:    "
        f"{player['momentum_score']:+.1f}"
    )

    print(
        f"   Trend:       "
        f"{player['trend_score']:.1f}/100 "
        f"({player['trend']})"
    )

    confidence = (
        player[
            "history_confidence"
        ]
    )

    print(
        f"   Histórico:   "
        f"{confidence['confidence']}% "
        f"({confidence['label']})"
    )

    print(
        f"   Registros:   "
        f"{player['records']}"
    )

    print(
        f"   Hist comp:   "
        f"{player['historical_component']:+.2f}"
    )

    print(
        f"   Aceleración: "
        f"{player['acceleration_component']:+.2f}"
    )

    print(
        f"   Precio:      "
        f"{player['price_opportunity_score']:.1f}"
    )

    print(
        f"   Soporte dep: "
        f"{player['sporting_support_score']:.1f}"
    )

    risk = (
        player[
            "availability_risk"
        ]
    )

    print(
        f"   Riesgo:      "
        f"{risk['risk']} "
        f"({risk['label']})"
    )

    external = (
        player[
            "external_signal"
        ]
    )

    print(
        f"   Externo:     "
        f"{external['status']}"
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
        build_speculation_board(
            snapshot
        )
    )

    print()
    print("=" * 105)
    print(
        "                 BORDALÁS IA - SPECULATION ENGINE V2"
    )
    print("=" * 105)

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    # ==================================================
    # FRANCHISE
    # ==================================================

    active_franchise = (
        board[
            "active_franchise_bid"
        ]
    )

    print()
    print("=" * 105)
    print(
        "PRIORIDAD FRANCHISE"
    )
    print("=" * 105)

    if active_franchise is None:

        print()
        print(
            "No existe puja Franchise activa."
        )

    else:

        player = (
            active_franchise[
                "player"
            ]
        )

        offer = (
            active_franchise[
                "offer"
            ]
        )

        print()
        print(
            f"Jugador:      "
            f"{player['name']}"
        )

        print(
            f"Franchise:    "
            f"{player['franchise_score']}/100"
        )

        print(
            f"Puja activa:  "
            f"{money(offer['amount'])}"
        )

        print(
            f"Estado:       "
            f"{offer['status']}"
        )

    # ==================================================
    # BUDGET
    # ==================================================

    budget = (
        board[
            "budget"
        ]
    )

    print()
    print("=" * 105)
    print(
        "PRESUPUESTO ESPECULATIVO"
    )
    print("=" * 105)

    print()

    print(
        f"Activo:                "
        f"{'SÍ' if budget['enabled'] else 'NO'}"
    )

    print(
        f"Presupuesto total:     "
        f"{money(budget['total_budget'])}"
    )

    print(
        f"Máximo por operación:  "
        f"{money(budget['single_operation_limit'])}"
    )

    print(
        f"Bloqueado por:         "
        f"{budget.get('blocked_by')}"
    )

    print()
    print(
        budget[
            "reason"
        ]
    )

    # ==================================================
    # MARKET
    # ==================================================

    print()
    print("=" * 105)
    print(
        "OPORTUNIDADES EN MERCADO"
    )
    print("=" * 105)

    candidates = (
        board[
            "buy_candidates"
        ][
            :15
        ]
    )

    if not candidates:

        print()
        print(
            "No hay compras especulativas "
            "confirmadas actualmente."
        )

    for player in candidates:

        print_player(
            player
        )

    # ==================================================
    # EXECUTABLE
    # ==================================================

    print()
    print("=" * 105)
    print(
        "COMPRAS ESPECULATIVAS EJECUTABLES"
    )
    print("=" * 105)

    executable = (
        board[
            "executable_buys"
        ][
            :10
        ]
    )

    if not executable:

        print()
        print(
            "Ninguna."
        )

    for player in executable:

        print_player(
            player
        )

    # ==================================================
    # HOLDS
    # ==================================================

    print()
    print("=" * 105)
    print(
        "ACTIVOS PROPIOS - MANTENER"
    )
    print("=" * 105)

    holds = (
        board[
            "hold_candidates"
        ][
            :12
        ]
    )

    if not holds:

        print()
        print(
            "Ninguno."
        )

    for player in holds:

        print_player(
            player
        )

    # ==================================================
    # SELL
    # ==================================================

    print()
    print("=" * 105)
    print(
        "ACTIVOS PROPIOS - VENDER / VIGILAR"
    )
    print("=" * 105)

    sells = (
        board[
            "sell_candidates"
        ][
            :12
        ]
    )

    if not sells:

        print()
        print(
            "Ninguno."
        )

    for player in sells:

        print_player(
            player
        )

    # ==================================================
    # WATCHLIST
    # ==================================================

    print()
    print("=" * 105)
    print(
        "WATCHLIST ESPECULATIVA"
    )
    print("=" * 105)

    watchlist = (
        board[
            "watchlist"
        ][
            :15
        ]
    )

    if not watchlist:

        print()
        print(
            "Ninguna."
        )

    for player in watchlist:

        print_player(
            player
        )

    # ==================================================
    # EXTERNAL
    # ==================================================

    print()
    print("=" * 105)
    print(
        "INTELIGENCIA EXTERNA"
    )
    print("=" * 105)

    print()
    print(
        "Estado: NOT_CONNECTED"
    )

    print()
    print(
        "El motor ya combina momentum actual, "
        "histórico, confianza y aceleración."
    )

    print(
        "La siguiente capa añadirá señales "
        "externas y precio real de adquisición."
    )

    print()
    print("=" * 105)


if __name__ == "__main__":
    main()