"""
Que lo que se ve sea lo que se ejecuta.

EL CASO REAL

    16/08/2026. El dashboard proponia cuatro pujas -Yusi,
    Castrin, Arriaga, Cabrera- y en Biwenger habia una sola puja
    viva, por Iker Munoz, que no estaba en la lista.

    Eran dos motores. El tablero de adquisicion -valoracion en
    euros, participacion medida de cada rival, barreras de
    rendimiento- pintaba el dashboard y no tocaba el ciclo. El
    ciclo ejecutaba `speculation.executable_buys[0]`, la lista
    del scoring antiguo.

    Un analista escribiendo informes y un becario comprando por
    su cuenta sin leerlos.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.decision_orchestrator import (  # noqa: E402
    best_acquisition_target,
    players_with_live_bid,
)

fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def objetivo(nombre, bid, ev, decision="BID", **extra):
    return {
        "id": abs(hash(nombre)) % 100000,
        "name": nombre,
        "bid": bid,
        "expected_value": ev,
        "decision": decision,
        "market_price": bid - 1,
        **extra,
    }


TABLERO = {
    "available": True,
    "market_size": 20,
    "biddable": 4,
    "targets": [
        objetivo("Yusi Enríquez", 504_000, 2_345_195),
        objetivo("Andrés Castrín", 1_236_001, 2_027_008),
        objetivo("Kervin Arriaga", 1_386_001, 933_591),
        objetivo("Cabrera", 4_389_001, 420_173),
        objetivo("Mbappé", 0, 0, decision="NO_COMPENSA"),
        objetivo("Soler", 0, 0, decision="RENDIMIENTO_INSUFICIENTE"),
    ],
}


# ================================================================
# 1. QUIEN MANDA
# ================================================================


print()
print("1. El objetivo sale del tablero que se ve")
print("-" * 60)

mejor = best_acquisition_target(TABLERO)

check(
    "elige el de mayor valor esperado",
    mejor["name"] == "Yusi Enríquez",
    str(mejor and mejor["name"]),
)

check(
    "es la primera fila con PUJAR del dashboard",
    mejor["expected_value"] == 2_345_195,
)

check(
    "no elige a los que no compensan",
    all(
        t["decision"] == "BID"
        for t in TABLERO["targets"]
        if t["name"] == mejor["name"]
    ),
)


# ================================================================
# 2. CUANDO NO HAY TABLERO NO SE INVENTA
# ================================================================


print()
print("2. Sin tablero, no se fuerza nada")
print("-" * 60)

check(
    "sin tablero devuelve None",
    best_acquisition_target(None) is None,
)

check(
    "un tablero no disponible devuelve None",
    best_acquisition_target(
        {"available": False, "targets": [objetivo("X", 1, 1)]}
    )
    is None,
)

check(
    "un tablero sin pujables devuelve None",
    best_acquisition_target(
        {
            "available": True,
            "targets": [objetivo("X", 0, 0, decision="NO_COMPENSA")],
        }
    )
    is None,
)

check(
    "una puja de cero no cuenta aunque diga BID",
    best_acquisition_target(
        {"available": True, "targets": [objetivo("X", 0, 999)]}
    )
    is None,
)

check(
    "aguanta un tablero roto",
    best_acquisition_target({"available": True}) is None,
)


# ================================================================
# 3. DESEMPATE
# ================================================================


print()
print("3. A igualdad de valor esperado, la puja menor")
print("-" * 60)

empate = best_acquisition_target(
    {
        "available": True,
        "targets": [
            objetivo("Caro", 4_000_000, 500_000),
            objetivo("Barato", 400_000, 500_000),
        ],
    }
)

check(
    "con el mismo valor esperado gana el que inmoviliza menos",
    empate["name"] == "Barato",
    str(empate["name"]),
)


# ================================================================
# 4. NO SE REPITE LO QUE YA ESTA PUJADO
# ================================================================


print()
print("4. Con puja viva, el ciclo baja al siguiente")
print("-" * 60)

# 16/08/2026 19:58: Pepe pujo por Yusi. Una puja no se resuelve
# hasta el reset, asi que Yusi sigue en el mercado y sigue siendo
# el de mayor valor esperado. Sin filtro, los siete ciclos de esa
# noche lo habrian elegido otra vez para no escribir nada, y
# Castrin, Arriaga y Cabrera se habrian quedado sin pujar.
EXPOSICION = {
    "bid_exposure": {
        "operations": [
            {
                "offer_id": 1,
                "amount": 504_000,
                "player_ids": [
                    TABLERO["targets"][0]["id"]
                ],
            }
        ]
    }
}

ocupados = players_with_live_bid(EXPOSICION)

check(
    "detecta el jugador con puja viva",
    TABLERO["targets"][0]["id"] in ocupados,
)

siguiente = best_acquisition_target(
    TABLERO,
    exclude_ids=ocupados,
)

check(
    "no repite a Yusi",
    siguiente["name"] != "Yusi Enríquez",
)

check(
    "y baja al segundo de la lista",
    siguiente["name"] == "Andrés Castrín",
    str(siguiente["name"]),
)

check(
    "sin exposicion no aparta a nadie",
    players_with_live_bid({}) == set()
    and players_with_live_bid(None) == set(),
)

check(
    "con todos pujados devuelve None en vez de repetir",
    best_acquisition_target(
        TABLERO,
        exclude_ids={
            t["id"] for t in TABLERO["targets"]
        },
    )
    is None,
)


# ================================================================
# 5. EL CABLEADO EXISTE DE VERDAD
# ================================================================


print()
print("5. Los cuatro puntos están conectados")
print("-" * 60)

import inspect  # noqa: E402

from src.analysis import decision_orchestrator as orch  # noqa: E402
from src.actions import autopilot_executor as ex  # noqa: E402
import src.autopilot as ap  # noqa: E402

fuente_orch = inspect.getsource(orch.build_global_decision)

check(
    "el orchestrator acepta el tablero",
    "acquisition_board" in inspect.signature(
        orch.build_global_decision
    ).parameters,
)

check(
    "y lo usa para elegir el objetivo",
    "best_acquisition_target" in fuente_orch,
)

check(
    "y marca de donde viene el objetivo",
    "ACQUISITION_BOARD" in fuente_orch,
)

check(
    "autopilot construye el tablero antes de decidir",
    hasattr(ap, "build_cycle_acquisition_board"),
)

check(
    "y comparte la inteligencia rival en vez de pedirla dos veces",
    hasattr(ap, "load_rival_intelligence")
    and hasattr(ap, "reset_rival_intelligence_cache"),
)

fuente_ex = inspect.getsource(ex)

check(
    "el executor ya no exige la lista del scoring antiguo",
    "from_acquisition" in fuente_ex,
)

check(
    "y respeta la puja recomendada",
    "recommended_bid" in fuente_ex,
)

check(
    "sin dejar de respetar el suelo del vendedor",
    "listed_price" in fuente_ex,
)


print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
