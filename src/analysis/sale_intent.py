"""
A quien soltaria Pepe si nadie le obligase. SOLO OBSERVA.

POR QUE EXISTE

    Para comprar, Pepe tiene iniciativa: mira el mercado, elige y
    puja. Para vender solo REACCIONA -si el Computer le ofrece
    dinero, decide si o no- y `roster_planner` unicamente propone
    ventas cuando falta caja (`liquidity_shortfall > 0`).

    O sea que un jugador puede estar deshaciendose solo -Reserva
    en su equipo, o roto hasta enero- y, mientras la caja aguante,
    nadie propone nada. Se queda en la plantilla perdiendo valor
    cada semana.

    El 17/08/2026 el analisis ya lo sabia: Hugo Rincon puntuaba 60
    sobre 100 en vender -Reserva en el Athletic, titular solo por
    falta de alternativa- y no habia forma de que eso llegase a
    ninguna decision.

ESTE MODULO NO VENDE

    A proposito. No importa ningun executor, no escribe en disco y
    no devuelve nada que un executor sepa ejecutar. Dice a quien
    venderia y por que, y ya.

    Vender mal no es como comprar mal. Una compra mala cuesta
    dinero y se corrige; una venta mala te deja SIN el jugador, y
    en un fantasy no se recupera: se lo lleva otro. Asi que esto
    corre en observacion hasta que su dueño haya leido unas
    cuantas propuestas y le parezcan sensatas.

EL LISTON ES MAS ALTO QUE PARA VENDER POR NECESIDAD

    `roster_planner` vende a partir de 40 puntos cuando falta
    caja: ahi no hay eleccion, hay que sacar dinero de algun sitio
    y se busca el menor daño.

    Proponer una venta sin necesitar el dinero es otra cosa y pide
    mas conviccion: 60, que es el corte de "VENDER" del propio
    analisis. Entre 40 y 60 se vigila y se dice, pero no se
    propone.
"""

from __future__ import annotations

from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)

from src.analysis.sales_analyzer import analyze_sales


# Corte para PROPONER una venta sin necesitar el dinero.
PROPOSE_SCORE = 60

# Corte para VIGILAR: se dice, no se propone.
WATCH_SCORE = 40


# ============================================================
# LOS INTOCABLES
# ============================================================
#
# DECISION DEL DUEÑO (18/08/2026)
#
#     "Que no me venda a Yamal ni haga locuras."
#     Intocables: los Dios, los Clave y el portero titular.
#
# POR QUE HACE FALTA UNA LISTA APARTE
#
#     `sales_analyzer` ya penaliza fuerte a los escalones altos
#     -un Dios arranca con -30 en la puntuacion de venta- pero
#     eso es un PESO, no un veto. Un Dios lesionado seis jornadas
#     acumula suficiente por otras vias para pasar de 60, y
#     entonces se propondria. Un peso se puede remontar; un veto
#     no.
#
#     Y hoy Yamal solo esta a salvo por accidente: el guardarrail
#     posicional bloquea la venta porque hay exactamente dos
#     delanteros. El dia que entre un tercero, esa proteccion
#     desaparece sola y nadie se entera.
#
# EL PORTERO TITULAR VA APARTE
#
#     No por jerarquia -Dituro es Importante, no Clave- sino por
#     el puesto: un portero no se rota, y quedarse sin el titular
#     a media jornada no se arregla comprando otro.
#
# SIN JERARQUIA NO SE VENDE
#
#     Aqui "ausencia de dato" se resuelve al reves que en el
#     once. Alinear a quien no conoces cuesta unos puntos;
#     venderlo te deja SIN el jugador, y en un fantasy eso no se
#     recupera: se lo lleva otro.
#
#     Asi que a un jugador sin escalon conocido no se le propone.
#     No es que sea intocable: es que no sabemos lo que es, y
#     esta decision no admite suposiciones.
# ============================================================


# De Clave para arriba no se toca. Es el valor de FF, no la
# etiqueta: comparar numeros no se rompe con un acento.
UNTOUCHABLE_HIERARCHY = 50

GOALKEEPER_POSITION = 1


def untouchable_reason(jugador: dict) -> str | None:
    """
    Por que este jugador no se propone. None si se puede.
    """

    escalon = jugador.get("hierarchy_value")

    if not escalon:
        return (
            "sin escalon conocido: vender a ciegas no se "
            "deshace"
        )

    if int(escalon) >= UNTOUCHABLE_HIERARCHY:
        return (
            f"{jugador.get('hierarchy') or 'escalon alto'}: "
            f"intocable por decision del dueño"
        )

    if (
        int(jugador.get("position") or 0) == GOALKEEPER_POSITION
        and
        jugador.get("in_lineup")
    ):
        return "portero titular: no se rota y no se improvisa"

    return None


