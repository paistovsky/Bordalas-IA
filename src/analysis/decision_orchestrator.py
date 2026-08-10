from src.actions.franchise_autopilot import (
    build_franchise_autopilot_state,
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

from src.analysis.portfolio_roi_engine import (
    build_portfolio_roi_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)


PRIORITY = {
    "EMERGENCY_SOLVENCY": 1000,
    "EMERGENCY_LINEUP": 990,
    "HARD_SAFETY": 970,
    "NEGATIVE_BALANCE": 940,
    "FRANCHISE_ACTION": 900,
    "FRANCHISE_WAIT": 880,
    "LINEUP_VERY_HIGH": 960,
    "LINEUP_HIGH": 910,
    "LINEUP_MODERATE": 820,
    "LINEUP_LOW": 700,
    "LINEUP_UPDATE_LOW": 760,
    "LINEUP_UPDATE_MODERATE": 835,
    "LINEUP_UPDATE_HIGH": 920,
    "LINEUP_UPDATE_VERY_HIGH": 965,
    "LINEUP_UPDATE_EMERGENCY": 995,
    "INCOMING_OFFERS": 650,
    "PLAYER_RISK_EXIT": 600,
    "LIQUIDITY_MAINTENANCE": 550,
    "SPECULATION_BUY": 400,
    "SPECULATION_WATCH": 300,
    "IDLE": 0,
}


def hours_remaining(seconds: int | None) -> float | None:
    if seconds is None:
        return None
    return max(seconds / 3600, 0.0)


def get_hard_safety(solvency: dict) -> dict:
    return solvency.get("hard_safety", {}) or {}


def build_lineup_state_from_monitor(monitor: dict) -> dict:
    lineup = monitor.get("lineup", {}) or {}
    playable_count = int(lineup.get("playable_count", 0) or 0)
    missing = max(11 - playable_count, 0)

    return {
        "lineup": lineup,
        "playable_count": playable_count,
        "missing": missing,
        "shortages": lineup.get("matchday_shortages", {}) or {},
        "complete": playable_count >= 11,
    }


def calculate_lineup_priority(
    missing: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
    pressure_score: int,
) -> int:
    if missing <= 0:
        return 0

    if seconds_to_deadline is None:
        return PRIORITY["LINEUP_MODERATE"] + min(pressure_score, 50)

    hours = hours_remaining(seconds_to_deadline)

    if hours <= 6:
        return PRIORITY["EMERGENCY_LINEUP"]
    if hours <= 24:
        return PRIORITY["LINEUP_VERY_HIGH"]
    if hours <= 48:
        return PRIORITY["LINEUP_HIGH"]
    if hours <= 120:
        priority = PRIORITY["LINEUP_MODERATE"]
        if lineup_risk == "ALTO":
            priority += 30
        elif lineup_risk == "MUY_ALTO":
            priority += 60
        return priority

    return PRIORITY["LINEUP_LOW"] + min(missing * 10, 40)


def calculate_lineup_update_priority(
    seconds_to_deadline: int | None,
) -> int:
    if seconds_to_deadline is None:
        return PRIORITY["LINEUP_UPDATE_MODERATE"]

    hours = hours_remaining(seconds_to_deadline)

    if hours <= 6:
        return PRIORITY["LINEUP_UPDATE_EMERGENCY"]
    if hours <= 24:
        return PRIORITY["LINEUP_UPDATE_VERY_HIGH"]
    if hours <= 48:
        return PRIORITY["LINEUP_UPDATE_HIGH"]
    if hours <= 120:
        return PRIORITY["LINEUP_UPDATE_MODERATE"]

    return PRIORITY["LINEUP_UPDATE_LOW"]


def calculate_franchise_priority(
    franchise_state: str,
    lineup_risk: str,
    seconds_to_deadline: int | None,
    missing: int,
) -> int:
    if franchise_state in {"CANCEL_BID", "PLACE_FRANCHISE_BID"}:
        base = PRIORITY["FRANCHISE_ACTION"]
    elif franchise_state == "WAIT_FRANCHISE_RESOLUTION":
        base = PRIORITY["FRANCHISE_WAIT"]
    else:
        return 0

    if missing <= 0:
        return base
    if seconds_to_deadline is None:
        return base - 100

    hours = hours_remaining(seconds_to_deadline)

    if hours <= 6:
        return 500
    if hours <= 24:
        return 650
    if hours <= 48:
        return 820
    if hours <= 120:
        if lineup_risk in {"ALTO", "MUY_ALTO", "CRITICO"}:
            return 800
        return base

    return base


def calculate_solvency_priority(
    balance: int,
    seconds_to_deadline: int | None,
) -> int:
    if balance >= 0:
        return 0
    if seconds_to_deadline is None:
        return PRIORITY["NEGATIVE_BALANCE"]

    hours = hours_remaining(seconds_to_deadline)

    if hours <= 24:
        return PRIORITY["EMERGENCY_SOLVENCY"]
    if hours <= 48:
        return 980
    if hours <= 120:
        return 960

    return PRIORITY["NEGATIVE_BALANCE"]


def build_global_decision(snapshot: dict) -> dict:
    """Construye UNA unica decision global sin ejecutar escrituras."""

    solvency = build_solvency_state(snapshot)
    franchise = build_franchise_autopilot_state(snapshot)
    lineup_monitor = build_lineup_monitor_state(snapshot=snapshot, persist=False)
    lineup_state = build_lineup_state_from_monitor(lineup_monitor)
    liquidity = build_liquidity_state(snapshot)
    offers = build_offer_board(snapshot)
    portfolio = build_portfolio_roi_board(snapshot)
    speculation = build_speculation_board(snapshot)

    balance = int(solvency.get("balance", 0) or 0)
    deadline = solvency.get("deadline", {}) or {}
    seconds_to_deadline = solvency.get("seconds_to_deadline")
    lineup_risk = solvency.get("lineup_risk", "DESCONOCIDO")
    pressure_score = int(deadline.get("lineup_pressure_score", 0) or 0)
    hard_safety = get_hard_safety(solvency)
    missing = int(lineup_state["missing"])
    playable_count = int(lineup_state["playable_count"])
    franchise_state = franchise.get("state", "NO_FRANCHISE")
    recovery = liquidity.get("recovery", {}) or {}
    to_list = liquidity.get("to_list", []) or []

    candidates = []

    # ========================================================
    # SOLVENCIA NEGATIVA
    # ========================================================

    if balance < 0:
        solvency_priority = calculate_solvency_priority(
            balance=balance,
            seconds_to_deadline=seconds_to_deadline,
        )

        if (
            recovery.get("needed", True)
            and recovery.get("possible", False)
            and recovery.get("selected")
        ):
            next_offer = recovery["selected"][0]
            candidates.append(
                {
                    "type": "SOLVENCY_RECOVERY",
                    "priority": solvency_priority,
                    "action": "ACCEPT_RECOVERY_OFFER",
                    "executable": True,
                    "executor": "AUTOPILOT",
                    "reason": (
                        f"Saldo negativo: {balance:,.0f} EUR. "
                        "Existe una combinacion completa de ofertas capaz de "
                        "recuperar solvencia. Se aceptara una unica oferta y "
                        "despues se recalculara."
                    ),
                    "data": {
                        "offer": next_offer,
                        "recovery": recovery,
                    },
                }
            )

        elif to_list:
            player = to_list[0]
            candidates.append(
                {
                    "type": "SOLVENCY_LIQUIDITY",
                    "priority": solvency_priority,
                    "action": "LIST_FOR_LIQUIDITY",
                    "executable": True,
                    "executor": "AUTOPILOT",
                    "reason": (
                        f"Saldo negativo: {balance:,.0f} EUR. "
                        "Aun no existen ofertas suficientes para cubrir el "
                        "deficit y quedan jugadores sin publicar. Se publicara "
                        "uno para aumentar la liquidez futura."
                    ),
                    "data": {
                        "player": player,
                        "recovery": recovery,
                    },
                }
            )

        else:
            candidates.append(
                {
                    "type": "WAIT_FOR_LIQUIDITY",
                    "priority": solvency_priority,
                    "action": "WAIT",
                    "executable": False,
                    "executor": None,
                    "reason": (
                        f"Saldo negativo: {balance:,.0f} EUR. "
                        "Toda la plantilla util esta publicada, pero las "
                        "ofertas disponibles todavia no cubren el deficit "
                        "completo."
                    ),
                    "data": {
                        "recovery": recovery,
                        "incoming_offers": liquidity.get("incoming_offers", []),
                    },
                }
            )

    # ========================================================
    # XI INCOMPLETO
    # ========================================================

    if missing > 0:
        lineup_priority = calculate_lineup_priority(
            missing=missing,
            seconds_to_deadline=seconds_to_deadline,
            lineup_risk=lineup_risk,
            pressure_score=pressure_score,
        )

        if lineup_priority >= 990:
            lineup_type = "EMERGENCY_LINEUP"
        elif lineup_priority >= 950:
            lineup_type = "LINEUP_VERY_HIGH"
        elif lineup_priority >= 900:
            lineup_type = "LINEUP_HIGH"
        elif lineup_priority >= 800:
            lineup_type = "LINEUP_MODERATE"
        else:
            lineup_type = "LINEUP_LOW"

        candidates.append(
            {
                "type": lineup_type,
                "priority": lineup_priority,
                "action": (
                    "REBUILD_LINEUP" if playable_count < 9 else "COMPLETE_LINEUP"
                ),
                "executable": False,
                "executor": None,
                "reason": (
                    f"XI con partido: {playable_count}/11. "
                    f"Faltan {missing}. Riesgo XI: {lineup_risk}. "
                    f"Presion temporal: {pressure_score}/100."
                ),
                "data": lineup_state,
            }
        )

    # ========================================================
    # CAMBIO RELEVANTE DEL XI
    # ========================================================

    if (
        lineup_monitor.get("should_save", False)
        and lineup_monitor.get("complete", False)
    ):
        candidates.append(
            {
                "type": "LINEUP_UPDATE",
                "priority": calculate_lineup_update_priority(seconds_to_deadline),
                "action": "SAVE_LINEUP",
                "executable": True,
                "executor": "AUTOPILOT",
                "reason": (
                    "Lineup Monitor ha detectado un cambio relevante en el "
                    "XI recomendado."
                ),
                "data": {
                    "lineup_monitor": lineup_monitor,
                },
            }
        )

    # ========================================================
    # FRANCHISE
    # ========================================================

    franchise_priority = calculate_franchise_priority(
        franchise_state=franchise_state,
        lineup_risk=lineup_risk,
        seconds_to_deadline=seconds_to_deadline,
        missing=missing,
    )

    if franchise_state in {"CANCEL_BID", "PLACE_FRANCHISE_BID"}:
        candidates.append(
            {
                "type": "FRANCHISE_ACTION",
                "priority": franchise_priority,
                "action": franchise_state,
                "executable": False,
                "executor": "EXISTING_FRANCHISE_FLOW",
                "reason": franchise.get("reason"),
                "data": franchise,
            }
        )

    elif franchise_state == "WAIT_FRANCHISE_RESOLUTION":
        candidates.append(
            {
                "type": "FRANCHISE_WAIT",
                "priority": franchise_priority,
                "action": "WAIT",
                "executable": False,
                "executor": None,
                "reason": franchise.get("reason"),
                "data": franchise,
            }
        )

    # ========================================================
    # HARD SAFETY
    # ========================================================

    if hard_safety.get("active", False):
        candidates.append(
            {
                "type": "HARD_SAFETY",
                "priority": PRIORITY["HARD_SAFETY"],
                "action": "SAFETY_MODE",
                "executable": False,
                "executor": None,
                "reason": (
                    "Hard Safety activo. Se bloquean operaciones economicas "
                    "de riesgo."
                ),
                "data": hard_safety,
            }
        )

    # ========================================================
    # MANTENIMIENTO DE LIQUIDEZ SI SOMOS SOLVENTES
    # ========================================================

    if balance >= 0 and to_list:
        player = to_list[0]
        candidates.append(
            {
                "type": "LIQUIDITY_MAINTENANCE",
                "priority": PRIORITY["LIQUIDITY_MAINTENANCE"],
                "action": "LIST_FOR_LIQUIDITY",
                "executable": True,
                "executor": "AUTOPILOT",
                "reason": (
                    "Hay un jugador de la plantilla sin publicar. Se mantendra "
                    "disponible para generar ofertas futuras."
                ),
                "data": {
                    "player": player,
                },
            }
        )

    # ========================================================
    # OFERTAS RECIBIDAS
    # ========================================================

    incoming = offers.get("incoming", []) or []

    if incoming:
        candidates.append(
            {
                "type": "INCOMING_OFFERS",
                "priority": PRIORITY["INCOMING_OFFERS"],
                "action": "EVALUATE_OFFERS",
                "executable": False,
                "executor": None,
                "reason": f"Hay {len(incoming)} ofertas recibidas pendientes.",
                "data": {
                    "offers": incoming,
                },
            }
        )

    # ========================================================
    # RIESGO DE CARTERA
    # ========================================================

    urgent_exits = [
        player
        for player in portfolio.get("exits", [])
        if player.get("portfolio_action")
        in {"EXIT_RISK", "CUT_LOSS", "TAKE_PROFIT"}
    ]

    if urgent_exits:
        urgent_exits.sort(
            key=lambda player: player.get("portfolio_priority", 0),
            reverse=True,
        )
        best_exit = urgent_exits[0]
        candidates.append(
            {
                "type": "PLAYER_RISK_EXIT",
                "priority": PRIORITY["PLAYER_RISK_EXIT"],
                "action": "CONSIDER_PLAYER_EXIT",
                "executable": False,
                "executor": None,
                "reason": best_exit.get("portfolio_reason"),
                "data": {
                    "player": best_exit,
                },
            }
        )

    # ========================================================
    # ESPECULACION
    # ========================================================

    budget = speculation.get("budget", {}) or {}
    executable_buys = speculation.get("executable_buys", []) or []

    if (
        budget.get("enabled")
        and executable_buys
        and not hard_safety.get("active", False)
        and balance >= 0
    ):
        candidates.append(
            {
                "type": "SPECULATION_BUY",
                "priority": PRIORITY["SPECULATION_BUY"],
                "action": "BUY_SPECULATION",
                "executable": False,
                "executor": None,
                "reason": (
                    "Existe una oportunidad especulativa dentro del presupuesto "
                    "autorizado."
                ),
                "data": {
                    "player": executable_buys[0],
                    "budget": budget,
                },
            }
        )

    elif speculation.get("buy_candidates"):
        candidates.append(
            {
                "type": "SPECULATION_WATCH",
                "priority": PRIORITY["SPECULATION_WATCH"],
                "action": "WATCH_SPECULATION",
                "executable": False,
                "executor": None,
                "reason": (
                    "Existen senales especulativas para vigilar, pero no una "
                    "compra automatica autorizada."
                ),
                "data": {
                    "candidates": speculation["buy_candidates"][:5],
                },
            }
        )

    candidates.append(
        {
            "type": "IDLE",
            "priority": PRIORITY["IDLE"],
            "action": "WAIT",
            "executable": False,
            "executor": None,
            "reason": "No existe ninguna accion prioritaria en este ciclo.",
            "data": {},
        }
    )

    candidates.sort(
        key=lambda item: item["priority"],
        reverse=True,
    )

    return {
        "decision": candidates[0],
        "candidates": candidates,
        "state": {
            "balance": balance,
            "seconds_to_deadline": seconds_to_deadline,
            "hours_to_deadline": hours_remaining(seconds_to_deadline),
            "lineup_risk": lineup_risk,
            "lineup_pressure_score": pressure_score,
            "hard_safety": hard_safety,
            "solvency": solvency,
            "franchise": franchise,
            "lineup": lineup_state,
            "lineup_monitor": lineup_monitor,
            "liquidity": liquidity,
            "offers": offers,
            "portfolio": portfolio,
            "speculation": speculation,
        },
    }
