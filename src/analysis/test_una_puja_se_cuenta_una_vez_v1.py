"""
Una puja se cuenta una vez.

MISMA FAMILIA QUE LA REJA DEL TABLON

    La clave del libro era `player_id:placed_at`, asi que la
    misma puja entraba UNA VEZ POR VUELTA HORARIA. Medido sobre
    el libro del 19/09/2026:

        47 entradas   ->   23 pujas de verdad     (x2,04)
        9 event_id distintos, 14 entradas sin event_id

        Maffeo     10 entradas, mismo event_id, mismo importe
        Boyomo      9
        Oriol Rey   5

    Alli la fecha en la clave descuadraba la caja. Aqui descuadra
    CUANTAS PUJAS PONEMOS Y CUANTAS GANAMOS, que es de donde
    salen las estadisticas que se venian citando.

POR QUE NO SE PUEDE USAR `event_id` A SECAS

    Cuando se anota la puja, `event_id` es None: no se sabe hasta
    que el tablon la resuelve. Lo que identifica a una puja viva
    es el par (jugador, importe) mientras siga PENDIENTE — que es
    lo que el propio libro ya usaba en `ya_estan` para no recoger
    dos veces la misma del tablon.

    Asi que: al anotar manda (jugador, importe) mientras este
    viva; al colapsar lo ya escrito manda el `event_id`.

LA FECHA NO SE PIERDE

    Quien reusa la clave conserva el `placed_at` ORIGINAL. De ahi
    sale cuanto tiempo estuvo viva una puja, y la primera marca
    es la buena.

QUE COMPRUEBA ESTA GUARDIA

    1. El mismo `event_id` en diez vueltas distintas da UNA
       entrada.
    2. Anotar diez veces la misma puja viva da UNA entrada, y
       conserva el `placed_at` de la primera.
    3. Dos pujas de verdad por el mismo jugador a importes
       distintos siguen siendo DOS.
    4. Una repeticion legitima -mismo jugador, mismo importe,
       pero la primera ya resuelta- sigue siendo DOS.

LA GUARDIA MUERDE CON EL LIBRO VACIO

    Sin pujas no hay nada que contar dos veces y todo pasaria por
    vacuidad. Por eso lo primero es exigir que el banco traiga
    libro.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj: cada `placed_at` es una marca escrita a mano y
    `save=False` en todas las anotaciones.
"""

import sys

sys.path.insert(0, ".")

