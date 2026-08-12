from __future__ import annotations

from src.analysis.competitive_transaction_engine import (
    evaluate_purchase_from_rival,
    evaluate_sale_to_rival,
)


def fake_intelligence() -> dict:
    return {
        "managers": [
            {
                "user_id": 1,
                "name": "Pepe",
                "points": 500,
                "points_rank": 1,
                "threat_score": None,
                "threat_level": "US",
                "balance": 2_000_000,
                "maximum_bid": 12_000_000,
                "roster_value": 80_000_000,
            },
            {
                "user_id": 2,
                "name": "Pollo17",
                "points": 490,
                "points_rank": 2,
                "threat_score": 88.0,
                "threat_level": "VERY_HIGH",
                "balance": -4_000_000,
                "maximum_bid": 9_000_000,
                "roster_value": 78_000_000,
                "market_activity": "VERY_HIGH",
                "profile": "AGGRESSIVE",
            },
            {
                "user_id": 3,
                "name": "Rival Medio",
                "points": 350,
                "points_rank": 6,
                "threat_score": 45.0,
                "threat_level": "MEDIUM",
                "balance": 4_000_000,
                "maximum_bid": 11_000_000,
                "roster_value": 60_000_000,
                "market_activity": "MEDIUM",
                "profile": "BALANCED",
            },
            {
                "user_id": 4,
                "name": "Rival Debil",
                "points": 150,
                "points_rank": 10,
                "threat_score": 12.0,
                "threat_level": "VERY_LOW",
                "balance": 6_000_000,
                "maximum_bid": 8_000_000,
                "roster_value": 35_000_000,
                "market_activity": "LOW",
                "profile": "INACTIVE",
            },
        ]
    }


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    intelligence = fake_intelligence()

    print("=" * 100)
    print("BORDALAS IA - COMPETITIVE TRANSACTIONS V1")
    print("=" * 100)

    # 1. Franchise nunca se vende.
    franchise = evaluate_sale_to_rival(
        amount=20_000_000,
        market_value=10_000_000,
        rival_user_id=4,
        rival_intelligence=intelligence,
        franchise_score=85,
        strategic_score=90,
        sale_score=10,
        in_lineup=True,
        price_increment=100_000,
    )
    assert_true(
        franchise["decision"] == "NEVER_SELL",
        "Franchise deberia quedar protegido.",
    )

    # 2. Rival directo: oferta suficiente para nosotros pero no para reforzarle => counter.
    direct_counter = evaluate_sale_to_rival(
        amount=10_500_000,
        market_value=9_000_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        franchise_score=40,
        strategic_score=72,
        sale_score=55,
        in_lineup=False,
        price_increment=50_000,
    )
    assert_true(
        direct_counter["decision"] in {"COUNTER_OFFER", "REJECT_RIVAL_REINFORCEMENT"},
        "Un rival directo no debe llevarse barato un activo relevante.",
    )

    # 3. Oferta extraordinaria por activo vendible => aceptar.
    extraordinary = evaluate_sale_to_rival(
        amount=8_500_000,
        market_value=6_000_000,
        rival_user_id=4,
        rival_intelligence=intelligence,
        franchise_score=10,
        strategic_score=35,
        sale_score=85,
        in_lineup=False,
        price_increment=-20_000,
    )
    assert_true(
        extraordinary["decision"] == "ACCEPT_NOW",
        "Una oferta extraordinaria de rival debil deberia aceptarse.",
    )

    # 4. Jugador barato con gran speculation: no regalar futura plusvalia.
    low_spec = evaluate_sale_to_rival(
        amount=2_300_000,
        market_value=2_000_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        franchise_score=5,
        strategic_score=30,
        sale_score=80,
        speculation_score=20,
        in_lineup=False,
        price_increment=0,
    )

    high_spec = evaluate_sale_to_rival(
        amount=2_300_000,
        market_value=2_000_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        franchise_score=5,
        strategic_score=30,
        sale_score=80,
        speculation_score=95,
        in_lineup=False,
        price_increment=0,
    )

    assert_true(
        high_spec["strategic_sell_price"] > low_spec["strategic_sell_price"],
        "Un gran speculation_score debe elevar el precio estrategico de venta.",
    )

    assert_true(
        high_spec["rival_reinforcement_score"] > low_spec["rival_reinforcement_score"],
        "Un gran speculation_score debe aumentar el beneficio potencial del rival.",
    )

    # 5. Compra a rival directo: puede justificar prima por dano deportivo.
    buy_direct = evaluate_purchase_from_rival(
        proposed_price=8_000_000,
        market_value=7_500_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        player_score=90,
        lineup_need_score=85,
        speculation_score=55,
    )
    assert_true(
        buy_direct["strategic_max_price"] >= 7_500_000,
        "Quitar un gran jugador a rival directo puede justificar pagar prima.",
    )

    # 6. Dar liquidez a rival directo endeudado debe penalizar.
    liquidity = evaluate_purchase_from_rival(
        proposed_price=6_000_000,
        market_value=5_000_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        player_score=45,
        lineup_need_score=30,
        speculation_score=55,
    )
    assert_true(
        liquidity["liquidity_help_score"] > 0,
        "Debe detectar que estamos dando liquidez al rival.",
    )

    # 7. Contraoferta rival dentro de nuestro maximo => aceptar.
    probe = evaluate_purchase_from_rival(
        proposed_price=8_200_000,
        market_value=8_000_000,
        rival_user_id=3,
        rival_intelligence=intelligence,
        player_score=82,
        lineup_need_score=80,
        speculation_score=50,
        negotiation_round=2,
        our_last_offer=7_800_000,
        is_rival_counter=True,
    )
    assert_true(
        probe["decision"] in {"ACCEPT_COUNTER", "COUNTER_AGAIN", "WALK_AWAY"},
        "La contraoferta debe producir una decision explicita.",
    )

    # 8. Precio absurdo: nunca perseguir al vendedor.
    walk = evaluate_purchase_from_rival(
        proposed_price=15_000_000,
        market_value=8_000_000,
        rival_user_id=2,
        rival_intelligence=intelligence,
        player_score=92,
        lineup_need_score=95,
        speculation_score=60,
        negotiation_round=3,
        our_last_offer=9_000_000,
        is_rival_counter=True,
    )
    assert_true(
        walk["decision"] == "WALK_AWAY",
        "Pepe debe retirarse si el precio supera claramente su maximo.",
    )

    assert_true(
        walk["our_counter_amount"] is None
        or walk["our_counter_amount"] <= walk["strategic_max_price"],
        "Nunca se puede contraofertar por encima del maximo estrategico.",
    )

    print()
    print("VENTA A RIVAL DIRECTO")
    print(direct_counter)
    print()
    print("SPECULATION - MISMO JUGADOR / MISMA OFERTA")
    print("LOW SPEC:", low_spec)
    print("HIGH SPEC:", high_spec)
    print()
    print("COMPRA A RIVAL DIRECTO")
    print(buy_direct)
    print()
    print("CONTRAOFERTA / WALK AWAY")
    print(walk)
    print()
    print("# COMPETITIVE TRANSACTIONS V1: OK")


if __name__ == "__main__":
    main()
