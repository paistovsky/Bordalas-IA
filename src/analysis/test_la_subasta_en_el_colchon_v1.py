"""
LA SUBASTA EN EL COLCHON (01/11/2026). Guardias de
`BORDALAS_LA_SUBASTA_EN_EL_COLCHON` (`src/analysis/la_subasta_en_el_colchon.py`
y su enganche en `la_subasta.plan_desde_el_estado`, por donde pasan el
ciclo, `_pujar_en_el_reset`, y la pantalla, `bloque_de_la_subasta`).

EL CASO (bitacora del 31/10 22:30; comentario «ENCENDIDO 31/10 —
BORDALAS_SIN_SUBASTA» del YAML)

    El 31/10 a las 04:48 la cesta del reset pujo 2.025.051 por Dani
    Lorenzo con el saldo en 1.299.975 y 929.800 en pujas vivas de la
    ronda (Macia 709.900, Angel Ortiz 219.900). El freno de la solvencia
    dijo SIN_DEUDA porque no ve ni la cesta ni las pujas vivas; el tope
    es min(presupuesto, 3 x saldo); no mira lo cerca que esta la jornada
    y el colchon de la casa (UN_SOLO_COLCHON) solo vive en el ejecutor.
    El colchon era 1.179.775 (1.299.975 - 929.800 + 92 % de 690.000 y
    190.000): la puja no cabia. Y Dani subia +10.000 sobre 2.020.000, por
    debajo de la subida minima de su tramo (22.220).

QUE SE COMPRUEBA

    1. NACE APAGADO, se lee en UN sitio y tiene frase en QUE_HACE.
    2. Apagado es main byte a byte: la huella de `plan_desde_el_estado` y
       `plan_del_reset` sobre una bateria de estados reales (el artefacto
       de la run 41291694432, 01/11 09:11 UTC, y la vuelta del 31/10
       04:48 reconstruida) y sinteticos, con cinco entornos de
       interruptores, sale clavada a la de main medida ANTES de tocar el
       codigo, en 3.11 y en 3.13. Y apagado no corre ni una linea del
       modulo.
    3. Encendido: la vuelta del 31/10 no puja (no sube de verdad; y
       aunque subiera, no cabe en el colchon). Lo barato que cabe, si.
       Las 40 h: jue 05/11 04:45 (40,25 h) pasa, vie 06/11 04:45
       (16,25 h) no. Sin reloj, no. Sin colchon, no. El colchon se
       cuenta ACUMULADO: dos que caben solas y no juntas, solo la
       primera. Las cuentas del plan cuadran con lo que queda.
    4. Los dos caminos de verdad: el ciclo (`_pujar_en_el_reset`, con el
       escritor cambiado por uno que apunta) y la pantalla
       (`bloque_de_la_subasta`) ven lo mismo.
    5. Nunca lanza: si algo falla, no se puja y se dice por que.

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui. El tablero, la plantilla, los bolsillos y el
    reloj de solvencia del 01/11 son los del artefacto de la run
    41291694432 (compactados a los campos que lee
    `la_subasta.lectura_del_estado`). La vuelta del 31/10 04:48:
    la puja, el precio y el 61 % salen del libro de pujas; el saldo y
    las pujas de la ronda, de la bitacora; los precios de Macia
    (690.000) y Angel Ortiz (190.000) a esa hora, de
    `price_history.json`; los bolsillos, reconstruidos (presupuesto =
    3 x saldo - pujas vivas, caja = saldo - pujas vivas). Ni la
    carpeta de estado, ni la red: el calendario se pasa como dict y el
    libro de la ronda va en una carpeta temporal.

COMO SE USA

    python -m src.analysis.test_la_subasta_en_el_colchon_v1
    python -m src.analysis.test_la_subasta_en_el_colchon_v1 --medir
"""

from __future__ import annotations

import ast
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


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Todo lo que mueve la
# cesta se quita aqui arriba, antes de importar nada; cada prueba pone lo
# suyo. Produccion corre con `BORDALAS_SIN_SUBASTA=1`, que cierra la cesta
# entera: sin quitarlo, todo esto saldria INTERRUPTOR.
ENV = "BORDALAS_LA_SUBASTA_EN_EL_COLCHON"
DE_LA_CESTA = (
    ENV,
    "BORDALAS_SIN_SUBASTA",
    "BORDALAS_CESTA_SOLO_EL_SUELO",
    "BORDALAS_CUPO_POR_VENTANA",
    "BORDALAS_SOLVENCIA_POR_SU_PLAZO",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA",
    "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_SIN_REVENTA",
    "BORDALAS_PRIMA_POR_TRAMO",
    "BORDALAS_LA_ORDEN_DEL_GESTOR",
)
for _nombre in DE_LA_CESTA:
    os.environ.pop(_nombre, None)


import src.analysis.la_subasta as sub  # noqa: E402


class _Interruptores:
    """Pone (valor) o quita (None) interruptores solo dentro del `with`.
    Los de la cesta que no se nombran, quitados."""

    def __init__(self, valores: dict | None = None):
        self.valores = {n: None for n in DE_LA_CESTA}
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


APAGADO = {}
PUESTO = {ENV: "1"}


class _LaOrdenVeta:
    """`la_orden_del_gestor.vetados`, cambiado por uno fijo (sin leer
    `config/` ni mirar el reloj)."""

    def __init__(self, ids):
        self.ids = set(ids)

    def __enter__(self):
        from src.actions import la_orden_del_gestor as orden

        self._orden, self._antes = orden, orden.vetados
        ids = self.ids
        orden.vetados = lambda *a, **k: set(ids)
        return self

    def __exit__(self, *_):
        self._orden.vetados = self._antes
        return False


# ============================================================
# EL TABLERO DEL 01/11 (artefacto de la run 41291694432)
# ============================================================

YO = 14175949

