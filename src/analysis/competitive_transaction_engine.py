from __future__ import annotations

from typing import Any


OBSERVER_ONLY = True

FRANCHISE_NEVER_SELL_THRESHOLD = 70.0
DIRECT_RIVAL_THREAT_THRESHOLD = 60.0
VERY_HIGH_RIVAL_THREAT_THRESHOLD = 80.0
POINTS_GAP_DIRECT_THRESHOLD = 50

ROUND_TO = 10_000


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def round_money(value: float | int) -> int:
    return int(round(float(value) / ROUND_TO) * ROUND_TO)


def build_manager_lookup(
    rival_intelligence: dict | None,
) -> dict[int, dict]:
    intelligence = rival_intelligence or {}
    managers = intelligence.get("managers", []) or []

    result: dict[int, dict] = {}

    for manager in managers:
        user_id = safe_int(manager.get("user_id"))

        if user_id > 0:
            result[user_id] = manager

    return result


def find_our_manager(
    rival_intelligence: dict | None,
) -> dict | None:
    intelligence = rival_intelligence or {}

    for manager in intelligence.get("managers", []) or []:
        if manager.get("threat_level") == "US":
            return manager

    return None


def classify_rival_context(
    *,
    rival_user_id: int | None,
    rival_intelligence: dict | None,
) -> dict:
    """
    Devuelve el contexto competitivo del manager rival.

    La etiqueta de rival directo es dinamica:
    - threat_score >= 60, o
    - distancia de puntos pequena cuando los puntos ya discriminan.
    """
    rival_user_id = safe_int(rival_user_id)

    if rival_user_id <= 0:
        return {
            "available": False,
            "user_id": None,
            "name": None,
            "threat_score": 0.0,
            "threat_level": "UNKNOWN",
            "points": 0,
            "points_gap": None,
            "direct_rival": False,
            "balance": 0,
            "maximum_bid": 0,
            "roster_value": 0,
            "market_activity": "UNKNOWN",
            "profile": "UNKNOWN",
        }

    lookup = build_manager_lookup(rival_intelligence)
    rival = lookup.get(rival_user_id)

    if rival is None:
        return {
            "available": False,
            "user_id": rival_user_id,
            "name": None,
            "threat_score": 0.0,
            "threat_level": "UNKNOWN",
            "points": 0,
            "points_gap": None,
            "direct_rival": False,
            "balance": 0,
            "maximum_bid": 0,
            "roster_value": 0,
            "market_activity": "UNKNOWN",
            "profile": "UNKNOWN",
        }

    threat_score = safe_float(rival.get("threat_score"))
    threat_level = str(rival.get("threat_level") or "UNKNOWN")
    rival_points = safe_int(rival.get("points"))

    our_manager = find_our_manager(rival_intelligence)
    points_gap = None
    points_direct = False

    if our_manager is not None:
        our_points = safe_int(our_manager.get("points"))

        # Si todos estan empatados al inicio, points_rank suele ser None.
        ranking_active = (
            our_manager.get("points_rank") is not None
            or rival.get("points_rank") is not None
        )

        if ranking_active:
            points_gap = abs(our_points - rival_points)
            points_direct = points_gap <= POINTS_GAP_DIRECT_THRESHOLD

    direct_rival = bool(
        threat_score >= DIRECT_RIVAL_THREAT_THRESHOLD
        or points_direct
    )

    return {
        "available": True,
        "user_id": rival_user_id,
        "name": rival.get("name"),
        "threat_score": round(threat_score, 1),
        "threat_level": threat_level,
        "points": rival_points,
        "points_gap": points_gap,
        "direct_rival": direct_rival,
        "balance": safe_int(rival.get("balance")),
        "maximum_bid": safe_int(rival.get("maximum_bid")),
        "roster_value": safe_int(rival.get("roster_value")),
        "market_activity": rival.get("market_activity", "UNKNOWN"),
        "profile": rival.get("profile", "UNKNOWN"),
    }


