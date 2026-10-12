"""
EL CALENDARIO DE PUNTOS (12/10/2026). Guardias de
`src/analysis/el_calendario_de_puntos.py`.

Todo lo que se usa va escrito aqui: ni `data/`, ni la foto, ni el
reloj (`ahora` se pasa siempre). Las veinte fichas del calendario y
de la clasificacion estan copiadas de los ficheros reales del 12/10
(data/calendar/laliga_calendar.json y
league_center.laliga.standings de dashboard/data/status.json).
"""

from __future__ import annotations

import json
import math
import sys

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.el_calendario_de_puntos import (  # noqa: E402
    RIVAL_DURO, RIVAL_RESTO, TASA_DEL_TRAMO, VENUE_CASA, VENUE_FUERA,
    casar_equipos, clave_de_equipo, contexto, factor, factor_medio,
    las_rondas, los_duros, los_ids, proximas_rondas, tasa_encogida, tier,
    valor_de_plantilla, xp_horizonte, xp_jugador, xp_ronda,
)


def _cerca(a, b, tol=1e-9):
    return a is not None and b is not None and math.isclose(a, b, rel_tol=0, abs_tol=tol)


# ------------------------------------------------------------
# Las veinte del calendario real (12/10/2026), tal cual.
# ------------------------------------------------------------
NOMBRES_DEL_CALENDARIO = [
    "Athletic Club", "Atlético de Madrid", "CA Osasuna", "Celta",
    "Deportivo Alavés", "Elche CF", "FC Barcelona", "Getafe CF",
    "Levante UD", "Málaga CF", "R. Racing Club", "RC Deportivo",
    "RCD Espanyol de Barcelona", "Rayo Vallecano", "Real Betis",
    "Real Madrid", "Real Sociedad", "Sevilla FC", "Valencia CF",
    "Villarreal CF",
]

# La clasificacion real del 12/10 14:07 (rank, team, points, played,
# goals_for, goals_against, goals_diff, biwenger_team_id).
_TABLA = [
    (1, "FC Barcelona", 24, 8, 34, 7, 27, 3),
    (2, "Atlético de Madrid", 19, 8, 18, 8, 10, 2),
    (3, "Real Betis", 19, 8, 14, 9, 5, 87),
    (4, "Real Madrid", 18, 8, 19, 8, 11, 15),
    (5, "Sevilla FC", 13, 7, 10, 9, 1, 17),
    (6, "Real Sociedad", 13, 8, 12, 15, -3, 13),
    (7, "Deportivo Alavés", 11, 8, 12, 8, 4, 91),
    (8, "RC Deportivo", 10, 8, 12, 11, 1, 6),
    (9, "Celta", 8, 8, 8, 6, 2, 5),
    (10, "Athletic Club", 8, 6, 7, 6, 1, 1),
    (11, "Villarreal CF", 8, 8, 13, 13, 0, 19),
    (12, "RCD Espanyol de Barcelona", 8, 8, 11, 11, 0, 7),
    (13, "Rayo Vallecano", 8, 7, 11, 16, -5, 70),
    (14, "Getafe CF", 8, 8, 4, 10, -6, 8),
    (15, "R. Racing Club", 8, 8, 13, 23, -10, 812),
    (16, "CA Osasuna", 8, 8, 8, 18, -10, 93),
    (17, "Elche CF", 6, 8, 11, 17, -6, 75),
    (18, "Levante UD", 5, 6, 8, 12, -4, 10),
    (19, "Valencia CF", 5, 8, 6, 15, -9, 18),
    (20, "Málaga CF", 4, 8, 4, 13, -9, 65),
]

CLASIFICACION = [
    {"rank": r, "team": t, "points": p, "played": j, "goals_for": gf,
     "goals_against": gc, "goals_diff": dg, "biwenger_team_id": i}
    for (r, t, p, j, gf, gc, dg, i) in _TABLA
]

ID = {t: i for (_, t, _, _, _, _, _, i) in _TABLA}


def _p(md, casa, fuera, hora):
    return {"matchday": md, "home": casa, "away": fuera, "kickoff": hora,
            "source": "MARCA_CALENDAR"}


