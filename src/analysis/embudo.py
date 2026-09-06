"""
Donde muere cada objetivo del mercado.

LA PIEZA QUE EL DUEÑO LLEVABA DOS NOCHES PIDIENDO

    "De los 20 del escaparate: cuantos mueren por precio,
     cuantos por el tope por operacion, cuantos por el liston de
     rendimiento, cuantos por calidad y cuantos por
     disponibilidad. Una tabla. Con eso delante se decide que
     aflojar, y no antes."

    La regla 9 de la doctrina dice que la via de comprar lo que
    sube esta "construida y casi nunca dispara". Esto contesta
    por que, con nombres y con cuentas, en vez de con una
    sospecha.

POR QUE UNA CAUSA Y NO VARIAS

    Un objetivo puede fallar tres filtros a la vez. Si se
    contaran todos, la tabla sumaria mas de 20 y no diria donde
    hay que mirar.

    Asi que se cuenta LA PRIMERA por la que muere, en el orden en
    que el motor las aplica: primero si se puede alinear, luego
    si sirve para algo, luego si el dinero llega, y al final si
    el rendimiento compensa.

    Y se publica tambien cuantos filtros mas habria fallado, por
    si aflojar el primero no sirviera de nada.

NO DECIDE NADA

    Cuenta cadaveres. No mueve ni un tope ni un liston: eso lo
    decide el dueño con esta tabla delante.
"""

from __future__ import annotations


# El orden en que el motor mata. Cambiarlo cambia la tabla, asi
# que esta escrito una sola vez y aqui.
CAUSAS = (
    (
        "DISPONIBILIDAD",
        "No se puede alinear: lesion, sancion o no disponible.",
    ),
    (
        "NO_MEJORA_EL_ONCE",
        "No vale para nuestro once: la posicion ya esta mejor "
        "cubierta.",
    ),
    (
        "PRECIO",
        "Cuesta mas de lo que hay, incluso vendiendo antes.",
    ),
    (
        "TOPE_POR_OPERACION",
        "Cabe en la caja pero no en el tope por operacion.",
    ),
    (
        "RENDIMIENTO",
        "Se puede pagar, pero no deja margen suficiente.",
    ),
    (
        "SIN_DATOS",
        "Falta el dato con el que se valora.",
    ),
    (
        "VIVE",
        "Pasa todos los filtros.",
    ),
)


DECISION_A_CAUSA = {
    "NO_DISPONIBLE": "DISPONIBILIDAD",
    "SIN_VALOR": "NO_MEJORA_EL_ONCE",
    "SUPERA_PRESUPUESTO": "PRECIO",
    "NO_COMPENSA": "RENDIMIENTO",
    "SIN_PRECIO": "SIN_DATOS",
    "SIN_RITMO": "SIN_DATOS",
    "BID": "VIVE",
    "PUJA": "VIVE",
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _causa(objetivo: dict) -> str:
    """Por que murio este, en el orden en que el motor mata."""

    decision = str(objetivo.get("decision") or "").upper()

    if decision in DECISION_A_CAUSA:

        causa = DECISION_A_CAUSA[decision]

        # EL MATIZ QUE HACE UTIL LA TABLA
        #
        #     `SUPERA_PRESUPUESTO` mezcla dos cosas muy
        #     distintas: no tener el dinero, y tenerlo pero no
        #     poder ponerlo de una vez. Aflojar una no arregla la
        #     otra, asi que se separan.
        if causa == "PRECIO":

            tope = safe_int(objetivo.get("budget_applied"))
            precio = safe_int(objetivo.get("market_price"))

            if tope and precio and precio <= tope:
                return "TOPE_POR_OPERACION"

        return causa

    if not decision:
        return "SIN_DATOS"

    return "VIVE"


def _tambien_fallaba(objetivo: dict, causa: str) -> list:
    """
    Que otros filtros habria fallado igualmente.

    Sirve para saber si aflojar el primero cambiaria algo o el
    objetivo moriria dos metros mas adelante.
    """

    otros = []

    valor = safe_int(objetivo.get("our_value"))
    precio = safe_int(objetivo.get("market_price"))
    tope = safe_int(objetivo.get("budget_applied"))

    if causa != "NO_MEJORA_EL_ONCE" and valor <= 0:
        otros.append("NO_MEJORA_EL_ONCE")

    if (
        causa not in ("PRECIO", "TOPE_POR_OPERACION")
        and tope
        and precio > tope
    ):
        otros.append("TOPE_POR_OPERACION")

    if (
        causa != "RENDIMIENTO"
        and valor
        and precio
        and valor <= precio
    ):
        otros.append("RENDIMIENTO")

    if (
        causa != "DISPONIBILIDAD"
        and str(objetivo.get("availability") or "").upper()
        not in ("DISPONIBLE", "OK", "")
    ):
        otros.append("DISPONIBILIDAD")

    return otros


def embudo(acquisition: dict | None) -> dict:
    """
    Donde muere cada objetivo del escaparate de hoy.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "targets": 0,
        "alive": 0,
        "rows": [],
        "deaths": [],
        "reason": None,
    }

    try:
        objetivos = (acquisition or {}).get("targets") or []

        if not objetivos:
            return {
                **vacio,
                "reason": (
                    "El escaparate esta vacio: no hay nada que "
                    "contar."
                ),
            }

        filas = []
        cuenta = {nombre: 0 for nombre, _ in CAUSAS}

        for objetivo in objetivos:

            causa = _causa(objetivo)
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
                "also_failed": _tambien_fallaba(objetivo, causa),

                # Cuanto le falta, cuando se puede decir.
                "gap": (
                    valor - precio
                    if valor and precio
                    else None
                ),
                "reason": objetivo.get("reason"),
            })

        muertes = [
            {
                "cause": nombre,
                "what": explicacion,
                "count": cuenta.get(nombre, 0),
                "percent": round(
                    100 * cuenta.get(nombre, 0) / len(objetivos),
                    1,
                ),
            }
            for nombre, explicacion in CAUSAS
        ]

        vivos = cuenta.get("VIVE", 0)

        return {
            "available": True,
            "targets": len(objetivos),
            "alive": vivos,
            "rows": sorted(filas, key=lambda f: f["cause"]),
            "deaths": sorted(
                muertes,
                key=lambda m: -m["count"],
            ),
            "reason": _reason(muertes, len(objetivos), vivos),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar el embudo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(muertes: list, total: int, vivos: int) -> str:

    # ORDENADAS AQUI, NO FUERA (20/09/2026)
    #
    #     Esta funcion recibia la lista en orden de CAUSAS y
    #     cogia la primera con muertos, no la mayor: decia que la
    #     causa mas comun era DISPONIBILIDAD con 2 cuando eran 12
    #     por no mejorar el once. El titular apuntaba al sitio
    #     equivocado, que es justo lo que esta tabla existe para
    #     evitar.
    mortales = sorted(
        (
            m
            for m in muertes
            if m["count"] and m["cause"] != "VIVE"
        ),
        key=lambda m: -m["count"],
    )

    if not mortales:
        return f"Los {total} objetivos pasan todos los filtros."

    mayor = mortales[0]

    frase = (
        f"De {total} objetivos, {vivos} pasan todos los filtros. "
        f"La causa de muerte mas comun es {mayor['cause']}: "
        f"{mayor['count']} de {total} ({mayor['percent']} %)."
    )

    if mayor["percent"] >= 50:
        frase += (
            f" Mas de la mitad mueren en el mismo sitio, asi que "
            f"es ahi donde hay que mirar antes de tocar nada."
        )

    return frase
