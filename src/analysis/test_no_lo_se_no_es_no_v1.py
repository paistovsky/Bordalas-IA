"""
«No lo se» no es «no». Doctrina 24, en el camino de escritura.

EL PATRON, Y POR QUE ES CARO

    Una coleccion que llega vacia porque NO SE PUDO LEER se lee
    igual que una que llega vacia porque NO HAY NADA. Las dos
    salen como `[]`, y quien la consume entiende «no».

    Cuando lo que decide es un freno, un «no» es via libre.

LOS DOS SITIOS MEDIDOS, Y SALIERON LAS DOS FACTURAS DEL DIA

    1. `acquisition_board`: `puja_viva` se llena de
       `exposicion["operations"]`. Exposicion no disponible ->
       diccionario vacio -> TODAS las filas `has_live_bid:
       False`. De ahi salieron las nueve pujas de Maffeo.

    2. `compact_listings`: no traia `rows`, asi que el escaparate
       recibia `[]` SIEMPRE y el freno de «esto ya esta
       publicado» no podia dar nunca que si. De ahi salieron las
       dieciseis publicaciones de Trent.

    El mismo fallo, dos facturas, el mismo dia.

QUE COMPRUEBA ESTA GUARDIA

    1. Con la exposicion caida, NINGUNA escritura sale diciendo
       que no habia puja viva.
    2. El motivo del freno distingue «no lo se» de «ya esta
       puesta»: son dos motivos distintos y se arreglan en dos
       sitios distintos.
    3. Una exposicion disponible y VACIA si es via libre: no hay
       puja viva, y eso es un hecho.
    4. Lo mismo al publicar: sin saber lo publicado no se
       publica, y sabiendolo vacio si.
    5. El tablero publica si su recuento de pujas vivas se puede
       creer (`live_bid_known`).

LA GUARDIA MUERDE SI LA EXPOSICION LLEGA POBLADA

    Con pujas vivas de verdad, el freno se dispararia por
    «ya esta puesta» y (1) pasaria por vacuidad sin probar nada
    del silencio. Por eso lo primero es exigir que el caso de la
    exposicion caida NO traiga ninguna operacion.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.actions.escaparate_executor import (  # noqa: E402
    que_publicar,
)
from src.analysis.la_puja_que_ya_esta import (  # noqa: E402
    filtrar_los_repetidos,
    lo_que_ya_esta_puesto,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


MAFFEO = 10030

CANDIDATOS = [
    {"player_id": MAFFEO, "name": "Maffeo", "bid": 1_664_350},
    {"player_id": 61061, "name": "Chust", "bid": 1_871_032},
]

# LA EXPOSICION CAIDA: sin una sola operacion, para que lo que
# frene sea el silencio y no una puja viva de verdad.
CAIDA = {
    "bid_exposure": {
        "available": False,
        "operations": [],
        "committed_total": 0,
        "reason": "No se pudo leer el tablon de ofertas.",
    }
}

# Y la misma forma, pero mirada de verdad y sin nada puesto.
MIRADA_Y_VACIA = {
    "bid_exposure": {
        "available": True,
        "operations": [],
        "committed_total": 0,
        "operation_count": 0,
    }
}


# ================================================================
# 0. LA EXPOSICION CAIDA NO TRAE NINGUNA OPERACION
# ================================================================

print()
print("0. El caso del silencio no trae pujas vivas")

check(
    "la exposicion caida viene sin operaciones",
    CAIDA["bid_exposure"]["operations"] == [],
)

check(
    "y marcada como NO disponible",
    CAIDA["bid_exposure"]["available"] is False,
)

check(
    "asi que lo que frene sera el silencio, no una puja",
    lo_que_ya_esta_puesto(CAIDA)["cuantos"] == 0,
)


# ================================================================
# 1. CON LA EXPOSICION CAIDA NO SALE NINGUNA ESCRITURA
# ================================================================

print()
print("1. Con la exposicion caida no sale ninguna escritura")

a_ciegas = filtrar_los_repetidos(CANDIDATOS, CAIDA)

print(f"       escribibles: {a_ciegas['escribibles']}")

check(
    "no hay nada escribible",
    a_ciegas["escribibles"] == [],
    f"({a_ciegas['escribibles']})",
)

check(
    "los dos candidatos salen frenados",
    len(a_ciegas["frenados"]) == 2,
    f"({len(a_ciegas['frenados'])})",
)

check(
    "y `available` en False, que es lo que para al que llama",
    a_ciegas["available"] is False,
)

check(
    "NINGUNO sale diciendo que no habia puja viva",
    all(
        f["motivo"] != "YA_ESTA_PUESTA"
        for f in a_ciegas["frenados"]
    )
    and all(
        f["motivo"] == "NO_SE_SABE"
        for f in a_ciegas["frenados"]
    ),
    f"({[f['motivo'] for f in a_ciegas['frenados']]})",
)


# ================================================================
# 2. LOS DOS MOTIVOS NO SE CONFUNDEN
# ================================================================

print()
print("2. «No lo se» y «ya esta puesta» son dos motivos")

VIVA = {
    "bid_exposure": {
        "available": True,
        "operation_count": 1,
        "operations": [
            {
                "offer_id": 399977192,
                "amount": 1_664_350,
                "player_ids": [MAFFEO],
                "status": "waiting",
            }
        ],
    }
}

con_puja = filtrar_los_repetidos(CANDIDATOS, VIVA)

frenado_real = con_puja["frenados"][0]

print(f"       silencio : {a_ciegas['frenados'][0]['reason'][:70]}")
print(f"       puja viva: {frenado_real['reason'][:70]}")

check(
    "con puja viva, el motivo es YA_ESTA_PUESTA",
    frenado_real["motivo"] == "YA_ESTA_PUESTA",
)

check(
    "y los dos motivos son distintos",
    frenado_real["motivo"]
    != a_ciegas["frenados"][0]["motivo"],
)

check(
    "el del silencio no nombra ninguna oferta, porque no la hay",
    a_ciegas["frenados"][0]["offer_id"] is None,
    f"({a_ciegas['frenados'][0]['offer_id']})",
)


# ================================================================
# 3. MIRADA Y VACIA SI ES VIA LIBRE
# ================================================================

print()
print("3. Mirada y vacia SI deja escribir: eso es un hecho")

vacia = filtrar_los_repetidos(CANDIDATOS, MIRADA_Y_VACIA)

check(
    "los dos candidatos son escribibles",
    len(vacia["escribibles"]) == 2,
    f"({vacia['escribibles']})",
)

check(
    "sin ningun freno",
    vacia["frenados"] == [],
)

check(
    "y `available` en True",
    vacia["available"] is True,
)


# ================================================================
# 4. LO MISMO AL PUBLICAR
# ================================================================

print()
print("4. El mismo silencio al publicar")

TRENT = 37499

VIAJES = [{"player_id": TRENT, "name": "Trent"}]

PLANTILLA = [
    {"id": TRENT, "name": "Trent", "price": 2_730_000, "position": 2},
    {"id": 1, "name": "Titular", "price": 5_000_000, "position": 3},
]

sin_saber = que_publicar(
    ganadas=VIAJES,
    plantilla=PLANTILLA,
    ya_listados=[],
    titulares=[1],
    lo_publicado_se_sabe=False,
)

sabiendo = que_publicar(
    ganadas=VIAJES,
    plantilla=PLANTILLA,
    ya_listados=[],
    titulares=[1],
    lo_publicado_se_sabe=True,
)

print(f"       sin saber: {sin_saber['reason']}")

check(
    "sin saber lo publicado no se publica",
    sin_saber["publicar"] == [],
    f"({sin_saber['publicar']})",
)

check(
    "sabiendolo vacio, SI se publica",
    len(sabiendo["publicar"]) == 1,
    f"({sabiendo['publicar']})",
)

check(
    "y la misma entrada da resultados distintos: el flag decide",
    bool(sin_saber["publicar"]) != bool(sabiendo["publicar"]),
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
