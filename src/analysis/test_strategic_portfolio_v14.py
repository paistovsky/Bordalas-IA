from __future__ import annotations

import src.analysis.competitive_offer_portfolio_engine as engine

from src.analysis.competitive_offer_portfolio_engine import (
    build_competitive_offer_portfolio,
)


def assert_true(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(
            message
        )


def main() -> None:

    snapshot = {
        "market": {
            "status": {
                "balance":
                    -4_651_032,
            }
        },
        "my_team":
            [],
    }

    decisions = [
        {
            "offer_id":
                1,

            "player_id":
                101,

            "player_name":
                "Jutgla",

            "counterparty_type":
                "MANAGER",

            "amount":
                4_300_000,

            "market_value":
                4_120_000,

            "decision":
                "KEEP_GOOD_OFFER",

            "competitive_observer":
                {
                    "counter_amount":
                        5_480_000,

                    "strategic_sell_price":
                        5_480_000,

                    "rival_reinforcement_score":
                        87.6,
                },
        },
        {
            "offer_id":
                2,

            "player_id":
                103,

            "player_name":
                "Ximo",

            "counterparty_type":
                "MANAGER",

            "amount":
                1_200_000,

            "market_value":
                1_170_000,

            "decision":
                "HOLD_OFFER",

            "competitive_observer":
                {
                    "counter_amount":
                        1_600_000,

                    "strategic_sell_price":
                        1_600_000,

                    "rival_reinforcement_score":
                        75.5,
                },
        },
    ]

    original = (
        engine.simulate_lineup_without_players
    )

    def fake_simulation(
        snapshot,
        player_ids,
    ):
        return {
            "playable_count":
                11,

            "missing":
                0,

            "complete":
                True,

            "shortages":
                {},
        }

    engine.simulate_lineup_without_players = (
        fake_simulation
    )

    try:

        board = (
            build_competitive_offer_portfolio(
                snapshot=
                    snapshot,

                decisions=
                    decisions,
            )
        )

        current = (
            board[
                "current"
            ][
                "recommended"
            ]
        )

        strategic = (
            board[
                "strategic"
            ][
                "recommended"
            ]
        )

        assert_true(
            current[
                "total_amount"
            ]
            ==
            5_500_000,
            "CURRENT debe usar ofertas actuales.",
        )

        assert_true(
            strategic[
                "player_names"
            ]
            ==
            [
                "Jutgla",
            ],
            "A precio estrategico, Jutgla solo ya debe bastar para sanear.",
        )

        assert_true(
            strategic[
                "total_amount"
            ]
            ==
            5_480_000,
            "STRATEGIC debe usar la contraoferta de Jutgla.",
        )

        assert_true(
            strategic[
                "post_balance"
            ]
            ==
            828_968,
            "Saldo estrategico incorrecto tras vender solo Jutgla.",
        )

        print("=" * 110)
        print("BORDALAS IA - STRATEGIC PORTFOLIO V1.4")
        print("=" * 110)

        print()
        print("CURRENT")
        print(current)

        print()
        print("STRATEGIC")
        print(strategic)

        print()
        print("# STRATEGIC PORTFOLIO V1.4: OK")

    finally:

        engine.simulate_lineup_without_players = (
            original
        )


if __name__ == "__main__":
    main()
