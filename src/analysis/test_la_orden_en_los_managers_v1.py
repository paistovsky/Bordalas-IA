"""
LA ORDEN EN LOS MANAGERS (04/11/2026). Guardias de
`BORDALAS_LA_ORDEN_EN_LOS_MANAGERS`
(`src/analysis/la_orden_en_los_managers.py` y sus dos enganches: la
eleccion de `competitive_safety_gate.select_single_competitive_action`
y la escritura de `competitive_live_executor.execute_competitive_live_action`).

EL HUECO (revision encendida del 04/11 por la manana)

    Competitive V2 es el motor que contesta las ofertas de OTROS
    MANAGERS: el motor (`competitive_transaction_engine`) decide
    ACCEPT_NOW, ACCEPT_SACRIFICE_LINEUP o COUNTER_OFFER, el Safety Gate
    solo frena NEVER_SELL y NEVER_AUTO_SELL, la eleccion se queda la
    primera autorizada y el ejecutor escribe (`counter_offer` o
    `accept_offer`) en la vuelta en que el motor viejo no ha escrito.
    Nadie mira la orden del gestor: su unica guarda parecida es EL_RELEVO.
    El escritor tampoco (`accept_offer` y `counter_offer` no tienen la
    guarda de `list_player_for_sale`). Asi que la oferta de un manager
    por Roberto Fernandez (`conservar` y `no_rotar`; el DUENO dijo el
    02/11 «No lo vendas de momento») o por Boye (`proteger`) se podia
    ACEPTAR o CONTRAOFERTAR (una contraoferta que el rival acepta tambien
    es vender). Hoy hay 0 ofertas de managers: no ha pasado todavia.

QUE SE COMPRUEBA

    1. Nace apagado, se lee en UN sitio (`activo`, al llamarse, solo
       desde el propio modulo), vale lo mismo que `el_paso_0.ENCENDIDO`,
       tiene frase en QUE_HACE y no hace nada al importarse.
    2. Apagado es main byte a byte: la huella de la bateria (la eleccion
       del Safety Gate, la sombra V1.9, el ejecutor V2.0 con el escritor
       real sin red y con uno de mentira, y la vuelta entera: eleccion,
       oferta elegida y escritura, como la junta `autopilot`), con la
       orden de hoy, la del lunes (Boye fuera de `proteger`), caducada,
       sin orden y una que no se lee; con el interruptor sin poner, "0",
       "", "off" y "2", sin interruptores y con los 27 del YAML de
       produccion (origin/main 1ac6fd51). La de main, medida antes de
       tocar el codigo, una por version de Python (3.11 y 3.13).
    3. EL CASO, ACEPTAR: un manager ofrece por Roberto (ACCEPT_NOW).
       Encendido: no se elige (BLOCK_LA_ORDEN_DEL_GESTOR), la vuelta no
       llama a `accept_offer`. Apagado: main (se acepta).
    4. EL CASO, CONTRAOFERTAR: COUNTER_OFFER por Boye. Encendido: ni se
       elige ni se llama a `counter_offer`.
    5. La siguiente se queda la vuelta: Roberto y luego Iglesias, o Boye
       y luego Iglesias: encendido, la de Iglesias.
    6. Un jugador que la orden no guarda (Juan Iglesias): igual que main.
    7. Orden caducada, sin orden, ilegible o apagada: igual que main.
    8. El ejecutor, defensa en profundidad: si le llega igual (la eleccion
       de otra version, una oferta elegida a mano), noop honesto
       COMPETITIVE_BLOCKED_LA_ORDEN, `success` False, `write_performed`
       False, `guardia`, y el escritor ni se crea.
    9. La misma puerta: los que se frenan son exactamente
       `conservados() | protegidos()` de la orden, jugador a jugador.
   10. Nada mas cambia: EL_RELEVO sigue primero, NEVER_SELL,
       NEVER_AUTO_SELL (Yamal no se vende nunca, ni encendido ni
       apagado), el cierre temporal y la revalidacion fresca.
   11. Hoy (20:07): 0 ofertas de managers. Encendido y apagado, nada.
   12. Nunca lanza; si la pieza no se pudiera importar, lo de siempre.
   13. El entorno no la decide (doctrina 104).

DE DONDE SALEN LOS NUMEROS

    La orden de `config/la_orden_del_gestor.json` del 04/11 (escrita
    09:00, caduca 30/11), copiada a mano. Los valores de mercado, de las
    publicaciones del 04/11 (Roberto 6.990.000, Boye 5.370.000, Iglesias
    3.800.000). Las ofertas de managers son de la prueba: hoy no hay
    ninguna (run de las 20:07). Ni `data/`, ni la red, ni el reloj: la
    hora se pasa, la orden va a una carpeta temporal y se lee con las
    funciones reales (`la_orden_del_gestor.conservados(ruta, ahora)` y
    `protegidos(ruta, ahora)`), la foto fresca y el tablero de ofertas
    son de mentira y el escritor es el real sin red (una sesion de
    mentira) o uno de mentira que apunta lo que le piden.

COMO SE USA

    python -m src.analysis.test_la_orden_en_los_managers_v1
    python -m src.analysis.test_la_orden_en_los_managers_v1 --medir
    python -m src.analysis.test_la_orden_en_los_managers_v1 --volcar FICHERO
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile

from datetime import date, datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


ENV = "BORDALAS_LA_ORDEN_EN_LOS_MANAGERS"
ENV_ORDEN = "BORDALAS_LA_ORDEN_DEL_GESTOR"
ENV_RELEVO = "BORDALAS_EL_RELEVO_NO_SE_VENDE"
ENV_MEJORA = "BORDALAS_LA_MEJORA_DEL_ONCE"

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
# LOS JUGADORES Y LA ORDEN DE HOY
# ============================================================

YO = 14175949
BOYE, CHUST, YAMAL = 12494, 1760, 26271
ROBERTO, IVAN, KIKE, OLASAGASTI = 35678, 12403, 28115, 29661
GULACSI, CARDONA, RAMON, IGLESIAS, DANI = 38433, 30493, 41411, 23840, 41418

_UTC = timezone.utc

# Mie 04/11, 20:50 en Madrid (UTC+1).
AHORA = datetime(2026, 11, 4, 19, 50, tzinfo=_UTC)
SALDO = 2_025_724

ORDEN_HOY = {
    "escrita": "2026-11-04T09:00:00+01:00",
    "caduca": "2026-11-30T23:59:00+01:00",
    "fichar": [],
    "no_pujar": [{"player_id": 1721, "nombre": "Manu Sánchez"}],
    "no_rotar": [{"player_id": ROBERTO, "nombre": "Roberto Fernández"}],
    "vender_si_ficha": {"jugadores": []},
    "proteger": [{"player_id": YAMAL, "nombre": "Yamal"},
                 {"player_id": BOYE, "nombre": "Boyé"}],
    "conservar": [{"player_id": p, "nombre": n} for p, n in (
        (CHUST, "Chust"), (OLASAGASTI, "Olasagasti"), (ROBERTO, "Roberto Fernández"),
        (GULACSI, "Gulácsi"), (CARDONA, "Sergi Cardona"), (BOYE, "Boyé"),
        (KIKE, "Kike Salas"), (IVAN, "Iván Martín"), (RAMON, "Ramón Enríquez"))],
}

# El lunes 09/11: Boye sale de `proteger` (sigue en `conservar`).
ORDEN_SIN_BOYE = {**ORDEN_HOY, "proteger": [{"player_id": YAMAL, "nombre": "Yamal"}]}

ORDEN_CADUCADA = {**ORDEN_HOY, "caduca": "2026-11-03T23:59:00+01:00"}

# `None`: no hay fichero. Un texto: el fichero tal cual (no se lee).
ORDENES = (("hoy", ORDEN_HOY), ("sin_boye", ORDEN_SIN_BOYE),
           ("caducada", ORDEN_CADUCADA), ("sin_orden", None),
           ("ilegible", "{esto no es una orden"))


# ============================================================
# LAS OFERTAS DE LOS MANAGERS (como las junta `autopilot`)
# ============================================================

RIVAL = (13000002, "Un rival de la liga")
OTRO_RIVAL = (13000005, "Otro rival")


def _oferta(pid, nombre, decision, importe, offer_id, *, contra=None, estrategico=None,
            accion="ALLOW_SINGLE_RESPONSE", responde=True, proteccion="", once=11,
            autoridad="COMPETITIVE", rival=RIVAL) -> dict:
    """Una entrada de `manager_offers` (`autopilot.build_competitive_observer`)."""
    return {
        "offer_id": offer_id,
        "player_id": pid,
        "protection": proteccion,
        "player_name": nombre,
        "rival_user_id": rival[0],
        "rival_name": rival[1],
        "amount": importe,
        "legacy_decision": "HOLD_OFFER",
        "competitive_decision": decision,
        "decision_authority": autoridad,
        "authoritative_decision": decision,
        "authoritative_counter_amount": contra,
        "authority_observer_only": False,
        "base_sell_price": estrategico,
        "strategic_sell_price": estrategico,
        "counter_amount": contra,
        "replacement": None,
        "replacement_detail": {"post_sale_playable_count": once} if once else {},
        "negotiation": {"action_gate": accion, "should_respond": responde,
                        "key": f"{pid}:{rival[0]}", "negotiation_round": 0},
        "legacy_differs": True,
    }


ROBERTO_ACEPTA = _oferta(ROBERTO, "Roberto Fernández", "ACCEPT_NOW", 8_400_000, 70001,
                         estrategico=8_100_000)
ROBERTO_SACRIFICIO = _oferta(ROBERTO, "Roberto Fernández", "ACCEPT_SACRIFICE_LINEUP",
                             9_000_000, 70002, estrategico=8_100_000, once=10)
BOYE_CONTRA = _oferta(BOYE, "Boyé", "COUNTER_OFFER", 5_600_000, 70003,
                      contra=6_450_000, estrategico=6_300_000)
IGLESIAS_ACEPTA = _oferta(IGLESIAS, "Juan Iglesias", "ACCEPT_NOW", 4_500_000, 70004,
                          estrategico=4_300_000, rival=OTRO_RIVAL)
IGLESIAS_CONTRA = _oferta(IGLESIAS, "Juan Iglesias", "COUNTER_OFFER", 3_900_000, 70005,
                          contra=4_400_000, estrategico=4_300_000, rival=OTRO_RIVAL)
YAMAL_ACEPTA = _oferta(YAMAL, "Yamal", "ACCEPT_NOW", 38_000_000, 70006,
                       estrategico=36_000_000, proteccion="NEVER_AUTO_SELL")
# De la prueba: Yamal sin su proteccion del roster (no pasa en
# produccion: la liquidez lo marca NEVER_AUTO_SELL).
YAMAL_SIN_PROTECCION = {**YAMAL_ACEPTA, "offer_id": 70007, "protection": ""}
CHUST_NUNCA = _oferta(CHUST, "Chust", "NEVER_SELL", 3_000_000, 70008, estrategico=3_500_000)
KIKE_ESPERA = _oferta(KIKE, "Kike Salas", "HOLD", 3_600_000, 70009, estrategico=3_900_000)
IVAN_LEGACY = _oferta(IVAN, "Iván Martín", "ACCEPT_NOW", 3_200_000, 70010,
                      estrategico=3_000_000, autoridad="LEGACY")
DANI_ESPERA_AL_RIVAL = _oferta(DANI, "Dani Lorenzo", "COUNTER_OFFER", 2_100_000, 70011,
                               contra=2_500_000, estrategico=2_400_000,
                               accion="WAITING_RIVAL", responde=False)
GULACSI_BAJA = _oferta(GULACSI, "Gulácsi", "COUNTER_OFFER", 2_300_000, 70012,
                       contra=2_350_000, estrategico=2_600_000)
# Raras: el id como texto (el de Roberto), sin id, un id que no es un id.
ROBERTO_TEXTO = {**ROBERTO_ACEPTA, "offer_id": 70013, "player_id": str(ROBERTO)}
SIN_ID = {**IGLESIAS_ACEPTA, "offer_id": 70014, "player_id": None}
ID_RARO = {**IGLESIAS_ACEPTA, "offer_id": 70015, "player_id": "no-es-un-id"}
ID_BOOL = {**IGLESIAS_ACEPTA, "offer_id": 70016, "player_id": True}

LISTAS = (
    ("hoy_ninguna", []),
    ("roberto_acepta", [ROBERTO_ACEPTA]),
    ("boye_contra", [BOYE_CONTRA]),
    ("roberto_luego_iglesias", [ROBERTO_ACEPTA, IGLESIAS_ACEPTA]),
    ("boye_luego_iglesias", [BOYE_CONTRA, IGLESIAS_CONTRA]),
    ("iglesias", [IGLESIAS_ACEPTA]),
    ("yamal_y_roberto", [YAMAL_ACEPTA, ROBERTO_SACRIFICIO]),
    ("yamal_sin_proteccion", [YAMAL_SIN_PROTECCION]),
    ("mezcla", [CHUST_NUNCA, KIKE_ESPERA, IVAN_LEGACY, DANI_ESPERA_AL_RIVAL, GULACSI_BAJA,
                ROBERTO_SACRIFICIO, BOYE_CONTRA, IGLESIAS_CONTRA]),
    ("raras", [ROBERTO_TEXTO, ID_BOOL, SIN_ID, ID_RARO]),
)

PUERTAS = (
    ("normal", {"phase": "NORMAL", "operations_locked": False, "hard_safety_mode": False,
                "target_matchday": 12, "next_matchday": 12}),
    ("cerrada", {"phase": "LOCKED", "operations_locked": True, "hard_safety_mode": False,
                 "target_matchday": 12, "next_matchday": 12}),
)


# ============================================================
# LO QUE SE SUSTITUYE (disco, red y reloj)
# ============================================================

def _la_orden_en(carpeta, nombre_orden, orden) -> Path:
    """La orden escrita en `carpeta` (o una ruta que no existe)."""
    ruta = Path(carpeta) / f"orden_{nombre_orden}.json"
    if orden is not None and not ruta.exists():
        texto = orden if isinstance(orden, str) else json.dumps(orden, ensure_ascii=False)
        ruta.write_text(texto, encoding="utf-8")
    return ruta


def _la_orden_de_mentira(ruta, ahora=AHORA):
    """`protegidos`, `vetados` y `conservados` de la orden real, leyendo
    `ruta` a la hora `ahora` (las tres funciones de verdad: solo cambia de
    donde leen y que hora es)."""
    import src.actions.la_orden_del_gestor as orden_mod

    reales = {n: getattr(orden_mod, n) for n in ("protegidos", "vetados", "conservados")}
    return [(orden_mod, n, (lambda f: (lambda *a, **k: f(ruta, ahora)))(f))
            for n, f in reales.items()]


def _fresca(oferta, cambio="igual"):
    """La decision del tablero fresco (`build_offer_decision_board`) para
    `oferta`, con `cambio`. None: no esta."""
    if not isinstance(oferta, dict) or cambio == "no_existe":
        return None
    d = {
        "counterparty_type": "MANAGER",
        "offer_id": oferta.get("offer_id"),
        "player_id": oferta.get("player_id"),
        "amount": oferta.get("amount"),
        "counterparty_id": oferta.get("rival_user_id"),
        "competitive_observer": {
            "decision": oferta.get("authoritative_decision"),
            "strategic_sell_price": oferta.get("strategic_sell_price"),
            "counter_amount": oferta.get("authoritative_counter_amount")
            or oferta.get("counter_amount"),
        },
    }
    if cambio == "importe":
        d["amount"] = (d["amount"] or 0) + 100_000
    elif cambio == "decision":
        d["competitive_observer"]["decision"] = "NEVER_SELL"
    elif cambio == "contra_cero":
        d["competitive_observer"]["counter_amount"] = 0
    elif cambio == "debajo":
        d["competitive_observer"]["strategic_sell_price"] = (d["amount"] or 0) + 1
    elif cambio == "otro_jugador":
        d["player_id"] = DANI
    return d


# Una oferta del Computer en el mismo tablero: el ejecutor la salta.
DEL_COMPUTER = {"counterparty_type": "COMPUTER", "offer_id": 8101, "player_id": CHUST,
                "amount": 2_855_600, "competitive_observer": {"decision": "ACCEPT_NOW"}}


def _tablero_fresco(ofertas, cambio="igual") -> dict:
    decisiones = [copy.deepcopy(DEL_COMPUTER)]
    for oferta in ofertas:
        d = _fresca(oferta, cambio)
        if d is not None:
            decisiones.append(d)
    return {"decisions": decisiones}


class _Respuesta:
    def __init__(self, status, cuerpo):
        self.status_code, self._cuerpo = status, cuerpo
        self.text = "" if cuerpo is None else json.dumps(cuerpo)

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin cuerpo")
        return self._cuerpo


def _escritor_real(status, cuerpo, enviados):
    """El `BiwengerWriteClient` de verdad, sin login y con una sesion de
    mentira: lo que se enviaria se apunta en `enviados`."""
    import src.biwenger.write_client as escritura

    class _Sesion:
        def post(self, url, json=None, timeout=None):
            enviados.append({"metodo": "POST", "url": url, "json": json})
            return _Respuesta(status, cuerpo)

        def put(self, url, json=None, timeout=None):
            enviados.append({"metodo": "PUT", "url": url, "json": json})
            return _Respuesta(status, cuerpo)

    class _Cliente:
        BASE_URL = "https://biwenger.invalid/api/v2"
        session = _Sesion()

    def fabrica():
        enviados.append({"metodo": "CREA_EL_ESCRITOR"})
        cliente = object.__new__(escritura.BiwengerWriteClient)
        cliente.client = _Cliente()
        cliente.version, cliente.league_id, cliente.user_id = "0", 2165477, YO
        return cliente

    return fabrica


def _escritor_de_mentira(enviados):
    class _Escritor:
        def __init__(self):
            enviados.append({"metodo": "CREA_EL_ESCRITOR"})

        def accept_offer(self, offer_id, execute=False):
            enviados.append({"metodo": "accept_offer", "offer_id": offer_id,
                             "execute": execute})
            return {"success": True, "http_status": 200, "response": {"status": 200}}

        def counter_offer(self, offer_id, amount, execute=False):
            enviados.append({"metodo": "counter_offer", "offer_id": offer_id,
                             "amount": amount, "execute": execute})
            return {"success": True, "http_status": 200, "response": {"status": 200}}

    return _Escritor


ESCRITORES = (
    ("real_200", lambda env: _escritor_real(200, {"status": 200, "data": {"ok": True}}, env)),
    ("real_400", lambda env: _escritor_real(
        400, {"status": 400, "message": "La oferta ya no existe"}, env)),
    ("mentira", _escritor_de_mentira),
)

# Solo un nombre: la foto fresca no se lee (ni se escribe) en ningun sitio.
FOTO_FRESCA = "snapshot_fresco_2026-11-04_20-07-00.json"


def _el_ejecutor_de_mentira(tablero, fabrica, refresco_falla=False):
    """La foto fresca (sin red), el tablero de ofertas fresco (sin
    calcular nada) y el escritor. `find_fresh_manager_decision` es la de
    verdad."""
    import src.analysis.competitive_live_executor as cle

    def _refresca():
        if refresco_falla:
            raise RuntimeError("Biwenger no contesta")
        return FOTO_FRESCA, {"timestamp": "snapshot_2026-11-04_20-07-00"}

    return [
        (cle, "refresh_snapshot", _refresca),
        (cle, "build_offer_decision_board", lambda **k: copy.deepcopy(tablero)),
        (cle, "BiwengerWriteClient", fabrica),
    ]


# ============================================================
# LAS LLAMADAS DE LA BATERIA (las firmas de main)
# ============================================================

def _la_eleccion(ofertas, puerta, ruta, entorno) -> dict:
    """`select_single_competitive_action` con estas ofertas."""
    from src.analysis.competitive_safety_gate import select_single_competitive_action

    with _Interruptores(entorno), _Sustituye(_la_orden_de_mentira(ruta)):
        return select_single_competitive_action(
            offers=copy.deepcopy(ofertas), temporal_gate=copy.deepcopy(puerta),
            current_balance=SALDO)


def _la_sombra(ofertas, puerta, ruta, entorno) -> dict:
    """La sombra V1.9: `build_competitive_shadow_decision` y
    `execute_competitive_shadow`."""
    from src.analysis.competitive_execution_shadow import (
        build_competitive_shadow_decision,
        execute_competitive_shadow,
    )

    with _Interruptores(entorno), _Sustituye(_la_orden_de_mentira(ruta)):
        sombra = build_competitive_shadow_decision(
            manager_offers=copy.deepcopy(ofertas), temporal_gate=copy.deepcopy(puerta),
            current_balance=SALDO)
        return {"sombra": sombra, "ejecucion": execute_competitive_shadow(sombra)}


def _el_ejecutor(oferta, cambio, escritor, ruta, entorno, execute=True) -> dict:
    """`execute_competitive_live_action` con `oferta` elegida, el tablero
    fresco con `cambio` y el escritor: lo que devuelve y lo que se pidio
    al escritor."""
    import src.analysis.competitive_live_executor as cle

    enviados = []
    tablero = _tablero_fresco([oferta] if oferta else [], cambio)
    with _Interruptores(entorno), _Sustituye(
            _la_orden_de_mentira(ruta)
            + _el_ejecutor_de_mentira(tablero, escritor(enviados),
                                      refresco_falla=(cambio == "refresco_falla"))):
        r = cle.execute_competitive_live_action(
            selected_offer=copy.deepcopy(oferta), rival_intelligence={}, execute=execute)
    return {"r": r, "enviados": enviados}


def _la_vuelta(ofertas, escritor, ruta, entorno, puerta=PUERTAS[0][1]) -> dict:
    """La vuelta competitiva como la junta `autopilot.run_cycle` (el motor
    viejo no ha escrito): la eleccion del Safety Gate, la oferta elegida
    (mismo `offer_id` y `player_id`) y el ejecutor con `execute=True`."""
    import src.analysis.competitive_live_executor as cle
    from src.analysis.competitive_safety_gate import select_single_competitive_action

    enviados = []
    with _Interruptores(entorno), _Sustituye(
            _la_orden_de_mentira(ruta)
            + _el_ejecutor_de_mentira(_tablero_fresco(ofertas), escritor(enviados))):
        manager_offers = copy.deepcopy(ofertas)
        eleccion = select_single_competitive_action(
            offers=manager_offers, temporal_gate=copy.deepcopy(puerta),
            current_balance=SALDO)
        elegida = eleccion.get("selected")
        oferta = None
        if elegida:
            oferta = next((o for o in manager_offers
                           if o.get("offer_id") == elegida.get("offer_id")
                           and o.get("player_id") == elegida.get("player_id")), None)
        r = cle.execute_competitive_live_action(
            selected_offer=oferta, rival_intelligence={}, execute=True)
    return {"eleccion": eleccion, "r": r, "enviados": enviados}


# ============================================================
# LA BATERIA Y SU HUELLA
# ============================================================

# Los 27 que enciende el YAML de produccion de origin/main (1ac6fd51,
# .github/workflows/bordalas-live.yml), contados con
# `el_paso_0.interruptores_encendidos_en`.
PRODUCCION = {n: "1" for n in (
    "BORDALAS_COBRA_LA_RACHA", "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA", "BORDALAS_EL_CIERRE_DE_LA_JORNADA",
    "BORDALAS_EL_INFORME_DE_LA_MANANA", "BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE",
    "BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR",
    "BORDALAS_EL_ONCE_UNA_VEZ", "BORDALAS_EL_PARTE_VENDE", "BORDALAS_JORNADAS_POR_SU_FECHA",
    "BORDALAS_LA_CARTERA", "BORDALAS_LA_JORNADA_DE_CADA_PAGINA",
    "BORDALAS_LA_MEJORA_DEL_ONCE", "BORDALAS_LA_MEJORA_SOLO_SI_SUBE",
    "BORDALAS_LA_MONEDA_DE_LA_LIGA", "BORDALAS_LA_ORDEN_DEL_GESTOR",
    "BORDALAS_LA_PUJA_EN_9900", "BORDALAS_LA_RONDA_DE_LA_MANANA", "BORDALAS_LA_ROTACION",
    "BORDALAS_LOS_CHOLLOS", "BORDALAS_REJA_CON_TOLERANCIA", "BORDALAS_REVENTA_SOLO_SI_JUEGA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL", "BORDALAS_REVISA_LAS_PUJAS_VIVAS",
    "BORDALAS_SIN_SUBASTA", "BORDALAS_SOLVENCIA_POR_SU_PLAZO", "BORDALAS_UN_SOLO_COLCHON",
)}
ENTORNOS = (("sin_interruptores", {}), ("produccion", PRODUCCION))

APAGADO = (None, "0", "", "off", "2")
ENCENDIDO = {**PRODUCCION, ENV: "1"}

# Las elegidas que llegan al ejecutor y lo que cambia en la foto fresca.
ELEGIDAS = (
    ("roberto_acepta", ROBERTO_ACEPTA), ("roberto_sacrificio", ROBERTO_SACRIFICIO),
    ("boye_contra", BOYE_CONTRA), ("iglesias_acepta", IGLESIAS_ACEPTA),
    ("iglesias_contra", IGLESIAS_CONTRA), ("yamal_acepta", YAMAL_ACEPTA),
    ("roberto_texto", ROBERTO_TEXTO), ("ninguna", None), ("kike_espera", KIKE_ESPERA),
    ("sin_offer_id", {**ROBERTO_ACEPTA, "offer_id": None}),
)
CAMBIOS = ("igual", "no_existe", "importe", "decision", "contra_cero", "debajo",
           "otro_jugador", "refresco_falla")


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


def _la_bateria(carpeta) -> list:
    """[(nombre, llamada)]: la eleccion, la sombra, el ejecutor y la
    vuelta, con la firma de main."""
    llamadas = []
    for nombre_orden, orden in ORDENES:
        ruta = _la_orden_en(carpeta, nombre_orden, orden)
        for nombre_lista, ofertas in LISTAS:
            for nombre_puerta, puerta in PUERTAS:
                llamadas.append((
                    f"eleccion/{nombre_lista}/{nombre_puerta}/{nombre_orden}",
                    lambda o=ofertas, p=puerta, r=ruta:
                    lambda entorno: _la_eleccion(o, p, r, entorno)))
                llamadas.append((
                    f"sombra/{nombre_lista}/{nombre_puerta}/{nombre_orden}",
                    lambda o=ofertas, p=puerta, r=ruta:
                    lambda entorno: _la_sombra(o, p, r, entorno)))
            for nombre_escritor, escritor in ESCRITORES:
                llamadas.append((
                    f"vuelta/{nombre_lista}/{nombre_escritor}/{nombre_orden}",
                    lambda o=ofertas, e=escritor, r=ruta:
                    lambda entorno: _la_vuelta(o, e, r, entorno)))
        for nombre_elegida, elegida in ELEGIDAS:
            llamadas.append((
                f"ensayo/{nombre_elegida}/{nombre_orden}",
                lambda o=elegida, r=ruta:
                lambda entorno: _el_ejecutor(o, "igual", ESCRITORES[2][1], r, entorno,
                                             execute=False)))
            for cambio in CAMBIOS:
                for nombre_escritor, escritor in ESCRITORES:
                    llamadas.append((
                        f"ejecutor/{nombre_elegida}/{cambio}/{nombre_escritor}/{nombre_orden}",
                        lambda o=elegida, c=cambio, e=escritor, r=ruta:
                        lambda entorno: _el_ejecutor(o, c, e, r, entorno)))
    return llamadas


LLAMADAS_DE_LA_BATERIA = len(ORDENES) * (
    len(LISTAS) * (2 * len(PUERTAS) + len(ESCRITORES))
    + len(ELEGIDAS) * (1 + len(CAMBIOS) * len(ESCRITORES)))


def _huellas(valores=APAGADO) -> dict:
    """{entorno/valor del interruptor: {llamada: sha256}}. El entorno se
    deja como estaba."""
    salida = {}
    with tempfile.TemporaryDirectory() as carpeta:
        bateria = _la_bateria(carpeta)
        for nombre_del_entorno, entorno in ENTORNOS:
            for valor in valores:
                huellas = {}
                for nombre, hacer in bateria:
                    texto = json.dumps(_normal(hacer()({**entorno, ENV: valor})),
                                       sort_keys=True, ensure_ascii=False, default=str)
                    huellas[nombre] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
                salida[f"{nombre_del_entorno}/{valor!r}"] = huellas
    return salida


def _la_huella(huellas: dict) -> str:
    """Una huella de todas: sha256 de las de cada llamada, en orden."""
    texto = "\n".join(f"{k} {v}" for k, v in sorted(huellas.items()))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# Medidas en main sin tocar (copia de origin/main 1ac6fd51 por `git
# archive`, con este fichero dentro) con `python -m
# src.analysis.test_la_orden_en_los_managers_v1 --medir`, una por Python y
# por entorno (sin interruptores y los 27 de produccion), con el
# interruptor sin poner, "0", "", "off" y "2" (las cinco, la misma).
# Cualquier cambio querido en el Safety Gate, la sombra, el ejecutor
# competitivo o el escritor la pone roja: se vuelve a medir en main, a
# proposito, en las dos versiones.
HUELLAS_DE_MAIN = {
    (3, 11): {
        "produccion": "d9b2b705404a308d44276308fe497a5e09b61126fbea5decafcd73d99dba815d",
        "sin_interruptores": "d9b2b705404a308d44276308fe497a5e09b61126fbea5decafcd73d99dba815d",
    },
    (3, 13): {
        "produccion": "d9b2b705404a308d44276308fe497a5e09b61126fbea5decafcd73d99dba815d",
        "sin_interruptores": "d9b2b705404a308d44276308fe497a5e09b61126fbea5decafcd73d99dba815d",
    },
}


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


def volcar(ruta) -> None:
    """Las huellas de cada llamada, apagada, a `ruta` (JSON), para
    comparar main y la rama llamada a llamada."""
    todas = _huellas(APAGADO)
    Path(ruta).write_text(json.dumps({"python": list(sys.version_info[:2]), "huellas": todas},
                                     indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Python {sys.version_info[:2]}: {sum(len(h) for h in todas.values())} "
          f"salidas en {ruta}")


# ============================================================
# LAS PRUEBAS
# ============================================================

def _texto(x) -> str:
    return json.dumps(_normal(x), sort_keys=True, ensure_ascii=False, default=str)


def _lista(nombre):
    return dict(LISTAS)[nombre]


def _escritor(nombre):
    return dict(ESCRITORES)[nombre]


def _escrituras(enviados) -> list:
    """Lo que de verdad se pidio a Biwenger (sin la creacion del
    escritor): (metodo, offer_id)."""
    salida = []
    for e in enviados:
        if e.get("metodo") == "CREA_EL_ESCRITOR":
            continue
        if e.get("metodo") in ("accept_offer", "counter_offer"):
            salida.append((e["metodo"], int(e["offer_id"])))
        elif e.get("metodo") == "PUT":
            salida.append(("accept_offer", int(e["url"].rsplit("/", 1)[1])))
        else:
            salida.append(("counter_offer", int(e["json"]["to"])))
    return salida


def _estados(eleccion) -> list:
    return [(e.get("player_id"), (e.get("gate") or {}).get("status"))
            for e in eleccion.get("evaluations") or []]


# 1. NACE APAGADO, UN LECTOR, SU FRASE, NADA AL IMPORTARSE

def test_nace_apagado_un_lector_y_su_frase():
    import ast
    from src.analysis import la_orden_en_los_managers as pieza
    from src.telemetry.el_tablon import QUE_HACE

    assert pieza.ENV == ENV
    for valor in (None, "0", "", "no", "false", "2", "off", " 0 "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is False, repr(valor)
    for valor in ("1", "true", "si", "yes", " SI ", "on", "sí", "Sí", " ON "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is True, repr(valor)

    # Un solo sitio lo lee: `activo`, y solo lo llama el propio modulo
    # (la eleccion y el ejecutor). Fuera, solo la frase del tablon.
    nombran = []
    for ruta in sorted(list((RAIZ / "src").rglob("*.py")) + list((RAIZ / "scripts").rglob("*.py"))):
        if ruta.name.startswith("test_"):
            continue
        if ENV in ruta.read_text(encoding="utf-8"):
            nombran.append(ruta.relative_to(RAIZ).as_posix())
    assert nombran == ["src/analysis/la_orden_en_los_managers.py",
                       "src/telemetry/el_tablon.py"], nombran
    fuente = (RAIZ / "src" / "analysis" / "la_orden_en_los_managers.py").read_text(
        encoding="utf-8")
    assert fuente.count(f'ENV = "{ENV}"') == 1
    assert fuente.count("os.environ.get(ENV") == 1
    assert fuente.count("activo()") - fuente.count("def activo()") == 2, \
        "activo() se llama en `la_eleccion` y en `lo_guarda_la_orden`"
    for ruta in (RAIZ / "src").rglob("*.py"):
        if ruta.name.startswith("test_") or ruta.name == "la_orden_en_los_managers.py":
            continue
        texto = ruta.read_text(encoding="utf-8")
        if "la_orden_en_los_managers" in texto:
            assert ".activo(" not in texto and "import activo" not in texto, ruta

    # Nada al importarse: ninguna sentencia de modulo llama al lector, mira
    # el entorno ni lee la orden.
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        if isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant):
            continue                                # el docstring
        texto = ast.dump(nodo)
        for prohibido in ("activo", "environ", "conservados", "protegidos",
                          "los_de_la_orden"):
            assert prohibido not in texto, ast.unparse(nodo)[:120]
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.ImportFrom):
            assert nodo.module == "__future__", ast.unparse(nodo)
        if isinstance(nodo, ast.Import):
            assert [a.name for a in nodo.names] == ["os"], ast.unparse(nodo)

    # Y el inventario de los interruptores lo ve leido al llamarse.
    from scripts.los_interruptores import lectores

    lee = lectores(RAIZ / "src" / "analysis" / "la_orden_en_los_managers.py")
    assert lee.get(ENV) == "AL_LLAMARSE", lee.get(ENV)

    frase = str(QUE_HACE.get(ENV) or "")
    for trozo in ("otro manager", "conservar o proteger", "ya no la acepta",
                  "contraoferta", "también es vender", "contesta a esa",
                  "antes de enviar nada a Biwenger", "«bloqueada por la orden»",
                  "apagada o caducada, todo como siempre"):
        assert trozo in frase, (trozo, frase)


def test_lo_que_el_paso_0_da_por_encendido():
    """Lo que el paso 0, el tablon, el panel y el ensayo dan por
    encendido (`el_paso_0.ENCENDIDO`), la pieza lo lee encendido, y al
    reves."""
    from src.analysis import el_paso_0
    from src.analysis import la_orden_en_los_managers as pieza

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
    """La bateria, con el interruptor sin poner, "0", "", "off" y "2",
    sin interruptores y con los 27 de produccion: la huella de main,
    medida antes de tocar el codigo, en esta version de Python."""
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


# 3. EL CASO, ACEPTAR: ROBERTO (conservar; «No lo vendas de momento»)

def test_el_caso_aceptar_a_roberto():
    """Un manager ofrece por Roberto y Competitive dice ACCEPT_NOW (o
    ACCEPT_SACRIFICE_LINEUP, o el id llega como texto). Apagado (main):
    se elige y se llama a `accept_offer`. Encendido: no se elige, la
    vuelta no crea el escritor y no acepta nada."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for oferta in (ROBERTO_ACEPTA, ROBERTO_SACRIFICIO, ROBERTO_TEXTO):
            for nombre, escritor in ESCRITORES:
                off = _la_vuelta([oferta], escritor, ruta, PRODUCCION)
                on = _la_vuelta([oferta], escritor, ruta, ENCENDIDO)
                assert (off["eleccion"]["selected"] or {}).get("offer_id") == \
                    oferta["offer_id"], off["eleccion"]
                assert _escrituras(off["enviados"]) == \
                    [("accept_offer", oferta["offer_id"])], (nombre, off["enviados"])
                assert off["r"]["write_performed"] is True, off["r"]

                assert on["eleccion"]["selected"] is None, on["eleccion"]
                assert on["eleccion"]["authorized_count"] == 0, on["eleccion"]
                gate = on["eleccion"]["evaluations"][0]["gate"]
                assert gate["status"] == "BLOCK_LA_ORDEN_DEL_GESTOR", gate
                assert gate["authorized"] is False and gate["would_execute"] is False, gate
                assert gate["guardia"] == "LA_ORDEN_EN_LOS_MANAGERS", gate
                assert gate["status_sin_la_orden"] == "ALLOW_DRY_RUN", gate
                assert gate["decision"] == oferta["authoritative_decision"], gate
                assert [f["player_id"] for f in on["eleccion"]["no_se_responden"]] == \
                    [ROBERTO], on["eleccion"]
                assert on["enviados"] == [], (nombre, on["enviados"])
                assert on["r"]["status"] == "NO_COMPETITIVE_ACTION", on["r"]
                assert on["r"]["write_performed"] is False, on["r"]


