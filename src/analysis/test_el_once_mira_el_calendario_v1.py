"""
EL ONCE MIRA EL CALENDARIO (12/10/2026). Guardias de
`src/analysis/el_once_mira_el_calendario.py` y de su enganche en
`lineup_engine.prepare_players`.

QUE SE COMPRUEBA

    1. APAGADO, el once es el de hoy: los scores de `prepare_players`
       salen clavados a los de main@21e33c70 sobre el mismo banco (el
       +5 de casa incluido), sin una clave nueva, y el calendario que
       se le pase ni se mira.
    2. PUESTO, entre dos delanteros con la misma base, el que juega en
       casa contra uno del resto queda por encima del que va al campo
       de un top-6. Y la busqueda del once lo pone a el.
    3. El que no juega en la ronda sale NEUTRO (1,0), nunca cero. La
       ronda objetivo es la proxima PRINCIPAL: el aplazado no lo es.
    4. Basura o falta de datos: neutro y los scores de hoy. Nunca lanza.
    5. Los factores se calculan UNA vez por vuelta (memoria).
    6. El +5 de casa no se suma cuando la sede ya va en el
       multiplicador; el bono del Dios sigue intacto.
    7. SOLO el once que se escribe (`con_calendario`, desde
       `lineup_monitor`) mira el calendario: `build_lineup` y
       `prepare_players` de los que valoran salen igual que apagado.
    8. Una vara negativa no mejora con un partido malo; un partido
       repetido cuenta una vez; una clasificacion de hace mas de 7
       dias no decide; un rival duro solo por valor de plantilla es
       duro; un nombre sin casar en la ronda deja neutro al que no
       sale; la memoria de la vuelta distingue catalogos.
    9. El camino de produccion: los dos ficheros del disco (en una
       carpeta temporal) y el reloj (suplantado).

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui. La clasificacion es la real del 12/10 14:07
    (league_center.laliga.standings de dashboard/data/status.json) y
    el calendario un trozo con la forma del real
    (data/calendar/laliga_calendar.json), como en
    `test_el_calendario_de_puntos_v1`. Ni `data/`, ni la foto, ni el
    reloj: `ahora` se pasa siempre.
"""

from __future__ import annotations

import math
import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Los dos
# interruptores que cambian la vara se quitan aqui arriba; el de este
# modulo lo pone y lo quita cada prueba.
ENV = "BORDALAS_EL_CALENDARIO_EN_EL_ONCE"
for _nombre in (ENV, "BORDALAS_CALIDAD_ETIQUETA", "BORDALAS_VARA_PLANA"):
    os.environ.pop(_nombre, None)


from src.analysis import el_once_mira_el_calendario as once_cal  # noqa: E402
from src.analysis.el_once_mira_el_calendario import (  # noqa: E402
    con_ids, del_ciclo, equipos_del_catalogo, los_factores, para_el_jugador,
    valores_del_catalogo,
)
from src.analysis.lineup_engine import (  # noqa: E402
    ESCALA_DE_LA_VARA, MANDATORY_HIERARCHY_BONUS, prepare_players,
    search_best_lineup_for_formation,
)


def _cerca(a, b, tol=1e-6):
    return a is not None and b is not None and math.isclose(a, b, rel_tol=0, abs_tol=tol)


class _Interruptor:
    """Pone (o quita) el interruptor solo dentro del `with`."""

    def __init__(self, puesto: bool):
        self.puesto = puesto

    def __enter__(self):
        self.antes = os.environ.get(ENV)
        if self.puesto:
            os.environ[ENV] = "1"
        else:
            os.environ.pop(ENV, None)
        once_cal.olvidar()
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.antes
        once_cal.olvidar()
        return False


# ============================================================
# LA CLASIFICACION REAL DEL 12/10 14:07
# ============================================================
# (rank, team, points, played, goals_for, goals_against, goals_diff,
# biwenger_team_id)
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

# La de la cache del panel (`data/league_center/laliga_standings.json`)
# NO trae `biwenger_team_id`: se lo pone el panel despues. Asi llega a
# la vuelta.
CLASIFICACION_DE_LA_CACHE = {
    "available": True,
    "source": "LALIGA_OFFICIAL",
    "standings": [
        {k: v for k, v in fila.items() if k != "biwenger_team_id"}
        for fila in CLASIFICACION
    ],
}

# Los equipos como los nombra Biwenger en `catalog.data.teams`. Nueve
# vistos en el roster del 12/10 (Villarreal, Espanyol, Alavés, Levante,
# Celta, Elche, Osasuna, Barcelona, Rayo Vallecano); el resto con la
# misma forma corta.
NOMBRES_DE_BIWENGER = {
    1: "Athletic", 2: "Atlético", 3: "Barcelona", 5: "Celta",
    6: "Deportivo", 7: "Espanyol", 8: "Getafe", 10: "Levante",
    13: "Real Sociedad", 15: "Real Madrid", 17: "Sevilla", 18: "Valencia",
    19: "Villarreal", 65: "Málaga", 70: "Rayo Vallecano", 75: "Elche",
    87: "Betis", 91: "Alavés", 93: "Osasuna", 812: "Racing",
}


# ============================================================
# EL CALENDARIO (la forma del real)
# ============================================================

def _p(md, casa, fuera, hora):
    return {"matchday": md, "home": casa, "away": fuera, "kickoff": hora,
            "source": "MARCA_CALENDAR"}


def _calendario():
    """
    La J9 de verdad a medias (seis partidos), el Levante-Athletic de
    la J6 APLAZADO al 21/10 (su propia ronda, entre la J9 y la J10) y
    un trozo de la J10. El Athletic no juega en esta J9.
    """
    jornadas = {
        6: [
            _p(6, "Rayo Vallecano", "RCD Espanyol de Barcelona", "2026-09-15T19:00:00+02:00"),
            _p(6, "Deportivo Alavés", "Valencia CF", "2026-09-15T20:00:00+02:00"),
            _p(6, "FC Barcelona", "R. Racing Club", "2026-09-16T21:30:00+02:00"),
            _p(6, "Levante UD", "Athletic Club", "2026-10-21T20:00:00+02:00"),
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
            _p(10, "Athletic Club", "Getafe CF", "2026-10-25T14:00:00+01:00"),
            _p(10, "FC Barcelona", "Real Madrid", "2026-10-25T21:00:00+01:00"),
        ],
    }
    return {
        "season": "2026-27",
        "matchdays": [
            {"matchday": md, "first_kickoff": min(m["kickoff"] for m in ms), "matches": ms}
            for md, ms in jornadas.items()
        ],
    }


AHORA = "2026-10-12T14:09:00+02:00"          # antes de la J9
TRAS_EL_CIERRE_J9 = "2026-10-17T10:00:00+02:00"  # la J9 ya empezo


# ============================================================
# EL BANCO: la plantilla, el tablero de FF y la foto
# ============================================================

def _jugador(pid, nombre, pos, equipo, precio=10_000_000, estado="ok"):
    """Misma base para todos salvo lo que se cambie: precio, puntos,
    partidos y temporada pasada iguales."""
    return {
        "id": pid, "name": nombre, "position": pos, "teamID": equipo,
        "price": precio, "points": 30, "played_home": 3, "played_away": 3,
        "pointsLastSeason": 100, "status": estado,
    }


