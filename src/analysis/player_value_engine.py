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


# ============================================================
# TITULARIDAD
# ============================================================
#
# Los puntos de la temporada pasada dicen lo bueno que es un
# jugador. No dicen si va a jugar. Y en Biwenger un suplente que
# no sale del banquillo puntua cero por muy bueno que sea.
#
# Que paso por no mirar esto: el 16/08/2026 Bordalas propuso
# pujar 1.236.001 EUR por Andres Castrin -97 puntos el ano
# pasado, pronostico SUPLENTE- para sustituir a Yeray -24 puntos,
# pronostico TITULAR-. La cuenta decia "suma 73 puntos". El campo
# habria dicho otra cosa.
#
# Dos correcciones distintas, y hacen falta las dos:
#
#   1. Los puntos esperados se escalan por la probabilidad de
#      jugar. Un suplente aporta algo -entra, hay lesiones,
#      rota- pero no lo que aportaria de titular.
#
#   2. Y aun escalados, un pronostico de suplente NO puede
#      reclamar que mejora el once por delante de un titular
#      confirmado. Eso ya no es una cuestion de cuanto: es que la
#      operacion no hace lo que dice que hace.

# Lo que aporta un jugador con probabilidad cero de ser titular.
# No es cero: los suplentes entran. Es poco.
BENCH_POINTS_FACTOR = 0.15

# Mismos cortes que el consenso multifuente, para que "titular"
# signifique lo mismo en todo el programa.
STARTER_PROBABILITY_THRESHOLD = 67.0
BENCH_PROBABILITY_THRESHOLD = 40.0

# De un candidato sin senal de titularidad no se sabe si jugara.
# No se le escalan los puntos -inventar un numero seria peor-
# pero se le exige mas margen, que es lo que se hace siempre que
# se sabe menos.
CONFIDENCE_NO_STARTER_DATA = 0.75

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


# ============================================================
# JERARQUIA
#
# El eje estructural. El % dice quien juega ESTE sabado y cambia
# cada semana; la jerarquia dice QUE ES un jugador en su equipo y
# aguanta la temporada. Una compra dura meses, asi que la base
# tiene que ser la jerarquia.
#
# DE DONDE SALEN ESTOS NUMEROS
#
#     No estan inventados: son los minutos reales que publica FF,
#     medidos sobre 137 jugadores de 18 equipos el 17/08/2026,
#     normalizados contra el escalon Clave.
#
#         Clave        n=32   71,8 min de media   ->  1,000
#         Importante   n=33   69,7                ->  0,971
#         Rotacion     n=35   40,6                ->  0,566
#         Revulsivo    n=16   28,8                ->  0,401
#         Reserva      n=20   16,1                ->  0,225
#
#     ADVERTENCIA: la muestra es de una jornada. Sirve para no
#     inventarse la escala, no para darla por cerrada. A partir de
#     la jornada 6-8 hay que recalibrar con minutos acumulados.
#
#     Dios (60) no se pudo medir: solo hay dos en toda la liga y
#     FF no publicaba sus minutos. Se le da el mismo 1,00 que a
#     Clave en vez de inflarlo por intuicion.
#
#     Descarte (10) tenia n=1, que no es una muestra. Se fija por
#     debajo de Reserva y se dice que es criterio, no medida.
# ============================================================

HIERARCHY_POINTS_FACTOR = {
    60: 1.00,   # Dios       (no medido)
    50: 1.00,   # Clave
    40: 0.97,   # Importante
    30: 0.57,   # Rotacion
    25: 0.40,   # Revulsivo
    20: 0.22,   # Reserva
    10: 0.10,   # Descarte   (criterio, n=1)
}


# Probabilidad TIPICA de cada escalon, medida en la misma tanda.
#
# Hace falta para no contar dos veces lo mismo. Jerarquia y % van
# de la mano -un Clave ronda el 72 %, un Reserva el 14 %-, asi que
# multiplicar los dos factores penalizaria dos veces al mismo
# jugador. Lo que aporta el % no es su valor absoluto: es cuanto
# se SEPARA de lo normal en su escalon.
#
# Un Clave al 90 % esta por encima de lo suyo y sube. Un Clave al
# 0 % -lesionado- se desploma. Un Clave al 72 % no mueve nada,
# porque eso es exactamente lo que se espera de un Clave.
HIERARCHY_TYPICAL_PROBABILITY = {
    60: 75.0,
    50: 71.7,
    40: 66.0,
    30: 43.4,
    25: 30.5,
    20: 13.9,
    10: 3.3,
}


# Cuanto pesa la desviacion semanal sobre la base estructural.
#
# BAJADO DE 0,5 A 0,15 EL 17/08/2026
#
#     Con 0,5, un dato de un sabado movia un tercio de una
#     estimacion de nueve meses, y producia el absurdo de que una
#     DUDA penalizase mas que una BAJA CONFIRMADA: la duda caia
#     por la via del porcentaje -que pesaba mucho- y la baja por
#     la via de las jornadas perdidas -que pesa lo que debe-.
#
#     Ahora que existen la jerarquia y los partes de baja, el
#     porcentaje semanal es en gran parte redundante. Se queda
#     como correccion pequeña, que es lo que es.
WEEKLY_ADJUSTMENT_WEIGHT = 0.15

