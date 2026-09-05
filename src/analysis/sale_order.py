"""
El orden de venta: a quien le toca salir, y en que orden.

POR QUE EXISTE (10/09/2026)

    Hoy nadie decide esto. Hay tres motores que hablan de vender
    y ninguno manda:

        `sales_analyzer`        puntua a quien vender
        `sale_intent`           propone, y no lo lee nadie: se
                                imprime en el terminal del ciclo
                                y no llega al dashboard
        `offer_decision_engine` etiqueta las ofertas que entran,
                                y contesta HOLD a las doce

    Medido en la foto de produccion del 05/09/2026 a las 14:03:

        saldo                       -421.792 EUR
        prioridad declarada         "recuperar solvencia"
        ofertas sobre la mesa       12, por 45.746.500 EUR
        ofertas cobrables ahora     0
        planes de solvencia         3, los tres calculados y
                                    ninguno ejecutado

    El plan A del propio motor de solvencia es vender a Lucas
    Cepeda por 471.200 -no juega, no toca el once, deja el saldo
    en +49.408- y el motor de ofertas contesta HOLD_OFFER a esa
    misma oferta. Dos motores, respuestas contrarias, y nadie
    arbitra.

QUE HACE ESTE MODULO

    Una COLA. Quien sale primero, quien despues, y por que, con
    el motivo escrito para que el dueño pueda leerlo ANTES de que
    pase.

    Se puede parar en cualquier punto: la cola esta construida de
    forma que vender a los `k` primeros, para cualquier `k`, deja
    todas las posiciones por encima de su suelo. No es una lista
    de sugerencias sueltas: es un orden que aguanta prefijos.

ESTE MODULO NO VENDE

    Igual que `sale_intent`, y por el mismo motivo, que sigue
    siendo bueno:

        "Vender mal no es como comprar mal. Una compra mala cuesta
        dinero y se corrige; una venta mala te deja SIN el
        jugador, y en un fantasy no se recupera: se lo lleva
        otro."

    No importa ningun executor, no escribe en disco y no devuelve
    nada que un executor sepa ejecutar.

EL ORDEN SALE DEL DUEÑO, NO DE UNA FORMULA

    Textualmente:

        1. "Primero quien no juega: un suplente no puntua, solo
            ocupa ficha y dinero."
        2. "Despues, peor relacion coste por punto."
        3. "Y ojo con el momento: el que viene subiendo es el que
            conviene retener, y el que cae se vende antes de que
            caiga mas."

    Los tres son escalones, no sumandos. Un titular caro por
    punto no sale antes que un suplente: sale despues, aunque su
    numero sea peor. Mezclarlos en una puntuacion unica haria
    justo lo contrario de lo que dice la frase.

    El momento no crea escalon: ordena DENTRO de cada uno. Con
    r=+0,90 de autocorrelacion diaria medida el 07/09, el que
    baja hoy baja mañana, y el que sube conviene retenerlo.

LO QUE MANDA POR ENCIMA

    Los intocables (`sale_intent.untouchable_reason`), el suelo
    por posicion (`position_guardrail.validate_sale_set`) y el
    tope de concentracion del 10/09. Ninguno de los tres se
    reimplementa aqui: se llaman.
"""

from __future__ import annotations

from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)

from src.analysis.sale_intent import untouchable_reason


# ============================================================
# LOS ESCALONES
# ============================================================

NO_JUEGA = "NO_JUEGA"
CARO_POR_PUNTO = "CARO_POR_PUNTO"

TIER_LABEL = {
    NO_JUEGA: "No juega",
    CARO_POR_PUNTO: "Caro por punto",
}

TIER_ORDER = {NO_JUEGA: 0, CARO_POR_PUNTO: 1}


# Por debajo de esto no es titular. Es el mismo corte que usa el
# resto de la casa para decir "suplente".
BENCH_PERCENT = 40.0

