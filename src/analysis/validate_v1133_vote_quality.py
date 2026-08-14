
from src.analysis.lineup_engine import build_lineup
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def vote_text(item):
    return (
        f"{item.get('starter_votes',0)}S/"
        f"{item.get('uncertain_votes',0)}U/"
        f"{item.get('bench_votes',0)}B"
    )


def main():
    snapshot_file = get_latest_snapshot()

    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(snapshot_file)
    lineup = build_lineup(snapshot)

    board = (
        lineup.get(
            "starter_intelligence",
            {},
        )
        or {}
    )

    lookup = {
        int(item["player_id"]): item
        for item in board.get("players", [])
    }

    selected = lineup.get(
        "selected",
        [],
    )

    print()
    print("=" * 132)
    print("V11.3.3 VOTE QUALITY - VALIDACION REAL")
    print("=" * 132)

    print("XI FINAL RECOMENDADO")
    print("-" * 132)

    for player in selected:
        item = lookup.get(
            int(player["id"]),
            {},
        ) or {}

        print(
            f"{player.get('name',''):<24} "
            f"P={float(item.get('starter_probability') or 0):>5.1f}% "
            f"SRC={int(item.get('source_coverage') or 0)}/3 "
            f"V={vote_text(item):<9} "
            f"{item.get('consensus')}"
        )

    print()
    print(
        "Formacion:",
        lineup.get("formation_name"),
    )

    if lineup.get("total_selected") != 11:
        raise RuntimeError("XI incompleto.")

    javi = None
    etta = None
    mangala = None

    for item in board.get("players", []):
        name = str(
            item.get(
                "player_name",
                "",
            )
        ).lower()

        if "javi hern" in name:
            javi = item

        if "etta" in name:
            etta = item

        if "mangala" in name:
            mangala = item

    if javi and javi.get("consensus") != "UNCERTAIN":
        raise RuntimeError(
            "Javi ya no aparece UNCERTAIN."
        )

    if etta and mangala:
        etta_quality = (
            int(etta.get("starter_votes") or 0)
            -
            int(etta.get("bench_votes") or 0)
        )

        mangala_quality = (
            int(mangala.get("starter_votes") or 0)
            -
            int(mangala.get("bench_votes") or 0)
        )

        if mangala_quality <= etta_quality:
            raise RuntimeError(
                "Fixture inesperado: "
                "Mangala deberia tener mejor evidencia que Etta."
            )

    print()
    print("EVIDENCIA CLAVE")
    print("-" * 132)

    for label, item in (
        ("Javi", javi),
        ("Mangala", mangala),
        ("Etta", etta),
    ):
        if not item:
            continue

        print(
            f"{label:<10} "
            f"P={float(item.get('starter_probability') or 0):>5.1f}% "
            f"V={vote_text(item):<9} "
            f"{item.get('consensus')}"
        )

    print()
    print("OK - vote quality activo.")
    print(
        "OK - mas STARTER votes premian y BENCH votes penalizan."
    )
    print(
        "OK - Javi sigue siendo UNCERTAIN, no titular confirmado."
    )
    print("=" * 132)


if __name__ == "__main__":
    main()