# 4. EL CASO, CONTRAOFERTAR: BOYE (proteger)

def test_el_caso_contraofertar_a_boye():
    """COUNTER_OFFER por Boye (una contraoferta aceptada por el rival
    tambien es vender). Apagado: `counter_offer` por 6.450.000.
    Encendido: ni se elige ni se llama a `counter_offer`. El lunes 09/11
    (Boye fuera de `proteger`, sigue en `conservar`): igual."""
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden, orden in (("hoy", ORDEN_HOY), ("sin_boye", ORDEN_SIN_BOYE)):
            ruta = _la_orden_en(carpeta, nombre_orden, orden)
            for nombre, escritor in ESCRITORES:
                off = _la_vuelta([BOYE_CONTRA], escritor, ruta, PRODUCCION)
                on = _la_vuelta([BOYE_CONTRA], escritor, ruta, ENCENDIDO)
                assert _escrituras(off["enviados"]) == [("counter_offer", 70003)], \
                    off["enviados"]
                if nombre == "real_200":
                    assert off["enviados"][-1]["json"] == {
                        "type": "counterOffer", "to": 70003, "amount": 6_450_000}
                    assert off["r"]["status"] == "COMPETITIVE_COUNTER_SENT", off["r"]
                assert on["enviados"] == [], (nombre_orden, nombre, on["enviados"])
                assert on["eleccion"]["selected"] is None, on["eleccion"]
                assert _estados(on["eleccion"]) == [(BOYE, "BLOCK_LA_ORDEN_DEL_GESTOR")]
                assert on["r"]["status"] == "NO_COMPETITIVE_ACTION", on["r"]


