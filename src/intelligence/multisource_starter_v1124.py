from __future__ import annotations

import json
import re
import time
import unicodedata

from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.intelligence.jornada_perfecta_provider import (
    build_roster_records,
    calculate_refresh_seconds,
    canonical_team_key,
    refresh_jornada_perfecta_data,
)


OUTPUT_FILE = Path(
    "data/intelligence/"
    "starter_multisource_v1124.json"
)

AF_BASE = (
    "https://www.analiticafantasy.com"
)

AF_URL_TEMPLATE = (
    AF_BASE
    + "/alineaciones-probables/la-liga/"
    + "temporada-2026/jornada-{matchday}"
)

FF_BASE = (
    "https://www.futbolfantasy.com"
)

FF_TEAM_SLUGS = {
    "alaves": "alaves",
    "athletic": "athletic",
    "athletic bilbao": "athletic",
    "atletico madrid": "atletico",
    "barcelona": "barcelona",
    "betis": "betis",
    "real betis": "betis",
    "celta": "celta",
    "celta vigo": "celta",
    "deportivo": "deportivo",
    "deportivo la coruna": "deportivo",
    "elche": "elche",
    "espanyol": "espanyol",
    "getafe": "getafe",
    "levante": "levante",
    "malaga": "malaga",
    "osasuna": "osasuna",
    "racing": "racing",
    "racing santander": "racing",
    "rayo": "rayo",
    "rayo vallecano": "rayo",
    "real madrid": "real-madrid",
    "real sociedad": "real-sociedad",
    "sevilla": "sevilla",
    "valencia": "valencia",
    "villarreal": "villarreal",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
}

TIMEOUT = 25


def load_cached_board(
    path: Path | None = None,
) -> dict | None:
    path = path or OUTPUT_FILE

    if not path.exists():
        return None

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8-sig",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    return value if isinstance(value, dict) else None


def cached_board_age_seconds(
    board: dict,
    *,
    path: Path | None = None,
    now: datetime | None = None,
) -> float | None:
    del path
    updated_at = board.get("updated_at")

    if updated_at:
        try:
            timestamp = datetime.fromisoformat(
                str(updated_at).replace("Z", "+00:00")
            )
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(
                    tzinfo=timezone.utc,
                )
        except (
            TypeError,
            ValueError,
        ):
            timestamp = None
    else:
        timestamp = None

    # Un cache antiguo sin timestamp verificable se renueva. No usamos el
    # mtime porque actions/checkout lo haria parecer nuevo tras cada deploy.
    if timestamp is None:
        return None

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    return max(
        0.0,
        (
            current.astimezone(timezone.utc)
            - timestamp.astimezone(timezone.utc)
        ).total_seconds(),
    )


def cached_board_is_fresh(
    board: dict | None,
    *,
    matchday: int,
    seconds_to_deadline=None,
    path: Path | None = None,
    now: datetime | None = None,
) -> bool:
    if not board:
        return False

    # UN TABLERO VACIO NO ES UN TABLERO FRESCO.
    #
    # 16/08/2026. El dashboard publicado pinto "sin dato" en los
    # once mientras en el PC de casa el mismo codigo sacaba 96 %.
    # No fallo nada: `cache_status` decia HIT, `error` decia null,
    # y el tablero traia CERO jugadores.
    #
    # Un tablero sin jugadores solo se genera cuando el snapshot
    # llego sin plantilla. Ese fichero se escribia igual, y a
    # partir de ahi esta funcion lo daba por bueno durante dos
    # horas -solo miraba jornada y antiguedad-, envenenando cada
    # generacion posterior aunque el snapshot siguiente fuese
    # perfecto.
    #
    # Servir la nada como si fuese un dato es el fallo mas caro
    # de todos, porque no se parece a un fallo.
    if not (board.get("players") or []):
        return False

    if int(board.get("matchday") or -1) != int(matchday):
        return False

    age = cached_board_age_seconds(
        board,
        path=path,
        now=now,
    )
    if age is None:
        return False

    return age < calculate_refresh_seconds(
        seconds_to_deadline
    )


def board_with_cache_status(
    board: dict,
    *,
    status: str,
    seconds_to_deadline=None,
    age_seconds: float | None = None,
    error: str | None = None,
) -> dict:
    result = dict(board)
    result["cache"] = {
        "status": status,
        "age_seconds": (
            round(age_seconds, 1)
            if age_seconds is not None
            else None
        ),
        "ttl_seconds": calculate_refresh_seconds(
            seconds_to_deadline
        ),
        "error": error,
    }
    return result


