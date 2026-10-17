"""
LA ROTACION (17/10/2026)

POR QUE EXISTE

    Laboratorio de la rotacion del 17/10 (vender al que cae, comprar al
    que sube, misma posicion): con N = 2 dias sin subir, el once
    incluido, tolerancia de xP 0 y como mucho 2 cambios por ventana y
    por semana, la rotacion le gano a no hacer nada en todas las
    pasadas completas: +0,39 M en 14 dias con una plantilla como la de
    hoy, +1,72 M en 27 dias con la de 19 jugadores del 19/09; +0,20 M de
    media por semana (mediana +65 mil, la peor -70 mil). Y sin perder
    puntos: J8 +3 y +6 contra no hacer nada.

    Casi todo lo medible lo da VENDER al que cae, no comprar al que
    sube: el que lleva 2 dias sin subir pierde un 6,1 % en los 7
    siguientes (n = 358, robusto); el que sube en el Computer y se gana
    con la prima del tramo da +2,3 % de media y -0,9 % de mediana
    (n = 38). Con la puja fuerte (+12 %) da -3,8 %: aqui nunca.

    OJO, DATOS FINOS. 31 dias de mercado, UNA jornada puntuada (J8) y 6
    cambios en total entre las dos pasadas; una o dos subidas baratas
    explican casi toda la ganancia (sin la mejor, la pasada B da 0).
    Se espera ~+30 mil al dia: compensa ~el 20 % de la deriva de
    -140 mil al dia, no toda. Roberto Fernandez (8,86 M, xP 7,75) no
    se rota con tolerancia 0: en 31 dias nunca hubo otro igual que
    subiera. Hay que volver a medirlo tras 3-4 jornadas.

LA REGLA

    1. EL QUE CAE (`decidir`). De la plantilla de la foto: posicion
       1-4, con nombre, sin Yamal, ni `proteger`/`fichar` del gestor
       (`la_orden_del_gestor.protegidos`), ni `no_rotar` de la orden
       (`no_rotados`), ni lo que aguanta LA CARTERA
       (`la_ronda_de_la_manana.los_que_aguanta`), ni lo que otro libro
       ya vende (ronda, chollos, mejora, orden: `los_que_otros_venden`;
       del cierre, solo su `vender` del plan fresco: sus `candidatos`
       son todo el banquillo), ni lo cobrado o publicado en esta vuelta
       (v10, la mejora, el cierre y el parte, de sus ficheros de la
       vuelta), ni lo que ya esta en una pareja. Y `priceIncrement` de hoy <= 0 Y el
       de ayer <= 0 (`DIAS_SIN_SUBIR`; ayer, de
       data/autopilot/price_history.json: el precio de ayer menos el de
       anteayer, cada uno el ultimo apuntado antes del reset siguiente;
       sin muestra en el dia, no se sabe y no cae). El plano en el
       suelo de 150 mil tambien cae: con el es una apuesta al que sube.
       Primero el que mas baja hoy; a igualdad, el de menos xP.

       `conservar` NO lo frena: la rotacion no vende para hacer caja,
       cambia a uno por otro igual o mejor, y solo vende cuando el otro
       YA esta en la plantilla. `conservar` es para los vendedores de
       liquidez. Para que el gestor la frene con uno, `no_rotar` en la
       orden (como `no_pujar`: `[{"player_id", "nombre", "por_que"}]`).

    2. EL QUE ENTRA. Del Computer (las listas de los managers no son
       subasta), que sube hoy (`priceIncrement` > 0), 'ok', que juega
       (`la_ronda_de_la_manana.juega`: 3 partidos y 3 puntos por
       partido), no nuestro, sin puja viva de NINGUN motor (foto y
       esta vuelta), ni vetado (`no_pujar`), ni en el libro de otro
       (lo que aguanta la cartera, lo que otro vende) ni un `fichar`
       del gestor (es de la orden). Misma posicion y xP >= el
       del que sale (`TOLERANCIA_XP` = 0). xP = puntos de la temporada /
       jornadas jugadas (las cerradas de
       data/intelligence/puntos_por_jornada.jsonl). El denominador es el
       mismo para todos: con tolerancia 0 no cambia ninguna decision,
       solo lo que se lee en el log. El de mas xP; a igualdad, el que
       mas sube en proporcion a su precio.

       NO se pide `la_subida_minima` de la ronda: esa se midio para
       comprar y revender (la cartera); aqui la ganancia es la venta del
       que cae. En el laboratorio, 3 de los 5 cambios de la pasada A y
       el UNICO de la B (Ruben Sanchez, +10 mil sobre 540 mil; minima
       16.740: toda su ganancia, +390 mil) no la pasaban.

    3. CUANTO. `la_ronda_de_la_manana.la_puja_de_la_cartera`: la prima
       del tramo (+12 % por debajo de 1 M, +4 % hasta 3 M, +1 % por
       encima), terminada en 9.900; NUNCA la puja fuerte. Como mucho
       `TOPE_POR_VIAJE` y `maximumBid`.

    4. CUANTOS. `MAXIMO_DE_CAMBIOS` (2) por ventana entre rondas Y por
       semana ISO, lo que apriete mas: las parejas ganadas mas las que
       tienen la puja viva. Una perdida no gasta cupo. Una puja por el
       que cae al dia. La ventana se nombra por la ronda que la cierra
       (`J10`, `J6-aparte`), no por la hora de su primer partido: si esa
       hora se mueve a mitad de ventana, la cuenta sigue.

    5. CUANDO SE PUJA. Nunca si el proximo reset (07:00 de Madrid) cae
       dentro de una ronda (`la_proxima_jornada`: aplazados incluidos,
       como el Levante-Athletic del 21/10): el que entra llegaria con la
       ronda empezada. Ni si la ronda empieza antes de ese reset (la
       puja se resolveria despues del partido). Pujar con una ronda
       jugandose si vale si el reset cae despues de su ultimo partido:
       una puja no toca el once. Y nunca de 04:45 a 07:00 de Madrid
       (`zona_de_silencio.en_la_franja`), tampoco en las vueltas puestas
       a proposito a las 04:45 y 04:50: son de la ventana (la subasta
       del reset de v10, que la caja de aqui no ve), no de la rotacion.

    6. LA CAJA, la de TODOS los motores. Antes = saldo - todas nuestras
       pujas vivas (foto y esta vuelta) + lo que se espera cobrar por
       los que salen de parejas ya ganadas (el 95 % de su valor si ya
       estan publicados y su oferta llega antes de la ronda; la oferta
       aceptada en esta vuelta, por su importe), y SOLO si nada frena su
       venta (ni `nunca`, ni titular sin relevo, ni titular antes de una
       ronda de aplazados, ni el once sin leer o incompleto, ni el que
       entro vendido en esta vuelta). Despues = antes - la puja + el 95 %
       del que sale SOLO si se cobra antes de la ronda (dos resets:
       `HORAS_PARA_COBRAR`) y no es (o puede ser: once sin saber)
       titular antes de una ronda de aplazados, que es cuando la venta
       se frena. Vale si despues >= 0 o despues >= antes. Hoy (saldo
       -432.317) solo pasan los cambios que no gastan caja. Si una puja
       solo cabe con lo aceptado en esta misma vuelta
       (`cuenta_con_lo_aceptado`) y esa aceptacion no entra, no se manda.

    7. LA VENTA, solo cuando el que entra YA esta en la plantilla, sin
       ronda jugandose y a mas de `HORAS_SIN_TOCAR_EL_ONCE` del cierre:
         a) EL ONCE. Antes de aceptar, se lee la alineacion vigente en
            Biwenger EN ESE MOMENTO (no la de la foto: el orquestador
            pudo escribir otra en esta vuelta). Si el que sale esta en
            ella, se escribe la misma alineacion con el que entra en su
            sitio (misma posicion, mismo dibujo), o, si el que entra no
            esta sano o ya es titular, el suplente sano de esa posicion
            con mas xP que nadie mas vende (ni la cartera, ni otro libro,
            ni lo publicado en esta vuelta: lo venderian sin mirar el
            once). Solo si Biwenger dice que se guardo se acepta la
            oferta. Sin relevo, o sin poder leer el once, no se vende. Si
            la proxima ronda es de aplazados (solo juegan dos equipos) y es
            titular, tampoco: su relevo seguramente no juega; se vende
            cuando acabe.
            No se fia del orquestador: escribe el once una vez por
            vuelta como mucho, la caja le gana la prioridad, se cierra
            de T-15 a +2 h y corre ANTES que este paso (una venta aqui
            dejaria el hueco al menos una hora, y la ultima antes de
            T-15, para toda la ronda). `BORDALAS_EL_ONCE_UNA_VEZ` no
            escribe nada (es una cache de la busqueda).
         b) Lo publica a su valor si no esta publicado.
         c) Acepta la oferta del Computer desde el 99 % de su valor, o
            desde el 95 % si la siguiente (48 h despues) no llegaria
            antes de la ronda o si la caja ya esta en rojo. Aunque haya
            empezado a subir: la pareja esta hecha.
       Si el que entro se vendio en esta vuelta (otro motor), la pareja
       se rompe: el que iba a salir no se vende.
       Puja perdida: nunca se vende al que iba a salir; se vuelve a
       mirar al dia siguiente. Perdida es solo con una foto de DESPUES
       del reset que resuelve la puja (la hora de la foto sin zona es de
       Madrid: `league_collector` y TZ del workflow); y si el que entra
       aparece antes del reset siguiente, la pareja vuelve a GANADA.

    Mientras la puja esta viva, `los_que_rota` lo da para que el motor
    viejo no lo venda (las dos puertas de `autopilot_executor` que
    aceptan ofertas). `las_parejas_abiertas` da a los demas los que
    salen (y entran) de las parejas abiertas: el reroll no tira la
    oferta de uno que sale (`los_que_otros_venden`, LA_ROTACION), la
    mejora del once no le busca otro relevo y el cierre no lo pone en
    su once si su relevo ya llego. Todo vacio con la rotacion apagada.

EL LIBRO

    `LIBRO` (data/trading/la_rotacion.json, en la cache de data/trading
    como el de la ronda): las parejas y su estado (PUJADA, GANADA,
    VENDIDA, PERDIDA, ROTA, FALLIDA). `REGISTRO`
    (data/trading/la_rotacion.jsonl, a git): una linea por cada cosa
    que pasa; la de cada PUJAR lleva la pareja entera (`nueva`). Si el
    estado falta (la cache se desalojo: el registro vuelve de git) o es
    mas viejo que la ultima linea del registro, `leer_libro` lo rehace
    del registro (`rehacer`). Lo que NO arregla: una vuelta que falla
    despues de este paso no guarda la cache, y la siguiente restaura el
    estado Y el registro de antes (la cache pisa lo de git); como el
    libro de la ronda o el de la mejora. Lo que queda entonces es la
    foto: la puja viva del que entraba no se vuelve a pujar.

QUE NO HACE

    No compra a managers ni vende a managers, no sube ni retira pujas,
    no quita de la venta y no cuadra la caja de la jornada (eso es del
    cierre: si una pareja ganada no cobra antes de la ronda y la caja
    queda en rojo, vende el cierre). No toca el once salvo para que el
    que sale no deje un hueco.

    Corre como paso propio del workflow, DESPUES del parte (lee lo que
    esta vuelta ya pujo, cobro y publico: v10, `la_mejora_vuelta.json`,
    el plan del cierre y `el_parte_vuelta.json`, que el parte escribe
    desde su `main`): `python -m src.actions.la_rotacion`. Nace
    APAGADA: `BORDALAS_LA_ROTACION`. Nunca lanza.
"""

