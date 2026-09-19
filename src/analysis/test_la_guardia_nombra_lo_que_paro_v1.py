"""
La guardia nombra lo que paro.

DOCTRINA 87, QUE YA VA CUATRO VECES ESTE MES

    Un motivo que nombra un campo distinto del que decidio es una
    frase falsa, aunque todos los numeros que cita sean ciertos.
    Este mes: el `intent` prestado por el `max()`, el motivo
    truncado, el reloj de solvencia que culpaba a `CUBIERTO`
    cuando bloqueo `deficit > 0`, y las dos frases de Trent.

    Una guardia que frena una escritura y dice "ya estaba puesta"
    SIN DECIR CUAL es exactamente esa forma: cierta, inutil, y el
    dia que este mal nadie lo va a ver. Con el id de la oferta
    delante se puede abrir Biwenger y comprobarlo en diez
    segundos.

LO QUE TIENE QUE DECIR CADA FRENO

    - el jugador, por su nombre;
    - el id de la operacion viva que lo paro;
    - su importe.

    Y cuando el freno NO es "ya estaba puesta" sino "no he podido
    mirar", tiene que decir ESO, con otro motivo, porque se
    arregla en otro sitio.

QUE COMPRUEBA ESTA GUARDIA

    1. El freno nombra al jugador.
    2. El freno nombra el id de la oferta viva.
    3. El freno nombra el importe.
    4. Los dos motivos son distintos y no se confunden:
       `YA_ESTA_PUESTA` contra `NO_SE_SABE`.
    5. Un freno sin id no se calla el hueco: lo dice.

LA GUARDIA MUERDE SI NO HAY NINGUNA REPETICION

    Sin repeticion no hay freno que explicar y las cinco pasarian
    por vacuidad. Por eso lo primero es exigir que el caso de
    prueba tenga una.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui, copiados de la puja real de Maffeo del
    18/09 (oferta 399977192, 1.664.350 EUR). No se lee `data/`,
    no se sale a la red y no se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.la_puja_que_ya_esta import (  # noqa: E402
    filtrar_los_repetidos,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


MAFFEO = 10030

OFERTA_VIVA = 399977192

IMPORTE = 1_664_350

SPECULATION = {
    "bid_exposure": {
        "available": True,
        "operation_count": 1,
        "operations": [
            {
                "offer_id": OFERTA_VIVA,
                "amount": IMPORTE,
                "player_ids": [MAFFEO],
                "status": "waiting",
                "created": 1789733768,
            }
        ],
    }
}

CANDIDATOS = [
    {"player_id": MAFFEO, "name": "Maffeo", "bid": IMPORTE},
    {"player_id": 61061, "name": "Chust", "bid": 1_871_032},
]


# ================================================================
# 0. HAY UNA REPETICION QUE EXPLICAR
# ================================================================

print()
print("0. El caso de prueba tiene una repeticion")

filtrado = filtrar_los_repetidos(CANDIDATOS, SPECULATION)

check(
    "hay exactamente un freno",
    len(filtrado["frenados"]) == 1,
    f"(n={len(filtrado['frenados'])})",
)

check(
    "y es por una puja que de verdad esta viva",
    filtrado["frenados"][0]["player_id"] == MAFFEO,
)


# ================================================================
# 1. EL MOTIVO NOMBRA AL JUGADOR, LA OFERTA Y EL IMPORTE
# ================================================================

print()
print("1. El motivo nombra lo que paro")

freno = filtrado["frenados"][0]

print(f"       {freno['reason']}")

check(
    "dice el nombre del jugador",
    "Maffeo" in freno["reason"],
    f"({freno['reason']})",
)

check(
    "dice el id de la oferta viva",
    str(OFERTA_VIVA) in freno["reason"],
    f"({freno['reason']})",
)

check(
    "dice el importe",
    "1.664.350" in freno["reason"],
    f"({freno['reason']})",
)

check(
    "y lo lleva tambien en campos, no solo en la frase",
    freno["offer_id"] == OFERTA_VIVA
    and freno["amount"] == IMPORTE
    and freno["player_id"] == MAFFEO,
    f"({freno})",
)


# ================================================================
# 2. LOS DOS MOTIVOS NO SE CONFUNDEN
# ================================================================

print()
print("2. `ya estaba puesta` y `no he podido mirar` son distintos")

check(
    "una repeticion sale como YA_ESTA_PUESTA",
    freno["motivo"] == "YA_ESTA_PUESTA",
    f"({freno['motivo']})",
)

CIEGO = {
    "bid_exposure": {
        "available": False,
        "operations": [],
        "reason": "No se pudo leer el tablon de ofertas.",
    }
}

a_ciegas = filtrar_los_repetidos(CANDIDATOS, CIEGO)

ciego = a_ciegas["frenados"][0]

print(f"       {ciego['reason']}")

check(
    "no poder mirar sale como NO_SE_SABE",
    ciego["motivo"] == "NO_SE_SABE",
    f"({ciego['motivo']})",
)

check(
    "y su motivo dice que no se ha podido mirar",
    "no se sabe" in (ciego["reason"] or "").lower()
    or "no esta disponible" in (ciego["reason"] or "").lower(),
    f"({ciego['reason']})",
)

check(
    "arrastrando el motivo de por que no se pudo",
    "tablon de ofertas" in (ciego["reason"] or ""),
    f"({ciego['reason']})",
)

check(
    "los dos motivos son distintos",
    freno["motivo"] != ciego["motivo"],
)


# ================================================================
# 3. UN FRENO SIN ID NO SE CALLA EL HUECO
# ================================================================

print()
print("3. Sin id, se dice que no lo hay")

SIN_ID = {
    "bid_exposure": {
        "available": True,
        "operation_count": 1,
        "operations": [
            {
                "offer_id": None,
                "amount": 0,
                "player_ids": [MAFFEO],
                "status": "waiting",
            }
        ],
    }
}

sin_id = filtrar_los_repetidos(CANDIDATOS, SIN_ID)

freno_sin_id = sin_id["frenados"][0]

print(f"       {freno_sin_id['reason']}")

check(
    "sigue frenando",
    freno_sin_id["motivo"] == "YA_ESTA_PUESTA",
)

check(
    "y dice que no hay id en vez de callarselo",
    "sin id" in freno_sin_id["reason"],
    f"({freno_sin_id['reason']})",
)

check(
    "sin inventar un importe",
    "0 EUR" not in freno_sin_id["reason"],
    f"({freno_sin_id['reason']})",
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
