from itertools import combinations

from src.analysis.player_availability import (
    analyze_player_availability,
)

from src.analysis.home_away_intelligence import (
    build_home_away_context,
)

from src.intelligence.penalty_intelligence import (
    get_penalty_context,
)

from src.analysis.position_policy import (
    POSITION_POLICY,
    assert_lineup_position_integrity,
    get_effective_positions,
)

from src.intelligence.lineup_intelligence import (
    build_lineup_intelligence,
)

from src.analysis.calendar_state import (
    build_calendar_state,
)

# El import de `multisource_starter_v1124` se retiro el
# 17/08/2026. Este modulo ya no scrapea nada: lee el lookup de
# FutbolFantasy que el ciclo refresca antes de valorar.


# ============================================================
# V11.3 STARTER INTELLIGENCE LIVE
# ============================================================

_MULTISOURCE_STARTER_CACHE = {}


def board_from_single_source() -> dict:
    """
    El tablero del once, hecho con la fuente unica.

    POR QUE EXISTE

        El 17/08/2026 se migro a FutbolFantasy todo: la compra, la
        valoracion, el veto, la venta y el dashboard. El once no.
        Seguia eligiendose con el sistema multifuente retirado, que
        ademas se reconstruia en cada ciclo scrapeando Jornada
        Perfecta y Analitica Fantasy.

        Lo vio el dueño en su propio dashboard:

            Jonny Castro  70 % IMPORTANTE  ->  al banquillo
            Hugo Rincon   41 % RESERVA     ->  al once

        En FF, Castro es Importante al 70 % y Rincon es Reserva y
        ni sale en el once del Athletic. El motor los alineaba al
        reves porque no miraba FF.

    QUE HACE

        Traduce el lookup de la fuente unica a la forma que ya
        espera el resto de este modulo. No se toca la logica de
        seleccion: solo de donde salen los numeros.

        Los votos se derivan del consenso porque con una sola
        fuente hay un solo voto. El desempate por calidad de voto
        sigue funcionando -un STARTER gana a un UNCERTAIN- pero ya
        no hay tres fuentes que puedan contradecirse.
    """

    from src.analysis.candidate_starter_lookup import (
        get_starter_lookup,
    )

    lookup = get_starter_lookup() or {}

    jugadores = []

    for player_id, senal in lookup.items():

        consenso = senal.get("consensus")

        jerarquia = senal.get("hierarchy") or {}

        jugadores.append(
            {
                "player_id": int(player_id),
                "player_name": senal.get("player_name"),

                "starter_probability": senal.get("probability"),
                "consensus": consenso,
                "source_coverage": int(senal.get("coverage") or 1),

                # Un voto, el de FF.
                "starter_votes": 1 if consenso == "STARTER" else 0,
                "bench_votes": 1 if consenso == "BENCH" else 0,
                "uncertain_votes": 1 if consenso == "UNCERTAIN" else 0,

                # De aqui salen la jerarquia y el parte de baja,
                # que hoy no los usa la seleccion pero viajan para
                # que pueda usarlos.
                "hierarchy": jerarquia,
                "absence": senal.get("absence"),
                "availability": senal.get("availability"),
                "team": senal.get("team"),

                "sources": {
                    "FUTBOLFANTASY": {
                        "source": "FUTBOLFANTASY",
                        "probability": senal.get("probability"),
                    },
                },
            }
        )

    return {
        "version": "V12.0_SINGLE_SOURCE",
        "source": "FUTBOLFANTASY",
        "players": jugadores,
    }


def build_starter_intelligence_for_snapshot(
    snapshot: dict,
) -> dict | None:

    cache_key = id(snapshot)

    cached = _MULTISOURCE_STARTER_CACHE.get(
        cache_key
    )

    if cached is not None:
        return cached

    # FUENTE UNICA (17/08/2026)
    #
    # Aqui se llamaba a `build_multisource_board`, que ademas de
    # decidir el once volvia a scrapear Jornada Perfecta y
    # Analitica Fantasy en CADA ciclo. Las dos estan retiradas.
    #
    # Ahora se lee el lookup de FutbolFantasy, que el ciclo ya ha
    # refrescado antes de valorar: ni una peticion mas, y el mismo
    # dato que usan la compra y la venta. Un solo sitio donde
    # equivocarse.
    try:
        board = board_from_single_source()

        if not board.get("players"):
            board = {
                "version": "V12.0_EMPTY",
                "error": (
                    "El tablero de FutbolFantasy esta vacio: se "
                    "alinea sin pronostico."
                ),
                "players": [],
            }

    except Exception as error:
        board = {
            "version": "V12.0_FALLBACK",
            "error": (
                f"{type(error).__name__}: "
                f"{error}"
            ),
            "players": [],
        }

    _MULTISOURCE_STARTER_CACHE[
        cache_key
    ] = board

    return board


