"""
La cola del que se queda: con que unidad se ordenan los candidatos
cuando las escalas son distintas.

POR QUE EXISTE (26/09/2026)

    Con 0 fichas libres y 2.208.580 en el bolsillo, el problema no es
    filtrar: es elegir uno. Eso pide un orden, no un liston.

    Y el orden no puede ser el porcentaje crudo de cada via, porque
    cada via cuenta una cosa distinta:

        mejora del once   los puntos de mas contra el titular mas flojo
                          DE SU POSICION (acquisition_valuation.py:444)
        ficha vacia       TODOS los puntos del candidato, como si jugara
                          (acquisition_valuation.py:640, replaced_points=0)

    Y en esta liga SOLO PUNTUAN ONCE: `lineupReserves: false`, sin
    cambios automaticos (DOCTRINA.md:593). Un fichaje que se queda en el
    banquillo nos suma cero, lo diga el porcentaje que lo diga. Medido
    el 23/09: los cinco de ficha vacia del Computer, publicados entre el
    98 % y el 128 %, no entraban en nuestro once.

LA UNIDAD COMUN

    Euros de premios que el once cobraria de mas, por euro de caja neta:

        premios   = mejora del once REHECHO (puntos de temporada)
                    x (jornadas que quedan / jornadas de la temporada)
                    x lo que paga la liga por punto
        caja neta = precio - lo que se recupera vendiendo para hacer sitio

    · La mejora es la del once rehecho entero, con las siete formaciones
      de `lineup_engine` y su busqueda de produccion: si el candidato no
      entra, vale cero; si entra, vale lo que suma el once nuevo contra
      el de hoy. Las dos escalas se reducen a esto: la ficha vacia es la
      que no obliga a vender, la mejora del once es la que si.
    · Los euros son los de la liga (`caja_de_la_liga.EUROS_POR_PUNTO`):
      es lo que un punto del once nos paga de verdad.
    · Se divide por la caja NETA porque es lo que se inmoviliza: el
      jugador sigue siendo nuestro y el que sale se cobra.

    NO cuenta lo que suba o baje el precio del jugador. Eso es el precio
    de reserva, que se mide aparte.

NO DECIDE NADA

    Funciones puras. Nadie las llama para pujar. Ni disco, ni red, ni
    reloj, ni entorno. Nunca lanza.
"""

from __future__ import annotations


from src.analysis.caja_de_la_liga import EUROS_POR_PUNTO      # noqa: E402
from src.analysis.lineup_engine import (                      # noqa: E402
    FORMATIONS,
    search_best_lineup_for_formation,
)


JORNADAS_DE_LA_TEMPORADA = 38


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def el_mejor_once(plantilla: list) -> dict:
    """
    El mejor once por puntos entre las siete formaciones, con la
    busqueda de produccion. `plantilla`: `[{id, pos, pts}]`.
    """

    preparados = [
        {
            "id": j["id"],
            "lineup_eligible": True,
            "automatic_lineup": True,
            "eligible_positions": [safe_int(j["pos"])],
            "lineup_score": float(j["pts"]),
        }
        for j in plantilla
    ]

    mejores = []
    for nombre, formacion in FORMATIONS.items():
        r = search_best_lineup_for_formation(preparados, formacion)
        mejores.append(
            (len(r["selected"]), r["score"], nombre,
             frozenset(p["id"] for p in r["selected"]))
        )

    mejores.sort(key=lambda x: (x[0], x[1]), reverse=True)
    lleno, puntos, nombre, ids = mejores[0]

    return {"puntos": puntos, "formacion": nombre, "ids": ids, "lleno": lleno}


def mejora_del_once(plantilla: list, candidato: dict, base: dict | None = None) -> dict:
    """
    Cuanto suma el once rehecho con el candidato dentro.

    `candidato`: `{id, pos, pts}`. Devuelve la mejora en puntos de
    temporada, la formacion nueva, si entra y quien sale del once.
    """

    try:
        antes = base or el_mejor_once(plantilla)
        despues = el_mejor_once(list(plantilla) + [candidato])
        entra = candidato["id"] in despues["ids"]
        return {
            "mejora": round(despues["puntos"] - antes["puntos"]) if entra else 0,
            "entra": entra,
            "formacion": despues["formacion"],
            "formacion_antes": antes["formacion"],
            "salen": sorted(antes["ids"] - despues["ids"]),
        }
    except Exception as error:                      # noqa: BLE001
        return {
            "mejora": 0, "entra": False, "formacion": None,
            "formacion_antes": None, "salen": [],
            "reason": f"{type(error).__name__}: {error}",
        }


def unidad(
    mejora_puntos,
    precio,
    jornadas_que_quedan,
    recuperado=0,
    euros_por_punto=EUROS_POR_PUNTO,
    jornadas_de_la_temporada=JORNADAS_DE_LA_TEMPORADA,
) -> dict:
    """Premios de mas por euro de caja neta. Forma fija. Nunca lanza."""

    try:
        premios = int(
            max(0, float(mejora_puntos))
            * float(jornadas_que_quedan) / float(jornadas_de_la_temporada)
            * float(euros_por_punto)
        )
        caja = max(0, safe_int(precio) - safe_int(recuperado))
        return {
            "premios": premios,
            "caja_neta": caja,
            "rendimiento": round(premios / caja, 4) if caja else None,
        }
    except Exception:                               # noqa: BLE001
        return {"premios": 0, "caja_neta": 0, "rendimiento": None}


def ordenar(candidatos: list) -> list:
    """
    Por rendimiento en la unidad comun, de mayor a menor. Empate: la
    mayor mejora del once, y despues el mas barato. Los que no suman al
    once (rendimiento 0 o None) al final.
    """

    return sorted(
        list(candidatos or []),
        key=lambda c: (
            -(c.get("rendimiento") or 0.0),
            -safe_int(c.get("mejora")),
            safe_int(c.get("precio")),
        ),
    )
