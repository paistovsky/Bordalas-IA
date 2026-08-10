from __future__ import annotations

from datetime import datetime, timedelta

from src.analysis.computer_cycle_engine import (
    MADRID_TZ,
    build_computer_cycle_state,
    find_first_safe_cycle_for_listing,
    parse_datetime_value,
)

from src.analysis.deadline_engine import (
    build_deadline_state,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)


SAFE_LIQUIDITY_BUFFER = 500_000

EXPECTED_LIQUIDITY_HAIRCUT_ONE_CYCLE = 0.70
EXPECTED_LIQUIDITY_HAIRCUT_TWO_CYCLES = 0.78
EXPECTED_LIQUIDITY_HAIRCUT_MANY_CYCLES = 0.82


FRANCHISE_PROTECTION_THRESHOLD = 70


# ======================================================
# SALDO
# ======================================================


def get_current_balance(
    snapshot: dict,
) -> int:

    return int(
        snapshot
        .get(
            "market",
            {},
        )
        .get(
            "status",
            {},
        )
        .get(
            "balance",
            0,
        )
        or 0
    )


# ======================================================
# ACTIVOS LIQUIDABLES
# ======================================================


def calculate_liquidatable_assets(
    snapshot: dict,
) -> dict:

    sales = (
        analyze_sales(
            snapshot
        )
    )

    players = []

    for player in sales:

        sale_score = float(
            player.get(
                "sale_score",
                0,
            )
            or 0
        )

        if sale_score < 50:
            continue

        value = int(
            player.get(
                "price",
                0,
            )
            or 0
        )

        if value <= 0:
            continue

        players.append(
            {
                "id":
                    player[
                        "id"
                    ],

                "name":
                    player[
                        "name"
                    ],

                "value":
                    value,

                "sale_score":
                    sale_score,
            }
        )

    total = sum(
        player[
            "value"
        ]

        for player in players
    )

    return {
        "players":
            players,

        "total":
            total,
    }


# ======================================================
# OFERTAS
# ======================================================


def resolve_offer_expiry(offer: dict) -> datetime | None:
    until = parse_datetime_value(offer.get("until"))
    if until is not None:
        return until

    created = parse_datetime_value(offer.get("created"))
    if created is None:
        return None

    return created + timedelta(days=2)


def is_computer_offer(offer: dict) -> bool:
    counterparty = offer.get("counterparty", {}) or {}
    counterparty_type = str(counterparty.get("type", "")).upper()
    counterparty_id = counterparty.get("id")

    return bool(
        counterparty_type == "COMPUTER"
        or counterparty_id in {0, "0"}
    )


def offer_has_franchise_player(offer: dict) -> bool:
    for player in offer.get("players", []):
        if float(player.get("franchise_score", 0) or 0) >= FRANCHISE_PROTECTION_THRESHOLD:
            return True
    return False


def calculate_incoming_offer_liquidity(snapshot: dict) -> dict:
    board = build_offer_board(snapshot)
    now = datetime.now(MADRID_TZ)

    computer_offers = []
    manager_offers = []
    expired_offers = []

    for offer in board["incoming"]:
        if offer.get("status") != "waiting":
            continue

        expiry = resolve_offer_expiry(offer)
        expired = bool(expiry is not None and expiry <= now)

        enriched = {
            **offer,
            "expires_at": expiry,
            "hours_to_expiry": (
                round((expiry - now).total_seconds() / 3600, 2)
                if expiry is not None
                else None
            ),
            "is_computer": is_computer_offer(offer),
            "franchise_protected": offer_has_franchise_player(offer),
        }

        if expired:
            expired_offers.append(enriched)
            continue

        if enriched["is_computer"]:
            computer_offers.append(enriched)
        else:
            manager_offers.append(enriched)

    eligible_computer_offers = [
        offer for offer in computer_offers
        if not offer["franchise_protected"]
    ]

    secured_total = sum(int(offer["amount"]) for offer in eligible_computer_offers)
    manager_total = sum(int(offer["amount"]) for offer in manager_offers)

    return {
        "offers": eligible_computer_offers,
        "all_computer_offers": computer_offers,
        "manager_offers": manager_offers,
        "expired_offers": expired_offers,
        "total": secured_total,
        "secured_total": secured_total,
        "manager_total": manager_total,
        "count": len(eligible_computer_offers),
    }


