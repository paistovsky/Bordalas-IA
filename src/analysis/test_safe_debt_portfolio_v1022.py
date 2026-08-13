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


def fake_prepared_roster() -> list[dict]:
    # 4-4-2 fijo para tests:
    # 1 POR, 5 DEF, 5 MED, 4 DEL = 15 jugadores seguros.
    players = [prepared_player(1, 1, 100)]
    players += [prepared_player(i, 2, 100 - i) for i in range(2, 7)]
    players += [prepared_player(i, 3, 100 - i) for i in range(7, 12)]
    players += [prepared_player(i, 4, 100 - i) for i in range(12, 16)]
    return players


def install_fast_fixture() -> None:
    engine.FORMATIONS = {"4-4-2": {1: 1, 2: 4, 3: 4, 4: 2}}
    engine.prepare_players = lambda snapshot: fake_prepared_roster()


def restore_fixture() -> None:
    engine.FORMATIONS = ORIGINAL_FORMATIONS
    engine.prepare_players = ORIGINAL_PREPARE


def fake_snapshot() -> dict:
    return {"my_team": [{"id": i, "name": f"P{i}"} for i in range(1, 16)]}


def offer(offer_id: str, player_id: int, amount: int) -> dict:
    return {
        "offer_id": offer_id,
        "amount": amount,
        "player_ids": [player_id],
        "players": [{"id": player_id, "name": f"P{player_id}"}],
    }


def listing(player_id: int, amount: int) -> dict:
    return {
        "id": player_id,
        "name": f"P{player_id}",
        "expected_liquidity": amount,
        "haircut": 0.78,
    }


def test_tier_a_sums_bench_liquidity_without_touching_xi() -> None:
    install_fast_fixture()
    # DEF 6 y MED 11 son banquillo con el roster ordenado por score.
    board = engine.build_safe_liquidity_portfolio(
        fake_snapshot(),
        {"offers": [offer("o6", 6, 2_000_000)]},
        {"players": [listing(11, 1_000_000)]},
    )
    assert board["gross_source_total"] == 3_000_000
    assert board["tier_a"]["amount"] == 3_000_000
    assert board["usable_total"] == 3_000_000
    assert board["tier_b"]["starters_sold"] == 0


def test_joint_validation_blocks_overestimated_starter_sales() -> None:
    install_fast_fixture()
    # Hay 5 DEF. Vender uno de los 4 titulares mantiene 4 defensas;
    # vender dos deja solo 3 => XI 10/11.
    board = engine.build_safe_liquidity_portfolio(
        fake_snapshot(),
        {"offers": [
            offer("o2", 2, 8_000_000),
            offer("o3", 3, 7_000_000),
        ]},
        {"players": []},
    )
    assert board["gross_source_total"] == 15_000_000
    assert board["tier_b"]["amount"] == 8_000_000
    assert board["tier_c"]["amount"] == 15_000_000
    assert board["usable_total"] == 8_000_000


def test_tier_c_never_funds_normal_safe_debt() -> None:
    install_fast_fixture()
    # Portero unico: venderlo deja XI 10/11.
    board = engine.build_safe_liquidity_portfolio(
        fake_snapshot(),
        {"offers": [offer("o1", 1, 9_000_000)]},
        {"players": []},
    )
    assert board["tier_b"]["amount"] == 0
    assert board["tier_c"]["amount"] == 9_000_000
    assert board["usable_total"] == 0
    assert len(board["individually_blocked_by_lineup"]) == 1


def test_overlapping_sources_cannot_sell_same_player_twice() -> None:
    install_fast_fixture()
    board = engine.build_safe_liquidity_portfolio(
        fake_snapshot(),
        {"offers": [offer("o6", 6, 2_000_000)]},
        {"players": [listing(6, 1_500_000)]},
    )
    assert board["source_count"] == 1
    assert board["gross_source_total"] == 2_000_000
    assert board["usable_total"] == 2_000_000


def test_selected_portfolio_preserves_secured_expected_breakdown() -> None:
    install_fast_fixture()
    board = engine.build_safe_liquidity_portfolio(
        fake_snapshot(),
        {"offers": [offer("o6", 6, 2_000_000)]},
        {"players": [listing(11, 1_000_000)]},
    )
    assert board["usable_secured_total"] == 2_000_000
    assert board["usable_expected_total"] == 1_000_000
    assert board["selected_offer_ids"] == ["o6"]


def test_fast_path_never_calls_full_lineup_simulation() -> None:
    install_fast_fixture()
    sources = [offer(f"o{i}", i, 1_000_000 + i) for i in range(2, 7)]
    board = engine.build_safe_liquidity_portfolio(
        fake_snapshot(),
        {"offers": sources},
        {"players": [listing(i, 500_000 + i) for i in range(7, 12)]},
    )
    search = board["search"]
    assert search["method"] == "FAST_POSITIONAL_BEAM_V10.2.2"
    assert search["full_lineup_simulations"] == 0
    assert search["fast_projections"] > 0


def main() -> None:
    tests = [
        test_tier_a_sums_bench_liquidity_without_touching_xi,
        test_joint_validation_blocks_overestimated_starter_sales,
        test_tier_c_never_funds_normal_safe_debt,
        test_overlapping_sources_cannot_sell_same_player_twice,
        test_selected_portfolio_preserves_secured_expected_breakdown,
        test_fast_path_never_calls_full_lineup_simulation,
    ]
    try:
        for test in tests:
            test()
            print(f"OK  {test.__name__}")
        print("SAFE DEBT PORTFOLIO V10.2.2 FAST: OK")
    finally:
        restore_fixture()


if __name__ == "__main__":
    main()