from __future__ import annotations

import json
import math
import os

from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ENV = "BORDALAS_LA_ROTACION"
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "la_rotacion.json"
REGISTRO = RAIZ / "data" / "trading" / "la_rotacion.jsonl"
JORNADAS = RAIZ / "data" / "intelligence" / "puntos_por_jornada.jsonl"
HISTORICO = RAIZ / "data" / "autopilot" / "price_history.json"

DIAS_SIN_SUBIR = 2              # hoy y ayer sin subir
TOLERANCIA_XP = 0.0             # el que entra, xP >= el del que sale
MAXIMO_DE_CAMBIOS = 2           # por ventana entre rondas y por semana ISO
VENTA_ESTIMADA = 0.95           # la oferta del Computer mas baja vista (0,951)
ACEPTA = 0.99                   # la oferta que se acepta por el que sale
ACEPTA_CON_PRISA = 0.95         # si la siguiente no llega o la caja esta en rojo
HORAS_PARA_COBRAR = 25          # dos resets antes de la ronda: llega y se cobra
HORAS_UN_RESET = 1              # la oferta del proximo reset, aceptada a las 07:15
HORAS_SIN_TOCAR_EL_ONCE = 0.25  # T-15, el cierre del orquestador
PARTIDOS_DE_UNA_RONDA = 5       # menos, o aparte: una ronda de aplazados
RESET_MADRID = 7                # el reset de las 07:00 de Madrid
MINUTOS_TRAS_EL_RESET = 10      # una foto de antes no sabe si la puja se perdio
DIAS_EN_EL_LIBRO = 30

# La puja que solo cabia con una aceptacion de esta vuelta que no entro.
SIN_EL_COBRO = "SIN_EL_COBRO_DE_ESTA_VUELTA"

POSICIONES = frozenset({1, 2, 3, 4})
SANOS = frozenset({"ok", "warned"})
INTOCABLE = "yamal"

# Las parejas: con la puja viva, ganada (falta vender al que sale),
# cerrada (el que sale ya no esta), perdida, rota (el que entro ya no
# esta: no se vende al que iba a salir) y fallida (la puja no entro).
PUJADA, GANADA, VENDIDA, PERDIDA, ROTA, FALLIDA = (
    "PUJADA", "GANADA", "VENDIDA", "PERDIDA", "ROTA", "FALLIDA")
ABIERTAS = frozenset({PUJADA, GANADA})
GASTAN_CUPO = frozenset({PUJADA, GANADA, VENDIDA, ROTA})


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
        v = float(x)
        return v if math.isfinite(v) else defecto
    except (TypeError, ValueError, OverflowError):
        return defecto


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
        if isinstance(x, (str, bytes)):
            return set()
        return {i for i in (_int(v) for v in (x or [])) if i is not None}
    except Exception:                               # noqa: BLE001
        return set()


def _por_id(x) -> dict:
    """`{player_id: valor}` con las claves en entero. Nunca lanza."""
    try:
        return {_int(k): v for k, v in _dict(x).items() if _int(k) is not None}
    except Exception:                               # noqa: BLE001
        return {}


def _cuando(x) -> datetime | None:
    """ISO (o datetime) a datetime con zona; sin zona, UTC (las vueltas
    corren en UTC). None si no se lee."""
    try:
        t = x if isinstance(x, datetime) else datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _utc(ahora) -> datetime:
    t = _cuando(ahora)
    return t.astimezone(timezone.utc) if t else datetime.now(timezone.utc)


def la_hora_de_la_foto(x) -> datetime | None:
    """La hora de la foto, con zona. `league_collector` la apunta con
    `datetime.now()` sin zona y el workflow corre con TZ Europe/Madrid:
    sin zona es hora de MADRID, no UTC (leida como UTC, una foto de
    antes de la puja parecia de despues). Nunca lanza; None si no se lee."""
    try:
        t = x if isinstance(x, datetime) else datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        if t.tzinfo:
            return t
        from src.analysis.market_clock import madrid_offset_hours

        como_utc = t.replace(tzinfo=timezone.utc)
        return como_utc - timedelta(hours=madrid_offset_hours(como_utc))
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# EL RELOJ (puro: la hora y el calendario entran por argumento)
# ============================================================

def el_reset_del_dia(dia: date) -> datetime:
    """Las 07:00 de Madrid de `dia`, en UTC. El desfase, el de ese dia a
    las 05:00 UTC (el cambio de hora es a la 01:00 UTC), con la regla
    europea de `market_clock` (sin `zoneinfo`)."""
    from src.analysis.market_clock import madrid_offset_hours

    base = datetime(dia.year, dia.month, dia.day, RESET_MADRID, tzinfo=timezone.utc)
    return base - timedelta(hours=madrid_offset_hours(base.replace(hour=5)))


def los_resets(ahora) -> tuple:
    """`(el ultimo reset <= ahora, el proximo > ahora)`, en UTC."""
    ahora = _utc(ahora)
    hoy = ahora.date()
    candidatos = [el_reset_del_dia(hoy + timedelta(days=d)) for d in (-2, -1, 0, 1, 2)]
    ultimo = max(r for r in candidatos if r <= ahora)
    proximo = min(r for r in candidatos if r > ahora)
    return ultimo, proximo


def el_dia_de_mercado(ahora) -> date:
    """El dia de Madrid del ultimo reset: lo que va de un reset al
    siguiente es un dia de mercado."""
    from src.analysis.market_clock import madrid_offset_hours

    ultimo, _ = los_resets(ahora)
    return (ultimo + timedelta(hours=madrid_offset_hours(ultimo))).date()


def la_ventana_de(ronda) -> str | None:
    """El nombre de la ventana que cierra `ronda` (una de `las_rondas`):
    `J{jornada}`, con `-aparte` si son aplazados fuera de su jornada.
    Sin jornada, la hora de su primer partido. Nunca lanza."""
    try:
        ronda = _dict(ronda)
        jornada = _int(ronda.get("jornada"))
        if jornada is None:
            return ronda["inicio"].astimezone(timezone.utc).isoformat()
        return f"J{jornada}" + ("-aparte" if ronda.get("aparte") else "")
    except Exception:                               # noqa: BLE001
        return None


def el_reloj(ahora, calendario=None, puede_escribir=True) -> dict:
    """
    Lo que `decidir` necesita del reloj, de `ahora` y el calendario
    (`la_proxima_jornada`: rondas a lo Biwenger, aplazados incluidos).

        horas_ronda     al primer partido de la proxima ronda sin empezar
        horas_reset     al proximo reset de las 07:00 de Madrid
        reset_en_ronda  ese reset cae dentro de una ronda (en duda, True)
        en_curso        hay una ronda jugandose (en duda, True)
        ventana         la proxima ronda (`la_ventana_de`: `J10`,
                        `J6-aparte`): la ventana entre rondas en la que
                        se decide. Por su nombre y no por su hora: si el
                        primer partido se mueve, la ventana es la misma
        inicio_ronda    la hora de ese primer partido (para el log)
        ronda_parcial   la proxima es una ronda de aplazados (aparte o
                        con menos de `PARTIDOS_DE_UNA_RONDA` partidos,
                        como el Levante-Athletic del 21/10): solo
                        puntuan los de esos equipos
        dia, semana     el dia de mercado y su semana ISO

    Nunca lanza: si algo falla, `sin_calendario`.
    """

    reloj = {"puede_escribir": bool(puede_escribir), "sin_calendario": True,
             "en_curso": True, "horas_ronda": None, "horas_reset": None,
             "reset_en_ronda": True, "ventana": None, "inicio_ronda": None,
             "ronda_parcial": False, "dia": None, "semana": None, "proximo_reset": None}
    try:
        from src.analysis.la_proxima_jornada import (
            horas_al_proximo_cierre, jornada_en_curso, las_rondas,
        )

        ahora = _utc(ahora)
        _, proximo = los_resets(ahora)
        dia = el_dia_de_mercado(ahora)
        ano, semana, _ = dia.isocalendar()
        reloj.update({"horas_reset": round((proximo - ahora).total_seconds() / 3600, 4),
                      "proximo_reset": proximo.isoformat(), "dia": dia.isoformat(),
                      "semana": f"{ano}-W{semana:02d}"})
        rondas = las_rondas(calendario)
        if not rondas:
            return reloj
        futuras = sorted((r for r in rondas if r["inicio"] > ahora), key=lambda r: r["inicio"])
        horas = horas_al_proximo_cierre(ahora, calendario)
        reloj.update({
            "sin_calendario": False,
            "en_curso": bool(jornada_en_curso(ahora, calendario)),
            "reset_en_ronda": bool(jornada_en_curso(proximo, calendario)),
            "horas_ronda": None if horas is None else round(float(horas), 4),
            "ventana": la_ventana_de(futuras[0]) if futuras else None,
            "inicio_ronda": (futuras[0]["inicio"].astimezone(timezone.utc).isoformat()
                             if futuras else None),
            "ronda_parcial": bool(futuras) and bool(
                futuras[0].get("aparte")
                or (_int(futuras[0].get("partidos"), 0) or 0) < PARTIDOS_DE_UNA_RONDA),
        })
    except Exception:                               # noqa: BLE001
        reloj["sin_calendario"] = True
    return reloj


