from itertools import combinations

from src.analysis.bid_restructuring_engine import (
    build_bid_restructuring_plan,
)

from src.analysis.lineup_engine import (
    build_lineup,
    player_has_current_round_game,
)


# ======================================================
# POSICIONES
# ======================================================


POSITION_NAMES = {
    1: "Portero",
    2: "Defensa",
    3: "Centrocampista",
    4: "Delantero",
}


# ======================================================
# NORMALIZACIÓN DE JUGADORES
# ======================================================


def normalize_player(
    player: dict,
) -> dict:
    """
    Los jugadores pueden venir de dos sitios:

    1. Snapshot Biwenger:
       teamID
       altPositions

    2. Strategic Target Engine:
       team_id
       alt_positions

    Este motor trabaja con ambos formatos.
    """

    normalized = dict(
        player
    )

    if (
        "teamID"
        not in normalized
    ):

        normalized[
            "teamID"
        ] = normalized.get(
            "team_id"
        )

    if (
        "altPositions"
        not in normalized
    ):

        normalized[
            "altPositions"
        ] = normalized.get(
            "alt_positions",
            [],
        )

    return normalized


def get_player_positions(
    player: dict,
) -> list[int]:

    player = (
        normalize_player(
            player
        )
    )

    position = player.get(
        "position"
    )

    positions = []

    if position is not None:

        positions.append(
            int(
                position
            )
        )

    for alt_position in player.get(
        "altPositions",
        [],
    ):

        alt_position = int(
            alt_position
        )

        if (
            alt_position
            not in positions
        ):

            positions.append(
                alt_position
            )

    return positions


# ======================================================
# DISPONIBILIDAD PARA ESTA JORNADA
# ======================================================


def can_help_current_round(
    snapshot: dict,
    player: dict,
) -> bool:

    player = (
        normalize_player(
            player
        )
    )

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

    # Protección adicional:
    # si por cualquier motivo no tenemos teamID
    # no inventamos el fixture.
    if player.get(
        "teamID"
    ) is None:

        return False

    return (
        player_has_current_round_game(
            snapshot,
            player,
        )
    )


# ======================================================
# COBERTURA DE HUECOS
# ======================================================


def calculate_best_shortage_coverage(
    snapshot: dict,
    bids: list[dict],
    shortages: dict[int, int],
) -> dict:
    """
    Calcula cuántos huecos actuales del XI podrían
    cubrir las pujas que mantenemos.

    Un jugador con posiciones alternativas puede
    cubrir distintos slots, por lo que usamos
    backtracking.

    IMPORTANTE:
    esto mide cobertura POTENCIAL.

    No significa que vayamos a ganar esas pujas.
    """

    usable = []

    for raw_player in bids:

        player = (
            normalize_player(
                raw_player
            )
        )

        if not can_help_current_round(
            snapshot,
            player,
        ):

            continue

        positions = (
            get_player_positions(
                player
            )
        )

        relevant_positions = [
            position

            for position in positions

            if shortages.get(
                position,
                0,
            ) > 0
        ]

        if not relevant_positions:
            continue

        usable.append(
            {
                **raw_player,

                "coverage_positions":
                    relevant_positions,
            }
        )

    best_covered = 0
    best_assignments = []

    initial_remaining = {
        position:
            int(
                shortages.get(
                    position,
                    0,
                )
                or 0
            )

        for position in (
            1,
            2,
            3,
            4,
        )
    }

    def search(
        index: int,
        remaining: dict[int, int],
        assignments: list[dict],
        covered: int,
    ) -> None:

        nonlocal best_covered
        nonlocal best_assignments

        if index >= len(
            usable
        ):

            if covered > best_covered:

                best_covered = covered

                best_assignments = list(
                    assignments
                )

            return

        player = usable[
            index
        ]

        # ==============================================
        # OPCIÓN 1:
        # no utilizar esta puja para cubrir un hueco
        # ==============================================

        search(
            index + 1,
            remaining,
            assignments,
            covered,
        )

        # ==============================================
        # OPCIÓN 2:
        # asignar el jugador a un hueco compatible
        # ==============================================

        for position in player[
            "coverage_positions"
        ]:

            if remaining.get(
                position,
                0,
            ) <= 0:

                continue

            next_remaining = dict(
                remaining
            )

            next_remaining[
                position
            ] -= 1

            assignments.append(
                {
                    "player_id":
                        player[
                            "id"
                        ],

                    "player_name":
                        player[
                            "name"
                        ],

                    "position":
                        position,
                }
            )

            search(
                index + 1,
                next_remaining,
                assignments,
                covered + 1,
            )

            assignments.pop()

    search(
        index=0,
        remaining=initial_remaining,
        assignments=[],
        covered=0,
    )

    remaining_shortages = dict(
        initial_remaining
    )

    for assignment in best_assignments:

        position = (
            assignment[
                "position"
            ]
        )

        remaining_shortages[
            position
        ] = max(
            remaining_shortages[
                position
            ] - 1,
            0,
        )

    return {
        "covered":
            best_covered,

        "assignments":
            best_assignments,

        "remaining_shortages":
            remaining_shortages,

        "usable_bid_count":
            len(
                usable
            ),
    }