def get_current_listings(snapshot: dict) -> dict[int, dict]:
    team_ids = {
        int(player["id"])
        for player in snapshot.get("my_team", [])
    }

    result = {}

    for sale in snapshot.get("market", {}).get("sales", []) or []:
        player_data = sale.get("player", {}) or {}
        player_id = player_data.get("id")

        if player_id is None:
            continue

        player_id = int(player_id)

        if player_id not in team_ids:
            continue

        result[player_id] = {
            "player_id": player_id,
            "listed_price": int(sale.get("price", 0) or 0),
            "listed_at": sale.get("date"),
            "until": sale.get("until"),
            "raw": sale,
        }

    return result


def get_expected_haircut(safe_cycles_remaining: int) -> float:
    if safe_cycles_remaining <= 0:
        return 0.0
    if safe_cycles_remaining == 1:
        return EXPECTED_LIQUIDITY_HAIRCUT_ONE_CYCLE
    if safe_cycles_remaining == 2:
        return EXPECTED_LIQUIDITY_HAIRCUT_TWO_CYCLES
    return EXPECTED_LIQUIDITY_HAIRCUT_MANY_CYCLES


def calculate_expected_liquidity(
    snapshot: dict,
    liquidatable: dict,
    incoming: dict,
    cycle_state: dict,
) -> dict:
    if not cycle_state.get("available", False):
        return {"players": [], "total": 0, "haircut": 0.0}

    listings = get_current_listings(snapshot)

    secured_player_ids = {
        int(player_id)
        for offer in incoming.get("offers", [])
        for player_id in offer.get("player_ids", [])
    }

    safe_cycles_remaining = int(cycle_state.get("safe_cycles_remaining", 0) or 0)
    haircut = get_expected_haircut(safe_cycles_remaining)

    players = []

    for player in liquidatable.get("players", []):
        player_id = int(player["id"])

        if player_id in secured_player_ids:
            continue

        listing = listings.get(player_id)
        if listing is None:
            continue

        eligible_cycle = find_first_safe_cycle_for_listing(
            cycle_state=cycle_state,
            listed_at=listing.get("listed_at"),
        )

        if eligible_cycle is None:
            continue

        market_value = int(player["value"])
        expected_value = int(market_value * haircut)

        players.append({
            **player,
            "market_value": market_value,
            "expected_liquidity": expected_value,
            "haircut": haircut,
            "first_safe_cycle": eligible_cycle,
            "listing": listing,
        })

    return {
        "players": players,
        "total": sum(player["expected_liquidity"] for player in players),
        "haircut": haircut,
    }


