"""
V10 CUENTA LO PUJADO (04/11/2026). Guardias de
`BORDALAS_V10_CUENTA_LO_PUJADO` (`src/analysis/v10_cuenta_lo_pujado.py`
y sus enganches en el BUY especulativo de V10: la caja y el plan de
`market_trader_shadow.build_market_trader_shadow(para_el_buy=True)`, el
T-15 fresco de `controlled_speculation_repricing.build_fresh_bid_reprice`,
la ultima puerta antes de escribir y las lineas del log en
`controlled_speculation_live`).

EL CASO (revision del 04/11 por la manana, vueltas de las 11:07 y 20:07)

    La regla de la casa: nunca empezar una jornada con
    saldo - pujas vivas < 0. El BUY de V10 no la cumplia:

      1. su caja era `max(saldo, 0)`: no restaba las pujas vivas (hoy
         798.000 por Loureiro, de la ronda; se resuelve el jue 07:00);
      2. su T-15 contaba como cobrable el B1 (5.316.300), que es
         exactamente la oferta del Computer por Boye, y Boye esta en
         `proteger` y en `conservar` de la orden del gestor: esa oferta
         no se cobra nunca.

    Log de las 20:07: «B1 trading-safe: 5,316,300», «Presupuesto
    trading: 3,193,638», «Saldo actual: 2,025,724», «Jugador 41031 |
    BID_PENDING | bid=798,000», «Candidato: NINGUNO».
    2.025.724 - 3.193.638 + 5.316.300 - 500.000 = 3.648.386 >= 0: el
    PASS_T15 no salta. Con un candidato, V10 podia pujar hasta el
    presupuesto (o el tope por operacion, 1.277.455) y dejar
    saldo - pujas vivas en -1.965.914 (o -49.731) si ganaba las dos.

QUE SE COMPRUEBA

    1. Nace apagado, se lee en UN sitio (`activo`, al llamarse, solo
       desde el propio modulo), vale lo mismo que `el_paso_0.ENCENDIDO`,
       tiene frase en QUE_HACE (sin ejemplos con fecha) y no hace nada
       al importarse.
    2. Apagado es main byte a byte: la huella de la bateria (la caja,
       el plan del trader, la puerta, el reprecio y el BUY entero con el
       escritor de verdad sin red, y su log), con el interruptor sin
       poner, "0", "", "off" y "2", sin interruptores y con los 27 del
       YAML de produccion (origin/main 1ac6fd51 y 4799bdc2). La de main,
       medida antes de tocar el codigo, una por version de Python (3.11,
       3.13).
    3. EL CASO DE HOY: encendido, con 798.000 pujados y la oferta de
       Boye fuera, el BUY no puja ni 3.000.000 ni el tope por operacion;
       el presupuesto baja a 727.724. Apagado, main: puja y deja
       saldo - pujas en negativo. Lo que cabe (700.000) se puja igual.
    4. Sin pujas vivas ni ofertas protegidas, encendido es main (solo
       se anade el bloque de la cuenta y sus lineas del log).
    5. La ultima puerta: con el saldo fresco mas bajo, no se puja; con
       cobrables de verdad (Iglesias), si.
    6. Que es cobrable: fuera los de `conservados()` y `protegidos()` de
       la orden viva (Boye, Chust publicado, Yamal) y Yamal siempre (por
       su nombre, intocable de la casa); con la orden caducada, sin
       orden o apagada, lo de main menos Yamal.
    7. Pujas desconocidas: no se puja. Sin bloque de exposicion, la
       misma cuenta (`build_bid_exposure`) desde la foto.
    8. Los demas del trader (V10.6, el cerebro, el libro) no cambian.
    9. Nunca lanza; si algo falla encendido, no se puja. Si la pieza no
       se pudiera importar, lo de siempre.
   10. El entorno no la decide (doctrina 104).
   11. La orden encendida, en su sitio y que no vale (JSON roto, vacia,
       sin `caduca`, un fichaje mal escrito, nombra a Yamal): no se puja
       (revision ON del 04/11: volvia a contar la oferta por Boye).
   12. Lo que la cesta del reset pujo en esta vuelta (antes del BUY, sin
       estar en la foto) se resta, por jugador; apagado no se pasa.
   13. Apagado, lo pujado de la caja y las lineas del log no miran el
       bloque (revision OFF del 04/11).

DE DONDE SALEN LOS NUMEROS

    De la vuelta de las 20:07 del 04/11 (run 41893822604): saldo
    +2.025.724, puja viva por Loureiro 798.000, B1 5.316.300 (la oferta
    del Computer por Boye, 34,81 h), colchon 500.000, presupuesto de
    trading 3.193.638 (tope por operacion: el 40 %, 1.277.455), puja
    maxima 16.282.724. Los candidatos son de prueba (hoy no habia). Ni
    `data/`, ni la red, ni el reloj: la orden va a una carpeta temporal
    y se lee con la funcion real a una hora fija; el escritor es el real
    con un cliente de mentira (lo que se enviaria se apunta).

COMO SE USA

    python -m src.analysis.test_v10_cuenta_lo_pujado_v1
    python -m src.analysis.test_v10_cuenta_lo_pujado_v1 --medir
    python -m src.analysis.test_v10_cuenta_lo_pujado_v1 --volcar FICHERO
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import sys
import tempfile

from datetime import date, datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


ENV = "BORDALAS_V10_CUENTA_LO_PUJADO"

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
# LOS JUGADORES, LOS NUMEROS Y LA ORDEN DE HOY
# ============================================================

YO = 14175949
BOYE, CHUST, YAMAL = 12494, 1760, 26271
ROBERTO, IVAN, KIKE, OLASAGASTI = 35678, 12403, 28115, 29661
GULACSI, CARDONA, RAMON, IGLESIAS, DANI = 38433, 30493, 41411, 23840, 41418
LOUREIRO, TRENT = 41031, 37499

PLANTILLA = (BOYE, CHUST, YAMAL, ROBERTO, IVAN, KIKE, OLASAGASTI, GULACSI,
             CARDONA, RAMON, IGLESIAS, DANI)

SALDO_HOY = 2_025_724
PUJA_LOUREIRO = 798_000
PUJA_TRENT = 1_100_000
OFERTA_BOYE = 5_316_300
OFERTA_IGLESIAS = 3_823_100
OFERTA_DANI = 2_089_300
OFERTA_YAMAL = 21_099_500
CHUST_PUBLICADO = 2_176_000
COLCHON = 500_000
PUJA_MAXIMA_HOY = 16_282_724
PRESUPUESTO_HOY = 3_193_638
TOPE_POR_OPERACION_HOY = 1_277_455     # int(3_193_638 * 0,40)

_UTC = timezone.utc

# La vuelta de las 20:07 (19:11 UTC).
AHORA = datetime(2026, 11, 4, 19, 11, tzinfo=_UTC)

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

# `None`: no hay fichero.
ORDENES = {"hoy": ORDEN_HOY, "sin_boye": ORDEN_SIN_BOYE,
           "caducada": ORDEN_CADUCADA, "sin_orden": None}

# Ordenes que estan en su sitio y no valen (texto tal cual, o la orden), y
# por que no valen (`la_orden_del_gestor.validar`, o que no se puede leer).
# Con la orden encendida, `protegidos()` y `conservados()` dan vacio y la
# oferta por Boye contaria como cobrable: encendido, no se puja.
ORDENES_QUE_NO_VALEN = {
    "json_roto": ('{"caduca": "2026-11-30T23:59:00+01:00", "proteger": [',
                  "NO_SE_PUEDE_LEER"),
    "vacia": ("", "NO_SE_PUEDE_LEER"),
    "nula": ("null", "NO_SE_PUEDE_LEER"),
    "lista": ("[]", "SIN_ORDEN"),
    "sin_caduca": ({k: v for k, v in ORDEN_HOY.items() if k != "caduca"}, "SIN_CADUCIDAD"),
    # Un fichaje sin `puja`.
    "fichaje_mal_escrito": ({**ORDEN_HOY, "fichar": [{"player_id": LOUREIRO,
                                                      "nombre": "Loureiro"}]},
                            "FICHAJE_MAL_ESCRITO"),
    "nombra_a_un_intocable": ({**ORDEN_HOY, "vender_si_ficha": {"jugadores": [
        {"player_id": YAMAL, "nombre": "Yamal"}]}}, "NOMBRA_A_UN_INTOCABLE"),
}

# La orden que suelta a Yamal lesionado (`yamal_por_lesion`, 28 dias o
# mas) y no lo protege: su oferta se cobra.
ORDEN_YAMAL_LESIONADO = {
    **ORDEN_HOY,
    "proteger": [{"player_id": BOYE, "nombre": "Boyé"}],
    "yamal_por_lesion": {"motivo": "Rotura de prueba.", "baja_estimada_dias": 60},
}


# ============================================================
# LA SOLVENCIA (B1) DE CADA ESCENARIO
# ============================================================

def _oferta(pid, nombre, importe, offer_id, horas) -> dict:
    """Una fuente de `safe_debt_portfolio_engine.build_recovery_sources`."""
    return {"source_id": f"COMPUTER:{offer_id}", "kind": "COMPUTER_OFFER",
            "confidence": "SECURED", "amount": importe, "player_ids": [pid],
            "player_names": [nombre], "offer_id": offer_id, "hours_to_expiry": horas}


def _publicado(pid, nombre, importe) -> dict:
    return {"source_id": f"LISTING:{pid}", "kind": "EXPECTED_LISTING",
            "confidence": "HAIRCUTTED", "amount": importe, "player_ids": [pid],
            "player_names": [nombre], "offer_id": None, "haircut": 0.2,
            "first_safe_cycle": 1}


F_BOYE = _oferta(BOYE, "Boyé", OFERTA_BOYE, 8108, 34.81)
F_IGLESIAS = _oferta(IGLESIAS, "Juan Iglesias", OFERTA_IGLESIAS, 8105, 10.81)
F_DANI = _oferta(DANI, "Dani Lorenzo", OFERTA_DANI, 8104, 10.81)
F_CHUST = _publicado(CHUST, "Chust", CHUST_PUBLICADO)
F_YAMAL = _oferta(YAMAL, "Yamal", OFERTA_YAMAL, 8199, 30.0)


def _cartera(fuentes) -> dict:
    """La cartera de `build_safe_liquidity_portfolio`, compactada: B1
    (`trading_safe`) con sus fuentes."""
    total = sum(f["amount"] for f in fuentes)
    pids = sorted({p for f in fuentes for p in f["player_ids"]})
    b1 = {
        "tier": "B" if fuentes else "A", "amount": total,
        "secured_total": sum(f["amount"] for f in fuentes if f["kind"] == "COMPUTER_OFFER"),
        "expected_total": sum(f["amount"] for f in fuentes if f["kind"] != "COMPUTER_OFFER"),
        "source_ids": [f["source_id"] for f in fuentes],
        "offer_ids": [f["offer_id"] for f in fuentes if f["offer_id"] is not None],
        "player_ids": pids, "player_names": [n for f in fuentes for n in f["player_names"]],
        "sold_count": len(pids), "starters_sold": 0, "playable_count": 11, "missing": 0,
        "lineup_complete": True, "lineup_score_loss_percent": 1.5,
        "trading_safe": True, "sporting_tier": "B1" if fuentes else "A",
        "sources": copy.deepcopy(list(fuentes)),
    }
    return {"trading_safe_total": total, "trading_safe": b1, "usable_total": total,
            "selected_sources": copy.deepcopy(list(fuentes)), "selected_player_ids": pids,
            "current_starter_ids": [ROBERTO, IVAN, KIKE, OLASAGASTI, GULACSI, CARDONA,
                                    RAMON, IGLESIAS, DANI, YAMAL, CHUST]}


CARTERAS = {
    "boye": _cartera([F_BOYE]),
    "boye_e_iglesias": _cartera([F_BOYE, F_IGLESIAS]),
    "iglesias": _cartera([F_IGLESIAS]),
    "publicado": _cartera([F_CHUST, F_DANI]),
    "vacia": _cartera([]),
    # La forma corta (como `test_market_trader_v103`): sin fuentes.
    "sin_fuentes": {"trading_safe_total": OFERTA_BOYE,
                    "trading_safe": {"amount": OFERTA_BOYE, "lineup_score_loss_percent": 2.0}},
    # Sin `trading_safe_total`: main cae a `usable_total` (Tier B).
    "usable": {"usable_total": OFERTA_BOYE, "selected_sources": [copy.deepcopy(F_BOYE)],
               "selected_player_ids": [BOYE]},
    # Solo para las pruebas de lo cobrable: la oferta por Yamal.
    "yamal": _cartera([F_YAMAL, F_IGLESIAS]),
}

# (nombre, saldo, cartera, deuda permitida, fase)
ESCENARIOS = (
    ("hoy", SALDO_HOY, "boye", True, "NORMAL"),
    ("hoy_sin_deuda", SALDO_HOY, "boye", False, "NORMAL"),
    ("negativo", -400_000, "boye_e_iglesias", True, "NORMAL"),
    ("sin_protegidos", SALDO_HOY, "iglesias", True, "NORMAL"),
    ("publicado", SALDO_HOY, "publicado", True, "NORMAL"),
    ("sin_fuentes", SALDO_HOY, "sin_fuentes", True, "NORMAL"),
    ("usable", SALDO_HOY, "usable", True, "NORMAL"),
    ("hard", SALDO_HOY, "boye", True, "HARD_SAFETY"),
    ("rico", 9_000_000, "vacia", False, "NORMAL"),
)


def _escenario(nombre):
    return next(e for e in ESCENARIOS if e[0] == nombre)


def _solvencia(escenario) -> dict:
    _, saldo, cartera, deuda, fase = escenario
    duro = fase == "HARD_SAFETY"
    return {
        "balance": saldo,
        "solvency_guarantee": {"safety_buffer": COLCHON},
        "safe_liquidity_portfolio": copy.deepcopy(CARTERAS[cartera]),
        "max_safe_debt": {"debt_window_open": deuda},
        "temporary_debt": {"allowed": deuda},
        "deadline": {"phase": fase, "operations_locked": False, "hard_safety_mode": duro},
        "hard_safety": {"active": duro},
    }


# ============================================================
# LAS PUJAS VIVAS (`build_bid_exposure`)
# ============================================================

def _puja_viva(offer_id, pid, importe) -> dict:
    """Una puja nuestra en `market.offers`, como la trae Biwenger."""
    return {"id": offer_id, "from": {"id": YO}, "to": None, "type": "purchase",
            "status": "waiting", "amount": importe, "requestedPlayers": [pid],
            "until": 1762498800, "created": 1762250000}


VIVAS = {
    "ninguna": [],
    "loureiro": [_puja_viva(2300924314, LOUREIRO, PUJA_LOUREIRO)],
    "dos": [_puja_viva(2300924314, LOUREIRO, PUJA_LOUREIRO),
            _puja_viva(2300930001, TRENT, PUJA_TRENT)],
}


def _exposicion(vivas) -> dict:
    return {
        "available": True,
        "committed_total": sum(v["amount"] for v in vivas),
        "operation_count": len(vivas),
        "operations": [{"offer_id": v["id"], "amount": v["amount"],
                        "player_ids": v["requestedPlayers"]} for v in vivas],
        "reason": "Prueba.",
    }


# (nombre, pujas en la foto, `bid_exposure` del tablero de especulacion;
#  None: el tablero no lo trae)
EXPOSICIONES = {
    "ninguna": (VIVAS["ninguna"], _exposicion(VIVAS["ninguna"])),
    "loureiro": (VIVAS["loureiro"], _exposicion(VIVAS["loureiro"])),
    "dos": (VIVAS["dos"], _exposicion(VIVAS["dos"])),
    "no_disponible": (VIVAS["loureiro"], {"available": False, "committed_total": 0,
                                          "operation_count": 0, "operations": [],
                                          "reason": "No se pudo identificar nuestro usuario."}),
    "sin_bloque": (VIVAS["loureiro"], None),
}


# ============================================================
# EL PRESUPUESTO Y LOS CANDIDATOS
# ============================================================

PRESUPUESTOS = {
    # Hoy: 3.193.638 con el tope por operacion del 40 %.
    "hoy": {"enabled": True, "total_budget": PRESUPUESTO_HOY,
            "single_operation_limit": TOPE_POR_OPERACION_HOY,
            "reason": "Existe margen de liquidez para operaciones especulativas."},
    # Sin tope por operacion (el presupuesto entero en una puja).
    "sin_tope": {"enabled": True, "total_budget": PRESUPUESTO_HOY,
                 "single_operation_limit": PRESUPUESTO_HOY,
                 "reason": "Existe margen de liquidez para operaciones especulativas."},
    "apagado": {"enabled": False, "total_budget": 0, "single_operation_limit": 0,
                "reason": "Presupuesto especulativo bloqueado."},
}

# (id, nombre, valor Biwenger, precio de la publicacion, puja de la
#  autoridad, vendedor). Con speculation 92, historico 85, +4 %, JP 60 e
#  inteligente 82: trading 87,7, ROI pedido 10 %, salida valor * 1,194.
CANDIDATOS = {
    "tres_millones": (90001, "Tres Millones", 2_900_000, 3_000_000, 3_000_000,
                      {"id": 999, "name": "Pollo17"}),
    "el_tope": (90002, "El Tope", 1_240_000, TOPE_POR_OPERACION_HOY,
                TOPE_POR_OPERACION_HOY, None),
    "setecientos": (90003, "Setecientos", 680_000, 700_000, 700_000, None),
}

LISTAS = {
    "ninguno": (),
    "tres_millones": ("tres_millones",),
    "el_tope": ("el_tope",),
    "setecientos": ("setecientos",),
    "dos": ("tres_millones", "setecientos"),
}


def _candidato(clave) -> dict:
    pid, nombre, valor, *_ = CANDIDATOS[clave]
    return {"id": pid, "name": nombre, "price": valor, "position": 3,
            "speculation_action": "BUY_SPECULATION", "speculation_score": 92.0,
            "dominant_role": "SPECULATION", "history_confidence": {"confidence": 85},
            "price_increment_percent": 4.0, "external_signal": {"jp_market_score": 60}}


def _venta(clave) -> dict:
    pid, nombre, _, publicado, _, vendedor = CANDIDATOS[clave]
    return {"player": {"id": pid, "name": nombre}, "price": publicado,
            "user": copy.deepcopy(vendedor)}


def _la_foto(escenario, exposicion, lista) -> dict:
    vivas, _ = EXPOSICIONES[exposicion]
    return {
        "timestamp": "snapshot_20261104_201125",
        "league": {"user": {"id": YO, "name": "Pepe"}},
        "my_team": [{"id": p} for p in PLANTILLA],
        "market": {"status": {"balance": escenario[1], "maximumBid": PUJA_MAXIMA_HOY},
                   "sales": [_venta(c) for c in LISTAS[lista]],
                   "offers": copy.deepcopy(vivas)},
    }


def _la_decision(escenario, exposicion, presupuesto, lista) -> dict:
    _, bloque = EXPOSICIONES[exposicion]
    especulacion = {"budget": copy.deepcopy(PRESUPUESTOS[presupuesto]),
                    "buy_candidates": [_candidato(c) for c in LISTAS[lista]]}
    if bloque is not None:
        especulacion["bid_exposure"] = copy.deepcopy(bloque)
    return {"state": {"speculation": especulacion, "solvency": _solvencia(escenario)}}


# ============================================================
# LO QUE SE SUSTITUYE (disco, red y reloj)
# ============================================================

def _por_id(clave_de_lista):
    return {CANDIDATOS[c][0]: CANDIDATOS[c] for c in CANDIDATOS}


def _inteligentes(snapshot, allow_external_checks=False):
    return [{"id": c[0], "suggested_bid": c[4], "intelligent_score": 82.0,
             "action": "COMPRAR", "competitive_strategic_max_price": None}
            for c in CANDIDATOS.values()]


def _autoridad(snapshot, player, intel, *, trading_score=None, seller_lookup=None):
    datos = _por_id(None).get(int(player.get("id") or 0))
    puja = datos[4] if datos else 0
    return {"authority_bid": puja, "allowed": bool(puja), "premium_percent": 0.0,
            "source": "PRUEBA", "confidence": "ALTA", "reason": "Autoridad de prueba.",
            "synthetic_bid": puja, "components": {}}


def _vendedores(snapshot):
    salida = {}
    for venta in ((snapshot or {}).get("market") or {}).get("sales") or []:
        usuario = venta.get("user")
        salida[int(venta["player"]["id"])] = {
            "seller_user_id": usuario.get("id") if isinstance(usuario, dict) else None}
    return salida


def _la_orden_en(carpeta, nombre_orden) -> Path:
    """La orden escrita en `carpeta` (o una ruta que no existe). Las de
    `ORDENES_QUE_NO_VALEN`, con su texto tal cual."""
    if nombre_orden in ORDENES:
        orden = ORDENES[nombre_orden]
    elif nombre_orden == "yamal_lesionado":
        orden = ORDEN_YAMAL_LESIONADO
    else:
        orden = ORDENES_QUE_NO_VALEN[nombre_orden][0]
    ruta = Path(carpeta) / f"orden_{nombre_orden}.json"
    if orden is not None and not ruta.exists():
        texto = orden if isinstance(orden, str) else json.dumps(orden, ensure_ascii=False)
        ruta.write_text(texto, encoding="utf-8")
    return ruta


def _la_orden_de_mentira(ruta, ahora=AHORA):
    """`protegidos`, `vetados` y `conservados` de la orden real, leyendo
    `ruta` a la hora `ahora` (las funciones de verdad: solo cambia de
    donde leen y que hora es). Y `RUTA` de la orden y el reloj de la
    pieza (`_ahora`), para que la pieza mire la misma orden a la misma
    hora: ni `config/` ni el reloj de verdad. Sin la pieza (main), solo
    lo de la orden."""
    import src.actions.la_orden_del_gestor as orden_mod

    reales = {n: getattr(orden_mod, n) for n in ("protegidos", "vetados", "conservados")}
    cambios = [(orden_mod, n, (lambda f: (lambda *a, **k: f(ruta, ahora)))(f))
               for n, f in reales.items()]
    cambios.append((orden_mod, "RUTA", Path(ruta)))
    try:
        from src.analysis import v10_cuenta_lo_pujado as pieza
    except ImportError:
        return cambios
    cambios.append((pieza, "_ahora", lambda: ahora))
    return cambios


class _Respuesta:
    def __init__(self, status, cuerpo):
        self.status_code, self._cuerpo = status, cuerpo
        self.text = "" if cuerpo is None else json.dumps(cuerpo)

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin cuerpo")
        return self._cuerpo


ESCRITORES = {
    "ok": (200, {"status": 200, "data": {"id": 2300999999}}),
    "rechazo": (400, {"status": 400, "message": "saldo insuficiente"}),
}


def _escritor_real(mercado, catalogo, escritor, enviados, lecturas):
    """El `BiwengerWriteClient` de verdad (con sus comprobaciones), sin
    login y con un cliente de mentira: lee `mercado` y `catalogo`; lo que
    se enviaria se apunta en `enviados`. Tras una puja aceptada, el
    mercado ya la trae (verificacion posterior)."""
    import src.biwenger.write_client as escritura

    status, cuerpo = ESCRITORES[escritor]
    estado = {"enviada": None}

    class _Sesion:
        def post(self, url, json=None, timeout=None):
            enviados.append({"url": url, "json": copy.deepcopy(json)})
            estado["enviada"] = copy.deepcopy(json)
            return _Respuesta(status, cuerpo)

    class _Cliente:
        BASE_URL = "https://biwenger.invalid/api/v2"
        session = _Sesion()

        def get_market(self):
            lecturas.append("market")
            m = copy.deepcopy(mercado)
            if estado["enviada"] is not None and status == 200:
                m["offers"].append({"id": 2300999999, "from": {"id": YO}, "type": "purchase",
                                    "status": "waiting", "amount": estado["enviada"]["amount"],
                                    "requestedPlayers": estado["enviada"]["requestedPlayers"]})
            return m

        def get_player_catalog(self):
            lecturas.append("catalog")
            return copy.deepcopy(catalogo)

    def fabrica():
        cliente = object.__new__(escritura.BiwengerWriteClient)
        cliente.client = _Cliente()
        cliente.version, cliente.league_id, cliente.user_id = "0", 2165477, YO
        return cliente

    return fabrica


def _los_del_trader():
    import src.analysis.market_trader_shadow as mts

    return [(mts, "calculate_intelligent_bids", _inteligentes),
            (mts, "build_market_bid_authority", _autoridad),
            (mts, "build_market_seller_lookup", _vendedores)]


def _el_buy(escenario, exposicion, orden, presupuesto, lista, entorno, *, ruta,
            escritor="ok", modo="live", saldo_fresco=None, maximo=None,
            de_la_vuelta=None) -> dict:
    """El BUY de V10 (`build_controlled_run`, como lo llama V10) con este
    entorno: el resultado, lo que se envio a Biwenger, cuantas lecturas
    hizo y el log (`print_result`). `de_la_vuelta`: las pujas de la cesta
    que el ciclo le pasa (`pujas_de_la_vuelta`); None, la llamada de
    main."""
    import src.actions.live_bid_executor as lbe
    import src.analysis.controlled_speculation_live as cs

    escenario = _escenario(escenario) if isinstance(escenario, str) else escenario
    foto = _la_foto(escenario, exposicion, lista)
    decision = _la_decision(escenario, exposicion, presupuesto, lista)
    mercado = copy.deepcopy(foto["market"])
    if saldo_fresco is not None:
        mercado["status"]["balance"] = saldo_fresco
    if maximo is not None:
        mercado["status"]["maximumBid"] = maximo
    catalogo = {str(c[0]): {"id": c[0], "price": c[2]} for c in CANDIDATOS.values()}
    enviados, lecturas = [], []
    log = io.StringIO()
    with _Interruptores(entorno):
        with _Sustituye([
            # Solo un nombre: `load_snapshot` es de mentira y no abre nada.
            (cs, "get_latest_snapshot", lambda: "snapshot_20261104_201125.json"),
            (cs, "load_snapshot", lambda archivo: copy.deepcopy(foto)),
            (cs, "build_global_decision", lambda snapshot, *a, **k: copy.deepcopy(decision)),
            (cs, "sync_position_ledger_snapshot",
             lambda snapshot, trader=None, **k: {
                 "ok": True, "summary": {"total_positions": 90,
                                         "counts": {"LOST": 48, "BID_PENDING": 1}},
                 "bootstrap": {"created": 0}}),
            (cs, "record_verified_bid",
             lambda result: {"registered": True, "position_id": "PRUEBA-1"}),
            (cs, "build_market_seller_lookup", _vendedores),
            (lbe, "BiwengerWriteClient",
             _escritor_real(mercado, catalogo, escritor, enviados, lecturas)),
        ] + _los_del_trader() + _la_orden_de_mentira(ruta)):
            extra = {} if de_la_vuelta is None else {"pujas_de_la_vuelta": de_la_vuelta}
            r = cs.build_controlled_run(
                refresh=False,
                execute_live=modo != "sombra",
                live_confirmation=None if modo == "sin_confirmar" else "BORDALAS",
                **extra,
            )
            with contextlib.redirect_stdout(log):
                cs.print_result(r)
    return {"r": r, "enviados": enviados, "lecturas": len(lecturas), "log": log.getvalue()}


def _la_caja(escenario, entorno) -> dict:
    from src.analysis.market_trader_shadow import build_sporting_safe_capital

    with _Interruptores(entorno):
        return build_sporting_safe_capital(_solvencia(escenario))


def _el_trader_de_los_demas(escenario, exposicion, presupuesto, lista, entorno, ruta) -> dict:
    """El trader como lo llaman V10.6, el cerebro y el libro (la firma de
    main, sin nada mas)."""
    import src.analysis.market_trader_shadow as mts

    escenario = _escenario(escenario) if isinstance(escenario, str) else escenario
    with _Interruptores(entorno):
        with _Sustituye(_los_del_trader() + _la_orden_de_mentira(ruta)):
            return mts.build_market_trader_shadow(
                _la_foto(escenario, exposicion, lista),
                decision_result=_la_decision(escenario, exposicion, presupuesto, lista),
            )


def _el_reprecio(escenario, clave, entorno) -> dict:
    """El reprecio fresco con la caja de main (como lo llaman las
    pruebas de V10.4E)."""
    from src.analysis.controlled_speculation_repricing import build_fresh_bid_reprice
    from src.analysis.market_trader_shadow import build_sporting_safe_capital

    pid, nombre, valor, publicado, puja, _ = CANDIDATOS[clave]
    with _Interruptores(entorno):
        capital = build_sporting_safe_capital(_solvencia(escenario))
        elegido = {"id": pid, "name": nombre, "price": valor, "recommended_bid": puja,
                   "max_rational_bid": int(valor * 1.194 / 1.10),
                   "expected_exit_value": int(valor * 1.194),
                   "bid_authority_premium_percent": 0.0}
        previo = {"current_price": publicado, "minimum_bid": valor,
                  "maximum_bid": PUJA_MAXIMA_HOY, "balance": escenario[1]}
        return build_fresh_bid_reprice(elegido, previo, capital, min_roi_percent=15.0)


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

VARIANTES = (
    ("rechazo", {"escritor": "rechazo"}),
    ("sombra", {"modo": "sombra"}),
    ("sin_confirmar", {"modo": "sin_confirmar"}),
    ("fresco_bajo", {"saldo_fresco": 1_000_000}),
    ("maximo_bajo", {"maximo": 500_000}),
)


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
    """[(nombre, llamada)]: la caja, el BUY entero, sus variantes, el
    trader de los demas y el reprecio, con la firma de main."""
    rutas = {n: _la_orden_en(carpeta, n) for n in ORDENES}
    llamadas = []
    for e in ESCENARIOS:
        llamadas.append((f"caja/{e[0]}", lambda entorno, e=e: _la_caja(e, entorno)))
    for e in ESCENARIOS:
        for x in EXPOSICIONES:
            for o in ("hoy", "sin_orden"):
                for p in ("hoy", "sin_tope"):
                    for c in LISTAS:
                        llamadas.append((
                            f"buy/{e[0]}/{x}/{o}/{p}/{c}",
                            lambda entorno, e=e, x=x, o=o, p=p, c=c:
                            _el_buy(e, x, o, p, c, entorno, ruta=rutas[o])))
    for e in ("hoy", "sin_protegidos"):
        for x in ("loureiro", "ninguna"):
            for c in ("setecientos", "tres_millones"):
                for nombre, extra in VARIANTES:
                    llamadas.append((
                        f"variante/{nombre}/{e}/{x}/{c}",
                        lambda entorno, e=e, x=x, c=c, extra=extra:
                        _el_buy(e, x, "hoy", "sin_tope", c, entorno, ruta=rutas["hoy"],
                                **extra)))
    for e in ESCENARIOS:
        llamadas.append((
            f"apagado/{e[0]}",
            lambda entorno, e=e: _el_buy(e, "loureiro", "hoy", "apagado", "dos", entorno,
                                         ruta=rutas["hoy"])))
    for e in ESCENARIOS:
        for x in ("loureiro", "ninguna"):
            llamadas.append((
                f"trader/{e[0]}/{x}",
                lambda entorno, e=e, x=x: _el_trader_de_los_demas(
                    e, x, "sin_tope", "dos", entorno, rutas["hoy"])))
    for e in ESCENARIOS:
        for c in CANDIDATOS:
            llamadas.append((f"reprecio/{e[0]}/{c}",
                             lambda entorno, e=e, c=c: _el_reprecio(e, c, entorno)))
    return llamadas


LLAMADAS_DE_LA_BATERIA = (
    len(ESCENARIOS)
    + len(ESCENARIOS) * len(EXPOSICIONES) * 2 * 2 * len(LISTAS)
    + 2 * 2 * 2 * len(VARIANTES)
    + len(ESCENARIOS)
    + len(ESCENARIOS) * 2
    + len(ESCENARIOS) * len(CANDIDATOS)
)


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
                    texto = json.dumps(_normal(hacer({**entorno, ENV: valor})),
                                       sort_keys=True, ensure_ascii=False, default=str)
                    huellas[nombre] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
                salida[f"{nombre_del_entorno}/{valor!r}"] = huellas
    return salida


def _la_huella(huellas: dict) -> str:
    """Una huella de todas: sha256 de las de cada llamada, en orden."""
    texto = "\n".join(f"{k} {v}" for k, v in sorted(huellas.items()))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# Medidas en main sin tocar (copias de origin/main 1ac6fd51, con la
# primera version de este fichero, y 4799bdc2, con esta; la misma) con `python -m src.analysis.test_v10_cuenta_lo_pujado_v1
# --medir`, una por Python y por entorno (sin interruptores y los 27 de
# produccion). Cualquier cambio querido en la caja, el trader, la puerta,
# el reprecio, el BUY, el escritor o el log del BUY la pone roja: se
# vuelve a medir en main, a proposito, en las dos versiones.
HUELLAS_DE_MAIN = {
    (3, 11): {
        "produccion": "aecfc52f048397bcead24ebf38c7580887bd04d345fa3ab28c942f30ef70e0cb",
        "sin_interruptores": "aecfc52f048397bcead24ebf38c7580887bd04d345fa3ab28c942f30ef70e0cb",
    },
    (3, 13): {
        "produccion": "aecfc52f048397bcead24ebf38c7580887bd04d345fa3ab28c942f30ef70e0cb",
        "sin_interruptores": "aecfc52f048397bcead24ebf38c7580887bd04d345fa3ab28c942f30ef70e0cb",
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

def _pujas(buy) -> list:
    return [e["json"]["amount"] for e in buy["enviados"]]


def _capital(buy) -> dict:
    return (buy["r"].get("trader") or {}).get("capital") or {}


def _oportunidad(buy, clave) -> dict:
    pid = CANDIDATOS[clave][0]
    return next(o for o in (buy["r"].get("trader") or {}).get("opportunities") or []
                if o["id"] == pid)


ETIQUETAS_NUEVAS = ("Pujas vivas:", "Caja tras pujas vivas:", "B1 cobrable:",
                    "B1 que no se cobra:")


def _sin_la_cuenta(buy) -> str:
    """El BUY sin el bloque de la cuenta ni sus lineas del log, en texto."""
    otro = copy.deepcopy(buy)
    capital = (otro["r"].get("trader") or {}).get("capital")
    if isinstance(capital, dict):
        capital.pop("cuenta_lo_pujado", None)
    otro["log"] = "".join(linea for linea in otro["log"].splitlines(keepends=True)
                          if not linea.startswith(ETIQUETAS_NUEVAS))
    return json.dumps(_normal(otro), sort_keys=True, ensure_ascii=False, default=str)


def _texto(x) -> str:
    return json.dumps(_normal(x), sort_keys=True, ensure_ascii=False, default=str)


# 1. NACE APAGADO, UN LECTOR, SU FRASE, NADA AL IMPORTARSE

def test_nace_apagado_un_lector_y_su_frase():
    import ast
    from src.analysis import v10_cuenta_lo_pujado as pieza
    from src.telemetry.el_tablon import QUE_HACE

    assert pieza.ENV == ENV
    for valor in (None, "0", "", "no", "false", "2", "off", " 0 "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is False, repr(valor)
    for valor in ("1", "true", "si", "yes", " SI ", "on", "sí", "Sí", " ON "):
        with _Interruptores({ENV: valor}):
            assert pieza.activo() is True, repr(valor)

    # Un solo sitio lo lee: `activo`, y solo lo llama el propio modulo
    # (la caja del BUY y la ultima puerta). Fuera, solo la frase del
    # tablon.
    nombran = []
    for ruta in sorted(list((RAIZ / "src").rglob("*.py")) + list((RAIZ / "scripts").rglob("*.py"))):
        if ruta.name.startswith("test_"):
            continue
        if ENV in ruta.read_text(encoding="utf-8"):
            nombran.append(ruta.relative_to(RAIZ).as_posix())
    assert nombran == ["src/analysis/v10_cuenta_lo_pujado.py",
                       "src/telemetry/el_tablon.py"], nombran
    fuente = (RAIZ / "src" / "analysis" / "v10_cuenta_lo_pujado.py").read_text(encoding="utf-8")
    assert fuente.count(f'ENV = "{ENV}"') == 1
    assert fuente.count("os.environ.get(ENV") == 1
    llaman = sorted(
        nodo.name for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.FunctionDef) and any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "activo"
            for n in ast.walk(nodo)))
    assert llaman == ["la_caja_del_buy", "la_puja_que_no_cabe", "las_lineas",
                      "lo_de_la_cesta", "lo_pujado_de_la_caja"], llaman
    assert fuente.count("activo()") - fuente.count("def activo()") == 5, \
        "activo() solo en la caja, la cesta, la puerta, lo pujado de la caja y el log"
    for ruta in (RAIZ / "src").rglob("*.py"):
        if ruta.name.startswith("test_") or ruta.name == "v10_cuenta_lo_pujado.py":
            continue
        texto = ruta.read_text(encoding="utf-8")
        if "v10_cuenta_lo_pujado" in texto:
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

    lee = lectores(RAIZ / "src" / "analysis" / "v10_cuenta_lo_pujado.py")
    assert lee.get(ENV) == "AL_LLAMARSE", lee.get(ENV)

    # La frase dice lo que hace, sin ejemplos con fecha (la orden cambia).
    frase = str(QUE_HACE.get(ENV) or "")
    for trozo in ("V10", "pujas vivas", "orden del gestor", "Yamal",
                  "antes de la jornada", "no puja"):
        assert trozo in frase, (trozo, frase)
    assert "hoy" not in frase.lower(), frase


def test_lo_que_el_paso_0_da_por_encendido():
    """Lo que el paso 0, el tablon, el panel y el ensayo dan por
    encendido (`el_paso_0.ENCENDIDO`), la pieza lo lee encendido, y al
    reves."""
    from src.analysis import el_paso_0
    from src.analysis import v10_cuenta_lo_pujado as pieza

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


# 3. EL CASO DE HOY

def test_el_caso_de_hoy():
    """Saldo 2.025.724, 798.000 pujados por Loureiro, la oferta de Boye
    (5.316.300) es todo el B1 y Boye esta protegido. Apagado (main): el
    BUY puja 3.000.000 (sin tope) o el tope por operacion (1.277.455) y
    deja saldo - pujas en negativo. Encendido: no puja; la caja es
    1.227.724, el B1 cobrable 0 y el presupuesto 727.724."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy")

        # A) Un candidato a 3.000.000, sin tope por operacion.
        apagado = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "tres_millones",
                          PRODUCCION, ruta=ruta)
        encendido = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "tres_millones",
                            ENCENDIDO, ruta=ruta)

        # Main: la puja sale y la regla de la casa se rompe.
        assert _pujas(apagado) == [3_000_000], apagado["enviados"]
        assert apagado["r"]["status"] == "LIVE_BID_SENT_AND_VERIFIED", apagado["r"]["status"]
        assert SALDO_HOY - PUJA_LOUREIRO - _pujas(apagado)[0] == -1_772_276
        cm = _capital(apagado)
        assert cm["trading_safe_recovery"] == OFERTA_BOYE, cm
        assert cm["cash_capacity"] == SALDO_HOY, cm
        assert cm["sporting_safe_spend_capacity"] == 6_842_024, cm
        assert apagado["r"]["trader"]["trading_budget"]["total_budget"] == PRESUPUESTO_HOY
        assert _oportunidad(apagado, "tres_millones")["projected_t15_after_buffer"] == \
            SALDO_HOY - 3_000_000 + OFERTA_BOYE - COLCHON
        assert "cuenta_lo_pujado" not in cm, sorted(cm)
        for linea in ("Saldo actual:                2,025,724 EUR",
                      "B1 trading-safe:             5,316,300 EUR",
                      "Capital sporting-safe:       6,842,024 EUR",
                      "Presupuesto trading:         3,193,638 EUR"):
            assert linea in apagado["log"], (linea, apagado["log"])
        assert not any(linea.startswith(ETIQUETAS_NUEVAS)
                       for linea in apagado["log"].splitlines())

        # Encendido: nada enviado.
        assert encendido["enviados"] == [], encendido["enviados"]
        assert encendido["r"]["writes_biwenger"] is False, encendido["r"]
        assert encendido["r"]["status"] == "NO_LIVE_CANDIDATE", encendido["r"]["status"]
        c = _capital(encendido)
        assert c["balance"] == SALDO_HOY, c
        assert c["cash_capacity"] == SALDO_HOY - PUJA_LOUREIRO == 1_227_724, c
        assert c["trading_safe_recovery"] == 0, c
        assert c["sporting_safe_spend_capacity"] == 727_724, c
        assert c["projected_t15_after_buffer_before_trading"] == 727_724, c
        cuenta = c["cuenta_lo_pujado"]
        assert cuenta["pujado"] == PUJA_LOUREIRO and cuenta["conocido"] is True, cuenta
        assert cuenta["b1"] == OFERTA_BOYE and cuenta["b1_cobrable"] == 0, cuenta
        assert [f["player_ids"] for f in cuenta["no_se_cobran"]] == [[BOYE]], cuenta
        assert cuenta["de_main"]["sporting_safe_spend_capacity"] == 6_842_024, cuenta
        presupuesto = encendido["r"]["trader"]["trading_budget"]
        assert presupuesto["total_budget"] == 727_724, presupuesto
        o = _oportunidad(encendido, "tres_millones")
        assert o["decision"] != "BUY_SHADOW", o["decision"]
        assert o["projected_t15_after_buffer"] == \
            SALDO_HOY - PUJA_LOUREIRO - 3_000_000 + 0 - COLCHON == -2_272_276
        # El log: las lineas de siempre siguen (con sus etiquetas) y se
        # anaden las de la cuenta.
        for linea in ("Saldo actual:                2,025,724 EUR",
                      "B1 trading-safe:             5,316,300 EUR",
                      "Presupuesto trading:         727,724 EUR",
                      "Candidato:                   NINGUNO",
                      "Pujas vivas:                 798,000 EUR",
                      "Caja tras pujas vivas:       1,227,724 EUR",
                      "B1 cobrable:                 0 EUR",
                      "B1 que no se cobra:          Boyé 5,316,300 EUR"):
            assert linea in encendido["log"], (linea, encendido["log"])
        etiquetas = [linea.split(":")[0] for linea in apagado["log"].splitlines()
                     if ":" in linea and not linea.startswith(">>>")]
        for etiqueta in ("Modo", "Snapshot", "Escrituras Biwenger", "Saldo actual",
                         "B1 trading-safe", "Capital sporting-safe", "Presupuesto trading",
                         "Fase", "Estado", "Motivo"):
            assert etiqueta in etiquetas, etiqueta
            assert f"\n{etiqueta}:" in "\n" + encendido["log"], etiqueta

        # B) El tope por operacion de hoy (1.277.455): main lo puja y
        #    deja saldo - pujas en -49.731; encendido no.
        apagado = _el_buy("hoy", "loureiro", "hoy", "hoy", "el_tope", PRODUCCION, ruta=ruta)
        encendido = _el_buy("hoy", "loureiro", "hoy", "hoy", "el_tope", ENCENDIDO, ruta=ruta)
        assert _pujas(apagado) == [TOPE_POR_OPERACION_HOY], apagado["enviados"]
        assert SALDO_HOY - PUJA_LOUREIRO - TOPE_POR_OPERACION_HOY == -49_731
        assert encendido["enviados"] == [], encendido["enviados"]
        assert _oportunidad(encendido, "el_tope")["decision"] != "BUY_SHADOW"

        # C) Lo que cabe se puja igual: 700.000 deja 527.724 (y 27.724
        #    sobre el colchon).
        apagado = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", PRODUCCION, ruta=ruta)
        encendido = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", ENCENDIDO, ruta=ruta)
        assert _pujas(apagado) == _pujas(encendido) == [700_000], (apagado["enviados"],
                                                                   encendido["enviados"])
        assert encendido["r"]["status"] == "LIVE_BID_SENT_AND_VERIFIED"
        assert _oportunidad(encendido, "setecientos")["projected_t15_after_buffer"] == 27_724
        assert encendido["r"]["fresh_reprice"]["fresh_projected_t15_after_buffer"] == 27_724
        assert SALDO_HOY - PUJA_LOUREIRO - 700_000 == 527_724

        # D) Los dos candidatos, sin tope: el de mas ROI (700.000) va
        #    primero en los dos; el de 3.000.000 se queda fuera en main
        #    por la cartera y encendido por el presupuesto de 727.724.
        apagado = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "dos", PRODUCCION, ruta=ruta)
        encendido = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "dos", ENCENDIDO, ruta=ruta)
        assert _pujas(apagado) == _pujas(encendido) == [700_000], (apagado["enviados"],
                                                                   encendido["enviados"])
        assert _oportunidad(apagado, "tres_millones")["decision"] == "PASS_PORTFOLIO_BUDGET"
        assert _oportunidad(encendido, "tres_millones")["decision"] == "PASS_SINGLE_LIMIT"

        # E) Con dos pujas vivas (798.000 + 1.100.000) ni los 700.000
        #    caben: 2.025.724 - 1.898.000 - 700.000 < 0.
        encendido = _el_buy("hoy", "dos", "hoy", "hoy", "setecientos", ENCENDIDO, ruta=ruta)
        assert encendido["enviados"] == [], encendido["enviados"]
        assert _capital(encendido)["cash_capacity"] == SALDO_HOY - 1_898_000


