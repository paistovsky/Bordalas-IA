from src.analysis.player_availability import (
    analyze_player_availability,
)


POSITION_NAMES = {
    1: "Portero",
    2: "Defensa",
    3: "Centrocampista",
    4: "Delantero",
}


# ======================================================
# CACHE EN MEMORIA
# ======================================================
#
# Solo vive durante la ejecución actual de Python.
#
# No se guarda en disco.
# No reutiliza datos entre ejecuciones.
# No modifica ninguna decisión.
#
# Evita recalcular varias veces los mismos 555
# jugadores cuando distintos motores solicitan
# Strategic Target Board.
#
# ======================================================


_TARGET_BOARD_CACHE = {}


def clear_strategic_target_cache() -> None:
    """
    Borra la caché del Strategic Target Engine.

    Normalmente no hace falta llamarlo:
    cada ejecución de Python empieza con caché vacía.
    """

    _TARGET_BOARD_CACHE.clear()


def _get_cached_board(
    snapshot: dict,
) -> list[dict] | None:

    key = id(
        snapshot
    )

    cached = (
        _TARGET_BOARD_CACHE.get(
            key
        )
    )

    if cached is None:
        return None

    cached_snapshot = (
        cached[
            "snapshot"
        ]
    )

    # Evita problemas teóricos si Python reutiliza
    # un id() durante un proceso muy largo.
    if cached_snapshot is not snapshot:
        return None

    return cached[
        "board"
    ]


def _set_cached_board(
    snapshot: dict,
    board: list[dict],
) -> None:

    key = id(
        snapshot
    )

    _TARGET_BOARD_CACHE[
        key
    ] = {
        "snapshot":
            snapshot,

        "board":
            board,
    }


# ======================================================
# UTILIDADES
# ======================================================


def calculate_points_per_million(
    player: dict,
) -> float:

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    points = int(
        player.get(
            "pointsLastSeason",
            0,
        )
        or 0
    )

    if price <= 0:
        return 0.0

    return (
        points
        / (price / 1_000_000)
    )


# ======================================================
# SCORE ESTRATÉGICO
# ======================================================


def calculate_absolute_quality_score(
    player: dict,
) -> float:

    points = int(
        player.get(
            "pointsLastSeason",
            0,
        )
        or 0
    )

    if points >= 270:
        return 50

    if points >= 250:
        return 48

    if points >= 230:
        return 44

    if points >= 210:
        return 40

    if points >= 190:
        return 36

    if points >= 170:
        return 31

    if points >= 150:
        return 26

    if points >= 130:
        return 21

    if points >= 110:
        return 16

    if points >= 90:
        return 12

    if points >= 70:
        return 8

    if points >= 40:
        return 4

    return 0


def calculate_strategic_efficiency_score(
    player: dict,
) -> float:

    ppm = (
        calculate_points_per_million(
            player
        )
    )

    if ppm >= 120:
        return 15

    if ppm >= 90:
        return 14

    if ppm >= 70:
        return 13

    if ppm >= 55:
        return 11

    if ppm >= 40:
        return 9

    if ppm >= 30:
        return 7

    if ppm >= 20:
        return 5

    if ppm >= 12:
        return 3

    return 0


def calculate_momentum_score(
    player: dict,
) -> float:

    increment = int(
        player.get(
            "priceIncrement",
            0,
        )
        or 0
    )

    if increment >= 150_000:
        return 10

    if increment >= 100_000:
        return 8

    if increment >= 60_000:
        return 7

    if increment >= 30_000:
        return 5

    if increment > 0:
        return 3

    if increment == 0:
        return 0

    if increment <= -150_000:
        return -8

    if increment <= -80_000:
        return -6

    if increment < 0:
        return -3

    return 0


def calculate_premium_asset_score(
    player: dict,
) -> float:

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    points = int(
        player.get(
            "pointsLastSeason",
            0,
        )
        or 0
    )

    if (
        points >= 240
        and price >= 15_000_000
    ):
        return 20

    if (
        points >= 220
        and price >= 10_000_000
    ):
        return 17

    if (
        points >= 190
        and price >= 7_000_000
    ):
        return 13

    if points >= 180:
        return 9

    if points >= 150:
        return 5

    return 0