def _calendario():
    """
    Un calendario como el real: la J6 con un partido ADELANTADO (el
    03/09, antes de toda la J5) y el Levante-Athletic APLAZADO al
    21/10 (entre la J9 y la J10). La J11 con dos aplazados a 1 dia
    entre si (una ronda) y otro en diciembre (otra).
    """
    jornadas = {
        5: [
            _p(5, "Sevilla FC", "Valencia CF", "2026-09-11T21:00:00+02:00"),
            _p(5, "R. Racing Club", "Deportivo Alavés", "2026-09-12T14:00:00+02:00"),
            _p(5, "Real Madrid", "Rayo Vallecano", "2026-09-12T21:00:00+02:00"),
            _p(5, "Villarreal CF", "Real Betis", "2026-09-14T21:00:00+02:00"),
        ],
        6: [
            _p(6, "Real Sociedad", "Celta", "2026-09-03T21:00:00+02:00"),
            _p(6, "Rayo Vallecano", "RCD Espanyol de Barcelona", "2026-09-15T19:00:00+02:00"),
            _p(6, "Deportivo Alavés", "Valencia CF", "2026-09-15T20:00:00+02:00"),
            _p(6, "Elche CF", "Real Madrid", "2026-09-15T21:30:00+02:00"),
            _p(6, "Atlético de Madrid", "CA Osasuna", "2026-09-16T19:00:00+02:00"),
            _p(6, "FC Barcelona", "R. Racing Club", "2026-09-16T21:30:00+02:00"),
            _p(6, "Levante UD", "Athletic Club", "2026-10-21T20:00:00+02:00"),
        ],
        7: [
            _p(7, "RCD Espanyol de Barcelona", "Elche CF", "2026-09-18T21:00:00+02:00"),
            _p(7, "Atlético de Madrid", "Real Madrid", "2026-09-20T16:15:00+02:00"),
        ],
        9: [
            _p(9, "RC Deportivo", "Levante UD", "2026-10-16T21:00:00+02:00"),
            _p(9, "RCD Espanyol de Barcelona", "Atlético de Madrid", "2026-10-17T14:00:00+02:00"),
            _p(9, "Villarreal CF", "Elche CF", "2026-10-17T16:15:00+02:00"),
            _p(9, "Real Betis", "FC Barcelona", "2026-10-17T18:30:00+02:00"),
            _p(9, "Real Madrid", "Sevilla FC", "2026-10-18T21:00:00+02:00"),
            _p(9, "Getafe CF", "Rayo Vallecano", "2026-10-19T21:00:00+02:00"),
        ],
        10: [
            _p(10, "Deportivo Alavés", "Málaga CF", "2026-10-23T21:00:00+02:00"),
            _p(10, "R. Racing Club", "RCD Espanyol de Barcelona", "2026-10-24T16:15:00+02:00"),
            _p(10, "Athletic Club", "Getafe CF", "2026-10-25T14:00:00+01:00"),
            _p(10, "FC Barcelona", "Real Madrid", "2026-10-25T21:00:00+01:00"),
            _p(10, "Sevilla FC", "CA Osasuna", "2026-10-26T21:00:00+01:00"),
        ],
        11: [
            _p(11, "Athletic Club", "Real Sociedad", "2026-10-30T21:00:00+01:00"),
            _p(11, "Real Betis", "Málaga CF", "2026-10-31T16:15:00+01:00"),
            _p(11, "Levante UD", "Atlético de Madrid", "2026-11-01T18:30:00+01:00"),
            _p(11, "Getafe CF", "Sevilla FC", "2026-11-02T21:00:00+01:00"),
            _p(11, "Rayo Vallecano", "Celta", "2026-11-11T19:00:00+01:00"),
            _p(11, "FC Barcelona", "Deportivo Alavés", "2026-11-12T21:00:00+01:00"),
            _p(11, "R. Racing Club", "Real Madrid", "2026-12-10T21:00:00+01:00"),
        ],
    }
    return {
        "season": "2026-27",
        "matchdays": [
            {"matchday": md, "first_kickoff": min(m["kickoff"] for m in ms), "matches": ms}
            for md, ms in jornadas.items()
        ],
    }


AHORA = "2026-10-12T14:09:00+02:00"


# ------------------------------------------------------------
# 4. Los factores
# ------------------------------------------------------------

def test_los_factores():
    assert (VENUE_CASA, VENUE_FUERA, RIVAL_DURO, RIVAL_RESTO) == (1.06, 0.94, 0.90, 1.04)
    assert _cerca(factor(4, True, True), 1.06 * 0.90)
    assert _cerca(factor(4, False, True), 0.94 * 0.90)      # el peor: 0,846
    assert _cerca(factor(4, True, False), 1.06 * 1.04)      # el mejor: 1,1024
    assert _cerca(factor(2, False, False), 0.94 * 1.04)
    assert _cerca(factor(3, True, None), 1.06)              # rival sin dato: 1,0
    assert _cerca(factor(3, None, True), 0.90)              # sede sin dato: 1,0
    # El portero no tiene sede (medido con n = 34: ruido), pero el
    # rival si le aplica.
    assert _cerca(factor(1, True, False), 1.04)
    assert _cerca(factor(1, False, False), 1.04)
    assert _cerca(factor(1, False, True), 0.90)
    assert _cerca(factor("GK", True, True), 0.90)
    assert _cerca(factor("DEL", True, True), 0.954)
    # Entrenador: lo de todos (no hay medida propia).
    assert _cerca(factor(5, True, False), 1.06 * 1.04)
    # Los extremos: 0,846 y 1,1024. En tres partidos, entre -15 % y
    # +10 % sobre el neutro (el desempate, no la regla).
    assert _cerca(factor(4, False, True), 0.846)
    assert _cerca(factor(4, True, False), 1.1024)


