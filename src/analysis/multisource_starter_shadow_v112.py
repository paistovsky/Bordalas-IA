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
from src.intelligence.multisource_starter_v112 import (
    build_board,
)


def build_shadow_lineup(prepared, board):
    lookup = {int(item["player_id"]): item for item in board}

    players = []
    for player in prepared:
        item = lookup.get(int(player["id"])) or {}
        probability = float(item.get("starter_probability") or 50.0)
        coverage = int(item.get("source_coverage") or 0)
        old_score = float(player.get("lineup_score") or 0)

        candidate = {
            **player,
            "starter_probability_v112": probability,
            "expected_minutes_v112": item.get("expected_minutes"),
            "starter_coverage_v112": coverage,
            "starter_consensus_v112": item.get("consensus"),
            "starter_confidence_v112": item.get("confidence_tier"),
            "starter_sources_v112": item.get("sources", []),
        }

        if old_score > -999999:
            # Coverage-aware: true multi-source data dominates.
            coverage_bonus = min(coverage, 3) * 20.0
            candidate["lineup_score"] = (
                probability * 10.0
                + coverage_bonus
                + old_score * 0.08
            )

        players.append(candidate)

    results = [
        evaluate_formation(players, name, formation)
        for name, formation in FORMATIONS.items()
    ]
    results.sort(
        key=lambda result: (
            result["filled"],
            result["score"],
        ),
        reverse=True,
    )
    return results[0]


def source_text(item):
    parts = []
    for source in item.get("sources", []):
        name = source.get("source", "?")
        value = source.get("probability")
        method = source.get("method")
        if value is None:
            parts.append(f"{name}=NA[{method}]")
        else:
            parts.append(f"{name}={float(value):.1f}%[{method}]")
    return " | ".join(parts)


def main():
    snapshot_file = get_latest_snapshot()
    if not snapshot_file:
        raise RuntimeError("No hay snapshot.")

    snapshot = load_snapshot(snapshot_file)
    prepared = prepare_players(snapshot)

    print("\nConsultando JP + FutbolFantasy + Analitica Fantasy...")
    board = build_board(prepared)

    v11 = build_shadow_lineup(prepared, board)
    lookup = {int(item["player_id"]): item for item in board}

    print("\n" + "=" * 122)
    print("BORDALAS IA - V11.2 MULTISOURCE STARTER INTELLIGENCE")
    print("=" * 122)
    print(f"Snapshot: {snapshot_file}")
    print(f"XI SHADOW: {v11.get('formation_name')} | {v11.get('filled')}/11")
    print("-" * 122)

    print("\nPLANTILLA COMPLETA:")
    for item in sorted(
        board,
        key=lambda x: (
            -int(x.get("source_coverage") or 0),
            -float(x.get("starter_probability") or 0),
        ),
    ):
        print(
            f"{item['player_name']:<24} "
            f"P={float(item['starter_probability']):>5.1f}% "
            f"MIN={float(item['expected_minutes']):>5.1f} "
            f"SRC={int(item['source_coverage'])}/3 "
            f"{item['confidence_tier']:<12} "
            f"{item['consensus']:<13}"
        )
        print(f"    {source_text(item)}")

    print("\nXI V11.2:")
    for player in v11.get("selected", []):
        item = lookup.get(int(player["id"])) or {}
        print(
            f"  {player.get('name',''):<24} "
            f"P={float(item.get('starter_probability') or 0):>5.1f}% "
            f"SRC={int(item.get('source_coverage') or 0)}/3 "
            f"{item.get('consensus')}"
        )

    weak = [
        item for item in board
        if int(item.get("source_coverage") or 0) < 2
    ]
    print("\nCOBERTURA:")
    print(
        f"{len(board) - len(weak)}/{len(board)} jugadores "
        f"con al menos 2 fuentes utilizables."
    )

    print("\nSHADOW ONLY - CERO WRITES BIWENGER")
    print("=" * 122)


if __name__ == "__main__":
    main()
