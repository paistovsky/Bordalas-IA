
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.intelligence.lineup_intelligence import (
    build_lineup_intelligence,
)


def main():
    snapshot_file = get_latest_snapshot()

    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(
        snapshot_file
    )

    intelligence = build_lineup_intelligence(
        snapshot
    )

    lookup = intelligence.get(
        "lookup",
        {},
    )

    print("\n" + "=" * 104)
    print("JORNADA PERFECTA V11.2.1 - VALIDACION REAL")
    print("=" * 104)

    fidalgo = None

    for player in snapshot.get(
        "my_team",
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
            f"{player.get('name',''):<24} "
            f"{str(item.get('status','UNKNOWN')):<10} "
            f"conf={int(item.get('effective_confidence') or item.get('confidence') or 0):>3}% "
            f"jp={item.get('jp_probability')} "
            f"role={item.get('jp_parser_role')}"
        )

        if "fidalgo" in str(
            player.get(
                "name",
                "",
            )
        ).lower():

            fidalgo = item

    print("\nFIDALGO:")
    print(fidalgo)

    if fidalgo:
        confidence = int(
            fidalgo.get(
                "effective_confidence"
            )
            or
            fidalgo.get(
                "confidence"
            )
            or 0
        )

        if (
            fidalgo.get(
                "status"
            )
            == "TITULAR"
            and
            confidence
            >= 88
        ):
            raise RuntimeError(
                "Fidalgo sigue como falso TITULAR 88."
            )

    print("\nOK: el falso TITULAR 88 ya no esta permitido.")
    print("=" * 104)


if __name__ == "__main__":
    main()
