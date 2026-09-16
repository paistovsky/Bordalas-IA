"""
Los tres denominadores: el plazo, los dias planos y la masa.

QUE SE MIDE AQUI, Y POR QUE HACIA FALTA

    El informe del 15/09 dejo tres numeros sueltos y los tres
    tenian el mismo defecto de fondo: se publicaron sin decir
    sobre que muestra estaban calculados.

        99,2 %    de persistencia, sobre pares "adyacentes" que
                  no siempre eran dias consecutivos, y quitando
                  del denominador los dias en que el precio no
                  se movio.

        0,1443 %  de rendimiento, presentado como "como
                  especulacion" cuando el valor con el que se
                  calculaba no venia de la especulacion.

        1/7       de masa en cada peldaño de la curva de pujas,
                  que es correcto por construccion -son
                  cuantiles- y falso como descripcion de donde
                  caen las pujas de verdad.

    DOCTRINA 53: un porcentaje sin su plazo no es un rendimiento.
    DOCTRINA 54: un ratio solo vale si numerador y denominador
                 cubren el mismo periodo.
    DOCTRINA 55: un agregado sin su `n` es una anecdota.
    DOCTRINA 57: una fuente que coincide al 100 % con un dato que
                 ya tienes es un eco.

EL ECO, MEDIDO (16/09/2026)

    Sobre la foto del 14/09 y sobre nuestra propia serie:

        acquisition.targets   magnitud == price_increment/precio
                              69 de 69, con signo
        scout.highlights      magnitud == (precio-ayer)/precio
                              15 de 15, contra NUESTRA serie
        market_gate.rate      == scout.mean_magnitude_percent
                              69 de 69

    Las tres webs no nos dan un dato que no tengamos: nos
    devuelven `price_increment` dividido entre el precio. Por eso
    `estimacion_desde_el_historico` existe: el mismo numero sale
    de casa, sin salir a la red.

SIN RELOJ, SIN DISCO, SIN RED

    Todo entra por argumento, incluida la zona horaria. Ninguna
    funcion de este modulo abre un fichero ni mira la hora.
"""

from __future__ import annotations

import statistics

from datetime import datetime, timedelta


# Por debajo de esto un movimiento no se distingue del redondeo
# del propio Biwenger, que mueve los precios en saltos de 10.000.
# Es el mismo que usa `el_pronostico_del_ojeador`.
MOVIMIENTO_MINIMO_PUNTOS = 1.0

# El almacen muestrea dos veces al dia y las dos traen el mismo
# precio hasta que cambia por la mañana. Se coge la primera
# muestra a partir de esta hora como "el precio de ese dia".
HORA_DEL_PRECIO_DEL_DIA = 7

SIN_PRONOSTICO = "SIN_PRONOSTICO"

# Las vias que SI proyectan el ritmo del jugador. Cualquier otra
# que se presente como especulacion esta usando un valor que no
# depende del jugador: ver `el_valor_de_reserva`.
VIAS_QUE_PROYECTAN = ("PRICE_TREND", "SPECULATION")


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# EL PRIMER DENOMINADOR: EL PLAZO
# ============================================================


def serie_por_dia(
    historico: dict | None,
    zona,
    hora_minima: int = HORA_DEL_PRECIO_DEL_DIA,
) -> dict:
    """
    Un precio por dia de calendario, por jugador.

    `historico` es `{jugador: {"t": [...], "p": [...]}}`, que es
    la forma de `price_history.json`. `zona` es el huso con el
    que se fecha cada marca: entra por argumento para que esto no
    dependa del reloj ni de la configuracion de la maquina.

    Devuelve `{jugador: {fecha: precio}}`. Forma fija, nunca
    lanza.
    """

    series = {}

    for jugador, fila in (historico or {}).items():

        por_dia = {}

        marcas = (fila or {}).get("t") or []
        precios = (fila or {}).get("p") or []

        for marca, precio in zip(marcas, precios):

            try:
                momento = datetime.fromtimestamp(marca, zona)

            except (TypeError, ValueError, OSError, OverflowError):
                continue

            if momento.hour >= hora_minima and precio:
                por_dia.setdefault(momento.date(), precio)

        if por_dia:
            series[str(jugador)] = por_dia

    return series


