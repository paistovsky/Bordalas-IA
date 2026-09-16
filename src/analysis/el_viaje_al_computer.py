"""
El viaje al Computer: comprar un jugador y vendérselo.

LA DEFINICION, EN UN SOLO SITIO

    Un VIAJE es comprar un jugador y vendérselo al Computer:

        compra   cuanto pagamos y que prima sobre el mercado de
                 aquel dia
        espera   cuantos dias, y cuanto se movio el precio
        venta    cuanto nos dio el Computer y que prima sobre el
                 mercado de aquel dia
        neto     venta - compra, en euros y en %

    Las tres cuentas del informe -la liga, los nuestros y el
    rendimiento por dia- salen de `viajes()`. No hay una segunda
    definicion en ningun sitio: `test_un_viaje_al_computer_es_comprar_y_venderle`
    lo comprueba.

DE DONDE SALE CADA PATA, Y COMO SE RECONOCE

    El tablon (`board_events.json`) trae tres formas de mover un
    jugador, y se distinguen por quien aparece:

        COMPRA AL COMPUTER   evento `market`, con `to` (quien la
                             gano) y la lista de pujas perdedoras.
                             Es la subasta diaria.

        VENTA AL COMPUTER    evento `transfer` con `from` y SIN
                             `to`. Si hubiera `to` seria un
                             traspaso entre managers, que se pacta
                             y no dice nada de lo que paga el
                             Computer.

        TRASPASO             evento `transfer` con `from` Y `to`.

    Medido sobre el tablon del 16/09/2026: 175 compras, 178
    ventas, 9 traspasos. NINGUNA venta es el Computer revendiendo
    -no existe el evento inverso-, asi que las 178 son managers
    vendiendole, que es justo lo que hariamos nosotros.

EL DENOMINADOR, QUE ES DONDE ESTA LA TRAMPA

    La prima de compra y la prima de venta tienen que salir de
    LOS MISMOS viajes, no de dos muestras distintas (doctrina 54).
    Comparar "+2,17 % que pagamos" con "+2,03 % que paga el
    Computer" cuando cada numero viene de un conjunto distinto de
    operaciones no resta: son dos medias de dos cosas.

    Aqui cada viaje lleva sus dos primas, medidas contra el precio
    de mercado DE SU DIA, y el neto se calcula viaje a viaje.

LO QUE NO SE PUEDE FECHAR NO CUENTA

    Un precio que no se puede fechar no se estima: el viaje va a
    un monton aparte, se cuenta y se dice. El almacen de precios
    empieza el 12/08 y el tablon el 10/08, asi que hay operaciones
    que no se pueden medir. Es una limitacion honesta.

SIN RELOJ, SIN DISCO, SIN RED

    Todo entra por argumento, incluida la funcion de precios.
    Ninguna funcion de este modulo abre un fichero ni mira la
    hora.
"""

from __future__ import annotations

import statistics


SEGUNDOS_POR_DIA = 86_400

# Solo vendemos si nos pagan el coste +1 %. No es un umbral de
# este modulo: es el de la casa, y entra por argumento para poder
# medir con otros sin tocarlo.
SUELO_DE_COBRO = 0.01

# Una operacion que se aparta un 50 % del mercado no describe la
# regla del Computer: describe un precio mal fechado.
MAX_PRIMA_ABSOLUTA = 0.50


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


# ============================================================
# LAS TRES FORMAS DE MOVER UN JUGADOR
# ============================================================


def _movimientos(events: list | None, tipo: str):
    for evento in events or []:

        if not isinstance(evento, dict):
            continue

        if evento.get("type") != tipo:
            continue

        instante = safe_int(evento.get("date"))

        for movimiento in evento.get("content") or []:

            if isinstance(movimiento, dict):
                yield instante, movimiento


def compras_en_el_mercado(events: list | None) -> list:
    """
    Subastas del Computer que alguien gano.

    `to` es quien la gano y `amount` lo que pago. `bids` son las
    pujas perdedoras, asi que de aqui sale tambien con cuantos
    rivales se peleo.
    """

    salida = []
    vistas = set()

    for instante, movimiento in _movimientos(events, "market"):

        jugador = movimiento.get("player")
        importe = safe_int(movimiento.get("amount"))
        comprador = (movimiento.get("to") or {}).get("name")

        if jugador is None or importe <= 0 or not comprador:
            continue

        # El tablon se re-descarga y el mismo hecho puede llegar
        # con dos ids. Contado dos veces pesa el doble.
        firma = (safe_int(jugador), instante, importe, comprador)

        if firma in vistas:
            continue

        vistas.add(firma)

        salida.append(
            {
                "player_id": safe_int(jugador),
                "amount": importe,
                "date": instante,
                "manager": comprador,
                "rivals": len(movimiento.get("bids") or []),
                "via": "MERCADO",
            }
        )

    return salida