def starter_lookup_from_board(
    board: dict | None,
) -> dict[int, dict]:

    if not board:
        return {}

    return {
        int(item["player_id"]): item
        for item in board.get(
            "players",
            [],
        )
        if item.get("player_id") is not None
    }


# ============================================================
# FORMACIONES
# ============================================================


FORMATION = {
    1: 1,
    2: 4,
    3: 3,
    4: 3,
}


# Formaciones que Pepe evalua automaticamente.
# No existe bonus por formacion: gana el XI legal completo
# con mejor lineup_score.
FORMATIONS = {
    "3-4-3": {1: 1, 2: 3, 3: 4, 4: 3},
    "3-5-2": {1: 1, 2: 3, 3: 5, 4: 2},
    "4-3-3": {1: 1, 2: 4, 3: 3, 4: 3},
    "4-4-2": {1: 1, 2: 4, 3: 4, 4: 2},
    "4-5-1": {1: 1, 2: 4, 3: 5, 4: 1},
    "5-3-2": {1: 1, 2: 5, 3: 3, 4: 2},
    "5-4-1": {1: 1, 2: 5, 3: 4, 4: 1},
}


# ============================================================
# JORNADA
# ============================================================
#
# La pertenencia a la jornada la gobierna el calendario dinamico.
# No usamos team.nextGames para decidir si un jugador puede entrar
# en el XI. Un partido aplazado sigue perteneciendo a su jornada
# original y usa el XI fijado antes del primer kickoff.
# ============================================================


# ============================================================
# COMPATIBILIDAD CON MODULOS ANTIGUOS
# ============================================================


def player_has_current_round_game(
    snapshot: dict,
    player: dict,
) -> bool:
    """
    Shim de compatibilidad.

    Algunos motores antiguos (por ejemplo, el de impacto de
    reestructuración/Franchise) todavía importan esta función.

    En la arquitectura V3 ya NO consultamos team.nextGames para
    decidir si un jugador pertenece a la jornada. El calendario
    dinámico gobierna la jornada completa y un aplazamiento no
    elimina al jugador de ella.

    Por tanto, para esos consumidores antiguos, "tener partido
    en la jornada" significa simplemente "pertenecer a la
    plantilla/competición de la jornada objetivo".

    `snapshot` se conserva en la firma para no romper imports y
    llamadas existentes.
    """

    del snapshot

    return bool(
        player
        and
        player.get(
            "teamID"
        )
        is not None
    )


# ============================================================
# POSICIONES
# ============================================================


def get_player_positions(
    player: dict,
) -> list[int]:
    """
    Compatibilidad publica con consumidores existentes.

    Position Policy V1:
    Pepe usa exclusivamente la posicion principal de Biwenger.
    altPositions se conserva como metadata, pero no permite ocupar
    otro slot del XI ni cubrir necesidades tacticas.
    """

    return get_effective_positions(
        player
    )


# ============================================================
# SCORE BASE
# ============================================================


def calculate_lineup_score(
    player: dict,
    availability: dict | None = None,
) -> float:
    """
    Score del XI de la JORNADA COMPLETA.

    NO se premia ni penaliza a un jugador porque su partido
    aparezca o no en team.nextGames.

    Esa lista puede omitir partidos aplazados de la jornada
    actual, por lo que usarla para +1000/-1000 distorsionaba
    gravemente el XI.

    Factores actuales:
    - puntos temporada anterior;
    - valor de mercado como proxy suave de calidad;
    - disponibilidad real;
    - status;
    - ajuste externo de Jornada Perfecta (se suma despues).

    Franchise/Strategic Score se integraran como capa adicional,
    pero no son necesarios para corregir el bug temporal.
    """

    score = 0.0

    if availability is None:

        availability = (
            analyze_player_availability(
                player
            )
        )

    if not availability[
        "available"
    ]:

        return -1_000_000.0

    last_points = (
        player.get(
            "pointsLastSeason"
        )
        or 0
    )

    score += float(
        last_points
    )

    price = (
        player.get(
            "price",
            0,
        )
        or 0
    )

    score += (
        float(
            price
        )
        / 1_000_000
    )

    # Automatic lineup representa si el motor de disponibilidad
    # considera seguro alinearlo. No lo bloqueamos aqui porque
    # search_best_lineup_for_formation ya tiene modo normal y
    # modo emergencia, pero sí penalizamos si entra como warning.
    if availability[
        "automatic_lineup"
    ]:

        score += 20.0

    else:

        score -= 500.0

    if (
        availability[
            "status"
        ]
        == "ok"
    ):

        score += 10.0

    return score