# 4. SIN PUJAS VIVAS NI OFERTAS PROTEGIDAS, MAIN

def test_sin_pujas_ni_protegidos_es_main():
    """Sin pujas vivas y sin ofertas de la orden en el B1 (Iglesias, o la
    de Boye sin orden, o sin B1 con caja de sobra), encendido decide y
    escribe lo mismo que main, euro a euro: solo se anade el bloque de la
    cuenta y sus lineas del log."""
    with tempfile.TemporaryDirectory() as carpeta:
        casos = (("sin_protegidos", "hoy"), ("hoy", "sin_orden"), ("rico", "hoy"),
                 ("negativo", "sin_orden"), ("publicado", "sin_orden"))
        for escenario, orden in casos:
            ruta = _la_orden_en(carpeta, orden)
            for presupuesto in ("hoy", "sin_tope"):
                for lista in LISTAS:
                    apagado = _el_buy(escenario, "ninguna", orden, presupuesto, lista,
                                      PRODUCCION, ruta=ruta)
                    encendido = _el_buy(escenario, "ninguna", orden, presupuesto, lista,
                                        ENCENDIDO, ruta=ruta)
                    assert _sin_la_cuenta(encendido) == _texto(apagado), (
                        escenario, orden, presupuesto, lista)
                    cuenta = _capital(encendido)["cuenta_lo_pujado"]
                    assert cuenta["pujado"] == 0 and cuenta["no_se_cobran"] == [], cuenta
        # Y alguno de verdad puja (no es un "igual porque no pasa nada").
        ruta = _la_orden_en(carpeta, "hoy")
        encendido = _el_buy("sin_protegidos", "ninguna", "hoy", "sin_tope", "tres_millones",
                            ENCENDIDO, ruta=ruta)
        assert _pujas(encendido) == [3_000_000], encendido["enviados"]


