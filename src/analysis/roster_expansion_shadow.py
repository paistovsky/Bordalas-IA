"""
Que ficharia Pepe si pudiera fichar para llenar un hueco.

POR QUE EXISTE

    `acquisition_valuation.py:352-358` compara cada candidato con
    UN jugador: el peor titular de su posicion. No existe la
    operacion "fichar y punto".

    Si el candidato no le gana a ese titular, la fila cae a
    `intent = SPECULATION` y se la juzga con el liston de la
    reventa. En la foto del 04/09 eso son 19 de 22 candidatos
    vetados por la regla del once, y los 22 acaban como
    especulacion.

    Mientras tanto Pepe tiene 14 fichas y el mayor de la liga
    tiene 17. Hay sitio libre y ninguna via para usarlo.

FASE OBSERVADOR

    Esto NO ficha, NO puja y NO cambia ninguna valoracion.
    `acquisition_valuation.py` no se toca. Es una lista escrita
    al margen: "con N fichas libres, estos serian los
    candidatos".

    Ningun motor importa este modulo, y hay guardia que lo
    comprueba.

CUANTAS FICHAS LIBRES HAY, DE VERDAD

    No se sabe. No hay constante de tope de plantilla en el
    codigo y la auditoria del 04/09 lo dejo anotado como no
    comprobado.

    Asi que no se inventa: se cuenta contra la plantilla MAS
    GRANDE que se ve en la liga -17, de Pollo17-, y el resultado
    se publica como lo que es, una COTA INFERIOR. Si Biwenger
    permite 18, hay una ficha mas de la que aqui se dice; nunca
    menos.

    Es la unica forma honesta de contestar sin abrir Biwenger.

POR QUE ORDENA POR VALOR DE TEMPORADA

    Porque es la pregunta que se esta haciendo. Llenar un hueco
    de plantilla es una operacion a meses: lo que valga la
    reventa el jueves no dice nada de si conviene ocupar una
    ficha con ese jugador de aqui a la jornada 38.
"""

from __future__ import annotations


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


# Las decisiones de `as_xi` que significan "no le gana al peor
# titular de su posicion". Son 16 de los 22 candidatos de la foto
# del 04/09.
XI_VETOES = frozenset(
    {
        "NO_MEJORA",
        "NO_MEJORA_JERARQUIA",
        "NO_MEJORA_TITULARIDAD",
        "PIERDE_TITULARIDAD",
        "SIN_PRONOSTICO",
    }
)

# El `intent` que significa "entra al once". Cualquier otro
# significa que hoy no se ficha para jugar.
XI_INTENT = "XI_UPGRADE"


def blocked_reason(fila: dict) -> tuple[str, str] | None:
    """
    Por que este candidato NO entra hoy como fichaje del once, si
    es que no entra.

    HAY DOS PUERTAS, NO UNA (05/09/2026)

        La primera version de esto filtraba solo por el veto de
        `as_xi`, y se dejaba fuera justo los casos que mas
        importan.

        Exposito, Odysseas y Natan NO estan vetados: la via del
        once les da valor -"Suma 81 puntos" en el caso de
        Exposito-. Lo que pasa es que `acquisition_valuation.py`
        elige el `intent` por euros, `max(opciones, key=value)`,
        gana la reventa, y entonces a un fichaje se le exige
        rendimiento de especulacion: "rinde un 0,59 % y se exige
        al menos un 3 %".

        Son las dos puertas por las que se cae un fichaje, y una
        lista de "que ficharia si pudiera" que solo mire la
        primera se deja fuera al mejor candidato del tablero.
    """

    veto = fila.get("xi_decision")

    if veto in XI_VETOES:
        return (veto, fila.get("xi_reason") or "")

    if fila.get("intent") != XI_INTENT:
        return (
            "INTENT_POR_EUROS",
            (
                "La via del once le da valor, pero el `intent` se "
                "elige por euros y gana la reventa: entonces se le "
                "exige rendimiento de especulacion. "
                + str(fila.get("reason") or "")
            ).strip(),
        )

    return None


def count_free_slots(ledger_audit: dict | None) -> dict:
    """
    Cuantas fichas libres hay, con la honestidad por delante.

    Se mide contra la plantilla mas grande de la liga porque el
    tope real de Biwenger no esta en el codigo ni comprobado.
    """

    managers = [
        m
        for m in ((ledger_audit or {}).get("by_manager") or [])
        if isinstance(m, dict) and safe_int(m.get("roster_size")) > 0
    ]

    if not managers:
        return {
            "known": False,
            "our_roster_size": None,
            "largest_roster_in_league": None,
            "free_slots": None,
            "reason": (
                "El ledger de rivales no trae el tamaño de ninguna "
                "plantilla: sin eso no se puede decir cuanto sitio "
                "libre hay."
            ),
        }

    nosotros = next((m for m in managers if m.get("is_us")), None)

    if nosotros is None:
        return {
            "known": False,
            "our_roster_size": None,
            "largest_roster_in_league": max(
                safe_int(m.get("roster_size")) for m in managers
            ),
            "free_slots": None,
            "reason": (
                "El ledger no dice cual de los managers somos "
                "nosotros: sin eso no hay huecos que contar."
            ),
        }

    nuestras = safe_int(nosotros.get("roster_size"))
    mayor = max(safe_int(m.get("roster_size")) for m in managers)

    return {
        "known": True,
        "our_roster_size": nuestras,
        "largest_roster_in_league": mayor,
        "free_slots": max(mayor - nuestras, 0),

        # Que quede escrito en el propio JSON: esto es un suelo,
        # no el tope de Biwenger.
        "is_lower_bound": True,
        "reason": (
            f"Tenemos {nuestras} fichas y la plantilla mas grande de "
            f"la liga tiene {mayor}. El tope real de Biwenger no "
            f"esta en el codigo ni comprobado, asi que "
            f"{max(mayor - nuestras, 0)} es una cota INFERIOR: si "
            f"Biwenger permite mas, hay mas sitio del que dice esto, "
            f"nunca menos."
        ),
    }


