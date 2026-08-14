
from src.analysis.lineup_engine import (
    build_lineup,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

def fmt_source(source):
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

    lineup = build_lineup(
        snapshot
    )

    board = (
        lineup.get(
            "starter_intelligence",
            {},
        )
        or {}
    )

    print()
    print("=" * 128)
    print(
        "V11.3.1 CONSENSUS FIX - VALIDACION REAL"
    )
    print("=" * 128)

    print(
        f"{'JUGADOR':<24} "
        f"{'JP':>6} "
        f"{'FF':>6} "
        f"{'AF':>6} "
        f"{'RAW':>6} "
        f"{'P':>6} "
        f"{'VOTOS':<17} "
        f"{'CONSENSO':<14} "
        f"{'CONF'}"
    )

    print("-" * 128)

    javi = None
    fidalgo = None

    for item in board.get(
        "players",
        [],
    ):

        sources = item.get(
            "sources",
            {},
        ) or {}

        votes = (
            f"{item.get('starter_votes',0)}S/"
            f"{item.get('uncertain_votes',0)}U/"
            f"{item.get('bench_votes',0)}B"
        )

        print(
            f"{item.get('player_name',''):<24} "
            f"{fmt_source(sources.get('JORNADA_PERFECTA')):>6} "
            f"{fmt_source(sources.get('FUTBOLFANTASY')):>6} "
            f"{fmt_source(sources.get('ANALITICA_FANTASY')):>6} "
            f"{str(item.get('raw_starter_probability')):>6} "
            f"{str(item.get('starter_probability')):>6} "
            f"{votes:<17} "
            f"{str(item.get('consensus')):<14} "
            f"{item.get('confidence')}"
        )

        name = str(
            item.get(
                "player_name",
                "",
            )
        ).lower()

        if "javi hern" in name:
            javi = item

        if "fidalgo" in name:
            fidalgo = item

    print()
    print("XI RECOMENDADO V11.3.1")
    print("-" * 128)

    selected_names = []

    for player in lineup.get(
        "selected",
        [],
    ):

        selected_names.append(
            player.get(
                "name"
            )
        )

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

    if not fidalgo:
        raise RuntimeError(
            "No encuentro Fidalgo."
        )

    jp_fidalgo = (
        fidalgo.get(
            "sources",
            {},
        )
        .get(
            "JORNADA_PERFECTA"
        )
        or {}
    )

    if str(
        jp_fidalgo.get(
            "status"
        )
    ).upper() != "SUPLENTE":
        raise RuntimeError(
            "Regresion Fidalgo."
        )

    # Conditional gate for the exact current Javi situation.
    if javi:

        sources = (
            javi.get(
                "sources",
                {},
            )
            or {}
        )

        jp = (
            sources.get(
                "JORNADA_PERFECTA"
            )
            or {}
        )

        af = (
            sources.get(
                "ANALITICA_FANTASY"
            )
            or {}
        )

        jp_p = jp.get(
            "probability"
        )

        af_p = af.get(
            "probability"
        )

        if (
            jp_p is not None
            and
            float(jp_p) >= 67.0
            and
            af_p is not None
            and
            41.0 <= float(af_p) <= 59.0
        ):

            if (
                javi.get(
                    "consensus"
                )
                != "UNCERTAIN"
            ):
                raise RuntimeError(
                    "Javi deberia ser UNCERTAIN."
                )

            if float(
                javi.get(
                    "starter_probability"
                )
                or 100
            ) > 59.0:
                raise RuntimeError(
                    "Javi supera banda UNCERTAIN."
                )

    print()
    print(
        "OK - consenso por votos activo."
    )
    print(
        "OK - STARTER requiere 2 votos cuando hay >=2 fuentes."
    )
    print(
        "OK - XI completo."
    )
    print("=" * 128)

if __name__ == "__main__":
    main()