# 5. LA ULTIMA PUERTA

def test_la_ultima_puerta():
    """Antes de escribir: saldo - pujas vivas - esta puja + lo cobrable
    antes de la jornada >= 0, con el saldo mas bajo de la foto y del
    mercado fresco. Si no, no se puja (V10_CUENTA_LO_PUJADO_BLOCK, nada
    enviado)."""
    from src.analysis import v10_cuenta_lo_pujado as pieza

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy")

        # El mercado fresco trae 1.000.000 de saldo: 1.000.000 - 798.000
        # - 700.000 + 0 < 0. Main puja igual.
        apagado = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", PRODUCCION,
                          ruta=ruta, saldo_fresco=1_000_000)
        encendido = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", ENCENDIDO,
                            ruta=ruta, saldo_fresco=1_000_000)
        assert _pujas(apagado) == [700_000], apagado["enviados"]
        assert encendido["enviados"] == [], encendido["enviados"]
        r = encendido["r"]
        assert r["status"] == "V10_CUENTA_LO_PUJADO_BLOCK", r["status"]
        assert r["ready"] is False and r["writes_biwenger"] is False, r
        assert r["execution"] is None, r["execution"]
        assert r["reason"].startswith("V10_CUENTA_LO_PUJADO: "), r["reason"]
        assert "-498,000" in r["reason"], r["reason"]
        assert "Estado:                      V10_CUENTA_LO_PUJADO_BLOCK" in encendido["log"]

        # En sombra, lo mismo: no se dice que se pujaria.
        sombra = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", ENCENDIDO,
                         ruta=ruta, saldo_fresco=1_000_000, modo="sombra")
        assert sombra["r"]["status"] == "V10_CUENTA_LO_PUJADO_BLOCK", sombra["r"]["status"]
        assert "WOULD BID" not in sombra["log"]

        # Con cobrables de verdad (la oferta por Iglesias): 2.025.724 -
        # 798.000 - 3.000.000 + 3.823.100 = 2.050.824 >= 0 y 1.550.824
        # sobre el colchon: se puja.
        encendido = _el_buy("sin_protegidos", "loureiro", "hoy", "sin_tope", "tres_millones",
                            ENCENDIDO, ruta=ruta)
        assert _pujas(encendido) == [3_000_000], encendido["enviados"]
        assert encendido["r"]["fresh_reprice"]["fresh_projected_t15_after_buffer"] == 1_550_824

    # La puerta sola.
    caja = {"balance": SALDO_HOY, "cuenta_lo_pujado": {
        "conocido": True, "saldo": SALDO_HOY, "pujado": PUJA_LOUREIRO, "b1_cobrable": 0}}
    trader = {"capital": caja}
    with _Interruptores(ENCENDIDO):
        assert pieza.la_puja_que_no_cabe(trader, {"balance": SALDO_HOY}, 1_227_724) is None
        assert pieza.la_puja_que_no_cabe(trader, {"balance": SALDO_HOY}, 1_227_725)
        assert pieza.la_puja_que_no_cabe(trader, {}, 1_227_724) is None
        assert pieza.la_puja_que_no_cabe(trader, {"balance": None}, 1_227_724) is None
        # Sin la cuenta en la caja, o sin saber lo pujado: no se puja.
        assert pieza.la_puja_que_no_cabe({"capital": {"balance": SALDO_HOY}}, {}, 1)
        desconocido = {"capital": {"cuenta_lo_pujado": {**caja["cuenta_lo_pujado"],
                                                        "conocido": False}}}
        assert pieza.la_puja_que_no_cabe(desconocido, {}, 1)
    with _Interruptores(PRODUCCION):
        assert pieza.la_puja_que_no_cabe(trader, {"balance": 0}, 10**9) is None
        assert pieza.la_puja_que_no_cabe({}, {}, 10**9) is None


