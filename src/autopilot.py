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
    players_with_live_bid,
)

from src.analysis.bid_exposure_engine import (
    build_bid_exposure,
)

from src.analysis.price_history_store import (
    describe_store,
    load_price_history_store,
    record_snapshot_prices,
    save_price_history_store,
)

from src.analysis.acquisition_board import (
    build_acquisition_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)

from src.analysis.action_failure_backoff import (
    candidate_target_id,
    load_backoff_state,
    record_action_result,
    save_backoff_state,
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

from src.intelligence.bid_outcome_ledger import (
    sync_bid_outcomes,
)

from src.intelligence.source_accuracy_ledger import (
    load_ledger,
    save_ledger,
    sync_ledger,
)

from src.analysis.negotiation_state_engine import (
    apply_observer_response,
    load_negotiation_state,
    save_negotiation_state,
)

from src.analysis.competitive_safety_gate import (
    select_single_competitive_action,
)

from src.analysis.market_clock import (
    build_market_clock,
    print_market_clock,
)

from src.analysis.position_guardrail import (
    print_position_guardrail,
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

            # Sin el cuerpo de la respuesta no se puede
            # diagnosticar un rechazo de Biwenger: un HTTP 400
            # a secas no dice nada.
            "response":
                (
                    str(
                        execution.get(
                            "response"
                        )
                    )[:1000]
                    if execution.get(
                        "response"
                    )
                    is not None
                    else None
                ),

            "player_id":
                execution.get(
                    "player_id"
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


# ============================================================
# INTELIGENCIA RIVAL COMPARTIDA
# ============================================================
#
# Se construia dentro de build_competitive_observer, que corre
# DESPUES de la decision. Por eso el orchestrator no podia usar
# el tablero de adquisicion -que la necesita- y acababa
# decidiendo con el scoring antiguo.
#
# Ahora se construye una vez, antes de decidir, y la reutilizan
# los dos. El tablon se pide una sola vez por ciclo: es una
# llamada de red y no hay motivo para hacerla dos veces.

_RIVAL_INTELLIGENCE_CACHE: dict = {}


def load_rival_intelligence(
    snapshot: dict,
) -> dict:
    """
    Retrato de la competencia, cacheado por ciclo.

    Nunca lanza: sin tablon devuelve un informe vacio y quien
    llame decide que hacer con el.
    """

    if "value" in _RIVAL_INTELLIGENCE_CACHE:
        return _RIVAL_INTELLIGENCE_CACHE["value"]

    vacio = {
        "available": False,
        "managers": [],
        "current_user_id": None,
        "reason": "No se pudo leer el tablon.",
    }

    try:
        board = collect_board_history()

        market_status = (
            (snapshot.get("market") or {}).get("status")
            or {}
        )

        current_user_id = board.get(
            "current_user_id"
        )

        inteligencia = build_rival_intelligence(
            events=board.get("events", []),
            users=board.get("users", []),
            profiles=board.get("profiles", []),
            catalog=snapshot.get("catalog", {}),
            current_user_id=current_user_id,
            own_finances=board.get("own_finances", {}),
            own_balance=market_status.get("balance"),
            own_maximum_bid=market_status.get("maximumBid"),
        )

        inteligencia["available"] = True
        inteligencia["current_user_id"] = current_user_id

    except Exception as error:
        inteligencia = {
            **vacio,
            "reason": (
                f"{type(error).__name__}: {error}"
            ),
        }

    _RIVAL_INTELLIGENCE_CACHE["value"] = inteligencia

    return inteligencia


def reset_rival_intelligence_cache() -> None:
    _RIVAL_INTELLIGENCE_CACHE.clear()


def refresh_starter_intelligence(
    snapshot: dict,
) -> dict:
    """
    Va a buscar el pronostico de titularidad ANTES de valorar.

    EL AGUJERO QUE TAPA

        Nadie lo hacia. `get_starter_lookup()` lee un fichero del
        disco, y el unico sitio que escribia ese fichero era un
        script de sombra que se lanza a mano. En produccion, la
        inteligencia de titularidad era lo que quedo escrito la
        ultima vez que alguien corrio un script.

        Por eso el tablero del 17/08 decia "0/20 CON PRONOSTICO":
        no es que la fuente fallase, es que nadie iba a buscarla.

    La cache del proveedor decide si toca bajar de verdad, asi que
    llamar aqui en cada ciclo no significa scrapear en cada ciclo.

    Blindado a proposito: un fallo del pronostico deja el tablero
    anterior en pie, pero jamas tumba un ciclo de produccion.
    """

    try:
        from src.analysis.calendar_state import (
            build_calendar_state,
        )

        from src.analysis.candidate_starter_lookup import (
            reset_starter_lookup_cache,
        )

        from src.intelligence.futbolfantasy_provider import (
            refresh_board,
        )

        from src.intelligence.jornada_perfecta_provider import (
            calculate_refresh_seconds,
        )

        calendario = build_calendar_state(snapshot) or {}

        jornada = int(
            calendario.get("target_matchday")
            or 1
        )

        tablero = refresh_board(
            snapshot,
            jornada,
            ttl_seconds=calculate_refresh_seconds(
                calendario.get("seconds_to_deadline")
            ),
        )

        # El lookup cachea por firma de fichero. Si el tablero se
        # ha reescrito en esta misma llamada, hay que soltar la
        # copia vieja antes de valorar.
        #
        # Y de paso se le dice contra que jornada tiene que
        # validar lo que lea del disco: aqui es donde se sabe.
        # `set_expected_matchday` suelta la cache por su cuenta.
        from src.analysis.candidate_starter_lookup import (
            set_expected_matchday,
        )

        set_expected_matchday(jornada)

        reset_starter_lookup_cache()

        meta = tablero.get("metadata") or {}

        return {
            "status": (tablero.get("cache") or {}).get("status"),
            "matchday": tablero.get("matchday"),
            "matched": meta.get("matched"),
            "targets": meta.get("targets"),
            "matched_market": meta.get("matched_market"),
            "targets_market": meta.get("targets_market"),
            "errors": meta.get("errors") or [],
            "error": (tablero.get("cache") or {}).get("error"),
        }

    except Exception as error:
        return {
            "status": "FAILED",
            "matched": None,
            "targets": None,
            "error": f"{type(error).__name__}: {error}",
        }


def build_cycle_acquisition_board(
    snapshot: dict,
) -> dict:
    """
    Lo que Bordalas quiere fichar hoy, con su cuenta hecha.

    Es EL MISMO tablero que pinta el dashboard. Ese era el
    problema: el dashboard lo enseñaba y el ciclo ejecutaba otra
    lista distinta.

    Nunca lanza. Si falla, devuelve no disponible y el
    orchestrator se queda con la ruta antigua en vez de dejar de
    operar.
    """

    # Primero el pronostico, despues la cuenta. Al reves se valora
    # con el dato de ayer.
    starter = refresh_starter_intelligence(snapshot)

    try:
        inteligencia = load_rival_intelligence(
            snapshot
        )

        solvency = build_solvency_state(
            snapshot
        )

        speculation = build_speculation_board(
            snapshot
        )

        presupuesto = (
            speculation.get("budget")
            or {}
        )

        disponible = presupuesto.get(
            "available_budget",
            presupuesto.get("total_budget"),
        )

        # EL DINERO DE FICHAR (21/08/2026)
        #
        # `presupuesto` es el de especular: 15 % de la caja y 60 %
        # del margen de deuda. Mejorar el once no es una apuesta y
        # tiene el suyo, con las mismas puertas y otra cantidad.
        # Si no llega se sigue con el viejo, como hasta hoy.
        fichajes = speculation.get("acquisition_budget") or {}

        para_fichar = (
            fichajes.get(
                "available_budget",
                fichajes.get("total_budget"),
            )
            if fichajes.get("enabled")
            else None
        )

        tablero = build_acquisition_board(
            snapshot=snapshot,
            rival_intelligence=inteligencia,
            current_user_id=inteligencia.get(
                "current_user_id"
            ),
            available_budget=disponible,
            acquisition_budget=para_fichar,
        )

        # Que se vea de donde salio el pronostico con el que se ha
        # valorado. Si un dia vuelve a haber "0 pujables", esto
        # dice en el acto si fue por falta de chollos o por falta
        # de dato.
        if isinstance(tablero, dict):
            tablero["starter_refresh"] = starter

        return tablero

    except Exception as error:
        return {
            "available": False,
            "targets": [],
            "starter_refresh": starter,
            "reason": (
                f"No se pudo construir el tablero de "
                f"adquisicion: {type(error).__name__}: {error}"
            ),
        }


def build_competitive_observer(
    snapshot: dict,
    temporal_gate: dict | None = None,
    current_balance: int | None = None,
    liquidity: dict | None = None,
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

        # Ya se construyo antes de decidir. Volver a pedir el
        # tablon seria una segunda llamada de red por el mismo
        # dato.
        compartida = load_rival_intelligence(
            snapshot
        )

        rival_intelligence = (
            compartida
            if compartida.get("available")
            else build_rival_intelligence(
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

        # Proteccion por jugador.
        #
        # competitive_safety_gate comprueba
        # offer["protection"] == "NEVER_AUTO_SELL", pero esa clave
        # nunca se rellenaba aqui: la palabra "protection" no
        # aparecia ni una vez en este fichero. BLOCK_PROTECTED_PLAYER
        # era, por tanto, una barrera inalcanzable.
        #
        # El dato ya existe: liquidity_manager lo calcula por
        # jugador y lo expone en el roster. Solo habia que traerlo.
        protection_lookup = {}

        for item in (
            (liquidity or {}).get(
                "roster",
                [],
            )
            or []
        ):
            try:
                protection_lookup[
                    int(item["id"])
                ] = str(
                    item.get(
                        "protection",
                        "",
                    )
                    or ""
                )

            except (KeyError, TypeError, ValueError):
                continue

        manager_offers = []

        updated_negotiation_state = (
            negotiation_state
        )

        # Transiciones que SOLO deben persistirse si de verdad
        # llegamos a escribir en Biwenger. Ver nota en el bloque
        # de should_respond, mas abajo.
        pending_negotiation_transitions = {}

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

                    "protection":
                        protection_lookup.get(
                            safe_int(
                                decision.get(
                                    "player_id"
                                )
                            ),
                            "",
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

                # apply_observer_response SIMULA el estado
                # posterior a responder: su propio docstring lo
                # dice. Antes esa simulacion se persistia sin mas,
                # y como los estados que escribe son terminales
                # (ACCEPT_NOW -> CLOSED, COUNTER_OFFER ->
                # WAITING_RIVAL) la oferta quedaba bloqueada para
                # siempre aunque no se hubiese escrito nada en
                # Biwenger. Bastaba un ciclo en observacion, o un
                # fallo HTTP, para perder la oferta.
                #
                # Ahora la simulacion se usa dentro del ciclo pero
                # la transicion queda EN ESPERA: solo se persiste
                # cuando la escritura se confirma.
                simulado = (
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

                updated_negotiation_state = simulado

                clave_negociacion = str(
                    negotiation.get(
                        "key"
                    )
                )

                entrada = (
                    (
                        simulado.get(
                            "negotiations",
                            {},
                        )
                        or {}
                    ).get(
                        clave_negociacion
                    )
                )

                if entrada is not None:

                    pending_negotiation_transitions[
                        clave_negociacion
                    ] = {
                        "entry":
                            entrada,

                        "offer_id":
                            decision.get(
                                "offer_id"
                            ),

                        "player_id":
                            decision.get(
                                "player_id"
                            ),
                    }


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

            "pending_negotiation_transitions":
                pending_negotiation_transitions,
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

    archive_prices(
        snapshot
    )

    return (
        snapshot_file,
        snapshot,
    )


def archive_prices(
    snapshot: dict,
) -> dict:
    """
    Guarda los precios de hoy en el historico compacto.

    Los snapshots completos se podan a 24 y con el ciclo cada 30
    minutos eso son 12 horas de memoria. Todo lo que Bordalas
    sabe del mercado -velocidad de cada jugador, curva de primas
    de los rivales, desgaste de la tendencia- se calcula
    comparando dias distintos, asi que sin archivo esos motores
    se degradan solos.

    Un fallo aqui no puede tumbar el ciclo: es archivo, no
    operativa.
    """

    try:
        store = load_price_history_store()

        resultado = record_snapshot_prices(
            snapshot,
            store=store,
        )

        save_price_history_store(
            resultado["store"]
        )

        estado = describe_store(
            resultado["store"]
        )

        print()
        print("-" * 70)
        print("HISTORICO DE PRECIOS")
        print("-" * 70)
        print(
            f"  Anotados hoy:            "
            f"{resultado['recorded']}"
        )
        print(
            f"  Sin cambio:              "
            f"{resultado['unchanged']}"
        )
        print(
            f"  Registros archivados:    "
            f"{estado.get('records', 0)}"
        )
        print(
            f"  Jugadores:               "
            f"{estado.get('players', 0)}"
        )
        print(
            f"  Historia acumulada:      "
            f"{estado.get('days', 0)} dias"
        )

        return estado

    except Exception as error:
        print(
            f"  Historico de precios no guardado: "
            f"{type(error).__name__}: {error}"
        )

        return {
            "available": False,
            "reason": f"{type(error).__name__}: {error}",
        }


# ============================================================
# OUTPUT
# ============================================================



def print_acquisition_board(
    board: dict,
    already_bid: set | None = None,
) -> None:
    """
    Lo mismo que enseña el dashboard, en la consola del ciclo.

    Si las dos listas no coinciden, se ve aqui antes que en una
    captura de pantalla.
    """

    print()
    print("-" * 70)
    print("OBJETIVOS DE FICHAJE")
    print("-" * 70)

    if not board or not board.get("available"):
        print(
            f"  No disponible: "
            f"{(board or {}).get('reason', 'sin motivo')}"
        )
        return

    objetivos = [
        item
        for item in (board.get("targets") or [])
        if item.get("decision") == "BID"
    ]

    print(
        f"  Valorados: {board.get('market_size', 0)}   "
        f"Pujables: {board.get('biddable', 0)}"
    )

    # Sin esto, "Pujables: 0" no distingue entre "hoy no hay
    # chollos" y "no llega el pronostico de titularidad y la
    # regla del once lo esta bloqueando todo". Son dos cosas muy
    # distintas y solo una hay que arreglarla.
    cobertura = board.get("starter_coverage") or {}

    if cobertura:

        con = int(cobertura.get("with_forecast") or 0)
        total = int(cobertura.get("total") or 0)
        bloqueados = int(
            cobertura.get("blocked_by_starter_rule") or 0
        )

        print(
            f"  Con pronostico de titular: {con}/{total}   "
            f"Bloqueados por la regla del once: {bloqueados}"
        )

        if total and con == 0:
            print(
                "  AVISO: ningun candidato tiene pronostico de "
                "titularidad."
            )
            print(
                "         Mientras siga asi no se mejora el once. "
                "Revisa el refresco de Jornada Perfecta."
            )

    if not objetivos:
        print("  Ninguno supera el filtro en este ciclo.")
        return

    # El marcador tiene que senalar al que se va a ejecutar de
    # verdad, no al primero de la lista. Los que ya tienen puja
    # nuestra viva se saltan.
    already_bid = already_bid or set()
    ejecutable_marcado = False

    for indice, objetivo in enumerate(objetivos, start=1):

        ya_pujado = (
            int(objetivo.get("id") or 0) in already_bid
        )

        if ya_pujado:
            marca = "(puja viva)"

        elif not ejecutable_marcado:
            marca = "-> EJECUTA"
            ejecutable_marcado = True

        else:
            marca = ""

        print(
            f"  {indice}. {str(objetivo.get('name'))[:22]:<24}"
            f"puja {int(objetivo.get('bid') or 0):>10,}   "
            f"gana {int((objetivo.get('win_probability') or 0) * 100):>3}%   "
            f"VE {int(objetivo.get('expected_value') or 0):>10,}   "
            f"{objetivo.get('intent') or ''} {marca}".replace(",", ".")
        )


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

    # De que motor salio el objetivo.
    #
    # Si aqui aparece SPECULATION_SCORING es que el tablero de
    # adquisicion ha fallado y hemos vuelto a la lista antigua.
    # La red de seguridad esta bien; enterarse tarde, no.
    if execution.get(
        "target_source"
    ):
        print(
            f"Objetivo elegido por:    "
            f"{execution.get('target_source')}"
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
    La libreta se escribe DESPUES de escribir en Biwenger.

    EL CASO (20/08/2026)

        Esta funcion guardaba el XI recomendado en
        `data/lineup_monitor/state.json` la primera vez que
        corria, "para tener una linea base". Nunca lo enviaba a
        Biwenger.

        A partir de ahi la recomendacion coincidia con la libreta,
        el monitor decia KEEP_LINEUP y no se escribia jamas. El
        dueño se encontro un 5-3-2 en el dashboard, un 4-3-3 en
        Biwenger y un 11/11 en verde diciendo que todo estaba
        bien.

        Una libreta que se adelanta a la realidad es peor que no
        tener libreta: convierte "no lo he hecho" en "ya estaba
        hecho".

    QUE HACE AHORA

        Nada. El estado lo guarda `autopilot_executor` justo
        despues de que Biwenger confirme la escritura, que es el
        unico momento en el que es verdad.

        Se conserva la funcion -y su hueco en el ciclo- para no
        mover el orquestador: devuelve False siempre.
    """

    return False


def _ensure_lineup_baseline_LEGACY(
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


def select_live_decision(
    result: dict,
) -> dict:
    """
    La decision global describe la preocupacion principal y puede ser solo
    informativa. action_decision es la primera accion LIVE ejecutable.

    Conservamos el fallback para resultados antiguos, pero produccion debe
    ejecutar action_decision cuando exista.
    """
    action_decision = result.get(
        "action_decision"
    )

    if action_decision:
        return action_decision

    return result[
        "decision"
    ]


def register_action_outcome(
    decision: dict,
    execution: dict,
) -> dict:
    """
    Recuerda si la escritura funciono.

    Una accion que falla en Biwenger ciclo tras ciclo no puede
    seguir siendo la primera de la cola: bloquea todo lo demas.
    Aqui se guarda el fallo para que el siguiente ciclo la
    aparte temporalmente.

    Solo cuentan los intentos de escritura reales. Un DRY_RUN
    no ha tocado nada y no se castiga.
    """

    if not execution:
        return {
            "recorded": False,
            "reason": "No hay resultado de ejecucion.",
        }

    if not execution.get(
        "write_performed",
        False,
    ):
        return {
            "recorded": False,
            "reason": (
                "Sin escritura real: no hay nada que "
                "registrar."
            ),
        }

    action = (
        execution.get(
            "action"
        )
        or decision.get(
            "action"
        )
    )

    target_id = (
        candidate_target_id(
            decision
        )
    )

    if target_id is None:
        target_id = execution.get(
            "player_id"
        )

    try:
        state = load_backoff_state()

        state = record_action_result(
            state,

            action=
                action,

            target_id=
                target_id,

            success=
                bool(
                    execution.get(
                        "success",
                        False,
                    )
                ),

            write_performed=
                True,

            status=
                execution.get(
                    "status"
                ),

            http_status=
                execution.get(
                    "http_status"
                ),

            reason=
                execution.get(
                    "reason"
                ),
        )

        save_backoff_state(
            state
        )

    except OSError as error:

        return {
            "recorded": False,
            "reason": (
                f"No se pudo guardar el estado de backoff: "
                f"{type(error).__name__}: {error}"
            ),
        }

    return {
        "recorded": True,
        "action": action,
        "target_id": target_id,
        "success": bool(
            execution.get(
                "success",
                False,
            )
        ),
    }


def confirm_negotiation_transitions(
    competitive_observer: dict,
    competitive_execution: dict,
) -> dict:
    """
    Persiste la transicion de negociacion SOLO de la oferta que
    de verdad se escribio en Biwenger.

    El observador ya no guarda nada: deja las transiciones en
    espera. Si la escritura no ocurre -ciclo en observacion, gate
    que bloquea, fallo HTTP- el estado no avanza y la oferta
    sigue disponible en el siguiente ciclo.
    """

    pendientes = (
        competitive_observer.get(
            "pending_negotiation_transitions",
            {},
        )
        or {}
    )

    if not pendientes:
        return {
            "persisted": False,
            "reason": "No hay transiciones en espera.",
        }

    escribio = bool(
        competitive_execution.get(
            "write_performed",
            False,
        )
    )

    ok = bool(
        competitive_execution.get(
            "success",
            False,
        )
    )

    if not (escribio and ok):
        return {
            "persisted": False,
            "reason": (
                "Sin escritura confirmada: el estado de "
                "negociacion no avanza."
            ),
        }

    offer_id = (
        competitive_execution.get(
            "offer_id"
        )
        or
        (
            competitive_execution.get(
                "selected_offer",
                {},
            )
            or {}
        ).get(
            "offer_id"
        )
    )

    claves = [
        clave
        for clave, dato in pendientes.items()
        if offer_id is not None
        and dato.get("offer_id") == offer_id
    ]

    if not claves:
        return {
            "persisted": False,
            "reason": (
                f"La escritura confirmada (oferta {offer_id}) no "
                f"corresponde a ninguna transicion en espera."
            ),
        }

    estado = (
        load_negotiation_state()
    )

    negociaciones = estado.setdefault(
        "negotiations",
        {},
    )

    for clave in claves:
        negociaciones[clave] = (
            pendientes[clave]["entry"]
        )

    save_negotiation_state(
        estado
    )

    return {
        "persisted": True,
        "keys": claves,
        "offer_id": offer_id,
        "reason": (
            "Escritura confirmada: estado de negociacion "
            "avanzado solo para esa oferta."
        ),
    }



def sync_press(
    snapshot: dict,
) -> dict:
    """
    El ojeador de PRENSA: lo unico que no copia el precio.

    POR QUE DOS VECES AL DIA Y NO CUARENTA Y OCHO

        El ciclo corre cada media hora y las noticias no cambian
        cada media hora. TTL de doce horas: si el informe de
        disco vale, no se sale a la calle.

    QUE APORTA QUE NO APORTEN LAS OTRAS

        Las tres webs de mercado dan la misma medida repetida
        -cero discrepancias en 288 jugadores el 06/09-. La prensa
        trae partes medicos, convocatorias y declaraciones de
        entrenador, que todavia no estan en ningun precio.

    FASE OBSERVADOR: no influye en ninguna decision.

    Blindado: un fallo del ojeador jamas puede detener un ciclo.
    """

    try:
        from src.intelligence.scout.accuracy import (
            sync_scout_accuracy,
        )
        from src.intelligence.scout.press import (
            as_accuracy_report,
            refresh_press,
        )

        informe = refresh_press(snapshot.get("catalog") or {})

        precios = {
            str(player_id): (ficha or {}).get("price")
            for player_id, ficha in (
                (snapshot.get("catalog") or {})
                .get("data", {})
                .get("players")
                or {}
            ).items()
            if isinstance(ficha, dict)
        }

        # El MISMO libro que las webs de precio. Un libro aparte
        # para la prensa seria una segunda forma de contar los
        # aciertos, y con dos formas siempre gana la que mejor
        # queda.
        acierto = sync_scout_accuracy(
            as_accuracy_report(informe),
            precios,
        )

        return {
            "status": (informe.get("cache") or {}).get("status"),
            "headlines": informe.get("headlines"),
            "players": informe.get("players_mentioned"),
            "with_signal": informe.get("players_with_signal"),
            "unmatched": informe.get("unmatched_total"),
            "accuracy_recorded": acierto.get("recorded_total"),
            "error": (informe.get("cache") or {}).get("error"),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "status": "ERROR",
            "error": f"{type(error).__name__}: {error}",
        }


def sync_scout(
    snapshot: dict,
    cycle_state: dict | None = None,
) -> dict:
    """
    El ojeador de mercado: que dicen las webs de cada jugador.

    POR QUE NO SALE EN CADA CICLO

        El ciclo corre 48 veces al dia y las noticias de mercado
        no cambian cada cuarto de hora. El informe se refresca por
        TTL de seis horas, y ademas se fuerza cuando el que hay en
        disco es de antes del reset de las 07:00: un informe de
        las 06:50 habla del mercado de ayer aunque solo tenga
        veinte minutos.

        Si esta fresco, se lee del disco y no se toca la red.

    FASE OBSERVADOR: no influye en ninguna decision.

    Blindado a proposito, igual que `sync_source_accuracy`: un
    fallo del ojeador jamas puede detener un ciclo de produccion.
    """

    try:
        from src.intelligence.scout.accuracy import (
            sync_scout_accuracy,
        )
        from src.intelligence.scout.divergence import sync_divergence
        from src.intelligence.scout.report import refresh_report

        jornada = (cycle_state or {}).get("target_matchday")

        informe = refresh_report(
            snapshot.get("catalog") or {},
            matchday=jornada,
        )

        # Los precios de HOY, que son la unica verdad contra la
        # que se puede puntuar lo que dijeron ayer.
        precios = {
            str(player_id): (ficha or {}).get("price")
            for player_id, ficha in (
                (snapshot.get("catalog") or {})
                .get("data", {})
                .get("players")
                or {}
            ).items()
            if isinstance(ficha, dict)
        }

        acierto = sync_scout_accuracy(informe, precios)

        # EL LIBRO DE LA DIVERGENCIA (07/09/2026)
        #
        # Precio contra demanda. Se apunta la foto de hoy -los
        # divergentes Y el grupo de control- y se cierra lo que
        # cumple 3 y 7 dias.
        #
        # No hay historico de demanda porque las fuentes publican
        # la de hoy y no una serie: por eso hay que empezar a
        # guardarla.
        divergencia = sync_divergence(informe, precios)

        return {
            "status": (informe.get("cache") or {}).get("status"),
            "players": informe.get("players_count"),
            "unmatched": informe.get("unmatched_count"),
            "sources_ok": informe.get("sources_ok"),
            "sources_total": informe.get("sources_total"),
            "accuracy_recorded": acierto.get("recorded_total"),
            "accuracy_decided": acierto.get("decided_total"),
            "divergent_today": divergencia.get("divergent_total"),
            "divergence_recorded": divergencia.get("recorded_total"),
            "divergence_closed": divergencia.get("closed_total"),
            "error": (informe.get("cache") or {}).get("error"),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "status": "FAILED",
            "players": None,
            "error": f"{type(error).__name__}: {error}",
        }


def sync_source_accuracy(
    cycle_state: dict,
) -> dict:
    """
    Alimenta el libro de acierto por fuente.

    starter_multisource_v1124.json se reescribe en cada ciclo:
    sin esta llamada las predicciones de una jornada se pierden
    en cuanto empieza a calcularse la siguiente, y no habria con
    que puntuar a las fuentes.

    FASE OBSERVADOR: no influye en ninguna decision.

    Blindado a proposito: un fallo del libro jamas puede detener
    un ciclo de produccion.
    """

    try:
        from src.intelligence.multisource_starter_v1124 import (
            OUTPUT_FILE,
        )

        if not OUTPUT_FILE.exists():
            return {
                "recorded": None,
                "scored": [],
                "error": "Sin tablero multifuente todavia.",
            }

        with open(
            OUTPUT_FILE,
            encoding="utf-8",
        ) as fichero:
            board = json.load(fichero)

        matchday = (
            cycle_state.get(
                "target_matchday"
            )
            or board.get(
                "matchday"
            )
        )

        if matchday is None:
            return {
                "recorded": None,
                "scored": [],
                "error": "Jornada objetivo desconocida.",
            }

        resultado = sync_ledger(
            board=board,
            snapshot=cycle_state.get(
                "_snapshot",
                {},
            ),
            current_matchday=int(matchday),
            ledger=load_ledger(),
        )

        save_ledger(
            resultado["ledger"]
        )

        return resultado["summary"]

    except Exception as error:
        return {
            "recorded": None,
            "scored": [],
            "error": (
                f"{type(error).__name__}: {error}"
            ),
        }


def run_cycle(
    live: bool = False,
    competitive_live: bool = False,
) -> dict:

    (
        snapshot_file,
        snapshot,
    ) = refresh_snapshot()

    # El reloj del mercado va antes del analisis porque condiciona
    # todo lo que venga detras: si el reset ya paso, las pujas de
    # este ciclo no se ejecutan hasta el siguiente, y lo que no
    # este publicado no recibira oferta del Computer.
    #
    # Aislado en try/except: es informacion, no puede tumbar un
    # ciclo.
    try:
        market_clock = build_market_clock(snapshot)

    except Exception as clock_error:
        market_clock = {
            "available": False,
            "window_state": "UNKNOWN",
            "reason": (
                f"{type(clock_error).__name__}: {clock_error}"
            ),
        }

    print_market_clock(market_clock)

    print()
    print(
        "Pensando..."
    )

    started = (
        time.perf_counter()
    )

    # Cada ciclo parte de cero: en --loop el proceso no muere
    # entre vueltas y el tablon cambia.
    reset_rival_intelligence_cache()

    # El tablero de adquisicion es el que pinta el dashboard.
    # Pasarselo al orchestrator es lo que hace que lo que se ve
    # sea lo que se ejecuta.
    acquisition_board = (
        build_cycle_acquisition_board(
            snapshot
        )
    )

    print_acquisition_board(
        acquisition_board,
        already_bid=players_with_live_bid(
            {
                "bid_exposure": build_bid_exposure(
                    snapshot
                )
            }
        ),
    )

    result = (
        build_global_decision(
            snapshot,
            acquisition_board=
                acquisition_board,
        )
    )

    # build_global_decision() devuelve temporal_gate y balance
    # DENTRO de result["state"], no en el nivel superior.
    #
    # Leerlos de result directamente daba siempre {} y 0, con lo
    # que operations_locked era siempre False y el bloqueo
    # BLOCK_TEMPORAL_LOCK del safety gate competitivo resultaba
    # inalcanzable: con la jornada bloqueada la ruta competitiva
    # podia llegar a escribir en Biwenger.
    cycle_state = (
        result.get(
            "state",
            {},
        )
        or {}
    )

    # Se cuelga del estado para que lo vean los motores que
    # decidan sobre el, y el dashboard cuando toque.
    cycle_state["market_clock"] = market_clock

    if isinstance(result, dict):
        result.setdefault("state", cycle_state)
        result["state"]["market_clock"] = market_clock

    # Estado posicional de la plantilla. Sale del mismo roster que
    # ya calcula liquidity_manager, asi que aqui solo se muestra.
    try:
        print_position_guardrail(
            (
                cycle_state.get("liquidity", {})
                or {}
            ).get("position_guardrail")
        )

    except Exception:
        pass

    # ----------------------------------------------------------
    # A QUIEN SOLTARIA PEPE SI NADIE LE OBLIGASE
    #
    # OBSERVACION PURA. No publica, no vende, no toca Biwenger.
    #
    # Hasta hoy Pepe solo proponia ventas cuando faltaba caja, asi
    # que un jugador podia deshacerse solo -Reserva, o roto hasta
    # enero- y nadie decia nada mientras la caja aguantase.
    #
    # Esto lo dice. Ejecutarlo es otra decision, y del dueño.
    # ----------------------------------------------------------
    try:
        from src.analysis.sale_intent import (
            build_sale_intent,
            describe_sale_intent,
        )

        intencion_venta = build_sale_intent(snapshot)

        print()
        print("-" * 70)
        print("INTENCION DE VENTA (OBSERVACION)")
        print("-" * 70)

        for linea in describe_sale_intent(intencion_venta):
            print(linea)

        if isinstance(result, dict):
            result["state"]["sale_intent"] = intencion_venta

    except Exception as error:
        print(
            f"  Intencion de venta no disponible: "
            f"{type(error).__name__}: {error}"
        )

    competitive_observer = (
        build_competitive_observer(
            snapshot,
            temporal_gate=(
                cycle_state.get(
                    "temporal_gate",
                    {},
                )
                or {}
            ),
            current_balance=(
                cycle_state.get(
                    "balance",
                    0,
                )
            ),
            liquidity=(
                cycle_state.get(
                    "liquidity",
                    {},
                )
                or {}
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
        select_live_decision(
            result
        )
    )

    execution = (
        execute_autopilot_decision(
            decision=
                decision,

            execute=
                live,
        )
    )

    register_action_outcome(
        decision=
            decision,

        execution=
            execution,
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

    source_accuracy = (
        sync_source_accuracy(
            {
                **cycle_state,
                "_snapshot": snapshot,
            }
        )
    )

    if source_accuracy.get("scored"):
        print()
        print(
            f"Libro de fuentes: puntuadas las jornadas "
            f"{source_accuracy['scored']}."
        )

    # EL OJEADOR (06/09/2026)
    #
    # Sale a la calle como mucho cada seis horas. Aqui solo se
    # le pregunta; si el informe esta fresco, ni toca la red.
    ojeador = sync_scout(snapshot, cycle_state)

    # LA PRENSA (05/09/2026). Dos veces al dia, por TTL.
    prensa = sync_press(snapshot)

    if ojeador.get("players"):
        print()
        print(
            f"Ojeador: {ojeador['players']} jugadores con señal de "
            f"{ojeador.get('sources_ok')} de "
            f"{ojeador.get('sources_total')} fuentes "
            f"({ojeador.get('status')}), "
            f"{ojeador.get('unmatched')} sin emparejar."
        )

        if ojeador.get("divergent_today") is not None:
            print(
                f"Divergencia: {ojeador['divergent_today']} jugadores "
                f"con el precio y la demanda en contra "
                f"({ojeador.get('divergence_closed')} cerradas de "
                f"{ojeador.get('divergence_recorded')} apuntadas)."
            )

    elif ojeador.get("error"):
        print()
        print(f"Ojeador: no disponible ({ojeador['error']}).")

    if prensa.get("headlines"):
        print(
            f"Prensa: {prensa['headlines']} titulares, "
            f"{prensa.get('with_signal')} jugadores con señal de "
            f"{prensa.get('players')} mencionados "
            f"({prensa.get('status')})."
        )

    elif prensa.get("error"):
        print(f"Prensa: no disponible ({prensa['error']}).")

    # El libro de pujas se cierra aqui, en la misma fase que el de
    # fuentes: post-ejecucion, leyendo el tablon ya persistido en vez
    # de volver a pedirlo por red.
    bid_outcomes = sync_bid_outcomes(
        (
            (
                snapshot.get("league")
                or {}
            ).get("user")
            or {}
        ).get("id")
    )

    if bid_outcomes.get("lost_with_margin"):
        print()
        print(
            f"Libro de pujas: {bid_outcomes['won']} ganadas y "
            f"{bid_outcomes['lost']} perdidas; nos ganan por "
            f"{bid_outcomes['median_lost_margin']:,} de mediana."
            .replace(",", ".")
        )

    negotiation_persistence = (
        confirm_negotiation_transitions(
            competitive_observer,
            competitive_execution,
        )
    )

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

        "market_clock":
            market_clock,

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