def build_sale_intent(
    snapshot: dict,
    *,
    propose_score: int = PROPOSE_SCORE,
    watch_score: int = WATCH_SCORE,
) -> dict:
    """
    Lo que Pepe soltaria hoy, en orden, y lo que se lo impide.

    Nunca lanza: si algo falla se devuelve no disponible con el
    motivo. Esto es informacion, no puede tumbar un ciclo.
    """

    try:
        analisis = analyze_sales(snapshot)

    except Exception as error:
        return {
            "available": False,
            "reason": f"{type(error).__name__}: {error}",
            "proposals": [],
            "watch": [],
            "blocked": [],
        }

    try:
        guardrail = build_position_guardrail(
            snapshot.get("my_team")
        )

    except Exception as error:
        return {
            "available": False,
            "reason": (
                f"Sin guardarrail posicional no se propone "
                f"ninguna venta: {type(error).__name__}: {error}"
            ),
            "proposals": [],
            "watch": [],
            "blocked": [],
        }

    propuestas = []
    vigilados = []
    bloqueados = []
    intocables = []

    # El guardarrail mira CONJUNTOS, no ventas sueltas: dos ventas
    # inocentes por separado pueden dejar una posicion vacia. Por
    # eso se va acumulando y se pregunta por la lista entera cada
    # vez.
    acumuladas: list[int] = []

    for jugador in analisis:

        puntuacion = jugador.get("sale_score") or 0

        if puntuacion < watch_score:
            continue

        ficha = {
            "id": jugador.get("id"),
            "name": jugador.get("name"),
            "position": jugador.get("position"),
            "price": jugador.get("price"),
            "hierarchy": jugador.get("hierarchy"),
            "starter_probability": (
                jugador.get("starter_probability")
            ),
            "availability": jugador.get("availability"),
            "matchdays_out": jugador.get("matchdays_out"),
            "sale_score": puntuacion,
            "recommendation": jugador.get("recommendation"),
            "reasons": jugador.get("reasons") or [],
            "in_lineup": jugador.get("in_lineup"),
        }

        # EL VETO VA ANTES QUE LA PUNTUACION.
        #
        # Si no, un Dios roto hasta enero acumularia puntos por
        # otras vias hasta pasar de 60 y saldria propuesto. El
        # veto no se remonta: se comprueba primero y se dice, para
        # que se vea que Pepe lo ha mirado y ha decidido que no.
        motivo = untouchable_reason(jugador)

        if motivo:
            ficha["untouchable_reason"] = motivo
            intocables.append(ficha)
            continue

        if puntuacion < propose_score:
            vigilados.append(ficha)
            continue

        veredicto = validate_sale_set(
            guardrail,
            acumuladas + [jugador.get("id")],
        )

        if not veredicto.get("ok"):
            ficha["blocked_reason"] = veredicto.get("reason")
            bloqueados.append(ficha)
            continue

        acumuladas.append(jugador.get("id"))

        # Publicar, no vender. Publicar es lo que genera ofertas,
        # y aceptar una oferta ya tiene su propio motor con sus
        # propios frenos.
        ficha["action"] = "PUBLICAR_EN_MERCADO"

        propuestas.append(ficha)

    return {
        "available": True,
        "reason": None,
        "mode": "OBSERVACION",
        "propose_score": propose_score,
        "watch_score": watch_score,
        "proposals": propuestas,
        "watch": vigilados,
        "blocked": bloqueados,

        # Los que Pepe ha mirado y ha decidido no tocar. Viajan
        # con su motivo: un veto silencioso es indistinguible de
        # un olvido.
        "untouchable": intocables,

        "recovers": sum(
            int(p.get("price") or 0) for p in propuestas
        ),
    }


def describe_sale_intent(intent: dict) -> list[str]:
    """
    El informe en texto, para el ciclo.
    """

    if not intent.get("available"):
        return [
            f"  No disponible: {intent.get('reason')}",
        ]

    lineas = []

    propuestas = intent.get("proposals") or []

    if not propuestas:
        lineas.append(
            "  Nadie que soltar: ningun jugador llega a "
            f"{intent.get('propose_score')} puntos de venta."
        )

    for ficha in propuestas:

        lineas.append(
            f"  {str(ficha.get('name'))[:20]:<20} "
            f"{str(ficha.get('hierarchy') or '-'):<12} "
            f"{int(ficha.get('price') or 0):>10,} EUR   "
            f"venta {ficha.get('sale_score')}/100   "
            f"{ficha.get('action')}".replace(",", ".")
        )

        for motivo in (ficha.get("reasons") or [])[:3]:
            lineas.append(f"      {motivo}")

    for ficha in (intent.get("blocked") or []):
        lineas.append(
            f"  {str(ficha.get('name'))[:20]:<20} "
            f"BLOQUEADO: {ficha.get('blocked_reason')}"
        )

    for ficha in (intent.get("untouchable") or []):
        lineas.append(
            f"  {str(ficha.get('name'))[:20]:<20} "
            f"INTOCABLE: {ficha.get('untouchable_reason')}"
        )

    vigilados = intent.get("watch") or []

    if vigilados:
        lineas.append(
            "  Vigilados (no se proponen): "
            + ", ".join(
                f"{f.get('name')} {f.get('sale_score')}"
                for f in vigilados[:6]
            )
        )

    if propuestas:
        lineas.append("")
        lineas.append(
            "  OBSERVACION: no se publica ni se vende nada. "
            "Es lo que Pepe haria."
        )

    return lineas
