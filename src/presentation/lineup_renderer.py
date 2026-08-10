# src/presentation/lineup_renderer.py


POSITION_NAMES = {
    1: "PORTERO",
    2: "DEFENSA",
    3: "CENTROCAMPISTA",
    4: "DELANTERO",
}


FIELD_WIDTH = 92
INNER_WIDTH = FIELD_WIDTH - 2


# ============================================================
# UTILIDADES
# ============================================================


def clean_name(
    name: str,
    max_length: int = 18,
) -> str:

    value = str(
        name
        or "?"
    )

    if len(value) <= max_length:
        return value

    return (
        value[
            :max_length - 1
        ]
        + "."
    )


def get_player_state(
    player: dict,
) -> str:

    if not player.get(
        "is_available",
        True,
    ):

        return "NO DISP"

    if (
        player.get(
            "has_game",
            False,
        )
        and
        player.get(
            "automatic_lineup",
            True,
        )
    ):

        return "PARTIDO"

    if (
        player.get(
            "has_game",
            False,
        )
        and
        not player.get(
            "automatic_lineup",
            True,
        )
    ):

        return "DUDA"

    return "SIN PARTIDO"


def field_line(
    content: str = "",
) -> str:

    return (
        "|"
        + content.center(
            INNER_WIDTH
        )[
            :INNER_WIDTH
        ]
        + "|"
    )


def horizontal_line() -> str:

    return (
        "+"
        + "-"
        * INNER_WIDTH
        + "+"
    )


def midfield_line() -> str:

    half = (
        INNER_WIDTH
        // 2
    )

    return (
        "|"
        + "-"
        * half
        + "+"
        + "-"
        * (
            INNER_WIDTH
            - half
            - 1
        )
        + "|"
    )


# ============================================================
# DISTRIBUIR NOMBRES
# ============================================================


def distribute_names(
    players: list[dict],
    width: int = INNER_WIDTH,
) -> str:

    if not players:
        return ""

    names = [
        clean_name(
            player.get(
                "name",
                "?",
            ),
            max_length=17,
        )

        for player in players
    ]

    count = len(
        names
    )

    if count == 1:

        return names[
            0
        ].center(
            width
        )

    slot_width = max(
        width
        // count,
        1,
    )

    result = ""

    for name in names:

        result += (
            name[
                :slot_width - 1
            ]
            .center(
                slot_width
            )
        )

    return result[
        :width
    ]


# ============================================================
# AGRUPAR
# ============================================================


def group_lineup_by_position(
    lineup: dict,
) -> dict[int, list[dict]]:

    grouped = {
        1: [],
        2: [],
        3: [],
        4: [],
    }

    for player in lineup.get(
        "selected",
        [],
    ):

        position = int(
            player.get(
                "lineup_position",
                player.get(
                    "position",
                    0,
                ),
            )
            or 0
        )

        if position in grouped:

            grouped[
                position
            ].append(
                player
            )

    return grouped


# ============================================================
# HUECOS
# ============================================================


def format_shortages(
    lineup: dict,
) -> str:

    shortages = (
        lineup.get(
            "matchday_shortages",
            {},
        )
        or {}
    )

    parts = []

    for position in (
        1,
        2,
        3,
        4,
    ):

        count = int(
            shortages.get(
                position,
                0,
            )
            or 0
        )

        if count <= 0:
            continue

        parts.append(
            f"{POSITION_NAMES[position]} x{count}"
        )

    if not parts:

        return "NINGUNO"

    return ", ".join(
        parts
    )


# ============================================================
# ESTADOS
# ============================================================


def render_player_states(
    lineup: dict,
) -> list[str]:

    selected = (
        lineup.get(
            "selected",
            [],
        )
        or []
    )

    lines = []

    for player in selected:

        name = clean_name(
            player.get(
                "name",
                "?",
            ),
            22,
        )

        state = (
            get_player_state(
                player
            )
        )

        position = (
            POSITION_NAMES.get(
                int(
                    player.get(
                        "lineup_position",
                        0,
                    )
                    or 0
                ),
                "?",
            )
        )

        lines.append(
            f"  {name:<23}"
            f"{position:<17}"
            f"{state}"
        )

    return lines


# ============================================================
# RENDER
# ============================================================


def render_lineup_field(
    lineup: dict,
    jornada: int | str | None = None,
) -> str:

    grouped = (
        group_lineup_by_position(
            lineup
        )
    )

    formation = (
        lineup.get(
            "formation_name",
            "DESCONOCIDA",
        )
    )

    playable = int(
        lineup.get(
            "playable_count",
            0,
        )
        or 0
    )

    selected_count = int(
        lineup.get(
            "total_selected",
            0,
        )
        or 0
    )

    title = (
        "BORDALAS IA - XI"
    )

    if jornada is not None:

        title += (
            f" - JORNADA {jornada}"
        )

    lines = [
        "",
        "=" * FIELD_WIDTH,
        title.center(
            FIELD_WIDTH
        ),
        "=" * FIELD_WIDTH,
        "",
        horizontal_line(),
        field_line(),
        field_line(
            distribute_names(
                grouped[
                    4
                ]
            )
        ),
        field_line(),
        field_line(),
        field_line(
            distribute_names(
                grouped[
                    3
                ]
            )
        ),
        field_line(),
        midfield_line(),
        field_line(),
        field_line(
            distribute_names(
                grouped[
                    2
                ]
            )
        ),
        field_line(),
        field_line(),
        field_line(
            distribute_names(
                grouped[
                    1
                ]
            )
        ),
        field_line(),
        horizontal_line(),
        "",
        f"Formacion:           {formation}",
        f"Jugadores elegidos: {selected_count}/11",
        f"Con partido:         {playable}/11",
        (
            "Huecos jornada:      "
            + format_shortages(
                lineup
            )
        ),
        "",
        "ESTADO DEL XI",
        "-" * FIELD_WIDTH,
    ]

    lines.extend(
        render_player_states(
            lineup
        )
    )

    blocked = (
        lineup.get(
            "blocked_players",
            [],
        )
        or []
    )

    if blocked:

        lines.extend(
            [
                "",
                "BLOQUEADOS",
                "-" * FIELD_WIDTH,
            ]
        )

        for player in blocked:

            lines.append(
                "  "
                + clean_name(
                    player.get(
                        "name",
                        "?",
                    ),
                    24,
                )
                + " - "
                + str(
                    player.get(
                        "availability_label",
                        "NO DISPONIBLE",
                    )
                )
            )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def print_lineup_field(
    lineup: dict,
    jornada: int | str | None = None,
) -> None:

    print(
        render_lineup_field(
            lineup=
                lineup,

            jornada=
                jornada,
        )
    )