PORTERO = _jugador(9001, "Portero del Villarreal", 1, 19)
DEL_CASA = _jugador(9002, "Delantero del Villarreal", 4, 19)    # en casa vs Elche (17.º)
DEL_FUERA = _jugador(9003, "Delantero del Sevilla", 4, 17)      # fuera, en el Bernabeu (4.º)
MEDIO_SIN_PARTIDO = _jugador(9004, "Medio del Athletic", 3, 1)  # el Athletic no juega la J9
DEFENSA_SIN_DATO = _jugador(9005, "Defensa sin pronostico", 2, 19)
LESIONADO = _jugador(9006, "Delantero lesionado", 4, 17, estado="injured")
DIOS = _jugador(9007, "Yamal", 4, 3)                            # fuera, en el Villamarin (3.º)

PLANTILLA = [PORTERO, DEL_FUERA, DEL_CASA, MEDIO_SIN_PARTIDO,
             DEFENSA_SIN_DATO, LESIONADO, DIOS]


def _fila(pid, prob, valor=40, etiqueta="Importante"):
    return {
        "player_id": pid, "starter_probability": prob, "consensus": "STARTER",
        "source_coverage": 1, "hierarchy": {"value": valor, "label": etiqueta},
    }


TABLERO = {"players": [
    _fila(9001, 90.0),
    _fila(9002, 70.0),
    _fila(9003, 70.0),
    _fila(9004, 80.0),
    _fila(9007, 85.0, 60, "Dios"),
]}

INTELIGENCIA_VACIA = {"lookup": {}}


def _juego(ronda, casa, fuera):
    return {"id": ronda * 100 + casa, "round": {"id": ronda},
            "home": {"id": casa}, "away": {"id": fuera}}


def _foto(con_catalogo_completo=False):
    """
    La foto con lo que lee el motor: la plantilla, la ronda de
    Biwenger y los `nextGames` que dan el +5 de casa al Villarreal.
    Con `con_catalogo_completo`, los veinte equipos y un jugador
    caro por equipo para el valor de plantilla.
    """
    equipos = {
        "19": {"id": 19, "name": "Villarreal", "nextGames": [_juego(5200, 19, 75)]},
        "17": {"id": 17, "name": "Sevilla", "nextGames": [_juego(5200, 15, 17)]},
        "3": {"id": 3, "name": "Barcelona", "nextGames": [_juego(5200, 87, 3)]},
        "1": {"id": 1, "name": "Athletic", "nextGames": []},
    }
    jugadores = {}
    if con_catalogo_completo:
        for ident, nombre in NOMBRES_DE_BIWENGER.items():
            equipos.setdefault(str(ident), {"id": ident, "name": nombre, "nextGames": []})
        # El valor de plantilla de verdad pone arriba a Barça, Madrid,
        # Atletico y Betis (165,8 / 133,4 / 94,4 / 78,2 M el 12/10).
        caros = {3: 165_800_000, 15: 133_400_000, 2: 94_400_000, 87: 78_200_000}
        for ident in NOMBRES_DE_BIWENGER:
            jugadores[str(80_000 + ident)] = {
                "id": 80_000 + ident, "teamID": ident,
                "price": caros.get(ident, 30_000_000),
            }
    return {
        "my_team": [dict(j) for j in PLANTILLA],
        "rounds": {"data": {"round": {"id": 5200}}},
        "catalog": {"data": {"teams": equipos, "players": jugadores}},
    }


def _preparar(foto=None, **kwargs):
    return {
        p["name"]: p
        for p in prepare_players(foto or _foto(), INTELIGENCIA_VACIA, TABLERO, **kwargs)
    }


def _huella(salida) -> str:
    import hashlib
    import json

    crudo = json.dumps(salida, sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _sin_lo_nuevo(salida) -> list:
    """La salida sin las dos claves que pone el interruptor."""
    limpia = []
    for p in salida:
        p = {k: v for k, v in p.items() if k not in ("fixture_multiplier", "fixture_reason")}
        p["lineup_score_components"] = {
            k: v for k, v in p["lineup_score_components"].items()
            if k not in ("fixture_multiplier", "fixture_reason")
        }
        limpia.append(p)
    return limpia


# ============================================================
# LO DE HOY: main@21e33c70, con el motor sin tocar
# ============================================================
#
# La salida ENTERA de `prepare_players` sobre este banco, medida con
# el `lineup_engine` de main antes de este cambio: sha256 del JSON
# ordenado (`_huella`). Con el interruptor apagado tiene que salir la
# misma, letra a letra. Si algun dia se cambia `prepare_players` A
# PROPOSITO (y apagado, como manda la casa, no deberia), se rehace
# con el interruptor apagado y se dice en el commit.
HUELLA_DE_MAIN = {
    "foto": "e68549230a56c4ca4389256dcbe3b001defc794f6da3e0624d290140471feb8b",
    "foto con catalogo": "76a9fd5ca4f4a5f3e8d12bee8da7119eb9845ff6b9ce2db58a9a7415cf3dfc20",
}

# Y los numeros, para que un rojo diga cual se movio. El +5 de casa
# del Villarreal va dentro (Biwenger: ronda 5200, Villarreal-Elche).
SCORES_DE_MAIN = {
    "Portero del Villarreal": 623479.1666666667,
    "Delantero del Sevilla": 609636.5141666667,
    "Delantero del Villarreal": 609641.5141666667,
    "Medio del Athletic": 663593.7450000001,
    "Defensa sin pronostico": -498605.0,
    "Delantero lesionado": -1000000.0,
    "Yamal": 10722843.939166667,
}

VARA_DE_MAIN = {
    "Delantero del Sevilla": 0.5994965141666667,
    "Delantero del Villarreal": 0.5994965141666667,
    "Medio del Athletic": 0.6524537450000001,
    "Yamal": 0.7112039391666667,
}

COMPONENTES_DE_MAIN = {
    "base", "jornada_perfecta_legacy", "starter_probability",
    "starter_source_coverage", "home_away", "penalty",
}

DATOS = dict(con_calendario=True, ahora=AHORA, calendario=_calendario(),
             clasificacion=CLASIFICACION)


# ============================================================
# 1. APAGADO, EL ONCE ES EL DE HOY
# ============================================================

def test_apagado_el_once_es_el_de_hoy():
    with _Interruptor(False):
        for nombre, foto in (("foto", _foto()), ("foto con catalogo", _foto(True))):
            salida = prepare_players(foto, INTELIGENCIA_VACIA, TABLERO)
            fichas = {p["name"]: p for p in salida}
            # Primero lo que dice QUE se movio; la huella, la ultima.
            for jugador, score in SCORES_DE_MAIN.items():
                assert fichas[jugador]["lineup_score"] == score, (jugador, fichas[jugador]["lineup_score"])
            for jugador, vara in VARA_DE_MAIN.items():
                assert fichas[jugador]["weekly_expected_value"] == vara, jugador
            for p in salida:
                assert "fixture_multiplier" not in p and "fixture_reason" not in p, p["name"]
                assert set(p["lineup_score_components"]) == COMPONENTES_DE_MAIN, p["name"]
            assert fichas["Delantero del Villarreal"]["home_away_adjustment"] == 5.0
            assert _huella(salida) == HUELLA_DE_MAIN[nombre], nombre


def test_apagado_ni_se_mira_el_calendario():
    """Apagado, el calendario que se le pase no cambia nada y ni se
    llega a montar: `del_ciclo` no se llama. Y PUESTO, quien no pide
    `con_calendario` (los que valoran) tampoco lo monta."""
    llamadas = []
    original = once_cal.del_ciclo

    def _espia(*args, **kwargs):
        llamadas.append(1)
        raise AssertionError("sin pedirlo no se monta el calendario")

    sin_pedirlo = {k: v for k, v in DATOS.items() if k != "con_calendario"}
    salidas = []
    try:
        once_cal.del_ciclo = _espia
        with _Interruptor(False):
            salidas.append(prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO, **DATOS))
            assert once_cal.para_el_once(_foto(), **sin_pedirlo) is None
        with _Interruptor(True):
            salidas.append(prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO, **sin_pedirlo))
            salidas.append(prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO))
    finally:
        once_cal.del_ciclo = original
    assert llamadas == []
    assert once_cal.cuenta()["calculos"] == 0
    for salida in salidas:
        assert _huella(salida) == HUELLA_DE_MAIN["foto"]


