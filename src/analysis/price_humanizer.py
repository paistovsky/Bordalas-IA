import hashlib


def _deterministic_number(
    key: str,
    minimum: int,
    maximum: int,
) -> int:
    """
    Genera un número pseudoaleatorio determinista.

    Para una misma operación devuelve siempre
    el mismo valor, evitando que cada ejecución
    cambie la puja arbitrariamente.
    """

    if maximum <= minimum:
        return minimum

    digest = hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()

    raw = int(
        digest[:12],
        16,
    )

    return (
        minimum
        + raw
        % (maximum - minimum + 1)
    )


def _avoid_round_number(
    amount: int,
    minimum: int,
    key: str,
) -> int:
    """
    Evita precios demasiado redondos:
    1.570.000 -> 1.563.847, por ejemplo.
    """

    if amount <= minimum:
        return amount

    if amount % 10 != 0:
        return amount

    adjustment = _deterministic_number(
        key=f"{key}:ending",
        minimum=1,
        maximum=9,
    )

    candidate = (
        amount - adjustment
    )

    return max(
        candidate,
        minimum,
    )


def humanize_bid_price(
    player_id: int,
    strategic_max: int,
    market_price: int,
    market_until: int | None = None,
) -> int:
    """
    Humaniza una puja SIN superar nunca
    el máximo estratégico calculado.

    La reducción respecto al máximo está entre
    aproximadamente 0.2% y 1.0%.

    Nunca queda por debajo del precio de salida.
    """

    strategic_max = int(
        strategic_max
    )

    market_price = int(
        market_price
    )

    if strategic_max <= market_price:
        return strategic_max

    seed = (
        f"bid:"
        f"{player_id}:"
        f"{market_until or 0}:"
        f"{strategic_max}"
    )

    basis_points = (
        _deterministic_number(
            key=seed,
            minimum=20,
            maximum=100,
        )
    )

    reduction = int(
        strategic_max
        * basis_points
        / 10_000
    )

    candidate = max(
        strategic_max - reduction,
        market_price,
    )

    candidate = (
        _avoid_round_number(
            amount=candidate,
            minimum=market_price,
            key=seed,
        )
    )

    return min(
        candidate,
        strategic_max,
    )


def humanize_sale_price(
    player_id: int,
    target_price: int,
    market_value: int,
) -> int:
    """
    Introduce una pequeña variación alrededor
    del precio estratégico de publicación.

    Nunca baja del valor Biwenger.

    Variación máxima aproximada:
    +/- 0.75%.
    """

    target_price = int(
        target_price
    )

    market_value = int(
        market_value
    )

    if target_price <= market_value:
        return market_value

    seed = (
        f"sale:"
        f"{player_id}:"
        f"{market_value}:"
        f"{target_price}"
    )

    variation_bp = (
        _deterministic_number(
            key=seed,
            minimum=-75,
            maximum=75,
        )
    )

    variation = int(
        target_price
        * variation_bp
        / 10_000
    )

    candidate = (
        target_price
        + variation
    )

    candidate = max(
        candidate,
        market_value,
    )

    candidate = (
        _avoid_round_number(
            amount=candidate,
            minimum=market_value,
            key=seed,
        )
    )

    return candidate