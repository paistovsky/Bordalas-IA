"""
LA PROXIMA JORNADA: las rondas de Biwenger, no las jornadas de LaLiga
(12/10/2026).

POR QUE EXISTE

    Tres relojes de Pepe preguntaban lo mismo («¿cuánto falta para que
    se cierre el once?» y «¿hay jornada jugándose?») y los tres miraban
    la hora del PRIMER partido de cada jornada de LaLiga:

        `los_chollos.horas_a_la_jornada`        (chollos, ronda, mejora)
        `la_mejora_del_once.jornada_en_curso`   (mejora)

    Y el primer partido miente cuando se adelanta o se aplaza:

        J6  Real Sociedad-Celta      03/09 21:00   ADELANTADO
            los otros 8              15-17/09      el grueso
            Levante-Athletic         21/10 20:00   APLAZADO (cambio del
                                                   17/09, calendar_changes)

    Con `first_kickoff` = 03/09, la «jornada 6 en curso» duró de 03/09
    21:00 a 04/09 00:00 y el arranque del 15/09 no lo vio nadie: el
    16/09 se podía vender a un titular con el partido por jugar, y la
    ronda contaba las horas hasta la J7. Y el aplazado del 21/10 cae
    entre la J9 y la J10: Biwenger ya hizo del último aplazado de la J6
    una ronda aparte (round 5125, `src/analysis/marcador.py:258-266`),
    con su propio cierre. Si ese día estamos en rojo, los nuestros del
    Levante y del Athletic hacen 0.

LA REGLA

    1. Por jornada de LaLiga, la VENTANA PRINCIPAL son los partidos a
       `VENTANA` (3 días) o menos de la mediana de sus horas (la de
       abajo si son pares: siempre es la hora de un partido de verdad).
    2. Lo que cae fuera (adelantado o aplazado) es OTRA RONDA. Los de
       fuera que se juegan juntos (a `VENTANA` o menos del primero del
       grupo) van en la misma, como el round 5125.
    3. Cada ronda empieza en su primer partido (el cierre del once) y
       acaba en su último partido. Las rondas de jornadas distintas NO
       se juntan aunque se pisen: cada una trae su cierre.
    4. `horas_al_proximo_cierre`: horas hasta el inicio de la próxima
       ronda que no ha empezado. None si no se sabe.
    5. `jornada_en_curso`: True entre el inicio de una ronda y 3 h
       (`MARGEN_FINAL`) después de su último partido. Si algo falla, o
       el calendario no trae ninguna ronda, True: sin saberlo, no se
       vende.

EL PROXIMO CIERRE, CON SU CLASE (20/10/2026)

    `horas_al_proximo_cierre` cuenta el aplazado como el cierre que
    viene, y es lo que tiene que hacer para VENDER: el aplazado tiene
    su propio control del saldo (en rojo, su premio es 0: E52, Luismi
    hizo 64 en la parcial de la J6 y cobro 0). Pero todos los motores
    de COMPRA paran a 40 h de esas horas, y el Levante-Athletic del
    mie 21/10 a las 20:00 los freno del mar 20/10 a las 04:00 hasta el
    partido: dos mercados (los resets del 20 y el 21) sin poder pujar,
    y el aplazado se puntua con el once congelado al empezar su jornada
    (laboratorio, n = 1): comprar no cambia sus puntos.

    `el_proximo_cierre` da las dos cosas a la vez, para quien las
    quiera separar (`la_orden_del_gestor.el_aplazado`):

        horas, inicio       el proximo cierre de CUALQUIER clase (las
                            mismas horas que `horas_al_proximo_cierre`)
        parcial             ese cierre es de una ronda de aplazados
                            (`es_parcial`: aparte, o con menos de
                            `PARTIDOS_DE_UNA_RONDA` partidos, como
                            `la_rotacion._es_parcial`; el calendario de
                            produccion trae el Levante-Athletic como J6
                            con un partido y SIN `aparte`)
        horas_principal,    la proxima ronda ENTERA que no ha empezado
        inicio_principal
        proximo_reset       el proximo reset de las 07:00 de Madrid
        resuelve_antes      ese reset cae ANTES del cierre: una puja de
                            ahora se resuelve antes del partido

    Sin saberlo (calendario ilegible, sin rondas por delante): `parcial`
    False y `resuelve_antes` False. Nadie relaja nada con un no se sabe.

QUE NO HACE

    No decide nada: da horas y un sí/no a quien vende o puja. No pide
    nada a Biwenger: lee `data/calendar/laliga_calendar.json` (el mismo
    que `los_chollos.CALENDARIO`), o el `ruta` o el dict que se le pase
    (los tests no tocan el de producción). Nunca lanza.
"""

