from __future__ import annotations

from src.analysis.decision_orchestrator import (
    build_global_decision,
)
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.market_trader_shadow import (
    build_market_trader_shadow,
)


def money(value) -> str:
    try:
        return f"{int(value or 0):,.0f} EUR"
    except (TypeError, ValueError):
        return "?"


def action_label(candidate: dict | None) -> str:
    if not candidate:
        return "NINGUNA"

    action = candidate.get("action", "?")
    priority = candidate.get("priority", 0)
    return f"{action} (prio {priority})"


def print_queue(title: str, queue: list[dict]) -> None:
    print()
    print(title)
    print("-" * 92)

    if not queue:
        print("  Sin acciones.")
        return

    for index, item in enumerate(queue[:8], start=1):
        player = ((item.get("data", {}) or {}).get("player", {}) or {})
        player_text = f" | {player.get('name')}" if player.get("name") else ""
        shadow = (
            " SHADOW"
            if item.get("shadow_executable") and not item.get("executable")
            else ""
        )
        print(
            f"  {index}. {item.get('action', '?'):<30} "
            f"prio={int(item.get('priority', 0) or 0):>4}"
            f"{shadow}{player_text}"
        )


def print_safe_debt_detail(forecast: dict) -> None:
    print()
    print("SAFE DEBT V10.2.2 - FAST PORTFOLIO VALIDADO CONTRA EL XI")
    print("-" * 92)
    print(
        "Liquidez bruta candidata:   "
        f"{money(forecast.get('gross_candidate_liquidity'))}"
    )
    print(
        "Tier A (sin tocar XI):       "
        f"{money(forecast.get('tier_a_liquidity'))}"
    )
    print(
        "Tier B (XI 11/11):           "
        f"{money(forecast.get('tier_b_liquidity'))}"
    )
    print(
        "Tier C (emergencia 10/11):   "
        f"{money(forecast.get('tier_c_liquidity'))}"
    )

    selected = forecast.get("selected_recovery_sources", []) or []
    print()
    print("Cartera A/B que respalda la deuda normal:")
    if not selected:
        print("  - Sin fuentes de recuperacion A/B.")
    else:
        for item in selected:
            names = ", ".join(item.get("player_names", []) or []) or "?"
            kind = item.get("kind", "?")
            print(
                f"  - {kind:<18} {names:<28} {money(item.get('amount'))}"
            )

    blocked = forecast.get("lineup_blocked_sources", []) or []
    if blocked:
        print()
        print("Fuentes excluidas de Safe Debt normal por XI:")
        for item in blocked[:8]:
            names = ", ".join(item.get("player_names", []) or []) or "?"
            print(
                f"  - {names:<28} {money(item.get('amount'))} "
                f"-> XI {item.get('playable_count', '?')}/11"
            )

    search = forecast.get("safe_portfolio_search", {}) or {}
    if search:
        print()
        print(
            "Validacion conjunta:          "
            f"{search.get('method')} | simulaciones={search.get('simulations', 0)}"
        )



def percent(value) -> str:
    try:
        return f"{float(value or 0):.1f}%"
    except (TypeError, ValueError):
        return "?"


