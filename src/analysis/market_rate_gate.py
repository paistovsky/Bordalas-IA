"""
Freno y acelerador: el ritmo real de cada jugador manda en la
via especulativa.

LO QUE SE MIDIO (07/09/2026)

    Sobre 554 jugadores y seis dias de historial de precios:

        r = +0,90   entre el cambio de precio de un dia y el del
                    siguiente
        85,1 %      de los que subieron ayer suben hoy
        90,7 %      de los que bajaron ayer bajan hoy
        0,5 %       de los que bajaron baten al mercado
        83,8 %      de los jugadores no cambian de direccion ni
                    una vez en seis dias

    El precio de Biwenger no es un paseo aleatorio: son rampas de
    varios dias que casi nunca se giran.

EL FALLO QUE ESTO CIERRA

    La valoracion especulativa daba el MISMO numero a jugadores
    con comportamientos opuestos. Sobre la foto del 04/09:

        Bardeli        subio  6,06 % ayer -> valor = precio x 1,0132
        Andre Almeida  subio 17,07 % ayer -> valor = precio x 1,0132
        Nico Guillen   bajo   2,33 % ayer -> valor = precio x 1,0132

    Se reprodujo el numero exacto: sale de
    `computer_resale_value(precio, 0,0176)`. La via que ganaba en
    21 de los 22 candidatos era la de REVENTA AL COMPUTER, cuyo
    premium es una medida de MERCADO -la misma para todos por
    construccion- y no del jugador.

    O sea: la entrada no era una velocidad rota. Era una via que
    no mira al jugador ganandole por euros a la que si lo mira.

LAS TRES REGLAS DE COMPRA, Y DE DONDE SALE CADA UNA

    1. ACELERADOR. La tasa que se proyecta es el ritmo OBSERVADO
       del jugador, el que recoge el ojeador. Con r = +0,90,
       proyectar el ritmo de ayer es lo que corresponde.

       Sin ritmo observado NO se inventa una tasa: la via
       especulativa no valora, y se dice por que. Volver a la
       constante seria reintroducir el fallo con otro nombre.

    2. FRENO. Un precio que viene bajando no se compra como
       especulacion. Con un 0,5 % de aciertos no hay lectura de
       los datos en la que eso sea buena idea. El que baja no
       esta barato: esta bajando.

    3. AVISO. Una racha de subidas con la demanda desplomada no
       se compra. Sangare y Lookman llevaban siete dias subiendo
       con la demanda a -60 y -57 puntos: es el patron de una
       racha sin gasolina.

       La divergencia no sirve para entrar. Sirve para NO entrar.

LO QUE ESTO NO TOCA

    La via de MEJORA DEL ONCE. Un jugador que cae puede seguir
    mereciendo la pena por razones de futbol, y eso se decide con
    puntos, no con el precio de ayer.

    Ni umbrales, ni presupuestos, ni topes por operacion, ni
    guardarrailes de posicion o solvencia. Todos siguen mandando
    por encima de esto: esta compuerta solo puede decir que NO.
"""

from __future__ import annotations


# ============================================================
# LOS CORTES, Y CONTRA QUE ESTAN PUESTOS
# ============================================================

# Cualquier ritmo negativo frena. No hay banda de tolerancia
# porque no hay nada que tolerar: de los que bajaron ayer, el
# 90,7 % siguio bajando y solo el 0,5 % batio al mercado.
FALLING_RATE = 0.0

# Dias de racha a partir de los cuales se mira la demanda.
#
# El estudio: tras 1 dia subiendo continua el 92 %, tras 2 el
# 94 %, y a partir de 3 baja al 74 %. Ahi es donde una rampa
# empieza a poder agotarse, y donde tiene sentido preguntarle a
# la demanda si queda gasolina.
STREAK_DAYS_TO_CHECK_DEMAND = 3

# Y cuanta demanda en contra hace falta para no entrar. Es el
# mismo corte que usa el ojeador para publicar el pulso: por
# debajo, casi todos los jugadores estan en el mismo monton y la
# señal no distingue a nadie.
DEMAND_COLLAPSED = -20.0