# 6. QUE ES COBRABLE

def test_que_es_cobrable():
    """Del B1 no se cobra la oferta (o la publicacion) de quien la orden
    viva protege o manda conservar (`conservados() | protegidos()`, las
    funciones de la orden) ni la de Yamal (intocable de la casa, por su
    nombre, con orden o sin ella). Con la orden caducada, sin orden o
    apagada, el B1 de main menos Yamal. Una fuente sin nombres no se
    cuenta (no se sabe si es la de Yamal). Con la orden que suelta a
    Yamal lesionado y no lo protege, su oferta se cobra."""
    from src.analysis import v10_cuenta_lo_pujado as pieza
    from src.analysis.market_trader_shadow import build_sporting_safe_capital

    esperado = {
        # cartera: (con la orden de hoy / del lunes, sin orden)
        "boye": (0, OFERTA_BOYE),
        "boye_e_iglesias": (OFERTA_IGLESIAS, OFERTA_BOYE + OFERTA_IGLESIAS),
        "iglesias": (OFERTA_IGLESIAS, OFERTA_IGLESIAS),
        "publicado": (OFERTA_DANI, OFERTA_DANI + CHUST_PUBLICADO),
        "vacia": (0, 0),
        "sin_fuentes": (0, 0),                 # no se sabe de quien: nada
        "usable": (0, OFERTA_BOYE),
        "yamal": (OFERTA_IGLESIAS, OFERTA_IGLESIAS),
    }
    with tempfile.TemporaryDirectory() as carpeta:
        for orden in ORDENES:
            ruta = _la_orden_en(carpeta, orden)
            for nombre_entorno, entorno in (("produccion", ENCENDIDO),
                                            ("sin_la_orden", {ENV: "1"})):
                for cartera, (con_orden, sin_orden) in esperado.items():
                    escenario = ("x", SALDO_HOY, cartera, True, "NORMAL")
                    solvencia = _solvencia(escenario)
                    capital = build_sporting_safe_capital(solvencia)
                    with _Interruptores(entorno), _Sustituye(_la_orden_de_mentira(ruta)):
                        caja = pieza.la_caja_del_buy(
                            capital,
                            speculation={"bid_exposure": _exposicion([])},
                            snapshot={})
                    viva = orden in ("hoy", "sin_boye") and nombre_entorno == "produccion"
                    quiero = con_orden if viva else sin_orden
                    assert caja["trading_safe_recovery"] == quiero, (
                        orden, nombre_entorno, cartera, caja["cuenta_lo_pujado"])
                    assert caja["cuenta_lo_pujado"]["b1"] == capital["trading_safe_recovery"]
                    # Lo que no cambia, no cambia.
                    for clave in ("balance", "safety_buffer", "can_use_temporary_debt",
                                  "portfolio", "phase", "hard_safety_active"):
                        assert caja[clave] == capital[clave], clave
                    fuera = {p for f in caja["cuenta_lo_pujado"]["no_se_cobran"]
                             for p in f.get("player_ids") or []}
                    if viva and cartera in ("boye", "boye_e_iglesias", "usable"):
                        assert fuera == {BOYE}, fuera
                    if viva and cartera == "publicado":
                        assert fuera == {CHUST}, fuera
                    if cartera == "yamal":
                        assert fuera == {YAMAL}, fuera
                        motivos = {f["motivo"] for f in caja["cuenta_lo_pujado"]["no_se_cobran"]}
                        assert motivos == ({"LA_ORDEN_DEL_GESTOR"} if viva else {"INTOCABLE"}), \
                            motivos
                    elif not viva:
                        assert fuera == set(), fuera
                    assert caja["cuenta_lo_pujado"]["conocido"] is True
                    assert caja["cuenta_lo_pujado"]["orden"] == (
                        "APAGADA" if nombre_entorno == "sin_la_orden" else
                        {"hoy": "VALE", "sin_boye": "VALE", "caducada": "CADUCADA",
                         "sin_orden": "SIN_FICHERO"}[orden]), caja["cuenta_lo_pujado"]

        # La orden que suelta a Yamal lesionado y no lo protege.
        ruta = _la_orden_en(carpeta, "yamal_lesionado")
        capital = build_sporting_safe_capital(
            _solvencia(("x", SALDO_HOY, "yamal", True, "NORMAL")))
        with _Interruptores(ENCENDIDO), _Sustituye(_la_orden_de_mentira(ruta)):
            caja = pieza.la_caja_del_buy(capital, speculation={"bid_exposure": _exposicion([])},
                                         snapshot={})
        assert caja["trading_safe_recovery"] == OFERTA_YAMAL + OFERTA_IGLESIAS, \
            caja["cuenta_lo_pujado"]
        assert caja["cuenta_lo_pujado"]["no_se_cobran"] == []

    # Lo cobrable, solo: Yamal por su nombre, como lo compara la orden.
    yamal = {"trading_safe_total": OFERTA_YAMAL,
             "trading_safe": {"sources": [{**F_YAMAL, "player_names": ["  LAMINE Yamal "]}]}}
    assert pieza.lo_cobrable(yamal, OFERTA_YAMAL, frozenset(), {"lamine yamal"})[0] == 0
    assert pieza.lo_cobrable(yamal, OFERTA_YAMAL, frozenset(), frozenset())[0] == OFERTA_YAMAL
    sin_nombres = {"trading_safe_total": OFERTA_DANI,
                   "trading_safe": {"sources": [{**F_DANI, "player_names": None}]}}
    assert pieza.lo_cobrable(sin_nombres, OFERTA_DANI, frozenset(), {"yamal"})[0] == 0
    assert pieza.lo_cobrable(sin_nombres, OFERTA_DANI, frozenset(), frozenset())[0] == \
        OFERTA_DANI
    assert pieza.lo_cobrable(CARTERAS["iglesias"], OFERTA_IGLESIAS, frozenset(), None)[0] == 0