def por_que_no(reloj) -> str | None:
    """None si toca mirar la rotacion en esta vuelta. Nunca lanza."""
    try:
        reloj = _dict(reloj)
        if not reloj.get("puede_escribir"):
            return "ZONA_DE_SILENCIO"
        if reloj.get("sin_calendario") or not reloj.get("dia"):
            return "SIN_CALENDARIO"
        return None
    except Exception:                               # noqa: BLE001
        return "SIN_CALENDARIO"


def por_que_no_puja(reloj) -> str | None:
    """None si una puja de hoy se resuelve entre rondas y antes de la
    proxima. Nunca lanza."""
    try:
        reloj = _dict(reloj)
        horas_ronda, horas_reset = _num(reloj.get("horas_ronda")), _num(reloj.get("horas_reset"))
        if horas_ronda is None or horas_reset is None:
            return "SIN_PROXIMA_RONDA"
        if reloj.get("reset_en_ronda") or reloj.get("reset_en_ronda") is None:
            return "EL_RESET_CAE_EN_UNA_RONDA"
        if horas_ronda <= horas_reset:
            return "LA_PUJA_SE_RESOLVERIA_CON_LA_RONDA_EMPEZADA"
        return None
    except Exception:                               # noqa: BLE001
        return "SIN_PROXIMA_RONDA"


def por_que_no_vende(reloj) -> str | None:
    """None si se puede vender al que sale (y tocar el once). Nunca lanza."""
    try:
        reloj = _dict(reloj)
        if reloj.get("en_curso") or reloj.get("en_curso") is None:
            return "JORNADA_EN_CURSO"
        horas = _num(reloj.get("horas_ronda"))
        if horas is not None and horas <= HORAS_SIN_TOCAR_EL_ONCE:
            return "CERCA_DEL_CIERRE"
        return None
    except Exception:                               # noqa: BLE001
        return "JORNADA_EN_CURSO"


def se_cobra_antes(reloj, horas_extra) -> bool:
    """¿Cabe `horas_extra` despues del proximo reset antes de la ronda?
    Sin proxima ronda, si (no hay ronda que pagar). Nunca lanza."""
    try:
        reloj = _dict(reloj)
        horas_ronda, horas_reset = _num(reloj.get("horas_ronda")), _num(reloj.get("horas_reset"))
        if horas_reset is None:
            return False
        if horas_ronda is None:
            return True
        return horas_ronda > horas_reset + horas_extra
    except Exception:                               # noqa: BLE001
        return False


MOTIVOS = {
    "ZONA_DE_SILENCIO": ("zona de silencio (04:45-07:00 de Madrid, tambien en las vueltas "
                         "de la ventana): no se escribe"),
    "SIN_CALENDARIO": "sin calendario no se sabe donde caen las rondas: no se rota",
    "SIN_PROXIMA_RONDA": "sin proxima ronda en el calendario: no se puja",
    "EL_RESET_CAE_EN_UNA_RONDA": ("el proximo reset cae dentro de una ronda: el que entra "
                                  "llegaria con la ronda empezada"),
    "LA_PUJA_SE_RESOLVERIA_CON_LA_RONDA_EMPEZADA": ("la proxima ronda empieza antes del "
                                                    "proximo reset: no se puja"),
    "JORNADA_EN_CURSO": ("hay una ronda jugandose (el once no se cambia empezada la "
                         "ronda): no se vende ni se publica al que sale"),
    "CERCA_DEL_CIERRE": "a menos de 15 minutos del cierre del once: no se vende",
    "SIN_CUPO": "ya hay 2 cambios en esta ventana o en esta semana",
    "SIN_SALDO": "sin saldo en la foto no se sabe si cabe: no se puja",
    "SIN_JORNADAS": "sin jornadas jugadas no hay xP: no se puja",
    "FALTA_LEER_EL_ONCE": "falta leer el once vigente en Biwenger antes de vender",
    "SIN_ONCE_DE_BIWENGER": ("no se pudo leer el once vigente en Biwenger: no se vende "
                             "(podria dejar un hueco)"),
    "SIN_RELEVO_PARA_EL_ONCE": ("es titular y no hay relevo sano de su posicion: no se "
                                "vende (dejaria el once en 10)"),
    "ONCE_INCOMPLETO": "el once vigente no tiene 11 o no trae dibujo: no se toca",
    "TITULAR_ANTES_DE_UNA_RONDA_PARCIAL": ("es titular y la proxima ronda es de aplazados: "
                                           "su relevo seguramente no juega; se vende "
                                           "cuando acabe"),
    "EL_QUE_ENTRO_SE_VENDIO_EN_ESTA_VUELTA": ("otro motor vendio en esta vuelta al que "
                                              "entro: la pareja se rompe y el que iba a "
                                              "salir no se vende"),
}


# ============================================================
# LO QUE CAE AYER (puro)
# ============================================================

def el_precio_del_dia(serie, desde, hasta) -> int | None:
    """El ultimo precio apuntado en [desde, hasta) (epoch). El historico
    apunta cuando cambia y cada 20 h como mucho: con vueltas, cada dia
    de mercado tiene al menos una muestra. Sin ella, None. Nunca lanza."""
    try:
        serie = _dict(serie)
        mejor = None
        for t, p in zip(serie.get("t") or [], serie.get("p") or []):
            t, p = _num(t), _int(p)
            if t is None or not p or not (desde <= t < hasta):
                continue
            if mejor is None or t >= mejor[0]:
                mejor = (t, p)
        return mejor[1] if mejor else None
    except Exception:                               # noqa: BLE001
        return None


def la_subida_de_ayer(serie, ahora) -> int | None:
    """Lo que subio ayer: el precio del dia de mercado de ayer menos el
    de anteayer (cada uno, el ultimo apuntado antes de su reset
    siguiente). None si falta alguno. Nunca lanza."""
    try:
        ultimo, _ = los_resets(ahora)
        dia = el_dia_de_mercado(ahora)
        ayer = el_reset_del_dia(dia - timedelta(days=1)).timestamp()
        anteayer = el_reset_del_dia(dia - timedelta(days=2)).timestamp()
        p_ayer = el_precio_del_dia(serie, ayer, ultimo.timestamp())
        p_anteayer = el_precio_del_dia(serie, anteayer, ayer)
        if p_ayer is None or p_anteayer is None:
            return None
        return p_ayer - p_anteayer
    except Exception:                               # noqa: BLE001
        return None


def el_xp(ficha, rondas) -> float | None:
    """Puntos de la temporada / jornadas jugadas. None sin jornadas."""
    rondas = _int(rondas)
    if not rondas or rondas <= 0:
        return None
    return (_num(_dict(ficha).get("points"), 0.0) or 0.0) / rondas


def _nombre(ficha) -> str:
    return str(_dict(ficha).get("name") or "").strip()


# ============================================================
# LAS PAREJAS (puro)
# ============================================================

def al_dia(parejas, *, plantilla, pujas_de_la_foto, foto_en=None, ahora=None,
           vendidos=frozenset()) -> tuple:
    """
    Las parejas con lo que dice la foto: `(parejas, eventos)`.

        PUJADA  el que entra en la plantilla: GANADA. Si no, y su puja
                ya no esta en una foto de DESPUES del reset que la
                resuelve (`MINUTOS_TRAS_EL_RESET`; la hora de la foto,
                `la_hora_de_la_foto`): PERDIDA (sin hora de la foto, a
                las 26 h). Si no, sigue.
        PERDIDA el que entra aparece en la plantilla antes del reset
                siguiente al que la resolvio: era una foto vieja,
                GANADA.
        GANADA  el que sale ya no esta (o se vendio en esta vuelta,
                `vendidos`): VENDIDA. El que entro ya no esta (o se
                vendio en esta vuelta): ROTA (no se vende al que iba a
                salir).

    Pura, nunca lanza.
    """

    nuevas, eventos = [], []
    try:
        plantilla, pujas, vendidos = _ids(plantilla), _ids(pujas_de_la_foto), _ids(vendidos)
        foto_en, ahora = la_hora_de_la_foto(foto_en), _cuando(ahora)
        for p in _lista(parejas):
            p = dict(p)
            sale, entra, estado = _int(p.get("sale")), _int(p.get("entra")), p.get("estado")
            pujada = _cuando(p.get("pujada_en"))
            # El reset que resuelve la puja (el primero despues de ella).
            resuelta = los_resets(pujada)[1] if pujada is not None else None
            cuando = ahora or foto_en
            if (estado == PERDIDA and entra in plantilla and resuelta is not None
                    and cuando is not None and cuando < los_resets(resuelta)[1]):
                estado = PUJADA
            if estado == PUJADA:
                if entra in plantilla:
                    estado = GANADA
                    p["llego_en"] = (ahora or foto_en or datetime.now(timezone.utc)).isoformat()
                    eventos.append({"evento": GANADA, "pareja": p.get("id"), "sale": sale,
                                    "entra": entra})
                elif entra not in pujas and pujada is not None and (
                        (foto_en is not None
                         and foto_en > resuelta + timedelta(minutes=MINUTOS_TRAS_EL_RESET))
                        or (foto_en is None and ahora is not None
                            and ahora - pujada > timedelta(hours=26))):
                    estado = PERDIDA
                    eventos.append({"evento": PERDIDA, "pareja": p.get("id"), "sale": sale,
                                    "entra": entra})
            if estado == GANADA:
                if sale not in plantilla or sale in vendidos:
                    estado = VENDIDA
                    eventos.append({"evento": VENDIDA, "pareja": p.get("id"), "sale": sale,
                                    "entra": entra})
                elif entra not in plantilla or entra in vendidos:
                    estado = ROTA
                    eventos.append({"evento": ROTA, "pareja": p.get("id"), "sale": sale,
                                    "entra": entra})
            p["estado"] = estado
            nuevas.append(p)
    except Exception:                               # noqa: BLE001
        return [dict(p) for p in _lista(parejas)], []
    return nuevas, eventos