# ============================================================
# 2. PUESTO: EN CASA CONTRA EL RESTO PASA POR DELANTE
# ============================================================

def test_puesto_el_de_casa_contra_el_resto_pasa_por_delante():
    with _Interruptor(True):
        fichas = _preparar(**DATOS)
    casa = fichas["Delantero del Villarreal"]
    fuera = fichas["Delantero del Sevilla"]

    # La misma base: la misma vara cruda, la misma titularidad.
    assert casa["weekly_expected_value"] == fuera["weekly_expected_value"] == VARA_DE_MAIN["Delantero del Villarreal"]
    assert casa["base_lineup_score"] == fuera["base_lineup_score"]
    # Apagado solo los separaba el +5 de casa.
    assert SCORES_DE_MAIN["Delantero del Villarreal"] - SCORES_DE_MAIN["Delantero del Sevilla"] == 5.0

    # En casa contra el Elche (17.º): 1,06 x 1,04. Fuera en el
    # Bernabeu (4.º, top-6): 0,94 x 0,90.
    assert _cerca(casa["fixture_multiplier"], 1.06 * 1.04)
    assert _cerca(fuera["fixture_multiplier"], 0.94 * 0.90)
    assert "en casa vs Elche CF (resto)" in casa["fixture_reason"]
    assert "fuera vs Real Madrid (duro)" in fuera["fixture_reason"]
    assert casa["lineup_score_components"]["fixture_multiplier"] == casa["fixture_multiplier"]
    assert casa["lineup_score_components"]["fixture_reason"] == casa["fixture_reason"]

    # El score es la cuenta de siempre con la vara multiplicada y sin
    # el +5: vara x mult x 1.000.000 + el resto igual.
    vara = VARA_DE_MAIN["Delantero del Villarreal"]
    for ficha, apagado, mult, cinco in (
        (casa, SCORES_DE_MAIN["Delantero del Villarreal"], 1.06 * 1.04, 5.0),
        (fuera, SCORES_DE_MAIN["Delantero del Sevilla"], 0.94 * 0.90, 0.0),
    ):
        esperado = apagado - cinco + vara * (mult - 1.0) * ESCALA_DE_LA_VARA
        assert _cerca(ficha["lineup_score"], esperado, 1e-4), (ficha["name"], ficha["lineup_score"], esperado)

    assert casa["lineup_score"] > fuera["lineup_score"]
    # Y no por un desempate: ~153.000 de score (0,256 de multiplicador
    # sobre 0,60 de vara).
    assert casa["lineup_score"] - fuera["lineup_score"] > 150_000


def test_la_busqueda_del_once_lo_pone_a_el():
    """Con un hueco de delantero: apagado gana el del Sevilla (diez
    millones mas caro, +10 de base contra el +5 de casa); puesto, el
    del Villarreal."""
    caro = {**DEL_FUERA, "price": DEL_FUERA["price"] + 10_000_000}
    foto = {**_foto(), "my_team": [dict(caro), dict(DEL_CASA)]}
    hueco = {4: 1}

    with _Interruptor(False):
        apagado = prepare_players(foto, INTELIGENCIA_VACIA, TABLERO)
        elegido_apagado = search_best_lineup_for_formation(apagado, hueco)["selected"]
    with _Interruptor(True):
        puesto = prepare_players(foto, INTELIGENCIA_VACIA, TABLERO, **DATOS)
        elegido_puesto = search_best_lineup_for_formation(puesto, hueco)["selected"]

    assert [p["name"] for p in elegido_apagado] == ["Delantero del Sevilla"]
    assert [p["name"] for p in elegido_puesto] == ["Delantero del Villarreal"]


# ============================================================
# 3. EL QUE NO JUEGA: NEUTRO, NUNCA CERO
# ============================================================

def test_el_que_no_juega_sale_neutro():
    with _Interruptor(True):
        fichas = _preparar(**DATOS)
        medio = fichas["Medio del Athletic"]
        assert medio["fixture_multiplier"] == 1.0
        assert "no juega en esta ronda" in medio["fixture_reason"]
        # Ni un punto movido: el Athletic no tenia +5 que quitar.
        assert medio["lineup_score"] == SCORES_DE_MAIN["Medio del Athletic"]

        # Empezada la J9, la proxima ronda PRINCIPAL es la J10. El
        # APLAZADO de la J6 (Levante-Athletic, 21/10) cae antes, pero
        # se puntua con el once de la J6: no es ronda objetivo (el
        # dueño, 12/10). Ni justo tras la J9, ni la vispera del
        # aplazado, ni con el aplazado ya empezado.
        tras = {}
        for momento in (TRAS_EL_CIERRE_J9, "2026-10-21T12:00:00+02:00",
                        "2026-10-21T20:30:00+02:00"):
            tras[momento] = _preparar(con_calendario=True, ahora=momento,
                                      calendario=_calendario(), clasificacion=CLASIFICACION)
    for momento, fichas in tras.items():
        for p in fichas.values():
            assert "aplazada" not in p["fixture_reason"], (momento, p["fixture_reason"])
        # J10: Athletic-Getafe (14.º, resto) en casa.
        assert "Jornada 10" in fichas["Medio del Athletic"]["fixture_reason"], momento
        assert _cerca(fichas["Medio del Athletic"]["fixture_multiplier"], 1.06 * 1.04), momento
        # Barça-Madrid (4.º, duro) en casa.
        assert _cerca(fichas["Yamal"]["fixture_multiplier"], 1.06 * 0.90), momento
        for nombre in ("Delantero del Villarreal", "Portero del Villarreal"):
            assert fichas[nombre]["fixture_multiplier"] == 1.0, (momento, nombre)
            assert "no juega en esta ronda" in fichas[nombre]["fixture_reason"], (momento, nombre)
        # Neutro es la vara de siempre: el del Villarreal pierde solo
        # su +5 (la sede ya la dice el calendario, y en esta ronda no
        # juega).
        assert fichas["Delantero del Villarreal"]["lineup_score"] == SCORES_DE_MAIN["Delantero del Villarreal"] - 5.0
        assert all(p["fixture_multiplier"] > 0 for p in fichas.values())
    # Y la pura dice lo mismo.
    assert los_factores(_calendario(), CLASIFICACION, "2026-10-21T12:00:00+02:00")["ronda"]["label"] == "Jornada 10"