# 7. PUJAS DESCONOCIDAS, O SIN BLOQUE

def test_pujas_desconocidas_no_se_puja():
    """Si no se sabe cuanto hay pujado (la exposicion no esta
    disponible), encendido no se puja. Si el tablero no trae el bloque,
    la misma cuenta (`build_bid_exposure`) desde la foto: 798.000."""
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "sin_orden")
        apagado = _el_buy("sin_protegidos", "no_disponible", "sin_orden", "sin_tope",
                          "setecientos", PRODUCCION, ruta=ruta)
        encendido = _el_buy("sin_protegidos", "no_disponible", "sin_orden", "sin_tope",
                            "setecientos", ENCENDIDO, ruta=ruta)
        assert _pujas(apagado) == [700_000], apagado["enviados"]
        assert encendido["enviados"] == [], encendido["enviados"]
        c = _capital(encendido)
        assert c["sporting_safe_spend_capacity"] == 0, c
        assert c["cuenta_lo_pujado"]["conocido"] is False, c["cuenta_lo_pujado"]

        sin_bloque = _el_buy("hoy", "sin_bloque", "sin_orden", "hoy", "setecientos",
                             ENCENDIDO, ruta=ruta)
        cuenta = _capital(sin_bloque)["cuenta_lo_pujado"]
        assert cuenta["pujado"] == PUJA_LOUREIRO and cuenta["conocido"] is True, cuenta
        assert cuenta["de_donde"] == "FOTO", cuenta
        con_bloque = _el_buy("hoy", "loureiro", "sin_orden", "hoy", "setecientos",
                             ENCENDIDO, ruta=ruta)
        assert _capital(con_bloque)["cuenta_lo_pujado"]["de_donde"] == "ESPECULACION"
        assert _pujas(sin_bloque) == _pujas(con_bloque) == [700_000]