def el_cupo(parejas, ventana, semana) -> dict:
    """Los cambios ya hechos (o con la puja viva) en esta ventana y en
    esta semana, y los que quedan. Nunca lanza."""
    try:
        cuentan = [p for p in _lista(parejas) if p.get("estado") in GASTAN_CUPO]
        en_ventana = sum(1 for p in cuentan if ventana and p.get("ventana") == ventana)
        en_semana = sum(1 for p in cuentan if semana and p.get("semana") == semana)
        return {"ventana": en_ventana, "semana": en_semana,
                "quedan": max(0, MAXIMO_DE_CAMBIOS - max(en_ventana, en_semana))}
    except Exception:                               # noqa: BLE001
        return {"ventana": None, "semana": None, "quedan": 0}


def el_relevo(sale, entra, once_ids, plantilla, fichas, rondas, no_valen=frozenset()) -> int | None:
    """Quien ocupa el sitio del que sale en el once: el que entra si esta
    sano y no es ya titular; si no, el suplente sano de su posicion con
    mas xP (ni otro que sale ni lo que se vende en esta vuelta). None si
    no hay. Pura."""
    posicion = _int(_dict(fichas.get(sale)).get("position"))
    if posicion not in POSICIONES:
        return None

    def vale(pid):
        f = _dict(fichas.get(pid))
        return (pid in plantilla and pid not in once_ids and pid not in no_valen
                and pid != sale and _int(f.get("position")) == posicion
                and str(f.get("status") or "").strip().lower() in SANOS)

    if vale(entra):
        return entra
    banquillo = sorted((pid for pid in plantilla if vale(pid)),
                       key=lambda pid: (-(el_xp(fichas.get(pid), rondas) or 0.0), pid))
    return banquillo[0] if banquillo else None


# ============================================================
# LA DECISION (pura)
# ============================================================

