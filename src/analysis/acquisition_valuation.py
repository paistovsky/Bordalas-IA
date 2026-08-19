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

from src.analysis.candidate_starter_lookup import (
    get_starter_lookup,
)

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
    starter_lookup: dict | None = None,

    # El once de hoy, para saber a quien se puede tocar barato y
    # a quien no. Opcional: sin el, nadie cuenta como titular y
    # el comportamiento es el de antes.
    lineup: dict | None = None,
) -> dict:
    """
    Lo que hay que calcular una sola vez por ciclo: el precio del
    punto, la fuerza de cada equipo, el peor de los nuestros en
    cada posicion, la velocidad de precio medida por jugador y el
    pronostico de titularidad.

    Si no se pasan los lookups se construyen aqui. Se calculan
    una vez y se reparten, porque leer el historial de precios
    para cada candidato seria absurdo.

    EL PEOR DE CADA POSICION SE ELIGE YA CON TITULARIDAD

        Es la mitad silenciosa del arreglo. "El peor" se decidia
        por puntos de la temporada pasada, asi que un jugador con
        buen historial que este semana no juega parecia mejor que
        un titular modesto. Y el peor es justo a quien se propone
        vender.
    """

    catalogo = (snapshot or {}).get("catalog") or {}

    if velocity_lookup is None:
        velocity_lookup = build_velocity_lookup()

    if starter_lookup is None:
        starter_lookup = get_starter_lookup()

    starter_lookup = starter_lookup or {}

    mercado = calibrate_points_market(catalogo)
    equipos = build_team_strength(catalogo)

    # ==================================================
    # A QUIEN SE LE PREGUNTA (19/08/2026)
    # ==================================================
    #
    # Aqui solo se guardaba el PEOR de cada posicion, y era el
    # unico sustituido que `xi_upgrade_value` llegaba a valorar
    # nunca. Un titular mediocre no estaba descartado: es que no
    # se le preguntaba.
    #
    # Y eso le ponia un techo a Pepe. El dueño pidio que vendiera
    # "siempre para mejorar el XI o ganar pasta", y con un solo
    # candidato a salir solo sabia hacer la segunda mitad.
    #
    # Ahora se guarda la plantilla entera por posicion. El motor
    # de cambio ya sabia hacer la cuenta; le faltaba a quien.
    #
    # `weakest_by_position` se mantiene porque lo lee mas gente y
    # sigue significando lo mismo.

    en_el_once = set()

    for jugador in (
        ((lineup or {}).get("lineup") or {}).get("selected")
        or (lineup or {}).get("selected")
        or []
    ):
        if isinstance(jugador, dict):
            en_el_once.add(safe_int(jugador.get("id")))

    peor_por_posicion = {}
    plantilla_por_posicion = {}

    for jugador in ((snapshot or {}).get("my_team") or []):

        if not isinstance(jugador, dict):
            continue

        posicion = safe_int(jugador.get("position"))

        if posicion not in (1, 2, 3, 4):
            continue

        player_id = safe_int(jugador.get("id"))

        titularidad = starter_lookup.get(player_id)

        puntos = estimate_season_points(
            jugador, mercado, equipos, starter=titularidad
        )

        ficha = {
            "id": player_id,
            "name": jugador.get("name"),
            "price": safe_int(jugador.get("price")),
            "points": puntos["points"],
            "raw_points": puntos.get("raw_points"),
            "points_source": puntos["source"],
            "starter": titularidad,
            "starter_probability": puntos.get(
                "starter_probability"
            ),
            "starter_consensus": puntos.get(
                "starter_consensus"
            ),

            # Si hoy juega. Cambiar a un titular se decide con
            # otras reglas, mas exigentes.
            "in_lineup": player_id in en_el_once,
        }

        plantilla_por_posicion.setdefault(
            posicion, []
        ).append(ficha)

        actual = peor_por_posicion.get(posicion)

        if (
            actual is None
            or ficha["points"] < actual["points"]
        ):
            peor_por_posicion[posicion] = ficha

    return {
        "velocity": velocity_lookup or {},
        "starter": starter_lookup,
        "points_market": mercado,
        "team_strength": equipos,
        "weakest_by_position": peor_por_posicion,
        "squad_by_position": plantilla_por_posicion,
        "lineup_ids": en_el_once,
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

        titulares = (context or {}).get("starter") or {}

        titularidad = titulares.get(
            safe_int(player.get("id"))
        )

        estimacion = estimate_season_points(
            player, mercado, equipos, starter=titularidad
        )

        # --------------------------------------------------
        # COMO MEJORA DEL ONCE
        # --------------------------------------------------

        # A quien podria sustituir: toda la plantilla de esa
        # posicion. Si no viene, al peor, como siempre.
        candidatos_a_salir = (
            (context or {}).get("squad_by_position") or {}
        ).get(posicion)

        if not candidatos_a_salir:
            peor = peores.get(posicion)
            candidatos_a_salir = [peor] if peor else []

        como_xi = None
        descartes = []

        for sustituido in candidatos_a_salir:

            if sustituido is None:
                continue

            titular = bool(sustituido.get("in_lineup"))

            # EL DINERO DE UNA VENTA QUE NO HA PASADO NO ES
            # DINERO (19/08/2026)
            #
            # `recovered_value` sube lo que estariamos dispuestos
            # a pagar contando con lo que entra al vender al
            # sustituido. Para un suplente vale: se publica y se
            # vende sin que el once lo note.
            #
            # Para un titular no. Comprar es instantaneo y vender
            # tarda dias, asi que ese cambio se juzga como si el
            # dinero no fuese a llegar. Si sale rentable igual,
            # es un buen cambio de verdad.
            recuperado = (
                sustituido["price"]
                if assume_replacement_sold and not titular
                else 0
            )

            intento = xi_upgrade_value(
                candidate_points=estimacion["points"],
                replaced_points=sustituido["points"],
                points_market=mercado,
                confidence=estimacion["confidence"],
                recovered_value=recuperado,
                candidate_starter=titularidad,
                replaced_starter=sustituido.get("starter"),

                # La jornada, para que el calendario pese lo que
                # le toca: casi nada al principio de temporada,
                # mucho al final.
                matchday=(titularidad or {}).get("matchday"),

                replaced_in_lineup=titular,
            )

            intento["replaces"] = sustituido

            if titular and recuperado == 0:
                intento["needs_sale_first"] = True

            if safe_int(intento.get("value")) <= 0:
                descartes.append(intento)
                continue

            # Se queda el cambio que mas valor deja. Empatados,
            # el que menos toca el once: sustituir a un suplente
            # es siempre mas barato de deshacer.
            if (
                como_xi is None
                or safe_int(intento["value"])
                > safe_int(como_xi["value"])
                or (
                    safe_int(intento["value"])
                    == safe_int(como_xi["value"])
                    and not titular
                    and como_xi.get("replaces_starter")
                )
            ):
                como_xi = intento

        # Si ninguno sale rentable, se enseña el que menos lejos
        # se quedo: un "no" sin motivo no se puede revisar.
        if como_xi is None and descartes:
            como_xi = descartes[0]

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
                starter=titularidad,
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
            "starter": titularidad,
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
    starter: dict | None = None,
) -> dict:
    """
    EL PRONOSTICO VIAJA TAMBIEN CUANDO SE DICE QUE NO.

        `starter` no estaba aqui, y era el motivo de que la
        cabecera del tablero dijese "8 de 20 con pronostico"
        teniendo 44 de 47. Un candidato rechazado perdia su
        pronostico por el camino, y justamente los rechazados son
        los que hay que poder explicar: la fila decia "tit=None"
        mientras su propio motivo rezaba "esta 20 % titular".

        El dato estaba en la decision y se perdia al enseñarlo.
    """

    return {
        "value": 0,
        "intent": None,
        "decision": decision,
        "reason": reason,
        "points": points,
        "starter": starter,
        "as_xi": as_xi,
        "as_speculation": as_speculation,
        "reasons": [reason],
    }
