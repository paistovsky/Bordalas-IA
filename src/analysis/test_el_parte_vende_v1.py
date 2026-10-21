"""
EL PARTE VENDE (17/10/2026; arreglos del 21/10/2026). Guardias de
`src/actions/el_parte_vende.py` (`BORDALAS_EL_PARTE_VENDE`, paso 4 del
laboratorio).

    1. Vende al de parte malo ('doubt', 'injured') que no esta en el
       once escrito si la oferta del Computer llega al 95 % de su valor;
       por debajo, no.
    2. Si no esta publicado, lo publica a su valor.
    3. Nunca toca al once escrito (el del panel y el de Biwenger), a
       Yamal, a los protegidos, a los `conservar`, a lo de la cartera ni
       a lo vendido en esta vuelta.
    4. Con una ronda jugandose, en la zona de silencio o sin calendario,
       nada.
    5. Sin el once escrito del panel, nada, y lo dice.
    6. Nace apagado (lo apaga esta guardia, no el entorno) y nunca lanza.
    7. (21/10, D1) Un fichaje de hace menos de 7 dias no se toca
       (`RECIEN_FICHADO`: el caso de Gaya), ni uno sin fecha de fichaje
       (`SIN_FECHA_DE_FICHAJE`: tablon ilegible, atrasado o que va por
       detras). La fecha sale del tablon, con sus formas de verdad.
    8. (21/10, D2) Sin el once de Biwenger (`user_lineup` None o vacio)
       tampoco se hace nada (`SIN_ONCE_DE_BIWENGER`), y lo dice.
    9. (21/10, D3) El sancionado se mira y no se vende (`SANCION`).

Todo con datos de mentira: la hora se pasa siempre, el calendario es un
dict de este fichero, la orden y el libro de la ronda se escriben en una
carpeta temporal, el tablon es una lista de este fichero y el escritor
es de mentira. No se lee el estado de produccion, ni el reloj, ni se
sale a la red.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.el_parte_vende import (     # noqa: E402
    AVISOS, DIAS_DE_FICHAJE, ENV, MALOS, MOTIVOS, SANCIONADO, SUELO, activa, correr,
    decidir, el_parte, el_suelo, el_ultimo_reset, ids_del_once, las_fechas_de_fichaje,
    lo_vendido_y_publicado, por_que_no,
)


AHORA = datetime(2026, 10, 14, 18, 7, tzinfo=timezone.utc)      # mie 20:07 Madrid
EN_CURSO = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)   # sab, la J9 jugandose
SILENCIO = datetime(2026, 10, 15, 3, 30, tzinfo=timezone.utc)   # jue 05:30 Madrid

# El reset de la liga (el `leagueReset` de verdad, 09/08) y el ultimo
# reset del Computer antes de AHORA (el `until` de sus ventas es el
# proximo, 24 h despues).
RESET_LIGA = datetime(2026, 8, 9, 12, 27, 26, tzinfo=timezone.utc)
ULTIMO_RESET = datetime(2026, 10, 14, 5, 0, tzinfo=timezone.utc)
PROXIMO_RESET = ULTIMO_RESET + timedelta(days=1)
# Nuestro desde hace mucho (el reparto).
VIEJO = RESET_LIGA


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
#            (comprado por nosotros en subasta el 20/09)
#     14     sancionado, 3 M, publicado, oferta de 2.849.999        -> no se toca
#            (D3, 21/10: SANCION; antes, NADA por la oferta)
#     15     en duda, 1 M, oferta de 949.999, sin publicar          -> se publica
#            (comprado a un manager el 01/10)
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
#
# Los que no tienen compra en el tablon son del reparto (nuestros desde
# el reset de la liga).

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

# El fichaje de la puja del dueño (D1): Gaya (1844) se resuelve el 22/10
# a las 05:00 UTC. Aqui, el 26, ganado en la subasta del ultimo reset.
GAYA = _j(26, "Gaya", "doubt", 1_700_000)


def _la_foto(once_de_biwenger=True):
    foto = {
        "league": {"user": {"id": 99}},
        "market": {
            "status": {"balance": 1_000_000, "maximumBid": 20_000_000},
            "sales": [{"player": {"id": p}, "user": {"id": 99}, "price": 3_100_000}
                      for p in PUBLICADOS]
            + [{"player": {"id": 500}, "user": None, "price": 1_000_000,
                "until": int(PROXIMO_RESET.timestamp())}],
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


def _con_gaya(foto, oferta=1_700_000):
    """La foto con el fichaje de hoy en la plantilla, en duda y con una
    oferta del Computer que llega al 95 %."""
    foto["my_team"].append({"id": GAYA["id"], "price": GAYA["price"]})
    foto["catalog"]["data"]["players"][str(GAYA["id"])] = {
        "name": GAYA["name"], "status": GAYA["status"], "price": GAYA["price"]}
    foto["market"]["offers"].append({"id": 726, "status": "waiting", "amount": oferta,
                                     "requestedPlayers": [{"id": GAYA["id"]}],
                                     "from": None})
    return foto


def _el_status(con_once=True):
    status = {"roster": {"players": [{"id": p["id"], "name": p["name"]} for p in PLANTILLA]}}
    if con_once:
        status["lineup"] = {"players": [{"id": i, "name": f"Titular {i}"} for i in sorted(ONCE)]}
    return status


# ------------------------------------------------------------------
# EL TABLON DE MENTIRA, CON LAS FORMAS DEL DE VERDAD
# ------------------------------------------------------------------
#
# `data/rival_intelligence/board_events.json` es una lista de eventos
# `{event_id, date (epoch), type, content}`. Una subasta ganada es un
# 'market' con `content[].to`; una venta al Computer, un 'transfer' con
# solo `from`; una compra entre managers, un 'transfer' con `from` y `to`.

NOSOTROS = {"id": 99, "name": "Pepe"}
RIVAL = {"id": 77, "name": "Rival"}


def _ev(eid, tipo, cuando, content):
    return {"event_id": eid, "date": int(cuando.timestamp()), "type": tipo,
            "fixed": False, "title": "", "author": None, "content": content}


def _el_tablon(*extra, con_reset=True, subastas_de_hoy=True, gaya=False):
    eventos = []
    if con_reset:
        eventos.append({"event_id": "reset", "date": int(RESET_LIGA.timestamp()),
                        "type": "leagueReset", "fixed": False, "title": "",
                        "author": RIVAL, "content": {"type": "full", "distribution": 12}})
    eventos += [
        # El 13, ganado en subasta hace semanas.
        _ev("m13", "market", datetime(2026, 9, 20, 5, 5, tzinfo=timezone.utc),
            [{"player": 13, "to": NOSOTROS, "amount": 900_000,
              "bids": [{"user": RIVAL, "amount": 880_000}]}]),
        # El 15, comprado a un manager.
        _ev("t15", "transfer", datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
            [{"player": 15, "from": RIVAL, "to": NOSOTROS, "amount": 1_000_000}]),
        # Un rival vende al Computer y apuesta (ruido).
        _ev("t601", "transfer", datetime(2026, 10, 10, 23, 0, tzinfo=timezone.utc),
            [{"player": 601, "from": RIVAL, "amount": 500_000}]),
        _ev("b1", "bettingPool", datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc),
            {"id": 1}),
    ]
    if subastas_de_hoy:
        hoy = [{"player": 600, "to": RIVAL, "amount": 1_000_000}]
        if gaya:
            hoy.append({"player": GAYA["id"], "to": NOSOTROS, "amount": 1_711_008,
                        "bids": [{"user": RIVAL, "amount": 1_650_000}]})
        # Las subastas del ultimo reset del Computer (05:00), a las 05:04.
        eventos.append(_ev("m-hoy", "market", ULTIMO_RESET + timedelta(minutes=4), hoy))
    return eventos + list(extra)


TABLON = _el_tablon()


# Lo que esta vuelta ya hizo: el cierre cobro al 23 y el escaparate
# publico al 24.
V10 = {"timestamp": AHORA.isoformat(),
       "escaparate": {"listed": [{"player_id": 24, "sent": True, "success": True}]}}
PLAN_CIERRE = {"generated_at": AHORA.isoformat(),
               "hechas": [{"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 23,
                           "exito": True}]}


def _d(**k):
    """`decidir` con la plantilla de mentira, ya leida: el once del panel
    (1-11) y el de Biwenger (1-11 y el 25), y todos nuestros desde el
    reparto."""
    base = dict(
        plantilla={p["id"] for p in PLANTILLA},
        estados={p["id"]: p["status"] for p in PLANTILLA},
        nombres={p["id"]: p["name"] for p in PLANTILLA},
        precios={p["id"]: p["price"] for p in PLANTILLA},
        ofertas_del_computer={p: {"offer_id": o, "amount": a} for p, (o, a) in OFERTAS.items()},
        en_venta=set(PUBLICADOS) | {24},
        once_escrito=ONCE, once_de_biwenger=ONCE | {25},
        protegidos={18}, conservados={19}, aguanta={21}, vendidos={23},
        fichajes={p["id"]: VIEJO for p in PLANTILLA}, ahora=AHORA,
    )
    base.update(k)
    return decidir(**base)


def _uno(estado="doubt", oferta=950_000, **k):
    """`decidir` con un solo suplente (el 7, 1 M), fuera de los dos onces
    y nuestro desde el reparto."""
    base = dict(plantilla={7}, estados={7: estado}, nombres={7: "Suplente"},
                precios={7: 1_000_000},
                ofertas_del_computer={7: {"offer_id": 70, "amount": oferta}},
                once_escrito={1}, once_de_biwenger={1}, fichajes={7: VIEJO}, ahora=AHORA)
    base.update(k)
    return decidir(**base)


def _acciones(d, accion=None):
    return sorted((a["accion"], a["player_id"]) for a in d["acciones"]
                  if accion is None or a["accion"] == accion)


def _escrituras(d):
    return sorted((a["accion"], a["player_id"]) for a in d["acciones"]
                  if a["accion"] != "NADA")


def _por(d):
    return {n["player_id"]: n["por"] for n in d["no_se_tocan"]}


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
                libro_ronda_ruta=libro, v10=V10, vuelta_mejora={}, plan_cierre=PLAN_CIERRE,
                tablon=TABLON)
    base.update(k)
    return correr(**base)


# ------------------------------------------------------------------
# 1. VENDE DESDE EL 95 %, Y POR DEBAJO NO
# ------------------------------------------------------------------

def test_vende_al_dudoso_fuera_del_once_desde_el_95():
    assert SUELO == 0.95 and MALOS == {"doubt", "injured"}
    assert el_suelo(2_000_000) == 1_900_000 and el_suelo(1_000_001) == 950_001
    assert el_suelo(0) is None and el_suelo("x") is None
    d = _d()
    assert d["activo"] and d["motivo"] is None, d
    venta = [a for a in d["acciones"] if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"]
    assert [(a["player_id"], a["offer_id"], a["importe"], a["suelo"]) for a in venta] == [
        (12, 712, 1_900_000, 1_900_000)], d["acciones"]
    # Los dos partes valen: en duda y lesionado (el sancionado, no: D3).
    for estado in ("doubt", "injured", " Injured "):
        d = _uno(estado)
        assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], (estado, d)
    # Las claves en texto (como vienen de un JSON) tambien, y la fecha en ISO.
    d = decidir(plantilla=["7"], estados={"7": "doubt"}, nombres={"7": "Suplente"},
                precios={"7": "1000000"},
                ofertas_del_computer={"7": {"offer_id": "70", "amount": "1000000"}},
                once_escrito=["1"], once_de_biwenger=["1"],
                fichajes={"7": VIEJO.isoformat()}, ahora=AHORA.isoformat())
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d


def test_no_vende_por_debajo_del_95():
    # 14, si estuviera en duda: publicado y la oferta se queda a 1 euro del
    # 95 %: nada, y dice por que. (Sancionado, ni se mira la oferta: D3.)
    d = _d(estados={**{p["id"]: p["status"] for p in PLANTILLA}, 14: "doubt"})
    nada = {a["player_id"]: a for a in d["acciones"] if a["accion"] == "NADA"}
    assert 14 in nada and "95 %" in nada[14]["motivo"], d["acciones"]
    assert 14 not in {a["player_id"] for a in d["acciones"] if a["accion"] != "NADA"}
    d = _d()
    # 15: oferta por debajo y sin publicar: se publica, no se cobra.
    assert ("PONER_A_LA_VENTA", 15) in _acciones(d)
    assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 15) not in _acciones(d)
    # Sin offer_id no se puede aceptar.
    d = _uno(ofertas_del_computer={7: {"amount": 2_000_000}}, en_venta={7})
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
    d = _uno(precios={}, oferta=5_000_000)
    assert _escrituras(d) == [] and d["no_se_tocan"][0]["por"] == "SIN_VALOR", d


# ------------------------------------------------------------------
# 2. A QUIEN NUNCA
# ------------------------------------------------------------------

def test_nunca_toca_once_yamal_protegidos_conservados_ni_cartera():
    d = _d()
    tocados = {a["player_id"] for a in d["acciones"]}
    assert tocados == {12, 13, 15, 24}, d["acciones"]
    por = _por(d)
    assert por == {3: "ONCE_ESCRITO", 4: "ONCE_ESCRITO", 14: "SANCION", 18: "PROTEGIDO",
                   19: "CONSERVAR", 20: "YAMAL", 21: "LA_CARTERA",
                   23: "VENDIDO_EN_ESTA_VUELTA", 25: "ONCE_ESCRITO"}, por
    # 'ok', 'warned' y sin estado ni se miran.
    assert not {16, 17, 22} & (tocados | set(por)) and set(d["malos"]) == tocados | set(por)
    # Yamal por su nombre, se escriba como se escriba, y sin nombre no se vende.
    for nombre in ("Yamal", "LAMINE YAMAL", ["Lamine", "L. Yamal"]):
        d = _uno("injured", oferta=2_000_000, nombres={7: nombre})
        assert d["acciones"] == [] and d["no_se_tocan"][0]["por"] == "YAMAL", (nombre, d)
    d = _uno("injured", oferta=2_000_000, nombres={})
    assert d["acciones"] == [] and d["no_se_tocan"][0]["por"] == "SIN_NOMBRE", d
    # Un titular del once escrito no se vende NUNCA, ni con la mejor oferta.
    d = _d(ofertas_del_computer={i: {"offer_id": i, "amount": 99_000_000} for i in range(1, 26)})
    assert not {a["player_id"] for a in d["acciones"]} & (ONCE | {25}), d["acciones"]
    assert not {a["player_id"] for a in d["acciones"]} & {14, 18, 19, 20, 21, 23}
    # El titular del de Biwenger tampoco aunque el panel lo haya quitado.
    d = _d(once_escrito=ONCE - {3}, once_de_biwenger=ONCE)
    assert _por(d)[3] == "ONCE_ESCRITO" and 3 not in {a["player_id"] for a in d["acciones"]}


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
            por = _por(r["decision"])
            assert por[20] == "YAMAL" and por[21] == "LA_CARTERA" and por[25] == "ONCE_ESCRITO"
            assert por[18] == "PROTEGIDO" and por[19] == "CONSERVAR" and por[14] == "SANCION"
            assert por[23] == "VENDIDO_EN_ESTA_VUELTA", por
            # El tablon esta al dia: sin aviso.
            assert "aviso_del_tablon" not in r, r.get("aviso_del_tablon")
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
    assert "ni a un sancionado" in QUE_HACE[ENV] and "7 días" in QUE_HACE[ENV], QUE_HACE[ENV]


def test_nunca_lanza_con_basura():
    for basura in (None, "x", 5, [1, 2], {"a": object()}, object()):
        d = decidir(plantilla=basura, estados=basura, nombres=basura, precios=basura,
                    ofertas_del_computer=basura, en_venta=basura, once_escrito=basura,
                    once_de_biwenger=basura, protegidos=basura, conservados=basura,
                    aguanta=basura, vendidos=basura, fichajes=basura, ahora=basura,
                    en_curso=False, puede_escribir=True, sin_calendario=False)
        assert isinstance(d, dict) and d["acciones"] == [], d
        por_que_no(puede_escribir=basura, sin_calendario=basura, en_curso=basura,
                   once_escrito=basura, once_de_biwenger=basura)
        el_parte(basura)
        ids_del_once(basura)
        el_suelo(basura)
        assert el_ultimo_reset(basura) is None
        assert el_ultimo_reset({"market": basura}) is None
        assert el_ultimo_reset({"market": {"sales": basura}}) is None
        f = las_fechas_de_fichaje(basura, basura, basura, basura)
        assert f["fechas"] == {} and f["aviso"] == "SIN_TABLON", f
        v = lo_vendido_y_publicado(basura, basura, basura, basura, basura)
        assert v["vendidos"] == set() and v["listados"] == set(), v
    d = decidir(plantilla=[7, "x", None], estados={7: "doubt", "x": 5},
                nombres={7: 5}, precios={7: "mucho"},
                ofertas_del_computer={7: "x"}, once_escrito={1}, once_de_biwenger={1},
                fichajes={7: "ayer", "x": object()}, ahora=AHORA)
    assert isinstance(d, dict) and _escrituras(d) == [], d
    # Eventos rotos en el tablon: los que se entienden cuentan, el resto no.
    f = las_fechas_de_fichaje([None, 5, {"type": "market", "date": "x"},
                               {"type": "market", "date": 10**20, "content": 5},
                               {"type": "transfer", "date": int(VIEJO.timestamp()),
                                "content": [{"player": {"id": 13}, "to": 5}, "x"]}]
                              + TABLON, 99, {13, 21}, ULTIMO_RESET)
    assert f["fechas"] == {13: datetime(2026, 9, 20, 5, 5, tzinfo=timezone.utc),
                           21: RESET_LIGA}, f
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden, libro = _ficheros(carpeta)
            for basura in (None, "x", 5, [1, 2], {"snapshot": "x"}, {"snapshot": {"my_team": 5}}):
                # (None seria «leelo de produccion»: aqui, vacio.)
                nada = {} if basura is None else basura
                r = correr(cycle=nada, escritor_factory=_Escritor, ahora=AHORA, status=nada,
                           calendario=CAL, orden_ruta=orden, libro_ronda_ruta=libro,
                           v10=nada, vuelta_mejora=nada, plan_cierre=nada, tablon=nada)
                assert isinstance(r, dict) and r["motivo"], r
            # Basura en la foto y el panel, con el reloj bueno: tampoco lanza.
            foto = _la_foto()
            foto["my_team"] = [5, {"id": "x"}, {"id": 12, "price": "x"}]
            foto["catalog"] = {"data": {"players": {"12": "x", "y": {}}}}
            r = _correr(carpeta, cycle={"snapshot": foto},
                        status={"lineup": {"players": [{"id": 1}]}, "roster": 5})
            assert isinstance(r, dict) and r["motivo"], r
            for tablon in ("x", 5, [1, 2], {"events": "x"}):
                r = _correr(carpeta, tablon=tablon)
                assert isinstance(r, dict) and r["motivo"], r
            r = correr(cycle={}, ahora=AHORA, calendario="x", orden_ruta=orden,
                       libro_ronda_ruta=libro, status={}, v10={}, vuelta_mejora={},
                       plan_cierre={}, tablon=[])
            assert r["motivo"] == "SIN_CALENDARIO", r
            # El escritor revienta: queda en `hechas` con el error, no lanza.
            r = _correr(carpeta, escritor_factory=_EscritorQueRevienta)
            assert r["motivo"] == "EJECUTADA" and all(h.get("error") for h in r["hechas"]), r
            # La fabrica revienta: el motivo lo dice.
            r = _correr(carpeta, escritor_factory=lambda: 1 / 0)
            assert r["motivo"].startswith("ERROR"), r
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 6. LOS ARREGLOS DEL 21/10/2026
# ------------------------------------------------------------------

def test_d1_el_fichaje_no_se_revende_antes_de_jugar():
    """El caso de Gaya: la puja del dueño se resuelve el 22/10 a las 05:00
    UTC; llega en duda y fuera del once. Antes, el parte lo publicaba el
    jueves y lo vendia el viernes, antes de la J10."""
    assert DIAS_DE_FICHAJE == 7
    llega = datetime(2026, 10, 22, 5, 0, tzinfo=timezone.utc)
    for ahora in (datetime(2026, 10, 22, 18, 0, tzinfo=timezone.utc),    # jue 20:00
                  datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc),    # vie, antes de la J10
                  llega + timedelta(days=7, minutes=-1)):
        # Con oferta que llega al 95 %: no se cobra.
        d = _uno(oferta=1_000_000, fichajes={7: llega}, ahora=ahora)
        assert d["acciones"] == [] and d["no_se_tocan"] == [
            {"player_id": 7, "nombre": "Suplente", "estado": "doubt",
             "por": "RECIEN_FICHADO", "fichado": llega.isoformat()}], (ahora, d)
        # Sin oferta y sin publicar: tampoco se publica (haria nacer la
        # oferta del proximo reset).
        d = _uno(ofertas_del_computer={}, fichajes={7: llega}, ahora=ahora)
        assert d["acciones"] == [] and _por(d) == {7: "RECIEN_FICHADO"}, (ahora, d)
        assert d["malos"] == [7], d
    # A los 7 dias justos ya es uno mas (y uno que llegara "del futuro",
    # por un reloj torcido, sigue siendo recien fichado).
    d = _uno(fichajes={7: llega}, ahora=llega + timedelta(days=7))
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d
    d = _uno(fichajes={7: llega}, ahora=llega - timedelta(hours=1))
    assert _por(d) == {7: "RECIEN_FICHADO"}, d
    # En la plantilla de mentira: el 12 recien llegado ya no se cobra.
    d = _d(fichajes={**{p["id"]: VIEJO for p in PLANTILLA}, 12: AHORA - timedelta(days=2)})
    assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 12) not in _acciones(d)
    assert _por(d)[12] == "RECIEN_FICHADO", _por(d)
    # Las otras puertas van antes: un recien fichado del once es ONCE_ESCRITO.
    d = _d(fichajes={**{p["id"]: VIEJO for p in PLANTILLA}, 3: AHORA})
    assert _por(d)[3] == "ONCE_ESCRITO", _por(d)

    # De punta a punta: Gaya ganado en las subastas de hoy (el tablon lo trae).
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": _con_gaya(_la_foto())},
                        tablon=_el_tablon(gaya=True))
            assert r["motivo"] == "EJECUTADA", r
            assert _escrituras(r["decision"]) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 12),
                                                  ("PONER_A_LA_VENTA", 13),
                                                  ("PONER_A_LA_VENTA", 15)], r["acciones"]
            assert _por(r["decision"])[26] == "RECIEN_FICHADO", r["decision"]["no_se_tocan"]
            assert ("accept_offer", {"offer_id": 726, "execute": True}) not in _Escritor.llamadas
            assert any("RECIEN_FICHADO" in linea and "26" in linea for linea in el_parte(r))
            # Sin el evento de su subasta (el tablon de la vuelta anterior,
            # si la peticion de esta fallo) tampoco: el tablon no esta al dia
            # y Gaya no tiene fecha. Los del reparto esperan; el 13 y el 15,
            # con su compra en el tablon, siguen.
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": _con_gaya(_la_foto())},
                        tablon=_el_tablon(subastas_de_hoy=False))
            por = _por(r["decision"])
            assert por[26] == "SIN_FECHA_DE_FICHAJE" and por[12] == "SIN_FECHA_DE_FICHAJE", por
            assert _escrituras(r["decision"]) == [("PONER_A_LA_VENTA", 13),
                                                  ("PONER_A_LA_VENTA", 15)], r["acciones"]
            assert r["aviso_del_tablon"] == "TABLON_ATRASADO", r
            assert any("TABLON_ATRASADO" in linea for linea in el_parte(r))
    finally:
        _entorno(**antes)


def test_d1_sin_fecha_de_fichaje_no_se_vende():
    # decidir: sin fechas (fuente ilegible), sin la suya o sin hora, nada.
    for k in (dict(fichajes=None), dict(fichajes={}), dict(ahora=None),
              dict(fichajes={p["id"]: "x" for p in PLANTILLA})):
        d = _d(**k)
        assert _escrituras(d) == [] and [a for a in d["acciones"]] == [], (k, d)
        por = _por(d)
        assert {12, 13, 15, 24} <= set(por) and all(
            por[p] == "SIN_FECHA_DE_FICHAJE" for p in (12, 13, 15, 24)), (k, por)
        assert por[3] == "ONCE_ESCRITO" and por[14] == "SANCION", por
    d = _uno(fichajes={8: VIEJO})
    assert d["acciones"] == [] and _por(d) == {7: "SIN_FECHA_DE_FICHAJE"}, d

    # El tablon, con las formas del de verdad (medido el 21/10): Sergi
    # Cardona (30493) lo vendio Mex al Computer el 02/09 y lo ganamos en
    # la subasta del 17/10; Luismi Cruz (25777), en la del 14/10.
    yo = 14175949
    pepe = {"id": yo, "name": "Pepe Bordalás", "icon": "i/u/14175949.png"}
    mex = {"id": 14178736, "name": "Mex"}
    luismi_haz = {"id": 14156489, "name": "Luismi_Haz", "icon": "icons/11.png"}
    reset = {"event_id": "233126199d2e0d8066c093df", "date": 1786278446,
             "type": "leagueReset", "fixed": False, "title": "",
             "author": {"id": 14145555, "name": "Pollo17", "icon": "icons/13.png"},
             "content": {"type": "full", "distribution": 12}}
    de_verdad = [
        reset,
        {"event_id": "40e70c46f633dc263540a753", "date": 1788343070, "type": "transfer",
         "fixed": False, "title": "", "author": None,
         "content": [{"player": 30493, "from": mex, "amount": 1126200}]},
        {"event_id": "086e748f5bc59190b8f2f56d", "date": 1791954183, "type": "market",
         "fixed": False, "title": "", "author": None,
         "content": [{"player": 25777, "to": pepe, "amount": 3252000}]},
        {"event_id": "5fc7cb95c5b62001ab53f304", "date": 1792213538, "type": "market",
         "fixed": False, "title": "", "author": None,
         "content": [{"player": 30493, "to": pepe, "amount": 919000,
                      "bids": [{"user": luismi_haz, "amount": 912000}]}]},
    ]
    hoy = datetime(2026, 10, 21, 8, 0, tzinfo=timezone.utc)
    f = las_fechas_de_fichaje(de_verdad, yo, {30493, 25777, 1844}, ultimo_reset=None)
    assert f["fechas"] == {
        30493: datetime(2026, 10, 17, 5, 5, 38, tzinfo=timezone.utc),
        25777: datetime(2026, 10, 14, 5, 3, 3, tzinfo=timezone.utc)}, f
    # Sin saber el ultimo reset, al que no se movio no se le da fecha.
    assert f["aviso"] == "TABLON_ATRASADO" and 1844 not in f["fechas"], f
    d = decidir(plantilla={30493, 25777}, estados={30493: "doubt", 25777: "injured"},
                nombres={30493: "Sergi Cardona", 25777: "Luismi Cruz"},
                precios={30493: 1_190_000, 25777: 2_870_000},
                ofertas_del_computer={30493: {"offer_id": 1, "amount": 1_190_000}},
                once_escrito={1}, once_de_biwenger={1}, fichajes=f["fechas"], ahora=hoy)
    assert _por(d) == {30493: "RECIEN_FICHADO"} and _acciones(d) == [
        ("PONER_A_LA_VENTA", 25777)], d

    # Del reparto: nuestro desde el reset, solo con el tablon al dia.
    f = las_fechas_de_fichaje(TABLON, 99, {13, 15, 21}, ULTIMO_RESET)
    assert f == {"fechas": {13: datetime(2026, 9, 20, 5, 5, tzinfo=timezone.utc),
                            15: datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
                            21: RESET_LIGA}, "aviso": None}, f
    for tablon, tope, aviso in ((_el_tablon(con_reset=False), ULTIMO_RESET,
                                 "SIN_RESET_EN_EL_TABLON"),
                                (_el_tablon(subastas_de_hoy=False), ULTIMO_RESET,
                                 "TABLON_ATRASADO"),
                                (TABLON, None, "TABLON_ATRASADO"),
                                (TABLON, ULTIMO_RESET + timedelta(days=1),
                                 "TABLON_ATRASADO")):
        f = las_fechas_de_fichaje(tablon, 99, {13, 15, 21}, tope)
        assert 21 not in f["fechas"] and f["aviso"] == aviso and aviso in AVISOS, f
        assert set(f["fechas"]) == {13, 15}, f
    # Ilegible o vacio: nadie tiene fecha.
    for tablon in (None, "x", [], {}, {"events": []}, [{"type": "bettingPool"}]):
        f = las_fechas_de_fichaje(tablon, 99, {13, 21}, ULTIMO_RESET)
        assert f["fechas"] == {} and f["aviso"] in AVISOS, (tablon, f)
    assert las_fechas_de_fichaje(TABLON, None, {13}, ULTIMO_RESET)["aviso"] == "SIN_TABLON"
    # El tablon va por detras: lo ultimo que dice es que se fue, o que lo
    # compro otro, y hoy es nuestro. Sin fecha.
    se_fue = _ev("t13", "transfer", datetime(2026, 10, 5, 22, 0, tzinfo=timezone.utc),
                 [{"player": 13, "from": NOSOTROS, "amount": 950_000}])
    de_otro = _ev("m21", "market", datetime(2026, 10, 6, 5, 3, tzinfo=timezone.utc),
                  [{"player": 21, "to": RIVAL, "amount": 1_000_000}])
    f = las_fechas_de_fichaje(_el_tablon(se_fue, de_otro), 99, {13, 21}, ULTIMO_RESET)
    assert f["fechas"] == {}, f
    # Vendido y vuelto a comprar: cuenta la ultima compra.
    vuelve = _ev("m13b", "market", datetime(2026, 10, 12, 5, 4, tzinfo=timezone.utc),
                 [{"player": 13, "to": NOSOTROS, "amount": 970_000}])
    f = las_fechas_de_fichaje(_el_tablon(se_fue, vuelve), 99, {13}, ULTIMO_RESET)
    assert f["fechas"] == {13: datetime(2026, 10, 12, 5, 4, tzinfo=timezone.utc)}, f
    # Lo de antes del reset es de otra temporada: no cuenta.
    viejo = _ev("m21-viejo", "market", RESET_LIGA - timedelta(days=30),
                [{"player": 21, "to": RIVAL, "amount": 1}])
    f = las_fechas_de_fichaje(_el_tablon(viejo), 99, {21}, ULTIMO_RESET)
    assert f["fechas"] == {21: RESET_LIGA}, f
    # El ultimo reset sale del `until` de las ventas del Computer.
    assert el_ultimo_reset(_la_foto()) == ULTIMO_RESET
    sin_computer = _la_foto()
    sin_computer["market"]["sales"] = [s for s in sin_computer["market"]["sales"] if s["user"]]
    assert el_ultimo_reset(sin_computer) is None and el_ultimo_reset({}) is None

    # De punta a punta: tablon ilegible o vacio, y foto sin el reset.
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            for tablon in ("x", [], {"events": []}):
                _limpiar()
                r = _correr(carpeta, tablon=tablon)
                assert r["motivo"] == "NADA_QUE_HACER" and _Escritor.creados == 0, r
                por = _por(r["decision"])
                assert all(por[p] == "SIN_FECHA_DE_FICHAJE" for p in (12, 13, 15, 24)), por
                assert r["aviso_del_tablon"] == "SIN_TABLON", r
                assert any("SIN_TABLON" in linea for linea in el_parte(r))
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": sin_computer})
            assert r["aviso_del_tablon"] == "TABLON_ATRASADO", r
            assert _escrituras(r["decision"]) == [("PONER_A_LA_VENTA", 13),
                                                  ("PONER_A_LA_VENTA", 15)], r["acciones"]
    finally:
        _entorno(**antes)


def test_d2_hacen_falta_los_dos_onces():
    assert por_que_no(once_escrito={1}, once_de_biwenger=set()) == "SIN_ONCE_DE_BIWENGER"
    assert por_que_no(once_escrito={1}, once_de_biwenger=None) is None
    assert por_que_no(once_escrito=set(), once_de_biwenger=set()) == "SIN_ONCE_ESCRITO"
    assert "SIN_ONCE_DE_BIWENGER" in MOTIVOS and "Biwenger" in MOTIVOS["SIN_ONCE_DE_BIWENGER"]
    for k in (dict(once_de_biwenger=set()), dict(once_de_biwenger=None),
              dict(once_de_biwenger="x")):
        d = _d(**k)
        assert d["acciones"] == [] and d["motivo"] == "SIN_ONCE_DE_BIWENGER", (k, d)
    d = _uno(once_de_biwenger=frozenset())
    assert d["acciones"] == [] and d["motivo"] == "SIN_ONCE_DE_BIWENGER", d
    d = _d(once_escrito=set(), once_de_biwenger=set())
    assert d["motivo"] == "SIN_ONCE_ESCRITO", d

    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            # El caso de la revision: el 3 (titular en duda) sigue en el once
            # de Biwenger, y el panel ya lo ha quitado. Con los dos onces, no
            # se toca; sin el de Biwenger (GET /user fallo), antes se vendia.
            status = _el_status()
            status["lineup"]["players"] = [p for p in status["lineup"]["players"]
                                           if p["id"] != 3]
            _limpiar()
            r = _correr(carpeta, status=status)
            assert _por(r["decision"])[3] == "ONCE_ESCRITO", r["decision"]["no_se_tocan"]
            assert 3 not in {a["player_id"] for a in r["acciones"]}, r["acciones"]
            sin_biwenger = []
            for user_lineup in (None, {}, {"data": None}, {"data": {"lineup": None}},
                                {"data": {"lineup": {"players": []}}}, "x"):
                foto = _la_foto()
                foto["user_lineup"] = user_lineup
                sin_biwenger.append(foto)
            sin_biwenger.append(_la_foto(once_de_biwenger=False))
            for foto in sin_biwenger:
                _limpiar()
                r = _correr(carpeta, cycle={"snapshot": foto}, status=status)
                assert r["motivo"] == "SIN_ONCE_DE_BIWENGER" and r["acciones"] == [], r
                assert r["decision"] is None and r["hechas"] == [], r
                assert _Escritor.creados == 0 and _Escritor.llamadas == [], r
                assert r["detalle"] == MOTIVOS["SIN_ONCE_DE_BIWENGER"], r
                assert any("SIN_ONCE_DE_BIWENGER" in linea and "Biwenger" in linea
                           for linea in el_parte(r)), el_parte(r)
            # Con el panel vacio (y el de Biwenger bien) tampoco: SIN_ONCE_ESCRITO.
            for status in ({"lineup": {"players": []}}, {"lineup": None}):
                _limpiar()
                r = _correr(carpeta, status=status)
                assert r["motivo"] == "SIN_ONCE_ESCRITO" and r["acciones"] == [], r
                assert _Escritor.creados == 0, r
                assert any("SIN_ONCE_ESCRITO" in linea for linea in el_parte(r))
    finally:
        _entorno(**antes)


def test_d3_el_sancionado_no_se_vende():
    assert SANCIONADO == "sanctioned" and SANCIONADO not in MALOS
    for estado in ("sanctioned", " Sanctioned "):
        d = _uno(estado, oferta=5_000_000)
        assert d["acciones"] == [] and d["malos"] == [7], (estado, d)
        assert d["no_se_tocan"] == [{"player_id": 7, "nombre": "Suplente",
                                     "estado": "sanctioned", "por": "SANCION"}], d
        # Sin publicar y sin oferta: tampoco se publica.
        d = _uno(estado, ofertas_del_computer={})
        assert d["acciones"] == [] and _por(d) == {7: "SANCION"}, d
    # El 14 de la plantilla de mentira (publicado, oferta de 2.849.999): ni
    # NADA, ni se cobra aunque la oferta llegue.
    d = _d(ofertas_del_computer={14: {"offer_id": 714, "amount": 9_000_000}})
    assert 14 not in {a["player_id"] for a in d["acciones"]} and _por(d)[14] == "SANCION"
    assert 14 in d["malos"], d["malos"]
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta)
            assert _por(r["decision"])[14] == "SANCION"
            assert 14 not in {a["player_id"] for a in r["acciones"]}
            assert ("accept_offer", {"offer_id": 714, "execute": True}) not in _Escritor.llamadas
            assert any("SANCION" in linea and "14" in linea for linea in el_parte(r))
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
    test_d1_el_fichaje_no_se_revende_antes_de_jugar,
    test_d1_sin_fecha_de_fichaje_no_se_vende,
    test_d2_hacen_falta_los_dos_onces,
    test_d3_el_sancionado_no_se_vende,
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
