"""
El carry: lo que cuesta de verdad tener a un jugador.

NI EL IMPORTE ENTERO NI CERO

    `xi_upgrade_value` cobra el importe entero, como si el dinero
    desapareciera. La via de reventa no cobra nada, porque cuenta
    el activo completo. Las dos estan mal por el mismo sitio: el
    coste de tener a alguien no es lo que pagas, es lo que pierdes
    mientras lo tienes.

        prima de compra        lo que pagas por encima del mercado
        deriva del precio      lo que hace su precio mientras lo tienes
        coste de oportunidad   lo que ese dinero habria hecho en otro sitio

EL CARRY NO ES UNA PROPIEDAD DEL JUGADOR: ES DEL MOMENTO EN QUE
ENTRAS (17/09/2026)

    Medido sobre 15.253 observaciones jugador-dia del 16/08 al
    16/09 (`data/autopilot/price_history.json`, sello 16/09 18:23),
    partiendo por lo que hizo el precio la vispera:

        vispera    n        deriva a 1 dia   a 10 dias
        SUBIA      4.120    +1,235 %         +7,430 %
        PLANO      4.865     0,000 %          0,000 %
        BAJABA     6.268    −1,389 %        −11,711 %

    Comprar a uno que sube y comprar a uno que baja no se
    diferencian en un poco: se diferencian en DIECINUEVE PUNTOS a
    diez dias. Un carry unico para todos los jugadores seria la
    media de dos cosas que no se parecen.

LA CONTRADICCION DE LAS DOS MEDICIONES, RESUELTA

        `sale_order` dice   +0,2479 %/dia   (nuestra plantilla, un dia)
        el 15/09 decia      mediana −376    (81 jugadores)

    Las dos son ciertas y ninguna sirve para esto. Sobre las 612
    fichas del catalogo con cinco o mas pares de dias seguidos:

        mediana de las medianas   +0,0000 %/dia
        media de las medias       +0,1285 %/dia
        suben 130 · bajan 248 · planos 234

    La MEDIA sube porque una minoria sube mucho; la MEDIANA no se
    mueve porque el jugador tipico no se mueve. Para el carry no
    vale ninguna de las dos: vale la CONDICIONADA, porque el dato
    que tienes cuando vas a comprar es que hizo su precio ayer.

EL HORIZONTE SALE DE LA MEDICION, NO DE UNA PREFERENCIA

    Doctrina 53: el carry no existe sin plazo. Y el plazo no se
    elige, se mide. La deriva del que sube SATURA:

        1 dia  +1,235 %      10 dias  +7,430 %   <- el techo
        3      +3,356 %      14       +6,963 %   <- ya devuelve
        6      +5,621 %      21       +6,061 %

    A partir del dia diez, tener al que sube deja de pagar y
    empieza a devolver. Asi que el horizonte es DIEZ DIAS: no
    porque nos guste, sino porque es donde la curva gira.

    Y COINCIDE, sin haberlo buscado, con los 10,2 dias medianos
    que duraron nuestras posiciones cerradas (medido el 16/09
    sobre 7 viajes). Es una coincidencia que conviene decir como
    coincidencia: son dos mediciones distintas que caen en el
    mismo sitio, no una derivada de la otra.

EL TOPE SE VA CON LA VIA — DOCTRINA 69

    Esta semana un freno se ha quedado huerfano cuatro veces. Si
    el coste de fichar baja y la vía del once NO tiene tope de
    prima —hoy no lo tiene—, `optimal_bid` pujaria hasta el valor.

    Por eso el tope va EN LA MISMA LINEA que la formula, y no es
    un numero nuevo: es `PRIMA_MAXIMA_DE_PUJA`, el +0,25 % que ya
    aplica a la otra via. No se inventa un umbral; se extiende el
    que hay. Y hay guardia que falla si llega a `None`.

FASE OBSERVADOR

    `ENCENDIDO = False`. Esto calcula y publica. No cambia ningun
    valor, ningun liston y ningun bolsillo.
"""

from __future__ import annotations

from src.analysis.rival_bid_model import PRIMA_MAXIMA_DE_PUJA


ENCENDIDO = False


# ============================================================
# EL HORIZONTE
# ============================================================
#
#     Diez dias: donde la deriva del que sube deja de crecer.
#     Medido sobre price_history.json, 16/08 a 16/09, n=3.057
#     observaciones a ese plazo.
HORIZONTE_DIAS = 10

HORIZONTE_FUENTE = (
    "La deriva del que subia satura en el dia 10 (+7,430 %) y "
    "despues devuelve (+6,963 % a 14, +6,061 % a 21). Medido sobre "
    "price_history.json del 16/09, 16/08 a 16/09, n=3.057 a diez "
    "dias."
)


