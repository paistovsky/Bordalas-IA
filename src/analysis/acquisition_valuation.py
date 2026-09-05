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

from src.analysis.market_rate_gate import (
    FALLING as FALLING_RATE_CODE,
    build_market_rates,
    evaluate as evaluate_market_rate,
)

from src.analysis.player_velocity_lookup import (
    build_velocity_lookup,
)

from src.analysis.deployment import (
    DEPLOYMENT_ENABLED,
    classify_operation,
    roster_fill_veto,
)

from src.analysis.route_confidence import (
    premium_confidence,
    streak_confidence,
    value_with_confidence_on_gain,
)

from src.analysis.computer_resale_premium import (
    measure_computer_resale_premium,
    usable_premium,
)

from src.analysis.player_value_engine import (
    build_team_strength,
    calibrate_points_market,
    computer_resale_value,
    estimate_season_points,
    speculation_value,
    xi_upgrade_value,
)


# Horizonte por defecto para valorar una reventa.
#
# Tres dias es lo que suele tardar el mercado en digerir una
# jornada. Mas alla la proyeccion de precio ya no dice gran cosa.
DEFAULT_SPECULATION_HORIZON = 3


# Cuanto se cuenta del titular que sale, al valorar el cambio.
#
# El Computer hace oferta por todo jugador publicado en cada
# reset, y en la ultima tanda observada pago entre -0,6 % y
# +4,5 % del precio de mercado. Se cuenta el 80 % igualmente: el
# dinero llega en el reset y no hoy, y el precio puede moverse.
#
# Subirlo hace a Pepe mas agresivo fichando; bajarlo lo vuelve a
# paralizar. A cero -como estuvo del 19 al 21/08- no puede
# mejorar el once nunca.
RECUPERACION_TITULAR = 0.80


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

    # Cuanto paga el Computer por encima del mercado. Se mide una
    # vez por ciclo, como el resto: leer el tablon entero por cada
    # candidato seria absurdo.
    computer_premium: dict | None = None,

    # El ritmo observado por jugador. Sin el, la via especulativa
    # no valora: ver `market_rate_gate`.
    market_rates: dict | None = None,

    # Cuantas fichas de plantilla estan vacias. Sin huecos, la
    # via de relleno no se abre.
    free_roster_slots: int | None = None,
    rival_intelligence: dict | None = None,
    current_user_id=None,
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

    # EL RITMO OBSERVADO DE CADA JUGADOR (08/09/2026)
    #
    # Se lee del informe del ojeador, que esta en disco: quien
    # sale a la calle es el ciclo, cada seis horas. Se carga una
    # vez y se reparte, como el resto de lookups.
    if market_rates is None:
        market_rates = build_market_rates()

    # LAS FICHAS LIBRES (10/09/2026)
    #
    # Se reutiliza `roster_expansion_shadow.count_free_slots`,
    # que lleva calculandolo en sombra desde el 05/09 y que ya
    # trae la honestidad puesta: el tope real de plantilla de
    # Biwenger NO esta en el codigo ni comprobado, asi que se
    # cuenta contra la plantilla mas grande de la liga y el
    # resultado es una COTA INFERIOR.
    #
    # Blindado: sin ledger de rivales, cero huecos y la via de
    # relleno no se abre. Que es lo correcto — no inventarse un
    # hueco es mejor que fichar contra uno que no existe.
    if free_roster_slots is None:

        try:
            from src.analysis.roster_expansion_shadow import (
                count_free_slots,
            )
            from src.analysis.rival_ledger_audit import (
                audit_rival_ledger,
            )

            free_roster_slots = safe_int(
                count_free_slots(
                    {
                        "by_manager": [
                            {**datos, "is_us": datos.get("is_us")}
                            for datos in (
                                (
                                    audit_rival_ledger(
                                        rival_intelligence,
                                        own_user_id=current_user_id,
                                    ).get("by_manager")
                                    or {}
                                ).values()
                            )
                        ]
                    }
                ).get("free_slots")
            )

        except Exception:                           # noqa: BLE001
            free_roster_slots = 0

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

    # LA SEGUNDA VIA DE REVENTA (21/08/2026)
    #
    # Si falla, sale sin calibrar y esa via queda cerrada. Nunca
    # tumba el ciclo por no poder leer el tablon.
    if computer_premium is None:
        try:
            computer_premium = measure_computer_resale_premium()

        except Exception as error:
            computer_premium = {
                "available": False,
                "calibrated": False,
                "median_percent": None,
                "reason": f"{type(error).__name__}: {error}",
            }

    return {
        "velocity": velocity_lookup or {},
        "market_rates": market_rates or {},
        "free_roster_slots": safe_int(free_roster_slots),
        "starter": starter_lookup,
        "points_market": mercado,
        "team_strength": equipos,
        "computer_premium": computer_premium,
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

        # ==================================================
        # MEJORAR EL ONCE ES QUITARLE EL SITIO A ALGUIEN DEL
        # ONCE (20/08/2026)
        # ==================================================
        #
        # El dueño tuvo que intervenir a mano: Pepe habia
        # acumulado CATORCE defensas. "No se que le ha dado con
        # los defensas, ficha muchos."
        #
        # Le habia dado esto. El sustituido se elegia entre toda
        # la plantilla de la posicion, y con nueve defensas el
        # que mas diferencia de puntos daba era siempre el PEOR,
        # que es un suplente que no juega. De ahi salian fichas
        # como estas, de su propio tablero:
        #
        #     Lucas Noubi   sustituye a Yeray            +109 pts
        #     Alvaro Nuñez  sustituye a Yusi Enriquez     +15 pts
        #
        # Yeray y Yusi son suplentes. Fichar a esos dos no habria
        # cambiado ni un nombre del once que sale el sabado, y el
        # motor lo contaba como mejora del once y pagaba por
        # ello.
        #
        # Y se realimentaba: compras un defensa porque el peor es
        # malo, ahora tienes diez, el peor sigue siendo malo,
        # compras otro. Los defensas son los mas abundantes y
        # baratos del mercado, asi que munición nunca falta.
        #
        # LA REGLA CORRECTA
        #
        #     Un fichaje mejora el once si le quita el sitio a
        #     alguien DEL once. El sustituido es el peor TITULAR
        #     de esa posicion -el unico que perderia su puesto de
        #     verdad-, no el peor de la plantilla.
        #
        #     Si el candidato no llega a ese, no es una mejora
        #     del once: es fondo de armario, y vale lo que valga
        #     su reventa. Esa via sigue abierta mas abajo, en la
        #     especulacion.
        #
        # De paso desaparece el bucle sin prohibir nada: contra
        # un titular de verdad, la mayoria de esos defensas ya no
        # cualifican solos.

        plantel_pos = (
            (context or {}).get("squad_by_position") or {}
        ).get(posicion) or []

        titulares_pos = [
            jugador
            for jugador in plantel_pos
            if jugador and jugador.get("in_lineup")
        ]

        if titulares_pos:
            # El que perderia el puesto: el titular mas flojo.
            candidatos_a_salir = [
                min(
                    titulares_pos,
                    key=lambda j: safe_int(j.get("points")),
                )
            ]

        else:
            # Sin titulares en esa posicion, cualquiera que
            # entre juega. Ahi el peor de la plantilla si es el
            # sustituido real.
            peor = (
                min(
                    plantel_pos,
                    key=lambda j: safe_int(j.get("points")),
                )
                if plantel_pos
                else peores.get(posicion)
            )

            candidatos_a_salir = [peor] if peor else []

        como_xi = None
        descartes = []

        for sustituido in candidatos_a_salir:

            if sustituido is None:
                continue

            titular = bool(sustituido.get("in_lineup"))

            # EL TITULAR QUE SALE TAMBIEN VALE DINERO
            # (21/08/2026)
            #
            #     "Lo que quiero ver es si Pepe pelea las pujas
            #      por jugadores que mejoren el XI."
            #
            # No las peleaba. Cero pujas de veinte candidatos,
            # dias seguidos, y no era prudencia: era aritmetica
            # imposible.
            #
            # Desde el 19/08, al cambiar un TITULAR se ponia
            # `recuperado = 0`: el dinero del que sale no contaba.
            # Asi la cuenta quedaba en
            #
            #     mejora marginal   vs   precio entero
            #
            # y una mejora marginal NUNCA supera un precio
            # entero. No es que compensara pocas veces: es que no
            # podia compensar nunca. Affengruber, 90 % titular y
            # Clave, costaba 3,74 M y aportaba 2,13 M sobre
            # Yeray. NO COMPENSA. Y Yeray, que valia 1,85 M,
            # contaba como cero.
            #
            # La operacion real es comprar Y vender:
            #
            #     pagas ..........  3,74 M
            #     recuperas ......  1,85 M
            #     coste neto .....  1,89 M   <  2,13 M de mejora
            #
            # POR QUE AHORA SI SE PUEDE CONTAR
            #
            #     Porque vender dejo de ser una incognita. En cada
            #     reset el Computer hace oferta por TODO jugador
            #     publicado -lo dice nuestra propia linea
            #     temporal-, asi que el riesgo no es quedarse
            #     pegado con el saliente: es cobrar algo menos.
            #
            #     Un riesgo de precio se cubre con un descuento.
            #     Uno de liquidez, no. Antes se cubria el
            #     equivocado, y con el descuento maximo posible:
            #     contar cero.
            #
            # EL DESCUENTO
            #
            #     Las ofertas observadas del Computer rondan el
            #     precio de mercado -en la ultima tanda, entre
            #     -0,6 % y +4,5 %-. Aun asi se cuenta el 80 %, y a
            #     proposito: el dinero llega en el reset, no hoy,
            #     y el precio puede moverse. Si el cambio solo
            #     sale a favor con el precio de escaparate, no
            #     sale.
            recuperado = 0

            if assume_replacement_sold:

                recuperado = int(
                    safe_int(sustituido["price"])
                    * (
                        1.0
                        if not titular
                        else RECUPERACION_TITULAR
                    )
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

            # `xi_upgrade_value` no se etiqueta: sin `route` no se
            # puede decir que via gana ni de que bolsillo sale.
            intento.setdefault("route", "XI_UPGRADE")

            # SIGUE HACIENDO FALTA VENDER (21/08/2026)
            #
            # La condicion era `recuperado == 0`, que dejo de
            # cumplirse en cuanto el saliente empezo a contar. Y
            # el aviso hace mas falta que antes: ahora la puja se
            # apoya en ese dinero, asi que la venta no es un
            # detalle, es parte de la operacion.
            if titular:
                intento["needs_sale_first"] = True
                intento["recovered_value"] = recuperado
                intento["recovered_from"] = sustituido.get("name")

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
        # COMO FICHA VACIA (10/09/2026)
        # --------------------------------------------------
        #
        # Pepe tiene 14 fichas de 17: tres huecos que no puntuan.
        # Cuando hay hueco, el candidato no le quita el sitio a
        # nadie, asi que se le compara contra el CERO de la ficha
        # vacia en vez de contra un titular.
        #
        # Sin el veto de "no mejora el once" -no esta desplazando
        # a nadie- pero CON los que si tocan: jerarquia minima,
        # titularidad y disponibilidad. Ese filtro es lo que corta
        # el bucle de las catorce defensas, avisado el 05/09.

        huecos = safe_int((context or {}).get("free_roster_slots"))

        como_relleno = None

        if huecos > 0:

            veto = roster_fill_veto(titularidad)

            if veto:
                como_relleno = _sin_valor("FICHA_NO_APTA", veto)

            else:
                como_relleno = xi_upgrade_value(
                    candidate_points=estimacion["points"],

                    # Contra el hueco: una ficha vacia aporta cero.
                    replaced_points=0,

                    points_market=mercado,
                    confidence=estimacion["confidence"],

                    # No sale nadie, asi que no se recupera nada.
                    recovered_value=0,

                    candidate_starter=titularidad,

                    # EL HUECO ES UN DATO, NO UNA INCOGNITA
                    #
                    #     `xi_upgrade_value` exige pronostico DEL
                    #     QUE SALE, y con `None` veta con
                    #     SIN_PRONOSTICO: es un guardarrail contra
                    #     fichar a ciegas y esta bien puesto.
                    #
                    #     Pero de un hueco no se ignora nada: una
                    #     ficha vacia juega el 0 % de los minutos,
                    #     con certeza. Se le pasa esa señal, que
                    #     es la verdad, en vez de un hueco de
                    #     informacion que dispararia un veto
                    #     pensado para otra cosa.
                    replaced_starter={
                        "probability": 0.0,
                        "hierarchy_value": 0,
                        "hierarchy_label": "FICHA VACIA",
                    },

                    matchday=(titularidad or {}).get("matchday"),
                    replaced_in_lineup=False,
                )

                como_relleno["route"] = "ROSTER_FILL"
                como_relleno["free_slots"] = huecos

        # --------------------------------------------------
        # COMO ESPECULACION
        # --------------------------------------------------

        velocidades = (context or {}).get("velocity") or {}

        velocidad = velocidades.get(
            safe_int(player.get("id"))
        )

        # ==================================================
        # FRENO Y ACELERADOR (08/09/2026)
        # ==================================================
        #
        # El ritmo que se proyecta es el OBSERVADO del jugador, y
        # si no lo hay, no se especula. Ver `market_rate_gate`
        # para las tres reglas y los numeros que las sostienen.
        #
        # Se calculan las dos valoraciones -la de antes y la de
        # ahora- porque este cambio mueve dinero de verdad y el
        # dueño tiene que poder ver que cambia antes de que se
        # gaste un euro. Las dos son aritmetica pura: no cuesta
        # nada tenerlas.

        compuerta = evaluate_market_rate(
            player.get("id"),
            (context or {}).get("market_rates"),
        )

        # LO QUE SE HACIA ANTES, para poder compararlo.
        antes_trading = speculation_value(
            price=precio,
            daily_increment=safe_int(
                player.get("priceIncrement")
            ),
            horizon_days=horizon_days,
            confidence=estimacion["confidence"],
            velocity_percent_per_day=velocidad,
        )

        if compuerta["allow"]:

            como_trading = speculation_value(
                price=precio,
                daily_increment=safe_int(
                    player.get("priceIncrement")
                ),
                horizon_days=horizon_days,
                confidence=estimacion["confidence"],

                # EL ACELERADOR. Ya no es el incremento de ayer ni
                # una velocidad de respaldo: es el ritmo que tres
                # webs han observado en este jugador.
                velocity_percent_per_day=compuerta[
                    "rate_percent_per_day"
                ],
            )

        else:
            # SI LA VIA YA SE CERRABA SOLA, MANDA SU MOTIVO
            #
            #     La compuerta explica por que no se especula con
            #     este jugador. Pero si la via ya decia que no por
            #     algo suyo -precio invalido, sin revalorizacion-
            #     ese motivo es mas concreto y no se pisa: tapar
            #     un "por que" bueno con otro peor no arregla
            #     nada, y se descubrio porque una guardia salto.
            como_trading = (
                antes_trading
                if safe_int(antes_trading.get("value")) <= 0
                else _sin_valor(
                    compuerta["code"],
                    compuerta["reason"],
                )
            )

        # --------------------------------------------------
        # COMO REVENTA AL COMPUTER
        # --------------------------------------------------
        #
        # La otra forma de ganar dinero con una reventa: no que el
        # jugador suba, sino que el Computer pague por encima del
        # mercado por cualquier cosa publicada.
        #
        # Hasta el 21/08 esta via no existia, y por eso 15 de 20
        # candidatos salian SIN VALOR: no eran malos, es que solo
        # se les preguntaba si iban a subir.
        #
        # Cerrada mientras la prima no este medida con muestras
        # suficientes. `usable_premium` devuelve None y de un None
        # no sale una compra.

        antes_reventa = computer_resale_value(
            price=precio,
            premium=usable_premium(
                (context or {}).get("computer_premium")
            ),
        )

        # AQUI SOLO FRENA EL PRECIO QUE CAE, Y NO LO DEMAS
        #
        #     Esta via es la que ganaba en 21 de los 22 candidatos
        #     del 04/09, y su premium es una medida de MERCADO: la
        #     misma para todos por construccion. Por eso Nico
        #     Guillen valia precio x 1,0132 mientras se desplomaba
        #     un 2,33 % diario.
        #
        #     PERO NO APUESTA A QUE EL JUGADOR SUBA. Apuesta a que
        #     el Computer paga por encima del mercado en el reset.
        #     Son dos tesis distintas:
        #
        #       - la de tendencia necesita un ritmo que proyectar,
        #         y sin ritmo no se valora;
        #       - esta no proyecta nada, asi que exigirle un ritmo
        #         seria importarle una dependencia que no tiene, y
        #         apagaria una via de ingresos entera para mas de
        #         la mitad del tablero solo porque el ojeador no
        #         empareja a ese jugador.
        #
        #     Lo que si la frena es que el precio VENGA CAYENDO:
        #     el Computer paga sobre el precio de mercado del
        #     reset, y sobre una base que encoge el premium vale
        #     menos. Eso es comprar un cuchillo cayendo con otro
        #     nombre.
        #
        #     Lo destapo una guardia -`test_reventa_al_computer_v1`-
        #     que se puso en rojo al frenar esta via por falta de
        #     ritmo. Tenia razon ella.
        if compuerta["code"] != FALLING_RATE_CODE:
            como_reventa = antes_reventa

        else:
            # Si la via ya se cerraba sola -prima sin medir-, ese
            # motivo es mas concreto y no se pisa.
            como_reventa = (
                antes_reventa
                if safe_int(antes_reventa.get("value")) <= 0
                else _sin_valor(
                    compuerta["code"],
                    compuerta["reason"],
                )
            )

        # --------------------------------------------------
        # LA MAYOR DE LAS TRES
        # --------------------------------------------------

        # ==================================================
        # CADA APUESTA CON SU CONFIANZA (09/09/2026)
        # ==================================================
        #
        # EN SOMBRA. Se calcula al lado y NO decide: el motor
        # sigue con el esquema de arriba. Aqui solo se responde a
        # "¿que pasaria si cada via llevase la confianza de lo que
        # de verdad apuesta?".
        #
        #   tendencia -> la de la RACHA, que es la continuacion
        #                medida el 07/09
        #   Computer  -> la del PREMIUM, que falla una de cada
        #                cuatro veces y hoy no lleva descuento
        #   el once   -> la de los puntos, sin tocar: ahi la
        #                confianza de puntos SI es la que toca

        conf_racha, base_racha = streak_confidence(
            compuerta.get("trend_days"),
            compuerta.get("sources"),
        )

        conf_prima, base_prima = premium_confidence(
            (context or {}).get("computer_premium")
        )

        # LA CONFIANZA VA SOBRE LA GANANCIA, NO SOBRE EL CAPITAL
        #
        #     Al calcular esto salio que TODAS las vias caian a
        #     cero, y el motivo no era el numero sino donde se
        #     multiplica. Hoy el motor hace:
        #
        #         maximo = (objetivo - ganancia x margen) x confianza
        #
        #     que multiplica el precio ENTERO. Con la via del
        #     Computer, cuya ventaja es del 1,76 %, una confianza
        #     de 0,72 deja el maximo por debajo del propio precio.
        #
        #     Pero el principal no esta en riesgo: si la apuesta
        #     falla sigues teniendo un jugador que vale lo que
        #     vale. Lo incierto es la GANANCIA. Ver
        #     `route_confidence.value_with_confidence_on_gain`.
        #
        #     Esto se hace SOLO en la sombra. Cambiar la semantica
        #     del motor mueve dinero y lo decide el dueño.

        if compuerta["allow"]:

            pleno_trading = speculation_value(
                price=precio,
                daily_increment=safe_int(
                    player.get("priceIncrement")
                ),
                horizon_days=horizon_days,
                confidence=1.0,
                velocity_percent_per_day=compuerta[
                    "rate_percent_per_day"
                ],
            )

            sombra_trading = {
                **pleno_trading,

                # `speculation_value` no se etiqueta a si misma, y
                # sin etiqueta la sombra no puede decir que via
                # gana — que es toda la pregunta.
                "route": "PRICE_TREND",

                "value": value_with_confidence_on_gain(
                    precio,
                    pleno_trading.get("expected_gain"),
                    conf_racha,
                ),
                "confidence": conf_racha,
                "confidence_basis": base_racha,
            }

        else:
            sombra_trading = como_trading

        if compuerta["code"] != FALLING_RATE_CODE:

            pleno_reventa = computer_resale_value(
                price=precio,
                premium=usable_premium(
                    (context or {}).get("computer_premium")
                ),
            )

            sombra_reventa = {
                **pleno_reventa,
                "value": value_with_confidence_on_gain(
                    precio,
                    pleno_reventa.get("expected_gain"),
                    conf_prima if conf_prima is not None else 0.0,
                ),
                "confidence": conf_prima,
                "confidence_basis": base_prima,
            }

        else:
            sombra_reventa = como_reventa

        sombra_opciones = [
            o for o in (como_xi, sombra_trading, sombra_reventa)
            if o and safe_int(o.get("value")) > 0
        ]

        sombra_mejor = (
            max(sombra_opciones, key=lambda o: safe_int(o.get("value")))
            if sombra_opciones
            else None
        )

        # ==================================================
        # LA CLASE DE OPERACION, Y DE QUE BOLSILLO SALE
        # ==================================================
        #
        # El `intent` salia de la via que diera MAS EUROS, no de
        # que clase de operacion era. Como la reventa al Computer
        # ganaba en 21 de 22, los 22 salian SPECULATION y se
        # median contra los 3,5 M de especular mientras los 8,5 M
        # de fichar seguian intactos.
        #
        # Bajo interruptor: con `DEPLOYMENT_ENABLED` apagado esto
        # se calcula, se publica y NO manda.

        clase = classify_operation(
            como_xi,
            como_relleno,
            como_trading,
            como_reventa,
        )

        despliegue = {
            **clase,
            "free_roster_slots": huecos,
            "roster_fill_value": safe_int(
                (como_relleno or {}).get("value")
            ),
            "roster_fill_decision": (
                (como_relleno or {}).get("decision")
                or (como_relleno or {}).get("route")
            ),
            "enabled": DEPLOYMENT_ENABLED,
            "observer_only": not DEPLOYMENT_ENABLED,
        }

        # La via que gana HOY. Se calcula aqui, antes de la
        # comparacion, porque la comparacion la necesita.
        # CON EL INTERRUPTOR APAGADO, LA LISTA ES LA DE SIEMPRE.
        # La via de ficha vacia se calcula igual -para poder
        # publicarla- pero no entra a competir.
        opciones_hoy = [
            o
            for o in (
                (como_xi, como_relleno, como_trading, como_reventa)
                if DEPLOYMENT_ENABLED
                else (como_xi, como_trading, como_reventa)
            )
            if o and safe_int(o.get("value")) > 0
        ]

        mejor_actual = (
            max(opciones_hoy, key=lambda o: safe_int(o.get("value")))
            if opciones_hoy
            else None
        )

        # LA COMPARACION, PARA QUE SE PUEDA VER EL CAMBIO
        #
        #     `before` es lo que Pepe habria valorado ayer con las
        #     mismas cuentas; `after`, lo que vale hoy. La
        #     diferencia es exactamente lo que introduce esta
        #     noche, y sale al dashboard fila a fila.
        antes_opciones = [
            o for o in (como_xi, antes_trading, antes_reventa)
            if o and safe_int(o.get("value")) > 0
        ]

        antes_mejor = (
            max(antes_opciones, key=lambda o: safe_int(o.get("value")))
            if antes_opciones
            else None
        )

        comparacion = {
            "gate": compuerta["code"],
            "gate_reason": compuerta["reason"],
            "rate_percent_per_day": compuerta.get(
                "rate_percent_per_day"
            ),
            "trend_days": compuerta.get("trend_days"),
            "demand_net": compuerta.get("demand_net"),

            "value_before": (
                safe_int(antes_mejor.get("value"))
                if antes_mejor
                else 0
            ),
            "intent_before": (
                antes_mejor.get("intent") if antes_mejor else None
            ),
        }

        # La via que gana HOY, con nombre. Misma razon: sin
        # etiqueta no se puede comparar con la de la sombra.
        ruta_hoy = (
            (
                mejor_actual.get("route")
                or (
                    "XI_UPGRADE"
                    if mejor_actual.get("intent") == "XI_UPGRADE"
                    else "PRICE_TREND"
                )
            )
            if mejor_actual
            else None
        )

        comparacion["route_now"] = ruta_hoy

        # EL ESQUEMA NUEVO, AL LADO Y SIN MANDAR
        confianza_sombra = {
            "streak_confidence": conf_racha,
            "streak_basis": base_racha,
            "premium_confidence": conf_prima,
            "premium_basis": base_prima,

            "value": (
                safe_int(sombra_mejor.get("value"))
                if sombra_mejor
                else 0
            ),
            "route": (
                (
                    sombra_mejor.get("route")
                    or (
                        "XI_UPGRADE"
                        if sombra_mejor.get("intent") == "XI_UPGRADE"
                        else "PRICE_TREND"
                    )
                )
                if sombra_mejor
                else None
            ),
            "intent": (
                sombra_mejor.get("intent") if sombra_mejor else None
            ),

            # Lo que cada via valdria con su confianza propia.
            "speculation_value": safe_int(
                (sombra_trading or {}).get("value")
            ),
            "computer_resale_value": safe_int(
                (sombra_reventa or {}).get("value")
            ),
            "xi_value": safe_int((como_xi or {}).get("value")),

            "observer_only": True,
        }

        opciones = opciones_hoy

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
            if como_reventa:
                motivos.append(
                    f"como reventa al Computer, "
                    f"{como_reventa.get('decision', '?')}"
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
                as_computer_resale=como_reventa,
                starter=titularidad,
                market_gate=comparacion,
                confidence_shadow=confianza_sombra,
                deployment=despliegue,
                as_roster_fill=como_relleno,
            )

        mejor = max(
            opciones,
            key=lambda o: safe_int(o.get("value")),
        )

        return {
            "value": safe_int(mejor["value"]),

            # EL BOLSILLO. Con el interruptor encendido lo decide
            # la CLASE de operacion; apagado, la via que dio mas
            # euros, que es lo que se hacia hasta hoy.
            "intent": (
                clase["intent"]
                if DEPLOYMENT_ENABLED and clase["intent"]
                else mejor.get("intent")
            ),
            "decision": "VALUED",
            "market_price": precio,
            "points": estimacion,
            "starter": titularidad,
            "as_xi": como_xi,
            "as_speculation": como_trading,
            "as_computer_resale": como_reventa,

            # Por que via se valora. Sin esto, una compra para
            # revenderle al Computer se leeria en pantalla igual
            # que una para mejorar el once.
            "route": mejor.get("route"),

            # Lo que decidia antes y lo que decide ahora, con el
            # motivo. Esto mueve dinero: tiene que poder mirarse.
            "market_gate": comparacion,

            # Que valdria con cada via llevando SU confianza.
            # Observador puro: el `value` de arriba no lo mira.
            "confidence_shadow": confianza_sombra,

            # Que clase de operacion es, de que bolsillo sale y
            # cuanto valdria llenando una ficha vacia.
            "deployment": despliegue,
            "as_roster_fill": como_relleno,

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
    as_computer_resale: dict | None = None,
    starter: dict | None = None,
    market_gate: dict | None = None,
    confidence_shadow: dict | None = None,
    deployment: dict | None = None,
    as_roster_fill: dict | None = None,
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
        "as_computer_resale": as_computer_resale,
        "market_gate": market_gate,
        "confidence_shadow": confidence_shadow,
        "deployment": deployment,
        "as_roster_fill": as_roster_fill,
        "reasons": [reason],
    }
