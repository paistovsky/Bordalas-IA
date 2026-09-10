"""
El reloj de la solvencia: la deuda tiene fecha de caducidad.

LA REGLA, DICHA POR EL DUEÑO (12/09/2026)

    "No quiero salir de rojo hoy. Con estar en positivo 6 horas
     antes del inicio de jornada es suficiente."

    Eso cambia el modelo entero. La solvencia deja de ser un
    ESTADO que hay que mantener y pasa a ser un PLAZO que hay que
    cumplir. Lejos del cierre, el deficit es una posicion
    legitima. Cerca, es una emergencia.

EL PLAZO YA ESTABA ESCRITO, Y VALE SEIS

    `computer_offer_reroll_engine.ACCEPT_BEFORE_DEADLINE_HOURS`
    vale 6.0 desde que se escribio, y hace exactamente esto: con
    la jornada encima, una oferta reservada para solvencia se
    cobra aunque todavia no caduque.

    Asi que este reloj NO inventa un plazo nuevo: importa el que
    ya manda. Un segundo numero seria un segundo sitio donde
    equivocarse.

LAS DOS VELOCIDADES

    Aceptar una oferta que ya esta sobre la mesa es INMEDIATO:
    un `PUT /offers/{id}` y el dinero esta. Cabe de sobra en un
    ciclo de media hora.

    Crear liquidez nueva es LENTO, y lo lento no se puede
    improvisar a seis horas.

CUANTO DE LENTO, MEDIDO Y NO INVENTADO

    Sobre el tablon de la liga en la foto de produccion del
    05/09/2026, ventana observada de 67,1 horas:

        SELL_TO_COMPUTER    19 movimientos   uno cada  3,5 h
        BUY_FROM_COMPUTER   10 movimientos   uno cada  6,7 h
        USER_TRANSFER        1 movimiento    uno cada 67,1 h

    UNO. En casi tres dias y con siete managers, una sola compra
    de un manager a otro — y fue la nuestra. Publicar y esperar a
    que un rival puje no es un plan con fecha: es una loteria.

    La liquidez que si tiene reloj es la del Computer. Sus ofertas
    caducan siempre en el reset de las 07:00, en dos cohortes:
    5 ofertas a 16,9 h y 7 a 40,9 h de aquella foto. La diferencia
    entre cohortes es de 24,0 horas exactas.

    De ahi sale el unico margen honesto: si el deficit no esta
    cubierto por ofertas vivas, hace falta al menos un CICLO
    COMPLETO del Computer -24 horas- para que valore lo que
    publiques y te haga una oferta. Menos de eso y el unico camino
    que queda es el de una compra cada 67 horas.

ESTE MODULO NO VENDE NI DECIDE

    Calcula cuanto queda, si el deficit esta cubierto y que
    tocaria hacer. Quien lo ejecuta es el camino de siempre
    -`ACCEPT_RECOVERY_OFFER`-, que existe, esta reconectado y
    tiene guardia de punta a punta desde hoy
    (`test_venta_ejecutable_v1`).
"""

from __future__ import annotations

from src.analysis.computer_offer_reroll_engine import (
    ACCEPT_BEFORE_DEADLINE_HOURS,
)


# El plazo del dueño. Se importa, no se copia: si algun dia
# cambia, cambia en un solo sitio.
SOLVENCY_DEADLINE_HOURS = ACCEPT_BEFORE_DEADLINE_HOURS


# ============================================================
# LO MEDIDO EL 05/09/2026 SOBRE 67,1 HORAS DE TABLON
# ============================================================

# Las ofertas del Computer caducan en el reset de las 07:00. Las
# dos cohortes observadas -16,9 h y 40,9 h- se llevan 24,0 horas
# exactas.
COMPUTER_CYCLE_HOURS = 24.0

# Una sola compra de manager a manager en toda la ventana, con
# siete managers jugando. Es una COTA INFERIOR del tiempo de
# espera, no una media: con n=1 no hay media que dar.
OBSERVED_USER_TRANSFER_HOURS = 67.1

OBSERVED_WINDOW_HOURS = 67.1
OBSERVED_USER_TRANSFERS = 1
OBSERVED_COMPUTER_SALES = 19


# ============================================================
# LOS ESTADOS DEL RELOJ
# ============================================================

SIN_DEUDA = "SIN_DEUDA"

