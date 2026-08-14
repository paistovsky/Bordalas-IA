import argparse
import json
import time

from datetime import datetime
from pathlib import Path

from src.actions.autopilot_executor import (
    execute_autopilot_decision,
)

from src.analysis.decision_orchestrator import (
    build_global_decision,
)

from src.analysis.lineup_monitor import (
    save_lineup_monitor_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)

from src.presentation.lineup_renderer import (
    print_lineup_field,
)

from src.analysis.intelligent_bid_engine import (
    calculate_intelligent_bids,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)

from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
)

from src.analysis.negotiation_state_engine import (
    apply_observer_response,
    load_negotiation_state,
    save_negotiation_state,
)

from src.analysis.competitive_safety_gate import (
    select_single_competitive_action,
)

from src.analysis.competitive_execution_shadow import (
    build_competitive_shadow_decision,
    execute_competitive_shadow,
)

from src.analysis.competitive_live_executor import (
    execute_competitive_live_action,
)

from src.collectors.board_history_collector import (
    collect_board_history,
)


DEFAULT_INTERVAL_MINUTES = 30

LOG_DIRECTORY = (
    Path("data")
    / "autopilot"
)

LOG_FILE = (
    LOG_DIRECTORY
    / "autopilot_log.jsonl"
)

COMPETITIVE_LOG_FILE = (
    LOG_DIRECTORY
    / "competitive_observer_log.jsonl"
)


# ============================================================
# FORMATO
# ============================================================


def money(
    value,
) -> str:

    if value is None:
        return "DESCONOCIDO"

    return (
        f"{value:,.0f} EUR"
    )


def format_hours(
    value,
) -> str:

    if value is None:
        return "DESCONOCIDO"

    if value <= 0:
        return "0m"

    if value < 1:
        return (
            f"{int(value * 60)}m"
        )

    if value < 48:
        return (
            f"{value:.1f}h"
        )

    days = int(
        value
        // 24
    )

    remaining_hours = int(
        value
        % 24
    )

    return (
        f"{days}d "
        f"{remaining_hours}h"
    )