def build_solvency_guarantee(
    balance: int,
    incoming: dict,
    expected: dict,
    cycle_state: dict,
) -> dict:
    """
    Fuente unica de verdad de solvencia.

    SECURED_LIQUIDITY cuenta al 100%.
    EXPECTED_LIQUIDITY ya llega con su haircut aplicado
    en calculate_expected_liquidity(), por lo que NO se
    vuelve a descontar aqui.
    """
    secured = int(incoming.get("secured_total", 0) or 0)
    expected_total = int(expected.get("total", 0) or 0)

    guaranteed_recovery = secured + expected_total
    current_debt = max(-int(balance), 0)
    required_recovery = current_debt + SAFE_LIQUIDITY_BUFFER

    guarantee_surplus = guaranteed_recovery - required_recovery
    guaranteed = guarantee_surplus >= 0

    safe_cycles_remaining = int(
        cycle_state.get("safe_cycles_remaining", 0) or 0
    )

    if current_debt <= 0:
        state = "SOLVENT"
    elif guaranteed:
        state = "GUARANTEED"
    else:
        state = "NOT_GUARANTEED"

    return {
        "state": state,
        "guaranteed": guaranteed,
        "current_debt": current_debt,
        "safety_buffer": SAFE_LIQUIDITY_BUFFER,
        "required_recovery": required_recovery,
        "secured_liquidity": secured,
        "expected_liquidity": expected_total,
        "guaranteed_recovery": guaranteed_recovery,
        "guarantee_surplus": guarantee_surplus,
        "safe_cycles_remaining": safe_cycles_remaining,
        "reason": (
            "SECURED_LIQUIDITY + EXPECTED_LIQUIDITY cubren deuda "
            "actual y buffer T-15."
            if guaranteed
            else
            "La liquidez conservadora no cubre todavia deuda "
            "actual y buffer T-15."
        ),
    }


def calculate_offer_reservations(
    balance: int,
    incoming: dict,
    guarantee: dict,
) -> dict:
    """
    Reserva solo la parte de SECURED_LIQUIDITY que no podemos
    permitirnos perder manteniendo la garantia T-15.

    EXPECTED_LIQUIDITY ya esta descontada una vez y se utiliza
    directamente: no existe un segundo haircut.
    """
    if balance >= 0:
        return {
            "required_recovery": 0,
            "reserved": [],
            "reserved_offer_ids": [],
            "reserved_total": 0,
            "expected_credit": int(
                guarantee.get("expected_liquidity", 0) or 0
            ),
            "covered": True,
            "reason": "No hay deficit actual.",
        }

    required_recovery = int(
        guarantee.get("required_recovery", 0) or 0
    )
    expected_credit = int(
        guarantee.get("expected_liquidity", 0) or 0
    )
    secured_needed = max(required_recovery - expected_credit, 0)

    offers = list(incoming.get("offers", []))

    def reservation_key(offer: dict):
        players = offer.get("players", []) or []
        max_franchise = max(
            [float(p.get("franchise_score", 0) or 0) for p in players]
            or [0.0]
        )
        max_strategic = max(
            [float(p.get("strategic_score", 0) or 0) for p in players]
            or [0.0]
        )
        premium = float(offer.get("premium_percent", 0) or 0)
        amount = int(offer.get("amount", 0) or 0)

        # Primero reservamos lo menos valioso deportivamente,
        # favoreciendo ofertas mejores y de mayor importe.
        return (
            max_franchise,
            max_strategic,
            -premium,
            -amount,
        )

    offers.sort(key=reservation_key)

    reserved = []
    reserved_total = 0

    for offer in offers:
        if reserved_total >= secured_needed:
            break

        reserved.append({
            **offer,
            "solvency_reserved": True,
            "reservation_reason": (
                "Esta oferta forma parte de la garantia unica "
                "de solvencia T-15."
            ),
        })
        reserved_total += int(offer.get("amount", 0) or 0)

    covered = bool(
        reserved_total + expected_credit >= required_recovery
    )

    return {
        "required_recovery": required_recovery,
        "secured_needed": secured_needed,
        "reserved": reserved,
        "reserved_offer_ids": [
            offer.get("offer_id")
            for offer in reserved
        ],
        "reserved_total": reserved_total,
        "expected_credit": expected_credit,
        "covered": covered,
        "guarantee_state": guarantee.get("state"),
        "reason": (
            "Las ofertas SOLVENCY_RESERVED no deben rechazarse "
            "sin recalcular SOLVENCY_GUARANTEE."
        ),
    }