# Y el mismo escalon minimo que usa la via de ficha vacia del
# 10/09 para decidir si alguien merece ocupar una ficha.
ROTATION_HIERARCHY = 40


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _plays(jugador: dict) -> bool:
    """
    ¿Este jugador juega?

    Titular puesto en el once, o pronostico por encima del corte
    de suplente. Basta con una de las dos: un suplente al 90 %
    esta a punto de entrar, y un titular sin pronostico esta
    puesto por alguien que le vio jugar.
    """

    if jugador.get("in_lineup") or jugador.get("is_starter"):
        return True

    probabilidad = jugador.get("starter_probability")

    if probabilidad is not None:
        return float(probabilidad) >= BENCH_PERCENT

    # Sin pronostico manda el escalon. De Rotacion para arriba se
    # asume que juega: es lo prudente cuando la duda te deja SIN
    # el jugador.
    return safe_int(jugador.get("hierarchy_value")) >= ROTATION_HIERARCHY


def euros_per_point(jugador: dict):
    """
    Lo que ha costado cada punto suyo.

    `None` cuando todavia no ha puntuado: no es cero ni infinito,
    es que no se sabe. Se ordena aparte y se dice.
    """

    precio = safe_int(jugador.get("price"))
    puntos = safe_int(jugador.get("points"))

    if precio <= 0 or puntos <= 0:
        return None

    return int(round(precio / puntos))


def momentum(jugador: dict) -> dict:
    """
    Hacia donde va su precio. Con r=+0,90, hoy predice mañana.
    """

    delta = safe_int(jugador.get("price_increment"))

    # El separador de miles se formatea APARTE. Hacer
    # `.replace(",", ".")` sobre la frase entera se comia las
    # comas de la prosa: "si hay que vender. antes que despues".
    importe = f"{abs(delta):,}".replace(",", ".")

    if delta > 0:
        return {
            "direction": "SUBE",
            "delta": delta,
            "reason": (
                f"Sube {importe} EUR al dia: conviene retenerlo, "
                f"no soltarlo."
            ),
        }

    if delta < 0:
        return {
            "direction": "CAE",
            "delta": delta,
            "reason": (
                f"Cae {importe} EUR al dia: si hay que vender, "
                f"antes que despues."
            ),
        }

    return {
        "direction": "QUIETO",
        "delta": 0,
        "reason": "Su precio no se mueve.",
    }


def _offer_for(ofertas, jugador: dict) -> dict | None:
    """
    La oferta viva por este jugador, si la hay.

    Es la diferencia entre caja HOY y caja CUANDO ALGUIEN COMPRE.
    """

    nombre = str(jugador.get("name") or "").strip().lower()
    player_id = safe_int(jugador.get("id"))

    for oferta in (ofertas or []):

        if not isinstance(oferta, dict):
            continue

        if player_id and safe_int(oferta.get("player_id")) == player_id:
            return oferta

        nombres = [
            str(n).strip().lower()
            for n in (oferta.get("players") or [])
        ]

        if nombre and nombre in nombres:
            return oferta

    return None


