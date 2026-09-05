"""
Poner el dinero a trabajar: el bolsillo correcto y la ficha
vacia.

EL INTERRUPTOR ESTA AQUI Y SOLO AQUI

        DEPLOYMENT_ENABLED

    Apagado de serie. Con el apagado, Pepe decide EXACTAMENTE
    igual que el 09/09: todo lo de este fichero se calcula, se
    publica al lado y no manda.

    Para encenderlo, una de las dos:

        variable de entorno   DEPLOYMENT_ENABLED=1
        o poner a True la constante de mas abajo

    Para apagarlo, quitarla. No hay mas sitios que tocar.

POR QUE EXISTE

    Siete noches arreglando como decide Pepe y ninguna toco lo
    que de verdad le separa del lider:

        3.400.000 EUR   parados en caja
        3               fichas vacias (14 de 17)
        8.561.940 EUR   en el bolsillo de FICHAR, sin usar

    Y el dinero en esta liga no sale de comerciar: Pollo lleva
    -27 M en ventas menos compras y su patrimonio sale de tener
    una plantilla grande que se revaloriza. Cada euro parado
    revaloriza cero y cada ficha vacia no puntua nada.

LAS DOS FONTANERIAS QUE SE ARREGLAN

    1. EL BOLSILLO. El `intent` salia de la via que diera MAS
       EUROS, no de que clase de operacion era. Como la via de
       reventa al Computer ganaba en 21 de 22 candidatos, los 22
       salian `SPECULATION` y se comparaban contra los 3,5 M de
       especular MIENTRAS LOS 8,5 M DE FICHAR SEGUIAN INTACTOS.
       Cinco se rechazaron por "supera presupuesto" teniendo el
       dinero al lado.

    2. LA FICHA VACIA. `candidatos_a_salir` es una lista de UN
       elemento: el titular mas flojo de la posicion. No hay
       forma de fichar sin quitarle el sitio a nadie, teniendo
       tres huecos que no puntuan.

LO QUE NO SE TOCA

    Ningun tope, ningun porcentaje, ningun presupuesto. El dinero
    no esta parado porque los limites sean estrechos: esta parado
    porque la fontaneria no llega hasta el.
"""

from __future__ import annotations

import os


# ============================================================
# EL INTERRUPTOR
# ============================================================

DEPLOYMENT_ENABLED = (
    os.getenv("DEPLOYMENT_ENABLED", "").strip().lower()
    in {"1", "true", "si", "sí", "yes"}
)


# ============================================================
# LAS CLASES DE OPERACION
# ============================================================
#
#     No son tres vias de valorar: son dos clases de negocio.
#
#     FICHAR    entra a la plantilla para puntuar. Sale del
#               bolsillo de fichar, y se le mide en puntos.
#     COMERCIAR entra para revenderlo. Sale del bolsillo de
#               especular, y se le mide en euros.
#
#     La via de valoracion que mas euros de puede ser cualquiera;
#     la CLASE la decide para que lo quieres.

SIGNING = "SIGNING"
TRADE = "TRADE"

# Los `intent` que ya entiende `budget_for_intent`. No se inventan
# etiquetas nuevas: se enruta a las que ya existen.
INTENT_BY_CLASS = {
    SIGNING: "XI_UPGRADE",
    TRADE: "SPECULATION",
}


