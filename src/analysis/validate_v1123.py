
from src.analysis.calendar_state import build_calendar_state
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.intelligence.jornada_perfecta_provider import (
    build_roster_records,
    canonical_team_key,
    refresh_jornada_perfecta_data,
)

def main():
    snapshot_file = get_latest_snapshot()

    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(
        snapshot_file
    )

    calendar = build_calendar_state(
        snapshot
    )

    response = refresh_jornada_perfecta_data(
        snapshot=snapshot,
        target_matchday=calendar.get(
            "target_matchday"
        ),
        seconds_to_deadline=calendar.get(
            "seconds_to_deadline"
        ),
        force=True,
    )

    data = response.get(
        "data",
        {},
    ) or {}

    rows = data.get(
        "players",
        [],
    ) or []

    roster = build_roster_records(
        snapshot
    )

    roster_by_id = {
        int(item["id"]): item
        for item in roster
    }

    by_id = {
        int(row["biwenger_id"]): row
        for row in rows
        if row.get("biwenger_id")
    }

    print()
    print("=" * 126)
    print("V11.2.3 JP IDENTITY MATCH - VALIDACION REAL")
    print("=" * 126)

    fidalgo = None

    for player in snapshot.get(
        "my_team",
        [],
    ):
        player_id = int(
            player["id"]
        )

        row = by_id.get(
            player_id,
            {},
        ) or {}

        roster_item = roster_by_id.get(
            player_id,
            {},
        ) or {}

        print(
            f"{player.get('name',''):<24} "
            f"{str(row.get('status','UNKNOWN')):<11} "
            f"JP={str(row.get('jp_name')):<20} "
            f"teamJP={str(row.get('team')):<18} "
            f"url={str(row.get('player_url') or row.get('source_url') or '')}"
        )

        if "fidalgo" in str(
            player.get(
                "name",
                "",
            )
        ).lower():
            fidalgo = (
                row,
                roster_item,
            )

    if not fidalgo:
        raise RuntimeError(
            "No encuentro Fidalgo."
        )

    row, roster_item = fidalgo

    print()
    print("FIDALGO RAW:")
    print(row)

    url = str(
        row.get("player_url")
        or row.get("source_url")
        or ""
    ).lower()

    if "alvaro-garcia" in url:
        raise RuntimeError(
            "Fidalgo sigue enlazado a Alvaro Garcia."
        )

    jp_team = canonical_team_key(
        row.get("team")
    )

    roster_team = roster_item.get(
        "team_key"
    )

    if (
        jp_team
        and
        roster_team
        and
        jp_team != roster_team
    ):
        raise RuntimeError(
            f"Team mismatch Fidalgo: "
            f"JP={jp_team} Biwenger={roster_team}"
        )

    if row.get("status") != "SUPLENTE":
        raise RuntimeError(
            "Fidalgo aun no aparece SUPLENTE."
        )

    print()
    print("OK - FIDALGO MATCH CORRECTO + SUPLENTE")
    print("=" * 126)

if __name__ == "__main__":
    main()