# 5. LA SIGUIENTE SE QUEDA LA VUELTA

def test_la_siguiente_se_queda_la_vuelta():
    """Roberto y luego Iglesias; Boye y luego Iglesias; la mezcla del
    Safety Gate. Apagado se contesta la primera (la de la orden).
    Encendido, la siguiente autorizada: Iglesias. La sombra V1.9 elige
    lo mismo."""
    casos = (
        ("roberto_luego_iglesias", ("accept_offer", 70001), ("accept_offer", 70004)),
        ("boye_luego_iglesias", ("counter_offer", 70003), ("counter_offer", 70005)),
        ("mezcla", ("accept_offer", 70002), ("counter_offer", 70005)),
    )
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for nombre_lista, de_main, encendido in casos:
            ofertas = _lista(nombre_lista)
            for nombre, escritor in ESCRITORES:
                off = _la_vuelta(ofertas, escritor, ruta, PRODUCCION)
                on = _la_vuelta(ofertas, escritor, ruta, ENCENDIDO)
                assert _escrituras(off["enviados"]) == [de_main], (nombre_lista, off)
                assert _escrituras(on["enviados"]) == [encendido], (nombre_lista, on)
                assert on["eleccion"]["selected"]["player_id"] == IGLESIAS
                frenadas = on["eleccion"]["no_se_responden"]
                assert len(frenadas) == (2 if nombre_lista == "mezcla" else 1), frenadas
                assert on["eleccion"]["authorized_count"] == \
                    off["eleccion"]["authorized_count"] - len(frenadas)
                assert on["eleccion"]["evaluated_count"] == off["eleccion"]["evaluated_count"]
                if nombre == "mentira":
                    assert on["r"]["status"] in ("COMPETITIVE_OFFER_ACCEPTED",
                                                 "COMPETITIVE_COUNTER_SENT"), on["r"]
                    assert on["r"]["player_id"] == IGLESIAS, on["r"]
            sombra_off = _la_sombra(ofertas, PUERTAS[0][1], ruta, PRODUCCION)
            sombra_on = _la_sombra(ofertas, PUERTAS[0][1], ruta, ENCENDIDO)
            assert sombra_off["sombra"]["shadow_decision"]["player_id"] in (ROBERTO, BOYE)
            assert sombra_on["sombra"]["shadow_decision"]["player_id"] == IGLESIAS
            assert sombra_on["ejecucion"]["write_performed"] is False

        # En la mezcla, solo cambian las autorizadas de la orden: las que
        # el Safety Gate ya frenaba (Chust NEVER_SELL, Kike, Ivan, Dani,
        # Gulacsi) salen como en main.
        on = _la_eleccion(_lista("mezcla"), PUERTAS[0][1], ruta, ENCENDIDO)
        off = _la_eleccion(_lista("mezcla"), PUERTAS[0][1], ruta, PRODUCCION)
        cambian = [(a, b) for a, b in zip(_estados(off), _estados(on)) if a != b]
        assert cambian == [((ROBERTO, "ALLOW_DRY_RUN"), (ROBERTO, "BLOCK_LA_ORDEN_DEL_GESTOR")),
                           ((BOYE, "ALLOW_DRY_RUN"), (BOYE, "BLOCK_LA_ORDEN_DEL_GESTOR"))], cambian
        assert dict(_estados(on))[CHUST] == "BLOCK_NEVER_SELL"
        assert [f["player_id"] for f in on["no_se_responden"]] == [ROBERTO, BOYE]
        for a, b in zip(off["evaluations"], on["evaluations"]):
            if a["gate"]["status"] != "ALLOW_DRY_RUN" or a["player_id"] == IGLESIAS:
                assert _texto(a) == _texto(b), (a, b)


