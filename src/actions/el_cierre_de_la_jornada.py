"""
EL CIERRE DE LA JORNADA (12/10/2026)

POR QUE EXISTE

    El dueño, 12/10: «tú fichas jugadores mejores cada día y gente que
    va a subir; luego, antes del inicio de jornada, se mira el
    calendario, se decide el mejor XI y se vende a los que falten para
    estar en positivo». Empezar una ronda con el saldo en rojo son 0
    puntos para el once ENTERO.

    Ese cierre no lo hace nadie (mapa de la solvencia del 12/10):

        · `solvency_clock` solo calcula y enseña (ESTE MODULO NO VENDE).
          El reloj estricto de v10 (v10_full_autonomous_live.py:341-355)
          no ve las pujas vivas: el 12/10 a las 14:07 decia SIN_DEUDA
          con 659.783 € de saldo mientras la orden tenia pujados
          3.777.000 + 4.989.000 y la ronda 1.101.000.
        · Cada vendedor (orquestador, orden, ronda, chollos, mejora)
          cuenta la caja a su manera y desde la foto de antes de la
          vuelta, y ninguno mira el calendario.
        · La plantilla es de 11 justos: vender a quien no toca deja un
          hueco en el once.

    Y el reloj de las ofertas es estrecho (J9: primer partido el
    viernes 16/10 a las 21:00; el plazo del dueño, T-6 h, las 14:45).
    Vender solo se puede aceptando una oferta del Computer, y esa
    oferta solo nace para quien se publico ANTES de un reset de las
    07:00 (nace a las 07:03-07:09 y vive hasta el siguiente). El ultimo
    reset antes de un partido de las 21:00 es el de las 07:00 de ese
    mismo dia, y la primera vuelta que puede cobrar es la de las 07:15.
    Por eso se PUBLICA pronto (desde `HORAS_CIERRE`) y se COBRA cuando
    hay oferta.

LA REGLA

    1. CUANDO, y EL PLAZO DE LA CAJA. La proxima ronda de Biwenger de
       CUALQUIER clase (`la_proxima_jornada`: un adelantado o un
       aplazado que va aparte es su propia ronda, con su propio control
       del saldo) empieza dentro de `HORAS_CIERRE` (64 h), no hay
       ninguna jugandose y se puede escribir (la zona de silencio de
       04:45-07:00 solo deja a las vueltas de 04:45, 04:50 y 07:15).
       Esa ronda es el PLAZO: si la proxima es un aplazado (la J6
       Levante-Athletic del 21/10), la caja tiene que estar en >= 0 a
       SU hora, aunque el once se elija para la siguiente principal.
    2. EL ONCE, el de la proxima ronda PRINCIPAL (`principal` en
       `el_calendario_de_puntos.las_rondas`). Un aplazado ('Jornada 6
       (aplazada)') lo puntua Biwenger con el once que habia cuando
       empezo su jornada (la regla del dueño): no se elige once para el
       ni pesa en el xP. El xP de la ronda del once y el de quedarse (3
       rondas) salen SOLO de rondas principales. Con TODA la plantilla
       (lo de la ronda y los chollos tambien es plantilla): xP con el
       rival delante (`el_calendario_de_puntos.xp_jugador`, tasa
       encogida hacia su tramo y factores sede x rival). Formaciones,
       las de `lineup_engine.FORMATIONS`. Yamal (los intocables de la
       orden) entra siempre que este sano. Fuera los que no esten 'ok'
       o 'warned' y los que ya se van (su relevo de la orden o de la
       mejora ya esta dentro).
       Lo de la ronda o los chollos que entra en este once se ADOPTA:
       sale de sus libros (los mismos ficheros y el mismo formato que
       usa la adopcion de la mejora del once) y queda en el plan
       (`adoptados`). Si no, la ronda lo malvenderia a menos de 20 h y
       los chollos en cuanto cubriera su coste, y el once se quedaria
       corto despues de que el cierre vendiera al banquillo contando
       con el. PERO (13/10/2026) solo si la caja al empezar la ronda,
       tras las pujas retiradas y las ventas elegidas (4), queda en
       >= 0, y si el jugador esta TAMBIEN en el once escrito
       (`status.lineup.players`). Porque el adoptado ya no lo vende
       nadie (el cierre no vende a nadie de su once) y al titular
       escrito al que desplaza tampoco: con la caja en rojo, su coste se
       quedaba dentro y la ronda empezaba en rojo (0 puntos para el once
       entero). Si no se cumple, no se adopta (la ronda o los chollos lo
       siguen vendiendo como tenian pensado) y el plan dice por que
       (`no_adoptados`).
    3. LA CAJA al empezar la ronda del plazo = saldo - TODAS nuestras
       pujas vivas a su importe entero (cualquiera se puede ganar en el
       reset) - lo pujado con exito en esta vuelta + lo cobrado en esta
       vuelta. Nada mas: ni premio de la jornada ni ventas pendientes.
       Si da >= 0, solo se publica (5) y se para.
    4. EN ROJO. Primero la palanca barata: a menos de `HORAS_SIN_TIEMPO`
       (40 h) se retiran las pujas vivas de la ronda y de los chollos
       (se resolverian en el ultimo reset, sin tiempo de revender), la
       mas grande primero, hasta volver a >= 0. Nunca la de un
       protegido, la de un `fichar` de la orden ni la del libro de la
       mejora, aunque su clave siga en el libro de los chollos (la
       orden la sustituye en el mismo jugador y a menos de 40 h ya no
       la vuelve a poner). Si sigue en rojo, se vende: candidatos =
       plantilla - el once - Yamal (por su nombre, siempre, este como
       este la orden) - protegidos - los TITULARES DEL ONCE ESCRITO
       (`status.lineup.players`) salvo que esten 'injured' o
       'sanctioned' (fuera seguro: un 'doubt' del once no se vende
       nunca, aunque el once del cierre lo siente) - los que ya vende
       la orden (`vender_si_ficha`) o la mejora - lo vendido en esta
       vuelta. Los de la orden o la mejora son suyos SOLO mientras su
       relevo llega (13/10/2026): esta en la plantilla, tiene puja viva
       nuestra o (la orden) sigue en el mercado del Computer. Perdida
       la puja por el relevo, nadie los vende y vuelven a ser del
       cierre. Se elige lo que cubre el deficit (al 95 % de su valor)
       perdiendo menos puntos de quedarse (xP de las 3 proximas rondas
       principales): con hasta `EXACTO_HASTA` (15) candidatos, el
       minimo EXACTO (todos los subconjuntos; a igual perdida, el que
       menos se pasa); con mas, voraz por puntos por euro, luego se
       quita a quien sobre (y si uno solo cubre perdiendo menos, ese).
       Si ni todos cubren, se venden todos y FALTA con el importe (los
       cambios del once son cosa de la mejora: aqui no se vende a nadie
       del once).
    5. LAS ESCRITURAS. PONER_A_LA_VENTA a su valor a todo candidato que
       no este publicado, ni en la foto ni en esta vuelta (tampoco lo
       que acaba de publicar el escaparate: su precio es suyo). No saca
       a nadie del once y hace nacer la oferta del proximo reset.
       ACEPTAR_OFERTA_DEL_COMPUTER para los elegidos si la oferta llega
       al 90 % de su valor, o la que haya a menos de `HORAS_SOLVENCIA`
       (20 h). Nunca a uno del once, ni a un titular escrito sano o en
       duda, ni a un protegido, ni a Yamal. Una escritura por jugador y
       vuelta.
    6. EL PLAN se publica en `data/trading/el_cierre.json` (la ronda del
       once, el plazo, el once, lo adoptado, a quien se vende, el
       deficit, lo que falta, las pujas retiradas y la hora), para que
       otros lo lean. Encendido, se publica SIEMPRE: fuera de la
       ventana y tambien si algo falla (activo False y el error), para
       que nadie lea uno viejo.

LOS `conservar`

    El modelo del dueño: «se vende a los que falten para estar en
    positivo» (12/10), y publicar no es vender: «podemos estar en
    negativo toda la semana mientras publiquemos a nuestros jugadores
    para tener liquido». Un `conservar` se publica como cualquiera y
    se le puede aceptar una oferta, pero SOLO si no es titular del once
    escrito (la regla de los titulares de 4; la orden, que vende como
    ultimo recurso, va por su cuenta). Lo que no se publica nunca son
    los protegidos (`proteger` y `fichar`) y Yamal.

QUE NO HACE

    No compra, no sube pujas, no pone el once (SAVE_LINEUP es del
    orquestador) y no vende a nadie del once: si el banquillo no llega,
    lo dice (FALTA) y lo arregla la mejora o el dueño. Sin once escrito
    en el panel, el que esta en duda (o sin estado) tampoco se vende.

    El adoptado de la ronda o los chollos (en su once) sale de sus
    libros, pero SIGUE PUBLICADO: Biwenger no tiene «quitar de la venta»
    en el cliente de escritura. La ronda y los chollos ya no lo venden;
    los vendedores del orquestador que no leen `el_cierre.json`, si
    podrian aceptar su oferta (el mismo hueco que la adopcion de la
    mejora del once). Con la caja proyectada en rojo, o fuera del once
    escrito, no se adopta a nadie (2).

    No cuenta como entrada el premio de la jornada ni lo que daran las
    ventas de la orden o de la mejora: al empezar la ronda solo vale
    lo cobrado.

    Lo escrito antes en la vuelta lo ve casi todo: las escrituras del
    orquestador y del competitivo refrescan la foto
    (`autopilot.refresh_snapshot`), las de compra y salida de v10 se
    verifican con otra foto antes de la orden, el carril, los chollos y
    la ronda, y las `hechas` de la orden, la ronda y los chollos, las
    pujas del carril, las retiradas y lo que publico el escaparate
    estan en el estado de v10. Lo que la mejora del once pujo, cobro y
    publico en esta vuelta sale de SU fichero de la vuelta
    (`VUELTA_MEJORA`: {run_id, generated_at, hechas}, 13/10/2026) y
    cuenta como las `hechas` de v10, solo si es de ESTA vuelta (el
    mismo `GITHUB_RUN_ID`; si falta alguno de los dos, escrito a
    `VUELTA_VIEJA_MINUTOS` o menos de ahora). El libro de la mejora ya
    no da pujas: una puja perdida en el reset no cuenta nunca. Lo que
    puede faltar lo trae la foto de la vuelta siguiente: una puja de la
    subasta del reset sin foto de verificacion detras.

    Corre DESPUES del panel (necesita la titularidad y el once
    escrito), como paso propio del workflow y DESPUES de la mejora del
    once (lo que pujo y cobro sale de su fichero de la vuelta, y su
    libro ya esta limpio de pujas perdidas):
    `python -m src.actions.el_cierre_de_la_jornada`. Nace APAGADO:
    `BORDALAS_EL_CIERRE_DE_LA_JORNADA`. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_EL_CIERRE_DE_LA_JORNADA"
RAIZ = Path(__file__).parents[2]
PLAN = RAIZ / "data" / "trading" / "el_cierre.json"

# Lo que hizo la mejora del once en ESTA vuelta (13/10/2026): lo escribe
# ella al acabar, encendida, siempre (= `la_mejora_del_once.VUELTA_MEJORA`):
# {"run_id": GITHUB_RUN_ID, "generated_at": ISO UTC, "hechas": [...]}.
VUELTA_MEJORA = RAIZ / "data" / "trading" / "la_mejora_vuelta.json"

# Sin run_id que casar, la vuelta de la mejora vale si se escribio a
# 45 min o menos de ahora (= `la_mejora_del_once.VUELTA_VIEJA_MINUTOS`).
VUELTA_VIEJA_MINUTOS = 45

# Desde cuando se cierra: 64 h, las mismas que `HORAS_CON_DEUDA` de la
# mejora del once. Para un partido del viernes a las 21:00 es el martes
# a las 05:00: la primera vuelta que escribe es la de las 07:15 del
# martes, y lo publicado entonces recibe oferta en los resets del
# miercoles, jueves y viernes (tres oportunidades de cobrar).
HORAS_CIERRE = 64

# A menos de 40 h toda puja viva se resuelve en el ultimo reset antes
# del partido (las 40 h de `la_orden_del_gestor.HORAS_SIN_FICHAR`): lo
# que se gane ahi no recibe oferta hasta despues del partido.
HORAS_SIN_TIEMPO = 40

# A menos de 20 h, en rojo, se acepta la oferta que haya (las de la
# ronda y la mejora: `HORAS_SOLVENCIA`). Las 07:15 del viernes de un
# partido a las 21:00 caen a 13,75 h.
HORAS_SOLVENCIA = 20

VENTA = 0.95                    # lo que se espera de la oferta del Computer
SUELO = 0.90                    # lo minimo que se acepta antes de las 20 h
HORIZONTE_DE_QUEDARSE = 3       # rondas PRINCIPALES que pesan para quedarse a alguien
SANOS = frozenset({"ok", "warned"})
INTOCABLES = frozenset({"yamal", "lamine yamal"})   # = la_orden_del_gestor.INTOCABLES

# Un titular del once escrito solo se puede vender si esta fuera seguro.
# 'doubt' no lo esta: puede jugar, y venderlo deja el once en 10.
FUERA_SEGURO = frozenset({"injured", "sanctioned"})

# Hasta 15 candidatos se busca el reparto exacto (2^15 = 32.768
# combinaciones, nada); con mas, el voraz.
EXACTO_HASTA = 15

# Las rondas que se piden al calendario para sacar de ellas las 3
# principales: entre medias puede haber adelantados y aplazados.
RONDAS_A_MIRAR = 12

# Copia de `lineup_engine.FORMATIONS` por si no se puede importar.
_FORMACIONES = {
    "3-4-3": {1: 1, 2: 3, 3: 4, 4: 3},
    "3-5-2": {1: 1, 2: 3, 3: 5, 4: 2},
    "4-3-3": {1: 1, 2: 4, 3: 3, 4: 3},
    "4-4-2": {1: 1, 2: 4, 3: 4, 4: 2},
    "4-5-1": {1: 1, 2: 4, 3: 5, 4: 1},
    "5-3-2": {1: 1, 2: 5, 3: 3, 4: 2},
    "5-4-1": {1: 1, 2: 5, 3: 4, 4: 1},
}


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _num(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        salida = float(x)
    except (TypeError, ValueError, OverflowError):
        return defecto
    if salida != salida or salida in (float("inf"), float("-inf")):
        return defecto
    return salida


def _dict(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    try:
        if isinstance(x, dict):
            x = list(x.values())
        return [f for f in (x or []) if isinstance(f, dict)]
    except Exception:                               # noqa: BLE001
        return []


def _ids(x) -> set:
    try:
        return {i for i in (_int(v) for v in (x or [])) if i is not None}
    except Exception:                               # noqa: BLE001
        return set()


def _nombre(ficha) -> str:
    try:
        return str(_dict(ficha).get("name") or "").strip().lower()
    except Exception:                               # noqa: BLE001
        return ""


def _importe(puja) -> int:
    """El importe de una puja: `{"amount"}` o el numero suelto."""
    if isinstance(puja, dict):
        return _int(puja.get("amount"), 0) or 0
    return _int(puja, 0) or 0


def _formaciones() -> dict:
    try:
        from src.analysis.lineup_engine import FORMATIONS

        if isinstance(FORMATIONS, dict) and FORMATIONS:
            return FORMATIONS
    except Exception:                               # noqa: BLE001
        pass
    return _FORMACIONES


# ============================================================
# 1. CUANDO
# ============================================================

def la_ventana(ahora, calendario=None) -> dict:
    """
    `{"horas", "en_curso", "puede_escribir"}` para `ahora`: horas al
    inicio de la proxima ronda (`la_proxima_jornada`), si hay una
    jugandose y si la zona de silencio deja escribir. `calendario` es un
    dict ya leido o una ruta (por defecto el de los chollos). Sin
    saberlo: horas None, en curso True, sin escribir. Nunca lanza.
    """

    ventana = {"horas": None, "en_curso": True, "puede_escribir": False}
    try:
        from src.actions.los_chollos import CALENDARIO, _puede_escribir
        from src.analysis.la_proxima_jornada import (
            horas_al_proximo_cierre, jornada_en_curso,
        )

        ruta = CALENDARIO if calendario is None else calendario
        horas = horas_al_proximo_cierre(ahora, ruta)
        ventana["horas"] = None if horas is None or isinstance(horas, bool) else float(horas)
        ventana["en_curso"] = bool(jornada_en_curso(ahora, ruta))
        ventana["puede_escribir"] = bool(_puede_escribir(ahora))
    except Exception:                               # noqa: BLE001
        pass
    return ventana


def por_que_no(horas, en_curso, puede_escribir):
    """None si el cierre toca en esta vuelta. Si no, el motivo. Sin
    horas es SIN_CALENDARIO aunque `en_curso` diga True (`la_ventana`
    y `jornada_en_curso` lo dicen por precaucion cuando no hay rondas)."""
    try:
        if not puede_escribir:
            return "ZONA_DE_SILENCIO"
        horas = _num(horas)
        if horas is None:
            return "SIN_CALENDARIO"
        if en_curso:
            return "JORNADA_EN_CURSO"
        if horas > HORAS_CIERRE or horas <= 0:
            return "FUERA_DE_LA_VENTANA"
        return None
    except Exception:                               # noqa: BLE001
        return "SIN_CALENDARIO"


# ============================================================
# 2. EL ONCE
# ============================================================

def el_mejor_once(jugadores, intocables=INTOCABLES) -> dict:
    """
    El mejor once de `jugadores` ([{id, name, position, xp}], ya solo
    los que pueden jugar). Por formacion, los de mas xP de cada puesto;
    gana la que llena mas huecos y, a igual, la que suma mas xP (y a
    igual, la primera de la lista). Los intocables entran primero en su
    puesto. Pura; con basura, el once vacio.
    """

    vacio = {"formacion": None, "ids": [], "puntos": 0.0, "lleno": 0}
    try:
        intocables = {str(n).strip().lower() for n in (intocables or ())}
        por_puesto: dict = {}
        for j in _lista(jugadores):
            pid = _int(j.get("id"))
            puesto = _int(j.get("position"))
            if pid is None or puesto not in (1, 2, 3, 4):
                continue
            xp = _num(j.get("xp"), 0.0) or 0.0
            forzado = _nombre(j) in intocables
            por_puesto.setdefault(puesto, []).append((not forzado, -xp, pid, xp))
        for lista in por_puesto.values():
            lista.sort()

        mejor, clave_mejor = vacio, None
        for indice, (nombre, huecos) in enumerate(_formaciones().items()):
            ids, puntos, lleno = [], 0.0, 0
            for puesto, n in huecos.items():
                for _, _, pid, xp in por_puesto.get(_int(puesto), [])[:max(_int(n, 0) or 0, 0)]:
                    ids.append(pid)
                    puntos += xp
                    lleno += 1
            clave = (lleno, round(puntos, 9), -indice)
            if clave_mejor is None or clave > clave_mejor:
                clave_mejor = clave
                mejor = {"formacion": nombre, "ids": ids, "puntos": round(puntos, 3),
                         "lleno": lleno}
        return mejor
    except Exception:                               # noqa: BLE001
        return vacio


# ============================================================
# 3. LA CAJA
# ============================================================

def la_caja(saldo, pujas=None, vendidos=None) -> int:
    """
    La caja al empezar la ronda: saldo - todas nuestras pujas vivas a su
    importe entero + lo cobrado en esta vuelta. `pujas` es
    `{player_id: {"amount"}}` (o el importe suelto), ya con lo pujado y
    lo retirado en esta vuelta; `vendidos`, `{player_id: importe}`.
    """
    try:
        caja = _int(saldo, 0) or 0
        caja -= sum(_importe(p) for p in _dict(pujas).values())
        caja += sum(_int(v, 0) or 0 for v in _dict(vendidos).values())
        return caja
    except Exception:                               # noqa: BLE001
        return _int(saldo, 0) or 0


# ============================================================
# 4. A QUIEN SE VENDE
# ============================================================

def _el_minimo_exacto(vendibles, deficit) -> list:
    """
    De `vendibles` (ya limpios y ordenados), el subconjunto que cubre
    `deficit` perdiendo menos puntos de quedarse; a igual perdida, el
    que menos se pasa del deficit; luego el de menos jugadores. Mira
    las 2^n combinaciones (n <= `EXACTO_HASTA`), cada una sumando a la
    de antes un solo jugador. [] si ninguna cubre.
    """
    n = len(vendibles)
    cobros = [c["cobro"] for c in vendibles]
    perdidas = [c["quedarse"] for c in vendibles]
    sumas, pierde = [0] * (1 << n), [0.0] * (1 << n)
    mejor, clave_mejor = 0, None
    for mascara in range(1, 1 << n):
        bajo = mascara & -mascara
        i = bajo.bit_length() - 1
        antes = mascara ^ bajo
        sumas[mascara] = sumas[antes] + cobros[i]
        pierde[mascara] = pierde[antes] + perdidas[i]
        if sumas[mascara] < deficit:
            continue
        clave = (round(pierde[mascara], 9), sumas[mascara] - deficit,
                 bin(mascara).count("1"), mascara)
        if clave_mejor is None or clave < clave_mejor:
            mejor, clave_mejor = mascara, clave
    return [c for i, c in enumerate(vendibles) if mejor >> i & 1]


def a_quien_vender(candidatos, deficit) -> tuple:
    """
    `(elegidos, falta)`. De `candidatos` ([{id, cobro, quedarse}]: lo que
    se espera cobrar y los puntos que se pierden), los que cubren
    `deficit` perdiendo menos puntos.

    Con hasta `EXACTO_HASTA` candidatos, el minimo EXACTO: de todas las
    combinaciones que cubren, la que menos puntos pierde y, a igual, la
    que menos se pasa del deficit. Con mas, el voraz: primero el que
    menos puntos pierde por euro (a igual, el que menos pierde y el que
    mas cobra), hasta cubrir; luego se quita, del que mas pierde al que
    menos, a quien no haga falta; y si un solo jugador cubre perdiendo
    menos que todo eso, solo el. Si ni todos cubren, todos y `falta` =
    lo que queda. Pura; con basura, ([], deficit).
    """

    try:
        deficit = _int(deficit, 0) or 0
        if deficit <= 0:
            return [], 0
        vendibles = []
        for c in _lista(candidatos):
            cobro = _int(c.get("cobro"), 0) or 0
            if _int(c.get("id")) is None or cobro <= 0:
                continue
            quedarse = max(_num(c.get("quedarse"), 0.0) or 0.0, 0.0)
            vendibles.append({**c, "id": _int(c.get("id")), "cobro": cobro,
                              "quedarse": quedarse})
        vendibles.sort(key=lambda c: (c["quedarse"] / c["cobro"], c["quedarse"],
                                      -c["cobro"], c["id"]))

        total = sum(c["cobro"] for c in vendibles)
        if total < deficit:
            return vendibles, deficit - total
        if len(vendibles) <= EXACTO_HASTA:
            return _el_minimo_exacto(vendibles, deficit), 0

        elegidos, suma = [], 0
        for c in vendibles:
            if suma >= deficit:
                break
            elegidos.append(c)
            suma += c["cobro"]
        if suma < deficit:
            return elegidos, deficit - suma

        for c in sorted(elegidos, key=lambda c: (-c["quedarse"], c["cobro"], c["id"])):
            if suma - c["cobro"] >= deficit:
                elegidos.remove(c)
                suma -= c["cobro"]

        # El voraz por euro falla con un deficit pequeño: con 200.000 €
        # que cubrir se lleva al de menos puntos POR EURO (4 M, 1,85
        # puntos) aunque uno de 500.000 € y 0,92 puntos baste solo. Si
        # un solo jugador cubre perdiendo menos, ese.
        solos = [c for c in vendibles if c["cobro"] >= deficit]
        if solos:
            solo = min(solos, key=lambda c: (c["quedarse"], c["cobro"], c["id"]))
            if solo["quedarse"] < sum(c["quedarse"] for c in elegidos):
                return [solo], 0
        return elegidos, 0
    except Exception:                               # noqa: BLE001
        return [], _int(deficit, 0) or 0


# ============================================================
# 5. LA DECISION (pura)
# ============================================================

def _xp(ctx, ficha, n) -> float:
    """xP de las `n` proximas rondas; 0 si no se sabe (sin tasa o sin
    titularidad: no suma al once ni pesa para quedarse)."""
    try:
        from src.analysis.el_calendario_de_puntos import xp_jugador

        xp = xp_jugador(ctx, ficha, ficha.get("starter_probability"), n)
        return float(xp) if xp is not None else 0.0
    except Exception:                               # noqa: BLE001
        return 0.0


def _la_ronda(r) -> dict | None:
    if not isinstance(r, dict):
        return None
    return {"label": r.get("label"), "start": r.get("start"),
            "principal": bool(r.get("principal"))}


def decidir(
    *, plantilla, ctx, horas, en_curso=False, puede_escribir=True, saldo,
    pujas=None, vendidos=None, ofertas=None, en_venta=frozenset(),
    especulativas=frozenset(), intocables=INTOCABLES, protegidos=frozenset(),
    no_vender=frozenset(), se_van=frozenset(), once_escrito=frozenset(),
    no_retirar=frozenset(), inventario=frozenset(),
) -> dict:
    """
    Que hace el cierre en esta vuelta. Pura: ni red, ni disco, ni reloj.

        plantilla      [{id, name, position, team_id, points, played,
                         price, status, starter_probability}] TODA la
                       plantilla (sin lo vendido en esta vuelta)
        ctx            `el_calendario_de_puntos.contexto` (rondas, duros,
                       tramos, ids). Sus rondas, de CUALQUIER clase: la
                       primera es el plazo de la caja; el once y el xP
                       salen solo de las principales
        horas          horas al inicio de la proxima ronda (cualquiera)
        saldo          el saldo de la foto de la vuelta
        pujas          {player_id: {"offer_id", "amount"}} nuestras pujas
                       vivas, ya con lo pujado y retirado en esta vuelta
                       (lo de esta vuelta, con offer_id None)
        vendidos       {player_id: importe} cobrado en esta vuelta
        ofertas        {player_id: {"offer_id", "amount"}} del Computer
        en_venta       publicados (la foto, esta vuelta y el escaparate)
        especulativas  los de los libros de la ronda y los chollos
        protegidos     `proteger` y `fichar` de la orden: ni se publican
                       ni se les retira la puja
        no_vender      los que vende la orden (`vender_si_ficha`) o la
                       mejora: suyos, no se tocan
        se_van         los de `no_vender` cuyo relevo ya esta dentro:
                       tampoco juegan
        once_escrito   los titulares del once que hay escrito
                       (`status.lineup.players`): no se venden ni se
                       publican salvo que esten fuera seguro
        no_retirar     pujas que no son del cierre (los `fichar` de la
                       orden, las del libro de la mejora)
        inventario     lo de la ronda y los chollos que es nuestro: si
                       entra en el once, se adopta (`adoptar`) solo con
                       la caja proyectada en >= 0 y si esta tambien en
                       `once_escrito`; si no, `no_adoptados` y por que
    """

    salida = {
        "activo": False, "motivo": None, "horas": None, "ronda": None, "plazo": None,
        "once": {"formacion": None, "ids": [], "puntos": 0.0, "lleno": 0, "jugadores": []},
        "caja": None, "caja_tras_cancelar": None, "deficit": 0, "cancelar": [],
        "vender": [], "falta": 0, "candidatos": [], "acciones": [], "adoptar": [],
        "no_adoptados": [], "caja_proyectada": None, "titulares_que_no_se_venden": [],
    }
    try:
        salida["horas"] = _num(horas)
        motivo = por_que_no(horas, en_curso, puede_escribir)
        if motivo:
            salida["motivo"] = motivo
            return salida
        horas = _num(horas)
        saldo = _int(saldo)
        if saldo is None:
            salida["motivo"] = "SIN_SALDO"
            return salida

        # Las rondas: la primera, de la clase que sea, es el plazo de la
        # caja. El once es el de la primera PRINCIPAL y el xP (de la ronda
        # y el de quedarse) sale solo de las principales: un aplazado se
        # puntua con el once de cuando empezo su jornada.
        ctx = _dict(ctx)
        rondas = [r for r in (ctx.get("rondas") or []) if isinstance(r, dict)]
        principales = [r for r in rondas if r.get("principal")]
        ctx = {**ctx, "rondas": principales}
        salida["plazo"] = _la_ronda(rondas[0]) if rondas else None
        salida["ronda"] = _la_ronda(principales[0]) if principales else None

        # Yamal, por su nombre, nunca se publica ni se vende, este como
        # este la orden (apagada, caducada o con `yamal_por_lesion`).
        intocables = {str(n).strip().lower() for n in (intocables or ())}
        nunca = intocables | set(INTOCABLES)
        protegidos, no_vender, se_van = _ids(protegidos), _ids(no_vender), _ids(se_van)
        once_escrito, inventario = _ids(once_escrito), _ids(inventario)
        especulativas = _ids(especulativas) - protegidos - _ids(no_retirar)
        vendidos = {_int(k): v for k, v in _dict(vendidos).items() if _int(k) is not None}
        ofertas = {_int(k): v for k, v in _dict(ofertas).items()
                   if _int(k) is not None and isinstance(v, dict)}
        en_venta = _ids(en_venta)
        pujas = {_int(k): v for k, v in _dict(pujas).items() if _int(k) is not None}

        # La plantilla, una ficha por jugador, sin lo ya vendido.
        fichas, vistos = [], set()
        for f in _lista(plantilla):
            pid = _int(f.get("id"))
            if pid is None or pid in vistos or pid in vendidos:
                continue
            vistos.add(pid)
            fichas.append({**f, "id": pid,
                           "xp": _xp(ctx, f, 1),
                           "quedarse": _xp(ctx, f, HORIZONTE_DE_QUEDARSE),
                           "valor": _int(f.get("price"), 0) or 0})

        # 2. EL ONCE de la ronda principal.
        pueden = [f for f in fichas
                  if str(f.get("status") or "").strip().lower() in SANOS
                  and f["id"] not in se_van]
        once = el_mejor_once(pueden, intocables)
        xi = set(once["ids"])
        por_id = {f["id"]: f for f in fichas}
        salida["once"] = {**once, "jugadores": [
            {"id": pid, "name": por_id[pid].get("name"),
             "position": por_id[pid].get("position"), "xp": round(por_id[pid]["xp"], 3)}
            for pid in once["ids"] if pid in por_id
        ]}

        # 3. LA CAJA.
        caja = la_caja(saldo, pujas, vendidos)
        salida["caja"] = caja

        # 4. La palanca barata: retirar lo especulativo que ya no da tiempo.
        acciones, cancelar, caja_tras = [], [], caja
        if caja < 0 and horas < HORAS_SIN_TIEMPO:
            vivas = sorted(
                ((_importe(p), pid, _int(_dict(p).get("offer_id")))
                 for pid, p in pujas.items() if pid in especulativas),
                key=lambda t: (-t[0], t[1]),
            )
            for importe, pid, offer_id in vivas:
                if caja_tras >= 0:
                    break
                if not offer_id or importe <= 0:
                    continue
                cancelar.append(pid)
                caja_tras += importe
                acciones.append({
                    "accion": "CANCELAR_PUJA", "player_id": pid, "offer_id": offer_id,
                    "importe": importe, "cierre": True,
                    "motivo": (f"en rojo a {horas:.1f} h: se resolveria en el ultimo "
                               "reset, sin tiempo de revenderlo"),
                })
        salida["cancelar"] = cancelar
        salida["caja_tras_cancelar"] = caja_tras
        deficit = max(0, -caja_tras)
        salida["deficit"] = deficit

        # Los candidatos: fuera del once, ni Yamal, ni protegidos, ni lo
        # que vende otro, ni un titular del once escrito que pueda jugar.
        candidatos, titulares = [], []
        for f in fichas:
            pid = f["id"]
            if (pid in xi or _nombre(f) in nunca or pid in protegidos
                    or pid in no_vender):
                continue
            estado = str(f.get("status") or "").strip().lower()
            if pid in once_escrito and estado not in FUERA_SEGURO:
                titulares.append(pid)
                continue
            # Sin once escrito en el panel no se sabe quien es titular: el
            # que esta en duda (o sin estado) puede serlo, y no se vende.
            if not once_escrito and estado not in FUERA_SEGURO | {"ok", "warned"}:
                titulares.append(pid)
                continue
            candidatos.append({"id": pid, "name": f.get("name"), "valor": f["valor"],
                               "cobro": int(f["valor"] * VENTA),
                               "quedarse": round(f["quedarse"], 3)})
        salida["titulares_que_no_se_venden"] = sorted(titulares)

        elegidos, falta = a_quien_vender(candidatos, deficit)
        vender = {c["id"] for c in elegidos}
        salida["vender"] = [c["id"] for c in elegidos]
        salida["falta"] = falta
        salida["candidatos"] = [{**c, "elegido": c["id"] in vender} for c in candidatos]

        # LA ADOPCION (13/10/2026), despues de la caja y las ventas. El
        # adoptado sale de los libros de la ronda y los chollos (ya no lo
        # venden) y el cierre no vende a nadie de su once; si el once
        # escrito sigue con el titular al que desplaza, tampoco se vende a
        # ese: su coste se queda en la caja. Solo con la caja al empezar la
        # ronda (tras retirar pujas y con las ventas elegidas cobradas) en
        # >= 0 y con el jugador tambien en el once escrito. Si no, la
        # ronda o los chollos lo siguen vendiendo como tenian pensado.
        proyectada = caja_tras + sum(c["cobro"] for c in elegidos)
        salida["caja_proyectada"] = proyectada
        adoptar, no_adoptados = [], []
        for pid in sorted(xi & inventario):
            if proyectada < 0:
                no_adoptados.append({"player_id": pid, "motivo": (
                    f"la caja al empezar la ronda queda en {proyectada} con lo que se "
                    "vende: su libro lo sigue vendiendo")})
            elif pid not in once_escrito:
                no_adoptados.append({"player_id": pid, "motivo": (
                    "no esta en el once escrito: su libro lo sigue vendiendo")})
            else:
                adoptar.append(pid)
        salida["adoptar"] = adoptar
        salida["no_adoptados"] = no_adoptados

        # 5. LAS ESCRITURAS: una por jugador. Cobrar a los elegidos;
        # publicar a todo candidato que no lo este.
        ventas = []
        for c in sorted(candidatos, key=lambda c: (c["id"] not in vender, c["id"])):
            pid, valor = c["id"], c["valor"]
            oferta = ofertas.get(pid)
            if pid in vender and oferta:
                importe = _int(oferta.get("amount"), 0) or 0
                suelo = 0 if horas < HORAS_SOLVENCIA else int(valor * SUELO)
                if importe > 0 and importe >= suelo and _int(oferta.get("offer_id")):
                    ventas.append({
                        "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                        "nombre": c.get("name"), "offer_id": _int(oferta.get("offer_id")),
                        "importe": importe, "suelo": suelo, "valor": valor, "cierre": True,
                    })
                    continue
            if pid not in en_venta and valor > 0:
                ventas.append({
                    "accion": "PONER_A_LA_VENTA", "player_id": pid, "nombre": c.get("name"),
                    "precio": valor, "elegido": pid in vender, "cierre": True,
                })
            elif pid in vender:
                ventas.append({
                    "accion": "NADA", "player_id": pid, "nombre": c.get("name"),
                    "cierre": True,
                    "motivo": ("publicado; esperando una oferta del Computer de al "
                               f"menos el {int(SUELO * 100)} % de su valor"),
                })
        acciones.extend(ventas)
        salida["acciones"] = acciones
        salida["activo"] = True
        if caja_tras >= 0:
            salida["motivo"] = "EN_POSITIVO" if not cancelar else "EN_POSITIVO_RETIRANDO_PUJAS"
        elif falta:
            salida["motivo"] = "FALTA"
        else:
            salida["motivo"] = "EN_ROJO_SE_VENDE"
        return salida
    except Exception as error:                      # noqa: BLE001
        salida["activo"] = False
        salida["acciones"] = []
        salida["adoptar"] = []
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"
        return salida


# ============================================================
# 6. DE LOS FICHEROS DE LA VUELTA A LO QUE `decidir` ENTIENDE
# ============================================================

def lo_de_esta_vuelta(v10) -> dict:
    """
    Lo que esta vuelta ya escribio antes del cierre, del estado de v10
    (`data/trading/v10_full_autonomous_status.json`): las `hechas` con
    exito de la orden, la ronda y los chollos, las `retiradas` de la
    revision de pujas, las pujas del carril y lo que publico el
    escaparate (`escaparate.listed`: su precio es suyo y es una
    escritura de esta vuelta; el cierre no lo vuelve a publicar). La
    foto es de ANTES de todo eso.

        pujas       {player_id: importe} pujado
        canceladas  {player_id} retirado
        vendidos    {player_id: importe} cobrado
        listados    {player_id} publicado

    Nunca lanza.
    """

    vuelta = {"pujas": {}, "canceladas": set(), "vendidos": {}, "listados": set()}
    try:
        for clave, bloque in _dict(v10).items():
            if not isinstance(bloque, dict):
                continue
            for h in _lista(bloque.get("hechas")):
                if not h.get("exito"):
                    continue
                pid = _int(h.get("player_id"))
                if pid is None:
                    continue
                accion = h.get("accion")
                if accion == "PUJAR":
                    vuelta["pujas"][pid] = _int(h.get("importe"), 0) or 0
                    vuelta["canceladas"].discard(pid)
                elif accion == "CANCELAR_PUJA":
                    vuelta["canceladas"].add(pid)
                    vuelta["pujas"].pop(pid, None)
                elif accion == "ACEPTAR_OFERTA_DEL_COMPUTER":
                    vuelta["vendidos"][pid] = _int(h.get("importe"), 0) or 0
                elif accion == "PONER_A_LA_VENTA":
                    vuelta["listados"].add(pid)
            for r in _lista(bloque.get("retiradas")):
                pid = _int(r.get("player_id"))
                if r.get("exito") and pid is not None:
                    vuelta["canceladas"].add(pid)
                    vuelta["pujas"].pop(pid, None)
            if clave == "carril":
                for b in _lista(bloque.get("bids")):
                    pid = _int(b.get("player_id"))
                    if pid is not None and b.get("sent") and b.get("success") is not False:
                        vuelta["pujas"][pid] = _int(b.get("amount"), 0) or 0
            if clave == "escaparate":
                # En ensayo tampoco: lo que el escaparate quiere publicar
                # lleva su precio, y el cierre no se lo pisa.
                # Solo lo que de verdad se envio: con el escaparate
                # apagado (ESCAPARATE_APAGADO=1) la fila llega en seco
                # (sent False) y no hay precio que respetar.
                for fila in _lista(bloque.get("listed")):
                    pid = _int(fila.get("player_id"))
                    if (pid is not None and fila.get("sent")
                            and fila.get("success") is not False):
                        vuelta["listados"].add(pid)
    except Exception:                               # noqa: BLE001
        pass
    return vuelta


def las_pujas_vivas(foto, vuelta) -> dict:
    """
    Nuestras pujas al empezar la ronda: las de la foto, con lo pujado y
    lo retirado en esta vuelta encima (`vuelta`: lo de v10 y lo de la
    mejora del once, de su fichero de la vuelta). Lo de esta vuelta va
    sin `offer_id`: no se sabe y no se retira.

    El libro de la mejora ya no se mira (13/10/2026): lo que no esta en
    la foto ni en la plantilla es, casi siempre, una puja PERDIDA en el
    reset que la mejora aun no habia soltado, y contarla vendia al
    banquillo por un dinero que no se debe. Nunca lanza.
    """
    try:
        foto, vuelta = _dict(foto), _dict(vuelta)
        pujas = {}
        for pid, p in _dict(foto.get("nuestras_pujas")).items():
            if _int(pid) is not None:
                pujas[_int(pid)] = {"offer_id": _int(_dict(p).get("offer_id")),
                                    "amount": _importe(p)}
        for pid, importe in _dict(vuelta.get("pujas")).items():
            pujas[_int(pid)] = {"offer_id": None, "amount": _int(importe, 0) or 0}
        for pid in vuelta.get("canceladas") or ():
            pujas.pop(_int(pid), None)
        return pujas
    except Exception:                               # noqa: BLE001
        return {}


def la_vuelta_de_la_mejora(datos, ahora, run_id=None) -> tuple:
    """
    `(hechas, descartado)`: las `hechas` de la mejora del once en ESTA
    vuelta, de su fichero (`VUELTA_MEJORA`: {run_id, generated_at,
    hechas}), y None; o `([], motivo)` si no son de esta vuelta.

    Valen si su `run_id` es el de esta vuelta (`GITHUB_RUN_ID`); si
    falta alguno de los dos, si su `generated_at` esta a
    `VUELTA_VIEJA_MINUTOS` o menos de `ahora`. Las de otra vuelta ya
    estan en la foto (o se perdieron en el reset): contarlas otra vez
    restaria pujas que no existen y sumaria cobros que ya estan en el
    saldo. Pura, nunca lanza.
    """
    try:
        if not isinstance(datos, dict) or not datos:
            return [], "no hay vuelta de la mejora"
        suyo = datos.get("run_id")
        if run_id and suyo:
            if str(suyo) != str(run_id):
                return [], f"la vuelta de la mejora es de otra vuelta (run {suyo}, esta {run_id})"
            return _lista(datos.get("hechas")), None
        sello = datos.get("generated_at")
        if not sello:
            return [], "la vuelta de la mejora no trae hora"
        cuando = datetime.fromisoformat(str(sello).replace("Z", "+00:00"))
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=timezone.utc)
        minutos = (ahora - cuando).total_seconds() / 60
        if abs(minutos) > VUELTA_VIEJA_MINUTOS:
            return [], (f"la vuelta de la mejora es de hace {int(minutos)} min "
                        "(de otra vuelta)")
        return _lista(datos.get("hechas")), None
    except Exception as error:                      # noqa: BLE001
        return [], f"la vuelta de la mejora no se puede fechar: {type(error).__name__}"


def las_fichas(status, ids, estados=None, precios=None) -> list:
    """
    Una ficha por jugador de `ids` para `decidir`, de lo que haya: la
    plantilla del panel (`roster.players`: titularidad, estado, precio),
    `todaLaLiga.players` (equipo, puntos, partidos) y el escaparate del
    dia (titularidad de lo recien comprado). El estado, el del catalogo
    de la foto si lo trae; el precio, el de la foto. Nunca lanza.
    """
    try:
        status = _dict(status)
        roster = {_int(p.get("id")): p for p in _lista(_dict(status.get("roster")).get("players"))}
        liga = {_int(p.get("id")): p for p in _lista(_dict(status.get("todaLaLiga")).get("players"))}
        escaparate = {_int(p.get("id")): p for p in
                      _lista(_dict(status.get("libro_del_escaparate")).get("players"))}
        clasificacion = _dict(_dict(status.get("league_center")).get("laliga")).get("standings")
        estados, precios = _dict(estados), _dict(precios)

        def _casar(nombre):
            try:
                from src.analysis.el_calendario_de_puntos import casar_equipos

                return casar_equipos([nombre], clasificacion).get(nombre) if nombre else None
            except Exception:                       # noqa: BLE001
                return None

        fichas = []
        for pid in sorted(_ids(ids)):
            r, l, e = roster.get(pid) or {}, liga.get(pid) or {}, escaparate.get(pid) or {}
            jugados = l.get("played")
            if jugados is None and (r.get("played_home") is not None or r.get("played_away") is not None):
                jugados = (_int(r.get("played_home"), 0) or 0) + (_int(r.get("played_away"), 0) or 0)
            if jugados is None:
                jugados = e.get("played")
            puntos = next((x.get("points") for x in (l, r, e) if x.get("points") is not None), None)
            prob = next((x.get("starter_probability") for x in (r, e, l)
                         if x.get("starter_probability") is not None), None)
            estado = estados.get(pid) or r.get("status") or l.get("status") or e.get("status")
            fichas.append({
                "id": pid,
                "name": r.get("name") or l.get("name") or e.get("name"),
                "position": r.get("position") or l.get("position") or e.get("position"),
                "team_id": _int(l.get("team_id")) or _int(r.get("team_id")) or _casar(r.get("team_name")),
                "points": puntos, "played": jugados, "starter_probability": prob,
                "price": _int(precios.get(pid)) or _int(r.get("price")) or _int(l.get("price"))
                or _int(e.get("price")),
                "status": estado,
            })
        return fichas
    except Exception:                               # noqa: BLE001
        return []


def la_orden(orden, plantilla, ahora, pujas=None, mercado=None) -> dict:
    """
    Lo que pesa de la orden del gestor, si esta viva (encendida, sin
    caducar, valida): sus intocables y a quien vende (`vender_si_ficha`),
    con los que ya se van (su relevo esta dentro). Apagada o muerta,
    Yamal sigue intocable y no vende a nadie.

    SOLO MIENTRAS SU RELEVO LLEGA (13/10/2026): un `vender_si_ficha` es de
    la orden (`vende`) si su relevo (su `si_esta` y el general, si lo
    hay: la orden pide los dos) esta en la plantilla, tiene puja viva
    nuestra (`pujas`: las de la foto y las de esta vuelta) o sigue en el
    mercado del Computer (`mercado`: la orden puede volver a pujar; vacio
    o sin pasar es no saberlo, y vale). Perdida la puja por el relevo ante
    un rival, la orden no lo vende nunca (vive hasta el 30/11): dejarlo
    en `no_vender` lo congelaba. Sin relevo, la orden no lo vende. Nunca
    lanza.
    """
    salida = {"intocables": INTOCABLES, "vende": set(), "se_van": set()}
    try:
        from src.actions.la_orden_del_gestor import _intocables, activa as orden_activa, validar

        if not orden_activa() or validar(orden, ahora) is not None:
            return salida
        salida["intocables"] = _intocables(orden)
        plantilla = _ids(plantilla)
        pujas = _ids(pujas.keys() if isinstance(pujas, dict) else pujas)
        mercado = _ids(mercado.keys() if isinstance(mercado, dict) else mercado)

        def _llega(relevo):
            return relevo in plantilla or relevo in pujas or not mercado or relevo in mercado

        venta = _dict(orden.get("vender_si_ficha"))
        general = _int(venta.get("si_esta"))
        for j in _lista(venta.get("jugadores")):
            pid = _int(j.get("player_id"))
            if pid is None:
                continue
            relevos = {r for r in (general, _int(j.get("si_esta"))) if r is not None}
            if not relevos or not all(_llega(r) for r in relevos):
                continue
            salida["vende"].add(pid)
            if all(r in plantilla for r in relevos):
                salida["se_van"].add(pid)
    except Exception:                               # noqa: BLE001
        pass
    return salida


def la_mejora(libro_mejora, plantilla, pujas=None) -> dict:
    """Los que salen por la mejora del once (`sale` de su libro), y los
    que ya se van (el que entra ya esta en la plantilla). Con `pujas`
    (nuestras pujas vivas, 13/10/2026), el cambio cuenta solo si el que
    entra esta en la plantilla o tiene puja viva: el de una puja perdida
    no es de nadie. Nunca lanza."""
    salida = {"vende": set(), "se_van": set()}
    try:
        plantilla = _ids(plantilla)
        vivas = None if pujas is None else _ids(
            pujas.keys() if isinstance(pujas, dict) else pujas)
        for entra, c in _dict(libro_mejora).items():
            sale = _int(_dict(c).get("sale"))
            if sale is None:
                continue
            if vivas is not None and _int(entra) not in plantilla and _int(entra) not in vivas:
                continue
            salida["vende"].add(sale)
            if _int(entra) in plantilla:
                salida["se_van"].add(sale)
    except Exception:                               # noqa: BLE001
        pass
    return salida


# ============================================================
# EL PASO DEL WORKFLOW
# ============================================================

def _leer(ruta, defecto):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return defecto


def publicar(plan, ruta=None) -> bool:
    """Escribe el plan en `ruta` (por defecto `PLAN`). Nunca lanza."""
    try:
        destino = Path(ruta or PLAN)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(plan, indent=2, ensure_ascii=False, default=str) + "\n",
                           encoding="utf-8")
        return True
    except Exception:                               # noqa: BLE001
        return False


def adoptar(ids, libros, rutas, escribir) -> list:
    """
    Saca de los libros de la ronda y los chollos a los de `ids` (lo de
    su inventario que el cierre mete en su once), como la adopcion de
    la mejora del once: los mismos ficheros y el mismo formato
    (`json.dumps(libro, indent=2)`). Asi la ronda no lo malvende a
    menos de 20 h ni los chollos lo venden al cubrir su coste.

        libros    {"ronda", "chollos"} ya leidos (se tocan en sitio)
        rutas     {"ronda", "chollos"} donde se escriben
        escribir  {"ronda": bool, "chollos": bool}: solo se escribe el
                  libro que se leyo de su fichero (o cuya ruta se dio)

    Devuelve [{player_id, libro, importe, escrito}]. Nunca lanza.
    """
    adoptados = []
    try:
        ids, libros, rutas, escribir = _ids(ids), _dict(libros), _dict(rutas), _dict(escribir)
        for nombre in ("ronda", "chollos"):
            libro = libros.get(nombre)
            if not isinstance(libro, dict):
                continue
            quitar = [k for k in list(libro) if _int(k) in ids]
            if not quitar:
                continue
            fila = [{"player_id": _int(k), "libro": nombre, "importe": libro.pop(k)}
                    for k in quitar]
            escrito = False
            if escribir.get(nombre) and rutas.get(nombre):
                try:
                    Path(rutas[nombre]).write_text(json.dumps(libro, indent=2) + "\n")
                    escrito = True
                except Exception:                   # noqa: BLE001
                    escrito = False
            adoptados.extend({**a, "escrito": escrito} for a in fila)
    except Exception:                               # noqa: BLE001
        pass
    return adoptados


def _el_plan(d, ventana, ahora, hechas=(), adoptados=(), mejora_descartada=None) -> dict:
    try:
        d, ventana = _dict(d), _dict(ventana)
        try:
            generado = ahora.isoformat()
        except Exception:                           # noqa: BLE001
            generado = None
        return {
            "version": 2,
            "activo": bool(d.get("activo")),
            "motivo": d.get("motivo"),
            "ronda": d.get("ronda"),
            "plazo": d.get("plazo"),
            "horas": d.get("horas") if d.get("horas") is not None else ventana.get("horas"),
            "formacion": _dict(d.get("once")).get("formacion"),
            "xi": list(_dict(d.get("once")).get("ids") or []),
            "adoptados": [{"player_id": a.get("player_id"), "libro": a.get("libro"),
                           "escrito": a.get("escrito")} for a in _lista(adoptados)],
            "no_adoptados": [{"player_id": a.get("player_id"), "motivo": a.get("motivo")}
                             for a in _lista(d.get("no_adoptados"))],
            "titulares_que_no_se_venden": list(d.get("titulares_que_no_se_venden") or []),
            "vender": list(d.get("vender") or []),
            "cancelar": list(d.get("cancelar") or []),
            "caja": d.get("caja"),
            "caja_tras_cancelar": d.get("caja_tras_cancelar"),
            "caja_proyectada": d.get("caja_proyectada"),
            "deficit": d.get("deficit") or 0,
            "falta": d.get("falta") or 0,
            "hechas": [{"accion": h.get("accion"), "player_id": h.get("player_id"),
                        "exito": h.get("exito")} for h in _lista(hechas)],
            "vuelta_mejora_descartada": mejora_descartada,
            "generated_at": generado,
        }
    except Exception as error:                      # noqa: BLE001
        return {"version": 2, "activo": False,
                "motivo": f"ERROR: {type(error).__name__}: {error}", "generated_at": None}


def correr(status=None, snapshot=None, v10=None, libros=None, calendario=None,
           orden_ruta=None, escritor_factory=None, ahora: datetime | None = None,
           plan_ruta=None, libros_rutas=None) -> dict:
    """
    El cierre, en esta vuelta. Nunca lanza.

    Lo que no se pasa se lee de produccion: `status` del panel, la
    ultima `data/snapshot_*.json`, el estado de v10, los libros de la
    ronda, los chollos y la mejora y lo que la mejora hizo en esta
    vuelta (`libros` = {"ronda", "chollos", "mejora", "vuelta_mejora"},
    leidos de `libros_rutas` o de sus ficheros de siempre; la vuelta de
    la mejora, de `VUELTA_MEJORA`), el calendario de los chollos y la
    orden del gestor. La adopcion
    escribe el libro donde se leyo: si `libros` llega ya leido, solo en
    la ruta que diga `libros_rutas`. Apagado, no lee ni escribe nada.
    Encendido, publica el plan siempre, tambien si algo falla (activo
    False y el error).
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "plan": None, "decision": None}
    ventana = {}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        salida["adoptados"] = []
        ahora = ahora or datetime.now(timezone.utc)

        from src.actions.la_orden_del_gestor import (
            _pid, ejecutar, leer_la_foto, leer_la_orden, leer_los_estados, protegidos,
        )
        from src.actions.los_chollos import CALENDARIO, LIBRO as LIBRO_CHOLLOS
        from src.actions.la_ronda_de_la_manana import LIBRO as LIBRO_RONDA
        from src.actions.la_mejora_del_once import (
            LIBRO as LIBRO_MEJORA, STATUS, V10, _la_ultima_foto,
        )
        from src.analysis.el_calendario_de_puntos import contexto

        calendario = calendario if isinstance(calendario, dict) else _leer(
            CALENDARIO if calendario is None else calendario, {})

        ventana = la_ventana(ahora, calendario)
        motivo = por_que_no(ventana["horas"], ventana["en_curso"], ventana["puede_escribir"])
        if motivo:
            salida["motivo"] = motivo
            salida["plan"] = _el_plan({"motivo": motivo}, ventana, ahora)
            publicar(salida["plan"], plan_ruta)
            return salida

        status = status if status is not None else _leer(STATUS, {})
        snapshot = snapshot if snapshot is not None else _la_ultima_foto()
        v10 = v10 if v10 is not None else _leer(V10, {})
        dadas = _dict(libros_rutas)
        rutas = {"ronda": dadas.get("ronda") or LIBRO_RONDA,
                 "chollos": dadas.get("chollos") or LIBRO_CHOLLOS,
                 "mejora": dadas.get("mejora") or LIBRO_MEJORA,
                 "vuelta_mejora": dadas.get("vuelta_mejora") or VUELTA_MEJORA}
        if libros is None:
            libros = {k: _leer(ruta, {}) for k, ruta in rutas.items()}
            escribir = {k: True for k in rutas}
        else:
            escribir = {k: bool(dadas.get(k)) for k in rutas}
        libros = _dict(libros)

        yo = _pid(_dict(_dict(snapshot).get("league")).get("user"))
        if yo is None:
            salida["motivo"] = "SIN_SABER_QUIEN_SOY"
            salida["plan"] = _el_plan({"motivo": salida["motivo"]}, ventana, ahora)
            publicar(salida["plan"], plan_ruta)
            return salida
        foto = leer_la_foto(snapshot, yo)
        # Solo lo de ESTA vuelta: con un 429 la cache trae el estado de la
        # anterior, y sus cobros (ya en el saldo) contarian dos veces. La
        # misma prueba que la mejora del once (run_id; si no, la hora).
        from src.actions.la_mejora_del_once import es_de_esta_vuelta

        run_id = os.environ.get("GITHUB_RUN_ID")
        salida["v10_descartado"] = es_de_esta_vuelta(v10, ahora, run_id)
        # La mejora del once corre ANTES (13/10/2026): lo que pujo, cobro y
        # publico en esta vuelta, de su fichero, como un bloque mas de v10
        # y detras de todos (escribio despues). Solo si es de esta vuelta.
        hechas_mejora, salida["vuelta_mejora_descartada"] = la_vuelta_de_la_mejora(
            libros.get("vuelta_mejora"), ahora, run_id)
        de_la_vuelta = {} if salida["v10_descartado"] else dict(_dict(v10))
        de_la_vuelta.pop("la_mejora_del_once", None)
        de_la_vuelta["la_mejora_del_once"] = {"hechas": hechas_mejora}
        vuelta = lo_de_esta_vuelta(de_la_vuelta)

        roster = _lista(_dict(_dict(status).get("roster")).get("players"))
        plantilla = set(foto["plantilla"]) or _ids(p.get("id") for p in roster)
        plantilla -= set(vuelta["vendidos"])
        once_escrito = _ids(p.get("id") for p in
                            _lista(_dict(_dict(status).get("lineup")).get("players")))
        pujas = las_pujas_vivas(foto, vuelta)

        orden = _dict(leer_la_orden(orden_ruta))
        de_la_orden = la_orden(orden, plantilla, ahora, pujas, foto.get("mercado"))
        de_la_mejora = la_mejora(libros.get("mejora"), plantilla, pujas)
        de_la_ronda_y_los_chollos = (_ids(_dict(libros.get("ronda")).keys())
                                     | _ids(_dict(libros.get("chollos")).keys()))
        # Las pujas que no son del cierre aunque la clave siga en el libro
        # de los chollos: los `fichar` de la orden (este o no viva) y las
        # de la mejora.
        no_retirar = (_ids(f.get("player_id") for f in _lista(orden.get("fichar")))
                      | _ids(_dict(libros.get("mejora")).keys()))

        # Rondas de sobra: `decidir` se queda con las principales.
        ctx = contexto(status, calendario, ahora, RONDAS_A_MIRAR)
        d = decidir(
            plantilla=las_fichas(status, plantilla, leer_los_estados(snapshot), foto["precios"]),
            ctx=ctx, horas=ventana["horas"], en_curso=ventana["en_curso"],
            puede_escribir=ventana["puede_escribir"], saldo=foto["saldo"],
            pujas=pujas,
            vendidos=vuelta["vendidos"], ofertas=foto["ofertas_del_computer"],
            en_venta=set(foto["en_venta"]) | vuelta["listados"],
            especulativas=de_la_ronda_y_los_chollos, intocables=de_la_orden["intocables"],
            protegidos=protegidos(orden_ruta, ahora),
            no_vender=de_la_orden["vende"] | de_la_mejora["vende"],
            se_van=de_la_orden["se_van"] | de_la_mejora["se_van"],
            once_escrito=once_escrito, no_retirar=no_retirar,
            inventario=de_la_ronda_y_los_chollos & plantilla,
        )
        salida["decision"] = d
        salida["acciones"] = d["acciones"]

        # Lo de la ronda y los chollos que entra en el once, adoptado
        # antes de escribir nada en Biwenger.
        if d.get("activo") and d.get("adoptar"):
            salida["adoptados"] = adoptar(d["adoptar"], libros, rutas, escribir)

        escrituras = [a for a in d["acciones"] if a.get("accion") != "NADA"]
        if escrituras:
            if escritor_factory is None:
                from src.biwenger.write_client import BiwengerWriteClient

                escritor_factory = BiwengerWriteClient
            salida["hechas"] = ejecutar(escrituras, escritor_factory())

        salida["plan"] = _el_plan(d, ventana, ahora, salida["hechas"], salida["adoptados"],
                                  salida.get("vuelta_mejora_descartada"))
        publicar(salida["plan"], plan_ruta)
        salida["motivo"] = d["motivo"]

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"
        # Que no quede el plan de otra vuelta como si valiera.
        if salida["activa"]:
            salida["plan"] = _el_plan({"motivo": salida["motivo"], "activo": False},
                                      ventana, ahora, salida.get("hechas"),
                                      salida.get("adoptados"))
            publicar(salida["plan"], plan_ruta)

    return salida


