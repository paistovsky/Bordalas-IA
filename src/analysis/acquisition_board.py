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
                "reason": valoracion.get("reason"),
                "bid": 0,
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

        filas.sort(
            key=lambda item: (
                item["decision"] != "BID",
                -(item.get("expected_value") or 0),
                -item["our_value"],
            )
        )

        return {
            "available": True,
            "market_size": len(filas),
            "biddable": sum(
                1 for f in filas if f["decision"] == "BID"
            ),
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
            "targets": filas[:limit],
        }

    except Exception as error:
        return {
            "available": False,
            "targets": [],
            "reason": f"{type(error).__name__}: {error}",
        }


