from __future__ import annotations

import copy
from itertools import combinations

from src.analysis.accept_before_expiry_safety_engine import (
    revalidate_accept_before_expiry_cluster,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)


# ============================================================
# CONFIGURACION
# ============================================================

# Un cluster de 13 ofertas implica 8191 subconjuntos posibles.
# Es perfectamente manejable para un planner Observer.
MAX_COMBINATION_OFFERS = 16


# ============================================================
# HELPERS
# ============================================================


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


def remove_offer_ids(
    snapshot: dict,
    offer_ids: set[int],
) -> set[int]:

    market = snapshot.setdefault(
        "market",
        {},
    )

    offers = market.get(
        "offers",
        [],
    ) or []

    kept = []
    removed = set()

    for raw_offer in offers:

        current_id = resolve_raw_offer_id(
            raw_offer
        )

        if (
            current_id is not None
            and
            current_id in offer_ids
        ):
            removed.add(current_id)
            continue

        kept.append(raw_offer)

    market["offers"] = kept

    return removed


def remove_players_after_sale(
    snapshot: dict,
    player_ids: set[int],
) -> None:

    snapshot["my_team"] = [
        player
        for player in (
            snapshot.get(
                "my_team",
                [],
            )
            or []
        )
        if safe_int(
            player.get("id")
        )
        not in player_ids
    ]

    market = snapshot.setdefault(
        "market",
        {},
    )

    market["sales"] = [
        sale
        for sale in (
            market.get(
                "sales",
                [],
            )
            or []
        )
        if safe_int(
            (
                sale.get(
                    "player",
                    {},
                )
                or {}
            ).get("id")
        )
        not in player_ids
    ]


def add_cash_to_balance(
    snapshot: dict,
    amount: int,
) -> None:

    status = snapshot.setdefault(
        "market",
        {},
    ).setdefault(
        "status",
        {},
    )

    status["balance"] = (
        safe_int(
            status.get("balance")
        )
        + int(amount)
    )


# ============================================================
# COSTE DE VENTA
# ============================================================


def calculate_sale_damage(
    decision: dict,
) -> float:

    if (
        decision.get("decision")
        == "NEVER_SELL"
        or
        decision.get("protection")
        == "NEVER_AUTO_SELL"
    ):
        return 1_000_000.0

    damage = 100.0

    damage += float(
        decision.get(
            "franchise_score",
            0,
        )
        or 0
    ) * 4.0

    damage += float(
        decision.get(
            "strategic_score",
            0,
        )
        or 0
    ) * 1.5

    if decision.get(
        "in_lineup",
        False,
    ):
        damage += 80.0

    speculation_score = float(
        decision.get(
            "speculation_score",
            50,
        )
        or 50
    )

    if speculation_score >= 70:
        damage += 60.0

    elif speculation_score >= 60:
        damage += 35.0

    sale_score = float(
        decision.get(
            "sale_score",
            0,
        )
        or 0
    )

    damage -= sale_score * 1.2

    premium = float(
        decision.get(
            "premium_percent",
            0,
        )
        or 0
    )

    damage -= max(
        min(
            premium,
            15.0,
        ),
        -10.0,
    ) * 2.0

    speculation_action = str(
        decision.get(
            "speculation_action",
            "",
        )
        or ""
    )

    if speculation_action.startswith(
        "SELL"
    ):
        damage -= 45.0

    return round(
        damage,
        2,
    )


# ============================================================
# SIMULACION DE COMBINACION
# ============================================================


