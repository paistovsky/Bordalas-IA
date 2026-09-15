"""
Cuanto se paga por encima del precio, y contra que precio.

LA PREGUNTA, Y POR QUE NO SE PODIA CONTESTAR

    "Pagamos un 8 % de mas y cobramos un 2 %: cada viaje nace
    seis puntos bajo el agua."

    El 8 % estaba medido contra LA FOTO DEL DIA: el catalogo de
    un `snapshot_*.json` tomado el mismo dia de la compra. Dos
    cosas lo rompen:

    1. LAS FOTOS TIENEN UN AGUJERO. Del 18/08 al 09/09 no hay
       ninguna. De nuestras 24 compras, solo 5 caen en un dia con
       foto. Una mediana de cinco.

    2. Y LA FOTO NO ES DEL MOMENTO DE LA COMPRA. Nuestras
       compras se resuelven a las 07:0x de Madrid; la foto del
       13/09 es de las 17:17. Diez horas despues, y los precios
       se mueven todos los dias.

    Medido: para Trent, la foto dice 2.730.000 y nuestro propio
    registro de puja anoto 2.760.000. La foto daba +1,10 % donde
    la verdad era +0,00 %.

LA REFERENCIA BUENA: EL PRECIO DEL DIA

    `data/autopilot/price_history.json` guarda una serie por
    jugador con marca de tiempo, y cubre del 16/08 al 15/09 sin
    huecos. Con el, 21 de nuestras 24 compras tienen referencia.

    Y LA HORA NO SE SUPONE, SE MIDE. Sobre 11.252 cambios de
    precio observados, el 89,8 % aparece por primera vez en la
    muestra de las 07h de Madrid; el 99,9 % ha entrado antes de
    las 10h. Asi que:

        precio del dia = la PRIMERA muestra de ese dia (Madrid)
                         a partir de las 07:00

    `cuando_cambian_los_precios` recalcula ese histograma desde
    la serie que se le pase: la regla es medible, no una opinion
    escrita en un comentario.

CONTRASTADA CONTRA NUESTRO PROPIO LIBRO

    `bid_outcome_ledger` anota el `market_price` que el motor
    veia al pujar. De las 15 pujas anotadas EN VIVO, el precio
    del dia coincide AL EURO en 11; las 4 que no, se pujaron
    antes de las 07:00 y el precio cambio entre la puja y la
    resolucion, que es exactamente lo que esta referencia dice
    que pasa.

    De las 10 anotadas RECONSTRUYENDO la plantilla a posteriori,
    no coincide ninguna — y tampoco deberia: su `market_price`
    es el del dia en que se reconstruyo, no el de la compra. Por
    eso esas no valen como contraste.

DOCTRINA 54: NO SE RESTAN PERIODOS DISTINTOS

    "Compramos al +8 % y vendemos al +2 %" resta dos numeros
    medidos sobre muestras distintas, de meses distintos y con
    referencias distintas. `bajo_el_agua` solo devuelve la resta
    cuando las dos mitades cubren el MISMO periodo, y si no,
    dice que no se puede.

SIN RELOJ, SIN DISCO, SIN RED

    Todo entra por argumento. No hay `datetime.now` en ningun
    sitio: las unicas fechas que se miran son las de los eventos.

MADRID ES UTC+2 AQUI

    Los datos van del 09/08 al 15/09/2026, entero dentro del
    horario de verano. Se usa un desplazamiento fijo, igual que
    `scripts/los_viajes_de_los_rivales.py`. El dia que esto tenga
    que cruzar el ultimo domingo de octubre, hara falta una zona
    de verdad — y la guardia lo dice en su cabecera.
"""

from __future__ import annotations

import bisect
import collections
import statistics

from datetime import datetime, timedelta, timezone


MADRID = timezone(timedelta(hours=2))

# LA HORA A LA QUE EL MERCADO CAMBIA DE PRECIO.
#
#     No es un umbral del motor: es una observacion sobre
#     Biwenger, y `cuando_cambian_los_precios` la recalcula.
HORA_DEL_CAMBIO = 7

TIPOS_DE_OPERACION = ("market", "transfer")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _mediana(valores):
    return statistics.median(valores) if valores else None


def _media(valores):
    return statistics.fmean(valores) if valores else None


# ============================================================
# LAS OPERACIONES
# ============================================================


