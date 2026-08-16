"""
Contador de exposicion: cuanto dinero tenemos ya comprometido.

POR QUE EXISTE
    En Biwenger una puja no descuenta el saldo. El dinero solo se
    mueve en el reset del Computer, cuando se resuelven todas las
    pujas a la vez.

    El ciclo de Bordalas corre cada 30 minutos y recalcula el
    presupuesto desde el saldo. Como el saldo no baja al pujar, el
    presupuesto sale intacto en cada ciclo:

        10:07  presupuesto 6.400.000  ->  puja 2.500.000 por A
        10:37  presupuesto 6.400.000  ->  puja 2.500.000 por B
        11:07  presupuesto 6.400.000  ->  puja 2.500.000 por C

    Siete millones y medio comprometidos con un presupuesto de
    seis y medio. Si se ganan las tres, el equipo se pasa de lo
    que habia autorizado.

    Dentro de un mismo ciclo esto no pasaba: `build_speculation_
    board` va restando de un `remaining_budget`. Pero ese contador
    nace y muere con el ciclo, y entre ciclos nadie se acordaba de
    nada.

    El tope por operacion del 40 % no arreglaba esto. Solo hacia
    que cada error individual fuese mas pequeno.

QUE HACE
    Suma nuestras pujas vivas leyendolas del snapshot, para que el
    presupuesto de cada ciclo parta de lo que queda y no de lo que
    habia al principio del dia.

DE DONDE SALEN LAS PUJAS
    De `market.offers`, filtrando por direccion. En el snapshot
    real las ofertas entrantes llegan con from=None y las nuestras
    con from=<nuestro id>. Mirar solo requestedPlayers confunde
    una oferta entrante con una puja propia.

UNA INCERTIDUMBRE HONESTA
    No esta verificado si Biwenger ya descuenta las pujas vivas de
    `maximumBid`. Si lo hiciera, estariamos restando dos veces y
    seriamos mas conservadores de la cuenta -nunca al reves-.

    `measure_biwenger_reflection` deja preparada la comprobacion:
    en cuanto haya una puja viva en un snapshot, dice si el
    maximumBid la refleja o no. Hasta entonces, restar es el lado
    seguro del error.
"""

from __future__ import annotations


# Estados en los que una puja sigue viva.
ACTIVE_BID_STATUS = frozenset({"waiting", "pending", ""})


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def get_own_user_id(snapshot: dict) -> int | None:

    usuario = (
        (snapshot.get("league") or {}).get("user")
        or {}
    )

    if not isinstance(usuario, dict):
        return None

    identificador = usuario.get("id")

    if identificador is None:
        return None

    try:
        return int(identificador)

    except (TypeError, ValueError):
        return None


def _offer_source_id(offer: dict):

    origen = offer.get("from")

    if isinstance(origen, dict):
        origen = origen.get("id")

    if origen is None:
        return None

    try:
        return int(origen)

    except (TypeError, ValueError):
        return None


def _requested_player_ids(offer: dict) -> list:

    resultado = []

    for solicitado in (offer.get("requestedPlayers") or []):

        identificador = (
            solicitado.get("id")
            if isinstance(solicitado, dict)
            else solicitado
        )

        try:
            resultado.append(int(identificador))

        except (TypeError, ValueError):
            continue

    return resultado


def build_bid_exposure(
    snapshot: dict,
    own_user_id: int | None = None,
) -> dict:
    """
    Dinero comprometido en pujas vivas.

    Nunca lanza. Si no puede leer el snapshot devuelve
    available=False y cero comprometido, que es el comportamiento
    de antes: sin contador.
    """

    try:
        if own_user_id is None:
            own_user_id = get_own_user_id(snapshot)

        if own_user_id is None:
            return {
                "available": False,
                "committed_total": 0,
                "operation_count": 0,
                "operations": [],
                "reason": (
                    "No se pudo identificar nuestro usuario en el "
                    "snapshot."
                ),
            }

        ofertas = (
            (snapshot.get("market") or {}).get("offers")
            or []
        )

        operaciones = []

        for oferta in ofertas:

            if not isinstance(oferta, dict):
                continue

            if _offer_source_id(oferta) != own_user_id:
                continue

            estado = str(
                oferta.get("status") or ""
            ).lower()

            if estado not in ACTIVE_BID_STATUS:
                continue

            importe = safe_int(oferta.get("amount"))

            if importe <= 0:
                continue

            operaciones.append(
                {
                    "offer_id": oferta.get("offer_id")
                    or oferta.get("id"),
                    "amount": importe,
                    "player_ids": _requested_player_ids(oferta),
                    "status": estado or "waiting",
                    "until": oferta.get("until"),
                }
            )

        comprometido = sum(
            item["amount"] for item in operaciones
        )

        return {
            "available": True,
            "committed_total": comprometido,
            "operation_count": len(operaciones),
            "operations": operaciones,
            "reason": (
                f"{len(operaciones)} puja(s) viva(s) por "
                f"{comprometido:,} EUR.".replace(",", ".")
                if operaciones
                else "No hay pujas vivas."
            ),
        }

    except Exception as error:
        return {
            "available": False,
            "committed_total": 0,
            "operation_count": 0,
            "operations": [],
            "reason": f"{type(error).__name__}: {error}",
        }


