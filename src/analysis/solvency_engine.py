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


def calculate_incoming_offer_liquidity(
    snapshot: dict,
) -> dict:

    board = (
        build_offer_board(
            snapshot
        )
    )

    offers = []

    for offer in board[
        "incoming"
    ]:

        if (
            offer.get(
                "status"
            )
            != "waiting"
        ):
            continue

        offers.append(
            offer
        )

    total = sum(
        int(
            offer[
                "amount"
            ]
        )

        for offer in offers
    )

    return {
        "offers":
            offers,

        "total":
            total,
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

        # La jornada ya esta cerrada.
        # El saldo negativo se evaluara para la siguiente
        # jornada tras el desbloqueo.
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


# ======================================================
# DEUDA TEMPORAL
# ======================================================


def calculate_temporary_debt_permission(
    balance: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
    phase: str,
) -> dict:

    if balance >= 0:

        return {
            "allowed":
                True,

            "reason":
                "El saldo actual no es negativo.",
        }

    if phase in {
        "ROUND_LOCKED",
        "ROUND_TRANSITION_LOCK",
    }:

        return {
            "allowed":
                False,

            "reason": (
                "La jornada esta temporalmente bloqueada. "
                "No se evalua nueva deuda hasta el desbloqueo."
            ),
        }

    if phase in {
        "HARD_SAFETY",
        "FINALIZATION",
    }:

        return {
            "allowed":
                False,

            "reason": (
                "Estamos en fase de cierre de jornada. "
                "Bordalas IA exige recuperar saldo >= 0."
            ),
        }

    deficit = abs(
        balance
    )

    if seconds_to_deadline is None:

        return {
            "allowed":
                False,

            "reason": (
                "No conocemos el deadline real y no podemos "
                "autorizar deuda temporal."
            ),
        }

    if lineup_risk in {
        "CRITICO",
        "MUY_ALTO",
    }:

        return {
            "allowed":
                False,

            "reason": (
                "El riesgo del XI es demasiado alto para "
                "mantener saldo negativo."
            ),
        }

    if recoverable_cash < deficit:

        return {
            "allowed":
                False,

            "reason": (
                "La liquidez recuperable detectada no cubre "
                "el deficit actual."
            ),
        }

    coverage_ratio = (
        recoverable_cash
        / deficit
    )

    if coverage_ratio < 1.25:

        return {
            "allowed":
                False,

            "reason": (
                "Existe cobertura teorica, pero el margen "
                "es demasiado pequeno."
            ),
        }

    return {
        "allowed":
            True,

        "reason": (
            "El deficit esta cubierto con margen y la fase "
            f"{phase} permite deuda temporal antes del cierre."
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


def build_solvency_state(
    snapshot: dict,
) -> dict:

    balance = (
        get_current_balance(
            snapshot
        )
    )

    deadline = (
        build_deadline_state(
            snapshot
        )
    )

    liquidatable = (
        calculate_liquidatable_assets(
            snapshot
        )
    )

    incoming = (
        calculate_incoming_offer_liquidity(
            snapshot
        )
    )

    recoverable_cash = max(
        liquidatable[
            "total"
        ],
        incoming[
            "total"
        ],
    )

    seconds_to_deadline = (
        deadline.get(
            "seconds_to_deadline"
        )
    )

    lineup_risk = (
        deadline[
            "lineup_risk"
        ]
    )

    phase = str(
        deadline.get(
            "phase",
            "CALENDAR_UNKNOWN",
        )
    )

    risk = (
        classify_solvency_risk(
            balance=
                balance,

            recoverable_cash=
                recoverable_cash,

            seconds_to_deadline=
                seconds_to_deadline,

            phase=
                phase,
        )
    )

    debt_permission = (
        calculate_temporary_debt_permission(
            balance=
                balance,

            recoverable_cash=
                recoverable_cash,

            seconds_to_deadline=
                seconds_to_deadline,

            lineup_risk=
                lineup_risk,

            phase=
                phase,
        )
    )

    hard_safety = (
        determine_hard_safety(
            balance=
                balance,

            deadline=
                deadline,

            lineup_risk=
                lineup_risk,
        )
    )

    return {
        "balance":
            balance,

        "is_negative":
            balance < 0,

        "phase":
            phase,

        "operations_locked":
            bool(
                deadline.get(
                    "operations_locked",
                    False,
                )
            ),

        "liquidatable_assets":
            liquidatable,

        "incoming_offer_liquidity":
            incoming,

        "recoverable_cash":
            recoverable_cash,

        "risk":
            risk,

        "temporary_debt":
            debt_permission,

        "hard_safety":
            hard_safety,

        "seconds_to_deadline":
            seconds_to_deadline,

        "lineup_risk":
            lineup_risk,

        "deadline":
            deadline,
    }