def operaciones(eventos: list) -> list:
    """
    Cada cambio de manos, una sola vez, con sus pujas perdedoras.

    Misma huella que `caja_de_la_liga.reconstruir`: si dos
    modulos deduplicaran distinto, los numeros dejarian de
    cuadrar por una razon que no seria el error de nadie.
    """

    vistos = set()

    filas = []

    for evento in sorted(
        [e for e in (eventos or []) if isinstance(e, dict)],
        key=lambda e: safe_int(e.get("date")),
    ):

        tipo = evento.get("type")

        if tipo not in TIPOS_DE_OPERACION:
            continue

        contenido = evento.get("content")

        if not isinstance(contenido, list):
            continue

        for operacion in contenido:

            if not isinstance(operacion, dict):
                continue

            vendedor = (operacion.get("from") or {}).get("id")
            comprador = (operacion.get("to") or {}).get("id")
            importe = safe_int(operacion.get("amount"))

            huella = (
                tipo,
                safe_int(evento.get("date")),
                operacion.get("player"),
                vendedor,
                comprador,
                importe,
            )

            if huella in vistos:
                continue

            vistos.add(huella)

            pujas = operacion.get("bids") or []

            filas.append(
                {
                    "type": tipo,
                    "date": safe_int(evento.get("date")),
                    "player": operacion.get("player"),
                    "amount": importe,
                    "seller": vendedor,
                    "buyer": comprador,

                    # LAS PUJAS PERDEDORAS VIENEN ESCRITAS. No
                    # hay que estimar la competencia de una
                    # subasta: el tablon la publica.
                    #
                    #     Y SE CUENTAN AQUI, sobre la operacion ya
                    #     deduplicada. Contandolas sobre los
                    #     eventos crudos, una subasta reemitida
                    #     suma sus perdedores dos veces: a Pollo
                    #     le salian 60 pujas perdidas donde tiene
                    #     46.
                    "losers": [
                        (b.get("user") or {}).get("id")
                        for b in pujas
                        if isinstance(b, dict)
                        and (b.get("user") or {}).get("id")
                        and (b.get("user") or {}).get("id")
                        != comprador
                    ],
                }
            )

    for fila in filas:
        fila["rivals"] = len(fila["losers"])

    return filas


# ============================================================
# EL PRECIO DEL DIA
# ============================================================


def indexar_precios(historico) -> dict:
    """
    {player_id: (marcas_de_tiempo, precios)}, ordenado.

    Acepta el `players` de `price_history.json`, que guarda cada
    serie como {"t": [...], "p": [...]}.
    """

    salida = {}

    for clave, serie in (historico or {}).items():

        if not isinstance(serie, dict):
            continue

        marcas = serie.get("t") or []
        precios = serie.get("p") or []

        if not marcas or len(marcas) != len(precios):
            continue

        pares = sorted(
            zip(
                (safe_int(t) for t in marcas),
                (safe_int(p) for p in precios),
            )
        )

        salida[safe_int(clave)] = (
            [t for t, _ in pares],
            [p for _, p in pares],
        )

    return salida


def cuando_cambian_los_precios(indice: dict) -> dict:
    """
    A que hora de Madrid aparece por primera vez un precio nuevo.

    LA REGLA SE MIDE, NO SE ESCRIBE. `HORA_DEL_CAMBIO` es una
    afirmacion sobre Biwenger, y una afirmacion sobre el mundo que
    no se puede recalcular es una opinion con cara de constante.
    """

    horas = collections.Counter()

    for marcas, precios in (indice or {}).values():

        for i in range(1, len(precios)):

            if precios[i] != precios[i - 1]:
                horas[
                    datetime.fromtimestamp(
                        marcas[i], MADRID
                    ).hour
                ] += 1

    total = sum(horas.values())

    dominante = horas.most_common(1)[0][0] if horas else None

    return {
        "available": bool(total),
        "horas": dict(sorted(horas.items())),
        "cambios": total,
        "hora_dominante": dominante,
        "parte_en_la_dominante": (
            horas[dominante] / total if total else None
        ),
    }


