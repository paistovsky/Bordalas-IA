from __future__ import annotations

from datetime import datetime
from typing import Any

from src.analysis.computer_offer_reroll_engine import (
    build_computer_offer_reroll_board,
)

from src.analysis.liquidity_manager import (
    build_liquidity_state,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ============================================================
# CONFIGURACION
# ============================================================

FRANCHISE_NEVER_SELL_THRESHOLD = 70.0

# Una oferta excelente no implica vender automaticamente.
# Solo eleva el atractivo economico de la oferta.
PREMIUM_EXCELLENT = 8.0
PREMIUM_GOOD = 3.0
PREMIUM_FAIR = 0.0

# Evitamos aceptar una oferta que destruya un activo que
# claramente sigue en tendencia de revalorizacion.
SPECULATION_HOLD_THRESHOLD = 62.0

# Observer V2: ninguna decision nueva se ejecuta.
OBSERVER_ONLY = True


# ============================================================
# HELPERS
# ============================================================


def parse_hours_to_expiry(
    offer: dict,
    now: datetime | None = None,
) -> float | None:
    """
    Calcula horas hasta caducidad a partir del campo unix `until`.
    """
    until = offer.get("until")

    if until is None:
        return None

    try:
        until = int(until)
    except (TypeError, ValueError):
        return None

    now_ts = (
        now.timestamp()
        if now is not None
        else datetime.now().timestamp()
    )

    return max(
        (until - now_ts) / 3600,
        0.0,
    )


def build_lookup(
    items: list[dict],
    key: str = "id",
) -> dict[int, dict]:

    result = {}

    for item in items:
        value = item.get(key)

        try:
            value = int(value)
        except (TypeError, ValueError):
            continue

        result[value] = item

    return result


def classify_offer_quality(
    premium_percent: float,
) -> str:

    if premium_percent >= PREMIUM_EXCELLENT:
        return "EXCELLENT"

    if premium_percent >= PREMIUM_GOOD:
        return "GOOD"

    if premium_percent >= PREMIUM_FAIR:
        return "FAIR"

    return "BELOW_MARKET"


def calculate_economic_score(
    premium_percent: float,
    sale_score: float,
    speculation_score: float,
    price_increment: int,
) -> float:
    """
    Score 0..100:
    - prima de oferta
    - facilidad/beneficio de venta
    - penalizacion si el activo sigue revalorizandose
    """

    score = 50.0

    score += max(
        min(
            premium_percent * 2.0,
            24.0,
        ),
        -20.0,
    )

    score += (
        max(
            min(
                sale_score,
                100.0,
            ),
            0.0,
        )
        - 50.0
    ) * 0.20

    if speculation_score >= 70:
        score -= 15

    elif speculation_score >= 60:
        score -= 8

    elif speculation_score <= 35:
        score += 8

    if price_increment >= 100_000:
        score -= 10

    elif price_increment >= 40_000:
        score -= 5

    elif price_increment < 0:
        score += 6

    return round(
        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),
        1,
    )


# ============================================================
# DECISION INDIVIDUAL
# ============================================================


