from itertools import combinations

from src.analysis.intelligent_bid_engine import (
    calculate_intelligent_bids,
)
from src.analysis.lineup_engine import (
    build_lineup,
)
from src.analysis.recommendation_engine import (
    TARGET_COUNTS,
)
from src.analysis.team_analyzer import (
    analyze_team,
)


CASH_RESERVE_PERCENT = 0.20
EXTRA_OPPORTUNITY_SLOTS = 1
MIN_EXTRA_SCORE = 60


def get_structural_shortages(
    snapshot: dict,
) -> dict[int, int]:

    team = analyze_team(snapshot)

    shortages = {}

    for position_id, target in TARGET_COUNTS.items():

        current = (
            team["positions"]
            [position_id]
            ["count"]
        )

        shortages[position_id] = max(
            target - current,
            0,
        )

    return shortages


def calculate_combo_score(
    combo: tuple,
    matchday_shortages: dict[int, int],
    structural_shortages: dict[int, int],
) -> float:

    # Usamos ya el score después de aplicar
    # inteligencia externa.
    score = sum(
        player["intelligent_score"]
        for player in combo
    )

    # --------------------------------------------------
    # NO DUPLICAR BONUS DE URGENCIA DE JORNADA
    # --------------------------------------------------

    for position_id, shortage in (
        matchday_shortages.items()
    ):

        candidates = [
            player
            for player in combo
            if (
                player.get("position")
                == position_id
                and
                player.get(
                    "has_current_round_game",
                    False,
                )
                and
                player.get(
                    "matchday_need_score",
                    0,
                ) > 0
            )
        ]

        candidates.sort(
            key=lambda player:
                player.get("intelligent_score", 0),
            reverse=True,
        )

        extras = candidates[
            shortage:
        ]

        for player in extras:
            score -= player.get(
                "matchday_need_score",
                0,
            )

    # --------------------------------------------------
    # NO DUPLICAR BONUS ESTRUCTURAL
    # --------------------------------------------------

    for position_id, shortage in (
        structural_shortages.items()
    ):

        candidates = [
            player
            for player in combo
            if (
                player.get("position")
                == position_id
                and
                player.get(
                    "structural_need_score",
                    0,
                ) > 0
            )
        ]

        candidates.sort(
            key=lambda player:
                player.get("intelligent_score", 0),
            reverse=True,
        )

        extras = candidates[
            shortage:
        ]

        for player in extras:
            score -= player.get(
                "structural_need_score",
                0,
            )

    return score


def count_real_needs(
    matchday_shortages: dict[int, int],
) -> int:

    return sum(
        matchday_shortages.values()
    )


def combo_is_strategically_valid(
    combo: tuple,
    matchday_shortages: dict[int, int],
) -> bool:

    for player in combo:

        # Sin el dato, se asume que NO resuelve una urgencia: el
        # jugador tendra que justificarse por score. Es el lado
        # conservador, y evita que una clave ausente tumbe el
        # optimizador con un KeyError.
        solves_matchday_need = (
            bool(
                player.get(
                    "has_current_round_game",
                    False,
                )
            )
            and
            matchday_shortages.get(
                player.get("position"),
                0,
            ) > 0
        )

        # Si no resuelve una urgencia,
        # exigimos que sea una oportunidad
        # suficientemente buena.
        if not solves_matchday_need:

            if (
                player[
                    "intelligent_score"
                ]
                < MIN_EXTRA_SCORE
            ):
                return False

    return True