# ------------------------------------------------------------
# 1. El casado de nombres
# ------------------------------------------------------------

def test_casan_los_veinte_del_calendario_real():
    casado = casar_equipos(NOMBRES_DEL_CALENDARIO, CLASIFICACION)
    assert len(casado) == 20
    assert all(casado[n] for n in NOMBRES_DEL_CALENDARIO), casado
    assert len(set(casado.values())) == 20, casado
    assert set(casado.values()) == {f["biwenger_team_id"] for f in CLASIFICACION}
    for nombre in NOMBRES_DEL_CALENDARIO:
        assert casado[nombre] == ID[nombre], nombre
    # Los pares peligrosos, cada uno a su sitio.
    assert casado["FC Barcelona"] == 3 and casado["RCD Espanyol de Barcelona"] == 7
    assert casado["Real Madrid"] == 15 and casado["Atlético de Madrid"] == 2
    assert casado["Rayo Vallecano"] == 70 and casado["Athletic Club"] == 1
    assert casado["RC Deportivo"] == 6 and casado["Deportivo Alavés"] == 91
    # Y `los_ids`, con calendario, los trae todos.
    ids = los_ids(CLASIFICACION, _calendario())
    assert all(ids.get(n) == ID[n] for n in NOMBRES_DEL_CALENDARIO)


def test_casan_con_otros_nombres_sin_subcadenas():
    # Clasificacion con los nombres cortos de Biwenger: el calendario
    # MARCA tiene que casar igual, veinte a veinte.
    cortos = {
        "Barcelona": 3, "Atlético": 2, "Betis": 87, "Real Madrid": 15,
        "Sevilla": 17, "Real Sociedad": 13, "Alavés": 91, "Deportivo": 6,
        "Celta": 5, "Athletic": 1, "Villarreal": 19, "Espanyol": 7,
        "Rayo Vallecano": 70, "Getafe": 8, "Racing": 812, "Osasuna": 93,
        "Elche": 75, "Levante": 10, "Valencia": 18, "Málaga": 65,
    }
    filas = [{"team": t, "biwenger_team_id": i} for t, i in cortos.items()]
    casado = casar_equipos(NOMBRES_DEL_CALENDARIO, filas)
    assert all(casado[n] == ID[n] for n in NOMBRES_DEL_CALENDARIO), casado
    # Y con un mapa montado SIN calendario, la ronda casa igual.
    ids_cortos = los_ids(filas)
    ronda = {"matches": [_p(9, "RCD Espanyol de Barcelona", "Atlético de Madrid",
                            "2026-10-17T14:00:00+02:00")]}
    assert _cerca(xp_ronda(5, 90, 7, 4, ronda, ids_cortos, {2}), 4.5 * 1.06 * 0.90)
    assert _cerca(xp_ronda(5, 90, 2, 4, ronda, ids_cortos, {7}), 4.5 * 0.94 * 0.90)

    variantes = {
        "Espanyol": 7, "RCD Espanyol": 7, "Barcelona": 3, "Barça": 3,
        "F.C. Barcelona": 3, "Atlético": 2, "Atl. Madrid": 2,
        "Atletico Madrid": 2, "At. Madrid": 2, "Athletic Bilbao": 1,
        "Athletic": 1, "Real Madrid CF": 15, "Rayo": 70,
        "Real Sociedad de Fútbol": 13, "Betis": 87,
        "Real Betis Balompié": 87, "Celta de Vigo": 5, "RC Celta": 5,
        "Deportivo de La Coruña": 6, "Deportivo": 6, "RC Deportivo": 6,
        "Alavés": 91, "Deportivo Alaves": 91, "Racing de Santander": 812,
        "Real Racing Club": 812, "Club Atlético Osasuna": 93,
        "sevilla fc": 17, "VILLARREAL": 19, "Malaga": 65,
        # Lo que no es nadie, no casa con nadie.
        "Real": None, "": None, "Real Oviedo": None, "Girona FC": None,
        "FC": None,
    }
    casado = casar_equipos(list(variantes), CLASIFICACION)
    for nombre, esperado in variantes.items():
        assert casado.get(nombre) == esperado, (nombre, casado.get(nombre))

    # Con el Oviedo en la tabla, "Real ..." sigue sin confundirse.
    con_oviedo = CLASIFICACION + [{"team": "Real Oviedo", "biwenger_team_id": 99}]
    casado = casar_equipos(["Oviedo", "Real Sociedad", "Real Betis", "Real Madrid"], con_oviedo)
    assert casado == {"Oviedo": 99, "Real Sociedad": 13, "Real Betis": 87, "Real Madrid": 15}

    assert clave_de_equipo("RCD Espanyol de Barcelona") == "espanyol"
    assert clave_de_equipo("Atlético de Madrid") == "atletico"
    assert clave_de_equipo("Athletic Club") == "athletic"
    assert clave_de_equipo("Deportivo Alavés") == "alaves"
    assert clave_de_equipo("Real") is None