def _row(jugador: dict, ofertas) -> dict:
    """
    Un candidato a salir, con todo lo que hace falta para
    ordenarlo y para explicarlo.
    """

    juega = _plays(jugador)
    coste = euros_per_point(jugador)
    ritmo = momentum(jugador)

    tier = CARO_POR_PUNTO if juega else NO_JUEGA

    oferta = _offer_for(ofertas, jugador)

    if tier == NO_JUEGA:
        probabilidad = jugador.get("starter_probability")

        motivo = (
            "No juega: "
            + (
                f"{float(probabilidad):.0f} % de titularidad"
                if probabilidad is not None
                else f"{jugador.get('hierarchy') or 'sin escalon'}"
            )
            + " y fuera del once. Una ficha ocupada por quien no "
            "puntua cuesta dinero dos veces."
        )

    elif coste is None:
        motivo = (
            "Juega, pero todavia no ha puntuado: no hay coste por "
            "punto que mirar."
        )

    else:
        motivo = (
            f"Cada punto suyo ha costado "
            f"{format(coste, ',').replace(',', '.')} EUR."
        )

    return {
        "id": safe_int(jugador.get("id")),
        "name": jugador.get("name"),
        "position": safe_int(jugador.get("position")),
        "price": safe_int(jugador.get("price")),
        "points": safe_int(jugador.get("points")),

        "hierarchy": jugador.get("hierarchy"),
        "hierarchy_value": jugador.get("hierarchy_value"),
        "starter_probability": jugador.get("starter_probability"),
        "in_lineup": bool(
            jugador.get("in_lineup") or jugador.get("is_starter")
        ),

        "plays": juega,
        "euros_per_point": coste,

        "momentum": ritmo["direction"],
        "price_increment": ritmo["delta"],

        "tier": tier,
        "tier_label": TIER_LABEL[tier],

        # Lo que entra en caja, y CUANDO. La diferencia importa:
        # una oferta sobre la mesa es caja en este ciclo; sin
        # oferta hay que publicarlo y esperar a que alguien lo
        # compre, que no es lo mismo ni tarda lo mismo.
        "offer_amount": safe_int(
            (oferta or {}).get("amount")
        ) or None,

        "cash_kind": "OFERTA_VIVA" if oferta else "A_MERCADO",

        "cash_now": (
            safe_int((oferta or {}).get("amount"))
            if oferta
            else 0
        ),

        "reason": motivo + " " + ritmo["reason"],
    }


def _sort_key(fila: dict) -> tuple:
    """
    El orden del dueño, en tres escalones.

    Dentro de cada escalon: primero el mas caro por punto -o el
    que no ha puntuado, que es el caso extremo del mismo
    problema- y, a igualdad, el que mas cae.
    """

    coste = fila["euros_per_point"]

    return (
        TIER_ORDER[fila["tier"]],

        # Sin puntos va primero dentro de su escalon: es dinero
        # parado que no ha devuelto nada todavia.
        0 if coste is None else 1,

        -(coste or 0),

        # Y el que cae, antes que el que sube.
        fila["price_increment"],

        -fila["price"],
    )