def decidir(
    *, plantilla, fichas, mercado, subidas_de_ayer, rondas_jugadas=None, saldo=None,
    pujas_vivas=None, maximo_de_puja=None, ofertas_del_computer=None,
    en_venta=frozenset(), parejas=(), protegidos=frozenset(), no_rotar=frozenset(),
    aguanta=frozenset(), vetados=frozenset(), otros_venden=frozenset(),
    vendidos=frozenset(), listados=frozenset(), once=None, once_de_la_foto=None,
    reloj=None,
) -> dict:
    """
    Que hace la rotacion en esta vuelta. Pura: ni red, ni disco, ni reloj.

        plantilla           {player_id} nuestros (la foto)
        fichas              {player_id: ficha del catalogo} (name, position,
                            price, priceIncrement, status, points,
                            playedHome, playedAway)
        mercado             {player_id: precio} del Computer
        subidas_de_ayer     {player_id: lo que subio ayer, o None}
        rondas_jugadas      el denominador del xP
        saldo               el de la foto
        pujas_vivas         {player_id: importe} de TODOS los motores
                            (foto y esta vuelta)
        maximo_de_puja      `maximumBid`
        ofertas_del_computer {player_id: {"offer_id", "amount"}}
        en_venta            {player_id} publicados (foto y esta vuelta)
        parejas             las del libro, ya al dia (`al_dia`)
        protegidos          `proteger` y `fichar` de la orden
        no_rotar            `no_rotar` de la orden
        aguanta             lo de LA CARTERA
        vetados             `no_pujar` de la orden
        otros_venden        {player_id} que otro libro ya vende
        vendidos, listados  lo cobrado y publicado en esta vuelta
        once                {"ids": [...] en orden, "formacion"} vigente en
                            Biwenger (leida al momento); None = sin leer
        once_de_la_foto     {player_id} del once de la foto
                            (`user_lineup`); None = no se sabe. Con
                            `once`, para la caja: quien es (o puede ser)
                            titular y no se vendera antes de una ronda
                            de aplazados
        reloj               `el_reloj`

    `{"activo", "motivo", "acciones", "caidos", "no_rota", "parejas_nuevas",
    "cupo", "caja", "por_que_no_puja", "por_que_no_vende",
    "necesita_el_once", "sin_cobro"}`. Las acciones van en orden de
    escritura: CAMBIAR_EL_ONCE, ACEPTAR_OFERTA_DEL_COMPUTER,
    PONER_A_LA_VENTA, PUJAR. `sin_cobro`: {player_id: por que} de los que
    salen de parejas ganadas cuya venta esta frenada (su cobro no cuenta
    en la caja). Una PUJAR con `cuenta_con_lo_aceptado` solo cabe con las
    aceptaciones de esta vuelta: `escribir` no la manda si alguna falla.
    """

    salida = {"activo": False, "motivo": None, "acciones": [], "caidos": [],
              "no_rota": [], "parejas_nuevas": [], "cupo": None, "caja": None,
              "por_que_no_puja": None, "por_que_no_vende": None,
              "necesita_el_once": False, "sin_cobro": {}}
    try:
        reloj = _dict(reloj)
        motivo = por_que_no(reloj)
        if motivo:
            salida["motivo"] = motivo
            return salida

        from src.actions.la_ronda_de_la_manana import (
            TOPE_POR_VIAJE, juega, la_puja, la_puja_de_la_cartera,
        )

        plantilla, fichas, mercado = _ids(plantilla), _por_id(fichas), _por_id(mercado)
        fichas = {k: v for k, v in fichas.items() if isinstance(v, dict)}
        subidas_de_ayer = _por_id(subidas_de_ayer)
        pujas = {k: _int(v, 0) or 0 for k, v in _por_id(pujas_vivas).items()}
        ofertas = _por_id(ofertas_del_computer)
        en_venta, vendidos, listados = _ids(en_venta), _ids(vendidos), _ids(listados)
        protegidos, no_rotar, aguanta = _ids(protegidos), _ids(no_rotar), _ids(aguanta)
        vetados, otros_venden = _ids(vetados), _ids(otros_venden)
        parejas = _lista(parejas)
        rondas = _int(rondas_jugadas)
        saldo = _int(saldo)
        once = _dict(once) if once is not None else None
        once_ids = [i for i in (_int(x) for x in (once or {}).get("ids") or []) if i is not None]
        # Quien es (o puede ser) titular, para la caja: el once leido y el
        # de la foto. Sin ninguno de los dos no se sabe: cualquiera.
        de_la_foto = None if once_de_la_foto is None else _ids(once_de_la_foto)
        conocidos = set(once_ids) | (de_la_foto or set())
        sabido = bool(conocidos)

        def puede_ser_titular(pid):
            return pid in conocidos if sabido else True

        def precio_de(pid):
            return _int(_dict(fichas.get(pid)).get("price")) or None

        def nunca(pid):
            """Por que no se toca nunca a este de la plantilla (o None)."""
            nombre = _nombre(fichas.get(pid))
            if INTOCABLE in nombre.lower():
                return "YAMAL"
            if not nombre:
                return "SIN_NOMBRE"
            if pid in protegidos:
                return "PROTEGIDO"
            if pid in no_rotar:
                return "NO_ROTAR"
            if pid in aguanta:
                return "LA_CARTERA"
            return None

        salida["activo"] = True
        cambios_al_once, aceptar, publicar, nada = [], [], [], []
        nuevo_once = list(once_ids)
        formacion = (once or {}).get("formacion")
        vende_ahora = set()
        # Los que salen de una pareja ganada y no se van a vender (o no se
        # sabe): su cobro NO cuenta en la caja de las pujas.
        sin_cobro = {}

        # 7. LA VENTA de las parejas ganadas: el que entra ya esta.
        no_vende = por_que_no_vende(reloj)
        salida["por_que_no_vende"] = no_vende
        # Sin saldo no se sabe si esta en rojo: no se da prisa por eso.
        en_rojo = saldo is not None and saldo - sum(pujas.values()) < 0
        con_prisa = en_rojo or not se_cobra_antes(reloj, HORAS_PARA_COBRAR)
        # El relevo en el once nunca es otro que sale, ni lo vendido o
        # publicado en esta vuelta, ni lo que otro vende sin mirar el once
        # (la cartera, otro libro): volveria el hueco.
        salen = {_int(p.get("sale")) for p in parejas if p.get("estado") in ABIERTAS}
        no_valen = vendidos | listados | salen | aguanta | otros_venden
        for p in parejas:
            if p.get("estado") != GANADA:
                continue
            sale, entra = _int(p.get("sale")), _int(p.get("entra"))
            if sale not in plantilla or entra not in plantilla or sale in vendidos:
                continue

            def frena(motivo, sale=sale, p=p):
                sin_cobro[sale] = motivo
                nada.append({"accion": "NADA", "player_id": sale, "pareja": p.get("id"),
                             "motivo": motivo})

            # El que entro lo vendio otro en esta vuelta: la pareja esta rota
            # (`al_dia` la cierra) y el que iba a salir no se vende.
            if entra in vendidos:
                frena("EL_QUE_ENTRO_SE_VENDIO_EN_ESTA_VUELTA")
                continue
            por = nunca(sale)
            valor = precio_de(sale)
            if por is None and valor is None:
                por = "SIN_VALOR"
            if por:
                frena(por)
                continue
            # Lo que ya se sabe que frenara la venta, haya oferta o no: su
            # cobro no cuenta (con la ronda jugandose tambien: se vende
            # despues, si nada lo frena).
            if puede_ser_titular(sale) and reloj.get("ronda_parcial"):
                sin_cobro[sale] = "TITULAR_ANTES_DE_UNA_RONDA_PARCIAL"
            elif puede_ser_titular(sale) and el_relevo(
                    sale, entra, conocidos, plantilla, fichas, rondas,
                    no_valen=no_valen | vende_ahora) is None:
                sin_cobro[sale] = "SIN_RELEVO_PARA_EL_ONCE"
            if no_vende:
                nada.append({"accion": "NADA", "player_id": sale, "pareja": p.get("id"),
                             "motivo": no_vende})
                continue
            suelo = math.ceil(valor * (ACEPTA_CON_PRISA if con_prisa else ACEPTA))
            oferta = _dict(ofertas.get(sale))
            importe, offer_id = _int(oferta.get("amount"), 0) or 0, _int(oferta.get("offer_id"))
            if offer_id and importe >= suelo:
                if once is None or not once_ids:
                    salida["necesita_el_once"] = salida["necesita_el_once"] or once is None
                    frena("FALTA_LEER_EL_ONCE" if once is None else "SIN_ONCE_DE_BIWENGER")
                    continue
                requiere = sale in nuevo_once
                if requiere and reloj.get("ronda_parcial"):
                    frena("TITULAR_ANTES_DE_UNA_RONDA_PARCIAL")
                    continue
                if requiere:
                    relevo = el_relevo(sale, entra, set(nuevo_once), plantilla, fichas,
                                       rondas, no_valen=no_valen | vende_ahora)
                    if (relevo is None or not formacion or len(nuevo_once) != 11
                            or len(set(nuevo_once)) != 11):
                        frena("SIN_RELEVO_PARA_EL_ONCE" if relevo is None
                              else "ONCE_INCOMPLETO")
                        continue
                    nuevo_once[nuevo_once.index(sale)] = relevo
                    cambios_al_once.append((sale, relevo))
                vende_ahora.add(sale)
                # Se vende ahora: cuenta por su importe (si la aceptacion entra).
                sin_cobro.pop(sale, None)
                aceptar.append({
                    "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": sale,
                    "nombre": _nombre(fichas.get(sale)), "offer_id": offer_id,
                    "importe": importe, "valor": valor, "suelo": suelo,
                    "con_prisa": con_prisa, "pareja": p.get("id"),
                    "requiere_el_once": requiere, "rotacion": True,
                })
            elif sale not in en_venta and sale not in listados:
                publicar.append({"accion": "PONER_A_LA_VENTA", "player_id": sale,
                                 "nombre": _nombre(fichas.get(sale)), "precio": valor,
                                 "pareja": p.get("id"), "rotacion": True})
            else:
                nada.append({"accion": "NADA", "player_id": sale, "pareja": p.get("id"),
                             "motivo": (f"publicado; la oferta del Computer ({importe}) no "
                                        f"llega a {suelo}" if offer_id else
                                        "publicado; esperando la oferta del Computer")})
        salida["sin_cobro"] = dict(sin_cobro)

        acciones = []
        if cambios_al_once:
            acciones.append({"accion": "CAMBIAR_EL_ONCE", "once": list(nuevo_once),
                             "formacion": formacion,
                             "salen": [s for s, _ in cambios_al_once],
                             "entran": [e for _, e in cambios_al_once], "rotacion": True})
        acciones += aceptar + publicar

        # 6. LA CAJA, la de todos los motores, con lo que ya se espera
        # cobrar por las parejas ganadas: lo aceptado ahora, por su
        # importe; el publicado (o que se publica ahora), al 95 % si su
        # oferta llega en el proximo reset y antes de la ronda. Nunca el
        # de una venta frenada (`sin_cobro`): con el, una puja que gasta
        # pasaba con el saldo en rojo.
        llega_una = se_cobra_antes(reloj, HORAS_UN_RESET)
        cobros, contados = 0, set()
        aceptadas = {a["player_id"]: a["importe"] for a in aceptar}
        publicados = en_venta | listados | {a["player_id"] for a in publicar}
        for p in parejas:
            sale, entra = _int(p.get("sale")), _int(p.get("entra"))
            if (p.get("estado") != GANADA or sale in contados or sale not in plantilla
                    or entra not in plantilla or sale in vendidos or entra in vendidos):
                continue
            contados.add(sale)
            if sale in aceptadas:
                cobros += aceptadas[sale]
            elif sale in sin_cobro:
                continue
            elif llega_una and sale in publicados and precio_de(sale):
                cobros += int(precio_de(sale) * VENTA_ESTIMADA)
        caja = None if saldo is None else saldo - sum(pujas.values()) + cobros
        # La misma caja sin lo aceptado en esta vuelta: la puja que solo
        # cabe con ello no se manda si la aceptacion no entra (`escribir`).
        caja_sin = None if caja is None else caja - sum(aceptadas.values())
        salida["caja"] = {"saldo": saldo, "pujas_vivas": sum(pujas.values()),
                          "cobros_esperados": cobros,
                          "aceptado_en_esta_vuelta": sum(aceptadas.values()),
                          "antes": caja, "despues": caja}

        # 4. EL CUPO.
        cupo = el_cupo(parejas, reloj.get("ventana"), reloj.get("semana"))
        salida["cupo"] = dict(cupo)

        no_puja = por_que_no_puja(reloj)
        if no_puja is None and cupo["quedan"] <= 0:
            no_puja = "SIN_CUPO"
        if no_puja is None and caja is None:
            no_puja = "SIN_SALDO"
        if no_puja is None and not rondas:
            no_puja = "SIN_JORNADAS"
        salida["por_que_no_puja"] = no_puja

        # 1. LOS QUE CAEN.
        emparejados = set()
        pujados_hoy = set()
        for p in parejas:
            if p.get("estado") in ABIERTAS:
                emparejados |= {_int(p.get("sale")), _int(p.get("entra"))}
            if p.get("dia") == reloj.get("dia"):
                pujados_hoy.add(_int(p.get("sale")))
        caidos, no_rota = [], []
        for pid in sorted(plantilla):
            f = _dict(fichas.get(pid))
            hoy, ayer = _int(f.get("priceIncrement")), _int(subidas_de_ayer.get(pid))
            if hoy is None or ayer is None or hoy > 0 or ayer > 0:
                continue
            por = nunca(pid)
            if por is None and pid in emparejados:
                por = "YA_EN_UNA_PAREJA"
            if por is None and (pid in vendidos or pid in listados):
                por = "VENDIDO_O_PUBLICADO_EN_ESTA_VUELTA"
            if por is None and pid in otros_venden:
                por = "LO_VENDE_OTRO_LIBRO"
            if por is None and _int(f.get("position")) not in POSICIONES:
                por = "SIN_POSICION"
            xp = el_xp(f, rondas)
            if por is None and (precio_de(pid) is None or xp is None):
                por = "SIN_VALOR"
            if por is None and pid in pujados_hoy:
                por = "UNA_PUJA_AL_DIA"
            if por:
                no_rota.append({"player_id": pid, "nombre": _nombre(f) or None, "por": por})
                continue
            caidos.append({"player_id": pid, "nombre": _nombre(f), "posicion": _int(f.get("position")),
                           "precio": precio_de(pid), "hoy": hoy, "ayer": ayer, "xp": xp})
        caidos.sort(key=lambda c: (c["hoy"], c["xp"], c["player_id"]))
        salida["caidos"] = caidos
        salida["no_rota"] = no_rota

        if no_puja is not None:
            salida["acciones"] = acciones + nada
            return salida

        # 2. LOS QUE ENTRAN: ni lo que esta en el libro de otro (lo que
        # aguanta la cartera, lo que otro vende) ni un `fichar` del gestor.
        candidatos = []
        for pid, pide in mercado.items():
            f = _dict(fichas.get(pid))
            pide = _int(pide) or precio_de(pid)
            sube = _int(f.get("priceIncrement"), 0) or 0
            if (not pide or pid in plantilla or pid in pujas or pid in vetados
                    or pid in emparejados or pid in aguanta or pid in otros_venden
                    or pid in protegidos or sube <= 0
                    or str(f.get("status") or "").strip().lower() != "ok"
                    or _int(f.get("position")) not in POSICIONES or not juega(f)):
                continue
            if la_puja(pide) > TOPE_POR_VIAJE:
                continue
            candidatos.append({"player_id": pid, "nombre": _nombre(f), "posicion": _int(f.get("position")),
                               "pide": pide, "sube": sube, "xp": el_xp(f, rondas),
                               "puja": min(la_puja_de_la_cartera(pide, sube), TOPE_POR_VIAJE)})
        # El de mas xP; a igualdad, el que mas sube en proporcion.
        candidatos.sort(key=lambda c: (-c["xp"], -c["sube"] / c["pide"], c["player_id"]))

        # 5. UNO POR OTRO.
        quedan = cupo["quedan"]
        disponible = _int(maximo_de_puja)
        cobra = se_cobra_antes(reloj, HORAS_PARA_COBRAR)
        pujar, usados = [], set()
        for c in caidos:
            if quedan <= 0:
                break
            # Su venta cuenta solo si se cobra antes de la ronda y no la
            # frenara la ronda de aplazados (titular, o no se sabe).
            frenada = bool(reloj.get("ronda_parcial")) and puede_ser_titular(c["player_id"])
            venta = int(c["precio"] * VENTA_ESTIMADA) if cobra and not frenada else 0
            for e in candidatos:
                if e["player_id"] in usados or e["posicion"] != c["posicion"]:
                    continue
                if e["xp"] < c["xp"] - TOLERANCIA_XP:
                    continue
                if disponible is not None and e["puja"] > disponible:
                    continue
                despues = caja - e["puja"] + venta
                if not (despues >= 0 or despues >= caja):
                    continue
                despues_sin = caja_sin - e["puja"] + venta
                cuenta_con = not (despues_sin >= 0 or despues_sin >= caja_sin)
                caja, caja_sin = despues, despues_sin
                if disponible is not None:
                    disponible -= e["puja"]
                usados.add(e["player_id"])
                quedan -= 1
                pareja = {
                    "id": f"{c['player_id']}>{e['player_id']}@{reloj.get('dia')}",
                    "sale": c["player_id"], "entra": e["player_id"], "estado": PUJADA,
                    "dia": reloj.get("dia"), "semana": reloj.get("semana"),
                    "ventana": reloj.get("ventana"), "puja": e["puja"], "pide": e["pide"],
                    "sube": e["sube"], "precio_sale": c["precio"],
                    "xp_sale": round(c["xp"], 3), "xp_entra": round(e["xp"], 3),
                    "se_cobra_antes": bool(venta),
                }
                salida["parejas_nuevas"].append(pareja)
                pujar.append({
                    "accion": "PUJAR", "player_id": e["player_id"], "nombre": e["nombre"],
                    "importe": e["puja"], "pide": e["pide"], "sube": e["sube"],
                    "sustituye": None, "sale": c["player_id"], "nombre_sale": c["nombre"],
                    "xp_sale": pareja["xp_sale"], "xp_entra": pareja["xp_entra"],
                    "pareja": pareja["id"], "rotacion": True,
                    "cuenta_con_lo_aceptado": sorted(aceptadas) if cuenta_con else [],
                })
                break
        salida["caja"]["despues"] = caja
        salida["acciones"] = acciones + pujar + nada
        return salida
    except Exception as error:                      # noqa: BLE001
        return {**salida, "activo": False, "acciones": [], "parejas_nuevas": [],
                "motivo": f"ERROR: {type(error).__name__}: {error}"}