def racha_hasta(por_dia: dict | None, dia) -> int:
    """
    Dias de calendario CONSECUTIVOS con el mismo signo que
    terminan en `dia`. Positivo si sube, negativo si baja.

    Se corta en el primer dia plano y en el primer agujero de la
    serie: una racha con un hueco en medio no es una racha, son
    dos trozos.
    """

    serie = por_dia or {}

    largo = 0
    signo = 0
    actual = dia

    while True:

        anterior = actual - timedelta(days=1)

        if anterior not in serie or actual not in serie:
            break

        delta = serie[actual] - serie[anterior]

        paso = (delta > 0) - (delta < 0)

        if paso == 0:
            break

        if signo == 0:
            signo = paso

        elif paso != signo:
            break

        largo += 1
        actual = anterior

    return largo * signo


def pares_al_plazo(series: dict | None, horizonte: int = 1) -> list:
    """
    Pares (lo que hizo AYER, lo que hizo en los `horizonte` dias
    siguientes) con el plazo GARANTIZADO.

    LA CORRECCION QUE OBLIGO A ESCRIBIR ESTO (16/09/2026)

        La primera medicion recorria la lista de precios de cada
        jugador y tomaba posiciones adyacentes como si fueran
        dias seguidos. No lo son: al almacen le faltan dias -el
        07/09 entero, y entre 366 y 579 jugadores segun el dia- y
        dos posiciones seguidas de la lista podian estar a tres
        dias de distancia.

        Medido: de 15.107 pares "adyacentes", 2.492 -el 16 %- no
        eran de un dia. Un factor diario calculado sobre ellos
        mezcla plazos, que es exactamente la doctrina 53.

    Aqui se exige que TODOS los dias del tramo esten en la serie.
    Cada par lleva su `plazo` escrito.
    """

    pares = []

    plazo = max(int(horizonte or 1), 1)

    for jugador, por_dia in (series or {}).items():

        for dia in sorted(por_dia):

            ayer = dia - timedelta(days=1)

            tramo = [dia + timedelta(days=k) for k in range(plazo + 1)]

            if ayer not in por_dia:
                continue

            if any(d not in por_dia for d in tramo):
                continue

            antes = por_dia[ayer]
            medio = por_dia[dia]
            despues = por_dia[tramo[-1]]

            if not antes or not medio:
                continue

            pares.append(
                {
                    "player": jugador,
                    "date": dia,
                    "plazo": plazo,
                    "ayer": (medio - antes) / antes * 100.0,
                    "hoy": (despues - medio) / medio * 100.0,
                    "racha": racha_hasta(por_dia, dia),
                }
            )

    return pares


# ============================================================
# EL SEGUNDO DENOMINADOR: LOS DIAS PLANOS
# ============================================================


