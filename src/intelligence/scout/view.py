"""
El ojeador, puesto donde se pueda leer.

DOS COSAS

    1. El bloque del panel: que fuentes entraron, cuantos
       jugadores trajo cada una, cuantos se quedaron sin
       emparejar y por que, y el libro de acierto.

    2. La columna de la tabla de MERCADO: el veredicto del
       ojeador AL LADO del de Pepe, fila a fila.

POR QUE AL LADO Y NO EN OTRA PANTALLA

    Porque lo que hay que ver es la diferencia. Pepe le da a
    Bardeli -que subio un 6 % ayer-, a Andre Almeida -que subio un
    17 %- y a Nico Guillen -que bajo un 2 %- exactamente el mismo
    0,17 % de rendimiento esperado. Tres comportamientos
    distintos, un solo numero.

    Esa es toda la historia, y solo se ve con las dos columnas
    pegadas.

FASE OBSERVADOR

    Se anota sobre COPIAS de las filas. El tablero que decide
    sigue siendo bit a bit el mismo.
"""

from __future__ import annotations

import re


# Lo que Pepe dice que rinde, dentro de su propia explicacion.
#
# Se saca del texto a proposito y solo para pintar: el motor no
# publica ese porcentaje como campo, y añadirselo seria tocar la
# ruta que decide para una columna de pantalla. Si algun dia deja
# de encontrarlo, la columna dice "—" y no se inventa nada.
RENDIMIENTO = re.compile(r"rinde un ([\d]+[.,]?[\d]*)\s*%")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def pepe_yield_percent(fila: dict):
    """El rendimiento que Pepe le asigna, o None si no lo dice."""

    encontrado = RENDIMIENTO.search(str(fila.get("reason") or ""))

    if not encontrado:
        return None

    try:
        return float(encontrado.group(1).replace(",", "."))

    except ValueError:
        return None


def _verdict(ficha: dict | None) -> dict | None:
    """El veredicto del ojeador sobre un jugador, resumido."""

    if not ficha:
        return None

    consenso = ficha.get("consensus") or {}
    demanda = ficha.get("demand") or {}

    return {
        "direction": consenso.get("direction"),
        "agreement": consenso.get("agreement"),
        "sources_agreeing": consenso.get("sources_agreeing"),
        "sources_total": consenso.get("sources_total"),
        "mean_magnitude_percent": consenso.get(
            "mean_magnitude_percent"
        ),
        "note": consenso.get("note"),

        # El pulso de demanda, que es lo unico que mira hacia
        # delante. Viaja aparte para que no se lea como parte del
        # consenso de lo ya ocurrido.
        "demand_direction": demanda.get("direction"),
        "demand_pressure": demanda.get("pressure_points"),

        "trend_days": ficha.get("trend_days"),
        "acceleration": ficha.get("acceleration"),
        "deceleration": ficha.get("deceleration"),

        # Como se identifico al jugador en cada fuente. Es lo que
        # permite auditar un emparejamiento raro sin volver a
        # bajar la pagina.
        "matches": ficha.get("matches") or [],
    }


def annotate_targets(rows: list | None, report: dict | None) -> list:
    """
    Cada fila del tablero, con el veredicto del ojeador al lado.

    Devuelve filas NUEVAS. No toca las que le pasan.
    """

    jugadores = (report or {}).get("players") or {}

    salida = []

    for fila in (rows or []):

        if not isinstance(fila, dict):
            continue

        nueva = dict(fila)

        nueva["scout"] = _verdict(
            jugadores.get(str(safe_int(fila.get("id"))))
        )

        # Lo que dice Pepe, en el mismo sitio, para que la
        # pantalla pueda poner los dos numeros juntos sin volver
        # a leer prosa.
        nueva["pepe_yield_percent"] = pepe_yield_percent(fila)

        salida.append(nueva)

    return salida