def format_datetime_value(
    value: str | None,
) -> str:

    if not value:
        return "DESCONOCIDO"

    try:

        parsed = (
            datetime.fromisoformat(
                value
            )
        )

        return (
            parsed.strftime(
                "%d/%m/%Y %H:%M"
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return str(
            value
        )


# ============================================================
# LOG
# ============================================================


def ensure_log_directory() -> None:

    LOG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def append_log(
    snapshot_file: str,
    result: dict,
    execution: dict | None = None,
    phase: str = "PRE_ACTION",
) -> None:

    ensure_log_directory()

    decision = (
        result[
            "decision"
        ]
    )

    state = (
        result[
            "state"
        ]
    )

    franchise = (
        state.get(
            "franchise",
            {},
        )
        or {}
    )

    target = (
        franchise.get(
            "target"
        )
        or {}
    )

    lineup_state = (
        state.get(
            "lineup",
            {},
        )
        or {}
    )

    lineup_monitor = (
        state.get(
            "lineup_monitor",
            {},
        )
        or {}
    )

    liquidity = (
        state.get(
            "liquidity",
            {},
        )
        or {}
    )

    recovery = (
        liquidity.get(
            "recovery",
            {},
        )
        or {}
    )

    offer_reroll = (
        state.get(
            "offer_reroll",
            {},
        )
        or {}
    )

    listing_lifecycle = (
        state.get(
            "listing_lifecycle",
            {},
        )
        or {}
    )

    deadline = (
        state.get(
            "deadline",
            {},
        )
        or {}
    )

    record = {
        "timestamp":
            datetime.now().isoformat(
                timespec=
                    "seconds"
            ),

        "log_phase":
            phase,

        "snapshot":
            snapshot_file,

        "target_matchday":
            state.get(
                "target_matchday"
            ),

        "next_matchday":
            state.get(
                "next_matchday"
            ),

        "matchday_phase":
            state.get(
                "phase"
            ),

        "first_kickoff":
            deadline.get(
                "first_kickoff"
            ),

        "real_deadline":
            deadline.get(
                "real_deadline"
            ),

        "next_round_unlock":
            deadline.get(
                "next_round_unlock"
            ),

        "operations_locked":
            state.get(
                "operations_locked"
            ),

        "balance":
            state.get(
                "balance"
            ),

        "hours_to_deadline":
            state.get(
                "hours_to_deadline"
            ),

        "lineup_risk":
            state.get(
                "lineup_risk"
            ),

        "lineup_pressure":
            state.get(
                "lineup_pressure_score"
            ),

        "lineup_playable":
            lineup_state.get(
                "playable_count"
            ),

        "lineup_missing":
            lineup_state.get(
                "missing"
            ),

        "lineup_monitor_action":
            lineup_monitor.get(
                "action"
            ),

        "lineup_external_source":
            lineup_monitor.get(
                "external_lineup_source"
            ),

        "hard_safety":
            bool(
                state.get(
                    "temporal_gate",
                    {},
                ).get(
                    "hard_safety_mode",
                    False,
                )
            ),

        "franchise_state":
            franchise.get(
                "state"
            ),

        "franchise_target":
            target.get(
                "name"
            ),

        "liquidity_listed":
            liquidity.get(
                "listing_count"
            ),

        "liquidity_to_list":
            liquidity.get(
                "to_list_count"
            ),

        "incoming_offer_count":
            liquidity.get(
                "incoming_offer_count"
            ),

        "recovery_needed":
            recovery.get(
                "needed"
            ),

        "recovery_possible":
            recovery.get(
                "possible"
            ),

        "recovery_deficit":
            recovery.get(
                "deficit"
            ),

        "computer_offer_count":
            offer_reroll.get(
                "offer_count"
            ),

        "computer_reroll_candidate_count":
            len(
                offer_reroll.get(
                    "reroll_candidates",
                    [],
                )
                or []
            ),

        "computer_accept_before_expiry_count":
            len(
                offer_reroll.get(
                    "accept_before_expiry",
                    [],
                )
                or []
            ),

        "listing_count":
            listing_lifecycle.get(
                "listing_count"
            ),

        "listing_renew_required_count":
            listing_lifecycle.get(
                "renew_required_count"
            ),

        "listing_renew_required":
            [
                {
                    "player_id":
                        item.get(
                            "player_id"
                        ),

                    "name":
                        item.get(
                            "name"
                        ),

                    "expires_at":
                        str(
                            item.get(
                                "expires_at"
                            )
                        ),

                    "hours_to_expiry":
                        item.get(
                            "hours_to_expiry"
                        ),

                    "listed_price":
                        item.get(
                            "listed_price"
                        ),
                }

                for item in listing_lifecycle.get(
                    "renew_required",
                    [],
                )
            ],

        "computer_offer_intelligence":
            [
                {
                    "offer_id":
                        offer.get(
                            "offer_id"
                        ),

                    "players":
                        [
                            player.get(
                                "name"
                            )

                            for player
                            in offer.get(
                                "players",
                                [],
                            )
                        ],

                    "amount":
                        offer.get(
                            "amount"
                        ),

                    "premium_percent":
                        offer.get(
                            "premium_percent"
                        ),

                    "solvency_reserved":
                        offer.get(
                            "solvency_reserved"
                        ),

                    "reroll_safe":
                        offer.get(
                            "reroll_safe"
                        ),

                    "projected_surplus":
                        (
                            offer.get(
                                "simulation",
                                {},
                            )
                            or {}
                        ).get(
                            "projected_surplus"
                        ),

                    "action":
                        offer.get(
                            "action"
                        ),
                }

                for offer
                in offer_reroll.get(
                    "offers",
                    [],
                )
            ],

        "decision_type":
            decision.get(
                "type"
            ),

        "decision_priority":
            decision.get(
                "priority"
            ),

        "decision_action":
            decision.get(
                "action"
            ),

        "decision_executable":
            decision.get(
                "executable"
            ),

        "decision_reason":
            decision.get(
                "reason"
            ),
    }

    if execution is not None:

        record[
            "execution"
        ] = {
            "action":
                execution.get(
                    "action"
                ),

            "status":
                execution.get(
                    "status"
                ),

            "write_performed":
                execution.get(
                    "write_performed"
                ),

            "success":
                execution.get(
                    "success"
                ),

            "http_status":
                execution.get(
                    "http_status"
                ),

            "reason":
                execution.get(
                    "reason"
                ),
        }

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
        )

        file.write(
            "\n"
        )



# ============================================================
# COMPETITIVE INTELLIGENCE V2.0 - CONTROLLED LIVE
# ============================================================


def safe_int(
    value,
    default: int = 0,
) -> int:

    try:
        return int(
            value
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        return default


def safe_float(
    value,
    default: float = 0.0,
) -> float:

    try:
        return float(
            value
            or 0.0
        )

    except (
        TypeError,
        ValueError,
    ):
        return default


def build_competitive_observer(
    snapshot: dict,
    temporal_gate: dict | None = None,
    current_balance: int | None = None,
) -> dict:
    """
    V1.8.1 SAFETY GATE DRY RUN.

    Calcula inteligencia competitiva en paralelo a la decision
    legacy. No ejecuta escrituras en Biwenger.
    """

    temporal_gate = (
        temporal_gate
        or {}
    )

    try:

        board = (
            collect_board_history()
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

        negotiation_state = (
            load_negotiation_state()
        )

        offer_decisions = (
            build_offer_decision_board(
                snapshot=
                    snapshot,

                rival_intelligence=
                    rival_intelligence,

                negotiation_state=
                    negotiation_state,
            )
        )

        intelligent_bids = (
            calculate_intelligent_bids(
                snapshot=
                    snapshot,

                rival_intelligence=
                    rival_intelligence,
            )
        )

        manager_offers = []

        updated_negotiation_state = (
            negotiation_state
        )

        for decision in (
            offer_decisions.get(
                "decisions",
                [],
            )
            or []
        ):

            if (
                decision.get(
                    "counterparty_type"
                )
                !=
                "MANAGER"
            ):
                continue

            competitive = (
                decision.get(
                    "competitive_observer",
                    {},
                )
                or {}
            )

            negotiation = (
                decision.get(
                    "negotiation_observer",
                    {},
                )
                or {}
            )

            manager_offers.append(
                {
                    "offer_id":
                        decision.get(
                            "offer_id"
                        ),

                    "player_id":
                        decision.get(
                            "player_id"
                        ),

                    "player_name":
                        decision.get(
                            "player_name"
                        )
                        or
                        decision.get(
                            "name"
                        ),

                    "rival_user_id":
                        decision.get(
                            "counterparty_id"
                        ),

                    "rival_name":
                        (
                            decision.get(
                                "counterparty_name"
                            )
                            or
                            (
                                competitive.get(
                                    "rival",
                                    {},
                                )
                                or {}
                            ).get(
                                "name"
                            )
                        ),

                    "amount":
                        decision.get(
                            "amount"
                        ),

                    "legacy_decision":
                        decision.get(
                            "decision"
                        ),

                    "competitive_decision":
                        competitive.get(
                            "decision"
                        ),

                    "decision_authority":
                        decision.get(
                            "decision_authority",
                            "LEGACY",
                        ),

                    "authoritative_decision":
                        decision.get(
                            "authoritative_decision"
                        ),

                    "authoritative_counter_amount":
                        decision.get(
                            "authoritative_counter_amount"
                        ),

                    "authority_observer_only":
                        decision.get(
                            "authority_observer_only",
                            True,
                        ),

                    "base_sell_price":
                        competitive.get(
                            "base_sell_price"
                        ),

                    "strategic_sell_price":
                        competitive.get(
                            "strategic_sell_price"
                        ),

                    "competitive_premium_percent":
                        competitive.get(
                            "competitive_premium_percent"
                        ),

                    "temporal_premium_percent":
                        competitive.get(
                            "temporal_premium_percent"
                        ),

                    "sporting_premium_percent":
                        competitive.get(
                            "sporting_premium_percent"
                        ),

                    "sporting_cost_score":
                        competitive.get(
                            "sporting_cost_score"
                        ),

                    "sporting_opportunity_cost":
                        competitive.get(
                            "sporting_opportunity_cost",
                            {},
                        ),

                    "solvency_discount_percent":
                        competitive.get(
                            "solvency_discount_percent"
                        ),

                    "counter_amount":
                        competitive.get(
                            "counter_amount"
                        ),

                    "speculation_score":
                        competitive.get(
                            "speculation_score"
                        ),

                    "rival_reinforcement_score":
                        competitive.get(
                            "rival_reinforcement_score"
                        ),

                    "replacement":
                        competitive.get(
                            "replacement"
                        ),

                    "replacement_detail":
                        (
                            (
                                offer_decisions.get(
                                    "replacement_lookup",
                                    {},
                                )
                                or {}
                            ).get(
                                safe_int(
                                    decision.get(
                                        "player_id"
                                    )
                                ),
                                {},
                            )
                            or {}
                        ),

                    "negotiation":
                        negotiation,

                    "legacy_differs":
                        (
                            decision.get(
                                "decision"
                            )
                            !=
                            decision.get(
                                "authoritative_decision"
                            )
                        ),
                }
            )

            if (
                negotiation.get(
                    "should_respond"
                )
            ):

                updated_negotiation_state = (
                    apply_observer_response(
                        state=
                            updated_negotiation_state,

                        assessment=
                            negotiation,

                        player_id=
                            decision.get(
                                "player_id"
                            ),

                        rival_user_id=
                            decision.get(
                                "counterparty_id"
                            ),

                        player_name=
                            (
                                decision.get(
                                    "player_name"
                                )
                                or
                                decision.get(
                                    "name"
                                )
                            ),
                    )
                )

        save_negotiation_state(
            updated_negotiation_state
        )

        portfolio = (
            offer_decisions.get(
                "competitive_portfolio",
                {},
            )
            or {}
        )

        safety_gate = (
            select_single_competitive_action(
                offers=
                    manager_offers,

                temporal_gate=
                    temporal_gate,

                current_balance=
                    current_balance,
            )
        )

        execution_shadow = (
            build_competitive_shadow_decision(
                manager_offers=
                    manager_offers,

                temporal_gate=
                    temporal_gate,

                current_balance=
                    current_balance,
            )
        )

        shadow_execution = (
            execute_competitive_shadow(
                execution_shadow
            )
        )

        return {
            "observer_only":
                True,

            "available":
                True,

            "error":
                None,

            "rival_intelligence":
                rival_intelligence,

            "manager_offers":
                manager_offers,

            "competitive_portfolio":
                portfolio,

            "competitive_safety_gate":
                safety_gate,

            "competitive_execution_shadow":
                execution_shadow,

            "competitive_shadow_execution":
                shadow_execution,

            "intelligent_bids":
                intelligent_bids,
        }

    except Exception as error:

        return {
            "observer_only":
                True,

            "available":
                False,

            "error":
                (
                    f"{type(error).__name__}: "
                    f"{error}"
                ),

            "rival_intelligence":
                {},

            "manager_offers":
                [],

            "competitive_portfolio":
                {},

            "intelligent_bids":
                {},
        }


def append_competitive_log(
    snapshot_file: str,
    observer: dict,
) -> None:

    ensure_log_directory()

    record = {
        "timestamp":
            datetime.now().isoformat(
                timespec=
                    "seconds"
            ),

        "snapshot":
            snapshot_file,

        "observer_only":
            True,

        "available":
            observer.get(
                "available"
            ),

        "error":
            observer.get(
                "error"
            ),

        "manager_offers":
            observer.get(
                "manager_offers",
                [],
            ),

        "competitive_portfolio":
            observer.get(
                "competitive_portfolio",
                {},
            ),
    }

    with open(
        COMPETITIVE_LOG_FILE,
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
        )

        file.write(
            "\n"
        )


def print_competitive_observer(
    observer: dict,
) -> None:

    print()
    print(
        "-"
        * 100
    )

    print(
        "COMPETITIVE INTELLIGENCE V2.0 - CONTROLLED LIVE"
    )

    print(
        "-"
        * 100
    )

    if not observer.get(
        "available"
    ):

        print()
        print(
            "Competitive Observer no disponible."
        )

        print(
            observer.get(
                "error"
            )
        )

        print()
        print(
            "La decision legacy NO se modifica."
        )

        return

    offers = (
        observer.get(
            "manager_offers",
            [],
        )
        or []
    )

    print()
    print(
        f"Ofertas de managers:     "
        f"{len(offers)}"
    )

    legacy_differences = sum(
        1

        for item
        in offers

        if item.get(
            "legacy_differs"
        )
    )

    print(
        f"Diferencias legacy:      "
        f"{legacy_differences}"
    )

    for item in offers:

        negotiation = (
            item.get(
                "negotiation",
                {},
            )
            or {}
        )

        replacement = (
            item.get(
                "replacement",
                {},
            )
            or {}
        )

        replacement_detail = (
            item.get(
                "replacement_detail",
                {},
            )
            or {}
        )

        print()
        print(
            f"{item.get('player_name') or '?'} "
            f"<- {item.get('rival_name') or 'RIVAL'}"
        )

        print(
            f"  Oferta rival:          "
            f"{money(item.get('amount'))}"
        )

        print(
            f"  Legacy:                "
            f"{item.get('legacy_decision')}"
        )

        print(
            f"  Competitive:           "
            f"{item.get('competitive_decision')}"
        )

        print(
            f"  Authority:             "
            f"{item.get('decision_authority') or 'LEGACY'}"
        )

        print(
            f"  Final autoritativo:    "
            f"{item.get('authoritative_decision')}"
        )

        print(
            f"  Final ejecutable:      NO (OBSERVER)"
        )

        print(
            f"  Precio base:           "
            f"{money(item.get('base_sell_price'))}"
        )

        print(
            f"  Precio estrategico:    "
            f"{money(item.get('strategic_sell_price'))}"
        )

        print(
            f"  Prima competitiva:     "
            f"{safe_float(item.get('competitive_premium_percent')):+.2f}%"
        )

        print(
            f"  Prima deadline:        "
            f"{safe_float(item.get('temporal_premium_percent')):+.2f}%"
        )

        print(
            f"  Prima deportiva:       "
            f"{safe_float(item.get('sporting_premium_percent')):+.2f}%"
        )

        print(
            f"  Descuento solvencia:   "
            f"{-safe_float(item.get('solvency_discount_percent')):+.2f}%"
        )

        print(
            f"  Contraoferta:          "
            f"{money(item.get('counter_amount'))}"
        )

        print(
            f"  Speculation:           "
            f"{safe_float(item.get('speculation_score')):.1f}/100"
        )

        print(
            f"  Refuerzo rival:        "
            f"{safe_float(item.get('rival_reinforcement_score')):.1f}/100"
        )

        replacement_status = (
            replacement_detail.get(
                "replacement_status"
            )
            or
            replacement.get(
                "replacement_status"
            )
            or
            "UNKNOWN"
        )

        print(
            f"  Replacement:           "
            f"{replacement_status}"
        )

        if replacement_detail:

            print(
                f"  XI antes/despues:      "
                f"{safe_int(replacement_detail.get('pre_sale_playable_count'))}/11"
                f" -> "
                f"{safe_int(replacement_detail.get('post_sale_playable_count'))}/11"
            )

            print(
                f"  Fuente reemplazo:      "
                f"{replacement_detail.get('replacement_source') or 'UNKNOWN'}"
            )

            incoming_names = ", ".join(
                str(
                    player.get(
                        "name"
                    )
                    or
                    player.get(
                        "id"
                    )
                )

                for player
                in (
                    replacement_detail.get(
                        "incoming_players",
                        [],
                    )
                    or []
                )
            )

            print(
                f"  Entra al XI:           "
                f"{incoming_names or 'NINGUNO'}"
            )

            print(
                f"  Formacion:             "
                f"{replacement_detail.get('formation_before') or '?'}"
                f" -> "
                f"{replacement_detail.get('formation_after') or '?'}"
            )

            sporting = (
                item.get(
                    "sporting_opportunity_cost",
                    {},
                )
                or {}
            )

            if sporting:

                before_score = (
                    sporting.get("lineup_score_before")
                    if sporting.get("lineup_score_before") is not None
                    else sporting.get("pre_sale_lineup_score")
                )
                after_score = (
                    sporting.get("lineup_score_after")
                    if sporting.get("lineup_score_after") is not None
                    else sporting.get("post_sale_lineup_score")
                )
                loss_score = (
                    sporting.get("lineup_score_loss")
                    if sporting.get("lineup_score_loss") is not None
                    else sporting.get("sporting_cost")
                )
                loss_percent = (
                    sporting.get("lineup_score_loss_percent")
                    if sporting.get("lineup_score_loss_percent") is not None
                    else sporting.get("sporting_cost_percent")
                )

                print(
                    f"  Lineup score:          "
                    f"{safe_float(before_score):.2f}"
                    f" -> "
                    f"{safe_float(after_score):.2f}"
                )

                print(
                    f"  Perdida deportiva:     "
                    f"{safe_float(loss_score):.2f}"
                    f" | "
                    f"{safe_float(loss_percent):.2f}%"
                )

                print(
                    f"  Sporting cost score:   "
                    f"{safe_float(item.get('sporting_cost_score')):.1f}/100"
                )

            else:

                quality_loss = (
                    replacement_detail.get(
                        "quality_loss_score"
                    )
                )

                print(
                    f"  Calidad legacy:        "
                    f"{'NO CALCULABLE' if quality_loss is None else f'{safe_float(quality_loss):.1f} (escala interna)'}"
                )

        print(
            f"  Negotiation event:     "
            f"{negotiation.get('event') or 'SIN ESTADO'}"
        )

        print(
            f"  Action gate:           "
            f"{negotiation.get('action_gate') or 'SIN ESTADO'}"
        )

        print(
            f"  Ronda:                 "
            f"{safe_int(negotiation.get('negotiation_round'))}"
        )

        print(
            f"  Responderia ahora:     "
            f"{'SI' if negotiation.get('should_respond') else 'NO'}"
        )

        gate_item = next(
            (
                row
                for row in (
                    observer.get(
                        "competitive_safety_gate",
                        {},
                    ).get(
                        "evaluations",
                        [],
                    )
                    or []
                )
                if (
                    row.get("offer_id") == item.get("offer_id")
                    and row.get("player_id") == item.get("player_id")
                )
            ),
            None,
        )

        gate = (
            (gate_item or {}).get(
                "gate",
                {},
            )
            or {}
        )

        print(
            f"  Safety Gate V1.8:      "
            f"{gate.get('status', 'UNKNOWN')}"
        )

        print(
            f"  Gate autorizado:       "
            f"{'SI' if gate.get('authorized') else 'NO'}"
        )

        print(
            "  Would execute:         NO (DRY RUN)"
        )

        print(
            f"  Gate reason:           "
            f"{gate.get('reason', '-')}"
        )

        if item.get(
            "legacy_differs"
        ):

            print(
                "  >>> AUDIT: LEGACY DIFIERE DE LA AUTORIDAD COMPETITIVE"
            )

    safety_gate = (
        observer.get(
            "competitive_safety_gate",
            {},
        )
        or {}
    )

    print()
    print(
        "SAFETY GATE V1.8"
    )
    print()

    print(
        f"  Evaluadas:             "
        f"{safety_gate.get('evaluated_count', 0)}"
    )

    print(
        f"  Autorizadas dry-run:   "
        f"{safety_gate.get('authorized_count', 0)}"
    )

    print(
        f"  Seleccionadas max:     "
        f"{safety_gate.get('selected_count', 0)}"
    )

    print(
        "  Regla por ciclo:       MAXIMO 1 ACCION"
    )

    print(
        "  Escritura competitiva: NO"
    )

    execution_shadow = (
        observer.get(
            "competitive_execution_shadow",
            {},
        )
        or {}
    )

    shadow_execution = (
        observer.get(
            "competitive_shadow_execution",
            {},
        )
        or {}
    )

    print()
    print(
        "EXECUTION SHADOW V1.9"
    )
    print()

    selected_shadow = (
        execution_shadow.get(
            "selected"
        )
        or {}
    )

    print(
        f"  Estado:                "
        f"{execution_shadow.get('status', 'UNKNOWN')}"
    )

    print(
        f"  Seleccion:             "
        f"{selected_shadow.get('player_name') or 'NINGUNA'}"
    )

    print(
        f"  Accion:                "
        f"{shadow_execution.get('action') or 'NINGUNA'}"
    )

    print(
        f"  Llegaria al executor:  "
        f"{'SI' if execution_shadow.get('would_reach_executor') else 'NO'}"
    )

    print(
        f"  Would write:           "
        f"{'SI' if shadow_execution.get('would_write') else 'NO'}"
    )

    print(
        f"  Shadow status:         "
        f"{shadow_execution.get('status', 'UNKNOWN')}"
    )

    print(
        f"  Escritura realizada:   "
        f"{'SI' if shadow_execution.get('write_performed') else 'NO'}"
    )

    print(
        f"  Shadow reason:         "
        f"{shadow_execution.get('reason', '-')}"
    )

    portfolio = (
        observer.get(
            "competitive_portfolio",
            {},
        )
        or {}
    )

    print()
    print(
        "PORTFOLIO COMPETITIVO"
    )

    for mode in (
        "current",
        "strategic",
    ):

        scenario = (
            portfolio.get(
                mode,
                {},
            )
            or {}
        )

        recommended = (
            scenario.get(
                "recommended"
            )
            or {}
        )

        print()

        print(
            f"  {mode.upper()}: "
            f"{', '.join(recommended.get('player_names', []) or []) or 'SIN RECOMENDACION'}"
        )

        if recommended:

            print(
                f"    Caja:                "
                f"{money(recommended.get('total_amount'))}"
            )

            print(
                f"    Saldo post:          "
                f"{money(recommended.get('post_balance'))}"
            )

            print(
                f"    XI post:             "
                f"{safe_int(recommended.get('playable_count'))}/11"
            )

            portfolio_incoming = ", ".join(
                str(
                    player.get(
                        "name"
                    )
                    or
                    player.get(
                        "id"
                    )
                )

                for player
                in (
                    recommended.get(
                        "incoming_players",
                        [],
                    )
                    or []
                )
            )

            print(
                f"    Entran al XI:        "
                f"{portfolio_incoming or 'NINGUNO'}"
            )

            print(
                f"    Formacion:           "
                f"{recommended.get('formation_before') or '?'}"
                f" -> "
                f"{recommended.get('formation_after') or '?'}"
            )

            print(
                f"    Solvencia:           "
                f"{'SI' if recommended.get('restores_solvency') else 'NO'}"
            )

    print()
    print(
        "V1.7 AUTHORITY OBSERVER: Competitive manda conceptualmente "
        "en ofertas de managers, pero ninguna decision autoritativa "
        "se envia todavia al executor de Biwenger."
    )


# ============================================================
# SNAPSHOT
# ============================================================


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
# OUTPUT
# ============================================================


def print_cycle_result(
    snapshot_file: str,
    snapshot: dict,
    result: dict,
) -> None:

    decision = (
        result[
            "decision"
        ]
    )

    state = (
        result[
            "state"
        ]
    )

    deadline = (
        state.get(
            "deadline",
            {},
        )
        or {}
    )

    first_match = (
        deadline.get(
            "first_match",
            {},
        )
        or {}
    )

    franchise = (
        state.get(
            "franchise",
            {},
        )
        or {}
    )

    lineup_state = (
        state.get(
            "lineup",
            {},
        )
        or {}
    )

    lineup = (
        lineup_state.get(
            "lineup",
            {},
        )
        or {}
    )

    lineup_monitor = (
        state.get(
            "lineup_monitor",
            {},
        )
        or {}
    )

    liquidity = (
        state.get(
            "liquidity",
            {},
        )
        or {}
    )

    recovery = (
        liquidity.get(
            "recovery",
            {},
        )
        or {}
    )

    speculation = (
        state.get(
            "speculation",
            {},
        )
        or {}
    )

    budget = (
        speculation.get(
            "budget",
            {},
        )
        or {}
    )

    offer_reroll = (
        state.get(
            "offer_reroll",
            {},
        )
        or {}
    )

    listing_lifecycle = (
        state.get(
            "listing_lifecycle",
            {},
        )
        or {}
    )

    target = (
        franchise.get(
            "target"
        )
    )

    temporal_gate = (
        state.get(
            "temporal_gate",
            {},
        )
        or {}
    )

    print()
    print(
        "="
        * 100
    )

    print(
        "                       BORDALAS IA - AUTOPILOT V3 + COMPETITIVE V2.0 CONTROLLED LIVE"
    )

    print(
        "="
        * 100
    )

    print()

    print(
        f"Hora:                    "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"Snapshot:                "
        f"{snapshot_file}"
    )

    print()

    # --------------------------------------------------------
    # JORNADA REAL
    # --------------------------------------------------------

    print(
        f"Jornada objetivo:        "
        f"{state.get('target_matchday')}"
    )

    print(
        f"Siguiente jornada:       "
        f"{state.get('next_matchday')}"
    )

    print(
        f"Fase:                    "
        f"{state.get('phase')}"
    )

    print(
        f"Primer partido:          "
        f"{first_match.get('home', '?')} - "
        f"{first_match.get('away', '?')}"
    )

    print(
        f"Inicio jornada:          "
        f"{format_datetime_value(deadline.get('first_kickoff'))}"
    )

    print(
        f"Safety T-90:             "
        f"{format_datetime_value(deadline.get('safety_deadline'))}"
    )

    print(
        f"Deadline T-15:           "
        f"{format_datetime_value(deadline.get('real_deadline'))}"
    )

    print(
        f"Unlock siguiente:        "
        f"{format_datetime_value(deadline.get('next_round_unlock'))}"
    )

    print(
        f"Tiempo al deadline:      "
        f"{format_hours(state.get('hours_to_deadline'))}"
    )

    print(
        f"Operaciones bloqueadas:  "
        f"{'SI' if temporal_gate.get('operations_locked') else 'NO'}"
    )

    print()

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    print(
        f"Saldo:                   "
        f"{money(state.get('balance'))}"
    )

    print(
        f"Riesgo XI:               "
        f"{state.get('lineup_risk')}"
    )

    print(
        f"Presion XI:              "
        f"{state.get('lineup_pressure_score')}/100"
    )

    print(
        f"XI valido:               "
        f"{lineup_state.get('playable_count', 0)}/11"
    )

    print(
        f"Huecos:                  "
        f"{lineup_state.get('missing', 0)}"
    )

    print(
        f"Lineup Monitor:          "
        f"{lineup_monitor.get('action')}"
    )

    print(
        f"Fuente legacy:       "
        f"{lineup_monitor.get('external_lineup_source')}"
    )

    print(
        f"Hard Safety:             "
        f"{'SI' if temporal_gate.get('hard_safety_mode') else 'NO'}"
    )

    print()

    print(
        f"Publicados liquidez:     "
        f"{liquidity.get('listing_count', 0)}/"
        f"{len(liquidity.get('roster', []))}"
    )

    print(
        f"Pendientes publicar:     "
        f"{liquidity.get('to_list_count', 0)}"
    )

    print(
        f"Ofertas de liquidez:     "
        f"{liquidity.get('incoming_offer_count', 0)}"
    )

    if recovery.get(
        "needed"
    ):

        print(
            f"Deficit recuperacion:    "
            f"{money(recovery.get('deficit'))}"
        )

        print(
            f"Plan financiable:        "
            f"{'SI' if recovery.get('possible') else 'NO'}"
        )

    print()

    print(
        f"Franchise state:         "
        f"{franchise.get('state')}"
    )

    if target:

        print(
            f"Franchise target:        "
            f"{target.get('name')}"
        )

    print()

    print(
        f"Speculation:             "
        f"{'ACTIVA' if budget.get('enabled') else 'BLOQUEADA'}"
    )

    if not budget.get(
        "enabled"
    ):

        print(
            f"Bloqueada por:           "
            f"{budget.get('blocked_by')}"
        )

    # --------------------------------------------------------
    # COMPUTER OFFER INTELLIGENCE
    # --------------------------------------------------------

    print()

    print(
        "COMPUTER OFFER INTELLIGENCE"
    )

    print(
        f"Ofertas Computer:        "
        f"{offer_reroll.get('offer_count', 0)}"
    )

    print(
        f"Reroll candidatos:       "
        f"{len(offer_reroll.get('reroll_candidates', []) or [])}"
    )

    print(
        f"Expiry watch:            "
        f"{len(offer_reroll.get('accept_before_expiry', []) or [])}"
    )

    for offer in (
        offer_reroll.get(
            "offers",
            [],
        )
        or []
    ):

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
            offer.get(
                "simulation",
                {},
            )
            or {}
        )

        print()

        print(
            f"{player_names}"
        )

        print(
            f"  Oferta:                "
            f"{money(offer.get('amount'))}"
        )

        print(
            f"  Premium:               "
            f"{float(offer.get('premium_percent', 0) or 0):+.2f}%"
        )

        print(
            f"  Reserved solvencia:    "
            f"{'SI' if offer.get('solvency_reserved') else 'NO'}"
        )

        print(
            f"  Otro ciclo seguro:     "
            f"{'SI' if offer.get('replacement_cycle_available') else 'NO'}"
        )

        print(
            f"  Garantia tras reroll:  "
            f"{'SI' if simulation.get('guaranteed_after_reroll') else 'NO'}"
        )

        print(
            f"  Margen tras reroll:    "
            f"{money(simulation.get('projected_surplus'))}"
        )

        print(
            f"  Caduca en:             "
            f"{offer.get('hours_to_expiry')} h"
        )

        print(
            f"  Decision Pepe:         "
            f"{offer.get('action')}"
        )

    print()

    print(
        "MARKET LISTING LIFECYCLE"
    )

    print(
        f"Publicaciones:           "
        f"{listing_lifecycle.get('listing_count', 0)}"
    )

    print(
        f"Renovacion requerida:    "
        f"{listing_lifecycle.get('renew_required_count', 0)}"
    )

    for listing in (
        listing_lifecycle.get(
            "renew_required",
            [],
        )
        or []
    ):

        print(
            f"  {listing.get('name')}: "
            f"caduca en {listing.get('hours_to_expiry')} h "
            f"-> RENEW_MARKET_LISTING"
        )

    print()
    print(
        "-"
        * 100
    )

    print(
        "DECISION GLOBAL"
    )

    print(
        "-"
        * 100
    )

    print()

    print(
        f"Tipo:                    "
        f"{decision.get('type')}"
    )

    print(
        f"Prioridad:               "
        f"{decision.get('priority')}"
    )

    print(
        f"Accion:                  "
        f"{decision.get('action')}"
    )

    print(
        f"Ejecutable por V3:       "
        f"{'SI' if decision.get('executable') else 'NO'}"
    )

    print()
    print(
        decision.get(
            "reason"
        )
    )

    print()
    print(
        "-"
        * 100
    )

    print(
        "TOP PRIORIDADES"
    )

    print(
        "-"
        * 100
    )

    for (
        index,
        candidate,
    ) in enumerate(
        result.get(
            "candidates",
            [],
        )[
            :7
        ],
        start=
            1,
    ):

        print(
            f"{index}. "
            f"{candidate.get('type', ''):<28} "
            f"{candidate.get('priority', 0):>4} "
            f"{candidate.get('action')}"
        )

    print_lineup_field(
        lineup=
            lineup,

        jornada=
            state.get(
                "target_matchday"
            ),
    )

    print(
        "="
        * 100
    )


def print_execution_result(
    execution: dict,
) -> None:

    print()
    print(
        "-"
        * 100
    )

    print(
        "EJECUCION"
    )

    print(
        "-"
        * 100
    )

    print()

    print(
        f"Accion:                  "
        f"{execution.get('action')}"
    )

    print(
        f"Estado:                  "
        f"{execution.get('status')}"
    )

    print(
        f"Escritura realizada:     "
        f"{'SI' if execution.get('write_performed') else 'NO'}"
    )

    print(
        f"Exito:                   "
        f"{'SI' if execution.get('success') else 'NO'}"
    )

    if (
        execution.get(
            "http_status"
        )
        is not None
    ):

        print(
            f"HTTP:                    "
            f"{execution.get('http_status')}"
        )

    print()
    print(
        execution.get(
            "reason"
        )
    )

    print()
    print(
        "="
        * 100
    )


# ============================================================
# LINEUP BASELINE
# ============================================================


def ensure_lineup_baseline(
    result: dict,
) -> bool:
    """
    Crear baseline local no modifica Biwenger.
    """

    monitor = (
        result.get(
            "state",
            {},
        )
        .get(
            "lineup_monitor",
            {},
        )
        or {}
    )

    comparison = (
        monitor.get(
            "comparison",
            {},
        )
        or {}
    )

    lineup = (
        monitor.get(
            "lineup",
            {},
        )
        or {}
    )

    if (
        comparison.get(
            "baseline",
            False,
        )
        and
        len(
            lineup.get(
                "selected",
                [],
            )
        )
        == 11
    ):

        save_lineup_monitor_state(
            lineup
        )

        print()
        print(
            "Baseline local del Lineup Monitor creada."
        )

        return True

    return False


# ============================================================
# CICLO
# ============================================================


def run_cycle(
    live: bool = False,
    competitive_live: bool = False,
) -> dict:

    (
        snapshot_file,
        snapshot,
    ) = refresh_snapshot()

    print()
    print(
        "Pensando..."
    )

    started = (
        time.perf_counter()
    )

    result = (
        build_global_decision(
            snapshot
        )
    )

    competitive_observer = (
        build_competitive_observer(
            snapshot,
            temporal_gate=(
                result.get(
                    "temporal_gate",
                    {},
                )
                or {}
            ),
            current_balance=(
                result.get(
                    "balance",
                    0,
                )
            ),
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    print()
    print(
        f"Analisis completado en "
        f"{elapsed:.2f} segundos."
    )

    print_cycle_result(
        snapshot_file=
            snapshot_file,

        snapshot=
            snapshot,

        result=
            result,
    )

    print_competitive_observer(
        competitive_observer
    )

    append_competitive_log(
        snapshot_file=
            snapshot_file,

        observer=
            competitive_observer,
    )

    ensure_lineup_baseline(
        result
    )

    decision = (
        result[
            "decision"
        ]
    )

    execution = (
        execute_autopilot_decision(
            decision=
                decision,

            execute=
                live,
        )
    )

    competitive_execution = {
        "action":
            None,

        "status":
            "COMPETITIVE_LIVE_DISABLED",

        "reason":
            "Competitive LIVE requiere --live y --competitive-live.",

        "write_performed":
            False,

        "success":
            True,
    }

    # Regla global: nunca permitimos una segunda escritura en el ciclo.
    if (
        competitive_live
        and
        live
        and
        not execution.get(
            "write_performed",
            False,
        )
    ):

        selected_gate = (
            (
                competitive_observer.get(
                    "competitive_safety_gate",
                    {},
                )
                or {}
            ).get(
                "selected"
            )
        )

        selected_offer = None

        if selected_gate:

            selected_offer = next(
                (
                    item

                    for item
                    in (
                        competitive_observer.get(
                            "manager_offers",
                            [],
                        )
                        or []
                    )

                    if (
                        item.get(
                            "offer_id"
                        )
                        ==
                        selected_gate.get(
                            "offer_id"
                        )
                        and
                        item.get(
                            "player_id"
                        )
                        ==
                        selected_gate.get(
                            "player_id"
                        )
                    )
                ),
                None,
            )

        competitive_execution = (
            execute_competitive_live_action(
                selected_offer=
                    selected_offer,

                rival_intelligence=
                    (
                        competitive_observer.get(
                            "rival_intelligence",
                            {},
                        )
                        or {}
                    ),

                execute=
                    True,
            )
        )

    elif (
        competitive_live
        and
        live
        and
        execution.get(
            "write_performed",
            False,
        )
    ):

        competitive_execution = {
            "action":
                None,

            "status":
                "BLOCKED_LEGACY_ALREADY_WROTE",

            "reason":
                "Legacy ya realizo la unica escritura permitida del ciclo.",

            "write_performed":
                False,

            "success":
                True,
        }

    print_execution_result(
        execution
    )

    if competitive_live:

        print()
        print(
            "-"
            * 100
        )

        print(
            "COMPETITIVE V2.0 EXECUTION"
        )

        print(
            "-"
            * 100
        )

        print()

        print(
            f"Accion:                  "
            f"{competitive_execution.get('action') or 'NINGUNA'}"
        )

        print(
            f"Estado:                  "
            f"{competitive_execution.get('status')}"
        )

        print(
            f"Escritura realizada:     "
            f"{'SI' if competitive_execution.get('write_performed') else 'NO'}"
        )

        print(
            f"Exito:                   "
            f"{'SI' if competitive_execution.get('success') else 'NO'}"
        )

        print()

        print(
            competitive_execution.get(
                "reason"
            )
        )

    append_log(
        snapshot_file=
            snapshot_file,

        result=
            result,

        execution=
            execution,

        phase=
            "PRE_ACTION",
    )

    post_action = None

    write_happened = (
        (
            execution.get(
                "write_performed",
                False,
            )
            and
            execution.get(
                "success",
                False,
            )
        )
        or
        (
            competitive_execution.get(
                "write_performed",
                False,
            )
            and
            competitive_execution.get(
                "success",
                False,
            )
        )
    )

    if (
        live
        and
        write_happened
    ):

        print()
        print(
            "Una escritura real ha sido completada."
        )

        print(
            "Refrescando Biwenger antes de terminar "
            "el ciclo..."
        )

        (
            post_snapshot_file,
            post_snapshot,
        ) = refresh_snapshot()

        print()
        print(
            "Recalculando estado post-operacion..."
        )

        post_result = (
            build_global_decision(
                post_snapshot
            )
        )

        post_action = {
            "snapshot_file":
                post_snapshot_file,

            "snapshot":
                post_snapshot,

            "result":
                post_result,
        }

        print_cycle_result(
            snapshot_file=
                post_snapshot_file,

            snapshot=
                post_snapshot,

            result=
                post_result,
        )

        append_log(
            snapshot_file=
                post_snapshot_file,

            result=
                post_result,

            execution=
                execution,

            phase=
                "POST_ACTION",
        )

        print()
        print(
            "REGLA DE SEGURIDAD:"
        )

        print(
            "No se ejecutara una segunda escritura "
            "en este ciclo."
        )

    return {
        "snapshot_file":
            snapshot_file,

        "snapshot":
            snapshot,

        "result":
            result,

        "execution":
            execution,

        "post_action":
            post_action,

        "analysis_seconds":
            elapsed,

        "competitive_observer":
            competitive_observer,

        "competitive_execution":
            competitive_execution,
    }


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    parser = (
        argparse.ArgumentParser(
            description=
                "Autopilot V3 + Competitive Intelligence V2.0 CONTROLLED LIVE de Bordalas IA."
        )
    )

    parser.add_argument(
        "--once",
        action=
            "store_true",

        help=
            "Ejecuta un unico ciclo y termina.",
    )

    parser.add_argument(
        "--live",
        action=
            "store_true",

        help=(
            "Permite una unica escritura real por ciclo "
            "si la fase temporal y el Safety Gate "
            "lo autorizan."
        ),
    )

    parser.add_argument(
        "--competitive-live",
        action=
            "store_true",

        help=(
            "Segundo opt-in obligatorio para permitir "
            "escrituras Competitive V2.0. Requiere tambien --live."
        ),
    )

    parser.add_argument(
        "--interval-minutes",
        type=
            int,

        default=
            DEFAULT_INTERVAL_MINUTES,

        help=
            "Minutos entre ciclos. Por defecto: 30.",
    )

    args = (
        parser.parse_args()
    )

    if (
        args.competitive_live
        and
        not args.live
    ):

        parser.error(
            "--competitive-live requiere tambien --live."
        )

    interval_minutes = max(
        int(
            args.interval_minutes
        ),
        1,
    )

    print()
    print(
        "="
        * 100
    )

    print(
        "                     BORDALAS IA - AUTOPILOT V3 + COMPETITIVE V2.0 CONTROLLED LIVE"
    )

    print(
        "="
        * 100
    )

    print()

    if args.live:

        print(
            "MODO: LIVE CONTROLADO"
        )

        print(
            "Maximo: UNA escritura real por ciclo."
        )

        print(
            "Los locks temporales pueden bloquear "
            "cualquier escritura."
        )

        if args.competitive_live:

            print(
                "Competitive V2.0 LIVE: HABILITADO "
                "(doble opt-in confirmado)."
            )

        else:

            print(
                "Competitive V2.0 LIVE: DESHABILITADO. "
                "Falta --competitive-live."
            )

    else:

        print(
            "MODO: OBSERVACION"
        )

        print(
            "No se modificara Biwenger."
        )

    print()

    if args.once:

        print(
            "Modo: un ciclo."
        )

    else:

        print(
            f"Intervalo: "
            f"{interval_minutes} minutos."
        )

    print()

    while True:

        cycle_started = (
            datetime.now()
        )

        try:

            run_cycle(
                live=
                    args.live,

                competitive_live=
                    args.competitive_live,
            )

        except KeyboardInterrupt:

            print()
            print(
                "Autopilot detenido por usuario."
            )

            break

        except Exception as error:

            print()
            print(
                "="
                * 100
            )

            print(
                "ERROR EN CICLO"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

            print(
                "No se ejecutaran mas operaciones "
                "en este ciclo."
            )

            print(
                "="
                * 100
            )

        if args.once:
            break

        elapsed = (
            datetime.now()
            - cycle_started
        ).total_seconds()

        interval_seconds = (
            interval_minutes
            * 60
        )

        wait_seconds = max(
            interval_seconds
            - elapsed,
            60,
        )

        next_cycle = (
            datetime.now().timestamp()
            + wait_seconds
        )

        next_cycle_text = (
            datetime.fromtimestamp(
                next_cycle
            )
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        print()
        print(
            f"Proximo ciclo: "
            f"{next_cycle_text}"
        )

        print(
            "Ctrl+C para detener."
        )

        try:

            time.sleep(
                wait_seconds
            )

        except KeyboardInterrupt:

            print()
            print(
                "Autopilot detenido por usuario."
            )

            break


if __name__ == "__main__":
    main()
