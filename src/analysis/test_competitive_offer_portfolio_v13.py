from __future__ import annotations

from src.analysis.competitive_offer_portfolio_engine import (
    build_competitive_offer_portfolio,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fake_snapshot() -> dict:
    # El test del portfolio puro no necesita recalcular lineup:
    # se monkeypatchea el simulador abajo.
    return {
        "market": {
            "status": {
                "balance": -4_651_032,
            }
        },
        "my_team": [],
    }


def main() -> None:
    import src.analysis.competitive_offer_portfolio_engine as engine

    original = engine.simulate_lineup_without_players

    def fake_simulation(snapshot, player_ids):
        count = len(set(player_ids))

        # 1 venta mantiene 11, 2 deja 10, 3 deja 9.
        playable = {
            1: 11,
            2: 10,
            3: 9,
        }.get(count, 11)

        return {
            "playable_count": playable,
            "missing": max(11 - playable, 0),
            "complete": playable >= 11,
            "shortages": {},
        }

    engine.simulate_lineup_without_players = fake_simulation

    try:
        decisions = [
            {
                "offer_id": 1,
                "player_id": 101,
                "player_name": "Jutgla",
                "counterparty_type": "MANAGER",
                "amount": 4_300_000,
                "market_value": 4_120_000,
                "decision": "KEEP_GOOD_OFFER",
                "competitive_observer": {
                    "rival_reinforcement_score": 87.6,
                },
            },
            {
                "offer_id": 2,
                "player_id": 102,
                "player_name": "Olasagasti",
                "counterparty_type": "MANAGER",
                "amount": 2_750_000,
                "market_value": 2_620_000,
                "decision": "KEEP_GOOD_OFFER",
                "competitive_observer": {
                    "rival_reinforcement_score": 88.2,
                },
            },
            {
                "offer_id": 3,
                "player_id": 103,
                "player_name": "Ximo",
                "counterparty_type": "MANAGER",
                "amount": 1_200_000,
                "market_value": 1_170_000,
                "decision": "HOLD_OFFER",
                "competitive_observer": {
                    "rival_reinforcement_score": 75.5,
                },
            },
        ]

        board = build_competitive_offer_portfolio(
            snapshot=fake_snapshot(),
            decisions=decisions,
        )

        solvency = board["solvency_combinations"]

        assert_true(
            len(solvency) > 0,
            "Debe existir alguna combinacion que recupere solvencia.",
        )

        recommended = board["recommended"]

        assert_true(
            recommended["restores_solvency"],
            "La recomendacion debe priorizar saldo >= 0.",
        )

        assert_true(
            recommended["sold_count"] == 2,
            "Con estas ofertas debe preferir 2 ventas a 3 si bastan para solvencia.",
        )

        assert_true(
            recommended["playable_count"] == 10,
            "El test simulado debe reflejar el coste de XI de la combinacion.",
        )

        print("=" * 100)
        print("BORDALAS IA - COMPETITIVE OFFER PORTFOLIO V1.3")
        print("=" * 100)
        print()
        print("RECOMMENDED")
        print(recommended)
        print()
        print("# COMPETITIVE OFFER PORTFOLIO V1.3: OK")

    finally:
        engine.simulate_lineup_without_players = original


if __name__ == "__main__":
    main()
