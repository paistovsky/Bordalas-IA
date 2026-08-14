from __future__ import annotations

import json
import re
import time
import unicodedata

from difflib import SequenceMatcher

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path
from urllib.parse import (
    urljoin,
    urlparse,
)

import requests

from urllib.parse import urljoin
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURACION
# ============================================================


BASE_URL = (
    "https://www.jornadaperfecta.com"
)

LINEUPS_URL = (
    f"{BASE_URL}/onces-posibles/"
)

DATA_DIRECTORY = (
    Path("data")
    / "intelligence"
)

DATA_FILE = (
    DATA_DIRECTORY
    / "jornada_perfecta_lineups.json"
)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),

    "Accept-Language":
        "es-ES,es;q=0.9,en;q=0.7",

    "Cache-Control":
        "no-cache",
}


MATCHDAY_RE = re.compile(
    r"\bJornada\s+(\d{1,2})\b",
    re.IGNORECASE,
)


LEGEND_RE = re.compile(
    r"Titular\s+Suplente\s+y\s+juega\s+Sin\s+minutos",
    re.IGNORECASE,
)


PLAYER_HREF_RE = re.compile(
    r"/jugador/",
    re.IGNORECASE,
)


# No queremos recorrer toda la web.
MAX_CRAWL_PAGES = 90
MAX_CRAWL_DEPTH = 4

REQUEST_TIMEOUT = 25


# ============================================================
# NORMALIZACION
# ============================================================


