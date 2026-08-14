
from src.analysis.lineup_engine import build_lineup
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

def main():
    snapshot_file = get_latest_snapshot()

    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(snapshot_file)
    lineup = build_lineup(snapshot)

    print()
    print("=" * 120)
    print("V11.3 STARTER INTELLIGENCE - VALIDACION REAL")
    print("=" * 120)
    print(
        "Version:",
        lineup.get("starter_intelligence_version"),
    )
    print(
        "Formacion:",
        lineup.get("formation_name"),
        "| XI:",
        lineup.get("total_selected"),
        "/11",
    )
    print("-" * 120)

    selected_fidalgo = None

    for player in lineup.get("selected", []):
        print(
            f"{player.get('name',''):<24} "
            f"P={str(player.get('starter_probability')):<6} "
            f"SRC={player.get('starter_source_coverage')}/3 "
            f"{player.get('starter_consensus')}"
        )

        if "fidalgo" in str(
            player.get("name", "")
        ).lower():
            selected_fidalgo = player

    board = lineup.get(
        "starter_intelligence",
        {},
    ) or {}

    fidalgo = next(
        (
            item
            for item in board.get("players", [])
            if "fidalgo"
            in str(
                item.get("player_name", "")
            ).lower()
        ),
        None,
    )

    print()
    print("FIDALGO BOARD:")
    print(fidalgo)

    if lineup.get("total_selected") != 11:
        raise RuntimeError(
            "No se genera XI completo."
        )

    if not fidalgo:
        raise RuntimeError(
            "Fidalgo no aparece en starter board."
        )

    jp = (
        fidalgo.get("sources", {})
        .get("JORNADA_PERFECTA")
        or {}
    )

    if str(
        jp.get("status")
    ).upper() != "SUPLENTE":
        raise RuntimeError(
            "REGRESION: JP no marca Fidalgo SUPLENTE."
        )

    if "alvaro-garcia" in str(
        jp.get("url")
        or ""
    ).lower():
        raise RuntimeError(
            "REGRESION: Fidalgo enlazado a Alvaro Garcia."
        )

    probability = float(
        fidalgo.get("starter_probability")
        or 100
    )

    if (
        selected_fidalgo is not None
        and
        probability <= 40.0
    ):
        raise RuntimeError(
            "Fidalgo entra en XI con P<=40."
        )

    coverages = [
        int(
            item.get("source_coverage")
            or 0
        )
        for item in board.get("players", [])
    ]

    if (
        not coverages
        or
        max(coverages) < 2
    ):
        raise RuntimeError(
            "No hay cobertura multisource >=2."
        )

    print()
    print("OK - XI completo con Starter Intelligence V11.3.")
    print("OK - Fidalgo protegido.")
    print("=" * 120)

if __name__ == "__main__":
    main()
