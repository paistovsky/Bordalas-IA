"""
Cuando vender: no a los tres dias, sino cuando deje de compensar.

EL HORIZONTE FIJO ERA UNA SUPOSICION

    Toda la via TENER se decidio a tres dias porque tres dias
    era lo maximo que permitia medir una ventana de seis. Nunca
    fue una eleccion: era el borde de la muestra.

    Con historico de verdad (27/09/2026) resulto que tres no es
    el maximo de NINGUNA metrica:

        por operacion        el maximo esta en 10 dias
        por dia de capital   el maximo esta en 1 dia

    Y cual manda depende de que escasee. Con el mercado seco
    -cero comprables de 47- el dinero iba a estar parado de
    todas formas, asi que conviene aguantar. Con el mercado
    lleno, cada dia de mas es un dia que ese dinero no esta
    girando.

    Un numero fijo no puede contestar eso. Por eso el horizonte
    deja de ser un numero y pasa a ser una comparacion.

LA REGLA

    Se vende cuando lo que queda por ganar aguantando un dia mas
    cae por debajo de lo que darian esa ficha y ese dinero en la
    mejor alternativa disponible EN ESE MOMENTO.

        aguantar   si   ganancia_de_un_dia_mas > coste_de_oportunidad
        vender     si   no

    Con el mercado seco el coste de oportunidad es cero y se
    aguanta hasta el tope. Con el mercado lleno el listón sube
    solo, sin tocar nada.

EL TOPE DURO

    Diez dias. No es prudencia: es el ultimo horizonte que el
    retrotest mide. Mas alla no hay dato, y este proyecto ya se
    quemo una vez extrapolando -el 15/09, con rachas de 50 dias
    juzgadas por una curva que llegaba a 2-.

LO QUE SE PUBLICA AL LADO DE CADA POSICION

    La tasa de perdida del horizonte elegido. Aguantar diez dias
    rinde mas por operacion Y pierde tres veces mas a menudo
    (2,8 % a un dia contra 30,3 % a diez). Un horizonte sin su
    tasa de perdida es medio dato.

FASE OBSERVADOR

    Calcula y publica. No vende, no compra y no mueve ningun
    liston. Ningun motor lee este modulo: esta para poder mirar
    una semana de decisiones simuladas antes de que mande.
"""

from __future__ import annotations

from src.analysis.hold_backtest import (
    HORIZONS,
    MIN_SAMPLE,
    _streak_bucket,
    rate_bucket_of,
)


# EL TOPE DURO
#
#     El ultimo horizonte medido. No se mueve por prudencia sino
#     porque a partir de aqui no hay muestra.
TOPE_DE_DIAS = max(HORIZONS)


# Lo que gana un dia mas tiene que superar al coste de
# oportunidad POR ESTE MARGEN para que valga la pena aguantar.
#
# Cero: la regla es una comparacion limpia y no lleva colchon.
# Existe como constante para que el dia que alguien quiera
# ponerle uno tenga que escribir el numero y no esconderlo en
# un `>=`.
MARGEN_PARA_AGUANTAR = 0.0


# El interruptor. Hoy no hace falta -nadie lee esto- pero la
# casa entera funciona asi y una pieza sin interruptor es una
# pieza que no se puede apagar el dia que haga falta.
DISABLE_ENV = "BORDALAS_HORIZONTE_FIJO"


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


def _vacio(motivo: str) -> dict:
    """
    LA FORMA NO CAMBIA CON LOS DATOS (17/09/2026)

    Las mismas claves con muestra y sin ella. Un `KeyError` en
    produccion por un campo que solo existe los dias buenos es
    como se cayo la verja el 18/09.
    """

    return {
        "available": False,
        "decision": None,
        "days_held": 0,
        "horizon": None,
        "max_horizon": TOPE_DE_DIAS,
        "marginal_percent": None,
        "opportunity_percent": None,
        "loss_rate_percent": None,
        "rate_bucket": None,
        "streak_band": None,
        "sample": 0,
        "capped_by": None,

        # Si sabemos desde cuando lo tenemos. Sin esto, el tope
        # de diez dias no se puede hacer cumplir y hay que
        # decirlo en vez de suponer que lleva cero.
        "days_known": False,

        "reason": motivo,
    }


