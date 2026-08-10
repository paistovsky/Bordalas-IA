from itertools import combinations

from src.analysis.fixture_analyzer import (
    get_team_fixture,
)

from src.analysis.player_availability import (
    analyze_player_availability,
)

from src.intelligence.lineup_intelligence import (
    build_lineup_intelligence,
)


# ============================================================
# FORMACIONES
# ============================================================


FORMATION = {
    1: 1,
    2: 4,
    3: 3,
    4: 3,
}


FORMATIONS = {
    "4-3-3": {
        1: 1,
        2: 4,
        3: 3,
        4: 3,
    },

    "4-4-2": {
        1: 1,
        2: 4,
        3: 4,
        4: 2,
    },
}


# ============================================================
# FIXTURES
# ============================================================


def player_has_current_round_game(
    snapshot: dict,
    player: dict,
) -> bool:

    team_id = (
        player.get(
            "teamID"
        )
    )

    if team_id is None:
        return False

    fixture = (
        get_team_fixture(
            snapshot,
            team_id,
            current_round_only=True,
        )
    )

    return bool(
        fixture
        and fixture.get(
            "has_current_round_game",
            False,
        )
    )


# ============================================================
# POSICIONES
# ============================================================


def get_player_positions(
    player: dict,
) -> list[int]:

    positions = []

    main_position = (
        player.get(
            "position"
        )
    )

    if main_position is not None:

        positions.append(
            main_position
        )

    for position in (
        player.get(
            "altPositions",
            [],
        )
        or []
    ):

        if position not in positions:

            positions.append(
                position
            )

    return positions


# ============================================================
# SCORE BASE
# ============================================================


def calculate_lineup_score(
    snapshot: dict,
    player: dict,
    has_game: bool | None = None,
    availability: dict | None = None,
) -> float:

    score = 0.0

    if availability is None:

        availability = (
            analyze_player_availability(
                player
            )
        )

    if not availability[
        "available"
    ]:

        return -1_000_000.0

    last_points = (
        player.get(
            "pointsLastSeason"
        )
        or 0
    )

    score += (
        last_points
    )

    price = (
        player.get(
            "price",
            0,
        )
        or 0
    )

    score += (
        price
        / 1_000_000
    )

    if has_game is None:

        has_game = (
            player_has_current_round_game(
                snapshot,
                player,
            )
        )

    if has_game:

        score += 1000

    else:

        score -= 1000

    if availability[
        "automatic_lineup"
    ]:

        score += 20

    else:

        score -= 500

    if (
        availability[
            "status"
        ]
        == "ok"
    ):

        score += 10

    return score


# ============================================================
# PREPARAR JUGADORES
# ============================================================


def prepare_players(
    snapshot: dict,
    lineup_intelligence: dict | None = None,
) -> list[dict]:

    if lineup_intelligence is None:

        lineup_intelligence = (
            build_lineup_intelligence(
                snapshot
            )
        )

    intelligence_lookup = (
        lineup_intelligence.get(
            "lookup",
            {},
        )
    )

    players = []

    for player in snapshot[
        "my_team"
    ]:

        player_id = int(
            player[
                "id"
            ]
        )

        availability = (
            analyze_player_availability(
                player
            )
        )

        has_game = (
            player_has_current_round_game(
                snapshot,
                player,
            )
        )

        base_score = (
            calculate_lineup_score(
                snapshot,
                player,
                has_game=has_game,
                availability=availability,
            )
        )

        external = (
            intelligence_lookup.get(
                player_id,
                {}
            )
            or {}
        )

        external_block = bool(
            external.get(
                "external_block",
                False,
            )
        )

        lineup_eligible = bool(
            availability[
                "available"
            ]
            and
            not external_block
        )

        external_adjustment = float(
            external.get(
                "score_adjustment",
                0.0,
            )
            or 0.0
        )

        if lineup_eligible:

            final_score = (
                base_score
                + external_adjustment
            )

        else:

            final_score = (
                -1_000_000.0
            )

        external_status = (
            external.get(
                "status",
                "UNKNOWN",
            )
        )

        if external_block:

            effective_label = (
                "NO CONVOCADO - JORNADA PERFECTA"
            )

        else:

            effective_label = (
                availability[
                    "label"
                ]
            )

        players.append(
            {
                **player,

                "eligible_positions":
                    get_player_positions(
                        player
                    ),

                "has_game":
                    has_game,

                "availability":
                    availability,

                "availability_label":
                    effective_label,

                "automatic_lineup":
                    availability[
                        "automatic_lineup"
                    ],

                "is_available":
                    availability[
                        "available"
                    ],

                "lineup_eligible":
                    lineup_eligible,

                "base_lineup_score":
                    base_score,

                "external_lineup":
                    external,

                "external_lineup_status":
                    external_status,

                "external_lineup_confidence":
                    external.get(
                        "effective_confidence",
                        0,
                    ),

                "external_lineup_adjustment":
                    external_adjustment,

                "external_lineup_block":
                    external_block,

                "lineup_score":
                    final_score,
            }
        )

    return players


