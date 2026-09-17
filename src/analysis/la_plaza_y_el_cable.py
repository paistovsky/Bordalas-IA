"""
La plaza y el cable: lo que se saca vendiendo, y lo que ocupa una ficha.

EL CABLE QUE FALTA

    Pepe tiene las dos piezas y no estan unidas:

        `sale_order`             quien sobra, y cuanto da cada uno
        `roster_expansion`       a quien se ficharia, y a que coste
        `acquisition_budget`     cuanto se puede gastar HOY

    El presupuesto de fichar mira el SALDO y el margen de deuda.
    No mira las ofertas vivas que hay encima de la mesa por
    jugadores que la cola de venta ya marca como sobrantes.

    En la foto del 13/09 eso son 0 EUR de presupuesto contra
    16.491.200 EUR de caja realizable sin tocar el once.

LA IDENTIDAD DEL TECHO, MEDIDA (17/09/2026)

    El docstring de `acquisition_budget` dice que `maximumBid` ya
    lleva dentro el valor de la plantilla y que por eso sumar lo
    que se recupera de una venta seria contarlo dos veces.

    Es verdad a medias, y la mitad que falta es la que importa.
    Medido sobre 15 combinaciones distintas de saldo, plantilla y
    puja viva -95 fotos del 12/08 al 13/09, mas 4 lineas de la
    bitacora del 16/09-, las 15 al euro:

        maximumBid = saldo + valor_de_plantilla / 4 - comprometido

    De cada jugador, dentro del techo hay UN CUARTO de su precio.
    Venderlo a precio de mercado mueve ese precio entero al saldo
    y quita un cuarto de la plantilla:

        el techo sube 0,75 x precio

    Asi que la caja realizable NO esta contada dos veces: esta
    contada al 25 %. Y el saldo -que es de donde sale
    `cash_budget`- no la tiene contada en absoluto.

FASE OBSERVADOR

    Nada de esto ficha, vende, puja ni acepta. `ENCENDIDO` es
    False y hay guardia que lo comprueba. Es una lista escrita al
    margen, como `roster_expansion_shadow`.

EL GUARDARRAIL NO SE REESCRIBE

    `position_guardrail.validate_sale_set` ya sabe decir si un
    CONJUNTO de ventas deja el once sin alinear. Aqui se le
    llama, prefijo a prefijo, igual que hace `sale_order`. No se
    copia su logica: copiarla seria tener dos respuestas para la
    misma pregunta, que es el fallo del 16/08.

DOCTRINA 55 Y 58

    Cada agregado sale con su `n`, y el `n` es el que se
    comprobo. Los tramos de la prima del Computer no se funden
    aunque uno se quede corto: un tramo flojo se marca y se
    queda con su muestra.
"""

from __future__ import annotations

import statistics


# ============================================================
# EL INTERRUPTOR
# ============================================================
#
# Este encargo mide, nombra y para. Nada se enciende.
ENCENDIDO = False


# ============================================================
# LA IDENTIDAD DEL TECHO DE BIWENGER
# ============================================================
#
#     Medida, no supuesta. Ver la cabecera: 15 de 15 al euro.
#
#     El denominador es 4 y no un porcentaje escrito a mano
#     porque asi sale de la medicion: `roster_value // 4`, con
#     division entera, clava las quince.
PARTE_DE_LA_PLANTILLA_EN_EL_TECHO = 4


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _miles(valor) -> str:
    """
    El separador de miles de la casa, puesto en el numero y no en
    la frase.

    `f"{x:,}".replace(",", ".")` sobre una frase entera se lleva
    por delante las comas de la prosa. Aqui se aplica solo al
    numero.
    """

    return f"{safe_int(valor):,}".replace(",", ".")


def esta_encendido() -> bool:
    """La via no manda. Se calcula, se enseña y se para."""

    return bool(ENCENDIDO)


# ============================================================
# EL TECHO, ANTES Y DESPUES DE VENDER
# ============================================================


def techo_de_biwenger(balance, roster_value, committed=0) -> int:
    """
    `maximumBid` reconstruido desde sus tres piezas.

    Existe para poder COMPROBAR la identidad contra lo que
    Biwenger publica, no para sustituirlo: si un dia dejan de
    cuadrar, el que manda sigue siendo el de Biwenger y esto es
    lo que avisa.
    """

    return (
        safe_int(balance)
        + safe_int(roster_value) // PARTE_DE_LA_PLANTILLA_EN_EL_TECHO
        - safe_int(committed)
    )