def coste_de_oportunidad(tablero: dict | None) -> dict:
    """
    Cuanto daria hoy la mejor alternativa, POR DIA.

    Se mide sobre lo que de verdad se podria comprar: una fila
    que no es BID no es una alternativa, es un deseo. Si no hay
    ninguna, el coste es CERO y aguantar sale gratis — que es
    justo lo que pasa con el mercado seco de hoy.

    `horizon_days` es a cuantos dias se compara. La alternativa
    tambien tarda en dar su rendimiento, asi que compararla en
    bruto contra la ganancia de UN dia seria hacer trampa a
    favor de vender.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "per_day_percent": 0.0,
        "best": None,
        "candidates": 0,
        "reason": "Sin tablero: no hay alternativa que medir.",
    }

    try:
        filas = (tablero or {}).get("targets") or []

        comprables = [
            f
            for f in filas
            if isinstance(f, dict) and f.get("decision") == "BID"
        ]

        if not comprables:
            return {
                **vacio,
                "available": True,
                "candidates": 0,
                "reason": (
                    "Hoy no hay ninguna compra ejecutable, asi "
                    "que el dinero liberado no tendria donde ir: "
                    "el coste de aguantar es cero."
                ),
            }

        mejor = None

        for fila in comprables:

            puja = safe_int(fila.get("bid"))
            ganancia = safe_float(fila.get("expected_value"), 0.0)

            if puja <= 0 or ganancia is None:
                continue

            # A cuantos dias se cobra esa ganancia. Sin dato, el
            # horizonte de la casa.
            dias = safe_int(
                (fila.get("deployment") or {}).get(
                    "horizon_days"
                ),
                default=3,
            ) or 3

            por_dia = 100 * (ganancia / puja) / dias

            if mejor is None or por_dia > mejor["per_day_percent"]:
                mejor = {
                    "name": fila.get("name"),
                    "id": fila.get("id"),
                    "per_day_percent": round(por_dia, 4),
                    "yield_percent": round(
                        100 * ganancia / puja, 3
                    ),
                    "horizon_days": dias,
                    "bid": puja,
                }

        if mejor is None:
            return {
                **vacio,
                "available": True,
                "candidates": len(comprables),
                "reason": (
                    "Hay compras ejecutables pero ninguna "
                    "publica puja y ganancia: no se puede medir "
                    "la alternativa."
                ),
            }

        return {
            "available": True,
            "per_day_percent": mejor["per_day_percent"],
            "best": mejor,
            "candidates": len(comprables),
            "reason": (
                f"La mejor alternativa de hoy es "
                f"{mejor['name']}: rinde un "
                f"{mejor['yield_percent']:.2f} % en "
                f"{mejor['horizon_days']} dias, que son "
                f"{mejor['per_day_percent']:.3f} % al dia."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir la alternativa: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _celda(retrotest: dict, tramo: str, banda: str, dias: int):
    """La celda del retrotest, o None si no tiene muestra."""

    celda = (retrotest.get("cells") or {}).get(
        f"{tramo}|{banda}|{dias}"
    )

    if not celda or not celda.get("enough"):
        return None

    return celda


def ganancia_de_un_dia_mas(
    retrotest: dict | None,
    rate_percent_per_day,
    trend_days,
) -> dict:
    """
    Lo que queda por ganar aguantando UN dia mas.

    SE REEVALUA, NO SE EXTRAPOLA

        No se pregunta "cuanto le queda a la curva desde el dia
        tres", porque la racha de hoy no es la del dia de la
        compra y esa curva ya no es la suya. Se pregunta lo
        unico que se puede contestar con muestra: que rinde UN
        dia para un jugador que HOY esta en este tramo y con
        esta racha.

        Es la misma disciplina del 15/09: no se opina fuera de
        donde hay dato.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "percent": None,
        "loss_rate_percent": None,
        "sample": 0,
        "rate_bucket": None,
        "streak_band": None,
        "reason": "Sin retrotest con el que medir.",
    }

    try:
        if not (retrotest or {}).get("available"):
            return vacio

        tramo = rate_bucket_of(rate_percent_per_day)

        # LA RACHA ES MAGNITUD, NO SIGNO (27/09/2026)
        #
        #     `streak()` del retrotest cuenta dias seguidos en la
        #     MISMA direccion y siempre devuelve positivo: el
        #     signo del movimiento vive en el tramo de tasa, no
        #     en la racha. El ojeador, en cambio, publica
        #     `trend_days` con signo: -21 es "lleva 21 dias
        #     bajando".
        #
        #     Sin este `abs()` un jugador que cae sale «sin
        #     banda» y por tanto SIN_DATO — justo el caso mas
        #     claro de venta que existe. Lo canto la primera
        #     pasada de la sombra.
        #
        #     `hold_switch` y `hold_value` ya lo hacian bien;
        #     esto era una pieza nueva repitiendo un error
        #     resuelto.
        banda = _streak_bucket(abs(safe_int(trend_days)))

        if tramo is None or banda is None:
            return {
                **vacio,
                "rate_bucket": tramo,
                "streak_band": banda,
                "reason": (
                    "Sin ritmo o sin racha: no cae en ninguna "
                    "celda del retrotest."
                ),
            }

        celda = _celda(retrotest, tramo, banda, 1)

        if celda is None:
            return {
                **vacio,
                "rate_bucket": tramo,
                "streak_band": banda,
                "reason": (
                    f"La celda «{tramo}» / «{banda}» no llega a "
                    f"{MIN_SAMPLE} operaciones a un dia."
                ),
            }

        return {
            "available": True,
            "percent": round(100 * celda["median"], 4),
            "loss_rate_percent": round(
                100 * celda["loss_rate"], 2
            ),
            "sample": celda["n"],
            "rate_bucket": tramo,
            "streak_band": banda,
            "reason": None,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir: "
                f"{type(error).__name__}: {error}"
            ),
        }


