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
    ENV, a_quien_vender, adoptar, correr, decidir, el_mejor_once, el_parte, la_caja,
    la_mejora, la_ventana, las_fichas, las_pujas_vivas, lo_de_esta_vuelta, por_que_no,
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
            v10 = {"timestamp": AHORA.isoformat(), "ronda": {"hechas": [{"accion": "PUJAR", "player_id": 700,
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
        adoptar(basura, basura, basura, basura)
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


# ------------------------------------------------------------------
# LA REVISION DEL 12/10
# ------------------------------------------------------------------

def _foto_con(pujas=(), ofertas=(), saldo=1_000_000, plantilla=PLANTILLA):
    """La foto con nuestras pujas [(offer_id, player_id, importe)] y las
    ofertas del Computer [(offer_id, player_id, importe)]."""
    foto = _la_foto()
    foto["market"]["status"]["balance"] = saldo
    foto["market"]["offers"] = (
        [{"id": o, "status": "waiting", "amount": a, "requestedPlayers": [{"id": p}],
          "from": {"id": 99}} for o, p, a in pujas]
        + [{"id": o, "status": "waiting", "amount": a, "requestedPlayers": [{"id": p}],
            "from": None} for o, p, a in ofertas])
    foto["my_team"] = [{"id": p["id"], "price": p["price"]} for p in plantilla]
    foto["catalog"] = {"data": {"players": {str(p["id"]): {"status": p["status"]}
                                            for p in plantilla}}}
    return foto


def _status_con(plantilla=PLANTILLA, once_escrito=()):
    roster = [{"id": p["id"], "name": p["name"], "position": p["position"],
               "team_name": f"Equipo {p['team_id']}", "price": p["price"],
               "points": p["points"], "played_home": 15, "played_away": 15,
               "starter_probability": p["starter_probability"], "status": p["status"]}
              for p in plantilla]
    liga = ESTRELLAS + [{k: v for k, v in p.items() if k != "starter_probability"}
                        for p in plantilla]
    return {"league_center": {"laliga": {"standings": TABLA}},
            "todaLaLiga": {"players": liga}, "roster": {"players": roster},
            "libro_del_escaparate": {"players": []},
            "lineup": {"players": [{"id": i} for i in sorted(once_escrito)]}}


def test_un_titular_escrito_en_duda_no_se_vende():
    # La reproduccion de la revision: plantilla de 11 justos (la de
    # verdad), F1 'doubt' en el once escrito, 9 M de valor y una oferta
    # de 8 M a las 15 h. El once del cierre lo sienta (no esta sano),
    # pero no es candidato: ni se acepta ni se publica, y lo que falta
    # se dice (FALTA).
    once = [dict(p) for p in PLANTILLA if p["id"] in ONCE]
    for p in once:
        if p["id"] == 10:
            p.update(status="doubt", price=9_000_000)
    ofertas = {10: {"offer_id": 79, "amount": 8_000_000}}
    d = _d(plantilla=once, horas=15, ofertas=ofertas, once_escrito=ONCE, protegidos=set())
    assert 10 not in d["once"]["ids"] and d["once"]["lleno"] == 10, d["once"]
    assert 10 not in {pid for _, pid in _acciones(d)}, d["acciones"]
    assert d["vender"] == [] and d["falta"] == 4_000_000 and d["motivo"] == "FALTA", d
    assert d["titulares_que_no_se_venden"] == [10], d
    # Lesionado o sancionado (fuera seguro), si se puede vender.
    for estado in ("injured", "sanctioned"):
        fuera = [{**p, "status": estado} if p["id"] == 10 else p for p in once]
        d = _d(plantilla=fuera, horas=15, ofertas=ofertas, once_escrito=ONCE,
               protegidos=set())
        assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)], (estado, d["acciones"])
    # Y un titular escrito sano que el once del cierre sienta (F2 fuera
    # contra un duro) tampoco se publica ni se vende.
    d = _d(once_escrito=ONCE | {11}, ofertas={11: {"offer_id": 81, "amount": 3_100_000}},
           horas=15)
    assert 11 not in d["once"]["ids"] and 11 not in {pid for _, pid in _acciones(d)}, d
    assert 11 in d["titulares_que_no_se_venden"]
    # Sin once escrito en el panel (segunda revision): el que esta en duda
    # puede ser titular y tampoco se vende; el lesionado, si.
    d = _d(plantilla=once, horas=15, ofertas=ofertas, once_escrito=set(), protegidos=set())
    assert 10 not in {pid for _, pid in _acciones(d)} and 10 in d["titulares_que_no_se_venden"], d
    fuera = [{**p, "status": "injured"} if p["id"] == 10 else p for p in once]
    d = _d(plantilla=fuera, horas=15, ofertas=ofertas, once_escrito=set(), protegidos=set())
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)], d["acciones"]


