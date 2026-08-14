from itertools import combinations

from src.analysis.player_availability import (
    analyze_player_availability,
)

from src.analysis.home_away_intelligence import (
    build_home_away_context,
)

from src.intelligence.penalty_intelligence import (
    get_penalty_context,
)

from src.analysis.position_policy import (
    POSITION_POLICY,
    assert_lineup_position_integrity,
    get_effective_positions,
)

from src.intelligence.lineup_intelligence import (
    build_lineup_intelligence,
)

from src.analysis.calendar_state import (
    build_calendar_state,
)

from src.intelligence.multisource_starter_v1124 import (
    build_multisource_board,
)


# ============================================================
# V11.3 STARTER INTELLIGENCE LIVE
# ============================================================

_MULTISOURCE_STARTER_CACHE = {}


def build_starter_intelligence_for_snapshot(
    snapshot: dict,
) -> dict | None:

    cache_key = id(snapshot)

    cached = _MULTISOURCE_STARTER_CACHE.get(
        cache_key
    )

    if cached is not None:
        return cached

    try:
        calendar = build_calendar_state(
            snapshot
        )

        matchday = int(
            calendar.get(
                "target_matchday"
            )
            or 1
        )

        board = build_multisource_board(
            snapshot=snapshot,
            matchday=matchday,
            seconds_to_deadline=calendar.get(
                "seconds_to_deadline"
            ),
        )

    except Exception as error:
        board = {
            "version": "V11.3_FALLBACK",
            "error": (
                f"{type(error).__name__}: "
                f"{error}"
            ),
            "players": [],
        }

    _MULTISOURCE_STARTER_CACHE[
        cache_key
    ] = board

    return board


def starter_lookup_from_board(
    board: dict | None,
) -> dict[int, dict]:

    if not board:
        return {}

    return {
        int(item["player_id"]): item
        for item in board.get(
            "players",
            [],
        )
        if item.get("player_id") is not None
    }


# ============================================================
# FORMACIONES
# ============================================================


FORMATION = {
    1: 1,
    2: 4,
    3: 3,
    4: 3,
}


# Formaciones que Pepe evalua automaticamente.
# No existe bonus por formacion: gana el XI legal completo
# con mejor lineup_score.
FORMATIONS = {
    "3-4-3": {1: 1, 2: 3, 3: 4, 4: 3},
    "3-5-2": {1: 1, 2: 3, 3: 5, 4: 2},
    "4-3-3": {1: 1, 2: 4, 3: 3, 4: 3},
    "4-4-2": {1: 1, 2: 4, 3: 4, 4: 2},
    "4-5-1": {1: 1, 2: 4, 3: 5, 4: 1},
    "5-3-2": {1: 1, 2: 5, 3: 3, 4: 2},
    "5-4-1": {1: 1, 2: 5, 3: 4, 4: 1},
}


# ============================================================
# JORNADA
# ============================================================
#
# La pertenencia a la jornada la gobierna el calendario dinamico.
# No usamos team.nextGames para decidir si un jugador puede entrar
# en el XI. Un partido aplazado sigue perteneciendo a su jornada
# original y usa el XI fijado antes del primer kickoff.
# ============================================================


# ============================================================
# COMPATIBILIDAD CON MODULOS ANTIGUOS
# ============================================================


def player_has_current_round_game(
    snapshot: dict,
    player: dict,
) -> bool:
    """
    Shim de compatibilidad.

    Algunos motores antiguos (por ejemplo, el de impacto de
    reestructuración/Franchise) todavía importan esta función.

    En la arquitectura V3 ya NO consultamos team.nextGames para
    decidir si un jugador pertenece a la jornada. El calendario
    dinámico gobierna la jornada completa y un aplazamiento no
    elimina al jugador de ella.

    Por tanto, para esos consumidores antiguos, "tener partido
    en la jornada" significa simplemente "pertenecer a la
    plantilla/competición de la jornada objetivo".

    `snapshot` se conserva en la firma para no romper imports y
    llamadas existentes.
    """

    del snapshot

    return bool(
        player
        and
        player.get(
            "teamID"
        )
        is not None
    )


# ============================================================
# POSICIONES
# ============================================================


def get_player_positions(
    player: dict,
) -> list[int]:
    """
    Compatibilidad publica con consumidores existentes.

    Position Policy V1:
    Pepe usa exclusivamente la posicion principal de Biwenger.
    altPositions se conserva como metadata, pero no permite ocupar
    otro slot del XI ni cubrir necesidades tacticas.
    """

    return get_effective_positions(
        player
    )


