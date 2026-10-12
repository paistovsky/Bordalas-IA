"""
LA MEJORA DEL ONCE (12/10/2026). Guardias de
`src/actions/la_mejora_del_once.py`.

Las del calendario (`BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`) y las de los
tres arreglos (la titularidad de la plantilla entera, el parte del relevo
y la caja con lo de esta vuelta) llevan TODO escrito aquí: ni `data/`, ni
la foto, ni el reloj (`AHORA` se pasa siempre). Los libros que escribe
`correr` van a un directorio temporal.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import tempfile

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.la_mejora_del_once import (     # noqa: E402
    ENV, ENV_CALENDARIO, GANANCIA_MINIMA, correr, decidir, el_calendario_activo,
    el_contexto, el_plan_del_calendario, la_caja, la_caja_de_la_jornada,
    las_probabilidades, lo_de_esta_vuelta, los_estados, xp_por_jornada,
)
from src.analysis.el_calendario_de_puntos import contexto  # noqa: E402


# Nuestro once (posición 3 = medio, 4 = delantero) y la liga.
ONCE = [
    {"id": 10, "name": "Flojo", "position": 4, "starter_probability": 60, "price": 2_700_000},
    {"id": 11, "name": "Caro", "position": 3, "starter_probability": 80, "price": 4_900_000},
    {"id": 12, "name": "Yamal", "position": 4, "starter_probability": 90, "price": 25_000_000},
    {"id": 13, "name": "Protegido", "position": 3, "starter_probability": 50, "price": 1_000_000},
]
LIGA = {
    10: {"tasa": 3.75, "price": 2_700_000, "de_quien": "nuestro", "position": 4},
    11: {"tasa": 4.5, "price": 4_900_000, "de_quien": "nuestro", "position": 3},
    12: {"tasa": 11.0, "price": 25_000_000, "de_quien": "nuestro", "position": 4},
    13: {"tasa": 1.0, "price": 1_000_000, "de_quien": "nuestro", "position": 3},
    20: {"tasa": 5.7, "status": "ok", "price": 3_700_000, "de_quien": "computer", "position": 4},
    21: {"tasa": 3.8, "status": "ok", "price": 1_100_000, "de_quien": "computer", "position": 3},
    22: {"tasa": 9.0, "status": "injured", "price": 1_000_000, "de_quien": "computer", "position": 4},
    23: {"tasa": 9.0, "status": "ok", "price": 1_000_000, "de_quien": "computer", "position": 4},
}


def _c(pid, prob=70, jugados=6):
    l = LIGA[pid]
    return {"id": pid, "name": f"c{pid}", "position": l["position"], "price": l["price"],
            "points": int(l["tasa"] * jugados), "played": jugados, "starter_probability": prob}


def _foto(**k):
    f = {"plantilla": {10, 11, 12, 13}, "nuestras_pujas": {}, "ofertas_del_computer": {},
         "en_venta": set(), "saldo": 500_000, "maximo_de_puja": 14_000_000, "mercado": {}}
    f.update(k)
    return f


def _base(**k):
    base = dict(once=ONCE, liga=LIGA, escaparate=[_c(20)], foto=_foto(), libro={},
                intocables={"yamal"}, protegidos={13}, caja=500_000, horas_jornada=100)
    base.update(k)
    return base


def _d(**k):
    return decidir(**_base(**k))


def _pujas(d):
    return [(a["player_id"], a.get("sale")) for a in d["acciones"] if a["accion"] == "PUJAR"]


def test_mejora_con_deuda_y_sin_tocar_intocables():
    # 20 por Flojo: 5,7x0,7 = 3,99 contra 3,75x0,6 = 2,25 (+1,74). Caja:
    # 500.000 + 2.565.000 - 3.737.000 = -672.000: vale, con deuda (>= -1 M
    # a más de 64 h). Yamal no sale nunca aunque sea de su posición.
    d = _d()
    assert _pujas(d) == [(20, 10)], d
    assert d["plan"]["caja_despues"] == 500_000 + int(2_700_000 * 0.95) - 3_737_000
    # A menos de 64 h, sin deuda: ya no llega.
    assert _pujas(_d(horas_jornada=50)) == []
    # Lesionados fuera; y si el bueno es más barato, gana el bueno.
    d = _d(escaparate=[_c(20), _c(22), _c(23)])
    assert _pujas(d) == [(23, 10)], d


def test_cambia_caro_por_barato_para_fichar_mejor():
    # Sin caja para 20, pero 21 por Caro da 3,5 M y pierde 0,94: la
    # combinación suma +0,80 y deja la caja en positivo.
    d = _d(escaparate=[_c(20), _c(21)], caja=-1_500_000)
    assert sorted(_pujas(d)) == [(20, 10), (21, 11)], d
    # Pero no se vende caro por barato por gusto.
    assert _pujas(_d(escaparate=[_c(21)])) == []


def test_en_rojo_vende_caro_y_ficha_barato_desde_las_88_horas():
    k = dict(escaparate=[_c(21)], caja=-3_000_000)
    assert _pujas(_d(**k, horas_jornada=100)) == []        # puede entrar el premio
    d = _d(**k, horas_jornada=80)
    assert _pujas(d) == [(21, 11)] and d["plan"]["deficit"], d
    # Ni el Protegido (13) ni Yamal salen nunca para cuadrar la caja.
    assert all(a.get("sale") not in (12, 13) for a in d["acciones"])


def test_solo_en_su_hora():
    assert _pujas(_d(puede_escribir=False)) == []
    assert _pujas(_d(horas_jornada=39)) == []
    assert _pujas(_d(horas_jornada=None)) == []
    assert _pujas(_d(ya_pujados={20})) == []                # ya pujado esta vuelta
    assert _pujas(_d(pendientes={20})) == []                # lo ficha la orden
    assert _pujas(_d(foto=_foto(nuestras_pujas={20: {"offer_id": 1, "amount": 1}}))) == []
    # Se puja lo que PIDE el Computer + 1 %, no su valor.
    d = _d(foto=_foto(mercado={20: 3_500_000}))
    assert [a["importe"] for a in d["acciones"]] == [3_535_000]
    # Y si no está en el mercado de la foto, no.
    assert _pujas(_d(foto=_foto(mercado={99: 1}))) == []


def test_el_que_sale_solo_se_vende_con_el_relevo_dentro():
    libro = {"20": {"sale": 10, "suelo": 2_430_000}}
    ofertas = {10: {"offer_id": 7, "amount": 2_500_000}}
    # Relevo con puja viva: no se vende, y el que sale no se cambia por otro.
    d = _d(libro=libro, foto=_foto(nuestras_pujas={20: {"offer_id": 1, "amount": 1}},
                                   ofertas_del_computer=ofertas), escaparate=[_c(23)])
    assert [a["accion"] for a in d["acciones"]] == [] and d["soltar"] == []
    # Relevo dentro: se acepta desde el suelo; por debajo, se publica.
    f = _foto(plantilla={10, 11, 12, 13, 20}, ofertas_del_computer=ofertas)
    d = _d(libro=libro, foto=f, escaparate=[])
    assert [(a["accion"], a["player_id"]) for a in d["acciones"]] == [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)]
    f = _foto(plantilla={10, 11, 12, 13, 20},
              ofertas_del_computer={10: {"offer_id": 7, "amount": 2_000_000}})
    d = _d(libro=libro, foto=f, escaparate=[])
    assert [(a["accion"], a["player_id"]) for a in d["acciones"]] == [("PONER_A_LA_VENTA", 10)]
    # A menos de 20 h y en rojo, la que haya.
    d = _d(libro=libro, foto={**f, "saldo": -1, "en_venta": {10}}, escaparate=[], horas_jornada=10)
    assert [a["accion"] for a in d["acciones"]] == ["ACEPTAR_OFERTA_DEL_COMPUTER"]
    # Con la jornada jugándose, no se vende a nadie.
    d = _d(libro=libro, foto=_foto(plantilla={10, 11, 12, 13, 20}, ofertas_del_computer=ofertas),
           escaparate=[], en_curso=True)
    assert d["acciones"] == []
    # Puja perdida: el que iba a salir se queda.
    assert _d(libro=libro, escaparate=[])["soltar"] == ["20"]


def test_se_queda_lo_que_compro_la_ronda_si_mejora_el_once():
    f = _foto(plantilla={10, 11, 12, 13, 23})
    once = ONCE + [{"id": 23, "name": "c23", "position": 4, "starter_probability": 70}]
    d = _d(foto=f, once=once, escaparate=[], inventario={23})
    assert [(c["entra"], c["sale"]) for c in d["adoptar"]] == [(23, 10)], d
    assert _pujas(d) == []


def test_la_caja():
    f = _foto(saldo=1_000_000, nuestras_pujas={1: {"amount": 3_000_000}, 2: {"amount": 1_000_000}})
    assert la_caja(f) == -3_000_000
    # La de la ronda se revende sola: solo cuenta lo que se puede perder.
    assert la_caja(f, se_venden_solos={2}, ventas_pendientes=500_000) == -1_570_000


def test_nace_apagada_y_nunca_lanza():
    os.environ.pop("BORDALAS_LA_MEJORA_DEL_ONCE", None)
    assert correr(status={}, snapshot={}, v10={})["motivo"] == "APAGADA"
    os.environ["BORDALAS_LA_MEJORA_DEL_ONCE"] = "1"
    try:
        r = correr(status={"lineup": None}, snapshot={"market": None}, v10={},
                   libro_ruta=os.devnull + ".no")
        assert r["motivo"] in {"NADA_QUE_HACER"} or r["motivo"].startswith("ERROR"), r
    finally:
        os.environ.pop("BORDALAS_LA_MEJORA_DEL_ONCE", None)


# ============================================================
# EL CALENDARIO EN LA MEJORA (12/10/2026)
# ============================================================
#
#     Veinte equipos con id = puesto: los duros por la tabla son el 1-6
#     (y por valor de plantilla el 1-4, las "estrellas" de 30 M). El 12 y
#     el 13 están en el tramo 11-20 (el mismo previo para encoger).
#
#         equipo 12   J9 en casa del 1, J10 del 2, J11 del 3 (x0,846)
#         equipo 13   J9-J11 en casa contra el 15, 16 y 17   (x1,102)
#         equipo 14 y 18   no juegan esas rondas: NEUTRO (x1,0)

AHORA = datetime(2026, 10, 13, 8, 0, tzinfo=timezone.utc)

TABLA = [{"rank": r, "team": f"Equipo {r}", "points": 3 * (21 - r), "played": 8,
          "goals_for": 30 - r, "goals_against": 10 + r, "goals_diff": 20 - 2 * r,
          "biwenger_team_id": r} for r in range(1, 21)]


def _partido(jornada, dia, casa, fuera):
    return {"matchday": jornada, "kickoff": f"2026-10-{dia:02d}T21:00:00+02:00",
            "home": f"Equipo {casa}", "away": f"Equipo {fuera}"}


CALENDARIO = {"matchdays": [
    {"matchday": 9, "matches": [_partido(9, 16, 1, 12), _partido(9, 17, 13, 15),
                                _partido(9, 18, 20, 19)]},
    {"matchday": 10, "matches": [_partido(10, 23, 2, 12), _partido(10, 24, 13, 16),
                                 _partido(10, 25, 7, 8)]},
    {"matchday": 11, "matches": [_partido(11, 30, 3, 12), _partido(11, 31, 13, 17),
                                 _partido(11, 31, 9, 10)]},
]}


def _ficha(pid, nombre, equipo, puntos, jugados, de_quien, precio=3_000_000, pos=4):
    return {"id": pid, "name": nombre, "position": pos, "team_id": equipo, "status": "ok",
            "points": puntos, "played": jugados, "tasa": round(puntos / jugados, 2),
            "price": precio, "de_quien": de_quien}


# `todaLaLiga` del mundo: la misma tasa (5,0) y la misma titularidad (80)
# para Roberto y el Casero; solo cambia el calendario.
MUNDO = {
    40: _ficha(40, "Roberto", 12, 40, 8, "nuestro"),
    41: _ficha(41, "Casero", 13, 40, 8, "computer"),
    42: _ficha(42, "Crack", 12, 52, 8, "nuestro"),
    43: _ficha(43, "Maravilla", 14, 27, 3, "computer"),
    44: _ficha(44, "Fijo", 18, 56, 8, "nuestro"),
    45: _ficha(45, "Casero bueno", 13, 44, 8, "computer"),
    48: _ficha(48, "De la ronda", 15, 48, 8, "nuestro", precio=2_000_000),
    **{90 + r: _ficha(90 + r, f"Estrella {r}", r, 60, 8, "rival", precio=30_000_000)
       for r in range(1, 5)},
}


def _nuestro(pid, prob=80):
    f = MUNDO[pid]
    return {"id": pid, "name": f["name"], "position": f["position"],
            "starter_probability": prob, "price": f["price"]}


def _del_computer(pid, prob=80):
    f = MUNDO[pid]
    return {"id": pid, "name": f["name"], "position": f["position"], "price": f["price"],
            "points": f["points"], "played": f["played"], "starter_probability": prob}


def _en_el_mundo(once, escaparate, **k):
    base = dict(once=[_nuestro(p) for p in once], liga=MUNDO,
                escaparate=[_del_computer(p) for p in escaparate],
                foto=_foto(plantilla=set(once)), libro={}, intocables={"yamal"},
                protegidos=set(), caja=500_000, horas_jornada=100)
    base.update(k)
    return base


def _ctx(clasificacion=TABLA, calendario=CALENDARIO):
    status = {"league_center": {"laliga": {"standings": clasificacion}},
              "todaLaLiga": {"players": list(MUNDO.values())}}
    return contexto(status, calendario, AHORA, n=3)


def _cerca(a, b, tol=0.006):
    return a is not None and b is not None and math.isclose(a, b, rel_tol=0, abs_tol=tol)


# ------------------------------------------------------------
# APAGADO: BYTE A BYTE LO DE ANTES
# ------------------------------------------------------------
#
#     La salida entera de `decidir` en catorce escenarios, capturada con
#     el código de main ANTES de este cambio (21e33c70): su sha256 sobre
#     el JSON canónico. Si un solo byte cambia con el interruptor
#     apagado, esto se pone rojo.

def ESCENARIOS_APAGADO():
    libro = {"20": {"sale": 10, "suelo": 2_430_000}}
    ofertas = {10: {"offer_id": 7, "amount": 2_500_000}}
    con_relevo = _foto(plantilla={10, 11, 12, 13, 20}, ofertas_del_computer=ofertas)
    once_23 = ONCE + [{"id": 23, "name": "c23", "position": 4, "starter_probability": 70}]
    return [
        _base(),
        _base(escaparate=[_c(20), _c(22), _c(23)]),
        _base(escaparate=[_c(20), _c(21)], caja=-1_500_000),
        _base(escaparate=[_c(21)], caja=-3_000_000, horas_jornada=80),
        _base(foto=_foto(mercado={20: 3_500_000})),
        _base(libro=libro, foto=con_relevo, escaparate=[]),
        _base(libro=libro, foto={**con_relevo, "saldo": -1, "en_venta": {10}},
              escaparate=[], horas_jornada=10),
        _base(libro=libro, escaparate=[_c(23)],
              foto=_foto(nuestras_pujas={20: {"offer_id": 1, "amount": 1}},
                         ofertas_del_computer=ofertas)),
        _base(foto=_foto(plantilla={10, 11, 12, 13, 23}), once=once_23, escaparate=[],
              inventario={23}),
        _en_el_mundo([40], [41]),
        _en_el_mundo([40], [45]),
        _en_el_mundo([42], [41]),
        _en_el_mundo([44], [43]),
        _en_el_mundo([40, 44], [41, 43, 45], caja=-2_000_000, horas_jornada=70),
    ]


HUELLA_DE_ANTES = "e757dffb1205f3f47be4774143f46dc4d42893eeb3d9b7ef4ea7228d9da3dd54"

# Lo mismo, legible: lo que se manda y lo que se adopta en cada escenario.
LO_DE_ANTES = [
    [("PUJAR", 20)], [("PUJAR", 23)], [("PUJAR", 20), ("PUJAR", 21)], [("PUJAR", 21)],
    [("PUJAR", 20)], [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)],
    [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)], [], [("ADOPTAR", 23)], [], [], [],
    [("PUJAR", 43)], [],
]


def _canon(x):
    if isinstance(x, (set, frozenset)):
        return sorted(x)
    raise TypeError(type(x))


def _huella(salidas):
    texto = json.dumps(salidas, sort_keys=True, default=_canon)
    return hashlib.sha256(texto.encode()).hexdigest()


def _lo_que_hace(d):
    return ([(a["accion"], a["player_id"]) for a in d["acciones"]]
            + [("ADOPTAR", c["entra"]) for c in d["adoptar"]])


def test_apagado_es_byte_a_byte_lo_de_antes():
    salidas = [decidir(**k) for k in ESCENARIOS_APAGADO()]
    assert [_lo_que_hace(d) for d in salidas] == LO_DE_ANTES, [_lo_que_hace(d) for d in salidas]
    assert _huella(salidas) == HUELLA_DE_ANTES, _huella(salidas)
    # Y pasando lo nuevo vacío, igual: sin contexto, sin titularidades de
    # la plantilla, sin estados.
    nada = dict(calendario_de_puntos=None, probabilidades=None, estados=None)
    assert _huella([decidir(**k, **nada) for k in ESCENARIOS_APAGADO()]) == HUELLA_DE_ANTES


class _Vigilado(dict):
    """Un calendario que apunta si alguien lo mira."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.mirado = 0

    def get(self, *a, **k):
        self.mirado += 1
        return super().get(*a, **k)

    def __getitem__(self, clave):
        self.mirado += 1
        return super().__getitem__(clave)