# 6. UN JUGADOR QUE LA ORDEN NO GUARDA: IGUAL QUE MAIN

def test_un_jugador_libre_igual_que_main():
    """Juan Iglesias no esta en la orden: encendido, la eleccion, la
    sombra, el ejecutor y la vuelta son las de main, byte a byte (sin
    `no_se_responden`)."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for ofertas in ([IGLESIAS_ACEPTA], [IGLESIAS_CONTRA],
                        [IGLESIAS_ACEPTA, IGLESIAS_CONTRA], [SIN_ID, ID_RARO, ID_BOOL]):
            for _, puerta in PUERTAS:
                on = _la_eleccion(ofertas, puerta, ruta, ENCENDIDO)
                assert _texto(on) == _texto(_la_eleccion(ofertas, puerta, ruta, PRODUCCION))
                assert "no_se_responden" not in on
                assert _texto(_la_sombra(ofertas, puerta, ruta, ENCENDIDO)) == \
                    _texto(_la_sombra(ofertas, puerta, ruta, PRODUCCION))
            for _, escritor in ESCRITORES:
                on = _la_vuelta(ofertas, escritor, ruta, ENCENDIDO)
                assert _texto(on) == _texto(_la_vuelta(ofertas, escritor, ruta, PRODUCCION))
        for oferta in (IGLESIAS_ACEPTA, IGLESIAS_CONTRA):
            for cambio in CAMBIOS:
                for _, escritor in ESCRITORES:
                    on = _el_ejecutor(oferta, cambio, escritor, ruta, ENCENDIDO)
                    off = _el_ejecutor(oferta, cambio, escritor, ruta, PRODUCCION)
                    assert _texto(on) == _texto(off), (oferta["offer_id"], cambio)
        r = _la_vuelta([IGLESIAS_ACEPTA], _escritor("mentira"), ruta, ENCENDIDO)
        assert _escrituras(r["enviados"]) == [("accept_offer", 70004)], r


# 7. SIN ORDEN QUE MIRAR: IGUAL QUE MAIN

def test_sin_orden_que_mirar_igual_que_main():
    """Encendido con la orden caducada, sin fichero, ilegible, o con la
    orden del gestor apagada (ni este interruptor sirve sin ella): toda la
    bateria es la de main, llamada a llamada."""
    sin_la_orden = {**ENCENDIDO, ENV_ORDEN: None}
    with tempfile.TemporaryDirectory() as carpeta:
        bateria = _la_bateria(carpeta)
        rutas = {n: _la_orden_en(carpeta, n, o) for n, o in ORDENES}
        assert not rutas["sin_orden"].exists()
        comparadas = 0
        for nombre, hacer in bateria:
            orden = nombre.rsplit("/", 1)[1]
            if orden in ("caducada", "sin_orden", "ilegible"):
                assert _texto(hacer()(ENCENDIDO)) == _texto(hacer()(PRODUCCION)), nombre
                comparadas += 1
            elif orden == "hoy":
                assert _texto(hacer()(sin_la_orden)) == _texto(hacer()(PRODUCCION)), nombre
                comparadas += 1
        assert comparadas == 4 * LLAMADAS_DE_LA_BATERIA // len(ORDENES), comparadas


# 8. EL EJECUTOR: DEFENSA EN PROFUNDIDAD

def test_el_ejecutor_defensa_en_profundidad():
    """Si la oferta de Roberto o de Boye llega igual al ejecutor (otra
    version de la eleccion, una elegida a mano), encendido, despues de
    revalidar y ANTES de crear el escritor: COMPETITIVE_BLOCKED_LA_ORDEN,
    `success` False, `write_performed` False y la `guardia`. Apagado,
    main: se escribe."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for oferta in (ROBERTO_ACEPTA, ROBERTO_SACRIFICIO, BOYE_CONTRA, ROBERTO_TEXTO,
                       YAMAL_ACEPTA):
            for nombre, escritor in ESCRITORES:
                off = _el_ejecutor(oferta, "igual", escritor, ruta, PRODUCCION)
                on = _el_ejecutor(oferta, "igual", escritor, ruta, ENCENDIDO)
                assert off["r"]["write_performed"] is True, off["r"]
                assert len(_escrituras(off["enviados"])) == 1, off["enviados"]
                r = on["r"]
                assert on["enviados"] == [], on["enviados"]     # ni se crea
                assert r["status"] == "COMPETITIVE_BLOCKED_LA_ORDEN", r
                assert r["success"] is False and r["write_performed"] is False, r
                assert r["guardia"] == "LA_ORDEN_EN_LOS_MANAGERS", r
                assert r["player_id"] == int(oferta["player_id"]), r
                assert r["offer_id"] == oferta["offer_id"], r
                assert r["action"] == oferta["authoritative_decision"], r
                assert r["revalidation_snapshot"] == FOTO_FRESCA, r
                assert r["http_status"] is None and r["response"] is None, r
                assert r["reason"].startswith("LA_ORDEN_DEL_GESTOR: "), r
            # Lo que la revalidacion ya frena antes, sale igual que en
            # main (va primero); lo que frenaria despues (contraoferta
            # sin importe, aceptar por debajo), lo frena la orden antes.
            for cambio in CAMBIOS:
                on = _el_ejecutor(oferta, cambio, _escritor("mentira"), ruta, ENCENDIDO)
                off = _el_ejecutor(oferta, cambio, _escritor("mentira"), ruta, PRODUCCION)
                assert on["enviados"] == [], (cambio, on)
                if cambio in ("no_existe", "importe", "decision", "otro_jugador",
                              "refresco_falla"):
                    assert _texto(on) == _texto(off), (cambio, on, off)
                else:
                    assert on["r"]["status"] == "COMPETITIVE_BLOCKED_LA_ORDEN", (cambio, on)
            # El ensayo (`execute=False`) no escribe: igual que main.
            on = _el_ejecutor(oferta, "igual", _escritor("mentira"), ruta, ENCENDIDO,
                              execute=False)
            off = _el_ejecutor(oferta, "igual", _escritor("mentira"), ruta, PRODUCCION,
                               execute=False)
            assert _texto(on) == _texto(off) and on["r"]["status"] == "COMPETITIVE_DRY_RUN"
        # Sin oferta, sin accion soportada o sin offer_id: igual que main.
        for oferta in (None, KIKE_ESPERA, {**ROBERTO_ACEPTA, "offer_id": None}):
            on = _el_ejecutor(oferta, "igual", _escritor("mentira"), ruta, ENCENDIDO)
            off = _el_ejecutor(oferta, "igual", _escritor("mentira"), ruta, PRODUCCION)
            assert _texto(on) == _texto(off) and on["enviados"] == [], on