def cuando_vender(
    posicion: dict | None,
    retrotest: dict | None,
    alternativa: dict | None,
) -> dict:
    """
    Aguantar un dia mas, o vender.

    `posicion` lleva `days_held`, `rate_percent_per_day` y
    `trend_days`. `alternativa` es lo que devuelve
    `coste_de_oportunidad`.

    Nunca lanza. Forma fija.
    """

    try:
        posicion = posicion or {}

        # LOS DIAS EN CARTERA: DECIMALES, Y EL DESCONOCIDO NO ES
        # CERO (27/09/2026)
        #
        #     `safe_int` truncaba: un jugador comprado hace 0,62
        #     dias salia con 0. Y lo peor, uno del que NO se sabe
        #     la fecha tambien salia con 0 — que significa
        #     "comprado hoy" y empuja a aguantar de mas.
        #
        #     Ahora el desconocido viaja como None y se dice:
        #     la regla se puede aplicar igual, pero el tope de
        #     diez dias no se puede hacer cumplir.
        dias = safe_float(posicion.get("days_held"))

        base = _vacio("")
        base["days_held"] = dias
        base["days_known"] = dias is not None

        # EL TOPE DURO, ANTES QUE NADA
        #
        #     Si ya lleva el maximo medido, no hay nada que
        #     comparar: cualquier respuesta seria una opinion
        #     sobre terreno sin muestra.
        if dias is not None and dias >= TOPE_DE_DIAS:
            return {
                **base,
                "available": True,
                "decision": "VENDER",
                "horizon": dias,
                "capped_by": "TOPE_MEDIDO",
                "reason": (
                    f"Lleva {dias:.1f} dias y el retrotest solo mide "
                    f"hasta {TOPE_DE_DIAS}. Mas alla no hay dato, "
                    f"y aqui no se opina sin muestra."
                ),
            }

        marginal = ganancia_de_un_dia_mas(
            retrotest,
            posicion.get("rate_percent_per_day"),
            posicion.get("trend_days"),
        )

        base["rate_bucket"] = marginal["rate_bucket"]
        base["streak_band"] = marginal["streak_band"]
        base["sample"] = marginal["sample"]
        base["loss_rate_percent"] = marginal["loss_rate_percent"]
        base["marginal_percent"] = marginal["percent"]

        if not marginal["available"]:
            return {
                **base,
                "available": True,
                "decision": "SIN_DATO",
                "reason": (
                    f"No se puede decidir: {marginal['reason']} "
                    f"Sin dato se deja como esta, que es lo que "
                    f"se hacia antes de existir esta regla."
                ),
            }

        coste = safe_float(
            (alternativa or {}).get("per_day_percent"), 0.0
        )

        base["opportunity_percent"] = round(coste, 4)

        gana = marginal["percent"]

        aguanta = gana > coste + MARGEN_PARA_AGUANTAR

        return {
            **base,
            "available": True,
            "decision": "AGUANTAR" if aguanta else "VENDER",
            # Sin fecha de compra no hay horizonte que nombrar:
            # se sabe QUE hacer, no en que dia se esta.
            "horizon": (
                None
                if dias is None
                else (dias + 1 if aguanta else dias)
            ),
            "capped_by": None,
            "reason": _reason(
                aguanta, gana, coste, marginal, dias, alternativa
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo decidir: "
            f"{type(error).__name__}: {error}"
        )


def _reason(
    aguanta, gana, coste, marginal, dias, alternativa
) -> str:

    cabeza = (
        f"Un dia mas rinde {gana:+.2f} % "
        f"(tramo «{marginal['rate_bucket']}», racha "
        f"«{marginal['streak_band']}», {marginal['sample']} "
        f"operaciones, pierde "
        f"{marginal['loss_rate_percent']:.1f} % de las veces)"
    )

    if coste <= 0:
        alternativa_texto = (
            "y hoy no hay ninguna compra ejecutable donde poner "
            "ese dinero"
        )

    else:
        mejor = (alternativa or {}).get("best") or {}

        alternativa_texto = (
            f"contra el {coste:.3f} % diario que daria "
            f"{mejor.get('name', 'la mejor alternativa')}"
        )

    if aguanta:

        if dias is None:
            return (
                f"{cabeza} {alternativa_texto}. Se aguanta. No "
                f"consta desde cuando lo tenemos, asi que el "
                f"tope de {TOPE_DE_DIAS} dias no se puede hacer "
                f"cumplir: el tablon de la liga solo guarda los "
                f"ultimos movimientos."
            )

        return (
            f"{cabeza} {alternativa_texto}. Se aguanta: lleva "
            f"{dias:.1f} dias y el tope medido son "
            f"{TOPE_DE_DIAS}."
        )

    return (
        f"{cabeza} {alternativa_texto}. Se vende: el dinero "
        f"rinde mas fuera."
    )


# Las lineas del tablon que significan "ahora es nuestro".
# `USER_TRANSFER` cuenta: un jugador comprado a un manager
# empieza su cartera igual que uno comprado al Computer.
COMPRAS = frozenset(
    {"BUY_FROM_COMPUTER", "USER_TRANSFER"}
)


def dias_en_cartera(
    market_feed: list | None,
    own_name: str | None,
    ahora=None,
) -> dict:
    """
    `{player_id: dias que llevamos con el}`.

    DE DONDE SALE, Y POR QUE NO DE LA PLANTILLA

        La plantilla dice a quien tenemos, no desde cuando. Sin
        fecha de compra el horizonte adaptativo no puede empezar
        a contar, asi que sale del tablon de la liga, que
        publica cada movimiento con su marca de tiempo.

    LO QUE NO ESTA, NO SE INVENTA

        El tablon guarda los ultimos movimientos, no la
        temporada entera. Un jugador comprado hace un mes no
        aparece y sale SIN DATO, no con un cero: un cero
        significa "comprado hoy" y seria mentira en la direccion
        peor -aguantar mas de la cuenta-.

    Nunca lanza. Forma fija.
    """

    dias = {}

    try:
        from datetime import datetime

        ahora = ahora or datetime.now()

        for linea in (market_feed or []):

            if not isinstance(linea, dict):
                continue

            if str(linea.get("type") or "") not in COMPRAS:
                continue

            if own_name is not None and (
                linea.get("buyer") != own_name
            ):
                continue

            marca = linea.get("timestamp")

            try:
                if isinstance(marca, (int, float)):
                    cuando = datetime.fromtimestamp(marca)

                else:
                    cuando = datetime.fromisoformat(
                        str(marca).replace("Z", "")
                    )

            except (TypeError, ValueError, OSError):
                continue

            jugador = safe_int(linea.get("player_id"))

            if not jugador:
                continue

            transcurrido = (
                ahora - cuando
            ).total_seconds() / 86400

            if transcurrido < 0:
                continue

            # La compra MAS RECIENTE manda: si se compro, se
            # vendio y se recompro, la cartera empieza en la
            # ultima y no en la primera.
            anterior = dias.get(jugador)

            if anterior is None or transcurrido < anterior:
                dias[jugador] = round(transcurrido, 2)

        return dias

    except Exception:                               # noqa: BLE001
        return {}


def posiciones_de(
    roster: list | None,
    market_rates: dict | None,
    dias_por_jugador: dict | None = None,
) -> list:
    """
    Nuestras posiciones, con lo que hace falta para decidir.

    Cada una lleva el ritmo y la racha del ojeador —los mismos
    que usa el tablero de compras, no unos parecidos— y cuantos
    dias llevamos con ella.

    Nunca lanza. Forma fija por elemento.
    """

    posiciones = []

    try:
        for jugador in (roster or []):

            if not isinstance(jugador, dict):
                continue

            identificador = safe_int(jugador.get("id"))

            if not identificador:
                continue

            señal = (market_rates or {}).get(identificador) or {}

            posiciones.append(
                {
                    "id": identificador,
                    "name": jugador.get("name"),
                    "price": safe_int(jugador.get("price")),
                    "rate_percent_per_day": señal.get(
                        "rate_percent_per_day"
                    ),
                    "trend_days": señal.get("trend_days"),
                    "days_held": (dias_por_jugador or {}).get(
                        identificador
                    ),
                }
            )

        return posiciones

    except Exception:                               # noqa: BLE001
        return posiciones


def sombra(
    posiciones: list | None,
    retrotest: dict | None,
    tablero: dict | None,
) -> dict:
    """
    La tabla entera de decisiones simuladas.

    EN SOMBRA Y SIN ENCENDER

        Publica lo que la regla HARIA. Ningun motor lee esto:
        existe para poder mirar una semana de decisiones antes
        de que ninguna se ejecute.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "observer_only": True,
        "enabled": False,
        "max_horizon": TOPE_DE_DIAS,
        "opportunity": None,
        "rows": [],
        "counts": {"AGUANTAR": 0, "VENDER": 0, "SIN_DATO": 0},
        "reason": None,
    }

    try:
        alternativa = coste_de_oportunidad(tablero)

        filas = []

        for posicion in (posiciones or []):

            if not isinstance(posicion, dict):
                continue

            veredicto = cuando_vender(
                posicion, retrotest, alternativa
            )

            filas.append(
                {
                    "id": posicion.get("id"),
                    "name": posicion.get("name"),
                    "days_held": veredicto["days_held"],
                    "rate_percent_per_day": posicion.get(
                        "rate_percent_per_day"
                    ),
                    "trend_days": posicion.get("trend_days"),

                    "decision": veredicto["decision"],
                    "horizon": veredicto["horizon"],

                    # LA TASA DE PERDIDA, AL LADO. SIEMPRE.
                    #
                    #     Aguantar diez dias rinde mas por
                    #     operacion y pierde tres veces mas a
                    #     menudo. Un horizonte sin su tasa de
                    #     perdida es medio dato.
                    "loss_rate_percent": veredicto[
                        "loss_rate_percent"
                    ],

                    "marginal_percent": veredicto[
                        "marginal_percent"
                    ],
                    "opportunity_percent": veredicto[
                        "opportunity_percent"
                    ],
                    "rate_bucket": veredicto["rate_bucket"],
                    "streak_band": veredicto["streak_band"],
                    "sample": veredicto["sample"],
                    "capped_by": veredicto["capped_by"],
                    "reason": veredicto["reason"],
                }
            )

        cuenta = {"AGUANTAR": 0, "VENDER": 0, "SIN_DATO": 0}

        for fila in filas:
            if fila["decision"] in cuenta:
                cuenta[fila["decision"]] += 1

        return {
            "available": True,
            "observer_only": True,
            "enabled": False,
            "max_horizon": TOPE_DE_DIAS,
            "opportunity": alternativa,
            "rows": filas,
            "counts": cuenta,
            "reason": (
                f"{len(filas)} posiciones miradas: "
                f"{cuenta['AGUANTAR']} aguantarian, "
                f"{cuenta['VENDER']} se venderian, "
                f"{cuenta['SIN_DATO']} sin dato. "
                f"EN SOMBRA: nadie ejecuta esto."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar la sombra: "
                f"{type(error).__name__}: {error}"
            ),
        }