def test_los_conservar_se_publican_y_solo_se_venden_fuera_del_once_escrito():
    # El modelo del dueño: publicar a los `conservar` esta bien (liquidez);
    # aceptar, solo si no son titulares del once escrito.
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": "1"})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden = Path(carpeta) / "orden.json"
            orden.write_text(json.dumps({
                "caduca": "2026-11-30T23:59:00+01:00",
                "proteger": [{"player_id": 9, "nombre": "Yamal"}],
                "conservar": [{"player_id": 13, "nombre": "B1"},
                              {"player_id": 11, "nombre": "F2"}],
            }))
            once = [dict(p) for p in PLANTILLA if p["id"] in ONCE | {11, 13}]
            # Caja: 1 M - 5 M = -4 M. F2 (conservar, titular escrito, sano
            # pero sentado por el calendario) no se toca; B1 (conservar,
            # fuera del once escrito) se publica y, con oferta, se vende.
            foto = _foto_con(pujas=[(9, 500, 5_000_000)],
                             ofertas=[(77, 13, 3_700_000), (81, 11, 3_100_000)],
                             plantilla=once)
            _Escritor.creados, _Escritor.llamadas = 0, []
            r = correr(status=_status_con(once, ONCE | {11}), snapshot=foto, v10={},
                       libros={}, calendario=CAL, orden_ruta=orden,
                       escritor_factory=_Escritor, ahora=AHORA,
                       plan_ruta=Path(carpeta) / "plan.json")
            d = r["decision"]
            assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 13)], d["acciones"]
            assert d["titulares_que_no_se_venden"] == [11], d
            # En positivo, al `conservar` de fuera del once se le publica.
            foto = _foto_con(saldo=10_000_000, plantilla=once)
            r = correr(status=_status_con(once, ONCE), snapshot=foto, v10={}, libros={},
                       calendario=CAL, orden_ruta=orden, escritor_factory=_Escritor,
                       ahora=AHORA, plan_ruta=Path(carpeta) / "plan.json")
            assert r["decision"]["motivo"] == "EN_POSITIVO"
            assert sorted(_acciones(r["decision"])) == [("PONER_A_LA_VENTA", 11),
                                                        ("PONER_A_LA_VENTA", 13)], r["decision"]
    finally:
        _entorno(**antes)


