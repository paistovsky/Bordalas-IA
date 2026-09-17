"""
LA ESCALA: en que orden manda cada cosa.

QUE ES ESTO (18/09/2026)

    La estrategia del dueño, escrita en UN SOLO SITIO para que el
    motor pueda citarla y la pantalla publicarla. Hasta hoy vivia
    repartida entre comentarios, y una regla que no se puede leer
    entera no se puede discutir entera.

    NO ES UN MOTOR. No decide nada por si misma: pone el orden y
    da el vocabulario para que cada decision diga a que peldaño
    responde.

LOS CINCO PELDAÑOS, y el mas bajo manda:

    1  ESTAR EN POSITIVO AL CIERRE
    2  NO DEGRADAR EL XI
    3  MEJORAR EL XI
    4  REVENDER
    5  LA FORMA NO SE PERSIGUE

POR QUE EL 1 ES EL 1

    Si al cierre estamos en negativo, NO PUNTUAMOS. No es una
    multa: es la jornada entera a cero. Todo lo demas vale cero
    si esto falla.

    Y de ahi sale algo que no parece de su peldaño: RENOVAR UNA
    OFERTA NO ES UNA TAREA MENOR. Las ofertas del Computer son el
    plan de emergencia para volver a positivo, y una oferta
    caducada es el plan roto. Se puede estar en negativo hasta
    horas antes del cierre —eso es libertad de maniobra, no
    riesgo— PERO solo mientras el plan siga vivo.

POR QUE EL 2 VA ANTES QUE EL 3

    Ninguna reventa vale un titular. Pero «no degradar» no es
    «no tocar»: si la operacion MEJORA el once, se vende un
    titular — comprando el recambio PRIMERO. Ese orden tiene
    nombre en esta casa: `RECAMBIO_PRIMERO`.

    Vender primero y comprar despues es quedarse sin las dos
    cosas si la compra falla, y la compra puede fallar: la gana
    quien puja mas.

POR QUE EL 5 ES UNA REGLA Y NO UNA PREFERENCIA

    Se alinean LOS ONCE MEJORES por puntos esperados. Si salen
    tres delanteros, 4-3-3. Si salen dos, 4-4-2. Nunca se saca a
    un titular bueno para cumplir una forma.

    Dicho por el dueño: «si no tengo 3 delanteros buenos, no me
    saques a uno bueno y me metas a uno malo para cumplir con el
    4-3-3».

LO QUE ESTE MODULO NO HACE

    No mueve ningun umbral, no enciende ninguna via y no decide
    ninguna operacion. Solo dice el orden.
"""

from __future__ import annotations


# ============================================================
# LOS PELDAÑOS
# ============================================================

POSITIVO_AL_CIERRE = 1

NO_DEGRADAR_EL_XI = 2

MEJORAR_EL_XI = 3

REVENDER = 4

LA_FORMA_NO_SE_PERSIGUE = 5


LA_ESCALA = (
    {
        "peldaño": POSITIVO_AL_CIERRE,
        "clave": "POSITIVO_AL_CIERRE",
        "titulo": "Estar en positivo al cierre",
        "regla": (
            "Si al cierre estamos en negativo no puntuamos. Se "
            "puede estar en negativo hasta horas antes, pero solo "
            "mientras el plan de vuelta siga vivo."
        ),
        "consecuencia": (
            "Renovar una oferta NO es una tarea menor: las "
            "ofertas del Computer son el plan de emergencia, y "
            "una oferta caducada es el plan roto."
        ),
    },
    {
        "peldaño": NO_DEGRADAR_EL_XI,
        "clave": "NO_DEGRADAR_EL_XI",
        "titulo": "No degradar el XI",
        "regla": (
            "Ninguna reventa vale un titular. Si la operacion "
            "MEJORA el once si se vende un titular, comprando el "
            "recambio PRIMERO."
        ),
        "consecuencia": (
            "`RECAMBIO_PRIMERO`: vender antes de comprar es "
            "quedarse sin las dos cosas el dia que la compra la "
            "gane otro."
        ),
    },
    {
        "peldaño": MEJORAR_EL_XI,
        "clave": "MEJORAR_EL_XI",
        "titulo": "Mejorar el XI",
        "regla": (
            "La caja y el margen de deuda son para esto, y se "
            "puja fuerte: por encima de lo que pujan los rivales."
        ),
        "consecuencia": (
            "Pujar por encima del rival SIN un techo atado al "
            "valor del jugador es la forma exacta del caso Ruben "
            "Garcia. El techo va con la regla o la regla no va."
        ),
    },
    {
        "peldaño": REVENDER,
        "clave": "REVENDER",
        "titulo": "Revender",
        "regla": (
            "Con lo que sobre despues del once, y nunca por "
            "debajo del liston propio."
        ),
        "consecuencia": (
            "Por debajo de ese liston el Computer no paga lo "
            "bastante para que el suelo de cobro deje vender: no "
            "seria un viaje flaco, seria un jugador que no se "
            "puede soltar."
        ),
    },
    {
        "peldaño": LA_FORMA_NO_SE_PERSIGUE,
        "clave": "LA_FORMA_NO_SE_PERSIGUE",
        "titulo": "La forma no se persigue",
        "regla": (
            "Se alinean los ONCE MEJORES por puntos esperados. La "
            "formacion es el RESULTADO, no el objetivo."
        ),
        "consecuencia": (
            "Nunca se saca a un titular bueno para cumplir una "
            "forma."
        ),
    },
)