def apply_exposure_to_budget(
    budget: dict,
    exposure: dict,
) -> dict:
    """
    Descuenta del presupuesto lo que ya esta comprometido.

    Devuelve una copia; no modifica el original.

    Si el contador no esta disponible el presupuesto sale intacto
    pero marcado, para que quede claro que ese numero no ha pasado
    por el control.
    """

    resultado = dict(budget or {})

    if not exposure or not exposure.get("available"):
        resultado["exposure_applied"] = False
        resultado["committed_total"] = 0
        resultado["available_budget"] = safe_int(
            resultado.get("total_budget")
        )
        return resultado

    comprometido = safe_int(exposure.get("committed_total"))
    total = safe_int(resultado.get("total_budget"))

    disponible = max(total - comprometido, 0)

    resultado["exposure_applied"] = True
    resultado["committed_total"] = comprometido
    resultado["committed_operations"] = exposure.get(
        "operation_count", 0
    )
    resultado["available_budget"] = disponible

    if comprometido <= 0:
        return resultado

    # Con todo comprometido no se deshabilita el presupuesto: las
    # ventas y el resto de la maquinaria siguen necesitandolo. Lo
    # que se cierra es la puerta a pujas nuevas.
    resultado["new_bids_allowed"] = disponible > 0

    resultado["reason"] = (
        f"{resultado.get('reason', '')} "
        f"Ya hay {comprometido:,} EUR comprometidos en "
        f"{exposure.get('operation_count', 0)} puja(s) viva(s); "
        f"quedan {disponible:,} EUR."
    ).replace(",", ".").strip()

    return resultado


def measure_biwenger_reflection(
    snapshot: dict,
    exposure: dict | None = None,
) -> dict:
    """
    ¿Biwenger ya descuenta las pujas vivas de maximumBid?

    No lo se, y afecta a si restar es correcto o conservador. Esto
    no lo decide: lo mide, para poder mirarlo cuando haya datos.

    La forma de leerlo: con pujas vivas, comparar maximumBid con
    balance + margen de deuda teorico. Si maximumBid ya viene
    reducido, Biwenger las descuenta.
    """

    if exposure is None:
        exposure = build_bid_exposure(snapshot)

    estado = (
        (snapshot.get("market") or {}).get("status")
        or {}
    )

    comprometido = safe_int(exposure.get("committed_total"))

    if comprometido <= 0:
        return {
            "measurable": False,
            "reason": (
                "Sin pujas vivas no se puede medir. Repetir "
                "cuando haya alguna."
            ),
            "balance": safe_int(estado.get("balance")),
            "maximum_bid": safe_int(estado.get("maximumBid")),
            "committed_total": 0,
        }

    return {
        "measurable": True,
        "balance": safe_int(estado.get("balance")),
        "maximum_bid": safe_int(estado.get("maximumBid")),
        "committed_total": comprometido,
        "reason": (
            "Comparar este maximumBid con el de un snapshot sin "
            "pujas vivas y la misma plantilla. Si baja en el "
            "importe comprometido, Biwenger ya lo descuenta y "
            "nuestro contador esta restando dos veces."
        ),
    }


def print_bid_exposure(
    exposure: dict,
) -> None:

    print()
    print("-" * 70)
    print("EXPOSICION EN PUJAS VIVAS")
    print("-" * 70)

    if not exposure or not exposure.get("available"):
        print(f"  No disponible: {(exposure or {}).get('reason')}")
        return

    if not exposure.get("operation_count"):
        print("  Sin pujas vivas.")
        return

    for operacion in exposure["operations"]:
        print(
            f"  oferta {operacion['offer_id']}  "
            f"{operacion['amount']:>12,} EUR  "
            f"jugadores={operacion['player_ids']}".replace(",", ".")
        )

    print(
        f"  {'TOTAL COMPROMETIDO':<28}"
        f"{exposure['committed_total']:>12,} EUR".replace(",", ".")
    )