def test_un_partido_repetido_cuenta_una_vez():
    """
    Una ronda es una jornada y en una jornada cada equipo juega una
    vez. Un partido duplicado en el calendario (mismo local, visitante
    y hora) no suma dos veces, y un equipo que saliese dos veces en la
    jornada se queda con el primero: nunca ~2,0 por un dato repetido.
    """
    calendario = _calendario()
    calendario["matchdays"].append({"matchday": 12, "matches": [
        _p(12, "Villarreal CF", "Elche CF", "2026-12-01T21:00:00+01:00"),
        _p(12, "Villarreal CF", "Elche CF", "2026-12-01T21:00:00+01:00"),
        _p(12, "Getafe CF", "Villarreal CF", "2026-12-03T21:00:00+01:00"),
        _p(12, "Real Madrid", "Celta", "2026-12-02T21:00:00+01:00"),
    ]})
    factores = los_factores(calendario, CLASIFICACION, "2026-11-20T12:00:00+01:00")
    assert factores["ronda"]["label"] == "Jornada 12", factores["ronda"]
    uno = para_el_jugador(factores, 19, 4)
    assert _cerca(uno["multiplicador"], 1.06 * 1.04), uno
    assert len(uno["partidos"]) == 1 and uno["con_calendario"] is True
    assert uno["partidos"][0]["rival"] == "Elche CF"
    # El Elche, una vez (fuera en Villarreal), y el Getafe tambien una.
    assert _cerca(para_el_jugador(factores, 75, 4)["multiplicador"], 0.94 * 1.04)
    assert len(para_el_jugador(factores, 8, 4)["partidos"]) == 1
    # El portero: sin sede, el rival si; una vez.
    assert _cerca(para_el_jugador(factores, 19, 1)["multiplicador"], 1.04)


# ============================================================
# 4. EL +5 DE CASA Y EL DIOS
# ============================================================

def test_el_mas_cinco_no_se_cuenta_dos_veces_y_el_dios_sigue():
    with _Interruptor(True):
        fichas = _preparar(**DATOS)
    casa = fichas["Delantero del Villarreal"]
    # El contexto sigue diciendo que juega en casa; el +5 ya no suma.
    assert casa["home_away_context"]["side"] == "home"
    assert casa["home_away_adjustment"] == 0.0
    assert casa["lineup_score_components"]["home_away"] == 0.0

    dios = fichas["Yamal"]
    assert dios["mandatory_hierarchy"] is True
    assert _cerca(dios["fixture_multiplier"], 0.94 * 0.90)          # fuera, Villamarin
    assert dios["lineup_score"] - dios["lineup_score_sporting"] == MANDATORY_HIERARCHY_BONUS
    assert dios["lineup_score"] > MANDATORY_HIERARCHY_BONUS
    assert dios["weekly_expected_value"] == VARA_DE_MAIN["Yamal"]    # la vara, cruda


# ============================================================
# 5. LA CLASIFICACION DE LA CACHE DEL PANEL (sin ids)
# ============================================================

def test_la_cache_del_panel_sin_ids_casa_con_el_catalogo():
    foto = _foto(True)
    filas = con_ids(CLASIFICACION_DE_LA_CACHE, equipos_del_catalogo(foto))
    assert {f["team"]: f.get("biwenger_team_id") for f in filas} == {
        f["team"]: f["biwenger_team_id"] for f in CLASIFICACION
    }
    # No toca lo que entra.
    assert all("biwenger_team_id" not in f for f in CLASIFICACION_DE_LA_CACHE["standings"])
    # El valor de plantilla mete a los cuatro caros.
    valores = valores_del_catalogo(foto)
    assert sorted(valores, key=lambda e: -valores[e])[:4] == [3, 15, 2, 87]

    with _Interruptor(True):
        con_tabla = _preparar(foto, **DATOS)
        con_cache = _preparar(foto, con_calendario=True, ahora=AHORA, calendario=_calendario(),
                              clasificacion=CLASIFICACION_DE_LA_CACHE)
    for nombre in SCORES_DE_MAIN:
        assert con_cache[nombre]["fixture_multiplier"] == con_tabla[nombre]["fixture_multiplier"], nombre
        assert con_cache[nombre]["lineup_score"] == con_tabla[nombre]["lineup_score"], nombre


def test_una_fila_sin_casar_no_cambia_los_duros():
    """
    Con un catalogo de cuatro equipos solo casan cuatro filas. Sin
    cuidado, el top-6 se contaria entre esas cuatro y el Villarreal
    (11.º) seria «duro». Las que no casan siguen en la tabla.
    """
    factores = los_factores(_calendario(), CLASIFICACION_DE_LA_CACHE, AHORA,
                            equipos_del_catalogo(_foto()), {})
    assert factores["available"] and factores["conocidos"] == [1, 3, 17, 19]
    assert 19 not in factores["duros"] and 1 not in factores["duros"]
    assert _cerca(para_el_jugador(factores, 19, 4)["multiplicador"], 1.06 * 1.04)
    assert _cerca(para_el_jugador(factores, 17, 4)["multiplicador"], 0.94 * 0.90)
    # Uno de un equipo que no casa (el Elche, 75): como hoy.
    elche = para_el_jugador(factores, 75, 4)
    assert elche["multiplicador"] == 1.0 and elche["con_calendario"] is False


# ============================================================
# 6. BASURA O FALTA DE DATOS: EL ONCE DE HOY, Y NUNCA LANZA
# ============================================================

# OJO: `calendario` y `clasificacion` a None son «los del disco» (la
# vuelta de produccion). Aqui la basura nunca es None: ninguna guardia
# abre `data/`.
BASURA = [
    dict(ahora=AHORA, calendario={"x": 1}, clasificacion="basura"),
    dict(ahora=AHORA, calendario=_calendario(), clasificacion=[]),
    dict(ahora=AHORA, calendario=_calendario(), clasificacion=[None, 7, "x"]),
    dict(ahora=AHORA, calendario=_calendario(), clasificacion={"available": False, "standings": []}),
    dict(ahora=AHORA, calendario="basura", clasificacion=CLASIFICACION),
    dict(ahora=AHORA, calendario={"matchdays": [None, {"matches": "x"}]}, clasificacion=CLASIFICACION),
    dict(ahora="no es una fecha", calendario=_calendario(), clasificacion=CLASIFICACION),
    dict(ahora="2027-08-01T12:00:00+02:00", calendario=_calendario(), clasificacion=CLASIFICACION),
    dict(ahora=AHORA, calendario=_calendario(),
         clasificacion=[{"team": t, "biwenger_team_id": "no"} for t in ("Celta", "Elche CF")]),
]


def test_basura_y_falta_de_datos_dan_el_once_de_hoy():
    for datos in BASURA:
        with _Interruptor(True):
            salida = prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO,
                                     con_calendario=True, **datos)
        assert all(p["fixture_multiplier"] == 1.0 for p in salida), datos
        assert all(p["fixture_reason"].startswith("neutro") for p in salida), (
            datos, [p["fixture_reason"] for p in salida])
        # Quitadas las dos claves nuevas, la salida es la de main.
        assert _huella(_sin_lo_nuevo(salida)) == HUELLA_DE_MAIN["foto"], datos


def test_nunca_lanza():
    basura = (None, 0, "x", [], {}, [None], {"available": True, "equipos": "x"},
              {"available": True, "conocidos": "x", "equipos": {19: "x"}})
    for b in basura:
        assert para_el_jugador(b, 19, 4)["multiplicador"] == 1.0
        assert para_el_jugador(b, b, b)["multiplicador"] == 1.0
        assert los_factores(b, b, b, b, b)["available"] is False
        assert los_factores(b, b, AHORA)["available"] is False
        assert isinstance(con_ids(b, b), list)
        assert equipos_del_catalogo(b) == [] and valores_del_catalogo(b) == {}
        assert del_ciclo(b, ahora="x", calendario=7, clasificacion=7)["available"] is False
    # Un equipo que es texto, un partido con el rival roto.
    factores = los_factores(_calendario(), CLASIFICACION, AHORA)
    assert para_el_jugador(factores, "abc", 4)["multiplicador"] == 1.0
    roto = {**factores, "equipos": {19: [{"en_casa": "?", "rival_duro": "?"}]}}
    assert para_el_jugador(roto, 19, 4)["multiplicador"] > 0
    with _Interruptor(True):
        foto = _foto()
        foto["my_team"].append({**DEL_CASA, "id": 9999, "name": "Sin equipo", "teamID": None})
        fichas = {p["name"]: p for p in prepare_players(foto, INTELIGENCIA_VACIA, TABLERO, **DATOS)}
    assert fichas["Sin equipo"]["fixture_multiplier"] == 1.0


