"""
EL PROTEGIDO NO GASTA LA VUELTA (04/11/2026). Guardias de
`BORDALAS_EL_PROTEGIDO_NO_GASTA_LA_VUELTA`
(`src/analysis/el_protegido_no_gasta_la_vuelta.py` y sus dos enganches:
el plan de `decision_orchestrator.build_global_decision_uncached` y la
renovacion de `autopilot_executor.execute_autopilot_decision`).

EL CASO (supervision del 04/11 08:22)

    Boye (12494) esta en `proteger` de la orden del gestor hasta el lun
    09/11. Su publicacion caducaba el 04/11 ~09:10 y la de Chust (1760),
    ~10:10. El autopilot viejo propone UNA renovacion por vuelta, la mas
    urgente: Boye, primero en la cola ordenada por caducidad. El
    ejecutor la manda, la guarda del escritor la frena antes de enviar
    nada (`blocked: PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR`), y el ejecutor:

      1. tira el `blocked` y dice «Biwenger no confirmo la renovacion»
         (falso: no se envio nada);
      2. la cuenta como fallo: backoff de 30 min, 1 h, 2 h... (07:15,
         08:07, 10:07);
      3. devuelve `write_performed: True` sin haber escrito: la vuelta
         pierde su UNICA escritura (BUY V10, la contraoferta y la salida
         de V10 no corren; el competitivo dice
         BLOCKED_LEGACY_ALREADY_WROTE).

    Y Chust no se renueva nunca: con Boye en backoff (09:07) el plan no
    propone ninguna renovacion (solo la primera), y su publicacion
    caduca a las 10:10.

QUE SE COMPRUEBA

    1. Nace apagado, se lee en UN sitio (`activo`, al llamarse, solo
       desde el propio modulo), vale lo mismo que `el_paso_0.ENCENDIDO`,
       tiene frase en QUE_HACE y no hace nada al importarse.
    2. Apagado es main byte a byte: la huella de la bateria (el plan del
       orquestador, el resultado del ejecutor con el escritor real sin
       red y con los de mentira, lo que apunta el backoff y lo que leen
       los consumidores de V10), sobre los estados compactados de hoy
       (07:15, 08:07, 09:07 con Boye en backoff, 10:07 con las dos
       caducadas, Chust primero, solo Boye, sin prisa y sin nada que
       renovar), con la orden de hoy, sin Boye, caducada, sin orden y
       con Boye y Chust protegidos; con el interruptor sin poner, "0" y
       "", sin interruptores y con los 26 del YAML de produccion
       (origin/main e5a51e88). La de main, medida antes de tocar el
       codigo, una por version de Python (3.11 y 3.13).
    3. EL CASO DE HOY, EL PLAN: encendido, Boye protegido y primero en
       la cola, la renovacion que entra es la de Chust (07:15, 08:07,
       09:07 y 10:07). Apagado, Boye (o nada a las 09:07).
    4. EL CASO DE HOY, LA VUELTA: si la guarda frena igual, encendido:
       `write_performed` False, status BLOCKED, el `blocked` en el
       resultado y en el motivo («BLOQUEADA_POR_LA_ORDEN: ...»), nada
       enviado a Biwenger, el backoff no apunta nada y V10 ve la vuelta
       libre. Apagado, lo de main (FAILED, escritura gastada, backoff).
    5. La misma puerta que el escritor: los que el plan quita son
       exactamente los que `list_player_for_sale` frena, jugador a
       jugador, con cada orden. Y la guarda sigue en su sitio.
    6. Sin protegido que quitar (orden sin Boye, caducada, sin orden,
       orden apagada) el plan encendido es el de main.
    7. Lo que se envia sigue siendo escritura: Chust renovado (204), el
       rechazo (400), el ensayo y la publicacion de liquidez, igual que
       en main.
    8. Ninguna renovacion que hacer: solo Boye, o Boye y Chust
       protegidos; la vuelta pasa a la siguiente accion.
    9. La venta del protegido: una oferta aprobada de Boye no es la que
       se cobra; se cobra la siguiente (Iglesias).
   10. Nunca lanza.
   11. El entorno no la decide (doctrina 104).

DE DONDE SALEN LOS NUMEROS

    Compactado de los artefactos de produccion del 04/11: las runs
    41784326165 (07:15), 41790042877 (08:07), 41797056440 (09:07, solo
    el log) y 41804815503 (10:07): las publicaciones (precio, horas),
    las ofertas del Computer, el saldo (+2.025.724), la puja viva por
    Loureiro (798.000) y el backoff de Boye (1, 2 y 3 fallos). Los
    valores de mercado de Boye (5.370.000) y Chust (2.720.000), del
    bloque `renovacion` de las 10:07. Ni `data/`, ni la red, ni el reloj:
    la hora se pasa, la orden va a una carpeta temporal y se lee con la
    funcion real (`la_orden_del_gestor.protegidos(ruta, ahora)`), el
    escritor es el real sin red (una sesion de mentira) o uno de
    mentira, y el backoff se apunta en memoria.

COMO SE USA

    python -m src.analysis.test_el_protegido_no_gasta_la_vuelta_v1
    python -m src.analysis.test_el_protegido_no_gasta_la_vuelta_v1 --medir
    python -m src.analysis.test_el_protegido_no_gasta_la_vuelta_v1 --volcar FICHERO
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile

from datetime import date, datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


ENV = "BORDALAS_EL_PROTEGIDO_NO_GASTA_LA_VUELTA"

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
LOUREIRO = 41031

_UTC = timezone.utc

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

ORDEN_BOYE_Y_CHUST = {**ORDEN_HOY, "proteger": ORDEN_HOY["proteger"]
                      + [{"player_id": CHUST, "nombre": "Chust"}]}

# `None`: no hay fichero.
ORDENES = (("hoy", ORDEN_HOY), ("sin_boye", ORDEN_SIN_BOYE),
           ("caducada", ORDEN_CADUCADA), ("sin_orden", None),
           ("boye_y_chust", ORDEN_BOYE_Y_CHUST))


# ============================================================
# LAS PUBLICACIONES (MARKET LISTING LIFECYCLE)
# ============================================================

# (player_id, nombre, publicado, valor de mercado)
BOYE_P = (BOYE, "Boyé", 6_450_000, 5_370_000)
CHUST_P = (CHUST, "Chust", 2_560_000, 2_720_000)

# Las otras nueve, sanas (horas de las 08:07).
SANAS = (
    (RAMON, "Ramón Enríquez", 430_000, 440_000, 25.0),
    (OLASAGASTI, "Olasagasti", 3_470_000, 2_840_000, 28.0),
    (CARDONA, "Sergi Cardona", 2_160_000, 2_170_000, 29.0),
    (ROBERTO, "Roberto Fernández", 10_200_000, 6_990_000, 30.0),
    (GULACSI, "Gulácsi", 2_980_000, 2_230_000, 31.0),
    (IVAN, "Iván Martín", 3_280_000, 2_700_000, 33.0),
    (IGLESIAS, "Juan Iglesias", 4_550_000, 3_800_000, 34.0),
    (KIKE, "Kike Salas", 4_110_000, 3_470_000, 35.0),
    (DANI, "Dani Lorenzo", 2_420_000, 2_010_000, 36.0),
)

HORAS_DE_RENOVAR = 20.0      # no llega al final del siguiente ciclo
HORAS_URGENTES = 3.0         # RENEW_URGENT_HOURS


def _publicacion(pid, nombre, precio, valor, horas) -> dict:
    renovar = horas < HORAS_DE_RENOVAR
    return {
        "player_id": pid,
        "name": nombre,
        "listed_price": precio,
        "hours_to_expiry": horas,
        "expired": horas <= 0,
        "renew_required": renovar,
        "renew_urgent": renovar and horas < HORAS_URGENTES,
        "renew_urgent_hours": HORAS_URGENTES,
        "action": "RENEW_MARKET_LISTING" if renovar else "KEEP_LISTING",
        "listing": {"player_id": pid, "listed_price": precio,
                    "player": {"id": pid, "name": nombre, "price": valor}},
    }


def _tablero(horas_boye, horas_chust) -> dict:
    """Lo que devuelve `build_market_listing_lifecycle_board`: ordenado
    por caducidad, con sus colas."""
    players = [_publicacion(*BOYE_P, horas_boye), _publicacion(*CHUST_P, horas_chust)]
    players += [_publicacion(*s) for s in SANAS]
    players.sort(key=lambda p: p["hours_to_expiry"])
    renovar = [p for p in players if p["renew_required"]]
    urgentes = [p for p in renovar if p["renew_urgent"]]
    sanas = [p for p in players if p["action"] == "KEEP_LISTING"]
    return {
        "players": players, "listing_count": len(players),
        "renew_required": renovar, "renew_required_count": len(renovar),
        "renew_urgent": urgentes, "renew_urgent_count": len(urgentes),
        "expiry_warnings": [], "expiry_warning_count": 0,
        "healthy": sanas, "healthy_count": len(sanas),
    }


def _fallos(n, hasta) -> dict:
    """El backoff de la renovacion de Boye: `n` fallos, castigado hasta
    `hasta` (hora sin zona, como lo apunta produccion)."""
    return {"actions": {f"RENEW_MARKET_LISTING:{BOYE}": {
        "action": "RENEW_MARKET_LISTING", "target_id": BOYE,
        "consecutive_failures": n, "last_failure_at": hasta,
        "blocked_until": hasta, "backoff_seconds": 1800 * 2 ** (n - 1),
        "last_status": "FAILED", "last_http_status": None,
        "last_reason": "Biwenger no confirmo la renovacion."}}}


# (nombre, ahora UTC, horas a la jornada, horas de Boye, horas de Chust,
#  backoff). La J12 empieza el vie 06/11 a las 21:00 (cierre 20:45).
VUELTAS = (
    ("0715", datetime(2026, 11, 4, 6, 15, tzinfo=_UTC), 61.41, 1.84, 2.84, {}),
    ("0807", datetime(2026, 11, 4, 7, 7, tzinfo=_UTC), 60.57, 1.0, 2.0,
     _fallos(1, "2026-11-04T06:50:33")),
    ("0907", datetime(2026, 11, 4, 8, 10, tzinfo=_UTC), 59.6, 0.01, 1.01,
     _fallos(2, "2026-11-04T08:11:00")),
    ("1007", datetime(2026, 11, 4, 9, 12, tzinfo=_UTC), 58.54, -1.03, -0.02,
     _fallos(2, "2026-11-04T08:11:00")),
    ("chust_primero", datetime(2026, 11, 4, 7, 7, tzinfo=_UTC), 60.57, 2.0, 1.0, {}),
    ("solo_boye", datetime(2026, 11, 4, 7, 7, tzinfo=_UTC), 60.57, 1.0, 47.0, {}),
    ("sin_prisa", datetime(2026, 11, 4, 3, 7, tzinfo=_UTC), 64.57, 5.0, 6.0, {}),
    ("ninguna", datetime(2026, 11, 4, 11, 7, tzinfo=_UTC), 56.57, 47.0, 47.0, {}),
)


# ============================================================
# LO DEMAS DE LA VUELTA, COMPACTADO
# ============================================================

def _oferta(pid, nombre, importe, prima, decision, offer_id) -> dict:
    return {"offer_id": offer_id, "player_id": pid, "player_name": nombre,
            "amount": importe, "premium_percent": prima, "decision": decision,
            "protection": "NORMAL", "sale_score": 60.0 if decision == "ACCEPT_NOW" else 0.0,
            "reasons": [f"{nombre}: {decision}"]}


# Las once ofertas del Computer del 04/11 (ninguna para cobrar).
OFERTAS_HOY = [
    _oferta(CHUST, "Chust", 2_855_600, 5.0, "KEEP_GOOD_OFFER", 8101),
    _oferta(IVAN, "Iván Martín", 2_717_200, 0.6, "KEEP_GOOD_OFFER", 8102),
    _oferta(ROBERTO, "Roberto Fernández", 7_001_600, 0.2, "KEEP_GOOD_OFFER", 8103),
    _oferta(DANI, "Dani Lorenzo", 2_089_300, 3.9, "KEEP_GOOD_OFFER", 8104),
    _oferta(IGLESIAS, "Juan Iglesias", 3_823_100, 0.6, "KEEP_GOOD_OFFER", 8105),
    _oferta(GULACSI, "Gulácsi", 2_314_000, 3.8, "KEEP_GOOD_OFFER", 8106),
    _oferta(CARDONA, "Sergi Cardona", 2_138_600, -1.4, "HOLD_OFFER", 8107),
    _oferta(BOYE, "Boyé", 5_316_300, -1.0, "HOLD_OFFER", 8108),
    _oferta(RAMON, "Ramón Enríquez", 449_500, 2.2, "KEEP_GOOD_OFFER", 8109),
    _oferta(KIKE, "Kike Salas", 3_633_500, 4.7, "KEEP_GOOD_OFFER", 8110),
    _oferta(OLASAGASTI, "Olasagasti", 2_891_900, 1.8, "KEEP_GOOD_OFFER", 8111),
]

# De la prueba: el motor aprueba vender a Boye (la que mas prima deja) y
# a Iglesias.
OFERTAS_BOYE_APROBADA = (
    [o for o in OFERTAS_HOY if o["player_id"] not in (BOYE, IGLESIAS)]
    + [_oferta(BOYE, "Boyé", 5_700_000, 6.1, "ACCEPT_NOW", 9001),
       _oferta(IGLESIAS, "Juan Iglesias", 3_900_000, 2.6, "ACCEPT_NOW", 9002)]
)

OFERTAS = (("hoy", OFERTAS_HOY), ("boye_aprobada", OFERTAS_BOYE_APROBADA))

# El tablero de fichajes del motor viejo: sin objetivo, o con uno.
OBJETIVO = {
    "id": 99001, "name": "Objetivo del tablero", "decision": "BID", "bid": 1_209_900,
    "expected_value": 310_000, "market_price": 1_150_000,
    "reason": "Mejora el once: +0,6 pts por jornada.", "intent": "XI_UPGRADE",
    "player": {"id": 99001, "name": "Objetivo del tablero", "price": 1_150_000},
}
TABLEROS = (("sin_tablero", None),
            ("con_objetivo", {"available": True, "biddable": 1, "actionable": 1,
                              "targets": [OBJETIVO]}))

# Lo que la liquidez quiere publicar: Yamal (lo unico sin publicar).
YAMAL_A_LA_VENTA = {"id": YAMAL, "name": "Yamal", "listing_price": 32_160_000,
                    "listing_action": "LIST_FOR_LIQUIDITY"}
OLASAGASTI_A_LA_VENTA = {"id": OLASAGASTI, "name": "Olasagasti",
                         "listing_price": 3_470_000, "listing_action": "LIST_FOR_LIQUIDITY"}


def _solvencia(horas) -> dict:
    return {
        "balance": 2_025_724,
        "deadline": {
            "phase": "NORMAL", "calendar": {"source": "CALENDARIO"},
            "lineup_pressure_score": 0, "target_matchday": 12, "next_matchday": 12,
            "operations_locked": False, "hard_safety_mode": False,
            "first_kickoff": "2026-11-06T21:00:00+01:00",
            "real_deadline": "2026-11-06T20:45:00+01:00",
            "next_round_unlock": "2026-11-06T23:00:00+01:00",
        },
        "seconds_to_deadline": int(horas * 3600),
        "lineup_risk": "BAJO",
        "hard_safety": {"active": False},
    }


def _especulacion() -> dict:
    return {
        "budget": {"enabled": False, "reason": "Sin presupuesto de especular."},
        "acquisition_budget": {"enabled": True, "available_budget": 6_044_024,
                               "reason": "Para mejorar el once: 6.842.024 EUR."},
        "executable_buys": [],
        "buy_candidates": [],
        "bid_exposure": {"available": True, "committed_total": 798_000,
                         "operations": [{"offer_id": 2300924314, "amount": 798_000,
                                         "player_ids": [LOUREIRO]}]},
    }


def _los_constructores(vuelta, ofertas) -> dict:
    """Lo que devuelve cada constructor del orquestador en esta vuelta."""
    nombre, ahora, horas, h_boye, h_chust, _ = vuelta
    solvencia = _solvencia(horas)
    return {
        "build_solvency_state": solvencia,
        "build_t15_solvency_forecast": {"available": True, "safe": True},
        "build_franchise_autopilot_state": {"state": "NO_FRANCHISE", "reason": None},
        "build_lineup_monitor_state": {"lineup": {"playable_count": 11},
                                       "should_save": False, "complete": True},
        "build_liquidity_state": {"recovery": {"needed": False, "possible": True},
                                  "to_list": [YAMAL_A_LA_VENTA], "incoming_offers": []},
        "build_offer_board": {"offers": len(ofertas)},
        "build_offer_decision_board": {"decisions": ofertas},
        "build_computer_offer_reroll_board": {"reroll_candidates": []},
        "build_accept_before_expiry_safety_board": {"urgent_clusters": [],
                                                    "watch_clusters": []},
        "build_market_listing_lifecycle_board": _tablero(h_boye, h_chust),
        "build_portfolio_roi_board": {"exits": []},
        "build_speculation_board": _especulacion(),
    }


# ============================================================
# LO QUE SE SUSTITUYE (disco, red y reloj)
# ============================================================

def _la_orden_en(carpeta, nombre_orden, orden) -> Path:
    """La orden escrita en `carpeta` (o una ruta que no existe)."""
    ruta = Path(carpeta) / f"orden_{nombre_orden}.json"
    if orden is not None and not ruta.exists():
        ruta.write_text(json.dumps(orden, ensure_ascii=False), encoding="utf-8")
    return ruta


def _la_orden_de_mentira(ruta, ahora):
    """`protegidos`, `vetados` y `conservados` de la orden real, leyendo
    `ruta` a la hora `ahora` (las tres funciones de verdad: solo cambia de
    donde leen y que hora es)."""
    import src.actions.la_orden_del_gestor as orden_mod

    reales = {n: getattr(orden_mod, n) for n in ("protegidos", "vetados", "conservados")}
    return [(orden_mod, n, (lambda f: (lambda *a, **k: f(ruta, ahora)))(f))
            for n, f in reales.items()]


def _el_orquestador_de_mentira(vuelta, ofertas):
    """Los constructores del orquestador devuelven lo compactado (una copia
    cada vez) y el backoff mira la hora de la vuelta (sin zona, como
    produccion)."""
    import src.analysis.action_failure_backoff as backoff_mod
    import src.analysis.decision_orchestrator as orq

    piezas = _los_constructores(vuelta, ofertas)
    cambios = [(orq, n, (lambda v: (lambda *a, **k: copy.deepcopy(v)))(v))
               for n, v in piezas.items()]
    ahora = vuelta[1].replace(tzinfo=None)
    real = backoff_mod.apply_backoff_to_candidates
    cambios.append((orq, "apply_backoff_to_candidates",
                    lambda candidates, state=None, now=None:
                    real(candidates=candidates, state=state, now=ahora)))
    return cambios


def _el_plan(vuelta, ofertas, tablero, ruta, entorno) -> dict:
    """El plan del orquestador en esta vuelta, con este entorno."""
    import src.analysis.decision_orchestrator as orq

    with _Interruptores(entorno):
        with _Sustituye(_el_orquestador_de_mentira(vuelta, ofertas)
                        + _la_orden_de_mentira(ruta, vuelta[1])):
            return orq.build_global_decision_uncached(
                {"timestamp": f"snapshot_{vuelta[0]}", "my_team": []},
                failure_backoff=copy.deepcopy(vuelta[5]),
                acquisition_board=copy.deepcopy(tablero),
            )


class _Respuesta:
    def __init__(self, status, cuerpo):
        self.status_code, self._cuerpo = status, cuerpo
        self.text = "" if cuerpo is None else json.dumps(cuerpo)

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin cuerpo")
        return self._cuerpo


def _escritor_real(status, cuerpo, enviados):
    """El `BiwengerWriteClient` de verdad (con su guarda), sin login y con
    una sesion de mentira: lo que se enviaria se apunta en `enviados`."""
    import src.biwenger.write_client as escritura

    class _Sesion:
        def post(self, url, json=None, timeout=None):
            enviados.append({"url": url, "json": json})
            return _Respuesta(status, cuerpo)

    class _Cliente:
        BASE_URL = "https://biwenger.invalid/api/v2"
        session = _Sesion()

    def fabrica():
        cliente = object.__new__(escritura.BiwengerWriteClient)
        cliente.client = _Cliente()
        cliente.version, cliente.league_id, cliente.user_id = "0", 2165477, YO
        return cliente

    return fabrica


def _escritor_que_devuelve(respuesta, enviados):
    class _Escritor:
        def list_player_for_sale(self, player_id, price, execute=False):
            enviados.append({"player_id": player_id, "price": price, "execute": execute})
            return copy.deepcopy(respuesta)

    return _Escritor


ESCRITORES = (
    ("real_204", lambda env: _escritor_real(204, None, env)),
    ("real_400", lambda env: _escritor_real(400, {"status": 400, "message": "precio"}, env)),
    ("ensayo", lambda env: _escritor_que_devuelve(
        {"operation": "LIST_FOR_SALE", "sent": False}, env)),
    ("rara", lambda env: _escritor_que_devuelve({}, env)),
)

PUERTA = {"phase": "NORMAL", "operations_locked": False, "hard_safety_mode": False,
          "target_matchday": 12, "next_matchday": 12}


def _renovar(publicacion) -> dict:
    return {
        "type": "MARKET_LISTING_RENEW_URGENT", "priority": 690, "renew_urgent": True,
        "action": "RENEW_MARKET_LISTING", "executable": True, "executor": "AUTOPILOT",
        "reason": f"La publicacion de {publicacion['name']} caduca.",
        "data": {"listing": publicacion}, "temporal_gate": dict(PUERTA),
    }


def _publicar(jugador) -> dict:
    return {
        "type": "LIQUIDITY_MAINTENANCE", "priority": 550, "action": "LIST_FOR_LIQUIDITY",
        "executable": True, "executor": "AUTOPILOT", "reason": "Hay un jugador sin publicar.",
        "data": {"player": jugador}, "temporal_gate": dict(PUERTA),
    }


_T0807 = _tablero(1.0, 2.0)
DECISIONES = (
    ("renovar_boye", _renovar(next(p for p in _T0807["renew_required"]
                                   if p["player_id"] == BOYE))),
    ("renovar_chust", _renovar(next(p for p in _T0807["renew_required"]
                                    if p["player_id"] == CHUST))),
    ("publicar_yamal", _publicar(YAMAL_A_LA_VENTA)),
    ("publicar_olasagasti", _publicar(OLASAGASTI_A_LA_VENTA)),
)

# El tablero fresco que ve el ejecutor al revalidar: el de las 08:07, o
# ya renovadas.
FRESCOS = (("0807", _T0807), ("renovadas", _tablero(47.0, 47.0)))

# El backoff que ya hay en disco (el de las 08:07) y la hora fija con la
# que se apunta (sin zona, como produccion).
BACKOFF_EN_DISCO = _fallos(1, "2026-11-04T06:50:33")
HORA_DEL_BACKOFF = datetime(2026, 11, 4, 7, 10, 50)
AHORA_DE_LA_VUELTA = datetime(2026, 11, 4, 7, 7, tzinfo=_UTC)


def _la_vuelta(decision, fabrica_de_escritor, fresco, ruta, entorno,
               ahora=AHORA_DE_LA_VUELTA) -> dict:
    """La escritura de la vuelta: el ejecutor (con el escritor dado y el
    tablero fresco), lo que apunta el backoff (`register_action_outcome`,
    en memoria y a hora fija) y lo que ven los consumidores de V10."""
    import src.actions.autopilot_executor as ex
    import src.analysis.action_failure_backoff as backoff_mod
    import src.autopilot as ap
    from src.v10_full_autonomous_live import (
        _compact_execution,
        _cycle_write_execution,
        _write_used,
    )

    enviados, guardados = [], []
    real_record = backoff_mod.record_action_result
    with _Interruptores(entorno):
        with _Sustituye([
            (ex, "BiwengerWriteClient", fabrica_de_escritor(enviados)),
            (ex, "refresh_snapshot_for_write_revalidation",
             lambda: ("snapshot_fresco_de_la_prueba.json", {"timestamp": "fresco"})),
            (ex, "build_market_listing_lifecycle_board",
             lambda snapshot, now=None: copy.deepcopy(fresco)),
            (ap, "load_backoff_state", lambda: copy.deepcopy(BACKOFF_EN_DISCO)),
            (ap, "save_backoff_state", lambda state: guardados.append(copy.deepcopy(state))),
            (ap, "record_action_result",
             lambda state, **kw: real_record(state, **{**kw, "now": HORA_DEL_BACKOFF})),
        ] + _la_orden_de_mentira(ruta, ahora)):
            decision = copy.deepcopy(decision)
            r = ex.execute_autopilot_decision(decision, execute=True)
            apuntado = ap.register_action_outcome(decision, r)
            ciclo = {"execution": r,
                     "competitive_execution": {"status": "NO_COMPETITIVE_ACTION",
                                               "write_performed": False}}
            fuente, escritura = _cycle_write_execution(ciclo)
            usada = _write_used(ciclo)
            v10 = {
                "write_used": usada,
                "fuente": fuente,
                "compacta": _compact_execution(
                    source=fuente,
                    action=(escritura or {}).get("action"),
                    result=escritura, write_used=usada),
            }
    return {"r": r, "enviados": enviados, "apuntado": apuntado,
            "guardados": guardados, "v10": v10}


# ============================================================
# LA BATERIA Y SU HUELLA
# ============================================================

# Los 26 que enciende el YAML de produccion de origin/main (e5a51e88,
# .github/workflows/bordalas-live.yml), contados con
# `el_paso_0.interruptores_encendidos_en`.
PRODUCCION = {n: "1" for n in (
    "BORDALAS_COBRA_LA_RACHA", "BORDALAS_COMPRA_SOLO_SI_SUBE",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA", "BORDALAS_EL_CIERRE_DE_LA_JORNADA",
    "BORDALAS_EL_INFORME_DE_LA_MANANA", "BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE",
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

APAGADO = (None, "0", "")
ENCENDIDO = {**PRODUCCION, ENV: "1"}


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
    """[(nombre, llamada)]: el plan del orquestador y la escritura de la
    vuelta, con la firma de main."""
    llamadas = []
    for vuelta in VUELTAS:
        for nombre_orden, orden in ORDENES:
            ruta = _la_orden_en(carpeta, nombre_orden, orden)
            for nombre_ofertas, ofertas in OFERTAS:
                for nombre_tablero, tablero in TABLEROS:
                    llamadas.append((
                        f"plan/{vuelta[0]}/{nombre_orden}/{nombre_ofertas}/{nombre_tablero}",
                        lambda vuelta=vuelta, ofertas=ofertas, tablero=tablero, ruta=ruta:
                        lambda entorno: _el_plan(vuelta, ofertas, tablero, ruta, entorno)))
    for nombre_decision, decision in DECISIONES:
        for nombre_escritor, escritor in ESCRITORES:
            for nombre_fresco, fresco in FRESCOS:
                for nombre_orden, orden in ORDENES:
                    ruta = _la_orden_en(carpeta, nombre_orden, orden)
                    llamadas.append((
                        f"vuelta/{nombre_decision}/{nombre_escritor}/{nombre_fresco}/"
                        f"{nombre_orden}",
                        lambda decision=decision, escritor=escritor, fresco=fresco, ruta=ruta:
                        lambda entorno: _la_vuelta(decision, escritor, fresco, ruta, entorno)))
    return llamadas


LLAMADAS_DE_LA_BATERIA = (len(VUELTAS) * len(ORDENES) * len(OFERTAS) * len(TABLEROS)
                          + len(DECISIONES) * len(ESCRITORES) * len(FRESCOS) * len(ORDENES))


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


# Medidas en main sin tocar (copia de origin/main e5a51e88 con este
# fichero dentro) con `python -m
# src.analysis.test_el_protegido_no_gasta_la_vuelta_v1 --medir`, una por
# Python y por entorno (sin interruptores y los 26 de produccion).
# Cualquier cambio querido en el orquestador, el ejecutor, el escritor,
# el backoff, `register_action_outcome` o los consumidores de V10 la pone
# roja: se vuelve a medir en main, a proposito, en las dos versiones.
HUELLAS_DE_MAIN = {
    (3, 11): {
        "produccion": "943ca3cfef0a1fca161e30d9fbd24912b0cccfca3ea731025c7407480bb896ea",
        "sin_interruptores": "61a0f2c63de47a730cb597970fc46efe68afb8a65313451cf363d38db76d60bf",
    },
    (3, 13): {
        "produccion": "943ca3cfef0a1fca161e30d9fbd24912b0cccfca3ea731025c7407480bb896ea",
        "sin_interruptores": "61a0f2c63de47a730cb597970fc46efe68afb8a65313451cf363d38db76d60bf",
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

def _vuelta(nombre):
    return next(v for v in VUELTAS if v[0] == nombre)


def _accion(plan) -> tuple:
    """(accion, jugador) de la accion de la vuelta (`action_decision`)."""
    d = plan.get("action_decision") or {}
    data = d.get("data") or {}
    jugador = ((data.get("listing") or {}).get("player_id")
               or (data.get("offer") or {}).get("player_id")
               or (data.get("player") or {}).get("id"))
    return d.get("action"), jugador


def _renovaciones(plan) -> list:
    return [((c.get("data") or {}).get("listing") or {}).get("player_id")
            for c in plan.get("candidates") or []
            if c.get("action") == "RENEW_MARKET_LISTING"]


# 1. NACE APAGADO, UN LECTOR, SU FRASE, NADA AL IMPORTARSE

def test_nace_apagado_un_lector_y_su_frase():
    import ast
    from src.analysis import el_protegido_no_gasta_la_vuelta as pieza
    from src.telemetry.el_tablon import QUE_HACE

    assert pieza.ENV == ENV
    for valor in (None, "0", "", "no", "false", "2", "off", " 0 "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is False, repr(valor)
    for valor in ("1", "true", "si", "yes", " SI ", "on", "sí", "Sí", " ON "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is True, repr(valor)

    # Un solo sitio lo lee: `activo`, y solo lo llama el propio modulo
    # (el plan y la escritura frenada). Fuera, solo la frase del tablon.
    nombran = []
    for ruta in sorted(list((RAIZ / "src").rglob("*.py")) + list((RAIZ / "scripts").rglob("*.py"))):
        if ruta.name.startswith("test_"):
            continue
        if ENV in ruta.read_text(encoding="utf-8"):
            nombran.append(ruta.relative_to(RAIZ).as_posix())
    assert nombran == ["src/analysis/el_protegido_no_gasta_la_vuelta.py",
                       "src/telemetry/el_tablon.py"], nombran
    fuente = (RAIZ / "src" / "analysis" / "el_protegido_no_gasta_la_vuelta.py").read_text(
        encoding="utf-8")
    assert fuente.count(f'ENV = "{ENV}"') == 1
    assert fuente.count("os.environ.get(ENV") == 1
    assert fuente.count("activo()") - fuente.count("def activo()") == 2, \
        "activo() se llama en `los_del_plan` y en `la_que_frena_el_escritor`"
    for ruta in (RAIZ / "src").rglob("*.py"):
        if ruta.name.startswith("test_") or ruta.name == "el_protegido_no_gasta_la_vuelta.py":
            continue
        texto = ruta.read_text(encoding="utf-8")
        if "el_protegido_no_gasta_la_vuelta" in texto:
            assert ".activo(" not in texto and "import activo" not in texto, ruta

    # Nada al importarse: ninguna sentencia de modulo llama al lector ni
    # mira el entorno.
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        if isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant):
            continue                                # el docstring
        texto = ast.dump(nodo)
        assert "activo" not in texto and "environ" not in texto, ast.unparse(nodo)[:120]

    # Y el inventario de los interruptores lo ve leido al llamarse.
    from scripts.los_interruptores import lectores

    lee = lectores(RAIZ / "src" / "analysis" / "el_protegido_no_gasta_la_vuelta.py")
    assert lee.get(ENV) == "AL_LLAMARSE", lee.get(ENV)

    frase = str(QUE_HACE.get(ENV) or "")
    for trozo in ("protegido por la orden del gestor", "renovar", "siguiente",
                  "no gasta la escritura de la vuelta", "castiga como un fallo",
                  "Proteger sigue siendo no vender, no publicar y no renovar"):
        assert trozo in frase, (trozo, frase)


def test_lo_que_el_paso_0_da_por_encendido():
    """Lo que el paso 0, el tablon, el panel y el ensayo dan por
    encendido (`el_paso_0.ENCENDIDO`), la pieza lo lee encendido, y al
    reves."""
    from src.analysis import el_paso_0
    from src.analysis import el_protegido_no_gasta_la_vuelta as pieza

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
    """La bateria, con el interruptor sin poner, "0" y "", sin
    interruptores y con los 26 de produccion: la huella de main, medida
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


