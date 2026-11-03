"""
LA ORDEN MANDA EN EL CAMBIO (03/11/2026). Guardias de
`BORDALAS_LA_ORDEN_MANDA_EN_EL_CAMBIO` (`src/actions/la_mejora_del_once.py`:
`la_orden_manda`, la SALIDA de `decidir` y `la_caja_de_la_jornada`).

EL CASO (supervision del 03/11 12:20, revision ON de LA PRIMA QUE GANA)

    El 03/11 a las 07:15 la mejora del once pujo 4.429.900 por Adrian
    Nino (35706) y apunto en su libro el cambio {35706: {"sale": 12494}}:
    entra Adrian, sale Boye. El dueno dijo Roberto (35678). Si la orden
    del gestor coge a Adrian en un solo paso (`fichar` 35706, que
    SUSTITUYE la puja de la mejora, y `vender_si_ficha` Roberto con
    `si_esta` 35706), en main:

      1. la mejora no suelta su cambio: la puja por Adrian sigue viva
         (ahora es la de la orden), asi que cuando llega Adrian se venden
         Roberto (la orden) Y Boye (la mejora) por un solo fichaje;
      2. `la_caja_de_la_jornada` cuenta dos ventas contra una sola puja
         (la de Roberto por la orden y la de Boye por el libro): la mejora
         puede gastar dinero que no existe;
      3. el cierre, el parte, la rotacion y el motor viejo leen el libro y
         siguen viendo a Boye de salida por Adrian.

    El gestor lo arreglo a mano en dos pasos (Adrian a `no_pujar` para que
    la mejora soltara el cambio, y `fichar` una vuelta despues).

QUE SE COMPRUEBA

    1. Nace apagado, se lee en UN sitio (`la_orden_manda_activa`, al
       llamarse, solo desde `la_orden_manda`, solo desde `correr`), vale
       lo mismo que `el_paso_0.ENCENDIDO`, tiene frase en QUE_HACE y no
       hace nada al importarse.
    2. Apagado es main byte a byte: la huella de la bateria (`decidir`,
       `la_caja_de_la_jornada` y `correr` con el escritor de mentira, y lo
       que leen del libro que deja `correr` el cierre, la rotacion y el
       motor viejo -`los_que_otros_venden`- y el relevo), sobre los
       estados compactados de hoy (el libro Adrian->Boye de las 07:15, la
       puja de la orden de las 11:07, el de las 20:07 con Unai Simon, y el
       miercoles con Adrian dentro), con la orden de hoy (fichar Adrian y
       vender_si_ficha Roberto), sin ella, caducada y sin `fichar`; con el
       interruptor sin poner, "0" y "", con lo minimo de la mejora y con
       los 26 interruptores del YAML de produccion (EL PARTE VENDE
       incluido). La de main, medida antes de tocar el codigo, una por
       version de Python (3.11 y 3.13).
    3. `la_orden_manda`: los que entran por un cambio del libro que la
       orden VIVA (encendida y valida a `ahora`) esta fichando. Apagado,
       con la orden apagada, caducada, sin `fichar`, sin hora o con
       basura: nadie.
    4. EL CASO DE HOY, el miercoles 04/11 a las 07:15, Adrian ganado:
       apagado se venden Roberto (la orden) y Boye (la mejora); encendido
       solo Roberto. La mejora suelta el cambio y lo dice
       (`plan["la_orden_manda"]`, la linea `LA_ORDEN_MANDA: suelta ...`).
    5. La caja de la jornada cuenta UNA venta por el fichaje: encendido,
       la de Roberto; la de Boye ya no (las 11:07 y las 20:07).
    6. Suelta el cambio en la primera vuelta, con la puja aun viva: Boye
       vuelve a ser uno mas y la mejora no lo publica ni lo cobra por
       Adrian.
    7. Nunca vuelve a apuntar a Adrian mientras esta en `fichar`: tres
       vueltas seguidas, ni libro ni puja de la mejora por el.
    8. Lo que leen el libro (el cierre, el relevo, la rotacion y el motor
       viejo) ya no ve el cambio.
    9. Sin fantasmas: quitado `fichar` con la puja aun viva, Adrian es uno
       mas (ni vuelve al libro ni vende a Boye al llegar), y la caja no
       cuenta la venta de Boye.
   10. Sin orden que mande (apagada, caducada, sin `fichar` desde el
       principio, o que ficha a otro) y con su propio cambio (Unai Simon
       por Gulacsi), lo de siempre.
   11. Nunca lanza.
   12. El entorno no la decide (doctrina 104).

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui, compactado de los artefactos de produccion del
    03/11: la plantilla, el Computer, las ofertas y lo publicado de las
    runs 41588746048 (07:15) y 41608412779 (10:07), y el saldo
    (+2.025.724 tras el premio de la J11), `maximumBid` (8.000.924) y las
    pujas vivas (Adrian 4.909.900 de la orden; Unai Simon 4.179.900 de la
    mejora, por Gulacsi) de la 41700251364 (20:07). El libro de la mejora
    no va en el artefacto: el cambio Adrian->Boye (suelo 4.896.000, puja
    4.429.900, +0,61) es el de la bitacora de las 12:20; el de Unai
    Simon, el de la mejora de las 17:13 (+1,04). El miercoles es de la
    prueba: Adrian ganado en el reset de las 07:00 y las ofertas nuevas
    del Computer por los publicados. Ni `data/`, ni la red, ni el reloj:
    la hora se pasa (`ahora`) y las horas a la jornada tambien; los
    libros van a una carpeta temporal y el escritor es de mentira.

COMO SE USA

    python -m src.analysis.test_la_orden_manda_en_el_cambio_v1
    python -m src.analysis.test_la_orden_manda_en_el_cambio_v1 --medir
    python -m src.analysis.test_la_orden_manda_en_el_cambio_v1 --volcar FICHERO
"""

from __future__ import annotations

import copy
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


ENV = "BORDALAS_LA_ORDEN_MANDA_EN_EL_CAMBIO"

# Los `BORDALAS_*` que no son del bot sino de la verja (el vigilante de
# `data/`): no se tocan.
DE_LA_VERJA = frozenset({"BORDALAS_VIGILA_DATA"})


def _de_fuera() -> list:
    return [k for k in os.environ if k.startswith("BORDALAS_") and k not in DE_LA_VERJA]


class _Interruptores:
    """EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Pone (valor) o
    quita (None) interruptores solo dentro del `with`; cualquier otro
    `BORDALAS_*` del entorno (menos `DE_LA_VERJA`) y `GITHUB_RUN_ID`,
    quitados dentro; al salir, el entorno de antes, tal cual."""

    def __init__(self, valores: dict | None = None):
        self.valores = dict(valores or {})

    def __enter__(self):
        self.antes = {k: os.environ[k] for k in _de_fuera()}
        self.run_id = os.environ.pop("GITHUB_RUN_ID", None)
        for k in self.antes:
            os.environ.pop(k, None)
        for nombre, valor in self.valores.items():
            if valor is not None:
                os.environ[nombre] = valor
        return self

    def __exit__(self, *_):
        for k in _de_fuera():
            os.environ.pop(k, None)
        os.environ.update(self.antes)
        if self.run_id is not None:
            os.environ["GITHUB_RUN_ID"] = self.run_id
        return False


class _Ademas:
    """Pone unos interruptores SOLO dentro del `with`, sin quitar los
    demas; al salir, esos, como estaban."""

    def __init__(self, valores: dict):
        self.valores = dict(valores)

    def __enter__(self):
        self.antes = {k: os.environ.get(k) for k in self.valores}
        os.environ.update(self.valores)
        return self

    def __exit__(self, *_):
        for k, v in self.antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


# ============================================================
# LOS ESTADOS DE HOY, COMPACTADOS
# ============================================================

YO = 14175949
ADRIAN = 35706
BOYE = 12494
ROBERTO = 35678
UNAI_SIMON = 17021
GULACSI = 38433
YAMAL = 26271

_UTC = timezone.utc

