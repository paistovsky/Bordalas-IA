from itertools import combinations

from src.analysis.premium_opportunity_engine import (
    build_premium_opportunity_plan,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.analysis.strategic_decision_gate import (
    build_strategic_decision,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ======================================================
# UTILIDADES DE OFERTAS
# ======================================================


def extract_requested_player_id(
    offer: dict,
) -> int | None:

    requested = offer.get(
        "requestedPlayers"
    )

    if requested:

        first = requested[0]

        if isinstance(
            first,
            int,
        ):
            return first

        if isinstance(
            first,
            dict,
        ):
            return first.get(
                "id"
            )

    player = offer.get(
        "player"
    )

    if isinstance(
        player,
        int,
    ):
        return player

    if isinstance(
        player,
        dict,
    ):
        return player.get(
            "id"
        )

    return None


def extract_offer_amount(
    offer: dict,
) -> int:

    return int(
        offer.get(
            "amount",
            offer.get(
                "price",
                0,
            ),
        )
        or 0
    )


# ======================================================
# JUGADORES
# ======================================================


def get_target_lookup(
    snapshot: dict,
) -> dict[int, dict]:

    board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="strategic",
        )
    )

    return {
        player["id"]:
            player

        for player in board
    }


# ======================================================
# PUJAS ACTIVAS
# ======================================================


def get_active_bid_players(
    snapshot: dict,
) -> list[dict]:

    lookup = (
        get_target_lookup(
            snapshot
        )
    )

    offers = (
        snapshot
        .get(
            "market",
            {}
        )
        .get(
            "offers",
            [],
        )
    )

    results = []

    for offer in offers:

        player_id = (
            extract_requested_player_id(
                offer
            )
        )

        if player_id is None:
            continue

        player = lookup.get(
            player_id
        )

        if player is None:
            continue

        results.append(
            {
                **player,

                "bid_amount":
                    extract_offer_amount(
                        offer
                    ),

                "offer_id":
                    offer.get(
                        "id"
                    ),

                "raw_offer":
                    offer,
            }
        )

    return results


# ======================================================
# VALOR DE CONSERVAR UNA PUJA
# ======================================================


def calculate_position_protection(
    player: dict,
) -> float:

    return float(
        player.get(
            "squad_need_bonus",
            0,
        )
        or 0
    )


def calculate_bid_keep_score(
    player: dict,
) -> float:

    franchise = float(
        player.get(
            "franchise_score",
            0,
        )
        or 0
    )

    strategic = float(
        player.get(
            "strategic_score",
            0,
        )
        or 0
    )

    tactical = float(
        player.get(
            "tactical_score",
            0,
        )
        or 0
    )

    need = (
        calculate_position_protection(
            player
        )
    )

    keep_score = (
        franchise * 0.30
        +
        strategic * 0.30
        +
        tactical * 0.30
        +
        need * 0.10
    )

    return round(
        keep_score,
        2,
    )


def calculate_cancel_cost(
    player: dict,
) -> float:

    amount = int(
        player.get(
            "bid_amount",
            0,
        )
        or 0
    )

    if amount <= 0:
        return 9999.0

    keep_score = (
        calculate_bid_keep_score(
            player
        )
    )

    millions = (
        amount
        / 1_000_000
    )

    return round(
        keep_score
        / millions,
        3,
    )


def enrich_bid(
    player: dict,
) -> dict:

    return {
        **player,

        "keep_score":
            calculate_bid_keep_score(
                player
            ),

        "cancel_cost":
            calculate_cancel_cost(
                player
            ),
    }


# ======================================================
# COMBINACIONES
# ======================================================


