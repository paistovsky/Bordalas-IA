from __future__ import annotations

# El precio del punto vive en un solo sitio. Si algun dia
# Biwenger cambia el abono, cambia ahi y cambia en todas partes.
from src.analysis.rival_intelligence_engine import EUROS_POR_PUNTO

"""
Que hay en el mercado, cuanto vale y cuanto pujariamos.

POR QUE ESTA AQUI Y NO EN TELEMETRIA

    Este tablero vivia dentro de `dashboard_state`, es decir,
    dentro del codigo que pinta pantallas. Y ahi se quedaba: el
    ciclo ejecutaba otra lista, la del scoring antiguo.

    El 16/08/2026 eso se vio desde fuera. El dashboard proponia
    cuatro pujas -Yusi, Castrin, Arriaga, Cabrera- y en Biwenger
    habia una sola puja viva, por Iker Munoz, que no estaba en la
    lista. Dos motores, y ejecutaba el que no se ve.

    Un motor de decision no puede vivir en la capa de
    presentacion. Aqui puede usarlo tanto quien pinta como quien
    decide, que es el requisito para que dejen de ser dos.

NO CAMBIA NADA POR SI SOLO

    Este fichero es un traslado, no un cambio de comportamiento.
    Conectarlo al ciclo es el paso siguiente y toca la ruta que
    escribe en Biwenger.
"""

from src.analysis.deployment import (
    DEPLOYMENT_ENABLED,
    PURE_SPECULATION,
)

from src.analysis.bid_jitter import apply_bid_jitter
from src.analysis.los_dos_techos import los_dos_techos

from src.analysis.hold_budget import hold_cap, hold_pocket

from src.analysis.acquisition_budget import (
    budget_for_intent,
)

from src.analysis.acquisition_valuation import (
    build_valuation_context,
    value_candidate,
)

from src.analysis.bid_exposure_engine import (
    build_bid_exposure,
)

from src.analysis.historical_price_lookup import (
    build_historical_price_lookup,
)

from src.analysis.intelligent_bid_engine import (
    build_market_seller_lookup,
)

from src.analysis.rival_bid_model import (
    PRIMA_DE_EQUILIBRIO,
    PRIMA_MAXIMA_DE_PUJA,
    build_bid_model,
    optimal_bid,
)


# ============================================================
# EL MERCADO DE LOS RIVALES: VERLO SIN PODER COMPRARLO
# ============================================================
#
# EL SINTOMA (24/09/2026)
#
#     El dueño pregunto "cuantos jugadores se pueden comprar
#     hoy" y la pantalla dijo veinte. Eran cuarenta y siete.
#     Los otros veintisiete los vendian managers, y un filtro
#     nuestro -no de Biwenger- los tiraba antes de mirarlos.
#
#     Peor que esconderlos: al no crearles fila, nadie les
#     pedia nunca el ritmo ni la racha. Del 56 % del escaparate
#     no se sabia absolutamente nada, y "no se sabe" se leia
#     como "no hay".
#
# LO QUE CAMBIA, Y LO QUE NO
#
#     CAMBIA: entran en la tabla, con el nombre de quien vende,
#     lo que pide, su ritmo y su racha. Y se valoran con el
#     MISMO codigo que los del Computer -no un camino paralelo-,
#     porque un numero calculado aparte no sirve para decidir
#     si merece la pena abrir esta puerta de verdad.
#
#     NO CAMBIA: no se compran. La puerta se cierra en UN solo
#     sitio, al final y despues de valorar, para que la fila
#     publique lo que HABRIA decidido -`would_be_decision`- sin
#     que eso pueda ejecutarse nunca.
#
# POR QUE VALORAR Y LUEGO CERRAR, Y NO CORTAR ANTES
#
#     Porque la pregunta que paga las noches es "cuantos
#     pasarian el liston", y solo la responde el camino de
#     produccion entero. Cortar antes daria una tabla bonita y
#     ningun numero.
#
# LO QUE NO ESTA GARANTIZADO AQUI (y si con el Computer)
#
#     Al Computer se le compra al precio pedido. A un manager
#     se le OFRECE, y acepta o no. La salida sigue valiendo
#     -una vez el jugador es nuestro da igual a quien se le
#     compro-, pero la ENTRADA no. De la tasa de aceptacion
#     tenemos una sola observacion, y con una no se abre nada.
#
# EL INTERRUPTOR
#
#     `BORDALAS_SIN_MERCADO_RIVALES=1` devuelve el filtro de
#     antes: la tabla vuelve a ser solo el mercado del
#     Computer. Una linea, como todo lo demas.
DISABLE_ENV = "BORDALAS_SIN_MERCADO_RIVALES"


# La decision que llevan las filas de rivales que no se pueden
# comprar. Cualquier cosa distinta de BID las mantiene fuera de
# `best_acquisition_target`; se le da nombre propio para que la
# pantalla no las confunda con un rechazo por valor.
MERCADO_DE_RIVAL = "MERCADO_DE_RIVAL"


# Un estado que no llego. No es "ok" y no es una dolencia:
# es la ausencia del dato, y se llama por su nombre.
ESTADO_DESCONOCIDO = "desconocido"

def _mercado_de_rivales_visible() -> bool:
    """
    Si los mercados de otros managers entran en la tabla.

    Encendido por defecto. Verlos no compra nada.
    """

    import os

    return str(
        os.environ.get(DISABLE_ENV, "")
    ).strip().lower() not in {"1", "true", "si", "yes"}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _se_paga_solo(cost_per_point) -> bool | None:
    """¿El abono cubre el fichaje?

    None cuando no se puede decir: sin coste por punto no hay
    respuesta, y un `False` ahi seria una respuesta inventada.
    """

    if cost_per_point is None:
        return None

    try:
        coste = float(cost_per_point)
    except (TypeError, ValueError):
        return None

    if coste <= 0:
        return None

    return coste < EUROS_POR_PUNTO


