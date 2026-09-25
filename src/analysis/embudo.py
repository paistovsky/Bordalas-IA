"""
Donde muere cada objetivo del mercado.

LA PIEZA QUE EL DUEÑO LLEVABA DOS NOCHES PIDIENDO

    "De los 20 del escaparate: cuantos mueren por precio,
     cuantos por el tope por operacion, cuantos por el liston de
     rendimiento, cuantos por calidad y cuantos por
     disponibilidad. Una tabla. Con eso delante se decide que
     aflojar, y no antes."

EL EMBUDO MENTIA (25/09/2026)

    El censo de las puertas lo midio sobre las tres fotos que hay:

        el embudo daba por VIVOS   49 · 40 · 19
        se podia pujar por          0 ·  2 ·  0

    Por tres fallos, y los tres a la vez:

        1. Contaba a los de los RIVALES, que no se pueden comprar:
           la compra de rivales esta cerrada por orden del dueño.
        2. Todo lo que no conocia lo daba por VIVO. No conocia
           `RENDIMIENTO_INSUFICIENTE`, `PROBABILIDAD_INSUFICIENTE`
           ni `MERCADO_DE_RIVAL`, asi que esos pasaban "todos los
           filtros".
        3. Llamaba "no mejora el once" a TODO `SIN_VALOR`. Y eso
           escondia a la regla 2 del `market_rate_gate`, que era
           la puerta decisiva de 31 de 60.

    "Ese embudo me tuvo una semana buscando puertas cerradas
     mientras el problema era una resta."

AHORA

    · Solo cuenta el mercado del COMPUTER. Los de rivales van
      aparte, con cuantos pasarian si la puerta estuviera abierta.
    · Cada objetivo muere en UNA puerta: la primera que le corta
      en el orden en que corre el codigo. Una decision que el
      embudo no conoce sale como `DESCONOCIDA`, nunca como viva.
    · Lo que no tiene valor se separa por lo que de verdad lo
      mato: la compuerta de ritmo -si con ella abierta habria
      tenido valor- o ninguna via.
    · La ultima linea es la que importa: "hoy se puede pujar por
      N". Con un cero si es cero.

EL ORDEN EN QUE CORRE EL CODIGO

    1. La valoracion, `value_candidate`. Cinco vias en paralelo;
       solo mata si mueren todas (`SIN_VALOR`). Aqui se cuenta LA
       DECISIVA: si con la compuerta de ritmo abierta habria
       valido algo (`market_gate.value_before > 0`), le mato la
       compuerta, y se dice cual de sus tres reglas.
    2. La cadena del tablero: contraoferta, puja fuera del
       Computer, estado del jugador. `NO_DISPONIBLE` pisa a un
       `SIN_VALOR` anterior en la decision publicada, pero aqui
       cuenta donde murio primero.
    3. `optimal_bid`, en su orden.
    4. `BID`: pujable.

NO DECIDE NADA

    Cuenta cadaveres. No mueve ni un tope ni un liston.
"""

from __future__ import annotations


# Las puertas, en el orden en que corre el codigo. Cambiarlo
# cambia la tabla, asi que esta escrito una sola vez y aqui.
CAUSAS = (
    ("PRECIO_INVALIDO", "Sin precio de mercado valido."),
    (
        "REGLA_1_SIN_RITMO",
        "La compuerta de ritmo: el ojeador no tiene ritmo de este "
        "jugador, y sin el ninguna otra via le daba valor.",
    ),
    (
        "REGLA_2_PRECIO_CAYENDO",
        "La compuerta de ritmo: el precio baja o esta quieto, y "
        "con ella abierta habria tenido valor.",
    ),
    (
        "REGLA_3_RACHA_SIN_DEMANDA",
        "La compuerta de ritmo: racha con el pulso en contra, y "
        "con ella abierta habria tenido valor.",
    ),
    (
        "SIN_VALOR",
        "No vale nada por ninguna via, ni con la compuerta abierta.",
    ),
    ("CONTRAOFERTA", "Es nuestro y se lo estamos pidiendo a un rival."),
    (
        "PUJA_FUERA_DEL_COMPUTER",
        "Tenemos puja viva fuera del Computer.",
    ),
    (
        "DISPONIBILIDAD",
        "No se puede alinear: lesion, sancion o no disponible.",
    ),
    ("NO_COMPENSA", "Vale menos que lo que cuesta."),
    ("PRECIO", "Cuesta mas de lo que hay, incluso vendiendo antes."),
    (
        "TOPE_POR_OPERACION",
        "Cabe en la caja pero no en el tope por operacion.",
    ),
    ("SIN_MARGEN", "Ningun importe entre el precio y el valor."),
    ("EV_NEGATIVO", "Ninguna puja con valor esperado positivo."),
    (
        "RENDIMIENTO_INSUFICIENTE",
        "Especulacion que no llega al rendimiento minimo.",
    ),
    (
        "GANANCIA_INSUFICIENTE",
        "Especulacion que deja demasiado poco para gastar el turno.",
    ),
    (
        "PROBABILIDAD_INSUFICIENTE",
        "La mejor puja gana demasiado pocas veces.",
    ),
    (
        "DESCONOCIDA",
        "Una decision que el embudo no conoce. No se da por viva: "
        "si aparece, hay que ensenarle esa puerta.",
    ),
    ("PUJABLE", "Pasa todas las puertas: hoy se puede pujar por el."),
)