# ======================================================
# IMPACTO DE CANCELAR PUJAS
# ======================================================


def evaluate_roster_impact(
    snapshot: dict,
    all_bids: list[dict],
    cancelled_players: list[dict],
    current_shortages: dict[int, int],
    current_playable_count: int,
    baseline_coverage: dict,
) -> dict:

    cancelled_ids = {
        player[
            "id"
        ]

        for player
        in cancelled_players
    }

    kept_bids = [
        player

        for player
        in all_bids

        if player[
            "id"
        ]
        not in cancelled_ids
    ]

    coverage = (
        calculate_best_shortage_coverage(
            snapshot=
                snapshot,

            bids=
                kept_bids,

            shortages=
                current_shortages,
        )
    )

    coverage_loss = max(
        baseline_coverage[
            "covered"
        ]
        - coverage[
            "covered"
        ],
        0,
    )

    projected_playable = min(
        current_playable_count
        + coverage[
            "covered"
        ],
        11,
    )

    remaining_total = sum(
        coverage[
            "remaining_shortages"
        ].values()
    )

    # ==================================================
    # DAÑO DE PLANTILLA
    # ==================================================
    #
    # Perder cobertura efectiva del XI pesa bastante.
    #
    # Sin embargo, no la hacemos infinita porque
    # estamos precisamente modelando escenarios en los
    # que quedan varios mercados por delante.
    # ==================================================

    roster_damage = (
        coverage_loss
        * 35.0
    )

    roster_damage += (
        remaining_total
        * 4.0
    )

    return {
        "kept_bids":
            kept_bids,

        "coverage":
            coverage,

        "coverage_loss":
            coverage_loss,

        "projected_playable_count":
            projected_playable,

        "remaining_total":
            remaining_total,

        "roster_damage":
            round(
                roster_damage,
                2,
            ),
    }


# ======================================================
# COMBINACIÓN ECONÓMICA + DEPORTIVA
# ======================================================


def evaluate_cancellation_combination(
    snapshot: dict,
    combo: tuple[dict, ...],
    all_bids: list[dict],
    required_unlock: int,
    current_shortages: dict[int, int],
    current_playable_count: int,
    baseline_coverage: dict,
) -> dict:

    unlocked = sum(
        int(
            player[
                "bid_amount"
            ]
        )

        for player in combo
    )

    excess = max(
        unlocked
        - required_unlock,
        0,
    )

    # ==================================================
    # DAÑO INDIVIDUAL
    # ==================================================

    keep_damage = sum(
        float(
            player[
                "keep_score"
            ]
        )

        for player in combo
    )

    # Fricción por cancelar muchas operaciones.
    operation_damage = (
        max(
            len(combo) - 1,
            0,
        )
        * 5.0
    )

    # Penalización por liberar mucho más capital
    # del necesario.
    excess_damage = (
        excess
        / 1_000_000
    ) * 2.0

    # ==================================================
    # IMPACTO REAL SOBRE COBERTURA
    # ==================================================

    roster = (
        evaluate_roster_impact(
            snapshot=
                snapshot,

            all_bids=
                all_bids,

            cancelled_players=
                list(
                    combo
                ),

            current_shortages=
                current_shortages,

            current_playable_count=
                current_playable_count,

            baseline_coverage=
                baseline_coverage,
        )
    )

    total_score = (
        keep_damage
        + operation_damage
        + excess_damage
        + roster[
            "roster_damage"
        ]
    )

    return {
        "players":
            list(
                combo
            ),

        "unlocked":
            unlocked,

        "excess":
            excess,

        "keep_damage":
            round(
                keep_damage,
                2,
            ),

        "operation_damage":
            round(
                operation_damage,
                2,
            ),

        "excess_damage":
            round(
                excess_damage,
                2,
            ),

        "roster_damage":
            roster[
                "roster_damage"
            ],

        "coverage_loss":
            roster[
                "coverage_loss"
            ],

        "projected_playable_count":
            roster[
                "projected_playable_count"
            ],

        "remaining_shortages":
            roster[
                "coverage"
            ][
                "remaining_shortages"
            ],

        "coverage_assignments":
            roster[
                "coverage"
            ][
                "assignments"
            ],

        "total_score":
            round(
                total_score,
                2,
            ),
    }


