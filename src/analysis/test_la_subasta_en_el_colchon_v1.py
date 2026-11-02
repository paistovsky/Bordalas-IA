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
    6. Un solo colchon en la vuelta (los revisores, 01/11): la foto del
       colchon es la mas fresca (`post_action`, si el motor viejo ya
       escribio), lo del libro de pujas de la ventana que la foto no trae
       cuenta delante, una foto en la que no se reconocen nuestras pujas
       no deja pujar, y lo que la cesta pujo queda en la foto de la vuelta
       para la ronda que puja detras (cesta + ronda no pasan del colchon).
    7. Un solo colchon ENTRE PROCESOS (la revision de 634edf03, 01/11:
       FIX_FIRST). Con la vuelta entera (`run_full_autonomous_cycle`, la
       cesta de verdad y lo demas cambiado):
         - el estado de la vuelta lleva el bloque `subasta`, con `hechas`
           como las de la ronda, lo mismo que se reservo en la foto, cuente
           o no se sepa si entro, tambien sin pujar (SIN_COLCHON);
         - la mejora del once (su caja, su `maximumBid` y su `correr`), el
           cierre, la rotacion y el parte, que son otros procesos, lo ven
           como una puja de la ronda, y no dos veces si la foto del disco
           ya la trae;
         - `con_lo_pujado` baja `maximumBid` lo que sube lo comprometido y
           no baja nunca una puja viva;
         - sin pujar tambien se reserva lo de `sin_foto` y `de_otra_foto`,
           y nunca las del plan que no se mandaron;
         - apagado, el estado de la vuelta, la pantalla, el escritor, la
           foto que ven la orden, los chollos y la ronda, y lo que sacan la
           mejora, el cierre, la rotacion y el parte, son los de main:
           huella medida en main ANTES del cambio, en 3.11 y en 3.13.
    8. Las revisiones de adc4eaa4 (02/11: OK_TO_SWITCH_ON y SHIP_OFF):
         - la puja que Biwenger rechaza (un 4xx) no se reserva ni la
           cuenta nadie; lo que no se sabe (un 5xx, un 200 con pagina de
           mantenimiento) sigue contando;
         - lo del libro que la foto no trae (`sin_foto`) no baja
           `maximumBid` ni entra en la caja de la mejora ni del cierre
           (que venden), y la mejora no vuelve a pujar por ello;
         - con un 429 despues de la cesta, `main` deja un estado minimo
           con el bloque y la mejora y el cierre lo cuentan; apagado no
           escribe nada;
         - una puja de despues por el mismo jugador solo resta del
           `maximumBid` de la mejora lo que crece;
         - la cesta no se abre en el YAML sin el colchon y el suelo
           encendidos para su lector de verdad ("1" literal);
         - y las vueltas enteras no miran el reloj: con el reloj en 2100,
           la cesta puja igual.

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


class _LaHoraDelCiclo:
    """`la_subasta.plan_desde_el_estado` con la hora fija: el ciclo
    (`_pujar_en_el_reset`) no se la pasa y el colchon miraria el reloj de
    verdad (el revisor, 02/11: con el reloj en 2100 fallaban siete). El
    comienzo de la ventana (`pujas_desde`), tambien desde esa hora, como lo
    saca el ciclo. Apagado no se miran: las huellas no cambian."""

    def __init__(self, hora):
        self.hora = hora

    def __enter__(self):
        original, hora = sub.plan_desde_el_estado, self.hora

        def _con_la_hora(state, *a, **k):
            if k.get("ahora") is None:
                k["ahora"] = hora
            if k.get("pujas_desde") is not None:
                try:
                    segundos = int(((state or {}).get("market_clock") or {})
                                   .get("seconds_to_reset") or 0)
                except Exception:                   # noqa: BLE001
                    segundos = 0
                k["pujas_desde"] = hora - timedelta(
                    seconds=max(0, sub.VENTANA_MINUTOS * 60 - segundos))
            return original(state, *a, **k)

        self._antes = original
        sub.plan_desde_el_estado = _con_la_hora
        return self

    def __exit__(self, *_):
        sub.plan_desde_el_estado = self._antes
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
          libro=None, en_vivo=True, **extra) -> dict:
    with _Interruptores(entorno), _Libro(libro) as ruta:
        return sub.plan_desde_el_estado(
            copy.deepcopy(estado), copy.deepcopy(foto), en_vivo=en_vivo,
            ahora=ahora, calendario=calendario, libro_ruta=ruta,
            **copy.deepcopy(extra))


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
    # Y el que se enciende con el (el comentario del YAML: con
    # `BORDALAS_CESTA_SOLO_EL_SUELO`), tambien: sin frase, la verja del
    # encendido se pondria roja (el revisor, 01/11).
    assert str(QUE_HACE.get(sub.ENV_SOLO_EL_SUELO) or "").strip(), "el suelo, sin frase"
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
    assert _detalle(jueves)["sin_reloj"] is False
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
            # El codigo es el del encargo; el detalle dice que es el reloj
            # que falta y no la jornada que se acerca.
            assert _detalle(plan)["sin_reloj"] is True
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

    # UNA FOTO EN LA QUE NO SE RECONOCEN NUESTRAS PUJAS (el revisor, 01/11):
    # con saldo pero sin `yo` o sin la lista de ofertas, el colchon saldria
    # sin restarlas. Una puja viva nuestra de 1.000.000 deja el colchon en
    # 299.975: la pareja A (701.751) no cabe. Rota, antes cabia.
    pareja = _vuelta_3110((MACIA, ORTIZ, PAREJA_A))
    buena = _foto(SALDO_3110, {55555: 1_000_000}, PLANTILLA_3110, CATALOGO_3110)
    plan = _plan(pareja, buena)
    assert _ids(plan) == [] and plan["blocked_by"] == "SIN_COLCHON"
    assert _detalle(plan)["colchon"] == 299_975, _detalle(plan)
    rotas = []
    for quita in (("league",), ("league", "user"), ("market", "offers")):
        rota = copy.deepcopy(buena)
        donde = rota
        for clave in quita[:-1]:
            donde = donde[clave]
        donde.pop(quita[-1])
        rotas.append(rota)
    sin_lista = copy.deepcopy(buena)
    sin_lista["market"]["offers"] = None
    rotas.append(sin_lista)
    for rota in rotas:
        plan = _plan(pareja, rota)
        assert _ids(plan) == [] and plan["execute"] is False, rota.keys()
        assert plan["blocked_by"] == "SIN_COLCHON", plan["blocked_by"]
        assert "no deja ver nuestras pujas" in plan["reason"], plan["reason"]
        assert _detalle(plan)["colchon"] is None
        # Apagado, la cesta de main tal cual.
        assert _ids(_plan(pareja, rota, entorno=APAGADO)) == [90002]


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

    plan, enviadas, _ = _la_vuelta(estado, {"snapshot": copy.deepcopy(foto)}, entorno,
                                   libro)
    return plan, enviadas


LIBRO_DE_PUJAS_VACIO = {"version": "V1.0", "bids": {}}


def _la_vuelta(estado, cycle, entorno, libro=None, libro_de_pujas=None) -> tuple:
    """Lo mismo, con el `cycle` entero (`post_action` incluido) y el libro de
    pujas cambiado por `libro_de_pujas` (ni `data/`). Devuelve tambien el
    `cycle` como queda: lo que veran los que pujan detras."""
    import src.actions.la_ronda_de_la_manana as ronda
    import src.actions.los_chollos as chollos
    import src.biwenger.write_client as escritura
    import src.intelligence.bid_outcome_ledger as libro_de_pujas_mod
    import src.v10_full_autonomous_live as ciclo

    enviadas = []

    class _Escritor:
        def __init__(self, *a, **k):
            pass

        def place_bid(self, player_id, amount, seller_user_id=None, execute=False):
            enviadas.append((int(player_id), int(amount)))
            return {"sent": False}

    libro_falso = LIBRO_DE_PUJAS_VACIO if libro_de_pujas is None else libro_de_pujas
    antes = (ciclo._estado_publicado, ciclo._anotar_en_el_libro,
             libro_de_pujas_mod.pujados_desde, libro_de_pujas_mod.load_ledger,
             escritura.BiwengerWriteClient, chollos.CALENDARIO, ronda.LIBRO)
    with tempfile.TemporaryDirectory() as d:
        calendario, ruta = _la_casa(d, libro)
        try:
            ciclo._estado_publicado = lambda cycle: copy.deepcopy(estado)
            ciclo._anotar_en_el_libro = lambda enviadas: None
            libro_de_pujas_mod.pujados_desde = lambda desde: []
            libro_de_pujas_mod.load_ledger = lambda *a, **k: copy.deepcopy(libro_falso)
            escritura.BiwengerWriteClient = _Escritor
            chollos.CALENDARIO, ronda.LIBRO = calendario, ruta
            with _Interruptores(entorno), _LaHoraDelCiclo(AHORA_3110):
                plan = ciclo._pujar_en_el_reset(cycle)
        finally:
            (ciclo._estado_publicado, ciclo._anotar_en_el_libro,
             libro_de_pujas_mod.pujados_desde, libro_de_pujas_mod.load_ledger,
             escritura.BiwengerWriteClient, chollos.CALENDARIO, ronda.LIBRO) = antes
    return plan, enviadas, cycle


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
            with _Interruptores(entorno), _LaHoraDelCiclo(AHORA_3110):
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
    # Apagado, el bloque de siempre: sin las claves del colchon.
    for clave in ("dropped_by_colchon", "dropped_by_no_sube_de_verdad", "en_el_colchon"):
        assert clave not in pantalla, clave
    pantalla = _la_pantalla(sube, FOTO_3110, PUESTO)
    assert pantalla["would_bid"] is False and pantalla["bids"] == []
    assert pantalla["blocked_by"] == "SIN_COLCHON" and "1.179.775" in pantalla["reason"]
    # Encendido, el panel dice cuantas quito y por que (el revisor, 01/11).
    assert pantalla["dropped_by_colchon"] == 1, pantalla.get("dropped_by_colchon")
    assert pantalla["dropped_by_no_sube_de_verdad"] == 0
    assert pantalla["en_el_colchon"]["colchon"] == COLCHON_3110
    assert pantalla["en_el_colchon"]["foto"] == "LA_DE_LA_VUELTA"
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


