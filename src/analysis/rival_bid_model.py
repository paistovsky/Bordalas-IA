"""
Cuanto va a pujar la competencia, y cuanto nos conviene pujar.

EL MODELO ANTERIOR ERA EL PEOR CASO CONTRA TODOS

    amenaza = min(capacidad del rival mas rico, precio * 1,25)
    compite quien pueda pagar el precio

    Con siete managers con millones en el banco, eso significaba
    que los 53 jugadores del mercado tenian seis competidores.
    Incluido Oluwaseyi, que costaba 420.000 EUR.

    Consecuencia: `uncontested` no se daba nunca, la ruta de
    mercado + 1 EUR no se activaba jamas, y el motor pedia pagar
    siempre un 25 % de prima. Como eso supera el techo, el
    resultado practico era no pujar por nadie.

    Y habia un caso que lo dejaba claro: Prinzipote puede pujar
    29,9 M y no ha pujado ni una sola vez en toda la liga. Su puja
    maxima observada es cero. Contarlo como amenaza en las 53
    subastas no tiene ningun sentido.

    Poder pagar no es ir a pujar.

QUE HACE ESTE MODULO

    Una subasta a ciegas no se gana adivinando el peor caso: se
    gana eligiendo cuanto arriesgar. Asi que en vez de un numero
    de amenaza, esto produce una probabilidad.

    1. Calibra, por rival, con que frecuencia puja de verdad
       -pujas hechas entre subastas observadas- y en que rango de
       importes se mueve.
    2. Calibra, para la liga, que prima sobre el precio de mercado
       se paga realmente. Antes era una constante inventada; ahora
       sale del historial de pujas.
    3. Calcula la probabilidad de ganar con cada importe posible.
    4. Elige el importe que maximiza el valor esperado:

           EV(puja) = P(ganar) * (lo que vale para nosotros - puja)

    Eso resuelve el "+1 EUR" de forma honesta. Si nadie suele
    pujar, la probabilidad de ganar al minimo es alta y el importe
    optimo es el minimo. Si hay tres rivales activos, subir la
    puja compra probabilidad, y el modelo la sube hasta donde
    compensa. Deja de ser una regla y pasa a ser una cuenta.

DE DONDE SALE "LO QUE VALE PARA NOSOTROS"
    De quien llame. Para especular, del precio de reventa menos el
    margen exigido. Para el once, de lo que valen los puntos que
    suma. Este modulo no lo inventa: si no se lo dan, no puja.
"""

from __future__ import annotations

from src.analysis.rival_ledger_audit import (
    audit_rival_ledger,
)


# Prima sobre el precio de mercado, cuando todavia no hay
# historial suficiente para calibrar.
#
# No es una medicion, es un punto de partida documentado: la
# mayoria de las pujas se hacen cerca del precio y las primas
# grandes son raras. En cuanto haya datos reales, se sustituye.
# El ultimo tramo es la cola: pujas raras y desproporcionadas.
# Existe y hay que dejarla en el modelo.
#
# Sin ella, cualquier importe por encima de 1,40x devolvia una
# probabilidad de ganar del 100 %, y "100 %" no es una prediccion:
# es el modelo diciendo que no ve mas alla de su propia curva. Con
# jugadores baratos eso es justo lo que pasa -por uno de 150.000
# EUR alguien puede poner el doble sin despeinarse-, y creerselo
# lleva a pagar de mas para comprar una certeza que no existe.
DEFAULT_PREMIUM_CURVE = (
    (1.00, 0.41),
    (1.02, 0.21),
    (1.05, 0.16),
    (1.10, 0.11),
    (1.20, 0.06),
    (1.40, 0.03),
    (2.00, 0.02),
)

# Por debajo de esto no hay muestra para calibrar nada.
MIN_PREMIUM_SAMPLES = 12
MIN_AUCTIONS_FOR_PARTICIPATION = 8

