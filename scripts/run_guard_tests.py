"""Ejecuta las guardias del ciclo en UN solo proceso de Python.

Antes, el workflow lanzaba 34 procesos independientes: cada uno arrancaba
un interprete nuevo y reimportaba el paquete entero. Eran 3-4,5 minutos
por ciclo, 48 veces al dia.

Aqui se importa una vez y se ejecutan los 34 seguidos. Cada modulo corre
con run_name="__main__", asi que se comporta exactamente igual que
`python -m modulo`: no hay que tocar ni un test.

Falla cerrado: si una guardia salta, este script termina en != 0 y el
ciclo de produccion no llega a ejecutarse, igual que antes.
"""

from __future__ import annotations

import runpy
import sys
import time
import traceback

# Mismo orden exacto que tenia bordalas-live.yml.
MODULES = [
    # Ciclo de produccion optimizado.
    "src.analysis.test_jp_profile_scope_v114",
    "src.analysis.test_multisource_starter_v1124",
    "src.analysis.test_v10_full_autonomous_live",
    "src.analysis.test_live_solvency_authority_v115",
    "src.telemetry.test_dashboard_execution_v121",
    # Candados de la auditoria del 15/08/2026.
    "src.analysis.test_solvency_deadlock_v1",
    "src.analysis.test_write_path_guards_v1",
    "src.analysis.test_negotiation_persistence_v1",
    "src.analysis.test_bid_deduplication_v1",
    "src.analysis.test_source_accuracy_v1",
    "src.analysis.test_write_verification_v1",
    "src.analysis.test_protection_gate_v1",
    "src.analysis.test_reroll_memory_v1",
    "src.analysis.test_ledger_dedup_v1",
    "src.analysis.test_market_clock_v1",
    "src.analysis.test_position_guardrail_v1",
    "src.analysis.test_speculation_budget_v1",
    "src.analysis.test_bid_exposure_v1",
    "src.analysis.test_bid_targets_v1",
    "src.analysis.test_external_name_safety_v1",
    "src.analysis.test_portfolio_budget_v1",
    "src.analysis.test_roster_plan_guardrail_v1",
    "src.analysis.test_rival_bid_model_v1",
    "src.analysis.test_player_value_v1",
    "src.analysis.test_acquisition_wiring_v1",
    "src.analysis.test_bid_visibility_v1",
    "src.analysis.test_dashboard_truth_v1",
    "src.analysis.test_intocables_v1",
    "src.analysis.test_calendario_v1",
    "src.analysis.test_cobrar_ofertas_v1",
    "src.analysis.test_action_starvation_v1",
    "src.analysis.test_price_history_store_v1",
    "src.analysis.test_futbolfantasy_source_v12",
    "src.analysis.test_starter_aware_xi_v1",
]


def run_one(module: str) -> tuple[bool, float, str]:
    """Ejecuta un modulo como __main__. Devuelve (ok, segundos, motivo)."""
    started = time.monotonic()
    try:
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit as exc:
        # Un test que termina con sys.exit(0) ha pasado; con otro codigo, no.
        code = exc.code
        if code in (None, 0):
            return True, time.monotonic() - started, ""
        return False, time.monotonic() - started, f"sys.exit({code!r})"
    except BaseException:  # noqa: BLE001 - queremos capturarlo todo y seguir informando
        traceback.print_exc()
        return False, time.monotonic() - started, "excepcion"
    return True, time.monotonic() - started, ""


def main() -> int:
    total = len(MODULES)
    failures: list[tuple[str, str]] = []
    started = time.monotonic()

    for index, module in enumerate(MODULES, start=1):
        print(f"\n[{index:02d}/{total}] {module}", flush=True)
        ok, elapsed, reason = run_one(module)
        mark = "OK  " if ok else "FALLA"
        print(f"    {mark} {elapsed:6.2f}s", flush=True)
        if not ok:
            failures.append((module, reason))

    elapsed = time.monotonic() - started
    print("\n" + "=" * 48)
    print(f" GUARDIAS: {total - len(failures)}/{total} en {elapsed:.1f}s")
    print("=" * 48)

    if failures:
        print("\nHan saltado estas guardias:")
        for module, reason in failures:
            suffix = f" ({reason})" if reason else ""
            print(f"  - {module}{suffix}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
