from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


MADRID_TZ = ZoneInfo("Europe/Madrid")

# ============================================================
# FUENTES
# ============================================================
#
# IMPORTANTE:
# La página completa de calendario de LALIGA puede renderizar
# buena parte del contenido mediante JavaScript. requests no
# ejecuta JavaScript, por lo que no la usamos como única fuente.
#
# Estrategia:
#
# 1. MARCA:
#    calendario HTML estático -> base amplia de jornadas.
#
# 2. LALIGA:
#    página server-rendered que ya hemos comprobado que expone
#    la jornada/horarios actuales -> autoridad preferente sobre
#    los partidos que consiga devolver.
#
# Cuando ambas fuentes contienen el mismo partido, LALIGA gana.
# ============================================================


MARCA_CALENDAR_URL = (
    "https://us.marca.com/soccer/laliga/calendario.shtml"
)

LALIGA_CURRENT_URL = (
    "https://www.laliga.com/donde-ver-laliga-easports"
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

DATE_PATTERNS = (
    re.compile(
        r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b"
    ),
    re.compile(
        r"\b(\d{1,2})[./](\d{1,2})\b"
    ),
)

TIME_RE = re.compile(
    r"\b([01]?\d|2[0-3]):([0-5]\d)\b"
)


# ============================================================
# TEXTO / FECHAS
# ============================================================


def clean_text(
    value: str | None,
) -> str:

    return " ".join(
        str(
            value
            or ""
        )
        .replace(
            "\xa0",
            " ",
        )
        .split()
    )


def parse_datetime_from_text(
    text: str,
    season_start_year: int,
) -> datetime | None:

    text = clean_text(
        text
    )

    time_match = (
        TIME_RE.search(
            text
        )
    )

    if time_match is None:
        return None

    hour = int(
        time_match.group(
            1
        )
    )

    minute = int(
        time_match.group(
            2
        )
    )

    full_date = (
        DATE_PATTERNS[
            0
        ].search(
            text
        )
    )

    if full_date is not None:

        day = int(
            full_date.group(
                1
            )
        )

        month = int(
            full_date.group(
                2
            )
        )

        year = int(
            full_date.group(
                3
            )
        )

    else:

        short_date = (
            DATE_PATTERNS[
                1
            ].search(
                text
            )
        )

        if short_date is None:
            return None

        day = int(
            short_date.group(
                1
            )
        )

        month = int(
            short_date.group(
                2
            )
        )

        year = (
            season_start_year
            if month >= 8
            else season_start_year + 1
        )

    try:

        return datetime(
            year,
            month,
            day,
            hour,
            minute,
            tzinfo=MADRID_TZ,
        )

    except ValueError:
        return None


def extract_matchday_number(
    text: str,
) -> int | None:

    match = (
        MATCHDAY_RE.search(
            clean_text(
                text
            )
        )
    )

    if match is None:
        return None

    matchday = int(
        match.group(
            1
        )
    )

    if not 1 <= matchday <= 38:
        return None

    return matchday


def split_match_text(
    text: str,
) -> tuple[str, str] | None:

    text = clean_text(
        text
    )

    parts = re.split(
        r"\s+(?:VS\.?|V\.?)\s+",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )

    if len(
        parts
    ) != 2:
        return None

    home = clean_text(
        parts[
            0
        ]
    )

    away = clean_text(
        parts[
            1
        ]
    )

    if not home or not away:
        return None

    return (
        home,
        away,
    )


# ============================================================
# NORMALIZACION DE NOMBRES
# ============================================================


TEAM_ALIASES = {
    "alaves":
        "Deportivo Alavés",

    "deportivo alaves":
        "Deportivo Alavés",

    "getafe":
        "Getafe CF",

    "sevilla":
        "Sevilla FC",

    "rayo":
        "Rayo Vallecano",

    "racing":
        "R. Racing Club",

    "villarreal":
        "Villarreal CF",

    "espanyol":
        "RCD Espanyol de Barcelona",

    "levante":
        "Levante UD",

    "celta":
        "Celta",

    "osasuna":
        "CA Osasuna",

    "deportivo":
        "RC Deportivo",

    "elche":
        "Elche CF",

    "atletico":
        "Atlético de Madrid",

    "atletico de madrid":
        "Atlético de Madrid",

    "malaga":
        "Málaga CF",

    "valencia":
        "Valencia CF",

    "betis":
        "Real Betis",

    "real madrid":
        "Real Madrid",

    "real sociedad":
        "Real Sociedad",

    "r sociedad":
        "Real Sociedad",

    "r. sociedad":
        "Real Sociedad",

    "barcelona":
        "FC Barcelona",

    "fc barcelona":
        "FC Barcelona",

    "athletic":
        "Athletic Club",

    "athletic club":
        "Athletic Club",
}


def normalize_for_key(
    value: str,
) -> str:

    value = (
        clean_text(
            value
        )
        .lower()
    )

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }

    for old, new in replacements.items():

        value = (
            value.replace(
                old,
                new,
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


def canonical_team_name(
    value: str,
) -> str:

    cleaned = clean_text(
        value
    )

    normalized = (
        normalize_for_key(
            cleaned
        )
    )

    return (
        TEAM_ALIASES.get(
            normalized,
            cleaned,
        )
    )


def match_key(
    match: dict,
) -> tuple[int, str, str]:

    return (
        int(
            match[
                "matchday"
            ]
        ),

        normalize_for_key(
            match[
                "home"
            ]
        ),

        normalize_for_key(
            match[
                "away"
            ]
        ),
    )


# ============================================================
# FILAS
# ============================================================


def row_to_match(
    cells: list[str],
    matchday: int,
    source: str,
    season_start_year: int,
) -> dict | None:

    if not cells:
        return None

    joined = " | ".join(
        cells
    )

    kickoff = (
        parse_datetime_from_text(
            joined,
            season_start_year,
        )
    )

    # No inventamos una hora si todavía no está confirmada.
    if kickoff is None:
        return None

    # --------------------------------------------------------
    # "Equipo A VS Equipo B"
    # --------------------------------------------------------

    for cell in cells:

        pair = (
            split_match_text(
                cell
            )
        )

        if pair is not None:

            return {
                "matchday":
                    matchday,

                "home":
                    canonical_team_name(
                        pair[
                            0
                        ]
                    ),

                "away":
                    canonical_team_name(
                        pair[
                            1
                        ]
                    ),

                "kickoff":
                    kickoff.isoformat(),

                "source":
                    source,
            }

    # --------------------------------------------------------
    # Tabla clásica:
    # Local | Fecha/Hora | Visitante
    # --------------------------------------------------------

    date_index = None

    for index, cell in enumerate(
        cells
    ):

        if (
            any(
                pattern.search(
                    cell
                )
                for pattern in DATE_PATTERNS
            )
            or
            parse_datetime_from_text(
                cell,
                season_start_year,
            )
            is not None
        ):

            date_index = index
            break

    if date_index is None:
        return None

    before = [
        clean_text(
            cell
        )

        for cell in cells[
            :date_index
        ]

        if clean_text(
            cell
        )
    ]

    after = [
        clean_text(
            cell
        )

        for cell in cells[
            date_index + 1:
        ]

        if clean_text(
            cell
        )
    ]

    # Fecha y hora pueden estar separadas en columnas.
    while (
        after
        and
        (
            TIME_RE.fullmatch(
                after[
                    0
                ]
            )
            or
            any(
                pattern.fullmatch(
                    after[
                        0
                    ]
                )
                for pattern in DATE_PATTERNS
            )
        )
    ):

        after = (
            after[
                1:
            ]
        )

    if not before or not after:
        return None

    home = (
        before[
            -1
        ]
    )

    away = (
        after[
            0
        ]
    )

    if home.lower() in {
        "equipo local",
        "local",
        "partido",
        "resultado",
    }:

        return None

    if away.lower() in {
        "equipo visitante",
        "visitante",
        "partido",
        "resultado",
    }:

        return None

    return {
        "matchday":
            matchday,

        "home":
            canonical_team_name(
                home
            ),

        "away":
            canonical_team_name(
                away
            ),

        "kickoff":
            kickoff.isoformat(),

        "source":
            source,
    }


# ============================================================
# PARSER GENÉRICO
# ============================================================


def parse_matchday_tables(
    html: str,
    source: str,
    season_start_year: int,
) -> list[dict]:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    matches = []

    candidate_tags: Iterable = (
        soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "div",
                "span",
                "p",
            ]
        )
    )

    for tag in candidate_tags:

        text = clean_text(
            tag.get_text(
                " ",
                strip=True,
            )
        )

        matchday = (
            extract_matchday_number(
                text
            )
        )

        if matchday is None:
            continue

        table = (
            tag.find_next(
                "table"
            )
        )

        if table is None:
            continue

        for row in table.find_all(
            "tr"
        ):

            cells = [
                clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )

                for cell in row.find_all(
                    [
                        "th",
                        "td",
                    ]
                )
            ]

            match = (
                row_to_match(
                    cells=
                        cells,

                    matchday=
                        matchday,

                    source=
                        source,

                    season_start_year=
                        season_start_year,
                )
            )

            if match is not None:

                matches.append(
                    match
                )

    return deduplicate_matches(
        matches
    )


