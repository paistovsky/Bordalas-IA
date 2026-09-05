"""
Cada apuesta con la confianza de lo que de verdad esta apostando.

EL ERROR DE CATEGORIA QUE ESTO CIERRA

    `speculation_value` multiplica su resultado por `confidence`,
    y esa confianza mide lo seguros que estamos de los PUNTOS del
    jugador: si tiene historico en LaLiga y si hay pronostico de
    titularidad.

    Para una apuesta de PRECIO eso no viene a cuento. Da igual
    cuantos puntos vaya a hacer Bardeli: lo que importa es si su
    precio sigue subiendo, que es justo lo que si esta medido.

    Medido el 08/09: Bardeli, a +4,62 %/dia, proyecta +138.628 EUR
    y se queda en cero porque se multiplica por 0,4125.

Y EL REMATE

        speculation_value      lleva confianza (la equivocada)
        computer_resale_value  no lleva NINGUNA

    La via que MIRA al jugador va penalizada; la que NO lo mira va
    limpia. Por eso ganaba en 21 de 22 candidatos, y por eso todo
    salia plano: esa via es igual para todos por construccion.

LO QUE SE HACE, QUE NO ES QUITAR LA PENALIZACION

    Darle a cada via la confianza de su propia apuesta:

        xi_upgrade_value       apuesta a que puntua
                               -> la de los puntos, sin tocar
        speculation_value      apuesta a que el precio sube
                               -> la de la RACHA
        computer_resale_value  apuesta a que el Computer recompra
                               -> la del PREMIUM MEDIDO

FASE OBSERVADOR

    Esto no decide nada. Se calcula la valoracion con el esquema
    nuevo AL LADO de la de hoy, y el motor sigue con la vieja.
"""

from __future__ import annotations


# ============================================================
# LA CONFIANZA DE LA RACHA
# ============================================================
#
#     NO ES UN NUMERO INVENTADO: ES LA CONTINUACION MEDIDA.
#
#     Del estudio del 07/09 sobre 554 jugadores y seis dias de
#     historial de precios, la probabilidad de que el movimiento
#     siga al dia siguiente:
#
#         se movio ayer, sin racha previa   85,1 %   (n=846)
#         1 dia de racha                    92,0 %   (n=264)
#         2 dias de racha                   94,1 %   (n=237)
#         3 dias o mas                      73,8 %   (n=351)
#
#     La confianza de una apuesta de precio ES esa probabilidad.
#     No hay que inventarse una forma: ya esta medida.
#
#     Y OJO, PORQUE NO ES MONOTONA. La intuicion dice "cuantos
#     mas dias de racha, mas fiable", y el encargo lo daba por
#     hecho. Los datos dicen que no: la continuacion sube hasta
#     el segundo dia y CAE al tercero, del 94 % al 74 %.
#
#     Tiene sentido -una rampa que lleva tres dias esta mas cerca
#     de agotarse que una de uno- y es la misma medicion que
#     sostiene el aviso de "racha sin gasolina" del 08/09. Darle
#     mas confianza a una racha larga habria ido contra nuestros
#     propios numeros.
STREAK_CONTINUATION = (
    # (dias minimos, probabilidad medida, muestra)
    (3, 0.738, 351),
    (2, 0.941, 237),
    (1, 0.920, 264),
    (0, 0.851, 846),
)

# Sin racha conocida se usa la base: "se movio ayer". Es lo unico
# que se sabe, y es un dato medido, no un relleno.
NO_STREAK_CONFIDENCE = 0.851


# ============================================================
# CUANTO SUMA QUE LO CONFIRMEN VARIAS FUENTES
# ============================================================
#
#     Poco, y hay que decir por que.
#
#     El 06/09 se midio que las tres fuentes de precio NO son tres
#     opiniones: son dos medidas y una repetida. Las tres copian
#     el mismo numero de Biwenger, y sobre 288 jugadores no hubo
#     NI UNO en el que discreparan de direccion.
#
#     Asi que "confirmado por tres fuentes" no dice que el
#     movimiento sea mas real: dice que lo hemos LEIDO bien. Es
#     confianza en la lectura -contra un fallo de parseo o de
#     emparejamiento-, no en el mercado.
#
#     Por eso suma poco y con techo. Tratarlo como corroboracion
#     seria contar tres veces el mismo dato, que es exactamente
#     lo que el estudio dijo que no hay que hacer.
READING_BONUS_PER_EXTRA_SOURCE = 0.02
MAX_READING_BONUS = 0.04


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def streak_confidence(trend_days=None, sources=None) -> tuple[float, str]:
    """
    Lo fiable que es una racha de precio, y por que.

    Devuelve `(confianza, explicacion)`. La explicacion viaja
    siempre: una confianza sin origen no se puede discutir.
    """

    dias = abs(safe_int(trend_days))

    probabilidad = NO_STREAK_CONFIDENCE
    muestra = 846
    tramo = "sin racha previa"

    for minimo, valor, n in STREAK_CONTINUATION:

        if dias >= minimo and minimo > 0:
            probabilidad = valor
            muestra = n
            tramo = (
                f"{minimo} dias o mas" if minimo == 3 else f"{minimo} dia(s)"
            )
            break

    # El bono de lectura: pequeño y con techo. Ver arriba.
    fuentes = safe_int(sources)

    bono = min(
        max(fuentes - 1, 0) * READING_BONUS_PER_EXTRA_SOURCE,
        MAX_READING_BONUS,
    )

    confianza = min(round(probabilidad + bono, 4), 1.0)

    return (
        confianza,
        (
            f"Racha de {dias} dia(s) ({tramo}): el movimiento "
            f"continuo el {probabilidad * 100:.1f} % de las veces "
            f"sobre {muestra} casos medidos el 07/09"
            + (
                f", +{bono:.2f} porque lo confirman {fuentes} "
                f"fuentes (confianza en la LECTURA, no en el "
                f"mercado: las tres copian el mismo numero)"
                if bono
                else ""
            )
            + "."
        ),
    )