def calculate_our_sale_cost_score(
    *,
    franchise_score: float,
    strategic_score: float,
    sale_score: float,
    speculation_score: float,
    in_lineup: bool,
    price_increment: int,
) -> float:
    """
    0..100. Cuanto mas alto, mas caro nos resulta desprendernos del jugador.
    """
    score = 25.0

    score += clamp(franchise_score) * 0.30
    score += clamp(strategic_score) * 0.18
    score += (100.0 - clamp(sale_score)) * 0.12

    # El valor especulativo futuro es un activo real.
    # Un jugador que hoy no entra en el XI puede ser caro de vender
    # si Pepe espera que se revalorice con fuerza.
    score += clamp(speculation_score) * 0.18

    if speculation_score >= 85:
        score += 8.0
    elif speculation_score >= 70:
        score += 4.0
    elif speculation_score <= 30:
        score -= 3.0

    if in_lineup:
        score += 15.0

    if price_increment >= 100_000:
        score += 8.0
    elif price_increment > 0:
        score += 4.0
    elif price_increment < 0:
        score -= 4.0

    return round(clamp(score), 1)


def calculate_rival_reinforcement_score(
    *,
    rival_context: dict,
    player_quality_score: float,
    speculation_score: float,
    in_our_lineup: bool,
) -> float:
    """
    Proxy conservador de cuanto puede reforzarse el rival.
    En V1 no inventamos su XI exacto: usamos amenaza + calidad del activo.
    """
    threat = safe_float(rival_context.get("threat_score"))
    quality = clamp(player_quality_score)
    speculation = clamp(speculation_score)

    # Deportivo + amenaza del manager + potencial especulativo.
    # La especulacion pesa de forma explicita porque un rival puede
    # estar comprando hoy una futura plusvalia que Pepe tambien detecta.
    score = (
        quality * 0.45
        + threat * 0.30
        + speculation * 0.25
    )

    if speculation >= 85:
        score += 8.0
    elif speculation >= 70:
        score += 4.0

    if rival_context.get("direct_rival"):
        score += 7.0

    if in_our_lineup:
        score += 3.0

    return round(clamp(score), 1)


def calculate_base_sell_price(
    *,
    market_value: int,
    our_sale_cost_score: float,
    price_increment: int,
) -> int:
    market_value = max(safe_int(market_value), 0)

    if market_value <= 0:
        return 0

    # 0..25% de prima por coste interno de desprendernos del activo.
    internal_premium = clamp(our_sale_cost_score) / 100.0 * 0.25

    trend_premium = 0.0

    if price_increment >= 100_000:
        trend_premium = 0.04
    elif price_increment > 0:
        trend_premium = 0.02

    return round_money(
        market_value * (1.0 + internal_premium + trend_premium)
    )


def calculate_competitive_sale_premium_percent(
    *,
    rival_context: dict,
    rival_reinforcement_score: float,
) -> float:
    """
    Prima adicional que exigimos por vender a ESE rival.
    Maximo deliberadamente acotado en V1 observer.
    """
    threat = safe_float(rival_context.get("threat_score"))

    premium = threat * 0.10
    premium += clamp(rival_reinforcement_score) * 0.08

    if rival_context.get("direct_rival"):
        premium += 5.0

    if threat >= VERY_HIGH_RIVAL_THREAT_THRESHOLD:
        premium += 2.0

    return round(min(max(premium, 0.0), 22.0), 2)