# ======================================================
# CLASIFICACIÓN DEL IMPACTO
# ======================================================


def classify_restructuring_impact(
    best_combination: dict | None,
) -> tuple[
    str,
    str,
]:

    if best_combination is None:

        return (
            "SIN_COMBINACION",
            (
                "No existe una combinación de pujas capaz "
                "de liberar la capacidad necesaria."
            ),
        )

    coverage_loss = int(
        best_combination[
            "coverage_loss"
        ]
    )

    projected_playable = int(
        best_combination[
            "projected_playable_count"
        ]
    )

    if coverage_loss == 0:

        return (
            "REESTRUCTURACION_DEPORTIVAMENTE_SEGURA",
            (
                "Existe una combinación que libera el capital "
                "necesario sin reducir la cobertura potencial "
                "de los huecos actuales del XI."
            ),
        )

    if projected_playable >= 10:

        return (
            "REESTRUCTURACION_ASUMIBLE",
            (
                "La reestructuración reduce parcialmente la "
                "cobertura potencial del XI, pero mantiene una "
                "base deportiva razonable para reconstruir "
                "durante los próximos mercados."
            ),
        )

    return (
        "REESTRUCTURACION_DEPORTIVAMENTE_AGRESIVA",
        (
            "La combinación necesaria deteriora de forma "
            "importante la cobertura potencial del XI y "
            "exigirá reconstrucción posterior."
        ),
    )


# ======================================================
# PLAN PRINCIPAL
# ======================================================


def build_restructuring_roster_impact_plan(
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
                    "No existe reestructuración activa.",
                ),
        }

    economy = (
        restructuring[
            "economy"
        ]
    )

    required_unlock = int(
        economy[
            "required_unlock"
        ]
    )

    active_bids = (
        restructuring[
            "active_bids"
        ]
    )

    # ==================================================
    # XI ACTUAL
    # ==================================================

    lineup = (
        build_lineup(
            snapshot
        )
    )

    current_shortages = {
        int(
            position
        ):
            int(
                value
            )

        for position, value
        in lineup[
            "matchday_shortages"
        ].items()
    }

    current_playable_count = int(
        lineup[
            "playable_count"
        ]
    )

    # ==================================================
    # COBERTURA SI MANTENEMOS TODAS LAS PUJAS
    # ==================================================

    baseline_coverage = (
        calculate_best_shortage_coverage(
            snapshot=
                snapshot,

            bids=
                active_bids,

            shortages=
                current_shortages,
        )
    )

    # ==================================================
    # YA TENEMOS CAPACIDAD SUFICIENTE
    # ==================================================

    if required_unlock <= 0:

        return {
            "active":
                True,

            "target":
                restructuring[
                    "target"
                ],

            "required_unlock":
                0,

            "current_playable_count":
                current_playable_count,

            "current_shortages":
                current_shortages,

            "baseline_coverage":
                baseline_coverage,

            "alternatives":
                [],

            "best_combination":
                None,

            "recommendation":
                "NO_CANCELAR",

            "reason":
                (
                    "La capacidad de puja actual "
                    "ya es suficiente."
                ),

            "restructuring":
                restructuring,
        }

    # ==================================================
    # TODAS LAS COMBINACIONES FINANCIABLES
    # ==================================================

    alternatives = []

    for size in range(
        1,
        len(active_bids) + 1,
    ):

        for combo in combinations(
            active_bids,
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

            result = (
                evaluate_cancellation_combination(
                    snapshot=
                        snapshot,

                    combo=
                        combo,

                    all_bids=
                        active_bids,

                    required_unlock=
                        required_unlock,

                    current_shortages=
                        current_shortages,

                    current_playable_count=
                        current_playable_count,

                    baseline_coverage=
                        baseline_coverage,
                )
            )

            alternatives.append(
                result
            )

    # ==================================================
    # MEJOR ALTERNATIVA
    # ==================================================

    alternatives.sort(
        key=lambda item: (
            item[
                "total_score"
            ],
            item[
                "coverage_loss"
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

    best_combination = (
        alternatives[0]
        if alternatives
        else None
    )

    (
        recommendation,
        reason,
    ) = classify_restructuring_impact(
        best_combination
    )

    return {
        "active":
            True,

        "target":
            restructuring[
                "target"
            ],

        "required_unlock":
            required_unlock,

        "current_playable_count":
            current_playable_count,

        "current_shortages":
            current_shortages,

        "baseline_coverage":
            baseline_coverage,

        "alternatives":
            alternatives,

        "best_combination":
            best_combination,

        "recommendation":
            recommendation,

        "reason":
            reason,

        "restructuring":
            restructuring,
    }