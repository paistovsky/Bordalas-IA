from src.analysis.lineup_engine import (
    FORMATIONS,
    get_player_positions,
    search_best_lineup_for_formation,
)

from src.analysis.position_policy import (
    POSITION_POLICY,
    assert_lineup_position_integrity,
)

from src.analysis.restructuring_roster_impact_engine import (
    get_player_positions as restructuring_positions,
)

from src.analysis.strategic_target_engine import (
    get_player_positions as strategic_positions,
)


def player(
    player_id: int,
    name: str,
    position: int,
    score: float,
    alt_positions: list[int] | None = None,
) -> dict:

    return {
        "id": player_id,
        "name": name,
        "position": position,
        "altPositions": alt_positions or [],

        # El test llama directamente al buscador de formaciones,
        # por lo que simulamos la salida de prepare_players().
        # Position Safety V1: solo posici?n principal.
        "eligible_positions": [position],

        "lineup_eligible": True,
        "automatic_lineup": True,
        "lineup_score": score,
    }


def main() -> None:

    suazo = player(
        38194,
        "Gabriel Suazo",
        2,
        331.79,
        [3],
    )

    assert POSITION_POLICY == "STRICT_PRIMARY"

    assert get_player_positions(suazo) == [2]
    assert strategic_positions(suazo) == [2]
    assert restructuring_positions(suazo) == [2]

    assert "3-4-3" in FORMATIONS
    assert "3-5-2" in FORMATIONS
    assert "4-3-3" in FORMATIONS
    assert "4-4-2" in FORMATIONS
    assert "4-5-1" in FORMATIONS
    assert "5-3-2" in FORMATIONS
    assert "5-4-1" in FORMATIONS

    squad = [
        player(1, "PT", 1, 100),

        player(2, "DF1", 2, 100),
        player(3, "DF2", 2, 99),
        suazo,

        player(5, "MC1", 3, 100),
        player(6, "MC2", 3, 99),
        player(7, "MC3", 3, 98),
        player(8, "MC4", 3, 97),

        player(9, "DL1", 4, 100),
        player(10, "DL2", 4, 99),
        player(11, "DL3", 4, 98),
    ]

    result_343 = search_best_lineup_for_formation(
        squad,
        FORMATIONS["3-4-3"],
    )

    assert result_343["complete"] is True
    assert result_343["filled"] == 11

    assert_lineup_position_integrity(
        result_343["selected"]
    )

    result_442 = search_best_lineup_for_formation(
        squad,
        FORMATIONS["4-4-2"],
    )

    # Solo hay 3 defensas reales. Suazo NO puede convertirse en MC
    # y ningun MC puede convertirse en defensa.
    assert result_442["complete"] is False
    assert result_442["filled"] < 11

    print()
    print("Position policy:       STRICT_PRIMARY")
    print("Suazo positions:       [2] DEFENSA")
    print("3-4-3 complete:        YES")
    print("4-4-2 complete:        NO (solo 3 defensas reales)")
    print()
    print("# POSITION INTEGRITY V1: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()
