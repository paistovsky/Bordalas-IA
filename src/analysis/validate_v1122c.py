
from src.analysis.calendar_state import build_calendar_state
from src.analysis.market_analyzer import get_latest_snapshot, load_snapshot
from src.intelligence.jornada_perfecta_provider import refresh_jornada_perfecta_data

def main():
    snapshot_file = get_latest_snapshot()

    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(snapshot_file)
    calendar = build_calendar_state(snapshot)

    response = refresh_jornada_perfecta_data(
        snapshot=snapshot,
        target_matchday=calendar.get("target_matchday"),
        seconds_to_deadline=calendar.get("seconds_to_deadline"),
        force=True,
    )

    data = response.get("data", {}) or {}
    rows = data.get("players", []) or []
    metadata = data.get("metadata", {}) or {}

    by_id = {
        int(row["biwenger_id"]): row
        for row in rows
        if row.get("biwenger_id")
    }

    print()
    print("=" * 120)
    print("JORNADA PERFECTA V11.2.2C - VALIDACION REAL")
    print("=" * 120)
    print("Profiles checked: ", metadata.get("jp_profile_checked"))
    print("Explicit profiles:", metadata.get("jp_profile_explicit"))
    print("Overrides:        ", metadata.get("jp_profile_overrides"))
    print("-" * 120)

    fidalgo = None

    for player in snapshot.get("my_team", []):
        row = by_id.get(int(player["id"]), {}) or {}

        print(
            f"{player.get('name',''):<24} "
            f"{str(row.get('status','UNKNOWN')):<12} "
            f"conf={int(row.get('confidence') or 0):>3}% "
            f"profile={str(row.get('jp_profile_pronostico')):<12} "
            f"role={row.get('jp_parser_role')}"
        )

        if "fidalgo" in str(player.get("name", "")).lower():
            fidalgo = row

    print()
    print("FIDALGO:")
    print(fidalgo)

    if not fidalgo:
        raise RuntimeError("Fidalgo no identificado.")

    if fidalgo.get("status") != "SUPLENTE":
        raise RuntimeError(
            "Fidalgo no esta como SUPLENTE."
        )

    if str(
        fidalgo.get("jp_profile_pronostico") or ""
    ).strip().lower() != "suplente":
        raise RuntimeError(
            "Fidalgo no confirmado por ficha individual."
        )

    print()
    print("OK - FIDALGO = SUPLENTE SEGUN FICHA INDIVIDUAL JP")
    print("=" * 120)

if __name__ == "__main__":
    main()