# ============================================================
# SCORE BASE
# ============================================================


def calculate_lineup_score(
    player: dict,
    availability: dict | None = None,
) -> float:
    """
    Score del XI de la JORNADA COMPLETA.

    NO se premia ni penaliza a un jugador porque su partido
    aparezca o no en team.nextGames.

    Esa lista puede omitir partidos aplazados de la jornada
    actual, por lo que usarla para +1000/-1000 distorsionaba
    gravemente el XI.

    Factores actuales:
    - puntos temporada anterior;
    - valor de mercado como proxy suave de calidad;
    - disponibilidad real;
    - status;
    - ajuste externo de Jornada Perfecta (se suma despues).

    Franchise/Strategic Score se integraran como capa adicional,
    pero no son necesarios para corregir el bug temporal.
    """

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

    score += float(
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
        float(
            price
        )
        / 1_000_000
    )

    # Automatic lineup representa si el motor de disponibilidad
    # considera seguro alinearlo. No lo bloqueamos aqui porque
    # search_best_lineup_for_formation ya tiene modo normal y
    # modo emergencia, pero sí penalizamos si entra como warning.
    if availability[
        "automatic_lineup"
    ]:

        score += 20.0

    else:

        score -= 500.0

    if (
        availability[
            "status"
        ]
        == "ok"
    ):

        score += 10.0

    return score


# ============================================================
# PREPARAR JUGADORES
# ============================================================


