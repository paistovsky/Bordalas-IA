"""
Cuanto pujar cuando hay rivales delante.

EL PROBLEMA
    Hasta ahora la puja salia de una escalera fija de primas sobre
    el precio de mercado: +8 % si el jugador nos gusta mucho, +6 %,
    +4 %, +2 %. El mismo numero tanto si el rival mas rico de la
    liga tiene veinte millones como si nadie puede pagar ni el
    precio base.

    Eso pierde por los dos lados. Cuando no hay competencia,
    pagamos una prima que nadie nos estaba disputando. Cuando la
    hay de verdad, nos quedamos cortos y perdemos al jugador
    despues de haber inmovilizado el dinero todo el dia.

COMO FUNCIONA LA SUBASTA
    Es a ciegas y de un solo intento. En el reset del Computer se
    resuelven todas las pujas y se lleva al jugador quien mas haya
    puesto. No hay segunda oportunidad ni se ve lo que ofrecen los
    demas.

    Asi que la puja no es una negociacion: es una apuesta unica
    contra lo que creemos que van a hacer los rivales.

QUE HACE ESTE MODULO
    1. Estima la amenaza real por ESE jugador: no el dinero total
       del rival mas rico, sino lo maximo que es plausible que
       alguien pague por el.
    2. Si nadie puede competir, puja lo minimo que gana.
    3. Si hay competencia, la supera con un margen que depende de
       para que queremos al jugador.

LOS DOS MARGENES
    No es lo mismo un jugador para el once que uno para revender.

    Para el ONCE el activo es el objetivo. Perderlo por mil euros
    seria absurdo, asi que se paga un margen holgado, con el unico
    techo de lo que el jugador vale para nosotros.

    Para ESPECULAR el margen ES el negocio. Pagar de mas se come
    la ganancia entera, asi que se aprieta y, si no sale, se deja
    pasar. Siempre habra otro mercado manana.

LA CAUTELA DEL "+1 EURO"
    Pujar el minimo solo tiene sentido si de verdad sabemos que
    nadie puede competir, y eso lo sabemos por el ledger de
    rivales reconstruido del tablon.

    Ese ledger ya ha estado mal: el 15/08/2026 daba puja maxima
    cero a tres managers mientras el mismo informe registraba
    pujas suyas de entre diez y veintidos millones. Era un doble
    conteo, esta arreglado y tiene test, pero la leccion queda.

    Por eso la agresividad del minimo esta atada a si el ledger
    cuadra al euro. Si no cuadra, no se puja al filo: se deja un
    margen de seguridad. La confianza en el dato decide cuanto se
    arriesga.
"""

from __future__ import annotations


# Para que queremos al jugador.
INTENT_XI_UPGRADE = "XI_UPGRADE"
INTENT_SPECULATION = "SPECULATION"

# Lo maximo que es plausible que un rival pague por encima del
# precio de mercado en una subasta a ciegas. Un rival con veinte
# millones no paga cinco por un jugador de trescientos mil.
RIVAL_MAX_OVERPAY = 1.25

# Cuanto superamos la amenaza estimada, segun para que lo
# queremos.
MARGIN_XI_UPGRADE = 0.06
MARGIN_SPECULATION = 0.015

# Suelo absoluto del margen, para que en importes pequenos no
# quede en calderilla.
MIN_MARGIN_XI_UPGRADE = 10_000
MIN_MARGIN_SPECULATION = 1_000

# Cuando creemos que nadie puede competir.
MINIMUM_WINNING_INCREMENT = 1

# Lo mismo, pero cuando el ledger de rivales no cuadra y por tanto
# "nadie puede competir" es una suposicion, no un dato.
UNTRUSTED_LEDGER_MARGIN = 0.02
MIN_UNTRUSTED_MARGIN = 5_000


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def ledger_is_trusted(
    rival_intelligence: dict | None,
) -> bool:
    """
    ¿Podemos fiarnos de las estimaciones de dinero de los rivales?

    Solo si el ledger reconstruido cuadra al euro con el saldo
    oficial. Si no cuadra, las pujas maximas que calcula son
    aritmetica sobre datos rotos.
    """

    validacion = (
        (rival_intelligence or {}).get("validation")
        or {}
    )

    return validacion.get("exact") is True


def build_rival_threat(
    rival_intelligence: dict | None,
    market_price: int,
    own_user_id: int | None = None,
) -> dict:
    """
    Lo maximo que es plausible que pague un rival por este
    jugador.

    No es el dinero del rival mas rico. Es el minimo entre lo que
    puede pagar y lo que tiene sentido pagar por un jugador de
    este precio.
    """

    precio = safe_int(market_price)

    managers = (
        (rival_intelligence or {}).get("managers")
        or []
    )

    techo_plausible = int(precio * RIVAL_MAX_OVERPAY)

    competidores = []

    for manager in managers:

        if not isinstance(manager, dict):
            continue

        identificador = safe_int(
            manager.get("user_id")
            or manager.get("id")
        )

        if (
            own_user_id is not None
            and identificador == safe_int(own_user_id)
        ):
            continue

        capacidad = safe_int(manager.get("maximum_bid"))

        if capacidad < precio:
            # No llega ni al precio base: no puede competir.
            continue

        competidores.append(
            {
                "user_id": identificador,
                "name": manager.get("name"),
                "maximum_bid": capacidad,
                "plausible_bid": min(
                    capacidad,
                    techo_plausible,
                ),
            }
        )

    competidores.sort(
        key=lambda item: -item["plausible_bid"]
    )

    amenaza = (
        competidores[0]["plausible_bid"]
        if competidores
        else 0
    )

    return {
        "market_price": precio,
        "threat_amount": amenaza,
        "competitor_count": len(competidores),
        "top_competitor": (
            competidores[0]
            if competidores
            else None
        ),
        "competitors": competidores[:5],
        "ledger_trusted": ledger_is_trusted(
            rival_intelligence
        ),
        "uncontested": not competidores,
    }


