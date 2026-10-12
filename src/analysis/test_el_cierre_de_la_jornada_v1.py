"""
EL CIERRE DE LA JORNADA (12/10/2026). Guardias de
`src/actions/el_cierre_de_la_jornada.py`.

Todo con datos de mentira: una liga de 10 equipos, un calendario de
tres jornadas (J9 el viernes 16/10 a las 21:00 de Madrid, como la de
verdad) y una plantilla de 16. La hora se pasa siempre (`AHORA`, el
miercoles 14/10 a las 20:07 de Madrid: a 48,9 h del partido). No se lee
`data/`, ni la foto, ni el reloj, ni se sale a la red: el escritor es de
mentira y el plan se escribe en una carpeta temporal.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.el_cierre_de_la_jornada import (     # noqa: E402
    ENV, a_quien_vender, correr, decidir, el_mejor_once, el_parte, la_caja,
    la_ventana, las_fichas, las_pujas_vivas, lo_de_esta_vuelta, por_que_no,
)
from src.analysis.el_calendario_de_puntos import contexto   # noqa: E402


AHORA = datetime(2026, 10, 14, 18, 7, tzinfo=timezone.utc)      # mié 20:07 Madrid

# La tabla: 1-6 son duros (puntos por partido). Las estrellas de 1-4
# hacen que el top-4 por valor de plantilla sean esos mismos.
TABLA = [
    {"rank": i, "team": f"Equipo {i}", "biwenger_team_id": i, "played": 8,
     "points": p, "goals_for": 10, "goals_against": 10}
    for i, p in zip(range(1, 11), [24, 21, 18, 16, 15, 14, 10, 8, 6, 4])
]
ESTRELLAS = [{"id": 900 + i, "team_id": i, "price": 100_000_000, "position": 4}
             for i in range(1, 5)]


def _p(j, casa, fuera, cuando):
    return {"matchday": j, "home": f"Equipo {casa}", "away": f"Equipo {fuera}",
            "kickoff": cuando}


CAL = {"matchdays": [
    {"matchday": 9, "matches": [
        _p(9, 7, 1, "2026-10-16T21:00:00+02:00"),     # el 7 en casa contra un duro
        _p(9, 8, 9, "2026-10-17T16:00:00+02:00"),     # el 8 en casa, el 9 fuera, contra el resto
        _p(9, 2, 10, "2026-10-17T18:30:00+02:00"),    # el 10 fuera contra un duro
        _p(9, 3, 4, "2026-10-18T14:00:00+02:00"),
        _p(9, 5, 6, "2026-10-19T21:00:00+02:00"),
    ]},
    {"matchday": 10, "matches": [
        _p(10, 7, 8, "2026-10-23T21:00:00+02:00"),
        _p(10, 9, 10, "2026-10-24T16:00:00+02:00"),
        _p(10, 1, 2, "2026-10-24T18:30:00+02:00"),
        _p(10, 3, 4, "2026-10-25T14:00:00+01:00"),
        _p(10, 5, 6, "2026-10-26T21:00:00+01:00"),
    ]},
    {"matchday": 11, "matches": [
        _p(11, 10, 7, "2026-10-30T21:00:00+01:00"),
        _p(11, 1, 8, "2026-10-31T16:00:00+01:00"),
        _p(11, 2, 9, "2026-10-31T18:30:00+01:00"),
        _p(11, 3, 4, "2026-11-01T14:00:00+01:00"),
        _p(11, 5, 6, "2026-11-02T21:00:00+01:00"),
    ]},
]}


def _j(pid, nombre, pos, equipo, tasa, prob, precio, status="ok"):
    return {"id": pid, "name": nombre, "position": pos, "team_id": equipo,
            "points": int(tasa * 30), "played": 30, "starter_probability": prob,
            "price": precio, "status": status}


# La plantilla. Once esperado (3-4-3): P1; D1-D3; M1-M4; Yamal, F1, F3.
PLANTILLA = [
    _j(1, "P1", 1, 7, 5, 90, 2_000_000),
    _j(2, "D1", 2, 7, 5, 80, 2_000_000),
    _j(3, "D2", 2, 8, 5, 80, 2_000_000),
    _j(4, "D3", 2, 9, 5, 80, 2_000_000),
    _j(5, "M1", 3, 7, 5, 80, 2_000_000),
    _j(6, "M2", 3, 8, 5, 80, 2_000_000),
    _j(7, "M3", 3, 9, 5, 80, 2_000_000),
    _j(8, "M4", 3, 10, 5, 80, 2_000_000),
    _j(9, "Yamal", 4, 10, 2, 10, 25_000_000),         # el peor xP de los delanteros
    _j(10, "F1", 4, 8, 5, 70, 3_000_000),             # en casa contra el resto: 1,10
    _j(11, "F2", 4, 10, 5, 70, 3_000_000),            # fuera contra un duro: 0,85
    _j(12, "F3", 4, 9, 5, 70, 3_000_000),             # fuera contra el resto: 0,98
    _j(13, "B1", 3, 9, 3, 20, 4_000_000),             # el que menos puntos por euro
    _j(14, "B2", 3, 7, 4, 30, 1_000_000),
    _j(15, "B3", 2, 8, 3, 10, 500_000),
    _j(16, "Lesionado", 3, 7, 9, 90, 6_000_000, status="injured"),
]
ONCE = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12}
BANQUILLO = {11, 13, 14, 15, 16}

STATUS = {"league_center": {"laliga": {"standings": TABLA}},
          "todaLaLiga": {"players": ESTRELLAS + [
              {k: v for k, v in p.items() if k != "starter_probability"} for p in PLANTILLA]}}


def _ctx(ahora=AHORA):
    return contexto(STATUS, CAL, ahora, 3)


def _d(**k):
    base = dict(plantilla=PLANTILLA, ctx=_ctx(), horas=48.9, saldo=1_000_000,
                pujas={500: {"offer_id": 9, "amount": 5_000_000}},
                intocables={"yamal"}, protegidos={9})
    base.update(k)
    return decidir(**base)


def _acciones(d, accion=None):
    return [(a["accion"], a["player_id"]) for a in d["acciones"]
            if accion is None or a["accion"] == accion]


def _cobro(pid):
    return int(next(p["price"] for p in PLANTILLA if p["id"] == pid) * 0.95)


# ------------------------------------------------------------------
# 1. CUANDO
# ------------------------------------------------------------------

def test_solo_dentro_de_la_ventana():
    # Fuera de las 64 h, sin calendario, con la ronda jugándose o en la
    # zona de silencio: ni una escritura, aunque la caja esté en rojo.
    for k, motivo in ((dict(horas=70), "FUERA_DE_LA_VENTANA"),
                      (dict(horas=None), "SIN_CALENDARIO"),
                      (dict(en_curso=True), "JORNADA_EN_CURSO"),
                      (dict(puede_escribir=False), "ZONA_DE_SILENCIO")):
        d = _d(saldo=-20_000_000, **k)
        assert not d["activo"] and d["acciones"] == [] and d["motivo"] == motivo, (k, d)
    assert por_que_no(64, False, True) is None
    assert por_que_no(64.01, False, True) == "FUERA_DE_LA_VENTANA"


def test_la_ventana_sale_del_calendario():
    v = la_ventana(AHORA, CAL)
    assert abs(v["horas"] - 48.883) < 0.01 and not v["en_curso"] and v["puede_escribir"], v
    # Sábado 17/10 a mediodía: la J9 se está jugando.
    v = la_ventana(datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc), CAL)
    assert v["en_curso"] and por_que_no(**v) == "JORNADA_EN_CURSO", v
    # Martes 13/10 a las 05:30 de Madrid: zona de silencio.
    v = la_ventana(datetime(2026, 10, 13, 3, 30, tzinfo=timezone.utc), CAL)
    assert not v["puede_escribir"] and por_que_no(**v) == "ZONA_DE_SILENCIO", v
    # Lunes 12/10 a las 12:07: a 105 h, fuera de la ventana.
    v = la_ventana(datetime(2026, 10, 12, 10, 7, tzinfo=timezone.utc), CAL)
    assert v["horas"] > 64 and por_que_no(**v) == "FUERA_DE_LA_VENTANA", v
    # Viernes a las 07:15, la primera vuelta que cobra: dentro, a 13,75 h.
    v = la_ventana(datetime(2026, 10, 16, 5, 15, tzinfo=timezone.utc), CAL)
    assert abs(v["horas"] - 13.75) < 0.01 and por_que_no(**v) is None, v


# ------------------------------------------------------------------
# 2. EL ONCE
# ------------------------------------------------------------------

def test_el_once_mira_el_calendario_y_lleva_a_yamal():
    d = _d(saldo=10_000_000)
    once = d["once"]
    assert once["formacion"] == "3-4-3" and once["lleno"] == 11, once
    assert set(once["ids"]) == ONCE, once
    # F1, F2 y F3 tienen la misma tasa y titularidad: decide el partido.
    xp = {j["id"]: j["xp"] for j in once["jugadores"]}
    assert xp[10] > xp[12], xp                       # casa contra el resto > fuera contra el resto
    assert 11 not in once["ids"]                     # F2, fuera contra un duro, al banquillo
    # Yamal entra con el peor xP de los delanteros: es intocable.
    assert 9 in once["ids"] and xp[9] < xp[12]
    # Sin la regla, el once lo echaría.
    sin = el_mejor_once([{**p, "xp": xp.get(p["id"], 3.0)} for p in PLANTILLA
                         if p["status"] == "ok"], intocables=set())
    assert 9 not in sin["ids"], sin
    # El lesionado (el de más xP) no juega.
    assert 16 not in once["ids"]


def test_la_formacion_es_de_las_validas():
    from src.analysis.lineup_engine import FORMATIONS

    # Con 5 defensas sanos y 2 delanteros, el once cambia de dibujo.
    plantilla = [p for p in PLANTILLA if p["id"] not in (10, 11, 12)] + [
        _j(20, "D4", 2, 8, 6, 90, 2_000_000), _j(21, "D5", 2, 9, 6, 90, 2_000_000),
        _j(22, "F4", 4, 8, 5, 70, 3_000_000)]
    d = _d(plantilla=plantilla, saldo=10_000_000)
    assert d["once"]["formacion"] in FORMATIONS and d["once"]["lleno"] == 11, d["once"]
    puestos = {}
    por_id = {p["id"]: p for p in plantilla}
    for pid in d["once"]["ids"]:
        puestos[por_id[pid]["position"]] = puestos.get(por_id[pid]["position"], 0) + 1
    assert puestos == FORMATIONS[d["once"]["formacion"]], (puestos, d["once"])


# ------------------------------------------------------------------
# 3-5. LA CAJA Y LAS VENTAS
# ------------------------------------------------------------------

def test_en_positivo_solo_publica_el_banquillo():
    # 10 M de saldo - 5 M de puja viva = +5 M: se publica a todo el que
    # no juega (salvo protegidos y lo ya publicado) y no se vende a nadie,
    # aunque haya una oferta buena.
    d = _d(saldo=10_000_000, protegidos={9, 15}, en_venta={14},
           ofertas={13: {"offer_id": 77, "amount": 4_000_000},
                    10: {"offer_id": 78, "amount": 9_000_000}})
    assert d["activo"] and d["motivo"] == "EN_POSITIVO" and d["caja"] == 5_000_000, d
    assert sorted(_acciones(d)) == [("PONER_A_LA_VENTA", 11), ("PONER_A_LA_VENTA", 13),
                                    ("PONER_A_LA_VENTA", 16)], d["acciones"]
    assert d["vender"] == [] and d["deficit"] == 0
    # A su valor.
    assert {a["player_id"]: a["precio"] for a in d["acciones"]}[13] == 4_000_000


def test_en_rojo_vende_lo_que_menos_puntos_pierde_por_euro():
    # 1 M - 5 M = -4 M. B1 (4 M, 1,85 puntos en 3 rondas) es el que menos
    # pierde por euro; con él no llega (3,8 M al 95 %) y entra B3 (el
    # siguiente). F2 vale más por euro y se queda.
    d = _d()
    assert d["caja"] == -4_000_000 and d["deficit"] == 4_000_000, d
    assert sorted(d["vender"]) == [13, 15] and d["falta"] == 0, d
    assert d["motivo"] == "EN_ROJO_SE_VENDE"
    tocados = {pid for _, pid in _acciones(d)}
    assert not tocados & ONCE, tocados              # nadie del once
    assert tocados <= BANQUILLO                     # y Yamal (protegido) tampoco
    # Sin ofertas, se publica a todos los candidatos.
    assert sorted(_acciones(d)) == [("PONER_A_LA_VENTA", p) for p in sorted(BANQUILLO)]
    # Protegido B1: se cubre con otros, y a B1 ni se le publica.
    d = _d(protegidos={9, 13})
    assert 13 not in d["vender"] and 13 not in {pid for _, pid in _acciones(d)}, d
    assert sum(_cobro(p) for p in d["vender"]) >= 4_000_000 and d["falta"] == 0, d
    # Lo que ya vende la orden o la mejora tampoco es candidato.
    d = _d(no_vender={13})
    assert 13 not in d["vender"] and 13 not in {pid for _, pid in _acciones(d)}, d


def test_si_ni_todo_el_banquillo_llega_falta():
    d = _d(saldo=0, pujas={500: {"offer_id": 9, "amount": 20_000_000}})
    todos = sum(_cobro(p) for p in BANQUILLO)
    assert sorted(d["vender"]) == sorted(BANQUILLO), d
    assert d["falta"] == 20_000_000 - todos and d["motivo"] == "FALTA", d
    assert not set(d["vender"]) & ONCE


def test_a_quien_vender():
    c = [{"id": 1, "cobro": 475_000, "quedarse": 0.1},
         {"id": 2, "cobro": 3_800_000, "quedarse": 1.8},
         {"id": 3, "cobro": 2_850_000, "quedarse": 10.0}]
    # El voraz coge 1 y 2; 1 sobra y se quita.
    assert [x["id"] for x in a_quien_vender(c, 3_000_000)[0]] == [2]
    assert [x["id"] for x in a_quien_vender(c, 4_000_000)[0]] == [1, 2]
    # Deficit pequeño: uno solo que cubre perdiendo menos.
    c2 = [{"id": 1, "cobro": 3_800_000, "quedarse": 1.85},
          {"id": 2, "cobro": 475_000, "quedarse": 0.92}]
    assert [x["id"] for x in a_quien_vender(c2, 200_000)[0]] == [2]
    elegidos, falta = a_quien_vender(c, 10_000_000)
    assert len(elegidos) == 3 and falta == 10_000_000 - 7_125_000
    assert a_quien_vender(c, 0) == ([], 0)


def test_la_caja_cuenta_las_pujas_enteras_y_la_vuelta():
    assert la_caja(1_000_000, {1: {"amount": 3_000_000}, 2: 500_000}, {7: 900_000}) == -1_600_000
    foto = {"plantilla": {1, 2}, "nuestras_pujas": {50: {"offer_id": 5, "amount": 1_000_000},
                                                    51: {"offer_id": 6, "amount": 2_000_000}}}
    v10 = {"orden_del_gestor": {"hechas": [
               {"accion": "PUJAR", "player_id": 50, "importe": 1_500_000, "exito": True},
               {"accion": "PUJAR", "player_id": 52, "importe": 700_000, "exito": False},
               {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 2, "importe": 900_000,
                "exito": True}]},
           "revision_de_pujas": {"retiradas": [{"player_id": 51, "offer_id": 6, "exito": True}]},
           "ronda": {"hechas": [{"accion": "PONER_A_LA_VENTA", "player_id": 1, "exito": True}]},
           "carril": {"bids": [{"player_id": 53, "amount": 300_000, "sent": True,
                                "success": True}]}}
    vuelta = lo_de_esta_vuelta(v10)
    assert vuelta["vendidos"] == {2: 900_000} and vuelta["listados"] == {1}, vuelta
    # La mejora pujó en esta vuelta por 54 (la foto no lo ve); 1 ya es nuestro.
    pujas = las_pujas_vivas(foto, vuelta, {"54": {"sale": 1, "puja": 400_000}, "1": {"sale": 2}})
    assert {k: v["amount"] for k, v in pujas.items()} == {50: 1_500_000, 53: 300_000, 54: 400_000}
    assert pujas[50]["offer_id"] is None             # la de esta vuelta no se sabe retirar


def test_retira_lo_especulativo_a_menos_de_40_horas():
    # La orden puja 1,2 M por 500; la ronda tiene 1,5 M vivos por 600 y
    # los chollos 0,4 M por 601. Caja: 1 - 3,1 = -2,1 M.
    pujas = {500: {"offer_id": 9, "amount": 1_200_000},
             600: {"offer_id": 61, "amount": 1_500_000},
             601: {"offer_id": 62, "amount": 400_000}}
    d = _d(horas=30, pujas=pujas, especulativas={600, 601})
    assert _acciones(d, "CANCELAR_PUJA") == [("CANCELAR_PUJA", 600), ("CANCELAR_PUJA", 601)], d
    assert d["acciones"][0]["offer_id"] == 61                    # la palanca barata, primero
    assert d["caja_tras_cancelar"] == -200_000 and d["deficit"] == 200_000, d
    assert d["vender"] == [15], d                                # B3 solo basta
    # Si con una basta, solo una.
    d = _d(horas=30, pujas={**pujas, 500: {"offer_id": 9, "amount": 500_000}},
           especulativas={600, 601})
    assert _acciones(d, "CANCELAR_PUJA") == [("CANCELAR_PUJA", 600)], d
    assert d["motivo"] == "EN_POSITIVO_RETIRANDO_PUJAS" and d["vender"] == [], d
    # A más de 40 h, o con la caja en positivo, no se retira nada; ni la
    # puja de la orden (no es especulativa) en ningún caso.
    assert _acciones(_d(horas=50, pujas=pujas, especulativas={600, 601}), "CANCELAR_PUJA") == []
    assert _acciones(_d(horas=30, saldo=10_000_000, pujas=pujas, especulativas={600, 601}),
                     "CANCELAR_PUJA") == []
    d = _d(horas=30, pujas=pujas, especulativas=set())
    assert _acciones(d, "CANCELAR_PUJA") == [] and d["deficit"] == 2_100_000


def test_solo_cobra_desde_el_90_por_ciento_salvo_a_menos_de_20_horas():
    ofertas = {13: {"offer_id": 77, "amount": 3_700_000},     # 92,5 % de 4 M
               15: {"offer_id": 78, "amount": 400_000},       # 80 % de 0,5 M
               10: {"offer_id": 79, "amount": 9_000_000},     # del once
               9: {"offer_id": 80, "amount": 30_000_000},     # Yamal
               11: {"offer_id": 81, "amount": 3_100_000}}     # F2, no elegido
    d = _d(ofertas=ofertas, en_venta={13, 15, 11})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [("ACEPTAR_OFERTA_DEL_COMPUTER", 13)], d
    assert [a for a in d["acciones"] if a["player_id"] == 15][0]["accion"] == "NADA"
    # A menos de 20 h y en rojo, la que haya; pero nunca del once ni de Yamal.
    d = _d(ofertas=ofertas, en_venta={13, 15, 11}, horas=15)
    assert sorted(_acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER")) == [
        ("ACEPTAR_OFERTA_DEL_COMPUTER", 13), ("ACEPTAR_OFERTA_DEL_COMPUTER", 15)], d
    # Una escritura por jugador.
    pids = [pid for _, pid in _acciones(d)]
    assert len(pids) == len(set(pids))
    # Lo vendido en esta vuelta ya no es plantilla.
    d = _d(ofertas=ofertas, vendidos={13: 3_700_000})
    assert 13 not in {pid for _, pid in _acciones(d)} and d["caja"] == -300_000, d


# ------------------------------------------------------------------
# EL PASO DEL WORKFLOW
# ------------------------------------------------------------------

class _Escritor:
    llamadas: list = []
    creados = 0

    def __init__(self):
        type(self).creados += 1

    def _ok(self, *a, **k):
        type(self).llamadas.append((a, k))
        return {"sent": True, "success": True, "http_status": 200}

    accept_offer = list_player_for_sale = cancel_bid = place_bid = _ok


def _entorno(**valores):
    """Pone los interruptores y devuelve cómo estaban."""
    antes = {k: os.environ.get(k) for k in valores}
    for k, v in valores.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return antes


def _el_status():
    roster = [{"id": p["id"], "name": p["name"], "position": p["position"],
               "team_name": f"Equipo {p['team_id']}", "price": p["price"],
               "points": p["points"], "played_home": 15, "played_away": 15,
               "starter_probability": p["starter_probability"], "status": p["status"]}
              for p in PLANTILLA]
    return {**STATUS, "roster": {"players": roster}, "libro_del_escaparate": {"players": []}}


def _la_foto():
    return {
        "league": {"user": {"id": 99}},
        "market": {
            "status": {"balance": 1_000_000, "maximumBid": 20_000_000},
            "sales": [],
            "offers": [
                {"id": 9, "status": "waiting", "amount": 5_000_000,
                 "requestedPlayers": [{"id": 500}], "from": {"id": 99}},
                {"id": 77, "status": "waiting", "amount": 3_700_000,
                 "requestedPlayers": [{"id": 13}], "from": None},
            ],
        },
        "my_team": [{"id": p["id"], "price": p["price"]} for p in PLANTILLA],
        "catalog": {"data": {"players": {str(p["id"]): {"status": p["status"]}
                                         for p in PLANTILLA}}},
    }


def test_apagado_no_lee_ni_escribe_nada():
    antes = _entorno(**{ENV: None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            plan = Path(carpeta) / "el_cierre.json"
            _Escritor.creados, _Escritor.llamadas = 0, []
            r = correr(status=_el_status(), snapshot=_la_foto(), v10={}, libros={},
                       calendario=CAL, orden_ruta=Path(carpeta) / "no_hay_orden.json",
                       escritor_factory=_Escritor, ahora=AHORA, plan_ruta=plan)
            assert r == {"activa": False, "motivo": "APAGADA", "acciones": [], "hechas": [],
                         "plan": None, "decision": None}, r
            assert _Escritor.creados == 0 and _Escritor.llamadas == [] and not plan.exists()
            # Y sin argumentos tampoco: vuelve antes de leer nada.
            assert correr()["motivo"] == "APAGADA"
    finally:
        _entorno(**antes)


def test_encendido_de_punta_a_punta():
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": "1"})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden = Path(carpeta) / "orden.json"
            orden.write_text(json.dumps({
                "caduca": "2026-11-30T23:59:00+01:00",
                "fichar": [{"player_id": 500, "nombre": "Fichaje", "puja": 5_000_000}],
                "proteger": [{"player_id": 9, "nombre": "Yamal"}],
                "vender_si_ficha": {"jugadores": [
                    {"player_id": 16, "nombre": "Lesionado", "suelo": 1, "si_esta": 500}]},
            }))
            plan = Path(carpeta) / "el_cierre.json"
            # En esta vuelta: la ronda pujó 0,3 M y la orden cobró a B2 (0,9 M).
            v10 = {"ronda": {"hechas": [{"accion": "PUJAR", "player_id": 700,
                                         "importe": 300_000, "exito": True}]},
                   "orden_del_gestor": {"hechas": [{"accion": "ACEPTAR_OFERTA_DEL_COMPUTER",
                                                    "player_id": 14, "importe": 900_000,
                                                    "exito": True}]}}
            _Escritor.creados, _Escritor.llamadas = 0, []
            r = correr(status=_el_status(), snapshot=_la_foto(), v10=v10,
                       libros={"ronda": {"700": 300_000}, "chollos": {}, "mejora": {}},
                       calendario=CAL, orden_ruta=orden, escritor_factory=_Escritor,
                       ahora=AHORA, plan_ruta=plan)
            d = r["decision"]
            # 1 M - 5 M - 0,3 M + 0,9 M = -3,4 M. B1 (3,8 M) basta y su
            # oferta (92,5 %) se cobra; F2 y B3 se publican. El lesionado
            # lo vende la orden y B2 ya se vendió: ni se tocan.
            assert d["caja"] == -3_400_000 and d["vender"] == [13], d
            assert sorted(_acciones(d)) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 13),
                                            ("PONER_A_LA_VENTA", 11),
                                            ("PONER_A_LA_VENTA", 15)], d["acciones"]
            assert len(r["hechas"]) == 3 and all(h["exito"] for h in r["hechas"]), r["hechas"]
            assert ((), {"offer_id": 77, "execute": True}) in _Escritor.llamadas
            publicado = json.loads(plan.read_text())
            assert publicado["activo"] and publicado["ronda"]["label"] == "Jornada 9", publicado
            assert publicado["vender"] == [13] and publicado["deficit"] == 3_400_000
            assert 9 in publicado["xi"] and len(publicado["xi"]) == 11
            assert publicado["generated_at"] == AHORA.isoformat()
            assert any("Jornada 9" in linea for linea in el_parte(r))

            # Fuera de la ventana: no escribe en Biwenger y el plan lo dice.
            _Escritor.creados = 0
            lunes = datetime(2026, 10, 12, 10, 7, tzinfo=timezone.utc)
            r = correr(status=_el_status(), snapshot=_la_foto(), v10={}, libros={},
                       calendario=CAL, orden_ruta=orden, escritor_factory=_Escritor,
                       ahora=lunes, plan_ruta=plan)
            assert r["motivo"] == "FUERA_DE_LA_VENTANA" and _Escritor.creados == 0, r
            assert json.loads(plan.read_text())["activo"] is False
    finally:
        _entorno(**antes)


def test_nunca_lanza_con_basura():
    for basura in (None, "x", 5, [1, 2], {"a": object()}):
        d = decidir(plantilla=basura, ctx=basura, horas=30, saldo=-1, pujas=basura,
                    vendidos=basura, ofertas=basura, en_venta=basura, especulativas=basura,
                    intocables=basura if basura is not None else (), protegidos=basura,
                    no_vender=basura, se_van=basura)
        assert isinstance(d, dict) and isinstance(d["acciones"], list), d
        decidir(plantilla=[{"id": "a"}, None, 5, {"id": 3, "price": "x"}], ctx={"rondas": "x"},
                horas="z", saldo=object())
        assert el_mejor_once(basura)["ids"] == [] or basura == [1, 2]
        a_quien_vender(basura, basura)
        la_caja(basura, basura, basura)
        lo_de_esta_vuelta(basura)
        las_pujas_vivas(basura, basura, basura)
        las_fichas(basura, basura, basura, basura)
        por_que_no(basura, basura, basura)
        el_parte(basura)
    assert la_ventana(None, CAL) == {"horas": None, "en_curso": True, "puede_escribir": False}
    antes = _entorno(**{ENV: "1"})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            r = correr(status=[], snapshot="x", v10=5, libros=7, calendario=CAL,
                       orden_ruta=Path(carpeta) / "nada.json", escritor_factory=_Escritor,
                       ahora=AHORA, plan_ruta=Path(carpeta) / "plan.json")
            assert isinstance(r, dict) and r["motivo"], r
    finally:
        _entorno(**antes)


TESTS = [
    test_solo_dentro_de_la_ventana,
    test_la_ventana_sale_del_calendario,
    test_el_once_mira_el_calendario_y_lleva_a_yamal,
    test_la_formacion_es_de_las_validas,
    test_en_positivo_solo_publica_el_banquillo,
    test_en_rojo_vende_lo_que_menos_puntos_pierde_por_euro,
    test_si_ni_todo_el_banquillo_llega_falta,
    test_a_quien_vender,
    test_la_caja_cuenta_las_pujas_enteras_y_la_vuelta,
    test_retira_lo_especulativo_a_menos_de_40_horas,
    test_solo_cobra_desde_el_90_por_ciento_salvo_a_menos_de_20_horas,
    test_apagado_no_lee_ni_escribe_nada,
    test_encendido_de_punta_a_punta,
    test_nunca_lanza_con_basura,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