@contextmanager
def _interruptores(valores):
    antes = {k: os.environ.get(k) for k in valores}
    try:
        for k, v in valores.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class _Escritor:
    def __init__(self):
        self.llamadas = []

    def _bien(self):
        return {"sent": True, "success": True, "http_status": 200}

    def place_bid(self, player_id, amount, execute):
        self.llamadas.append(("PUJAR", player_id, amount))
        return self._bien()

    def accept_offer(self, offer_id, execute):
        self.llamadas.append(("ACEPTAR", offer_id))
        return self._bien()

    def list_player_for_sale(self, player_id, price, execute):
        self.llamadas.append(("PUBLICAR", player_id, price))
        return self._bien()

    def cancel_bid(self, offer_id, execute):
        self.llamadas.append(("CANCELAR", offer_id))
        return self._bien()


def _correr(once, escaparate, plantilla, *, con_calendario, roster=None, v10=None,
            libro_ronda=None, calendario=None):
    """`correr` con TODO dado: foto, panel, vuelta, calendario y lo que
    si no se lee de producción. Los libros, en un directorio temporal."""
    roster = {p: 80 for p in plantilla} if roster is None else roster
    status = {
        "todaLaLiga": {"players": list(MUNDO.values())},
        "lineup": {"players": [_nuestro(p) for p in once]},
        "roster": {"players": [_nuestro(p, prob) for p, prob in roster.items()]},
        "libro_del_escaparate": {"players": [_del_computer(p) for p in escaparate]},
        "league_center": {"laliga": {"standings": TABLA}},
    }
    snapshot = {
        "league": {"user": {"id": 7}},
        "market": {"sales": [{"player": {"id": p}, "user": None, "price": MUNDO[p]["price"]}
                             for p in escaparate],
                   "offers": [],
                   "status": {"maximumBid": 14_000_000, "balance": 500_000}},
        "my_team": [{"id": p, "price": MUNDO[p]["price"]} for p in plantilla],
    }
    escritor = _Escritor()
    interruptores = {ENV: "1", ENV_CALENDARIO: "1" if con_calendario else None}
    with tempfile.TemporaryDirectory() as tmp, _interruptores(interruptores):
        rutas = {k: os.path.join(tmp, f"{k}.json") for k in ("mejora", "ronda", "chollos")}
        Path(rutas["ronda"]).write_text(json.dumps(libro_ronda or {}))
        Path(rutas["chollos"]).write_text("{}")
        s = correr(
            status=status, snapshot=snapshot, v10=v10 or {},
            escritor_factory=lambda: escritor, ahora=AHORA, libro_ruta=rutas["mejora"],
            calendario=CALENDARIO if calendario is None else calendario,
            de_fuera={"orden": {}, "vetados": set(), "protegidos": set(),
                      "libro_ronda": rutas["ronda"], "libro_chollos": rutas["chollos"],
                      "horas_jornada": 100.0, "puede_escribir": True, "en_curso": False},
        )
        libros = {k: json.loads(Path(r).read_text()) for k, r in rutas.items()}
    return s, escritor, libros