# 9. LA MISMA PUERTA: conservados() | protegidos()

def test_la_misma_puerta_que_la_orden():
    """Los que se frenan (en la eleccion y en el ejecutor) son
    exactamente `conservados() | protegidos()` de la orden, jugador a
    jugador y orden a orden; `los_de_la_orden` las llama sin argumentos
    (la orden de `config/`, a la hora de ahora)."""
    import src.actions.la_orden_del_gestor as orden_mod
    from src.analysis import la_orden_en_los_managers as pieza

    fuente = (RAIZ / "src" / "analysis" / "la_orden_en_los_managers.py").read_text(
        encoding="utf-8")
    assert "from src.actions.la_orden_del_gestor import conservados, protegidos" in fuente
    assert "conservados() or ()" in fuente and "protegidos() or ()" in fuente

    jugadores = (BOYE, CHUST, YAMAL, ROBERTO, IVAN, KIKE, OLASAGASTI, GULACSI, CARDONA,
                 RAMON, IGLESIAS, DANI, 41031, 1721)
    extra = {**ORDEN_HOY, "fichar": [{"player_id": DANI, "nombre": "Dani Lorenzo",
                                      "puja": 2_100_000}],
             "conservar": [], "proteger": [{"player_id": BOYE, "nombre": "Boyé"}]}
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden, orden in ORDENES + (("solo_proteger_y_fichar", extra),):
            ruta = _la_orden_en(carpeta, nombre_orden, orden)
            with _Interruptores({ENV_ORDEN: "1"}):
                esperados = (set(orden_mod.conservados(ruta, AHORA))
                             | set(orden_mod.protegidos(ruta, AHORA)))
            with _Interruptores(ENCENDIDO), _Sustituye(_la_orden_de_mentira(ruta)):
                assert pieza.los_de_la_orden() == frozenset(esperados), nombre_orden
            for pid in jugadores:
                oferta = {**IGLESIAS_ACEPTA, "player_id": pid, "offer_id": 80000 + pid % 1000}
                on = _la_vuelta([oferta], _escritor("mentira"), ruta, ENCENDIDO)
                frenada = not _escrituras(on["enviados"])
                assert frenada is (pid in esperados), (nombre_orden, pid, on)
                r = _el_ejecutor(oferta, "igual", _escritor("mentira"), ruta, ENCENDIDO)
                assert (r["r"]["status"] == "COMPETITIVE_BLOCKED_LA_ORDEN") is \
                    (pid in esperados), (nombre_orden, pid, r)
        # La ultima (solo `proteger` y `fichar`): Boye y Dani (los dos
        # vienen de `protegidos()`; `conservados()` los incluye).
        assert esperados == {BOYE, DANI}, esperados
        # Con la orden de hoy: Yamal, Boye y los nueve de `conservar`.
        with _Interruptores({ENV_ORDEN: "1"}):
            ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
            hoy = set(orden_mod.conservados(ruta, AHORA)) | set(orden_mod.protegidos(ruta, AHORA))
        assert hoy == {BOYE, CHUST, YAMAL, ROBERTO, IVAN, KIKE, OLASAGASTI, GULACSI,
                       CARDONA, RAMON}, hoy


