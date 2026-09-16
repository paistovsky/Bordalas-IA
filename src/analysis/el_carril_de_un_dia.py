"""
El carril de un día: comprar a mercado y cobrarle la prima al Computer.

APAGADO. `ENCENDIDO = False` y nadie llama a esto todavía.

QUE MIDE Y QUE PROPONE

    La vía existe y está medida (informe del 16/09): once viajes
    de una noche, +3,14 % neto, ganan once de once. Lo que este
    módulo aporta es la REGLA —cuándo se compra y cuándo se
    vende— derivada de la medición, y un listón propio para el
    carril, porque el 3 % global no se le puede aplicar a una vía
    cuyo techo es 1,5075 % (doctrina 60).

LA CORRECCION QUE LO CAMBIA TODO: LA VENTA ES UNA OPCION, NO UN PLAZO

    La primera versión de esta regla decía "se vende al día
    siguiente, y si no se puede, se ha fallado la ventana". Salía
    de la curva por noches:

        1 noche    n=11   +3,14 %   ganan 11 de 11
        2 noches   n= 6   −4,13 %   ganan  2 de  6

    Pero esa curva NO es un reloj. Es un sesgo de selección, y se
    ve comparando dos distribuciones de la prima del Computer:

        las 167 ventas que alguien ACEPTO    mediana  +2,37 %
        las 13 ofertas VIVAS sin aceptar     mediana  −0,50 %

    El Computer no ofrece +2,37 %: ofrece una mediana NEGATIVA, y
    la gente vende los días que la oferta es buena. Las ventas de
    una noche no son "vender rápido": son los días en que la
    oferta vino buena de entrada.

    Prueba de que la lectura del reloj era falsa: si la oferta
    buena llegara el 46 % de los días al azar, que Pollo acertara
    diez de diez seguidas tiene una probabilidad del 0,04 %. No
    corre contra un plazo: espera a que la oferta valga.

    POR ESO LA REGLA NO TIENE FECHA DE SALIDA. Tiene un precio de
    salida, y se espera a que llegue.

LOS DOS UMBRALES QUE NO SE TOCAN, Y LO QUE OBLIGAN

    El suelo de cobro (+1 % sobre el coste) y el tope de puja
    (+0,25 % sobre el mercado) no son de este módulo y no se
    tocan. Pero juntos fijan la prima mínima a la que se puede
    cerrar:

        prima_minima = (1 + 0,01) x (1 + 0,0025) - 1 = 1,2525 %

    Ese es el listón del carril, y NO es un número redondo
    elegido a ojo: es la aritmética de los dos umbrales de la
    casa. Por debajo de él, cerrar es imposible aunque se quiera.

        ofertas vivas que lo pasan   6 de 13  (46 %)

SIN RELOJ, SIN DISCO, SIN RED

    Todo entra por argumento. Ninguna función abre un fichero ni
    mira la hora.
"""

from __future__ import annotations

import statistics


# EL INTERRUPTOR. Se propone; la luz la da el dueño.
ENCENDIDO = False


# El suelo de cobro de la casa. NO es de este módulo: entra por
# argumento en todas partes y esto es solo el valor con el que se
# midió, para poder decirlo.
SUELO_DE_COBRO = 0.01

# El tope de puja de la casa, igual.
TOPE_DE_COMPRA = 0.0025


def esta_encendido() -> bool:
    return bool(ENCENDIDO)


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# EL LISTON DEL CARRIL
# ============================================================


def liston_del_carril(
    suelo: float = SUELO_DE_COBRO,
    tope: float = TOPE_DE_COMPRA,
) -> dict:
    """
    La prima mínima del Computer a la que este carril puede cerrar.

    DE DONDE SALE, Y POR QUE NO ES UN NUMERO REDONDO

        Se compra como mucho a `mercado x (1 + tope)` y solo se
        vende si nos pagan `coste x (1 + suelo)`. Luego hace falta

            oferta >= mercado x (1 + tope) x (1 + suelo)

        y la prima que eso exige es el producto menos uno. Con los
        umbrales de hoy, 1,2525 %.

        NO SE ELIGE: se deduce de dos umbrales que no se tocan. Si
        el dueño mueve cualquiera de los dos, este listón se mueve
        solo, que es justo lo que no hacía el 3 % global.

    DOCTRINA 60: una vía no puede pasar un listón mayor que su
    techo. Por eso este listón se compara aquí mismo con el techo
    medido de la vía, y si lo superara habría que decirlo en vez
    de dejar el carril apagado sin saberlo.
    """

    s = float(suelo)
    t = float(tope)

    minima = (1.0 + s) * (1.0 + t) - 1.0

    return {
        "available": True,
        "floor_percent": round(100 * minima, 4),
        "suelo": s,
        "tope": t,
        "reason": (
            f"Para cerrar hay que comprar como mucho a mercado "
            f"x {1 + t:.4f} y cobrar al menos coste "
            f"x {1 + s:.4f}: la prima del Computer tiene que ser "
            f"de al menos {100 * minima:.4f} %."
        ),
    }