def test_apagado_correr_ni_mira_el_calendario():
    # Roberto (fuera en casa del 1, 2 y 3) y el Casero (en casa contra
    # el 15, 16 y 17): misma tasa, misma titularidad. Apagado: 0 puntos
    # de diferencia, no se toca, y el calendario ni se abre.
    cal = _Vigilado(CALENDARIO)
    with _interruptores({ENV_CALENDARIO: None}):
        assert not el_calendario_activo()
    s, escritor, _ = _correr([40], [41], [40], con_calendario=False, calendario=cal)
    assert s["motivo"] == "NADA_QUE_HACER" and escritor.llamadas == [], s
    assert cal.mirado == 0, cal.mirado
    assert "calendario" not in s["plan"], s["plan"]
    assert s["plan"] == decidir(**_en_el_mundo([40], [41]))["plan"], s["plan"]


def test_encendido_vende_al_del_mal_calendario():
    # Encendido: 4,77 de tasa encogida x 0,8 = 3,82 neutro; Roberto
    # x0,846 = 3,23 por jornada, el Casero x1,102 = 4,21: +0,98 >= 0,5.
    for valor in ("1", "true", "si", "yes", "SI"):
        with _interruptores({ENV_CALENDARIO: valor}):
            assert el_calendario_activo(), valor
    cal = _Vigilado(CALENDARIO)
    s, escritor, libros = _correr([40], [41], [40], con_calendario=True, calendario=cal)
    assert cal.mirado > 0
    assert escritor.llamadas == [("PUJAR", 41, 3_030_000)], (s, escritor.llamadas)
    assert libros["mejora"]["41"]["sale"] == 40, libros
    plan = s["plan"]
    assert plan["calendario"]["usado"] and plan["calendario"]["rondas"] == [
        "Jornada 9", "Jornada 10", "Jornada 11"], plan
    assert plan["calendario"]["duros"] == [1, 2, 3, 4, 5, 6], plan
    (c,) = plan["cambios"]
    tasa = (40 + 3 * 4.17) / 11                     # encogida hacia el 11-20 (DEL 4,17)
    assert _cerca(c["xp_sale"], tasa * 0.8 * 0.94 * 0.90), c
    assert _cerca(c["xp_entra"], tasa * 0.8 * 1.06 * 1.04), c
    assert c["factor_sale"] == 0.846 and c["factor_entra"] == 1.102, c
    assert c["sin_calendario"] == 0.0 and c["puntos"] >= GANANCIA_MINIMA, c
    # Los puntos siguen siendo POR JORNADA: la resta de los xP por jornada.
    assert abs(c["puntos"] - (c["xp_entra"] - c["xp_sale"])) <= 0.011, c