def simulate_accept_combination_and_lose_rest(
    snapshot: dict,
    cluster: dict,
    accepted_offers: list[dict],
) -> dict:
    """
    Simula aceptar un subconjunto del cluster y perder
    simultaneamente todas las ofertas restantes del cluster.

    Los jugadores aceptados salen de plantilla y su dinero
    entra en balance. Los no aceptados permanecen en plantilla,
    por lo que pueden volver a producir EXPECTED_LIQUIDITY
    si existen ciclos Computer seguros.
    """

    simulated = copy.deepcopy(
        snapshot
    )

    cluster_offers = (
        cluster.get(
            "offers",
            [],
        )
        or []
    )

    cluster_offer_ids = {
        safe_int(
            offer.get("offer_id")
        )
        for offer in cluster_offers
        if safe_int(
            offer.get("offer_id")
        )
        > 0
    }

    accepted_offer_ids = {
        safe_int(
            offer.get("offer_id")
        )
        for offer in accepted_offers
        if safe_int(
            offer.get("offer_id")
        )
        > 0
    }

    if not accepted_offer_ids:
        return {
            "valid": False,
            "reason": "La combinacion aceptada esta vacia.",
            "guaranteed_after": False,
        }

    if not accepted_offer_ids.issubset(
        cluster_offer_ids
    ):
        return {
            "valid": False,
            "reason": "La combinacion contiene ofertas fuera del cluster.",
            "guaranteed_after": False,
        }

    removed = remove_offer_ids(
        snapshot=simulated,
        offer_ids=cluster_offer_ids,
    )

    if removed != cluster_offer_ids:
        return {
            "valid": False,
            "reason": "No se pudieron retirar todas las ofertas del cluster.",
            "guaranteed_after": False,
        }

    sold_player_ids = set()
    accepted_cash = 0

    for offer in accepted_offers:

        accepted_cash += safe_int(
            offer.get("amount")
        )

        sold_player_ids.update(
            safe_int(player_id)
            for player_id in (
                offer.get(
                    "player_ids",
                    [],
                )
                or []
            )
            if safe_int(player_id) > 0
        )

    if not sold_player_ids:
        return {
            "valid": False,
            "reason": "Las ofertas aceptadas no contienen jugadores validos.",
            "guaranteed_after": False,
        }

    add_cash_to_balance(
        snapshot=simulated,
        amount=accepted_cash,
    )

    remove_players_after_sale(
        snapshot=simulated,
        player_ids=sold_player_ids,
    )

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
        "accepted_offer_ids": sorted(
            accepted_offer_ids
        ),
        "sold_player_ids": sorted(
            sold_player_ids
        ),
        "accepted_cash": accepted_cash,
        "accepted_count": len(
            accepted_offer_ids
        ),
        "balance_after": safe_int(
            solvency_after.get("balance")
        ),
        "guaranteed_after": bool(
            guarantee.get(
                "guaranteed",
                False,
            )
        ),
        "state_after": guarantee.get(
            "state"
        ),
        "surplus_after": safe_int(
            guarantee.get(
                "guarantee_surplus"
            )
        ),
        "secured_after": safe_int(
            guarantee.get(
                "secured_liquidity"
            )
        ),
        "expected_after": safe_int(
            guarantee.get(
                "expected_liquidity"
            )
        ),
        "required_recovery": safe_int(
            guarantee.get(
                "required_recovery"
            )
        ),
        "solvency_after": solvency_after,
    }


# ============================================================
# PLANNER
# ============================================================


def build_offer_metadata(
    snapshot: dict,
    cluster: dict,
) -> list[dict]:

    decision_board = build_offer_decision_board(
        snapshot
    )

    decision_lookup = {
        safe_int(
            item.get("offer_id")
        ):
            item
        for item in (
            decision_board.get(
                "decisions",
                [],
            )
            or []
        )
        if safe_int(
            item.get("offer_id")
        )
        > 0
    }

    result = []

    for offer in (
        cluster.get(
            "offers",
            [],
        )
        or []
    ):

        offer_id = safe_int(
            offer.get("offer_id")
        )

        decision = (
            decision_lookup.get(
                offer_id,
                {},
            )
            or {}
        )

        damage = calculate_sale_damage(
            decision
        )

        players = (
            offer.get(
                "players",
                [],
            )
            or []
        )

        result.append(
            {
                "offer_id": offer_id,
                "player_ids": (
                    offer.get(
                        "player_ids",
                        [],
                    )
                    or []
                ),
                "player_names": [
                    player.get(
                        "name",
                        "?",
                    )
                    for player in players
                ],
                "amount": safe_int(
                    offer.get("amount")
                ),
                "damage_score": damage,
                "protected": bool(
                    damage >= 1_000_000
                ),
                "offer_decision": decision,
                "offer": offer,
            }
        )

    return result