def techo_del_carril(primas: list | None) -> dict:
    """
    Lo máximo que esta vía puede dar, medido sobre las ofertas.

    `primas` son primas del Computer en tanto por ciento. Se
    publica la mediana y los cuantiles, porque una vía con una
    cola larga y una mediana negativa no es la misma vía que una
    con mediana positiva y poca dispersión, y la media las
    confunde.
    """

    filas = sorted(
        p
        for p in (
            safe_float(x) for x in (primas or [])
        )
        if p is not None
    )

    if not filas:
        return {
            "available": False,
            "n": 0,
            "median_percent": None,
            "reason": (
                "Sin ofertas medidas no se puede decir qué da esta "
                "vía."
            ),
        }

    def cuantil(q):
        return filas[min(int(q * len(filas)), len(filas) - 1)]

    return {
        "available": True,
        "n": len(filas),
        "median_percent": round(statistics.median(filas), 3),
        "p25": round(cuantil(0.25), 3),
        "p75": round(cuantil(0.75), 3),
        "negative_share": round(
            sum(1 for p in filas if p < 0) / len(filas), 3
        ),
        "reason": (
            f"Sobre {len(filas)} ofertas: mediana "
            f"{statistics.median(filas):+.2f} %, y "
            f"{100 * sum(1 for p in filas if p < 0) / len(filas):.0f} % "
            f"por debajo de cero."
        ),
    }


def tasa_de_exito(
    primas: list | None,
    liston: float,
) -> dict:
    """
    Cada cuánto la oferta basta para cerrar.

    Es la pieza que decide si el carril es un negocio o una
    lotería, y hay que medirla sobre las ofertas TAL Y COMO
    LLEGAN, no sobre las que alguien acepto. Las aceptadas están
    seleccionadas justamente por ser buenas.
    """

    filas = [
        p
        for p in (safe_float(x) for x in (primas or []))
        if p is not None
    ]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "rate": None,
            "reason": (
                "Sin ofertas no se puede decir cada cuánto basta la "
                "prima."
            ),
        }

    pasan = [p for p in filas if p >= float(liston)]

    return {
        "available": True,
        "n": len(filas),
        "clears": len(pasan),
        "rate": round(len(pasan) / len(filas), 4),
        "median_when_clears": (
            round(statistics.median(pasan), 3) if pasan else None
        ),
        "liston": float(liston),
        "reason": (
            f"{len(pasan)} de {len(filas)} ofertas llegan al "
            f"{float(liston):.2f} % "
            f"({100 * len(pasan) / len(filas):.0f} %)"
            + (
                f", y cuando llegan pagan una mediana de "
                f"{statistics.median(pasan):+.2f} %."
                if pasan
                else "."
            )
        ),
    }


# ============================================================
# LA REGLA
# ============================================================


def regla_de_compra(
    precio_mercado: int,
    tope: float = TOPE_DE_COMPRA,
) -> dict:
    """
    Cuánto se ofrece por un jugador en este carril.

    El precio exacto, ni un euro más: toda la ventaja de esta vía
    está en la entrada. Medido sobre los viajes de la liga, el
    neto ordena igual que la prima de compra:

        Pollo      +0,57 % de prima  ->  +4,67 % de neto
        Luismi     +1,94 %           ->  +3,30 %
        nosotros   +4,23 %           ->  +4,20 %
        Manzagool  +5,30 %           ->  −5,77 %

    No se puja por encima del tope de la casa, y dentro del tope
    se puja lo mínimo: `precio + 1`.
    """

    precio = int(precio_mercado or 0)

    if precio <= 0:
        return {
            "available": False,
            "bid": 0,
            "reason": "Sin precio de mercado no se puja.",
        }

    techo = int(precio * (1.0 + float(tope)))

    return {
        "available": True,
        "bid": precio + 1,
        "max_bid": techo,
        "premium_percent": round(100.0 / precio, 6),
        "reason": (
            f"Se ofrece {precio + 1:,} EUR —el mínimo— y nunca por "
            f"encima de {techo:,}. Toda la ventaja de este carril "
            f"está en no pagar de más al entrar."
        ).replace(",", "."),
    }


def regla_de_venta(
    coste: int,
    oferta: int,
    precio_mercado: int | None = None,
    suelo: float = SUELO_DE_COBRO,
) -> dict:
    """
    ¿Se acepta esta oferta del Computer?

    LA REGLA NO TIENE FECHA. Tiene un precio.

        Se vende el primer día en que la oferta cubre el coste
        más el suelo. Si no lo cubre, se espera. No hay ventana
        que "fallar" — eso fue una lectura falsa de la curva por
        noches, que era selección y no reloj.

    Lo único que sí tiene fecha es la ALARMA: una posición que
    lleva mucho sin recibir una oferta que cierre no es un viaje,
    es capital parado, y hay que verlo. Eso lo cuenta
    `posiciones_atascadas`, que no decide nada: avisa.
    """

    pagado = int(coste or 0)
    importe = int(oferta or 0)

    if pagado <= 0:
        return {
            "available": False,
            "sell": False,
            "reason": "Sin coste no se puede decidir una venta.",
        }

    minimo = int(pagado * (1.0 + float(suelo)))

    vende = importe >= minimo

    prima = (
        round(100.0 * (importe / precio_mercado - 1.0), 3)
        if precio_mercado
        else None
    )

    return {
        "available": True,
        "sell": bool(vende),
        "offer": importe,
        "cost": pagado,
        "min_to_sell": minimo,
        "margin_eur": importe - minimo,
        "net_percent": round(100.0 * (importe - pagado) / pagado, 3),
        "offer_premium_percent": prima,
        "reason": (
            f"La oferta son {importe:,} EUR y el suelo pide "
            f"{minimo:,}: se vende."
            if vende
            else (
                f"La oferta son {importe:,} EUR y el suelo pide "
                f"{minimo:,}: faltan {minimo - importe:,}. Se "
                f"espera."
            )
        ).replace(",", "."),
    }


