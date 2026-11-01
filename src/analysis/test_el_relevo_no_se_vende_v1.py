"""
EL RELEVO NO SE VENDE (01/11/2026). Guardias de
`BORDALAS_EL_RELEVO_NO_SE_VENDE` (`la_mejora_del_once.el_relevo`) y de
sus tres enganches: el cierre de la jornada, el parte vende y las dos
aceptaciones del motor viejo (`autopilot_executor`: la oferta de
solvencia y la de antes de caducar).

EL CASO (parte del 01/11 19:10 y la medida del laboratorio del 01/11)

    La mejora del once tiene apuntados dos cambios: Juan Iglesias entra
    por Gaya, y Ramon Enriquez (el chollo del 30/10, adoptado) entra por
    Unai Lopez, que se vende para pagar a Iglesias. Su libro
    (`data/trading/la_mejora.json`) es {el que entra: {"sale": ...}}.
    Si alguien vende AL QUE ENTRA antes de que se venda el que sale, la
    mejora suelta el cambio (el que entra ya no esta: "sin relevo, el que
    sale se queda") y Unai NO se vende: la caja de la J12 se queda sin
    sus 2,6 M y la ronda puede empezar en rojo (0 puntos el once entero).

    El cierre lee el libro pero solo guarda al que SALE (`no_vender`);
    el que entra es un suplente mas. El mie 04/11 a las 07:15 (61,75 h
    de la J12), con Ivan perdido, Gaya y Ortiz vendidos, el premio
    minimo y Unai sin vender (caja -1.990.776), el unico candidato del
    cierre es Ramon, y su oferta (409.200) pasa el 90 %: lo vende. Y el
    motor viejo puede aceptar su oferta de madrugada (el cluster que
    caduca) porque Ramon no esta en `conservar`.

QUE SE COMPRUEBA

    1. NACE APAGADO, se lee en un solo sitio y tiene su frase.
    2. Apagado, los tres vendedores son los de main byte a byte: la
       huella de la bateria (el cierre, el parte y las dos aceptaciones
       del motor viejo, en 22 escenarios) medida en main@85e052e3 ANTES
       de tocar el codigo, una por version de Python (3.11 y 3.13).
    3. El libro se lee como lo lee la mejora (claves = el que entra,
       `sale` = el que sale), y con la plantilla, solo cuenta el cambio
       VIVO: el que entra es nuestro y el que sale aun tambien.
    4. Encendido, el mie 04/11 07:15 con la caja en rojo el cierre no
       vende a Ramon (apagado, si: lo de main).
    5. Con el cambio hecho (Unai vendido antes, o en esta misma vuelta)
       Ramon vuelve a ser uno mas y se vende como siempre.
    6. Uno que no esta en ningun cambio (Ortiz, de la cartera) se vende
       como siempre, encendido o no.
    7. Sin libro que leer (basura, o un fichero que no es JSON), lo de
       main, y el plan lo dice.
    8. El parte vende (apagado en produccion) no vende al relevo en duda
       el viernes; con el cambio hecho, si.
    9. El motor viejo no acepta la oferta del relevo, ni la de
       solvencia ni la de antes de caducar; la de otro, si.
   10. Nunca lanza.

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui. Los jugadores (id, nombre, puesto, precio,
    puntos, partidos, titularidad) son los del panel del artefacto de
    produccion de la run 41340081708 (01/11 19:10 UTC); la caja de cada
    escenario, la de la medida del 01/11 (E1, E1c). La liga y el
    calendario son de mentira (los equipos de verdad, la tabla y las
    fechas inventadas, con la J12 el viernes 06/11 a las 21:00 de
    Madrid). Ni la carpeta de estado, ni la red, ni el reloj: la hora se
    pasa siempre, los libros van en una carpeta temporal y los
    escritores son de mentira (el del motor viejo revienta antes de la
    red y del rastro).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Todo lo que mueve a
# los tres vendedores se quita aqui arriba; cada prueba pone lo suyo.
ENV = "BORDALAS_EL_RELEVO_NO_SE_VENDE"
ENV_CIERRE = "BORDALAS_EL_CIERRE_DE_LA_JORNADA"
ENV_PARTE = "BORDALAS_EL_PARTE_VENDE"
ENV_ORDEN = "BORDALAS_LA_ORDEN_DEL_GESTOR"
ENV_CARTERA = "BORDALAS_LA_CARTERA"
ENV_ROTACION = "BORDALAS_LA_ROTACION"
ENV_MEJORA = "BORDALAS_LA_MEJORA_DEL_ONCE"
for _nombre in (
    ENV, ENV_CIERRE, ENV_PARTE, ENV_ORDEN, ENV_CARTERA, ENV_ROTACION, ENV_MEJORA,
    "BORDALAS_LA_PUJA_EN_9900", "GITHUB_RUN_ID",
):
    os.environ.pop(_nombre, None)


from src.actions import el_cierre_de_la_jornada as cierre  # noqa: E402
from src.actions import el_parte_vende as parte  # noqa: E402
from src.actions import la_mejora_del_once as mejora  # noqa: E402


class _Interruptores:
    """Pone (valor) o quita (None) interruptores solo dentro del `with`."""

    def __init__(self, valores: dict):
        self.valores = dict(valores)

    def __enter__(self):
        self.antes = {n: os.environ.get(n) for n in self.valores}
        for nombre, valor in self.valores.items():
            if valor is None:
                os.environ.pop(nombre, None)
            else:
                os.environ[nombre] = valor
        return self

    def __exit__(self, *_):
        for nombre, valor in self.antes.items():
            if valor is None:
                os.environ.pop(nombre, None)
            else:
                os.environ[nombre] = valor
        return False


# Los de produccion que leen el cierre y el parte (bordalas-live.yml del
# 01/11; el parte, apagado alli, se enciende aqui para medirlo).
VENDEDORES = {ENV_CIERRE: "1", ENV_PARTE: "1", ENV_ORDEN: "1", ENV_CARTERA: "1",
              ENV_ROTACION: "1", ENV_MEJORA: "1", "GITHUB_RUN_ID": None,
              "BORDALAS_LA_PUJA_EN_9900": None}
APAGADO = {**VENDEDORES, ENV: None}
PUESTO = {**VENDEDORES, ENV: "1"}
# El motor viejo, sin la orden, la cartera ni la rotacion: sus
# `_conservados`, `_aguanta` y `_rota` leerian la orden y los libros de
# produccion (`config/`, `data/`). Asi solo pesa lo que se mide.
MOTOR_APAGADO = {ENV_ORDEN: None, ENV_CARTERA: None, ENV_ROTACION: None, ENV: None}
MOTOR_PUESTO = {**MOTOR_APAGADO, ENV: "1"}


# ============================================================
# LA PLANTILLA DEL 01/11 (artefacto de la run 41340081708)
# ============================================================

YO = 14175949

EQUIPOS = {
    "Barcelona": 1, "Real Madrid": 2, "Villarreal": 3, "Atlético": 4, "Betis": 5,
    "Espanyol": 6, "Sevilla": 7, "Elche": 8, "Alavés": 9, "Rayo Vallecano": 10,
    "Osasuna": 11, "Valencia": 12, "Levante": 13, "Málaga": 14,
}
PUNTOS_DE_LIGA = [28, 27, 22, 21, 18, 17, 15, 14, 13, 12, 11, 10, 8, 7]
TABLA = [
    {"rank": i + 1, "team": nombre, "biwenger_team_id": eid, "played": 10,
     "points": PUNTOS_DE_LIGA[i], "goals_for": 12, "goals_against": 12}
    for i, (nombre, eid) in enumerate(EQUIPOS.items())
]


def _j(pid, nombre, pos, equipo, precio, puntos, jugados, prob, status="ok"):
    return {"id": pid, "name": nombre, "position": pos, "team": equipo,
            "price": precio, "points": puntos, "played": jugados,
            "starter_probability": prob, "status": status}


GULACSI = _j(38433, "Gulácsi", 1, "Villarreal", 2_330_000, 31, 7, 90.0)
IGLESIAS = _j(23840, "Juan Iglesias", 2, "Sevilla", 3_750_000, 51, 10, 100.0)
KIKE = _j(28115, "Kike Salas", 2, "Sevilla", 3_300_000, 35, 8, 100.0)
CHUST = _j(1760, "Chust", 2, "Elche", 2_500_000, 41, 10, 90.0)
CARDONA = _j(30493, "Sergi Cardona", 2, "Villarreal", 2_100_000, 25, 7, 50.0)
GAYA = _j(1844, "Gayà", 2, "Valencia", 1_760_000, 27, 8, 80.0)
ORTIZ = _j(35765, "Angel Ortiz", 2, "Betis", 190_000, 17, 5, 30.0)
OLASAGASTI = _j(29661, "Olasagasti", 3, "Levante", 2_880_000, 54, 11, 80.0)
UNAI = _j(1969, "Unai López", 3, "Rayo Vallecano", 2_740_000, 53, 10, 80.0)
IBANEZ = _j(14800, "Pablo Ibáñez", 3, "Alavés", 2_670_000, 46, 11, 60.0)
DANI = _j(41418, "Dani Lorenzo", 3, "Málaga", 2_010_000, 39, 10, 70.0)
RAMON = _j(41411, "Ramón Enríquez", 3, "Málaga", 410_000, 25, 10, 60.0)
YAMAL = _j(26271, "Yamal", 4, "Barcelona", 25_310_000, 131, 11, 95.0)
ROBERTO = _j(35678, "Roberto Fernández", 4, "Espanyol", 7_240_000, 69, 11, 90.0)
BOYE = _j(12494, "Boyé", 4, "Alavés", 5_490_000, 63, 10, 90.0)

TODOS = [GULACSI, IGLESIAS, KIKE, CHUST, CARDONA, GAYA, ORTIZ, OLASAGASTI, UNAI,
         IBANEZ, DANI, RAMON, YAMAL, ROBERTO, BOYE]
POR_ID = {j["id"]: j for j in TODOS}

# El mie 04/11: Gaya y Ortiz vendidos el martes, Ivan perdido el lunes.
PLANTILLA_MIE = [GULACSI, IGLESIAS, KIKE, CHUST, CARDONA, OLASAGASTI, UNAI, IBANEZ,
                 DANI, RAMON, YAMAL, ROBERTO, BOYE]

# El once escrito del panel del 01/11 (3-4-3), ya con Iglesias por Gaya.
ONCE_343 = [GULACSI, IGLESIAS, KIKE, CHUST, UNAI, OLASAGASTI, IBANEZ, DANI, YAMAL,
            ROBERTO, BOYE]
# Sin Unai: el 4-3-3 con Cardona.
ONCE_433 = [GULACSI, IGLESIAS, KIKE, CHUST, CARDONA, OLASAGASTI, IBANEZ, DANI, YAMAL,
            ROBERTO, BOYE]

# El libro de la mejora: Iglesias por Gaya (la puja ganada el 01/11) y
# Ramon por Unai (adoptado de los chollos el 30/10).
LIBRO_MEJORA = {
    "23840": {"sale": 1844, "suelo": 1_584_000, "puja": 3_769_900, "puntos": 1.54},
    "41411": {"sale": 1969, "suelo": 2_466_000, "puntos": -0.68, "adoptado": True},
}

# Las ofertas del Computer {player_id: (offer_id, importe)}: la de Ramon
# (409.200, del artefacto) pasa el 90 % de su valor; la de Unai, no.
OFERTAS_MIE = {41411: (70411, 409_200), 1969: (70196, 2_350_000)}
PUBLICADOS = {41411, 1969}

# La caja de la medida del 01/11, escenario E1: -4.714.876 + 870.000
# (premio minimo) + 1.672.000 (Gaya) + 182.100 (Ortiz).
SALDO_E1 = -1_990_776

ORDEN = {
    "caduca": "2026-11-30T23:59:00+01:00",
    "proteger": [{"player_id": 26271, "nombre": "Yamal"}],
    "conservar": [{"player_id": 1969, "nombre": "Unai López"}],
}


# ============================================================
# EL CALENDARIO DE MENTIRA (J11 jugada; J12 el viernes 06/11 21:00)
# ============================================================

def _p(j, casa, fuera, cuando):
    return {"matchday": j, "home": casa, "away": fuera, "kickoff": cuando}


CAL = {"matchdays": [
    {"matchday": 11, "matches": [
        _p(11, "Málaga", "Valencia", "2026-10-30T21:00:00+01:00"),
        _p(11, "Barcelona", "Elche", "2026-10-31T16:15:00+01:00"),
        _p(11, "Villarreal", "Levante", "2026-10-31T18:30:00+01:00"),
        _p(11, "Sevilla", "Betis", "2026-11-01T14:00:00+01:00"),
        _p(11, "Espanyol", "Alavés", "2026-11-01T16:15:00+01:00"),
        _p(11, "Rayo Vallecano", "Atlético", "2026-11-01T18:30:00+01:00"),
        _p(11, "Osasuna", "Real Madrid", "2026-11-02T21:00:00+01:00"),
    ]},
    {"matchday": 12, "matches": [
        _p(12, "Sevilla", "Alavés", "2026-11-06T21:00:00+01:00"),
        _p(12, "Valencia", "Barcelona", "2026-11-07T16:15:00+01:00"),
        _p(12, "Málaga", "Villarreal", "2026-11-07T18:30:00+01:00"),
        _p(12, "Levante", "Espanyol", "2026-11-07T21:00:00+01:00"),
        _p(12, "Elche", "Rayo Vallecano", "2026-11-08T14:00:00+01:00"),
        _p(12, "Betis", "Osasuna", "2026-11-08T18:30:00+01:00"),
        _p(12, "Atlético", "Real Madrid", "2026-11-08T21:00:00+01:00"),
    ]},
    {"matchday": 13, "matches": [
        _p(13, "Alavés", "Málaga", "2026-11-20T21:00:00+01:00"),
        _p(13, "Barcelona", "Sevilla", "2026-11-21T16:15:00+01:00"),
        _p(13, "Villarreal", "Elche", "2026-11-21T18:30:00+01:00"),
        _p(13, "Espanyol", "Valencia", "2026-11-21T21:00:00+01:00"),
        _p(13, "Rayo Vallecano", "Levante", "2026-11-22T14:00:00+01:00"),
        _p(13, "Real Madrid", "Betis", "2026-11-22T18:30:00+01:00"),
        _p(13, "Osasuna", "Atlético", "2026-11-23T21:00:00+01:00"),
    ]},
    {"matchday": 14, "matches": [
        _p(14, "Málaga", "Sevilla", "2026-11-27T21:00:00+01:00"),
        _p(14, "Elche", "Alavés", "2026-11-28T16:15:00+01:00"),
        _p(14, "Levante", "Barcelona", "2026-11-28T18:30:00+01:00"),
        _p(14, "Valencia", "Villarreal", "2026-11-28T21:00:00+01:00"),
        _p(14, "Betis", "Rayo Vallecano", "2026-11-29T14:00:00+01:00"),
        _p(14, "Atlético", "Espanyol", "2026-11-29T18:30:00+01:00"),
        _p(14, "Real Madrid", "Osasuna", "2026-11-30T21:00:00+01:00"),
    ]},
]}

MIE = datetime(2026, 11, 4, 6, 15, tzinfo=timezone.utc)       # mie 04/11 07:15 Madrid
VIE = datetime(2026, 11, 6, 6, 15, tzinfo=timezone.utc)       # vie 06/11 07:15 Madrid


# ============================================================
# LO QUE LEEN EL CIERRE Y EL PARTE
# ============================================================

def _el_status(plantilla, once):
    roster = [{"id": j["id"], "name": j["name"], "position": j["position"],
               "team_name": j["team"], "price": j["price"], "points": j["points"],
               "played_home": j["played"] // 2, "played_away": j["played"] - j["played"] // 2,
               "starter_probability": j["starter_probability"], "status": j["status"]}
              for j in plantilla]
    liga = [{"id": j["id"], "name": j["name"], "position": j["position"],
             "team_id": EQUIPOS[j["team"]], "price": j["price"], "points": j["points"],
             "played": j["played"], "status": j["status"]} for j in TODOS]
    return {"league_center": {"laliga": {"standings": TABLA}},
            "todaLaLiga": {"players": liga}, "roster": {"players": roster},
            "libro_del_escaparate": {"players": []},
            "lineup": {"players": [{"id": j["id"], "name": j["name"]} for j in once]}}


def _la_foto(plantilla, saldo, ofertas, publicados, estados=None, once_de_biwenger=None,
             proximo_reset=None):
    estados = estados or {}
    ventas = [{"player": {"id": p}, "user": {"id": YO}, "price": POR_ID[p]["price"]}
              for p in sorted(publicados) if any(j["id"] == p for j in plantilla)]
    if proximo_reset is not None:
        # Las del Computer, con el `until` del proximo reset (el parte lo
        # lee para saber si el tablon esta al dia).
        ventas += [{"player": {"id": 900_000 + i}, "user": None, "price": 1_000_000,
                    "until": int(proximo_reset.timestamp())} for i in (1, 2)]
    foto = {
        "league": {"user": {"id": YO}},
        "market": {
            "status": {"balance": saldo, "maximumBid": 10_000_000},
            "sales": ventas,
            "offers": [{"id": o, "status": "waiting", "amount": a,
                        "requestedPlayers": [{"id": p}], "from": None}
                       for p, (o, a) in sorted(ofertas.items())
                       if any(j["id"] == p for j in plantilla)],
        },
        "my_team": [{"id": j["id"], "price": j["price"]} for j in plantilla],
        "catalog": {"data": {"players": {
            str(j["id"]): {"name": j["name"], "status": estados.get(j["id"], j["status"]),
                           "price": j["price"]} for j in plantilla}}},
    }
    if once_de_biwenger is not None:
        foto["user_lineup"] = {"data": {"lineup": {"players": [
            {"id": j["id"]} for j in once_de_biwenger]}}}
    return foto


class _Escritor:
    """El escritor de Biwenger, de mentira: apunta y dice que si."""

    llamadas: list = []

    def _ok(self, *a, **k):
        type(self).llamadas.append(k)
        return {"sent": True, "success": True, "http_status": 200}

    accept_offer = list_player_for_sale = cancel_bid = place_bid = _ok


def _sin(plantilla, *fuera):
    ids = {j["id"] for j in fuera}
    return [j for j in plantilla if j["id"] not in ids]


def _el_cierre(*, plantilla=None, saldo=SALDO_E1, once=None, libro=None, estados=None,
               ofertas=None, publicados=None, inventario=None, vuelta_mejora=None,
               run_id=None, en_ficheros=False, libro_crudo=None, sin_mejora=False):
    """
    `el_cierre_de_la_jornada.correr` el mie 04/11 07:15, con todo dado.
    `en_ficheros`: los libros se leen de sus ficheros (como en
    produccion), en la carpeta temporal; `libro_crudo`, el texto del de
    la mejora; `sin_mejora`, los libros dados sin el de la mejora.
    Devuelve la salida, el plan escrito y las escrituras.
    """
    plantilla = PLANTILLA_MIE if plantilla is None else plantilla
    once = ONCE_343 if once is None else once
    libro = LIBRO_MEJORA if libro is None else libro
    ofertas = OFERTAS_MIE if ofertas is None else ofertas
    publicados = PUBLICADOS if publicados is None else publicados
    ronda = {str(k): v for k, v in (inventario or {}).items()}
    _Escritor.llamadas = []
    with tempfile.TemporaryDirectory() as carpeta, _Interruptores({"GITHUB_RUN_ID": run_id}):
        carpeta = Path(carpeta)
        orden = carpeta / "orden.json"
        orden.write_text(json.dumps(ORDEN))
        plan = carpeta / "el_cierre.json"
        comun = dict(
            status=_el_status(plantilla, once),
            snapshot=_la_foto(plantilla, saldo, ofertas, publicados, estados),
            v10={}, calendario=CAL, orden_ruta=orden, escritor_factory=_Escritor,
            ahora=MIE, plan_ruta=plan,
        )
        if en_ficheros:
            rutas = {n: carpeta / f"{n}.json" for n in ("ronda", "chollos", "mejora",
                                                       "vuelta_mejora")}
            rutas["ronda"].write_text(json.dumps(ronda))
            rutas["chollos"].write_text("{}")
            rutas["mejora"].write_text(json.dumps(libro) if libro_crudo is None
                                       else libro_crudo)
            rutas["vuelta_mejora"].write_text(json.dumps(vuelta_mejora or {}))
            r = cierre.correr(libros=None, libros_rutas=rutas, **comun)
        else:
            libros = {"ronda": ronda, "chollos": {}, "mejora": libro,
                      "vuelta_mejora": vuelta_mejora or {}, "rotacion": {}}
            if sin_mejora:
                libros.pop("mejora")
            r = cierre.correr(libros=libros, **comun)
        escrito = json.loads(plan.read_text()) if plan.exists() else None
    return {"salida": r, "plan": escrito, "parte": cierre.el_parte(r),
            "escrituras": list(_Escritor.llamadas)}


# El tablon del parte: el reset de la liga, Ramon ganado en la subasta
# del 30/10 (el chollo, 369.000), Iglesias el 01/11 y las subastas del
# ultimo reset del Computer (el tablon esta al dia). El resto, del reparto.
RESET_LIGA = datetime(2026, 8, 9, 12, 27, 26, tzinfo=timezone.utc)


def _ev(eid, tipo, cuando, content):
    return {"event_id": eid, "date": int(cuando.timestamp()), "type": tipo,
            "fixed": False, "title": "", "author": None, "content": content}


def _el_tablon(hoy):
    nosotros, rival = {"id": YO, "name": "Pepe"}, {"id": 77, "name": "Rival"}
    return [
        {"event_id": "reset", "date": int(RESET_LIGA.timestamp()), "type": "leagueReset",
         "fixed": False, "title": "", "author": rival,
         "content": {"type": "full", "distribution": 12}},
        _ev("m-ramon", "market", datetime(2026, 10, 30, 5, 5, tzinfo=timezone.utc),
            [{"player": 41411, "to": nosotros, "amount": 369_000}]),
        _ev("m-iglesias", "market", datetime(2026, 11, 1, 5, 4, tzinfo=timezone.utc),
            [{"player": 23840, "to": nosotros, "amount": 3_769_900}]),
        _ev("m-hoy", "market", hoy + timedelta(minutes=4),
            [{"player": 900_100, "to": rival, "amount": 1_000_000}]),
    ]


def _el_parte(*, plantilla=None, estados=None, libro=None, once=None, ahora=VIE,
              ofertas=None, publicados=None):
    """`el_parte_vende.correr` el vie 06/11 07:15 (Ramon en duda), con todo
    dado. El libro de la mejora va junto al de la ronda (quien mueve los
    libros no lee los de produccion)."""
    plantilla = PLANTILLA_MIE if plantilla is None else plantilla
    estados = {41411: "doubt"} if estados is None else estados
    once = ONCE_343 if once is None else once
    reset = ahora.replace(hour=5, minute=0, second=0, microsecond=0)
    ofertas = OFERTAS_MIE if ofertas is None else ofertas
    publicados = PUBLICADOS if publicados is None else publicados
    _Escritor.llamadas = []
    with tempfile.TemporaryDirectory() as carpeta:
        carpeta = Path(carpeta)
        orden = carpeta / "orden.json"
        orden.write_text(json.dumps(ORDEN))
        ronda = carpeta / "la_ronda.json"
        ronda.write_text("{}")
        if libro is not None:
            (carpeta / "la_mejora.json").write_text(json.dumps(libro))
        status = _el_status(plantilla, once)
        for p in status["roster"]["players"]:
            p["status"] = estados.get(p["id"], p["status"])
        r = parte.correr(
            cycle={"snapshot": _la_foto(plantilla, 500_000, ofertas, publicados, estados,
                                        once_de_biwenger=once,
                                        proximo_reset=reset + timedelta(days=1))},
            escritor_factory=_Escritor, ahora=ahora, status=status, calendario=CAL,
            orden_ruta=orden, libro_ronda_ruta=ronda, v10={}, vuelta_mejora={},
            plan_cierre={}, tablon=_el_tablon(reset),
        )
    return {"salida": r, "parte": parte.el_parte(r), "escrituras": list(_Escritor.llamadas)}


# ============================================================
# EL MOTOR VIEJO, SIN RED NI RASTRO
# ============================================================

class _Escribiria(Exception):
    """El ejecutor llego a llamar al escritor: habria aceptado."""


class _EscritorQueNoSale:
    """El escritor del motor viejo, cambiado por uno que LANZA antes de
    tocar la red (y antes de apuntar el rastro en `data/`)."""

    ultimo = None

    def accept_offer(self, offer_id, execute=False):
        _EscritorQueNoSale.ultimo = {"offer_id": int(offer_id), "execute": execute}
        raise _Escribiria()


GATE_NORMAL = {"phase": "NORMAL", "operations_locked": False, "hard_safety_mode": False}


def _oferta(jugador, offer_id, importe):
    return {"offer_id": offer_id, "player_id": jugador["id"],
            "player_name": jugador["name"], "amount": importe, "protection": "SELLABLE"}


def _el_motor_viejo(decision, libro, seleccionada=None):
    """
    `autopilot_executor.execute_autopilot_decision(decision, execute=True)`
    con el libro de la mejora en una carpeta temporal (`la_mejora_del_once.
    LIBRO`), la foto fresca y el selector de antes de caducar suplantados
    y un escritor que revienta antes de la red. Su salida, o
    `{"status": "WOULD_WRITE", ...}` si llega a aceptar.
    """
    from src.actions import autopilot_executor as ejecutor

    antes = (mejora.LIBRO, ejecutor.BiwengerWriteClient,
             ejecutor.refresh_snapshot_for_write_revalidation,
             ejecutor.select_emergency_accept_offer)
    _EscritorQueNoSale.ultimo = None
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "la_mejora.json"
        if libro is not None:
            ruta.write_text(json.dumps(libro))
        mejora.LIBRO = ruta
        ejecutor.BiwengerWriteClient = _EscritorQueNoSale
        ejecutor.refresh_snapshot_for_write_revalidation = lambda: ("foto_fresca.json", {})
        ejecutor.select_emergency_accept_offer = lambda snapshot, offer_ids: (
            {"ready": True, "selected": seleccionada, "status": "READY"}
            if seleccionada else {"ready": False, "status": "SIN_CANDIDATA",
                                  "reason": "ninguna"})
        try:
            return ejecutor.execute_autopilot_decision(decision, execute=True)
        except _Escribiria:
            return {"status": "WOULD_WRITE", **_EscritorQueNoSale.ultimo}
        finally:
            (mejora.LIBRO, ejecutor.BiwengerWriteClient,
             ejecutor.refresh_snapshot_for_write_revalidation,
             ejecutor.select_emergency_accept_offer) = antes


def _solvencia(jugador, offer_id, importe, libro=LIBRO_MEJORA):
    return _el_motor_viejo({
        "action": "ACCEPT_RECOVERY_OFFER", "executable": True, "priority": 960,
        "temporal_gate": GATE_NORMAL,
        "data": {"offer": _oferta(jugador, offer_id, importe)},
    }, libro)


def _antes_de_caducar(jugador, offer_id, importe, libro=LIBRO_MEJORA):
    seleccionada = {**_oferta(jugador, offer_id, importe),
                    "offer_decision": {"decision": "ACCEPT", "protection": "SELLABLE"}}
    return _el_motor_viejo({
        "action": "ACCEPT_CLUSTER_BEFORE_EXPIRY", "executable": True, "priority": 990,
        "temporal_gate": GATE_NORMAL,
        "data": {"cluster": {"offer_ids": [offer_id, 71249]}},
    }, libro, seleccionada)


# ============================================================
# LA BATERIA (solo lo que ya existe en main)
# ============================================================

def _normal(x):
    """Lo mismo, sin lo que no es del resultado: los conjuntos, en orden."""
    if isinstance(x, dict):
        return {str(k): _normal(v) for k, v in x.items()}
    if isinstance(x, (set, frozenset)):
        return sorted((_normal(v) for v in x),
                      key=lambda v: json.dumps(v, sort_keys=True, default=repr))
    if isinstance(x, (list, tuple)):
        return [_normal(v) for v in x]
    if isinstance(x, datetime):
        return x.isoformat()
    return x


def _huella(salida) -> str:
    crudo = json.dumps(_normal(salida), sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _resumen(huellas) -> str:
    return hashlib.sha256("".join(huellas).encode("ascii")).hexdigest()


# La mejora vendio a Unai en ESTA vuelta (corre antes que el cierre).
VUELTA_UNAI = {"run_id": "4242", "generated_at": MIE.isoformat(), "hechas": [
    {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 1969, "offer_id": 70196,
     "importe": 1_700_000, "suelo": 0, "relevo": 41411, "mejora": True, "exito": True}]}

ESCENARIOS_DEL_CIERRE = {
    # E1: Ivan perdido; Gaya y Ortiz vendidos; Unai sin vender.
    "E1": dict(),
    # E1 con Ramon en duda (el parte del 01/11 19:10: DUDA 58).
    "E1_ramon_en_duda": dict(estados={41411: "doubt"}),
    # E1c, la vuelta siguiente en main: Ramon ya vendido, la mejora soltó
    # su cambio (Unai se queda) y el once escrito lleva a Cardona y a Unai
    # (4-3-3): no queda nadie que vender y la J12 empieza en rojo.
    "E1c_la_vuelta_siguiente": dict(
        plantilla=_sin(PLANTILLA_MIE, RAMON), saldo=SALDO_E1 + 409_200,
        libro={"23840": LIBRO_MEJORA["23840"]},
        once=[GULACSI, IGLESIAS, KIKE, CHUST, CARDONA, UNAI, OLASAGASTI, IBANEZ, YAMAL,
              ROBERTO, BOYE]),
    # Ortiz sin vender, en la cartera de la ronda: uno que no es relevo.
    "E1_con_ortiz": dict(plantilla=PLANTILLA_MIE + [ORTIZ], saldo=SALDO_E1 - 182_100,
                         inventario={35765: 219_900},
                         ofertas={**OFERTAS_MIE, 35765: (73576, 182_100)},
                         publicados=PUBLICADOS | {35765}),
    # El cambio ya hecho: Unai vendido antes (el libro aun lo tiene hasta
    # la proxima vuelta de la mejora) y el once escrito, el 4-3-3.
    "hecho_antes": dict(plantilla=_sin(PLANTILLA_MIE, UNAI), saldo=-300_000,
                        once=ONCE_433),
    # El cambio hecho en ESTA vuelta: la mejora cobro a Unai antes.
    "hecho_en_esta_vuelta": dict(vuelta_mejora=VUELTA_UNAI, run_id="4242"),
    # En positivo: solo se publica.
    "en_positivo": dict(saldo=700_000),
    # Sin cambios en el libro.
    "libro_vacio": dict(libro={}),
    # Un libro que no es un libro.
    "libro_basura": dict(libro=["no", "es", "un", "libro"]),
    # Leido de sus ficheros, como en produccion; y uno que no es JSON.
    "de_sus_ficheros": dict(en_ficheros=True),
    "fichero_ilegible": dict(en_ficheros=True, libro_crudo="{no es json"),
}

ESCENARIOS_DEL_PARTE = {
    # Vie 06/11 07:15: Ramon en duda, fuera de los dos onces.
    "ramon_en_duda": dict(libro=LIBRO_MEJORA),
    # El cambio hecho: Unai ya vendido.
    "hecho": dict(plantilla=_sin(PLANTILLA_MIE, UNAI), once=ONCE_433, libro=LIBRO_MEJORA),
    # Sin libro de la mejora junto al de la ronda.
    "sin_libro": dict(),
    # Cardona en duda (no es relevo de nadie) y Ramon sano.
    "cardona_en_duda": dict(estados={30493: "doubt"},
                            ofertas={**OFERTAS_MIE, 30493: (73049, 2_000_000)},
                            libro=LIBRO_MEJORA),
}

ESCENARIOS_DEL_MOTOR = {
    "solvencia_ramon": lambda: _solvencia(RAMON, 70411, 409_200),
    "solvencia_cardona": lambda: _solvencia(CARDONA, 73049, 2_000_000),
    "solvencia_unai": lambda: _solvencia(UNAI, 70196, 2_350_000),
    "solvencia_ramon_sin_libro": lambda: _solvencia(RAMON, 70411, 409_200, libro=None),
    "caduca_ramon": lambda: _antes_de_caducar(RAMON, 70411, 409_200),
    "caduca_boye": lambda: _antes_de_caducar(BOYE, 71249, 5_100_000),
    "caduca_ramon_sin_libro": lambda: _antes_de_caducar(RAMON, 70411, 409_200, libro=None),
}


def la_bateria(entorno, motor) -> dict:
    """{escenario: huella} de los tres vendedores con `entorno` (el cierre
    y el parte) y `motor` (el motor viejo)."""
    huellas = {}
    with _Interruptores(entorno):
        for nombre, k in ESCENARIOS_DEL_CIERRE.items():
            huellas[f"cierre/{nombre}"] = _huella(_el_cierre(**k))
        for nombre, k in ESCENARIOS_DEL_PARTE.items():
            huellas[f"parte/{nombre}"] = _huella(_el_parte(**k))
    with _Interruptores(motor):
        for nombre, llamada in ESCENARIOS_DEL_MOTOR.items():
            huellas[f"motor/{nombre}"] = _huella(llamada())
    return huellas


# ============================================================
# LO DE HOY: main, sin tocar
# ============================================================
#
# La salida ENTERA de cada vendedor en cada escenario de la bateria (el
# cierre: su salida, el plan que escribe, su parte y lo que manda al
# escritor; el parte: su salida, su parte y lo que manda; el motor viejo:
# su veredicto), medida con el codigo de main@85e052e3 ANTES de este
# cambio, el 01/11/2026: sha256 del JSON ordenado de cada una
# (`_huella`) y sha256 de todas seguidas, en el orden de la bateria
# (`_resumen`). Apagado tiene que salir la misma, letra a letra, en cada
# version de Python (la de la vuelta es la 3.13). Igual con el
# interruptor quitado que puesto a "0". Medida en las dos versiones con
# PYTHONHASHSEED 0, 3 y 11, y con los 25 interruptores de produccion
# puestos: sale la misma en todas (los conjuntos se ordenan antes de la
# huella, `_normal`). Si algun dia se cambia uno de los tres vendedores A
# PROPOSITO, se rehace con el interruptor apagado (`--huella`) y se dice
# en el commit.
HUELLA_DE_MAIN = "87bcc700365f4b049d8bf5bf8e9f3cacdfaf8f50a7e015d4fa9bdbf6fa52897e"
HUELLAS_DE_MAIN = {
    (3, 11): HUELLA_DE_MAIN,
    (3, 13): "87bcc700365f4b049d8bf5bf8e9f3cacdfaf8f50a7e015d4fa9bdbf6fa52897e",
}


# ============================================================
# 1. NACE APAGADO
# ============================================================

def test_nace_apagado():
    assert mejora.ENV_EL_RELEVO == ENV
    activo = mejora.el_relevo_no_se_vende_activo
    with _Interruptores({ENV: None}):
        assert activo() is False
    for valor, puesto in (("1", True), ("true", True), ("si", True), ("yes", True),
                          (" YES ", True), ("0", False), ("no", False), ("", False)):
        with _Interruptores({ENV: valor}):
            assert activo() is puesto, valor
    # Se lee en UN sitio: los tres enganches no miran el entorno (lo
    # nombran en sus comentarios, nada mas).
    import re

    for modulo in ("src/actions/el_cierre_de_la_jornada.py", "src/actions/el_parte_vende.py",
                   "src/actions/autopilot_executor.py"):
        texto = (RAIZ / modulo).read_text(encoding="utf-8")
        assert "ENV_EL_RELEVO" not in texto, modulo
        assert not re.search(r"environ[^\n]*" + ENV, texto), modulo
        assert "el_relevo" in texto or "los_que_entran" in texto, modulo
    texto = (RAIZ / "src/actions/la_mejora_del_once.py").read_text(encoding="utf-8")
    assert texto.count("os.environ.get(ENV_EL_RELEVO") == 1
    assert len(re.findall(r"environ[^\n]*(ENV_EL_RELEVO|" + ENV + ")", texto)) == 1
    # Un interruptor sin frase para el dueño pone la verja en rojo el dia
    # que se enciende (leccion del 26/10).
    from src.telemetry.el_tablon import QUE_HACE
    assert str(QUE_HACE.get(ENV) or "").strip(), "sin frase en QUE_HACE"


# ============================================================
# 2. APAGADO ES MAIN, BYTE A BYTE
# ============================================================

def test_apagado_los_tres_vendedores_son_los_de_main():
    esperada = HUELLAS_DE_MAIN.get(sys.version_info[:2])
    assert esperada is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    hoy = la_bateria(APAGADO, MOTOR_APAGADO)
    assert len(hoy) == (len(ESCENARIOS_DEL_CIERRE) + len(ESCENARIOS_DEL_PARTE)
                        + len(ESCENARIOS_DEL_MOTOR))
    assert _resumen(hoy.values()) == esperada, _resumen(hoy.values())
    # Puesto a "0", lo mismo.
    cero = la_bateria({**APAGADO, ENV: "0"}, {**MOTOR_APAGADO, ENV: "0"})
    assert cero == hoy
    # Y lo que mueve el arreglo, dicho antes que la huella: apagado, el
    # mie 04/11 el cierre vende a Ramon.
    with _Interruptores(APAGADO):
        r = _el_cierre()["salida"]
    assert r["decision"]["vender"] == [41411], r["decision"]["vender"]
    assert "el_relevo" not in r and "el_relevo" not in (r.get("plan") or {})


# ============================================================
# 3. EL LIBRO, COMO LO LEE LA MEJORA
# ============================================================

def test_el_libro_se_lee_como_lo_lee_la_mejora():
    el_relevo, los_que_entran = mejora.el_relevo, mejora.los_que_entran
    nuestros = {j["id"] for j in PLANTILLA_MIE}
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "la_mejora.json"
        ruta.write_text(json.dumps(LIBRO_MEJORA))
        falta = Path(carpeta) / "no_esta.json"
        ilegible = Path(carpeta) / "roto.json"
        ilegible.write_text("{no es json")
        lista = Path(carpeta) / "lista.json"
        lista.write_text("[1, 2]")

        # Apagado: vacio, y sin abrir nada (ni el que no es JSON).
        with _Interruptores({ENV: None}):
            r = el_relevo(ruta=ilegible)
            assert r == {"activo": False, "motivo": "APAGADO", "entran": frozenset(),
                         "detalle": None}, r
            assert los_que_entran(LIBRO_MEJORA, plantilla=nuestros) == frozenset()
            assert los_que_entran(ruta=ruta) == frozenset()

        with _Interruptores({ENV: "1"}):
            # Sin plantilla: todo el que entra del libro.
            assert los_que_entran(ruta=ruta) == frozenset({23840, 41411})
            assert los_que_entran(LIBRO_MEJORA) == frozenset({23840, 41411})
            # Con la plantilla, solo el cambio VIVO: Gaya ya no es nuestro
            # (vendido el martes), asi que Iglesias es uno mas.
            r = el_relevo(LIBRO_MEJORA, plantilla=nuestros)
            assert r["activo"] and r["motivo"] == "LEIDO", r
            assert r["entran"] == frozenset({41411}), r
            # Con Unai vendido, Ramon tambien.
            assert los_que_entran(LIBRO_MEJORA, plantilla=nuestros - {1969}) == frozenset()
            # El que entra aun no es nuestro (puja viva): no hay a quien guardar.
            assert los_que_entran(LIBRO_MEJORA, plantilla=nuestros - {41411}) == frozenset()
            # Las claves y el `sale` en texto o numero; lo que no se
            # entiende, como la mejora: ese cambio no existe.
            raro = {"41411": {"sale": "1969"}, "x": {"sale": 1844}, "23840": {"sale": None},
                    "28115": "basura", 30493: {"sale": 1760}}
            r = el_relevo(raro, plantilla=nuestros)
            assert r["entran"] == frozenset({41411, 30493}), r
            # Sin fichero: no hay cambios vivos. Nadie.
            r = el_relevo(ruta=falta)
            assert (r["motivo"], r["entran"]) == ("SIN_LIBRO", frozenset()), r
            # No se puede leer: no se sabe quien entra, lo de main (nadie) y
            # se dice. La mejora lo lee igual ({}) y suelta los cambios.
            for roto, motivo in ((ilegible, "LIBRO_ILEGIBLE"), (lista, "NO_ES_UN_LIBRO")):
                r = el_relevo(ruta=roto)
                assert (r["motivo"], r["entran"]) == (motivo, frozenset()), r
                assert r["detalle"], r
            r = el_relevo(["no", "es", "un", "libro"])
            assert (r["motivo"], r["entran"]) == ("NO_ES_UN_LIBRO", frozenset()), r
            # Por defecto, el libro de la mejora (`LIBRO`), leido al llamar.
            antes = mejora.LIBRO
            try:
                mejora.LIBRO = ruta
                assert los_que_entran() == frozenset({23840, 41411})
                mejora.LIBRO = falta
                assert los_que_entran() == frozenset()
            finally:
                mejora.LIBRO = antes


# ============================================================
# 4. EL CIERRE NO VENDE AL RELEVO
# ============================================================

def _vender(r):
    return r["salida"]["decision"]["vender"]


def _aceptadas(r):
    return sorted(a["player_id"] for a in r["salida"]["acciones"]
                  if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER")


def test_ramon_por_unai_el_miercoles_con_la_caja_en_rojo():
    with _Interruptores(APAGADO):
        hoy = _el_cierre()
    with _Interruptores(PUESTO):
        puesto = _el_cierre()
    d_hoy, d = hoy["salida"]["decision"], puesto["salida"]["decision"]
    # Lo de main: -1.990.776, el once del cierre sin Unai (se va) es el
    # 4-3-3 con Cardona; el unico candidato es Ramon y su oferta pasa el 90 %.
    assert d_hoy["caja"] == SALDO_E1 and d_hoy["deficit"] == -SALDO_E1, d_hoy
    assert 30493 in d_hoy["once"]["ids"] and 41411 not in d_hoy["once"]["ids"]
    assert [c["id"] for c in d_hoy["candidatos"]] == [41411], d_hoy["candidatos"]
    assert _vender(hoy) == [41411] and _aceptadas(hoy) == [41411]
    assert {"offer_id": 70411, "execute": True} in hoy["escrituras"], hoy["escrituras"]
    # Encendido: Ramon no es candidato, no se publica ni se acepta; lo que
    # falta se dice (FALTA) y Unai sigue siendo de la mejora.
    assert d["caja"] == SALDO_E1 and d["once"] == d_hoy["once"], d
    assert d["candidatos"] == [] and d["vender"] == [] and d["acciones"] == [], d
    assert d["motivo"] == "FALTA" and d["falta"] == -SALDO_E1, d
    assert puesto["escrituras"] == [], puesto["escrituras"]
    assert puesto["salida"]["el_relevo"] == {"motivo": "LEIDO", "no_se_venden": [41411],
                                             "detalle": None}, puesto["salida"]
    assert puesto["plan"]["el_relevo"] == puesto["salida"]["el_relevo"], puesto["plan"]
    assert puesto["plan"]["vender"] == [] and puesto["plan"]["falta"] == -SALDO_E1
    assert any("relevo" in linea.lower() and "41411" in linea for linea in puesto["parte"]), \
        puesto["parte"]
    # Lo que se evita (main, la vuelta siguiente): Ramon vendido, la mejora
    # soltó su cambio y Unai se queda; con Cardona en el once escrito no
    # queda nadie que vender: FALTA 1.581.576 y la J12 empieza en rojo.
    with _Interruptores(APAGADO):
        despues = _el_cierre(**ESCENARIOS_DEL_CIERRE["E1c_la_vuelta_siguiente"])
    d_despues = despues["salida"]["decision"]
    assert d_despues["motivo"] == "FALTA" and d_despues["candidatos"] == [], d_despues
    assert d_despues["falta"] == -(SALDO_E1 + 409_200) == 1_581_576, d_despues
    # En duda, igual (el once del cierre ya no lo sienta y sigue sin venderse).
    with _Interruptores(PUESTO):
        duda = _el_cierre(estados={41411: "doubt"})
    assert _vender(duda) == [] and _aceptadas(duda) == [], duda["salida"]["acciones"]
    # Leido de sus ficheros (como en produccion), lo mismo.
    with _Interruptores(PUESTO):
        ficheros = _el_cierre(en_ficheros=True)
    assert _vender(ficheros) == [] and ficheros["escrituras"] == []
    assert ficheros["salida"]["el_relevo"]["no_se_venden"] == [41411]


def test_con_el_cambio_hecho_el_relevo_es_uno_mas():
    # Unai vendido antes (el libro de la mejora aun trae el cambio hasta su
    # proxima vuelta): Ramon se vende como siempre, encendido o no.
    for k in (ESCENARIOS_DEL_CIERRE["hecho_antes"], ESCENARIOS_DEL_CIERRE["hecho_en_esta_vuelta"]):
        with _Interruptores(APAGADO):
            hoy = _el_cierre(**k)
        with _Interruptores(PUESTO):
            puesto = _el_cierre(**k)
        assert _vender(hoy) == [41411] and _aceptadas(hoy) == [41411], hoy["salida"]["decision"]
        assert puesto["salida"]["decision"] == hoy["salida"]["decision"]
        assert puesto["escrituras"] == hoy["escrituras"]
        assert puesto["salida"]["el_relevo"]["no_se_venden"] == [], puesto["salida"]
    # En esta vuelta: la caja cuenta lo cobrado por Unai.
    with _Interruptores(PUESTO):
        r = _el_cierre(**ESCENARIOS_DEL_CIERRE["hecho_en_esta_vuelta"])
    assert r["salida"]["decision"]["caja"] == SALDO_E1 + 1_700_000, r["salida"]["decision"]


def test_el_que_no_es_relevo_se_vende_como_siempre():
    k = ESCENARIOS_DEL_CIERRE["E1_con_ortiz"]
    with _Interruptores(APAGADO):
        hoy = _el_cierre(**k)
    with _Interruptores(PUESTO):
        puesto = _el_cierre(**k)
    # Main vende a los dos y aun falta; encendido, solo a Ortiz.
    assert sorted(_vender(hoy)) == [35765, 41411] and _aceptadas(hoy) == [35765, 41411]
    assert _vender(puesto) == [35765] and _aceptadas(puesto) == [35765], puesto["salida"]
    assert {"offer_id": 73576, "execute": True} in puesto["escrituras"]
    assert puesto["salida"]["decision"]["falta"] == hoy["salida"]["decision"]["falta"] + 389_500
    # Sin cambios en el libro, encendido es lo de main.
    with _Interruptores(APAGADO):
        hoy = _el_cierre(**ESCENARIOS_DEL_CIERRE["libro_vacio"])
    with _Interruptores(PUESTO):
        puesto = _el_cierre(**ESCENARIOS_DEL_CIERRE["libro_vacio"])
    assert puesto["salida"]["decision"] == hoy["salida"]["decision"]
    assert puesto["escrituras"] == hoy["escrituras"] and _vender(hoy) == [30493]
    # En positivo no se vende a nadie; el relevo, ademas, ni es candidato a
    # publicar (va con los protegidos). Ya estaba publicado: nada que escribir.
    with _Interruptores(APAGADO):
        hoy = _el_cierre(**ESCENARIOS_DEL_CIERRE["en_positivo"])
    with _Interruptores(PUESTO):
        puesto = _el_cierre(**ESCENARIOS_DEL_CIERRE["en_positivo"])
    assert hoy["salida"]["decision"]["motivo"] == "EN_POSITIVO" == puesto["salida"]["motivo"]
    assert [c["id"] for c in hoy["salida"]["decision"]["candidatos"]] == [41411]
    assert puesto["salida"]["decision"]["candidatos"] == []
    assert hoy["escrituras"] == puesto["escrituras"] == []


def test_sin_libro_que_leer_lo_de_main_y_lo_dice():
    for nombre, motivo in (("libro_basura", "NO_ES_UN_LIBRO"),
                           ("fichero_ilegible", "LIBRO_ILEGIBLE")):
        k = ESCENARIOS_DEL_CIERRE[nombre]
        with _Interruptores(APAGADO):
            hoy = _el_cierre(**k)
        with _Interruptores(PUESTO):
            puesto = _el_cierre(**k)
        assert puesto["salida"]["decision"] == hoy["salida"]["decision"], nombre
        assert puesto["escrituras"] == hoy["escrituras"], nombre
        # Main, sin poder leer el libro de la mejora: tampoco aparta a Unai,
        # el once del cierre es el 3-4-3 y se publica a Cardona. Igual.
        assert _vender(puesto) == _vender(hoy) == [30493], (nombre, _vender(puesto))
        relevo = puesto["salida"]["el_relevo"]
        assert relevo["motivo"] == motivo and relevo["no_se_venden"] == [], relevo
        assert relevo["detalle"] and puesto["plan"]["el_relevo"] == relevo, relevo
        assert any(motivo in linea for linea in puesto["parte"]), puesto["parte"]
    # Con los libros dados y sin el de la mejora, ninguno (como `la_mejora`
    # del cierre): no se va a buscar el de produccion (`LIBRO`, aqui uno
    # temporal con el cambio de Ramon que no se tiene que leer).
    antes = mejora.LIBRO
    with tempfile.TemporaryDirectory() as carpeta:
        mejora.LIBRO = Path(carpeta) / "la_mejora.json"
        mejora.LIBRO.write_text(json.dumps(LIBRO_MEJORA))
        try:
            with _Interruptores(APAGADO):
                hoy = _el_cierre(sin_mejora=True)
            with _Interruptores(PUESTO):
                puesto = _el_cierre(sin_mejora=True)
        finally:
            mejora.LIBRO = antes
    assert puesto["salida"]["decision"] == hoy["salida"]["decision"]
    assert puesto["salida"]["el_relevo"] == {"motivo": "LEIDO", "no_se_venden": [],
                                             "detalle": None}, puesto["salida"]


# ============================================================
# 5. EL PARTE VENDE TAMPOCO
# ============================================================

def _por(r):
    return {n["player_id"]: n["por"] for n in r["salida"]["decision"]["no_se_tocan"]}


def test_el_parte_no_vende_al_relevo_en_duda():
    with _Interruptores(APAGADO):
        hoy = _el_parte(libro=LIBRO_MEJORA)
    with _Interruptores(PUESTO):
        puesto = _el_parte(libro=LIBRO_MEJORA)
    # Main: Ramon en duda, fuera de los dos onces, 7 dias y una ronda con
    # nosotros: su oferta (409.200) pasa el 95 % (389.500) y se vende.
    assert hoy["salida"]["motivo"] == "EJECUTADA", hoy["salida"]
    assert [(a["accion"], a["player_id"]) for a in hoy["salida"]["acciones"]] == [
        ("ACEPTAR_OFERTA_DEL_COMPUTER", 41411)], hoy["salida"]["acciones"]
    # Encendido: no se toca, y dice por que.
    assert puesto["salida"]["acciones"] == [] and puesto["escrituras"] == [], puesto["salida"]
    assert _por(puesto)[41411] == "EL_RELEVO", _por(puesto)
    assert puesto["salida"]["el_relevo"] == {"motivo": "LEIDO", "no_se_venden": [41411],
                                             "detalle": None}
    assert any("EL_RELEVO" in linea for linea in puesto["parte"]), puesto["parte"]
    # Con el cambio hecho, o sin libro, lo de main.
    for k in (ESCENARIOS_DEL_PARTE["hecho"], ESCENARIOS_DEL_PARTE["sin_libro"],
              ESCENARIOS_DEL_PARTE["cardona_en_duda"]):
        with _Interruptores(APAGADO):
            hoy = _el_parte(**k)
        with _Interruptores(PUESTO):
            puesto = _el_parte(**k)
        assert puesto["salida"]["decision"] == hoy["salida"]["decision"], k
        assert puesto["escrituras"] == hoy["escrituras"], k
        assert hoy["escrituras"], k


# ============================================================
# 6. EL MOTOR VIEJO TAMPOCO
# ============================================================

def test_el_motor_viejo_no_acepta_por_el_relevo():
    for llamada, bloqueo in ((lambda: _solvencia(RAMON, 70411, 409_200),
                              "BLOCKED_PROTECTED_PLAYER"),
                             (lambda: _antes_de_caducar(RAMON, 70411, 409_200),
                              "INVALID_SELECTED_OFFER")):
        with _Interruptores(MOTOR_APAGADO):
            hoy = llamada()
        with _Interruptores(MOTOR_PUESTO):
            puesto = llamada()
        assert hoy == {"status": "WOULD_WRITE", "offer_id": 70411, "execute": True}, hoy
        assert puesto["status"] == bloqueo and puesto["write_performed"] is False, puesto
    # El motor viejo no sabe la plantilla: guarda a todo el que entra del
    # libro hasta que la mejora lo limpia (corre despues, en la misma
    # vuelta). Al que sale y a otro cualquiera, como siempre; sin libro, igual.
    with _Interruptores(MOTOR_PUESTO):
        assert _solvencia(IGLESIAS, 72384, 3_600_000)["status"] == "BLOCKED_PROTECTED_PLAYER"
        assert _solvencia(UNAI, 70196, 2_350_000)["status"] == "WOULD_WRITE"
        assert _solvencia(CARDONA, 73049, 2_000_000)["status"] == "WOULD_WRITE"
        assert _antes_de_caducar(BOYE, 71249, 5_100_000)["status"] == "WOULD_WRITE"
        assert _solvencia(RAMON, 70411, 409_200, libro=None)["status"] == "WOULD_WRITE"
        assert _antes_de_caducar(RAMON, 70411, 409_200, libro=None)["status"] == "WOULD_WRITE"
    # Y la rotacion ya no lo tocaba (`los_que_otros_venden._de_la_mejora`
    # trae las claves del libro): no hace falta engancharla.
    from src.analysis.los_que_otros_venden import _de_la_mejora
    assert {23840, 41411, 1844, 1969} <= _de_la_mejora(LIBRO_MEJORA)


# ============================================================
# 7. NUNCA LANZA
# ============================================================

def test_nunca_lanza():
    # Sin libro dado se lee `LIBRO`: aqui, uno que no existe en la carpeta
    # temporal (la guardia no abre `data/`).
    antes = mejora.LIBRO
    with tempfile.TemporaryDirectory() as carpeta, _Interruptores({ENV: "1"}):
        mejora.LIBRO = Path(carpeta) / "la_mejora.json"
        try:
            for basura in (None, "x", 5, [1, 2], {"a": object()}, {"1": {"sale": object()}},
                           {None: None}, {"1": {"sale": float("inf")}}, object()):
                for plantilla in (None, basura, [1, "2", None], {41411: 1}):
                    r = mejora.el_relevo(basura, plantilla=plantilla)
                    assert isinstance(r, dict) and isinstance(r["entran"], frozenset), r
                    assert isinstance(mejora.los_que_entran(basura, plantilla=plantilla),
                                      frozenset)
                assert isinstance(mejora.el_relevo(ruta=basura), dict)
                assert isinstance(mejora.los_que_entran(ruta=basura), frozenset)
            assert mejora.los_que_entran(ruta=Path(carpeta) / "no_existe.json") == frozenset()
            assert mejora.el_relevo(ruta=Path(carpeta))["motivo"] == "LIBRO_ILEGIBLE"
            d = parte.decidir(plantilla={7}, estados={7: "doubt"}, nombres={7: "Suplente"},
                              precios={7: 1_000_000}, once_escrito={1}, once_de_biwenger={1},
                              relevos="basura")
            assert isinstance(d, dict), d
        finally:
            mejora.LIBRO = antes
    assert cierre.el_parte({"el_relevo": object()})
    assert parte.el_parte({"el_relevo": "x"})


TESTS = [
    test_nace_apagado,
    test_apagado_los_tres_vendedores_son_los_de_main,
    test_el_libro_se_lee_como_lo_lee_la_mejora,
    test_ramon_por_unai_el_miercoles_con_la_caja_en_rojo,
    test_con_el_cambio_hecho_el_relevo_es_uno_mas,
    test_el_que_no_es_relevo_se_vende_como_siempre,
    test_sin_libro_que_leer_lo_de_main_y_lo_dice,
    test_el_parte_no_vende_al_relevo_en_duda,
    test_el_motor_viejo_no_acepta_por_el_relevo,
    test_nunca_lanza,
]


def main() -> None:
    if "--huella" in sys.argv:
        # Para medir `HUELLAS_DE_MAIN` (con el codigo de main, apagado).
        hoy = la_bateria(APAGADO, MOTOR_APAGADO)
        for nombre, huella in hoy.items():
            print(f"  {nombre:<36} {huella}")
        print(f"{sys.version_info[:2]} {_resumen(hoy.values())}")
        return
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