def tabla_de_persistencia(
    pares: list | None,
    minimo: float = MOVIMIENTO_MINIMO_PUNTOS,
) -> dict:
    """
    De los pares en que AYER subio: hoy sube / hoy plano / hoy
    baja. Y lo mismo para los que ayer bajaron.

    POR QUE UNA TABLA Y NO UN PORCENTAJE

        El 99,2 % del informe anterior se calculaba sobre los
        pares en que el precio se movio los DOS dias. Contado
        asi, un dia plano no cuenta ni a favor ni en contra, y el
        numero describe "cuando se mueve, ¿sigue?" — que no es la
        pregunta que decide una compra.

        La que decide una compra es "si ayer subio, ¿que pasa
        hoy?", y ahi el dia plano es un resultado: el dinero se
        queda quieto. Por eso las tres filas suman el 100 % y el
        denominador son TODOS los pares.

    Forma fija, nunca lanza. Cada grupo lleva su `n` y su plazo.
    """

    filas = [p for p in (pares or []) if isinstance(p, dict)]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "plazo": None,
            "groups": {},
            "reason": (
                "No llega ni un par: sin muestra no hay tabla, y "
                "una tabla vacia no es un resultado."
            ),
        }

    plazos = sorted({int(p.get("plazo") or 1) for p in filas})

    def reparto(seleccion):

        total = len(seleccion)

        sube = sum(1 for p in seleccion if p["hoy"] > 0)
        plano = sum(1 for p in seleccion if p["hoy"] == 0)
        baja = sum(1 for p in seleccion if p["hoy"] < 0)

        return {
            "n": total,
            "sube": sube,
            "plano": plano,
            "baja": baja,
            "sube_percent": (
                round(100.0 * sube / total, 1) if total else None
            ),
            "plano_percent": (
                round(100.0 * plano / total, 1) if total else None
            ),
            "baja_percent": (
                round(100.0 * baja / total, 1) if total else None
            ),
        }

    corte = abs(float(minimo))

    grupos = {
        "subio": reparto([p for p in filas if p["ayer"] > 0]),
        "subio_fuerte": reparto([p for p in filas if p["ayer"] >= corte]),
        "bajo": reparto([p for p in filas if p["ayer"] < 0]),
        "bajo_fuerte": reparto([p for p in filas if p["ayer"] <= -corte]),
        "plano": reparto([p for p in filas if p["ayer"] == 0]),
    }

    return {
        "available": True,
        "n": len(filas),
        "plazo": plazos[0] if len(plazos) == 1 else plazos,
        "minimo": corte,
        "groups": grupos,
        "reason": (
            f"{len(filas):,} pares a {plazos[0]} dia(s) de plazo. De "
            f"los que ayer subieron al menos {corte} punto, hoy "
            f"sigue subiendo el "
            f"{grupos['subio_fuerte']['sube_percent']} % "
            f"(n={grupos['subio_fuerte']['n']:,})."
        ),
    }


def factor_de_persistencia(
    pares: list | None,
    minimo: float = MOVIMIENTO_MINIMO_PUNTOS,
    contando_planos: bool = True,
) -> dict:
    """
    Cuanto del movimiento de ayer se repite, EN TAMAÑO.

    `contando_planos` es el denominador del titulo. Con `True`
    -que es lo honesto- los dias en que el precio no se movio
    entran en la mediana como el cero que son. Con `False` se
    reproduce el calculo viejo, que los quitaba.

    La diferencia no es grande -los dias planos son el 2,1 % de
    la muestra- pero la guardia
    `test_la_persistencia_cuenta_los_dias_planos` exige que los
    dos numeros se puedan pedir por separado: si salieran iguales
    la guardia no probaria nada.
    """

    corte = abs(float(minimo))

    filas = [
        p
        for p in (pares or [])
        if isinstance(p, dict) and abs(p.get("ayer") or 0) >= corte
    ]

    if not contando_planos:
        filas = [p for p in filas if p["hoy"] != 0]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "factor": None,
            "misma_direccion": None,
            "plazo": None,
            "contando_planos": bool(contando_planos),
            "reason": (
                "Ni un par con movimiento suficiente: sin muestra "
                "no se mide la persistencia."
            ),
        }

    # El signo se normaliza: interesa si el movimiento CONTINUA,
    # no si sube o baja.
    ayer = statistics.median(abs(p["ayer"]) for p in filas)

    hoy = statistics.median(
        p["hoy"] if p["ayer"] > 0 else -p["hoy"] for p in filas
    )

    sigue = sum(
        1
        for p in filas
        if p["hoy"] != 0 and (p["ayer"] > 0) == (p["hoy"] > 0)
    )

    plazos = sorted({int(p.get("plazo") or 1) for p in filas})

    return {
        "available": True,
        "n": len(filas),
        "plazo": plazos[0] if len(plazos) == 1 else plazos,
        "factor": round(hoy / ayer, 4) if ayer else None,

        # Sobre TODOS los pares del grupo, no solo sobre los que
        # se movieron: es el mismo denominador que el factor.
        "misma_direccion": round(sigue / len(filas), 4),
        "contando_planos": bool(contando_planos),
        "reason": (
            f"Sobre {len(filas):,} pares a {plazos[0]} dia(s) "
            f"{'contando' if contando_planos else 'SIN contar'} los "
            f"dias planos: la mediana de ayer ({ayer:+.3f} %) se "
            f"repite como {hoy:+.3f} %, factor {hoy / ayer:.4f}."
            if ayer
            else "Sin movimiento medible ayer."
        ),
    }