# ============================================================
# CUANTO ESPERO DE ESTE JUGADOR ESTE SABADO
# ============================================================
#
# EL CASO QUE LO DESTAPO (18/08/2026)
#
#     Yamal, Dios del Barcelona, 60 % de titular segun FF, se
#     cayo del once. Entraba en su lugar cualquier titular
#     confirmado, incluido un Revulsivo al 70 %.
#
#     No era un fallo de datos: la jerarquia ya llegaba hasta
#     aqui -se migro el 17/08- pero no puntuaba. El once se
#     ordenaba por la ETIQUETA del consenso:
#
#         starter_tier * 100.000
#
#     y esa etiqueta sale de un corte seco: STARTER a partir del
#     67 %, BENCH hasta el 40 %, UNCERTAIN en medio. Yamal al
#     60 % caia en UNCERTAIN -tier 3- y cualquier jugador al
#     70 % era STARTER -tier 5-. Doscientos mil puntos de
#     ventaja que el 60 % de Yamal, valorado a 100 por punto, no
#     podia recortar ni de lejos.
#
#     El dueño lo dijo en una linea: "hay que ponerlo en el XI
#     aunque vaya a jugar unos minutos solo".
#
# POR QUE NO BASTA CON ORDENAR POR PORCENTAJE
#
#     Porque el porcentaje de FF responde a "¿SALE DE INICIO?",
#     y esa no es la pregunta del fantasy. La pregunta es
#     "¿cuantos puntos me hace?". Y ahi hay dos cosas que el
#     porcentaje solo no dice:
#
#     1. Un Dios que no sale de inicio ENTRA. Un coach guarda a
#        Yamal media hora y lo mete; a un Reserva no lo mete
#        nunca. El 40 % que le falta a Yamal no es cero: es un
#        banquillo del que se sale casi siempre.
#
#     2. Cuando juegan, no rinden igual. Un Dios en media hora
#        puede hacer mas que un Rotacion en noventa minutos.
#
#     Asi que el valor de la semana son dos factores:
#
#         participacion  =  % titular  +  (lo que falta) * cuanto
#                                          entra desde el banquillo
#
#         valor          =  participacion * calidad del escalon
#
# ESTOS NUMEROS SON CRITERIO, NO MEDICION
#
#     A dia de hoy no hay minutos acumulados suficientes para
#     medir ninguna de las dos tablas: van dos jornadas. Estan
#     puestos a ojo, con una forma que se defiende sola -un Dios
#     entra casi siempre, un Reserva casi nunca, un Revulsivo
#     entra mas que un Importante porque para eso esta- y se
#     recalibran con minutos reales en la jornada 6-8, junto con
#     la escala de puntos que ya esta pendiente.
#
#     Lo que NO es criterio es la direccion: que la jerarquia
#     pese en el once es una de las cuatro decisiones del plan.
# ============================================================


# Cuanto entra desde el banquillo cada escalon, cuando FF no lo
# da de titular. El Revulsivo esta alto a proposito: entrar es
# literalmente su oficio.
HIERARCHY_BENCH_APPEARANCE = {
    60: 0.70,   # Dios
    50: 0.50,   # Clave
    40: 0.35,   # Importante
    30: 0.20,   # Rotacion
    25: 0.45,   # Revulsivo
    20: 0.08,   # Reserva
    10: 0.03,   # Descarte
}


# Cuanto rinde cada escalon cuando juega.
HIERARCHY_MATCH_QUALITY = {
    60: 1.00,   # Dios
    50: 0.92,   # Clave
    40: 0.80,   # Importante
    30: 0.62,   # Rotacion
    25: 0.50,   # Revulsivo
    20: 0.38,   # Reserva
    10: 0.25,   # Descarte
}


# Sin jerarquia NO se asume la peor. Ausencia de dato no es dato:
# un jugador sin ficha en FF -un recien llegado, un portero
# suplente- se trata como un escalon medio y se ordena por su
# porcentaje, que es lo unico que si se sabe de el.
HIERARCHY_UNKNOWN_VALUE = 30


# ============================================================
# UN DIOS JUEGA SIEMPRE
# ============================================================
#
# LA REGLA (decision del dueño, 18/08/2026)
#
#     "Para elegir el XI, hay que hacer que los jerarquia DIOS
#     jueguen siempre salvo caso de titularidad 0 % asegurada
#     -lesion, sancion u otro motivo-."
#
# POR QUE NO BASTABA CON LO DE ESTA MISMA MAÑANA
#
#     Con `weekly_expected_value` a secas, un Dios al 60 % ya
#     ganaba a un Revulsivo al 70 % -ese era el caso Yamal- pero
#     seguia siendo una competicion: bastaba con que dos Claves
#     al 90 % ocupasen su linea para que el Dios volviese al
#     banquillo. Y un Dios al 20 % perdia contra medio equipo.
#
#     El dueño no quiere que compita. Quiere que juegue. Un Dios
#     con dudas y treinta minutos rinde mas que un Rotacion
#     confirmado noventa, y sobre todo: si marca, marca el.
#
# LO QUE SIGUE SIENDO CIERTO
#
#     Esto NO pasa por encima de la disponibilidad. Un Dios que
#     Biwenger da por no alineable sigue valiendo -1.000.000 y no
#     entra: el bono se suma DESPUES de comprobar que se le puede
#     alinear, no antes.
#
# EL 0 % TIENE QUE ESTAR MOTIVADO
#
#     "Asegurada" es la palabra del dueño y se toma en serio: un
#     0 % suelto no basta para sentar a un Dios. Hace falta un
#     motivo -lesionado, sancionado, no disponible, un parte de
#     baja con jornadas-.
#
#     Un Dios al 0 % que FF da como DISPONIBLE y sin parte es una
#     contradiccion, no una noticia. Ausencia de dato no es dato:
#     ese juega, y se avisa en el ciclo para poder mirarlo.
# ============================================================


