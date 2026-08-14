from src.actions.franchise_autopilot import (
    build_franchise_autopilot_state,
)

from src.analysis.computer_offer_reroll_engine import (
    build_computer_offer_reroll_board,
)

from src.analysis.accept_before_expiry_safety_engine import (
    build_accept_before_expiry_safety_board,
)

from src.analysis.market_listing_lifecycle_engine import (
    build_market_listing_lifecycle_board,
)

from src.analysis.lineup_monitor import (
    build_lineup_monitor_state,
)

from src.analysis.liquidity_manager import (
    build_liquidity_state,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)

from src.analysis.portfolio_roi_engine import (
    build_portfolio_roi_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
    build_t15_solvency_forecast,
    evaluate_purchase_at_t15,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


PRIORITY = {
    # Barrera temporal absoluta.
    "ROUND_LOCK": 2000,

    # Emergencias reales antes de T-15.
    "EMERGENCY_SOLVENCY": 1100,
    "EMERGENCY_LINEUP": 1080,
    "HARD_SAFETY": 1040,

    # Fases previas.
    "SOLVENCY_FINALIZATION": 1010,
    "LINEUP_UPDATE_EMERGENCY": 1000,
    "LINEUP_VERY_HIGH": 980,
    "LINEUP_UPDATE_VERY_HIGH": 975,
    "SOLVENCY_HIGH_ATTENTION": 960,
    "LINEUP_HIGH": 940,
    "LINEUP_UPDATE_HIGH": 935,
    "FRANCHISE_ACTION": 900,
    "FRANCHISE_WAIT": 880,
    "LINEUP_MODERATE": 820,
    "LINEUP_UPDATE_MODERATE": 835,
    "SOLVENCY_PREPARATION": 780,
    "LINEUP_UPDATE_LOW": 760,
    "LINEUP_LOW": 700,
    "MARKET_LISTING_RENEW": 660,
    "INCOMING_OFFERS": 650,
    "COMPUTER_OFFER_REROLL_WATCH": 670,
    "ACCEPT_EXPIRY_WATCH": 665,
    "ACCEPT_EXPIRY_URGENT": 680,
    "PLAYER_RISK_EXIT": 600,
    "LIQUIDITY_MAINTENANCE": 550,
    "SOLVENCY_NORMAL": 500,
    "SPECULATION_BUY": 400,
    "SPECULATION_WATCH": 300,
    "IDLE": 0,
}


# ============================================================
# FEATURE FLAGS
# ============================================================

# Todavia permanece desactivado hasta terminar la validacion
# del Orchestrator corregido.
ENABLE_LIVE_COMPUTER_REROLL = True

# Renovacion automatica de publicaciones del mercado.
# Observer hasta validar el lifecycle completo.
ENABLE_LIVE_MARKET_LISTING_RENEW = True

# Aceptacion automatica SOLO para clusters criticos y urgentes.
# El executor hace read-before-write y revalidacion completa.
ENABLE_LIVE_ACCEPT_BEFORE_EXPIRY = True

# Compra especulativa LIVE conservadora:
# solo con saldo positivo y candidato ejecutable.
# El executor refresca y recalcula antes de pujar.
ENABLE_LIVE_SPECULATION_BUY = True


LOCK_PHASES = {
    "ROUND_LOCKED",
    "ROUND_TRANSITION_LOCK",
}


RISKY_PHASES = {
    "FINALIZATION",
    "HARD_SAFETY",
    "ROUND_LOCKED",
    "ROUND_TRANSITION_LOCK",
}


def hours_remaining(
    seconds: int | None,
) -> float | None:

    if seconds is None:
        return None

    return max(
        seconds / 3600,
        0.0,
    )


def get_hard_safety(
    solvency: dict,
) -> dict:

    return (
        solvency.get(
            "hard_safety",
            {},
        )
        or {}
    )


def get_deadline_phase(
    solvency: dict,
) -> str:

    deadline = (
        solvency.get(
            "deadline",
            {},
        )
        or {}
    )

    return str(
        deadline.get(
            "phase",
            "CALENDAR_UNKNOWN",
        )
    )


def build_temporal_gate(
    solvency: dict,
) -> dict:

    deadline = (
        solvency.get(
            "deadline",
            {},
        )
        or {}
    )

    phase = get_deadline_phase(
        solvency
    )

    return {
        "phase":
            phase,

        "operations_locked":
            bool(
                deadline.get(
                    "operations_locked",
                    False,
                )
                or
                phase in LOCK_PHASES
            ),

        "hard_safety_mode":
            bool(
                deadline.get(
                    "hard_safety_mode",
                    False,
                )
                or
                phase == "HARD_SAFETY"
            ),

        "target_matchday":
            deadline.get(
                "target_matchday"
            ),

        "next_matchday":
            deadline.get(
                "next_matchday"
            ),

        "real_deadline":
            deadline.get(
                "real_deadline"
            ),

        "first_kickoff":
            deadline.get(
                "first_kickoff"
            ),

        "next_round_unlock":
            deadline.get(
                "next_round_unlock"
            ),
    }




def build_action_queue(
    candidates: list[dict],
    *,
    shadow: bool = False,
) -> list[dict]:
    """
    Separa la preocupacion principal de las acciones posibles.

    En LIVE solo cuentan candidatos executable=True.
    En SHADOW tambien cuentan shadow_executable=True, pero el
    resultado nunca se envia al executor de produccion.
    """

    queue = []

    for candidate in candidates:

        executable = bool(
            candidate.get("executable", False)
        )

        shadow_executable = bool(
            candidate.get(
                "shadow_executable",
                False,
            )
        )

        if executable or (
            shadow
            and shadow_executable
        ):
            queue.append(candidate)

    queue.sort(
        key=lambda item: int(
            item.get("priority", 0) or 0
        ),
        reverse=True,
    )

    return queue


def build_shadow_speculation_candidate(
    *,
    speculation: dict,
    solvency: dict,
    phase: str,
    hard_safety_mode: bool,
    operations_locked: bool,
) -> dict | None:
    """
    Construye una compra especulativa solo para Market Brain
    SHADOW cuando el engine ya la considera comprable y la
    simulacion T-15 confirma que la deuda adicional es segura.

    No cambia ENABLE_LIVE_SPECULATION_BUY ni el executor actual.
    """

    if operations_locked or hard_safety_mode:
        return None

    if phase not in {"NORMAL", "PREPARATION"}:
        return None

    budget = (
        speculation.get("budget", {})
        or {}
    )

    if not budget.get("enabled", False):
        return None

    executable_buys = (
        speculation.get("executable_buys", [])
        or []
    )

    if not executable_buys:
        return None

    player = executable_buys[0]

    price = int(
        player.get("price", 0) or 0
    )

    if price <= 0:
        return None

    purchase_forecast = evaluate_purchase_at_t15(
        solvency=solvency,
        purchase_amount=price,
    )

    if not purchase_forecast.get("safe", False):
        return None

    return {
        "type": "SPECULATION_BUY_SHADOW",
        "priority": PRIORITY["SPECULATION_BUY"],
        "action": "BUY_SPECULATION",
        "executable": False,
        "shadow_executable": True,
        "executor": None,
        "shadow_executor": "MARKET_BRAIN_V10",
        "reason": (
            "Market Brain V10 SHADOW: oportunidad especulativa "
            "compatible con la solvencia proyectada T-15."
        ),
        "data": {
            "player": player,
            "budget": budget,
            "t15_purchase_forecast": purchase_forecast,
        },
    }


def build_lineup_state_from_monitor(
    monitor: dict,
) -> dict:

    lineup = (
        monitor.get(
            "lineup",
            {},
        )
        or {}
    )

    playable_count = int(
        lineup.get(
            "playable_count",
            0,
        )
        or 0
    )

    missing = max(
        11
        - playable_count,
        0,
    )

    return {
        "lineup":
            lineup,

        "playable_count":
            playable_count,

        "missing":
            missing,

        "shortages":
            lineup.get(
                "matchday_shortages",
                {},
            )
            or {},

        "complete":
            playable_count >= 11,
    }


def calculate_lineup_priority(
    missing: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
    pressure_score: int,
    phase: str,
) -> int:

    if missing <= 0:
        return 0

    if phase in LOCK_PHASES:
        return PRIORITY["EMERGENCY_LINEUP"]

    if phase == "HARD_SAFETY":
        return PRIORITY["EMERGENCY_LINEUP"]

    if phase == "FINALIZATION":
        return 1020

    if phase == "HIGH_ATTENTION":
        return PRIORITY["LINEUP_VERY_HIGH"]

    if phase == "PREPARATION":
        return PRIORITY["LINEUP_HIGH"]

    if seconds_to_deadline is None:

        return (
            PRIORITY[
                "LINEUP_MODERATE"
            ]
            + min(
                pressure_score,
                50,
            )
        )

    hours = hours_remaining(
        seconds_to_deadline
    )

    if hours is not None and hours <= 48:

        return PRIORITY[
            "LINEUP_HIGH"
        ]

    return (
        PRIORITY[
            "LINEUP_LOW"
        ]
        + min(
            missing * 10,
            40,
        )
    )


def calculate_lineup_update_priority(
    phase: str,
    seconds_to_deadline: int | None,
) -> int:

    if phase in LOCK_PHASES:
        return 0

    if phase == "HARD_SAFETY":
        return PRIORITY[
            "LINEUP_UPDATE_EMERGENCY"
        ]

    if phase == "FINALIZATION":
        return PRIORITY[
            "LINEUP_UPDATE_VERY_HIGH"
        ]

    if phase == "HIGH_ATTENTION":
        return PRIORITY[
            "LINEUP_UPDATE_HIGH"
        ]

    if phase == "PREPARATION":
        return PRIORITY[
            "LINEUP_UPDATE_MODERATE"
        ]

    if seconds_to_deadline is None:
        return PRIORITY[
            "LINEUP_UPDATE_MODERATE"
        ]

    return PRIORITY[
        "LINEUP_UPDATE_LOW"
    ]


def calculate_franchise_priority(
    franchise_state: str,
    lineup_risk: str,
    seconds_to_deadline: int | None,
    missing: int,
    phase: str,
    balance: int,
) -> int:

    if franchise_state in {
        "CANCEL_BID",
        "PLACE_FRANCHISE_BID",
    }:

        base = PRIORITY[
            "FRANCHISE_ACTION"
        ]

    elif (
        franchise_state
        == "WAIT_FRANCHISE_RESOLUTION"
    ):

        base = PRIORITY[
            "FRANCHISE_WAIT"
        ]

    else:
        return 0

    # En lock no se actua.
    if phase in LOCK_PHASES:
        return 0

    # A T-90/T-15 ya no iniciamos operaciones Franchise.
    if phase in {
        "HARD_SAFETY",
        "FINALIZATION",
    }:

        if (
            franchise_state
            == "WAIT_FRANCHISE_RESOLUTION"
        ):
            return 500

        return 0

    # Con saldo negativo cerca del deadline,
    # solvencia debe ganar.
    if (
        balance < 0
        and
        phase
        in {
            "HIGH_ATTENTION",
            "PREPARATION",
        }
    ):
        base -= 150

    if missing > 0:

        if phase == "HIGH_ATTENTION":
            return min(
                base,
                700,
            )

        if phase == "PREPARATION":
            return min(
                base,
                820,
            )

    if seconds_to_deadline is None:
        return max(
            base - 100,
            0,
        )

    if (
        lineup_risk
        in {
            "ALTO",
            "MUY_ALTO",
            "CRITICO",
        }
        and
        phase
        != "NORMAL"
    ):

        return min(
            base,
            800,
        )

    return base


def calculate_solvency_priority(
    balance: int,
    phase: str,
    seconds_to_deadline: int | None,
) -> int:

    if balance >= 0:
        return 0

    if phase in LOCK_PHASES:

        # La jornada ya ha cerrado.
        # No intentamos "arreglar" la jornada anterior.
        return 0

    if phase == "HARD_SAFETY":
        return PRIORITY[
            "EMERGENCY_SOLVENCY"
        ]

    if phase == "FINALIZATION":
        return PRIORITY[
            "SOLVENCY_FINALIZATION"
        ]

    if phase == "HIGH_ATTENTION":
        return PRIORITY[
            "SOLVENCY_HIGH_ATTENTION"
        ]

    if phase == "PREPARATION":
        return PRIORITY[
            "SOLVENCY_PREPARATION"
        ]

    if seconds_to_deadline is None:

        return PRIORITY[
            "SOLVENCY_HIGH_ATTENTION"
        ]

    # En NORMAL estar en negativo es legal:
    # debemos vigilar y generar liquidez,
    # pero no tiene por que bloquear Franchise/mercado.
    return PRIORITY[
        "SOLVENCY_NORMAL"
    ]


def calculate_accept_expiry_priority(
    balance: int,
    phase: str,
) -> int:
    """
    Una oferta cuya perdida rompe SOLVENCY_GUARANTEE es una accion de
    solvencia, no una simple decision comercial.

    Cuando el saldo es negativo debe ganar a cualquier cambio del XI,
    reroll o mantenimiento. La ventana urgente ya esta limitada por el
    motor Accept-Before-Expiry a las seis horas anteriores al deadline
    efectivo, por lo que esta prioridad no provoca ventas prematuras.
    """
    if phase in LOCK_PHASES:
        return 0

    if balance < 0:
        return PRIORITY["EMERGENCY_SOLVENCY"] + 10

    return PRIORITY["ACCEPT_EXPIRY_URGENT"]


def add_temporal_gate(
    candidates: list[dict],
    temporal_gate: dict,
) -> None:

    for candidate in candidates:

        candidate[
            "temporal_gate"
        ] = dict(
            temporal_gate
        )


def build_global_decision(
    snapshot: dict,
) -> dict:
    """
    Construye UNA unica decision global sin ejecutar escrituras.

    La jornada real y sus fases temporales gobiernan las
    prioridades. El round interno de Biwenger NO decide
    el deadline.
    """

    solvency = (
        build_solvency_state(
            snapshot
        )
    )

    t15_forecast = (
        build_t15_solvency_forecast(
            solvency
        )
    )

    franchise = (
        build_franchise_autopilot_state(
            snapshot
        )
    )

    lineup_monitor = (
        build_lineup_monitor_state(
            snapshot=
                snapshot,

            persist=
                False,
        )
    )

    lineup_state = (
        build_lineup_state_from_monitor(
            lineup_monitor
        )
    )

    liquidity = (
        build_liquidity_state(
            snapshot
        )
    )

    offers = (
        build_offer_board(
            snapshot
        )
    )

    offer_decisions = (
        build_offer_decision_board(
            snapshot
        )
    )

    offer_reroll = (
        build_computer_offer_reroll_board(
            snapshot=
                snapshot,

            # Observer integration:
            # NO persistimos historial ni ejecutamos escrituras.
            persist_history=
                False,
        )
    )

    accept_expiry_safety = (
        build_accept_before_expiry_safety_board(
            snapshot
        )
    )

    listing_lifecycle = (
        build_market_listing_lifecycle_board(
            snapshot
        )
    )

    portfolio = (
        build_portfolio_roi_board(
            snapshot
        )
    )

    speculation = (
        build_speculation_board(
            snapshot
        )
    )

    balance = int(
        solvency.get(
            "balance",
            0,
        )
        or 0
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

    phase = str(
        deadline.get(
            "phase",
            "CALENDAR_UNKNOWN",
        )
    )

    seconds_to_deadline = (
        solvency.get(
            "seconds_to_deadline"
        )
    )

    lineup_risk = (
        solvency.get(
            "lineup_risk",
            "DESCONOCIDO",
        )
    )

    pressure_score = int(
        deadline.get(
            "lineup_pressure_score",
            0,
        )
        or 0
    )

    hard_safety = (
        get_hard_safety(
            solvency
        )
    )

    temporal_gate = (
        build_temporal_gate(
            solvency
        )
    )

    operations_locked = bool(
        temporal_gate[
            "operations_locked"
        ]
    )

    hard_safety_mode = bool(
        temporal_gate[
            "hard_safety_mode"
        ]
    )

    missing = int(
        lineup_state[
            "missing"
        ]
    )

    playable_count = int(
        lineup_state[
            "playable_count"
        ]
    )

    franchise_state = (
        franchise.get(
            "state",
            "NO_FRANCHISE",
        )
    )

    recovery = (
        liquidity.get(
            "recovery",
            {},
        )
        or {}
    )

    to_list = (
        liquidity.get(
            "to_list",
            [],
        )
        or []
    )

    candidates = []

    # ========================================================
    # LOCK TEMPORAL ABSOLUTO
    # ========================================================

    if operations_locked:

        if phase == "ROUND_TRANSITION_LOCK":

            reason = (
                "La jornada acaba de comenzar. "
                "Bordalas IA mantiene un bloqueo de seguridad "
                "hasta dos horas despues del primer kickoff. "
                "Despues empezara a trabajar para la jornada "
                "siguiente."
            )

        else:

            reason = (
                "La jornada ya ha alcanzado su deadline T-15. "
                "No se realizaran cambios hasta superar el "
                "bloqueo de transicion posterior al kickoff."
            )

        candidates.append(
            {
                "type":
                    phase,

                "priority":
                    PRIORITY[
                        "ROUND_LOCK"
                    ],

                "action":
                    "WAIT",

                "executable":
                    False,

                "executor":
                    None,

                "reason":
                    reason,

                "data": {
                    "target_matchday":
                        deadline.get(
                            "target_matchday"
                        ),

                    "next_matchday":
                        deadline.get(
                            "next_matchday"
                        ),

                    "first_kickoff":
                        deadline.get(
                            "first_kickoff"
                        ),

                    "next_round_unlock":
                        deadline.get(
                            "next_round_unlock"
                        ),
                },
            }
        )

    # ========================================================
    # SOLVENCIA NEGATIVA
    # ========================================================

    if (
        balance < 0
        and
        not operations_locked
    ):

        solvency_priority = (
            calculate_solvency_priority(
                balance=
                    balance,

                phase=
                    phase,

                seconds_to_deadline=
                    seconds_to_deadline,
            )
        )

        if (
            recovery.get(
                "needed",
                True,
            )
            and
            recovery.get(
                "possible",
                False,
            )
            and
            recovery.get(
                "selected"
            )
        ):

            # Offer Decision Engine V2 es la unica autoridad
            # para decidir si una oferta concreta debe aceptarse.
            # El recovery clasico sigue calculando si el plan es
            # financiable, pero ya NO genera ACCEPT_RECOVERY_OFFER.
            candidates.append(
                {
                    "type":
                        "SOLVENCY_GUARANTEE",

                    "priority":
                        solvency_priority,

                    "action":
                        "MONITOR_SOLVENCY",

                    "executable":
                        False,

                    "executor":
                        None,

                    "reason": (
                        f"Saldo negativo: {balance:,.0f} EUR. "
                        f"Fase: {phase}. "
                        "Existe liquidez suficiente para garantizar "
                        "la recuperacion, pero las ofertas concretas "
                        "son gobernadas por Offer Decision Engine V2."
                    ),

                    "data": {
                        "recovery":
                            recovery,
                    },
                }
            )

        elif to_list:

            player = (
                to_list[
                    0
                ]
            )

            candidates.append(
                {
                    "type":
                        "SOLVENCY_LIQUIDITY",

                    "priority":
                        solvency_priority,

                    "action":
                        "LIST_FOR_LIQUIDITY",

                    "executable":
                        True,

                    "executor":
                        "AUTOPILOT",

                    "reason": (
                        f"Saldo negativo: {balance:,.0f} EUR. "
                        f"Fase: {phase}. "
                        "Todavia faltan ofertas suficientes y hay "
                        "jugadores sin publicar. Se publicara uno "
                        "para generar liquidez futura."
                    ),

                    "data": {
                        "player":
                            player,

                        "recovery":
                            recovery,
                    },
                }
            )

        else:

            candidates.append(
                {
                    "type":
                        "WAIT_FOR_LIQUIDITY",

                    "priority":
                        solvency_priority,

                    "action":
                        "WAIT",

                    "executable":
                        False,

                    "executor":
                        None,

                    "reason": (
                        f"Saldo negativo: {balance:,.0f} EUR. "
                        f"Fase: {phase}. "
                        "Toda la plantilla util esta publicada, "
                        "pero las ofertas disponibles todavia no "
                        "cubren el deficit completo."
                    ),

                    "data": {
                        "recovery":
                            recovery,

                        "incoming_offers":
                            liquidity.get(
                                "incoming_offers",
                                [],
                            ),
                    },
                }
            )

    # ========================================================
    # XI INCOMPLETO
    # ========================================================

    if (
        missing > 0
        and
        not operations_locked
    ):

        lineup_priority = (
            calculate_lineup_priority(
                missing=
                    missing,

                seconds_to_deadline=
                    seconds_to_deadline,

                lineup_risk=
                    lineup_risk,

                pressure_score=
                    pressure_score,

                phase=
                    phase,
            )
        )

        if lineup_priority >= 1050:
            lineup_type = "EMERGENCY_LINEUP"

        elif lineup_priority >= 970:
            lineup_type = "LINEUP_VERY_HIGH"

        elif lineup_priority >= 900:
            lineup_type = "LINEUP_HIGH"

        elif lineup_priority >= 800:
            lineup_type = "LINEUP_MODERATE"

        else:
            lineup_type = "LINEUP_LOW"

        candidates.append(
            {
                "type":
                    lineup_type,

                "priority":
                    lineup_priority,

                "action":
                    (
                        "REBUILD_LINEUP"
                        if playable_count < 9
                        else "COMPLETE_LINEUP"
                    ),

                "executable":
                    False,

                "executor":
                    None,

                "reason": (
                    f"XI valido: {playable_count}/11. "
                    f"Faltan {missing}. "
                    f"Riesgo XI: {lineup_risk}. "
                    f"Fase: {phase}. "
                    f"Presion temporal: {pressure_score}/100."
                ),

                "data":
                    lineup_state,
            }
        )

    # ========================================================
    # CAMBIO RELEVANTE DEL XI
    # ========================================================

    if (
        not operations_locked
        and
        lineup_monitor.get(
            "should_save",
            False,
        )
        and
        lineup_monitor.get(
            "complete",
            False,
        )
    ):

        lineup_update_priority = (
            calculate_lineup_update_priority(
                phase=
                    phase,

                seconds_to_deadline=
                    seconds_to_deadline,
            )
        )

        if lineup_update_priority > 0:

            candidates.append(
                {
                    "type":
                        "LINEUP_UPDATE",

                    "priority":
                        lineup_update_priority,

                    "action":
                        "SAVE_LINEUP",

                    "executable":
                        True,

                    "executor":
                        "AUTOPILOT",

                    "reason": (
                        "Lineup Monitor ha detectado un cambio "
                        "relevante en el XI recomendado para la "
                        f"Jornada {deadline.get('target_matchday')}."
                    ),

                    "data": {
                        "lineup_monitor":
                            lineup_monitor,
                    },
                }
            )

    # ========================================================
    # FRANCHISE
    # ========================================================

    franchise_priority = (
        calculate_franchise_priority(
            franchise_state=
                franchise_state,

            lineup_risk=
                lineup_risk,

            seconds_to_deadline=
                seconds_to_deadline,

            missing=
                missing,

            phase=
                phase,

            balance=
                balance,
        )
    )

    if (
        franchise_priority > 0
        and
        franchise_state
        in {
            "CANCEL_BID",
            "PLACE_FRANCHISE_BID",
        }
    ):

        candidates.append(
            {
                "type":
                    "FRANCHISE_ACTION",

                "priority":
                    franchise_priority,

                "action":
                    franchise_state,

                "executable":
                    False,

                "executor":
                    "EXISTING_FRANCHISE_FLOW",

                "reason":
                    franchise.get(
                        "reason"
                    ),

                "data":
                    franchise,
            }
        )

    elif (
        franchise_priority > 0
        and
        franchise_state
        == "WAIT_FRANCHISE_RESOLUTION"
    ):

        candidates.append(
            {
                "type":
                    "FRANCHISE_WAIT",

                "priority":
                    franchise_priority,

                "action":
                    "WAIT",

                "executable":
                    False,

                "executor":
                    None,

                "reason":
                    franchise.get(
                        "reason"
                    ),

                "data":
                    franchise,
            }
        )

    # ========================================================
    # HARD SAFETY
    # ========================================================

    if (
        hard_safety_mode
        and
        not operations_locked
    ):

        candidates.append(
            {
                "type":
                    "HARD_SAFETY",

                "priority":
                    PRIORITY[
                        "HARD_SAFETY"
                    ],

                "action":
                    "SAFETY_MODE",

                "executable":
                    False,

                "executor":
                    None,

                "reason": (
                    "Estamos entre T-90 y T-15. "
                    "Solo se permiten acciones orientadas a "
                    "cerrar un XI valido y alcanzar saldo >= 0."
                ),

                "data":
                    hard_safety,
            }
        )

    # ========================================================
    # MANTENIMIENTO DE LIQUIDEZ
    # ========================================================

    if (
        balance >= 0
        and
        to_list
        and
        phase not in RISKY_PHASES
    ):

        player = (
            to_list[
                0
            ]
        )

        candidates.append(
            {
                "type":
                    "LIQUIDITY_MAINTENANCE",

                "priority":
                    PRIORITY[
                        "LIQUIDITY_MAINTENANCE"
                    ],

                "action":
                    "LIST_FOR_LIQUIDITY",

                "executable":
                    True,

                "executor":
                    "AUTOPILOT",

                "reason": (
                    "Hay un jugador sin publicar. "
                    "Se mantendra disponible para generar "
                    "ofertas futuras."
                ),

                "data": {
                    "player":
                        player,
                },
            }
        )

    # ========================================================
    # OFFER DECISION ENGINE V2 - OBSERVER
    # ========================================================

    evaluated_offers = (
        offer_decisions.get(
            "decisions",
            [],
        )
        or []
    )

    if evaluated_offers:

        protections = [
            item
            for item in evaluated_offers
            if item.get("decision")
            == "NEVER_SELL"
        ]

        solvency_reserves = [
            item
            for item in evaluated_offers
            if item.get("decision")
            == "HOLD_SOLVENCY_RESERVED"
        ]

        good_offers = [
            item
            for item in evaluated_offers
            if item.get("decision")
            == "KEEP_GOOD_OFFER"
        ]

        hold_offers = [
            item
            for item in evaluated_offers
            if item.get("decision")
            == "HOLD_OFFER"
        ]

        actionable = [
            item
            for item in evaluated_offers
            if item.get("decision")
            in {
                "ACCEPT_FOR_SOLVENCY",
                "ACCEPT_NOW",
                "REROLL_CANDIDATE",
            }
        ]

        summary_counts = {
            "PROTECTIONS":
                len(protections),

            "SOLVENCY_RESERVES":
                len(solvency_reserves),

            "GOOD_OFFERS":
                len(good_offers),

            "HOLD_OFFERS":
                len(hold_offers),

            "ACTIONABLE":
                len(actionable),
        }

        candidates.append(
            {
                "type":
                    "OFFER_DECISION_INTELLIGENCE",

                "priority":
                    PRIORITY[
                        "INCOMING_OFFERS"
                    ],

                # Las protecciones y reservas son ESTADO,
                # no acciones globales.
                "action":
                    "MONITOR_OFFERS",

                "executable":
                    False,

                "executor":
                    None,

                "reason": (
                    f"Offer Decision Engine V2 controla "
                    f"{len(evaluated_offers)} ofertas: "
                    f"{len(protections)} protegidas, "
                    f"{len(solvency_reserves)} reservas de solvencia, "
                    f"{len(good_offers)} buenas para conservar, "
                    f"{len(hold_offers)} en espera y "
                    f"{len(actionable)} con signal accionable. "
                    "Observer: la inteligencia general de ofertas "
                    "no ejecuta escrituras."
                ),

                "data": {
                    "protections":
                        protections,

                    "solvency_reserves":
                        solvency_reserves,

                    "good_offers":
                        good_offers,

                    "hold_offers":
                        hold_offers,

                    "actionable":
                        actionable,

                    "summary_counts":
                        summary_counts,

                    "offer_decisions":
                        offer_decisions,
                },
            }
        )


    # ========================================================
    # COMPUTER OFFER INTELLIGENCE - OBSERVER
    # ========================================================
    #
    # IMPORTANTE:
    # - Esta capa NO ejecuta rechazo ni relistado.
    # - Solo incorpora la inteligencia de Reroll Engine
    #   al Orchestrator y a la telemetria.
    # ========================================================

    reroll_candidates = (
        offer_reroll.get(
            "reroll_candidates",
            [],
        )
        or []
    )

    if (
        reroll_candidates
        and
        not operations_locked
    ):

        best_reroll = (
            reroll_candidates[
                0
            ]
        )

        player_names = ", ".join(
            player.get(
                "name",
                "?"
            )

            for player
            in best_reroll.get(
                "players",
                [],
            )
        )

        candidates.append(
            {
                "type":
                    "COMPUTER_OFFER_REROLL_WATCH",

                "priority":
                    PRIORITY[
                        "COMPUTER_OFFER_REROLL_WATCH"
                    ],

                "action":
                    (
                        "REROLL_COMPUTER_OFFER"
                        if ENABLE_LIVE_COMPUTER_REROLL
                        else "REROLL_CANDIDATE"
                    ),

                "executable":
                    bool(
                        ENABLE_LIVE_COMPUTER_REROLL
                    ),

                "executor":
                    (
                        "AUTOPILOT"
                        if ENABLE_LIVE_COMPUTER_REROLL
                        else None
                    ),

                "reason": (
                    f"Reroll Engine considera mejorable la "
                    f"oferta Computer de {player_names}. "
                    "La simulacion mantiene SOLVENCY_GUARANTEE. "
                    + (
                        "Reroll LIVE habilitado: el executor volvera "
                        "a revalidar con snapshot fresco antes de escribir."
                        if ENABLE_LIVE_COMPUTER_REROLL
                        else
                        "El rechazo automatico sigue desactivado."
                    )
                ),

                "data": {
                    "offer":
                        best_reroll,

                    "offer_reroll":
                        offer_reroll,
                },
            }
        )



    # ========================================================
    # ACCEPT-BEFORE-EXPIRY SAFETY V2.1 - OBSERVER
    # ========================================================
    #
    # Esta capa sustituye al watcher legacy de caducidad.
    # La necesidad de aceptar se decide simulando la pÃƒÂ©rdida
    # simultÃƒÂ¡nea de clusters de ofertas y recalculando
    # SOLVENCY_GUARANTEE desde cero.
    #
    # AÃƒÂºn NO ejecuta ACCEPT_OFFER automÃƒÂ¡ticamente.
    # ========================================================

    urgent_expiry_clusters = (
        accept_expiry_safety.get(
            "urgent_clusters",
            [],
        )
        or []
    )

    watch_expiry_clusters = (
        accept_expiry_safety.get(
            "watch_clusters",
            [],
        )
        or []
    )

    if (
        urgent_expiry_clusters
        and
        not operations_locked
    ):

        urgent_cluster = (
            urgent_expiry_clusters[
                0
            ]
        )

        player_names = ", ".join(
            urgent_cluster.get(
                "player_names",
                [],
            )
        )

        candidates.append(
            {
                "type":
                    "ACCEPT_BEFORE_EXPIRY_SAFETY",

                "priority":
                    calculate_accept_expiry_priority(
                        balance=balance,
                        phase=phase,
                    ),

                "action":
                    "ACCEPT_CLUSTER_BEFORE_EXPIRY",

                "executable":
                    bool(
                        ENABLE_LIVE_ACCEPT_BEFORE_EXPIRY
                    ),

                "executor":
                    (
                        "AUTOPILOT"
                        if ENABLE_LIVE_ACCEPT_BEFORE_EXPIRY
                        else None
                    ),

                "reason": (
                    f"Cluster crÃƒÂ­tico de ofertas: {player_names}. "
                    "Perderlo rompe SOLVENCY_GUARANTEE y el lÃƒÂ­mite "
                    "efectivo ya estÃƒÂ¡ dentro del margen operativo. "
                    + (
                        "Aceptacion LIVE habilitada: el executor "
                        "refrescara Biwenger y revalidara TODO antes "
                        "de aceptar una sola oferta."
                        if ENABLE_LIVE_ACCEPT_BEFORE_EXPIRY
                        else
                        "Observer: aceptacion LIVE desactivada."
                    )
                ),

                "data": {
                    "cluster":
                        urgent_cluster,

                    "accept_expiry_safety":
                        accept_expiry_safety,
                },
            }
        )

    elif (
        watch_expiry_clusters
        and
        not operations_locked
    ):

        watch_cluster = (
            watch_expiry_clusters[
                0
            ]
        )

        player_names = ", ".join(
            watch_cluster.get(
                "player_names",
                [],
            )
        )

        candidates.append(
            {
                "type":
                    "ACCEPT_BEFORE_EXPIRY_WATCH",

                "priority":
                    PRIORITY[
                        "ACCEPT_EXPIRY_WATCH"
                    ],

                "action":
                    "WATCH_CRITICAL_EXPIRY_CLUSTER",

                "executable":
                    False,

                "executor":
                    None,

                "reason": (
                    f"Cluster crÃƒÂ­tico de ofertas: {player_names}. "
                    "Perderlo romperÃƒÂ­a SOLVENCY_GUARANTEE, pero "
                    "todavÃƒÂ­a no estamos dentro del margen operativo "
                    "de aceptaciÃƒÂ³n. Debe conservarse y vigilarse."
                ),

                "data": {
                    "cluster":
                        watch_cluster,

                    "accept_expiry_safety":
                        accept_expiry_safety,
                },
            }
        )

    # ========================================================
    # MARKET LISTING LIFECYCLE
    # ========================================================

    renewal_candidates = (
        listing_lifecycle.get(
            "renew_required",
            [],
        )
        or []
    )

    if (
        renewal_candidates
        and
        not operations_locked
    ):

        # Solo una renovacion por ciclo.
        renewal = (
            renewal_candidates[
                0
            ]
        )

        candidates.append(
            {
                "type":
                    "MARKET_LISTING_RENEW",

                "priority":
                    PRIORITY[
                        "MARKET_LISTING_RENEW"
                    ],

                "action":
                    (
                        "RENEW_MARKET_LISTING"
                        if ENABLE_LIVE_MARKET_LISTING_RENEW
                        else "RENEW_MARKET_LISTING_WATCH"
                    ),

                "executable":
                    bool(
                        ENABLE_LIVE_MARKET_LISTING_RENEW
                    ),

                "executor":
                    (
                        "AUTOPILOT"
                        if ENABLE_LIVE_MARKET_LISTING_RENEW
                        else None
                    ),

                "reason": (
                    f"La publicacion de {renewal.get('name')} "
                    "caduca antes de terminar el siguiente ciclo "
                    "Computer. "
                    + (
                        "Renovacion LIVE habilitada."
                        if ENABLE_LIVE_MARKET_LISTING_RENEW
                        else
                        "Observer: renovacion automatica desactivada."
                    )
                ),

                "data": {
                    "listing":
                        renewal,
                },
            }
        )

    # ========================================================
    # RIESGO DE CARTERA
    # ========================================================

    urgent_exits = [
        player

        for player in portfolio.get(
            "exits",
            [],
        )

        if player.get(
            "portfolio_action"
        )
        in {
            "EXIT_RISK",
            "CUT_LOSS",
            "TAKE_PROFIT",
        }
    ]

    if (
        urgent_exits
        and
        phase not in RISKY_PHASES
    ):

        urgent_exits.sort(
            key=lambda player:
                player.get(
                    "portfolio_priority",
                    0,
                ),
            reverse=True,
        )

        best_exit = (
            urgent_exits[
                0
            ]
        )

        candidates.append(
            {
                "type":
                    "PLAYER_RISK_EXIT",

                "priority":
                    PRIORITY[
                        "PLAYER_RISK_EXIT"
                    ],

                "action":
                    "CONSIDER_PLAYER_EXIT",

                "executable":
                    False,

                "executor":
                    None,

                "reason":
                    best_exit.get(
                        "portfolio_reason"
                    ),

                "data": {
                    "player":
                        best_exit,
                },
            }
        )

    # ========================================================
    # ESPECULACION
    # ========================================================

    budget = (
        speculation.get(
            "budget",
            {},
        )
        or {}
    )

    executable_buys = (
        speculation.get(
            "executable_buys",
            [],
        )
        or []
    )

    speculation_phase_allowed = (
        phase
        in {
            "NORMAL",
            "PREPARATION",
        }
    )

    if (
        speculation_phase_allowed
        and
        budget.get(
            "enabled"
        )
        and
        executable_buys
        and
        not hard_safety_mode
        and
        balance >= 0
    ):

        candidates.append(
            {
                "type":
                    "SPECULATION_BUY",

                "priority":
                    PRIORITY[
                        "SPECULATION_BUY"
                    ],

                "action":
                    "BUY_SPECULATION",

                "executable":
                    bool(
                        ENABLE_LIVE_SPECULATION_BUY
                    ),

                "executor":
                    (
                        "AUTOPILOT"
                        if ENABLE_LIVE_SPECULATION_BUY
                        else None
                    ),

                "reason": (
                    "Existe una oportunidad especulativa "
                    "dentro del presupuesto autorizado. "
                    + (
                        "Compra LIVE habilitada con read-before-write "
                        "y revalidacion completa."
                        if ENABLE_LIVE_SPECULATION_BUY
                        else
                        "Observer: compra automatica desactivada."
                    )
                ),

                "data": {
                    "player":
                        executable_buys[
                            0
                        ],

                    "budget":
                        budget,
                },
            }
        )

    elif (
        speculation.get(
            "buy_candidates"
        )
        and
        phase not in LOCK_PHASES
    ):

        candidates.append(
            {
                "type":
                    "SPECULATION_WATCH",

                "priority":
                    PRIORITY[
                        "SPECULATION_WATCH"
                    ],

                "action":
                    "WATCH_SPECULATION",

                "executable":
                    False,

                "executor":
                    None,

                "reason": (
                    "Existen senales especulativas para "
                    "vigilar, pero no una compra automatica "
                    "autorizada."
                ),

                "data": {
                    "candidates":
                        speculation[
                            "buy_candidates"
                        ][
                            :5
                        ],
                },
            }
        )

    candidates.append(
        {
            "type":
                "IDLE",

            "priority":
                PRIORITY[
                    "IDLE"
                ],

            "action":
                "WAIT",

            "executable":
                False,

            "executor":
                None,

            "reason":
                (
                    "No existe ninguna accion "
                    "prioritaria en este ciclo."
                ),

            "data":
                {},
        }
    )

    add_temporal_gate(
        candidates=
            candidates,

        temporal_gate=
            temporal_gate,
    )

    candidates.sort(
        key=lambda item:
            item[
                "priority"
            ],
        reverse=True,
    )

    # V10.1: la preocupacion principal sigue siendo candidates[0]
    # para preservar compatibilidad. En paralelo exponemos la
    # primera accion realmente ejecutable y una cola SHADOW.
    action_queue = build_action_queue(
        candidates
    )

    action_decision = (
        action_queue[0]
        if action_queue
        else None
    )

    shadow_candidates = list(candidates)

    shadow_speculation = (
        build_shadow_speculation_candidate(
            speculation=speculation,
            solvency=solvency,
            phase=phase,
            hard_safety_mode=hard_safety_mode,
            operations_locked=operations_locked,
        )
    )

    # Si BUY_SPECULATION ya existe como accion LIVE, no duplicamos
    # el mismo jugador en la cola shadow.
    if (
        shadow_speculation is not None
        and not any(
            item.get("action") == "BUY_SPECULATION"
            and item.get("executable", False)
            for item in shadow_candidates
        )
    ):
        shadow_candidates.append(
            shadow_speculation
        )

    shadow_action_queue = build_action_queue(
        shadow_candidates,
        shadow=True,
    )

    shadow_action_decision = (
        shadow_action_queue[0]
        if shadow_action_queue
        else None
    )

    return {
        "decision":
            candidates[
                0
            ],

        "action_decision":
            action_decision,

        "action_queue":
            action_queue,

        "shadow_action_decision":
            shadow_action_decision,

        "shadow_action_queue":
            shadow_action_queue,

        "candidates":
            candidates,

        "state": {
            "balance":
                balance,

            "phase":
                phase,

            "target_matchday":
                deadline.get(
                    "target_matchday"
                ),

            "next_matchday":
                deadline.get(
                    "next_matchday"
                ),

            "calendar":
                calendar,

            "deadline":
                deadline,

            "temporal_gate":
                temporal_gate,

            "operations_locked":
                operations_locked,

            "seconds_to_deadline":
                seconds_to_deadline,

            "hours_to_deadline":
                hours_remaining(
                    seconds_to_deadline
                ),

            "lineup_risk":
                lineup_risk,

            "lineup_pressure_score":
                pressure_score,

            "hard_safety":
                hard_safety,

            "solvency":
                solvency,

            "t15_forecast":
                t15_forecast,

            "franchise":
                franchise,

            "lineup":
                lineup_state,

            "lineup_monitor":
                lineup_monitor,

            "liquidity":
                liquidity,

            "offers":
                offers,

            "offer_decisions":
                offer_decisions,

            "offer_reroll":
                offer_reroll,

            "accept_expiry_safety":
                accept_expiry_safety,

            "listing_lifecycle":
                listing_lifecycle,

            "portfolio":
                portfolio,

            "speculation":
                speculation,
        },
    }