# Suelo y techo del ajuste.
#
# EL TECHO ES 1,0 POR DECISION DEL DUENO (17/08/2026)
#
#     `raw_points` son los puntos de la temporada pasada. Dejar
#     que el factor pasase de 1,0 significaba valorar a un jugador
#     por encima de lo que nunca ha hecho, solo porque esta semana
#     va mejor de lo normal en su escalon.
#
#     El cambio a base estructural ya sube las valoraciones entre
#     un 19 % y un 36 % -un Importante al 70 % pasa de 0,745 a
#     0,989-, y esa subida esta justificada: el modelo anterior
#     recortaba la temporada entera por un dato de una semana.
#     Pero el historico se queda como tope. Se paga mejor, no se
#     paga de mas.
MIN_EXPECTED_FACTOR = 0.05
MAX_EXPECTED_FACTOR = 1.00

# EL RIVAL SI PUEDE EMPUJAR POR ENCIMA DEL TECHO
#
# Con el tope en 1,0 a secas, el calendario solo podia hacer daño
# a los mejores: un Clave o un Dios ya estan pegados al techo, asi
# que el -10 % de un rival dificil bajaba y el +10 % de uno
# asequible no subia nada. Medido: Dios +0,0 % / -9,3 %, Rotacion
# +10,0 % / -10,0 %.
#
# El techo existe para no inventarse valor de la nada, no para
# ignorar que este sabado le toca el colista. Asi que el historico
# sigue siendo el tope de la base, y solo el rival puede pasar de
# ahi, y solo hasta un 10 %.
MAX_FACTOR_WITH_FIXTURE = 1.10


# La escalera, en orden. La distancia se mide en ESCALONES, no en
# el numero de FF, porque la escala no es lineal: de Revulsivo a
# Rotacion hay 5 puntos y de Rotacion a Importante hay 10.
HIERARCHY_LADDER = [10, 20, 25, 30, 40, 50, 60]

# Cuantos escalones puede bajar un fichaje respecto al que sale
# antes de que sea un destrozo del once. Dos: cambiar un Clave por
# un Rotacion ya no se permite; por un Importante, si.
HIERARCHY_VETO_STEPS = 2


# ============================================================
# CAMBIAR A UN TITULAR (19/08/2026)
# ============================================================
#
# Hasta hoy Pepe solo se planteaba sustituir al PEOR de cada
# posicion, porque era el unico que se le ofrecia. A un titular
# mediocre no lo descartaba: no se lo preguntaba nadie.
#
# Al abrirlo hay que apretar, porque cambiar a un titular no es
# lo mismo que cambiar a un suplente:
#
#   - se paga con una venta que puede tardar dias
#   - por medio se juegan jornadas
#   - y el que sale ya no vuelve
#
# El dueño lo dijo asi: "Clave se puede tocar, siempre y cuando
# sea para fichar otro clave con mas puntos y nos salga rentable
# el coste/punto".

DIOS_HIERARCHY = 60

# Margen exigido cuando el que sale es titular. El normal es del
# 10 %; aqui se pide mas del doble, porque un cambio que gana por
# poco no compensa el riesgo de quedarse a medias.
STARTER_SWAP_MARGIN = 0.25

# Y una mejora minima en puntos de temporada. Sin esto, un cambio
# de +1 punto pasaria el filtro del margen por pura aritmetica.
STARTER_SWAP_MIN_DELTA = 8

# Cuanto mas seguro titular tiene que ser el que entra. Cero
# significa "al menos igual": cambiar cuatro puntos por menos
# minutos es como se pierden las ligas.
STARTER_SWAP_MIN_PROBABILITY_GAIN = 0.0


# ============================================================
# AUSENCIAS
#
# Cuantas jornadas se pierde, no si juega el sabado.
#
# POR QUE HACE FALTA APARTE DEL %
#
#     Con solo el porcentaje, una gripe y un cruzado roto son el
#     mismo dato: 0 %. Al pasar a base estructural, un Clave
#     lesionado paso de valer el 15 % de sus puntos al 64 %,
#     porque la jerarquia dice "es un Clave" y nadie contaba las
#     jornadas perdidas.
#
# COMO ENTRA
#
#     Cuando se conoce el horizonte, la parte de temporada que se
#     pierde SUSTITUYE al ajuste semanal, no se multiplica con el.
#     Multiplicarlos seria contar dos veces la misma baja: el 0 %
#     de esta jornada ya esta dentro de "se pierde seis jornadas".
# ============================================================

# Jornadas de una temporada. Se usa para medir que fraccion de lo
# que queda se pierde un jugador.
SEASON_MATCHDAYS = 38

# Que hacer con una "Baja indefinida".
#
# NO ES UNA MEDIDA, ES UNA POLITICA. FF dice que no sabe cuanto
# durara; nosotros no podemos fingir que si. Diez jornadas es un
# punto medio prudente entre "vuelve pronto" y "temporada
# terminada", elegido a mano el 17/08/2026 y revisable.
INDEFINITE_ABSENCE_MATCHDAYS = 10