def build_sale_order(
    roster,
    *,
    lineup_ids=None,
    offers=None,
    concentration=None,
) -> dict:
    """
    La cola de venta. Nunca lanza.

    `roster` son los jugadores enriquecidos -precio, puntos,
    escalon, pronostico-. `offers` las ofertas vivas, para
    distinguir la caja de hoy de la caja de cuando alguien compre.
    """

    try:
        jugadores = [
            j for j in (roster or []) if isinstance(j, dict)
        ]

        if not jugadores:
            return {
                "available": False,
                "reason": (
                    "Sin plantilla que ordenar: no hay a quien "
                    "vender."
                ),
                "queue": [],
                "excluded": [],
                "blocked": [],
            }

        # EL PORTERO SE SALVABA POR ACCIDENTE (10/09/2026)
        #
        #     `untouchable_reason` protege al "portero titular"
        #     mirando `in_lineup`, y el roster del dashboard trae
        #     ese dato con otro nombre: `is_starter`. Con la
        #     plantilla tal cual, Dituro NO salia como intocable;
        #     solo lo salvaba el suelo posicional, que es
        #     exactamente el accidente contra el que avisa el
        #     docstring de `sale_intent`:
        #
        #         "hoy Yamal solo esta a salvo por accidente: el
        #          guardarrail posicional bloquea la venta porque
        #          hay exactamente dos delanteros."
        #
        #     No se toca la regla: se le da el dato con el nombre
        #     que espera.
        titulares = {safe_int(pid) for pid in (lineup_ids or [])}

        jugadores = [
            {
                **j,
                "in_lineup": bool(
                    j.get("in_lineup")
                    or j.get("is_starter")
                    or safe_int(j.get("id")) in titulares
                ),
            }
            for j in jugadores
        ]

        guardarrail = build_position_guardrail(
            jugadores,
            lineup_ids=lineup_ids,
        )

        # ----------------------------------------------------
        # 1. QUIEN NI SE PROPONE
        # ----------------------------------------------------
        #
        # No es que esten al final de la cola: es que no entran.
        # Y se dice quienes son y por que, porque un tope que
        # recorta en silencio es el problema que este repo lleva
        # una semana arreglando.

        candidatos = []
        excluidos = []

        for jugador in jugadores:

            motivo = untouchable_reason(jugador)

            if motivo:
                excluidos.append(
                    {
                        "id": safe_int(jugador.get("id")),
                        "name": jugador.get("name"),
                        "price": safe_int(jugador.get("price")),
                        "reason": motivo,
                    }
                )
                continue

            candidatos.append(_row(jugador, offers))

        # ----------------------------------------------------
        # 2. EL ORDEN
        # ----------------------------------------------------

        candidatos.sort(key=_sort_key)

        # ----------------------------------------------------
        # 3. LA COLA AGUANTA PREFIJOS
        # ----------------------------------------------------
        #
        # Vender a los `k` primeros, para CUALQUIER k, tiene que
        # dejar todas las posiciones por encima de su suelo. Si
        # meter al siguiente rompiera un suelo, no se cuela mas
        # abajo: se aparta con el motivo. Bajarlo de puesto seria
        # mentir sobre el orden.

        cola = []
        vendiendo = []
        bloqueados = []

        for fila in candidatos:

            comprobacion = validate_sale_set(
                guardarrail,
                vendiendo + [fila["id"]],
            )

            if not comprobacion.get("ok"):
                bloqueados.append(
                    {
                        **fila,
                        "blocked_reason": comprobacion.get("reason"),
                    }
                )
                continue

            vendiendo.append(fila["id"])

            cola.append({**fila, "order": len(cola) + 1})

        # ----------------------------------------------------
        # 4. CUANTA CAJA, Y CUANDO
        # ----------------------------------------------------

        con_oferta = [f for f in cola if f["cash_kind"] == "OFERTA_VIVA"]

        # SOLO SE EJECUTA UNA ACCION POR CICLO
        #
        #     Asi que "caja en un ciclo" no es la suma de todas
        #     las ofertas: es la PRIMERA de la cola que tenga una
        #     oferta viva. Sumarlas seria prometer en media hora
        #     lo que tardaria cinco ciclos.
        caja_ciclo = con_oferta[0]["cash_now"] if con_oferta else 0

        caja_mesa = sum(f["cash_now"] for f in cola)
        caja_mercado = sum(f["price"] for f in cola)

        return {
            "available": True,
            "reason": None,

            "queue": cola,
            "excluded": excluidos,
            "blocked": bloqueados,

            "queue_size": len(cola),

            # Lo que se cobra EN ESTE CICLO: la primera venta de
            # la cola que tenga oferta viva. Es el numero que hace
            # falta para saber si una deuda es cubrible, y no
            # ninguno de los dos de abajo.
            "cash_one_cycle": caja_ciclo,
            "cash_one_cycle_player": (
                con_oferta[0]["name"] if con_oferta else None
            ),

            # Lo que hay sobre la mesa en ofertas vivas por gente
            # de la cola. Tarda tantos ciclos como ventas.
            "cash_on_the_table": caja_mesa,
            "offers_on_the_table": len(con_oferta),

            # Y lo que valen todos a precio de mercado, que exige
            # publicarlos y que alguien los compre.
            "cash_to_market": caja_mercado,

            "position_check": validate_sale_set(guardarrail, vendiendo),

            # El tope de concentracion del 10/09 viaja al lado
            # para que la pantalla pueda decir si vender a alguien
            # concentra todavia mas la plantilla.
            "concentration": concentration or None,

            "first": cola[0] if cola else None,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo ordenar la venta: "
                f"{type(error).__name__}: {error}"
            ),
            "queue": [],
            "excluded": [],
            "blocked": [],
        }
