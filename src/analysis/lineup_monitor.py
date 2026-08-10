import json

from datetime import datetime

from pathlib import Path

from src.analysis.lineup_engine import (
    build_lineup,
)


STATE_DIRECTORY = (
    Path("data")
    / "lineup_monitor"
)


STATE_FILE = (
    STATE_DIRECTORY
    / "state.json"
)


# ============================================================
# STATE
# ============================================================


def ensure_state_directory() -> None:

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_selected_ids(
    lineup: dict,
) -> list[int]:

    return sorted(
        int(
            player[
                "id"
            ]
        )

        for player in lineup.get(
            "selected",
            []
        )
    )


def get_selected_lookup(
    lineup: dict,
) -> dict[int, dict]:

    return {
        int(
            player[
                "id"
            ]
        ):
            player

        for player in lineup.get(
            "selected",
            []
        )
    }


def load_lineup_monitor_state() -> dict | None:

    if not STATE_FILE.exists():

        return None

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return (
                json.load(
                    file
                )
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


def save_lineup_monitor_state(
    lineup: dict,
) -> None:

    ensure_state_directory()

    selected = []

    for player in lineup.get(
        "selected",
        [],
    ):

        selected.append(
            {
                "id":
                    int(
                        player[
                            "id"
                        ]
                    ),

                "name":
                    player.get(
                        "name"
                    ),

                "lineup_position":
                    int(
                        player.get(
                            "lineup_position",
                            0,
                        )
                        or 0
                    ),


                "automatic_lineup":
                    bool(
                        player.get(
                            "automatic_lineup",
                            False,
                        )
                    ),

                "availability_label":
                    player.get(
                        "availability_label"
                    ),

                "external_lineup_status":
                    player.get(
                        "external_lineup_status",
                        "UNKNOWN",
                    ),

                "external_lineup_confidence":
                    player.get(
                        "external_lineup_confidence",
                        0,
                    ),
            }
        )

    state = {
        "saved_at":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "formation_name":
            lineup.get(
                "formation_name"
            ),

        "playable_count":
            lineup.get(
                "playable_count"
            ),

        "external_source_state":
            lineup.get(
                "external_source_state"
            ),

        "external_updated_at":
            lineup.get(
                "external_updated_at"
            ),

        "selected_ids":
            get_selected_ids(
                lineup
            ),

        "selected":
            selected,
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# CAMBIOS EXTERNOS
# ============================================================


def is_external_deterioration(
    previous: str,
    current: str,
) -> bool:

    ranking = {
        "TITULAR":
            5,

        "PROBABLE":
            4,

        "UNKNOWN":
            3,

        "DUDA":
            2,

        "SUPLENTE":
            1,

        "NO_CONVOCADO":
            0,
    }

    return (
        ranking.get(
            current,
            3,
        )
        <
        ranking.get(
            previous,
            3,
        )
    )


def is_serious_external_deterioration(
    previous: str,
    current: str,
) -> bool:

    return bool(
        previous
        in {
            "TITULAR",
            "PROBABLE",
        }

        and
        current
        in {
            "DUDA",
            "SUPLENTE",
            "NO_CONVOCADO",
        }
    )


# ============================================================
# COMPARE
# ============================================================


def compare_lineups(
    previous_state: dict | None,
    current_lineup: dict,
) -> dict:

    current_ids = (
        get_selected_ids(
            current_lineup
        )
    )

    current_lookup = (
        get_selected_lookup(
            current_lineup
        )
    )

    if previous_state is None:

        return {
            "baseline":
                True,

            "changed":
                False,

            "significant_change":
                False,

            "added":
                [],

            "removed":
                [],

            "state_changes":
                [],

            "external_changes":
                [],

            "reason":
                (
                    "No existe estado anterior. "
                    "Se creara la linea base del XI."
                ),
        }

    previous_ids = {
        int(
            player_id
        )

        for player_id in previous_state.get(
            "selected_ids",
            []
        )
    }

    current_id_set = set(
        current_ids
    )

    added_ids = (
        current_id_set
        - previous_ids
    )

    removed_ids = (
        previous_ids
        - current_id_set
    )

    previous_lookup = {
        int(
            player[
                "id"
            ]
        ):
            player

        for player in previous_state.get(
            "selected",
            []
        )
    }

    added = [
        current_lookup[
            player_id
        ]

        for player_id in added_ids

        if player_id in current_lookup
    ]

    removed = [
        previous_lookup[
            player_id
        ]

        for player_id in removed_ids

        if player_id in previous_lookup
    ]

    state_changes = []

    external_changes = []

    shared_ids = (
        previous_ids
        & current_id_set
    )

    significant_change = bool(
        added
        or removed
    )

    for player_id in shared_ids:

        previous = (
            previous_lookup.get(
                player_id,
                {}
            )
        )

        current = (
            current_lookup.get(
                player_id,
                {}
            )
        )


        previous_auto = bool(
            previous.get(
                "automatic_lineup",
                False,
            )
        )

        current_auto = bool(
            current.get(
                "automatic_lineup",
                False,
            )
        )

        previous_position = int(
            previous.get(
                "lineup_position",
                0,
            )
            or 0
        )

        current_position = int(
            current.get(
                "lineup_position",
                0,
            )
            or 0
        )

        if (
            previous_auto
            != current_auto

            or
            previous_position
            != current_position
        ):

            state_changes.append(
                {
                    "id":
                        player_id,

                    "name":
                        current.get(
                            "name",
                            previous.get(
                                "name"
                            ),
                        ),


                    "previous_automatic":
                        previous_auto,

                    "current_automatic":
                        current_auto,

                    "previous_position":
                        previous_position,

                    "current_position":
                        current_position,
                }
            )

        previous_external = (
            previous.get(
                "external_lineup_status",
                "UNKNOWN",
            )
        )

        current_external = (
            current.get(
                "external_lineup_status",
                "UNKNOWN",
            )
        )

        if (
            previous_external
            != current_external
        ):

            deterioration = (
                is_external_deterioration(
                    previous=
                        previous_external,

                    current=
                        current_external,
                )
            )

            serious = (
                is_serious_external_deterioration(
                    previous=
                        previous_external,

                    current=
                        current_external,
                )
            )

            external_changes.append(
                {
                    "id":
                        player_id,

                    "name":
                        current.get(
                            "name",
                            previous.get(
                                "name"
                            ),
                        ),

                    "previous":
                        previous_external,

                    "current":
                        current_external,

                    "confidence":
                        current.get(
                            "external_lineup_confidence",
                            0,
                        ),

                    "deterioration":
                        deterioration,

                    "serious":
                        serious,
                }
            )

            if serious:

                significant_change = True


        if (
            previous_auto
            and
            not current_auto
        ):

            significant_change = True

    previous_formation = (
        previous_state.get(
            "formation_name"
        )
    )

    current_formation = (
        current_lineup.get(
            "formation_name"
        )
    )

    formation_changed = (
        previous_formation
        != current_formation
    )

    if formation_changed:

        significant_change = True

    changed = bool(
        added
        or removed
        or state_changes
        or external_changes
        or formation_changed
    )

    if not changed:

        reason = (
            "El XI recomendado no ha cambiado."
        )

    elif significant_change:

        reason = (
            "Se ha detectado un cambio relevante "
            "en el XI recomendado."
        )

    else:

        reason = (
            "Hay cambios menores en el estado "
            "del XI, pero no requieren actuacion."
        )

    return {
        "baseline":
            False,

        "changed":
            changed,

        "significant_change":
            significant_change,

        "formation_changed":
            formation_changed,

        "previous_formation":
            previous_formation,

        "current_formation":
            current_formation,

        "added":
            added,

        "removed":
            removed,

        "state_changes":
            state_changes,

        "external_changes":
            external_changes,

        "reason":
            reason,
    }


# ============================================================
# BUILD
# ============================================================


def build_lineup_monitor_state(
    snapshot: dict,
    persist: bool = False,
) -> dict:

    lineup = (
        build_lineup(
            snapshot
        )
    )

    previous_state = (
        load_lineup_monitor_state()
    )

    comparison = (
        compare_lineups(
            previous_state=
                previous_state,

            current_lineup=
                lineup,
        )
    )

    complete = (
        len(
            lineup.get(
                "selected",
                []
            )
        )
        == 11
    )

    if not complete:

        action = (
            "BLOCKED_INCOMPLETE_LINEUP"
        )

        should_save = False

    elif comparison[
        "baseline"
    ]:

        action = (
            "CREATE_BASELINE"
        )

        should_save = False

    elif comparison[
        "significant_change"
    ]:

        action = (
            "UPDATE_LINEUP"
        )

        should_save = True

    else:

        action = (
            "KEEP_LINEUP"
        )

        should_save = False

    result = {
        "lineup":
            lineup,

        "previous_state":
            previous_state,

        "comparison":
            comparison,

        "complete":
            complete,

        "action":
            action,

        "should_save":
            should_save,

        "external_lineup_source":
            lineup.get(
                "external_source_state",
                "NOT_CONNECTED",
            ),

        "external_updated_at":
            lineup.get(
                "external_updated_at"
            ),

        "external_matched_players":
            lineup.get(
                "external_matched_players",
                0,
            ),
    }

    if persist:

        save_lineup_monitor_state(
            lineup
        )

        result[
            "state_persisted"
        ] = True

    else:

        result[
            "state_persisted"
        ] = False

    return result