# 8. LOS DEMAS DEL TRADER NO CAMBIAN

def test_los_demas_del_trader_no_cambian():
    """V10.6 (`position_manager_shadow_v106`), el cerebro
    (`market_brain_shadow`) y el libro (`position_ledger_v105`) llaman al
    trader sin `para_el_buy`: encendido, lo de main. Y el reprecio con
    una caja sin la cuenta, tambien."""
    import inspect

    import src.analysis.controlled_speculation_live as cs

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy")
        for e in ESCENARIOS:
            for x in ("loureiro", "dos", "ninguna"):
                apagado = _el_trader_de_los_demas(e, x, "sin_tope", "dos", PRODUCCION, ruta)
                encendido = _el_trader_de_los_demas(e, x, "sin_tope", "dos", ENCENDIDO, ruta)
                assert _texto(apagado) == _texto(encendido), (e[0], x)
            for c in CANDIDATOS:
                assert _texto(_el_reprecio(e, c, PRODUCCION)) == \
                    _texto(_el_reprecio(e, c, ENCENDIDO)), (e[0], c)

    for modulo in ("position_manager_shadow_v106", "market_brain_shadow",
                   "position_ledger_v105"):
        texto = (RAIZ / "src" / "analysis" / f"{modulo}.py").read_text(encoding="utf-8")
        assert "build_market_trader_shadow(" in texto and "para_el_buy" not in texto, modulo
    fuente = inspect.getsource(cs.build_controlled_run)
    assert "para_el_buy=True" in fuente, "el BUY de V10 pide la caja que cuenta lo pujado"
    assert fuente.index("_la_puja_que_no_cabe(") < fuente.index("execute=True"), \
        "la ultima puerta va antes de escribir"


