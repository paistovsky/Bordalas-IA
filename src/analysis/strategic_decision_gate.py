from src.analysis.deadline_engine import (
    build_deadline_state,
)

from src.analysis.strategic_budget_engine import (
    build_strategic_budget,
)

from src.analysis.strategic_plan_comparator import (
    compare_strategic_plans,
)


# ======================================================
# CONFIGURACIÓN
# ======================================================

MIN_RESTRUCTURE_FRANCHISE_SCORE = 70.0


# ======================================================
# PRESIÓN DE VENTA
# ======================================================


def calculate_sale_pressure(
    minimum_sale_needed: int,
    balance: int,
) -> float:

    if balance <= 0:
        return 100.0

    return (
        minimum_sale_needed
        / balance
    ) * 100


# ======================================================
# FASE DE TEMPORADA
# ======================================================


def determine_season_phase(
    deadline: dict,
    premium_active: bool,
) -> str:

    lineup_risk = (
        deadline[
            "lineup_risk"
        ]
    )

    missing = (
        deadline[
            "missing_playable"
        ]
    )

    if lineup_risk == "CRITICO":
        return "CERRAR XI"

    if lineup_risk in {
        "MUY_ALTO",
        "ALTO",
    }:
        return "PRIORIZAR XI"

    if premium_active:
        return "VENTANA ESTRATÉGICA"

    if missing > 0:
        return "CONSTRUIR XI"

    return "OPTIMIZAR PLANTILLA"


# ======================================================
# AJUSTE TEMPORAL
# ======================================================


def calculate_time_adjustment(
    deadline: dict,
) -> float:
    """
    Muchos días restantes:
    podemos tolerar un XI incompleto hoy.

    Cerca del deadline:
    completar XI y asegurar solvencia domina.
    """

    lineup_risk = (
        deadline[
            "lineup_risk"
        ]
    )

    premium_freedom = (
        deadline[
            "premium_freedom_bonus"
        ]
    )

    adjustment = float(
        premium_freedom
    )

    if lineup_risk == "CRITICO":
        adjustment -= 20

    elif lineup_risk == "MUY_ALTO":
        adjustment -= 12

    elif lineup_risk == "ALTO":
        adjustment -= 7

    elif lineup_risk == "MODERADO":
        adjustment -= 3

    return adjustment


# ======================================================
# MERCADOS FUTUROS
# ======================================================


def calculate_market_cycle_adjustment(
    deadline: dict,
) -> float:
    """
    Cuantos más mercados queden antes del bloqueo
    del XI, mayor libertad tenemos para capturar
    hoy una oportunidad escasa.
    """

    future = (
        deadline[
            "future_market_opportunities"
        ]
    )

    cycles = (
        future.get(
            "cycles"
        )
    )

    if cycles is None:
        return 0.0

    if cycles >= 5:
        return 6.0

    if cycles >= 3:
        return 4.0

    if cycles >= 1:
        return 1.0

    return -8.0


# ======================================================
# PRESIÓN DE VENTAS
# ======================================================


def calculate_sale_adjustment(
    sale_pressure: float,
) -> float:

    if sale_pressure > 40:
        return -15.0

    if sale_pressure > 30:
        return -10.0

    if sale_pressure > 20:
        return -7.0

    if sale_pressure > 10:
        return -3.0

    if sale_pressure > 0:
        return -1.0

    return 0.0


# ======================================================
# FRANCHISE ADJUSTMENT
# ======================================================


def calculate_franchise_adjustment(
    franchise_score: float,
) -> float:
    """
    Bonus reservado para jugadores realmente
    diferenciales.

    IMPORTANTE:

    Ya NO utilizamos Strategic Score aquí.

    Un jugador puede ser:

        Strategic 70+
        Franchise 55

    y seguir siendo un gran fichaje, pero NO debe
    autorizar una reestructuración agresiva.

    Solo Franchise permite romper el plan normal.
    """

    if franchise_score >= 95:
        return 18.0

    if franchise_score >= 90:
        return 15.0

    if franchise_score >= 85:
        return 10.0

    if franchise_score >= 80:
        return 7.0

    if franchise_score >= 75:
        return 4.0

    if franchise_score >= 70:
        return 2.0

    return 0.0