def calculate_availability_component(
    player: dict,
) -> tuple[
    float,
    dict,
]:

    availability = (
        analyze_player_availability(
            player
        )
    )

    if not availability[
        "available"
    ]:

        return (
            -100,
            availability,
        )

    if not availability[
        "automatic_lineup"
    ]:

        return (
            -20,
            availability,
        )

    return (
        0,
        availability,
    )


def classify_strategic_target(
    score: float,
    availability: dict,
) -> str:

    if not availability[
        "available"
    ]:
        return "EVITAR"

    if score >= 80:
        return "OBJETIVO ESTRATÉGICO TOP"

    if score >= 70:
        return "OBJETIVO CORE"

    if score >= 60:
        return "PRIORIDAD ALTA"

    if score >= 50:
        return "INTERESANTE"

    if score >= 40:
        return "BUEN ACTIVO"

    if score >= 30:
        return "VIGILAR"

    return "NO PRIORITARIO"


def calculate_strategic_score(
    player: dict,
) -> dict:

    quality = (
        calculate_absolute_quality_score(
            player
        )
    )

    efficiency = (
        calculate_strategic_efficiency_score(
            player
        )
    )

    momentum = (
        calculate_momentum_score(
            player
        )
    )

    premium = (
        calculate_premium_asset_score(
            player
        )
    )

    (
        availability_component,
        availability,
    ) = calculate_availability_component(
        player
    )

    total = (
        quality
        + efficiency
        + momentum
        + premium
        + availability_component
    )

    total = max(
        0,
        min(
            100,
            total,
        ),
    )

    return {
        "strategic_score":
            round(
                total,
                1,
            ),

        "strategic_classification":
            classify_strategic_target(
                total,
                availability,
            ),

        "absolute_quality_score":
            quality,

        "strategic_efficiency_score":
            efficiency,

        "momentum_score":
            momentum,

        "premium_asset_score":
            premium,

        "availability_component":
            availability_component,

        "availability":
            availability,
    }


# ======================================================
# FRANCHISE SCORE
# ======================================================


def calculate_franchise_score(
    player: dict,
) -> dict:

    points = int(
        player.get(
            "pointsLastSeason",
            0,
        )
        or 0
    )

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    availability = (
        analyze_player_availability(
            player
        )
    )

    # ==================================================
    # PRODUCCIÓN ABSOLUTA
    # ==================================================

    if points >= 320:
        points_score = 68

    elif points >= 300:
        points_score = 65

    elif points >= 280:
        points_score = 61

    elif points >= 260:
        points_score = 57

    elif points >= 240:
        points_score = 52

    elif points >= 220:
        points_score = 46

    elif points >= 200:
        points_score = 39

    elif points >= 180:
        points_score = 31

    elif points >= 160:
        points_score = 23

    elif points >= 140:
        points_score = 16

    elif points >= 120:
        points_score = 10

    else:
        points_score = 0

    # ==================================================
    # SEÑAL DE MERCADO
    # ==================================================

    if price >= 30_000_000:
        market_score = 26

    elif price >= 25_000_000:
        market_score = 25

    elif price >= 20_000_000:
        market_score = 23

    elif price >= 15_000_000:
        market_score = 20

    elif price >= 12_000_000:
        market_score = 17

    elif price >= 10_000_000:
        market_score = 14

    elif price >= 8_000_000:
        market_score = 10

    elif price >= 6_000_000:
        market_score = 6

    elif price >= 4_000_000:
        market_score = 3

    else:
        market_score = 0

    # ==================================================
    # CONFIRMACIÓN DE ÉLITE
    # ==================================================

    premium_confirmation = 0

    if (
        points >= 270
        and price >= 18_000_000
    ):

        premium_confirmation = 10

    elif (
        points >= 250
        and price >= 15_000_000
    ):

        premium_confirmation = 9

    elif (
        points >= 230
        and price >= 12_000_000
    ):

        premium_confirmation = 8

    elif (
        points >= 210
        and price >= 10_000_000
    ):

        premium_confirmation = 6

    elif (
        points >= 190
        and price >= 8_000_000
    ):

        premium_confirmation = 4

    # ==================================================
    # BARRERA DE PRODUCCIÓN
    # ==================================================

    production_penalty = 0

    if points < 120:

        production_penalty = -20

    elif points < 150:

        production_penalty = -10

    elif points < 180:

        production_penalty = -5

    # ==================================================
    # DISPONIBILIDAD
    # ==================================================

    availability_penalty = 0

    if not availability[
        "available"
    ]:

        availability_penalty = -100

    elif not availability[
        "automatic_lineup"
    ]:

        availability_penalty = -25

    total = (
        points_score
        + market_score
        + premium_confirmation
        + production_penalty
        + availability_penalty
    )

    total = max(
        0,
        min(
            100,
            total,
        ),
    )

    if not availability[
        "available"
    ]:

        classification = (
            "NO DISPONIBLE"
        )

    elif total >= 90:

        classification = (
            "SUPERSTAR"
        )

    elif total >= 80:

        classification = (
            "FRANCHISE"
        )

    elif total >= 70:

        classification = (
            "PREMIUM"
        )

    elif total >= 55:

        classification = (
            "CORE"
        )

    else:

        classification = (
            "NO FRANCHISE"
        )

    can_trigger_restructure = (
        total >= 70
        and
        availability[
            "available"
        ]
    )

    exceptional_asset = (
        total >= 85
        and
        availability[
            "available"
        ]
    )

    return {
        "franchise_score":
            round(
                total,
                1,
            ),

        "franchise_classification":
            classification,

        "franchise_points_score":
            points_score,

        "franchise_market_score":
            market_score,

        "franchise_confirmation":
            premium_confirmation,

        "franchise_production_penalty":
            production_penalty,

        "franchise_availability_penalty":
            availability_penalty,

        "can_trigger_restructure":
            can_trigger_restructure,

        "exceptional_asset":
            exceptional_asset,
    }