def test_el_calendario_desempata_y_no_vende_a_uno_mucho_mejor():
    ctx = _ctx()
    # El Casero bueno (5,5) por Roberto (5,0): apagado +0,40, no llega a
    # 0,5; con el calendario +1,30, sí.
    assert _lo_que_hace(decidir(**_en_el_mundo([40], [45]))) == []
    d = decidir(**_en_el_mundo([40], [45], calendario_de_puntos=ctx))
    assert _lo_que_hace(d) == [("PUJAR", 45)], d
    # El Crack (6,5) con el peor calendario contra el Casero (5,0) con el
    # mejor: 3,97 contra 4,21, +0,24 < 0,5. Un jugador mucho mejor no se
    # vende por un calendario.
    d = decidir(**_en_el_mundo([42], [41], calendario_de_puntos=ctx))
    assert _lo_que_hace(d) == [] and d["plan"]["calendario"]["usado"], d
    sale = xp_por_jornada(ctx, {**MUNDO[42]}, 80)
    entra = xp_por_jornada(ctx, {**MUNDO[41]}, 80)
    assert 0 < entra["xp"] - sale["xp"] < GANANCIA_MINIMA, (entra, sale)
    # Y al revés (el bueno es el nuestro): nunca.
    assert _lo_que_hace(decidir(**_en_el_mundo([41], [40]) | {
        "liga": {**MUNDO, 41: {**MUNDO[41], "de_quien": "nuestro"},
                 40: {**MUNDO[40], "de_quien": "computer"}},
        "calendario_de_puntos": ctx})) == []


