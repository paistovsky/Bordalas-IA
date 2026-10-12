"""
LA MEJORA DEL ONCE (12/10/2026)

POR QUE EXISTE

    El dueño, 12/10: «2 días que te he preguntado, 2 días que había
    jugadores en el mercado que eran interesantes para mejorar el XI o
    subían de precio y Pepe no ha hecho nada… Se compra, se ejecuta toda
    la deuda, se aguanta y se vende más caro o se mejora el XI. Revisión
    cada ciclo, que para eso está 24/7». Y: «no se trata de ejecutar mis
    órdenes al pie de la letra, se trata de que entiendas cómo funciona
    el juego».

    Hasta hoy la mejora del once la decidía `scripts/el_fichaje_del_dia.py`
    una vez al día, fuera de Pepe, y con la caja en positivo SIN deuda: el
    12/10 tiró a Iván Romero (por Jutglà, +1,7 puntos por jornada) por
    520.000 € y a Gerard Martín (por Diego Rico, +2,3) por 3,8 M. Los dos
    los tuvo que señalar el dueño.

LA REGLA

    Puntos esperados = puntos por partido x titularidad (la vara E16/E23).

    1. En CADA vuelta fuera de la zona de silencio y con la jornada a
       `HORAS_SIN_COMPRAR` o más (el relevo tiene que llegar en un reset y
       el que sale cobrar la oferta del Computer en el siguiente).
    2. Cambios de uno por uno y de la misma posición (el once no pierde
       su forma): entra uno del Computer de hoy (sano, 3+ partidos, 60 %+
       de titularidad) o uno que ya compró la ronda o los chollos (se lo
       queda el once y deja de revenderse: «se aguanta… o se mejora el
       XI»); sale un titular que no sea intocable ni protegido.
    3. Se busca la COMBINACIÓN (hasta `MAXIMO_POR_VUELTA` cambios) que más
       puntos suma, con al menos `GANANCIA_MINIMA`. Vale meter un cambio
       que pierde un poco de puntos si da caja para otro que gana más
       (cambiar caro por barato para fichar mejor).
    4. La caja, CON deuda: saldo - pujas vivas (las de la ronda y los
       chollos se venden solas) + lo que darán las ventas pendientes y el
       inventario de la ronda (al 95 % de su valor) + lo que dan los que
       salen (al 95 %) - lo que cuestan los que entran (precio + 1 %, E9).
       Tiene que quedar >= - `DEUDA_TOLERADA` si la jornada está a
       `HORAS_CON_DEUDA` o más (dos resets para arreglarlo), y >= 0 si no.
       Y las pujas, dentro de `maximumBid` - `RESERVA`.
    4b. Si la caja de la jornada YA no llega (pujas de la orden, compras
       con deuda) y faltan menos de `HORAS_DEFICIT`: se elige la
       combinación que la devuelve al mínimo perdiendo menos puntos, aunque
       pierda (vender caro y fichar barato antes que quedarse en rojo, que
       son 0 puntos). Antes de esa hora se espera: el premio de la jornada
       recién jugada entra en la caja sin hacer nada.
    5. Salida: el que sale se publica cuando su relevo está dentro, y se
       acepta la oferta del Computer desde el 90 % de su valor; a menos de
       `HORAS_SOLVENCIA` de la jornada y en rojo, la que haya. Si la puja
       se pierde, el que iba a salir se queda.

EL CALENDARIO (12/10/2026, `BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`)

    El dueño, 12/10: «antes de la jornada se mira el calendario… si
    Roberto Fernández… juega en casa del Barça, Atleti y Real Madrid,
    sabes que va a puntuar mal, es mejor venderle y poner a otro
    delantero con mejor calendario; generalmente es mejor tener
    jugadores de los equipos de arriba».

    Con el interruptor puesto, los puntos por jornada de CADA lado de
    cada cambio (el titular que sale, el del Computer que entra y el del
    inventario que se adopta) son el xP de las próximas
    `RONDAS_DEL_CALENDARIO` rondas / esas rondas, de
    `src/analysis/el_calendario_de_puntos.py`: tasa ENCOGIDA hacia la
    media de su posición en el tramo de su equipo (k = 3; un 3 de 3
    partidos no es un 9 de verdad) x la MISMA titularidad de siempre x
    sede (1,06 / 0,94; el portero 1,0) x rival (0,90 top-6, 1,04 el
    resto). Laboratorio del 12/10, n = 564 jugador-partido. Un equipo
    que no juega en una ronda cuenta NEUTRO, nunca cero.

    Es un DESEMPATE: el factor por partido va de 0,846 a 1,102, así que
    para un delantero de 5 puntos el calendario mueve ~1 punto por
    jornada. `GANANCIA_MINIMA` sigue en puntos por jornada: un jugador
    mucho mejor nunca se vende por un calendario.

    OJO, EL ENCOGIMIENTO TAMBIÉN MUEVE (k = 3 es juicio, no medida): con
    8 partidos el previo pesa un 27 %. Con el panel del 12/10 14:07,
    Yamal pasa de 10,57 a 8,68 puntos por jornada y Hugo Duro de 1,35 a
    1,78; Roberto Fernández de 6,97 a 5,96 (factor 0,977). Y la J6
    aplazada (Levante-Athletic, 21/10) es una de esas tres rondas: quien
    no la juega cuenta neutro en ella.

    El contexto (ids, duros, tramos, rondas) se monta UNA vez por vuelta
    en `correr`. Sin clasificación o sin calendario, el `esperado` de
    siempre, y el plan lo dice (`plan["calendario"]`). Cada cambio lleva
    en el plan el xP y el factor medio de cada lado.

    Nace APAGADO. Apagado, todo es byte a byte lo de antes.

TRES ARREGLOS QUE VAN SIEMPRE (12/10/2026, el análisis del calendario)

    1. La titularidad de LOS NUESTROS sale de `roster.players` (la
       plantilla entera), no solo de `lineup.players`: `todaLaLiga` no
       la trae nunca, y adoptar a uno de la ronda o los chollos que no
       estaba en el once no funcionaba nunca. Quién puede SALIR sigue
       siendo el once.
    2. EL PARTE DEL RELEVO (la misma regla que `la_orden_del_gestor`):
       para COBRAR al que sale, el que entra tiene que estar 'ok' o
       'warned' (catálogo de la foto o `todaLaLiga`). Publicar siempre
       se puede. En rojo y a menos de `HORAS_ROJO` de la jornada se
       cobra igual: un hueco cuesta un jugador; el rojo, el once entero.
    3. La caja cuenta lo que ESTA vuelta ya hizo (la foto es de antes):
       las pujas que ya puso, las de la orden enteras y las de la ronda
       y los chollos al 7 % (se revenden solas), y lo cobrado al
       Computer entra; el vendido ya no cuenta como venta pendiente ni
       como inventario, ni puede salir otra vez.

QUE NO HACE

    No toca a Yamal (salvo su llave de lesión), ni a los `proteger` de la
    orden del gestor, ni a nadie que la orden ya esté fichando o
    vendiendo. No sube pujas ni compra a rivales.

    No mira el calendario sin su interruptor, ni para cobrar (al cobrar
    solo manda el parte del relevo). No descuenta las pujas que esta
    vuelta retiró (`CANCELAR_PUJA`): la caja sale más prudente, nunca
    más optimista.

    Corre DESPUÉS del panel (necesita su titularidad), como paso propio
    del workflow: `python -m src.actions.la_mejora_del_once`.
    Nace APAGADA: `BORDALAS_LA_MEJORA_DEL_ONCE`. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path


ENV = "BORDALAS_LA_MEJORA_DEL_ONCE"
ENV_CALENDARIO = "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA"     # nace APAGADO
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "la_mejora.json"
STATUS = RAIZ / "dashboard" / "data" / "status.json"
V10 = RAIZ / "data" / "trading" / "v10_full_autonomous_status.json"

GANANCIA_MINIMA = 0.5            # puntos por jornada, la combinación entera
PEOR_FINANCIACION = -1.5         # lo más que se pierde en un cambio que da caja
MAXIMO_POR_VUELTA = 3
TITULARIDAD_MINIMA = 60
PARTIDOS_MINIMOS = 3
HORAS_SIN_COMPRAR = 40
HORAS_CON_DEUDA = 64
HORAS_DEFICIT = 88               # en rojo, desde aquí se cambia caro por barato
HORAS_SOLVENCIA = 20
DEUDA_TOLERADA = 1_000_000
RESERVA = 1_000_000
SUBE = 1.01                      # la puja (E9)
VENTA = 0.95                     # lo que se espera de la oferta del Computer
SUELO = 0.90                     # lo mínimo que se acepta por el que sale
CANDIDATOS = 25                  # de cada lista, para la combinación

# El horizonte del calendario: tres rondas (el de `el_calendario_de_puntos`,
# HORIZONTE = 3). Se divide entre las rondas que cuenta: puntos por jornada.
RONDAS_DEL_CALENDARIO = 3

# EL PARTE DEL RELEVO: los mismos que `la_orden_del_gestor.SANOS` y
# `HORAS_ROJO` (12/10/2026). 'warned' (apercibido) juega.
SANOS = frozenset({"ok", "warned"})
HORAS_ROJO = 24

# Lo que cuenta en la caja una puja que se revende sola (ronda, chollos).
SE_REVENDE = 0.07


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def el_calendario_activo() -> bool:
    """`BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`, leído como `activa`. Nace
    APAGADO. Nunca lanza."""
    try:
        return str(os.environ.get(ENV_CALENDARIO, "")).strip().lower() in {
            "1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError):
        return defecto


def esperado(tasa, prob):
    """Puntos por jornada: puntos por partido x titularidad."""
    try:
        if tasa is None or prob is None:
            return None
        return float(tasa) * float(prob) / 100.0
    except (TypeError, ValueError):
        return None


def la_puja(precio: int) -> int:
    return int(round(precio * SUBE, -3))


# ============================================================
# EL CALENDARIO (12/10/2026): los puntos por jornada, con el rival
# ============================================================

def la_ficha(ficha_de_la_liga, pos=None, respaldo=None) -> dict:
    """
    Lo que `el_calendario_de_puntos.xp_jugador` necesita de un jugador:
    equipo (`todaLaLiga.team_id`), posición, puntos y partidos jugados.
    Puntos y partidos, los de `todaLaLiga`; si no los trae, los de
    `respaldo` (la ficha del escaparate). La posición, la del cambio
    (`pos`), que es la que casa entra con sale. Pura, nunca lanza.
    """
    try:
        lc = ficha_de_la_liga if isinstance(ficha_de_la_liga, dict) else {}
        ficha = {"team_id": lc.get("team_id"),
                 "position": pos if pos is not None else lc.get("position"),
                 "points": lc.get("points"), "played": lc.get("played")}
        if (ficha["points"] is None or ficha["played"] is None) and isinstance(respaldo, dict):
            ficha["points"], ficha["played"] = respaldo.get("points"), respaldo.get("played")
        return ficha
    except Exception:                               # noqa: BLE001
        return {}


def xp_por_jornada(ctx, ficha, prob):
    """
    Los puntos por jornada CON el calendario: `{"xp", "factor"}`.

        xp      el xP de las próximas `RONDAS_DEL_CALENDARIO` rondas
                (`xp_jugador`: tasa encogida hacia su tramo x `prob` x
                sede x rival) entre las rondas que cuenta (menos al final
                de la liga). Sin rondas por delante, `xp_horizonte` da el
                neutro: la tasa encogida x `prob`.
        factor  el factor medio por ronda (`factor_medio`): 1,0 neutro,
                0,846 tres veces fuera contra un duro, 1,102 en casa
                contra el resto.

    None si no se puede: contexto no disponible, sin titularidad o sin
    puntos y partidos (entonces manda el `esperado` de siempre). Pura,
    nunca lanza.
    """
    try:
        if not isinstance(ctx, dict) or not ctx.get("available"):
            return None
        if not isinstance(ficha, dict) or prob is None:
            return None
        if ficha.get("points") is None or _int(ficha.get("played")) is None:
            return None
        from src.analysis.el_calendario_de_puntos import factor_medio, xp_jugador

        rondas = [r for r in (ctx.get("rondas") or []) if isinstance(r, dict)]
        cuantas = len(rondas[:RONDAS_DEL_CALENDARIO]) or RONDAS_DEL_CALENDARIO
        xp = xp_jugador(ctx, ficha, prob, n=RONDAS_DEL_CALENDARIO)
        if xp is None:
            return None
        factor = factor_medio(ficha.get("team_id"), ficha.get("position"), rondas,
                              ctx.get("ids") or {}, ctx.get("duros") or set(),
                              n=RONDAS_DEL_CALENDARIO)
        return {"xp": float(xp) / cuantas, "factor": float(factor)}
    except Exception:                               # noqa: BLE001
        return None


def el_plan_del_calendario(ctx) -> dict:
    """Lo que el plan cuenta del calendario: si se usó, por qué, qué
    rondas y quién es duro. Pura, nunca lanza."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        usado = bool(ctx.get("available"))
        salida = {"usado": usado,
                  "motivo": ctx.get("reason") or ("" if usado else "sin contexto del calendario")}
        if not usado:
            salida["motivo"] = f"sin calendario, el esperado de siempre: {salida['motivo']}"
        else:
            salida["rondas"] = [r.get("label") for r in (ctx.get("rondas") or [])
                                if isinstance(r, dict)][:RONDAS_DEL_CALENDARIO]
            salida["duros"] = sorted(d for d in (ctx.get("duros") or []) if d is not None)
        return salida
    except Exception as error:                      # noqa: BLE001
        return {"usado": False, "motivo": f"{type(error).__name__}: {error}"}


