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
    jornada. `GANANCIA_MINIMA` sigue en puntos por jornada. Y una
    guardia explícita: un cambio que con el `esperado` de siempre
    (`sin_calendario`) pierde más de `MARGEN_DEL_CALENDARIO` por jornada
    no se hace, por bueno que lo pinten el calendario y el tramo; uno
    que solo financia (pierde a propósito para dar caja) no puede
    perder con el `esperado` más que `PEOR_FINANCIACION`, como apagado.
    Un jugador mucho mejor nunca se vende por un calendario.

    OJO, EL ENCOGIMIENTO TAMBIÉN MUEVE (k = 3 es juicio, no medida): con
    8 partidos el previo pesa un 27 %. Con el panel del 12/10 14:07,
    Yamal pasa de 10,57 a 8,68 puntos por jornada y Hugo Duro de 1,35 a
    1,78; Roberto Fernández de 6,97 a 5,96 (factor 0,977).

    LAS RONDAS, SOLO LAS PRINCIPALES (la regla del dueño): un adelantado
    o un aplazado (el Levante-Athletic de la J6, el 21/10) lo puntúa
    Biwenger con el once que había al empezar SU jornada. No es una
    ronda que se pueda planear: las tres son las tres próximas ventanas
    principales (`proximas_rondas(..., solo_principales=True)`).

    El contexto (ids, duros, tramos, rondas) se monta UNA vez por vuelta
    en `correr`. Sin clasificación o sin calendario, el `esperado` de
    siempre, y el plan lo dice (`plan["calendario"]`). Cada cambio lleva
    en el plan el xP y el factor medio de cada lado, y con qué vara se
    midió (`medida`): si a un lado le falta el xP, los DOS lados van con
    el `esperado` (nunca uno encogido contra otro crudo).

    Nace APAGADO. Apagado, todo es byte a byte lo de antes.

TRES ARREGLOS QUE VAN SIEMPRE (12/10/2026, el análisis del calendario)

    1. La titularidad de LOS NUESTROS sale de `roster.players` (la
       plantilla entera), no solo de `lineup.players`: `todaLaLiga` no
       la trae nunca, y adoptar a uno de la ronda o los chollos que no
       estaba en el once no funcionaba nunca. Quién puede SALIR sigue
       siendo el once. Y al de la ronda o los chollos se le pide LO
       MISMO que al del Computer para entrar: sano, `PARTIDOS_MINIMOS`
       partidos y `TITULARIDAD_MINIMA` de titularidad (los chollos
       compran sin mirar los minutos: un 12 en un partido con un 40 %
       no es un titular).
    2. EL PARTE DEL RELEVO (la misma regla que `la_orden_del_gestor`):
       para COBRAR al que sale, el que entra tiene que estar 'ok' o
       'warned' (catálogo de la foto o `todaLaLiga`). Publicar siempre
       se puede. En rojo y a menos de `HORAS_ROJO` de la jornada se
       cobra igual: un hueco cuesta un jugador; el rojo, el once entero.
    3. La caja cuenta lo que ESTA vuelta ya hizo (la foto es de antes):
       las pujas que ya puso, las de la orden enteras y las de la ronda
       y los chollos al 7 % (se revenden solas), y lo cobrado al
       Computer entra; el vendido ya no cuenta como venta pendiente ni
       como inventario, ni puede salir otra vez, ni es de la plantilla
       para los cambios vivos (ni el que sale se cobra otra vez, ni se
       cobra al que sale si el que se vendió es su relevo). Solo si el
       estado de la vuelta es DE ESTA vuelta: con más de
       `VUELTA_VIEJA_MINUTOS` (o sin hora), no se cuenta nada de él.

SIN FANTASMAS EN LA CAJA (13/10/2026)

    La orden del gestor no cambia sola (vive hasta el 30/11): vendidos
    Jutglà y Rico, se seguían contando como venta pendiente en cada
    vuelta (+3,1 M que ya estaban en el saldo); perdida la puja por su
    relevo, se contaba una venta que no llega nunca y se restaba una
    puja que ya no existe, y los dos quedaban quietos para siempre.
    Ahora (`las_ventas_de_la_orden`, `la_caja_de_la_jornada`): la venta
    de la orden cuenta si el que sale aún es nuestro y su relevo está
    dentro o con puja viva; la de la mejora, si el que sale aún es
    nuestro y el que entra está dentro o con puja viva (lo que `decidir`
    suelta, ahora antes de la caja); un `fichar` sin puja se resta solo
    si sigue en el mercado del Computer. Y el que la orden vende queda
    quieto (`pendientes`) solo si su relevo está dentro, con puja viva o
    aún en el mercado.

    Al final de cada vuelta encendida escribe `VUELTA_MEJORA` (run_id,
    hora, las `hechas`): el cierre de la jornada corre después.

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

from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path


