from __future__ import annotations

import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

from src.intelligence.bid_outcome_ledger import (
    summary as bid_outcome_summary,
)

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
from src.telemetry.squads import (
    build_rival_squads,
    enrich_roster,
)
from src.analysis.marcador import (
    observar as anotar_jornada,
    estado_para_dashboard as build_marcador,
)
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


# LA CADENCIA SALE DEL CRON, NO DE LA MEMORIA (10/09/2026)
#
#     El cron interno de `bordalas-live.yml` es la AUTORIDAD:
#
#         7 0-2,7-23 * * *
#
#     o sea, una vez a la hora. Aqui ponia 30 escrito a mano,
#     de cuando el cron corria cada media hora, y al cambiarlo
#     nadie toco esto: el aviso amarillo decia "cada 30", el
#     lateral "ciclo 30 min" y `STALE_CYCLE_SECONDS` marcaba
#     rancio un ciclo perfectamente normal a la hora de vida.
#
#     `test_la_cadencia_sale_del_cron` compara este numero con
#     el cron del workflow y con `relojes.js`, para que los tres
#     no puedan volver a discrepar.
CRON_INTERNO = "7 0-2,7-23 * * *"

CADENCIA_MINUTOS = 60


# A partir de cuando "este ciclo" deja de ser este ciclo.
#
# Dos ciclos de margen absorben un retraso normal -un refresco
# lento, una cola de GitHub-; a partir de ahi lo que se esta
# enseñando es historia y hay que decirlo.
STALE_CYCLE_SECONDS = 2 * CADENCIA_MINUTOS * 60


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

    # Las que no llevan veredicto, dichas por su nombre en vez de
    # dejar la casilla en blanco.
    "OFFER_EXPIRED": "Caducada",
    "MANAGER_OFFER": "De un mánager: no la decide el motor",
    "NOT_EVALUATED": "Sin analizar",

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

                # UNA JERARQUIA TOCADA A MANO TIENE QUE VERSE
                # TOCADA A MANO (22/08/2026)
                #
                # Es lo unico que separa una correccion de una
                # mentira. Si en pantalla se pinta igual que la de
                # FF, dentro de tres semanas nadie sabra cual es
                # cual -ni yo-.
                "hierarchy_source": senal_ff.get("hierarchy_source"),
                "hierarchy_override": senal_ff.get(
                    "hierarchy_override"
                ),

                "availability": (
                    (senal_ff.get("availability") or {}).get("label")
                ),
                "absence": senal_ff.get("absence"),

                # CONTRA QUIEN Y DONDE (19/08/2026)
                #
                # El motor de valor ya usa el rival y el campo
                # desde el 18/08 -un partido fuera contra el Barsa
                # no vale lo mismo que uno en casa contra el
                # Elche- pero eso se quedaba dentro del calculo.
                # Para explicar un XI hace falta poder decir a
                # quien se enfrenta cada uno.
                "next_match": senal_ff.get("next_match") or {},

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

    # EL 11/11 EN VERDE MENTIA (20/08/2026)
    #
    # El dueño se encontro un 5-3-2 en esta pantalla, un 4-3-3 en
    # Biwenger y esta cabecera diciendo 11/11 tan contenta. El
    # 11/11 era del once IMAGINADO; el que iba a jugar era otro.
    #
    # Se compara con lo que hay puesto de verdad y se publica la
    # diferencia. Blindado: si falla, se pintan menos columnas,
    # pero no se tumba la telemetria.
    try:
        from src.analysis.lineup_monitor import (
            compare_with_live,
            live_lineup,
        )

        once_real = compare_with_live(
            live_lineup(snapshot),
            lineup.get("selected", []) or [],
            lineup.get("formation_name"),
        )

    except Exception as error:                      # noqa: BLE001
        once_real = {
            "known": False,
            "matches": None,
            "reason": f"No se pudo leer el XI real: {error}",
        }

    # POSIBLES CAMBIOS (10/09/2026)
    #
    # El banquillo con el motivo que dio el motor al descartarlo.
    # No se decide nada aqui: `banquillo_con_motivo` lee lo que
    # `build_lineup` ya comparo. Solo se le pega la foto, para
    # que el panel no tenga que buscarla.
    banquillo = []

    for fila in lineup.get("bench") or []:

        if not isinstance(fila, dict):
            continue

        foto = photo_lookup.get(safe_int(fila.get("id"))) or {}

        banquillo.append(
            {
                **fila,
                "photo_url": (
                    foto.get("photo_url")
                    or (
                        f"https://cdn.biwenger.com/cdn-cgi/image/"
                        f"f=avif/i/p/{safe_int(fila.get('id'))}.png"
                    )
                ),
            }
        )

    return {
        "formation": lineup.get("formation_name"),
        # Los suplentes, y POR QUE cada uno se queda fuera.
        # Va tambien en su bloque propio -`posibles_cambios`-
        # porque el panel que lo pinta es suyo y tiene que poder
        # decir "no se sabe" sin arrastrar al XI.
        "bench": banquillo,


        # Lo que hay puesto en Biwenger y en que se diferencia.
        "live": once_real,

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

        # EL TABLERO RECHAZADO SE DICE EN ALTO (05/09/2026)
        #
        # Si es de otra jornada, no alimenta nada: ni el XI, ni la
        # valoracion de fichajes. Pepe se queda quieto a
        # proposito. Fallar cerrado esta bien; fallar en silencio
        # dejaria al dueño dias preguntandose que le pasa.
        "starter_board_rejected": bool(tablero.get("rejected")),
        "starter_board_rejection_reason": tablero.get(
            "rejection_reason"
        ),
        "starter_expected_matchday": tablero.get(
            "expected_matchday"
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

                # EL ABONO DE LAS JORNADAS (20/08/2026)
                #
                # 30.000 EUR por punto, que Biwenger paga al
                # cerrar cada jornada. Es la mitad de la economia
                # del juego y hasta hoy no estaba en ningun
                # libro. Sale en pantalla porque explica una
                # parte grande del saldo de cada rival.
                "matchday_bonus": safe_int(
                    manager.get("matchday_bonus")
                ),
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


SIN_ANALIZAR_POR_CADUCADA = "OFFER_EXPIRED"
SIN_ANALIZAR_POR_MANAGER = "MANAGER_OFFER"
SIN_ANALIZAR_SIN_MOTIVO = "NOT_EVALUATED"


def _por_que_no_se_analiza(entrante: dict) -> str:
    """
    Por que una oferta no lleva veredicto, dicho por su nombre.

    Una fila en blanco se lee como un fallo. Una fila que dice
    "caducada" o "de un manager" se lee como lo que es.
    """

    if entrante.get("expired"):
        return SIN_ANALIZAR_POR_CADUCADA

    if entrante.get("counterparty") != "COMPUTER":
        return SIN_ANALIZAR_POR_MANAGER

    return SIN_ANALIZAR_SIN_MOTIVO


def _ofertas_entrantes(
    snapshot: dict | None,
    current_user_id=None,
) -> list[dict]:
    """
    Las ofertas de compra por jugadores nuestros, del snapshot.

    MISMA REGLA QUE EL CHEQUEO DE CONSISTENCIA

        Una oferta es entrante si no sale de nosotros. Punto. Es
        literalmente lo que cuenta `dashboard_consistency`, y por
        eso se escribe igual aqui: dos recuentos de la misma cosa
        que se calculan por caminos distintos acaban discrepando
        siempre, y el dueño se come un aviso rojo permanente que
        no significa nada.
    """

    mercado = (snapshot or {}).get("market") or {}

    ahora = datetime.now().timestamp()

    entrantes = []

    for oferta in (mercado.get("offers") or []):

        if not isinstance(oferta, dict):
            continue

        emisor = oferta.get("from")
        emisor = emisor if isinstance(emisor, dict) else {}

        if (
            current_user_id is not None
            and safe_int(emisor.get("id"))
            == safe_int(current_user_id)
        ):
            continue

        hasta = oferta.get("until")

        horas = None
        caducada = False

        if hasta is not None:
            try:
                horas = round(
                    (float(hasta) - ahora) / 3600.0,
                    1,
                )
                caducada = horas <= 0

            except (TypeError, ValueError):
                horas = None

        entrantes.append(
            {
                "offer_id": oferta.get("id"),

                "amount": safe_int(oferta.get("amount")),

                "player_names": _nombres_de_jugadores(
                    snapshot,
                    oferta.get("requestedPlayers") or [],
                ),

                # El Computer llega con from=None; un manager
                # llega con su ficha.
                "counterparty": (
                    emisor.get("name")
                    if emisor
                    else "COMPUTER"
                ),

                "status": oferta.get("status"),
                "expired": caducada,
                "hours_to_expiry": horas,
            }
        )

    return entrantes


def _nombres_de_jugadores(
    snapshot: dict | None,
    player_ids: list,
) -> list[str]:
    """
    De ids a nombres, mirando primero nuestra plantilla.

    Si un id no aparece por ningun lado se enseña el id y no un
    interrogante: con el numero se puede seguir tirando del hilo.
    """

    catalogo = (
        ((snapshot or {}).get("catalog") or {}).get("data")
        or {}
    ).get("players") or {}

    plantilla = {
        safe_int(j.get("id")): j.get("name")
        for j in ((snapshot or {}).get("my_team") or [])
        if isinstance(j, dict)
    }

    nombres = []

    for player_id in player_ids:

        pid = safe_int(player_id)

        nombre = plantilla.get(pid)

        if not nombre:
            ficha = (
                catalogo.get(str(pid))
                or catalogo.get(pid)
                or {}
            )
            nombre = ficha.get("name")

        nombres.append(nombre or f"#{pid}")

    return nombres


def compact_offers(
    state: dict,
    offer_decisions: dict | None = None,
    collecting: dict | None = None,
    snapshot: dict | None = None,
    current_user_id=None,
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

    # ==================================================
    # LA LISTA SALE DE DONDE SE CUENTA (19/08/2026)
    # ==================================================
    #
    # El aviso rojo llevaba dias diciendo "Biwenger dice 16, aqui
    # sale 15". Y las dos cifras eran correctas: contaban cosas
    # distintas.
    #
    # El chequeo cuenta las ofertas entrantes del snapshot -todas
    # las que no salen de nosotros-. La tabla se pintaba desde el
    # tablero del Computer, que por el camino se deja tres tipos:
    #
    #     - las que no estan en `waiting`
    #     - las caducadas
    #     - las de managers, que van a otra lista
    #
    # Ninguna de esas tres es un error del motor: son decisiones
    # razonables de un tablero que solo mira ofertas del Computer
    # vivas. El error era enseñar ESE recuento bajo el titulo
    # "OFERTAS RECIBIDAS" y luego compararlo con otro.
    #
    # Ahora la fila la genera el snapshot, con la misma regla que
    # usa el chequeo, y el tablero del Computer y V2 entran como
    # enriquecimiento. Asi el aviso no puede volver por un
    # desajuste de fuentes: es la misma.
    #
    # Lo que no sepamos de una oferta se dice, no se rellena con
    # ceros. Una prima de 0,0 % inventada es peor que un hueco.

    del_computer = {
        item.get("offer_id"): item
        for item in (offer_reroll.get("offers") or [])
        if item.get("offer_id") is not None
    }

    entrantes = _ofertas_entrantes(snapshot, current_user_id)

    if not entrantes:
        # Sin snapshot no se inventa una lista: se sigue con lo
        # que hay, que es como funcionaba hasta hoy.
        entrantes = [
            {
                "offer_id": item.get("offer_id"),
                "amount": item.get("amount"),
                "player_names": [
                    p.get("name", "?")
                    for p in (item.get("players") or [])
                ],
                "counterparty": "COMPUTER",
                "status": "waiting",
                "expired": False,
                "hours_to_expiry": item.get("hours_to_expiry"),
            }
            for item in (offer_reroll.get("offers") or [])
        ]

    offers = []

    for entrante in entrantes:

        offer_id = entrante.get("offer_id")

        offer = del_computer.get(offer_id) or {}

        names = entrante.get("player_names") or [
            player.get("name", "?")
            for player in (offer.get("players") or [])
        ]

        decision = por_id.get(offer_id) or {}

        # La accion que se enseña es la de V2 cuando la hay. Si no
        # la hay se dice cual es, en vez de disfrazar la del otro
        # motor de veredicto.
        accion = (
            decision.get("decision")
            or offer.get("action")
            or _por_que_no_se_analiza(entrante)
        )

        offers.append(
            {
                "players": names,

                "amount": safe_int(
                    entrante.get("amount")
                    if entrante.get("amount") is not None
                    else offer.get("amount")
                ),

                # Sin tablero no hay prima calculada, y un 0,0 %
                # se lee como "no sube nada" en vez de como "no
                # se sabe".
                "premium_percent": (
                    round(
                        safe_float(offer.get("premium_percent")),
                        2,
                    )
                    if offer.get("premium_percent") is not None
                    else None
                ),

                "solvency_reserved": bool(
                    offer.get("solvency_reserved")
                ),

                "action": accion,
                "action_label": human_action(accion),

                # Quien es la otra parte. El Computer y un manager
                # no se negocian igual, y hasta hoy los de
                # managers no salian en esta tabla.
                "counterparty": entrante.get("counterparty"),

                "status": entrante.get("status"),
                "expired": bool(entrante.get("expired")),

                # De donde sale el veredicto de arriba. Sin esto
                # vuelve a ser imposible saber quien esta
                # hablando.
                "decision_source": (
                    "OFFER_DECISION_V2"
                    if decision
                    else (
                        "REROLL_ENGINE"
                        if offer
                        else "SIN_ANALIZAR"
                    )
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
                    round(
                        safe_float(
                            offer.get("hours_to_expiry")
                            if offer.get("hours_to_expiry")
                            is not None
                            else entrante.get("hours_to_expiry")
                        ),
                        1,
                    )
                    if (
                        offer.get("hours_to_expiry") is not None
                        or entrante.get("hours_to_expiry")
                        is not None
                    )
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
        # EL TOPE POR OPERACION SE LLAMA `single_operation_limit`
        #
        #     El motor lo devuelve con ese nombre desde siempre
        #     -`speculation_engine.py`, las dos ramas de
        #     presupuesto-. El lector buscaba `max_operation` y
        #     `max_single_operation`, que no existen en ningun
        #     sitio, asi que la pantalla enseñaba `max_operation:
        #     0`.
        #
        #     Y cero era falso: el tope real es el 40 % del
        #     bolsillo. Un cero en pantalla se lee como "no puedes
        #     hacer ni una operacion", que es lo contrario de lo
        #     que decia el motor.
        #
        #     Se arregla en el lector, y punto: el motor no se
        #     toca. Los dos nombres viejos se dejan detras por si
        #     algun estado guardado los trae.
        "max_operation": safe_int(
            budget.get("single_operation_limit")
            if budget.get("single_operation_limit") is not None
            else budget.get(
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

    # Con mas de dos ciclos de retraso
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

                # PARTIDOS JUGADOS, QUE ES EL DENOMINADOR BUENO
                # (22/09/2026)
                #
                #     La calidad medida son puntos por PARTIDO
                #     jugado, no por jornada. El motor los tenia
                #     -vienen en `my_team`- y la plantilla
                #     publicada no, asi que quien leia el tablero
                #     no podia recalcular la misma vara que el
                #     motor y le salia otro once.
                #
                #     Es la misma familia de fallo que `in_lineup`
                #     contra `is_starter`: el mismo concepto
                #     viajando entero por un lado y cojo por otro.
                "played_home": safe_int(player.get("playedHome")),
                "played_away": safe_int(player.get("playedAway")),
                "points_last_season": safe_int(
                    player.get("pointsLastSeason")
                ),

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

        # EL OTRO BOLSILLO (21/08/2026)
        #
        # Todo lo de arriba es el limite de ESPECULAR. Fichar para
        # mejorar el once tiene el suyo, mucho mayor, y hasta hoy
        # no se veia en ninguna pantalla porque no existia.
        "acquisition": compact_acquisition_budget(
            speculation.get("acquisition_budget") or {}
        ),
    }


def compact_acquisition_budget(budget: dict) -> dict:
    """
    Con cuanto dinero puede Pepe mejorar el once.
    """

    if not budget:
        return {"available": False}

    return {
        "available": True,
        "enabled": bool(budget.get("enabled")),
        "cash_budget": safe_int(budget.get("cash_budget")),
        "debt_budget": safe_int(budget.get("debt_budget")),
        "gross_budget": safe_int(budget.get("gross_budget")),
        "total_budget": safe_int(budget.get("total_budget")),
        "available_budget": safe_int(
            budget.get(
                "available_budget",
                budget.get("total_budget"),
            )
        ),
        "maximum_bid": safe_int(budget.get("maximum_bid")),
        "committed_total": safe_int(budget.get("committed_total")),
        "capped_by_biwenger": bool(budget.get("capped_by_biwenger")),
        "mode": budget.get("mode"),
        "blocked_by": budget.get("blocked_by"),
        "reason": budget.get("reason"),
        "debt_unavailable_reason": budget.get(
            "debt_unavailable_reason"
        ),
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


def _libro_de_pujas(limite: int = 8) -> list:
    """
    Las ultimas pujas con nombre, importe y como acabaron.

    Observador puro: lee el libro ya escrito. Nunca lanza.
    """

    try:
        from src.intelligence.bid_outcome_ledger import load_ledger

        filas = [
            {
                "name": b.get("player_name"),
                "amount": safe_int(b.get("amount")),
                "outcome": b.get("outcome"),
                "source": b.get("target_source"),
                "margin": b.get("margin"),
                "placed_at": b.get("placed_at"),
            }
            for b in (load_ledger().get("bids") or {}).values()
            if isinstance(b, dict)
        ]

        filas.sort(
            key=lambda f: str(f.get("placed_at") or ""),
            reverse=True,
        )

        return filas[:limite]

    except Exception:                               # noqa: BLE001
        return []


def bloque_de_la_subasta(
    state: dict | None,
    snapshot: dict | None,
) -> dict:
    """
    Lo que el ciclo va a pujar en el reset, ANTES del reset.

    POR QUE EN LA PANTALLA Y NO SOLO EN EL LOG

        Una pieza que escribe en Biwenger sola, en una ventana de
        15 minutos, a las siete menos cinco de la manana, no se
        puede auditar leyendo un log despues. Aqui sale antes:
        por quien puja, cuanto, cuanto compromete si se ganan
        todas y cuanto falta para el cierre.

    OBSERVADOR PURO

        Llama al MISMO `plan_desde_el_estado` que el ciclo, y no
        ejecuta nada. Si esta pantalla dice tres nombres, el
        ciclo puja por esos tres.

        `would_bid` es "el ciclo pujaria", no "se ha pujado". Lo
        que ya se pujo esta en `outcomes`.

    Nunca lanza: un termometro roto no puede tumbar la pantalla.
    """

    vacio = {
        "available": False,
        "would_bid": False,
        "bids": [],
        "committed": 0,
        "expected": 0,
        "all_won": 0,
        "seconds_to_reset": None,
        "kill_switch": "BORDALAS_SIN_SUBASTA=1",
        "reason": None,
    }

    try:
        from src.analysis.la_subasta import (
            DISABLE_ENV,
            MAX_PUJAS_PRIMER_DIA,
            plan_desde_el_estado,
        )

        plan = plan_desde_el_estado(
            state,
            snapshot,

            # En vivo A PROPOSITO: la pregunta que contesta esta
            # pantalla es "¿que va a hacer el ciclo?", y el ciclo
            # corre en vivo. Con `False` diria siempre "no puja
            # porque no esta en vivo", que es verdad de esta
            # llamada y mentira del ciclo.
            en_vivo=True,
        )

        ventana = plan.get("window") or {}

        return {
            "available": bool(plan.get("available")),
            "would_bid": bool(plan.get("execute")),
            "bids": [
                {
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "team_id": b.get("team_id"),
                    "market_price": safe_int(b.get("market_price")),
                    "bid": safe_int(b.get("bid")),
                    "win_odds": b.get("win_odds"),
                    "expected_value": safe_int(
                        b.get("expected_value")
                    ),
                }
                for b in (plan.get("bids") or [])
            ],

            # Lo que se compromete si se ganan TODAS: el peor
            # caso de caja, que es el que hay que poder mirar.
            "committed": safe_int(plan.get("committed")),
            "expected": safe_int(plan.get("expected")),
            "all_won": safe_int(plan.get("all_won")),

            "slots_used": safe_int(plan.get("slots_used")),
            "capped_at": plan.get("capped_at"),
            "dropped_by_cap": safe_int(plan.get("dropped_by_cap")),
            "dropped_by_club": safe_int(
                plan.get("dropped_by_club")
            ),
            "first_day_cap": MAX_PUJAS_PRIMER_DIA,

            # Cuanto falta para el cierre.
            "seconds_to_reset": ventana.get("seconds_to_reset"),
            "window_open": bool(ventana.get("abierta")),

            "worst_case": plan.get("worst_case"),
            "blocked_by": plan.get("blocked_by"),
            "reason": plan.get("reason"),

            # El interruptor, escrito donde se mira el resultado.
            "kill_switch": f"{DISABLE_ENV}=1",

            # Y DESPUES: que gano y que perdio de lo que pujo
            # ESTE camino, no mezclado con el de siempre.
            "outcomes": bid_outcome_summary(
                target_source="SUBASTA_CARTERA"
            ),

            # TODAS las pujas, vengan de donde vengan: el dueno
            # tambien puja a mano y esas no son de la cartera.
            "outcomes_all": bid_outcome_summary(),

            # CON NOMBRE Y APELLIDOS.
            #
            #     Los contadores dicen "1 ganada"; no dicen A
            #     QUIEN. Y la pregunta de las 07:15 es literal:
            #     "¿gané a Aubameyang?". Sin el nombre hay que
            #     ir a buscarlo a otra pagina, que es justo lo
            #     que la portada tiene que evitar.
            "bids_book": _libro_de_pujas(),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"La subasta no se pudo publicar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _saldo_fresco(market_status: dict | None):
    """
    El saldo de AHORA, no el de la foto. `None` si no se puede.

    Nunca lanza: si la llamada falla se devuelve `None`, y el
    cuadre de la caja dira "no se sabe" en vez de ponerse rojo
    contra un saldo caduco.
    """

    try:
        from src.biwenger.client import cliente_del_ciclo

        cliente = cliente_del_ciclo()

        estado = (cliente.get_market() or {}).get("status") or {}

        saldo = estado.get("balance")

        if saldo is not None:
            return saldo

    except Exception as error:                      # noqa: BLE001
        print(f"Saldo fresco: no se pudo pedir ({error}).")

    return None


def build_dashboard_state() -> dict:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    # LA JORNADA, ANTES DE RECALCULAR NADA (05/09/2026)
    #
    # El ciclo valida el tablero de titularidad contra la jornada
    # que se juega. La telemetria corre en OTRO proceso y tiene
    # que validar contra la misma, o las dos pantallas contarian
    # cosas distintas del mismo tablero: el ciclo quieto y el
    # dashboard tan contento con el pronostico de la semana
    # pasada.
    #
    # Va antes de `build_global_decision` a proposito: ese
    # recalculo ya usa el lookup.
    #
    # Blindado: si el calendario no se puede leer, no se fija
    # expectativa y el lookup se comporta como siempre. Un
    # termometro no puede tumbar la telemetria.
    try:
        from src.analysis.calendar_state import build_calendar_state
        from src.analysis.candidate_starter_lookup import (
            set_expected_matchday,
        )

        set_expected_matchday(
            (build_calendar_state(snapshot) or {}).get(
                "target_matchday"
            )
        )

    except Exception as error:                      # noqa: BLE001
        print(f"Jornada esperada: no se pudo fijar ({error}).")

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

    # El marcador. `/rounds/league` solo devuelve la jornada en
    # curso: cuando cierra y salta a la siguiente, sus puntos
    # desaparecen de la API. Si nadie los anota en el momento, no
    # se recuperan. Por eso se anota en cada ciclo, aqui, que es
    # donde ya esta el snapshot cargado.
    #
    # Observador puro: solo escribe su propio fichero. Si falla,
    # el dashboard sigue: un termometro roto no puede parar el
    # equipo.
    try:
        anotar_jornada(
            snapshot,
            current_user_id=board.get("current_user_id"),
        )
    except Exception as error:                      # noqa: BLE001
        print(f"Marcador: no se pudo anotar la jornada ({error}).")

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
        # EL SALDO, FRESCO Y NO DE LA FOTO.
        #
        #     El cuadre de la caja compara contra este numero.
        #     Con el de la foto dio un rojo falso de 140.977 EUR
        #     el 12/09: la reconstruccion estaba bien y lo viejo
        #     era el saldo. Se pide a la API, y si no se puede,
        #     se manda `None` para que el cuadre diga "no se
        #     sabe" en vez de comparar contra algo caduco.
        own_balance=_saldo_fresco(market_status),
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

    # Las plantillas de los siete, con la misma ficha. Se saca a
    # una variable porque de ella cuelga el estado de carrera.
    rival_squads = build_rival_squads(
        snapshot,
        current_user_id=board.get("current_user_id"),
        rival_intelligence=rival_intelligence,
    )

    # EN QUE CARRERA VA PEPE (05/09/2026)
    #
    # Puesto, distancia al lider, jornadas restantes, ritmo
    # necesario y brecha de plantilla. Nada de esto entra en
    # ninguna decision: Pepe sigue pujando igual fuese primero o
    # ultimo.
    #
    # FASE OBSERVADOR. Se calcula, se pinta, y ahi acaba. Ningun
    # motor importa `race_state`.
    #
    # Blindado: nunca lanza por su cuenta, pero el envoltorio se
    # queda por si el import falla. Un marcador roto no puede
    # tumbar la telemetria.
    try:
        from src.analysis.race_state import build_race_state

        race = build_race_state(rival_squads)

    except Exception as error:                      # noqa: BLE001
        race = {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo construir el estado de carrera: "
                f"{type(error).__name__}: {error}"
            ),
            "managers": [],
        }

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


    # El dashboard tiene que decidir con el MISMO dinero que
    # produccion. Si aqui se pasara solo el de especular, la
    # pantalla volveria a enseñar una decision que el ciclo no
    # toma.
    fichajes = exposure.get("acquisition") or {}

    presupuesto_fichajes = (
        (
            fichajes.get("available_budget")
            or fichajes.get("total_budget")
        )
        if fichajes.get("enabled")
        else None
    )

    acquisition = build_acquisition_board(
        snapshot=snapshot,
        rival_intelligence=rival_intelligence,
        current_user_id=board.get("current_user_id"),
        available_budget=exposure.get("available_budget") or None,
        acquisition_budget=presupuesto_fichajes or None,
    )

    points_market = calibrate_points_market(
        snapshot.get("catalog", {})
    )

    photo_lookup = build_player_photo_lookup(
        snapshot
    )

    # LA SEGUNDA OPINION, A HORIZONTE DE TEMPORADA (05/09/2026)
    #
    # La misma lista de candidatos, valorada por lo que van a dar
    # de aqui a la jornada 38 en vez de por lo que valga su
    # reventa el jueves.
    #
    # FASE OBSERVADOR: se escribe AL LADO de la valoracion de
    # siempre, sobre copias de las filas. El tablero que decide
    # sigue siendo bit a bit el mismo, y ninguna ruta de decision
    # importa este modulo.
    try:
        from src.analysis.season_horizon_shadow import (
            build_season_horizon_shadow,
        )

        season_horizon = build_season_horizon_shadow(
            acquisition,
            race,
            points_market,
        )

    except Exception as error:                      # noqa: BLE001
        season_horizon = {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo valorar a temporada: "
                f"{type(error).__name__}: {error}"
            ),
            "rows": [],
            "biggest_gaps": [],
        }

    # QUE FICHARIA SI PUDIERA LLENAR UN HUECO (05/09/2026)
    #
    # Hoy a cada candidato solo se le compara con un jugador: el
    # peor titular de su posicion. No existe "fichar y punto", y
    # Pepe tiene 14 fichas contra las 17 del mayor de la liga.
    #
    # FASE OBSERVADOR: una lista al margen. No ficha, no puja y
    # no toca `acquisition_valuation.py`.
    try:
        from src.analysis.roster_expansion_shadow import (
            build_roster_expansion_shadow,
        )

        roster_expansion = build_roster_expansion_shadow(
            season_horizon,
            compact_ledger_audit(ledger_audit),
            (exposure or {}).get("acquisition"),
            current_user_id=board.get("current_user_id"),
        )

    except Exception as error:                      # noqa: BLE001
        roster_expansion = {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo calcular la via de ampliar plantilla: "
                f"{type(error).__name__}: {error}"
            ),
            "candidates": [],
            "slots": {"known": False},
        }


    # EL OJEADOR (06/09/2026)
    #
    # Lo que tres webs dicen del precio de cada jugador, al lado
    # de lo que dice Pepe. Se LEE del disco: quien sale a la
    # calle es el ciclo, cada seis horas. La telemetria nunca
    # raspa.
    #
    # FASE OBSERVADOR: se anota sobre copias de las filas del
    # tablero, y ningun motor lee este bloque.
    try:
        from src.intelligence.scout.accuracy import summary as scout_summary
        from src.intelligence.scout.report import load_report
        from src.intelligence.scout.view import (
            annotate_targets,
            build_scout_block,
        )

        scout_report = load_report() or {}

        acquisition_rows = annotate_targets(
            (acquisition or {}).get("targets"),
            scout_report,
        )

        scout = build_scout_block(
            scout_report,
            scout_summary(),
            acquisition_rows,
        )

        # EL ESTUDIO DE LA DIVERGENCIA (07/09/2026)
        #
        # Se LEE del libro; quien lo alimenta es el ciclo. Va
        # dentro del bloque del ojeador porque es su hipotesis,
        # no un modulo aparte.
        from src.intelligence.scout.divergence import study as divergence_study

        scout["divergence"] = divergence_study()

        # Las filas anotadas sustituyen a las que se PINTAN. El
        # tablero que decidio sigue intacto: `annotate_targets`
        # devuelve copias.
        if acquisition_rows:
            acquisition = {**(acquisition or {}), "targets": acquisition_rows}

    except Exception as error:                      # noqa: BLE001
        scout = {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo leer el informe del ojeador: "
                f"{type(error).__name__}: {error}"
            ),
            "sources": {},
            "unmatched": [],
            "accuracy": {"available": False},
        }

    # EL OJEADOR DE PRENSA (05/09/2026)
    #
    # Lo unico que no copia el precio de Biwenger. Se LEE del
    # disco, igual que el ojeador de mercado: quien sale a la
    # calle es el ciclo, dos veces al dia. La telemetria nunca
    # raspa.
    #
    # FASE OBSERVADOR: ningun motor lee este bloque.
    try:
        from src.intelligence.scout.press import (
            build_press_block,
            load_press_report,
        )

        press = build_press_block(load_press_report())

    except Exception as error:                      # noqa: BLE001
        press = {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo leer el informe de prensa: "
                f"{type(error).__name__}: {error}"
            ),
            "sources": {},
            "items": [],
            "unmatched": [],
        }

    # EL ARBITRO (16/09/2026)
    #
    #     ¿Quien tenia razon? Cuatro noches concluyendo que no hay
    #     que comprar nada mientras Pollo compraba siete
    #     jugadores. Esto lo cuenta con numeros: lo que pago, lo
    #     que vale hoy, y cuantos dias han pasado.
    #
    #     Y el libro de rechazos, que es lo que nos juzga a
    #     nosotros: cada objetivo que Pepe rechazo contra lo que
    #     ha hecho su precio desde entonces.
    #
    #     Observador puro: ningun motor lee este bloque.
    try:
        from src.analysis.hold_backtest import store_depth
        from src.analysis.rejection_ledger import (
            rule_backtest,
            summary as rejection_summary,
        )
        from src.analysis.rival_scoreboard import build_scoreboard

        arbitro = build_scoreboard(
            {
                "meta": {
                    "generated_at": datetime.now().isoformat()
                },
                "rival_squads": rival_squads,
                "league_center": league_center,
                "race": race,
            }
        )

        arbitro["rejections"] = rejection_summary()
        arbitro["rule_backtest"] = rule_backtest()

        # Y la linea que faltaba: cuantos dias de historico hay de
        # verdad. Toda la discusion de "el almacen son seis dias"
        # salio de mirar una copia local caducada.
        arbitro["history"] = store_depth()

    except Exception as error:                      # noqa: BLE001
        arbitro = {
            "available": False,
            "observer_only": True,
            "managers": {},
            "reason": (
                f"No se pudo montar el arbitro: "
                f"{type(error).__name__}: {error}"
            ),
        }

    # LA CONCENTRACION DE LA PLANTILLA (10/09/2026)
    #
    # Cuanto pesa el jugador mas caro y cuantos hay del mismo
    # club. Yamal son el 41 % de la plantilla, y no habia ningun
    # tope que lo mirase.
    #
    # Avisa y acota, no prohibe: no obliga a vender a nadie.
    try:
        from src.analysis.concentration_guardrail import (
            build_concentration,
        )

        concentration = build_concentration(snapshot.get("my_team"))

    except Exception as error:                      # noqa: BLE001
        concentration = {
            "available": False,
            "reason": (
                f"No se pudo medir la concentracion: "
                f"{type(error).__name__}: {error}"
            ),
            "players": [],
            "teams": [],
            "breaches": [],
        }

    # LA PLANTILLA TAMBIEN SABE (20/08/2026)
    #
    # La tabla de PLANTILLA enseñaba nombre, posicion, valor y
    # titular/suplente. La jerarquia, el pronostico de salir y el
    # parte de lesion o sancion ya se calculaban, pero solo
    # llegaban al XI -once de dieciseis- y al mercado.
    roster = enrich_roster(
        compact_roster(
            snapshot,
            state.get("lineup", {}) or {},
            photo_lookup,
        )
    )

    # ============================================================
    # DE AQUI EN ADELANTE HACE FALTA LA PLANTILLA ENRIQUECIDA
    # ============================================================
    #
    #     La vara, el banquillo y la via TENER necesitan
    #     `roster`: jerarquia, probabilidad de titular y puntos
    #     de cada ficha.
    #
    #     Estaban mas arriba, antes de que `roster` existiera. No
    #     reventaban -cada bloque tiene su try- pero se publicaban
    #     vacios con un NameError dentro, que es la peor forma de
    #     fallar: en silencio y con la clave puesta.

    # ============================================================
    # LA VARA CON FACTORES POR POSICION (18/09/2026)
    # ============================================================
    #
    #     Con la misma marca de la vara, un medio entregaba 8,51
    #     puntos por jornada y un defensa 5,82. El motor, que los
    #     trataba igual, alineaba defensas: 5-4-1, con un lateral
    #     de 0 puntos titular y dos delanteros en el banquillo.
    #
    #     Los factores se aplican en el motor. Aqui se publica lo
    #     que hacen, con su muestra y con la linea para apagarlos.
    try:
        from src.analysis.position_factor import (
            state as vara_state,
        )
        from src.analysis.vara_comparada import (
            comparar as comparar_onces,
            elegir_once,
        )

        vara = vara_state()

        vara["lineups"] = comparar_onces(
            (roster or {}).get("players") or []
        )

        # LA RED: se anota el once que habria elegido la vara
        # vieja, para poder compararlo con puntos de verdad
        # cuando la jornada cierre.
        try:
            from src.analysis.marcador import (
                anotar_once_alternativo,
                jornada_en_curso,
            )

            from src.analysis.vara_comparada import VARAS

            fichas = (roster or {}).get("players") or []

            por_vara = {
                nombre: elegir_once(fichas, vara=nombre)
                for nombre in VARAS
            }

            alternativo = por_vara["base"]

            if alternativo.get("available"):
                anotar_once_alternativo(
                    jornada_en_curso(snapshot),
                    {
                        "formation": alternativo["formation"],
                        "players": alternativo["players"],
                        "vara": "base",

                        # Los tres, para separar el efecto de los
                        # factores del de la calidad.
                        "por_vara": {
                            nombre: {
                                "formation": o.get("formation"),
                                "players": o.get("players"),
                            }
                            for nombre, o in por_vara.items()
                            if o.get("available")
                        },
                    },
                )

        except Exception as error:                  # noqa: BLE001
            print(
                f"Vara: no se pudo anotar el once alternativo "
                f"({error})."
            )

    except Exception as error:                      # noqa: BLE001
        vara = {
            "available": False,
            "active": None,
            "rows": [],
            "window": {},
            "disable_with": "BORDALAS_VARA_PLANA=1",
            "lineups": {"available": False},
            "reason": (
                f"No se pudo leer la vara: "
                f"{type(error).__name__}: {error}"
            ),
        }

    # ============================================================
    # ¿SIGUE RESPALDADA LA VIA TENER? (17/09/2026)
    # ============================================================
    #
    #     Las dos aserciones de mercado que se quitaron de la
    #     verja no se pierden: se mudan aqui, donde tienen
    #     consecuencias de verdad.
    #
    #     En la verja se comprobaban una vez, contra el almacen
    #     de quien lanzara CI, y ponian el despliegue en rojo
    #     cuando el mercado cambiaba. Aqui se comprueban en cada
    #     ciclo, contra el almacen de produccion, y lo que hacen
    #     es apagar la via que se ha quedado sin respaldo.
    try:
        from src.analysis.hold_switch import route_state
        from src.analysis.hold_value import (
            DEFAULT_HORIZON_DAYS,
            calibration_for,
        )

        via_tener = route_state(
            calibration_for(DEFAULT_HORIZON_DAYS),
            horizon_days=DEFAULT_HORIZON_DAYS,
        )

    except Exception as error:                      # noqa: BLE001
        via_tener = {
            "available": False,
            "on": None,
            "buckets": [],
            "reason": (
                f"No se pudo leer el estado de la via TENER: "
                f"{type(error).__name__}: {error}"
            ),
        }

    # ============================================================
    # EL ONCE: LOS PUNTOS QUE SE QUEDARON SENTADOS (17/09/2026)
    # ============================================================
    #
    # POR QUE ESTE BLOQUE EXISTE
    #
    #     El arbitro tumbo la tesis de cuatro noches: el valor de
    #     plantilla no explica los puntos en esta liga. Lo que
    #     gana son los puntos, y los puntos los marcan once
    #     jugadores.
    #
    #     Y la distancia es 13 puntos en 35 jornadas: 0,371 por
    #     jornada. Si el once esta dejando mas que eso sentado,
    #     la liga esta en el banquillo y no en el mercado.
    #
    # OBSERVADOR PURO
    #
    #     Ni el banquillo, ni el sesgo por posicion, ni la
    #     comparacion con Mex tocan un umbral. Miden y publican.
    marcador_estado = build_marcador()

    try:
        from src.analysis.banquillo import puntos_en_el_banquillo
        from src.analysis.rival_once import comparar_con
        from src.analysis.sesgo_posicion import sesgo_por_posicion

        entorno_once = {
            "rival_squads": rival_squads,
            "league_center": league_center,
            "rival_intelligence": rival_intelligence,
            "race": race,
        }

        once_bloque = {
            "available": True,
            "observer_only": True,

            # BLOQUE 1: los puntos sentados.
            "bench": puntos_en_el_banquillo(
                marcador_estado,
                race,

                # Para separar lo que se dejo entonces de lo que
                # se podria ganar hoy: Yusi Enriquez aportaba 5 de
                # aquellos 8 puntos y ya es de Prinzipote.
                plantilla_actual=(
                    (roster or {}).get("players") or []
                ),
            ),

            # BLOQUE 2: ¿la vara mide igual en las cuatro
            # posiciones? Se mide y se propone; no se aplica.
            "position_bias": sesgo_por_posicion(entorno_once),

            # BLOQUE 3: el equipo comparable, que no era Pollo.
            "rival": comparar_con(entorno_once, "Mex"),

            # BLOQUE 4: que la pantalla deje de contar la pelicula
            # vieja. La brecha se recalcula sola y ya dice 18,3 M;
            # lo que faltaba era la advertencia AL LADO, para que
            # nadie vuelva a montar una estrategia encima de una
            # correlacion que no llega a su valor critico.
            "value_warning": (arbitro or {}).get(
                "value_versus_points"
            ) or {"available": False},
        }

    except Exception as error:                      # noqa: BLE001
        once_bloque = {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo montar el once: "
                f"{type(error).__name__}: {error}"
            ),
        }

    offers_compactas = compact_offers(
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

        # La lista sale del snapshot, que es de donde la cuenta el
        # chequeo de consistencia.
        snapshot=snapshot,
        current_user_id=board.get("current_user_id"),
    )

    # A QUIEN LE TOCA SALIR (10/09/2026)
    #
    # Hoy nadie decide esto: `sales_analyzer` puntua,
    # `sale_intent` propone y se imprime en un terminal que no
    # mira nadie, y el motor de ofertas contesta HOLD a las doce
    # mientras el saldo esta en -421.792.
    #
    # Esto es una COLA con el motivo escrito, para que el dueño
    # pueda leerla ANTES de que pase. Observador puro: no vende.
    #
    # Se le pasan las ofertas compactadas para poder distinguir la
    # caja de este ciclo -oferta viva- de la caja de cuando
    # alguien compre.
    try:
        from src.analysis.sale_order import build_sale_order

        sale_order = build_sale_order(
            roster.get("players") or [],
            lineup_ids=[
                jugador.get("id")
                for jugador in (
                    (state.get("lineup", {}) or {}).get("players")
                    or []
                )
            ],
            offers=offers_compactas,
            concentration=concentration,
        )

    except Exception as error:                      # noqa: BLE001
        sale_order = {
            "available": False,
            "reason": (
                f"No se pudo ordenar la venta: "
                f"{type(error).__name__}: {error}"
            ),
            "queue": [],
            "excluded": [],
            "blocked": [],
        }

    # ============================================================
    # DE AQUI EN ADELANTE HACE FALTA LA COLA DE VENTAS
    # ============================================================
    #
    #     La doctrina mira la porteria, y la porteria necesita
    #     saber que se abriria vendiendo al primero de la cola.
    #     Estaba mas arriba, antes de que `sale_order` existiera:
    #     no reventaba -tiene su try- pero se publicaba vacia con
    #     un NameError dentro. Segunda vez esta semana.

    # ============================================================
    # LA DOCTRINA (20/09/2026)
    # ============================================================
    #
    #     El dueño junto los consejos basicos de Biwenger, un
    #     video de trucos y la forma medida de jugar de Pollo, y
    #     dijo: "eso es lo que quiero que haga Pepe".
    #
    #     Dieciocho reglas en `docs/DOCTRINA.md`. Aqui se publica:
    #
    #       - que decisiones citan una regla y CUALES NO CITAN
    #         NINGUNA, que es lo que de verdad interesa;
    #       - que clubes acaban de ascender, deducidos del
    #         catalogo, y si de verdad suben mas;
    #       - donde muere cada objetivo del escaparate;
    #       - y el activo que pesa demasiado, en dos columnas.
    #
    #     Observador puro: no mueve un tope ni un liston.
    try:
        from src.analysis.activo_grande import evaluar as activo_grande
        from src.analysis.ascendidos import (
            detectar as detectar_ascendidos,
            en_el_mercado as ascendidos_en_mercado,
        )
        from src.analysis.calidad_medida import comparar_varas
        from src.analysis.doctrina import auditar as auditar_doctrina
        from src.analysis.porteria import estado_de_la_porteria
        from src.analysis.embudo import embudo as construir_embudo

        catalogo_crudo = snapshot.get("catalog") or {}

        ascendidos = detectar_ascendidos(catalogo_crudo)

        equipo_de_jugador = {
            str(j.get("id")): str(j.get("teamID"))
            for j in (
                (catalogo_crudo.get("data") or {}).get("players")
                or {}
            ).values()
            if isinstance(j, dict)
        }

        doctrina = {
            "available": True,
            "observer_only": True,

            # Regla 17.
            "citations": auditar_doctrina(
                {
                    "acquisition": acquisition,
                    "season_horizon": season_horizon,
                    "decision": state.get("decision") or {},
                }
            ),

            # Regla 8.
            "promoted": ascendidos,
            "promoted_on_sale": ascendidos_en_mercado(
                (acquisition or {}).get("targets"),
                equipo_de_jugador,
                ascendidos.get("team_ids"),
            ),

            # Regla 9: por que casi nunca dispara.
            "funnel": construir_embudo(acquisition),

            # Regla 3: la porteria nunca se queda a uno.
            "goalkeeping": estado_de_la_porteria(
                (roster or {}).get("players") or [],
                (acquisition or {}).get("targets") or [],
                cash=safe_int(
                    (exposure or {}).get("cash_budget")
                ),
                sale_queue=(sale_order or {}).get("queue") or [],
            ),

            # Regla 6: la calidad medida, medida y NO encendida.
            "measured_quality": comparar_varas(
                [
                    {
                        **j,
                        "hierarchy_value": j.get("hierarchy_value"),
                        "starter_probability": j.get(
                            "starter_probability"
                        ),
                        "playedHome": j.get("playedHome"),
                        "playedAway": j.get("playedAway"),
                        "pointsLastSeason": j.get(
                            "points_last_season"
                        ),
                    }
                    for m in (
                        (rival_squads or {}).get("managers") or []
                    )
                    for j in (m.get("players") or [])
                ],
                safe_int((race or {}).get("matchdays_played")),
            ),

            # Regla 15.
            "big_asset": activo_grande(
                (roster or {}).get("players") or [],
                (acquisition or {}).get("targets") or [],
                safe_int((race or {}).get("matchdays_played")),
                cash=safe_int(
                    (exposure or {}).get("cash_budget")
                ),
            ),
        }

    except Exception as error:                      # noqa: BLE001
        doctrina = {
            "available": False,
            "observer_only": True,
            "citations": {"available": False},
            "goalkeeping": {"available": False},
            "measured_quality": {"available": False},
            "promoted": {"available": False},
            "promoted_on_sale": {"available": False},
            "funnel": {"available": False},
            "big_asset": {"available": False},
            "reason": (
                f"No se pudo montar la doctrina: "
                f"{type(error).__name__}: {error}"
            ),
        }


    # EL RELOJ DE LA SOLVENCIA (12/09/2026)
    #
    #     "No quiero salir de rojo hoy. Con estar en positivo 6
    #      horas antes del inicio de jornada es suficiente."
    #
    # La solvencia deja de ser un estado y pasa a ser un plazo.
    # Lejos del cierre un deficit es una posicion legitima; cerca,
    # una emergencia. Y de ahi sale el desempate del punto 2: quien
    # gana cuando el motor de solvencia dice "vende" y el de
    # ofertas dice "conserva".
    #
    # Observador: calcula y publica. Quien ejecuta es el camino de
    # siempre, ACCEPT_RECOVERY_OFFER.
    # LAS PUJAS DEL DUENO, ANTES DEL RELOJ (10/09/2026)
    #
    #     El dueno puja a mano cuando le apetece. El 10/09 puso
    #     11,8 M por Aubameyang y este reloj siguio diciendo
    #     "Saldo positivo. El plazo no aprieta." durante horas,
    #     porque leia `balance` y una puja viva no mueve el
    #     balance: baja `maximumBid`.
    #
    #     Tres vias, y manda la mas conservadora. Va ANTES del
    #     reloj porque el reloj necesita el numero.
    try:
        from src.analysis.pujas_del_dueno import (
            pujas_comprometidas,
            valor_de_plantilla,
        )
        from src.analysis.bid_exposure_engine import (
            build_bid_exposure,
        )
        from src.intelligence.bitacora_del_saldo import (
            apuntar_lectura,
            ultima_lectura,
        )

        estado_mercado = (
            (snapshot.get("market") or {}).get("status") or {}
        )

        valor_squad = valor_de_plantilla(snapshot.get("my_team"))

        # La foto anterior, para la via de la diferencia. Se lee
        # ANTES de apuntar la de ahora, o se restaria contra si
        # misma y siempre daria cero.
        anterior = ultima_lectura()

        ahora_lectura = {
            "balance": estado_mercado.get("balance"),
            "maximum_bid": estado_mercado.get("maximumBid"),
            "hours_to_reset": (market_clock or {}).get(
                "hours_to_reset"
            ),
        }

        pujas_del_dueno = pujas_comprometidas(
            exposicion=build_bid_exposure(snapshot),
            balance=estado_mercado.get("balance"),
            maximum_bid=estado_mercado.get("maximumBid"),
            valor_plantilla=valor_squad,
            antes=anterior,
            ahora=ahora_lectura,
        )

        # CON CUANTO SE PUEDE PUJAR DE VERDAD
        #
        #     Sobre maximumBid, que ya descuenta las pujas
        #     vivas. Y la caja, con lo comprometido restado: el
        #     saldo no sabe nada de pujas y quien reparta por
        #     caja repartiria dinero ya gastado.
        from src.analysis.pujas_del_dueno import (
            capacidad_de_pujar,
        )

        # LA VERDAD MEDIDA DE LA LINEA DE CREDITO
        #
        #     headroom = valor_plantilla x 0,25
        #
        # Medido al euro en 12 de 12 estados. NO depende de
        # `maximumBid`, y ese es todo el punto: la tira calcula
        # el credito restando -deuda maxima + comprometido -
        # saldo-, asi que sus cuatro numeros cuadran SIEMPRE,
        # incluso si `maximumBid` viniera mal.
        #
        # Una pantalla que no puede estar equivocada tampoco
        # puede avisar de que lo esta. Por eso se publica aqui la
        # otra via, la que no pasa por `maximumBid`: para poder
        # contrastarlas y CANTARLO si no coinciden.
        from src.analysis.linea_de_credito import (
            LINEA_DE_CREDITO,
            MEDIDA,
            headroom_de,
        )

        pujas_del_dueno["credito"] = {
            "available": bool(safe_int(valor_squad)),
            "roster_value": safe_int(valor_squad),
            "ratio": LINEA_DE_CREDITO,
            "headroom": headroom_de(valor_squad),
            "source": MEDIDA,
        }

        pujas_del_dueno["capacity"] = capacidad_de_pujar(
            estado_mercado.get("maximumBid"),
            cash_budget=(exposure or {}).get("cash_budget"),
            comprometido=pujas_del_dueno.get("committed"),
        )

        apuntar_lectura(
            balance=estado_mercado.get("balance"),
            maximum_bid=estado_mercado.get("maximumBid"),
            roster_value=valor_squad,
            hours_to_reset=ahora_lectura["hours_to_reset"],
            committed=pujas_del_dueno.get("committed"),
            source=pujas_del_dueno.get("source"),
        )

    except Exception as error:                      # noqa: BLE001
        pujas_del_dueno = {
            "available": False,
            "committed": 0,
            "source": None,
            "sources": {},
            "disagreement": 0,
            "reason": (
                f"No se pudieron contar las pujas del dueno: "
                f"{type(error).__name__}: {error}"
            ),
        }

    # Los titulares, por nombre: con deuda contingente no se toca
    # a ninguno, y para decirlo hay que saber quienes son.
    titulares_ahora = [
        j.get("name")
        for j in (roster.get("players") or [])
        if isinstance(j, dict) and j.get("is_starter")
    ]

    # EL CENSO DE LA TANDA NUEVA (una linea por reset)
    #
    #     "¿Hace falta vender a ciegas la noche antes de un
    #      reset?" Si el Computer publica todas las mananas una
    #     tanda que tapa el agujero con gente del banquillo, la
    #     respuesta es que no hace falta nunca.
    #
    #     Con dos observaciones no se sabe. Se empieza a contar.
    try:
        from src.intelligence.bitacora_del_saldo import (
            censar_el_reset,
        )

        censo = censar_el_reset(
            offers_compactas,
            (market_clock or {}).get("hours_to_reset"),
            starters=titulares_ahora,
        )

    except Exception as error:                      # noqa: BLE001
        censo = {
            "available": False,
            "reason": (
                f"No se pudo censar el reset: "
                f"{type(error).__name__}: {error}"
            ),
        }

    try:
        from src.analysis.solvency_clock import build_solvency_clock

        solvency_clock = build_solvency_clock(
            state.get("balance"),
            state.get("hours_to_deadline"),
            offers=offers_compactas,
            market_clock=market_clock,
            sale_order=sale_order,
            committed_bids=pujas_del_dueno.get("committed"),
            starters=titulares_ahora,
        )

    except Exception as error:                      # noqa: BLE001
        solvency_clock = {
            "available": False,
            "reason": (
                f"No se pudo calcular el reloj de solvencia: "
                f"{type(error).__name__}: {error}"
            ),
            "state": None,
            "recommended_sale": None,
        }

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

    # ==========================================================
    # LA ZONA DE SILENCIO Y LA RENOVACION (10/09/2026)
    # ==========================================================
    #
    #     La telemetria NO escribe: calcula lo mismo que el ciclo
    #     y lo ensena. Si esta pantalla dice "renovaria a estos
    #     ocho", el ciclo renueva a esos ocho.
    try:
        from datetime import datetime as _dt, timezone as _tz
        import os as _os

        from src.analysis.renovar_ofertas import (
            filas_desde_lo_publicado,
            que_renovar,
        )
        from src.analysis.zona_de_silencio import (
            lo_que_se_quedo_sin_hacer,
            observacion_del_reset,
            permite_escribir,
        )

        _ahora = _dt.now(_tz.utc)

        silencio_ahora = permite_escribir(
            _ahora,
            _os.environ.get("GITHUB_EVENT_NAME"),
        )

        _filas = filas_desde_lo_publicado(
            compact_listings(state),
            offers_compactas,
            roster,
        )

        plan_de_renovacion = que_renovar(
            _filas,
            (market_clock or {}).get("seconds_to_reset"),
            puede_escribir=bool(silencio_ahora.get("allowed")),
            deuda_contingente=0,
        )

        silencio_ahora["blocked"] = lo_que_se_quedo_sin_hacer(
            silencio_ahora,
            (
                [
                    f"renovar {plan_de_renovacion['count']} "
                    f"listado(s)"
                ]
                if plan_de_renovacion.get("count")
                else []
            ),
        )

        # LA MEDICION QUE SALE GRATIS: de cada vuelta dentro de
        # la franja, si los precios YA habian cambiado. En una
        # semana hay hora exacta del reset sin gastar nada.
        # CUANDO SE ENTRO POR ULTIMA VEZ EN LA VENTANA
        #
        #     Y en ROJO si hace mas de 24 h. La ventana no se
        #     abrio nunca hasta hoy y `FUERA_DE_VENTANA` es
        #     indistinguible de una noche normal: una capacidad
        #     que no se dispara tiene que anunciar su ausencia.
        from src.intelligence.libro_de_la_ventana import (
            estado_de_la_ventana,
            ultima_ventana,
        )

        plan_de_renovacion["ventana"] = estado_de_la_ventana(
            ultima_ventana(), _ahora
        )

        silencio_ahora["reset_observation"] = (
            observacion_del_reset(
                silencio_ahora,
                precios_cambiados=None,
                momento_utc=_ahora,
            )
        )

    except Exception as error:                      # noqa: BLE001
        silencio_ahora = {
            "available": False,
            "allowed": False,
            "reason": (
                f"No se pudo calcular la zona de silencio: "
                f"{type(error).__name__}: {error}"
            ),
        }
        plan_de_renovacion = {
            "available": False,
            "count": 0,
            "reason": "No se pudo calcular la renovacion.",
        }

    # ==========================================================
    # EL LIBRO DE PRIMERA PUBLICACION (10/09/2026)
    # ==========================================================
    #
    #     Renovar REESCRIBE la fecha del listado, asi que cada
    #     renovacion destruye la evidencia de cuando se publico
    #     un jugador por primera vez. Empieza hoy.
    try:
        from src.intelligence.libro_de_publicacion import (
            apuntar_publicaciones,
            resumen as resumen_publicacion,
        )

        nuestros = {
            j.get("name"): j
            for j in (roster.get("players") or [])
            if isinstance(j, dict)
        }

        listados_hoy = [
            {
                "id": (nuestros.get(item.get("name")) or {}).get(
                    "id"
                ),
                "name": item.get("name"),
                "price": (
                    nuestros.get(item.get("name")) or {}
                ).get("price"),
                "listed_price": item.get("listed_price"),
            }
            for item in (
                (compact_listings(state) or {}).get(
                    "renew_required"
                )
                or []
            )
        ]

        apuntar_publicaciones(listados_hoy)

        publicacion = resumen_publicacion()

    except Exception as error:                      # noqa: BLE001
        publicacion = {
            "available": False,
            "reason": (
                f"No se pudo apuntar la publicacion: "
                f"{type(error).__name__}: {error}"
            ),
        }

    # ==========================================================
    # EL ORDEN DE PREFERENCIA AL COMPRAR (10/09/2026)
    # ==========================================================
    #
    #     De la prima de recompra medida: un defensa se recompra
    #     dos puntos mas caro que un delantero. NO quita a nadie.
    try:
        from src.analysis.salida_del_viaje import (
            orden_de_preferencia,
        )

        preferencia = orden_de_preferencia(
            [
                dict(fila)
                for fila in (
                    (acquisition or {}).get("targets") or []
                )
                if isinstance(fila, dict)
                and not fila.get("outside_computer_market")
                and fila.get("decision") != "NO_DISPONIBLE"
            ]
        )[:12]

    except Exception as error:                      # noqa: BLE001
        preferencia = []

    # ==========================================================
    # EL LIBRO EN LA SOMBRA (10/09/2026)
    # ==========================================================
    #
    #     La compuerta de ritmo cierra la via de especulacion en
    #     la mitad del escaparate, y sobre los 36 viajes de
    #     Pollo no discrimina: bloqueo las 6 con las que gano
    #     1,78 M. Pero eso son 9 casos y con 9 no se retira un
    #     filtro.
    #
    #     Se apunta lo que se compraria con la compuerta
    #     apagada, TODOS LOS DIAS Y SIN DINERO. En dos semanas
    #     hay ~280 casos y se decide con ellos.
    try:
        from src.intelligence.libro_en_la_sombra import (
            apuntar_dia,
            los_que_la_compuerta_rechaza,
            resumen as resumen_sombra,
        )

        objetivos = (acquisition or {}).get("targets") or []

        apuntar_dia(objetivos)

        sombra = {
            **resumen_sombra(),
            "today": los_que_la_compuerta_rechaza(objetivos),
        }

    except Exception as error:                      # noqa: BLE001
        sombra = {
            "available": False,
            "cases": 0,
            "today": [],
            "reason": (
                f"No se pudo montar la sombra: "
                f"{type(error).__name__}: {error}"
            ),
        }

    # Los rivales compactados, UNA vez: los miran el payload y
    # el bloque de la subasta, y tienen que ser la misma lista.
    rivales_compactos = compact_rivals(
        rival_intelligence,
        board.get("current_user_id"),
    )

    # El XI, calculado UNA vez: lo leen dos bloques -`lineup`
    # y `posibles_cambios`- y tienen que contar lo mismo.
    lineup_payload = compact_lineup(
        state.get("lineup", {}) or {},
        snapshot,
        photo_lookup,
    )

    # ------------------------------------------------------
    # LA RENDIJA
    # ------------------------------------------------------
    # Observador puro: lee el cupo vigente y mide el ritmo de
    # los candidatos. No decide nada y no escribe nada.
    try:
        from src.analysis.la_rendija import (
            con_margen,
            cupo_del_reset,
            en_vivo,
            ritmo_de_los_candidatos,
            se_apaga_sola,
        )

        _cierres = []

        try:
            import json as _json

            _libro = (
                Path("data") / "trading" / "libro_de_salidas.jsonl"
            )

            if _libro.exists():
                for _linea in _libro.read_text(
                    encoding="utf-8"
                ).splitlines():
                    if _linea.strip():
                        _cierres.append(
                            _json.loads(_linea)
                        )

        except Exception:                           # noqa: BLE001
            _cierres = []

        _cupo = cupo_del_reset(_cierres)

        from src.analysis.market_rate_gate import (
            build_market_rates,
        )

        _rates = build_market_rates()

        from src.actions.escaparate_executor import (
            viajes_sin_listar,
        )

        from src.analysis.libro_de_viajes import abiertos

        _abiertos = abiertos(
            plantilla=(roster or {}).get("players") or []
        )

        _sin_listar = viajes_sin_listar(
            viajes=_abiertos.get("viajes") or [],
            listados=(compact_listings(state) or {}).get("rows") or [],
        )

        # LOS CANDIDATOS DEL CARRIL, NO LOS DEL TABLERO.
        #
        # El tablero de fichajes mira a todo el mercado; el
        # carril solo compra del Computer, con estado `ok` y de
        # 1 M para arriba -por debajo, un +1,52 % sobre 150.000
        # son 2.250 EUR y no pagan la ficha-. Pintar la lista del
        # tablero diria el ritmo de jugadores que este carril no
        # va a comprar.
        _candidatos = [
            {
                "player_id": safe_int(t.get("id")),
                "name": t.get("name"),
                "position": safe_int(t.get("position")),
                "market_price": safe_int(t.get("market_price")),
            }
            for t in ((acquisition or {}).get("targets") or [])
            if safe_int(t.get("market_price")) >= 1_000_000
            and str(t.get("status") or "").lower() == "ok"
            # SOLO EL MERCADO DEL COMPUTER. La puerta del
            # mercado de rivales sigue cerrada por regla del
            # dueno, asi que pintar su ritmo seria enseñar
            # jugadores que este carril no va a comprar.
            and not t.get("outside_computer_market")
        ]

        # LA PRIMA DE PUJA, de la curva calibrada en vivo. No se
        # escribe aqui: sale del modelo de puja de los rivales.
        _prima = (
            (
                (acquisition or {}).get("premium_model") or {}
            ).get("curve")
            or [[1.0, 0]]
        )[0][0]

        _margen = con_margen(
            _candidatos,
            prima_de_puja=(float(_prima) - 1.0) * 100.0,
            rates=_rates,
        )

        rendija_ahora = {
            "available": True,
            "cupo": _cupo["cupo"],
            "cupo_estado": _cupo["estado"],
            "cupo_reason": _cupo["reason"],
            "apagado": se_apaga_sola(_cierres),
            "ritmo": ritmo_de_los_candidatos(
                _candidatos, rates=_rates
            ),

            # EL MARGEN ESPERADO, que es el numero que define un
            # viaje. Quien no gana dinero no entra en la lista.
            "margen": _margen,

            # EL INDICADOR LO ENCIENDE EL HECHO (doctrina 37).
            #
            #     `en_vivo` es la INTENCION -la bandera del
            #     modulo- y por si sola mentia: el 12/09 el
            #     panel decia EN VIVO sobre codigo que nadie
            #     llamaba. Lo que enciende el indicador es
            #     `ultima_vuelta`: cuando corrio de verdad.
            "en_vivo": en_vivo(),
            "ultima_vuelta": (
                (load_full_autonomous_status() or {}).get("carril") or {}
            ).get("ran_at"),
            "ultima_decision": (
                (load_full_autonomous_status() or {}).get("carril") or {}
            ).get("reason"),

            # LA GUARDIA CLAVE, como dato: un jugador marcado
            # VIAJE que termina el ciclo SIN LISTAR. Comprado
            # para revender y fuera del escaparate es una vuelta
            # tirada, y sin esto no lo notaria nadie.
            "sin_listar": _sin_listar,
        }

    except Exception as error:                      # noqa: BLE001
        rendija_ahora = {
            "available": False,
            "reason": (
                f"No se pudo leer el estado de la rendija: "
                f"{type(error).__name__}: {error}"
            ),
        }

    dashboard = {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "snapshot": snapshot_file,
            "league_id": board.get("league_id"),
            "current_user_id": board.get("current_user_id"),
            "mode": "LIVE",
            "cycle_minutes": CADENCIA_MINUTOS,
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
        "lineup": lineup_payload,
        "roster": roster,

        # Las plantillas de los seis rivales, con la misma ficha.
        #
        # Salen del ledger de rivales, que reconstruye la plantilla
        # desde los perfiles de usuario. `standings[].lineup` queda
        # de respaldo: venia vacio en los siete managers, y la
        # pantalla publicaba `available: true` con `players: []`.
        "rival_squads": rival_squads,

        # El marcador de la temporada. Observador puro: ningun
        # motor lo lee.
        "race": race,

        # La valoracion a horizonte de temporada, al lado de la
        # de siempre. Observador puro tambien.
        "season_horizon": season_horizon,

        # El ojeador de mercado: lo que dicen las webs del precio
        # de cada jugador. Observador puro.
        "scout": scout,

        # Lo que dice la PRENSA de los jugadores de Biwenger.
        # Partes medicos, convocatorias y declaraciones: lo unico
        # que no esta ya dentro del precio. Observador puro.
        "press": press,

        # Cuanto pesa el jugador mas caro y cuantos hay
        # del mismo club. Observador: avisa y acota.
        "concentration": concentration,

        # A quien le toca salir cuando haga falta caja, en orden y
        # con el motivo. Observador puro: no vende nada.
        "sale_order": sale_order,

        # Quien tenia razon: el marcador de los rivales, el libro
        # de rechazos y los dias de historico que hay de verdad.
        "arbiter": arbitro,

        # Cuanto queda para el plazo de solvencia -T-6h del primer
        # partido-, si la deuda llega tapada y con que venta.
        "solvency_clock": solvency_clock,

        # Cuanto dinero nuestro esta comprometido en pujas vivas,
        # por las tres vias, aunque las haya puesto el dueno a
        # mano y Biwenger no las publique en el tablon.
        "pujas_del_dueno": pujas_del_dueno,

        # Que trae la tanda nueva del Computer en cada reset.
        # Observador puro: una linea al dia que dentro de un mes
        # contesta si hace falta vender a ciegas o no.
        "censo_del_reset": censo,

        # EL LIBRO EN LA SOMBRA. Lo que se compraria con la
        # compuerta de ritmo apagada del todo. SIN DINERO:
        # ninguna ruta lo lee, es un cuaderno para decidir
        # dentro de dos semanas si la compuerta se retira.
        "sombra": sombra,

        # CUANDO SE PUBLICO CADA JUGADOR POR PRIMERA VEZ.
        # Renovar reescribe la fecha del listado, asi que sin
        # esto la evidencia se destruye en cada renovacion.
        "publicacion": publicacion,

        # EL ORDEN DE PREFERENCIA al comprar, que sale de la
        # prima de recompra medida. NO es un filtro: no quita a
        # nadie, los pone en orden.
        "preferencia": preferencia,

        # Que ficharia si pudiera llenar un hueco de plantilla.
        # Una lista al margen: no ficha nada.
        "roster_expansion": roster_expansion,
        "rival_intelligence": {
            "ledger_status": rival_intelligence.get("ledger_status"),

            # DE DONDE SALE LA CAJA Y SI CUADRA (10/09/2026).
            #
            # De la caja cuelgan CAJA, PATRIMONIO, TOPE, PUJA %,
            # MAX. VISTO y AMENAZA. Si el metodo falla con el
            # nuestro -el unico saldo que podemos ver- la caja de
            # los seis rivales tampoco vale, y eso tiene que
            # salir en ROJO en vez de quedarse en un log.
            "cash_reconstruction": rival_intelligence.get(
                "cash_reconstruction"
            ),
            "cash_check": rival_intelligence.get("cash_check"),
            "maximum_bid_calibration": rival_intelligence.get(
                "maximum_bid_calibration"
            ),
            "managers": rivales_compactos,
        },
        "league_center": league_center,
        "competition": competition,

        "offers": offers_compactas,
        "speculation": compact_speculation(state),
        "listings": compact_listings(state),

        # LA ZONA DE SILENCIO y lo que se quedo sin hacer por
        # ella. Una barandilla que frena en silencio es
        # indistinguible de una averia.
        # POSIBLES CAMBIOS: el banquillo con el motivo del motor.
        # Bloque propio para que el panel pueda distinguir "no hay
        # suplentes" de "no se sabe", que no es lo mismo.
        "posibles_cambios": {
            "available": bool(
                (lineup_payload.get("bench") or [])
                or lineup_payload.get("formation")
            ),
            "bench": lineup_payload.get("bench") or [],
        },

        # LA RENDIJA: en que cupo esta y por que, y el ritmo
        # de lo que compraria. El cupo NO se escribe aqui: se
        # pregunta a `cupo_del_reset()`, que es su unico sitio.
        "rendija": rendija_ahora,

        "silencio": silencio_ahora,

        # QUE SE RENOVARIA EN LA VENTANA, y que listados no
        # llegan vivos a ella. Observador puro.
        "renovacion": plan_de_renovacion,
        "market_clock": market_clock,
        "position_guardrail": compact_guardrail(liquidity),
        "exposure": exposure,
        "acquisition": acquisition,
        "points_market": points_market,
        "ledger_audit": compact_ledger_audit(ledger_audit),

        # El marcador. La nota del once jornada a jornada. Se
        # publica aunque este vacio: la pantalla tiene que poder
        # decir "todavia no hay jornadas cerradas" en vez de
        # desaparecer y dejar al dueño sin saber si mide o no.
        "marcador": marcador_estado,

        # El once: los puntos sentados, el sesgo por posicion y
        # el equipo que habia que mirar. No decide nada.
        "once": once_bloque,

        # La doctrina: que decisiones citan regla, cuales no,
        # los recien ascendidos, el embudo del mercado y el
        # activo que pesa demasiado. No decide nada.
        "doctrina": doctrina,

        # La vara del once: los factores por posicion, su
        # muestra, el once que sale con ellos y el que salia sin
        # ellos, y la linea para apagarlos.
        "vara": vara,

        # La via TENER y el tramo que la sostiene. Esta SI
        # decide: si el tramo de un jugador esta medido y rinde
        # por debajo del liston, `hold_value` no le da valor.
        "hold_route": via_tener,

        # Lo que Pepe hizo al pujar, no solo lo que pensaba pujar.
        "bid_outcomes": bid_outcome_summary(),

        # LA SUBASTA DEL RESET, antes de que ocurra: por quien
        # va a pujar el ciclo, cuanto compromete y cuanto falta
        # para el cierre. Y debajo, lo que gano y perdio.
        "subasta": bloque_de_la_subasta(
            {
                # LA MISMA FORMA QUE VE EL CICLO
                #
                #     El tablero, los bolsillos y el reloj no
                #     estan en `state`: se montan aqui. Si se
                #     le pasara `state` a secas, esta pantalla
                #     diria "no hay candidatos" mientras el
                #     ciclo puja por tres.
                "acquisition": acquisition,
                "exposure": exposure,
                "market_clock": market_clock,
                "rival_intelligence": {
                    "managers": rivales_compactos
                },
                "solvency_clock": solvency_clock,
                "operations_locked": state.get("operations_locked"),
                "phase": state.get("phase"),
            },
            snapshot,
        ),

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