# ============================================================
# EL LIBRO
# ============================================================

def el_registro(ruta=None) -> list:
    """Las lineas del registro (`REGISTRO`), en orden. Las que no se leen
    se saltan. Nunca lanza."""
    lineas = []
    try:
        for texto in Path(ruta or REGISTRO).read_text(encoding="utf-8").splitlines():
            try:
                linea = json.loads(texto)
            except Exception:                       # noqa: BLE001
                continue
            if isinstance(linea, dict):
                lineas.append(linea)
    except Exception:                               # noqa: BLE001
        pass
    return lineas


def rehacer(lineas) -> list:
    """
    Las parejas, de las lineas del registro en orden: cada PUJAR trae la
    pareja (`nueva`, PUJADA o FALLIDA); GANADA, PERDIDA, VENDIDA y ROTA
    le cambian el estado; la aceptacion que entro la vende y la
    publicacion que entro la apunta. Lo mismo que hizo `apuntar`. Pura,
    nunca lanza.
    """
    parejas = {}
    try:
        for linea in _lista(lineas):
            evento, cual = linea.get("evento"), linea.get("pareja")
            if evento == "PUJAR" and isinstance(linea.get("nueva"), dict):
                nueva = dict(linea["nueva"])
                parejas[nueva.get("id") or cual] = nueva
                continue
            p = parejas.get(cual)
            if p is None:
                continue
            exito = bool(linea.get("exito")) and linea.get("enviada") is not False
            if evento in (GANADA, PERDIDA, VENDIDA, ROTA):
                p["estado"] = evento
                if evento == GANADA:
                    p["llego_en"] = linea.get("at")
            elif evento == "ACEPTAR_OFERTA_DEL_COMPUTER" and exito:
                p.update({"estado": VENDIDA, "vendida_en": linea.get("at"),
                          "importe_venta": linea.get("importe")})
            elif evento == "PONER_A_LA_VENTA" and exito:
                p["publicado_en"] = linea.get("at")
    except Exception:                               # noqa: BLE001
        pass
    return list(parejas.values())


def leer_libro(ruta=None, registro_ruta=None) -> dict:
    """
    `{"parejas": [...]}`. Si el estado falta o no se lee (la cache se
    desalojo: el registro vuelve de git), o es mas viejo que la ultima
    linea del registro (`actualizado` < su `at`), se rehace del registro
    (`rehecho`: True). El registro, `registro_ruta` o el del estado con
    `.jsonl` (`LIBRO` -> `REGISTRO`). Vacio si no hay ninguno. Nunca
    lanza.
    """
    try:
        ruta = Path(ruta or LIBRO)
    except Exception:                               # noqa: BLE001
        return {"parejas": []}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        libro = ({**datos, "parejas": _lista(datos.get("parejas"))}
                 if isinstance(datos, dict) else None)
    except Exception:                               # noqa: BLE001
        libro = None
    try:
        lineas = el_registro(registro_ruta or ruta.with_suffix(".jsonl"))
        if lineas:
            ultima = _cuando(lineas[-1].get("at"))
            actualizado = _cuando(libro.get("actualizado")) if libro else None
            if libro is None or (actualizado is not None and ultima is not None
                                 and ultima > actualizado):
                return {"parejas": rehacer(lineas), "rehecho": True}
    except Exception:                               # noqa: BLE001
        pass
    return libro if libro is not None else {"parejas": []}


def las_parejas_abiertas(libro_ruta=None, libro=None) -> dict:
    """
    Para los demas motores, con la rotacion encendida: los que salen de
    las parejas abiertas (PUJADA y GANADA: la rotacion los vende cuando
    llega su relevo), los que entran, y los que ya se van (GANADA: su
    relevo esta dentro). `libro` ya leido (las guardias) o de
    `libro_ruta`. Apagada, todo vacio. Nunca lanza.
    """
    salida = {"salen": set(), "entran": set(), "se_van": set()}
    try:
        if not activa():
            return salida
        libro = leer_libro(libro_ruta) if libro is None else _dict(libro)
        for p in _lista(libro.get("parejas")):
            sale, entra, estado = _int(p.get("sale")), _int(p.get("entra")), p.get("estado")
            if estado not in ABIERTAS:
                continue
            if sale is not None:
                salida["salen"].add(sale)
                if estado == GANADA:
                    salida["se_van"].add(sale)
            if entra is not None:
                salida["entran"].add(entra)
    except Exception:                               # noqa: BLE001
        return {"salen": set(), "entran": set(), "se_van": set()}
    return salida


def los_que_rota(libro_ruta=None) -> set:
    """
    Los que salen de una pareja con la puja todavia viva (PUJADA) y la
    rotacion encendida: ni el motor viejo ni nadie que mire esto los
    vende hasta saber si el que entra llega. Vacio si esta apagada.
    Nunca lanza.
    """
    try:
        if not activa():
            return set()
        return {s for s in (_int(p.get("sale")) for p in leer_libro(libro_ruta)["parejas"]
                            if p.get("estado") == PUJADA) if s is not None}
    except Exception:                               # noqa: BLE001
        return set()


def no_rotados(ruta=None, ahora=None) -> set:
    """Los `no_rotar` de la orden viva del gestor. Vacio si la orden esta
    apagada, caducada o no vale. Nunca lanza."""
    try:
        from src.actions import la_orden_del_gestor as orden_mod

        if not orden_mod.activa():
            return set()
        orden = orden_mod.leer_la_orden(ruta)
        if orden_mod.validar(orden, _utc(ahora)):
            return set()
        return _ids(_dict(n).get("player_id") for n in orden.get("no_rotar") or []
                    if isinstance(n, dict))
    except Exception:                               # noqa: BLE001
        return set()


def las_jornadas_jugadas(fichas=None, ruta=None) -> int | None:
    """Las jornadas cerradas (la mayor de `JORNADAS`); si no, el mayor
    numero de partidos jugados del catalogo. Nunca lanza."""
    try:
        mayor = None
        for linea in Path(ruta or JORNADAS).read_text(encoding="utf-8").splitlines():
            try:
                j = _int(json.loads(linea).get("jornada"))
            except Exception:                       # noqa: BLE001
                continue
            if j and (mayor is None or j > mayor):
                mayor = j
        if mayor:
            return mayor
    except Exception:                               # noqa: BLE001
        pass
    try:
        jugados = [(_int(f.get("playedHome"), 0) or 0) + (_int(f.get("playedAway"), 0) or 0)
                   for f in _por_id(fichas).values() if isinstance(f, dict)]
        return (max(jugados) or None) if jugados else None
    except Exception:                               # noqa: BLE001
        return None


def lo_de_esta_vuelta(v10, vuelta_mejora, plan_cierre, ahora, run_id=None,
                      vuelta_parte=None) -> dict:
    """
    Lo que ESTA vuelta ya pujo, retiro, cobro y publico antes de la
    rotacion (la foto es de antes): v10 (ronda, chollos, orden, carril,
    escaparate), la mejora, el cierre y el parte (`el_parte_vuelta.json`,
    mismo formato que el de la mejora), con las mismas pruebas de vuelta
    que el parte. `{"pujas", "canceladas", "vendidos", "listados",
    "descartados"}`. Nunca lanza.
    """
    salida = {"pujas": {}, "canceladas": set(), "vendidos": {}, "listados": set(),
              "descartados": []}
    try:
        from src.actions.el_cierre_de_la_jornada import (
            la_vuelta_de_la_mejora, lo_de_esta_vuelta as _de_la_vuelta,
        )
        from src.actions.la_mejora_del_once import es_de_esta_vuelta

        ahora = _utc(ahora)
        descartado = es_de_esta_vuelta(v10, ahora, run_id)
        de_la_vuelta = {} if descartado else dict(_dict(v10))
        if descartado:
            salida["descartados"].append(f"v10: {descartado}")
        hechas_mejora, d_mejora = la_vuelta_de_la_mejora(vuelta_mejora, ahora, run_id)
        hechas_cierre, d_cierre = la_vuelta_de_la_mejora(plan_cierre, ahora, run_id)
        if d_mejora:
            salida["descartados"].append(f"mejora: {d_mejora}")
        if d_cierre:
            salida["descartados"].append(f"cierre: {d_cierre}")
        # El parte, si escribio (apagado no hay fichero: no se dice nada).
        hechas_parte, d_parte = la_vuelta_de_la_mejora(vuelta_parte, ahora, run_id)
        if d_parte and _dict(vuelta_parte):
            salida["descartados"].append(f"parte: {d_parte}")
        de_la_vuelta["la_mejora_del_once"] = {"hechas": hechas_mejora}
        de_la_vuelta["el_cierre_de_la_jornada"] = {"hechas": hechas_cierre}
        de_la_vuelta["el_parte_vende"] = {"hechas": hechas_parte}
        salida.update(_de_la_vuelta(de_la_vuelta))
    except Exception as error:                      # noqa: BLE001
        salida["descartados"].append(f"lo de esta vuelta: {type(error).__name__}")
    return salida


