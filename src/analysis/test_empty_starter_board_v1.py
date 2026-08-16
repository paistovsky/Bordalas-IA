"""
Un tablero de titularidad vacio no puede pasar por bueno.

EL CASO REAL

    16/08/2026, noche. El dashboard publicado pintaba "sin dato"
    en los once jugadores. En el PC de casa, el mismo codigo y el
    mismo ciclo sacaban 96 %.

    Lo que decia la telemetria del dashboard publicado:

        "starter_board_players":    0
        "starter_cache_status":     "HIT"
        "starter_source_error":     null
        "starter_board_matchday":   2

    HIT, sin error, jornada correcta. Todo verde. Y cero
    jugadores.

QUE HABIA PASADO

    Un snapshot llego sin plantilla. `build_roster_records`
    devolvio lista vacia, el bucle no produjo ninguna fila, y el
    tablero se escribio igual: un fichero legitimo con
    `players: []`.

    A partir de ahi `cached_board_is_fresh` lo daba por bueno
    durante dos horas, porque solo miraba jornada y antiguedad.
    Cada generacion posterior lo servia como HIT aunque el
    snapshot nuevo trajera la plantilla entera.

    Un fallo que se disfraza de exito envenena todo lo que viene
    detras. Y este ademas apagaba la regla del once: sin
    pronostico, ninguna mejora del XI puede aprobarse.

LAS DOS MITADES DEL ARREGLO

    1. No dar por fresco un tablero sin jugadores.
    2. No escribirlo en primer lugar cuando el snapshot llega
       sin plantilla.

    Hacen falta las dos: la primera evita seguir sirviendo el
    veneno, la segunda evita fabricarlo.
"""

import sys

sys.path.insert(0, ".")

from datetime import datetime, timedelta, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

import shutil  # noqa: E402
import tempfile  # noqa: E402

from src.intelligence import (  # noqa: E402
    multisource_starter_v1124 as board_mod,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


AHORA = datetime(2026, 8, 16, 21, 0, tzinfo=timezone.utc)


def tablero(players, *, matchday=2, edad_minutos=5):
    return {
        "version": "V11.2.4",
        "updated_at": (
            AHORA - timedelta(minutes=edad_minutos)
        ).isoformat(),
        "matchday": matchday,
        "players": players,
    }


JUGADOR = {
    "player_id": 5771,
    "player_name": "Yeray",
    "starter_probability": 92.2,
    "consensus": "STARTER",
    "source_coverage": 2,
}


# ================================================================
# 1. LA CACHE
# ================================================================


print()
print("1. Un tablero vacío no es una caché válida")
print("-" * 60)


check(
    "el tablero real del 16/08 -0 jugadores, jornada 2- se rechaza",
    board_mod.cached_board_is_fresh(
        tablero([]),
        matchday=2,
        seconds_to_deadline=335_482,
        now=AHORA,
    )
    is False,
)

check(
    "con jugadores y reciente, sí vale",
    board_mod.cached_board_is_fresh(
        tablero([JUGADOR]),
        matchday=2,
        seconds_to_deadline=335_482,
        now=AHORA,
    )
    is True,
)

check(
    "sigue rechazando por jornada distinta",
    board_mod.cached_board_is_fresh(
        tablero([JUGADOR], matchday=1),
        matchday=2,
        seconds_to_deadline=335_482,
        now=AHORA,
    )
    is False,
)

check(
    "y por antigüedad",
    board_mod.cached_board_is_fresh(
        tablero([JUGADOR], edad_minutos=60 * 5),
        matchday=2,
        seconds_to_deadline=335_482,
        now=AHORA,
    )
    is False,
)

check(
    "sin tablero, tampoco",
    board_mod.cached_board_is_fresh(
        None,
        matchday=2,
        seconds_to_deadline=335_482,
        now=AHORA,
    )
    is False,
)

check(
    "la clave 'players' ausente cuenta como vacío",
    board_mod.cached_board_is_fresh(
        {"matchday": 2, "updated_at": AHORA.isoformat()},
        matchday=2,
        seconds_to_deadline=335_482,
        now=AHORA,
    )
    is False,
)


# ================================================================
# 2. NO FABRICAR EL VENENO
# ================================================================


print()
print("2. Sin plantilla no se escribe el fichero")
print("-" * 60)


directorio = Path(tempfile.mkdtemp())
original = board_mod.OUTPUT_FILE
board_mod.OUTPUT_FILE = directorio / "starter.json"

try:

    # Snapshot roto: sin `my_team`.
    resultado = board_mod.build_multisource_board(
        snapshot={"catalog": {"data": {"players": {}, "teams": {}}}},
        matchday=2,
        seconds_to_deadline=335_482,
    )

    check(
        "no se crea ningún fichero de tablero",
        not board_mod.OUTPUT_FILE.exists(),
        str(list(directorio.iterdir())),
    )

    check(
        "el estado NO es HIT: dice que no hay plantilla",
        (resultado.get("cache") or {}).get("status")
        in {"NO_ROSTER", "STALE_FALLBACK"},
        str((resultado.get("cache") or {}).get("status")),
    )

    check(
        "y trae un motivo, no un error nulo",
        bool((resultado.get("cache") or {}).get("error")),
        str((resultado.get("cache") or {}).get("error")),
    )

    check(
        "el motivo nombra la causa real",
        "plantilla"
        in str((resultado.get("cache") or {}).get("error", "")),
    )

    # Con un tablero anterior bueno en disco, se conserva.
    #
    # Se escribe CADUCADO a proposito: si estuviera fresco se
    # serviria como HIT sin llegar a mirar la plantilla, que es
    # el comportamiento correcto y no lo que se quiere probar
    # aqui. Lo que hay que probar es el caso feo: la cache ya no
    # vale, el snapshot viene roto, y aun asi no se pisa lo
    # ultimo bueno que teniamos.
    import json

    board_mod.OUTPUT_FILE.write_text(
        json.dumps(
            tablero([JUGADOR], edad_minutos=60 * 24)
        ),
        encoding="utf-8",
    )

    con_cache = board_mod.build_multisource_board(
        snapshot={"my_team": []},
        matchday=2,
        seconds_to_deadline=335_482,
    )

    check(
        "el tablero bueno anterior no se pisa",
        len(con_cache.get("players") or []) == 1,
        str(len(con_cache.get("players") or [])),
    )

    check(
        "y se sirve marcado como respaldo, no como HIT",
        (con_cache.get("cache") or {}).get("status")
        == "STALE_FALLBACK",
        str((con_cache.get("cache") or {}).get("status")),
    )

    check(
        "el fichero en disco sigue teniendo al jugador",
        len(
            json.loads(
                board_mod.OUTPUT_FILE.read_text(encoding="utf-8")
            )["players"]
        )
        == 1,
    )

finally:
    board_mod.OUTPUT_FILE = original
    shutil.rmtree(directorio, ignore_errors=True)


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