# ------------------------------------------------------------
# 2. Los duros
# ------------------------------------------------------------

def _seis_mas(x, y):
    """Cinco claramente arriba y dos que se juegan el sexto puesto."""
    fuertes = [
        {"rank": i, "team": f"F{i}", "points": 30, "played": 10,
         "goals_for": 20, "goals_against": 5, "goals_diff": 15,
         "biwenger_team_id": i}
        for i in range(1, 6)
    ]
    return fuertes + [x, y]


def _e(i, rank, pts, pj, gf, gc):
    return {"rank": rank, "team": f"E{i}", "points": pts, "played": pj,
            "goals_for": gf, "goals_against": gc, "goals_diff": gf - gc,
            "biwenger_team_id": i}


def test_los_duros_y_sus_desempates():
    # La tabla real: top-6 por puntos por partido. Atletico y Betis
    # empatan a 19/8 y desempata la diferencia de goles.
    assert los_duros(CLASIFICACION) == {3, 2, 87, 15, 17, 13}

    # Por partido, no por puntos: 15 en 9 (1,67) gana a 16 en 10 (1,6).
    assert los_duros(_seis_mas(_e(50, 6, 16, 10, 12, 10), _e(51, 7, 15, 9, 12, 10))) == {1, 2, 3, 4, 5, 51}
    # A igual por partido, la diferencia de goles por partido (aunque
    # el puesto oficial diga otra cosa).
    assert los_duros(_seis_mas(_e(50, 6, 15, 10, 12, 10), _e(51, 7, 15, 10, 12, 8))) == {1, 2, 3, 4, 5, 51}
    # A igual diferencia, los goles a favor por partido.
    assert los_duros(_seis_mas(_e(50, 7, 15, 10, 14, 12), _e(51, 6, 15, 10, 12, 10))) == {1, 2, 3, 4, 5, 50}
    # Empate total: el puesto oficial (LaLiga ya mira el particular).
    # Y nunca entra un septimo.
    assert los_duros(_seis_mas(_e(50, 7, 15, 10, 12, 10), _e(51, 6, 15, 10, 12, 10))) == {1, 2, 3, 4, 5, 51}
    # Sin partidos jugados, todo empata: decide el puesto oficial.
    cero = [_e(i, 21 - i, 0, 0, 0, 0) for i in range(1, 21)]
    assert los_duros(cero) == {20, 19, 18, 17, 16, 15}

    # UNION top-4 por valor de plantilla.
    tabla = _seis_mas(_e(50, 6, 16, 10, 12, 10), _e(51, 7, 15, 10, 12, 10))
    valores = {1: 10, 2: 9, 3: 8, 51: 50, 777: 999}      # 777 no esta en la tabla
    assert los_duros(tabla, valores) == {1, 2, 3, 4, 5, 50, 51}
    # A igual valor, el puesto oficial.
    assert los_duros(tabla, {50: 5, 51: 5, 1: 9, 2: 9, 3: 9}) == {1, 2, 3, 4, 5, 50}


def test_el_valor_de_plantilla():
    jugadores = [{"id": k, "team_id": 3, "price": k * 1_000_000, "position": 3} for k in range(1, 17)]
    jugadores += [
        {"id": 100, "team_id": 7, "price": 2_000_000, "position": 5},     # entrenador: cuenta
        {"id": 101, "team_id": 7, "price": None},
        {"id": 102, "team_id": None, "price": 9_000_000},
        {"id": 103, "team_id": 7, "price": 0},
        "basura",
    ]
    valores = valor_de_plantilla(jugadores)
    # Los 15 mas caros: 2..16 M.
    assert valores == {3: sum(range(2, 17)) * 1_000_000, 7: 2_000_000}
    # Tambien como dict {id: jugador}.
    assert valor_de_plantilla({j["id"]: j for j in jugadores if isinstance(j, dict)}) == valores


