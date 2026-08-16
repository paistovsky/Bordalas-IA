"""
Que vale para nosotros cada jugador del mercado, y para que.

QUE JUNTA
    `player_value_engine` sabe convertir puntos y reventa en
    euros. `rival_bid_model` sabe cuanto pujar dado un valor. Lo
    que faltaba entre medias era decidir, para cada jugador
    concreto, POR QUE lo queremos:

    - Como mejora del once, si es mejor que el peor de nuestros
      jugadores de su posicion. Entonces vale lo que valen los
      puntos que suma, mas lo que recuperemos vendiendo al que
      sustituye.

    - Como especulacion, si solo esperamos revenderlo. Entonces
      vale la reventa estimada menos el margen.

    Un jugador puede valer por las dos cosas. Se queda la mayor, y
    se deja escrito cual fue y por que.

POR QUE IMPORTA A QUIEN SUSTITUYE
    Sin eso, "mejora el once" no significa nada. Un delantero de
    160 puntos no mejora nada si el peor delantero que tenemos ya
    hace 158.

    Y el que sustituye no desaparece: se puede vender. Ignorar ese
    dinero hacia que casi ninguna mejora saliera rentable. Con la
    plantilla real, fichar a Tenaglia por 3,25 M y vender a Ximo
    Navarro por 1,28 M cuesta 1,97 M netos por 103 puntos: 19.126
    EUR el punto, cuando el mercado los cobra a 22.240.

    Ese es el chollo, y solo se ve mirando la operacion entera.

LO QUE NO HACE
    No decide si se ejecuta. Solo pone precio. Quien decide es el
    modelo de rivales, que anade la probabilidad de ganar, y los
    guardarrailes, que miran plantilla y caja.
"""

from __future__ import annotations

from src.analysis.player_velocity_lookup import (
    build_velocity_lookup,
)

from src.analysis.player_value_engine import (
    build_team_strength,
    calibrate_points_market,
    estimate_season_points,
    speculation_value,
    xi_upgrade_value,
)


# Horizonte por defecto para valorar una reventa.
#
# Tres dias es lo que suele tardar el mercado en digerir una
# jornada. Mas alla la proyeccion de precio ya no dice gran cosa.
DEFAULT_SPECULATION_HORIZON = 3


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def build_valuation_context(
    snapshot: dict,
    velocity_lookup: dict | None = None,
) -> dict:
    """
    Lo que hay que calcular una sola vez por ciclo: el precio del
    punto, la fuerza de cada equipo, el peor de los nuestros en
    cada posicion y la velocidad de precio medida por jugador.

    Si no se pasa `velocity_lookup` se construye aqui. Se calcula
    una vez y se reparte, porque leer el historial de precios
    para cada candidato seria absurdo.
    """

    catalogo = (snapshot or {}).get("catalog") or {}

    if velocity_lookup is None:
        velocity_lookup = build_velocity_lookup()

    mercado = calibrate_points_market(catalogo)
    equipos = build_team_strength(catalogo)

    peor_por_posicion = {}

    for jugador in ((snapshot or {}).get("my_team") or []):

        if not isinstance(jugador, dict):
            continue

        posicion = safe_int(jugador.get("position"))

        if posicion not in (1, 2, 3, 4):
            continue

        puntos = estimate_season_points(
            jugador, mercado, equipos
        )

        actual = peor_por_posicion.get(posicion)

        if (
            actual is None
            or puntos["points"] < actual["points"]
        ):
            peor_por_posicion[posicion] = {
                "id": safe_int(jugador.get("id")),
                "name": jugador.get("name"),
                "price": safe_int(jugador.get("price")),
                "points": puntos["points"],
                "points_source": puntos["source"],
            }

    return {
        "velocity": velocity_lookup or {},
        "points_market": mercado,
        "team_strength": equipos,
        "weakest_by_position": peor_por_posicion,
        "squad_size": len(
            (snapshot or {}).get("my_team") or []
        ),
    }