# DEUDA QUE TODAVIA NO EXISTE (10/09/2026)
#
#     No es lo mismo deber dinero que haberlo comprometido. Una
#     puja viva es dinero que saldra SI se gana, y puede no
#     ganarse.
#
#     Merece etiqueta propia porque se trata distinto: con deuda
#     de verdad se vende lo que haga falta; con deuda contingente
#     no se toca a ningun titular, porque una puja no ganada no
#     justifica perder puntos.
DEUDA_CONTINGENTE = "DEUDA_CONTINGENTE"

CUBIERTO = "CUBIERTO"
CUBIERTO_PERO_CADUCA = "CUBIERTO_PERO_CADUCA"
PUBLICAR = "PUBLICAR"
CRITICO = "CRITICO"
EN_EL_PLAZO = "EN_EL_PLAZO"

ESTADO_LABEL = {
    SIN_DEUDA: "Sin deuda",
    DEUDA_CONTINGENTE: "Deuda contingente: se debera si se gana",
    CUBIERTO: "Cubierto por ofertas vivas",
    CUBIERTO_PERO_CADUCA: "Cubierto, pero la oferta caduca antes",
    PUBLICAR: "Hay que crear liquidez ya",
    CRITICO: "Sin margen para crear liquidez",
    EN_EL_PLAZO: "El plazo es AHORA",
}


def euros(valor) -> str:
    """
    El separador de miles, formateado APARTE.

    Hacer `.replace(",", ".")` sobre la frase entera se come las
    comas de la prosa: "cubren los 421.792 EUR. pero caducan". Ya
    paso el 11/09 en `sale_order` y volvio a pasar aqui el mismo
    dia siguiente, asi que ahora hay una funcion y una guardia.
    """

    return f"{int(valor or 0):,}".replace(",", ".")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sellable_offers(offers) -> list:
    """
    Las ofertas que de verdad se pueden cobrar.

    Un jugador protegido no cuenta como liquidez: contarlo seria
    decir que la deuda esta cubierta con dinero que no se va a
    tocar.
    """

    filas = []

    for oferta in (offers or []):

        if not isinstance(oferta, dict):
            continue

        if oferta.get("protection") == "NEVER_AUTO_SELL":
            continue

        importe = safe_int(oferta.get("amount"))

        if importe <= 0:
            continue

        nombres = oferta.get("players") or []

        filas.append(
            {
                "name": (
                    oferta.get("player_name")
                    or (nombres[0] if nombres else None)
                ),
                "amount": importe,
                "hours_to_expiry": safe_float(
                    oferta.get("hours_to_expiry")
                ),
                "solvency_reserved": bool(
                    oferta.get("solvency_reserved")
                ),
                "action": oferta.get("action"),
            }
        )

    return sorted(filas, key=lambda f: f["amount"])