# ============================================================
# 6. UN SOLO COLCHON EN LA VUELTA (los revisores, 01/11)
# ============================================================

# El motor viejo ya pujo en `run_cycle` (900.000 por el 77777): la foto de
# `post_action` lo trae y la de la vuelta no.
PUJA_DEL_EJECUTOR = {77777: 900_000}
FOTO_POST_3110 = _foto(SALDO_3110, {**PUJAS_3110, **PUJA_DEL_EJECUTOR}, PLANTILLA_3110,
                       CATALOGO_3110)


def _nuestras_en(foto) -> dict:
    from src.actions.la_orden_del_gestor import leer_la_foto

    return {pid: fila["amount"]
            for pid, fila in leer_la_foto(foto, YO)["nuestras_pujas"].items()}


def test_la_foto_mas_fresca_de_la_vuelta():
    pareja = _vuelta_3110((MACIA, ORTIZ, PAREJA_A))
    # Directo: con la foto de `post_action`, el colchon ya no es 1.179.775
    # sino 279.775, y la pareja A no cabe.
    plan = _plan(pareja, FOTO_3110, foto_del_colchon=FOTO_POST_3110)
    assert _ids(plan) == [] and plan["blocked_by"] == "SIN_COLCHON", plan["reason"]
    assert _detalle(plan)["colchon"] == COLCHON_3110 - 900_000 == 279_775
    assert _detalle(plan)["foto"] == "POST_ACTION"
    assert _detalle(plan)["de_otra_foto"] == [{"id": 77777, "amount": 900_000}]
    sin = _plan(pareja, FOTO_3110)
    assert _ids(sin) == [90002] and _detalle(sin)["foto"] == "LA_DE_LA_VUELTA"
    # Apagado no se mira: la de main, con foto fresca o sin ella.
    assert _plan(pareja, FOTO_3110, entorno=APAGADO, foto_del_colchon=FOTO_POST_3110) \
        == _plan(pareja, FOTO_3110, entorno=APAGADO)

    # El ciclo de verdad le pasa la de `post_action` (P3 del revisor).
    vuelta = {"snapshot": copy.deepcopy(FOTO_3110),
              "post_action": {"snapshot": copy.deepcopy(FOTO_POST_3110)}}
    plan, enviadas, _ = _la_vuelta(pareja, copy.deepcopy(vuelta), PUESTO)
    assert enviadas == [] and plan["blocked_by"] == "SIN_COLCHON", plan.get("reason")
    assert _detalle(plan)["colchon"] == 279_775
    _, enviadas, _ = _la_vuelta(pareja, copy.deepcopy(vuelta), APAGADO)
    assert enviadas == [(90002, 701_751)], enviadas
    # Sin `post_action` (no escribio nadie), la de la vuelta.
    _, enviadas, _ = _la_vuelta(pareja, {"snapshot": copy.deepcopy(FOTO_3110),
                                         "post_action": None}, PUESTO)
    assert enviadas == [(90002, 701_751)], enviadas


def test_el_libro_de_la_ventana_cuenta_delante():
    pareja = _vuelta_3110((MACIA, ORTIZ, PAREJA_A))
    abierta = AHORA_3110 - timedelta(minutes=4)

    def _entrada(pid, importe, cuando, outcome="PENDING"):
        return {"player_id": pid, "amount": importe, "outcome": outcome,
                "placed_at": cuando.isoformat(), "target_source": "SUBASTA_CARTERA"}

    libro = {"version": "V1.0", "bids": {
        # puesta en esta ventana y la foto aun no la trae: cuenta
        "a": _entrada(55555, 600_000, AHORA_3110 - timedelta(minutes=1)),
        # antes de abrir la ventana: la foto tendria que traerla
        "b": _entrada(55556, 900_000, AHORA_3110 - timedelta(hours=3)),
        # la foto ya la trae (Macia, de la ronda): no se cuenta dos veces
        "c": _entrada(39357, 709_900, AHORA_3110 - timedelta(minutes=1)),
        # ya resuelta
        "d": _entrada(55557, 900_000, AHORA_3110 - timedelta(minutes=1), "LOST"),
        # basura
        "e": {"player_id": "x", "amount": None}, "f": 7,
    }}
    plan = _plan(pareja, FOTO_3110, pujas_desde=abierta, libro_de_pujas=libro)
    # 1.179.775 - 600.000 = 579.775 < 701.751: no cabe.
    assert _ids(plan) == [] and plan["blocked_by"] == "SIN_COLCHON", plan["reason"]
    assert [f["id"] for f in _detalle(plan)["sin_foto"]] == [55555], _detalle(plan)
    assert _detalle(plan)["fuera"][0]["acumulado"] == 600_000
    assert "que la foto aun no trae (600.000 EUR)" in plan["reason"], plan["reason"]
    # Sin la de esta ventana, cabe; y sin `pujas_desde` (la pantalla) no se
    # mira el libro.
    del libro["bids"]["a"]
    assert _ids(_plan(pareja, FOTO_3110, pujas_desde=abierta, libro_de_pujas=libro)) == [90002]
    libro["bids"]["a"] = _entrada(55555, 600_000, AHORA_3110 - timedelta(minutes=1))
    assert _ids(_plan(pareja, FOTO_3110, libro_de_pujas=libro)) == [90002]

    # El ciclo de verdad le pasa el comienzo de la ventana y el libro de la
    # casa (aqui cambiado): una marca muy lejana cae dentro de la ventana y
    # una muy antigua no, sin mirar el reloj.
    lejana = datetime(2099, 1, 1, tzinfo=timezone.utc)
    antigua = datetime(2000, 1, 1, tzinfo=timezone.utc)
    for cuando, sale in ((lejana, []), (antigua, [(90002, 701_751)])):
        libro_casa = {"version": "V1.0", "bids": {"a": _entrada(55555, 600_000, cuando)}}
        plan, enviadas, _ = _la_vuelta(pareja, {"snapshot": copy.deepcopy(FOTO_3110)},
                                       PUESTO, libro_de_pujas=libro_casa)
        assert enviadas == sale, (cuando, enviadas, plan.get("reason"))


# La vuelta del revisor (misma_vuelta_2.py): la cesta puja por X y, en la
# misma vuelta, la ronda compraria Y al Computer.
X_CESTA = (90010, 'Barato que sube', 1_150_000, 40_000, 5, 'BID', False, None, False,
           80.0, 40, 'DISPONIBLE', 'SPECULATION', 'COMPUTER_RESALE', None, 40)
Y_RONDA = 90020


def _foto_de_la_misma_vuelta() -> dict:
    foto = copy.deepcopy(FOTO_3110)
    foto["market"]["sales"] = [
        {"player": {"id": X_CESTA[0]}, "user": None, "price": 1_150_000},
        {"player": {"id": Y_RONDA}, "user": None, "price": 1_000_000}]
    for pid in (X_CESTA[0], Y_RONDA):
        foto["catalog"]["data"]["players"][str(pid)] = {
            "id": pid, "price": X_CESTA[2] if pid == X_CESTA[0] else 1_000_000,
            "priceIncrement": 40_000, "status": "ok", "points": 40,
            "playedHome": 4, "playedAway": 4}
    return foto


def _la_ronda_detras(foto, libro=LIBRO_3110) -> list:
    """Lo que la ronda pujaria con esta foto (su `decidir`, con la cartera y
    a 40,25 h): [(jugador, importe)]."""
    import src.actions.la_ronda_de_la_manana as ronda
    from src.actions.la_orden_del_gestor import leer_la_foto

    f = leer_la_foto(foto, YO)
    fichas = {int(k): v for k, v in foto["catalog"]["data"]["players"].items()}
    acciones = ronda.decidir(
        mercado=dict(f["mercado"]), fichas=fichas, nuestras_pujas=f["nuestras_pujas"],
        plantilla=f["plantilla"], ofertas_del_computer=f["ofertas_del_computer"],
        en_venta=f["en_venta"], maximo_de_puja=f["maximo_de_puja"], minutos_al_reset=133,
        horas_jornada=40.25, libro=dict(libro), puede_escribir=True, cartera=True,
        saldo=f["saldo"])
    return [(a["player_id"], a["importe"]) for a in acciones if a["accion"] == "PUJAR"]