# ======================================================
# VALIDACIÓN HARD DEL PREMIUM
# ======================================================


def validate_premium_target(
    target: dict | None,
) -> tuple[
    bool,
    str,
]:

    if not target:

        return (
            False,
            "No existe objetivo premium.",
        )

    ownership_state = (
        target.get(
            "ownership_state"
        )
    )

    if ownership_state != "EN_MERCADO":

        return (
            False,
            "El objetivo Franchise no está actualmente "
            "en el mercado.",
        )

    franchise_score = float(
        target.get(
            "franchise_score",
            0,
        )
        or 0
    )

    if (
        franchise_score
        < MIN_RESTRUCTURE_FRANCHISE_SCORE
    ):

        return (
            False,
            "El objetivo no alcanza el Franchise Score "
            "mínimo para permitir una reestructuración.",
        )

    if not target.get(
        "can_trigger_restructure",
        False,
    ):

        return (
            False,
            "El Franchise Engine no autoriza una "
            "reestructuración por este jugador.",
        )

    availability = (
        target.get(
            "availability",
            {}
        )
        or {}
    )

    if not availability.get(
        "available",
        True,
    ):

        return (
            False,
            "El jugador no está disponible "
            "deportivamente.",
        )

    return (
        True,
        "Objetivo Franchise válido.",
    )


# ======================================================
# DECISION GATE
# ======================================================