# ============================================================
# EL TOPE, EN LA MISMA LINEA QUE LA FORMULA
# ============================================================
#
#     NO ES UN NUMERO NUEVO. Es el mismo +0,25 % que `optimal_bid`
#     ya aplica a SPECULATION, extendido a la via del once. Si
#     alguien lo mueve alli, se mueve aqui.
TOPE_DE_PRIMA_DE_FICHAJE = PRIMA_MAXIMA_DE_PUJA


# ============================================================
# LA DERIVA, CONDICIONADA. Medida, no supuesta.
# ============================================================
#
#     Mediana del cambio ACUMULADO de precio a H dias, segun lo
#     que hizo el precio la vispera del dia en que compras.
#
#     Fuente: data/autopilot/price_history.json, sello 2026-09-16
#     18:23. Ventana 16/08 a 16/09 2026.
DERIVA = {
    "SUBIA": {
        1: (1.235, 4120),
        3: (3.356, 3806),
        6: (5.621, 3373),
        10: (7.430, 3057),
        14: (6.963, 2438),
        21: (6.061, 1319),
    },
    "PLANO": {
        1: (0.000, 4865),
        3: (0.000, 4489),
        6: (0.000, 3844),
        10: (0.000, 3400),
        14: (0.000, 2653),
        21: (0.000, 1410),
    },
    "BAJABA": {
        1: (-1.389, 6268),
        3: (-4.032, 5739),
        6: (-7.628, 5014),
        10: (-11.711, 4500),
        14: (-14.609, 3512),
        21: (-17.035, 1970),
    },
}

DERIVA_FUENTE = (
    "data/autopilot/price_history.json (sello 2026-09-16 18:23), "
    "16/08 a 16/09 2026, 15.253 observaciones jugador-dia"
)


# LA PRIMA QUE PAGAMOS DE VERDAD AL ENTRAR.
#
#     Medida sobre el libro de pujas: 11 compras ganadas en
#     septiembre, mediana +0,2507 %. Es el tope del +0,25 %
#     mordiendo: la prima no es una eleccion, es el techo.
#
#     Las 8 de agosto salen a −20,74 % y NO se usan: son
#     posiciones adoptadas por el bootstrap, donde `market_price`
#     no significa lo mismo. Queda dicho en vez de mezclarlas.
PRIMA_DE_COMPRA_PERCENT = 0.2507

PRIMA_DE_COMPRA_N = 11

PRIMA_DE_COMPRA_FUENTE = (
    "data/trading/bid_outcome_ledger.json, 11 compras ganadas en "
    "2026-09, mediana +0,2507 %"
)


# EL COSTE DE OPORTUNIDAD.
#
#     El dinero metido en un jugador no pelea otras subastas. Lo
#     que habria rendido en otro sitio son dos numeros medidos,
#     multiplicados:
#
#       - lo que rinde un viaje nuestro: +4,20 % netos en 10,2
#         dias medianos (medido el 16/09 sobre 7 viajes cerrados)
#       - cuantas veces de verdad lo habriamos usado: pujamos en
#         el 20,3 % de las 182 subastas (medido el 17/09)
#
#     Ignorar el segundo factor seria cobrar un coste de
#     oportunidad que no existe: no se pierde lo que no se iba a
#     hacer.
RENDIMIENTO_DE_UN_VIAJE_PERCENT = 4.20

VIAJES_N = 7

PARTICIPACION = 0.203

PARTICIPACION_N = 182

OPORTUNIDAD_FUENTE = (
    "+4,20 % netos por viaje (n=7 viajes cerrados, medido el "
    "16/09) x 20,3 % de participacion en subastas (n=182, medido "
    "el 17/09)"
)