def precio_del_dia(indice: dict, jugador, cuando) -> int | None:
    """
    El precio vigente el dia (Madrid) de la operacion.

    La PRIMERA muestra de ese dia a partir de `HORA_DEL_CAMBIO`.
    Si ese dia no hay ninguna muestra a esa hora o despues,
    devuelve None: NO SE ESTIMA NI SE COGE LA DE LA VISPERA.
    """

    serie = (indice or {}).get(safe_int(jugador))

    if not serie:
        return None

    marcas, precios = serie

    dia = datetime.fromtimestamp(
        safe_int(cuando), MADRID
    ).date()

    # La serie esta ordenada: se entra por el primer instante del
    # dia y se sale en cuanto se pasa.
    desde = int(
        datetime(
            dia.year, dia.month, dia.day, tzinfo=MADRID
        ).timestamp()
    )

    i = bisect.bisect_left(marcas, desde)

    while i < len(marcas):

        momento = datetime.fromtimestamp(marcas[i], MADRID)

        if momento.date() != dia:
            return None

        if momento.hour >= HORA_DEL_CAMBIO:
            return precios[i]

        i += 1

    return None


# ============================================================
# LA PRIMA
# ============================================================


def _mes(cuando) -> str:
    return datetime.fromtimestamp(
        safe_int(cuando), MADRID
    ).strftime("%Y-%m")