def ventas_al_computer(events: list | None) -> list:
    """
    Ventas de un manager al Computer: con vendedor y SIN comprador.
    """

    salida = []
    vistas = set()

    for instante, movimiento in _movimientos(events, "transfer"):

        if movimiento.get("to"):
            continue

        vendedor = (movimiento.get("from") or {}).get("name")

        jugador = movimiento.get("player")
        importe = safe_int(movimiento.get("amount"))

        if jugador is None or importe <= 0 or not vendedor:
            continue

        firma = (safe_int(jugador), instante, importe)

        if firma in vistas:
            continue

        vistas.add(firma)

        salida.append(
            {
                "player_id": safe_int(jugador),
                "amount": importe,
                "date": instante,
                "manager": vendedor,
            }
        )

    return salida


def traspasos_entre_managers(events: list | None) -> list:
    """
    Con vendedor Y comprador. No son viajes al Computer, pero SI
    son una forma de adquirir al jugador que luego se le vende.
    """

    salida = []
    vistas = set()

    for instante, movimiento in _movimientos(events, "transfer"):

        vendedor = (movimiento.get("from") or {}).get("name")
        comprador = (movimiento.get("to") or {}).get("name")

        if not vendedor or not comprador:
            continue

        jugador = movimiento.get("player")
        importe = safe_int(movimiento.get("amount"))

        if jugador is None or importe <= 0:
            continue

        firma = (
            safe_int(jugador),
            instante,
            importe,
            vendedor,
            comprador,
        )

        if firma in vistas:
            continue

        vistas.add(firma)

        salida.append(
            {
                "player_id": safe_int(jugador),
                "amount": importe,
                "date": instante,
                "manager": comprador,
                "rivals": 0,
                "via": "TRASPASO",
            }
        )

    return salida


# ============================================================
# EL VIAJE
# ============================================================


def viajes(
    compras: list | None,
    ventas: list | None,
    price_at=None,
    suelo: float = SUELO_DE_COBRO,
) -> dict:
    """
    Empareja cada venta al Computer con la compra que la precede.

    COMO SE EMPAREJA

        Por (manager, jugador) y en orden de tiempo, primero en
        entrar primero en salir. Una venta busca la compra mas
        antigua de ese manager de ese jugador que siga abierta; si
        no hay ninguna, la venta queda HUERFANA y se cuenta
        aparte. Un manager puede comprar y vender al mismo jugador
        varias veces y cada par es un viaje.

    `price_at(player_id, cuando)` devuelve el precio de mercado de
    aquel momento, o 0 si no se puede fechar. SIN ESA FUNCION NO
    SE MIDE NINGUNA PRIMA: usar el precio de hoy es el sesgo que
    `historical_price_lookup` nacio para quitar. Los viajes se
    devuelven igual, con las primas en `None`.

    Forma fija, nunca lanza.
    """

    entradas = sorted(
        (c for c in (compras or []) if isinstance(c, dict)),
        key=lambda c: safe_int(c.get("date")),
    )

    salidas = sorted(
        (v for v in (ventas or []) if isinstance(v, dict)),
        key=lambda v: safe_int(v.get("date")),
    )

    abiertas: dict = {}

    for compra in entradas:
        clave = (compra.get("manager"), safe_int(compra.get("player_id")))
        abiertas.setdefault(clave, []).append(compra)

    hechos = []
    huerfanas = []

    for venta in salidas:

        clave = (venta.get("manager"), safe_int(venta.get("player_id")))

        cola = abiertas.get(clave) or []

        compra = None

        for candidata in cola:
            if safe_int(candidata.get("date")) <= safe_int(
                venta.get("date")
            ):
                compra = candidata
                break

        if compra is None:
            huerfanas.append(venta)
            continue

        cola.remove(compra)

        pagado = safe_int(compra.get("amount"))
        cobrado = safe_int(venta.get("amount"))

        dias = (
            safe_int(venta.get("date")) - safe_int(compra.get("date"))
        ) / SEGUNDOS_POR_DIA

        mercado_compra = (
            safe_int(price_at(compra["player_id"], compra["date"]))
            if price_at
            else 0
        )

        mercado_venta = (
            safe_int(price_at(venta["player_id"], venta["date"]))
            if price_at
            else 0
        )

        prima_compra = (
            pagado / mercado_compra - 1.0
            if mercado_compra > 0
            else None
        )

        prima_venta = (
            cobrado / mercado_venta - 1.0
            if mercado_venta > 0
            else None
        )

        # Una prima imposible no describe al Computer: describe un
        # precio mal fechado. Se marca y no entra en las medianas
        # de primas, pero el neto en euros SIGUE siendo bueno,
        # porque los dos importes son hechos del tablon.
        fechado = (
            prima_compra is not None
            and prima_venta is not None
            and abs(prima_compra) <= MAX_PRIMA_ABSOLUTA
            and abs(prima_venta) <= MAX_PRIMA_ABSOLUTA
        )

        neto = cobrado - pagado

        hechos.append(
            {
                "manager": venta.get("manager"),
                "player_id": venta["player_id"],
                "bought_at": compra["date"],
                "sold_at": venta["date"],
                "paid": pagado,
                "collected": cobrado,
                "days": round(dias, 2),
                "via": compra.get("via"),
                "rivals": compra.get("rivals"),
                "market_on_buy": mercado_compra or None,
                "market_on_sell": mercado_venta or None,
                "buy_premium": (
                    round(prima_compra * 100, 3)
                    if prima_compra is not None
                    else None
                ),
                "sell_premium": (
                    round(prima_venta * 100, 3)
                    if prima_venta is not None
                    else None
                ),
                "priced": fechado,
                "net_eur": neto,
                "net_percent": (
                    round(100.0 * neto / pagado, 3) if pagado else None
                ),
                "net_percent_per_day": (
                    round(100.0 * neto / pagado / dias, 4)
                    if pagado and dias > 0
                    else None
                ),
                # EL SUELO DE COBRO: solo vendemos si nos pagan el
                # coste +1 %. Se evalua sobre lo que se pago, que
                # es lo que hace la casa.
                "clears_floor": cobrado >= pagado * (1.0 + float(suelo)),
            }
        )

    sin_cerrar = [c for cola in abiertas.values() for c in cola]

    return {
        "available": bool(hechos),
        "trips": hechos,
        "n": len(hechos),
        "orphan_sales": huerfanas,
        "open_positions": sin_cerrar,
        "floor": float(suelo),
        "reason": (
            f"{len(hechos)} viaje(s) cerrado(s); "
            f"{len(huerfanas)} venta(s) sin compra que las preceda "
            f"y {len(sin_cerrar)} compra(s) todavia sin vender."
            if hechos
            else (
                "Ninguna venta al Computer se puede emparejar con "
                "una compra anterior: sin viajes no hay nada que "
                "medir."
            )
        ),
    }


