import src.analysis.safe_debt_portfolio_engine as engine


ORIGINAL_FORMATIONS = engine.FORMATIONS
ORIGINAL_PREPARE = engine.prepare_players


def prepared_player(player_id: int, position: int, score: float) -> dict:
    return {
        "id": player_id,
        "name": f"P{player_id}",
        "position": position,
        "eligible_positions": [position],
        "lineup_eligible": True,
        "automatic_lineup": True,
        "lineup_score": score,
    }


def install_fixture() -> None:
    engine.FORMATIONS = {"4-4-2": {1: 1, 2: 4, 3: 4, 4: 2}}

    # XI de 100 puntos por jugador + banquillo.
    # DEF 6 es reemplazo muy debil: vender un DEF titular mantiene 11/11
    # pero causa una perdida deportiva >5% del XI total.
    roster = [prepared_player(1, 1, 100)]
    roster += [prepared_player(i, 2, 100) for i in range(2, 6)]
    roster += [prepared_player(6, 2, 10)]
    roster += [prepared_player(i, 3, 100) for i in range(7, 11)]
    roster += [prepared_player(11, 3, 95)]  # banquillo MED vendible sin tocar XI
    roster += [prepared_player(i, 4, 100) for i in range(12, 14)]

    engine.prepare_players = lambda snapshot: roster


def restore_fixture() -> None:
    engine.FORMATIONS = ORIGINAL_FORMATIONS
    engine.prepare_players = ORIGINAL_PREPARE


def offer(offer_id: str, player_id: int, amount: int) -> dict:
    return {
        "offer_id": offer_id,
        "amount": amount,
        "player_ids": [player_id],
        "players": [{"id": player_id, "name": f"P{player_id}"}],
    }


def test_b1_excludes_complete_xi_with_excessive_sporting_loss() -> None:
    install_fixture()
    board = engine.build_safe_liquidity_portfolio(
        {"my_team": []},
        {"offers": [
            offer("starter", 2, 8_000_000),
            offer("bench", 11, 1_000_000),
        ]},
        {"players": []},
        trading_max_lineup_loss_percent=5.0,
    )

    # B2 puede vender titular + banquillo y conservar 11/11 por el DEF 6.
    assert board["tier_b"]["amount"] == 9_000_000
    assert board["tier_b"]["lineup_complete"] is True
    assert board["tier_b"]["lineup_score_loss_percent"] > 5.0

    # B1 solo permite el MED de banquillo: no degrada el XI actual.
    assert board["trading_safe_total"] == 1_000_000
    assert board["trading_safe"]["trading_safe"] is True
    assert board["trading_safe"]["lineup_score_loss_percent"] <= 5.0


def test_b1_preserves_legacy_tier_b_for_emergency_compatibility() -> None:
    install_fixture()
    board = engine.build_safe_liquidity_portfolio(
        {"my_team": []},
        {"offers": [offer("starter", 2, 8_000_000)]},
        {"players": []},
        trading_max_lineup_loss_percent=5.0,
    )
    assert board["usable_total"] == 8_000_000  # legacy/solvency unchanged
    assert board["trading_safe_total"] == 0    # trader refuses to fund from B2
    assert board["emergency_complete_total"] == 8_000_000


def test_search_reports_no_full_lineup_simulations() -> None:
    install_fixture()
    board = engine.build_safe_liquidity_portfolio(
        {"my_team": []},
        {"offers": [offer("starter", 2, 8_000_000)]},
        {"players": []},
    )
    assert board["search"]["full_lineup_simulations"] == 0
    assert board["search"]["method"] == "FAST_POSITIONAL_BEAM_V10.2.2"
    assert board["search"]["sporting_extension"] == "V10.3_B1"


def main() -> None:
    tests = [
        test_b1_excludes_complete_xi_with_excessive_sporting_loss,
        test_b1_preserves_legacy_tier_b_for_emergency_compatibility,
        test_search_reports_no_full_lineup_simulations,
    ]
    try:
        for test in tests:
            test()
            print(f"OK  {test.__name__}")
        print("SPORTING SAFE DEBT B1 V10.3: OK")
    finally:
        restore_fixture()


if __name__ == "__main__":
    main()