from src.intelligence.bid_outcome_ledger import (  # noqa: E402
    clave_de_la_puja,
    deduplicar,
    record_bid,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


MAFFEO = 10030

IMPORTE = 1_664_350

EVENTO = "3d15660bd0c3d1e7813beaab"

# Las nueve vueltas reales del 18/09, tal cual.
VUELTAS = [
    "2026-09-18T05:23:13.169304+00:00",
    "2026-09-18T07:14:46.541780+00:00",
    "2026-09-18T08:14:54.128055+00:00",
    "2026-09-18T09:12:16.134981+00:00",
    "2026-09-18T10:15:10.109578+00:00",
    "2026-09-18T11:15:35.156605+00:00",
    "2026-09-18T12:16:07.714290+00:00",
    "2026-09-18T13:15:04.151555+00:00",
    "2026-09-18T14:15:17.836437+00:00",
]


# ================================================================
# 0. EL LIBRO NO LLEGA VACIO
# ================================================================

print()
print("0. El libro de pujas no llega vacio")

check(
    "el banco trae las nueve vueltas",
    len(VUELTAS) == 9,
    f"(n={len(VUELTAS)})",
)

check(
    "con el libro vacio no hay nada que deduplicar",
    deduplicar({"bids": {}})["bids"] == {},
)

check(
    "y con el libro vacio la clave es nueva",
    clave_de_la_puja({"bids": {}}, MAFFEO, IMPORTE, VUELTAS[0])
    == f"{MAFFEO}:{VUELTAS[0]}",
)


# ================================================================
# 1. ANOTAR LA MISMA PUJA VIVA NUEVE VECES DA UNA ENTRADA
# ================================================================

print()
print("1. Nueve vueltas, una puja")

libro = {"bids": {}}

for puesta in VUELTAS:
    record_bid(
        MAFFEO,
        IMPORTE,
        player_name="Maffeo",
        target_source="RENDIJA",
        placed_at=puesta,
        ledger=libro,
        save=False,
    )

print(f"       entradas tras nueve vueltas: {len(libro['bids'])}")

check(
    "nueve anotaciones dan una entrada",
    len(libro["bids"]) == 1,
    f"(dio {len(libro['bids'])})",
)

unica = list(libro["bids"].values())[0]

check(
    "y conserva el placed_at de la PRIMERA vuelta",
    unica["placed_at"] == VUELTAS[0],
    f"(dio {unica['placed_at']}, esperado {VUELTAS[0]})",
)

check(
    "con el importe intacto",
    unica["amount"] == IMPORTE,
)


# ================================================================
# 2. EL MISMO event_id EN DIEZ VUELTAS DA UNA ENTRADA
# ================================================================

print()
print("2. El mismo event_id en diez vueltas da una entrada")

# Lo ya escrito con la clave vieja: diez entradas resueltas.
viejo = {
    "bids": {
        f"{MAFFEO}:{puesta}": {
            "player_id": MAFFEO,
            "player_name": "Maffeo",
            "amount": IMPORTE,
            "target_source": "RENDIJA",
            "placed_at": puesta,
            "outcome": "WON",
            "resolved_at": "2026-09-19T05:26:03.785314+00:00",
            "event_id": EVENTO,
        }
        for puesta in VUELTAS
    }
}

check(
    "el libro viejo trae las nueve",
    len(viejo["bids"]) == 9,
)

limpio = deduplicar(viejo)

check(
    "deduplicar deja una",
    len(limpio["bids"]) == 1,
    f"(dio {len(limpio['bids'])})",
)

sobreviviente = list(limpio["bids"].values())[0]

check(
    "y la que queda lleva el placed_at mas temprano",
    sobreviviente["placed_at"] == VUELTAS[0],
    f"(dio {sobreviviente['placed_at']})",
)

check(
    "sin perder el event_id",
    sobreviviente["event_id"] == EVENTO,
)


# ================================================================
# 3. DOS PUJAS DE VERDAD SIGUEN SIENDO DOS
# ================================================================

print()
print("3. Lo que SI son dos pujas, siguen siendo dos")

# (a) Mismo jugador, importe distinto: subimos la puja.
dos_importes = {"bids": {}}

record_bid(
    MAFFEO, IMPORTE, placed_at=VUELTAS[0],
    ledger=dos_importes, save=False,
)

record_bid(
    MAFFEO, IMPORTE + 50_000, placed_at=VUELTAS[3],
    ledger=dos_importes, save=False,
)

check(
    "dos importes distintos son dos pujas",
    len(dos_importes["bids"]) == 2,
    f"(dio {len(dos_importes['bids'])})",
)

# (b) Mismo jugador y mismo importe, pero la primera YA resuelta:
#     lo compramos, lo vendimos y lo volvimos a comprar.
repetida = {"bids": {}}

record_bid(
    MAFFEO, IMPORTE, placed_at=VUELTAS[0],
    ledger=repetida, save=False,
)

for fila in repetida["bids"].values():
    fila["outcome"] = "WON"
    fila["resolved_at"] = "2026-09-19T05:26:03+00:00"
    fila["event_id"] = EVENTO

record_bid(
    MAFFEO, IMPORTE, placed_at="2026-09-24T05:20:00+00:00",
    ledger=repetida, save=False,
)

check(
    "una repeticion legitima con la primera resuelta son dos",
    len(repetida["bids"]) == 2,
    f"(dio {len(repetida['bids'])})",
)

check(
    "y deduplicar no las funde",
    len(deduplicar(repetida)["bids"]) == 2,
    f"(dio {len(deduplicar(repetida)['bids'])})",
)


# ================================================================
# 4. EL CASO REAL: 47 ENTRADAS, 23 PUJAS
# ================================================================

print()
print("4. El caso real del libro del 19/09")

# Reproducido con la misma forma: 9 grupos con event_id (uno de
# ellos x10, otro x9, otro x5, tres x2) y 14 sueltas sin evento.
real = {"bids": {}}

reparto = [10, 9, 5, 2, 2, 2, 1, 1, 1]

for grupo, veces in enumerate(reparto):
    for i in range(veces):
        real["bids"][f"{900 + grupo}:2026-09-18T{i:02d}:00:00+00:00"] = {
            "player_id": 900 + grupo,
            "amount": 100_000 + grupo,
            "placed_at": f"2026-09-18T{i:02d}:00:00+00:00",
            "outcome": "WON",
            "resolved_at": "2026-09-19T05:26:03+00:00",
            "event_id": f"evento{grupo:02d}",
        }

for suelta in range(14):
    real["bids"][f"{800 + suelta}:2026-09-17T05:08:00+00:00"] = {
        "player_id": 800 + suelta,
        "amount": 400_000 + suelta,
        "placed_at": "2026-09-17T05:08:00+00:00",
        "outcome": "WON",
        "resolved_at": "2026-09-17T05:08:00+00:00",
        "event_id": None,
    }

check(
    "el libro crudo tiene 47 entradas",
    len(real["bids"]) == 47,
    f"(dio {len(real['bids'])})",
)

real_limpio = deduplicar(real)

check(
    "y limpio, 23 pujas",
    len(real_limpio["bids"]) == 23,
    f"(dio {len(real_limpio['bids'])})",
)

check(
    "factor de inflacion x2,04",
    round(47 / len(real_limpio["bids"]), 2) == 2.04,
    f"(x{47 / len(real_limpio['bids']):.2f})",
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
