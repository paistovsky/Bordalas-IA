
from src.analysis.calendar_state import (
    build_calendar_state,
)

from src.analysis.lineup_engine import (
    build_lineup,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.intelligence.multisource_starter_v1124 import (
    build_multisource_board,
)


def fmt(source):
    if not source:
        return "--"

    return str(
        source.get(
            "probability"
        )
    )


def main():

    snapshot_file = get_latest_snapshot()

    if not snapshot_file:
        raise RuntimeError(
            "No hay snapshot."
        )

    snapshot = load_snapshot(
        snapshot_file
    )

    calendar = build_calendar_state(
        snapshot
    )

    board = build_multisource_board(
        snapshot=
            snapshot,

        matchday=
            int(
                calendar.get(
                    "target_matchday"
                )
                or 1
            ),

        seconds_to_deadline=
            calendar.get(
                "seconds_to_deadline"
            ),
    )

    metadata = (
        board.get(
            "metadata",
            {},
        )
        or {}
    )

    ff_meta = (
        metadata.get(
            "futbolfantasy",
            {},
        )
        or {}
    )

    print()
    print("=" * 138)
    print(
        "V11.3.2 FUTBOLFANTASY DIRECT - VALIDACION REAL"
    )
    print("=" * 138)

    print(
        "FF metadata:",
        ff_meta,
    )

    print("-" * 138)

    print(
        f"{'JUGADOR':<24} "
        f"{'JP':>6} "
        f"{'FF':>6} "
        f"{'AF':>6} "
        f"{'P':>6} "
        f"{'VOTOS':<15} "
        f"{'CONSENSO':<14} "
        f"{'FF METHOD'}"
    )

    javi = None
    mangala = None

    for item in board.get(
        "players",
        [],
    ):

        sources = (
            item.get(
                "sources",
                {},
            )
            or {}
        )

        ff = (
            sources.get(
                "FUTBOLFANTASY"
            )
            or {}
        )

        votes = (
            f"{item.get('starter_votes',0)}S/"
            f"{item.get('uncertain_votes',0)}U/"
            f"{item.get('bench_votes',0)}B"
        )

        print(
            f"{item.get('player_name',''):<24} "
            f"{fmt(sources.get('JORNADA_PERFECTA')):>6} "
            f"{fmt(sources.get('FUTBOLFANTASY')):>6} "
            f"{fmt(sources.get('ANALITICA_FANTASY')):>6} "
            f"{str(item.get('starter_probability')):>6} "
            f"{votes:<15} "
            f"{str(item.get('consensus')):<14} "
            f"{str(ff.get('method','--'))}"
        )

        name = str(
            item.get(
                "player_name",
                "",
            )
        ).lower()

        if "javi hern" in name:
            javi = item

        if "mangala" in name:
            mangala = item

    matched = int(
        ff_meta.get(
            "matched"
        )
        or 0
    )

    if matched < 5:
        raise RuntimeError(
            f"FF coverage insuficiente: {matched}. "
            "NO promocionar."
        )

    key_cases = [
        item
        for item in (
            javi,
            mangala,
        )
        if item
        and
        (
            item.get(
                "sources",
                {},
            )
            .get(
                "FUTBOLFANTASY"
            )
        )
    ]

    if not key_cases:
        raise RuntimeError(
            "FF no resuelve ni Javi ni Mangala. "
            "NO promocionar."
        )

    lineup = build_lineup(
        snapshot
    )

    print()
    print("XI V11.3.2")
    print("-" * 138)

    for player in lineup.get(
        "selected",
        [],
    ):

        print(
            f"{player.get('name',''):<24} "
            f"P={str(player.get('starter_probability')):<6} "
            f"SRC={player.get('starter_source_coverage')}/3 "
            f"{player.get('starter_consensus')}"
        )

    if lineup.get(
        "total_selected"
    ) != 11:
        raise RuntimeError(
            "XI incompleto."
        )

    print()
    print(
        "OK - FutbolFantasy aporta cobertura real."
    )
    print(
        "OK - al menos Javi o Mangala queda resuelto por FF."
    )
    print(
        "OK - XI completo."
    )
    print("=" * 138)


if __name__ == "__main__":
    main()