def test_lo_que_la_cesta_puja_lo_ve_la_ronda():
    import src.actions.la_ronda_de_la_manana as ronda

    estado = _vuelta_3110((MACIA, ORTIZ, X_CESTA))
    foto = _foto_de_la_misma_vuelta()
    # La ronda, sola, con esta foto, compraria Y (y X, que tambien sube).
    assert Y_RONDA in [p for p, _ in _la_ronda_detras(foto)], _la_ronda_detras(foto)

    # Encendido: la cesta puja por X y la foto de la vuelta queda con su puja.
    vuelta = {"snapshot": foto}
    plan, enviadas, despues = _la_vuelta(estado, vuelta, PUESTO)
    assert [p for p, _ in enviadas] == [X_CESTA[0]], (enviadas, plan.get("reason"))
    puja = enviadas[0][1]
    assert despues["snapshot"] is not foto, "la foto de la vuelta no se cambio"
    assert _nuestras_en(despues["snapshot"]) == {**PUJAS_3110, X_CESTA[0]: puja}
    assert _nuestras_en(foto) == PUJAS_3110, "la foto vieja no se toca"
    # Y la ronda que puja detras ya no ve el colchon entero: no compra.
    libro = LIBRO_3110
    f = __import__("src.actions.la_orden_del_gestor", fromlist=["x"]).leer_la_foto(
        despues["snapshot"], YO)
    fichas = {int(k): v for k, v in despues["snapshot"]["catalog"]["data"]["players"].items()}
    queda = ronda.el_colchon(f["saldo"], f["nuestras_pujas"], libro, f["plantilla"], fichas)
    assert queda == COLCHON_3110 - puja, queda
    assert _la_ronda_detras(despues["snapshot"]) == []
    # Lo vivo despues de la vuelta no pasa del colchon de la casa.
    assert puja <= COLCHON_3110

    # Apagado: la foto de la vuelta es la misma (el objeto), y la ronda
    # volveria a comprar Y.
    vuelta = {"snapshot": _foto_de_la_misma_vuelta()}
    original = vuelta["snapshot"]
    plan, enviadas, despues = _la_vuelta(estado, vuelta, APAGADO)
    assert [p for p, _ in enviadas] == [X_CESTA[0]], enviadas
    assert despues["snapshot"] is original
    assert Y_RONDA in [p for p, _ in _la_ronda_detras(despues["snapshot"])]

    # Lo que el colchon conto sin estar en la foto de la vuelta (la puja del
    # ejecutor en `post_action`, la del libro) tambien queda: la ronda la
    # tiene que ver igual.
    pareja = _vuelta_3110((MACIA, ORTIZ, PAREJA_A))
    post = _foto(SALDO_3110, {**PUJAS_3110, 77777: 100_000}, PLANTILLA_3110, CATALOGO_3110)
    libro_casa = {"version": "V1.0", "bids": {"z": {
        "player_id": 66666, "amount": 50_000, "outcome": "PENDING",
        "placed_at": "2099-01-01T00:00:00+00:00"}}}
    plan, enviadas, despues = _la_vuelta(
        pareja, {"snapshot": copy.deepcopy(FOTO_3110), "post_action": {"snapshot": post}},
        PUESTO, libro_de_pujas=libro_casa)
    assert enviadas == [(90002, 701_751)], (enviadas, plan.get("reason"))
    assert _nuestras_en(despues["snapshot"]) == {
        **PUJAS_3110, 77777: 100_000, 66666: 50_000, 90002: 701_751}

    # `con_lo_pujado`, sola: la que ya estaba cambia su importe, la nueva se
    # apunta con `id` None; sin `yo` o sin ofertas, la misma foto.
    from src.analysis.la_subasta_en_el_colchon import con_lo_pujado

    nueva = con_lo_pujado(FOTO_3110, [(39357, 750_000), (5, 10), ("x", 3), (6, -1)])
    assert _nuestras_en(nueva) == {39357: 750_000, 35765: 219_900, 5: 10}
    assert [o for o in nueva["market"]["offers"] if o.get("id") is None][0][
        "reservada_por"] == "LA_SUBASTA_EN_EL_COLCHON"
    assert _nuestras_en(FOTO_3110) == PUJAS_3110
    for rota in ({}, None, {"league": {}}, {"league": {"user": {"id": YO}}, "market": {}}):
        assert con_lo_pujado(rota, [(5, 10)]) is rota
    assert con_lo_pujado(FOTO_3110, []) is FOTO_3110


# ============================================================
# 7. UN SOLO COLCHON ENTRE PROCESOS (revision de 634edf03, 01/11)
# ============================================================
#
# La mejora del once y la rotacion (que pujan) y el cierre y el parte (en
# sus cuentas) corren DESPUES en el mismo workflow, en otros procesos: leen
# la foto del disco (de antes de la cesta) y el estado de v10. Aqui la
# vuelta entera (`run_full_autonomous_cycle`) corre con la cesta de verdad
# y todo lo demas cambiado; el estado se escribe en una carpeta temporal y
# se lee como lo leen ellos. Ni red, ni `data/`, ni el reloj: la hora del
# estado es fija.

RUN_ID = "la-vuelta-del-colchon"
LA_HORA_DEL_ESTADO = datetime(2026, 11, 5, 3, 45, tzinfo=timezone.utc)
AHORA_DESPUES = LA_HORA_DEL_ESTADO + timedelta(minutes=5)
PUJA_DE_LA_PAREJA = 701_751
# Lo que dejan en el estado los demas pasos de la vuelta (cambiados): la
# orden puja por Ivan y cobra a Pablo, la revision retira a Ortiz y la
# ronda puja por el 4242.
LO_DE_LOS_DEMAS = {
    "orden": {"hechas": [
        {"accion": "PUJAR", "player_id": 12403, "importe": 2_779_900, "exito": True},
        {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 30, "importe": 2_505_300,
         "exito": True}]},
    "revision": {"retiradas": [{"player_id": 35765, "exito": True}]},
    "ronda": {"hechas": [{"accion": "PUJAR", "player_id": 4242, "importe": 10_000,
                          "exito": True, "ronda": True}]},
}
# Una puja del libro en esta ventana que la foto aun no trae (`sin_foto`).
LIBRO_DE_LA_VENTANA = {"version": "V1.0", "bids": {"z": {
    "player_id": 66666, "amount": 50_000, "outcome": "PENDING",
    "placed_at": "2099-01-01T00:00:00+00:00"}}}


def _lo_que_ve(cycle) -> dict:
    """Nuestras pujas y el `maximumBid` de `cycle["snapshot"]`."""
    try:
        from src.actions.la_orden_del_gestor import leer_la_foto

        foto = leer_la_foto((cycle or {}).get("snapshot"), YO)
        return {"pujas": {str(k): v["amount"] for k, v in sorted(foto["nuestras_pujas"].items())},
                "maximo": foto["maximo_de_puja"]}
    except Exception as error:                      # noqa: BLE001
        return {"error": type(error).__name__}


def _la_vuelta_entera(estado, cycle, entorno, libro_de_pujas=None, veta=None,
                      demas=None, *, escritor=None, buy=None, por_main=False,
                      de_antes=None) -> dict:
    """
    `run_full_autonomous_cycle` con la cesta de verdad (`_pujar_en_el_reset`)
    y lo demas cambiado: `run_cycle` devuelve `cycle`; BUY, posiciones,
    contraofertas, carril, escaparate, renovacion y racha no hacen nada; la
    orden, la revision, los chollos y la ronda apuntan la foto que ven y
    dejan `demas` (por defecto, nada). El escritor apunta: la puja par
    entra; la impar revienta (no se sabe si entro); con `escritor`
    (jugador, importe) -> lo que contesta. `buy`, el BUY de v10 (por
    defecto no escribe). Con `por_main`, por `main()` (la salida del 429)
    y con el estado de otra vuelta ya en disco (`de_antes`). La hora del
    colchon, fija (`_LaHoraDelCiclo`). El estado, en una carpeta temporal.
    Devuelve {texto, pantalla, enviadas, cycle, vistos, rc}.
    """
    import contextlib
    import io

    import src.actions.la_orden_del_gestor as orden
    import src.actions.la_racha as racha
    import src.actions.la_revision_de_pujas as revision
    import src.actions.la_ronda_de_la_manana as ronda
    import src.actions.los_chollos as chollos
    import src.biwenger.write_client as escritura
    import src.intelligence.bid_outcome_ledger as libro_mod
    import src.v10_full_autonomous_live as ciclo

    demas = demas or {}
    enviadas, vistos = [], {}

    class _Escritor:
        def __init__(self, *a, **k):
            pass

        def place_bid(self, player_id, amount, seller_user_id=None, execute=False):
            enviadas.append((int(player_id), int(amount)))
            if escritor is not None:
                return escritor(int(player_id), int(amount))
            if int(player_id) % 2:
                raise RuntimeError("se corta la red")
            return {"sent": True, "success": True, "http_status": 200}

    class _LaHora(datetime):
        @classmethod
        def now(cls, tz=None):
            return LA_HORA_DEL_ESTADO if tz is None else LA_HORA_DEL_ESTADO.astimezone(tz)

    def _paso(nombre):
        def correr(cycle, *a, **k):
            vistos[nombre] = _lo_que_ve(cycle)
            return {"motivo": "CAMBIADO", "acciones": [], "avisos": [], "hechas": [],
                    "retiradas": [], **copy.deepcopy(demas.get(nombre) or {})}
        return correr

    libro_falso = LIBRO_DE_PUJAS_VACIO if libro_de_pujas is None else libro_de_pujas
    pantalla = io.StringIO()
    texto, rc = None, None
    with tempfile.TemporaryDirectory() as d:
        calendario, ruta = _la_casa(d)
        if de_antes is not None:
            (Path(d) / "v10_full_autonomous_status.json").write_text(
                json.dumps(de_antes), encoding="utf-8")
        cambios = [
            (ciclo, "run_cycle", lambda **k: cycle),
            (ciclo, "_estado_publicado", lambda c: copy.deepcopy(estado)),
            (ciclo, "_anotar_en_el_libro", lambda x: None),
            (ciclo, "_renovar_en_la_ventana", lambda c: {"available": False}),
            (ciclo, "build_controlled_run", buy or (lambda **k: {"writes_biwenger": False})),
            (ciclo, "print_controlled_buy", lambda *a, **k: None),
            (ciclo, "_publicar_peticiones", lambda: None),
            (ciclo, "sync_position_manager", lambda **k: {"board": {}}),
            (ciclo, "print_position_manager", lambda *a, **k: None),
            (ciclo, "sync_counter_repricing", lambda **k: {"board": {}}),
            (ciclo, "print_counter_repricing", lambda *a, **k: None),
            (ciclo, "_correr_el_carril", lambda c, a: {"bids": []}),
            (ciclo, "_llenar_el_escaparate", lambda c, a: {"listed": []}),
            (ciclo, "_verify_v10_write", lambda a: {"attempted": False}),
            (ciclo, "STATUS_PATH", Path(d) / "v10_full_autonomous_status.json"),
            (ciclo, "datetime", _LaHora),
            (libro_mod, "pujados_desde", lambda desde: []),
            (libro_mod, "load_ledger", lambda *a, **k: copy.deepcopy(libro_falso)),
            (escritura, "BiwengerWriteClient", _Escritor),
            (chollos, "CALENDARIO", calendario),
            (ronda, "LIBRO", ruta),
            # Sin `config/` ni reloj (con la orden apagada ya sale vacio;
            # `veta` lo cambia dentro).
            (orden, "vetados", lambda *a, **k: set()),
            (orden, "correr", _paso("orden")),
            (revision, "correr", _paso("revision")),
            (chollos, "correr", _paso("chollos")),
            (ronda, "correr", _paso("ronda")),
            (racha, "cobrar", lambda c: {"racha": None, "motivo": "CAMBIADA"}),
        ]
        antes = [(modulo, nombre, getattr(modulo, nombre)) for modulo, nombre, _ in cambios]
        run_id_antes = os.environ.get("GITHUB_RUN_ID")
        try:
            for modulo, nombre, valor in cambios:
                setattr(modulo, nombre, valor)
            os.environ["GITHUB_RUN_ID"] = RUN_ID
            with _Interruptores(entorno), \
                    (_LaOrdenVeta(veta) if veta else _Nada()), \
                    _LaHoraDelCiclo(LA_HORA_DEL_ESTADO), \
                    contextlib.redirect_stdout(pantalla):
                if por_main:
                    rc = ciclo.main()
                else:
                    ciclo.run_full_autonomous_cycle()
            estado_ruta = Path(d) / "v10_full_autonomous_status.json"
            texto = estado_ruta.read_text(encoding="utf-8") if estado_ruta.exists() else None
        finally:
            for modulo, nombre, valor in antes:
                setattr(modulo, nombre, valor)
            if run_id_antes is None:
                os.environ.pop("GITHUB_RUN_ID", None)
            else:
                os.environ["GITHUB_RUN_ID"] = run_id_antes
    return {"texto": texto, "pantalla": pantalla.getvalue(), "enviadas": enviadas,
            "cycle": cycle, "vistos": vistos, "rc": rc}


