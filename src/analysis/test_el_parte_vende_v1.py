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
   10. (21/10, segunda revision, H1) Un fichaje no se toca hasta que
       acaba la primera ronda que empezo despues de su llegada, y
       nunca antes de 7 dias (`SIN_JUGAR_CON_NOSOTROS`): el fichaje
       del paron de noviembre, el de Navidad y el que llega con la J10
       empezada. Sin ninguna ronda despues de su llegada, no se toca
       (`SIN_RONDA_TRAS_EL_FICHAJE`). Al del reparto no le cambia nada.
   11. (21/10, segunda revision, H2) Con el tablon atrasado nadie tiene
       fecha y no se vende a nadie (el vendido y recomprado ya no pasa
       por nuestro desde la primera compra); un dia sin subasta, un
       movimiento de 2 h despues del reset dice que esta al dia.

Todo con datos de mentira: la hora se pasa siempre, el calendario es un
dict de este fichero (con la J8 ya jugada antes de AHORA: sin una ronda
jugada despues de su llegada no se vende a nadie), la orden y el libro
de la ronda se escriben en una carpeta temporal, el tablon es una lista
de este fichero y el escritor es de mentira. No se lee el estado de
produccion, ni el reloj, ni se sale a la red.
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
    AVISOS, DIAS_DE_FICHAJE, ENV, MALOS, MARGEN_DEL_TABLON, MARGEN_FINAL, MOTIVOS,
    PARTIDOS_DE_RONDA, SANCIONADO, SUELO, activa, correr, decidir, el_parte, el_suelo,
    el_ultimo_reset, hasta_cuando_no_se_toca, ids_del_once, las_fechas_de_fichaje,
    lo_vendido_y_publicado, por_que_no,
)
from src.analysis.la_proxima_jornada import las_rondas     # noqa: E402


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


# La J8 (09-12/10) ya se jugo antes de AHORA: es la ronda que "jugaron"
# con nosotros los del reparto y los fichajes de la plantilla de mentira
# (sin ella, nadie habria jugado una ronda desde su llegada y no se
# venderia a nadie: H1). La J9 empieza el viernes 16/10 a las 21:00 de
# Madrid y acaba el lunes 19/10; la J10, del 23 al 26/10; la J11, del 30/10
# al 02/11. La J12 acaba el 08/11; el paron de noviembre; la J13, del 20
# al 23/11. La J17 acaba el 20/12; el de Navidad; la J18, del 02 al 04/01.
CAL = {"matchdays": [
    {"matchday": 8, "matches": [
        _p(8, 1, 2, "2026-10-09T21:00:00+02:00"),
        _p(8, 3, 4, "2026-10-10T16:15:00+02:00"),
        _p(8, 5, 6, "2026-10-11T14:00:00+02:00"),
        _p(8, 7, 8, "2026-10-11T18:30:00+02:00"),
        _p(8, 9, 10, "2026-10-12T21:00:00+02:00"),
    ]},
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
    {"matchday": 11, "matches": [
        _p(11, 2, 7, "2026-10-30T21:00:00+01:00"),
        _p(11, 4, 9, "2026-10-31T16:15:00+01:00"),
        _p(11, 6, 1, "2026-11-01T14:00:00+01:00"),
        _p(11, 8, 3, "2026-11-01T18:30:00+01:00"),
        _p(11, 10, 5, "2026-11-02T21:00:00+01:00"),
    ]},
    {"matchday": 12, "matches": [
        _p(12, 1, 3, "2026-11-06T21:00:00+01:00"),
        _p(12, 5, 7, "2026-11-07T16:15:00+01:00"),
        _p(12, 9, 2, "2026-11-07T18:30:00+01:00"),
        _p(12, 4, 6, "2026-11-08T14:00:00+01:00"),
        _p(12, 8, 10, "2026-11-08T21:00:00+01:00"),
    ]},
    {"matchday": 13, "matches": [
        _p(13, 3, 5, "2026-11-20T21:00:00+01:00"),
        _p(13, 7, 9, "2026-11-21T16:15:00+01:00"),
        _p(13, 2, 4, "2026-11-22T14:00:00+01:00"),
        _p(13, 6, 8, "2026-11-22T18:30:00+01:00"),
        _p(13, 10, 1, "2026-11-23T21:00:00+01:00"),
    ]},
    {"matchday": 17, "matches": [
        _p(17, 1, 5, "2026-12-18T21:00:00+01:00"),
        _p(17, 2, 6, "2026-12-19T16:15:00+01:00"),
        _p(17, 3, 7, "2026-12-19T18:30:00+01:00"),
        _p(17, 4, 8, "2026-12-20T14:00:00+01:00"),
        _p(17, 9, 10, "2026-12-20T21:00:00+01:00"),
    ]},
    {"matchday": 18, "matches": [
        _p(18, 5, 2, "2027-01-02T16:15:00+01:00"),
        _p(18, 6, 3, "2027-01-02T18:30:00+01:00"),
        _p(18, 7, 4, "2027-01-03T14:00:00+01:00"),
        _p(18, 8, 9, "2027-01-03T18:30:00+01:00"),
        _p(18, 10, 1, "2027-01-04T21:00:00+01:00"),
    ]},
]}
# Las rondas de ese calendario, como se las pasa `correr` a `decidir`.
RONDAS = las_rondas(CAL)


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