def test_lo_de_la_ronda_y_los_chollos_que_entra_en_el_once_se_adopta():
    # F3 (12) es de los chollos y entra en el once; B2 (14) es de la ronda
    # y se queda en el banquillo; 700 es una puja viva de la ronda.
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = {k: Path(carpeta) / f"{k}.json" for k in ("ronda", "chollos", "mejora")}
            rutas["ronda"].write_text(json.dumps({"14": 900_000, "700": 300_000}))
            rutas["chollos"].write_text(json.dumps({"12": 2_500_000}))
            rutas["mejora"].write_text(json.dumps({}))
            plan = Path(carpeta) / "plan.json"
            r = correr(status=_status_con(), snapshot=_foto_con(saldo=10_000_000), v10={},
                       libros=None, libros_rutas=rutas, calendario=CAL,
                       orden_ruta=Path(carpeta) / "no_hay_orden.json",
                       escritor_factory=_Escritor, ahora=AHORA, plan_ruta=plan)
            assert 12 in r["decision"]["once"]["ids"], r["decision"]["once"]
            assert r["decision"]["adoptar"] == [12], r["decision"]
            # Fuera de su libro, con el mismo formato; lo demas, igual.
            assert rutas["chollos"].read_text() == json.dumps({}, indent=2) + "\n"
            assert json.loads(rutas["ronda"].read_text()) == {"14": 900_000, "700": 300_000}
            publicado = json.loads(plan.read_text())
            assert publicado["adoptados"] == [
                {"player_id": 12, "libro": "chollos", "escrito": True}], publicado
            # Con los libros ya leidos y sin ruta, no se escribe nada (y
            # los tests no tocan los de produccion).
            r = correr(status=_status_con(), snapshot=_foto_con(saldo=10_000_000), v10={},
                       libros={"ronda": {}, "chollos": {"12": 1}, "mejora": {}},
                       calendario=CAL, orden_ruta=Path(carpeta) / "no_hay_orden.json",
                       escritor_factory=_Escritor, ahora=AHORA, plan_ruta=plan)
            assert r["adoptados"] == [{"player_id": 12, "libro": "chollos", "importe": 1,
                                       "escrito": False}], r["adoptados"]
    finally:
        _entorno(**antes)


def test_no_retira_las_pujas_de_la_orden_ni_las_de_la_mejora():
    # 500: el `fichar` de la orden (su clave sigue en el libro de los
    # chollos porque la orden la sustituyo); 600: la ronda; 601: la
    # mejora. Solo la de la ronda es del cierre.
    pujas = {500: {"offer_id": 9, "amount": 1_200_000},
             600: {"offer_id": 61, "amount": 1_500_000},
             601: {"offer_id": 62, "amount": 400_000}}
    d = _d(horas=30, pujas=pujas, especulativas={500, 600, 601}, protegidos={9, 500},
           no_retirar={601})
    assert _acciones(d, "CANCELAR_PUJA") == [("CANCELAR_PUJA", 600)], d["acciones"]
    # De punta a punta, con la orden APAGADA (protegidos vacio): el
    # `fichar` sale del fichero de la orden y la de la mejora de su libro
    # (las dos con la clave aun en el libro de los chollos).
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden = Path(carpeta) / "orden.json"
            orden.write_text(json.dumps({"caduca": "2026-11-30T23:59:00+01:00",
                                         "fichar": [{"player_id": 500, "puja": 1_200_000}]}))
            jueves = datetime(2026, 10, 15, 5, 15, tzinfo=timezone.utc)   # a 37,75 h
            foto = _foto_con(pujas=[(9, 500, 1_200_000), (61, 600, 1_500_000),
                                    (62, 601, 400_000)])
            r = correr(status=_status_con(), snapshot=foto, v10={},
                       libros={"ronda": {"600": 1_500_000},
                               "chollos": {"500": 1_200_000, "601": 400_000},
                               "mejora": {"601": {"sale": 15, "puja": 400_000}}},
                       calendario=CAL, orden_ruta=orden, escritor_factory=_Escritor,
                       ahora=jueves, plan_ruta=Path(carpeta) / "plan.json")
            assert _acciones(r["decision"], "CANCELAR_PUJA") == [("CANCELAR_PUJA", 600)], \
                r["decision"]["acciones"]
    finally:
        _entorno(**antes)


def test_a_quien_vender_busca_el_minimo_exacto():
    # La de la revision: 4 M de deficit; uno de 9,5 M que pierde 12 o tres
    # de 1,425 M que pierden 3 cada uno. Los tres (pierden 9).
    grande = {"id": 1, "cobro": 9_500_000, "quedarse": 12.0}
    chicos = [{"id": i, "cobro": 1_425_000, "quedarse": 3.0} for i in (2, 3, 4)]
    elegidos, falta = a_quien_vender([grande] + chicos, 4_000_000)
    assert sorted(x["id"] for x in elegidos) == [2, 3, 4] and falta == 0, elegidos
    # A igual perdida, el que menos se pasa del deficit.
    c = [{"id": 1, "cobro": 1_500_000, "quedarse": 2.0},
         {"id": 2, "cobro": 1_100_000, "quedarse": 2.0}]
    assert [x["id"] for x in a_quien_vender(c, 1_000_000)[0]] == [2]
    # Con mas de 15 candidatos, el voraz de siempre.
    relleno = [{"id": 100 + i, "cobro": 1_000_000, "quedarse": 100.0} for i in range(12)]
    elegidos, falta = a_quien_vender([grande] + chicos + relleno, 4_000_000)
    assert [x["id"] for x in elegidos] == [1] and falta == 0, elegidos


