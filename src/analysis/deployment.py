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

# ENCENDIDO EL 13/09/2026, POR ORDEN EXPRESA DEL DUEÑO
#
#     "Activa lo que haga falta."
#
#     Estuvo apagado desde el 10/09 esperando una prueba: que se
#     pudiera demostrar que Pepe deshace una posicion antes de
#     dejarle endeudarse para fichar. Esa prueba existe desde el
#     12/09 -`test_venta_ejecutable_v1` recorre los siete tramos
#     hasta el `PUT /offers/{id}` con cuerpo- y ademas el saldo
#     volvio a positivo: +1.725.383 EUR en la foto del 06/09.
#
# COMO SE APAGA, EN UNA LINEA
#
#     Por entorno, sin tocar codigo:
#
#         DEPLOYMENT_ENABLED=0
#
#     En PowerShell, para la sesion en curso:
#
#         $env:DEPLOYMENT_ENABLED = "0"
#
#     Y para apagarlo de forma permanente, cambiar el "1" de
#     `DEPLOYMENT_DEFAULT` por un "0". Al apagarlo vuelve
#     exactamente lo de antes: el `intent` se elige por euros, un
#     fichaje se mide contra el bolsillo de especular y la via de
#     ficha vacia no compite.

DEPLOYMENT_DEFAULT = "1"

DEPLOYMENT_ENABLED = (
    os.getenv("DEPLOYMENT_ENABLED", DEPLOYMENT_DEFAULT)
    .strip()
    .lower()
    not in {"0", "false", "no", "off", ""}
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

        # LO QUE VALE POR TODAS LAS VIAS. Informativo: el jugador
        # vale al menos esto, y por eso se sigue publicando.
        "value": safe_int(mejor.get("value")),
        "value_route": mejor.get("route"),

        # LO QUE VALE POR LA VIA CON LA QUE SE LE VA A PAGAR
        # (13/09/2026)
        #
        #     Esto es lo que decide, y no lo de arriba.
        #
        #     Lo destapo `test_acquisition_wiring_v1` en cuanto se
        #     encendio el interruptor: un jugador de 9.000.000 que
        #     suma 6 puntos salia PUJAR a 9.000.001. Su valor como
        #     fichaje eran 2.068.000; los 9.092.475 con los que se
        #     justificaba la puja venian de la via de REVENTA.
        #
        #     O sea: se pagaba dinero de fichar amparandose en un
        #     numero de comerciar, y encima sin el liston de
        #     rendimiento que esa via tiene que pasar. Es la misma
        #     mezcla que ya costo dos noches: el valor de una via
        #     medido con la vara de otra.
        #
        #     La regla: el bolsillo, el liston Y el valor salen
        #     todos de la misma via.
        "decision_value": safe_int(elegida.get("value")),

        "reason": motivo,
    }


# ============================================================
# EL ORDEN DE PRIORIDAD (13/09/2026)
# ============================================================
#
#     LO QUE HACE POLLO, MEDIDO
#
#         Siete compras en la ventana observada por 21.198.020
#         EUR, repartidas por todas las bandas de precio -de
#         277.000 a 6.450.000- y con la prima MEDIANA pegada a
#         cero. No paga de mas: simplemente compra.
#
#         Tiene 22 fichas. Pepe tiene 14 y ocho huecos.
#
#     El dinero parado no se revaloriza; los jugadores si. Cada
#     ficha vacia es capital al 0 %.
#
#     Asi que cuando el bolsillo de fichar no llegue para todo,
#     el orden es este, y no el del valor esperado:
#
#         0  llena ficha Y mejora el once
#         1  llena ficha Y se revaloriza
#         2  cualquier otro fichaje
#         3  especulacion pura
#
#     Repartido en varias operaciones, que ademas es lo que
#     reparte el riesgo de concentracion. El ciclo ejecuta una
#     accion por vuelta, asi que ordenar ya reparte: no hace
#     falta ningun mecanismo nuevo para eso.

FILL_AND_XI = 0
FILL_AND_RISING = 1
OTHER_SIGNING = 2
PURE_SPECULATION = 3

PRIORITY_LABEL = {
    FILL_AND_XI: "Llena ficha y mejora el once",
    FILL_AND_RISING: "Llena ficha y se revaloriza",
    OTHER_SIGNING: "Fichaje",
    PURE_SPECULATION: "Especulacion",
}


def signing_priority(
    operation: dict | None,
    *,
    as_xi: dict | None = None,
    price_increment=None,
) -> dict:
    """
    En que escalon entra esta operacion.

    `operation` es lo que devuelve `classify_operation`.
    """

    clase = (operation or {}).get("operation_class")
    via = (operation or {}).get("route")

    if clase != SIGNING:
        escalon = PURE_SPECULATION

    elif via == "ROSTER_FILL":

        if as_xi and safe_int(as_xi.get("value")) > 0:
            escalon = FILL_AND_XI

        elif safe_int(price_increment) > 0:
            escalon = FILL_AND_RISING

        else:
            escalon = OTHER_SIGNING

    else:
        escalon = OTHER_SIGNING

    return {
        "priority": escalon,
        "priority_label": PRIORITY_LABEL[escalon],
        "priority_reason": (
            "Con ocho fichas vacias, llenar una vale mas que una "
            "especulacion: el dinero parado no se revaloriza y una "
            "ficha vacia es capital al 0 %."
            if escalon < PURE_SPECULATION
            else "No entra a la plantilla: va detras de los fichajes."
        ),
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