def print_market_trader(trader: dict) -> None:
    capital = trader.get("capital", {}) or {}
    budget = trader.get("trading_budget", {}) or {}
    portfolio = capital.get("portfolio", {}) or {}
    trading_safe = portfolio.get("trading_safe", {}) or {}
    tier_b = portfolio.get("tier_b", {}) or {}
    tier_c = portfolio.get("tier_c", {}) or {}

    print()
    print("MARKET TRADER V10.3.1 - BID AUTHORITY + INTELLIGENT BID + SPORTING SAFE DEBT")
    print("-" * 92)
    print(
        "B1 trading-safe (<=5% XI): "
        f"{money(capital.get('trading_safe_recovery'))}"
    )
    print(
        "B1 perdida XI proyectada:  "
        f"{percent(trading_safe.get('lineup_score_loss_percent'))}"
    )
    print(
        "B2 completo emergencia:    "
        f"{money(tier_b.get('amount'))}"
    )
    print(
        "Tier C 10/11 emergencia:   "
        f"{money(tier_c.get('amount'))}"
    )
    print(
        "Capital sporting-safe:     "
        f"{money(budget.get('sporting_safe_capacity'))}"
    )
    print(
        "Presupuesto trading V10.3.1: "
        f"{money(budget.get('total_budget'))}"
    )
    print(
        "Limite por operacion:      "
        f"{money(budget.get('single_operation_limit'))}"
    )
    print(
        "Plan de compras:            "
        f"{trader.get('planned_positions', 0)} posiciones | "
        f"{money(trader.get('planned_spend'))}"
    )
    print(
        "T-15 tras plan shadow:      "
        f"{money(trader.get('projected_t15_after_plan'))}"
    )

    print()
    print("TOP OPORTUNIDADES DE TRADING")
    print("-" * 92)

    opportunities = trader.get("opportunities", []) or []
    if not opportunities:
        print("  Sin oportunidades BUY/WATCH en el mercado actual.")
        return

    for index, item in enumerate(opportunities[:8], start=1):
        print(
            f"{index:>2}. {str(item.get('name') or '?'):<24} "
            f"score={float(item.get('trading_score', 0) or 0):>5.1f} "
            f"spec={float(item.get('speculation_score', 0) or 0):>5.1f} "
            f"{str(item.get('decision') or '?'):<22}"
        )
        print(
            "    Valor " + money(item.get("price"))
            + " | Legacy " + money(item.get("legacy_intelligent_bid"))
            + " | Authority " + money(item.get("bid_authority_bid"))
            + " | Puja " + money(item.get("recommended_bid"))
            + " | Max racional " + money(item.get("max_rational_bid"))
        )
        print(
            "    Authority " + str(item.get("bid_authority_source") or "?")
            + " | confianza " + str(item.get("bid_authority_confidence") or "?")
            + " | prima " + percent(item.get("bid_authority_premium_percent"))
        )
        print(
            "    Salida esperada " + money(item.get("expected_exit_value"))
            + " | Beneficio " + money(item.get("expected_profit"))
            + " | ROI " + percent(item.get("expected_roi_percent"))
            + " | upside " + percent(item.get("expected_upside_percent"))
        )
        print(
            "    T-15 post " + money(item.get("projected_t15_after_buffer"))
            + " | " + str(item.get("decision_reason") or "")
        )


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    result = build_global_decision(snapshot)

    concern = result.get("decision") or {}
    live_action = result.get("action_decision")
    shadow_action = result.get("shadow_action_decision")

    state = result.get("state", {}) or {}
    forecast = state.get("t15_forecast", {}) or {}

    print()
    print("=" * 92)
    print("BORDALAS IA - MARKET BRAIN V10.3.1 - BID AUTHORITY SHADOW")
    print("=" * 92)
    print(f"Snapshot:                    {snapshot_file}")
    print("Escrituras Biwenger:         NO")
    print()
    print(f"Saldo actual:                {money(forecast.get('balance'))}")
    print(
        "Liquidez usable A/B:         "
        f"{money(forecast.get('guaranteed_recovery'))}"
    )
    print(
        "Saldo proyectado T-15:       "
        f"{money(forecast.get('projected_t15_balance'))}"
    )
    print(
        "T-15 tras buffer:            "
        f"{money(forecast.get('projected_t15_after_buffer'))}"
    )
    print(
        "Deuda segura adicional:      "
        f"{money(forecast.get('additional_debt_headroom'))}"
    )
    print(
        "Capital seguro desplegable:  "
        f"{money(forecast.get('safe_spend_capacity'))}"
    )
    print(
        "Nueva deuda permitida:       "
        f"{'SI' if forecast.get('can_increase_debt') else 'NO'}"
    )
    print(f"Fase:                        {forecast.get('phase')}")

    print_safe_debt_detail(forecast)

    trader = build_market_trader_shadow(
        snapshot,
        decision_result=result,
    )
    print_market_trader(trader)

    print()
    print("SEPARACION V10.1")
    print("-" * 92)
    print("Preocupacion principal:      " f"{action_label(concern)}")
    print("Primera accion LIVE actual:  " f"{action_label(live_action)}")
    print("Primera accion SHADOW V10:   " f"{action_label(shadow_action)}")

    print_queue(
        "COLA DE ACCIONES LIVE (NO se ejecuta desde este comando)",
        result.get("action_queue", []) or [],
    )
    print_queue(
        "COLA MARKET BRAIN SHADOW",
        result.get("shadow_action_queue", []) or [],
    )

    print()
    print("=" * 92)
    print(
        "SHADOW MODE: simula Market Trader + Bid Authority + Sporting Safe Debt; "
        "no envia compras, ventas ni cambios de XI a Biwenger."
    )
    print("=" * 92)


if __name__ == "__main__":
    main()