def test_yamal_nunca_se_publica_ni_se_vende():
    # Sin protegidos (orden apagada, caducada o rota) y aun sin la lista
    # de intocables (`yamal_por_lesion`): Yamal, por su nombre, ni se
    # publica ni se vende, aunque haga falta y haya oferta.
    ofertas = {9: {"offer_id": 80, "amount": 30_000_000}}
    for intocables in ({"yamal"}, set()):
        for estado in ("ok", "injured"):
            plantilla = [{**p, "status": estado} if p["id"] == 9 else p for p in PLANTILLA]
            d = _d(plantilla=plantilla, protegidos=set(), intocables=intocables,
                   ofertas=ofertas, horas=15, saldo=-30_000_000)
            assert 9 not in {pid for _, pid in _acciones(d)}, (intocables, estado, d["acciones"])
            assert 9 not in d["vender"] and 9 not in {c["id"] for c in d["candidatos"]}


def test_lo_que_publico_el_escaparate_no_se_vuelve_a_publicar():
    v10 = {"timestamp": AHORA.isoformat(), "escaparate": {"listed": [{"player_id": 11, "listed_price": 3_450_000,
                                      "sent": True, "success": True}]}}
    assert lo_de_esta_vuelta(v10)["listados"] == {11}
    # En seco (ESCAPARATE_APAGADO=1: sent False) no cuenta: no hay precio
    # que respetar y el cierre lo publica si le toca.
    seco = {"escaparate": {"listed": [{"player_id": 11, "live": False, "sent": False}]}}
    assert lo_de_esta_vuelta(seco)["listados"] == set()
    fallido = {"escaparate": {"listed": [{"player_id": 11, "sent": True, "success": False}]}}
    assert lo_de_esta_vuelta(fallido)["listados"] == set()
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            r = correr(status=_status_con(), snapshot=_foto_con(saldo=10_000_000), v10=v10,
                       libros={}, calendario=CAL, orden_ruta=Path(carpeta) / "nada.json",
                       escritor_factory=_Escritor, ahora=AHORA,
                       plan_ruta=Path(carpeta) / "plan.json")
            publicados = {pid for _, pid in _acciones(r["decision"], "PONER_A_LA_VENTA")}
            assert 11 not in publicados and 13 in publicados, r["decision"]["acciones"]
            # El estado de OTRA vuelta (hace 2 h, o con otro run_id) no
            # cuenta: la cache lo trae cuando esta no lo escribe (429).
            from datetime import timedelta as _td
            viejo = {**v10, "timestamp": (AHORA - _td(hours=2)).isoformat()}
            r = correr(status=_status_con(), snapshot=_foto_con(saldo=10_000_000), v10=viejo,
                       libros={}, calendario=CAL, orden_ruta=Path(carpeta) / "nada.json",
                       escritor_factory=_Escritor, ahora=AHORA,
                       plan_ruta=Path(carpeta) / "plan.json")
            assert r.get("v10_descartado"), r
            publicados = {pid for _, pid in _acciones(r["decision"], "PONER_A_LA_VENTA")}
            assert 11 in publicados, r["decision"]["acciones"]
    finally:
        _entorno(**antes)


