from src.analysis.premium_opportunity_engine import (
    build_premium_opportunity_plan,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


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
        player["id"]: player
        for player in board
    }


def get_market_sale_lookup(
    snapshot: dict,
) -> dict[int, dict]:

    return {
        int(
            sale["player"]["id"]
        ): sale

        for sale in snapshot[
            "market"
        ].get(
            "sales",
            [],
        )
    }


def extract_requested_player_id(
    offer: dict,
) -> int | None:
    """
    Intenta obtener el jugador de una
    oferta activa soportando varios formatos.
    """

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


def get_active_bid_players(
    snapshot: dict,
) -> list[dict]:

    target_lookup = (
        get_target_lookup(
            snapshot
        )
    )

    results = []

    offers = (
        snapshot[
            "market"
        ].get(
            "offers",
            [],
        )
    )

    for offer in offers:

        player_id = (
            extract_requested_player_id(
                offer
            )
        )

        if player_id is None:
            continue

        target = target_lookup.get(
            player_id
        )

        if target is None:
            continue

        amount = int(
            offer.get(
                "amount",
                offer.get(
                    "price",
                    0,
                ),
            )
            or 0
        )

        results.append(
            {
                **target,

                "bid_amount":
                    amount,
            }
        )

    return results


def calculate_plan_asset_score(
    players: list[dict],
) -> float:
    """
    Valor estratégico acumulado.

    Aplicamos rendimientos decrecientes para
    evitar que 4 jugadores mediocres ganen
    automáticamente a una superestrella solo
    porque sumamos cuatro scores completos.
    """

    if not players:
        return 0.0

    ordered = sorted(
        players,
        key=lambda player:
            player[
                "strategic_score"
            ],
        reverse=True,
    )

    weights = [
        1.00,
        0.65,
        0.45,
        0.30,
        0.20,
    ]

    total = 0.0

    for index, player in enumerate(
        ordered
    ):

        weight = (
            weights[index]
            if index < len(weights)
            else 0.15
        )

        total += (
            player[
                "strategic_score"
            ]
            * weight
        )

    return round(
        total,
        2,
    )


def calculate_tactical_plan_score(
    players: list[dict],
) -> float:

    if not players:
        return 0.0

    ordered = sorted(
        players,
        key=lambda player:
            player[
                "tactical_score"
            ],
        reverse=True,
    )

    weights = [
        1.00,
        0.70,
        0.50,
        0.35,
        0.25,
    ]

    total = 0.0

    for index, player in enumerate(
        ordered
    ):

        weight = (
            weights[index]
            if index < len(weights)
            else 0.20
        )

        total += (
            player[
                "tactical_score"
            ]
            * weight
        )

    return round(
        total,
        2,
    )


def get_cheap_market_reinforcements(
    snapshot: dict,
    exclude_ids: set[int],
    maximum_price: int = 3_000_000,
    limit: int = 3,
) -> list[dict]:
    """
    Busca jugadores baratos disponibles ahora
    para acompañar al fichaje premium.

    Priorizamos Tactical Score.
    """

    board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="tactical",
        )
    )

    candidates = [
        player

        for player in board

        if (
            player[
                "ownership_state"
            ]
            == "EN_MERCADO"

            and player["id"]
            not in exclude_ids

            and int(
                player["price"]
            )
            <= maximum_price

            and player[
                "tactical_score"
            ]
            >= 40
        )
    ]

    candidates.sort(
        key=lambda player: (
            player[
                "tactical_score"
            ],
            player[
                "strategic_score"
            ],
        ),
        reverse=True,
    )

    return candidates[
        :limit
    ]


def build_current_plan(
    snapshot: dict,
) -> dict:

    active_players = (
        get_active_bid_players(
            snapshot
        )
    )

    cost = sum(
        player[
            "bid_amount"
        ]

        for player
        in active_players
    )

    strategic_score = (
        calculate_plan_asset_score(
            active_players
        )
    )

    tactical_score = (
        calculate_tactical_plan_score(
            active_players
        )
    )

    return {
        "name":
            "PLAN TÁCTICO ACTUAL",

        "players":
            active_players,

        "cost":
            cost,

        "strategic_score":
            strategic_score,

        "tactical_score":
            tactical_score,
    }


