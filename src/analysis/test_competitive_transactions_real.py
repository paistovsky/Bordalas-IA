from __future__ import annotations

from src.analysis.intelligent_bid_engine import (
    calculate_intelligent_bids,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)

from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
)

from src.collectors.board_history_collector import (
    collect_board_history,
)


def money(value) -> str:
    try:
        value = int(value or 0)
    except (TypeError, ValueError):
        value = 0

    return f"{value:,.0f} EUR"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def print_rivals(
    intelligence: dict,
    current_user_id: int | None,
) -> None:

    print()
    print("## THREAT SCORE REAL")
    print()

    managers = (
        intelligence.get(
            "managers",
            [],
        )
        or []
    )

    rivals = []

    for manager in managers:

        user_id = safe_int(
            manager.get(
                "user_id"
            )
        )

        if (
            current_user_id is not None
            and
            user_id == safe_int(
                current_user_id
            )
        ):
            continue

        threat = safe_float(
            manager.get(
                "threat_score"
            )
        )

        points = safe_int(
            manager.get(
                "points"
            )
        )

        rivals.append(
            {
                **manager,
                "_threat":
                    threat,

                "_points":
                    points,
            }
        )

    rivals.sort(
        key=lambda item: (
            item["_threat"],
            item["_points"],
        ),
        reverse=True,
    )

    header = (
        f"{'MANAGER':<30} "
        f"{'PTS':>6} "
        f"{'THREAT':>9} "
        f"{'NIVEL':>11} "
        f"{'SALDO EST.':>15} "
        f"{'PUJA MAX EST.':>15} "
        f"{'PERFIL':>12}"
    )

    print(header)
    print("-" * len(header))

    for manager in rivals:

        print(
            f"{str(manager.get('name') or '?'):<30} "
            f"{manager['_points']:>6} "
            f"{manager['_threat']:>8.1f} "
            f"{str(manager.get('threat_level') or '?'):>11} "
            f"{money(manager.get('balance')):>15} "
            f"{money(manager.get('maximum_bid')):>15} "
            f"{str(manager.get('profile') or '?'):>12}"
        )


def print_incoming_manager_offers(
    offer_decisions: dict,
) -> None:

    print()
    print("## OFERTAS REALES DE RIVALES POR NUESTROS JUGADORES")
    print()

    decisions = (
        offer_decisions.get(
            "decisions",
            [],
        )
        or []
    )

    manager_offers = [
        item
        for item in decisions
        if item.get(
            "counterparty_type"
        )
        == "MANAGER"
    ]

    if not manager_offers:

        print(
            "No hay ofertas de managers detectadas en el snapshot actual."
        )
        return

    for item in manager_offers:

        competitive = (
            item.get(
                "competitive_observer"
            )
            or {}
        )

        rival = (
            competitive.get(
                "rival"
            )
            or {}
        )

        print("-" * 100)

        print(
            f"Jugador:                 "
            f"{item.get('player_name') or item.get('player_id')}"
        )

        print(
            f"Rival:                   "
            f"{rival.get('name') or item.get('counterparty_id') or '?'}"
        )

        print(
            f"Oferta:                  "
            f"{money(item.get('amount'))}"
        )

        print(
            f"Valor mercado:           "
            f"{money(item.get('market_value'))}"
        )

        print(
            f"Speculation:             "
            f"{safe_float(item.get('speculation_score')):.1f}/100"
        )

        print(
            f"Threat rival:            "
            f"{safe_float(rival.get('threat_score')):.1f}/100"
        )

        print(
            f"Rival directo:           "
            f"{'SI' if rival.get('direct_rival') else 'NO'}"
        )

        print(
            f"Coste venta Pepe:        "
            f"{safe_float(competitive.get('our_sale_cost_score')):.1f}/100"
        )

        print(
            f"Refuerzo rival:          "
            f"{safe_float(competitive.get('rival_reinforcement_score')):.1f}/100"
        )

        print(
            f"Precio base venta:       "
            f"{money(competitive.get('base_sell_price'))}"
        )

        print(
            f"Precio estrategico:      "
            f"{money(competitive.get('strategic_sell_price'))}"
        )

        counter_amount = (
            competitive.get(
                "counter_amount"
            )
        )

        print(
            f"Decision competitiva:    "
            f"{competitive.get('decision') or 'SIN EVALUAR'}"
        )

        if counter_amount:

            print(
                f"Contraoferta propuesta:  "
                f"{money(counter_amount)}"
            )

        replacement = (
            competitive.get(
                "replacement",
                {},
            )
            or {}
        )

        replacement_detail = (
            (
                offer_decisions.get(
                    "replacement_lookup",
                    {},
                )
                or {}
            ).get(
                safe_int(
                    item.get(
                        "player_id"
                    )
                ),
                {},
            )
            or {}
        )

        print(
            f"Replacement status:      "
            f"{replacement_detail.get('replacement_status') or replacement.get('replacement_status') or '?'}"
        )

        print(
            f"XI tras venderlo:        "
            f"{safe_int(replacement_detail.get('post_sale_playable_count'), 0)}/11"
        )

        viable_names = ", ".join(
            str(
                candidate.get(
                    "name"
                )
                or
                candidate.get(
                    "id"
                )
            )
            for candidate
            in (
                replacement_detail.get(
                    "viable_market_candidates",
                    [],
                )
                or []
            )[
                :3
            ]
        )

        if viable_names:

            print(
                f"Alternativas mercado:     "
                f"{viable_names}"
            )

        print(
            f"Decision legacy actual:  "
            f"{item.get('decision')}"
        )

        reasons = (
            competitive.get(
                "reasons",
                [],
            )
            or []
        )

        for reason in reasons:
            print(
                f"  - {reason}"
            )