# Por debajo de esto no se baja aunque la baja sea eterna: un
# jugador con contrato sigue teniendo valor de reventa.
MIN_ABSENCE_FACTOR = 0.05


def absence_factor(
    starter: dict | None,
    current_matchday: int | None = None,
) -> tuple[float | None, str | None]:
    """
    Fraccion de lo que queda de temporada que SI va a jugar.

    Devuelve `None` cuando no hay parte de baja: entonces manda el
    ajuste semanal de siempre.
    """

    ausencia = (starter or {}).get("absence") or {}

    if not ausencia:
        return (None, None)

    fuera = ausencia.get("matchdays_out")

    if fuera is None:

        if ausencia.get("basis") == "INDEFINIDA":
            fuera = INDEFINITE_ABSENCE_MATCHDAYS

        else:
            return (None, None)

    fuera = max(0, int(fuera))

    if fuera == 0:
        return (None, None)

    # La jornada viaja dentro de la propia senal, asi que quien
    # llame no tiene que acordarse de pasarla.
    if current_matchday is None:
        current_matchday = (starter or {}).get("matchday")

    jugadas = max(0, int(current_matchday or 1) - 1)

    quedan = max(1, SEASON_MATCHDAYS - jugadas)

    factor = max(
        MIN_ABSENCE_FACTOR,
        (quedan - min(fuera, quedan)) / quedan,
    )

    detalle = ausencia.get("prognosis") or ausencia.get("detail")

    return (
        factor,
        (
            f"se pierde {fuera} de las {quedan} jornadas que "
            f"quedan"
            + (f" ({detalle})" if detalle else "")
        ),
    )


# ============================================================
# EL RIVAL DE LA PROXIMA JORNADA
#
# FF publica `data-rival_dif_index`, escala de 5 y simetrica.
# Comprobada contra los 18 equipos y consistente consigo misma:
# Getafe-Racing sale 1 en una pagina y 5 en la otra.
#
#     1 muy asequible · 2 asequible · 3 igualado
#     4 dificil       · 5 muy dificil
#
# PESA POCO A PROPOSITO
#
#     Un Clave contra el Levante no vale lo que contra el Barca,
#     pero esto es una estimacion de TEMPORADA y el proximo rival
#     es un partido de 38. Darle mas peso seria repetir el error
#     que ya cometimos con el porcentaje semanal: decidir meses
#     con el dato de un sabado.
#
#     Donde este dato manda de verdad es en la reventa a tres
#     dias, que es otro motor.
# ============================================================

FIXTURE_WEIGHT = 0.10

FIXTURE_LABELS = {
    1: "muy asequible",
    2: "asequible",
    3: "igualado",
    4: "dificil",
    5: "muy dificil",
}


# ============================================================
# JUGAR EN CASA (18/08/2026)
# ============================================================
#
# LA DIFICULTAD DE FF NO INCLUYE EL CAMPO. COMPROBADO.
#
#     Se miraron los emparejamientos de la jornada 2 y salen por
#     parejas identicas:
#
#         Deportivo vs ELC casa 3  |  Elche   vs DEP fuera 3
#         Osasuna   vs LEV casa 3  |  Levante vs OSA fuera 3
#         Athletic  vs SEV casa 3  |  Sevilla vs ATH fuera 3
#
#     El mismo partido, la misma dificultad para los dos lados. Y
#     el Madrid FUERA en Espanyol saca un 2 -facil- mientras el
#     Espanyol EN CASA saca un 4. La dificultad mide al rival, no
#     donde se juega.
#
#     `away` viene aparte en el dato de FF y no lo miraba nadie.
#
# EL PESO ES CRITERIO, NO MEDICION
#
#     Un 5 % arriba en casa y un 5 % abajo fuera. Puesto a ojo,
#     en el orden de magnitud de la ventaja de campo que se
#     observa en el futbol, y deliberadamente por debajo del peso
#     del rival: importa mas contra quien juegas que donde.
#
#     Medible de verdad cuando haya puntos acumulados por local y
#     visitante, igual que las dos tablas de la jerarquia.
# ============================================================

HOME_WEIGHT = 0.05


def venue_factor(starter: dict | None) -> tuple[float | None, str | None]:
    """
    Jugar en casa o fuera. None si no se sabe donde se juega.

    Ausencia de dato no es dato: sin `away` no se asume campo
    neutral con un 1.0 silencioso.
    """

    partido = (starter or {}).get("next_match") or {}

    if partido.get("away") is None:
        return (None, None)

    if bool(partido.get("away")):
        return (1.0 - HOME_WEIGHT, "fuera de casa")

    return (1.0 + HOME_WEIGHT, "en casa")


