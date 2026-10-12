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
