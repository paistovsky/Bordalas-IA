from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.autopilot import run_cycle
from src.analysis.controlled_speculation_live import (
    build_controlled_run,
    print_result as print_controlled_buy,
)
from src.analysis.position_manager_shadow_v106 import (
    sync_current as sync_position_manager,
    print_board as print_position_manager,
)
from src.analysis.dynamic_counteroffer_repricing_v107 import (
    sync_current as sync_counter_repricing,
    print_board as print_counter_repricing,
)


STATUS_PATH = Path("data/trading/v10_production_status.json")
COUNTER_STATE_PATH = Path(
    "data/trading/counteroffer_repricing_state.json"
)

COUNTER_MIN_INTERVAL_SECONDS = 55 * 60


def write_attempt_used(cycle: dict) -> bool:
    """
    Regla global: una sola escritura/intentona por ciclo.
    Cuenta también un write fallido para no encadenar otra operación.
    """
    legacy = cycle.get("execution", {}) or {}
    competitive = cycle.get("competitive_execution", {}) or {}

    return bool(
        legacy.get("write_performed")
        or competitive.get("write_performed")
    )


def counter_repricing_due(
    path: Path = COUNTER_STATE_PATH,
    *,
    now: float | None = None,
) -> bool:
    if not path.exists():
        return True

    now = float(now if now is not None else time.time())

    try:
        age = now - path.stat().st_mtime
    except OSError:
        return True

    return age >= COUNTER_MIN_INTERVAL_SECONDS


def _error_payload(error: Exception) -> dict:
    return {
        "ok": False,
        "error": f"{type(error).__name__}: {error}",
    }


def run_v10_production_cycle() -> dict:
    print("\n" + "=" * 100)
    print("BORDALAS IA - V10.8 PRODUCTION CYCLE")
    print("=" * 100)

    # ---------------------------------------------------------
    # 1. LIVE existente + Competitive LIVE
    # ---------------------------------------------------------
    cycle = run_cycle(
        live=True,
        competitive_live=True,
    )

    write_used = write_attempt_used(cycle)

    # ---------------------------------------------------------
    # 2. BUY V10 LIVE solo si nadie escribió antes
    # ---------------------------------------------------------
    controlled_buy = {
        "status": "SKIPPED_WRITE_ALREADY_USED",
        "writes_biwenger": False,
        "reason": (
            "Legacy/Competitive ya consumió la única escritura "
            "permitida del ciclo."
        ),
    }

    if not write_used:
        try:
            controlled_buy = build_controlled_run(
                refresh=True,
                execute_live=True,
                live_confirmation="BORDALAS",
            )
            print_controlled_buy(controlled_buy)

            # Aunque la API falle, si se intentó enviar ya no permitimos
            # otra escritura en este ciclo.
            write_used = bool(
                controlled_buy.get("writes_biwenger")
            )
        except Exception as error:
            controlled_buy = {
                **_error_payload(error),
                "status": "CONTROLLED_BUY_EXCEPTION",
                "writes_biwenger": False,
            }

    # ---------------------------------------------------------
    # 3. Position Ledger + Manager automáticos en PROD.
    #    V10.6 sigue sin escritura propia.
    # ---------------------------------------------------------
    try:
        position_manager = sync_position_manager(
            refresh=True,
        )
        print_position_manager(
            position_manager.get("board", {}) or {}
        )
    except Exception as error:
        position_manager = _error_payload(error)

    # ---------------------------------------------------------
    # 4. Repricing automático aprox. cada hora.
    #    V10.7 sigue sin escritura propia.
    # ---------------------------------------------------------
    repricing_due = counter_repricing_due()

    if repricing_due:
        try:
            counter = sync_counter_repricing(
                refresh=True,
            )
            print_counter_repricing(
                counter.get("board", {}) or {}
            )
        except Exception as error:
            counter = _error_payload(error)
    else:
        counter = {
            "ok": True,
            "skipped": True,
            "reason": "Cadencia V10.7: todavía no han pasado ~55 minutos.",
            "writes_biwenger": False,
        }

    payload = {
        "version": "V10.8",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "production": True,
        "legacy_live": True,
        "competitive_live": True,
        "controlled_buy_live": True,
        "global_write_used": write_used,
        "controlled_buy": {
            "status": controlled_buy.get("status"),
            "writes_biwenger": bool(
                controlled_buy.get("writes_biwenger")
            ),
            "reason": controlled_buy.get("reason"),
        },
        "position_manager": {
            "ok": position_manager.get("ok", False),
            "writes_biwenger": bool(
                position_manager.get("writes_biwenger", False)
            ),
            "error": position_manager.get("error"),
        },
        "counter_repricing": {
            "ok": counter.get("ok", False),
            "skipped": counter.get("skipped", False),
            "writes_biwenger": bool(
                counter.get("writes_biwenger", False)
            ),
            "error": counter.get("error"),
        },
    }

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 100)
    print("V10.8 PRODUCTION SUMMARY")
    print("=" * 100)
    print(f"Legacy LIVE:                SI")
    print(f"Competitive LIVE:           SI")
    print(f"BUY V10 LIVE:               SI")
    print(f"Position Manager PROD:      SI (decision, cero writes V10.6)")
    print(f"Counter Repricing PROD:     SI (hourly, cero writes V10.7)")
    print(f"Write usado en ciclo:       {'SI' if write_used else 'NO'}")
    print("=" * 100)

    return payload


def main() -> None:
    run_v10_production_cycle()


if __name__ == "__main__":
    main()