def build_roster_expansion_shadow(
    season_horizon: dict | None,
    ledger_audit: dict | None,
    acquisition_budget: dict | None = None,
) -> dict:
    """
    La lista de "si hubiera hueco". Nunca lanza.

    FASE OBSERVADOR: se calcula, se pinta, y no manda.
    """

    try:
        huecos = count_free_slots(ledger_audit)

        filas = (season_horizon or {}).get("rows") or []

        # Los que hoy no entran por la via del once, por
        # cualquiera de las dos puertas. Son los que una via de
        # "ampliar plantilla" rescataria.
        vetados = []
        motivos = {}

        for fila in filas:

            if not isinstance(fila, dict):
                continue

            bloqueo = blocked_reason(fila)

            if bloqueo is None:
                continue

            vetados.append(fila)
            motivos[id(fila)] = bloqueo

        # Solo los que se han podido valorar a temporada: ordenar
        # por un valor que no existe seria ordenar por nada.
        valorados = [
            f
            for f in vetados
            if (f.get("season_horizon") or {}).get("season_value")
            is not None
        ]

        ordenados = sorted(
            valorados,
            key=lambda f: -(
                (f.get("season_horizon") or {}).get("season_value") or 0
            ),
        )

        libres = huecos.get("free_slots")

        # Sin saber cuantos huecos hay se enseñan los diez
        # mejores: la lista sigue siendo util, y lo que no se
        # sabe se dice, no se rellena con un numero.
        entrarian = ordenados[: libres if libres else 10]

        coste = sum(safe_int(f.get("market_price")) for f in entrarian)

        puntos = sum(
            (f.get("season_horizon") or {}).get(
                "season_points_remaining"
            )
            or 0
            for f in entrarian
        )

        presupuesto = safe_int(
            (acquisition_budget or {}).get("available_budget")
            or (acquisition_budget or {}).get("total_budget")
        )

        return {
            "available": bool(entrarian),
            "observer_only": True,

            "slots": huecos,

            "reason": (
                None
                if entrarian
                else (
                    "Ningun candidato vetado por la regla del once "
                    "se ha podido valorar a temporada: sin valor no "
                    "hay orden que proponer."
                )
            ),

            "candidates": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "position": f.get("position"),
                    "market_price": safe_int(f.get("market_price")),
                    "expected_points": f.get("expected_points"),
                    "starter_probability": f.get("starter_probability"),
                    "starter_consensus": f.get("starter_consensus"),

                    # Por que NO entra hoy. Es la mitad de la
                    # explicacion: sin esto la lista parece un
                    # capricho.
                    "blocked_by": motivos.get(id(f), (None, ""))[0],
                    "blocked_reason": motivos.get(id(f), (None, ""))[1],

                    "current_value": (
                        f.get("season_horizon") or {}
                    ).get("current_value"),
                    "season_value": (
                        f.get("season_horizon") or {}
                    ).get("season_value"),
                    "season_points_remaining": (
                        f.get("season_horizon") or {}
                    ).get("season_points_remaining"),
                    "cost_per_point": (
                        f.get("season_horizon") or {}
                    ).get("cost_per_point"),
                    "beats_market_rate": (
                        f.get("season_horizon") or {}
                    ).get("beats_market_rate"),
                    "starter_known": (
                        f.get("season_horizon") or {}
                    ).get("starter_known"),
                    "caveat": (
                        f.get("season_horizon") or {}
                    ).get("caveat"),
                }
                for f in entrarian
            ],

            "vetoed_total": len(vetados),
            "candidates_considered": len(valorados),

            "total_cost": coste,
            "total_season_points": round(puntos, 1),

            # Lo que hay hoy para fichar, para que la lista no se
            # lea como una compra hecha. Es informativo: aqui no
            # se decide nada.
            "acquisition_budget": presupuesto or None,
            "affordable_today": (
                coste <= presupuesto if presupuesto else None
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo calcular la via de ampliar plantilla: "
                f"{type(error).__name__}: {error}"
            ),
            "candidates": [],
            "slots": {"known": False},
        }