def value_candidate(
    player: dict,
    context: dict,
    horizon_days: int = DEFAULT_SPECULATION_HORIZON,
    assume_replacement_sold: bool = True,
) -> dict:
    """
    Cuanto vale este jugador para nosotros, y por que.

    `assume_replacement_sold` decide si contamos el dinero que
    entraria al vender al que sustituye. Por defecto si: la
    estrategia es publicar a todos cada dia, asi que el sustituido
    es vendible de hecho.

    Nunca lanza.
    """

    try:
        mercado = (context or {}).get("points_market") or {}
        equipos = (context or {}).get("team_strength") or {}
        peores = (context or {}).get("weakest_by_position") or {}

        precio = safe_int(player.get("price"))
        posicion = safe_int(player.get("position"))

        if precio <= 0:
            return _sin_valor(
                "PRECIO_INVALIDO",
                "El jugador no tiene precio de mercado valido.",
            )

        estimacion = estimate_season_points(
            player, mercado, equipos
        )

        # --------------------------------------------------
        # COMO MEJORA DEL ONCE
        # --------------------------------------------------

        sustituido = peores.get(posicion)

        como_xi = None

        if sustituido is not None:

            recuperado = (
                sustituido["price"]
                if assume_replacement_sold
                else 0
            )

            como_xi = xi_upgrade_value(
                candidate_points=estimacion["points"],
                replaced_points=sustituido["points"],
                points_market=mercado,
                confidence=estimacion["confidence"],
                recovered_value=recuperado,
            )

            como_xi["replaces"] = sustituido

        # --------------------------------------------------
        # COMO ESPECULACION
        # --------------------------------------------------

        velocidades = (context or {}).get("velocity") or {}

        velocidad = velocidades.get(
            safe_int(player.get("id"))
        )

        como_trading = speculation_value(
            price=precio,
            daily_increment=safe_int(
                player.get("priceIncrement")
            ),
            horizon_days=horizon_days,
            confidence=estimacion["confidence"],

            # Medida sobre varios dias cuando la hay; si no,
            # dentro se cae al incremento de ayer y lo dice.
            velocity_percent_per_day=velocidad,
        )

        # --------------------------------------------------
        # LA MAYOR DE LAS DOS
        # --------------------------------------------------

        opciones = [
            o for o in (como_xi, como_trading)
            if o and safe_int(o.get("value")) > 0
        ]

        if not opciones:
            motivos = []

            if como_xi:
                motivos.append(
                    f"como mejora del once, "
                    f"{como_xi.get('decision', '?')}"
                )
            if como_trading:
                motivos.append(
                    f"como especulacion, "
                    f"{como_trading.get('decision', '?')}"
                )

            return _sin_valor(
                "SIN_VALOR",
                (
                    "No vale la pena por ninguna via: "
                    + "; ".join(motivos)
                    + "."
                ),
                points=estimacion,
                as_xi=como_xi,
                as_speculation=como_trading,
            )

        mejor = max(
            opciones,
            key=lambda o: safe_int(o.get("value")),
        )

        return {
            "value": safe_int(mejor["value"]),
            "intent": mejor.get("intent"),
            "decision": "VALUED",
            "market_price": precio,
            "points": estimacion,
            "as_xi": como_xi,
            "as_speculation": como_trading,
            "replaces": mejor.get("replaces"),
            "reason": mejor.get("reason"),
            "reasons": [
                estimacion["reason"],
                mejor.get("reason", ""),
            ],
        }

    except Exception as error:
        return _sin_valor(
            "ERROR",
            f"{type(error).__name__}: {error}",
        )


def _sin_valor(
    decision: str,
    reason: str,
    points: dict | None = None,
    as_xi: dict | None = None,
    as_speculation: dict | None = None,
) -> dict:
    return {
        "value": 0,
        "intent": None,
        "decision": decision,
        "reason": reason,
        "points": points,
        "as_xi": as_xi,
        "as_speculation": as_speculation,
        "reasons": [reason],
    }