def calculate_max_safe_debt(
    guarantee: dict,
) -> dict:
    """
    MAX_SAFE_DEBT deriva exclusivamente de SOLVENCY_GUARANTEE.
    No recalcula liquidez ni aplica descuentos adicionales.
    """
    guaranteed_recovery = int(
        guarantee.get("guaranteed_recovery", 0) or 0
    )
    current_debt = int(
        guarantee.get("current_debt", 0) or 0
    )
    safety_buffer = int(
        guarantee.get("safety_buffer", SAFE_LIQUIDITY_BUFFER) or 0
    )

    max_total_debt = max(
        guaranteed_recovery - safety_buffer,
        0,
    )

    additional_debt_headroom = max(
        max_total_debt - current_debt,
        0,
    )

    debt_window_open = bool(
        guarantee.get("guaranteed", False)
        and additional_debt_headroom > 0
    )

    return {
        "secured_liquidity": int(
            guarantee.get("secured_liquidity", 0) or 0
        ),
        "expected_liquidity": int(
            guarantee.get("expected_liquidity", 0) or 0
        ),
        "safe_recoverable_cash": guaranteed_recovery,
        "safety_buffer": safety_buffer,
        "max_total_debt": max_total_debt,
        "current_debt": current_debt,
        "additional_debt_headroom": additional_debt_headroom,
        "debt_window_open": debt_window_open,
        "safe_cycles_remaining": int(
            guarantee.get("safe_cycles_remaining", 0) or 0
        ),
        "guarantee_state": guarantee.get("state"),
    }


# ======================================================
# RIESGO
# ======================================================