def se_agota_la_racha(
    pares: list | None,
    tramos=(
        (1, 1),
        (2, 3),
        (4, 6),
        (7, 10),
        (11, 15),
        (16, 25),
        (26, 999),
    ),
    minimo: float = MOVIMIENTO_MINIMO_PUNTOS,
) -> dict:
    """
    ¿Un jugador con veintidos dias subiendo sigue subiendo?

    Parte la muestra por dias de racha y da, en cada tramo, la
    direccion y el factor con su `n`. Un tramo sin muestra se
    publica con `n = 0` y sin numeros: no se interpola.
    """

    corte = abs(float(minimo))

    filas = [
        p
        for p in (pares or [])
        if isinstance(p, dict) and abs(p.get("ayer") or 0) >= corte
    ]

    salida = []

    for bajo, alto in tramos:

        grupo = [
            p for p in filas if bajo <= abs(p.get("racha") or 0) <= alto
        ]

        if not grupo:
            salida.append(
                {
                    "tramo": f"{bajo}-{alto}",
                    "n": 0,
                    "sigue_percent": None,
                    "plano_percent": None,
                    "gira_percent": None,
                    "factor": None,
                }
            )
            continue

        sigue = sum(
            1
            for p in grupo
            if p["hoy"] != 0 and (p["ayer"] > 0) == (p["hoy"] > 0)
        )

        plano = sum(1 for p in grupo if p["hoy"] == 0)

        medido = factor_de_persistencia(grupo, minimo=minimo)

        salida.append(
            {
                "tramo": f"{bajo}-{alto}",
                "n": len(grupo),
                "sigue_percent": round(100.0 * sigue / len(grupo), 1),
                "plano_percent": round(100.0 * plano / len(grupo), 1),
                "gira_percent": round(
                    100.0 * (len(grupo) - sigue - plano) / len(grupo), 1
                ),
                "factor": medido.get("factor"),
            }
        )

    return {
        "available": bool(filas),
        "n": len(filas),
        "tramos": salida,
        "reason": (
            f"Muestra partida por dias de racha sobre "
            f"{len(filas):,} pares."
            if filas
            else "Sin muestra que partir."
        ),
    }


# ============================================================
# EL TERCER DENOMINADOR: LA MASA DE LA CURVA
# ============================================================


