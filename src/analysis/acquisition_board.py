from __future__ import annotations

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


def build_acquisition_board(
    snapshot: dict,
    rival_intelligence: dict,
    current_user_id,
    available_budget: int | None,
    limit: int = 12,
) -> dict:
    """
    Que hay en el mercado del Computer, cuanto vale para nosotros y
    cuanto pujariamos.

    Es la vista que responde a "que va a hacer Pepe hoy". Antes no
    existia: el panel de especulacion solo mostraba nombres y
    scores, sin decir cuanto ni por que.
    """

    try:
        contexto = build_valuation_context(snapshot)

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

        for operacion in (exposicion.get("operations") or []):
            for jugador in (operacion.get("player_ids") or []):
                puja_viva[safe_int(jugador)] = safe_int(
                    operacion.get("amount")
                )

        filas = []

        for player_id, venta in vendedores.items():

            if venta.get("seller_user_id") is not None:
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

                # Sin esto la pantalla no puede explicar por que
                # un jugador con mas puntos que el nuestro NO es
                # una mejora, que fue exactamente la pregunta.
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

                "win_probability": None,
                "expected_value": None,
                "decision": valoracion.get("decision"),
            }

            if estado not in {"ok", "unknown"}:
                fila["decision"] = "NO_DISPONIBLE"
                fila["reason"] = f"Estado del jugador: {estado}."

            elif valoracion.get("value", 0) > 0:

                plan = optimal_bid(
                    price=safe_int(ficha.get("price")),
                    value=valoracion["value"],
                    model=modelo,
                    available_budget=available_budget,

                    # El dashboard tiene que enseñar la misma
                    # decision que toma produccion, no una
                    # parecida.
                    intent=valoracion.get("intent"),
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

        # El recorte no puede esconder nuestro propio dinero.
        #
        # Con `limit=12` sobre 20 valorados, dos de las tres pujas
        # vivas caian fuera de la lista y la pantalla no tenia
        # forma de ensenarlas aunque quisiera. Lo que ya esta
        # comprometido entra siempre.
        mostradas = filas[:limit]

        vistos = {f["id"] for f in mostradas}

        mostradas.extend(
            f
            for f in filas
            if f.get("has_live_bid") and f["id"] not in vistos
        )

        con_puja_viva = [
            f for f in filas if f.get("has_live_bid")
        ]

        return {
            "available": True,
            "market_size": len(filas),
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
            "premium_model": modelo.get("premium"),
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


