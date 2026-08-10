from __future__ import annotations

from src.analysis.calendar_state import (
    build_calendar_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.intelligence.jornada_perfecta_adapter import (
    clear_jornada_perfecta_cache,
)

from src.intelligence.jornada_perfecta_provider import (
    refresh_jornada_perfecta_data,
)

from src.intelligence.lineup_intelligence import (
    build_lineup_intelligence,
)


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    calendar = (
        build_calendar_state(
            snapshot
        )
    )

    target_matchday = (
        calendar.get(
            "target_matchday"
        )
    )

    print()
    print("=" * 100)
    print(
        "             BORDALAS IA - JORNADA PERFECTA LIVE TEST"
    )
    print("=" * 100)
    print()

    print(
        f"Snapshot:              "
        f"{snapshot_file}"
    )

    print(
        f"Jornada objetivo:      "
        f"{target_matchday}"
    )

    print()
    print(
        "Refrescando Jornada Perfecta..."
    )
    print()

    refresh = (
        refresh_jornada_perfecta_data(
            snapshot=
                snapshot,

            target_matchday=
                target_matchday,

            seconds_to_deadline=
                calendar.get(
                    "seconds_to_deadline"
                ),

            force=
                True,
        )
    )

    clear_jornada_perfecta_cache()

    metadata = (
        refresh.get(
            "data",
            {},
        ).get(
            "metadata",
            {},
        )
        or {}
    )

    print(
        f"Estado provider:       "
        f"{refresh.get('status')}"
    )

    print(
        f"Paginas jornada:       "
        f"{metadata.get('pages_found')}"
    )

    print(
        f"Paginas visitadas:     "
        f"{metadata.get('pages_visited')}"
    )

    print(
        f"Equipos parseados:     "
        f"{metadata.get('parsed_teams')}"
    )

    print(
        f"Señales raw:           "
        f"{metadata.get('raw_signals')}"
    )

    print(
        f"Plantilla identificada:"
        f" {metadata.get('matched_roster_players')}"
    )

    print()

    board = (
        build_lineup_intelligence(
            snapshot
        )
    )

    print(
        f"Fuente:                "
        f"{board.get('source_state')}"
    )

    print(
        f"Provider:              "
        f"{board.get('provider_status')}"
    )

    print(
        f"Error provider:        "
        f"{board.get('provider_error') or 'NINGUNO'}"
    )

    print(
        f"Matched:               "
        f"{board.get('matched_players')}/"
        f"{board.get('team_players')}"
    )

    print(
        f"Actualizado:           "
        f"{board.get('updated_at')}"
    )

    print()

    print(
        "JUGADORES DE NUESTRA PLANTILLA"
    )

    print(
        "-" * 100
    )

    rows = []

    for player in snapshot.get(
        "my_team",
        [],
    ):

        signal = (
            board.get(
                "lookup",
                {},
            ).get(
                int(
                    player[
                        "id"
                    ]
                ),
                {},
            )
            or {}
        )

        rows.append(
            (
                player.get(
                    "name"
                ),
                signal.get(
                    "status"
                ),
                signal.get(
                    "confidence"
                ),
                signal.get(
                    "effective_confidence"
                ),
                signal.get(
                    "score_adjustment"
                ),
                signal.get(
                    "match_method"
                ),
            )
        )

    for (
        name,
        status,
        confidence,
        effective,
        adjustment,
        method,
    ) in rows:

        print(
            f"{str(name):<23}"
            f"{str(status):<15}"
            f"conf={str(confidence):<5}"
            f"eff={str(effective):<7}"
            f"adj={str(adjustment):<9}"
            f"{method}"
        )

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