def deduplicate_matches(
    matches: list[dict],
) -> list[dict]:

    lookup = {}

    for match in matches:

        lookup[
            match_key(
                match
            )
        ] = match

    return sorted(
        lookup.values(),
        key=lambda item: (
            int(
                item[
                    "matchday"
                ]
            ),
            item[
                "kickoff"
            ],
        ),
    )


# ============================================================
# HTTP
# ============================================================


def fetch_html(
    url: str,
    timeout: int = 30,
) -> str:

    response = (
        requests.get(
            url,
            headers=
                DEFAULT_HEADERS,
            timeout=
                timeout,
        )
    )

    response.raise_for_status()

    response.encoding = (
        response.encoding
        or "utf-8"
    )

    return response.text


def fetch_source(
    url: str,
    source: str,
    season_start_year: int,
) -> list[dict]:

    html = (
        fetch_html(
            url
        )
    )

    return (
        parse_matchday_tables(
            html=
                html,

            source=
                source,

            season_start_year=
                season_start_year,
        )
    )


# ============================================================
# MERGE DE FUENTES
# ============================================================


def merge_sources(
    base_matches: list[dict],
    authoritative_matches: list[dict],
) -> list[dict]:
    """
    MARCA aporta amplitud del calendario.

    LALIGA pisa la fecha/hora del mismo partido cuando
    podemos emparejarlo, porque es la fuente prioritaria.
    """

    merged = {
        match_key(
            match
        ):
            match

        for match in base_matches
    }

    for match in authoritative_matches:

        merged[
            match_key(
                match
            )
        ] = match

    return sorted(
        merged.values(),
        key=lambda item: (
            int(
                item[
                    "matchday"
                ]
            ),
            item[
                "kickoff"
            ],
        ),
    )


