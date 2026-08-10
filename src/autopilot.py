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


def money(value) -> str:
    if value is None:
        return "DESCONOCIDO"
    return f"{value:,.0f} EUR"


def format_hours(value) -> str:
    if value is None:
        return "DESCONOCIDO"
    if value < 1:
        return f"{int(value * 60)}m"
    if value < 48:
        return f"{value:.1f}h"

    days = int(value // 24)
    remaining_hours = int(value % 24)
    return f"{days}d {remaining_hours}h"


def get_round_id(snapshot: dict):
    competition = snapshot.get("competition", {}) or {}
    round_data = competition.get("round")

    if isinstance(round_data, dict):
        for key in ("id", "round"):
            if round_data.get(key) is not None:
                return round_data[key]

    if round_data is not None:
        return round_data

    for key in ("round", "round_id", "current_round"):
        value = snapshot.get(key)
        if value is not None:
            return value

    return None


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

    decision = result["decision"]
    state = result["state"]
    franchise = state.get("franchise", {}) or {}
    target = franchise.get("target") or {}
    lineup_state = state.get("lineup", {}) or {}
    lineup_monitor = state.get("lineup_monitor", {}) or {}
    liquidity = state.get("liquidity", {}) or {}
    recovery = liquidity.get("recovery", {}) or {}

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "phase": phase,
        "snapshot": snapshot_file,
        "balance": state.get("balance"),
        "hours_to_deadline": state.get("hours_to_deadline"),
        "lineup_risk": state.get("lineup_risk"),
        "lineup_pressure": state.get("lineup_pressure_score"),
        "lineup_playable": lineup_state.get("playable_count"),
        "lineup_missing": lineup_state.get("missing"),
        "lineup_monitor_action": lineup_monitor.get("action"),
        "lineup_external_source": lineup_monitor.get("external_lineup_source"),
        "hard_safety": (
            state.get("hard_safety", {}).get("active", False)
        ),
        "franchise_state": franchise.get("state"),
        "franchise_target": target.get("name"),
        "liquidity_listed": liquidity.get("listing_count"),
        "liquidity_to_list": liquidity.get("to_list_count"),
        "incoming_offer_count": liquidity.get("incoming_offer_count"),
        "recovery_needed": recovery.get("needed"),
        "recovery_possible": recovery.get("possible"),
        "recovery_deficit": recovery.get("deficit"),
        "decision_type": decision.get("type"),
        "decision_priority": decision.get("priority"),
        "decision_action": decision.get("action"),
        "decision_executable": decision.get("executable"),
        "decision_reason": decision.get("reason"),
    }

    if execution is not None:
        record["execution"] = {
            "action": execution.get("action"),
            "status": execution.get("status"),
            "write_performed": execution.get("write_performed"),
            "success": execution.get("success"),
            "http_status": execution.get("http_status"),
            "reason": execution.get("reason"),
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
        file.write("\n")


def refresh_snapshot() -> tuple[str, dict]:
    print()
    print("Actualizando Biwenger...")
    print()

    collect_league_snapshot()

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    return snapshot_file, snapshot


def print_cycle_result(
    snapshot_file: str,
    snapshot: dict,
    result: dict,
) -> None:
    decision = result["decision"]
    state = result["state"]
    franchise = state.get("franchise", {}) or {}
    lineup_state = state.get("lineup", {}) or {}
    lineup = lineup_state.get("lineup", {}) or {}
    lineup_monitor = state.get("lineup_monitor", {}) or {}
    liquidity = state.get("liquidity", {}) or {}
    recovery = liquidity.get("recovery", {}) or {}
    speculation = state.get("speculation", {}) or {}
    budget = speculation.get("budget", {}) or {}
    target = franchise.get("target")

    print()
    print("=" * 100)
    print("                       BORDALAS IA - AUTOPILOT V2")
    print("=" * 100)
    print()

    print(f"Hora:                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Snapshot:                {snapshot_file}")
    print()
    print(f"Saldo:                   {money(state.get('balance'))}")
    print(f"Deadline:                {format_hours(state.get('hours_to_deadline'))}")
    print(f"Riesgo XI:               {state.get('lineup_risk')}")
    print(f"Presion XI:              {state.get('lineup_pressure_score')}/100")
    print(f"XI con partido:          {lineup_state.get('playable_count', 0)}/11")
    print(f"Huecos:                  {lineup_state.get('missing', 0)}")
    print(f"Lineup Monitor:          {lineup_monitor.get('action')}")
    print(f"Fuente alineacion:       {lineup_monitor.get('external_lineup_source')}")
    print(
        f"Hard Safety:             "
        f"{'SI' if state.get('hard_safety', {}).get('active') else 'NO'}"
    )
    print()
    print(
        f"Publicados liquidez:     "
        f"{liquidity.get('listing_count', 0)}/"
        f"{len(liquidity.get('roster', []))}"
    )
    print(f"Pendientes publicar:     {liquidity.get('to_list_count', 0)}")
    print(f"Ofertas de liquidez:     {liquidity.get('incoming_offer_count', 0)}")

    if recovery.get("needed"):
        print(f"Deficit recuperacion:    {money(recovery.get('deficit'))}")
        print(
            f"Plan financiable:        "
            f"{'SI' if recovery.get('possible') else 'NO'}"
        )

    print()
    print(f"Franchise state:         {franchise.get('state')}")
    if target:
        print(f"Franchise target:        {target.get('name')}")

    print()
    print(
        f"Speculation:             "
        f"{'ACTIVA' if budget.get('enabled') else 'BLOQUEADA'}"
    )
    if not budget.get("enabled"):
        print(f"Bloqueada por:           {budget.get('blocked_by')}")

    print()
    print("-" * 100)
    print("DECISION GLOBAL")
    print("-" * 100)
    print()
    print(f"Tipo:                    {decision.get('type')}")
    print(f"Prioridad:               {decision.get('priority')}")
    print(f"Accion:                  {decision.get('action')}")
    print(
        f"Ejecutable por V2:       "
        f"{'SI' if decision.get('executable') else 'NO'}"
    )
    print()
    print(decision.get("reason"))

    print()
    print("-" * 100)
    print("TOP PRIORIDADES")
    print("-" * 100)

    for index, candidate in enumerate(
        result.get("candidates", [])[:7],
        start=1,
    ):
        print(
            f"{index}. "
            f"{candidate.get('type', ''):<24} "
            f"{candidate.get('priority', 0):>4} "
            f"{candidate.get('action')}"
        )

    jornada = get_round_id(snapshot)
    print_lineup_field(
        lineup=lineup,
        jornada=jornada,
    )
    print("=" * 100)


def print_execution_result(execution: dict) -> None:
    print()
    print("-" * 100)
    print("EJECUCION")
    print("-" * 100)
    print()
    print(f"Accion:                  {execution.get('action')}")
    print(f"Estado:                  {execution.get('status')}")
    print(
        f"Escritura realizada:     "
        f"{'SI' if execution.get('write_performed') else 'NO'}"
    )
    print(f"Exito:                   {'SI' if execution.get('success') else 'NO'}")

    if execution.get("http_status") is not None:
        print(f"HTTP:                    {execution.get('http_status')}")

    print()
    print(execution.get("reason"))
    print()
    print("=" * 100)


def ensure_lineup_baseline(result: dict) -> bool:
    """Crear baseline local no modifica Biwenger."""

    monitor = (
        result.get("state", {}).get("lineup_monitor", {})
        or {}
    )
    comparison = monitor.get("comparison", {}) or {}
    lineup = monitor.get("lineup", {}) or {}

    if (
        comparison.get("baseline", False)
        and len(lineup.get("selected", [])) == 11
    ):
        save_lineup_monitor_state(lineup)
        print()
        print("Baseline local del Lineup Monitor creada.")
        return True

    return False


def run_cycle(live: bool = False) -> dict:
    snapshot_file, snapshot = refresh_snapshot()

    print()
    print("Pensando...")

    started = time.perf_counter()
    result = build_global_decision(snapshot)
    elapsed = time.perf_counter() - started

    print()
    print(f"Analisis completado en {elapsed:.2f} segundos.")

    print_cycle_result(
        snapshot_file=snapshot_file,
        snapshot=snapshot,
        result=result,
    )

    ensure_lineup_baseline(result)

    decision = result["decision"]
    execution = execute_autopilot_decision(
        decision=decision,
        execute=live,
    )

    print_execution_result(execution)

    append_log(
        snapshot_file=snapshot_file,
        result=result,
        execution=execution,
        phase="PRE_ACTION",
    )

    post_action = None

    if (
        live
        and execution.get("write_performed", False)
        and execution.get("success", False)
    ):
        print()
        print("Una escritura real ha sido completada.")
        print("Refrescando Biwenger antes de terminar el ciclo...")

        post_snapshot_file, post_snapshot = refresh_snapshot()

        print()
        print("Recalculando estado post-operacion...")

        post_result = build_global_decision(post_snapshot)

        post_action = {
            "snapshot_file": post_snapshot_file,
            "snapshot": post_snapshot,
            "result": post_result,
        }

        print_cycle_result(
            snapshot_file=post_snapshot_file,
            snapshot=post_snapshot,
            result=post_result,
        )

        append_log(
            snapshot_file=post_snapshot_file,
            result=post_result,
            execution=execution,
            phase="POST_ACTION",
        )

        print()
        print("REGLA DE SEGURIDAD:")
        print("No se ejecutara una segunda escritura en este ciclo.")

    return {
        "snapshot_file": snapshot_file,
        "snapshot": snapshot,
        "result": result,
        "execution": execution,
        "post_action": post_action,
        "analysis_seconds": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Autopilot v2 de Bordalas IA."
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta un unico ciclo y termina.",
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Permite una unica escritura real por ciclo "
            "para las acciones soportadas."
        ),
    )

    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        help="Minutos entre ciclos. Por defecto: 30.",
    )

    args = parser.parse_args()
    interval_minutes = max(int(args.interval_minutes), 1)

    print()
    print("=" * 100)
    print("                     BORDALAS IA - AUTOPILOT V2")
    print("=" * 100)
    print()

    if args.live:
        print("MODO: LIVE CONTROLADO")
        print("Maximo: UNA escritura real por ciclo.")
    else:
        print("MODO: OBSERVACION")
        print("No se modificara Biwenger.")

    print()

    if args.once:
        print("Modo: un ciclo.")
    else:
        print(f"Intervalo: {interval_minutes} minutos.")

    print()

    while True:
        cycle_started = datetime.now()

        try:
            run_cycle(live=args.live)

        except KeyboardInterrupt:
            print()
            print("Autopilot detenido por usuario.")
            break

        except Exception as error:
            print()
            print("=" * 100)
            print("ERROR EN CICLO")
            print(f"{type(error).__name__}: {error}")
            print("No se ejecutaran mas operaciones en este ciclo.")
            print("=" * 100)

        if args.once:
            break

        elapsed = (
            datetime.now()
            - cycle_started
        ).total_seconds()

        interval_seconds = interval_minutes * 60
        wait_seconds = max(interval_seconds - elapsed, 60)

        next_cycle = datetime.now().timestamp() + wait_seconds
        next_cycle_text = datetime.fromtimestamp(next_cycle).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        print()
        print(f"Proximo ciclo: {next_cycle_text}")
        print("Ctrl+C para detener.")

        try:
            time.sleep(wait_seconds)

        except KeyboardInterrupt:
            print()
            print("Autopilot detenido por usuario.")
            break


if __name__ == "__main__":
    main()