def print_offer_portfolio(
    offer_decisions: dict,
) -> None:

    print()
    print("## SIMULACION CONJUNTA DE OFERTAS RIVALES")
    print()

    portfolio = (
        offer_decisions.get(
            "competitive_portfolio",
            {},
        )
        or {}
    )

    recommended = (
        portfolio.get(
            "recommended"
        )
    )

    if not recommended:

        print(
            "No hay combinaciones de ofertas de managers para simular."
        )
        return

    print(
        f"Saldo actual:             "
        f"{money(portfolio.get('balance'))}"
    )

    print(
        f"Deficit:                  "
        f"{money(portfolio.get('deficit'))}"
    )

    print(
        f"Ofertas de managers:      "
        f"{safe_int(portfolio.get('offer_count'))}"
    )

    print()
    print("MEJORES COMBINACIONES")
    print()

    combos = (
        portfolio.get(
            "combinations",
            [],
        )
        or []
    )

    for combo in combos[:10]:

        print(
            "- "
            +
            ", ".join(
                combo.get(
                    "player_names",
                    [],
                )
            )
        )

        print(
            f"  Caja: {money(combo.get('total_amount'))} | "
            f"Saldo post: {money(combo.get('post_balance'))} | "
            f"XI: {safe_int(combo.get('playable_count'))}/11 | "
            f"Solvencia: {'SI' if combo.get('restores_solvency') else 'NO'} | "
            f"Dano rival agregado: {safe_float(combo.get('competitive_damage')):.1f}"
        )

    print()
    print("RECOMENDACION PORTFOLIO")
    print(
        ", ".join(
            recommended.get(
                "player_names",
                [],
            )
        )
        or
        "SIN DATOS"
    )

    print(
        f"Caja total:              "
        f"{money(recommended.get('total_amount'))}"
    )

    print(
        f"Saldo posterior:         "
        f"{money(recommended.get('post_balance'))}"
    )

    print(
        f"XI posterior:            "
        f"{safe_int(recommended.get('playable_count'))}/11"
    )

    print(
        f"Recupera solvencia:      "
        f"{'SI' if recommended.get('restores_solvency') else 'NO'}"
    )

