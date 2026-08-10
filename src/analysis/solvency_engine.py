from src.analysis.deadline_engine import (
    build_deadline_state,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)


# ======================================================
# CONFIGURACIÓN
# ======================================================


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
            {}
        )
        .get(
            "status",
            {}
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
    """
    Patrimonio que potencialmente podemos convertir
    en liquidez.

    IMPORTANTE:
    esto NO es saldo confirmado.

    Solo usamos jugadores que el Sales Analyzer
    considera razonablemente prescindibles:
    Sale Score >= 50.
    """

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
                    player["id"],

                "name":
                    player["name"],

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
# OFERTAS RECIBIDAS
# ======================================================


def calculate_incoming_offer_liquidity(
    snapshot: dict,
) -> dict:
    """
    Dinero potencial procedente de ofertas
    recibidas.

    Sigue sin ser saldo confirmado mientras no
    aceptemos y comprobemos el nuevo balance.
    """

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
# RIESGO DE SOLVENCIA
# ======================================================


def classify_solvency_risk(
    balance: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
) -> str:

    # --------------------------------------------------
    # SALDO POSITIVO
    # --------------------------------------------------

    if balance >= 0:

        if balance >= SAFE_LIQUIDITY_BUFFER:
            return "BAJO"

        return "CONTROLAR"

    # --------------------------------------------------
    # SALDO NEGATIVO
    # --------------------------------------------------

    deficit = abs(
        balance
    )

    covered = (
        recoverable_cash
        >= deficit
    )

    if seconds_to_deadline is None:

        if covered:
            return "MODERADO"

        return "ALTO"

    hours = max(
        seconds_to_deadline
        / 3600,
        0,
    )

    if hours <= 6:
        return "CRITICO"

    if hours <= 24:

        if covered:
            return "MUY_ALTO"

        return "CRITICO"

    if hours <= 48:

        if covered:
            return "ALTO"

        return "MUY_ALTO"

    if covered:
        return "MODERADO"

    return "ALTO"


# ======================================================
# DEUDA TEMPORAL
# ======================================================


def calculate_temporary_debt_permission(
    balance: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
) -> dict:
    """
    Determina si mantener saldo negativo de forma
    temporal es razonablemente aceptable.

    Esta función NO autoriza sacrificar una jornada.
    Ese futuro modo excepcional será independiente.
    """

    if balance >= 0:

        return {
            "allowed":
                True,

            "reason":
                "El saldo actual no es negativo.",
        }

    deficit = abs(
        balance
    )

    if seconds_to_deadline is None:

        return {
            "allowed":
                False,

            "reason": (
                "No conocemos el deadline de jornada "
                "y no podemos autorizar deuda temporal."
            ),
        }

    hours = (
        seconds_to_deadline
        / 3600
    )

    if hours <= 24:

        return {
            "allowed":
                False,

            "reason": (
                "Quedan menos de 24 horas para el "
                "deadline. Bordalás IA bloquea nueva "
                "deuda temporal."
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
                "El riesgo de XI es demasiado alto "
                "para mantener saldo negativo."
            ),
        }

    if recoverable_cash < deficit:

        return {
            "allowed":
                False,

            "reason": (
                "La liquidez recuperable detectada "
                "no cubre el déficit actual."
            ),
        }

    coverage_ratio = (
        recoverable_cash
        / deficit
    )

    # Exigimos cierto colchón.
    if coverage_ratio < 1.25:

        return {
            "allowed":
                False,

            "reason": (
                "Existe cobertura teórica, pero el "
                "margen es demasiado pequeño para "
                "asumir el riesgo."
            ),
        }

    return {
        "allowed":
            True,

        "reason": (
            "El déficit está cubierto por activos "
            "liquidables y queda margen temporal "
            "suficiente antes de la jornada."
        ),
    }


# ======================================================
# HARD SAFETY
# ======================================================


def determine_hard_safety(
    balance: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
) -> dict:

    reasons = []
    active = False

    if seconds_to_deadline is not None:

        # A menos de 24h:
        # saldo negativo ya se convierte en situación
        # de emergencia.
        if (
            seconds_to_deadline
            <= 24 * 3600
            and balance < 0
        ):

            active = True

            reasons.append(
                "Saldo negativo a menos de 24h."
            )

        # A menos de 6h entramos en Safety Mode
        # aunque el saldo sea positivo.
        if (
            seconds_to_deadline
            <= 6 * 3600
        ):

            active = True

            reasons.append(
                "Menos de 6h para el deadline."
            )

    if lineup_risk == "CRITICO":

        active = True

        reasons.append(
            "Riesgo crítico de XI."
        )

    return {
        "active":
            active,

        "reasons":
            reasons,
    }


# ======================================================
# COBERTURA DE UNA DEUDA HIPOTÉTICA
# ======================================================


def evaluate_projected_debt(
    debt: int,
    recoverable_cash: int,
    seconds_to_deadline: int | None,
    lineup_risk: str,
) -> dict:
    """
    Permite que otros motores pregunten:

    "Si esta operación me dejara X euros en negativo,
    ¿sería razonablemente saneable?"

    Así Solvency Engine sigue siendo independiente
    de Yamal, Franchise, Speculation, etc.
    """

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
                "La operación no generaría deuda.",
        }

    covered = (
        recoverable_cash
        >= debt
    )

    coverage_ratio = (
        recoverable_cash
        / debt
    )

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
                "No conocemos el deadline y no podemos "
                "validar deuda futura con seguridad."
            ),
        }

    hours = (
        seconds_to_deadline
        / 3600
    )

    if hours <= 24:

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
                "No autorizamos una nueva deuda a menos "
                "de 24 horas del deadline."
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
                "El riesgo de alineación es demasiado "
                "alto para asumir deuda adicional."
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
                "La deuda está cubierta, pero no existe "
                "un colchón de liquidez suficiente."
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
            "La deuda proyectada está cubierta con "
            "margen y queda tiempo suficiente para "
            "sanearla antes del deadline."
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

    # ==================================================
    # LIQUIDEZ RECUPERABLE
    # ==================================================
    #
    # No sumamos ambos bloques porque una oferta
    # recibida podría corresponder al mismo jugador
    # que ya estamos contando como activo liquidable.
    #
    # Hasta validar ofertas recibidas reales,
    # usamos el mayor de los dos valores.
    # ==================================================

    recoverable_cash = max(
        liquidatable[
            "total"
        ],
        incoming[
            "total"
        ],
    )

    seconds_to_deadline = (
        deadline[
            "calendar"
        ][
            "seconds_to_lineup_lock"
        ]
    )

    lineup_risk = (
        deadline[
            "lineup_risk"
        ]
    )

    risk = (
        classify_solvency_risk(
            balance=
                balance,

            recoverable_cash=
                recoverable_cash,

            seconds_to_deadline=
                seconds_to_deadline,
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
        )
    )

    hard_safety = (
        determine_hard_safety(
            balance=
                balance,

            seconds_to_deadline=
                seconds_to_deadline,

            lineup_risk=
                lineup_risk,
        )
    )

    return {
        "balance":
            balance,

        "is_negative":
            balance < 0,

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