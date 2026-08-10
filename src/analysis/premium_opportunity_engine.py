from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)

from src.analysis.strategic_budget_engine import (
    build_strategic_budget,
)


# ======================================================
# CONFIGURACIÓN PREMIUM / FRANCHISE
# ======================================================

MIN_RESTRUCTURE_FRANCHISE_SCORE = 70.0


# ======================================================
# CLASIFICACIÓN DE OPORTUNIDAD
# ======================================================


def classify_premium_opportunity(
    player: dict,
) -> str:
    """
    Clasifica la magnitud de una oportunidad premium.

    IMPORTANTE:

    Ya NO utilizamos Strategic Score para decidir
    si un jugador puede provocar una reestructuración.

    Strategic:
        ¿Es un buen activo de temporada?

    Franchise:
        ¿Es suficientemente diferencial como para
        construir/reorganizar la plantilla alrededor
        de él?
    """

    franchise_score = float(
        player.get(
            "franchise_score",
            0,
        )
        or 0
    )

    if franchise_score >= 90:
        return "SUPERSTAR"

    if franchise_score >= 85:
        return "EXCEPCIONAL"

    if franchise_score >= 80:
        return "MUY_ALTA"

    if franchise_score >= 70:
        return "ALTA"

    return "NORMAL"


# ======================================================
# VALIDACIÓN PREMIUM
# ======================================================


def is_actionable_premium(
    player: dict,
) -> bool:
    """
    Un jugador solo puede activar el motor Premium si:

    1. Está realmente en el mercado.
    2. Su Franchise Score supera el mínimo.
    3. El Franchise Engine permite reestructurar.
    4. Está disponible deportivamente.

    Esto evita que jugadores como Mbappé provoquen
    operaciones cuando todavía NO están en mercado.
    """

    if (
        player.get(
            "ownership_state"
        )
        != "EN_MERCADO"
    ):
        return False

    franchise_score = float(
        player.get(
            "franchise_score",
            0,
        )
        or 0
    )

    if (
        franchise_score
        < MIN_RESTRUCTURE_FRANCHISE_SCORE
    ):
        return False

    if not player.get(
        "can_trigger_restructure",
        False,
    ):
        return False

    availability = (
        player.get(
            "availability",
            {}
        )
        or {}
    )

    if not availability.get(
        "available",
        True,
    ):
        return False

    return True


# ======================================================
# CAJA OBJETIVO
# ======================================================


def calculate_required_cash(
    player: dict,
) -> int:
    """
    Calcula la caja objetivo para competir por un
    jugador Franchise/Premium.

    No utilizamos exactamente el valor de mercado.

    Dejamos margen para una puja competitiva, pero
    seguimos tratando este valor como PRESUPUESTO
    objetivo, no como obligación de pujar siempre
    exactamente esa cantidad.

    La agresividad depende principalmente del
    Franchise Score.
    """

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    franchise_score = float(
        player.get(
            "franchise_score",
            0,
        )
        or 0
    )

    strategic_score = float(
        player.get(
            "strategic_score",
            0,
        )
        or 0
    )

    # --------------------------------------------------
    # Multiplicador base Franchise
    # --------------------------------------------------

    if franchise_score >= 90:
        multiplier = 1.14

    elif franchise_score >= 85:
        multiplier = 1.11

    elif franchise_score >= 80:
        multiplier = 1.09

    elif franchise_score >= 75:
        multiplier = 1.07

    else:
        multiplier = 1.05

    # --------------------------------------------------
    # Confirmación Strategic
    # --------------------------------------------------
    #
    # Franchise permite plantear la reestructuración.
    #
    # Strategic confirma que además estamos ante un
    # activo fuerte de temporada.
    #
    # Añadimos solo una pequeña prima.
    #

    if strategic_score >= 80:
        multiplier += 0.02

    elif strategic_score >= 70:
        multiplier += 0.01

    required_cash = int(
        price
        * multiplier
    )

    return max(
        required_cash,
        price,
    )