# Con pocos datos, a un rival con dinero se le supone esta
# probabilidad de pujar. Prudente: sin historial no se puede
# afirmar que alguien no puja.
PRIOR_PARTICIPATION = 0.30

# Cuando no se puede conciliar la plantilla de un rival -el
# informe viene resumido y no trae roster-, se supone esta
# cobertura. Ni fiarse del todo ni ignorar lo medido.
ASSUMED_COVERAGE_WHEN_UNKNOWN = 0.50

# Primas por debajo o muy por encima de esto son ruido: precios
# historicos desfasados, operaciones raras.
PREMIUM_FLOOR = 0.80
PREMIUM_CEILING = 2.50

# Suelo de probabilidad para que una puja merezca la pena.
#
# Con un margen estrecho el modelo encontraba pujas de valor
# esperado positivo pero ridiculo: 428.401 EUR inmovilizados para
# ganar 168 EUR esperados con un 11 % de probabilidad. Es dinero
# muerto hasta el reset, y ese dinero le hace falta a la siguiente
# operacion.
#
# El valor esperado por si solo no ve ese coste de oportunidad,
# porque no sabe que hay otras subastas compitiendo por la misma
# caja. Quien reparta el presupuesto entre varias pujas puede
# ordenar por `expected_value_per_euro`; este suelo es la
# proteccion para quien llame de una en una.
MIN_WIN_PROBABILITY = 0.15


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


# ============================================================
# CALIBRACION
# ============================================================


def _observed_bids(manager: dict) -> list:
    """
    Todas las pujas que le hemos visto: las perdidas quedan en el
    historial y las ganadas en las transacciones.
    """

    bids = []

    for item in (manager.get("lost_bid_history") or []):
        if not isinstance(item, dict):
            continue
        importe = safe_int(item.get("amount"))
        if importe > 0:
            bids.append(
                {
                    "amount": importe,
                    "player_id": safe_int(item.get("player_id")),
                }
            )

    ganada = safe_int(manager.get("max_winning_bid"))

    if ganada > 0:
        bids.append({"amount": ganada, "player_id": 0})

    return bids


def calibrate_premium_curve(
    managers: list,
    price_lookup=None,
) -> dict:
    """
    Que prima sobre el precio de mercado se paga en esta liga.

    Se aproxima dividiendo cada puja observada entre el precio
    actual del jugador. Es ruidoso -el precio de entonces no es el
    de ahora- pero es una medicion, y una medicion ruidosa vence a
    una constante inventada.

    Con menos de MIN_PREMIUM_SAMPLES muestras se devuelve la curva
    por defecto, y se dice.
    """

    muestras = []

    if price_lookup is not None:

        for manager in managers:

            if not isinstance(manager, dict):
                continue

            for bid in _observed_bids(manager):

                precio = safe_int(
                    price_lookup(bid["player_id"])
                )

                if precio <= 0:
                    continue

                prima = bid["amount"] / precio

                if PREMIUM_FLOOR <= prima <= PREMIUM_CEILING:
                    muestras.append(prima)

    if len(muestras) < MIN_PREMIUM_SAMPLES:
        return {
            "curve": list(DEFAULT_PREMIUM_CURVE),
            "calibrated": False,
            "samples": len(muestras),
            "reason": (
                f"Solo {len(muestras)} pujas medibles; hacen falta "
                f"{MIN_PREMIUM_SAMPLES}. Se usa la curva por "
                f"defecto."
            ),
        }

    muestras.sort()

    # Siete tramos por cuantiles: describe la forma real de las
    # pujas sin asumir ninguna distribucion. El ultimo corte esta
    # muy arriba a proposito, para que la cola quede dentro del
    # modelo y ninguna puja parezca ganar con certeza.
    cortes = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95, 0.995]

    curva = []

    for corte in cortes:
        indice = min(
            int(corte * len(muestras)),
            len(muestras) - 1,
        )
        curva.append(
            (round(muestras[indice], 4), round(1.0 / len(cortes), 4))
        )

    return {
        "curve": curva,
        "calibrated": True,
        "samples": len(muestras),
        "reason": (
            f"Calibrada con {len(muestras)} pujas observadas. "
            f"Prima mediana {muestras[len(muestras) // 2]:.2f}x."
        ),
    }


