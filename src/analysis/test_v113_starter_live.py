
from src.intelligence.multisource_starter_v1124 import (
    consensus,
    strict_name_score,
)

def main():
    result = consensus(
        [
            {"probability": 92},
            {"probability": 25},
        ]
    )
    assert result["starter_probability"] == 58.5

    result = consensus(
        [
            {"probability": 90},
            {"probability": 30},
            {"probability": 35},
        ]
    )
    assert result["starter_probability"] == 35.0
    assert result["consensus"] == "BENCH"

    assert strict_name_score(
        "Alvaro Garcia",
        ["alvaro fidalgo"],
    ) < 0.75

    assert strict_name_score(
        "Fidalgo",
        ["alvaro fidalgo"],
    ) >= 0.86

    print("V11.3 STARTER CORE: 4/4 OK")

if __name__ == "__main__":
    main()