def build_solvency_clock(
    balance,
    hours_to_deadline,
    *,
    offers=None,
    market_clock=None,
    sale_order=None,
    first_kickoff=None,

    # LO QUE YA ESTA GASTADO AUNQUE EL SALDO NO LO DIGA
    #
    #     El 10/09 el dueno pujo 11,8 M a mano y este reloj
    #     siguio publicando "Saldo positivo. El plazo no
    #     aprieta.", porque leia `balance` y una puja viva no
    #     mueve el balance: baja `maximumBid`.
    #
    #     Lo cuenta `pujas_del_dueno`, con tres vias y quedandose
    #     con la mas conservadora. Aqui llega ya contado: este
    #     modulo no lee el mundo.
    committed_bids=0,

    # Los titulares, por nombre. Con deuda contingente no se
    # toca a ninguno, asi que hay que saber quienes son para
    # poder decir si el agujero se tapa sin ellos.
    starters=None,
) -> dict:
    """
    Cuanto queda para el plazo, y si la deuda llega tapada.

    TRES NUMEROS, NO UNO REFUNDIDO

        saldo               lo que hay en la cuenta
        pujas comprometidas lo que saldra si se gana
        saldo efectivo      el peor caso, que es sobre el que se
                            calcula el deficit

    Nunca lanza.
    """

    try:
        saldo = safe_int(balance)

        comprometido = max(0, safe_int(committed_bids))

        # EL PEOR CASO, QUE ES EL QUE HAY QUE PODER MIRAR
        #
        #     Si se ganan todas las pujas vivas. Es el unico
        #     numero con el que la pregunta "¿llego en verde al
        #     T-6h?" tiene una respuesta que no depende de la
        #     suerte.
        efectivo = saldo - comprometido

        deficit = max(-efectivo, 0)

        horas_cierre = safe_float(hours_to_deadline)

        horas_plazo = (
            None
            if horas_cierre is None
            else horas_cierre - SOLVENCY_DEADLINE_HOURS
        )

        vendibles = _sellable_offers(offers)

        # EL HORIZONTE QUE IMPORTA NO ES SIEMPRE EL PLAZO
        #
        #     Preguntar "¿sobreviven las ofertas de hoy hasta el
        #     plazo?" es la pregunta equivocada cuando el plazo
        #     esta a seis dias: las ofertas del Computer se
        #     renuevan CADA 24 HORAS, asi que las de hoy no son
        #     las que van a tapar nada.
        #
        #     La primera version de este reloj decia
        #     "cubierto pero caduca" a 144,7 horas del plazo, que
        #     es una alarma sin sentido. El horizonte relevante es
        #     el plazo o un ciclo del Computer, el que sea menor.
        horizonte = (
            COMPUTER_CYCLE_HOURS
            if horas_plazo is None
            else min(horas_plazo, COMPUTER_CYCLE_HOURS)
        )

        def sobrevive(oferta) -> bool:
            caducidad = oferta["hours_to_expiry"]

            if caducidad is None:
                return True

            return caducidad >= horizonte

        vivas_al_plazo = [o for o in vendibles if sobrevive(o)]

        cubierto_ahora = sum(o["amount"] for o in vendibles)
        cubierto_al_plazo = sum(o["amount"] for o in vivas_al_plazo)

        horas_reset = safe_float(
            (market_clock or {}).get("hours_to_reset")
        )

        # ----------------------------------------------------
        # LA PRIMERA VENTA QUE TAPA EL AGUJERO
        # ----------------------------------------------------
        #
        # De la cola de venta del 11/09, que ya ordena por quien
        # sobra: el primero que tenga oferta viva y llegue al
        # importe. Vender mas de lo necesario es vender de mas.

        # EL MISMO CRITERIO QUE EL CAMINO VIVO, NO OTRO
        #
        #     `offers_to_collect` cobra la oferta mas PEQUEÑA que
        #     tape el agujero, y si ninguna lo tapa, la mas
        #     grande. Aqui se hace exactamente lo mismo sobre la
        #     cola.
        #
        #     Publicar una recomendacion distinta de la que va a
        #     ejecutar la maquina seria la peor de las dos
        #     mentiras: el dueño aprobaria una venta y ocurriria
        #     otra.

        con_oferta = [
            f
            for f in ((sale_order or {}).get("queue") or [])
            if f.get("cash_kind") == "OFERTA_VIVA"
            and safe_int(f.get("cash_now")) > 0
        ]

        tapan = [
            f for f in con_oferta
            if safe_int(f.get("cash_now")) >= deficit
        ]

        elegida = (
            min(tapan, key=lambda f: safe_int(f["cash_now"]))
            if tapan and deficit > 0
            else (
                max(con_oferta, key=lambda f: safe_int(f["cash_now"]))
                if con_oferta
                else None
            )
        )

        recomendada = (
            None
            if elegida is None
            else {
                "name": elegida.get("name"),
                "amount": safe_int(elegida.get("cash_now")),
                "order": elegida.get("order"),
                "reason": elegida.get("reason"),
                "covers_deficit": bool(
                    deficit > 0
                    and safe_int(elegida.get("cash_now")) >= deficit
                ),
            }
        )

        # ----------------------------------------------------
        # EL PLAN DE LOS DOS MUNDOS
        # ----------------------------------------------------
        #
        #     "Si gano, cubro con esto; si pierdo, no he perdido
        #      nada."
        #
        #     Se publica ANTES del reset, que es cuando sirve de
        #     algo. Y si NO existe un plan que cubra sin tocar
        #     titulares, lo dice: es justo lo que el 10/09 no
        #     dijo y por eso el dueno se entero por su cuenta.

        titulares = {
            str(n) for n in (starters or []) if n
        }

        del_banquillo = [
            o for o in vendibles
            if str(o.get("name")) not in titulares
        ]

        sin_titulares = sum(
            o["amount"] for o in del_banquillo
        )

        # LO QUE ES GRATIS EN LOS DOS MUNDOS
        #
        #     Ofertas de gente que no juega, que caducan en el
        #     mismo reset en el que se resuelve la puja. Cobrarlas
        #     no cuesta ni un punto y no cobrarlas las pierde.
        #     Eso es preparacion, no reaccion.
        gratis_ahora = [
            o for o in del_banquillo
            if o["hours_to_expiry"] is not None
            and horas_reset is not None
            and o["hours_to_expiry"] <= horas_reset + 1.0
        ]

        plan = {
            "available": comprometido > 0,
            "committed": comprometido,

            "if_won": {
                "need": deficit,
                "from_bench": sin_titulares,
                "covered": bool(
                    deficit <= 0 or sin_titulares >= deficit
                ),
                "players": [
                    {
                        "name": o["name"],
                        "amount": o["amount"],
                        "hours_to_expiry": o["hours_to_expiry"],
                    }
                    for o in sorted(
                        del_banquillo,
                        key=lambda x: -x["amount"],
                    )
                ],
            },

            "if_lost": {
                "need": 0,
                "reason": (
                    "Si la puja se pierde no hay agujero: el "
                    "saldo se queda como esta."
                ),
            },

            "free_in_both_worlds": [
                {
                    "name": o["name"],
                    "amount": o["amount"],
                    "hours_to_expiry": o["hours_to_expiry"],
                }
                for o in gratis_ahora
            ],

            # LA REGLA, ESCRITA DONDE SE LEE EL PLAN
            "never_sell_starters": True,
        }

        if comprometido <= 0:
            plan["reason"] = (
                "Sin pujas comprometidas no hay dos mundos que "
                "planificar."
            )

        elif deficit <= 0:
            plan["reason"] = (
                f"Aunque se ganen las pujas ({euros(comprometido)} "
                f"EUR), el saldo aguanta: quedaria en "
                f"{euros(efectivo)} EUR."
            )

        elif sin_titulares >= deficit:
            plan["reason"] = (
                f"SI SE GANA: faltan {euros(deficit)} EUR y hay "
                f"{euros(sin_titulares)} EUR en ofertas de gente "
                f"que no juega. Se tapa sin tocar el once. SI SE "
                f"PIERDE: no hay nada que hacer."
            )

        else:
            plan["reason"] = (
                f"SI SE GANA: faltan {euros(deficit)} EUR y las "
                f"ofertas de los que no juegan solo dan "
                f"{euros(sin_titulares)} EUR. NO HAY PLAN QUE "
                f"CUBRA SIN TOCAR A UN TITULAR: lo decide el "
                f"dueno, no la maquina. SI SE PIERDE: no hay "
                f"nada que hacer."
            )

        # ----------------------------------------------------
        # EL ESTADO
        # ----------------------------------------------------

        if deficit > 0 and saldo >= 0:
            # DEUDA CONTINGENTE: el saldo esta en positivo y el
            # agujero lo abre una puja que todavia puede
            # perderse. No es deuda hasta el reset.
            estado = DEUDA_CONTINGENTE

            motivo = (
                f"Saldo {euros(saldo)} EUR, pero hay "
                f"{euros(comprometido)} EUR comprometidos en "
                f"pujas vivas: si se ganan, el saldo queda en "
                f"{euros(efectivo)} EUR. No es deuda todavia. NO "
                f"se vende a ningun titular por una puja que "
                f"puede no ganarse."
            )

        elif deficit <= 0:
            estado = SIN_DEUDA

            motivo = (
                f"Saldo positivo ({euros(saldo)} EUR). El plazo no "
                f"aprieta."
            )

        elif horas_plazo is not None and horas_plazo <= 0:
            # Estamos DENTRO de las seis horas. Es el momento en
            # que la regla del dueño deja de ser una holgura y
            # pasa a ser una orden.
            estado = EN_EL_PLAZO

            motivo = (
                f"Quedan {horas_cierre:.1f} h para el cierre y el "
                f"saldo sigue en {euros(saldo)} EUR. El plazo es "
                f"AHORA: hay que cobrar en este ciclo."
            )

        elif cubierto_al_plazo >= deficit:
            estado = CUBIERTO

            motivo = (
                f"El deficit son {euros(deficit)} EUR y hay "
                f"{euros(cubierto_al_plazo)} EUR en ofertas vivas "
                f"que aguantan las proximas {horizonte:.0f} h. "
                f"Aceptar una oferta es inmediato: no hay prisa."
            )

        elif cubierto_ahora >= deficit:
            estado = CUBIERTO_PERO_CADUCA

            motivo = (
                f"Las ofertas de hoy cubren los {euros(deficit)} "
                f"EUR pero caducan en el proximo reset. Hay que "
                f"cobrar antes de perderlas o esperar a que el "
                f"Computer vuelva a ofertar."
            )

        elif (
            horas_plazo is not None
            and horas_plazo >= COMPUTER_CYCLE_HOURS
        ):
            estado = PUBLICAR

            motivo = (
                f"Las ofertas vivas no cubren los "
                f"{euros(deficit)} EUR y quedan {horas_plazo:.1f} "
                f"h: da tiempo a un ciclo entero del Computer "
                f"({COMPUTER_CYCLE_HOURS:.0f} h). Hay que publicar "
                f"AHORA para que haya oferta antes del plazo."
            )

        else:
            estado = CRITICO

            queda = (
                f"{horas_plazo:.1f} h"
                if horas_plazo is not None
                else "un plazo desconocido"
            )

            motivo = (
                f"Las ofertas vivas no cubren los "
                f"{euros(deficit)} EUR y solo quedan {queda}: "
                f"menos de un ciclo del Computer. El unico camino "
                f"que queda es que un manager compre una "
                f"publicacion, y de eso se ha visto UNO en "
                f"{OBSERVED_WINDOW_HOURS:.0f} horas de tablon."
            )

        # ----------------------------------------------------
        # EL DESEMPATE (punto 2 del encargo)
        # ----------------------------------------------------
        #
        #     "Cerca del plazo, manda la solvencia. Lejos del
        #      plazo, el motor de ofertas puede seguir diciendo
        #      que conserve."
        #
        #     "Cerca" es exactamente el plazo del dueño: dentro de
        #     las seis horas. Y no es un numero nuevo: es el mismo
        #     `ACCEPT_BEFORE_DEADLINE_HOURS` con el que el motor
        #     de reroll ya convierte una oferta reservada en
        #     ACCEPT_BEFORE_EXPIRY.
        #
        #     Ponerlo antes seria malvender con tiempo por
        #     delante, que es la otra forma de perder.

        manda_solvencia = bool(
            deficit > 0
            and horas_cierre is not None
            and horas_cierre <= SOLVENCY_DEADLINE_HOURS
        )

        return {
            "available": True,
            "reason": None,

            # LOS TRES NUMEROS, POR SEPARADO Y NO REFUNDIDOS
            "balance": saldo,
            "committed_bids": comprometido,
            "effective_balance": efectivo,

            # El deficit se calcula sobre el EFECTIVO, que es el
            # peor caso.
            "deficit": deficit,

            "hours_to_deadline": (
                round(horas_cierre, 2)
                if horas_cierre is not None
                else None
            ),

            # El plazo del dueño: T-6h del primer partido.
            "solvency_deadline_hours": SOLVENCY_DEADLINE_HOURS,
            "hours_to_solvency_deadline": (
                round(horas_plazo, 2)
                if horas_plazo is not None
                else None
            ),

            "first_kickoff": first_kickoff,

            "covered_now": cubierto_ahora,
            "covered_at_deadline": cubierto_al_plazo,
            "covered": bool(cubierto_al_plazo >= deficit),

            "offers_alive": len(vendibles),
            "offers_alive_at_deadline": len(vivas_al_plazo),

            "hours_to_computer_reset": horas_reset,
            "computer_cycle_hours": COMPUTER_CYCLE_HOURS,

            "state": estado,
            "state_label": ESTADO_LABEL[estado],
            "reason_text": motivo,

            # ------------------------------------------------
            # EL DESEMPATE (punto 2 del encargo)
            # ------------------------------------------------
            #
            # Cuando el motor de solvencia dice "vende a X" y el
            # de ofertas dice "conserva a X", cerca del plazo
            # manda la solvencia. Lejos, no: malvender con tiempo
            # por delante es la otra forma de perder.
            "solvency_overrides_hold": manda_solvencia,

            "override_reason": (
                (
                    f"Quedan {horas_cierre:.1f} h para el cierre y "
                    f"el saldo es {euros(saldo)} EUR: manda la "
                    f"solvencia por encima del HOLD del motor de "
                    f"ofertas."
                )
                if manda_solvencia and horas_cierre is not None
                else (
                    f"Quedan {horas_plazo:.1f} h de margen: lejos "
                    f"del plazo manda el motor de ofertas, que "
                    f"para eso mira el precio."
                    if horas_plazo is not None and deficit > 0
                    else None
                )
            ),

            "recommended_sale": recomendada,

            # "Si gano, cubro con esto; si pierdo, no he perdido
            # nada." Publicado ANTES del reset.
            "two_world_plan": plan,

            # Lo medido, para que el numero de arriba se pueda
            # discutir con datos y no de memoria.
            "measured": {
                "window_hours": OBSERVED_WINDOW_HOURS,
                "user_transfers": OBSERVED_USER_TRANSFERS,
                "computer_sales": OBSERVED_COMPUTER_SALES,
                "user_transfer_every_hours": (
                    OBSERVED_USER_TRANSFER_HOURS
                ),
            },
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo calcular el reloj de solvencia: "
                f"{type(error).__name__}: {error}"
            ),
            "state": None,
            "recommended_sale": None,
        }