# ------------------------------------------------------------
# 3. Las rondas
# ------------------------------------------------------------

def test_las_rondas_parten_el_adelantado_y_el_aplazado():
    rondas = las_rondas(_calendario())
    vistas = [(r["label"], r["start"], r["end"], len(r["matches"])) for r in rondas]
    assert vistas == [
        ("Jornada 6 (adelantada)", "2026-09-03T21:00:00+02:00", "2026-09-03T21:00:00+02:00", 1),
        ("Jornada 5", "2026-09-11T21:00:00+02:00", "2026-09-14T21:00:00+02:00", 4),
        ("Jornada 6", "2026-09-15T19:00:00+02:00", "2026-09-16T21:30:00+02:00", 5),
        ("Jornada 7", "2026-09-18T21:00:00+02:00", "2026-09-20T16:15:00+02:00", 2),
        ("Jornada 9", "2026-10-16T21:00:00+02:00", "2026-10-19T21:00:00+02:00", 6),
        ("Jornada 6 (aplazada)", "2026-10-21T20:00:00+02:00", "2026-10-21T20:00:00+02:00", 1),
        ("Jornada 10", "2026-10-23T21:00:00+02:00", "2026-10-26T21:00:00+01:00", 5),
        ("Jornada 11", "2026-10-30T21:00:00+01:00", "2026-11-02T21:00:00+01:00", 4),
        # Dos aplazados a un dia entre si: UNA ronda. El de diciembre, otra.
        ("Jornada 11 (aplazada)", "2026-11-11T19:00:00+01:00", "2026-11-12T21:00:00+01:00", 2),
        ("Jornada 11 (aplazada)", "2026-12-10T21:00:00+01:00", "2026-12-10T21:00:00+01:00", 1),
    ], vistas
    assert [r["principal"] for r in rondas][:3] == [False, True, True]
    assert all(r["matchday"] == 6 for r in rondas if "Jornada 6" in r["label"])
    assert rondas[5]["matches"][0]["home"] == "Levante UD"
    # Se puede publicar tal cual.
    json.dumps(rondas)
    # Con los partidos sueltos en `matches` (sin `matchdays`), lo mismo.
    sueltos = [m for md in _calendario()["matchdays"] for m in md["matches"]]
    assert [r["label"] for r in las_rondas({"matches": sueltos})] == [v[0] for v in vistas]


def test_las_proximas_por_reloj():
    cal = _calendario()
    # El 12/10 (J8 en curso): J9, el aplazado de la J6 y la J10.
    assert [r["label"] for r in proximas_rondas(cal, AHORA, 3)] == [
        "Jornada 9", "Jornada 6 (aplazada)", "Jornada 10"]
    # Empezada la J9, ya no cuenta: su once esta cerrado.
    assert [r["label"] for r in proximas_rondas(cal, "2026-10-17T12:00:00+02:00", 3)] == [
        "Jornada 6 (aplazada)", "Jornada 10", "Jornada 11"]
    # Sin zona se lee UTC: 18:00 UTC son las 20:00 de Madrid, el
    # pitido del aplazado. "Despues de ahora" es estricto.
    assert proximas_rondas(cal, "2026-10-21T17:59:00", 1)[0]["label"] == "Jornada 6 (aplazada)"
    assert proximas_rondas(cal, "2026-10-21T18:00:00", 1)[0]["label"] == "Jornada 10"
    assert proximas_rondas(cal, datetime(2026, 10, 21, 18, 0, tzinfo=timezone.utc), 1)[0]["label"] == "Jornada 10"
    assert len(proximas_rondas(cal, AHORA, 10)) == 6
    assert proximas_rondas(cal, "2027-06-01T00:00:00+02:00", 3) == []
    assert proximas_rondas(cal, AHORA, 0) == []