TABLERO_0111 = (
    # (id, nombre, precio, sube, club, decision, fuera_del_computer, vendedor,
    #  puja_viva, titular %, jerarquia, disponible, intent, via, ritmo %/dia, puntos)
    (9480, 'Comesaña', 1940000, -20000, 19, 'BID', False, None, False, 50.0, 40, 'DISPONIBLE', 'XI_UPGRADE', 'ROSTER_FILL', None, 167),
    (1462, 'Moi Gómez', 1580000, 20000, 93, 'MERCADO_DE_RIVAL', True, 14145555, False, 70.0, 40, 'DISPONIBLE', 'XI_UPGRADE', 'ROSTER_FILL', None, 95),
    (43268, 'Revivo', 2740000, 110000, 75, 'MERCADO_DE_RIVAL', True, 14176382, False, 90.0, 40, 'DISPONIBLE', 'XI_UPGRADE', 'XI_UPGRADE', 4.289, 144),
    (429, 'Rodri', 17150000, 30000, 3, 'SUPERA_PRESUPUESTO', False, None, False, 100.0, 50, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.234, 946),
    (19547, 'Baena', 13060000, 80000, 2, 'MERCADO_DE_RIVAL', True, 14176382, False, 80.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.576, 124),
    (25127, 'Ez Abde', 13050000, 100000, 87, 'MERCADO_DE_RIVAL', True, 14176382, False, 100.0, 50, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.766, 232),
    (30495, 'Moleiro', 10590000, 20000, 19, 'MERCADO_DE_RIVAL', True, 14145555, False, 70.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.662, 213),
    (38962, 'Mikautadze', 7140000, 50000, 19, 'MERCADO_DE_RIVAL', True, 14145555, False, 70.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.846, 125),
    (30487, 'Álvaro Valles', 7070000, 20000, 87, 'MERCADO_DE_RIVAL', True, 14176382, False, 100.0, 50, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.426, 129),
    (15430, 'Joan García', 6640000, -30000, 3, 'NO_COMPENSA', False, None, False, 100.0, 50, 'DISPONIBLE', 'SPECULATION', 'ROSTER_FILL', -0.45, 235),
    (17687, 'Kang-in Lee', 8970000, -40000, 2, 'MERCADO_DE_RIVAL', True, 14156489, False, 70.0, 40, 'DISPONIBLE', 'SPECULATION', 'ROSTER_FILL', 0.0, 461),
    (20969, 'Germán Valera', 5820000, 50000, 75, 'MERCADO_DE_RIVAL', True, 14145555, False, 90.0, 50, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.867, 203),
    (15396, 'Brugué', 4830000, 10000, 10, 'MERCADO_DE_RIVAL', True, 14145555, False, 70.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.415, 39),
    (30081, 'Pape Gueye', 6230000, -10000, 19, 'MERCADO_DE_RIVAL', True, 14176382, False, 70.0, 40, 'DISPONIBLE', 'SPECULATION', 'ROSTER_FILL', -1.282, 186),
    (39901, 'Freeman', 3860000, 40000, 19, 'MERCADO_DE_RIVAL', True, 14176382, False, 40.0, 30, 'DISPONIBLE', 'SPECULATION', 'HOLD', 2.094, 17),
    (18174, 'De Jong', 3560000, 110000, 3, 'MERCADO_DE_RIVAL', True, 14176382, False, 100.0, 20, 'DISPONIBLE', 'SPECULATION', 'HOLD', 3.09, 38),
    (43262, 'Félix Correia', 3320000, 50000, 17, 'MERCADO_DE_RIVAL', True, 14176382, False, 80.0, 40, 'DISPONIBLE', 'SPECULATION', 'HOLD', 2.141, 164),
    (2044, 'Ceballos', 2980000, 0, 87, 'SUPERA_PRESUPUESTO', False, None, False, 0.0, 25, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.336, 22),
    (19860, 'Febas', 2640000, 0, 5, 'MERCADO_DE_RIVAL', True, 14145555, False, 70.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.758, 139),
    (32363, 'Isaac Romero', 1970000, 80000, 17, 'SUPERA_PRESUPUESTO', False, None, False, 50.0, 25, 'DISPONIBLE', 'SPECULATION', 'HOLD', 4.676, 31),
    (39431, 'Thiago Fernández', 1700000, 60000, 10, 'MERCADO_DE_RIVAL', True, 14156489, False, 70.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 57),
    (38318, 'Valentín Gómez', 1540000, 30000, 87, 'MERCADO_DE_RIVAL', True, 14145555, False, 0.0, 20, 'DISPONIBLE', 'SPECULATION', 'PRICE_TREND', 3.974, 21),
    (17645, 'Galán', 1450000, -10000, 5, 'SUPERA_PRESUPUESTO', False, None, False, 50.0, 25, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 46),
    (37897, 'Gorrotxategi', 1390000, 40000, 13, 'MERCADO_DE_RIVAL', True, 14145555, False, 80.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 71),
    (42757, 'Ndukwe', 1340000, 40000, 10, 'MERCADO_DE_RIVAL', True, 14156489, False, 80.0, 25, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', 0.769, 26),
    (12734, 'Javi Morcillo', 1110000, 20000, 75, 'MERCADO_DE_RIVAL', True, 14176382, False, 90.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 18),
    (5352, 'Óscar Valentín', 1100000, -10000, 70, 'NO_DISPONIBLE', False, None, False, 30.0, 30, 'DUDA', 'SPECULATION', 'COMPUTER_RESALE', None, 64),
    (34483, 'Pedro Díaz', 950000, -10000, 70, 'MERCADO_DE_RIVAL', True, 14176382, False, 50.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 49),
    (18382, 'Raul García', 920000, -10000, 93, 'SUPERA_PRESUPUESTO', False, None, False, 20.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 72),
    (41609, 'Valentini', 910000, -20000, 91, 'SUPERA_PRESUPUESTO', False, None, False, 0.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 21),
    (39357, 'Maciá', 750000, 20000, 19, 'MERCADO_DE_RIVAL', True, 14176382, False, 40.0, 20, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 2),
    (41264, 'Mantilla', 770000, 0, 812, 'MERCADO_DE_RIVAL', True, 14176382, False, 80.0, 50, 'DISPONIBLE', 'SPECULATION', 'ROSTER_FILL', -1.299, 36),
    (26676, 'Luiz Felipe', 150000, 0, 70, 'NO_DISPONIBLE', False, None, False, 0.0, 20, 'LESIONADO', None, None, 0.0, 6),
    (27575, 'Barzic', 150000, 0, 75, 'SIN_VALOR', False, None, False, 0.0, 20, 'DISPONIBLE', None, None, 0.0, 2),
    (31254, 'Echegoyen', 150000, 0, 93, 'SIN_VALOR', False, None, False, None, None, None, None, None, 0.0, 7),
    (37723, 'José Salinas', 540000, -10000, 65, 'SIN_VALOR', False, None, False, 0.0, 30, 'DISPONIBLE', None, None, -1.818, 7),
    (38355, 'Neto', 370000, 0, 75, 'SIN_VALOR', False, None, False, 30.0, 20, 'DISPONIBLE', None, None, -2.703, 24),
    (38457, 'Ali Houary', 280000, 0, 75, 'SIN_VALOR', False, None, False, 0.0, 20, 'DISPONIBLE', None, None, 0.0, 1),
    (40037, 'Ochieng', 850000, -10000, 13, 'SIN_VALOR', False, None, False, 5.0, 30, 'DISPONIBLE', None, None, -2.326, 4),
    (42261, 'Jorge Domínguez', 180000, 0, 2, 'SIN_VALOR', False, None, False, None, None, None, None, None, 0.0, 9),
    (42802, 'Saliba', 1720000, -50000, 19, 'SIN_VALOR', False, None, False, 50.0, 30, 'TOCADO', None, None, -2.907, 55),
    (43207, 'Axel Tape', 170000, 0, 10, 'SIN_VALOR', False, None, False, 10.0, 20, 'DISPONIBLE', None, None, 0.0, 2),
    (18945, 'Koundé', 2940000, -20000, 3, 'MERCADO_DE_RIVAL', True, 14156489, False, None, None, None, None, None, -2.027, 130),
    (34111, 'Gerard Martín', 5250000, -20000, 3, 'MERCADO_DE_RIVAL', True, 14156489, False, 0.0, 40, 'DISPONIBLE', None, None, -0.19, 147),
    (1721, 'Manu Sánchez', 1640000, -30000, 10, 'MERCADO_DE_RIVAL', True, 14176382, False, 50.0, 50, 'DUDA', None, None, -1.198, 94),
    (42557, 'Adeyemi', 9250000, -50000, 3, 'MERCADO_DE_RIVAL', True, 14176382, False, 100.0, 30, 'DISPONIBLE', None, None, -0.808, 331),
    (12403, 'Iván Martín', 2770000, 0, 812, 'SUPERA_PRESUPUESTO', False, None, True, 90.0, 50, 'DISPONIBLE', 'XI_UPGRADE', 'ROSTER_FILL', 0.0, 131),
)
PRIMA_0111 = 2.32
PLANTILLA_0111 = (
    # (id, nombre, club, precio)
    (38433, 'Gulácsi', 19, 2330000),
    (23840, 'Juan Iglesias', 17, 3750000),
    (28115, 'Kike Salas', 17, 3300000),
    (1760, 'Chust', 75, 2500000),
    (29661, 'Olasagasti', 10, 2880000),
    (1969, 'Unai López', 70, 2740000),
    (41418, 'Dani Lorenzo', 65, 2010000),
    (41411, 'Ramón Enríquez', 65, 410000),
    (26271, 'Yamal', 3, 25310000),
    (35678, 'Roberto Fernández', None, 7240000),
    (12494, 'Boyé', 91, 5490000),
    (30493, 'Sergi Cardona', 19, 2100000),
    (1844, 'Gayà', None, 1760000),
    (35765, 'Angel Ortiz', 87, 190000),
    (14800, 'Pablo Ibáñez', 91, 2670000),
)
FICHAS_0111 = ((21, False), (15, True), (17, False), (14, False), (13, False),
               (17, False), (20, False), (14, False))
BOLSILLOS_0111 = {'available_budget': 447994, 'cash_budget': 0}
SEGUNDOS_0111 = 74887
SOLVENCIA_0111 = {
    'state': 'CUBIERTO_PERO_CADUCA', 'deficit': 7494776,
    'hours_to_solvency_deadline': 124.55,
    'real_deadline': '2026-11-06T20:45:00+01:00',
    'solvency_deadline': {
        'known': True, 'at': '2026-11-06T14:45:00+01:00', 'source': 'CALENDARIO',
        'text': ('el plazo, del calendario, es el 06/11 a las 14:45 -6 h antes del '
                 'cierre de la jornada, 06/11 20:45-: quedan 125 h (5,2 dias)'),
    },
}
SIN_DEUDA = {'state': 'SIN_DEUDA', 'deficit': 0}


# ============================================================
# LA VUELTA DEL 31/10 04:48 (reconstruida)
# ============================================================

DANI = (41418, 'Dani Lorenzo', 2_020_000, 10_000, 65, 'BID', False, None, False,
        80.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 35)
MACIA = (39357, 'Maciá', 690_000, 60_000, 19, 'BID', False, None, True,
         40.0, 20, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 2)
ORTIZ = (35765, 'Angel Ortiz', 190_000, 10_000, 87, 'BID', False, None, True,
         50.0, 30, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 5)
TABLERO_3110 = (DANI, MACIA, ORTIZ)
PUJA_DE_DANI = 2_025_051                       # el libro de pujas
SALDO_3110 = 1_299_975
PUJAS_3110 = {39357: 709_900, 35765: 219_900}  # la ronda, vivas
LIBRO_3110 = {"39357": 709_900, "35765": 219_900}
CATALOGO_3110 = {39357: (690_000, 60_000), 35765: (190_000, 10_000),
                 41418: (2_020_000, 10_000)}
COLCHON_3110 = 1_299_975 - 929_800 + int(0.92 * (690_000 + 190_000))   # 1.179.775
PLANTILLA_3110 = tuple(j for j in PLANTILLA_0111 if j[0] not in (41418, 35765, 23840))
BOLSILLOS_3110 = {'available_budget': 3 * SALDO_3110 - 929_800,
                  'cash_budget': SALDO_3110 - 929_800}
SEGUNDOS_3110 = 7_867                          # 03:48:53 UTC al reset de las 06:00 UTC
FICHAS_3110 = ((21, False), (12, True), (17, False), (14, False), (13, False),
               (17, False), (20, False), (14, False))
AHORA_3110 = datetime(2026, 10, 31, 3, 48, 53, tzinfo=timezone.utc)

# Sinteticos: uno barato que sube de verdad (+10.000 sobre 300.000: el
# tramo pide 9.300) y dos de 700.000 que suben +30.000 (piden 21.700).
BARATO = (90001, 'Barato', 300_000, 10_000, 5, 'BID', False, None, False,
          80.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 40)
PAREJA_A = (90002, 'Pareja A', 700_000, 30_000, 2, 'BID', False, None, False,
            80.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 40)
PAREJA_B = (90003, 'Pareja B', 700_000, 30_000, 13, 'BID', False, None, False,
            80.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 40)
DANI_SUBE = DANI[:3] + (30_000,) + DANI[4:]

# El calendario: la J11 empezo el 30/10 21:00 y la J12 empieza el vie
# 06/11 a las 21:00 de Madrid (20:00 UTC).
CALENDARIO = {"matchdays": [
    {"matchday": 11, "matches": [{"kickoff": "2026-10-30T21:00:00+01:00"},
                                 {"kickoff": "2026-11-01T18:30:00+01:00"},
                                 {"kickoff": "2026-11-02T21:00:00+01:00"}]},
    {"matchday": 12, "matches": [{"kickoff": "2026-11-06T21:00:00+01:00"},
                                 {"kickoff": "2026-11-08T18:30:00+01:00"},
                                 {"kickoff": "2026-11-09T21:00:00+01:00"}]},
    {"matchday": 13, "matches": [{"kickoff": "2026-11-20T21:00:00+01:00"}]},
]}
JUEVES_0511_0445 = datetime(2026, 11, 5, 3, 45, tzinfo=timezone.utc)    # 40,25 h
VIERNES_0611_0445 = datetime(2026, 11, 6, 3, 45, tzinfo=timezone.utc)   # 16,25 h


def _fila(t) -> dict:
    (pid, nombre, precio, sube, club, decision, fuera, vendedor, viva,
     titular, jerarquia, disponible, intent, via, ritmo, puntos) = t
    return {"id": pid, "name": nombre, "market_price": precio,
            "price_increment": sube, "team_id": club, "decision": decision,
            "outside_computer_market": fuera, "seller_id": vendedor,
            "has_live_bid": viva, "starter_probability": titular,
            "hierarchy_value": jerarquia, "availability": disponible,
            "intent": intent, "deployment": {"route": via},
            "market_gate": {"rate_percent_per_day": ritmo},
            "expected_points": puntos}


def _estado(tablero, bolsillos, segundos, solvencia, fichas,
            prima=PRIMA_0111, bloqueado=False) -> dict:
    return {
        "acquisition": {"targets": [_fila(t) for t in tablero],
                        "computer_premium": {"median_percent": prima}},
        "exposure": dict(bolsillos),
        "market_clock": {"seconds_to_reset": segundos},
        "rival_intelligence": {"managers": [
            {"roster_count": n, "is_us": us} for n, us in fichas]},
        "solvency_clock": copy.deepcopy(solvencia),
        "operations_locked": bloqueado,
        "phase": "NORMAL",
    }


def _foto(saldo, pujas, plantilla, catalogo=None) -> dict:
    """La foto de Biwenger con la forma que lee `leer_la_foto`."""
    status = {"maximumBid": 8_675_224}
    if saldo is not None:
        status["balance"] = saldo
    return {
        "league": {"user": {"id": YO}},
        "market": {
            "status": status,
            "sales": [],
            "offers": [
                {"id": 900_000 + pid, "from": {"id": YO}, "status": "waiting",
                 "amount": importe, "requestedPlayers": [{"id": pid}]}
                for pid, importe in (pujas or {}).items()
            ],
        },
        "my_team": [{"id": p, "name": n, "teamID": c, "price": v}
                    for p, n, c, v in plantilla],
        "catalog": {"data": {"players": {
            str(p): {"id": p, "price": v, "priceIncrement": s}
            for p, (v, s) in (catalogo or {}).items()}}},
    }


def _vuelta_3110(tablero=TABLERO_3110, bolsillos=BOLSILLOS_3110) -> dict:
    return _estado(tablero, bolsillos, SEGUNDOS_3110, SIN_DEUDA, FICHAS_3110)


FOTO_3110 = _foto(SALDO_3110, PUJAS_3110, PLANTILLA_3110, CATALOGO_3110)
FOTO_0111 = _foto(-4_714_876, {12403: 2_779_900}, PLANTILLA_0111)


# ============================================================
# LA BATERIA
# ============================================================

RICO = {'available_budget': 5_000_000, 'cash_budget': 1_500_000}


def _estados() -> list:
    """(nombre, estado, foto). Reales y sinteticos."""
    salida = []
    for segundos in (SEGUNDOS_0111, 7_651):
        for bolsillos in (BOLSILLOS_0111, RICO):
            for solvencia in (SOLVENCIA_0111, SIN_DEUDA, None):
                salida.append((f"0111 s={segundos} b={bolsillos['cash_budget']} "
                               f"r={(solvencia or {}).get('state')}",
                               _estado(TABLERO_0111, bolsillos, segundos, solvencia,
                                       FICHAS_0111), FOTO_0111))
    salida.append(("0111 bloqueado", _estado(TABLERO_0111, RICO, 7_651, SIN_DEUDA,
                                             FICHAS_0111, bloqueado=True), FOTO_0111))
    salida += [
        ("3110", _vuelta_3110(), FOTO_3110),
        ("3110 + barato", _vuelta_3110(TABLERO_3110 + (BARATO,)), FOTO_3110),
        ("3110 + pareja", _vuelta_3110(TABLERO_3110 + (PAREJA_A, PAREJA_B)), FOTO_3110),
        ("3110 sube", _vuelta_3110((DANI_SUBE, MACIA, ORTIZ)), FOTO_3110),
        ("3110 todos, rico", _vuelta_3110(TABLERO_3110 + (BARATO, PAREJA_A, PAREJA_B),
                                          RICO), FOTO_3110),
        ("3110 fuera de la ventana", _estado(TABLERO_3110, BOLSILLOS_3110, 9_000,
                                             SIN_DEUDA, FICHAS_3110), FOTO_3110),
        ("3110 sin foto", _vuelta_3110(), None),
        ("vacio", {}, {}),
        ("nada", None, None),
        ("basura", {"acquisition": "x", "exposure": 7, "market_clock": []}, {"my_team": 3}),
        ("filas basura", {**_vuelta_3110(), "acquisition": {
            "targets": [None, 3, {"id": "x"}, {}, _fila(DANI)],
            "computer_premium": {"median_percent": PRIMA_0111}}}, FOTO_3110),
    ]
    return salida


# Los entornos: todo quitado; los de la cesta que produccion tiene hoy
# puestos (sin `BORDALAS_SIN_SUBASTA`); esos mas los del dia que se quite
# (`BORDALAS_CESTA_SOLO_EL_SUELO`) y el cupo; el interruptor que la cierra;
# y la orden del gestor vetando a Dani y a la pareja A.
PRODUCCION = {"BORDALAS_REVENTA_SOLO_SI_JUEGA": "1", "BORDALAS_COMPRA_SOLO_SI_SUBE": "1",
              "BORDALAS_SOLVENCIA_POR_SU_PLAZO": "1"}
ENTORNOS = (
    ("apagado", {}, None),
    ("produccion", PRODUCCION, None),
    ("el suelo y el cupo", {**PRODUCCION, "BORDALAS_CESTA_SOLO_EL_SUELO": "1",
                            "BORDALAS_CUPO_POR_VENTANA": "1"}, None),
    ("sin subasta", {"BORDALAS_SIN_SUBASTA": "1", "BORDALAS_SIN_REVENTA": "1"}, None),
    ("la orden veta", PRODUCCION, (41418, 90002)),
)


def _llamadas(extra: dict | None = None) -> list:
    """Las llamadas de cada estado: el ciclo, la pantalla y sus variantes."""
    extra = dict(extra or {})
    return [
        lambda st, ft: sub.plan_desde_el_estado(st, ft, en_vivo=True, **extra),
        lambda st, ft: sub.plan_desde_el_estado(st, ft, en_vivo=False, max_pujas=1,
                                                ya_pujados=[41418], **extra),
        lambda st, ft: sub.plan_desde_el_estado(st, ft, True, 3, [1, 2, 3], **extra),
        lambda st, ft: sub.plan_del_reset(**sub.lectura_del_estado(st, ft), en_vivo=True),
    ]


def _huella(salida) -> str:
    crudo = json.dumps(salida, sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _resumen(huellas) -> str:
    return hashlib.sha256("".join(huellas).encode("ascii")).hexdigest()


def _huellas(interruptores: dict | None = None, extra: dict | None = None) -> list:
    """La huella de cada llamada, en cada entorno, sobre cada estado."""
    salida = []
    for _, entorno, veta in ENTORNOS:
        with _Interruptores({**entorno, **(interruptores or {})}), \
                _LaOrdenVeta(veta or ()) if veta else _Nada():
            for _, estado, foto in _estados():
                for llamada in _llamadas(extra):
                    salida.append(_huella(llamada(copy.deepcopy(estado),
                                                  copy.deepcopy(foto))))
    return salida


class _Nada:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


# ============================================================
# LO DE HOY: main, con la cesta sin tocar
# ============================================================
#
# La salida ENTERA de cada llamada de la bateria (`_huellas`), medida con
# la `la_subasta` de main ANTES de este cambio (main@a33b65e5, 01/11/2026):
# sha256 del JSON ordenado de cada una, y sha256 de todas seguidas. Una
# por version de Python (la leccion de la vuelta roja #2623: la vuelta
# corre en 3.13). Medidas con PYTHONHASHSEED 0, 3 y 11: salen iguales, y
# en las dos versiones sale la misma. Apagado, tiene que salir la misma,
# letra a letra. Si algun dia se cambia la cesta A PROPOSITO, se rehace con
# el interruptor apagado (`--medir`) y se dice en el commit.
HUELLAS_DE_MAIN = {
    (3, 11): "ee6e1bce903878634add53c9a7f9db7350aac4885ef7be57258e32f6a904421a",
    (3, 13): "ee6e1bce903878634add53c9a7f9db7350aac4885ef7be57258e32f6a904421a",
}
LLAMADAS_DE_LA_BATERIA = 480


# ============================================================
# EL LIBRO DE LA RONDA, EN UNA CARPETA TEMPORAL
# ============================================================

class _Libro:
    """`la_ronda.json` con `contenido`, en una carpeta temporal."""

    def __init__(self, contenido=None):
        self.contenido = LIBRO_3110 if contenido is None else contenido

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self._dir.name) / "la_ronda.json"
        self.ruta.write_text(json.dumps(self.contenido), encoding="utf-8")
        return self.ruta

    def __exit__(self, *_):
        self._dir.cleanup()
        return False


def _plan(estado, foto, entorno=PUESTO, ahora=AHORA_3110, calendario=CALENDARIO,
          libro=None, en_vivo=True) -> dict:
    with _Interruptores(entorno), _Libro(libro) as ruta:
        return sub.plan_desde_el_estado(
            copy.deepcopy(estado), copy.deepcopy(foto), en_vivo=en_vivo,
            ahora=ahora, calendario=calendario, libro_ruta=ruta)


def _ids(plan) -> list:
    return [int(b["id"]) for b in plan.get("bids") or []]


def _detalle(plan) -> dict:
    return plan.get("en_el_colchon") or {}


# ============================================================
# 1. NACE APAGADO, Y SE LEE EN UN SOLO SITIO
# ============================================================

def test_nace_apagado():
    assert sub.EN_EL_COLCHON_ENV == ENV
    with _Interruptores({ENV: None}):
        assert sub._en_el_colchon() is False
    for valor, puesto in (("1", True), ("true", True), ("si", True), ("yes", True),
                          (" 1 ", True), ("0", False), ("no", False), ("", False)):
        with _Interruptores({ENV: valor}):
            assert sub._en_el_colchon() is puesto, valor
    # Un interruptor sin frase para el dueño pone la verja en rojo el dia
    # que se enciende (leccion del 26/10).
    from src.telemetry.el_tablon import QUE_HACE
    assert str(QUE_HACE.get(ENV) or "").strip(), "sin frase en QUE_HACE"
    # Se lee en UN sitio, al llamarse: `la_subasta._en_el_colchon`.
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
    assert quien == {"src/analysis/la_subasta.py": "AL_LLAMARSE"}, quien
    # Y el modulo no hace nada al importarse: solo constantes y funciones.
    arbol = ast.parse((RAIZ / "src" / "analysis" / "la_subasta_en_el_colchon.py")
                      .read_text(encoding="utf-8"))
    for nodo in arbol.body:
        assert isinstance(nodo, (ast.Expr, ast.ImportFrom, ast.Import, ast.FunctionDef,
                                 ast.Assign, ast.AnnAssign)), ast.dump(nodo)[:80]
        if isinstance(nodo, ast.Expr):
            assert isinstance(nodo.value, ast.Constant), "solo el docstring"
        if isinstance(nodo, ast.Assign):
            assert isinstance(nodo.value, (ast.Constant, ast.Tuple)), ast.dump(nodo)[:80]


# ============================================================
# 2. APAGADO ES MAIN, BYTE A BYTE
# ============================================================

def test_apagado_es_main_byte_a_byte():
    esperada = HUELLAS_DE_MAIN.get(sys.version_info[:2])
    assert esperada is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    hoy = _huellas(APAGADO)
    assert len(hoy) == LLAMADAS_DE_LA_BATERIA, len(hoy)
    assert _resumen(hoy) == esperada, _resumen(hoy)

    # Lo que mueve el arreglo, dicho antes que la huella: apagado, la
    # vuelta del 31/10 sigue pujando por Dani lo que pujo.
    with _Interruptores(APAGADO):
        plan = sub.plan_desde_el_estado(_vuelta_3110(), copy.deepcopy(FOTO_3110),
                                        en_vivo=True)
    assert _ids(plan) == [41418] and plan["bids"][0]["bid"] == PUJA_DE_DANI
    assert plan["execute"] is True and "en_el_colchon" not in plan

    # Apagado, pasar la hora, el calendario y el libro no cambia nada, y
    # no corre ni una linea del modulo (uno que revienta no se nota).
    from src.analysis import la_subasta_en_el_colchon as colchon

    llamadas = []
    original = colchon.en_el_colchon

    def _espia(*args, **kwargs):
        llamadas.append(1)
        raise RuntimeError("apagado no se llama")

    colchon.en_el_colchon = _espia
    try:
        with _Libro() as ruta:
            con_todo = _huellas(APAGADO, {"ahora": VIERNES_0611_0445,
                                          "calendario": {}, "libro_ruta": ruta})
    finally:
        colchon.en_el_colchon = original
    assert llamadas == [], len(llamadas)
    assert con_todo == hoy


# ============================================================
# 3. ENCENDIDO
# ============================================================

def test_la_vuelta_del_3110_no_puja():
    # Apagado: Dani, 2.025.051, en vivo. Es lo que paso.
    apagado = _plan(_vuelta_3110(), FOTO_3110, entorno=APAGADO)
    assert _ids(apagado) == [41418] and apagado["committed"] == PUJA_DE_DANI
    assert apagado["execute"] is True

    # Encendido: no se puja. Dani subia +10.000 sobre 2.020.000 y su tramo
    # pide 22.220: no sube de verdad.
    puesto = _plan(_vuelta_3110(), FOTO_3110)
    assert _ids(puesto) == [] and puesto["execute"] is False, puesto["reason"]
    assert puesto["blocked_by"] == "NO_SUBE_DE_VERDAD", puesto["blocked_by"]
    assert puesto["committed"] == 0 and puesto["expected"] == 0
    assert puesto["slots_used"] == 0 and puesto["all_won"] == 0
    assert puesto["dropped_by_no_sube_de_verdad"] == 1
    assert "Dani Lorenzo" in puesto["reason"]
    # La jornada estaba lejos (160 h): no es el reloj.
    assert 160 < _detalle(puesto)["horas_a_la_jornada"] < 161

    # Y aunque subiera de verdad: no cabe en el colchon de la casa.
    sube = _plan(_vuelta_3110((DANI_SUBE, MACIA, ORTIZ)), FOTO_3110)
    assert _ids(sube) == [] and sube["execute"] is False
    assert sube["blocked_by"] == "SIN_COLCHON", sube["blocked_by"]
    assert _detalle(sube)["colchon"] == COLCHON_3110 == 1_179_775
    assert sube["dropped_by_colchon"] == 1 and sube["committed"] == 0
    assert "1.179.775" in sube["reason"] and "2.025.051" in sube["reason"], sube["reason"]
    # Apagado, esa tambien se pujaba.
    assert _ids(_plan(_vuelta_3110((DANI_SUBE, MACIA, ORTIZ)), FOTO_3110,
                      entorno=APAGADO)) == [41418]


def test_lo_barato_que_cabe_sigue():
    tablero = (DANI_SUBE, MACIA, ORTIZ, BARATO)
    apagado = _plan(_vuelta_3110(tablero), FOTO_3110, entorno=APAGADO)
    assert sorted(_ids(apagado)) == [41418, 90001]

    puesto = _plan(_vuelta_3110(tablero), FOTO_3110)
    assert _ids(puesto) == [90001], _ids(puesto)
    assert puesto["execute"] is True and puesto["blocked_by"] is None
    assert puesto["committed"] == 300_751 == puesto["bids"][0]["bid"]
    assert puesto["dropped_by_colchon"] == 1
    assert [f["id"] for f in _detalle(puesto)["fuera"]] == [41418]
    # Solo, con la J12 lejos y el mismo colchon: sale igual que apagado.
    solo = _plan(_vuelta_3110((MACIA, ORTIZ, BARATO)), FOTO_3110)
    solo_apagado = _plan(_vuelta_3110((MACIA, ORTIZ, BARATO)), FOTO_3110, entorno=APAGADO)
    assert _ids(solo) == _ids(solo_apagado) == [90001]
    for clave in ("execute", "bids", "committed", "expected", "all_won", "slots_used",
                  "worst_case", "blocked_by", "window"):
        assert solo[clave] == solo_apagado[clave], clave


def test_el_corte_de_las_40_horas():
    estado = _vuelta_3110((MACIA, ORTIZ, BARATO))
    jueves = _plan(estado, FOTO_3110, ahora=JUEVES_0511_0445)
    assert abs(_detalle(jueves)["horas_a_la_jornada"] - 40.25) < 1e-6
    assert _ids(jueves) == [90001] and jueves["execute"] is True

    viernes = _plan(estado, FOTO_3110, ahora=VIERNES_0611_0445)
    assert abs(_detalle(viernes)["horas_a_la_jornada"] - 16.25) < 1e-6
    assert _ids(viernes) == [] and viernes["execute"] is False
    assert viernes["blocked_by"] == "CERCA_DE_LA_JORNADA", viernes["blocked_by"]
    assert viernes["committed"] == 0 and "40 h" in viernes["reason"], viernes["reason"]

    # El borde: 40 h justas pasan; un minuto menos, no.
    cuarenta = datetime(2026, 11, 5, 4, 0, tzinfo=timezone.utc)
    assert _ids(_plan(estado, FOTO_3110, ahora=cuarenta)) == [90001]
    menos = _plan(estado, FOTO_3110, ahora=cuarenta + timedelta(minutes=1))
    assert menos["blocked_by"] == "CERCA_DE_LA_JORNADA" and _ids(menos) == []
    # Apagado, el viernes se pujaba.
    assert _ids(_plan(estado, FOTO_3110, entorno=APAGADO, ahora=VIERNES_0611_0445)) == [90001]


def test_sin_reloj_no_se_puja():
    estado = _vuelta_3110((MACIA, ORTIZ, BARATO))
    with tempfile.TemporaryDirectory() as d:
        no_existe = Path(d) / "laliga_calendar.json"
        pasado = {"matchdays": [{"matchday": 1, "matches": [
            {"kickoff": "2026-08-15T21:00:00+02:00"}]}]}
        for calendario in ({}, {"matchdays": []}, pasado, no_existe, "basura"):
            plan = _plan(estado, FOTO_3110, calendario=calendario)
            assert _ids(plan) == [] and plan["execute"] is False, calendario
            assert plan["blocked_by"] == "CERCA_DE_LA_JORNADA", plan["blocked_by"]
            assert _detalle(plan)["horas_a_la_jornada"] is None
            assert "no se sabe" in plan["reason"].lower(), plan["reason"]


def test_sin_colchon_no_se_puja():
    estado = _vuelta_3110((MACIA, ORTIZ, BARATO))
    sin_saldo = _foto(None, PUJAS_3110, PLANTILLA_3110, CATALOGO_3110)
    for foto in (None, {}, {"market": "x"}, sin_saldo):
        plan = _plan(estado, foto)
        assert _ids(plan) == [] and plan["execute"] is False, foto
        assert plan["blocked_by"] == "SIN_COLCHON", plan["blocked_by"]
        assert _detalle(plan)["colchon"] is None
    # Con saldo de sobra, la misma sale.
    rica = _foto(5_000_000, PUJAS_3110, PLANTILLA_3110, CATALOGO_3110)
    assert _ids(_plan(estado, rica)) == [90001]


def test_el_colchon_se_cuenta_acumulado():
    # Cada una cabe sola en 1.179.775; las dos juntas (1.403.502) no.
    for una in (PAREJA_A, PAREJA_B):
        assert _ids(_plan(_vuelta_3110((MACIA, ORTIZ, una)), FOTO_3110)) == [una[0]]
    estado = _vuelta_3110((MACIA, ORTIZ, PAREJA_A, PAREJA_B))
    apagado = _plan(estado, FOTO_3110, entorno=APAGADO)
    assert _ids(apagado) == [90002, 90003]
    puesto = _plan(estado, FOTO_3110)
    assert _ids(puesto) == [90002], _ids(puesto)
    assert puesto["committed"] == 701_751 and puesto["dropped_by_colchon"] == 1
    fuera = _detalle(puesto)["fuera"]
    assert [f["id"] for f in fuera] == [90003] and fuera[0]["colchon"] == COLCHON_3110
    # Con la ronda pujando menos, caben las dos.
    holgada = _foto(SALDO_3110 + 300_000, PUJAS_3110, PLANTILLA_3110, CATALOGO_3110)
    assert _ids(_plan(estado, holgada)) == [90002, 90003]


def test_encendido_las_cuentas_cuadran():
    estado = _vuelta_3110((DANI_SUBE, MACIA, ORTIZ, BARATO, PAREJA_A, PAREJA_B), RICO)
    for en_vivo in (True, False):
        plan = _plan(estado, FOTO_3110, en_vivo=en_vivo)
        pujas = plan["bids"]
        assert pujas, plan["reason"]
        assert plan["committed"] == sum(b["bid"] for b in pujas)
        assert plan["committed"] <= _detalle(plan)["colchon"]
        assert plan["expected"] == int(sum(float(b["expected_value"]) * float(b["win_odds"])
                                           for b in pujas))
        assert plan["all_won"] == int(sum(float(b["expected_value"]) for b in pujas))
        assert plan["slots_used"] == len(pujas)
        assert plan["worst_case"]["jugadores"] == len(PLANTILLA_3110) + len(pujas)
        assert plan["execute"] is en_vivo
        assert plan["blocked_by"] == (None if en_vivo else "SIN_LIVE")
        assert plan["reason"].startswith(f"{len(pujas)} puja(s) por "), plan["reason"]
        assert ("NO se ejecuta" in plan["reason"]) is (not en_vivo)
    # La orden del gestor sigue mandando, y antes que el colchon: el vetado
    # no ocupa sitio.
    with _LaOrdenVeta({90002}):
        plan = _plan(_vuelta_3110((MACIA, ORTIZ, PAREJA_A, PAREJA_B)), FOTO_3110)
    assert _ids(plan) == [90003] and plan["committed"] == 701_751
    # Sin pujas que mirar (la cesta ya estaba cerrada), el plan no cambia:
    # con `BORDALAS_SIN_SUBASTA` puesto y fuera de la ventana, lo mismo.
    fuera = _estado(TABLERO_3110, BOLSILLOS_3110, 9_000, SIN_DEUDA, FICHAS_3110)
    for estado, entorno, motivo in (
            (_vuelta_3110(), {"BORDALAS_SIN_SUBASTA": "1"}, "INTERRUPTOR"),
            (fuera, {}, "FUERA_DE_VENTANA")):
        cerrado = _plan(estado, FOTO_3110, entorno=entorno)
        assert cerrado["blocked_by"] == motivo, cerrado["blocked_by"]
        assert _plan(estado, FOTO_3110, entorno={**entorno, ENV: "1"}) == cerrado, motivo


# ============================================================
# 4. LOS DOS CAMINOS DE VERDAD
# ============================================================

def test_los_dos_caminos_pasan_por_el_colchon():
    # Del arbol: el ciclo y la pantalla llaman a `plan_desde_el_estado`, y
    # el colchon va DESPUES de la orden del gestor.
    for fichero, funcion in (("src/v10_full_autonomous_live.py", "_pujar_en_el_reset"),
                             ("src/telemetry/dashboard_state.py", "bloque_de_la_subasta")):
        arbol = ast.parse((RAIZ / fichero).read_text(encoding="utf-8"))
        cuerpo = next(n for n in ast.walk(arbol)
                      if isinstance(n, ast.FunctionDef) and n.name == funcion)
        llama = {getattr(h.func, "id", None) for h in ast.walk(cuerpo)
                 if isinstance(h, ast.Call)}
        assert "plan_desde_el_estado" in llama, funcion
    texto = (RAIZ / "src" / "analysis" / "la_subasta.py").read_text(encoding="utf-8")
    cuerpo = texto[texto.index("def plan_desde_el_estado("):texto.index("def para_la_pantalla(")]
    assert cuerpo.index("vetados()") < cuerpo.index("_en_el_colchon()")
    assert cuerpo.count("_en_el_colchon()") == 1


# El ciclo y la pantalla no reciben la hora: el colchon mira el reloj de
# verdad. Para que la guardia no lo mire (`test_el_reloj_de_las_guardias_v1`)
# ni dependa del dia en que se corre, la proxima jornada del calendario de la
# casa se pone lejisimos: el reloj pasa siempre y lo que se mira es el
# colchon. Las 40 h se miran arriba, con la hora pasada.
JORNADA_LEJANA = "2099-11-06T21:00:00+01:00"


def _la_casa(carpeta, libro=None) -> tuple:
    """El calendario y el libro de la ronda de la casa, en `carpeta`."""
    calendario = Path(carpeta) / "laliga_calendar.json"
    calendario.write_text(json.dumps({"matchdays": [{"matchday": 12, "matches": [
        {"kickoff": JORNADA_LEJANA}]}]}), encoding="utf-8")
    ruta = Path(carpeta) / "la_ronda.json"
    ruta.write_text(json.dumps(LIBRO_3110 if libro is None else libro), encoding="utf-8")
    return calendario, ruta


def _el_ciclo(estado, foto, entorno, libro=None) -> tuple:
    """`_pujar_en_el_reset` de verdad, con el escritor cambiado por uno que
    apunta. El calendario y el libro de la ronda, en una carpeta temporal
    (`_la_casa`)."""
    import src.actions.la_ronda_de_la_manana as ronda
    import src.actions.los_chollos as chollos
    import src.biwenger.write_client as escritura
    import src.intelligence.bid_outcome_ledger as libro_de_pujas
    import src.v10_full_autonomous_live as ciclo

    enviadas = []

    class _Escritor:
        def __init__(self, *a, **k):
            pass

        def place_bid(self, player_id, amount, seller_user_id=None, execute=False):
            enviadas.append((int(player_id), int(amount)))
            return {"sent": False}

    antes = (ciclo._estado_publicado, ciclo._anotar_en_el_libro,
             libro_de_pujas.pujados_desde, escritura.BiwengerWriteClient,
             chollos.CALENDARIO, ronda.LIBRO)
    with tempfile.TemporaryDirectory() as d:
        calendario, ruta = _la_casa(d, libro)
        try:
            ciclo._estado_publicado = lambda cycle: copy.deepcopy(estado)
            ciclo._anotar_en_el_libro = lambda enviadas: None
            libro_de_pujas.pujados_desde = lambda desde: []
            escritura.BiwengerWriteClient = _Escritor
            chollos.CALENDARIO, ronda.LIBRO = calendario, ruta
            with _Interruptores(entorno):
                plan = ciclo._pujar_en_el_reset({"snapshot": copy.deepcopy(foto)})
        finally:
            (ciclo._estado_publicado, ciclo._anotar_en_el_libro,
             libro_de_pujas.pujados_desde, escritura.BiwengerWriteClient,
             chollos.CALENDARIO, ronda.LIBRO) = antes
    return plan, enviadas


def _la_pantalla(estado, foto, entorno, libro=None) -> dict:
    import src.actions.la_ronda_de_la_manana as ronda
    import src.actions.los_chollos as chollos
    import src.telemetry.dashboard_state as pantalla

    antes = (pantalla.bid_outcome_summary, pantalla._libro_de_pujas,
             chollos.CALENDARIO, ronda.LIBRO)
    with tempfile.TemporaryDirectory() as d:
        calendario, ruta = _la_casa(d, libro)
        try:
            pantalla.bid_outcome_summary = lambda **k: {"available": False}
            pantalla._libro_de_pujas = lambda *a, **k: []
            chollos.CALENDARIO, ronda.LIBRO = calendario, ruta
            with _Interruptores(entorno):
                return pantalla.bloque_de_la_subasta(copy.deepcopy(estado),
                                                     copy.deepcopy(foto))
        finally:
            (pantalla.bid_outcome_summary, pantalla._libro_de_pujas,
             chollos.CALENDARIO, ronda.LIBRO) = antes


def test_el_ciclo_y_la_pantalla_ven_lo_mismo():
    sube = _vuelta_3110((DANI_SUBE, MACIA, ORTIZ))
    plan, enviadas = _el_ciclo(sube, FOTO_3110, APAGADO)
    assert enviadas == [(41418, PUJA_DE_DANI)], enviadas
    plan, enviadas = _el_ciclo(sube, FOTO_3110, PUESTO)
    assert enviadas == [] and plan["blocked_by"] == "SIN_COLCHON", plan.get("reason")

    con_barato = _vuelta_3110((DANI_SUBE, MACIA, ORTIZ, BARATO))
    plan, enviadas = _el_ciclo(con_barato, FOTO_3110, PUESTO)
    assert enviadas == [(90001, 300_751)], enviadas

    pantalla = _la_pantalla(sube, FOTO_3110, APAGADO)
    assert pantalla["would_bid"] is True and [b["id"] for b in pantalla["bids"]] == [41418]
    pantalla = _la_pantalla(sube, FOTO_3110, PUESTO)
    assert pantalla["would_bid"] is False and pantalla["bids"] == []
    assert pantalla["blocked_by"] == "SIN_COLCHON" and "1.179.775" in pantalla["reason"]
    pantalla = _la_pantalla(con_barato, FOTO_3110, PUESTO)
    assert [b["id"] for b in pantalla["bids"]] == [90001]
    assert pantalla["committed"] == 300_751 and pantalla["would_bid"] is True


# ============================================================
# 5. NUNCA LANZA
# ============================================================

def test_nunca_lanza():
    from src.analysis import la_subasta_en_el_colchon as colchon
    import src.actions.la_ronda_de_la_manana as ronda

    con_pujas = _plan(_vuelta_3110((MACIA, ORTIZ, BARATO)), FOTO_3110, entorno=APAGADO)
    assert con_pujas["bids"]
    # Basura en el plan o en la foto: nunca lanza y nunca deja una puja.
    for plan in (None, 7, "x", {}, {"bids": "x"}, {"bids": [None, 3, {}]},
                 {"bids": [{"id": "?", "bid": "mucho"}]}):
        salida = colchon.en_el_colchon(plan, FOTO_3110, ahora=AHORA_3110,
                                       calendario=CALENDARIO)
        assert isinstance(salida, dict)
        assert salida.get("execute") in (False, None) and not salida.get("bids"), plan
    for foto in (None, 7, "x", {"market": {"offers": "x"}}):
        with _Libro() as ruta:
            salida = colchon.en_el_colchon(con_pujas, foto, plantilla="x", ahora=AHORA_3110,
                                           calendario=CALENDARIO, libro_ruta=ruta)
        assert salida["execute"] is False and salida["bids"] == []
        assert salida["blocked_by"] == "SIN_COLCHON", salida["blocked_by"]
    # El colchon que revienta, o el reloj que revienta: no se puja.
    def _revienta(*a, **k):
        raise RuntimeError("revienta a proposito")

    for nombre in ("cabe_en_el_colchon", "horas_a_la_jornada", "HORAS_SIN_COMPRAR"):
        antes = getattr(ronda, nombre)
        setattr(ronda, nombre, _revienta if callable(antes) else "basura")
        try:
            with _Libro() as ruta:
                salida = colchon.en_el_colchon(con_pujas, FOTO_3110, ahora=AHORA_3110,
                                               calendario=CALENDARIO, libro_ruta=ruta)
        finally:
            setattr(ronda, nombre, antes)
        assert salida["execute"] is False and salida["bids"] == [], nombre
        assert salida["blocked_by"] in ("SIN_COLCHON", "CERCA_DE_LA_JORNADA"), nombre
        assert salida["reason"], nombre
    # Si el modulo no se puede cargar, encendido no se puja.
    antes = sys.modules.get("src.analysis.la_subasta_en_el_colchon")
    sys.modules["src.analysis.la_subasta_en_el_colchon"] = None
    try:
        plan = _plan(_vuelta_3110((MACIA, ORTIZ, BARATO)), FOTO_3110)
    finally:
        sys.modules["src.analysis.la_subasta_en_el_colchon"] = antes
    assert plan["execute"] is False and plan["bids"] == []
    assert plan["blocked_by"] == "SIN_COLCHON" and "No se pudo" in plan["reason"]
    # Y el interruptor que no se puede leer: el de la casa, apagado.
    class _OsQueRevienta:
        @property
        def environ(self):
            raise RuntimeError("revienta a proposito")

    import builtins
    original_import = builtins.__import__

    def _import(nombre, *a, **k):
        if nombre == "os":
            return _OsQueRevienta()
        return original_import(nombre, *a, **k)

    builtins.__import__ = _import
    try:
        assert sub._en_el_colchon() is False
    finally:
        builtins.__import__ = original_import


TESTS = [
    test_nace_apagado,
    test_apagado_es_main_byte_a_byte,
    test_la_vuelta_del_3110_no_puja,
    test_lo_barato_que_cabe_sigue,
    test_el_corte_de_las_40_horas,
    test_sin_reloj_no_se_puja,
    test_sin_colchon_no_se_puja,
    test_el_colchon_se_cuenta_acumulado,
    test_encendido_las_cuentas_cuadran,
    test_los_dos_caminos_pasan_por_el_colchon,
    test_el_ciclo_y_la_pantalla_ven_lo_mismo,
    test_nunca_lanza,
]


def medir() -> None:
    """La huella de la bateria, apagada, para `HUELLAS_DE_MAIN`."""
    with _Interruptores(APAGADO):
        hoy = _huellas(APAGADO)
    print(f"Python {sys.version_info[:2]}: {len(hoy)} llamadas, {_resumen(hoy)}")


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