def test_encoge_a_la_maravilla_de_tres_partidos():
    # La Maravilla: 27 puntos en 3 partidos (9,0). El Fijo: 56 en 8
    # (7,0). Ninguno juega esas rondas (neutro). Apagado: +1,60 y se
    # ficha. Encendido, la tasa se encoge hacia el 11-20 (k = 3):
    # (27 + 3 x 4,17) / 6 = 6,59 contra (56 + 12,51) / 11 = 6,23: +0,29.
    ctx = _ctx()
    assert _lo_que_hace(decidir(**_en_el_mundo([44], [43]))) == [("PUJAR", 43)]
    d = decidir(**_en_el_mundo([44], [43], calendario_de_puntos=ctx))
    assert _lo_que_hace(d) == [], d
    maravilla = xp_por_jornada(ctx, MUNDO[43], 80)
    assert _cerca(maravilla["xp"], (27 + 3 * 4.17) / 6 * 0.8), maravilla
    assert maravilla["factor"] == 1.0, maravilla            # no juega: neutro, no cero


def test_sin_clasificacion_el_esperado_de_siempre_y_lo_dice():
    ctx = _ctx(clasificacion=[])
    assert not ctx["available"]
    for once, esc in (([40], [41]), ([40], [45]), ([44], [43])):
        apagado = decidir(**_en_el_mundo(once, esc))
        d = decidir(**_en_el_mundo(once, esc, calendario_de_puntos=ctx))
        assert d["acciones"] == apagado["acciones"], (d, apagado)
        plan = dict(d["plan"])
        cal = plan.pop("calendario")
        assert plan == apagado["plan"], (plan, apagado["plan"])
        assert cal["usado"] is False and "esperado de siempre" in cal["motivo"], cal
    # Sin calendario que leer: tampoco.
    assert not el_contexto({"league_center": {"laliga": {"standings": TABLA}}}, {},
                           AHORA)["available"]