def prepare_players(
    snapshot: dict,
    lineup_intelligence: dict | None = None,
    starter_intelligence: dict | None = None,
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

    if starter_intelligence is None:
        starter_intelligence = (
            build_starter_intelligence_for_snapshot(
                snapshot
            )
        )

    starter_lookup = (
        starter_lookup_from_board(
            starter_intelligence
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

        base_score = (
            calculate_lineup_score(
                player=
                    player,

                availability=
                    availability,
            )
        )

        external = (
            intelligence_lookup.get(
                player_id,
                {},
            )
            or {}
        )

        starter = (
            starter_lookup.get(
                player_id,
                {},
            )
            or {}
        )

        starter_coverage = int(
            starter.get(
                "source_coverage"
            )
            or 0
        )

        starter_probability = (
            float(
                starter.get(
                    "starter_probability"
                )
            )
            if (
                starter_coverage > 0
                and
                starter.get(
                    "starter_probability"
                )
                is not None
            )
            else None
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

        home_away_context = (
            build_home_away_context(
                snapshot,
                player,
            )
        )

        penalty_context = (
            get_penalty_context(
                snapshot,
                player,
            )
        )

        home_away_adjustment = float(
            home_away_context.get(
                "bonus",
                0.0,
            )
            or 0.0
        )

        penalty_adjustment = float(
            penalty_context.get(
                "bonus",
                0.0,
            )
            or 0.0
        )

        if lineup_eligible:

            if starter_probability is not None:

                # ====================================================
                # V11.3.1 CONSENSUS CLASS RANKING
                # ====================================================
                #
                # Confirmed multi-source STARTER beats:
                # STARTER_LEAN > UNCERTAIN > BENCH_LEAN > BENCH.
                #
                # Probability is only a tie-breaker INSIDE the class.
                # ====================================================

                starter_consensus = str(
                    starter.get(
                        "consensus"
                    )
                    or "UNCERTAIN"
                ).upper()

                starter_tier = int(
                    starter.get(
                        "ranking_tier"
                    )
                    or {
                        "STARTER": 5,
                        "STARTER_LEAN": 4,
                        "UNCERTAIN": 3,
                        "BENCH_LEAN": 2,
                        "BENCH": 1,
                    }.get(
                        starter_consensus,
                        3,
                    )
                )

                # ====================================================
                # V11.3.3 VOTE QUALITY TIEBREAK
                # ====================================================
                #
                # Inside the SAME consensus class:
                # STARTER votes are positive evidence.
                # BENCH votes are negative evidence.
                #
                # Example:
                # 1S/2U/0B > 1S/1U/1B > 0S/2U/1B
                # ====================================================

                starter_votes = int(
                    starter.get(
                        "starter_votes"
                    )
                    or 0
                )

                bench_votes = int(
                    starter.get(
                        "bench_votes"
                    )
                    or 0
                )

                vote_quality = (
                    starter_votes
                    * 5_000.0
                    -
                    bench_votes
                    * 5_000.0
                )

                final_score = (
                    starter_tier
                    * 100_000.0

                    + vote_quality

                    + starter_coverage
                    * 3_000.0

                    + starter_probability
                    * 100.0

                    + base_score

                    + home_away_adjustment

                    + penalty_adjustment
                )

            else:

                # Unknown external status is safer than a known bench,
                # but worse than a resolved UNCERTAIN.
                final_score = (
                    250_000.0
                    + base_score
                    + external_adjustment
                    + home_away_adjustment
                    + penalty_adjustment
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

                # ------------------------------------------------
                # JORNADA FANTASY
                # ------------------------------------------------
                # Todos los jugadores disponibles de la plantilla
                # pertenecen al target matchday. Un aplazamiento no
                # los saca de la jornada.

                "counts_for_round":
                    True,

                "round_scoring_eligible":
                    lineup_eligible,

                # ------------------------------------------------
                # DISPONIBILIDAD
                # ------------------------------------------------

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

                # ------------------------------------------------
                # SCORE
                # ------------------------------------------------

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

                "starter_intelligence":
                    starter,

                "starter_probability":
                    starter_probability,

                "starter_expected_minutes":
                    starter.get(
                        "expected_minutes"
                    ),

                "starter_source_coverage":
                    starter_coverage,

                "starter_consensus":
                    starter.get(
                        "consensus"
                    ),

                "starter_confidence":
                    starter.get(
                        "confidence"
                    ),

                "starter_sources":
                    starter.get(
                        "sources",
                        {},
                    ),

                "home_away_context":
                    home_away_context,

                "home_away_adjustment":
                    home_away_adjustment,

                "penalty_context":
                    penalty_context,

                "penalty_adjustment":
                    penalty_adjustment,

                "lineup_score_components":
                    {
                        "base":
                            base_score,

                        "jornada_perfecta_legacy":
                            external_adjustment,

                        "starter_probability":
                            starter_probability,

                        "starter_source_coverage":
                            starter_coverage,

                        "home_away":
                            home_away_adjustment,

                        "penalty":
                            penalty_adjustment,
                    },

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

    starter_intelligence = (
        build_starter_intelligence_for_snapshot(
            snapshot
        )
    )

    players = (
        prepare_players(
            snapshot=
                snapshot,

            lineup_intelligence=
                lineup_intelligence,

            starter_intelligence=
                starter_intelligence,
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

    # Hard Safety: ningun jugador puede salir de su posicion.
    assert_lineup_position_integrity(
        best_lineup
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
                "automatic_lineup"
            ]
        )
    ]

    # ========================================================
    # PLAYABLE COUNT
    # ========================================================
    #
    # Ahora "playable" significa:
    # - pertenece al XI;
    # - esta disponible;
    # - el motor considera seguro alinearlo.
    #
    # NO depende de que team.nextGames contenga el partido.
    # ========================================================

    playable_count = sum(
        1

        for player in best_lineup

        if (
            player[
                "lineup_eligible"
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
                    "lineup_eligible"
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

        if (
            (
                player.get(
                    "starter_probability"
                )
                is not None
                and
                str(
                    player.get(
                        "starter_consensus"
                    )
                    or ""
                ).upper()
                in {
                    "UNCERTAIN",
                    "BENCH_LEAN",
                    "BENCH",
                }
            )
            or
            (
                player.get(
                    "starter_probability"
                )
                is None
                and
                player.get(
                    "external_lineup_status"
                )
                in {
                    "DUDA",
                    "SUPLENTE",
                }
            )
        )
    ]

    probable_starters = sum(
        1

        for player in best_lineup

        if (
            (
                player.get(
                    "starter_probability"
                )
                is not None
                and
                str(
                    player.get(
                        "starter_consensus"
                    )
                    or ""
                ).upper()
                in {
                    "STARTER",
                    "STARTER_LEAN",
                }
            )
            or
            (
                player.get(
                    "starter_probability"
                )
                is None
                and
                player.get(
                    "external_lineup_status"
                )
                in {
                    "TITULAR",
                    "PROBABLE",
                }
            )
        )
    )


    return {
        "position_policy":
            POSITION_POLICY,

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

        "starter_intelligence":
            starter_intelligence,

        "starter_intelligence_version":
            starter_intelligence.get(
                "version"
            )
            if starter_intelligence
            else None,

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
