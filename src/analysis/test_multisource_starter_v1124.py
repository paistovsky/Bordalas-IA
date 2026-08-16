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

    # OJO: este fixture NO llevaba `players`, y el test afirmaba
    # que era fresco. Es literalmente el fallo del 16/08/2026:
    # un tablero sin jugadores servido como HIT durante dos horas,
    # que dejo el XI del dashboard publicado en "sin dato" y apago
    # la regla del once. La cobertura estaba, y estaba bendiciendo
    # el bug.
    cached = {
        "matchday": 1,
        "updated_at": (
            now - timedelta(minutes=10)
        ).isoformat(),
        "players": [
            {
                "player_id": 5771,
                "starter_probability": 92.2,
                "consensus": "STARTER",
            }
        ],
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

    # Y un tablero reciente pero vacio tampoco vale.
    assert not cached_board_is_fresh(
        {**cached, "players": []},
        matchday=1,
        seconds_to_deadline=24 * 3600,
        now=now,
    ), (
        "Un tablero de cero jugadores no es una cache valida: "
        "servirlo apaga la titularidad sin dar ningun error."
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