def fixture_factor(starter: dict | None) -> tuple[float | None, str | None]:
    """
    Como de bueno es el proximo partido: rival y campo.

    Es el factor de UNA jornada, a peso completo. Para decisiones
    que duran meses hay que diluirlo con `season_fixture_factor`.
    """

    indice = (
        (starter or {}).get("next_match") or {}
    ).get("difficulty")

    campo, motivo_campo = venue_factor(starter)

    try:
        indice = int(indice) if indice else None

    except (TypeError, ValueError):
        indice = None

    if indice not in FIXTURE_LABELS:

        # Sin rival pero con campo todavia hay algo que decir.
        if campo is not None:
            return (campo, motivo_campo)

        return (None, None)

    # 3 es igualado y no mueve nada. 1 sube, 5 baja.
    factor = 1.0 + FIXTURE_WEIGHT * (3 - indice) / 2.0

    rival = (
        (starter or {}).get("next_match") or {}
    ).get("rival")

    motivo = (
        f"rival {FIXTURE_LABELS[indice]}"
        + (f" ({rival})" if rival else "")
    )

    if campo is not None:
        factor *= campo
        motivo += f", {motivo_campo}"

    return (factor, motivo)


# ============================================================
# EL PARTIDO DECIDE CUANDO, NO SI
# ============================================================
#
# EL CASO (dueño, 18/08/2026)
#
#     "Tenemos a un tio que vale 50 y en el mercado hay uno de
#     52. Pero el de 52 juega fuera y contra el Barsa. Pierde
#     seguro. Hay que valorar si juegan en casa y contra un
#     equipo grande o no, ¿no crees?"
#
# POR QUE NO SE APLICA A PESO COMPLETO
#
#     Porque el cambio dura lo que queda de temporada y el
#     partido dura un sabado. A peso completo:
#
#         sin campo:  52 − 50           = +2   se hace
#         con campo:  52×0.90 − 50×1.10 = −8   se bloquea
#
#     Ocho puntos de temporada decididos por una jornada. Es el
#     mismo error que ya se cometio con WEEKLY_ADJUSTMENT_WEIGHT,
#     que estaba en 0,5 y hubo que bajarlo a 0,15 porque un dato
#     de un sabado movia un tercio de una estimacion de nueve
#     meses.
#
# LA SOLUCION: QUE EL PESO LO PONGA EL CALENDARIO
#
#     El proximo partido es UNO de los que quedan. En la jornada
#     2 quedan 37: pesa 1/37 y no mueve casi nada. En la 35
#     quedan 4 y pesa un cuarto. En la ultima pesa entero, que es
#     cuando el partido ES la decision.
#
#     La misma formula sirve todo el año y se ajusta sola.
# ============================================================


def remaining_matchdays(matchday) -> int:
    """
    Cuantas jornadas quedan contando la que viene. Minimo 1.
    """

    try:
        jugadas = int(matchday or 0)

    except (TypeError, ValueError):
        jugadas = 0

    return max(
        1,
        SEASON_MATCHDAYS - max(0, jugadas) + 1,
    )


def season_fixture_factor(
    starter: dict | None,
    matchday=None,
) -> tuple[float | None, str | None]:
    """
    El proximo partido, diluido en lo que queda de temporada.

    Sin jornada conocida devuelve None: antes no tocar la
    valoracion que diluirla por un numero inventado.
    """

    factor, motivo = fixture_factor(starter)

    if factor is None or not matchday:
        return (None, None)

    quedan = remaining_matchdays(matchday)

    return (
        1.0 + (factor - 1.0) / quedan,
        f"{motivo} (pesa 1 de {quedan} jornadas)",
    )


# ============================================================
# LO FIABLE QUE ES EL PRONOSTICO DE ESE EQUIPO
#
# FF mide cuanto acierta prediciendo cada alineacion. Un
# pronostico de un equipo "Previsible" vale mas que el mismo
# numero de uno "Imprevisible", y hasta hoy valian igual.
#
# SE USA LA DE LA JORNADA, NO LA DE LA TEMPORADA
#
#     La de temporada seria mejor -es estable- pero el 17/08/2026
#     solo 7 equipos de 18 tenian valor, y los otros 11 marcaban
#     0,0. Ese 0 no es "impredecible": es que aun no hay
#     historial. Usarlo como multiplicador habria castigado a once
#     equipos por un dato que no existe, que es exactamente el
#     error del `hierarchy = 0`.
#
#     La de la jornada esta siempre y discrimina: 40 Imprevisible,
#     60 Poco previsible, 80 Previsible.
#
# Esto NO toca los puntos. Toca la CONFIANZA, que es lo que
# decide cuanto se paga por ellos.
# ============================================================

MIN_PREDICTABILITY_CONFIDENCE = 0.85


def predictability_confidence(
    starter: dict | None,
) -> tuple[float | None, str | None]:

    contexto = (starter or {}).get("team_context") or {}

    valor = contexto.get("predictability")

    if not valor:
        return (None, None)

    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return (None, None)

    # 40 -> 0,85   60 -> 0,925   80 -> 1,00
    factor = MIN_PREDICTABILITY_CONFIDENCE + (
        (1.0 - MIN_PREDICTABILITY_CONFIDENCE)
        * max(0.0, min((valor - 40.0) / 40.0, 1.0))
    )

    etiqueta = contexto.get("predictability_label")

    return (
        round(factor, 4),
        f"alineacion {etiqueta or f'{valor:.0f} %'}",
    )