# 10. NADA MAS CAMBIA

def test_nada_mas_cambia():
    """EL_RELEVO sigue primero en el ejecutor; NEVER_SELL, NEVER_AUTO_SELL
    y el cierre temporal, como en main (Yamal no se vende nunca: ni
    encendido ni apagado); el Safety Gate por oferta no se toca."""
    import src.actions.la_mejora_del_once as mejora
    from src.analysis.competitive_safety_gate import evaluate_competitive_safety_gate

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        # EL_RELEVO primero: Roberto entra por un cambio vivo de la mejora.
        with _Sustituye([(mejora, "los_que_entran", lambda *a, **k: frozenset({ROBERTO}))]):
            for entorno in (PRODUCCION, ENCENDIDO):
                r = _el_ejecutor(ROBERTO_ACEPTA, "igual", _escritor("mentira"), ruta, entorno)
                assert r["r"]["status"] == "COMPETITIVE_BLOCKED_EL_RELEVO", r
                assert r["r"]["guardia"] == "EL_RELEVO" and r["enviados"] == [], r
            on = _el_ejecutor(BOYE_CONTRA, "igual", _escritor("mentira"), ruta, ENCENDIDO)
            assert on["r"]["status"] == "COMPETITIVE_BLOCKED_LA_ORDEN", on

        # Yamal, NEVER_AUTO_SELL: nunca se elige ni se vende.
        for entorno in (PRODUCCION, ENCENDIDO):
            for ofertas in ([YAMAL_ACEPTA], _lista("yamal_y_roberto")):
                v = _la_vuelta(ofertas, _escritor("mentira"), ruta, entorno)
                assert ("accept_offer", 70006) not in _escrituras(v["enviados"]), v
                assert dict(_estados(v["eleccion"]))[YAMAL] == "BLOCK_PROTECTED_PLAYER"
        # Sin la proteccion del roster (de la prueba): main lo aceptaria;
        # encendido, `proteger` lo frena.
        off = _la_vuelta([YAMAL_SIN_PROTECCION], _escritor("mentira"), ruta, PRODUCCION)
        on = _la_vuelta([YAMAL_SIN_PROTECCION], _escritor("mentira"), ruta, ENCENDIDO)
        assert _escrituras(off["enviados"]) == [("accept_offer", 70007)], off
        assert on["enviados"] == [] and on["eleccion"]["selected"] is None, on

        # El cierre temporal: todo frenado antes; igual que main.
        for _, ofertas in LISTAS:
            puerta = PUERTAS[1][1]
            assert _texto(_la_eleccion(ofertas, puerta, ruta, ENCENDIDO)) == \
                _texto(_la_eleccion(ofertas, puerta, ruta, PRODUCCION))
            v = _la_vuelta(ofertas, _escritor("mentira"), ruta, ENCENDIDO, puerta=puerta)
            assert v["enviados"] == [] and v["r"]["status"] == "NO_COMPETITIVE_ACTION"

        # El Safety Gate por oferta, el de siempre (no mira la orden).
        for oferta in (ROBERTO_ACEPTA, BOYE_CONTRA, CHUST_NUNCA, YAMAL_ACEPTA):
            with _Interruptores(ENCENDIDO), _Sustituye(_la_orden_de_mentira(ruta)):
                on = evaluate_competitive_safety_gate(
                    offer=copy.deepcopy(oferta), temporal_gate=PUERTAS[0][1],
                    current_balance=SALDO)
            with _Interruptores(PRODUCCION):
                off = evaluate_competitive_safety_gate(
                    offer=copy.deepcopy(oferta), temporal_gate=PUERTAS[0][1],
                    current_balance=SALDO)
            assert on == off, (on, off)