# ============================================================
# LO QUE DAN
# ============================================================


def resumen(trips: list | None, suelo: float = SUELO_DE_COBRO) -> dict:
    """
    Neto, dias y rendimiento por dia, cada uno con su `n`.

    DOCTRINA 53: el rendimiento por viaje no es un rendimiento. Lo
    que se compara con otra via es el porcentaje POR DIA DE
    CAPITAL INMOVILIZADO, y por eso se publica el mediano de los
    ratios y no el ratio de las medianas — un viaje de 20 dias y
    otro de uno no se promedian como si fueran lo mismo.

    Forma fija, nunca lanza.
    """

    filas = [t for t in (trips or []) if isinstance(t, dict)]

    vacio = {
        "available": False,
        "n": 0,
        "net_eur_total": 0,
        "net_eur_median": None,
        "net_percent_median": None,
        "days_median": None,
        "percent_per_day_median": None,
        "winners": 0,
        "losers": 0,
        "clears_floor": 0,
        "priced_n": 0,
        "buy_premium_median": None,
        "sell_premium_median": None,
        "premium_gap": None,
        "best": None,
        "worst": None,
        "reason": "Sin viajes no hay agregado que dar.",
    }

    if not filas:
        return vacio

    netos = [t["net_eur"] for t in filas]

    porcentajes = [
        t["net_percent"] for t in filas if t["net_percent"] is not None
    ]

    dias = [t["days"] for t in filas if t.get("days") is not None]

    por_dia = [
        t["net_percent_per_day"]
        for t in filas
        if t.get("net_percent_per_day") is not None
    ]

    # LAS DOS PRIMAS, DE LOS MISMOS VIAJES (doctrina 54).
    fechados = [t for t in filas if t.get("priced")]

    primas_compra = [t["buy_premium"] for t in fechados]
    primas_venta = [t["sell_premium"] for t in fechados]

    mejor = max(filas, key=lambda t: t["net_eur"])
    peor = min(filas, key=lambda t: t["net_eur"])

    return {
        "available": True,
        "n": len(filas),
        "net_eur_total": sum(netos),
        "net_eur_median": statistics.median(netos),
        "net_percent_median": (
            round(statistics.median(porcentajes), 3)
            if porcentajes
            else None
        ),
        "net_percent_n": len(porcentajes),
        "days_median": (
            round(statistics.median(dias), 2) if dias else None
        ),
        "days_n": len(dias),
        "percent_per_day_median": (
            round(statistics.median(por_dia), 4) if por_dia else None
        ),
        "percent_per_day_n": len(por_dia),
        "winners": sum(1 for t in filas if t["net_eur"] > 0),
        "losers": sum(1 for t in filas if t["net_eur"] < 0),
        "clears_floor": sum(1 for t in filas if t.get("clears_floor")),
        "priced_n": len(fechados),
        "buy_premium_median": (
            round(statistics.median(primas_compra), 3)
            if primas_compra
            else None
        ),
        "sell_premium_median": (
            round(statistics.median(primas_venta), 3)
            if primas_venta
            else None
        ),
        # LA CUENTA QUE PUEDE MATARLO TODO: si la prima de compra
        # se come la de venta, el viaje nace en perdida.
        "premium_gap": (
            round(
                statistics.median(primas_venta)
                - statistics.median(primas_compra),
                3,
            )
            if primas_compra and primas_venta
            else None
        ),
        "best": mejor,
        "worst": peor,
        "floor": float(suelo),
        "reason": (
            f"{len(filas)} viaje(s): neto mediano "
            f"{statistics.median(netos):+,.0f} EUR en "
            f"{statistics.median(dias) if dias else 0:.1f} dias "
            f"medianos."
        ).replace(",", "."),
    }