def leer_el_once(escritor) -> dict | None:
    """La alineacion vigente en Biwenger AHORA (la misma lectura que la
    foto: `GET /user?fields=*,lineup(*,players(*))`), con el cliente del
    escritor. `{"ids": [...] en orden, "formacion"}`; None si no se lee."""
    try:
        from src.analysis.el_once_que_jugo import ids_del_once, once_del_dueno

        cliente = escritor.client
        r = cliente.session.get(f"{cliente.BASE_URL}/user",
                                params={"fields": "*,lineup(*,players(*))"}, timeout=30)
        r.raise_for_status()
        return el_once_de(once_del_dueno({"user_lineup": r.json()}), ids_del_once)
    except Exception:                               # noqa: BLE001
        return None


def el_once_de(alineacion, ids_del_once=None) -> dict | None:
    """`{"ids", "formacion"}` de `user_lineup.data.lineup` (`type`,
    `players`). None si no trae jugadores. Nunca lanza."""
    try:
        if ids_del_once is None:
            from src.analysis.el_once_que_jugo import ids_del_once
        alineacion = _dict(alineacion)
        ids = ids_del_once(alineacion)
        if not ids:
            return None
        return {"ids": [int(i) for i in ids], "formacion": alineacion.get("type")}
    except Exception:                               # noqa: BLE001
        return None


def escribir(acciones, escritor, rastro_ruta=None) -> list:
    """
    Manda las escrituras en orden. El once primero; la venta de un
    titular (`requiere_el_once`) solo si Biwenger dijo que el once se
    guardo. Si una aceptacion no entra (o no se manda), las pujas que
    solo cabian con ella (`cuenta_con_lo_aceptado`) tampoco: quedan con
    `SIN_EL_COBRO` y sin mandar (la vuelta siguiente lo vuelve a mirar
    con la caja de verdad). Lo demas, por `la_orden_del_gestor.ejecutar`.
    Nunca lanza.
    """
    from src.actions.la_orden_del_gestor import ejecutar

    hechas, once_guardado, sin_cobrar = [], False, set()
    for a in _lista(acciones):
        try:
            if a.get("accion") == "NADA":
                continue
            if a.get("accion") == "PUJAR" and set(_ids(a.get("cuenta_con_lo_aceptado"))) & sin_cobrar:
                hechas.append({**a, "enviada": False, "exito": False, "error": SIN_EL_COBRO})
                continue
            if a.get("accion") == "CAMBIAR_EL_ONCE":
                # Como el orquestador (`autopilot_executor`): sin reservas.
                r = _dict(escritor.save_lineup(player_ids=list(a["once"]),
                                               formation=a["formacion"],
                                               reserve_ids=[], execute=True))
                once_guardado = bool(r.get("sent")) and bool(r.get("success"))
                hechas.append({**a, "enviada": bool(r.get("sent")), "exito": r.get("success"),
                               "http_status": r.get("http_status")})
                try:
                    from src.actions.el_rastro import apuntar_escritura

                    apuntar_escritura(
                        "alineacion", resultado=r,
                        contenido={"player_ids": sorted(int(x) for x in a["once"]),
                                   "formation": a["formacion"]},
                        extra={"formation": a["formacion"], "player_ids": list(a["once"]),
                               "modulo": "la_rotacion"},
                        ruta=Path(rastro_ruta) if rastro_ruta else None)
                except Exception:                   # noqa: BLE001
                    pass
                continue
            if a.get("requiere_el_once") and not once_guardado:
                hechas.append({**a, "enviada": False, "error": "EL_ONCE_NO_SE_GUARDO"})
                if a.get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER":
                    sin_cobrar.add(_int(a.get("player_id")))
                continue
            hecha = ejecutar([a], escritor)
            hechas.extend(hecha)
            if a.get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER" and not any(
                    h.get("exito") and h.get("enviada") is not False for h in _lista(hecha)):
                sin_cobrar.add(_int(a.get("player_id")))
        except Exception as error:                  # noqa: BLE001
            hechas.append({**a, "enviada": False, "error": f"{type(error).__name__}: {error}"})
            if _dict(a).get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER":
                sin_cobrar.add(_int(_dict(a).get("player_id")))
    return hechas


def apuntar(libro, parejas, eventos, hechas, nuevas, ahora, libro_ruta=None,
            registro_ruta=None) -> dict:
    """
    El libro despues de la vuelta: las parejas al dia, las nuevas
    (PUJADA si la puja entro; FALLIDA si no: cuenta para una puja al dia
    pero no gasta cupo; la que no se mando por `SIN_EL_COBRO`, ninguna:
    se vuelve a mirar en la vuelta siguiente), la venta y la
    publicacion. Se escribe el estado y una linea por cada cosa que paso
    en el registro (la de cada PUJAR, con la pareja entera: `nueva`, para
    `rehacer`); el registro, `registro_ruta` o el del estado con
    `.jsonl`. Lo cerrado hace mas de `DIAS_EN_EL_LIBRO` sale del estado
    (no del registro). Un libro rehecho del registro se escribe aunque no
    cambie nada. Nunca lanza; devuelve `{"parejas", "lineas", "escrito"}`.
    """
    salida = {"parejas": [], "lineas": [], "escrito": False}
    try:
        ahora = _utc(ahora)
        cuando = ahora.isoformat()
        parejas = [dict(p) for p in _lista(parejas)]
        por_id = {p.get("id"): p for p in parejas}
        nuevas = {p.get("id"): dict(p) for p in _lista(nuevas)}
        lineas = [{"at": cuando, **e} for e in _lista(eventos)]
        for h in _lista(hechas):
            accion, pareja = h.get("accion"), h.get("pareja")
            exito = bool(h.get("exito")) and h.get("enviada") is not False
            nueva = None
            if accion == "PUJAR" and pareja in nuevas and h.get("error") == SIN_EL_COBRO:
                nuevas.pop(pareja)
            elif accion == "PUJAR" and pareja in nuevas:
                p = nuevas.pop(pareja)
                p.update({"estado": PUJADA if exito else FALLIDA, "pujada_en": cuando})
                parejas.append(p)
                por_id[pareja] = p
                nueva = dict(p)
            elif accion == "ACEPTAR_OFERTA_DEL_COMPUTER" and exito and pareja in por_id:
                por_id[pareja].update({"estado": VENDIDA, "vendida_en": cuando,
                                       "importe_venta": h.get("importe")})
            elif accion == "PONER_A_LA_VENTA" and exito and pareja in por_id:
                por_id[pareja]["publicado_en"] = cuando
            lineas.append({"at": cuando, "evento": accion, "pareja": pareja,
                           "player_id": h.get("player_id"), "importe": h.get("importe"),
                           "precio": h.get("precio"), "sale": h.get("sale"),
                           "salen": h.get("salen"), "entran": h.get("entran"),
                           "exito": h.get("exito"), "enviada": h.get("enviada"),
                           "http_status": h.get("http_status"), "error": h.get("error"),
                           **({"nueva": nueva} if nueva else {})})
        limite = ahora - timedelta(days=DIAS_EN_EL_LIBRO)
        quedan = []
        for p in parejas:
            fecha = _cuando(p.get("pujada_en"))
            if p.get("estado") not in ABIERTAS and fecha is not None and fecha < limite:
                continue
            quedan.append(p)
        salida["parejas"], salida["lineas"] = quedan, lineas
        if (quedan == _lista(_dict(libro).get("parejas")) and not lineas
                and not _dict(libro).get("rehecho")):
            return salida
        ruta = Path(libro_ruta or LIBRO)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"version": 1, "actualizado": cuando, "parejas": quedan},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if lineas:
            registro = (Path(registro_ruta) if registro_ruta
                        else Path(libro_ruta or LIBRO).with_suffix(".jsonl"))
            registro.parent.mkdir(parents=True, exist_ok=True)
            with registro.open("a", encoding="utf-8") as fh:
                for linea in lineas:
                    fh.write(json.dumps(linea, ensure_ascii=False, default=str) + "\n")
        salida["escrito"] = True
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