def la_mejor_combinacion(cambios: list, caja: int, minimo_de_caja: int,
                         disponible: int, deficit: bool = False) -> list:
    """
    De los cambios posibles (cada uno con `entra`, `sale`, `puntos`,
    `caja`, `puja`), la combinación sin repetir jugador que más puntos
    suma con al menos `GANANCIA_MINIMA`, sin bajar la caja de
    `minimo_de_caja` ni pasar de `disponible` en pujas. A igualdad, la
    que deja más caja. Pura.

    Con `deficit` (la caja de la jornada ya no llega): vale una
    combinación que pierde puntos si es la que menos pierde de las que
    devuelven la caja a `minimo_de_caja` («fichar y luego ver con quién
    nos quedamos y vender para quedarnos en positivo», el dueño, 12/10).
    """

    mejoras = sorted((c for c in cambios if c["puntos"] >= GANANCIA_MINIMA),
                     key=lambda c: -c["puntos"])[:CANDIDATOS]
    financian = sorted((c for c in cambios
                        if PEOR_FINANCIACION <= c["puntos"] < GANANCIA_MINIMA and c["caja"] > 0),
                       key=lambda c: -c["caja"])[:CANDIDATOS]
    todos = mejoras + financian

    mejor, clave = [], None
    for n in range(1, MAXIMO_POR_VUELTA + 1):
        for combo in combinations(todos, n):
            if not deficit and not any(c["puntos"] >= GANANCIA_MINIMA for c in combo):
                continue
            entran = {c["entra"] for c in combo}
            salen = {c["sale"] for c in combo}
            if len(entran) < n or len(salen) < n:
                continue
            puntos = sum(c["puntos"] for c in combo)
            if not deficit and puntos < GANANCIA_MINIMA:
                continue
            if caja + sum(c["caja"] for c in combo) < minimo_de_caja:
                continue
            if sum(c["puja"] for c in combo) > disponible:
                continue
            k = (round(puntos, 6), caja + sum(c["caja"] for c in combo))
            if clave is None or k > clave:
                mejor, clave = list(combo), k
    return mejor