ENV = "BORDALAS_LA_MEJORA_DEL_ONCE"
ENV_CALENDARIO = "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA"     # nace APAGADO
ENV_PUJA_FUERTE = "BORDALAS_LA_MEJORA_PUJA_FUERTE"          # nace APAGADO
ENV_SOLO_SI_SUBE = "BORDALAS_LA_MEJORA_SOLO_SI_SUBE"        # nace APAGADO
ENV_PUJA_EN_9900 = "BORDALAS_LA_PUJA_EN_9900"               # nace APAGADO
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "la_mejora.json"
# Lo que hizo la mejora en ESTA vuelta (13/10/2026), para el cierre de la
# jornada, que corre después: {"run_id", "generated_at", "hechas"}.
VUELTA_MEJORA = RAIZ / "data" / "trading" / "la_mejora_vuelta.json"
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
# Solo las PRINCIPALES: un aplazado se puntúa con el once de su jornada.
RONDAS_DEL_CALENDARIO = 3

# Lo más que el calendario (y el encogimiento) pueden darle la vuelta a la
# vara de siempre: un cambio que con el `esperado` pierde más de esto por
# jornada no se hace por el calendario. El laboratorio: en tres rondas el
# calendario vale ~1,3 puntos por partido en los extremos; el ejemplo del
# dueño es entre delanteros parecidos.
MARGEN_DEL_CALENDARIO = 0.5

# El estado de la vuelta (`v10_full_autonomous_status.json`) más viejo
# que esto respecto a `ahora` es de OTRA vuelta (con un 429 la v10 no lo
# escribe y se queda el de la anterior): no se cuenta.
VUELTA_VIEJA_MINUTOS = 45

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


# LA PUJA FUERTE (13/10/2026). El reset del 13/10: las tres pujas a
# precio + 1 % (E9), perdidas -Ivan Romero y Moi Gomez para Pollo17,
# Gerard Martin para Luismi_Haz-; el libro: 59 ganadas y 14 perdidas, nos
# ganan por 200.000 de mediana. E9 es para revender (el margen manda);
# para el ONCE manda el punto: 1 punto por jornada son ~30.000 EUR de
# premio por cada jornada que queda (29), y lo pagado de mas vuelve en
# buena parte en el valor del jugador. Con el interruptor, la puja de un
# cambio que MEJORA (>= `GANANCIA_MINIMA`) sube `PRIMA_POR_PUNTO` por punto
# por jornada, hasta `PRIMA_MAXIMA` encima del +1 %: +2,25 pts -> +10 %.
# Los que solo financian siguen a +1 %. La caja del cambio cuenta la puja
# de verdad. Nace APAGADA.
PRIMA_POR_PUNTO = 0.04
PRIMA_MAXIMA = 0.12


# SOLO SI SUBE (17/10/2026, laboratorio de la revalorización). La mejora
# no miraba el precio: el 14/10 metió a Luismi Cruz (3.252.000) tras 16
# días seguidos bajando. Verificado (price_history, 18/08-16/10): el que
# no sube hoy sube mañana el 2,4 % de las veces (551/23.301); en la lista
# del Computer, del 17/09 al 08/10, pierde -5,9 % de mediana a 7 días
# (n=369, igual en las dos mitades); las 34 compras de Pepe así, -4,44 M.
# Con el interruptor, el que entra del Computer tiene que subir hoy al
# menos la subida mínima de su tramo (la de la ronda). Única excepción:
# tapar un hueco de verdad (el que sale lesionado, sancionado o con menos
# de `TITULARIDAD_HUECO` de titularidad); ahí, a precio + 1 % como siempre.
TITULARIDAD_HUECO = 50
FUERA_DEL_ONCE = {"injured", "sanctioned"}