def decide_incoming_offer(
    offer: dict,
    roster: dict,
    strategic: dict,
    speculation: dict,
    reroll_offer: dict | None,
    recovery_selected_offer_ids: set[int],
) -> dict:

    offer_id = offer.get("offer_id")

    player_id = int(
        offer.get("player_id")
        or 0
    )

    amount = int(
        offer.get("amount", 0)
        or 0
    )

    market_value = int(
        offer.get("market_value", 0)
        or 0
    )

    premium_percent = float(
        offer.get("delta_percent", 0.0)
        or 0.0
    )

    franchise_score = float(
        strategic.get(
            "franchise_score",
            0,
        )
        or 0
    )

    strategic_score = float(
        strategic.get(
            "strategic_score",
            0,
        )
        or 0
    )

    sale_score = float(
        roster.get(
            "sale_score",
            0,
        )
        or 0
    )

    protection = roster.get(
        "protection",
        "NORMAL",
    )

    in_lineup = bool(
        roster.get(
            "in_lineup",
            False,
        )
    )

    speculation_score = float(
        speculation.get(
            "speculation_score",
            50,
        )
        or 50
    )

    speculation_action = speculation.get(
        "speculation_action",
        "UNKNOWN",
    )

    price_increment = int(
        speculation.get(
            "price_increment",
            roster.get(
                "price_increment",
                0,
            ),
        )
        or 0
    )

    economic_score = (
        calculate_economic_score(
            premium_percent=
                premium_percent,

            sale_score=
                sale_score,

            speculation_score=
                speculation_score,

            price_increment=
                price_increment,
        )
    )

    quality = (
        classify_offer_quality(
            premium_percent
        )
    )

    # El recovery plan clasico sirve para saber qué ofertas
    # podrían cubrir saldo, pero NO significa que debamos aceptar
    # ahora. La fuente de verdad temporal para Computer es
    # computer_offer_reroll_engine / solvency_guarantee.
    recovery_selected = (
        offer_id
        in recovery_selected_offer_ids
    )

    reroll_action = (
        reroll_offer.get(
            "action"
        )
        if reroll_offer
        else None
    )

    reroll_safe = bool(
        reroll_offer
        and
        reroll_offer.get(
            "reroll_safe",
            False,
        )
    )

    solvency_reserved = bool(
        reroll_offer
        and
        reroll_offer.get(
            "solvency_reserved",
            False,
        )
    )

    counterparty = (
        (
            offer.get(
                "raw_offer",
                {},
            )
            or {}
        )
        .get(
            "counterparty",
            {},
        )
        or {}
    )

    counterparty_type = (
        counterparty.get(
            "type",
            "UNKNOWN",
        )
    )

    reasons = []

    # ========================================================
    # NEVER SELL
    # ========================================================

    if (
        protection == "NEVER_AUTO_SELL"
        or
        franchise_score
        >= FRANCHISE_NEVER_SELL_THRESHOLD
    ):

        action = "NEVER_SELL"
        confidence = 100

        reasons.append(
            "Jugador Franchise/NEVER_AUTO_SELL."
        )

    # ========================================================
    # COMPUTER: RESPETAR SU MOTOR COMO FUENTE DE VERDAD
    # ========================================================

    elif (
        counterparty_type == "COMPUTER"
        and
        reroll_offer is not None
    ):

        if reroll_action == "ACCEPT_BEFORE_EXPIRY":

            action = "ACCEPT_FOR_SOLVENCY"
            confidence = 99

            reasons.append(
                "Oferta Computer necesaria para solvencia "
                "y próxima a caducar."
            )

        elif solvency_reserved:

            action = "HOLD_SOLVENCY_RESERVED"
            confidence = 99

            reasons.append(
                "Oferta marcada SOLVENCY_RESERVED. "
                "Se conserva como garantía de liquidez y "
                "no se acepta ni rerollea mientras siga reservada."
            )

        elif reroll_action == "REROLL_CANDIDATE":

            action = "REROLL_CANDIDATE"
            confidence = 95

            reasons.append(
                "Computer Reroll Engine autoriza buscar "
                "una oferta mejor manteniendo solvencia."
            )

        elif reroll_action == "KEEP_PROTECTED":

            action = "NEVER_SELL"
            confidence = 100

            reasons.append(
                "Computer Reroll Engine protege este activo."
            )

        elif reroll_action == "KEEP_GOOD_OFFER":

            action = "KEEP_GOOD_OFFER"
            confidence = 90

            reasons.append(
                "Oferta Computer buena; conservar opcionalidad "
                "sin vender automáticamente."
            )

        elif reroll_action == "KEEP_OFFER":

            action = "HOLD_OFFER"
            confidence = 88

            reasons.append(
                "Computer Reroll Engine considera que el reroll "
                "no compensa con la información actual."
            )

        else:

            action = "HOLD_OFFER"
            confidence = 80

            reasons.append(
                "Oferta Computer sin señal ejecutable específica; "
                "se conserva en observación."
            )

    # ========================================================
    # OFERTAS DE OTROS MANAGERS / CASOS NO COMPUTER
    # ========================================================

    elif (
        speculation_score
        >= SPECULATION_HOLD_THRESHOLD
        and
        price_increment > 0
        and
        quality != "EXCELLENT"
    ):

        action = "HOLD_OFFER"
        confidence = 85

        reasons.append(
            "El activo mantiene una señal especulativa positiva."
        )

    elif (
        quality == "EXCELLENT"
        and
        sale_score >= 45
        and
        not in_lineup
    ):

        action = "ACCEPT_NOW"
        confidence = 88

        reasons.append(
            "Prima excelente y coste deportivo asumible."
        )

    elif (
        quality
        in {
            "GOOD",
            "EXCELLENT",
        }
        and
        sale_score >= 60
    ):

        action = "ACCEPT_NOW"
        confidence = 84

        reasons.append(
            "Oferta favorable por un activo claramente vendible."
        )

    elif quality in {
        "GOOD",
        "EXCELLENT",
    }:

        action = "KEEP_GOOD_OFFER"
        confidence = 80

        reasons.append(
            "Oferta favorable; se conserva sin vender automáticamente."
        )

    else:

        action = "HOLD_OFFER"
        confidence = 75

        reasons.append(
            "No existe ventaja suficiente para aceptar ahora."
        )

    # ========================================================
    # CONTEXTO EXPLICATIVO
    # ========================================================

    if recovery_selected:
        reasons.append(
            "El recovery plan clásico la incluye como posible "
            "fuente de caja, pero eso NO fuerza aceptación inmediata."
        )

    if solvency_reserved:
        reasons.append(
            "SOLVENCY_RESERVED=SI."
        )

    if in_lineup:
        reasons.append(
            "Forma parte del XI actual."
        )

    if price_increment > 0:
        reasons.append(
            f"Valor de mercado subiendo: +{price_increment:,} EUR."
        )

    if speculation_action not in {
        None,
        "UNKNOWN",
    }:
        reasons.append(
            f"Speculation: {speculation_action} ({speculation_score:.1f})."
        )

    return {
        "offer_id":
            offer_id,

        "player_id":
            player_id,

        "player_name":
            offer.get(
                "player_name"
            ),

        "counterparty_type":
            counterparty_type,

        "amount":
            amount,

        "market_value":
            market_value,

        "premium_percent":
            round(
                premium_percent,
                2,
            ),

        "offer_quality":
            quality,

        "franchise_score":
            franchise_score,

        "strategic_score":
            strategic_score,

        "sale_score":
            sale_score,

        "protection":
            protection,

        "in_lineup":
            in_lineup,

        "speculation_score":
            speculation_score,

        "speculation_action":
            speculation_action,

        "price_increment":
            price_increment,

        "economic_score":
            economic_score,

        "recovery_selected":
            recovery_selected,

        "solvency_reserved":
            solvency_reserved,

        "reroll_safe":
            reroll_safe,

        "reroll_action":
            reroll_action,

        "decision":
            action,

        "confidence":
            confidence,

        "automatic":
            False,

        "observer_only":
            OBSERVER_ONLY,

        "reasons":
            reasons,

        "raw_offer":
            offer,
    }