def normalize(value) -> str:
    value = str(value or "").strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(
            char
        )
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def fetch(
    session: requests.Session,
    url: str,
) -> str:
    response = session.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    return response.text


def aliases_for_roster_player(
    player: dict,
    snapshot: dict,
) -> list[str]:
    aliases = []

    name = normalize(
        player.get("name")
    )

    if name:
        aliases.append(name)

    catalog = (
        snapshot.get(
            "catalog",
            {},
        )
        .get(
            "data",
            {},
        )
        .get(
            "players",
            {},
        )
        or {}
    )

    raw = (
        catalog.get(
            str(
                player.get("id")
            ),
            {},
        )
        or {}
    )

    slug = normalize(
        str(
            raw.get("slug")
            or ""
        ).replace("-", " ")
    )

    if slug and slug not in aliases:
        aliases.append(slug)

    return aliases


def strict_name_score(
    external_name: str,
    roster_aliases: list[str],
) -> float:
    external = normalize(
        external_name
    )

    if not external:
        return 0.0

    ext_tokens = external.split()

    best = 0.0

    for alias in roster_aliases:

        alias = normalize(
            alias
        )

        if not alias:
            continue

        if external == alias:
            best = max(
                best,
                1.0,
            )
            continue

        alias_tokens = alias.split()

        if (
            ext_tokens
            and
            alias_tokens
            and
            ext_tokens[-1]
            ==
            alias_tokens[-1]
        ):
            best = max(
                best,
                SequenceMatcher(
                    None,
                    external,
                    alias,
                ).ratio(),
                0.86,
            )
            continue

        # Within an already-strict team section, a distinctive
        # first name may be used only as a weak candidate.
        if (
            len(ext_tokens) >= 1
            and
            len(alias_tokens) >= 1
            and
            ext_tokens[0]
            ==
            alias_tokens[0]
            and
            len(ext_tokens[0]) >= 5
        ):
            best = max(
                best,
                0.0,
            )

    return best