# 11. HOY (20:07): 0 OFERTAS DE MANAGERS

def test_hoy_cero_ofertas_de_managers():
    """La vuelta de las 20:07: ninguna oferta de managers. Encendido y
    apagado, nada que elegir ni escribir, y la orden ni se lee."""
    import src.actions.la_orden_del_gestor as orden_mod

    leidas = []

    def _apunta(f):
        return lambda *a, **k: leidas.append(f.__name__) or f(*a, **k)

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for _, escritor in ESCRITORES:
            off = _la_vuelta([], escritor, ruta, PRODUCCION)
            with _Sustituye([(orden_mod, n, _apunta(getattr(orden_mod, n)))
                             for n in ("conservados", "protegidos")]):
                on = _la_vuelta([], escritor, ruta, ENCENDIDO)
            assert _texto(on) == _texto(off)
            assert on["enviados"] == [] and on["r"]["status"] == "NO_COMPETITIVE_ACTION"
            assert on["eleccion"]["evaluated_count"] == 0
    assert leidas == [], leidas


# 12. NUNCA LANZA

def test_nunca_lanza():
    from src.analysis import la_orden_en_los_managers as pieza
    import src.actions.la_orden_del_gestor as orden_mod

    def _revienta(*a, **k):
        raise RuntimeError("la orden no se puede leer")

    autorizada = {"player_id": ROBERTO, "gate": {"authorized": True, "status": "ALLOW_DRY_RUN",
                                                 "decision": "ACCEPT_NOW"}}
    raras = [None, "x", 7, {}, {"gate": "no-es-un-dict"}, {"player_id": ROBERTO},
             {"player_id": "no-es-un-id", "gate": {"authorized": True}},
             {"player_id": True, "gate": {"authorized": True}}, autorizada]
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        with _Interruptores(ENCENDIDO), _Sustituye(_la_orden_de_mentira(ruta)):
            r = pieza.la_eleccion(raras)
            assert [e for e in r["evaluations"][:-1]] == raras[:-1], r
            assert r["evaluations"][-1]["gate"]["status"] == "BLOCK_LA_ORDEN_DEL_GESTOR", r
            assert [f["player_id"] for f in r["no_se_responden"]] == [ROBERTO], r
            assert all(a is b for a, b in zip(r["evaluations"][:-1], raras[:-1]))
            for mala in (None, "texto", 7, {"a": 1}, (autorizada,), [], [None]):
                assert pieza.la_eleccion(mala) is None, mala
            for ids in ((), (None,), ("x",), (0,), (-ROBERTO,), (True,), (object(),),
                        (float("nan"),), (float("inf"),)):
                assert pieza.lo_guarda_la_orden(*ids) is False, ids
            assert pieza.lo_guarda_la_orden(0, ROBERTO) is True
            assert pieza.lo_guarda_la_orden(str(ROBERTO)) is True
            assert pieza.lo_guarda_la_orden(IGLESIAS) is False
        with _Interruptores({ENV: None, ENV_ORDEN: "1"}), _Sustituye(_la_orden_de_mentira(ruta)):
            assert pieza.la_eleccion([autorizada]) is None
            assert pieza.lo_guarda_la_orden(ROBERTO) is False
        # La orden que revienta: vacio, y la eleccion y el ejecutor de main.
        with _Interruptores(ENCENDIDO), _Sustituye(
                [(orden_mod, n, _revienta) for n in ("conservados", "protegidos")]):
            assert pieza.los_de_la_orden() == frozenset()
            assert pieza.la_eleccion([autorizada]) is None
            assert pieza.lo_guarda_la_orden(ROBERTO) is False
        revienta = [(orden_mod, n, _revienta) for n in ("conservados", "protegidos")]
        for ofertas in (_lista("roberto_acepta"), _lista("mezcla")):
            off = _la_vuelta(ofertas, _escritor("mentira"), ruta, PRODUCCION)
            with _Sustituye(revienta):
                import src.analysis.competitive_live_executor as cle
                from src.analysis.competitive_safety_gate import select_single_competitive_action
                enviados = []
                with _Interruptores(ENCENDIDO), _Sustituye(_el_ejecutor_de_mentira(
                        _tablero_fresco(ofertas), _escritor_de_mentira(enviados))):
                    eleccion = select_single_competitive_action(
                        offers=copy.deepcopy(ofertas), temporal_gate=PUERTAS[0][1],
                        current_balance=SALDO)
                    oferta = next(o for o in ofertas
                                  if o["offer_id"] == eleccion["selected"]["offer_id"])
                    r = cle.execute_competitive_live_action(
                        selected_offer=copy.deepcopy(oferta), rival_intelligence={},
                        execute=True)
            assert _texto({"eleccion": eleccion, "r": r, "enviados": enviados}) == _texto(off)


