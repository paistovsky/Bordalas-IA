from src.intelligence.multisource_starter_v1124 import (
    consensus,
    strict_name_score,
)


def main():

    # Median: 2 sources beat one outlier.
    value = consensus(
        [
            {"probability": 90},
            {"probability": 30},
            {"probability": 35},
        ]
    )

    assert (
        value[
            "starter_probability"
        ]
        == 35.0
    )

    assert (
        value[
            "consensus"
        ]
        == "BENCH"
    )

    # Two-source average.
    value = consensus(
        [
            {"probability": 80},
            {"probability": 70},
        ]
    )

    assert (
        value[
            "starter_probability"
        ]
        == 75.0
    )

    assert (
        value[
            "consensus"
        ]
        == "STARTER"
    )

    # Identity: full surname strong.
    assert strict_name_score(
        "Matias Dituro",
        [
            "dituro",
            "matias dituro",
        ],
    ) >= 0.86

    # Cross identity not strong enough.
    assert strict_name_score(
        "Alvaro Garcia",
        [
            "alvaro fidalgo",
        ],
    ) < 0.75

    print(
        "V11.2.4 MULTISOURCE: 4/4 OK"
    )


if __name__ == "__main__":
    main()