def hierarchy_rank(starter: dict | None) -> int | None:
    """
    Posicion en la escalera, o None si no hay jerarquia.

    El 0 de FF ("sin definir") no es el escalon de abajo: es
    ausencia de dato y devuelve None.
    """

    valor = (starter or {}).get("hierarchy_value")

    if not valor:
        return None

    try:
        valor = int(valor)
    except (TypeError, ValueError):
        return None

    if valor not in HIERARCHY_LADDER:
        return None

    return HIERARCHY_LADDER.index(valor)


def hierarchy_label(starter: dict | None) -> str | None:
    return (starter or {}).get("hierarchy_label")


def hierarchy_value(starter: dict | None) -> int | None:
    """
    El numero de FF tal cual, o None si no lo hay.

    Se separa de `hierarchy_rank` a proposito: el rango sirve
    para medir distancias entre escalones y este para preguntar
    por uno concreto -"¿es Dios?"-, que no es lo mismo.
    """

    valor = (starter or {}).get("hierarchy_value")

    return int(valor) if valor else None


def expected_points_factor(
    starter: dict | None,
    current_matchday: int | None = None,
) -> tuple[float, str]:
    """
    Que fraccion de sus puntos cabe esperar, y por que.

    Tres cosas, multiplicadas:

        base estructural  x  ajuste semanal  x  fraccion que juega

    LAS TRES, NO UNA U OTRA

        La primera version aplicaba la ausencia EN LUGAR del
        ajuste semanal, para no contar dos veces la misma lesion.
        Con el peso semanal en 0,5 tenia sentido, pero producia un
        orden absurdo: una duda salia peor que una baja confirmada
        de una jornada.

        Con el peso semanal en 0,15 la superposicion es pequeña y
        multiplicar da el orden correcto, que es el que pidio el
        dueño: una baja de una jornada nunca vale mas que una
        duda, y cuantas mas jornadas se pierda, menos vale.

            duda de esta jornada        0,888
            baja confirmada 1 jornada   0,864
            baja de 2 jornadas          0,840
            baja de 3 jornadas          0,816
    """

    probabilidad = (starter or {}).get("probability")
    rango = hierarchy_rank(starter)

    ausencia, motivo_ausencia = absence_factor(
        starter,
        current_matchday,
    )

    # Sin jerarquia: se cae al comportamiento anterior, solo con
    # el % de la semana. Peor, pero no ciego.
    if rango is None:
        return (
            starter_factor(probabilidad),
            "sin jerarquia: solo cuenta el pronostico de la jornada",
        )

    escalon = HIERARCHY_LADDER[rango]
    base = HIERARCHY_POINTS_FACTOR[escalon]

    factor = base

    motivos = [f"base {base:.2f} por jerarquia"]

    # 1. La jornada, como correccion pequeña.
    if probabilidad is not None:

        tipica = HIERARCHY_TYPICAL_PROBABILITY[escalon]

        desviacion = (float(probabilidad) - tipica) / 100.0

        factor *= 1.0 + WEEKLY_ADJUSTMENT_WEIGHT * desviacion

        motivos.append(
            f"{float(probabilidad):.0f} % frente al {tipica:.0f} % "
            f"tipico de su escalon"
        )

    # 2. Las jornadas que se pierde, que es lo que de verdad manda
    #    cuando la baja es larga.
    if ausencia is not None:

        factor *= ausencia

        motivos.append(motivo_ausencia)

    # EL TECHO DEL HISTORICO, ANTES DEL RIVAL
    #
    # Todo lo de arriba -lo que un jugador es y lo que va a estar
    # disponible- no puede pasar de sus puntos del año pasado. Esa
    # fue la decision del dueño.
    factor = min(factor, MAX_EXPECTED_FACTOR)

    # 3. Y ahora si, el rival, que es lo unico que puede asomar por
    #    encima de ese techo.
    rival, motivo_rival = fixture_factor(starter)

    if rival is not None:

        factor *= rival

        motivos.append(motivo_rival)

    factor = max(
        MIN_EXPECTED_FACTOR,
        min(factor, MAX_FACTOR_WITH_FIXTURE),
    )

    return (factor, "; ".join(motivos))


def starter_factor(probability) -> float:
    """
    Que fraccion de sus puntos cabe esperar de un jugador con esta
    probabilidad de ser titular.

    Lineal entre `BENCH_POINTS_FACTOR` -no cuento con el- y 1,0
    -titular seguro-. Sin dato devuelve 1,0: no se escala lo que
    no se sabe, se penaliza por otro lado (la confianza).
    """

    if probability is None:
        return 1.0

    try:
        p = float(probability)
    except (TypeError, ValueError):
        return 1.0

    p = max(0.0, min(p, 100.0)) / 100.0

    return BENCH_POINTS_FACTOR + (1.0 - BENCH_POINTS_FACTOR) * p


def _is_predicted_bench(starter: dict | None) -> bool:
    """
    Claramente suplente esta jornada, no simplemente "no titular".

    La diferencia importa: entre el 40 y el 67 hay una franja de
    duda que no es motivo para vetar una compra, y tratarla como
    suplencia era lo que hacia que el veto saltase por un punto.
    """

    probabilidad = (starter or {}).get("probability")

    if probabilidad is None:
        return False

    return float(probabilidad) <= BENCH_PROBABILITY_THRESHOLD


