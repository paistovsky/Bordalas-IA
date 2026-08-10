from src.analysis.price_humanizer import (
    humanize_sale_price,
)


def round_price(
    price: int,
    step: int = 10_000,
) -> int:

    if price <= 0:
        return 0

    return (
        ((price + step - 1) // step)
        * step
    )


def calculate_sale_price(
    player: dict,
) -> dict:

    market_value = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    sale_score = int(
        player.get(
            "sale_score",
            0,
        )
        or 0
    )

    in_lineup = bool(
        player.get(
            "in_lineup",
            False,
        )
    )

    player_id = int(
        player["id"]
    )

    # ==================================================
    # PROTECCIÓN DE JUGADORES IMPORTANTES
    # ==================================================

    if sale_score < 40:

        return {
            "should_list":
                False,

            "market_value":
                market_value,

            "sale_score":
                sale_score,

            "multiplier":
                None,

            "base_recommended_price":
                None,

            "recommended_price":
                None,

            "strategy":
                "NO LISTAR",

            "reason": (
                "Jugador demasiado importante "
                "para ponerlo en mercado."
            ),
        }

    # ==================================================
    # PRIMA SEGÚN PRESCINDIBILIDAD
    # ==================================================

    if sale_score >= 80:

        multiplier = 1.02
        strategy = "VENTA RÁPIDA"

    elif sale_score >= 70:

        multiplier = 1.05
        strategy = "VENDER"

    elif sale_score >= 60:

        multiplier = 1.10
        strategy = "VENDER CON MARGEN"

    elif sale_score >= 50:

        multiplier = 1.15
        strategy = "ESCUCHAR OFERTAS"

    else:

        multiplier = 1.25
        strategy = "SOLO OFERTA ALTA"

    # Si está entrando en nuestro XI,
    # exigimos una prima todavía mayor.
    if in_lineup:
        multiplier += 0.10

    raw_price = int(
        market_value
        * multiplier
    )

    base_recommended_price = (
        round_price(
            raw_price
        )
    )

    # ==================================================
    # PRECIO MENOS MECÁNICO
    # ==================================================

    recommended_price = (
        humanize_sale_price(
            player_id=player_id,
            target_price=
                base_recommended_price,
            market_value=
                market_value,
        )
    )

    premium = (
        recommended_price
        - market_value
    )

    premium_percent = (
        (
            premium
            / market_value
        )
        * 100
        if market_value > 0
        else 0
    )

    return {
        "should_list":
            True,

        "market_value":
            market_value,

        "sale_score":
            sale_score,

        "multiplier":
            multiplier,

        "base_recommended_price":
            base_recommended_price,

        "recommended_price":
            recommended_price,

        "premium":
            premium,

        "premium_percent":
            premium_percent,

        "strategy":
            strategy,

        "reason": (
            "Precio estratégico con una "
            "pequeña variación controlada."
        ),
    }