def _la_cesta(estado=None, foto=None, post=None, entorno=PUESTO, libro_de_pujas=None,
              demas=None, **como) -> tuple:
    """La vuelta entera de la pareja A (por defecto): (estado de v10 leido
    del disco, la vuelta). `como`: lo de `_la_vuelta_entera` (escritor,
    buy, por_main, de_antes)."""
    cycle = {"snapshot": copy.deepcopy(FOTO_3110 if foto is None else foto)}
    if post is not None:
        cycle["post_action"] = {"snapshot": copy.deepcopy(post)}
    vuelta = _la_vuelta_entera(_vuelta_3110((MACIA, ORTIZ, PAREJA_A)) if estado is None
                               else estado, cycle, entorno, libro_de_pujas, demas=demas,
                               **como)
    assert vuelta["texto"], vuelta["pantalla"][-400:]
    return json.loads(vuelta["texto"]), vuelta


def _importes(foto) -> dict:
    """{jugador: importe} de las pujas vivas de una foto ya leida."""
    return {pid: fila["amount"] for pid, fila in (foto.get("nuestras_pujas") or {}).items()}


def _foto_fresca() -> dict:
    """La foto que se sacaria DESPUES de la cesta (una escritura de v10 la
    refresca antes de la orden): la puja de la pareja A con su `id` de
    verdad y el `maximumBid` ya bajado."""
    foto = _foto(SALDO_3110, {**PUJAS_3110, 90002: PUJA_DE_LA_PAREJA}, PLANTILLA_3110,
                 CATALOGO_3110)
    foto["market"]["status"]["maximumBid"] -= PUJA_DE_LA_PAREJA
    return foto


def test_el_estado_de_la_vuelta_lleva_la_cesta():
    # Encendido: la cesta puja 701.751 por la pareja A y el estado de la
    # vuelta lo dice, antes del carril y de la revision (el cierre lee los
    # bloques en orden: lo que se retire despues tiene que ir despues).
    estado, vuelta = _la_cesta()
    assert vuelta["enviadas"] == [(90002, PUJA_DE_LA_PAREJA)], vuelta["enviadas"]
    assert "subasta" in estado, f"el estado no lleva la cesta: {list(estado)}"
    claves = list(estado)
    assert claves.index("subasta") < claves.index("carril") < claves.index("revision_de_pujas")
    hechas = estado["subasta"]["hechas"]
    assert [(h["accion"], h["player_id"], h["importe"], h["exito"]) for h in hechas] == [
        ("PUJAR", 90002, PUJA_DE_LA_PAREJA, True)], hechas
    # La forma de las `hechas` de la ronda (`la_orden_del_gestor.ejecutar`).
    for clave in ("accion", "player_id", "importe", "sustituye", "enviada", "exito",
                  "http_status"):
        assert clave in hechas[0], clave
    assert hechas[0]["sustituye"] is None and hechas[0]["subasta"] is True
    assert hechas[0]["enviada"] is True and hechas[0]["http_status"] == 200
    # Lo mismo que se reservo en la foto de la vuelta.
    assert _nuestras_en(vuelta["cycle"]["snapshot"]) == {**PUJAS_3110, 90002: PUJA_DE_LA_PAREJA}
    assert estado["subasta"]["reservado"] == PUJA_DE_LA_PAREJA

    # La que revienta (no se sabe si entro) cuenta igual, con su error.
    todos = _vuelta_3110((MACIA, ORTIZ, BARATO, PAREJA_A))
    estado, vuelta = _la_cesta(todos)
    assert sorted(vuelta["enviadas"]) == [(90001, 300_751), (90002, PUJA_DE_LA_PAREJA)], \
        vuelta["enviadas"]
    por_jugador = {h["player_id"]: h for h in estado["subasta"]["hechas"]}
    assert {p: h["importe"] for p, h in por_jugador.items()} == dict(vuelta["enviadas"])
    assert all(h["exito"] is True for h in por_jugador.values())
    assert por_jugador[90001]["enviada"] is False and "se corta la red" in por_jugador[90001]["error"]
    assert _nuestras_en(vuelta["cycle"]["snapshot"]) == {**PUJAS_3110, **dict(vuelta["enviadas"])}

    # Sin pujar (SIN_COLCHON: el motor viejo ya pujo 900.000 en `post_action`)
    # y con una del libro de esta ventana que la foto no trae: el bloque
    # lleva la del motor viejo, marcada, y la del libro aparte (02/11: no va
    # a ninguna caja); la foto de la vuelta, las dos.
    estado, vuelta = _la_cesta(post=FOTO_POST_3110, libro_de_pujas=LIBRO_DE_LA_VENTANA)
    assert vuelta["enviadas"] == [], vuelta["enviadas"]
    assert [(h["player_id"], h["importe"], h["reservada"], h["exito"], h["enviada"])
            for h in estado["subasta"]["hechas"]] == [
        (77777, 900_000, "DE_OTRA_FOTO", True, False)], estado["subasta"]["hechas"]
    assert estado["subasta"]["de_otra_foto"] == [{"id": 77777, "amount": 900_000}]
    assert estado["subasta"]["sin_foto"] == [{"id": 66666, "amount": 50_000}]
    assert estado["subasta"]["reservado"] == 900_000
    assert _nuestras_en(vuelta["cycle"]["snapshot"]) == {
        **PUJAS_3110, **PUJA_DEL_EJECUTOR, 66666: 50_000}

    # Apagado no hay bloque.
    estado, _ = _la_cesta(entorno=APAGADO)
    assert "subasta" not in estado, list(estado)