# ============================================================
# LA CONFIANZA DEL PREMIUM DEL COMPUTER
# ============================================================
#
#     Esta via apuesta a que el Computer recompra por encima del
#     mercado. Y eso NO siempre pasa: sobre la foto del 04/09,
#     `positive_ratio = 0,745`, o sea 76 de 102 ventas con precio.
#
#     Falla una de cada cuatro veces, y hasta hoy no llevaba
#     descuento ninguno. De ahi que ganase siempre.
#
#     La confianza es ese ratio medido, encogido hacia la moneda
#     al aire cuando hay pocas muestras: con 12 -el minimo que
#     exige el propio medidor- el numero es fragil y no puede
#     valer lo mismo que con 102.

# Hacia donde se encoge cuando no hay muestra: no saber nada es
# una moneda al aire.
PREMIUM_PRIOR = 0.5

# Con esta muestra, el ratio medido y el prior pesan lo mismo.
# Es `min_samples` del propio medidor: por debajo de ahi ni
# siquiera publica una prima.
PREMIUM_SHRINK_SAMPLES = 12


def premium_confidence(premium_block: dict | None) -> tuple[float | None, str]:
    """
    Lo fiable que es la prima del Computer, con su muestra.

    Devuelve `(confianza, explicacion)`. Sin medida devuelve
    `None`: de un hueco no sale una compra, y esa regla ya la
    aplica `computer_resale_value`.
    """

    bloque = premium_block or {}

    if not bloque.get("available"):
        return (
            None,
            "No hay medida de lo que paga el Computer.",
        )

    ratio = safe_float(bloque.get("positive_ratio"))

    if ratio is None:
        return (
            None,
            (
                "La prima esta medida pero no se sabe cuantas veces "
                "acierta: sin `positive_ratio` no hay confianza que "
                "dar."
            ),
        )

    muestra = safe_int(bloque.get("priced"))

    if muestra <= 0:
        return (
            None,
            "La medida de la prima no dice sobre cuantas ventas.",
        )

    peso = muestra / (muestra + PREMIUM_SHRINK_SAMPLES)

    confianza = round(
        ratio * peso + PREMIUM_PRIOR * (1 - peso),
        4,
    )

    aciertos = int(round(ratio * muestra))

    return (
        confianza,
        (
            f"El Computer pago por encima del mercado en "
            f"{aciertos} de {muestra} ventas ({ratio * 100:.1f} %). "
            f"Encogido hacia {PREMIUM_PRIOR} por el tamaño de la "
            f"muestra queda en {confianza:.3f}: esta via falla "
            f"aproximadamente una de cada "
            f"{max(round(1 / max(1 - ratio, 0.01)), 2)}."
        ),
    )


# ============================================================
# DONDE SE APLICA LA CONFIANZA: A LA GANANCIA, NO AL CAPITAL
# ============================================================
#
#     Al calcular la sombra salio que TODAS las vias caian a
#     cero, y el motivo no era la confianza sino donde se
#     multiplica.
#
#     Hoy, `speculation_value` hace:
#
#         maximo = (objetivo - ganancia x margen) x confianza
#
#     O sea que multiplica el PRECIO ENTERO que estariamos
#     dispuestos a pagar. Con la via del Computer, cuya ventaja
#     es del 1,76 %, una confianza de 0,72 deja el maximo en
#     1.202.010 EUR sobre un precio de 1.650.000: por debajo del
#     precio, luego MARGEN_INSUFICIENTE, luego cero.
#
#     Cualquier confianza por debajo de 1 anula la via. No es que
#     el numero sea severo: es que se aplica sobre la cosa
#     equivocada.
#
#     EL PRINCIPAL NO ESTA EN RIESGO. Si la apuesta falla, sigues
#     teniendo un jugador que vale aproximadamente el precio de
#     mercado; no se evapora el dinero. Lo que es incierto es la
#     GANANCIA, y es lo unico que hay que descontar:
#
#         maximo = precio + ganancia x confianza x (1 - margen)
#
#     Con Bardeli: la via del Computer pasa de 0 a 1.665.660 y la
#     de tendencia a 1.747.837. Y ahi la tendencia por fin gana,
#     que era justo lo que este arreglo buscaba.
#
#     ESTO NO SE TOCA EN EL MOTOR VIVO. Se usa solo para la
#     sombra: cambiar la semantica de `speculation_value` mueve
#     dinero y lo decide el dueño.


def value_with_confidence_on_gain(
    price,
    expected_gain,
    confidence,
    margin: float = 0.25,
) -> int:
    """
    Lo maximo que se pagaria descontando la GANANCIA por su
    confianza, no el capital.

    Devuelve 0 cuando no queda nada por encima del precio: sin
    margen no hay operacion.
    """

    base = safe_int(price)
    ganancia = safe_int(expected_gain)

    if base <= 0 or ganancia <= 0:
        return 0

    seguridad = max(min(safe_float(confidence, 0.0) or 0.0, 1.0), 0.0)

    esperada = ganancia * seguridad

    maximo = int(base + esperada * (1.0 - margin))

    return maximo if maximo > base else 0

