"""
Cuanto vale un jugador PARA NOSOTROS, en euros.

POR QUE HACE FALTA
    `rival_bid_model.optimal_bid` necesita un numero: lo que el
    jugador vale para nosotros. Sin el no hay valor esperado que
    calcular y no se puede pujar.

    Hasta ahora ese numero era el precio que habria puesto una
    escalera de primas fija sobre el precio de mercado. Eso no es
    un valor: es una regla de redondeo. Con el, Pepe descartaba
    fichajes por una razon que no tenia nada que ver con si le
    salian rentables.

    Aqui se calcula de verdad, y de dos formas distintas segun
    para que queramos al jugador.

PARA EL ONCE: LO QUE CUESTAN LOS PUNTOS
    El mercado pone precio a un punto. En el catalogo del
    16/08/2026, con 393 jugadores con historico, la mediana son
    22.240 EUR por punto de la temporada pasada, con el cuartil
    bajo en 9.692.

    Asi que si un fichaje suma 136 puntos sobre el que sustituye,
    esos puntos valen unos 3 millones a precio de mercado. Pagar
    1,3 M por ellos es comprarlos a un tercio de su precio.

    No es una regla escrita a mano: es una medicion del catalogo,
    y se recalcula sola cada ciclo.

PARA ESPECULAR: LO QUE SE PUEDE REVENDER
    Precio de reventa esperado menos el margen que exigimos. Si no
    queda margen, no se compra. El resto -cuanto pujar, con que
    probabilidad- lo decide el modelo de rivales.

LOS JUGADORES SIN HISTORICO
    El 30 % del catalogo -172 de 568- no jugo en LaLiga la
    temporada pasada. No tienen puntos que mirar.

    Para esos se usa lo que el mercado cree: precio dividido entre
    el precio del punto. Y se marca la confianza como baja, lo que
    se traduce en exigir mas margen, no en inventar puntos.

    Sobre lo de "si son titulares en Madrid, Barsa o Atleti van a
    hacer puntos": es cierto, y ademas se puede derivar de los
    datos en vez de escribirlo. Sumando el valor de mercado de
    cada plantilla sale Real Madrid 2,62, Barcelona 2,34, Atletico
    1,58 sobre la media de la liga.

    Pero ese indice NO multiplica los puntos estimados, porque el
    precio del jugador ya refleja en gran parte en que club juega:
    contarlo dos veces inflaria a los caros de los equipos
    grandes, que es justo lo contrario de buscar chollos. Se usa
    como senal de confianza, que es donde aporta sin duplicar.
"""

from __future__ import annotations


# Confianza segun de donde salen los puntos estimados.
CONFIDENCE_HISTORICAL = 1.00
CONFIDENCE_MARKET_IMPLIED = 0.55

# Margen que exigimos sobre el valor justo.
#
# OJO: esto NO es "el descuento con el que compramos". Ese
# descuento ya aparece solo.
#
# `rival_bid_model.optimal_bid` maximiza
#
#     P(ganar) x (valor - puja)
#
# y ese producto nunca elige pujar el valor entero, porque
# entonces el margen seria cero y el valor esperado tambien. El
# descuento con el que compramos es una consecuencia de la
# optimizacion, no un parametro.
#
# Al principio puse aqui un 30 % y el resultado fue que se
# rechazaba todo. Tenaglia salia a 19.126 EUR por punto, por
# debajo de la mediana de mercado de 22.240 -o sea, barato- y aun
# asi se descartaba. Estaba exigiendo el margen dos veces.
#
# Lo que queda aqui es solo el colchon por incertidumbre: los
# puntos del ano pasado no garantizan los de este. Para especular
# es mayor porque el riesgo es otro y si es real: que la reventa
# no llegue a producirse.
DEFAULT_XI_MARGIN = 0.10
DEFAULT_SPECULATION_MARGIN = 0.25

