from __future__ import annotations

import argparse
from typing import Any

from src.actions.live_bid_executor import execute_bid
from src.analysis.controlled_speculation_repricing import build_fresh_bid_reprice
from src.analysis.decision_orchestrator import build_global_decision
from src.analysis.intelligent_bid_engine import build_market_seller_lookup
from src.analysis.market_analyzer import get_latest_snapshot, load_snapshot
from src.analysis.market_trader_shadow import build_market_trader_shadow
from src.collectors.league_collector import collect_league_snapshot
from src.analysis.position_ledger_v105 import (
    record_verified_bid,
    sync_position_ledger_snapshot,
)


MIN_LIVE_SPECULATION_SCORE = 85.0
MIN_LIVE_TRADING_SCORE = 70.0
MIN_LIVE_EXPECTED_ROI_PERCENT = 15.0
LIVE_CONFIRM_TOKEN = "BORDALAS"

BLOCKED_PHASES = {
    "HARD_SAFETY",
    "ROUND_LOCKED",
    "ROUND_TRANSITION_LOCK",
    "FINALIZATION",
}


def classify_live_execution(execution: dict) -> tuple[str, str]:
    sent = bool(execution.get("sent"))
    success = bool(execution.get("success"))
    verified = bool(execution.get("offer_detected_after"))
    http_status = execution.get("http_status")
    api_response = execution.get("api_response")

    if not sent:
        return "LIVE_BID_NOT_SENT", "No se envio la puja."

    if not success:
        return (
            "LIVE_BID_REJECTED",
            f"Biwenger rechazo la puja (HTTP {http_status}). Respuesta: {api_response!r}",
        )

    if verified:
        return (
            "LIVE_BID_SENT_AND_VERIFIED",
            "Puja LIVE enviada y detectada en el mercado tras la escritura.",
        )

    return (
        "LIVE_BID_SENT_VERIFY_WARNING",
        "Biwenger acepto la peticion HTTP, pero la verificacion posterior no encontro la oferta.",
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def _money(value: Any) -> str:
    return f"{_safe_int(value):,} EUR"


def evaluate_controlled_live_gate(
    trader: dict,
    *,
    requested_player_id: int | None = None,
) -> dict:
    capital = trader.get("capital", {}) or {}
    opportunities = trader.get("opportunities", []) or []

    eligible = []
    rejected = []

    for item in opportunities:
        player_id = _safe_int(item.get("id"))
        if requested_player_id is not None and player_id != int(requested_player_id):
            continue

        reasons = []
        decision = str(item.get("decision") or "")
        spec = _safe_float(item.get("speculation_score"))
        trading = _safe_float(item.get("trading_score"))
        roi = _safe_float(item.get("expected_roi_percent"))
        bid = _safe_int(item.get("recommended_bid"))
        price = _safe_int(item.get("price"))
        max_rational = _safe_int(item.get("max_rational_bid"))
        t15 = _safe_int(item.get("projected_t15_after_buffer"))

        if decision != "BUY_SHADOW":
            reasons.append(f"market_trader={decision or 'UNKNOWN'}")
        if spec < MIN_LIVE_SPECULATION_SCORE:
            reasons.append(f"spec<{MIN_LIVE_SPECULATION_SCORE:.0f}")
        if trading < MIN_LIVE_TRADING_SCORE:
            reasons.append(f"trading<{MIN_LIVE_TRADING_SCORE:.0f}")
        if roi < MIN_LIVE_EXPECTED_ROI_PERCENT:
            reasons.append(f"roi<{MIN_LIVE_EXPECTED_ROI_PERCENT:.0f}%")
        if not bool(item.get("bid_authority_allowed", False)):
            reasons.append("bid_authority_block")
        if bid <= 0:
            reasons.append("invalid_bid")
        if max_rational <= 0 or bid > max_rational:
            reasons.append("bid_above_max_rational")
        if price <= 0 or max_rational < price:
            reasons.append("no_price_edge")
        if t15 < 0:
            reasons.append("t15_below_buffer")

        phase = str(capital.get("phase") or "UNKNOWN")
        if bool(capital.get("operations_locked", False)):
            reasons.append("operations_locked")
        if bool(capital.get("hard_safety_active", False)):
            reasons.append("hard_safety")
        if phase in BLOCKED_PHASES:
            reasons.append(f"phase={phase}")
        if _safe_int(capital.get("balance")) < 0 and not bool(
            capital.get("can_use_temporary_debt", False)
        ):
            reasons.append("negative_balance_without_safe_debt")

        result = {
            **item,
            "live_gate_reasons": reasons,
            "live_gate_passed": not reasons,
        }
        (rejected if reasons else eligible).append(result)

    eligible.sort(
        key=lambda item: (
            _safe_float(item.get("trading_score")),
            _safe_float(item.get("expected_roi_percent")),
            _safe_float(item.get("speculation_score")),
        ),
        reverse=True,
    )

    selected = eligible[0] if eligible else None
    return {
        "version": "V10.5",
        "selected": selected,
        "eligible": eligible,
        "rejected": rejected,
        "ready": selected is not None,
        "thresholds": {
            "min_speculation_score": MIN_LIVE_SPECULATION_SCORE,
            "min_trading_score": MIN_LIVE_TRADING_SCORE,
            "min_expected_roi_percent": MIN_LIVE_EXPECTED_ROI_PERCENT,
        },
        "status": "LIVE_CHECK_CANDIDATE" if selected else "NO_LIVE_CANDIDATE",
    }


def build_controlled_run(
    *,
    refresh: bool = True,
    execute_live: bool = False,
    live_confirmation: str | None = None,
) -> dict:
    """
    V10.4B pipeline:
      SNAPSHOT -> TRADER -> LIVE GATE -> DIRECT FRESH READ
      -> FRESH REPRICE -> REVALIDATE -> optional WRITE.

    Default and shadow mode contain zero writes. LIVE additionally requires the
    exact confirmation token BORDALAS.
    """
    if refresh:
        collect_league_snapshot()

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)
    decision_result = build_global_decision(snapshot)
    trader = build_market_trader_shadow(snapshot, decision_result=decision_result)

    try:
        ledger_sync = sync_position_ledger_snapshot(
            snapshot,
            trader,
        )
    except Exception as error:
        ledger_sync = {
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
        }

    gate = evaluate_controlled_live_gate(trader)

    result = {
        "version": "V10.5",
        "mode": "CONTROLLED_LIVE" if execute_live else "SHADOW_LIVE_CHECK",
        "writes_biwenger": False,
        "snapshot_file": snapshot_file,
        "trader": trader,
        "gate": gate,
        "preflight": None,
        "fresh_reprice": None,
        "execution": None,
        "ledger_sync": ledger_sync,
        "ledger_record": None,
        "ready": False,
        "status": gate.get("status"),
        "reason": "No hay candidato que supere todos los gates BUY; Position Ledger sigue reconciliado.",
    }

    selected = gate.get("selected") or {}
    if not selected:
        return result

    player_id = _safe_int(selected.get("id"))
    initial_bid = _safe_int(selected.get("recommended_bid"))
    seller_lookup = build_market_seller_lookup(snapshot)
    seller_user_id = (seller_lookup.get(player_id, {}) or {}).get("seller_user_id")

    try:
        # First direct fresh read. execute=False guarantees zero write.
        preflight = execute_bid(
            player_id=player_id,
            amount=initial_bid,
            expected_seller_id=seller_user_id,
            execute=False,
        )
    except Exception as error:
        result["status"] = "DIRECT_MARKET_PREFLIGHT_BLOCK"
        result["reason"] = f"Preflight Biwenger bloqueado: {type(error).__name__}: {error}"
        return result

    result["preflight"] = preflight
    capital = trader.get("capital", {}) or {}
    fresh = build_fresh_bid_reprice(
        selected,
        preflight,
        capital,
        min_roi_percent=MIN_LIVE_EXPECTED_ROI_PERCENT,
    )
    result["fresh_reprice"] = fresh

    if preflight.get("sent"):
        result["status"] = "UNEXPECTED_SHADOW_WRITE_BLOCK"
        result["reason"] = "El preflight reporto una escritura inesperada."
        return result

    if not fresh.get("allowed"):
        result["status"] = "FRESH_REPRICE_BLOCK"
        result["reason"] = str(fresh.get("reason"))
        return result

    result["ready"] = True

    if not execute_live:
        result["status"] = "LIVE_CHECK_PASSED_REPRICED"
        result["reason"] = (
            "READ -> REPRICE -> REVALIDATE completado. NO se ha enviado ninguna puja."
        )
        return result

    if str(live_confirmation or "").strip().upper() != LIVE_CONFIRM_TOKEN:
        result["ready"] = False
        result["status"] = "LIVE_CONFIRMATION_REQUIRED"
        result["reason"] = (
            "LIVE bloqueado: requiere --confirm-live BORDALAS. No se ha enviado ninguna puja."
        )
        return result

    final_bid = _safe_int(fresh.get("fresh_recommended_bid"))

    try:
        # execute_bid performs ANOTHER direct get_market before the write and
        # aborts if seller, listing floor, maximumBid or duplicate offer changed.
        execution = execute_bid(
            player_id=player_id,
            amount=final_bid,
            expected_seller_id=seller_user_id,
            execute=True,
        )
    except Exception as error:
        result["ready"] = False
        result["status"] = "FINAL_READ_BEFORE_WRITE_BLOCK"
        result["reason"] = f"La segunda lectura LIVE aborto la puja: {type(error).__name__}: {error}"
        return result

    result["execution"] = execution
    result["writes_biwenger"] = bool(execution.get("sent"))

    result["status"], result["reason"] = classify_live_execution(execution)

    if result["status"] == "LIVE_BID_SENT_AND_VERIFIED":
        try:
            result["ledger_record"] = record_verified_bid(result)
        except Exception as error:
            result["ledger_record"] = {
                "registered": False,
                "error": f"{type(error).__name__}: {error}",
            }

    return result


