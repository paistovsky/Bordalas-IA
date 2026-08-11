from src.analysis.home_away_intelligence import AWAY_BONUS, HOME_BONUS
from src.intelligence.penalty_intelligence import (
    PRIMARY_BONUS,
    SECONDARY_BONUS,
    _role_from_taken,
)


def main() -> None:
    assert HOME_BONUS == 5.0
    assert AWAY_BONUS == 0.0

    role, bonus, _ = _role_from_taken(0)
    assert role == "UNKNOWN"
    assert bonus == 0.0

    role, bonus, _ = _role_from_taken(1)
    assert role == "SECONDARY_EVIDENCE"
    assert bonus == SECONDARY_BONUS

    role, bonus, _ = _role_from_taken(2)
    assert role == "PRIMARY_EVIDENCE"
    assert bonus == PRIMARY_BONUS

    assert HOME_BONUS + PRIMARY_BONUS < 20

    print()
    print("Home bonus:            +5")
    print("Away bonus:             0")
    print("Penalty primary:       +8")
    print("Penalty secondary:     +3")
    print("Context max combined: +13")
    print()
    print("# CONTEXTUAL SCORING V1: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()
