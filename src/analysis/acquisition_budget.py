from __future__ import annotations

"""
El dinero de fichar no es el dinero de especular.

EL CASO (21/08/2026)

    "Tengo 1.5M en la cuenta ahora mismo. Que significa eso de
     que supera_presupuesto?"

    Agoumé costaba 2.580.000 EUR. Biwenger nos dejaba pujar hasta
    13.050.000. El tablero decia:

        SUPERA_PRESUPUESTO
        "Cuesta 2.580.000 EUR y solo quedan 1.497.444 sin
         comprometer."

    Ese 1.497.444 no salia de la cuenta ni de Biwenger. Salia de
    dos porcentajes:

        MAX_SPECULATION_BUDGET_PERCENT = 0.15
        MAX_DEBT_SPECULATION_PERCENT   = 0.60

    Son el limite de ESPECULAR. Comprar barato, esperar a que
    suba, revender. Ahi arriesgar el 15 % de la caja es sensato:
    es una apuesta, y una apuesta que sale mal no puede llevarse
    la temporada por delante.

    Pero se estaba aplicando igual a fichar para mejorar el once,
    que no es una apuesta: es la razon de ser del bot.

    Con el techo de especulacion, Pepe se limitaba a si mismo a la
    novena parte de lo que Biwenger le dejaba gastar.

LA TERCERA PARED

    Es la tercera regla seguida que, sola, hacia imposible mejorar
    el once:

        1. El titular que sale contaba cero.        (arreglado 21/08)
        2. Hacia falta un 25 % de margen para tocarlo.
        3. El presupuesto era el de especular.      (esto)

    Cada una parecia prudente por separado. Juntas daban cero
    pujas en veinte candidatos, dias seguidos.

QUE CAMBIA Y QUE NO

    Cambia el PORCENTAJE, no las condiciones.

    La deuda sigue exigiendo exactamente lo mismo que exigia:
    solvencia garantizada, ventana de deuda abierta, permiso
    temporal y margen dentro de MAX_SAFE_DEBT. Hard Safety sigue
    bloqueando. Una puja Franchise viva sigue congelandolo todo.

    Lo que se quita es el descuento sobre un limite que YA es el
    limite prudente. `additional_debt_headroom` significa "hasta
    aqui se puede llegar sin peligro"; quedarse en el 60 % de eso
    era una segunda red debajo de la red, y las redes duplicadas
    no protegen mas: paralizan.

    Y se quita el minimo. MIN_SPECULATION_BUDGET = 150.000 evita
    micro-apuestas irrelevantes. Pero un fichaje de 150.000 no es
    irrelevante: Copete costaba eso y sumaba 32 puntos.

EL TECHO SIGUE SIENDO EL DE BIWENGER

    `maximumBid` es la unica pared que no es nuestra, y se
    respeta. Ahi dentro ya esta contado lo que vale la plantilla:
    por eso el 80 % que se recupera del titular que sale NO se
    suma aparte. Sumarlo seria contarlo dos veces.

    Y `maximumBid` ya viene con las pujas vivas descontadas
    -medido el 16/08-, asi que lo comprometido se resta del bruto
    y no del neto. Esa cuenta no se reescribe aqui: se llama a
    `apply_exposure_to_budget`, que es donde vive.
"""

from src.analysis.bid_exposure_engine import (
    apply_exposure_to_budget,
)


# ======================================================
# CONFIGURACION
# ======================================================

# Fichar no es apostar. La caja entera esta disponible: gastarla
# deja el saldo a cero, que es exactamente donde empieza la deuda,
# y la deuda tiene su propio limite justo debajo.
ACQUISITION_CASH_PERCENT = 1.00

# Todo el margen que el motor de solvencia declara SEGURO. Ni un
# euro mas: `additional_debt_headroom` ya es el limite.
ACQUISITION_DEBT_PERCENT = 1.00

