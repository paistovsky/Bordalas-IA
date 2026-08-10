from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


def money(value) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)
    board = build_speculation_board(snapshot)

    jp = board["jp_market_intelligence"]
    budget = board["budget"]
    solvency = board["solvency"]

    print()
    print("=" * 120)
    print("                   BORDALAS IA - SPECULATION ENGINE V4 + JP INTELLIGENCE")
    print("=" * 120)
    print()

    print(f"Snapshot:                    {snapshot_file}")
    print(f"Saldo:                       {money(solvency['balance'])}")
    print(f"JP provider:                 {jp.get('provider_status')}")
    print(f"JP age:                      {jp.get('age_hours')} h")
    print(f"JP jugadores:                {jp.get('players')}")
    print(f"JP lookup:                   {jp.get('lookup_size')}")
    print(f"JP matches strategic board:  {jp.get('matched_strategic_players')}/{len(board['players'])}")

    print()
    print("## PRESUPUESTO")
    print(f"Modo:                        {budget.get('mode')}")
    print(f"Habilitado:                  {'SI' if budget.get('enabled') else 'NO'}")
    print(f"Budget total:                {money(budget.get('total_budget'))}")
    print(f"Limite una operacion:        {money(budget.get('single_operation_limit'))}")
    print(f"Bloqueado por:               {budget.get('blocked_by') or 'NINGUNO'}")

    print()
    print("## TOP MERCADO REAL + JP")
    print()

    market_players = [
        player
        for player in board["buy_candidates"]
        if player.get("ownership_state") == "EN_MERCADO"
    ][:20]

    if not market_players:
        print("NINGUNO")
    else:
        for player in market_players:
            ext = player.get("external_signal") or {}

            print(
                f"{str(player.get('name') or '?'):<23} "
                f"spec={player.get('speculation_score', 0):>5.1f} "
                f"JP={str(ext.get('jp_market_score')):>6} "
                f"adj={float(ext.get('score', 0) or 0):>+6.1f} "
                f"inc={money(player.get('price_increment')):>14} "
                f"precio={money(player.get('price')):>15} "
                f"{player.get('speculation_action')}"
            )

            editorial = ext.get("jp_editorial") or {}
            if editorial:
                print(
                    f"{'':23} "
                    f"JP {editorial.get('editorial_type')} "
                    f"age={editorial.get('effective_age_hours')}h "
                    f"forecast={editorial.get('forecast')}"
                )

    print()
    print("## TOP JP EN NUESTRO MERCADO")
    print()

    current_market = [
        player
        for player in board["players"]
        if player.get("ownership_state") == "EN_MERCADO"
        and (player.get("external_signal") or {}).get("status") == "CONNECTED"
    ]

    current_market.sort(
        key=lambda player: (
            (player.get("external_signal") or {}).get("jp_market_score")
            or 0
        ),
        reverse=True,
    )

    for player in current_market[:20]:
        ext = player["external_signal"]

        print(
            f"{str(player.get('name') or '?'):<23} "
            f"JP={ext.get('jp_market_score'):>5.1f} "
            f"spec={player.get('speculation_score', 0):>5.1f} "
            f"tip={str(ext.get('jp_tip') or '-'):>16} "
            f"{ext.get('jp_action')}"
        )

    print()
    print("## EXECUTABLE BUYS")

    if not board["executable_buys"]:
        print("NINGUNA")
    else:
        for player in board["executable_buys"]:
            print(
                f"{player.get('name'):<23} "
                f"{money(player.get('price'))} "
                f"spec={player.get('speculation_score')} "
                f"JP={(player.get('external_signal') or {}).get('jp_market_score')}"
            )

    print()
    print("## SAFETY")

    if jp.get("lookup_size", 0) < 500:
        raise SystemExit("ERROR: JP lookup incompleto.")

    if jp.get("matched_strategic_players", 0) < 300:
        raise SystemExit(
            "ERROR: el cruce JP/Biwenger parece demasiado bajo."
        )

    if (
        solvency["balance"] < 0
        and budget.get("enabled")
        and not solvency.get("solvency_guarantee", {}).get("guaranteed")
    ):
        raise SystemExit(
            "ERROR: especulacion con deuda sin garantia T-15."
        )

    print("SPECULATION V4 + JP: OK")
    print("=" * 120)


if __name__ == "__main__":
    main()
