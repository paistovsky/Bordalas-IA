"""
EL ONCE QUE SE PUEDE ESCRIBIR (31/10/2026). Guardias de
`src/analysis/el_once_que_se_puede_escribir.py` y de su enganche en
`lineup_engine.build_lineup`, `lineup_monitor.build_lineup_monitor_state`
y `autopilot_executor` (SAVE_LINEUP).

EL CASO (bitacora del 27/10 21:00 y analisis del suplente del 29/10)

    Un dibujo de emergencia con un jugador en duda (10 alineables sin
    aviso) gana a uno completo de 11 sanos, y el ejecutor bloquea el
    SAVE_LINEUP (`playable_count` < 11: BLOCKED_INVALID_LINEUP). En
    Biwenger se queda el ultimo once escrito, con el lesionado dentro si
    lo hay, y el SAVE_LINEUP bloqueado se come la unica escritura de la
    vuelta, vuelta tras vuelta. El de la J12: Boyé en duda y Kike Salas
    lesionado (los dos juegan el Sevilla-Alavés del viernes 06/11): el
    motor elige un 3-4-3 con Boyé y Cardona (10 alineables) en vez del
    3-5-2 sano, y Kike se queda en el once de Biwenger.

QUE SE COMPRUEBA

    1. NACE APAGADO, y apagado el once es el de hoy byte a byte: la
       huella de `build_lineup` sobre la bateria corta sale clavada a la
       de main (medida antes de tocar el motor), y el monitor da el
       mismo once. Puesto, los que valoran (`build_lineup(foto)` a
       secas) tambien, sin que corra ni una linea del modulo. La bateria
       larga (11, 12, 14 y 15 jugadores, cada estado solo y cada pareja
       de estados) se corre a mano: `--larga`.
    2. Solo el monitor (el once que se escribe) lo pide, y solo con el
       interruptor.
    3. Encendido, el once que llega a SAVE_LINEUP lo acepta el ejecutor
       de verdad: con un dudoso, el once sano si existe en algun dibujo
       (el de la J12, Olasagasti, dos defensas en duda, un delantero en
       duda solo); un Dios en duda juega (la regla del 18/08) y se
       escribe; sin once sano, el que lleva menos dudosos, y el
       lesionado no se queda; sin once de 11 (portero lesionado), nada
       que escribir, como hoy.
    4. El ejecutor sin la marca es el de hoy, y con la marca solo deja
       pasar a los dudosos autorizados y alineables.
    5. Nunca lanza: si algo falla, el once de hoy.

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui. La plantilla, los precios, los puntos, los
    partidos y la titularidad de FF son los del ultimo artefacto de
    produccion (run 41187359006, 31/10 09:07 UTC); Juan Iglesias, del
    `season_horizon` del mismo artefacto. El once puesto en Biwenger,
    el del artefacto. Ni la carpeta de estado, ni la red, ni el reloj:
    el tablero de FF, JP, el estado guardado del monitor y el once
    puesto se suplantan (`_Produccion`).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Todo lo que mueve
# el once se quita aqui arriba; cada prueba pone lo suyo.
ENV = "BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR"
ENV_UNA_VEZ = "BORDALAS_EL_ONCE_UNA_VEZ"
ENV_SIN_ELLOS = "BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN"
for _nombre in (
    ENV, ENV_UNA_VEZ, ENV_SIN_ELLOS,
    "BORDALAS_EL_CALENDARIO_EN_EL_ONCE", "BORDALAS_CALIDAD_ETIQUETA",
    "BORDALAS_VARA_PLANA", "PENALTY_INTELLIGENCE_ENABLED",
):
    os.environ.pop(_nombre, None)


from src.analysis import el_once_se_busca_una_vez as una_vez  # noqa: E402
from src.analysis import lineup_engine, lineup_monitor  # noqa: E402
from src.analysis.lineup_engine import build_lineup  # noqa: E402


class _Interruptores:
    """Pone (valor) o quita (None) interruptores solo dentro del
    `with`, y vacia la memoria del once al entrar y al salir."""

    def __init__(self, valores: dict):
        self.valores = dict(valores)

    def __enter__(self):
        self.antes = {n: os.environ.get(n) for n in self.valores}
        for nombre, valor in self.valores.items():
            if valor is None:
                os.environ.pop(nombre, None)
            else:
                os.environ[nombre] = valor
        una_vez.olvidar()
        return self

    def __exit__(self, *_):
        for nombre, valor in self.antes.items():
            if valor is None:
                os.environ.pop(nombre, None)
            else:
                os.environ[nombre] = valor
        una_vez.olvidar()
        return False


# La memoria del once va puesta como en produccion
# (`BORDALAS_EL_ONCE_UNA_VEZ=1`, bordalas-live.yml): da el mismo once
# (`test_el_once_se_busca_una_vez_v1`) y la bateria repetida no busca
# dos veces lo mismo. Las huellas de main salen iguales con y sin ella.
APAGADO = {ENV: None, ENV_SIN_ELLOS: None, ENV_UNA_VEZ: "1"}
PUESTO = {ENV: "1", ENV_SIN_ELLOS: None, ENV_UNA_VEZ: "1"}


# ============================================================
# LA PLANTILLA DEL 31/10 (artefacto de la run 41187359006)
# ============================================================

ETIQUETAS = {60: "Dios", 50: "Clave", 40: "Importante", 30: "Rotación",
             25: "Revulsivo", 20: "Reserva"}


def _j(pid, nombre, pos, equipo, precio, puntos, casa, fuera, pasada) -> dict:
    return {"id": pid, "name": nombre, "position": pos, "teamID": equipo,
            "price": precio, "points": puntos, "played_home": casa,
            "played_away": fuera, "pointsLastSeason": pasada, "status": "ok"}


GULACSI = _j(38433, "Gulácsi", 1, 19, 2_360_000, 31, 4, 3, 0)
KIKE = _j(28115, "Kike Salas", 2, 17, 3_280_000, 35, 4, 4, 135)
CHUST = _j(1760, "Chust", 2, 75, 2_480_000, 41, 4, 6, 131)
GAYA = _j(1844, "Gayà", 2, 18, 1_770_000, 27, 5, 3, 108)
CARDONA = _j(30493, "Sergi Cardona", 2, 19, 2_060_000, 25, 4, 3, 107)
ORTIZ = _j(35765, "Angel Ortiz", 2, 87, 190_000, 14, 2, 2, 34)
OLASAGASTI = _j(29661, "Olasagasti", 3, 10, 2_900_000, 50, 4, 6, 121)
IBANEZ = _j(14800, "Pablo Ibáñez", 3, 91, 2_690_000, 44, 6, 4, 139)
UNAI = _j(1969, "Unai López", 3, 70, 2_680_000, 39, 4, 5, 97)
RAMON = _j(41411, "Ramón Enríquez", 3, 65, 400_000, 22, 4, 5, 0)
DANI = _j(41418, "Dani Lorenzo", 3, 65, 2_020_000, 35, 5, 4, 0)
YAMAL = _j(26271, "Yamal", 4, 3, 25_320_000, 112, 5, 5, 266)
ROBERTO = _j(35678, "Roberto Fernández", 4, 7, 7_320_000, 69, 5, 6, 157)
BOYE = _j(12494, "Boyé", 4, 91, 5_480_000, 61, 5, 4, 141)

# La puja viva de la mejora (se resuelve el domingo a las 07:00).
JUAN = _j(23840, "Juan Iglesias", 2, 17, 3_730_000, 51, 5, 5, 154)

# Los 14 de hoy, en el orden del artefacto.
PLANTILLA_14 = [GULACSI, KIKE, CHUST, GAYA, OLASAGASTI, IBANEZ, UNAI, DANI,
                YAMAL, ROBERTO, BOYE, CARDONA, ORTIZ, RAMON]

# Con Juan Iglesias, si se gana la puja.
PLANTILLA_15 = PLANTILLA_14 + [JUAN]

# La de antes del 31/10 (sin Dani Lorenzo ni Angel Ortiz).
PLANTILLA_12 = [j for j in PLANTILLA_14 if j not in (DANI, ORTIZ)]

# La del 27/10, ya vendido Jonny: once justos, un 4-3-3.
PLANTILLA_11 = [j for j in PLANTILLA_12 if j is not RAMON]

PLANTILLAS = {11: PLANTILLA_11, 12: PLANTILLA_12, 14: PLANTILLA_14, 15: PLANTILLA_15}

# (titularidad de FF, escalon), los del artefacto.
FF = {38433: (90.0, 40), 28115: (90.0, 50), 1760: (90.0, 50), 1844: (80.0, 40),
      30493: (50.0, 30), 35765: (50.0, 30), 29661: (80.0, 50), 14800: (80.0, 50),
      1969: (70.0, 50), 41411: (70.0, 25), 41418: (70.0, 40), 26271: (95.0, 60),
      35678: (90.0, 50), 12494: (90.0, 50), 23840: (90.0, 50)}


def _fila(pid, prob, valor):
    consenso = "STARTER" if prob >= 67 else ("BENCH" if prob <= 40 else "UNCERTAIN")
    return {"player_id": pid, "starter_probability": prob, "consensus": consenso,
            "source_coverage": 1,
            "hierarchy": {"value": valor, "label": ETIQUETAS[valor]},
            "availability": {"label": "DISPONIBLE", "can_play": True},
            "absence": None}


TABLERO = {"version": "V12.0_SINGLE_SOURCE", "source": "FUTBOLFANTASY", "matchday": 12,
           "players": [_fila(pid, *v) for pid, v in FF.items()]}

# Sin Jornada Perfecta (lo de produccion el 31/10).
JP_VACIA = {"source_state": "NOT_CONNECTED", "available": False, "lookup": {}}

# El once puesto en Biwenger el 31/10 (artefacto): 3-4-3.
LIVE_14 = {"source": "USER", "formation": "3-4-3",
           "player_ids": sorted([1760, 1844, 1969, 12494, 14800, 26271, 28115, 29661,
                                 35678, 38433, 41418])}

NOMBRES = {j["id"]: j["name"] for j in PLANTILLA_15}


def _foto(plantilla=None, estados=None, fuera=()) -> dict:
    """La foto con lo que lee el motor: la plantilla (con `estados`
    {id: status} encima) y el catalogo con los mismos estados.
    `fuera`, los ids que ya no estan (vendidos)."""
    jugadores = []
    for j in (PLANTILLA_14 if plantilla is None else plantilla):
        if j["id"] in fuera:
            continue
        j = dict(j)
        if estados and j["id"] in estados:
            j["status"] = estados[j["id"]]
        jugadores.append(j)
    return {"my_team": jugadores,
            "rounds": {"data": {"round": {"id": 5212}}},
            "catalog": {"data": {
                "teams": {},
                "players": {str(j["id"]): {"id": j["id"], "status": j["status"]}
                            for j in jugadores}}}}


def _huella(salida) -> str:
    crudo = json.dumps(salida, sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _ids(once) -> set:
    return {int(p["id"]) for p in once["selected"]}


class _Produccion:
    """
    Lo que la vuelta lee sola, suplantado: el tablero de FF y JP que
    `build_lineup` pide por su cuenta, el estado guardado del monitor y
    el once puesto en Biwenger (`live`, None si no se sabe). Todo vuelve
    a su sitio al salir.
    """

    def __init__(self, live=None, tablero=None):
        self.live = LIVE_14 if live is None else live
        self.tablero = TABLERO if tablero is None else tablero

    def __enter__(self):
        self._antes = (
            lineup_engine.build_starter_intelligence_for_snapshot,
            lineup_engine.build_lineup_intelligence,
            lineup_monitor.load_lineup_monitor_state,
            lineup_monitor.live_lineup,
        )
        tablero, live = self.tablero, self.live
        lineup_engine.build_starter_intelligence_for_snapshot = lambda snapshot: tablero
        lineup_engine.build_lineup_intelligence = lambda snapshot: copy.deepcopy(JP_VACIA)
        lineup_monitor.load_lineup_monitor_state = lambda: None
        lineup_monitor.live_lineup = lambda snapshot: copy.deepcopy(live)
        return self

    def __exit__(self, *_):
        (lineup_engine.build_starter_intelligence_for_snapshot,
         lineup_engine.build_lineup_intelligence,
         lineup_monitor.load_lineup_monitor_state,
         lineup_monitor.live_lineup) = self._antes
        return False


# ============================================================
# LAS BATERIAS
# ============================================================

ESTADOS = ("doubt", "injured", "sanctioned", "warned")


def _solos(plantilla, estados=ESTADOS) -> list:
    return [{j["id"]: e} for j in plantilla for e in estados]


def _parejas(plantilla, estados=ESTADOS) -> list:
    salida = []
    for i, a in enumerate(plantilla):
        for b in plantilla[i + 1:]:
            for ea in estados:
                for eb in estados:
                    salida.append({a["id"]: ea, b["id"]: eb})
    return salida


# Las parejas que cuenta el analisis del 31/10, en 14 y en 15.
PAREJAS_DEL_ANALISIS = [
    {12494: "doubt", 28115: "injured"},       # la J12: Boyé en duda, Kike lesionado
    {29661: "doubt", 14800: "injured"},       # Olasagasti en duda, Ibáñez lesionado
    {28115: "doubt", 1760: "doubt"},          # dos defensas en duda
    {26271: "doubt", 29661: "injured"},       # Yamal en duda, Olasagasti lesionado
    {38433: "doubt", 28115: "injured"},       # el unico portero en duda
    {38433: "injured", 12494: "doubt"},       # el unico portero lesionado
    {26271: "warned", 1760: "sanctioned"},
]

# La bateria de la verja: (plantilla, estados). Cabe en unos segundos.
BATERIA_CORTA = (
    [(n, {}) for n in (11, 12, 14, 15)]
    + [(11, e) for e in _solos(PLANTILLA_11)]
    + [(12, e) for e in _solos(PLANTILLA_12, ("doubt",))]
    + [(14, e) for e in _solos(PLANTILLA_14, ("doubt", "injured"))]
    + [(n, e) for n in (14, 15) for e in PAREJAS_DEL_ANALISIS]
)


def bateria_larga(n) -> list:
    """Con `n` jugadores: todos sanos, cada uno con cada estado y cada
    pareja con cada par de estados."""
    plantilla = PLANTILLAS[n]
    return [(n, {})] + [(n, e) for e in _solos(plantilla)] + [(n, e) for e in _parejas(plantilla)]


def _huellas(bateria, llamada) -> list:
    """La huella de `llamada(foto)` para cada escenario."""
    salida = []
    with _Produccion():
        for n, estados in bateria:
            salida.append(_huella(llamada(_foto(PLANTILLAS[n], estados))))
    return salida


def _resumen(huellas) -> str:
    return hashlib.sha256("".join(huellas).encode("ascii")).hexdigest()


# ============================================================
# LO DE HOY: main, con el motor sin tocar
# ============================================================
#
# La salida ENTERA de `build_lineup` en cada escenario de la bateria,
# medida con el `lineup_engine` de main ANTES de este cambio (main@fee1f551,
# 31/10/2026): sha256 del JSON ordenado de cada una (`_huella`), y
# sha256 de todas seguidas (`_resumen`). Apagado, tiene que salir la
# misma, letra a letra. Igual con y sin la memoria del once, y con
# PYTHONHASHSEED 3 y 11. Si algun dia se cambia el motor A PROPOSITO,
# se rehace con el interruptor apagado y se dice en el commit.
HUELLA_DE_MAIN = "6b2e87b70378ace38d8618f68d3f779c466462ced7349756ee096594d734b72b"
# La misma medida en Python 3.13, el de la vuelta (bordalas-live.yml): la
# salida cambia de version a version y la huella con ella. Medida tambien
# con el `lineup_engine` de main@fee1f551 en 3.13 (el gestor, 31/10/2026,
# tras la vuelta roja #2623): sale esta, asi que apagado sigue siendo lo
# mismo letra a letra; solo faltaba la huella de 3.13.
HUELLAS_DE_MAIN = {
    (3, 11): HUELLA_DE_MAIN,
    (3, 13): "84df35a06263706794a3f80f91ae1d9a5acab7401a4cec74c6afa3bc35e9ba41",
}

# La larga (`bateria_larga`), por tamaño de plantilla. No cabe en la
# verja (unos 15 minutos con 15 jugadores): se corre a mano,
# `python -m src.analysis.test_el_once_que_se_puede_escribir_v1 --larga`.
HUELLAS_LARGAS_DE_MAIN = {
    11: "b4012a14d42480d4c41dbe66b9c0d5423401b6acba4122cd986578e796b48511",
    12: "f697b17cbddd8216421d70dba6df25a9764beb8e3f0855f86a3820166f532c4c",
    14: "86480315cb3e3e6f4a996bc7abb93475fbc0f277928fa64adc4933799a789e3c",
    15: "11586fd46e8c7622478cab9220d355059a45778d940eb4261271b33d31e823ec",
}


# ============================================================
# EL EJECUTOR DE VERDAD, SIN RED
# ============================================================

class _Escribiria(Exception):
    """El ejecutor llego a llamar al escritor: habria escrito."""


class _EscritorQueNoSale:
    """El escritor de Biwenger, cambiado por uno que LANZA antes de
    tocar la red (y antes del rastro y del estado guardado). Comprueba
    lo mismo que el cliente real: once ids distintos."""

    ultimo = None

    def save_lineup(self, player_ids, formation, reserve_ids=None, execute=False):
        assert len(player_ids) == 11 and len(set(player_ids)) == 11, player_ids
        _EscritorQueNoSale.ultimo = {"player_ids": sorted(player_ids), "formation": formation}
        raise _Escribiria()


def _ejecutor(lineup) -> dict:
    """El veredicto del ejecutor de verdad sobre el SAVE_LINEUP de este
    once: su salida, o `{"status": "WOULD_WRITE"}` si llega a escribir."""
    from src.actions import autopilot_executor

    decision = {
        "action": "SAVE_LINEUP", "executable": True, "priority": 760,
        "temporal_gate": {"phase": "NORMAL", "operations_locked": False,
                          "hard_safety_mode": False},
        "data": {"lineup_monitor": {"lineup": lineup}},
    }
    original = autopilot_executor.BiwengerWriteClient
    autopilot_executor.BiwengerWriteClient = _EscritorQueNoSale
    _EscritorQueNoSale.ultimo = None
    try:
        return autopilot_executor.execute_autopilot_decision(decision, execute=True)
    except _Escribiria:
        return {"status": "WOULD_WRITE", **_EscritorQueNoSale.ultimo}
    finally:
        autopilot_executor.BiwengerWriteClient = original


def _monitor(n=14, estados=None, live=None, entorno=None, fuera=()) -> dict:
    """`build_lineup_monitor_state` con la produccion suplantada."""
    with _Interruptores(APAGADO if entorno is None else entorno), _Produccion(live=live):
        return lineup_monitor.build_lineup_monitor_state(
            _foto(PLANTILLAS[n], estados, fuera), persist=False)


def _lo_que_queda(estado) -> set:
    """Lo que se queda puesto en Biwenger tras la vuelta: lo que se
    escribe si se pide y el ejecutor lo acepta; si no, el once puesto."""
    if estado["should_save"] and _ejecutor(estado["lineup"])["status"] == "WOULD_WRITE":
        return _ids(estado["lineup"])
    return set(LIVE_14["player_ids"])


def _marca(once) -> dict:
    return once.get("el_once_que_se_puede_escribir") or {}


BLOQUEADO_DE_SIEMPRE = {
    "action": "SAVE_LINEUP",
    "status": "BLOCKED_INVALID_LINEUP",
    "reason": "El XI contiene 11 nombres, pero no 11 jugadores validos para la jornada.",
    "write_performed": False,
    "success": False,
    "http_status": None,
    "response": None,
}


# ============================================================
# 1. NACE APAGADO, Y APAGADO EL ONCE ES EL DE HOY
# ============================================================

def test_nace_apagado():
    from src.analysis import el_once_que_se_puede_escribir as escribible

    with _Interruptores({ENV: None}):
        assert escribible.activa() is False
    for valor, puesto in (("1", True), ("true", True), ("si", True), ("yes", True),
                          ("0", False), ("no", False), ("", False)):
        with _Interruptores({ENV: valor}):
            assert escribible.activa() is puesto, valor
    assert escribible.ENV == ENV
    # Un interruptor sin frase para el dueño pone la verja en rojo el dia
    # que se enciende (leccion del 26/10).
    from src.telemetry.el_tablon import QUE_HACE
    assert str(QUE_HACE.get(ENV) or "").strip(), "sin frase en QUE_HACE"


def test_apagado_el_once_es_el_de_hoy():
    # Los de 14 con un dudoso o un lesionado, y las parejas del analisis:
    # para pedirlo como `False` y para los que valoran con el interruptor.
    subconjunto = [i for i, (n, e) in enumerate(BATERIA_CORTA)
                   if n == 14 and (len(e) == 2 or 12494 in e or 26271 in e)]
    bateria = [BATERIA_CORTA[i] for i in subconjunto]
    with _Interruptores(APAGADO):
        hoy = _huellas(BATERIA_CORTA, build_lineup)
        # Apagado, pedirlo como `False` es lo mismo que no pedirlo.
        con_false = _huellas(bateria, lambda f: build_lineup(f, que_se_puede_escribir=False))
        # Lo que mueve el arreglo, dicho antes que la huella: apagado, el
        # once de la J12 sigue siendo el 3-4-3 con Boyé en duda (10
        # alineables).
        with _Produccion():
            j12 = build_lineup(_foto(PLANTILLA_14, {12494: "doubt", 28115: "injured"}))
    assert j12["formation_name"] == "3-4-3", j12["formation_name"]
    assert 12494 in _ids(j12) and j12["playable_count"] == 10, j12["playable_count"]
    assert "el_once_que_se_puede_escribir" not in j12
    esperada = HUELLAS_DE_MAIN.get(sys.version_info[:2])
    assert esperada is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    assert _resumen(hoy) == esperada, _resumen(hoy)

    por_escenario = dict(zip(range(len(BATERIA_CORTA)), hoy))
    assert con_false == [por_escenario[i] for i in subconjunto]

    # Puesto, los que valoran (sin el argumento) ven el de hoy, y sin que
    # corra ni una linea del modulo.
    from src.analysis import el_once_que_se_puede_escribir as escribible

    llamadas = []
    ordenar, marca = escribible.ordenar, escribible.marca

    def _espia_ordenar(*args, **kwargs):
        llamadas.append("ordenar")
        return ordenar(*args, **kwargs)

    def _espia_marca(*args, **kwargs):
        llamadas.append("marca")
        return marca(*args, **kwargs)

    escribible.ordenar, escribible.marca = _espia_ordenar, _espia_marca
    try:
        with _Interruptores(PUESTO):
            valoran = _huellas(bateria, build_lineup)
            del_que_valora = list(llamadas)
            with _Produccion():
                escribe = build_lineup(_foto(PLANTILLA_14, {12494: "doubt"}),
                                       que_se_puede_escribir=True)
    finally:
        escribible.ordenar, escribible.marca = ordenar, marca
    assert del_que_valora == [], del_que_valora
    assert llamadas and set(llamadas) == {"ordenar", "marca"}, llamadas
    assert valoran == [por_escenario[i] for i in subconjunto]
    assert escribe["formation_name"] == "3-5-2" and escribe["playable_count"] == 11


def test_apagado_el_ejecutor_y_el_monitor_son_los_de_hoy():
    # El monitor apagado da el mismo once que `build_lineup` a secas.
    for estados in PAREJAS_DEL_ANALISIS:
        estado = _monitor(14, estados)
        with _Interruptores(APAGADO), _Produccion():
            directo = build_lineup(_foto(PLANTILLA_14, estados))
        assert _huella(estado["lineup"]) == _huella(directo), estados
        assert "el_once_que_se_puede_escribir" not in estado["lineup"]

    # El ejecutor, con un once de 10 alineables y sin la marca: el bloqueo
    # de siempre, campo a campo. Y con 11, escribe.
    j12 = _monitor(14, {12494: "doubt", 28115: "injured"})
    assert j12["action"] == "UPDATE_LINEUP" and j12["should_save"] is True
    assert _ejecutor(j12["lineup"]) == BLOQUEADO_DE_SIEMPRE
    sano = _monitor(14, {28115: "injured"})
    assert sano["lineup"]["playable_count"] == 11
    assert _ejecutor(sano["lineup"])["status"] == "WOULD_WRITE"


# ============================================================
# 2. SOLO EL MONITOR LO PIDE, Y SOLO CON EL INTERRUPTOR
# ============================================================

def test_el_monitor_lo_pide_solo_con_el_interruptor():
    pedidos = []

    def _espia(snapshot, *args, **kwargs):
        pedidos.append(kwargs.get("que_se_puede_escribir"))
        return lineup_engine.build_lineup(snapshot, *args, **kwargs)

    original = lineup_monitor.build_lineup
    lineup_monitor.build_lineup = _espia
    try:
        apagado = _monitor(14, {12494: "doubt"})
        puesto = _monitor(14, {12494: "doubt"}, entorno=PUESTO)
    finally:
        lineup_monitor.build_lineup = original

    assert pedidos == [False, True], pedidos
    assert 12494 in _ids(apagado["lineup"]) and apagado["action"] == "KEEP_LINEUP"
    assert 12494 not in _ids(puesto["lineup"]) and puesto["action"] == "UPDATE_LINEUP"
    assert _marca(puesto["lineup"])["motivo"] == "SANO"


# ============================================================
# 3. ENCENDIDO, EL ONCE QUE LLEGA A SAVE_LINEUP SE ESCRIBE
# ============================================================

def test_la_j12_boye_en_duda_y_kike_lesionado():
    """El de la J12 (Sevilla-Alavés, viernes 06/11): el 3-5-2 sano, con
    Ramón Enríquez, en vez del 3-4-3 con Boyé que se bloqueaba."""
    estados = {12494: "doubt", 28115: "injured"}
    for n in (14, 15):
        hoy = _monitor(n, estados)
        assert hoy["action"] == "UPDATE_LINEUP"
        assert _ejecutor(hoy["lineup"])["status"] == "BLOCKED_INVALID_LINEUP"
        # Hoy, Kike lesionado se queda en Biwenger.
        assert 28115 in _lo_que_queda(hoy)

        arreglo = _monitor(n, estados, entorno=PUESTO)
        once = arreglo["lineup"]
        assert once["formation_name"] == "3-5-2", (n, once["formation_name"])
        assert once["playable_count"] == 11 and once["used_warning_players"] is False
        assert 12494 not in _ids(once) and 28115 not in _ids(once)
        assert 41411 in _ids(once), sorted(_ids(once))          # Ramón Enríquez
        assert _marca(once) == {**_marca(once), "se_puede_escribir": True,
                                "motivo": "SANO", "autorizados": []}
        assert arreglo["action"] == "UPDATE_LINEUP" and arreglo["should_save"] is True
        assert _ejecutor(once)["status"] == "WOULD_WRITE"
        queda = _lo_que_queda(arreglo)
        assert 28115 not in queda and 12494 not in queda
        # Boyé, al banquillo con su motivo de siempre.
        boye = {f["id"]: f for f in once["bench"]}[12494]
        assert boye["reason"] == "EN_DUDA", boye["reason"]


def test_un_delantero_en_duda_ya_no_congela_el_once():
    """Boyé en duda, solo: hoy el 3-4-3 con el es el puesto (KEEP_LINEUP)
    y no se toca, con 10 alineables. Encendido, se escribe el sano."""
    for pid in (12494, 35678):                                   # Boyé, Roberto
        hoy = _monitor(14, {pid: "doubt"})
        assert hoy["action"] == "KEEP_LINEUP" and hoy["lineup"]["playable_count"] == 10
        arreglo = _monitor(14, {pid: "doubt"}, entorno=PUESTO)
        assert arreglo["lineup"]["playable_count"] == 11, pid
        assert pid not in _ids(arreglo["lineup"])
        assert arreglo["action"] == "UPDATE_LINEUP"
        assert _ejecutor(arreglo["lineup"])["status"] == "WOULD_WRITE"


def test_con_un_dudoso_gana_el_once_sano_de_cualquier_dibujo():
    casos = [
        # Olasagasti en duda y Pablo Ibáñez lesionado: el 4-3-3 sano.
        ({29661: "doubt", 14800: "injured"}, "4-3-3", {29661, 14800}),
        # Kike y Chust en duda: el 3-4-3 con Gayà, Cardona y Angel Ortiz.
        ({28115: "doubt", 1760: "doubt"}, "3-4-3", {28115, 1760}),
    ]
    for estados, dibujo, fuera in casos:
        hoy = _monitor(14, estados)
        assert _ejecutor(hoy["lineup"])["status"] == "BLOCKED_INVALID_LINEUP", estados
        arreglo = _monitor(14, estados, entorno=PUESTO)
        once = arreglo["lineup"]
        assert once["formation_name"] == dibujo, (estados, once["formation_name"])
        assert once["playable_count"] == 11 and not (_ids(once) & fuera)
        assert _ejecutor(once)["status"] == "WOULD_WRITE"
    once = _monitor(14, {28115: "doubt", 1760: "doubt"}, entorno=PUESTO)["lineup"]
    assert {1844, 30493, 35765} <= _ids(once), sorted(_ids(once))

    # Un dudoso que no entraba en el once no cambia nada: el de siempre.
    hoy = _monitor(14, {35765: "doubt"})
    arreglo = _monitor(14, {35765: "doubt"}, entorno=PUESTO)
    assert _ids(arreglo["lineup"]) == _ids(hoy["lineup"]) == set(LIVE_14["player_ids"])
    assert arreglo["action"] == "KEEP_LINEUP"


def test_un_dios_en_duda_juega_y_se_escribe():
    """La regla del 18/08: un Dios juega salvo 0 % asegurado, y una duda
    no lo es. Hoy juega y se bloquea; encendido, juega y se escribe."""
    estados = {26271: "doubt", 29661: "injured"}                 # Yamal, Olasagasti
    hoy = _monitor(14, estados)
    assert _ejecutor(hoy["lineup"])["status"] == "BLOCKED_INVALID_LINEUP"
    assert 29661 in _lo_que_queda(hoy)                           # se queda el lesionado

    arreglo = _monitor(14, estados, entorno=PUESTO)
    once = arreglo["lineup"]
    assert 26271 in _ids(once) and 29661 not in _ids(once)
    assert once["playable_count"] == 10                          # se sigue contando igual
    marca = _marca(once)
    assert marca["se_puede_escribir"] is True and marca["motivo"] == "UN_DIOS_EN_DUDA"
    assert marca["autorizados"] == [26271], marca
    assert _ejecutor(once)["status"] == "WOULD_WRITE"
    assert 29661 not in _lo_que_queda(arreglo)

    # Solo: se queda puesto (es el once de Biwenger), ahora autorizado.
    solo = _monitor(14, {26271: "doubt"}, entorno=PUESTO)
    assert solo["action"] == "KEEP_LINEUP" and 26271 in _ids(solo["lineup"])
    assert _marca(solo["lineup"])["motivo"] == "UN_DIOS_EN_DUDA"

    # Los tres delanteros en duda: el 4-5-1 con Yamal, sin los otros dos.
    tres = _monitor(14, {26271: "doubt", 35678: "doubt", 12494: "doubt"}, entorno=PUESTO)
    assert tres["lineup"]["formation_name"] == "4-5-1"
    assert _ids(tres["lineup"]) & {26271, 35678, 12494} == {26271}
    assert _ejecutor(tres["lineup"])["status"] == "WOULD_WRITE"


def test_sin_once_sano_el_que_lleva_menos_dudosos():
    """El unico portero en duda: ningun dibujo se llena sin el. Se escribe
    con Gulácsi (y solo con el en duda) en vez de dejar al lesionado."""
    hoy = _monitor(14, {38433: "doubt", 28115: "injured"})
    assert _ejecutor(hoy["lineup"])["status"] == "BLOCKED_INVALID_LINEUP"
    assert 28115 in _lo_que_queda(hoy)

    for estados in ({38433: "doubt", 28115: "injured"},
                    {38433: "doubt", 28115: "injured", 12494: "doubt"}):
        arreglo = _monitor(14, estados, entorno=PUESTO)
        once = arreglo["lineup"]
        marca = _marca(once)
        assert marca["motivo"] == "SIN_ONCE_SANO" and marca["autorizados"] == [38433], marca
        assert 38433 in _ids(once) and 28115 not in _ids(once)
        # Boyé en duda tambien: fuera, que su hueco lo llena un sano.
        assert (12494 in _ids(once)) is (12494 not in estados), estados
        assert once["playable_count"] == 10
        assert _ejecutor(once)["status"] == "WOULD_WRITE"
        assert 28115 not in _lo_que_queda(arreglo)

    # Con once justos (la plantilla del 27/10), uno en duda: el mismo
    # once, ahora escrito.
    hoy = _monitor(11, {29661: "doubt"})
    assert _ejecutor(hoy["lineup"])["status"] == "BLOCKED_INVALID_LINEUP"
    arreglo = _monitor(11, {29661: "doubt"}, entorno=PUESTO)
    assert _ids(arreglo["lineup"]) == _ids(hoy["lineup"])
    assert _marca(arreglo["lineup"])["autorizados"] == [29661]
    assert _ejecutor(arreglo["lineup"])["status"] == "WOULD_WRITE"


def test_sin_once_de_once_nada_que_escribir():
    """El unico portero lesionado: no hay once de 11. Como hoy, nada que
    escribir (solo lo arregla un segundo portero)."""
    for estados in ({38433: "injured"}, {38433: "injured", 12494: "doubt"}):
        hoy = _monitor(14, estados)
        arreglo = _monitor(14, estados, entorno=PUESTO)
        assert hoy["action"] == arreglo["action"] == "BLOCKED_INCOMPLETE_LINEUP"
        assert arreglo["should_save"] is False
        assert _marca(arreglo["lineup"])["motivo"] == "SIN_ONCE_DE_ONCE"
        assert _marca(arreglo["lineup"])["se_puede_escribir"] is False


def test_encendido_lo_que_se_pide_siempre_se_escribe():
    """Cada estado solo y cada pareja de estados de los del analisis, en
    14 y 15: encendido, todo SAVE_LINEUP pedido lo acepta el ejecutor, y
    nunca se queda en Biwenger un lesionado o sancionado si habia once."""
    malos = {"injured", "sanctioned"}
    escenarios = ([(14, e) for e in _solos(PLANTILLA_14, ("doubt", "injured"))]
                  + [(n, e) for n in (14, 15) for e in PAREJAS_DEL_ANALISIS])
    for n, estados in escenarios:
        estado = _monitor(n, estados, entorno=PUESTO)
        if estado["should_save"]:
            assert _ejecutor(estado["lineup"])["status"] == "WOULD_WRITE", (n, estados)
        if len(estado["lineup"]["selected"]) == 11:
            queda = _lo_que_queda(estado)
            assert not {p for p, e in estados.items() if e in malos} & queda, (n, estados)


# ============================================================
# 4. EL EJECUTOR: SIN LA MARCA EL DE HOY; CON ELLA, SOLO LO AUTORIZADO
# ============================================================

def test_el_ejecutor_solo_deja_pasar_lo_autorizado():
    from src.analysis import el_once_que_se_puede_escribir as escribible

    once = _monitor(14, {26271: "doubt", 29661: "injured"}, entorno=PUESTO)["lineup"]
    assert _ejecutor(once)["status"] == "WOULD_WRITE"
    assert escribible.admite(once) is True

    def _con(**cambios):
        otro = copy.deepcopy(once)
        marca = otro["el_once_que_se_puede_escribir"]
        for clave, valor in cambios.items():
            if clave == "selected":
                otro["selected"] = valor(otro["selected"])
            elif valor is None:
                marca.pop(clave, None)
            else:
                marca[clave] = valor
        return otro

    sin_marca = copy.deepcopy(once)
    sin_marca.pop("el_once_que_se_puede_escribir")
    malos = {
        "sin la marca": sin_marca,
        "la marca dice que no": _con(se_puede_escribir=False),
        "sin autorizar": _con(autorizados=[]),
        "otro autorizado": _con(autorizados=[12494]),
        "sin autorizados": _con(autorizados=None),
        "el autorizado no es alineable": _con(selected=lambda s: [
            {**p, "lineup_eligible": False} if p["id"] == 26271 else p for p in s]),
        "un id repetido": _con(selected=lambda s: s[:-1] + [dict(s[0])]),
        "diez": _con(selected=lambda s: s[:-1]),
        "marca de mentira": {**sin_marca, "el_once_que_se_puede_escribir": "si"},
    }
    for motivo, lineup in malos.items():
        assert escribible.admite(lineup) is False, motivo
        resultado = _ejecutor(lineup)
        assert resultado["status"] in ("BLOCKED_INVALID_LINEUP", "BLOCKED_INCOMPLETE_LINEUP"), (
            motivo, resultado)
        assert resultado["write_performed"] is False, motivo
    assert _ejecutor(sin_marca) == BLOQUEADO_DE_SIEMPRE


def test_el_monitor_no_pide_lo_que_no_se_puede_escribir():
    """Si la ordenacion fallase (cae a la de siempre, con Boyé en duda
    dentro), la marca dice NO_SE_PUEDE_ESCRIBIR y el monitor no pide el
    SAVE_LINEUP: no se come la escritura de la vuelta."""
    from src.analysis import el_once_que_se_puede_escribir as escribible

    original = escribible._completo
    escribible._completo = _revienta
    try:
        estado = _monitor(14, {12494: "doubt", 28115: "injured"}, entorno=PUESTO)
    finally:
        escribible._completo = original
    once = estado["lineup"]
    assert 12494 in _ids(once) and once["playable_count"] == 10
    assert _marca(once)["motivo"] == "NO_SE_PUEDE_ESCRIBIR"
    assert estado["action"] == "BLOCKED_INVALID_LINEUP" and estado["should_save"] is False


def test_con_el_once_sin_los_que_se_van():
    """Con los dos interruptores: la busqueda sin los que se van usa la
    misma ordenacion, y el once sigue siendo uno que se puede escribir."""
    from src.analysis import el_once_sin_los_que_se_van as sin_ellos

    def _preparado(snapshot, players, lineup_intelligence, **_kwargs):
        return {"se_van": {35678: ["LA_ORDEN_DEL_GESTOR"]}, "se_quedan": {},
                "jp": {"vale": False, "motivo": "lab"}, "segundos_al_cierre": None}

    original = sin_ellos.preparar
    sin_ellos.preparar = _preparado
    try:
        estado = _monitor(14, {12494: "doubt", 28115: "injured"},
                          entorno={**PUESTO, ENV_SIN_ELLOS: "1"})
    finally:
        sin_ellos.preparar = original
    once = estado["lineup"]
    assert "el_once_sin_los_que_se_van" in once
    assert len(once["selected"]) == 11 and once["playable_count"] == 11
    assert 12494 not in _ids(once) and 28115 not in _ids(once)
    assert _marca(once)["se_puede_escribir"] is True
    assert _ejecutor(once)["status"] == "WOULD_WRITE"


# ============================================================
# 5. NUNCA LANZA
# ============================================================

def _revienta(*_args, **_kwargs):
    raise RuntimeError("revienta a proposito")


def test_nunca_lanza():
    from src.analysis import el_once_que_se_puede_escribir as escribible

    candidatas = [{"formation_name": "3-4-3", "selected": [], "score": 0.0}]
    for basura in (None, 7, "x", [None], [{"id": "?"}], [{}]):
        assert escribible.ordenar(basura, candidatas, lineup_engine.FORMATIONS,
                                  _revienta) == candidatas
        assert escribible.ordenar([{"id": 1, "lineup_eligible": True}], basura,
                                  lineup_engine.FORMATIONS, _revienta) == basura
        assert escribible.marca(basura, basura, basura)["se_puede_escribir"] is False
        assert escribible.admite(basura) is False
        assert escribible.sano(basura) is False and escribible.en_duda(basura) is False
    # La busqueda que revienta: las de siempre.
    dudoso = [{"id": 1, "lineup_eligible": True, "automatic_lineup": False}]
    assert escribible.ordenar(dudoso, candidatas, lineup_engine.FORMATIONS,
                              _revienta) == candidatas
    # Un interruptor que no se puede leer: apagado.
    class _OsQueRevienta:
        @property
        def environ(self):
            raise RuntimeError("revienta a proposito")

    antes = escribible.os
    try:
        escribible.os = _OsQueRevienta()
        assert escribible.activa() is False
        assert lineup_monitor._el_once_que_se_puede_escribir() is False
    finally:
        escribible.os = antes
    # Y el monitor con basura no se cree que no se puede escribir.
    assert lineup_monitor._no_se_puede_escribir(None) is False
    assert lineup_monitor._no_se_puede_escribir({"selected": []}) is False


TESTS = [
    test_nace_apagado,
    test_apagado_el_once_es_el_de_hoy,
    test_apagado_el_ejecutor_y_el_monitor_son_los_de_hoy,
    test_el_monitor_lo_pide_solo_con_el_interruptor,
    test_la_j12_boye_en_duda_y_kike_lesionado,
    test_un_delantero_en_duda_ya_no_congela_el_once,
    test_con_un_dudoso_gana_el_once_sano_de_cualquier_dibujo,
    test_un_dios_en_duda_juega_y_se_escribe,
    test_sin_once_sano_el_que_lleva_menos_dudosos,
    test_sin_once_de_once_nada_que_escribir,
    test_encendido_lo_que_se_pide_siempre_se_escribe,
    test_el_ejecutor_solo_deja_pasar_lo_autorizado,
    test_el_monitor_no_pide_lo_que_no_se_puede_escribir,
    test_con_el_once_sin_los_que_se_van,
    test_nunca_lanza,
]


def larga(tamanos) -> int:
    """La bateria larga, apagada y con el interruptor puesto (los que
    valoran), contra `HUELLAS_LARGAS_DE_MAIN`. A mano: no cabe en la
    verja."""
    fallos = 0
    for n in tamanos:
        for nombre, entorno in (("apagado", APAGADO), ("puesto, los que valoran", PUESTO)):
            with _Interruptores(entorno):
                resumen = _resumen(_huellas(bateria_larga(n), build_lineup))
            bien = resumen == HUELLAS_LARGAS_DE_MAIN[n]
            fallos += not bien
            print(f"{'OK  ' if bien else 'FALLA'} larga {n} ({nombre}): {resumen}")
    return fallos


def main() -> None:
    if "--larga" in sys.argv:
        tamanos = [int(x) for x in sys.argv[sys.argv.index("--larga") + 1:]] or [11, 12, 14, 15]
        sys.exit(1 if larga(tamanos) else 0)
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