# No hay minimo. Un fichaje de 150.000 EUR puede ser la mejor
# operacion del mercado.
MIN_ACQUISITION_BUDGET = 0


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def calculate_acquisition_budget(
    snapshot: dict,
    solvency: dict,
    active_franchise_bid: dict | None = None,
    exposure: dict | None = None,
) -> dict:
    """
    Cuanto se puede gastar HOY en mejorar el once.

    Mismas puertas que la especulacion, otra cantidad al otro
    lado. Nunca lanza: si algo falla devuelve un presupuesto
    deshabilitado con el motivo, y quien lo use se queda sin
    fichar en vez de fichar a ciegas.
    """

    try:
        status = (
            (snapshot or {}).get("market") or {}
        ).get("status") or {}

        balance = safe_int(status.get("balance"))
        maximum_bid = safe_int(status.get("maximumBid"))

        solvency = solvency or {}

        hard_safety = solvency.get("hard_safety") or {}
        guarantee = solvency.get("solvency_guarantee") or {}
        safe_debt = solvency.get("max_safe_debt") or {}
        temporary_debt = solvency.get("temporary_debt") or {}

        headroom = safe_int(
            safe_debt.get("additional_debt_headroom")
        )

        base = {
            "cash_budget": 0,
            "debt_budget": 0,
            "gross_budget": 0,
            "total_budget": 0,
            "available_budget": 0,
            "single_operation_limit": 0,
            "maximum_bid": maximum_bid,
            "balance": balance,
            "safe_debt_headroom": headroom,
            "purpose": "XI_UPGRADE",
        }

        # --------------------------------------------------
        # LAS PUERTAS QUE NO SE TOCAN
        # --------------------------------------------------

        if active_franchise_bid is not None:

            jugador = (
                (active_franchise_bid or {}).get("player") or {}
            )

            return {
                **base,
                "enabled": False,
                "blocked_by": "FRANCHISE_ACTIVE_BID",
                "mode": "BLOCKED",
                "reason": (
                    "Hay una puja Franchise viva por "
                    f"{jugador.get('name') or 'un jugador'}. "
                    "Hasta que se resuelva no se ficha nada mas."
                ),
            }

        if hard_safety.get("active", False):

            return {
                **base,
                "enabled": False,
                "blocked_by": "HARD_SAFETY",
                "mode": "BLOCKED",
                "reason": (
                    "Hard Safety activo: primero se arregla la "
                    "solvencia y despues se ficha."
                ),
            }

        # --------------------------------------------------
        # CAJA
        # --------------------------------------------------

        cash_budget = int(
            max(balance, 0) * ACQUISITION_CASH_PERCENT
        )

        # --------------------------------------------------
        # DEUDA SEGURA
        #
        # Condiciones IDENTICAS a las de la especulacion. Lo unico
        # distinto es que se usa entero el margen que ya se llama
        # seguro.
        # --------------------------------------------------

        guaranteed = bool(guarantee.get("guaranteed", False))

        debt_window_open = bool(
            safe_debt.get("debt_window_open", False)
        )

        debt_allowed = bool(
            temporary_debt.get("allowed", False)
        )

        debt_usable = bool(
            guaranteed
            and debt_window_open
            and debt_allowed
            and headroom > 0
        )

        if debt_usable:
            debt_reason = None

        elif not guaranteed:
            debt_reason = "SOLVENCY_GUARANTEE no esta garantizada."

        elif not debt_window_open:
            debt_reason = "La ventana de deuda segura esta cerrada."

        elif not debt_allowed:
            debt_reason = "La ventana temporal no permite nueva deuda."

        else:
            debt_reason = "MAX_SAFE_DEBT no deja margen adicional."

        debt_budget = (
            int(headroom * ACQUISITION_DEBT_PERCENT)
            if debt_usable
            else 0
        )

        # --------------------------------------------------
        # EL TECHO DE BIWENGER
        # --------------------------------------------------

        gross_budget = cash_budget + debt_budget

        total_budget = gross_budget

        if maximum_bid > 0:
            total_budget = min(total_budget, maximum_bid)

        presupuesto = {
            **base,
            "enabled": total_budget > MIN_ACQUISITION_BUDGET,
            "cash_budget": cash_budget,
            "debt_budget": debt_budget,
            "gross_budget": gross_budget,
            "total_budget": total_budget,

            # Fichar es UNA operacion. Partir el presupuesto en
            # trozos es de especular, donde se reparte el riesgo
            # entre varias apuestas.
            "single_operation_limit": total_budget,

            "capped_by_biwenger": bool(
                maximum_bid > 0 and gross_budget > maximum_bid
            ),
            "debt_unavailable_reason": debt_reason,
            "blocked_by": (
                None if total_budget > 0 else "SIN_CAPACIDAD"
            ),
            "mode": (
                "CASH_AND_DEBT" if debt_budget > 0 else "CASH"
            ),
            "reason": (
                f"Para mejorar el once: {total_budget:,} EUR."
                + (
                    f" Son {cash_budget:,} de caja"
                    + (
                        f" y {debt_budget:,} de deuda dentro de "
                        f"MAX_SAFE_DEBT."
                        if debt_budget > 0
                        else "."
                    )
                )
                + (
                    f" Recortado por el maximo de Biwenger "
                    f"({maximum_bid:,})."
                    if maximum_bid > 0 and gross_budget > maximum_bid
                    else ""
                )
            ).replace(",", "."),
        }

        # --------------------------------------------------
        # LO YA COMPROMETIDO
        #
        # No se reescribe la cuenta: la hace el mismo sitio que la
        # hace para la especulacion. Si un dia Biwenger cambia como
        # refleja las pujas vivas, cambia en un sitio.
        # --------------------------------------------------

        if exposure is not None:
            presupuesto = apply_exposure_to_budget(
                presupuesto,
                exposure,
            )

        else:
            presupuesto["available_budget"] = total_budget
            presupuesto["exposure_applied"] = False

        return presupuesto

    except Exception as error:
        return {
            "enabled": False,
            "cash_budget": 0,
            "debt_budget": 0,
            "gross_budget": 0,
            "total_budget": 0,
            "available_budget": 0,
            "single_operation_limit": 0,
            "purpose": "XI_UPGRADE",
            "blocked_by": "ERROR",
            "mode": "BLOCKED",
            "reason": (
                f"No se pudo calcular el presupuesto de fichajes: "
                f"{type(error).__name__}: {error}"
            ),
        }