# ============================================================
# LOS LIBROS QUE LA VERJA ENSUCIA
# ============================================================
#
#     Medido el 17/09 corriendo la verja entera con los libros en
#     HEAD antes y despues: CINCO de dieciseis cambian. La verja
#     ejercita `build_state` con la foto del 13/09 de fixture, y
#     lo que escribe lleva la fecha de hoy con datos de hace
#     cuatro dias.
#
#     LA LISTA VIVE AQUI Y NO EN LA GUARDIA a proposito. La Regla
#     A de `test_verja_determinista_v1` busca el directorio de
#     estado en cualquier literal de un modulo de la verja, y no
#     distingue una ruta que se LEE de una que se NOMBRA. Es un
#     falso positivo de una regla conservadora, y la respuesta es
#     poner la lista donde le corresponde —es un dato sobre
#     produccion— en vez de relajar la regla.
#
#     Solo puede ENCOGER: el dia que se arregle otro, se marca
#     ARREGLADO aqui y la guardia lo cuenta.
LIBROS_QUE_LA_VERJA_TOCABA = {
    "data/trading/libro_del_escaparate.jsonl": (
        "ARREGLADO el 17/09: ahora exige que la foto sea de este "
        "reset."
    ),
    "data/solvency/bitacora_del_saldo.jsonl": (
        "+1 linea por vuelta de verja, con el saldo del 13/09 y la "
        "fecha de hoy. De las 11 lineas fechadas el 17/09, las 11 "
        "llevan los numeros del 13/09."
    ),
    "data/intelligence/marcador.json": (
        "se reescribe entero; el 17/09 paso de 1.538 a 1.524 "
        "lineas, o sea que ENCOGIO."
    ),
    "data/intelligence/libro_de_publicacion.jsonl": (
        "+1 linea y `last_seen` con la fecha de hoy."
    ),
    "data/rival_intelligence/board_events.json": (
        "crece por vuelta; el 17/09, +1.119 lineas."
    ),
}


PENDIENTES_DE_ARREGLAR = tuple(
    ruta
    for ruta, que in sorted(LIBROS_QUE_LA_VERJA_TOCABA.items())
    if not que.startswith("ARREGLADO")
)


DIRECCIONES = ("SUBIA", "PLANO", "BAJABA")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def esta_encendido() -> bool:
    return bool(ENCENDIDO)


def _miles(valor) -> str:
    return f"{safe_int(valor):,}".replace(",", ".")


# ============================================================
# LAS TRES PIEZAS
# ============================================================


def deriva_esperada(direccion, horizonte: int = HORIZONTE_DIAS) -> dict:
    """
    Lo que hara el precio en `horizonte` dias, segun lo que hizo
    la vispera.

    Sin direccion conocida NO se devuelve la media de las tres:
    se devuelve que no se sabe. La media de +7,43 y −11,71 no
    describe a nadie.
    """

    clave = str(direccion or "").upper()

    if clave not in DERIVA:
        return {
            "available": False,
            "direccion": direccion,
            "percent": None,
            "n": 0,
            "reason": (
                "Sin saber que hizo el precio la vispera no hay "
                "deriva que esperar. La media de las tres "
                "direcciones no describe a ningun jugador: son "
                "+7,43 % y −11,71 % a diez dias."
            ),
        }

    tabla = DERIVA[clave]

    plazo = min(tabla, key=lambda h: abs(h - int(horizonte)))

    valor, n = tabla[plazo]

    return {
        "available": True,
        "direccion": clave,
        "horizonte_pedido": int(horizonte),
        "horizonte_usado": plazo,
        "percent": valor,
        "n": n,
        "fuente": DERIVA_FUENTE,
        "reason": (
            f"Quien venia {clave.lower()} mueve {valor:+.3f} % en "
            f"{plazo} dias (n={n}, {DERIVA_FUENTE})."
        ),
    }