def build_strategic_decision(
    snapshot: dict,
) -> dict:

    comparison = (
        compare_strategic_plans(
            snapshot
        )
    )

    budget = (
        build_strategic_budget(
            snapshot
        )
    )

    deadline = (
        build_deadline_state(
            snapshot
        )
    )

    premium = (
        comparison.get(
            "premium",
            {}
        )
        or {}
    )

    comparison_premium_active = bool(
        premium.get(
            "available"
        )
    )

    target = (
        premium.get(
            "target"
        )
    )

    (
        premium_valid,
        premium_validation_reason,
    ) = validate_premium_target(
        target
    )

    premium_active = (
        comparison_premium_active
        and premium_valid
    )

    phase = determine_season_phase(
        deadline=
            deadline,

        premium_active=
            premium_active,
    )

    # ==================================================
    # SIN PREMIUM ACCIONABLE
    # ==================================================

    if not premium_active:

        return {
            "phase":
                phase,

            "decision":
                "MANTENER_PLAN_TACTICO",

            "premium_active":
                False,

            "premium_target":
                target,

            "premium_validation":
                premium_validation_reason,

            "difference":
                None,

            "effective_difference":
                None,

            "reason": (
                "No existe una oportunidad Franchise "
                "accionable que permita reestructurar "
                "el plan actual. "
                + premium_validation_reason
            ),

            "comparison":
                comparison,

            "budget":
                budget,

            "deadline":
                deadline,
        }

    # ==================================================
    # DATOS DEL OBJETIVO
    # ==================================================

    difference = float(
        comparison.get(
            "difference",
            0,
        )
        or 0
    )

    minimum_sale_needed = int(
        premium.get(
            "minimum_sale_needed",
            0,
        )
        or 0
    )

    balance = int(
        budget[
            "balance"
        ]
    )

    sale_pressure = (
        calculate_sale_pressure(
            minimum_sale_needed=
                minimum_sale_needed,

            balance=
                balance,
        )
    )

    strategic_score = float(
        target.get(
            "strategic_score",
            0,
        )
        or 0
    )

    franchise_score = float(
        target.get(
            "franchise_score",
            0,
        )
        or 0
    )

    franchise_classification = (
        target.get(
            "franchise_classification",
            "NO FRANCHISE",
        )
    )

    # ==================================================
    # AJUSTES
    # ==================================================

    time_adjustment = (
        calculate_time_adjustment(
            deadline
        )
    )

    market_cycle_adjustment = (
        calculate_market_cycle_adjustment(
            deadline
        )
    )

    sale_adjustment = (
        calculate_sale_adjustment(
            sale_pressure
        )
    )

    franchise_adjustment = (
        calculate_franchise_adjustment(
            franchise_score
        )
    )

    effective_difference = (
        difference
        + time_adjustment
        + market_cycle_adjustment
        + sale_adjustment
        + franchise_adjustment
    )

    # ==================================================
    # HARD SAFETY
    # ==================================================
    #
    # El Franchise Score NUNCA puede saltarse este
    # bloqueo.
    #
    # Cerca del deadline:
    #
    # 1. XI válido.
    # 2. Saldo no negativo.
    # 3. Después, oportunidades premium.
    #
    # ==================================================

    if deadline[
        "hard_safety_mode"
    ]:

        decision = (
            "PRIORIZAR_XI_Y_SOLVENCIA"
        )

        reason = (
            "Estamos demasiado cerca del deadline. "
            "La prioridad absoluta es asegurar XI "
            "válido y saldo no negativo. Ni siquiera "
            "un jugador Franchise puede saltarse "
            "esta protección."
        )

    # ==================================================
    # DECISIÓN NORMAL
    # ==================================================

    elif effective_difference >= 18:

        decision = (
            "REESTRUCTURAR_POR_FRANCHISE"
        )

        reason = (
            "Existe una oportunidad Franchise real en "
            "el mercado y su ventaja supera claramente "
            "al plan actual considerando calidad de "
            "temporada, carácter diferencial, calendario, "
            "liquidez y mercados futuros."
        )

    elif effective_difference >= 10:

        decision = (
            "PRIORIZAR_FRANCHISE"
        )

        reason = (
            "El objetivo Franchise merece prioridad. "
            "El calendario permite asumir riesgo "
            "controlado y reconstruir el XI en mercados "
            "posteriores."
        )

    elif effective_difference >= 5:

        decision = (
            "ESTUDIAR_REESTRUCTURACION"
        )

        reason = (
            "El jugador Franchise ofrece ventaja "
            "suficiente para revisar pujas secundarias, "
            "pero todavía no justifica una "
            "reestructuración agresiva."
        )

    elif effective_difference >= 0:

        decision = (
            "MANTENER_Y_VIGILAR_FRANCHISE"
        )

        reason = (
            "La oportunidad Franchise es interesante, "
            "pero la ventaja frente al plan actual "
            "todavía es demasiado pequeña."
        )

    else:

        decision = (
            "MANTENER_PLAN_TACTICO"
        )

        reason = (
            "Aunque existe un jugador Franchise en "
            "mercado, el plan actual ofrece mejor "
            "equilibrio entre valor estratégico, "
            "cobertura y liquidez."
        )

    # ==================================================
    # RESULTADO
    # ==================================================

    return {
        "phase":
            phase,

        "decision":
            decision,

        "premium_active":
            True,

        "premium_target":
            target,

        "premium_validation":
            premium_validation_reason,

        "strategic_score":
            round(
                strategic_score,
                1,
            ),

        "franchise_score":
            round(
                franchise_score,
                1,
            ),

        "franchise_classification":
            franchise_classification,

        "difference":
            round(
                difference,
                2,
            ),

        "effective_difference":
            round(
                effective_difference,
                2,
            ),

        "adjustments": {
            "time":
                round(
                    time_adjustment,
                    2,
                ),

            "future_markets":
                round(
                    market_cycle_adjustment,
                    2,
                ),

            "sale_pressure":
                round(
                    sale_adjustment,
                    2,
                ),

            "franchise":
                round(
                    franchise_adjustment,
                    2,
                ),
        },

        "minimum_sale_needed":
            minimum_sale_needed,

        "sale_pressure_percent":
            round(
                sale_pressure,
                1,
            ),

        "reason":
            reason,

        "comparison":
            comparison,

        "budget":
            budget,

        "deadline":
            deadline,
    }