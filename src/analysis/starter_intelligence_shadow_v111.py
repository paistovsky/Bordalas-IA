from __future__ import annotations

from src.analysis.lineup_engine import (
    FORMATIONS,
    evaluate_formation,
    prepare_players,
)
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.intelligence.starter_intelligence_v11 import (
    build_starter_signal,
)


def build_v11_shadow_lineup(snapshot):
    players = prepare_players(snapshot)

    for player in players:
        signal = build_starter_signal(
            player.get("external_lineup") or {}
        )

        player["starter_probability"] = signal["starter_probability"]
        player["expected_minutes"] = signal["expected_minutes"]
        player["starter_source_coverage"] = signal["source_coverage"]
        player["starter_confidence_tier"] = signal["confidence_tier"]
        player["starter_consensus"] = signal["consensus"]
        player["starter_sources"] = signal["sources"]

        old_score = float(player.get("lineup_score") or 0)

        if old_score > -999999:
            # Titularidad domina. El score anterior solo desempata calidad.
            player["lineup_score"] = (
                signal["starter_probability"] * 10.0
                + old_score * 0.10
            )

    results = []
    for name, formation in FORMATIONS.items():
        results.append(
            evaluate_formation(
                players,
                name,
                formation,
            )
        )

    results.sort(
        key=lambda r: (
            r["filled"],
            r["score"],
        ),
        reverse=True,
    )

    return results[0] if results else {
        "selected": [],
        "complete": False,
        "filled": 0,
        "formation_name": "NONE",
        "score": 0,
    }


def main():
    snapshot_file = get_latest_snapshot()
    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(snapshot_file)

    legacy_players = prepare_players(snapshot)
    legacy_results = []
    for name, formation in FORMATIONS.items():
        legacy_results.append(
            evaluate_formation(
                legacy_players,
                name,
                formation,
            )
        )
    legacy_results.sort(
        key=lambda r: (r["filled"], r["score"]),
        reverse=True,
    )
    legacy = legacy_results[0]

    v11 = build_v11_shadow_lineup(snapshot)

    legacy_ids = {int(p["id"]) for p in legacy.get("selected", [])}
    v11_ids = {int(p["id"]) for p in v11.get("selected", [])}

    print("\n" + "=" * 112)
    print("BORDALAS IA - V11.1 STARTER INTELLIGENCE SHADOW")
    print("=" * 112)
    print(f"Snapshot: {snapshot_file}")
    print(f"Legacy: {legacy.get('formation_name')} | XI={legacy.get('filled')}")
    print(f"V11.1:  {v11.get('formation_name')} | XI={v11.get('filled')}")
    print("-" * 112)

    for p in sorted(
        v11.get("selected", []),
        key=lambda x: (
            int(x.get("lineup_position") or 99),
            -float(x.get("lineup_score") or 0),
        ),
    ):
        marker = " NEW" if int(p["id"]) not in legacy_ids else ""
        print(
            f"{p.get('name',''):<24} "
            f"P={float(p.get('starter_probability') or 0):>5.1f}% "
            f"MIN={float(p.get('expected_minutes') or 0):>5.1f} "
            f"SRC={int(p.get('starter_source_coverage') or 0)}/3 "
            f"CONF={p.get('starter_confidence_tier'):<6} "
            f"{p.get('starter_consensus')}{marker}"
        )

    removed = [
        p for p in legacy.get("selected", [])
        if int(p["id"]) not in v11_ids
    ]

    if removed:
        print("\nSALEN VS LEGACY:")
        for p in removed:
            print(f"  - {p.get('name')}")

    print("\nCOBERTURA:")
    weak = [
        p for p in v11.get("selected", [])
        if int(p.get("starter_source_coverage") or 0) < 2
    ]
    if weak:
        print(f"{len(weak)} jugadores del XI tienen <2/3 fuentes.")
        print("Pepe NO los considera consenso fuerte.")
    else:
        print("Todos los jugadores del XI tienen >=2/3 fuentes.")

    print("\nSHADOW ONLY - CERO WRITES BIWENGER")
    print("=" * 112)


if __name__ == "__main__":
    main()