def build_premium_plan(
    snapshot: dict,
) -> dict:

    premium = (
        build_premium_opportunity_plan(
            snapshot
        )
    )

    if not premium[
        "active"
    ]:

        return {
            "available":
                False,
        }

    target = premium[
        "target"
    ]

    target_cost = int(
        premium[
            "required_cash"
        ]
    )

    cheap_reinforcements = (
        get_cheap_market_reinforcements(
            snapshot=
                snapshot,

            exclude_ids={
                target["id"]
            },

            maximum_price=
                3_000_000,

            limit=
                3,
        )
    )

    # Para la simulación utilizamos aproximadamente
    # el valor actual como coste de los complementos.
    reinforcement_cost = sum(
        int(
            player[
                "price"
            ]
        )

        for player
        in cheap_reinforcements
    )

    players = [
        target,
        *cheap_reinforcements,
    ]

    return {
        "available":
            True,

        "name":
            "PLAN PREMIUM",

        "target":
            target,

        "reinforcements":
            cheap_reinforcements,

        "players":
            players,

        "premium_cost":
            target_cost,

        "reinforcement_cost":
            reinforcement_cost,

        "cost":
            target_cost
            + reinforcement_cost,

        "strategic_score":
            calculate_plan_asset_score(
                players
            ),

        "tactical_score":
            calculate_tactical_plan_score(
                players
            ),

        "minimum_sale_needed":
            max(
                (
                    target_cost
                    + reinforcement_cost
                )
                - int(
                    premium[
                        "balance"
                    ]
                ),
                0,
            ),

        "premium_info":
            premium,
    }


def calculate_combined_score(
    strategic_score: float,
    tactical_score: float,
) -> float:
    """
    Estamos al inicio de temporada.

    Damos más peso a estrategia de largo plazo,
    sin ignorar la urgencia de presentar XI.
    """

    return round(
        (
            strategic_score
            * 0.62
        )
        +
        (
            tactical_score
            * 0.38
        ),
        2,
    )


def compare_strategic_plans(
    snapshot: dict,
) -> dict:

    current = build_current_plan(
        snapshot
    )

    premium = build_premium_plan(
        snapshot
    )

    current[
        "combined_score"
    ] = calculate_combined_score(
        current[
            "strategic_score"
        ],
        current[
            "tactical_score"
        ],
    )

    if not premium.get(
        "available"
    ):

        return {
            "current":
                current,

            "premium":
                premium,

            "recommendation":
                "MANTENER_PLAN_ACTUAL",

            "reason":
                "No hay oportunidad premium activa.",
        }

    premium[
        "combined_score"
    ] = calculate_combined_score(
        premium[
            "strategic_score"
        ],
        premium[
            "tactical_score"
        ],
    )

    difference = (
        premium[
            "combined_score"
        ]
        -
        current[
            "combined_score"
        ]
    )

    # --------------------------------------------------
    # DECISIÓN
    # --------------------------------------------------

    if (
        difference >= 15
        and premium[
            "minimum_sale_needed"
        ]
        <= 2_000_000
    ):

        recommendation = (
            "REESTRUCTURAR_POR_PREMIUM"
        )

        reason = (
            "El plan premium mejora claramente "
            "el valor esperado de temporada y "
            "requiere poca venta adicional."
        )

    elif difference >= 8:

        recommendation = (
            "ESTUDIAR_PLAN_PREMIUM"
        )

        reason = (
            "El plan premium parece superior, "
            "pero el coste de reestructuración "
            "requiere prudencia."
        )

    elif difference <= -8:

        recommendation = (
            "MANTENER_PLAN_ACTUAL"
        )

        reason = (
            "La cobertura táctica del plan actual "
            "compensa el activo premium."
        )

    else:

        recommendation = (
            "DECISIÓN_AJUSTADA"
        )

        reason = (
            "Los dos planes tienen valor esperado "
            "similar. Deben pesar liquidez y "
            "riesgo de la jornada."
        )

    return {
        "current":
            current,

        "premium":
            premium,

        "difference":
            round(
                difference,
                2,
            ),

        "recommendation":
            recommendation,

        "reason":
            reason,
    }