def tres_piezas(
    precio,
    direccion,
    *,
    horizonte: int = HORIZONTE_DIAS,
    prima_percent: float = PRIMA_DE_COMPRA_PERCENT,
) -> dict:
    """
    Las tres piezas del carry, cada una con su `n`, su plazo y su
    fuente.

    Nunca lanza. Si falta cualquiera de las tres, NO se publica un
    carry: un coste al que le falta una pieza no es un coste, es
    media cuenta.
    """

    try:
        importe = safe_int(precio)

        if importe <= 0:
            return {
                "available": False,
                "reason": "Sin precio no hay carry que calcular.",
            }

        movimiento = deriva_esperada(direccion, horizonte)

        prima = {
            "nombre": "prima de compra",
            "percent": float(prima_percent),
            "euros": round(importe * float(prima_percent) / 100),
            "n": PRIMA_DE_COMPRA_N,
            "plazo": "al entrar",
            "fuente": PRIMA_DE_COMPRA_FUENTE,
        }

        deriva = {
            "nombre": "deriva del precio",
            # El coste es MENOS lo que sube: si el precio sube, la
            # tenencia te devuelve dinero.
            "percent": (
                -movimiento["percent"]
                if movimiento["available"]
                else None
            ),
            "euros": (
                round(-importe * movimiento["percent"] / 100)
                if movimiento["available"]
                else None
            ),
            "n": movimiento["n"],
            "plazo": (
                f"{movimiento.get('horizonte_usado')} dias"
                if movimiento["available"]
                else None
            ),
            "fuente": DERIVA_FUENTE,
            "direccion": movimiento["direccion"],
        }

        # Lo que ese dinero habria rendido en otro sitio, POR LAS
        # VECES QUE DE VERDAD LO HABRIAMOS USADO.
        oportunidad_percent = (
            RENDIMIENTO_DE_UN_VIAJE_PERCENT * PARTICIPACION
        )

        oportunidad = {
            "nombre": "coste de oportunidad",
            "percent": round(oportunidad_percent, 4),
            "euros": round(importe * oportunidad_percent / 100),
            "n": min(VIAJES_N, PARTICIPACION_N),
            "n_viajes": VIAJES_N,
            "n_subastas": PARTICIPACION_N,
            "plazo": f"{horizonte} dias",
            "fuente": OPORTUNIDAD_FUENTE,
        }

        piezas = {
            "prima": prima,
            "deriva": deriva,
            "oportunidad": oportunidad,
        }

        if not movimiento["available"]:
            return {
                "available": False,
                "piezas": piezas,
                "reason": (
                    "Falta la deriva: " + movimiento["reason"]
                ),
            }

        total_percent = (
            prima["percent"]
            + deriva["percent"]
            + oportunidad["percent"]
        )

        return {
            "available": True,
            "precio": importe,
            "horizonte_dias": int(horizonte),
            "horizonte_fuente": HORIZONTE_FUENTE,

            "piezas": piezas,

            "carry_percent": round(total_percent, 4),
            "carry_euros": round(importe * total_percent / 100),

            # EL SIGNO, DICHO CON PALABRAS. Un carry negativo
            # significa que tener al jugador PAGA, y eso es tan
            # raro que conviene que no se lea de un vistazo al
            # reves.
            "paga": total_percent < 0,

            "reason": (
                f"Tener a un jugador de {_miles(importe)} EUR que "
                f"venia {deriva['direccion'].lower()} durante "
                f"{horizonte} dias "
                + (
                    f"DEVUELVE {_miles(abs(round(importe * total_percent / 100)))} EUR "
                    f"({total_percent:+.3f} %)"
                    if total_percent < 0
                    else f"cuesta "
                    f"{_miles(round(importe * total_percent / 100))} EUR "
                    f"({total_percent:+.3f} %)"
                )
                + f": prima {prima['percent']:+.3f} %, deriva "
                f"{deriva['percent']:+.3f} %, oportunidad "
                f"{oportunidad['percent']:+.3f} %."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo calcular el carry: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 2 — LA FORMULA
# ============================================================


def coste_de_fichar(
    precio,
    direccion,
    *,
    horizonte: int = HORIZONTE_DIAS,
    tope_de_prima: float | None = TOPE_DE_PRIMA_DE_FICHAJE,
) -> dict:
    """
    Lo que cuesta de verdad fichar, y CON QUE TOPE.

    LAS DOS COSAS VAN EN LA MISMA FUNCION A PROPOSITO (doctrina
    69). Esta semana un freno se ha quedado huerfano cuatro veces
    al mover un valor. Si el coste baja y el tope no viaja con el,
    `optimal_bid` puja hasta el valor porque hoy la via del once
    NO tiene tope de prima.

    `tope_de_prima=None` es el comportamiento de hoy, y se
    devuelve marcado `sin_tope` para que quien lo vea sepa lo que
    esta pidiendo. Hay guardia que exige que la via de fichaje
    nunca salga sin tope.

    Nunca lanza.
    """

    try:
        importe = safe_int(precio)

        carry = tres_piezas(
            importe, direccion, horizonte=horizonte
        )

        if not carry.get("available"):
            return {
                "available": False,
                "tope_de_prima": tope_de_prima,
                "sin_tope": tope_de_prima is None,
                "reason": carry.get("reason"),
            }

        techo = (
            round(importe * (1 + float(tope_de_prima)))
            if tope_de_prima is not None
            else None
        )

        return {
            "available": True,
            "precio": importe,

            "coste_viejo": importe,
            "coste_nuevo": carry["carry_euros"],
            "ahorro": importe - carry["carry_euros"],

            "carry": carry,

            # EL TOPE, EN LA MISMA RESPUESTA QUE EL COSTE.
            "tope_de_prima": tope_de_prima,
            "tope_de_prima_euros": techo,
            "sin_tope": tope_de_prima is None,
            "tope_fuente": (
                "PRIMA_MAXIMA_DE_PUJA, el mismo +0,25 % que ya "
                "aplica a la otra via. No es un umbral nuevo."
            ),

            "reason": (
                f"El coste viejo son los {_miles(importe)} EUR "
                f"enteros. El carry a {horizonte} dias son "
                f"{_miles(carry['carry_euros'])} EUR "
                f"({carry['carry_percent']:+.3f} %). "
                + (
                    f"Y la puja no pasa de {_miles(techo)} EUR "
                    f"(+{float(tope_de_prima) * 100:.2f} % sobre el "
                    f"precio)."
                    if techo is not None
                    else "Y SIN TOPE DE PRIMA: asi no se escribe."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "tope_de_prima": tope_de_prima,
            "sin_tope": tope_de_prima is None,
            "reason": (
                f"No se pudo calcular el coste de fichar: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 3 — QUE CAMBIA
# ============================================================


def que_cambia(
    candidatos: list | None,
    *,
    horizonte: int = HORIZONTE_DIAS,
    bolsillo_de_fichar: int = 0,
    techo_de_biwenger: int = 0,
) -> dict:
    """
    Cuantos candidatos pasarian de la puerta con el carry en vez
    del importe entero, y cuanto mas se podria gastar.

    Cada fila: `name`, `market_price`, `xi_value` y `direccion`
    -lo que hizo su precio la vispera-.

    LA PUERTA SIGUE SIENDO LA MISMA: el valor como fichaje tiene
    que superar al COSTE. Lo unico que cambia es que el coste deja
    de ser el importe entero.

    Nunca lanza. Con la lista vacia no publica ceros.
    """

    try:
        filas = [c for c in (candidatos or []) if isinstance(c, dict)]

        if not filas:
            return {
                "available": False,
                "n": 0,
                "pasan_ahora": 0,
                "pasarian": 0,
                "reason": (
                    "La lista de candidatos llega vacia: no hay nada "
                    "que comparar."
                ),
            }

        ahora = []
        despues = []
        sin_direccion = []

        for fila in filas:

            precio = safe_int(fila.get("market_price"))

            valor = safe_int(fila.get("xi_value"))

            if precio <= 0:
                continue

            if valor > precio:
                ahora.append({**fila, "coste": precio})
                continue

            coste = coste_de_fichar(
                precio, fila.get("direccion"), horizonte=horizonte
            )

            if not coste.get("available"):
                sin_direccion.append(
                    {**fila, "reason": coste.get("reason")}
                )
                continue

            # La via del once tiene que haberle dado valor. Si le
            # dio cero, abaratar el coste no lo convierte en
            # fichaje.
            if valor > 0 and valor > coste["coste_nuevo"]:
                despues.append(
                    {
                        **fila,
                        "coste": coste["coste_nuevo"],
                        "carry_percent": coste["carry"]["carry_percent"],
                        "margen": valor - coste["coste_nuevo"],
                        "tope_euros": coste["tope_de_prima_euros"],
                    }
                )

        # EL PEOR CASO. Con el tope puesto, una puja no pasa de
        # `precio x (1 + tope)`, y ademas la limitan el bolsillo y
        # el techo de Biwenger.
        def tope(item):
            return min(
                safe_int(
                    item.get("tope_euros")
                    or item.get("market_price")
                ),
                safe_int(bolsillo_de_fichar) or 10**15,
                safe_int(techo_de_biwenger) or 10**15,
            )

        peor_hoy = max((tope(i) for i in ahora), default=0)

        peor_despues = max(
            (tope(i) for i in ahora + despues), default=0
        )

        return {
            "available": True,
            "n": len(filas),
            "horizonte_dias": int(horizonte),

            "pasan_ahora": len(ahora),
            "pasarian": len(despues),
            "sin_direccion": len(sin_direccion),

            "los_que_pasarian": sorted(
                despues, key=lambda f: -f["margen"]
            ),

            "peor_caso_hoy": peor_hoy,
            "peor_caso_con_carry": peor_despues,
            "cuanto_mas": peor_despues - peor_hoy,

            "reason": (
                f"De {len(filas)} candidatos, {len(ahora)} pasan hoy "
                f"y {len(despues)} mas pasarian con el carry a "
                f"{horizonte} dias. "
                + (
                    f"{len(sin_direccion)} no se pueden juzgar: no "
                    f"se sabe que hizo su precio la vispera."
                    if sin_direccion
                    else ""
                )
                + f" La operacion mas grande pasaria de "
                f"{_miles(peor_hoy)} a {_miles(peor_despues)} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "pasan_ahora": 0,
            "pasarian": 0,
            "reason": (
                f"No se pudo medir que cambia: "
                f"{type(error).__name__}: {error}"
            ),
        }
