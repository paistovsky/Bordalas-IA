
from src.intelligence.multisource_starter_v1124 import (
    consensus,
)

def main():

    # Javi-type case: one strong starter + one 50% uncertain.
    value = consensus(
        [
            {
                "source": "JP",
                "probability": 92.2,
            },
            {
                "source": "AF",
                "probability": 50.0,
            },
        ]
    )

    assert value["consensus"] == "UNCERTAIN"
    assert value["starter_probability"] == 59.0
    assert value["starter_votes"] == 1
    assert value["uncertain_votes"] == 1
    assert value["ranking_tier"] == 3

    # Two true starter votes.
    value = consensus(
        [
            {
                "source": "JP",
                "probability": 92.2,
            },
            {
                "source": "AF",
                "probability": 70.0,
            },
        ]
    )

    assert value["consensus"] == "STARTER"
    assert value["ranking_tier"] == 5

    # One source cannot become confirmed STARTER.
    value = consensus(
        [
            {
                "source": "JP",
                "probability": 92.2,
            },
        ]
    )

    assert value["consensus"] == "STARTER_LEAN"
    assert value["starter_probability"] == 74.0
    assert value["ranking_tier"] == 4

    # Starter vs bench = conflict/uncertain.
    value = consensus(
        [
            {
                "source": "JP",
                "probability": 92.2,
            },
            {
                "source": "AF",
                "probability": 25.0,
            },
        ]
    )

    assert value["consensus"] == "UNCERTAIN"
    assert 41.0 <= value["starter_probability"] <= 59.0

    # Two bench votes.
    value = consensus(
        [
            {
                "source": "JP",
                "probability": 31.3,
            },
            {
                "source": "AF",
                "probability": 25.0,
            },
        ]
    )

    assert value["consensus"] == "BENCH"
    assert value["ranking_tier"] == 1

    print(
        "V11.3.1 CONSENSUS: 5/5 OK"
    )

if __name__ == "__main__":
    main()