def test_si_algo_falla_el_plan_viejo_no_se_queda():
    class _Roto:
        def __init__(self):
            raise RuntimeError("login")

    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            plan = Path(carpeta) / "el_cierre.json"
            plan.write_text(json.dumps({"activo": True, "xi": [1], "vender": [13],
                                        "generated_at": "2026-10-13T05:15:00+00:00"}))
            r = correr(status=_status_con(), snapshot=_foto_con(), v10={}, libros={},
                       calendario=CAL, orden_ruta=Path(carpeta) / "nada.json",
                       escritor_factory=_Roto, ahora=AHORA, plan_ruta=plan)
            assert r["motivo"].startswith("ERROR: RuntimeError"), r["motivo"]
            publicado = json.loads(plan.read_text())
            assert publicado["activo"] is False and publicado["motivo"] == r["motivo"], publicado
            assert publicado["generated_at"] == AHORA.isoformat() and publicado["xi"] == []
    finally:
        _entorno(**antes)


# Un aplazado de la J6 entre la J9 y la J10, como el Levante-Athletic
# del 21/10: el 8 en casa contra un duro.
CAL_CON_APLAZADO = {"matchdays": [
    {"matchday": 6, "matches": [
        _p(6, 2, 3, "2026-09-18T21:00:00+02:00"), _p(6, 4, 5, "2026-09-19T16:00:00+02:00"),
        _p(6, 6, 7, "2026-09-20T18:30:00+02:00"), _p(6, 9, 10, "2026-09-21T21:00:00+02:00"),
        _p(6, 8, 1, "2026-10-21T20:00:00+02:00"),
    ]},
] + CAL["matchdays"] + [
    {"matchday": 12, "matches": [
        _p(12, 9, 1, "2026-11-06T21:00:00+01:00"), _p(12, 2, 8, "2026-11-07T16:00:00+01:00"),
        _p(12, 3, 10, "2026-11-07T18:30:00+01:00"), _p(12, 4, 7, "2026-11-08T14:00:00+01:00"),
        _p(12, 5, 6, "2026-11-09T21:00:00+01:00"),
    ]},
]}


def test_el_once_es_para_la_principal_y_la_caja_para_la_que_venga():
    from src.analysis.el_calendario_de_puntos import xp_jugador

    martes = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)    # J9 acabada
    v = la_ventana(martes, CAL_CON_APLAZADO)
    # El plazo es el aplazado (32 h): dentro de la ventana, aunque la J10
    # este a 81 h.
    assert abs(v["horas"] - 32.0) < 0.01 and por_que_no(**v) is None, v
    ctx = contexto(STATUS, CAL_CON_APLAZADO, martes, 12)
    assert not ctx["rondas"][0]["principal"]
    d = _d(ctx=ctx, horas=v["horas"])
    assert d["activo"] and d["deficit"] == 4_000_000 and d["vender"], d
    assert d["plazo"]["label"] == "Jornada 6 (aplazada)", d["plazo"]
    assert d["ronda"]["label"] == "Jornada 10" and d["ronda"]["principal"], d["ronda"]
    # El xP del once es el de la J10, no el del aplazado.
    f1 = next(p for p in PLANTILLA if p["id"] == 10)
    principales = {**ctx, "rondas": [r for r in ctx["rondas"] if r["principal"]]}
    de_la_j10 = xp_jugador(principales, f1, f1["starter_probability"], 1)
    del_aplazado = xp_jugador(ctx, f1, f1["starter_probability"], 1)
    assert abs(de_la_j10 - del_aplazado) > 0.01
    xp = {j["id"]: j["xp"] for j in d["once"]["jugadores"]}
    assert abs(xp[10] - round(de_la_j10, 3)) < 1e-9, (xp[10], de_la_j10, del_aplazado)
    # Y de punta a punta, el plan lo dice.
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            plan = Path(carpeta) / "plan.json"
            correr(status=_status_con(), snapshot=_foto_con(), v10={}, libros={},
                   calendario=CAL_CON_APLAZADO, orden_ruta=Path(carpeta) / "nada.json",
                   escritor_factory=_Escritor, ahora=martes, plan_ruta=plan)
            publicado = json.loads(plan.read_text())
            assert publicado["ronda"]["label"] == "Jornada 10", publicado
            assert publicado["plazo"]["label"] == "Jornada 6 (aplazada)", publicado
            assert abs(publicado["horas"] - 32.0) < 0.01 and publicado["activo"], publicado
            # Quedarse pesa 3 rondas PRINCIPALES (J10, J11, J12), aunque el
            # aplazado vaya delante: el contexto se pide con rondas de sobra.
            r = correr(status=_status_con(), snapshot=_foto_con(), v10={}, libros={},
                       calendario=CAL_CON_APLAZADO, orden_ruta=Path(carpeta) / "nada.json",
                       escritor_factory=_Escritor, ahora=martes, plan_ruta=plan)
            b1 = next(c for c in r["decision"]["candidatos"] if c["id"] == 13)
            ficha = next(f for f in las_fichas(_status_con(), {13}))
            tres = {**principales, "rondas": principales["rondas"][:3]}
            assert [x["label"] for x in tres["rondas"]] == ["Jornada 10", "Jornada 11",
                                                          "Jornada 12"], tres["rondas"]
            assert b1["quedarse"] == round(xp_jugador(tres, ficha, None, 3), 3), b1
            dos = {**principales, "rondas": principales["rondas"][:2]}
            assert b1["quedarse"] != round(xp_jugador(dos, ficha, None, 3), 3), b1
    finally:
        _entorno(**antes)