def test_solo_las_principales():
    # La regla del dueño (12/10/2026): el aplazado del 21/10 lo puntua
    # Biwenger con el once de la J6, asi que no es ronda que planear.
    # Con `solo_principales`, las tres son la J9, la J10 y la J11.
    cal = _calendario()
    assert [r["label"] for r in proximas_rondas(cal, AHORA, 3, solo_principales=True)] == [
        "Jornada 9", "Jornada 10", "Jornada 11"]
    assert all(r["principal"] for r in proximas_rondas(cal, AHORA, 10, solo_principales=True))
    # Empezada la J9: quedan dos principales (los de la J11 en noviembre y
    # diciembre son aplazados), no se rellena con aplazados.
    assert [r["label"] for r in proximas_rondas(
        cal, "2026-10-17T12:00:00+02:00", 3, solo_principales=True)] == ["Jornada 10", "Jornada 11"]
    # El adelantado de la J6 (03/09) tampoco.
    assert [r["label"] for r in proximas_rondas(
        cal, "2026-09-01T00:00:00+02:00", 3, solo_principales=True)] == [
        "Jornada 5", "Jornada 6", "Jornada 7"]
    # Sin pedirlo, como antes.
    assert [r["label"] for r in proximas_rondas(cal, AHORA, 3)][1] == "Jornada 6 (aplazada)"
    # Y el contexto lo pasa.
    status = {"league_center": {"laliga": {"standings": CLASIFICACION}}}
    assert [r["label"] for r in contexto(status, cal, AHORA, 3, solo_principales=True)["rondas"]] == [
        "Jornada 9", "Jornada 10", "Jornada 11"]
    assert [r["label"] for r in contexto(status, cal, AHORA, 3)["rondas"]] == [
        "Jornada 9", "Jornada 6 (aplazada)", "Jornada 10"]
    assert proximas_rondas("basura", AHORA, 3, solo_principales=True) == []


# ------------------------------------------------------------
# 5. El xP: neutro sin partido, y el horizonte
# ------------------------------------------------------------

def test_neutro_si_no_juega_y_suma_si_juega_dos():
    cal = _calendario()
    ids = los_ids(CLASIFICACION, cal)
    duros = los_duros(CLASIFICACION)
    j9, aplazado, j10 = proximas_rondas(cal, AHORA, 3)
    base = 5 * 90 / 100

    # Espanyol, delantero: en casa contra el Atletico (duro).
    assert _cerca(xp_ronda(5, 90, 7, 4, j9, ids, duros), base * 1.06 * 0.90)
    # El aplazado no es suyo: NEUTRO, no cero.
    assert _cerca(xp_ronda(5, 90, 7, 4, aplazado, ids, duros), base)
    # Fuera en el Racing (15º, no duro).
    assert _cerca(xp_ronda(5, 90, 7, 4, j10, ids, duros), base * 0.94 * 1.04)
    # Su portero: sin sede, con rival.
    assert _cerca(xp_ronda(5, 90, 7, 1, j9, ids, duros), base * 0.90)
    # Levante: fuera en Riazor; en casa contra el Athletic en el aplazado.
    assert _cerca(xp_ronda(5, 90, 10, 3, j9, ids, duros), base * 0.94 * 1.04)
    assert _cerca(xp_ronda(5, 90, 10, 3, aplazado, ids, duros), base * 1.06 * 1.04)
    # Sin titularidad o sin tasa: None, como `esperado`.
    assert xp_ronda(5, None, 7, 4, j9, ids, duros) is None
    assert xp_ronda(None, 90, 7, 4, j9, ids, duros) is None
    # Sin duros conocidos, el rival no pesa (1,0): solo la sede.
    assert _cerca(xp_ronda(5, 90, 7, 4, j9, ids, set()), base * 1.06)

    # Dos partidos en una ronda: se suman los dos.
    doble = {"label": "doble", "matches": [
        _p(9, "RCD Espanyol de Barcelona", "Málaga CF", "2026-10-17T14:00:00+02:00"),
        _p(6, "FC Barcelona", "RCD Espanyol de Barcelona", "2026-10-19T21:00:00+02:00"),
    ]}
    assert _cerca(xp_ronda(5, 90, 7, 4, doble, ids, duros),
                  base * (1.06 * 1.04 + 0.94 * 0.90))


