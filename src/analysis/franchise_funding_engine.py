from src.analysis.bid_restructuring_engine import (
    build_bid_restructuring_plan,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ======================================================
# LOOKUP
# ======================================================


def get_strategic_lookup(
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
# CANDIDATOS LIQUIDABLES
# ======================================================


def calculate_sale_keep_score(
    sale: dict,
    strategic: dict | None,
) -> float:

    sale_score = float(
        sale.get(
            "sale_score",
            0,
        )
        or 0
    )

    if strategic is None:

        strategic_score = 0.0
        franchise_score = 0.0
        tactical_score = 0.0

    else:

        strategic_score = float(
            strategic.get(
                "strategic_score",
                0,
            )
            or 0
        )

        franchise_score = float(
            strategic.get(
                "franchise_score",
                0,
            )
            or 0
        )

        tactical_score = float(
            strategic.get(
                "tactical_score",
                0,
            )
            or 0
        )

    protection = (
        strategic_score * 0.30
        +
        franchise_score * 0.40
        +
        tactical_score * 0.20
        -
        sale_score * 0.45
    )

    return round(
        max(
            protection,
            0.0,
        ),
        2,
    )


def build_liquidatable_candidates(
    snapshot: dict,
) -> list[dict]:

    sales = (
        analyze_sales(
            snapshot
        )
    )

    lookup = (
        get_strategic_lookup(
            snapshot
        )
    )

    candidates = []

    for sale in sales:

        sale_score = float(
            sale.get(
                "sale_score",
                0,
            )
            or 0
        )

        if sale_score < 50:
            continue

        player_id = sale.get(
            "id"
        )

        if player_id is None:
            continue

        strategic = lookup.get(
            player_id
        )

        value = int(
            sale.get(
                "price",
                0,
            )
            or 0
        )

        if value <= 0:
            continue

        candidates.append(
            {
                **sale,

                "estimated_liquidity":
                    value,

                "keep_score":
                    calculate_sale_keep_score(
                        sale,
                        strategic,
                    ),

                "strategic_score":
                    (
                        strategic.get(
                            "strategic_score",
                            0,
                        )
                        if strategic
                        else 0
                    ),

                "franchise_score":
                    (
                        strategic.get(
                            "franchise_score",
                            0,
                        )
                        if strategic
                        else 0
                    ),
            }
        )

    candidates.sort(
        key=lambda player: (
            player[
                "keep_score"
            ],
            -player[
                "estimated_liquidity"
            ],
        )
    )

    return candidates


# ======================================================
# COBERTURA DE DEUDA
# ======================================================


def select_liquidity_plan(
    candidates: list[dict],
    debt: int,
) -> dict:

    if debt <= 0:

        return {
            "players":
                [],

            "estimated_liquidity":
                0,

            "covered":
                True,

            "excess":
                0,
        }

    selected = []

    liquidity = 0

    for player in candidates:

        selected.append(
            player
        )

        liquidity += int(
            player[
                "estimated_liquidity"
            ]
        )

        if liquidity >= debt:
            break

    return {
        "players":
            selected,

        "estimated_liquidity":
            liquidity,

        "covered":
            liquidity >= debt,

        "excess":
            max(
                liquidity
                - debt,
                0,
            ),
    }


# ======================================================
# PLAN PRINCIPAL
# ======================================================


def build_franchise_funding_plan(
    snapshot: dict,
) -> dict:

    restructuring = (
        build_bid_restructuring_plan(
            snapshot
        )
    )

    if not restructuring.get(
        "active"
    ):

        return {
            "active":
                False,

            "reason":
                restructuring.get(
                    "reason",
                    "No existe oportunidad Franchise.",
                ),
        }

    target = (
        restructuring[
            "target"
        ]
    )

    economy = (
        restructuring[
            "economy"
        ]
    )

    projected_debt = int(
        economy[
            "projected_debt_if_won"
        ]
    )

    projected_balance = int(
        economy[
            "projected_balance_if_won"
        ]
    )

    candidates = (
        build_liquidatable_candidates(
            snapshot
        )
    )

    liquidity_plan = (
        select_liquidity_plan(
            candidates,
            projected_debt,
        )
    )

    # ==================================================
    # DEADLINE / SOLVENCIA
    # ==================================================

    solvency = (
        restructuring[
            "solvency"
        ]
    )

    deadline = (
        solvency[
            "deadline"
        ]
    )

    seconds_to_deadline = (
        deadline[
            "calendar"
        ][
            "seconds_to_lineup_lock"
        ]
    )

    hours_to_deadline = None

    if seconds_to_deadline is not None:

        hours_to_deadline = (
            seconds_to_deadline
            / 3600
        )

    # ==================================================
    # DECISIÓN
    # ==================================================

    if projected_debt <= 0:

        recommendation = (
            "SIN_DEUDA"
        )

        reason = (
            "La compra Franchise no dejaría saldo "
            "negativo."
        )

    elif not liquidity_plan[
        "covered"
    ]:

        recommendation = (
            "DEUDA_NO_CUBIERTA"
        )

        reason = (
            "La deuda temporal proyectada supera la "
            "liquidez conservadora de los activos "
            "considerados vendibles."
        )

    elif (
        hours_to_deadline
        is not None
        and hours_to_deadline <= 24
    ):

        recommendation = (
            "NO_ASUMIR_DEUDA"
        )

        reason = (
            "La deuda sería liquidable, pero estamos "
            "demasiado cerca del deadline de jornada."
        )

    else:

        recommendation = (
            "DEUDA_TEMPORAL_CONTROLADA"
        )

        reason = (
            "La operación puede dejar saldo negativo "
            "temporalmente, pero la deuda estimada está "
            "cubierta por activos liquidables y existe "
            "margen temporal suficiente para volver a "
            "saldo no negativo antes de la jornada."
        )

    return {
        "active":
            True,

        "target":
            target,

        "target_bid":
            economy[
                "target_bid"
            ],

        "current_balance":
            economy[
                "balance"
            ],

        "projected_balance":
            projected_balance,

        "projected_debt":
            projected_debt,

        "required_unlock":
            economy[
                "required_unlock"
            ],

        "liquidatable_candidates":
            candidates,

        "liquidity_plan":
            liquidity_plan,

        "hours_to_deadline":
            (
                round(
                    hours_to_deadline,
                    1,
                )
                if hours_to_deadline
                is not None
                else None
            ),

        "recommendation":
            recommendation,

        "reason":
            reason,

        "restructuring":
            restructuring,
    }