def masa_real_de_la_curva(
    curva: list | None,
    cortes: list | None,
    muestras: int,
) -> dict:
    """
    Cuantas de las pujas medidas caen en cada peldaño DE VERDAD.

    LA DIFERENCIA ENTRE UN CUANTIL Y UNA MASA

        `calibrate_premium_curve` reparte 1/7 a cada peldaño, y
        eso es correcto por construccion: son siete cuantiles y
        cada uno marca una posicion de la lista ordenada.

        Pero los cortes NO estan repartidos por igual: 0,05 /
        0,20 / 0,40 / 0,60 / 0,80 / 0,95 / 0,995. Los saltos son
        0,15 / 0,20 / 0,20 / 0,20 / 0,15 y 0,045. El ultimo
        peldaño cubre el 0,5 % de arriba y se lleva el 14,29 % de
        la masa.

        `win_probability` usa esos pesos como la probabilidad de
        que un rival puje ahi. Con 1/7 el modelo afirma que un
        rival paga la prima del percentil 99,5 una de cada siete
        veces.

    Aqui se cuenta cuantas muestras caen entre corte y corte, que
    es lo que el modelo deberia creer. NO TOCA LA CURVA: la
    devuelve al lado para poder mirar las dos.
    """

    puntos = list(curva or [])

    quiebres = list(cortes or [])

    n = int(muestras or 0)

    if not puntos or not quiebres or n <= 0:
        return {
            "available": False,
            "samples": n,
            "steps": [],
            "curva_por_masa": [],
            "reason": (
                "Sin curva, sin cortes o sin muestras no se puede "
                "decir donde cae la masa."
            ),
        }

    if len(puntos) != len(quiebres):
        return {
            "available": False,
            "samples": n,
            "steps": [],
            "curva_por_masa": [],
            "reason": (
                f"La curva trae {len(puntos)} peldaños y los cortes "
                f"son {len(quiebres)}: no se pueden emparejar."
            ),
        }

    # El indice de la muestra ordenada que marca cada corte, con
    # la misma aritmetica que `calibrate_premium_curve`.
    indices = [min(int(q * n), n - 1) for q in quiebres]

    pasos = []

    for k, (punto, indice) in enumerate(zip(puntos, indices)):

        # El primer peldaño se lleva tambien lo que queda por
        # debajo del primer corte: esas pujas existieron y tienen
        # que caer en algun sitio.
        desde = 0 if k == 0 else indice

        hasta = indices[k + 1] if k + 1 < len(indices) else n

        cuantas = max(hasta - desde, 0)

        factor = punto[0] if isinstance(punto, (list, tuple)) else punto

        peso = (
            punto[1]
            if isinstance(punto, (list, tuple)) and len(punto) > 1
            else None
        )

        pasos.append(
            {
                "factor": factor,
                "peso_por_construccion": peso,
                "n": cuantas,
                "masa_real": round(cuantas / n, 4),
                "corte": quiebres[k],
            }
        )

    return {
        "available": True,
        "samples": n,
        "steps": pasos,
        "curva_por_masa": [(p["factor"], p["masa_real"]) for p in pasos],
        "reason": (
            f"Sobre {n} pujas medidas: el peldaño de arriba "
            f"(+{100 * (pasos[-1]['factor'] - 1):.2f} %) lleva "
            f"{pasos[-1]['peso_por_construccion']} por construccion "
            f"y {pasos[-1]['masa_real']} de verdad "
            f"(n={pasos[-1]['n']})."
        ),
    }


# ============================================================
# EL VALOR DE RESERVA, QUE TIENE QUE GRITAR
# ============================================================