def build_bid_model(
    rival_intelligence: dict | None,
    price_lookup=None,
    own_user_id: int | None = None,
) -> dict:
    """
    Retrato de la competencia: quien puja, con que frecuencia y
    hasta donde.
    """

    inteligencia = rival_intelligence or {}

    managers = [
        m for m in (inteligencia.get("managers") or [])
        if isinstance(m, dict)
    ]

    subastas = safe_int(
        inteligencia.get("competitive_bids")
    )

    # Si no viene el total, se aproxima con las pujas vistas.
    if subastas <= 0:
        subastas = sum(
            safe_int(m.get("lost_bids"))
            + safe_int(m.get("won_auctions"))
            for m in managers
        )

    hay_historial = subastas >= MIN_AUCTIONS_FOR_PARTICIPATION

    # Conciliacion jugador a jugador.
    #
    # Antes la confianza en los datos salia de
    # `validation.exact`, que compara nuestro saldo oficial con el
    # reconstruido. Solo el nuestro: Biwenger no publica el saldo
    # de nadie mas. Sobre ese indicador se decidia si pujar al
    # minimo, o sea que se medía una cosa para decidir sobre otra.
    #
    # Lo que si se puede comprobar es si sabemos explicar cada
    # jugador de cada plantilla rival: o vino en el reparto
    # inicial, o hay una compra registrada. Eso si mide lo que nos
    # importa.
    auditoria = audit_rival_ledger(
        inteligencia,
        own_user_id=own_user_id,
    )

    por_manager = auditoria.get("by_manager") or {}

    rivales = []

    for manager in managers:

        identificador = safe_int(
            manager.get("user_id") or manager.get("id")
        )

        if (
            own_user_id is not None
            and identificador == safe_int(own_user_id)
        ):
            continue

        pujas = (
            safe_int(manager.get("lost_bids"))
            + safe_int(manager.get("won_auctions"))
        )

        observada = max(
            safe_int(manager.get("max_observed_bid")),
            safe_int(manager.get("max_lost_bid")),
            safe_int(manager.get("max_winning_bid")),
        )

        conciliacion = por_manager.get(identificador) or {}

        cobertura = conciliacion.get("coverage")

        if cobertura is None:
            cobertura = ASSUMED_COVERAGE_WHEN_UNKNOWN

        if hay_historial:

            medida = min(pujas / max(subastas, 1), 1.0)

            # Lo medido pesa tanto como completa sea nuestra
            # informacion de ese rival. De uno del que nos falta
            # media historia, "ha pujado dos veces" no significa
            # que solo haya pujado dos veces.
            participacion = (
                medida * cobertura
                + PRIOR_PARTICIPATION * (1.0 - cobertura)
            )

        else:
            participacion = (
                PRIOR_PARTICIPATION
                if safe_int(manager.get("maximum_bid")) > 0
                else 0.0
            )

        rivales.append(
            {
                "user_id": identificador,
                "name": manager.get("name"),
                "capacity": safe_int(manager.get("maximum_bid")),
                "bids_made": pujas,
                "max_observed_bid": observada,
                "participation": round(participacion, 4),
                "profile": manager.get("profile"),
                "coverage": round(cobertura, 4),

                # Afirmar que alguien NO puja es una afirmacion en
                # negativo, y solo se puede hacer si de verdad
                # conocemos su historia. Con cobertura baja, un
                # cero puede ser simplemente lo que no hemos
                # visto.
                "never_bids": bool(
                    hay_historial
                    and pujas == 0
                    and conciliacion.get(
                        "can_claim_never_bids",
                        False,
                    )
                ),
            }
        )

    prima = calibrate_premium_curve(managers, price_lookup)

    return {
        "available": bool(rivales),
        "rivals": rivales,
        "auctions_observed": subastas,
        "participation_from_history": hay_historial,
        "premium": prima,
        "ledger_audit": auditoria,
        "data_coverage": auditoria.get("min_coverage"),

        # Fiarse del ledger exige las dos cosas: que nuestro saldo
        # cuadre Y que sepamos explicar las plantillas rivales.
        # Antes bastaba con lo primero.
        "ledger_trusted": bool(
            (inteligencia.get("validation") or {}).get("exact")
            is True
            and auditoria.get("status") == "COMPLETO"
        ),
        "ledger_exact": (
            (inteligencia.get("validation") or {}).get("exact")
            is True
        ),
    }