def evaluate_sale_to_rival(
    *,
    amount: int,
    market_value: int,
    rival_user_id: int | None,
    rival_intelligence: dict | None,
    franchise_score: float = 0.0,
    strategic_score: float = 0.0,
    sale_score: float = 50.0,
    speculation_score: float = 50.0,
    in_lineup: bool = False,
    price_increment: int = 0,
) -> dict:
    """
    Evalua una oferta de un manager por un jugador nuestro.

    Observer only:
    ACCEPT_NOW / COUNTER_OFFER / REJECT_RIVAL_REINFORCEMENT / HOLD_OFFER.
    """
    amount = safe_int(amount)
    market_value = safe_int(market_value)

    rival_context = classify_rival_context(
        rival_user_id=rival_user_id,
        rival_intelligence=rival_intelligence,
    )

    our_sale_cost_score = calculate_our_sale_cost_score(
        franchise_score=franchise_score,
        strategic_score=strategic_score,
        sale_score=sale_score,
        speculation_score=speculation_score,
        in_lineup=in_lineup,
        price_increment=price_increment,
    )

    player_quality_score = max(
        clamp(franchise_score),
        clamp(strategic_score),
        100.0 - clamp(sale_score),
    )

    rival_reinforcement_score = calculate_rival_reinforcement_score(
        rival_context=rival_context,
        player_quality_score=player_quality_score,
        speculation_score=speculation_score,
        in_our_lineup=in_lineup,
    )

    base_sell_price = calculate_base_sell_price(
        market_value=market_value,
        our_sale_cost_score=our_sale_cost_score,
        price_increment=price_increment,
    )

    competitive_premium_percent = (
        calculate_competitive_sale_premium_percent(
            rival_context=rival_context,
            rival_reinforcement_score=rival_reinforcement_score,
        )
        if rival_context.get("available")
        else 0.0
    )

    strategic_sell_price = round_money(
        base_sell_price * (1.0 + competitive_premium_percent / 100.0)
    )

    reasons: list[str] = []

    if franchise_score >= FRANCHISE_NEVER_SELL_THRESHOLD:
        decision = "NEVER_SELL"
        counter_amount = None
        reasons.append(
            "Jugador Franchise/NEVER_SELL: la negociacion queda bloqueada."
        )

    elif market_value <= 0:
        decision = "HOLD_OFFER"
        counter_amount = None
        reasons.append(
            "No existe valor de mercado fiable para fijar un precio estrategico."
        )

    elif amount >= strategic_sell_price:
        decision = "ACCEPT_NOW"
        counter_amount = None
        reasons.append(
            "La oferta ya compensa el coste interno y el coste competitivo de reforzar al rival."
        )

    elif amount >= base_sell_price:
        decision = "COUNTER_OFFER"
        counter_amount = strategic_sell_price
        reasons.append(
            "La oferta compensa nuestro coste base, pero no la prima competitiva exigible a este rival."
        )

    elif (
        rival_context.get("direct_rival")
        and rival_reinforcement_score >= 60
    ):
        decision = "REJECT_RIVAL_REINFORCEMENT"
        counter_amount = None
        reasons.append(
            "Precio insuficiente para entregar un activo relevante a un rival directo."
        )

    else:
        decision = "HOLD_OFFER"
        counter_amount = None
        reasons.append(
            "La oferta todavia no alcanza el precio minimo interno de venta."
        )

    if rival_context.get("direct_rival"):
        reasons.append("Rival directo dinamico: SI.")

    reasons.append(
        f"Threat rival: {safe_float(rival_context.get('threat_score')):.1f}/100."
    )
    reasons.append(
        f"Speculation jugador: {clamp(speculation_score):.1f}/100."
    )
    reasons.append(
        f"Refuerzo rival estimado: {rival_reinforcement_score:.1f}/100."
    )

    return {
        "observer_only": OBSERVER_ONLY,
        "direction": "RIVAL_BUYS_FROM_US",
        "decision": decision,
        "amount": amount,
        "market_value": market_value,
        "base_sell_price": base_sell_price,
        "competitive_premium_percent": competitive_premium_percent,
        "strategic_sell_price": strategic_sell_price,
        "counter_amount": counter_amount,
        "our_sale_cost_score": our_sale_cost_score,
        "speculation_score": round(clamp(speculation_score), 1),
        "rival_reinforcement_score": rival_reinforcement_score,
        "rival": rival_context,
        "reasons": reasons,
    }


