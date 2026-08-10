from src.intelligence.jornada_perfecta_market_intelligence import (
    refresh_jp_market_intelligence,
)


def money(value) -> str:
    return f"{int(value or 0):,} EUR"


def pct(value) -> str:
    return f"{float(value or 0):+.2f}%"


def main() -> None:
    print()
    print("=" * 120)
    print("                 BORDALAS IA - JP MARKET INTELLIGENCE V1")
    print("=" * 120)
    print()

    payload = refresh_jp_market_intelligence(
        force_provider_refresh=False
    )

    players = payload["players"]

    print(f"Provider:                 {payload['provider_status']}")
    print(f"Jugadores:                {payload['player_count']}")
    print()

    print("## TOP JP MARKET SCORE")
    print()

    for player in players[:25]:
        daily = player["daily_returns_pct"]
        editorial = player.get("latest_relevant_editorial") or {}

        print(
            f"{str(player.get('name') or '?'):<23} "
            f"score={player['jp_market_score']:>5.1f} "
            f"market={player['market_score']:>5.1f} "
            f"1d={pct(daily.get('1')):>9} "
            f"3d={pct(daily.get('3')):>9} "
            f"tip={str(player.get('tip') or '-'):>16} "
            f"edit={player['editorial_score']:>5.1f} "
            f"{player['intelligence_action']}"
        )

        if editorial:
            print(
                f"{'':23} "
                f"EDITORIAL={editorial.get('editorial_type')} "
                f"age={editorial.get('effective_age_hours')}h "
                f"forecast={editorial.get('forecast')}"
            )

    print()
    print("## OUTLIERS DETECTADOS")
    print()

    outliers = [
        player
        for player in players
        if player.get("outlier")
    ]

    for player in outliers[:30]:
        print(
            f"{str(player.get('name') or '?'):<23} "
            f"precio={money(player.get('price')):>16} "
            f"5={money((player.get('last_markets') or {}).get('5')):>16} "
            f"10={money((player.get('last_markets') or {}).get('10')):>16} "
            f"30={money((player.get('last_markets') or {}).get('30')):>16} "
            f"{','.join(player.get('outlier_reasons') or [])}"
        )

    print()
    print("## CHOLLOS FRESCOS CON SCORE")
    print()

    fresh = []

    for player in players:
        editorial = player.get("latest_relevant_editorial") or {}

        if not editorial:
            continue

        age = editorial.get("effective_age_hours")

        if age is None or age > 24 * 14:
            continue

        fresh.append(player)

    fresh.sort(
        key=lambda player: player["jp_market_score"],
        reverse=True,
    )

    for player in fresh[:30]:
        editorial = player["latest_relevant_editorial"]

        print(
            f"{str(player.get('name') or '?'):<23} "
            f"score={player['jp_market_score']:>5.1f} "
            f"{editorial.get('editorial_type', '?'):<9} "
            f"age={editorial.get('effective_age_hours')}h "
            f"forecast={editorial.get('forecast')} "
            f"tip={player.get('tip')}"
        )

    print()
    print("## SANITY")
    print()

    if payload["player_count"] < 500:
        raise SystemExit("ERROR: intelligence incompleta.")

    remote_ids = {
        player.get("biwenger_remote_id")
        for player in players
        if player.get("biwenger_remote_id")
    }

    print(f"Remote IDs unicos:        {len(remote_ids)}")
    print(f"Outliers detectados:      {len(outliers)}")
    print(f"Editorial fresca <=14d:   {len(fresh)}")

    if len(remote_ids) < 500:
        raise SystemExit("ERROR: demasiados jugadores sin remote id.")

    scores = [
        player["jp_market_score"]
        for player in players
    ]

    if not scores or min(scores) < 0 or max(scores) > 100:
        raise SystemExit("ERROR: score fuera de rango.")

    print()
    print("JP MARKET INTELLIGENCE V1: OK")
    print("=" * 120)


if __name__ == "__main__":
    main()