# ======================================================
# SCORE TÁCTICO
# ======================================================


def get_player_positions(
    player: dict,
) -> list[int]:

    positions = [
        player[
            "position"
        ]
    ]

    for alt_position in player.get(
        "altPositions",
        [],
    ):

        if (
            alt_position
            not in positions
        ):

            positions.append(
                alt_position
            )

    return positions


def calculate_squad_need_bonus(
    player: dict,
    shortages: dict[int, int],
) -> float:

    positions = (
        get_player_positions(
            player
        )
    )

    best_bonus = 0

    for position in positions:

        shortage = (
            shortages.get(
                position,
                0,
            )
        )

        if shortage >= 3:

            best_bonus = max(
                best_bonus,
                25,
            )

        elif shortage == 2:

            best_bonus = max(
                best_bonus,
                18,
            )

        elif shortage == 1:

            best_bonus = max(
                best_bonus,
                10,
            )

    return best_bonus


def calculate_affordability_bonus(
    player: dict,
) -> float:

    price = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    if price <= 1_000_000:
        return 6

    if price <= 3_000_000:
        return 5

    if price <= 6_000_000:
        return 3

    if price <= 10_000_000:
        return 1

    return 0


def classify_tactical_target(
    score: float,
    ownership_state: str,
) -> str:

    if ownership_state == "MI_EQUIPO":
        return "YA EN PLANTILLA"

    if ownership_state == "NO_DISPONIBLE":

        if score >= 65:
            return "WATCHLIST ALTA"

        if score >= 45:
            return "WATCHLIST"

        return "ESPERAR"

    if score >= 85:
        return "FICHAR YA"

    if score >= 70:
        return "PRIORIDAD ACTUAL"

    if score >= 55:
        return "INTERESANTE AHORA"

    if score >= 40:
        return "VIGILAR MERCADO"

    return "ESPERAR"


def calculate_tactical_score(
    player: dict,
    strategic_score: float,
    shortages: dict[int, int],
    ownership_state: str,
) -> dict:

    if ownership_state == "MI_EQUIPO":

        return {
            "tactical_score":
                0.0,

            "tactical_classification":
                "YA EN PLANTILLA",

            "strategic_component":
                0.0,

            "squad_need_bonus":
                0,

            "market_bonus":
                0,

            "affordability_bonus":
                0,
        }

    strategic_component = (
        strategic_score
        * 0.70
    )

    need_bonus = (
        calculate_squad_need_bonus(
            player,
            shortages,
        )
    )

    affordability = (
        calculate_affordability_bonus(
            player
        )
    )

    market_bonus = (
        10
        if ownership_state
        == "EN_MERCADO"
        else 0
    )

    total = (
        strategic_component
        + need_bonus
        + affordability
        + market_bonus
    )

    total = max(
        0,
        min(
            100,
            total,
        ),
    )

    return {
        "tactical_score":
            round(
                total,
                1,
            ),

        "tactical_classification":
            classify_tactical_target(
                total,
                ownership_state,
            ),

        "strategic_component":
            round(
                strategic_component,
                1,
            ),

        "squad_need_bonus":
            need_bonus,

        "market_bonus":
            market_bonus,

        "affordability_bonus":
            affordability,
    }