def test_sin_calendario_lo_dice():
    v = la_ventana(AHORA, {})
    assert v["horas"] is None and por_que_no(**v) == "SIN_CALENDARIO", v
    antes = _entorno(**{ENV: "1"})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            r = correr(status=_status_con(), snapshot=_foto_con(), v10={}, libros={},
                       calendario={}, orden_ruta=Path(carpeta) / "nada.json",
                       escritor_factory=_Escritor, ahora=AHORA,
                       plan_ruta=Path(carpeta) / "plan.json")
            assert r["motivo"] == "SIN_CALENDARIO", r
    finally:
        _entorno(**antes)


def test_los_que_se_van_y_los_de_la_mejora_no_cuentan():
    # Los que ya se van (su relevo esta dentro) no entran en el once.
    d = _d(se_van={10}, no_vender={10})
    assert 10 not in d["once"]["ids"] and 10 not in {c["id"] for c in d["candidatos"]}, d
    # El que sale por la mejora es suyo; si su relevo ya esta, se va.
    m = la_mejora({"700": {"sale": 13, "puja": 300_000}, "14": {"sale": 15}}, {13, 14, 15})
    assert m == {"vende": {13, 15}, "se_van": {15}}, m
    # El estado es el del catalogo de la foto, aunque el panel diga otra cosa.
    fichas = las_fichas(_status_con(), {10, 11}, estados={10: "injured"})
    assert {f["id"]: f["status"] for f in fichas} == {10: "injured", 11: "ok"}, fichas
    # De punta a punta: lo que vende la mejora ni se publica.
    antes = _entorno(**{ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            r = correr(status=_status_con(), snapshot=_foto_con(), v10={},
                       libros={"ronda": {}, "chollos": {},
                               "mejora": {"700": {"sale": 13, "puja": 300_000}}},
                       calendario=CAL, orden_ruta=Path(carpeta) / "nada.json",
                       escritor_factory=_Escritor, ahora=AHORA,
                       plan_ruta=Path(carpeta) / "plan.json")
            assert 13 not in {pid for _, pid in _acciones(r["decision"])}, r["decision"]
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
    test_un_titular_escrito_en_duda_no_se_vende,
    test_los_conservar_se_publican_y_solo_se_venden_fuera_del_once_escrito,
    test_lo_de_la_ronda_y_los_chollos_que_entra_en_el_once_se_adopta,
    test_no_retira_las_pujas_de_la_orden_ni_las_de_la_mejora,
    test_a_quien_vender_busca_el_minimo_exacto,
    test_yamal_nunca_se_publica_ni_se_vende,
    test_lo_que_publico_el_escaparate_no_se_vuelve_a_publicar,
    test_si_algo_falla_el_plan_viejo_no_se_queda,
    test_el_once_es_para_la_principal_y_la_caja_para_la_que_venga,
    test_sin_calendario_lo_dice,
    test_los_que_se_van_y_los_de_la_mejora_no_cuentan,
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
