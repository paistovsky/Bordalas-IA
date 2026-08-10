from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURACION
# ============================================================

BASE_URL = "https://www.jornadaperfecta.com"

MARKET_URL = f"{BASE_URL}/mercado/"
CHOLLOS_URL = f"{BASE_URL}/chollos/"

DATA_DIRECTORY = Path("data") / "intelligence"
DATA_FILE = DATA_DIRECTORY / "jornada_perfecta_market.json"

REQUEST_TIMEOUT = 30

# Con 5-6 articulos recientes tenemos suficiente señal editorial
# sin golpear innecesariamente la web.
MAX_CHOLLOS_ARTICLES = 6

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
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
}

MARKET_CACHE_RE = re.compile(
    r"(?:const|let|var)\s+marketCaching\s*=\s*(\[[\s\S]*?\])\s*;",
    re.IGNORECASE,
)

PLAYER_CARD_RE = re.compile(
    r"Pron[oó]stico\s*:",
    re.IGNORECASE,
)


# ============================================================
# HTTP
# ============================================================

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_html(
    session: requests.Session,
    url: str,
) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    # requests puede inferir ISO-8859-1 en HTML español aunque
    # el documento real sea UTF-8. apparent_encoding suele
    # resolver correctamente Jornada Perfecta.
    if response.apparent_encoding:
        response.encoding = response.apparent_encoding

    return response.text


# ============================================================
# UTILIDADES
# ============================================================

def ensure_directory() -> None:
    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def normalize_slug(
    value: str | None,
) -> str:
    if not value:
        return ""

    value = str(value).strip().lower()

    if "/jugador/" in value:
        parsed = urlparse(value)
        path = parsed.path.rstrip("/")
        value = path.split("/")[-1]

    return re.sub(
        r"[^a-z0-9\-]+",
        "",
        value,
    )


def int_value(
    value,
    default: int = 0,
) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def parse_iso_datetime(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    try:
        result = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )
    except (TypeError, ValueError):
        return None

    if result.tzinfo is None:
        result = result.replace(
            tzinfo=timezone.utc,
        )

    return result.astimezone(
        timezone.utc
    )


def calculate_age_hours(
    value: str | None,
) -> float | None:
    parsed = parse_iso_datetime(value)

    if parsed is None:
        return None

    age = (
        datetime.now(timezone.utc)
        - parsed
    ).total_seconds() / 3600

    return max(
        round(age, 2),
        0.0,
    )


# ============================================================
# MERCADO JP
# ============================================================

def extract_market_cache(
    html: str,
) -> list[dict]:
    """
    Jornada Perfecta renderiza /mercado/ usando una variable
    JavaScript:

        const marketCaching=[{...}, {...}]

    El contenido observado es JSON valido.
    """
    match = MARKET_CACHE_RE.search(html)

    if match is None:
        raise RuntimeError(
            "No se encontro marketCaching en Jornada Perfecta."
        )

    raw_json = match.group(1)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "marketCaching existe, pero no se pudo parsear como JSON: "
            f"{error}"
        ) from error

    if not isinstance(data, list):
        raise RuntimeError(
            "marketCaching no contiene una lista."
        )

    return [
        item
        for item in data
        if isinstance(item, dict)
    ]


def normalize_market_player(
    raw: dict,
) -> dict:
    last_markets_raw = (
        raw.get("lastMarkets", {})
        or {}
    )

    last_markets = {}

    for horizon in (
        1,
        2,
        3,
        5,
        10,
        14,
        30,
    ):
        last_markets[str(horizon)] = int_value(
            last_markets_raw.get(
                str(horizon),
                last_markets_raw.get(horizon),
            )
        )

    price = int_value(
        raw.get("price")
    )

    max_price = int_value(
        raw.get("max_price")
    )

    min_price = int_value(
        raw.get("min_price")
    )

    return {
        "jp_player_id": int_value(
            raw.get("playerId")
        ),
        "slug": normalize_slug(
            raw.get("playerUrl")
            or raw.get("url")
        ),
        "name": raw.get("name"),
        "real_name": raw.get("real_name"),
        "position": raw.get("position"),
        "biwenger_remote_id": int_value(
            raw.get("remote_player")
        ),
        "price": price,
        "max_price": max_price,
        "min_price": min_price,
        "last_markets": last_markets,
        "team_id": int_value(
            raw.get("teamId")
        ),
        "team": raw.get("team"),
        "team_slug": raw.get("teamUrl"),
        "biwenger_remote_team": int_value(
            raw.get("remote_team")
        ),
        "available": str(
            raw.get("available", "0")
        ),
        "penalized": str(
            raw.get("penalized", "0")
        ),
        "injured": str(
            raw.get("injured", "0")
        ),
        "warned": str(
            raw.get("warned", "0")
        ),
        "doubt": str(
            raw.get("doubt", "0")
        ),
        "other": str(
            raw.get("other", "0")
        ),
        "tip": raw.get("tip"),
        "tip_desc": raw.get("tip_desc"),
        "status": raw.get("status"),
        "icon": raw.get("icon"),
        "status_desc": raw.get("desc"),
        "racha": int_value(
            raw.get("racha")
        ),
    }