MANDATORY_HIERARCHY_VALUE = 60


# Por encima de cualquier score posible de un no-Dios. El maximo
# alcanzable sin bono ronda 1.000.000 -valor semanal 1,0- mas
# unos cientos de base, asi que diez millones no deja duda.
MANDATORY_HIERARCHY_BONUS = 10_000_000.0


def god_is_ruled_out(starter: dict) -> tuple[bool, str | None]:
    """
    Un Dios solo se sienta con el 0 % MOTIVADO.

    Devuelve (se_sienta, motivo). Sin motivo no se sienta, aunque
    el porcentaje sea 0: eso es un dato raro, no una baja.
    """

    probabilidad = starter.get("starter_probability")

    if probabilidad is None or float(probabilidad) > 0:
        return False, None

    disponibilidad = starter.get("availability") or {}

    if disponibilidad.get("can_play") is False:
        return True, str(
            disponibilidad.get("label") or "NO DISPONIBLE"
        )

    if disponibilidad.get("sanctioned"):
        return True, "SANCIONADO"

    etiqueta = str(disponibilidad.get("label") or "").upper()

    if etiqueta and etiqueta != "DISPONIBLE":
        return True, etiqueta

    baja = starter.get("absence") or {}

    if baja.get("matchdays_out") or baja.get("reason"):
        return True, str(
            baja.get("reason") or "BAJA"
        )

    # 0 % y nadie dice por que.
    return False, None


def weekly_expected_value(
    hierarchy_value: int | None,
    starter_probability: float | None,
) -> float:
    """
    Lo que espero de este jugador ESTA jornada, de 0 a 1.

    No es una prediccion de puntos: es una vara comun para
    ordenar el once, la misma para un Dios con dudas y para un
    Rotacion confirmado.

    Devuelve None-seguro: si no hay porcentaje no se inventa, lo
    resuelve quien llama.
    """

    if starter_probability is None:
        return 0.0

    escalon = (
        int(hierarchy_value)
        if hierarchy_value
        else HIERARCHY_UNKNOWN_VALUE
    )

    if escalon not in HIERARCHY_MATCH_QUALITY:
        escalon = HIERARCHY_UNKNOWN_VALUE

    titular = max(
        0.0,
        min(
            1.0,
            float(starter_probability) / 100.0,
        ),
    )

    desde_el_banquillo = HIERARCHY_BENCH_APPEARANCE[escalon]

    participacion = (
        titular
        +
        (1.0 - titular) * desde_el_banquillo
    )

    return participacion * HIERARCHY_MATCH_QUALITY[escalon]


# ============================================================
# PREPARAR JUGADORES
# ============================================================


