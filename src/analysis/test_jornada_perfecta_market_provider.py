from src.intelligence.jornada_perfecta_market_provider import (
    refresh_jornada_perfecta_market_data,
)


def money(value) -> str:
    return f"{int(value or 0):,.0f} EUR"


def main() -> None:
    print()
    print("=" * 110)
    print("                 BORDALAS IA - JORNADA PERFECTA MARKET PROVIDER")
    print("=" * 110)
    print()

    result = refresh_jornada_perfecta_market_data(
        force=True
    )

    data = result["data"]
    metadata = data["metadata"]

    print(
        f"Estado:                   {result['status']}"
    )
    print(
        f"Archivo:                  {result['file']}"
    )
    print(
        f"Jugadores mercado JP:     {metadata['market_players']}"
    )
    print(
        f"Articulos visitados:      {metadata['articles_visited']}"
    )
    print(
        f"Senales editoriales:      {metadata['editorial_signals']}"
    )
    print(
        f"Errores:                  {len(metadata['errors'])}"
    )

    print()
    print("## TOP SUBIDA 1 MERCADO")

    top_1 = sorted(
        data["players"],
        key=lambda player: (
            player.get(
                "last_markets",
                {},
            ).get(
                "1",
                0,
            )
        ),
        reverse=True,
    )[:15]

    for player in top_1:
        last = player["last_markets"]

        print(
            f"{str(player.get('name') or '?'):<24} "
            f"{money(player.get('price')):>15} "
            f"1={money(last.get('1')):>13} "
            f"3={money(last.get('3')):>13} "
            f"5={money(last.get('5')):>13} "
            f"tip={player.get('tip')}"
        )

    print()
    print("## CHOLLOS / EDITORIAL")

    editorial_players = [
        player
        for player in data["players"]
        if player.get(
            "editorial_signal_count",
            0,
        ) > 0
    ]

    editorial_players.sort(
        key=lambda player: (
            (
                player.get(
                    "latest_editorial_signal"
                )
                or {}
            ).get(
                "published_at"
            )
            or ""
        ),
        reverse=True,
    )

    for player in editorial_players[:30]:
        signal = (
            player.get(
                "latest_editorial_signal"
            )
            or {}
        )

        print(
            f"{str(player.get('name') or '?'):<24} "
            f"{signal.get('editorial_type', '?'):<10} "
            f"age={signal.get('age_hours')}h "
            f"forecast={signal.get('forecast')} "
            f"| {signal.get('article_title')}"
        )

    print()
    print("## SANITY")

    if metadata["market_players"] < 300:
        raise SystemExit(
            "ERROR: se han parseado demasiado pocos jugadores."
        )

    remote_ids = [
        player.get("biwenger_remote_id")
        for player in data["players"]
        if player.get("biwenger_remote_id")
    ]

    print(
        f"Remote IDs Biwenger:       {len(remote_ids)}"
    )

    if len(remote_ids) < 300:
        raise SystemExit(
            "ERROR: faltan demasiados remote_player."
        )

    print("JP MARKET PROVIDER: OK")
    print("=" * 110)


if __name__ == "__main__":
    main()