def decidir(
    *, once, liga, escaparate, foto, libro, inventario=frozenset(),
    pendientes=frozenset(), intocables=frozenset(), protegidos=frozenset(),
    ya_pujados=frozenset(), caja, horas_jornada, puede_escribir=True,
    en_curso=False, calendario_de_puntos=None, probabilidades=None,
    estados=None,
) -> dict:
    """
    Qué hace la mejora del once en esta vuelta. Pura.

        once        [{id, name, position, starter_probability, price}]
        liga        {id: {tasa, status, price, de_quien, position}}
        escaparate  [{id, name, position, price, points, played,
                      starter_probability}] (Computer, hoy)
        foto        la de `leer_la_foto` (plantilla, nuestras_pujas,
                    ofertas_del_computer, en_venta, maximo_de_puja, saldo)
        libro       {"entra": {"sale", "suelo", ...}} de los cambios vivos
        inventario  lo que tienen la ronda y los chollos en la plantilla
        caja        la caja de la jornada sin estos cambios (ver `la_caja`)
        en_curso    hay jornada jugándose: no se vende a nadie (el once de
                    la jornada es el de su inicio, pero el que se vende
                    deja de puntuar para nosotros)

    Lo del 12/10/2026 (`correr` lo pasa siempre; sin pasarlo, lo de antes):

        calendario_de_puntos  el `contexto` de `el_calendario_de_puntos`
                    (solo con `BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`): los
                    puntos de cada lado son `xp_por_jornada`. None: el
                    `esperado` de siempre, byte a byte.
        probabilidades  {id: titularidad} de NUESTRA plantilla entera
                    (`roster.players`): manda sobre la del once y es la
                    única que tienen los del inventario fuera del once.
        estados     {id: status} (catálogo de la foto, `todaLaLiga`): EL
                    PARTE DEL RELEVO. Para cobrar al que sale, el que
                    entra 'ok' o 'warned'; si no, se publica pero no se
                    cobra, salvo en rojo a menos de `HORAS_ROJO`.
    """

    acciones, soltar, adoptar, frenadas = [], [], [], []
    plantilla = foto.get("plantilla") or set()
    ofertas = foto.get("ofertas_del_computer") or {}
    en_venta = foto.get("en_venta") or set()
    saldo = _int(foto.get("saldo"), 0) or 0

    # 5. SALIDA de los cambios vivos.
    saliendo = set()
    for k, c in (libro or {}).items():
        entra, sale = _int(k), _int(c.get("sale"))
        if sale not in plantilla:
            soltar.append(k)                         # ya vendido
            continue
        if entra not in plantilla:
            if entra not in (foto.get("nuestras_pujas") or {}):
                soltar.append(k)                     # puja perdida: se queda
            else:
                saliendo.add(sale)
            continue
        saliendo.add(sale)
        if en_curso:
            continue
        suelo = _int(c.get("suelo"), 0) or 0
        if horas_jornada is not None and horas_jornada < HORAS_SOLVENCIA and saldo < 0:
            suelo = 0
        oferta = ofertas.get(sale)
        cobra = bool(oferta and (_int(oferta.get("amount"), 0) or 0) >= suelo)
        # EL PARTE DEL RELEVO (12/10/2026, la regla de `la_orden_del_gestor`):
        # la plantilla es de 11 justos; si el que entra está lesionado o en
        # duda, cobrar al que sale deja un hueco en el once. Solo frena el
        # COBRO (publicar no saca a nadie y hace nacer la oferta); en rojo y
        # a menos de `HORAS_ROJO`, manda la caja.
        if cobra and estados is not None:
            parte = str(estados.get(entra) or "").strip().lower()
            en_rojo_y_cerca = (saldo < 0 and horas_jornada is not None
                               and horas_jornada < HORAS_ROJO)
            if parte not in SANOS and not en_rojo_y_cerca:
                cobra = False
                frenadas.append({
                    "guardia": "EL_PARTE_DEL_RELEVO", "player_id": sale,
                    "relevo": entra, "estado_del_relevo": parte or None,
                    "motivo": (f"el relevo ({entra}) no esta sano "
                               f"({parte or 'sin estado'}): no se cobra"),
                })
        if cobra:
            acciones.append({
                "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": sale,
                "offer_id": _int(oferta.get("offer_id")),
                "importe": _int(oferta.get("amount")), "suelo": suelo,
                "relevo": entra, "mejora": True,
            })
        elif sale not in en_venta and _int((liga.get(sale) or {}).get("price")):
            acciones.append({
                "accion": "PONER_A_LA_VENTA", "player_id": sale,
                "precio": _int((liga.get(sale) or {}).get("price")),
                "relevo": entra, "mejora": True,
            })

    plan = {"caja": caja, "cambios": []}
    if calendario_de_puntos is not None:
        plan["calendario"] = el_plan_del_calendario(calendario_de_puntos)
    if frenadas:
        plan["frenadas"] = frenadas
    if not puede_escribir or horas_jornada is None or horas_jornada < HORAS_SIN_COMPRAR:
        return {"acciones": acciones, "soltar": soltar, "adoptar": adoptar, "plan": plan}

    # EL CALENDARIO: con contexto, los puntos de cada lado son el xP por
    # jornada; sin él (o sin datos de ese jugador), el `esperado`.
    ctx = calendario_de_puntos if (isinstance(calendario_de_puntos, dict)
                                   and calendario_de_puntos.get("available")) else None

    def _con_calendario(fila, ficha, prob):
        if ctx is None:
            return fila
        r = xp_por_jornada(ctx, ficha, prob)
        fila["plano"] = fila["esperado"]
        fila["xp"] = None if r is None else round(r["xp"], 2)
        fila["factor"] = None if r is None else round(r["factor"], 3)
        if r is not None:
            fila["esperado"] = r["xp"]
        return fila

    def _prob_nuestra(pid, de_respaldo):
        prob = (probabilidades or {}).get(pid)
        return de_respaldo if prob is None else prob

    # 2. Quién puede salir: titulares, ni intocables ni protegidos, ni
    # los que ya salen o la orden vende.
    vivos = {_int(k) for k in (libro or {})}
    nuestros = []
    for p in once:
        pid = _int(p.get("id"))
        if (str(p.get("name") or "").strip().lower() in intocables or pid in protegidos
                or pid in saliendo or pid in pendientes or pid in vivos or pid in inventario):
            continue
        prob = _prob_nuestra(pid, p.get("starter_probability"))
        e = esperado((liga.get(pid) or {}).get("tasa"), prob)
        if e is None:
            continue
        valor = _int(p.get("price")) or _int((liga.get(pid) or {}).get("price"), 0) or 0
        nuestros.append(_con_calendario(
            {"id": pid, "nombre": p.get("name"), "pos": p.get("position"),
             "esperado": e, "valor": valor},
            la_ficha(liga.get(pid), p.get("position")), prob))

    # Quién puede entrar: el Computer de hoy, y lo que ya tienen la ronda
    # y los chollos (sin pujar: ya es nuestro).
    entran = []
    for c in escaparate or []:
        pid = _int(c.get("id"))
        lc = liga.get(pid) or {}
        if (pid in plantilla or pid in pendientes or pid in ya_pujados
                or pid in (foto.get("nuestras_pujas") or {})
                or lc.get("de_quien") not in (None, "computer")
                or str(lc.get("status") or "ok").lower() != "ok"
                or (_int(c.get("played"), 0) or 0) < PARTIDOS_MINIMOS):
            continue
        prob = c.get("starter_probability")
        if prob is None or prob < TITULARIDAD_MINIMA:
            continue
        tasa = lc.get("tasa") or ((c.get("points") or 0) / c["played"])
        e = esperado(tasa, prob)
        # Lo que PIDE el Computer (E12: el precio del día en que salió).
        precio = _int((foto.get("mercado") or {}).get(pid)) or _int(c.get("price"), 0) or 0
        if foto.get("mercado") and pid not in foto["mercado"]:
            continue
        if e is None or not precio:
            continue
        entran.append(_con_calendario(
            {"id": pid, "nombre": c.get("name"), "pos": c.get("position"),
             "esperado": e, "puja": la_puja(precio), "coste": la_puja(precio),
             "ya_es_nuestro": False},
            la_ficha(lc, c.get("position"), respaldo=c), prob))
    prob_once = {_int(p.get("id")): p.get("starter_probability") for p in once}
    for pid in inventario:
        lc = liga.get(pid) or {}
        if pid not in plantilla or str(lc.get("status") or "ok").lower() != "ok":
            continue
        # La titularidad de la plantilla entera (`roster.players`): el del
        # inventario casi nunca está en el once, y `todaLaLiga` no la trae.
        prob = _prob_nuestra(pid, prob_once.get(pid) or lc.get("starter_probability"))
        e = esperado(lc.get("tasa"), prob)
        valor = _int(lc.get("price"), 0) or 0
        if e is None or not valor:
            continue
        # Quedárselo cuesta lo que ya no da su reventa.
        entran.append(_con_calendario(
            {"id": pid, "nombre": lc.get("name"), "pos": lc.get("position"),
             "esperado": e, "puja": 0, "coste": int(valor * VENTA),
             "ya_es_nuestro": True},
            la_ficha(lc, lc.get("position")), prob))

    cambios = []
    for e in entran:
        for o in nuestros:
            if o["pos"] != e["pos"]:
                continue
            cambio = {
                "entra": e["id"], "entra_nombre": e["nombre"], "sale": o["id"],
                "sale_nombre": o["nombre"], "puntos": round(e["esperado"] - o["esperado"], 2),
                "caja": int(o["valor"] * VENTA) - e["coste"], "puja": e["puja"],
                "suelo": int(o["valor"] * SUELO), "ya_es_nuestro": e["ya_es_nuestro"],
            }
            if ctx is not None:
                # Por qué: el xP de cada lado, su factor medio y lo que
                # habría dicho el `esperado` de siempre.
                cambio.update({
                    "xp_entra": e["xp"], "xp_sale": o["xp"],
                    "factor_entra": e["factor"], "factor_sale": o["factor"],
                    "sin_calendario": round(e["plano"] - o["plano"], 2),
                })
            cambios.append(cambio)

    minimo = -DEUDA_TOLERADA if horas_jornada >= HORAS_CON_DEUDA else 0
    disponible = (_int(foto.get("maximo_de_puja"), 0) or 0) - RESERVA
    # En rojo, cambiar caro por barato solo a partir de `HORAS_DEFICIT`:
    # antes puede entrar el premio de la jornada que acaba de jugarse.
    deficit = caja < minimo and horas_jornada < HORAS_DEFICIT
    elegidos = la_mejor_combinacion(cambios, caja, minimo, disponible, deficit=deficit)
    plan = {"caja": caja, "minimo": minimo, "disponible": disponible, "deficit": deficit,
            "cambios": elegidos,
            "caja_despues": caja + sum(c["caja"] for c in elegidos)}
    if calendario_de_puntos is not None:
        plan["calendario"] = el_plan_del_calendario(calendario_de_puntos)
    if frenadas:
        plan["frenadas"] = frenadas

    for c in elegidos:
        if c["ya_es_nuestro"]:
            adoptar.append(c)
        else:
            acciones.append({
                "accion": "PUJAR", "player_id": c["entra"], "importe": c["puja"],
                "sustituye": None, "sale": c["sale"], "suelo": c["suelo"],
                "puntos": c["puntos"], "mejora": True,
            })

    return {"acciones": acciones, "soltar": soltar, "adoptar": adoptar, "plan": plan}