def test_la_mejora_ve_la_cesta_despues_de_la_vuelta():
    from src.actions import el_cierre_de_la_jornada as cierre
    from src.actions import el_parte_vende as parte
    from src.actions import la_mejora_del_once as mejora
    from src.actions import la_rotacion as rotacion
    from src.actions.la_orden_del_gestor import leer_la_foto
    from src.analysis.la_subasta_en_el_colchon import con_lo_pujado

    v10, _ = _la_cesta()
    # La foto del disco es de ANTES de la cesta; la de verdad, con su puja.
    disco = leer_la_foto(copy.deepcopy(FOTO_3110), YO)
    de_verdad = leer_la_foto(con_lo_pujado(FOTO_3110, [(90002, PUJA_DE_LA_PAREJA)]), YO)
    real = SALDO_3110 - 929_800 - PUJA_DE_LA_PAREJA
    assert mejora.la_caja(de_verdad) == real == -331_576

    # LA MEJORA (la revision: veia 370.175 y el `maximumBid` entero).
    ev = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera=True)
    assert ev["descartado"] is None, ev["descartado"]
    assert ev["pujas"] == {90002: PUJA_DE_LA_PAREJA}, ev
    assert ev["gastado"] == PUJA_DE_LA_PAREJA and 90002 in ev["ya_pujados"]
    assert mejora.la_caja(disco, esta_vuelta=ev) == real, mejora.la_caja(disco, esta_vuelta=ev)
    assert disco["maximo_de_puja"] - ev["gastado"] == de_verdad["maximo_de_puja"] \
        == 8_675_224 - PUJA_DE_LA_PAREJA
    vacio = dict(liga={}, orden={}, libro={}, solos=set(), inventario=set())
    assert mejora.la_caja_de_la_jornada(disco, esta_vuelta=ev, **vacio) \
        == mejora.la_caja_de_la_jornada(de_verdad, **vacio)
    # Cuenta entera: no se revende sola (la ronda, con la cartera, igual).
    assert 90002 not in ev["solas"]

    # EL CIERRE, LA ROTACION Y EL PARTE: todos los bloques con `hechas`.
    vc = cierre.lo_de_esta_vuelta(v10)
    assert {p: f["amount"] for p, f in cierre.las_pujas_vivas(disco, vc).items()} \
        == {**PUJAS_3110, 90002: PUJA_DE_LA_PAREJA}
    vr = rotacion.lo_de_esta_vuelta(v10, None, None, AHORA_DESPUES, RUN_ID, None)
    # (sin fichero de la vuelta de la mejora ni del cierre: lo dice, y el
    # estado de v10 si cuenta)
    assert vr["pujas"] == {90002: PUJA_DE_LA_PAREJA}, vr
    assert not [d for d in vr["descartados"] if d.startswith("v10")], vr["descartados"]
    vp = parte.lo_vendido_y_publicado(v10, None, None, AHORA_DESPUES, RUN_ID)
    assert vp["vendidos"] == set() and vp["listados"] == set(), vp
    assert not [d for d in vp["descartados"] if d.startswith("v10")], vp["descartados"]

    # COMO UNA PUJA DE LA RONDA: la misma fila en el bloque `ronda` da lo
    # mismo en la mejora (con la cartera, la de produccion), el cierre y la
    # rotacion.
    como_ronda = {k: v for k, v in v10.items() if k != "subasta"}
    como_ronda["ronda"] = {"hechas": [{**h, "ronda": True} for h in v10["subasta"]["hechas"]]}
    er = mejora.lo_de_esta_vuelta(como_ronda, AHORA_DESPUES, RUN_ID, cartera=True)
    for clave in ("pujas", "gastado", "ya_pujados", "solas", "cobros", "canceladas"):
        assert er[clave] == ev[clave], clave
    assert cierre.lo_de_esta_vuelta(como_ronda) == vc
    assert rotacion.lo_de_esta_vuelta(como_ronda, None, None, AHORA_DESPUES, RUN_ID, None) == vr

    # NI DOS VECES: si la foto del disco ya la trae (una foto sacada
    # despues de la cesta), la mejora no la resta otra vez del
    # `maximumBid` ni de la caja, y el cierre la cuenta una vez.
    fresca = leer_la_foto(_foto_fresca(), YO)
    ef = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera=True,
                                  vistas=_importes(fresca))
    assert ef["gastado"] == 0 and ef["pujas"] == {} and 90002 in ef["ya_pujados"], ef
    assert mejora.la_caja(fresca, esta_vuelta=ef) == mejora.la_caja(fresca) == real
    vivas = cierre.las_pujas_vivas(fresca, vc)
    assert sum(f["amount"] for f in vivas.values()) == 929_800 + PUJA_DE_LA_PAREJA
    # Y si la foto la trae mas baja (otra puja vieja por el mismo), solo lo
    # que sube; la mas alta de la foto no baja.
    ev_baja = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera=True,
                                       vistas={90002: 500_000})
    assert ev_baja["gastado"] == PUJA_DE_LA_PAREJA - 500_000
    ev_alta = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera=True,
                                       vistas={90002: 900_000})
    assert ev_alta["gastado"] == 0 and ev_alta["pujas"] == {}

    # LA MEJORA ENTERA (su `correr`, con el `_correr` de su guardia: foto,
    # panel, libros y escritor suyos). La puja de la cesta baja lo
    # disponible y la caja entera, como una de la orden; con la foto que ya
    # la trae, el disponible es el de la foto.
    from src.analysis.test_la_mejora_del_once_v1 import _correr, _hace

    def _la_mejora(bloques, pujas=None):
        v = {"timestamp": _hace(5), **bloques}
        s, _, _ = _correr([40], [41], [40], con_calendario=True, v10=v, pujas=pujas)
        return s["plan"]

    fila = {k: v for k, v in v10["subasta"]["hechas"][0].items() if k != "subasta"}
    sin = _la_mejora({})
    con = _la_mejora({"subasta": v10["subasta"]})
    de_la_orden = _la_mejora({"orden_del_gestor": {"hechas": [fila]}})
    assert con["disponible"] == sin["disponible"] - PUJA_DE_LA_PAREJA, (con, sin)
    assert con["caja"] == sin["caja"] - PUJA_DE_LA_PAREJA, (con, sin)
    assert (con["caja"], con["disponible"]) == (de_la_orden["caja"], de_la_orden["disponible"])
    en_la_foto = _la_mejora({"subasta": v10["subasta"]}, pujas={90002: PUJA_DE_LA_PAREJA})
    sola_la_foto = _la_mejora({}, pujas={90002: PUJA_DE_LA_PAREJA})
    assert (en_la_foto["caja"], en_la_foto["disponible"]) == \
        (sola_la_foto["caja"], sola_la_foto["disponible"]), (en_la_foto, sola_la_foto)


def test_con_lo_pujado_baja_el_maximo_de_puja():
    from src.actions import la_orden_del_gestor as orden
    from src.analysis.la_subasta_en_el_colchon import con_lo_pujado

    maximo = FOTO_3110["market"]["status"]["maximumBid"]
    nueva = con_lo_pujado(FOTO_3110, [(90002, PUJA_DE_LA_PAREJA)])
    assert nueva["market"]["status"]["maximumBid"] == maximo - PUJA_DE_LA_PAREJA
    assert FOTO_3110["market"]["status"]["maximumBid"] == maximo, "la foto vieja no se toca"
    # La que ya estaba sube: solo lo que crece.
    sube = con_lo_pujado(FOTO_3110, [(39357, 750_000), (90002, 100_000)])
    assert sube["market"]["status"]["maximumBid"] == maximo - (750_000 - 709_900) - 100_000
    # Sin `maximumBid` entero, como estaba.
    for raro in (None, "8675224", 8_675_224.0, True):
        foto = copy.deepcopy(FOTO_3110)
        foto["market"]["status"]["maximumBid"] = raro
        assert con_lo_pujado(foto, [(90002, 5)])["market"]["status"]["maximumBid"] is raro
    sin_estado = copy.deepcopy(FOTO_3110)
    del sin_estado["market"]["status"]
    assert "status" not in con_lo_pujado(sin_estado, [(90002, 5)])["market"]

    # El caso del revisor: la orden ficha a la pareja A a 1.500.000 con el
    # `maximumBid` en 1.000.000. Sin la cesta, NADA (supera el tope). Con la
    # puja de la cesta reservada, lo mismo: el tope es el maximo MAS lo ya
    # pujado, y el maximo ya trae la puja (antes pujaba 1.500.000).
    foto = _foto_de_la_misma_vuelta()
    foto["market"]["status"]["maximumBid"] = 1_000_000
    foto["market"]["sales"].append({"player": {"id": 90002}, "user": None, "price": 700_000})
    foto["catalog"]["data"]["players"]["90002"] = {
        "id": 90002, "price": 700_000, "priceIncrement": 30_000, "status": "ok",
        "points": 40, "playedHome": 4, "playedAway": 4}
    la_orden = {"fichar": [{"player_id": 90002, "nombre": "Pareja A", "puja": 1_500_000}]}

    def _decide(f):
        lf = orden.leer_la_foto(f, YO)
        lf.pop("de_managers", None)
        return [(a["accion"], a.get("importe")) for a in orden.decidir(
            la_orden, **lf, horas_jornada=64.0, estados={90002: "ok"}, en_curso=False)]

    sin_cesta = _decide(foto)
    assert [a for a, _ in sin_cesta] == ["NADA"], sin_cesta
    assert _decide(con_lo_pujado(foto, [(90002, PUJA_DE_LA_PAREJA)])) == sin_cesta


def test_una_puja_viva_no_baja():
    import src.actions.la_ronda_de_la_manana as ronda
    from src.actions.la_orden_del_gestor import leer_la_foto
    from src.analysis.la_subasta_en_el_colchon import con_lo_pujado

    # Macia tiene viva 709.900: reservar 500.000 por el no la baja (la foto
    # nueva la traeria a 709.900), ni sube el `maximumBid`, ni agranda el
    # colchon de la ronda (el revisor: salia 1.389.675).
    baja = con_lo_pujado(FOTO_3110, [(39357, 500_000)])
    assert _nuestras_en(baja) == PUJAS_3110, _nuestras_en(baja)
    assert baja["market"]["status"]["maximumBid"] == FOTO_3110["market"]["status"]["maximumBid"]
    fichas = {int(k): v for k, v in FOTO_3110["catalog"]["data"]["players"].items()}
    for f in (FOTO_3110, baja):
        lf = leer_la_foto(f, YO)
        assert ronda.el_colchon(lf["saldo"], lf["nuestras_pujas"], LIBRO_3110,
                                lf["plantilla"], fichas) == COLCHON_3110
    # La que sube, sube.
    assert _nuestras_en(con_lo_pujado(FOTO_3110, [(39357, 750_000)]))[39357] == 750_000


