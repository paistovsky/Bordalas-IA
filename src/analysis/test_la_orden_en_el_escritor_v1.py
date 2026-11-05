"""
LA ORDEN EN EL ESCRITOR (05/11/2026). Guardias de
`BORDALAS_LA_ORDEN_EN_EL_ESCRITOR` (`src/analysis/la_orden_en_el_escritor.py`,
sus dos enganches en el escritor, `accept_offer` y `counter_offer`, y las
respuestas honestas del motor viejo y de Competitive V2).

EL HUECO (mapa del 05/11 por la manana)

    Todas las aceptaciones y contraofertas salen por `accept_offer` y
    `counter_offer`, que solo reciben el `offer_id` y no miran la orden del
    gestor. Competitive V2 contesta las ofertas de managers, V10 sube
    contraofertas vivas y el motor viejo acepta la fila de un jugador de una
    oferta que pide a varios: ninguno sabe, en la escritura, a quien vende.

QUE SE COMPRUEBA

    1. Nace apagado, se lee en UN sitio (`activo`, al llamarse), vale lo
       mismo que `el_paso_0.ENCENDIDO`, tiene frase en QUE_HACE, no hace
       nada al importarse y solo lo nombran sus ficheros.
    2. Apagado es main byte a byte: la huella de la bateria (el escritor
       real sin red, aceptar y contraofertar, en seco y de verdad, con y
       sin ensayo, doce ofertas, dos respuestas de Biwenger, el mercado que
       se lee y el que revienta, siete ordenes; y los llamadores: el motor
       viejo, su cluster, Competitive V2 y la orden), con el interruptor
       sin poner, "0", "", "no" y "off", sin interruptores y con los 27 de
       produccion. Medida en main antes de tocar el codigo, una por
       version de Python (3.11 y 3.13).
    3. Apagado, ni red ni orden: una PUT o POST, cero GET, cero lecturas
       de `protegidos()`/`conservados()`, con la orden encendida y Boye en
       `proteger` (caracterizacion: pasa en main).
    4. Encendido: Boye y Yamal (proteger) no se aceptan ni se
       contraofertan; Roberto (conservar) no se contraoferta ni se acepta
       de un manager, pero SI del Computer (la venta de la mejora, de la
       orden, del cierre y de la rotacion). Una oferta por varios se mira
       entera. Un jugador libre, como main.
    5. Sin ver la oferta (el GET revienta, el mercado no se lee, la oferta
       no esta): se escribe como siempre, con `guardia_sin_ver`.
    6. En seco ni se mira; el ensayo no apunta la frenada y si la que pasa.
    7. Con la orden apagada, caducada, rota o sin orden: no se frena nada
       (ni GET). El lunes (Boye fuera de `proteger`): su oferta del
       Computer pasa, la de un manager no. Yamal con su llave: pasa.
    8. Una peticion mas, y solo una: un GET `/market` por escritura.
    9. Los llamadores, con el escritor real: el motor viejo (la fila de
       Iglesias de una oferta que pide tambien a Roberto) y su cluster
       devuelven BLOCKED_PROTECTED_PLAYER con `write_performed` False y sin
       rastro; Competitive V2, COMPETITIVE_BLOCKED_EL_ESCRITOR; V10,
       `write_used` False; la orden, `enviada` False y sus mismas claves.
   10. Las fuentes: la guarda va antes del ensayo, el resto del escritor y
       `la_orden_del_gestor.ejecutar` son los de main.
   11. Nunca lanza; si la pieza no se pudiera importar, lo de siempre; el
       entorno no la decide (doctrina 104).

DE DONDE SALEN LOS NUMEROS

    La orden de `config/la_orden_del_gestor.json` del 05/11, recortada y
    copiada a mano (Yamal 26271 y Boye 12494 en `proteger`; Roberto 35678,
    Ivan 12403, Boye y Gulacsi 38433 en `conservar`), con la caducidad
    lejos para no depender del reloj. Las ofertas del Computer, de la vuelta
    de las 11:07 del 05/11 (Boye 5.316.300, Roberto 7.001.600, Iglesias
    3.823.100); las de managers son de la prueba (hoy no hay ninguna). Ni
    `config/`, ni el directorio de estado, ni la red: la orden va a una
    carpeta temporal (`la_orden_del_gestor.RUTA`), el mercado y la sesion
    son de mentira y el escritor es el real, sin login.

COMO SE USA

    python -m src.analysis.test_la_orden_en_el_escritor_v1
    python -m src.analysis.test_la_orden_en_el_escritor_v1 --medir
    python -m src.analysis.test_la_orden_en_el_escritor_v1 --volcar FICHERO
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import sys
import tempfile

from datetime import date, datetime
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


ENV = "BORDALAS_LA_ORDEN_EN_EL_ESCRITOR"

# Los de la orden y el ensayo, de sus modulos (sin escribir su nombre aqui).
from src.actions.la_orden_del_gestor import ENV as ENV_ORDEN  # noqa: E402
from src.biwenger.write_client import ENSAYO_ENV  # noqa: E402

# Los `BORDALAS_*` que no son del bot sino de la verja (el vigilante del
# directorio de estado): no se tocan.
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


class _Sustituye:
    """Cambia atributos de modulos SOLO dentro del `with` y los deja como
    estaban al salir (aunque algo reviente dentro)."""

    def __init__(self, cambios):
        self.cambios = list(cambios)

    def __enter__(self):
        self.antes = [(objeto, nombre, getattr(objeto, nombre))
                      for objeto, nombre, _ in self.cambios]
        for objeto, nombre, valor in self.cambios:
            setattr(objeto, nombre, valor)
        return self

    def __exit__(self, *_):
        for objeto, nombre, valor in reversed(self.antes):
            setattr(objeto, nombre, valor)
        return False


# ============================================================
# LOS JUGADORES, LA ORDEN Y EL MERCADO
# ============================================================

YO = 14175949
RIVAL = 13000002
BOYE, YAMAL, ROBERTO, IVAN, GULACSI = 12494, 26271, 35678, 12403, 38433
IGLESIAS, DANI = 23840, 41418

ORDEN_HOY = {
    "escrita": "2026-11-05T08:22:00+01:00",
    # Lejos: la prueba no depende del reloj (la de verdad caduca el 30/11).
    "caduca": "2099-12-31T23:59:00+01:00",
    "fichar": [],
    "no_pujar": [{"player_id": 1721, "nombre": "Manu Sánchez"}],
    "no_rotar": [{"player_id": ROBERTO, "nombre": "Roberto Fernández"}],
    "vender_si_ficha": {"jugadores": []},
    "proteger": [{"player_id": YAMAL, "nombre": "Yamal"},
                 {"player_id": BOYE, "nombre": "Boyé"}],
    "conservar": [{"player_id": ROBERTO, "nombre": "Roberto Fernández"},
                  {"player_id": IVAN, "nombre": "Iván Martín"},
                  {"player_id": BOYE, "nombre": "Boyé"},
                  {"player_id": GULACSI, "nombre": "Gulácsi"}],
}
# El lunes 09/11: Boye sale de `proteger` y sigue en `conservar`.
ORDEN_LUNES = {**ORDEN_HOY, "proteger": [{"player_id": YAMAL, "nombre": "Yamal"}]}
# La llave de Yamal: el gestor lo quita de `proteger`.
ORDEN_YAMAL_POR_LESION = {
    **ORDEN_HOY,
    "proteger": [{"player_id": BOYE, "nombre": "Boyé"}],
    "yamal_por_lesion": {"motivo": "rotura de prueba", "baja_estimada_dias": 42},
}
ORDEN_CADUCADA = {**ORDEN_HOY, "caduca": "2026-11-03T23:59:00+01:00"}

# (nombre, orden, interruptor de la orden encendido). None: no hay fichero.
ORDENES = (
    ("hoy", ORDEN_HOY, True),
    ("lunes", ORDEN_LUNES, True),
    ("yamal_por_lesion", ORDEN_YAMAL_POR_LESION, True),
    ("caducada", ORDEN_CADUCADA, True),
    ("rota", '{"caduca": "2099-12-31T23:59:00+01:00", "proteger": [', True),
    ("sin_orden", None, True),
    ("apagada", ORDEN_HOY, False),
)


def _oferta(oid, pedidos, *, de=None, importe=1_000_000, campo="requestedPlayers"):
    """Una oferta recibida como la da `/market` (`offers`). `de` None: el
    Computer; un id: un manager."""
    o = {"id": oid, "type": "purchase", "status": "waiting", "amount": importe,
         "from": None if de is None else {"id": de, "name": "Un rival de la liga"},
         "to": {"id": YO, "name": "Pepe Bordalás"}}
    o[campo] = pedidos
    return o


OFERTAS = {
    "boye_del_computer": _oferta(91001, [BOYE], importe=5_316_300),
    "yamal_del_computer": _oferta(91002, [YAMAL], importe=38_000_000),
    "roberto_de_un_manager": _oferta(91003, [ROBERTO], de=RIVAL, importe=8_400_000),
    "roberto_del_computer": _oferta(91004, [ROBERTO], importe=7_001_600),
    "lote_iglesias_ivan": _oferta(91005, [{"id": IGLESIAS}, {"id": IVAN}], de=RIVAL,
                                  importe=6_900_000),
    "iglesias_de_un_manager": _oferta(91006, [{"id": IGLESIAS}], de=RIVAL, importe=4_500_000),
    "iglesias_del_computer": _oferta(91007, [IGLESIAS], importe=3_823_100),
    "lote_iglesias_roberto": _oferta(91008, [{"id": IGLESIAS}, {"id": ROBERTO}], de=RIVAL,
                                     importe=12_500_000),
    "boye_de_un_manager": _oferta(91009, [BOYE], de=RIVAL, importe=5_600_000),
    "boye_en_player": _oferta(91010, {"id": BOYE}, campo="player", importe=5_316_300),
    "dani_del_computer": _oferta(91011, [DANI], importe=2_089_300),
}
# Una puja nuestra por otro (sale en `offers` con `from` nuestro): ruido.
NUESTRA_PUJA = {"id": 91012, "type": "purchase", "status": "waiting", "amount": 900_000,
                "from": {"id": YO}, "to": None, "requestedPlayers": [1721]}
NO_ESTA = 99999

MERCADO = {
    "status": {"balance": 2_275_724, "maximumBid": 17_363_224},
    "sales": [],
    "offers": list(OFERTAS.values()) + [NUESTRA_PUJA],
}


def _id(nombre) -> int:
    return NO_ESTA if nombre == "no_esta" else OFERTAS[nombre]["id"]


def _importe(nombre) -> int:
    return 1_000_000 if nombre == "no_esta" else OFERTAS[nombre]["amount"]


class _Revienta:
    """El mercado que no se puede leer: `get_market` lanza esto."""

    def __init__(self, error):
        self.error = error


MERCADOS = (("normal", MERCADO), ("revienta", _Revienta(RuntimeError("Biwenger no contesta"))))

RESPUESTAS = (
    ("200", 200, {"status": 200, "data": {"id": 777}}),
    ("400", 400, {"status": 400, "message": "La oferta ya no existe"}),
)


class _Respuesta:
    def __init__(self, status, cuerpo):
        self.status_code, self._cuerpo = status, cuerpo
        self.text = "" if cuerpo is None else json.dumps(cuerpo)

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin cuerpo")
        return copy.deepcopy(self._cuerpo)


def _fabrica(red, respuesta=RESPUESTAS[0], mercado=MERCADO):
    """El `BiwengerWriteClient` de verdad, sin login, con un cliente y una
    sesion de mentira: todo lo que iria a Biwenger se apunta en `red`."""
    from src.biwenger.write_client import BiwengerWriteClient

    _, status, cuerpo = respuesta

    class _Sesion:
        def put(self, url, json=None, timeout=None):
            red.append({"metodo": "PUT", "url": url, "json": json, "timeout": timeout})
            return _Respuesta(status, cuerpo)

        def post(self, url, json=None, timeout=None):
            red.append({"metodo": "POST", "url": url, "json": json, "timeout": timeout})
            return _Respuesta(status, cuerpo)

        def delete(self, url, timeout=None):
            red.append({"metodo": "DELETE", "url": url, "timeout": timeout})
            return _Respuesta(status, cuerpo)

        def get(self, url, *a, **k):
            red.append({"metodo": "GET_DE_LA_SESION", "url": url})
            return _Respuesta(200, {"status": 200, "data": copy.deepcopy(mercado)})

    class _Cliente:
        BASE_URL = "https://biwenger.invalid/api/v2"

        def __init__(self):
            self.session = _Sesion()

        def get_market(self):
            red.append({"metodo": "GET", "url": f"{self.BASE_URL}/market"})
            if isinstance(mercado, _Revienta):
                raise mercado.error
            return copy.deepcopy(mercado)

    def crea():
        red.append({"metodo": "CREA_EL_ESCRITOR"})
        escritor = object.__new__(BiwengerWriteClient)
        escritor.client = _Cliente()
        escritor.version, escritor.league_id, escritor.user_id = "0", 2165477, YO
        return escritor

    return crea


def _la_orden_en(carpeta, nombre, orden) -> Path:
    """La orden escrita en `carpeta` (o una ruta que no existe)."""
    ruta = Path(carpeta) / f"orden_{nombre}.json"
    if orden is not None and not ruta.exists():
        texto = orden if isinstance(orden, str) else json.dumps(orden, ensure_ascii=False)
        ruta.write_text(texto, encoding="utf-8")
    return ruta


def _la_orden(ruta, cuentas):
    """`la_orden_del_gestor.RUTA` a `ruta` y `protegidos`/`conservados` (las
    de verdad) contadas en `cuentas`."""
    import src.actions.la_orden_del_gestor as orden_mod

    def _cuenta(nombre, real):
        def contada(*a, **k):
            cuentas[nombre] = cuentas.get(nombre, 0) + 1
            return real(*a, **k)
        return contada

    return [(orden_mod, "RUTA", Path(ruta))] + [
        (orden_mod, n, _cuenta(n, getattr(orden_mod, n))) for n in ("protegidos", "conservados")]


def _sin_libros_ajenos(rastro):
    """Lo que el motor viejo lee y apunta fuera de la orden, de mentira: la
    cartera, la rotacion y el relevo (vacios) y el rastro (apuntado aqui)."""
    import src.actions.el_rastro as el_rastro
    import src.actions.la_mejora_del_once as mejora
    import src.actions.la_ronda_de_la_manana as ronda
    import src.actions.la_rotacion as rotacion

    def _apunta(familia, **k):
        rastro.append({"familia": familia, "resultado": copy.deepcopy(k.get("resultado")),
                       "extra": copy.deepcopy(k.get("extra"))})
        return {"anotada": False}

    vacio = (lambda *a, **k: frozenset())
    return [(el_rastro, "apuntar_escritura", _apunta), (ronda, "los_que_aguanta", vacio),
            (rotacion, "los_que_rota", vacio), (mejora, "los_que_entran", vacio)]


def _corre(hacer, *, ruta, orden_encendida=True, entorno=None, valor=None, ensayo=False,
           mercado=MERCADO, respuesta=RESPUESTAS[0], carpeta) -> dict:
    """Corre `hacer(fabrica)` con la orden de `ruta`, el interruptor a
    `valor` y el ensayo, y devuelve lo que devolvio, lo que fue a la red,
    lo que se apunto en el rastro y en el ensayo y cuantas veces se leyo la
    orden."""
    import src.biwenger.write_client as escritura

    red, rastro, cuentas = [], [], {}
    log = Path(carpeta) / "ensayo" / "escrituras_no_enviadas.jsonl"
    if log.exists():
        log.unlink()
    entorno = {**(entorno or {}), ENV_ORDEN: "1" if orden_encendida else None,
               ENSAYO_ENV: "1" if ensayo else None, ENV: valor}
    with _Interruptores(entorno), _Sustituye(
            _la_orden(ruta, cuentas) + _sin_libros_ajenos(rastro)
            + [(escritura, "ESCRITURAS_DEL_ENSAYO", str(log))]):
        try:
            r = hacer(_fabrica(red, respuesta, mercado))
        except Exception as error:                  # noqa: BLE001
            r = {"LANZA": f"{type(error).__name__}: {error}"}
    apuntadas = []
    if log.exists():
        for linea in log.read_text(encoding="utf-8").splitlines():
            fila = json.loads(linea)
            fila.pop("at", None)
            apuntadas.append(fila)
    return {"r": r, "red": red, "rastro": rastro, "cuentas": cuentas, "ensayo": apuntadas}


# ============================================================
# LAS LLAMADAS (las firmas de main)
# ============================================================

def _acepta(nombre, execute=True):
    def hacer(fabrica):
        return fabrica().accept_offer(offer_id=_id(nombre), execute=execute)
    return hacer


def _contraoferta(nombre, execute=True):
    def hacer(fabrica):
        return fabrica().counter_offer(offer_id=_id(nombre), amount=_importe(nombre) + 500_000,
                                       execute=execute)
    return hacer


FILAS_DEL_MOTOR_VIEJO = (
    # La fila de Iglesias de una oferta que pide tambien a Roberto: el
    # hueco de la oferta por varios.
    ("iglesias_en_lote_roberto", "lote_iglesias_roberto", IGLESIAS, "Juan Iglesias"),
    ("iglesias_del_computer", "iglesias_del_computer", IGLESIAS, "Juan Iglesias"),
    ("dani_del_computer", "dani_del_computer", DANI, "Dani Lorenzo"),
    ("boye_del_computer", "boye_del_computer", BOYE, "Boyé"),
    ("roberto_del_computer", "roberto_del_computer", ROBERTO, "Roberto Fernández"),
)


def _el_motor_viejo(oferta, pid, nombre_jugador, execute=True):
    """`execute_autopilot_decision` ACCEPT_RECOVERY_OFFER con la fila."""
    def hacer(fabrica):
        import src.actions.autopilot_executor as ae

        decision = {
            "action": "ACCEPT_RECOVERY_OFFER", "executable": True,
            "temporal_gate": {"phase": "PREPARATION", "operations_locked": False,
                              "hard_safety_mode": False},
            "data": {"offer": {"offer_id": _id(oferta), "player_id": pid,
                               "player_name": nombre_jugador, "amount": _importe(oferta),
                               "protection": "NORMAL"}},
        }
        with _Sustituye([(ae, "BiwengerWriteClient", fabrica)]):
            return ae.execute_autopilot_decision(decision, execute=execute)
    return hacer


FOTO_FRESCA = "snapshot_fresco_2026-11-05_11-07-00.json"


def _el_cluster(oferta, pid, nombre_jugador):
    """`execute_autopilot_decision` ACCEPT_CLUSTER_BEFORE_EXPIRY, con la foto
    fresca y el selector de mentira (elige la fila)."""
    def hacer(fabrica):
        import src.actions.autopilot_executor as ae

        seleccion = {"ready": True, "status": "READY", "selected": {
            "offer_id": _id(oferta), "player_id": pid, "player_name": nombre_jugador,
            "amount": _importe(oferta),
            "offer_decision": {"decision": "ACCEPT", "protection": "NORMAL"}}}
        decision = {
            "action": "ACCEPT_CLUSTER_BEFORE_EXPIRY", "executable": True,
            "temporal_gate": {"phase": "PREPARATION"},
            "data": {"cluster": {"offer_ids": [_id(oferta)]}},
        }
        with _Sustituye([
                (ae, "BiwengerWriteClient", fabrica),
                (ae, "refresh_snapshot_for_write_revalidation",
                 lambda: (FOTO_FRESCA, {"market": {"offers": []}})),
                (ae, "select_emergency_accept_offer", lambda **k: copy.deepcopy(seleccion))]):
            return ae.execute_autopilot_decision(decision, execute=True)
    return hacer


OFERTAS_DE_MANAGERS = ("roberto_de_un_manager", "boye_de_un_manager", "iglesias_de_un_manager",
                       "lote_iglesias_ivan", "lote_iglesias_roberto")
JUGADOR_DE = {"roberto_de_un_manager": ROBERTO, "boye_de_un_manager": BOYE,
              "iglesias_de_un_manager": IGLESIAS, "lote_iglesias_ivan": IGLESIAS,
              "lote_iglesias_roberto": IGLESIAS}


def _competitive(oferta, decision):
    """`execute_competitive_live_action` con la oferta elegida, la foto
    fresca y el tablero fresco de mentira (la misma decision)."""
    def hacer(fabrica):
        import src.analysis.competitive_live_executor as cle

        oid, importe, pid = _id(oferta), _importe(oferta), JUGADOR_DE[oferta]
        elegida = {"offer_id": oid, "amount": importe, "player_id": pid, "rival_user_id": RIVAL,
                   "authoritative_decision": decision,
                   "strategic_sell_price": importe - 100_000,
                   "authoritative_counter_amount": importe + 500_000}
        tablero = {"decisions": [{
            "counterparty_type": "MANAGER", "offer_id": oid, "player_id": pid,
            "amount": importe, "counterparty_id": RIVAL,
            "competitive_observer": {"decision": decision,
                                     "strategic_sell_price": importe - 100_000,
                                     "counter_amount": importe + 500_000}}]}
        with _Sustituye([
                (cle, "refresh_snapshot",
                 lambda: (FOTO_FRESCA, {"market": copy.deepcopy(MERCADO)})),
                (cle, "build_offer_decision_board", lambda **k: copy.deepcopy(tablero)),
                (cle, "BiwengerWriteClient", fabrica)]):
            return cle.execute_competitive_live_action(
                selected_offer=elegida, rival_intelligence={}, execute=True)
    return hacer


ACCIONES_DE_LA_ORDEN = (
    ("boye", ("boye_del_computer",)),
    ("roberto", ("roberto_del_computer",)),
    ("iglesias", ("iglesias_del_computer",)),
    ("lote_ivan_y_dani", ("lote_iglesias_ivan", "dani_del_computer")),
)


def _la_orden_ejecuta(nombres):
    """`la_orden_del_gestor.ejecutar` con ACEPTAR_OFERTA_DEL_COMPUTER."""
    def hacer(fabrica):
        from src.actions.la_orden_del_gestor import ejecutar

        acciones = [{"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "offer_id": _id(n),
                     "player_id": JUGADOR_DE.get(n) or OFERTAS[n]["requestedPlayers"][0],
                     "nombre": n} for n in nombres]
        return ejecutar(acciones, fabrica())
    return hacer


# ============================================================
# LA BATERIA Y SU HUELLA
# ============================================================

# Los 27 que enciende el YAML de produccion de origin/main b3286e86
# (.github/workflows/bordalas-live.yml), contados con
# `el_paso_0.interruptores_encendidos_en`.
PRODUCCION = {n: "1" for n in (
    "BORDALAS_COBRA_LA_RACHA", "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA", "BORDALAS_EL_CIERRE_DE_LA_JORNADA",
    "BORDALAS_EL_INFORME_DE_LA_MANANA", "BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE",
    "BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR",
    "BORDALAS_EL_ONCE_UNA_VEZ", "BORDALAS_EL_PARTE_VENDE", "BORDALAS_JORNADAS_POR_SU_FECHA",
    "BORDALAS_LA_CARTERA", "BORDALAS_LA_JORNADA_DE_CADA_PAGINA",
    "BORDALAS_LA_MEJORA_DEL_ONCE", "BORDALAS_LA_MEJORA_SOLO_SI_SUBE",
    "BORDALAS_LA_MONEDA_DE_LA_LIGA", ENV_ORDEN,
    "BORDALAS_LA_PUJA_EN_9900", "BORDALAS_LA_RONDA_DE_LA_MANANA", "BORDALAS_LA_ROTACION",
    "BORDALAS_LOS_CHOLLOS", "BORDALAS_REJA_CON_TOLERANCIA", "BORDALAS_REVENTA_SOLO_SI_JUEGA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL", "BORDALAS_REVISA_LAS_PUJAS_VIVAS",
    "BORDALAS_SIN_SUBASTA", "BORDALAS_SOLVENCIA_POR_SU_PLAZO", "BORDALAS_UN_SOLO_COLCHON",
)}
ENTORNOS = (("sin_interruptores", {}), ("produccion", PRODUCCION))

APAGADO = (None, "0", "", "no", "off")
ESCRITURAS = tuple(OFERTAS) + ("no_esta",)


def _la_bateria(carpeta) -> list:
    """[(nombre, {argumentos de `_corre` menos el entorno})]."""
    llamadas = []
    for nombre_orden, orden, encendida in ORDENES:
        ruta = _la_orden_en(carpeta, nombre_orden, orden)
        base = {"ruta": ruta, "orden_encendida": encendida}
        for ensayo in (False, True):
            for respuesta in RESPUESTAS:
                nombre_resp = respuesta[0]
                comun = {**base, "ensayo": ensayo, "respuesta": respuesta}
                sufijo = f"{nombre_resp}/ensayo={ensayo}/{nombre_orden}"
                for nombre_mercado, mercado in MERCADOS:
                    for oferta in ESCRITURAS:
                        for execute in (True, False):
                            llamadas.append((
                                f"acepta/{oferta}/{execute}/{nombre_mercado}/{sufijo}",
                                {**comun, "mercado": mercado, "hacer": _acepta(oferta, execute)}))
                            llamadas.append((
                                f"contra/{oferta}/{execute}/{nombre_mercado}/{sufijo}",
                                {**comun, "mercado": mercado,
                                 "hacer": _contraoferta(oferta, execute)}))
                for fila, oferta, pid, nombre in FILAS_DEL_MOTOR_VIEJO:
                    for execute in (True, False):
                        llamadas.append((f"motor_viejo/{fila}/{execute}/{sufijo}", {
                            **comun, "hacer": _el_motor_viejo(oferta, pid, nombre, execute)}))
                    llamadas.append((f"cluster/{fila}/{sufijo}", {
                        **comun, "hacer": _el_cluster(oferta, pid, nombre)}))
                for oferta in OFERTAS_DE_MANAGERS:
                    for decision in ("ACCEPT_NOW", "COUNTER_OFFER"):
                        llamadas.append((f"competitive/{oferta}/{decision}/{sufijo}", {
                            **comun, "hacer": _competitive(oferta, decision)}))
                for nombre_acciones, nombres in ACCIONES_DE_LA_ORDEN:
                    llamadas.append((f"la_orden/{nombre_acciones}/{sufijo}", {
                        **comun, "hacer": _la_orden_ejecuta(nombres)}))
    return llamadas


LLAMADAS_DE_LA_BATERIA = len(ORDENES) * 2 * len(RESPUESTAS) * (
    len(MERCADOS) * len(ESCRITURAS) * 2 * 2
    + len(FILAS_DEL_MOTOR_VIEJO) * 3
    + len(OFERTAS_DE_MANAGERS) * 2
    + len(ACCIONES_DE_LA_ORDEN))


def _normal(x):
    """Para la huella: conjuntos ordenados, fechas en ISO, nada al azar."""
    if isinstance(x, dict):
        return {str(k): _normal(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_normal(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted((_normal(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True,
                                                                         default=str))
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    return x


def _texto(x) -> str:
    """Con el orden de las claves tal cual (la huella mira tambien el orden
    de las claves que devuelve el escritor)."""
    return json.dumps(_normal(x), ensure_ascii=False, default=str)


def _huellas(valores=APAGADO) -> dict:
    """{entorno/valor del interruptor: {llamada: sha256}}. El entorno se
    deja como estaba."""
    salida = {}
    with tempfile.TemporaryDirectory() as carpeta:
        bateria = _la_bateria(carpeta)
        for nombre_del_entorno, entorno in ENTORNOS:
            for valor in valores:
                huellas = {}
                for nombre, argumentos in bateria:
                    hecho = _corre(**argumentos, entorno=entorno, valor=valor, carpeta=carpeta)
                    huellas[nombre] = hashlib.sha256(
                        _texto(hecho).encode("utf-8")).hexdigest()
                salida[f"{nombre_del_entorno}/{valor!r}"] = huellas
    return salida


def _la_huella(huellas: dict) -> str:
    """Una huella de todas: sha256 de las de cada llamada, en orden."""
    texto = "\n".join(f"{k} {v}" for k, v in sorted(huellas.items()))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# Medidas en main sin tocar (copia de origin/main b3286e86 por `git
# archive`, con este fichero dentro) con `python -m
# src.analysis.test_la_orden_en_el_escritor_v1 --medir`, una por Python y
# por entorno (sin interruptores y los 27 de produccion), con el
# interruptor sin poner, "0", "", "no" y "off" (las cinco, la misma).
# Cualquier cambio querido en el escritor, el motor viejo, Competitive V2 o
# la orden la pone roja: se vuelve a medir en main, a proposito, en las dos
# versiones (3.11 y 3.13; con otra no hay huella y la prueba falla).
HUELLAS_DE_MAIN = {
    (3, 11): {
        "produccion": "da3c48932de56c95986296ff6188d68e30c50ba615654771c97a1b11c807699d",
        "sin_interruptores": "da3c48932de56c95986296ff6188d68e30c50ba615654771c97a1b11c807699d",
    },
    (3, 13): {
        "produccion": "da3c48932de56c95986296ff6188d68e30c50ba615654771c97a1b11c807699d",
        "sin_interruptores": "da3c48932de56c95986296ff6188d68e30c50ba615654771c97a1b11c807699d",
    },
}


# ============================================================
# LAS FUENTES DE MAIN
# ============================================================

def _fuentes(ruta, clase=None, nombres=None, sin=()) -> dict:
    """{nombre: sha256 del texto} de las funciones de `ruta` (de `clase`
    si se da), las de `nombres` o todas menos `sin`. El texto, no el AST:
    no cambia entre versiones de Python."""
    texto = Path(ruta).read_text(encoding="utf-8")
    arbol = ast.parse(texto)
    cuerpo = arbol.body
    if clase:
        cuerpo = next(n for n in arbol.body if isinstance(n, ast.ClassDef)
                      and n.name == clase).body
    salida = {}
    for nodo in cuerpo:
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if (nombres and nodo.name not in nombres) or nodo.name in sin:
            continue
        segmento = ast.get_source_segment(texto, nodo)
        salida[nodo.name] = hashlib.sha256(segmento.encode("utf-8")).hexdigest()
    return salida


def _las_fuentes() -> dict:
    escritor = RAIZ / "src" / "biwenger" / "write_client.py"
    orden = RAIZ / "src" / "actions" / "la_orden_del_gestor.py"
    return {
        "el_resto_del_escritor": _fuentes(escritor, "BiwengerWriteClient",
                                          sin=("accept_offer", "counter_offer")),
        "el_modulo_del_escritor": _fuentes(escritor),
        "la_orden_ejecutar": _fuentes(orden, nombres=("ejecutar",)),
    }


def _huella_de(fuentes: dict) -> str:
    return hashlib.sha256(json.dumps(fuentes, sort_keys=True).encode("utf-8")).hexdigest()


# Medida en main (b3286e86) con `--medir`: las demas funciones del
# escritor (publicar, retirar, rechazar, pujar, el once, la racha, los
# `build_*`, el ensayo...), las de modulo de `write_client` y
# `la_orden_del_gestor.ejecutar`. El texto, igual en todas las versiones.
FUENTES_DE_MAIN = "ee8208bf444de8208a8a294830f802eb6a25853e0424f304b143aeb907c33757"


def medir() -> None:
    """La huella de la bateria, apagada, para `HUELLAS_DE_MAIN`, y la de las
    fuentes para `FUENTES_DE_MAIN`."""
    todas = _huellas(APAGADO)
    por_entorno = {}
    for clave, huellas in todas.items():
        entorno = clave.split("/")[0]
        por_entorno.setdefault(entorno, set()).add(_la_huella(huellas))
    for entorno, huellas in sorted(por_entorno.items()):
        assert len(huellas) == 1, f"apagada depende de como se apague ({entorno})"
    n = {len(h) for h in todas.values()}
    print(f"Python {sys.version_info[:2]}: {n} llamadas (esperadas {LLAMADAS_DE_LA_BATERIA})"
          f" x {len(todas)} entornos y valores")
    for entorno, huellas in sorted(por_entorno.items()):
        print(f"  {entorno}: {next(iter(huellas))}")
    print(f"  fuentes: {_huella_de(_las_fuentes())}")


def volcar(ruta) -> None:
    """Las huellas de cada llamada, apagada, a `ruta` (JSON), para comparar
    main y la rama llamada a llamada."""
    todas = _huellas(APAGADO)
    Path(ruta).write_text(json.dumps({"python": list(sys.version_info[:2]), "huellas": todas,
                                      "fuentes": _las_fuentes()},
                                     indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Python {sys.version_info[:2]}: {sum(len(h) for h in todas.values())} "
          f"salidas en {ruta}")


# ============================================================
# LAS PRUEBAS
# ============================================================

ENCENDIDO = {ENV: "1"}


def _escrituras(red) -> list:
    """Lo que de verdad se pidio a Biwenger: (metodo, url), sin crear el
    escritor."""
    return [(e["metodo"], e["url"]) for e in red if e["metodo"] != "CREA_EL_ESCRITOR"]


def _con(carpeta, nombre_orden="hoy", **k) -> dict:
    """`_corre` con la orden `nombre_orden` de `ORDENES`."""
    orden, encendida = next((o, e) for n, o, e in ORDENES if n == nombre_orden)
    ruta = _la_orden_en(carpeta, nombre_orden, orden)
    k.setdefault("orden_encendida", encendida)
    return _corre(ruta=ruta, carpeta=carpeta, **k)


URL = "https://biwenger.invalid/api/v2"


def _la_de_main(operacion, nombre, execute=True, respuesta=RESPUESTAS[0]) -> dict:
    """La respuesta que da main, escrita a mano: el `build_*` y lo de
    siempre detras."""
    oid = _id(nombre)
    if operacion == "acepta":
        request = {"operation": "ACCEPT_OFFER", "method": "PUT", "url": f"{URL}/offers/{oid}"}
        cola = {"json": {"status": "accepted"}, "offer_id": oid, "execute": False}
    else:
        importe = _importe(nombre) + 500_000
        request = {"operation": "COUNTER_OFFER", "method": "POST", "url": f"{URL}/offers"}
        cola = {"json": {"type": "counterOffer", "to": oid, "amount": importe},
                "offer_id": oid, "amount": importe, "execute": False}
    request["headers"] = {
        "Content-Type": "application/json", "Accept": "application/json, text/plain, */*",
        "X-Lang": "es", "X-Version": "0", "X-League": "2165477", "X-User": str(YO),
        "Authorization": "*** OCULTO ***"}
    request.update(cola)
    if not execute:
        return {**request, "sent": False, "success": True}
    _, status, cuerpo = respuesta
    ok = status == 200
    return {**request, "sent": True, "http_status": status, "response": cuerpo,
            "success": ok,
            "success_detail": "OK" if ok else f"HTTP {status}"}


# 1. NACE APAGADO, UN LECTOR, SU FRASE, NADA AL IMPORTARSE

def test_nace_apagado_un_lector_y_su_frase():
    from src.analysis import la_orden_en_el_escritor as pieza
    from src.telemetry.el_tablon import QUE_HACE

    assert pieza.ENV == ENV
    for valor in (None, "0", "", "no", "false", "2", "off", " 0 "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is False, repr(valor)
    for valor in ("1", "true", "si", "yes", " SI ", "on", "sí", "Sí", " ON "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is True, repr(valor)

    # Solo lo nombran sus ficheros (fuera de las pruebas): el modulo y la
    # frase del tablon.
    nombran = []
    for ruta in sorted(list((RAIZ / "src").rglob("*.py")) + list((RAIZ / "scripts").rglob("*.py"))):
        if ruta.name.startswith("test_"):
            continue
        if ENV in ruta.read_text(encoding="utf-8"):
            nombran.append(ruta.relative_to(RAIZ).as_posix())
    assert nombran == ["src/analysis/la_orden_en_el_escritor.py",
                       "src/telemetry/el_tablon.py"], nombran
    fuente = (RAIZ / "src" / "analysis" / "la_orden_en_el_escritor.py").read_text(
        encoding="utf-8")
    assert fuente.count(f'ENV = "{ENV}"') == 1
    assert fuente.count("os.environ.get(ENV") == 1
    assert fuente.count("activo()") - fuente.count("def activo()") == 1, \
        "activo() se llama solo en `guardar`"
    for ruta in (RAIZ / "src").rglob("*.py"):
        if ruta.name.startswith("test_") or ruta.name == "la_orden_en_el_escritor.py":
            continue
        texto = ruta.read_text(encoding="utf-8")
        if "la_orden_en_el_escritor" in texto:
            assert ".activo(" not in texto and "import activo" not in texto, ruta

    # Nada al importarse: ninguna sentencia de modulo llama al lector, mira
    # el entorno, lee la orden o sale a la red. Solo importa `os`.
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        if isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant):
            continue                                # el docstring
        texto = ast.dump(nodo)
        for prohibido in ("activo", "environ", "conservados", "protegidos", "get_market",
                          "guardar"):
            assert prohibido not in texto, ast.unparse(nodo)[:120]
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.ImportFrom):
            assert nodo.module == "__future__", ast.unparse(nodo)
        if isinstance(nodo, ast.Import):
            assert [a.name for a in nodo.names] == ["os"], ast.unparse(nodo)
    # Dentro, solo la orden: ni `requests`, ni el cliente, ni el escritor.
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.ImportFrom):
            assert nodo.module in ("__future__", "src.actions.la_orden_del_gestor"), nodo.module
        if isinstance(nodo, ast.Import):
            assert [a.name for a in nodo.names] == ["os"], ast.unparse(nodo)

    # El inventario de los interruptores lo ve leido al llamarse.
    from scripts.los_interruptores import lectores

    lee = lectores(RAIZ / "src" / "analysis" / "la_orden_en_el_escritor.py")
    assert lee.get(ENV) == "AL_LLAMARSE", lee.get(ENV)

    frase = str(QUE_HACE.get(ENV) or "")
    for trozo in ("Justo antes de enviar", "aceptar una oferta o contraofertar",
                  "todos los jugadores que pide", "proteger", "ni se acepta ni se contesta",
                  "conservar", "nunca se contraoferta", "otro manager",
                  "la del Computer sí", "no se envía nada",
                  "no puede leer la oferta", "no gasta la escritura de la vuelta",
                  "apagada o caducada, todo como siempre"):
        assert trozo in frase, (trozo, frase)


def test_lo_que_el_paso_0_da_por_encendido():
    """Lo que el paso 0, el tablon, el panel y el ensayo dan por encendido
    (`el_paso_0.ENCENDIDO`), la pieza lo lee encendido, y al reves."""
    from src.analysis import el_paso_0
    from src.analysis import la_orden_en_el_escritor as pieza

    assert pieza.ENCENDIDO == el_paso_0.ENCENDIDO
    for valor in ('"1"', "1", '"on"', "on", '"sí"', '"Sí"', '"si"', '"true"', "true",
                  '"yes"', "'1'", '"0"', '""', '"no"', '"off"', '"false"', '"2"',
                  '"1"   # un motivo'):
        yaml = f"    env:\n      {ENV}: {valor}\n"
        en_el_paso_0 = ENV in el_paso_0.interruptores_encendidos_en(yaml)
        limpio = el_paso_0._limpio(valor)
        with _Interruptores({ENV: limpio}):
            assert pieza.activo() is en_el_paso_0, (valor, limpio)


# 2. APAGADO ES MAIN BYTE A BYTE

def test_apagado_es_main_byte_a_byte():
    """La bateria, con el interruptor sin poner, "0", "", "no" y "off", sin
    interruptores y con los 27 de produccion: la huella de main, medida
    antes de tocar el codigo, en esta version de Python."""
    esperadas = HUELLAS_DE_MAIN.get(sys.version_info[:2])
    assert esperadas is not None, f"sin huella medida para Python {sys.version_info[:2]}"
    todas = _huellas(APAGADO)
    assert len(todas) == len(ENTORNOS) * len(APAGADO), sorted(todas)
    for clave, huellas in todas.items():
        entorno = clave.split("/")[0]
        assert len(huellas) == LLAMADAS_DE_LA_BATERIA, (clave, len(huellas))
        assert _la_huella(huellas) == esperadas[entorno], (
            f"apagado ya no es main en Python {sys.version_info[:2]} ({clave}): "
            f"{_la_huella(huellas)} (main: {esperadas[entorno]})")


# 3. APAGADO, NI RED NI ORDEN (caracterizacion: pasa en main)

def test_apagado_ni_red_ni_orden():
    """Con la orden encendida y Boye en `proteger`: apagado se acepta y se
    contraoferta su oferta como en main. Una PUT o una POST, cero GET, cero
    lecturas de la orden, la respuesta de main clave a clave."""
    with tempfile.TemporaryDirectory() as carpeta:
        for valor in (None, "0", "", "no"):
            for respuesta in RESPUESTAS:
                for operacion, hacer, metodo in (
                        ("acepta", _acepta, "PUT"), ("contra", _contraoferta, "POST")):
                    for nombre in ("boye_del_computer", "boye_de_un_manager",
                                   "roberto_de_un_manager", "lote_iglesias_ivan"):
                        h = _con(carpeta, valor=valor, respuesta=respuesta,
                                 hacer=hacer(nombre))
                        assert [e["metodo"] for e in h["red"]] == ["CREA_EL_ESCRITOR", metodo], h
                        assert h["cuentas"] == {}, h["cuentas"]
                        de_main = _la_de_main(operacion, nombre, respuesta=respuesta)
                        assert list(h["r"]) == list(de_main), (list(h["r"]), list(de_main))
                        assert h["r"] == de_main, (h["r"], de_main)
                        # En seco: la de main, sin red.
                        h = _con(carpeta, valor=valor, respuesta=respuesta,
                                 hacer=hacer(nombre, execute=False))
                        assert [e["metodo"] for e in h["red"]] == ["CREA_EL_ESCRITOR"], h
                        assert h["cuentas"] == {}, h["cuentas"]
                        assert h["r"] == _la_de_main(operacion, nombre, execute=False)
                        assert list(h["r"]) == list(_la_de_main(operacion, nombre,
                                                                execute=False))
            # Con el ensayo: se apunta como hoy y no sale nada.
            h = _con(carpeta, valor=valor, ensayo=True, hacer=_acepta("boye_del_computer"))
            assert [e["metodo"] for e in h["red"]] == ["CREA_EL_ESCRITOR"], h
            assert h["cuentas"] == {}
            assert h["r"] == _la_de_main("acepta", "boye_del_computer", execute=False)
            assert h["ensayo"] == [{"operation": "ACCEPT_OFFER", "method": "PUT",
                                    "url": f"{URL}/offers/91001",
                                    "json": {"status": "accepted"}}], h["ensayo"]


# 4. ENCENDIDO: PROTEGER

def _frenada(h, codigo, de_la_orden, pedidos, de_un_manager):
    """Que se freno y como lo dice el escritor."""
    r = h["r"]
    assert _escrituras(h["red"]) in ([], [("GET", f"{URL}/market")]), h["red"]
    assert all(e["metodo"] not in ("PUT", "POST", "DELETE") for e in h["red"]), \
        f"se envio: {h['red']}"
    assert r.get("sent") is False and r.get("success") is False, r
    assert r.get("blocked") == codigo, r
    assert r.get("status") == "BLOQUEADA_POR_LA_ORDEN", r
    assert r.get("guardia") == "LA_ORDEN_EN_EL_ESCRITOR", r
    assert r.get("de_la_orden") == de_la_orden, r
    assert r.get("pedidos") == pedidos, r
    assert r.get("de_un_manager") is de_un_manager, r
    assert "LA_ORDEN_EN_EL_ESCRITOR" in str(r.get("reason")), r
    assert "http_status" not in r and "response" not in r, r
    assert h["ensayo"] == [], h["ensayo"]


PROTEGIDO, CONSERVADO = "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR", "CONSERVADO_POR_LA_ORDEN_DEL_GESTOR"


def test_encendido_proteger_ni_se_acepta_ni_se_contraoferta():
    """Boye y Yamal (proteger): ni su oferta del Computer ni la de un
    manager, ni aceptar ni contraofertar. Tambien si la oferta lo pide por
    `player`."""
    with tempfile.TemporaryDirectory() as carpeta:
        for valor in ("1", "si", "on"):
            for nombre, pid, manager in (("boye_del_computer", BOYE, False),
                                         ("yamal_del_computer", YAMAL, False),
                                         ("boye_de_un_manager", BOYE, True),
                                         ("boye_en_player", BOYE, False)):
                for hacer in (_acepta, _contraoferta):
                    h = _con(carpeta, valor=valor, hacer=hacer(nombre))
                    _frenada(h, PROTEGIDO, [pid], [pid], manager)
                    # Y en el ensayo, ni se apunta.
                    h = _con(carpeta, valor=valor, ensayo=True, hacer=hacer(nombre))
                    _frenada(h, PROTEGIDO, [pid], [pid], manager)


# 5. ENCENDIDO: CONSERVAR

def test_encendido_conservar_solo_se_acepta_del_computer():
    """Roberto (conservar): la contraoferta, nunca; la oferta de un manager,
    no; la del Computer, SI (es la venta de la mejora, de la orden, del
    cierre y de la rotacion), con el exito que diga Biwenger."""
    with tempfile.TemporaryDirectory() as carpeta:
        h = _con(carpeta, valor="1", hacer=_contraoferta("roberto_de_un_manager"))
        _frenada(h, CONSERVADO, [ROBERTO], [ROBERTO], True)
        h = _con(carpeta, valor="1", hacer=_acepta("roberto_de_un_manager"))
        _frenada(h, CONSERVADO, [ROBERTO], [ROBERTO], True)
        h = _con(carpeta, valor="1", hacer=_contraoferta("roberto_del_computer"))
        _frenada(h, CONSERVADO, [ROBERTO], [ROBERTO], False)
        for respuesta in RESPUESTAS:
            h = _con(carpeta, valor="1", respuesta=respuesta,
                     hacer=_acepta("roberto_del_computer"))
            assert _escrituras(h["red"]) == [("GET", f"{URL}/market"),
                                             ("PUT", f"{URL}/offers/91004")], h["red"]
            assert h["r"] == _la_de_main("acepta", "roberto_del_computer",
                                         respuesta=respuesta), h["r"]
            assert h["r"]["success"] is (respuesta[1] == 200)


# 6. UNA OFERTA POR VARIOS; UN JUGADOR LIBRE, COMO MAIN

def test_una_oferta_por_varios_y_un_jugador_libre():
    """Un manager pide a Iglesias y a Ivan (conservar) en UNA oferta:
    aceptarla o contraofertarla vende a los dos. Frenada, con `de_la_orden`
    [Ivan]. Iglesias solo: como main (se envia)."""
    with tempfile.TemporaryDirectory() as carpeta:
        for hacer in (_acepta, _contraoferta):
            h = _con(carpeta, valor="1", hacer=hacer("lote_iglesias_ivan"))
            _frenada(h, CONSERVADO, [IVAN], sorted([IGLESIAS, IVAN]), True)
            h = _con(carpeta, valor="1", hacer=hacer("lote_iglesias_roberto"))
            _frenada(h, CONSERVADO, [ROBERTO], sorted([IGLESIAS, ROBERTO]), True)
        for operacion, hacer, metodo in (("acepta", _acepta, "PUT"),
                                         ("contra", _contraoferta, "POST")):
            for nombre in ("iglesias_de_un_manager", "iglesias_del_computer",
                           "dani_del_computer"):
                h = _con(carpeta, valor="1", hacer=hacer(nombre))
                assert [m for m, _ in _escrituras(h["red"])] == ["GET", metodo], h["red"]
                assert h["r"] == _la_de_main(operacion, nombre), h["r"]


# 7. LO QUE LEE DE LA OFERTA

def test_lo_que_lee_de_la_oferta():
    from src.analysis import la_orden_en_el_escritor as pieza

    mercado = {"offers": [
        None, 7, "x",
        {"id": 1, "from": None, "requestedPlayers": [BOYE, {"id": ROBERTO}]},
        {"id": "2", "from": {"id": RIVAL}, "requestedPlayers": [str(IVAN)],
         "player": {"id": DANI}},
        {"id": 3, "from": RIVAL, "player": IGLESIAS},
        {"id": 4, "from": {}, "requestedPlayers": [True, None, "no", {"id": None},
                                                   {"id": "x"}, [BOYE], -5, 0,
                                                   {"id": str(GULACSI)}]},
        {"id": 5, "requestedPlayers": "x", "player": "x"},
        {"id": -6, "from": None, "requestedPlayers": [BOYE]},
        {"id": True, "from": None, "requestedPlayers": [BOYE]},
        {"id": "siete", "from": None, "requestedPlayers": [BOYE]},
        {"id": None, "from": None, "requestedPlayers": [BOYE]},
        {"id": 8, "from": None, "requestedPlayers": [BOYE]},
        {"id": 8, "from": {"id": RIVAL}, "requestedPlayers": [IVAN]},
    ]}
    assert pieza.la_oferta(mercado, 1) == {"pedidos": {BOYE, ROBERTO}, "de_un_manager": False}
    # El id de la oferta, como numero: "2" es la 2. Ids como texto, tambien.
    assert pieza.la_oferta(mercado, 2) == {"pedidos": {IVAN, DANI}, "de_un_manager": True}
    assert pieza.la_oferta(mercado, "2") == {"pedidos": {IVAN, DANI}, "de_un_manager": True}
    assert pieza.la_oferta(mercado, 3) == {"pedidos": {IGLESIAS}, "de_un_manager": True}
    # Un `from` raro no es el Computer (el lado seguro, ver el modulo).
    assert pieza.la_oferta(mercado, 4) == {"pedidos": {GULACSI}, "de_un_manager": True}
    assert pieza.la_oferta(mercado, 5) == {"pedidos": set(), "de_un_manager": False}
    # Dos con el mismo id: se juntan.
    assert pieza.la_oferta(mercado, 8) == {"pedidos": {BOYE, IVAN}, "de_un_manager": True}
    # Ids de oferta que no son un id: no estan.
    for oid in (-6, 6, 0, None, True, False, "siete", "x", 1.5j, 99999, [1], {"id": 1}):
        assert pieza.la_oferta(mercado, oid) is None, oid
    for malo in (None, "x", 7, [], {}, {"offers": "x"}, {"offers": None}, {"offers": {}},
                 {"offers": [None]}):
        assert pieza.la_oferta(malo, 1) is None, malo

    # Lo que frena: puro, con la orden que se le pase.
    prot, cons = {BOYE, YAMAL}, {ROBERTO, IVAN, BOYE, GULACSI}
    computer = {"pedidos": {ROBERTO}, "de_un_manager": False}
    manager = {"pedidos": {ROBERTO}, "de_un_manager": True}
    assert pieza.lo_que_frena("ACCEPT_OFFER", computer, prot, cons) is None
    assert pieza.lo_que_frena("COUNTER_OFFER", computer, prot, cons) == {
        "blocked": CONSERVADO, "de_la_orden": [ROBERTO]}
    assert pieza.lo_que_frena("ACCEPT_OFFER", manager, prot, cons) == {
        "blocked": CONSERVADO, "de_la_orden": [ROBERTO]}
    mezcla = {"pedidos": {BOYE, ROBERTO, IGLESIAS}, "de_un_manager": True}
    assert pieza.lo_que_frena("ACCEPT_OFFER", mezcla, prot, cons) == {
        "blocked": PROTEGIDO, "de_la_orden": sorted([BOYE, ROBERTO])}
    del_computer = {"pedidos": {BOYE, ROBERTO}, "de_un_manager": False}
    assert pieza.lo_que_frena("ACCEPT_OFFER", del_computer, prot, cons) == {
        "blocked": PROTEGIDO, "de_la_orden": [BOYE]}
    libre = {"pedidos": {IGLESIAS, DANI}, "de_un_manager": True}
    for operacion in ("ACCEPT_OFFER", "COUNTER_OFFER"):
        assert pieza.lo_que_frena(operacion, libre, prot, cons) is None
        assert pieza.lo_que_frena(operacion, manager, set(), set()) is None
        assert pieza.lo_que_frena(operacion, {"pedidos": set()}, prot, cons) is None
    # Sin pasarle la orden, la de `la_orden_del_gestor` (sin argumentos).
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        cuentas = {}
        with _Interruptores({ENV_ORDEN: "1"}), _Sustituye(_la_orden(ruta, cuentas)):
            assert pieza.lo_que_frena("ACCEPT_OFFER", manager) == {
                "blocked": CONSERVADO, "de_la_orden": [ROBERTO]}
            assert pieza.lo_que_frena("ACCEPT_OFFER", computer) is None
        assert cuentas == {"protegidos": 2, "conservados": 2}, cuentas


# 8. SIN VER LA OFERTA, SE ESCRIBE COMO SIEMPRE

def test_sin_ver_la_oferta_se_escribe():
    """El GET revienta, el mercado no se lee o la oferta no esta: se envia
    como en main, con `guardia_sin_ver` al final. En el ensayo, igual (se
    apunta). Nunca lanza."""
    casos = (
        (_Revienta(RuntimeError("Biwenger no contesta")), "SIN_LEER_EL_MERCADO: RuntimeError"),
        (_Revienta(KeyError("data")), "SIN_LEER_EL_MERCADO: KeyError"),
        (None, "LA_OFERTA_NO_ESTA_EN_EL_MERCADO"),
        ("x", "LA_OFERTA_NO_ESTA_EN_EL_MERCADO"),
        ({"offers": "x"}, "LA_OFERTA_NO_ESTA_EN_EL_MERCADO"),
        ({"offers": [{**OFERTAS["boye_del_computer"], "id": None}]},
         "LA_OFERTA_NO_ESTA_EN_EL_MERCADO"),
        ({"offers": [OFERTAS["iglesias_del_computer"]]}, "LA_OFERTA_NO_ESTA_EN_EL_MERCADO"),
        ({"offers": [{"id": 91001, "from": None, "requestedPlayers": [None, "x"]}]},
         "LA_OFERTA_SIN_JUGADORES"),
    )
    with tempfile.TemporaryDirectory() as carpeta:
        for mercado, motivo in casos:
            for operacion, hacer, metodo in (("acepta", _acepta, "PUT"),
                                             ("contra", _contraoferta, "POST")):
                h = _con(carpeta, valor="1", mercado=mercado, hacer=hacer("boye_del_computer"))
                assert [m for m, _ in _escrituras(h["red"])] == ["GET", metodo], h["red"]
                de_main = _la_de_main(operacion, "boye_del_computer")
                assert h["r"] == {**de_main, "guardia_sin_ver": motivo}, h["r"]
                assert list(h["r"]) == list(de_main) + ["guardia_sin_ver"], list(h["r"])
                h = _con(carpeta, valor="1", ensayo=True, mercado=mercado,
                         hacer=hacer("boye_del_computer"))
                assert [m for m, _ in _escrituras(h["red"])] == ["GET"], h["red"]
                assert h["r"] == {**_la_de_main(operacion, "boye_del_computer", execute=False),
                                  "guardia_sin_ver": motivo}, h["r"]
                assert len(h["ensayo"]) == 1, h["ensayo"]
        # La oferta que no esta en el mercado bueno.
        h = _con(carpeta, valor="1", hacer=_acepta("no_esta"))
        assert h["r"]["guardia_sin_ver"] == "LA_OFERTA_NO_ESTA_EN_EL_MERCADO", h["r"]
        assert h["r"]["sent"] is True, h["r"]


# 9. EN SECO NI SE MIRA; EL ENSAYO

def test_en_seco_ni_se_mira_y_el_ensayo():
    """`execute=False` encendido: ni GET ni orden, la respuesta de main. El
    ensayo: la frenada no se apunta; la que pasa, si (como hoy)."""
    with tempfile.TemporaryDirectory() as carpeta:
        for operacion, hacer in (("acepta", _acepta), ("contra", _contraoferta)):
            for nombre in ESCRITURAS:
                h = _con(carpeta, valor="1", hacer=hacer(nombre, execute=False))
                assert [e["metodo"] for e in h["red"]] == ["CREA_EL_ESCRITOR"], h["red"]
                assert h["cuentas"] == {}, h["cuentas"]
                assert h["r"] == _la_de_main(operacion, nombre, execute=False)
                assert list(h["r"]) == list(_la_de_main(operacion, nombre, execute=False))
                assert h["ensayo"] == []
        h = _con(carpeta, valor="1", ensayo=True, hacer=_acepta("boye_del_computer"))
        _frenada(h, PROTEGIDO, [BOYE], [BOYE], False)
        h = _con(carpeta, valor="1", ensayo=True, hacer=_acepta("roberto_del_computer"))
        assert [m for m, _ in _escrituras(h["red"])] == ["GET"], h["red"]
        assert h["r"] == _la_de_main("acepta", "roberto_del_computer", execute=False)
        assert h["ensayo"] == [{"operation": "ACCEPT_OFFER", "method": "PUT",
                                "url": f"{URL}/offers/91004",
                                "json": {"status": "accepted"}}], h["ensayo"]


# 10. SIN ORDEN QUE MIRAR, NADA (como la guarda de publicar)

def test_sin_orden_no_se_frena_nada():
    """La orden apagada, caducada, rota o sin fichero: no se frena nada y ni
    se hace el GET (la respuesta de main). El lunes (Boye solo en
    `conservar`): su oferta del Computer pasa, la de un manager no. Yamal
    con su llave (fuera de `proteger`): pasa."""
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden in ("apagada", "caducada", "rota", "sin_orden"):
            for operacion, hacer, metodo in (("acepta", _acepta, "PUT"),
                                             ("contra", _contraoferta, "POST")):
                for nombre in ("boye_del_computer", "yamal_del_computer",
                               "roberto_de_un_manager", "lote_iglesias_ivan"):
                    h = _con(carpeta, nombre_orden, valor="1", hacer=hacer(nombre))
                    assert [m for m, _ in _escrituras(h["red"])] == [metodo], \
                        (nombre_orden, h["red"])
                    assert h["r"] == _la_de_main(operacion, nombre), h["r"]
        h = _con(carpeta, "lunes", valor="1", hacer=_acepta("boye_del_computer"))
        assert [m for m, _ in _escrituras(h["red"])] == ["GET", "PUT"], h["red"]
        assert h["r"] == _la_de_main("acepta", "boye_del_computer")
        for hacer in (_acepta, _contraoferta):
            h = _con(carpeta, "lunes", valor="1", hacer=hacer("boye_de_un_manager"))
            _frenada(h, CONSERVADO, [BOYE], [BOYE], True)
        h = _con(carpeta, "lunes", valor="1", hacer=_contraoferta("boye_del_computer"))
        _frenada(h, CONSERVADO, [BOYE], [BOYE], False)
        h = _con(carpeta, "lunes", valor="1", hacer=_acepta("yamal_del_computer"))
        _frenada(h, PROTEGIDO, [YAMAL], [YAMAL], False)
        h = _con(carpeta, "yamal_por_lesion", valor="1", hacer=_acepta("yamal_del_computer"))
        assert [m for m, _ in _escrituras(h["red"])] == ["GET", "PUT"], h["red"]
        assert h["r"] == _la_de_main("acepta", "yamal_del_computer")


# 11. UNA PETICION MAS, Y SOLO UNA

def test_una_peticion_mas():
    """Encendido, una aceptacion: un GET `/market` y una PUT, en ese orden;
    la orden se lee una vez (protegidos y conservados)."""
    with tempfile.TemporaryDirectory() as carpeta:
        h = _con(carpeta, valor="1", hacer=_acepta("iglesias_del_computer"))
        assert _escrituras(h["red"]) == [("GET", f"{URL}/market"),
                                         ("PUT", f"{URL}/offers/91007")], h["red"]
        assert h["cuentas"] == {"protegidos": 1, "conservados": 1}, h["cuentas"]
        assert not any(e["metodo"] == "GET_DE_LA_SESION" for e in h["red"])
        h = _con(carpeta, valor="1", hacer=_contraoferta("iglesias_de_un_manager"))
        assert _escrituras(h["red"]) == [("GET", f"{URL}/market"),
                                         ("POST", f"{URL}/offers")], h["red"]


# 12. LOS LLAMADORES

def test_el_motor_viejo_y_su_cluster():
    """La fila de Iglesias de una oferta que pide tambien a Roberto: el
    ejecutor solo mira la fila y deja pasar; encendido, el escritor la
    frena y el motor viejo lo dice como su BLOCKED_PROTECTED_PLAYER, sin
    escritura gastada ni rastro. Iglesias y Dani del Computer: se aceptan."""
    with tempfile.TemporaryDirectory() as carpeta:
        for hacer, extra in (
                (_el_motor_viejo("lote_iglesias_roberto", IGLESIAS, "Juan Iglesias"), {}),
                (_el_cluster("lote_iglesias_roberto", IGLESIAS, "Juan Iglesias"),
                 {"revalidation_snapshot": FOTO_FRESCA, "player_id": IGLESIAS})):
            h = _con(carpeta, valor="1", hacer=hacer)
            r = h["r"]
            assert not any(e["metodo"] in ("PUT", "POST") for e in h["red"]), \
                f"se envio: {h['red']}"
            assert r["status"] == "BLOCKED_PROTECTED_PLAYER", r
            assert r["write_performed"] is False and r["success"] is False, r
            assert r["http_status"] is None and r["response"] is None, r
            assert r["guardia"] == "LA_ORDEN_EN_EL_ESCRITOR", r
            assert r["de_la_orden"] == [ROBERTO], r
            assert r["offer"]["offer_id"] == 91008, r
            assert "LA_ORDEN_EN_EL_ESCRITOR" in r["reason"], r
            for clave, valor in extra.items():
                assert r[clave] == valor, (clave, r)
            assert h["rastro"] == [], h["rastro"]
        for oferta, pid in (("iglesias_del_computer", IGLESIAS), ("dani_del_computer", DANI)):
            h = _con(carpeta, valor="1", hacer=_el_motor_viejo(oferta, pid, "libre"))
            assert h["r"]["status"] == "OFFER_ACCEPTED" and h["r"]["write_performed"], h["r"]
            assert [m for m, _ in _escrituras(h["red"])] == ["GET", "PUT"], h["red"]
            assert len(h["rastro"]) == 1
            h = _con(carpeta, valor="1", hacer=_el_cluster(oferta, pid, "libre"))
            assert h["r"]["status"] == "EXPIRY_OFFER_ACCEPTED", h["r"]
        # Apagado: main (lo envia, OFFER_ACCEPTED/FAILED con escritura).
        for respuesta, estado in ((RESPUESTAS[0], "OFFER_ACCEPTED"), (RESPUESTAS[1], "FAILED")):
            h = _con(carpeta, respuesta=respuesta, hacer=_el_motor_viejo(
                "lote_iglesias_roberto", IGLESIAS, "Juan Iglesias"))
            assert h["r"]["status"] == estado and h["r"]["write_performed"] is True, h["r"]


def test_competitive_v2():
    """Competitive V2, con la pieza de los managers apagada: aceptar o
    contraofertar la oferta de un manager por Boye (o por Roberto, o la de
    Iglesias e Ivan) se frena en el escritor: COMPETITIVE_BLOCKED_EL_ESCRITOR,
    `write_performed` False. La de Iglesias solo: se envia."""
    with tempfile.TemporaryDirectory() as carpeta:
        for oferta, de_la_orden in (("boye_de_un_manager", [BOYE]),
                                    ("roberto_de_un_manager", [ROBERTO]),
                                    ("lote_iglesias_ivan", [IVAN])):
            for decision in ("ACCEPT_NOW", "COUNTER_OFFER"):
                h = _con(carpeta, valor="1", hacer=_competitive(oferta, decision))
                r = h["r"]
                assert not any(e["metodo"] in ("PUT", "POST") for e in h["red"]), \
                    f"se envio: {h['red']}"
                assert r["status"] == "COMPETITIVE_BLOCKED_EL_ESCRITOR", r
                assert r["write_performed"] is False and r["success"] is False, r
                assert r["http_status"] is None and r["response"] is None, r
                assert r["guardia"] == "LA_ORDEN_EN_EL_ESCRITOR", r
                assert r["de_la_orden"] == de_la_orden, r
                assert r["offer_id"] == _id(oferta) and r["player_id"] == JUGADOR_DE[oferta], r
                assert r["revalidation_snapshot"] == FOTO_FRESCA, r
                assert r["action"] == decision, r
        for decision, estado in (("ACCEPT_NOW", "COMPETITIVE_OFFER_ACCEPTED"),
                                 ("COUNTER_OFFER", "COMPETITIVE_COUNTER_SENT")):
            h = _con(carpeta, valor="1", hacer=_competitive("iglesias_de_un_manager", decision))
            assert h["r"]["status"] == estado and h["r"]["write_performed"] is True, h["r"]


def test_v10_y_la_orden():
    """V10 RAISE_COUNTER: `write_used = bool(action_result.get("success"))`
    da False con la frenada. La orden (`ejecutar`): `enviada` False, `exito`
    False, las mismas claves que siempre; su venta del Computer por uno de
    `conservar` (Roberto) se envia."""
    fuente = (RAIZ / "src" / "v10_full_autonomous_live.py").read_text(encoding="utf-8")
    contra = fuente.index("action_result = writer.counter_offer(")
    usado = fuente.index("write_used = bool(", contra)
    assert fuente[usado:usado + 80].split("\n")[1].strip() == 'action_result.get("success")', \
        fuente[usado:usado + 80]
    assert fuente.index('action_taken = "RAISE_COUNTER"', contra) > usado
    with tempfile.TemporaryDirectory() as carpeta:
        h = _con(carpeta, valor="1", hacer=_contraoferta("roberto_de_un_manager"))
        assert bool(h["r"].get("success")) is False, h["r"]
        h = _con(carpeta, valor="1", hacer=_la_orden_ejecuta(
            ("boye_del_computer", "roberto_del_computer", "lote_iglesias_ivan")))
        hechas = h["r"]
        assert [(x["offer_id"], x["enviada"], x["exito"], x["http_status"]) for x in hechas] == [
            (91001, False, False, None), (91004, True, True, 200),
            (91005, False, False, None)], hechas
        claves = {"accion", "offer_id", "player_id", "nombre", "enviada", "exito", "http_status"}
        assert all(set(x) == claves for x in hechas), hechas


# 13. LAS FUENTES

def test_las_fuentes():
    """La guarda va con `execute` y antes del ensayo en los dos metodos; el
    resto del escritor y `la_orden_del_gestor.ejecutar`, los de main."""
    texto = (RAIZ / "src" / "biwenger" / "write_client.py").read_text(encoding="utf-8")
    arbol = ast.parse(texto)
    clase = next(n for n in arbol.body if isinstance(n, ast.ClassDef)
                 and n.name == "BiwengerWriteClient")
    for nombre, operacion in (("accept_offer", "ACCEPT_OFFER"),
                              ("counter_offer", "COUNTER_OFFER")):
        nodo = next(n for n in clase.body if isinstance(n, ast.FunctionDef) and n.name == nombre)
        cuerpo = ast.get_source_segment(texto, nodo)
        construye = cuerpo.index("self.build_")
        importa = cuerpo.index("from src.analysis.la_orden_en_el_escritor import")
        guarda = cuerpo.index(f'guardar(self, "{operacion}", offer_id)')
        ensayo = cuerpo.index("self._en_ensayo(request)")
        envia = cuerpo.index("self.client.session.")
        assert construye < importa < guarda < ensayo < envia, nombre
        assert cuerpo.count("from src.analysis.la_orden_en_el_escritor import") == 1, nombre
        assert cuerpo[:importa].rstrip().endswith("try:"), nombre
        assert cuerpo[:cuerpo.index("try:", construye)].rstrip().endswith("if execute:"), nombre
    assert texto.count("from src.analysis.la_orden_en_el_escritor import") == 2
    fuentes = _las_fuentes()
    assert _huella_de(fuentes) == FUENTES_DE_MAIN, (
        "el resto del escritor o `la_orden_del_gestor.ejecutar` ya no son los de main: "
        f"{_huella_de(fuentes)}")
    # Los llamadores: el motor viejo y Competitive V2 miran `blocked` justo
    # despues de escribir; V10 y la orden no se tocan.
    ae = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text(encoding="utf-8")
    assert ae.count('result.get("blocked")') == 2
    cle = (RAIZ / "src" / "analysis" / "competitive_live_executor.py").read_text(
        encoding="utf-8")
    assert cle.count("_frenada_por_el_escritor(") == 3     # la funcion y sus dos llamadas
    assert cle.count('result.get("blocked")') == 1
    assert cle.count('"COMPETITIVE_BLOCKED_EL_ESCRITOR"') == 1
    contra = cle.index("writer.counter_offer(")
    acepta = cle.index("writer.accept_offer(")
    assert contra < cle.index("_frenada_por_el_escritor(", contra) < acepta
    assert acepta < cle.index("_frenada_por_el_escritor(", acepta)


# 14. NUNCA LANZA; SI NO SE IMPORTA, LO DE SIEMPRE

def test_nunca_lanza():
    from src.analysis import la_orden_en_el_escritor as pieza
    import src.actions.la_orden_del_gestor as orden_mod

    def _revienta(*a, **k):
        raise RuntimeError("la orden no se puede leer")

    class _SinCliente:
        pass

    class _ClienteRaro:
        client = "x"

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        with _Interruptores({ENV: "1", ENV_ORDEN: "1"}), _Sustituye(_la_orden(ruta, {})):
            for escritor in (None, _SinCliente(), _ClienteRaro(), "x"):
                r = pieza.guardar(escritor, "ACCEPT_OFFER", 91001)
                assert set(r) == {"sin_ver"}, r
                assert r["sin_ver"].startswith("SIN_LEER_EL_MERCADO: "), r
            for rara in (None, "x", 7, {}, {"pedidos": "x"}, {"pedidos": None},
                         {"pedidos": 7}, {"pedidos": [None, True, "no", -BOYE]}):
                assert pieza.lo_que_frena("COUNTER_OFFER", rara, {BOYE}, {BOYE}) is None, rara
        # La orden que revienta: nada (lo de siempre), y el escritor envia.
        with _Interruptores({ENV: "1", ENV_ORDEN: "1"}), _Sustituye(
                [(orden_mod, n, _revienta) for n in ("conservados", "protegidos")]):
            assert pieza.guardar(_SinCliente(), "ACCEPT_OFFER", 91001) is None
            red = []
            r = _fabrica(red)().accept_offer(offer_id=91001, execute=True)
            assert r == _la_de_main("acepta", "boye_del_computer"), r
            assert [e["metodo"] for e in red] == ["CREA_EL_ESCRITOR", "PUT"], red


def test_si_no_se_importa_lo_de_siempre():
    """La pieza se importa dentro de un `try` en los dos metodos. Si no se
    pudiera importar, encendido es main."""
    nombre = "src.analysis.la_orden_en_el_escritor"
    import src.analysis.la_orden_en_el_escritor  # noqa: F401  (ya cargada)

    with tempfile.TemporaryDirectory() as carpeta:
        antes = sys.modules.get(nombre)
        sys.modules[nombre] = None                  # la importacion falla
        try:
            hechos = [_con(carpeta, valor="1", hacer=h("boye_del_computer"))
                      for h in (_acepta, _contraoferta)]
        finally:
            if antes is None:
                sys.modules.pop(nombre, None)
            else:
                sys.modules[nombre] = antes
    assert sys.modules.get(nombre) is antes
    for hecho, operacion in zip(hechos, ("acepta", "contra")):
        assert hecho["r"] == _la_de_main(operacion, "boye_del_computer"), hecho["r"]


# 15. EL ENTORNO NO DECIDE (doctrina 104)

def test_el_entorno_no_decide_esta_guardia():
    """Con todo lo de fuera puesto (los del tablon, este incluido, el
    ensayo, uno que no existe), cada prueba da lo mismo, y al salir el
    entorno es el de antes."""
    from src.analysis.el_paso_0 import PREFIJO
    from src.telemetry.el_tablon import QUE_HACE

    de_fuera = {n: "1" for n in QUE_HACE if n.startswith(PREFIJO)}
    de_fuera.update({PREFIJO + "SIN_REVENTA": "1", PREFIJO + "BID_SALT": "otra-sal",
                     PREFIJO + "LA_HUCHA": "1", ENSAYO_ENV: "1",
                     PREFIJO + "UNO_QUE_NO_EXISTE": "si", ENV: "1",
                     "GITHUB_RUN_ID": "41810000000"})
    antes = {k: os.environ.get(k) for k in de_fuera}
    os.environ.update(de_fuera)
    try:
        with _Interruptores({ENV_ORDEN: "1"}):
            dentro = sorted(k for k in os.environ
                            if k.startswith(PREFIJO) and k not in DE_LA_VERJA)
            assert dentro == [ENV_ORDEN], dentro
            assert "GITHUB_RUN_ID" not in os.environ
        assert {k: os.environ.get(k) for k in de_fuera} == de_fuera
        for test in TESTS:
            if test in (test_apagado_es_main_byte_a_byte, test_el_entorno_no_decide_esta_guardia):
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
    test_nace_apagado_un_lector_y_su_frase,
    test_lo_que_el_paso_0_da_por_encendido,
    test_apagado_es_main_byte_a_byte,
    test_apagado_ni_red_ni_orden,
    test_encendido_proteger_ni_se_acepta_ni_se_contraoferta,
    test_encendido_conservar_solo_se_acepta_del_computer,
    test_una_oferta_por_varios_y_un_jugador_libre,
    test_lo_que_lee_de_la_oferta,
    test_sin_ver_la_oferta_se_escribe,
    test_en_seco_ni_se_mira_y_el_ensayo,
    test_sin_orden_no_se_frena_nada,
    test_una_peticion_mas,
    test_el_motor_viejo_y_su_cluster,
    test_competitive_v2,
    test_v10_y_la_orden,
    test_las_fuentes,
    test_nunca_lanza,
    test_si_no_se_importa_lo_de_siempre,
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
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}"[:600])
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