# ============================================================
# 7. UNA VEZ POR VUELTA
# ============================================================

def test_una_vez_por_vuelta():
    import copy

    calculos = []
    original = once_cal.los_factores

    def _cuenta(*args, **kwargs):
        calculos.append(1)
        return original(*args, **kwargs)

    with _Interruptor(True):
        once_cal.los_factores = _cuenta
        try:
            foto = _foto(True)
            for minuto in range(0, 40, 4):
                # Como en la vuelta: copias de la foto (deepcopy en
                # `competitive_offer_portfolio_engine`) y el reloj
                # que avanza dentro de la misma ronda.
                prepare_players(copy.deepcopy(foto), INTELIGENCIA_VACIA, TABLERO,
                                con_calendario=True,
                                ahora=f"2026-10-12T14:{9 + minuto:02d}:00+02:00",
                                calendario=_calendario(), clasificacion=CLASIFICACION)
            assert len(calculos) == 1, calculos
            assert once_cal.cuenta()["calculos"] == 1
            assert once_cal.cuenta()["aciertos"] == 9

            # Otra ronda (la J9 ya empezo): otra cuenta, una sola vez.
            for _ in range(3):
                prepare_players(copy.deepcopy(foto), INTELIGENCIA_VACIA, TABLERO,
                                con_calendario=True,
                                ahora=TRAS_EL_CIERRE_J9, calendario=_calendario(),
                                clasificacion=CLASIFICACION)
            assert len(calculos) == 2, calculos

            # El aplazado de la J6 empieza (21/10 20:00) y la ronda
            # objetivo sigue siendo la J10: ni otra clave ni otra
            # cuenta.
            for momento in ("2026-10-21T19:59:00+02:00", "2026-10-21T20:01:00+02:00"):
                prepare_players(copy.deepcopy(foto), INTELIGENCIA_VACIA, TABLERO,
                                con_calendario=True, ahora=momento,
                                calendario=_calendario(), clasificacion=CLASIFICACION)
            assert len(calculos) == 2, calculos

            # Otra clasificacion (otra vuelta): otra cuenta.
            prepare_players(copy.deepcopy(foto), INTELIGENCIA_VACIA, TABLERO,
                            con_calendario=True,
                            ahora=TRAS_EL_CIERRE_J9, calendario=_calendario(),
                            clasificacion=CLASIFICACION_DE_LA_CACHE)
            assert len(calculos) == 3, calculos
        finally:
            once_cal.los_factores = original


def test_la_memoria_del_once_no_se_queda_vieja():
    """
    La memoria de `el_once_se_busca_una_vez` recuerda por el CONTENIDO
    de los jugadores. El multiplicador va dentro: con otro factor la
    entrada es otra y se busca otra vez.
    """
    from src.analysis import el_once_se_busca_una_vez as una_vez

    antes = os.environ.get(una_vez.ENV)
    os.environ[una_vez.ENV] = "1"
    try:
        una_vez.olvidar()
        hueco = {4: 1}
        with _Interruptor(False):
            apagado = prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO)
        with _Interruptor(True):
            j9 = prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO, **DATOS)
            j10 = prepare_players(_foto(), INTELIGENCIA_VACIA, TABLERO, con_calendario=True,
                                  ahora=TRAS_EL_CIERRE_J9, calendario=_calendario(),
                                  clasificacion=CLASIFICACION)
        for jugadores in (apagado, j9, j10):
            una_vez.buscar(jugadores, hueco, False, search_best_lineup_for_formation)
        assert una_vez.cuenta()["fallos"] == 3 and una_vez.cuenta()["aciertos"] == 0
        # La misma entrada otra vez: esa si se recuerda.
        una_vez.buscar(j9, hueco, False, search_best_lineup_for_formation)
        assert una_vez.cuenta()["aciertos"] == 1
    finally:
        una_vez.olvidar()
        if antes is None:
            os.environ.pop(una_vez.ENV, None)
        else:
            os.environ[una_vez.ENV] = antes


# ============================================================
# 8. LA VARA NEGATIVA, EL RIVAL CARO, EL NOMBRE SIN CASAR, LA
#    MEMORIA POR CATALOGO Y LA CLASIFICACION CADUCADA
# ============================================================

def _defensa_en_negativo(pid, nombre, equipo):
    """Un defensa con puntos negativos y sin temporada pasada: su vara
    sale por debajo de cero (`calidad_para_la_vara`)."""
    return {**_jugador(pid, nombre, 2, equipo), "points": -10, "pointsLastSeason": 0}


def test_la_vara_negativa_no_mejora_con_un_partido_malo():
    """
    El caso del revisor: dos defensas con la misma vara NEGATIVA. El
    del Villarreal juega en casa contra el Elche (x1,102); el del
    Sevilla, en el Bernabeu (x0,846). Multiplicar sin mas acercaba a
    cero al del Sevilla y lo subia por encima del otro. Ahora el
    partido malo hunde y el bueno acerca a cero.
    """
    casa = _defensa_en_negativo(9101, "Defensa del Villarreal", 19)
    fuera = _defensa_en_negativo(9102, "Defensa del Sevilla", 17)
    foto = {**_foto(), "my_team": [dict(casa), dict(fuera)]}
    tablero = {"players": TABLERO["players"] + [_fila(9101, 70.0), _fila(9102, 70.0)]}

    with _Interruptor(False):
        apagado = {p["name"]: p for p in prepare_players(foto, INTELIGENCIA_VACIA, tablero)}
    with _Interruptor(True):
        puesto = {p["name"]: p for p in prepare_players(foto, INTELIGENCIA_VACIA, tablero, **DATOS)}

    vara = apagado["Defensa del Villarreal"]["weekly_expected_value"]
    assert vara < 0 and vara == apagado["Defensa del Sevilla"]["weekly_expected_value"], vara
    # Apagado solo los separa el +5 de casa.
    assert apagado["Defensa del Villarreal"]["lineup_score"] - apagado["Defensa del Sevilla"]["lineup_score"] == 5.0

    for nombre, mult, cinco in (("Defensa del Villarreal", 1.06 * 1.04, 5.0),
                                ("Defensa del Sevilla", 0.94 * 0.90, 0.0)):
        ficha = puesto[nombre]
        assert _cerca(ficha["fixture_multiplier"], mult), (nombre, ficha["fixture_multiplier"])
        esperado = apagado[nombre]["lineup_score"] - cinco + abs(vara) * (mult - 1.0) * ESCALA_DE_LA_VARA
        assert _cerca(ficha["lineup_score"], esperado, 1e-4), (nombre, ficha["lineup_score"], esperado)

    # El partido bueno sube, el malo baja, y el orden NO se invierte.
    assert puesto["Defensa del Villarreal"]["lineup_score"] > apagado["Defensa del Villarreal"]["lineup_score"] - 5.0
    assert puesto["Defensa del Sevilla"]["lineup_score"] < apagado["Defensa del Sevilla"]["lineup_score"]
    assert puesto["Defensa del Villarreal"]["lineup_score"] > puesto["Defensa del Sevilla"]["lineup_score"]

    # La pura: positiva multiplica, negativa se mueve con el partido.
    assert once_cal.vara_del_once(0.5, 0.846) == 0.5 * 0.846
    assert _cerca(once_cal.vara_del_once(-0.1, 0.846), -0.1154)
    assert _cerca(once_cal.vara_del_once(-0.1, 1.1024), -0.08976)
    assert once_cal.vara_del_once(0.0, 0.846) == 0.0