def test_el_horizonte_y_el_factor_medio():
    cal = _calendario()
    ids = los_ids(CLASIFICACION, cal)
    duros = los_duros(CLASIFICACION)
    rondas = proximas_rondas(cal, AHORA, 3)
    base = 5 * 90 / 100

    suma = sum(xp_ronda(5, 90, 7, 4, r, ids, duros) for r in rondas)
    assert _cerca(xp_horizonte(5, 90, 7, 4, rondas, ids, duros), suma)
    # Espanyol: 0,954 + 1,0 (no juega) + 0,9776.
    assert _cerca(suma, base * (0.954 + 1.0 + 0.9776))
    fm = factor_medio(7, 4, rondas, ids, duros)
    assert _cerca(fm, (0.954 + 1.0 + 0.9776) / 3)
    assert _cerca(xp_horizonte(5, 90, 7, 4, rondas, ids, duros), base * fm * 3)
    # n = 1 es la primera ronda.
    assert _cerca(xp_horizonte(5, 90, 7, 4, rondas, ids, duros, n=1),
                  xp_ronda(5, 90, 7, 4, rondas[0], ids, duros))
    assert _cerca(factor_medio(7, 4, rondas, ids, duros, n=1), 0.954)
    # Sin calendario: n x neutro (el esperado de siempre).
    assert _cerca(xp_horizonte(5, 90, 7, 4, [], ids, duros), 3 * base)
    assert factor_medio(7, 4, [], ids, duros) == 1.0
    # El ejemplo del dueño: tres fuera, en el Camp Nou, el
    # Metropolitano y el Bernabeu. Tasa 6 al 90 %: 13,7, no 16,2.
    tres_fuera = [
        {"matches": [_p(1, "FC Barcelona", "Elche CF", "2026-10-17T14:00:00+02:00")]},
        {"matches": [_p(2, "Atlético de Madrid", "Elche CF", "2026-10-24T14:00:00+02:00")]},
        {"matches": [_p(3, "Real Madrid", "Elche CF", "2026-10-31T14:00:00+01:00")]},
    ]
    assert round(xp_horizonte(6, 90, 75, 4, tres_fuera, ids, duros), 1) == 13.7
    assert round(xp_horizonte(6, 90, 75, 4, [], ids, duros), 1) == 16.2


# ------------------------------------------------------------
# 6. El encogimiento
# ------------------------------------------------------------

def test_el_encogimiento_hacia_el_tramo():
    assert TASA_DEL_TRAMO["1-4"][4] == 6.54 and TASA_DEL_TRAMO["11-20"][2] == 2.86
    # 2 partidos, delantero de arriba: (10 + 3·6,54) / 5.
    assert _cerca(tasa_encogida(10, 2, "1-4", 4), (10 + 3 * 6.54) / 5)
    # Sin partidos, el previo.
    assert _cerca(tasa_encogida(0, 0, "11-20", 2), 2.86)
    # Con muchos, casi la suya.
    assert _cerca(tasa_encogida(60, 15, "5-10", 3), (60 + 3 * 4.02) / 18)
    # k = 0: la tasa cruda.
    assert _cerca(tasa_encogida(10, 2, "1-4", 4, k=0), 5.0)
    # Sin tramo: el 5-10 (1,00x la liga).
    assert _cerca(tasa_encogida(10, 2, None, 1), (10 + 3 * 5.30) / 5)
    # Entrenador: sin previo medido, su tasa; sin partidos, None.
    assert _cerca(tasa_encogida(20, 4, "1-4", 5), 5.0)
    assert tasa_encogida(0, 0, "1-4", 5) is None
    # Los tramos, por el puesto de la tabla.
    assert tier(3, CLASIFICACION) == "1-4" and tier(15, CLASIFICACION) == "1-4"
    assert tier(17, CLASIFICACION) == "5-10" and tier(1, CLASIFICACION) == "5-10"
    assert tier(19, CLASIFICACION) == "11-20" and tier(65, CLASIFICACION) == "11-20"
    assert tier(999, CLASIFICACION) is None
    # Sin `rank`, el orden de la lista.
    sin_puesto = [{"team": f"T{i}", "biwenger_team_id": 100 + i} for i in range(1, 12)]
    assert [tier(100 + i, sin_puesto) for i in (4, 5, 10, 11)] == ["1-4", "5-10", "5-10", "11-20"]


# ------------------------------------------------------------
# 7. El contexto, una vez por vuelta
# ------------------------------------------------------------

def test_el_contexto_y_el_xp_del_jugador():
    jugadores = [
        {"id": 1, "team_id": 3, "price": 50_000_000, "position": 4},
        {"id": 2, "team_id": 3, "price": 50_000_000, "position": 3},
        {"id": 3, "team_id": 15, "price": 80_000_000, "position": 4},
        {"id": 4, "team_id": 19, "price": 70_000_000, "position": 4},   # Villarreal
        {"id": 5, "team_id": 2, "price": 30_000_000, "position": 3},
        {"id": 6, "team_id": 87, "price": 10_000_000, "position": 2},
        {"id": 7, "team_id": 75, "price": 3_000_000, "position": 2,      # Elche
         "points": 29, "played": 8},
        {"id": 8, "team_id": 7, "price": 4_000_000, "position": 4,       # Espanyol
         "points": 40, "played": 8},
    ]
    status = {"league_center": {"laliga": {"standings": CLASIFICACION}},
              "todaLaLiga": {"players": jugadores}}
    ctx = contexto(status, _calendario(), AHORA)
    assert ctx["available"] is True, ctx["reason"]
    assert ctx["sin_casar"] == []
    # Villarreal entra por valor de plantilla (top-4), no por tabla.
    assert ctx["duros"] == {3, 2, 87, 15, 17, 13, 19}
    assert [r["label"] for r in ctx["rondas"]] == ["Jornada 9", "Jornada 6 (aplazada)", "Jornada 10"]
    assert ctx["tramos"][75] == "11-20" and ctx["tramos"][3] == "1-4"

    # Elche, defensa: tasa encogida al 11-20; J9 fuera en Villarreal
    # (duro por valor), el aplazado y la J10 sin partido: neutros.
    elche = jugadores[6]
    tasa = (29 + 3 * 2.86) / 11
    base = tasa * 80 / 100
    assert _cerca(xp_jugador(ctx, elche, 80, 1), base * 0.94 * 0.90)
    assert _cerca(xp_jugador(ctx, elche, 80, 3), base * (0.846 + 1.0 + 1.0))
    # Espanyol, delantero del 11-20.
    esp = jugadores[7]
    tasa = (40 + 3 * 4.17) / 11
    assert _cerca(xp_jugador(ctx, esp, 90, 3), tasa * 0.9 * (0.954 + 1.0 + 0.9776))
    # La titularidad del propio jugador si no llega otra; sin ninguna, None.
    assert _cerca(xp_jugador(ctx, {**esp, "starter_probability": 90}, None, 3),
                  xp_jugador(ctx, esp, 90, 3))
    assert xp_jugador(ctx, esp, None, 3) is None