def la_mejora_solo_si_sube_activa() -> bool:
    """`BORDALAS_LA_MEJORA_SOLO_SI_SUBE`, leído como `activa`. Nunca lanza."""
    try:
        return str(os.environ.get(ENV_SOLO_SI_SUBE, "")).strip().lower() in {
            "1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def sube_de_verdad(ficha, precio=None) -> bool:
    """
    El de `ficha` (`todaLaLiga`: price, price_increment) sube hoy al menos
    la subida mínima de su tramo de precio (`la_ronda_de_la_manana.
    la_subida_minima`). Sin dato, no. Pura, nunca lanza.
    """
    try:
        from src.actions.la_ronda_de_la_manana import la_subida_minima
        f = ficha or {}
        sube = _int(f.get("price_increment"))
        if sube is None:
            sube = _int(f.get("priceIncrement"))
        minima = la_subida_minima(_int(f.get("price")) or _int(precio))
        return sube is not None and minima is not None and sube > 0 and sube >= minima
    except Exception:                               # noqa: BLE001
        return False


def la_puja_en_9900_activa() -> bool:
    """`BORDALAS_LA_PUJA_EN_9900` (17/10, laboratorio: la puja del once
    terminada en 9.900 gana los empates; ver `la_ronda_de_la_manana.
    en_9900`). Nunca lanza."""
    try:
        return str(os.environ.get(ENV_PUJA_EN_9900, "")).strip().lower() in {
            "1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def la_puja_fuerte_activa() -> bool:
    """`BORDALAS_LA_MEJORA_PUJA_FUERTE`, leído como `activa`. Nunca lanza."""
    try:
        return str(os.environ.get(ENV_PUJA_FUERTE, "")).strip().lower() in {
            "1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def la_puja_fuerte(precio, puntos) -> int:
    """Precio x (1 % + `PRIMA_POR_PUNTO` por punto, hasta `PRIMA_MAXIMA`),
    a miles. Con basura, la de siempre. Pura, nunca lanza."""
    try:
        prima = min(PRIMA_MAXIMA, PRIMA_POR_PUNTO * max(0.0, float(puntos)))
        return int(round(int(precio) * (SUBE + prima), -3))
    except Exception:                               # noqa: BLE001
        try:
            return la_puja(int(precio))
        except Exception:                           # noqa: BLE001
            return 0


def con_puja_fuerte(cambio: dict, precio) -> dict:
    """El cambio con la puja fuerte, si mejora y hay que pujar; si no, tal
    cual. La caja del cambio pasa a contar la puja nueva. Pura."""
    try:
        if (cambio.get("ya_es_nuestro") or not precio
                or cambio.get("puntos") is None or cambio["puntos"] < GANANCIA_MINIMA):
            return cambio
        puja = la_puja_fuerte(precio, cambio["puntos"])
        if puja <= (cambio.get("puja") or 0):
            return cambio
        return {**cambio, "caja": cambio["caja"] + (cambio.get("puja") or 0) - puja,
                "puja": puja, "prima": round(puja / int(precio) - 1, 4)}
    except Exception:                               # noqa: BLE001
        return cambio


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
    puntos y partidos (entonces manda el `esperado` de siempre). Solo
    cuentan las rondas PRINCIPALES (`las_rondas_que_cuentan`), venga
    de donde venga el contexto. Pura, nunca lanza.
    """
    try:
        if not isinstance(ctx, dict) or not ctx.get("available"):
            return None
        if not isinstance(ficha, dict) or prob is None:
            return None
        if ficha.get("points") is None or _int(ficha.get("played")) is None:
            return None
        from src.analysis.el_calendario_de_puntos import factor_medio, xp_jugador

        rondas = las_rondas_que_cuentan(ctx)
        cuantas = len(rondas) or RONDAS_DEL_CALENDARIO
        ctx = {**ctx, "rondas": rondas}
        xp = xp_jugador(ctx, ficha, prob, n=RONDAS_DEL_CALENDARIO)
        if xp is None:
            return None
        factor = factor_medio(ficha.get("team_id"), ficha.get("position"), rondas,
                              ctx.get("ids") or {}, ctx.get("duros") or set(),
                              n=RONDAS_DEL_CALENDARIO)
        return {"xp": float(xp) / cuantas, "factor": float(factor)}
    except Exception:                               # noqa: BLE001
        return None


def las_rondas_que_cuentan(ctx) -> list:
    """
    Las rondas del contexto con las que se valora a un jugador: las
    PRINCIPALES (la que no lo dice, también), las
    `RONDAS_DEL_CALENDARIO` primeras. Un aplazado o un adelantado se
    puntúa con el once de su jornada: no se planea (la regla del dueño,
    12/10/2026). Pura, nunca lanza.
    """
    try:
        rondas = ctx.get("rondas") if isinstance(ctx, dict) else None
        if not isinstance(rondas, (list, tuple)):
            return []
        return [r for r in rondas
                if isinstance(r, dict) and r.get("principal") is not False
                ][:RONDAS_DEL_CALENDARIO]
    except Exception:                               # noqa: BLE001
        return []


def no_vende_a_uno_mejor(cambio) -> bool:
    """
    LA GUARDIA DEL CALENDARIO: con el calendario, un cambio tiene que
    valer también con la vara de siempre (`sin_calendario`, el
    `esperado`):

        el que cuenta como mejora (`puntos` >= `GANANCIA_MINIMA`) no
        puede perder más de `MARGEN_DEL_CALENDARIO` por jornada con el
        `esperado`: el calendario y el tramo desempatan, no venden a
        uno claramente mejor;

        el que solo financia (pierde a propósito para dar caja) no
        puede perder con el `esperado` más que `PEOR_FINANCIACION`,
        lo mismo que apagado.

    Sin `sin_calendario` (sin calendario), vale. Pura, nunca lanza: con
    basura, no.
    """
    try:
        sin = cambio.get("sin_calendario")
        if sin is None:
            return True
        if cambio["puntos"] >= GANANCIA_MINIMA:
            return sin >= -MARGEN_DEL_CALENDARIO
        return sin >= PEOR_FINANCIACION
    except Exception:                               # noqa: BLE001
        return False


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
            salida["rondas"] = [r.get("label") for r in las_rondas_que_cuentan(ctx)]
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
            # EL PEOR CASO (14/10/2026): las pujas de la combinacion se
            # resuelven a la vez y cada una puede perderse. Un cambio que da
            # caja no puede pagar a otro que la quita: si se pierde el
            # primero y se gana el segundo, la jornada empieza en rojo (lo
            # del 14/10: Lemar por Exposito pagaba a Pablo Ramon por Diego
            # Rico). Fuera del rojo, los que dan caja no cuentan (como si se
            # perdieran) y los que la quitan, enteros. En rojo solo valen
            # cambios que dan caja (ni uno que la quite). Lo que ya es
            # nuestro (adoptar) no depende de nadie: cuenta como es.
            def _seguro(c):
                return c["caja"] if c.get("ya_es_nuestro") else min(0, c["caja"])
            if deficit:
                if any(c["caja"] < 0 and not c.get("ya_es_nuestro") for c in combo):
                    continue
                if caja + sum(c["caja"] for c in combo) < minimo_de_caja:
                    continue
            elif caja + sum(_seguro(c) for c in combo) < minimo_de_caja:
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
    estados=None, vendidos=frozenset(), puja_fuerte=None, solo_si_sube=False,
    en_9900=False,
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
        vendidos    {id} que ESTA vuelta ya vendió (la foto es de antes):
                    ya no son de la plantilla. El cambio vivo cuyo `sale`
                    se vendió se suelta (ya vendido); el cuyo `entra` se
                    vendió, también (sin relevo, el que sale se queda).
        solo_si_sube  SOLO SI SUBE (17/10): del Computer solo entra el que
                    sube hoy de verdad (`sube_de_verdad`), salvo para tapar
                    un hueco (el que sale fuera o con poca titularidad)
        en_9900     LA PUJA EN 9.900 (17/10): la puja del que entra termina
                    en 9.900 (`la_ronda_de_la_manana.en_9900`)
    """

    acciones, soltar, adoptar, frenadas = [], [], [], []
    plantilla = foto.get("plantilla") or set()
    if vendidos:
        plantilla = set(plantilla) - set(vendidos)
    ofertas = foto.get("ofertas_del_computer") or {}
    en_venta = foto.get("en_venta") or set()
    saldo = _int(foto.get("saldo"), 0) or 0

    # 5. SALIDA de los cambios vivos.
    saliendo = set()
    # La plantilla ya sin lo que esta vuelta vendió (`vendidos`).
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
        fila["xp_por_jornada"] = None if r is None else r["xp"]
        fila["xp"] = None if r is None else round(r["xp"], 2)
        fila["factor"] = None if r is None else round(r["factor"], 3)
        return fila

    def _titular(prob):
        # La titularidad mínima, como texto o número; con basura, no.
        try:
            return prob is not None and float(prob) >= TITULARIDAD_MINIMA
        except (TypeError, ValueError):
            return False

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
        estado = str((estados or {}).get(pid) or (liga.get(pid) or {}).get("status")
                     or "ok").strip().lower()
        try:
            hueco = estado in FUERA_DEL_ONCE or (prob is not None
                                                  and float(prob) < TITULARIDAD_HUECO)
        except (TypeError, ValueError):
            hueco = estado in FUERA_DEL_ONCE
        nuestros.append(_con_calendario(
            {"id": pid, "nombre": p.get("name"), "pos": p.get("position"),
             "esperado": e, "valor": valor, "hueco": hueco},
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
        puja = la_puja(precio)
        if en_9900:
            from src.actions.la_ronda_de_la_manana import en_9900 as _en_9900
            puja = _en_9900(puja)
        entran.append(_con_calendario(
            {"id": pid, "nombre": c.get("name"), "pos": c.get("position"),
             "esperado": e, "puja": puja, "coste": puja,
             "ya_es_nuestro": False, "precio": precio,
             "sube": sube_de_verdad(lc, precio)},
            la_ficha(lc, c.get("position"), respaldo=c), prob))
    prob_once = {_int(p.get("id")): p.get("starter_probability") for p in once}
    for pid in inventario:
        lc = liga.get(pid) or {}
        if pid not in plantilla or str(lc.get("status") or "ok").lower() != "ok":
            continue
        # Lo MISMO que al del Computer: `PARTIDOS_MINIMOS` partidos (los de
        # `todaLaLiga`) y `TITULARIDAD_MINIMA`. Los chollos compran sin
        # mirar los minutos: un 12 en un partido con un 40 % de
        # titularidad no es un titular, y por él se vendía uno del once.
        if (_int(lc.get("played"), 0) or 0) < PARTIDOS_MINIMOS:
            continue
        # La titularidad de la plantilla entera (`roster.players`): el del
        # inventario casi nunca está en el once, y `todaLaLiga` no la trae.
        prob = _prob_nuestra(pid, prob_once.get(pid) or lc.get("starter_probability"))
        if not _titular(prob):
            continue
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
    sin_subir = 0
    for e in entran:
        for o in nuestros:
            if o["pos"] != e["pos"]:
                continue
            # SOLO SI SUBE: el del Computer que no sube solo tapa huecos.
            if (solo_si_sube and not e["ya_es_nuestro"] and not e.get("sube")
                    and not o.get("hueco")):
                sin_subir += 1
                continue
            # Con el calendario, el xP por jornada de los DOS lados; si a
            # uno le falta, el `esperado` de los dos (la misma vara).
            con_xp = (ctx is not None and e["xp_por_jornada"] is not None
                      and o["xp_por_jornada"] is not None)
            puntos = (e["xp_por_jornada"] - o["xp_por_jornada"] if con_xp
                      else e["esperado"] - o["esperado"])
            cambio = {
                "entra": e["id"], "entra_nombre": e["nombre"], "sale": o["id"],
                "sale_nombre": o["nombre"], "puntos": round(puntos, 2),
                "caja": int(o["valor"] * VENTA) - e["coste"], "puja": e["puja"],
                "suelo": int(o["valor"] * SUELO), "ya_es_nuestro": e["ya_es_nuestro"],
            }
            if ctx is not None:
                # Por qué: el xP de cada lado, su factor medio, lo que
                # habría dicho el `esperado` de siempre y con qué vara.
                cambio.update({
                    "xp_entra": e["xp"], "xp_sale": o["xp"],
                    "factor_entra": e["factor"], "factor_sale": o["factor"],
                    "sin_calendario": round(e["plano"] - o["plano"], 2),
                    "medida": "calendario" if con_xp else "esperado",
                })
            cambios.append(cambio)

    # LA GUARDIA DEL CALENDARIO: nunca vende a uno claramente mejor con la
    # vara de siempre (`no_vende_a_uno_mejor`).
    #     El frenado por el margen no se tira: se vuelve a medir con la
    #     vara de siempre (`puntos` = `sin_calendario`) y, si apagado
    #     valdria para financiar (en rojo, caro por barato), sigue
    #     valiendo para eso. Encendido nunca financia peor que apagado.
    frenados_por_el_margen = 0
    if ctx is not None:
        validos = []
        for c in cambios:
            if no_vende_a_uno_mejor(c):
                validos.append(c)
                continue
            frenados_por_el_margen += 1
            sin = c.get("sin_calendario")
            if sin is not None and sin >= PEOR_FINANCIACION:
                validos.append({**c, "puntos": sin, "medida": "esperado (frenado por el margen)"})
        cambios = validos

    # LA PUJA FUERTE (con su interruptor): la mejora de verdad puja mas
    # que +1 %, y su caja lo cuenta antes de elegir la combinacion.
    if puja_fuerte:
        precios = {e["id"]: e.get("precio") for e in entran}
        cambios = [con_puja_fuerte(c, precios.get(c["entra"])) for c in cambios]

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
        if ctx is not None:
            plan["calendario"]["frenados_por_el_margen"] = frenados_por_el_margen
    if frenadas:
        plan["frenadas"] = frenadas
    if solo_si_sube:
        plan["sin_subir"] = sin_subir

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


def es_de_esta_vuelta(v10, ahora, run_id=None) -> str | None:
    """
    None si el estado de la vuelta es de ESTA vuelta: si los dos traen el
    `run_id` de GitHub, tiene que ser el mismo (las vueltas de las 04:45
    y 04:50 van seguidas: a 5 minutos, la hora no las distingue); si no,
    su `timestamp` a `VUELTA_VIEJA_MINUTOS` o menos antes de `ahora` (uno
    posterior, también). Si no, el motivo para no contarlo.

    Con un 429 la v10 sale con 0 sin escribir su estado, y la caché
    devuelve el de la vuelta anterior: sus cobros (ya dentro del saldo
    nuevo) se sumarían otra vez a la caja y al saldo, y un saldo inflado
    apaga las reglas del rojo. Sin hora, no se sabe de qué vuelta es: no
    se cuenta. Pura, nunca lanza.
    """
    try:
        suyo = (v10 or {}).get("run_id") if isinstance(v10, dict) else None
        if run_id and suyo:
            if str(suyo) != str(run_id):
                return f"el estado de la vuelta es de otra vuelta (run {suyo}, esta {run_id})"
            return None
        sello = (v10 or {}).get("timestamp") if isinstance(v10, dict) else None
        if not sello:
            return "el estado de la vuelta no trae hora"
        cuando = datetime.fromisoformat(str(sello).replace("Z", "+00:00"))
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=timezone.utc)
        if cuando < ahora - timedelta(minutes=VUELTA_VIEJA_MINUTOS):
            minutos = int((ahora - cuando).total_seconds() // 60)
            return f"el estado de la vuelta es de hace {minutos} min (de otra vuelta)"
        return None
    except Exception as error:                      # noqa: BLE001
        return f"el estado de la vuelta no se puede fechar: {type(error).__name__}"


def lo_de_esta_vuelta(v10, ahora=None, run_id=None, cartera=False) -> dict:
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
        descartado  None, o por qué no se ha contado nada

    Con `ahora` (`correr` lo pasa siempre), solo si es de ESTA vuelta
    (`es_de_esta_vuelta`); si no, todo vacío y `descartado` dice por qué.

    El 12/10 la orden pujó 3.777.000 por Iván Romero y 4.989.000 por
    Gerard Martín y la ronda 1.101.000 por el 1462 en la misma vuelta: la
    caja de la mejora solo veía `maximumBid` bajar. Pura, nunca lanza.
    """
    salida = {"ya_pujados": set(), "gastado": 0, "pujas": {}, "solas": set(), "cobros": {},
              "canceladas": set(),
              "descartado": None}
    try:
        if ahora is not None:
            salida["descartado"] = es_de_esta_vuelta(v10, ahora, run_id)
            if salida["descartado"]:
                return salida
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
                        # Con LA CARTERA (16/10) la ronda ya no revende
                        # sola: su puja cuenta entera, como la de la orden.
                        if bloque == "chollos" or (bloque == "ronda" and not cartera):
                            salida["solas"].add(pid)
                elif h.get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER" and pid is not None:
                    salida["cobros"][pid] = salida["cobros"].get(pid, 0) + importe
                elif h.get("accion") == "CANCELAR_PUJA" and pid is not None:
                    # (14/10: la orden retiro la de Pablo Ramon y la mejora
                    # la seguia restando de la foto, que es de antes.)
                    salida["canceladas"].add(pid)
                    salida["pujas"].pop(pid, None)
    except Exception:                               # noqa: BLE001
        pass
    return salida


def las_ventas_de_la_orden(orden, *, plantilla, pujadas, mercado=None) -> list:
    """
    Los `vender_si_ficha` de la orden que SIGUEN EN PIE (13/10/2026): el
    que sale aún es nuestro (`plantilla`, ya sin lo vendido en esta
    vuelta) y su relevo (su `si_esta` y el general, si lo hay: la orden
    pide los dos) está en la plantilla o tiene puja viva nuestra
    (`pujadas`: las de la foto y las de esta vuelta). Con `mercado` (el
    del Computer, para `pendientes`), vale también un relevo que sigue en
    él (la orden puede volver a pujar); un mercado vacío es no saberlo, y
    vale. Sin relevo, la orden no lo vende nunca.

    El 13/10: vendidos Jutglà y Rico, la orden los sigue listando hasta el
    30/11 y su venta se contaba otra vez en cada vuelta (+3,1 M que no
    existen); perdida la puja por Iván Romero, Jutglà no se vende nunca y
    se contaba igual. Pura, nunca lanza.
    """
    salida = []
    try:
        plantilla = set(plantilla or ())
        pujadas = set(pujadas or ())
        venta = (orden or {}).get("vender_si_ficha") or {}
        general = _int(venta.get("si_esta"))

        def _llega(relevo):
            return (relevo in plantilla or relevo in pujadas
                    or (mercado is not None and (not mercado or relevo in mercado)))

        for j in venta.get("jugadores") or []:
            if not isinstance(j, dict) or _int(j.get("player_id")) not in plantilla:
                continue
            relevos = {r for r in (general, _int(j.get("si_esta"))) if r is not None}
            if relevos and all(_llega(r) for r in relevos):
                salida.append(j)
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
    no dos veces. Sin pasarlo, lo de antes.

    SIN FANTASMAS (13/10/2026): una venta pendiente es solo la que sigue
    en pie. La de la orden, si el que sale aún es nuestro y su relevo está
    dentro o con puja viva (`las_ventas_de_la_orden`); la de la mejora, si
    el que sale aún es nuestro y el que entra está dentro o con puja viva
    (lo mismo que `decidir` suelta, ahora ANTES de la caja). Vendido en
    una vuelta anterior, su dinero ya está en el saldo. Y un `fichar` sin
    puja se resta solo si el jugador sigue en el mercado del Computer (la
    orden puede volver a pujar): perdido ante un rival, ya no se paga. Un
    mercado vacío es no saberlo: se resta, como antes. Pura.
    """
    esta = esta_vuelta or {}
    vendidos = set(esta.get("cobros") or {})
    pujadas = set(foto.get("nuestras_pujas") or {}) | set(esta.get("pujas") or {})
    plantilla = set(foto.get("plantilla") or set()) - vendidos
    mercado = foto.get("mercado") or {}
    orden = orden or {}
    venta = las_ventas_de_la_orden(orden, plantilla=plantilla, pujadas=pujadas)

    # EL PEOR CASO (14/10/2026). Las pujas vivas se resuelven a la vez y
    # cada una puede ganarse o perderse. La venta del que sale solo llega
    # si se GANA la de su relevo; la puja se resta entera. Un cambio que da
    # caja (Lemar por Exposito: -3,77 M + 4,6 M) no puede pagar otro que la
    # quita (Pablo Ramon por Diego Rico: -1,46 M + 0,47 M): si se gana el
    # segundo y se pierde el primero, la J9 empezaba en -0,7 M. Asi que la
    # venta cuyo relevo aun no es nuestro cuenta, como mucho, lo que cuesta
    # su relevo: el cambio que da caja vale 0 (como si se perdiera) y el
    # que la quita, lo que quita (como si se ganara).
    pujas_vivas = {}
    for q, puja in (foto.get("nuestras_pujas") or {}).items():
        pujas_vivas[_int(q)] = _int((puja or {}).get("amount"), 0) or 0
    for q, importe in (esta.get("pujas") or {}).items():
        pujas_vivas[_int(q)] = _int(importe, 0) or 0

    def _hasta_su_relevo(cobro, relevos):
        por_llegar = [r for r in relevos if r is not None and r not in plantilla]
        if not por_llegar:
            return cobro
        return min(cobro, sum(pujas_vivas.get(r, 0) for r in por_llegar))

    general = _int(((orden or {}).get("vender_si_ficha") or {}).get("si_esta"))
    de_la_orden_euros = sum(
        _hasta_su_relevo(int(int((_int(j.get("suelo"), 0) or 0) / SUELO) * VENTA),
                         {general, _int(j.get("si_esta"))})
        for j in venta
    )
    # Un mismo jugador no se vende dos veces: si la orden ya cuenta su
    # venta, la del libro no suma (tercera revision: la orden vuelve a
    # pujar por un relevo perdido y la mejora ya lo habia cambiado).
    de_la_orden = {_int(j.get("player_id")) for j in venta}
    por_el_que_sale = {}
    for k, c in (libro or {}).items():
        sale, entra = _int(c.get("sale")), _int(k)
        if sale not in plantilla or sale in de_la_orden:
            continue
        if not (entra in plantilla or entra in pujadas):
            continue
        cobro = _hasta_su_relevo(
            int((_int((liga.get(sale) or {}).get("price"), 0) or 0) * VENTA), {entra})
        por_el_que_sale[sale] = max(por_el_que_sale.get(sale, 0), cobro)
    return la_caja(
        foto, se_venden_solos=solos,
        inventario_valor=int(sum(_int((liga.get(p) or {}).get("price"), 0) or 0
                                 for p in inventario if p not in vendidos) * VENTA),
        ventas_pendientes=de_la_orden_euros + sum(por_el_que_sale.values())
        - sum(_int(f.get("puja"), 0) or 0 for f in orden.get("fichar") or []
              if _int(f.get("player_id")) not in pujadas
              and _int(f.get("player_id")) not in plantilla
              and (not mercado or _int(f.get("player_id")) in mercado)),
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
    las `RONDAS_DEL_CALENDARIO` próximas rondas PRINCIPALES (un aplazado
    se puntúa con el once de su jornada: no se planea). `calendario`: un
    dict ya leído, o la ruta (por defecto la de los chollos). Nunca
    lanza: si algo falla, un contexto no disponible con el motivo, y la
    mejora usa el `esperado`.
    """
    try:
        from src.analysis.el_calendario_de_puntos import contexto

        if not isinstance(calendario, dict):
            from src.actions.los_chollos import CALENDARIO

            calendario = _leer(CALENDARIO if calendario is None else calendario, {})
        return contexto(status, calendario, ahora, n=RONDAS_DEL_CALENDARIO,
                        solo_principales=True)
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


def escribir_la_vuelta(hechas, ruta=None, ahora=None) -> bool:
    """
    LO QUE HIZO LA MEJORA EN ESTA VUELTA (13/10/2026), para el cierre de
    la jornada, que corre después y no lo ve en la foto (es de antes):

        {"run_id": GITHUB_RUN_ID, "generated_at": ISO UTC,
         "hechas": las de `ejecutar`, tal cual (lista vacía si nada)}

    `ruta`, por defecto `VUELTA_MEJORA`. True si se escribió. Nunca lanza.
    """
    try:
        cuando = ahora if isinstance(ahora, datetime) else datetime.now(timezone.utc)
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        datos = {"run_id": os.environ.get("GITHUB_RUN_ID"),
                 "generated_at": cuando.astimezone(timezone.utc).isoformat(),
                 "hechas": list(hechas) if isinstance(hechas, list) else []}
        ruta = Path(ruta or VUELTA_MEJORA)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False, default=str) + "\n",
                        encoding="utf-8")
        return True
    except Exception:                               # noqa: BLE001
        return False


def correr(status=None, snapshot=None, v10=None, escritor_factory=None,
           ahora: datetime | None = None, libro_ruta=None, calendario=None,
           de_fuera=None, vuelta_ruta=None) -> dict:
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
        vuelta_ruta dónde va `escribir_la_vuelta` (encendida, siempre,
                    también con error). Por defecto `VUELTA_MEJORA`; con
                    `libro_ruta` y sin esto, junto al libro (quien mueve
                    el libro no escribe en producción).
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "adoptados": [], "plan": None, "v10_descartado": None}

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
        # cobrado entran en la caja; lo vendido ya no sale otra vez. Solo
        # si el estado es de ESTA vuelta (con un 429 queda el de otra).
        from src.actions.la_ronda_de_la_manana import la_cartera_activa
        cartera = la_cartera_activa()
        esta_vuelta = lo_de_esta_vuelta(v10, ahora, os.environ.get("GITHUB_RUN_ID"),
                                        cartera=cartera)
        salida["v10_descartado"] = esta_vuelta["descartado"]
        ya_pujados = esta_vuelta["ya_pujados"]
        vendidos = set(esta_vuelta["cobros"])
        # Lo retirado en esta vuelta ya no es una puja viva (la foto es de
        # antes): ni se resta de la caja ni bloquea a nadie.
        foto["nuestras_pujas"] = {
            q: v for q, v in (foto.get("nuestras_pujas") or {}).items()
            if _int(q) not in esta_vuelta.get("canceladas", set())}
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
        # SIN FANTASMAS (13/10/2026): el que la orden vende y aún es
        # nuestro queda quieto solo mientras su relevo está dentro, con
        # puja viva o aún en el mercado del Computer. Perdido el relevo, la
        # orden no lo vende nunca y vuelve a poder cambiarse. El que ya no
        # es nuestro, como antes (no se vuelve a fichar).
        nuestros_ahora = set(foto["plantilla"]) - vendidos
        siguen = {_int(j.get("player_id")) for j in las_ventas_de_la_orden(
            orden, plantilla=nuestros_ahora,
            pujadas=set(foto.get("nuestras_pujas") or {}) | set(esta_vuelta["pujas"]),
            mercado=foto.get("mercado") or {})}
        venta = (orden.get("vender_si_ficha") or {}).get("jugadores") or []
        pendientes |= {_int(j.get("player_id")) for j in venta
                       if _int(j.get("player_id")) not in nuestros_ahora
                       or _int(j.get("player_id")) in siguen}
        # los `no_pujar` del gestor
        pendientes |= set(fuera["vetados"] if "vetados" in fuera else vetados())
        pendientes |= vendidos

        ruta_ronda = fuera.get("libro_ronda") or LIBRO_RONDA
        ruta_chollos = fuera.get("libro_chollos") or LIBRO_CHOLLOS
        libro_ronda = _leer(ruta_ronda, {})
        libro_chollos = _leer(ruta_chollos, {})
        libros = {_int(k) for k in list(libro_ronda) + list(libro_chollos)}
        inventario = {p for p in libros if p in foto["plantilla"] and p not in vendidos}
        # LA CARTERA (16/10/2026): lo que puja la ronda ya no se revende
        # solo antes de la jornada; su puja viva cuenta entera. Lo que ya
        # es nuestro sigue contando como inventario: si hace falta, el
        # cierre lo vende antes de la jornada.
        solos = ({_int(k) for k in libro_chollos} if cartera else libros)

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
            calendario_de_puntos=ctx, puja_fuerte=la_puja_fuerte_activa(),
            solo_si_sube=la_mejora_solo_si_sube_activa(),
            en_9900=la_puja_en_9900_activa(),
            probabilidades=las_probabilidades(status),
            estados=los_estados(snapshot, liga),
            vendidos=vendidos,
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

    # Encendida, SIEMPRE (también con error o sin nada hecho): lo que esta
    # vuelta mandó, para el cierre de la jornada.
    try:
        if salida["activa"]:
            if vuelta_ruta is None and libro_ruta is not None:
                vuelta_ruta = Path(libro_ruta).with_name(VUELTA_MEJORA.name)
            escribir_la_vuelta(salida["hechas"], vuelta_ruta, ahora)
    except Exception:                               # noqa: BLE001
        pass

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
                  f"(x{c['factor_sale']}); sin calendario {c['sin_calendario']:+}; "
                  f"vara: {c.get('medida')}")
    if (calendario or {}).get("frenados_por_el_margen"):
        print(f"  frenados por el margen del calendario: {calendario['frenados_por_el_margen']}")
    if plan.get("sin_subir"):
        print(f"  frenados por no subir (solo si sube): {plan['sin_subir']}")
    if r.get("v10_descartado"):
        print(f"  lo de esta vuelta, sin contar: {r['v10_descartado']}")
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