# (id, nombre, posicion, precio, sube hoy, estado, titularidad, puntos,
#  jugados, tasa, equipo): los de la plantilla (catalogo y panel del
#  03/11; los 12 de despues de vender a Gaya y a Ortiz).
PLANTILLA = (
    (38433, "Gulacsi", 1, 2260000, -30000, "ok", 90.0, 31, 7, 4.43, 19),
    (23840, "Juan Iglesias", 2, 3790000, 20000, "ok", 90.0, 56, 11, 5.09, 17),
    (28115, "Kike Salas", 2, 3420000, 60000, "ok", 90.0, 47, 9, 5.22, 17),
    (1760, "Chust", 2, 2640000, 80000, "ok", 90.0, 48, 11, 4.36, 75),
    (29661, "Olasagasti", 3, 2860000, -10000, "ok", 80.0, 54, 11, 4.91, 10),
    (12403, "Ivan Martin", 3, 2730000, -30000, "ok", 80.0, 42, 9, 4.67, 812),
    (41418, "Dani Lorenzo", 3, 2010000, 0, "ok", 70.0, 39, 10, 3.9, 65),
    (26271, "Yamal", 4, 25450000, 90000, "ok", 95.0, 131, 11, 11.91, 3),
    (35678, "Roberto Fernandez", 4, 7070000, -90000, "ok", 90.0, 69, 11, 6.27, 7),
    (12494, "Boye", 4, 5440000, -40000, "ok", 90.0, 63, 10, 6.3, 91),
    (30493, "Sergi Cardona", 2, 2160000, 30000, "ok", 50.0, 25, 7, 3.57, 19),
    (41411, "Ramon Enriquez", 3, 430000, 10000, "ok", 60.0, 25, 10, 2.5, 65),
)

# El mercado del Computer del 03/11 (el escaparate: 20; lo que pide = su
# valor del dia).
COMPUTER = (
    (38405, "Odysseas", 1, 2520000, -30000, "ok", 95.0, 37, 11, 3.36, 17),
    (17731, "Catena", 2, 2310000, -40000, "ok", 70.0, 29, 10, 2.9, 93),
    (1599, "Jonny", 2, 1390000, -40000, "ok", 70.0, 23, 9, 2.56, 91),
    (11, "David Soria", 1, 4810000, -60000, "ok", 95.0, 59, 11, 5.36, 8),
    (35706, "Adrian Nino", 4, 4380000, 170000, "ok", 80.0, 52, 7, 7.43, 65),
    (38290, "Hancko", 2, 4340000, 60000, "ok", 90.0, 52, 11, 4.73, 2),
    (17021, "Unai Simon", 1, 4130000, 30000, "ok", 95.0, 53, 10, 5.3, 1),
    (25384, "Tenaglia", 2, 4460000, -70000, "ok", 90.0, 53, 11, 4.82, 91),
    (26131, "Andres Garcia", 2, 1590000, 30000, "ok", 70.0, 41, 10, 4.1, 8),
    (41031, "Loureiro", 2, 790000, 20000, "ok", 70.0, 31, 7, 4.43, 6),
    (14466, "Hinojo", 2, 1040000, -10000, "sanctioned", 0.0, 32, 10, 3.2, 7),
    (22061, "Josan", 3, 170000, 0, "ok", 0.0, 8, 3, 2.67, 75),
    (24734, "Jesus Vazquez", 2, 460000, -10000, "ok", 10.0, 15, 9, 1.67, 18),
    (25403, "Gonzalo Villar", 3, 2510000, -10000, "warned", 80.0, 45, 11, 4.09, 75),
    (27960, "Carmona", 2, 410000, -10000, "ok", 10.0, 13, 5, 2.6, 17),
    (32460, "Hector Fort", 2, 1710000, -40000, "ok", 30.0, 16, 5, 3.2, 13),
    (37499, "Trent", 2, 1410000, -10000, "ok", 30.0, 25, 7, 3.57, 15),
    (39386, "Manas", 4, 280000, 0, "ok", 30.0, 26, 8, 3.25, 91),
    (39966, "Fidalgo", 3, 330000, -10000, "ok", 10.0, 9, 4, 2.25, 87),
    (41157, "Diatta", 3, 200000, 0, "doubt", 0.0, 0, 0, None, 19),
)
TODOS = {f[0]: f for f in PLANTILLA + COMPUTER}
REALES = tuple(f[0] for f in COMPUTER)
DOCE = tuple(f[0] for f in PLANTILLA)

# Las ofertas del Computer por los nuestros: las del martes (status.json
# de las 10:07 y de las 20:07, iguales) y las del miercoles tras el reset
# (de la prueba: las que caducaban el mie 07:00 vuelven un poco movidas;
# las del jueves, las mismas).
OFERTAS_MARTES = {
    35678: 7474000, 29661: 2735700, 1760: 2576600, 38433: 2314000, 30493: 2138600,
    12494: 5414700, 41411: 449500,
}
OFERTAS_MIERCOLES = {
    35678: 7180000, 29661: 2750000, 1760: 2600000, 38433: 2314000, 30493: 2138600,
    12494: 5390000, 41411: 449500,
}

# Lo que tenemos publicado (lo que pedimos), 03/11 20:07.
EN_VENTA = {1760: 2560000, 12403: 3280000, 12494: 6450000, 23840: 4550000,
            28115: 4110000, 29661: 3470000, 30493: 2160000, 35678: 10200000,
            38433: 2980000, 41411: 430000, 41418: 2420000}

ONCE = (38433, 23840, 28115, 1760, 29661, 12403, 41418, 41411, 26271, 35678, 12494)

# Los cambios del libro de la mejora: Adrian por Boye (07:15) y Unai Simon
# por Gulacsi (17:13).
CAMBIO_ADRIAN = {"sale": BOYE, "suelo": 4896000, "puja": 4429900, "puntos": 0.61}
CAMBIO_UNAI = {"sale": GULACSI, "suelo": 2034000, "puja": 4179900, "puntos": 1.04}

# Los estados: 08:07 (la mejora puja por Adrian y lo apunta por Boye),
# 11:07 (la orden ficha a Adrian en UN paso y su puja sustituye a la de la
# mejora: el libro sigue con el cambio), 20:07 (tras el premio, con la
# puja de la mejora por Unai Simon), 20:07 como fue (el gestor ya habia
# hecho soltar el cambio en dos pasos) y el miercoles 07:15 tras el reset
# (Adrian ganado; Unai Simon perdido o ganado).
E0807 = {"nombre": "0807", "plantilla": DOCE, "saldo": -164276, "maximo": 10470824,
         "ofertas": OFERTAS_MARTES, "pujas": {ADRIAN: 4429900},
         "libro": {str(ADRIAN): CAMBIO_ADRIAN}, "mercado": REALES}
E1107 = {**E0807, "nombre": "1107", "maximo": 9990824, "pujas": {ADRIAN: 4909900}}
E2007 = {**E0807, "nombre": "2007", "saldo": 2025724, "maximo": 8000924,
         "pujas": {ADRIAN: 4909900, UNAI_SIMON: 4179900},
         "libro": {str(ADRIAN): CAMBIO_ADRIAN, str(UNAI_SIMON): CAMBIO_UNAI}}
E2007_COMO_FUE = {**E2007, "nombre": "2007_como_fue",
                  "libro": {str(UNAI_SIMON): CAMBIO_UNAI}}
EMIERCOLES = {"nombre": "mie0715", "plantilla": DOCE + (ADRIAN,), "saldo": -2884176,
              "maximo": 12150000, "ofertas": OFERTAS_MIERCOLES, "pujas": {},
              "libro": {str(ADRIAN): CAMBIO_ADRIAN, str(UNAI_SIMON): CAMBIO_UNAI},
              "mercado": tuple(i for i in REALES if i not in (ADRIAN, UNAI_SIMON))}
EMIERCOLES_LOS_DOS = {**EMIERCOLES, "nombre": "mie0715_los_dos",
                      "plantilla": DOCE + (ADRIAN, UNAI_SIMON), "saldo": -7064076,
                      "maximo": 10130000}
ESTADOS = (E0807, E1107, E2007, E2007_COMO_FUE, EMIERCOLES, EMIERCOLES_LOS_DOS)

# La orden de hoy en UN paso (el caso): fichar Adrian a 4.909.900 y
# vender_si_ficha Roberto con `si_esta` Adrian (y su red del viernes).
ORDEN_HOY = {
    "caduca": "2026-11-30T23:59:00+01:00",
    "fichar": [{"player_id": ADRIAN, "nombre": "Adrian Nino", "puja": 4909900,
                "la_pagan_sus_ventas": True}],
    "no_pujar": [{"player_id": 1721, "nombre": "Manu Sanchez"}],
    "vender_si_ficha": {
        "si_esta": ADRIAN,
        "jugadores": [
            {"player_id": ROBERTO, "nombre": "Roberto Fernandez", "si_esta": ADRIAN,
             "suelo": 6200000},
            {"player_id": ROBERTO, "nombre": "Roberto Fernandez", "si_esta": ADRIAN,
             "suelo": 0, "desde": "2026-11-06T07:00:00+01:00", "si_saldo_negativo": True},
        ],
    },
    "proteger": [{"player_id": YAMAL, "nombre": "Yamal"}],
    "conservar": [{"player_id": 1760, "nombre": "Chust"},
                  {"player_id": ROBERTO, "nombre": "Roberto Fernandez"},
                  {"player_id": GULACSI, "nombre": "Gulacsi"}],
}
# La de verdad (los dos pasos): Boye en `proteger`.
ORDEN_CON_BOYE = {**ORDEN_HOY, "proteger": ORDEN_HOY["proteger"]
                  + [{"player_id": BOYE, "nombre": "Boye"}]}
