from __future__ import annotations

import copy

from src.analysis.accept_before_expiry_safety_engine import (
    revalidate_accept_before_expiry_cluster,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)


def safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def resolve_raw_offer_id(
    raw_offer: dict,
) -> int | None:

    for key in ("id", "offer_id"):
        value = raw_offer.get(key)

        if value is None:
            continue

        try:
            return int(value)
        except (TypeError, ValueError):
            continue

    return None


def calculate_sale_damage(
    decision: dict,
) -> float:
    """
    Menor = mejor candidato para una venta forzada.

    Nunca permite NEVER_SELL / NEVER_AUTO_SELL.
    """

    if (
        decision.get("decision") == "NEVER_SELL"
        or
        decision.get("protection") == "NEVER_AUTO_SELL"
    ):
        return 1_000_000.0

    damage = 100.0

    damage += float(
        decision.get("franchise_score", 0)
        or 0
    ) * 4.0

    damage += float(
        decision.get("strategic_score", 0)
        or 0
    ) * 1.5

    if decision.get("in_lineup", False):
        damage += 80.0

    speculation_score = float(
        decision.get("speculation_score", 50)
        or 50
    )

    if speculation_score >= 70:
        damage += 60.0
    elif speculation_score >= 60:
        damage += 35.0

    sale_score = float(
        decision.get("sale_score", 0)
        or 0
    )

    damage -= sale_score * 1.2

    premium = float(
        decision.get("premium_percent", 0)
        or 0
    )

    damage -= max(
        min(premium, 15.0),
        -10.0,
    ) * 2.0

    speculation_action = str(
        decision.get("speculation_action", "")
        or ""
    )

    if speculation_action.startswith("SELL"):
        damage -= 45.0

    return round(damage, 2)