def match_team_player(
    external_name: str,
    candidates: list[dict],
    snapshot: dict,
) -> dict | None:
    scored = []

    for player in candidates:

        score = strict_name_score(
            external_name,
            aliases_for_roster_player(
                player,
                snapshot,
            ),
        )

        scored.append(
            (
                score,
                player,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    if not scored:
        return None

    best_score, best = scored[0]

    second = (
        scored[1][0]
        if len(scored) > 1
        else 0.0
    )

    if best_score < 0.75:
        return None

    if (
        second >= 0.75
        and
        best_score - second < 0.08
    ):
        return None

    return {
        "player":
            best,

        "score":
            round(
                best_score,
                3,
            ),
    }


def jp_probability(
    status: str | None,
    confidence,
) -> float | None:
    status = str(
        status
        or "UNKNOWN"
    ).upper()

    prior = {
        "TITULAR": 94.0,
        "PROBABLE": 76.0,
        "DUDA": 50.0,
        "SUPLENTE": 24.0,
        "NO_CONVOCADO": 1.0,
    }.get(
        status
    )

    if prior is None:
        return None

    try:
        conf = float(
            confidence
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        conf = 0.0

    conf = max(
        0.0,
        min(
            conf,
            100.0,
        ),
    )

    # JP status can be inferred. Never pretend it was a literal
    # percentage when it was not.
    value = (
        50.0
        +
        (
            prior
            - 50.0
        )
        *
        (
            conf
            / 100.0
        )
    )

    return round(
        value,
        1,
    )


def build_jp_signals(
    snapshot: dict,
    matchday: int,
    seconds_to_deadline,
) -> dict[int, dict]:

    response = (
        refresh_jornada_perfecta_data(
            snapshot=
                snapshot,

            target_matchday=
                matchday,

            seconds_to_deadline=
                seconds_to_deadline,

            force=
                False,
        )
    )

    data = (
        response.get(
            "data",
            {},
        )
        or {}
    )

    rows = (
        data.get(
            "players",
            [],
        )
        or []
    )

    result = {}

    for row in rows:

        player_id = row.get(
            "biwenger_id"
        )

        if not player_id:
            continue

        probability = jp_probability(
            row.get(
                "status"
            ),
            row.get(
                "confidence"
            ),
        )

        result[
            int(
                player_id
            )
        ] = {
            "source":
                "JORNADA_PERFECTA",

            "probability":
                probability,

            "status":
                row.get(
                    "status"
                ),

            "confidence":
                row.get(
                    "confidence"
                ),

            "method":
                row.get(
                    "jp_parser_role"
                )
                or
                "JP_PROVIDER",

            "source_name":
                row.get(
                    "jp_name"
                ),

            "url":
                row.get(
                    "player_url"
                )
                or
                row.get(
                    "source_url"
                ),

            "team":
                row.get(
                    "team"
                ),
        }

    return result


def percentage_after_element(
    element,
) -> float | None:
    seen = 0

    for node in element.next_elements:

        if node is element:
            continue

        if getattr(
            node,
            "name",
            None,
        ) in {
            "h2",
            "h3",
        }:
            break

        if getattr(
            node,
            "name",
            None,
        ) == "img":
            break

        text = (
            str(node)
            if not hasattr(
                node,
                "get_text"
            )
            else node.get_text(
                " ",
                strip=True,
            )
        )

        match = re.search(
            r"\b(\d{1,3})\s*%",
            text,
        )

        if match:
            value = float(
                match.group(1)
            )

            if 0 <= value <= 100:
                return value

        seen += 1

        if seen >= 20:
            break

    return None


def parse_analitica_page(
    html: str,
) -> list[dict]:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    current_team = None
    records = []

    for element in soup.find_all(
        [
            "h3",
            "img",
        ]
    ):

        if element.name == "h3":

            heading = element.get_text(
                " ",
                strip=True,
            )

            match = re.search(
                r"Alineaci[oó]n probable de\s+(.+?)(?:\s*\(|$)",
                heading,
                re.IGNORECASE,
            )

            if match:
                current_team = (
                    match.group(1)
                    .strip()
                )

            continue

        alt = str(
            element.get(
                "alt"
            )
            or ""
        ).strip()

        name_match = re.match(
            r"Foto de\s+(.+)",
            alt,
            re.IGNORECASE,
        )

        if not name_match:
            continue

        external_name = (
            name_match.group(1)
            .strip()
        )

        probability = (
            percentage_after_element(
                element
            )
        )

        records.append(
            {
                "team":
                    current_team,

                "name":
                    external_name,

                "probability":
                    probability,

                "method":
                    (
                        "EXPLICIT_PERCENT"
                        if probability
                        is not None
                        else
                        "PLAYER_NO_PERCENT"
                    ),
            }
        )

    return records


def build_af_signals(
    snapshot: dict,
    roster: list[dict],
    matchday: int,
    session: requests.Session,
) -> tuple[
    dict[int, dict],
    dict,
]:

    url = AF_URL_TEMPLATE.format(
        matchday=
            matchday
    )

    try:

        html = fetch(
            session,
            url,
        )

    except Exception as error:

        return (
            {},
            {
                "url":
                    url,

                "error":
                    (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),

                "records":
                    0,
            },
        )

    records = parse_analitica_page(
        html
    )

    roster_by_team = {}

    for player in roster:

        key = player.get(
            "team_key"
        )

        if not key:
            continue

        roster_by_team.setdefault(
            key,
            [],
        ).append(
            player
        )

    team_record_counts = {}
    matched_ids = set()
    result = {}

    for record in records:

        team_key = canonical_team_key(
            record.get(
                "team"
            )
        )

        if not team_key:
            continue

        team_record_counts[
            team_key
        ] = (
            team_record_counts.get(
                team_key,
                0,
            )
            +
            (
                1
                if record.get(
                    "probability"
                )
                is not None
                else 0
            )
        )

        candidates = roster_by_team.get(
            team_key,
            [],
        )

        if not candidates:
            continue

        matched = match_team_player(
            record.get(
                "name",
                "",
            ),
            candidates,
            snapshot,
        )

        if not matched:
            continue

        player = matched[
            "player"
        ]

        player_id = int(
            player[
                "id"
            ]
        )

        probability = record.get(
            "probability"
        )

        if probability is None:
            continue

        previous = result.get(
            player_id
        )

        if (
            previous is None
            or
            matched[
                "score"
            ]
            >
            previous.get(
                "match_score",
                0.0,
            )
        ):

            result[
                player_id
            ] = {
                "source":
                    "ANALITICA_FANTASY",

                "probability":
                    round(
                        float(
                            probability
                        ),
                        1,
                    ),

                "status":
                    (
                        "STARTER"
                        if probability >= 67
                        else
                        "BENCH"
                        if probability <= 40
                        else
                        "UNCERTAIN"
                    ),

                "confidence":
                    100,

                "method":
                    "EXPLICIT_PERCENT",

                "source_name":
                    record.get(
                        "name"
                    ),

                "team":
                    record.get(
                        "team"
                    ),

                "url":
                    url,

                "match_score":
                    matched[
                        "score"
                    ],
            }

            matched_ids.add(
                player_id
            )

    # Absence from a properly parsed probable XI is meaningful.
    # We only use it when that team section supplied >=9 explicit
    # starter percentages.
    for player in roster:

        player_id = int(
            player[
                "id"
            ]
        )

        if player_id in matched_ids:
            continue

        team_key = player.get(
            "team_key"
        )

        if (
            not team_key
            or
            team_record_counts.get(
                team_key,
                0,
            )
            < 9
        ):
            continue

        result[
            player_id
        ] = {
            "source":
                "ANALITICA_FANTASY",

            "probability":
                25.0,

            "status":
                "BENCH",

            "confidence":
                75,

            "method":
                "NOT_IN_PROBABLE_XI",

            "source_name":
                None,

            "team":
                player.get(
                    "team"
                ),

            "url":
                url,

            "match_score":
                1.0,
        }

    return (
        result,
        {
            "url":
                url,

            "error":
                None,

            "records":
                len(
                    records
                ),

            "matched":
                len(
                    result
                ),
        },
    )


def ff_team_slug(
    team_name: str,
) -> str | None:

    normalized = normalize(
        team_name
    )

    direct = FF_TEAM_SLUGS.get(
        normalized
    )

    if direct:
        return direct

    key = canonical_team_key(
        team_name
    )

    return FF_TEAM_SLUGS.get(
        normalize(
            key
        )
    )


def ff_percentages(
    text: str,
) -> list[float]:

    result = []

    for raw in re.findall(
        r"(?<!\d)(\d{1,3})\s*%",
        str(
            text
            or ""
        ),
    ):

        value = float(
            raw
        )

        if 0.0 <= value <= 100.0:
            result.append(
                value
            )

    return result


def ff_element_external_names(
    element,
) -> list[str]:

    names = []

    for anchor in element.find_all(
        "a",
        href=True,
    ):

        label = anchor.get_text(
            " ",
            strip=True,
        )

        if (
            label
            and
            len(
                normalize(
                    label
                )
            )
            >= 3
        ):
            names.append(
                label
            )

        href = str(
            anchor.get(
                "href"
            )
            or ""
        )

        for token in (
            "/jugadores/",
            "/jugador/",
        ):

            if token in href:

                tail = (
                    href.split(
                        token,
                        1,
                    )[
                        1
                    ]
                    .split(
                        "?",
                        1,
                    )[
                        0
                    ]
                    .strip(
                        "/"
                    )
                )

                pieces = [
                    part
                    for part in tail.split(
                        "/"
                    )
                    if part
                ]

                if pieces:

                    slug = pieces[
                        -1
                    ].replace(
                        "-",
                        " ",
                    )

                    if slug:
                        names.append(
                            slug
                        )

    for image in element.find_all(
        "img",
    ):

        alt = str(
            image.get(
                "alt"
            )
            or ""
        ).strip()

        match = re.search(
            r"(?:Foto|Imagen|Jugador)\s+de\s+(.+)",
            alt,
            re.IGNORECASE,
        )

        if match:
            names.append(
                match.group(
                    1
                )
            )

    unique = []

    for name in names:

        normalized = normalize(
            name
        )

        if (
            normalized
            and
            normalized
            not in {
                normalize(
                    item
                )
                for item in unique
            }
        ):
            unique.append(
                name
            )

    return unique


def ff_match_external_names(
    external_names: list[str],
    players: list[dict],
    snapshot: dict,
) -> dict | None:

    scored = []

    for player in players:

        aliases = (
            aliases_for_roster_player(
                player,
                snapshot,
            )
        )

        score = 0.0
        source_name = None

        for external_name in external_names:

            current = (
                strict_name_score(
                    external_name,
                    aliases,
                )
            )

            if current > score:

                score = current
                source_name = (
                    external_name
                )

        scored.append(
            (
                score,
                player,
                source_name,
            )
        )

    scored.sort(
        key=lambda item: item[
            0
        ],
        reverse=True,
    )

    if not scored:
        return None

    best_score, best, best_name = (
        scored[
            0
        ]
    )

    second = (
        scored[
            1
        ][
            0
        ]
        if len(
            scored
        )
        > 1
        else 0.0
    )

    if best_score < 0.75:
        return None

    if (
        second >= 0.75
        and
        best_score - second < 0.08
    ):
        return None

    return {
        "player":
            best,

        "score":
            round(
                best_score,
                3,
            ),

        "source_name":
            best_name,
    }


def ff_find_probability_column(
    table,
) -> int | None:

    rows = table.find_all(
        "tr"
    )

    for row in rows[:4]:

        cells = row.find_all(
            [
                "th",
                "td",
            ]
        )

        for index, cell in enumerate(
            cells
        ):

            header = normalize(
                cell.get_text(
                    " ",
                    strip=True,
                )
            )

            if (
                header == "prob"
                or
                header.startswith(
                    "prob "
                )
                or
                "probabilidad"
                in header
            ):
                return index

    return None


def ff_extract_table_records(
    soup,
    players: list[dict],
    snapshot: dict,
) -> list[dict]:

    records = []

    for table in soup.find_all(
        "table"
    ):

        probability_index = (
            ff_find_probability_column(
                table
            )
        )

        # Strongest signal: the table explicitly contains
        # a Prob./Probabilidad column.
        if probability_index is None:
            continue

        for row in table.find_all(
            "tr"
        ):

            cells = row.find_all(
                [
                    "td",
                    "th",
                ]
            )

            if (
                len(
                    cells
                )
                <= probability_index
            ):
                continue

            probability_values = (
                ff_percentages(
                    cells[
                        probability_index
                    ].get_text(
                        " ",
                        strip=True,
                    )
                )
            )

            if not probability_values:
                continue

            external_names = (
                ff_element_external_names(
                    row
                )
            )

            # Some FF versions render the player as plain text.
            if not external_names:

                for cell in cells:

                    text_value = (
                        cell.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    if (
                        text_value
                        and
                        "%"
                        not in text_value
                        and
                        len(
                            normalize(
                                text_value
                            )
                        )
                        <= 50
                    ):

                        external_names.append(
                            text_value
                        )

            matched = (
                ff_match_external_names(
                    external_names,
                    players,
                    snapshot,
                )
            )

            if not matched:
                continue

            records.append(
                {
                    "player":
                        matched[
                            "player"
                        ],

                    "source_name":
                        matched[
                            "source_name"
                        ],

                    "match_score":
                        matched[
                            "score"
                        ],

                    "probability":
                        probability_values[
                            0
                        ],

                    "method":
                        "TEAM_TABLE_PROB_COLUMN",
                }
            )

    return records


def ff_extract_row_records(
    soup,
    players: list[dict],
    snapshot: dict,
) -> list[dict]:

    records = []

    # Fallback for versions where the lineup is rendered as
    # div/list cards instead of a semantic table.
    for element in soup.find_all(
        [
            "tr",
            "li",
            "article",
            "div",
        ]
    ):

        text_value = element.get_text(
            " ",
            strip=True,
        )

        if (
            not text_value
            or
            len(
                text_value
            )
            > 260
        ):
            continue

        values = ff_percentages(
            text_value
        )

        if len(values) != 1:
            continue

        classes = " ".join(
            element.get(
                "class",
                [],
            )
            or []
        )

        marker = normalize(
            f"{element.get('id','')} "
            f"{classes}"
        )

        # Avoid unrelated market/stat cards unless DOM semantics
        # look lineup/player/probability-related.
        semantic = any(
            token in marker
            for token in (
                "aline",
                "lineup",
                "player",
                "jugador",
                "prob",
                "once",
            )
        )

        external_names = (
            ff_element_external_names(
                element
            )
        )

        if (
            not semantic
            and
            not external_names
        ):
            continue

        matched = (
            ff_match_external_names(
                external_names,
                players,
                snapshot,
            )
        )

        if not matched:
            continue

        records.append(
            {
                "player":
                    matched[
                        "player"
                    ],

                "source_name":
                    matched[
                        "source_name"
                    ],

                "match_score":
                    matched[
                        "score"
                    ],

                "probability":
                    values[
                        0
                    ],

                "method":
                    "TEAM_DOM_NEAR_PLAYER_PERCENT",
            }
        )

    return records


def ff_extract_text_window_records(
    soup,
    players: list[dict],
    snapshot: dict,
) -> list[dict]:

    records = []

    # Last conservative fallback. Search only inside a section
    # whose text contains "Posible alineacion".
    possible_section = None

    for heading in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
        ]
    ):

        heading_text = normalize(
            heading.get_text(
                " ",
                strip=True,
            )
        )

        if (
            "posible alineacion"
            in heading_text
            or
            "alineacion probable"
            in heading_text
        ):

            possible_section = (
                heading.parent
            )
            break

    if possible_section is None:
        return records

    section_text = (
        possible_section.get_text(
            " ",
            strip=True,
        )
    )

    section_norm = normalize(
        section_text
    )

    for player in players:

        aliases = (
            aliases_for_roster_player(
                player,
                snapshot,
            )
        )

        candidate_aliases = sorted(
            aliases,
            key=len,
            reverse=True,
        )

        found = None

        for alias in candidate_aliases:

            alias_norm = normalize(
                alias
            )

            if (
                len(
                    alias_norm
                )
                < 4
            ):
                continue

            index = section_norm.find(
                alias_norm
            )

            if index >= 0:
                found = alias_norm
                break

        if not found:
            continue

        # Normalized-text offsets are approximate. Use a generous
        # local window but accept ONLY one percentage.
        index = section_norm.find(
            found
        )

        window = section_norm[
            max(
                0,
                index - 80,
            ):
            index
            + len(
                found
            )
            + 100
        ]

        values = ff_percentages(
            window
        )

        if len(values) != 1:
            continue

        records.append(
            {
                "player":
                    player,

                "source_name":
                    found,

                "match_score":
                    0.90,

                "probability":
                    values[
                        0
                    ],

                "method":
                    "TEAM_POSSIBLE_XI_TEXT_WINDOW",
            }
        )

    return records


def parse_ff_team_page(
    html: str,
    players: list[dict],
    snapshot: dict,
) -> list[dict]:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    strategies = [
        ff_extract_table_records(
            soup,
            players,
            snapshot,
        ),

        ff_extract_row_records(
            soup,
            players,
            snapshot,
        ),

        ff_extract_text_window_records(
            soup,
            players,
            snapshot,
        ),
    ]

    best_by_id = {}

    method_priority = {
        "TEAM_TABLE_PROB_COLUMN":
            3,

        "TEAM_DOM_NEAR_PLAYER_PERCENT":
            2,

        "TEAM_POSSIBLE_XI_TEXT_WINDOW":
            1,
    }

    for records in strategies:

        for record in records:

            player_id = int(
                record[
                    "player"
                ][
                    "id"
                ]
            )

            previous = (
                best_by_id.get(
                    player_id
                )
            )

            if previous is None:

                best_by_id[
                    player_id
                ] = record

                continue

            current_key = (
                method_priority.get(
                    record[
                        "method"
                    ],
                    0,
                ),
                record[
                    "match_score"
                ],
            )

            previous_key = (
                method_priority.get(
                    previous[
                        "method"
                    ],
                    0,
                ),
                previous[
                    "match_score"
                ],
            )

            if current_key > previous_key:

                best_by_id[
                    player_id
                ] = record

    return list(
        best_by_id.values()
    )


def build_ff_signals(
    snapshot: dict,
    roster: list[dict],
    matchday: int,
    session: requests.Session,
) -> tuple[
    dict[int, dict],
    dict,
]:

    del matchday

    roster_by_team = {}

    for player in roster:

        key = player.get(
            "team_key"
        )

        if key:

            roster_by_team.setdefault(
                key,
                [],
            ).append(
                player
            )

    result = {}
    errors = []
    team_pages = 0
    parsed_records = 0
    methods = {}

    for team_key, players in roster_by_team.items():

        team_name = (
            players[
                0
            ].get(
                "team"
            )
            or team_key
        )

        slug = ff_team_slug(
            team_name
        )

        if not slug:

            errors.append(
                f"NO_SLUG:{team_name}"
            )
            continue

        team_url = (
            f"{FF_BASE}/laliga/"
            f"equipos/{slug}"
        )

        try:

            html = fetch(
                session,
                team_url,
            )

        except Exception as error:

            errors.append(
                f"{team_name}:"
                f"{type(error).__name__}:"
                f"{error}"
            )

            continue

        team_pages += 1

        records = parse_ff_team_page(
            html,
            players,
            snapshot,
        )

        parsed_records += len(
            records
        )

        for record in records:

            player = record[
                "player"
            ]

            player_id = int(
                player[
                    "id"
                ]
            )

            probability = float(
                record[
                    "probability"
                ]
            )

            method = record[
                "method"
            ]

            methods[
                method
            ] = (
                methods.get(
                    method,
                    0,
                )
                + 1
            )

            result[
                player_id
            ] = {
                "source":
                    "FUTBOLFANTASY",

                "probability":
                    round(
                        probability,
                        1,
                    ),

                "status":
                    (
                        "STARTER"
                        if probability >= 67
                        else
                        "BENCH"
                        if probability <= 40
                        else
                        "UNCERTAIN"
                    ),

                "confidence":
                    100,

                "method":
                    method,

                "source_name":
                    record.get(
                        "source_name"
                    ),

                "team":
                    team_name,

                "url":
                    team_url,

                "match_score":
                    record[
                        "match_score"
                    ],
            }

    return (
        result,
        {
            "team_pages":
                team_pages,

            "player_profiles":
                0,

            "parsed_records":
                parsed_records,

            "matched":
                len(
                    result
                ),

            "methods":
                methods,

            "errors":
                errors[:20],
        },
    )



def source_vote(
    probability: float,
) -> str:

    if probability >= 67.0:
        return "STARTER"

    if probability <= 40.0:
        return "BENCH"

    return "UNCERTAIN"


def consensus(
    signals: list[dict],
) -> dict:

    usable = [
        signal
        for signal in signals
        if (
            signal
            and
            signal.get(
                "probability"
            )
            is not None
        )
    ]

    probabilities = [
        float(
            signal[
                "probability"
            ]
        )
        for signal in usable
    ]

    coverage = len(
        probabilities
    )

    sorted_values = sorted(
        probabilities
    )

    if not sorted_values:
        raw_probability = 50.0

    elif coverage == 1:
        raw_probability = sorted_values[0]

    elif coverage == 2:
        raw_probability = (
            sorted_values[0]
            +
            sorted_values[1]
        ) / 2.0

    else:
        # Median: two agreeing sources beat one outlier.
        raw_probability = sorted_values[1]

    votes = [
        source_vote(
            value
        )
        for value in probabilities
    ]

    starter_votes = votes.count(
        "STARTER"
    )

    bench_votes = votes.count(
        "BENCH"
    )

    uncertain_votes = votes.count(
        "UNCERTAIN"
    )

    # --------------------------------------------------------
    # V11.3.1 CONSENSUS RULE
    #
    # STARTER/BENCH needs two real votes when >=2 sources exist.
    # One STARTER + one 50% source is UNCERTAIN, not STARTER_LEAN.
    # --------------------------------------------------------

    if (
        coverage >= 2
        and
        starter_votes >= 2
    ):
        label = "STARTER"

    elif (
        coverage >= 2
        and
        bench_votes >= 2
    ):
        label = "BENCH"

    elif coverage == 1:

        if starter_votes == 1:
            label = "STARTER_LEAN"

        elif bench_votes == 1:
            label = "BENCH_LEAN"

        else:
            label = "UNCERTAIN"

    else:
        label = "UNCERTAIN"

    # Do not let a numerical average contradict the vote class.
    if label == "STARTER":

        probability = max(
            67.0,
            raw_probability,
        )

    elif label == "BENCH":

        probability = min(
            40.0,
            raw_probability,
        )

    elif label == "STARTER_LEAN":

        # One source can be strongly positive, but it cannot
        # pretend to have multi-source certainty.
        probability = min(
            74.0,
            max(
                67.0,
                raw_probability,
            ),
        )

    elif label == "BENCH_LEAN":

        probability = max(
            26.0,
            min(
                40.0,
                raw_probability,
            ),
        )

    else:

        # Any unresolved disagreement stays inside the
        # uncertainty band.
        probability = max(
            41.0,
            min(
                59.0,
                raw_probability,
            ),
        )

    spread = (
        max(
            sorted_values
        )
        -
        min(
            sorted_values
        )
        if coverage >= 2
        else 0.0
    )

    if (
        coverage == 3
        and
        label
        in {
            "STARTER",
            "BENCH",
        }
        and
        spread <= 20.0
    ):
        confidence = "HIGH"

    elif (
        coverage >= 2
        and
        label
        in {
            "STARTER",
            "BENCH",
        }
        and
        spread <= 30.0
    ):
        confidence = "MEDIUM"

    elif coverage >= 2:
        confidence = "CONFLICT"

    elif coverage == 1:
        confidence = "LOW"

    else:
        confidence = "NONE"

    ranking_tier = {
        "STARTER": 5,
        "STARTER_LEAN": 4,
        "UNCERTAIN": 3,
        "BENCH_LEAN": 2,
        "BENCH": 1,
    }.get(
        label,
        0,
    )

    vote_details = []

    for signal in usable:

        value = float(
            signal[
                "probability"
            ]
        )

        vote_details.append(
            {
                "source":
                    signal.get(
                        "source"
                    ),

                "probability":
                    round(
                        value,
                        1,
                    ),

                "vote":
                    source_vote(
                        value
                    ),
            }
        )

    return {
        "starter_probability":
            round(
                probability,
                1,
            ),

        "raw_starter_probability":
            round(
                raw_probability,
                1,
            ),

        "expected_minutes":
            round(
                max(
                    0.0,
                    min(
                        90.0,
                        probability
                        * 0.90,
                    ),
                ),
                1,
            ),

        "source_coverage":
            coverage,

        "consensus":
            label,

        "confidence":
            confidence,

        "ranking_tier":
            ranking_tier,

        "starter_votes":
            starter_votes,

        "bench_votes":
            bench_votes,

        "uncertain_votes":
            uncertain_votes,

        "source_votes":
            vote_details,

        "spread":
            round(
                spread,
                1,
            ),
    }

def build_multisource_board(
    snapshot: dict,
    matchday: int,
    seconds_to_deadline=None,
) -> dict:

    cached = load_cached_board()
    cached_age = (
        cached_board_age_seconds(cached)
        if cached
        else None
    )

    if cached_board_is_fresh(
        cached,
        matchday=matchday,
        seconds_to_deadline=seconds_to_deadline,
    ):
        return board_with_cache_status(
            cached,
            status="HIT",
            seconds_to_deadline=seconds_to_deadline,
            age_seconds=cached_age,
        )

    roster = build_roster_records(
        snapshot
    )

    # SIN PLANTILLA NO SE ESCRIBE NADA.
    #
    # La otra mitad del mismo fallo. Con un snapshot sin
    # `my_team` este bucle no produce ninguna fila, y aun asi el
    # fichero se guardaba: un tablero de cero jugadores, con
    # `error: null` y jornada correcta, que despues se servia
    # como cache valida.
    #
    # Un snapshot sin plantilla es un snapshot roto, no una
    # plantilla vacia. Se dice, se conserva el tablero anterior
    # si lo hay, y no se pisa el disco.
    if not roster:

        cached_vacio = load_cached_board()

        motivo = (
            "El snapshot llego sin plantilla ('my_team' vacio): "
            "no se puede construir el tablero de titularidad y "
            "no se sobrescribe el anterior."
        )

        if cached_vacio and (cached_vacio.get("players") or []):
            return board_with_cache_status(
                cached_vacio,
                status="STALE_FALLBACK",
                seconds_to_deadline=seconds_to_deadline,
                age_seconds=cached_board_age_seconds(
                    cached_vacio
                ),
                error=motivo,
            )

        return {
            "version": "V11.2.4",
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "matchday": matchday,
            "metadata": {},
            "players": [],
            "cache": {
                "status": "NO_ROSTER",
                "age_seconds": None,
                "ttl_seconds": calculate_refresh_seconds(
                    seconds_to_deadline
                ),
                "error": motivo,
            },
        }

    session = requests.Session()

    try:
        jp = build_jp_signals(
            snapshot,
            matchday,
            seconds_to_deadline,
        )

        af, af_meta = build_af_signals(
            snapshot,
            roster,
            matchday,
            session,
        )

        ff, ff_meta = build_ff_signals(
            snapshot,
            roster,
            matchday,
            session,
        )
    except Exception as error:
        if cached:
            return board_with_cache_status(
                cached,
                status="STALE_FALLBACK",
                seconds_to_deadline=seconds_to_deadline,
                age_seconds=cached_age,
                error=(
                    f"{type(error).__name__}: {error}"
                ),
            )
        raise

    players = []

    for player in roster:

        player_id = int(
            player[
                "id"
            ]
        )

        signals = [
            value
            for value in (
                jp.get(
                    player_id
                ),
                ff.get(
                    player_id
                ),
                af.get(
                    player_id
                ),
            )
            if value
        ]

        aggregate = consensus(
            signals
        )

        players.append(
            {
                "player_id":
                    player_id,

                "player_name":
                    player.get(
                        "name"
                    ),

                "team":
                    player.get(
                        "team"
                    ),

                **aggregate,

                "sources":
                    {
                        "JORNADA_PERFECTA":
                            jp.get(
                                player_id
                            ),

                        "FUTBOLFANTASY":
                            ff.get(
                                player_id
                            ),

                        "ANALITICA_FANTASY":
                            af.get(
                                player_id
                            ),
                    },
            }
        )

    output = {
        "version":
            "V11.2.4",

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "matchday":
            matchday,

        "metadata":
            {
                "analitica":
                    af_meta,

                "futbolfantasy":
                    ff_meta,
            },

        "players":
            players,

        "cache": {
            "status":
                "REFRESHED",

            "age_seconds":
                0.0,

            "ttl_seconds":
                calculate_refresh_seconds(
                    seconds_to_deadline
                ),

            "error":
                None,
        },
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output
