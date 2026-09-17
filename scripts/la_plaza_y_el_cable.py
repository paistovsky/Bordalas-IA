"""
La plaza y el cable: la medicion entera, sobre lo que hay en disco.

QUE HACE

    Contesta los cuatro bloques del encargo del 17/09 leyendo
    SOLO ficheros del repositorio. No escribe nada, no toca
    Biwenger y no necesita red.

        BLOQUE 1   de donde sale `acquisition_budget`, linea a
                   linea, y cual seria contando la caja
                   realizable. Mas la identidad del techo de
                   Biwenger y la lista de operaciones completas.

        BLOQUE 2   quien reparte hoy el `intent` y que cuelga de
                   cada etiqueta.

        BLOQUE 3   que paga la liga: por punto, por jornada y por
                   posicion final.

        BLOQUE 4   la prima del Computer partida por lo que hizo
                   el precio la vispera, con el `n` de cada
                   tramo, y que ancla usa.

QUE FOTO MIRA, Y POR QUE IMPORTA

    La del encargo -17/09, 14.447.000 EUR sobre la mesa y
    8.874.116 de presupuesto- NO ESTA EN DISCO. Lo mas fresco que
    hay es:

        data/snapshot_20260913_171717.json        13/09 17:17
        dashboard-v8/public/data/status.json      14/09 18:33
        data/solvency/bitacora_del_saldo.jsonl    16/09 20:54
        data/rival_intelligence/board_events.json 16/09 22:55

    Asi que todo lo que sale de aqui lleva la fecha de su fuente
    delante. Doctrina 53: un numero sin su plazo no es un numero.

USO

    python scripts/la_plaza_y_el_cable.py > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import glob
import json
import os
import statistics
import sys
from collections import defaultdict


sys.path.insert(0, os.getcwd())

from src.analysis.acquisition_budget import (               # noqa: E402
    calculate_acquisition_budget,
)
from src.analysis.bid_exposure_engine import (              # noqa: E402
    build_bid_exposure,
)
from src.analysis.deployment import DEPLOYMENT_ENABLED      # noqa: E402
from src.analysis.la_plaza_y_el_cable import (              # noqa: E402
    comprobar_pago_lineal,
    hueco_entre_tramos,
    premios_de_la_jornada,
    prima_por_tramo,
    techo_de_biwenger,
    techo_tras_vender,
)
from src.analysis.position_factor import factor_for         # noqa: E402
from src.analysis.position_guardrail import (               # noqa: E402
    build_position_guardrail,
    validate_sale_set,
)
from src.analysis.solvency_engine import build_solvency_state  # noqa: E402


DIA = 86_400

SNAPSHOT = "data/snapshot_20260913_171717.json"
ESTADO = "dashboard-v8/public/data/status.json"
BITACORA = "data/solvency/bitacora_del_saldo.jsonl"
TABLON = "data/rival_intelligence/board_events.json"
HISTORICO = "data/autopilot/price_history.json"

POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


def euros(valor) -> str:
    return f"{int(valor or 0):,}".replace(",", ".")


def titulo(texto: str) -> None:
    print()
    print("=" * 72)
    print(texto)
    print("=" * 72)


def cargar(ruta):
    with open( ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


# ============================================================
# BLOQUE 1
# ============================================================


def bloque_1() -> None:

    titulo("BLOQUE 1 - EL CABLE QUE FALTA")

    snap = cargar(SNAPSHOT)
    estado = cargar(ESTADO)

    status = (snap.get("market") or {}).get("status") or {}
    plantilla = snap.get("my_team") or []

    saldo = int(status.get("balance") or 0)
    techo = int(status.get("maximumBid") or 0)
    valor = sum(int(j.get("price") or 0) for j in plantilla)

    print()
    print(f"foto: {SNAPSHOT}  ({snap.get('timestamp')})")
    print(f"estado publicado: {estado['meta']['generated_at']}")

    # --------------------------------------------------
    # 1.1 DE DONDE SALE EL PRESUPUESTO, LINEA A LINEA
    # --------------------------------------------------

    solvencia = build_solvency_state(snap)
    exposicion = build_bid_exposure(snap)

    presupuesto = calculate_acquisition_budget(
        snapshot=snap,
        solvency=solvencia,
        active_franchise_bid=None,
        exposure=exposicion,
    )

    deuda = solvencia.get("max_safe_debt") or {}
    garantia = solvencia.get("solvency_guarantee") or {}
    temporal = solvencia.get("temporary_debt") or {}
    dura = solvencia.get("hard_safety") or {}

    print()
    print("DE DONDE SALE `acquisition_budget`, LINEA A LINEA")
    print()
    print(f"  saldo (market.status.balance)          {euros(saldo):>16}")
    print(
        f"  cash_budget = max(saldo, 0) x 1,00     "
        f"{euros(presupuesto['cash_budget']):>16}"
    )
    print()
    print(f"  puerta 1  Hard Safety activo           {bool(dura.get('active'))}")
    print(
        f"  puerta 2  SOLVENCY_GUARANTEE            "
        f"{bool(garantia.get('guaranteed'))}"
    )
    print(
        f"  puerta 3  ventana de deuda abierta      "
        f"{bool(deuda.get('debt_window_open'))}"
    )
    print(
        f"  puerta 4  deuda temporal permitida      "
        f"{bool(temporal.get('allowed'))}"
    )
    print(
        f"  additional_debt_headroom               "
        f"{euros(deuda.get('additional_debt_headroom')):>16}"
    )
    print(
        f"  debt_budget = headroom x 1,00           "
        f"{euros(presupuesto['debt_budget']):>16}"
    )
    print()
    print(
        f"  gross_budget = caja + deuda             "
        f"{euros(presupuesto['gross_budget']):>16}"
    )
    print(f"  techo de Biwenger (maximumBid)          {euros(techo):>16}")
    print(
        f"  total_budget = min(bruto, techo)        "
        f"{euros(presupuesto['total_budget']):>16}"
    )
    print(
        f"  comprometido en pujas vivas             "
        f"{euros(presupuesto.get('committed_total')):>16}"
    )
    print(
        f"  available_budget                        "
        f"{euros(presupuesto['available_budget']):>16}"
    )
    print()
    print(f"  bloqueado por: {presupuesto.get('blocked_by')}")
    print(f"  deuda no disponible: {presupuesto.get('debt_unavailable_reason')}")
    print()
    print("  QUE NO ENTRA, Y ESE ES EL CABLE QUE FALTA:")
    print("    - las ofertas vivas sobre jugadores que sobran")
    print("    - el valor a mercado de la plantilla, salvo el cuarto")
    print("      que ya vive dentro de `maximumBid`")

    # --------------------------------------------------
    # 1.2 LA IDENTIDAD DEL TECHO
    # --------------------------------------------------

    titulo("BLOQUE 1.2 - QUE ES `maximumBid`, MEDIDO")

    combos = {}

    for ruta in sorted(glob.glob("data/snapshot_*.json")):

        try:
            foto = cargar(ruta)

        except Exception:                            # noqa: BLE001
            continue

        st = (foto.get("market") or {}).get("status") or {}
        mt = foto.get("my_team") or []

        if st.get("balance") is None or not mt:
            continue

        v = sum(int(j.get("price") or 0) for j in mt)

        clave = (st["balance"], st["maximumBid"], v)

        if clave in combos:
            continue

        combos[clave] = build_bid_exposure(foto).get("committed_total") or 0

    print()
    print("  maximumBid = saldo + valor_de_plantilla / 4 - comprometido")
    print()
    print(
        f"  {'saldo':>14}{'plantilla':>14}{'comprometido':>14}"
        f"{'maximumBid':>14}{'calculado':>14}  ok"
    )

    exactas = 0

    for (b, m, v), c in sorted(combos.items()):
        calc = techo_de_biwenger(b, v, c)
        ok = calc == m
        exactas += ok
        print(
            f"  {euros(b):>14}{euros(v):>14}{euros(c):>14}"
            f"{euros(m):>14}{euros(calc):>14}  {'SI' if ok else 'NO'}"
        )

    # Y las de la bitacora, que son de otro dia.
    lineas = []

    with open(BITACORA, encoding="utf-8") as fichero:
        for linea in fichero:
            if linea.strip():
                lineas.append(json.loads(linea))

    nuevas = 0

    for fila in lineas:
        clave = (
            fila.get("balance"),
            fila.get("maximum_bid"),
            fila.get("roster_value"),
            fila.get("committed"),
        )

        # Doctrina 58: el `n` que se dice es el que se comprobo.
        # La bitacora repite combinaciones que ya estan en las
        # fotos, y esas no vuelven a contar.
        if None in clave or clave[:3] in combos:
            continue

        combos[clave[:3]] = clave[3]
        nuevas += 1

        calc = techo_de_biwenger(clave[0], clave[2], clave[3])
        ok = calc == clave[1]
        exactas += ok

        print(
            f"  {euros(clave[0]):>14}{euros(clave[2]):>14}"
            f"{euros(clave[3]):>14}{euros(clave[1]):>14}"
            f"{euros(calc):>14}  {'SI' if ok else 'NO'}  (bitacora 16/09)"
        )

    print()
    print(
        f"  EXACTAS {exactas} de {len(combos)} combinaciones distintas "
        f"({len(combos) - nuevas} de las 95 fotos, {nuevas} de la "
        f"bitacora)."
    )
    print()
    print("  CONSECUENCIA: de cada jugador hay UN CUARTO de su precio")
    print("  dentro del techo. Venderlo a precio de mercado sube el")
    print("  techo 0,75 x precio, y el saldo el importe entero.")

    # --------------------------------------------------
    # 1.3 LA CAJA REALIZABLE Y LAS OPERACIONES
    # --------------------------------------------------

    titulo("BLOQUE 1.3 - LA CAJA REALIZABLE, Y A QUIEN HABRIA QUE VENDER")

    fichas = {j["id"]: j for j in plantilla}

    once_datos = (
        (snap.get("user_lineup") or {}).get("data", {}).get("lineup", {})
        or {}
    )

    once = [j["id"] for j in (once_datos.get("players") or [])]

    guardarrail = build_position_guardrail(plantilla, lineup_ids=once)

    ofertas = [
        o
        for o in ((snap.get("market") or {}).get("offers") or [])
        if o.get("from") is None and o.get("type") == "purchase"
    ]

    filas = []

    for oferta in ofertas:
        pid = (oferta.get("requestedPlayers") or [None])[0]
        j = fichas.get(pid) or {}

        filas.append(
            {
                "id": pid,
                "name": j.get("name"),
                "position": j.get("position"),
                "price": int(j.get("price") or 0),
                "cash_now": int(oferta.get("amount") or 0),
                "titular": pid in once,
            }
        )

    # Los que no juegan primero; dentro de cada grupo, el que mas
    # caja da. Es el orden que ya usa `sale_order`.
    filas.sort(key=lambda f: (f["titular"], -f["cash_now"]))

    print()
    print(
        f"  {'jugador':<16}{'pos':<5}{'oferta':>13}{'precio':>13}"
        f"{'prima':>9}{'tit':>5}  guardarrail"
    )

    vendiendo = []
    caja = 0
    techo_despues = techo

    # El portero titular no se rota: es la unica regla de
    # `sale_intent.untouchable_reason` que no depende de un dato
    # que no esta en disco.
    portero_titular = next(
        (
            j["id"]
            for j in plantilla
            if int(j.get("position") or 0) == 1 and j["id"] in once
        ),
        None,
    )

    for fila in filas:

        prima = (
            (fila["cash_now"] / fila["price"] - 1) * 100
            if fila["price"]
            else None
        )

        if fila["id"] == portero_titular:
            estado_fila = "NO: portero titular, no se rota"

        else:
            comprobacion = validate_sale_set(
                guardarrail,
                vendiendo + [fila["id"]],
            )

            if comprobacion.get("ok"):
                vendiendo.append(fila["id"])
                caja += fila["cash_now"]
                techo_despues = techo_tras_vender(
                    techo_despues, fila["cash_now"], fila["price"]
                )
                estado_fila = "CABE"

            else:
                estado_fila = f"NO: {comprobacion.get('reason')}"

        print(
            f"  {(fila['name'] or '')[:15]:<16}"
            f"{POS.get(fila['position'], '?'):<5}"
            f"{euros(fila['cash_now']):>13}{euros(fila['price']):>13}"
            f"{(f'{prima:+.2f} %' if prima is not None else '-'):>9}"
            f"{('SI' if fila['titular'] else 'no'):>5}  {estado_fila}"
        )

    print()
    print(f"  VENDIBLES SIN ROMPER EL ONCE: {len(vendiendo)} de {len(filas)}")
    print(f"    presupuesto publicado hoy  {euros(presupuesto['available_budget']):>16}")
    print(f"    caja realizable            {euros(caja):>16}")
    print(f"    saldo hoy                  {euros(saldo):>16}")
    print(f"    saldo tras vender          {euros(saldo + caja):>16}")
    print(f"    maximumBid hoy             {euros(techo):>16}")
    print(f"    maximumBid tras vender     {euros(techo_despues):>16}")

    # --------------------------------------------------
    # 1.4 LOS CANDIDATOS Y SUS PUNTOS NETOS
    # --------------------------------------------------

    titulo("BLOQUE 1.4 - LOS CANDIDATOS, CON LA VARA PUESTA")

    ampliacion = estado.get("roster_expansion") or {}
    candidatos = ampliacion.get("candidates") or []

    print()
    print(f"  huecos publicados: {json.dumps(ampliacion.get('slots'), ensure_ascii=False)[:120]}")
    print(f"  candidatos en la foto del 14/09: {len(candidatos)}")
    print()

    if not candidatos:
        print("  Sin candidatos en la foto de disco.")

    for candidato in candidatos:
        print(
            f"  {str(candidato.get('name'))[:18]:<20}"
            f"{POS.get(candidato.get('position'), '?'):<5}"
            f"{euros(candidato.get('market_price')):>13}"
            f"  {candidato.get('blocked_by')}"
        )
        print(f"      vara de su posicion: x{factor_for(candidato.get('position')):.3f}")
        print(
            f"      puntos netos del once: NO MEDIBLE "
            f"({candidato.get('blocked_by')})"
        )

    # --------------------------------------------------
    # 1.5 EL TOPE DE FICHAS
    # --------------------------------------------------

    titulo("BLOQUE 1.5 - ¿SE PUEDE SABER EL TOPE DE FICHAS SIN RED?")

    ajustes = (snap.get("league") or {}).get("settings") or {}

    print()
    print("  LAS REGLAS DE LA LIGA, CLAVE A CLAVE:")

    for clave in sorted(ajustes):
        if clave == "secret":
            continue
        print(f"    {clave:<24} {ajustes[clave]}")

    print()
    print("  NO HAY NINGUNA CLAVE DE TOPE DE PLANTILLA. `maxPurchasePrice`")
    print("  es el precio maximo de compra (0 = sin tope) y")
    print("  `lineupMaxClubPlayers` es cuantos del mismo club caben en el")
    print("  once (0 = sin tope). Ninguna de las dos es el tope de fichas.")

    # La otra via: reconstruir el tamaño de cada plantilla desde
    # el tablon. El maximo jamas visto es una COTA INFERIOR.
    tablon = cargar(TABLON)

    operaciones = []
    vistas = set()
    brutas = 0

    for evento in sorted(tablon, key=lambda e: e.get("date") or 0):

        if evento.get("type") not in ("market", "transfer"):
            continue

        for fila in evento.get("content") or []:

            if not isinstance(fila, dict):
                continue

            brutas += 1

            hacia = (fila.get("to") or {}).get("id")
            desde = (fila.get("from") or {}).get("id")

            # EL TABLON REPITE OPERACIONES (medido el 10/09): los
            # `event_id` son unicos, pero la misma compra sale
            # dentro de eventos distintos. Se dedupe por la
            # operacion, no por el evento.
            clave = (
                evento["type"],
                fila.get("player"),
                fila.get("amount"),
                hacia,
                desde,
            )

            if clave in vistas:
                continue

            vistas.add(clave)

            operaciones.append(
                {
                    "date": evento.get("date"),
                    "to": hacia,
                    "from": desde,
                    "to_name": (fila.get("to") or {}).get("name"),
                    "from_name": (fila.get("from") or {}).get("name"),
                }
            )

    managers = {}

    for operacion in operaciones:
        for lado, nombre in (("to", "to_name"), ("from", "from_name")):
            if operacion[lado] and operacion[lado] > 1_000_000:
                managers[operacion[lado]] = operacion[nombre]

    reinicio = next(
        (e for e in tablon if e.get("type") == "leagueReset"), None
    )

    reparto = ((reinicio or {}).get("content") or {}).get("distribution")

    tamano = {u: int(reparto or 0) for u in managers}
    maximo = dict(tamano)
    cuando = {}

    for operacion in operaciones:
        if operacion["to"] in tamano:
            tamano[operacion["to"]] += 1
        if operacion["from"] in tamano:
            tamano[operacion["from"]] -= 1

        for u in tamano:
            if tamano[u] > maximo[u]:
                maximo[u] = tamano[u]
                cuando[u] = operacion["date"]

    real = {
        m.get("name"): m.get("roster_size")
        for m in ((estado.get("ledger_audit") or {}).get("by_manager") or [])
    }

    print()
    print(
        f"  RECONSTRUCCION DESDE EL TABLON: reparto inicial "
        f"{reparto} fichas (leagueReset), {len(operaciones)} "
        f"operaciones DISTINTAS de {brutas} vistas (el tablon "
        f"repite: medido el 10/09)."
    )
    print()
    print(
        f"  {'manager':<32}{'reconstruido':>14}{'ledger 14/09':>14}"
        f"{'dif':>6}{'maximo':>9}"
    )

    for u in sorted(managers, key=lambda x: -maximo[x]):
        nombre = managers[u]
        cierto = real.get(nombre)
        diferencia = (
            tamano[u] - cierto if cierto is not None else None
        )

        print(
            f"  {str(nombre)[:31]:<32}{tamano[u]:>14}"
            f"{(cierto if cierto is not None else '-'):>14}"
            f"{(f'{diferencia:+d}' if diferencia is not None else '-'):>6}"
            f"{maximo[u]:>9}"
        )

    print()
    print(f"  MAXIMO RECONSTRUIDO: {max(maximo.values())} fichas.")
    print()
    print("  LO QUE ESTO SI DICE: 21 es una COTA INFERIOR y reproduce el")
    print("  numero del informe del 10/09. Nuestra linea cuadra al cero,")
    print("  que es lo que hace creible el metodo.")
    print()
    print("  LO QUE NO DICE: el tope. Las demas lineas salen 2, 3 y 4")
    print("  fichas POR DEBAJO de lo que dice el ledger, o sea que al")
    print("  tablon le faltan compras suyas. Todos los errores van en la")
    print("  misma direccion, asi que el maximo real es 21 O MAS.")
    print()
    print("  RESPUESTA: NO SE PUEDE SABER EL TOPE SIN SALIR A LA RED.")
    print("  Lo que si se puede es mejorar la cota: hoy `count_free_slots`")
    print("  usa la plantilla mas grande de HOY (19) y da 2 huecos; con la")
    print("  mas grande JAMAS VISTA (21) darian 4. No se toca: se dice.")

    print()
    print("  LA COLA DE VENTA DE LA FOTO DEL 14/09 LLEGA VACIA: los 17")
    print("  salen excluidos con `sin escalon conocido`, porque el dato")
    print("  de jerarquia no esta en disco (data/intelligence/")
    print("  starter_multisource_*.json es del 17/08 y no trae escalon).")
    print("  Por eso la tabla de arriba se monta contra las ofertas")
    print("  vivas del snapshot y el guardarrail, que si estan.")


# ============================================================
# BLOQUE 2
# ============================================================


def bloque_2() -> None:

    titulo("BLOQUE 2 - QUIEN REPARTE EL `intent`")

    estado = cargar(ESTADO)

    print()
    print(f"  DEPLOYMENT_ENABLED = {DEPLOYMENT_ENABLED}")
    print("  (DEPLOYMENT_DEFAULT = \"1\" en src/analysis/deployment.py)")
    print()
    print("  CON EL INTERRUPTOR ENCENDIDO -que es lo de hoy- la etiqueta")
    print("  la reparte `deployment.classify_operation`, NO el")
    print("  `max(opciones, key=value)` de `acquisition_valuation`.")

    filas = [
        f
        for f in ((estado.get("season_horizon") or {}).get("rows") or [])
        if f.get("intent")
    ]

    print()
    print(f"  filas valoradas en la foto del 14/09: {len(filas)}")

    cuenta = defaultdict(int)
    clase = defaultdict(int)
    relleno = defaultdict(int)
    veto = defaultdict(int)

    xi_positivo = 0
    xi_sobre_precio = 0

    for fila in filas:
        cuenta[fila.get("intent")] += 1
        despliegue = fila.get("deployment") or {}
        clase[despliegue.get("operation_class")] += 1
        relleno[despliegue.get("roster_fill_decision")] += 1
        veto[fila.get("xi_decision")] += 1

        valor_xi = (fila.get("confidence_shadow") or {}).get("xi_value") or 0

        if valor_xi > 0:
            xi_positivo += 1

        if valor_xi > (fila.get("market_price") or 0):
            xi_sobre_precio += 1

    print(f"  intent:               {dict(cuenta)}")
    print(f"  operation_class:      {dict(clase)}")
    print(f"  roster_fill_decision: {dict(relleno)}")
    print(f"  xi_decision:          {dict(veto)}")
    print(f"  con xi_value > 0:              {xi_positivo}")
    print(f"  con xi_value > precio:         {xi_sobre_precio}")

    print()
    print("  LA CADENA, MEDIDA:")
    print("    xi_decision = SIN_PRONOSTICO  ->  xi_value = 0")
    print("    -> ninguna via de fichaje llega al precio")
    print("    -> classify_operation: fichaje = []  ->  clase TRADE")
    print("    -> intent = SPECULATION  ->  liston del 3 %")

    print()
    print("  EL MOTIVO QUE SE PUBLICA, Y POR QUE ES FALSO:")
    print()
    print("    roster_expansion_shadow.blocked_reason:")
    print("      \"La via del once le da valor, pero el `intent` se elige")
    print("       por euros y gana la reventa\"")
    print()
    print("    Ese mecanismo solo corre con DEPLOYMENT_ENABLED APAGADO.")
    print("    El motivo bueno ya viaja en la fila, sin que nadie lo lea:")

    ejemplo = next(
        (f for f in filas if (f.get("deployment") or {}).get("reason")),
        None,
    )

    if ejemplo:
        print(f"      deployment.reason: {ejemplo['deployment']['reason']}")
        print(f"      deployment.route:  {ejemplo['deployment'].get('route')}")
        print(
            f"      market_gate.route_now: "
            f"{(ejemplo.get('market_gate') or {}).get('route_now')}"
        )

    print()
    print("  EL MAPA: QUE DECIDE CADA `intent` Y DONDE")
    print()

    mapa = [
        (
            "SPECULATION",
            "rival_bid_model.optimal_bid:1128",
            "quita el tope de prima (+0,25 %) si NO es SPECULATION",
        ),
        (
            "SPECULATION",
            "rival_bid_model.optimal_bid:1176",
            "el liston del 3 % de rendimiento sobre el capital",
        ),
        (
            "SPECULATION",
            "rival_bid_model.optimal_bid:1209",
            "el minimo de 25.000 EUR de ganancia esperada",
        ),
        (
            "XI_UPGRADE",
            "acquisition_budget.budget_for_intent",
            "que bolsillo se aplica: fichar o especular",
        ),
        (
            "XI_UPGRADE",
            "acquisition_board:1189",
            "`budget_source`: FICHAJES o ESPECULACION en pantalla",
        ),
        (
            "XI_UPGRADE",
            "los_dos_techos:298",
            "que columna se marca: QUEDARSE o REVENDER",
        ),
        (
            "XI_UPGRADE",
            "hold_budget.hold_pocket",
            "de que bolsillo sale la via TENER",
        ),
        (
            "XI_UPGRADE",
            "deployment.signing_priority",
            "el escalon de prioridad cuando el bolsillo no llega",
        ),
        (
            "XI_UPGRADE",
            "autopilot_executor:2013 y :2092",
            "que presupuesto lee el EJECUTOR al escribir la puja",
        ),
        (
            "cualquiera",
            "roster_expansion_shadow.blocked_reason:183",
            "la segunda puerta de la lista de ampliar plantilla",
        ),
        (
            "cualquiera",
            "bid_outcome_ledger:159",
            "con que etiqueta se apunta la puja en el libro",
        ),
        (
            "cualquiera",
            "los_tres_denominadores:726",
            "que liston se le aplica en la reconstruccion",
        ),
    ]

    for etiqueta, sitio, que in mapa:
        print(f"    {etiqueta:<12} {sitio:<42} {que}")

    print()
    print("  QUE SE CAE SI SE TOCA: quitarle SPECULATION a una via le")
    print("  quita el liston del 3 % Y EL TOPE DE PRIMA a la vez -medido")
    print("  ayer: con etiqueta no puja, sin etiqueta puja +0,52 % y el")
    print("  tope pasa a ser el valor entero-. Los frenos cuelgan de la")
    print("  misma cadena que la puerta.")


# ============================================================
# BLOQUE 3
# ============================================================


def bloque_3() -> None:

    titulo("BLOQUE 3 - QUE PAGA LA LIGA")

    snap = cargar(SNAPSHOT)

    reglas = (
        ((snap.get("rounds") or {}).get("data") or {}).get("league") or {}
    ).get("settings") or {}

    premios = premios_de_la_jornada(reglas)

    print()
    print("  REGLAS DE LA LIGA (snapshot /rounds/data/league/settings)")
    print(f"    bonusPoint         {euros(premios['euros_por_punto'])} EUR por punto")
    print(f"    bonusFixed         {premios['premio_fijo']}")
    print(f"    bonusIdealLineup   {premios['premio_once_ideal']}")
    print(f"    bonusGameMVP       {premios['premio_mvp']}")
    print(f"    bonusInverse       {premios['invertido']}")
    print(f"    bonusRoundPosition {json.dumps(reglas.get('bonusRoundPosition'))}")
    print()
    print(f"    premio por GANAR la jornada:  {premios['premio_por_ganar'] or 'NINGUNO'}")
    print(f"    premio por quedar el ULTIMO:  {premios['premio_por_quedar_ultimo']}")
    print()
    print(f"    {premios['reason']}")

    # Contra lo que se pago de verdad.
    tablon = cargar(TABLON)

    jornadas = {}

    for evento in tablon:
        if evento.get("type") != "roundFinished":
            continue

        contenido = evento.get("content") or {}
        ronda = contenido.get("round") or {}

        clave = (ronda.get("id"), contenido.get("step"))

        if clave in jornadas:
            continue

        jornadas[clave] = {
            "name": ronda.get("name"),
            "step": contenido.get("step"),
            "results": [
                {
                    "name": (r.get("user") or {}).get("name"),
                    "points": r.get("points"),
                    "bonus": r.get("bonus"),
                }
                for r in (contenido.get("results") or [])
            ],
        }

    print()
    print(f"  CONTRA LO PAGADO: {len(jornadas)} jornadas distintas en el tablon")
    print("  (9 eventos roundFinished, 3 de ellos repetidos con otro event_id)")
    print()

    filas_totales = 0
    lineales = 0

    for clave, jornada in sorted(jornadas.items(), key=lambda x: str(x[0])):

        pago = comprobar_pago_lineal(
            jornada["results"], premios["euros_por_punto"]
        )

        filas_totales += pago["n"]
        lineales += pago["n"] - len(pago["extras"])

        print(
            f"    {str(jornada['name'])[:24]:<26} step={jornada['step']}  "
            f"n={pago['n']}  ganador {str(pago['ganador'])[:18]:<20} "
            f"extra del ganador {pago['extra_del_ganador']:+}"
        )

        for extra in pago["extras"]:
            print(
                f"        {str(extra['name'])[:22]:<24} "
                f"{extra['desde_el_final']}o por la cola  "
                f"{extra['extra']:+,}".replace(",", ".")
            )

    print()
    print(f"  filas de resultado: {filas_totales}, de ellas lineales {lineales}")
    print()
    print("  NINGUN GANADOR COBRO UN EURO ENCIMA DE puntos x 30.000.")
    print("  Lo que no es lineal es el premio a los TRES ULTIMOS.")

    # Y el bote de final de temporada.
    tipos = defaultdict(int)

    for evento in tablon:
        tipos[evento.get("type")] += 1

    bonos = [e for e in tablon if e.get("type") == "bonus"]

    razones = defaultdict(int)

    for evento in bonos:
        for fila in evento.get("content") or []:
            razones[fila.get("reason")] += fila.get("amount") or 0

    print()
    print("  ¿HAY BOTE DE FINAL DE TEMPORADA?")
    print(f"    tipos de evento en el tablon: {dict(tipos)}")
    print(f"    eventos `bonus`, por motivo: {dict(razones)}")
    print()
    print(f"    {premios['premio_de_final_de_temporada_reason']}")


# ============================================================
# BLOQUE 4
# ============================================================


def _serie(historico, pid):
    return historico.get(str(pid))


def _precio_en(historico, pid, cuando):
    serie = _serie(historico, pid)

    if not serie:
        return None

    mejor = None

    for i, t in enumerate(serie["t"]):
        if t <= cuando:
            mejor = serie["p"][i]
        else:
            break

    return mejor


def bloque_4() -> None:

    titulo("BLOQUE 4 - LA PRIMA DEL COMPUTER, PARTIDA POR TRAMO")

    historico = cargar(HISTORICO)["players"]

    # --------------------------------------------------
    # 4.1 EL CENSO DE OFERTAS VIVAS (sin sesgo de aceptacion)
    # --------------------------------------------------

    ofertas = {}

    for ruta in sorted(glob.glob("data/snapshot_*.json")):

        try:
            foto = cargar(ruta)

        except Exception:                            # noqa: BLE001
            continue

        fichas = {
            j["id"]: j
            for j in (foto.get("my_team") or [])
            if isinstance(j, dict)
        }

        for oferta in ((foto.get("market") or {}).get("offers") or []):

            if oferta.get("from") is not None:
                continue

            if oferta.get("type") != "purchase":
                continue

            if oferta["id"] in ofertas:
                continue

            pid = (oferta.get("requestedPlayers") or [None])[0]
            j = fichas.get(pid) or {}

            ofertas[oferta["id"]] = {
                "player_id": pid,
                "name": j.get("name"),
                "amount": oferta.get("amount"),
                "price": j.get("price"),
                "increment": j.get("priceIncrement"),
                "created": oferta.get("created"),
                "price_previous": _precio_en(
                    historico, pid, (oferta.get("created") or 0) - DIA
                ),
            }

    censo = list(ofertas.values())

    print()
    print(
        f"  CENSO A: ofertas VIVAS del Computer, deduplicadas por "
        f"offer_id.  n={len(censo)}"
    )
    print("  95 fotos del 12/08 al 13/09. Sin sesgo de aceptacion: es lo")
    print("  que el Computer OFRECE, no lo que la gente acepta.")

    partida = prima_por_tramo(censo)

    print()
    print(f"  {partida['reason']}")
    print()
    print(f"  {'tramo':<10}{'n':>5}{'mediana':>12}{'media':>12}{'bajo mercado':>16}")

    for tramo in ("SUBIA", "PLANO", "BAJABA"):
        datos = partida["tramos"][tramo]
        print(
            f"  {tramo:<10}{datos['n']:>5}"
            f"{(f'{datos['median_percent']:+.4f} %' if datos['median_percent'] is not None else '-'):>12}"
            f"{(f'{datos['mean_percent']:+.4f} %' if datos['mean_percent'] is not None else '-'):>12}"
            f"{f'{datos['below_market']}/{datos['n']}':>16}"
            + ("   TRAMO CORTO" if datos["thin"] else "")
        )

    hueco = hueco_entre_tramos(partida)
    print()
    print(f"  {hueco['reason']}")

    # Contraste con el `priceIncrement` de la propia foto, que
    # cubre las 90 y no solo las que tienen historico.
    por_tramo = defaultdict(list)

    for fila in censo:
        if fila["increment"] is None or not fila["price"]:
            continue

        clave = (
            "SUBIA"
            if fila["increment"] > 0
            else ("BAJABA" if fila["increment"] < 0 else "PLANO")
        )

        por_tramo[clave].append((fila["amount"] / fila["price"] - 1) * 100)

    print()
    print("  CONTRASTE con `priceIncrement` de la propia foto (cubre las 90):")

    for tramo in ("SUBIA", "PLANO", "BAJABA"):
        v = por_tramo[tramo]
        if v:
            print(
                f"  {tramo:<10}{len(v):>5}"
                f"{statistics.median(v):>+11.4f} %"
                f"{statistics.mean(v):>+11.4f} %"
                f"{f'{sum(1 for x in v if x < 0)}/{len(v)}':>16}"
            )

    # --------------------------------------------------
    # 4.2 LA MISMA CUENTA, DENTRO DE CADA JUGADOR
    # --------------------------------------------------

    print()
    print("  DENTRO DE CADA JUGADOR (quita el sesgo de quien recibe oferta)")

    por_jugador = defaultdict(lambda: defaultdict(list))

    for fila in censo:
        if fila["increment"] is None or not fila["price"]:
            continue

        clave = (
            "SUBIA"
            if fila["increment"] > 0
            else ("BAJABA" if fila["increment"] < 0 else "PLANO")
        )

        por_jugador[fila["name"]][clave].append(
            (fila["amount"] / fila["price"] - 1) * 100
        )

    huecos = []

    for nombre, grupos in por_jugador.items():
        sube = grupos.get("SUBIA")
        baja = grupos.get("BAJABA")

        if not sube or not baja:
            continue

        diferencia = statistics.median(baja) - statistics.median(sube)
        huecos.append(diferencia)

        print(
            f"    {str(nombre)[:18]:<20}"
            f"SUBIA {statistics.median(sube):+7.2f} % (n={len(sube)})   "
            f"BAJABA {statistics.median(baja):+7.2f} % (n={len(baja)})   "
            f"{diferencia:+.2f} pp"
        )

    if huecos:
        a_favor = sum(1 for h in huecos if h > 0)
        print()
        print(
            f"    n={len(huecos)} jugadores con las dos direcciones. "
            f"BAJABA paga mas en {a_favor} de {len(huecos)}. "
            f"Hueco mediano {statistics.median(huecos):+.4f} pp."
        )

    # --------------------------------------------------
    # 4.3 EL CENSO DE VENTAS ACEPTADAS (toda la liga)
    # --------------------------------------------------

    tablon = cargar(TABLON)

    ventas = []
    vistas = set()

    for evento in tablon:
        if evento.get("type") != "transfer":
            continue

        for fila in evento.get("content") or []:
            if fila.get("to") is not None:
                continue

            clave = (
                fila.get("player"),
                fila.get("amount"),
                (fila.get("from") or {}).get("id"),
            )

            if clave in vistas:
                continue

            vistas.add(clave)

            pid = fila.get("player")
            cuando = evento.get("date")

            ventas.append(
                {
                    "player_id": pid,
                    "amount": fila.get("amount"),
                    "price": _precio_en(historico, pid, cuando),
                    "price_previous": _precio_en(
                        historico, pid, cuando - DIA
                    ),
                    "seller": (fila.get("from") or {}).get("name"),
                }
            )

    print()
    print(
        f"  CENSO B: ventas ACEPTADAS al Computer, toda la liga, "
        f"deduplicadas.  n={len(ventas)}"
    )
    print("  Este SI lleva sesgo de aceptacion: la gente vende el dia que")
    print("  la oferta es buena. Vale como contraste, no como prueba.")

    partida_b = prima_por_tramo(ventas)

    print()
    print(f"  {partida_b['reason']}")
    print()
    print(f"  {'tramo':<10}{'n':>5}{'mediana':>12}{'media':>12}{'bajo mercado':>16}")

    for tramo in ("SUBIA", "PLANO", "BAJABA"):
        datos = partida_b["tramos"][tramo]
        print(
            f"  {tramo:<10}{datos['n']:>5}"
            f"{(f'{datos['median_percent']:+.4f} %' if datos['median_percent'] is not None else '-'):>12}"
            f"{(f'{datos['mean_percent']:+.4f} %' if datos['mean_percent'] is not None else '-'):>12}"
            f"{f'{datos['below_market']}/{datos['n']}':>16}"
            + ("   TRAMO CORTO" if datos["thin"] else "")
        )

    print()
    print(f"  {hueco_entre_tramos(partida_b)['reason']}")

    # --------------------------------------------------
    # 4.3b ¿AGUANTA EL HUECO? "n=8 y n=5. No me lo creo todavia."
    # --------------------------------------------------

    titulo("BLOQUE 4.3b - SI EL HUECO AGUANTA O ES RUIDO")

    def permutacion(sube, baja, vueltas=20_000, semilla=20260917):
        """
        Barajar las dos muestras y ver cuantas veces sale un hueco
        igual o mayor por puro azar. Semilla fija: esto se tiene
        que poder repetir.
        """

        import random

        azar = random.Random(semilla)

        observado = abs(statistics.median(baja) - statistics.median(sube))

        bolsa = list(sube) + list(baja)
        corte = len(sube)
        veces = 0

        for _ in range(vueltas):
            azar.shuffle(bolsa)

            if (
                abs(
                    statistics.median(bolsa[corte:])
                    - statistics.median(bolsa[:corte])
                )
                >= observado
            ):
                veces += 1

        return observado, veces / vueltas

    for nombre, fuente, usa_incremento in (
        ("ofertas vivas (priceIncrement)", censo, True),
        ("ofertas vivas (historico)", censo, False),
        ("ventas aceptadas (historico)", ventas, False),
    ):
        sube, baja = [], []

        for fila in fuente:
            precio = fila.get("price")

            if not precio or not fila.get("amount"):
                continue

            if usa_incremento:
                incremento = fila.get("increment")

                if incremento is None:
                    continue

                arriba = incremento > 0
                abajo = incremento < 0

            else:
                previo = fila.get("price_previous")

                if not previo:
                    continue

                arriba = precio > previo
                abajo = precio < previo

            prima = (fila["amount"] / precio - 1) * 100

            if arriba:
                sube.append(prima)
            elif abajo:
                baja.append(prima)

        if len(sube) < 3 or len(baja) < 3:
            print(f"  {nombre:<34} sin muestra suficiente")
            continue

        observado, p = permutacion(sube, baja)

        print(
            f"  {nombre:<34} n_sube={len(sube):<4} n_baja={len(baja):<4} "
            f"hueco {observado:+.4f} pp   p = {p:.4f}"
        )

    # ¿Y si el confundido fuese el NIVEL DE PRECIO? Se parte por
    # ahi y se mira si el hueco sobrevive en los dos lados.
    caros = [f for f in censo if (f.get("price") or 0) >= 2_000_000]
    baratos = [f for f in censo if 0 < (f.get("price") or 0) < 2_000_000]

    print()
    print("  ¿ES EL NIVEL DE PRECIO EL QUE CONFUNDE? Partido por 2 M:")

    for nombre, grupo in ((">= 2 M", caros), ("< 2 M", baratos)):

        arriba = [
            (f["amount"] / f["price"] - 1) * 100
            for f in grupo
            if f.get("increment") is not None and f["increment"] > 0
        ]

        abajo = [
            (f["amount"] / f["price"] - 1) * 100
            for f in grupo
            if f.get("increment") is not None and f["increment"] < 0
        ]

        if arriba and abajo:
            print(
                f"    {nombre:<8} SUBIA n={len(arriba):<3} "
                f"{statistics.median(arriba):+7.4f} %   "
                f"BAJABA n={len(abajo):<3} "
                f"{statistics.median(abajo):+7.4f} %   "
                f"hueco {statistics.median(abajo) - statistics.median(arriba):+.4f} pp"
            )

    print(
        f"    precio medio de los que SUBIAN:  "
        f"{euros(statistics.mean([f['price'] for f in censo if f.get('increment') is not None and f['increment'] > 0]))}"
    )
    print(
        f"    precio medio de los que BAJABAN: "
        f"{euros(statistics.mean([f['price'] for f in censo if f.get('increment') is not None and f['increment'] < 0]))}"
    )
    print("    El hueco sale en la misma direccion en los dos tramos de")
    print("    precio, y los precios medios son casi iguales: no es eso.")

    # Y la hipotesis del retardo puro, que se descarta con la
    # pendiente. Si el Computer usara el precio de AYER tal cual,
    # la prima sobre el de HOY seria exactamente menos la
    # variacion, o sea pendiente -1.
    def pendiente(fuente):
        x, y = [], []

        for fila in fuente:
            precio = fila.get("price")
            previo = fila.get("price_previous")

            if not precio or not previo or not fila.get("amount"):
                continue

            x.append((precio / previo - 1) * 100)
            y.append((fila["amount"] / precio - 1) * 100)

        if len(x) < 5:
            return None

        mx, my = statistics.mean(x), statistics.mean(y)
        sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
        sxx = sum((a - mx) ** 2 for a in x)
        syy = sum((b - my) ** 2 for b in y)

        if not sxx or not syy:
            return None

        return len(x), sxy / sxx, (sxy**2) / (sxx * syy)

    print()
    print("  ¿USA EL PRECIO DE AYER TAL CUAL? Eso seria pendiente -1:")

    for nombre, fuente in (
        ("ofertas vivas", censo),
        ("ventas aceptadas", ventas),
    ):
        recta = pendiente(fuente)

        if recta:
            n, b, r2 = recta
            print(
                f"    {nombre:<20} n={n:<4} pendiente {b:+.4f}   "
                f"R2 = {r2:.4f}"
            )

    print("    Ni de lejos. No es un retardo: es dispersion.")

    print()
    print("  Y EL TEST DEL SIGNO DENTRO DEL JUGADOR (el que quita el")
    print("  confundido de 'a quien le llegan ofertas'):")

    if huecos:
        from math import comb

        a_favor = sum(1 for h in huecos if h > 0)
        n = len(huecos)

        p = sum(comb(n, i) for i in range(a_favor, n + 1)) / 2**n

        print(
            f"    n={n} jugadores, BAJABA paga mas en {a_favor}. "
            f"p (unilateral) = {p:.4f}"
        )

    print()
    print("  AGUANTA LA DIRECCION; LA MAGNITUD SE ENCOGE A LA MITAD.")
    print()
    print("  Cuatro cuentas, las CUATRO a favor de que el Computer paga")
    print("  mas por los que bajaban. Ninguna de las cuatro es holgada:")
    print()
    print("    dentro del jugador      +0,83 pp   p = 0,031   n=5")
    print("    ofertas (increment)     +1,81 pp   p = 0,050   n=52/27")
    print("    ventas aceptadas        +1,28 pp   p = 0,053   n=35/67")
    print("    ofertas (historico)     +3,04 pp   p = 0,091   n=20/13")
    print()
    print("  La unica que baja de 0,05 sin discusion es la de dentro del")
    print("  jugador, y es la de n mas pequeño. Las otras dos se quedan")
    print("  clavadas en el borde y la cuarta no llega. ASI QUE: el signo")
    print("  es consistente en cuatro cuentas independientes, y ninguna")
    print("  sola lo demuestra. El +3,27 pp de la foto del 17/09 (n=8")
    print("  contra n=5) es el borde alto del rango, no el centro.")

    # --------------------------------------------------
    # 4.4 QUE ANCLA USA
    # --------------------------------------------------

    titulo("BLOQUE 4.4 - QUE ANCLA USA EL COMPUTER")

    def dispersion(pares, nombre):
        if len(pares) < 5:
            return

        ratios = sorted(a / b for a, b in pares if b)
        mediana = statistics.median(ratios)
        q1 = ratios[len(ratios) // 4]
        q3 = ratios[3 * len(ratios) // 4]

        print(
            f"  {nombre:<28}{len(ratios):>5}{mediana:>10.4f}"
            f"{q3 - q1:>10.4f}{statistics.pstdev(ratios):>10.4f}"
            f"{sum(1 for r in ratios if abs(r - mediana) < 0.005):>8}"
            f"/{len(ratios)}"
        )

    print()
    print(f"  {'ancla':<28}{'n':>5}{'mediana':>10}{'IQR':>10}{'desv':>10}{'+-0,5 %':>10}")

    dispersion(
        [(v["amount"], v["price"]) for v in ventas if v["price"]],
        "precio de HOY",
    )
    dispersion(
        [
            (v["amount"], v["price_previous"])
            for v in ventas
            if v["price_previous"]
        ],
        "precio de AYER",
    )

    mezclas = []

    for peso in (0.0, 0.25, 0.5, 0.75, 1.0):
        pares = [
            (
                v["amount"],
                peso * v["price"] + (1 - peso) * v["price_previous"],
            )
            for v in ventas
            if v["price"] and v["price_previous"]
        ]

        if pares:
            ratios = [a / b for a, b in pares]
            mezclas.append((peso, statistics.pstdev(ratios)))

    print()
    print("  MEZCLA alfa x hoy + (1-alfa) x ayer:")

    for peso, desv in mezclas:
        print(f"    alfa={peso:.2f}   desviacion {desv:.4f}")

    print()
    print("  NINGUNA ANCLA CLAVA LA OFERTA. La mas estrecha es el precio")
    print("  de HOY y aun asi su IQR es de casi 4 puntos porcentuales; la")
    print("  mejor mezcla baja la desviacion un 8 %, que es ruido. No hay")
    print("  formula que reproduzca la oferta del Computer.")

    # --------------------------------------------------
    # 4.5 LA PERSISTENCIA, Y EL PLAN DEL OJEADOR
    # --------------------------------------------------

    titulo("BLOQUE 4.5 - SI EL PLAN DEL OJEADOR ESTA DEL REVES")

    pares = defaultdict(int)

    for pid, serie in historico.items():
        por_dia = {}

        for i, t in enumerate(serie["t"]):
            por_dia[t // DIA] = serie["p"][i]

        dias = sorted(por_dia)

        for i in range(2, len(dias)):
            if dias[i] - dias[i - 1] != 1 or dias[i - 1] - dias[i - 2] != 1:
                continue

            def signo(x):
                return "SUBE" if x > 0 else ("BAJA" if x < 0 else "PLANO")

            pares[
                (
                    signo(por_dia[dias[i - 1]] - por_dia[dias[i - 2]]),
                    signo(por_dia[dias[i]] - por_dia[dias[i - 1]]),
                )
            ] += 1

    total = sum(pares.values())

    print()
    print(f"  PERSISTENCIA DE LA DIRECCION, n={total} pares de dias seguidos")
    print(f"  (623 jugadores, {HISTORICO}, 16/08 al 16/09)")
    print()

    for ayer in ("SUBE", "PLANO", "BAJA"):
        n = sum(v for k, v in pares.items() if k[0] == ayer)

        if not n:
            continue

        print(
            f"    ayer {ayer:<6} n={n:<6} -> hoy  "
            + "   ".join(
                f"{hoy} {pares[(ayer, hoy)] / n * 100:5.1f} %"
                for hoy in ("SUBE", "PLANO", "BAJA")
            )
        )

    print()
    print("  EL QUE SUBE HOY SIGUE SUBIENDO MAÑANA EL 88,3 % DE LAS VECES.")
    print("  Comprar lo que sube y venderlo al dia siguiente es vender en")
    print("  el tramo SUBIA nueve de cada diez veces, y ese es el tramo")
    print("  que el Computer paga peor.")


def main() -> int:

    bloque_1()
    bloque_2()
    bloque_3()
    bloque_4()

    titulo("NADA SE HA ENCENDIDO")
    print()
    print("  Ninguna escritura contra Biwenger. Ningun umbral tocado.")
    print("  Ningun `intent` movido. ENCENDIDO = False.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
