from datetime import datetime, timedelta, timezone

from src.intelligence.multisource_starter_v1124 import (
    cached_board_is_fresh,
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

    now = datetime.now(timezone.utc)
    cached = {
        "matchday": 1,
        "updated_at": (
            now - timedelta(minutes=10)
        ).isoformat(),
    }

    assert cached_board_is_fresh(
        cached,
        matchday=1,
        seconds_to_deadline=24 * 3600,
        now=now,
    )

    stale = {
        **cached,
        "updated_at": (
            now - timedelta(minutes=31)
        ).isoformat(),
    }

    assert not cached_board_is_fresh(
        stale,
        matchday=1,
        seconds_to_deadline=24 * 3600,
        now=now,
    )

    near_deadline = {
        **cached,
        "updated_at": (
            now - timedelta(minutes=11)
        ).isoformat(),
    }

    assert not cached_board_is_fresh(
        near_deadline,
        matchday=1,
        seconds_to_deadline=60 * 60,
        now=now,
    )

    print(
        "V11.2.4 MULTISOURCE: 7/7 OK"
    )


if __name__ == "__main__":
    main()