def evaluate_combination(
    players: tuple[dict, ...],
    required_unlock: int,
) -> dict:

    unlocked = sum(
        int(
            player[
                "bid_amount"
            ]
        )
        for player in players
    )

    excess = max(
        unlocked
        - required_unlock,
        0,
    )

    base_damage = sum(
        float(
            player[
                "keep_score"
            ]
        )
        for player in players
    )

    # Penalizamos retirar muchas operaciones.
    base_damage += (
        max(
            len(players) - 1,
            0,
        )
        * 5
    )

    position_damage = sum(
        float(
            player.get(
                "squad_need_bonus",
                0,
            )
            or 0
        )
        * 0.40
        for player in players
    )

    # Evitamos liberar mucho más capital
    # del necesario sin motivo.
    excess_penalty = (
        excess
        / 1_000_000
    ) * 2.0

    optimization_score = (
        base_damage
        + position_damage
        + excess_penalty
    )

    return {
        "players":
            list(
                players
            ),

        "unlocked":
            unlocked,

        "excess":
            excess,

        "base_damage":
            round(
                base_damage,
                2,
            ),

        "position_damage":
            round(
                position_damage,
                2,
            ),

        "optimization_score":
            round(
                optimization_score,
                2,
            ),
    }


def find_best_cancellation_combination(
    bids: list[dict],
    required_unlock: int,
) -> dict | None:

    if required_unlock <= 0:

        return {
            "players":
                [],

            "unlocked":
                0,

            "excess":
                0,

            "base_damage":
                0.0,

            "position_damage":
                0.0,

            "optimization_score":
                0.0,
        }

    candidates = []

    for size in range(
        1,
        len(bids) + 1,
    ):

        for combo in combinations(
            bids,
            size,
        ):

            unlocked = sum(
                int(
                    player[
                        "bid_amount"
                    ]
                )
                for player in combo
            )

            if unlocked < required_unlock:
                continue

            candidates.append(
                evaluate_combination(
                    combo,
                    required_unlock,
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[
                "optimization_score"
            ],
            item[
                "excess"
            ],
            len(
                item[
                    "players"
                ]
            ),
        )
    )

    return candidates[0]


# ======================================================
# ECONOMÍA REAL DE LA REESTRUCTURACIÓN
# ======================================================


def calculate_restructuring_economy(
    snapshot: dict,
    premium_plan: dict,
    active_bids: list[dict],
) -> dict:

    market_status = (
        snapshot
        .get(
            "market",
            {}
        )
        .get(
            "status",
            {}
        )
    )

    balance = int(
        market_status.get(
            "balance",
            0,
        )
        or 0
    )

    maximum_bid = int(
        market_status.get(
            "maximumBid",
            0,
        )
        or 0
    )

    target_bid = int(
        premium_plan.get(
            "required_cash",
            0,
        )
        or 0
    )

    active_commitment = sum(
        int(
            player.get(
                "bid_amount",
                0,
            )
            or 0
        )
        for player in active_bids
    )

    # ==================================================
    # CAPACIDAD DE COMPRA
    # ==================================================
    #
    # maximumBid determina cuánto podemos ofertar AHORA.
    #
    # Si target_bid > maximumBid,
    # necesitamos desbloquear capital retirando ofertas.
    # ==================================================

    required_unlock = max(
        target_bid
        - maximum_bid,
        0,
    )

    # ==================================================
    # DEUDA PROYECTADA
    # ==================================================
    #
    # Comprar por encima del saldo NO implica que la
    # operación sea imposible.
    #
    # Representa la deuda temporal que tendremos que
    # corregir antes del deadline de jornada.
    # ==================================================

    projected_debt_if_won = max(
        target_bid
        - balance,
        0,
    )

    projected_balance_if_won = (
        balance
        - target_bid
    )

    # Capacidad máxima teórica observada en la liga:
    #
    # maximumBid + pujas comprometidas
    #
    # Lo usamos como señal diagnóstica, no como una
    # fórmula universal hardcodeada.
    observed_total_bid_capacity = (
        maximum_bid
        + active_commitment
    )

    return {
        "balance":
            balance,

        "maximum_bid":
            maximum_bid,

        "target_bid":
            target_bid,

        "active_commitment":
            active_commitment,

        "required_unlock":
            required_unlock,

        "projected_debt_if_won":
            projected_debt_if_won,

        "projected_balance_if_won":
            projected_balance_if_won,

        "total_unlockable":
            active_commitment,

        "observed_total_bid_capacity":
            observed_total_bid_capacity,
    }


# ======================================================
# PLAN PRINCIPAL
# ======================================================


