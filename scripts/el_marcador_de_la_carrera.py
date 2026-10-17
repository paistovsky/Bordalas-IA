"""
EL MARCADOR DE LA CARRERA (17/10/2026)

POR QUE EXISTE

    El dueño, 16/10 noche: «Pollo nos sigue ganando pujas… sigue
    distanciándose en patrimonio». Esa noche la brecha se midió con
    scripts sueltos fuera del repositorio, que cuadraban al euro (caja de
    Pepe 486.683 y patrimonio de Pollo17 103.324.651 al cierre del 16/10),
    pero que nadie podía volver a correr. Este script trae esa medida al
    repo, en un solo sitio y solo con lo que ya está en `data/`:

      1. EL PATRIMONIO de cada manager en cada día de mercado: caja más
         plantilla a precio de ese día.
      2. LA SEMANA CONTRA NO HACER NADA. De lunes a lunes, la semana en
         curso y los últimos 7 días: cuánto cambió el patrimonio de Pepe,
         Pollo17 y Luismi_Haz frente a quedarse quietos con la plantilla y
         la caja del principio de la ventana. Separa lo que puso el
         mercado (lo que habría pasado igual), lo que pagó la liga
         (premios de jornada y racha) y lo que aportó operar.
      3. NUESTRAS SUBASTAS DEL COMPUTER en esa ventana (libro de pujas):
         pujadas, ganadas, perdidas y el porcentaje de acierto.
      4. EL ONCE POR PRECIO de Pepe, Pollo17 y Luismi_Haz: el mejor once
         válido (1 POR, 3-5 DEF, 2-5 MED, 1-3 DEL) que se puede formar con
         la plantilla de hoy, a precio de hoy.

DE DONDE SALE CADA NUMERO (las convenciones del laboratorio, 16/10)

    día de mercado D   fecha(hora de Madrid - 7 h). El reset de las 07:00
                       (precios, subastas del Computer) cae en D.
    precio de D        la última muestra de `price_history` del día D; si
                       falta, la última de hasta `ARRASTRE` días antes.
    caja               23.300.000 + premios de jornada + racha + ventas
                       - compras, leído evento a evento del tablón.
    plantilla inicial  15 por manager. Se reconstruye desde una foto con
                       las plantillas de todos (`data/fotos/`): la de la
                       foto + lo vendido antes de la foto - lo comprado
                       antes de la foto. Con la foto de hoy es «la de hoy
                       + vendidos - comprados».
    patrimonio         caja + plantilla a precio de D, al CIERRE de D
                       (después de todas las operaciones de D).

    El tablón se reescribe: Biwenger reemite el mismo hecho con otro
    `event_id` y a veces con la fecha movida unos minutos. La misma
    operación (tipo, jugador, de, a, importe) dentro de una hora desde la
    primera copia es una copia (la regla de `caja_de_la_liga`, que es de
    donde sale cuáles jornadas pagan).

NI RED, NI ESCRITURAS, NI RELOJ

    Solo lee `data/`. Con `--escribir`, y solo entonces, escribe
    `data/trading/el_marcador_de_la_carrera.json`. «Hoy» es el último día
    de mercado con precios, no el reloj del sistema. Nunca escribe en
    Biwenger.

USO

    python3 scripts/el_marcador_de_la_carrera.py [--hoy AAAA-MM-DD] [--escribir]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.caja_de_la_liga import (                  # noqa: E402
    SALDO_INICIAL,
    VENTANA_REEMISION,
    jornadas_que_pagan,
)


TABLON = RAIZ / "data" / "rival_intelligence" / "board_events.json"
PRECIOS = RAIZ / "data" / "autopilot" / "price_history.json"
LIBRO_DE_PUJAS = RAIZ / "data" / "trading" / "bid_outcome_ledger.json"
ESCAPARATE = RAIZ / "data" / "trading" / "libro_del_escaparate.jsonl"
MARCADOR = RAIZ / "data" / "intelligence" / "marcador.json"
BITACORA = RAIZ / "data" / "solvency" / "bitacora_del_saldo.jsonl"
FOTOS = RAIZ / "data" / "fotos"
SALIDA = RAIZ / "data" / "trading" / "el_marcador_de_la_carrera.json"

PEPE = 14175949
POLLO = 14145555
LUISMI = 14156489
LOS_TRES = (PEPE, POLLO, LUISMI)
NOMBRES = {PEPE: "Pepe", POLLO: "Pollo17", LUISMI: "Luismi_Haz"}

JUGADORES_DEL_REPARTO = 15
HORA_DEL_RESET = 7
# Días que se arrastra el último precio si falta el del día. El 07/09 no
# hay ninguna muestra y el 23/09 faltan unos 40 jugadores: sin arrastre,
# esos días el patrimonio de todos se hundiría por un hueco del libro.
ARRASTRE = 3
SEMANAS_EN_EL_INFORME = 4

# Las formaciones válidas: 1 POR + DEF + MED + DEL = 11.
POSICIONES = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}
FORMACIONES = tuple(
    (d, m, f)
    for d in range(3, 6)
    for m in range(2, 6)
    for f in range(1, 4)
    if d + m + f == 10
)

# Lo que paga la liga: mueve caja y no plantilla, y lo cobra también
# quien no hace nada.
INGRESOS_DE_LA_LIGA = ("premio", "racha")


# ============================================================
# LO PEQUEÑO
# ============================================================


def _int(valor, defecto=None):
    """Entero o `defecto`. Los booleanos no son enteros aquí. Nunca lanza."""
    try:
        if isinstance(valor, bool) or valor is None:
            return defecto
        return int(valor)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _lista(contenido) -> list:
    if isinstance(contenido, dict):
        return [contenido]
    return contenido if isinstance(contenido, list) else []


def _id(quien):
    return _int(quien.get("id")) if isinstance(quien, dict) else None


def _ultimo_domingo(anio: int, mes: int) -> date:
    d = date(anio, mes, 31)                 # marzo y octubre tienen 31
    return d - timedelta(days=(d.weekday() + 1) % 7)


def hora_de_madrid(ts):
    """
    El instante `ts` (epoch) en hora de Madrid, sin zona. None si no se
    puede.

    POR QUE NO `zoneinfo`: en Windows -donde el dueño corre parte de las
    cosas- `ZoneInfo("Europe/Madrid")` necesita el paquete `tzdata`, y el
    día que falte el script no debe caerse. La regla de la UE es fija
    desde 1996: verano desde el último domingo de marzo a la 01:00 UTC
    hasta el último domingo de octubre a la 01:00 UTC. Nunca lanza.
    """
    try:
        utc = datetime(1970, 1, 1) + timedelta(seconds=float(ts))
        inicio = datetime.combine(_ultimo_domingo(utc.year, 3), time(1))
        fin = datetime.combine(_ultimo_domingo(utc.year, 10), time(1))
        return utc + timedelta(hours=2 if inicio <= utc < fin else 1)
    except Exception:                               # noqa: BLE001
        return None


def dia_de_mercado(ts):
    """
    El día de mercado de un instante: lo que pasa entre D 07:00 y D+1 06:59
    (Madrid) es de D. Acepta epoch o texto ISO (sin zona = UTC). None si
    no se puede. Nunca lanza.
    """
    try:
        if isinstance(ts, str):
            instante = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
            if instante.tzinfo is None:
                instante = instante.replace(tzinfo=timezone.utc)
            ts = instante.timestamp()
        local = hora_de_madrid(ts)
        if local is None:
            return None
        return (local - timedelta(hours=HORA_DEL_RESET)).date()
    except Exception:                               # noqa: BLE001
        return None


def _desde_hora_de_madrid(texto):
    """Texto ISO en hora de Madrid sin zona -> epoch. None si no se puede."""
    try:
        local = datetime.fromisoformat(str(texto).strip().strip("'\""))
        if local.tzinfo is not None:
            return local.timestamp()
        como_utc = local.replace(tzinfo=timezone.utc).timestamp()
        # El desfase (+1 h o +2 h) se mira una hora antes: a esa distancia
        # del cambio de hora solo se equivoca en la hora que no existe.
        sonda = como_utc - 3600
        desfase = hora_de_madrid(sonda) - (datetime(1970, 1, 1) + timedelta(seconds=sonda))
        return como_utc - desfase.total_seconds()
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# 1. EL TABLON, SIN COPIAS
# ============================================================


def movimientos_del_tablon(eventos, ventana: int = VENTANA_REEMISION) -> dict:
    """
    Todo lo que mueve caja o plantilla, una sola vez y en orden.

    Cada movimiento: {t, dia, tipo, jugador, de, a, quien, importe}.

        subasta   `market`: el Computer vende en el reset; paga `a`.
        venta     `transfer` sin `a`: `de` vende al Computer y cobra.
        traspaso  `transfer` con `a`: entre managers; paga `a`, cobra `de`.
        premio    `roundFinished` de una jornada que paga; cobra `quien`.
        racha     `bonus` (racha diaria); cobra `quien`.

    LA COPIA SE ANCLA EN LA PRIMERA APARICION y no se reancla al
    descartar: tres copias a 16:29, 16:34 y 16:38 caen las tres contra la
    de las 16:29, y una cadena larga de reemisiones no puede arrastrar la
    ventana hasta tragarse una operación de verdad. Comprar al mismo
    jugador por lo mismo dentro de dos semanas son dos hechos.

    LA JORNADA, UNA VEZ POR `round.id`: con la fecha de la primera copia
    (cuando se cobró) y el importe de la última (una corrección de puntos
    sustituye a la anterior, no se suma).

    Nunca lanza: con basura devuelve la forma vacía.
    """
    salida = {"movimientos": [], "copias": 0, "eventos": 0,
              "jornadas_pagadas": [], "altas": {}}
    try:
        filas = [e for e in _lista(eventos) if isinstance(e, dict)]
        filas.sort(key=lambda e: _int(e.get("date"), 0))
        pagan = jornadas_que_pagan(filas)
        vistos: dict = {}
        copias = 0
        movs = []
        jornadas: dict = {}
        altas: dict = {}

        def es_copia(clave, t) -> bool:
            primera = vistos.get(clave)
            if primera is not None and t - primera <= ventana:
                return True
            vistos[clave] = t
            return False

        for evento in filas:
            t = _int(evento.get("date"))
            dia = dia_de_mercado(t) if t is not None else None
            if dia is None:
                continue
            tipo = evento.get("type")
            contenido = evento.get("content")

            if tipo in ("market", "transfer"):
                for op in _lista(contenido):
                    if not isinstance(op, dict):
                        continue
                    pid = _int(op.get("player"))
                    de, a = _id(op.get("from")), _id(op.get("to"))
                    importe = _int(op.get("amount"))
                    if pid is None or importe is None or not (de or a):
                        continue
                    if es_copia((tipo, pid, de, a, importe), t):
                        copias += 1
                        continue
                    clase = ("subasta" if tipo == "market"
                             else "traspaso" if (de and a) else "venta")
                    movs.append({"t": t, "dia": dia, "tipo": clase, "jugador": pid,
                                 "de": de or None, "a": a or None, "quien": None,
                                 "importe": importe})

            elif tipo == "bonus":
                for op in _lista(contenido):
                    if not isinstance(op, dict):
                        continue
                    quien = _id(op.get("user"))
                    importe = _int(op.get("amount"))
                    if not quien or importe is None:
                        continue
                    if es_copia(("bonus", quien, importe, op.get("reason")), t):
                        copias += 1
                        continue
                    movs.append({"t": t, "dia": dia, "tipo": "racha", "jugador": None,
                                 "de": None, "a": None, "quien": quien, "importe": importe})

            elif tipo == "roundFinished":
                for bloque in _lista(contenido):
                    if not isinstance(bloque, dict):
                        continue
                    ronda = bloque.get("round") if isinstance(bloque.get("round"), dict) else {}
                    rid = ronda.get("id")
                    if rid is None or rid not in pagan:
                        continue
                    if rid in jornadas:
                        copias += 1
                        jornadas[rid] = (jornadas[rid][0], jornadas[rid][1], bloque)
                    else:
                        jornadas[rid] = (t, dia, bloque)

            elif tipo == "userJoin":
                for u in _lista(contenido):
                    uid = _id(u)
                    if uid:
                        altas.setdefault(uid, t)

        for rid, (t, dia, bloque) in jornadas.items():
            for fila in _lista(bloque.get("results")):
                if not isinstance(fila, dict):
                    continue
                quien = _id(fila.get("user"))
                importe = _int(fila.get("bonus"), 0)
                if quien and importe:
                    movs.append({"t": t, "dia": dia, "tipo": "premio", "jugador": None,
                                 "de": None, "a": None, "quien": quien, "importe": importe,
                                 "jornada": rid})

        movs.sort(key=lambda m: (m["t"], m["tipo"], m["jugador"] or 0))
        return {"movimientos": movs, "copias": copias, "eventos": len(filas),
                "jornadas_pagadas": sorted(jornadas, key=str), "altas": altas}
    except Exception:                               # noqa: BLE001
        return salida


def flujos_de(movimientos, uid) -> list:
    """
    Los movimientos de un manager como (t, dia, caja, entra, sale, tipo):
    `caja` con signo, `entra`/`sale` el jugador que entra o sale de su
    plantilla (o None). Nunca lanza.
    """
    salida = []
    try:
        for m in _lista(movimientos):
            if not isinstance(m, dict):
                continue
            importe = _int(m.get("importe"), 0)
            if m.get("quien") == uid:
                salida.append((m["t"], m["dia"], importe, None, None, m["tipo"]))
            if m.get("a") == uid:
                salida.append((m["t"], m["dia"], -importe, m.get("jugador"), None, m["tipo"]))
            if m.get("de") == uid:
                salida.append((m["t"], m["dia"], importe, None, m.get("jugador"), m["tipo"]))
        salida.sort(key=lambda f: f[0])
    except Exception:                               # noqa: BLE001
        return []
    return salida


# ============================================================
# 2. LOS PRECIOS POR DIA
# ============================================================


def precios_por_dia(historial) -> dict:
    """
    {jugador: {día de mercado: precio}} con la ÚLTIMA muestra de cada día:
    es el precio que rige desde el reset de D hasta el de D+1 (el 99,99 %
    de los días no cambia dentro del día). Nunca lanza.
    """
    salida: dict = {}
    try:
        jugadores = historial.get("players") if isinstance(historial, dict) else None
        if not isinstance(jugadores, dict):
            return salida
        for pid, serie in jugadores.items():
            pid = _int(pid)
            if pid is None or not isinstance(serie, dict):
                continue
            ts, ps = serie.get("t"), serie.get("p")
            if not isinstance(ts, list) or not isinstance(ps, list):
                continue
            pares = [(_int(t), _int(p)) for t, p in zip(ts, ps)]
            dias = {}
            for t, p in sorted((x for x in pares if x[0] is not None), key=lambda x: x[0]):
                if p is None or p <= 0:
                    continue
                d = dia_de_mercado(t)
                if d is not None:
                    dias[d] = p
            if dias:
                salida[pid] = dias
    except Exception:                               # noqa: BLE001
        return salida
    return salida


def precio(precios, pid, dia, arrastre: int = ARRASTRE):
    """El precio de `pid` en `dia`, o el último de hasta `arrastre` días antes. Nunca lanza."""
    try:
        serie = precios.get(pid) or {}
        for i in range(max(0, int(arrastre)) + 1):
            p = serie.get(dia - timedelta(days=i))
            if p is not None:
                return p
    except Exception:                               # noqa: BLE001
        return None
    return None


def valorar(tenencia, precios, dia) -> tuple:
    """(valor de la plantilla a precio de `dia`, jugadores sin precio). Nunca lanza."""
    valor, sin_precio = 0, 0
    try:
        for pid, n in dict(tenencia or {}).items():
            n = _int(n, 0)
            if n <= 0:
                continue
            p = precio(precios, pid, dia)
            if p is None:
                sin_precio += n
            else:
                valor += p * n
    except Exception:                               # noqa: BLE001
        return 0, 0
    return valor, sin_precio


# ============================================================
# 3. LA PLANTILLA DEL REPARTO Y EL PATRIMONIO DIA A DIA
# ============================================================


def plantilla_inicial(ancla, flujos, t_ancla=None) -> dict:
    """
    La plantilla del reparto: la del ancla + lo vendido antes del ancla -
    lo comprado antes del ancla. Sin `t_ancla` el ancla es «hoy» y cuenta
    todo. En multiconjunto: un jugador comprado, vendido y recomprado
    cuenta las veces que toca. Lo que no cuadre (negativos, un total
    distinto de 15) lo dice `el_reparto_cuadra`. Nunca lanza.
    """
    cuenta = collections.Counter()
    try:
        for pid in _lista(ancla):
            pid = _int(pid)
            if pid is not None:
                cuenta[pid] += 1
        for t, _dia, _caja, entra, sale, _tipo in _lista(flujos):
            if t_ancla is not None and t > t_ancla:
                continue
            if entra is not None:
                cuenta[entra] -= 1
            if sale is not None:
                cuenta[sale] += 1
    except Exception:                               # noqa: BLE001
        return {}
    return {pid: n for pid, n in cuenta.items() if n != 0}


def el_reparto_cuadra(inicial, tamano: int = JUGADORES_DEL_REPARTO) -> bool:
    """15 jugadores y ninguno en negativo. Nunca lanza."""
    try:
        valores = [_int(n, 0) for n in dict(inicial or {}).values()]
        return bool(valores) and min(valores) > 0 and sum(valores) == tamano
    except Exception:                               # noqa: BLE001
        return False


def serie_de_patrimonio(inicial, flujos, precios, dias, saldo_inicial: int = SALDO_INICIAL,
                        desde=None) -> dict:
    """
    {día: {caja, plantilla, patrimonio, jugadores, sin_precio, tenencia}}
    al CIERRE de cada día de mercado de `dias`: después de todas las
    operaciones del día, a precio del día. Lo anterior al primer día (el
    reparto y las subastas del 10 al 17/08, que no tienen precio) entra
    en el primer día. `desde` salta los días antes del alta del manager.

    `tenencia` es la plantilla de ese cierre ({jugador: n}); de ella sale
    «no hacer nada». Nunca lanza.
    """
    salida: dict = {}
    try:
        tenencia = collections.Counter({k: _int(v, 0) for k, v in dict(inicial or {}).items()})
        caja = _int(saldo_inicial, 0)
        pendientes = sorted(_lista(flujos), key=lambda f: f[0])
        i = 0
        for dia in sorted(d for d in _lista(dias) if isinstance(d, date)):
            while i < len(pendientes) and pendientes[i][1] <= dia:
                _t, _d, delta, entra, sale, _tipo = pendientes[i]
                caja += _int(delta, 0)
                if entra is not None:
                    tenencia[entra] += 1
                if sale is not None:
                    tenencia[sale] -= 1
                i += 1
            if desde is not None and dia < desde:
                continue
            viva = {pid: n for pid, n in tenencia.items() if n > 0}
            valor, sin_precio = valorar(viva, precios, dia)
            salida[dia] = {"caja": caja, "plantilla": valor, "patrimonio": caja + valor,
                           "jugadores": sum(viva.values()), "sin_precio": sin_precio,
                           "tenencia": viva}
    except Exception:                               # noqa: BLE001
        return salida
    return salida


def caja_en(flujos, t, saldo_inicial: int = SALDO_INICIAL):
    """La caja justo después del instante `t` (epoch). None si no se puede. Nunca lanza."""
    try:
        return _int(saldo_inicial, 0) + sum(_int(f[2], 0) for f in _lista(flujos) if f[0] <= t)
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# 4. LA VENTANA CONTRA NO HACER NADA
# ============================================================


def contra_no_hacer_nada(serie, flujos, precios, desde, hasta):
    """
    Del cierre de `desde` al cierre de `hasta`:

        real     patrimonio(hasta) - patrimonio(desde)
        nada     lo que habría cambiado quedándose quieto: la plantilla
                 del cierre de `desde` valorada en `hasta` menos en
                 `desde`, con la misma caja. Lo pone el mercado.
        premios  lo que pagó la liga en la ventana (jornada + racha).
        operar   real - nada - premios: lo que aportaron las compras y las
                 ventas (lo que se dejó de ganar o se ganó por moverse).

    `real - nada` es la ventaja sobre no hacer nada, premios incluidos: la
    liga los paga también al que no se mueve, pero el que no se mueve
    también los cobra, así que se enseñan aparte para no confundirlos con
    operar. Quien no mueve nada en la ventana tiene operar = 0 exacto,
    porque los dos lados se valoran con la misma función. None si falta
    uno de los dos cierres. Nunca lanza.
    """
    try:
        a, b = serie.get(desde), serie.get(hasta)
        if not a or not b:
            return None
        quieto_desde, _ = valorar(a["tenencia"], precios, desde)
        quieto_hasta, sin_precio = valorar(a["tenencia"], precios, hasta)
        real = b["patrimonio"] - a["patrimonio"]
        nada = quieto_hasta - quieto_desde
        dentro = [f for f in _lista(flujos) if desde < f[1] <= hasta]
        premios = sum(f[2] for f in dentro if f[5] in INGRESOS_DE_LA_LIGA)
        return {
            "desde": desde, "hasta": hasta,
            "patrimonio_desde": a["patrimonio"], "patrimonio_hasta": b["patrimonio"],
            "real": real, "nada": nada, "ventaja": real - nada,
            "premios": premios, "operar": real - nada - premios,
            "compras": sum(1 for f in dentro if f[3] is not None),
            "ventas": sum(1 for f in dentro if f[4] is not None),
            "sin_precio_quieto": sin_precio,
        }
    except Exception:                               # noqa: BLE001
        return None


def las_ventanas(hoy, primer_dia) -> list:
    """
    Los últimos 7 días, la semana en curso (del cierre del último lunes a
    hoy) y cada semana de lunes a lunes (del cierre de un lunes al cierre
    del siguiente), de la más reciente a la más antigua. Ninguna empieza
    antes del primer día con precios. Nunca lanza.
    """
    salida = []
    try:
        if not isinstance(hoy, date) or not isinstance(primer_dia, date) or hoy <= primer_dia:
            return salida
        hace_7 = max(primer_dia, hoy - timedelta(days=7))
        salida.append({"clave": "ultimos_7_dias", "etiqueta": "Últimos 7 días",
                       "desde": hace_7, "hasta": hoy})
        lunes = hoy - timedelta(days=hoy.weekday())
        if lunes < hoy and lunes >= primer_dia:
            salida.append({"clave": "semana_en_curso", "etiqueta": "Semana en curso",
                           "desde": lunes, "hasta": hoy})
        fin = lunes
        while fin - timedelta(days=7) >= primer_dia:
            ini = fin - timedelta(days=7)
            salida.append({"clave": f"lunes_{ini.isoformat()}",
                           "etiqueta": f"{ini:%d/%m} → {fin:%d/%m}",
                           "desde": ini, "hasta": fin})
            fin = ini
    except Exception:                               # noqa: BLE001
        return []
    return salida


# ============================================================
# 5. NUESTRAS SUBASTAS DEL COMPUTER
# ============================================================


PRIORIDAD_DEL_RESULTADO = {"WON": 3, "LOST": 2}


def las_pujas(libro, desde, hasta, nombres=None) -> dict:
    """
    Nuestras subastas del Computer de la ventana, del libro de pujas.

    UNA SUBASTA ES UN JUGADOR EN UN RESET, NO UNA FILA DEL LIBRO. El libro
    apunta cada vez que se PONE la puja, y el bot la renovaba en cada
    vuelta: Boyomo tiene 5 filas para el reset del 18/09 y Maffeo 9 para
    el del 19/09. Contando filas, la semana del 14 al 21/09 salían 35
    ganadas; el tablón dice 23. Así que se agrupa por (jugador, reset que
    la resuelve): ganada si alguna fila ganó, si no perdida, si no
    pendiente; nuestra puja, la más alta.

    Una subasta es de la ventana si la resuelve un reset de (desde, hasta]:
    los mismos resets que mueven el patrimonio de la ventana. Una
    pendiente (sin resolver) se resuelve en el reset siguiente a cuando se
    pujó, y cuenta si se pujó dentro. Las pujas a managers
    (`seller_user_id`) no son subastas: se cuentan aparte.

        acierto = ganadas / (ganadas + perdidas); None sin resueltas.

    Nunca lanza.
    """
    salida = {"pujadas": 0, "ganadas": 0, "perdidas": 0, "pendientes": 0,
              "acierto": None, "a_managers": 0, "filas_del_libro": 0,
              "perdidas_detalle": []}
    try:
        pujas = libro.get("bids") if isinstance(libro, dict) else None
        filas = list(pujas.values()) if isinstance(pujas, dict) else _lista(pujas)
        nombres = nombres if isinstance(nombres, dict) else {}
        subastas: dict = {}
        a_managers = set()
        for p in filas:
            if not isinstance(p, dict):
                continue
            resultado = str(p.get("outcome") or "").upper()
            puesta = dia_de_mercado(p.get("placed_at")) if p.get("placed_at") else None
            reset = None
            if resultado in PRIORIDAD_DEL_RESULTADO and p.get("resolved_at"):
                reset = dia_de_mercado(p.get("resolved_at"))
            if reset is None and puesta is not None:
                reset = puesta + timedelta(days=1)
            if reset is None:
                continue
            pendiente = resultado not in PRIORIDAD_DEL_RESULTADO
            if not (desde < reset <= hasta or (pendiente and reset == hasta + timedelta(days=1))):
                continue
            pid = _int(p.get("player_id"))
            clave = (pid if pid is not None else str(p.get("player_name")), reset)
            salida["filas_del_libro"] += 1
            if p.get("seller_user_id"):
                a_managers.add(clave)
                continue
            s = subastas.setdefault(clave, {"jugador": pid, "nombre": None, "resultado": "PENDING",
                                            "puja": None, "gano_con": None})
            s["nombre"] = s["nombre"] or p.get("player_name") or nombres.get(pid) or str(pid)
            if PRIORIDAD_DEL_RESULTADO.get(resultado, 0) > PRIORIDAD_DEL_RESULTADO.get(s["resultado"], 0):
                s["resultado"] = resultado
            nuestra, gano = _int(p.get("amount")), _int(p.get("winning_amount"))
            if nuestra is not None and (s["puja"] is None or nuestra > s["puja"]):
                s["puja"] = nuestra
            if gano is not None and (s["gano_con"] is None or gano > s["gano_con"]):
                s["gano_con"] = gano
        salida["a_managers"] = len(a_managers)
        for (_clave, reset), s in sorted(subastas.items(), key=lambda kv: (kv[0][1], str(kv[0][0]))):
            salida["pujadas"] += 1
            if s["resultado"] == "WON":
                salida["ganadas"] += 1
            elif s["resultado"] == "LOST":
                salida["perdidas"] += 1
                nuestra, gano = s["puja"], s["gano_con"]
                salida["perdidas_detalle"].append({
                    "jugador": s["jugador"], "nombre": s["nombre"], "reset": reset,
                    "puja": nuestra, "gano_con": gano,
                    "por_encima": (round(100.0 * (gano / nuestra - 1), 1)
                                   if gano and nuestra else None),
                })
            else:
                salida["pendientes"] += 1
        resueltas = salida["ganadas"] + salida["perdidas"]
        if resueltas:
            salida["acierto"] = round(salida["ganadas"] / resueltas, 3)
    except Exception:                               # noqa: BLE001
        return salida
    return salida


# ============================================================
# 6. EL ONCE POR PRECIO
# ============================================================


def once_por_precio(jugadores) -> dict:
    """
    El once válido más caro: 1 POR, 3-5 DEF, 2-5 MED, 1-3 DEL, 11 en
    total. Para cada formación se cogen los más caros de cada puesto y se
    queda la que más suma; si ninguna se puede llenar, la que menos
    huecos deja (y entre esas, la que más suma).

    `jugadores`: [{id, posicion (1-4), precio}]. Sin posición o sin precio
    no entran (se cuentan). Empates: el orden de `FORMACIONES` y, dentro
    de un puesto, el id más bajo. Nunca lanza.
    """
    salida = {"formacion": None, "valor": 0, "jugadores": [], "completo": False,
              "huecos": 11, "sin_posicion": 0, "sin_precio": 0}
    try:
        por_puesto = {1: [], 2: [], 3: [], 4: []}
        for j in _lista(jugadores):
            if not isinstance(j, dict):
                continue
            pid = _int(j.get("id"))
            if pid is None:
                continue
            valor = _int(j.get("precio"))
            puesto = _int(j.get("posicion"))
            if valor is None or valor < 0:
                salida["sin_precio"] += 1
                continue
            if puesto not in por_puesto:
                salida["sin_posicion"] += 1
                continue
            por_puesto[puesto].append((valor, pid))
        for lista in por_puesto.values():
            lista.sort(key=lambda x: (-x[0], x[1]))
        mejor = None
        for d, m, f in FORMACIONES:
            pide = {1: 1, 2: d, 3: m, 4: f}
            elegidos = [(puesto, x) for puesto, n in pide.items() for x in por_puesto[puesto][:n]]
            huecos = 11 - len(elegidos)
            suma = sum(x[0] for _, x in elegidos)
            if mejor is None or (-huecos, suma) > (-mejor[1], mejor[2]):
                mejor = ((d, m, f), huecos, suma, elegidos)
        (d, m, f), huecos, suma, elegidos = mejor
        salida.update({
            "formacion": f"{d}-{m}-{f}", "valor": suma, "huecos": huecos,
            "completo": huecos == 0,
            "jugadores": [{"id": pid, "posicion": puesto, "precio": valor}
                          for puesto, (valor, pid) in elegidos],
        })
    except Exception:                               # noqa: BLE001
        return salida
    return salida


# ============================================================
# 7. LAS FICHAS: POSICION Y NOMBRE DE CADA JUGADOR
# ============================================================


def las_fichas(*fuentes) -> tuple:
    """
    ({jugador: posición}, {jugador: nombre}) de todo lo que se le pase: la
    foto, las filas del escaparate, el marcador… Se recorre entero y vale
    cualquier diccionario con `id` (o `player_id`) y `position` de 1 a 4.
    La posición principal no cambia en la temporada, así que da igual de
    qué fecha sea la fuente. Nunca lanza.
    """
    posiciones, nombres = {}, {}

    def recorrer(o, profundidad=0):
        if profundidad > 12:
            return
        if isinstance(o, dict):
            pid = _int(o.get("id"), _int(o.get("player_id")))
            puesto = _int(o.get("position"))
            if pid is not None and puesto in POSICIONES:
                posiciones[pid] = puesto
                nombre = o.get("name") or o.get("player_name")
                if isinstance(nombre, str) and nombre:
                    nombres.setdefault(pid, nombre)
            # Un nombre sin posición solo si las claves dicen que es un
            # JUGADOR: `{id, name}` también es un equipo o un manager.
            elif _int(o.get("player_id")) is not None and isinstance(o.get("player_name"), str):
                nombres.setdefault(_int(o.get("player_id")), o["player_name"])
            for v in o.values():
                if isinstance(v, (dict, list)):
                    recorrer(v, profundidad + 1)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, (dict, list)):
                    recorrer(v, profundidad + 1)

    try:
        for fuente in fuentes:
            recorrer(fuente)
    except Exception:                               # noqa: BLE001
        pass
    return posiciones, nombres


def el_ancla(foto) -> dict | None:
    """
    De una foto con `rival_squads`: {t, plantillas {manager: [jugadores]},
    nombres {manager: nombre}, valores {manager: team_value}}. El instante
    sale del reloj del mercado de la foto (`next_reset_epoch` -
    `seconds_to_reset`, que es epoch y no admite dudas de zona); si no lo
    trae, de `meta.generated_at`, que está en hora de Madrid. None si la
    foto no sirve. Nunca lanza.
    """
    try:
        if not isinstance(foto, dict):
            return None
        bloque = foto.get("rival_squads")
        managers = bloque.get("managers") if isinstance(bloque, dict) else None
        if not isinstance(managers, list) or not managers:
            return None
        reloj = foto.get("market_clock") if isinstance(foto.get("market_clock"), dict) else {}
        t = None
        if _int(reloj.get("next_reset_epoch")) and _int(reloj.get("seconds_to_reset")) is not None:
            t = _int(reloj["next_reset_epoch"]) - _int(reloj["seconds_to_reset"])
        if t is None:
            meta = foto.get("meta") if isinstance(foto.get("meta"), dict) else {}
            t = _desde_hora_de_madrid(meta.get("generated_at"))
        if t is None:
            return None
        plantillas, nombres, valores = {}, {}, {}
        for m in managers:
            if not isinstance(m, dict):
                continue
            uid = _int(m.get("user_id"))
            jugadores = m.get("players")
            if not uid or not isinstance(jugadores, list):
                continue
            plantillas[uid] = [_int(j.get("id")) for j in jugadores
                               if isinstance(j, dict) and _int(j.get("id")) is not None]
            nombres[uid] = str(m.get("name") or uid)
            valores[uid] = _int(m.get("team_value"))
        if not plantillas:
            return None
        return {"t": t, "plantillas": plantillas, "nombres": nombres, "valores": valores}
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# 8. TODO JUNTO
# ============================================================


def el_marcador(eventos, historial, libro_de_pujas=None, foto=None, otras_fichas=None,
                hoy=None, bitacora=None, plantilla_del_marcador=None) -> dict:
    """
    El marcador entero, sin leer ni escribir nada: todo entra por
    argumento.

        eventos                 `board_events.json`
        historial               `price_history.json`
        libro_de_pujas          `bid_outcome_ledger.json`
        foto                    una foto con `rival_squads` (el ancla)
        otras_fichas            más fuentes de posición y nombre
        hoy                     el día de mercado de «hoy» (por defecto,
                                el último con precios)
        bitacora                la última fila de `bitacora_del_saldo`
                                (para el cuadre de nuestra caja)
        plantilla_del_marcador  nuestra plantilla según `marcador.json`

    Forma fija; `available: False` y `reason` si no se puede. Nunca lanza.
    """
    salida = {"available": False, "reason": None, "hoy": None}
    try:
        tablon = movimientos_del_tablon(eventos)
        if not tablon["movimientos"]:
            return {**salida, "reason": "El tablón llega vacío: sin eventos no hay caja."}
        precios = precios_por_dia(historial)
        if not precios:
            return {**salida, "reason": "Sin precios no hay patrimonio."}
        ancla = el_ancla(foto)
        if ancla is None:
            return {**salida, "reason": "Sin una foto con las plantillas de todos no se "
                                        "puede reconstruir el reparto."}
        todos_los_dias = sorted({d for s in precios.values() for d in s})
        primer_dia = todos_los_dias[0]
        if hoy is None:
            hoy = todos_los_dias[-1]
        if not isinstance(hoy, date) or hoy < primer_dia:
            return {**salida, "reason": f"«Hoy» ({hoy}) cae antes del primer precio ({primer_dia})."}
        dias = [primer_dia + timedelta(days=i) for i in range((hoy - primer_dia).days + 1)]

        posiciones, nombres = las_fichas(foto, otras_fichas)
        movs = tablon["movimientos"]

        managers = {}
        for uid, plantilla in ancla["plantillas"].items():
            flujos = flujos_de(movs, uid)
            inicial = plantilla_inicial(plantilla, flujos, ancla["t"])
            alta = tablon["altas"].get(uid)
            desde = dia_de_mercado(alta) if alta else None
            serie = serie_de_patrimonio(inicial, flujos, precios, dias, desde=desde)
            managers[uid] = {
                "nombre": NOMBRES.get(uid) or ancla["nombres"].get(uid) or str(uid),
                "inicial": inicial,
                "reparto_cuadra": el_reparto_cuadra(inicial),
                "flujos": flujos,
                "serie": serie,
            }

        ventanas = []
        for v in las_ventanas(hoy, primer_dia):
            fila = dict(v)
            fila["managers"] = {
                uid: contra_no_hacer_nada(managers[uid]["serie"], managers[uid]["flujos"],
                                          precios, v["desde"], v["hasta"])
                for uid in LOS_TRES if uid in managers
            }
            fila["pujas"] = las_pujas(libro_de_pujas, v["desde"], v["hasta"], nombres)
            if PEPE in managers:
                fila["pujas"]["ganadas_en_el_tablon"] = sum(
                    1 for f in managers[PEPE]["flujos"]
                    if f[5] == "subasta" and f[3] is not None and v["desde"] < f[1] <= v["hasta"])
            ventanas.append(fila)

        onces = {}
        for uid in LOS_TRES:
            if uid not in managers or hoy not in managers[uid]["serie"]:
                continue
            tenencia = managers[uid]["serie"][hoy]["tenencia"]
            jugadores = [{"id": pid, "posicion": posiciones.get(pid),
                          "precio": precio(precios, pid, hoy)}
                         for pid, n in tenencia.items() for _ in range(n)]
            onces[uid] = once_por_precio(jugadores)

        return {
            "available": True,
            "reason": None,
            "hoy": hoy,
            "primer_dia": primer_dia,
            "tablon": {"eventos": tablon["eventos"], "copias": tablon["copias"],
                       "movimientos": len(movs),
                       "jornadas_pagadas": tablon["jornadas_pagadas"]},
            "ancla": {"t": ancla["t"], "managers": len(ancla["plantillas"])},
            "managers": managers,
            "ventanas": ventanas,
            "onces": onces,
            "nombres": nombres,
            "cuadre": el_cuadre(managers, precios, bitacora, plantilla_del_marcador, hoy),
        }
    except Exception as error:                      # noqa: BLE001
        return {**salida, "reason": f"No se pudo calcular: {type(error).__name__}: {error}"}


def el_cuadre(managers, precios, bitacora=None, plantilla_del_marcador=None, hoy=None) -> dict:
    """
    Lo que se puede comprobar contra algo medido fuera del tablón:

        reparto     cuántos managers salen con 15 jugadores y ninguno en
                    negativo.
        caja        nuestra caja reconstruida en el instante de la última
                    fila de la bitácora del saldo (el `balance` de la API),
                    y el valor de nuestra plantilla en ese instante contra
                    su `roster_value`.
        plantilla   nuestra plantilla de hoy contra la del marcador.

    Nunca lanza.
    """
    salida = {"reparto_ok": 0, "reparto_de": 0, "caja": None, "plantilla": None}
    try:
        salida["reparto_de"] = len(managers or {})
        salida["reparto_ok"] = sum(1 for m in (managers or {}).values() if m.get("reparto_cuadra"))
        pepe = (managers or {}).get(PEPE)
        if pepe and isinstance(bitacora, dict) and bitacora.get("at") is not None:
            instante = datetime.fromisoformat(str(bitacora["at"]).replace("Z", "+00:00"))
            if instante.tzinfo is None:
                instante = instante.replace(tzinfo=timezone.utc)
            t = instante.timestamp()
            nuestra = caja_en(pepe["flujos"], t)
            leida = _int(bitacora.get("balance"))
            tenencia = collections.Counter(pepe.get("inicial") or {})
            for f in pepe["flujos"]:
                if f[0] <= t and f[3] is not None:
                    tenencia[f[3]] += 1
                if f[0] <= t and f[4] is not None:
                    tenencia[f[4]] -= 1
            valor, _ = valorar(tenencia, precios, dia_de_mercado(t))
            leido = _int(bitacora.get("roster_value"))
            salida["caja"] = {"at": str(bitacora["at"]), "reconstruida": nuestra,
                              "bitacora": leida,
                              "cuadra": nuestra is not None and nuestra == leida,
                              "plantilla_reconstruida": valor, "plantilla_bitacora": leido,
                              "plantilla_cuadra": leido is not None and valor == leido}
        if pepe and hoy in (pepe.get("serie") or {}) and plantilla_del_marcador is not None:
            hoy_ids = sorted(pid for pid, n in pepe["serie"][hoy]["tenencia"].items() for _ in range(n))
            suyos = sorted(p for p in (_int(x) for x in _lista(plantilla_del_marcador)) if p is not None)
            salida["plantilla"] = {"reconstruida": len(hoy_ids), "marcador": len(suyos),
                                   "cuadra": hoy_ids == suyos}
    except Exception:                               # noqa: BLE001
        return salida
    return salida


# ============================================================
# 9. EL INFORME
# ============================================================


def _e(x, signo=False) -> str:
    """Euros con puntos de miles: 1.234.567 (con signo si se pide)."""
    v = _int(x)
    if v is None:
        return "—"
    texto = f"{abs(v):,}".replace(",", ".")
    if signo:
        return ("+" if v >= 0 else "−") + texto
    return ("−" if v < 0 else "") + texto


def _m(x, signo=False) -> str:
    """Millones con una o dos decimales y coma: 103,3 M / +0,35 M."""
    v = _int(x)
    if v is None:
        return "—"
    decimales = 1 if abs(v) >= 10_000_000 else 2
    texto = f"{abs(v) / 1e6:.{decimales}f}".replace(".", ",")
    if signo:
        return ("+" if v >= 0 else "−") + texto + " M"
    return ("−" if v < 0 else "") + texto + " M"


def informe(r) -> str:
    """El informe para la consola, en castellano y corto. Nunca lanza."""
    try:
        if not isinstance(r, dict) or not r.get("available"):
            motivo = r.get("reason") if isinstance(r, dict) else None
            return f"EL MARCADOR DE LA CARRERA: SIN DATO. {motivo or 'Sin resultado.'}"
        hoy = r["hoy"]
        man = r["managers"]
        nombres = r.get("nombres") or {}
        lineas = []
        di = lineas.append
        t = r["tablon"]
        di(f"EL MARCADOR DE LA CARRERA · día de mercado {hoy:%d/%m/%Y}")
        anclada = hora_de_madrid(r["ancla"]["t"])
        di(f"  Tablón: {t['eventos']} eventos, {t['copias']} copias descartadas, "
           f"{t['movimientos']} movimientos. Precios del {r['primer_dia']:%d/%m} al {hoy:%d/%m}. "
           f"Reparto reconstruido desde la foto del {anclada:%d/%m %H:%M}.")
        di("")

        # --- patrimonio de hoy
        hace = hoy - timedelta(days=7)
        di("PATRIMONIO AL CIERRE DE HOY (caja + plantilla a precio de hoy)")
        filas = sorted(((m["serie"][hoy]["patrimonio"], uid) for uid, m in man.items()
                        if hoy in m["serie"]), reverse=True)
        for puesto, (nw, uid) in enumerate(filas, 1):
            s = man[uid]["serie"][hoy]
            antes = man[uid]["serie"].get(hace)
            d7 = f"  7 d {_m(nw - antes['patrimonio'], True):>9}" if antes else ""
            aviso = "" if man[uid]["reparto_cuadra"] else "  (el reparto no cuadra)"
            di(f"  {puesto}. {man[uid]['nombre'][:16]:16} {_m(nw):>8}  caja {_m(s['caja']):>8}  "
               f"{s['jugadores']:>2} jug.{d7}{aviso}")
        if PEPE in man and POLLO in man and hoy in man[PEPE]["serie"] and hoy in man[POLLO]["serie"]:
            brecha = man[POLLO]["serie"][hoy]["patrimonio"] - man[PEPE]["serie"][hoy]["patrimonio"]
            texto = f"  Brecha Pollo17 − Pepe: {_m(brecha)}"
            if hace in man[PEPE]["serie"] and hace in man[POLLO]["serie"]:
                antes = man[POLLO]["serie"][hace]["patrimonio"] - man[PEPE]["serie"][hace]["patrimonio"]
                texto += f" (hace 7 días {_m(antes)}: {_m(brecha - antes, True)})"
            di(texto)
        di("")

        # --- cuadre
        c = r.get("cuadre") or {}
        di("CUADRE")
        di(f"  Reparto: {c.get('reparto_ok')} de {c.get('reparto_de')} managers con "
           f"{JUGADORES_DEL_REPARTO} jugadores y ninguno en negativo.")
        if c.get("caja"):
            k = c["caja"]
            di(f"  Caja de Pepe en {k['at'][:16].replace('T', ' ')} UTC: reconstruida {_e(k['reconstruida'])}"
               f" · bitácora del saldo {_e(k['bitacora'])} · {'CUADRA' if k['cuadra'] else 'NO CUADRA'}")
            di(f"  Plantilla de Pepe en ese instante: {_e(k['plantilla_reconstruida'])}"
               f" · bitácora {_e(k['plantilla_bitacora'])}"
               f" · {'CUADRA' if k['plantilla_cuadra'] else 'NO CUADRA'}")
        if c.get("plantilla"):
            k = c["plantilla"]
            di(f"  Plantilla de Pepe hoy: {k['reconstruida']} jugadores · marcador {k['marcador']}"
               f" · {'CUADRA' if k['cuadra'] else 'NO CUADRA'}")
        di("")

        # --- ventanas
        di("CONTRA NO HACER NADA (del cierre de «desde» al de «hasta»)")
        di("  real = cambio de patrimonio · nada = lo que habría hecho la plantilla del")
        di("  principio con la misma caja · premios = jornada + racha · operar = real − nada − premios")
        semanas = 0
        for v in r["ventanas"]:
            es_semana = v["clave"].startswith("lunes_")
            if es_semana:
                semanas += 1
                if semanas > SEMANAS_EN_EL_INFORME:
                    break
            cab = v["etiqueta"] if es_semana else f"{v['etiqueta']} ({v['desde']:%d/%m} → {v['hasta']:%d/%m})"
            di(f"  {cab}")
            for uid in LOS_TRES:
                x = (v.get("managers") or {}).get(uid)
                if not x:
                    continue
                di(f"    {NOMBRES[uid]:11} real {_m(x['real'], True):>9} · nada {_m(x['nada'], True):>9}"
                   f" · ventaja {_m(x['ventaja'], True):>9} · premios {_m(x['premios'], True):>8}"
                   f" · operar {_m(x['operar'], True):>9}  (compras {x['compras']}, ventas {x['ventas']})")
            p = v.get("pujas") or {}
            acierto = f"{100 * p['acierto']:.0f} %" if p.get("acierto") is not None else "—"
            tablon = (f" (tablón {p['ganadas_en_el_tablon']})"
                      if p.get("ganadas_en_el_tablon") is not None else "")
            di(f"    Nuestras subastas del Computer: pujadas {p.get('pujadas', 0)} · "
               f"ganadas {p.get('ganadas', 0)}{tablon} · perdidas {p.get('perdidas', 0)} · "
               f"pendientes {p.get('pendientes', 0)} · acierto {acierto}"
               + (f" · pujas a managers {p['a_managers']}" if p.get("a_managers") else ""))
            if not es_semana and p.get("perdidas_detalle"):
                perdidas = []
                for x in p["perdidas_detalle"]:
                    if x.get("gano_con") and x.get("por_encima") is not None:
                        encima = f"{x['por_encima']:+.1f}".replace(".", ",")
                        perdidas.append(f"{x['nombre']} {_e(x['puja'])} (ganó {_e(x['gano_con'])}, "
                                        f"{encima} %)")
                    else:
                        perdidas.append(f"{x['nombre']} {_e(x['puja'])} (sin dato del ganador)")
                di("      perdidas: " + "; ".join(perdidas))
        di("")

        # --- el once por precio
        di("EL ONCE POR PRECIO (el mejor once válido de la plantilla de hoy, a precio de hoy)")
        onces = r.get("onces") or {}
        for uid in LOS_TRES:
            o = onces.get(uid)
            if not o:
                continue
            falta = "" if o["completo"] else f"  (faltan {o['huecos']})"
            extra = (f"  [{o['sin_posicion']} sin posición]" if o.get("sin_posicion") else "") + \
                    (f"  [{o['sin_precio']} sin precio]" if o.get("sin_precio") else "")
            di(f"  {NOMBRES[uid]:11} {o['formacion'] or '—':6} {_m(o['valor']):>8}{falta}{extra}")
        if onces.get(PEPE) and onces.get(POLLO):
            di(f"  Pollo17 − Pepe: {_m(onces[POLLO]['valor'] - onces[PEPE]['valor'], True)}")
        o = onces.get(PEPE)
        if o and o.get("jugadores"):
            di("  El de Pepe: " + ", ".join(
                f"{nombres.get(j['id'], j['id'])} {_m(j['precio'])}" for j in o["jugadores"]))
        return "\n".join(lineas)
    except Exception as error:                      # noqa: BLE001
        return f"EL MARCADOR DE LA CARRERA: no se pudo pintar ({type(error).__name__}: {error})."


# ============================================================
# 10. EL JSON
# ============================================================


def para_json(r) -> dict:
    """
    El resultado en forma de JSON: fechas en ISO, sin la tenencia de cada
    día ni los flujos (se reconstruyen en milisegundos y harían el fichero
    diez veces más grande). Nunca lanza.
    """
    def limpio(o):
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, dict):
            return {str(limpio(k)): limpio(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [limpio(v) for v in o]
        return o

    try:
        if not isinstance(r, dict) or not r.get("available"):
            return {"version": 1, "available": False,
                    "reason": r.get("reason") if isinstance(r, dict) else None}
        managers = {}
        for uid, m in r["managers"].items():
            managers[uid] = {
                "nombre": m["nombre"],
                "reparto_cuadra": m["reparto_cuadra"],
                "plantilla_inicial": m["inicial"],
                "serie": [{"dia": d, **{k: v for k, v in s.items() if k != "tenencia"}}
                          for d, s in sorted(m["serie"].items())],
                "plantilla_de_hoy": sorted(
                    pid for pid, n in (m["serie"].get(r["hoy"]) or {}).get("tenencia", {}).items()
                    for _ in range(n)),
            }
        return limpio({
            "version": 1,
            "available": True,
            "hoy": r["hoy"],
            "primer_dia": r["primer_dia"],
            "tablon": r["tablon"],
            "ancla": r["ancla"],
            "cuadre": r["cuadre"],
            "managers": managers,
            "ventanas": r["ventanas"],
            "onces": r["onces"],
        })
    except Exception as error:                      # noqa: BLE001
        return {"version": 1, "available": False,
                "reason": f"No se pudo pasar a JSON: {type(error).__name__}: {error}"}


# ============================================================
# 11. LA LECTURA (lo único que toca disco, y solo para leer)
# ============================================================


def leer_json(ruta):
    """El JSON de `ruta` o None. Nunca lanza."""
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return None


def leer_jsonl(ruta) -> list:
    """Las filas válidas de un JSONL; las rotas se saltan. Nunca lanza."""
    filas = []
    try:
        for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
            try:
                fila = json.loads(linea)
            except ValueError:
                continue
            if isinstance(fila, dict):
                filas.append(fila)
    except Exception:                               # noqa: BLE001
        return filas
    return filas


def la_foto_mas_reciente(carpeta=None):
    """La foto más reciente de `data/fotos/` que traiga `rival_squads`. Nunca lanza."""
    try:
        for ruta in sorted(Path(carpeta or FOTOS).glob("*.json"), reverse=True):
            foto = leer_json(ruta)
            if el_ancla(foto) is not None:
                return foto
    except Exception:                               # noqa: BLE001
        return None
    return None


def nuestra_plantilla_del_marcador(marcador):
    """
    La `plantilla` (ids) de la jornada del marcador vista MÁS TARDE, o None.

    Por `visto` y no por el id de la jornada: la J6 aplazada es la 5125 y
    se vio el 19/09; ordenando por id salía una plantilla de hace un mes.
    Nunca lanza.
    """
    try:
        jornadas = (marcador or {}).get("jornadas") or {}
        vistas = sorted(
            (str(j.get("visto") or j.get("escrito_en") or ""), clave)
            for clave, j in jornadas.items() if isinstance(j, dict)
        )
        for _visto, clave in reversed(vistas):
            plantilla = jornadas[clave].get("plantilla")
            if isinstance(plantilla, list) and plantilla:
                return [_int(j.get("id")) for j in plantilla if isinstance(j, dict)]
    except Exception:                               # noqa: BLE001
        return None
    return None


def _relativa(ruta) -> str:
    try:
        return str(Path(ruta).resolve().relative_to(RAIZ))
    except Exception:                               # noqa: BLE001
        return str(ruta)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="El marcador de la carrera (solo lectura).")
    parser.add_argument("--hoy", help="día de mercado de «hoy» (AAAA-MM-DD); por defecto, el último con precios")
    parser.add_argument("--escribir", action="store_true",
                        help=f"escribir además {_relativa(SALIDA)}")
    args = parser.parse_args(argv)

    hoy = None
    if args.hoy:
        try:
            hoy = date.fromisoformat(args.hoy)
        except ValueError:
            print(f"--hoy no es una fecha AAAA-MM-DD: {args.hoy!r}")
            return 2

    marcador = leer_json(MARCADOR)
    escaparate = leer_jsonl(ESCAPARATE)
    libro = leer_json(LIBRO_DE_PUJAS)
    bitacora = leer_jsonl(BITACORA)

    r = el_marcador(
        eventos=leer_json(TABLON),
        historial=leer_json(PRECIOS),
        libro_de_pujas=libro,
        foto=la_foto_mas_reciente(),
        otras_fichas=[escaparate, marcador, libro],
        hoy=hoy,
        bitacora=bitacora[-1] if bitacora else None,
        plantilla_del_marcador=nuestra_plantilla_del_marcador(marcador),
    )
    print(informe(r))

    if args.escribir:
        SALIDA.parent.mkdir(parents=True, exist_ok=True)
        SALIDA.write_text(json.dumps(para_json(r), ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        print(f"\nEscrito {_relativa(SALIDA)}")
    return 0 if r.get("available") else 1


if __name__ == "__main__":
    sys.exit(main())
