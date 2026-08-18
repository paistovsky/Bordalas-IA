from __future__ import annotations

from datetime import datetime
from typing import Any

from src.analysis.competitive_transaction_engine import (
    evaluate_sale_to_rival,
    extract_counterparty_from_offer,
)

from src.analysis.competitive_offer_portfolio_engine import (
    build_competitive_offer_portfolio,
    build_offer_replacement_lookup,
)

from src.analysis.negotiation_state_engine import (
    assess_incoming_offer_event,
    empty_state,
)

from src.analysis.computer_offer_reroll_engine import (
    MAX_REROLLS_PER_PLAYER,
    build_computer_offer_reroll_board,
)

from src.analysis.liquidity_manager import (
    build_liquidity_state,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ============================================================
# CONFIGURACION
# ============================================================

FRANCHISE_NEVER_SELL_THRESHOLD = 70.0

# Una oferta excelente no implica vender automaticamente.
# Solo eleva el atractivo economico de la oferta.
PREMIUM_EXCELLENT = 8.0
PREMIUM_GOOD = 3.0
PREMIUM_FAIR = 0.0

# Cuanta puntuacion de venta hace falta para cobrar una oferta.
#
# Mas baja para quien no juega -si esta en el banquillo, el coste
# deportivo de soltarlo es casi cero y basta con que la prima sea
# excelente- y mas alta para quien si juega, porque ahi la venta
# toca el once.
ACCEPT_BENCH_SALE_SCORE = 45.0
ACCEPT_CLEAR_SALE_SCORE = 60.0


# ============================================================
# LA TIERRA DE NADIE ENTRE 0 % Y 3 %
# ============================================================
#
# EL CASO (18/08/2026)
#
#     Alvaro Fidalgo, 75 sobre 100 en venta, suplente. El
#     Computer ofrecio 977.400 EUR, un +1,8 % sobre su precio. En
#     pantalla salio "Conservar buena oferta" y ahi se quedo, con
#     33 horas por delante para caducar.
#
# POR QUE PASABA
#
#     Dos motores con dos definiciones distintas de "buena":
#
#         motor de reroll:    prima >= 0 %  -> buena, no la cambies
#         motor de decision:  prima >= 3 %  -> buena, se puede cobrar
#
#     Entre 0 % y 3 % una oferta es demasiado buena para pedir
#     otra y demasiado floja para cobrarla. No se hace nada con
#     ella y caduca. La palabra "buena" significaba dos cosas en
#     dos ficheros.
#
#     Y no era un caso raro: de las doce ofertas de aquel dia,
#     OCHO caian en esa banda. Prima media +1,8 %.
#
# COMO SE RESUELVE
#
#     La banda tiene que resolverse siempre, en un sentido o en
#     otro. Con un jugador que claramente sobra:
#
#     - Quedan rerolls y queda tiempo -> se pide otra oferta y se
#       persigue el 3 %. Sobre la muestra de aquel dia, un 25 %
#       de las ofertas llegan a cobrables; con los tres intentos
#       que permite el tope, un 58 %.
#
#     - Se acabaron los rerolls o queda poco para caducar -> se
#       cobra igual, aunque sea un +1,8 %. Porque caducar da
#       CERO, y un +1,8 % sobre 960.000 son 17.400 EUR que no
#       vuelven.
#
#     Lo unico claramente mal era no hacer ninguna de las dos.
# ============================================================


# Por debajo de esto no se cobra una oferta floja ni corriendo:
# vender por debajo de mercado no es cobrar, es regalar.
LAST_CALL_MIN_PREMIUM = 0.0

# A partir de aqui ya no da tiempo a perseguir nada mejor. Es el
# mismo margen que usa el camino de solvencia.
LAST_CALL_HOURS = 6.0

# Evitamos aceptar una oferta que destruya un activo que
# claramente sigue en tendencia de revalorizacion.
SPECULATION_HOLD_THRESHOLD = 62.0

# Observer V2: ninguna decision nueva se ejecuta.
OBSERVER_ONLY = True


# ============================================================
# HELPERS
# ============================================================


def parse_hours_to_expiry(
    offer: dict,
    now: datetime | None = None,
) -> float | None:
    """
    Calcula horas hasta caducidad a partir del campo unix `until`.
    """
    until = offer.get("until")

    if until is None:
        return None

    try:
        until = int(until)
    except (TypeError, ValueError):
        return None

    now_ts = (
        now.timestamp()
        if now is not None
        else datetime.now().timestamp()
    )

    return max(
        (until - now_ts) / 3600,
        0.0,
    )


def build_lookup(
    items: list[dict],
    key: str = "id",
) -> dict[int, dict]:

    result = {}

    for item in items:
        value = item.get(key)

        try:
            value = int(value)
        except (TypeError, ValueError):
            continue

        result[value] = item

    return result


def classify_offer_quality(
    premium_percent: float,
) -> str:

    if premium_percent >= PREMIUM_EXCELLENT:
        return "EXCELLENT"

    if premium_percent >= PREMIUM_GOOD:
        return "GOOD"

    if premium_percent >= PREMIUM_FAIR:
        return "FAIR"

    return "BELOW_MARKET"


# ============================================================
# CUANDO UNA OFERTA COMPENSA
# ============================================================
#
# POR QUE ESTA AQUI, EN UNA FUNCION, Y NO ESCRITO DOS VECES
#
#     Esta regla vivia suelta en la rama de "ofertas de otros
#     managers", debajo de la rama del Computer. Y como el
#     Computer se comia su propia rama antes, estas dos
#     condiciones NUNCA se evaluaban para una oferta suya.
#
#     Auditado el 18/08/2026 con doce ofertas del Computer sobre
#     la mesa -44,15 millones- entre ellas Alvaro Fidalgo, 75 de
#     100 en venta, suplente, con la mejor prima de las doce
#     (+4,4 %). Se iba a quedar en plantilla y la oferta iba a
#     caducar, con el saldo en -1,46 millones.
#
#     El unico camino a aceptar una oferta del Computer era
#     ACCEPT_FOR_SOLVENCY, que exige DOS cosas a la vez: que la
#     oferta este reservada para tapar un agujero y que queden
#     menos de seis horas para que caduque. O sea: Pepe solo
#     vendia al Computer cuando le faltaba el dinero y se le
#     acababa el tiempo. Nunca por buen precio.
#
#     Ahora la regla es una sola y la usan los dos caminos. Si
#     algun dia cambia, cambia para ambos.
#
# NO LLEVA VETO DE JERARQUIA, Y ES DELIBERADO
#
#     `sale_intent` si veta a los Dios, los Clave y al portero
#     titular, porque ahi Pepe vende por iniciativa propia. Aqui
#     REACCIONA a una oferta, y la regla del dueño para eso es
#     otra: "Yamal solo se vende si cae por lesion o sancion
#     larga". Un Dios roto seis jornadas es justo el caso en que
#     su puntuacion de venta sube y hay que venderlo.
#
#     Quien protege aqui es la puntuacion, que ya mira la
#     jerarquia: hoy Yamal, Olasagasti, Gustavo Puerta y Dituro
#     estan a 0 sobre 100 y el corte esta en 60.
# ============================================================


def sale_is_worth_it(
    quality: str,
    sale_score: float,
    in_lineup: bool,
) -> tuple[bool, str | None]:
    """
    Si esta oferta compensa venderla. Vale para cualquiera.

    Dos puertas, y basta con una:

    - Prima excelente por alguien que no juega. El coste
      deportivo es asumible porque no estaba en el once.
    - Prima buena por alguien claramente vendible. Aqui el
      jugador PUEDE estar en el once: si su puntuacion de venta
      pasa de 60 es que ya no deberia estar.
    """

    if (
        quality == "EXCELLENT"
        and sale_score >= ACCEPT_BENCH_SALE_SCORE
        and not in_lineup
    ):
        return (
            True,
            "Prima excelente y coste deportivo asumible.",
        )

    if (
        quality in {"GOOD", "EXCELLENT"}
        and sale_score >= ACCEPT_CLEAR_SALE_SCORE
    ):
        return (
            True,
            "Oferta favorable por un activo claramente vendible.",
        )

    return (False, None)


def resolve_dead_zone(
    premium_percent: float,
    sale_score: float,
    hours_to_expiry: float | None,
    rerolls_used: int,
    max_rerolls: int,
    reroll_safe: bool,
) -> tuple[str | None, str | None]:
    """
    Que hacer con una oferta que ni se cobra ni se cambia.

    Devuelve (accion, motivo), o (None, None) si esta oferta no
    esta en la banda o el jugador no sobra.

    Solo actua sobre jugadores que CLARAMENTE sobran. Con el
    resto, quedarse quieto es la respuesta correcta: no hay prisa
    por deshacerse de quien no molesta.
    """

    if sale_score < ACCEPT_CLEAR_SALE_SCORE:
        return (None, None)

    if premium_percent < LAST_CALL_MIN_PREMIUM:
        # Por debajo de mercado. Que la cambie el motor de
        # reroll, que para eso esta.
        return (None, None)

    if premium_percent >= PREMIUM_GOOD:
        # No esta en la banda: la cobra `sale_is_worth_it`.
        return (None, None)

    quedan = max(0, int(max_rerolls) - int(rerolls_used))

    sin_tiempo = (
        hours_to_expiry is not None
        and hours_to_expiry <= LAST_CALL_HOURS
    )

    # ULTIMA LLAMADA. Caducar da cero.
    if sin_tiempo or quedan <= 0 or not reroll_safe:

        falta = (
            "se acaba el plazo"
            if sin_tiempo
            else (
                "no quedan rerolls"
                if quedan <= 0
                else "rerollear dejaria la caja sin cubrir"
            )
        )

        return (
            "ACCEPT_NOW",
            (
                f"Prima de {premium_percent:.1f} % por un jugador "
                f"que sobra y {falta}. Dejarla caducar seria "
                f"cobrar cero."
            ),
        )

    # Hay margen: se persigue una mejor.
    return (
        "REROLL_CANDIDATE",
        (
            f"Prima de {premium_percent:.1f} %: ni para cobrarla "
            f"ni para conservarla. Quedan {quedan} intento(s) "
            f"para buscar una mejor."
        ),
    )


def calculate_economic_score(
    premium_percent: float,
    sale_score: float,
    speculation_score: float,
    price_increment: int,
) -> float:
    """
    Score 0..100:
    - prima de oferta
    - facilidad/beneficio de venta
    - penalizacion si el activo sigue revalorizandose
    """

    score = 50.0

    score += max(
        min(
            premium_percent * 2.0,
            24.0,
        ),
        -20.0,
    )

    score += (
        max(
            min(
                sale_score,
                100.0,
            ),
            0.0,
        )
        - 50.0
    ) * 0.20

    if speculation_score >= 70:
        score -= 15

    elif speculation_score >= 60:
        score -= 8

    elif speculation_score <= 35:
        score += 8

    if price_increment >= 100_000:
        score -= 10

    elif price_increment >= 40_000:
        score -= 5

    elif price_increment < 0:
        score += 6

    return round(
        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),
        1,
    )


