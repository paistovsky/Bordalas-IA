from __future__ import annotations

import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

from src.analysis.decision_orchestrator import build_global_decision
from src.analysis.acquisition_board import build_acquisition_board
from src.analysis.market_analyzer import get_latest_snapshot, load_snapshot
from src.analysis.rival_intelligence_engine import (
    build_rival_intelligence,
    save_rival_intelligence,
)
from src.collectors.board_history_collector import collect_board_history
from src.analysis.market_clock import build_market_clock
from src.analysis.rival_ledger_audit import audit_rival_ledger
from src.analysis.player_value_engine import calibrate_points_market
from src.analysis.acquisition_valuation import (
    build_valuation_context,
    value_candidate,
)
from src.analysis.historical_price_lookup import (
    build_historical_price_lookup,
)

from src.analysis.rival_bid_model import build_bid_model, optimal_bid
from src.analysis.intelligent_bid_engine import (
    build_market_seller_lookup,
)
from src.telemetry.league_center import build_league_center


from src.telemetry.player_photo_resolver import (
    build_player_photo_lookup as build_player_photo_lookup_v3,
    display_name as display_player_name,
)

AUTOPILOT_LOG = Path("data") / "autopilot" / "autopilot_log.jsonl"
COMPETITIVE_LOG = Path("data") / "autopilot" / "competitive_observer_log.jsonl"
DASHBOARD_STATUS = Path("dashboard") / "data" / "status.json"
REACT_DASHBOARD_STATUS = Path("dashboard-v8") / "public" / "data" / "status.json"
PLAYER_MAPPING_CACHE = Path("data") / "player_mapping_cache.json"
PLAYER_PHOTO_CACHE = Path("data") / "dashboard_player_photo_cache.json"
FULL_AUTONOMOUS_STATUS = (
    Path("data") / "trading" / "v10_full_autonomous_status.json"
)


# A partir de cuando "este ciclo" deja de ser este ciclo.
#
# Un ciclo son 30 minutos. Dos ciclos de margen absorben un
# retraso normal -un refresco lento, una cola de GitHub-; a
# partir de ahi lo que se esta enseñando es historia y hay que
# decirlo.
STALE_CYCLE_SECONDS = 2 * 30 * 60


def _edad_en_segundos(marca) -> int | None:
    """
    Cuanto hace de esa marca de tiempo. None si no se sabe.

    Ausencia de dato no es dato: si la marca no viene o no se
    puede leer, se devuelve None y NO cero, que se leeria como
    "acaba de pasar" -justo el error que esto viene a evitar-.
    """

    if not marca:
        return None

    texto = str(marca).strip().replace("Z", "+00:00")

    try:
        instante = datetime.fromisoformat(texto)

    except ValueError:
        return None

    ahora = datetime.now(tz=instante.tzinfo)

    return max(
        0,
        int((ahora - instante).total_seconds()),
    )


ACTION_LABELS = {
    "MONITOR_OFFERS": "Vigilar ofertas",

    # Cobrar una oferta que el motor ya ha aprobado. Hasta el
    # 18/08 no se emitia nunca, asi que tampoco tenia nombre en
    # castellano y salia "Accept Recovery Offer".
    "ACCEPT_RECOVERY_OFFER": "Cobrar oferta aprobada",

    # Las dos que salian en ingles en la pantalla de MERCADO.
    "KEEP_PROTECTED": "Conservar: jugador protegido",
    "KEEP_SOLVENCY_RESERVED": "Conservar: reservado para solvencia",

    # Los veredictos de Offer Decision Engine V2. No tenian
    # nombre porque hasta ahora no se enseñaban en ningun sitio:
    # la tabla de ofertas hablaba en nombre del motor de reroll.
    "ACCEPT_NOW": "Cobrar ahora",
    "ACCEPT_FOR_SOLVENCY": "Cobrar para tapar la caja",
    "REROLL_CANDIDATE": "Pedir otra oferta mejor",
    "HOLD_OFFER": "Esperar",

    "NEVER_SELL": "No vender",
    "KEEP_GOOD_OFFER": "Conservar buena oferta",
    "HOLD_SOLVENCY_RESERVED": "Reservar para solvencia",
    "WATCH_SPECULATION": "Vigilar especulación",
    "BUY_SPECULATION": "Comprar para especular",
    "MONITOR_SOLVENCY": "Vigilar solvencia",
    "CONSIDER_PLAYER_EXIT": "Revisar riesgo de plantilla",
    "RENEW_MARKET_LISTING": "Renovar publicación",
    "RENEW_MARKET_LISTING_WATCH": "Vigilar renovación",
    "REROLL_COMPUTER_OFFER": "Pedir nueva oferta a Computer",
    "ACCEPT_CLUSTER_BEFORE_EXPIRY": "Aceptar oferta antes de caducar",
    "WATCH_CRITICAL_EXPIRY_CLUSTER": "Vigilar ofertas críticas",
    "LIST_FOR_LIQUIDITY": "Publicar jugador para generar liquidez",
    "SAVE_LINEUP": "Guardar XI",
    "BUY_V10": "Comprar oportunidad de mercado",
    "RAISE_COUNTER": "Mejorar contraoferta",
    "EXIT_LISTING": "Publicar salida de cartera",
    "WAIT": "Esperar",
}

TYPE_LABELS = {
    "OFFER_DECISION_INTELLIGENCE": "Ofertas Computer",
    "PLAYER_RISK_EXIT": "Riesgo de plantilla",
    "SOLVENCY_GUARANTEE": "Solvencia",
    "SPECULATION_WATCH": "Especulación",
    "SPECULATION_BUY": "Especulación",
    "MARKET_LISTING_RENEW": "Publicaciones en venta",
    "MARKET_LISTING_RENEW_URGENT": "Publicación a punto de caducar",
    "COMPUTER_OFFER_REROLL_WATCH": "Ofertas Computer",
    "ACCEPT_BEFORE_EXPIRY_WATCH": "Caducidad de ofertas",
    "ACCEPT_BEFORE_EXPIRY_SAFETY": "Caducidad de ofertas",
    "LINEUP": "Alineación",
    "IDLE": "Sin acciones",
}

STATUS_LABELS = {
    "MONITOR_OFFERS": "VIGILANDO",
    "CONSIDER_PLAYER_EXIT": "REVISANDO",
    "MONITOR_SOLVENCY": "GARANTIZADA",
    "WATCH_SPECULATION": "OPORTUNIDADES",
    "BUY_SPECULATION": "OPORTUNIDAD",
    "WAIT": "EN ESPERA",
}


def safe_int(value, default=0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def human_action(action: str | None) -> str:
    if not action:
        return "Sin decisión"
    return ACTION_LABELS.get(action, action.replace("_", " ").title())


def human_candidate(candidate: dict) -> dict:
    action = candidate.get("action")
    candidate_type = candidate.get("type")
    return {
        "type": candidate_type,
        "label": TYPE_LABELS.get(
            candidate_type,
            str(candidate_type or "").replace("_", " ").title(),
        ),
        "action": action,
        "status": STATUS_LABELS.get(
            action,
            human_action(action).upper(),
        ),
        "priority": safe_int(candidate.get("priority")),
        "executable": bool(candidate.get("executable")),
    }



def load_player_mapping_cache() -> dict:
    if not PLAYER_MAPPING_CACHE.exists():
        return {}

    try:
        payload = json.loads(
            PLAYER_MAPPING_CACHE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}

    if isinstance(payload, dict):
        # Algunas versiones guardan directamente el lookup;
        # otras pueden envolverlo.
        for key in (
            "mappings",
            "players",
            "data",
        ):
            nested = payload.get(key)
            if isinstance(nested, dict):
                return nested

        return payload

    return {}


def get_external_player_id(
    mapping_cache: dict,
    biwenger_id: int,
) -> int | None:
    entry = (
        mapping_cache.get(str(biwenger_id))
        or mapping_cache.get(biwenger_id)
        or {}
    )

    if not isinstance(entry, dict):
        return None

    value = (
        entry.get("external_id")
        or entry.get("api_football_id")
        or entry.get("api_id")
    )

    try:
        value = int(value)
    except (TypeError, ValueError):
        return None

    return value if value > 0 else None


def api_football_photo_url(
    external_id: int | None,
) -> str | None:
    if not external_id:
        return None

    return (
        "https://media.api-sports.io/"
        f"football/players/{external_id}.png"
    )



def _normalize_name(value: str) -> str:
    text = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    )
    text = "".join(
        ch
        for ch in text
        if not unicodedata.combining(ch)
    )
    return " ".join(
        text.lower().strip().split()
    )


def load_dashboard_player_photo_cache() -> dict:
    if not PLAYER_PHOTO_CACHE.exists():
        return {}

    try:
        payload = json.loads(
            PLAYER_PHOTO_CACHE.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}

    return (
        payload
        if isinstance(payload, dict)
        else {}
    )