def print_rival_market_players(
    intelligent_bids: list[dict],
) -> None:

    print()
    print("## JUGADORES REALES VENDIDOS POR OTROS MANAGERS")
    print()

    rival_players = [
        item
        for item in intelligent_bids
        if item.get(
            "seller_user_id"
        )
        is not None
    ]

    if not rival_players:

        print(
            "No se ha detectado ningun jugador del mercado actual "
            "con seller_user_id identificable en la estructura recibida."
        )

        print(
            "Esto NO significa que no existan ventas de managers; "
            "solo que el resultado actual de bid_engine no conserva "
            "todavia un propietario identificable para este test."
        )

        return

    for item in rival_players[:20]:

        competitive = (
            item.get(
                "competitive_observer"
            )
            or {}
        )

        rival = (
            competitive.get(
                "rival"
            )
            or {}
        )

        print("-" * 100)

        print(
            f"Jugador:                 "
            f"{item.get('name') or item.get('player_name') or item.get('id')}"
        )

        print(
            f"Vendedor:                "
            f"{rival.get('name') or item.get('seller_name') or item.get('seller_user_id')}"
        )

        print(
            f"Valor mercado:           "
            f"{money(item.get('market_price') or item.get('player_price'))}"
        )

        print(
            f"Puja sugerida legacy:    "
            f"{money(item.get('suggested_bid'))}"
        )

        print(
            f"Score jugador:           "
            f"{safe_float(item.get('final_score')):.1f}/100"
        )

        print(
            f"Threat vendedor:         "
            f"{safe_float(rival.get('threat_score')):.1f}/100"
        )

        print(
            f"Rival directo:           "
            f"{'SI' if rival.get('direct_rival') else 'NO'}"
        )

        print(
            f"Dano rival:              "
            f"{safe_float(competitive.get('rival_damage_score')):.1f}/100"
        )

        print(
            f"Ayuda liquidez rival:    "
            f"{safe_float(competitive.get('liquidity_help_score')):.1f}/100"
        )

        print(
            f"Maximo estrategico:      "
            f"{money(competitive.get('strategic_max_price'))}"
        )

        print(
            f"Decision competitiva:    "
            f"{competitive.get('decision') or 'SIN EVALUAR'}"
        )

        print(
            f"Decision legacy actual:  "
            f"{item.get('action')}"
        )

        reasons = (
            competitive.get(
                "reasons",
                [],
            )
            or []
        )

        for reason in reasons:
            print(
                f"  - {reason}"
            )


def main() -> None:

    print("=" * 120)
    print(
        "BORDALAS IA - COMPETITIVE TRANSACTIONS REAL LEAGUE - OBSERVER"
    )
    print("=" * 120)

    board = (
        collect_board_history()
    )

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    market_status = (
        snapshot.get(
            "market",
            {},
        )
        .get(
            "status",
            {},
        )
        or {}
    )

    current_user_id = (
        board.get(
            "current_user_id"
        )
    )

    rival_intelligence = (
        build_rival_intelligence(
            events=
                board.get(
                    "events",
                    [],
                ),

            users=
                board.get(
                    "users",
                    [],
                ),

            profiles=
                board.get(
                    "profiles",
                    [],
                ),

            catalog=
                snapshot.get(
                    "catalog",
                    {},
                ),

            current_user_id=
                current_user_id,

            own_finances=
                board.get(
                    "own_finances",
                    {},
                ),

            own_balance=
                market_status.get(
                    "balance"
                ),

            own_maximum_bid=
                market_status.get(
                    "maximumBid"
                ),
        )
    )

    print(
        f"Snapshot:                 "
        f"{snapshot_file}"
    )

    print(
        f"Ledger rival intelligence:"
        f" {rival_intelligence.get('ledger_status')}"
    )

    print(
        f"Saldo Pepe:               "
        f"{money(market_status.get('balance'))}"
    )

    print(
        f"Puja maxima Pepe:         "
        f"{money(market_status.get('maximumBid'))}"
    )

    print_rivals(
        rival_intelligence=
            rival_intelligence,
        current_user_id=
            current_user_id,
    )

    offer_decisions = (
        build_offer_decision_board(
            snapshot=
                snapshot,

            rival_intelligence=
                rival_intelligence,
        )
    )

    print_incoming_manager_offers(
        offer_decisions
    )

    print_offer_portfolio(
        offer_decisions
    )

    intelligent_bids = (
        calculate_intelligent_bids(
            snapshot=
                snapshot,

            rival_intelligence=
                rival_intelligence,
        )
    )

    print_rival_market_players(
        intelligent_bids
    )

    print()
    print("=" * 120)
    print(
        "# COMPETITIVE TRANSACTIONS REAL LEAGUE: FINISHED"
    )
    print(
        "# OBSERVER ONLY: NO SE HA EJECUTADO NINGUNA OPERACION"
    )
    print("=" * 120)


if __name__ == "__main__":
    main()