# ============================================================
# DECISION INDIVIDUAL
# ============================================================


def decide_incoming_offer(
    offer: dict,
    roster: dict,
    strategic: dict,
    speculation: dict,
    reroll_offer: dict | None,
    recovery_selected_offer_ids: set[int],
    rival_intelligence: dict | None = None,
    competitive_context: dict | None = None,
) -> dict:

    offer_id = offer.get("offer_id")

    player_id = int(
        offer.get("player_id")
        or 0
    )

    amount = int(
        offer.get("amount", 0)
        or 0
    )

    market_value = int(
        offer.get("market_value", 0)
        or 0
    )

    premium_percent = float(
        offer.get("delta_percent", 0.0)
        or 0.0
    )

    franchise_score = float(
        strategic.get(
            "franchise_score",
            0,
        )
        or 0
    )

    strategic_score = float(
        strategic.get(
            "strategic_score",
            0,
        )
        or 0
    )

    sale_score = float(
        roster.get(
            "sale_score",
            0,
        )
        or 0
    )

    protection = roster.get(
        "protection",
        "NORMAL",
    )

    in_lineup = bool(
        roster.get(
            "in_lineup",
            False,
        )
    )

    speculation_score = float(
        speculation.get(
            "speculation_score",
            50,
        )
        or 50
    )

    speculation_action = speculation.get(
        "speculation_action",
        "UNKNOWN",
    )

    price_increment = int(
        speculation.get(
            "price_increment",
            roster.get(
                "price_increment",
                0,
            ),
        )
        or 0
    )

    economic_score = (
        calculate_economic_score(
            premium_percent=
                premium_percent,

            sale_score=
                sale_score,

            speculation_score=
                speculation_score,

            price_increment=
                price_increment,
        )
    )

    quality = (
        classify_offer_quality(
            premium_percent
        )
    )

    # El recovery plan clasico sirve para saber quÃ© ofertas
    # podrÃ­an cubrir saldo, pero NO significa que debamos aceptar
    # ahora. La fuente de verdad temporal para Computer es
    # computer_offer_reroll_engine / solvency_guarantee.
    recovery_selected = (
        offer_id
        in recovery_selected_offer_ids
    )

    reroll_action = (
        reroll_offer.get(
            "action"
        )
        if reroll_offer
        else None
    )

    reroll_safe = bool(
        reroll_offer
        and
        reroll_offer.get(
            "reroll_safe",
            False,
        )
    )

    solvency_reserved = bool(
        reroll_offer
        and
        reroll_offer.get(
            "solvency_reserved",
            False,
        )
    )

    counterparty = (
        extract_counterparty_from_offer(
            offer
        )
    )

    counterparty_type = (
        counterparty.get(
            "type",
            "UNKNOWN",
        )
    )

    counterparty_id = (
        counterparty.get(
            "id"
        )
    )

    competitive_context = (
        competitive_context
        or {}
    )

    current_balance = (
        competitive_context.get(
            "current_balance"
        )
    )

    deadline_context = (
        competitive_context.get(
            "deadline_context",
            {},
        )
        or {}
    )

    replacement_status = (
        competitive_context.get(
            "replacement_status",
            "UNKNOWN",
        )
    )

    replacement_detail = (
        competitive_context.get(
            "replacement_detail",
            {},
        )
        or {}
    )

    sporting_opportunity_cost = (
        replacement_detail.get(
            "sporting_opportunity_cost",
            {},
        )
        or {}
    )

    empty_slot_penalty_points = (
        competitive_context.get(
            "empty_slot_penalty_points"
        )
    )

    reasons = []

    # ========================================================
    # NEVER SELL
    # ========================================================

    if (
        protection == "NEVER_AUTO_SELL"
        or
        franchise_score
        >= FRANCHISE_NEVER_SELL_THRESHOLD
    ):

        action = "NEVER_SELL"
        confidence = 100

        reasons.append(
            "Jugador Franchise/NEVER_AUTO_SELL."
        )

    # ========================================================
    # COMPUTER: RESPETAR SU MOTOR COMO FUENTE DE VERDAD
    # ========================================================

    # DOS REGIMENES SEGUN SI OTRO MOTOR TUVO OPINION (18/08/2026)
    #
    # Esta rama exigia ademas `reroll_offer is not None`. Si el
    # motor de reroll no habia opinado sobre una oferta del
    # Computer, la oferta se caia hacia abajo y la decidian las
    # reglas de los managers.
    #
    # O sea: la misma oferta se juzgaba con dos varas distintas
    # segun si otro motor la habia mirado o no, y eso no lo
    # decide nadie, lo decide el azar de que exista una entrada.
    #
    # Ahora entra toda oferta del Computer. Sin entrada de reroll,
    # `reroll_action` es None y cae al else, que aplica la misma
    # regla que aplicaria abajo. Los dos regimenes convergen.
    elif counterparty_type == "COMPUTER":

        if reroll_action == "ACCEPT_BEFORE_EXPIRY":

            action = "ACCEPT_FOR_SOLVENCY"
            confidence = 99

            reasons.append(
                "Oferta Computer necesaria para solvencia "
                "y prÃ³xima a caducar."
            )

        elif solvency_reserved:

            action = "HOLD_SOLVENCY_RESERVED"
            confidence = 99

            reasons.append(
                "Oferta marcada SOLVENCY_RESERVED. "
                "Se conserva como garantÃ­a de liquidez y "
                "no se acepta ni rerollea mientras siga reservada."
            )

        elif reroll_action == "REROLL_CANDIDATE":

            action = "REROLL_CANDIDATE"
            confidence = 95

            reasons.append(
                "Computer Reroll Engine autoriza buscar "
                "una oferta mejor manteniendo solvencia."
            )

        elif reroll_action == "KEEP_PROTECTED":

            action = "NEVER_SELL"
            confidence = 100

            reasons.append(
                "Computer Reroll Engine protege este activo."
            )

        else:

            # ------------------------------------------------
            # AQUI SE COBRA
            # ------------------------------------------------
            #
            # El motor de reroll ya ha dicho lo suyo y no pide ni
            # reroll ni reserva: la oferta se queda como esta. Es
            # el momento de preguntarse si compensa cobrarla, que
            # es justo lo que nunca se preguntaba.
            #
            # Y se pregunta con la MISMA funcion que usa el
            # camino de los managers, no con una copia.
            # ------------------------------------------------

            compensa, motivo = sale_is_worth_it(
                quality=quality,
                sale_score=sale_score,
                in_lineup=in_lineup,
            )

            banda_accion, banda_motivo = resolve_dead_zone(
                premium_percent=premium_percent,
                sale_score=sale_score,
                hours_to_expiry=parse_hours_to_expiry(offer),
                rerolls_used=int(
                    (reroll_offer or {}).get("reroll_count") or 0
                ),
                max_rerolls=MAX_REROLLS_PER_PLAYER,
                reroll_safe=reroll_safe,
            )

            if compensa:

                action = "ACCEPT_NOW"
                confidence = 86

                reasons.append(motivo)

            elif banda_accion is not None:

                # Ni se cobraba ni se cambiaba: se quedaba
                # mirando hasta caducar.
                action = banda_accion
                confidence = 82

                reasons.append(banda_motivo)

            elif reroll_action == "KEEP_GOOD_OFFER":

                action = "KEEP_GOOD_OFFER"
                confidence = 90

                reasons.append(
                    "Oferta Computer buena, pero el jugador no "
                    "esta para vender: se conserva la "
                    "opcionalidad."
                )

            elif reroll_action == "KEEP_OFFER":

                action = "HOLD_OFFER"
                confidence = 88

                reasons.append(
                    "Computer Reroll Engine considera que el "
                    "reroll no compensa con la informacion "
                    "actual."
                )

            else:

                action = "HOLD_OFFER"
                confidence = 80

                reasons.append(
                    "Oferta Computer sin señal ejecutable "
                    "especifica; se conserva en observacion."
                )

    # ========================================================
    # OFERTAS DE OTROS MANAGERS / CASOS NO COMPUTER
    # ========================================================

    elif (
        speculation_score
        >= SPECULATION_HOLD_THRESHOLD
        and
        price_increment > 0
        and
        quality != "EXCELLENT"
    ):

        action = "HOLD_OFFER"
        confidence = 85

        reasons.append(
            "El activo mantiene una seÃ±al especulativa positiva."
        )

    # LA MISMA REGLA QUE ARRIBA, NO UNA COPIA.
    #
    # Estas dos condiciones estaban escritas a mano aqui, y por
    # estar debajo de la rama del Computer no se aplicaban nunca
    # a sus ofertas. Ahora viven en `sale_is_worth_it` y las usan
    # los dos caminos: si un dia cambia el criterio, cambia para
    # ambos.
    elif sale_is_worth_it(
        quality=quality,
        sale_score=sale_score,
        in_lineup=in_lineup,
    )[0]:

        action = "ACCEPT_NOW"
        confidence = 88

        reasons.append(
            sale_is_worth_it(
                quality=quality,
                sale_score=sale_score,
                in_lineup=in_lineup,
            )[1]
        )

    elif quality in {
        "GOOD",
        "EXCELLENT",
    }:

        action = "KEEP_GOOD_OFFER"
        confidence = 80

        reasons.append(
            "Oferta favorable; se conserva sin vender automÃ¡ticamente."
        )

    else:

        action = "HOLD_OFFER"
        confidence = 75

        reasons.append(
            "No existe ventaja suficiente para aceptar ahora."
        )

    # ========================================================
    # COMPETITIVE TRANSACTION ENGINE V1 - OBSERVER
    # ========================================================
    #
    # IMPORTANTE:
    # - NO cambia `action`.
    # - NO ejecuta aceptar/rechazar/contraofertar.
    # - Solo calcula que haria Pepe si el comprador es un manager.
    # ========================================================

    competitive_observer = None

    if (
        counterparty_type == "MANAGER"
        and
        counterparty_id is not None
        and
        rival_intelligence is not None
    ):

        competitive_observer = (
            evaluate_sale_to_rival(
                amount=
                    amount,

                market_value=
                    market_value,

                rival_user_id=
                    counterparty_id,

                rival_intelligence=
                    rival_intelligence,

                franchise_score=
                    franchise_score,

                strategic_score=
                    strategic_score,

                sale_score=
                    sale_score,

                speculation_score=
                    speculation_score,

                in_lineup=
                    in_lineup,

                price_increment=
                    price_increment,

                current_balance=
                    current_balance,

                deadline_context=
                    deadline_context,

                replacement_status=
                    replacement_status,

                empty_slot_penalty_points=
                    empty_slot_penalty_points,

                sporting_opportunity_cost=
                    sporting_opportunity_cost,
            )
        )

    # ========================================================
    # CONTEXTO EXPLICATIVO
    # ========================================================

    if recovery_selected:
        reasons.append(
            "El recovery plan clÃ¡sico la incluye como posible "
            "fuente de caja, pero eso NO fuerza aceptaciÃ³n inmediata."
        )

    if solvency_reserved:
        reasons.append(
            "SOLVENCY_RESERVED=SI."
        )

    if in_lineup:
        reasons.append(
            "Forma parte del XI actual."
        )

    if price_increment > 0:
        reasons.append(
            f"Valor de mercado subiendo: +{price_increment:,} EUR."
        )

    if speculation_action not in {
        None,
        "UNKNOWN",
    }:
        reasons.append(
            f"Speculation: {speculation_action} ({speculation_score:.1f})."
        )

    return {
        "offer_id":
            offer_id,

        "player_id":
            player_id,

        "player_name":
            offer.get(
                "player_name"
            ),

        "counterparty_type":
            counterparty_type,

        "counterparty_id":
            counterparty_id,

        "counterparty_name":
            (
                (
                    competitive_observer.get(
                        "rival",
                        {},
                    )
                    or {}
                ).get(
                    "name"
                )
                if competitive_observer
                else counterparty.get(
                    "name"
                )
            ),

        "competitive_observer":
            competitive_observer,

        "competitive_observer_decision":
            (
                competitive_observer.get(
                    "decision"
                )
                if competitive_observer
                else None
            ),

        "competitive_counter_amount":
            (
                competitive_observer.get(
                    "counter_amount"
                )
                if competitive_observer
                else None
            ),

        # V1.7: Competitive es la autoridad de DECISION para
        # ofertas de managers, pero sigue siendo OBSERVER ONLY.
        # Estos campos NO se conectan al executor todavia.
        "decision_authority":
            (
                "COMPETITIVE"
                if (
                    counterparty_type == "MANAGER"
                    and competitive_observer is not None
                )
                else "LEGACY"
            ),

        "authoritative_decision":
            (
                competitive_observer.get("decision")
                if (
                    counterparty_type == "MANAGER"
                    and competitive_observer is not None
                )
                else action
            ),

        "authoritative_counter_amount":
            (
                competitive_observer.get("counter_amount")
                if (
                    counterparty_type == "MANAGER"
                    and competitive_observer is not None
                )
                else None
            ),

        "authority_observer_only":
            True,

        "amount":
            amount,

        "market_value":
            market_value,

        "premium_percent":
            round(
                premium_percent,
                2,
            ),

        "offer_quality":
            quality,

        "franchise_score":
            franchise_score,

        "strategic_score":
            strategic_score,

        "sale_score":
            sale_score,

        "protection":
            protection,

        "in_lineup":
            in_lineup,

        "speculation_score":
            speculation_score,

        "speculation_action":
            speculation_action,

        "price_increment":
            price_increment,

        "economic_score":
            economic_score,

        "recovery_selected":
            recovery_selected,

        "solvency_reserved":
            solvency_reserved,

        "reroll_safe":
            reroll_safe,

        "reroll_action":
            reroll_action,

        "decision":
            action,

        "confidence":
            confidence,

        "automatic":
            False,

        "observer_only":
            OBSERVER_ONLY,

        "reasons":
            reasons,

        "raw_offer":
            offer,
    }