ALLOW = "RITMO_OBSERVADO"
NO_RATE = "SIN_RITMO_OBSERVADO"
FALLING = "PRECIO_CAYENDO"
NO_FUEL = "RACHA_SIN_DEMANDA"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_market_rates(report: dict | None = None) -> dict:
    """
    `{player_id: {rate, direction, trend_days, demand_net}}`.

    Sale del informe del ojeador, que se LEE del disco: quien
    sale a la calle es el ciclo, cada seis horas.

    Nunca lanza. Sin informe devuelve un diccionario vacio, y sin
    ritmos la via especulativa simplemente no valora — que es el
    comportamiento correcto y no un fallo.
    """

    try:
        if report is None:
            from src.intelligence.scout.report import load_report

            report = load_report() or {}

        ritmos = {}

        for player_id, ficha in (report.get("players") or {}).items():

            if not isinstance(ficha, dict):
                continue

            consenso = ficha.get("consensus") or {}

            porcentaje = safe_float(
                consenso.get("mean_magnitude_percent")
            )

            if porcentaje is None:
                continue

            direccion = consenso.get("direction")

            # El ojeador publica la magnitud sin signo y la
            # direccion aparte. Sin esto, una bajada del 6 %
            # entraria como una subida del 6 %, que es el error
            # mas caro que se puede cometer aqui.
            if direccion == "DOWN":
                porcentaje = -abs(porcentaje)

            elif direccion == "FLAT":
                porcentaje = 0.0

            else:
                porcentaje = abs(porcentaje)

            try:
                clave = int(player_id)

            except (TypeError, ValueError):
                continue

            ritmos[clave] = {
                "rate_percent_per_day": round(porcentaje, 4),
                "direction": direccion,
                "trend_days": ficha.get("trend_days"),
                "demand_net": (ficha.get("demand") or {}).get(
                    "pressure_points"
                ),
                "sources": consenso.get("sources_total"),
                "agreement": consenso.get("agreement"),
            }

        return ritmos

    except Exception:                               # noqa: BLE001
        return {}


def evaluate(player_id, rates: dict | None) -> dict:
    """
    ¿Se puede valorar a este jugador como especulacion, y a que
    ritmo?

    Devuelve siempre `allow`, `code`, `reason` y el ritmo, para
    que la fila del tablero pueda explicar el "no" sin que nadie
    tenga que ir a leer el codigo.
    """

    señal = (rates or {}).get(safe_int(player_id))

    if not señal:
        return {
            "allow": False,
            "code": NO_RATE,
            "rate_percent_per_day": None,
            "trend_days": None,
            "demand_net": None,
            "reason": (
                "El ojeador no tiene ritmo observado de este "
                "jugador, y una tasa inventada es justo el fallo "
                "que se acaba de cerrar: no se valora como "
                "especulacion."
            ),
        }

    ritmo = safe_float(señal.get("rate_percent_per_day"))
    racha = safe_int(señal.get("trend_days"))
    demanda = safe_float(señal.get("demand_net"))

    base = {
        "rate_percent_per_day": ritmo,
        "trend_days": señal.get("trend_days"),
        "demand_net": señal.get("demand_net"),
        "sources": señal.get("sources"),
        "agreement": señal.get("agreement"),
    }

    # ------------------------------------------------------
    # EL FRENO
    # ------------------------------------------------------

    if ritmo is None or ritmo < FALLING_RATE:
        return {
            **base,
            "allow": False,
            "code": FALLING,
            "reason": (
                f"El precio viene bajando ({ritmo:+.2f} %/dia). De "
                f"los que bajaron ayer, el 90,7 % siguio bajando y "
                f"solo el 0,5 % batio al mercado: el que cae no "
                f"esta barato, esta cayendo."
            ),
        }

    if ritmo == 0:
        return {
            **base,
            "allow": False,
            "code": FALLING,
            "reason": (
                "El precio esta quieto: no hay ritmo que proyectar, "
                "y proyectar cero es no esperar ninguna "
                "revalorizacion."
            ),
        }

    # ------------------------------------------------------
    # EL AVISO: RACHA SIN GASOLINA
    # ------------------------------------------------------

    if (
        racha >= STREAK_DAYS_TO_CHECK_DEMAND
        and demanda is not None
        and demanda <= DEMAND_COLLAPSED
    ):
        return {
            **base,
            "allow": False,
            "code": NO_FUEL,
            "reason": (
                f"Lleva {racha} dias subiendo pero la demanda esta "
                f"desplomada ({demanda:+.0f} puntos netos): es el "
                f"patron de una racha agotandose. A partir de tres "
                f"dias la continuidad cae del 93 % al 74 %, y sin "
                f"compradores detras no hay quien sostenga la "
                f"subida."
            ),
        }

    # ------------------------------------------------------
    # EL ACELERADOR
    # ------------------------------------------------------

    return {
        **base,
        "allow": True,
        "code": ALLOW,
        "reason": (
            f"Ritmo observado {ritmo:+.2f} %/dia"
            + (f", {racha} dia(s) de racha" if racha else "")
            + (
                f", demanda {demanda:+.0f}"
                if demanda is not None
                else ""
            )
            + "."
        ),
    }