def el_valor_de_reserva(candidatos: list | None) -> dict:
    """
    ¿Que candidatos llevan un valor que NO depende del jugador?

    EL FALLO, CON SU NOMBRE (medido el 16/09/2026)

        `computer_resale_value` devuelve `intent: "SPECULATION"` y
        `route: "COMPUTER_RESALE"`. `evaluate_market_rate` +
        `speculation_value` devuelven lo mismo por la via
        `PRICE_TREND`. Las dos compiten en un `max(...)` por
        valor, y la que gana presta su `value` Y su `intent`.

        Cuando gana COMPUTER_RESALE, `optimal_bid` ve
        `intent == SPECULATION`, aplica el liston del 3 % y
        escribe "Como especulacion rinde un X %" — sobre un valor
        que es `precio x (1 + prima_del_Computer x 0,75)`, la
        MISMA constante para todo el tablero.

        Por eso salian rechazos con el mismo numero teniendo
        ritmos del ojeador distintos, y por eso Veiga -cayendo un
        1,19 % al dia, con `speculation_value` = 0- rendia
        exactamente lo mismo que Marc Roca subiendo.

        NO ES QUE EL RITMO NO LLEGARA. Llego, se uso, y perdio el
        `max`.

    `candidatos` es una lista de
        {"player", "price", "value", "route", "intent",
         "rate_percent_per_day"}

    Devuelve los sospechosos CON NOMBRE Y MOTIVO. Con la lista
    vacia devuelve `available: False`: pasar con las manos vacias
    no es un aprobado.
    """

    filas = [c for c in (candidatos or []) if isinstance(c, dict)]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "reserva": [],
            "ratios": {},
            "reason": (
                "La lista de candidatos llega vacia: no se ha "
                "mirado nada, y no haber mirado no es un resultado "
                "limpio."
            ),
        }

    sospechosos = []

    # RATIO valor/precio: la huella de un valor de reserva es que
    # dos jugadores con ritmos DISTINTOS compartan ratio.
    ratios = {}

    for fila in filas:

        precio = safe_float(fila.get("price"), 0.0) or 0.0
        valor = safe_float(fila.get("value"), 0.0) or 0.0

        if precio <= 0 or valor <= 0:
            continue

        ratios.setdefault(round(valor / precio, 6), []).append(fila)

    for clave, grupo in ratios.items():

        ritmos = {
            round(
                safe_float(f.get("rate_percent_per_day"), 0.0) or 0.0,
                3,
            )
            for f in grupo
        }

        if len(grupo) < 2 or len(ritmos) < 2:
            continue

        for fila in grupo:
            sospechosos.append(
                {
                    "player": fila.get("player"),
                    "price": fila.get("price"),
                    "value": fila.get("value"),
                    "ratio": clave,
                    "route": fila.get("route"),
                    "intent": fila.get("intent"),
                    "rate_percent_per_day": fila.get(
                        "rate_percent_per_day"
                    ),
                    "motivo": "RATIO_COMPARTIDO",
                    "reason": (
                        f"{fila.get('player')}: el valor es "
                        f"{clave:.6f} veces el precio, el mismo "
                        f"ratio que otros {len(grupo) - 1} "
                        f"candidato(s) con ritmos distintos "
                        f"({sorted(ritmos)}). Un valor que no cambia "
                        f"con el ritmo no es una estimacion de ESTE "
                        f"jugador."
                    ),
                }
            )

    for fila in filas:

        via = str(fila.get("route") or "").upper()
        intencion = str(fila.get("intent") or "").upper()

        if intencion != "SPECULATION" or not via:
            continue

        if via in VIAS_QUE_PROYECTAN:
            continue

        sospechosos.append(
            {
                "player": fila.get("player"),
                "price": fila.get("price"),
                "value": fila.get("value"),
                "ratio": None,
                "route": fila.get("route"),
                "intent": fila.get("intent"),
                "rate_percent_per_day": fila.get(
                    "rate_percent_per_day"
                ),
                "motivo": "VIA_QUE_NO_PROYECTA",
                "reason": (
                    f"{fila.get('player')}: se presenta como "
                    f"SPECULATION pero el valor viene de la via "
                    f"{via}, que no proyecta el ritmo del jugador. "
                    f"El liston del 3 % se le aplica a un numero que "
                    f"no es suyo."
                ),
            }
        )

    return {
        "available": True,
        "n": len(filas),
        "reserva": sospechosos,
        "ratios": {
            k: len(v) for k, v in sorted(ratios.items()) if len(v) > 1
        },
        "reason": (
            f"De {len(filas)} candidatos, {len(sospechosos)} aviso(s) "
            f"de valor que no depende del jugador."
            if sospechosos
            else (
                f"De {len(filas)} candidatos, ninguno lleva un valor "
                f"de reserva: cada valor cambia con su ritmo."
            )
        ),
    }


# ============================================================
# QUE EL OJEADOR DEJE DE SER UNA DEPENDENCIA
# ============================================================