# ======================================================
# ANÁLISIS COMPLETO
# ======================================================


def analyze_strategic_target(
    player: dict,
    shortages: dict[int, int],
    ownership_state: str,
) -> dict:

    strategic = (
        calculate_strategic_score(
            player
        )
    )

    franchise = (
        calculate_franchise_score(
            player
        )
    )

    tactical = (
        calculate_tactical_score(
            player=
                player,

            strategic_score=
                strategic[
                    "strategic_score"
                ],

            shortages=
                shortages,

            ownership_state=
                ownership_state,
        )
    )

    return {
        "id":
            player[
                "id"
            ],

        "name":
            player[
                "name"
            ],

        "team_id":
            player[
                "teamID"
            ],

        "position":
            player[
                "position"
            ],

        "alt_positions":
            player.get(
                "altPositions",
                [],
            ),

        "price":
            player.get(
                "price",
                0,
            )
            or 0,

        "points_last_season":
            player.get(
                "pointsLastSeason",
                0,
            )
            or 0,

        "price_increment":
            player.get(
                "priceIncrement",
                0,
            )
            or 0,

        "points_per_million":
            calculate_points_per_million(
                player
            ),

        "ownership_state":
            ownership_state,

        **strategic,
        **franchise,
        **tactical,
    }


# ======================================================
# CONSTRUIR BOARD SIN CACHE
# ======================================================


def _calculate_full_target_board(
    snapshot: dict,
) -> list[dict]:

    from src.analysis.lineup_engine import (
        build_lineup,
    )

    catalog = (
        snapshot[
            "catalog"
        ][
            "data"
        ][
            "players"
        ]
    )

    lineup = (
        build_lineup(
            snapshot
        )
    )

    shortages = (
        lineup[
            "matchday_shortages"
        ]
    )

    market_ids = {
        sale[
            "player"
        ][
            "id"
        ]

        for sale
        in snapshot[
            "market"
        ].get(
            "sales",
            [],
        )
    }

    my_ids = {
        player[
            "id"
        ]

        for player
        in snapshot[
            "my_team"
        ]
    }

    analyzed = []

    for player in catalog.values():

        player_id = (
            player[
                "id"
            ]
        )

        if player_id in my_ids:

            ownership_state = (
                "MI_EQUIPO"
            )

        elif player_id in market_ids:

            ownership_state = (
                "EN_MERCADO"
            )

        else:

            ownership_state = (
                "NO_DISPONIBLE"
            )

        result = (
            analyze_strategic_target(
                player=
                    player,

                shortages=
                    shortages,

                ownership_state=
                    ownership_state,
            )
        )

        analyzed.append(
            result
        )

    return analyzed


# ======================================================
# TARGET BOARD PÚBLICO
# ======================================================


def build_strategic_target_board(
    snapshot: dict,
    limit: int | None = None,
    sort_by: str = "strategic",
) -> list[dict]:

    # ==================================================
    # CACHE
    # ==================================================

    analyzed = (
        _get_cached_board(
            snapshot
        )
    )

    if analyzed is None:

        analyzed = (
            _calculate_full_target_board(
                snapshot
            )
        )

        _set_cached_board(
            snapshot,
            analyzed,
        )

    # Nunca ordenamos la lista guardada en caché.
    # Trabajamos con una copia superficial.
    result = list(
        analyzed
    )

    # ==================================================
    # ORDEN
    # ==================================================

    if sort_by == "tactical":

        result.sort(
            key=lambda item: (
                item[
                    "tactical_score"
                ],
                item[
                    "strategic_score"
                ],
                item[
                    "franchise_score"
                ],
            ),
            reverse=True,
        )

    elif sort_by == "franchise":

        result.sort(
            key=lambda item: (
                item[
                    "franchise_score"
                ],
                item[
                    "strategic_score"
                ],
                item[
                    "points_last_season"
                ],
            ),
            reverse=True,
        )

    else:

        result.sort(
            key=lambda item: (
                item[
                    "strategic_score"
                ],
                item[
                    "franchise_score"
                ],
                item[
                    "points_last_season"
                ],
            ),
            reverse=True,
        )

    if limit is not None:

        return result[
            :limit
        ]

    return result