def _margin_for(
    intent: str,
    base_amount: int,
) -> int:

    if intent == INTENT_XI_UPGRADE:
        return max(
            int(base_amount * MARGIN_XI_UPGRADE),
            MIN_MARGIN_XI_UPGRADE,
        )

    return max(
        int(base_amount * MARGIN_SPECULATION),
        MIN_MARGIN_SPECULATION,
    )


def calculate_pvp_bid(
    market_price: int,
    threat: dict,
    intent: str = INTENT_SPECULATION,
    available_budget: int | None = None,
    rational_max: int | None = None,
    is_starter: bool | None = None,
) -> dict:
    """
    Cuanto pujar por un jugador concreto.

    market_price      precio al que esta publicado
    threat            salida de build_rival_threat
    intent            XI_UPGRADE o SPECULATION
    available_budget  lo que queda tras descontar pujas vivas
    rational_max      lo maximo que el jugador vale para nosotros
    is_starter        si es titular en su equipo real

    Devuelve siempre un dict con `bid` y `decision`. Nunca lanza.
    """

    try:
        precio = safe_int(market_price)

        if precio <= 0:
            return _no_bid(
                "PRECIO_INVALIDO",
                "El jugador no tiene un precio de mercado valido.",
            )

        amenaza = safe_int(threat.get("threat_amount"))
        confiable = bool(threat.get("ledger_trusted"))
        sin_competencia = bool(threat.get("uncontested"))

        razones = []

        # Un no titular no deja de valer, pero no mejora el once.
        #
        # Esto va ANTES de calcular nada. En la primera version
        # estaba al final, despues del margen, asi que el
        # resultado decia "especulacion" mientras cobraba el
        # margen holgado del once. Una salida que se contradecia a
        # si misma es peor que un error a secas: parece auditada.
        if (
            is_starter is False
            and intent == INTENT_XI_UPGRADE
        ):
            intent = INTENT_SPECULATION

            razones.append(
                "No es titular en su equipo: no mejora el once. "
                "Se evalua como especulacion."
            )

        # ----------------------------------------------
        # SIN COMPETENCIA
        # ----------------------------------------------

        if sin_competencia:

            if confiable:
                puja = precio + MINIMUM_WINNING_INCREMENT
                razones.append(
                    "Ningun rival puede pagar el precio base y el "
                    "ledger cuadra al euro: basta el minimo."
                )

            else:
                margen = max(
                    int(precio * UNTRUSTED_LEDGER_MARGIN),
                    MIN_UNTRUSTED_MARGIN,
                )
                puja = precio + margen
                razones.append(
                    "Parece que nadie puede competir, pero el "
                    "ledger de rivales no cuadra: no se puja al "
                    "filo."
                )

        # ----------------------------------------------
        # CON COMPETENCIA
        # ----------------------------------------------

        else:
            base = max(amenaza, precio)
            margen = _margin_for(intent, base)
            puja = base + margen

            razones.append(
                f"Hay {threat.get('competitor_count', 0)} rival(es) "
                f"con dinero suficiente; el mas fuerte podria "
                f"llegar a {amenaza:,} EUR.".replace(",", ".")
            )

            if not confiable:
                razones.append(
                    "El ledger de rivales no cuadra: la amenaza "
                    "es una estimacion con margen de error."
                )

        # ----------------------------------------------
        # TECHOS
        # ----------------------------------------------

        if rational_max is not None:

            techo = safe_int(rational_max)

            if puja > techo:
                return _no_bid(
                    "SUPERA_VALOR_RACIONAL",
                    (
                        f"Ganar costaria {puja:,} EUR y el jugador "
                        f"no vale mas de {techo:,} EUR para "
                        f"nosotros."
                    ).replace(",", "."),
                    bid_needed=puja,
                    threat=threat,
                )

        if available_budget is not None:

            disponible = safe_int(available_budget)

            if puja > disponible:
                return _no_bid(
                    "SUPERA_PRESUPUESTO",
                    (
                        f"Ganar costaria {puja:,} EUR y solo "
                        f"quedan {disponible:,} EUR sin "
                        f"comprometer."
                    ).replace(",", "."),
                    bid_needed=puja,
                    threat=threat,
                )

        return {
            "bid": puja,
            "decision": "BID",
            "intent": intent,
            "market_price": precio,
            "threat_amount": amenaza,
            "premium_over_market": puja - precio,
            "premium_percent": round(
                (puja - precio) / precio * 100,
                2,
            ),
            "uncontested": sin_competencia,
            "ledger_trusted": confiable,
            "competitor_count": threat.get(
                "competitor_count", 0
            ),
            "reasons": razones,
        }

    except Exception as error:
        return _no_bid(
            "ERROR",
            f"{type(error).__name__}: {error}",
        )


def _no_bid(
    decision: str,
    reason: str,
    bid_needed: int = 0,
    threat: dict | None = None,
) -> dict:
    return {
        "bid": 0,
        "decision": decision,
        "reason": reason,
        "bid_needed": bid_needed,
        "threat_amount": safe_int(
            (threat or {}).get("threat_amount")
        ),
        "reasons": [reason],
    }