# ============================================================
# BOARD GLOBAL
# ============================================================


def build_offer_decision_board(
    snapshot: dict,
    rival_intelligence: dict | None = None,
    negotiation_state: dict | None = None,
) -> dict:

    offer_board = (
        build_offer_board(
            snapshot
        )
    )

    negotiation_state = (
        negotiation_state
        or
        empty_state()
    )

    liquidity = (
        build_liquidity_state(
            snapshot
        )
    )

    offer_liquidity = (
        offer_board.get(
            "liquidity",
            {},
        )
        or {}
    )

    deadline_context = (
        offer_liquidity.get(
            "deadline",
            {},
        )
        or {}
    )

    current_balance = int(
        (
            snapshot.get(
                "market",
                {},
            )
            .get(
                "status",
                {},
            )
            or {}
        ).get(
            "balance",
            0,
        )
        or 0
    )

    competitive_context = {
        "current_balance":
            current_balance,

        "deadline_context":
            deadline_context,

        # V1.2 no inventa sustitutos.
        # Cuando integremos roster/lineup replacement planner,
        # este valor se refinara por jugador.
        "replacement_status":
            "UNKNOWN",

        # No hardcodeamos -4 hasta validar configuracion concreta.
        "empty_slot_penalty_points":
            None,
    }

    strategic_board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="strategic",
        )
    )

    speculation_board = (
        build_speculation_board(
            snapshot
        )
    )

    reroll_board = (
        build_computer_offer_reroll_board(
            snapshot=
                snapshot,

            persist_history=
                False,
        )
    )

    roster_lookup = {
        int(
            item["id"]
        ):
            item

        for item
        in liquidity.get(
            "roster",
            [],
        )
    }

    strategic_lookup = (
        build_lookup(
            strategic_board,
            key="id",
        )
    )

    speculation_lookup = (
        build_lookup(
            speculation_board.get(
                "owned",
                [],
            ),
            key="id",
        )
    )

    reroll_lookup = {
        int(
            player_id
        ):
            reroll

        for reroll
        in reroll_board.get(
            "offers",
            [],
        )

        for player_id
        in reroll.get(
            "player_ids",
            [],
        )
    }

    recovery = (
        liquidity.get(
            "recovery",
            {},
        )
        or {}
    )

    recovery_selected_offer_ids = {
        int(
            item["offer_id"]
        )

        for item
        in recovery.get(
            "selected",
            [],
        )

        if item.get(
            "offer_id"
        )
        is not None
    }

    incoming_candidates = (
        liquidity.get(
            "incoming_offers",
            [],
        )
        or []
    )

    replacement_lookup = (
        build_offer_replacement_lookup(
            snapshot=
                snapshot,

            offers=
                incoming_candidates,
        )
    )

    decisions = []

    for incoming in incoming_candidates:

        player_id = int(
            incoming.get(
                "player_id",
                0,
            )
            or 0
        )

        decision = (
            decide_incoming_offer(
                offer=
                    incoming,

                roster=
                    roster_lookup.get(
                        player_id,
                        {},
                    ),

                strategic=
                    strategic_lookup.get(
                        player_id,
                        {},
                    ),

                speculation=
                    speculation_lookup.get(
                        player_id,
                        {},
                    ),

                reroll_offer=
                    reroll_lookup.get(
                        player_id
                    ),

                recovery_selected_offer_ids=
                    recovery_selected_offer_ids,

                rival_intelligence=
                    rival_intelligence,

                competitive_context=
                    {
                        **competitive_context,

                        "replacement_status":
                            (
                                replacement_lookup.get(
                                    player_id,
                                    {},
                                )
                                or {}
                            ).get(
                                "replacement_status",
                                "UNKNOWN",
                            ),

                        "replacement_detail":
                            replacement_lookup.get(
                                player_id,
                                {},
                            ),
                    },
            )
        )


        competitive = (
            decision.get(
                "competitive_observer"
            )
            or {}
        )

        if (
            decision.get(
                "counterparty_type"
            )
            ==
            "MANAGER"
        ):

            negotiation_observer = (
                assess_incoming_offer_event(
                    state=
                        negotiation_state,

                    offer_id=
                        decision.get(
                            "offer_id"
                        ),

                    player_id=
                        decision.get(
                            "player_id"
                        ),

                    rival_user_id=
                        decision.get(
                            "counterparty_id"
                        ),

                    rival_amount=
                        decision.get(
                            "amount",
                            0,
                        ),

                    proposed_decision=
                        competitive.get(
                            "decision"
                        ),

                    proposed_counter_amount=
                        competitive.get(
                            "counter_amount"
                        ),
                )
            )

        else:

            negotiation_observer = None

        decision[
            "negotiation_observer"
        ] = negotiation_observer

        decisions.append(
            decision
        )
    decision_priority = {
        "NEVER_SELL": 100,
        "ACCEPT_FOR_SOLVENCY": 95,
        "HOLD_SOLVENCY_RESERVED": 90,
        "REROLL_CANDIDATE": 85,
        "ACCEPT_NOW": 80,
        "KEEP_GOOD_OFFER": 60,
        "HOLD_OFFER": 50,
    }

    decisions.sort(
        key=lambda item: (
            decision_priority.get(
                item["decision"],
                0,
            ),
            item["confidence"],
            item["economic_score"],
        ),
        reverse=True,
    )

    grouped = {}

    for decision in decisions:
        grouped.setdefault(
            decision[
                "decision"
            ],
            [],
        ).append(
            decision
        )

    competitive_portfolio = (
        build_competitive_offer_portfolio(
            snapshot=
                snapshot,

            decisions=
                decisions,
        )
    )

    return {
        "observer_only":
            OBSERVER_ONLY,

        "offer_count":
            len(
                decisions
            ),

        "replacement_lookup":
            replacement_lookup,

        "competitive_portfolio":
            competitive_portfolio,

        "negotiation_observer_state":
            negotiation_state,

        "decisions":
            decisions,

        "grouped":
            grouped,

        "accept_now":
            grouped.get(
                "ACCEPT_NOW",
                [],
            ),

        "accept_for_solvency":
            grouped.get(
                "ACCEPT_FOR_SOLVENCY",
                [],
            ),

        "hold_solvency_reserved":
            grouped.get(
                "HOLD_SOLVENCY_RESERVED",
                [],
            ),

        "reroll_candidates":
            grouped.get(
                "REROLL_CANDIDATE",
                [],
            ),

        "hold":
            (
                grouped.get(
                    "HOLD_OFFER",
                    [],
                )
                +
                grouped.get(
                    "KEEP_GOOD_OFFER",
                    [],
                )
            ),

        "never_sell":
            grouped.get(
                "NEVER_SELL",
                [],
            ),

        "recovery":
            recovery,

        "reroll":
            reroll_board,

        "liquidity":
            liquidity,

        "speculation":
            speculation_board,

        "offer_board":
            offer_board,
    }