def test_sin_pujar_tambien_se_reserva():
    import src.v10_full_autonomous_live as ciclo

    pareja = _vuelta_3110((MACIA, ORTIZ, PAREJA_A))
    # SIN_COLCHON: el motor viejo ya pujo 900.000 en `post_action` y la
    # pareja A no cabe. La foto de la vuelta tiene que traer esa puja: si
    # no, la orden, los chollos y la ronda ven 1.179.775 de colchon donde
    # la cesta acaba de ver 279.775 (el revisor).
    vuelta = {"snapshot": copy.deepcopy(FOTO_3110),
              "post_action": {"snapshot": copy.deepcopy(FOTO_POST_3110)}}
    plan, enviadas, despues = _la_vuelta(pareja, vuelta, PUESTO)
    assert enviadas == [] and plan["blocked_by"] == "SIN_COLCHON", plan.get("reason")
    assert _nuestras_en(despues["snapshot"]) == {**PUJAS_3110, **PUJA_DEL_EJECUTOR}
    assert despues["snapshot"]["market"]["status"]["maximumBid"] == 8_675_224 - 900_000
    import src.actions.la_ronda_de_la_manana as ronda
    from src.actions.la_orden_del_gestor import leer_la_foto

    lf = leer_la_foto(despues["snapshot"], YO)
    fichas = {int(k): v for k, v in despues["snapshot"]["catalog"]["data"]["players"].items()}
    assert ronda.el_colchon(lf["saldo"], lf["nuestras_pujas"], LIBRO_3110, lf["plantilla"],
                            fichas) == 279_775

    # Apagado, la foto de la vuelta ni se toca (el mismo objeto).
    vuelta = {"snapshot": copy.deepcopy(FOTO_3110),
              "post_action": {"snapshot": copy.deepcopy(FOTO_POST_3110)}}
    original = vuelta["snapshot"]
    plan, enviadas, despues = _la_vuelta(pareja, vuelta, APAGADO)
    assert despues["snapshot"] is original and "bloque_de_la_vuelta" not in plan

    # Sin mandar nada, las del plan NO se reservan (no se pujaron): solo lo
    # que el colchon conto sin estar en la foto. Un plan sin ejecutar con
    # pujas (sin el modo en vivo) y una del libro de esta ventana.
    abierta = AHORA_3110 - timedelta(minutes=4)
    sin_vivo = _plan(pareja, FOTO_3110, en_vivo=False, pujas_desde=abierta,
                     libro_de_pujas={"version": "V1.0", "bids": {"a": {
                         "player_id": 55555, "amount": 60_000, "outcome": "PENDING",
                         "placed_at": (AHORA_3110 - timedelta(minutes=1)).isoformat()}}})
    assert _ids(sin_vivo) == [90002] and sin_vivo["execute"] is False, sin_vivo["reason"]
    cycle = {"snapshot": copy.deepcopy(FOTO_3110)}
    with _Interruptores(PUESTO):
        bloque = ciclo._reservar_lo_pujado(cycle, sin_vivo, None)
    assert _nuestras_en(cycle["snapshot"]) == {**PUJAS_3110, 55555: 60_000}
    # (02/11: la del libro, como puja viva para los que pujan detras, pero
    # sin bajar el tope ni ir a las `hechas` que leen los que venden.)
    assert cycle["snapshot"]["market"]["status"]["maximumBid"] == 8_675_224
    assert bloque["hechas"] == [] and bloque["sin_foto"] == [{"id": 55555, "amount": 60_000}]
    with _Interruptores(APAGADO):
        cycle = {"snapshot": copy.deepcopy(FOTO_3110)}
        original = cycle["snapshot"]
        assert ciclo._reservar_lo_pujado(cycle, sin_vivo, None) is None
        assert cycle["snapshot"] is original


# ============================================================
# 8. LAS REVISIONES DE adc4eaa4 (02/11)
# ============================================================

RECHAZO_400 = {"sent": True, "success": False, "http_status": 400,
               "response": {"status": 400, "message": "No tienes dinero suficiente"}}


def _despues(v10, foto=None) -> dict:
    """Lo que ven la mejora y el cierre (otros procesos) con ese estado de
    la vuelta y la foto del disco (por defecto, la de antes de la cesta)."""
    from src.actions import el_cierre_de_la_jornada as cierre
    from src.actions import la_mejora_del_once as mejora
    from src.actions.la_orden_del_gestor import leer_la_foto

    disco = leer_la_foto(copy.deepcopy(FOTO_3110 if foto is None else foto), YO)
    ev = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera=True,
                                  vistas=_importes(disco))
    vc = cierre.lo_de_esta_vuelta(v10)
    vivas = cierre.las_pujas_vivas(disco, vc)
    return {"descartado": ev["descartado"], "pujas": ev["pujas"], "gastado": ev["gastado"],
            "ya_pujados": ev["ya_pujados"], "caja": mejora.la_caja(disco, esta_vuelta=ev),
            "cierre": {p: f["amount"] for p, f in vivas.items()},
            "caja_del_cierre": cierre.la_caja(disco["saldo"], vivas, {})}


def test_la_que_biwenger_rechaza_no_cuenta():
    # Biwenger contesta 400 a la puja de la pareja A: no existe. Ni se
    # reserva en la foto de la vuelta (ni su tope), ni la cuentan la mejora
    # ni el cierre, que vende en rojo (el revisor: caja -331.576 de una
    # puja que no hay; la de verdad, 370.175).
    v10, vuelta = _la_cesta(escritor=lambda pid, importe: copy.deepcopy(RECHAZO_400))
    assert vuelta["enviadas"] == [(90002, PUJA_DE_LA_PAREJA)], vuelta["enviadas"]
    filas = v10["subasta"]["hechas"]
    assert [(h["player_id"], h["exito"], h.get("rechazada"), h["http_status"]) for h in filas] \
        == [(90002, False, "HTTP 400", 400)], filas
    assert v10["subasta"]["reservado"] == 0
    assert _nuestras_en(vuelta["cycle"]["snapshot"]) == PUJAS_3110
    assert vuelta["cycle"]["snapshot"]["market"]["status"]["maximumBid"] == 8_675_224
    assert vuelta["vistos"]["ronda"]["maximo"] == 8_675_224, vuelta["vistos"]
    sin_cesta = SALDO_3110 - 929_800
    for foto in (None, FOTO_3110):
        d = _despues(v10, foto)
        assert d["descartado"] is None and d["pujas"] == {} and d["gastado"] == 0, d
        assert d["caja"] == sin_cesta == 370_175, d
        assert 90002 not in d["cierre"] and d["caja_del_cierre"] == sin_cesta, d
    # Un 200 con {"status": 409} en el cuerpo tambien es una respuesta.
    v10, _ = _la_cesta(escritor=lambda pid, importe: {
        "sent": True, "success": False, "http_status": 200, "response": {"status": 409}})
    assert [h["exito"] for h in v10["subasta"]["hechas"]] == [False]

    # Lo que NO se sabe sigue contando entero: un 200 con una pagina de
    # mantenimiento, un 5xx, un 429 que la sesion no pudo con el, lo que el
    # ensayo no manda.
    for duda in ({"sent": True, "success": False, "http_status": 200,
                  "response": "<html>mantenimiento</html>"},
                 {"sent": True, "success": False, "http_status": 502},
                 {"sent": False, "success": False}):
        v10, vuelta = _la_cesta(escritor=lambda pid, importe, d=duda: copy.deepcopy(d))
        assert [(h["player_id"], h["exito"], h["importe"]) for h in v10["subasta"]["hechas"]] \
            == [(90002, True, PUJA_DE_LA_PAREJA)], (duda, v10["subasta"]["hechas"])
        assert _nuestras_en(vuelta["cycle"]["snapshot"])[90002] == PUJA_DE_LA_PAREJA
        assert _despues(v10)["caja"] == sin_cesta - PUJA_DE_LA_PAREJA == -331_576

    # La vara, sola.
    from src.analysis.la_subasta_en_el_colchon import la_rechazada

    assert la_rechazada(RECHAZO_400) == "HTTP 400"
    for duda in ({"sent": True, "success": False, "http_status": 200, "response": "<html>"},
                 {"sent": True, "success": False, "http_status": 503},
                 {"sent": True, "success": False, "http_status": True},
                 {"sent": True, "success": True, "http_status": 400},
                 {"sent": False, "success": False, "http_status": 400},
                 {"sent": True, "success": None, "http_status": 400},
                 None, "x", [], {}):
        assert la_rechazada(duda) is None, duda


def test_lo_del_libro_no_baja_el_tope_ni_vende():
    from src.actions import la_orden_del_gestor as orden

    # SIN_COLCHON: el motor viejo pujo 900.000 en `post_action` (de verdad:
    # su foto la trae) y el libro de la ventana apunta 50.000 por el 66666
    # que ninguna foto trae (casi siempre, rechazada o retirada). En la foto
    # de la vuelta, las dos como pujas vivas (los que pujan detras no se
    # gastan ese colchon); el tope de Biwenger solo baja la de verdad (el
    # revisor: la orden no fichaba por un tope 50.000 por debajo del real).
    v10, vuelta = _la_cesta(post=FOTO_POST_3110, libro_de_pujas=LIBRO_DE_LA_VENTANA)
    reservada = vuelta["cycle"]["snapshot"]
    assert _nuestras_en(reservada) == {**PUJAS_3110, **PUJA_DEL_EJECUTOR, 66666: 50_000}
    real = 8_675_224 - 900_000
    assert reservada["market"]["status"]["maximumBid"] == real, \
        reservada["market"]["status"]["maximumBid"]
    assert vuelta["vistos"]["orden"]["maximo"] == real

    def _decide(foto, puja):
        f = copy.deepcopy(foto)
        f["market"]["sales"].append({"player": {"id": 90002}, "user": None, "price": 700_000})
        f["catalog"]["data"]["players"]["90002"] = {
            "id": 90002, "price": 700_000, "priceIncrement": 30_000, "status": "ok",
            "points": 40, "playedHome": 4, "playedAway": 4}
        lf = orden.leer_la_foto(f, YO)
        lf.pop("de_managers", None)
        return [a["accion"] for a in orden.decidir(
            {"fichar": [{"player_id": 90002, "nombre": "F", "puja": puja}]}, **lf,
            horas_jornada=64.0, estados={90002: "ok"}, en_curso=False)]

    de_verdad = copy.deepcopy(FOTO_POST_3110)
    de_verdad["market"]["status"]["maximumBid"] = real
    assert _decide(de_verdad, real - 20_000) == _decide(reservada, real - 20_000) == ["PUJAR"]

    # Los otros procesos: la del motor viejo cuenta (la foto del disco es
    # de antes); la del libro, ni en la caja de la mejora ni en la del
    # cierre (los dos venden), pero la mejora no vuelve a pujar por ella.
    d = _despues(v10)
    assert d["pujas"] == PUJA_DEL_EJECUTOR and d["gastado"] == 900_000, d
    assert {66666, 77777} <= d["ya_pujados"], d["ya_pujados"]
    assert d["caja"] == SALDO_3110 - 929_800 - 900_000, d
    assert d["cierre"] == {**PUJAS_3110, **PUJA_DEL_EJECUTOR}, d["cierre"]