def build_scout_block(
    report: dict | None,
    accuracy: dict | None = None,
    rows: list | None = None,
) -> dict:
    """
    El bloque entero para la Sala de Operaciones. Nunca lanza.
    """

    try:
        informe = report or {}

        jugadores = informe.get("players") or {}

        if not jugadores:
            return {
                "available": False,
                "observer_only": True,
                "reason": (
                    (informe.get("cache") or {}).get("error")
                    or "Todavia no hay informe del ojeador."
                ),
                "sources": informe.get("sources") or {},
                "unmatched": [],
                "accuracy": accuracy or {"available": False},
            }

        # Cuantos de cada tipo de acuerdo. Es el numero que
        # contesta a "¿se ponen de acuerdo estas webs?".
        acuerdos = {}

        for ficha in jugadores.values():
            clave = (ficha.get("consensus") or {}).get(
                "agreement", "NONE"
            )
            acuerdos[clave] = acuerdos.get(clave, 0) + 1

        # Los que mas se mueven, que es lo que se mira primero.
        destacados = sorted(
            (
                {
                    "player_id": pid,
                    "player_name": ficha.get("player_name"),
                    "market_price": ficha.get("market_price"),
                    "direction": (ficha.get("consensus") or {}).get(
                        "direction"
                    ),
                    "agreement": (ficha.get("consensus") or {}).get(
                        "agreement"
                    ),
                    "sources_agreeing": (
                        ficha.get("consensus") or {}
                    ).get("sources_agreeing"),
                    "sources_total": (
                        ficha.get("consensus") or {}
                    ).get("sources_total"),
                    "magnitude_percent": (
                        ficha.get("consensus") or {}
                    ).get("mean_magnitude_percent"),
                    "demand_direction": (
                        ficha.get("demand") or {}
                    ).get("direction"),
                    "demand_pressure": (
                        ficha.get("demand") or {}
                    ).get("pressure_points"),
                    "trend_days": ficha.get("trend_days"),
                }
                for pid, ficha in jugadores.items()
                if (ficha.get("consensus") or {}).get(
                    "mean_magnitude_percent"
                )
                is not None
            ),
            key=lambda item: -abs(item["magnitude_percent"] or 0),
        )[:15]

        # DONDE SE CONTRADICEN LAS FUENTES
        #
        #     Dos formas de contradecirse, y la segunda es la
        #     interesante:
        #
        #     1. Unas dicen UP y otras DOWN (`SPLIT`).
        #     2. El precio subio pero la gente esta vendiendo, o
        #        al reves. El movimiento ya ocurrido y la demanda
        #        de ahora apuntan a lados distintos.
        contradicciones = [
            {
                "player_id": pid,
                "player_name": ficha.get("player_name"),
                "price_direction": (
                    ficha.get("consensus") or {}
                ).get("direction"),
                "demand_direction": (
                    ficha.get("demand") or {}
                ).get("direction"),
                "demand_pressure": (
                    ficha.get("demand") or {}
                ).get("pressure_points"),
                "agreement": (ficha.get("consensus") or {}).get(
                    "agreement"
                ),
                "note": (
                    "Las fuentes no se ponen de acuerdo."
                    if (ficha.get("consensus") or {}).get("agreement")
                    == "SPLIT"
                    else (
                        "El precio se movio en un sentido y la "
                        "demanda de las ultimas 24 h apunta al otro."
                    )
                ),
            }
            for pid, ficha in jugadores.items()
            if (
                (ficha.get("consensus") or {}).get("agreement")
                == "SPLIT"
            )
            or (
                (ficha.get("demand") or {}).get("direction")
                and (ficha.get("consensus") or {}).get("direction")
                and (ficha.get("demand") or {}).get("direction")
                != (ficha.get("consensus") or {}).get("direction")
            )
        ]

        return {
            "available": True,
            "observer_only": True,
            "reason": None,

            "version": informe.get("version"),
            "generated_at": informe.get("generated_at"),
            "matchday": informe.get("matchday"),
            "cache": informe.get("cache") or {},

            # Lo que NO es esto, escrito donde se lee.
            "caveat": informe.get("caveat"),

            "sources": informe.get("sources") or {},
            "sources_ok": informe.get("sources_ok"),
            "sources_total": informe.get("sources_total"),

            "players_count": informe.get("players_count"),
            "agreement_counts": acuerdos,

            "highlights": destacados,

            "disagreements": contradicciones[:15],
            "disagreements_count": len(contradicciones),

            # Los que no se pudieron identificar, con su motivo.
            # Se publican a proposito: un emparejamiento que no se
            # hizo y no se cuenta es un agujero invisible.
            "unmatched": (informe.get("unmatched") or [])[:40],
            "unmatched_count": informe.get("unmatched_count"),

            "accuracy": accuracy or {"available": False},

            # Cuantas filas del tablero llevan veredicto. Si son
            # pocas, el ojeador esta mirando a otro sitio que la
            # tabla que decide.
            "targets_with_verdict": sum(
                1
                for fila in (rows or [])
                if isinstance(fila, dict) and fila.get("scout")
            ),
            "targets_total": len(rows or []),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo construir el bloque del ojeador: "
                f"{type(error).__name__}: {error}"
            ),
            "sources": {},
            "unmatched": [],
            "accuracy": {"available": False},
        }
