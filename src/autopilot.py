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


DEFAULT_INTERVAL_MINUTES = 30

LOG_DIRECTORY = (
    Path("data")
    / "autopilot"
)

LOG_FILE = (
    LOG_DIRECTORY
    / "autopilot_log.jsonl"
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
        "                       BORDALAS IA - AUTOPILOT V3"
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
        f"Fuente alineacion:       "
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

    print_execution_result(
        execution
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

    if (
        live
        and
        execution.get(
            "write_performed",
            False,
        )
        and
        execution.get(
            "success",
            False,
        )
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
    }


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    parser = (
        argparse.ArgumentParser(
            description=
                "Autopilot v3 de Bordalas IA."
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
        "                     BORDALAS IA - AUTOPILOT V3"
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
                    args.live
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