# 9. NUNCA LANZA

def test_nunca_lanza():
    """Con cualquier cosa, encendido o apagado, ninguna funcion lanza.
    Si algo falla encendido, no se puja (la caja a cero y la puerta
    cerrada). Apagado, lo que llega sale igual (el mismo objeto)."""
    from src.analysis import v10_cuenta_lo_pujado as pieza

    raros = (None, "texto", 7, [], {}, {"balance": "x"}, {"portfolio": "x"},
             {"balance": 1, "portfolio": {"trading_safe_total": "x"}},
             {"cuenta_lo_pujado": "x"}, {"cuenta_lo_pujado": {"pujado": "x"}},
             [{"player_id": "x", "amount": None}], {"sent": "x"}, {"sent": [None, 3]},
             {"sent": [{"id": "x", "amount": "y", "sent": True}]})
    import src.actions.la_orden_del_gestor as orden_mod
    from src.analysis.market_trader_shadow import build_sporting_safe_capital

    # Con la orden de mentira (ni `config/` ni el reloj), la de hoy y las
    # que no valen.
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden in ("hoy", "json_roto", "sin_caduca"):
            ruta = _la_orden_en(carpeta, nombre_orden)
            for entorno in (PRODUCCION, ENCENDIDO):
                with _Interruptores(entorno), _Sustituye(_la_orden_de_mentira(ruta)):
                    for raro in raros:
                        for otro in raros:
                            caja = pieza.la_caja_del_buy(raro, speculation=otro, snapshot=otro,
                                                         de_la_vuelta=otro)
                            if entorno is PRODUCCION:
                                assert caja is raro
                            pieza.la_puja_que_no_cabe(raro, otro, 1)
                            pieza.la_puja_que_no_cabe({"capital": raro}, otro, raro)
                            pieza.lo_pujado(raro, otro)
                            pieza.lo_pujado(raro, otro, raro)
                            pieza.lo_cobrable(raro, otro, raro)
                            pieza.lo_cobrable(raro, otro, frozenset(), raro)
                        assert isinstance(pieza.lo_pujado_de_la_caja(raro), int)
                        assert isinstance(pieza.las_lineas(raro), list)
                        cesta = pieza.lo_de_la_cesta(raro)
                        assert isinstance(cesta, dict)
                        if entorno is PRODUCCION:
                            assert cesta == {}
                    ids, nombres, estado = pieza.los_que_no_se_cobran()
                    assert isinstance(nombres, frozenset) and isinstance(estado, str)

    # Encendido, si la orden revienta: no se puja, y nada lanza.
    def revienta(*a, **k):
        raise RuntimeError("la orden revienta")

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy")
        for que in (("conservados", "protegidos"), ("leer_la_orden",), ("validar",),
                    ("activa",)):
            with _Sustituye([(orden_mod, n, revienta) for n in que]):
                with _Interruptores(ENCENDIDO), _Sustituye(_la_orden_de_mentira(ruta)):
                    assert pieza.los_que_no_se_cobran()[0] is None, que
                    solvencia = _solvencia(_escenario("sin_protegidos"))
                    caja = pieza.la_caja_del_buy(build_sporting_safe_capital(solvencia),
                                                 speculation={}, snapshot={})
                    assert caja["sporting_safe_spend_capacity"] == 0, (que, caja)
                    assert pieza.la_puja_que_no_cabe({"capital": caja}, {}, 1)
                buy = _el_buy("sin_protegidos", "ninguna", "hoy", "sin_tope", "setecientos",
                              ENCENDIDO, ruta=ruta)
                assert buy["enviados"] == [], (que, buy["enviados"])


# 12. LA ORDEN ENCENDIDA QUE NO VALE: NO SE PUJA

def test_la_orden_que_no_vale_no_puja():
    """Revision ON del 04/11: con la orden encendida y su fichero en su
    sitio pero roto o que no vale (JSON roto, vacio, `null`, una lista,
    sin `caduca`, un fichaje sin puja, nombra a Yamal), `protegidos()` y
    `conservados()` dan vacio y la oferta por Boye volvia a contar como
    cobrable: presupuesto 3.193.638 y la puja de 3.000.000 salia, como
    en main. Encendido: no se puja (caja a cero, la ultima puerta
    cerrada), aunque el B1 no sea de nadie de la orden. Con la orden
    caducada, sin fichero o apagada, lo de main (menos Yamal)."""
    from src.analysis import v10_cuenta_lo_pujado as pieza

    sin_la_orden = {k: v for k, v in ENCENDIDO.items() if k != "BORDALAS_LA_ORDEN_DEL_GESTOR"}
    with tempfile.TemporaryDirectory() as carpeta:
        for nombre_orden, (_, motivo) in ORDENES_QUE_NO_VALEN.items():
            ruta = _la_orden_en(carpeta, nombre_orden)
            with _Interruptores(ENCENDIDO), _Sustituye(_la_orden_de_mentira(ruta)):
                ids, nombres, estado = pieza.los_que_no_se_cobran()
            assert ids is None and estado == motivo, (nombre_orden, ids, estado)
            assert nombres == frozenset({"yamal", "lamine yamal"}), nombres

            # El caso de hoy con la orden rota: main puja 3.000.000.
            apagado = _el_buy("hoy", "loureiro", nombre_orden, "sin_tope", "tres_millones",
                              PRODUCCION, ruta=ruta)
            encendido = _el_buy("hoy", "loureiro", nombre_orden, "sin_tope", "tres_millones",
                                ENCENDIDO, ruta=ruta)
            assert _pujas(apagado) == [3_000_000], (nombre_orden, apagado["enviados"])
            assert encendido["enviados"] == [], (nombre_orden, encendido["enviados"])
            c = _capital(encendido)
            assert c["sporting_safe_spend_capacity"] == 0, (nombre_orden, c)
            cuenta = c["cuenta_lo_pujado"]
            assert cuenta["conocido"] is False and cuenta["orden"] == motivo, cuenta
            assert motivo in cuenta["motivo"] and "no puja" in cuenta["motivo"], cuenta
            assert encendido["r"]["trader"]["trading_budget"]["total_budget"] == 0
            assert "Pujas vivas:                 NO SE SABE" in encendido["log"], \
                encendido["log"]
            # La ultima puerta, sola, tambien cerrada.
            with _Interruptores(ENCENDIDO):
                assert pieza.la_puja_que_no_cabe({"capital": c}, {"balance": SALDO_HOY}, 1)

            # Sin nada de la orden en el B1 (Iglesias) y sin pujas: tampoco.
            encendido = _el_buy("sin_protegidos", "ninguna", nombre_orden, "sin_tope",
                                "setecientos", ENCENDIDO, ruta=ruta)
            assert encendido["enviados"] == [], (nombre_orden, encendido["enviados"])

            # Con la orden apagada, su fichero no manda: lo de main con las
            # pujas vivas restadas (la oferta por Boye cuenta).
            sin_orden = _el_buy("hoy", "loureiro", nombre_orden, "sin_tope", "tres_millones",
                                sin_la_orden, ruta=ruta)
            assert _pujas(sin_orden) == [3_000_000], (nombre_orden, sin_orden["enviados"])
            cuenta = _capital(sin_orden)["cuenta_lo_pujado"]
            assert cuenta["orden"] == "APAGADA" and cuenta["b1_cobrable"] == OFERTA_BOYE, cuenta

        # Caducada o sin fichero: se cuenta (lo de main, sin Yamal).
        for nombre_orden, estado in (("caducada", "CADUCADA"), ("sin_orden", "SIN_FICHERO")):
            ruta = _la_orden_en(carpeta, nombre_orden)
            encendido = _el_buy("hoy", "loureiro", nombre_orden, "sin_tope", "tres_millones",
                                ENCENDIDO, ruta=ruta)
            cuenta = _capital(encendido)["cuenta_lo_pujado"]
            assert cuenta["orden"] == estado and cuenta["conocido"] is True, cuenta
            assert cuenta["b1_cobrable"] == OFERTA_BOYE, cuenta
            assert _pujas(encendido) == [3_000_000], (nombre_orden, encendido["enviados"])