def test_un_429_despues_de_la_cesta_deja_su_bloque():
    from src.biwenger.peticiones import LimiteDePeticiones

    def _429(**k):
        raise LimiteDePeticiones("429 Too Many Requests")

    de_antes = {"run_id": "la-de-antes", "timestamp": "2026-11-05T02:45:00+00:00",
                "orden_del_gestor": {"hechas": [{"accion": "PUJAR", "player_id": 4242,
                                                 "importe": 10_000, "exito": True}]}}

    # La cesta puja y el BUY de v10 se lleva un 429 que no cede: `main` sale
    # con 0 y, encendido, deja un estado minimo de ESTA vuelta con el bloque
    # (antes la cache dejaba el de la anterior y la mejora y el cierre
    # veian la caja de antes de la cesta: 370.175 contra -331.576).
    v10, vuelta = _la_cesta(buy=_429, por_main=True, de_antes=de_antes)
    assert vuelta["rc"] == 0 and vuelta["enviadas"] == [(90002, PUJA_DE_LA_PAREJA)]
    assert v10.get("run_id") == RUN_ID, v10
    assert (v10.get("retirada") or {}).get("motivo") == "LIMITE_DE_PETICIONES", v10
    assert [(h["player_id"], h["importe"], h["exito"]) for h in v10["subasta"]["hechas"]] \
        == [(90002, PUJA_DE_LA_PAREJA, True)]
    assert "orden_del_gestor" not in v10 and "carril" not in v10, list(v10)
    d = _despues(v10)
    assert d["descartado"] is None and d["pujas"] == {90002: PUJA_DE_LA_PAREJA}, d
    assert d["caja"] == d["caja_del_cierre"] == -331_576, d
    assert d["cierre"][90002] == PUJA_DE_LA_PAREJA

    # Apagado, como siempre: no se escribe nada (queda el de la anterior).
    v10, vuelta = _la_cesta(entorno=APAGADO, buy=_429, por_main=True, de_antes=de_antes)
    assert vuelta["rc"] == 0 and vuelta["enviadas"] == [(90002, PUJA_DE_LA_PAREJA)]
    assert v10 == de_antes, v10
    # Encendido, sin nada de la cesta (fuera de la ventana), tampoco.
    fuera = _estado(TABLERO_3110 + (PAREJA_A,), BOLSILLOS_3110, 9_000, SIN_DEUDA, FICHAS_3110)
    v10, vuelta = _la_cesta(estado=fuera, buy=_429, por_main=True, de_antes=de_antes)
    assert vuelta["enviadas"] == [] and v10 == de_antes, v10
    # Y un 429 ANTES de la cesta (en `run_cycle`) no deja la de otra
    # llamada: solo cuenta la cesta de esta.
    import src.v10_full_autonomous_live as ciclo

    with tempfile.TemporaryDirectory() as d, _Interruptores(PUESTO):
        ruta = Path(d) / "v10_full_autonomous_status.json"
        antes = (ciclo.run_cycle, ciclo.STATUS_PATH, ciclo._publicar_peticiones,
                 ciclo.__dict__.get("_ultima_subasta"))
        try:
            ciclo.run_cycle = lambda **k: (_ for _ in ()).throw(LimiteDePeticiones("429"))
            ciclo.STATUS_PATH, ciclo._publicar_peticiones = ruta, (lambda: None)
            ciclo._ultima_subasta = {"bloque_de_la_vuelta": {"hechas": [{"player_id": 1}]}}
            import contextlib
            import io

            with contextlib.redirect_stdout(io.StringIO()):
                assert ciclo.main() == 0
            assert not ruta.exists()
        finally:
            ciclo.run_cycle, ciclo.STATUS_PATH, ciclo._publicar_peticiones = antes[:3]
            if antes[3] is None:
                ciclo.__dict__.pop("_ultima_subasta", None)
            else:
                ciclo._ultima_subasta = antes[3]


def test_la_misma_puja_despues_cuenta_lo_que_crece():
    from src.actions import la_mejora_del_once as mejora

    # La cesta puja 701.751 por la pareja A y despues la orden sube la misma
    # a 1.000.000 (una puja por jugador): el `maximumBid` de la mejora baja
    # 1.000.000, no 1.701.751 (el revisor). La caja y el cierre, por
    # jugador, ya estaban bien.
    sube = {"orden": {"hechas": [{
        "accion": "PUJAR", "player_id": 90002, "importe": 1_000_000, "exito": True,
        "sustituye": {"offer_id": None, "amount": PUJA_DE_LA_PAREJA}}]}}
    v10, _ = _la_cesta(demas=sube)
    d = _despues(v10)
    assert d["gastado"] == 1_000_000, d
    assert d["pujas"] == {90002: 1_000_000} and d["cierre"][90002] == 1_000_000, d
    # Si la de despues es mas baja, no se devuelve nada (de mas, del lado de
    # no pujar); con la foto que ya trae la de la cesta, solo lo que crece.
    baja = {"orden": {"hechas": [{"accion": "PUJAR", "player_id": 90002,
                                  "importe": 500_000, "exito": True}]}}
    v10_baja, _ = _la_cesta(demas=baja)
    assert _despues(v10_baja)["gastado"] == PUJA_DE_LA_PAREJA
    ev = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera=True,
                                  vistas={90002: PUJA_DE_LA_PAREJA})
    assert ev["gastado"] == 1_000_000 - PUJA_DE_LA_PAREJA, ev
    # Sin cesta, la orden como siempre (entera).
    solo = {k: v for k, v in v10.items() if k != "subasta"}
    assert mejora.lo_de_esta_vuelta(solo, AHORA_DESPUES, RUN_ID, cartera=True)["gastado"] \
        == 1_000_000


# LA CESTA NO SE ABRE SIN SUS CANDADOS (el revisor de apagado, 02/11). El
# dia que se quite `BORDALAS_SIN_SUBASTA`, el colchon y el suelo tienen que
# quedar ENCENDIDOS para su lector de verdad; quitar el colchon para
# apagarlo devolveria la cesta del 31/10 (2.025.051 por Dani Lorenzo). Y
# el valor, "1": el paso 0 y la verja dan "on" o "si" por encendido y estos
# lectores no. Se apaga volviendo a poner `BORDALAS_SIN_SUBASTA: "1"`.
WORKFLOW = RAIZ / ".github" / "workflows" / "bordalas-live.yml"
SUELO = "BORDALAS_CESTA_SOLO_EL_SUELO"
SIN_SUBASTA = "BORDALAS_SIN_SUBASTA"


def _los_literales(texto) -> dict:
    """{interruptor: valor tal cual} de las lineas sin comentar del YAML."""
    from src.analysis.el_paso_0 import LINEA

    salida = {}
    for linea in str(texto or "").splitlines():
        m = LINEA.match(linea)
        if m and not linea.strip().startswith("#"):
            salida[m.group("nombre")] = m.group("valor")
    return salida


def los_candados_de_la_cesta(texto) -> list:
    """Lo que esta mal en el YAML para la cesta (vacio: bien). Pregunta a
    los lectores de verdad (`_sin_subasta`, `_en_el_colchon`,
    `solo_el_suelo`) con el valor del YAML en el entorno, y al del paso 0
    (`interruptores_encendidos_en`)."""
    from src.analysis.el_paso_0 import _limpio, interruptores_encendidos_en

    lectores = {SIN_SUBASTA: sub._sin_subasta, ENV: sub._en_el_colchon,
                SUELO: sub.solo_el_suelo}
    literales = _los_literales(texto)
    del_paso_0 = interruptores_encendidos_en(texto)
    lee, mal = {}, []
    for nombre, lector in lectores.items():
        literal = literales.get(nombre)
        with _Interruptores({nombre: None if literal is None else _limpio(literal)}):
            lee[nombre] = bool(lector())
        if (nombre in del_paso_0) != lee[nombre]:
            mal.append(f"{nombre}: {literal} es {'encendido' if nombre in del_paso_0 else 'apagado'} "
                       f"para el paso 0 y la verja y {'encendido' if lee[nombre] else 'apagado'} "
                       f"para su lector de verdad: escribir \"1\"")
    if not lee[SIN_SUBASTA]:
        for nombre in (ENV, SUELO):
            if not lee[nombre]:
                mal.append(f"la cesta esta abierta (sin {SIN_SUBASTA}) y {nombre} no esta "
                           f"encendido: la cesta del 31/10 otra vez. Para apagarla se vuelve a "
                           f"poner {SIN_SUBASTA}: \"1\"; el colchon y el suelo no se quitan")
    return mal