def normalize_text(
    value: str | None,
) -> str:

    if value is None:
        return ""

    value = str(
        value
    ).strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character

        for character in value

        if not unicodedata.combining(
            character
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


def canonical_team_key(
    value: str | None,
) -> str:

    value = normalize_text(
        value
    )

    removable = {
        "cf",
        "fc",
        "rc",
        "rcd",
        "ud",
        "club",
        "de",
        "del",
        "la",
    }

    tokens = [
        token

        for token in value.split()

        if token not in removable
    ]

    aliases = {
        "barca":
            "barcelona",

        "atletico madrid":
            "atletico",

        "athletic club":
            "athletic",

        "real sociedad":
            "sociedad",

        "r sociedad":
            "sociedad",

        "deportivo alaves":
            "alaves",

        "racing club":
            "racing",

        "racing santander":
            "racing",

        "deportivo coruna":
            "deportivo",

        "deportivo la coruna":
            "deportivo",
    }

    key = " ".join(
        tokens
    )

    return aliases.get(
        key,
        key,
    )


# ============================================================
# HTTP
# ============================================================


def build_session() -> requests.Session:

    session = (
        requests.Session()
    )

    session.headers.update(
        DEFAULT_HEADERS
    )

    return session


def fetch_html(
    session: requests.Session,
    url: str,
) -> str:

    response = (
        session.get(
            url,
            timeout=
                REQUEST_TIMEOUT,
        )
    )

    response.raise_for_status()

    response.encoding = (
        response.encoding
        or "utf-8"
    )

    return response.text


# ============================================================
# CACHE / FRESHNESS
# ============================================================


def ensure_directory() -> None:

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def parse_iso_datetime(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    try:

        result = (
            datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if result.tzinfo is None:

        result = (
            result.replace(
                tzinfo=
                    timezone.utc,
            )
        )

    return result.astimezone(
        timezone.utc
    )


def load_existing_file() -> dict | None:

    if not DATA_FILE.exists():
        return None

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:

            value = (
                json.load(
                    file
                )
            )

        if isinstance(
            value,
            dict,
        ):

            return value

    except (
        OSError,
        json.JSONDecodeError,
    ):
        pass

    return None


def calculate_refresh_seconds(
    seconds_to_deadline: int | None,
) -> int:
    """
    El Autopilot de GitHub corre cada 30 minutos.

    Lejos del cierre no necesitamos golpear Jornada Perfecta
    en cada ciclo. Cerca de T-15 queremos información fresca.
    """

    if seconds_to_deadline is None:
        return 2 * 3600

    if seconds_to_deadline <= 12 * 3600:
        return 20 * 60

    if seconds_to_deadline <= 48 * 3600:
        return 30 * 60

    if seconds_to_deadline <= 7 * 24 * 3600:
        return 2 * 3600

    return 6 * 3600


def cache_is_fresh(
    current: dict | None,
    target_matchday: int | None,
    seconds_to_deadline: int | None,
) -> bool:

    if not current:
        return False

    if int(
        current.get(
            "round",
            -1,
        )
        or -1
    ) != int(
        target_matchday
        or -2
    ):
        return False

    updated_at = (
        parse_iso_datetime(
            current.get(
                "updated_at"
            )
        )
    )

    if updated_at is None:
        return False

    age_seconds = (
        datetime.now(
            timezone.utc
        )
        - updated_at
    ).total_seconds()

    return (
        age_seconds
        < calculate_refresh_seconds(
            seconds_to_deadline
        )
    )


# ============================================================
# METADATA DE PAGINA
# ============================================================


def extract_matchday(
    soup: BeautifulSoup,
) -> int | None:

    title = (
        soup.title.get_text(
            " ",
            strip=True,
        )
        if soup.title
        else ""
    )

    match = (
        MATCHDAY_RE.search(
            title
        )
    )

    if match is None:

        text = (
            soup.get_text(
                " ",
                strip=True,
            )[
                :5000
            ]
        )

        match = (
            MATCHDAY_RE.search(
                text
            )
        )

    if match is None:
        return None

    value = int(
        match.group(
            1
        )
    )

    if not 1 <= value <= 38:
        return None

    return value


def extract_teams(
    soup: BeautifulSoup,
) -> tuple[
    str | None,
    str | None,
]:

    title = (
        soup.title.get_text(
            " ",
            strip=True,
        )
        if soup.title
        else ""
    )

    # Normalmente:
    # "Barcelona - Athletic | Alineaciones probables Jornada 1"
    if "|" in title:

        prefix = (
            title.split(
                "|",
                1,
            )[
                0
            ].strip()
        )

        if " - " in prefix:

            home, away = (
                prefix.split(
                    " - ",
                    1,
                )
            )

            return (
                home.strip(),
                away.strip(),
            )

    # Fallback: buscar texto inicial de la página.
    text = (
        soup.get_text(
            "\n",
            strip=True,
        )
    )

    lines = [
        line.strip()

        for line in text.splitlines()

        if line.strip()
    ]

    for index, line in enumerate(
        lines[
            :80
        ]
    ):

        if (
            MATCHDAY_RE.search(
                line
            )
            and
            index + 2
            < len(
                lines
            )
        ):

            return (
                lines[
                    index + 1
                ],
                lines[
                    index + 2
                ],
            )

    return (
        None,
        None,
    )


def extract_match_links(
    soup: BeautifulSoup,
) -> list[str]:

    urls = []

    seen = set()

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = str(
            anchor.get(
                "href"
            )
            or ""
        )

        if (
            "/partido/"
            not in href
        ):
            continue

        url = (
            urljoin(
                BASE_URL,
                href,
            )
        )

        parsed = (
            urlparse(
                url
            )
        )

        # Solo dominio Jornada Perfecta.
        if (
            parsed.netloc
            and
            "jornadaperfecta.com"
            not in parsed.netloc
        ):
            continue

        if url in seen:
            continue

        seen.add(
            url
        )

        urls.append(
            url
        )

    return urls


# ============================================================
# PREDICCION DE JUGADORES
# ============================================================


def is_player_anchor(
    tag,
) -> bool:

    if (
        getattr(
            tag,
            "name",
            None,
        )
        != "a"
    ):

        return False

    href = str(
        tag.get(
            "href"
        )
        or ""
    )

    return bool(
        PLAYER_HREF_RE.search(
            href
        )
    )


def nearest_team_image_reached(
    tag,
    team_name: str | None,
) -> bool:

    if not team_name:
        return False

    if (
        getattr(
            tag,
            "name",
            None,
        )
        != "img"
    ):

        return False

    alt = (
        tag.get(
            "alt"
        )
    )

    if not alt:
        return False

    return (
        canonical_team_key(
            alt
        )
        ==
        canonical_team_key(
            team_name
        )
    )


def is_numeric_probability_text(
    value: str,
) -> bool:

    value = " ".join(
        str(
            value
            or ""
        ).split()
    )

    return bool(
        re.fullmatch(
            r"\d{1,3}%?",
            value,
        )
    )


def clean_player_name_text(
    value: str,
) -> str:

    value = " ".join(
        str(
            value
            or ""
        ).split()
    )

    if not value:
        return ""

    # No usar textos de tarjetas FIFA / lesiones como nombre.
    lowered = (
        value.lower()
    )

    noisy_tokens = {
        "lesionado",
        "sancionado",
        "duda",
        "baja",
        "alta",
        "fifa-card",
    }

    if any(
        token in lowered
        for token in noisy_tokens
    ):

        return ""

    if is_numeric_probability_text(
        value
    ):

        return ""

    return value


def get_unique_player_links(
    container,
) -> list[dict]:
    """
    Jornada Perfecta repite cada jugador con el mismo href:

        <a class="player">50</a>
        <a>Gordon</a>

    o:

        <a class="player"></a>
        <a>Yamal</a>

    Agrupamos por href y elegimos como nombre el texto
    descriptivo, no el porcentaje.
    """

    grouped = {}

    for anchor in container.find_all(
        "a",
        href=True,
    ):

        href = str(
            anchor.get(
                "href"
            )
            or ""
        )

        if "/jugador/" not in href:
            continue

        classes = set(
            anchor.get(
                "class",
                [],
            )
            or []
        )

        text_value = " ".join(
            anchor.get_text(
                " ",
                strip=True,
            ).split()
        )

        record = grouped.setdefault(
            href,
            {
                "href":
                    href,

                "name":
                    "",

                "probability":
                    None,

                "has_player_marker":
                    False,

                "empty_player_marker":
                    False,

                "numeric_player_marker":
                    False,

                "raw_texts":
                    [],
            },
        )

        if text_value:

            record[
                "raw_texts"
            ].append(
                text_value
            )

        if (
            "player"
            in classes
        ):

            record[
                "has_player_marker"
            ] = True

            if text_value:

                record[
                    "numeric_player_marker"
                ] = bool(
                    is_numeric_probability_text(
                        text_value
                    )
                )

            else:

                record[
                    "empty_player_marker"
                ] = True

        # El anchor class=player contiene el porcentaje
        # cuando hay una alternativa.
        if (
            "player"
            in classes
            and
            is_numeric_probability_text(
                text_value
            )
        ):

            probability = int(
                text_value.rstrip(
                    "%"
                )
            )

            if 0 <= probability <= 100:

                record[
                    "probability"
                ] = probability

        candidate_name = (
            clean_player_name_text(
                text_value
            )
        )

        # Preferimos el anchor sin class=player, que en el HTML
        # real contiene "Yamal", "M. Bernal", etc.
        if (
            candidate_name
            and
            (
                "player"
                not in classes
                or
                not record[
                    "name"
                ]
            )
        ):

            record[
                "name"
            ] = candidate_name

    return [
        item

        for item in grouped.values()

        if item[
            "name"
        ]
    ]


def count_unique_player_links(
    container,
) -> int:

    return len(
        get_unique_player_links(
            container
        )
    )


def find_team_pitch_containers(
    soup: BeautifulSoup,
) -> list:
    """
    Jornada Perfecta renderiza cada once dentro de:

        <div class="campo-futbol lineas-X">

    Cada bloque contiene exactamente los jugadores del once
    probable de UN equipo, más posibles alternativas.
    """

    return [
        container

        for container in soup.find_all(
            "div",
            class_=lambda value:
                value
                and
                "campo-futbol"
                in (
                    value
                    if isinstance(
                        value,
                        list,
                    )
                    else str(
                        value
                    ).split()
                ),
        )
    ]


def get_pitch_team_name(
    container,
) -> str | None:
    """
    El bloque campo-futbol no siempre lleva el nombre del equipo.
    Lo inferimos por proximidad hacia atrás buscando el primer
    escudo/imagen con alt de equipo conocido.
    """

    current = (
        container
    )

    examined = 0

    while current is not None:

        previous = (
            current.find_previous(
                "img"
            )
        )

        if previous is None:
            break

        examined += 1

        if examined > 12:
            break

        alt = (
            previous.get(
                "alt"
            )
        )

        if alt:

            # Ignorar imágenes de jugadores: suelen aparecer
            # dentro de campo-futbol, mientras que el escudo
            # anterior suele ser el equipo.
            classes = set(
                previous.get(
                    "class",
                    [],
                )
                or []
            )

            if (
                "shield-item"
                in classes
            ):

                return str(
                    alt
                )

        current = (
            previous
        )

    return None


def build_signals_from_pitch(
    container,
    team_name: str | None,
    url: str,
) -> list[dict]:

    players = get_unique_player_links(
        container
    )

    base_candidates = [
        item
        for item in players
        if (
            item.get(
                "empty_player_marker",
                False,
            )
            and
            item.get(
                "probability"
            )
            is None
        )
    ]

    base_xi_hrefs = set()

    if len(base_candidates) == 11:
        base_xi_hrefs = {
            item["href"]
            for item in base_candidates
        }

    signals = []

    for item in players:

        probability = item.get(
            "probability"
        )

        href = item.get(
            "href"
        )

        if probability is not None:

            probability = int(
                probability
            )

            if probability >= 67:
                status = "PROBABLE"
            elif probability <= 40:
                status = "SUPLENTE"
            else:
                status = "DUDA"

            confidence = max(
                40,
                min(
                    probability,
                    95,
                ),
            )

            parser_role = (
                "EXPLICIT_PERCENT"
            )

        elif href in base_xi_hrefs:

            status = "TITULAR"
            confidence = 82
            parser_role = (
                "BASE_XI_STRUCTURAL"
            )

        else:

            status = "UNKNOWN"
            confidence = 0
            parser_role = (
                "UNPROVEN_NO_PERCENT"
            )

        signals.append(
            {
                "name":
                    item["name"],

                "status":
                    status,

                "confidence":
                    confidence,

                "team":
                    team_name,

                "source":
                    "JORNADA_PERFECTA",

                "note": (
                    "JP pitch discovery: "
                    f"{parser_role}; {url}"
                ),

                "source_url":
                    url,

                "player_url":
                    (
                        urljoin(
                            BASE_URL,
                            href,
                        )
                        if href
                        else None
                    ),

                "jp_probability":
                    probability,

                "jp_parser_role":
                    parser_role,
            }
        )

    return signals


def parse_player_profile_pronostico(
    html: str,
) -> dict | None:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    page_text = soup.get_text(
        " ",
        strip=True,
    )

    match = re.search(
        r"Pron[oó]stico\s*:\s*"
        r"(Titular|Suplente|Probable|Duda|"
        r"No\s+convocado|Sin\s+minutos)",
        page_text,
        re.IGNORECASE,
    )

    if not match:
        return None

    raw = normalize_text(
        match.group(1)
    )

    mapping = {
        "titular":
            ("TITULAR", 96),

        "probable":
            ("PROBABLE", 84),

        "duda":
            ("DUDA", 60),

        "suplente":
            ("SUPLENTE", 96),

        "no convocado":
            ("NO_CONVOCADO", 99),

        "sin minutos":
            ("SUPLENTE", 96),
    }

    status, confidence = mapping.get(
        raw,
        ("UNKNOWN", 0),
    )

    return {
        "status":
            status,

        "confidence":
            confidence,

        "raw_pronostico":
            match.group(1),
    }


def verify_signals_with_player_profiles(
    session: requests.Session,
    signals: list[dict],
) -> tuple[list[dict], dict]:

    verified = []
    cache = {}

    checked = 0
    explicit = 0
    overrides = 0
    errors = []

    for signal in signals:

        player_url = signal.get(
            "player_url"
        )

        if not player_url:

            verified.append(
                signal
            )
            continue

        checked += 1

        try:

            if player_url not in cache:

                profile_html = fetch_html(
                    session,
                    player_url,
                )

                cache[
                    player_url
                ] = (
                    parse_player_profile_pronostico(
                        profile_html
                    )
                )

                time.sleep(
                    0.04
                )

            profile = cache[
                player_url
            ]

        except Exception as error:

            errors.append(
                f"{player_url}: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            verified.append(
                signal
            )
            continue

        if not profile:

            verified.append(
                {
                    **signal,

                    "jp_profile_checked":
                        True,

                    "jp_profile_pronostico":
                        None,
                }
            )
            continue

        explicit += 1

        previous = signal.get(
            "status"
        )

        if previous != profile["status"]:
            overrides += 1

        verified.append(
            {
                **signal,

                "status":
                    profile["status"],

                "confidence":
                    profile["confidence"],

                "source_url":
                    player_url,

                "note": (
                    "JP PLAYER PROFILE SOURCE OF TRUTH: "
                    f"Pronostico={profile['raw_pronostico']}; "
                    f"{player_url}"
                ),

                "jp_profile_checked":
                    True,

                "jp_profile_pronostico":
                    profile[
                        "raw_pronostico"
                    ],

                "jp_structural_status_before_profile":
                    previous,

                "jp_parser_role":
                    "PLAYER_PROFILE_PRONOSTICO",
            }
        )

    return (
        verified,
        {
            "checked":
                checked,

            "explicit":
                explicit,

            "overrides":
                overrides,

            "errors":
                errors[:10],
        },
    )



def build_page_signals(
    soup: BeautifulSoup,
    url: str,
) -> list[dict]:

    home, away = (
        extract_teams(
            soup
        )
    )

    known_teams = [
        team

        for team in (
            home,
            away,
        )

        if team
    ]

    pitches = (
        find_team_pitch_containers(
            soup
        )
    )

    signals = []

    used_team_keys = set()

    for container in pitches:

        player_count = (
            count_unique_player_links(
                container
            )
        )

        # Un once probable real debe rondar 11 jugadores.
        if not 8 <= player_count <= 16:
            continue

        inferred_team = (
            get_pitch_team_name(
                container
            )
        )

        team_name = None

        if inferred_team:

            inferred_key = (
                canonical_team_key(
                    inferred_team
                )
            )

            for candidate in known_teams:

                if (
                    canonical_team_key(
                        candidate
                    )
                    == inferred_key
                ):

                    team_name = (
                        candidate
                    )
                    break

        # Fallback estable:
        # primera cancha -> local
        # segunda cancha -> visitante
        if team_name is None:

            for candidate in known_teams:

                key = (
                    canonical_team_key(
                        candidate
                    )
                )

                if key not in used_team_keys:

                    team_name = (
                        candidate
                    )
                    break

        if team_name is None:
            continue

        team_key = (
            canonical_team_key(
                team_name
            )
        )

        if team_key in used_team_keys:
            continue

        used_team_keys.add(
            team_key
        )

        signals.extend(
            build_signals_from_pitch(
                container=
                    container,

                team_name=
                    team_name,

                url=
                    url,
            )
        )

        if len(
            used_team_keys
        ) >= 2:
            break

    return signals


# ============================================================
# MATCHING CON BIWENGER
# ============================================================


def get_catalog_team_name(
    snapshot: dict,
    team_id,
) -> str | None:

    if team_id is None:
        return None

    teams = (
        snapshot
        .get(
            "catalog",
            {},
        )
        .get(
            "data",
            {},
        )
        .get(
            "teams",
            {},
        )
        or {}
    )

    team = (
        teams.get(
            str(
                team_id
            )
        )
        or {}
    )

    return team.get(
        "name"
    )


def build_roster_records(
    snapshot: dict,
) -> list[dict]:

    records = []

    for player in snapshot.get(
        "my_team",
        [],
    ):

        records.append(
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

                "normalized_name":
                    normalize_text(
                        player.get(
                            "name"
                        )
                    ),

                "team":
                    get_catalog_team_name(
                        snapshot,
                        player.get(
                            "teamID"
                        ),
                    ),

                "team_key":
                    canonical_team_key(
                        get_catalog_team_name(
                            snapshot,
                            player.get(
                                "teamID"
                            ),
                        )
                    ),
            }
        )

    return records


def name_similarity(
    left: str,
    right: str,
) -> float:

    left_n = (
        normalize_text(
            left
        )
    )

    right_n = (
        normalize_text(
            right
        )
    )

    if not left_n or not right_n:
        return 0.0

    if left_n == right_n:
        return 1.0

    if (
        left_n in right_n
        or
        right_n in left_n
    ):

        return 0.92

    left_tokens = (
        left_n.split()
    )

    right_tokens = (
        right_n.split()
    )

    # "H. Rincon" -> "Hugo Rincon"
    if (
        left_tokens
        and
        right_tokens
        and
        left_tokens[
            -1
        ]
        ==
        right_tokens[
            -1
        ]
    ):

        return 0.86

    return (
        SequenceMatcher(
            None,
            left_n,
            right_n,
        ).ratio()
    )


def jp_identity_aliases(
    signal: dict,
) -> list[str]:
    aliases = []

    raw_name = normalize_text(
        signal.get("name")
    )

    if raw_name:
        aliases.append(raw_name)

    player_url = str(
        signal.get("player_url")
        or signal.get("source_url")
        or ""
    )

    if "/jugador/" in player_url:
        slug = (
            player_url
            .split("/jugador/", 1)[1]
            .split("/", 1)[0]
            .split("?", 1)[0]
        )

        slug_name = normalize_text(
            slug.replace("-", " ")
        )

        if slug_name and slug_name not in aliases:
            aliases.append(slug_name)

    return aliases


def strict_identity_similarity(
    external_name: str,
    roster_name: str,
) -> float:
    left = normalize_text(external_name)
    right = normalize_text(roster_name)

    if not left or not right:
        return 0.0

    if left == right:
        return 1.0

    left_tokens = left.split()
    right_tokens = right.split()

    if len(left_tokens) == 1:
        token = left_tokens[0]

        if right_tokens and token == right_tokens[-1]:
            return 0.90

        return 0.0

    if len(right_tokens) == 1:
        token = right_tokens[0]

        if left_tokens and token == left_tokens[-1]:
            return 0.90

        return 0.0

    if left_tokens[-1] != right_tokens[-1]:
        return (
            SequenceMatcher(
                None,
                left,
                right,
            ).ratio()
            * 0.70
        )

    return max(
        0.86,
        SequenceMatcher(
            None,
            left,
            right,
        ).ratio(),
    )


def attach_biwenger_identity(
    signals: list[dict],
    snapshot: dict,
) -> tuple[
    list[dict],
    set[int],
    set[str],
]:
    roster = build_roster_records(
        snapshot
    )

    result = []
    matched_ids = set()

    parsed_team_keys = {
        canonical_team_key(
            signal.get("team")
        )
        for signal in signals
        if signal.get("team")
    }

    for signal in signals:
        signal_team_key = canonical_team_key(
            signal.get("team")
        )

        if signal_team_key:
            candidates = [
                player
                for player in roster
                if (
                    player.get("team_key")
                    and
                    player["team_key"] == signal_team_key
                    and
                    player["id"] not in matched_ids
                )
            ]
        else:
            candidates = [
                player
                for player in roster
                if player["id"] not in matched_ids
            ]

        if not candidates:
            continue

        aliases = jp_identity_aliases(
            signal
        )

        scored = []

        for player in candidates:
            alias_scores = [
                strict_identity_similarity(
                    alias,
                    player["name"],
                )
                for alias in aliases
            ]

            score = max(alias_scores) if alias_scores else 0.0

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
            continue

        best_score, best = scored[0]
        second_score = (
            scored[1][0]
            if len(scored) > 1
            else 0.0
        )

        if best_score < 0.80:
            continue

        if (
            second_score >= 0.80
            and
            (best_score - second_score) < 0.08
        ):
            continue

        matched_ids.add(
            best["id"]
        )

        result.append(
            {
                **signal,

                "biwenger_id":
                    best["id"],

                "name":
                    best["name"],

                "jp_name":
                    signal.get("name"),

                "match_confidence":
                    round(
                        best_score * 100,
                        1,
                    ),

                "identity_aliases":
                    aliases,

                "identity_team_strict":
                    bool(signal_team_key),
            }
        )

    counts_by_team = {}

    for signal in signals:
        key = canonical_team_key(
            signal.get("team")
        )

        if not key:
            continue

        counts_by_team[key] = (
            counts_by_team.get(
                key,
                0,
            )
            + 1
        )

    for player in roster:
        if player["id"] in matched_ids:
            continue

        team_key = player.get(
            "team_key"
        )

        if (
            not team_key
            or
            counts_by_team.get(
                team_key,
                0,
            )
            < 11
        ):
            continue

        result.append(
            {
                "biwenger_id":
                    player["id"],

                "name":
                    player["name"],

                "jp_name":
                    None,

                "status":
                    "SUPLENTE",

                "confidence":
                    72,

                "team":
                    player["team"],

                "source":
                    "JORNADA_PERFECTA",

                "note":
                    (
                        "Jugador no localizado entre las "
                        "senales JP de su propio equipo."
                    ),

                "match_confidence":
                    100.0,

                "identity_team_strict":
                    True,

                "jp_parser_role":
                    "TEAM_ABSENCE_CONSERVATIVE",
            }
        )

    return (
        result,
        matched_ids,
        parsed_team_keys,
    )

def crawl_target_matchday(
    session: requests.Session,
    target_matchday: int,
) -> dict:

    main_html = (
        fetch_html(
            session,
            LINEUPS_URL,
        )
    )

    main_soup = (
        BeautifulSoup(
            main_html,
            "html.parser",
        )
    )

    queue = [
        (
            url,
            0,
        )

        for url in extract_match_links(
            main_soup
        )
    ]

    visited = set()

    target_pages = []

    discovered_by_round = {}

    errors = []

    while (
        queue
        and
        len(
            visited
        )
        < MAX_CRAWL_PAGES
    ):

        url, depth = (
            queue.pop(
                0
            )
        )

        if url in visited:
            continue

        visited.add(
            url
        )

        try:

            html = (
                fetch_html(
                    session,
                    url,
                )
            )

            soup = (
                BeautifulSoup(
                    html,
                    "html.parser",
                )
            )

        except Exception as error:

            errors.append(
                f"{url}: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            continue

        matchday = (
            extract_matchday(
                soup
            )
        )

        if matchday is None:
            continue

        discovered_by_round[
            matchday
        ] = (
            discovered_by_round.get(
                matchday,
                0,
            )
            + 1
        )

        if (
            matchday
            == target_matchday
        ):

            target_pages.append(
                (
                    url,
                    soup,
                )
            )

            # Cuando ya tenemos los 10 partidos no hace falta
            # seguir expandiendo el grafo.
            if len(
                target_pages
            ) >= 10:

                break

        if depth >= MAX_CRAWL_DEPTH:
            continue

        # No necesitamos alejarnos demasiado del target.
        if matchday > target_matchday + 1:
            continue

        for next_url in extract_match_links(
            soup
        ):

            if next_url in visited:
                continue

            queue.append(
                (
                    next_url,
                    depth + 1,
                )
            )

        # Pequeño respiro para no bombardear la web.
        time.sleep(
            0.05
        )

    # Deduplicar por URL.
    unique = {}

    for url, soup in target_pages:

        unique[
            url
        ] = soup

    return {
        "pages":
            list(
                unique.items()
            ),

        "visited_pages":
            len(
                visited
            ),

        "discovered_by_round":
            discovered_by_round,

        "errors":
            errors,
    }


# ============================================================
# REFRESH PRINCIPAL
# ============================================================


def refresh_jornada_perfecta_data(
    snapshot: dict,
    target_matchday: int | None,
    seconds_to_deadline: int | None = None,
    force: bool = False,
) -> dict:

    if target_matchday is None:

        raise RuntimeError(
            "No se conoce la jornada objetivo."
        )

    target_matchday = int(
        target_matchday
    )

    existing = (
        load_existing_file()
    )

    if (
        not force
        and
        cache_is_fresh(
            current=
                existing,

            target_matchday=
                target_matchday,

            seconds_to_deadline=
                seconds_to_deadline,
        )
    ):

        return {
            "status":
                "CACHE",

            "data":
                existing,

            "refreshed":
                False,
        }

    session = (
        build_session()
    )

    crawl = (
        crawl_target_matchday(
            session=
                session,

            target_matchday=
                target_matchday,
        )
    )

    pages = (
        crawl[
            "pages"
        ]
    )

    if not pages:

        raise RuntimeError(
            "Jornada Perfecta no ha devuelto paginas "
            f"para la Jornada {target_matchday}. "
            f"Rondas descubiertas: "
            f"{crawl.get('discovered_by_round')}"
        )

    raw_signals = []

    page_summaries = []

    for url, soup in pages:

        page_signals = (
            build_page_signals(
                soup=
                    soup,

                url=
                    url,
            )
        )

        home, away = (
            extract_teams(
                soup
            )
        )

        raw_signals.extend(
            page_signals
        )

        page_summaries.append(
            {
                "url":
                    url,

                "home":
                    home,

                "away":
                    away,

                "signals":
                    len(
                        page_signals
                    ),
            }
        )

    (
        raw_signals,
        profile_metadata,
    ) = (
        verify_signals_with_player_profiles(
            session=
                session,

            signals=
                raw_signals,
        )
    )

    (
        players,
        matched_ids,
        parsed_team_keys,
    ) = (
        attach_biwenger_identity(
            signals=
                raw_signals,

            snapshot=
                snapshot,
        )
    )

    now = (
        datetime.now(
            timezone.utc
        )
    )

    payload = {
        "source":
            "JORNADA_PERFECTA",

        "updated_at":
            now.isoformat(),

        "round":
            target_matchday,

        "players":
            players,

        "metadata": {
            "target_matchday":
                target_matchday,

            "pages_found":
                len(
                    pages
                ),

            "pages_visited":
                crawl.get(
                    "visited_pages"
                ),

            "raw_signals":
                len(
                    raw_signals
                ),

            "jp_profile_checked":
                profile_metadata.get(
                    "checked",
                    0,
                ),

            "jp_profile_explicit":
                profile_metadata.get(
                    "explicit",
                    0,
                ),

            "jp_profile_overrides":
                profile_metadata.get(
                    "overrides",
                    0,
                ),

            "matched_roster_players":
                len(
                    matched_ids
                ),

            "parsed_teams":
                len(
                    parsed_team_keys
                ),

            "discovered_by_round":
                crawl.get(
                    "discovered_by_round"
                ),

            "page_summaries":
                page_summaries,

            "errors":
                crawl.get(
                    "errors",
                    [],
                )[
                    :10
                ],
        },
    }

    ensure_directory()

    temporary = (
        DATA_FILE.with_suffix(
            ".json.tmp"
        )
    )

    with open(
        temporary,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary.replace(
        DATA_FILE
    )

    return {
        "status":
            "REFRESHED",

        "data":
            payload,

        "refreshed":
            True,
    }