LA_ESCALA_FUENTE = (
    "Decision del dueño, 18/09/2026. Escrita aqui para que viva "
    "en un solo sitio, se publique y cada decision pueda citar a "
    "que peldaño responde."
)


def peldaños() -> tuple:
    """Los numeros, en orden. El mas bajo manda."""

    return tuple(fila["peldaño"] for fila in LA_ESCALA)


def por_clave(clave) -> dict | None:
    """El peldaño que se llama asi, o None."""

    nombre = str(clave or "").upper()

    for fila in LA_ESCALA:
        if fila["clave"] == nombre:
            return dict(fila)

    return None


def manda(una, otra):
    """
    Cual de las dos manda. Devuelve la que va antes, o None si no
    se reconoce alguna.

    Lo que no se reconoce NO gana: una via sin nombre no se cuela
    por delante de la solvencia.
    """

    a = por_clave(una)

    b = por_clave(otra)

    if a is None and b is None:
        return None

    if a is None:
        return b["clave"]

    if b is None:
        return a["clave"]

    return (a if a["peldaño"] <= b["peldaño"] else b)["clave"]


def publicar() -> dict:
    """
    La escala, para el JSON. Forma fija; nunca lanza.

    Se publica ENTERA —regla y consecuencia— porque media regla
    es la que se interpreta mal.
    """

    return {
        "available": True,
        "n": len(LA_ESCALA),
        "fuente": LA_ESCALA_FUENTE,
        "peldaños": [dict(fila) for fila in LA_ESCALA],
    }


def a_que_peldaño_responde(decision) -> dict:
    """
    Traduce una decision del motor al peldaño que la justifica.

    `decision` es el texto de una via o de un motivo. Lo que no
    se reconoce se dice —`SIN PELDAÑO`— en vez de colocarlo a
    ojo: una decision que no sabe a que regla responde es
    exactamente lo que esta escala viene a arreglar.

    Nunca lanza.
    """

    texto = str(decision or "").upper()

    # El orden importa: se mira de arriba abajo, y la solvencia
    # gana a todo lo demas aunque el texto mencione las dos.
    señales = (
        (POSITIVO_AL_CIERRE, (
            "SOLVENC", "DEUDA", "DEFICIT", "RENOV", "CADUC",
            "ACCEPT_NOW", "EMERGENC",
        )),
        (NO_DEGRADAR_EL_XI, (
            "GUARDARRAIL", "TITULAR", "RECAMBIO_PRIMERO",
            "NEEDS_SALE_FIRST",
        )),
        (MEJORAR_EL_XI, ("XI_UPGRADE", "ROSTER_FILL", "FICHAJE")),
        (REVENDER, (
            "COMPUTER_RESALE", "SPECULATION", "REVENDER",
            "CARRIL",
        )),
        (LA_FORMA_NO_SE_PERSIGUE, ("FORMACION", "FORMATION")),
    )

    for numero, palabras in señales:

        if any(palabra in texto for palabra in palabras):

            fila = LA_ESCALA[numero - 1]

            return {
                "peldaño": numero,
                "clave": fila["clave"],
                "titulo": fila["titulo"],
            }

    return {
        "peldaño": None,
        "clave": "SIN_PELDAÑO",
        "titulo": (
            "No se sabe a que regla responde esta decision."
        ),
    }