def optimize_portfolio(
    snapshot: dict,
    available_budget: int | None = None,
    rival_intelligence: dict | None = None,
) -> dict:
    """
    Elige la mejor COMBINACION de fichajes que cabe en el
    presupuesto.

    EL PRESUPUESTO SE MEDIA CONTRA LA MAGNITUD EQUIVOCADA

    Igual que pasaba en bid_engine: el presupuesto operativo salia
    del SALDO menos una reserva del 20 %. Con el saldo real del
    16/08/2026 eran 191.975 EUR, y de los diez candidatos el mas
    barato costaba 440.000. La salida era literalmente

        "No se ha encontrado ninguna combinacion valida."

    En Biwenger la capacidad de gasto no es la caja: es
    maximumBid, que el juego calcula ya con el limite de deuda
    dentro.

    Quien llame puede pasar un presupuesto propio, y deberia: el
    bueno es `available_budget` del motor de especulacion, que ya
    descuenta las pujas vivas de ciclos anteriores. El calculo de
    aqui es solo el respaldo.
    """

    # --------------------------------------------------
    # MOTOR INTELIGENTE
    # --------------------------------------------------

    recommendations = (
        calculate_intelligent_bids(
            snapshot,
            rival_intelligence=rival_intelligence,
        )
    )

    status = (
        snapshot.get("market", {}) or {}
    ).get("status", {}) or {}

    balance = int(status.get("balance", 0) or 0)

    maximum_bid = int(status.get("maximumBid", 0) or 0)

    budget_source = "INYECTADO"

    if available_budget is None:

        # Capacidad real de gasto, no caja.
        capacity = maximum_bid if maximum_bid > 0 else balance

        cash_reserve = int(
            capacity
            * CASH_RESERVE_PERCENT
        )

        available_budget = capacity - cash_reserve

        budget_source = (
            "MAXIMUM_BID"
            if maximum_bid > 0
            else "BALANCE"
        )

    else:
        available_budget = max(int(available_budget), 0)
        cash_reserve = 0

    # Nunca por encima de lo que Biwenger permite comprometer.
    if maximum_bid > 0:
        available_budget = min(available_budget, maximum_bid)

    # --------------------------------------------------
    # SOLO JUGADORES QUE SIGUEN SIENDO PUJABLES
    # DESPUÉS DE LA INTELIGENCIA EXTERNA
    # --------------------------------------------------

    candidates = [
        player
        for player in recommendations
        if (
            player["action"]
            == "PUJAR"
            and
            player["suggested_bid"]
            > 0
        )
    ]

    lineup = build_lineup(
        snapshot
    )

    matchday_shortages = (
        lineup[
            "matchday_shortages"
        ]
    )

    structural_shortages = (
        get_structural_shortages(
            snapshot
        )
    )

    real_needs = (
        count_real_needs(
            matchday_shortages
        )
    )

    max_players = min(
        real_needs
        + EXTRA_OPPORTUNITY_SLOTS,
        len(candidates),
    )

    max_players = max(
        max_players,
        1,
    )

    best_selection = []
    best_score = -1
    best_cost = 0

    # --------------------------------------------------
    # PROBAR COMBINACIONES
    # --------------------------------------------------

    for size in range(
        1,
        max_players + 1,
    ):

        for combo in combinations(
            candidates,
            size,
        ):

            total_cost = sum(
                player[
                    "suggested_bid"
                ]
                for player in combo
            )

            if (
                total_cost
                > available_budget
            ):
                continue

            if not combo_is_strategically_valid(
                combo,
                matchday_shortages,
            ):
                continue

            portfolio_score = (
                calculate_combo_score(
                    combo,
                    matchday_shortages,
                    structural_shortages,
                )
            )

            if (
                portfolio_score
                > best_score
                or (
                    portfolio_score
                    == best_score
                    and
                    total_cost
                    < best_cost
                )
            ):

                best_score = (
                    portfolio_score
                )

                best_selection = (
                    list(combo)
                )

                best_cost = (
                    total_cost
                )

    remaining_budget = (
        available_budget
        - best_cost
    )

    rejected = [
        player
        for player in candidates
        if player
        not in best_selection
    ]

    return {
        "balance":
            balance,

        "cash_reserve":
            cash_reserve,

        "available_budget":
            available_budget,

        "budget_source":
            budget_source,

        "maximum_bid":
            maximum_bid,

        "matchday_shortages":
            matchday_shortages,

        "structural_shortages":
            structural_shortages,

        "real_needs":
            real_needs,

        "max_players":
            max_players,

        "selected":
            best_selection,

        "rejected":
            rejected,

        "total_cost":
            best_cost,

        "remaining_budget":
            remaining_budget,

        "portfolio_score":
            best_score,
    }