def _resumen_de_los_techos(filas) -> dict:
    """
    Cuantas pujas pasan del techo del comerciante, POR VIA.

    Forma fija. Nunca lanza. No decide: cuenta.
    """

    salida = {
        "available": False,
        "revender": 0,
        "quedarse": 0,
        "sin_via": 0,
        "con_tope_aplicado": 0,
        "pasan_el_del_comerciante": [],
        "reason": None,
    }

    try:
        pasan = []

        # REGLA 24: "ninguna pasa el techo" y "ninguna tiene tope
        # aplicado" son dos cosas distintas, y la segunda no
        # prueba nada. Se cuentan aparte.
        con_tope = 0

        por_via = {"REVENDER": 0, "QUEDARSE": 0, None: 0}

        for fila in filas or []:

            techos = (fila or {}).get("los_dos_techos") or {}

            if not techos.get("available"):
                continue

            via = techos.get("via")

            por_via[via if via in por_via else None] += 1

            comerciante = (
                techos.get("comerciante") or {}
            ).get("techo")

            aplicado = techos.get("aplicado")

            if aplicado:
                con_tope += 1

            if (
                comerciante
                and aplicado
                and aplicado > comerciante
            ):
                pasan.append(
                    {
                        "name": fila.get("name"),
                        "via": via,
                        "aplicado": aplicado,
                        "techo_del_comerciante": comerciante,
                        "de_mas": aplicado - comerciante,
                    }
                )

        return {
            "available": True,
            "revender": por_via["REVENDER"],
            "quedarse": por_via["QUEDARSE"],
            "sin_via": por_via[None],
            "con_tope_aplicado": con_tope,
            "pasan_el_del_comerciante": pasan,
            "reason": (
                f"{por_via['QUEDARSE']} para quedarse y "
                f"{por_via['REVENDER']} para revender. "
                + (
                    "Ninguna lleva tope aplicado en esta vuelta, "
                    "asi que no se puede decir si alguna lo "
                    "pasaria."
                    if not con_tope
                    else (
                        f"De las {con_tope} con tope aplicado, "
                        f"{len(pasan)} van por encima del techo "
                        f"del comerciante."
                    )
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo resumir los techos: "
                f"{type(error).__name__}: {error}"
            ),
        }


def build_acquisition_board(
    snapshot: dict,
    rival_intelligence: dict,
    current_user_id,
    available_budget: int | None,
    limit: int = 60,
    acquisition_budget: int | None = None,
) -> dict:
    """
    Que hay en el mercado del Computer, cuanto vale para nosotros y
    cuanto pujariamos.

    Es la vista que responde a "que va a hacer Pepe hoy". Antes no
    existia: el panel de especulacion solo mostraba nombres y
    scores, sin decir cuanto ni por que.

    DOS PRESUPUESTOS, NO UNO (21/08/2026)

        `available_budget` es el de ESPECULAR: el 15 % de la caja
        mas el 60 % del margen de deuda. `acquisition_budget` es
        el de FICHAR: la caja entera mas el margen entero, con el
        techo de Biwenger.

        Cada fila usa el suyo segun su `intent`. Antes las dos
        vias pasaban por el estrecho, y por eso un candidato de
        2,58 M salia SUPERA_PRESUPUESTO teniendo 13 M de puja
        maxima.

        Si no se pasa el de fichajes se sigue usando el viejo:
        peor, pero igual que ayer.
    """

    try:
        # EL ONCE, PARA SABER A QUIEN SE PUEDE TOCAR BARATO
        #
        # Sin el, nadie cuenta como titular y los cambios sobre el
        # once se valorarian con las reglas del suplente, que son
        # mucho mas blandas. Si el motor del once falla se sigue
        # sin el: no habra titulares y solo se propondran cambios
        # sobre el peor de cada posicion, que es exactamente lo
        # que se hacia hasta hoy.
        try:
            from src.analysis.lineup_engine import build_lineup

            once = build_lineup(snapshot)

        except Exception:
            once = None

        contexto = build_valuation_context(
            snapshot,
            lineup=once,

            # Para contar las fichas libres: el tamaño de
            # plantilla sale del ledger de rivales, que es
            # quien sabe cuantos jugadores tiene cada uno.
            rival_intelligence=rival_intelligence,
            current_user_id=current_user_id,
        )

        # LA CONCENTRACION DE HOY (10/09/2026)
        #
        # Yamal son el 41 % de la plantilla. Mientras Pepe no
        # compraba eso era una foto; en cuanto despliegue caja,
        # cada compra decide si se concentra mas o se reparte.
        #
        # Blindado: sin plantilla no acota nada.
        try:
            from src.analysis.concentration_guardrail import (
                build_concentration,
                check_purchase,
            )

            concentracion = build_concentration(
                snapshot.get("my_team")
            )

        except Exception:                           # noqa: BLE001
            concentracion = {"available": False}
            check_purchase = None

        catalogo = {
            safe_int(item.get("id")): item
            for item in (
                (
                    (snapshot.get("catalog") or {}).get("data") or {}
                ).get("players") or {}
            ).values()
            if isinstance(item, dict)
        }

        modelo = build_bid_model(
            rival_intelligence,
            # Precio de aquel momento, no el de hoy.
            price_lookup=build_historical_price_lookup(),
            own_user_id=current_user_id,
        )

        vendedores = build_market_seller_lookup(snapshot)

        # LO QUE YA HEMOS PUJADO
        #
        # El tablero decia "0 CON PUJA" con tres pujas vivas en
        # Biwenger por 3.126.002 EUR. El contador de la caja SI
        # las veia; esta tabla no, porque nunca se le paso el
        # dato. Y la columna se llamaba PUJAMOS, que es lo que
        # cualquiera entiende por "tenemos una puja puesta"
        # cuando en realidad ensenaba la puja *recomendada*.
        #
        # Aqui entra el hecho: cuanto hay puesto, por quien.
        exposicion = build_bid_exposure(
            snapshot,
            own_user_id=current_user_id,
        )

        puja_viva = {}
        contraparte = {}

        for operacion in (exposicion.get("operations") or []):
            for jugador in (operacion.get("player_ids") or []):

                puja_viva[safe_int(jugador)] = safe_int(
                    operacion.get("amount")
                )

                contraparte[safe_int(jugador)] = {
                    "id": operacion.get("counterparty_id"),
                    "name": operacion.get("counterparty_name"),
                }

        # LO QUE LE PEDIMOS POR UNO NUESTRO (23/08/2026)
        #
        # Una contraoferta salia aqui como PUJA PUESTA sobre un
        # jugador que ya es nuestro. El dueño lo leyo asi: "a
        # Andrés Castrín ya le tengo y dice que ha pujado por él".
        #
        # Es lo contrario de una puja: Pollo17 ofrecio 977.000 por
        # Castrín y le pedimos 1.190.038. Dinero a cobrar.
        contra_oferta = {}

        for operacion in (exposicion.get("counter_offers") or []):
            for jugador in (operacion.get("player_ids") or []):

                contra_oferta[safe_int(jugador)] = {
                    "amount": safe_int(operacion.get("amount")),
                    "counterparty_name": operacion.get(
                        "counterparty_name"
                    ),
                    "until": operacion.get("until"),
                }

        # ------------------------------------------------------
        # A QUIEN SE LE COMPRA
        # ------------------------------------------------------
        #
        # Esta tabla es "el mercado del Computer": mas abajo se
        # descartan las ventas de otros managers, porque Pepe
        # compra ahi y no en las listas de los rivales.
        #
        # Pero una puja NUESTRA puede caer fuera de ese mercado:
        # se puede ofertar por un jugador de un manager sin que
        # el lo haya publicado. Y esas pujas no tenian donde
        # salir.
        #
        # Lo destapo la propia pantalla el 18/08/2026:
        #
        #     Pujas vivas:  Biwenger 2, aqui 1
        #     Comprometido: Biwenger 2.531.501, aqui 2.068.001
        #
        # 463.500 EUR nuestros, vivos, sin una fila donde
        # aparecer. El dueño leia "solo tengo una puja".
        #
        # Asi que la regla pasa a ser: el mercado del Computer
        # MAS todo aquello en lo que ya hay dinero nuestro. Lo
        # segundo entra aunque lo venda un rival y aunque no este
        # publicado, y entra marcado con el nombre de quien vende
        # -no "un rival", el nombre-, porque de cada manager se
        # sabe cuanto suele pagar y eso cambia lo que esperas.
        #
        # Lo que NO cambia es a quien se compra: estas filas
        # llevan `decision` propia y nunca son BID, asi que
        # `best_acquisition_target` no las elige. Se ven, no se
        # persiguen.
        # ------------------------------------------------------

        def _vendedor(player_id: int, venta: dict | None) -> dict:
            """
            Quien vende: el Computer o un manager con nombre.

            Se pregunta primero a la venta publicada y despues a
            la puja, porque una oferta directa por un jugador no
            publicado solo aparece en la segunda.
            """

            venta = venta or {}

            seller_id = venta.get("seller_user_id")
            seller_name = venta.get("seller_name")

            if seller_id is None:

                de_la_puja = contraparte.get(
                    safe_int(player_id)
                ) or {}

                seller_id = de_la_puja.get("id")
                seller_name = (
                    seller_name
                    or de_la_puja.get("name")
                )

            if seller_id is None:
                return {
                    "seller_kind": "COMPUTER",
                    "seller_id": None,
                    "seller_name": "Computer",
                }

            return {
                "seller_kind": "MANAGER",
                "seller_id": safe_int(seller_id),

                # Sin nombre se dice que no se sabe. "Rival" a
                # secas no informa de nada.
                "seller_name": (
                    seller_name
                    or f"Manager {safe_int(seller_id)}"
                ),
            }

        # LA JORNADA, PARA LA SEMILLA DEL DESVIO (13/09/2026)
        #
        #     El desvio de puja se siembra con jugador, fecha,
        #     jornada y sal. La jornada tiene que ser la MISMA que
        #     use el ejecutor, o el importe que enseña la pantalla
        #     no seria el que se puja.
        #
        #     Si no se puede leer, va None y la semilla se queda
        #     con fecha y jugador: se degrada, no se rompe.
        try:
            from src.analysis.calendar_state import (
                build_calendar_state,
            )

            jornada_para_el_desvio = (
                build_calendar_state(snapshot) or {}
            ).get("target_matchday")

        except Exception:                           # noqa: BLE001
            jornada_para_el_desvio = None

        # EL SALDO Y EL PATRIMONIO, PARA EL TOPE DE LA VIA TENER
        #
        #     Las dos condiciones del tope deducido: que la peor
        #     perdida medida la aguante la caja, y que la posicion
        #     no pase del 10 % del patrimonio.
        saldo_actual = safe_int(
            (
                ((snapshot or {}).get("market") or {}).get("status")
                or {}
            ).get("balance")
        )

        valor_de_la_plantilla = sum(
            safe_int(j.get("price"))
            for j in ((snapshot or {}).get("my_team") or [])
            if isinstance(j, dict)
        )

        filas = []

        # Todo lo que hay que mirar: lo que vende el Computer mas
        # aquello donde ya hay dinero nuestro puesto.
        a_mirar = list(vendedores.items())

        ya_listados = {safe_int(pid) for pid, _ in a_mirar}

        for jugador_pujado in puja_viva:

            if safe_int(jugador_pujado) not in ya_listados:
                a_mirar.append((jugador_pujado, {}))
                ya_listados.add(safe_int(jugador_pujado))

        # Y las negociaciones abiertas por uno NUESTRO. Antes
        # entraban de rebote, porque una contraoferta se contaba
        # como puja; al dejar de contarse, la fila desaparecia de
        # la pantalla entera. Y el dueño pidio justo lo contrario:
        # que se vea, pero llamada por su nombre.
        for jugador_negociado in contra_oferta:

            if safe_int(jugador_negociado) not in ya_listados:
                a_mirar.append((jugador_negociado, {}))
                ya_listados.add(safe_int(jugador_negociado))

        for player_id, venta in a_mirar:

            fuera_del_computer = (
                venta.get("seller_user_id") is not None
                or not venta
            )

            # DE UN RIVAL, Y SIN DINERO NUESTRO DENTRO
            #
            #     Estos son los que el filtro tiraba. Ahora
            #     entran, se valoran igual que los del Computer y
            #     se les cierra la compra al final.
            #
            #     Se calcula ANTES de cualquier `continue` para
            #     que la bandera exista siempre: es la que decide
            #     tanto la rama de la decision como la puerta.
            # NUESTRO PROPIO ESCAPARATE NO ES UN MERCADO
            #
            #     De las 61 ventas del tablon, 14 son NUESTRAS.
            #     Al levantar el filtro entraron tambien, y
            #     Mangala -jugador de la casa, publicado por
            #     nosotros- salio con `would_pass: True`.
            #
            #     Un "pasaria el liston" sobre algo que ya es
            #     tuyo es exactamente la familia que llevamos
            #     seis arreglando: un dato correcto contestando
            #     una pregunta que no era la suya. Lo canto la
            #     primera pasada de la sonda y no llego a
            #     ninguna pantalla.
            vende_uno_de_los_nuestros = (
                venta.get("seller_user_id") is not None
                and safe_int(venta.get("seller_user_id"))
                == safe_int(current_user_id)
            )

            de_rival_sin_dinero = (
                fuera_del_computer
                and not vende_uno_de_los_nuestros
                and safe_int(player_id) not in puja_viva
                and safe_int(player_id) not in contra_oferta
            )

            # El filtro de siempre, intacto. Lo unico que cambia
            # es que ahora tiene una salida: el mercado de un
            # rival, con la puerta de mirar abierta.
            #
            # Con `BORDALAS_SIN_MERCADO_RIVALES=1` esa salida se
            # cierra y la tabla es exactamente la de antes del
            # 24/09.
            if (
                fuera_del_computer
                and safe_int(player_id) not in puja_viva
                and safe_int(player_id) not in contra_oferta
                and not (
                    de_rival_sin_dinero
                    and _mercado_de_rivales_visible()
                )
            ):
                continue

            ficha = catalogo.get(safe_int(player_id))

            if not ficha:
                continue

            # DOCTRINA 36: un estado que falta NO es "ok".
            #
            # Un jugador sin ficha de estado se colaba en el
            # tablero como sano. Hoy no pasa -los 20 del tablero
            # traen estado- pero el defecto estaba puesto para
            # cuando dejara de pasar, y ese es justo el dia en
            # que nadie estaria mirando.
            estado = str(
                ficha.get("status") or ESTADO_DESCONOCIDO
            ).lower()

            valoracion = value_candidate(ficha, contexto)

            fila = {
                "id": safe_int(player_id),
                "name": ficha.get("name"),
                "position": safe_int(ficha.get("position")),
                "team_id": safe_int(ficha.get("teamID")),
                "market_price": safe_int(ficha.get("price")),
                "price_increment": safe_int(
                    ficha.get("priceIncrement")
                ),
                "points_last_season": ficha.get("pointsLastSeason"),
                "status": estado,
                "our_value": safe_int(valoracion.get("value")),
                "intent": valoracion.get("intent"),
                "replaces": (
                    (valoracion.get("replaces") or {}).get("name")
                ),

                # LO QUE ESTE CAMBIO PROMETE (19/08/2026)
                #
                # Un cambio se propone con un numero de puntos en
                # la mano. Si no queda escrito, dentro de un mes
                # no habra forma de saber si aquello pago o no, y
                # la conversacion sera de opiniones.
                #
                # `replaces_starter` distingue tocar el once de
                # cambiar a un suplente: se deciden distinto y hay
                # que poder revisarlos por separado.
                "replaces_starter": bool(
                    (valoracion.get("as_xi") or {}).get(
                        "replaces_starter"
                    )
                ),

                "promised_points": (
                    (valoracion.get("as_xi") or {}).get(
                        "promised_points"
                    )
                ),

                "cost_per_point": (
                    (valoracion.get("as_xi") or {}).get(
                        "cost_per_point"
                    )
                ),

                # ============================================
                # LO QUE EL FICHAJE DEVUELVE EN CAJA
                # ============================================
                #
                # Biwenger abona 30.000 EUR por punto al cerrar
                # cada jornada. Hasta hoy la unica vara era
                # "cuanto pide el mercado por un punto" -22.058
                # EUR de mediana-, que dice si algo esta caro
                # COMPARADO CON OTROS. No decia si se paga solo.
                #
                # Y un punto es un punto: da igual en que jornada
                # llegue, paga lo mismo. Asi que las dos cifras
                # son directamente comparables sin inventar
                # horizontes:
                #
                #     cost_per_point < 30.000  -> el abono solo
                #                                 ya cubre el
                #                                 fichaje
                #
                # Lo que sobra es beneficio, y encima queda el
                # jugador para revenderlo.
                "abono_return": (
                    safe_int(
                        (valoracion.get("as_xi") or {}).get(
                            "promised_points"
                        )
                    )
                    * EUROS_POR_PUNTO
                ),

                "pays_for_itself": _se_paga_solo(
                    (valoracion.get("as_xi") or {}).get(
                        "cost_per_point"
                    )
                ),

                # Un cambio de titular no se paga con el dinero de
                # una venta que todavia no ha pasado.
                "needs_sale_first": bool(
                    (valoracion.get("as_xi") or {}).get(
                        "needs_sale_first"
                    )
                ),

                # Sin esto la pantalla no puede explicar por que
                # un jugador con mas puntos que el nuestro NO es
                # una mejora, que fue exactamente la pregunta.

                # EL EQUIPO Y LA JERARQUIA, QUE SON LO QUE AGUANTA
                #
                # El % dice quien juega este sabado; la jerarquia
                # dice que es un jugador en su equipo. Desde el
                # 17/08/2026 la valoracion decide con las dos, asi
                # que las dos tienen que verse: si un dato no se
                # ve, no se mete.
                "team": (
                    (valoracion.get("starter") or {}).get("team")
                ),
                "hierarchy": (
                    (valoracion.get("starter") or {}).get(
                        "hierarchy_label"
                    )
                ),
                "hierarchy_value": (
                    (valoracion.get("starter") or {}).get(
                        "hierarchy_value"
                    )
                ),
                "franchise": bool(
                    (valoracion.get("starter") or {}).get(
                        "franchise"
                    )
                ),
                "availability": (
                    (
                        (valoracion.get("starter") or {}).get(
                            "availability"
                        )
                        or {}
                    ).get("label")
                ),
                "absence": (
                    (valoracion.get("starter") or {}).get("absence")
                ),

                "starter_probability": (
                    (valoracion.get("starter") or {}).get(
                        "probability"
                    )
                ),
                "starter_consensus": (
                    (valoracion.get("starter") or {}).get(
                        "consensus"
                    )
                ),
                "starter_source": (
                    (valoracion.get("starter") or {}).get("source")
                ),
                "expected_points": (
                    (valoracion.get("points") or {}).get("points")
                ),
                # Puntos de la temporada ANTERIOR. El alias
                # `raw_points` se conserva y sigue mintiendo por
                # el nombre: usar el de abajo.
                "last_season_points": (
                    (valoracion.get("points") or {}).get(
                        "last_season_points"
                    )
                ),
                "raw_points": (
                    (valoracion.get("points") or {}).get(
                        "raw_points"
                    )
                ),
                "xi_decision": (
                    (valoracion.get("as_xi") or {}).get("decision")
                ),
                "xi_reason": (
                    (valoracion.get("as_xi") or {}).get("reason")
                ),

                "reason": valoracion.get("reason"),

                # Lo que decidia antes y lo que decide ahora,
                # con el motivo. Esto mueve dinero: tiene que
                # poder mirarse fila a fila.
                "market_gate": valoracion.get("market_gate"),

                # Y que valdria si cada via llevase la
                # confianza de lo que de verdad apuesta.
                # Observador puro: el `our_value` de arriba
                # no lo mira.
                "confidence_shadow": valoracion.get(
                    "confidence_shadow"
                ),

                # Que clase de operacion es, de que bolsillo
                # sale y cuanto valdria llenando una ficha
                # vacia. Bajo interruptor: hoy no manda.
                "deployment": valoracion.get("deployment"),

                # `bid` es lo que pujariamos. `live_bid` es lo que
                # YA tenemos puesto en Biwenger. Dos numeros
                # distintos que la pantalla estaba mezclando en
                # una sola columna.
                "bid": 0,
                "live_bid": puja_viva.get(safe_int(player_id)) or 0,
                "has_live_bid": (
                    safe_int(player_id) in puja_viva
                ),

                # Lo que le PEDIMOS a un rival por este jugador,
                # que es nuestro. Nada que ver con pujar.
                "counter_offer": contra_oferta.get(
                    safe_int(player_id)
                ),

                # A QUIEN SE LE COMPRA. Con nombre.
                **_vendedor(player_id, venta),

                "outside_computer_market": fuera_del_computer,

                # DE UN RIVAL Y SIN DINERO NUESTRO DENTRO
                #
                #     La columna que separa "se puede comprar" de
                #     "solo se puede mirar". Sin ella la pantalla
                #     enseñaria cuarenta y siete filas iguales y
                #     ninguna diria cual es cual.
                "rival_market": de_rival_sin_dinero,

                # Lo que PIDE el vendedor, que no es el precio de
                # mercado. Los dos numeros juntos: el hueco entre
                # ellos es la mitad de la conversacion.
                "asking_price": safe_int(
                    (venta.get("raw_sale") or {}).get("price")
                ) or None,

                "win_probability": None,
                "expected_value": None,
                "decision": valoracion.get("decision"),
            }

            if fila["counter_offer"]:

                # NEGOCIANDO UNA VENTA, NO UNA COMPRA
                #
                # Este jugador es NUESTRO y hay una contraoferta
                # nuestra encima. No se puja por lo que ya se
                # tiene: la fila existe para que se vea la
                # negociacion abierta y por cuanto.
                detalle = fila["counter_offer"]

                fila["decision"] = "CONTRAOFERTA"

                fila["reason"] = (
                    f"Es nuestro. Le hemos pedido "
                    + f"{detalle['amount']:,}".replace(",", ".")
                    + " EUR a "
                    + str(detalle.get("counterparty_name") or "un rival")
                    + " por el. Es dinero a cobrar, no a pagar."
                )

            elif fuera_del_computer and not de_rival_sin_dinero:

                # Ya hay dinero nuestro aqui, pero no es un
                # objetivo del ciclo: Pepe compra en el mercado
                # del Computer. La fila existe para que el euro se
                # vea, no para que se persiga.
                #
                # `and not de_rival_sin_dinero` (24/09/2026): sin
                # esa mitad, los veintisiete recien admitidos
                # caerian aqui y saldrian sin valorar, que es
                # justo el numero que hemos venido a buscar.
                #
                # `decision` distinta de BID es lo que mantiene
                # esta fila fuera de `best_acquisition_target`.
                fila["decision"] = "PUJA_FUERA_DEL_COMPUTER"

                fila["reason"] = (
                    f"Puja nuestra viva por "
                    f"{fila['live_bid']:,} EUR a "
                    f"{fila['seller_name']}. Fuera del mercado "
                    f"del Computer: se enseña, no se persigue."
                ).replace(",", ".")

            elif estado not in {"ok", "unknown"}:
                fila["decision"] = "NO_DISPONIBLE"
                fila["reason"] = f"Estado del jugador: {estado}."

            elif valoracion.get("value", 0) > 0:

                # EL PRESUPUESTO QUE TOCA
                #
                # Mejorar el once no se paga con el limite de las
                # apuestas. La eleccion vive en
                # `acquisition_budget.budget_for_intent` para que
                # produccion y dashboard no puedan contestar
                # distinto.
                presupuesto = budget_for_intent(
                    intent=valoracion.get("intent"),
                    speculation_budget=available_budget,
                    acquisition_budget=acquisition_budget,
                )

                # EL BOLSILLO DE LA VIA TENER (15/09/2026)
                #
                #     Lo decide el efecto sobre el balance, no el
                #     nombre de la via: una compra que ocupa una
                #     ficha vacia no da nada a cambio -convierte
                #     caja en activo- y eso es un fichaje a
                #     efectos contables, aunque la tesis sea la
                #     rampa.
                #
                #     El valor y el liston siguen siendo los de
                #     TENER: la regla del 13/09 se respeta.
                #
                #     Y el tope NO es el del bolsillo grande: es
                #     el deducido, que arranca exactamente donde
                #     esta hoy el limite por operacion. El primer
                #     dia no se afloja nada.
                despliegue_fila = valoracion.get("deployment") or {}

                if (
                    DEPLOYMENT_ENABLED
                    and despliegue_fila.get("route") == "HOLD"
                ):

                    bolsillo = hold_pocket(
                        despliegue_fila.get("free_roster_slots")
                    )

                    if bolsillo["pocket"] == "FICHAR" and (
                        acquisition_budget is not None
                    ):
                        presupuesto = safe_int(acquisition_budget)

                    tope_tener = hold_cap(
                        balance=saldo_actual,
                        squad_value=valor_de_la_plantilla,
                    )

                    if tope_tener.get("cap") is not None:
                        presupuesto = (
                            min(presupuesto, tope_tener["cap"])
                            if presupuesto is not None
                            else tope_tener["cap"]
                        )

                    fila["hold_pocket"] = bolsillo
                    fila["hold_cap"] = tope_tener

                # EL TOPE DE CONCENTRACION
                #
                # Acota, no prohibe: si esta compra dejaria al
                # jugador por encima del 35 % de la plantilla o
                # metiera un quinto del mismo club, se recorta el
                # presupuesto de esa fila y se dice por que.
                #
                # Bajo interruptor, como el resto.
                tope = (
                    check_purchase(
                        concentracion,
                        safe_int(ficha.get("price")),
                        team_id=safe_int(ficha.get("teamID")),
                    )
                    if check_purchase is not None
                    else {"capped": False}
                )

                fila["concentration"] = tope

                if (
                    DEPLOYMENT_ENABLED
                    and tope.get("capped")
                    and tope.get("allowed") is not None
                ):
                    presupuesto = (
                        min(presupuesto, tope["allowed"])
                        if presupuesto is not None
                        else tope["allowed"]
                    )

                plan = optimal_bid(
                    price=safe_int(ficha.get("price")),
                    value=valoracion["value"],
                    model=modelo,
                    available_budget=presupuesto,

                    # El dashboard tiene que enseñar la misma
                    # decision que toma produccion, no una
                    # parecida.
                    intent=valoracion.get("intent"),
                )

                # LO QUE SE OFRECIA ANTES, AL LADO (11/09/2026)
                #
                #     `optimal_bid` ya no puede pasar del
                #     +0,25 % sobre el precio -ver
                #     `PRIMA_MAXIMA_DE_PUJA` y la curva de las
                #     115 subastas-.
                #
                #     Se recalcula SIN el tope para poder enseñar
                #     los dos numeros. No cuesta red: es
                #     aritmetica sobre datos que ya estan en
                #     memoria.
                #
                #     Sin esto, bajar el precio de la puja seria
                #     un cambio invisible: la pantalla enseñaria
                #     una cifra menor y nadie sabria de cuanto
                #     fue el recorte.
                sin_tope = optimal_bid(
                    price=safe_int(ficha.get("price")),
                    value=valoracion["value"],
                    model=modelo,
                    available_budget=presupuesto,
                    intent=valoracion.get("intent"),
                    prima_maxima=None,
                )

                fila["bid_sin_tope"] = safe_int(
                    sin_tope.get("bid")
                )

                fila["ahorro_del_tope"] = max(
                    0,
                    safe_int(sin_tope.get("bid"))
                    - safe_int(plan.get("bid")),
                )

                fila["prima_maxima_percent"] = round(
                    100 * PRIMA_MAXIMA_DE_PUJA, 3
                )

                # LOS DOS TECHOS, CADA UNO CON SU NOMBRE
                # (12/09/2026)
                #
                #     Habia UN solo tope para todos, y su
                #     `break_even_percent` -1,80 %- es donde deja
                #     de ser negocio REVENDER al Computer. Se le
                #     aplicaba igual al jugador que queremos
                #     QUEDARNOS, que es otra moneda entera: los
                #     puntos se pagan a 30.000 EUR.
                #
                #     ESTO NO MUEVE NADA. Publica los dos para
                #     que se vea cual se esta aplicando.
                fila["los_dos_techos"] = los_dos_techos(
                    safe_int(ficha.get("price")),
                    prima_computer_percent=(
                        (
                            contexto.get("computer_premium")
                            or {}
                        ).get("median_percent")
                    ),
                    intent=valoracion.get("intent"),
                    tope_aplicado=safe_int(plan.get("bid")),
                )

                # Que techo se le aplico y de que bolsillo sale.
                # Sin esto, un SUPERA_PRESUPUESTO vuelve a ser un
                # numero que nadie sabe de donde sale.
                fila["budget_applied"] = presupuesto
                fila["budget_source"] = (
                    "FICHAJES"
                    if str(valoracion.get("intent") or "").upper()
                    == "XI_UPGRADE"
                    and acquisition_budget is not None
                    else "ESPECULACION"
                )

                fila["decision"] = plan.get("decision")
                fila["bid"] = safe_int(plan.get("bid"))
                fila["win_probability"] = plan.get("win_probability")
                fila["expected_value"] = plan.get("expected_value")
                fila["bid_reasons"] = plan.get("reasons", [])

                # EL DESVIO, EN PANTALLA (13/09/2026)
                #
                #     El dueño lo pidio asi: "quiero poder mirar la
                #     pantalla y ver cuanto nos esta costando el
                #     seguro. Si en un mes ha costado mas de lo que
                #     ha ganado, se apaga."
                #
                #     Es la MISMA funcion que usa el ejecutor y con
                #     los mismos argumentos, asi que el numero de
                #     aqui es el que se va a pujar de verdad: si
                #     fuese otro, la pantalla estaria enseñando una
                #     puja que no existe.
                if plan.get("decision") == "BID":

                    desvio = apply_bid_jitter(
                        safe_int(plan.get("bid")),
                        safe_int(ficha.get("price")),
                        ceiling=presupuesto,
                        player_id=safe_int(ficha.get("id")),
                        matchday=jornada_para_el_desvio,

                        # EL SEGURO SE PAGA CON LA GANANCIA
                        # (10/09/2026)
                        #
                        #     Sin esto el tope del desvio era el
                        #     0,5 % del PRECIO, que en los
                        #     jugadores que busca la subasta es
                        #     el 52 % de lo que suben en un dia.
                        expected_gain=plan.get(
                            "expected_value"
                        ),
                    )

                    fila["bid"] = safe_int(desvio["bid"])
                    fila["bid_clean"] = safe_int(desvio["clean_bid"])
                    fila["bid_jitter"] = safe_int(desvio["jitter"])
                    fila["bid_jitter_ceiling"] = safe_int(
                        desvio["jitter_ceiling"]
                    )
                    fila["bid_salt_from_env"] = bool(
                        desvio["salt_from_env"]
                    )

                if plan.get("decision") != "BID":
                    fila["reason"] = plan.get("reason")

            # ==================================================
            # LA PUERTA: SE MIRA, NO SE COMPRA
            # ==================================================
            #
            #     UN solo sitio, el ultimo, y despues de haber
            #     valorado. Antes de esta linea la fila ha pasado
            #     por el mismo camino que un jugador del
            #     Computer; a partir de ella no puede comprarse
            #     pase lo que pase, porque `decision` deja de ser
            #     BID y `best_acquisition_target` solo elige BID.
            #
            #     Lo que HABRIA decidido se guarda en vez de
            #     tirarse: es la unica forma de contestar
            #     "cuantos pasarian el liston" sin abrir la
            #     compra para averiguarlo.
            if de_rival_sin_dinero:

                fila["would_be_decision"] = fila["decision"]
                fila["would_pass"] = fila["decision"] == "BID"
                fila["would_bid"] = safe_int(fila.get("bid"))

                fila["decision"] = MERCADO_DE_RIVAL

                # Y el importe a cero. Un numero en la columna de
                # puja sobre una fila que no se puede pujar es
                # exactamente la familia de fallos que llevamos
                # cinco arreglando.
                fila["bid"] = 0

                pedido = fila.get("asking_price")

                fila["reason"] = (
                    f"Lo vende {fila['seller_name']}"
                    + (
                        " y pide "
                        + f"{pedido:,}".replace(",", ".")
                        + " EUR"
                        if pedido
                        else ""
                    )
                    + ". "
                    + (
                        "Pasaria el liston"
                        if fila["would_pass"]
                        else "No pasaria el liston"
                    )
                    + " ("
                    + str(fila["would_be_decision"])
                    + "), pero la compra a managers esta cerrada: "
                    "se ofrece, no se compra, y la tasa de "
                    "aceptacion no esta medida. Se mira."
                )

            filas.append(fila)

        # Primero lo que se puede ejecutar HOY, y dentro de eso lo
        # que todavia no tiene puja nuestra. Asi la primera fila
        # de la tabla es la que el ciclo va a ejecutar de verdad,
        # que es como se lee en la consola.
        # EL ORDEN DE PRIORIDAD (13/09/2026)
        #
        #     Primero lo ejecutable HOY, y dentro de eso lo que
        #     todavia no tiene puja nuestra: asi la primera fila
        #     es la que el ciclo va a ejecutar de verdad.
        #
        #     Y entre las ejecutables manda el ESCALON antes que
        #     el valor esperado. Es lo que hace Pollo: llenar
        #     fichas antes que especular, porque una ficha vacia
        #     es capital al 0 % y el dinero parado no se
        #     revaloriza.
        #
        #     Con el despliegue apagado el escalon vale igual para
        #     todos y el orden es exactamente el de antes.
        def _escalon(item) -> int:

            if not DEPLOYMENT_ENABLED:
                return 0

            return safe_int(
                (item.get("deployment") or {}).get("priority"),
                default=PURE_SPECULATION,
            )

        filas.sort(
            key=lambda item: (
                item["decision"] != "BID",
                bool(item.get("has_live_bid")),
                _escalon(item),
                -(item.get("expected_value") or 0),
                -item["our_value"],
            )
        )

        # Cuantos candidatos del mercado tienen pronostico de
        # titularidad. Importa mirarlo: la regla del once bloquea
        # a quien no lo tiene, asi que si esta cobertura se cae a
        # cero Pepe deja de mejorar el once y hay que enterarse
        # por aqui, no por el silencio.
        con_pronostico = sum(
            1
            for f in filas
            if f.get("starter_probability") is not None
        )

        # Los tres motivos por los que la regla del once frena una
        # compra. `NO_MEJORA_JERARQUIA` y `SIN_PRONOSTICO` son del
        # 17/08/2026, y sin anadirlos aqui el contador volvia a
        # quedarse corto: paso de 12 bloqueados a 5 el dia que el
        # veto empezo a hacer MAS trabajo, no menos.
        VETOS_DEL_ONCE = (
            "NO_MEJORA_TITULARIDAD",
            "NO_MEJORA_JERARQUIA",
            "SIN_PRONOSTICO",
        )

        bloqueados = sum(
            1
            for f in filas
            if f.get("xi_decision") in VETOS_DEL_ONCE
        )

        # EL RECORTE MUDO (21/08/2026)
        #
        #     "Mira los jugadores del mercado y mira los que ve
        #      Pepe. No ve todos, ¿por qué?"
        #
        #     Si los veia: la cabecera decia "20 VALORADOS" y la
        #     tabla enseñaba doce. Los otros ocho estaban
        #     valorados, puntuados y ordenados, y se tiraban en la
        #     ultima linea antes de la pantalla.
        #
        #     Un recorte que no se anuncia se lee como "esto es
        #     todo lo que hay". El dueño reviso el mercado a mano
        #     para descubrirlo.
        #
        # El mercado del Computer son veinte jugadores al dia. No
        # hay ninguna razon para no enseñarlos todos, asi que el
        # limite sube a un tamaño que no recorta nada real y se
        # queda solo como freno ante un mercado anomalo.
        #
        # Y si algun dia recorta, LO DICE: `hidden` sale en el
        # payload y la pantalla lo canta. Un tope silencioso es
        # una mentira por omision.
        mostradas = filas[:limit]

        vistos = {f["id"] for f in mostradas}

        # Lo que ya esta comprometido entra siempre, aunque el
        # recorte lo hubiera dejado fuera: el recorte no puede
        # esconder nuestro propio dinero.
        mostradas.extend(
            f
            for f in filas
            if f.get("has_live_bid") and f["id"] not in vistos
        )

        vistos.update(f["id"] for f in mostradas)

        # Y lo mismo con el rival que SI pasaria el liston
        # (24/09/2026). Estas filas nunca son BID, asi que el
        # orden las manda al final y serian las primeras en caer
        # por el recorte. Justo las unicas por las que se ha
        # abierto esta puerta.
        mostradas.extend(
            f
            for f in filas
            if f.get("would_pass") and f["id"] not in vistos
        )

        ocultas = len(filas) - len(mostradas)

        con_puja_viva = [
            f for f in filas if f.get("has_live_bid")
        ]

        return {
            "available": True,

            # CON QUE DINERO SE HA DECIDIDO
            #
            # Los dos numeros, juntos y visibles. Mientras solo se
            # publicaba uno, nadie podia ver que se estaba usando
            # el que no era.
            "budgets": {
                "acquisition": acquisition_budget,
                "speculation": available_budget,
                "separated": acquisition_budget is not None,
            },

            # El tamaño del mercado sigue siendo el del Computer.
            # Las filas de pujas fuera de el se ven en la tabla
            # pero no engordan este numero, que es el que dice
            # cuanto habia donde elegir.
            "market_size": sum(
                1
                for f in filas
                if not f.get("outside_computer_market")
            ),

            "outside_computer_market": sum(
                1
                for f in filas
                if f.get("outside_computer_market")
            ),

            "biddable": sum(
                1 for f in filas if f["decision"] == "BID"
            ),

            # LO QUE AHORRA EL TOPE DE LA PRIMA (11/09/2026)
            #
            #     Sumado sobre todo el escaparate, no fila a
            #     fila: un recorte de mil euros por jugador no
            #     dice nada; el acumulado si.
            #
            #     `bids_capped` son cuantas pujas ha recortado
            #     de verdad. Si sale cero, el tope no esta
            #     mordiendo — que hoy es lo que pasa, porque la
            #     curva de primas esta plana y `optimal_bid` ya
            #     ofrecia el precio y un euro.
            # LOS DOS TECHOS, CADA UNO CON SU NOMBRE
            # (12/09/2026)
            #
            #     `bid_cap` de abajo es UN solo tope para todos, y
            #     su `break_even_percent` es donde deja de ser
            #     negocio REVENDERLO al Computer — un numero que
            #     no tiene nada que ver con el jugador que
            #     queremos QUEDARNOS, y que se le aplicaba igual.
            #
            #     Esto los calcula y dice cual se esta aplicando.
            #     NO MUEVE NINGUNO: `bid_cap` sigue exactamente
            #     como estaba y ninguna puja cambia de importe.
            # EL NUMERO QUE CONTESTA LA PREGUNTA
            # (12/09/2026)
            #
            #     Cuantas pujas llevan hoy un tope aplicado POR
            #     ENCIMA del techo del comerciante. En una puja
            #     de revender eso es pagar mas de lo que el viaje
            #     puede recuperar; en una de fichar no significa
            #     nada, porque ese techo no es el suyo.
            #
            #     Se publica separado por via, que es justo lo
            #     que no se podia ver.
            "techos": _resumen_de_los_techos(filas),

            "bid_cap": {
                "premium_percent": round(
                    100 * PRIMA_MAXIMA_DE_PUJA, 3
                ),
                "break_even_percent": round(
                    100 * PRIMA_DE_EQUILIBRIO, 3
                ),
                "bids_capped": sum(
                    1
                    for f in filas
                    if safe_int(f.get("ahorro_del_tope")) > 0
                ),
                "saved_total": sum(
                    safe_int(f.get("ahorro_del_tope"))
                    for f in filas
                ),
            },

            # EL ESCAPARATE, CON SUS DOS MITADES (24/09/2026)
            #
            #     `market_size` cuenta solo el Computer y asi se
            #     queda: es lo que dice donde se puede comprar
            #     HOY. Pero "cuantos hay a la venta" y "a cuantos
            #     se les puede comprar" son dos preguntas, y la
            #     pantalla contestaba las dos con el mismo numero.
            #
            #     `would_pass` es el que decide si merece la pena
            #     abrir esta puerta: cuantos de los del rival
            #     habrian salido BID si se pudiese.
            "rival_market": {
                "shown": sum(
                    1 for f in filas if f.get("rival_market")
                ),
                "would_pass": sum(
                    1 for f in filas if f.get("would_pass")
                ),
                "sellers": sorted({
                    str(f.get("seller_name"))
                    for f in filas
                    if f.get("rival_market")
                }),
                "buying_closed": True,
                "visible": _mercado_de_rivales_visible(),
            },

            "buyable_universe": sum(
                1
                for f in filas
                if not f.get("outside_computer_market")
                or f.get("rival_market")
            ),

            # Lo que YA tenemos puesto, frente a lo que se podria
            # pujar. Son dos cosas y la pantalla las confundia.
            "with_live_bid": len(con_puja_viva),
            "live_bid_total": sum(
                safe_int(f.get("live_bid")) for f in con_puja_viva
            ),
            "actionable": sum(
                1
                for f in filas
                if f["decision"] == "BID"
                and not f.get("has_live_bid")
            ),

            "starter_coverage": {
                "with_forecast": con_pronostico,
                "total": len(filas),
                "blocked_by_starter_rule": bloqueados,
            },
            # Cuantos valorados NO llegan a la tabla. Cero casi
            # siempre; si deja de serlo, la pantalla lo dice en
            # vez de callarse.
            "valued": len(filas),
            "shown": len(mostradas),
            "hidden": max(0, ocultas),

            "premium_model": modelo.get("premium"),

            # LA SEGUNDA VIA DE REVENTA
            #
            # Cuanto paga el Computer por encima del mercado, y si
            # se sabe ya con muestras suficientes. Mientras salga
            # sin calibrar, esa via de ingresos esta apagada y
            # tiene que verse que lo esta.
            "computer_premium": contexto.get("computer_premium"),
            "data_coverage": modelo.get("data_coverage"),
            "ledger_trusted": modelo.get("ledger_trusted"),
            "rivals": [
                {
                    "name": r.get("name"),
                    "participation": r.get("participation"),
                    "capacity": r.get("capacity"),
                    "coverage": r.get("coverage"),
                    "never_bids": r.get("never_bids"),
                }
                for r in (modelo.get("rivals") or [])
            ],
            "targets": mostradas,
        }

    except Exception as error:
        return {
            "available": False,
            "targets": [],
            "reason": f"{type(error).__name__}: {error}",
        }