from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
CALENDARIO = RAIZ / "data" / "calendar" / "laliga_calendar.json"   # = los_chollos.CALENDARIO

# La ventana principal de una jornada: a 3 días o menos de su mediana.
# Una jornada normal va de viernes 21:00 a lunes 21:00 (J8: 09-12/10,
# J9: 16-19/10): de la mediana a cada punta hay menos de 2 días. El
# adelantado de la J6 estaba a 13 días del grueso y el aplazado a 35.
VENTANA = timedelta(days=3)

# La jornada sigue «en curso» hasta 3 h después del último partido (lo
# que ya usaba `la_mejora_del_once.jornada_en_curso`): 90 min, descanso
# y el añadido, con margen.
MARGEN_FINAL = timedelta(hours=3)

# LA RONDA DE APLAZADOS (20/10/2026): aparte, o con menos de estos
# partidos. Las mismas 5 que `la_rotacion.PARTIDOS_DE_UNA_RONDA`: una
# jornada entera trae 10, y el calendario de produccion trae el
# Levante-Athletic como una J6 de un partido, sin `aparte`.
PARTIDOS_DE_UNA_RONDA = 5

# El reset del mercado: las 07:00 de Madrid (`la_rotacion.RESET_MADRID`).
RESET_MADRID = 7


def _hora(valor) -> datetime | None:
    """ISO a datetime con zona. Sin zona, la de Madrid (las del calendario
    son de LaLiga); si no hay tabla de zonas, UTC."""
    if not valor:
        return None
    try:
        t = datetime.fromisoformat(str(valor))
    except (TypeError, ValueError):
        return None
    if t.tzinfo is None:
        try:
            from zoneinfo import ZoneInfo

            t = t.replace(tzinfo=ZoneInfo("Europe/Madrid"))
        except Exception:                           # noqa: BLE001
            t = t.replace(tzinfo=timezone.utc)
    return t


def _ahora(ahora: datetime) -> datetime:
    """`ahora` sin zona se toma como UTC (los `correr` usan UTC)."""
    if ahora.tzinfo is None:
        return ahora.replace(tzinfo=timezone.utc)
    return ahora


def _leer(calendario) -> dict:
    """El calendario: un dict ya leído, o la ruta del fichero (por
    defecto `CALENDARIO`). Lanza si no se puede leer."""
    if isinstance(calendario, dict):
        return calendario
    return json.loads(Path(CALENDARIO if calendario is None else calendario).read_text())


def _horas_por_jornada(d: dict) -> dict:
    """{jornada: [hora de cada partido]}. Sin partidos, el `first_kickoff`."""
    por_jornada: dict = {}
    for j in d.get("matchdays") or []:
        if not isinstance(j, dict):
            continue
        horas = [_hora(m.get("kickoff")) for m in j.get("matches") or []
                 if isinstance(m, dict)]
        horas = [h for h in horas if h is not None]
        if not horas and _hora(j.get("first_kickoff")):
            horas = [_hora(j.get("first_kickoff"))]
        if horas:
            por_jornada.setdefault(j.get("matchday"), []).extend(horas)
    if not por_jornada:
        # Sin `matchdays`, la lista suelta de partidos.
        for m in d.get("matches") or []:
            if isinstance(m, dict) and _hora(m.get("kickoff")):
                por_jornada.setdefault(m.get("matchday"), []).append(_hora(m.get("kickoff")))
    return por_jornada


def _ronda(jornada, horas: list, aparte: bool) -> dict:
    return {"jornada": jornada, "inicio": horas[0], "fin": horas[-1],
            "partidos": len(horas), "aparte": aparte}


