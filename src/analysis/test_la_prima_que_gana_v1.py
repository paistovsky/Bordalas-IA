"""
LA PRIMA QUE GANA (03/11/2026). Guardias de `BORDALAS_LA_PRIMA_QUE_GANA`
(`src/actions/la_mejora_del_once.py`).

EL CASO (laboratorio del 02/11 22:30 y la puja por Adrian Nino del 03/11)

    En las 33 subastas disputadas del Computer que ganaron los rivales en
    30 dias, el ganador pago una prima mediana de +11,5 % sobre lo que
    pedia el Computer (p75 +18,3 %): +14,2 % por los titulares que suben
    de 1 a 3 M, +10,1 % de 3 a 8 M, +16 % por encima de 8 M. Contra los
    que suben fuerte, ganar cuesta: +10 % gana el 31 %, +12 % el 46 %,
    +14 % el 54 %, +18 % el 62 %. La mejora pujaba +1 % (o lo que pide
    en 9.900 por el que no sube) y de nuestras 7 disputadas perdidas, con
    +12 % habriamos ganado 6. El 03/11 la mejora pujo 4.429.900 (+1,1 %)
    por Adrian Nino (4.380.000, +170.000 al dia) para que saliera Boye; el
    gestor la retiro y la orden puja 4.909.900 (+12,1 %).

QUE SE COMPRUEBA

    1. Nace apagada, se lee en UN sitio (al llamarse), tiene frase en
       QUE_HACE y no hace nada al importarse.
    2. Apagada es main byte a byte: la huella de la bateria (la
       combinacion, `decidir` y `correr` con el escritor de mentira, sobre
       estados compactados de los artefactos de hoy, con relojes a mas y
       a menos de 64 h, los que suben y los que no, de menos de 1 M, de
       1 a 3 M, de 3 a 8 M y de mas de 8 M), con el interruptor sin poner,
       "0" y "", con lo minimo de la mejora y con los 26 interruptores del
       YAML de produccion, es la de main medida ANTES de tocar el codigo,
       en 3.11 y en 3.13.
    3. La puja: `en_9900(precio x 1,12)`, `en_9900(precio x 1,18)` si el
       cambio suma 1 punto por jornada o mas; nunca por debajo de lo que
       pide ni de la puja de siempre; solo de 1 a 8 M (los dos bordes
       dentro).
    4. Solo por el del Computer que SUBE hoy (o del que no se sabe), a 64 h
       o mas de la jornada. El que no sube, el de menos de 1 M, el de mas
       de 8 M, lo que ya es nuestro y a menos de 64 h: lo de siempre.
    5. La caja: la del cambio, la combinacion, la `caja_despues`, el
       importe del PUJAR, el libro y el plan cuentan la puja de verdad.
       Con la prima, ganado el cambio, la caja de la jornada tiene que
       quedar >= 0 (lo peor del resto de la combinacion: los que dan caja,
       perdidos); si no, ese cambio puja lo de siempre y la combinacion
       no pierde ningun cambio. Ni por encima de `maximumBid` disponible
       (ya sin las pujas vivas) ni de lo libre de la hucha.
    6. Con LA PUJA FUERTE puesta, manda la prima donde toca; donde no,
       la puja fuerte como siempre.
    7. LA HUCHA: el dia de su jugador, ni prima. El deficit y el colchon,
       como siempre.
    8. Nunca lanza.
    9. El entorno no la decide (doctrina 104).

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui: la plantilla, el mercado del Computer y las ofertas
    del 03/11 (status.json de las runs 41588746048, 07:15, y 41608412779,
    10:07), compactados. Siete del Computer son de la prueba (ids 9000xx),
    para tener cada tramo con uno que sube y uno que mejora el once. Ni
    `data/`, ni la red, ni el reloj: la hora se pasa (`ahora`) y las horas
    a la jornada tambien.

COMO SE USA

    python -m src.analysis.test_la_prima_que_gana_v1
    python -m src.analysis.test_la_prima_que_gana_v1 --medir
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


ENV = "BORDALAS_LA_PRIMA_QUE_GANA"

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


# ============================================================
# LOS ESTADOS DE HOY, COMPACTADOS
# ============================================================

YO = 14175949
ADRIAN = 35706
BOYE = 12494
GULACSI = 38433
GAYA = 1844
CARDONA = 30493
ORTIZ = 35765

_UTC = timezone.utc

# (id, nombre, posicion, precio, sube hoy, estado, titularidad, puntos,
#  jugados, tasa, equipo): la plantilla de las 07:15 (catalogo, panel).
PLANTILLA = (
    (38433, "Gulacsi", 1, 2260000, -30000, "ok", 90.0, 31, 7, 4.43, 19),
    (23840, "Juan Iglesias", 2, 3790000, 20000, "ok", 90.0, 56, 11, 5.09, 17),
    (28115, "Kike Salas", 2, 3420000, 60000, "ok", 90.0, 47, 9, 5.22, 17),
    (1760, "Chust", 2, 2640000, 80000, "ok", 90.0, 48, 11, 4.36, 75),
    (1844, "Gaya", 2, 1770000, 10000, "ok", 90.0, 33, 9, 3.67, 18),
    (29661, "Olasagasti", 3, 2860000, -10000, "ok", 80.0, 54, 11, 4.91, 10),
    (12403, "Ivan Martin", 3, 2730000, -30000, "ok", 80.0, 42, 9, 4.67, 812),
    (41418, "Dani Lorenzo", 3, 2010000, 0, "ok", 70.0, 39, 10, 3.9, 65),
    (26271, "Yamal", 4, 25450000, 90000, "ok", 95.0, 131, 11, 11.91, 3),
    (35678, "Roberto Fernandez", 4, 7070000, -90000, "ok", 90.0, 69, 11, 6.27, 7),
    (12494, "Boye", 4, 5440000, -40000, "ok", 90.0, 63, 10, 6.3, 91),
    (30493, "Sergi Cardona", 2, 2160000, 30000, "ok", 50.0, 25, 7, 3.57, 19),
    (35765, "Angel Ortiz", 2, 190000, 0, "ok", 30.0, 17, 5, 3.4, 87),
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

# Los de la prueba (ids 9000xx): un tramo cada uno, para que haya un
# cambio que mejora en cada uno. `None` en la subida: no se sabe.
EXTRA = (
    (900001, "Caro que sube", 4, 9200000, 160000, "ok", 90.0, 70, 10, 7.0, 3),
    (900002, "Sin dato de subida", 3, 2900000, None, "ok", 85.0, 52, 10, 5.2, 12),
    (900003, "Barato que sube", 3, 820000, 30000, "ok", 80.0, 48, 10, 4.8, 15),
    (900004, "Medio que sube", 3, 2450000, 70000, "ok", 85.0, 55, 10, 5.5, 13),
    (900005, "Medio que baja", 3, 2600000, -40000, "ok", 85.0, 55, 10, 5.5, 14),
    (900006, "Justo 8 M", 2, 8000000, 120000, "ok", 90.0, 60, 11, 5.6, 2),
    (900007, "Justo 1 M", 2, 1000000, 20000, "ok", 85.0, 48, 10, 4.8, 6),
)

# Las ofertas del Computer por los nuestros (status.json).
OFERTAS_0715 = {
    35678: 7474000, 1844: 1782000, 35765: 191400, 29661: 2735700, 1760: 2576600,
    38433: 2314000, 30493: 2138600, 12494: 5414700, 41411: 449500,
}
OFERTAS_1007 = {k: v for k, v in OFERTAS_0715.items() if k not in (1844, 35765)}

# Lo que tenemos publicado (lo que pedimos).
EN_VENTA = {35678: 10200000, 29661: 3470000, 30493: 2100000, 38433: 2980000,
            41411: 410000, 12494: 6450000}

ONCE_0715 = (38433, 23840, 28115, 1760, 1844, 29661, 12403, 41418, 26271, 35678, 12494)
ONCE_1007 = (38433, 23840, 28115, 1760, 29661, 12403, 41418, 41411, 26271, 35678, 12494)

# Los estados: el de las 07:15 (antes de la mejora: la ronda acaba de
# cobrar a Ortiz y Gaya sale por un cambio vivo cuyo relevo ya esta), el
# de las 10:07 (Gaya y Ortiz vendidos, ninguna puja viva) y el de las
# 11:07 (la orden puja 4.909.900 por Adrian).
ESTADOS = (
    {"nombre": "0715", "plantilla": tuple(f[0] for f in PLANTILLA), "once": ONCE_0715,
     "saldo": -2137676, "maximo": 13417324, "ofertas": OFERTAS_0715, "pujas": {},
     "libro": {str(CARDONA): {"sale": GAYA, "suelo": 1593000, "puja": 2179900,
                              "puntos": 0.55}},
     "ronda": {str(ORTIZ): 219900}, "cobros": {ORTIZ: 191400}},
    {"nombre": "1007",
     "plantilla": tuple(f[0] for f in PLANTILLA if f[0] not in (GAYA, ORTIZ)),
     "once": ONCE_1007, "saldo": -164276, "maximo": 14900724, "ofertas": OFERTAS_1007,
     "pujas": {}, "libro": {}, "ronda": {}, "cobros": {}},
    {"nombre": "1107",
     "plantilla": tuple(f[0] for f in PLANTILLA if f[0] not in (GAYA, ORTIZ)),
     "once": ONCE_1007, "saldo": -164276, "maximo": 9990824, "ofertas": OFERTAS_1007,
     "pujas": {ADRIAN: 4909900}, "libro": {}, "ronda": {}, "cobros": {}},
)

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


def _los_del_computer(cambiados=None, mercado=None) -> list:
    """El Computer y los de la prueba; `cambiados` {id: {campo: valor}};
    `mercado`, si se da, solo esos ids."""
    salida = []
    for f in COMPUTER + EXTRA:
        if mercado is not None and f[0] not in mercado:
            continue
        f = list(f)
        for campo, valor in ((cambiados or {}).get(f[0]) or {}).items():
            f[_CAMPOS.index(campo)] = valor
        salida.append(tuple(f))
    return salida


_CAMPOS = ("id", "nombre", "pos", "precio", "sube", "estado", "prob", "puntos", "jugados",
           "tasa", "equipo")


def _la_foto(e, cambiados=None, mercado=None) -> dict:
    """La foto de Biwenger (la de `refresh_snapshot`) de un estado."""
    computer = _los_del_computer(cambiados, mercado)
    ventas = [{"player": {"id": f[0]}, "price": f[3], "user": None} for f in computer]
    ventas += [{"player": {"id": pid}, "price": precio, "user": {"id": YO}}
               for pid, precio in sorted(EN_VENTA.items()) if pid in e["plantilla"]]
    ofertas = []
    for i, (pid, importe) in enumerate(sorted(e["pujas"].items())):
        ofertas.append({"id": 9000 + i, "amount": importe, "status": "waiting",
                        "requestedPlayers": [{"id": pid}], "from": {"id": YO}})
    for i, (pid, importe) in enumerate(sorted(e["ofertas"].items())):
        ofertas.append({"id": 8000 + i, "amount": importe, "status": "waiting",
                        "requestedPlayers": [{"id": pid}], "from": None})
    plantilla = [f for f in PLANTILLA if f[0] in e["plantilla"]]
    return {
        "timestamp": "2026-11-03T06:15:00+00:00",
        "league": {"id": 1, "user": {"id": YO, "name": "Pepe"}},
        "market": {"sales": ventas, "offers": ofertas,
                   "status": {"balance": e["saldo"], "maximumBid": e["maximo"]}},
        "my_team": [{"id": f[0], "price": f[3]} for f in plantilla],
        "catalog": {"data": {"players": {str(f[0]): _ficha(f)
                                         for f in plantilla + computer}}},
        "_estado": e["nombre"],
    }


def _el_status(e, cambiados=None, mercado=None) -> dict:
    """Lo que la mejora lee del panel: el once, toda la liga, el
    escaparate y la plantilla entera."""
    computer = _los_del_computer(cambiados, mercado)
    plantilla = [f for f in PLANTILLA if f[0] in e["plantilla"]]
    liga = []
    for de_quien, filas in (("nuestro", plantilla), ("computer", computer)):
        for f in filas:
            pid, nombre, pos, precio, sube, estado, prob, puntos, jugados, tasa, equipo = f
            liga.append({
                "id": pid, "name": nombre, "position": pos, "price": precio,
                "price_increment": sube, "status": estado, "points": puntos,
                "played": jugados, "tasa": tasa, "team_id": equipo,
                "de_quien": de_quien, "starter_probability": prob,
            })
    once = [{"id": f[0], "name": f[1], "position": f[2], "starter_probability": f[6],
             "price": f[3]} for f in plantilla if f[0] in e["once"]]
    escaparate = [{"id": f[0], "name": f[1], "position": f[2], "price": f[3],
                   "points": f[7], "played": f[8], "starter_probability": f[6]}
                  for f in computer]
    return {
        "todaLaLiga": {"players": liga},
        "lineup": {"players": once},
        "libro_del_escaparate": {"players": escaparate},
        "roster": {"players": [{"id": f[0], "name": f[1], "starter_probability": f[6]}
                               for f in plantilla]},
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


def _la_vuelta(e, ahora) -> dict:
    """El estado de la vuelta de v10 de ESTA vuelta (cinco minutos antes):
    lo que la ronda cobro."""
    if not e["cobros"]:
        return {}
    return {"timestamp": (ahora - timedelta(minutes=5)).isoformat(),
            "ronda": {"hechas": [{"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                                  "importe": importe, "exito": True}
                                 for pid, importe in sorted(e["cobros"].items())]}}


def _correr(e, ahora, horas, carpeta, *, cambiados=None, v10=None, orden=None,
            nombre="prueba", mercado=None, protegidos=frozenset()):
    """`correr` de la mejora con el escritor de mentira: libros en la
    carpeta, sin leer nada de produccion. {r, escritor, libro, vuelta}."""
    from src.actions import la_mejora_del_once as mejora

    carpeta = Path(carpeta) / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    libro = carpeta / "la_mejora.json"
    libro.write_text(json.dumps(e["libro"]), encoding="utf-8")
    ronda = carpeta / "ronda.json"
    ronda.write_text(json.dumps(e["ronda"]), encoding="utf-8")
    chollos = carpeta / "chollos.json"
    chollos.write_text("{}", encoding="utf-8")
    escritor = _Escritor()
    r = mejora.correr(
        status=_el_status(e, cambiados, mercado), snapshot=_la_foto(e, cambiados, mercado),
        v10=_la_vuelta(e, ahora) if v10 is None else v10,
        escritor_factory=lambda: escritor, ahora=ahora, libro_ruta=libro,
        calendario=_el_calendario(),
        de_fuera={"orden": orden or {}, "vetados": set(), "protegidos": set(protegidos),
                  "libro_ronda": ronda, "libro_chollos": chollos,
                  "horas_jornada": horas, "puede_escribir": True, "en_curso": False,
                  "rotando": set(), "de_otra_jornada": set(), "avisos_de_ff": []})
    vuelta = carpeta / "la_mejora_vuelta.json"
    return {"r": r, "escritor": escritor.llamadas,
            "libro": json.loads(libro.read_text(encoding="utf-8")),
            "vuelta": (json.loads(vuelta.read_text(encoding="utf-8"))
                       if vuelta.exists() else None)}


def _decidir_de(e, *, caja, horas, cambiados=None, mercado=None, **kw):
    """`decidir` de la mejora sobre un estado, como lo llama `correr` (sin
    la parte de `correr` que lee libros): la caja y las horas, dadas."""
    from src.actions import la_mejora_del_once as mejora
    from src.actions.la_orden_del_gestor import leer_la_foto

    status = _el_status(e, cambiados, mercado)
    liga = {p["id"]: p for p in status["todaLaLiga"]["players"]}
    foto = leer_la_foto(_la_foto(e, cambiados, mercado), YO)
    args = dict(
        once=status["lineup"]["players"], liga=liga,
        escaparate=status["libro_del_escaparate"]["players"], foto=foto,
        libro=copy.deepcopy(e["libro"]),
        inventario={int(k) for k in e["ronda"] if int(k) in e["plantilla"]} - set(e["cobros"]),
        pendientes=set(e["cobros"]), intocables=frozenset({"yamal", "lamine yamal"}),
        protegidos=set(), ya_pujados=set(), caja=caja, horas_jornada=horas,
        puede_escribir=True, en_curso=False,
        probabilidades={f[0]: f[6] for f in PLANTILLA if f[0] in e["plantilla"]},
        estados={p["id"]: p["status"] for p in status["todaLaLiga"]["players"]},
        vendidos=set(e["cobros"]),
    )
    args.update(kw)
    return mejora.decidir(**args)


# ============================================================
# LA BATERIA DE APAGADO (medida en main ANTES de tocar el codigo)
# ============================================================
#
#     Todo con la firma de main (sin el argumento nuevo de `decidir`).

# Las horas a la jornada: el paron (J13), las 07:15 y las 10:07 del
# martes (J12, vie 21:00), el borde de las 64 h y por debajo, y fuera de
# la ventana de comprar (< 40 h).
HORAS = (227.0, 85.75, 64.0, 63.9, 30.0)

# Las cajas de la jornada: la de las 07:15, la de las 10:07, una con
# premio, una holgada y una en rojo de verdad (el deficit).
CAJAS = (-264776, -164276, 2500000, 9000000, -2000000)

# (solo_si_sube, en_9900, a_la_salida, puja_fuerte): produccion primero.
BANDERAS = (
    (True, True, False, False),
    (False, True, False, False),
    (False, False, False, False),
    (False, True, True, False),
    (False, True, False, True),
    (True, True, True, True),
)

HUCHAS = (
    None,
    {"activa": True, "apartado": 2000000, "libre": 500000},
    {"activa": True, "apartado": 0, "libre": -300000},
    {"activa": True, "apartado": 0, "libre": 0, "en_juego": True},
)

# Los cambios de la combinacion: los de la vuelta de las 07:15 y los de
# los tramos (la caja con el +1 % en 9.900).
CAMBIOS = (
    [
        {"entra": ADRIAN, "sale": BOYE, "puntos": 0.61, "caja": 738100, "puja": 4429900,
         "ya_es_nuestro": False, "suelo": 4896000},
        {"entra": 38290, "sale": 1760, "puntos": 0.33, "caja": -1878100, "puja": 4389900,
         "ya_es_nuestro": False, "suelo": 2376000},
        {"entra": 17021, "sale": GULACSI, "puntos": 1.05, "caja": -2032900, "puja": 4179900,
         "ya_es_nuestro": False, "suelo": 2034000},
    ],
    [
        {"entra": 900004, "sale": 41418, "puntos": 1.95, "caja": -569900, "puja": 2479900,
         "ya_es_nuestro": False, "suelo": 1809000},
        {"entra": 900003, "sale": 12403, "puntos": 0.34, "caja": 1763600, "puja": 829900,
         "ya_es_nuestro": False, "suelo": 2457000},
        {"entra": 900001, "sale": 35678, "puntos": 0.66, "caja": -2585400, "puja": 9299900,
         "ya_es_nuestro": False, "suelo": 6363000},
        {"entra": 900006, "sale": GAYA, "puntos": 1.74, "caja": -6406400, "puja": 8089900,
         "ya_es_nuestro": False, "suelo": 1593000},
        {"entra": 900007, "sale": 1760, "puntos": 0.16, "caja": 1498100, "puja": 1009900,
         "ya_es_nuestro": False, "suelo": 2376000},
    ],
    [
        {"entra": 900002, "sale": 29661, "puntos": 0.49, "caja": -212900, "puja": 2929900,
         "ya_es_nuestro": False, "suelo": 2574000},
        {"entra": ORTIZ, "sale": 41411, "puntos": 0.54, "caja": 228000, "puja": 0,
         "ya_es_nuestro": True, "suelo": 387000},
        {"entra": 900004, "sale": 12403, "puntos": 0.94, "caja": 113600, "puja": 2479900,
         "ya_es_nuestro": False, "suelo": 2457000},
        {"entra": 900005, "sale": 41418, "puntos": 1.95, "caja": -719900, "puja": 2629900,
         "ya_es_nuestro": False, "suelo": 1809000},
    ],
)

# Lo minimo para que la mejora corra (lo que mira de los suyos) y los 26
# del YAML de produccion del 03/11 (.github/workflows/bordalas-live.yml).
ENTORNO_MINIMO = {
    "BORDALAS_LA_MEJORA_DEL_ONCE": "1",
    "BORDALAS_LA_MEJORA_SOLO_SI_SUBE": "1",
    "BORDALAS_LA_PUJA_EN_9900": "1",
}
PRODUCCION = {n: "1" for n in (
    "BORDALAS_COBRA_LA_RACHA", "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA", "BORDALAS_EL_CIERRE_DE_LA_JORNADA",
    "BORDALAS_EL_INFORME_DE_LA_MANANA", "BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE",
    "BORDALAS_EL_ONCE_UNA_VEZ", "BORDALAS_JORNADAS_POR_SU_FECHA", "BORDALAS_LA_CARTERA",
    "BORDALAS_LA_JORNADA_DE_CADA_PAGINA", "BORDALAS_LA_MEJORA_DEL_ONCE",
    "BORDALAS_LA_MEJORA_SOLO_SI_SUBE", "BORDALAS_LA_MONEDA_DE_LA_LIGA",
    "BORDALAS_LA_ORDEN_DEL_GESTOR", "BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO",
    "BORDALAS_LA_PUJA_EN_9900", "BORDALAS_LA_RONDA_DE_LA_MANANA", "BORDALAS_LA_ROTACION",
    "BORDALAS_LOS_CHOLLOS", "BORDALAS_REJA_CON_TOLERANCIA", "BORDALAS_REVENTA_SOLO_SI_JUEGA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL", "BORDALAS_REVISA_LAS_PUJAS_VIVAS",
    "BORDALAS_SIN_SUBASTA", "BORDALAS_SOLVENCIA_POR_SU_PLAZO", "BORDALAS_UN_SOLO_COLCHON",
)}
ENTORNOS = (("minimo", ENTORNO_MINIMO), ("produccion", PRODUCCION))

APAGADO = (None, "0", "")

# Los relojes de `correr`: martes 07:15 y 10:07, jueves 05:50 y el paron.
RELOJES = (
    datetime(2026, 11, 3, 6, 15, tzinfo=_UTC),
    datetime(2026, 11, 3, 9, 7, tzinfo=_UTC),
    datetime(2026, 11, 5, 4, 50, tzinfo=_UTC),
    datetime(2026, 11, 11, 5, 50, tzinfo=_UTC),
)


def _la_bateria(carpeta) -> list:
    """[(nombre, llamada)] de la mejora, con la firma de main."""

    from src.actions import la_mejora_del_once as mejora

    llamadas = []

    # 1. LA COMBINACION.
    for i, cambios in enumerate(CAMBIOS):
        for caja in (-264776, -164276, 0, 1500000, 9000000):
            for minimo in (-1000000, 0):
                for disponible in (3000000, 13900724):
                    for deficit in (False, True):
                        for libre in (None, 400000):
                            kw = {} if libre is None else {"libre": libre}
                            llamadas.append((
                                f"combinacion/{i}/{caja}/{minimo}/{disponible}/{deficit}/{libre}",
                                lambda cambios=cambios, caja=caja, minimo=minimo,
                                disponible=disponible, deficit=deficit, kw=kw:
                                mejora.la_mejor_combinacion(copy.deepcopy(cambios), caja,
                                                            minimo, disponible,
                                                            deficit=deficit, **kw)))

    # 2. DECIDIR: cada estado, cada reloj, cada caja y cada combinacion de
    # interruptores de la mejora; la hucha, en produccion y sin hucha.
    for e in ESTADOS:
        for horas in HORAS:
            for caja in CAJAS:
                for banderas in BANDERAS:
                    huchas = HUCHAS if banderas in BANDERAS[:2] else HUCHAS[:1]
                    for h, hucha in enumerate(huchas):
                        solo_si_sube, en_9900, a_la_salida, puja_fuerte = banderas
                        kw = {} if hucha is None else {"hucha": hucha}
                        llamadas.append((
                            f"decidir/{e['nombre']}/{horas}/{caja}/{banderas}/{h}",
                            lambda e=e, horas=horas, caja=caja, solo_si_sube=solo_si_sube,
                            en_9900=en_9900, a_la_salida=a_la_salida,
                            puja_fuerte=puja_fuerte, kw=kw:
                            _decidir_de(e, caja=caja, horas=horas, solo_si_sube=solo_si_sube,
                                        en_9900=en_9900, a_la_salida=a_la_salida,
                                        puja_fuerte=puja_fuerte, **copy.deepcopy(kw))))

    # 3. CORRER, con el escritor de mentira: cada estado, cada reloj y las
    # horas a mas y a menos de 64.
    for e in ESTADOS:
        for ahora in RELOJES:
            for horas in (227.0, 85.75, 64.0, 63.9, 45.0):
                nombre = f"{e['nombre']}_{ahora.strftime('%d%H%M')}_{horas}"
                llamadas.append((
                    f"correr/{e['nombre']}/{ahora.isoformat()}/{horas}",
                    lambda e=e, ahora=ahora, horas=horas, nombre=nombre:
                    _correr(e, ahora, horas, carpeta, nombre=nombre)))
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


# Medidas en main (2e52c95d, antes de tocar el codigo) con
# `python -m src.analysis.test_la_prima_que_gana_v1 --medir`, una por
# Python y por entorno (lo minimo de la mejora y los 26 de produccion).
HUELLAS_DE_MAIN = {
    (3, 11): {
        "minimo": "5d61cdb27128a5b863181b2d62a53bc65ee907be3c74d35a3f5c70666baeb289",
        "produccion": "432ee558dff765838b65653eabb2177dfe0f00dadc706520ef015f8b08458b71",
    },
    (3, 13): {
        "minimo": "5d61cdb27128a5b863181b2d62a53bc65ee907be3c74d35a3f5c70666baeb289",
        "produccion": "432ee558dff765838b65653eabb2177dfe0f00dadc706520ef015f8b08458b71",
    },
}
LLAMADAS_DE_LA_BATERIA = 1200


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


# ============================================================
# LAS PRUEBAS
# ============================================================

# Los 20 de verdad del Computer (sin los de la prueba).
REALES = tuple(f[0] for f in COMPUTER)
ROBERTO = 35678
UNAI_SIMON = 17021
# La vara de las 07:15 era la del calendario: Adrian por Boye +0,61 por
# jornada (xP 5,47 por 4,87). Con el `esperado` de la prueba, la misma
# diferencia: tasa 7,85 x 80 % - 6,30 x 90 % = +0,61.
CON_EL_CALENDARIO = {ADRIAN: {"tasa": 7.85}}
# Roberto no se vende (la orden del dueno del 02/11 16:30): el cambio de
# Adrian es por Boye, como en la vuelta de las 07:15.
SIN_ROBERTO = frozenset({ROBERTO})
PRODUCCION_DE_LA_MEJORA = {"solo_si_sube": True, "en_9900": True}
E0715, E1007, E1107 = ESTADOS


def _el_de(d, pid):
    """El cambio elegido de `pid` en el plan de `decidir`."""
    for c in d["plan"]["cambios"]:
        if c["entra"] == pid:
            return c
    raise AssertionError(f"{pid} no esta entre los elegidos: {d['plan']['cambios']}")


def _la_puja(d, pid):
    pujas = [a["importe"] for a in d["acciones"]
             if a["accion"] == "PUJAR" and a["player_id"] == pid]
    assert len(pujas) == 1, d["acciones"]
    return pujas[0]


def _adrian(caja, horas=84.0, *, prima=True, estado=None, **kw):
    """La mejora de las 10:07 (o `estado`) con Adrian en el mercado del
    Computer (los 20 de verdad), Roberto protegido."""
    args = {**PRODUCCION_DE_LA_MEJORA, "protegidos": set(SIN_ROBERTO),
            "cambiados": CON_EL_CALENDARIO, "mercado": REALES}
    args.update(kw)
    return _decidir_de(estado or E1007, caja=caja, horas=horas, prima_que_gana=prima, **args)


# 1. NACE APAGADA, UN LECTOR, SU FRASE, NADA AL IMPORTARSE

def test_nace_apagada_un_lector_y_su_frase():
    import ast
    from src.actions import la_mejora_del_once as mejora
    from src.telemetry.el_tablon import QUE_HACE

    assert mejora.ENV_LA_PRIMA_QUE_GANA == ENV
    for valor in (None, "0", "", "no", "false", "2"):
        with _Interruptores({ENV: valor}):
            assert mejora.la_prima_que_gana_activa() is False, repr(valor)
    for valor in ("1", "true", "si", "yes", " SI "):
        with _Interruptores({ENV: valor}):
            assert mejora.la_prima_que_gana_activa() is True, repr(valor)

    # Un solo sitio la lee: `la_prima_que_gana_activa`, llamada solo
    # desde `correr`. Fuera de la mejora, solo la frase del tablon.
    nombran = []
    for ruta in sorted((RAIZ / "src").rglob("*.py")):
        if ruta.name.startswith("test_"):
            continue
        if ENV in ruta.read_text(encoding="utf-8"):
            nombran.append(ruta.relative_to(RAIZ).as_posix())
    assert nombran == ["src/actions/la_mejora_del_once.py", "src/telemetry/el_tablon.py"], \
        nombran
    fuente = (RAIZ / "src" / "actions" / "la_mejora_del_once.py").read_text(encoding="utf-8")
    assert fuente.count(f'ENV_LA_PRIMA_QUE_GANA = "{ENV}"') == 1
    assert fuente.count("ENV_LA_PRIMA_QUE_GANA") == 2         # el nombre y su lector
    assert fuente.count("os.environ.get(ENV_LA_PRIMA_QUE_GANA") == 1
    assert (fuente.count("la_prima_que_gana_activa()")
            - fuente.count("def la_prima_que_gana_activa()")) == 1      # en `correr`

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
        assert "la_prima_que_gana_activa" not in texto and "environ" not in texto, \
            ast.unparse(nodo)[:120]

    frase = str(QUE_HACE.get(ENV) or "")
    assert "12 %" in frase and "18 %" in frase and "64 h" in frase, frase
    assert "positivo" in frase and "puja fuerte" in frase, frase


# 2. APAGADA ES MAIN BYTE A BYTE

def test_apagada_es_main_byte_a_byte():
    """La bateria (1.200 llamadas por entorno), con el interruptor sin
    poner, "0" y "", con lo minimo de la mejora y con los 26 de
    produccion: la huella de main, medida antes de tocar el codigo."""
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


# 3. LA PUJA

def test_la_puja_de_la_prima():
    from src.actions import la_mejora_del_once as mejora

    f = mejora.la_puja_de_la_prima
    # Adrian Nino: 4.380.000 x 1,12 = 4.905.600 -> 4.909.900 (+12,1 %).
    assert f(4_380_000, 0.61) == 4_909_900
    # Un punto o mas por jornada: x 1,18. Justo 1,0 ya es; 0,99 no.
    assert f(4_380_000, 1.0) == 5_169_900
    assert f(4_380_000, 0.99) == 4_909_900
    assert f(4_130_000, 1.05) == 4_879_900          # Unai Simon, +18,2 %
    # Los bordes, dentro: 1 M y 8 M. Fuera, None (lo de siempre).
    assert f(1_000_000, 0.6) == 1_129_900
    assert f(8_000_000, 0.6) == 8_969_900
    assert f(999_999, 0.6) is None and f(8_000_001, 0.6) is None
    assert f(790_000, 2.0) is None and f(9_200_000, 2.0) is None
    # En enteros: 2.767.768 x 1,12 = 3.099.900,16, que no cabe en
    # 3.099.900: el primer ...9.900 que no baja de ahi es 3.109.900.
    assert f(2_767_768, 0.6) == 3_109_900
    assert f(2_767_767, 0.6) == 3_099_900
    # Nunca por debajo de la de siempre.
    assert f(2_000_000, 0.6, de_siempre=2_500_000) == 2_500_000
    assert f(2_000_000, 0.6, de_siempre=2_009_900) == 2_249_900
    # Con basura: None; puntos basura, el 12 %.
    for basura in (None, "x", True, [], {}):
        assert f(basura, 1.0) is None, basura
    assert f(4_380_000, "x") == 4_909_900 and f(4_380_000, None) == 4_909_900


# 4. A QUIEN LE TOCA

def test_solo_el_que_sube_de_1_a_8_m_a_64_h_o_mas():
    from src.actions import la_mejora_del_once as mejora

    cambio = {"entra": 900002, "sale": 41418, "puntos": 0.7, "caja": -500_000,
              "puja": 2_929_900, "suelo": 1_809_000, "ya_es_nuestro": False}
    c = mejora.con_la_prima
    # El que no se sabe si sube (sin dato o con basura): toca.
    for ficha in ({}, None, {"price_increment": None}, {"price_increment": "x"},
                  {"price_increment": 10_000}, {"priceIncrement": 50_000}):
        otra = c(cambio, 2_900_000, ficha, 85.75)
        assert otra is not None and otra["puja"] == 3_249_900, (ficha, otra)
        assert otra["caja"] == -500_000 - (3_249_900 - 2_929_900), otra
        assert otra["prima_que_gana"] == 0.1207 and otra["puja_de_siempre"] == 2_929_900
    # El que no sube (sabido y <= 0): nunca.
    for ficha in ({"price_increment": 0}, {"price_increment": -40_000},
                  {"priceIncrement": -10_000}):
        assert c(cambio, 2_900_000, ficha, 85.75) is None, ficha
    # Fuera de 1 a 8 M, nunca.
    for precio in (999_999, 820_000, 8_000_001, 9_200_000):
        assert c(cambio, precio, {"price_increment": 30_000}, 85.75) is None, precio
    # A menos de 64 h (o sin saberlo), nunca; a 64 h justas, si.
    for horas in (63.9, 40.0, None, float("nan"), "x"):
        assert c(cambio, 2_900_000, {}, horas) is None, horas
    assert c(cambio, 2_900_000, {}, 64.0) is not None
    assert c(cambio, 2_900_000, {}, 227.0) is not None
    # Lo que ya es nuestro, nunca (no puja).
    assert c({**cambio, "ya_es_nuestro": True, "puja": 0}, 2_900_000, {}, 85.75) is None
    # Una puja de siempre que ya llega: nada que subir.
    assert c({**cambio, "puja": 3_300_000}, 2_900_000, {}, 85.75) is None


def test_los_demas_como_siempre():
    """En `decidir`, con los de la prueba de cada tramo: el de mas de 8 M,
    el de menos de 1 M y el que no sube pujan lo mismo que apagada; el que
    no se sabe si sube, con la prima. Los mismos cambios."""
    tramos = (900001, 900003, 900005, 900002)
    estado = dict(E1007, maximo=40_000_000)
    kw = dict(caja=12_000_000, horas=85.75, mercado=tramos, solo_si_sube=False, en_9900=True)
    apagada = _decidir_de(estado, prima_que_gana=False, **kw)
    encendida = _decidir_de(estado, prima_que_gana=True, **kw)
    assert ({(c["entra"], c["sale"]) for c in apagada["plan"]["cambios"]}
            == {(c["entra"], c["sale"]) for c in encendida["plan"]["cambios"]})
    for pid in (900001, 900005):
        assert _la_puja(apagada, pid) == _la_puja(encendida, pid), pid
    assert _la_puja(apagada, 900002) == 2_929_900
    assert _la_puja(encendida, 900002) == 3_429_900        # 1,69 pts: x 1,18
    assert encendida["plan"]["prima_que_gana"] == {900002: 0.1827}
    # El de menos de 1 M (Ramon sale por el), solo: lo mismo.
    kw = dict(caja=-164_276, horas=85.75, mercado=(900003,), solo_si_sube=False,
              en_9900=True)
    a, e = (_decidir_de(E1007, prima_que_gana=x, **kw) for x in (False, True))
    assert _la_puja(a, 900003) == _la_puja(e, 900003) == 829_900
    assert e["plan"]["prima_que_gana"] == {} and "prima_que_no_cabe" not in e["plan"]


# 5. ADRIAN NINO: LA CAJA, LA COMBINACION, LA ACCION Y EL PLAN

def test_adrian_nino_con_la_caja_de_las_10():
    """Las 10:07 (caja -164.276, 84 h): 4.909.900 en vez de 4.429.900. La
    caja del cambio (Boye al 95 %: 5.168.000) es 258.100 y la de la
    jornada queda en 93.824."""
    apagada = _adrian(-164_276, prima=False)
    d = _adrian(-164_276)
    assert _la_puja(apagada, ADRIAN) == 4_429_900
    c = _el_de(d, ADRIAN)
    assert c["sale"] == BOYE and c["puntos"] == 0.61, c
    assert c["puja"] == 4_909_900 and c["caja"] == 258_100, c
    assert c["prima_que_gana"] == 0.121 and c["puja_de_siempre"] == 4_429_900, c
    assert d["plan"]["caja_despues"] == -164_276 + 258_100 == 93_824
    assert d["plan"]["prima_que_gana"] == {ADRIAN: 0.121}
    assert "prima_que_no_cabe" not in d["plan"]
    assert [(a["accion"], a["player_id"], a["importe"], a.get("prima_que_gana"))
            for a in d["acciones"]] == [("PUJAR", ADRIAN, 4_909_900, 0.121)]
    # Apagada no lleva nada de la prima.
    assert "prima_que_gana" not in apagada["plan"]
    assert all("prima_que_gana" not in a for a in apagada["acciones"])


def test_adrian_nino_con_la_caja_de_las_07_no_cabe():
    """Las 07:15 (caja -264.776): con la prima la jornada quedaria en
    -6.676. Puja la de siempre, 4.429.900, y el plan lo dice."""
    d = _adrian(-264_776, estado=E0715)
    assert _la_puja(d, ADRIAN) == 4_429_900
    assert d["plan"]["caja_despues"] == -264_776 + 738_100
    assert d["plan"]["prima_que_gana"] == {} and d["plan"]["prima_que_no_cabe"] == [ADRIAN]
    assert d == {**_adrian(-264_776, estado=E0715, prima=False),
                 "plan": d["plan"]} and {
        k: v for k, v in d["plan"].items() if not k.startswith("prima_")} == \
        _adrian(-264_776, estado=E0715, prima=False)["plan"]


def test_la_caja_de_la_jornada_no_baja_de_cero():
    """El borde: con la prima, la jornada en 0 justo vale; un euro menos,
    no (aunque el minimo con deuda sea -1 M)."""
    d = _adrian(-258_100)
    assert _la_puja(d, ADRIAN) == 4_909_900 and d["plan"]["caja_despues"] == 0
    d = _adrian(-258_101)
    assert _la_puja(d, ADRIAN) == 4_429_900 and d["plan"]["minimo"] == -1_000_000
    assert d["plan"]["prima_que_no_cabe"] == [ADRIAN]


def test_un_punto_o_mas_18_y_la_combinacion_cuenta_la_prima():
    """Unai Simon por Gulacsi (+1,05): 4.879.900 (+18,2 %); con Adrian, las
    dos primas caben con 3 M de caja (la jornada queda en 525.200)."""
    d = _decidir_de(E1007, caja=3_000_000, horas=84.0, mercado=(UNAI_SIMON,),
                    protegidos=set(SIN_ROBERTO), prima_que_gana=True,
                    **PRODUCCION_DE_LA_MEJORA)
    c = _el_de(d, UNAI_SIMON)
    assert c["puja"] == 4_879_900 and c["caja"] == 2_147_000 - 4_879_900, c
    assert d["plan"]["caja_despues"] == 3_000_000 - 2_732_900 == 267_100
    d = _adrian(3_000_000)
    assert _la_puja(d, ADRIAN) == 4_909_900 and _la_puja(d, UNAI_SIMON) == 4_879_900
    assert d["plan"]["caja_despues"] == 3_000_000 + 258_100 - 2_732_900 == 525_200
    assert d["plan"]["prima_que_gana"] == {ADRIAN: 0.121, UNAI_SIMON: 0.1816}


def test_la_prima_nunca_hace_perder_un_cambio():
    """Dos cambios que mejoran, cada prima cabe sola pero no las dos: van
    los dos cambios (los mismos puntos que apagada), uno con prima. Y un
    cambio que da caja no paga la prima de otro (el peor caso)."""
    from src.actions import la_mejora_del_once as mejora

    a = {"entra": 1, "sale": 11, "puntos": 1.2, "caja": -400_000, "puja": 2_029_900,
         "ya_es_nuestro": False}
    a2 = {**a, "puja": 2_369_900, "caja": -740_000, "prima_que_gana": 0.1849,
          "puja_de_siempre": 2_029_900}
    b = {"entra": 2, "sale": 12, "puntos": 0.8, "caja": -300_000, "puja": 3_039_900,
         "ya_es_nuestro": False}
    b2 = {**b, "puja": 3_369_900, "caja": -630_000, "prima_que_gana": 0.1233,
          "puja_de_siempre": 3_039_900}
    apagada = mejora.la_mejor_combinacion([a, b], 1_050_000, -1_000_000, 20_000_000)
    elegidos = mejora.la_mejor_combinacion([a, b, a2, b2], 1_050_000, -1_000_000, 20_000_000)
    assert sorted(c["entra"] for c in apagada) == [1, 2]
    assert sorted((c["entra"], c["puja"]) for c in elegidos) == [(1, 2_029_900),
                                                                 (2, 3_369_900)], elegidos
    # Con caja para las dos, las dos.
    elegidos = mejora.la_mejor_combinacion([a, b, a2, b2], 1_400_000, -1_000_000, 20_000_000)
    assert sorted((c["entra"], c["puja"]) for c in elegidos) == [(1, 2_369_900),
                                                                 (2, 3_369_900)], elegidos
    # Sin caja ni para una: las dos de siempre (como apagada).
    elegidos = mejora.la_mejor_combinacion([a, b, a2, b2], 1_000_000, -1_000_000, 20_000_000)
    assert sorted((c["entra"], c["puja"]) for c in elegidos) == [(1, 2_029_900),
                                                                 (2, 3_039_900)], elegidos
    # La puja maxima disponible tambien manda: con 5.400.000 caben las dos
    # de siempre (5.069.800) y una prima, la de B (5.399.800); la de A no
    # (5.409.800).
    elegidos = mejora.la_mejor_combinacion([a, b, a2, b2], 1_400_000, -1_000_000, 5_400_000)
    assert sorted((c["entra"], c["puja"]) for c in elegidos) == [(1, 2_029_900),
                                                                 (2, 3_369_900)], elegidos
    # El que da caja (F, +600.000) no paga la prima de A: ganado A y
    # perdido F, la jornada quedaria en -540.000.
    f = {"entra": 3, "sale": 13, "puntos": 0.9, "caja": 600_000, "puja": 1_019_900,
         "ya_es_nuestro": False}
    elegidos = mejora.la_mejor_combinacion([a, f, a2], 200_000, -1_000_000, 20_000_000)
    assert sorted((c["entra"], c["puja"]) for c in elegidos) == [(1, 2_029_900),
                                                                 (3, 1_019_900)], elegidos
    # Lo que ya es nuestro si cuenta (no depende de ninguna puja).
    g = {**f, "entra": 4, "ya_es_nuestro": True, "puja": 0}
    elegidos = mejora.la_mejor_combinacion([a, g, a2], 200_000, -1_000_000, 20_000_000)
    assert sorted((c["entra"], c["puja"]) for c in elegidos) == [(1, 2_369_900),
                                                                 (4, 0)], elegidos


def test_nunca_por_encima_de_la_puja_maxima_ni_de_lo_libre():
    """Con `maximumBid` 5,5 M (4,5 M disponibles) cabe la de siempre y no
    la prima; con una puja viva de 4.909.900 por otro, lo mismo. Con la
    hucha, lo libre manda igual que apagada."""
    d = _adrian(-164_276, estado=dict(E1007, maximo=5_500_000))
    assert _la_puja(d, ADRIAN) == 4_429_900 and d["plan"]["prima_que_no_cabe"] == [ADRIAN]
    viva = dict(E1007, maximo=10_409_900 - 4_909_900, pujas={UNAI_SIMON: 4_909_900})
    d = _adrian(-164_276, estado=viva)
    assert _la_puja(d, ADRIAN) == 4_429_900 and d["plan"]["prima_que_no_cabe"] == [ADRIAN]
    # Lo libre de la hucha (2,1 M): la de siempre de Unai Simon saca
    # 2.032.900 y cabe; con la prima sacaria 2.732.900.
    kw = dict(caja=3_000_000, horas=84.0, mercado=(UNAI_SIMON,), **PRODUCCION_DE_LA_MEJORA,
              hucha={"activa": True, "apartado": 0, "libre": 2_100_000})
    d = _decidir_de(E1007, prima_que_gana=True, **kw)
    assert _la_puja(d, UNAI_SIMON) == 4_179_900, d["acciones"]
    assert d["plan"]["prima_que_no_cabe"] == [UNAI_SIMON]
    kw["hucha"] = {"activa": True, "apartado": 0, "libre": 2_800_000}
    assert _la_puja(_decidir_de(E1007, prima_que_gana=True, **kw), UNAI_SIMON) == 4_879_900


def test_a_menos_de_64_horas_lo_de_siempre():
    """A 63,9 h, encendida es apagada (mas el plan vacio); a 64 h y en el
    paron, con la prima."""
    for horas in (63.9, 50.0, 40.0):
        a, e = _adrian(2_000_000, horas, prima=False), _adrian(2_000_000, horas)
        assert e["plan"].pop("prima_que_gana") == {} and e == a, horas
    for horas in (64.0, 85.75, 227.0):
        assert _la_puja(_adrian(2_000_000, horas), ADRIAN) == 4_909_900, horas
    # Fuera de la ventana de comprar ni plan.
    assert "prima_que_gana" not in _adrian(2_000_000, 30.0)["plan"]


# 6. LA PUJA FUERTE

def test_manda_sobre_la_puja_fuerte():
    """Con LA PUJA FUERTE: Adrian (+0,61) pujaria 4.531.000 (+3,4 %); con la
    prima, 4.909.900. El de mas de 8 M, la fuerte como siempre. Sin caja
    para la prima, la fuerte."""
    estado = dict(E1007, maximo=40_000_000)
    kw = dict(caja=12_000_000, horas=85.75, cambiados=CON_EL_CALENDARIO,
              mercado=(ADRIAN, 900001), solo_si_sube=False, en_9900=True, puja_fuerte=True)
    a = _decidir_de(estado, prima_que_gana=False, **kw)
    e = _decidir_de(estado, prima_que_gana=True, **kw)
    assert _la_puja(a, ADRIAN) == 4_536_000 and _la_puja(e, ADRIAN) == 4_909_900
    assert _la_puja(a, 900001) == _la_puja(e, 900001) == 9_524_000
    assert "prima" not in _el_de(e, ADRIAN) and _el_de(e, 900001)["prima"] == 0.0352
    a = _adrian(-164_276, prima=False, puja_fuerte=True, solo_si_sube=False)
    e = _adrian(-164_276, puja_fuerte=True, solo_si_sube=False)
    assert _la_puja(a, ADRIAN) == 4_531_000 and _la_puja(e, ADRIAN) == 4_909_900
    e = _adrian(-264_776, estado=E0715, puja_fuerte=True, solo_si_sube=False)
    assert _la_puja(e, ADRIAN) == 4_531_000 and e["plan"]["prima_que_no_cabe"] == [ADRIAN]


# 7. LA HUCHA

def test_el_dia_del_jugador_de_la_hucha_ninguna_prima():
    """El dia de Raphinha, con nuestra puja por el viva y la mejora en
    deficit (vende caro, ficha barato): Adrian por Roberto pagaria la
    prima (la jornada quedaria en +606.600) y no se pone."""
    kw = dict(caja=-1_200_000, horas=84.0, cambiados=CON_EL_CALENDARIO, mercado=(ADRIAN,),
              protegidos={BOYE}, **PRODUCCION_DE_LA_MEJORA)
    sin_hucha = _decidir_de(E1007, prima_que_gana=True, **kw)
    assert _la_puja(sin_hucha, ADRIAN) == 4_909_900 and sin_hucha["plan"]["deficit"]
    hucha = {"activa": True, "apartado": 0, "libre": 0, "en_juego": True,
             "su_puja_viva": True}
    d = _decidir_de(E1007, prima_que_gana=True, hucha=dict(hucha), **kw)
    assert _la_puja(d, ADRIAN) == 4_429_900
    assert d["plan"]["prima_que_gana"] == {} and "prima_que_no_cabe" not in d["plan"]
    assert d == {**_decidir_de(E1007, prima_que_gana=False, hucha=dict(hucha), **kw),
                 "plan": d["plan"]}


# 8. CORRER: LO QUE SE ESCRIBE

def test_correr_puja_y_apunta_la_de_verdad():
    """`correr` encendida a las 10:07: Biwenger recibe 4.909.900, el libro
    y el estado de la vuelta lo apuntan con su prima; apagada, 4.429.900 y
    nada de la prima. A las 07:15, la de siempre y el plan dice por que."""
    ahora = datetime(2026, 11, 3, 9, 7, tzinfo=_UTC)
    salidas = {}
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre, entorno in (("encendida", {**ENTORNO_MINIMO, ENV: "1"}),
                                ("produccion", {**PRODUCCION, ENV: "1"}),
                                ("apagada", {**PRODUCCION, ENV: "0"})):
            with _Interruptores(entorno):
                salidas[nombre] = _correr(E1007, ahora, 84.0, carpeta, nombre=nombre,
                                          cambiados=CON_EL_CALENDARIO, mercado=REALES,
                                          protegidos=SIN_ROBERTO)
        with _Interruptores({**PRODUCCION, ENV: "1"}):
            temprano = _correr(E0715, datetime(2026, 11, 3, 6, 15, tzinfo=_UTC), 85.75,
                               carpeta, nombre="temprano", cambiados=CON_EL_CALENDARIO,
                               mercado=REALES, protegidos=SIN_ROBERTO)
    for nombre in ("encendida", "produccion"):
        s = salidas[nombre]
        assert s["r"]["motivo"] == "EJECUTADA", s["r"]
        assert s["escritor"] == [["place_bid", {"player_id": ADRIAN, "amount": 4_909_900,
                                                "execute": True}]], s["escritor"]
        assert s["libro"] == {str(ADRIAN): {"sale": BOYE, "suelo": 4_896_000,
                                            "puja": 4_909_900, "puntos": 0.61,
                                            "prima_que_gana": 0.121}}, s["libro"]
        assert s["r"]["plan"]["caja"] == -164_276
        assert s["r"]["plan"]["caja_despues"] == 93_824
        assert s["r"]["plan"]["prima_que_gana"] == {ADRIAN: 0.121}
        assert [h["importe"] for h in s["vuelta"]["hechas"]] == [4_909_900]
    a = salidas["apagada"]
    assert a["escritor"] == [["place_bid", {"player_id": ADRIAN, "amount": 4_429_900,
                                            "execute": True}]], a["escritor"]
    assert a["libro"] == {str(ADRIAN): {"sale": BOYE, "suelo": 4_896_000,
                                        "puja": 4_429_900, "puntos": 0.61}}, a["libro"]
    assert "prima_que_gana" not in a["r"]["plan"]
    assert temprano["r"]["plan"]["caja"] == -264_776
    assert [c for c in temprano["escritor"] if c[0] == "place_bid"] == [
        ["place_bid", {"player_id": ADRIAN, "amount": 4_429_900, "execute": True}]]
    assert temprano["r"]["plan"]["prima_que_no_cabe"] == [ADRIAN]


# 9. NUNCA LANZA

def test_nunca_lanza():
    from src.actions import la_mejora_del_once as mejora

    for basura in (None, 3, "x", [], {"puja": "x"}, {"caja": None, "puja": 2_000_000},
                   {"puja": 2_000_000, "caja": 0, "ya_es_nuestro": False, "puntos": "x"}):
        mejora.con_la_prima(basura, 2_500_000, {}, 85.0)
        mejora.con_la_prima(basura, "x", "x", "x")
    assert mejora.la_puja_de_la_prima(float("nan"), 1.0) is None
    for precio in (None, "x", -5, 0, True):
        mejora.la_puja_de_la_prima(precio, float("nan"), "x")
    # `decidir` encendida con precios basura y horas basura.
    rotos = {ADRIAN: {"precio": None}, 38290: {"precio": "x"}, UNAI_SIMON: {"sube": "x"}}
    for horas in (84.0, 227.0):
        _decidir_de(E1007, caja=2_000_000, horas=horas, cambiados=rotos,
                    prima_que_gana=True, **PRODUCCION_DE_LA_MEJORA)
    # `correr` encendida con basura: no lanza (motivo ERROR o nada).
    with _Interruptores({**ENTORNO_MINIMO, ENV: "1"}), tempfile.TemporaryDirectory() as c:
        r = mejora.correr(status={"todaLaLiga": {"players": [None, 3]}}, snapshot={},
                          v10={}, escritor_factory=_Escritor,
                          ahora=datetime(2026, 11, 3, 9, 7, tzinfo=_UTC),
                          libro_ruta=Path(c) / "l.json", calendario={},
                          de_fuera={"orden": {}, "vetados": set(), "protegidos": set(),
                                    "libro_ronda": Path(c) / "r.json",
                                    "libro_chollos": Path(c) / "ch.json",
                                    "horas_jornada": 84.0, "puede_escribir": True,
                                    "en_curso": False, "rotando": set()})
        assert isinstance(r, dict) and r["activa"] is True, r


# 10. EL ENTORNO NO DECIDE (doctrina 104)

def test_el_entorno_no_decide_esta_guardia():
    """Con todo lo de fuera puesto (los del tablon, esta incluida, la puja
    fuerte, la hucha, uno que no existe), cada prueba da lo mismo, y al
    salir el entorno es el de antes."""
    from src.telemetry.el_tablon import QUE_HACE

    de_fuera = {n: "1" for n in QUE_HACE if n.startswith("BORDALAS_")}
    de_fuera.update({"BORDALAS_SIN_REVENTA": "1", "BORDALAS_BID_SALT": "otra-sal",
                     "BORDALAS_LA_MEJORA_PUJA_FUERTE": "1", "BORDALAS_LA_HUCHA": "1",
                     "BORDALAS_UNO_QUE_NO_EXISTE": "si", ENV: "1"})
    antes = {k: os.environ.get(k) for k in de_fuera}
    os.environ.update(de_fuera)
    try:
        with _Interruptores({"BORDALAS_LA_MEJORA_DEL_ONCE": "1"}):
            dentro = sorted(k for k in os.environ
                            if k.startswith("BORDALAS_") and k not in DE_LA_VERJA)
            assert dentro == ["BORDALAS_LA_MEJORA_DEL_ONCE"], dentro
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
    test_apagada_es_main_byte_a_byte,
    test_la_puja_de_la_prima,
    test_solo_el_que_sube_de_1_a_8_m_a_64_h_o_mas,
    test_los_demas_como_siempre,
    test_adrian_nino_con_la_caja_de_las_10,
    test_adrian_nino_con_la_caja_de_las_07_no_cabe,
    test_la_caja_de_la_jornada_no_baja_de_cero,
    test_un_punto_o_mas_18_y_la_combinacion_cuenta_la_prima,
    test_la_prima_nunca_hace_perder_un_cambio,
    test_nunca_por_encima_de_la_puja_maxima_ni_de_lo_libre,
    test_a_menos_de_64_horas_lo_de_siempre,
    test_manda_sobre_la_puja_fuerte,
    test_el_dia_del_jugador_de_la_hucha_ninguna_prima,
    test_correr_puja_y_apunta_la_de_verdad,
    test_nunca_lanza,
    test_el_entorno_no_decide_esta_guardia,
]


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