def build_bid_restructuring_plan(
    snapshot: dict,
) -> dict:

    strategic_decision = (
        build_strategic_decision(
            snapshot
        )
    )

    premium = (
        build_premium_opportunity_plan(
            snapshot
        )
    )

    if not premium.get(
        "active"
    ):

        return {
            "active":
                False,

            "reason":
                "No existe oportunidad Franchise activa.",

            "target":
                None,
        }

    target = (
        premium[
            "target"
        ]
    )

    active_bids = [
        enrich_bid(
            player
        )
        for player
        in get_active_bid_players(
            snapshot
        )
        if player[
            "id"
        ]
        != target[
            "id"
        ]
    ]

    active_bids.sort(
        key=lambda player: (
            player[
                "cancel_cost"
            ],
            player[
                "keep_score"
            ],
        )
    )

    economy = (
        calculate_restructuring_economy(
            snapshot=
                snapshot,

            premium_plan=
                premium,

            active_bids=
                active_bids,
        )
    )

    required_unlock = (
        economy[
            "required_unlock"
        ]
    )

    best_combination = (
        find_best_cancellation_combination(
            active_bids,
            required_unlock,
        )
    )

    can_unlock = (
        required_unlock <= 0
        or
        best_combination is not None
    )

    # ==================================================
    # SOLVENCIA DE LA DEUDA POSTERIOR
    # ==================================================

    solvency = (
        build_solvency_state(
            snapshot
        )
    )

    projected_debt = (
        economy[
            "projected_debt_if_won"
        ]
    )

    recoverable_cash = int(
        solvency.get(
            "recoverable_cash",
            0,
        )
        or 0
    )

    debt_coverage_ratio = None

    if projected_debt > 0:

        debt_coverage_ratio = (
            recoverable_cash
            / projected_debt
        )

    debt_theoretically_covered = (
        projected_debt == 0
        or
        recoverable_cash
        >= projected_debt
    )

    # ==================================================
    # DECISIÓN
    # ==================================================

    if not can_unlock:

        recommendation = (
            "CAPACIDAD_INSUFICIENTE"
        )

        reason = (
            "Las pujas activas cancelables no permiten "
            "desbloquear suficiente capacidad para alcanzar "
            "la puja objetivo del jugador Franchise."
        )

    elif required_unlock <= 0:

        if debt_theoretically_covered:

            recommendation = (
                "FRANCHISE_FINANCIABLE"
            )

            reason = (
                "La puja máxima actual ya permite atacar "
                "al Franchise y la deuda temporal proyectada "
                "está cubierta teóricamente por activos "
                "liquidables."
            )

        else:

            recommendation = (
                "PUJA_POSIBLE_DEUDA_NO_CUBIERTA"
            )

            reason = (
                "La puja es técnicamente posible, pero la "
                "deuda temporal proyectada no está cubierta "
                "por la liquidez recuperable detectada."
            )

    else:

        if debt_theoretically_covered:

            recommendation = (
                "REESTRUCTURAR_Y_ATACAR"
            )

            reason = (
                "Cancelando la combinación óptima se puede "
                "alcanzar la capacidad de puja necesaria. "
                "La deuda temporal proyectada está cubierta "
                "teóricamente y existe margen antes del "
                "deadline."
            )

        else:

            recommendation = (
                "REESTRUCTURAR_PERO_NO_ATACAR_AUN"
            )

            reason = (
                "Podemos desbloquear capacidad de compra, "
                "pero la deuda resultante todavía no tiene "
                "cobertura de liquidez suficiente."
            )

    return {
        "active":
            True,

        "target":
            target,

        "economy":
            economy,

        "active_bids":
            active_bids,

        "best_combination":
            best_combination,

        "can_unlock":
            can_unlock,

        "solvency":
            solvency,

        "recoverable_cash":
            recoverable_cash,

        "debt_coverage_ratio":
            (
                round(
                    debt_coverage_ratio,
                    2,
                )
                if debt_coverage_ratio
                is not None
                else None
            ),

        "debt_theoretically_covered":
            debt_theoretically_covered,

        "recommendation":
            recommendation,

        "reason":
            reason,

        "premium_plan":
            premium,

        "strategic_decision":
            strategic_decision,
    }