from __future__ import annotations

import json
import re
import time
import unicodedata

from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.intelligence.jornada_perfecta_provider import (
    build_roster_records,
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


def parse_ff_profile_probability(
    html: str,
    matchday: int,
) -> float | None:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    text = soup.get_text(
        " ",
        strip=True,
    )

    patterns = [
        rf"Titular\s+J{int(matchday)}\s*(\d{{1,3}})\s*%",
        rf"Titular\s+Jornada\s*{int(matchday)}\s*(\d{{1,3}})\s*%",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            value = float(
                match.group(1)
            )

            if 0 <= value <= 100:
                return value

    return None


def build_ff_signals(
    snapshot: dict,
    roster: list[dict],
    matchday: int,
    session: requests.Session,
) -> tuple[
    dict[int, dict],
    dict,
]:

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
    player_profiles = 0

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

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        links = []
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

            if "/jugadores/" not in href:
                continue

            url = urljoin(
                FF_BASE,
                href,
            )

            label = anchor.get_text(
                " ",
                strip=True,
            )

            if not label:
                parts = (
                    href.strip(
                        "/"
                    )
                    .split(
                        "/"
                    )
                )

                if len(parts) >= 2:
                    label = (
                        parts[
                            1
                        ]
                        .replace(
                            "-",
                            " ",
                        )
                    )

            key = (
                normalize(
                    label
                ),
                url,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            links.append(
                {
                    "name":
                        label,

                    "url":
                        url,
                }
            )

        used_links = set()

        for player in players:

            scored = []

            aliases = (
                aliases_for_roster_player(
                    player,
                    snapshot,
                )
            )

            for link in links:

                if link[
                    "url"
                ] in used_links:
                    continue

                score = strict_name_score(
                    link[
                        "name"
                    ],
                    aliases,
                )

                # Also use profile URL slug.
                slug_alias = normalize(
                    link[
                        "url"
                    ]
                    .split(
                        "/jugadores/",
                        1,
                    )[
                        -1
                    ]
                    .split(
                        "/",
                        1,
                    )[
                        0
                    ]
                    .replace(
                        "-",
                        " ",
                    )
                )

                score = max(
                    score,
                    strict_name_score(
                        slug_alias,
                        aliases,
                    ),
                )

                scored.append(
                    (
                        score,
                        link,
                    )
                )

            scored.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            if not scored:
                continue

            score, link = scored[
                0
            ]

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

            if score < 0.75:
                continue

            if (
                second >= 0.75
                and
                score - second < 0.08
            ):
                continue

            try:

                profile_html = fetch(
                    session,
                    link[
                        "url"
                    ],
                )

                player_profiles += 1

            except Exception as error:

                errors.append(
                    f"{player.get('name')}:"
                    f"{type(error).__name__}:"
                    f"{error}"
                )

                continue

            probability = (
                parse_ff_profile_probability(
                    profile_html,
                    matchday,
                )
            )

            if probability is None:
                continue

            used_links.add(
                link[
                    "url"
                ]
            )

            player_id = int(
                player[
                    "id"
                ]
            )

            result[
                player_id
            ] = {
                "source":
                    "FUTBOLFANTASY",

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
                    (
                        f"PROFILE_TITULAR_J"
                        f"{matchday}"
                    ),

                "source_name":
                    link[
                        "name"
                    ],

                "team":
                    team_name,

                "url":
                    link[
                        "url"
                    ],

                "match_score":
                    round(
                        score,
                        3,
                    ),
            }

            time.sleep(
                0.05
            )

    return (
        result,
        {
            "team_pages":
                team_pages,

            "player_profiles":
                player_profiles,

            "matched":
                len(
                    result
                ),

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

    roster = build_roster_records(
        snapshot
    )

    session = requests.Session()

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
