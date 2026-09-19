"""
La republicacion legitima pasa.

EL OTRO LADO DEL FRENO

    Frenar las repeticiones es la mitad facil. La cara es no
    frenar lo que SI hay que hacer — y ahi el fallo no se ve,
    porque lo que no pasa no deja rastro en ningun libro.

    Dos casos son republicacion legitima:

        1. EL PRECIO CAMBIO. El de Biwenger se mueve cada dia, y
           el de escaparate sale de el. Una publicacion a 3,14 M
           sobre un mercado que ya va por 2,5 M esta pidiendo un
           precio que nadie va a pagar.

        2. LA PUBLICACION CADUCO. Sigue figurando en la lista y
           ya no esta viva. Si no se vuelve a poner, el jugador
           se queda fuera del escaparate para siempre.

    Con el freno viejo —un conjunto de `player_id` a secas— los
    dos casos quedaban bloqueados: el jugador estaba en el
    conjunto y se saltaba, punto. Cambiar el precio de una
    publicacion era IMPOSIBLE por este camino.

QUE COMPRUEBA ESTA GUARDIA

    1. Cambiado el precio, SI se republica.
    2. Caducada la publicacion, SI se republica — aunque el
       precio sea el mismo.
    3. Las dos cosas a la vez, tambien.
    4. Y el control: al mismo precio y viva, NO.
    5. El precio nuevo es el que sale del mercado de ahora, no
       el viejo.

LA GUARDIA MUERDE SI EL CASO DE PRUEBA NO INCLUYE LAS DOS

    Si el banco no trae a la vez un cambio de precio y una
    caducidad, las comprobaciones pasarian por vacuidad. Por eso
    lo primero es exigir las dos, y ademas el control de que al
    mismo precio y viva se frena.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El precio de partida es el real de
    Trent el 13/09 (mercado 2.730.000, publicado 3.139.500). No
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

MERCADO_VIEJO = 2_730_000

MERCADO_NUEVO = 2_400_000

PRECIO_VIEJO = precio_de_escaparate(MERCADO_VIEJO)

PRECIO_NUEVO = precio_de_escaparate(MERCADO_NUEVO)

VIAJES = [{"player_id": TRENT, "name": "Trent"}]

TITULARES = [1]


def plantilla(mercado):
    return [
        {
            "id": TRENT,
            "name": "Trent",
            "price": mercado,
            "position": 2,
        },
        {
            "id": 1,
            "name": "Titular",
            "price": 5_000_000,
            "position": 3,
        },
    ]


def listado(precio, caducado=False):
    return [
        {
            "player_id": TRENT,
            "name": "Trent",
            "listed_price": precio,
            "expired": caducado,
        }
    ]


def plan(mercado, publicado, caducado=False):
    return que_publicar(
        ganadas=VIAJES,
        plantilla=plantilla(mercado),
        ya_listados=listado(publicado, caducado),
        titulares=TITULARES,
        lo_publicado_se_sabe=True,
    )


# ================================================================
# 0. EL BANCO TRAE LOS DOS CASOS
# ================================================================

print()
print("0. El banco trae cambio de precio Y caducidad")

check(
    "los dos precios de escaparate son distintos",
    PRECIO_VIEJO != PRECIO_NUEVO,
    f"({PRECIO_VIEJO} vs {PRECIO_NUEVO})",
)

check(
    "el mercado ha bajado de verdad",
    MERCADO_NUEVO < MERCADO_VIEJO,
    f"({MERCADO_VIEJO} -> {MERCADO_NUEVO})",
)

check(
    "y el banco sabe marcar una publicacion caducada",
    listado(PRECIO_VIEJO, caducado=True)[0]["expired"] is True,
)


# ================================================================
# 1. EL CONTROL: MISMO PRECIO Y VIVA, NO SE TOCA
# ================================================================

print()
print("1. El control: mismo precio y viva, no se republica")

igual = plan(MERCADO_VIEJO, PRECIO_VIEJO)

check(
    "no se publica",
    igual["publicar"] == [],
    f"({igual['publicar']})",
)

check(
    "y lo dice con su precio",
    "3.139.500" in igual["saltados"][0]["reason"],
    f"({igual['saltados'][0]['reason']})",
)


# ================================================================
# 2. PRECIO CAMBIADO: SI SALE
# ================================================================

print()
print("2. Cambiado el precio, si se republica")

cambiado = plan(MERCADO_NUEVO, PRECIO_VIEJO)

print(f"       publicar: {cambiado['publicar']}")

check(
    "se republica",
    len(cambiado["publicar"]) == 1,
    f"({cambiado['publicar']}, saltados={cambiado['saltados']})",
)

check(
    "al precio NUEVO, no al viejo",
    cambiado["publicar"][0]["listed_price"] == PRECIO_NUEVO,
    f"({cambiado['publicar'][0]['listed_price']} "
    f"esperado {PRECIO_NUEVO})",
)

check(
    "y el precio nuevo sale del mercado de ahora",
    cambiado["publicar"][0]["market_price"] == MERCADO_NUEVO,
    f"({cambiado['publicar'][0]['market_price']})",
)


# ================================================================
# 3. CADUCADA: SI SALE, AUNQUE EL PRECIO SEA EL MISMO
# ================================================================

print()
print("3. Caducada, si se republica aunque el precio no cambie")

caducada = plan(MERCADO_VIEJO, PRECIO_VIEJO, caducado=True)

check(
    "se republica",
    len(caducada["publicar"]) == 1,
    f"({caducada['publicar']}, saltados={caducada['saltados']})",
)

check(
    "al mismo precio, que es el que toca",
    caducada["publicar"][0]["listed_price"] == PRECIO_VIEJO,
    f"({caducada['publicar'][0]['listed_price']})",
)


# ================================================================
# 4. LAS DOS COSAS A LA VEZ
# ================================================================

print()
print("4. Caducada Y con el precio cambiado")

ambas = plan(MERCADO_NUEVO, PRECIO_VIEJO, caducado=True)

check(
    "se republica",
    len(ambas["publicar"]) == 1,
    f"({ambas['publicar']})",
)

check(
    "al precio nuevo",
    ambas["publicar"][0]["listed_price"] == PRECIO_NUEVO,
    f"({ambas['publicar'][0]['listed_price']})",
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