# ============================================================
# PROBABILIDAD DE GANAR
# ============================================================


def credible_rivals(
    model: dict,
    price: int,
) -> list:
    """
    Quien puede disputarnos ESTE jugador.

    Se exige poder pagarlo y haber pujado alguna vez. Un rival con
    treinta millones que no ha pujado nunca no es una amenaza:
    es un espectador con dinero.
    """

    precio = safe_int(price)

    return [
        rival
        for rival in (model.get("rivals") or [])
        if rival["capacity"] >= precio
        and rival["participation"] > 0
        and not rival["never_bids"]
    ]


def win_probability(
    bid: int,
    price: int,
    model: dict,
    rivals: list | None = None,
) -> float:
    """
    Probabilidad de que nuestra puja sea la mas alta.

    Cada rival puja con su probabilidad de participacion, y si
    puja, su importe sale de la curva de primas. Ganamos si nadie
    supera nuestro importe.

    Los empates se cuentan como derrota: es el lado seguro, y en
    Biwenger no sabemos como se desempata.
    """

    importe = safe_int(bid)
    precio = safe_int(price)

    if precio <= 0:
        return 0.0

    if rivals is None:
        rivals = credible_rivals(model, precio)

    curva = (model.get("premium") or {}).get(
        "curve", list(DEFAULT_PREMIUM_CURVE)
    )

    probabilidad = 1.0

    for rival in rivals:

        # Probabilidad de que ESTE rival nos supere.
        supera = 0.0

        for factor, peso in curva:

            puja_rival = min(
                int(precio * factor),
                rival["capacity"],
            )

            if puja_rival >= importe:
                supera += peso

        probabilidad *= (
            1.0
            - rival["participation"] * supera
        )

    return max(0.0, min(1.0, probabilidad))


# ============================================================
# CUANTO PUJAR
# ============================================================


def candidate_bids(
    price: int,
    ceiling: int,
    model: dict,
) -> list:
    """
    Importes que merece la pena evaluar.

    No hace falta probar euro a euro: solo los que cambian la
    probabilidad, que son los que quedan justo por encima de cada
    escenario de puja rival.
    """

    precio = safe_int(price)
    techo = safe_int(ceiling)

    curva = (model.get("premium") or {}).get(
        "curve", list(DEFAULT_PREMIUM_CURVE)
    )

    importes = {precio + 1}

    for factor, _ in curva:
        importes.add(int(precio * factor) + 1)

    importes.add(techo)

    return sorted(
        importe
        for importe in importes
        if precio < importe <= techo
    )