def techo_tras_vender(maximum_bid, importe_de_venta, precio_de_mercado) -> int:
    """
    A cuanto sube el techo de Biwenger al cobrar una venta.

    El importe entra al saldo; el precio de mercado sale de la
    plantilla, y de ahi solo estaba contado un cuarto.
    """

    return (
        safe_int(maximum_bid)
        + safe_int(importe_de_venta)
        - safe_int(precio_de_mercado)
        // PARTE_DE_LA_PLANTILLA_EN_EL_TECHO
    )


# ============================================================
# BLOQUE 1 — EL PRESUPUESTO QUE CUENTA LO REALIZABLE
# ============================================================


def presupuesto_con_lo_realizable(
    acquisition_budget: dict | None,
    sale_order: dict | None,
) -> dict:
    """
    Los DOS numeros, con nombre cada uno: la caja que hay y la
    que habria vendiendo.

    No sustituye a `acquisition_budget`: lo acompaña. El que
    manda sigue siendo el que publica `calculate_acquisition_budget`,
    y aqui se dice cuanto se esta dejando fuera.

    Nunca lanza. Con la cola de venta vacia NO publica un
    realizable: publica que no lo sabe. Una cola vacia y una cola
    sin ofertas vivas no son lo mismo que "no hay nada que
    vender", y dar 0 por bueno seria afirmar mas de lo que se ha
    medido.
    """

    try:
        presupuesto = acquisition_budget or {}
        cola_datos = sale_order or {}

        en_caja = safe_int(
            presupuesto.get("available_budget")
            if presupuesto.get("available_budget") is not None
            else presupuesto.get("total_budget")
        )

        techo = safe_int(presupuesto.get("maximum_bid"))

        cola = [
            f
            for f in (cola_datos.get("queue") or [])
            if isinstance(f, dict)
        ]

        base = {
            "available": False,
            "observer_only": True,

            # EL NOMBRE DE CADA UNO. Sin los dos nombres esto
            # seria otro numero suelto en una pantalla.
            "en_caja": en_caja,
            "en_caja_label": "lo que Pepe puede gastar hoy",

            "realizable": None,
            "realizable_label": "lo que entraria aceptando ofertas vivas",
            "realizable_n": 0,

            "total_si_se_vende": None,
            "techo_biwenger": techo,
            "techo_si_se_vende": None,

            "cola_vacia": not cola,
            "vendedores": [],
        }

        if not cola:
            return {
                **base,
                "reason": (
                    "La cola de venta llega vacia: sin saber quien "
                    "sobra no se puede decir cuanta caja es "
                    "realizable. Lo que Pepe puede gastar hoy son "
                    f"{_miles(en_caja)} EUR y de lo otro no hay "
                    "numero."
                ),
            }

        # Solo la caja de HOY: las ofertas vivas. Lo que valen a
        # precio de mercado exige publicarlos y que alguien los
        # compre, y eso no es caja, es una esperanza.
        con_oferta = [
            f
            for f in cola
            if f.get("cash_kind") == "OFERTA_VIVA"
            and safe_int(f.get("cash_now")) > 0
        ]

        realizable = sum(safe_int(f.get("cash_now")) for f in con_oferta)

        techo_despues = techo

        for fila in con_oferta:
            techo_despues = techo_tras_vender(
                techo_despues,
                safe_int(fila.get("cash_now")),
                safe_int(fila.get("price")),
            )

        return {
            **base,
            "available": True,
            "realizable": realizable,
            "realizable_n": len(con_oferta),
            "total_si_se_vende": en_caja + realizable,
            "techo_si_se_vende": techo_despues,
            "vendedores": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "position": f.get("position"),
                    "cash_now": safe_int(f.get("cash_now")),
                    "price": safe_int(f.get("price")),
                }
                for f in con_oferta
            ],
            "reason": (
                f"En caja para fichar hoy: {_miles(en_caja)} EUR. "
                f"Vendiendo a los {len(con_oferta)} de la cola que "
                f"ya tienen oferta viva entrarian "
                f"{_miles(realizable)} EUR mas, y el techo de "
                f"Biwenger pasaria de {_miles(techo)} a "
                f"{_miles(techo_despues)}. "
                "Son dos numeros distintos y ninguno sustituye al "
                "otro: el primero es dinero, el segundo es dinero "
                "si alguien acepta."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "en_caja": 0,
            "realizable": None,
            "realizable_n": 0,
            "cola_vacia": True,
            "vendedores": [],
            "reason": (
                f"No se pudo cruzar el presupuesto con la cola de "
                f"venta: {type(error).__name__}: {error}"
            ),
        }