def test_el_xp_por_jornada_y_el_plan_nunca_lanzan():
    ctx = _ctx()
    for basura in (None, 3, "x", [], {}, {"available": False}):
        assert xp_por_jornada(basura, MUNDO[40], 80) is None, basura
        assert el_plan_del_calendario(basura)["usado"] is False, basura
    # Un contexto roto no lanza: sin rondas que leer, el neutro encogido.
    raro = xp_por_jornada({"available": True, "rondas": "x", "tramos": 7}, MUNDO[40], 80)
    assert raro is not None and raro["factor"] == 1.0, raro
    assert xp_por_jornada(ctx, MUNDO[40], None) is None              # sin titularidad
    assert xp_por_jornada(ctx, {"team_id": 12, "position": 4}, 80) is None  # sin partidos
    assert xp_por_jornada(ctx, None, 80) is None
    # Al final de la liga, una ronda: se divide entre una, no entre tres.
    una = {**ctx, "rondas": ctx["rondas"][:1]}
    r = xp_por_jornada(una, MUNDO[40], 80)
    assert _cerca(r["xp"], (40 + 3 * 4.17) / 11 * 0.8 * 0.846) and r["factor"] == 0.846, r
    assert isinstance(el_contexto("basura", {"matchdays": "x"}, AHORA), dict)


# ------------------------------------------------------------
# ARREGLO 1: LA TITULARIDAD DE LA PLANTILLA ENTERA
# ------------------------------------------------------------