# Sin `fichar` (ganado o retirado) y con la venta aun escrita.
ORDEN_SIN_FICHAR = {k: v for k, v in ORDEN_HOY.items() if k != "fichar"}
# Caducada (el 02/11).
ORDEN_CADUCADA = {**ORDEN_HOY, "caduca": "2026-11-02T23:59:00+01:00"}
# Que ficha a otro (Hancko) y no a Adrian.
ORDEN_OTRO = {**ORDEN_HOY, "fichar": [{"player_id": 38290, "nombre": "Hancko",
                                        "puja": 4389900}]}
ORDENES = (("sin_orden", {}), ("hoy", ORDEN_HOY), ("con_boye", ORDEN_CON_BOYE),
           ("sin_fichar", ORDEN_SIN_FICHAR), ("caducada", ORDEN_CADUCADA))

_EQUIPOS = ("Athletic Club", "FC Barcelona", "Real Madrid", "Villarreal CF", "Celta",
            "Real Betis", "Sevilla FC", "Getafe CF", "Valencia CF", "Elche CF",
            "RCD Mallorca", "Girona FC", "CA Osasuna", "Rayo Vallecano", "Levante UD",
            "Deportivo Alaves", "RC Deportivo", "Real Sociedad", "Atletico de Madrid",
            "Malaga CF")