def simulate_accept_one_and_lose_rest(
    snapshot: dict,
    cluster: dict,
    selected_offer: dict,
) -> dict:
    """
    Escenario conservador:
    aceptamos UNA oferta y suponemos que todas las demas
    ofertas del mismo cluster desaparecen.

    Se usa solo para medir cuanto protege esa venta.
    No escribe en Biwenger.
    """

    simulated = copy.deepcopy(snapshot)

    cluster_offer_ids = {
        safe_int(offer_id)
        for offer_id in (
            cluster.get("offer_ids", [])
            or []
        )
        if safe_int(offer_id) > 0
    }

    selected_offer_id = safe_int(
        selected_offer.get("offer_id")
    )

    if (
        selected_offer_id <= 0
        or selected_offer_id not in cluster_offer_ids
    ):
        return {
            "valid": False,
            "guaranteed_after": False,
            "surplus_after": -10**18,
        }

    market = simulated.setdefault(
        "market",
        {},
    )

    kept_offers = []

    for raw_offer in (
        market.get("offers", [])
        or []
    ):
        raw_id = resolve_raw_offer_id(
            raw_offer
        )

        if (
            raw_id is not None
            and raw_id in cluster_offer_ids
        ):
            continue

        kept_offers.append(raw_offer)

    market["offers"] = kept_offers

    amount = safe_int(
        selected_offer.get("amount")
    )

    status = market.setdefault(
        "status",
        {},
    )

    status["balance"] = (
        safe_int(status.get("balance"))
        + amount
    )

    sold_player_ids = {
        safe_int(player_id)
        for player_id in (
            selected_offer.get("player_ids", [])
            or []
        )
        if safe_int(player_id) > 0
    }

    if not sold_player_ids:
        return {
            "valid": False,
            "guaranteed_after": False,
            "surplus_after": -10**18,
        }

    simulated["my_team"] = [
        player
        for player in (
            simulated.get("my_team", [])
            or []
        )
        if safe_int(player.get("id"))
        not in sold_player_ids
    ]

    market["sales"] = [
        sale
        for sale in (
            market.get("sales", [])
            or []
        )
        if safe_int(
            (
                sale.get("player", {})
                or {}
            ).get("id")
        )
        not in sold_player_ids
    ]

    solvency_after = build_solvency_state(
        simulated
    )

    guarantee = (
        solvency_after.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    return {
        "valid": True,
        "guaranteed_after": bool(
            guarantee.get("guaranteed", False)
        ),
        "state_after": guarantee.get("state"),
        "surplus_after": safe_int(
            guarantee.get("guarantee_surplus")
        ),
        "required_recovery": safe_int(
            guarantee.get("required_recovery")
        ),
        "accepted_cash": amount,
    }


def select_emergency_accept_offer(
    snapshot: dict,
    offer_ids: set[int] | list[int],
) -> dict:
    """
    Selector LIVE ligero.

    NO hace busqueda combinatoria.

    Flujo:
    1. revalida el cluster completo;
    2. bloquea protegidos;
    3. simula cada venta individual;
    4. si una sola venta resuelve el peor caso, elige la de
       menor daño;
    5. si ninguna basta sola, elige el mejor progreso por
       daño por millon. El siguiente ciclo recalculara TODO.

    Esta funcion nunca escribe.
    """

    validation = (
        revalidate_accept_before_expiry_cluster(
            snapshot=snapshot,
            offer_ids=offer_ids,
        )
    )

    if not validation.get(
        "authorized",
        False,
    ):
        return {
            "ready": False,
            "status": validation.get(
                "status",
                "NOT_AUTHORIZED",
            ),
            "reason": validation.get(
                "reason",
                "Aceptacion no autorizada.",
            ),
            "selected": None,
            "candidates": [],
            "revalidation": validation,
        }

    cluster = (
        validation.get("cluster", {})
        or {}
    )

    decision_board = (
        build_offer_decision_board(
            snapshot
        )
    )

    decisions_by_offer_id = {
        safe_int(item.get("offer_id")): item
        for item in (
            decision_board.get(
                "decisions",
                [],
            )
            or []
        )
        if safe_int(item.get("offer_id")) > 0
    }

    candidates = []

    for offer in (
        cluster.get("offers", [])
        or []
    ):

        offer_id = safe_int(
            offer.get("offer_id")
        )

        player_ids = [
            safe_int(player_id)
            for player_id in (
                offer.get("player_ids", [])
                or []
            )
            if safe_int(player_id) > 0
        ]

        if (
            offer_id <= 0
            or len(player_ids) != 1
        ):
            continue

        decision = (
            decisions_by_offer_id.get(
                offer_id,
                {},
            )
            or {}
        )

        protected = bool(
            decision.get("decision") == "NEVER_SELL"
            or
            decision.get("protection") == "NEVER_AUTO_SELL"
        )

        if protected:
            continue

        damage = calculate_sale_damage(
            decision
        )

        simulation = (
            simulate_accept_one_and_lose_rest(
                snapshot=snapshot,
                cluster=cluster,
                selected_offer=offer,
            )
        )

        amount = safe_int(
            offer.get("amount")
        )

        amount_m = max(
            amount / 1_000_000,
            0.10,
        )

        damage_per_million = (
            damage / amount_m
        )

        players = (
            offer.get("players", [])
            or []
        )

        candidates.append(
            {
                "offer_id": offer_id,
                "player_id": player_ids[0],
                "player_name": (
                    players[0].get("name", "?")
                    if players
                    else "?"
                ),
                "amount": amount,
                "damage_score": damage,
                "damage_per_million": round(
                    damage_per_million,
                    3,
                ),
                "individually_sufficient": bool(
                    simulation.get(
                        "guaranteed_after",
                        False,
                    )
                ),
                "simulation": simulation,
                "offer_decision": decision,
                "offer": offer,
            }
        )

    if not candidates:
        return {
            "ready": False,
            "status": "NO_ELIGIBLE_OFFERS",
            "reason": (
                "No existe ninguna oferta no protegida "
                "apta para venta automatica."
            ),
            "selected": None,
            "candidates": [],
            "revalidation": validation,
        }

    individually_sufficient = [
        item
        for item in candidates
        if item.get(
            "individually_sufficient",
            False,
        )
    ]

    if individually_sufficient:
        individually_sufficient.sort(
            key=lambda item: (
                item["damage_score"],
                -item["amount"],
            )
        )

        selected = individually_sufficient[0]
        status = "SINGLE_ACCEPT_RESOLVES_CLUSTER"
        reason = (
            "Una unica oferta basta para mantener "
            "SOLVENCY_GUARANTEE incluso si desaparece "
            "el resto del cluster."
        )

    else:
        # No intentamos resolver 8191 combinaciones.
        # Vendemos una sola pieza eficiente y el siguiente
        # ciclo vuelve a calcular la situacion completa.
        candidates.sort(
            key=lambda item: (
                item["damage_per_million"],
                item["damage_score"],
                -item["amount"],
            )
        )

        selected = candidates[0]
        status = "STEPWISE_ACCEPT_REQUIRED"
        reason = (
            "Ninguna venta individual resuelve todo el peor caso. "
            "Se autoriza UNA sola venta de bajo daño por millon; "
            "el siguiente ciclo recalculara antes de otra escritura."
        )

    return {
        "ready": True,
        "status": status,
        "reason": reason,
        "selected": selected,
        "candidates": candidates,
        "cluster": cluster,
        "revalidation": validation,
    }
