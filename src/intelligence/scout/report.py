"""
El informe del ojeador: junta a las fuentes y dice quien dijo que.

QUE PROBLEMA RESUELVE

    La revalorizacion estimada de Pepe es una CONSTANTE. Los 22
    candidatos del tablero rendian exactamente 0,22 %, todos. No
    es un fallo de calculo: es que no hay calculo. Pepe no puede
    distinguir a un jugador de otro por precio, asi que cualquier
    decision de compra que dependa de eso es una moneda al aire.

    Este informe pone, al lado de esa constante, lo que tres webs
    dicen de CADA jugador. Aunque acierten regular, discriminan; y
    una constante no discrimina nada.

EL CONSENSO NO ES UNA MEDIA CIEGA

    Con una sola fuente, el consenso ES esa fuente, y se dice con
    esas palabras: `agreement: "SINGLE"`. Nunca se inventa un
    acuerdo que no existe.

    Y el pulso de Comuniate -la demanda de las ultimas 24 h- NO
    vota en el consenso de direccion, aunque venga de Comuniate.
    Si votara, Comuniate contaria dos veces y ademas mezclaria lo
    que ya paso con lo que la gente esta haciendo ahora. Viaja
    aparte, en `demand`.

LO QUE ESTE INFORME NO ES

    Un pronostico. Las tres fuentes publican movimiento
    OBSERVADO: el cambio del ultimo mercado. Ninguna publica un
    porcentaje de confianza. Esta escrito en cada señal
    (`observed`) y en la cabecera del informe (`caveat`), para
    que dentro de un mes nadie lo lea al reves.

FASE OBSERVADOR

    Ningun motor lee esto. Se calcula, se escribe en disco, se
    pinta, y ahi acaba.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path

from src.intelligence.scout import (
    analitica_market,
    comuniate_market,
    futbolfantasy_market,
    jornada_perfecta_market,
)
from src.intelligence.scout.common import DOWN, FLAT, UP, now_iso, safe_int
from src.intelligence.scout.matching import build_targets, match_records


VERSION = "V1.0"

REPORT_FILE = (
    Path("data")
    / "intelligence"
    / "scout_report.json"
)


# Seis horas. Las noticias de mercado no cambian cada cuarto de
# hora, y el ciclo corre 48 veces al dia: sin TTL serian 48
# visitas diarias a cada web para leer lo mismo.
DEFAULT_TTL_SECONDS = 6 * 3600

# El mercado del Computer se resetea a las 07:00 (Madrid). Los
# precios de Biwenger se mueven ahi, asi que un informe de antes
# del reset esta hablando de otro mercado.
RESET_HOUR_MADRID = 7


SCOUTS = (
    futbolfantasy_market,
    analitica_market,
    comuniate_market,
    jornada_perfecta_market,
)


# El pulso no vota la direccion: no es lo mismo que se movio que
# lo que la gente esta haciendo.
DEMAND_SOURCE = "COMUNIATE_PULSO"


CAVEAT = (
    "Movimiento OBSERVADO, no pronostico. Las tres fuentes "
    "publican el cambio del ultimo mercado -sus propias paginas "
    "se llaman 'subidas y bajadas'- y ninguna publica un "
    "porcentaje de confianza. Que esto ademas prediga es una "
    "apuesta razonable, y por eso existe el libro de acierto."
)


def _load(path: Path) -> dict | None:
    try:
        valor = json.loads(path.read_text(encoding="utf-8-sig"))

    except (OSError, json.JSONDecodeError):
        return None

    return valor if isinstance(valor, dict) else None


def load_report(path: Path | None = None) -> dict | None:
    return _load(path or REPORT_FILE)


def report_age_seconds(
    report: dict | None,
    now: datetime | None = None,
) -> float | None:

    marca = (report or {}).get("generated_at")

    if not marca:
        return None

    try:
        momento = datetime.fromisoformat(
            str(marca).replace("Z", "+00:00")
        )

    except ValueError:
        return None

    return (
        (now or datetime.now(timezone.utc)) - momento
    ).total_seconds()


def crossed_reset(
    report: dict | None,
    now: datetime | None = None,
) -> bool:
    """
    ¿El informe es de antes del ultimo reset de las 07:00?

    Un informe de las 06:50 habla del mercado de ayer aunque solo
    tenga veinte minutos. La edad no basta: hay que mirar si por
    en medio ha pasado el reset.
    """

    marca = (report or {}).get("generated_at")

    if not marca:
        return True

    try:
        from zoneinfo import ZoneInfo

        madrid = ZoneInfo("Europe/Madrid")

        generado = datetime.fromisoformat(
            str(marca).replace("Z", "+00:00")
        ).astimezone(madrid)

        ahora = (now or datetime.now(timezone.utc)).astimezone(madrid)

    except Exception:                               # noqa: BLE001
        return False

    ultimo_reset = ahora.replace(
        hour=RESET_HOUR_MADRID,
        minute=0,
        second=0,
        microsecond=0,
    )

    if ahora < ultimo_reset:
        from datetime import timedelta

        ultimo_reset = ultimo_reset - timedelta(days=1)

    return generado < ultimo_reset


def is_fresh(
    report: dict | None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: datetime | None = None,
) -> bool:

    if not report or not report.get("players"):
        return False

    edad = report_age_seconds(report, now=now)

    if edad is None or edad >= ttl_seconds:
        return False

    return not crossed_reset(report, now=now)


# ============================================================
# EL CONSENSO
# ============================================================


def _consensus(signals: list) -> dict:
    """
    Quien dice que, y si estan de acuerdo.

    Una fuente, un voto: si FutbolFantasy manda tres señales -a
    1, 3 y 7 dias- no son tres votos. Se queda la de horizonte
    mas corto, que es la que habla del proximo mercado.
    """

    por_fuente: dict[str, dict] = {}

    for señal in signals:

        fuente = señal.get("source")

        if not fuente or fuente == DEMAND_SOURCE:
            continue

        horizonte = señal.get("horizon_days")

        actual = por_fuente.get(fuente)

        if actual is None or (
            horizonte is not None
            and (actual.get("horizon_days") or 99) > horizonte
        ):
            por_fuente[fuente] = señal

    votos = list(por_fuente.values())

    if not votos:
        return {
            "direction": None,
            "sources_agreeing": 0,
            "sources_total": 0,
            "mean_magnitude_percent": None,
            "agreement": "NONE",
            "note": "Ninguna fuente dice nada de este jugador.",
        }

    conteo = {UP: 0, DOWN: 0, FLAT: 0}

    for voto in votos:
        conteo[voto.get("direction", FLAT)] = (
            conteo.get(voto.get("direction", FLAT), 0) + 1
        )

    direccion = max(conteo, key=lambda clave: conteo[clave])
    de_acuerdo = conteo[direccion]

    porcentajes = [
        v["magnitude_percent"]
        for v in votos
        if v.get("direction") == direccion
        and v.get("magnitude_percent") is not None
    ]

    media = (
        round(sum(porcentajes) / len(porcentajes), 3)
        if porcentajes
        else None
    )

    if len(votos) == 1:
        acuerdo = "SINGLE"
        nota = (
            f"Solo lo dice {votos[0]['source']}. Esto no es un "
            f"consenso: es una fuente."
        )

    elif de_acuerdo == len(votos):
        acuerdo = "UNANIMOUS"
        nota = f"Las {len(votos)} fuentes dicen lo mismo."

    elif de_acuerdo * 2 > len(votos):
        acuerdo = "MAJORITY"
        nota = (
            f"{de_acuerdo} de {len(votos)} dicen {direccion}; el "
            f"resto no."
        )

    else:
        acuerdo = "SPLIT"
        nota = (
            f"No hay acuerdo: {conteo[UP]} dicen UP, "
            f"{conteo[DOWN]} DOWN, {conteo[FLAT]} FLAT."
        )

    return {
        "direction": direccion,
        "sources_agreeing": de_acuerdo,
        "sources_total": len(votos),
        "mean_magnitude_percent": media,
        "agreement": acuerdo,
        "note": nota,
    }


def _demand(signals: list) -> dict | None:
    """El pulso de Comuniate, aparte y sin votar."""

    for señal in signals:

        if señal.get("source") == DEMAND_SOURCE:
            return {
                "direction": señal.get("direction"),
                "pressure_points": señal.get("magnitude_percent"),
                "quote": señal.get("quote"),
                "observed": False,
            }

    return None


# ============================================================
# EL INFORME
# ============================================================


def build_report(
    catalog: dict | None,
    matchday=None,
    session=None,
    html_by_source: dict | None = None,
) -> dict:
    """
    Sale a la calle, empareja y sintetiza. Nunca lanza.

    `html_by_source` existe para las guardias: se le pasan
    paginas en disco y no se toca la red.
    """

    objetivos = build_targets(catalog)

    fuentes = {}
    sin_emparejar = []
    por_jugador: dict[str, dict] = {}

    for modulo in SCOUTS:

        nombre = modulo.SOURCE

        try:
            if html_by_source and nombre in html_by_source:
                resultado = modulo.scout(
                    html=html_by_source[nombre]
                )
            else:
                resultado = modulo.scout(session=session)

        except Exception as error:                  # noqa: BLE001
            resultado = {
                "source": nombre,
                "ok": False,
                "records": [],
                "error": f"{type(error).__name__}: {error}",
                "note": None,
            }

        registros = resultado.get("records") or []

        emparejados, huerfanos = (
            match_records(registros, objetivos)
            if registros and objetivos
            else ([], [])
        )

        # Sin catalogo no se puede emparejar nada, y eso no es lo
        # mismo que una fuente caida: se dice aparte.
        if registros and not objetivos:
            huerfanos = [
                {
                    "source": nombre,
                    "name": r.get("ff_name"),
                    "team": r.get("team_hint"),
                    "market_value": r.get("market_value"),
                    "reason": (
                        "No hay catalogo de Biwenger contra el que "
                        "emparejar."
                    ),
                }
                for r in registros
            ]

        sin_emparejar.extend(huerfanos)

        fuentes[nombre] = {
            "ok": bool(resultado.get("ok")),
            "players": len(emparejados),
            "records": len(registros),
            "unmatched": len(huerfanos),
            "error": resultado.get("error"),
            "note": resultado.get("note"),
            "fetched_at": resultado.get("fetched_at"),
        }

        for pareja in emparejados:

            objetivo = pareja["target"]
            registro = pareja["record"]

            clave = str(objetivo["id"])

            ficha = por_jugador.setdefault(
                clave,
                {
                    "player_name": objetivo["name"],
                    "market_price": objetivo.get("price"),
                    "signals": [],
                    "matches": [],
                },
            )

            for señal in registro.get("signals") or []:
                ficha["signals"].append(señal)

            # Como se identifico a este jugador en esta fuente.
            # Es lo que permite auditar un emparejamiento raro sin
            # volver a bajar la pagina.
            ficha["matches"].append(
                {
                    "source": nombre,
                    "method": pareja["method"],
                    "score": pareja["score"],
                    "margin": pareja["margin"],
                    "source_name": registro.get("ff_name"),
                    "source_value": registro.get("market_value"),
                }
            )

            for extra in ("trend_days", "acceleration", "deceleration",
                          "demand_percent", "supply_percent",
                          "ownership_percent"):
                if registro.get(extra) is not None:
                    ficha[extra] = registro[extra]

    for ficha in por_jugador.values():
        ficha["consensus"] = _consensus(ficha["signals"])
        ficha["demand"] = _demand(ficha["signals"])

    activas = [n for n, d in fuentes.items() if d["ok"]]

    return {
        "version": VERSION,
        "generated_at": now_iso(),
        "matchday": safe_int(matchday) or None,

        # Que quede escrito en el propio fichero.
        "observer_only": True,
        "caveat": CAVEAT,

        "sources": fuentes,
        "sources_ok": len(activas),
        "sources_total": len(fuentes),

        "players": por_jugador,
        "players_count": len(por_jugador),

        "unmatched": sin_emparejar,
        "unmatched_count": len(sin_emparejar),
    }


def save_report(report: dict, path: Path | None = None) -> None:
    destino = path or REPORT_FILE

    destino.parent.mkdir(parents=True, exist_ok=True)

    destino.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def refresh_report(
    catalog: dict | None,
    matchday=None,
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    force: bool = False,
    session=None,
    path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """
    El informe de hoy, de disco si vale y de la calle si no.

    NUNCA LANZA. Un fallo del ojeador jamas puede detener un
    ciclo: si algo va mal se devuelve lo ultimo que hubiera, y si
    no hay nada, un informe vacio que dice por que.
    """

    destino = path or REPORT_FILE

    try:
        anterior = _load(destino)

        if not force and is_fresh(anterior, ttl_seconds, now=now):
            salida = dict(anterior)
            salida["cache"] = {
                "status": "HIT",
                "age_seconds": round(
                    report_age_seconds(anterior, now=now) or 0, 1
                ),
                "ttl_seconds": ttl_seconds,
            }
            return salida

        nuevo = build_report(
            catalog,
            matchday=matchday,
            session=session,
        )

        # Si no ha entrado NI UNA fuente, no se pisa lo que
        # habia: un informe vacio recien escrito es peor que uno
        # de hace seis horas, porque parece dato.
        if not nuevo.get("players") and anterior and anterior.get("players"):

            salida = dict(anterior)
            salida["cache"] = {
                "status": "STALE_FALLBACK",
                "age_seconds": round(
                    report_age_seconds(anterior, now=now) or 0, 1
                ),
                "ttl_seconds": ttl_seconds,
                "error": (
                    "Ninguna fuente trajo jugadores emparejados: se "
                    "conserva el informe anterior."
                ),
            }
            return salida

        save_report(nuevo, destino)

        nuevo["cache"] = {
            "status": "REFRESHED",
            "age_seconds": 0.0,
            "ttl_seconds": ttl_seconds,
        }

        return nuevo

    except Exception as error:                      # noqa: BLE001
        return {
            "version": VERSION,
            "generated_at": now_iso(),
            "observer_only": True,
            "caveat": CAVEAT,
            "sources": {},
            "players": {},
            "players_count": 0,
            "unmatched": [],
            "unmatched_count": 0,
            "cache": {
                "status": "FAILED",
                "error": f"{type(error).__name__}: {error}",
            },
        }