# 3. EL CASO DE HOY: EL PLAN

def test_el_caso_de_hoy_el_plan():
    """Boye protegido y primero en la cola. Apagado (main): la vuelta
    renueva a Boye (07:15, 08:07, 10:07) y a las 09:07, con Boye en
    backoff, ninguna renovacion. Encendido: la de Chust, todas las
    vueltas; Boye queda apuntado en `no_se_renuevan`."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for nombre in ("0715", "0807", "0907", "1007"):
            v = _vuelta(nombre)
            apagado = _el_plan(v, OFERTAS_HOY, None, ruta, PRODUCCION)
            encendido = _el_plan(v, OFERTAS_HOY, None, ruta, ENCENDIDO)

            if nombre == "0907":
                assert _renovaciones(apagado) == [BOYE], _renovaciones(apagado)
                assert _accion(apagado)[0] != "RENEW_MARKET_LISTING", _accion(apagado)
            else:
                assert _accion(apagado) == ("RENEW_MARKET_LISTING", BOYE), _accion(apagado)

            assert _accion(encendido) == ("RENEW_MARKET_LISTING", CHUST), (
                nombre, _accion(encendido))
            assert _renovaciones(encendido) == [CHUST], _renovaciones(encendido)
            assert encendido["action_decision"]["type"] == "MARKET_LISTING_RENEW_URGENT"
            assert encendido["action_decision"]["priority"] == 690
            fuera = encendido["state"]["no_se_renuevan"]
            assert [f["player_id"] for f in fuera] == [BOYE], fuera
            assert fuera[0]["motivo"] == "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR", fuera
            # El tablero de publicaciones no se toca: el panel sigue
            # viendo las dos.
            assert [p["player_id"] for p in
                    encendido["state"]["listing_lifecycle"]["renew_required"]] == \
                [p["player_id"] for p in apagado["state"]["listing_lifecycle"]["renew_required"]]


# 4. EL CASO DE HOY: LA VUELTA

def test_el_caso_de_hoy_la_vuelta():
    """La renovacion de Boye llega igual al ejecutor y la guarda la frena.
    Apagado (main): FAILED, «Biwenger no confirmo», escritura gastada,
    backoff y V10 sin turno. Encendido: BLOCKED, el `blocked` en el
    resultado y en el motivo, nada enviado, sin backoff y V10 libre."""
    renovar_boye = dict(DECISIONES)["renovar_boye"]
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for nombre_escritor, escritor in ESCRITORES[:2]:
            apagado = _la_vuelta(renovar_boye, escritor, _T0807, ruta, PRODUCCION)
            encendido = _la_vuelta(renovar_boye, escritor, _T0807, ruta, ENCENDIDO)

            # Main: nada enviado, pero escritura gastada y castigada.
            assert apagado["enviados"] == [], apagado["enviados"]
            assert apagado["r"]["write_performed"] is True, apagado["r"]
            assert apagado["r"]["status"] == "FAILED", apagado["r"]
            assert "blocked" not in apagado["r"], apagado["r"]
            assert apagado["apuntado"]["recorded"] is True, apagado["apuntado"]
            assert apagado["guardados"][0]["actions"][f"RENEW_MARKET_LISTING:{BOYE}"][
                "consecutive_failures"] == 2, apagado["guardados"]
            assert apagado["v10"]["write_used"] is True, apagado["v10"]

            r = encendido["r"]
            assert encendido["enviados"] == [], encendido["enviados"]
            assert r["write_performed"] is False, r
            assert r["success"] is False, r
            assert r["status"] == "BLOCKED", r
            assert r["blocked"] == "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR", r
            assert r["guardia"] == "EL_PROTEGIDO_NO_GASTA_LA_VUELTA", r
            assert r["reason"].startswith("BLOQUEADA_POR_LA_ORDEN: "), r["reason"]
            assert "Boyé" in r["reason"] and "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR" in r["reason"]
            assert "no confirmo" not in r["reason"], r["reason"]
            assert r["http_status"] is None and r["response"] is None, r
            # Lo demas del resultado, como en main.
            for clave in ("action", "player_id", "listed_price", "renewal_price",
                          "market_value", "price_raised_to_market_value",
                          "revalidation_snapshot", "listing"):
                assert r[clave] == apagado["r"][clave], clave
            # Ni backoff ni escritura gastada.
            assert encendido["apuntado"]["recorded"] is False, encendido["apuntado"]
            assert encendido["guardados"] == [], encendido["guardados"]
            assert encendido["v10"]["write_used"] is False, encendido["v10"]
            assert encendido["v10"]["fuente"] is None, encendido["v10"]


# 5. LA MISMA PUERTA QUE EL ESCRITOR

def test_la_misma_puerta_que_el_escritor():
    """Con cada orden, los que quita el plan son exactamente los que
    `list_player_for_sale` frena (`los_protegidos` lee la misma funcion
    que la guarda, `la_orden_del_gestor.protegidos`). Y la guarda sigue
    en su sitio, tal cual."""
    import inspect

    import src.biwenger.write_client as escritura
    from src.analysis import el_protegido_no_gasta_la_vuelta as pieza

    todos = [BOYE, CHUST, YAMAL, ROBERTO, IVAN, KIKE, OLASAGASTI, GULACSI, CARDONA,
             RAMON, IGLESIAS, DANI]
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden, orden in ORDENES:
            ruta = _la_orden_en(carpeta, nombre_orden, orden)
            for nombre_entorno, entorno in (("produccion", ENCENDIDO),
                                            ("sin_la_orden", {ENV: "1"})):
                with _Interruptores(entorno), _Sustituye(
                        _la_orden_de_mentira(ruta, AHORA_DE_LA_VUELTA)):
                    del_plan = pieza.los_del_plan()
                    frenados = set()
                    cliente = _escritor_real(204, None, [])()
                    for pid in todos:
                        respuesta = cliente.list_player_for_sale(pid, 1_000_000)
                        assert respuesta.get("sent") is False, respuesta
                        if respuesta.get("blocked"):
                            frenados.add(pid)
                    assert set(del_plan) == frenados, (nombre_orden, nombre_entorno,
                                                       del_plan, frenados)
                    quita = pieza.fuera_los_protegidos(
                        [{"player_id": p, "name": str(p)} for p in todos], del_plan)
                    assert {f["player_id"] for f in quita["fuera"]} == frenados
                    esperados = ({YAMAL, BOYE} if nombre_orden == "hoy"
                                 else {YAMAL} if nombre_orden == "sin_boye"
                                 else {YAMAL, BOYE, CHUST} if nombre_orden == "boye_y_chust"
                                 else set())
                    if nombre_entorno == "sin_la_orden":
                        esperados = set()
                    assert frenados == esperados, (nombre_orden, nombre_entorno, frenados)

    # La guarda, intacta: misma funcion, mismo motivo, antes de enviar.
    fuente = inspect.getsource(escritura.BiwengerWriteClient.list_player_for_sale)
    assert "from src.actions.la_orden_del_gestor import protegidos" in fuente
    assert "if int(player_id) in protegidos():" in fuente
    assert '"blocked": "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"' in fuente
    assert fuente.index("protegidos()") < fuente.index("self.client.session.post")
    pieza_fuente = inspect.getsource(pieza.los_protegidos)
    assert "from src.actions.la_orden_del_gestor import protegidos" in pieza_fuente
    assert pieza.MOTIVO == "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"


# 6. SIN PROTEGIDO QUE QUITAR, EL PLAN DE MAIN

def _sin_lo_suyo(plan) -> dict:
    """El plan sin las claves que solo pone esta pieza encendida."""
    plan = copy.deepcopy(plan)
    for clave in ("no_se_renuevan", "no_se_cobran"):
        (plan.get("state") or {}).pop(clave, None)
    return _normal(plan)


def test_sin_protegido_que_quitar_el_plan_de_main():
    """Encendido, con la orden sin Boye (el lunes), caducada, sin orden o
    con la orden apagada, el plan es el de main en cada vuelta (con
    `no_se_renuevan` y `no_se_cobran` vacios)."""
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden, orden in ORDENES:
            ruta = _la_orden_en(carpeta, nombre_orden, orden)
            for v in VUELTAS:
                for _, ofertas in OFERTAS:
                    for entorno_on, entorno_off in ((ENCENDIDO, PRODUCCION),
                                                    ({ENV: "1"}, {})):
                        sin_la_orden = ENV in entorno_on and len(entorno_on) == 1
                        if nombre_orden in ("hoy", "boye_y_chust") and not sin_la_orden:
                            continue
                        on = _el_plan(v, ofertas, None, ruta, entorno_on)
                        off = _el_plan(v, ofertas, None, ruta, entorno_off)
                        assert on["state"]["no_se_renuevan"] == [], on["state"]
                        assert on["state"]["no_se_cobran"] == [], on["state"]
                        assert _sin_lo_suyo(on) == _normal(off), (v[0], nombre_orden)
                        assert "no_se_renuevan" not in off["state"]


# 7. LO QUE SE ENVIA SIGUE SIENDO ESCRITURA

def test_lo_que_se_envia_sigue_siendo_escritura():
    """Encendido, la renovacion de Chust (204 y 400), el ensayo, la
    respuesta rara, la publicacion de liquidez (frenada o no) y la
    renovacion que ya no hace falta: lo mismo que apagado."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        for nombre_decision, decision in DECISIONES:
            for nombre_escritor, escritor in ESCRITORES:
                for _, fresco in FRESCOS:
                    on = _la_vuelta(decision, escritor, fresco, ruta, ENCENDIDO)
                    off = _la_vuelta(decision, escritor, fresco, ruta, PRODUCCION)
                    frenada_por_la_guarda = (nombre_decision == "renovar_boye"
                                             and nombre_escritor.startswith("real")
                                             and fresco is _T0807)
                    if frenada_por_la_guarda:
                        assert _normal(on) != _normal(off)
                        continue
                    assert _normal(on) == _normal(off), (nombre_decision, nombre_escritor)

        chust = _la_vuelta(dict(DECISIONES)["renovar_chust"], ESCRITORES[0][1], _T0807, ruta,
                           ENCENDIDO)
        assert chust["r"]["status"] == "LISTING_RENEWED", chust["r"]
        assert chust["r"]["write_performed"] is True, chust["r"]
        assert len(chust["enviados"]) == 1 and chust["enviados"][0]["json"]["player"] == CHUST
        assert chust["v10"]["write_used"] is True, chust["v10"]