def correr(cycle=None, escritor_factory=None, ahora: datetime | None = None, *,
           calendario=None, orden_ruta=None, libro_ronda_ruta=None, libro_ruta=None,
           registro_ruta=None, historico=None, rondas_jugadas=None, otros_venden=None,
           v10=None, vuelta_mejora=None, plan_cierre=None, lector_del_once=None,
           rastro_ruta=None, vuelta_parte=None) -> dict:
    """
    La rotacion, en esta vuelta. Nunca lanza.

    Lo que no se pasa se lee de produccion: la foto de `cycle["snapshot"]`
    (sin `cycle`, la ultima `snapshot_*.json`, como el parte), el
    calendario de los chollos, la orden del gestor (`orden_ruta`), el
    libro de la ronda (`libro_ronda_ruta`), el suyo (`libro_ruta`,
    `registro_ruta`), el historico de precios (`historico`), las jornadas
    jugadas, los libros de los demas (`otros_venden`; el `vender` del
    plan fresco del cierre se suma siempre) y lo que esta vuelta ya hizo
    (`v10`, `vuelta_mejora`, `plan_cierre`, `vuelta_parte`). El once
    vigente se lee con `lector_del_once(escritor)` (por defecto
    `leer_el_once`) solo si hay una venta que hacer; para la caja vale
    tambien el de la foto. Apagada, no lee ni escribe nada.
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "decision": None}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.el_cierre_de_la_jornada import las_pujas_vivas
        from src.actions.la_orden_del_gestor import (
            _pid, leer_la_foto, protegidos, vetados,
        )
        from src.actions.la_ronda_de_la_manana import los_que_aguanta
        from src.actions.los_chollos import CALENDARIO, _puede_escribir
        from src.analysis.los_que_otros_venden import lo_que_vende_el_cierre, quien_los_vende
        from src.analysis.zona_de_silencio import en_la_franja

        ahora = _utc(ahora)

        # CUANDO: en la zona de silencio o sin calendario, nada (y sin
        # leer nada mas). De 04:45 a 07:00 nunca, tampoco en las vueltas
        # puestas a proposito (04:45 y 04:50, que `_puede_escribir` deja
        # pasar): son de la ventana, y la subasta del reset que v10 puja en
        # ellas no esta en ningun fichero de la vuelta (la caja no la ve).
        cal = CALENDARIO if calendario is None else calendario
        reloj = el_reloj(ahora, cal, bool(_puede_escribir(ahora)) and not en_la_franja(ahora))
        salida["reloj"] = reloj
        motivo = por_que_no(reloj)
        if motivo:
            salida["motivo"] = motivo
            salida["detalle"] = MOTIVOS.get(motivo)
            return salida

        if cycle is None:
            from src.actions.la_mejora_del_once import _la_ultima_foto

            snapshot = _la_ultima_foto()
        else:
            snapshot = _dict(cycle).get("snapshot")
        snapshot = _dict(snapshot)

        yo = _pid(_dict(snapshot.get("league")).get("user"))
        if yo is None:
            salida["motivo"] = "SIN_SABER_QUIEN_SOY"
            return salida
        foto = leer_la_foto(snapshot, yo)

        catalogo = _dict(_dict(_dict(snapshot.get("catalog")).get("data")).get("players"))
        fichas = {k: v for k, v in _por_id(catalogo).items() if isinstance(v, dict)}
        for j in _lista(snapshot.get("my_team")):
            pid = _int(j.get("id"))
            if pid is not None and pid not in fichas:
                fichas[pid] = j

        # Lo que esta vuelta ya pujo, retiro, cobro y publico.
        if v10 is None or vuelta_mejora is None or plan_cierre is None or vuelta_parte is None:
            from src.actions.el_cierre_de_la_jornada import PLAN, VUELTA_MEJORA
            from src.actions.el_parte_vende import VUELTA_PARTE
            from src.actions.la_mejora_del_once import V10

            v10 = _leer(V10, {}) if v10 is None else v10
            vuelta_mejora = _leer(VUELTA_MEJORA, {}) if vuelta_mejora is None else vuelta_mejora
            plan_cierre = _leer(PLAN, {}) if plan_cierre is None else plan_cierre
            vuelta_parte = _leer(VUELTA_PARTE, {}) if vuelta_parte is None else vuelta_parte
        vuelta = lo_de_esta_vuelta(v10, vuelta_mejora, plan_cierre, ahora,
                                   os.environ.get("GITHUB_RUN_ID"), vuelta_parte)
        salida["vuelta_descartada"] = vuelta["descartados"]
        pujas_vivas = {pid: _int(_dict(p).get("amount"), 0) or 0
                       for pid, p in las_pujas_vivas(foto, vuelta).items()}

        # Las parejas, al dia con la foto y con lo vendido en esta vuelta
        # (el que entro, vendido por otro: ROTA).
        libro = leer_libro(libro_ruta, registro_ruta)
        salida["libro_rehecho"] = bool(libro.get("rehecho"))
        parejas, eventos = al_dia(libro["parejas"], plantilla=foto["plantilla"],
                                  pujas_de_la_foto=set(foto["nuestras_pujas"]),
                                  foto_en=snapshot.get("timestamp"), ahora=ahora,
                                  vendidos=set(vuelta["vendidos"]))

        # Lo que subio ayer, del historico de precios.
        if historico is None:
            historico = _dict(_dict(_leer(HISTORICO, {})).get("players"))
        historico = _dict(historico)
        subidas_de_ayer = {pid: la_subida_de_ayer(historico.get(str(pid)), ahora)
                           for pid in foto["plantilla"]}
        if rondas_jugadas is None:
            rondas_jugadas = las_jornadas_jugadas(fichas)
        if otros_venden is None:
            # Sin el cierre (sus `candidatos` son todo el banquillo) y sin
            # la propia rotacion.
            otros_venden = set(quien_los_vende({"cierre": None, "rotacion": None}, ahora))
        # Del cierre, lo que ya eligio vender (`vender` de su plan fresco):
        # ya cuenta con ese dinero para la jornada; emparejarlo lo contaria
        # dos veces.
        otros_venden = _ids(otros_venden) | lo_que_vende_el_cierre(plan_cierre, ahora)
        # El once de la foto, para la caja (quien puede ser titular).
        try:
            from src.analysis.el_once_que_jugo import once_del_dueno

            once_de_la_foto = (el_once_de(once_del_dueno(snapshot)) or {}).get("ids") or None
        except Exception:                           # noqa: BLE001
            once_de_la_foto = None

        base = dict(
            plantilla=foto["plantilla"], fichas=fichas, mercado=foto["mercado"],
            subidas_de_ayer=subidas_de_ayer, rondas_jugadas=rondas_jugadas,
            saldo=foto.get("saldo"), pujas_vivas=pujas_vivas,
            maximo_de_puja=foto.get("maximo_de_puja"),
            ofertas_del_computer=foto["ofertas_del_computer"],
            en_venta=set(foto["en_venta"]) | set(vuelta["listados"]), parejas=parejas,
            protegidos=protegidos(orden_ruta, ahora), no_rotar=no_rotados(orden_ruta, ahora),
            aguanta=los_que_aguanta(libro_ronda_ruta), vetados=vetados(orden_ruta, ahora),
            otros_venden=otros_venden, vendidos=set(vuelta["vendidos"]),
            listados=set(vuelta["listados"]), once_de_la_foto=once_de_la_foto, reloj=reloj,
        )
        d = decidir(**base, once=None)

        # EL ONCE, leido al momento: solo si hay que vender.
        escritor = None
        if d.get("necesita_el_once"):
            if escritor_factory is None:
                from src.biwenger.write_client import BiwengerWriteClient

                escritor_factory = BiwengerWriteClient
            escritor = escritor_factory()
            # Sin leerlo, {}: `decidir` no vende (SIN_ONCE_DE_BIWENGER).
            once = (lector_del_once or leer_el_once)(escritor) or {}
            salida["once_leido"] = once
            d = decidir(**base, once=once)

        salida["decision"] = d
        salida["acciones"] = d["acciones"]

        escrituras = [a for a in d["acciones"] if a.get("accion") != "NADA"]
        if not d.get("activo"):
            salida["motivo"] = d.get("motivo")
        elif not escrituras:
            salida["motivo"] = "NADA_QUE_HACER"
        else:
            if escritor is None:
                if escritor_factory is None:
                    from src.biwenger.write_client import BiwengerWriteClient

                    escritor_factory = BiwengerWriteClient
                escritor = escritor_factory()
            salida["hechas"] = escribir(escrituras, escritor, rastro_ruta)
            salida["motivo"] = "EJECUTADA"

        salida["libro"] = apuntar(libro, parejas, eventos, salida["hechas"],
                                  d.get("parejas_nuevas"), ahora, libro_ruta, registro_ruta)

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida


def el_resumen(r) -> list:
    """Las lineas de la vuelta, para leerlas en el log. Nunca lanza."""
    lineas = []
    try:
        r = _dict(r)
        lineas.append(f"  {r.get('motivo')}"
                      + (f": {r.get('detalle')}" if r.get("detalle") else ""))
        reloj = _dict(r.get("reloj"))
        if reloj:
            lineas.append(f"  Reloj: {reloj.get('horas_ronda')} h a la ronda, "
                          f"{reloj.get('horas_reset')} h al reset, ventana {reloj.get('ventana')}, "
                          f"en curso {reloj.get('en_curso')}")
        for v in r.get("vuelta_descartada") or []:
            lineas.append(f"  Sin contar lo de esta vuelta de {v}")
        if r.get("libro_rehecho"):
            lineas.append("  El estado de las parejas se rehizo del registro")
        d = _dict(r.get("decision"))
        if d.get("sin_cobro"):
            lineas.append(f"  Ventas frenadas (su cobro no cuenta en la caja): {d.get('sin_cobro')}")
        if d.get("por_que_no_puja"):
            lineas.append(f"  No puja: {d.get('por_que_no_puja')}")
        if d.get("por_que_no_vende"):
            lineas.append(f"  No vende: {d.get('por_que_no_vende')}")
        if d.get("cupo"):
            lineas.append(f"  Cupo: {d.get('cupo')}  Caja: {d.get('caja')}")
        for c in _lista(d.get("caidos")):
            lineas.append(f"      cae {c.get('player_id')} {c.get('nombre')} hoy {c.get('hoy')} "
                          f"ayer {c.get('ayer')} xP {round(c.get('xp') or 0, 2)}")
        for n in _lista(d.get("no_rota")):
            lineas.append(f"      no se rota {n.get('player_id')} {n.get('nombre') or ''}: "
                          f"{n.get('por')}")
        for a in _lista(r.get("acciones")):
            importe = a.get("importe") or a.get("precio")
            lineas.append(f"  -> {a.get('accion')} {a.get('player_id') or a.get('salen')} "
                          f"{a.get('nombre') or ''} {importe if importe else ''}"
                          f"{(' sale ' + str(a.get('sale'))) if a.get('sale') else ''}"
                          f"{(' (' + str(a.get('motivo')) + ')') if a.get('motivo') else ''}")
        for h in _lista(r.get("hechas")):
            lineas.append(f"  hecha {h.get('accion')} {h.get('player_id') or h.get('salen')} "
                          f"exito={h.get('exito')} http={h.get('http_status')} "
                          f"{h.get('error') or ''}")
    except Exception as error:                      # noqa: BLE001
        lineas.append(f"  (la rotacion no se pudo escribir: {type(error).__name__})")
    return lineas


def main() -> int:
    r = correr()
    print("=" * 100)
    print("LA ROTACION")
    print("=" * 100)
    for linea in el_resumen(r):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
