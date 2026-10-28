"""
LA RONDA, SOLO LO QUE PAGA (28/10/2026). Guardias de
`BORDALAS_LA_RONDA_SOLO_LO_QUE_PAGA` en
`src/actions/la_ronda_de_la_manana.py` (la compra de `decidir`, y
`correr`, que lee el interruptor).

EL CASO (28/10/2026, 07:19)

    A 61,7 h de la J11 (sin prima: menos de `HORAS_PRIMA`) la ronda
    pujo precio + 1 % por Fortuño (1.830.000, +7 %: 1.848.000) y por
    Nacho Pérez (830.000, +5,1 %: 838.000). A + 1 % por uno que sube el
    4 % o mas no se gana casi nunca (0 de 13), y con las dos ganadas la
    J11 empezaba en -1.267.025. El gestor retiro la de Fortuño.

QUE SE COMPRUEBA

    1. NACE APAGADO, y apagado `decidir` es el de main byte a byte: la
       huella de una bateria amplia (precios de todos los tramos,
       subidas, a 30/41/63/64/65/90 h y sin calendario, con y sin
       cartera, con managers, con el colchon justo y lo disponible
       corto, con salidas, hueco, protegidos y pujas vivas) sale
       clavada a la de main@6358dabe. Y `decidir` es pura: el
       interruptor en el entorno no la mueve, solo lo lee `correr`.
    2. Encendido, del Computer solo se puja por el que pide menos de
       1 M, sube hoy el 2 % o mas de su valor de hoy (la ficha; si no,
       lo que pide) y a 64 h o mas de la jornada; y a
       `la_puja_de_la_cartera` (+12 %, en 9.900).
    3. El 28/10: ni Fortuño (caro) ni Nacho (a 61,7 h). A 70 h, Nacho
       si (+12 %) y Fortuño no.
    4. Los de los managers (la puerta), igual que hoy.
    5. Las demas guardias siguen: estado, juega, la subida minima, el
       colchon, el hueco, el tope, lo disponible, protegidos, pujas
       vivas, plantilla, zona de silencio y `HORAS_SIN_COMPRAR`.
    6. La salida (publicar, aceptar, suelos, aguantar) no cambia: en
       toda la bateria, lo que no es PUJAR sale igual encendido.
    7. `correr` lee el interruptor y se lo pasa a `decidir`.
    8. Nunca lanza.

DE DONDE SALEN LOS NUMEROS

    Las pujas del 28/10 (1.848.000 y 838.000) y las horas (07:19 del
    miercoles al viernes 21:00) son las de esa mañana; el resto del
    mercado, construido aqui. Ni la foto, ni la red, ni el reloj.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Cada prueba pone lo
# suyo; aqui arriba se quita lo que mueve la ronda.
ENV = "BORDALAS_LA_RONDA_SOLO_LO_QUE_PAGA"
ENV_RONDA = "BORDALAS_LA_RONDA_DE_LA_MANANA"
ENV_CARTERA = "BORDALAS_LA_CARTERA"
ENV_PUERTA = "BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO"
for _nombre in (ENV, ENV_RONDA, ENV_CARTERA, ENV_PUERTA):
    os.environ.pop(_nombre, None)


import src.actions.la_ronda_de_la_manana as ronda      # noqa: E402

from src.actions.la_ronda_de_la_manana import (       # noqa: E402
    decidir, la_puja, la_puja_de_la_cartera,
)


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


def _f(precio=1_000_000, sube=40_000, estado="ok", puntos=30, partidos=6):
    ficha = {"priceIncrement": sube, "status": estado, "points": puntos,
             "playedHome": partidos // 2, "playedAway": partidos - partidos // 2}
    if precio is not None:
        ficha["price"] = precio
    return ficha


def _d(paga=True, **k):
    """`decidir` con la cartera (como produccion), lejos de la jornada
    y con caja; `paga` es el interruptor."""
    base = dict(
        mercado={}, fichas={}, nuestras_pujas={}, plantilla=set(),
        ofertas_del_computer={}, en_venta=set(), maximo_de_puja=20_000_000,
        minutos_al_reset=127, horas_jornada=70, libro={}, cartera=True,
        saldo=5_000_000,
    )
    base.update(k)
    return decidir(**base, solo_lo_que_paga=paga)


def _pujas(a) -> dict:
    return {x["player_id"]: x["importe"] for x in a if x["accion"] == "PUJAR"}


def _huella(salida) -> str:
    crudo = json.dumps(salida, sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


# ============================================================
# LA BATERIA
# ============================================================

#   pid, lo que pide, su valor (la ficha; None: sin precio), sube hoy,
#   estado, puntos, partidos
JUGADORES = (
    (1, 450_000, 450_000, 15_750, "ok", 30, 6),          # < 1 M, +3,5 %
    (2, 830_000, 830_000, 42_330, "ok", 33, 9),          # Nacho, +5,1 %
    (3, 1_830_000, 1_830_000, 128_100, "ok", 40, 9),     # Fortuño, +7 %
    (4, 2_000_000, 2_000_000, 30_000, "ok", 30, 6),      # 1-3 M, +1,5 %
    (5, 990_000, 1_010_000, 20_000, "ok", 30, 6),        # pide < 1 M, vale 1,01 M: +1,98 %
    (6, 700_000, 700_000, 21_700, "ok", 30, 6),          # +3,1 % justo
    (7, 2_900_000, 2_900_000, 40_000, "ok", 30, 6),      # en el tope
    (8, 4_690_000, 4_690_000, 30_000, "ok", 30, 6),      # pasa del tope
    (9, 980_000, 980_000, 30_380, "ok", 30, 6),          # +3,1 %
    (10, 600_000, 600_000, 30_000, "doubt", 30, 6),      # en duda
    (11, 500_000, 500_000, 20_000, "ok", 6, 6),          # no puntua
    (12, 1_000_000, 1_000_000, 50_000, "ok", 30, 6),     # 1 M justo, +5 %
    (13, 999_000, None, 40_000, "ok", 30, 6),            # ficha sin precio
    (14, 300_000, 300_000, -5_000, "ok", 30, 6),         # baja
    (15, 750_000, 750_000, 15_000, "ok", 30, 6),         # +2 %, sin la subida minima (3,1 %)
    (16, 1_500_000, 1_500_000, 30_000, "ok", 30, 6),     # 1-3 M, +2 % justo
    (17, 995_000, 1_000_000, 20_000, "ok", 30, 6),       # pide < 1 M, vale 1 M: +2 % justo
)

# Lo de la ronda, para la salida: pagado, su ficha y la oferta del Computer.
LIBRO = {"20": 1_000_000, "21": 900_000, "22": 2_000_000, "23": 1_500_000}
FICHAS_DEL_LIBRO = {
    20: _f(1_200_000, sube=30_000), 21: _f(850_000, sube=-10_000),
    22: _f(2_000_000, sube=0), 23: _f(1_600_000, sube=25_000),
}
OFERTAS = {20: {"offer_id": 1, "amount": 1_300_000},
           21: {"offer_id": 2, "amount": 830_000},
           22: {"offer_id": 3, "amount": 1_950_000}}


def _el_mercado():
    mercado = {pid: pide for pid, pide, *_ in JUGADORES}
    fichas = {pid: _f(valor, sube, estado, puntos, partidos)
              for pid, _, valor, sube, estado, puntos, partidos in JUGADORES}
    fichas.update(FICHAS_DEL_LIBRO)
    return mercado, fichas


def _la_bateria() -> list:
    """[(nombre, argumentos de `decidir`)], siempre en el mismo orden."""

    mercado, fichas = _el_mercado()
    casos = []

    def caso(nombre, **k):
        base = dict(
            mercado=dict(mercado), fichas=fichas, nuestras_pujas={}, plantilla=set(),
            ofertas_del_computer={}, en_venta=set(), maximo_de_puja=20_000_000,
            minutos_al_reset=127, horas_jornada=90, libro={},
        )
        base.update(k)
        casos.append((nombre, base))

    for horas in (30, 41, 63, 64, 65, 90, None):
        for cartera in (False, True):
            for saldo in (20_000_000, 400_000, None):
                for managers in (frozenset(), frozenset({3, 4, 9})):
                    for maximo in (20_000_000, 3_500_000):
                        caso(f"h={horas} cartera={cartera} saldo={saldo} "
                             f"managers={sorted(managers)} max={maximo}",
                             horas_jornada=horas, cartera=cartera, saldo=saldo,
                             de_managers=managers, maximo_de_puja=maximo)

    for horas in (15, 30, 41, 65, 90, None):
        for cartera in (False, True):
            for en_curso in (False, True):
                caso(f"salida h={horas} cartera={cartera} en_curso={en_curso}",
                     horas_jornada=horas, cartera=cartera, en_curso=en_curso,
                     libro=dict(LIBRO), plantilla={20, 21, 22, 23, 30},
                     ofertas_del_computer=OFERTAS, en_venta={20}, saldo=1_000_000,
                     nuestras_pujas={40: {"offer_id": 9, "amount": 700_000}})

    for horas in (63, 65, 90):
        for cartera in (False, True):
            caso(f"hueco h={horas} cartera={cartera}", horas_jornada=horas,
                 cartera=cartera, saldo=20_000_000, plantilla=set(range(100, 118)),
                 nuestras_pujas={200: {"offer_id": 1, "amount": 1}})
            caso(f"protegidos y vivas h={horas} cartera={cartera}", horas_jornada=horas,
                 cartera=cartera, saldo=20_000_000, protegidos={2, 6},
                 nuestras_pujas={9: {"offer_id": 5, "amount": 1_099_900}},
                 libro={"9": 1_099_900}, plantilla={1})
            caso(f"silencio h={horas} cartera={cartera}", horas_jornada=horas,
                 cartera=cartera, saldo=20_000_000, puede_escribir=False)
            for saldo in (150_000, 0, -432_317):
                caso(f"colchon {saldo} h={horas} cartera={cartera}", horas_jornada=horas,
                     cartera=cartera, saldo=saldo)
    return casos


def _salidas(**extra) -> list:
    return [[nombre, decidir(**k, **extra)] for nombre, k in _la_bateria()]


# LA HUELLA DE MAIN. Medida el 28/10/2026 en main@6358dabe (la ronda sin
# tocar), igual con PYTHONHASHSEED 0, 3 y 11: sha256 del JSON ordenado de
# [nombre, lo que decide] de toda la bateria. Apagado tiene que salir la
# misma, letra a letra. Si algun dia se cambia la ronda A PROPOSITO, se
# rehace con el interruptor apagado y se dice en el commit.
CASOS_DE_MAIN = 228
PUJAS_DE_MAIN = 951
HUELLA_DE_MAIN = "01e759bacf3868a9a4eb02e7de54f695f1e78c5f6af6fec3667c12d47ea64ce3"


# ============================================================
# 1. NACE APAGADO, Y APAGADO ES EL DE MAIN
# ============================================================

def test_nace_apagado():
    with _Interruptores({ENV: None}):
        assert ronda.la_ronda_solo_lo_que_paga_activa() is False
    for valor, puesto in (("1", True), ("si", True), ("true", True), ("yes", True),
                          ("0", False), ("no", False), ("", False), ("x", False)):
        with _Interruptores({ENV: valor}):
            assert ronda.la_ronda_solo_lo_que_paga_activa() is puesto, valor
    assert ronda.ENV_SOLO_LO_QUE_PAGA == ENV
    # Un interruptor sin frase para el dueño pone la verja en rojo el dia
    # que se enciende (leccion del 26/10).
    from src.telemetry.el_tablon import QUE_HACE
    assert str(QUE_HACE.get(ENV) or "").strip(), "sin frase en QUE_HACE"


def test_apagado_es_el_de_main():
    with _Interruptores({ENV: None}):
        hoy = _salidas()
    # Primero lo que dice QUE se movio; la huella, la ultima.
    assert len(hoy) == CASOS_DE_MAIN, len(hoy)
    pujas = sum(1 for _, s in hoy for a in s if a["accion"] == "PUJAR")
    assert pujas == PUJAS_DE_MAIN, pujas
    assert _huella(hoy) == HUELLA_DE_MAIN, _huella(hoy)
    # Apagado a mano, lo mismo.
    assert _huella(_salidas(solo_lo_que_paga=False)) == HUELLA_DE_MAIN
    # `decidir` es pura: con el interruptor en el entorno no cambia (solo
    # lo lee `correr`).
    with _Interruptores({ENV: "1"}):
        assert _huella(_salidas()) == HUELLA_DE_MAIN


# ============================================================
# 2. ENCENDIDO: SOLO LO QUE PAGA
# ============================================================

def test_solo_el_de_menos_de_1m_que_sube_el_2_y_lejos():
    nuevo = {1: 450_000}
    fichas = {1: _f(450_000, sube=15_750)}                    # +3,5 %
    # A 70 h: la prima de la cartera (+12 %, en 9.900).
    a = _pujas(_d(mercado=nuevo, fichas=fichas, horas_jornada=70))
    assert a == {1: la_puja_de_la_cartera(450_000, 15_750)} == {1: 509_900}, a
    # A 64 h justas, tambien; a 63,9 y a 60, nada (apagado: + 1 %).
    assert _pujas(_d(mercado=nuevo, fichas=fichas, horas_jornada=64)) == {1: 509_900}
    for horas in (63.9, 60, 41):
        assert _pujas(_d(mercado=nuevo, fichas=fichas, horas_jornada=horas)) == {}, horas
        assert _pujas(_d(paga=False, mercado=nuevo, fichas=fichas, horas_jornada=horas)) == {
            1: la_puja(450_000)}, horas
    # Caro (1,83 M, +7 %): nada; apagado, + 4 % de la cartera.
    caro = dict(mercado={3: 1_830_000}, fichas={3: _f(1_830_000, sube=128_100)})
    assert _pujas(_d(**caro)) == {}
    assert _pujas(_d(paga=False, **caro)) == {3: la_puja_de_la_cartera(1_830_000)}
    # 1 M justo (+5 %): no es menos de 1 M.
    assert _pujas(_d(mercado={12: 1_000_000}, fichas={12: _f(1_000_000, sube=50_000)})) == {}


def test_el_2_por_ciento_donde_la_subida_minima_deja():
    # 2 M que sube +1,5 %: pasa la subida minima de su tramo (1,1 %), asi
    # que apagado se puja (con y sin cartera); encendido, no.
    k = dict(mercado={4: 2_000_000}, fichas={4: _f(2_000_000, sube=30_000)})
    assert _pujas(_d(paga=False, **k)) == {4: la_puja_de_la_cartera(2_000_000)} == {4: 2_089_900}
    assert _pujas(_d(paga=False, cartera=False, **k)) == {4: la_puja(2_000_000)} == {4: 2_020_000}
    assert _pujas(_d(**k)) == {} and _pujas(_d(cartera=False, **k)) == {}
    # Pide menos de 1 M pero vale 1,01 M y sube 20.000 (+1,98 % de su
    # valor de hoy): la subida minima (la de 1,01 M) deja; el 2 %, no.
    k = dict(mercado={5: 990_000}, fichas={5: _f(1_010_000, sube=20_000)})
    assert _pujas(_d(paga=False, **k)) == {5: la_puja_de_la_cartera(990_000)}
    assert _pujas(_d(**k)) == {}
    # El 2 % justo de su valor (1 M, sube 20.000; pide 995.000): si.
    k = dict(mercado={17: 995_000}, fichas={17: _f(1_000_000, sube=20_000)})
    assert _pujas(_d(**k)) == {17: la_puja_de_la_cartera(995_000, 20_000)} == {17: 1_119_900}
    # Ficha sin precio: el 2 % va sobre lo que pide.
    k = dict(mercado={13: 999_000}, fichas={13: _f(None, sube=40_000)})
    assert _pujas(_d(**k)) == {13: la_puja_de_la_cartera(999_000)}
    k = dict(mercado={13: 999_000}, fichas={13: _f(None, sube=19_979)})
    assert _pujas(_d(**k)) == {}
    # Sin la cartera, la misma regla y la misma puja (+12 %).
    k = dict(mercado={1: 450_000}, fichas={1: _f(450_000, sube=15_750)})
    assert _pujas(_d(cartera=False, **k)) == {1: 509_900}


def test_el_28_10_ni_fortuno_ni_nacho():
    mercado = {3: 1_830_000, 2: 830_000}
    fichas = {3: _f(1_830_000, sube=128_100, puntos=40, partidos=9),
              2: _f(830_000, sube=42_330, puntos=33, partidos=9)}
    # 07:19 del miercoles al viernes 21:00: 61,7 h.
    k = dict(mercado=mercado, fichas=fichas, horas_jornada=61.7)
    apagado = _d(paga=False, **k)
    assert [(x["player_id"], x["importe"]) for x in apagado] == [
        (3, 1_848_000), (2, 838_000)], apagado
    assert _d(**k) == [], _d(**k)
    # A 70 h, Nacho si (+12 %) y Fortuño no.
    assert _pujas(_d(mercado=mercado, fichas=fichas, horas_jornada=70)) == {2: 929_900}


def test_los_de_los_managers_como_hoy():
    k = dict(mercado={3: 1_830_000, 4: 2_000_000},
             fichas={3: _f(1_830_000, sube=128_100), 4: _f(2_000_000, sube=30_000)},
             de_managers=frozenset({3, 4}))
    for horas in (41, 61.7, 64, 70, 90):
        for cartera in (False, True):
            encendido = _d(horas_jornada=horas, cartera=cartera, **k)
            assert encendido == _d(paga=False, horas_jornada=horas, cartera=cartera, **k)
            assert _pujas(encendido) == {3: la_puja(1_830_000), 4: la_puja(2_000_000)}, (
                horas, cartera, encendido)


# ============================================================
# 3. LAS DEMAS GUARDIAS SIGUEN
# ============================================================

def test_las_demas_guardias_siguen():
    uno = dict(mercado={1: 450_000}, fichas={1: _f(450_000, sube=15_750)})
    assert _pujas(_d(**uno)) == {1: 509_900}
    # Estado, juega, la subida minima (750.000 +2 %: el 2 % si, el 3,1 % no).
    assert _pujas(_d(mercado={1: 450_000}, fichas={1: _f(450_000, 15_750, "doubt")})) == {}
    assert _pujas(_d(mercado={1: 450_000}, fichas={1: _f(450_000, 15_750, puntos=6)})) == {}
    assert _pujas(_d(mercado={1: 450_000}, fichas={1: _f(450_000, 15_750, partidos=2)})) == {}
    assert _pujas(_d(mercado={15: 750_000}, fichas={15: _f(750_000, sube=15_000)})) == {}
    assert _pujas(_d(mercado={1: 450_000}, fichas={})) == {}
    # Protegidos, pujas vivas, plantilla.
    assert _pujas(_d(protegidos={1}, **uno)) == {}
    assert _pujas(_d(nuestras_pujas={1: {"offer_id": 3, "amount": 460_000}}, **uno)) == {}
    assert _pujas(_d(plantilla={1}, **uno)) == {}
    # Zona de silencio, `HORAS_SIN_COMPRAR` y sin calendario.
    assert _pujas(_d(puede_escribir=False, **uno)) == {}
    for horas in (30, 39.9, None):
        assert _pujas(_d(horas_jornada=horas, **uno)) == {}, horas
    # El colchon: la puja (509.900) cuesta 509.900 - 0,92 x 450.000 = 95.900.
    assert _pujas(_d(saldo=95_900, **uno)) == {1: 509_900}
    assert _pujas(_d(saldo=95_899, **uno)) == {}
    assert _pujas(_d(saldo=None, **uno)) == {}
    # El hueco: con 19 entre plantilla y pujas, solo el primero.
    dos = dict(mercado={1: 450_000, 2: 830_000},
               fichas={1: _f(450_000, sube=15_750), 2: _f(830_000, sube=42_330)})
    assert len(_pujas(_d(**dos))) == 2
    assert _pujas(_d(plantilla=set(range(100, 119)), **dos)) == {2: 929_900}
    assert _pujas(_d(plantilla=set(range(100, 120)), **dos)) == {}
    # Lo disponible: `maximumBid` - 1 M de reserva.
    assert _pujas(_d(maximo_de_puja=1_509_900, **uno)) == {1: 509_900}
    assert _pujas(_d(maximo_de_puja=1_509_899, **uno)) == {}
    # El tope por viaje (con uno de mentira, que a < 1 M no se llega).
    viejo = ronda.TOPE_POR_VIAJE
    try:
        ronda.TOPE_POR_VIAJE = 509_899
        assert _pujas(_d(**uno)) == {}
        ronda.TOPE_POR_VIAJE = 509_900
        assert _pujas(_d(**uno)) == {1: 509_900}
    finally:
        ronda.TOPE_POR_VIAJE = viejo


# ============================================================
# 4. EN TODA LA BATERIA: LA SALIDA IGUAL, Y SOLO LO QUE PAGA
# ============================================================

def test_en_toda_la_bateria():
    del_computer = 0
    for nombre, k in _la_bateria():
        apagado = decidir(**k)
        encendido = decidir(**k, solo_lo_que_paga=True)
        # La salida (publicar, aceptar) no cambia.
        assert ([x for x in encendido if x["accion"] != "PUJAR"]
                == [x for x in apagado if x["accion"] != "PUJAR"]), nombre
        managers = k.get("de_managers") or frozenset()
        for x in encendido:
            if x["accion"] != "PUJAR":
                continue
            pid, pide, sube = x["player_id"], x["pide"], x["sube"]
            if pid in managers:
                assert x["importe"] == la_puja(pide), (nombre, x)
                continue
            del_computer += 1
            valor = (k["fichas"].get(pid) or {}).get("price") or pide
            assert pide < 1_000_000, (nombre, x)
            assert sube >= math.ceil(round(valor * 0.02, 6)), (nombre, x)
            assert k["horas_jornada"] >= ronda.HORAS_PRIMA, (nombre, x)
            assert x["importe"] == la_puja_de_la_cartera(pide, sube), (nombre, x)
        # Solo con los de los managers en el mercado, lo mismo que apagado.
        solo_managers = {**k, "mercado": {p: v for p, v in k["mercado"].items()
                                          if p in managers}}
        assert (decidir(**solo_managers, solo_lo_que_paga=True)
                == decidir(**solo_managers)), nombre
    assert del_computer > 0, "la bateria no puja por nadie encendida"


# ============================================================
# 5. CORRER LEE EL INTERRUPTOR
# ============================================================

def test_correr_le_pasa_el_interruptor():
    vistos = []

    def _espia(**kwargs):
        vistos.append(kwargs.get("solo_lo_que_paga"))
        return []

    viejo = ronda.decidir
    try:
        ronda.decidir = _espia
        for valor, esperado in ((None, False), ("1", True), ("0", False), ("si", True)):
            with _Interruptores({ENV: valor, ENV_RONDA: "1"}):
                with tempfile.TemporaryDirectory() as d:
                    r = ronda.correr({"snapshot": None}, 10,
                                     libro_ruta=Path(d) / "la_ronda.json")
            assert r["motivo"] == "NADA_QUE_HACER", r
            assert vistos and vistos[-1] is esperado, (valor, vistos)
    finally:
        ronda.decidir = viejo
    assert len(vistos) == 4, vistos


# ============================================================
# 6. NUNCA LANZA
# ============================================================

def test_nunca_lanza():
    lo_que_paga = ronda.lo_que_paga
    for basura in (None, "x", [], {}, float("nan"), -1, 0):
        assert lo_que_paga(basura, basura, basura, basura) is False, repr(basura)
        assert lo_que_paga(450_000, 15_750, basura, 70) in (True, False), repr(basura)
        assert lo_que_paga(450_000, 15_750, {"price": basura}, 70) in (True, False)
        assert lo_que_paga(450_000, 15_750, {"price": 450_000}, basura) is False, repr(basura)
    assert lo_que_paga(450_000, 15_750, {"price": 450_000}, 70) is True
    assert lo_que_paga(450_000, 15_750, None, 70) is True
    assert lo_que_paga("450000", "15750", {"price": "450000"}, 70) is True
    # `decidir` encendida, con fichas de basura: nada, y sin lanzar.
    for ficha in ({"status": "ok", "priceIncrement": "x"},
                  {"status": "ok", "priceIncrement": 40_000, "price": "y",
                   "points": 30, "playedHome": 3, "playedAway": 3},
                  {"status": "ok", "priceIncrement": 40_000, "price": None,
                   "points": "z", "playedHome": 3, "playedAway": 3},
                  {"status": "ok", "priceIncrement": 40_000, "price": -5,
                   "points": 30, "playedHome": 3, "playedAway": 3}):
        for horas in (70, float("nan"), float("inf"), 64):
            _d(mercado={1: 450_000, 2: 0}, fichas={1: ficha, 2: ficha},
               horas_jornada=horas)
    assert _d(mercado={1: 0}, fichas={1: {"status": "ok", "priceIncrement": "x"}},
              maximo_de_puja=None, libro={"x": "y"}) == []
    with _Interruptores({ENV: "1", ENV_RONDA: "1"}):
        for cycle in ({"snapshot": None}, None, {"snapshot": {"catalog": 7}}):
            with tempfile.TemporaryDirectory() as d:
                r = ronda.correr(cycle, 10, libro_ruta=Path(d) / "la_ronda.json")
            assert r["motivo"] == "NADA_QUE_HACER" or r["motivo"].startswith("ERROR"), r
    # El lector, con el entorno roto.
    viejo = ronda.os.environ
    try:
        ronda.os.environ = None
        assert ronda.la_ronda_solo_lo_que_paga_activa() is False
    finally:
        ronda.os.environ = viejo


TESTS = [
    test_nace_apagado,
    test_apagado_es_el_de_main,
    test_solo_el_de_menos_de_1m_que_sube_el_2_y_lejos,
    test_el_2_por_ciento_donde_la_subida_minima_deja,
    test_el_28_10_ni_fortuno_ni_nacho,
    test_los_de_los_managers_como_hoy,
    test_las_demas_guardias_siguen,
    test_en_toda_la_bateria,
    test_correr_le_pasa_el_interruptor,
    test_nunca_lanza,
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