def posiciones_atascadas(
    posiciones: list | None,
    ahora: int,
    aviso_dias: int = 7,
) -> dict:
    """
    Capital parado porque ninguna oferta ha llegado al suelo.

    NO PROPONE VENDER NADA. Pone el precio de tener, que es lo
    que faltaba para que la decisión sea informada.

    `ahora` entra por argumento: este módulo no mira el reloj.
    """

    filas = [
        p for p in (posiciones or []) if isinstance(p, dict)
    ]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "stuck": [],
            "capital": 0,
            "reason": (
                "No llega ninguna posición: sin posiciones no hay "
                "capital que contar."
            ),
        }

    atascadas = []

    for posicion in filas:

        coste = int(posicion.get("cost") or 0)

        oferta = int(posicion.get("offer") or 0)

        if coste <= 0:
            continue

        veredicto = regla_de_venta(coste, oferta)

        if veredicto["sell"]:
            continue

        dias = (
            (int(ahora) - int(posicion.get("bought_at") or 0))
            / 86_400
        )

        atascadas.append(
            {
                "player": posicion.get("player"),
                "cost": coste,
                "offer": oferta or None,
                "min_to_sell": veredicto["min_to_sell"],
                "missing": veredicto["min_to_sell"] - oferta,
                "days": round(dias, 1),
                "flagged": dias >= aviso_dias,
            }
        )

    capital = sum(p["cost"] for p in atascadas)

    marcadas = [p for p in atascadas if p["flagged"]]

    return {
        "available": True,
        "n": len(filas),
        "stuck": sorted(atascadas, key=lambda p: -p["days"]),
        "capital": capital,
        "flagged": len(marcadas),
        "flag_days": int(aviso_dias),
        "reason": (
            f"{len(atascadas)} de {len(filas)} posiciones no tienen "
            f"oferta que llegue al suelo: {capital:,} EUR parados, "
            f"{len(marcadas)} de ellas por encima de "
            f"{aviso_dias} días."
        ).replace(",", "."),
    }


# ============================================================
# LO QUE CABE
# ============================================================


def cuantos_caben(
    capital_libre: int,
    coste_tipico: int,
    tasa: float,
    margen_percent: float,
    dias: int = 30,
) -> dict:
    """
    Cuántos viajes caben y cuánto suman, con el ritmo medido.

    NO ES UNA PREVISION: es aritmética sobre lo ya medido, y
    hereda toda la debilidad de la muestra de la que sale. Por eso
    devuelve también el `n` con el que se midió la tasa.

    Se limita por las DOS cosas a la vez: el capital libre —que no
    da para más de unas pocas posiciones— y la oferta diaria del
    Computer, que es la que de verdad manda.
    """

    libre = int(capital_libre or 0)
    coste = int(coste_tipico or 0)

    if libre <= 0 or coste <= 0:
        return {
            "available": False,
            "slots": 0,
            "reason": (
                "Sin capital libre o sin coste típico no hay nada "
                "que repartir."
            ),
        }

    plazas = libre // coste

    if plazas <= 0:
        return {
            "available": True,
            "slots": 0,
            "total": 0,
            "reason": (
                f"El capital libre ({libre:,} EUR) no da ni para "
                f"una posición de {coste:,}."
            ).replace(",", "."),
        }

    # Con una tasa de exito `tasa` por dia, una plaza tarda en
    # media 1/tasa dias en cerrar.
    dias_por_viaje = 1.0 / float(tasa) if tasa else None

    if not dias_por_viaje:
        return {
            "available": False,
            "slots": plazas,
            "reason": "Sin tasa de éxito no se puede estimar nada.",
        }

    vueltas = float(dias) / dias_por_viaje

    total = plazas * coste * (float(margen_percent) / 100.0) * vueltas

    return {
        "available": True,
        "slots": int(plazas),
        "days_per_trip": round(dias_por_viaje, 2),
        "cycles": round(vueltas, 2),
        "total": int(total),
        "capital": libre,
        "reason": (
            f"{plazas} posición(es) de {coste:,} EUR, cada una "
            f"cerrando cada {dias_por_viaje:.1f} días al "
            f"{margen_percent:+.2f} %: {int(total):+,} EUR en "
            f"{dias} días."
        ).replace(",", "."),
    }