# ============================================================
# CHOLLOS / EDITORIAL
# ============================================================

def extract_published_at(
    soup: BeautifulSoup,
) -> str | None:
    preferred = (
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "article:published_time"}),
        ("meta", {"property": "og:published_time"}),
    )

    for tag_name, attrs in preferred:
        tag = soup.find(
            tag_name,
            attrs=attrs,
        )

        if tag is not None:
            value = tag.get("content")

            parsed = parse_iso_datetime(value)

            if parsed is not None:
                return parsed.isoformat()

    for tag in soup.find_all("time"):
        value = (
            tag.get("datetime")
            or tag.get_text(
                " ",
                strip=True,
            )
        )

        parsed = parse_iso_datetime(value)

        if parsed is not None:
            return parsed.isoformat()

    # Fallback: buscar cualquier meta relacionada con fecha
    # y quedarnos con el primer ISO parseable.
    for tag in soup.find_all("meta"):
        key = str(
            tag.get("property")
            or tag.get("name")
            or ""
        ).lower()

        if (
            "date" not in key
            and
            "publish" not in key
        ):
            continue

        parsed = parse_iso_datetime(
            tag.get("content")
        )

        if parsed is not None:
            return parsed.isoformat()

    return None


def classify_editorial_type(
    title: str,
) -> str:
    lower = title.lower()

    if "tapado" in lower:
        return "TAPADO"

    if "chollo" in lower:
        return "CHOLLO"

    if "rentable" in lower:
        return "RENTABLE"

    return "EDITORIAL"


def extract_chollos_article_links(
    soup: BeautifulSoup,
) -> list[dict]:
    results = []
    seen = set()

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = str(
            anchor.get("href")
            or ""
        )

        if "/blog/" not in href:
            continue

        text = " ".join(
            anchor.get_text(
                " ",
                strip=True,
            ).split()
        )

        if not text:
            continue

        lower = text.lower()

        if not any(
            token in lower
            for token in (
                "chollo",
                "tapado",
                "rentable",
            )
        ):
            continue

        url = urljoin(
            BASE_URL,
            href,
        )

        if url in seen:
            continue

        seen.add(url)

        results.append(
            {
                "title": text,
                "url": url,
                "editorial_type": (
                    classify_editorial_type(
                        text
                    )
                ),
            }
        )

    return results


def extract_card_slug(
    href: str,
) -> str:
    parsed = urlparse(
        urljoin(
            BASE_URL,
            href,
        )
    )

    path = parsed.path.rstrip("/")

    if "/jugador/" not in path:
        return ""

    return normalize_slug(
        path.split("/")[-1]
    )