def calculate_purchase_value_score(
    *,
    player_score: float,
    lineup_need_score: float,
    speculation_score: float,
) -> float:
    return round(
        clamp(
            clamp(player_score) * 0.55
            + clamp(lineup_need_score) * 0.30
            + clamp(speculation_score) * 0.15
        ),
        1,
    )


def calculate_rival_damage_score(
    *,
    rival_context: dict,
    player_score: float,
) -> float:
    threat = safe_float(rival_context.get("threat_score"))

    score = clamp(player_score) * 0.60
    score += threat * 0.25

    if rival_context.get("direct_rival"):
        score += 10.0

    return round(clamp(score), 1)


def calculate_liquidity_help_score(
    *,
    price: int,
    rival_context: dict,
) -> float:
    """
    Cuanto ayudamos al vendedor al entregarle liquidez.
    Se compara con su saldo y capacidad de puja estimada.
    """
    price = max(safe_int(price), 0)
    balance = safe_int(rival_context.get("balance"))
    maximum_bid = max(safe_int(rival_context.get("maximum_bid")), 0)

    if price <= 0:
        return 0.0

    score = 0.0

    if balance < 0:
        deficit = abs(balance)
        score += min(price / max(deficit, 1) * 45.0, 45.0)

    if maximum_bid > 0:
        score += min(price / maximum_bid * 30.0, 30.0)
    else:
        score += 10.0

    score += safe_float(rival_context.get("threat_score")) * 0.15

    return round(clamp(score), 1)


def calculate_strategic_max_purchase_price(
    *,
    market_value: int,
    purchase_value_score: float,
    rival_damage_score: float,
    liquidity_help_score: float,
) -> int:
    market_value = max(safe_int(market_value), 0)

    if market_value <= 0:
        return 0

    # Valor propio permite hasta +20%.
    own_premium = clamp(purchase_value_score) / 100.0 * 0.20

    # Debilitar rival permite hasta +10%.
    damage_premium = clamp(rival_damage_score) / 100.0 * 0.10

    # Dar liquidez resta hasta 12%.
    liquidity_penalty = clamp(liquidity_help_score) / 100.0 * 0.12

    multiplier = 1.0 + own_premium + damage_premium - liquidity_penalty

    # Guardarrail observer V1.
    multiplier = max(0.90, min(multiplier, 1.30))

    return round_money(market_value * multiplier)