def test_adopta_al_de_la_ronda_con_la_titularidad_de_la_plantilla():
    # El 23 de la ronda NO está en el once: hasta hoy su titularidad se
    # buscaba en el once y en `todaLaLiga` (que no la trae): nunca se
    # adoptaba.
    f = _foto(plantilla={10, 11, 12, 13, 23})
    assert _d(foto=f, escaparate=[], inventario={23})["adoptar"] == []
    d = _d(foto=f, escaparate=[], inventario={23}, probabilidades={23: 70})
    assert [(c["entra"], c["sale"]) for c in d["adoptar"]] == [(23, 10)], d
    # Manda la de la plantilla también para los del once (60 -> 30: el
    # Flojo pasa a 1,1 puntos y el 20 lo mejora aún más).
    d = _d(probabilidades={10: 30})
    assert d["plan"]["cambios"][0]["puntos"] == round(5.7 * 70 / 100 - 3.75 * 30 / 100, 2), d
    # Y en `correr`, de `roster.players`.
    assert las_probabilidades({"roster": {"players": [{"id": 1, "starter_probability": 70}]},
                               "lineup": {"players": [{"id": 1, "starter_probability": 10},
                                                      {"id": 2, "starter_probability": 50}]}}
                              ) == {1: 70, 2: 50}
    assert las_probabilidades(None) == {} and las_probabilidades({"roster": "x"}) == {}
    s, escritor, libros = _correr([40], [], [40, 48], con_calendario=False,
                                  libro_ronda={"48": 2_000_000})
    assert [(c["entra"], c["sale"]) for c in s["adoptados"]] == [(48, 40)], s
    assert escritor.llamadas == [] and libros["ronda"] == {}, (escritor.llamadas, libros)
    assert libros["mejora"]["48"] == {"sale": 40, "suelo": 2_700_000, "puntos": 0.8,
                                      "adoptado": True}, libros
    # Sin él en `roster.players`, como antes: no se adopta.
    s, _, libros = _correr([40], [], [40, 48], con_calendario=False, roster={40: 80},
                           libro_ronda={"48": 2_000_000})
    assert s["adoptados"] == [] and libros["ronda"] == {"48": 2_000_000}, s


# ------------------------------------------------------------
# ARREGLO 2: EL PARTE DEL RELEVO
# ------------------------------------------------------------

def test_no_se_cobra_al_que_sale_si_el_relevo_no_esta_sano():
    libro = {"20": {"sale": 10, "suelo": 2_430_000}}
    f = _foto(plantilla={10, 11, 12, 13, 20},
              ofertas_del_computer={10: {"offer_id": 7, "amount": 2_500_000}})

    def hace(estados, foto=None, **k):
        d = _d(libro=libro, foto={**f, **(foto or {})}, escaparate=[], estados=estados, **k)
        return [(a["accion"], a["player_id"]) for a in d["acciones"]], d["plan"].get("frenadas")

    acepta = [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)]
    assert hace({20: "ok"}) == (acepta, None)
    assert hace({20: "warned"}) == (acepta, None)              # apercibido juega
    for malo in ({20: "injured"}, {20: "doubt"}, {20: "sanctioned"}, {}):
        hechas, frenadas = hace(malo)
        # No se cobra, pero publicar sí (hace nacer la oferta).
        assert hechas == [("PONER_A_LA_VENTA", 10)], (malo, hechas)
        assert frenadas[0]["guardia"] == "EL_PARTE_DEL_RELEVO" and frenadas[0]["relevo"] == 20
    # Ya publicado: ni se cobra ni se publica otra vez.
    assert hace({20: "injured"}, foto={"en_venta": {10}})[0] == []
    # En rojo y a menos de 24 h, se cobra igual (a 22 h, con su suelo).
    assert hace({20: "injured"}, foto={"saldo": -1}, horas_jornada=22) == (acepta, None)
    # En rojo pero lejos, o cerca pero en positivo: no.
    assert hace({20: "injured"}, foto={"saldo": -1}, horas_jornada=30)[0] != acepta
    assert hace({20: "injured"}, horas_jornada=10)[0] != acepta
    # Los estados: los del catálogo de la foto mandan sobre `todaLaLiga`.
    foto_de_la_vuelta = {"catalog": {"data": {"players": {"20": {"status": "injured"}}}}}
    assert los_estados(foto_de_la_vuelta, {20: {"status": "ok"}, 21: {"status": "ok"}}) == {
        20: "injured", 21: "ok"}
    assert los_estados(None, None) == {}


# ------------------------------------------------------------
# ARREGLO 3: LA CAJA CON LO QUE ESTA VUELTA YA HIZO
# ------------------------------------------------------------

V10 = {
    "orden_del_gestor": {"hechas": [
        {"accion": "PUJAR", "player_id": 17937, "importe": 3_777_000, "exito": True,
         "sustituye": {"offer_id": 1, "amount": 3_000_000}},
        {"accion": "PUJAR", "player_id": 34111, "importe": 4_989_000, "exito": False},
        {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 11, "importe": 2_500_000,
         "exito": True},
    ]},
    "ronda": {"hechas": [
        {"accion": "PUJAR", "player_id": 1462, "importe": 1_101_000, "exito": True},
        {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 23, "importe": 1_050_000,
         "exito": True},
    ]},
    "chollos": {"hechas": [
        {"accion": "PUJAR", "player_id": 555, "importe": 1_000_000, "exito": True},
    ]},
}


