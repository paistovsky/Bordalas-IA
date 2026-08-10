from src.analysis.restructuring_roster_impact_engine import (
    build_restructuring_roster_impact_plan,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


# ======================================================
# CONSTANTES
# ======================================================


SAFE_RESTRUCTURING_RECOMMENDATIONS = {
    "REESTRUCTURACION_DEPORTIVAMENTE_SEGURA",
    "REESTRUCTURACION_ASUMIBLE",
}


SAFE_FINANCIAL_RECOMMENDATIONS = {
    "FRANCHISE_FINANCIABLE",
    "REESTRUCTURAR_Y_ATACAR",
}


# ======================================================
# UTILIDADES
# ======================================================


def money(
    value: int | float,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def get_first_cancellation(
    impact_plan: dict,
) -> dict | None:
    """
    Devuelve SOLO la primera cancelación recomendada.

    Nunca asumimos que la segunda cancelación seguirá
    siendo correcta tras ejecutar la primera.

    Flujo:

        cancelar una
        -> refresh
        -> recalcular
        -> decidir siguiente acción
    """

    combination = (
        impact_plan.get(
            "best_combination"
        )
    )

    if not combination:
        return None

    players = (
        combination.get(
            "players",
            [],
        )
    )

    if not players:
        return None

    return players[0]


# ======================================================
# VALIDACIÓN DEL PLAN
# ======================================================


def validate_franchise_plan(
    impact_plan: dict,
) -> dict:

    if not impact_plan.get(
        "active"
    ):

        return {
            "valid":
                False,

            "status":
                "SIN_FRANCHISE",

            "reason":
                impact_plan.get(
                    "reason",
                    (
                        "No existe una operación "
                        "Franchise activa."
                    ),
                ),
        }

    restructuring = (
        impact_plan.get(
            "restructuring",
            {},
        )
        or {}
    )

    if not restructuring:

        return {
            "valid":
                False,

            "status":
                "SIN_PLAN_FINANCIERO",

            "reason":
                (
                    "No existe información de "
                    "reestructuración financiera."
                ),
        }

    financial_recommendation = (
        restructuring.get(
            "recommendation"
        )
    )

    roster_recommendation = (
        impact_plan.get(
            "recommendation"
        )
    )

    # ==================================================
    # HARD SAFETY
    # ==================================================

    solvency = (
        restructuring.get(
            "solvency",
            {},
        )
        or {}
    )

    hard_safety = (
        solvency.get(
            "hard_safety",
            {},
        )
        or {}
    )

    hard_safety_active = bool(
        hard_safety.get(
            "active",
            False,
        )
    )

    if hard_safety_active:

        reasons = (
            hard_safety.get(
                "reasons",
                [],
            )
            or []
        )

        reason_text = (
            "; ".join(
                str(reason)
                for reason in reasons
            )
        )

        if not reason_text:

            reason_text = (
                "Hard Safety activo."
            )

        return {
            "valid":
                False,

            "status":
                "HARD_SAFETY",

            "reason":
                (
                    "El motor de solvencia ha activado "
                    "Hard Safety. No se permite iniciar "
                    "la operación Franchise. "
                    f"{reason_text}"
                ),
        }

    # ==================================================
    # COBERTURA DE DEUDA
    # ==================================================

    if not restructuring.get(
        "debt_theoretically_covered",
        False,
    ):

        return {
            "valid":
                False,

            "status":
                "DEUDA_NO_CUBIERTA",

            "reason":
                (
                    "La deuda temporal proyectada no "
                    "está cubierta por la liquidez "
                    "recuperable detectada."
                ),
        }

    # ==================================================
    # VALIDACIÓN FINANCIERA
    # ==================================================

    if (
        financial_recommendation
        not in SAFE_FINANCIAL_RECOMMENDATIONS
    ):

        return {
            "valid":
                False,

            "status":
                "FINANCIACION_NO_AUTORIZADA",

            "reason":
                (
                    "El motor financiero no recomienda "
                    "atacar actualmente al Franchise. "
                    f"Estado: "
                    f"{financial_recommendation}"
                ),
        }

    # ==================================================
    # VALIDACIÓN DE PLANTILLA
    # ==================================================

    required_unlock = int(
        impact_plan.get(
            "required_unlock",
            0,
        )
        or 0
    )

    if (
        required_unlock > 0
        and
        roster_recommendation
        not in SAFE_RESTRUCTURING_RECOMMENDATIONS
    ):

        return {
            "valid":
                False,

            "status":
                "IMPACTO_DEPORTIVO_EXCESIVO",

            "reason":
                (
                    "La reestructuración financiera "
                    "es posible, pero el impacto sobre "
                    "la plantilla es demasiado elevado. "
                    f"Estado: "
                    f"{roster_recommendation}"
                ),
        }

    return {
        "valid":
            True,

        "status":
            "PLAN_VALIDO",

        "reason":
            (
                "La operación Franchise supera las "
                "validaciones financiera, deportiva "
                "y de solvencia."
            ),
    }


# ======================================================
# CONSTRUIR SIGUIENTE ACCIÓN
# ======================================================


def build_next_franchise_action(
    snapshot: dict,
) -> dict:
    """
    Determina UNA sola acción.

    NO modifica Biwenger.

    Posibles acciones:

        CANCEL_BID
        PLACE_FRANCHISE_BID
        WAIT
        ABORT
    """

    impact = (
        build_restructuring_roster_impact_plan(
            snapshot
        )
    )

    validation = (
        validate_franchise_plan(
            impact
        )
    )

    if not validation[
        "valid"
    ]:

        return {
            "action":
                "ABORT",

            "validation":
                validation,

            "impact_plan":
                impact,
        }

    restructuring = (
        impact[
            "restructuring"
        ]
    )

    economy = (
        restructuring[
            "economy"
        ]
    )

    target = (
        impact[
            "target"
        ]
    )

    target_bid = int(
        economy[
            "target_bid"
        ]
    )

    maximum_bid = int(
        economy[
            "maximum_bid"
        ]
    )

    required_unlock = int(
        economy[
            "required_unlock"
        ]
    )

    # ==================================================
    # YA TENEMOS CAPACIDAD PARA PUJAR
    # ==================================================

    if maximum_bid >= target_bid:

        return {
            "action":
                "PLACE_FRANCHISE_BID",

            "target":
                target,

            "amount":
                target_bid,

            "maximum_bid":
                maximum_bid,

            "projected_balance":
                economy[
                    "projected_balance_if_won"
                ],

            "projected_debt":
                economy[
                    "projected_debt_if_won"
                ],

            "recoverable_cash":
                restructuring.get(
                    "recoverable_cash",
                    0,
                ),

            "debt_coverage_ratio":
                restructuring.get(
                    "debt_coverage_ratio"
                ),

            "validation":
                validation,

            "impact_plan":
                impact,
        }

    # ==================================================
    # NECESITAMOS CANCELAR UNA PUJA
    # ==================================================

    if required_unlock > 0:

        player = (
            get_first_cancellation(
                impact
            )
        )

        if player is None:

            return {
                "action":
                    "ABORT",

                "validation": {
                    "valid":
                        False,

                    "status":
                        "SIN_CANCELACION_VALIDA",

                    "reason":
                        (
                            "Es necesario liberar capital "
                            "pero no existe una cancelación "
                            "válida disponible."
                        ),
                },

                "impact_plan":
                    impact,
            }

        offer_id = (
            player.get(
                "offer_id"
            )
        )

        if offer_id is None:

            return {
                "action":
                    "ABORT",

                "validation": {
                    "valid":
                        False,

                    "status":
                        "OFFER_ID_DESCONOCIDO",

                    "reason":
                        (
                            "La puja recomendada para "
                            "cancelar no contiene offer_id."
                        ),
                },

                "impact_plan":
                    impact,
            }

        return {
            "action":
                "CANCEL_BID",

            "player_id":
                player[
                    "id"
                ],

            "player_name":
                player[
                    "name"
                ],

            "offer_id":
                int(
                    offer_id
                ),

            "amount":
                int(
                    player[
                        "bid_amount"
                    ]
                ),

            "keep_score":
                player.get(
                    "keep_score"
                ),

            "required_unlock":
                required_unlock,

            "maximum_bid":
                maximum_bid,

            "target_bid":
                target_bid,

            "validation":
                validation,

            "impact_plan":
                impact,
        }

    return {
        "action":
            "WAIT",

        "validation":
            validation,

        "impact_plan":
            impact,
    }


# ======================================================
# DRY RUN
# ======================================================


def run_franchise_dry_run(
    snapshot: dict,
) -> dict:

    result = (
        build_next_franchise_action(
            snapshot
        )
    )

    action = (
        result[
            "action"
        ]
    )

    print()
    print("=" * 90)
    print(
        "BORDALÁS IA - FRANCHISE EXECUTOR"
    )
    print("=" * 90)

    impact = (
        result.get(
            "impact_plan",
            {},
        )
        or {}
    )

    if impact.get(
        "active"
    ):

        target = (
            impact.get(
                "target",
                {},
            )
            or {}
        )

        restructuring = (
            impact.get(
                "restructuring",
                {},
            )
            or {}
        )

        economy = (
            restructuring.get(
                "economy",
                {},
            )
            or {}
        )

        solvency = (
            restructuring.get(
                "solvency",
                {},
            )
            or {}
        )

        hard_safety = (
            solvency.get(
                "hard_safety",
                {},
            )
            or {}
        )

        print()
        print(
            "OBJETIVO FRANCHISE"
        )

        print(
            "-" * 90
        )

        print()

        print(
            f"Jugador:              "
            f"{target.get('name')}"
        )

        print(
            f"Franchise:            "
            f"{target.get('franchise_score', 0)}/100"
        )

        print(
            f"Strategic:            "
            f"{target.get('strategic_score', 0)}/100"
        )

        print(
            f"Valor mercado:        "
            f"{money(target.get('price', 0))}"
        )

        print()

        print(
            f"Saldo:                "
            f"{money(economy.get('balance', 0))}"
        )

        print(
            f"Puja máxima:          "
            f"{money(economy.get('maximum_bid', 0))}"
        )

        print(
            f"Puja objetivo:        "
            f"{money(economy.get('target_bid', 0))}"
        )

        print(
            f"Capital a desbloquear:"
            f" {money(economy.get('required_unlock', 0))}"
        )

        print()

        print(
            f"Saldo si ganamos:     "
            f"{money(economy.get('projected_balance_if_won', 0))}"
        )

        print(
            f"Deuda proyectada:     "
            f"{money(economy.get('projected_debt_if_won', 0))}"
        )

        print(
            f"Liquidez recuperable: "
            f"{money(restructuring.get('recoverable_cash', 0))}"
        )

        ratio = (
            restructuring.get(
                "debt_coverage_ratio"
            )
        )

        if ratio is not None:

            print(
                f"Cobertura deuda:      "
                f"{ratio:.2f}x"
            )

        print()

        print(
            f"Riesgo solvencia:     "
            f"{solvency.get('risk')}"
        )

        print(
            f"Hard Safety:          "
            f"{'SÍ' if hard_safety.get('active', False) else 'NO'}"
        )

        deadline = (
            solvency.get(
                "deadline",
                {},
            )
            or {}
        )

        calendar = (
            deadline.get(
                "calendar",
                {},
            )
            or {}
        )

        print(
            f"Deadline XI:          "
            f"{calendar.get('time_to_lineup_lock')}"
        )

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    print()
    print(
        "VALIDACIÓN"
    )

    print(
        "-" * 90
    )

    validation = (
        result.get(
            "validation",
            {},
        )
        or {}
    )

    print()

    print(
        f"Estado: "
        f"{validation.get('status')}"
    )

    print(
        validation.get(
            "reason",
            "",
        )
    )

    # ==================================================
    # SIGUIENTE ACCIÓN
    # ==================================================

    print()
    print(
        "SIGUIENTE ACCIÓN"
    )

    print(
        "-" * 90
    )

    print()

    if action == "CANCEL_BID":

        print(
            "CANCELAR UNA ÚNICA PUJA"
        )

        print()

        print(
            f"Jugador:      "
            f"{result['player_name']}"
        )

        print(
            f"Player ID:    "
            f"{result['player_id']}"
        )

        print(
            f"Offer ID:     "
            f"{result['offer_id']}"
        )

        print(
            f"Importe:      "
            f"{money(result['amount'])}"
        )

        print(
            f"Keep score:   "
            f"{result.get('keep_score')}"
        )

        print()

        print(
            f"Falta liberar:"
            f" {money(result['required_unlock'])}"
        )

        print()

        print(
            "Después de cancelar esta única puja:"
        )

        print(
            "1. Refrescar Biwenger."
        )

        print(
            "2. Crear snapshot nuevo."
        )

        print(
            "3. Recalcular todo el plan."
        )

        print(
            "4. No asumir que la siguiente "
            "cancelación sigue siendo la misma."
        )

    elif action == "PLACE_FRANCHISE_BID":

        target = (
            result[
                "target"
            ]
        )

        print(
            "PUJAR POR EL FRANCHISE"
        )

        print()

        print(
            f"Jugador:      "
            f"{target['name']}"
        )

        print(
            f"Player ID:    "
            f"{target['id']}"
        )

        print(
            f"Puja:         "
            f"{money(result['amount'])}"
        )

        print(
            f"Puja máxima:  "
            f"{money(result['maximum_bid'])}"
        )

        print()

        print(
            f"Saldo teórico posterior: "
            f"{money(result['projected_balance'])}"
        )

        print(
            f"Deuda temporal:          "
            f"{money(result['projected_debt'])}"
        )

        print(
            f"Liquidez recuperable:    "
            f"{money(result['recoverable_cash'])}"
        )

    elif action == "ABORT":

        print(
            "ABORTAR OPERACIÓN"
        )

        print()

        print(
            validation.get(
                "reason",
                "",
            )
        )

    else:

        print(
            "ESPERAR / RECALCULAR"
        )

    print()
    print(
        "MODO: DRY-RUN"
    )

    print(
        "No se ha modificado Biwenger."
    )

    print()
    print("=" * 90)

    return result


# ======================================================
# EJECUTAR UNA ÚNICA ACCIÓN
# ======================================================


def execute_single_franchise_action(
    snapshot: dict,
    execute: bool = False,
) -> dict:
    """
    Ejecuta como máximo UNA operación Franchise.

    Si execute=False:
        DRY-RUN.

    Si execute=True:
        CANCEL_BID
        o
        PLACE_FRANCHISE_BID

    Nunca ejecuta dos operaciones consecutivas.
    """

    next_action = (
        build_next_franchise_action(
            snapshot
        )
    )

    action = (
        next_action[
            "action"
        ]
    )

    if action in {
        "ABORT",
        "WAIT",
    }:

        return {
            **next_action,

            "executed":
                False,

            "success":
                False,

            "status":
                action,
        }

    # ==================================================
    # DRY RUN
    # ==================================================

    if not execute:

        return {
            **next_action,

            "executed":
                False,

            "success":
                True,

            "status":
                "DRY_RUN_OK",
        }

    writer = (
        BiwengerWriteClient()
    )

    # ==================================================
    # CANCELAR UNA PUJA
    # ==================================================

    if action == "CANCEL_BID":

        result = (
            writer.cancel_bid(
                offer_id=
                    next_action[
                        "offer_id"
                    ],

                execute=True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            **next_action,

            "executed":
                True,

            "success":
                success,

            "status":
                (
                    "CANCELLED"
                    if success
                    else "FAILED"
                ),

            "write_result":
                result,
        }

    # ==================================================
    # PUJA FRANCHISE
    # ==================================================

    if action == "PLACE_FRANCHISE_BID":

        target = (
            next_action[
                "target"
            ]
        )

        result = (
            writer.place_bid(
                player_id=
                    target[
                        "id"
                    ],

                amount=
                    next_action[
                        "amount"
                    ],

                seller_user_id=
                    None,

                execute=True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            **next_action,

            "executed":
                True,

            "success":
                success,

            "status":
                (
                    "BID_PLACED"
                    if success
                    else "FAILED"
                ),

            "write_result":
                result,
        }

    return {
        **next_action,

        "executed":
            False,

        "success":
            False,

        "status":
            "UNKNOWN_ACTION",
    }