def print_result(result: dict) -> None:
    print("\n" + "=" * 92)
    print("BORDALAS IA - V10.5 POSITION LEDGER + CONTROLLED LIVE")
    print("=" * 92)
    print(f"Modo:                        {result.get('mode')}")
    print(f"Snapshot:                    {result.get('snapshot_file')}")
    print(f"Escrituras Biwenger:         {'SI' if result.get('writes_biwenger') else 'NO'}")

    trader = result.get("trader", {}) or {}
    capital = trader.get("capital", {}) or {}
    budget = trader.get("trading_budget", {}) or {}
    portfolio = capital.get("portfolio", {}) or {}

    print(f"Saldo actual:                {_money(capital.get('balance'))}")
    print(f"B1 trading-safe:             {_money(portfolio.get('trading_safe_total'))}")
    print(f"Capital sporting-safe:       {_money(capital.get('sporting_safe_spend_capacity'))}")
    print(f"Presupuesto trading:         {_money(budget.get('total_budget'))}")
    print(f"Fase:                        {capital.get('phase')}")

    gate = result.get("gate", {}) or {}
    selected = gate.get("selected") or {}
    print("\nGATE INICIAL")
    print("-" * 92)
    if selected:
        print(f"Candidato:                   {selected.get('name')}")
        print(f"Speculation score:           {_safe_float(selected.get('speculation_score')):.1f}")
        print(f"Trading score:               {_safe_float(selected.get('trading_score')):.1f}")
        print(f"ROI inicial:                 {_safe_float(selected.get('expected_roi_percent')):.1f}%")
        print(f"Valor jugador:               {_money(selected.get('price'))}")
        print(f"Puja inicial V10:            {_money(selected.get('recommended_bid'))}")
        print(f"Max racional:                {_money(selected.get('max_rational_bid'))}")
    else:
        print("Candidato:                   NINGUNO")

    preflight = result.get("preflight") or {}
    print("\nREAD FRESCO")
    print("-" * 92)
    if preflight:
        print(f"Listing manager fresco:      {_money(preflight.get('current_price'))}")
        print(f"Minimo Biwenger fresco:      {_money(preflight.get('minimum_bid'))}")
        print(f"Suelo efectivo entrada:      {_money(preflight.get('effective_bid_floor'))}")
        print(f"MaximumBid fresco:           {_money(preflight.get('maximum_bid'))}")
        print(f"Vendedor:                    {preflight.get('seller')}")
        print(f"Seller ID fresco:            {preflight.get('seller_id')}")
        preview = preflight.get("preview", {}) or {}
        print(f"Endpoint BID:                {preview.get('url')}")
        print(f"Payload BID:                 {preview.get('json')}")
        print(f"Oferta previa detectada:     {'SI' if preflight.get('existing_offer') else 'NO'}")
    else:
        print("Lectura directa:             NO EJECUTADA / BLOQUEADA")

    fresh = result.get("fresh_reprice") or {}
    print("\nREPRICE + REVALIDATE")
    print("-" * 92)
    if fresh:
        print(f"Puja inicial:                {_money(fresh.get('old_planned_bid'))}")
        print(f"Valor snapshot:              {_money(fresh.get('snapshot_player_value'))}")
        print(f"Minimo Biwenger fresco:      {_money(fresh.get('fresh_biwenger_minimum_bid'))}")
        print(f"Listing fresco:              {_money(fresh.get('fresh_listing_price'))}")
        print(f"Suelo efectivo entrada:      {_money(fresh.get('effective_entry_floor'))}")
        print(f"Prima Authority:             {_safe_float(fresh.get('authority_premium_percent')):.1f}%")
        print(f"Authority sobre suelo fresco:{_money(fresh.get('fresh_authority_bid'))}")
        print(f"Puja FRESCA:                 {_money(fresh.get('fresh_recommended_bid'))}")
        print(f"Max racional:                {_money(fresh.get('max_rational_bid'))}")
        print(f"Salida esperada:             {_money(fresh.get('expected_exit_value'))}")
        print(f"Beneficio fresco:            {_money(fresh.get('fresh_expected_profit'))}")
        print(f"ROI fresco:                  {_safe_float(fresh.get('fresh_expected_roi_percent')):.1f}%")
        print(f"T-15 fresco:                 {_money(fresh.get('fresh_projected_t15_after_buffer'))}")
        print(f"Reprice:                     {fresh.get('bid_change'):+,} EUR")
        print(f"Revalidacion:                {'PASS' if fresh.get('allowed') else 'BLOCK'}")
    else:
        print("Reprice:                     NO EJECUTADO")

    execution = result.get("execution") or {}
    if execution:
        print("\nWRITE LIVE")
        print("-" * 92)
        print(f"Importe enviado:             {_money(execution.get('amount'))}")
        print(f"HTTP status:                 {execution.get('http_status')}")
        print(f"API success:                 {execution.get('success')}")
        print(f"API response:                {execution.get('api_response')}")
        print(f"Oferta detectada despues:    {execution.get('offer_detected_after')}")

    ledger_sync = result.get("ledger_sync") or {}
    ledger_record = result.get("ledger_record") or {}

    print("\nPOSITION LEDGER V10.5")
    print("-" * 92)
    if ledger_sync.get("ok"):
        summary = ledger_sync.get("summary", {}) or {}
        bootstrap = ledger_sync.get("bootstrap", {}) or {}
        print(f"Sync ledger:                 OK")
        print(f"Ofertas activas adoptadas:   {bootstrap.get('created', 0)}")
        print(f"Posiciones registradas:      {summary.get('total_positions', 0)}")
        print(f"Estados:                     {summary.get('counts', {})}")
    else:
        print(f"Sync ledger:                 WARNING | {ledger_sync.get('error')}")

    if ledger_record:
        print(
            f"Registro nueva puja:          "
            f"{'OK' if ledger_record.get('registered') else 'WARNING'}"
        )
        if ledger_record.get("position_id"):
            print(f"Position ID:                 {ledger_record.get('position_id')}")

    print("\nRESULTADO")
    print("-" * 92)
    print(f"Estado:                      {result.get('status')}")
    print(f"Motivo:                      {result.get('reason')}")

    if result.get("ready") and selected and fresh and not result.get("writes_biwenger"):
        print("\n>>> WOULD BID AFTER FRESH REPRICE (NO ENVIADA)")
        print(f">>> {selected.get('name')} | {_money(fresh.get('fresh_recommended_bid'))}")

    print("=" * 92)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--shadow-live-check",
        action="store_true",
        help="Default seguro: READ -> REPRICE -> REVALIDATE, cero escrituras.",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Permite una unica puja si TODOS los gates pasan.",
    )
    parser.add_argument(
        "--confirm-live",
        default=None,
        help="Para LIVE debe ser exactamente BORDALAS.",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Solo depuracion: usa el ultimo snapshot local.",
    )
    args = parser.parse_args()

    result = build_controlled_run(
        refresh=not args.no_refresh,
        execute_live=bool(args.live),
        live_confirmation=args.confirm_live,
    )
    print_result(result)


if __name__ == "__main__":
    main()