def _euros(x) -> str:
    try:
        return f"{int(x):,}".replace(",", ".")
    except Exception:                               # noqa: BLE001
        return str(x)


def el_parte(r) -> list:
    """Las lineas del plan, para leerlo en el log. Nunca lanza."""
    lineas = []
    try:
        r = _dict(r)
        d = _dict(r.get("decision"))
        plan = _dict(r.get("plan"))
        ronda = _dict(plan.get("ronda") or d.get("ronda"))
        plazo = _dict(plan.get("plazo") or d.get("plazo"))
        horas = plan.get("horas")
        lineas.append(f"  {r.get('motivo')}  once para {ronda.get('label')} ({ronda.get('start')})"
                      + (f"; caja en >= 0 para {plazo.get('label')} ({plazo.get('start')})"
                         if plazo and plazo.get("label") != ronda.get("label") else "")
                      + (f", a {float(horas):.1f} h" if _num(horas) is not None else ""))
        if not d:
            return lineas
        once = _dict(d.get("once"))
        lineas.append(f"  Once {once.get('formacion')} ({once.get('lleno')}/11, "
                      f"{once.get('puntos')} xP de la ronda):")
        for j in _lista(once.get("jugadores")):
            lineas.append(f"      {str(j.get('name'))[:24]:<24} pos {j.get('position')}  "
                          f"xP {j.get('xp')}")
        for a in _lista(r.get("adoptados")):
            lineas.append(f"  Adoptado del libro de {a.get('libro')}: {a.get('player_id')}"
                          f"{'' if a.get('escrito') else ' (sin escribir el libro)'}")
        for a in _lista(d.get("no_adoptados")):
            lineas.append(f"  No se adopta a {a.get('player_id')}: {a.get('motivo')}")
        if r.get("vuelta_mejora_descartada"):
            lineas.append(f"  Sin la vuelta de la mejora: {r.get('vuelta_mejora_descartada')}")
        if d.get("titulares_que_no_se_venden"):
            lineas.append(f"  Titulares del once escrito que no se venden: "
                          f"{d.get('titulares_que_no_se_venden')}")
        lineas.append(f"  Caja al empezar la ronda: {_euros(d.get('caja'))}"
                      f"  (saldo - pujas vivas enteras + cobrado en la vuelta)")
        if d.get("cancelar"):
            lineas.append(f"  Retirar pujas especulativas: {d.get('cancelar')}"
                          f"  -> caja {_euros(d.get('caja_tras_cancelar'))}")
        if d.get("deficit"):
            lineas.append(f"  Deficit: {_euros(d.get('deficit'))}")
        for c in _lista(d.get("candidatos")):
            marca = "VENDER " if c.get("elegido") else "publicar"
            lineas.append(f"      {marca} {str(c.get('name'))[:24]:<24} valor "
                          f"{_euros(c.get('valor'))}  cobro {_euros(c.get('cobro'))}  "
                          f"xP {HORIZONTE_DE_QUEDARSE} rondas {c.get('quedarse')}")
        if d.get("falta"):
            lineas.append(f"  FALTA {_euros(d.get('falta'))}: ni todo el banquillo llega "
                          "(los cambios del once son de la mejora o del dueño)")
        for a in _lista(r.get("acciones")):
            lineas.append(f"  -> {a.get('accion')} {a.get('player_id')} {a.get('nombre') or ''} "
                          f"{_euros(a.get('importe') or a.get('precio')) if (a.get('importe') or a.get('precio')) else ''}"
                          f"{(' (' + str(a.get('motivo')) + ')') if a.get('motivo') else ''}")
        for h in _lista(r.get("hechas")):
            lineas.append(f"  hecha {h.get('accion')} {h.get('player_id')} exito={h.get('exito')} "
                          f"http={h.get('http_status')} {h.get('error') or ''}")
    except Exception as error:                      # noqa: BLE001
        lineas.append(f"  (el parte no se pudo escribir: {type(error).__name__})")
    return lineas


def main() -> int:
    r = correr()
    print("=" * 100)
    print("EL CIERRE DE LA JORNADA")
    print("=" * 100)
    for linea in el_parte(r):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
