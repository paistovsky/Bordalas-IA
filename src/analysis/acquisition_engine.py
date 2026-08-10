from pathlib import Path

from src.analysis.price_history_engine import (
    get_snapshot_files,
    load_raw_snapshot,
    parse_snapshot_timestamp,
)


# ======================================================
# CACHE
# ======================================================


_ACQUISITION_CACHE = {}


def clear_acquisition_cache() -> None:

    _ACQUISITION_CACHE.clear()


# ======================================================
# UTILIDADES
# ======================================================


def get_my_team_lookup(
    snapshot: dict,
) -> dict[int, dict]:

    return {
        int(
            player["id"]
        ):
            player

        for player in snapshot.get(
            "my_team",
            [],
        )
    }


def extract_requested_player_ids(
    offer: dict,
) -> list[int]:

    result = []

    requested = offer.get(
        "requestedPlayers",
        [],
    )

    if isinstance(
        requested,
        list,
    ):

        for item in requested:

            if isinstance(
                item,
                int,
            ):

                result.append(
                    int(item)
                )

            elif isinstance(
                item,
                dict,
            ):

                player_id = item.get(
                    "id"
                )

                if player_id is not None:

                    result.append(
                        int(player_id)
                    )

    return result


def detect_my_user_id(
    snapshot: dict,
) -> int | None:

    league = snapshot.get(
        "league",
        {},
    )

    if isinstance(
        league,
        dict,
    ):

        user = league.get(
            "user",
            {},
        )

        if isinstance(
            user,
            dict,
        ):

            user_id = user.get(
                "id"
            )

            if user_id is not None:

                return int(
                    user_id
                )

    # Fallback:
    # nuestras pujas salientes contienen nuestro
    # user ID en "from".
    market = snapshot.get(
        "market",
        {},
    )

    for offer in market.get(
        "offers",
        [],
    ):

        from_user = offer.get(
            "from"
        )

        if not isinstance(
            from_user,
            dict,
        ):
            continue

        user_id = from_user.get(
            "id"
        )

        if user_id is not None:

            return int(
                user_id
            )

    return None


def is_our_purchase_offer(
    offer: dict,
    my_user_id: int | None,
) -> bool:

    if offer.get(
        "type"
    ) != "purchase":

        return False

    if my_user_id is None:
        return True

    from_user = offer.get(
        "from"
    )

    if not isinstance(
        from_user,
        dict,
    ):

        return False

    from_id = from_user.get(
        "id"
    )

    if from_id is None:
        return False

    return (
        int(from_id)
        == int(my_user_id)
    )


# ======================================================
# SNAPSHOTS NORMALIZADOS
# ======================================================


def build_snapshot_timeline(
    directory: str = "data",
) -> list[dict]:

    files = (
        get_snapshot_files(
            directory
        )
    )

    timeline = []

    for path in files:

        snapshot = (
            load_raw_snapshot(
                path
            )
        )

        if snapshot is None:
            continue

        timeline.append(
            {
                "path":
                    str(path),

                "timestamp":
                    parse_snapshot_timestamp(
                        path
                    ),

                "snapshot":
                    snapshot,

                "team":
                    get_my_team_lookup(
                        snapshot
                    ),
            }
        )

    timeline.sort(
        key=lambda item:
            item["timestamp"]
    )

    return timeline


# ======================================================
# BUSCAR PUJA PREVIA
# ======================================================


def find_latest_purchase_offer_before(
    timeline: list[dict],
    before_index: int,
    player_id: int,
    my_user_id: int | None,
) -> dict | None:
    """
    Busca hacia atrás la última puja nuestra por
    el jugador justo antes de que aparezca en plantilla.

    No necesitamos que siga apareciendo como "waiting"
    en el snapshot posterior: precisamente puede haber
    desaparecido porque el mercado ya se resolvió.
    """

    for index in range(
        before_index - 1,
        -1,
        -1,
    ):

        snapshot = (
            timeline[index][
                "snapshot"
            ]
        )

        offers = (
            snapshot
            .get(
                "market",
                {},
            )
            .get(
                "offers",
                [],
            )
        )

        matching = []

        for offer in offers:

            if not is_our_purchase_offer(
                offer,
                my_user_id,
            ):

                continue

            requested_ids = (
                extract_requested_player_ids(
                    offer
                )
            )

            if (
                int(player_id)
                not in requested_ids
            ):

                continue

            amount = int(
                offer.get(
                    "amount",
                    0,
                )
                or 0
            )

            if amount <= 0:
                continue

            matching.append(
                offer
            )

        if matching:

            # Si por cualquier motivo existe más de una,
            # elegimos la más reciente.
            matching.sort(
                key=lambda offer:
                    int(
                        offer.get(
                            "created",
                            0,
                        )
                        or 0
                    ),
                reverse=True,
            )

            offer = matching[0]

            return {
                "offer_id":
                    offer.get(
                        "id"
                    ),

                "amount":
                    int(
                        offer.get(
                            "amount",
                            0,
                        )
                        or 0
                    ),

                "created":
                    offer.get(
                        "created"
                    ),

                "until":
                    offer.get(
                        "until"
                    ),

                "snapshot_file":
                    timeline[index][
                        "path"
                    ],

                "snapshot_timestamp":
                    timeline[index][
                        "timestamp"
                    ],
            }

    return None