# 12b. SI NO SE PUDIERA IMPORTAR, LO DE SIEMPRE

def test_si_no_se_importa_lo_de_siempre():
    """En los dos enganches la pieza se importa dentro de un `try`; en el
    ejecutor, despues de EL_RELEVO y ANTES de crear el escritor. Si no se
    pudiera importar, encendido es main."""
    ejecutor = (RAIZ / "src" / "analysis" / "competitive_live_executor.py").read_text(
        encoding="utf-8")
    relevo = ejecutor.index('"COMPETITIVE_BLOCKED_EL_RELEVO"')
    importa = ejecutor.index("from src.analysis.la_orden_en_los_managers import")
    crea = ejecutor.index("BiwengerWriteClient()")
    acepta = ejecutor.index("writer.accept_offer(")
    contra = ejecutor.index("writer.counter_offer(")
    assert relevo < importa < crea < contra < acepta, (relevo, importa, crea, contra, acepta)
    assert ejecutor.count("la_orden_en_los_managers import") == 1
    assert ejecutor[:importa].rstrip().endswith("try:"), ejecutor[importa - 80:importa]
    puerta = (RAIZ / "src" / "analysis" / "competitive_safety_gate.py").read_text(
        encoding="utf-8")
    importa = puerta.index("from src.analysis.la_orden_en_los_managers import")
    assert puerta.count("la_orden_en_los_managers import") == 1
    assert puerta[:importa].rstrip().endswith("try:"), puerta[importa - 80:importa]
    assert importa < puerta.index("    authorized = [", importa)

    import src.analysis.la_orden_en_los_managers  # noqa: F401  (ya cargada)

    nombre = "src.analysis.la_orden_en_los_managers"
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        de_main = [_la_vuelta(o, _escritor("mentira"), ruta, PRODUCCION)
                   for o in (_lista("roberto_acepta"), _lista("mezcla"))]
        ejec_main = _el_ejecutor(BOYE_CONTRA, "igual", _escritor("mentira"), ruta, PRODUCCION)
        antes = sys.modules.get(nombre)
        sys.modules[nombre] = None                  # la importacion falla
        try:
            vueltas = [_la_vuelta(o, _escritor("mentira"), ruta, ENCENDIDO)
                       for o in (_lista("roberto_acepta"), _lista("mezcla"))]
            ejec = _el_ejecutor(BOYE_CONTRA, "igual", _escritor("mentira"), ruta, ENCENDIDO)
        finally:
            if antes is None:
                sys.modules.pop(nombre, None)
            else:
                sys.modules[nombre] = antes
    assert sys.modules.get(nombre) is antes
    for vuelta, main_ in zip(vueltas, de_main):
        assert _texto(vuelta) == _texto(main_)
    assert _texto(ejec) == _texto(ejec_main)
    assert ejec["r"]["status"] == "COMPETITIVE_COUNTER_SENT", ejec


# 13. EL ENTORNO NO DECIDE (doctrina 104)

def test_el_entorno_no_decide_esta_guardia():
    """Con todo lo de fuera puesto (los del tablon, este incluido, el
    ensayo, el relevo, uno que no existe), cada prueba da lo mismo, y al
    salir el entorno es el de antes."""
    from src.analysis.el_paso_0 import PREFIJO
    from src.telemetry.el_tablon import QUE_HACE

    de_fuera = {n: "1" for n in QUE_HACE if n.startswith(PREFIJO)}
    de_fuera.update({PREFIJO + "SIN_REVENTA": "1", PREFIJO + "BID_SALT": "otra-sal",
                     PREFIJO + "LA_HUCHA": "1", PREFIJO + "ENSAYO": "1",
                     ENV_RELEVO: "1", ENV_MEJORA: "1",
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
    test_el_caso_aceptar_a_roberto,
    test_el_caso_contraofertar_a_boye,
    test_la_siguiente_se_queda_la_vuelta,
    test_un_jugador_libre_igual_que_main,
    test_sin_orden_que_mirar_igual_que_main,
    test_el_ejecutor_defensa_en_profundidad,
    test_la_misma_puerta_que_la_orden,
    test_nada_mas_cambia,
    test_hoy_cero_ofertas_de_managers,
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
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