# Las tendencias de precio se agotan. Proyectar la subida diaria
# en linea recta a cinco dias da numeros de fantasia, asi que cada
# dia siguiente cuenta menos.
# ============================================================
# DESGASTE DE LA TENDENCIA
# ============================================================
#
# Antes era 0,65 escrito a mano. Medido el 16/08/2026 sobre 80
# snapshots reales -572 jugadores, 2.657 cambios diarios-:
#
#   Que predice mejor el dia siguiente
#     como euros planos       coef 0,710   R2 0,538
#     como tasa (% del precio) coef 0,851   R2 0,569  <-- gana
#     normalizado a precio^0,325 coef 0,739  R2 0,546
#
#   Que predice mejor los TRES dias siguientes
#     ultimo incremento diario  coef 0,570   R2 0,659
#     velocidad de 3 dias       coef 0,601   R2 0,674  <-- gana
#
# El movimiento diario persiste de verdad: va en el mismo sentido
# el 88 % de las veces. Proyectar esta justificado.
#
# La media diaria de los tres dias siguientes es 0,601 veces la
# de hoy. Para que la suma con desgaste de esos tres dias valga
# 3 x 0,601 = 1,803 hace falta:
#
#   1 + d + d^2 = 1,803   ->   d = 0,53
#
# Es decir: el 0,65 de antes proyectaba un 15 % MAS de lo que el
# mercado hace en realidad.
TREND_DECAY = 0.53

# Cuanto de la varianza del futuro explica esta proyeccion.
# Se guarda para poder decirlo, no para calcular con ello.
TREND_R2 = 0.67

# Techo plausible de subida diaria, medido sobre los mismos 403
# jugadores con historial: el p90 esta en +4,53 %/dia.
#
# Por encima existe -Yusi Enriquez venia subiendo un 12 % diario
# tras firmar- pero proyectar tres dias mas a ese ritmo es
# extrapolar la cola. Se recorta y se deja constancia.
#
# EL RECORTE ES SOLO AL ALZA, a proposito. Recortar tambien las
# caidas nos haria optimistas justo con el jugador que se esta
# desplomando, que es el error caro. Una bajada se proyecta
# entera y sin desgaste.
MAX_PROJECTED_DAILY_RATE = 4.53

MIN_POINTS_SAMPLES = 40


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _catalog_players(catalog: dict) -> list:
    data = (catalog or {}).get("data") or catalog or {}
    players = data.get("players") or {}

    if isinstance(players, dict):
        players = list(players.values())

    return [p for p in players if isinstance(p, dict)]


# ============================================================
# CUANTO CUESTA UN PUNTO
# ============================================================


def calibrate_points_market(catalog: dict) -> dict:
    """
    Precio de mercado de un punto, medido en el catalogo.
    """

    ratios = sorted(
        p["price"] / p["pointsLastSeason"]
        for p in _catalog_players(catalog)
        if safe_int(p.get("price")) > 0
        and safe_int(p.get("pointsLastSeason")) > 0
    )

    if len(ratios) < MIN_POINTS_SAMPLES:
        return {
            "calibrated": False,
            "samples": len(ratios),
            "rate_median": 0,
            "rate_p25": 0,
            "rate_p75": 0,
            "reason": (
                f"Solo {len(ratios)} jugadores con historico y "
                f"precio; hacen falta {MIN_POINTS_SAMPLES}. Sin "
                f"esto no se puede valorar una mejora del once."
            ),
        }

    def q(p):
        return int(ratios[min(int(p * len(ratios)), len(ratios) - 1)])

    return {
        "calibrated": True,
        "samples": len(ratios),
        "rate_median": q(0.50),
        "rate_p25": q(0.25),
        "rate_p75": q(0.75),
        "reason": (
            f"{len(ratios)} jugadores con historico. Un punto "
            f"cuesta {q(0.50):,} EUR de mediana."
        ).replace(",", "."),
    }


def build_team_strength(catalog: dict) -> dict:
    """
    Fuerza de cada equipo, derivada del valor de su plantilla.

    Indice 1,0 = equipo medio de la liga.
    """

    por_equipo = {}

    for player in _catalog_players(catalog):

        equipo = player.get("teamID")

        if equipo is None:
            continue

        por_equipo[int(equipo)] = (
            por_equipo.get(int(equipo), 0)
            + safe_int(player.get("price"))
        )

    if not por_equipo:
        return {"available": False, "index": {}, "teams": 0}

    media = sum(por_equipo.values()) / len(por_equipo)

    return {
        "available": True,
        "teams": len(por_equipo),
        "index": {
            equipo: round(valor / media, 3)
            for equipo, valor in por_equipo.items()
        },
    }


# ============================================================
# PUNTOS ESPERADOS
# ============================================================