def jornada_en_curso(ahora: datetime, ruta=None) -> bool:
    """
    Entre el primer partido de una ronda de Biwenger y 3 h después del
    último. Las rondas las da `la_proxima_jornada`: los partidos fuera de
    la ventana de su jornada (adelantados y aplazados) son rondas aparte.
    Antes se cortaba a 5 días del PRIMER partido, y con el adelantado de
    la J6 (03/09) el grueso del 15-17/09 no contaba como jornada en curso;
    el aplazado Levante-Athletic del 21/10 cuenta como la suya.
    """
    try:
        from src.actions.los_chollos import CALENDARIO
        from src.analysis.la_proxima_jornada import jornada_en_curso as _en_curso

        return bool(_en_curso(ahora, CALENDARIO if ruta is None else ruta))
    except Exception:                               # noqa: BLE001
        return True                                 # sin saberlo, no se vende


def la_caja(foto: dict, *, se_venden_solos=frozenset(), inventario_valor=0,
            ventas_pendientes=0, esta_vuelta=None) -> int:
    """
    La caja con la que se llega a la jornada si nada más cambia: saldo -
    pujas vivas (salvo las que se revenden solas: ronda y chollos, que
    cuentan a -7 %) + lo que darán el inventario de la ronda y las ventas
    pendientes (ya al 95 %).

    Con `esta_vuelta` (la de `lo_de_esta_vuelta`, 12/10/2026): la foto es
    de ANTES de la vuelta, así que las pujas que esta vuelta ya puso se
    suman a las vivas (la que sustituye a otra, en su lugar), las de la
    ronda y los chollos también al 7 %, y lo cobrado al Computer entra.
    Sin pasarlo, lo de antes.
    """

    saldo = _int(foto.get("saldo"), 0) or 0
    vivas = dict(foto.get("nuestras_pujas") or {})
    solos = set(se_venden_solos or ())
    cobrado = 0
    if esta_vuelta:
        for pid, importe in (esta_vuelta.get("pujas") or {}).items():
            vivas[pid] = {"amount": importe}
        solos |= set(esta_vuelta.get("solas") or ())
        cobrado = sum(_int(v, 0) or 0 for v in (esta_vuelta.get("cobros") or {}).values())
    pujas = 0
    for pid, p in vivas.items():
        importe = _int(p.get("amount"), 0) or 0
        pujas += int(importe * SE_REVENDE) if pid in solos else importe
    return saldo - pujas + int(inventario_valor) + int(ventas_pendientes) + cobrado