def save_dashboard_player_photo_cache(
    cache: dict,
) -> None:
    try:
        PLAYER_PHOTO_CACHE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        PLAYER_PHOTO_CACHE.write_text(
            json.dumps(
                cache,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def fetch_api_football_player_photo(
    player_name: str,
) -> dict:
    """
    Fallback de telemetría para fotos.
    Se usa únicamente cuando no existe mapping previo.
    El resultado se cachea para no consumir API en cada ciclo.
    """
    api_key = os.getenv(
        "API_FOOTBALL_KEY"
    )

    if not api_key:
        return {}

    name = str(player_name or "").strip()

    if len(name) < 3:
        return {}

    try:
        response = requests.get(
            "https://v3.football.api-sports.io/players",
            headers={
                "x-apisports-key": api_key,
            },
            params={
                "search": name,
            },
            timeout=4,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return {}

    rows = payload.get("response") or []

    if not isinstance(rows, list):
        return {}

    target = _normalize_name(name)
    best = None
    best_score = -1

    for row in rows:
        player = (
            row.get("player")
            if isinstance(row, dict)
            else None
        ) or {}

        candidate_name = (
            player.get("name")
            or ""
        )

        candidate = _normalize_name(
            candidate_name
        )

        if not candidate:
            continue

        score = 0

        if candidate == target:
            score = 100
        elif (
            candidate in target
            or target in candidate
        ):
            score = 70
        else:
            target_tokens = set(
                target.split()
            )
            candidate_tokens = set(
                candidate.split()
            )
            score = len(
                target_tokens
                & candidate_tokens
            ) * 20

        if score > best_score:
            best_score = score
            best = player

    if not best or best_score <= 0:
        return {}

    external_id = safe_int(
        best.get("id")
    )

    photo_url = best.get("photo")

    if not photo_url and external_id:
        photo_url = (
            "https://media.api-sports.io/"
            f"football/players/{external_id}.png"
        )

    return {
        "api_football_id": (
            external_id or None
        ),
        "photo_url": photo_url,
        "api_name": best.get("name"),
    }


def build_player_photo_lookup(
    snapshot: dict,
) -> dict[int, dict]:
    return build_player_photo_lookup_v3(snapshot)


def _ff_signal(player_id) -> dict:
    """
    La señal de FutbolFantasy de un jugador, para pintarla.

    Blindado a proposito: el dashboard es telemetria. Si el tablero
    no esta o no se puede leer, se pintan menos columnas; lo que no
    puede es tumbar la generacion del estado.
    """

    try:
        from src.analysis.candidate_starter_lookup import (
            get_starter_lookup,
        )

        return get_starter_lookup().get(safe_int(player_id)) or {}

    except Exception:
        return {}


def compact_lineup(
    lineup_state: dict,
    snapshot: dict,
    photo_lookup: dict[int, dict] | None = None,
) -> dict:
    lineup = lineup_state.get("lineup", {}) or {}
    selected = lineup.get("selected", []) or []
    photo_lookup = photo_lookup or {}

    my_team_by_id = {
        safe_int(player.get("id")): player
        for player in snapshot.get("my_team", []) or []
    }

    catalog_players = (
        snapshot.get("catalog", {})
        .get("data", {})
        .get("players", {})
        or {}
    )

    players = []

    for player in selected:
        player_id = safe_int(player.get("id"))

        catalog_source = {}
        if isinstance(catalog_players, dict):
            catalog_source = (
                catalog_players.get(str(player_id))
                or catalog_players.get(player_id)
                or {}
            )

        source = my_team_by_id.get(player_id) or catalog_source or {}
        photo = photo_lookup.get(player_id) or {}

        icon_hero = (
            player.get("iconHero")
            or source.get("iconHero")
            or photo.get("icon_hero")
        )

        raw_name = (
            player.get("name")
            or source.get("name")
            or photo.get("name")
            or "?"
        )

        fixed_name = display_player_name(raw_name)

        price = safe_int(
            player.get(
                "price",
                source.get("price"),
            )
        )

        # ====================================================
        # V11.4.1 DASHBOARD MULTISOURCE HOTFIX
        # ====================================================
        starter = (
            player.get(
                "starter_intelligence"
            )
            or {}
        )

        starter_sources = (
            player.get(
                "starter_sources"
            )
            or starter.get(
                "sources"
            )
            or {}
        )

        starter_consensus = (
            player.get(
                "starter_consensus"
            )
            or starter.get(
                "consensus"
            )
        )

        starter_probability = (
            player.get(
                "starter_probability"
            )
        )

        if starter_probability is None:
            starter_probability = starter.get(
                "starter_probability"
            )

        starter_coverage = safe_int(
            player.get(
                "starter_source_coverage",
                starter.get(
                    "source_coverage"
                ),
            )
        )

        def source_probability(
            source_name: str,
        ):
            source = (
                starter_sources.get(
                    source_name
                )
                or {}
            )

            value = source.get(
                "probability"
            )

            if value is None:
                return None

            return round(
                safe_float(
                    value
                ),
                1,
            )

        # LO QUE VE PEPE TIENE QUE VERSE EN PANTALLA
        #
        # Desde el 17/08/2026 el tablero de FutbolFantasy trae
        # equipo, jerarquia y parte de baja de cada jugador, y la
        # valoracion ya decide con ellos. Si no salen aqui, el
        # dashboard cuenta una historia mas pobre que la que Pepe
        # esta usando para gastar dinero.
        senal_ff = _ff_signal(player_id)

        jerarquia_ff = senal_ff.get("hierarchy") or {}

        players.append(
            {
                "id": player_id,
                "name": fixed_name,

                "team_name": senal_ff.get("team"),

                "hierarchy": jerarquia_ff.get("label"),
                "hierarchy_value": jerarquia_ff.get("value"),
                "franchise": bool(jerarquia_ff.get("franchise")),

                "availability": (
                    (senal_ff.get("availability") or {}).get("label")
                ),
                "absence": senal_ff.get("absence"),
                "position": safe_int(
                    player.get(
                        "lineup_position",
                        player.get(
                            "position",
                            source.get("position"),
                        ),
                    )
                ),
                "price": price,
                "price_increment": safe_int(
                    player.get(
                        "priceIncrement",
                        source.get("priceIncrement"),
                    )
                ),
                "points": safe_int(
                    player.get(
                        "points",
                        source.get("points"),
                    )
                ),
                "lineup_score": round(
                    safe_float(player.get("lineup_score")),
                    2,
                ),

                # POR QUE ESTE Y NO OTRO (18/08/2026)
                #
                # El numero que ordena el once: jerarquia y
                # porcentaje en una sola cifra de 0 a 1. Sube al
                # dashboard porque el dia que Yamal se cayo del
                # XI no habia forma de ver contra quien habia
                # perdido ni por cuanto.
                "weekly_expected_value": round(
                    safe_float(
                        player.get("weekly_expected_value")
                    ),
                    3,
                ),
                "availability": player.get("availability_label"),

                # Compatibility aliases for current dashboard frontend:
                # no longer JP-only; now real multisource consensus.
                "jp_status": (
                    starter_consensus
                    or player.get(
                        "external_lineup_status"
                    )
                ),

                # Un 0 % no es una prediccion: es que no hay
                # dato.
                #
                # El 16/08/2026 el dashboard pinto los once
                # jugadores con "tit. 0 %" y la barra vacia,
                # mientras la consola del mismo ciclo decia
                # conf:96 %. La fuente externa habia fallado y
                # aqui un 0.0 se colaba como si fuese una
                # medicion. Pintar cero cuando no sabes es peor
                # que no pintar nada: parece que el once no juega.
                "jp_confidence": (
                    _starter_confidence(
                        starter_probability,
                        player.get(
                            "external_lineup_confidence"
                        ),
                    )
                ),

                # Native multisource fields for the next UI iteration.
                "starter_consensus":
                    starter_consensus,

                "starter_probability": (
                    round(
                        safe_float(
                            starter_probability
                        ),
                        1,
                    )
                    if starter_probability is not None
                    else None
                ),

                "starter_expected_minutes": (
                    round(
                        safe_float(
                            player.get(
                                "starter_expected_minutes",
                                starter.get(
                                    "expected_minutes"
                                ),
                            )
                        ),
                        1,
                    )
                    if (
                        player.get(
                            "starter_expected_minutes"
                        )
                        is not None
                        or starter.get(
                            "expected_minutes"
                        )
                        is not None
                    )
                    else None
                ),

                "starter_source_coverage":
                    starter_coverage,

                "starter_confidence": (
                    player.get(
                        "starter_confidence"
                    )
                    or starter.get(
                        "confidence"
                    )
                ),

                "starter_votes":
                    safe_int(
                        starter.get(
                            "starter_votes"
                        )
                    ),

                "uncertain_votes":
                    safe_int(
                        starter.get(
                            "uncertain_votes"
                        )
                    ),

                "bench_votes":
                    safe_int(
                        starter.get(
                            "bench_votes"
                        )
                    ),

                "jp_probability":
                    source_probability(
                        "JORNADA_PERFECTA"
                    ),

                "ff_probability":
                    source_probability(
                        "FUTBOLFANTASY"
                    ),

                "af_probability":
                    source_probability(
                        "ANALITICA_FANTASY"
                    ),
                "icon_hero": icon_hero,
                "biwenger_photo_url": photo.get("biwenger_photo_url"),
                "api_football_id": photo.get("api_football_id"),
                "api_photo_url": photo.get("api_photo_url"),
                "photo_url": photo.get("photo_url"),
                "photo_source": photo.get("photo_source"),
                "team_id": safe_int(
                    player.get(
                        "teamID",
                        source.get("teamID"),
                    )
                ),
                "number": safe_int(
                    player.get(
                        "number",
                        source.get("number"),
                    )
                ),
            }
        )

    # Cuantos del once tienen probabilidad de titular MEDIDA.
    #
    # Cuando la fuente externa falla, todos salen sin dato y el
    # panel lo dice, pero nadie se entera de que la fuente ha
    # caido. Con este recuento el fallo se ve en la consola del
    # ciclo y en la pantalla, en vez de descubrirse mirando once
    # huecos.
    con_dato = sum(
        1
        for item in players
        if item.get("jp_confidence") is not None
    )

    # Y POR QUE ha fallado.
    #
    # Contar los huecos dice que la fuente cayo. No dice si es que
    # la pagina no respondio, si devolvio un 403, o si es que la
    # cache estaba caducada y no se pudo refrescar. Sin eso, «sin
    # dato» en el dashboard y 96 % en la consola del PC parecen
    # una contradiccion en vez de dos entornos distintos: el
    # scraper corre igual en los dos, pero desde GitHub Actions
    # sale por una IP de centro de datos.
    # Import local a proposito: `lineup_engine` importa de aqui,
    # y a nivel de modulo esto seria un ciclo. La funcion cachea
    # por snapshot, asi que no hay coste.
    try:
        from src.analysis.lineup_engine import (
            build_starter_intelligence_for_snapshot,
        )

        tablero = (
            build_starter_intelligence_for_snapshot(snapshot) or {}
        )
    except Exception as error:
        tablero = {
            "error": f"{type(error).__name__}: {error}",
        }

    cache_tablero = tablero.get("cache") or {}

    return {
        "formation": lineup.get("formation_name"),

        # LA REGLA DEL DIOS (18/08/2026)
        #
        # Un Dios juega siempre salvo 0 % motivado. Si alguno
        # falta, aqui esta el motivo; si alguno esta al 0 % y
        # nadie lo explica, aqui esta el aviso. Sin esto, un Dios
        # ausente vuelve a ser un misterio que hay que reconstruir
        # a mano, que es como empezo todo esto con Yamal.
        "mandatory_hierarchy": (
            lineup.get("mandatory_hierarchy") or {}
        ),

        "playable": safe_int(lineup_state.get("playable_count")),
        "missing": safe_int(lineup_state.get("missing")),
        "score": round(safe_float(lineup.get("score")), 2),
        "total_value": sum(safe_int(item.get("price")) for item in players),
        "starter_data_players": con_dato,
        "starter_data_total": len(players),
        "starter_data_ok": bool(
            players and con_dato == len(players)
        ),
        "starter_board_version": tablero.get("version"),
        "starter_board_matchday": tablero.get("matchday"),
        "starter_board_updated_at": tablero.get("updated_at"),
        "starter_board_players": len(
            tablero.get("players") or []
        ),
        "starter_cache_status": cache_tablero.get("status"),
        "starter_source_error": (
            cache_tablero.get("error")
            or tablero.get("error")
        ),
        "players": players,
    }

def compact_rivals(intelligence: dict, current_user_id: int | None) -> list[dict]:
    rows = []

    for manager in intelligence.get("managers", []) or []:
        user_id = safe_int(manager.get("user_id"))
        rows.append(
            {
                "user_id": user_id,
                "name": manager.get("name", "?"),
                "is_us": (
                    current_user_id is not None
                    and user_id == int(current_user_id)
                ),
                "points": safe_int(manager.get("points")),
                "rank": manager.get("points_rank"),
                "balance": safe_int(manager.get("balance")),
                "roster_count": safe_int(manager.get("roster_count")),
                "roster_value": safe_int(manager.get("roster_value")),
                "net_worth": safe_int(manager.get("net_worth")),
                "maximum_bid": safe_int(manager.get("maximum_bid")),
                "maximum_bid_source": manager.get("maximum_bid_source"),
                "max_observed_bid": safe_int(manager.get("max_observed_bid")),
                "lost_bids": safe_int(manager.get("lost_bids")),
                "activity": manager.get("market_activity"),
                "profile": manager.get("profile"),
                "threat_score": manager.get("threat_score"),
                "threat_level": manager.get("threat_level"),
                "top_assets": manager.get("top_assets", [])[:3],
            }
        )

    return rows


def compact_offers(
    state: dict,
    offer_decisions: dict | None = None,
    collecting: dict | None = None,
) -> list[dict]:
    """
    Las ofertas recibidas, con la respuesta del motor que MANDA.

    LA PANTALLA ENSEÑABA AL MOTOR EQUIVOCADO (18/08/2026)

        Esta tabla se pintaba entera desde `offer_reroll`, que es
        el motor viejo y solo sabe contestar a una pregunta:
        ¿merece la pena pedirle otra oferta al Computer? Por eso
        trece ofertas seguidas decian "Conservar buena oferta",
        cinco de ellas con mas del 3 % de prima.

        Quien decide si una oferta se cobra es Offer Decision
        Engine V2 -"la unica autoridad", dice su propio codigo- y
        su veredicto no aparecia en ninguna pantalla del
        dashboard. Ni uno solo de sus campos: ni la decision, ni
        la puntuacion de venta, ni el motivo.

        Asi que el dia que arreglamos que cobrase, no habia forma
        de mirar la pantalla y saber si lo estaba haciendo.

        Es el fallo de siempre aqui: el dato existe, se calcula
        bien, y nadie lo enseña.

    LO QUE SE VE AHORA

        Manda la decision de V2. La opinion del motor de reroll
        se queda al lado, porque sigue siendo util saber si va a
        pedir otra oferta, pero ya no habla en su nombre.

        Y `collecting` marca cual se cobra en ESTE ciclo: de
        varias aprobadas solo cae una, y la diferencia entre "se
        cobra ahora" y "esta aprobada y espera turno" es justo lo
        que el dueño necesita ver para no pensar que algo falla.
    """

    offer_reroll = state.get("offer_reroll", {}) or {}

    # Indice por oferta y, de rebote, por jugador: el motor de
    # reroll agrupa por operacion y V2 decide por oferta, asi que
    # el id de oferta es lo unico que casa siempre.
    por_id = {}

    for item in (
        (offer_decisions or {}).get("decisions") or []
    ):
        if item.get("offer_id") is not None:
            por_id[item.get("offer_id")] = item

    cobrando = (collecting or {}).get("offer_id")

    en_cola = {
        item.get("offer_id")
        for item in ((collecting or {}).get("queued") or [])
        if item.get("offer_id") is not None
    }

    offers = []

    for offer in offer_reroll.get("offers", []) or []:
        names = [
            player.get("name", "?")
            for player in offer.get("players", []) or []
        ]

        offer_id = offer.get("offer_id")

        decision = por_id.get(offer_id) or {}

        # La accion que se enseña es la de V2 cuando la hay. Si no
        # la hay se dice cual es, en vez de disfrazar la del otro
        # motor de veredicto.
        accion = decision.get("decision") or offer.get("action")

        offers.append(
            {
                "players": names,
                "amount": safe_int(offer.get("amount")),
                "premium_percent": round(
                    safe_float(offer.get("premium_percent")),
                    2,
                ),
                "solvency_reserved": bool(
                    offer.get("solvency_reserved")
                ),

                "action": accion,
                "action_label": human_action(accion),

                # De donde sale el veredicto de arriba. Sin esto
                # vuelve a ser imposible saber quien esta
                # hablando.
                "decision_source": (
                    "OFFER_DECISION_V2"
                    if decision
                    else "REROLL_ENGINE"
                ),

                "sale_score": (
                    round(safe_float(decision.get("sale_score")), 0)
                    if decision.get("sale_score") is not None
                    else None
                ),

                "protection": decision.get("protection"),

                "decision_reason": (
                    (decision.get("reasons") or [None])[0]
                ),

                # La opinion del motor viejo, al lado y con su
                # nombre puesto.
                "reroll_action": offer.get("action"),
                "reroll_action_label": human_action(
                    offer.get("action")
                ),

                "collecting_now": (
                    offer_id is not None
                    and offer_id == cobrando
                ),

                "queued_to_collect": (
                    offer_id in en_cola
                    and offer_id != cobrando
                ),

                "hours_to_expiry": (
                    round(safe_float(offer.get("hours_to_expiry")), 1)
                    if offer.get("hours_to_expiry") is not None
                    else None
                ),
            }
        )

    return offers


def compact_speculation(state: dict) -> dict:
    speculation = state.get("speculation", {}) or {}
    budget = speculation.get("budget", {}) or {}

    candidates = (
        speculation.get("executable_buys")
        or speculation.get("buy_candidates")
        or []
    )

    compact = []

    for item in candidates[:5]:
        compact.append(
            {
                "name": item.get("name") or item.get("player_name") or "?",
                "score": round(
                    safe_float(
                        item.get(
                            "speculation_score",
                            item.get("score"),
                        )
                    ),
                    1,
                ),
                "price": safe_int(
                    item.get(
                        "price",
                        item.get("market_price"),
                    )
                ),
                "price_increment": safe_int(
                    item.get(
                        "price_increment",
                        item.get("priceIncrement"),
                    )
                ),
                "action": item.get("action"),
            }
        )

    return {
        "enabled": bool(budget.get("enabled")),
        "mode": budget.get("mode"),
        "blocked_by": budget.get("blocked_by"),
        "budget": safe_int(
            budget.get(
                "available_budget",
                budget.get("budget"),
            )
        ),
        "max_operation": safe_int(
            budget.get(
                "max_operation",
                budget.get("max_single_operation"),
            )
        ),
        "candidate_count": len(
            speculation.get("buy_candidates", []) or []
        ),
        "executable_count": len(
            speculation.get("executable_buys", []) or []
        ),
        "candidates": compact,
    }


def compact_listings(state: dict) -> dict:
    lifecycle = state.get("listing_lifecycle", {}) or {}
    return {
        "listing_count": safe_int(lifecycle.get("listing_count")),
        "renew_required_count": safe_int(
            lifecycle.get("renew_required_count")
        ),
        "renew_required": [
            {
                "name": item.get("name"),
                "hours_to_expiry": (
                    round(safe_float(item.get("hours_to_expiry")), 1)
                    if item.get("hours_to_expiry") is not None
                    else None
                ),
                "listed_price": safe_int(item.get("listed_price")),
            }
            for item in lifecycle.get("renew_required", []) or []
        ][:8],
    }


def _activity_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _same_cycle_execution(previous: dict, current: dict) -> bool:
    if previous.get("phase") != "PRE_ACTION":
        return False
    if current.get("phase") != "POST_ACTION":
        return False
    if not previous.get("write_performed"):
        return False
    if previous.get("action") != current.get("action"):
        return False
    if previous.get("status") != current.get("status"):
        return False

    before = _activity_timestamp(previous.get("timestamp"))
    after = _activity_timestamp(current.get("timestamp"))
    if before is None or after is None:
        return True

    return 0 <= (after - before).total_seconds() <= 15 * 60


def load_activity_feed(limit: int = 100) -> list[dict]:
    if not AUTOPILOT_LOG.exists():
        return []

    rows = []

    try:
        lines = AUTOPILOT_LOG.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return []

    for line in lines[-limit:]:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        execution = record.get("execution", {}) or {}
        action = (
            execution.get("action")
            or record.get("decision_action")
            or record.get("action")
        )

        row = {
            "timestamp": record.get("timestamp"),
            "phase": record.get("log_phase") or record.get("phase"),
            "action": action,
            "label": human_action(action),
            "write_performed": bool(
                execution.get("write_performed", False)
            ),
            "success": execution.get("success"),
            "status": execution.get("status"),
            "reason": execution.get("reason"),
            "http_status": execution.get("http_status"),
            "verified_post_action": False,
        }

        merged = False
        if row["phase"] == "POST_ACTION" and row["write_performed"]:
            for index in range(len(rows) - 1, max(-1, len(rows) - 6), -1):
                if _same_cycle_execution(rows[index], row):
                    row["started_at"] = rows[index].get("timestamp")
                    row["verified_post_action"] = True
                    rows[index] = row
                    merged = True
                    break

        if not merged:
            rows.append(row)

    return rows[::-1]


def load_full_autonomous_status() -> dict:
    if not FULL_AUTONOMOUS_STATUS.exists():
        return {}
    try:
        payload = json.loads(
            FULL_AUTONOMOUS_STATUS.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_execution_telemetry(
    activity: list[dict],
    cycle_status: dict | None = None,
) -> tuple[dict, dict]:
    cycle_status = (
        cycle_status
        if cycle_status is not None
        else load_full_autonomous_status()
    )
    execution = cycle_status.get("execution", {}) or {}
    action = execution.get("action") or cycle_status.get("action_taken")
    write_used = bool(
        execution.get(
            "write_performed",
            cycle_status.get("write_used", False),
        )
    )
    snapshot_policy = cycle_status.get("snapshot_policy", {}) or {}
    post_write_verified = bool(
        snapshot_policy.get("legacy_post_write")
        or snapshot_policy.get("v10_post_write")
    )

    cycle = {
        "version": cycle_status.get("version"),
        "timestamp": cycle_status.get("timestamp"),
        "write_used": write_used,
        "action": action,
        "label": human_action(action) if action else None,
        "status": execution.get("status"),
        "success": execution.get("success"),
        "source": execution.get("source"),
        "reason": execution.get("reason"),
        "http_status": execution.get("http_status"),
        "post_write_verified": post_write_verified,
    }

    # ==================================================
    # CUANTOS ANOS TIENE ESTO (18/08/2026)
    # ==================================================
    #
    # `v10_full_autonomous_status.json` se leia tal cual, sin
    # mirar su fecha. Y ese fichero solo se reescribe cuando el
    # motor con permiso de escritura ejecuta; el observador que
    # regenera el dashboard corre mucho mas a menudo.
    #
    # Resultado: el 17/08 a las 20:44 la pantalla enseñaba, bajo
    # el titulo "ESTE CICLO", una escritura del 16/08 a las 18:56.
    # Mas de un dia, con fecha absoluta y sin ningun aviso. Se leia
    # como lo que parecia -"acaba de escribir"- y de ahi salio la
    # pregunta de si Pepe estaba pujando siquiera.
    #
    # El fichero no puede decir su propia edad, asi que se calcula
    # aqui y viaja con el. Que la pantalla decida como pintarlo,
    # pero que no pueda alegar que no lo sabia.
    cycle["age_seconds"] = _edad_en_segundos(
        cycle.get("timestamp")
    )

    # Un ciclo son 30 minutos. Con mas de dos ciclos de retraso
    # esto ya no es "este ciclo", es historia.
    cycle["stale"] = bool(
        cycle["age_seconds"] is not None
        and
        cycle["age_seconds"] > STALE_CYCLE_SECONDS
    )

    # ==================================================
    # INTENTAR ESCRIBIR NO ES HABER ESCRITO (19/08/2026)
    # ==================================================
    #
    # La barra lateral decia "Ultima escritura: cobrar oferta
    # aprobada" mientras el saldo seguia clavado en -4,00 M. Y era
    # verdad a medias: se habia mandado la peticion, y Biwenger
    # habia contestado HTTP 500 siete veces seguidas.
    #
    # `write_performed` no miente: significa "se envio una
    # escritura", y por eso vale True aunque falle. Esa es la
    # semantica correcta para la regla de una sola escritura por
    # ciclo -si no sabemos si llego, no se manda otra- y no se
    # toca.
    #
    # Lo que estaba mal era la pantalla, que llamaba escritura a
    # un intento fallido. En una pantalla sobre dinero, "lo ha
    # hecho" y "lo ha intentado" no pueden leerse igual.
    #
    # Es la misma familia que el ciclo viejo con cara de reciente
    # que arreglamos ayer: el dato existia -aqui mismo, en
    # `execution.success`- y nadie lo miraba al pintar.

    if write_used and action:

        salio_bien = bool(
            execution.get("success")
        )

        etiqueta = human_action(action)

        if not salio_bien:
            codigo = execution.get("http_status")

            etiqueta = (
                f"{etiqueta}: NO se completó"
                + (f" (HTTP {codigo})" if codigo else "")
            )

        last_execution = {
            **cycle,
            "timestamp": cycle.get("timestamp"),

            # Se mando la peticion. Lo que no sabemos es si el
            # otro lado hizo algo con ella.
            "write_performed": True,

            # Si el otro lado hizo algo con ella.
            "succeeded": salio_bien,

            "label": etiqueta,

            # Verificar despues de una escritura que fallo no
            # verifica nada.
            "verified_post_action": (
                post_write_verified and salio_bien
            ),
        }
        return cycle, last_execution

    # Y en el historial, lo mismo: la ultima escritura de verdad
    # es la ultima que salio bien. Si no hay ninguna se cae a la
    # ultima intentada, pero avisando de que no se completo.
    history_execution = next(
        (
            item
            for item in activity
            if item.get("write_performed")
            and item.get("success")
        ),
        None,
    )

    if history_execution is None:

        intentada = next(
            (
                item
                for item in activity
                if item.get("write_performed")
            ),
            None,
        )

        if intentada is None:
            return cycle, {}

        history_execution = {
            **intentada,
            "succeeded": False,
            "label": (
                f"{human_action(intentada.get('action'))}: "
                f"NO se completó"
            ),
        }

    return cycle, history_execution



def compact_roster(
    snapshot: dict,
    lineup_state: dict,
    photo_lookup: dict[int, dict] | None = None,
) -> dict:
    photo_lookup = photo_lookup or {}
    selected = (
        (lineup_state.get("lineup", {}) or {}).get("selected", [])
        or []
    )
    starter_ids = {
        safe_int(player.get("id"))
        for player in selected
        if isinstance(player, dict)
    }

    players = []

    for player in snapshot.get("my_team", []) or []:
        if not isinstance(player, dict):
            continue

        player_id = safe_int(player.get("id"))
        if player_id <= 0:
            continue

        photo = photo_lookup.get(player_id, {}) or {}

        players.append(
            {
                "id": player_id,
                "name": display_player_name(
                    player.get("name")
                    or photo.get("name")
                    or "?"
                ),
                "position": safe_int(player.get("position")),
                "price": safe_int(player.get("price")),
                "price_increment": safe_int(
                    player.get("priceIncrement")
                ),
                "points": safe_int(player.get("points")),
                "status": player.get("status"),
                "number": safe_int(player.get("number")),
                "is_starter": player_id in starter_ids,
                "photo_url": (
                    photo.get("photo_url")
                    or (
                        f"https://cdn.biwenger.com/cdn-cgi/image/"
                        f"f=avif/i/p/{player_id}.png"
                    )
                ),
                "photo_source": photo.get("photo_source") or "BIWENGER",
            }
        )

    players.sort(
        key=lambda item: (
            not item["is_starter"],
            safe_int(item.get("position")),
            -safe_int(item.get("price")),
        )
    )

    starters = [p for p in players if p["is_starter"]]
    substitutes = [p for p in players if not p["is_starter"]]

    return {
        "count": len(players),
        "starters": starters,
        "substitutes": substitutes,
        "players": players,
    }


def load_latest_jsonl(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    return {}


def compact_portfolio_recommendation(item: dict | None) -> dict | None:
    if not item:
        return None

    sporting = item.get("sporting_opportunity_cost", {}) or {}

    return {
        "player_names": item.get("player_names", []) or [],
        "sold_count": safe_int(item.get("sold_count")),
        "total_amount": safe_int(item.get("total_amount")),
        "post_balance": safe_int(item.get("post_balance")),
        "restores_solvency": bool(item.get("restores_solvency")),
        "playable_count": safe_int(item.get("playable_count")),
        "missing": safe_int(item.get("missing")),
        "lineup_complete": bool(item.get("lineup_complete")),
        "formation_before": item.get("formation_before"),
        "formation_after": item.get("formation_after"),
        "incoming_players": item.get("incoming_players", []) or [],
        "competitive_damage": round(
            safe_float(item.get("competitive_damage")),
            1,
        ),
        "lineup_score_before": round(
            safe_float(
                item.get(
                    "lineup_score_before",
                    sporting.get("lineup_score_before"),
                )
            ),
            2,
        ),
        "lineup_score_after": round(
            safe_float(
                item.get(
                    "lineup_score_after",
                    sporting.get("lineup_score_after"),
                )
            ),
            2,
        ),
        "lineup_score_loss": round(
            safe_float(
                item.get(
                    "lineup_score_loss",
                    sporting.get("lineup_score_loss"),
                )
            ),
            2,
        ),
        "lineup_score_loss_percent": round(
            safe_float(
                item.get(
                    "lineup_score_loss_percent",
                    sporting.get("lineup_score_loss_percent"),
                )
            ),
            2,
        ),
    }


def _select_recovery_subset(
    sources: list[dict],
    deficit: int,
    *,
    avoid_player_ids: set[int] | None = None,
    excluded_signatures: set[tuple[int, ...]] | None = None,
) -> list[dict]:
    """
    Selecciona una combinación suficiente para recuperar solvencia.

    Ranking:
    1. menor solapamiento con planes anteriores;
    2. menor exceso de caja;
    3. menos jugadores;
    4. menos fuentes.

    excluded_signatures evita repetir exactamente el mismo plan A/B/C.
    """
    clean = [
        source for source in (sources or [])
        if safe_int(source.get("amount")) > 0
    ]
    deficit = max(safe_int(deficit), 0)
    avoid_player_ids = set(avoid_player_ids or set())
    excluded_signatures = set(excluded_signatures or set())

    if not clean or deficit <= 0:
        return []

    if len(clean) <= 18:
        best = None
        best_rank = None

        for mask in range(1, 1 << len(clean)):
            selected = []
            total = 0

            for index, source in enumerate(clean):
                if mask & (1 << index):
                    selected.append(source)
                    total += safe_int(source.get("amount"))

            if total < deficit:
                continue

            player_ids = {
                safe_int(player_id)
                for source in selected
                for player_id in (source.get("player_ids", []) or [])
                if safe_int(player_id) > 0
            }
            signature = tuple(sorted(player_ids))

            if signature in excluded_signatures:
                continue

            overlap = len(
                player_ids.intersection(avoid_player_ids)
            )

            rank = (
                overlap,
                total - deficit,
                len(player_ids),
                len(selected),
                total,
            )

            if best_rank is None or rank < best_rank:
                best = selected
                best_rank = rank

        if best is not None:
            return best

    # Fallback defensivo para ligas con demasiadas fuentes.
    remaining = sorted(
        clean,
        key=lambda source: (
            len(
                {
                    safe_int(player_id)
                    for player_id in (
                        source.get("player_ids", []) or []
                    )
                    if safe_int(player_id) in avoid_player_ids
                }
            ),
            -safe_int(source.get("amount")),
        ),
    )

    selected = []
    total = 0

    while remaining and total < deficit:
        need = deficit - total
        enough = [
            source
            for source in remaining
            if safe_int(source.get("amount")) >= need
        ]

        pool = enough or remaining

        chosen = min(
            pool,
            key=lambda source: (
                len(
                    {
                        safe_int(player_id)
                        for player_id in (
                            source.get("player_ids", []) or []
                        )
                        if safe_int(player_id) in avoid_player_ids
                    }
                ),
                abs(safe_int(source.get("amount")) - need),
            ),
        )

        selected.append(chosen)
        total += safe_int(chosen.get("amount"))
        remaining.remove(chosen)

    player_ids = {
        safe_int(player_id)
        for source in selected
        for player_id in (source.get("player_ids", []) or [])
        if safe_int(player_id) > 0
    }

    if tuple(sorted(player_ids)) in excluded_signatures:
        return []

    return selected


def compact_safe_debt_recovery_plan(
    plan: dict | None,
    *,
    balance: int,
    deficit: int,
    plan_kind: str,
    avoid_player_ids: set[int] | None = None,
    excluded_signatures: set[tuple[int, ...]] | None = None,
) -> dict | None:
    if not plan:
        return None

    selected_sources = _select_recovery_subset(
        plan.get("sources", []) or [],
        deficit,
        avoid_player_ids=avoid_player_ids,
        excluded_signatures=excluded_signatures,
    )
    if not selected_sources:
        return None

    total_amount = sum(
        safe_int(source.get("amount"))
        for source in selected_sources
    )

    player_ids = []
    player_names = []
    source_kinds = []

    for source in selected_sources:
        source_kinds.append(str(source.get("kind") or "UNKNOWN"))

        for player_id in source.get("player_ids", []) or []:
            player_id = safe_int(player_id)
            if player_id > 0 and player_id not in player_ids:
                player_ids.append(player_id)

        for name in source.get("player_names", []) or []:
            name = str(name or "").strip()
            if name and name not in player_names:
                player_names.append(name)

    post_balance = safe_int(balance) + total_amount

    return {
        "source": "SAFE_DEBT_V10",
        "plan_kind": plan_kind,
        "tier": plan.get("sporting_tier") or plan.get("tier"),
        "player_ids": player_ids,
        "player_names": player_names,
        "source_kinds": source_kinds,
        "sold_count": len(player_ids),
        "total_amount": total_amount,
        "post_balance": post_balance,
        "restores_solvency": post_balance >= 0,
        "playable_count": safe_int(plan.get("playable_count")),
        "missing": safe_int(plan.get("missing")),
        "lineup_complete": bool(plan.get("lineup_complete")),
        "formation_before": None,
        "formation_after": plan.get("formation_after"),
        "incoming_players": [],
        "competitive_damage": 0.0,
        "lineup_score_before": 0.0,
        "lineup_score_after": round(safe_float(plan.get("lineup_score_after")), 2),
        "lineup_score_loss": round(safe_float(plan.get("lineup_score_loss")), 2),
        "lineup_score_loss_percent": round(
            safe_float(plan.get("lineup_score_loss_percent")),
            2,
        ),
    }


def build_dashboard_solvency_plans(state: dict) -> dict:
    """
    V10.7.2C

    A: Tier A, no tocar XI.
    B: B1 trading-safe, buscando una combinación distinta de A.
    C: Tier C de contingencia, buscando minimizar solapamiento con A+B.

    Si un tier no puede producir una combinación distinta, usa B2 como
    fallback antes de renunciar al plan.
    """
    solvency = state.get("solvency", {}) or {}
    portfolio = solvency.get("safe_liquidity_portfolio", {}) or {}
    balance = safe_int(
        solvency.get("balance", state.get("balance"))
    )
    deficit = max(-balance, 0)

    if deficit <= 0 or not portfolio:
        return {
            "available": False,
            "source": "SAFE_DEBT_V10",
            "deficit": deficit,
            "plans": [],
            "a": None,
            "b": None,
            "c": None,
        }

    used_players: set[int] = set()
    used_signatures: set[tuple[int, ...]] = set()

    def add_plan(kind: str, raw: dict | None) -> dict | None:
        plan = compact_safe_debt_recovery_plan(
            raw,
            balance=balance,
            deficit=deficit,
            plan_kind=kind,
            avoid_player_ids=used_players,
            excluded_signatures=used_signatures,
        )

        if not plan:
            return None

        signature = tuple(
            sorted(
                safe_int(player_id)
                for player_id in (
                    plan.get("player_ids", []) or []
                )
                if safe_int(player_id) > 0
            )
        )

        used_signatures.add(signature)
        used_players.update(signature)
        return plan

    plan_a = add_plan(
        "A_NO_XI",
        portfolio.get("tier_a"),
    )

    plan_b = add_plan(
        "B1_TRADING_SAFE",
        portfolio.get("trading_safe"),
    )

    if plan_b is None:
        plan_b = add_plan(
            "B2_FULL_XI",
            portfolio.get("tier_b"),
        )

    plan_c = add_plan(
        "C_EMERGENCY_10_OF_11",
        portfolio.get("tier_c"),
    )

    # Si Tier C no aporta una alternativa distinta, probamos B2 si aún
    # tiene otra combinación diferente. Sigue siendo un Plan C de respaldo,
    # pero sin inventar liquidez ni repetir A/B.
    if plan_c is None:
        plan_c = add_plan(
            "C_FALLBACK_B2_DISTINCT",
            portfolio.get("tier_b"),
        )

    selected = [plan_a, plan_b, plan_c]

    return {
        "available": any(plan is not None for plan in selected),
        "source": "SAFE_DEBT_V10",
        "policy": portfolio.get("policy"),
        "deficit": deficit,
        "gross_source_total": safe_int(
            portfolio.get("gross_source_total")
        ),
        "trading_safe_total": safe_int(
            portfolio.get("trading_safe_total")
        ),
        "emergency_complete_total": safe_int(
            portfolio.get("emergency_complete_total")
        ),
        "emergency_ten_total": safe_int(
            portfolio.get("emergency_ten_total")
        ),
        "plans": [
            plan
            for plan in selected
            if plan is not None
        ],
        "a": plan_a,
        "b": plan_b,
        "c": plan_c,
    }


def compact_competitive_offer(item: dict) -> dict:
    negotiation = item.get("negotiation", {}) or {}
    replacement = item.get("replacement_detail", {}) or {}
    sporting = item.get("sporting_opportunity_cost", {}) or {}

    incoming = []

    for player in replacement.get("incoming_players", []) or []:
        if not isinstance(player, dict):
            continue

        player_id = safe_int(player.get("id"))

        incoming.append(
            {
                "id": player_id,
                "name": display_player_name(
                    player.get("name")
                    or (
                        f"Player {player_id}"
                        if player_id > 0
                        else "?"
                    )
                ),
                "position": safe_int(player.get("position")),
                "lineup_score": round(
                    safe_float(
                        player.get(
                            "lineup_score",
                            player.get("quality_score"),
                        )
                    ),
                    2,
                ),
                "photo_url": (
                    f"https://cdn.biwenger.com/cdn-cgi/image/"
                    f"f=avif/i/p/{player_id}.png"
                    if player_id > 0
                    else None
                ),
            }
        )

    return {
        "offer_id": item.get("offer_id"),
        "player_id": safe_int(item.get("player_id")),
        "player_name": item.get("player_name") or "?",
        "rival_name": item.get("rival_name") or "Rival",
        "amount": safe_int(item.get("amount")),
        "decision_authority": item.get("decision_authority"),
        "authoritative_decision": item.get("authoritative_decision"),
        "authoritative_counter_amount": safe_int(
            item.get("authoritative_counter_amount")
            or item.get("counter_amount")
        ),
        "strategic_sell_price": safe_int(item.get("strategic_sell_price")),
        "competitive_premium_percent": round(
            safe_float(item.get("competitive_premium_percent")),
            2,
        ),
        "temporal_premium_percent": round(
            safe_float(item.get("temporal_premium_percent")),
            2,
        ),
        "sporting_premium_percent": round(
            safe_float(item.get("sporting_premium_percent")),
            2,
        ),
        "solvency_discount_percent": round(
            safe_float(item.get("solvency_discount_percent")),
            2,
        ),
        "rival_reinforcement_score": round(
            safe_float(item.get("rival_reinforcement_score")),
            1,
        ),
        "sporting_cost_score": round(
            safe_float(item.get("sporting_cost_score")),
            1,
        ),
        "negotiation_event": negotiation.get("event"),
        "action_gate": negotiation.get("action_gate"),
        "negotiation_round": safe_int(negotiation.get("negotiation_round")),
        "should_respond": bool(negotiation.get("should_respond")),
        "negotiation_status": negotiation.get("status"),
        "replacement_status": (
            replacement.get("replacement_status")
            or (item.get("replacement", {}) or {}).get("replacement_status")
        ),
        "replacement_source": replacement.get("replacement_source"),
        "pre_sale_playable_count": safe_int(
            replacement.get("pre_sale_playable_count")
        ),
        "post_sale_playable_count": safe_int(
            replacement.get("post_sale_playable_count")
        ),
        "formation_before": replacement.get("formation_before"),
        "formation_after": replacement.get("formation_after"),
        "incoming_players": incoming,
        "lineup_score_before": round(
            safe_float(sporting.get("lineup_score_before")),
            2,
        ),
        "lineup_score_after": round(
            safe_float(sporting.get("lineup_score_after")),
            2,
        ),
        "lineup_score_loss": round(
            safe_float(sporting.get("lineup_score_loss")),
            2,
        ),
        "lineup_score_loss_percent": round(
            safe_float(sporting.get("lineup_score_loss_percent")),
            2,
        ),
    }


def load_competitive_dashboard_state() -> dict:
    record = load_latest_jsonl(COMPETITIVE_LOG)

    if not record:
        return {
            "available": False,
            "live_enabled": True,
            "status": "SIN_TELEMETRIA",
            "status_label": "SIN TELEMETRÍA COMPETITIVE",
            "message": "Aún no existe competitive_observer_log.jsonl.",
            "offers": [],
            "portfolio": {},
        }

    offers = [
        compact_competitive_offer(item)
        for item in record.get("manager_offers", []) or []
    ]

    responding = [item for item in offers if item.get("should_respond")]
    waiting = [
        item
        for item in offers
        if item.get("action_gate") == "NO_ACTION_WAITING_RIVAL"
    ]

    if responding:
        status = "ACTIONABLE"
        status_label = "PEPE TIENE RESPUESTA PENDIENTE"
        message = (
            f"{len(responding)} negociación(es) requieren recalcular/responder. "
            "La ejecución real sigue dependiendo del Safety Gate del ciclo."
        )
    elif offers and len(waiting) == len(offers):
        status = "WAITING_RIVAL"
        status_label = "PEPE ESPERANDO AL RIVAL"
        message = "Las ofertas observadas no han cambiado desde la última respuesta."
    elif offers:
        status = "MONITORING"
        status_label = "PEPE VIGILANDO NEGOCIACIONES"
        message = "Competitive V2.0 está siguiendo ofertas activas de managers."
    else:
        status = "IDLE"
        status_label = "SIN OFERTAS DE MANAGERS"
        message = "Competitive V2.0 está activo y no hay negociaciones de managers."

    portfolio = record.get("competitive_portfolio", {}) or {}

    current_state = portfolio.get("current", {}) or {}
    strategic_state = portfolio.get("strategic", {}) or {}

    current = current_state.get("recommended") or {}
    strategic = strategic_state.get("recommended") or {}

    strategic_alternatives = [
        compact_portfolio_recommendation(item)
        for item in (
            strategic_state.get("solvency_combinations", [])
            or []
        )[:5]
        if item
    ]

    current_alternatives = [
        compact_portfolio_recommendation(item)
        for item in (
            current_state.get("solvency_combinations", [])
            or []
        )[:5]
        if item
    ]

    return {
        "available": bool(record.get("available", True)),
        "live_enabled": True,
        "source_timestamp": record.get("timestamp"),
        "snapshot": record.get("snapshot"),
        "status": status,
        "status_label": status_label,
        "message": message,
        "offer_count": len(offers),
        "responding_count": len(responding),
        "waiting_count": len(waiting),
        "offers": offers,
        "portfolio": {
            "balance": safe_int(portfolio.get("balance")),
            "deficit": safe_int(portfolio.get("deficit")),
            "current": compact_portfolio_recommendation(current),
            "strategic": compact_portfolio_recommendation(strategic),
            "strategic_alternatives": strategic_alternatives,
            "current_alternatives": current_alternatives,
        },
        # El log Competitive V2.0 actual persiste ofertas + portfolio, pero no
        # el Safety Gate ni competitive_execution. No inventamos esos datos.
        "safety_gate_persisted": False,
        "execution_persisted": False,
    }


def _normalize_display_text(value) -> str:
    text = str(value or "")
    try:
        repaired = text.encode("latin1").decode("utf-8")
        if repaired:
            return repaired
    except Exception:
        pass
    return text


def load_recent_competitive_closed(
    hours: float = 12.0,
) -> list[dict]:
    """
    Reconstruye cierres recientes comparando manager_offers
    entre snapshots consecutivos del observer.

    Si una oferta existía en N y desaparece en N+1:
    RETIRADA POR RIVAL.
    """
    if not COMPETITIVE_LOG.exists():
        return []

    try:
        raw_lines = COMPETITIVE_LOG.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return []

    records = []

    for line in raw_lines[-500:]:
        try:
            record = json.loads(line)
        except Exception:
            continue

        timestamp = record.get("timestamp")
        manager_offers = (
            record.get("manager_offers")
            or []
        )

        if timestamp and isinstance(
            manager_offers,
            list,
        ):
            records.append(
                (timestamp, manager_offers)
            )

    if len(records) < 2:
        return []

    now = datetime.now()
    closed_by_key = {}

    for index in range(
        1,
        len(records),
    ):
        previous_ts, previous_offers = (
            records[index - 1]
        )
        current_ts, current_offers = (
            records[index]
        )

        previous_map = {}

        for offer in previous_offers:
            player_id = safe_int(
                offer.get("player_id")
            )

            rival_name = (
                _normalize_display_text(
                    offer.get("rival_name")
                    or "Rival"
                )
            )

            if player_id <= 0:
                continue

            previous_map[
                (player_id, rival_name)
            ] = offer

        current_keys = set()

        for offer in current_offers:
            player_id = safe_int(
                offer.get("player_id")
            )

            rival_name = (
                _normalize_display_text(
                    offer.get("rival_name")
                    or "Rival"
                )
            )

            if player_id <= 0:
                continue

            current_keys.add(
                (player_id, rival_name)
            )

        try:
            closed_dt = datetime.fromisoformat(
                str(current_ts)
            )
            age_hours = (
                now - closed_dt
            ).total_seconds() / 3600.0
        except Exception:
            continue

        if not (
            0 <= age_hours <= hours
        ):
            continue

        for key, old_offer in (
            previous_map.items()
        ):
            if key in current_keys:
                continue

            player_id, rival_name = key

            closed_by_key[key] = {
                "player_id": player_id,
                "player_name": (
                    _normalize_display_text(
                        old_offer.get(
                            "player_name"
                        )
                        or "?"
                    )
                ),
                "rival_name": rival_name,
                "amount": safe_int(
                    old_offer.get("amount")
                ),
                "authoritative_counter_amount": (
                    safe_int(
                        old_offer.get(
                            "authoritative_counter_amount"
                        )
                        or old_offer.get(
                            "counter_amount"
                        )
                        or old_offer.get(
                            "strategic_amount"
                        )
                    )
                ),
                "closed_at": current_ts,
                "closed_status": (
                    "RIVAL_WITHDREW"
                ),
                "closed_label": (
                    "RETIRADA POR RIVAL"
                ),
                "previous_snapshot_timestamp": (
                    previous_ts
                ),
            }

    # HARD TELEMETRY SAFETY:
    # anything still present in the latest observer snapshot
    # is ACTIVE and must never be reported as withdrawn/rejected.
    latest_active_keys = set()

    if records:
        _, latest_offers = records[-1]

        for offer in latest_offers:
            player_id = safe_int(
                offer.get("player_id")
            )

            rival_name = (
                _normalize_display_text(
                    offer.get("rival_name")
                    or "Rival"
                )
            )

            if player_id > 0:
                latest_active_keys.add(
                    (player_id, rival_name)
                )

    safe_closed = [
        item
        for key, item in closed_by_key.items()
        if key not in latest_active_keys
    ]

    return sorted(
        safe_closed,
        key=lambda item: (
            item.get("closed_at")
            or ""
        ),
        reverse=True,
    )


def compact_biwenger_competition(
    snapshot: dict,
    current_user_id=None,
) -> dict:
    """Expose the fantasy competition standings already returned by Biwenger.

    Source in the snapshot:
        rounds.data.league.standings

    Observer-only: this reads existing snapshot data and performs no writes.
    """
    league = (
        snapshot.get("rounds", {})
        .get("data", {})
        .get("league", {})
        or {}
    )

    rows = league.get("standings", []) or []
    current_user_id = safe_int(current_user_id, default=0)

    standings = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        user_id = safe_int(row.get("id"))
        rank = safe_int(row.get("position"), default=index)

        standings.append({
            "rank": rank or index,
            "user_id": user_id,
            "name": str(row.get("name") or f"Mánager {index}"),
            "points": safe_int(row.get("points")),
            "team_value": safe_int(row.get("teamValue")),
            "team_value_inc": safe_int(row.get("teamValueInc")),
            "icon": row.get("icon"),
            "is_current_user": bool(
                current_user_id
                and user_id
                and user_id == current_user_id
            ),
        })

    standings.sort(key=lambda item: item.get("rank", 9999))

    current_row = next(
        (item for item in standings if item.get("is_current_user")),
        None,
    )

    return {
        "id": safe_int(league.get("id")),
        "name": league.get("name") or "Biwenger",
        "competition": league.get("competition"),
        "mode": league.get("mode"),
        "type": league.get("type"),
        "standings": standings,
        "current_user_rank": (
            current_row.get("rank") if current_row else None
        ),
        "current_user_points": (
            current_row.get("points") if current_row else None
        ),
    }

def _starter_confidence(
    starter_probability,
    external_confidence,
):
    """
    Probabilidad de ser titular, o None si no la sabemos.

    Nunca devuelve 0: si no hay medicion se dice que no la hay y
    la interfaz pinta "sin dato".
    """

    for candidato in (starter_probability, external_confidence):

        if candidato is None:
            continue

        valor = safe_float(candidato)

        if valor > 0:
            return round(valor, 1)

    return None


def compact_guardrail(liquidity: dict) -> dict:
    """
    Estado posicional: cuantos tengo, cuantos necesito para poder
    alinear, cuantos sobran.
    """

    guardrail = (liquidity or {}).get("position_guardrail") or {}

    if not guardrail.get("available"):
        return {"available": False}

    return {
        "available": True,
        "by_position": [
            {
                "position": datos["position"],
                "name": datos["position_name"],
                "owned": datos["owned"],
                "floor": datos["floor"],
                "desired": datos["desired"],
                "disposable": datos["disposable"],
                "at_floor": datos["at_floor"],
                "below_desired": datos["below_desired"],
            }
            for datos in (
                guardrail.get("by_position") or {}
            ).values()
        ],
        "goalkeeper_warning": guardrail.get("goalkeeper_warning"),
        "positions_to_replenish": guardrail.get(
            "positions_to_replenish", []
        ),
    }


def compact_exposure(state: dict) -> dict:
    """
    Dinero comprometido en pujas vivas y cuanto queda libre.
    """

    speculation = state.get("speculation", {}) or {}
    exposure = speculation.get("bid_exposure") or {}
    budget = speculation.get("budget", {}) or {}

    return {
        "available": bool(exposure.get("available")),
        "committed_total": safe_int(exposure.get("committed_total")),
        "operation_count": safe_int(exposure.get("operation_count")),
        "operations": [
            {
                "offer_id": item.get("offer_id"),
                "amount": safe_int(item.get("amount")),
                "player_ids": item.get("player_ids", []),
            }
            for item in (exposure.get("operations") or [])[:8]
        ],
        "total_budget": safe_int(budget.get("total_budget")),
        "available_budget": safe_int(
            budget.get("available_budget", budget.get("total_budget"))
        ),
        "cash_budget": safe_int(budget.get("cash_budget")),
        "debt_budget": safe_int(budget.get("debt_budget")),
        "mode": budget.get("mode"),
        "blocked_by": budget.get("blocked_by"),
        "reason": budget.get("reason"),
    }


def compact_ledger_audit(audit: dict) -> dict:
    """
    ¿Sabemos explicar la plantilla de cada rival?
    """

    if not audit or not audit.get("available"):
        return {
            "available": False,
            "status": (audit or {}).get("status"),
            "reason": (audit or {}).get("reason"),
        }

    return {
        "available": True,
        "status": audit.get("status"),
        "min_coverage": audit.get("min_coverage"),
        "reason": audit.get("reason"),
        "managers_with_gaps": audit.get("managers_with_gaps", []),
        "by_manager": [
            {
                "name": datos.get("name"),
                "is_us": datos.get("is_us"),
                "coverage": datos.get("coverage"),
                "roster_size": datos.get("roster_size"),
                "from_initial_draft": datos.get("from_initial_draft"),
                "acquired": datos.get("acquired"),
                "explained": datos.get("explained"),
                "unexplained": [
                    j.get("name")
                    for j in (datos.get("unexplained") or [])
                ],
            }
            for datos in (audit.get("by_manager") or {}).values()
            if datos.get("auditable")
        ],
    }


def build_dashboard_state() -> dict:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    # Observer puro: recalcula, pero no ejecuta.
    result = build_global_decision(snapshot)
    state = result.get("state", {}) or {}
    decision = result.get("decision", {}) or {}
    action_decision = result.get("action_decision", {}) or {}

    # El bloque de ofertas del ciclo. Lleva dentro el veredicto de
    # Offer Decision Engine V2 y cual se cobra ahora, que hasta el
    # 18/08/2026 se calculaba y no salia por ninguna pantalla.
    offer_intelligence = next(
        (
            (item.get("data") or {})
            for item in (result.get("candidates") or [])
            if item.get("type") == "OFFER_DECISION_INTELLIGENCE"
        ),
        {},
    )

    board = collect_board_history()

    market_status = (
        snapshot.get("market", {})
        .get("status", {})
        or {}
    )

    rival_intelligence = build_rival_intelligence(
        events=board.get("events", []),
        users=board.get("users", []),
        profiles=board.get("profiles", []),
        catalog=snapshot.get("catalog", {}),
        current_user_id=board.get("current_user_id"),
        own_finances=board.get("own_finances", {}),
        own_balance=market_status.get("balance"),
        own_maximum_bid=market_status.get("maximumBid"),
    )

    save_rival_intelligence(rival_intelligence)

    # Conciliacion jugador a jugador: ¿sabemos explicar la
    # plantilla de cada rival? Sin esto, el panel podia decir que
    # un manager no habia comprado nada cuando lo que pasaba es
    # que no lo habiamos visto.
    ledger_audit = audit_rival_ledger(
        rival_intelligence,
        own_user_id=board.get("current_user_id"),
    )

    league_center = build_league_center(
        snapshot=snapshot,
        board=board,
        rival_intelligence=rival_intelligence,
    )

    competition = compact_biwenger_competition(
        snapshot=snapshot,
        current_user_id=board.get("current_user_id"),
    )

    deadline = state.get("deadline", {}) or {}
    temporal_gate = state.get("temporal_gate", {}) or {}
    liquidity = state.get("liquidity", {}) or {}
    recovery = liquidity.get("recovery", {}) or {}
    franchise = state.get("franchise", {}) or {}
    target = franchise.get("target", {}) or {}

    candidates = [
        human_candidate(candidate)
        for candidate in result.get("candidates", [])[:7]
    ]

    # El otro reloj: el reset del Computer. La operativa diaria
    # depende de el, no del deadline de jornada.
    try:
        market_clock = build_market_clock(snapshot)

    except Exception as clock_error:
        market_clock = {
            "available": False,
            "window_state": "UNKNOWN",
            "reason": f"{type(clock_error).__name__}: {clock_error}",
        }

    exposure = compact_exposure(state)

    acquisition = build_acquisition_board(
        snapshot=snapshot,
        rival_intelligence=rival_intelligence,
        current_user_id=board.get("current_user_id"),
        available_budget=exposure.get("available_budget") or None,
    )

    points_market = calibrate_points_market(
        snapshot.get("catalog", {})
    )

    photo_lookup = build_player_photo_lookup(
        snapshot
    )

    competitive = load_competitive_dashboard_state()
    solvency_plans = build_dashboard_solvency_plans(state)
    activity = load_activity_feed()
    cycle_telemetry, last_execution = build_execution_telemetry(
        activity
    )

    for offer in competitive.get("offers", []) or []:
        player_id = safe_int(
            offer.get("player_id")
        )
        photo = photo_lookup.get(
            player_id,
            {}
        )
        offer["api_football_id"] = (
            photo.get("api_football_id")
        )
        offer["photo_url"] = (
            photo.get("photo_url")
        )
        offer["icon_hero"] = (
            photo.get("icon_hero")
        )

    recent_closed = load_recent_competitive_closed()
    for closed in recent_closed:
        photo = photo_lookup.get(safe_int(closed.get("player_id")), {})
        closed["photo_url"] = photo.get("photo_url")
        closed["icon_hero"] = photo.get("icon_hero")
    competitive["recent_closed"] = recent_closed

    competitive_status = competitive.get("status")

    if competitive_status == "ACTIONABLE":
        pepe_now = {
            "level": "ACTION",
            "title": "Pepe tiene una respuesta competitiva pendiente",
            "detail": (
                f"{safe_int(competitive.get('responding_count'))} negociación(es) "
                "requieren recalcular y pasar Safety Gate."
            ),
        }
    elif competitive_status == "WAITING_RIVAL":
        recent_closed = (
            competitive.get(
                "recent_closed",
                [],
            )
            or []
        )

        if recent_closed:
            latest_closed = (
                recent_closed[0]
            )

            pepe_now = {
                "level": "WAIT",
                "title": (
                    "Movimiento rival detectado"
                ),
                "detail": (
                    f"{latest_closed.get('rival_name', 'El rival')} "
                    f"retiró su oferta por "
                    f"{latest_closed.get('player_name', 'un jugador')}. "
                    "Bordalás lo ha registrado y mantiene abiertas "
                    "las negociaciones restantes."
                ),
            }
        else:
            pepe_now = {
                "level": "WAIT",
                "title": "Esperar al rival",
                "detail": (
                    "No hay nuevos movimientos desde la última respuesta. "
                    "Bordalás no repetirá contraofertas mientras espera al rival."
                ),
            }

    elif bool(recovery.get("needed")):
        pepe_now = {
            "level": "SOLVENCY",
            "title": "Prioridad: recuperar solvencia",
            "detail": (
                f"Déficit actual de {safe_int(recovery.get('deficit')):,} EUR. "
                "Pepe mantiene el XI válido mientras busca la salida más eficiente."
            ),
        }
    else:
        pepe_now = {
            "level": "OK",
            "title": human_action(decision.get("action")),
            "detail": decision.get("reason") or "Sin urgencias críticas.",
        }

    dashboard = {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "snapshot": snapshot_file,
            "league_id": board.get("league_id"),
            "current_user_id": board.get("current_user_id"),
            "mode": "LIVE",
            "cycle_minutes": 30,
        },
        "summary": {
            "balance": safe_int(state.get("balance")),
            "maximum_bid": safe_int(market_status.get("maximumBid")),
            "target_matchday": state.get("target_matchday"),
            "phase": state.get("phase"),
            "hours_to_deadline": round(
                safe_float(state.get("hours_to_deadline")),
                2,
            ),
            "lineup_risk": state.get("lineup_risk"),
            "lineup_pressure": safe_int(
                state.get("lineup_pressure_score")
            ),
            "hard_safety": bool(
                temporal_gate.get(
                    "hard_safety_mode",
                    temporal_gate.get("hard_safety", False),
                )
            ),
            "operations_locked": bool(
                temporal_gate.get(
                    "operations_locked",
                    state.get("operations_locked", False),
                )
            ),
        },
        "pepe_now": pepe_now,
        "decision": {
            "type": decision.get("type"),
            "action": decision.get("action"),
            "label": human_action(decision.get("action")),
            "priority": safe_int(decision.get("priority")),
            "executable": bool(decision.get("executable")),
            "reason": decision.get("reason"),
        },
        "next_action": {
            "type": action_decision.get("type"),
            "action": action_decision.get("action"),
            "label": (
                human_action(action_decision.get("action"))
                if action_decision
                else None
            ),
            "priority": safe_int(action_decision.get("priority")),
            "executable": bool(action_decision.get("executable")),
            "reason": action_decision.get("reason"),
        },
        "cycle": cycle_telemetry,
        "last_execution": last_execution,
        # Acciones apartadas temporalmente porque su escritura
        # falla en Biwenger. Se muestran para que un fallo
        # persistente no quede escondido.
        "backoff": result.get("failure_backoff") or {
            "blocked": [],
            "blocked_count": 0,
        },
        "solvency": {
            "needed": bool(recovery.get("needed")),
            "possible": recovery.get("possible"),
            "deficit": safe_int(recovery.get("deficit")),
            "incoming_offers": safe_int(
                liquidity.get("incoming_offer_count")
            ),
            "listed": safe_int(liquidity.get("listing_count")),
            "to_list": safe_int(liquidity.get("to_list_count")),
            "plans": solvency_plans,
        },
        "franchise": {
            "state": franchise.get("state"),
            "target": target.get("name"),
            "score": target.get("franchise_score"),
            "price": safe_int(
                target.get("price", target.get("market_price"))
            ),
            "price_increment": safe_int(
                target.get(
                    "price_increment",
                    target.get("priceIncrement"),
                )
            ),
        },
        "lineup": compact_lineup(
            state.get("lineup", {}) or {},
            snapshot,
            photo_lookup,
        ),
        "roster": compact_roster(
            snapshot,
            state.get("lineup", {}) or {},
            photo_lookup,
        ),
        "rival_intelligence": {
            "ledger_status": rival_intelligence.get("ledger_status"),
            "maximum_bid_calibration": rival_intelligence.get(
                "maximum_bid_calibration"
            ),
            "managers": compact_rivals(
                rival_intelligence,
                board.get("current_user_id"),
            ),
        },
        "league_center": league_center,
        "competition": competition,
        "offers": compact_offers(
            state,
            offer_decisions=offer_intelligence.get(
                "offer_decisions"
            ),
            collecting={
                "offer_id": (
                    offer_intelligence.get("offer") or {}
                ).get("offer_id"),

                "queued": offer_intelligence.get(
                    "queued_to_collect"
                ),
            },
        ),
        "speculation": compact_speculation(state),
        "listings": compact_listings(state),
        "market_clock": market_clock,
        "position_guardrail": compact_guardrail(liquidity),
        "exposure": exposure,
        "acquisition": acquisition,
        "points_market": points_market,
        "ledger_audit": compact_ledger_audit(ledger_audit),
        "priorities": candidates,
        "activity": activity,
        "competitive": competitive,
    }

    # LO ULTIMO, Y A PROPOSITO.
    #
    # Se audita el payload ya montado contra el snapshot, que es
    # la verdad. Si una parte de la pantalla sabe algo que otra
    # no -tres pujas vivas en CAJA y cero en OBJETIVOS-, sale
    # aqui y la interfaz lo grita en rojo.
    #
    # No corrige: levanta la mano. Un dashboard que se equivoca
    # en silencio es peor que uno que falta.
    from src.telemetry.dashboard_consistency import (
        build_consistency_report,
    )

    dashboard["consistency"] = build_consistency_report(
        dashboard,
        snapshot,
        current_user_id=board.get("current_user_id"),
    )

    return dashboard


def save_dashboard_state(
    state: dict,
    path: Path = DASHBOARD_STATUS,
) -> Path:
    """Persist one canonical dashboard payload for production and local React.

    Production/legacy Cloudflare assets read dashboard/data/status.json.
    Vite local development reads dashboard-v8/public/data/status.json.
    Keeping both mirrors in this single write path prevents the React UI from
    silently displaying stale telemetry after backend fields are added.
    """
    payload = json.dumps(
        state,
        ensure_ascii=False,
        indent=2,
    )

    targets = [path]

    # Only mirror the default dashboard status.  Explicit custom paths used by
    # tests/tools remain isolated and retain the old behavior.
    if Path(path) == DASHBOARD_STATUS:
        targets.append(REACT_DASHBOARD_STATUS)

    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")

    return path
