"""
EL APLAZADO NO FRENA LA COMPRA (20/10/2026). Guardias de
`BORDALAS_EL_APLAZADO_NO_FRENA_LA_COMPRA` en la orden del gestor, la
mejora del once y el cierre de la jornada, y de `el_proximo_cierre` en
`src/analysis/la_proxima_jornada.py`.

QUE SE PRUEBA

    El 20/10 Pepe no podia pujar: todos los motores de compra paran a
    40 h de «la proxima jornada», y la proxima era el Levante-Athletic
    (J6 aplazada, una ronda aparte de un partido, mie 21/10 20:00 de
    Madrid). Del lun 19/10 04:00 al mie 21/10 20:00 no se compraba: el
    mercado del reset del 21/10 (Kubo, que resolvia ese reset) perdido.

    T1-T2   la regla en la orden (Kubo por Luismi) y en la mejora (Kubo
            por Exposito), con el limite exacto de la caja.
    T1b     la vuelta de despues del reset cobra al que sale (y con el
            relevo lesionado, encendido, tambien: manda la caja).
    T3      APAGADO, BYTE A BYTE LO DE ANTES: la salida de `decidir` y
            `correr` de los tres motores, capturada con el codigo de
            ANTES del cambio (7f35ef4f). Sin claves nuevas.
    T4-T6   donde la regla no aplica (el aplazado sin ventana propia, la
            J10 entera, despues del ultimo reset): encendido = apagado.
    T7-T8   un cambio solo paga su puja, y cada oferta cuenta una vez.
    T9      el cierre cuenta el mismo cobro que dejo pujar y no vende al
            banquillo por un deficit que ya esta cubierto.
    T10-T11 que es una ronda de aplazados, y dos seguidos.
    T12-T13 con basura no lanza ni relaja nada; nace apagado.

    Sin red, sin `data/` y sin el reloj: calendario, foto y libros se
    pasan a mano; la hora tambien. Lo que escribe `correr` va a un
    temporal. El entorno se deja limpio (sin ningun `BORDALAS_*` ni
    `GITHUB_RUN_ID`) dentro de cada prueba, y como estaba al salir: la
    verja corre esto con los interruptores de produccion puestos.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.el_cierre_de_la_jornada as cierre_mod      # noqa: E402
import src.actions.la_mejora_del_once as mejora_mod           # noqa: E402
import src.actions.la_orden_del_gestor as orden_mod           # noqa: E402
import src.analysis.la_proxima_jornada as pj                  # noqa: E402


EL_APLAZADO = "BORDALAS_EL_APLAZADO_NO_FRENA_LA_COMPRA"
ORDEN_ENV = "BORDALAS_LA_ORDEN_DEL_GESTOR"
MEJORA_ENV = "BORDALAS_LA_MEJORA_DEL_ONCE"
CIERRE_ENV = "BORDALAS_EL_CIERRE_DE_LA_JORNADA"

UTC = timezone.utc
YO = 7

AHORA = datetime(2026, 10, 20, 18, 47, tzinfo=UTC)            # mar 20:47 de Madrid
TRAS_EL_RESET = datetime(2026, 10, 21, 5, 15, tzinfo=UTC)     # mie 07:15 de Madrid
RESET_21 = datetime(2026, 10, 21, 5, 0, tzinfo=UTC)           # mie 07:00 de Madrid
INICIO_J6 = datetime(2026, 10, 21, 18, 0, tzinfo=UTC)         # Levante-Athletic, 20:00
INICIO_J10 = datetime(2026, 10, 23, 19, 0, tzinfo=UTC)        # Alaves-Malaga, 21:00

# Las ofertas del Computer nacen a las 07:03-07:09 y viven 48 h.
HASTA_LUISMI = datetime(2026, 10, 22, 5, 0, 40, tzinfo=UTC)   # nacio el 20/10
PUBLICADO_LUISMI = datetime(2026, 10, 22, 9, 10, tzinfo=UTC)
HASTA_DEL_19 = datetime(2026, 10, 21, 5, 0, 40, tzinfo=UTC)   # nacio el 19/10
PUBLICADO_EXPOSITO = datetime(2026, 10, 21, 5, 16, tzinfo=UTC)

KUBO, LUISMI, EXPOSITO = 20102, 25777, 19862
SALDO = 1_467_983
OFERTA_LUISMI = 2_958_000
OFERTA_EXPOSITO = 4_745_600


def _h(hasta, desde) -> float:
    return (hasta - desde).total_seconds() / 3600


def _epoch(cuando) -> int:
    return int(cuando.timestamp())


# ------------------------------------------------------------------
# EL CALENDARIO: el de produccion del 20/10 (la J6 solo trae el
# Levante-Athletic, con un partido y sin `aparte`) y la J10 entera.
# ------------------------------------------------------------------

def _p(j, casa, fuera, cuando):
    return {"matchday": j, "home": casa, "away": fuera, "kickoff": cuando}


J10 = [
    _p(10, "Deportivo Alavés", "Málaga CF", "2026-10-23T21:00:00+02:00"),
    _p(10, "Rayo Vallecano", "Elche CF", "2026-10-24T14:00:00+02:00"),
    _p(10, "R. Racing Club", "RCD Espanyol de Barcelona", "2026-10-24T16:15:00+02:00"),
    _p(10, "Valencia CF", "Villarreal CF", "2026-10-24T18:30:00+02:00"),
    _p(10, "Atlético de Madrid", "RC Deportivo", "2026-10-24T21:00:00+02:00"),
    _p(10, "Athletic Club", "Getafe CF", "2026-10-25T14:00:00+01:00"),
    _p(10, "Celta", "Real Betis", "2026-10-25T16:15:00+01:00"),
    _p(10, "Real Sociedad", "Levante UD", "2026-10-25T18:30:00+01:00"),
    _p(10, "FC Barcelona", "Real Madrid", "2026-10-25T21:00:00+01:00"),
    _p(10, "Sevilla FC", "CA Osasuna", "2026-10-26T21:00:00+01:00"),
]
LEV_ATH = _p(6, "Levante UD", "Athletic Club", "2026-10-21T20:00:00+02:00")
CAL = {"matchdays": [{"matchday": 6, "matches": [LEV_ATH]},
                     {"matchday": 10, "matches": J10}]}


# ------------------------------------------------------------------
# LA ORDEN: Kubo (si llega) por Luismi Cruz, con su oferta del Computer.
# ------------------------------------------------------------------

ORDEN = {
    "caduca": "2026-11-30T23:59:00+01:00",
    "fichar": [{"player_id": KUBO, "nombre": "Kubo", "puja": 3_000_000}],
    "vender_si_ficha": {"si_esta": KUBO, "jugadores": [
        {"player_id": LUISMI, "nombre": "Luismi Cruz", "suelo": 2_700_000}]},
}
OTROS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
NUESTROS = frozenset(OTROS) | {LUISMI, EXPOSITO}


def _con_puja(orden, puja):
    return {**orden, "fichar": [{**orden["fichar"][0], "puja": puja}]}


def _orden_decidir(orden=ORDEN, **k):
    base = dict(
        mercado={KUBO: 2_880_000}, nuestras_pujas={}, plantilla=set(NUESTROS),
        ofertas_del_computer={LUISMI: {"offer_id": 901, "amount": OFERTA_LUISMI}},
        en_venta={LUISMI}, precios={LUISMI: 2_900_000}, maximo_de_puja=14_000_000,
        saldo=SALDO, ahora=AHORA, horas_jornada=_h(INICIO_J6, AHORA),
        estados={KUBO: "ok", LUISMI: "ok"}, en_curso=False,
    )
    base.update(k)
    return orden_mod.decidir(orden, **base)


# La vuelta de despues del reset del 21/10: Kubo ya es nuestro y el saldo
# esta en rojo (1.467.983 - 3.000.000).
T1B = dict(plantilla=set(NUESTROS) | {KUBO}, mercado={}, saldo=-1_532_017,
           horas_jornada=_h(INICIO_J6, TRAS_EL_RESET), ahora=TRAS_EL_RESET)


def _caducidades(hasta=HASTA_LUISMI, publicado=PUBLICADO_LUISMI):
    return {LUISMI: {"offer_id": 901, "oferta": hasta, "publicacion": publicado}}


def _aparte(ahora=AHORA, **k):
    """El `aparte` de las 20:47 del 20/10, como lo monta `el_aplazado`."""
    a = {"inicio": INICIO_J6, "horas": _h(INICIO_J6, ahora),
         "horas_principal": _h(INICIO_J10, ahora), "inicio_principal": INICIO_J10,
         "proximo_reset": RESET_21, "resuelve_antes": True,
         "caducidades": _caducidades()}
    a.update(k)
    return a


def _la_foto(saldo=SALDO, hasta=HASTA_LUISMI, publicado=PUBLICADO_LUISMI,
             plantilla=NUESTROS, pujas=None, catalogo=None, ofertas=None):
    """La foto de la vuelta (`cycle["snapshot"]`): Kubo en el mercado del
    Computer, Luismi publicado por nosotros con su oferta, el saldo."""
    pujas = pujas or {}
    ofertas = {LUISMI: (901, OFERTA_LUISMI, hasta)} if ofertas is None else ofertas
    estados = {p: "ok" for p in sorted(set(plantilla) | {KUBO})}
    estados.update(catalogo or {})
    return {
        "league": {"user": {"id": YO}},
        "market": {
            "sales": [{"player": {"id": KUBO}, "user": None, "price": 2_880_000},
                      {"player": {"id": LUISMI}, "user": {"id": YO}, "price": 2_900_000,
                       "until": _epoch(publicado)}],
            "offers": [{"id": oid, "status": "waiting", "amount": importe,
                        "requestedPlayers": [{"id": pid}], "from": None,
                        "until": None if fin is None else _epoch(fin)}
                       for pid, (oid, importe, fin) in sorted(ofertas.items())]
                      + [{"id": 800 + i, "status": "waiting", "amount": importe,
                          "requestedPlayers": [{"id": pid}], "from": {"id": YO}}
                         for i, (pid, importe) in enumerate(sorted(pujas.items()))],
            "status": {"maximumBid": 14_000_000, "balance": saldo},
        },
        "my_team": [{"id": p, "price": 2_900_000 if p == LUISMI else 1_000_000}
                    for p in sorted(plantilla)],
        "catalog": {"data": {"players": {str(p): {"status": s} for p, s in estados.items()}}},
    }


class _Escritor:
    def __init__(self):
        self.llamadas = []

    def _bien(self):
        return {"sent": True, "success": True, "http_status": 200}

    def place_bid(self, player_id, amount, execute, **k):
        self.llamadas.append(("PUJAR", player_id, amount))
        return self._bien()

    def cancel_bid(self, offer_id, execute):
        self.llamadas.append(("CANCELAR", offer_id))
        return self._bien()

    def accept_offer(self, offer_id, execute):
        self.llamadas.append(("ACEPTAR", offer_id))
        return self._bien()

    def list_player_for_sale(self, player_id, price, execute):
        self.llamadas.append(("PUBLICAR", player_id, price))
        return self._bien()


@contextmanager
def _entorno(**puestos):
    """Sin ningun `BORDALAS_*` (salvo el vigilante de la verja) ni
    `GITHUB_RUN_ID`, con `puestos` encima; al salir, como estaba."""
    antes = dict(os.environ)
    try:
        for k in list(os.environ):
            if (k.startswith("BORDALAS_") and k != "BORDALAS_VIGILA_DATA") or k == "GITHUB_RUN_ID":
                os.environ.pop(k, None)
        for k, v in puestos.items():
            if v is not None:
                os.environ[k] = v
        yield
    finally:
        os.environ.clear()
        os.environ.update(antes)


def _orden_correr(ahora=AHORA, snapshot=None, orden=ORDEN, calendario=CAL):
    escritor = _Escritor()
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(json.dumps(orden))
        s = orden_mod.correr({"snapshot": snapshot or _la_foto()}, lambda: escritor,
                             ruta=ruta, ahora=ahora, calendario=calendario)
    return s, escritor


# ------------------------------------------------------------------
# LA MEJORA: Kubo (medio, 5,0 x 70 %) por Exposito (medio, 2,9 x 100 %):
# +0,6 puntos por jornada, puja 2.909.900 (+1 % y en 9.900).
# ------------------------------------------------------------------

ONCE_MEJORA = [
    {"id": EXPOSITO, "name": "Exposito", "position": 3, "starter_probability": 100,
     "price": 4_995_368},
    {"id": 1, "name": "Portero", "position": 1, "starter_probability": 100, "price": 1_000_000},
    {"id": LUISMI, "name": "Luismi Cruz", "position": 4, "starter_probability": 60,
     "price": 2_900_000},
]
LIGA_MEJORA = {
    EXPOSITO: {"id": EXPOSITO, "name": "Exposito", "tasa": 2.9, "status": "ok",
               "price": 4_995_368, "de_quien": "nuestro", "position": 3, "played": 8},
    1: {"id": 1, "name": "Portero", "tasa": 3.0, "status": "ok", "price": 1_000_000,
        "de_quien": "nuestro", "position": 1, "played": 8},
    LUISMI: {"id": LUISMI, "name": "Luismi Cruz", "tasa": 4.67, "status": "ok",
             "price": 2_900_000, "de_quien": "nuestro", "position": 4, "played": 8},
    KUBO: {"id": KUBO, "name": "Kubo", "tasa": 5.0, "status": "ok", "price": 2_880_000,
           "de_quien": "computer", "position": 3, "played": 6, "price_increment": 200_000},
}
ESCAPARATE = [{"id": KUBO, "name": "Kubo", "position": 3, "price": 2_880_000, "points": 30,
               "played": 6, "starter_probability": 70}]
PUJA_KUBO = 2_909_900


def _foto_mejora(**k):
    f = {"plantilla": {1, EXPOSITO, LUISMI}, "nuestras_pujas": {},
         "ofertas_del_computer": {EXPOSITO: {"offer_id": 902, "amount": OFERTA_EXPOSITO}},
         "en_venta": {EXPOSITO}, "saldo": SALDO, "maximo_de_puja": 14_000_000,
         "mercado": {KUBO: 2_880_000}}
    f.update(k)
    return f


def _mejora_decidir(**k):
    base = dict(once=ONCE_MEJORA, liga=LIGA_MEJORA, escaparate=ESCAPARATE,
                foto=_foto_mejora(), libro={}, caja=SALDO,
                horas_jornada=_h(INICIO_J6, AHORA), en_9900=True)
    base.update(k)
    return mejora_mod.decidir(**base)


def _caducidades_exposito(hasta=HASTA_DEL_19):
    return {EXPOSITO: {"offer_id": 902, "oferta": hasta, "publicacion": PUBLICADO_EXPOSITO}}


def _mejora_correr(horas, aparte=None, saldo=SALDO, hasta_exposito=HASTA_DEL_19,
                   puestos=None):
    status = {
        "todaLaLiga": {"players": list(LIGA_MEJORA.values())},
        "lineup": {"players": ONCE_MEJORA},
        "roster": {"players": [{"id": p["id"], "starter_probability": p["starter_probability"]}
                               for p in ONCE_MEJORA]},
        "libro_del_escaparate": {"players": ESCAPARATE},
    }
    snapshot = {
        "league": {"user": {"id": YO}},
        "market": {
            "sales": [{"player": {"id": KUBO}, "user": None, "price": 2_880_000},
                      {"player": {"id": EXPOSITO}, "user": {"id": YO}, "price": 4_995_368,
                       "until": _epoch(PUBLICADO_EXPOSITO)}],
            "offers": [{"id": 902, "status": "waiting", "amount": OFERTA_EXPOSITO,
                        "requestedPlayers": [{"id": EXPOSITO}], "from": None,
                        "until": _epoch(hasta_exposito)}],
            "status": {"maximumBid": 14_000_000, "balance": saldo},
        },
        "my_team": [{"id": p["id"], "price": p["price"]} for p in ONCE_MEJORA],
        "catalog": {"data": {"players": {str(p): {"status": "ok"}
                                         for p in (1, EXPOSITO, LUISMI, KUBO)}}},
    }
    escritor = _Escritor()
    with tempfile.TemporaryDirectory() as tmp, _entorno(**(puestos or {MEJORA_ENV: "1"})):
        fuera = {"orden": {}, "vetados": set(), "protegidos": set(), "rotando": set(),
                 "libro_ronda": os.path.join(tmp, "ronda.json"),
                 "libro_chollos": os.path.join(tmp, "chollos.json"),
                 "horas_jornada": horas, "puede_escribir": True, "en_curso": False}
        if aparte is not None:
            fuera["aparte"] = aparte(snapshot) if callable(aparte) else aparte
        s = mejora_mod.correr(status=status, snapshot=snapshot, v10={},
                              escritor_factory=lambda: escritor, ahora=AHORA,
                              libro_ruta=os.path.join(tmp, "mejora.json"), calendario={},
                              de_fuera=fuera)
    return s, escritor


# ------------------------------------------------------------------
# EL CIERRE: 11 justos en 3-5-2 (el 5, del libro de los chollos, en el
# once escrito), un portero suplente con oferta y la puja por Kubo viva.
# ------------------------------------------------------------------

def _jug(pid, nombre, pos, precio=1_000_000):
    return {"id": pid, "name": nombre, "position": pos, "team_id": 1, "points": 30,
            "played": 8, "starter_probability": 80, "price": precio, "status": "ok"}


PLANTILLA_CIERRE = (
    [_jug(1, "Portero", 1)]
    + [_jug(p, f"D{p}", 2) for p in (2, 3, 4)]
    + [_jug(p, f"M{p}", 3) for p in (5, 6, 7, 8, 9)]
    + [_jug(10, "F10", 4), _jug(LUISMI, "Luismi Cruz", 4, 2_900_000)]
    + [_jug(12, "Suplente", 1, 2_000_000)]
)
ONCE_ESCRITO = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, LUISMI})
OFERTA_SUPLENTE = 1_900_000


def _cierre_decidir(**k):
    base = dict(
        plantilla=PLANTILLA_CIERRE, ctx={}, horas=_h(INICIO_J6, AHORA), saldo=SALDO,
        pujas={KUBO: {"offer_id": 801, "amount": 3_000_000}},
        ofertas={LUISMI: {"offer_id": 901, "amount": OFERTA_LUISMI},
                 12: {"offer_id": 903, "amount": OFERTA_SUPLENTE}},
        en_venta={LUISMI}, especulativas={5}, protegidos={KUBO}, no_vender={LUISMI},
        once_escrito=set(ONCE_ESCRITO), no_retirar={KUBO}, inventario={5},
    )
    base.update(k)
    return cierre_mod.decidir(**base)


def _cierre_correr(ahora=AHORA, puestos=None, pujas=None, calendario=CAL, libros=None,
                   hasta=HASTA_LUISMI):
    pujas = {KUBO: 3_000_000} if pujas is None else pujas
    status = {"roster": {"players": PLANTILLA_CIERRE},
              "lineup": {"players": [{"id": p} for p in sorted(ONCE_ESCRITO)]},
              "todaLaLiga": {"players": PLANTILLA_CIERRE}}
    plantilla = {p["id"] for p in PLANTILLA_CIERRE}
    snapshot = _la_foto(plantilla=plantilla, pujas=pujas, hasta=hasta,
                        ofertas={LUISMI: (901, OFERTA_LUISMI, hasta),
                                 12: (903, OFERTA_SUPLENTE, HASTA_LUISMI)})
    snapshot["my_team"] = [{"id": p["id"], "price": p["price"]} for p in PLANTILLA_CIERRE]
    escritor = _Escritor()
    libros = {"ronda": {}, "chollos": {"5": 1_000_000}, "mejora": {}} if libros is None else libros
    with tempfile.TemporaryDirectory() as tmp, \
            _entorno(**(puestos or {CIERRE_ENV: "1", ORDEN_ENV: "1"})):
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(json.dumps(ORDEN))
        s = cierre_mod.correr(status=status, snapshot=snapshot, v10={}, libros=libros,
                              calendario=calendario, orden_ruta=ruta,
                              escritor_factory=lambda: escritor, ahora=ahora,
                              plan_ruta=Path(tmp) / "el_cierre.json")
    return s, escritor


# ------------------------------------------------------------------
# T3. APAGADO, BYTE A BYTE LO DE ANTES
# ------------------------------------------------------------------
#
#     Las salidas enteras de `decidir` (y `la_mejor_combinacion`) y de
#     `correr` de los tres motores en estos escenarios, capturadas con el
#     codigo de ANTES de este cambio (7f35ef4f, 20/10/2026): su sha256
#     sobre el JSON canonico. Apagado, un solo byte distinto (o una clave
#     nueva) lo pone rojo.
#
#     Si un motor cambia A PROPOSITO en otro arreglo, se vuelven a grabar:
#     `python -m src.analysis.test_el_aplazado_no_frena_v1 --grabar`.

def _apagado_orden():
    return [
        _orden_decidir(),                                       # T1: EL_RELOJ
        _orden_decidir(horas_jornada=50.0),                     # a 50 h: se puja
        _orden_decidir(horas_jornada=None),                     # sin calendario
        _orden_decidir(nuestras_pujas={KUBO: {"offer_id": 801, "amount": 2_500_000}}),
        _orden_decidir(orden=_con_puja(ORDEN, 1_000_000)),     # Kubo es relevo: no la paga la caja
        _orden_decidir(**T1B),                                  # T1b: se cobra a Luismi
        _orden_decidir(**{**T1B, "estados": {KUBO: "injured", LUISMI: "ok"}}),
        _orden_decidir(**{**T1B, "estados": {KUBO: "doubt", LUISMI: "ok"}}),
        _orden_decidir(**{**T1B, "plantilla": set(NUESTROS)}),  # Kubo perdido
        _orden_decidir(**{**T1B, "saldo": 100}),                # en positivo
    ]


def _apagado_mejora():
    libro = {str(KUBO): {"sale": EXPOSITO, "suelo": 4_495_000}}
    con_kubo = _foto_mejora(plantilla={1, EXPOSITO, LUISMI, KUBO}, saldo=-1_441_917,
                            mercado={})
    cambios = [
        {"entra": 1, "sale": 2, "puntos": 0.8, "caja": -2_000_000, "puja": 2_000_000},
        {"entra": 3, "sale": 4, "puntos": 0.2, "caja": 3_000_000, "puja": 1_000_000},
        {"entra": 5, "sale": 6, "puntos": 0.6, "caja": 0, "puja": 0, "ya_es_nuestro": True},
    ]
    return [
        _mejora_decidir(),                                       # a 23,2 h: no compra
        _mejora_decidir(horas_jornada=45.0),                     # compra, minimo 0
        _mejora_decidir(horas_jornada=_h(INICIO_J10, AHORA)),    # compra, minimo -1 M
        _mejora_decidir(horas_jornada=45.0, caja=-2_000_000),
        _mejora_decidir(horas_jornada=_h(INICIO_J6, TRAS_EL_RESET), libro=libro,
                        foto=con_kubo, escaparate=[]),           # cobra a Exposito
        mejora_mod.la_mejor_combinacion(cambios, 0, -1_000_000, 10_000_000),
        mejora_mod.la_mejor_combinacion(cambios, -3_000_000, 0, 10_000_000, deficit=True),
    ]


def _apagado_cierre():
    return [
        _cierre_decidir(),                                       # T9 apagado: se vende
        _cierre_decidir(pujas={KUBO: {"offer_id": 801, "amount": 3_000_000},
                               700: {"offer_id": 802, "amount": 300_000}},
                        especulativas={5, 700}),                 # y se retira la de 700
        _cierre_decidir(horas=50.0),
        _cierre_decidir(saldo=5_000_000),                        # en positivo: se adopta
    ]


def _apagado_correr():
    salidas = []
    with _entorno(**{ORDEN_ENV: "1"}):
        for ahora in (AHORA, TRAS_EL_RESET):
            snapshot = _la_foto() if ahora == AHORA else _la_foto(
                saldo=-1_532_017, plantilla=set(NUESTROS) | {KUBO})
            s, escritor = _orden_correr(ahora=ahora, snapshot=snapshot)
            salidas.append([s, escritor.llamadas])
    for horas in (_h(INICIO_J6, AHORA), _h(INICIO_J10, AHORA)):
        s, escritor = _mejora_correr(horas)
        salidas.append([s, escritor.llamadas])
    s, escritor = _cierre_correr()
    salidas.append([s, escritor.llamadas])
    return salidas


def _canon(x):
    if isinstance(x, (set, frozenset)):
        return sorted(x, key=str)
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(type(x))


def _texto(x) -> str:
    return json.dumps(x, sort_keys=True, default=_canon, ensure_ascii=False)


def _huella(x) -> str:
    return hashlib.sha256(_texto(x).encode("utf-8")).hexdigest()


def _las_huellas() -> dict:
    with _entorno():
        return {
            "orden": _huella(_apagado_orden()),
            "mejora": _huella(_apagado_mejora()),
            "cierre": _huella(_apagado_cierre()),
            "correr": _huella(_apagado_correr()),
        }


# Grabadas con el codigo de 7f35ef4f (antes de este cambio), con el
# entorno limpio. Lo mismo, legible, en `LO_DE_ANTES`.
HUELLAS_DE_ANTES = {
    "orden": "aa31d1c2b3d28937bb624126447ce56c6f2f418c7cfd553a2cf5cd52085cd157",
    "mejora": "223e69393da73dde243783cb7612fd9e4e2ccd0ae716dd7e7e9271e1e3f461c5",
    "cierre": "c0af8b01381f13073de0255da5cadabdce91bfb91d92f21e897fcbf5bd65db8d",
    "correr": "715d1d3fe5263f41b0bcb4fca6f73fd045d29558bb39497d0ed28c53225e70f5",
}

LO_DE_ANTES = {
    "orden": [[("NADA", KUBO, "EL_RELOJ")], [("PUJAR", KUBO, None)],
              [("NADA", KUBO, "EL_RELOJ")], [("NADA", KUBO, "EL_RELOJ")],
              [("NADA", KUBO, "EL_RELOJ")], [("ACEPTAR_OFERTA_DEL_COMPUTER", LUISMI, None)],
              [("NADA", LUISMI, "EL_PARTE_DEL_RELEVO")],
              [("ACEPTAR_OFERTA_DEL_COMPUTER", LUISMI, None)], [],
              [("ACEPTAR_OFERTA_DEL_COMPUTER", LUISMI, None)]],
    "cierre": ["EN_ROJO_SE_VENDE", "EN_ROJO_SE_VENDE", "EN_ROJO_SE_VENDE", "EN_POSITIVO"],
}


def _las_claves(x, salida=None) -> set:
    salida = set() if salida is None else salida
    if isinstance(x, dict):
        for k, v in x.items():
            salida.add(k)
            _las_claves(v, salida)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _las_claves(v, salida)
    return salida


NUEVAS = {"aplazado", "credito_del_aplazado", "caja_del_aplazado", "caja_aplazado"}


def _tipos(acciones):
    return [(a["accion"], a["player_id"], a.get("guardia")) for a in acciones]


# ------------------------------------------------------------------
# LAS PRUEBAS
# ------------------------------------------------------------------

def test_t13_nace_apagado() -> None:
    assert orden_mod.ENV_EL_APLAZADO == EL_APLAZADO
    with _entorno():
        assert not orden_mod.el_aplazado_activo()
    for valor in ("1", "true", "si", "yes", "SI", " True "):
        with _entorno(**{EL_APLAZADO: valor}):
            assert orden_mod.el_aplazado_activo(), valor
    for valor in ("0", "no", "", "false", "2"):
        with _entorno(**{EL_APLAZADO: valor}):
            assert not orden_mod.el_aplazado_activo(), valor


def test_t3_apagado_es_byte_a_byte_lo_de_antes() -> None:
    with _entorno():
        orden = _apagado_orden()
        cierre = _apagado_cierre()
        mejora = _apagado_mejora()
        correr = _apagado_correr()
        assert [[(a["accion"], a["player_id"], a.get("guardia")) for a in d]
                for d in orden] == LO_DE_ANTES["orden"], [_tipos(d) for d in orden]
        assert [d["motivo"] for d in cierre] == LO_DE_ANTES["cierre"], [d["motivo"] for d in cierre]
        huellas = {"orden": _huella(orden), "mejora": _huella(mejora),
                   "cierre": _huella(cierre), "correr": _huella(correr)}
        assert huellas == HUELLAS_DE_ANTES, huellas
        # Ni una clave nueva en nada de lo que sale (salida, plan, reloj).
        nuevas = _las_claves([orden, mejora, cierre, correr]) & NUEVAS
        assert not nuevas, nuevas
        # Y pasando lo nuevo vacio (None, 0), igual.
        assert _huella([_orden_decidir(aparte=None), _orden_decidir(**T1B, aparte=None)]) == \
            _huella(orden[:1] + orden[5:6])
        assert _huella(_mejora_decidir(aparte=None, horas_jornada=45.0)) == _huella(mejora[1])
        assert _huella([_cierre_decidir(credito=0), _cierre_decidir(credito=None)]) == \
            _huella([cierre[0], cierre[0]])
        cambios = [{"entra": 1, "sale": 2, "puntos": 0.8, "caja": -2_000_000, "puja": 2_000_000}]
        assert mejora_mod.la_mejor_combinacion(cambios, 0, -1_000_000, 10_000_000,
                                               caja_aplazado=None) == \
            mejora_mod.la_mejor_combinacion(cambios, 0, -1_000_000, 10_000_000)


def test_el_proximo_cierre_en_el_calendario_de_produccion() -> None:
    c = pj.el_proximo_cierre(AHORA, CAL)
    assert c["parcial"] is True and c["resuelve_antes"] is True, c
    assert c["inicio"] == INICIO_J6 and c["inicio_principal"] == INICIO_J10, c
    assert c["proximo_reset"] == RESET_21, c
    assert round(c["horas"], 2) == 23.22 and round(c["horas_principal"], 2) == 72.22, c
    # La vuelta de despues del reset: el aplazado a 12,75 h, ya sin reset antes.
    c = pj.el_proximo_cierre(TRAS_EL_RESET, CAL)
    assert c["parcial"] and c["horas"] == 12.75 and c["resuelve_antes"] is False, c
    # Con el aplazado jugandose, lo proximo es la J10 entera a 48,5 h.
    c = pj.el_proximo_cierre(datetime(2026, 10, 21, 18, 30, tzinfo=UTC), CAL)
    assert c["parcial"] is False and c["horas"] == 48.5 == c["horas_principal"], c
    # Las mismas horas que `horas_al_proximo_cierre` (las de vender), siempre.
    for h in range(0, 24 * 8, 5):
        ahora = datetime(2026, 10, 18, 0, 7, tzinfo=UTC) + timedelta(hours=h)
        assert pj.el_proximo_cierre(ahora, CAL)["horas"] == pj.horas_al_proximo_cierre(ahora, CAL)
    # Un reset dado a mano manda; uno sin zona no se sabe.
    tarde = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)
    assert pj.el_proximo_cierre(AHORA, CAL, reset=tarde)["resuelve_antes"] is False
    assert pj.el_proximo_cierre(AHORA, CAL, reset=datetime(2026, 10, 21, 5))["resuelve_antes"] is False


def test_el_proximo_reset_es_el_de_la_rotacion() -> None:
    from src.actions.la_rotacion import los_resets

    assert pj.el_proximo_reset(AHORA) == RESET_21
    assert pj.el_proximo_reset(RESET_21) == RESET_21 + timedelta(days=1)
    # El cambio de hora del 25/10: el reset pasa a las 06:00 UTC.
    assert pj.el_proximo_reset(datetime(2026, 10, 25, 2, 0, tzinfo=UTC)) == \
        datetime(2026, 10, 25, 6, 0, tzinfo=UTC)
    for h in range(0, 24 * 12, 7):
        ahora = datetime(2026, 10, 19, 3, 0, tzinfo=UTC) + timedelta(hours=h)
        assert pj.el_proximo_reset(ahora) == los_resets(ahora)[1], ahora


def test_t10_que_es_un_aplazado() -> None:
    from src.actions.la_rotacion import _es_parcial

    # El de produccion: la J6 con UN partido y sin `aparte`.
    rondas = pj.las_rondas(CAL)
    lev = [r for r in rondas if r["jornada"] == 6]
    assert len(lev) == 1 and lev[0]["partidos"] == 1 and lev[0]["aparte"] is False, lev
    assert pj.es_parcial(lev[0]) is True
    j10 = [r for r in rondas if r["jornada"] == 10]
    assert j10[0]["partidos"] == 10 and pj.es_parcial(j10[0]) is False
    # Reconstruido (la J6 con el adelantado, el grueso y el aplazado): el
    # Levante-Athletic va `aparte`, y sigue siendo de aplazados.
    grueso = [_p(6, f"Equipo {i}", f"Equipo {i + 10}", f"2026-09-{15 + i % 3}T{14 + i}:00:00+02:00")
              for i in range(8)]
    rehecho = {"matchdays": [{"matchday": 6, "matches": [
        _p(6, "Real Sociedad", "Celta", "2026-09-03T21:00:00+02:00")] + grueso + [LEV_ATH]}]}
    rondas = pj.las_rondas(rehecho)
    aparte = [r for r in rondas if r["inicio"] == INICIO_J6]
    assert aparte and aparte[0]["aparte"] is True and pj.es_parcial(aparte[0]), rondas
    principal = [r for r in rondas if r["partidos"] == 8]
    assert principal and not pj.es_parcial(principal[0]), rondas
    # La misma regla que la rotacion; sin saberlo, no es de aplazados.
    for r in rondas + [{"partidos": 4}, {"partidos": 5}, {"aparte": True, "partidos": 9}]:
        assert pj.es_parcial(r) == _es_parcial(r), r
    for basura in (None, "x", 5, {}, {"partidos": "x"}, {"partidos": True}):
        assert pj.es_parcial(basura) is False, basura


def test_las_caducidades() -> None:
    foto = _la_foto()
    cad = orden_mod.las_caducidades(foto, YO)
    assert cad[LUISMI] == {"offer_id": 901, "oferta": HASTA_LUISMI,
                           "publicacion": PUBLICADO_LUISMI}, cad
    # La oferta que se queda es la de `leer_la_foto` (la mas alta).
    foto["market"]["offers"].append({"id": 905, "status": "waiting", "amount": 3_100_000,
                                     "requestedPlayers": [{"id": LUISMI}], "from": None,
                                     "created": _epoch(datetime(2026, 10, 20, 5, 6, tzinfo=UTC))})
    cad = orden_mod.las_caducidades(foto, YO)
    assert orden_mod.leer_la_foto(foto, YO)["ofertas_del_computer"][LUISMI]["offer_id"] == 905
    # Sin `until`: su `created` + 48 h.
    assert cad[LUISMI]["offer_id"] == 905, cad
    assert cad[LUISMI]["oferta"] == datetime(2026, 10, 22, 5, 6, tzinfo=UTC), cad
    # Ni `until` ni `created`: no se sabe, y no cuenta.
    del foto["market"]["offers"][-1]["created"]
    cad = orden_mod.las_caducidades(foto, YO)
    assert cad[LUISMI]["oferta"] is None
    ofertas = orden_mod.leer_la_foto(foto, YO)["ofertas_del_computer"]
    assert orden_mod.cobrable(LUISMI, 0, ofertas, cad, INICIO_J6) == 0
    # La publicacion de otro manager no es nuestra; la nuestra si.
    assert orden_mod.las_caducidades(_la_foto(), 99)[LUISMI]["publicacion"] is None
    # Una oferta que no es la que se cobra (otro `offer_id`) no vale.
    cad = orden_mod.las_caducidades(_la_foto(), YO)
    otra = {LUISMI: {"offer_id": 777, "amount": OFERTA_LUISMI}}
    assert orden_mod.cobrable(LUISMI, 0, otra, cad, INICIO_J6) == 0
    assert orden_mod.cobrable(LUISMI, 0, {LUISMI: {"amount": OFERTA_LUISMI}}, cad,
                              INICIO_J6) == OFERTA_LUISMI
    # Bajo el suelo, no.
    assert orden_mod.cobrable(LUISMI, 3_000_000, {LUISMI: {"amount": OFERTA_LUISMI}}, cad,
                              INICIO_J6) == 0


def test_t1_kubo_por_luismi() -> None:
    with _entorno():
        # Apagado: el reloj, a 23,2 h del aplazado.
        a = _orden_decidir()
        assert _tipos(a) == [("NADA", KUBO, "EL_RELOJ")] and "23.2 h" in a[0]["motivo"], a
        # Encendido: el `aparte` que monta `el_aplazado` con la foto de la vuelta.
        aparte = orden_mod.el_aplazado(AHORA, CAL, _la_foto(), YO)
        assert aparte is not None and aparte["resuelve_antes"] and aparte["inicio"] == INICIO_J6
        assert aparte["caducidades"][LUISMI]["oferta"] == HASTA_LUISMI, aparte
        a = _orden_decidir(aparte=aparte)
        assert a == [{"accion": "PUJAR", "player_id": KUBO, "nombre": "Kubo",
                      "importe": 3_000_000, "sustituye": None, "guardia": "EL_APLAZADO",
                      "caja_del_aplazado": 1_425_983}], a
        assert 1_425_983 == SALDO - 3_000_000 + OFERTA_LUISMI
        # El limite: hasta 4.425.983 pasa (caja 0); un euro mas, no.
        a = _orden_decidir(orden=_con_puja(ORDEN, 4_425_983), aparte=aparte)
        assert _tipos(a) == [("PUJAR", KUBO, "EL_APLAZADO")] and a[0]["caja_del_aplazado"] == 0
        a = _orden_decidir(orden=_con_puja(ORDEN, 4_425_984), aparte=aparte)
        assert _tipos(a) == [("NADA", KUBO, "EL_APLAZADO")] and a[0]["caja_del_aplazado"] == -1, a
        # Subir la viva: la vieja deja de contar, la nueva cuenta entera.
        viva = {KUBO: {"offer_id": 801, "amount": 3_000_000}}
        a = _orden_decidir(orden=_con_puja(ORDEN, 4_425_983), aparte=aparte, nuestras_pujas=viva)
        assert _tipos(a) == [("PUJAR", KUBO, "EL_APLAZADO")] and a[0]["sustituye"] == viva[KUBO]
        assert a[0]["caja_del_aplazado"] == 0, a
        # Las demas pujas vivas cuentan enteras.
        otra = {555: {"offer_id": 802, "amount": 1_425_984}}
        a = _orden_decidir(aparte=aparte, nuestras_pujas=otra)
        assert _tipos(a) == [("NADA", KUBO, "EL_APLAZADO")] and a[0]["caja_del_aplazado"] == -1, a


def test_t1_correr_de_punta_a_punta() -> None:
    with _entorno(**{ORDEN_ENV: "1"}):
        s, escritor = _orden_correr()
        assert s["motivo"] == "NADA_QUE_HACER" and escritor.llamadas == [], s
        assert "aplazado" not in s and _tipos(s["acciones"]) == [("NADA", KUBO, "EL_RELOJ")]
    with _entorno(**{ORDEN_ENV: "1", EL_APLAZADO: "1"}):
        s, escritor = _orden_correr()
        assert s["motivo"] == "EJECUTADA" and escritor.llamadas == [("PUJAR", KUBO, 3_000_000)], s
        assert s["aplazado"] == {"inicio": INICIO_J6.isoformat(), "horas": 23.22,
                                 "horas_principal": 72.22,
                                 "inicio_principal": INICIO_J10.isoformat(),
                                 "proximo_reset": RESET_21.isoformat(),
                                 "resuelve_antes": True}, s["aplazado"]
        assert json.loads(json.dumps(s, default=str))["aplazado"] == s["aplazado"]
        assert s["acciones"][0]["caja_del_aplazado"] == 1_425_983
        # El reloj de la vuelta es el de siempre (las horas al aplazado).
        assert round(s["reloj"]["horas_jornada"], 2) == 23.22 and set(s["reloj"]) == {
            "horas_jornada", "en_curso"}, s["reloj"]


def test_t1b_la_vuelta_siguiente_cobra() -> None:
    with _entorno():
        foto = _la_foto(saldo=-1_532_017, plantilla=set(NUESTROS) | {KUBO})
        aparte = orden_mod.el_aplazado(TRAS_EL_RESET, CAL, foto, YO)
        assert aparte is not None and aparte["resuelve_antes"] is False, aparte
        cobra = [("ACEPTAR_OFERTA_DEL_COMPUTER", LUISMI, None)]
        for ap in (None, aparte):
            a = _orden_decidir(**T1B, aparte=ap)
            assert _tipos(a) == cobra and a[0]["importe"] == OFERTA_LUISMI, (ap, a)
        # Kubo lesionado (o sancionado): apagado no se cobra; encendido, antes
        # del aplazado y en rojo, manda la caja.
        for parte in ("injured", "sanctioned"):
            lesion = {**T1B, "estados": {KUBO: parte, LUISMI: "ok"}}
            assert _tipos(_orden_decidir(**lesion)) == [
                ("NADA", LUISMI, "EL_PARTE_DEL_RELEVO")]
            assert _tipos(_orden_decidir(**lesion, aparte=aparte)) == cobra
            # En positivo no hace falta la caja: tampoco encendido.
            sobra = {**lesion, "saldo": 100}
            assert _tipos(_orden_decidir(**sobra, aparte=aparte)) == [
                ("NADA", LUISMI, "EL_PARTE_DEL_RELEVO")]
            # Con la ronda entera ya dentro del reloj (no da tiempo a fichar
            # otro relevo para ella) o sin saber cuando es: decide el gestor.
            for cerca in ({**aparte, "horas_principal": 39.9}, {**aparte, "horas_principal": None}):
                assert _tipos(_orden_decidir(**lesion, aparte=cerca)) == [
                    ("NADA", LUISMI, "EL_PARTE_DEL_RELEVO")], cerca
        # Un calendario de rondas cortas sin ninguna entera detras (el de
        # `test_la_orden_del_gestor_v1`: una «J9» de tres partidos): el
        # aplazado se ve, pero la caja no manda sobre el relevo lesionado.
        corto = {"matchdays": [{"matchday": 9, "matches": [
            {"kickoff": "2026-10-21T20:00:00+02:00"}, {"kickoff": "2026-10-22T18:30:00+02:00"},
            {"kickoff": "2026-10-23T21:00:00+02:00"}]}]}
        sin_entera = orden_mod.el_aplazado(TRAS_EL_RESET, corto, foto, YO)
        assert sin_entera is not None and sin_entera["horas_principal"] is None, sin_entera
        lesion = {**T1B, "estados": {KUBO: "injured", LUISMI: "ok"}}
        assert _tipos(_orden_decidir(**lesion, aparte=sin_entera)) == [
            ("NADA", LUISMI, "EL_PARTE_DEL_RELEVO")]
        # Kubo perdido: Luismi no se vende y el saldo no se toca.
        perdido = {**T1B, "plantilla": set(NUESTROS), "saldo": SALDO}
        assert _orden_decidir(**perdido) == [] == _orden_decidir(**perdido, aparte=aparte)


def test_t2_la_oferta_que_muere_en_el_reset() -> None:
    with _entorno():
        aparte = orden_mod.el_aplazado(AHORA, CAL, _la_foto(hasta=HASTA_DEL_19), YO)
        assert aparte["caducidades"][LUISMI]["oferta"] == HASTA_DEL_19 < INICIO_J6
        # Minutos DESPUES del reset que la resuelve, y muerta antes del aplazado.
        assert HASTA_DEL_19 > RESET_21
        a = _orden_decidir(aparte=aparte)
        assert _tipos(a) == [("NADA", KUBO, "EL_APLAZADO")], a
        assert a[0]["caja_del_aplazado"] == -1_532_017, a
        # La que paga el saldo sola (sin vender a nadie) si pasa.
        a = _orden_decidir(orden=_con_puja(ORDEN, SALDO), aparte=aparte)
        assert _tipos(a) == [("PUJAR", KUBO, "EL_APLAZADO")] and a[0]["caja_del_aplazado"] == 0
        # La oferta viva pero la publicacion muerta antes del aplazado: no cuenta.
        muerta = orden_mod.el_aplazado(AHORA, CAL, _la_foto(publicado=PUBLICADO_EXPOSITO), YO)
        a = _orden_decidir(aparte=muerta)
        assert _tipos(a) == [("NADA", KUBO, "EL_APLAZADO")], a
        # Viva, pero por debajo del suelo de la orden (2,7 M): tampoco.
        viva = orden_mod.el_aplazado(AHORA, CAL, _la_foto(), YO)
        a = _orden_decidir(aparte=viva, ofertas_del_computer={
            LUISMI: {"offer_id": 901, "amount": 2_600_000}})
        assert _tipos(a) == [("NADA", KUBO, "EL_APLAZADO")], a
        assert a[0]["caja_del_aplazado"] == -1_532_017, a


def test_t2_la_mejora_no_elige_el_cambio_que_no_se_paga() -> None:
    with _entorno():
        aparte = {**_aparte(caducidades=_caducidades_exposito()), "caja": SALDO}
        # Apagado (sin aparte), a 23,2 h: no compra.
        d = _mejora_decidir()
        assert d["acciones"] == [] and "minimo" not in d["plan"], d["plan"]
        # Encendido: se mide hasta la J10 (72,2 h: minimo con deuda), pero la
        # oferta de Exposito muere en el reset y la puja no cabe.
        d = _mejora_decidir(aparte=aparte)
        assert d["acciones"] == [] and d["plan"]["minimo"] == -1_000_000, d["plan"]
        assert d["plan"]["aplazado"] == {"inicio": INICIO_J6.isoformat(),
                                         "horas_principal": 72.22, "caja": SALDO,
                                         "caja_despues": SALDO}, d["plan"]["aplazado"]
        cambio = mejora_mod.con_la_caja_del_aplazado(
            {"entra": KUBO, "sale": EXPOSITO, "puja": PUJA_KUBO, "ya_es_nuestro": False},
            _foto_mejora()["ofertas_del_computer"], mejora_mod._el_aplazado_de_la_mejora(aparte))
        assert cambio["caja_aplazado"] == -PUJA_KUBO and SALDO - PUJA_KUBO == -1_441_917
        # A 45 h, como hoy: se elige, y el plan no dice nada del aplazado.
        d45 = _mejora_decidir(horas_jornada=45.0, aparte=aparte)
        assert d45 == _mejora_decidir(horas_jornada=45.0), d45
        assert [(a["accion"], a["player_id"], a["importe"]) for a in d45["acciones"]] == [
            ("PUJAR", KUBO, PUJA_KUBO)] and "aplazado" not in d45["plan"]
        # Con la oferta (y la publicacion) de Exposito vivas al empezar el
        # aplazado, el cambio se paga solo: se elige.
        viva = {**aparte, "caducidades": {EXPOSITO: {"offer_id": 902, "oferta": HASTA_LUISMI,
                                                     "publicacion": PUBLICADO_LUISMI}}}
        d = _mejora_decidir(aparte=viva)
        assert [(a["accion"], a["player_id"], a["importe"]) for a in d["acciones"]] == [
            ("PUJAR", KUBO, PUJA_KUBO)], d
        assert d["plan"]["cambios"][0]["caja_aplazado"] == 0
        assert d["plan"]["aplazado"]["caja_despues"] == SALDO
        # Sin `resuelve_antes`, o con la J10 a menos de 40 h, lo de siempre.
        for malo in ({**viva, "resuelve_antes": False}, {**viva, "horas_principal": 37.0},
                     {**viva, "caja": None}, {**viva, "inicio": None}):
            assert _mejora_decidir(aparte=malo) == _mejora_decidir(), malo


def test_t2_la_mejora_correr() -> None:
    def _de_la_foto(snapshot):
        return orden_mod.el_aplazado(AHORA, CAL, snapshot, YO)

    horas = _h(INICIO_J6, AHORA)
    apagado, _ = _mejora_correr(horas)
    assert "aplazado" not in apagado["plan"] and apagado["motivo"] == "NADA_QUE_HACER"
    puestos = {MEJORA_ENV: "1", EL_APLAZADO: "1", "BORDALAS_LA_PUJA_EN_9900": "1"}
    s, escritor = _mejora_correr(horas, aparte=_de_la_foto, puestos=puestos)
    assert s["motivo"] == "NADA_QUE_HACER" and escritor.llamadas == [], s
    assert s["plan"]["aplazado"]["caja"] == SALDO and s["plan"]["minimo"] == -1_000_000, s["plan"]
    # Con la oferta de Exposito viva hasta el 22/10 pero su publicacion
    # muerta el 21/10 a las 07:16: sigue sin pagarse.
    s, escritor = _mejora_correr(horas, aparte=_de_la_foto, puestos=puestos,
                                 hasta_exposito=HASTA_LUISMI)
    assert escritor.llamadas == [], s
    # Encendido, con las horas dadas y sin `aparte`: no lee produccion, como apagado.
    s, _ = _mejora_correr(horas, puestos={MEJORA_ENV: "1", EL_APLAZADO: "1"})
    assert _huella(s) == _huella(apagado), s


def test_t4_el_aplazado_sin_ventana_propia() -> None:
    cal = {"matchdays": [
        {"matchday": 6, "matches": [_p(6, "Levante UD", "Athletic Club",
                                       "2026-10-23T14:00:00+02:00")]},
        {"matchday": 10, "matches": J10}]}
    ahora = datetime(2026, 10, 22, 6, 0, tzinfo=UTC)
    c = pj.el_proximo_cierre(ahora, cal)
    assert c["parcial"] and c["horas"] == 30.0 and c["horas_principal"] == 37.0, c
    with _entorno():
        aparte = orden_mod.el_aplazado(ahora, cal, _la_foto(), YO)
        assert aparte is not None
        kw = dict(ahora=ahora, horas_jornada=30.0)
        assert _orden_decidir(**kw, aparte=aparte) == _orden_decidir(**kw)
        assert _tipos(_orden_decidir(**kw)) == [("NADA", KUBO, "EL_RELOJ")]
        mejora = {**aparte, "caja": SALDO, "caducidades": _caducidades_exposito(HASTA_LUISMI)}
        assert _mejora_decidir(horas_jornada=30.0, aparte=mejora) == \
            _mejora_decidir(horas_jornada=30.0)
        # T4b: el aplazado a 54 h: ni se mira.
        antes = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
        assert pj.el_proximo_cierre(antes, CAL)["horas"] == 54.0
        assert orden_mod.el_aplazado(antes, CAL, _la_foto(), YO) is None


def test_t5_la_ronda_entera_como_hoy() -> None:
    a_37 = datetime(2026, 10, 22, 6, 0, tzinfo=UTC)          # J10 a 37 h
    jugandose = datetime(2026, 10, 21, 18, 30, tzinfo=UTC)  # J10 a 48,5 h
    c = pj.el_proximo_cierre(a_37, CAL)
    assert c["parcial"] is False and c["horas"] == 37.0, c
    for ahora in (a_37, jugandose):
        assert orden_mod.el_aplazado(ahora, CAL, _la_foto(), YO) is None
        salidas = {}
        for puesto in (None, "1"):
            with _entorno(**{ORDEN_ENV: "1", EL_APLAZADO: puesto}):
                s, escritor = _orden_correr(ahora=ahora)
            c_s, c_e = _cierre_correr(ahora=ahora, puestos={
                CIERRE_ENV: "1", ORDEN_ENV: "1", EL_APLAZADO: puesto})
            salidas[puesto] = _huella([s, escritor.llamadas, c_s, c_e.llamadas])
            if ahora == a_37:
                assert _tipos(s["acciones"]) == [("NADA", KUBO, "EL_RELOJ")], s
            else:
                assert _tipos(s["acciones"]) == [("PUJAR", KUBO, None)], s
            assert "credito_del_aplazado" not in (c_s.get("decision") or {}), c_s
        assert salidas[None] == salidas["1"], ahora
    # La mejora: con la J10 entera, `el_aplazado` es None y `decidir` es el de siempre.
    with _entorno():
        assert _mejora_decidir(horas_jornada=37.0, aparte=None) == _mejora_decidir(
            horas_jornada=37.0)


def test_t6_tras_el_ultimo_reset() -> None:
    ahora = datetime(2026, 10, 21, 7, 0, tzinfo=UTC)
    c = pj.el_proximo_cierre(ahora, CAL)
    assert c["parcial"] and c["horas"] == 11.0 and c["resuelve_antes"] is False, c
    with _entorno():
        aparte = orden_mod.el_aplazado(ahora, CAL, _la_foto(), YO)
        kw = dict(ahora=ahora, horas_jornada=11.0)
        assert _orden_decidir(**kw, aparte=aparte) == _orden_decidir(**kw)
        assert _tipos(_orden_decidir(**kw)) == [("NADA", KUBO, "EL_RELOJ")]
    # El cierre: con la puja por Kubo viva y la oferta de Luismi, credito 0.
    apagado, _ = _cierre_correr(ahora=ahora)
    encendido, _ = _cierre_correr(ahora=ahora, puestos={CIERRE_ENV: "1", ORDEN_ENV: "1",
                                                        EL_APLAZADO: "1"})
    assert _huella(apagado) == _huella(encendido), encendido["decision"]
    with _entorno(**{ORDEN_ENV: "1", EL_APLAZADO: "1"}):
        foto = _la_foto(pujas={KUBO: 3_000_000})
        assert cierre_mod.el_credito_del_aplazado(
            ahora, CAL, foto, YO, orden_mod.leer_la_foto(foto, YO),
            {KUBO: {"amount": 3_000_000}}, ORDEN, {}, NUESTROS) == 0
        assert cierre_mod.el_credito_del_aplazado(
            AHORA, CAL, foto, YO, orden_mod.leer_la_foto(foto, YO),
            {KUBO: {"amount": 3_000_000}}, ORDEN, {}, NUESTROS) == OFERTA_LUISMI


def test_t7_un_cambio_no_paga_otra_puja() -> None:
    a, b, c = 30001, 30002, 30003
    ofertas = {LUISMI: {"offer_id": 901, "amount": OFERTA_LUISMI}}
    pujas = {a: {"amount": 1_000_000}, b: {"amount": 500_000}}
    parejas = {a: [(LUISMI, 0)]}
    assert orden_mod.lo_que_se_cobra_antes(pujas, parejas, ofertas, _caducidades(),
                                           INICIO_J6) == 1_000_000
    assert orden_mod.la_caja_del_aplazado(0, pujas, parejas, ofertas, _caducidades(),
                                          INICIO_J6) == -500_000
    orden = {"caduca": ORDEN["caduca"],
             "fichar": [{"player_id": c, "nombre": "C", "puja": 100_000}],
             "vender_si_ficha": {"jugadores": [
                 {"player_id": LUISMI, "nombre": "Luismi Cruz", "suelo": 0, "si_esta": a}]}}
    assert orden_mod.las_parejas_de_la_orden(orden, AHORA) == parejas
    with _entorno():
        acciones = _orden_decidir(
            orden=orden, mercado={c: 90_000}, saldo=0, estados={c: "ok"}, aparte=_aparte(),
            nuestras_pujas={a: {"offer_id": 1, "amount": 1_000_000},
                            b: {"offer_id": 2, "amount": 500_000}})
    assert _tipos(acciones) == [("NADA", c, "EL_APLAZADO")], acciones
    assert acciones[0]["caja_del_aplazado"] == -600_000, acciones


def test_t8_cada_oferta_cuenta_una_vez() -> None:
    x = 30010
    ofertas = {LUISMI: {"offer_id": 901, "amount": OFERTA_LUISMI}}
    pujas = {KUBO: 3_000_000, x: 2_000_000}
    parejas = {KUBO: [(LUISMI, 2_700_000)], x: [(LUISMI, 0)]}
    assert orden_mod.lo_que_se_cobra_antes(pujas, parejas, ofertas, _caducidades(),
                                           INICIO_J6) == OFERTA_LUISMI
    # La misma pareja dos veces en el mismo relevo, tambien una.
    assert orden_mod.lo_que_se_cobra_antes(
        {KUBO: 9_000_000}, {KUBO: [(LUISMI, 0), (LUISMI, 0)]}, ofertas, _caducidades(),
        INICIO_J6) == OFERTA_LUISMI
    # En el cierre: la de la orden y la del libro de la mejora, una vez.
    foto = _la_foto(pujas=pujas)
    with _entorno(**{ORDEN_ENV: "1", EL_APLAZADO: "1"}):
        credito = cierre_mod.el_credito_del_aplazado(
            AHORA, CAL, foto, YO, orden_mod.leer_la_foto(foto, YO),
            {KUBO: {"amount": 3_000_000}, x: {"amount": 2_000_000}}, ORDEN,
            {str(x): {"sale": LUISMI}}, NUESTROS)
        assert credito == OFERTA_LUISMI, credito
    # Sin la orden viva, solo la del libro de la mejora (con su puja de tope).
    with _entorno(**{EL_APLAZADO: "1"}):
        credito = cierre_mod.el_credito_del_aplazado(
            AHORA, CAL, foto, YO, orden_mod.leer_la_foto(foto, YO),
            {KUBO: {"amount": 3_000_000}, x: {"amount": 2_000_000}}, ORDEN,
            {str(x): {"sale": LUISMI}}, NUESTROS)
        assert credito == 2_000_000, credito
        # El relevo de la mejora ya dentro: su cambio no tiene puja que pagar.
        assert cierre_mod.el_credito_del_aplazado(
            AHORA, CAL, foto, YO, orden_mod.leer_la_foto(foto, YO),
            {KUBO: {"amount": 3_000_000}, x: {"amount": 2_000_000}}, ORDEN,
            {str(x): {"sale": LUISMI}}, set(NUESTROS) | {x}) == 0
    # En la mejora: el cambio cuyo `sale` ya cuenta para la orden no entra.
    with _entorno(**{ORDEN_ENV: "1"}):
        aparte = mejora_mod.el_aplazado_de_la_vuelta(
            {"aparte": _aparte()}, AHORA, None, YO,
            {"saldo": SALDO, "nuestras_pujas": {KUBO: {"amount": 3_000_000}},
             "ofertas_del_computer": ofertas},
            ORDEN, {str(x): {"sale": LUISMI}}, {"pujas": {x: 2_000_000}})
    assert aparte["caja"] == SALDO - 5_000_000 + OFERTA_LUISMI, aparte["caja"]


def test_t9_el_cierre_cuenta_el_cobro_del_aplazado() -> None:
    with _entorno():
        apagado = _cierre_decidir()
        assert apagado["caja"] == -1_532_017 and apagado["deficit"] == 1_532_017, apagado
        assert ("ACEPTAR_OFERTA_DEL_COMPUTER", 12, None) in _tipos(apagado["acciones"])
        d = _cierre_decidir(credito=OFERTA_LUISMI)
        assert d["caja"] == -1_532_017 and d["caja_tras_cancelar"] == -1_532_017, d
        assert d["deficit"] == 0 and d["credito_del_aplazado"] == OFERTA_LUISMI, d
        assert d["motivo"] == "EN_POSITIVO_CON_EL_COBRO_DEL_APLAZADO", d["motivo"]
        assert not [a for a in d["acciones"] if a["accion"] in (
            "CANCELAR_PUJA", "ACEPTAR_OFERTA_DEL_COMPUTER")], d["acciones"]
        assert _tipos(d["acciones"]) == [("PONER_A_LA_VENTA", 12, None)], d["acciones"]
        # La adopcion sigue mirando la caja sin el credito.
        assert d["adoptar"] == [] and [x["player_id"] for x in d["no_adoptados"]] == [5]
        # La puja especulativa de la ronda no se retira si el cobro la cubre.
        dos = {KUBO: {"offer_id": 801, "amount": 3_000_000},
               700: {"offer_id": 802, "amount": 300_000}}
        d = _cierre_decidir(credito=OFERTA_LUISMI, pujas=dos, especulativas={5, 700})
        assert d["cancelar"] == [] and d["deficit"] == 0, d
        apagado = _cierre_decidir(pujas=dos, especulativas={5, 700})
        assert apagado["cancelar"] == [700], apagado
        # Un credito que no llega: retira y vende lo que falta, como siempre.
        d = _cierre_decidir(credito=1_000_000)
        assert d["deficit"] == 532_017 and d["motivo"] == "EN_ROJO_SE_VENDE", d
    # De punta a punta: el mismo credito que dejo pujar a la orden.
    puestos = {CIERRE_ENV: "1", ORDEN_ENV: "1", EL_APLAZADO: "1"}
    s, escritor = _cierre_correr(puestos=puestos)
    d = s["decision"]
    assert d["credito_del_aplazado"] == OFERTA_LUISMI and d["deficit"] == 0, d
    assert d["caja"] == -1_532_017 and s["motivo"] == "EN_POSITIVO_CON_EL_COBRO_DEL_APLAZADO"
    assert escritor.llamadas == [("PUBLICAR", 12, 2_000_000)], escritor.llamadas
    assert s["plan"]["credito_del_aplazado"] == OFERTA_LUISMI and s["plan"]["caja"] == -1_532_017
    assert any("aplazado" in linea for linea in cierre_mod.el_parte(s))
    apagado, escritor = _cierre_correr()
    assert apagado["decision"]["deficit"] == 1_532_017 and escritor.llamadas == [
        ("ACEPTAR", 903)], apagado["decision"]
    assert "credito_del_aplazado" not in apagado["plan"]
    # La oferta de Luismi muere en el reset: no hay credito.
    s, _ = _cierre_correr(puestos=puestos, hasta=HASTA_DEL_19)
    assert "credito_del_aplazado" not in s["decision"] and s["decision"]["deficit"] == 1_532_017


def test_t11_dos_aplazados_seguidos() -> None:
    ray_get = _p(8, "Rayo Vallecano", "Getafe CF", "2026-10-22T20:00:00+02:00")
    cal = {"matchdays": [{"matchday": 6, "matches": [LEV_ATH]},
                         {"matchday": 8, "matches": [ray_get]},
                         {"matchday": 10, "matches": J10}]}
    jueves = datetime(2026, 10, 22, 18, 0, tzinfo=UTC)
    c = pj.el_proximo_cierre(datetime(2026, 10, 20, 20, 0, tzinfo=UTC), cal)
    assert c["inicio"] == INICIO_J6 and c["parcial"] and c["resuelve_antes"], c
    assert c["horas_principal"] == 71.0, c
    c = pj.el_proximo_cierre(datetime(2026, 10, 21, 19, 0, tzinfo=UTC), cal)
    assert c["inicio"] == jueves and c["parcial"] and c["resuelve_antes"], c
    assert c["horas_principal"] == 48.0 and c["horas"] == 23.0, c
    jueves_06 = datetime(2026, 10, 22, 6, 0, tzinfo=UTC)
    c = pj.el_proximo_cierre(jueves_06, cal)
    assert c["inicio"] == jueves and c["resuelve_antes"] is False, c
    with _entorno():
        # El martes, medido hasta el miercoles: la oferta de Luismi lo paga.
        martes = datetime(2026, 10, 20, 20, 0, tzinfo=UTC)
        aparte = orden_mod.el_aplazado(martes, cal, _la_foto(), YO)
        a = _orden_decidir(ahora=martes, horas_jornada=22.0, aparte=aparte)
        assert _tipos(a) == [("PUJAR", KUBO, "EL_APLAZADO")], a
        # El miercoles a las 21:00, medido hasta el jueves: esa oferta ya no
        # vive al empezar el Rayo-Getafe.
        miercoles = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)
        aparte = orden_mod.el_aplazado(miercoles, cal, _la_foto(), YO)
        assert aparte["inicio"] == jueves
        a = _orden_decidir(ahora=miercoles, horas_jornada=23.0, aparte=aparte)
        assert _tipos(a) == [("NADA", KUBO, "EL_APLAZADO")], a
        # El jueves a las 08:00 de Madrid, despues del ultimo reset: como hoy.
        aparte = orden_mod.el_aplazado(jueves_06, cal, _la_foto(), YO)
        kw = dict(ahora=jueves_06, horas_jornada=12.0)
        assert _orden_decidir(**kw, aparte=aparte) == _orden_decidir(**kw)


def test_t12_con_basura_ni_lanza_ni_relaja() -> None:
    vacio = {"horas": None, "inicio": None, "parcial": False, "horas_principal": None,
             "inicio_principal": None, "proximo_reset": None, "resuelve_antes": False}
    with tempfile.TemporaryDirectory() as tmp:
        no_hay = Path(tmp) / "no_hay.json"
        for basura in (no_hay, "x", 5, [1], {"matchdays": "x"},
                       {"matchdays": [None, {"matchday": 6, "matches": "x"}]}):
            c = pj.el_proximo_cierre(AHORA, basura)
            assert c["parcial"] is False and c["resuelve_antes"] is False and c["horas"] is None, c
            assert orden_mod.el_aplazado(AHORA, basura, _la_foto(), YO) is None
    assert pj.el_proximo_cierre("ayer", CAL) == vacio
    assert pj.el_proximo_cierre(AHORA, CAL, reset="x")["resuelve_antes"] is False
    assert pj.el_proximo_reset(None) is None and pj.el_proximo_reset("x") is None
    for basura in (None, "x", 5, [1], {"market": "x"},
                   {"market": {"offers": [None, 5, {"requestedPlayers": "x"}], "sales": [7]}}):
        with _entorno(**{ORDEN_ENV: "1"}):
            assert isinstance(orden_mod.las_caducidades(basura, YO), dict)
            assert orden_mod.las_parejas_de_la_orden(basura, AHORA) == {}
            assert orden_mod.lo_que_se_cobra_antes(basura, basura, basura, basura, basura) == 0
            assert orden_mod.cobrable(basura, basura, basura, basura, basura) == 0
            assert orden_mod.la_caja_del_aplazado(basura, basura, basura, basura, basura,
                                                  basura) is None
            assert orden_mod._pasa_el_aplazado(basura, KUBO, 1, basura, basura, basura,
                                               basura) is None
            publicado = orden_mod.el_aplazado_publicado(basura)
            assert (publicado is None) == (not isinstance(basura, dict)), publicado
            json.dumps(publicado)
            assert mejora_mod._el_aplazado_de_la_mejora(basura) is None
            # (Con `aparte` dado: sin el, leeria el calendario de produccion.)
            r = mejora_mod.el_aplazado_de_la_vuelta({"aparte": basura}, AHORA, basura, YO,
                                                    basura, basura, basura, basura)
            assert r is None or mejora_mod._el_aplazado_de_la_mejora(r) is None, r
            r = mejora_mod.el_aplazado_de_la_vuelta({"aparte": _aparte()}, AHORA, basura, YO,
                                                    basura, basura, basura, basura)
            assert r is None or mejora_mod._el_aplazado_de_la_mejora(r) is None, r
            # Con las horas dadas y sin `aparte`: None, sin leer produccion.
            assert mejora_mod.el_aplazado_de_la_vuelta({"horas_jornada": 20.0}, AHORA, basura,
                                                       YO, basura, basura, basura,
                                                       basura) is None
        with _entorno(**{EL_APLAZADO: "1"}):
            assert cierre_mod.el_credito_del_aplazado(AHORA, CAL, basura, YO, basura, basura,
                                                      basura, basura, basura) == 0
    # Ofertas sin `until` ni `created`: no cuentan.
    foto = _la_foto(ofertas={LUISMI: (901, OFERTA_LUISMI, None)})
    aparte = orden_mod.el_aplazado(AHORA, CAL, foto, YO)
    assert aparte["caducidades"][LUISMI]["oferta"] is None
    with _entorno():
        assert _tipos(_orden_decidir(aparte=aparte)) == [("NADA", KUBO, "EL_APLAZADO")]
        # Sin saldo: el reloj de siempre.
        assert _orden_decidir(saldo=None, aparte=_aparte()) == _orden_decidir(saldo=None)
        # Un `aparte` a medias o basura: el reloj de siempre.
        for malo in ("x", 5, {"resuelve_antes": True}, _aparte(horas_principal=float("nan")),
                     _aparte(horas_principal="x"), _aparte(inicio="x"), _aparte(caducidades="x")):
            assert _tipos(_orden_decidir(aparte=malo)) in (
                [("NADA", KUBO, "EL_RELOJ")], [("NADA", KUBO, "EL_APLAZADO")]), malo
        for malo in ("x", 5, {"resuelve_antes": True}, _aparte(horas_principal=float("inf"))):
            assert _orden_decidir(aparte=malo) == _orden_decidir(), malo
            assert _mejora_decidir(aparte=malo) == _mejora_decidir(), malo
        # El credito del cierre con basura es 0.
        for malo in ("x", None, -5, object()):
            assert _cierre_decidir(credito=malo) == _cierre_decidir(), malo
    # `correr` encendido con una foto sin ofertas: no lanza.
    with _entorno(**{ORDEN_ENV: "1", EL_APLAZADO: "1"}):
        foto = _la_foto()
        foto["market"].pop("offers")
        s, _ = _orden_correr(snapshot=foto)
        assert not str(s["motivo"]).startswith("ERROR"), s
        assert _tipos(s["acciones"]) == [("NADA", KUBO, "EL_APLAZADO")], s


TESTS = [
    test_t13_nace_apagado,
    test_t3_apagado_es_byte_a_byte_lo_de_antes,
    test_el_proximo_cierre_en_el_calendario_de_produccion,
    test_el_proximo_reset_es_el_de_la_rotacion,
    test_t10_que_es_un_aplazado,
    test_las_caducidades,
    test_t1_kubo_por_luismi,
    test_t1_correr_de_punta_a_punta,
    test_t1b_la_vuelta_siguiente_cobra,
    test_t2_la_oferta_que_muere_en_el_reset,
    test_t2_la_mejora_no_elige_el_cambio_que_no_se_paga,
    test_t2_la_mejora_correr,
    test_t4_el_aplazado_sin_ventana_propia,
    test_t5_la_ronda_entera_como_hoy,
    test_t6_tras_el_ultimo_reset,
    test_t7_un_cambio_no_paga_otra_puja,
    test_t8_cada_oferta_cuenta_una_vez,
    test_t9_el_cierre_cuenta_el_cobro_del_aplazado,
    test_t11_dos_aplazados_seguidos,
    test_t12_con_basura_ni_lanza_ni_relaja,
]


def main() -> None:
    if "--grabar" in sys.argv:
        print(json.dumps(_las_huellas(), indent=4))
        return
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
