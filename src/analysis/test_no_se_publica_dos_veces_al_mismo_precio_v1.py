"""
No se publica dos veces al mismo precio.

EL CASO, Y LO QUE HAY QUE CORREGIR DE COMO SE CONTO

    `libro_de_escaparate.jsonl`: 16 escrituras, 1 operacion,
    93,8 % de desperdicio. Trent, el 13/09, de 12:05 a 20:10.

    Las DIECISEIS filas son IDENTICAS: mismo jugador, mismo
    `listed_price` (3.139.500), mismo `market_price`, mismo
    margen, todas `sent: True` y HTTP 204.

    Asi que no hay una decimosexta distinta. El "1 operacion" de
    aquella tabla era el recuento DEDUPLICADO, y la que
    sobrevive es simplemente la PRIMERA — la que de verdad puso
    el jugador en el escaparate. Las otras quince son reenvios
    del mismo hecho.

POR QUE PASO, Y YA ESTABA ARREGLADO

    El freno de idempotencia existia -`if pid in en_venta`- y no
    podia dar nunca que si, porque `compact_listings` NO TENIA la
    clave `rows` y los dos consumidores recibian `[]` siempre. Lo
    cuenta el propio codigo, fechado «13/09/2026, noche»: la
    misma noche de las dieciseis publicaciones.

    Por eso no hay ni una repeticion del escaparate despues del
    13/09 20:10.

LO QUE SEGUIA ABIERTO, Y ES LO QUE SE ARREGLA AQUI

    1. `en_venta` era un conjunto de `player_id` a secas, asi que
       «ya esta publicado» tapaba dos casos: publicado al mismo
       precio (no hay que tocarlo) y publicado a OTRO precio (hay
       que republicar). Cambiar el precio de una publicacion era
       imposible por este camino.

    2. Y `rows: []` seguia valiendo por dos cosas: «no hay nada
       publicado» y «no he podido leerlo». La segunda es
       exactamente la que publico a Trent dieciseis veces.

QUE COMPRUEBA ESTA GUARDIA

    1. Un jugador ya publicado a X no se republica a X.
    2. El motivo dice el precio, no solo «ya esta publicado».
    3. Dieciseis vueltas seguidas dan UNA publicacion.
    4. Sin poder leer lo publicado, no se publica nada.
    5. Publicado a un precio DESCONOCIDO tampoco se toca a
       ciegas.

LA GUARDIA MUERDE CON LA LISTA DE PUBLICACIONES VACIA

    Con `ya_listados` vacio no hay nada que frenar y todo pasaria
    por vacuidad. Por eso lo primero es exigir que el banco
    traiga una publicacion viva del jugador que se va a publicar.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui, copiados de la publicacion real de
    Trent del 13/09 (3.139.500 sobre un mercado de 2.730.000). No
    se lee `data/`, no se sale a la red y no se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.actions.escaparate_executor import (  # noqa: E402
    precio_de_escaparate,
    que_publicar,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


TRENT = 37499

MERCADO = 2_730_000

PUBLICADO = precio_de_escaparate(MERCADO)

# El viaje abierto del carril, que es lo que se publica.
VIAJES = [{"player_id": TRENT, "name": "Trent"}]

PLANTILLA = [
    {"id": TRENT, "name": "Trent", "price": MERCADO, "position": 2},
    {"id": 1, "name": "Titular", "price": 5_000_000, "position": 3},
]

TITULARES = [1]


def listado(precio, caducado=False):
    return [
        {
            "player_id": TRENT,
            "name": "Trent",
            "listed_price": precio,
            "expired": caducado,
        }
    ]


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. La lista de publicaciones no llega vacia")

check(
    "el precio de escaparate sale del mercado",
    PUBLICADO == 3_139_500,
    f"({PUBLICADO})",
)

check(
    "y el banco trae a Trent ya publicado a ese precio",
    listado(PUBLICADO)[0]["listed_price"] == PUBLICADO,
)

check(
    "hay un viaje que publicar",
    len(VIAJES) == 1,
)

# Sin nada publicado, SI se publica: si no, lo de abajo pasaria
# por vacuidad.
sin_nada = que_publicar(
    ganadas=VIAJES,
    plantilla=PLANTILLA,
    ya_listados=[],
    titulares=TITULARES,
    lo_publicado_se_sabe=True,
)

check(
    "con nada publicado, Trent SI se publica",
    len(sin_nada["publicar"]) == 1,
    f"({sin_nada['reason']})",
)


# ================================================================
# 1. YA PUBLICADO AL MISMO PRECIO: NO SE REPUBLICA
# ================================================================

print()
print("1. Ya publicado a X no se republica a X")

mismo = que_publicar(
    ganadas=VIAJES,
    plantilla=PLANTILLA,
    ya_listados=listado(PUBLICADO),
    titulares=TITULARES,
    lo_publicado_se_sabe=True,
)

print(f"       {mismo['saltados']}")

check(
    "no se publica nada",
    mismo["publicar"] == [],
    f"({mismo['publicar']})",
)

check(
    "y sale como saltado",
    len(mismo["saltados"]) == 1,
    f"({mismo['saltados']})",
)

check(
    "el motivo dice el precio, no solo que ya esta",
    "3.139.500" in mismo["saltados"][0]["reason"],
    f"({mismo['saltados'][0]['reason']})",
)


# ================================================================
# 2. DIECISEIS VUELTAS, UNA PUBLICACION
# ================================================================

print()
print("2. Dieciseis vueltas dan una publicacion")

publicadas = 0

listados_ahora = []

for vuelta in range(16):

    plan = que_publicar(
        ganadas=VIAJES,
        plantilla=PLANTILLA,
        ya_listados=listados_ahora,
        titulares=TITULARES,
        lo_publicado_se_sabe=True,
    )

    if plan["publicar"]:
        publicadas += 1
        # Lo que Biwenger diria a partir de ahora.
        listados_ahora = listado(PUBLICADO)

print(f"       publicaciones en 16 vueltas: {publicadas}")

check(
    "dieciseis vueltas dan UNA publicacion",
    publicadas == 1,
    f"({publicadas})",
)


# ================================================================
# 3. SIN SABER LO PUBLICADO, NO SE PUBLICA
# ================================================================

print()
print("3. No saber que hay publicado no es via libre")

a_ciegas = que_publicar(
    ganadas=VIAJES,
    plantilla=PLANTILLA,
    ya_listados=[],
    titulares=TITULARES,
    lo_publicado_se_sabe=False,
)

print(f"       {a_ciegas['reason']}")

check(
    "no se publica nada",
    a_ciegas["publicar"] == [],
    f"({a_ciegas['publicar']})",
)

check(
    "y el motivo lo distingue de «no hay nada publicado»",
    "no saberlo no es que no haya nada"
    in (a_ciegas["reason"] or ""),
    f"({a_ciegas['reason']})",
)

check(
    "con la misma entrada pero sabiendolo, SI publica",
    len(sin_nada["publicar"]) == 1,
)


# ================================================================
# 4. PUBLICADO A PRECIO DESCONOCIDO: NO SE TOCA
# ================================================================

print()
print("4. Publicado y sin saber a cuanto: no se toca a ciegas")

sin_precio = que_publicar(
    ganadas=VIAJES,
    plantilla=PLANTILLA,
    ya_listados=listado(0),
    titulares=TITULARES,
    lo_publicado_se_sabe=True,
)

check(
    "no se republica",
    sin_precio["publicar"] == [],
    f"({sin_precio['publicar']})",
)

check(
    "y lo dice",
    "no consta a que precio"
    in (sin_precio["saltados"][0]["reason"] or ""),
    f"({sin_precio['saltados']})",
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
