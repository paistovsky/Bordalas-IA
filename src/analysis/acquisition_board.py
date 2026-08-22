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
    build_bid_model,
    optimal_bid,
)


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

        contexto = build_valuation_context(snapshot, lineup=once)

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

        filas = []

        # Todo lo que hay que mirar: lo que vende el Computer mas
        # aquello donde ya hay dinero nuestro puesto.
        a_mirar = list(vendedores.items())

        ya_listados = {safe_int(pid) for pid, _ in a_mirar}

        for jugador_pujado in puja_viva:

            if safe_int(jugador_pujado) not in ya_listados:
                a_mirar.append((jugador_pujado, {}))

        for player_id, venta in a_mirar:

            fuera_del_computer = (
                venta.get("seller_user_id") is not None
                or not venta
            )

            # Un mercado de otro manager solo entra si ya hay
            # dinero nuestro dentro. Si no, esta tabla seguiria
            # siendo el mercado del Computer, como hasta ahora.
            if (
                fuera_del_computer
                and safe_int(player_id) not in puja_viva
            ):
                continue

            ficha = catalogo.get(safe_int(player_id))

            if not ficha:
                continue

            estado = str(ficha.get("status") or "ok").lower()

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

                # `bid` es lo que pujariamos. `live_bid` es lo que
                # YA tenemos puesto en Biwenger. Dos numeros
                # distintos que la pantalla estaba mezclando en
                # una sola columna.
                "bid": 0,
                "live_bid": puja_viva.get(safe_int(player_id)) or 0,
                "has_live_bid": (
                    safe_int(player_id) in puja_viva
                ),

                # A QUIEN SE LE COMPRA. Con nombre.
                **_vendedor(player_id, venta),

                "outside_computer_market": fuera_del_computer,

                "win_probability": None,
                "expected_value": None,
                "decision": valoracion.get("decision"),
            }

            if fuera_del_computer:

                # Ya hay dinero nuestro aqui, pero no es un
                # objetivo del ciclo: Pepe compra en el mercado
                # del Computer. La fila existe para que el euro se
                # vea, no para que se persiga.
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

                if plan.get("decision") != "BID":
                    fila["reason"] = plan.get("reason")

            filas.append(fila)

        # Primero lo que se puede ejecutar HOY, y dentro de eso lo
        # que todavia no tiene puja nuestra. Asi la primera fila
        # de la tabla es la que el ciclo va a ejecutar de verdad,
        # que es como se lee en la consola.
        filas.sort(
            key=lambda item: (
                item["decision"] != "BID",
                bool(item.get("has_live_bid")),
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