# ============================================================
# BUSQUEDA OPTIMIZADA
# ============================================================


def search_best_lineup_for_formation(
    players: list[dict],
    formation: dict[int, int],
    allow_warning_players: bool = False,
) -> dict:

    usable_players = []

    for player in players:

        if not player[
            "lineup_eligible"
        ]:

            continue

        if (
            not allow_warning_players
            and
            not player[
                "automatic_lineup"
            ]
        ):

            continue

        usable_players.append(
            player
        )

    position_candidates = {}

    for position in formation:

        candidates = [
            player

            for player in usable_players

            if position
            in player[
                "eligible_positions"
            ]
        ]

        candidates.sort(
            key=lambda player:
                player[
                    "lineup_score"
                ],
            reverse=True,
        )

        position_candidates[
            position
        ] = candidates

    position_order = sorted(
        formation.keys(),
        key=lambda position: (
            len(
                position_candidates[
                    position
                ]
            ),
            formation[
                position
            ],
        ),
    )

    best_lineup = []

    best_score = float(
        "-inf"
    )

    best_filled = -1

    def search_position(
        position_index: int,
        used_ids: set[int],
        selected: list[dict],
        score: float,
    ) -> None:

        nonlocal best_lineup
        nonlocal best_score
        nonlocal best_filled

        if (
            position_index
            >= len(
                position_order
            )
        ):

            filled = len(
                selected
            )

            if (
                filled > best_filled

                or (
                    filled
                    == best_filled

                    and
                    score
                    > best_score
                )
            ):

                best_filled = (
                    filled
                )

                best_score = (
                    score
                )

                best_lineup = list(
                    selected
                )

            return

        position = (
            position_order[
                position_index
            ]
        )

        required = (
            formation[
                position
            ]
        )

        candidates = [
            player

            for player in (
                position_candidates[
                    position
                ]
            )

            if player[
                "id"
            ]
            not in used_ids
        ]

        max_take = min(
            required,
            len(
                candidates
            ),
        )

        for take_count in range(
            max_take,
            -1,
            -1,
        ):

            for combo in combinations(
                candidates,
                take_count,
            ):

                combo_ids = {
                    player[
                        "id"
                    ]

                    for player in combo
                }

                combo_score = sum(
                    player[
                        "lineup_score"
                    ]

                    for player in combo
                )

                combo_selected = [
                    {
                        **player,

                        "lineup_position":
                            position,
                    }

                    for player in combo
                ]

                search_position(
                    position_index + 1,

                    used_ids
                    | combo_ids,

                    selected
                    + combo_selected,

                    score
                    + combo_score,
                )

    search_position(
        position_index=0,
        used_ids=set(),
        selected=[],
        score=0.0,
    )

    if best_filled < 0:

        best_filled = 0

        best_score = 0.0

        best_lineup = []

    return {
        "selected":
            best_lineup,

        "score":
            best_score,

        "filled":
            best_filled,

        "complete":
            best_filled == 11,
    }


# ============================================================
# FORMACION
# ============================================================


def evaluate_formation(
    players: list[dict],
    formation_name: str,
    formation: dict[int, int],
) -> dict:

    normal = (
        search_best_lineup_for_formation(
            players,
            formation,
            allow_warning_players=False,
        )
    )

    if normal[
        "complete"
    ]:

        return {
            **normal,

            "formation_name":
                formation_name,

            "formation":
                formation,

            "used_warning_players":
                False,
        }

    emergency = (
        search_best_lineup_for_formation(
            players,
            formation,
            allow_warning_players=True,
        )
    )

    return {
        **emergency,

        "formation_name":
            formation_name,

        "formation":
            formation,

        "used_warning_players":
            True,
    }


