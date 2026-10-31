"""
EL ONCE SIN LOS QUE SE VAN (27/10/2026). Guardias de
`src/analysis/el_once_sin_los_que_se_van.py` y de su enganche en
`lineup_engine.build_lineup` y `lineup_monitor.build_lineup_monitor_state`.

EL CASO (26/10/2026, J11)

    El once escrito llevaba a Jonny (que la orden vendia esa noche:
    `vender_si_ficha` con Kike Salas ya dentro) en vez de a Sergi
    Cardona. FF los tenia a los dos al 50 %; Jonny 'Importante' (27
    puntos) y Cardona 'Rotacion' (22). Jornada Perfecta tenia a Cardona
    de titular y a Jonny al 40 % (SUPLENTE), y el motor no la miraba.

QUE SE COMPRUEBA

    1. NACE APAGADO, y apagado el once es el de hoy byte a byte: la
       huella de `build_lineup` sale clavada a la de main@a454432c
       sobre el mismo banco, pedido o no, con la orden viva. Puesto,
       los que valoran (`build_lineup(foto)` a secas) tambien, y sin
       que corra ni una linea del modulo.
    2. Solo el monitor (el once que se escribe) lo pide, y solo con el
       interruptor.
    3. EL 26/10: con la orden, Cardona juega y Jonny no; el banquillo
       dice SE_VA; ningun numero castigado sale del motor.
    4. EL 26/10 SIN LA ORDEN: Jornada Perfecta desempata. Y cuando no
       toca (margen, edad, jornada, veredictos, sin FF, un Dios, uno
       que se va, un PROBABLE dentro, uno en duda fuera), no desempata.
    5. Sin alternativa juega el que se va; si hace falta, cambia el
       dibujo. Y solo por uno de fiar: ni en duda (el once no baja de
       11 alineables sin aviso, revision del 27/10), ni sin pronostico,
       ni al 0 % o lejos de el.
    6. Quien se va y quien no, regla a regla (`los_que_se_van`, pura):
       las puertas de `decidir`, EL PARTE DEL RELEVO y si se cobra
       antes del cierre (la puja ya no cuenta).
    7. Quien no se sienta aunque se venda: un Dios, el que juega la
       ronda de aplazados, el que no se cobra antes del cierre.
    8. La memoria del once no mezcla al que valora con el que escribe.
    9. Nunca lanza: si algo falla, el once de hoy.

DE DONDE SALEN LOS NUMEROS

    Todo escrito aqui. Los ids, los nombres, los equipos, los precios,
    los puntos y la titularidad son los del panel del 26-27/10; la
    orden, la del gestor de ese dia (git 5fb3aee2). Ni la carpeta de
    estado, ni la foto, ni la red, ni el reloj: el tablero de FF, JP,
    el calendario, las rondas de aplazados, los libros y la hora se
    suplantan (`_Produccion`).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import sys

from datetime import datetime
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Todo lo que mueve
# el once o los libros se quita aqui arriba; cada prueba pone lo suyo.
ENV = "BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN"
ENV_UNA_VEZ = "BORDALAS_EL_ONCE_UNA_VEZ"
ENV_ORDEN = "BORDALAS_LA_ORDEN_DEL_GESTOR"
ENV_MEJORA = "BORDALAS_LA_MEJORA_DEL_ONCE"
ENV_ROTACION = "BORDALAS_LA_ROTACION"
for _nombre in (
    ENV, ENV_UNA_VEZ, ENV_ORDEN, ENV_MEJORA, ENV_ROTACION,
    "BORDALAS_EL_CALENDARIO_EN_EL_ONCE", "BORDALAS_CALIDAD_ETIQUETA",
    "BORDALAS_VARA_PLANA",
    # EL ONCE QUE SE PUEDE ESCRIBIR TAMPOCO (31/10/2026). Puesto, el once
    # del monitor trae su marca y la huella de main no cuadra
    # (`--con BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR`).
    "BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR",
):
    os.environ.pop(_nombre, None)


from src.analysis import el_once_se_busca_una_vez as una_vez  # noqa: E402
from src.analysis import el_once_sin_los_que_se_van as sin_ellos  # noqa: E402
from src.analysis import lineup_engine, lineup_monitor  # noqa: E402
from src.analysis.lineup_engine import build_lineup, prepare_players  # noqa: E402
from src.analysis.position_policy import (  # noqa: E402
    assert_lineup_position_integrity,
)


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


APAGADO = {ENV: None, ENV_ORDEN: None, ENV_MEJORA: None, ENV_ROTACION: None, ENV_UNA_VEZ: None}


def _con(**puestos) -> dict:
    """Todo apagado salvo lo que se nombra: `_con(ENV=1, ORDEN=1)`."""
    nombres = {"ENV": ENV, "ORDEN": ENV_ORDEN, "MEJORA": ENV_MEJORA,
               "ROTACION": ENV_ROTACION, "UNA_VEZ": ENV_UNA_VEZ}
    return {**APAGADO, **{nombres[k]: "1" for k, v in puestos.items() if v}}


# ============================================================
# EL BANCO DEL 26/10
# ============================================================

def _j(pid, nombre, pos, equipo, precio, puntos, pasada=100):
    """La misma base para todos (diez partidos, 100 puntos la pasada),
    con su precio y sus puntos del panel."""
    return {"id": pid, "name": nombre, "position": pos, "teamID": equipo, "price": precio,
            "points": puntos, "played_home": 5, "played_away": 5, "pointsLastSeason": pasada,
            "status": "ok"}


GULACSI = _j(38433, "Gulácsi", 1, 19, 2_470_000, 29)
KIKE = _j(28115, "Kike Salas", 2, 17, 3_170_000, 35)
CHUST = _j(1760, "Chust", 2, 75, 2_260_000, 41)
GAYA = _j(1844, "Gayà", 2, 18, 1_740_000, 27)
CARDONA = _j(30493, "Sergi Cardona", 2, 19, 1_610_000, 22)
JONNY = _j(1599, "Jonny", 2, 5, 1_450_000, 27)
OLASAGASTI = _j(29661, "Olasagasti", 3, 10, 2_970_000, 50)
IBANEZ = _j(14800, "Pablo Ibáñez", 3, 91, 2_660_000, 44)
UNAI = _j(1969, "Unai López", 3, 70, 2_550_000, 39)
YAMAL = _j(26271, "Yamal", 4, 3, 25_520_000, 112)
ROBERTO = _j(35678, "Roberto Fernández", 4, 7, 7_680_000, 66)
BOYE = _j(12494, "Boyé", 4, 91, 5_440_000, 61)

# Para dos pruebas: un cuarto medio flojo y un cuarto delantero.
MEDIO_DE_RELLENO = _j(77001, "Medio de relleno", 3, 8, 400_000, 6)
DELANTERO_DE_RELLENO = _j(77002, "Delantero de relleno", 4, 8, 900_000, 20)

# Para la revision del 27/10, fuera del tablero de siempre (su FF se da
# con `_tablero` en cada prueba): un cuarto medio de fiar, uno en duda
# (flojo: apagado no le gana a Jonny) y un lateral que entra por la
# mejora (De Haas).
MEDIO_DE_FIAR = _j(77003, "Medio de fiar", 3, 8, 900_000, 20)
MEDIO_EN_DUDA = {**_j(77005, "Medio en duda", 3, 8, 400_000, 6), "status": "doubt"}
DE_HAAS = _j(77004, "De Haas", 2, 12, 1_300_000, 18)

PLANTILLA = [GULACSI, KIKE, CHUST, GAYA, CARDONA, JONNY, OLASAGASTI, IBANEZ, UNAI,
             YAMAL, ROBERTO, BOYE]

SIN_CARDONA = [j for j in PLANTILLA if j is not CARDONA]

ETIQUETAS = {60: "Dios", 50: "Clave", 40: "Importante", 30: "Rotación", 20: "Reserva"}

# (titularidad de FF, escalon), los del panel.
FF = {38433: (90.0, 40), 28115: (90.0, 50), 1760: (90.0, 50), 1844: (80.0, 40),
      30493: (50.0, 30), 1599: (50.0, 40), 29661: (80.0, 50), 14800: (80.0, 50),
      1969: (70.0, 50), 26271: (95.0, 60), 35678: (90.0, 50), 12494: (90.0, 50),
      77001: (20.0, 20), 77002: (50.0, 30)}


def _fila(pid, prob, valor):
    consenso = "STARTER" if prob >= 67 else ("BENCH" if prob <= 40 else "UNCERTAIN")
    return {"player_id": pid, "starter_probability": prob, "consensus": consenso,
            "source_coverage": 1, "hierarchy": {"value": valor, "label": ETIQUETAS[valor]}}


def _tablero(cambios=None) -> dict:
    """El tablero de FF; `cambios` {id: (prob, escalon)} o {id: None}
    para quitarle el pronostico."""
    ff = {**FF, **(cambios or {})}
    return {"version": "V12.0_SINGLE_SOURCE", "source": "FUTBOLFANTASY", "matchday": 11,
            "players": [_fila(pid, *v) for pid, v in ff.items() if v is not None]}


TABLERO = _tablero()


def _jp(veredictos=None, ronda=11, edad=1.0, disponible=True) -> dict:
    """El bloque de `build_lineup_intelligence`: {id: (estado, confianza)}
    o {id: None} para uno sin casar."""
    lookup = {}
    for pid, v in (veredictos or {}).items():
        lookup[pid] = (
            {"matched": False, "status": "UNKNOWN", "confidence": 0}
            if v is None else {"matched": True, "status": v[0], "confidence": v[1]}
        )
    return {"source_state": "JORNADA_PERFECTA", "available": disponible, "round": ronda,
            "age_hours": edad, "updated_at": "2026-10-26T10:00:00+00:00", "lookup": lookup}


# JP del 26/10: Cardona Titular (perfil, 96) y Jonny al 40 % (SUPLENTE).
VEREDICTOS_26 = {30493: ("TITULAR", 96), 1599: ("SUPLENTE", 40)}
JP_26 = _jp(VEREDICTOS_26)

# Sin Jornada Perfecta: no desempata nada.
JP_VACIA = {"source_state": "NOT_CONNECTED", "available": False, "lookup": {}}

DIA = 24 * 3600
HORA = 3600

# El calendario de la J11 visto el 26/10 a mediodia: cuatro dias al cierre.
RELOJ = {"target_matchday": 11, "seconds_to_deadline": 4 * DIA}

# Las rondas (`la_rotacion.el_reloj`): la proxima es entera.
SIN_APLAZADOS = {"sin_calendario": False, "ronda_parcial": False, "equipos_parcial": None}

AHORA = "2026-10-26T12:00:00+01:00"

# La orden del 26/10 (git 5fb3aee2): vender a Jonny cuando este Kike.
JONNY_SE_VENDE = {"player_id": 1599, "nombre": "Jonny", "suelo": 1_450_000}


def _orden(jugadores=(JONNY_SE_VENDE,), si_esta=28115, caduca="2026-11-30T23:59:00+01:00",
           **mas) -> dict:
    venta = {"jugadores": [dict(j) for j in jugadores]}
    if si_esta is not None:
        venta["si_esta"] = si_esta
    return {"caduca": caduca, "vender_si_ficha": venta, **mas}


ORDEN_26 = _orden()

SIN_PAREJAS = {"salen": set(), "entran": set(), "se_van": set()}

LIBROS_VACIOS = {"orden": None, "mejora": {}, "parejas": SIN_PAREJAS}
LIBROS_26 = {"orden": ORDEN_26, "mejora": {}, "parejas": SIN_PAREJAS}


def _foto(plantilla=None, liga=True, estados=None, ofertas=None, equipos=None,
          saldo=250_000) -> dict:
    """La foto con lo que lee el motor (la plantilla) y lo que lee el
    once que se escribe (la liga, el mercado, el saldo y el catalogo).

        estados   {id: status} del catalogo (`todaLaLiga`); por defecto
                  el de la ficha de cada uno de la plantilla
        ofertas   {id: importe} del Computer por los nuestros
        equipos   {teamID: nombre} del catalogo
    """
    jugadores = [dict(j) for j in (PLANTILLA if plantilla is None else plantilla)]
    catalogo = {str(j["id"]): {"id": j["id"], "status": j.get("status")} for j in jugadores}
    for pid, estado in (estados or {}).items():
        catalogo[str(pid)] = {"id": pid, "status": estado}
    foto = {"my_team": jugadores,
            "rounds": {"data": {"round": {"id": 5211}}},
            "catalog": {"data": {
                "teams": {str(k): {"id": k, "name": v} for k, v in (equipos or {}).items()},
                "players": catalogo}}}
    if liga:
        foto["league"] = {"id": 1, "user": {"id": 777}}
        foto["market"] = {
            "sales": [],
            "offers": [{"id": 90_000 + n, "amount": importe, "status": "waiting",
                        "requestedPlayers": [{"id": pid}]}
                       for n, (pid, importe) in enumerate((ofertas or {}).items())],
            "status": {"balance": saldo, "maximumBid": 5_000_000}}
    return foto


def _huella(salida) -> str:
    crudo = json.dumps(salida, sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _ids(once) -> set:
    return {int(p["id"]) for p in once["selected"]}


def _banco(once) -> dict:
    return {int(f["id"]): f for f in once["bench"]}


def _revienta(*_args, **_kwargs):
    raise RuntimeError("revienta a proposito")


class _Produccion:
    """
    Lo que la vuelta lee sola, suplantado: el tablero de FF y JP que
    `build_lineup` pide por su cuenta, el calendario, los libros y la
    hora del once que se escribe, y el estado guardado del monitor.
    `reloj` y `libros` pueden ser una funcion (para hacerlos fallar).
    Todo vuelve a su sitio al salir.
    """

    def __init__(self, tablero=None, jp=None, reloj=None, libros=None, ahora=AHORA,
                 rondas=None):
        self.tablero = TABLERO if tablero is None else tablero
        self.jp = JP_26 if jp is None else jp
        self.reloj = RELOJ if reloj is None else reloj
        self.libros = LIBROS_VACIOS if libros is None else libros
        self.ahora = datetime.fromisoformat(ahora)
        self.rondas = SIN_APLAZADOS if rondas is None else rondas

    def __enter__(self):
        self._antes = (
            lineup_engine.build_starter_intelligence_for_snapshot,
            lineup_engine.build_lineup_intelligence,
            sin_ellos._el_reloj, sin_ellos._libros_de_produccion, sin_ellos._ahora,
            sin_ellos._las_rondas,
            lineup_monitor.load_lineup_monitor_state,
        )
        tablero, jp, reloj, libros, ahora, rondas = (
            self.tablero, self.jp, self.reloj, self.libros, self.ahora, self.rondas)
        lineup_engine.build_starter_intelligence_for_snapshot = lambda snapshot: tablero
        lineup_engine.build_lineup_intelligence = lambda snapshot: copy.deepcopy(jp)
        sin_ellos._el_reloj = reloj if callable(reloj) else (lambda snapshot: dict(reloj))
        sin_ellos._libros_de_produccion = (
            libros if callable(libros) else (lambda: copy.deepcopy(libros)))
        sin_ellos._ahora = lambda: ahora
        sin_ellos._las_rondas = rondas if callable(rondas) else (lambda _ahora: dict(rondas))
        lineup_monitor.load_lineup_monitor_state = lambda: None
        una_vez.olvidar()
        return self

    def __exit__(self, *_):
        (lineup_engine.build_starter_intelligence_for_snapshot,
         lineup_engine.build_lineup_intelligence,
         sin_ellos._el_reloj, sin_ellos._libros_de_produccion, sin_ellos._ahora,
         sin_ellos._las_rondas,
         lineup_monitor.load_lineup_monitor_state) = self._antes
        una_vez.olvidar()
        return False


def _once(foto=None, pedido=None, **produccion) -> dict:
    """`build_lineup` con la produccion suplantada. `pedido` None: la
    llamada de los que valoran, sin el argumento nuevo."""
    with _Produccion(**produccion):
        foto = _foto() if foto is None else foto
        if pedido is None:
            return build_lineup(foto)
        return build_lineup(foto, sin_los_que_se_van=pedido)


# ============================================================
# LO DE HOY: main@a454432c, con el motor sin tocar
# ============================================================
#
# La salida ENTERA de `build_lineup` sobre el banco del 26/10 (JP_26,
# el tablero de arriba), medida con el `lineup_engine` de main antes de
# este cambio: sha256 del JSON ordenado (`_huella`). Apagado, tiene que
# salir la misma, letra a letra. Si algun dia se cambia el motor A
# PROPOSITO, se rehace con el interruptor apagado y se dice en el commit.
#
# Medida el 27/10/2026 en main@a454432c (lineup_engine y lineup_monitor
# sin tocar), igual con PYTHONHASHSEED 3 y 11. El once: 4-3-3 con Jonny,
# y Cardona en el banquillo con «puntúa menos que Jonny» (el 26/10).
HUELLA_DE_MAIN = "8ef3e41aa100d88c01dcea877ca5a1870ef6f5cc062036bb5f73dbb3220dbdb4"


# ============================================================
# 1. NACE APAGADO, Y APAGADO EL ONCE ES EL DE HOY
# ============================================================

def test_nace_apagado():
    with _Interruptores({ENV: None}):
        assert sin_ellos.activa() is False
    for valor, puesto in (("1", True), ("si", True), ("0", False), ("no", False), ("", False)):
        with _Interruptores({ENV: valor}):
            assert sin_ellos.activa() is puesto, valor
    # Leccion del 26/10: un interruptor sin frase para el dueño pone la
    # verja en rojo el dia que se enciende.
    from src.telemetry.el_tablon import QUE_HACE
    assert str(QUE_HACE.get(ENV) or "").strip(), "sin frase en QUE_HACE"


def test_apagado_el_once_es_el_de_hoy():
    # Apagado, con la orden del 26/10 viva: ni pedido ni sin pedir.
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(libros=LIBROS_26)
        pedido = _once(pedido=True, libros=LIBROS_26)

    # Primero lo que dice QUE se movio; la huella, la ultima.
    assert hoy["formation_name"] == "4-3-3", hoy["formation_name"]
    assert 1599 in _ids(hoy) and 30493 not in _ids(hoy), sorted(_ids(hoy))
    cardona = _banco(hoy)[30493]
    assert cardona["reason"] == "PUNTUA_MENOS", cardona["reason"]
    assert cardona["reason_text"] == "puntúa menos que Jonny", cardona["reason_text"]
    for salida in (hoy, pedido):
        assert "el_once_sin_los_que_se_van" not in salida
    assert _huella(pedido) == _huella(hoy)
    assert _huella(hoy) == HUELLA_DE_MAIN, _huella(hoy)

    # Puesto, los que valoran (sin el argumento) ven el de hoy, y sin
    # que corra ni una linea del modulo. El espia se comprueba con la
    # llamada del que escribe, que si los pide.
    llamadas = []
    preparar, elegir = sin_ellos.preparar, sin_ellos.elegir

    def _espia_preparar(*args, **kwargs):
        llamadas.append("preparar")
        return preparar(*args, **kwargs)

    def _espia_elegir(*args, **kwargs):
        llamadas.append("elegir")
        return elegir(*args, **kwargs)

    sin_ellos.preparar, sin_ellos.elegir = _espia_preparar, _espia_elegir
    try:
        with _Interruptores(_con(ENV=1, ORDEN=1)):
            valora = _once(libros=LIBROS_26)
            del_que_valora = list(llamadas)
            escribe = _once(pedido=True, libros=LIBROS_26)
    finally:
        sin_ellos.preparar, sin_ellos.elegir = preparar, elegir
    assert del_que_valora == [], del_que_valora
    assert llamadas == ["preparar", "elegir"], llamadas
    assert "el_once_sin_los_que_se_van" not in valora
    assert 30493 in _ids(escribe) and 1599 not in _ids(escribe), sorted(_ids(escribe))
    assert _huella(valora) == HUELLA_DE_MAIN


def test_el_monitor_lo_pide_solo_con_el_interruptor():
    """`build_lineup_monitor_state` -el once que lleva SAVE_LINEUP- lo
    pide, y solo con el interruptor puesto."""
    pedidos = []

    def _espia(snapshot, *args, **kwargs):
        pedidos.append(kwargs.get("sin_los_que_se_van"))
        return lineup_engine.build_lineup(snapshot, *args, **kwargs)

    original = lineup_monitor.build_lineup
    lineup_monitor.build_lineup = _espia
    try:
        with _Produccion(libros=LIBROS_26):
            with _Interruptores(_con(ORDEN=1)):
                apagado = lineup_monitor.build_lineup_monitor_state(_foto(), persist=False)
                directo = build_lineup(_foto())
            with _Interruptores(_con(ENV=1, ORDEN=1)):
                puesto = lineup_monitor.build_lineup_monitor_state(_foto(), persist=False)
    finally:
        lineup_monitor.build_lineup = original

    assert pedidos == [False, True], pedidos
    assert _huella(apagado["lineup"]) == _huella(directo) == HUELLA_DE_MAIN
    assert 1599 in _ids(apagado["lineup"])
    assert 30493 in _ids(puesto["lineup"]) and 1599 not in _ids(puesto["lineup"])
    assert puesto["complete"] is True


# ============================================================
# 3. EL 26/10: LA ORDEN VENDE A JONNY Y JUEGA CARDONA
# ============================================================

def _sin_castigo(once, fichas) -> None:
    """Ningun numero castigado sale del motor: cada ficha del once y
    del banquillo trae su `lineup_score` de `prepare_players`, y los
    totales son la suma de las fichas."""
    for p in once["selected"]:
        assert p["lineup_score"] == fichas[p["id"]]["lineup_score"], p["name"]
        assert {k: v for k, v in p.items() if k != "lineup_position"} == fichas[p["id"]], p["name"]
    for f in once["bench"]:
        assert f["lineup_score"] == fichas[f["id"]]["lineup_score"], f["name"]
    total = sum(p["lineup_score"] for p in once["selected"])
    assert math.isclose(once["lineup_score_with_mandatory"], total, rel_tol=0, abs_tol=1e-6)
    deportivo = sum(
        p["lineup_score_sporting"] if p.get("lineup_score_sporting") is not None
        else p["lineup_score"] for p in once["selected"])
    assert once["lineup_score"] == round(deportivo, 2)
    for candidata in once["formation_candidates"]:
        for p in candidata["selected"]:
            assert p["lineup_score"] == fichas[p["id"]]["lineup_score"], (
                candidata["formation_name"], p["name"])
        assert candidata["score"] > -sin_ellos.SE_VA / 2, candidata["formation_name"]


def test_el_26_10_jonny_se_vende_y_juega_cardona():
    produccion = dict(libros=LIBROS_26, jp=JP_VACIA)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        once = _once(pedido=True, **produccion)
        with _Produccion(**produccion):
            monitor = lineup_monitor.build_lineup_monitor_state(_foto(), persist=False)
        fichas = {p["id"]: p for p in prepare_players(_foto(), JP_VACIA, TABLERO)}

    for salida in (once, monitor["lineup"]):
        assert 30493 in _ids(salida) and 1599 not in _ids(salida), sorted(_ids(salida))
        assert salida["formation_name"] == "4-3-3", salida["formation_name"]
        assert len(salida["selected"]) == 11
        assert_lineup_position_integrity(salida["selected"])

        jonny = _banco(salida)[1599]
        assert jonny["reason"] == "SE_VA", jonny["reason"]
        assert "LA_ORDEN_DEL_GESTOR" in jonny["reason_text"], jonny["reason_text"]

        informe = salida["el_once_sin_los_que_se_van"]
        assert informe["se_van"] == [
            {"id": 1599, "name": "Jonny", "por": ["LA_ORDEN_DEL_GESTOR"], "en_el_once": False}
        ], informe["se_van"]
        assert informe["desempates"] == []
        assert informe["jp"]["vale"] is False

        _sin_castigo(salida, fichas)

    assert monitor["complete"] is True


# ============================================================
# 4. EL 26/10 SIN LA ORDEN: JORNADA PERFECTA DESEMPATA
# ============================================================

def test_el_26_10_jp_desempata_sin_la_orden():
    with _Interruptores(_con(ENV=1)):
        once = _once(pedido=True)
        fichas = {p["id"]: p for p in prepare_players(_foto(), JP_26, TABLERO)}
    with _Interruptores(APAGADO):
        hoy = _once(pedido=True)

    assert 30493 in _ids(once) and 1599 not in _ids(once), sorted(_ids(once))
    assert once["formation_name"] == "4-3-3"
    assert_lineup_position_integrity(once["selected"])
    informe = once["el_once_sin_los_que_se_van"]
    assert informe["desempates"] == [{
        "entra": 30493, "entra_nombre": "Sergi Cardona",
        "sale": 1599, "sale_nombre": "Jonny",
        "ff": [50.0, 50.0], "jp": ["TITULAR", "SUPLENTE"],
    }], informe["desempates"]
    assert informe["se_van"] == []
    assert informe["jp"]["vale"] is True and informe["jp"]["ronda"] == 11
    jonny = _banco(once)[1599]
    assert jonny["reason"] == "DESEMPATE_JP", jonny["reason"]
    assert "Sergi Cardona (TITULAR)" in jonny["reason_text"], jonny["reason_text"]
    _sin_castigo(once, fichas)

    # El mismo banco, apagado: Jonny.
    assert 1599 in _ids(hoy) and 30493 not in _ids(hoy)


def test_jp_no_desempata_si_no_toca():
    casos = {
        "FF 65 contra 50 (15 de margen)": dict(tablero=_tablero({1599: (65.0, 40)})),
        "JP de hace 13 h": dict(jp=_jp(VEREDICTOS_26, edad=13.0)),
        "JP sin edad": dict(jp=_jp(VEREDICTOS_26, edad=None)),
        "JP de la J10 con la J11 por jugar": dict(jp=_jp(VEREDICTOS_26, ronda=10)),
        "JP no disponible": dict(jp=_jp(VEREDICTOS_26, disponible=False)),
        "Cardona en DUDA (no dice que juega)": dict(
            jp=_jp({30493: ("DUDA", 60), 1599: ("SUPLENTE", 40)})),
        "los dos PROBABLE (no hay mejor veredicto)": dict(
            jp=_jp({30493: ("PROBABLE", 84), 1599: ("PROBABLE", 84)})),
        # Revision del 27/10: dentro, un PROBABLE dice que juega. Entre
        # 84 y 96 hay muy poco para ganarle a la calidad.
        "Jonny PROBABLE (JP dice que juega)": dict(
            jp=_jp({30493: ("TITULAR", 96), 1599: ("PROBABLE", 84)})),
        "Jonny sin casar (sin veredicto)": dict(jp=_jp({30493: ("TITULAR", 96), 1599: None})),
        "Cardona sin pronostico de FF": dict(tablero=_tablero({30493: None})),
    }
    with _Interruptores(_con(ENV=1)):
        for caso, produccion in casos.items():
            once = _once(pedido=True, **produccion)
            assert 1599 in _ids(once) and 30493 not in _ids(once), caso
            informe = once.get("el_once_sin_los_que_se_van") or {}
            assert not informe.get("desempates"), (caso, informe.get("desempates"))


def test_jp_nunca_sienta_a_un_dios_ni_mete_a_uno_que_se_va():
    # Un cuarto delantero al 50 % que JP da de titular, y Yamal al 50 %
    # que JP da de suplente: Yamal no se sienta.
    plantilla = PLANTILLA + [DELANTERO_DE_RELLENO]
    veredictos = {77002: ("TITULAR", 96), 26271: ("SUPLENTE", 72),
                  35678: ("TITULAR", 96), 12494: ("TITULAR", 96)}
    with _Interruptores(_con(ENV=1)):
        dios = _once(foto=_foto(plantilla), pedido=True,
                     tablero=_tablero({26271: (50.0, 60)}), jp=_jp(veredictos))
        # El control: el mismo caso con Boyé (Clave) en el sitio de Yamal.
        control = _once(foto=_foto(plantilla), pedido=True,
                        tablero=_tablero({12494: (50.0, 50)}),
                        jp=_jp({77002: ("TITULAR", 96), 12494: ("SUPLENTE", 72)}))
    assert 26271 in _ids(dios) and 77002 not in _ids(dios), sorted(_ids(dios))
    assert dios["el_once_sin_los_que_se_van"]["desempates"] == []
    assert 77002 in _ids(control) and 12494 not in _ids(control), sorted(_ids(control))
    assert [(d["entra"], d["sale"]) for d in
            control["el_once_sin_los_que_se_van"]["desempates"]] == [(77002, 12494)]

    # Jonny se va (la orden) y JP lo da de titular: no entra por JP.
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        se_va = _once(pedido=True, libros=LIBROS_26,
                      jp=_jp({1599: ("TITULAR", 96), 30493: ("SUPLENTE", 40)}))
    assert 30493 in _ids(se_va) and 1599 not in _ids(se_va), sorted(_ids(se_va))
    assert se_va["el_once_sin_los_que_se_van"]["desempates"] == []
    assert _banco(se_va)[1599]["reason"] == "SE_VA"


# ============================================================
# 5. SIN ALTERNATIVA JUEGA; SI HACE FALTA, CAMBIA EL DIBUJO
# ============================================================

def test_sin_alternativa_juega_el_que_se_va():
    foto = _foto(SIN_CARDONA)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        once = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA)
        fichas = {p["id"]: p for p in prepare_players(foto, JP_VACIA, TABLERO)}
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA)
    assert 1599 in _ids(once) and len(once["selected"]) == 11
    assert once["complete"] is True
    assert _ids(once) == _ids(hoy)
    assert once["formation_name"] == hoy["formation_name"] == "4-3-3"
    informe = once["el_once_sin_los_que_se_van"]
    assert informe["se_van"][0]["id"] == 1599
    assert informe["se_van"][0]["en_el_once"] is True
    assert once["bench"] == []
    _sin_castigo(once, fichas)


def test_cambia_el_dibujo_si_hace_falta():
    # Un cuarto medio al 45 %: a 10 puntos o menos de Jonny (50 %), de
    # fiar. Sin Jonny, el 3-4-3.
    foto = _foto(SIN_CARDONA + [MEDIO_DE_FIAR])
    tablero = _tablero({77003: (45.0, 30)})
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA, tablero=tablero)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        once = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA, tablero=tablero)
    assert hoy["formation_name"] == "4-3-3" and 1599 in _ids(hoy), hoy["formation_name"]
    assert once["formation_name"] == "3-4-3", once["formation_name"]
    assert 1599 not in _ids(once) and 77003 in _ids(once), sorted(_ids(once))
    assert_lineup_position_integrity(once["selected"])
    assert once["playable_count"] == 11
    assert _banco(once)[1599]["reason"] == "SE_VA"
    informe = once["el_once_sin_los_que_se_van"]
    assert informe["no_entran"] == [] and informe["al_de_siempre"] is False, informe

    # El de relleno (20 %, a 30 puntos de Jonny) no es de fiar: antes
    # juega Jonny, que si al final se queda puntua.
    foto = _foto(SIN_CARDONA + [MEDIO_DE_RELLENO])
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        flojo = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA)
    assert flojo["formation_name"] == hoy["formation_name"] == "4-3-3", flojo["formation_name"]
    assert _ids(flojo) == _ids(hoy) and 1599 in _ids(flojo), sorted(_ids(flojo))
    informe = flojo["el_once_sin_los_que_se_van"]
    assert informe["no_entran"] == [{"id": 77001, "name": "Medio de relleno"}], informe["no_entran"]
    assert informe["se_van"] == [
        {"id": 1599, "name": "Jonny", "por": ["LA_ORDEN_DEL_GESTOR"], "en_el_once": True}
    ], informe["se_van"]


def test_nunca_baja_los_alineables_sin_aviso():
    """Revision del 27/10: el `SE_VA` hacia ganar a un dibujo de
    emergencia (con uno en duda, 10 alineables) sobre el completo con
    el que se va; SAVE_LINEUP lo rechazaba en cada vuelta y se quedaba
    el once vivo, con Boyé lesionado dentro."""
    boye_lesionado = {**BOYE, "status": "injured"}
    plantilla = ([j for j in SIN_CARDONA if j is not BOYE]
                 + [boye_lesionado, DELANTERO_DE_RELLENO, MEDIO_EN_DUDA])
    tablero = _tablero({77005: (60.0, 20)})
    foto = _foto(plantilla)
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA, tablero=tablero)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        once = _once(foto=foto, pedido=True, libros=LIBROS_26, jp=JP_VACIA, tablero=tablero)

    assert hoy["formation_name"] == "4-3-3" and hoy["playable_count"] == 11, (
        hoy["formation_name"], hoy["playable_count"])
    assert 1599 in _ids(hoy) and 12494 not in _ids(hoy), sorted(_ids(hoy))
    assert once["playable_count"] == 11, (once["formation_name"], sorted(_ids(once)))
    assert once["used_warning_players"] is False
    assert once["formation_name"] == "4-3-3", once["formation_name"]
    assert _ids(once) == _ids(hoy), sorted(_ids(once))
    informe = once["el_once_sin_los_que_se_van"]
    assert informe["no_entran"] == [{"id": 77005, "name": "Medio en duda"}], informe["no_entran"]
    assert informe["se_van"][0]["en_el_once"] is True


def test_el_que_entra_tiene_que_ser_de_fiar():
    """Revision del 27/10: la mejora cambia a Gayà (80 %) por De Haas, ya
    dentro. Sin Cardona, De Haas es el unico que puede entrar por el:
    solo entra si tiene pronostico y llega al liston (50 %: el hueco de
    la mejora; Gayà menos 10 es mas)."""
    libros = {"orden": None, "mejora": {"77004": {"sale": 1844, "suelo": 1_700_000}},
              "parejas": SIN_PAREJAS}
    foto = _foto(SIN_CARDONA + [DE_HAAS])
    casos = {
        "De Haas al 0 %": {77004: (0.0, 30)},
        "De Haas sin pronostico": {},
        "De Haas al 45 % (a 35 de Gayà)": {77004: (45.0, 30)},
    }
    with _Interruptores(_con(ENV=1, MEJORA=1)):
        for caso, ff in casos.items():
            once = _once(foto=foto, pedido=True, libros=libros, jp=JP_VACIA,
                         tablero=_tablero(ff))
            assert 1844 in _ids(once) and 77004 not in _ids(once), (caso, sorted(_ids(once)))
            informe = once["el_once_sin_los_que_se_van"]
            assert informe["no_entran"] == [{"id": 77004, "name": "De Haas"}], caso
            assert informe["se_van"] == [
                {"id": 1844, "name": "Gayà", "por": ["LA_MEJORA"], "en_el_once": True}
            ], caso
        de_fiar = _once(foto=foto, pedido=True, libros=libros, jp=JP_VACIA,
                        tablero=_tablero({77004: (72.0, 30)}))
        # EL PARTE DEL RELEVO de la mejora: De Haas en duda, no se cobra.
        en_duda = _once(foto=_foto(SIN_CARDONA + [DE_HAAS], estados={77004: "doubt"}),
                        pedido=True, libros=libros, jp=JP_VACIA,
                        tablero=_tablero({77004: (72.0, 30)}))
    with _Interruptores(_con(MEJORA=1)):
        hoy = _once(foto=foto, pedido=True, libros=libros, jp=JP_VACIA,
                    tablero=_tablero({77004: (72.0, 30)}))
    assert 77004 in _ids(de_fiar) and 1844 not in _ids(de_fiar), sorted(_ids(de_fiar))
    assert _banco(de_fiar)[1844]["reason"] == "SE_VA"
    assert 1844 in _ids(en_duda) and "el_once_sin_los_que_se_van" not in en_duda
    assert _ids(en_duda) == _ids(hoy)


# ============================================================
# 6. QUIEN SE VA Y QUIEN NO (pura)
# ============================================================

IDS = {j["id"] for j in PLANTILLA}

# El catalogo del 26/10: todos los nuestros sanos.
SANOS_26 = {j["id"]: "ok" for j in PLANTILLA}


def _quien(**kwargs) -> dict:
    datos = {"saldo": 250_000, "ahora": AHORA, "segundos_al_cierre": 4 * DIA,
             "estados": SANOS_26, **kwargs}
    return sin_ellos.los_que_se_van(IDS, **datos)


def _oferta(importe) -> dict:
    return {1599: {"offer_id": 1, "amount": importe}}


def test_quien_se_va_y_quien_no():
    orden_dentro = {1599: ["LA_ORDEN_DEL_GESTOR"]}
    con_relevo_fuera = _orden(si_esta=99001)

    with _Interruptores(_con(ORDEN=1)):
        # El relevo, dentro. Fuera, pujado o no, nadie: la puja ya no
        # cuenta (revision del 27/10: solo metia vaivenes).
        assert _quien(orden=ORDEN_26) == orden_dentro
        assert _quien(orden=con_relevo_fuera) == {}, "relevo general fuera"
        su_relevo_fuera = _orden([{**JONNY_SE_VENDE, "si_esta": 99001}])
        assert _quien(orden=su_relevo_fuera) == {}, "su relevo fuera"

        # EL PARTE DEL RELEVO, el de `decidir`: 'ok' o 'warned'.
        assert _quien(orden=ORDEN_26, estados={**SANOS_26, 28115: "doubt"}) == {}, "en duda"
        assert _quien(orden=ORDEN_26, estados={**SANOS_26, 28115: "warned"}) == orden_dentro
        assert _quien(orden=ORDEN_26, estados={}) == {}, "sin catalogo"
        assert _quien(orden=ORDEN_26, estados=None) == orden_dentro, "sin mirar el parte"
        # En rojo y a menos de 24 h manda la caja (con oferta: a 10 h no
        # hay reset antes del cierre)...
        rojo_cerca = dict(saldo=-5, segundos_al_cierre=10 * HORA, ofertas=_oferta(1_450_000))
        assert _quien(orden=ORDEN_26, estados={**SANOS_26, 28115: "doubt"},
                      **rojo_cerca) == orden_dentro, "en rojo y cerca"
        # ...salvo si el relevo no juega seguro y el que sale si.
        assert _quien(orden=ORDEN_26, estados={**SANOS_26, 28115: "injured"},
                      **rojo_cerca) == {}, "relevo lesionado"
        assert _quien(orden=ORDEN_26, estados={**SANOS_26, 28115: "injured", 1599: "injured"},
                      **rojo_cerca) == orden_dentro, "los dos lesionados"

        # ¿SE COBRA ANTES DEL CIERRE? AHORA es el 26/10 a las 12:00 de
        # Madrid; el proximo reset, el 27/10 a las 07:00 (19 h).
        assert _quien(orden=ORDEN_26, segundos_al_cierre=20 * HORA) == orden_dentro, "20 h"
        assert _quien(orden=ORDEN_26, segundos_al_cierre=18 * HORA) == {}, "18 h"
        assert _quien(orden=ORDEN_26, segundos_al_cierre=None) == {}, "sin reloj"
        assert _quien(orden=ORDEN_26, segundos_al_cierre=-HORA) == {}, "cierre pasado"
        for segundos in (18 * HORA, None):
            assert _quien(orden=ORDEN_26, segundos_al_cierre=segundos,
                          ofertas=_oferta(1_450_000)) == orden_dentro, ("oferta al suelo", segundos)
            assert _quien(orden=ORDEN_26, segundos_al_cierre=segundos,
                          ofertas=_oferta(1_449_999)) == {}, ("oferta bajo el suelo", segundos)

        # `desde` y `si_saldo_negativo` (el ultimo recurso no mira el parte).
        manana = _orden([{**JONNY_SE_VENDE, "desde": "2026-10-27T07:00:00+01:00"}])
        ayer = _orden([{**JONNY_SE_VENDE, "desde": "2026-10-25T07:00:00+01:00"}])
        assert _quien(orden=manana) == {}, "desde manana"
        assert _quien(orden=ayer) == orden_dentro, "desde ayer"
        rojo = _orden([{**JONNY_SE_VENDE, "si_saldo_negativo": True}])
        assert _quien(orden=rojo, saldo=100) == {}, "saldo positivo"
        assert _quien(orden=rojo, saldo=None) == {}, "saldo sin saber"
        assert _quien(orden=rojo, saldo=-5) == orden_dentro, "saldo en rojo"
        assert _quien(orden=rojo, saldo=-5, estados={**SANOS_26, 28115: "doubt"}) == orden_dentro

        # Caducada, nombra a un intocable, sin hora.
        assert _quien(orden=_orden(caduca="2026-10-20T00:00:00+02:00")) == {}, "caducada"
        con_yamal = _orden([JONNY_SE_VENDE, {"player_id": 26271, "nombre": "Yamal"}])
        assert _quien(orden=con_yamal) == {}, "intocable"
        assert _quien(orden=ORDEN_26, ahora=None) == {}, "sin hora"

        # Sin `si_esta` general, todos con el suyo; si falta uno, nadie.
        cada_uno = [{**JONNY_SE_VENDE, "si_esta": 28115},
                    {"player_id": 1844, "nombre": "Gayà", "si_esta": 28115}]
        assert _quien(orden=_orden(cada_uno, si_esta=None)) == {
            1599: ["LA_ORDEN_DEL_GESTOR"], 1844: ["LA_ORDEN_DEL_GESTOR"]}
        uno_sin = [{**JONNY_SE_VENDE, "si_esta": 28115}, {"player_id": 1844, "nombre": "Gayà"}]
        assert _quien(orden=_orden(uno_sin, si_esta=None)) == {}, "uno sin relevo"

        # Los viajes, con el suelo de `decidir`: lo pujado + 1 %; pasado
        # `hasta`, - 5 %.
        viaje = {"tope_por_viaje": 2_000_000, "candidatos": [{"player_id": 1969, "puja": 1_500_000}]}
        de_viaje = {1969: ["LA_ORDEN_DEL_GESTOR: viaje"]}
        assert _quien(orden=_orden((), viajes=viaje)) == de_viaje
        caro = {**viaje, "candidatos": [{"player_id": 1969, "puja": 2_500_000}]}
        assert _quien(orden=_orden((), viajes=caro)) == {}, "viaje por encima del tope"
        cerca = dict(segundos_al_cierre=18 * HORA)
        assert _quien(orden=_orden((), viajes=viaje), ofertas={1969: {"amount": 1_515_000}},
                      **cerca) == de_viaje, "viaje con su margen"
        assert _quien(orden=_orden((), viajes=viaje), ofertas={1969: {"amount": 1_500_000}},
                      **cerca) == {}, "viaje sin margen"
        vencido = {**viaje, "hasta": "2026-10-26T00:00:00+01:00"}
        assert _quien(orden=_orden((), viajes=vencido), ofertas={1969: {"amount": 1_425_000}},
                      **cerca) == de_viaje, "viaje vencido"

        # Uno que no es nuestro no cuenta.
        assert _quien(orden=_orden([{"player_id": 99009, "nombre": "Otro"}])) == {}

    # La orden apagada: nadie.
    with _Interruptores(APAGADO):
        assert _quien(orden=ORDEN_26) == {}, "orden apagada"

    # LA MEJORA: el `sale` de cada cambio con el `entra` dentro y sano;
    # nunca el `entra`.
    with _Interruptores(_con(MEJORA=1)):
        assert _quien(libro_mejora={"30493": {"sale": 1599}}) == {1599: ["LA_MEJORA"]}
        assert _quien(libro_mejora={"99002": {"sale": 1599}}) == {}, "mejora con el entra fuera"
        assert _quien(libro_mejora={"30493": {"sale": 1599}},
                      estados={**SANOS_26, 30493: "doubt"}) == {}, "mejora con el entra en duda"
        assert 30493 not in _quien(libro_mejora={"30493": {"sale": 1599}})
        # Su suelo; en rojo a menos de 20 h, cualquiera (`decidir`).
        con_suelo = {"30493": {"sale": 1599, "suelo": 1_500_000}}
        assert _quien(libro_mejora=con_suelo, segundos_al_cierre=18 * HORA,
                      ofertas=_oferta(1_400_000)) == {}, "mejora bajo su suelo"
        assert _quien(libro_mejora=con_suelo, segundos_al_cierre=18 * HORA, saldo=-5,
                      ofertas=_oferta(1_400_000)) == {1599: ["LA_MEJORA"]}, "mejora en rojo"
    with _Interruptores(APAGADO):
        assert _quien(libro_mejora={"30493": {"sale": 1599}}) == {}, "mejora apagada"

    # LA ROTACION: de su libro, con `las_parejas_abiertas`. Solo GANADA.
    from src.actions.la_rotacion import las_parejas_abiertas
    with _Interruptores(_con(ROTACION=1)):
        ganada = las_parejas_abiertas(libro={"parejas": [
            {"sale": 1599, "entra": 30493, "estado": "GANADA"}]})
        pujada = las_parejas_abiertas(libro={"parejas": [
            {"sale": 1599, "entra": 99003, "estado": "PUJADA"}]})
        de_otro = las_parejas_abiertas(libro={"parejas": [
            {"sale": 99004, "entra": 30493, "estado": "GANADA"}]})
    assert _quien(parejas=ganada) == {1599: ["LA_ROTACION"]}
    assert _quien(parejas=pujada) == {}, "rotacion pujada"
    assert _quien(parejas=de_otro) == {}, "el que sale no es nuestro"
    # Su suelo, el 99 % de su valor (Jonny, 1.450.000).
    precios = {1599: 1_450_000}
    assert _quien(parejas=ganada, precios=precios, segundos_al_cierre=18 * HORA,
                  ofertas=_oferta(1_440_000)) == {1599: ["LA_ROTACION"]}, "rotacion con oferta"
    assert _quien(parejas=ganada, precios=precios, segundos_al_cierre=18 * HORA,
                  ofertas=_oferta(1_400_000)) == {}, "rotacion bajo su suelo"

    # Los motivos se juntan.
    with _Interruptores(_con(ORDEN=1, MEJORA=1)):
        assert _quien(orden=ORDEN_26, libro_mejora={"30493": {"sale": 1599}}, parejas=ganada) == {
            1599: ["LA_ORDEN_DEL_GESTOR", "LA_MEJORA", "LA_ROTACION"]}

    # Basura: vacio y nunca lanza.
    with _Interruptores(_con(ORDEN=1, MEJORA=1)):
        for basura in (None, [], "x", 7, {"vender_si_ficha": "x"}, {"caduca": "x"}):
            assert sin_ellos.los_que_se_van(
                basura, orden=basura, libro_mejora=basura, parejas=basura, saldo=basura,
                ahora=basura, segundos_al_cierre=basura, estados=basura, ofertas=basura,
                precios=basura) == {}, repr(basura)
            assert _quien(orden=basura, libro_mejora=basura, parejas=basura) == {}, repr(basura)
            if not isinstance(basura, int):
                assert sin_ellos.se_cobra_antes_del_cierre(
                    basura, basura, basura, basura) is False, repr(basura)


# ============================================================
# 7. QUIEN NO SE SIENTA AUNQUE SE VENDA
# ============================================================

def test_no_se_sientan_aunque_se_vendan():
    # NO SE COBRA ANTES DEL CIERRE: a 18 h, el proximo reset (27/10 a las
    # 07:00) cae despues. Jonny sigue siendo nuestro al cierre: juega, y
    # el once es el de hoy byte a byte.
    tarde = {**RELOJ, "seconds_to_deadline": 18 * HORA}
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(pedido=True, libros=LIBROS_26, jp=JP_VACIA, reloj=tarde)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        sin_oferta = _once(pedido=True, libros=LIBROS_26, jp=JP_VACIA, reloj=tarde)
        con_oferta = _once(foto=_foto(ofertas={1599: 1_450_000}), pedido=True,
                           libros=LIBROS_26, jp=JP_VACIA, reloj=tarde)
        a_tiempo = _once(pedido=True, libros=LIBROS_26, jp=JP_VACIA,
                         reloj={**RELOJ, "seconds_to_deadline": 20 * HORA})
        # EL PARTE DEL RELEVO: Kike en duda en el catalogo; la orden no
        # cobraria a Jonny.
        parte = _once(foto=_foto(estados={28115: "doubt"}), pedido=True, libros=LIBROS_26,
                      jp=JP_VACIA)
    assert _huella(sin_oferta) == _huella(hoy) and 1599 in _ids(sin_oferta)
    assert 30493 in _ids(con_oferta) and 1599 not in _ids(con_oferta), sorted(_ids(con_oferta))
    assert 30493 in _ids(a_tiempo) and 1599 not in _ids(a_tiempo), sorted(_ids(a_tiempo))
    assert 1599 in _ids(parte) and "el_once_sin_los_que_se_van" not in parte

    # Y si algo mas cambia el once, el informe lo cuenta: con JP, Jonny
    # sale por el desempate, no por venderse.
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        con_jp = _once(pedido=True, libros=LIBROS_26, jp=JP_26, reloj=tarde)
    informe = con_jp["el_once_sin_los_que_se_van"]
    assert informe["se_van"] == []
    assert informe["se_quedan"] == [{"id": 1599, "name": "Jonny", "por": ["LA_ORDEN_DEL_GESTOR"],
                                     "motivo": sin_ellos.NO_SE_COBRA_ANTES}], informe["se_quedan"]
    assert [(d["entra"], d["sale"]) for d in informe["desempates"]] == [(30493, 1599)]

    # UN DIOS: un viaje que nombra a Yamal no lo sienta (la orden no
    # mira los intocables en los viajes).
    viaje = {"tope_por_viaje": 30_000_000,
             "candidatos": [{"player_id": 26271, "puja": 25_000_000}]}
    libros = {**LIBROS_26, "orden": _orden(viajes=viaje)}
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        dios = _once(pedido=True, libros=libros, jp=JP_VACIA)
    assert 26271 in _ids(dios) and 1599 not in _ids(dios), sorted(_ids(dios))
    informe = dios["el_once_sin_los_que_se_van"]
    assert [e["id"] for e in informe["se_van"]] == [1599], informe["se_van"]
    assert informe["se_quedan"] == [{"id": 26271, "name": "Yamal",
                                     "por": ["LA_ORDEN_DEL_GESTOR: viaje"],
                                     "motivo": sin_ellos.UN_DIOS}], informe["se_quedan"]
    assert [d["id"] for d in dios["mandatory_hierarchy"]["in_lineup"]] == [26271]

    # LA RONDA DE APLAZADOS: la rotacion vende a Jonny (GANADA). Si su
    # equipo la juega, o no se sabe, juega: el once de hoy byte a byte.
    from src.actions.la_rotacion import las_parejas_abiertas
    from src.analysis.el_calendario_de_puntos import clave_de_equipo
    with _Interruptores(_con(ROTACION=1)):
        ganada = las_parejas_abiertas(libro={"parejas": [
            {"sale": 1599, "entra": 30493, "estado": "GANADA"}]})
    libros = {"orden": None, "mejora": {}, "parejas": ganada}
    foto = _foto(equipos={5: "RC Celta"})
    parcial = {"sin_calendario": False, "ronda_parcial": True}
    casos = {
        "su equipo juega los aplazados": {**parcial, "equipos_parcial": [clave_de_equipo("RC Celta")]},
        "no se sabe quien los juega": {**parcial, "equipos_parcial": None},
        "no se sabe si vienen": {"sin_calendario": True},
    }
    with _Interruptores(_con(ROTACION=1)):
        hoy = _once(foto=foto, pedido=True, libros=libros, jp=JP_VACIA)
    with _Interruptores(_con(ENV=1, ROTACION=1)):
        for caso, rondas in casos.items():
            once = _once(foto=foto, pedido=True, libros=libros, jp=JP_VACIA, rondas=rondas)
            assert _huella(once) == _huella(hoy), caso
        otros = _once(foto=foto, pedido=True, libros=libros, jp=JP_VACIA,
                      rondas={**parcial, "equipos_parcial": ["athletic", "levante"]})
    assert 1599 in _ids(hoy)
    assert 30493 in _ids(otros) and 1599 not in _ids(otros), sorted(_ids(otros))

    # La regla, pura: el motivo de cada uno.
    fichas = [{"id": 1599, "name": "Jonny", "teamID": 5},
              {"id": 26271, "name": "Lamine Yamal", "teamID": 3},
              {"id": 1844, "name": "Gayà", "teamID": 18, "mandatory_hierarchy": True}]
    equipos = {5: "RC Celta", 3: "FC Barcelona", 18: "Valencia CF"}
    regla = sin_ellos.los_que_no_se_sientan
    juega = {**parcial, "equipos_parcial": [clave_de_equipo("RC Celta")]}
    assert regla(fichas, {1599: [], 26271: [], 1844: []}, juega, equipos) == {
        1599: sin_ellos.JUEGA_LOS_APLAZADOS, 26271: sin_ellos.UN_DIOS,
        1844: sin_ellos.UN_DIOS}
    assert regla(fichas, {1599: []}, SIN_APLAZADOS, equipos) == {}
    assert regla(fichas, {1599: []}, {**parcial, "equipos_parcial": ["levante"]}, equipos) == {}
    assert regla(fichas, {1599: []}, {**parcial, "equipos_parcial": ["levante"]}, {}) == {
        1599: sin_ellos.JUEGA_LOS_APLAZADOS}, "sin saber su equipo"
    for basura in (None, {}, "x", {"ronda_parcial": "x"}):
        assert regla(fichas, {1599: []}, basura, equipos) == {
            1599: sin_ellos.SIN_SABER_LAS_RONDAS}, repr(basura)


# ============================================================
# JORNADA PERFECTA: EL QUE ENTRA, SIEMPRE SIN AVISO
# ============================================================

def test_jp_solo_mete_a_uno_alineable_sin_aviso():
    """Revision del 27/10: con un portero en duda la busqueda va con
    avisos (`used_warning_players`), y JP metia a Cardona en duda por un
    Jonny sano: 9 alineables en vez de 10."""
    gulacsi = {**GULACSI, "status": "doubt"}
    jp = _jp({30493: ("TITULAR", 96), 1599: ("DUDA", 60)})
    control = [gulacsi if j is GULACSI else j for j in PLANTILLA]
    en_duda = [{**CARDONA, "status": "doubt"} if j is CARDONA else j for j in control]
    with _Interruptores(_con(ENV=1)):
        sano = _once(foto=_foto(control), pedido=True, jp=jp)
        duda = _once(foto=_foto(en_duda), pedido=True, jp=jp)
    assert sano["used_warning_players"] is True and duda["used_warning_players"] is True
    assert [(d["entra"], d["sale"]) for d in
            sano["el_once_sin_los_que_se_van"]["desempates"]] == [(30493, 1599)]
    assert 1599 in _ids(duda) and 30493 not in _ids(duda), sorted(_ids(duda))
    assert duda["el_once_sin_los_que_se_van"]["desempates"] == []
    assert duda["playable_count"] == sano["playable_count"] == 10


# ============================================================
# 8. LA MEMORIA DEL ONCE NO LOS MEZCLA
# ============================================================

def test_la_memoria_del_once_no_los_mezcla():
    """La busqueda sin los que se van es otra entrada: nunca se contesta
    con la del que valora. La de siempre si se comparte (`elegir` empieza
    por ella): es la misma pregunta, con la misma respuesta."""
    with _Interruptores(_con(ENV=1, ORDEN=1, UNA_VEZ=1)), \
            _Produccion(libros=LIBROS_26, jp=JP_VACIA):
        for orden in ((True, False), (False, True)):
            una_vez.olvidar()
            salidas = {}
            for pedido in orden:
                antes = una_vez.cuenta()
                salidas[pedido] = (build_lineup(_foto(), sin_los_que_se_van=True)
                                   if pedido else build_lineup(_foto()))
                despues = una_vez.cuenta()
                if pedido or orden[0] is False:
                    # La del que escribe siempre busca algo nuevo; la del
                    # que valora, si va primera.
                    assert despues["fallos"] > antes["fallos"], (orden, pedido, despues)
                else:
                    # La del que valora detras de la del que escribe: la
                    # de siempre ya esta, recordada.
                    assert despues["fallos"] == antes["fallos"], (orden, pedido, despues)
                    assert despues["aciertos"] > antes["aciertos"], (orden, pedido, despues)
            assert 1599 in _ids(salidas[False]) and 30493 not in _ids(salidas[False]), orden
            assert 30493 in _ids(salidas[True]) and 1599 not in _ids(salidas[True]), orden
            # La misma pregunta del que valora otra vez: recordada, y la misma.
            cuenta = una_vez.cuenta()
            otra = build_lineup(_foto())
            assert una_vez.cuenta()["fallos"] == cuenta["fallos"], orden
            assert una_vez.cuenta()["aciertos"] > cuenta["aciertos"], orden
            assert _huella(otra) == _huella(salidas[False]), orden
            assert _ids(otra) == _ids(salidas[False]), orden


# ============================================================
# 9. NUNCA LANZA: SI ALGO FALLA, EL ONCE DE HOY
# ============================================================

def test_nunca_lanza():
    casos = {
        "el calendario revienta": dict(reloj=_revienta, libros=LIBROS_26),
        "los libros revientan": dict(libros=_revienta),
        "foto sin liga ni mercado": dict(foto=_foto(liga=False), libros=LIBROS_VACIOS, jp=JP_VACIA),
        "JP sin claves": dict(jp={"lookup": {}}),
        "JP con basura": dict(jp={"available": True, "round": "x", "age_hours": "y", "lookup": {}}),
        "las rondas revientan": dict(rondas=_revienta, libros=LIBROS_26, jp=JP_VACIA),
    }
    for caso, datos in casos.items():
        foto = datos.pop("foto", None)
        with _Interruptores(_con(ORDEN=1)):
            hoy = _once(foto=foto, **datos)
        with _Interruptores(_con(ENV=1, ORDEN=1)):
            puesto = _once(foto=foto, pedido=True, **datos)
        assert "el_once_sin_los_que_se_van" not in puesto, caso
        assert _huella(puesto) == _huella(hoy), caso

    # Sin liga ni mercado, la orden sigue sabiendo que Kike ya esta (y
    # sano, en el catalogo).
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        sin_liga = _once(foto=_foto(liga=False), pedido=True, libros=LIBROS_26, jp=JP_VACIA)
    assert 30493 in _ids(sin_liga) and 1599 not in _ids(sin_liga)

    # Sin calendario no se sabe si se cobra antes del cierre: solo cuenta
    # la oferta que ya esta. Roto y sin oferta, el once de hoy; con su
    # oferta, Cardona.
    with _Interruptores(_con(ORDEN=1)):
        hoy = _once(pedido=True, libros=LIBROS_26, jp=JP_VACIA, reloj=_revienta)
    with _Interruptores(_con(ENV=1, ORDEN=1)):
        sin_reloj = _once(pedido=True, libros=LIBROS_26, jp=JP_VACIA, reloj=_revienta)
        con_oferta = _once(foto=_foto(ofertas={1599: 1_450_000}), pedido=True,
                           libros=LIBROS_26, jp=JP_VACIA, reloj=_revienta)
    assert _huella(sin_reloj) == _huella(hoy) and 1599 in _ids(sin_reloj)
    assert 30493 in _ids(con_oferta) and 1599 not in _ids(con_oferta), sorted(_ids(con_oferta))

    # Las piezas, con basura: devuelven lo que les llego.
    for basura in (None, [], [1, 2], "x", {"selected": 3}):
        assert sin_ellos.rematar(basura, basura, basura)[0] == basura, repr(basura)
        assert sin_ellos.con_motivo(basura, basura) == basura, repr(basura)
        assert sin_ellos.con_motivo(basura, {"se_van": [{"id": 1}]}) == basura, repr(basura)
        assert sin_ellos.sin_castigo(basura, basura) == basura, repr(basura)
        assert sin_ellos.elegir(basura, basura, basura, _revienta)[0] == basura, repr(basura)
    assert sin_ellos.elegir({"se_van": {1599: ["x"]}}, [], [{"selected": [{"id": 1599}]}],
                            _revienta)[1]["al_de_siempre"] is True
    assert sin_ellos.jp_vale(None, 11)[0] is False
    assert sin_ellos.para_la_busqueda([], {1599: ["x"]}) == []
    with _Interruptores(_con(ENV=1)):
        assert sin_ellos.preparar(None, None, None, reloj={}, libros={}) is None
        assert sin_ellos.preparar("x", "y", "z", reloj="r", libros="l", ahora="a") is None
    with _Interruptores(APAGADO):
        assert sin_ellos.preparar(_foto(), [], JP_26, reloj=RELOJ, libros=LIBROS_26) is None


TESTS = [
    test_nace_apagado,
    test_apagado_el_once_es_el_de_hoy,
    test_el_monitor_lo_pide_solo_con_el_interruptor,
    test_el_26_10_jonny_se_vende_y_juega_cardona,
    test_el_26_10_jp_desempata_sin_la_orden,
    test_jp_no_desempata_si_no_toca,
    test_jp_nunca_sienta_a_un_dios_ni_mete_a_uno_que_se_va,
    test_sin_alternativa_juega_el_que_se_va,
    test_cambia_el_dibujo_si_hace_falta,
    test_nunca_baja_los_alineables_sin_aviso,
    test_el_que_entra_tiene_que_ser_de_fiar,
    test_quien_se_va_y_quien_no,
    test_no_se_sientan_aunque_se_vendan,
    test_jp_solo_mete_a_uno_alineable_sin_aviso,
    test_la_memoria_del_once_no_los_mezcla,
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