def prepare_players(
    snapshot: dict,
    lineup_intelligence: dict | None = None,
    starter_intelligence: dict | None = None,
) -> list[dict]:

    if lineup_intelligence is None:

        lineup_intelligence = (
            build_lineup_intelligence(
                snapshot
            )
        )

    intelligence_lookup = (
        lineup_intelligence.get(
            "lookup",
            {},
        )
    )

    if starter_intelligence is None:
        starter_intelligence = (
            build_starter_intelligence_for_snapshot(
                snapshot
            )
        )

    starter_lookup = (
        starter_lookup_from_board(
            starter_intelligence
        )
    )

    players = []

    for player in snapshot[
        "my_team"
    ]:

        player_id = int(
            player[
                "id"
            ]
        )

        availability = (
            analyze_player_availability(
                player
            )
        )

        base_score = (
            calculate_lineup_score(
                player=
                    player,

                availability=
                    availability,
            )
        )

        external = (
            intelligence_lookup.get(
                player_id,
                {},
            )
            or {}
        )

        starter = (
            starter_lookup.get(
                player_id,
                {},
            )
            or {}
        )

        starter_coverage = int(
            starter.get(
                "source_coverage"
            )
            or 0
        )

        starter_probability = (
            float(
                starter.get(
                    "starter_probability"
                )
            )
            if (
                starter_coverage > 0
                and
                starter.get(
                    "starter_probability"
                )
                is not None
            )
            else None
        )

        external_block = bool(
            external.get(
                "external_block",
                False,
            )
        )

        lineup_eligible = bool(
            availability[
                "available"
            ]
            and
            not external_block
        )

        external_adjustment = float(
            external.get(
                "score_adjustment",
                0.0,
            )
            or 0.0
        )

        home_away_context = (
            build_home_away_context(
                snapshot,
                player,
            )
        )

        penalty_context = (
            get_penalty_context(
                snapshot,
                player,
            )
        )

        home_away_adjustment = float(
            home_away_context.get(
                "bonus",
                0.0,
            )
            or 0.0
        )

        penalty_adjustment = float(
            penalty_context.get(
                "bonus",
                0.0,
            )
            or 0.0
        )

        expected_value = 0.0

        # UN DIOS JUEGA SIEMPRE.
        #
        # Se resuelve aqui, con el jugador delante, y no dentro
        # del score: son tres estados distintos -es Dios y juega,
        # es Dios y esta de baja motivada, no es Dios- y los tres
        # tienen que poder contarse luego.
        jerarquia = starter.get("hierarchy") or {}

        es_dios = (
            int(jerarquia.get("value") or 0)
            == MANDATORY_HIERARCHY_VALUE
        )

        dios_sentado = False
        dios_motivo = None
        dios_forzado = False
        dios_sin_motivo = False

        if es_dios:

            dios_sentado, dios_motivo = god_is_ruled_out(
                starter
            )

            dios_forzado = not dios_sentado

            # Un Dios al 0 % que nadie explica. Juega -no se
            # sienta a un Dios por un dato suelto- pero se canta,
            # porque o FF sabe algo que no vemos o el dato esta
            # viejo.
            dios_sin_motivo = (
                dios_forzado
                and
                starter_probability is not None
                and
                starter_probability <= 0
            )

        if lineup_eligible:

            if starter_probability is not None:

                # ====================================================
                # JERARQUIA + PORCENTAJE  (18/08/2026)
                # ====================================================
                #
                # Aqui se ordenaba por la CLASE del consenso
                # -STARTER > UNCERTAIN > BENCH, 100.000 por
                # escalon- y el porcentaje solo desempataba dentro
                # de la clase.
                #
                # Ese corte seco saco a Yamal del once: 60 % es
                # UNCERTAIN, 70 % es STARTER, y diez puntos de
                # porcentaje valian doscientos mil de score. El
                # Dios del Barcelona perdia el sitio contra un
                # Revulsivo.
                #
                # Ahora ordena `weekly_expected_value`, que junta
                # las dos senales de FF -el escalon estructural y
                # el pronostico de la semana- en un solo numero.
                # El consenso se conserva para informar, no para
                # puntuar: la etiqueta no decide nada.
                #
                # La cobertura se queda como desempate porque un
                # dato con fuente vale mas que uno sin ella, y el
                # porcentaje crudo debajo, para que dos jugadores
                # del mismo escalon no queden empatados.
                # ====================================================

                expected_value = weekly_expected_value(
                    jerarquia.get("value"),
                    starter_probability,
                )

                final_score = (
                    expected_value
                    * 1_000_000.0

                    + starter_coverage
                    * 3_000.0

                    + starter_probability
                    * 100.0

                    + base_score

                    + home_away_adjustment

                    + penalty_adjustment
                )

            else:

                # Sin pronostico de FF. No se inventa un escalon ni
                # un porcentaje: se le da un valor de 0,25 en la
                # misma escala, que lo deja por encima de un
                # suplente conocido -un Reserva al 40 % vale 0,17-
                # y por debajo de cualquier titular conocido.
                #
                # Dicho de otro modo: no saber es peor que saber
                # que si, y mejor que saber que no.
                expected_value = 0.25

                final_score = (
                    250_000.0
                    + base_score
                    + external_adjustment
                    + home_away_adjustment
                    + penalty_adjustment
                )

        else:

            final_score = (
                -1_000_000.0
            )

            # Un Dios no alineable no es un Dios sentado por
            # criterio: no lo deja Biwenger. Se anota como tal
            # para que el informe no diga que se le ha dejado
            # fuera a proposito.
            if es_dios and not dios_sentado:

                dios_forzado = False
                dios_sin_motivo = False
                dios_sentado = True

                dios_motivo = (
                    availability.get("label")
                    or "NO ALINEABLE"
                )

        # EL BONO VA AQUI, NO DENTRO DEL SCORE.
        #
        # Despues de comprobar que se le puede alinear. Un Dios
        # lesionado sigue valiendo -1.000.000: la regla dice que
        # juega siempre, no que juegue roto.
        if dios_forzado and lineup_eligible:
            final_score += MANDATORY_HIERARCHY_BONUS

        external_status = (
            external.get(
                "status",
                "UNKNOWN",
            )
        )

        if external_block:

            effective_label = (
                "NO CONVOCADO - JORNADA PERFECTA"
            )

        else:

            effective_label = (
                availability[
                    "label"
                ]
            )

        players.append(
            {
                **player,

                "eligible_positions":
                    get_player_positions(
                        player
                    ),

                # ------------------------------------------------
                # JORNADA FANTASY
                # ------------------------------------------------
                # Todos los jugadores disponibles de la plantilla
                # pertenecen al target matchday. Un aplazamiento no
                # los saca de la jornada.

                "counts_for_round":
                    True,

                "round_scoring_eligible":
                    lineup_eligible,

                # ------------------------------------------------
                # DISPONIBILIDAD
                # ------------------------------------------------

                "availability":
                    availability,

                "availability_label":
                    effective_label,

                "automatic_lineup":
                    availability[
                        "automatic_lineup"
                    ],

                "is_available":
                    availability[
                        "available"
                    ],

                "lineup_eligible":
                    lineup_eligible,

                # ------------------------------------------------
                # SCORE
                # ------------------------------------------------

                "base_lineup_score":
                    base_score,

                "external_lineup":
                    external,

                "external_lineup_status":
                    external_status,

                "external_lineup_confidence":
                    external.get(
                        "effective_confidence",
                        0,
                    ),

                "external_lineup_adjustment":
                    external_adjustment,

                "external_lineup_block":
                    external_block,

                "starter_intelligence":
                    starter,

                "starter_probability":
                    starter_probability,

                "starter_expected_minutes":
                    starter.get(
                        "expected_minutes"
                    ),

                "starter_source_coverage":
                    starter_coverage,

                "starter_consensus":
                    starter.get(
                        "consensus"
                    ),

                # Lo que ordena el once. Viaja hasta el dashboard
                # para que se pueda ver POR QUE entra cada uno,
                # que es la cuarta decision del plan: todo lo que
                # entra tiene que verse.
                "weekly_expected_value":
                    expected_value,

                "hierarchy":
                    starter.get("hierarchy"),

                # Los tres estados de la regla del Dios, para que
                # el informe pueda decir cual de ellos toco.
                "mandatory_hierarchy":
                    dios_forzado,

                "mandatory_hierarchy_ruled_out":
                    dios_sentado,

                "mandatory_hierarchy_reason":
                    dios_motivo,

                "mandatory_hierarchy_unexplained":
                    dios_sin_motivo,

                "starter_confidence":
                    starter.get(
                        "confidence"
                    ),

                "starter_sources":
                    starter.get(
                        "sources",
                        {},
                    ),

                "home_away_context":
                    home_away_context,

                "home_away_adjustment":
                    home_away_adjustment,

                "penalty_context":
                    penalty_context,

                "penalty_adjustment":
                    penalty_adjustment,

                "lineup_score_components":
                    {
                        "base":
                            base_score,

                        "jornada_perfecta_legacy":
                            external_adjustment,

                        "starter_probability":
                            starter_probability,

                        "starter_source_coverage":
                            starter_coverage,

                        "home_away":
                            home_away_adjustment,

                        "penalty":
                            penalty_adjustment,
                    },

                "lineup_score":
                    final_score,

                # EL MISMO SCORE, SIN EL BONO DEL DIOS
                #
                # El bono existe para ELEGIR, no para VALORAR. Si
                # se colase en el valor deportivo del once, diez
                # millones de bono inflarian el total y todo lo
                # demas se volveria barato en comparacion: vender
                # un Clave pasaria de costar un 15 % del once a
                # costar un 8 %, y `safe_debt_portfolio_engine`
                # -que decide a quien se puede soltar mirando ese
                # porcentaje- se volveria mas permisivo justo por
                # tener un Dios en plantilla.
                #
                # Asi que el bono manda dentro de la busqueda y se
                # queda fuera de la cuenta.
                "lineup_score_sporting":
                    (
                        final_score
                        -
                        MANDATORY_HIERARCHY_BONUS
                    )
                    if (dios_forzado and lineup_eligible)
                    else final_score,
            }
        )

    return players