# ============================================================
# BOARD GLOBAL
# ============================================================


def build_offer_decision_board(
    snapshot: dict,
) -> dict:

    offer_board = (
        build_offer_board(
            snapshot
        )
    )

    liquidity = (
        build_liquidity_state(
            snapshot
        )
    )

    strategic_board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="strategic",
        )
    )

    speculation_board = (
        build_speculation_board(
            snapshot
        )
    )

    reroll_board = (
        build_computer_offer_reroll_board(
            snapshot=
                snapshot,

            persist_history=
                False,
        )
    )

    roster_lookup = {
        int(
            item["id"]
        ):
            item

        for item
        in liquidity.get(
            "roster",
            [],
        )
    }

    strategic_lookup = (
        build_lookup(
            strategic_board,
            key="id",
        )
    )

    speculation_lookup = (
        build_lookup(
            speculation_board.get(
                "owned",
                [],
            ),
            key="id",
        )
    )

    reroll_lookup = {
        int(
            player_id
        ):
            reroll

        for reroll
        in reroll_board.get(
            "offers",
            [],
        )

        for player_id
        in reroll.get(
            "player_ids",
            [],
        )
    }

    recovery = (
        liquidity.get(
            "recovery",
            {},
        )
        or {}
    )

    recovery_selected_offer_ids = {
        int(
            item["offer_id"]
        )

        for item
        in recovery.get(
            "selected",
            [],
        )

        if item.get(
            "offer_id"
        )
        is not None
    }

    incoming_candidates = (
        liquidity.get(
            "incoming_offers",
            [],
        )
        or []
    )

    decisions = []

    for incoming in incoming_candidates:

        player_id = int(
            incoming.get(
                "player_id",
                0,
            )
            or 0
        )

        decisions.append(
            decide_incoming_offer(
                offer=
                    incoming,

                roster=
                    roster_lookup.get(
                        player_id,
                        {},
                    ),

                strategic=
                    strategic_lookup.get(
                        player_id,
                        {},
                    ),

                speculation=
                    speculation_lookup.get(
                        player_id,
                        {},
                    ),

                reroll_offer=
                    reroll_lookup.get(
                        player_id
                    ),

                recovery_selected_offer_ids=
                    recovery_selected_offer_ids,
            )
        )

    decision_priority = {
        "NEVER_SELL": 100,
        "ACCEPT_FOR_SOLVENCY": 95,
        "HOLD_SOLVENCY_RESERVED": 90,
        "REROLL_CANDIDATE": 85,
        "ACCEPT_NOW": 80,
        "KEEP_GOOD_OFFER": 60,
        "HOLD_OFFER": 50,
    }

    decisions.sort(
        key=lambda item: (
            decision_priority.get(
                item["decision"],
                0,
            ),
            item["confidence"],
            item["economic_score"],
        ),
        reverse=True,
    )

    grouped = {}

    for decision in decisions:
        grouped.setdefault(
            decision[
                "decision"
            ],
            [],
        ).append(
            decision
        )

    return {
        "observer_only":
            OBSERVER_ONLY,

        "offer_count":
            len(
                decisions
            ),

        "decisions":
            decisions,

        "grouped":
            grouped,

        "accept_now":
            grouped.get(
                "ACCEPT_NOW",
                [],
            ),

        "accept_for_solvency":
            grouped.get(
                "ACCEPT_FOR_SOLVENCY",
                [],
            ),

        "hold_solvency_reserved":
            grouped.get(
                "HOLD_SOLVENCY_RESERVED",
                [],
            ),

        "reroll_candidates":
            grouped.get(
                "REROLL_CANDIDATE",
                [],
            ),

        "hold":
            (
                grouped.get(
                    "HOLD_OFFER",
                    [],
                )
                +
                grouped.get(
                    "KEEP_GOOD_OFFER",
                    [],
                )
            ),

        "never_sell":
            grouped.get(
                "NEVER_SELL",
                [],
            ),

        "recovery":
            recovery,

        "reroll":
            reroll_board,

        "liquidity":
            liquidity,

        "speculation":
            speculation_board,

        "offer_board":
            offer_board,
    }