def _la_foto(once_de_biwenger=True, proximo_reset=PROXIMO_RESET):
    foto = {
        "league": {"user": {"id": 99}},
        "market": {
            "status": {"balance": 1_000_000, "maximumBid": 20_000_000},
            "sales": [{"player": {"id": p}, "user": {"id": 99}, "price": 3_100_000}
                      for p in PUBLICADOS]
            + [{"player": {"id": 500}, "user": None, "price": 1_000_000,
                "until": int(proximo_reset.timestamp())}],
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


def _con_fichaje(foto, ficha, offer_id, oferta):
    """La foto con un fichaje mas en la plantilla y una oferta del
    Computer por el."""
    foto["my_team"].append({"id": ficha["id"], "price": ficha["price"]})
    foto["catalog"]["data"]["players"][str(ficha["id"])] = {
        "name": ficha["name"], "status": ficha["status"], "price": ficha["price"]}
    foto["market"]["offers"].append({"id": offer_id, "status": "waiting", "amount": oferta,
                                     "requestedPlayers": [{"id": ficha["id"]}],
                                     "from": None})
    return foto


def _con_gaya(foto, oferta=1_700_000):
    """La foto con el fichaje de hoy en la plantilla, en duda y con una
    oferta del Computer que llega al 95 %."""
    return _con_fichaje(foto, GAYA, 726, oferta)


# El fichaje del paron de noviembre (H1): en duda, 3 M, oferta de 2,9 M.
PARON = _j(27, "Fichaje del paron", "doubt", 3_000_000)


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


def _el_tablon(*extra, con_reset=True, subastas_de_hoy=True, gaya=False, hoy=ULTIMO_RESET):
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
        ganadas = [{"player": 600, "to": RIVAL, "amount": 1_000_000}]
        if gaya:
            ganadas.append({"player": GAYA["id"], "to": NOSOTROS, "amount": 1_711_008,
                            "bids": [{"user": RIVAL, "amount": 1_650_000}]})
        # Las subastas del ultimo reset del Computer (05:00), a las 05:04.
        eventos.append(_ev("m-hoy", "market", hoy + timedelta(minutes=4), ganadas))
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
    (1-11) y el de Biwenger (1-11 y el 25), todos nuestros desde el
    reparto y las rondas del calendario de mentira (la J8, jugada)."""
    base = dict(
        plantilla={p["id"] for p in PLANTILLA},
        estados={p["id"]: p["status"] for p in PLANTILLA},
        nombres={p["id"]: p["name"] for p in PLANTILLA},
        precios={p["id"]: p["price"] for p in PLANTILLA},
        ofertas_del_computer={p: {"offer_id": o, "amount": a} for p, (o, a) in OFERTAS.items()},
        en_venta=set(PUBLICADOS) | {24},
        once_escrito=ONCE, once_de_biwenger=ONCE | {25},
        protegidos={18}, conservados={19}, aguanta={21}, vendidos={23},
        fichajes={p["id"]: VIEJO for p in PLANTILLA}, ahora=AHORA, rondas=RONDAS,
    )
    base.update(k)
    return decidir(**base)


def _uno(estado="doubt", oferta=950_000, **k):
    """`decidir` con un solo suplente (el 7, 1 M), fuera de los dos onces
    y nuestro desde el reparto."""
    base = dict(plantilla={7}, estados={7: estado}, nombres={7: "Suplente"},
                precios={7: 1_000_000},
                ofertas_del_computer={7: {"offer_id": 70, "amount": oferta}},
                once_escrito={1}, once_de_biwenger={1}, fichajes={7: VIEJO}, ahora=AHORA,
                rondas=RONDAS)
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


def _el_reset_de(ahora):
    """El ultimo reset del Computer (05:00 UTC) antes de `ahora`."""
    reset = ahora.replace(hour=5, minute=0, second=0, microsecond=0)
    return reset if reset <= ahora else reset - timedelta(days=1)


def _el_dia(ahora, ficha=None, llega=None, offer_id=None, oferta=None):
    """La foto y el tablon de una vuelta de otro dia: el `until` del
    Computer y las subastas de hoy son los de `ahora`. Con `ficha`, ese
    fichaje esta en la plantilla, ganado en la subasta de `llega`."""
    reset = _el_reset_de(ahora)
    foto = _la_foto(proximo_reset=reset + timedelta(days=1))
    extra = []
    if ficha is not None:
        foto = _con_fichaje(foto, ficha, offer_id, oferta)
        extra.append(_ev(f"m{ficha['id']}", "market", llega,
                         [{"player": ficha["id"], "to": NOSOTROS, "amount": ficha["price"]}]))
    return {"cycle": {"snapshot": foto}, "tablon": _el_tablon(*extra, hoy=reset),
            "ahora": ahora, "v10": {}, "plan_cierre": {}}


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
                fichajes={"7": VIEJO.isoformat()}, ahora=AHORA.isoformat(),
                rondas=[{**r, "inicio": r["inicio"].isoformat(), "fin": r["fin"].isoformat()}
                        for r in RONDAS])
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
    assert "no ha jugado una ronda" in QUE_HACE[ENV], QUE_HACE[ENV]       # H1
    assert "tablón atrasado, a nadie" in QUE_HACE[ENV], QUE_HACE[ENV]     # H2


def test_nunca_lanza_con_basura():
    for basura in (None, "x", 5, [1, 2], {"a": object()}, object()):
        d = decidir(plantilla=basura, estados=basura, nombres=basura, precios=basura,
                    ofertas_del_computer=basura, en_venta=basura, once_escrito=basura,
                    once_de_biwenger=basura, protegidos=basura, conservados=basura,
                    aguanta=basura, vendidos=basura, fichajes=basura, ahora=basura,
                    rondas=basura, en_curso=False, puede_escribir=True,
                    sin_calendario=False)
        assert isinstance(d, dict) and d["acciones"] == [], d
        assert hasta_cuando_no_se_toca(basura, basura) is None
        assert hasta_cuando_no_se_toca(VIEJO, basura) is None
        # Rondas rotas con un buen jugador: no se sabe, no se vende.
        d = _uno(rondas=basura)
        assert d["acciones"] == [] and _por(d) == {7: "SIN_RONDA_TRAS_EL_FICHAJE"}, d
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
                fichajes={7: "ayer", "x": object()}, ahora=AHORA,
                rondas=[None, 5, {"inicio": "x"}, {"inicio": AHORA, "fin": "y"}] + RONDAS)
    assert isinstance(d, dict) and _escrituras(d) == [], d
    assert hasta_cuando_no_se_toca(VIEJO, [None, 5, {"inicio": "x", "fin": 3, "partidos": 9},
                                           {"inicio": object(), "partidos": "x"}]) is None
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
        # Con oferta que llega al 95 %: no se cobra. Hasta los 7 dias (la
        # J10, su primera ronda, acaba antes: H1).
        d = _uno(oferta=1_000_000, fichajes={7: llega}, ahora=ahora)
        assert d["acciones"] == [] and d["no_se_tocan"] == [
            {"player_id": 7, "nombre": "Suplente", "estado": "doubt",
             "por": "RECIEN_FICHADO", "fichado": llega.isoformat(),
             "hasta": (llega + timedelta(days=7)).isoformat()}], (ahora, d)
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
            # y Gaya no tiene fecha. Y desde la segunda revision (H2) nadie:
            # el 13 y el 15, con su compra en el tablon, antes se vendian.
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": _con_gaya(_la_foto())},
                        tablon=_el_tablon(subastas_de_hoy=False))
            por = _por(r["decision"])
            assert all(por[p] == "SIN_FECHA_DE_FICHAJE" for p in (12, 13, 15, 24, 26)), por
            assert _escrituras(r["decision"]) == [] and r["motivo"] == "NADA_QUE_HACER", r
            assert _Escritor.creados == 0, r
            assert r["aviso_del_tablon"] == "TABLON_ATRASADO", r
            assert any("TABLON_ATRASADO" in linea and "NADIE" in linea for linea in el_parte(r))
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
    # Sin saber el ultimo reset no se sabe si esta al dia: nadie tiene
    # fecha (H2; antes, la tenian los que se habian movido).
    f = las_fechas_de_fichaje(de_verdad, yo, {30493, 25777, 1844}, ultimo_reset=None)
    assert f == {"fechas": {}, "aviso": "TABLON_ATRASADO"}, f
    # Con la foto del 17/10 (su reset, a las 05:00 UTC) esta al dia: la
    # subasta de Sergi Cardona es de las 05:05:38.
    f = las_fechas_de_fichaje(de_verdad, yo, {30493, 25777, 1844},
                              ultimo_reset=datetime(2026, 10, 17, 5, 0, tzinfo=timezone.utc))
    assert f["aviso"] is None and f["fechas"] == {
        30493: datetime(2026, 10, 17, 5, 5, 38, tzinfo=timezone.utc),
        25777: datetime(2026, 10, 14, 5, 3, 3, tzinfo=timezone.utc),
        1844: datetime.fromtimestamp(1786278446, timezone.utc)}, f
    # El 21/10, con la J9 (16-19/10) jugada: Luismi Cruz, nuestro desde el
    # 14/10, ya jugo una ronda; Sergi Cardona, del 17/10, no lleva 7 dias.
    d = decidir(plantilla={30493, 25777}, estados={30493: "doubt", 25777: "injured"},
                nombres={30493: "Sergi Cardona", 25777: "Luismi Cruz"},
                precios={30493: 1_190_000, 25777: 2_870_000},
                ofertas_del_computer={30493: {"offer_id": 1, "amount": 1_190_000}},
                once_escrito={1}, once_de_biwenger={1}, fichajes=f["fechas"], ahora=hoy,
                rondas=RONDAS)
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
        # Sin el reset, los que se movieron; atrasado, nadie (H2).
        assert set(f["fechas"]) == ({13, 15} if aviso == "SIN_RESET_EN_EL_TABLON"
                                    else set()), f
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
            # La foto no dice cuando fue el reset: no se sabe si el tablon
            # esta al dia y no se vende a nadie (H2; antes, al 13 y al 15).
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": sin_computer})
            assert r["aviso_del_tablon"] == "TABLON_ATRASADO", r
            assert _escrituras(r["decision"]) == [] and _Escritor.creados == 0, r["acciones"]
            assert _por(r["decision"])[13] == "SIN_FECHA_DE_FICHAJE", r["decision"]
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


# ------------------------------------------------------------------
# 7. LA SEGUNDA REVISION DEL 21/10/2026
# ------------------------------------------------------------------

UTC = timezone.utc


def _fin(jornada, rondas=RONDAS):
    """Cuando se da por jugada la ronda principal de `jornada` (en UTC,
    como la escribe `decidir`)."""
    fin = [r["fin"] for r in rondas if r["jornada"] == jornada and not r["aparte"]][0]
    return (fin + MARGEN_FINAL).astimezone(UTC)


def test_h1_el_fichaje_no_se_vende_sin_jugar_una_ronda():
    """E14: «un fichaje para el once no se revende antes de jugar con
    nosotros». Los cuatro de -3,3 M se vendieron en un paron: con el
    reloj de 7 dias solo, el fichaje del 10/11 se vendia el 17/11, sin
    haber jugado la J13."""
    from src.analysis.la_proxima_jornada import MARGEN_FINAL as MARGEN_DE_LA_JORNADA

    assert MARGEN_FINAL == MARGEN_DE_LA_JORNADA == timedelta(hours=3)
    assert PARTIDOS_DE_RONDA == 5

    # La cuenta, pura. Al del reparto le vale la J8 (ya jugada).
    assert hasta_cuando_no_se_toca(VIEJO, RONDAS) == _fin(8) < AHORA
    # Gaya llega el 22/10 a las 05:00 UTC, antes del cierre de la J10: la
    # J10 acaba antes de los 7 dias, y mandan los 7 dias.
    gaya = datetime(2026, 10, 22, 5, 0, tzinfo=UTC)
    assert hasta_cuando_no_se_toca(gaya, RONDAS) == gaya + timedelta(days=7) > _fin(10)
    # El que llega justo cuando empieza una ronda no la juega: la siguiente.
    j10 = [r for r in RONDAS if r["jornada"] == 10][0]
    assert hasta_cuando_no_se_toca(j10["inicio"], RONDAS) == _fin(11)
    # Sin rondas, o sin ninguna que empiece despues de su llegada: no se sabe.
    llega = datetime(2026, 11, 10, 5, 4, tzinfo=UTC)
    hasta_la_j12 = [r for r in RONDAS if r["jornada"] <= 12]
    for rondas in (None, [], hasta_la_j12):
        assert hasta_cuando_no_se_toca(llega, rondas) is None, rondas
    assert hasta_cuando_no_se_toca(None, RONDAS) is None
    # Y en decidir: SIN_RONDA_TRAS_EL_FICHAJE (sin rondas, ni al del reparto).
    d = _uno(fichajes={7: llega}, ahora=datetime(2026, 11, 17, 10, 7, tzinfo=UTC),
             rondas=hasta_la_j12)
    assert d["acciones"] == [] and d["no_se_tocan"] == [
        {"player_id": 7, "nombre": "Suplente", "estado": "doubt",
         "por": "SIN_RONDA_TRAS_EL_FICHAJE", "fichado": llega.isoformat()}], d
    for rondas in (None, []):
        d = _d(rondas=rondas)
        assert d["acciones"] == [] and {p: "SIN_RONDA_TRAS_EL_FICHAJE" for p in (12, 13, 15, 24)
                                        }.items() <= _por(d).items(), _por(d)

    # EL PARON DE NOVIEMBRE: ganado en la subasta del 10/11 (la J12 acabo
    # el 08/11), en duda y fuera del once. El 17/11 lleva 7 dias y no ha
    # jugado: no se toca hasta que acaba la J13 (23/11 a las 21:00 CET).
    oferta = {7: {"offer_id": 70, "amount": 990_000}}
    for ahora in (datetime(2026, 11, 17, 10, 7, tzinfo=UTC),       # el caso de la revision
                  datetime(2026, 11, 20, 18, 0, tzinfo=UTC),       # antes de la J13
                  _fin(13) - timedelta(minutes=1)):
        d = _uno(ofertas_del_computer=oferta, fichajes={7: llega}, ahora=ahora)
        assert d["acciones"] == [] and d["no_se_tocan"] == [
            {"player_id": 7, "nombre": "Suplente", "estado": "doubt",
             "por": "SIN_JUGAR_CON_NOSOTROS", "fichado": llega.isoformat(),
             "hasta": _fin(13).isoformat()}], (ahora, d)
    d = _uno(ofertas_del_computer=oferta, fichajes={7: llega}, ahora=_fin(13))
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d

    # Un aplazado suelto en el paron (aparte) o una jornada de la que el
    # calendario solo guarda un partido (como la J6 de hoy) no cuentan.
    cal = {"matchdays": [m for m in CAL["matchdays"] if m["matchday"] in (12, 13)] + [
        {"matchday": 5, "matches": [_p(5, 1, 2, "2026-09-12T18:30:00+02:00"),
                                    _p(5, 3, 4, "2026-09-13T14:00:00+02:00"),
                                    _p(5, 5, 6, "2026-09-13T18:30:00+02:00"),
                                    _p(5, 7, 8, "2026-09-14T21:00:00+02:00"),
                                    _p(5, 9, 10, "2026-11-18T19:00:00+01:00")]},
        {"matchday": 6, "matches": [_p(6, 3, 8, "2026-11-19T19:00:00+01:00")]},
    ]}
    rondas = las_rondas(cal)
    sueltas = [r for r in rondas if r["jornada"] in (5, 6) and r["inicio"] > llega]
    assert len(sueltas) == 2 and sueltas[0]["aparte"] and sueltas[1]["partidos"] == 1, rondas
    assert hasta_cuando_no_se_toca(llega, rondas) == _fin(13, rondas) == _fin(13)

    # UNA JORNADA PARTIDA 5/5 (revision del 21/10): la mitad aplazada tiene
    # 5 partidos, asi que solo `aparte` la deja fuera. El que llega entre
    # las dos mitades no se vende al acabar la mitad aplazada (su equipo
    # puede no jugarla): espera a la J21.
    partida = {"matchdays": [
        {"matchday": 20, "matches": (
            [_p(20, i, i + 10, f"2027-01-{16 + i // 2:02d}T18:00:00+01:00") for i in range(5)]
            + [_p(20, i + 5, i + 15, f"2027-02-0{3 + i // 3}T21:00:00+01:00") for i in range(5)])},
        {"matchday": 21, "matches": [
            _p(21, i, i + 10, f"2027-02-{12 + i // 2:02d}T18:00:00+01:00") for i in range(10)]},
    ]}
    rondas = las_rondas(partida)
    mitad = [r for r in rondas if r["jornada"] == 20 and r["aparte"]]
    assert len(mitad) == 1 and mitad[0]["partidos"] == PARTIDOS_DE_RONDA, rondas
    entre = datetime(2027, 1, 20, 5, 4, tzinfo=UTC)
    assert hasta_cuando_no_se_toca(entre, rondas) == _fin(21, rondas), rondas
    d = _uno(ofertas_del_computer={7: {"offer_id": 70, "amount": 990_000}},
             fichajes={7: entre}, ahora=datetime(2027, 2, 6, 10, 0, tzinfo=UTC), rondas=rondas)
    assert d["acciones"] == [] and _por(d) == {7: "SIN_JUGAR_CON_NOSOTROS"}, d

    # NAVIDAD: la J17 acaba el 20/12 y la J18 empieza el 02/01. El fichaje
    # del 22/12 no se vende el 29/12; despues de la J18, si. El del 17/12,
    # que juega la J17, a los 7 dias.
    navidad = datetime(2026, 12, 22, 5, 4, tzinfo=UTC)
    d = _uno(fichajes={7: navidad}, ahora=datetime(2026, 12, 29, 10, 7, tzinfo=UTC))
    assert _por(d) == {7: "SIN_JUGAR_CON_NOSOTROS"} and d["acciones"] == [], d
    assert d["no_se_tocan"][0]["hasta"] == _fin(18).isoformat(), d
    d = _uno(fichajes={7: navidad}, ahora=datetime(2027, 1, 5, 10, 7, tzinfo=UTC))
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d
    antes_de_la_j17 = datetime(2026, 12, 17, 5, 4, tzinfo=UTC)
    assert hasta_cuando_no_se_toca(antes_de_la_j17, RONDAS) == antes_de_la_j17 + timedelta(days=7)

    # COMO GAYA, FUERA DEL ONCE EN LA J10: si llega con la J10 empezada
    # (la subasta del sabado 24/10), no la puede jugar con nosotros. El
    # jueves 29/10 no se toca (5 dias); el 01/11, con 7 dias, tampoco: no
    # ha acabado la J11. Despues de la J11, si.
    sabado = datetime(2026, 10, 24, 5, 4, tzinfo=UTC)
    assert hasta_cuando_no_se_toca(sabado, RONDAS) == _fin(11)
    for ahora, por in ((datetime(2026, 10, 29, 9, 7, tzinfo=UTC), "RECIEN_FICHADO"),
                       (datetime(2026, 11, 1, 12, 0, tzinfo=UTC), "SIN_JUGAR_CON_NOSOTROS"),
                       (_fin(11) - timedelta(minutes=1), "SIN_JUGAR_CON_NOSOTROS")):
        d = _uno(oferta=1_000_000, fichajes={7: sabado}, ahora=ahora)
        assert d["acciones"] == [] and _por(d) == {7: por}, (ahora, d)
        assert d["no_se_tocan"][0]["hasta"] == _fin(11).isoformat(), d
    d = _uno(oferta=1_000_000, fichajes={7: sabado}, ahora=_fin(11))
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d
    # LO QUE EL CALENDARIO NO VE: si llega el 22/10, antes del cierre de la
    # J10, la J10 cuenta como jugada aunque se quedara fuera del once (no
    # hay libro de los onces de cada ronda): desde el 29/10 a las 05:00 UTC.
    d = _uno(oferta=1_000_000, fichajes={7: gaya},
             ahora=gaya + timedelta(days=7, minutes=-1))
    assert _por(d) == {7: "RECIEN_FICHADO"}, d
    d = _uno(oferta=1_000_000, fichajes={7: gaya}, ahora=datetime(2026, 10, 29, 9, 7, tzinfo=UTC))
    assert _acciones(d) == [("ACEPTAR_OFERTA_DEL_COMPUTER", 7)], d

    # De punta a punta, con el tablon y la foto de cada dia.
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            # El paron: el 17/11 no se toca al 27; a los del reparto, si.
            _limpiar()
            r = _correr(carpeta, **_el_dia(datetime(2026, 11, 17, 10, 7, tzinfo=UTC),
                                           PARON, llega, 727, 2_900_000))
            assert r["motivo"] == "EJECUTADA" and not r.get("aviso_del_tablon"), r
            assert _por(r["decision"])[27] == "SIN_JUGAR_CON_NOSOTROS", r["decision"]
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 12) in _escrituras(r["decision"]), r
            assert 27 not in {a["player_id"] for a in r["acciones"]}, r["acciones"]
            assert ("accept_offer", {"offer_id": 727, "execute": True}) not in _Escritor.llamadas
            assert any("SIN_JUGAR_CON_NOSOTROS" in linea and "27" in linea
                       and _fin(13).isoformat() in linea for linea in el_parte(r)), el_parte(r)
            # Acabada la J13, se vende.
            _limpiar()
            r = _correr(carpeta, **_el_dia(datetime(2026, 11, 24, 10, 7, tzinfo=UTC),
                                           PARON, llega, 727, 2_900_000))
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 27) in _escrituras(r["decision"]), r
            assert ("accept_offer", {"offer_id": 727, "execute": True}) in _Escritor.llamadas

            # Como Gaya: ganado el sabado 24/10, con la J10 jugandose.
            gaya_del_sabado = dict(ficha=GAYA, llega=sabado, offer_id=726, oferta=1_700_000)
            _limpiar()
            r = _correr(carpeta, **_el_dia(datetime(2026, 10, 29, 9, 7, tzinfo=UTC),
                                           **gaya_del_sabado))
            assert _por(r["decision"])[26] == "RECIEN_FICHADO", r["decision"]
            assert ("accept_offer", {"offer_id": 726, "execute": True}) not in _Escritor.llamadas
            _limpiar()
            r = _correr(carpeta, **_el_dia(datetime(2026, 11, 1, 12, 0, tzinfo=UTC),
                                           **gaya_del_sabado))
            assert r["motivo"] == "JORNADA_EN_CURSO" and _Escritor.creados == 0, r
            _limpiar()
            r = _correr(carpeta, **_el_dia(datetime(2026, 11, 3, 9, 7, tzinfo=UTC),
                                           **gaya_del_sabado))
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 26) in _escrituras(r["decision"]), r
    finally:
        _entorno(**antes)


def test_h2_con_el_tablon_atrasado_no_se_vende_a_nadie():
    """Con el tablon atrasado, al que tenia un movimiento se le fechaba con
    el ultimo que traia el fichero. Jonny (1599), de verdad: nuestro desde
    el 10/08, vendido el 20/08 y recomprado en la subasta del 23/08; con el
    tablon parado el 20/08 se le daba por nuestro desde el 10/08."""
    assert MARGEN_DEL_TABLON == timedelta(hours=2)
    assert "NADIE" in AVISOS["TABLON_ATRASADO"], AVISOS["TABLON_ATRASADO"]

    # El 13 (comprado el 20/09) se vende al Computer el 20/10 a las 22:00 y
    # se recompra en la subasta del 21/10 (05:04). La peticion del tablon
    # falla desde el 20/10 a mediodia: el fichero se queda en las subastas
    # del 20/10 (05:04).
    hoy = datetime(2026, 10, 21, 5, 0, tzinfo=UTC)
    ahora = datetime(2026, 10, 21, 10, 7, tzinfo=UTC)
    ayer = _ev("m-ayer", "market", hoy - timedelta(days=1) + timedelta(minutes=4),
               [{"player": 600, "to": RIVAL, "amount": 1}])
    se_fue = _ev("t13", "transfer", datetime(2026, 10, 20, 22, 0, tzinfo=UTC),
                 [{"player": 13, "from": NOSOTROS, "amount": 950_000}])
    vuelve = _ev("m13-hoy", "market", hoy + timedelta(minutes=4),
                 [{"player": 13, "to": NOSOTROS, "amount": 1_000_000}])
    al_dia = _el_tablon(ayer, se_fue, vuelve, hoy=hoy)
    atrasado = _el_tablon(ayer, subastas_de_hoy=False)
    f = las_fechas_de_fichaje(al_dia, 99, {13, 21}, hoy)
    assert f == {"fechas": {13: hoy + timedelta(minutes=4), 21: RESET_LIGA}, "aviso": None}, f
    f = las_fechas_de_fichaje(atrasado, 99, {13, 21}, hoy)
    assert f == {"fechas": {}, "aviso": "TABLON_ATRASADO"}, f
    d = _d(fichajes=f["fechas"], ahora=ahora, vendidos=set())
    assert d["acciones"] == [] and all(
        _por(d)[p] == "SIN_FECHA_DE_FICHAJE" for p in (12, 13, 15, 23, 24)), _por(d)

    # UN DIA SIN SUBASTA (5 de 73): sin 'market' desde el reset, pero un
    # rival vende al Computer a las 07:43 UTC (como el 09/10): se pidio
    # despues, esta al dia. Justo a las 2 h, tambien; un minuto antes, no.
    sin_subasta = _el_tablon(subastas_de_hoy=False)

    def _vende_un_rival(despues, tipo="transfer"):
        return _ev(f"{tipo}-{despues}", tipo, ULTIMO_RESET + despues,
                   [{"player": 602, "from": RIVAL, "amount": 500_000}])

    base = {13: datetime(2026, 9, 20, 5, 5, tzinfo=UTC),
            15: datetime(2026, 10, 1, 10, 0, tzinfo=UTC), 21: RESET_LIGA}
    for despues in (timedelta(hours=2, minutes=43), MARGEN_DEL_TABLON):
        f = las_fechas_de_fichaje(sin_subasta + [_vende_un_rival(despues)], 99, {13, 15, 21},
                                  ULTIMO_RESET)
        assert f == {"fechas": base, "aviso": None}, (despues, f)
    f = las_fechas_de_fichaje(sin_subasta + [_vende_un_rival(MARGEN_DEL_TABLON
                                                             - timedelta(minutes=1))],
                              99, {13, 15, 21}, ULTIMO_RESET)
    assert f == {"fechas": {}, "aviso": "TABLON_ATRASADO"}, f
    # Solo cuentan 'market' y 'transfer': las porras, las encuestas y los
    # avisos llegan con fecha de atras (medido el 21/10: 2.545 veces).
    for tipo in ("bettingPool", "poll", "adminText", "bonus", "roundFinished"):
        f = las_fechas_de_fichaje(sin_subasta + [_ev(tipo, tipo, ULTIMO_RESET
                                                     + timedelta(hours=5), {"id": 1})],
                                  99, {13, 15, 21}, ULTIMO_RESET)
        assert f == {"fechas": {}, "aviso": "TABLON_ATRASADO"}, (tipo, f)
    # Sin saber el ultimo reset, ni con un movimiento de esta tarde.
    f = las_fechas_de_fichaje(sin_subasta + [_vende_un_rival(timedelta(hours=9))], 99,
                              {13, 15, 21}, None)
    assert f == {"fechas": {}, "aviso": "TABLON_ATRASADO"}, f

    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            # El vendido y recomprado, de punta a punta: con el tablon
            # atrasado no se vende a nadie (antes, el 13 por nuestro desde
            # el 20/09); al dia, el 13 es un recien fichado.
            vuelta = _el_dia(ahora)
            _limpiar()
            r = _correr(carpeta, **{**vuelta, "tablon": atrasado})
            assert r["motivo"] == "NADA_QUE_HACER" and _Escritor.creados == 0, r
            assert r["aviso_del_tablon"] == "TABLON_ATRASADO", r
            assert all(_por(r["decision"])[p] == "SIN_FECHA_DE_FICHAJE"
                       for p in (12, 13, 15, 23, 24)), r["decision"]
            assert any("TABLON_ATRASADO" in linea and "NADIE" in linea for linea in el_parte(r))
            _limpiar()
            r = _correr(carpeta, **{**vuelta, "tablon": al_dia})
            assert r["motivo"] == "EJECUTADA" and not r.get("aviso_del_tablon"), r
            assert _por(r["decision"])[13] == "RECIEN_FICHADO", r["decision"]
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 12) in _escrituras(r["decision"]), r
            # Un dia sin subasta, con un movimiento de las 07:43: se vende.
            _limpiar()
            r = _correr(carpeta, tablon=sin_subasta
                        + [_vende_un_rival(timedelta(hours=2, minutes=43))])
            assert r["motivo"] == "EJECUTADA" and not r.get("aviso_del_tablon"), r
            assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 12) in _escrituras(r["decision"]), r
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
    test_h1_el_fichaje_no_se_vende_sin_jugar_una_ronda,
    test_h2_con_el_tablon_atrasado_no_se_vende_a_nadie,
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