def _calendario_j9(*partidos):
    """Una J9 a medida (ventana del 16 al 19/10) y la J10 de siempre."""
    calendario = _calendario()
    for jornada in calendario["matchdays"]:
        if jornada["matchday"] == 9:
            jornada["matches"] = [
                _p(9, casa, fuera, hora) for casa, fuera, hora in partidos
            ]
            jornada["first_kickoff"] = min(m["kickoff"] for m in jornada["matches"])
    return calendario


def _foto_con_valores(caros):
    """La foto con catalogo completo y el valor de plantilla a mano."""
    foto = _foto(True)
    for ident in NOMBRES_DE_BIWENGER:
        foto["catalog"]["data"]["players"][str(80_000 + ident)]["price"] = caros.get(ident, 30_000_000)
    return foto


# El Valencia (19.º por puntos) con la plantilla mas cara de la liga:
# duro SOLO por valor.
CAROS_CON_VALENCIA = {18: 300_000_000, 3: 165_800_000, 15: 133_400_000, 2: 94_400_000}
CAROS_DE_VERDAD = {3: 165_800_000, 15: 133_400_000, 2: 94_400_000, 87: 78_200_000}

J9_CONTRA_EL_VALENCIA = (
    ("Villarreal CF", "Valencia CF", "2026-10-17T16:15:00+02:00"),
    ("Real Madrid", "Sevilla FC", "2026-10-18T21:00:00+02:00"),
    ("Real Betis", "FC Barcelona", "2026-10-17T18:30:00+02:00"),
)


def test_un_duro_solo_por_valor_es_duro():
    """
    El top-4 por valor de plantilla entra en los duros aunque no este
    en el top-6 por puntos. Por el camino de la vuelta: el catalogo de
    la foto -> `valores_del_catalogo` -> `los_duros`.
    """
    calendario = _calendario_j9(*J9_CONTRA_EL_VALENCIA)
    with _Interruptor(True):
        caro = _preparar(_foto_con_valores(CAROS_CON_VALENCIA), con_calendario=True, ahora=AHORA,
                         calendario=calendario, clasificacion=CLASIFICACION)
        normal = _preparar(_foto_con_valores(CAROS_DE_VERDAD), con_calendario=True, ahora=AHORA,
                           calendario=calendario, clasificacion=CLASIFICACION)
    assert _cerca(caro["Delantero del Villarreal"]["fixture_multiplier"], 1.06 * 0.90), caro["Delantero del Villarreal"]["fixture_reason"]
    assert "vs Valencia CF (duro)" in caro["Delantero del Villarreal"]["fixture_reason"]
    assert _cerca(normal["Delantero del Villarreal"]["fixture_multiplier"], 1.06 * 1.04)
    assert "vs Valencia CF (resto)" in normal["Delantero del Villarreal"]["fixture_reason"]

    factores = los_factores(calendario, CLASIFICACION, AHORA,
                            valores=valores_del_catalogo(_foto_con_valores(CAROS_CON_VALENCIA)))
    assert 18 in factores["duros"] and 18 not in los_factores(calendario, CLASIFICACION, AHORA)["duros"]


def test_un_nombre_sin_casar_en_la_ronda_deja_neutro_al_que_no_sale():
    """
    Si un nombre del calendario de ESTA ronda no casa con nadie, no se
    puede decir de ningun equipo ausente que «no juega»: podria ser el.
    Ese jugador se queda EXACTAMENTE como hoy (con su +5).
    """
    calendario = _calendario_j9(
        ("Equipo Fantasma", "Real Sociedad", "2026-10-17T14:00:00+02:00"),
        ("Real Madrid", "Sevilla FC", "2026-10-18T21:00:00+02:00"),
        ("Real Betis", "FC Barcelona", "2026-10-17T18:30:00+02:00"),
    )
    factores = los_factores(calendario, CLASIFICACION, AHORA)
    assert factores["available"] and factores["sin_casar"] == ["Equipo Fantasma"]
    assert factores["ronda_completa"] is False
    villarreal = para_el_jugador(factores, 19, 4)
    assert villarreal["con_calendario"] is False and villarreal["multiplicador"] == 1.0
    assert "sin casar" in villarreal["motivo"]
    # Los que si salen, con su partido.
    assert _cerca(para_el_jugador(factores, 17, 4)["multiplicador"], 0.94 * 0.90)

    with _Interruptor(True):
        fichas = _preparar(con_calendario=True, ahora=AHORA, calendario=calendario,
                           clasificacion=CLASIFICACION)
    for nombre in ("Delantero del Villarreal", "Portero del Villarreal", "Medio del Athletic"):
        assert fichas[nombre]["fixture_multiplier"] == 1.0, nombre
        assert fichas[nombre]["lineup_score"] == SCORES_DE_MAIN[nombre], (nombre, fichas[nombre]["lineup_score"])
    assert fichas["Delantero del Villarreal"]["home_away_adjustment"] == 5.0


def test_la_memoria_de_la_vuelta_distingue_catalogos():
    """
    Mismo calendario, misma clasificacion, misma hora; otro catalogo
    (otro valor de plantilla): otra respuesta, no la recordada.
    """
    calendario = _calendario_j9(*J9_CONTRA_EL_VALENCIA)
    with _Interruptor(True):
        normal = del_ciclo(_foto_con_valores(CAROS_DE_VERDAD), ahora=AHORA,
                           calendario=calendario, clasificacion=CLASIFICACION)
        caro = del_ciclo(_foto_con_valores(CAROS_CON_VALENCIA), ahora=AHORA,
                         calendario=calendario, clasificacion=CLASIFICACION)
        assert once_cal.cuenta()["calculos"] == 2 and once_cal.cuenta()["aciertos"] == 0
        # El mismo catalogo otra vez: ese si se recuerda.
        otra_vez = del_ciclo(_foto_con_valores(CAROS_CON_VALENCIA), ahora=AHORA,
                             calendario=calendario, clasificacion=CLASIFICACION)
        assert once_cal.cuenta()["aciertos"] == 1
    assert 18 not in normal["duros"]
    assert 18 in caro["duros"] and otra_vez["duros"] == caro["duros"]


def _con_fecha(segundos_antes, campo="fetched_at_unix"):
    """La cache del panel bajada `segundos_antes` de AHORA."""
    from datetime import datetime

    bajada = datetime.fromisoformat(AHORA).timestamp() - segundos_antes
    valor = int(bajada) if campo == "fetched_at_unix" else (
        datetime.fromtimestamp(bajada, tz=datetime.fromisoformat(AHORA).tzinfo).isoformat()
    )
    return {**CLASIFICACION_DE_LA_CACHE, campo: valor}


DIA = 24 * 3600


