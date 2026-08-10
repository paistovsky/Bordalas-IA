from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


def clamp(
    value: int,
    minimum: int,
    maximum: int,
) -> int:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def get_active_bid_commitment(
    snapshot: dict,
) -> int:
    """
    Calcula dinero comprometido en pujas activas.

    Intentamos soportar distintas estructuras
    devueltas por Biwenger.
    """

    total = 0

    offers = (
        snapshot[
            "market"
        ].get(
            "offers",
            [],
        )
    )

    for offer in offers:

        amount = (
            offer.get("amount")
            or offer.get("price")
            or 0
        )

        try:
            total += int(
                amount
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

    return total


def get_premium_targets(
    snapshot: dict,
) -> list[dict]:

    board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="strategic",
        )
    )

    return [
        player
        for player in board
        if (
            player[
                "strategic_score"
            ]
            >= 70
            and
            player[
                "ownership_state"
            ]
            != "MI_EQUIPO"
        )
    ]


def get_premium_targets_in_market(
    snapshot: dict,
) -> list[dict]:

    return [
        player
        for player
        in get_premium_targets(
            snapshot
        )
        if (
            player[
                "ownership_state"
            ]
            == "EN_MERCADO"
        )
    ]


def calculate_emergency_reserve(
    balance: int,
    playable_count: int,
) -> int:
    """
    Reserva mínima.

    Si el XI está incompleto tenemos que dejar
    más flexibilidad para solucionar urgencias.
    """

    if playable_count <= 7:
        percentage = 0.20

    elif playable_count <= 9:
        percentage = 0.15

    else:
        percentage = 0.10

    reserve = int(
        balance
        * percentage
    )

    return max(
        reserve,
        1_500_000,
    )


def calculate_premium_reserve(
    balance: int,
    premium_targets: list[dict],
    premium_in_market: list[dict],
) -> int:
    """
    Dinero que Bordalás quiere conservar para
    jugadores verdaderamente diferenciales.

    Si aparece un premium EN MERCADO, ya no
    hablamos de una reserva futura:
    la oportunidad es actual.
    """

    if premium_in_market:

        best = max(
            premium_in_market,
            key=lambda player:
                player[
                    "strategic_score"
                ],
        )

        target_price = int(
            best["price"]
        )

        # Intentamos conservar una cantidad
        # significativa para competir por él,
        # sin bloquear absolutamente toda la caja.
        desired = int(
            target_price
            * 0.70
        )

        return clamp(
            desired,
            4_000_000,
            int(
                balance
                * 0.75
            ),
        )

    if not premium_targets:
        return 0

    best = premium_targets[0]

    score = (
        best[
            "strategic_score"
        ]
    )

    if score >= 85:
        percentage = 0.40

    elif score >= 78:
        percentage = 0.35

    elif score >= 70:
        percentage = 0.30

    else:
        percentage = 0.20

    return int(
        balance
        * percentage
    )


def determine_budget_mode(
    playable_count: int,
    premium_in_market: list[dict],
) -> str:

    if playable_count < 9:
        return "EMERGENCIA XI"

    if premium_in_market:
        return "OPORTUNIDAD PREMIUM"

    if playable_count < 11:
        return "COMPLETAR XI"

    return "CONSTRUCCIÓN DE PLANTILLA"


def build_strategic_budget(
    snapshot: dict,
) -> dict:

    from src.analysis.lineup_engine import (
        build_lineup,
    )

    lineup = build_lineup(
        snapshot
    )

    balance = int(
        snapshot[
            "market"
        ][
            "status"
        ][
            "balance"
        ]
    )

    maximum_bid = int(
        snapshot[
            "market"
        ][
            "status"
        ].get(
            "maximumBid",
            balance,
        )
        or balance
    )

    active_commitment = (
        get_active_bid_commitment(
            snapshot
        )
    )

    premium_targets = (
        get_premium_targets(
            snapshot
        )
    )

    premium_in_market = (
        get_premium_targets_in_market(
            snapshot
        )
    )

    emergency_reserve = (
        calculate_emergency_reserve(
            balance=
                balance,

            playable_count=
                lineup[
                    "playable_count"
                ],
        )
    )

    premium_reserve = (
        calculate_premium_reserve(
            balance=
                balance,

            premium_targets=
                premium_targets,

            premium_in_market=
                premium_in_market,
        )
    )

    # No duplicamos reservas hasta el punto
    # de hacer imposible toda operación.
    total_reserve = min(
        emergency_reserve
        + premium_reserve,

        int(
            balance
            * 0.85
        ),
    )

    tactical_budget = max(
        balance
        - total_reserve,
        0,
    )

    free_after_active_bids = max(
        balance
        - active_commitment,
        0,
    )

    safe_new_spending = max(
        min(
            tactical_budget,
            free_after_active_bids,
        ),
        0,
    )

    mode = determine_budget_mode(
        playable_count=
            lineup[
                "playable_count"
            ],

        premium_in_market=
            premium_in_market,
    )

    return {
        "mode":
            mode,

        "balance":
            balance,

        "maximum_bid":
            maximum_bid,

        "active_bid_commitment":
            active_commitment,

        "emergency_reserve":
            emergency_reserve,

        "premium_reserve":
            premium_reserve,

        "total_reserve":
            total_reserve,

        "tactical_budget":
            tactical_budget,

        "free_after_active_bids":
            free_after_active_bids,

        "safe_new_spending":
            safe_new_spending,

        "playable_count":
            lineup[
                "playable_count"
            ],

        "premium_targets":
            premium_targets,

        "premium_in_market":
            premium_in_market,

        "best_premium":
            (
                premium_targets[0]
                if premium_targets
                else None
            ),
    }