VIVE = "PUJABLE"


# Las decisiones del tablero que son su propia puerta.
DECISION_A_CAUSA = {
    "PRECIO_INVALIDO": "PRECIO_INVALIDO",
    "SIN_VALOR": "SIN_VALOR",
    "CONTRAOFERTA": "CONTRAOFERTA",
    "PUJA_FUERA_DEL_COMPUTER": "PUJA_FUERA_DEL_COMPUTER",
    "NO_DISPONIBLE": "DISPONIBILIDAD",
    "NO_COMPENSA": "NO_COMPENSA",
    "SUPERA_PRESUPUESTO": "PRECIO",
    "SIN_MARGEN": "SIN_MARGEN",
    "EV_NEGATIVO": "EV_NEGATIVO",
    "RENDIMIENTO_INSUFICIENTE": "RENDIMIENTO_INSUFICIENTE",
    "GANANCIA_INSUFICIENTE": "GANANCIA_INSUFICIENTE",
    "PROBABILIDAD_INSUFICIENTE": "PROBABILIDAD_INSUFICIENTE",
    "BID": VIVE,
}


# Lo que publica `market_gate.gate` para cada regla de la compuerta.
COMPUERTA_A_CAUSA = {
    "SIN_RITMO_OBSERVADO": "REGLA_1_SIN_RITMO",
    "PRECIO_CAYENDO": "REGLA_2_PRECIO_CAYENDO",
    "RACHA_SIN_DEMANDA": "REGLA_3_RACHA_SIN_DEMANDA",
}

COMPUERTA_ABIERTA = "RITMO_OBSERVADO"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def es_de_rival(objetivo: dict) -> bool:
    """Lo vende un manager, no el Computer."""

    return bool(
        objetivo.get("seller_id") is not None
        or objetivo.get("rival_market")
        or str(objetivo.get("decision") or "").upper() == "MERCADO_DE_RIVAL"
    )


def la_puerta(objetivo: dict) -> str:
    """
    Donde murio este objetivo del Computer, en el orden en que
    corre el codigo.
    """

    decision = str(objetivo.get("decision") or "").upper()

    if decision == "PRECIO_INVALIDO":
        return "PRECIO_INVALIDO"

    compuerta = objetivo.get("market_gate") or {}
    puerta = compuerta.get("gate")

    # LA VALORACION VA PRIMERO. Si no vale nada por ninguna via,
    # la cadena del tablero puede haber escrito NO_DISPONIBLE
    # encima, pero el objetivo ya habia muerto antes.
    sin_valor = (
        safe_int(objetivo.get("our_value")) <= 0
        if "our_value" in objetivo
        else decision == "SIN_VALOR"
    )

    if sin_valor or decision == "SIN_VALOR":
        if (
            puerta
            and puerta != COMPUERTA_ABIERTA
            and safe_int(compuerta.get("value_before")) > 0
        ):
            return COMPUERTA_A_CAUSA.get(puerta, "DESCONOCIDA")
        return "SIN_VALOR"

    causa = DECISION_A_CAUSA.get(decision)

    if causa is None:
        return "DESCONOCIDA"

    # `SUPERA_PRESUPUESTO` mezcla dos cosas: no tener el dinero, y
    # tenerlo pero no poder ponerlo de una vez. Aflojar una no
    # arregla la otra, asi que se separan.
    if causa == "PRECIO":
        tope = safe_int(objetivo.get("budget_applied"))
        precio = safe_int(objetivo.get("market_price"))
        if tope and precio and precio <= tope:
            return "TOPE_POR_OPERACION"

    return causa