def lo_de_esta_vuelta(v10) -> dict:
    """
    Lo que ESTA vuelta ya hizo antes que la mejora (la foto es de antes),
    de los bloques `orden_del_gestor`, `chollos` y `ronda` de
    `v10_full_autonomous_status.json`, solo lo que salió bien (`exito`):

        ya_pujados  {id} pujados (no se vuelve a pujar por ellos)
        gastado     lo pujado, para `maximumBid` (como antes)
        pujas       {id: importe} de cada puja puesta (enviada con éxito)
        solas       {id} de las de la ronda y los chollos (se revenden
                    solas: cuentan al 7 % en la caja)
        cobros      {id: importe} de las ofertas del Computer aceptadas

    El 12/10 la orden pujó 3.777.000 por Iván Romero y 4.989.000 por
    Gerard Martín y la ronda 1.101.000 por el 1462 en la misma vuelta: la
    caja de la mejora solo veía `maximumBid` bajar. Pura, nunca lanza.
    """
    salida = {"ya_pujados": set(), "gastado": 0, "pujas": {}, "solas": set(), "cobros": {}}
    try:
        for bloque in ("orden_del_gestor", "chollos", "ronda"):
            for h in ((v10 or {}).get(bloque) or {}).get("hechas") or []:
                if not isinstance(h, dict) or not h.get("exito"):
                    continue
                pid = _int(h.get("player_id"))
                importe = _int(h.get("importe"), 0) or 0
                if h.get("accion") == "PUJAR":
                    salida["ya_pujados"].add(pid)
                    salida["gastado"] += importe
                    if pid is not None:
                        salida["pujas"][pid] = importe
                        if bloque != "orden_del_gestor":
                            salida["solas"].add(pid)
                elif h.get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER" and pid is not None:
                    salida["cobros"][pid] = salida["cobros"].get(pid, 0) + importe
    except Exception:                               # noqa: BLE001
        pass
    return salida