# ============================================================
# LA OPERACION COMPLETA
# ============================================================


def _puntos_con_vara(puntos, position, factor_de) -> float:
    """
    Los puntos de una plaza, medidos con la vara de su posicion.

    `factor_de` entra por argumento -no se importa- para que las
    guardias puedan probar esto sin depender del entorno ni del
    modulo de la vara.
    """

    return float(puntos or 0) * float(factor_de(position))


def operacion_completa(
    candidato: dict,
    *,
    cola: list,
    guardarrail: dict | None,
    validador,
    factor_de,
    fichas_libres=None,
    presupuesto_en_caja: int = 0,
) -> dict:
    """
    Un fichaje entero: a quien se vende, cuanto se saca, si cabe
    la ficha y cuantos puntos netos gana el once.

    `validador` es `position_guardrail.validate_sale_set`. Entra
    por argumento para que quede escrito que esta pieza NO
    reescribe el guardarrail: lo llama.

    Nunca lanza.
    """

    try:
        coste = safe_int(candidato.get("market_price"))

        libres = (
            safe_int(fichas_libres) if fichas_libres is not None else None
        )

        # ------------------------------------------------
        # 1. ¿CABE LA FICHA?
        # ------------------------------------------------
        #
        # Con hueco libre no hace falta que salga nadie por la
        # ficha -otra cosa es el dinero-. Sin hueco, entra uno y
        # sale otro.
        cabe_sin_vender = bool(libres) and libres > 0

        # ------------------------------------------------
        # 2. A QUIEN SE VENDE
        # ------------------------------------------------
        #
        # Se cogen de la cola por orden hasta cubrir el coste, y
        # cada prefijo se valida con el guardarrail. Si meter al
        # siguiente rompiera el once, no se cuela: se aparta con
        # su motivo, igual que hace `sale_order`.
        vendiendo = []
        apartados = []
        caja = safe_int(presupuesto_en_caja)

        for fila in cola:

            if caja >= coste and (cabe_sin_vender or vendiendo):
                break

            comprobacion = validador(
                guardarrail,
                [f["id"] for f in vendiendo] + [fila.get("id")],
            )

            if not comprobacion.get("ok"):
                apartados.append(
                    {
                        "id": fila.get("id"),
                        "name": fila.get("name"),
                        "reason": comprobacion.get("reason"),
                    }
                )
                continue

            vendiendo.append(
                {
                    "id": fila.get("id"),
                    "name": fila.get("name"),
                    "position": fila.get("position"),
                    "cash_now": safe_int(fila.get("cash_now")),
                    "price": safe_int(fila.get("price")),
                    "points_per_matchday": fila.get("points_per_matchday"),
                }
            )

            caja += safe_int(fila.get("cash_now"))

        # ------------------------------------------------
        # 3. LOS PUNTOS NETOS DEL ONCE, CON LA VARA
        # ------------------------------------------------
        #
        # Doctrina 62: con las plazas llenas manda el punto por
        # plaza. El que entra suma su plaza; los que salen
        # restan la suya SOLO si estaban en el once.
        entran = _puntos_con_vara(
            candidato.get("points_per_matchday"),
            candidato.get("position"),
            factor_de,
        )

        salen = sum(
            _puntos_con_vara(
                v.get("points_per_matchday"),
                v.get("position"),
                factor_de,
            )
            for v in vendiendo
            if v.get("points_per_matchday") is not None
        )

        # Sin pronostico del que entra no hay resta que hacer: se
        # dice, no se estima.
        medible = candidato.get("points_per_matchday") is not None

        return {
            "id": candidato.get("id"),
            "name": candidato.get("name"),
            "position": candidato.get("position"),
            "market_price": coste,

            "free_slots": libres,
            "cabe_la_ficha": bool(cabe_sin_vender or vendiendo),
            "cabe_sin_vender": cabe_sin_vender,

            "vende_a": vendiendo,
            "apartados": apartados,
            "caja_tras_vender": caja,
            "financiada": caja >= coste,

            "puntos_que_entran": round(entran, 3) if medible else None,
            "puntos_que_salen": round(salen, 3),
            "puntos_netos": (
                round(entran - salen, 3) if medible else None
            ),
            "vara_puesta": True,

            "reason": (
                f"Cuesta {_miles(coste)} EUR. "
                + (
                    "Hay ficha libre: no tiene que salir nadie "
                    "por la plaza."
                    if cabe_sin_vender
                    else "No hay ficha libre: entra uno y sale otro."
                )
                + (
                    " Se cubre vendiendo a "
                    + ", ".join(str(v.get("name")) for v in vendiendo)
                    + f" ({_miles(caja)} EUR)."
                    if vendiendo
                    else (
                        f" Con {_miles(caja)} EUR en caja "
                        + (
                            "llega."
                            if caja >= coste
                            else "no llega y no hay a quien vender "
                            "sin romper el once."
                        )
                    )
                )
                + (
                    ""
                    if medible
                    else " Sin pronostico de titularidad no se "
                    "puede decir cuantos puntos gana el once: no se "
                    "estima."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "id": (candidato or {}).get("id"),
            "name": (candidato or {}).get("name"),
            "cabe_la_ficha": None,
            "vende_a": [],
            "apartados": [],
            "puntos_netos": None,
            "reason": (
                f"No se pudo montar la operacion: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 2 — EL MOTIVO ENTERO
# ============================================================
#
#     `roster_expansion_shadow.blocked_reason` publica, para los
#     candidatos que la via del once valora y el `intent` deja
#     fuera:
#
#         "La via del once le da valor, pero el `intent` se elige
#          por euros y gana la reventa"
#
#     Ese mecanismo -`max(opciones, key=value)`- solo corre con
#     `DEPLOYMENT_ENABLED` APAGADO, y por defecto esta ENCENDIDO
#     desde el 13/09 (`DEPLOYMENT_DEFAULT = "1"`). Con el
#     interruptor puesto la etiqueta la reparte
#     `deployment.classify_operation`, que es otro sitio y otra
#     regla.
#
#     EL MOTIVO NO ESTA TRUNCADO: ESTA CADUCADO. Y el dato bueno
#     ya viaja en la propia fila -`deployment.reason`,
#     `deployment.operation_class`, `market_gate.route_now`-, sin
#     que nadie lo lea.
#
#     Esto no arregla `blocked_reason`: escribe al lado el motivo
#     que la fila ya trae, entero, para que se pueda comparar.

# Las etiquetas que decide cada via, con lo que cuelga de cada
# una. El mapa del encargo: que decide cada `intent` y que se
# cae si se toca.
QUE_DECIDE_CADA_INTENT = {
    "SPECULATION": (
        "el liston del 3 % sobre el capital",
        "el minimo de 25.000 EUR de ganancia esperada",
        "el tope de prima de puja (+0,25 %)",
        "el bolsillo de especular en `budget_for_intent`",
        "la columna REVENDER de `los_dos_techos`",
    ),
    "XI_UPGRADE": (
        "el bolsillo de fichar en `budget_for_intent`",
        "la prioridad 1 de `signing_priority`",
        "la columna QUEDARSE de `los_dos_techos`",
        "el presupuesto que lee el ejecutor al escribir la puja",
        "sin liston de rendimiento y SIN TOPE DE PRIMA",
    ),
}


def motivo_entero(fila: dict) -> dict:
    """
    Por que este candidato no entra hoy como fichaje, con el
    mecanismo que de verdad lo decidio y sin cortar.

    Nunca lanza. Si la fila no trae de donde salio la etiqueta,
    se dice; no se rellena con el mecanismo de antes.
    """

    try:
        despliegue = (fila or {}).get("deployment") or {}
        compuerta = (fila or {}).get("market_gate") or {}

        intent = str((fila or {}).get("intent") or "").upper() or None

        # ¿Quien puso la etiqueta? Es la pregunta del encargo.
        if despliegue.get("enabled"):
            mecanismo = "deployment.classify_operation"

            explicacion = despliegue.get("reason") or (
                "La clase de operacion la decide `classify_operation` "
                "y no dejo motivo escrito."
            )

        elif despliegue:
            mecanismo = "max(opciones, key=value) en acquisition_valuation"

            explicacion = (
                "Con `DEPLOYMENT_ENABLED` apagado el `intent` sale "
                "de la via que da mas euros, no de la clase de "
                "operacion."
            )

        else:
            mecanismo = None

            explicacion = (
                "La fila no trae bloque `deployment`: no se puede "
                "saber quien puso la etiqueta, y no se adivina."
            )

        via = (
            despliegue.get("route")
            or compuerta.get("route_now")
            or (fila or {}).get("route")
        )

        cuelga = QUE_DECIDE_CADA_INTENT.get(intent, ())

        return {
            "intent": intent,
            "operation_class": despliegue.get("operation_class"),
            "decidido_por": mecanismo,
            "route": via,
            "de_esta_etiqueta_cuelga": list(cuelga),
            "truncado": False,
            "reason": (
                (
                    f"El `intent` es {intent or 'desconocido'}"
                    + (f" por la via {via}" if via else "")
                    + (f", puesto por {mecanismo}" if mecanismo else "")
                    + ". "
                    + explicacion
                    + (
                        " De esa etiqueta cuelgan: "
                        + "; ".join(cuelga)
                        + "."
                        if cuelga
                        else ""
                    )
                ).strip()
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "intent": None,
            "decidido_por": None,
            "de_esta_etiqueta_cuelga": [],
            "truncado": False,
            "reason": (
                f"No se pudo reconstruir el motivo: "
                f"{type(error).__name__}: {error}"
            ),
        }


# Los finales que delatan una frase cortada. Si un motivo
# publicado acaba en cualquiera de estos, el que lo lea se queda
# sin la mitad que explica.
FINALES_DE_FRASE_CORTADA = ("…", "...", ":", ",", ";", "y", "el", "la", "de")


def esta_truncado(texto) -> bool:
    """
    ¿Este motivo sale cortado?

    No mide longitud: mide si TERMINA como termina una frase a
    medias. Un motivo largo esta bien; uno que acaba en puntos
    suspensivos o en preposicion, no.
    """

    limpio = str(texto or "").strip()

    if not limpio:
        return True

    for final in FINALES_DE_FRASE_CORTADA:
        if limpio.endswith(final):
            return True

    return not limpio.endswith((".", "!", "?", "%", ")"))


# ============================================================
# BLOQUE 3 — LOS PREMIOS DE LA LIGA
# ============================================================
#
#     La discusion era si el pago es lineal. Se cierra con las
#     reglas de la liga y con lo que se pago de verdad.
#
#     `bonusPoint` = 30.000 EUR por punto, y ni `bonusFixed` ni
#     `bonusIdealLineup` ni `bonusGameMVP` valen nada. El unico
#     premio que no es lineal es `bonusRoundPosition`, y sus
#     indices son NEGATIVOS: se cuentan desde el FINAL.


def premios_de_la_jornada(settings: dict | None) -> dict:
    """
    Que paga la liga por jornada, leido de las reglas.

    `bonusRoundPosition` viene como [[indice, euros], ...]. Un
    indice NEGATIVO cuenta desde el ultimo: -1 es el ultimo
    clasificado, -2 el penultimo. Se lee tal cual, sin
    interpretar, y quien mire decide.
    """

    reglas = settings or {}

    por_punto = safe_int(reglas.get("bonusPoint"))

    posiciones = reglas.get("bonusRoundPosition") or []

    desde_el_final = []
    desde_arriba = []

    for entrada in posiciones:

        try:
            indice, euros = int(entrada[0]), safe_int(entrada[1])

        except (TypeError, ValueError, IndexError):
            continue

        if indice < 0:
            desde_el_final.append({"desde_el_final": -indice, "euros": euros})

        else:
            desde_arriba.append({"puesto": indice, "euros": euros})

    return {
        "available": bool(reglas),
        "euros_por_punto": por_punto,
        "premio_fijo": safe_int(reglas.get("bonusFixed")),
        "premio_once_ideal": safe_int(reglas.get("bonusIdealLineup")),
        "premio_mvp": safe_int(reglas.get("bonusGameMVP")),
        "invertido": bool(reglas.get("bonusInverse")),

        "premio_por_ganar": desde_arriba,
        "premio_por_quedar_ultimo": desde_el_final,

        "hay_premio_por_ganar": bool(desde_arriba),
        "hay_premio_por_quedar_ultimo": bool(desde_el_final),

        # NO CONSTA es una respuesta. Las reglas de jornada no
        # dicen nada de la clasificacion final, y no se inventa.
        "premio_de_final_de_temporada": None,
        "premio_de_final_de_temporada_reason": (
            "No consta: en las reglas de la liga no hay ninguna "
            "clave de premio por posicion final de temporada, y en "
            "el tablon no hay ningun evento que pague uno."
        ),

        # El separador de miles se pone jugador a jugador, no con
        # un `.replace(",", ".")` sobre la frase entera: eso se
        # come tambien las comas de la prosa y deja el motivo
        # escrito a trompicones.
        "reason": (
            f"{_miles(por_punto)} EUR por punto. "
            + (
                "Ningun premio por GANAR la jornada: los indices de "
                "`bonusRoundPosition` son negativos, o sea desde el "
                "final. "
                if desde_el_final and not desde_arriba
                else ""
            )
            + (
                "Premio por quedar de los ultimos: "
                + ", ".join(
                    f"{p['desde_el_final']}º por la cola "
                    f"{_miles(p['euros'])} EUR"
                    for p in desde_el_final
                )
                + "."
                if desde_el_final
                else ""
            )
        ),
    }


def comprobar_pago_lineal(resultados: list, euros_por_punto: int) -> dict:
    """
    Contra lo que se pago de verdad: ¿es `euros x puntos` y nada
    mas, o hay algo encima?

    `resultados` son las filas de un `roundFinished`: nombre,
    puntos y bonus. Se ordena por puntos y se compara cada fila
    con lo lineal. Lo que sobre se atribuye a su puesto DESDE EL
    FINAL, que es lo que dicen las reglas.
    """

    filas = [f for f in (resultados or []) if isinstance(f, dict)]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "reason": (
                "La jornada llega sin resultados: no hay pago que "
                "comprobar."
            ),
        }

    ordenadas = sorted(
        filas,
        key=lambda f: -safe_int(f.get("points")),
    )

    total = len(ordenadas)
    extras = []

    for puesto, fila in enumerate(ordenadas, start=1):

        lineal = safe_int(fila.get("points")) * safe_int(euros_por_punto)

        sobra = safe_int(fila.get("bonus")) - lineal

        if sobra:
            extras.append(
                {
                    "name": fila.get("name"),
                    "puesto": puesto,
                    "desde_el_final": total - puesto + 1,
                    "extra": sobra,
                }
            )

    gano = ordenadas[0]

    return {
        "available": True,
        "n": total,
        "ganador": gano.get("name"),
        "extra_del_ganador": (
            safe_int(gano.get("bonus"))
            - safe_int(gano.get("points")) * safe_int(euros_por_punto)
        ),
        "extras": extras,
        "lineal_para_todos": not extras,
        "reason": (
            "Todos cobraron exactamente puntos x euros: el pago es "
            "lineal de arriba abajo."
            if not extras
            else (
                f"{len(extras)} de {total} cobraron algo encima de "
                f"lo lineal, y ninguno es el ganador: "
                + ", ".join(
                    f"{e['name']} ({e['desde_el_final']}º por la "
                    f"cola, +{_miles(e['extra'])} EUR)"
                    for e in extras
                )
                + "."
            )
        ),
    }


# ============================================================
# BLOQUE 4 — LA PRIMA DEL COMPUTER, PARTIDA POR TRAMO
# ============================================================

TRAMOS = ("SUBIA", "PLANO", "BAJABA")


def direccion_de_la_vispera(precio_hoy, precio_ayer) -> str | None:
    """
    Que hizo el precio la vispera. None si no se sabe.
    """

    hoy = safe_int(precio_hoy)
    ayer = safe_int(precio_ayer)

    if not hoy or not ayer:
        return None

    if hoy > ayer:
        return "SUBIA"

    if hoy < ayer:
        return "BAJABA"

    return "PLANO"


def prima_por_tramo(censo: list) -> dict:
    """
    La prima del Computer partida por lo que hizo el precio la
    vispera, cada tramo con su `n`.

    `censo` son filas con `amount`, `price` y `price_previous`.
    Nunca lanza. Con el censo vacio NO publica tramos: publica
    que no hay censo.
    """

    try:
        filas = [f for f in (censo or []) if isinstance(f, dict)]

        if not filas:
            return {
                "available": False,
                "n": 0,
                "tramos": {},
                "reason": (
                    "El censo de ofertas llega vacio: sin ofertas no "
                    "hay prima que partir, y un tramo sin muestra no "
                    "se publica con un cero."
                ),
            }

        por_tramo: dict[str, list] = {t: [] for t in TRAMOS}
        sin_vispera = 0

        for fila in filas:

            precio = safe_int(fila.get("price"))
            importe = safe_int(fila.get("amount"))

            if not precio or not importe:
                sin_vispera += 1
                continue

            tramo = direccion_de_la_vispera(
                precio,
                fila.get("price_previous"),
            )

            if tramo is None:
                sin_vispera += 1
                continue

            por_tramo[tramo].append((importe / precio - 1) * 100)

        salida = {}

        for tramo in TRAMOS:

            primas = por_tramo[tramo]

            salida[tramo] = {
                "n": len(primas),

                # DOCTRINA 55: un agregado sin su `n` es una
                # anecdota. El `n` va dentro del tramo, no en una
                # nota al pie.
                "median_percent": (
                    round(statistics.median(primas), 4) if primas else None
                ),
                "mean_percent": (
                    round(statistics.mean(primas), 4) if primas else None
                ),
                "below_market": sum(1 for p in primas if p < 0),

                # Un tramo corto se MARCA y se queda con su
                # muestra. Fundirlo con el de al lado afirmaria
                # algo mas fuerte que el dato.
                "thin": len(primas) < 10,
            }

        medibles = sum(s["n"] for s in salida.values())

        return {
            "available": medibles > 0,
            "n": medibles,
            "sin_vispera": sin_vispera,
            "tramos": salida,
            "reason": (
                f"{medibles} ofertas con precio de la vispera "
                f"conocido de {len(filas)} del censo. "
                + "; ".join(
                    f"{t} n={salida[t]['n']} "
                    + (
                        f"mediana {salida[t]['median_percent']:+.4f} %"
                        if salida[t]["median_percent"] is not None
                        else "sin muestra"
                    )
                    for t in TRAMOS
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "tramos": {},
            "reason": (
                f"No se pudo partir la prima por tramo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def hueco_entre_tramos(partida: dict) -> dict:
    """
    Cuanto mas paga el Computer por los que bajaban, con el `n`
    de los dos tramos delante.

    Si a cualquiera de los dos le falta muestra, no se publica el
    hueco: se dice cual falta.
    """

    tramos = (partida or {}).get("tramos") or {}

    sube = tramos.get("SUBIA") or {}
    baja = tramos.get("BAJABA") or {}

    if not sube.get("n") or not baja.get("n"):
        return {
            "available": False,
            "n_subia": sube.get("n", 0),
            "n_bajaba": baja.get("n", 0),
            "reason": (
                "Falta muestra en uno de los dos tramos: sin las dos "
                "medianas no hay hueco que medir."
            ),
        }

    hueco = baja["median_percent"] - sube["median_percent"]

    return {
        "available": True,
        "n_subia": sube["n"],
        "n_bajaba": baja["n"],
        "gap_pp": round(hueco, 4),
        "thin": bool(sube.get("thin") or baja.get("thin")),
        "reason": (
            f"El Computer paga {hueco:+.4f} puntos porcentuales mas "
            f"por los que BAJABAN (n={baja['n']}, "
            f"{baja['median_percent']:+.4f} %) que por los que "
            f"SUBIAN (n={sube['n']}, {sube['median_percent']:+.4f} %)."
            + (
                " Uno de los dos tramos va corto de muestra: el "
                "numero se publica marcado."
                if sube.get("thin") or baja.get("thin")
                else ""
            )
        ),
    }