def budget_for_intent(
    intent: str | None,
    speculation_budget: int | None,
    acquisition_budget: int | None,
) -> int | None:
    """
    Cual de los dos presupuestos aplica a este candidato.

    Vive aqui y no en el tablero para que produccion y dashboard
    no puedan contestar distinto. Ese es exactamente el fallo que
    el 16/08 puso cuatro pujas en pantalla y una viva en Biwenger.

    Sin `intent` se aplica el mas estrecho de los dos. No saber
    por que via lo queremos no es motivo para gastar mas.
    """

    via = str(intent or "").upper()

    if via == "XI_UPGRADE":
        if acquisition_budget is not None:
            return safe_int(acquisition_budget)

        # Sin presupuesto de fichajes se usa el que haya. Es lo
        # que se hacia hasta el 21/08 y es peor, pero es mejor que
        # quedarse sin techo.
        return (
            safe_int(speculation_budget)
            if speculation_budget is not None
            else None
        )

    if via == "SPECULATION":
        return (
            safe_int(speculation_budget)
            if speculation_budget is not None
            else None
        )

    # Intencion desconocida: el mas estrecho de los que haya.
    candidatos = [
        safe_int(valor)
        for valor in (speculation_budget, acquisition_budget)
        if valor is not None
    ]

    return min(candidatos) if candidatos else None


def print_acquisition_budget(budget: dict) -> None:

    print()
    print("-" * 70)
    print("PRESUPUESTO PARA MEJORAR EL ONCE")
    print("-" * 70)

    if not budget:
        print("  No disponible.")
        return

    for etiqueta, clave in (
        ("Caja", "cash_budget"),
        ("Deuda segura", "debt_budget"),
        ("Bruto", "gross_budget"),
        ("Techo Biwenger", "maximum_bid"),
        ("Autorizado", "total_budget"),
        ("Comprometido", "committed_total"),
        ("Disponible", "available_budget"),
    ):
        print(
            f"  {etiqueta:<18}"
            f"{safe_int(budget.get(clave)):>14,} EUR".replace(
                ",", "."
            )
        )

    print(f"  {budget.get('reason')}")
