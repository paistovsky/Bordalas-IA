"""
V10 CUENTA LO PUJADO (04/11/2026)

LO QUE PASO (revision del 04/11 por la manana, vueltas de las 11:07 y 20:07)

    La regla de la casa: nunca empezar una jornada con
    saldo - pujas vivas < 0. El BUY especulativo de V10
    (`controlled_speculation_live.build_controlled_run`, que corre si la
    vuelta no ha escrito) no la cumplia:

      1. su caja (`market_trader_shadow.build_sporting_safe_capital`)
         era `max(saldo, 0)`: no restaba las pujas vivas (hoy 798.000
         por Loureiro, de la ronda, que se resuelve el jue 07:00);
      2. su T-15 contaba como cobrable el B1 de la cartera de deuda
         segura (`safe_debt_portfolio_engine`, «trading-safe»): hoy
         5.316.300, que es exactamente la oferta del Computer por Boye.
         Boye esta en `proteger` y en `conservar` de la orden del gestor:
         esa oferta no se cobra nunca.

    Log de las 20:07: «B1 trading-safe: 5,316,300», «Presupuesto trading:
    3,193,638», «Saldo actual: 2,025,724», «Jugador 41031 | BID_PENDING |
    bid=798,000». 2.025.724 - 3.193.638 + 5.316.300 - 500.000 = 3.648.386
    >= 0: el PASS_T15 no salta. Con un candidato (hoy no habia: la via
    vieja esta en pausa y V10 no compra desde el 04/09), el BUY podia
    pujar hasta el tope por operacion (1.277.455) y dejar
    saldo - pujas vivas en -49.731 si ganaba las dos; sin tope, hasta el
    presupuesto (-1.965.914).

QUE HACE, ENCENDIDO (solo en el BUY de V10)

    1. LA CAJA (`la_caja_del_buy`, desde
       `build_market_trader_shadow(..., para_el_buy=True)`, que solo pide
       `build_controlled_run`):
         a. la caja es saldo - TODAS nuestras pujas vivas, con la misma
            cuenta que usa el resto del bot: `committed_total` de
            `bid_exposure_engine.build_bid_exposure` (la `exposure` del
            panel), que ya viene en el tablero de especulacion de la
            vuelta (`state.speculation.bid_exposure`); si no viniera, la
            misma funcion sobre la foto. Mas las que la cesta del reset
            acaba de mandar en esta misma vuelta, antes del BUY, y que la
            foto aun no trae (`lo_de_la_cesta`, desde
            `run_full_autonomous_cycle`; por jugador, sin contar dos veces
            la que la foto ya trae). Si no se sabe cuanto hay pujado, no
            se puja;
         b. el B1 cobrable es el B1 sin las fuentes (ofertas del Computer
            o publicaciones) de los jugadores de
            `la_orden_del_gestor.conservados() | protegidos()` de la orden
            viva y valida (hoy: Boye, Yamal, Chust y los demas de
            `conservar`) y sin las de los intocables de la casa (Yamal,
            `la_orden_del_gestor.INTOCABLES`, por su nombre, con orden o
            sin ella; con la orden valida, los suyos: `_intocables`). Si
            no se sabe de quien es una fuente, no se cuenta;
         Que pasa con la orden (`los_que_no_se_cobran`):
            - encendida, valida: fuera los suyos y los intocables;
            - apagada (`la_orden_del_gestor.ENV`), sin fichero o
              caducada: fuera solo los intocables (lo de main, menos
              Yamal);
            - encendida, con el fichero y que no se puede leer o no vale
              (JSON roto, vacio, sin `caduca`, un fichaje mal escrito,
              nombra a un intocable): no se puja (la caja a cero y la
              ultima puerta cerrada). Esa orden manda proteger a alguien y
              no se sabe a quien: contar su oferta como cobrable es lo que
              esta pieza viene a quitar;
         c. el T-15 de la vuelta (la capacidad, el T-15 de cada compra
            del plan y el T-15 fresco del reprecio) usa (a) y (b):
            saldo - pujas vivas - lo comprado + B1 cobrable - colchon.
       Las demas puertas (presupuesto de la via vieja, tope por
       operacion, ROI, fase, deuda) siguen igual. La caja trae ademas el
       bloque `cuenta_lo_pujado` con las cuentas de main al lado.
    2. LA ULTIMA PUERTA (`la_puja_que_no_cabe`, en `build_controlled_run`
       despues del reprecio fresco y antes de dar la puja por buena):
       nunca se puja si saldo - pujas vivas - esta puja + lo cobrable
       antes de la jornada < 0, con el saldo mas bajo de la foto y del
       mercado fresco. Si no cuadra, status V10_CUENTA_LO_PUJADO_BLOCK,
       nada enviado.
    3. EL LOG: las lineas de siempre siguen (la de «B1 trading-safe»
       ensena el B1 de la cartera, como siempre) y se anaden «Pujas
       vivas», «Caja tras pujas vivas», «B1 cobrable» y «B1 que no se
       cobra».

QUE NO HACE

    No toca la cartera de deuda segura ni la solvencia (las ven igual el
    panel, la liquidez y los demas), ni el trader de V10.6, el cerebro o
    el libro de posiciones (llaman al trader sin `para_el_buy`), ni el
    presupuesto de la via vieja, ni ninguna otra puja (la ronda, los
    chollos, la mejora, el carril y la orden tienen sus cuentas). No
    anade politica del once: el B1 ya es el que deja el once completo
    con los intocables del guardarrail fuera.

    No ve una puja puesta entre la foto de `run_cycle` y el BUY por otro
    (el dueno a mano, otro proceso): el mercado fresco del preflight
    (`execute_bid`) no trae las pujas, y leerlas seria tocar el escritor
    de todos o una lectura mas a la API. Son segundos de la misma vuelta.

    Cuando para un BUY que main habria mandado, la vuelta queda sin
    escribir (`write_used` False) y el paso 5 (contraofertas,
    publicaciones) puede correr en esa vuelta: es lo mismo que pasa en
    main en cada vuelta sin candidato (hoy todas, con la especulacion
    vieja en pausa).

EL INTERRUPTOR

    `BORDALAS_V10_CUENTA_LO_PUJADO`. Nace APAGADO. Se lee en UN sitio
    (`activo`, al llamarse; lo llaman la caja, la cesta, la ultima
    puerta, lo pujado de la caja y las lineas del log, todas de este
    modulo) y vale encendido con lo mismo que el paso 0, el tablon y el
    panel dan por encendido (`el_paso_0.ENCENDIDO`). Apagado, la caja, el
    plan, el reprecio, la puerta, el BUY y su log son main byte a byte (y
    la llamada del ciclo al BUY, la de siempre). Nunca lanza; si algo
    falla ENCENDIDO, no se puja (la caja a cero y la puerta cerrada): es
    dinero. Si la pieza no se pudiera importar, lo de main. Al importarse
    no hace nada.

AL ENCENDERLO

    1. En UN commit, sobre el ultimo main, con el arbol limpio e igual al
       commit que se sube (`git status` sin nada, ni un `.py` sin seguir
       en `src/` o `scripts/`: el inventario del paso 0 mira el disco, no
       git), y con las piezas en paralelo (la orden en los managers) ya
       en main o fuera del todo: la linea del interruptor a "1" en el
       YAML de produccion y `scripts/run_validation_gate.py --paso-0` en
       ESE arbol, al final. Si hay que tocar los literales de
       `UNO_QUE_NO_EXISTE` (`test_la_hucha_v1`,
       `test_la_prima_que_gana_v1`), ANTES del paso 0 y en ese commit,
       nunca despues. Se anaden por nombre el YAML y `config/paso_0.json`
       (nunca `add -A`, nunca `data/`) y despues la verja normal con 3.11
       y 3.13.
    2. Con la orden de hoy y la puja por Loureiro viva, el BUY tiene
       727.724 de presupuesto (no 3.193.638). Si Loureiro se pierde (jue
       07:00), 1.525.724. Hoy no cambia ninguna decision (la especulacion
       vieja esta en pausa: «Candidato: NINGUNO»); si cambian cuatro
       lineas del log y el presupuesto. Apuntarlo en la bitacora.
    3. La parte de la orden depende del interruptor de la orden
       (`la_orden_del_gestor.ENV`) y de que la orden viva (caduca el 30/11 23:59). Caducada o apagada, la
       oferta por Boye vuelve a contar como cobrable (lo de main), sin
       aviso: renovarla antes si debe seguir sin cobrarse.
    4. Cuando se levante la pausa de la especulacion vieja, mirar en el
       primer log «Pujas vivas» y «B1 cobrable».
    5. La huella de apagado (`HUELLAS_DE_MAIN` de la prueba) cubre el
       escritor, `execute_bid`, el trader, el reprecio y el log del BUY:
       si alguien los cambia a proposito, o el YAML cambia de Python, se
       vuelve a medir en un main sin tocar con
       `python -m src.analysis.test_v10_cuenta_lo_pujado_v1 --medir`, en
       3.11 y en 3.13.
"""