# ======================================================
# PREMIUM OPPORTUNITY PLAN
# ======================================================


def build_premium_opportunity_plan(
    snapshot: dict,
) -> dict:

    budget = (
        build_strategic_budget(
            snapshot
        )
    )

    # --------------------------------------------------
    # Utilizamos el board Franchise.
    # --------------------------------------------------

    board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="franchise",
        )
    )

    # --------------------------------------------------
    # Premiums accionables HOY
    # --------------------------------------------------

    available = [
        player
        for player in board
        if is_actionable_premium(
            player
        )
    ]

    # --------------------------------------------------
    # Ningún Franchise disponible
    # --------------------------------------------------

    if not available:

        return {
            "active":
                False,

            "target":
                None,

            "decision":
                "NO_PREMIUM_AVAILABLE",

            "opportunity_level":
                None,

            "market_price":
                0,

            "required_cash":
                0,

            "balance":
                int(
                    budget.get(
                        "balance",
                        0,
                    )
                    or 0
                ),

            "active_commitment":
                int(
                    budget.get(
                        "active_bid_commitment",
                        0,
                    )
                    or 0
                ),

            "free_cash":
                0,

            "recover_needed":
                0,

            "budget":
                budget,
        }

    # --------------------------------------------------
    # Selección del objetivo
    # --------------------------------------------------
    #
    # Primero Franchise.
    #
    # En empate:
    # Strategic y producción histórica.
    # --------------------------------------------------

    target = max(
        available,
        key=lambda player: (
            float(
                player.get(
                    "franchise_score",
                    0,
                )
                or 0
            ),
            float(
                player.get(
                    "strategic_score",
                    0,
                )
                or 0
            ),
            int(
                player.get(
                    "points_last_season",
                    0,
                )
                or 0
            ),
        ),
    )

    required_cash = (
        calculate_required_cash(
            target
        )
    )

    balance = int(
        budget.get(
            "balance",
            0,
        )
        or 0
    )

    active_commitment = int(
        budget.get(
            "active_bid_commitment",
            0,
        )
        or 0
    )

    free_cash = max(
        balance
        - active_commitment,
        0,
    )

    recover_needed = max(
        required_cash
        - free_cash,
        0,
    )

    opportunity_level = (
        classify_premium_opportunity(
            target
        )
    )

    # ==================================================
    # DECISIÓN ECONÓMICA
    # ==================================================
    #
    # ATACAR_PREMIUM:
    # tenemos caja incluso respetando compromisos.
    #
    # REESTRUCTURAR_PUJAS:
    # podemos atacarlo cancelando/reduciendo pujas.
    #
    # NECESITA_VENTAS:
    # ni liberando las pujas actuales basta.
    #
    # IMPORTANTE:
    #
    # Esta decisión NO ejecuta ventas.
    # Solo informa al Decision Gate.
    # ==================================================

    if required_cash <= free_cash:

        decision = (
            "ATACAR_PREMIUM"
        )

    elif required_cash <= balance:

        decision = (
            "REESTRUCTURAR_PUJAS"
        )

    else:

        decision = (
            "NECESITA_VENTAS"
        )

    return {
        "active":
            True,

        "target":
            target,

        "opportunity_level":
            opportunity_level,

        "decision":
            decision,

        "market_price":
            int(
                target.get(
                    "price",
                    0,
                )
                or 0
            ),

        "franchise_score":
            float(
                target.get(
                    "franchise_score",
                    0,
                )
                or 0
            ),

        "strategic_score":
            float(
                target.get(
                    "strategic_score",
                    0,
                )
                or 0
            ),

        "franchise_classification":
            target.get(
                "franchise_classification",
                "NO FRANCHISE",
            ),

        "required_cash":
            required_cash,

        "balance":
            balance,

        "active_commitment":
            active_commitment,

        "free_cash":
            free_cash,

        "recover_needed":
            recover_needed,

        "budget":
            budget,
    }