def optimal_bid(
    price: int,
    value: int,
    model: dict,
    available_budget: int | None = None,
) -> dict:
    """
    El importe que maximiza el valor esperado.

        EV(puja) = P(ganar) * (valor - puja)

    `value` es lo que el jugador vale PARA NOSOTROS: reventa menos
    margen si es especulacion, valor en puntos si es para el once.
    Sin ese numero no se puja, porque no habria forma de saber si
    ganar la subasta es bueno.

    Nunca lanza.
    """

    try:
        precio = safe_int(price)
        valor = safe_int(value)

        if precio <= 0:
            return _no_bid(
                "PRECIO_INVALIDO",
                "El jugador no tiene precio de mercado valido.",
            )

        if valor <= precio:
            return _no_bid(
                "NO_COMPENSA",
                (
                    f"Vale {valor:,} EUR para nosotros y ya cuesta "
                    f"{precio:,}. No hay margen."
                ).replace(",", "."),
            )

        techo = valor

        if available_budget is not None:
            techo = min(techo, safe_int(available_budget))

        if techo <= precio:
            return _no_bid(
                "SUPERA_PRESUPUESTO",
                (
                    f"Cuesta {precio:,} EUR y solo quedan "
                    f"{safe_int(available_budget):,} sin "
                    f"comprometer."
                ).replace(",", "."),
            )

        rivales = credible_rivals(model, precio)

        opciones = []

        for importe in candidate_bids(precio, techo, model):

            p = win_probability(importe, precio, model, rivales)

            opciones.append(
                {
                    "bid": importe,
                    "win_probability": round(p, 4),
                    "expected_value": round(p * (valor - importe)),
                    "expected_value_per_euro": round(
                        p * (valor - importe) / max(importe, 1),
                        6,
                    ),
                    "premium_percent": round(
                        (importe - precio) / precio * 100, 2
                    ),
                }
            )

        if not opciones:
            return _no_bid(
                "SIN_MARGEN",
                "No hay ningun importe entre el precio y el valor.",
            )

        # Mas valor esperado; a igualdad, el importe menor.
        mejor = max(
            opciones,
            key=lambda o: (o["expected_value"], -o["bid"]),
        )

        if mejor["expected_value"] <= 0:
            return _no_bid(
                "EV_NEGATIVO",
                (
                    "Ninguna puja tiene valor esperado positivo: "
                    "ganar costaria mas de lo que vale."
                ),
                options=opciones,
            )

        if mejor["win_probability"] < MIN_WIN_PROBABILITY:
            return _no_bid(
                "PROBABILIDAD_INSUFICIENTE",
                (
                    f"La mejor puja ({mejor['bid']:,} EUR) solo "
                    f"gana el "
                    f"{mejor['win_probability'] * 100:.0f} % de "
                    f"las veces. Inmoviliza la caja hasta el reset "
                    f"a cambio de casi nada."
                ).replace(",", "."),
                options=opciones,
            )

        razones = []

        if not rivales:
            razones.append(
                "Ningun rival con dinero ha pujado nunca: el "
                "minimo basta."
            )

        else:
            activos = ", ".join(
                f"{r['name']} ({r['participation'] * 100:.0f}%)"
                for r in sorted(
                    rivales,
                    key=lambda r: -r["participation"],
                )[:3]
            )
            razones.append(
                f"{len(rivales)} rival(es) que pujan de verdad: "
                f"{activos}."
            )

        razones.append(
            f"A {mejor['bid']:,} EUR la probabilidad de ganar es "
            f"{mejor['win_probability'] * 100:.0f} % y el valor "
            f"esperado {mejor['expected_value']:,} EUR."
            .replace(",", ".")
        )

        if not (model.get("premium") or {}).get("calibrated"):
            razones.append(
                "Curva de primas sin calibrar todavia: "
                + str((model.get("premium") or {}).get("reason"))
            )

        return {
            "bid": mejor["bid"],
            "decision": "BID",
            "win_probability": mejor["win_probability"],
            "expected_value": mejor["expected_value"],
            "expected_value_per_euro": mejor[
                "expected_value_per_euro"
            ],
            "premium_percent": mejor["premium_percent"],
            "market_price": precio,
            "our_value": valor,
            "competitor_count": len(rivales),
            "competitors": [
                {
                    "name": r["name"],
                    "participation": r["participation"],
                    "capacity": r["capacity"],
                }
                for r in rivales
            ],
            "options": opciones,
            "premium_model": model.get("premium"),
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
    options: list | None = None,
) -> dict:
    return {
        "bid": 0,
        "decision": decision,
        "reason": reason,
        "win_probability": 0.0,
        "expected_value": 0,
        "options": options or [],
        "reasons": [reason],
    }