# ------------------------------------------------------------
# Nunca lanza
# ------------------------------------------------------------

def test_nunca_lanza_con_basura():
    basuras = [None, 7, "x", [], {}, [None, 3, "y"], {"matchdays": "x"},
               {"matchdays": [None, {"matches": 5}]}, {"matches": [{"kickoff": "ayer"}]},
               {"matchdays": [{"matchday": "seis", "matches": [{"home": None, "kickoff": 3}]}]},
               float("nan"), object()]
    for b in basuras:
        assert isinstance(factor(b, b, b), float)
        assert isinstance(casar_equipos(b, b), dict)
        assert clave_de_equipo(b) is None or isinstance(clave_de_equipo(b), str)
        assert isinstance(los_ids(b, b), dict)
        assert isinstance(los_duros(b, b), set)
        assert isinstance(valor_de_plantilla(b), dict)
        assert tier(b, b) is None
        assert las_rondas(b) == []
        assert proximas_rondas(b, AHORA, 3) == []
        if b is not None:                           # None seria el reloj
            assert proximas_rondas(_calendario(), b, 3) == []
        assert xp_ronda(None, b, b, b, b, b, b) is None
        assert xp_horizonte(b, None, b, b, b, b, b, b) is None
        for x in (xp_ronda(b, b, b, b, b, b, b), xp_horizonte(b, b, b, b, b, b, b, b)):
            assert x is None or isinstance(x, float)
        assert factor_medio(b, b, b, b, b) == 1.0
        assert xp_jugador(b, b, b, b) is None
        assert contexto(b, b, AHORA)["available"] is False
        tasa_encogida(b, b, b, b, b)
    # Basura en las filas no tumba lo bueno.
    tabla = CLASIFICACION + [None, "x", {"team": "Real", "biwenger_team_id": "z"}]
    assert los_duros(tabla) == {3, 2, 87, 15, 17, 13}
    assert los_ids(tabla, _calendario())["Celta"] == 5
    # Tasa y titularidad como texto valen; la ronda rota da neutro.
    assert _cerca(xp_ronda("5", "90", 7, 4, None, None, None), 4.5)
    assert _cerca(xp_horizonte(5, 90, 7, 4, "basura", None, None), 3 * 4.5)
    assert _cerca(xp_jugador({}, {"points": 10, "played": 2, "position": 4, "team_id": 7}, 90, 3),
                  3 * 0.9 * (10 + 3 * 4.39) / 5)
    # El contexto sin calendario sale neutro y lo dice.
    status = {"league_center": {"laliga": {"standings": CLASIFICACION}}}
    ctx = contexto(status, None, AHORA)
    assert ctx["available"] is False and ctx["rondas"] == [] and ctx["reason"]


TESTS = [test_los_factores, test_casan_los_veinte_del_calendario_real,
         test_casan_con_otros_nombres_sin_subcadenas, test_los_duros_y_sus_desempates,
         test_el_valor_de_plantilla, test_las_rondas_parten_el_adelantado_y_el_aplazado,
         test_las_proximas_por_reloj, test_solo_las_principales,
         test_neutro_si_no_juega_y_suma_si_juega_dos,
         test_el_horizonte_y_el_factor_medio, test_el_encogimiento_hacia_el_tramo,
         test_el_contexto_y_el_xp_del_jugador, test_nunca_lanza_con_basura]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