# ============================================================
# PROVIDER PRINCIPAL
# ============================================================


def fetch_dynamic_calendar(
    season_start_year: int = 2026,
) -> dict:

    errors = []

    marca_matches = []

    laliga_matches = []

    # --------------------------------------------------------
    # 1. BASE AMPLIA
    # --------------------------------------------------------

    try:

        marca_matches = (
            fetch_source(
                url=
                    MARCA_CALENDAR_URL,

                source=
                    "MARCA_CALENDAR",

                season_start_year=
                    season_start_year,
            )
        )

    except Exception as error:

        errors.append(
            "MARCA_CALENDAR: "
            f"{type(error).__name__}: "
            f"{error}"
        )

    # --------------------------------------------------------
    # 2. AUTORIDAD PARA HORARIOS ACTUALES
    # --------------------------------------------------------

    try:

        laliga_matches = (
            fetch_source(
                url=
                    LALIGA_CURRENT_URL,

                source=
                    "LALIGA_OFFICIAL",

                season_start_year=
                    season_start_year,
            )
        )

    except Exception as error:

        errors.append(
            "LALIGA_OFFICIAL: "
            f"{type(error).__name__}: "
            f"{error}"
        )

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    if marca_matches:

        merged = (
            merge_sources(
                base_matches=
                    marca_matches,

                authoritative_matches=
                    laliga_matches,
            )
        )

        matchday_count = len(
            {
                int(
                    match[
                        "matchday"
                    ]
                )

                for match in merged
            }
        )

        return {
            "source":
                (
                    "MARCA+LALIGA"
                    if laliga_matches
                    else "MARCA_CALENDAR"
                ),

            "matches":
                merged,

            "errors":
                errors,

            "metadata": {
                "marca_matches":
                    len(
                        marca_matches
                    ),

                "laliga_matches":
                    len(
                        laliga_matches
                    ),

                "matchdays":
                    matchday_count,
            },
        }

    # Si MARCA no puede leerse pero LALIGA sí,
    # seguimos pudiendo operar con las jornadas visibles.
    if laliga_matches:

        return {
            "source":
                "LALIGA_OFFICIAL",

            "matches":
                laliga_matches,

            "errors":
                errors,

            "metadata": {
                "marca_matches":
                    0,

                "laliga_matches":
                    len(
                        laliga_matches
                    ),

                "matchdays":
                    len(
                        {
                            int(
                                match[
                                    "matchday"
                                ]
                            )

                            for match in laliga_matches
                        }
                    ),
            },
        }

    raise RuntimeError(
        "No se pudo obtener calendario dinamico. "
        + " | ".join(
            errors
        )
    )
