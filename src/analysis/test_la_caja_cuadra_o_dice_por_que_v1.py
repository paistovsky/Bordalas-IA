"""
Si la caja no cuadra, se dice QUE evento la descuadra.

EL CASO QUE LO DESTAPO

    18/09/2026. La caja reconstruida se separo del saldo real:

        reconstruida  4.744.815
        real          4.324.615
        diferencia      420.200

    Y la pantalla publicaba eso: 420.200. El numero y nada mas.

    Con el numero solo no se puede hacer nada. No dice si sobra
    un cobro o falta un pago, ni de que dia, ni de quien, ni de
    que tipo. Doctrina 48: una foto dice que algo esta mal, nunca
    por que.

    Buscado a mano, estaba en un minuto: una venta al Computer de
    Lunin -jugador 15289- por 420.200 EUR, ese mismo 18/09 a las
    07:03. Cuadraba al euro. Lo que se encuentra a mano en un
    minuto lo encuentra el programa.

LA AVERIA DE FONDO

    La reja de duplicados de `reconstruir` es la clave

        (tipo, FECHA, jugador, de, a, importe)

    y lleva la fecha dentro. Biwenger reemite la misma operacion
    minutos despues con otro `event_id` y otro `date`: la copia
    entra como un hecho nuevo y el dinero se cuenta dos veces.

    Ya habia cinco grupos asi en el tablon, todos de rivales,
    separados entre 2m34s y 4m45s. Nadie los vio porque los
    saldos de los rivales estan ocultos y no hay contra que
    comprobarlos. El 18/09 le toco por primera vez a una venta
    NUESTRA, que es la unica caja comprobable.

QUE SE COMPRUEBA AQUI

    1. Con descuadre se publica la diferencia Y el tipo de
       evento sospechoso, y el motivo lo dice con palabras.
    2. El sospechoso es el evento CONCRETO: tipo, jugador e
       importe, y si es nuestro o de un rival.
    3. Se detecta la reemision con otra fecha y se dice cuanto se
       cuenta de mas.
    4. La racha diaria de dos dias distintos NO se marca como
       copia: son dos cobros de verdad.
    5. Cuando cuadra no se inventan sospechosos.

LA GUARDIA MUERDE CON LA LISTA DE EVENTOS VACIA

    Es la trampa de este test concreto. Sin eventos no hay nada
    que senalar, `suspects` sale vacio y las comprobaciones de
    arriba pasarian por vacuidad.

    Asi que lo primero es comprobar que el banco de pruebas trae
    eventos, y que con la lista vacia el buscador no encuentra
    nada: con el tablon vacio esta guardia FALLA, no pasa.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. NO se lee `data/rival_intelligence/`
    ni ningun otro estado de produccion, no se sale a la red y no
    se mira el reloj: las fechas son marcas de tiempo escritas a
    mano.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.caja_de_la_liga import (  # noqa: E402
    VENTANA_REEMISION,
    cuadra,
    sospechosos,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO DE PRUEBAS
# ================================================================

NOSOTROS = 14175949
RIVAL = 14156489

# 18/09/2026 07:03:10 UTC, la hora del evento real.
VENTA_LUNIN = 1_789_707_790

# 04/09/2026 16:29:16 y 16:34:01 UTC: la reemision real, a 4m45s.
REEMISION_1 = 1_788_539_356
REEMISION_2 = 1_788_539_641

# Dos rachas diarias, con un dia entero por medio.
RACHA_LUNES = 1_788_400_000
RACHA_MARTES = RACHA_LUNES + 86_400


def transfer(date, player, de, importe, event_id):
    """Venta al Computer: `transfer` con `from` y sin `to`."""

    return {
        "event_id": event_id,
        "date": date,
        "type": "transfer",
        "content": [
            {
                "player": player,
                "from": {"id": de, "name": "manager"},
                "amount": importe,
            }
        ],
    }


def racha(date, quien, event_id):

    return {
        "event_id": event_id,
        "date": date,
        "type": "bonus",
        "content": [
            {
                "user": {"id": quien, "name": "manager"},
                "amount": 250_000,
                "reason": "streak",
            }
        ],
    }


TABLON = [
    # La venta de Lunin: nuestra, y por el importe del descuadre.
    transfer(VENTA_LUNIN, 15289, NOSOTROS, 420_200, "a1"),

    # Una venta de un rival, reemitida a los 4m45s con otro id.
    transfer(REEMISION_1, 31069, RIVAL, 2_464_100, "b1"),
    transfer(REEMISION_2, 31069, RIVAL, 2_464_100, "b2"),

    # Dos rachas diarias iguales, con un dia por medio. No son
    # copias: son dos cobros.
    racha(RACHA_LUNES, NOSOTROS, "c1"),
    racha(RACHA_MARTES, NOSOTROS, "c2"),
]


RECONSTRUIDA = 4_744_815
REAL = 4_324_615
DIFERENCIA = 420_200


# ================================================================
# 0. EL BANCO DE PRUEBAS SIRVE
# ================================================================

print()
print("0. La lista de eventos no llega vacia")

check(
    "el tablon de la prueba trae eventos",
    len(TABLON) > 0,
    f"(eventos={len(TABLON)})",
)

check(
    "con la lista VACIA no se encuentra ningun sospechoso",
    sospechosos([], DIFERENCIA, manager=NOSOTROS) == []
    and sospechosos(None, DIFERENCIA, manager=NOSOTROS) == [],
)

# La reja de esta guardia: si el tablon llegara vacio, el
# `suspect_types` de abajo saldria vacio y todo lo que sigue se
# cae. Aqui se deja dicho a proposito.
vacio = cuadra(
    RECONSTRUIDA,
    REAL,
    eventos=[],
    manager=NOSOTROS,
)

check(
    "y con la lista vacia la comprobacion NO senala nada",
    vacio["suspect_types"] == [] and vacio["suspects"] == [],
    f"(tipos={vacio['suspect_types']})",
)

check(
    "pero lo dice con palabras en vez de callarse",
    "metodo" in (vacio["reason"] or ""),
    f"(motivo={vacio['reason']!r})",
)


# ================================================================
# 1. CON DESCUADRE SE PUBLICA EL TIPO, NO SOLO EL NUMERO
# ================================================================

print()
print("1. No cuadra: se publica la diferencia Y el tipo")

resultado = cuadra(
    RECONSTRUIDA,
    REAL,
    eventos=TABLON,
    manager=NOSOTROS,
)

check(
    "la comprobacion dice que no cuadra",
    resultado["available"] is True and resultado["ok"] is False,
)

check(
    "publica la diferencia",
    resultado["difference"] == DIFERENCIA,
    f"(diferencia={resultado['difference']})",
)

check(
    "publica el tipo de evento sospechoso",
    resultado["suspect_types"] != [],
    f"(tipos={resultado['suspect_types']})",
)

check(
    "y el tipo es `transfer`",
    "transfer" in resultado["suspect_types"],
    f"(tipos={resultado['suspect_types']})",
)

check(
    "el motivo nombra el tipo con palabras, no solo el numero",
    "transfer" in (resultado["reason"] or ""),
    f"(motivo={resultado['reason']!r})",
)


# ================================================================
# 2. EL EVENTO CONCRETO, NO UNA TEORIA
# ================================================================

print()
print("2. El sospechoso es el evento concreto")

clavado = [
    s for s in resultado["suspects"] if s["match"] == "IMPORTE_EXACTO"
]

check(
    "hay un sospechoso cuyo importe cuadra al euro",
    len(clavado) == 1,
    f"(encontrados={len(clavado)})",
)

if clavado:

    uno = clavado[0]

    check(
        "es la venta de Lunin, por su jugador y su importe",
        uno["player"] == 15289 and uno["amount"] == DIFERENCIA,
        f"(jugador={uno['player']}, importe={uno['amount']})",
    )

    check(
        "y se dice que es NUESTRO",
        uno["ours"] is True,
    )

    check(
        "va primero: lo nuestro es la unica caja comprobable",
        resultado["suspects"][0]["match"] == "IMPORTE_EXACTO",
        f"(primero={resultado['suspects'][0]['match']})",
    )

check(
    "y se dice si sobra un cobro o falta un pago",
    "sobra un cobro" in (resultado["reason"] or ""),
    f"(motivo={resultado['reason']!r})",
)


# ================================================================
# 3. LA REEMISION CON OTRA FECHA
# ================================================================

print()
print("3. La copia que la reja no ve")

copias = [
    s
    for s in resultado["suspects"]
    if s["match"] == "REEMITIDA_CON_OTRA_FECHA"
]

check(
    "se detecta la venta reemitida con otra fecha",
    len(copias) == 1,
    f"(encontradas={len(copias)})",
)

if copias:

    copia = copias[0]

    check(
        "con sus dos copias",
        copia["copies"] == 2,
        f"(copias={copia['copies']})",
    )

    check(
        "y se dice cuanto se cuenta de mas",
        copia["overcount"] == 2_464_100,
        f"(sobrecuenta={copia['overcount']})",
    )

    check(
        "marcada como de un rival, no nuestra",
        copia["ours"] is False,
    )


# ================================================================
# 4. DOS COBROS NO SON UNA COPIA
# ================================================================

print()
print("4. La racha diaria de dos dias no se marca")

check(
    "ninguna racha diaria sale como copia",
    all(s["type"] != "bonus" for s in resultado["suspects"]),
    f"(sospechosos={[(s['type'], s['match']) for s in resultado['suspects']]})",
)

# El separador es la ventana, y se comprueba que es la ventana y
# no la casualidad: las mismas dos rachas PEGADAS si son copia.
pegadas = [
    racha(RACHA_LUNES, NOSOTROS, "d1"),
    racha(RACHA_LUNES + 120, NOSOTROS, "d2"),
]

check(
    "pero dos rachas iguales a dos minutos SI lo son",
    any(
        s["match"] == "REEMITIDA_CON_OTRA_FECHA"
        for s in sospechosos(pegadas, 250_000, manager=NOSOTROS)
    ),
)

check(
    "la ventana separa las dos cosas con holgura",
    120 < VENTANA_REEMISION < 86_400,
    f"(ventana={VENTANA_REEMISION})",
)


# ================================================================
# 5. CUANDO CUADRA NO SE INVENTAN SOSPECHOSOS
# ================================================================

print()
print("5. Cuadrando, no se senala a nadie")

cuadrado = cuadra(REAL, REAL, eventos=TABLON, manager=NOSOTROS)

check(
    "cuadra",
    cuadrado["ok"] is True and cuadrado["difference"] == 0,
)

check(
    "y no senala ningun evento",
    cuadrado["suspects"] == [] and cuadrado["suspect_types"] == [],
    f"(sospechosos={cuadrado['suspects']})",
)

check(
    "sin las dos cifras no se compara ni se senala",
    cuadra(None, REAL, eventos=TABLON)["available"] is False
    and cuadra(REAL, None, eventos=TABLON)["available"] is False,
)


# ================================================================
# RESULTADO
# ================================================================

print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