def embudo(acquisition: dict | None) -> dict:
    """
    Donde muere cada objetivo del Computer hoy, y por cuantos se
    puede pujar. Los de rivales, aparte.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "targets": 0,
        "alive": 0,
        "pujables": 0,
        "rows": [],
        "deaths": [],
        "rivales": {"n": 0, "pasarian": 0, "nombres": []},
        "ultima_linea": None,
        "reason": None,
    }

    try:
        todos = [
            o for o in ((acquisition or {}).get("targets") or [])
            if isinstance(o, dict)
        ]

        del_computer = [o for o in todos if not es_de_rival(o)]
        de_rivales = [o for o in todos if es_de_rival(o)]

        rivales = {
            "n": len(de_rivales),
            "pasarian": sum(1 for o in de_rivales if o.get("would_pass")),
            "nombres": [o.get("name") for o in de_rivales if o.get("would_pass")],
            "reason": (
                f"{len(de_rivales)} de rivales: no se cuentan, la compra "
                f"de rivales esta cerrada. Con la puerta abierta "
                f"pasarian {sum(1 for o in de_rivales if o.get('would_pass'))}."
            ),
        }

        if not del_computer:
            return {
                **vacio,
                "available": bool(todos),
                "rivales": rivales,
                "ultima_linea": "Hoy se puede pujar por 0.",
                "reason": (
                    "No hay ningun objetivo del Computer que contar. "
                    "Hoy se puede pujar por 0."
                ),
            }

        filas = []
        cuenta = {nombre: 0 for nombre, _ in CAUSAS}

        for objetivo in del_computer:
            causa = la_puerta(objetivo)
            cuenta[causa] = cuenta.get(causa, 0) + 1
            valor = safe_int(objetivo.get("our_value"))
            precio = safe_int(objetivo.get("market_price"))
            filas.append({
                "name": objetivo.get("name"),
                "position": safe_int(objetivo.get("position")),
                "price": precio,
                "our_value": valor,
                "cause": causa,
                "decision": objetivo.get("decision"),
                # Lo que decia la via del once, que no es la causa
                # pero ayuda a leerla.
                "xi_decision": objetivo.get("xi_decision"),
                "gap": valor - precio if valor and precio else None,
                "reason": objetivo.get("reason"),
            })

        total = len(del_computer)

        muertes = [
            {
                "cause": nombre,
                "what": explicacion,
                "count": cuenta.get(nombre, 0),
                "percent": round(100 * cuenta.get(nombre, 0) / total, 1),
            }
            for nombre, explicacion in CAUSAS
        ]

        pujables = cuenta.get(VIVE, 0)
        ultima = f"Hoy se puede pujar por {pujables}."

        return {
            "available": True,
            "targets": total,
            "alive": pujables,
            "pujables": pujables,
            "rows": sorted(filas, key=lambda f: f["cause"]),
            "deaths": sorted(muertes, key=lambda m: -m["count"]),
            "rivales": rivales,
            "ultima_linea": ultima,
            "reason": _reason(muertes, total, pujables) + " " + ultima,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar el embudo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(muertes: list, total: int, pujables: int) -> str:

    # ORDENADAS AQUI, NO FUERA (20/09/2026): el titular cita la
    # causa MAYOR, no la primera en el orden de la tabla.
    mortales = sorted(
        (m for m in muertes if m["count"] and m["cause"] != VIVE),
        key=lambda m: -m["count"],
    )

    if not mortales:
        return f"Los {total} objetivos del Computer pasan todas las puertas."

    mayor = mortales[0]

    frase = (
        f"De {total} objetivos del Computer, {pujables} pasan todas "
        f"las puertas. Donde mas mueren es {mayor['cause']}: "
        f"{mayor['count']} de {total} ({mayor['percent']} %)."
    )

    if mayor["percent"] >= 50:
        frase += (
            " Mas de la mitad mueren en el mismo sitio, asi que es "
            "ahi donde hay que mirar antes de tocar nada."
        )

    desconocidas = next(
        (m["count"] for m in muertes if m["cause"] == "DESCONOCIDA"), 0
    )

    if desconocidas:
        frase += (
            f" OJO: {desconocidas} con una decision que el embudo no "
            f"conoce; no se cuentan como vivos."
        )

    return frase
