from __future__ import annotations

from src.analysis.calendar_state import (
    build_calendar_state,
)

from src.analysis.lineup_engine import (
    FORMATIONS,
    evaluate_formation,
    prepare_players,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.intelligence.multisource_starter_v1124 import (
    build_multisource_board,
)


def source_short(
    source: dict | None,
) -> str:
    if not source:
        return "--"

    probability = source.get(
        "probability"
    )

    if probability is None:
        return "--"

    return (
        f"{float(probability):.0f}"
    )


def source_detail(
    source: dict | None,
) -> str:
    if not source:
        return "NO_DATA"

    return (
        f"P={source_short(source)} "
        f"{source.get('method')} "
        f"name={source.get('source_name')}"
    )


def build_shadow_xi(
    snapshot: dict,
    board: dict,
) -> dict:

    prepared = prepare_players(
        snapshot
    )

    lookup = {
        int(
            item[
                "player_id"
            ]
        ):
            item
        for item in board.get(
            "players",
            [],
        )
    }

    adjusted = []

    for player in prepared:

        intelligence = lookup.get(
            int(
                player[
                    "id"
                ]
            ),
            {},
        ) or {}

        probability = float(
            intelligence.get(
                "starter_probability"
            )
            or 50.0
        )

        coverage = int(
            intelligence.get(
                "source_coverage"
            )
            or 0
        )

        old_score = float(
            player.get(
                "lineup_score"
            )
            or 0.0
        )

        candidate = {
            **player,

            "starter_probability_v1124":
                probability,

            "starter_coverage_v1124":
                coverage,

            "starter_consensus_v1124":
                intelligence.get(
                    "consensus"
                ),
        }

        if old_score > -999999:

            # Titularidad dominates sporting tie-breakers.
            candidate[
                "lineup_score"
            ] = (
                probability
                * 100.0
                +
                coverage
                * 25.0
                +
                old_score
                * 0.03
            )

        adjusted.append(
            candidate
        )

    results = [
        evaluate_formation(
            adjusted,
            name,
            formation,
        )
        for name, formation
        in FORMATIONS.items()
    ]

    results.sort(
        key=lambda value: (
            value.get(
                "filled",
                0,
            ),
            value.get(
                "score",
                0.0,
            ),
        ),
        reverse=True,
    )

    return results[
        0
    ]


def main():

    snapshot_file = (
        get_latest_snapshot()
    )

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

    matchday = int(
        calendar.get(
            "target_matchday"
        )
        or 1
    )

    print()
    print(
        "Consultando JP corregido + "
        "FutbolFantasy + Analitica Fantasy..."
    )

    board = build_multisource_board(
        snapshot=
            snapshot,

        matchday=
            matchday,

        seconds_to_deadline=
            calendar.get(
                "seconds_to_deadline"
            ),
    )

    xi = build_shadow_xi(
        snapshot,
        board,
    )

    print()
    print(
        "="
        * 136
    )

    print(
        "BORDALAS IA - V11.2.4 "
        "MULTISOURCE REAL SHADOW"
    )

    print(
        "="
        * 136
    )

    print(
        f"Snapshot: {snapshot_file}"
    )

    print(
        f"Jornada:  {matchday}"
    )

    print(
        "-"
        * 136
    )

    print(
        f"{'JUGADOR':<24} "
        f"{'EQUIPO':<17} "
        f"{'JP':>4} "
        f"{'FF':>4} "
        f"{'AF':>4} "
        f"{'CONS':>6} "
        f"{'SRC':>5} "
        f"{'CONF':<9} "
        f"ESTADO"
    )

    print(
        "-"
        * 136
    )

    lookup = {}

    for item in board.get(
        "players",
        [],
    ):

        lookup[
            int(
                item[
                    "player_id"
                ]
            )
        ] = item

        sources = item.get(
            "sources",
            {},
        ) or {}

        print(
            f"{item.get('player_name',''):<24} "
            f"{str(item.get('team','')):<17} "
            f"{source_short(sources.get('JORNADA_PERFECTA')):>4} "
            f"{source_short(sources.get('FUTBOLFANTASY')):>4} "
            f"{source_short(sources.get('ANALITICA_FANTASY')):>4} "
            f"{float(item.get('starter_probability') or 0):>5.1f}% "
            f"{int(item.get('source_coverage') or 0):>3}/3 "
            f"{str(item.get('confidence','')):<9} "
            f"{item.get('consensus')}"
        )

    print()
    print(
        "DETALLE FUENTES:"
    )

    for item in board.get(
        "players",
        [],
    ):

        sources = item.get(
            "sources",
            {},
        ) or {}

        print()
        print(
            f"{item.get('player_name')} "
            f"({item.get('team')})"
        )

        print(
            "  JP:",
            source_detail(
                sources.get(
                    "JORNADA_PERFECTA"
                )
            ),
        )

        print(
            "  FF:",
            source_detail(
                sources.get(
                    "FUTBOLFANTASY"
                )
            ),
        )

        print(
            "  AF:",
            source_detail(
                sources.get(
                    "ANALITICA_FANTASY"
                )
            ),
        )

    print()
    print(
        "XI V11.2.4:"
    )

    for player in xi.get(
        "selected",
        [],
    ):

        item = lookup.get(
            int(
                player[
                    "id"
                ]
            ),
            {},
        ) or {}

        print(
            f"  {player.get('name',''):<24} "
            f"P={float(item.get('starter_probability') or 0):>5.1f}% "
            f"SRC={int(item.get('source_coverage') or 0)}/3 "
            f"{item.get('consensus')}"
        )

    print()
    print(
        "Formacion:",
        xi.get(
            "formation_name"
        ),
        "| XI=",
        xi.get(
            "filled"
        ),
        "/11",
    )

    metadata = board.get(
        "metadata",
        {},
    ) or {}

    print()
    print(
        "COBERTURA PROVEEDORES:"
    )

    print(
        "  Analitica:",
        metadata.get(
            "analitica"
        ),
    )

    print(
        "  FutbolFantasy:",
        metadata.get(
            "futbolfantasy"
        ),
    )

    # Hard validations for the bug we just fixed.
    fidalgo = next(
        (
            item
            for item in board.get(
                "players",
                [],
            )
            if "fidalgo"
            in str(
                item.get(
                    "player_name",
                    "",
                )
            ).lower()
        ),
        None,
    )

    if fidalgo:

        jp = (
            fidalgo.get(
                "sources",
                {},
            )
            .get(
                "JORNADA_PERFECTA"
            )
            or {}
        )

        jp_url = str(
            jp.get(
                "url"
            )
            or ""
        ).lower()

        if (
            "alvaro-garcia"
            in jp_url
        ):

            raise RuntimeError(
                "REGRESION: Fidalgo vuelve "
                "a apuntar a Alvaro Garcia."
            )

        if (
            str(
                jp.get(
                    "status"
                )
            ).upper()
            != "SUPLENTE"
        ):

            raise RuntimeError(
                "REGRESION: JP ya no clasifica "
                "Fidalgo como SUPLENTE."
            )

    print()
    print(
        "SHADOW ONLY - CERO WRITES BIWENGER"
    )

    print(
        "="
        * 136
    )


if __name__ == "__main__":
    main()