def _el_calendario() -> dict:
    """J12 (06/11-09/11) y J13 (20/11-23/11): diez partidos cada una."""
    partidos = []
    for jornada, dia, mes in ((12, 6, 11), (13, 20, 11)):
        inicio = datetime(2026, mes, dia, 20, 0, tzinfo=_UTC)
        for i in range(10):
            hora = inicio + timedelta(hours=(i // 3) * 24 + (i % 3) * 2)
            partidos.append({
                "matchday": jornada,
                "home": _EQUIPOS[(2 * i) % 20], "away": _EQUIPOS[(2 * i + 1) % 20],
                "kickoff": hora.isoformat(),
            })
    return {"season": "2026/27", "matches": partidos}


def _ficha(fila) -> dict:
    pid, nombre, pos, precio, sube, estado, prob, puntos, jugados, tasa, equipo = fila
    return {
        "id": pid, "name": nombre, "position": pos, "price": precio,
        "priceIncrement": sube, "status": estado, "points": puntos,
        "playedHome": (jugados + 1) // 2, "playedAway": jugados // 2, "teamID": equipo,
    }


def _nuestros(e) -> list:
    return [TODOS[i] for i in e["plantilla"]]


def _del_computer(e) -> list:
    return [TODOS[i] for i in e["mercado"] if i not in e["plantilla"]]


def _la_foto(e) -> dict:
    """La foto de Biwenger (la de `refresh_snapshot`) de un estado."""
    computer = _del_computer(e)
    ventas = [{"player": {"id": f[0]}, "price": f[3], "user": None} for f in computer]
    ventas += [{"player": {"id": pid}, "price": precio, "user": {"id": YO}}
               for pid, precio in sorted(EN_VENTA.items()) if pid in e["plantilla"]]
    ofertas = []
    for i, (pid, importe) in enumerate(sorted(e["pujas"].items())):
        ofertas.append({"id": 9000 + i, "amount": importe, "status": "waiting",
                        "requestedPlayers": [{"id": pid}], "from": {"id": YO}})
    for i, (pid, importe) in enumerate(sorted(e["ofertas"].items())):
        if pid in e["plantilla"]:
            ofertas.append({"id": 8000 + i, "amount": importe, "status": "waiting",
                            "requestedPlayers": [{"id": pid}], "from": None})
    nuestros = _nuestros(e)
    return {
        "timestamp": "2026-11-03T19:07:00+00:00",
        "league": {"id": 1, "user": {"id": YO, "name": "Pepe"}},
        "market": {"sales": ventas, "offers": ofertas,
                   "status": {"balance": e["saldo"], "maximumBid": e["maximo"]}},
        "my_team": [{"id": f[0], "price": f[3]} for f in nuestros],
        "catalog": {"data": {"players": {str(f[0]): _ficha(f)
                                         for f in nuestros + computer}}},
        "_estado": e["nombre"],
    }


def _el_status(e) -> dict:
    """Lo que la mejora lee del panel: el once, toda la liga, el
    escaparate y la plantilla entera."""
    computer = _del_computer(e)
    nuestros = _nuestros(e)
    liga = []
    for de_quien, filas in (("nuestro", nuestros), ("computer", computer)):
        for f in filas:
            pid, nombre, pos, precio, sube, estado, prob, puntos, jugados, tasa, equipo = f
            liga.append({
                "id": pid, "name": nombre, "position": pos, "price": precio,
                "price_increment": sube, "status": estado, "points": puntos,
                "played": jugados, "tasa": tasa, "team_id": equipo,
                "de_quien": de_quien, "starter_probability": prob,
            })
    once = [{"id": f[0], "name": f[1], "position": f[2], "starter_probability": f[6],
             "price": f[3]} for f in nuestros if f[0] in ONCE]
    escaparate = [{"id": f[0], "name": f[1], "position": f[2], "price": f[3],
                   "points": f[7], "played": f[8], "starter_probability": f[6]}
                  for f in computer]
    return {
        "todaLaLiga": {"players": liga},
        "lineup": {"players": once},
        "libro_del_escaparate": {"players": escaparate},
        "roster": {"players": [{"id": f[0], "name": f[1], "starter_probability": f[6]}
                               for f in nuestros]},
    }


def _normal(x):
    """Lo que sale de un motor, en algo que `json` escribe igual siempre."""
    if isinstance(x, dict):
        return {str(k): _normal(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (set, frozenset)):
        return sorted((_normal(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(x, (list, tuple)):
        return [_normal(v) for v in x]
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, float):
        return round(x, 6)
    return x


class _Escritor:
    """El escritor de Biwenger, de mentira: apunta y dice que si."""

    def __init__(self):
        self.llamadas = []

    def _si(self, que, **kw):
        self.llamadas.append([que, kw])
        return {"sent": True, "success": True, "http_status": 200}

    def place_bid(self, **kw):
        return self._si("place_bid", **kw)

    def cancel_bid(self, **kw):
        return self._si("cancel_bid", **kw)

    def accept_offer(self, **kw):
        return self._si("accept_offer", **kw)

    def list_player_for_sale(self, **kw):
        return self._si("list_player_for_sale", **kw)


def _cuando(texto):
    d = datetime.fromisoformat(texto)
    return d if d.tzinfo else d.replace(tzinfo=_UTC)


def _viva(orden, ahora) -> bool:
    """La orden vale a `ahora` (lo de `la_orden_del_gestor.validar`, sin
    importarla: los ids que pasan las guardias como `de_fuera`). Con
    basura, no."""
    try:
        return bool(orden) and ahora < _cuando(orden["caduca"])
    except (KeyError, TypeError, ValueError):
        return False


def _correr(e, ahora, horas, carpeta, *, orden=None, nombre="prueba", libro=None, v10=None):
    """`correr` de la mejora con el escritor de mentira: libros en la
    carpeta, sin leer nada de produccion. `libro`, si se da, manda sobre
    el del estado (las vueltas seguidas). {r, escritor, libro, vuelta,
    leen}: `leen`, lo que sacan del libro que deja el cierre
    (`la_mejora`), la rotacion y el motor viejo (`los_que_otros_venden`)
    y el relevo (`el_relevo`, con su interruptor y el de la mejora)."""
    from src.actions import la_mejora_del_once as mejora
    from src.actions.el_cierre_de_la_jornada import la_mejora as del_cierre
    from src.analysis.los_que_otros_venden import _de_la_mejora

    orden = orden or {}
    viva = _viva(orden, ahora)
    carpeta = Path(carpeta) / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "la_mejora.json"
    ruta.write_text(json.dumps(e["libro"] if libro is None else libro), encoding="utf-8")
    ronda = carpeta / "ronda.json"
    ronda.write_text("{}", encoding="utf-8")
    chollos = carpeta / "chollos.json"
    chollos.write_text("{}", encoding="utf-8")
    escritor = _Escritor()
    r = mejora.correr(
        status=_el_status(e), snapshot=_la_foto(e), v10=v10 or {},
        escritor_factory=lambda: escritor, ahora=ahora, libro_ruta=ruta,
        calendario=_el_calendario(),
        de_fuera={"orden": orden,
                  "vetados": ({n["player_id"] for n in orden.get("no_pujar") or []}
                              if viva else set()),
                  "protegidos": ({x["player_id"] for x in (orden.get("proteger") or [])
                                  + (orden.get("fichar") or [])} if viva else set()),
                  "libro_ronda": ronda, "libro_chollos": chollos,
                  "horas_jornada": horas, "puede_escribir": True, "en_curso": False,
                  "rotando": set(), "de_otra_jornada": set(), "avisos_de_ff": []})
    vuelta = carpeta / "la_mejora_vuelta.json"
    queda = json.loads(ruta.read_text(encoding="utf-8"))
    plantilla = set(e["plantilla"])
    with _Ademas({"BORDALAS_EL_RELEVO_NO_SE_VENDE": "1", "BORDALAS_LA_MEJORA_DEL_ONCE": "1"}):
        relevo = mejora.el_relevo(queda, plantilla=plantilla)
    leen = {"cierre": del_cierre(queda, plantilla, dict(e["pujas"])),
            "otros_venden": _de_la_mejora(queda),
            "relevo": relevo}
    return {"r": r, "escritor": escritor.llamadas, "libro": queda,
            "vuelta": (json.loads(vuelta.read_text(encoding="utf-8"))
                       if vuelta.exists() else None),
            "leen": leen}


def _la_foto_leida(e) -> dict:
    from src.actions.la_orden_del_gestor import leer_la_foto

    return leer_la_foto(_la_foto(e), YO)


def _la_liga(e) -> dict:
    return {p["id"]: p for p in _el_status(e)["todaLaLiga"]["players"]}


def _la_caja_de(e, orden, esta_vuelta=None, **kw):
    """`la_caja_de_la_jornada` sobre un estado, como la monta `correr`
    (sin ronda ni chollos)."""
    from src.actions import la_mejora_del_once as mejora

    return mejora.la_caja_de_la_jornada(
        _la_foto_leida(e), liga=_la_liga(e), orden=copy.deepcopy(orden),
        libro=copy.deepcopy(e["libro"]), solos=set(), inventario=set(),
        esta_vuelta=copy.deepcopy(esta_vuelta), **kw)


def _decidir_de(e, *, caja, horas, pendientes=frozenset(), protegidos=frozenset(), **kw):
    """`decidir` de la mejora sobre un estado, como lo llama `correr` (sin
    la parte de `correr` que lee libros): la caja y las horas, dadas."""
    from src.actions import la_mejora_del_once as mejora

    status = _el_status(e)
    liga = _la_liga(e)
    args = dict(
        once=status["lineup"]["players"], liga=liga,
        escaparate=status["libro_del_escaparate"]["players"], foto=_la_foto_leida(e),
        libro=copy.deepcopy(e["libro"]), inventario=set(),
        pendientes=set(pendientes), intocables=frozenset({"yamal", "lamine yamal"}),
        protegidos=set(protegidos), ya_pujados=set(), caja=caja, horas_jornada=horas,
        puede_escribir=True, en_curso=False,
        probabilidades={f[0]: f[6] for f in _nuestros(e)},
        estados={p["id"]: p["status"] for p in status["todaLaLiga"]["players"]},
        vendidos=set(),
    )
    args.update(kw)
    return mejora.decidir(**args)


# ============================================================
# LA BATERIA DE APAGADO (medida en main ANTES de tocar el codigo)
# ============================================================
#
#     Todo con la firma de main (sin los argumentos nuevos de `decidir`
#     y de `la_caja_de_la_jornada`).

# Las horas a la jornada: el paron (J13), el martes por la manana y por la
# noche, el miercoles 07:15, fuera de la ventana de comprar (< 40 h) y a
# menos de `HORAS_SOLVENCIA` (20 h, el suelo en rojo).
HORAS = (227.0, 83.9, 72.8, 61.75, 30.0, 13.75)

# Las cajas de la jornada: la de las 07:15, la de las 10:07, la de la mejora
# con el fallo (las 20:07, dos ventas), la de verdad de las 20:07 y una en
# rojo de verdad (Adrian y Unai ganados, nada vendido).
CAJAS = (-264776, -164276, 4902724, -7176, -7064076)

# (solo_si_sube, en_9900, a_la_salida, puja_fuerte): produccion primero.
BANDERAS = (
    (True, True, False, False),
    (False, True, False, False),
    (False, False, False, False),
)

# Lo que la orden deja quieto para la mejora (`correr`: los `fichar` y
# los de `vender_si_ficha` cuyo relevo sigue en pie) y lo protegido.
PENDIENTES = (frozenset(), frozenset({ADRIAN, ROBERTO}))
PROTEGIDOS = (frozenset(), frozenset({YAMAL, BOYE, ADRIAN}))

# Lo que esta vuelta ya hizo: nada, o la orden cobro a Roberto (el
# miercoles) y retiro una puja.
VUELTAS = (
    None,
    {"pujas": {}, "solas": set(), "cobros": {ROBERTO: 7180000}, "canceladas": set()},
)

# Lo minimo para que la mejora corra (lo que mira de los suyos) y los 26
# que enciende el YAML de produccion del 03/11 (origin/main df2cac90,
# .github/workflows/bordalas-live.yml, con EL PARTE VENDE), contados con
# `el_paso_0.interruptores_encendidos_en`.
ENTORNO_MINIMO = {
    "BORDALAS_LA_MEJORA_DEL_ONCE": "1",
    "BORDALAS_LA_MEJORA_SOLO_SI_SUBE": "1",
    "BORDALAS_LA_PUJA_EN_9900": "1",
}
PRODUCCION = {n: "1" for n in (
    "BORDALAS_COBRA_LA_RACHA", "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA", "BORDALAS_EL_CIERRE_DE_LA_JORNADA",
    "BORDALAS_EL_INFORME_DE_LA_MANANA", "BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE",
    "BORDALAS_EL_ONCE_UNA_VEZ", "BORDALAS_EL_PARTE_VENDE", "BORDALAS_JORNADAS_POR_SU_FECHA",
    "BORDALAS_LA_CARTERA", "BORDALAS_LA_JORNADA_DE_CADA_PAGINA",
    "BORDALAS_LA_MEJORA_DEL_ONCE", "BORDALAS_LA_MEJORA_SOLO_SI_SUBE",
    "BORDALAS_LA_MONEDA_DE_LA_LIGA", "BORDALAS_LA_ORDEN_DEL_GESTOR",
    "BORDALAS_LA_PUJA_EN_9900", "BORDALAS_LA_RONDA_DE_LA_MANANA", "BORDALAS_LA_ROTACION",
    "BORDALAS_LOS_CHOLLOS", "BORDALAS_REJA_CON_TOLERANCIA", "BORDALAS_REVENTA_SOLO_SI_JUEGA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL", "BORDALAS_REVISA_LAS_PUJAS_VIVAS",
    "BORDALAS_SIN_SUBASTA", "BORDALAS_SOLVENCIA_POR_SU_PLAZO", "BORDALAS_UN_SOLO_COLCHON",
)}
ENTORNOS = (("minimo", ENTORNO_MINIMO), ("produccion", PRODUCCION))

APAGADO = (None, "0", "")

# Los relojes de `correr`, con sus horas a la jornada (vie 06/11 20:00
# UTC): martes 10:07 y 20:07, miercoles 07:15 y jueves 05:50 (fuera de la
# ventana de comprar).
RELOJES = (
    (datetime(2026, 11, 3, 9, 7, tzinfo=_UTC), 82.9),
    (datetime(2026, 11, 3, 19, 7, tzinfo=_UTC), 72.8),
    (datetime(2026, 11, 4, 6, 15, tzinfo=_UTC), 61.75),
    (datetime(2026, 11, 5, 4, 50, tzinfo=_UTC), 39.2),
)


def _la_bateria(carpeta) -> list:
    """[(nombre, llamada)] de la mejora y de quien lee su libro, con la
    firma de main."""

    llamadas = []

    # 1. LA CAJA DE LA JORNADA: cada estado, cada orden, con y sin lo de
    # esta vuelta.
    for e in ESTADOS:
        for nombre_orden, orden in ORDENES:
            for v, vuelta in enumerate(VUELTAS):
                llamadas.append((
                    f"caja/{e['nombre']}/{nombre_orden}/{v}",
                    lambda e=e, orden=orden, vuelta=vuelta: _la_caja_de(e, orden, vuelta)))

    # 2. DECIDIR: cada estado, cada reloj, cada caja, las banderas de la
    # mejora, lo que la orden deja quieto y lo protegido.
    for e in ESTADOS:
        for horas in HORAS:
            for caja in CAJAS:
                for banderas in BANDERAS:
                    for p, pendientes in enumerate(PENDIENTES):
                        protegidos = PROTEGIDOS[p]
                        solo_si_sube, en_9900, a_la_salida, puja_fuerte = banderas
                        llamadas.append((
                            f"decidir/{e['nombre']}/{horas}/{caja}/{banderas}/{p}",
                            lambda e=e, horas=horas, caja=caja, solo_si_sube=solo_si_sube,
                            en_9900=en_9900, a_la_salida=a_la_salida,
                            puja_fuerte=puja_fuerte, pendientes=pendientes,
                            protegidos=protegidos:
                            _decidir_de(e, caja=caja, horas=horas, pendientes=pendientes,
                                        protegidos=protegidos, solo_si_sube=solo_si_sube,
                                        en_9900=en_9900, a_la_salida=a_la_salida,
                                        puja_fuerte=puja_fuerte)))

    # 3. CORRER, con el escritor de mentira, y lo que leen del libro que
    # deja: cada estado, cada reloj y cada orden.
    for e in ESTADOS:
        for ahora, horas in RELOJES:
            for nombre_orden, orden in ORDENES:
                nombre = f"{e['nombre']}_{ahora.strftime('%d%H%M')}_{nombre_orden}"
                llamadas.append((
                    f"correr/{e['nombre']}/{ahora.isoformat()}/{nombre_orden}",
                    lambda e=e, ahora=ahora, horas=horas, orden=orden, nombre=nombre:
                    _correr(e, ahora, horas, carpeta, orden=orden, nombre=nombre)))
    return llamadas


def _huellas(valores=APAGADO) -> dict:
    """{entorno/valor del interruptor: {llamada: sha256}}. El entorno se
    deja como estaba."""
    salida = {}
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_del_entorno, entorno in ENTORNOS:
            for valor in valores:
                with _Interruptores({**entorno, ENV: valor}):
                    huellas = {}
                    for nombre, llamada in _la_bateria(carpeta):
                        texto = json.dumps(_normal(llamada()), sort_keys=True,
                                           ensure_ascii=False, default=str)
                        huellas[nombre] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
                salida[f"{nombre_del_entorno}/{valor!r}"] = huellas
    return salida


def _la_huella(huellas: dict) -> str:
    """Una huella de todas: sha256 de las de cada llamada, en orden."""
    texto = "\n".join(f"{k} {v}" for k, v in sorted(huellas.items()))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# Medidas en main sin tocar (copia de origin/main df2cac90 con este
# fichero dentro) con `python -m src.analysis.test_la_orden_manda_en_el_cambio_v1
# --medir`, una por Python y por entorno (lo minimo de la mejora y los 26
# de produccion). Cualquier cambio querido en la mejora, `leer_la_foto`,
# `ejecutar`, `en_9900`, el cierre (`la_mejora`), `los_que_otros_venden`
# o el relevo la pone roja: se vuelve a medir en main, a proposito, en las
# dos versiones.
HUELLAS_DE_MAIN = {
    (3, 11): {
        "minimo": "63b48c5bbe16213269f3055451d75c0568a87d5e17048878a9262ed7f09102df",
        "produccion": "11e35aa0ab94f247214c4eedb0774d1c2a97619974509622215559da662ea5ee",
    },
    (3, 13): {
        "minimo": "63b48c5bbe16213269f3055451d75c0568a87d5e17048878a9262ed7f09102df",
        "produccion": "11e35aa0ab94f247214c4eedb0774d1c2a97619974509622215559da662ea5ee",
    },
}
LLAMADAS_DE_LA_BATERIA = (len(ESTADOS) * len(ORDENES) * len(VUELTAS)
                          + len(ESTADOS) * len(HORAS) * len(CAJAS) * len(BANDERAS)
                          * len(PENDIENTES)
                          + len(ESTADOS) * len(RELOJES) * len(ORDENES))


def medir() -> None:
    """La huella de la bateria, apagada, para `HUELLAS_DE_MAIN`."""
    todas = _huellas(APAGADO)
    por_entorno = {}
    for clave, huellas in todas.items():
        entorno = clave.split("/")[0]
        por_entorno.setdefault(entorno, set()).add(_la_huella(huellas))
    for entorno, huellas in sorted(por_entorno.items()):
        assert len(huellas) == 1, f"apagada depende de como se apague ({entorno})"
    n = {len(h) for h in todas.values()}
    print(f"Python {sys.version_info[:2]}: {n} llamadas")
    for entorno, huellas in sorted(por_entorno.items()):
        print(f"  {entorno}: {next(iter(huellas))}")


def volcar(ruta) -> None:
    """Las huellas de cada llamada, apagada, a `ruta` (JSON), para
    comparar main y la rama llamada a llamada."""
    todas = _huellas(APAGADO)
    Path(ruta).write_text(json.dumps({"python": list(sys.version_info[:2]), "huellas": todas},
                                     indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Python {sys.version_info[:2]}: {sum(len(h) for h in todas.values())} "
          f"salidas en {ruta}")


# ============================================================
# LAS PRUEBAS
# ============================================================

ENCENDIDO = {**PRODUCCION, ENV: "1"}
MIERCOLES = datetime(2026, 11, 4, 6, 15, tzinfo=_UTC)
HORAS_MIERCOLES = 61.75
MARTES_1107 = datetime(2026, 11, 3, 10, 7, tzinfo=_UTC)
MARTES_2007 = datetime(2026, 11, 3, 19, 7, tzinfo=_UTC)


def _el_miercoles(entorno, orden=ORDEN_HOY, libro=None, estado=EMIERCOLES) -> dict:
    """La vuelta del miercoles 04/11 a las 07:15, Adrian ganado, como en
    produccion: primero la orden (en el paso de la v10: lo que cobra va al
    estado de la vuelta) y despues la mejora (`correr`). {orden, mejora,
    vendidos, publicados, r, libro, leen}."""
    from src.actions import la_orden_del_gestor as la_orden

    with _Interruptores(entorno):
        foto = la_orden.leer_la_foto(_la_foto(estado), YO)
        foto.pop("de_managers", None)
        # La orden corre como en `la_orden_del_gestor.correr`: encendida y
        # valida; si no, no hace nada.
        acciones = []
        if la_orden.activa() and la_orden.validar(orden, MIERCOLES) is None:
            acciones = la_orden.decidir(
                copy.deepcopy(orden), **foto, ahora=MIERCOLES,
                horas_jornada=HORAS_MIERCOLES, en_curso=False,
                estados=la_orden.leer_los_estados(_la_foto(estado)))
        hechas = [{**a, "exito": True} for a in acciones
                  if a["accion"] in ("ACEPTAR_OFERTA_DEL_COMPUTER", "PONER_A_LA_VENTA",
                                     "PUJAR", "CANCELAR_PUJA")]
        v10 = {"timestamp": (MIERCOLES - timedelta(minutes=5)).isoformat(),
               "orden_del_gestor": {"hechas": hechas}}
        with tempfile.TemporaryDirectory() as carpeta:
            m = _correr(estado, MIERCOLES, HORAS_MIERCOLES, carpeta, orden=orden,
                        nombre="miercoles", libro=libro, v10=v10)
    todas = acciones + list(m["r"]["acciones"])
    return {
        "orden": acciones, "mejora": m["r"]["acciones"], "r": m["r"], "libro": m["libro"],
        "leen": m["leen"],
        "vendidos": sorted({a["player_id"] for a in todas
                            if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"}),
        "publicados": sorted({a["player_id"] for a in todas
                              if a["accion"] == "PONER_A_LA_VENTA"}),
    }


def _plan(m) -> dict:
    return (m["r"] or {}).get("plan") or {}


# 1. NACE APAGADO, UN LECTOR, SU FRASE, NADA AL IMPORTARSE

def test_nace_apagada_un_lector_y_su_frase():
    import ast
    from src.actions import la_mejora_del_once as mejora
    from src.telemetry.el_tablon import QUE_HACE

    assert mejora.ENV_LA_ORDEN_MANDA == ENV
    for valor in (None, "0", "", "no", "false", "2", "off", " 0 "):
        with _Interruptores({ENV: valor}):
            assert mejora.la_orden_manda_activa() is False, repr(valor)
    for valor in ("1", "true", "si", "yes", " SI ", "on", "sí", "Sí", " ON "):
        with _Interruptores({ENV: valor}):
            assert mejora.la_orden_manda_activa() is True, repr(valor)

    # Un solo sitio lo lee: `la_orden_manda_activa`, llamada solo desde
    # `la_orden_manda`, que se llama solo desde `correr`. Fuera de la
    # mejora, solo la frase del tablon.
    nombran = []
    for ruta in sorted(list((RAIZ / "src").rglob("*.py")) + list((RAIZ / "scripts").rglob("*.py"))):
        if ruta.name.startswith("test_"):
            continue
        if ENV in ruta.read_text(encoding="utf-8"):
            nombran.append(ruta.relative_to(RAIZ).as_posix())
    assert nombran == ["src/actions/la_mejora_del_once.py", "src/telemetry/el_tablon.py"], \
        nombran
    fuente = (RAIZ / "src" / "actions" / "la_mejora_del_once.py").read_text(encoding="utf-8")
    assert fuente.count(f'ENV_LA_ORDEN_MANDA = "{ENV}"') == 1
    assert fuente.count("ENV_LA_ORDEN_MANDA") == 2           # el nombre y su lector
    assert fuente.count("os.environ.get(ENV_LA_ORDEN_MANDA") == 1
    assert (fuente.count("la_orden_manda_activa()")
            - fuente.count("def la_orden_manda_activa()")) == 1     # en `la_orden_manda`
    assert (fuente.count("la_orden_manda(orden, libro, ahora)")) == 1   # en `correr`

    # Nada al importarse: ninguna sentencia de modulo llama al lector ni
    # mira el entorno.
    arbol = ast.parse(fuente)
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        if isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant):
            continue                                # el docstring
        texto = ast.dump(nodo)
        assert "la_orden_manda" not in texto and "environ" not in texto, \
            ast.unparse(nodo)[:120]

    # Y el inventario de los interruptores lo ve leido al llamarse.
    from scripts.los_interruptores import lectores

    lee = lectores(RAIZ / "src" / "actions" / "la_mejora_del_once.py")
    assert lee.get(ENV) == "AL_LLAMARSE", lee.get(ENV)

    frase = str(QUE_HACE.get(ENV) or "")
    assert "la orden del gestor" in frase and "la mejora del once" in frase, frase
    assert "suelta su cambio" in frase and "una sola venta" in frase, frase


def test_lo_que_el_paso_0_da_por_encendido():
    """Lo que el paso 0, el tablon, el panel y el ensayo dan por
    encendido (`el_paso_0.ENCENDIDO`), la mejora lo lee encendido, y al
    reves (como LA PRIMA QUE GANA)."""
    from src.actions import la_mejora_del_once as mejora
    from src.analysis import el_paso_0

    assert mejora.ENCENDIDA == el_paso_0.ENCENDIDO
    for valor in ('"1"', "1", '"on"', "on", '"sí"', '"Sí"', '"si"', '"true"', "true",
                  '"yes"', "'1'", '"0"', '""', '"no"', '"off"', '"false"', '"2"',
                  '"1"   # un motivo'):
        yaml = f"    env:\n      {ENV}: {valor}\n"
        en_el_paso_0 = ENV in el_paso_0.interruptores_encendidos_en(yaml)
        limpio = el_paso_0._limpio(valor)
        with _Interruptores({ENV: limpio}):
            assert mejora.la_orden_manda_activa() is en_el_paso_0, (valor, limpio)


# 2. APAGADO ES MAIN BYTE A BYTE

def test_apagada_es_main_byte_a_byte():
    """La bateria, con el interruptor sin poner, "0" y "", con lo minimo
    de la mejora y con los 26 de produccion: la huella de main, medida
    antes de tocar el codigo, en esta version de Python."""
    esperadas = HUELLAS_DE_MAIN.get(sys.version_info[:2])
    assert esperadas is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    todas = _huellas(APAGADO)
    assert len(todas) == len(ENTORNOS) * len(APAGADO), sorted(todas)
    for clave, huellas in todas.items():
        entorno = clave.split("/")[0]
        assert len(huellas) == LLAMADAS_DE_LA_BATERIA, (clave, len(huellas))
        assert _la_huella(huellas) == esperadas[entorno], (
            f"apagada ya no es main en Python {sys.version_info[:2]} ({clave}): "
            f"{_la_huella(huellas)} (main: {esperadas[entorno]})")


# 3. QUIEN MANDA

def test_la_orden_manda_quien():
    """`la_orden_manda`: los que entran por un cambio del libro que la
    orden VIVA (encendida y valida a `ahora`) esta fichando."""
    from src.actions import la_mejora_del_once as mejora

    libro = {str(ADRIAN): CAMBIO_ADRIAN, str(UNAI_SIMON): CAMBIO_UNAI}
    f = mejora.la_orden_manda
    with _Interruptores(ENCENDIDO):
        assert f(ORDEN_HOY, libro, MARTES_1107) == frozenset({ADRIAN})
        assert f(ORDEN_CON_BOYE, libro, MIERCOLES) == frozenset({ADRIAN})
        # La clave del libro como numero, y el id de `fichar` como texto.
        assert f({**ORDEN_HOY, "fichar": [{"player_id": str(ADRIAN), "puja": 4909900}]},
                 {ADRIAN: CAMBIO_ADRIAN}, MARTES_1107) == frozenset({ADRIAN})
        # Su propio cambio (Unai Simon) no es de la orden.
        assert f(ORDEN_HOY, {str(UNAI_SIMON): CAMBIO_UNAI}, MARTES_1107) == frozenset()
        # Sin `fichar`, ficha a otro, caducada, sin hora, sin libro: nadie.
        assert f(ORDEN_SIN_FICHAR, libro, MARTES_1107) == frozenset()
        assert f(ORDEN_OTRO, libro, MARTES_1107) == frozenset()
        assert f(ORDEN_CADUCADA, libro, MARTES_1107) == frozenset()
        assert f(ORDEN_HOY, libro, None) == frozenset()
        assert f(ORDEN_HOY, {}, MARTES_1107) == frozenset()
        assert f({}, libro, MARTES_1107) == frozenset()
        # Una orden que no vale (un `fichar` sin puja) no manda.
        assert f({**ORDEN_HOY, "fichar": [{"player_id": ADRIAN}]}, libro,
                 MARTES_1107) == frozenset()
    # La orden apagada: no ficha a nadie, no manda.
    with _Interruptores({k: v for k, v in ENCENDIDO.items()
                         if k != "BORDALAS_LA_ORDEN_DEL_GESTOR"}):
        assert f(ORDEN_HOY, libro, MARTES_1107) == frozenset()
    # Apagado: nadie, se mire lo que se mire.
    for valor in APAGADO:
        with _Interruptores({**PRODUCCION, ENV: valor}):
            assert f(ORDEN_HOY, libro, MARTES_1107) == frozenset()


# 4. EL CASO DE HOY: EL MIERCOLES, ADRIAN DENTRO

def test_el_caso_de_hoy_el_miercoles():
    """Adrian ganado en el reset del mie 04/11. Apagado (main): la orden
    cobra a Roberto y la mejora a Boye, dos ventas por un fichaje.
    Encendido: solo Roberto; la mejora suelta su cambio y lo dice."""
    apagado = _el_miercoles(PRODUCCION)
    assert apagado["vendidos"] == sorted({ROBERTO, BOYE}), apagado["vendidos"]
    assert [a["player_id"] for a in apagado["orden"]
            if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"] == [ROBERTO]
    assert [a["player_id"] for a in apagado["mejora"]
            if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"] == [BOYE]

    encendido = _el_miercoles(ENCENDIDO)
    assert encendido["vendidos"] == [ROBERTO], encendido["vendidos"]
    assert BOYE not in encendido["publicados"], encendido["publicados"]
    assert not [a for a in encendido["mejora"] if a.get("player_id") == BOYE], \
        encendido["mejora"]
    assert str(ADRIAN) not in encendido["libro"], encendido["libro"]
    cedidos = _plan(encendido).get("la_orden_manda")
    assert isinstance(cedidos, list) and len(cedidos) == 1, _plan(encendido)
    c = cedidos[0]
    assert (c["entra"], c["sale"]) == (ADRIAN, BOYE), c
    assert c["linea"].startswith("LA_ORDEN_MANDA: suelta Adrian Nino (35706) por "
                                 "Boye (12494)"), c["linea"]
    # Lo mismo con la orden de verdad (Boye en `proteger`): proteger no
    # frena la SALIDA de la mejora; solo la orden que manda.
    con_boye = _el_miercoles(PRODUCCION, orden=ORDEN_CON_BOYE)
    assert con_boye["vendidos"] == sorted({ROBERTO, BOYE}), con_boye["vendidos"]
    assert _el_miercoles(ENCENDIDO, orden=ORDEN_CON_BOYE)["vendidos"] == [ROBERTO]
    # Con Unai Simon tambien ganado, su cambio sigue: Gulacsi se vende.
    los_dos = _el_miercoles(ENCENDIDO, estado=EMIERCOLES_LOS_DOS)
    assert los_dos["vendidos"] == sorted({ROBERTO, GULACSI}), los_dos["vendidos"]


# 5. LA CAJA: UNA VENTA POR UN FICHAJE

def test_la_caja_cuenta_una_venta():
    """Con la puja de la orden por Adrian viva y el cambio aun en el
    libro: apagado la caja suma la venta de Roberto (la orden) y la de
    Boye (el libro) contra la misma puja; encendido, solo la de Roberto.

        11:07  -164.276 - 4.909.900 (Adrian) + 4.909.900 (Roberto, hasta su
               relevo) [+ 4.909.900 (Boye), apagado] = -164.276 [4.745.624]
        20:07  2.025.724 - 9.089.800 (Adrian y Unai Simon) + 4.909.900
               (Roberto) + 2.147.000 (Gulacsi) [+ 4.909.900] = -7.176
               [4.902.724]"""
    puja = 4909900
    # Por `correr`: la caja del plan.
    with tempfile.TemporaryDirectory() as carpeta:
        for e, ahora, horas, cajas in ((E1107, MARTES_1107, 81.9, (4745624, -164276)),
                                      (E2007, MARTES_2007, 72.8, (4902724, -7176))):
            with _Interruptores(PRODUCCION):
                apagado = _correr(e, ahora, horas, carpeta, orden=ORDEN_HOY,
                                  nombre=f"off_{e['nombre']}")
            with _Interruptores(ENCENDIDO):
                encendido = _correr(e, ahora, horas, carpeta, orden=ORDEN_HOY,
                                    nombre=f"on_{e['nombre']}")
            assert _plan(apagado)["caja"] == cajas[0], (e["nombre"], _plan(apagado)["caja"])
            assert _plan(encendido)["caja"] == cajas[1], (e["nombre"], _plan(encendido)["caja"])

    # Directa: el mismo calculo con y sin el cambio de la orden.
    for e in (E1107, E2007):
        de_siempre = _la_caja_de(e, ORDEN_HOY)
        manda = _la_caja_de(e, ORDEN_HOY, manda_la_orden=frozenset({ADRIAN}))
        assert de_siempre - manda == puja, (e["nombre"], de_siempre, manda)
        # Lo que nadie manda, lo de siempre.
        assert _la_caja_de(e, ORDEN_HOY, manda_la_orden=frozenset()) == de_siempre
    assert _la_caja_de(E2007, ORDEN_HOY) == 4902724
    assert _la_caja_de(E2007, ORDEN_HOY, manda_la_orden=frozenset({ADRIAN})) == -7176


# 6. SUELTA EL CAMBIO EN LA PRIMERA VUELTA

def test_suelta_el_cambio_con_la_puja_viva():
    """Las 11:07: la orden acaba de sustituir la puja. Encendido, la
    mejora suelta el cambio ya (Boye deja de salir por Adrian) y lo dice;
    apagado, lo guarda."""
    with tempfile.TemporaryDirectory() as carpeta:
        with _Interruptores(PRODUCCION):
            apagado = _correr(E1107, MARTES_1107, 81.9, carpeta, orden=ORDEN_HOY, nombre="off")
        with _Interruptores(ENCENDIDO):
            encendido = _correr(E1107, MARTES_1107, 81.9, carpeta, orden=ORDEN_HOY, nombre="on")
    assert str(ADRIAN) in apagado["libro"], apagado["libro"]
    assert "la_orden_manda" not in _plan(apagado), _plan(apagado)
    assert str(ADRIAN) not in encendido["libro"], encendido["libro"]
    cedidos = _plan(encendido)["la_orden_manda"]
    assert [(c["entra"], c["sale"]) for c in cedidos] == [(ADRIAN, BOYE)], cedidos
    # Ni publica ni cobra a Boye, ni puja por Adrian.
    for a in encendido["r"]["acciones"]:
        assert a.get("player_id") not in (BOYE, ADRIAN), a
    assert not [x for x in encendido["escritor"]
                if x[1].get("player_id") in (BOYE, ADRIAN)], encendido["escritor"]
    # En la vuelta de silencio tambien suelta (soltar no escribe).
    from src.actions import la_mejora_del_once as mejora
    with _Interruptores(ENCENDIDO):
        manda = mejora.la_orden_manda(ORDEN_HOY, E1107["libro"], MARTES_1107)
    d = _decidir_de(E1107, caja=-164276, horas=81.9, puede_escribir=False,
                    pendientes={ADRIAN, ROBERTO}, manda_la_orden=manda)
    assert d["soltar"] == [str(ADRIAN)] and d["acciones"] == [], d
    assert d["plan"]["la_orden_manda"][0]["entra"] == ADRIAN, d["plan"]


# 7. NUNCA LO VUELVE A APUNTAR

def test_no_lo_vuelve_a_apuntar():
    """Tres vueltas seguidas encendido (11:07, 20:07 y el miercoles con
    Adrian dentro): ni el libro ni una puja de la mejora por Adrian, y
    Boye nunca se vende por el."""
    with tempfile.TemporaryDirectory() as carpeta, _Interruptores(ENCENDIDO):
        uno = _correr(E1107, MARTES_1107, 81.9, carpeta, orden=ORDEN_HOY, nombre="uno")
        # A las 17:13 la mejora pujo por Unai Simon (por Gulacsi).
        dos = _correr(E2007, MARTES_2007, 72.8, carpeta, orden=ORDEN_HOY, nombre="dos",
                      libro={**uno["libro"], str(UNAI_SIMON): CAMBIO_UNAI})
        tres = _correr(EMIERCOLES, MIERCOLES, HORAS_MIERCOLES, carpeta, orden=ORDEN_HOY,
                       nombre="tres", libro=dos["libro"])
    for vuelta in (uno, dos, tres):
        assert str(ADRIAN) not in vuelta["libro"], vuelta["libro"]
        for a in vuelta["r"]["acciones"]:
            assert a.get("player_id") not in (ADRIAN, BOYE), a
    # La segunda y la tercera ya no tienen nada que soltar de la orden.
    assert "la_orden_manda" not in _plan(dos) and "la_orden_manda" not in _plan(tres)


# 8. LO QUE LEEN EL LIBRO

def test_los_que_leen_el_libro_ya_no_lo_ven():
    """El cierre (`la_mejora`), la rotacion y el motor viejo
    (`los_que_otros_venden`) y el relevo leen el libro que deja `correr`:
    encendido, ni Boye sale ni Adrian entra por la mejora."""
    with tempfile.TemporaryDirectory() as carpeta:
        with _Interruptores(PRODUCCION):
            apagado = _correr(E2007, MARTES_2007, 72.8, carpeta, orden=ORDEN_HOY, nombre="off")
        with _Interruptores(ENCENDIDO):
            encendido = _correr(E2007, MARTES_2007, 72.8, carpeta, orden=ORDEN_HOY, nombre="on")
    assert BOYE in apagado["leen"]["cierre"]["vende"], apagado["leen"]
    assert {ADRIAN, BOYE} <= apagado["leen"]["otros_venden"], apagado["leen"]
    assert BOYE not in encendido["leen"]["cierre"]["vende"], encendido["leen"]
    assert GULACSI in encendido["leen"]["cierre"]["vende"], encendido["leen"]
    assert not {ADRIAN, BOYE} & encendido["leen"]["otros_venden"], encendido["leen"]
    assert {UNAI_SIMON, GULACSI} <= encendido["leen"]["otros_venden"], encendido["leen"]
    # El relevo (con la plantilla): Adrian aun no es nuestro, asi que en
    # ninguno de los dos; el miercoles, con Adrian dentro, solo apagado.
    apagado_mie = _el_miercoles(PRODUCCION, estado=EMIERCOLES_LOS_DOS)
    assert apagado_mie["leen"]["relevo"]["entran"] >= {ADRIAN}, apagado_mie["leen"]
    encendido_mie = _el_miercoles(ENCENDIDO, estado=EMIERCOLES_LOS_DOS)
    assert ADRIAN not in encendido_mie["leen"]["relevo"]["entran"], encendido_mie["leen"]
    assert BOYE not in encendido_mie["leen"]["cierre"]["vende"], encendido_mie["leen"]


# 9. SIN FANTASMAS

def test_sin_fichar_sin_fantasma():
    """Encendido, la mejora suelta el cambio a las 11:07. A las 20:07 el
    gestor quita `fichar` (la puja sigue viva): Adrian no vuelve al libro
    ni la mejora puja por el; el miercoles, ganado, es uno mas: Boye no
    se vende por el. Y la caja no cuenta la venta de Boye."""
    with tempfile.TemporaryDirectory() as carpeta, _Interruptores(ENCENDIDO):
        uno = _correr(E1107, MARTES_1107, 81.9, carpeta, orden=ORDEN_HOY, nombre="uno")
        dos = _correr(E2007, MARTES_2007, 72.8, carpeta, orden=ORDEN_SIN_FICHAR, nombre="dos",
                      libro={**uno["libro"], str(UNAI_SIMON): CAMBIO_UNAI})
    assert str(ADRIAN) not in uno["libro"] and str(ADRIAN) not in dos["libro"], dos["libro"]
    assert not [a for a in dos["r"]["acciones"] if a.get("player_id") in (ADRIAN, BOYE)], \
        dos["r"]["acciones"]
    # Sin cambio de la mejora: Roberto (la orden, su relevo con puja viva)
    # y Gulacsi (Unai Simon); Boye no.
    assert _plan(dos)["caja"] == -7176, _plan(dos)["caja"]
    mie = _el_miercoles(ENCENDIDO, orden=ORDEN_SIN_FICHAR, libro=dos["libro"])
    assert mie["vendidos"] == [ROBERTO], mie["vendidos"]
    assert BOYE not in mie["publicados"], mie["publicados"]
    assert str(ADRIAN) not in mie["libro"], mie["libro"]


# 10. SIN ORDEN QUE MANDE, LO DE SIEMPRE

def test_sin_orden_que_mande_lo_de_siempre():
    """Encendido, con la orden apagada, caducada, sin `fichar` desde el
    principio o fichando a otro, la mejora hace lo mismo que apagada (su
    cambio sigue y Boye sale por Adrian). Y su propio cambio (Unai Simon
    por Gulacsi) sigue siempre."""
    sin_la_orden = {k: v for k, v in ENCENDIDO.items() if k != "BORDALAS_LA_ORDEN_DEL_GESTOR"}
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre, orden, entorno in (("apagada", ORDEN_HOY, sin_la_orden),
                                       ("caducada", ORDEN_CADUCADA, ENCENDIDO),
                                       ("sin_fichar", ORDEN_SIN_FICHAR, ENCENDIDO),
                                       ("otro", ORDEN_OTRO, ENCENDIDO),
                                       ("sin_orden", {}, ENCENDIDO)):
            base = {k: v for k, v in entorno.items() if k != ENV}
            with _Interruptores(base):
                de_siempre = _correr(E2007, MARTES_2007, 72.8, carpeta, orden=orden,
                                     nombre=f"off_{nombre}")
            with _Interruptores(entorno):
                ahora = _correr(E2007, MARTES_2007, 72.8, carpeta, orden=orden,
                                nombre=f"on_{nombre}")
            assert _normal(ahora) == _normal(de_siempre), nombre
            assert str(ADRIAN) in ahora["libro"] and str(UNAI_SIMON) in ahora["libro"], \
                (nombre, ahora["libro"])
    # El miercoles con la orden caducada: lo de main (Boye sale por Adrian).
    assert _el_miercoles(ENCENDIDO, orden=ORDEN_CADUCADA)["vendidos"] == [BOYE]


# 11. NUNCA LANZA

def test_nunca_lanza():
    from src.actions import la_mejora_del_once as mejora

    with _Interruptores(ENCENDIDO):
        for orden in (None, 3, "x", [], {"fichar": "x"}, {"fichar": [None, 3, {"player_id": []}]},
                      {"caduca": "x", "fichar": [{"player_id": ADRIAN, "puja": 1}]},
                      {**ORDEN_HOY, "fichar": [{"player_id": True, "puja": 1}]}):
            for libro in (None, 3, "x", [], {None: None}, {"x": {"sale": "y"}},
                          {str(ADRIAN): None}, {str(ADRIAN): CAMBIO_ADRIAN}):
                for ahora in (None, "x", 3, MARTES_1107, datetime(2026, 11, 3, 10, 7)):
                    r = mejora.la_orden_manda(orden, libro, ahora)
                    assert isinstance(r, frozenset), (orden, libro, ahora, r)
        # Sin zona horaria: se toma por UTC, como el resto de la mejora.
        assert mejora.la_orden_manda(ORDEN_HOY, {str(ADRIAN): CAMBIO_ADRIAN},
                                     datetime(2026, 11, 3, 10, 7)) == frozenset({ADRIAN})
        # `decidir` y la caja con basura en lo que manda la orden.
        for basura in (frozenset({"x"}), {None}, frozenset({ADRIAN, "35706"})):
            _decidir_de(E1107, caja=-164276, horas=81.9, manda_la_orden=basura)
            _la_caja_de(E1107, ORDEN_HOY, manda_la_orden=basura)
    # `correr` con una orden basura: no lanza, no suelta nada y sale lo
    # mismo que apagado (la basura que main no sabe leer, la misma).
    with tempfile.TemporaryDirectory() as carpeta:
        for i, orden in enumerate(({"fichar": "x"}, {"caduca": None, "fichar": [3]},
                                   {**ORDEN_HOY, "caduca": "x"},
                                   {**ORDEN_HOY, "fichar": [{"player_id": ADRIAN}]})):
            with _Interruptores(PRODUCCION):
                de_siempre = _correr(E1107, MARTES_1107, 81.9, carpeta, orden=orden,
                                     nombre=f"off{i}")
            with _Interruptores(ENCENDIDO):
                r = _correr(E1107, MARTES_1107, 81.9, carpeta, orden=orden, nombre=f"on{i}")
            assert r["r"]["activa"] is True, r["r"]
            assert _normal(r) == _normal(de_siempre), (orden, r["r"]["motivo"])
            assert str(ADRIAN) in r["libro"], (orden, r["libro"])


# 12. EL ENTORNO NO DECIDE (doctrina 104)

def test_el_entorno_no_decide_esta_guardia():
    """Con todo lo de fuera puesto (los del tablon, este incluido, la puja
    fuerte, la hucha, la prima, el relevo, uno que no existe), cada prueba
    da lo mismo, y al salir el entorno es el de antes."""
    from src.analysis.el_paso_0 import PREFIJO
    from src.telemetry.el_tablon import QUE_HACE

    de_fuera = {n: "1" for n in QUE_HACE if n.startswith(PREFIJO)}
    de_fuera.update({PREFIJO + "SIN_REVENTA": "1", PREFIJO + "BID_SALT": "otra-sal",
                     PREFIJO + "LA_MEJORA_PUJA_FUERTE": "1", PREFIJO + "LA_HUCHA": "1",
                     PREFIJO + "LA_PRIMA_QUE_GANA": "1",
                     PREFIJO + "EL_RELEVO_NO_SE_VENDE": "1",
                     PREFIJO + "UNO_QUE_NO_EXISTE": "si", ENV: "1",
                     "GITHUB_RUN_ID": "41700251364"})
    antes = {k: os.environ.get(k) for k in de_fuera}
    os.environ.update(de_fuera)
    try:
        with _Interruptores({"BORDALAS_LA_MEJORA_DEL_ONCE": "1"}):
            dentro = sorted(k for k in os.environ
                            if k.startswith(PREFIJO) and k not in DE_LA_VERJA)
            assert dentro == ["BORDALAS_LA_MEJORA_DEL_ONCE"], dentro
            assert "GITHUB_RUN_ID" not in os.environ
        assert {k: os.environ.get(k) for k in de_fuera} == de_fuera
        for test in TESTS:
            if test in (test_apagada_es_main_byte_a_byte, test_el_entorno_no_decide_esta_guardia):
                continue
            test()
            assert {k: os.environ.get(k) for k in de_fuera} == de_fuera, test.__name__
    finally:
        for k, v in antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


TESTS = [
    test_nace_apagada_un_lector_y_su_frase,
    test_lo_que_el_paso_0_da_por_encendido,
    test_apagada_es_main_byte_a_byte,
    test_la_orden_manda_quien,
    test_el_caso_de_hoy_el_miercoles,
    test_la_caja_cuenta_una_venta,
    test_suelta_el_cambio_con_la_puja_viva,
    test_no_lo_vuelve_a_apuntar,
    test_los_que_leen_el_libro_ya_no_lo_ven,
    test_sin_fichar_sin_fantasma,
    test_sin_orden_que_mande_lo_de_siempre,
    test_nunca_lanza,
    test_el_entorno_no_decide_esta_guardia,
]


def main() -> None:
    if "--medir" in sys.argv:
        medir()
        return
    if "--volcar" in sys.argv:
        volcar(sys.argv[sys.argv.index("--volcar") + 1])
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