def test_la_cesta_no_se_abre_sin_sus_candados():
    from src.analysis.el_paso_0 import LINEA

    def _yaml(**lineas):
        return "env:\n  BORDALAS_LA_CARTERA: \"1\"\n" + "".join(
            f"  {n}: {v}\n" for n, v in lineas.items())

    bien = {
        "hoy, cerrada": {SIN_SUBASTA: '"1"'},
        "encendida": {ENV: '"1"', SUELO: '"1"'},
        "apagada otra vez": {SIN_SUBASTA: '"1"', ENV: '"1"', SUELO: '"1"'},
        "con comentario": {ENV: '"1"   # el colchon', SUELO: "'1'"},
        "cerrada, con el colchon a 0": {SIN_SUBASTA: '"1"', ENV: '"0"'},
    }
    for caso, lineas in bien.items():
        assert los_candados_de_la_cesta(_yaml(**lineas)) == [], caso
    mal = {
        "sin el colchon": {SUELO: '"1"'},
        "sin los dos": {},
        "el colchon a 0": {ENV: '"0"', SUELO: '"1"'},
        "el colchon en on": {ENV: '"on"', SUELO: '"1"'},
        "cerrada, el colchon en si": {SIN_SUBASTA: '"1"', ENV: '"sí"'},
        "la de cerrar en on": {SIN_SUBASTA: "on", ENV: '"1"'},
        "comentada": {"#" + SIN_SUBASTA: '"1"'},
    }
    for caso, lineas in mal.items():
        assert los_candados_de_la_cesta(_yaml(**lineas)), caso
    assert any(ENV in m for m in los_candados_de_la_cesta(_yaml(**{SUELO: '"1"'})))

    # El YAML de verdad; y la linea del dia que se encienda, sobre el.
    real = WORKFLOW.read_text(encoding="utf-8")
    assert los_candados_de_la_cesta(real) == [], los_candados_de_la_cesta(real)

    def _sin(texto, nombre):
        return "".join(l for l in texto.splitlines(True)
                       if not (LINEA.match(l) and LINEA.match(l).group("nombre") == nombre))

    cerrada = [l for l in real.splitlines(True)
               if LINEA.match(l) and LINEA.match(l).group("nombre") == SIN_SUBASTA]
    encendida = real
    if cerrada:
        sangria = LINEA.match(cerrada[0]).group("sangria")
        encendida = real.replace(cerrada[0], f'{sangria}{ENV}: "1"\n{sangria}{SUELO}: "1"\n')
    assert los_candados_de_la_cesta(encendida) == [], los_candados_de_la_cesta(encendida)
    assert los_candados_de_la_cesta(_sin(encendida, ENV))
    assert los_candados_de_la_cesta(_sin(_sin(encendida, ENV), SUELO))


def test_la_vuelta_no_mira_el_reloj():
    import datetime as reloj

    # Con el reloj en 2100 (pasada la jornada del calendario de la casa), la
    # vuelta entera puja igual: la hora del colchon es la de la vuelta, no
    # la del sistema (el revisor: sin esto fallaban siete).
    real = reloj.datetime

    class _En2100(real):
        @classmethod
        def now(cls, tz=None):
            cuando = real(2100, 1, 1, 12, tzinfo=timezone.utc)
            return cuando if tz else cuando.replace(tzinfo=None)

    try:
        reloj.datetime = _En2100
        v10, vuelta = _la_cesta()
        plan, enviadas, _ = _la_vuelta(_vuelta_3110((MACIA, ORTIZ, PAREJA_A)),
                                       {"snapshot": copy.deepcopy(FOTO_3110)}, PUESTO)
        panel = _la_pantalla(_vuelta_3110((MACIA, ORTIZ, PAREJA_A)), FOTO_3110, PUESTO)
    finally:
        reloj.datetime = real
    assert vuelta["enviadas"] == [(90002, PUJA_DE_LA_PAREJA)], vuelta["pantalla"][-600:]
    assert [h["player_id"] for h in v10["subasta"]["hechas"]] == [90002]
    assert enviadas == [(90002, PUJA_DE_LA_PAREJA)], plan.get("reason")
    assert [b["id"] for b in panel["bids"]] == [90002], panel.get("reason")


# APAGADO, EL ESTADO DE LA VUELTA ES EL DE MAIN. La bateria: estos casos en
# los cinco entornos de la cesta, con el libro de la ventana puesto. De cada
# vuelta entera: el estado de v10 (el texto que se escribe, letra a
# letra), la pantalla, el escritor, la foto que ven la orden, la revision,
# los chollos y la ronda, el `cycle` como queda, y lo que sacan del estado
# la mejora (con y sin cartera, y su caja), el cierre, la rotacion y el
# parte. Medida en main@c2842a58 ANTES del cambio (el `--medir` de abajo,
# con esta guardia copiada en un `git archive` de main), en 3.11 y 3.13.
def _casos_del_estado() -> list:
    pareja = _vuelta_3110((MACIA, ORTIZ, PAREJA_A))
    return [
        ("3110", _vuelta_3110(), FOTO_3110, None),
        ("pareja", pareja, FOTO_3110, None),
        ("pareja+post", pareja, FOTO_3110, FOTO_POST_3110),
        ("todos, rico", _vuelta_3110(TABLERO_3110 + (BARATO, PAREJA_A, PAREJA_B), RICO),
         FOTO_3110, None),
        ("misma", _vuelta_3110((MACIA, ORTIZ, X_CESTA)), _foto_de_la_misma_vuelta(), None),
        ("fuera", _estado(TABLERO_3110 + (PAREJA_A,), BOLSILLOS_3110, 9_000, SIN_DEUDA,
                          FICHAS_3110), FOTO_3110, FOTO_POST_3110),
        ("sin foto", _vuelta_3110(), None, None),
        ("basura", {"acquisition": "x", "exposure": 7}, {"my_team": 3}, None),
    ]


def _plano(valor):
    """Para la huella: los conjuntos, ordenados."""
    if isinstance(valor, (set, frozenset)):
        return sorted(valor, key=repr)
    return repr(valor)


def _lo_de_despues(v10) -> dict:
    from src.actions import el_cierre_de_la_jornada as cierre
    from src.actions import el_parte_vende as parte
    from src.actions import la_mejora_del_once as mejora
    from src.actions import la_rotacion as rotacion
    from src.actions.la_orden_del_gestor import leer_la_foto

    disco = leer_la_foto(copy.deepcopy(FOTO_3110), YO)
    salida = {}
    for cartera in (False, True):
        ev = mejora.lo_de_esta_vuelta(v10, AHORA_DESPUES, RUN_ID, cartera)
        salida[f"mejora {cartera}"] = ev
        salida[f"caja {cartera}"] = mejora.la_caja(disco, esta_vuelta=ev)
    vc = cierre.lo_de_esta_vuelta(v10)
    salida["cierre"] = vc
    salida["cierre, vivas"] = cierre.las_pujas_vivas(disco, vc)
    salida["rotacion"] = rotacion.lo_de_esta_vuelta(v10, None, None, AHORA_DESPUES, RUN_ID, None)
    salida["parte"] = parte.lo_vendido_y_publicado(v10, None, None, AHORA_DESPUES, RUN_ID)
    return json.loads(json.dumps(salida, default=_plano))


def _huellas_del_estado() -> list:
    salida = []
    for _, entorno, veta in ENTORNOS:
        for _, estado, foto, post in _casos_del_estado():
            cycle = {"snapshot": copy.deepcopy(foto)}
            if post is not None:
                cycle["post_action"] = {"snapshot": copy.deepcopy(post)}
            vuelta = _la_vuelta_entera(copy.deepcopy(estado), cycle, entorno,
                                       LIBRO_DE_LA_VENTANA, veta, LO_DE_LOS_DEMAS)
            v10 = json.loads(vuelta["texto"]) if vuelta["texto"] else {}
            salida.append(_huella({
                "texto": vuelta["texto"], "pantalla": vuelta["pantalla"],
                "enviadas": vuelta["enviadas"], "vistos": vuelta["vistos"],
                "cycle": json.loads(json.dumps(vuelta["cycle"], sort_keys=True, default=repr)),
                "despues": _lo_de_despues(v10),
                "subasta": "subasta" in v10,
            }))
    return salida


HUELLAS_DEL_ESTADO_DE_MAIN = {
    (3, 11): "a8a1f177f2680e4b2dd5d2ddd562307e661925c1279a5537cf40d29a73190bb4",
    (3, 13): "a8a1f177f2680e4b2dd5d2ddd562307e661925c1279a5537cf40d29a73190bb4",
}
VUELTAS_DEL_ESTADO = 40


def test_apagado_el_estado_de_la_vuelta_es_el_de_main():
    esperada = HUELLAS_DEL_ESTADO_DE_MAIN.get(sys.version_info[:2])
    assert esperada is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    hoy = _huellas_del_estado()
    assert len(hoy) == VUELTAS_DEL_ESTADO, len(hoy)
    assert _resumen(hoy) == esperada, _resumen(hoy)
    # Y apagado no hay bloque ni en la pareja que puja.
    estado, vuelta = _la_cesta(entorno=APAGADO)
    assert "subasta" not in estado and vuelta["enviadas"] == [(90002, PUJA_DE_LA_PAREJA)]


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
    test_la_foto_mas_fresca_de_la_vuelta,
    test_el_libro_de_la_ventana_cuenta_delante,
    test_lo_que_la_cesta_puja_lo_ve_la_ronda,
    test_el_estado_de_la_vuelta_lleva_la_cesta,
    test_la_mejora_ve_la_cesta_despues_de_la_vuelta,
    test_con_lo_pujado_baja_el_maximo_de_puja,
    test_una_puja_viva_no_baja,
    test_sin_pujar_tambien_se_reserva,
    test_la_que_biwenger_rechaza_no_cuenta,
    test_lo_del_libro_no_baja_el_tope_ni_vende,
    test_un_429_despues_de_la_cesta_deja_su_bloque,
    test_la_misma_puja_despues_cuenta_lo_que_crece,
    test_la_cesta_no_se_abre_sin_sus_candados,
    test_la_vuelta_no_mira_el_reloj,
    test_apagado_el_estado_de_la_vuelta_es_el_de_main,
]


def medir() -> None:
    """Las huellas, apagadas, para `HUELLAS_DE_MAIN` y
    `HUELLAS_DEL_ESTADO_DE_MAIN`."""
    with _Interruptores(APAGADO):
        hoy = _huellas(APAGADO)
    print(f"Python {sys.version_info[:2]}: {len(hoy)} llamadas, {_resumen(hoy)}")
    estado = _huellas_del_estado()
    print(f"Python {sys.version_info[:2]}: {len(estado)} vueltas enteras, {_resumen(estado)}")


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
