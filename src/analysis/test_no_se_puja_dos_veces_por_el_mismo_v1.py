"""
No se puja dos veces por el mismo.

EL CASO, MEDIDO EL 19/09/2026

    Sobre `libro_del_carril.jsonl`, que registra lo que de verdad
    salio contra Biwenger (`sent`, `http_status`):

        16 escrituras reales   ->   4 operaciones distintas
        Maffeo x9 en 8,9 h, cada una con su id de Biwenger
        Boyomo x5 en 3,7 h

    Y no es solo la puja. `libro_de_escaparate.jsonl`:

        16 escrituras   ->   1 operacion    (93,8 %)
        Trent, DIECISEIS publicaciones al mismo precio en 8,1 h

EL FALLO, CON NOMBRE

    No es que nadie sepa que hay una puja viva:
    `acquisition_board` calcula `has_live_bid` por fila, la
    publica en `targets`, ordena con ella y la descuenta de
    `actionable`. Y mete esas filas en `targets` A PROPOSITO,
    para que la pantalla ensene nuestro propio dinero.

    `carril_executor` recibe esas mismas filas y filtra por tres
    cosas —`market_price >= suelo`, `status == "ok"`,
    `not outside_computer_market`— y por ninguna mas.

    El campo viaja hasta la linea de la escritura y nadie lo
    mira. No es "pregunta y le contestan tarde": es que en el
    camino de escritura NO SE PREGUNTA.

EL SEGUNDO FALLO, QUE ESTABA DEBAJO

    `has_live_bid` sale de `puja_viva`, que se llena de
    `exposicion["operations"]`. Si la exposicion no esta
    disponible ese diccionario queda vacio y TODAS las filas
    salen `has_live_bid: False`: "no hay pujas" y "no he podido
    mirar" se escriben igual.

    Por eso la guardia distingue las dos cosas, y cuando no puede
    mirar NO deja escribir.

QUE COMPRUEBA ESTA GUARDIA

    1. Con una puja viva por un jugador, una segunda vuelta no
       escribe otra.
    2. El hueco que libera el repetido se lo queda otro candidato
       en la MISMA vuelta: no se pierde la escritura.
    3. Sin poder mirar lo puesto, no se escribe NADA.
    4. Apagada, el comportamiento es el de siempre.
    5. `players_with_live_bid()` sigue siendo la fuente del
       conjunto (doctrina 84: no se ha escrito una segunda).

LA GUARDIA MUERDE CON LA LISTA DE PUJAS VIVAS VACIA

    Sin pujas vivas no hay repeticion que evitar y todo pasaria
    por vacuidad. Por eso lo primero es exigir que el banco
    traiga una puja viva.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red, no se mira el
    reloj y no se escribe en ningun libro. El interruptor se pone
    y se quita aqui dentro.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.decision_orchestrator import (  # noqa: E402
    players_with_live_bid,
)
from src.analysis.la_puja_que_ya_esta import (  # noqa: E402
    GUARDIA_ENV,
    filtrar_los_repetidos,
    guardia_activa,
    lo_que_ya_esta_puesto,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def con_guardia(valor):
    if valor:
        os.environ[GUARDIA_ENV] = valor
    else:
        os.environ.pop(GUARDIA_ENV, None)


# ================================================================
# EL BANCO: MAFFEO CON PUJA VIVA, Y DOS SIN ELLA
# ================================================================

MAFFEO = 10030

BOYOMO = 33694

CHUST = 61061

# Lo que devuelve `build_bid_exposure` con la puja de Maffeo
# puesta. Mismos campos que trae de verdad.
EXPOSICION = {
    "available": True,
    "committed_total": 1_664_350,
    "operation_count": 1,
    "operations": [
        {
            "offer_id": 399977192,
            "amount": 1_664_350,
            "player_ids": [MAFFEO],
            "status": "waiting",
            "created": 1789733768,
        }
    ],
}

SPECULATION = {"bid_exposure": EXPOSICION}

# Los candidatos que llegan al carril, con la forma real.
CANDIDATOS = [
    {"player_id": MAFFEO, "name": "Maffeo", "bid": 1_664_350},
    {"player_id": BOYOMO, "name": "Boyomo", "bid": 1_817_297},
    {"player_id": CHUST, "name": "Chust", "bid": 1_871_032},
]


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. La lista de pujas vivas no llega vacia")

check(
    "hay una puja viva en el banco",
    len(EXPOSICION["operations"]) == 1,
    f"(n={len(EXPOSICION['operations'])})",
)

check(
    "y es por un jugador que esta entre los candidatos",
    MAFFEO in {c["player_id"] for c in CANDIDATOS},
)

sin_pujas = lo_que_ya_esta_puesto(
    {"bid_exposure": {
        "available": True, "operations": [], "operation_count": 0,
    }}
)

check(
    "sin pujas vivas la guardia no frena a nadie",
    sin_pujas["available"] is True
    and sin_pujas["cuantos"] == 0,
    f"({sin_pujas})",
)


# ================================================================
# 1. DOCTRINA 84: LA FUENTE DEL CONJUNTO YA EXISTIA
# ================================================================

print()
print("1. El conjunto sale de `players_with_live_bid()`")

ocupados = players_with_live_bid(SPECULATION)

check(
    "`players_with_live_bid` ve a Maffeo",
    MAFFEO in ocupados,
    f"({ocupados})",
)

puestas = lo_que_ya_esta_puesto(SPECULATION)

check(
    "y la guardia ve exactamente los mismos",
    set(puestas["por_jugador"]) == set(ocupados),
    f"({set(puestas['por_jugador'])} vs {ocupados})",
)

check(
    "con el detalle que hace falta para explicar el freno",
    puestas["por_jugador"][MAFFEO]["offer_id"] == 399977192,
    f"({puestas['por_jugador'].get(MAFFEO)})",
)


# ================================================================
# 2. UNA SEGUNDA VUELTA NO ESCRIBE OTRA
# ================================================================

print()
print("2. Con la puja viva, la segunda vuelta no la repite")

filtrado = filtrar_los_repetidos(CANDIDATOS, SPECULATION)

escribibles = [c["name"] for c in filtrado["escribibles"]]

frenados = [f["name"] for f in filtrado["frenados"]]

print(f"       escribibles: {escribibles}")
print(f"       frenados   : {frenados}")

check(
    "Maffeo queda frenado",
    frenados == ["Maffeo"],
    f"({frenados})",
)

check(
    "y no aparece entre los escribibles",
    "Maffeo" not in escribibles,
)

check(
    "se frena UNA, no todas",
    len(filtrado["frenados"]) == 1,
    f"({len(filtrado['frenados'])})",
)


# ================================================================
# 3. EL HUECO NO SE PIERDE
# ================================================================

print()
print("3. El hueco que libera el repetido se lo queda otro")

check(
    "quedan dos candidatos escribibles",
    len(filtrado["escribibles"]) == 2,
    f"({escribibles})",
)

check(
    "y son los que no tenian puja viva",
    set(escribibles) == {"Boyomo", "Chust"},
    f"({escribibles})",
)


# ================================================================
# 4. SIN PODER MIRAR, NO SE ESCRIBE NADA
# ================================================================

print()
print("4. Un fallo de lectura no es via libre")

CIEGO = {
    "bid_exposure": {
        "available": False,
        "operations": [],
        "reason": "No se pudo leer el tablon de ofertas.",
    }
}

a_ciegas = filtrar_los_repetidos(CANDIDATOS, CIEGO)

check(
    "sin exposicion disponible no hay nada escribible",
    a_ciegas["escribibles"] == [],
    f"({a_ciegas['escribibles']})",
)

check(
    "los tres salen frenados",
    len(a_ciegas["frenados"]) == 3,
    f"({len(a_ciegas['frenados'])})",
)

check(
    "con el motivo NO_SE_SABE, distinto de YA_ESTA_PUESTA",
    all(f["motivo"] == "NO_SE_SABE" for f in a_ciegas["frenados"]),
    f"({[f['motivo'] for f in a_ciegas['frenados']]})",
)

check(
    "y `available` en False, que es lo que para al que llama",
    a_ciegas["available"] is False,
)

# Y sin `bid_exposure` ninguno, lo mismo.
sin_nada = filtrar_los_repetidos(CANDIDATOS, {})

check(
    "sin `bid_exposure` tampoco se escribe",
    sin_nada["available"] is False
    and sin_nada["escribibles"] == [],
)


# ================================================================
# 5. APAGADA, EL COMPORTAMIENTO ES EL DE SIEMPRE
# ================================================================

print()
print("5. El interruptor")

con_guardia(None)

check(
    "apagada por defecto",
    guardia_activa() is False,
)

con_guardia("1")

try:
    check(
        "y se enciende con BORDALAS_NO_REPETIR_LA_ESCRITURA",
        guardia_activa() is True,
    )

finally:
    con_guardia(None)


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
