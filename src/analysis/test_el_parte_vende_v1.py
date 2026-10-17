"""
EL PARTE VENDE (17/10/2026). Guardias de `src/actions/el_parte_vende.py`
(`BORDALAS_EL_PARTE_VENDE`, paso 4 del laboratorio).

    1. Vende al de parte malo ('doubt', 'injured', 'sanctioned') que no
       esta en el once escrito si la oferta del Computer llega al 95 % de
       su valor; por debajo, no.
    2. Si no esta publicado, lo publica a su valor.
    3. Nunca toca al once escrito (el del panel y el de Biwenger), a
       Yamal, a los protegidos, a los `conservar`, a lo de la cartera ni
       a lo vendido en esta vuelta.
    4. Con una ronda jugandose, en la zona de silencio o sin calendario,
       nada.
    5. Sin el once escrito del panel, nada, y lo dice.
    6. Nace apagado (lo apaga esta guardia, no el entorno) y nunca lanza.

Todo con datos de mentira: la hora se pasa siempre, el calendario es un
dict de este fichero, la orden y el libro de la ronda se escriben en una
carpeta temporal y el escritor es de mentira. No se lee el estado de
produccion, ni el reloj, ni se sale a la red.
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

from src.actions.el_parte_vende import (     # noqa: E402
    ENV, MALOS, SUELO, activa, correr, decidir, el_parte, el_suelo, ids_del_once,
    lo_vendido_y_publicado, por_que_no,
)


AHORA = datetime(2026, 10, 14, 18, 7, tzinfo=timezone.utc)      # mie 20:07 Madrid
EN_CURSO = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)   # sab, la J9 jugandose
SILENCIO = datetime(2026, 10, 15, 3, 30, tzinfo=timezone.utc)   # jue 05:30 Madrid


def _p(j, casa, fuera, cuando):
    return {"matchday": j, "home": f"Equipo {casa}", "away": f"Equipo {fuera}",
            "kickoff": cuando}


# La J9 empieza el viernes 16/10 a las 21:00 de Madrid y acaba el lunes 19/10.
CAL = {"matchdays": [
    {"matchday": 9, "matches": [
        _p(9, 7, 1, "2026-10-16T21:00:00+02:00"),
        _p(9, 8, 9, "2026-10-17T16:00:00+02:00"),
        _p(9, 2, 10, "2026-10-17T18:30:00+02:00"),
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
]}


# ------------------------------------------------------------------
# LA PLANTILLA DE MENTIRA
# ------------------------------------------------------------------
#
#     1-11   el once escrito del panel (3 en duda y 4 lesionado: titulares)
#     12     en duda, 2 M, oferta de 1,9 M (el 95 % justo)        -> se vende
#     13     lesionado, 1 M, sin oferta, sin publicar               -> se publica
#     14     sancionado, 3 M, publicado, oferta de 2.849.999        -> nada
#     15     en duda, 1 M, oferta de 949.999, sin publicar          -> se publica
#     16     'ok' con oferta de 9 M                                 -> no se toca
#     17     'warned'                                               -> no se toca
#     18     en duda, `proteger` de la orden                        -> no se toca
#     19     lesionado, `conservar` de la orden                     -> no se toca
#     20     Lamine Yamal, lesionado, oferta de 30 M                -> no se toca
#     21     en duda, de la cartera de la ronda                     -> no se toca
#     22     sin estado                                             -> no se toca
#     23     en duda, ya vendido por el cierre en esta vuelta       -> no se toca
#     24     lesionado, publicado por el escaparate en esta vuelta  -> nada
#     25     en duda, titular en la alineacion de Biwenger          -> no se toca

def _j(pid, nombre, estado, valor):
    return {"id": pid, "name": nombre, "status": estado, "price": valor}


PLANTILLA = [_j(i, f"Titular {i}", "ok", 2_000_000) for i in range(1, 12)]
PLANTILLA[2]["status"] = "doubt"
PLANTILLA[3]["status"] = "injured"
PLANTILLA += [
    _j(12, "Dudoso", "doubt", 2_000_000),
    _j(13, "Lesionado", "injured", 1_000_000),
    _j(14, "Sancionado", "sanctioned", 3_000_000),
    _j(15, "Bajo", "doubt", 1_000_000),
    _j(16, "Sano", "ok", 1_000_000),
    _j(17, "Apercibido", "warned", 1_000_000),
    _j(18, "Protegido", "doubt", 1_000_000),
    _j(19, "Conservado", "injured", 1_000_000),
    _j(20, "Lamine Yamal", "injured", 25_000_000),
    _j(21, "De la cartera", "doubt", 1_000_000),
    _j(22, "Sin estado", None, 1_000_000),
    _j(23, "Vendido hoy", "doubt", 1_000_000),
    _j(24, "Publicado hoy", "injured", 1_000_000),
    _j(25, "Titular en Biwenger", "doubt", 1_000_000),
]
ONCE = set(range(1, 12))

# {player_id: (offer_id, importe)} del Computer.
OFERTAS = {3: (703, 5_000_000), 12: (712, 1_900_000), 14: (714, 2_849_999),
           15: (715, 949_999), 16: (716, 9_000_000), 18: (718, 5_000_000),
           19: (719, 5_000_000), 20: (720, 30_000_000), 21: (721, 5_000_000),
           23: (723, 5_000_000), 25: (725, 5_000_000)}
PUBLICADOS = {14}


def _la_foto(once_de_biwenger=True):
    foto = {
        "league": {"user": {"id": 99}},
        "market": {
            "status": {"balance": 1_000_000, "maximumBid": 20_000_000},
            "sales": [{"player": {"id": p}, "user": {"id": 99}, "price": 3_100_000}
                      for p in PUBLICADOS]
            + [{"player": {"id": 500}, "user": None, "price": 1_000_000}],
            "offers": [{"id": o, "status": "waiting", "amount": a,
                        "requestedPlayers": [{"id": p}], "from": None}
                       for p, (o, a) in OFERTAS.items()],
        },
        "my_team": [{"id": p["id"], "price": p["price"]} for p in PLANTILLA],
        "catalog": {"data": {"players": {str(p["id"]): {"name": p["name"],
                                                        "status": p["status"],
                                                        "price": p["price"]}
                                         for p in PLANTILLA}}},
    }
    if once_de_biwenger:
        foto["user_lineup"] = {"data": {"lineup": {"players": [
            {"id": i} for i in sorted(ONCE | {25})]}}}
    return foto


def _el_status(con_once=True):
    status = {"roster": {"players": [{"id": p["id"], "name": p["name"]} for p in PLANTILLA]}}
    if con_once:
        status["lineup"] = {"players": [{"id": i, "name": f"Titular {i}"} for i in sorted(ONCE)]}
    return status


# Lo que esta vuelta ya hizo: el cierre cobro al 23 y el escaparate
# publico al 24.
V10 = {"timestamp": AHORA.isoformat(),
       "escaparate": {"listed": [{"player_id": 24, "sent": True, "success": True}]}}
PLAN_CIERRE = {"generated_at": AHORA.isoformat(),
               "hechas": [{"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 23,
                           "exito": True}]}


def _d(**k):
    """`decidir` con la plantilla de mentira, ya leida."""
    base = dict(
        plantilla={p["id"] for p in PLANTILLA},
        estados={p["id"]: p["status"] for p in PLANTILLA},
        nombres={p["id"]: p["name"] for p in PLANTILLA},
        precios={p["id"]: p["price"] for p in PLANTILLA},
        ofertas_del_computer={p: {"offer_id": o, "amount": a} for p, (o, a) in OFERTAS.items()},
        en_venta=set(PUBLICADOS) | {24},
        once_escrito=ONCE | {25},
        protegidos={18}, conservados={19}, aguanta={21}, vendidos={23},
    )
    base.update(k)
    return decidir(**base)


def _acciones(d, accion=None):
    return sorted((a["accion"], a["player_id"]) for a in d["acciones"]
                  if accion is None or a["accion"] == accion)


def _escrituras(d):
    return sorted((a["accion"], a["player_id"]) for a in d["acciones"]
                  if a["accion"] != "NADA")


class _Escritor:
    llamadas: list = []
    creados = 0

    def __init__(self):
        type(self).creados += 1

    def accept_offer(self, **k):
        type(self).llamadas.append(("accept_offer", k))
        return {"sent": True, "success": True, "http_status": 200}

    def list_player_for_sale(self, **k):
        type(self).llamadas.append(("list_player_for_sale", k))
        return {"sent": True, "success": True, "http_status": 200}

    def place_bid(self, **k):
        type(self).llamadas.append(("place_bid", k))
        return {"sent": True, "success": True, "http_status": 200}

    def cancel_bid(self, **k):
        type(self).llamadas.append(("cancel_bid", k))
        return {"sent": True, "success": True, "http_status": 200}


class _EscritorQueRevienta:
    def __getattr__(self, nombre):
        raise RuntimeError("la red se ha caido")


def _limpiar():
    _Escritor.creados, _Escritor.llamadas = 0, []


def _entorno(**valores):
    """Pone los interruptores (None = quitarlo) y devuelve como estaban."""
    antes = {k: os.environ.get(k) for k in valores}
    for k, v in valores.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return antes


# Los interruptores que esta guardia lee, puestos por ella (doctrina 104).
ENCENDIDO = {ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": "1", "BORDALAS_LA_CARTERA": "1",
             "GITHUB_RUN_ID": None}


def _ficheros(carpeta):
    """La orden del gestor y el libro de la ronda, en la carpeta temporal."""
    orden = Path(carpeta) / "orden.json"
    orden.write_text(json.dumps({
        "caduca": "2026-11-30T23:59:00+01:00",
        "proteger": [{"player_id": 18, "nombre": "Protegido"}],
        "conservar": [{"player_id": 19, "nombre": "Conservado"}],
    }))
    libro = Path(carpeta) / "la_ronda.json"
    libro.write_text(json.dumps({"21": 1_000_000}))
    return orden, libro


def _correr(carpeta, **k):
    orden, libro = _ficheros(carpeta)
    base = dict(cycle={"snapshot": _la_foto()}, escritor_factory=_Escritor, ahora=AHORA,
                status=_el_status(), calendario=CAL, orden_ruta=orden,
                libro_ronda_ruta=libro, v10=V10, vuelta_mejora={}, plan_cierre=PLAN_CIERRE)
    base.update(k)
    return correr(**base)


# ------------------------------------------------------------------
# 1. VENDE DESDE EL 95 %, Y POR DEBAJO NO
# ------------------------------------------------------------------

def test_vende_al_dudoso_fuera_del_once_desde_el_95():
    assert SUELO == 0.95 and MALOS == {"doubt", "injured", "sanctioned"}
    assert el_suelo(2_000_000) == 1_900_000 and el_suelo(1_000_001) == 950_001
    assert el_suelo(0) is None and el_suelo("x") is None
    d = _d()
    assert d["activo"] and d["motivo"] is None, d
    venta = [a for a in d["acciones"] if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"]
    assert [(a["player_id"], a["offer_id"], a["importe"], a["suelo"]) for a in venta] == [
        (12, 712, 1_900_000, 1_900_000)], d["acciones"]
    # Los tres partes valen: en duda, lesionado y sancionado.
    for estado in ("doubt", "injured", "sanctioned", " Injured "):
        d = decidir(plantilla={7}, estados={7: estado}, nombres={7: "Suplente"},
                    precios={7: 1_000_000},
                    ofertas_del_computer={7: {"offer_id": 70, "amount": 950_000}},
                    once_escrito={1})
        assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], (estado, d)
    # Las claves en texto (como vienen de un JSON) tambien.
    d = decidir(plantilla=["7"], estados={"7": "doubt"}, nombres={"7": "Suplente"},
                precios={"7": "1000000"},
                ofertas_del_computer={"7": {"offer_id": "70", "amount": "1000000"}},
                once_escrito=["1"])
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d


def test_no_vende_por_debajo_del_95():
    d = _d()
    # 14: publicado y la oferta se queda a 1 euro del 95 %: nada, y dice por que.
    nada = {a["player_id"]: a for a in d["acciones"] if a["accion"] == "NADA"}
    assert 14 in nada and "95 %" in nada[14]["motivo"], d["acciones"]
    assert 14 not in {a["player_id"] for a in d["acciones"] if a["accion"] != "NADA"}
    # 15: oferta por debajo y sin publicar: se publica, no se cobra.
    assert ("PONER_A_LA_VENTA", 15) in _acciones(d)
    assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 15) not in _acciones(d)
    # Sin offer_id no se puede aceptar.
    d = decidir(plantilla={7}, estados={7: "doubt"}, nombres={7: "S"}, precios={7: 1_000_000},
                ofertas_del_computer={7: {"amount": 2_000_000}}, en_venta={7},
                once_escrito={1})
    assert _escrituras(d) == [], d


def test_lo_publica_si_no_esta_publicado():
    d = _d()
    publica = {a["player_id"]: a["precio"] for a in d["acciones"]
               if a["accion"] == "PONER_A_LA_VENTA"}
    assert publica == {13: 1_000_000, 15: 1_000_000}, d["acciones"]
    # Ya publicado y sin oferta: nada que escribir.
    d = _d(en_venta=set(PUBLICADOS) | {13, 15, 24})
    assert _escrituras(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 12)], d["acciones"]
    # Sin valor ni se publica ni se cobra.
    d = decidir(plantilla={7}, estados={7: "doubt"}, nombres={7: "S"}, precios={},
                ofertas_del_computer={7: {"offer_id": 70, "amount": 5_000_000}},
                once_escrito={1})
    assert _escrituras(d) == [] and d["no_se_tocan"][0]["por"] == "SIN_VALOR", d


# ------------------------------------------------------------------
# 2. A QUIEN NUNCA
# ------------------------------------------------------------------

def test_nunca_toca_once_yamal_protegidos_conservados_ni_cartera():
    d = _d()
    tocados = {a["player_id"] for a in d["acciones"]}
    assert tocados == {12, 13, 14, 15, 24}, d["acciones"]
    por = {n["player_id"]: n["por"] for n in d["no_se_tocan"]}
    assert por == {3: "ONCE_ESCRITO", 4: "ONCE_ESCRITO", 18: "PROTEGIDO",
                   19: "CONSERVAR", 20: "YAMAL", 21: "LA_CARTERA",
                   23: "VENDIDO_EN_ESTA_VUELTA", 25: "ONCE_ESCRITO"}, por
    # 'ok', 'warned' y sin estado ni se miran.
    assert not {16, 17, 22} & (tocados | set(por)) and set(d["malos"]) == tocados | set(por)
    # Yamal por su nombre, se escriba como se escriba, y sin nombre no se vende.
    for nombre in ("Yamal", "LAMINE YAMAL", ["Lamine", "L. Yamal"]):
        d = decidir(plantilla={7}, estados={7: "injured"}, nombres={7: nombre},
                    precios={7: 1_000_000},
                    ofertas_del_computer={7: {"offer_id": 70, "amount": 2_000_000}},
                    once_escrito={1})
        assert d["acciones"] == [] and d["no_se_tocan"][0]["por"] == "YAMAL", (nombre, d)
    d = decidir(plantilla={7}, estados={7: "injured"}, nombres={}, precios={7: 1_000_000},
                ofertas_del_computer={7: {"offer_id": 70, "amount": 2_000_000}},
                once_escrito={1})
    assert d["acciones"] == [] and d["no_se_tocan"][0]["por"] == "SIN_NOMBRE", d
    # Un titular del once escrito no se vende NUNCA, ni con la mejor oferta.
    d = _d(ofertas_del_computer={i: {"offer_id": i, "amount": 99_000_000} for i in range(1, 26)})
    assert not {a["player_id"] for a in d["acciones"]} & (ONCE | {25}), d["acciones"]
    assert not {a["player_id"] for a in d["acciones"]} & {18, 19, 20, 21, 23}


# ------------------------------------------------------------------
# 3. CUANDO NO
# ------------------------------------------------------------------

def test_nada_con_una_ronda_jugandose():
    for en_curso in (True, None, "x"):
        d = _d(en_curso=en_curso)
        assert d["acciones"] == [] and d["motivo"] == "JORNADA_EN_CURSO", (en_curso, d)
    assert _d(puede_escribir=False)["acciones"] == []
    assert _d(sin_calendario=True)["motivo"] == "SIN_CALENDARIO"
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            for ahora, motivo, cal in ((EN_CURSO, "JORNADA_EN_CURSO", CAL),
                                       (SILENCIO, "ZONA_DE_SILENCIO", CAL),
                                       (AHORA, "SIN_CALENDARIO", {})):
                _limpiar()
                r = _correr(carpeta, ahora=ahora, calendario=cal)
                assert r["motivo"] == motivo and r["acciones"] == [] and r["hechas"] == [], r
                assert _Escritor.creados == 0 and _Escritor.llamadas == [], r
                assert any(motivo in linea for linea in el_parte(r))
    finally:
        _entorno(**antes)


def test_nada_sin_el_once_escrito_y_lo_dice():
    assert por_que_no(once_escrito=set()) == "SIN_ONCE_ESCRITO"
    assert por_que_no(once_escrito=None) is None
    d = _d(once_escrito=set())
    assert d["acciones"] == [] and d["motivo"] == "SIN_ONCE_ESCRITO", d
    assert ids_del_once({"players": [{"id": 1}, {"id": "2"}, {"x": 3}, 4]}) == {1, 2}
    assert ids_del_once(None) == set() and ids_del_once({"players": "x"}) == set()
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            # Sin el once del panel no basta con el de Biwenger: no se sabe.
            for status in (_el_status(con_once=False), {}, {"lineup": {"players": []}}):
                _limpiar()
                r = _correr(carpeta, status=status)
                assert r["motivo"] == "SIN_ONCE_ESCRITO" and r["acciones"] == [], r
                assert "once escrito" in r["detalle"] and _Escritor.creados == 0, r
                assert any("SIN_ONCE_ESCRITO" in linea for linea in el_parte(r))
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 4. DE PUNTA A PUNTA
# ------------------------------------------------------------------

def test_encendido_de_punta_a_punta():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta)
            assert r["motivo"] == "EJECUTADA", r
            assert _escrituras(r["decision"]) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 12),
                                                  ("PONER_A_LA_VENTA", 13),
                                                  ("PONER_A_LA_VENTA", 15)], r["acciones"]
            assert _Escritor.creados == 1 and sorted(_Escritor.llamadas, key=str) == sorted([
                ("accept_offer", {"offer_id": 712, "execute": True}),
                ("list_player_for_sale", {"player_id": 13, "price": 1_000_000,
                                          "execute": True}),
                ("list_player_for_sale", {"player_id": 15, "price": 1_000_000,
                                          "execute": True}),
            ], key=str), _Escritor.llamadas
            assert len(r["hechas"]) == 3 and all(h["exito"] for h in r["hechas"]), r["hechas"]
            # El once escrito es el del panel MAS el de Biwenger (el 25).
            assert r["once_escrito"] == sorted(ONCE | {25}), r["once_escrito"]
            por = {n["player_id"]: n["por"] for n in r["decision"]["no_se_tocan"]}
            assert por[20] == "YAMAL" and por[21] == "LA_CARTERA" and por[25] == "ONCE_ESCRITO"
            assert por[18] == "PROTEGIDO" and por[19] == "CONSERVAR"
            assert por[23] == "VENDIDO_EN_ESTA_VUELTA", por
            # El 24 lo publico el escaparate en esta vuelta: no se publica otra vez.
            assert ("NADA", 24) in _acciones(r["decision"])
            assert el_parte(r) and any("EJECUTADA" in linea for linea in el_parte(r))

            # Sin la cartera, lo de la ronda es como cualquier suplente.
            _entorno(BORDALAS_LA_CARTERA=None)
            _limpiar()
            r = _correr(carpeta)
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 21) in _escrituras(r["decision"]), r
            _entorno(BORDALAS_LA_CARTERA="1")

            # Lo de una vuelta vieja (de hace 2 h) no cuenta como de esta.
            vieja = AHORA.replace(hour=16)
            _limpiar()
            r = _correr(carpeta, v10={**V10, "timestamp": vieja.isoformat()},
                        plan_cierre={**PLAN_CIERRE, "generated_at": vieja.isoformat()})
            escrituras = _escrituras(r["decision"])
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 23) in escrituras, escrituras
            assert ("PONER_A_LA_VENTA", 24) in escrituras, escrituras
            assert len(r["vuelta_descartada"]) == 3, r["vuelta_descartada"]

            # Nada que escribir: NADA_QUE_HACER y sin crear el escritor.
            _limpiar()
            foto = _la_foto()
            foto["market"]["offers"] = []
            foto["market"]["sales"] += [{"player": {"id": p}, "user": {"id": 99}}
                                        for p in (12, 13, 15)]
            r = _correr(carpeta, cycle={"snapshot": foto})
            assert r["motivo"] == "NADA_QUE_HACER" and _Escritor.creados == 0, r
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 5. NACE APAGADO Y NUNCA LANZA
# ------------------------------------------------------------------

def test_nace_apagado():
    antes = _entorno(**{ENV: None})
    try:
        assert activa() is False
        # Sin argumentos: vuelve antes de leer nada.
        assert correr() == {"activa": False, "motivo": "APAGADA", "acciones": [],
                            "hechas": [], "decision": None}
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta)
            assert r["motivo"] == "APAGADA" and _Escritor.creados == 0, r
        for valor in ("0", "", "no", "false"):
            _entorno(**{ENV: valor})
            assert activa() is False, valor
        for valor in ("1", "true", "si", "yes", " TRUE "):
            _entorno(**{ENV: valor})
            assert activa() is True, valor
    finally:
        _entorno(**antes)
    from src.telemetry.el_tablon import QUE_HACE

    assert "95 %" in QUE_HACE[ENV], QUE_HACE.get(ENV)


def test_nunca_lanza_con_basura():
    for basura in (None, "x", 5, [1, 2], {"a": object()}, object()):
        d = decidir(plantilla=basura, estados=basura, nombres=basura, precios=basura,
                    ofertas_del_computer=basura, en_venta=basura, once_escrito=basura,
                    protegidos=basura, conservados=basura, aguanta=basura,
                    vendidos=basura, en_curso=False, puede_escribir=True,
                    sin_calendario=False)
        assert isinstance(d, dict) and d["acciones"] == [], d
        por_que_no(puede_escribir=basura, sin_calendario=basura, en_curso=basura,
                   once_escrito=basura)
        el_parte(basura)
        ids_del_once(basura)
        el_suelo(basura)
        v = lo_vendido_y_publicado(basura, basura, basura, basura, basura)
        assert v["vendidos"] == set() and v["listados"] == set(), v
    d = decidir(plantilla=[7, "x", None], estados={7: "doubt", "x": 5},
                nombres={7: 5}, precios={7: "mucho"},
                ofertas_del_computer={7: "x"}, once_escrito={1})
    assert isinstance(d, dict) and _escrituras(d) == [], d
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden, libro = _ficheros(carpeta)
            for basura in (None, "x", 5, [1, 2], {"snapshot": "x"}, {"snapshot": {"my_team": 5}}):
                # (None seria «leelo de produccion»: aqui, vacio.)
                nada = {} if basura is None else basura
                r = correr(cycle=nada, escritor_factory=_Escritor, ahora=AHORA, status=nada,
                           calendario=CAL, orden_ruta=orden, libro_ronda_ruta=libro,
                           v10=nada, vuelta_mejora=nada, plan_cierre=nada)
                assert isinstance(r, dict) and r["motivo"], r
            # Basura en la foto y el panel, con el reloj bueno: tampoco lanza.
            foto = _la_foto()
            foto["my_team"] = [5, {"id": "x"}, {"id": 12, "price": "x"}]
            foto["catalog"] = {"data": {"players": {"12": "x", "y": {}}}}
            r = _correr(carpeta, cycle={"snapshot": foto},
                        status={"lineup": {"players": [{"id": 1}]}, "roster": 5})
            assert isinstance(r, dict) and r["motivo"], r
            r = correr(cycle={}, ahora=AHORA, calendario="x", orden_ruta=orden,
                       libro_ronda_ruta=libro, status={}, v10={}, vuelta_mejora={},
                       plan_cierre={})
            assert r["motivo"] == "SIN_CALENDARIO", r
            # El escritor revienta: queda en `hechas` con el error, no lanza.
            r = _correr(carpeta, escritor_factory=_EscritorQueRevienta)
            assert r["motivo"] == "EJECUTADA" and all(h.get("error") for h in r["hechas"]), r
            # La fabrica revienta: el motivo lo dice.
            r = _correr(carpeta, escritor_factory=lambda: 1 / 0)
            assert r["motivo"].startswith("ERROR"), r
    finally:
        _entorno(**antes)


TESTS = [
    test_vende_al_dudoso_fuera_del_once_desde_el_95,
    test_no_vende_por_debajo_del_95,
    test_lo_publica_si_no_esta_publicado,
    test_nunca_toca_once_yamal_protegidos_conservados_ni_cartera,
    test_nada_con_una_ronda_jugandose,
    test_nada_sin_el_once_escrito_y_lo_dice,
    test_encendido_de_punta_a_punta,
    test_nace_apagado,
    test_nunca_lanza_con_basura,
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