# 13. LO QUE LA CESTA PUJO EN ESTA VUELTA

def test_la_cesta_de_la_vuelta():
    """La cesta del reset puja antes del BUY y la foto del disco no lo
    trae. El ciclo le pasa al BUY lo enviado (`lo_de_la_cesta`, solo
    encendido): la caja lo resta, por jugador (la que la foto ya trae no
    se cuenta dos veces); si no se entiende, no se puja. Apagado: nada se
    pasa y, aunque se pasara, el BUY es el de main."""
    import inspect

    import src.v10_full_autonomous_live as ciclo
    from src.analysis import v10_cuenta_lo_pujado as pieza

    subasta = {"available": True, "sent": [
        {"id": TRENT, "name": "Trent", "amount": PUJA_TRENT, "sent": True},
        {"id": 90009, "name": "Rechazada", "amount": 50_000, "sent": False}]}
    trent = [{"player_id": TRENT, "amount": PUJA_TRENT}]
    for valor in APAGADO:
        with _Interruptores({**PRODUCCION, ENV: valor}):
            assert pieza.lo_de_la_cesta(subasta) == {}
            assert ciclo._lo_de_la_cesta_para_el_buy(subasta) == {}
    with _Interruptores(ENCENDIDO):
        assert pieza.lo_de_la_cesta(subasta) == {"pujas_de_la_vuelta": trent}
        assert ciclo._lo_de_la_cesta_para_el_buy(subasta) == {"pujas_de_la_vuelta": trent}
        for nada in (None, {}, {"sent": []}, {"sent": [{"id": 1, "amount": 2, "sent": False}]},
                     {"available": False, "sent": None}):
            assert pieza.lo_de_la_cesta(nada) == {}, nada
        raro = pieza.lo_de_la_cesta({"sent": [None]})
        assert raro == {"pujas_de_la_vuelta": [{"player_id": None, "amount": None}]}, raro
        # Si la pieza no se pudiera importar, la llamada de siempre.
        nombre = "src.analysis.v10_cuenta_lo_pujado"
        antes = sys.modules.get(nombre)
        sys.modules[nombre] = None
        try:
            assert ciclo._lo_de_la_cesta_para_el_buy(subasta) == {}
        finally:
            if antes is None:
                sys.modules.pop(nombre, None)
            else:
                sys.modules[nombre] = antes

    # El ciclo se lo pasa al BUY.
    fuente = inspect.getsource(ciclo.run_full_autonomous_cycle)
    llamada = fuente[fuente.index("buy = build_controlled_run("):]
    llamada = llamada[:llamada.index("print_controlled_buy(buy)")]
    assert "**_lo_de_la_cesta_para_el_buy(subasta)" in llamada, llamada
    assert fuente.index("subasta = _pujar_en_el_reset(cycle)") < fuente.index(
        "buy = build_controlled_run(")

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy")
        # Sin cesta, los 700.000 caben (527.724 tras las pujas).
        base = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", ENCENDIDO, ruta=ruta)
        assert _pujas(base) == [700_000], base["enviados"]
        # La cesta pujo 1.100.000 por Trent: 2.025.724 - 798.000 -
        # 1.100.000 = 127.724 de caja; los 700.000 no caben.
        cesta = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", ENCENDIDO, ruta=ruta,
                        de_la_vuelta=trent)
        assert cesta["enviados"] == [], cesta["enviados"]
        cuenta = _capital(cesta)["cuenta_lo_pujado"]
        assert cuenta["pujado"] == PUJA_LOUREIRO + PUJA_TRENT, cuenta
        assert cuenta["caja"] == 127_724 and cuenta["de_donde"] == "ESPECULACION+CESTA", cuenta
        # La de Loureiro ya esta en la foto: no se cuenta dos veces.
        repetida = _el_buy("hoy", "loureiro", "hoy", "hoy", "setecientos", ENCENDIDO,
                           ruta=ruta, de_la_vuelta=[{"player_id": LOUREIRO,
                                                     "amount": PUJA_LOUREIRO}])
        assert _pujas(repetida) == [700_000], repetida["enviados"]
        assert _capital(repetida)["cuenta_lo_pujado"]["pujado"] == PUJA_LOUREIRO
        # Desde la foto (sin bloque de exposicion), igual.
        foto = _el_buy("hoy", "sin_bloque", "hoy", "hoy", "setecientos", ENCENDIDO, ruta=ruta,
                       de_la_vuelta=trent)
        assert foto["enviados"] == [], foto["enviados"]
        assert _capital(foto)["cuenta_lo_pujado"]["de_donde"] == "FOTO+CESTA"
        # Una que no se entiende: no se sabe lo pujado, no se puja.
        for mala in ([{"player_id": None, "amount": None}], [{"player_id": TRENT}],
                     [{"player_id": TRENT, "amount": "1"}], "x"):
            no = _el_buy("sin_protegidos", "ninguna", "hoy", "sin_tope", "setecientos",
                         ENCENDIDO, ruta=ruta, de_la_vuelta=mala)
            assert no["enviados"] == [], (mala, no["enviados"])
            assert _capital(no)["cuenta_lo_pujado"]["conocido"] is False, mala
        # Apagado, aunque se pasara: el BUY de main.
        for valor in APAGADO:
            entorno = {**PRODUCCION, ENV: valor}
            main = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "tres_millones", entorno,
                           ruta=ruta)
            con = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "tres_millones", entorno,
                          ruta=ruta, de_la_vuelta=trent)
            assert _texto(con) == _texto(main), valor
            assert _pujas(con) == [3_000_000]


# 14. APAGADO, EL BLOQUE NO CUENTA

def test_apagado_el_bloque_no_cuenta():
    """Revision OFF del 04/11: apagado, lo pujado de la caja y las lineas
    del log no dependen de que la caja traiga el bloque (lo lee
    `activo`): 0 y ninguna. El reprecio y el log con una caja que lo
    trae son los de una caja sin el."""
    from src.analysis import v10_cuenta_lo_pujado as pieza
    import src.analysis.controlled_speculation_live as cs

    bloque = {"conocido": True, "saldo": SALDO_HOY, "pujado": PUJA_LOUREIRO,
              "caja": SALDO_HOY - PUJA_LOUREIRO, "b1": 0, "b1_cobrable": 0,
              "no_se_cobran": [{"player_names": ["Boyé"], "amount": OFERTA_BOYE}]}
    for valor in APAGADO:
        with _Interruptores({**PRODUCCION, ENV: valor}):
            from src.analysis.controlled_speculation_repricing import build_fresh_bid_reprice

            caja = {"balance": SALDO_HOY, "trading_safe_recovery": 0, "safety_buffer": COLCHON}
            con = {**caja, "cuenta_lo_pujado": bloque}
            assert pieza.lo_pujado_de_la_caja(con) == 0
            assert pieza.las_lineas(con) == []
            elegido = {"id": 90003, "name": "Setecientos", "price": 680_000,
                       "recommended_bid": 700_000, "max_rational_bid": 800_000,
                       "expected_exit_value": 900_000, "bid_authority_premium_percent": 0.0}
            previo = {"current_price": 700_000, "minimum_bid": 700_000,
                      "maximum_bid": PUJA_MAXIMA_HOY, "balance": SALDO_HOY}
            sin = build_fresh_bid_reprice(elegido, previo, caja, min_roi_percent=15.0)
            assert _texto(build_fresh_bid_reprice(elegido, previo, con, min_roi_percent=15.0)) \
                == _texto(sin)
            assert sin["fresh_projected_t15_after_buffer"] == 825_724
            logs = []
            for capital in (caja, con):
                log = io.StringIO()
                with contextlib.redirect_stdout(log):
                    cs.print_result({"trader": {"capital": capital}})
                logs.append(log.getvalue())
            assert logs[0] == logs[1], logs
    with _Interruptores(ENCENDIDO):
        assert pieza.lo_pujado_de_la_caja({"cuenta_lo_pujado": bloque}) == PUJA_LOUREIRO
        assert pieza.las_lineas({"cuenta_lo_pujado": bloque})


# 10. SI NO SE PUEDE IMPORTAR, LO DE SIEMPRE

def test_si_no_se_importa_lo_de_siempre():
    """Si la pieza no se pudiera importar, el BUY, el trader y el
    reprecio son los de main (y no revientan), encendido o no."""
    nombre = "src.analysis.v10_cuenta_lo_pujado"
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = _la_orden_en(carpeta, "hoy")
        main = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "tres_millones", PRODUCCION,
                       ruta=ruta)
        antes = sys.modules.get(nombre)
        sys.modules[nombre] = None                  # `import` lanza ImportError
        try:
            sin_pieza = _el_buy("hoy", "loureiro", "hoy", "sin_tope", "tres_millones",
                                ENCENDIDO, ruta=ruta)
        finally:
            if antes is None:
                sys.modules.pop(nombre, None)
            else:
                sys.modules[nombre] = antes
        assert _texto(sin_pieza) == _texto(main)


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
                     "GITHUB_RUN_ID": "41893822604"})
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
    test_el_caso_de_hoy,
    test_sin_pujas_ni_protegidos_es_main,
    test_la_ultima_puerta,
    test_que_es_cobrable,
    test_pujas_desconocidas_no_se_puja,
    test_los_demas_del_trader_no_cambian,
    test_nunca_lanza,
    test_la_orden_que_no_vale_no_puja,
    test_la_cesta_de_la_vuelta,
    test_apagado_el_bloque_no_cuenta,
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