def _las_rondas(calendario) -> list:
    """Como `las_rondas`, pero lanza si el calendario no se puede leer."""
    rondas = []
    for jornada, horas in _horas_por_jornada(_leer(calendario)).items():
        horas = sorted(horas)
        mediana = horas[(len(horas) - 1) // 2]
        dentro = [h for h in horas if abs(h - mediana) <= VENTANA]
        fuera = [h for h in horas if abs(h - mediana) > VENTANA]
        rondas.append(_ronda(jornada, dentro, False))
        grupo: list = []
        for h in fuera:
            if grupo and h - grupo[0] > VENTANA:
                rondas.append(_ronda(jornada, grupo, True))
                grupo = []
            grupo.append(h)
        if grupo:
            rondas.append(_ronda(jornada, grupo, True))
    return sorted(rondas, key=lambda r: (r["inicio"], r["fin"]))


def las_rondas(calendario=None) -> list:
    """
    Las rondas «a lo Biwenger» del calendario, por hora de inicio:

        [{jornada, inicio, fin, partidos, aparte}]

    `inicio` es el primer partido (el cierre del once), `fin` el último;
    `aparte` dice que son partidos fuera de la ventana de su jornada
    (adelantados o aplazados). `calendario` es un dict ya leído o una
    ruta (por defecto la de producción). [] si no se puede leer.
    """
    try:
        return _las_rondas(calendario)
    except Exception:                               # noqa: BLE001
        return []


def los_equipos_de(ronda, calendario=None) -> list | None:
    """
    Los equipos que juegan una ronda (una de `las_rondas`): local y
    visitante de cada partido de su jornada que cae entre su `inicio`
    y su `fin`, con el nombre que trae el calendario («Levante UD»,
    «Athletic Club»). Ordenados y sin repetir.

    None si no se sabe: calendario ilegible, ningun partido en la
    ronda (la jornada sin partidos, solo con `first_kickoff`) o algun
    partido de la ronda sin los dos nombres. Quien pregunta para
    frenar algo tiene que frenarlo entero con None: una lista a
    medias diria que no juega quien si juega. Nunca lanza.
    """
    try:
        ronda = ronda if isinstance(ronda, dict) else {}
        inicio, fin = ronda.get("inicio"), ronda.get("fin")
        if inicio is None or fin is None:
            return None
        d = _leer(calendario)
        partidos = []
        for j in d.get("matchdays") or []:
            if isinstance(j, dict) and j.get("matchday") == ronda.get("jornada"):
                partidos += [m for m in j.get("matches") or [] if isinstance(m, dict)]
        if not partidos:
            # Sin `matchdays`, la lista suelta (como `_horas_por_jornada`).
            partidos = [m for m in d.get("matches") or []
                        if isinstance(m, dict) and m.get("matchday") == ronda.get("jornada")]
        equipos, vistos = set(), 0
        for m in partidos:
            hora = _hora(m.get("kickoff"))
            if hora is None or not inicio <= hora <= fin:
                continue
            vistos += 1
            casa, fuera = str(m.get("home") or "").strip(), str(m.get("away") or "").strip()
            if not casa or not fuera:
                return None
            equipos |= {casa, fuera}
        # Uno por partido de la ronda, o no se sabe.
        if not vistos or vistos != ronda.get("partidos"):
            return None
        return sorted(equipos)
    except Exception:                               # noqa: BLE001
        return None


def horas_al_proximo_cierre(ahora: datetime, ruta=None):
    """Horas desde `ahora` hasta el inicio de la próxima ronda que no ha
    empezado (aplazados y adelantados incluidos). None si no se sabe."""
    try:
        ahora = _ahora(ahora)
        futuros = [r["inicio"] for r in _las_rondas(ruta) if r["inicio"] > ahora]
        if not futuros:
            return None
        return (min(futuros) - ahora).total_seconds() / 3600
    except Exception:                               # noqa: BLE001
        return None


def jornada_en_curso(ahora: datetime, ruta=None) -> bool:
    """True entre el inicio de una ronda y 3 h después de su último
    partido. Si algo falla o no hay ninguna ronda, True: no se vende."""
    try:
        ahora = _ahora(ahora)
        rondas = _las_rondas(ruta)
        if not rondas:
            return True
        return any(r["inicio"] <= ahora <= r["fin"] + MARGEN_FINAL for r in rondas)
    except Exception:                               # noqa: BLE001
        return True


# ============================================================
# EL PROXIMO CIERRE, CON SU CLASE (20/10/2026)
# ============================================================

def es_parcial(ronda) -> bool:
    """
    Una ronda de aplazados (una de `las_rondas`): `aparte`, o con menos
    de `PARTIDOS_DE_UNA_RONDA` partidos. La misma regla que
    `la_rotacion._es_parcial`, y no el `principal` de
    `el_calendario_de_puntos` (que da el Levante-Athletic del 21/10 por
    principal: es la unica ronda de su J6 en el calendario de produccion).
    Sin saber sus partidos ni `aparte`, False: no se relaja nada. Pura,
    nunca lanza.
    """
    try:
        if not isinstance(ronda, dict):
            return False
        if ronda.get("aparte"):
            return True
        partidos = ronda.get("partidos")
        if partidos is None or isinstance(partidos, bool):
            return False
        return int(partidos) < PARTIDOS_DE_UNA_RONDA
    except Exception:                               # noqa: BLE001
        return False


def _el_reset_del_dia(dia) -> datetime:
    """Las 07:00 de Madrid de `dia`, en UTC, con la regla europea de
    `market_clock` (como `la_rotacion.el_reset_del_dia`: sin `zoneinfo`)."""
    from src.analysis.market_clock import madrid_offset_hours

    base = datetime(dia.year, dia.month, dia.day, RESET_MADRID, tzinfo=timezone.utc)
    return base - timedelta(hours=madrid_offset_hours(base.replace(hour=5)))


def el_proximo_reset(ahora) -> datetime | None:
    """El proximo reset de las 07:00 de Madrid DESPUES de `ahora`, en UTC
    (el de este mismo instante ya paso). None si no se sabe. Nunca
    lanza."""
    try:
        ahora = _ahora(ahora).astimezone(timezone.utc)
        hoy = ahora.date()
        futuros = [r for r in (_el_reset_del_dia(hoy + timedelta(days=d)) for d in (-1, 0, 1, 2))
                   if r > ahora]
        return min(futuros) if futuros else None
    except Exception:                               # noqa: BLE001
        return None


def el_proximo_cierre(ahora, ruta=None, reset=None) -> dict:
    """
    El proximo cierre y de que clase es (ver la cabecera, EL PROXIMO
    CIERRE, CON SU CLASE):

        {"horas", "inicio", "parcial", "horas_principal",
         "inicio_principal", "proximo_reset", "resuelve_antes"}

    `horas` e `inicio`: la proxima ronda de cualquier clase que no ha
    empezado (las horas de `horas_al_proximo_cierre`). `parcial`: es de
    aplazados (`es_parcial`); si a esa misma hora empieza tambien una
    ronda entera, no lo es. `horas_principal` e `inicio_principal`: la
    proxima ronda entera. `proximo_reset`: `reset` si se pasa (una hora
    con zona), si no el de `el_proximo_reset`. `resuelve_antes`: ese
    reset cae antes de `inicio`.

    Las horas, en UTC (`datetime` con zona). Sin saberlo: horas None,
    `parcial` False, `resuelve_antes` False. Nunca lanza.
    """
    salida = {"horas": None, "inicio": None, "parcial": False, "horas_principal": None,
              "inicio_principal": None, "proximo_reset": None, "resuelve_antes": False}
    try:
        ahora = _ahora(ahora)
        if reset is None:
            proximo = el_proximo_reset(ahora)
        elif isinstance(reset, datetime) and reset.tzinfo is not None:
            proximo = reset
        else:
            proximo = None
        salida["proximo_reset"] = proximo
        futuras = [r for r in _las_rondas(ruta) if r["inicio"] > ahora]
        if not futuras:
            return salida
        inicio = min(r["inicio"] for r in futuras)
        a_la_vez = [r for r in futuras if r["inicio"] == inicio]
        enteras = [r for r in futuras if not es_parcial(r)]
        salida.update({
            "horas": (inicio - ahora).total_seconds() / 3600,
            "inicio": inicio.astimezone(timezone.utc),
            "parcial": all(es_parcial(r) for r in a_la_vez),
            "resuelve_antes": bool(proximo is not None and proximo < inicio),
        })
        if enteras:
            principal = min(r["inicio"] for r in enteras)
            salida["inicio_principal"] = principal.astimezone(timezone.utc)
            salida["horas_principal"] = (principal - ahora).total_seconds() / 3600
        return salida
    except Exception:                               # noqa: BLE001
        return {"horas": None, "inicio": None, "parcial": False, "horas_principal": None,
                "inicio_principal": None, "proximo_reset": None, "resuelve_antes": False}