# Las vias que son un fichaje, por su `route`.
SIGNING_ROUTES = frozenset({"XI_UPGRADE", "ROSTER_FILL"})


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def classify_operation(
    as_xi: dict | None,
    as_roster_fill: dict | None,
    as_speculation: dict | None,
    as_computer_resale: dict | None,
) -> dict:
    """
    Que clase de operacion es esto, y de que bolsillo sale.

    LA REGLA

        Si el jugador entra a la plantilla para jugar -mejora el
        once o llena un hueco- es un FICHAJE, aunque su reventa
        diera mas euros. Para lo que lo quieres no lo decide cual
        de las cuentas sale mas gorda.

        Solo cuando ninguna de esas dos vias da valor, la
        operacion es comerciar.

    EL VALOR NO CAMBIA

        Sigue siendo el mayor de todas las vias: si ademas se
        puede revender, el jugador vale al menos eso. Lo que
        cambia es de que bolsillo se paga y con que liston se le
        mide.
    """

    def vale(via):
        return bool(via) and safe_int(via.get("value")) > 0

    fichaje = [
        via
        for via in (as_xi, as_roster_fill)
        if vale(via)
    ]

    comercio = [
        via
        for via in (as_speculation, as_computer_resale)
        if vale(via)
    ]

    todas = fichaje + comercio

    if not todas:
        return {
            "operation_class": None,
            "intent": None,
            "route": None,
            "value": 0,
            "reason": "Ninguna via da valor.",
        }

    # El valor: el mayor de todas. El jugador vale lo que vale.
    mejor = max(todas, key=lambda via: safe_int(via.get("value")))

    if fichaje:
        clase = SIGNING
        elegida = max(fichaje, key=lambda via: safe_int(via.get("value")))
        motivo = (
            "Entra a la plantilla para jugar"
            + (
                " llenando una ficha vacia"
                if elegida.get("route") == "ROSTER_FILL"
                else " mejorando el once"
            )
            + ": es un fichaje y sale del bolsillo de fichar"
            + (
                ", aunque su reventa diera mas euros"
                if mejor is not elegida
                else ""
            )
            + "."
        )

    else:
        clase = TRADE
        elegida = mejor
        motivo = (
            "No entra al once ni llena hueco: se compra para "
            "revender, y sale del bolsillo de especular."
        )

    return {
        "operation_class": clase,
        "intent": INTENT_BY_CLASS[clase],
        "route": elegida.get("route"),
        "value": safe_int(mejor.get("value")),
        "value_route": mejor.get("route"),
        "reason": motivo,
    }


# ============================================================
# LA VIA QUE HOY NO EXISTE: LLENAR UNA FICHA VACIA
# ============================================================
#
#     Cuando hay hueco, el candidato no le quita el sitio a
#     nadie: se le compara contra el CERO de una ficha vacia, que
#     es lo que hoy aporta.
#
#     SIN EL VETO DE "NO MEJORA EL ONCE", porque no esta
#     desplazando a nadie. PERO CON LOS QUE SI TOCAN.
#
#     El 05/09 quedo avisado y hay que tomarselo en serio: de 18
#     fichables, los dos unicos baratos por punto eran SUPLENTES.
#     Una via de ampliacion sin filtro empuja derecha al bucle de
#     las catorce defensas, que ya costo una intervencion a mano
#     del dueño.
#
#     El filtro es lo que corta el bucle.

# Jerarquia minima para ocupar una ficha. Por debajo de
# "Rotacion" el jugador no juega, y una ficha ocupada por alguien
# que no juega es una ficha vacia que ademas cuesta dinero.
MIN_HIERARCHY_VALUE = 40

# Y probabilidad minima de ser titular. Mismo corte que usa el
# resto del sistema para decir "suplente".
MIN_STARTER_PERCENT = 40.0


def roster_fill_veto(
    starter: dict | None,
    availability: dict | None = None,
) -> str | None:
    """
    Por que este candidato NO puede ocupar una ficha libre.

    None significa que puede.
    """

    señal = starter or {}

    # 1. Sin pronostico no se ficha a ciegas. Es la misma regla
    #    que ya aplica la via del once.
    probabilidad = señal.get("probability")

    if probabilidad is None:
        return (
            "Sin pronostico de titularidad no se ocupa una ficha: "
            "a ciegas, llenar el hueco es lo mismo que dejarlo "
            "vacio pagando."
        )

    # 2. Ni a alguien que no va a jugar.
    if float(probabilidad) < MIN_STARTER_PERCENT:
        return (
            f"Solo {float(probabilidad):.0f} % de titularidad. Una "
            f"ficha ocupada por un suplente es una ficha vacia que "
            f"ademas cuesta dinero."
        )

    # 3. Ni a un descarte de su equipo. Es el filtro que corta el
    #    bucle de las catorce defensas: sin el, la via de
    #    ampliacion compra a los baratos, que son justo los que no
    #    juegan.
    jerarquia = señal.get("hierarchy_value")

    if jerarquia is not None and safe_int(jerarquia) < MIN_HIERARCHY_VALUE:
        return (
            f"Jerarquia {señal.get('hierarchy_label') or jerarquia} "
            f"en su equipo: por debajo de Rotacion no se ocupa una "
            f"ficha. Es el filtro que evita repetir el bucle de las "
            f"catorce defensas."
        )

    # 4. Y no se llena un hueco con alguien que no puede jugar.
    estado = (availability or señal.get("availability") or {})

    if estado and estado.get("can_play") is False:
        etiqueta = estado.get("label") or "sin estado"

        return (
            f"No esta disponible ({etiqueta}): una ficha libre no "
            f"se ocupa con quien no puede jugar."
        )

    return None