def classify_solvency_risk(
    balance: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
    phase: str,
) -> str:

    if balance >= 0:

        if balance >= SAFE_LIQUIDITY_BUFFER:
            return "BAJO"

        return "CONTROLAR"

    deficit = abs(
        balance
    )

    covered = (
        recoverable_cash
        >= deficit
    )

    if phase in {
        "HARD_SAFETY",
        "FINALIZATION",
    }:

        return (
            "MUY_ALTO"
            if covered
            else "CRITICO"
        )

    if phase in {
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return "BLOQUEADO"

    if phase == "HIGH_ATTENTION":

        return (
            "ALTO"
            if covered
            else "MUY_ALTO"
        )

    if phase == "PREPARATION":

        return (
            "MODERADO"
            if covered
            else "ALTO"
        )

    if seconds_to_deadline is None:

        return (
            "MODERADO"
            if covered
            else "ALTO"
        )

    return (
        "MODERADO"
        if covered
        else "ALTO"
    )

def calculate_temporary_debt_permission(
    balance: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
    phase: str,
    max_safe_debt: dict | None = None,
) -> dict:
    if phase in {"ROUND_LOCKED", "ROUND_TRANSITION_LOCK"}:
        return {
            "allowed": False,
            "reason": (
                "La jornada esta temporalmente bloqueada. "
                "No se evalua nueva deuda hasta el desbloqueo."
            ),
        }

    if phase in {"HARD_SAFETY", "FINALIZATION"}:
        return {
            "allowed": False,
            "reason": (
                "Estamos en fase de cierre de jornada. "
                "Bordalas IA exige recuperar saldo >= 0."
            ),
        }

    if seconds_to_deadline is None:
        return {
            "allowed": False,
            "reason": (
                "No conocemos el deadline real y no podemos "
                "autorizar deuda temporal."
            ),
        }

    if lineup_risk in {"CRITICO", "MUY_ALTO"}:
        return {
            "allowed": False,
            "reason": (
                "El riesgo del XI es demasiado alto para "
                "mantener o aumentar deuda."
            ),
        }

    if max_safe_debt is not None:
        headroom = int(max_safe_debt.get("additional_debt_headroom", 0) or 0)
        debt_window_open = bool(max_safe_debt.get("debt_window_open", False))

        if not debt_window_open:
            return {
                "allowed": False,
                "reason": (
                    "No queda una ventana de liquidez suficientemente "
                    "segura para asumir nueva deuda."
                ),
            }

        if headroom <= 0:
            return {
                "allowed": False,
                "reason": (
                    "La deuda actual consume todo el MAX_SAFE_DEBT "
                    "disponible."
                ),
            }

        return {
            "allowed": True,
            "additional_debt_headroom": headroom,
            "reason": (
                "Existe margen de deuda adicional dentro de "
                "MAX_SAFE_DEBT sin comprometer el T-15."
            ),
        }

    if balance >= 0:
        return {"allowed": True, "reason": "El saldo actual no es negativo."}

    deficit = abs(balance)

    if recoverable_cash < deficit:
        return {
            "allowed": False,
            "reason": "La liquidez recuperable no cubre el deficit actual.",
        }

    coverage_ratio = recoverable_cash / deficit

    if coverage_ratio < 1.25:
        return {
            "allowed": False,
            "reason": (
                "Existe cobertura teorica, pero el margen "
                "es demasiado pequeno."
            ),
        }

    return {
        "allowed": True,
        "reason": (
            "El deficit esta cubierto con margen y la fase "
            f"{phase} permite deuda temporal."
        ),
    }

# ======================================================
# HARD SAFETY
# ======================================================


def determine_hard_safety(
    balance: int,
    deadline: dict,
    lineup_risk: str,
) -> dict:

    phase = str(
        deadline.get(
            "phase",
            "CALENDAR_UNKNOWN",
        )
    )

    reasons = []

    active = bool(
        phase
        in {
            "HARD_SAFETY",
            "ROUND_LOCKED",
            "ROUND_TRANSITION_LOCK",
        }
    )

    if phase == "HARD_SAFETY":

        reasons.append(
            "Ventana T-90 a T-15 activa."
        )

    if phase in {
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        reasons.append(
            "Jornada temporalmente bloqueada."
        )

    if (
        balance < 0
        and
        phase
        in {
            "FINALIZATION",
            "HARD_SAFETY",
        }
    ):

        active = True

        reasons.append(
            "Saldo negativo en fase de cierre."
        )

    if (
        lineup_risk
        == "CRITICO"
        and
        phase
        not in {
            "NORMAL",
            "ROUND_LOCKED",
            "ROUND_TRANSITION_LOCK",
        }
    ):

        active = True

        reasons.append(
            "Riesgo critico de XI."
        )

    return {
        "active":
            active,

        "phase":
            phase,

        "operations_locked":
            bool(
                deadline.get(
                    "operations_locked",
                    False,
                )
            ),

        "reasons":
            reasons,
    }


# ======================================================
# DEUDA HIPOTETICA
# ======================================================


def evaluate_projected_debt(
    debt: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
    phase: str = "NORMAL",
) -> dict:

    debt = max(
        int(
            debt
        ),
        0,
    )

    if debt <= 0:

        return {
            "debt":
                0,

            "covered":
                True,

            "coverage_ratio":
                None,

            "allowed":
                True,

            "reason":
                "La operacion no generaria deuda.",
        }

    covered = (
        recoverable_cash
        >= debt
    )

    coverage_ratio = (
        recoverable_cash
        / debt
    )

    if phase in {
        "FINALIZATION",
        "HARD_SAFETY",
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return {
            "debt":
                debt,

            "covered":
                covered,

            "coverage_ratio":
                round(
                    coverage_ratio,
                    2,
                ),

            "allowed":
                False,

            "reason": (
                f"La fase {phase} no permite asumir "
                "nueva deuda."
            ),
        }

    if seconds_to_deadline is None:

        return {
            "debt":
                debt,

            "covered":
                covered,

            "coverage_ratio":
                round(
                    coverage_ratio,
                    2,
                ),

            "allowed":
                False,

            "reason": (
                "No conocemos el deadline real y no podemos "
                "validar deuda futura con seguridad."
            ),
        }

    if lineup_risk in {
        "CRITICO",
        "MUY_ALTO",
    }:

        return {
            "debt":
                debt,

            "covered":
                covered,

            "coverage_ratio":
                round(
                    coverage_ratio,
                    2,
                ),

            "allowed":
                False,

            "reason": (
                "El riesgo de alineacion es demasiado alto "
                "para asumir deuda adicional."
            ),
        }

    if not covered:

        return {
            "debt":
                debt,

            "covered":
                False,

            "coverage_ratio":
                round(
                    coverage_ratio,
                    2,
                ),

            "allowed":
                False,

            "reason": (
                "La liquidez recuperable no cubre "
                "la deuda proyectada."
            ),
        }

    if coverage_ratio < 1.25:

        return {
            "debt":
                debt,

            "covered":
                True,

            "coverage_ratio":
                round(
                    coverage_ratio,
                    2,
                ),

            "allowed":
                False,

            "reason": (
                "La deuda esta cubierta, pero no existe "
                "un colchon suficiente."
            ),
        }

    return {
        "debt":
            debt,

        "covered":
            True,

        "coverage_ratio":
            round(
                coverage_ratio,
                2,
            ),

        "allowed":
            True,

        "reason": (
            f"La fase {phase} permite deuda temporal y "
            "la deuda proyectada esta cubierta con margen."
        ),
    }


# ======================================================
# ESTADO GLOBAL
# ======================================================


def build_solvency_state(snapshot: dict) -> dict:
    balance = get_current_balance(snapshot)
    deadline = build_deadline_state(snapshot)

    cycle_state = build_computer_cycle_state(deadline)
    liquidatable = calculate_liquidatable_assets(snapshot)
    incoming = calculate_incoming_offer_liquidity(snapshot)

    expected = calculate_expected_liquidity(
        snapshot=snapshot,
        liquidatable=liquidatable,
        incoming=incoming,
        cycle_state=cycle_state,
    )

    guarantee = build_solvency_guarantee(
        balance=balance,
        incoming=incoming,
        expected=expected,
        cycle_state=cycle_state,
    )

    max_safe_debt = calculate_max_safe_debt(
        guarantee=guarantee,
    )

    reservations = calculate_offer_reservations(
        balance=balance,
        incoming=incoming,
        guarantee=guarantee,
    )

    recoverable_cash = int(
        guarantee["guaranteed_recovery"]
    )

    seconds_to_deadline = deadline.get(
        "seconds_to_deadline"
    )
    lineup_risk = deadline["lineup_risk"]
    phase = str(
        deadline.get("phase", "CALENDAR_UNKNOWN")
    )

    risk = classify_solvency_risk(
        balance=balance,
        recoverable_cash=recoverable_cash,
        seconds_to_deadline=seconds_to_deadline,
        phase=phase,
    )

    debt_permission = calculate_temporary_debt_permission(
        balance=balance,
        recoverable_cash=recoverable_cash,
        seconds_to_deadline=seconds_to_deadline,
        lineup_risk=lineup_risk,
        phase=phase,
        max_safe_debt=max_safe_debt,
    )

    hard_safety = determine_hard_safety(
        balance=balance,
        deadline=deadline,
        lineup_risk=lineup_risk,
    )

    return {
        "balance": balance,
        "is_negative": balance < 0,
        "phase": phase,
        "operations_locked": bool(
            deadline.get("operations_locked", False)
        ),
        "liquidatable_assets": liquidatable,
        "incoming_offer_liquidity": incoming,
        "recoverable_cash": recoverable_cash,
        "cash": max(balance, 0),
        "secured_liquidity": incoming,
        "expected_liquidity": expected,
        "computer_cycles": cycle_state,
        "solvency_guarantee": guarantee,
        "solvency_reservations": reservations,
        "max_safe_debt": max_safe_debt,
        "risk": risk,
        "temporary_debt": debt_permission,
        "hard_safety": hard_safety,
        "seconds_to_deadline": seconds_to_deadline,
        "lineup_risk": lineup_risk,
        "deadline": deadline,
    }