def la_caja_de_la_jornada(foto: dict, *, liga, orden, libro, solos, inventario,
                          esta_vuelta=None) -> int:
    """
    La caja de la jornada como la monta `correr`: `la_caja` con el
    inventario de la ronda y los chollos y las ventas pendientes (las de
    `vender_si_ficha` de la orden por su suelo / 0,90 y los que salen por
    la mejora, al 95 %), menos los `fichar` de la orden aún sin puja.

    Con `esta_vuelta`: lo vendido en esta vuelta YA es caja (entra por
    `cobros`) y no cuenta otra vez ni como venta pendiente ni como
    inventario; y un `fichar` que esta vuelta ya pujó cuenta por su puja,
    no dos veces. Sin pasarlo, lo de antes. Pura.
    """
    esta = esta_vuelta or {}
    vendidos = set(esta.get("cobros") or {})
    pujadas = set(foto.get("nuestras_pujas") or {}) | set(esta.get("pujas") or {})
    plantilla = foto.get("plantilla") or set()
    orden = orden or {}
    venta = [j for j in (orden.get("vender_si_ficha") or {}).get("jugadores") or []
             if _int(j.get("player_id")) not in vendidos]
    saliendo_valor = sum(
        _int((liga.get(_int(c.get("sale"))) or {}).get("price"), 0) or 0
        for c in (libro or {}).values() if _int(c.get("sale")) not in vendidos
    )
    return la_caja(
        foto, se_venden_solos=solos,
        inventario_valor=int(sum(_int((liga.get(p) or {}).get("price"), 0) or 0
                                 for p in inventario if p not in vendidos) * VENTA),
        ventas_pendientes=int((sum(int((_int(j.get("suelo"), 0) or 0) / SUELO) for j in venta)
                               + saliendo_valor) * VENTA)
        - sum(_int(f.get("puja"), 0) or 0 for f in orden.get("fichar") or []
              if _int(f.get("player_id")) not in pujadas
              and _int(f.get("player_id")) not in plantilla),
        esta_vuelta=esta_vuelta,
    )