def test_una_clasificacion_de_hace_mas_de_una_semana_no_decide():
    foto = _foto(True)
    with _Interruptor(True):
        fresca = _preparar(foto, con_calendario=True, ahora=AHORA, calendario=_calendario(),
                           clasificacion=_con_fecha(6 * DIA))
        for campo in ("fetched_at_unix", "fetched_at"):
            vieja = _preparar(foto, con_calendario=True, ahora=AHORA, calendario=_calendario(),
                              clasificacion=_con_fecha(8 * DIA, campo))
            for nombre in SCORES_DE_MAIN:
                assert vieja[nombre]["fixture_multiplier"] == 1.0, (campo, nombre)
                assert "caducada" in vieja[nombre]["fixture_reason"], (campo, vieja[nombre]["fixture_reason"])
                # Neutro es el de hoy, +5 incluido.
                assert vieja[nombre]["lineup_score"] == SCORES_DE_MAIN[nombre], (campo, nombre)
    assert _cerca(fresca["Delantero del Villarreal"]["fixture_multiplier"], 1.06 * 1.04)

    # La misma tabla, la misma ronda, dos horas despues: deja de valer.
    # La memoria de la vuelta no puede servir la respuesta de antes.
    casi = _con_fecha(7 * DIA - 3600)
    with _Interruptor(True):
        antes = del_ciclo(foto, ahora=AHORA, calendario=_calendario(), clasificacion=casi)
        despues = del_ciclo(foto, ahora="2026-10-12T16:09:00+02:00", calendario=_calendario(),
                            clasificacion=casi)
    assert antes["available"] is True
    assert despues["available"] is False and "caducada" in despues["reason"], despues["reason"]

    # Sin fecha (una lista, o la cache sin sello) no se puede decir: vale.
    assert once_cal.caducada(CLASIFICACION, AHORA) is False
    assert once_cal.caducada(CLASIFICACION_DE_LA_CACHE, AHORA) is False
    for basura in (None, 7, "x", {"fetched_at_unix": "x"}, {"fetched_at": 3}):
        assert once_cal.caducada(basura, AHORA) is False
        assert once_cal.caducada(_con_fecha(8 * DIA), basura) is False


# ============================================================
# 9. EL CAMINO DE PRODUCCION: el disco y el reloj (suplantados)
# ============================================================

class _Produccion:
    """
    Lo que la vuelta lee sola, en una carpeta temporal: el calendario
    y la cache de la clasificacion del panel, el reloj, y el tablero
    de FF y la inteligencia del once que `build_lineup` pide por su
    cuenta. Nada de `data/`. Todo vuelve a su sitio al salir.
    """

    def __init__(self, calendario=None, clasificacion=None, ahora=AHORA, tablero=None):
        self.calendario = _calendario() if calendario is None else calendario
        self.clasificacion = (
            {**CLASIFICACION_DE_LA_CACHE,
             "fetched_at_unix": int(once_cal._momento(ahora).timestamp()) - 3600}
            if clasificacion is None else clasificacion
        )
        self.ahora = ahora
        self.tablero = TABLERO if tablero is None else tablero

    def escribir(self, ruta, contenido):
        import json

        Path(ruta).write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")

    def __enter__(self):
        import tempfile

        from src.analysis import lineup_engine

        self._carpeta = tempfile.TemporaryDirectory()
        raiz = Path(self._carpeta.name)
        self.ruta_calendario = raiz / "laliga_calendar.json"
        self.ruta_clasificacion = raiz / "laliga_standings.json"
        self.escribir(self.ruta_calendario, self.calendario)
        self.escribir(self.ruta_clasificacion, self.clasificacion)

        momento = once_cal._momento(self.ahora)
        self._antes = (
            once_cal.CALENDARIO, once_cal.CLASIFICACION, once_cal._reloj,
            lineup_engine.build_starter_intelligence_for_snapshot,
            lineup_engine.build_lineup_intelligence,
        )
        once_cal.CALENDARIO = self.ruta_calendario
        once_cal.CLASIFICACION = self.ruta_clasificacion
        once_cal._reloj = lambda: momento
        tablero = self.tablero
        lineup_engine.build_starter_intelligence_for_snapshot = lambda snapshot: tablero
        lineup_engine.build_lineup_intelligence = lambda snapshot: INTELIGENCIA_VACIA
        once_cal.olvidar()
        return self

    def __exit__(self, *_):
        from src.analysis import lineup_engine

        (once_cal.CALENDARIO, once_cal.CLASIFICACION, once_cal._reloj,
         lineup_engine.build_starter_intelligence_for_snapshot,
         lineup_engine.build_lineup_intelligence) = self._antes
        once_cal.olvidar()
        self._carpeta.cleanup()
        return False


def test_el_disco_se_lee_una_vez_por_version():
    foto = _foto(True)
    with _Interruptor(True), _Produccion() as prod:
        primera = del_ciclo(foto)
        segunda = del_ciclo(foto)
        assert primera["available"] is True, primera["reason"]
        assert primera["ronda"]["label"] == "Jornada 9"
        assert segunda is primera
        assert once_cal.cuenta()["calculos"] == 1 and once_cal.cuenta()["aciertos"] == 1
        assert set(once_cal._DISCO) == {str(prod.ruta_calendario), str(prod.ruta_clasificacion)}

        # Sin `ahora` y sin datos: el reloj y los ficheros, y la misma
        # respuesta que inyectandolos.
        inyectado = los_factores(prod.calendario, prod.clasificacion, AHORA,
                                 equipos_del_catalogo(foto), valores_del_catalogo(foto))
        assert primera["equipos"] == inyectado["equipos"] and primera["duros"] == inyectado["duros"]

        # Otra version de la clasificacion (otra vuelta): se relee y
        # se recalcula.
        otra = {**prod.clasificacion, "standings": prod.clasificacion["standings"][:-1]}
        prod.escribir(prod.ruta_clasificacion, otra)
        del_ciclo(foto)
        assert once_cal.cuenta()["calculos"] == 2

        # Una clasificacion caducada en el disco: neutro.
        prod.escribir(prod.ruta_clasificacion, {**otra, "fetched_at_unix": 1})
        assert "caducada" in del_ciclo(foto)["reason"]

        # Sin calendario en el disco: neutro, nunca lanza.
        prod.ruta_calendario.unlink()
        assert del_ciclo(foto)["available"] is False


# EL BANCO DEL ONCE ENTERO: un portero y cuatro delanteros para tres
# huecos. Los dos del Athletic (no juega la J9) entran siempre; el
# tercero lo deciden el del Sevilla (diez millones mas caro) y el del
# Villarreal.
DEL_ATHLETIC_1 = {**_jugador(9011, "Delantero del Athletic 1", 4, 1), "points": 80}
DEL_ATHLETIC_2 = {**_jugador(9012, "Delantero del Athletic 2", 4, 1), "points": 80}
DEL_SEVILLA_CARO = {**DEL_FUERA, "price": DEL_FUERA["price"] + 10_000_000}

TABLERO_DEL_ONCE = {"players": TABLERO["players"] + [_fila(9011, 95.0), _fila(9012, 95.0)]}


def _foto_del_once():
    return {**_foto(), "my_team": [dict(j) for j in (
        PORTERO, DEL_ATHLETIC_1, DEL_ATHLETIC_2, DEL_SEVILLA_CARO, DEL_CASA)]}


def _nombres(once) -> list:
    return sorted(p["name"] for p in once["selected"])


EL_ONCE_DE_SIEMPRE = sorted(["Portero del Villarreal", "Delantero del Athletic 1",
                             "Delantero del Athletic 2", "Delantero del Sevilla"])
EL_ONCE_CON_CALENDARIO = sorted(["Portero del Villarreal", "Delantero del Athletic 1",
                                 "Delantero del Athletic 2", "Delantero del Villarreal"])