def test_la_caja_cuenta_lo_que_esta_vuelta_ya_hizo():
    esta = lo_de_esta_vuelta(V10)
    assert esta["ya_pujados"] == {17937, 1462, 555}, esta
    assert esta["gastado"] == 3_777_000 + 1_101_000 + 1_000_000, esta
    assert esta["solas"] == {1462, 555} and esta["cobros"] == {11: 2_500_000, 23: 1_050_000}
    assert lo_de_esta_vuelta(None)["pujas"] == {} and lo_de_esta_vuelta("x")["cobros"] == {}

    # La foto (de antes) tenía la puja vieja de la orden por el 17937.
    f = _foto(saldo=500_000, plantilla={10, 11, 23},
              nuestras_pujas={17937: {"offer_id": 1, "amount": 3_000_000}})
    assert la_caja(f) == 500_000 - 3_000_000                     # como antes
    # La de la orden entera (la nueva en lugar de la vieja), las de la
    # ronda y los chollos al 7 %, y lo cobrado entra.
    assert la_caja(f, esta_vuelta=esta) == (500_000 - 3_777_000 - 77_070 - 70_000
                                            + 2_500_000 + 1_050_000)

    liga = {10: {"price": 2_700_000}, 11: {"price": 4_900_000}, 23: {"price": 1_000_000}}
    orden = {"vender_si_ficha": {"jugadores": [{"player_id": 11, "suelo": 4_410_000}]},
             "fichar": [{"player_id": 17937, "puja": 3_777_000},
                        {"player_id": 99, "puja": 1_000_000}]}
    libro = {"20": {"sale": 10, "suelo": 2_430_000}}
    k = dict(liga=liga, orden=orden, libro=libro, solos={23}, inventario={23})
    # Sin lo de esta vuelta, la cuenta de siempre (la que hacía `correr`).
    antes = la_caja(
        f, se_venden_solos={23}, inventario_valor=int(1_000_000 * 0.95),
        ventas_pendientes=int((int(4_410_000 / 0.9) + 2_700_000) * 0.95) - 1_000_000)
    assert la_caja_de_la_jornada(f, **k) == antes == 4_670_000, antes
    # Con ella: el 11 (vendido por la orden) y el 23 (por la ronda) ya no
    # son ventas pendientes ni inventario: son caja. El 17937 cuenta una
    # vez, por su puja nueva.
    assert la_caja_de_la_jornada(f, **k, esta_vuelta=esta) == (
        500_000 - 3_777_000 - 77_070 - 70_000 + 2_500_000 + 1_050_000
        + int(2_700_000 * 0.95) - 1_000_000)


def test_correr_con_lo_que_esta_vuelta_ya_hizo():
    # La orden ya vendió a Roberto en esta vuelta (la foto es de antes) y
    # la ronda pujó por el 1462: Roberto no sale otra vez aunque el
    # calendario lo pida; lo cobrado está en la caja y lo pujado baja la
    # puja disponible.
    v10 = {"orden_del_gestor": {"hechas": [
               {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 40,
                "importe": 2_900_000, "exito": True}]},
           "ronda": {"hechas": [
               {"accion": "PUJAR", "player_id": 1462, "importe": 1_101_000, "exito": True}]}}
    s, escritor, _ = _correr([40], [41], [40], con_calendario=True, v10=v10)
    assert escritor.llamadas == [] and s["motivo"] == "NADA_QUE_HACER", s
    assert s["plan"]["caja"] == 500_000 + 2_900_000 - 77_070, s["plan"]
    assert s["plan"]["disponible"] == 14_000_000 - 1_101_000 - 1_000_000, s["plan"]


TESTS = [test_mejora_con_deuda_y_sin_tocar_intocables,
         test_cambia_caro_por_barato_para_fichar_mejor,
         test_en_rojo_vende_caro_y_ficha_barato_desde_las_88_horas,
         test_solo_en_su_hora, test_el_que_sale_solo_se_vende_con_el_relevo_dentro,
         test_se_queda_lo_que_compro_la_ronda_si_mejora_el_once, test_la_caja,
         test_nace_apagada_y_nunca_lanza,
         # El calendario (12/10/2026, `BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`).
         test_apagado_es_byte_a_byte_lo_de_antes,
         test_apagado_correr_ni_mira_el_calendario,
         test_encendido_vende_al_del_mal_calendario,
         test_el_calendario_desempata_y_no_vende_a_uno_mucho_mejor,
         test_encoge_a_la_maravilla_de_tres_partidos,
         test_sin_clasificacion_el_esperado_de_siempre_y_lo_dice,
         test_el_xp_por_jornada_y_el_plan_nunca_lanzan,
         # Los tres arreglos (siempre).
         test_adopta_al_de_la_ronda_con_la_titularidad_de_la_plantilla,
         test_no_se_cobra_al_que_sale_si_el_relevo_no_esta_sano,
         test_la_caja_cuenta_lo_que_esta_vuelta_ya_hizo,
         test_correr_con_lo_que_esta_vuelta_ya_hizo]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