def evaluate_purchase_from_rival(
    *,
    proposed_price: int,
    market_value: int,
    rival_user_id: int | None,
    rival_intelligence: dict | None,
    player_score: float,
    lineup_need_score: float = 50.0,
    speculation_score: float = 50.0,
    negotiation_round: int = 1,
    our_last_offer: int | None = None,
    is_rival_counter: bool = False,
) -> dict:
    """
    Evalua comprar un jugador a otro manager.

    Si is_rival_counter=True, proposed_price es la contraoferta que
    nos acaba de hacer el rival. La operacion se recalcula desde cero.
    """
    proposed_price = safe_int(proposed_price)
    market_value = safe_int(market_value)

    rival_context = classify_rival_context(
        rival_user_id=rival_user_id,
        rival_intelligence=rival_intelligence,
    )

    purchase_value_score = calculate_purchase_value_score(
        player_score=player_score,
        lineup_need_score=lineup_need_score,
        speculation_score=speculation_score,
    )

    rival_damage_score = calculate_rival_damage_score(
        rival_context=rival_context,
        player_score=player_score,
    )

    liquidity_help_score = calculate_liquidity_help_score(
        price=proposed_price,
        rival_context=rival_context,
    )

    strategic_max_price = calculate_strategic_max_purchase_price(
        market_value=market_value,
        purchase_value_score=purchase_value_score,
        rival_damage_score=rival_damage_score,
        liquidity_help_score=liquidity_help_score,
    )

    reasons: list[str] = []

    if market_value <= 0:
        decision = "WALK_AWAY" if is_rival_counter else "NO_OFFER"
        our_counter_amount = None
        reasons.append(
            "Sin valor de mercado fiable no se autoriza escalar una negociacion."
        )

    elif proposed_price <= strategic_max_price:
        if is_rival_counter:
            decision = "ACCEPT_COUNTER"
            our_counter_amount = None
            reasons.append(
                "La contraoferta rival sigue dentro de nuestro precio maximo estrategico recalculado."
            )
        else:
            decision = "OFFER"
            our_counter_amount = proposed_price
            reasons.append(
                "La puja propuesta esta dentro del precio maximo estrategico."
            )

    elif (
        is_rival_counter
        and strategic_max_price > 0
        and proposed_price > strategic_max_price * 1.15
    ):
        decision = "WALK_AWAY"
        our_counter_amount = None
        reasons.append(
            "La contraoferta se aleja mas de un 15% de nuestro maximo estrategico; no se entra en escalada."
        )

    elif (
        is_rival_counter
        and our_last_offer is not None
        and safe_int(our_last_offer) < strategic_max_price
        and negotiation_round <= 3
    ):
        decision = "COUNTER_AGAIN"
        our_counter_amount = strategic_max_price
        reasons.append(
            "El precio pedido supera nuestro maximo, pero aun queda margen para una ultima contraoferta disciplinada."
        )

    else:
        decision = "WALK_AWAY" if is_rival_counter else "NO_OFFER"
        our_counter_amount = None
        reasons.append(
            "El precio supera el maximo estrategico; Pepe no persigue al vendedor."
        )

    if rival_context.get("direct_rival"):
        reasons.append("Rival directo dinamico: SI.")

    reasons.append(
        f"Valor de compra Pepe: {purchase_value_score:.1f}/100."
    )
    reasons.append(
        f"Dano deportivo rival estimado: {rival_damage_score:.1f}/100."
    )
    reasons.append(
        f"Ayuda de liquidez al rival: {liquidity_help_score:.1f}/100."
    )

    return {
        "observer_only": OBSERVER_ONLY,
        "direction": "WE_BUY_FROM_RIVAL",
        "decision": decision,
        "proposed_price": proposed_price,
        "market_value": market_value,
        "strategic_max_price": strategic_max_price,
        "our_counter_amount": our_counter_amount,
        "purchase_value_score": purchase_value_score,
        "rival_damage_score": rival_damage_score,
        "liquidity_help_score": liquidity_help_score,
        "negotiation_round": safe_int(negotiation_round, 1),
        "is_rival_counter": bool(is_rival_counter),
        "our_last_offer": (
            safe_int(our_last_offer)
            if our_last_offer is not None
            else None
        ),
        "rival": rival_context,
        "reasons": reasons,
    }


def extract_counterparty_from_offer(
    offer: dict,
) -> dict:
    """
    Compatibilidad con dos estructuras:
    - offer['counterparty'] generado por offer_analyzer
    - offer['raw_offer']['counterparty'] de estructuras antiguas
    """
    direct = offer.get("counterparty")

    if isinstance(direct, dict):
        return direct

    raw_offer = offer.get("raw_offer", {}) or {}
    nested = raw_offer.get("counterparty")

    if isinstance(nested, dict):
        return nested

    return {}


def extract_seller_user_id(
    player: dict,
) -> int | None:
    """
    Busca de forma defensiva el propietario/vendedor en estructuras
    de mercado conocidas o futuras. Si no esta disponible, no inventa.
    """
    direct_keys = (
        "seller_user_id",
        "sellerUserID",
        "owner_user_id",
        "ownerUserID",
    )

    for key in direct_keys:
        value = safe_int(player.get(key))
        if value > 0:
            return value

    object_keys = (
        "seller",
        "owner",
        "market_owner",
        "user",
        "from",
    )

    for key in object_keys:
        value = player.get(key)

        if isinstance(value, dict):
            user_id = safe_int(value.get("id"))
            if user_id > 0:
                return user_id

    return None