def estimacion_desde_el_historico(
    por_dia: dict | None,
    dia,
    persistencia: float,
    minimo: float = MOVIMIENTO_MINIMO_PUNTOS,
) -> dict:
    """
    Lo que el ojeador diria, calculado en casa.

    Las tres webs publican `price_increment / precio` -medido: 69
    de 69 en la foto del 14/09, y 15 de 15 contra nuestra propia
    serie-. Ese numero sale de `price_history.json` sin salir a la
    red, asi que el ojeador deja de ser una dependencia y pasa a
    ser un contraste.

    Devuelve el porcentaje esperado a UN dia, con su plazo y su
    origen escritos. Sin serie, sin `dia` o sin el dia anterior:
    `SIN_PRONOSTICO` con el motivo. Nunca una constante.
    """

    vacio = {
        "available": False,
        "percent_per_day": None,
        "observed_percent": None,
        "decision": SIN_PRONOSTICO,
        "source": "PRICE_HISTORY",
        "plazo": 1,
        "reason": None,
    }

    serie = por_dia or {}

    if not serie:
        return {
            **vacio,
            "reason": (
                "El historico de precios llega vacio: sin serie "
                "propia no hay estimacion, y no se inventa una."
            ),
        }

    if dia is None:
        return {**vacio, "reason": "Sin dia de referencia."}

    ayer = dia - timedelta(days=1)

    if dia not in serie or ayer not in serie:
        return {
            **vacio,
            "reason": (
                f"Falta el precio del {dia} o del {ayer} en nuestra "
                f"serie: no se estima a ciegas."
            ),
        }

    hoy = serie[dia]
    antes = serie[ayer]

    if not hoy or not antes:
        return {**vacio, "reason": "Precio nulo en la serie."}

    # La misma convencion que publican las tres webs: el
    # incremento dividido entre el precio de HOY.
    observado = (hoy - antes) / hoy * 100.0

    if abs(observado) < abs(float(minimo)):
        return {
            **vacio,
            "observed_percent": round(observado, 4),
            "reason": (
                f"El precio se movio {observado:+.3f} % en un dia, "
                f"por debajo de {minimo} punto: no se distingue del "
                f"redondeo de 10.000 de Biwenger."
            ),
        }

    esperado = observado * float(persistencia)

    return {
        "available": True,
        "percent_per_day": round(esperado, 4),
        "observed_percent": round(observado, 4),
        "persistence": float(persistencia),
        "decision": "PRONOSTICO",
        "source": "PRICE_HISTORY",
        "plazo": 1,
        "trend_days": racha_hasta(serie, dia),
        "reason": (
            f"Nuestra propia serie: {antes:,} -> {hoy:,} "
            f"({observado:+.3f} % en un dia). Con la persistencia "
            f"medida ({persistencia:.4f}) se espera "
            f"{esperado:+.3f} % al dia. Sin salir a la red."
        ).replace(",", "."),
    }


def contraste_con_el_ojeador(
    nuestro: dict | None,
    magnitud_del_ojeador,
    tolerancia: float = 0.01,
) -> dict:
    """
    Si una web discrepa de nuestro propio precio, eso SI es
    informacion.

    Mientras coincidan, la web es un eco y no aporta nada
    (doctrina 57). El dia que no coincida, una de las dos fotos
    esta mal y hay que gritarlo.
    """

    mio = (nuestro or {}).get("observed_percent")

    suyo = safe_float(magnitud_del_ojeador)

    if mio is None or suyo is None:
        return {
            "available": False,
            "agree": None,
            "delta": None,
            "reason": (
                "Falta uno de los dos numeros: sin los dos no hay "
                "contraste."
            ),
        }

    delta = suyo - mio

    coinciden = abs(delta) <= abs(float(tolerancia))

    return {
        "available": True,
        "agree": coinciden,
        "delta": round(delta, 4),
        "ours": round(mio, 4),
        "theirs": round(suyo, 4),
        "reason": (
            f"El ojeador dice {suyo:+.3f} % y nuestra serie dice "
            f"{mio:+.3f} %: coinciden. Es un ECO, confirma la "
            f"tuberia y no aporta informacion (doctrina 57)."
            if coinciden
            else (
                f"DISCREPAN: el ojeador dice {suyo:+.3f} % y nuestra "
                f"serie dice {mio:+.3f} % ({delta:+.3f} puntos). Una "
                f"de las dos fotos esta mal, y ESO si es informacion."
            )
        ),
    }