# 8. NINGUNA RENOVACION QUE HACER: LA SIGUIENTE ACCION

def test_ninguna_renovacion_la_siguiente_accion():
    """Encendido: solo Boye por renovar (Chust ya renovado), o Boye y
    Chust protegidos: ninguna renovacion en el plan; la vuelta es para la
    siguiente accion (la puja del tablero) y apagado es la de Boye."""
    with tempfile.TemporaryDirectory() as carpeta:
        hoy = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        los_dos = _la_orden_en(carpeta, "boye_y_chust", ORDEN_BOYE_Y_CHUST)
        for nombre, ruta in (("solo_boye", hoy), ("0807", los_dos), ("0715", los_dos)):
            v = _vuelta(nombre)
            on = _el_plan(v, OFERTAS_HOY, dict(TABLEROS)["con_objetivo"], ruta, ENCENDIDO)
            off = _el_plan(v, OFERTAS_HOY, dict(TABLEROS)["con_objetivo"], ruta, PRODUCCION)
            assert _accion(off) == ("RENEW_MARKET_LISTING", BOYE), _accion(off)
            assert _renovaciones(on) == [], _renovaciones(on)
            assert _accion(on) == ("BUY_SPECULATION", 99001), _accion(on)
            fuera = {f["player_id"] for f in on["state"]["no_se_renuevan"]}
            assert BOYE in fuera, fuera

        # Sin tablero tampoco hay otra cosa que hacer: la vuelta no gasta
        # nada (ni siquiera lo intenta).
        on = _el_plan(_vuelta("solo_boye"), OFERTAS_HOY, None, hoy, ENCENDIDO)
        assert on["action_decision"] is None, on["action_decision"]