def estimate_season_points(
    player: dict,
    points_market: dict,
    team_strength: dict | None = None,
) -> dict:
    """
    Cuantos puntos cabe esperar de este jugador.

    Con historico, los del ano pasado. Sin el, los que implica su
    precio, con la confianza rebajada.
    """

    historico = safe_int(player.get("pointsLastSeason"))

    fuerza = None

    if team_strength and team_strength.get("available"):
        fuerza = (team_strength.get("index") or {}).get(
            safe_int(player.get("teamID"))
        )

    if historico > 0:
        return {
            "points": historico,
            "source": "HISTORICO",
            "confidence": CONFIDENCE_HISTORICAL,
            "team_strength": fuerza,
            "reason": (
                f"{historico} puntos la temporada pasada en LaLiga."
            ),
        }

    tarifa = safe_int(points_market.get("rate_median"))
    precio = safe_int(player.get("price"))

    if tarifa <= 0 or precio <= 0:
        return {
            "points": 0,
            "source": "DESCONOCIDO",
            "confidence": 0.0,
            "team_strength": fuerza,
            "reason": (
                "Sin historico y sin precio del punto: no hay por "
                "donde estimar."
            ),
        }

    implicados = int(precio / tarifa)

    return {
        "points": implicados,
        "source": "IMPLICITO_MERCADO",
        "confidence": CONFIDENCE_MARKET_IMPLIED,
        "team_strength": fuerza,
        "reason": (
            f"Sin historico en LaLiga. Su precio implica unos "
            f"{implicados} puntos"
            + (
                f"; su equipo esta en el indice {fuerza:.2f} de la "
                f"liga."
                if fuerza is not None
                else "."
            )
        ),
    }


# ============================================================
# VALOR PARA EL ONCE
# ============================================================


def xi_upgrade_value(
    candidate_points: int,
    replaced_points: int,
    points_market: dict,
    confidence: float = CONFIDENCE_HISTORICAL,
    recovered_value: int = 0,
    margin: float = DEFAULT_XI_MARGIN,
) -> dict:
    """
    Lo maximo que pagariamos por un fichaje que mejora el once.

    `recovered_value` es lo que recuperamos vendiendo al que
    sustituye. Por defecto cero: lo prudente es suponer que se
    queda de suplente y no entra caja.
    """

    tarifa = safe_int(points_market.get("rate_median"))

    if tarifa <= 0:
        return _sin_valor(
            "SIN_TARIFA",
            "No se ha podido medir cuanto cuesta un punto.",
        )

    delta = safe_int(candidate_points) - safe_int(replaced_points)

    if delta <= 0:
        return _sin_valor(
            "NO_MEJORA",
            (
                f"Suma {safe_int(candidate_points)} puntos y el que "
                f"sustituiria tiene {safe_int(replaced_points)}. "
                f"No es una mejora."
            ),
        )

    justo = int(delta * tarifa)

    maximo = int(
        justo * (1.0 - margin) * max(min(confidence, 1.0), 0.0)
    ) + safe_int(recovered_value)

    return {
        "value": maximo,
        "fair_value": justo,
        "points_delta": delta,
        "rate_per_point": tarifa,
        "confidence": confidence,
        "recovered_value": safe_int(recovered_value),
        "intent": "XI_UPGRADE",
        "reason": (
            f"Suma {delta} puntos. A precio de mercado "
            f"({tarifa:,} EUR/punto) valen {justo:,} EUR; con un "
            f"{margin*100:.0f} % de margen exigido y confianza "
            f"{confidence:.2f}, pagariamos hasta {maximo:,} EUR."
        ).replace(",", "."),
    }


# ============================================================
# VALOR PARA ESPECULAR
# ============================================================