def dias_hasta_cruzar_el_suelo(
    trips: list | None,
    suelo: float = SUELO_DE_COBRO,
) -> dict:
    """
    Cuanto tarda un viaje en llegar a coste +1 %.

    Solo se puede contestar con los que YA cruzaron: los que no
    cruzaron no tienen ese dia, y meterlos como si hubieran
    tardado "lo que llevan" mezclaria dos cosas. Se cuentan
    aparte.
    """

    filas = [t for t in (trips or []) if isinstance(t, dict)]

    cruzan = [t for t in filas if t.get("clears_floor")]

    no_cruzan = [t for t in filas if not t.get("clears_floor")]

    dias = [t["days"] for t in cruzan if t.get("days") is not None]

    return {
        "available": bool(dias),
        "n": len(filas),
        "crossed": len(cruzan),
        "did_not_cross": len(no_cruzan),
        "days_median": (
            round(statistics.median(dias), 2) if dias else None
        ),
        "days_n": len(dias),
        "floor": float(suelo),
        "reason": (
            f"{len(cruzan)} de {len(filas)} viajes pasaron el suelo "
            f"de coste +{100 * suelo:.0f} %, en "
            f"{statistics.median(dias):.1f} dias medianos."
            if dias
            else (
                f"Ninguno de los {len(filas)} viajes paso el suelo "
                f"de coste +{100 * suelo:.0f} %."
            )
        ),
    }


def por_manager(trips: list | None) -> dict:
    """
    Quien hace esto, cuantas veces y con que resultado.
    """

    filas = [t for t in (trips or []) if isinstance(t, dict)]

    agrupado: dict = {}

    for viaje in filas:
        agrupado.setdefault(viaje.get("manager") or "?", []).append(
            viaje
        )

    return {
        nombre: resumen(lista)
        for nombre, lista in sorted(
            agrupado.items(), key=lambda kv: -len(kv[1])
        )
    }


def cuanto_cabe_en_un_mes(
    medido: dict | None,
    capital: int,
    dias: int = 30,
) -> dict:
    """
    Con el capital y el ritmo medidos, cuanto suma un mes.

    NO ES UNA PROYECCION DE LO QUE VA A PASAR: es aritmetica sobre
    lo que ya paso. Si la mediana fuese de un puñado de viajes, el
    numero hereda esa debilidad, y por eso viaja con su `n`.
    """

    vacio = {
        "available": False,
        "cycles": None,
        "total": None,
        "reason": "Sin ritmo medido no se proyecta nada.",
    }

    if not medido or not medido.get("available"):
        return vacio

    dias_por_viaje = medido.get("days_median")

    neto = medido.get("net_percent_median")

    if not dias_por_viaje or dias_por_viaje <= 0 or neto is None:
        return {
            **vacio,
            "reason": (
                "El ritmo medido no trae dias o no trae neto: sin "
                "los dos no hay cuenta."
            ),
        }

    vueltas = float(dias) / float(dias_por_viaje)

    total = capital * (neto / 100.0) * vueltas

    return {
        "available": True,
        "capital": int(capital),
        "days": int(dias),
        "days_per_trip": dias_por_viaje,
        "net_percent_per_trip": neto,
        "cycles": round(vueltas, 2),
        "total": int(total),
        "n": medido.get("n"),
        "reason": (
            f"Con {capital:,} EUR rotando cada "
            f"{dias_por_viaje:.1f} dias al {neto:+.2f} % por "
            f"viaje: {vueltas:.1f} vueltas en {dias} dias, "
            f"{int(total):+,} EUR (sobre n={medido.get('n')} "
            f"viajes medidos)."
        ).replace(",", "."),
    }