def test_solo_el_once_que_se_escribe_mira_el_calendario():
    """
    El HALLAZGO GORDO del revisor. Con el interruptor puesto, el once
    que VALORA (venta, liquidez, deuda segura, fichajes, orden de
    venta: `build_lineup(foto)` y `prepare_players(foto)` a secas) es
    el de apagado, byte a byte, `lineup_score` incluido. Solo el que
    pide `con_calendario` -el de `lineup_monitor`- ordena por el
    partido, y lo cuenta en su salida.
    """
    from src.analysis.lineup_engine import build_lineup

    with _Produccion(tablero=TABLERO_DEL_ONCE):
        with _Interruptor(False):
            valora_apagado = build_lineup(_foto_del_once())
            escribe_apagado = build_lineup(_foto_del_once(), con_calendario=True)
            fichas_apagado = prepare_players(_foto_del_once(), INTELIGENCIA_VACIA, TABLERO_DEL_ONCE)
        with _Interruptor(True):
            valora = build_lineup(_foto_del_once())
            fichas = prepare_players(_foto_del_once(), INTELIGENCIA_VACIA, TABLERO_DEL_ONCE)
            escribe = build_lineup(_foto_del_once(), con_calendario=True)

    # Apagado, pedirlo o no da lo mismo.
    assert _nombres(valora_apagado) == _nombres(escribe_apagado) == EL_ONCE_DE_SIEMPRE
    assert _huella(escribe_apagado) == _huella(valora_apagado)

    # Puesto, el que valora es el de siempre.
    assert _nombres(valora) == EL_ONCE_DE_SIEMPRE
    assert valora["lineup_score"] == valora_apagado["lineup_score"]
    assert "fixture_multipliers" not in valora
    for p in valora["selected"] + fichas:
        assert "fixture_multiplier" not in p, p["name"]
    for fila in valora["bench"]:
        assert "fixture_multiplier" not in fila, fila["name"]
    assert _huella(fichas) == _huella(fichas_apagado)
    assert _huella(valora) == _huella(valora_apagado)

    # Y el que se escribe, por el partido.
    assert _nombres(escribe) == EL_ONCE_CON_CALENDARIO
    elegido = next(p for p in escribe["selected"] if p["name"] == "Delantero del Villarreal")
    assert _cerca(elegido["fixture_multiplier"], 1.06 * 1.04)
    assert escribe["lineup_score"] != valora["lineup_score"]

    # LO CUENTA: en cada ficha, en el banquillo y en un bloque propio.
    banco = {f["name"]: f for f in escribe["bench"]}
    sevilla = banco["Delantero del Sevilla"]
    assert sevilla["reason"] == "PUNTUA_MENOS"
    assert _cerca(sevilla["fixture_multiplier"], 0.94 * 0.90)
    assert "fuera vs Real Madrid (duro)" in sevilla["fixture_reason"]
    assert sevilla["compared_to_fixture_multiplier"] is not None
    partidos = {f["name"]: f for f in escribe["fixture_multipliers"]}
    assert set(partidos) == {p["name"] for p in _foto_del_once()["my_team"]}
    assert partidos["Delantero del Villarreal"]["in_lineup"] is True
    assert partidos["Delantero del Sevilla"]["in_lineup"] is False
    assert _cerca(partidos["Delantero del Sevilla"]["fixture_multiplier"], 0.94 * 0.90)
    assert "Jornada 9" in partidos["Delantero del Villarreal"]["fixture_reason"]


def test_la_memoria_del_once_distingue_al_que_valora_del_que_escribe():
    """
    Con `el_once_se_busca_una_vez` puesto, el once que se escribe y el
    que valora no se pisan en la memoria, en ningun orden: la entrada
    del que escribe lleva el partido dentro y es otra.
    """
    from src.analysis import el_once_se_busca_una_vez as una_vez
    from src.analysis.lineup_engine import build_lineup

    antes = os.environ.get(una_vez.ENV)
    os.environ[una_vez.ENV] = "1"
    try:
        with _Produccion(tablero=TABLERO_DEL_ONCE), _Interruptor(True):
            for orden in ((True, False), (False, True)):
                una_vez.olvidar()
                salidas = {flag: build_lineup(_foto_del_once(), con_calendario=flag) for flag in orden}
                assert _nombres(salidas[True]) == EL_ONCE_CON_CALENDARIO, orden
                assert _nombres(salidas[False]) == EL_ONCE_DE_SIEMPRE, orden
                assert una_vez.cuenta()["fallos"] >= 2, (orden, una_vez.cuenta())
                # La misma pregunta otra vez: recordada, y la misma.
                fallos = una_vez.cuenta()["fallos"]
                assert _nombres(build_lineup(_foto_del_once())) == EL_ONCE_DE_SIEMPRE
                assert una_vez.cuenta()["fallos"] == fallos and una_vez.cuenta()["aciertos"] > 0
    finally:
        una_vez.olvidar()
        if antes is None:
            os.environ.pop(una_vez.ENV, None)
        else:
            os.environ[una_vez.ENV] = antes


def test_el_monitor_pide_el_calendario_solo_con_el_interruptor():
    """
    `build_lineup_monitor_state` -el once que lleva SAVE_LINEUP- es el
    unico que pide `con_calendario`, y solo con el interruptor puesto.
    """
    from src.analysis import lineup_engine, lineup_monitor

    pedidos = []

    def _espia(snapshot, *args, **kwargs):
        pedidos.append(kwargs.get("con_calendario"))
        return lineup_engine.build_lineup(snapshot, *args, **kwargs)

    original_build = lineup_monitor.build_lineup
    original_estado = lineup_monitor.load_lineup_monitor_state
    lineup_monitor.build_lineup = _espia
    lineup_monitor.load_lineup_monitor_state = lambda: None
    try:
        with _Produccion(tablero=TABLERO_DEL_ONCE):
            with _Interruptor(False):
                apagado = lineup_monitor.build_lineup_monitor_state(_foto_del_once(), persist=False)
            with _Interruptor(True):
                puesto = lineup_monitor.build_lineup_monitor_state(_foto_del_once(), persist=False)
    finally:
        lineup_monitor.build_lineup = original_build
        lineup_monitor.load_lineup_monitor_state = original_estado

    assert pedidos == [False, True], pedidos
    assert _nombres(apagado["lineup"]) == EL_ONCE_DE_SIEMPRE
    assert "fixture_multipliers" not in apagado["lineup"]
    assert _nombres(puesto["lineup"]) == EL_ONCE_CON_CALENDARIO
    assert puesto["lineup"]["fixture_multipliers"]


TESTS = [
    test_apagado_el_once_es_el_de_hoy,
    test_apagado_ni_se_mira_el_calendario,
    test_puesto_el_de_casa_contra_el_resto_pasa_por_delante,
    test_la_busqueda_del_once_lo_pone_a_el,
    test_el_que_no_juega_sale_neutro,
    test_un_partido_repetido_cuenta_una_vez,
    test_el_mas_cinco_no_se_cuenta_dos_veces_y_el_dios_sigue,
    test_la_cache_del_panel_sin_ids_casa_con_el_catalogo,
    test_una_fila_sin_casar_no_cambia_los_duros,
    test_basura_y_falta_de_datos_dan_el_once_de_hoy,
    test_nunca_lanza,
    test_una_vez_por_vuelta,
    test_la_memoria_del_once_no_se_queda_vieja,
    test_la_vara_negativa_no_mejora_con_un_partido_malo,
    test_un_duro_solo_por_valor_es_duro,
    test_un_nombre_sin_casar_en_la_ronda_deja_neutro_al_que_no_sale,
    test_la_memoria_de_la_vuelta_distingue_catalogos,
    test_una_clasificacion_de_hace_mas_de_una_semana_no_decide,
    test_el_disco_se_lee_una_vez_por_version,
    test_solo_el_once_que_se_escribe_mira_el_calendario,
    test_la_memoria_del_once_distingue_al_que_valora_del_que_escribe,
    test_el_monitor_pide_el_calendario_solo_con_el_interruptor,
]


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