# 9. LA VENTA DEL PROTEGIDO

def test_la_venta_del_protegido():
    """El motor aprueba vender a Boye (la que mas prima deja) y a
    Iglesias. Apagado (main): la vuelta propone cobrar la de Boye, que el
    ejecutor frena (`conservar`). Encendido: la de Iglesias, y la de Boye
    queda en `no_se_cobran`."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        v = _vuelta("ninguna")
        off = _el_plan(v, OFERTAS_BOYE_APROBADA, None, ruta, PRODUCCION)
        on = _el_plan(v, OFERTAS_BOYE_APROBADA, None, ruta, ENCENDIDO)
        assert _accion(off) == ("ACCEPT_RECOVERY_OFFER", BOYE), _accion(off)
        assert _accion(on) == ("ACCEPT_RECOVERY_OFFER", IGLESIAS), _accion(on)
        cola = on["action_decision"]["data"]["queued_to_collect"]
        assert [o["player_id"] for o in cola] == [IGLESIAS], cola
        assert [f["player_id"] for f in on["state"]["no_se_cobran"]] == [BOYE]

        # Con Boye fuera de `proteger` (el lunes), su venta vuelve a ser
        # la primera, como en main.
        lunes = _la_orden_en(carpeta, "sin_boye", ORDEN_SIN_BOYE)
        assert _accion(_el_plan(v, OFERTAS_BOYE_APROBADA, None, lunes, ENCENDIDO)) == \
            ("ACCEPT_RECOVERY_OFFER", BOYE)


# 10. NUNCA LANZA

def test_nunca_lanza():
    from src.analysis import el_protegido_no_gasta_la_vuelta as pieza
    import src.actions.la_orden_del_gestor as orden_mod

    def _revienta(*a, **k):
        raise RuntimeError("la orden no se puede leer")

    raros = [None, "x", 7, {"player_id": "no-es-un-id"}, {"name": "sin id"},
             {"player_id": BOYE, "name": "Boyé"}, {"player_id": CHUST}]
    r = pieza.fuera_los_protegidos(raros, frozenset({BOYE}))
    assert r["quedan"] == [None, "x", 7, raros[3], raros[4], raros[6]], r
    assert [f["player_id"] for f in r["fuera"]] == [BOYE], r
    assert pieza.fuera_los_protegidos(None, frozenset({BOYE})) == {"quedan": [], "fuera": []}
    assert pieza.fuera_los_protegidos(raros, None)["quedan"] == raros
    assert pieza.fuera_los_protegidos(raros, {"no-es-un-id"})["quedan"] == raros

    for valor in (None, "1"):
        with _Interruptores({ENV: valor, "BORDALAS_LA_ORDEN_DEL_GESTOR": "1"}), \
                _Sustituye([(orden_mod, "protegidos", _revienta)]):
            assert pieza.los_protegidos() == frozenset()
            assert pieza.los_del_plan() == (frozenset() if valor else None)

    salida = {"action": "RENEW_MARKET_LISTING", "status": "FAILED", "write_performed": True,
              "success": False, "reason": "Biwenger no confirmo la renovacion."}
    with _Interruptores({ENV: "1"}):
        for rara in (None, "texto", 7, {}, {"sent": True, "blocked": "X"},
                     {"sent": False}, {"blocked": ""}):
            assert pieza.la_que_frena_el_escritor(salida, rara) is salida, rara
        for mala in (None, "texto", 7):
            assert pieza.la_que_frena_el_escritor(
                mala, {"sent": False, "blocked": "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"}) is mala
        otra = pieza.la_que_frena_el_escritor(
            {**salida, "listing": "basura"}, {"sent": False, "blocked": "OTRA_GUARDIA"})
        assert otra["write_performed"] is False and otra["blocked"] == "OTRA_GUARDIA", otra
        assert otra["reason"].startswith("BLOQUEADA_POR_EL_ESCRITOR: "), otra["reason"]
    with _Interruptores({ENV: None}):
        frenada = {"sent": False, "blocked": "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"}
        assert pieza.la_que_frena_el_escritor(salida, frenada) is salida

    # El orquestador encendido con la orden que revienta: el plan de
    # siempre (el escritor sigue frenando).
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy", ORDEN_HOY)
        v = _vuelta("0807")
        off = _el_plan(v, OFERTAS_HOY, None, ruta, PRODUCCION)
        import src.analysis.decision_orchestrator as orq
        with _Interruptores(ENCENDIDO), _Sustituye(
                _el_orquestador_de_mentira(v, OFERTAS_HOY)
                + _la_orden_de_mentira(ruta, v[1])):
            with _Sustituye([(orden_mod, "protegidos", _revienta)]):
                on = orq.build_global_decision_uncached(
                    {"timestamp": "snapshot_0807", "my_team": []},
                    failure_backoff=copy.deepcopy(v[5]), acquisition_board=None)
        assert _accion(on) == _accion(off) == ("RENEW_MARKET_LISTING", BOYE)


# 11. EL ENTORNO NO DECIDE (doctrina 104)

def test_el_entorno_no_decide_esta_guardia():
    """Con todo lo de fuera puesto (los del tablon, este incluido, el
    ensayo no, uno que no existe), cada prueba da lo mismo, y al salir el
    entorno es el de antes."""
    from src.analysis.el_paso_0 import PREFIJO
    from src.telemetry.el_tablon import QUE_HACE

    de_fuera = {n: "1" for n in QUE_HACE if n.startswith(PREFIJO)}
    de_fuera.update({PREFIJO + "SIN_REVENTA": "1", PREFIJO + "BID_SALT": "otra-sal",
                     PREFIJO + "LA_HUCHA": "1", PREFIJO + "PUJAR_EN_LA_VENTANA": "1",
                     PREFIJO + "UNO_QUE_NO_EXISTE": "si", ENV: "1",
                     "GITHUB_RUN_ID": "41804815503"})
    antes = {k: os.environ.get(k) for k in de_fuera}
    os.environ.update(de_fuera)
    try:
        with _Interruptores({"BORDALAS_LA_ORDEN_DEL_GESTOR": "1"}):
            dentro = sorted(k for k in os.environ
                            if k.startswith(PREFIJO) and k not in DE_LA_VERJA)
            assert dentro == ["BORDALAS_LA_ORDEN_DEL_GESTOR"], dentro
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
    test_el_caso_de_hoy_el_plan,
    test_el_caso_de_hoy_la_vuelta,
    test_la_misma_puerta_que_el_escritor,
    test_sin_protegido_que_quitar_el_plan_de_main,
    test_lo_que_se_envia_sigue_siendo_escritura,
    test_ninguna_renovacion_la_siguiente_accion,
    test_la_venta_del_protegido,
    test_nunca_lanza,
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