def estimate_resale_price(
    price: int,
    daily_increment: int,
    horizon_days: int = 3,
    velocity_percent_per_day: float | None = None,
) -> dict:
    """
    A cuanto creemos que se puede revender.

    Se proyecta en TASA, no en euros, y se compone dia a dia con
    el desgaste medido. En la practica el resultado casi coincide
    con proyectar euros -porque precio x tasa = incremento-, y esa
    fue una correccion que llegue a proponer creyendo que habia
    un fallo donde no lo habia. La diferencia real aparece solo
    con jugadores baratos que se mueven rapido, donde componer si
    cambia el numero.

    `velocity_percent_per_day` es la velocidad medida por el motor
    de tendencias sobre varios dias. Cuando esta disponible se usa
    en lugar del incremento de ayer: un solo dia es ruidoso y
    medir sobre tres predice mejor (R2 0,674 frente a 0,659).

    La proyeccion explica unos dos tercios de lo que hace el
    precio despues. No es una certeza y el margen exigido en
    `speculation_value` esta ahi para cubrir el tercio restante.
    """

    base = safe_int(price)
    dias = max(int(horizon_days), 0)

    if base <= 0:
        return {
            "resale": 0,
            "appreciation": 0,
            "reason": "Sin precio.",
        }

    paso = safe_int(daily_increment)

    if velocity_percent_per_day is not None:
        porcentaje = float(velocity_percent_per_day)
        fuente = "velocidad medida"
    else:
        porcentaje = (paso / base) * 100 if base else 0.0
        fuente = "incremento de ayer"

    recortado = False

    if porcentaje > MAX_PROJECTED_DAILY_RATE:
        porcentaje = MAX_PROJECTED_DAILY_RATE
        recortado = True

    tasa = porcentaje / 100.0

    if dias == 0 or tasa == 0:
        return {
            "resale": base,
            "appreciation": 0,
            "horizon_days": dias,
            "source": fuente,
            "clamped": recortado,
            "reason": "Sin tendencia que proyectar.",
        }

    # Una tendencia bajista se respeta entera: si esta cayendo,
    # no se le aplica desgaste a la caida.
    if tasa < 0:
        factor = 1 + tasa * dias
    else:
        factor = 1.0
        peso = 1.0
        for _ in range(dias):
            factor *= (1 + tasa * peso)
            peso *= TREND_DECAY

    reventa = max(int(base * factor), 0)
    subida = reventa - base

    return {
        "resale": reventa,
        "appreciation": subida,
        "horizon_days": dias,
        "daily_rate_percent": round(tasa * 100, 3),
        "source": fuente,
        "clamped": recortado,
        "reason": (
            f"{fuente}: {tasa * 100:+.2f} %/dia"
            + (
                " (recortado a la banda plausible)"
                if recortado
                else ""
            )
            + f". A {dias} dias con desgaste medido "
            f"({TREND_DECAY}), {subida:,} EUR."
        ).replace(",", "."),
    }


def speculation_value(
    price: int,
    daily_increment: int,
    horizon_days: int = 3,
    margin: float = DEFAULT_SPECULATION_MARGIN,
    confidence: float = CONFIDENCE_HISTORICAL,
    velocity_percent_per_day: float | None = None,
) -> dict:
    """
    Lo maximo que pagariamos por un jugador que solo queremos para
    revender.
    """

    base = safe_int(price)

    # Un precio no positivo no es un jugador barato: es un dato
    # roto. Sin este corte, un precio de -100 producia un valor
    # negativo que se propagaba como si fuese un presupuesto.
    if base <= 0:
        return _sin_valor(
            "PRECIO_INVALIDO",
            "El jugador no tiene un precio de mercado valido.",
        )

    reventa = estimate_resale_price(
        base,
        daily_increment,
        horizon_days,
        velocity_percent_per_day=velocity_percent_per_day,
    )

    objetivo = reventa["resale"]

    if objetivo <= base:
        return _sin_valor(
            "SIN_REVALORIZACION",
            (
                f"No se espera que suba: reventa estimada "
                f"{objetivo:,} EUR sobre un precio de {base:,}."
            ).replace(",", "."),
        )

    ganancia = objetivo - base

    exigido = ganancia * margin

    maximo = int(
        (objetivo - exigido) * max(min(confidence, 1.0), 0.0)
    )

    if maximo <= base:
        return _sin_valor(
            "MARGEN_INSUFICIENTE",
            (
                f"La revalorizacion esperada ({ganancia:,} EUR) no "
                f"deja margen suficiente sobre el precio."
            ).replace(",", "."),
        )

    return {
        "value": maximo,
        "resale_estimate": objetivo,
        "expected_gain": ganancia,
        "horizon_days": int(horizon_days),
        "confidence": confidence,
        "intent": "SPECULATION",
        "reason": (
            f"Reventa estimada {objetivo:,} EUR en "
            f"{horizon_days} dias. Exigiendo un {margin*100:.0f} % "
            f"de la ganancia como margen, pagariamos hasta "
            f"{maximo:,} EUR."
        ).replace(",", "."),
    }


def _sin_valor(decision: str, reason: str) -> dict:
    return {
        "value": 0,
        "decision": decision,
        "reason": reason,
    }
