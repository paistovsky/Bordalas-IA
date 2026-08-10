import argparse
import sys

from src.actions.action_plan import (
    build_action_plan,
)

from src.actions.live_bid_executor import (
    find_existing_offer,
    get_sale_for_player,
    get_seller_description,
)

from src.actions.live_sale_executor import (
    find_existing_sale,
)

from src.actions.multi_bid_executor import (
    execute_bid_plan,
)

from src.actions.multi_sale_executor import (
    execute_sale_plan,
)

from src.analysis.lineup_engine import (
    build_lineup,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.sale_price_engine import (
    calculate_sale_price,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)

from src.analysis.strategic_decision_gate import (
    build_strategic_decision,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)

from src.analysis.transaction_planner import (
    POSITION_NAMES,
    simulate_transactions,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)


PREMIUM_BLOCKING_DECISIONS = {
    "PRIORIZAR_PREMIUM",
    "REESTRUCTURAR_POR_PREMIUM",
    "ESTUDIAR_REESTRUCTURACION",
}


def header(
    title: str,
) -> None:

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def money(
    value: int,
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

    snapshot = load_snapshot(
        snapshot_file
    )

    return (
        snapshot_file,
        snapshot,
    )


def get_user_id(
    snapshot: dict,
) -> int | None:

    league = snapshot.get(
        "league",
        {},
    )

    user = league.get(
        "user",
        {},
    )

    return user.get(
        "id"
    )


# ======================================================
# ALINEACIÓN
# ======================================================


def print_lineup(
    lineup: dict,
) -> None:

    header(
        "XI RECOMENDADO"
    )

    print()
    print(
        f"Formación: "
        f"{lineup['formation_name']}"
    )

    print(
        f"Alineados: "
        f"{lineup['total_selected']}/11"
    )

    print(
        f"Con partido: "
        f"{lineup['playable_count']}/11"
    )

    print()

    for player in lineup[
        "selected"
    ]:

        position = (
            POSITION_NAMES.get(
                player[
                    "lineup_position"
                ],
                "?",
            )
        )

        if not player[
            "automatic_lineup"
        ]:
            state = "DUDA"

        elif player[
            "has_game"
        ]:
            state = "PARTIDO"

        else:
            state = "SIN PARTIDO"

        print(
            f"{position:<18}"
            f"{player['name']:<24}"
            f"{state}"
        )

    blocked = lineup.get(
        "blocked_players",
        [],
    )

    if blocked:

        print()
        print(
            "BLOQUEADOS POR ESTADO"
        )

        print(
            "-" * 80
        )

        for player in blocked:

            availability = (
                player[
                    "availability"
                ]
            )

            print(
                f"{player['name']:<24}"
                f"{availability['label']}"
            )

            if availability[
                "status_info"
            ]:

                print(
                    "   "
                    f"{availability['status_info']}"
                )


# ======================================================
# PUJAS
# ======================================================


def get_bid_statuses(
    snapshot: dict,
    action_plan: dict,
) -> list[dict]:

    market = snapshot[
        "market"
    ]

    statuses = []

    for bid in action_plan[
        "bids"
    ]:

        player_id = (
            bid[
                "player_id"
            ]
        )

        existing = (
            find_existing_offer(
                market,
                player_id,
            )
        )

        sale = (
            get_sale_for_player(
                market,
                player_id,
            )
        )

        item = {
            **bid,

            "already_bid":
                existing
                is not None,

            "in_market":
                sale
                is not None,
        }

        if sale is not None:

            item[
                "seller"
            ] = (
                get_seller_description(
                    sale
                )
            )

            item[
                "current_price"
            ] = (
                sale.get(
                    "price",
                    0,
                )
            )

        statuses.append(
            item
        )

    return statuses


def print_bids(
    snapshot: dict,
    action_plan: dict,
) -> None:

    header(
        "PUJAS"
    )

    statuses = (
        get_bid_statuses(
            snapshot,
            action_plan,
        )
    )

    if not statuses:

        print()
        print(
            "Ninguna."
        )

        return

    print()

    for bid in statuses:

        print(
            bid[
                "player_name"
            ].upper()
        )

        print(
            f"   Valor mercado: "
            f"{money(bid['market_price'])}"
        )

        print(
            f"   Máximo IA:     "
            f"{money(bid['strategic_amount'])}"
        )

        print(
            f"   Puja propuesta:"
            f" {money(bid['amount'])}"
        )

        print(
            f"   Score:         "
            f"{bid['score']}/100"
        )

        if bid[
            "already_bid"
        ]:

            print(
                "   Estado:        "
                "YA PUJADO"
            )

        elif not bid[
            "in_market"
        ]:

            print(
                "   Estado:        "
                "FUERA DEL MERCADO"
            )

        else:

            print(
                f"   Origen:        "
                f"{bid.get('seller')}"
            )

            print(
                "   Estado:        "
                "PUJAR"
            )

        print()


# ======================================================
# VENTAS / PUBLICACIONES
# ======================================================


def get_safe_sales(
    snapshot: dict,
    transaction_plan: dict,
) -> list[dict]:

    analyzed_sales = (
        analyze_sales(
            snapshot
        )
    )

    by_id = {
        player["id"]:
            player

        for player
        in analyzed_sales
    }

    safe_ids = {
        player["id"]

        for player
        in transaction_plan[
            "safe_optional_sales"
        ]
    }

    mandatory_ids = {
        player["id"]

        for player
        in transaction_plan[
            "mandatory_sales"
        ]
    }

    target_ids = (
        safe_ids
        | mandatory_ids
    )

    return [
        by_id[player_id]

        for player_id
        in target_ids

        if player_id
        in by_id
    ]


def print_sales(
    snapshot: dict,
    sales: list[dict],
) -> None:

    header(
        "MERCADO DE SALIDA"
    )

    if not sales:

        print()
        print(
            "Ninguno."
        )

        return

    market = snapshot[
        "market"
    ]

    my_user_id = (
        get_user_id(
            snapshot
        )
    )

    print()

    for player in sales:

        pricing = (
            calculate_sale_price(
                player
            )
        )

        existing = None

        if my_user_id is not None:

            existing = (
                find_existing_sale(
                    market,
                    player["id"],
                    my_user_id,
                )
            )

        print(
            player[
                "name"
            ].upper()
        )

        print(
            f"   Valor:          "
            f"{money(player['price'])}"
        )

        print(
            f"   Sale score:     "
            f"{player['sale_score']}/100"
        )

        print(
            f"   Estrategia:     "
            f"{pricing['strategy']}"
        )

        if existing is not None:

            print(
                f"   Precio listado: "
                f"{money(existing.get('price', 0))}"
            )

            print(
                "   Estado:         "
                "YA PUBLICADO"
            )

        elif pricing[
            "should_list"
        ]:

            print(
                f"   Publicar a:     "
                f"{money(pricing['recommended_price'])}"
            )

            print(
                "   Estado:         "
                "PUBLICAR"
            )

        else:

            print(
                "   Estado:         "
                "NO PUBLICAR"
            )

        print()


# ======================================================
# ECONOMÍA
# ======================================================


def print_economy(
    snapshot: dict,
    action_plan: dict,
) -> None:

    header(
        "ECONOMÍA"
    )

    balance = int(
        snapshot[
            "market"
        ][
            "status"
        ][
            "balance"
        ]
    )

    total_bids = sum(
        bid[
            "amount"
        ]

        for bid
        in action_plan[
            "bids"
        ]
    )

    if_all_win = (
        balance
        - total_bids
    )

    print()
    print(
        f"Saldo actual:           "
        f"{money(balance)}"
    )

    print(
        f"Pujas del plan:         "
        f"{money(total_bids)}"
    )

    print(
        f"Saldo si ganamos todas: "
        f"{money(if_all_win)}"
    )

    print()
    print(
        "Las publicaciones NO se consideran "
        "dinero disponible."
    )


# ======================================================
# ESTRATEGIA DE TEMPORADA
# ======================================================


def print_strategy(
    snapshot: dict,
    decision: dict,
) -> None:

    header(
        "ESTRATEGIA DE TEMPORADA"
    )

    deadline = (
        decision[
            "deadline"
        ]
    )

    calendar = (
        deadline[
            "calendar"
        ]
    )

    print()
    print(
        f"Fase:               "
        f"{decision['phase']}"
    )

    print(
        f"XI con partido:      "
        f"{deadline['playable_count']}/11"
    )

    print(
        f"Huecos:              "
        f"{deadline['missing_playable']}"
    )

    print(
        f"Deadline XI:         "
        f"{calendar['time_to_lineup_lock']}"
    )

    print(
        f"Riesgo XI:           "
        f"{deadline['lineup_risk']}"
    )

    future = (
        deadline[
            "future_market_opportunities"
        ]
    )

    print(
        f"Mercados estimados:  "
        f"{future['cycles']} "
        f"({future['level']})"
    )

    if decision[
        "premium_active"
    ]:

        player = (
            decision[
                "premium_target"
            ]
        )

        print()
        print(
            "OPORTUNIDAD PREMIUM"
        )

        print(
            "-" * 80
        )

        print()
        print(
            f"Jugador:             "
            f"{player['name']}"
        )

        print(
            f"Strategic score:     "
            f"{player['strategic_score']}/100"
        )

        print(
            f"Valor:               "
            f"{money(player['price'])}"
        )

        print(
            f"Ventaja plan inicial:"
            f" {decision['difference']:+.2f}"
        )

        print(
            f"Ventaja temporal:    "
            f"{decision['effective_difference']:+.2f}"
        )

        print(
            f"Venta necesaria:     "
            f"{money(decision['minimum_sale_needed'])}"
        )

        print(
            f"Presión de venta:    "
            f"{decision['sale_pressure_percent']:.1f}%"
        )

    print()
    print(
        f"DECISIÓN ESTRATÉGICA:"
        f" {decision['decision']}"
    )

    print()
    print(
        decision[
            "reason"
        ]
    )

    # ==================================================
    # WATCHLIST
    # ==================================================

    board = (
        build_strategic_target_board(
            snapshot,
            limit=5,
            sort_by="strategic",
        )
    )

    print()
    print(
        "TOP OBJETIVOS DE TEMPORADA"
    )

    print(
        "-" * 80
    )

    for index, player in enumerate(
        board,
        start=1,
    ):

        print(
            f"{index}. "
            f"{player['name']:<20}"
            f"{player['strategic_score']:>5.1f}/100   "
            f"{player['ownership_state']}"
        )


# ======================================================
# CONFIRMACIÓN LIVE
# ======================================================


def confirm_execution() -> bool:

    print()
    print("=" * 80)

    print(
        "*** MODO LIVE SOLICITADO ***"
    )

    print()
    print(
        "Se realizarán operaciones reales "
        "en Biwenger."
    )

    print()
    print(
        "Escribe EJECUTAR para continuar:"
    )

    answer = input(
        "> "
    ).strip()

    return (
        answer
        == "EJECUTAR"
    )


# ======================================================
# GUARDAR XI
# ======================================================


def execute_lineup(
    snapshot: dict,
) -> dict:

    lineup = build_lineup(
        snapshot
    )

    if (
        lineup[
            "total_selected"
        ]
        != 11
    ):

        raise RuntimeError(
            "No existe un XI completo "
            "y seguro."
        )

    player_ids = [
        player["id"]

        for player
        in lineup[
            "selected"
        ]
    ]

    writer = (
        BiwengerWriteClient()
    )

    return writer.save_lineup(
        player_ids=
            player_ids,

        formation=
            lineup[
                "formation_name"
            ],

        reserve_ids=[],

        execute=True,
    )


# ======================================================
# MAIN
# ======================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Bordalás IA"
        )
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Ejecuta operaciones reales."
        ),
    )

    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help=(
            "Usa el último snapshot."
        ),
    )

    args = parser.parse_args()

    header(
        "BORDALÁS IA"
    )

    # ==================================================
    # SNAPSHOT
    # ==================================================

    if args.no_refresh:

        snapshot_file = (
            get_latest_snapshot()
        )

        snapshot = load_snapshot(
            snapshot_file
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
        "Pensando..."
    )

    # ==================================================
    # PLANES
    # ==================================================

    lineup = build_lineup(
        snapshot
    )

    transaction_plan = (
        simulate_transactions(
            snapshot
        )
    )

    action_plan = (
        build_action_plan(
            snapshot
        )
    )

    safe_sales = (
        get_safe_sales(
            snapshot,
            transaction_plan,
        )
    )

    strategic_decision = (
        build_strategic_decision(
            snapshot
        )
    )

    # ==================================================
    # INFORME
    # ==================================================

    print_lineup(
        lineup
    )

    print_bids(
        snapshot,
        action_plan,
    )

    print_sales(
        snapshot,
        safe_sales,
    )

    print_economy(
        snapshot,
        action_plan,
    )

    print_strategy(
        snapshot,
        strategic_decision,
    )

    # ==================================================
    # DRY RUN
    # ==================================================

    if not args.execute:

        header(
            "DRY-RUN COMPLETADO"
        )

        print()
        print(
            "No se ha modificado Biwenger."
        )

        return

    # ==================================================
    # GATE ESTRATÉGICO
    # ==================================================

    decision_name = (
        strategic_decision[
            "decision"
        ]
    )

    if (
        decision_name
        in PREMIUM_BLOCKING_DECISIONS
    ):

        header(
            "EJECUCIÓN TÁCTICA BLOQUEADA"
        )

        print()
        print(
            f"Decisión estratégica: "
            f"{decision_name}"
        )

        print()
        print(
            strategic_decision[
                "reason"
            ]
        )

        print()
        print(
            "Bordalás IA NO ejecutará nuevas "
            "pujas tácticas mientras exista esta "
            "decisión estratégica."
        )

        print()
        print(
            "Las pujas existentes tampoco serán "
            "canceladas automáticamente porque "
            "todavía no hemos validado esa operación."
        )

        return

    # ==================================================
    # CONFIRMACIÓN
    # ==================================================

    if not confirm_execution():

        print()
        print(
            "Ejecución cancelada."
        )

        return

    # ==================================================
    # PUJAS
    # ==================================================

    header(
        "1/3 - PUJAS"
    )

    bid_result = (
        execute_bid_plan(
            bids=
                action_plan[
                    "bids"
                ],

            execute=True,

            stop_on_error=True,
        )
    )

    for result in bid_result[
        "results"
    ]:

        print()
        print(
            result[
                "player_name"
            ]
        )

        print(
            f"   "
            f"{result['status']}"
        )

    if bid_result[
        "failed"
    ] > 0:

        sys.exit(1)

    # ==================================================
    # PUBLICACIONES
    # ==================================================

    header(
        "2/3 - MERCADO DE SALIDA"
    )

    sale_result = (
        execute_sale_plan(
            sales=
                safe_sales,

            execute=True,

            stop_on_error=True,
        )
    )

    for result in sale_result[
        "results"
    ]:

        print()
        print(
            result[
                "player_name"
            ]
        )

        print(
            f"   "
            f"{result['status']}"
        )

    if sale_result[
        "failed"
    ] > 0:

        sys.exit(1)

    # ==================================================
    # REFRESH ANTES DE XI
    # ==================================================

    print()
    print(
        "Refrescando antes del XI..."
    )

    collect_league_snapshot()

    fresh_snapshot_file = (
        get_latest_snapshot()
    )

    fresh_snapshot = (
        load_snapshot(
            fresh_snapshot_file
        )
    )

    # ==================================================
    # XI
    # ==================================================

    header(
        "3/3 - ALINEACIÓN"
    )

    lineup_result = (
        execute_lineup(
            fresh_snapshot
        )
    )

    print()
    print(
        f"HTTP: "
        f"{lineup_result.get('http_status')}"
    )

    print(
        f"Éxito: "
        f"{'SÍ' if lineup_result.get('success') else 'NO'}"
    )

    # ==================================================
    # FINAL
    # ==================================================

    header(
        "BORDALÁS IA - COMPLETADO"
    )

    print()
    print(
        f"Pujas nuevas: "
        f"{bid_result['executed']}"
    )

    print(
        f"Pujas omitidas: "
        f"{bid_result['skipped']}"
    )

    print(
        f"Publicaciones nuevas: "
        f"{sale_result['executed']}"
    )

    print(
        f"Publicaciones omitidas: "
        f"{sale_result['skipped']}"
    )

    print(
        f"Alineación guardada: "
        f"{'SÍ' if lineup_result.get('success') else 'NO'}"
    )

    print()


if __name__ == "__main__":
    main()