def extract_article_player_cards(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Solo consideramos como señal editorial los enlaces de
    jugador cuyo texto contiene 'Pronostico:'.

    Esto evita falsos positivos como Yamal/Mbappe mencionados
    simplemente en la introduccion del articulo.
    """
    result = []
    seen = set()

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = str(
            anchor.get("href")
            or ""
        )

        if "/jugador/" not in href:
            continue

        text = " ".join(
            anchor.get_text(
                " ",
                strip=True,
            ).split()
        )

        if not PLAYER_CARD_RE.search(text):
            continue

        slug = extract_card_slug(
            href
        )

        if not slug:
            continue

        if slug in seen:
            continue

        seen.add(slug)

        forecast_match = re.search(
            r"Pron[oó]stico\s*:\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+)",
            text,
            re.IGNORECASE,
        )

        forecast = (
            " ".join(
                forecast_match.group(1).split()
            )
            if forecast_match
            else None
        )

        result.append(
            {
                "slug": slug,
                "player_url": urljoin(
                    BASE_URL,
                    href,
                ),
                "raw_card_text": text,
                "forecast": forecast,
            }
        )

    return result


def crawl_chollos(
    session: requests.Session,
) -> dict:
    html = fetch_html(
        session,
        CHOLLOS_URL,
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    article_links = (
        extract_chollos_article_links(
            soup
        )[
            :MAX_CHOLLOS_ARTICLES
        ]
    )

    articles = []
    signals = []

    errors = []

    for article in article_links:
        try:
            article_html = fetch_html(
                session,
                article["url"],
            )

            article_soup = BeautifulSoup(
                article_html,
                "html.parser",
            )

        except Exception as error:
            errors.append(
                {
                    "url": article["url"],
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

            continue

        published_at = (
            extract_published_at(
                article_soup
            )
        )

        age_hours = (
            calculate_age_hours(
                published_at
            )
        )

        cards = (
            extract_article_player_cards(
                article_soup
            )
        )

        article_record = {
            **article,
            "published_at": published_at,
            "age_hours": age_hours,
            "players_found": len(cards),
        }

        articles.append(
            article_record
        )

        for card in cards:
            signals.append(
                {
                    **card,
                    "editorial_type": (
                        article[
                            "editorial_type"
                        ]
                    ),
                    "article_title": (
                        article["title"]
                    ),
                    "article_url": (
                        article["url"]
                    ),
                    "published_at": (
                        published_at
                    ),
                    "age_hours": (
                        age_hours
                    ),
                }
            )

    return {
        "articles": articles,
        "signals": signals,
        "errors": errors,
    }


# ============================================================
# MERGE MARKET + EDITORIAL
# ============================================================

def attach_editorial_signals(
    players: list[dict],
    editorial_signals: list[dict],
) -> list[dict]:
    by_slug = {}

    for signal in editorial_signals:
        slug = normalize_slug(
            signal.get("slug")
        )

        if not slug:
            continue

        by_slug.setdefault(
            slug,
            [],
        ).append(
            signal
        )

    result = []

    for player in players:
        slug = normalize_slug(
            player.get("slug")
        )

        signals = list(
            by_slug.get(
                slug,
                [],
            )
        )

        signals.sort(
            key=lambda item: (
                item.get("published_at")
                or ""
            ),
            reverse=True,
        )

        result.append(
            {
                **player,
                "editorial_signals": signals,
                "editorial_signal_count": len(
                    signals
                ),
                "latest_editorial_signal": (
                    signals[0]
                    if signals
                    else None
                ),
            }
        )

    return result


# ============================================================
# REFRESH PRINCIPAL
# ============================================================

def refresh_jornada_perfecta_market_data(
    force: bool = False,
) -> dict:
    """
    Descarga y normaliza:
    - /mercado/ -> marketCaching
    - /chollos/ -> articulos editoriales recientes

    `force` se conserva para mantener una interfaz compatible
    con futuros controles de cache. En esta primera version
    el refresh es siempre real.
    """
    del force

    session = build_session()

    market_html = fetch_html(
        session,
        MARKET_URL,
    )

    raw_market = extract_market_cache(
        market_html
    )

    market_players = [
        normalize_market_player(
            item
        )
        for item in raw_market
    ]

    chollos = crawl_chollos(
        session
    )

    players = attach_editorial_signals(
        players=market_players,
        editorial_signals=(
            chollos["signals"]
        ),
    )

    now = datetime.now(
        timezone.utc
    )

    payload = {
        "source": "JORNADA_PERFECTA_MARKET",
        "updated_at": now.isoformat(),
        "players": players,
        "editorial_signals": (
            chollos["signals"]
        ),
        "articles": (
            chollos["articles"]
        ),
        "metadata": {
            "market_players": len(
                market_players
            ),
            "articles_visited": len(
                chollos["articles"]
            ),
            "editorial_signals": len(
                chollos["signals"]
            ),
            "errors": (
                chollos["errors"]
            ),
        },
    }

    ensure_directory()

    temporary = DATA_FILE.with_suffix(
        ".json.tmp"
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
        "status": "REFRESHED",
        "data": payload,
        "refreshed": True,
        "file": str(
            DATA_FILE
        ),
    }


def load_jornada_perfecta_market_data() -> dict | None:
    if not DATA_FILE.exists():
        return None

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:
            value = json.load(
                file
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