# ======================================================
# ADQUISICIÓN DE UN JUGADOR
# ======================================================


def analyze_player_acquisition(
    timeline: list[dict],
    player_id: int,
    my_user_id: int | None,
) -> dict:

    owned_indices = []

    for index, item in enumerate(
        timeline
    ):

        if (
            int(player_id)
            in item["team"]
        ):

            owned_indices.append(
                index
            )

    if not owned_indices:

        return {
            "player_id":
                player_id,

            "currently_owned":
                False,

            "acquisition_known":
                False,

            "acquisition_price":
                None,

            "source":
                "NOT_OWNED",

            "confidence":
                0,
        }

    first_owned_index = (
        owned_indices[0]
    )

    first_owned_snapshot = (
        timeline[
            first_owned_index
        ]
    )

    player = (
        first_owned_snapshot[
            "team"
        ][
            int(player_id)
        ]
    )

    # ==================================================
    # YA ESTABA EN EL PRIMER SNAPSHOT
    # ==================================================

    if first_owned_index == 0:

        return {
            "player_id":
                player_id,

            "name":
                player.get(
                    "name"
                ),

            "currently_owned":
                True,

            "acquisition_known":
                False,

            "acquisition_price":
                None,

            "acquired_at":
                None,

            "first_observed_owned_at":
                first_owned_snapshot[
                    "timestamp"
                ],

            "first_observed_owned_snapshot":
                first_owned_snapshot[
                    "path"
                ],

            "source":
                "PREHISTORY",

            "confidence":
                0,

            "reason": (
                "El jugador ya estaba en plantilla "
                "en el snapshot más antiguo disponible."
            ),
        }

    # ==================================================
    # BUSCAR PUJA PREVIA
    # ==================================================

    offer = (
        find_latest_purchase_offer_before(
            timeline=
                timeline,

            before_index=
                first_owned_index,

            player_id=
                player_id,

            my_user_id=
                my_user_id,
        )
    )

    if offer is not None:

        return {
            "player_id":
                player_id,

            "name":
                player.get(
                    "name"
                ),

            "currently_owned":
                True,

            "acquisition_known":
                True,

            "acquisition_price":
                offer[
                    "amount"
                ],

            "acquired_at":
                first_owned_snapshot[
                    "timestamp"
                ],

            "first_observed_owned_at":
                first_owned_snapshot[
                    "timestamp"
                ],

            "first_observed_owned_snapshot":
                first_owned_snapshot[
                    "path"
                ],

            "purchase_offer_id":
                offer[
                    "offer_id"
                ],

            "purchase_offer_snapshot":
                offer[
                    "snapshot_file"
                ],

            "source":
                "MATCHED_PURCHASE_OFFER",

            "confidence":
                100,

            "reason": (
                "Se detectó la transición a plantilla "
                "y una puja nuestra previa por el jugador."
            ),
        }

    # ==================================================
    # TRANSICIÓN DETECTADA PERO SIN PUJA
    # ==================================================

    return {
        "player_id":
            player_id,

        "name":
            player.get(
                "name"
            ),

        "currently_owned":
            True,

        "acquisition_known":
            False,

        "acquisition_price":
            None,

        "acquired_at":
            first_owned_snapshot[
                "timestamp"
            ],

        "first_observed_owned_at":
            first_owned_snapshot[
                "timestamp"
            ],

        "first_observed_owned_snapshot":
            first_owned_snapshot[
                "path"
            ],

        "source":
            "OWNERSHIP_TRANSITION_NO_OFFER",

        "confidence":
            20,

        "reason": (
            "Se detectó cuándo apareció en plantilla, "
            "pero no existe una puja previa suficiente "
            "para conocer el precio pagado."
        ),
    }


# ======================================================
# BOARD DE ADQUISICIONES
# ======================================================


def build_acquisition_board(
    current_snapshot: dict,
    directory: str = "data",
) -> dict:

    cache_key = (
        str(
            Path(directory).resolve()
        ),
        id(
            current_snapshot
        ),
    )

    cached = (
        _ACQUISITION_CACHE.get(
            cache_key
        )
    )

    if cached is not None:
        return cached

    timeline = (
        build_snapshot_timeline(
            directory
        )
    )

    my_user_id = (
        detect_my_user_id(
            current_snapshot
        )
    )

    current_team = (
        get_my_team_lookup(
            current_snapshot
        )
    )

    players = []

    for player_id, player in current_team.items():

        acquisition = (
            analyze_player_acquisition(
                timeline=
                    timeline,

                player_id=
                    player_id,

                my_user_id=
                    my_user_id,
            )
        )

        players.append(
            {
                **acquisition,

                "current_price":
                    int(
                        player.get(
                            "price",
                            0,
                        )
                        or 0
                    ),

                "status":
                    player.get(
                        "status"
                    ),
            }
        )

    known = [
        item
        for item in players
        if item[
            "acquisition_known"
        ]
    ]

    unknown = [
        item
        for item in players
        if not item[
            "acquisition_known"
        ]
    ]

    result = {
        "my_user_id":
            my_user_id,

        "players":
            players,

        "known":
            known,

        "unknown":
            unknown,

        "known_count":
            len(
                known
            ),

        "unknown_count":
            len(
                unknown
            ),

        "timeline_snapshots":
            len(
                timeline
            ),
    }

    _ACQUISITION_CACHE[
        cache_key
    ] = result

    return result