from __future__ import annotations

import os

from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_V10_CUENTA_LO_PUJADO"

# Lo que vale como encendido: lo mismo que `el_paso_0.ENCENDIDO` (el paso
# 0, el tablon, el panel y el ensayo). Escrito aqui para no importar nada
# al leerlo; la prueba mira que sean iguales.
ENCENDIDO = frozenset({"1", "true", "si", "sí", "yes", "on"})

GUARDIA = "V10_CUENTA_LO_PUJADO"
STATUS = "V10_CUENTA_LO_PUJADO_BLOCK"
BLOQUE = "cuenta_lo_pujado"

# Lo que la caja cambia (y guarda, como era, en `de_main`).
_LO_QUE_CAMBIA = ("cash_capacity", "trading_safe_recovery",
                  "sporting_safe_spend_capacity",
                  "projected_t15_after_buffer_before_trading")


def activo() -> bool:
    """`BORDALAS_V10_CUENTA_LO_PUJADO`, leido al llamarse. Encendido con
    lo que el paso 0 da por encendido (`ENCENDIDO`); cualquier otra cosa,
    apagado. Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in ENCENDIDO
    except Exception:                               # noqa: BLE001
        return False


def _int(valor, defecto: int = 0) -> int:
    try:
        if isinstance(valor, bool):
            return defecto
        return int(valor or 0)
    except (TypeError, ValueError):
        return defecto


def _euros(valor) -> str:
    return f"{_int(valor):,} EUR"


def _ahora() -> datetime:
    """La hora de ahora, en UTC (la que usan las funciones de la orden
    sin `ahora`). Aparte, para que las pruebas la fijen."""
    return datetime.now(timezone.utc)


def _nombre(valor) -> str:
    """Un nombre como lo compara la orden (`validar`): sin espacios a los
    lados y en minusculas."""
    return str(valor if valor is not None else "").strip().lower()


def _nombres(valor):
    """Los nombres de una lista, como los compara la orden; None si no es
    una lista."""
    if not isinstance(valor, (list, tuple)):
        return None
    return {_nombre(n) for n in valor}


# ============================================================
# (a) LO PUJADO
# ============================================================

def lo_pujado(speculation, snapshot, de_la_vuelta=None) -> tuple:
    """
    `(pujado, conocido, de_donde)`: lo comprometido en nuestras pujas
    vivas. La cuenta del bot (`build_bid_exposure`, `committed_total`):
    la que ya trae el tablero de especulacion de la vuelta
    (`ESPECULACION`) o, si no la trae, la misma funcion sobre la foto
    (`FOTO`). Mas `de_la_vuelta` (las de la cesta del reset de esta
    vuelta, de `lo_de_la_cesta`): cada una por su jugador, si la cuenta
    no trae ya una puja por el (`+CESTA`). `conocido` False si la cuenta
    no esta disponible o una puja de la vuelta no se entiende. Nunca
    lanza (si algo falla, desconocido).
    """
    try:
        exposicion = (speculation.get("bid_exposure")
                      if isinstance(speculation, dict) else None)
        de_donde = "ESPECULACION"
        if not isinstance(exposicion, dict) or "available" not in exposicion:
            from src.analysis.bid_exposure_engine import build_bid_exposure

            exposicion = build_bid_exposure(snapshot if isinstance(snapshot, dict) else {})
            de_donde = "FOTO"
        if not isinstance(exposicion, dict) or not exposicion.get("available"):
            return 0, False, de_donde
        pujado = max(_int(exposicion.get("committed_total")), 0)
        if de_la_vuelta is None:
            return pujado, True, de_donde
        if not isinstance(de_la_vuelta, (list, tuple)):
            return 0, False, de_donde
        ya = set()
        for operacion in exposicion.get("operations") or []:
            if isinstance(operacion, dict):
                ya |= _jugadores(operacion.get("player_ids")) or set()
        for puja in de_la_vuelta:
            if not isinstance(puja, dict):
                return 0, False, de_donde
            pid = _int(puja.get("player_id"))
            importe = puja.get("amount")
            if pid <= 0 or isinstance(importe, bool) or not isinstance(importe, int) \
                    or importe < 0:
                return 0, False, de_donde
            if pid not in ya:
                pujado += importe
                ya.add(pid)
        return pujado, True, f"{de_donde}+CESTA" if de_la_vuelta else de_donde
    except Exception:                               # noqa: BLE001
        return 0, False, None


def lo_de_la_cesta(subasta) -> dict:
    """
    Para el BUY de `run_full_autonomous_cycle`: las pujas que la cesta
    del reset mando en esta vuelta (`subasta["sent"]`, las enviadas),
    que van antes del BUY y que la foto del disco aun no trae, como
    argumento de `build_controlled_run` (`pujas_de_la_vuelta`). Apagado,
    o sin nada enviado: {} (la llamada de siempre). Una que no se
    entiende va sin jugador: la caja no sabe lo pujado y no puja. Nunca
    lanza.
    """
    try:
        if not activo():
            return {}
    except Exception:                               # noqa: BLE001
        return {}
    try:
        enviadas = subasta.get("sent") if isinstance(subasta, dict) else None
        if not enviadas:
            return {}
        if not isinstance(enviadas, (list, tuple)):
            return {"pujas_de_la_vuelta": [{"player_id": None, "amount": None}]}
        pujas = []
        for e in enviadas:
            if not isinstance(e, dict):
                pujas.append({"player_id": None, "amount": None})
            elif e.get("sent"):
                pujas.append({"player_id": e.get("id"), "amount": e.get("amount")})
        return {"pujas_de_la_vuelta": pujas} if pujas else {}
    except Exception:                               # noqa: BLE001
        return {"pujas_de_la_vuelta": [{"player_id": None, "amount": None}]}


# ============================================================
# (b) LO COBRABLE
# ============================================================

def los_que_no_se_cobran() -> tuple:
    """
    `(ids, nombres, estado)`: de quien no se cobra la oferta.

      - `ids`: `conservados() | protegidos()` de la orden (las funciones
        de la orden, con la de `config/` y la hora de `_ahora`).
      - `nombres`: los intocables de la casa, por su nombre:
        `la_orden_del_gestor.INTOCABLES` (Yamal) con orden o sin ella;
        con la orden valida, los suyos (`_intocables`: la orden puede
        soltar a Yamal lesionado).
      - `estado`: `VALE`, `APAGADA`, `SIN_FICHERO`, `CADUCADA`, o por
        que no vale (`NO_SE_PUEDE_LEER`, `SIN_ORDEN`, `SIN_CADUCIDAD`,
        `FICHAJE_MAL_ESCRITO`, `NOMBRA_A_UN_INTOCABLE`, `ERROR`).

    Apagada, sin fichero o caducada: `ids` vacio (lo de main, menos los
    intocables). Encendida, con el fichero y que no se puede leer o no
    vale: `ids` None (no se puja): esa orden manda proteger a alguien y
    no se sabe a quien (`protegidos()` y `conservados()` darian vacio y
    su oferta contaria como cobrable). Nunca lanza (si algo revienta,
    `ids` None).
    """
    try:
        from src.actions import la_orden_del_gestor as orden_mod

        ahora = _ahora()
        nombres = frozenset(_nombre(n) for n in orden_mod.INTOCABLES)
        if not orden_mod.activa():
            estado = "APAGADA"
        elif not Path(orden_mod.RUTA).exists():
            estado = "SIN_FICHERO"
        else:
            orden = orden_mod.leer_la_orden()
            if orden is None:
                estado = "NO_SE_PUEDE_LEER"
            else:
                estado = orden_mod.validar(orden, ahora) or "VALE"
            if estado == "VALE":
                nombres = frozenset(_nombre(n) for n in orden_mod._intocables(orden))
            elif estado != "CADUCADA":
                return None, nombres, estado
        ids = set()
        for grupo in (orden_mod.conservados(None, ahora), orden_mod.protegidos(None, ahora)):
            for pid in grupo or ():
                if _int(pid) > 0:
                    ids.add(_int(pid))
        return frozenset(ids), nombres, estado
    except Exception:                               # noqa: BLE001
        return None, frozenset(), "ERROR"


def _la_cartera_b1(portfolio):
    """(fuentes, jugadores, nombres) de la cartera que da el B1 de main:
    `trading_safe` si hay `trading_safe_total`; si no (main cae a
    `usable_total`), la de Tier B (`selected_*`, sin nombres)."""
    if not isinstance(portfolio, dict):
        return None, None, None
    if "trading_safe_total" in portfolio:
        cartera = portfolio.get("trading_safe")
        if not isinstance(cartera, dict):
            return None, None, None
        return cartera.get("sources"), cartera.get("player_ids"), cartera.get("player_names")
    return portfolio.get("selected_sources"), portfolio.get("selected_player_ids"), None


def _jugadores(valor):
    """Los ids de una lista; None si no es una lista de ids."""
    if not isinstance(valor, (list, tuple)):
        return None
    ids = set()
    for pid in valor:
        n = _int(pid)
        if n <= 0:
            return None
        ids.add(n)
    return ids


def lo_cobrable(portfolio, b1, fuera, intocables=frozenset()) -> tuple:
    """
    `(cobrable, no_se_cobran)`: el B1 (`b1`, el de main) sin las fuentes
    de los jugadores de `fuera` (ids) ni las de los `intocables` (por su
    nombre). Sin nadie fuera, el B1 entero. Una fuente sin jugadores o
    sin nombres claros, o un B1 sin fuentes con alguien fuera: no
    cobrable (no se sabe de quien es). Nunca lanza (si algo falla, nada
    cobrable).
    """
    try:
        total = max(_int(b1), 0)
        vetados = _jugadores(list(fuera)) if isinstance(fuera, (set, frozenset, list,
                                                                 tuple)) else None
        if vetados is None:
            return 0, [{"motivo": "NO_SE_SABE_QUIEN_NO_SE_COBRA", "amount": total}]
        nunca = (_nombres(list(intocables))
                 if isinstance(intocables, (set, frozenset, list, tuple)) else None)
        if nunca is None:
            return 0, [{"motivo": "NO_SE_SABE_QUIEN_NO_SE_COBRA", "amount": total}]
        if (not vetados and not nunca) or total <= 0:
            return total, []
        fuentes, jugadores, nombres = _la_cartera_b1(portfolio)
        if isinstance(fuentes, list) and fuentes:
            quitado, no = 0, []
            for fuente in fuentes:
                if not isinstance(fuente, dict):
                    return 0, [{"motivo": "FUENTE_QUE_NO_SE_ENTIENDE", "amount": total}]
                suyos = _jugadores(fuente.get("player_ids"))
                sus_nombres = _nombres(fuente.get("player_names"))
                if suyos and suyos & vetados:
                    motivo = "LA_ORDEN_DEL_GESTOR"
                elif suyos and nunca and sus_nombres is not None and sus_nombres & nunca:
                    motivo = "INTOCABLE"
                elif not suyos or (nunca and sus_nombres is None):
                    motivo = "NO_SE_SABE_DE_QUIEN"
                else:
                    continue
                importe = max(_int(fuente.get("amount")), 0)
                quitado += importe
                no.append({
                    "source_id": fuente.get("source_id"),
                    "kind": fuente.get("kind"),
                    "player_ids": sorted(suyos or ()),
                    "player_names": list(fuente.get("player_names") or []),
                    "amount": importe,
                    "motivo": motivo,
                })
            return max(total - quitado, 0), no
        suyos = _jugadores(jugadores)
        sus_nombres = _nombres(nombres)
        if (suyos and not (suyos & vetados)
                and (not nunca or (sus_nombres is not None and not (sus_nombres & nunca)))):
            return total, []
        return 0, [{"motivo": "NO_SE_SABE_DE_QUIEN", "player_ids": sorted(suyos or ()),
                    "amount": total}]
    except Exception:                               # noqa: BLE001
        return 0, [{"motivo": "ERROR"}]


# ============================================================
# (a) + (b) + (c): LA CAJA DEL BUY
# ============================================================

def la_caja_del_buy(capital, *, speculation=None, snapshot=None, de_la_vuelta=None):
    """
    Para `build_market_trader_shadow(..., para_el_buy=True)`, con la caja
    de `build_sporting_safe_capital` (y `de_la_vuelta`, las pujas de la
    cesta de esta vuelta, si las hubo). Apagado: `capital` tal cual (el
    mismo objeto). Encendido: una caja nueva con la caja = saldo - pujas
    vivas, el B1 cobrable y el T-15 con los dos, y el bloque
    `cuenta_lo_pujado`. Nunca lanza: si algo falla encendido (o no se
    sabe lo pujado, o la orden encendida no vale), la caja a cero (no se
    puja).
    """
    try:
        if not activo():
            return capital
    except Exception:                               # noqa: BLE001
        return capital
    if not isinstance(capital, dict):
        return capital
    try:
        saldo = _int(capital.get("balance"))
        colchon = _int(capital.get("safety_buffer"))
        b1 = _int(capital.get("trading_safe_recovery"))
        con_deuda = bool(capital.get("can_use_temporary_debt", False))

        pujado, sabido, de_donde = lo_pujado(speculation, snapshot, de_la_vuelta)
        fuera, intocables, orden = los_que_no_se_cobran()
        cobrable, no_se_cobran = lo_cobrable(capital.get("portfolio"), b1, fuera,
                                             intocables)
        conocido = bool(sabido and fuera is not None)

        caja = saldo - pujado
        efectivo = max(caja, 0)
        t15 = caja + cobrable - colchon
        desplegable = max(t15, 0) if con_deuda else efectivo
        if caja < 0 and not con_deuda:
            desplegable = 0
        if not conocido:
            desplegable = 0

        if not sabido:
            motivo = "No se sabe cuanto hay pujado en vivo: el BUY no puja."
        elif fuera is None:
            motivo = (f"La orden del gestor esta encendida y no vale ({orden}): no se "
                      "sabe a quien protege; el BUY no puja.")
        else:
            motivo = (f"Caja = saldo {saldo:,} - pujas vivas {pujado:,} = {caja:,}; "
                      f"B1 cobrable {cobrable:,} de {b1:,}.")
        return {
            **capital,
            "cash_capacity": efectivo,
            "trading_safe_recovery": cobrable,
            "sporting_safe_spend_capacity": max(_int(desplegable), 0),
            "projected_t15_after_buffer_before_trading": t15,
            BLOQUE: {
                "guardia": GUARDIA,
                "conocido": conocido,
                "saldo": saldo,
                "pujado": pujado,
                "de_donde": de_donde,
                "caja": caja,
                "b1": b1,
                "b1_cobrable": cobrable,
                "no_se_cobran": no_se_cobran,
                "orden": orden,
                "motivo": motivo,
                "de_main": {k: capital.get(k) for k in _LO_QUE_CAMBIA},
            },
        }
    except Exception as error:                      # noqa: BLE001
        try:
            return {
                **capital,
                "cash_capacity": 0,
                "trading_safe_recovery": 0,
                "sporting_safe_spend_capacity": 0,
                BLOQUE: {"guardia": GUARDIA, "conocido": False, "saldo": 0, "pujado": 0,
                         "caja": 0, "b1": 0, "b1_cobrable": 0, "no_se_cobran": [],
                         "motivo": (f"No se pudo hacer la cuenta ({type(error).__name__}): "
                                    "el BUY no puja.")},
            }
        except Exception:                           # noqa: BLE001
            return capital


def lo_pujado_de_la_caja(capital) -> int:
    """Lo pujado que la caja ya cuenta (el bloque de `la_caja_del_buy`);
    0 apagado (traiga lo que traiga la caja) o si la caja no lo trae (la
    caja de los demas). Para el T-15 del plan y del reprecio. Nunca
    lanza."""
    try:
        if not activo():
            return 0
        if not isinstance(capital, dict):
            return 0
        bloque = capital.get(BLOQUE)
        if not isinstance(bloque, dict):
            return 0
        return max(_int(bloque.get("pujado")), 0)
    except Exception:                               # noqa: BLE001
        return 0


# ============================================================
# (d) LA ULTIMA PUERTA
# ============================================================

def la_puja_que_no_cabe(trader, preflight, puja):
    """
    Para `build_controlled_run`, con el reprecio fresco ya aprobado y la
    puja final. Apagado: None (nada cambia). Encendido: None si
    saldo - pujas vivas - esta puja + B1 cobrable >= 0 (con el saldo mas
    bajo de la foto y del mercado fresco); si no, el motivo. Sin la
    cuenta en la caja, o sin saber lo pujado, el motivo. Nunca lanza: si
    algo falla encendido, el motivo (no se puja).
    """
    try:
        if not activo():
            return None
    except Exception:                               # noqa: BLE001
        return None
    try:
        capital = trader.get("capital") if isinstance(trader, dict) else None
        bloque = capital.get(BLOQUE) if isinstance(capital, dict) else None
        if not isinstance(bloque, dict):
            return (f"{GUARDIA}: la caja de esta vuelta no paso por la cuenta de lo "
                    "pujado: no se puja.")
        if not bloque.get("conocido"):
            return f"{GUARDIA}: {bloque.get('motivo') or 'la cuenta no se pudo hacer.'}"
        saldo = _int(bloque.get("saldo"))
        fresco = preflight.get("balance") if isinstance(preflight, dict) else None
        if fresco is not None and not isinstance(fresco, bool):
            try:
                saldo = min(saldo, int(fresco))
            except (TypeError, ValueError):
                pass
        pujado = _int(bloque.get("pujado"))
        cobrable = _int(bloque.get("b1_cobrable"))
        esta = _int(puja)
        queda = saldo - pujado - esta + cobrable
        if queda >= 0:
            return None
        return (f"{GUARDIA}: saldo {saldo:,} - pujas vivas {pujado:,} - esta puja "
                f"{esta:,} + cobrable antes de la jornada {cobrable:,} = {queda:,} < 0: "
                "no se puja (nunca empezar una jornada con saldo - pujas vivas en "
                "negativo).")
    except Exception as error:                      # noqa: BLE001
        return f"{GUARDIA}: no se pudo hacer la cuenta ({type(error).__name__}): no se puja."


# ============================================================
# EL LOG
# ============================================================

def las_lineas(capital) -> list:
    """Las lineas que se anaden al log del BUY (`print_result`) si la
    caja trae la cuenta; ninguna si no, o apagado. Nunca lanza."""
    try:
        if not activo():
            return []
        bloque = capital.get(BLOQUE) if isinstance(capital, dict) else None
        if not isinstance(bloque, dict):
            return []
        lineas = []
        if bloque.get("conocido"):
            lineas.append(f"{'Pujas vivas:':<29}{_euros(bloque.get('pujado'))}")
            lineas.append(f"{'Caja tras pujas vivas:':<29}{_euros(bloque.get('caja'))}")
        else:
            lineas.append(f"{'Pujas vivas:':<29}NO SE SABE ({bloque.get('motivo')})")
        lineas.append(f"{'B1 cobrable:':<29}{_euros(bloque.get('b1_cobrable'))}")
        fuera = [
            f"{', '.join(str(n) for n in f.get('player_names') or []) or f.get('motivo')} "
            f"{_euros(f.get('amount'))}"
            for f in bloque.get("no_se_cobran") or [] if isinstance(f, dict)
        ]
        if fuera:
            lineas.append(f"{'B1 que no se cobra:':<29}{'; '.join(fuera)}")
        return lineas
    except Exception:                               # noqa: BLE001
        return []