# ============================================================
# BUSQUEDA OPTIMIZADA
# ============================================================


def search_best_lineup_for_formation(
    players: list[dict],
    formation: dict[int, int],
    allow_warning_players: bool = False,
) -> dict:

    usable_players = []

    for player in players:

        if not player[
            "lineup_eligible"
        ]:

            continue

        if (
            not allow_warning_players
            and
            not player[
                "automatic_lineup"
            ]
        ):

            continue

        usable_players.append(
            player
        )

    position_candidates = {}

    for position in formation:

        candidates = [
            player

            for player in usable_players

            if position
            in player[
                "eligible_positions"
            ]
        ]

        candidates.sort(
            key=lambda player:
                player[
                    "lineup_score"
                ],
            reverse=True,
        )

        position_candidates[
            position
        ] = candidates

    position_order = sorted(
        formation.keys(),
        key=lambda position: (
            len(
                position_candidates[
                    position
                ]
            ),
            formation[
                position
            ],
        ),
    )

    best_lineup = []

    best_score = float(
        "-inf"
    )

    best_filled = -1

    def search_position(
        position_index: int,
        used_ids: set[int],
        selected: list[dict],
        score: float,
    ) -> None:

        nonlocal best_lineup
        nonlocal best_score
        nonlocal best_filled

        if (
            position_index
            >= len(
                position_order
            )
        ):

            filled = len(
                selected
            )

            if (
                filled > best_filled

                or (
                    filled
                    == best_filled

                    and
                    score
                    > best_score
                )
            ):

                best_filled = (
                    filled
                )

                best_score = (
                    score
                )

                best_lineup = list(
                    selected
                )

            return

        position = (
            position_order[
                position_index
            ]
        )

        required = (
            formation[
                position
            ]
        )

        candidates = [
            player

            for player in (
                position_candidates[
                    position
                ]
            )

            if player[
                "id"
            ]
            not in used_ids
        ]

        max_take = min(
            required,
            len(
                candidates
            ),
        )

        for take_count in range(
            max_take,
            -1,
            -1,
        ):

            for combo in combinations(
                candidates,
                take_count,
            ):

                combo_ids = {
                    player[
                        "id"
                    ]

                    for player in combo
                }

                combo_score = sum(
                    player[
                        "lineup_score"
                    ]

                    for player in combo
                )

                combo_selected = [
                    {
                        **player,

                        "lineup_position":
                            position,
                    }

                    for player in combo
                ]

                search_position(
                    position_index + 1,

                    used_ids
                    | combo_ids,

                    selected
                    + combo_selected,

                    score
                    + combo_score,
                )

    search_position(
        position_index=0,
        used_ids=set(),
        selected=[],
        score=0.0,
    )

    if best_filled < 0:

        best_filled = 0

        best_score = 0.0

        best_lineup = []

    return {
        "selected":
            best_lineup,

        "score":
            best_score,

        "filled":
            best_filled,

        "complete":
            best_filled == 11,
    }