def las_probabilidades(status) -> dict:
    """
    {id: titularidad} de NUESTRA plantilla entera: `roster.players` (la
    plantilla, con `starter_probability`) y, si falta alguno, el de
    `lineup.players`. `todaLaLiga` no la trae nunca: sin esto, el de la
    ronda o los chollos que no está en el once no se podía adoptar. Pura,
    nunca lanza.
    """
    salida = {}
    try:
        for bloque in ("roster", "lineup"):
            for p in ((status or {}).get(bloque) or {}).get("players") or []:
                pid = _int((p or {}).get("id"))
                prob = (p or {}).get("starter_probability")
                if pid is not None and prob is not None and pid not in salida:
                    salida[pid] = prob
    except Exception:                               # noqa: BLE001
        pass
    return salida


def los_estados(snapshot, liga) -> dict:
    """
    {id: status} para EL PARTE DEL RELEVO: el del catálogo de la foto de
    la vuelta (`la_orden_del_gestor.leer_los_estados`) y, si no lo trae,
    el de `todaLaLiga`. Pura, nunca lanza.
    """
    estados = {}
    try:
        for pid, ficha in (liga or {}).items():
            if isinstance(ficha, dict) and ficha.get("status") is not None:
                estados[pid] = ficha.get("status")
        from src.actions.la_orden_del_gestor import leer_los_estados

        for pid, estado in leer_los_estados(snapshot).items():
            if estado is not None:
                estados[pid] = estado
    except Exception:                               # noqa: BLE001
        pass
    return estados


def el_contexto(status, calendario, ahora) -> dict:
    """
    El `contexto` de `el_calendario_de_puntos`, UNA vez por vuelta, con
    `RONDAS_DEL_CALENDARIO` rondas. `calendario`: un dict ya leído, o la
    ruta (por defecto la de los chollos). Nunca lanza: si algo falla, un
    contexto no disponible con el motivo, y la mejora usa el `esperado`.
    """
    try:
        from src.analysis.el_calendario_de_puntos import contexto

        if not isinstance(calendario, dict):
            from src.actions.los_chollos import CALENDARIO

            calendario = _leer(CALENDARIO if calendario is None else calendario, {})
        return contexto(status, calendario, ahora, n=RONDAS_DEL_CALENDARIO)
    except Exception as error:                      # noqa: BLE001
        return {"available": False, "reason": f"{type(error).__name__}: {error}"}


# ============================================================
# EL PASO DEL WORKFLOW
# ============================================================

def _leer(ruta, defecto):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return defecto


def _la_ultima_foto():
    fotos = sorted((RAIZ / "data").glob("snapshot_*.json"))
    return _leer(fotos[-1], {}) if fotos else {}