def build_accept_before_expiry_execution_plan(
    snapshot: dict,
    offer_ids: set[int] | list[int],
) -> dict:
    """
    Busca el subconjunto minimo de ofertas que debemos aceptar
    para mantener SOLVENCY_GUARANTEE si todo el resto del cluster
    desaparece.

    Criterios, en este orden:
    1. menor numero de ventas;
    2. menor daño deportivo total;
    3. menor caja vendida innecesariamente;
    4. mayor surplus final.

    Observer: NO ejecuta escrituras.
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
                "reason"
            ),
            "selected_offers": [],
            "first_offer": None,
            "evaluated_combinations": 0,
            "revalidation": validation,
        }

    cluster = (
        validation.get(
            "cluster",
            {},
        )
        or {}
    )

    metadata = build_offer_metadata(
        snapshot=snapshot,
        cluster=cluster,
    )

    eligible = [
        item
        for item in metadata
        if not item.get(
            "protected",
            False,
        )
    ]

    if not eligible:
        return {
            "ready": False,
            "status": "NO_ELIGIBLE_OFFERS",
            "reason": "Todas las ofertas del cluster estan protegidas.",
            "selected_offers": [],
            "first_offer": None,
            "candidates": metadata,
            "evaluated_combinations": 0,
            "cluster": cluster,
            "revalidation": validation,
        }

    if len(
        eligible
    ) > MAX_COMBINATION_OFFERS:
        return {
            "ready": False,
            "status": "COMBINATION_LIMIT",
            "reason": (
                "Hay demasiadas ofertas para una busqueda combinatoria "
                "segura en este planner."
            ),
            "selected_offers": [],
            "first_offer": None,
            "candidates": metadata,
            "evaluated_combinations": 0,
            "cluster": cluster,
            "revalidation": validation,
        }

    evaluated_count = 0
    winning_options = []

    # Buscamos por cardinalidad creciente.
    for size in range(
        1,
        len(eligible) + 1,
    ):

        size_winners = []

        for combo in combinations(
            eligible,
            size,
        ):

            evaluated_count += 1

            accepted_offers = [
                item["offer"]
                for item in combo
            ]

            simulation = (
                simulate_accept_combination_and_lose_rest(
                    snapshot=snapshot,
                    cluster=cluster,
                    accepted_offers=accepted_offers,
                )
            )

            if not (
                simulation.get(
                    "valid",
                    False,
                )
                and
                simulation.get(
                    "guaranteed_after",
                    False,
                )
            ):
                continue

            total_damage = round(
                sum(
                    float(
                        item.get(
                            "damage_score",
                            0,
                        )
                    )
                    for item in combo
                ),
                2,
            )

            total_amount = sum(
                safe_int(
                    item.get("amount")
                )
                for item in combo
            )

            size_winners.append(
                {
                    "offers": list(combo),
                    "offer_ids": [
                        item["offer_id"]
                        for item in combo
                    ],
                    "player_names": [
                        name
                        for item in combo
                        for name in (
                            item.get(
                                "player_names",
                                [],
                            )
                            or []
                        )
                    ],
                    "count": size,
                    "total_damage": total_damage,
                    "total_amount": total_amount,
                    "simulation": simulation,
                }
            )

        if size_winners:
            winning_options = size_winners
            break

    if not winning_options:

        return {
            "ready": False,
            "status": "NO_SAFE_COMBINATION",
            "reason": (
                "Ni siquiera aceptando todas las ofertas elegibles "
                "se consigue mantener SOLVENCY_GUARANTEE."
            ),
            "selected_offers": [],
            "first_offer": None,
            "candidates": metadata,
            "evaluated_combinations": evaluated_count,
            "cluster": cluster,
            "revalidation": validation,
        }

    winning_options.sort(
        key=lambda option: (
            option["total_damage"],
            option["total_amount"],
            -safe_int(
                option["simulation"].get(
                    "surplus_after"
                )
            ),
        )
    )

    selected_plan = winning_options[0]

    # Dentro del plan ganador, ordenamos qué vender primero.
    # Menor daño primero; empate -> mayor importe.
    ordered = sorted(
        selected_plan["offers"],
        key=lambda item: (
            item.get(
                "damage_score",
                1_000_000,
            ),
            -safe_int(
                item.get("amount")
            ),
        ),
    )

    first_offer = (
        ordered[0]
        if ordered
        else None
    )

    status = (
        "SINGLE_ACCEPT_READY"
        if selected_plan["count"] == 1
        else "MULTI_ACCEPT_PLAN_READY"
    )

    return {
        "ready": True,
        "status": status,
        "reason": (
            f"Plan minimo encontrado: aceptar "
            f"{selected_plan['count']} oferta(s) mantiene "
            "SOLVENCY_GUARANTEE incluso si el resto del cluster "
            "desaparece."
        ),
        "required_accept_count": selected_plan["count"],
        "selected_offers": ordered,
        "selected_offer_ids": [
            item["offer_id"]
            for item in ordered
        ],
        "first_offer": first_offer,
        "selected_plan": selected_plan,
        "alternative_minimum_plans": winning_options[:10],
        "candidates": metadata,
        "evaluated_combinations": evaluated_count,
        "cluster": cluster,
        "revalidation": validation,
        "observer_only": True,
    }