def primas(eventos: list, indice: dict) -> dict:
    """
    Lo que cada uno paga de mas al comprar y cobra de mas al
    vender, contra el precio del dia. Forma fija, nunca lanza.

    Una operacion sin precio del dia NO entra con una referencia
    inventada: se cuenta aparte en `sin_referencia`.
    """

    vacio = {
        "available": False,
        "managers": {},
        "computer": {},
        "operations": 0,
        "reason": None,
    }

    try:
        filas = operaciones(eventos)

        if not filas:
            return {
                **vacio,
                "reason": (
                    "El tablon llega vacio: sin operaciones no "
                    "hay prima que medir."
                ),
            }

        if not indice:
            return {
                **vacio,
                "operations": len(filas),
                "reason": (
                    "El almacen de precios llega vacio: sin "
                    "precio del dia no se puede medir ninguna "
                    "prima. No se sustituye por la foto."
                ),
            }

        gente = collections.defaultdict(
            lambda: {
                "compras": [],
                "ventas": [],
                "compras_sin_referencia": [],
                "ventas_sin_referencia": [],
            }
        )

        del_computer = []

        for fila in filas:

            referencia = precio_del_dia(
                indice, fila["player"], fila["date"]
            )

            apunte = {
                "player": fila["player"],
                "date": fila["date"],
                "mes": _mes(fila["date"]),
                "amount": fila["amount"],
                "reference": referencia,
                "premium": (
                    (fila["amount"] - referencia)
                    / referencia
                    * 100.0
                    if referencia
                    else None
                ),
                "rivals": fila["rivals"],
                "disputed": fila["rivals"] > 0,
            }

            if fila["buyer"]:
                destino = (
                    "compras"
                    if referencia
                    else "compras_sin_referencia"
                )
                gente[fila["buyer"]][destino].append(apunte)

            # VENTA AL COMPUTER: `transfer` sin `to`. Las ventas
            # entre managers no cuentan aqui — el precio lo pone
            # una persona, no la formula de recompra.
            if (
                fila["type"] == "transfer"
                and fila["seller"]
                and not fila["buyer"]
            ):
                destino = (
                    "ventas"
                    if referencia
                    else "ventas_sin_referencia"
                )
                gente[fila["seller"]][destino].append(apunte)

                if referencia:
                    del_computer.append(apunte)

        managers = {
            quien: _resumen(fila)
            for quien, fila in gente.items()
            if quien
        }

        return {
            "available": True,
            "managers": managers,
            "computer": _bloque(
                [a["premium"] for a in del_computer]
            ),
            "computer_por_mes": {
                mes: _bloque(
                    [
                        a["premium"]
                        for a in del_computer
                        if a["mes"] == mes
                    ]
                )
                for mes in sorted(
                    {a["mes"] for a in del_computer}
                )
            },
            "operations": len(filas),
            "reason": (
                f"{len(filas)} operaciones de "
                f"{len(managers)} managers, con el precio del "
                f"dia de `price_history`."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir la prima: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _bloque(valores) -> dict:
    """
    Un resumen que NUNCA viaja sin su `n`.

    Regla de la casa: cada numero con su n. Aqui es estructural —
    no se puede leer la mediana de este diccionario sin tener el
    `n` delante.
    """

    limpios = [v for v in (valores or []) if v is not None]

    return {
        "n": len(limpios),
        "median": _mediana(limpios),
        "mean": _media(limpios),
        "worst": max(limpios) if limpios else None,
        "best": min(limpios) if limpios else None,
    }


def _resumen(fila: dict) -> dict:
    compras = fila["compras"]

    ventas = fila["ventas"]

    def por(apuntes, cond):
        return _bloque(
            [a["premium"] for a in apuntes if cond(a)]
        )

    meses = sorted({a["mes"] for a in compras})

    return {
        "buys": _bloque([a["premium"] for a in compras]),
        "buys_detail": compras,
        "buys_without_reference": len(
            fila["compras_sin_referencia"]
        ),
        "buys_without_reference_detail": (
            fila["compras_sin_referencia"]
        ),

        "sells_to_computer": _bloque(
            [a["premium"] for a in ventas]
        ),
        "sells_without_reference": len(
            fila["ventas_sin_referencia"]
        ),

        # ¿PAGA DE MAS PORQUE LE DISPUTAN, O SIEMPRE?
        "undisputed": por(compras, lambda a: not a["disputed"]),
        "disputed": por(compras, lambda a: a["disputed"]),

        "by_month": {
            mes: {
                "all": por(compras, lambda a, m=mes: a["mes"] == m),
                "undisputed": por(
                    compras,
                    lambda a, m=mes: a["mes"] == m
                    and not a["disputed"],
                ),
                "disputed": por(
                    compras,
                    lambda a, m=mes: a["mes"] == m
                    and a["disputed"],
                ),
            }
            for mes in meses
        },

        "sells_by_month": {
            mes: _bloque(
                [
                    a["premium"]
                    for a in ventas
                    if a["mes"] == mes
                ]
            )
            for mes in sorted({a["mes"] for a in ventas})
        },
    }


# ============================================================
# DOCTRINA 54: LA RESTA SOLO VALE SI CUBRE EL MISMO PERIODO
# ============================================================


def bajo_el_agua(resumen: dict, mes: str | None = None) -> dict:
    """
    Cuanto nace bajo el agua un viaje: prima de venta menos prima
    de compra.

    SOLO SI LAS DOS MITADES CUBREN EL MISMO PERIODO.

        "Compramos al +8 % y cobramos el +2 %" restaba una
        mediana de 5 compras medidas contra fotos de dias
        sueltos, contra una prima de venta medida sobre otra
        muestra y otros meses. La resta salia -6 puntos y no
        significaba nada.

    Si falta una de las dos mitades, o si se pide un mes en el
    que solo hay una, devuelve `available: False` y lo dice. No
    se rellena el hueco con el numero de otro periodo.
    """

    vacio = {
        "available": False,
        "months": 0,
        "buy": None,
        "sell": None,
        "difference": None,
        "reason": None,
    }

    if not resumen:
        return {**vacio, "reason": "No hay resumen que restar."}

    if mes:
        compra = (resumen.get("by_month") or {}).get(mes, {}).get(
            "all"
        ) or {"n": 0}

        venta = (resumen.get("sells_by_month") or {}).get(
            mes
        ) or {"n": 0}

        etiqueta = mes

    else:
        compra = resumen.get("buys") or {"n": 0}

        venta = resumen.get("sells_to_computer") or {"n": 0}

        etiqueta = "todo el periodo"

    if not compra.get("n") or not venta.get("n"):
        return {
            **vacio,
            "buy": compra,
            "sell": venta,
            "reason": (
                f"En {etiqueta} hay {compra.get('n', 0)} compras "
                f"y {venta.get('n', 0)} ventas con referencia: "
                f"sin las dos mitades la resta no significa "
                f"nada (doctrina 54)."
            ),
        }

    diferencia = venta["median"] - compra["median"]

    return {
        "available": True,
        "months": 1 if mes else len(
            resumen.get("by_month") or {}
        ),
        "buy": compra,
        "sell": venta,
        "difference": diferencia,
        "reason": (
            f"En {etiqueta}: compra {compra['median']:+.2f} % "
            f"(n={compra['n']}) contra venta "
            f"{venta['median']:+.2f} % (n={venta['n']}). "
            + (
                f"Cada viaje nace {abs(diferencia):.2f} puntos "
                f"bajo el agua."
                if diferencia < 0
                else f"Cada viaje nace {diferencia:.2f} puntos "
                f"por encima del agua."
            )
        ),
    }
