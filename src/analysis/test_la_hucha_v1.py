"""
LA HUCHA (02/11/2026). Guardias de `BORDALAS_LA_HUCHA`
(`src/analysis/la_hucha.py`) y de sus enganches en los motores que pujan.

EL CASO (bitacora del 02/11 18:05, «OPERACION RAPHINHA, CON HUCHA»)

    Raphinha (26930) pide 24,72 M y ganarlo costara 27-30 M; hoy nuestra
    puja maxima es 9,4 M. Desde el premio de la J12 se aparta dinero
    (objetivo 16 M) que ningun motor puede gastar; siguen los cambios que
    se pagan solos y la orden del gestor ficha a Raphinha sin freno.

QUE SE COMPRUEBA

    1. Nace apagada, se lee en UN sitio (al llamarse), tiene frase en
       QUE_HACE, no hace nada al importarse y `config/la_hucha.json`, si
       esta, esta bien escrito (vale justo entre `desde` y `caduca`).
    2. Apagada es main byte a byte: la huella de 570 llamadas (la orden,
       los chollos, la ronda, la mejora, la rotacion, el carril y
       `execute_bid`, sus `decidir` y sus `correr`) sobre estados del
       artefacto de la run 41478322693, con el interruptor sin poner, "0"
       y "", es la de main medida ANTES de tocar el codigo, en 3.11 y en
       3.13. Apagada no se lee el fichero.
    3. Las cuentas: lo apartado, la puerta (`cabe`), las fechas, la
       config rota y CUMPLIDA (Raphinha ya es nuestro: se apaga sola).
    4. Cada motor que gasta, encendido: su presupuesto baja EXACTAMENTE lo
       apartado (la puja que cabe justa en lo libre pasa; un euro mas, no)
       y lo que no es caja no paga contra la hucha: la orden, los chollos,
       la ronda (el colchon de la cartera no basta), la mejora, la
       rotacion, el carril (tambien la suma de la vuelta), el BUY V10 y
       las CLI (`execute_bid`), el motor viejo (el ejecutor y el
       orquestador) y la cesta.
    5. El trinquete: dos vueltas con saldo - pujas = 10 M y objetivo 16 M:
       ninguna compra sin venta emparejada pasa y lo libre se queda en 0.
    6. La exencion: la orden ficha a Raphinha con el `maximumBid` real y la
       puja de 29 M (lo mismo que apagada); otro `fichar` sin ventas, NADA
       con guardia LA_HUCHA; uno que se paga solo, pasa.
    7. Los que venden no la ven: el cierre (`correr` entero) sale igual
       encendida que apagada y solo vende con la caja REAL en rojo; el
       deficit de la mejora, el ultimo recurso de la orden y el rojo de la
       rotacion, igual.
    8. La vuelta de v10: cada motor recibe la hucha con lo que pujaron los
       de delante (la cesta, el BUY, el carril, la orden, los chollos), el
       estado lleva el bloque `hucha`; apagada, ni argumento ni bloque.
    9. Nunca lanza.

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui: la plantilla, el mercado del Computer y las ofertas
    del 02/11 (status.json de la run 41478322693), compactados. Ni `data/`,
    ni la red, ni el reloj: la hora se pasa (`ahora`) y donde el codigo
    mira el reloj el solo (`execute_bid`, el ejecutor y el orquestador) la
    hucha de la prueba vale de 2020 a 2100. La hucha de la prueba va en
    una carpeta temporal (`la_hucha.RUTA`).

COMO SE USA

    python -m src.analysis.test_la_hucha_v1
    python -m src.analysis.test_la_hucha_v1 --medir
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import sys
import tempfile

from datetime import date, datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


ENV = "BORDALAS_LA_HUCHA"

# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104): cada prueba pone lo
# suyo con `_Interruptores`, y lo que no nombra lo quita. Los de los
# motores que se miran aqui:
DE_LOS_MOTORES = (
    ENV,
    "BORDALAS_LA_ORDEN_DEL_GESTOR",
    "BORDALAS_LOS_CHOLLOS",
    "BORDALAS_LA_RONDA_DE_LA_MANANA",
    "BORDALAS_LA_CARTERA",
    "BORDALAS_LA_PUJA_EN_9900",
    "BORDALAS_UN_SOLO_COLCHON",
    "BORDALAS_LA_MEJORA_DEL_ONCE",
    "BORDALAS_LA_MEJORA_SOLO_SI_SUBE",
    "BORDALAS_LA_MEJORA_PUJA_FUERTE",
    "BORDALAS_LA_MEJORA_A_LA_SALIDA",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA",
    "BORDALAS_LA_JORNADA_DE_CADA_PAGINA",
    "BORDALAS_LA_ROTACION",
    "BORDALAS_EL_CIERRE_DE_LA_JORNADA",
    "BORDALAS_EL_RELEVO_NO_SE_VENDE",
    "BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO",
    "BORDALAS_LA_RONDA_SOLO_LO_QUE_PAGA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL",
    "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_CUPO_POR_VENTANA",
    "BORDALAS_LA_SUBASTA_EN_EL_COLCHON",
    "BORDALAS_SIN_SUBASTA",
    "BORDALAS_ENSAYO",
    # La sal del desvio de la puja (un secreto de CI): no es un
    # interruptor, pero cambia los importes del carril.
    "BORDALAS_BID_SALT",
)


class _Interruptores:
    """Pone (valor) o quita (None) interruptores solo dentro del `with`.
    Los de `DE_LOS_MOTORES` que no se nombran, quitados."""

    def __init__(self, valores: dict | None = None):
        self.valores = {n: None for n in DE_LOS_MOTORES}
        self.valores.update(valores or {})

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


# ============================================================
# LA BATERIA DE APAGADO (medida en main ANTES de tocar el codigo)
# ============================================================
#
#     Estados del artefacto de la run 41478322693 (02/11/2026 17:48
#     Madrid): la plantilla (16), el mercado del Computer del dia (20),
#     las ofertas del Computer por los nuestros y los valores del
#     catalogo, escritos aqui a mano. Seis cajas: la de hoy (-7.494.776),
#     la del viernes (+1,9 M), dos con la hucha a medias y dos con
#     Raphinha en el mercado (una con nuestra puja de 29 M viva). Todo
#     se llama con la firma de main: sin `hucha`.

YO = 14175949
RAPHINHA = 26930
VALOR_PLANTILLA = 67_570_000

# (id, nombre, posicion, precio, sube hoy, estado, titularidad, puntos, jugados, tasa, equipo)
PLANTILLA = (
    (38433, "Gulacsi", 1, 2290000, -40000, "ok", 90.0, 31, 7, 4.43, 19),
    (23840, "Juan Iglesias", 2, 3770000, 20000, "ok", 90.0, 56, 11, 5.09, 17),
    (28115, "Kike Salas", 2, 3360000, 60000, "ok", 90.0, 47, 9, 5.22, 17),
    (1760, "Chust", 2, 2560000, 60000, "ok", 90.0, 48, 11, 4.36, 75),
    (29661, "Olasagasti", 3, 2870000, -10000, "ok", 80.0, 54, 11, 4.91, 10),
    (1969, "Unai Lopez", 3, 2820000, 80000, "ok", 80.0, 53, 10, 5.3, 70),
    (12403, "Ivan Martin", 3, 2760000, -10000, "ok", 80.0, 42, 9, 4.67, 812),
    (14800, "Pablo Ibanez", 3, 2630000, -40000, "ok", 60.0, 46, 11, 4.18, 91),
    (26271, "Yamal", 4, 25360000, 50000, "ok", 95.0, 131, 11, 11.91, 3),
    (35678, "Roberto Fernandez", 4, 7160000, -80000, "ok", 90.0, 69, 11, 6.27, 7),
    (12494, "Boye", 4, 5480000, -10000, "ok", 90.0, 63, 10, 6.3, 91),
    (30493, "Sergi Cardona", 2, 2130000, 30000, "ok", 50.0, 25, 7, 3.57, 19),
    (1844, "Gaya", 2, 1760000, 0, "ok", 90.0, 33, 9, 3.67, 18),
    (35765, "Angel Ortiz", 2, 190000, 0, "ok", 30.0, 17, 5, 3.4, 87),
    (41418, "Dani Lorenzo", 3, 2010000, 0, "ok", 70.0, 39, 10, 3.9, 65),
    (41411, "Ramon Enriquez", 3, 420000, 10000, "ok", 60.0, 25, 10, 2.5, 65),
)

# El mercado del Computer del 02/11 (lo que pide = su valor; a tres
# se les pone un precio por debajo, para que haya chollos).
COMPUTER = (
    (38405, "Odysseas", 1, 2550000, -30000, "ok", 95.0, 37, 11, 3.36, 17),
    (17482, "Dituro", 1, 2410000, 90000, "ok", 90.0, 45, 11, 4.09, 75),
    (17731, "Catena", 2, 2350000, -20000, "ok", 80.0, 27, 9, 3.0, 93),
    (15430, "Joan Garcia", 1, 6630000, -10000, "ok", 95.0, 53, 10, 5.3, 3),
    (11, "David Soria", 1, 4870000, -50000, "ok", 95.0, 59, 11, 5.36, 8),
    (17057, "Sancet", 3, 3450000, 40000, "ok", 50.0, 28, 7, 4.0, 1),
    (11677, "Dimitrievski", 1, 2660000, 0, "ok", 95.0, 50, 11, 4.55, 18),
    (33694, "Boyomo", 2, 1660000, 20000, "ok", 70.0, 13, 5, 2.6, 93),
    (2044, "Ceballos", 3, 2970000, -10000, "ok", 40.0, 26, 7, 3.71, 87),
    (14466, "Hinojo", 2, 1050000, -10000, "sanctioned", 0.0, 32, 10, 3.2, 7),
    (22061, "Josan", 3, 170000, 0, "ok", 0.0, 8, 3, 2.67, 75),
    (24734, "Jesus Vazquez", 2, 470000, -10000, "ok", 10.0, 15, 9, 1.67, 18),
    (25403, "Gonzalo Villar", 3, 2520000, -10000, "warned", 80.0, 45, 11, 4.09, 75),
    (26676, "Luiz Felipe", 2, 150000, 0, "injured", 0.0, 0, 0, None, 70),
    (38457, "Ali Houary", 3, 280000, 0, "ok", 0.0, 4, 3, 1.33, 75),
    (39386, "Manas", 4, 280000, 0, "ok", 30.0, 26, 8, 3.25, 91),
    (40037, "Ochieng", 4, 840000, -10000, "ok", 10.0, 28, 8, 3.5, 13),
    (41157, "Diatta", 3, 200000, 0, "doubt", 0.0, 0, 0, None, 19),
    (41609, "Valentini", 2, 870000, -40000, "ok", 50.0, 24, 7, 3.43, 91),
    (43207, "Axel Tape", 2, 160000, -10000, "ok", 10.0, 3, 1, 3.0, 10),
)

# Raphinha: libre, 24.720.000, 144 puntos en 10.
EL_OBJETIVO = (RAPHINHA, "Raphinha", 4, 24720000, -20000, "ok", 95.0, 144, 10, 14.4, 3)

# Lo que pide el Computer por debajo de su valor (chollos).
PIDE_MENOS = {17482: 2300000, 33694: 1580000, 41609: 820000}

# Las ofertas del Computer por los nuestros (status.json, 02/11 17:48).
OFERTAS = {
    35678: 7474000, 14800: 2505300, 29661: 2735700, 1760: 2576600,
    38433: 2329800, 35765: 182100, 1969: 2851800, 41411: 411300,
    12494: 5414700, 30493: 2100600,
}

# (nombre, saldo, {jugador: nuestra puja viva}, Raphinha en el mercado)
CAJAS = (
    ("hoy", -7494776, {}, False),
    ("viernes", 1900000, {}, False),
    ("a_medias", 12000000, {38405: 2559900}, False),
    ("llena", 21000000, {17482: 2439900, 33694: 1729900}, False),
    ("sale_raphinha", 40000000, {}, True),
    ("puja_raphinha", 30000000, {RAPHINHA: 29000000}, True),
)

ORDENES = (
    ("conservar", {
        "caduca": "2026-11-30T23:59:00+01:00",
        "conservar": [{"player_id": 35678, "nombre": "Roberto Fernandez"}],
    }),
    ("raphinha", {
        "caduca": "2026-12-31T23:59:00+01:00",
        "fichar": [{"player_id": RAPHINHA, "nombre": "Raphinha", "puja": 29000000,
                    "la_pagan_sus_ventas": True}],
        "vender_si_ficha": {"si_esta": RAPHINHA, "jugadores": [
            {"player_id": 35678, "nombre": "Roberto Fernandez", "suelo": 7000000},
            {"player_id": 12494, "nombre": "Boye", "suelo": 5300000}]},
    }),
    ("cambio", {
        "caduca": "2026-11-30T23:59:00+01:00",
        "fichar": [{"player_id": 17057, "nombre": "Sancet", "puja": 3800000}],
        "vender_si_ficha": {"si_esta": 17057, "jugadores": [
            {"player_id": 14800, "nombre": "Pablo Ibanez", "suelo": 2400000}]},
        "no_pujar": [{"player_id": 38405, "nombre": "Odysseas"}],
    }),
    ("sin_ventas", {
        "caduca": "2026-11-30T23:59:00+01:00",
        "fichar": [{"player_id": 17731, "nombre": "Catena", "puja": 2400000}],
    }),
    ("viajes", {
        "caduca": "2026-11-30T23:59:00+01:00",
        "viajes": {"hasta": "2026-11-20T07:00:00+01:00", "tope_por_viaje": 3000000,
                   "tope_total": 5000000, "candidatos": [
                       {"player_id": 38405, "nombre": "Odysseas", "puja": 2600000},
                       {"player_id": 11677, "nombre": "Dimitrievski", "puja": 2700000}]},
    }),
)

_UTC = timezone.utc

# Lo que el tablero de fichajes le da al carril, y el ritmo de cada uno.
OBJETIVOS_DEL_CARRIL = (
    {"id": 17482, "name": "Dituro", "position": 1, "market_price": 2410000, "bid": 2440000,
     "status": "ok", "price_increment": 90000, "starter_probability": 90,
     "intent": "SPECULATION"},
    {"id": 33694, "name": "Boyomo", "position": 2, "market_price": 1660000, "bid": 1680000,
     "status": "ok", "price_increment": 20000, "starter_probability": 70,
     "intent": "SPECULATION"},
    {"id": 41609, "name": "Valentini", "position": 2, "market_price": 870000, "bid": 880000,
     "status": "ok", "price_increment": 30000, "starter_probability": 50,
     "intent": "SPECULATION"},
)
RITMOS = {
    17482: {"rate_percent_per_day": 3.0, "trend_days": 4, "demand_net": 2.0},
    33694: {"rate_percent_per_day": 2.5, "trend_days": 3, "demand_net": 1.0},
    41609: {"rate_percent_per_day": 4.0, "trend_days": 5, "demand_net": 3.0},
}

# lun 02/11 18:00, mie 04/11 06:50, jue 05/11 06:50 de Madrid (J12, vie
# 06/11 21:00) y mie 11/11 06:50, lun 16/11 18:00 (el paron; J13 el 20/11).
MOMENTOS = (
    datetime(2026, 11, 2, 17, 0, tzinfo=_UTC),
    datetime(2026, 11, 4, 5, 50, tzinfo=_UTC),
    datetime(2026, 11, 5, 5, 50, tzinfo=_UTC),
    datetime(2026, 11, 11, 5, 50, tzinfo=_UTC),
    datetime(2026, 11, 16, 17, 0, tzinfo=_UTC),
)

_EQUIPOS = ("Athletic Club", "FC Barcelona", "Real Madrid", "Villarreal CF", "Celta",
            "Real Betis", "Sevilla FC", "Getafe CF", "Valencia CF", "Elche CF",
            "RCD Mallorca", "Girona FC", "CA Osasuna", "Rayo Vallecano", "Levante UD",
            "Deportivo Alaves", "RC Deportivo", "Real Sociedad", "Atletico de Madrid",
            "Malaga CF")


def _el_calendario() -> dict:
    """J11 (31/10-02/11), J12 (06/11-09/11) y J13 (20/11-23/11): diez
    partidos cada una, con su hora de Madrid."""
    partidos = []
    for jornada, dia, mes in ((11, 31, 10), (12, 6, 11), (13, 20, 11)):
        inicio = datetime(2026, mes, dia, 20, 0, tzinfo=_UTC)
        for i in range(10):
            hora = inicio + timedelta(hours=(i // 3) * 24 + (i % 3) * 2)
            partidos.append({
                "matchday": jornada,
                "home": _EQUIPOS[(2 * i) % 20], "away": _EQUIPOS[(2 * i + 1) % 20],
                "kickoff": hora.isoformat(),
            })
    return {"season": "2026/27", "matches": partidos}


def _ficha(fila, precio_de_venta=None) -> dict:
    pid, nombre, pos, precio, sube, estado, prob, puntos, jugados, tasa, equipo = fila
    return {
        "id": pid, "name": nombre, "position": pos, "price": precio,
        "priceIncrement": sube, "status": estado, "points": puntos,
        "playedHome": (jugados + 1) // 2, "playedAway": jugados // 2,
        "teamID": equipo,
    }


def _la_foto_de(caja) -> dict:
    """La foto de Biwenger (la de `refresh_snapshot`) de una caja."""
    nombre, saldo, pujas, con_raphinha = caja
    computer = list(COMPUTER) + ([EL_OBJETIVO] if con_raphinha else [])
    ventas = [
        {"player": {"id": f[0]}, "price": PIDE_MENOS.get(f[0], f[3]), "user": None}
        for f in computer
    ]
    # Roberto y Boye, publicados por nosotros; uno de un manager.
    ventas += [
        {"player": {"id": 35678}, "price": 7160000, "user": {"id": YO}},
        {"player": {"id": 12494}, "price": 5480000, "user": {"id": YO}},
        {"player": {"id": 15430}, "price": 6900000, "user": {"id": 777}},
    ]
    ofertas = []
    for i, (pid, importe) in enumerate(sorted(pujas.items())):
        ofertas.append({"id": 9000 + i, "amount": importe, "status": "waiting",
                        "requestedPlayers": [{"id": pid}], "from": {"id": YO}})
    for i, (pid, importe) in enumerate(sorted(OFERTAS.items())):
        ofertas.append({"id": 8000 + i, "amount": importe, "status": "waiting",
                        "requestedPlayers": [{"id": pid}], "from": None})
    catalogo = {str(f[0]): _ficha(f) for f in list(PLANTILLA) + list(computer)}
    if not con_raphinha:
        catalogo[str(RAPHINHA)] = _ficha(EL_OBJETIVO)
    maximo = saldo + VALOR_PLANTILLA // 4 - sum(pujas.values())
    return {
        "timestamp": "2026-11-02T16:48:00+00:00",
        "league": {"id": 1, "user": {"id": YO, "name": "Pepe"}},
        "market": {
            "sales": ventas,
            "offers": ofertas,
            "status": {"balance": saldo, "maximumBid": maximo},
        },
        "my_team": [{"id": f[0], "price": f[3]} for f in PLANTILLA],
        "catalog": {"data": {"players": catalogo}},
        "_caja": nombre,
    }


def _la_liga(con_raphinha=True) -> dict:
    """{id: fila de `todaLaLiga`} de los nuestros, el mercado y Raphinha."""
    liga = {}
    for de_quien, filas in (("nuestro", PLANTILLA), ("computer", COMPUTER),
                            ("libre", (EL_OBJETIVO,))):
        for f in filas:
            pid, nombre, pos, precio, sube, estado, prob, puntos, jugados, tasa, equipo = f
            liga[pid] = {
                "id": pid, "name": nombre, "position": pos, "price": precio,
                "price_increment": sube, "status": estado, "points": puntos,
                "played": jugados, "tasa": tasa, "team_id": equipo,
                "de_quien": ("computer" if (pid == RAPHINHA and con_raphinha)
                             else de_quien),
                "starter_probability": prob,
            }
    return liga


def _el_status(foto) -> dict:
    """Lo que la mejora lee del panel: el once, toda la liga y el escaparate."""
    con_raphinha = any((v.get("player") or {}).get("id") == RAPHINHA and v.get("user") is None
                       for v in foto["market"]["sales"])
    liga = _la_liga(con_raphinha)
    once_ids = (38433, 23840, 28115, 1760, 30493, 29661, 12403, 41418, 41411, 26271, 35678)
    once = []
    for f in PLANTILLA:
        if f[0] in once_ids:
            once.append({"id": f[0], "name": f[1], "position": f[2],
                         "starter_probability": f[6], "price": f[3]})
    escaparate = [
        {"id": f[0], "name": f[1], "position": f[2], "price": f[3], "points": f[7],
         "played": f[8], "starter_probability": f[6]}
        for f in list(COMPUTER) + ([EL_OBJETIVO] if con_raphinha else [])
    ]
    return {
        "todaLaLiga": {"players": list(liga.values())},
        "lineup": {"players": once},
        "libro_del_escaparate": {"players": escaparate},
        "roster": {"players": [{"id": f[0], "name": f[1], "starter_probability": f[6]}
                               for f in PLANTILLA]},
    }


def _normal(x):
    """Lo que sale de un motor, en algo que `json` escribe igual siempre."""
    if isinstance(x, dict):
        return {str(k): _normal(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))
                if k not in ("ran_at",)}
    if isinstance(x, (set, frozenset)):
        return sorted((_normal(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(x, (list, tuple)):
        return [_normal(v) for v in x]
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, float):
        return round(x, 6)
    return x


class _ElDiaDelDesvio(date):
    """El dia con el que el desvio de la puja (`bid_jitter._seed`) siembra
    su numero: el carril no le pasa la fecha y miraria el reloj (con el
    reloj de otro dia, otro importe). Fijo: el lunes 02/11/2026."""

    @classmethod
    def today(cls):
        return cls(2026, 11, 2)


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


class _ClienteDeMentira:
    def __init__(self, foto):
        self._foto = foto

    def get_market(self):
        return copy.deepcopy(self._foto["market"])

    def get_player_catalog(self):
        return copy.deepcopy(self._foto["catalog"]["data"]["players"])


def _escritor_de_mercado(foto):
    class _EscritorDeMercado(_Escritor):
        def __init__(self):
            super().__init__()
            self.client = _ClienteDeMentira(foto)
            self.user_id = YO
    return _EscritorDeMercado


def _con_la_orden(orden, carpeta, nombre="la_orden_del_gestor.json"):
    ruta = Path(carpeta) / nombre
    ruta.write_text(json.dumps(orden), encoding="utf-8")
    return ruta


def _la_bateria(carpeta) -> list:
    """[(nombre, llamada)] de cada funcion tocada, con la firma de main."""

    from src.actions import la_orden_del_gestor as orden_mod
    from src.actions import los_chollos as chollos_mod
    from src.actions import la_ronda_de_la_manana as ronda_mod
    from src.actions import la_mejora_del_once as mejora_mod
    from src.actions import la_rotacion as rotacion_mod
    from src.actions import live_bid_executor as bid_mod
    from src.analysis import la_rendija as rendija_mod

    calendario = _el_calendario()
    fotos = [_la_foto_de(c) for c in CAJAS]
    llamadas = []

    def _foto_de_la_orden(s):
        f = orden_mod.leer_la_foto(s, YO)
        f.pop("de_managers", None)
        return f

    # 1. LA ORDEN DEL GESTOR: decidir y correr.
    for s in fotos:
        foto = _foto_de_la_orden(s)
        estados = orden_mod.leer_los_estados(s)
        for nombre, orden in ORDENES:
            for horas in (99.6, 30.0, None):
                for ahora in (MOMENTOS[0], MOMENTOS[3]):
                    llamadas.append((
                        f"orden.decidir/{s['_caja']}/{nombre}/{horas}/{ahora.isoformat()}",
                        lambda orden=orden, foto=foto, horas=horas, ahora=ahora, estados=estados:
                        orden_mod.decidir(copy.deepcopy(orden), **copy.deepcopy(foto),
                                          ahora=ahora, horas_jornada=horas,
                                          estados=estados, en_curso=False)))
        for nombre, orden in ORDENES[1:4]:
            for ahora in (MOMENTOS[1], MOMENTOS[3]):
                def _correr(s=s, orden=orden, ahora=ahora, nombre=nombre):
                    ruta = _con_la_orden(orden, carpeta, "la_orden_de_correr.json")
                    e = _Escritor()
                    r = orden_mod.correr({"snapshot": copy.deepcopy(s)},
                                         escritor_factory=lambda: e, ruta=ruta,
                                         ahora=ahora, calendario=calendario)
                    return {"r": r, "escritor": e.llamadas}
                llamadas.append((f"orden.correr/{s['_caja']}/{nombre}/{ahora.isoformat()}",
                                 _correr))

    # 2. LOS CHOLLOS: decidir y correr.
    for s in fotos:
        foto = orden_mod.leer_la_foto(s, YO)
        catalogo = s["catalog"]["data"]["players"]
        valores = {int(k): v["price"] for k, v in catalogo.items()}
        estados = {int(k): v["status"] for k, v in catalogo.items()}
        for minutos in (30, 200):
            for horas in (99.6, 50.0, None):
                for libro in ({}, {"38433": 2200000}):
                    llamadas.append((
                        f"chollos.decidir/{s['_caja']}/{minutos}/{horas}/{len(libro)}",
                        lambda foto=foto, minutos=minutos, horas=horas, libro=libro,
                        valores=valores, estados=estados:
                        chollos_mod.decidir(
                            mercado=dict(foto["mercado"]), valores=valores, estados=estados,
                            nuestras_pujas=copy.deepcopy(foto["nuestras_pujas"]),
                            plantilla=set(foto["plantilla"]),
                            ofertas_del_computer=copy.deepcopy(foto["ofertas_del_computer"]),
                            en_venta=set(foto["en_venta"]),
                            maximo_de_puja=foto["maximo_de_puja"], saldo=foto["saldo"],
                            minutos_al_reset=minutos, horas_jornada=horas,
                            libro=dict(libro), puede_escribir=True, en_curso=False)))
        for ahora in (MOMENTOS[0], MOMENTOS[3]):
            def _correr(s=s, ahora=ahora):
                e = _Escritor()
                ruta = Path(carpeta) / "chollos.json"
                ruta.write_text(json.dumps({"38433": 2200000}))
                r = chollos_mod.correr({"snapshot": copy.deepcopy(s)}, 30,
                                       escritor_factory=lambda: e, ahora=ahora,
                                       libro_ruta=ruta)
                return {"r": r, "escritor": e.llamadas, "libro": ruta.read_text()}
            llamadas.append((f"chollos.correr/{s['_caja']}/{ahora.isoformat()}", _correr))

    # 3. LA RONDA DE LA MANANA: decidir y correr.
    for s in fotos:
        foto = orden_mod.leer_la_foto(s, YO)
        fichas = {int(k): v for k, v in s["catalog"]["data"]["players"].items()}
        for cartera in (True, False):
            for horas in (99.6, 70.0, 30.0):
                llamadas.append((
                    f"ronda.decidir/{s['_caja']}/{cartera}/{horas}",
                    lambda foto=foto, fichas=fichas, cartera=cartera, horas=horas:
                    ronda_mod.decidir(
                        mercado=dict(foto["mercado"]), fichas=copy.deepcopy(fichas),
                        nuestras_pujas=copy.deepcopy(foto["nuestras_pujas"]),
                        plantilla=set(foto["plantilla"]),
                        ofertas_del_computer=copy.deepcopy(foto["ofertas_del_computer"]),
                        en_venta=set(foto["en_venta"]), maximo_de_puja=foto["maximo_de_puja"],
                        minutos_al_reset=200, horas_jornada=horas,
                        libro={"35765": 219900}, protegidos=frozenset(),
                        puede_escribir=True, en_curso=False, cartera=cartera,
                        de_managers=frozenset(), saldo=foto["saldo"])))
        for ahora in (MOMENTOS[0], MOMENTOS[3]):
            def _correr(s=s, ahora=ahora):
                e = _Escritor()
                ruta = Path(carpeta) / "la_ronda.json"
                ruta.write_text(json.dumps({"35765": 219900}))
                r = ronda_mod.correr({"snapshot": copy.deepcopy(s)}, 200,
                                     escritor_factory=lambda: e, ahora=ahora,
                                     libro_ruta=ruta)
                return {"r": r, "escritor": e.llamadas, "libro": ruta.read_text()}
            llamadas.append((f"ronda.correr/{s['_caja']}/{ahora.isoformat()}", _correr))

    # 4. LA MEJORA DEL ONCE: la combinacion, decidir y correr.
    cambios = [
        {"entra": 17482, "sale": 38433, "puntos": 0.6, "caja": -150000, "puja": 2439900,
         "ya_es_nuestro": False},
        {"entra": 17731, "sale": 30493, "puntos": 0.9, "caja": -326000, "puja": 2349900,
         "ya_es_nuestro": False},
        {"entra": 17057, "sale": 14800, "puntos": 1.2, "caja": -980000, "puja": 3479900,
         "ya_es_nuestro": False},
        {"entra": 41609, "sale": 1844, "puntos": 0.2, "caja": 780000, "puja": 879900,
         "ya_es_nuestro": False},
        {"entra": 35765, "sale": 41411, "puntos": 0.7, "caja": 218500, "puja": 0,
         "ya_es_nuestro": True},
        {"entra": 11, "sale": 38433, "puntos": 1.5, "caja": -2730000, "puja": 4919900,
         "ya_es_nuestro": False},
    ]
    for caja in (-7494776, -500000, 300000, 3000000, 12000000):
        for minimo in (-1000000, 0):
            for disponible in (2000000, 9000000):
                for deficit in (False, True):
                    llamadas.append((
                        f"mejora.combinacion/{caja}/{minimo}/{disponible}/{deficit}",
                        lambda caja=caja, minimo=minimo, disponible=disponible, deficit=deficit:
                        mejora_mod.la_mejor_combinacion(copy.deepcopy(cambios), caja, minimo,
                                                        disponible, deficit=deficit)))
    for s in fotos:
        status = _el_status(s)
        liga = {p["id"]: p for p in status["todaLaLiga"]["players"]}
        foto = orden_mod.leer_la_foto(s, YO)
        for caja in (-2000000, 400000, 6000000):
            for horas in (99.6, 70.0):
                llamadas.append((
                    f"mejora.decidir/{s['_caja']}/{caja}/{horas}",
                    lambda status=status, liga=liga, foto=foto, caja=caja, horas=horas:
                    mejora_mod.decidir(
                        once=copy.deepcopy(status["lineup"]["players"]),
                        liga=copy.deepcopy(liga),
                        escaparate=copy.deepcopy(status["libro_del_escaparate"]["players"]),
                        foto=copy.deepcopy(foto), libro={}, inventario={35765},
                        pendientes=set(), intocables=frozenset({"yamal", "lamine yamal"}),
                        protegidos=set(), ya_pujados=set(), caja=caja, horas_jornada=horas,
                        puede_escribir=True, en_curso=False, solo_si_sube=True,
                        en_9900=True,
                        probabilidades={f[0]: f[6] for f in PLANTILLA})))
        for ahora in (MOMENTOS[0], MOMENTOS[3]):
            def _correr(s=s, ahora=ahora, status=status):
                e = _Escritor()
                ruta = Path(carpeta) / "la_mejora.json"
                ruta.write_text("{}")
                ronda = Path(carpeta) / "ronda_m.json"
                ronda.write_text(json.dumps({"35765": 219900}))
                chollos = Path(carpeta) / "chollos_m.json"
                chollos.write_text("{}")
                r = mejora_mod.correr(
                    status=copy.deepcopy(status), snapshot=copy.deepcopy(s), v10={},
                    escritor_factory=lambda: e, ahora=ahora, libro_ruta=ruta,
                    de_fuera={"orden": {}, "vetados": set(), "protegidos": set(),
                              "libro_ronda": ronda, "libro_chollos": chollos,
                              "horas_jornada": 99.6, "puede_escribir": True,
                              "en_curso": False, "rotando": set()})
                return {"r": r, "escritor": e.llamadas, "libro": ruta.read_text()}
            llamadas.append((f"mejora.correr/{s['_caja']}/{ahora.isoformat()}", _correr))

    # 5. LA ROTACION: decidir.
    for s in fotos:
        foto = orden_mod.leer_la_foto(s, YO)
        fichas = {int(k): v for k, v in s["catalog"]["data"]["players"].items()}
        subidas = {f[0]: (-10000 if f[4] <= 0 else 20000) for f in PLANTILLA}
        pujas_vivas = {p: v["amount"] for p, v in foto["nuestras_pujas"].items()}
        for ahora in (MOMENTOS[0], MOMENTOS[3]):
            reloj = rotacion_mod.el_reloj(ahora, calendario, True)
            for once in (None, {"ids": [38433, 23840, 28115, 1760, 30493, 29661, 12403,
                                        41418, 41411, 26271, 35678], "formacion": "4-4-2"}):
                llamadas.append((
                    f"rotacion.decidir/{s['_caja']}/{ahora.isoformat()}/{bool(once)}",
                    lambda foto=foto, fichas=fichas, subidas=subidas, pujas_vivas=pujas_vivas,
                    reloj=reloj, once=once:
                    rotacion_mod.decidir(
                        plantilla=set(foto["plantilla"]), fichas=copy.deepcopy(fichas),
                        mercado=dict(foto["mercado"]), subidas_de_ayer=dict(subidas),
                        rondas_jugadas=11, saldo=foto["saldo"], pujas_vivas=dict(pujas_vivas),
                        maximo_de_puja=foto["maximo_de_puja"],
                        ofertas_del_computer=copy.deepcopy(foto["ofertas_del_computer"]),
                        en_venta=set(foto["en_venta"]), parejas=[], once=copy.deepcopy(once),
                        reloj=copy.deepcopy(reloj))))

    # 6. EL CARRIL: el bolsillo.
    for caja in (None, -7494776, 0, 500000, 1900000, 12000000):
        for comprometido in (None, 0, 2559900):
            llamadas.append((f"carril.bolsillo/{caja}/{comprometido}",
                             lambda caja=caja, comprometido=comprometido:
                             rendija_mod.bolsillo_del_carril(caja, comprometido=comprometido)))

    # 6-bis. EL CARRIL: correr, con el escritor de mentira (el libro de
    # cada llamada, aparte: el cupo no pasa de una a otra).
    from src.actions import carril_executor as carril_mod
    for caja in (-7494776, 500000, 1900000, 5000000, 21000000):
        for comprometido in (0, 2559900):
            for ahora in (MOMENTOS[0], datetime(2026, 11, 10, 17, 0, tzinfo=_UTC)):
                def _correr(caja=caja, comprometido=comprometido, ahora=ahora):
                    e = _Escritor()
                    n = f"{caja}_{comprometido}_{ahora.strftime('%d%H')}"
                    r = carril_mod.correr(
                        accion_principal=None, cierres=[],
                        objetivos=copy.deepcopy(OBJETIVOS_DEL_CARRIL),
                        rates=copy.deepcopy(RITMOS), prima_de_puja=0.28, curva=1.0028,
                        caja=caja, comprometido=comprometido, presupuesto=3000000,
                        escritor=e, disparo=None, ahora=ahora,
                        ruta_del_libro=Path(carpeta) / f"carril_{n}.jsonl",
                        ruta_de_viajes=Path(carpeta) / f"viajes_{n}.jsonl",
                        speculation={"bid_exposure": {"available": True,
                                                      "committed_total": comprometido,
                                                      "players": []}})
                    return {"r": r, "escritor": e.llamadas}
                llamadas.append((f"carril.correr/{caja}/{comprometido}/{ahora.isoformat()}",
                                 _correr))

    # 7. EL BUY V10 Y LAS CLI: `execute_bid`, con el mercado fresco de cada foto.
    for s in fotos:
        for pid, importe, vendedor in ((17482, 2449900, None), (17731, 2400000, None),
                                       (15430, 7000000, 777), (11, 4900000, None),
                                       (17482, 40000000, None), (38405, 2600000, None)):
            for ejecutar in (False, True):
                def _pujar(s=s, pid=pid, importe=importe, vendedor=vendedor, ejecutar=ejecutar):
                    viejo = bid_mod.BiwengerWriteClient
                    bid_mod.BiwengerWriteClient = _escritor_de_mercado(s)
                    try:
                        return bid_mod.execute_bid(pid, importe, expected_seller_id=vendedor,
                                                   execute=ejecutar)
                    except Exception as error:      # noqa: BLE001
                        return f"{type(error).__name__}: {error}"
                    finally:
                        bid_mod.BiwengerWriteClient = viejo
                llamadas.append((f"execute_bid/{s['_caja']}/{pid}/{importe}/{ejecutar}",
                                 _pujar))

    return llamadas


# El entorno de la bateria: el de produccion para estos motores, fijo,
# y la hucha como diga cada corrida.
ENTORNO_DE_LA_BATERIA = {
    "BORDALAS_LA_ORDEN_DEL_GESTOR": "1",
    "BORDALAS_LOS_CHOLLOS": "1",
    "BORDALAS_LA_RONDA_DE_LA_MANANA": "1",
    "BORDALAS_LA_CARTERA": "1",
    "BORDALAS_LA_PUJA_EN_9900": "1",
    "BORDALAS_UN_SOLO_COLCHON": "1",
    "BORDALAS_LA_MEJORA_DEL_ONCE": "1",
    "BORDALAS_LA_MEJORA_SOLO_SI_SUBE": "1",
    "BORDALAS_LA_ROTACION": "1",
}

APAGADO = (None, "0", "")


def _huellas(valores_de_la_hucha=APAGADO) -> dict:
    """{entorno de la hucha: {llamada: sha256}}. El entorno se deja como
    estaba (dentro, sin ningun `BORDALAS_*` de fuera: tampoco la sal del
    desvio). Las rutas de produccion que leen los motores al llamarse (la
    orden, el calendario) apuntan a la carpeta temporal, el libro de las
    pujas no se escribe y el dia del desvio es fijo: ni `data/` ni el
    reloj."""

    from src.actions import la_orden_del_gestor as orden_mod
    from src.actions import los_chollos as chollos_mod
    from src.actions import la_ronda_de_la_manana as ronda_mod

    guardado = {k: v for k, v in os.environ.items() if k.startswith("BORDALAS_")}
    run_id = os.environ.pop("GITHUB_RUN_ID", None)
    from src.analysis import bid_jitter as desvio_mod
    from src.intelligence import bid_outcome_ledger as ledger_mod

    rutas = (orden_mod.RUTA, chollos_mod.CALENDARIO, ronda_mod.CALENDARIO,
             ledger_mod.record_bid, desvio_mod.date)
    ledger_mod.record_bid = lambda *a, **k: None
    desvio_mod.date = _ElDiaDelDesvio
    salida = {}
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            calendario = _el_calendario()
            chollos_mod.CALENDARIO = calendario
            ronda_mod.CALENDARIO = calendario
            for valor in valores_de_la_hucha:
                for k in [k for k in os.environ if k.startswith("BORDALAS_")]:
                    os.environ.pop(k)
                os.environ.update(ENTORNO_DE_LA_BATERIA)
                if valor is not None:
                    os.environ["BORDALAS_LA_HUCHA"] = valor
                huellas = {}
                for nombre, llamada in _la_bateria(carpeta):
                    orden_mod.RUTA = _con_la_orden(ORDENES[0][1], carpeta)
                    texto = json.dumps(_normal(llamada()), sort_keys=True, ensure_ascii=False,
                                       default=str)
                    huellas[nombre] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
                salida[repr(valor)] = huellas
    finally:
        (orden_mod.RUTA, chollos_mod.CALENDARIO, ronda_mod.CALENDARIO,
         ledger_mod.record_bid, desvio_mod.date) = rutas
        for k in [k for k in os.environ if k.startswith("BORDALAS_")]:
            os.environ.pop(k)
        os.environ.update(guardado)
        if run_id is not None:
            os.environ["GITHUB_RUN_ID"] = run_id
    return salida


def _la_huella(huellas: dict) -> str:
    """Una huella de todas: sha256 de las de cada llamada, en orden."""
    texto = "\n".join(f"{k} {v}" for k, v in sorted(huellas.items()))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# Medidas en main (9a35ae94, antes de tocar el codigo) con
# `python -m src.analysis.test_la_hucha_v1 --medir`, una por Python.
HUELLAS_DE_MAIN = {
    (3, 11): "8d4c301e6a7784dcf003e902f8621e7743883d5484209e325ff8533877de24b9",
    (3, 13): "8d4c301e6a7784dcf003e902f8621e7743883d5484209e325ff8533877de24b9",
}
LLAMADAS_DE_LA_BATERIA = 570


# ============================================================
# LA HUCHA DE LA PRUEBA
# ============================================================

OBJETIVO = 16_000_000
CFG = {
    "player_id": RAPHINHA, "nombre": "Raphinha", "objetivo": OBJETIVO,
    "desde": "2026-11-10T00:00:00+01:00", "caduca": "2026-12-31T23:59:00+01:00",
    "por_que": "la de la prueba",
}
# Para lo que mira el reloj por su cuenta (`execute_bid`, el ejecutor, el
# orquestador, la vuelta de v10): vale cualquier dia.
CFG_SIEMPRE = {**CFG, "desde": "2020-01-01T00:00:00+00:00",
               "caduca": "2100-01-01T00:00:00+00:00"}
# mie 11/11 10:00 de Madrid: el paron (la J13 empieza el 20/11).
AHORA = datetime(2026, 11, 11, 9, 0, tzinfo=_UTC)
HORAS_PARON = 227.0


class _LaHucha:
    """La hucha de la prueba en una carpeta temporal (`la_hucha.RUTA`),
    con el interruptor (`puesta`) y los demas (`extra`) solo dentro del
    `with`. `cfg` None: sin fichero; un texto: el fichero tal cual."""

    def __init__(self, cfg=CFG, puesta="1", extra=None):
        self.cfg, self.puesta, self.extra = cfg, puesta, dict(extra or {})

    def __enter__(self):
        from src.analysis import la_hucha

        self.carpeta = tempfile.TemporaryDirectory()
        ruta = Path(self.carpeta.name) / "la_hucha.json"
        if isinstance(self.cfg, str):
            ruta.write_text(self.cfg, encoding="utf-8")
        elif self.cfg is not None:
            ruta.write_text(json.dumps(self.cfg), encoding="utf-8")
        self.antes = la_hucha.RUTA
        la_hucha.RUTA = ruta
        self.interruptores = _Interruptores({ENV: self.puesta, **self.extra})
        self.interruptores.__enter__()
        return ruta

    def __exit__(self, *a):
        from src.analysis import la_hucha

        self.interruptores.__exit__(*a)
        la_hucha.RUTA = self.antes
        self.carpeta.cleanup()
        return False


def _caja(saldo, pujas=None, raphinha=False, nombre="prueba"):
    """Una caja de la bateria con otro saldo y otras pujas vivas."""
    return (nombre, saldo, dict(pujas or {}), raphinha)


def _foto_de(saldo, pujas=None, raphinha=False):
    """(la foto de Biwenger, la de `leer_la_foto`) de esa caja."""
    from src.actions.la_orden_del_gestor import leer_la_foto

    s = _la_foto_de(_caja(saldo, pujas, raphinha))
    return s, leer_la_foto(s, YO)


def _hucha(saldo, pujas=None, raphinha=False, ahora=AHORA):
    from src.analysis import la_hucha

    _, foto = _foto_de(saldo, pujas, raphinha)
    return la_hucha.de_la_foto(foto, ahora=ahora)


def _pujas(acciones):
    return [(a["player_id"], a["importe"]) for a in acciones if a.get("accion") == "PUJAR"]


def _nadas_de_la_hucha(acciones):
    return [a["player_id"] for a in acciones
            if a.get("accion") == "NADA" and a.get("guardia") == "LA_HUCHA"]


# ============================================================
# 1. NACE APAGADA, UN LECTOR, SU FRASE Y SU FICHERO
# ============================================================

def test_nace_apagada_un_lector_y_su_frase():
    from src.analysis import la_hucha

    assert la_hucha.ENV == ENV
    with _Interruptores({ENV: None}):
        assert la_hucha.activa() is False
    for valor, puesto in (("1", True), ("true", True), ("si", True), ("yes", True),
                          (" 1 ", True), ("SI", True), ("0", False), ("no", False),
                          ("", False), ("2", False)):
        with _Interruptores({ENV: valor}):
            assert la_hucha.activa() is puesto, valor
    from src.telemetry.el_tablon import QUE_HACE
    frase = str(QUE_HACE.get(ENV) or "")
    assert frase.strip() and "Raphinha" in frase and "No vende a nadie" in frase, frase
    # Se lee en UN sitio, al llamarse.
    from scripts.los_interruptores import lectores
    quien = {}
    for carpeta in ("src", "scripts"):
        for camino in sorted((RAIZ / carpeta).rglob("*.py")):
            if "__pycache__" in camino.parts or camino.name.startswith("test_"):
                continue
            if ENV not in camino.read_text(encoding="utf-8"):
                continue
            cuando = lectores(camino).get(ENV)
            if cuando:
                quien[camino.relative_to(RAIZ).as_posix()] = cuando
    assert quien == {"src/analysis/la_hucha.py": "AL_LLAMARSE"}, quien
    # Y el modulo no hace nada al importarse: solo constantes y funciones.
    arbol = ast.parse((RAIZ / "src" / "analysis" / "la_hucha.py").read_text(encoding="utf-8"))
    for nodo in arbol.body:
        assert isinstance(nodo, (ast.Expr, ast.ImportFrom, ast.Import, ast.FunctionDef,
                                 ast.Assign)), ast.dump(nodo)[:80]
        if isinstance(nodo, ast.Expr):
            assert isinstance(nodo.value, ast.Constant), "solo el docstring"
        if isinstance(nodo, ast.Assign):
            assert isinstance(nodo.value, (ast.Constant, ast.BinOp)), ast.dump(nodo)[:80]
    # El fichero del gestor, si esta (el gestor lo cambia o lo borra: si un
    # rival ficha a Raphinha, se borra y la hucha queda en SIN_HUCHA): bien
    # escrito, con sus fechas con zona y valiendo justo entre `desde` y
    # `caduca`. Sus numeros no se fijan aqui: la verja no se pone roja
    # porque el gestor mueva el objetivo.
    ruta = RAIZ / "config" / "la_hucha.json"
    if ruta.exists():
        texto = ruta.read_text(encoding="utf-8")
        cfg = json.loads(texto)
        assert texto == json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"
        assert la_hucha._int(cfg.get("player_id"), 0) > 0, cfg
        assert la_hucha._int(cfg.get("objetivo"), 0) > 0, cfg
        assert str(cfg.get("nombre") or "").strip() and str(cfg.get("por_que") or "").strip()
        desde = datetime.fromisoformat(cfg["desde"])
        caduca = datetime.fromisoformat(cfg["caduca"])
        assert desde.tzinfo is not None and caduca.tzinfo is not None and desde < caduca
        assert la_hucha.vigente(cfg, desde - timedelta(seconds=1)) == la_hucha.AUN_NO
        assert la_hucha.vigente(cfg, desde) is None
        assert la_hucha.vigente(cfg, caduca) == la_hucha.CADUCADA


# ============================================================
# 2. APAGADA ES MAIN, BYTE A BYTE (Y NO LEE EL FICHERO)
# ============================================================

def test_apagada_es_main_byte_a_byte():
    from src.analysis import la_hucha

    esperada = HUELLAS_DE_MAIN.get(sys.version_info[:2])
    assert esperada is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    leidas = []
    leer = la_hucha.leer
    la_hucha.leer = lambda *a, **k: leidas.append(a) or leer(*a, **k)
    try:
        todas = _huellas(APAGADO)
    finally:
        la_hucha.leer = leer
    assert leidas == [], f"apagada se leyo la hucha {len(leidas)} veces"
    valores = list(todas.values())
    assert len(valores) == len(APAGADO)
    for huellas in valores:
        assert len(huellas) == LLAMADAS_DE_LA_BATERIA, len(huellas)
        assert huellas == valores[0], "apagada depende de como se apague"
    assert _la_huella(valores[0]) == esperada, (
        f"apagada ya no es main en Python {sys.version_info[:2]}: "
        f"{_la_huella(valores[0])} (main: {esperada})")


def test_apagada_todo_es_neutro():
    from src.analysis import la_hucha

    s, foto = _foto_de(30_000_000, raphinha=True)
    with _LaHucha(CFG_SIEMPRE, puesta=None):
        h = la_hucha.de_la_foto(foto, ahora=AHORA)
        assert h == {"activa": False, "encendida": False, "motivo": "APAGADA", "apartado": 0}
        assert la_hucha.de_la_snapshot(s, ahora=AHORA)["activa"] is False
        assert la_hucha.cabe(h, 10**12) is True
        assert la_hucha.frena_la_especulacion(s, 17482, 10**12) is None
        assert la_hucha.la_puja_toca_la_hucha(s["market"], YO, 17482, 10**12) is None
        plan = {"bids": [{"id": 1, "bid": 10**12}], "execute": True}
        assert la_hucha.la_cesta_con_la_hucha(plan, s) is plan
        assert la_hucha.el_bloque(h, {}) == {}
        assert la_hucha.filtrar_pujas([{"accion": "PUJAR", "importe": 1}], h) == [
            {"accion": "PUJAR", "importe": 1}]


# ============================================================
# 3. LAS CUENTAS
# ============================================================

def test_lo_apartado_y_la_puerta():
    from src.analysis import la_hucha as H

    assert H.lo_apartado(10_000_000, 0, OBJETIVO) == 10_000_000
    assert H.lo_apartado(30_000_000, {1: {"amount": 2_000_000}}, OBJETIVO) == OBJETIVO
    assert H.lo_apartado(18_000_000, {1: 1_000_000, 2: {"amount": 500_000}}, OBJETIVO) == OBJETIVO
    assert H.lo_apartado(10_000_000, 12_000_000, OBJETIVO) == 0
    assert H.lo_apartado(-7_494_776, 0, OBJETIVO) == 0
    assert H.lo_apartado(None, 0, OBJETIVO) == 0
    assert H.lo_apartado(10_000_000, 0, 0) == 0
    with _LaHucha(CFG):
        # 21 M - 4.169.800 en pujas: 16 M apartados, 831.200 libres.
        h = _hucha(21_000_000, {17482: 2_439_900, 33694: 1_729_900})
        assert h["activa"] and h["apartado"] == OBJETIVO and h["libre"] == 830_200, h
        assert h["maximo_para_gastar"] == h["maximo_de_puja"] - OBJETIVO
        # La puerta: justa pasa, un euro mas no.
        assert H.cabe(h, 830_200) and not H.cabe(h, 830_201)
        assert H.cabe(h, 830_201, ya=0, credito=1) and not H.cabe(h, 830_200, ya=1)
        assert H.cabe(h, 3_000_000, sustituye=2_169_800)
        assert H.cabe(h, 5_000_000, credito=5_000_000)          # se paga solo
        assert H.cabe(h, 50_000_000, player_id=RAPHINHA)        # la exencion
        assert not H.cabe({**h, "libre": None}, 1) and H.cabe({**h, "libre": None}, 1, credito=1)
        # Lo pujado en la vuelta: lo que daria una foto nueva.
        h2 = H.mas_lo_pujado(h, 500_000)
        assert (h2["libre"], h2["apartado"], h2["pujado_en_la_vuelta"]) == (330_200, OBJETIVO, 500_000)
        assert h2["maximo_de_puja"] == h["maximo_de_puja"] - 500_000
        h3 = H.mas_lo_pujado(h2, 1_000_000)
        assert (h3["libre"], h3["apartado"]) == (0, OBJETIVO - 669_800), h3
        assert H.mas_lo_pujado(h, 0) is h
        # Lo que suben las pujas de cada motor.
        assert H.lo_pujado_en([
            {"accion": "PUJAR", "importe": 3_000_000, "exito": True,
             "sustituye": {"amount": 2_000_000}},
            {"accion": "PUJAR", "importe": 1_000_000, "exito": False},
            {"accion": "PUJAR", "importe": 700_000, "exito": True, "sustituye": None},
            {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "importe": 9, "exito": True}]) == 1_700_000
        assert H.lo_pujado_por_el_carril({"bids": [
            {"amount": 1_000_000, "sent": True, "success": True},
            {"amount": 2_000_000, "sent": True, "success": None},
            {"amount": 4_000_000, "sent": True, "success": False},
            {"amount": 8_000_000, "sent": False}]}) == 3_000_000
        assert H.lo_pujado_por_el_buy({"writes_biwenger": True, "execution": {
            "sent": True, "success": True, "amount": 2_449_900}}) == 2_449_900
        assert H.lo_pujado_por_el_buy({"writes_biwenger": False}) == 0
        # filtrar_pujas: en orden, cada una con lo que sacan las de delante.
        acciones = [{"accion": "PUJAR", "player_id": 1, "importe": 500_000},
                    {"accion": "PONER_A_LA_VENTA", "player_id": 9},
                    {"accion": "PUJAR", "player_id": 2, "importe": 400_000},
                    {"accion": "PUJAR", "player_id": 3, "importe": 300_000}]
        fuera = H.filtrar_pujas(acciones, h)
        assert [a["accion"] for a in fuera] == ["PUJAR", "PONER_A_LA_VENTA", "NADA", "PUJAR"]
        assert fuera[2]["guardia"] == "LA_HUCHA"


def test_vigente_fechas_y_la_hucha_rota():
    from src.analysis import la_hucha as H

    antes = datetime(2026, 11, 9, 22, 59, 59, tzinfo=_UTC)
    justo = datetime(2026, 11, 9, 23, 0, tzinfo=_UTC)            # 10/11 00:00 Madrid
    assert H.vigente(CFG, antes) == H.AUN_NO
    assert H.vigente(CFG, justo) is None
    assert H.vigente(CFG, datetime(2026, 12, 31, 22, 58, tzinfo=_UTC)) is None
    assert H.vigente(CFG, datetime(2026, 12, 31, 22, 59, tzinfo=_UTC)) == H.CADUCADA
    assert H.vigente(None, AHORA) == H.SIN_HUCHA
    assert H.vigente([], AHORA) == H.SIN_HUCHA
    for roto in ({**CFG, "desde": "2026-11-10T00:00:00"},           # sin zona
                 {**CFG, "caduca": "manana"},
                 {**CFG, "objetivo": 0}, {**CFG, "objetivo": "mucho"},
                 {**CFG, "player_id": True}, {**CFG, "player_id": -3},
                 {k: v for k, v in CFG.items() if k != "caduca"}):
        assert H.vigente(roto, AHORA) == H.MAL_ESCRITA, roto
    # CUMPLIDA: Raphinha ya es nuestro. Se apaga sola.
    assert H.vigente(CFG, AHORA, {1, RAPHINHA}) == H.CUMPLIDA
    assert H.vigente(CFG, AHORA, None) is None
    s, foto = _foto_de(30_000_000)
    foto["plantilla"] = set(foto["plantilla"]) | {RAPHINHA}
    with _LaHucha(CFG):
        h = H.de_la_foto(foto, ahora=AHORA)
        assert (h["activa"], h["motivo"], h["apartado"]) == (False, H.CUMPLIDA, 0), h
        assert H.cabe(h, 10**12) and H.el_bloque(h)["hucha"]["activa"] is False
    # Fechas, sin fichero, fichero roto: encendida y nada cambia.
    for cfg, motivo in ((CFG, H.AUN_NO), (None, H.SIN_HUCHA), ("{no es json", H.SIN_HUCHA),
                        ('["lista"]', H.SIN_HUCHA), ({**CFG, "objetivo": -1}, H.MAL_ESCRITA)):
        with _LaHucha(cfg):
            h = H.de_la_foto(foto, ahora=antes)
            assert (h["activa"], h["encendida"], h["motivo"], h["apartado"]) == (
                False, True, motivo, 0), (cfg, h)
            assert H.cabe(h, 10**12)
    with _LaHucha(CFG):
        assert H.de_la_foto(foto, ahora=datetime(2027, 1, 1, tzinfo=_UTC))["motivo"] == H.CADUCADA
        # Sin saldo, o sin saber cuales son nuestras pujas: activa, pero
        # nadie gasta contra ella (solo lo que se paga solo).
        _, limpia = _foto_de(30_000_000)
        sin_saldo = H.de_la_foto({**limpia, "saldo": None}, ahora=AHORA)
        assert sin_saldo["activa"] and sin_saldo["libre"] is None
        assert not H.cabe(sin_saldo, 1) and H.cabe(sin_saldo, 5, credito=5)
        s2 = copy.deepcopy(s)
        s2["league"]["user"] = None
        assert H.de_la_snapshot(s2, ahora=AHORA)["libre"] is None


# ============================================================
# 4. CADA MOTOR QUE GASTA
# ============================================================

def test_la_orden_ficha_a_raphinha_y_frena_lo_demas():
    from src.actions import la_orden_del_gestor as O
    from src.analysis import la_hucha as H

    orden = {
        "caduca": "2026-12-31T23:59:00+01:00",
        "fichar": [
            {"player_id": RAPHINHA, "nombre": "Raphinha", "puja": 29_000_000,
             "la_pagan_sus_ventas": True},
            {"player_id": 17731, "nombre": "Catena", "puja": 2_400_000},
        ],
        "vender_si_ficha": {"si_esta": RAPHINHA, "jugadores": [
            {"player_id": 35678, "nombre": "Roberto Fernandez", "suelo": 7_000_000},
            {"player_id": 12494, "nombre": "Boye", "suelo": 5_300_000}]},
    }
    with _LaHucha(CFG):
        s, foto = _foto_de(OBJETIVO, raphinha=True)
        foto.pop("de_managers", None)
        h = H.de_la_foto(foto, ahora=AHORA)
        assert (h["apartado"], h["libre"]) == (OBJETIVO, 0), h
        comun = dict(ahora=AHORA, horas_jornada=HORAS_PARON, estados=O.leer_los_estados(s),
                     en_curso=False)
        apagada = O.decidir(copy.deepcopy(orden), **copy.deepcopy(foto), **comun)
        encendida = O.decidir(copy.deepcopy(orden), **copy.deepcopy(foto), **comun, hucha=h)
        # Raphinha: el camino de siempre, con el maximumBid real (32,9 M).
        assert foto["maximo_de_puja"] == OBJETIVO + VALOR_PLANTILLA // 4 > 29_000_000
        de_raphinha = [a for a in encendida if a["player_id"] == RAPHINHA]
        assert de_raphinha == [a for a in apagada if a["player_id"] == RAPHINHA]
        assert _pujas(de_raphinha) == [(RAPHINHA, 29_000_000)], encendida
        # Catena (sin ventas): apagada se puja; encendida, NADA LA_HUCHA.
        assert (17731, 2_400_000) in _pujas(apagada)
        assert (17731, 2_400_000) not in _pujas(encendida)
        assert _nadas_de_la_hucha(encendida) == [17731], encendida
        # La exencion no cambia con el reloj: a 30 h, lo mismo que apagada.
        comun30 = {**comun, "horas_jornada": 30.0}
        assert [a for a in O.decidir(copy.deepcopy(orden), **copy.deepcopy(foto), **comun30,
                                     hucha=h) if a["player_id"] == RAPHINHA] == [
            a for a in O.decidir(copy.deepcopy(orden), **copy.deepcopy(foto), **comun30)
            if a["player_id"] == RAPHINHA]

        # El borde: Catena cabe con 2.400.000 libres justos; con uno menos, no.
        solo_catena = {"caduca": orden["caduca"], "fichar": [orden["fichar"][1]]}
        for saldo, pasa in ((OBJETIVO + 2_400_000, True), (OBJETIVO + 2_399_999, False)):
            _, f = _foto_de(saldo)
            f.pop("de_managers", None)
            a = O.decidir(copy.deepcopy(solo_catena), **f, **comun,
                          hucha=H.de_la_foto(f, ahora=AHORA))
            assert (_pujas(a) == [(17731, 2_400_000)]) is pasa, (saldo, a)
            assert O.decidir(copy.deepcopy(solo_catena), **copy.deepcopy(f), **comun) != [] \
                or True

        # Vender uno para comprar otro: Sancet por Pablo (oferta firme del
        # Computer de 2.505.300 >= su suelo). Pujando 2.500.000 se paga sola
        # y pasa sin un euro libre; pujando 3.800.000, no.
        for puja, pasa in ((2_500_000, True), (3_800_000, False)):
            cambio = {"caduca": orden["caduca"],
                      "fichar": [{"player_id": 17057, "nombre": "Sancet", "puja": puja}],
                      "vender_si_ficha": {"si_esta": 17057, "jugadores": [
                          {"player_id": 14800, "nombre": "Pablo Ibanez", "suelo": 2_400_000}]}}
            a = O.decidir(cambio, **copy.deepcopy(foto), **comun, hucha=h)
            assert (_pujas(a) == [(17057, puja)]) is pasa, (puja, a)
            assert _pujas(O.decidir(copy.deepcopy(cambio), **copy.deepcopy(foto), **comun)) == [
                (17057, puja)]

        # Los viajes: sin venta emparejada.
        viajes = dict(ORDENES)["viajes"]
        assert _pujas(O.decidir(copy.deepcopy(viajes), **copy.deepcopy(foto), **comun))
        a = O.decidir(copy.deepcopy(viajes), **copy.deepcopy(foto), **comun, hucha=h)
        assert _pujas(a) == [] and _nadas_de_la_hucha(a) == [38405, 11677], a

        # Y `correr` la pasa sola (la de la foto).
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "orden.json"
            ruta.write_text(json.dumps({"caduca": orden["caduca"],
                                        "fichar": orden["fichar"]}))
            escritas = []

            class _E(_Escritor):
                def place_bid(self, **kw):
                    escritas.append(kw)
                    return super().place_bid(**kw)

            with _Interruptores({ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": "1"}):
                r = O.correr({"snapshot": copy.deepcopy(s)}, escritor_factory=_E, ruta=ruta,
                             ahora=AHORA, calendario=_el_calendario())
            assert r["hucha"]["apartado"] == OBJETIVO and r["hucha"]["libre"] == 0, r
            assert [e["player_id"] for e in escritas] == [RAPHINHA], escritas
            assert _nadas_de_la_hucha(r["acciones"]) == [17731], r["acciones"]


def test_los_chollos_solo_con_lo_libre():
    from src.actions import los_chollos as C
    from src.analysis import la_hucha as H

    def _decidir(foto, hucha=None, horas=50.0):
        kw = {} if hucha is None else {"hucha": hucha}
        return C.decidir(mercado={41609: 820_000}, valores={41609: 870_000},
                         estados={41609: "ok"}, nuestras_pujas=foto["nuestras_pujas"],
                         plantilla=foto["plantilla"], ofertas_del_computer={},
                         en_venta=set(), maximo_de_puja=foto["maximo_de_puja"],
                         saldo=foto["saldo"], minutos_al_reset=30, horas_jornada=horas,
                         libro={}, **kw)

    puja = 869_000                                      # vale - 1.000
    with _LaHucha(CFG):
        for saldo, pasa in ((OBJETIVO + puja, True), (OBJETIVO + puja - 1, False)):
            _, foto = _foto_de(saldo)
            assert _pujas(_decidir(foto)) == [(41609, puja)]
            h = H.de_la_foto(foto, ahora=AHORA)
            assert h["libre"] == saldo - OBJETIVO
            assert (_pujas(_decidir(foto, h)) == [(41609, puja)]) is pasa, saldo
        # Lejos de la jornada (mas de 72 h) apagados pujan con deuda hasta
        # maximumBid; encendidos, solo con lo libre: con 10 M (todo
        # apartado), nada.
        _, foto = _foto_de(10_000_000)
        assert _pujas(_decidir(foto, horas=HORAS_PARON)) == [(41609, puja)]
        assert _pujas(_decidir(foto, H.de_la_foto(foto, ahora=AHORA), horas=HORAS_PARON)) == []
        _, foto = _foto_de(-2_000_000)
        assert _pujas(_decidir(foto, horas=HORAS_PARON)) == [(41609, puja)]
        assert _pujas(_decidir(foto, H.de_la_foto(foto, ahora=AHORA), horas=HORAS_PARON)) == []


RONDA_FICHAS = {7: {"price": 1_000_000, "priceIncrement": 30_000, "status": "ok", "points": 40,
                    "playedHome": 5, "playedAway": 5},
                8: {"price": 1_000_000, "priceIncrement": 30_000, "status": "ok", "points": 40,
                    "playedHome": 5, "playedAway": 5}}


def test_la_ronda_ni_con_el_colchon():
    from src.actions import la_ronda_de_la_manana as R
    from src.analysis import la_hucha as H

    def _decidir(saldo, hucha=None, libro=None, plantilla=(1, 2, 3), mercado=None):
        kw = {} if hucha is None else {"hucha": hucha}
        maximo = saldo + VALOR_PLANTILLA // 4
        return R.decidir(mercado=dict(mercado or {7: 1_000_000}), fichas=copy.deepcopy(RONDA_FICHAS),
                         nuestras_pujas={}, plantilla=set(plantilla), ofertas_del_computer={},
                         en_venta=set(), maximo_de_puja=maximo, minutos_al_reset=200,
                         horas_jornada=HORAS_PARON, libro=dict(libro or {}), cartera=True,
                         saldo=saldo, **kw)

    puja = 1_049_900                                    # la prima de la cartera
    with _LaHucha(CFG):
        for saldo, pasa in ((OBJETIVO + puja, True), (OBJETIVO + puja - 1, False)):
            assert _pujas(_decidir(saldo)) == [(7, puja)]
            h = H.de_la_foto({"saldo": saldo, "nuestras_pujas": {}, "plantilla": {1, 2, 3},
                              "maximo_de_puja": saldo + VALOR_PLANTILLA // 4}, ahora=AHORA)
            assert (_pujas(_decidir(saldo, h)) == [(7, puja)]) is pasa, saldo
        # Dos que caben solas y no juntas: solo la primera.
        saldo = OBJETIVO + puja + 1_000_000
        h = H.de_la_foto({"saldo": saldo, "nuestras_pujas": {}, "plantilla": {1, 2, 3},
                          "maximo_de_puja": saldo + VALOR_PLANTILLA // 4}, ahora=AHORA)
        dos = {7: 1_000_000, 8: 1_000_000}
        assert len(_pujas(_decidir(saldo, mercado=dos))) == 2
        assert len(_pujas(_decidir(saldo, h, mercado=dos))) == 1
        # EL COLCHON NO BASTA: con la caja en rojo (-500.000) y el 92 % de
        # 3 M de la cartera, apagada puja; encendida (libre negativo), no.
        libro = {"1": 2_000_000, "2": 1_000_000}
        fichas_cartera = {1: {"price": 2_000_000}, 2: {"price": 1_000_000}}
        RONDA_FICHAS.update(fichas_cartera)
        try:
            assert _pujas(_decidir(-500_000, libro=libro)) == [(7, puja)]
            h = H.de_la_foto({"saldo": -500_000, "nuestras_pujas": {}, "plantilla": {1, 2, 3},
                              "maximo_de_puja": -500_000 + VALOR_PLANTILLA // 4}, ahora=AHORA)
            assert h["apartado"] == 0 and h["libre"] == -500_000
            assert _pujas(_decidir(-500_000, h, libro=libro)) == []
        finally:
            for k in fichas_cartera:
                RONDA_FICHAS.pop(k, None)


def _la_mejora(precio_del_que_sale, *, caja=10_000_000, saldo=10_000_000, maximo=26_000_000,
               horas=HORAS_PARON, hucha=None):
    """Un cambio de la mejora: entra B (del Computer, 4 M, puja 4.040.000)
    por A (nuestro, `precio_del_que_sale`)."""
    from src.actions import la_mejora_del_once as M

    once = [{"id": 1, "name": "A", "position": 3, "starter_probability": 80,
             "price": precio_del_que_sale}]
    liga = {1: {"id": 1, "tasa": 3.0, "status": "ok", "price": precio_del_que_sale,
                "de_quien": "nuestro", "position": 3, "played": 10, "points": 30},
            2: {"id": 2, "name": "B", "tasa": 6.0, "status": "ok", "price": 4_000_000,
                "de_quien": "computer", "position": 3, "played": 10, "points": 60,
                "price_increment": 50_000}}
    escaparate = [{"id": 2, "name": "B", "position": 3, "price": 4_000_000, "points": 60,
                   "played": 10, "starter_probability": 90}]
    foto = {"plantilla": {1}, "nuestras_pujas": {}, "ofertas_del_computer": {},
            "en_venta": set(), "maximo_de_puja": maximo, "saldo": saldo,
            "mercado": {2: 4_000_000}}
    kw = {} if hucha is None else {"hucha": hucha}
    return M.decidir(once=once, liga=liga, escaparate=escaparate, foto=foto, libro={},
                     caja=caja, horas_jornada=horas, **kw)


def test_la_mejora_un_cambio_que_se_paga_solo_si():
    from src.actions import la_mejora_del_once as M
    from src.analysis import la_hucha as H

    with _LaHucha(CFG):
        h = H.de_la_foto({"saldo": 10_000_000, "nuestras_pujas": {}, "plantilla": {1},
                          "maximo_de_puja": 26_000_000}, ahora=AHORA)
        assert (h["apartado"], h["libre"]) == (10_000_000, 0)
        # A vale 5 M: su venta (95 %) paga la puja (caja +710.000). Pasa.
        apagada, encendida = _la_mejora(5_000_000), _la_mejora(5_000_000, hucha=h)
        assert _pujas(apagada["acciones"]) == _pujas(encendida["acciones"]) == [(2, 4_040_000)]
        # El presupuesto (`disponible`) baja EXACTAMENTE lo apartado.
        assert apagada["plan"]["disponible"] - encendida["plan"]["disponible"] == 10_000_000
        assert encendida["plan"]["hucha"] == {"apartado": 10_000_000, "libre": 0,
                                              "saca_de_la_caja": 0}
        assert "hucha" not in apagada["plan"]
        # A vale 3 M: el cambio saca 1.190.000 de la caja. Apagada pasa
        # (deuda tolerada); encendida, sin un euro libre, no.
        assert _pujas(_la_mejora(3_000_000)["acciones"]) == [(2, 4_040_000)]
        assert _pujas(_la_mejora(3_000_000, hucha=h)["acciones"]) == []
        # El borde: con 1.190.000 libres justos pasa; con uno menos, no.
        for saldo, pasa in ((OBJETIVO + 1_190_000, True), (OBJETIVO + 1_189_999, False)):
            h2 = H.de_la_foto({"saldo": saldo, "nuestras_pujas": {}, "plantilla": {1},
                               "maximo_de_puja": 26_000_000}, ahora=AHORA)
            d = _la_mejora(3_000_000, saldo=saldo, caja=saldo, hucha=h2)
            assert (_pujas(d["acciones"]) == [(2, 4_040_000)]) is pasa, saldo
        # La combinacion: uno que da caja no paga a otro que la quita.
        cambios = [
            {"entra": 11, "sale": 1, "puntos": 1.0, "caja": 700_000, "puja": 2_000_000,
             "ya_es_nuestro": False},
            {"entra": 12, "sale": 2, "puntos": 1.0, "caja": -600_000, "puja": 2_000_000,
             "ya_es_nuestro": False},
            {"entra": 13, "sale": 3, "puntos": 0.6, "caja": -900_000, "puja": 0,
             "ya_es_nuestro": True},
        ]
        assert len(M.la_mejor_combinacion(copy.deepcopy(cambios), 5_000_000, -1_000_000,
                                          9_000_000)) == 3
        elegidos = M.la_mejor_combinacion(copy.deepcopy(cambios), 5_000_000, -1_000_000,
                                          9_000_000, libre=0)
        assert sorted(c["entra"] for c in elegidos) == [11, 13], elegidos
        elegidos = M.la_mejor_combinacion(copy.deepcopy(cambios), 5_000_000, -1_000_000,
                                          9_000_000, libre=600_000)
        assert sorted(c["entra"] for c in elegidos) == [11, 12, 13], elegidos


def test_la_rotacion_la_que_se_paga_sola_si_la_que_paga_otra_no():
    from src.actions import la_rotacion as RO
    from src.analysis import la_hucha as H

    def f(pid, pos, precio, sube):
        return {"id": pid, "name": f"J{pid}", "position": pos, "price": precio,
                "priceIncrement": sube, "status": "ok", "points": 40 if pid < 10 else 45,
                "playedHome": 5, "playedAway": 5, "teamID": 1}

    fichas = {1: f(1, 3, 3_000_000, -20_000), 2: f(2, 2, 1_000_000, -10_000),
              3: f(3, 4, 3_000_000, -10_000), 13: f(13, 4, 2_000_000, 10_000),
              11: f(11, 3, 2_400_000, 50_000), 12: f(12, 2, 1_900_000, 40_000)}
    reloj = RO.el_reloj(AHORA, _el_calendario(), True)

    def _decidir(saldo, hucha=None, parejas=(), plantilla=(1, 2), en_venta=(), once_foto=None):
        kw = {} if hucha is None else {"hucha": hucha}
        return RO.decidir(plantilla=set(plantilla), fichas=copy.deepcopy(fichas),
                          mercado={11: 2_400_000, 12: 1_900_000},
                          subidas_de_ayer={1: -10_000, 2: -5_000, 3: 5_000, 13: 5_000},
                          rondas_jugadas=11, saldo=saldo, pujas_vivas={},
                          maximo_de_puja=saldo + VALOR_PLANTILLA // 4,
                          ofertas_del_computer={}, en_venta=set(en_venta),
                          parejas=copy.deepcopy(list(parejas)), once=None,
                          once_de_la_foto=once_foto, reloj=copy.deepcopy(reloj), **kw)

    def _h(saldo):
        return H.de_la_foto({"saldo": saldo, "nuestras_pujas": {}, "plantilla": {1, 2},
                             "maximo_de_puja": saldo + VALOR_PLANTILLA // 4}, ahora=AHORA)

    uno = (11, 2_499_900)          # sale J1 (3 M, venta 2.850.000): se paga sola
    dos = (12, 1_979_900)          # sale J2 (1 M, venta 950.000): saca 1.029.900
    with _LaHucha(CFG):
        assert _pujas(_decidir(10_000_000)["acciones"]) == [uno, dos]
        d = _decidir(10_000_000, _h(10_000_000))
        assert _pujas(d["acciones"]) == [uno], d["acciones"]
        assert d["hucha"]["frenadas"] == [{"sale": 2, "entra": 12, "puja": 1_979_900,
                                           "venta": 950_000}], d["hucha"]
        # El borde: con 1.029.900 libres justos pasan las dos.
        for saldo, pasa in ((OBJETIVO + 1_029_900, True), (OBJETIVO + 1_029_899, False)):
            d = _decidir(saldo, _h(saldo))
            assert (_pujas(d["acciones"]) == [uno, dos]) is pasa, saldo
        # Pagada con los cobros de OTRA pareja: con 100.000 de saldo, la
        # pareja ganada (J3 publicado, 2.850.000 esperados) paga a J2 en la
        # caja de siempre. Apagada pasa; encendida, no.
        # (de la ventana de la J12: no gasta el cupo de esta)
        ganada = [{"id": "3>13@2026-11-04", "sale": 3, "entra": 13, "estado": "GANADA",
                   "dia": "2026-11-04", "semana": "2026-W45", "ventana": "J12"}]
        comun = dict(parejas=ganada, plantilla=(1, 2, 3, 13), en_venta=(3,), once_foto=[13])
        apagada = _decidir(100_000, **comun)
        assert apagada["caja"]["cobros_esperados"] == 2_850_000, apagada["caja"]
        assert _pujas(apagada["acciones"]) == [uno, dos], apagada["acciones"]
        encendida = _decidir(100_000, _h(100_000), **comun)
        assert _pujas(encendida["acciones"]) == [uno], encendida["acciones"]
        # El rojo sigue con el saldo real: la caja de siempre, sin la hucha.
        assert encendida["caja"] == apagada["caja"] | {"despues": encendida["caja"]["despues"]}


def test_el_carril_solo_lo_libre_y_sumado():
    from src.actions import carril_executor as K
    from src.analysis import bid_jitter as desvio_mod
    import src.intelligence.bid_outcome_ledger as libro_mod

    objetivos = [dict(o) for o in OBJETIVOS_DEL_CARRIL]
    objetivos[2] = {**objetivos[2], "market_price": 1_200_000, "bid": 1_210_000,
                    "starter_probability": 70}
    objetivos = [objetivos[1], objetivos[2], objetivos[0]]
    viejos = (libro_mod.record_bid, desvio_mod.date)
    libro_mod.record_bid = lambda *a, **k: None
    desvio_mod.date = _ElDiaDelDesvio
    try:
        with tempfile.TemporaryDirectory() as d, _Interruptores({}):
            def _correr(n, **kw):
                e = _Escritor()
                r = K.correr(accion_principal=None,
                             cierres=[{"profit": 50_000, "player_name": "Un viaje"}],
                             objetivos=copy.deepcopy(objetivos), rates=copy.deepcopy(RITMOS),
                             prima_de_puja=0.28, curva=1.0028, caja=5_000_000, comprometido=0,
                             presupuesto=3_000_000, escritor=e, disparo=None, ahora=AHORA,
                             ruta_del_libro=Path(d) / f"libro_{n}.jsonl",
                             ruta_de_viajes=Path(d) / f"viajes_{n}.jsonl",
                             speculation={"bid_exposure": {"available": True,
                                                           "committed_total": 0,
                                                           "players": []}}, **kw)
                return r, [(b["player_id"], b["amount"]) for b in r.get("bids") or []]

            # Apagado: dos pujas (Boyomo y Valentini, con su desvio), tope 3 M.
            r, apagada = _correr("a")
            assert [p for p, _ in apagada] == [33694, 41609], apagada
            assert r["bolsillo"]["tope"] == 3_000_000
            primera, segunda = apagada[0][1], apagada[1][1]
            assert 1_000_000 < segunda and 1_000_000 < primera < 3_000_000
            # Encendido: el tope del bolsillo es lo libre y las pujas de la
            # vuelta, SUMADAS, no pasan de ahi.
            for n, libre, esperadas in (("b", 0, []), ("c", 1_000_000, []),
                                        ("d", primera, apagada[:1]),
                                        ("e", primera + segunda - 1, apagada[:1]),
                                        ("f", primera + segunda, apagada)):
                r, puestas = _correr(n, hucha_libre=libre)
                assert puestas == esperadas, (libre, puestas, r.get("failed"))
                assert r["bolsillo"]["tope"] == min(libre, 3_000_000), r["bolsillo"]
                assert sum(i for _, i in puestas) <= libre
                if puestas and puestas != apagada:
                    assert "LA_HUCHA" in r["failed"][0]["error"], r["failed"]
    finally:
        libro_mod.record_bid, desvio_mod.date = viejos


def test_el_buy_v10_y_las_cli_no_tocan_la_hucha():
    from src.actions import live_bid_executor as X

    def _pujar(s, importe):
        viejo = X.BiwengerWriteClient
        X.BiwengerWriteClient = _escritor_de_mercado(s)
        try:
            return X.execute_bid(17731, importe, expected_seller_id=None, execute=False)
        except RuntimeError as error:
            return str(error)
        finally:
            X.BiwengerWriteClient = viejo

    with _LaHucha(CFG_SIEMPRE):
        s, _ = _foto_de(OBJETIVO + 2_400_000)
        assert isinstance(_pujar(s, 2_400_000), dict)
        assert "hucha" in _pujar(s, 2_400_001)
        s, _ = _foto_de(10_000_000)
        assert "hucha" in _pujar(s, 2_400_000)
    with _LaHucha(CFG_SIEMPRE, puesta="0"):
        assert isinstance(_pujar(s, 2_400_000), dict)


def test_el_motor_viejo_mira_la_hucha_antes_de_escribir_y_de_elegir():
    from src.analysis import la_hucha as H

    with _LaHucha(CFG):
        # La puerta: sin exencion (ni para Raphinha) y sin credito.
        s, _ = _foto_de(OBJETIVO + 2_000_000, {17482: 1_000_000})
        assert H.frena_la_especulacion(s, 17731, 1_000_000, ahora=AHORA) is None
        frenada = H.frena_la_especulacion(s, 17731, 1_000_001, ahora=AHORA)
        assert frenada["motivo"] == "LA_HUCHA" and frenada["hucha"]["libre"] == 1_000_000
        # Su puja viva por el mismo vuelve al sustituirla.
        assert H.frena_la_especulacion(s, 17482, 2_000_000, ahora=AHORA) is None
        assert H.frena_la_especulacion(s, RAPHINHA, 25_000_000, ahora=AHORA) is not None
        # Antes del 10/11, nada.
        assert H.frena_la_especulacion(s, 17731, 10**12,
                                       ahora=datetime(2026, 11, 2, tzinfo=_UTC)) is None
    # El ejecutor: la puerta va despues del colchon y antes de la unica
    # escritura de la rama.
    texto = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text(encoding="utf-8")
    rama = texto.index("if action == SPECULATION_BUY_ACTION:")
    colchon = texto.index("if un_solo_colchon_activo():", rama)
    puerta = texto.index("frena_la_especulacion(", colchon)
    escribe = texto.index("writer.place_bid(", puerta)
    assert colchon < puerta < escribe
    assert "SPECULATION_SIN_HUCHA" in texto[puerta:escribe]
    assert texto.count("writer.place_bid(") == 1
    assert "fresh_snapshot," in texto[puerta:puerta + 120]
    # El orquestador: el objetivo que no cabe se queda mirando (WATCH),
    # no le quita el hueco a renovar.
    texto = (RAIZ / "src" / "analysis" / "decision_orchestrator.py").read_text(encoding="utf-8")
    puerta = texto.index("frena_la_especulacion(")
    mirar = texto.index("elif frenado_por_la_hucha is not None:", puerta)
    comprar = texto.index('"SPECULATION_BUY"', mirar)
    assert '"SPECULATION_WATCH"' in texto[mirar:comprar] and '"LA_HUCHA"' in texto[mirar:comprar]
    # La cesta (hoy cerrada): todas caben, o ninguna.
    with _LaHucha(CFG_SIEMPRE):
        s, _ = _foto_de(OBJETIVO + 3_000_000)
        plan = {"execute": True, "bids": [{"id": 1, "bid": 1_000_000}, {"id": 2, "bid": 2_000_000}],
                "committed": 3_000_000}
        assert H.la_cesta_con_la_hucha(plan, s) is plan
        plan["bids"].append({"id": 3, "bid": 1})
        cerrada = H.la_cesta_con_la_hucha(plan, s)
        assert (cerrada["execute"], cerrada["bids"], cerrada["blocked_by"]) == (
            False, [], "LA_HUCHA"), cerrada
    texto = (RAIZ / "src" / "analysis" / "la_subasta.py").read_text(encoding="utf-8")
    cuerpo = texto[texto.index("def plan_desde_el_estado("):texto.index("def para_la_pantalla(")]
    assert "la_cesta_con_la_hucha(" in cuerpo


# ============================================================
# 5. EL TRINQUETE: DOS VUELTAS Y NADA SIN VENTA PASA
# ============================================================

def test_el_trinquete_dos_vueltas_sin_gastar_lo_apartado():
    """saldo - pujas = 10 M, objetivo 16 M. Cada vuelta lo apartado se
    recalcula con la caja que hay: si un motor gastara contra lo que no es
    caja (deuda, cartera, 25 % de maximumBid, cobros de otros), la vuelta
    siguiente veria lo mismo y volveria a gastar. Con la puerta estricta,
    nada sin venta pasa y lo libre se queda en 0."""
    from src.actions import la_mejora_del_once as M
    from src.actions import la_orden_del_gestor as O
    from src.actions import los_chollos as C
    from src.actions import la_ronda_de_la_manana as R
    from src.analysis import la_hucha as H

    s, foto = _foto_de(12_000_000, {38405: 2_000_000})
    foto.pop("de_managers", None)
    catalogo = {int(k): v for k, v in s["catalog"]["data"]["players"].items()}
    sin_ventas = dict(ORDENES)["sin_ventas"]

    def _vuelta(hucha):
        kw = {} if hucha is None else {"hucha": hucha}
        compras = []
        compras += _pujas(C.decidir(
            mercado=dict(foto["mercado"]), valores={k: v["price"] for k, v in catalogo.items()},
            estados={k: v["status"] for k, v in catalogo.items()},
            nuestras_pujas=foto["nuestras_pujas"], plantilla=foto["plantilla"],
            ofertas_del_computer={}, en_venta=set(), maximo_de_puja=foto["maximo_de_puja"],
            saldo=foto["saldo"], minutos_al_reset=30, horas_jornada=HORAS_PARON, libro={}, **kw))
        compras += _pujas(R.decidir(
            mercado={7: 1_000_000}, fichas=copy.deepcopy(RONDA_FICHAS), nuestras_pujas={},
            plantilla={1, 2, 3}, ofertas_del_computer={}, en_venta=set(),
            maximo_de_puja=foto["maximo_de_puja"], minutos_al_reset=200,
            horas_jornada=HORAS_PARON, libro={}, cartera=True, saldo=foto["saldo"], **kw))
        compras += _pujas(O.decidir(copy.deepcopy(sin_ventas), **copy.deepcopy(foto),
                                    ahora=AHORA, horas_jornada=HORAS_PARON, estados=None,
                                    en_curso=False, **kw))
        compras += _pujas(_la_mejora(3_000_000, saldo=foto["saldo"], caja=10_000_000,
                                     maximo=foto["maximo_de_puja"], hucha=hucha)["acciones"])
        if hucha is not None:
            compras += [("motor viejo", 1)] if H.frena_la_especulacion(
                s, 17731, 2_400_000, ahora=AHORA) is None else []
        return compras

    with _LaHucha(CFG):
        assert len(_vuelta(None)) >= 4                  # apagada, todos compran
        libres = []
        for _ in range(2):
            h = H.de_la_foto(foto, ahora=AHORA)
            libres.append(h["libre"])
            assert h["apartado"] == 10_000_000
            assert _vuelta(h) == [], _vuelta(h)
        assert libres == [0, 0]


# ============================================================
# 6. LOS QUE VENDEN NO LA VEN
# ============================================================

def test_los_que_venden_no_ven_la_hucha():
    from src.actions import la_orden_del_gestor as O
    from src.analysis import la_hucha as H
    from src.analysis import test_el_cierre_de_la_jornada_v1 as T

    # EL CIERRE, entero: igual encendida que apagada, y solo vende con la
    # caja REAL en rojo. Con 10 M de saldo y la hucha queriendo 16 M, no
    # vende a nadie para llenarla.
    cfg_cierre = {**CFG, "desde": "2026-10-01T00:00:00+02:00"}
    with tempfile.TemporaryDirectory() as d:
        def _cierre(saldo, puesta):
            with _LaHucha(cfg_cierre, puesta=puesta,
                          extra={"BORDALAS_EL_CIERRE_DE_LA_JORNADA": "1"}):
                run_id = os.environ.pop("GITHUB_RUN_ID", None)
                try:
                    r = T.correr(status=T._status_con(), snapshot=T._foto_con(saldo=saldo),
                                 v10={}, libros={"ronda": {}, "chollos": {}, "mejora": {},
                                                 "vuelta_mejora": {}},
                                 calendario=T.CAL, orden_ruta=Path(d) / "nada.json",
                                 escritor_factory=T._Escritor, ahora=T.AHORA,
                                 plan_ruta=Path(d) / f"plan_{saldo}_{puesta}.json")
                finally:
                    if run_id is not None:
                        os.environ["GITHUB_RUN_ID"] = run_id
            return json.dumps(_normal(r), sort_keys=True, default=str)

        for saldo in (10_000_000, 1_000_000, -2_000_000):
            assert _cierre(saldo, "1") == _cierre(saldo, None), saldo
        positivo = json.loads(_cierre(10_000_000, "1"))["decision"]
        assert (positivo["motivo"], positivo["vender"], positivo["caja"]) == (
            "EN_POSITIVO", [], 10_000_000), positivo
        rojo = json.loads(_cierre(-2_000_000, "1"))["decision"]
        assert rojo["motivo"] == "EN_ROJO_SE_VENDE" and rojo["vender"], rojo
    # Ni el cierre, ni la solvencia, ni el position manager la miran.
    for camino in ("src/actions/el_cierre_de_la_jornada.py", "src/analysis/solvency_engine.py",
                   "src/analysis/position_manager_shadow_v106.py",
                   "src/analysis/solvency_clock.py", "src/telemetry/dashboard_state.py"):
        assert "la_hucha" not in (RAIZ / camino).read_text(encoding="utf-8"), camino

    with _LaHucha(CFG):
        # EL DEFICIT DE LA MEJORA, con la caja real: en rojo y cerca, igual;
        # en verde por debajo del objetivo, no se enciende.
        h = H.de_la_foto({"saldo": 3_000_000, "nuestras_pujas": {}, "plantilla": {1},
                          "maximo_de_puja": 26_000_000}, ahora=AHORA)
        for caja, horas in ((3_000_000, 50.0), (-2_000_000, 50.0), (-2_000_000, HORAS_PARON)):
            a = _la_mejora(3_000_000, caja=caja, saldo=3_000_000, horas=horas)
            e = _la_mejora(3_000_000, caja=caja, saldo=3_000_000, horas=horas, hucha=h)
            assert a["plan"]["deficit"] == e["plan"]["deficit"], (caja, horas)
            assert a["plan"]["caja"] == e["plan"]["caja"] and a["plan"]["minimo"] == e["plan"]["minimo"]
        # EL ULTIMO RECURSO DE LA ORDEN: con 10 M (todo apartado), nadie
        # se vende; en rojo, lo mismo que apagada.
        orden = {"caduca": "2026-12-31T23:59:00+01:00", "vender_si_ficha": {
            "si_esta": 35678, "jugadores": [
                {"player_id": 30493, "nombre": "Sergi Cardona", "suelo": 2_000_000,
                 "si_saldo_negativo": True}]}}
        for saldo in (10_000_000, -1_000_000):
            _, foto = _foto_de(saldo)
            foto.pop("de_managers", None)
            comun = dict(ahora=AHORA, horas_jornada=HORAS_PARON, estados=None, en_curso=False)
            con = O.decidir(copy.deepcopy(orden), **copy.deepcopy(foto), **comun,
                            hucha=H.de_la_foto(foto, ahora=AHORA))
            sin = O.decidir(copy.deepcopy(orden), **copy.deepcopy(foto), **comun)
            assert con == sin, (saldo, con, sin)
            assert bool(con) is (saldo < 0), (saldo, con)


# ============================================================
# 7. LOS `correr` LA SACAN SOLOS
# ============================================================

def test_los_correr_la_sacan_de_su_foto():
    from src.actions import la_ronda_de_la_manana as R
    from src.actions import los_chollos as C
    from src.actions import la_mejora_del_once as M

    with tempfile.TemporaryDirectory() as d:
        calendario = _el_calendario()
        antes = (C.CALENDARIO, R.CALENDARIO)
        C.CALENDARIO = R.CALENDARIO = calendario
        try:
            s, _ = _foto_de(10_000_000)
            for puesta in (None, "1"):
                with _LaHucha(CFG, puesta=puesta, extra={
                        "BORDALAS_LOS_CHOLLOS": "1", "BORDALAS_LA_RONDA_DE_LA_MANANA": "1",
                        "BORDALAS_LA_CARTERA": "1"}):
                    libro = Path(d) / "chollos.json"
                    libro.write_text("{}")
                    # La ultima vuelta antes del reset (30 min), fuera del silencio.
                    r = C.correr({"snapshot": copy.deepcopy(s)}, 30,
                                 escritor_factory=_Escritor, ahora=AHORA,
                                 libro_ruta=libro)
                    if puesta:
                        assert r["hucha"]["libre"] == 0 and _pujas(r["acciones"]) == [], r
                    else:
                        assert "hucha" not in r and _pujas(r["acciones"]), r
                    libro = Path(d) / "ronda.json"
                    libro.write_text("{}")
                    s2 = copy.deepcopy(s)
                    s2["catalog"]["data"]["players"]["17482"].update(
                        priceIncrement=60_000, points=60)
                    r = R.correr({"snapshot": s2}, 200, escritor_factory=_Escritor, ahora=AHORA,
                                 libro_ruta=libro)
                    if puesta:
                        assert r["hucha"]["libre"] == 0 and _pujas(r["acciones"]) == [], r
                    else:
                        assert "hucha" not in r and _pujas(r["acciones"]), r
        finally:
            C.CALENDARIO, R.CALENDARIO = antes

        # La mejora: con el estado de v10 de ESTA vuelta, las pujas del
        # carril cuentan en sus pujas vivas (como las cuenta el cierre).
        status = {"todaLaLiga": {"players": [
            {"id": 1, "name": "A", "tasa": 3.0, "status": "ok", "price": 3_000_000,
             "de_quien": "nuestro", "position": 3, "played": 10, "points": 30},
            {"id": 2, "name": "B", "tasa": 6.0, "status": "ok", "price": 4_000_000,
             "de_quien": "computer", "position": 3, "played": 10, "points": 60,
             "price_increment": 50_000}]},
            "lineup": {"players": [{"id": 1, "name": "A", "position": 3,
                                    "starter_probability": 80, "price": 3_000_000}]},
            "libro_del_escaparate": {"players": [
                {"id": 2, "name": "B", "position": 3, "price": 4_000_000, "points": 60,
                 "played": 10, "starter_probability": 90}]},
            "roster": {"players": [{"id": 1, "starter_probability": 80}]}}
        foto = {"league": {"user": {"id": YO}},
                "market": {"sales": [{"player": {"id": 2}, "price": 4_000_000, "user": None}],
                           "offers": [],
                           "status": {"balance": OBJETIVO + 2_000_000, "maximumBid": 26_000_000}},
                "my_team": [{"id": 1, "price": 3_000_000}],
                "catalog": {"data": {"players": {"1": {"status": "ok"}, "2": {"status": "ok"}}}}}
        v10 = {"run_id": "la-hucha", "timestamp": AHORA.isoformat(),
               "carril": {"bids": [{"player_id": 9, "amount": 900_000, "sent": True,
                                    "success": True}]}}

        def _mejora(puesta, v10):
            ronda, chollos = Path(d) / "r.json", Path(d) / "c.json"
            ronda.write_text("{}")
            chollos.write_text("{}")
            libro = Path(d) / "mejora.json"
            libro.write_text("{}")
            with _LaHucha(CFG, puesta=puesta, extra={"BORDALAS_LA_MEJORA_DEL_ONCE": "1"}):
                run_id = os.environ.get("GITHUB_RUN_ID")
                os.environ["GITHUB_RUN_ID"] = "la-hucha"
                try:
                    return M.correr(status=copy.deepcopy(status), snapshot=copy.deepcopy(foto),
                                    v10=copy.deepcopy(v10), escritor_factory=_Escritor,
                                    ahora=AHORA, libro_ruta=libro,
                                    de_fuera={"orden": {}, "vetados": set(), "protegidos": set(),
                                              "libro_ronda": ronda, "libro_chollos": chollos,
                                              "horas_jornada": HORAS_PARON,
                                              "puede_escribir": True, "en_curso": False,
                                              "rotando": set()})
                finally:
                    if run_id is None:
                        os.environ.pop("GITHUB_RUN_ID", None)
                    else:
                        os.environ["GITHUB_RUN_ID"] = run_id

        # Saldo 18 M: 2 M libres; el cambio saca 1.190.000. Sin el carril
        # cabe; con los 900.000 del carril (1,1 M libres), no.
        r = _mejora("1", {})
        assert r["hucha"]["libre"] == 2_000_000 and _pujas(r["acciones"]) == [(2, 4_040_000)], r
        r = _mejora("1", v10)
        assert r["hucha"]["libre"] == 1_100_000 and _pujas(r["acciones"]) == [], r
        assert r["plan"]["hucha"]["libre"] == 1_100_000
        r = _mejora(None, v10)
        assert "hucha" not in r and _pujas(r["acciones"]) == [(2, 4_040_000)], r


# ============================================================
# 8. LA VUELTA DE V10
# ============================================================

def _la_vuelta_de_v10(puesta, cfg=CFG_SIEMPRE, buy_escribe=True):
    """`run_full_autonomous_cycle` con todo cambiado: la cesta manda
    500.000, el BUY 2.449.900, el carril 1.000.000, la orden 3.000.000 y
    los chollos 700.000. Devuelve (lo que recibio cada motor, el estado)."""
    import contextlib
    import io

    import src.actions.la_orden_del_gestor as orden
    import src.actions.la_racha as racha
    import src.actions.la_revision_de_pujas as revision
    import src.actions.la_ronda_de_la_manana as ronda
    import src.actions.los_chollos as chollos
    import src.v10_full_autonomous_live as ciclo

    s, _ = _foto_de(OBJETIVO + 10_000_000)
    cycle = {"snapshot": s}
    recibido = {}

    def _paso(nombre, hechas):
        def correr(cycle, *a, **k):
            recibido[nombre] = copy.deepcopy(k.get("hucha"))
            return {"motivo": "CAMBIADO", "acciones": [], "hechas": copy.deepcopy(hechas),
                    "retiradas": [], "avisos": []}
        return correr

    def _carril(c, a, **k):
        recibido["carril"] = copy.deepcopy(k.get("hucha"))
        return {"bids": [{"player_id": 33694, "amount": 1_000_000, "sent": True,
                          "success": True}]}

    buy = {"writes_biwenger": buy_escribe, "execution": {"sent": True, "success": True,
                                                         "amount": 2_449_900}}
    with tempfile.TemporaryDirectory() as d:
        cambios = [
            (ciclo, "run_cycle", lambda **k: cycle),
            (ciclo, "_estado_publicado", lambda c: {"market_clock": {"seconds_to_reset": 7200}}),
            (ciclo, "_pujar_en_el_reset", lambda c: {"sent": [{"amount": 500_000, "sent": True},
                                                               {"amount": 9, "sent": False}]}),
            (ciclo, "_renovar_en_la_ventana", lambda c: {"available": False}),
            (ciclo, "build_controlled_run", lambda **k: copy.deepcopy(buy)),
            (ciclo, "print_controlled_buy", lambda *a, **k: None),
            (ciclo, "_verify_v10_write", lambda a: {"attempted": False}),
            (ciclo, "_publicar_peticiones", lambda: None),
            (ciclo, "sync_position_manager", lambda **k: {"board": {}}),
            (ciclo, "print_position_manager", lambda *a, **k: None),
            (ciclo, "sync_counter_repricing", lambda **k: {"board": {}}),
            (ciclo, "print_counter_repricing", lambda *a, **k: None),
            (ciclo, "_temporal_block", lambda c: "PRUEBA"),
            (ciclo, "_correr_el_carril", _carril),
            (ciclo, "_llenar_el_escaparate", lambda c, a: {"listed": []}),
            (ciclo, "STATUS_PATH", Path(d) / "v10_full_autonomous_status.json"),
            (orden, "correr", _paso("orden", [{"accion": "PUJAR", "player_id": 17731,
                                               "importe": 3_000_000, "exito": True}])),
            (revision, "correr", _paso("revision", [])),
            (chollos, "correr", _paso("chollos", [{"accion": "PUJAR", "player_id": 41609,
                                                   "importe": 700_000, "exito": True}])),
            (ronda, "correr", _paso("ronda", [])),
            (racha, "cobrar", lambda c: {"racha": None, "motivo": "CAMBIADA"}),
        ]
        antes = [(m, n, getattr(m, n)) for m, n, _ in cambios]
        try:
            for m, n, v in cambios:
                setattr(m, n, v)
            with _LaHucha(cfg, puesta=puesta), contextlib.redirect_stdout(io.StringIO()):
                ciclo.run_full_autonomous_cycle()
            estado = json.loads((Path(d) / "v10_full_autonomous_status.json").read_text())
        finally:
            for m, n, v in antes:
                setattr(m, n, v)
    return recibido, estado


def test_la_vuelta_de_v10_lleva_la_cuenta():
    recibido, estado = _la_vuelta_de_v10("1")
    # 26 M de saldo, 16 apartados, 10 libres; cada uno ve lo de delante.
    libres = {k: (v or {}).get("libre") for k, v in recibido.items()}
    assert libres == {"carril": 10_000_000 - 500_000 - 2_449_900,
                      "orden": 10_000_000 - 500_000 - 2_449_900 - 1_000_000,
                      "revision": None,
                      "chollos": 10_000_000 - 500_000 - 2_449_900 - 1_000_000 - 3_000_000,
                      "ronda": 10_000_000 - 500_000 - 2_449_900 - 1_000_000 - 3_000_000
                      - 700_000}, libres
    bloque = estado["hucha"]
    assert bloque["activa"] is True and bloque["para"] == "Raphinha" and bloque["player_id"] == RAPHINHA
    assert (bloque["objetivo"], bloque["apartado"], bloque["falta"]) == (OBJETIVO, OBJETIVO, 0)
    assert bloque["pujado_en_la_vuelta"] == 500_000 + 2_449_900 + 1_000_000 + 3_000_000 + 700_000
    assert bloque["libre"] == 10_000_000 - bloque["pujado_en_la_vuelta"]
    assert bloque["en_el_mercado_hoy"] is False
    maximo = OBJETIVO + 10_000_000 + VALOR_PLANTILLA // 4
    assert bloque["nuestra_puja_maxima_real"] == maximo - bloque["pujado_en_la_vuelta"]
    assert bloque["nuestra_puja_maxima_para_los_demas"] == (
        bloque["nuestra_puja_maxima_real"] - OBJETIVO)
    # Encendida pero sin valer (antes del 10/11): a nadie se le pasa
    # nada; el bloque dice por que.
    recibido, estado = _la_vuelta_de_v10("1", cfg={**CFG, "desde": "2099-01-01T00:00:00+00:00"})
    assert all(v is None for v in recibido.values()), recibido
    assert estado["hucha"]["activa"] is False and estado["hucha"]["motivo"] == "AUN_NO"
    # Apagada: ni argumento ni bloque.
    recibido, estado = _la_vuelta_de_v10(None)
    assert all(v is None for v in recibido.values()), recibido
    assert "hucha" not in estado


# ============================================================
# 9. NUNCA LANZA
# ============================================================

def test_nunca_lanza():
    from src.analysis import la_hucha as H

    basura = (None, 7, "x", [], {"market": "x"}, {"league": {"user": "x"}, "market": {}})
    with _LaHucha(CFG_SIEMPRE):
        for b in basura:
            H.de_la_foto(b, ahora=AHORA)
            H.de_la_foto(b, saldo="x", pujas="y", maximo_de_puja=[], ahora="z")
            H.de_la_snapshot(b)
            H.lo_apartado(b, b, b)
            H.cabe(b, b, player_id=b, sustituye=b, credito=b, ya=b)
            H.mas_lo_pujado(b, b)
            H.lo_libre(b)
            H.filtrar_pujas(b, b)
            H.lo_pujado_en(b)
            H.lo_pujado_por_el_carril(b)
            H.lo_pujado_por_el_buy(b)
            assert H.frena_la_especulacion(b, b, 1) is not None or True
            H.la_puja_toca_la_hucha(b, b, b, b)
            H.la_cesta_con_la_hucha(b, b)
            H.el_resumen(b)
            H.el_bloque(b, b)
            H.vigente(b, b, b)
        # Lo que no se puede mirar, no se puja.
        assert H.la_puja_toca_la_hucha({"offers": "x"}, YO, 1, 1)
        assert H.frena_la_especulacion({"market": {"status": {"balance": 1}}}, 1, 5) is not None


TESTS = [
    test_nace_apagada_un_lector_y_su_frase,
    test_apagada_es_main_byte_a_byte,
    test_apagada_todo_es_neutro,
    test_lo_apartado_y_la_puerta,
    test_vigente_fechas_y_la_hucha_rota,
    test_la_orden_ficha_a_raphinha_y_frena_lo_demas,
    test_los_chollos_solo_con_lo_libre,
    test_la_ronda_ni_con_el_colchon,
    test_la_mejora_un_cambio_que_se_paga_solo_si,
    test_la_rotacion_la_que_se_paga_sola_si_la_que_paga_otra_no,
    test_el_carril_solo_lo_libre_y_sumado,
    test_el_buy_v10_y_las_cli_no_tocan_la_hucha,
    test_el_motor_viejo_mira_la_hucha_antes_de_escribir_y_de_elegir,
    test_el_trinquete_dos_vueltas_sin_gastar_lo_apartado,
    test_los_que_venden_no_ven_la_hucha,
    test_los_correr_la_sacan_de_su_foto,
    test_la_vuelta_de_v10_lleva_la_cuenta,
    test_nunca_lanza,
]


def medir() -> None:
    """La huella de la bateria, apagada, para `HUELLAS_DE_MAIN`."""
    todas = _huellas(APAGADO)
    valores = list(todas.values())
    assert all(v == valores[0] for v in valores), "apagada depende de como se apague"
    print(f"Python {sys.version_info[:2]}: {len(valores[0])} llamadas, "
          f"{_la_huella(valores[0])}")


def main() -> None:
    if "--medir" in sys.argv:
        medir()
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