# ============================================================
# FORMACION
# ============================================================


def evaluate_formation(
    players: list[dict],
    formation_name: str,
    formation: dict[int, int],
) -> dict:

    normal = (
        search_best_lineup_for_formation(
            players,
            formation,
            allow_warning_players=False,
        )
    )

    if normal[
        "complete"
    ]:

        return {
            **normal,

            "formation_name":
                formation_name,

            "formation":
                formation,

            "used_warning_players":
                False,
        }

    emergency = (
        search_best_lineup_for_formation(
            players,
            formation,
            allow_warning_players=True,
        )
    )

    return {
        **emergency,

        "formation_name":
            formation_name,

        "formation":
            formation,

        "used_warning_players":
            True,
    }


# ============================================================
# BUILD
# ============================================================


def build_lineup(
    snapshot: dict,
    lineup_intelligence: dict | None = None,
) -> dict:

    if lineup_intelligence is None:

        lineup_intelligence = (
            build_lineup_intelligence(
                snapshot
            )
        )

    starter_intelligence = (
        build_starter_intelligence_for_snapshot(
            snapshot
        )
    )

    players = (
        prepare_players(
            snapshot=
                snapshot,

            lineup_intelligence=
                lineup_intelligence,

            starter_intelligence=
                starter_intelligence,
        )
    )

    formation_results = []

    for (
        formation_name,
        formation,
    ) in FORMATIONS.items():

        result = (
            evaluate_formation(
                players,
                formation_name,
                formation,
            )
        )

        formation_results.append(
            result
        )

    formation_results.sort(
        key=lambda result: (
            result[
                "filled"
            ],
            result[
                "score"
            ],
        ),
        reverse=True,
    )

    best = (
        formation_results[
            0
        ]

        if formation_results

        else {
            "selected": [],
            "score": 0.0,
            "filled": 0,
            "complete": False,
            "formation_name": "4-3-3",
            "formation": FORMATION,
            "used_warning_players": False,
        }
    )

    best_lineup = (
        best[
            "selected"
        ]
    )

    selected_formation = (
        best[
            "formation"
        ]
    )

    best_lineup.sort(
        key=lambda player: (
            player.get(
                "lineup_position",
                99,
            ),

            -player.get(
                "lineup_score",
                0,
            ),
        )
    )

    # Hard Safety: ningun jugador puede salir de su posicion.
    assert_lineup_position_integrity(
        best_lineup
    )

    blocked_players = [
        player

        for player in players

        if (
            not player[
                "is_available"
            ]

            or
            player[
                "external_lineup_block"
            ]
        )
    ]

    unavailable_selected = [
        player

        for player in best_lineup

        if (
            not player[
                "automatic_lineup"
            ]
        )
    ]

    # ========================================================
    # PLAYABLE COUNT
    # ========================================================
    #
    # Ahora "playable" significa:
    # - pertenece al XI;
    # - esta disponible;
    # - el motor considera seguro alinearlo.
    #
    # NO depende de que team.nextGames contenga el partido.
    # ========================================================

    playable_count = sum(
        1

        for player in best_lineup

        if (
            player[
                "lineup_eligible"
            ]

            and
            player[
                "automatic_lineup"
            ]
        )
    )

    matchday_shortages = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
    }

    for (
        position_id,
        required,
    ) in selected_formation.items():

        playable_in_position = sum(
            1

            for player in best_lineup

            if (
                player[
                    "lineup_position"
                ]
                == position_id

                and
                player[
                    "lineup_eligible"
                ]

                and
                player[
                    "automatic_lineup"
                ]
            )
        )

        matchday_shortages[
            position_id
        ] = max(
            required
            - playable_in_position,
            0,
        )

    external_risk_selected = [
        player

        for player in best_lineup

        if (
            (
                player.get(
                    "starter_probability"
                )
                is not None
                and
                str(
                    player.get(
                        "starter_consensus"
                    )
                    or ""
                ).upper()
                in {
                    "UNCERTAIN",
                    "BENCH_LEAN",
                    "BENCH",
                }
            )
            or
            (
                player.get(
                    "starter_probability"
                )
                is None
                and
                player.get(
                    "external_lineup_status"
                )
                in {
                    "DUDA",
                    "SUPLENTE",
                }
            )
        )
    ]

    probable_starters = sum(
        1

        for player in best_lineup

        if (
            (
                player.get(
                    "starter_probability"
                )
                is not None
                and
                str(
                    player.get(
                        "starter_consensus"
                    )
                    or ""
                ).upper()
                in {
                    "STARTER",
                    "STARTER_LEAN",
                }
            )
            or
            (
                player.get(
                    "starter_probability"
                )
                is None
                and
                player.get(
                    "external_lineup_status"
                )
                in {
                    "TITULAR",
                    "PROBABLE",
                }
            )
        )
    )


    return {
        "position_policy":
            POSITION_POLICY,

        "formation":
            selected_formation,

        "formation_name":
            best[
                "formation_name"
            ],

        "selected":
            best_lineup,

        "total_selected":
            len(
                best_lineup
            ),

        "complete":
            len(
                best_lineup
            )
            == 11,

        "playable_count":
            playable_count,

        "unavailable_count":
            len(
                unavailable_selected
            ),

        "unavailable_selected":
            unavailable_selected,

        "blocked_players":
            blocked_players,

        "matchday_shortages":
            matchday_shortages,

        # EL VALOR DEPORTIVO DEL ONCE, SIN EL BONO DEL DIOS.
        #
        # Lo leen `safe_debt_portfolio_engine` y el motor de
        # ofertas para medir cuanto se rompe el equipo con cada
        # venta, y esa medida tiene que seguir significando lo
        # mismo que ayer.
        "lineup_score":
            round(
                sum(
                    float(
                        p.get("lineup_score_sporting")
                        if p.get("lineup_score_sporting")
                        is not None
                        else p.get("lineup_score", 0.0)
                    )
                    for p in best_lineup
                ),
                2,
            ),

        # El que uso para elegir, con el bono dentro. Para poder
        # auditar la busqueda sin rehacerla.
        "lineup_score_with_mandatory":
            best[
                "score"
            ],

        "used_warning_players":
            best[
                "used_warning_players"
            ],

        "formation_candidates":
            formation_results,

        "lineup_intelligence":
            lineup_intelligence,

        "starter_intelligence":
            starter_intelligence,

        "starter_intelligence_version":
            starter_intelligence.get(
                "version"
            )
            if starter_intelligence
            else None,

        "external_source_state":
            lineup_intelligence.get(
                "source_state",
                "NOT_CONNECTED",
            ),

        "external_updated_at":
            lineup_intelligence.get(
                "updated_at"
            ),

        "external_matched_players":
            lineup_intelligence.get(
                "matched_players",
                0,
            ),

        "external_risk_selected":
            external_risk_selected,

        "probable_starter_count":
            probable_starters,

        # LA REGLA DEL DIOS, EN EL INFORME
        #
        # Un Dios que no aparece en el once tiene que tener una
        # linea que lo explique. Sin esto, la unica forma de
        # saber por que falta es reconstruir el score a mano,
        # que es exactamente lo que hubo que hacer con Yamal.
        "mandatory_hierarchy": {

            "in_lineup": [
                {
                    "id": p["id"],
                    "name": p.get("name"),
                }
                for p in best_lineup
                if p.get("mandatory_hierarchy")
            ],

            "ruled_out": [
                {
                    "id": p["id"],
                    "name": p.get("name"),
                    "reason": p.get(
                        "mandatory_hierarchy_reason"
                    ),
                }
                for p in players
                if p.get("mandatory_hierarchy_ruled_out")
            ],

            # Un Dios al 0 % que nadie explica: juega, pero se
            # canta.
            "unexplained": [
                {
                    "id": p["id"],
                    "name": p.get("name"),
                }
                for p in players
                if p.get("mandatory_hierarchy_unexplained")
            ],
        },
    }