def correr(status=None, snapshot=None, v10=None, escritor_factory=None,
           ahora: datetime | None = None, libro_ruta=None, calendario=None,
           de_fuera=None) -> dict:
    """
    La mejora del once, en esta vuelta. Nunca lanza.

        calendario  el de LaLiga (dict o ruta; por defecto el de los
                    chollos). Solo se lee con
                    `BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`.
        de_fuera    para las guardias: lo que si no se lee de producción
                    (`orden`, `vetados`, `protegidos`, las rutas
                    `libro_ronda` y `libro_chollos`, `horas_jornada`,
                    `puede_escribir`, `en_curso`). Lo que no trae, de
                    producción, como siempre.
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "adoptados": [], "plan": None}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _intocables, _pid, ejecutar, leer_la_foto, leer_la_orden, protegidos,
            vetados,
        )
        from src.actions.los_chollos import (
            LIBRO as LIBRO_CHOLLOS, _puede_escribir, horas_a_la_jornada,
        )
        from src.actions.la_ronda_de_la_manana import LIBRO as LIBRO_RONDA

        fuera = de_fuera if isinstance(de_fuera, dict) else {}
        ahora = ahora or datetime.now(timezone.utc)
        status = status if status is not None else _leer(STATUS, {})
        snapshot = snapshot if snapshot is not None else _la_ultima_foto()
        v10 = v10 if v10 is not None else _leer(V10, {})

        yo = _pid((snapshot.get("league") or {}).get("user"))
        foto = leer_la_foto(snapshot, yo)

        # Lo que esta misma vuelta ya hizo (la foto es de antes): lo
        # pujado baja `maximumBid` y no se vuelve a pujar; lo pujado y lo
        # cobrado entran en la caja; lo vendido ya no sale otra vez.
        esta_vuelta = lo_de_esta_vuelta(v10)
        ya_pujados = esta_vuelta["ya_pujados"]
        vendidos = set(esta_vuelta["cobros"])
        foto["maximo_de_puja"] = ((_int(foto.get("maximo_de_puja"), 0) or 0)
                                  - esta_vuelta["gastado"])

        liga = {}
        for p in (status.get("todaLaLiga") or {}).get("players") or []:
            if _int(p.get("id")) is not None:
                liga[_int(p["id"])] = p
        once = (status.get("lineup") or {}).get("players") or []
        escaparate = (status.get("libro_del_escaparate") or {}).get("players") or []

        orden = (fuera["orden"] if "orden" in fuera else leer_la_orden()) or {}
        pendientes = {_int(f.get("player_id")) for f in orden.get("fichar") or []}
        venta = (orden.get("vender_si_ficha") or {}).get("jugadores") or []
        pendientes |= {_int(j.get("player_id")) for j in venta}
        # los `no_pujar` del gestor
        pendientes |= set(fuera["vetados"] if "vetados" in fuera else vetados())
        pendientes |= vendidos

        ruta_ronda = fuera.get("libro_ronda") or LIBRO_RONDA
        ruta_chollos = fuera.get("libro_chollos") or LIBRO_CHOLLOS
        libro_ronda = _leer(ruta_ronda, {})
        libro_chollos = _leer(ruta_chollos, {})
        solos = {_int(k) for k in list(libro_ronda) + list(libro_chollos)}
        inventario = {p for p in solos if p in foto["plantilla"] and p not in vendidos}

        libro = _leer(libro_ruta or LIBRO, {})
        caja = la_caja_de_la_jornada(
            foto, liga=liga, orden=orden, libro=libro, solos=solos,
            inventario=inventario, esta_vuelta=esta_vuelta,
        )
        # El saldo de la foto, con lo ya cobrado en esta vuelta (para el
        # suelo en rojo y el parte del relevo).
        if esta_vuelta["cobros"]:
            foto["saldo"] = ((_int(foto.get("saldo"), 0) or 0)
                             + sum(esta_vuelta["cobros"].values()))

        # EL CALENDARIO, una vez por vuelta y solo con su interruptor.
        ctx = el_contexto(status, calendario, ahora) if el_calendario_activo() else None

        d = decidir(
            once=once, liga=liga, escaparate=escaparate, foto=foto, libro=libro,
            inventario=inventario, pendientes=pendientes,
            intocables=_intocables(orden),
            protegidos=set(fuera["protegidos"] if "protegidos" in fuera else protegidos()),
            ya_pujados=ya_pujados, caja=caja,
            horas_jornada=(fuera["horas_jornada"] if "horas_jornada" in fuera
                           else horas_a_la_jornada(ahora)),
            puede_escribir=(fuera["puede_escribir"] if "puede_escribir" in fuera
                            else _puede_escribir(ahora)),
            en_curso=(fuera["en_curso"] if "en_curso" in fuera
                      else jornada_en_curso(ahora)),
            calendario_de_puntos=ctx,
            probabilidades=las_probabilidades(status),
            estados=los_estados(snapshot, liga),
        )
        salida["acciones"], salida["plan"] = d["acciones"], d["plan"]

        for k in d["soltar"]:
            libro.pop(k, None)
        for c in d["adoptar"]:
            libro[str(c["entra"])] = {"sale": c["sale"], "suelo": c["suelo"],
                                      "puntos": c["puntos"], "adoptado": True}
            libro_ronda.pop(str(c["entra"]), None)
            libro_chollos.pop(str(c["entra"]), None)
            salida["adoptados"].append(c)
        if d["adoptar"]:
            for ruta, datos in ((ruta_ronda, libro_ronda), (ruta_chollos, libro_chollos)):
                try:
                    Path(ruta).write_text(json.dumps(datos, indent=2) + "\n")
                except Exception:                   # noqa: BLE001
                    pass

        if d["acciones"]:
            if escritor_factory is None:
                from src.biwenger.write_client import BiwengerWriteClient

                escritor_factory = BiwengerWriteClient
            hechas = ejecutar(d["acciones"], escritor_factory())
            salida["hechas"] = hechas
            for h in hechas:
                if h.get("accion") == "PUJAR" and h.get("exito"):
                    libro[str(h["player_id"])] = {
                        "sale": h.get("sale"), "suelo": h.get("suelo"),
                        "puja": h.get("importe"), "puntos": h.get("puntos"),
                    }

        try:
            ruta = Path(libro_ruta or LIBRO)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(libro, indent=2) + "\n")
        except Exception:                           # noqa: BLE001
            pass

        salida["motivo"] = "EJECUTADA" if (d["acciones"] or d["adoptar"]) else "NADA_QUE_HACER"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida


def main() -> int:
    r = correr()
    plan = r.get("plan") or {}
    print("=" * 100)
    print("LA MEJORA DEL ONCE")
    print("=" * 100)
    print(f"  {r.get('motivo')}  caja de la jornada {plan.get('caja')}  "
          f"minimo {plan.get('minimo')}  puja disponible {plan.get('disponible')}")
    calendario = plan.get("calendario")
    if calendario:
        print(f"  calendario: {'SI' if calendario.get('usado') else 'NO'}  "
              f"{calendario.get('rondas') or ''} {calendario.get('motivo') or ''}")
    for c in plan.get("cambios") or []:
        print(f"  {c['entra_nombre']} por {c['sale_nombre']}: {c['puntos']:+} pts por jornada, "
              f"caja {c['caja']:+,}{' (ya es nuestro)' if c['ya_es_nuestro'] else ''}")
        if "xp_entra" in c:
            print(f"      xP {c['xp_entra']} (x{c['factor_entra']}) por {c['xp_sale']} "
                  f"(x{c['factor_sale']}); sin calendario {c['sin_calendario']:+}")
    for f in plan.get("frenadas") or []:
        print(f"  frenada {f.get('guardia')} {f.get('player_id')}: {f.get('motivo')}")
    for a in r.get("acciones") or []:
        print(f"  -> {a.get('accion')} {a.get('player_id')} {a.get('importe') or a.get('precio')}")
    for h in r.get("hechas") or []:
        print(f"  hecha {h.get('accion')} {h.get('player_id')} exito={h.get('exito')} "
              f"http={h.get('http_status')} {h.get('error') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