# ============================================================
# BUILD
# ============================================================


def build_lineup(
    snapshot: dict,
    lineup_intelligence: dict | None = None,
) -> dict:

    if lineup_intelligence is None:

        lineup_intelligence = (
            build_lineup_intelligence(
                snapshot
            )
        )

    players = (
        prepare_players(
            snapshot=
                snapshot,

            lineup_intelligence=
                lineup_intelligence,
        )
    )

    formation_results = []

    for (
        formation_name,
        formation,
    ) in FORMATIONS.items():

        result = (
            evaluate_formation(
                players,
                formation_name,
                formation,
            )
        )

        formation_results.append(
            result
        )

    formation_results.sort(
        key=lambda result: (
            result[
                "filled"
            ],
            result[
                "score"
            ],
        ),
        reverse=True,
    )

    best = (
        formation_results[
            0
        ]

        if formation_results

        else {
            "selected": [],
            "score": 0.0,
            "filled": 0,
            "complete": False,
            "formation_name": "4-3-3",
            "formation": FORMATION,
            "used_warning_players": False,
        }
    )

    best_lineup = (
        best[
            "selected"
        ]
    )

    selected_formation = (
        best[
            "formation"
        ]
    )

    best_lineup.sort(
        key=lambda player: (
            player.get(
                "lineup_position",
                99,
            ),

            -player.get(
                "lineup_score",
                0,
            ),
        )
    )

    blocked_players = [
        player

        for player in players

        if (
            not player[
                "is_available"
            ]

            or
            player[
                "external_lineup_block"
            ]
        )
    ]

    unavailable_selected = [
        player

        for player in best_lineup

        if (
            not player[
                "has_game"
            ]

            or
            not player[
                "automatic_lineup"
            ]
        )
    ]

    playable_count = sum(
        1

        for player in best_lineup

        if (
            player[
                "has_game"
            ]

            and
            player[
                "automatic_lineup"
            ]
        )
    )

    matchday_shortages = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
    }

    for (
        position_id,
        required,
    ) in selected_formation.items():

        playable_in_position = sum(
            1

            for player in best_lineup

            if (
                player[
                    "lineup_position"
                ]
                == position_id

                and
                player[
                    "has_game"
                ]

                and
                player[
                    "automatic_lineup"
                ]
            )
        )

        matchday_shortages[
            position_id
        ] = max(
            required
            - playable_in_position,
            0,
        )

    external_risk_selected = [
        player

        for player in best_lineup

        if player.get(
            "external_lineup_status"
        )
        in {
            "DUDA",
            "SUPLENTE",
        }
    ]

    probable_starters = sum(
        1

        for player in best_lineup

        if player.get(
            "external_lineup_status"
        )
        in {
            "TITULAR",
            "PROBABLE",
        }
    )

    return {
        "formation":
            selected_formation,

        "formation_name":
            best[
                "formation_name"
            ],

        "selected":
            best_lineup,

        "total_selected":
            len(
                best_lineup
            ),

        "complete":
            len(
                best_lineup
            )
            == 11,

        "playable_count":
            playable_count,

        "unavailable_count":
            len(
                unavailable_selected
            ),

        "unavailable_selected":
            unavailable_selected,

        "blocked_players":
            blocked_players,

        "matchday_shortages":
            matchday_shortages,

        "lineup_score":
            best[
                "score"
            ],

        "used_warning_players":
            best[
                "used_warning_players"
            ],

        "formation_candidates":
            formation_results,

        "lineup_intelligence":
            lineup_intelligence,

        "external_source_state":
            lineup_intelligence.get(
                "source_state",
                "NOT_CONNECTED",
            ),

        "external_updated_at":
            lineup_intelligence.get(
                "updated_at"
            ),

        "external_matched_players":
            lineup_intelligence.get(
                "matched_players",
                0,
            ),

        "external_risk_selected":
            external_risk_selected,

        "probable_starter_count":
            probable_starters,
    }