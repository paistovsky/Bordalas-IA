"""
LA REGLA DEL COBRO EN DEFICIT

    Si hay deficit, se acepta la oferta de mejor prima entre los
    jugadores que NO estan en el once, y solo hasta volver a
    positivo. Ni un euro mas.

    Decidida por el dueno el 19/09/2026. No hay reloj, no hay
    ventana de seis horas, no hay espera.

POR QUE, MEDIDO

    Estar en rojo no es un riesgo lejano: apaga la compra
    entera. Con el saldo en -455.766 el presupuesto de fichaje
    sale `blocked_by: SIN_CAPACIDAD`, y de ahi cuelga toda la
    rama del orquestador que genera el candidato de puja. El
    19/09 costo que Chust no se pujara solo.

    Y esperar tampoco es gratis: Boyomo pagaba +4,9 % y bajaba
    30.000 EUR al dia.

LOS DOS FRENOS QUE TIENE QUE HACER CEDER

    No es uno, son dos, y levantar solo el primero no desbloquea
    nada:

    1. HOLD_SOLVENCY_RESERVED
       `solvency_engine.calculate_offer_reservations` reserva
       ofertas hasta tapar la deuda -`secured_needed = max(...,
       current_debt)`- y `computer_offer_reroll_engine` solo
       levanta esa reserva por RELOJ: las dos puertas a <= 6,0 h.
       El deficit no entra en esa decision.

    2. KEEP_GOOD_OFFER
       La rama por defecto de una oferta favorable. Ni siquiera
       mira la solvencia.

    Esta regla pasa por delante de los dos.

POR QUE "SOLO HASTA VOLVER A POSITIVO"

    Cada oferta aceptada es un jugador que se va. Cobrar de mas
    para tener colchon es vender plantilla por comodidad. Se
    ordena por prima -lo que mejor pagan primero- y se para en
    cuanto la suma cubre el deficit.

POR QUE "LOS QUE NO ESTAN EN EL ONCE"

    Es `A_NO_XI` con un criterio de orden. El once no se toca
    para tapar un agujero de caja: los puntos son el marcador y
    la caja es el medio.

ENTREGADO APAGADO

    `BORDALAS_COBRAR_EN_DEFICIT`. Apagado, el comportamiento es
    el de siempre y los dos frenos siguen mandando.
"""

from __future__ import annotations

import os


REGLA_ENV = "BORDALAS_COBRAR_EN_DEFICIT"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def regla_activa() -> bool:
    """
    Si la regla del cobro en deficit esta encendida.

    Forma fija. Nunca lanza.
    """

    return str(
        os.environ.get(REGLA_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def _esta_en_el_once(oferta: dict) -> bool:
    """
    Si algun jugador de esta oferta esta en el once.

    SIN SABERLO, SE SUPONE QUE SI. Es el lado seguro: equivocarse
    diciendo que no esta cuesta un titular; equivocarse diciendo
    que si cuesta esperar a la siguiente oferta.
    """

    if oferta.get("in_lineup") is not None:
        return bool(oferta.get("in_lineup"))

    jugadores = oferta.get("players") or []

    if not jugadores:
        # Una oferta sin jugadores no se puede juzgar, y no se
        # adivina.
        return True

    for jugador in jugadores:

        if not isinstance(jugador, dict):
            return True

        marca = (
            jugador.get("in_lineup")
            if jugador.get("in_lineup") is not None
            else jugador.get("is_starter")
        )

        if marca is None:
            return True

        if bool(marca):
            return True

    return False


def el_cobro_que_cierra(
    deficit,
    ofertas: list | None,
) -> dict:
    """
    Que ofertas cierran el deficit, con el menor dano al once.

    El orden es POR PRIMA, de mayor a menor: lo que mejor pagan
    primero. A igualdad de prima manda el importe mayor, porque
    cierra el agujero con menos jugadores.

    Forma fija, nunca lanza. Devuelve siempre `descartadas` con
    el motivo de cada una: una oferta que no entra tiene que
    poder explicarse sin abrir el codigo.
    """

    vacio = {
        "available": False,
        "deficit": safe_int(deficit),
        "seleccionadas": [],
        "offer_ids": set(),
        "total": 0,
        "cubre": False,
        "sobra": 0,
        "descartadas": [],
        "reason": None,
    }

    try:
        falta = safe_int(deficit)

        if falta <= 0:
            return {
                **vacio,
                "available": True,
                "cubre": True,
                "reason": "No hay deficit: no se cobra nada.",
            }

        filas = [
            o for o in (ofertas or []) if isinstance(o, dict)
        ]

        if not filas:
            return {
                **vacio,
                "reason": (
                    "La lista de ofertas llega vacia: sin ofertas "
                    "no hay cobro que planear."
                ),
            }

        fuera_del_once = []

        descartadas = []

        for oferta in filas:

            if _esta_en_el_once(oferta):
                descartadas.append({
                    "offer_id": oferta.get("offer_id"),
                    "amount": safe_int(oferta.get("amount")),
                    "motivo": "EN_EL_ONCE",
                    "reason": (
                        "Esta en el once. El once no se toca para "
                        "tapar un agujero de caja."
                    ),
                })
                continue

            if safe_int(oferta.get("amount")) <= 0:
                descartadas.append({
                    "offer_id": oferta.get("offer_id"),
                    "amount": 0,
                    "motivo": "SIN_IMPORTE",
                    "reason": "Sin importe no cierra nada.",
                })
                continue

            fuera_del_once.append(oferta)

        # MEJOR PRIMA PRIMERO. A igualdad, el importe mayor:
        # cierra el agujero con menos jugadores.
        fuera_del_once.sort(
            key=lambda o: (
                -safe_float(o.get("premium_percent")),
                -safe_int(o.get("amount")),
            )
        )

        seleccionadas = []

        total = 0

        for oferta in fuera_del_once:

            if total >= falta:
                descartadas.append({
                    "offer_id": oferta.get("offer_id"),
                    "amount": safe_int(oferta.get("amount")),
                    "motivo": "YA_ESTA_CUBIERTO",
                    "reason": (
                        "El deficit ya queda tapado sin esta. No "
                        "se cobra de mas."
                    ),
                })
                continue

            seleccionadas.append(oferta)

            total += safe_int(oferta.get("amount"))

        cubre = total >= falta

        return {
            "available": True,
            "deficit": falta,
            "seleccionadas": seleccionadas,
            "offer_ids": {
                o.get("offer_id")
                for o in seleccionadas
                if o.get("offer_id") is not None
            },
            "total": total,
            "cubre": cubre,
            "sobra": max(total - falta, 0),
            "descartadas": descartadas,
            "reason": (
                (
                    f"Con {len(seleccionadas)} oferta(s) de fuera "
                    f"del once se recuperan {total:,} EUR y el "
                    f"deficit de {falta:,} queda tapado."
                    if cubre
                    else
                    f"Las {len(seleccionadas)} oferta(s) de fuera "
                    f"del once suman {total:,} EUR y NO llegan a "
                    f"los {falta:,} del deficit: faltarian "
                    f"{falta - total:,}. Se aceptan igual porque "
                    f"acercarse es mejor que quedarse quieto, "
                    f"pero el once no se toca y con esto no se "
                    f"sale del rojo."
                ).replace(",", ".")
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo planear el cobro: "
                f"{type(error).__name__}: {error}"
            ),
        }