def is_predicted_starter(starter: dict | None) -> bool:

    if not starter:
        return False

    probabilidad = starter.get("probability")

    if probabilidad is None:
        return False

    return float(probabilidad) >= STARTER_PROBABILITY_THRESHOLD


def estimate_season_points(
    player: dict,
    points_market: dict,
    team_strength: dict | None = None,
    starter: dict | None = None,
) -> dict:
    """
    Cuantos puntos cabe esperar de este jugador.

    Con historico, los del ano pasado. Sin el, los que implica su
    precio, con la confianza rebajada.

    Y en los dos casos, escalados por la probabilidad de que
    llegue a jugar. `starter` es la entrada de
    `candidate_starter_lookup`: `{"probability", "consensus",
    "coverage", "source"}`. Sin ella el numero es el de siempre,
    pero se marca que se esta valorando a ciegas.

    `raw_points` conserva el numero sin escalar, porque explicar
    la decision requiere poder decir "97 puntos, pero suplente".
    """

    fuerza = None

    if team_strength and team_strength.get("available"):
        fuerza = (team_strength.get("index") or {}).get(
            safe_int(player.get("teamID"))
        )

    probabilidad = (starter or {}).get("probability")
    consenso = (starter or {}).get("consensus")

    factor, explicacion = expected_points_factor(starter)

    etiqueta = hierarchy_label(starter)

    if probabilidad is None and etiqueta is None:
        nota_titular = (
            " Sin pronostico de titularidad: se valora a ciegas y "
            "se exige mas margen."
        )
    else:
        nota_titular = (
            f" {etiqueta or 'sin jerarquia'}"
            + (
                f", {float(probabilidad):.0f} % titular"
                if probabilidad is not None
                else ""
            )
            + f" ({explicacion}): cuentan el "
            f"{factor*100:.0f} % de esos puntos."
        )

    def envolver(
        puntos_brutos: int,
        source: str,
        confidence: float,
        reason: str,
    ) -> dict:

        if probabilidad is None:
            confidence = confidence * CONFIDENCE_NO_STARTER_DATA

        # LO FIABLE QUE ES EL PRONOSTICO DE ESE EQUIPO
        #
        # No toca los puntos: toca cuanto se paga por ellos. Un
        # pronostico de un equipo "Imprevisible" vale lo mismo en
        # puntos y menos en euros, que es justo la distincion que
        # faltaba.
        fiabilidad, motivo_fiabilidad = predictability_confidence(
            starter
        )

        if fiabilidad is not None:
            confidence = confidence * fiabilidad

        return {
            "points": int(round(puntos_brutos * factor)),
            "raw_points": int(puntos_brutos),
            "source": source,
            "confidence": round(confidence, 4),
            "team_strength": fuerza,
            "starter_probability": (
                float(probabilidad)
                if probabilidad is not None
                else None
            ),
            "starter_consensus": consenso,
            "starter_factor": round(factor, 4),
            "starter_source": (
                (starter or {}).get("source")
                if probabilidad is not None
                else "SIN_DATO"
            ),
            "reason": reason + nota_titular,
        }

    historico = safe_int(player.get("pointsLastSeason"))

    if historico > 0:
        return envolver(
            historico,
            "HISTORICO",
            CONFIDENCE_HISTORICAL,
            f"{historico} puntos la temporada pasada en LaLiga.",
        )

    tarifa = safe_int(points_market.get("rate_median"))
    precio = safe_int(player.get("price"))

    if tarifa <= 0 or precio <= 0:
        return {
            "points": 0,
            "raw_points": 0,
            "source": "DESCONOCIDO",
            "confidence": 0.0,
            "team_strength": fuerza,
            "starter_probability": (
                float(probabilidad)
                if probabilidad is not None
                else None
            ),
            "starter_consensus": consenso,
            "starter_factor": round(factor, 4),
            "starter_source": "SIN_DATO",
            "reason": (
                "Sin historico y sin precio del punto: no hay por "
                "donde estimar."
            ),
        }

    implicados = int(precio / tarifa)

    return envolver(
        implicados,
        "IMPLICITO_MERCADO",
        CONFIDENCE_MARKET_IMPLIED,
        (
            f"Sin historico en LaLiga. Su precio implica unos "
            f"{implicados} puntos"
            + (
                f"; su equipo esta en el indice {fuerza:.2f} de la "
                f"liga."
                if fuerza is not None
                else "."
            )
        ),
    )


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
    candidate_starter: dict | None = None,
    replaced_starter: dict | None = None,

    # Sin jornada no se aplica el calendario. Es opcional a
    # proposito: quien no la pase se comporta como antes.
    matchday=None,

    # Si el que saldria esta HOY en el once. Opcional a proposito
    # por lo mismo: quien no lo pase se comporta como antes de
    # existir esta regla.
    replaced_in_lineup: bool = False,
) -> dict:
    """
    Lo maximo que pagariamos por un fichaje que mejora el once.

    `recovered_value` es lo que recuperamos vendiendo al que
    sustituye. Por defecto cero: lo prudente es suponer que se
    queda de suplente y no entra caja.

    `candidate_starter` y `replaced_starter` son las entradas de
    `candidate_starter_lookup`. Con ellas se aplica la regla que
    faltaba: quitar del once a un titular confirmado para meter a
    alguien que no lo es no es mejorar el once, sea cual sea la
    diferencia de puntos historicos. Ahi la operacion se rechaza
    entera, no se descuenta.
    """

    tarifa = safe_int(points_market.get("rate_median"))

    if tarifa <= 0:
        return _sin_valor(
            "SIN_TARIFA",
            "No se ha podido medir cuanto cuesta un punto.",
        )

    # --------------------------------------------------------
    # SIN PRONOSTICO NO SE PUJA
    #
    # La regla del once de aqui abajo solo se dispara cuando SABE
    # que el sustituido es titular. Con eso, la ausencia de dato
    # no frenaba: dejaba pasar.
    #
    # Se vio el 17/08/2026 al cambiar de fuente. Con el tablero
    # vacio la regla bloqueo cero operaciones y el sistema propuso
    # tres compras a ciegas -entre ellas la de Castrin, la que
    # destapo todo esto-. Antes bloqueaba diecisiete.
    #
    # Es el peor fallo posible en un guardarrail: cuanto menos
    # sabe, mas permite. Se invierte. Si falta el pronostico de
    # cualquiera de los dos lados, no hay mejora del once que
    # valorar. Si la fuente se cae, Pepe deja de mejorar el once
    # -que es molesto- en vez de fichar a ciegas -que es caro-.
    # --------------------------------------------------------

    for quien, senal in (
        ("del que saldria", replaced_starter),
        ("del que entraria", candidate_starter),
    ):

        if (senal or {}).get("probability") is None:

            return _sin_valor(
                "SIN_PRONOSTICO",
                (
                    f"No hay pronostico de titularidad {quien}. "
                    f"Sin ese dato no se puede saber si el once "
                    f"mejora, y a ciegas no se puja."
                ),
            )

    # --------------------------------------------------------
    # EL VETO ESTRUCTURAL
    #
    # Antes el veto era semanal: saltaba porque un porcentaje
    # cruzaba el 67. Eso hace que la misma compra este permitida
    # el martes y prohibida el jueves sin que haya cambiado nada
    # de fondo, y al reves: deja pasar a un Reserva que esta
    # puntualmente al 70 % porque el titular tiene gripe.
    #
    # Lo que no cambia el jueves es lo que es cada uno en su
    # equipo. Un Clave sigue siendo Clave en diciembre. Asi que el
    # veto se mide en escalones de jerarquia: se rechaza bajar dos
    # o mas. Clave por Importante, si. Clave por Rotacion, no.
    #
    # Es el error de Castrin dicho en su idioma: no era un
    # problema de porcentaje, era que es Reserva.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # A UN DIOS NO SE LE TOCA
    #
    # El veto por escalones no cubre este caso: de Dios a Clave
    # hay UN escalon, asi que colaba. Y la regla del dueño no
    # admite grises: "Yamal no se toca, a no ser que haya otro
    # DIOS en el mercado con mas puntos".
    #
    # Asi que la unica puerta es esa: otro Dios, y con mas
    # puntos. Cualquier otra cosa se rechaza entera.
    # --------------------------------------------------------

    if hierarchy_value(replaced_starter) == DIOS_HIERARCHY:

        entra_dios = (
            hierarchy_value(candidate_starter) == DIOS_HIERARCHY
        )

        if not entra_dios:
            return _sin_valor(
                "NO_SE_TOCA_UN_DIOS",
                (
                    f"Sustituiria a un Dios por un "
                    f"{hierarchy_label(candidate_starter)}. Un "
                    f"Dios solo se cambia por otro Dios con mas "
                    f"puntos."
                ),
            )

        if safe_int(candidate_points) <= safe_int(replaced_points):
            return _sin_valor(
                "NO_SE_TOCA_UN_DIOS",
                (
                    f"Los dos son Dios, pero el que entra no suma "
                    f"mas puntos "
                    f"({safe_int(candidate_points)} contra "
                    f"{safe_int(replaced_points)}). No se toca."
                ),
            )

    rango_sale = hierarchy_rank(replaced_starter)
    rango_entra = hierarchy_rank(candidate_starter)

    if rango_sale is not None and rango_entra is not None:

        caida = rango_sale - rango_entra

        if caida >= HIERARCHY_VETO_STEPS:

            return _sin_valor(
                "NO_MEJORA_JERARQUIA",
                (
                    f"Sustituiria a un "
                    f"{hierarchy_label(replaced_starter)} por un "
                    f"{hierarchy_label(candidate_starter)}: "
                    f"{caida} escalones de bajada. El once empeora "
                    f"toda la temporada, no solo esta jornada."
                ),
            )

    # --------------------------------------------------------
    # LA REGLA DEL ONCE, AHORA SOLO PARA LO EXTREMO
    #
    # Se mantiene como suelo, pero deja de dispararse por un
    # porcentaje que baja de 67 a 63: solo frena cuando el que
    # entra es claramente suplente esta jornada.
    # --------------------------------------------------------

    if is_predicted_starter(replaced_starter):

        if _is_predicted_bench(candidate_starter):

            p_sale = float(replaced_starter["probability"])

            p_entra = (candidate_starter or {}).get("probability")

            como_esta = (
                f"{float(p_entra):.0f} % titular"
                if p_entra is not None
                else "sin pronostico de titularidad"
            )

            return _sin_valor(
                "NO_MEJORA_TITULARIDAD",
                (
                    f"Sustituiria a un titular confirmado "
                    f"({p_sale:.0f} % titular) por alguien que "
                    f"esta {como_esta}. Sumara puntos en la hoja, "
                    f"no en el campo: el once empeora."
                ),
            )

    # --------------------------------------------------------
    # EL PROXIMO PARTIDO, DILUIDO
    # --------------------------------------------------------
    #
    # Los puntos que llegan aqui son de temporada y no saben nada
    # del calendario. El proximo partido se aplica a los dos
    # lados -al que entra y al que sale- pero repartido entre las
    # jornadas que quedan, porque el cambio dura eso y el partido
    # dura un sabado.
    #
    # En la jornada 2 esto casi no mueve nada, que es lo correcto.
    # En la 35 decide, que tambien.
    # --------------------------------------------------------

    entra = float(safe_int(candidate_points))
    sale = float(safe_int(replaced_points))

    partido_entra, motivo_entra = season_fixture_factor(
        candidate_starter,
        matchday,
    )

    partido_sale, _ = season_fixture_factor(
        replaced_starter,
        matchday,
    )

    if partido_entra is not None:
        entra *= partido_entra

    if partido_sale is not None:
        sale *= partido_sale

    delta = int(round(entra - sale))

    if delta <= 0:

        crudo = safe_int(candidate_points) - safe_int(
            replaced_points
        )

        # Que se note cuando lo que tumba el cambio es el
        # calendario y no el jugador: no es lo mismo "no mejora"
        # que "no mejora ESTA semana".
        por_el_partido = (
            crudo > 0
            and (
                partido_entra is not None
                or partido_sale is not None
            )
        )

        return _sin_valor(
            "NO_MEJORA",
            (
                (
                    f"Sumaria {crudo} puntos, pero con el "
                    f"calendario de la mano el cambio se queda "
                    f"en {delta}"
                    + (f": {motivo_entra}" if motivo_entra else "")
                    + ". Mejor esperar a otra jornada."
                )
                if por_el_partido
                else (
                    f"Suma {safe_int(candidate_points)} puntos y "
                    f"el que sustituiria tiene "
                    f"{safe_int(replaced_points)}. No es una "
                    f"mejora."
                )
            ),
        )

    # --------------------------------------------------------
    # SI EL QUE SALE ES TITULAR, SE APRIETA
    # --------------------------------------------------------
    #
    # Cambiar a un suplente es barato de deshacer: si sale mal, el
    # que entra se sienta y ya esta. Cambiar a un titular no: se
    # paga con una venta que tarda, por medio se juegan jornadas,
    # y el que sale no vuelve.
    #
    # Asi que se piden tres cosas a la vez, y las tres tienen que
    # cumplirse. Un cambio que gana por poco no compensa.

    if replaced_in_lineup:

        if delta < STARTER_SWAP_MIN_DELTA:
            return _sin_valor(
                "MEJORA_INSUFICIENTE",
                (
                    f"Solo sumaria {delta} puntos y saldria del "
                    f"once un titular. Para tocar el once hacen "
                    f"falta {STARTER_SWAP_MIN_DELTA}: un cambio "
                    f"asi se paga con una venta que tarda dias."
                ),
            )

        p_entra = (candidate_starter or {}).get("probability")
        p_sale = (replaced_starter or {}).get("probability")

        if p_entra is not None and p_sale is not None:

            ganancia = float(p_entra) - float(p_sale)

            if ganancia < STARTER_SWAP_MIN_PROBABILITY_GAIN:
                return _sin_valor(
                    "PIERDE_TITULARIDAD",
                    (
                        f"Suma {delta} puntos pero juega menos: "
                        f"{float(p_entra):.0f} % titular contra "
                        f"{float(p_sale):.0f} % del que sale. Los "
                        f"puntos estan en la hoja, no en el campo."
                    ),
                )

        # El margen normal es del 10 %. Aqui se exige el que sea
        # mayor de los dos, para que nadie pueda relajarlo pasando
        # un margen pequeño desde fuera.
        margin = max(margin, STARTER_SWAP_MARGIN)

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

        # Que clase de cambio es. Un cambio de titular hay que
        # poder distinguirlo en el tablero y en el registro: se
        # decide distinto y se revisa distinto.
        "replaces_starter": bool(replaced_in_lineup),

        # Lo que este cambio PROMETE. Se guarda para poder mirar
        # dentro de un mes si los cambios pagaron, en vez de
        # discutirlo.
        "promised_points": delta,
        "cost_per_point": (
            int(round((justo - safe_int(recovered_value)) / delta))
            if delta > 0
            else None
        ),

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
