"""
Estar a las siete menos cinco: pujar por varios en la misma ventana.

LO QUE FALTABA

    Las pujas se resuelven en el reset de las 07:00. Pepe hoy
    pone -como mucho- UNA accion por vuelta, y la ultima vuelta
    antes del reset le pillaba a 53 minutos del cierre.

    El dueño lo dijo asi: "si cinco minutos antes entro y le meto
    una puja, me lo puedo llevar".

LO QUE DICE LA MEDICION, QUE NO ES LO MISMO (10/09/2026)

    Sobre las 156 compras al Computer del tablon, en 27 dias:

        43 % se llevaron SIN NINGUN RIVAL        (67 de 156)
        de esos, solo el 29 % venia subiendo     (16 de 55)
        -> 0,59 jugadores al dia sin competencia Y subiendo

    No son seis cada mañana: es uno cada dos dias. Y no son
    baratos: precio mediano 4.550.000, y solo 2 de 16 caben en
    el tope por operacion de la via especulativa.

    PERO el premio no es el que parecia, y es mejor de lo que
    parece:

        estar solo   prima mediana  +1,33 %
        con rivales  prima mediana  +8,30 %

    Siete puntos de diferencia. Sobre un jugador de 4,5 M eso son
    ~318.000 EUR por operacion. El negocio no es el que sube
    20.000 al dia: es NO PAGAR la prima de la puja disputada.

QUE HACE ESTE MODULO

    Elige el CONJUNTO que mas gana con el dinero y las fichas que
    hay, no una puja detras de otra. Lo que ata a los candidatos
    entre si es el presupuesto y los huecos, no su calidad.

    Y comprueba las barandillas sobre el PEOR CASO: que se ganen
    todas. Mirarlas una por una es como comprobar que cada bala
    pesa poco.

FASE OBSERVADOR

    Calcula y publica. No puja, no compra y no mueve ningun
    liston. Ningun motor lee esto todavia.
"""

from __future__ import annotations


# ============================================================
# LA VENTANA
# ============================================================
#
#     Cuanto antes del reset se abre la puja multiple. El resto
#     del dia, una accion por vuelta como siempre.
#
#     Quince minutos y no cinco: el cron de GitHub Actions se
#     retrasa con frecuencia -a veces diez minutos-, y una
#     ventana de cinco minutos se pierde entera con un retraso
#     normal. Ver el informe.
#
#     AMPLIADA A 135 EL 10/09/2026, Y POR QUE
#
#         Con quince minutos la ventana era 06:45-07:00 de
#         Madrid, y el disparo externo NO ENTRABA:
#
#             cron a 04:45 Madrid  ->  135 min al reset
#             cron a 04:50 Madrid  ->  130 min
#             y si cron-job.org aplica CET -medido el 10/09-,
#             dispara a 05:45 y 05:50: 75 y 70 min.
#
#         Las cuatro fuera. Manana no se habria pujado ni
#         renovado, y el plan habria dicho FUERA_DE_VENTANA,
#         que es lo mismo que dice el resto del dia:
#         indistinguible de una noche normal.
#
#         135 minutos -04:45 a 07:00- cubren las dos lecturas
#         del reloj con un solo numero. Deja de depender de
#         acertar la zona horaria de un tercero.
#
#         Y NO CUESTA CASI NADA pujar antes: los precios no se
#         mueven hasta el reset y las pujas de los rivales son
#         invisibles. La asimetria manda: llegar tarde cuesta la
#         ventana entera; llegar pronto, informacion, y poca.
#
#         VA ATADO a `zona_de_silencio.SILENCIO_DESDE`, que se
#         movio a las 04:45 en el mismo cambio. Ampliar la
#         ventana sin mover el silencio dejaria 04:45-05:00 sin
#         vigilar, y ahi una vuelta `schedule` que llegue tarde
#         escribiria de verdad. Medido antes de tocarlo.
VENTANA_MINUTOS = 135


# ============================================================
# EL TOPE DE LA VENTANA, QUE SALE DE UNA CUENTA
# ============================================================
#
#     La unica forma real de hacernos daño con esto es tener
#     varias posiciones en rojo a la vez con una fecha limite
#     encima: el viernes hay que estar en positivo.
#
#     Asi que el tope es lo que se pueda DESHACER el viernes
#     aunque el mercado haya caido un 5 %.
#
#     LA CUENTA
#
#         Si se compra con deuda D y el mercado cae un `CAIDA`,
#         al vender se recupera D * (1 - CAIDA). Falta
#         D * CAIDA, y eso tiene que salir de la caja libre.
#
#             D * CAIDA <= caja_libre
#             D <= caja_libre / CAIDA
#
#     No es un umbral: es el resultado de esa division. Si la
#     caja sube, el tope sube solo.
CAIDA_QUE_HAY_QUE_AGUANTAR = 0.05


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _euros(valor) -> str:
    """
    Un numero con puntos de millar, y NADA MAS.

    Existe para que nadie vuelva a hacer
    `f"frase, {n:,}".replace(",", ".")`, que se come las comas
    de la frase.
    """

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"


def ventana_abierta(
    seconds_to_reset,
    ventana_minutos: int = VENTANA_MINUTOS,
) -> dict:
    """
    Si estamos en la ventana del reset.

    `seconds_to_reset` lo publica `market_clock`. NO se lee el
    reloj aqui: se recibe. Forma fija, nunca lanza.
    """

    vacio = {
        "abierta": False,
        "seconds_to_reset": None,
        "minutes_to_reset": None,
        "window_minutes": ventana_minutos,
        "reason": None,
    }

    try:
        segundos = seconds_to_reset

        if segundos is None:
            return {
                **vacio,
                "reason": (
                    "El reloj del mercado no sabe cuando es el "
                    "reset: la ventana no se abre."
                ),
            }

        segundos = safe_int(segundos)

        minutos = segundos / 60.0

        abierta = 0 < segundos <= ventana_minutos * 60

        return {
            "abierta": bool(abierta),
            "seconds_to_reset": segundos,
            "minutes_to_reset": round(minutos, 1),
            "window_minutes": ventana_minutos,
            "reason": (
                f"Quedan {minutos:.0f} min para el reset: "
                f"ventana ABIERTA."
                if abierta
                else f"Quedan {minutos:.0f} min para el reset y "
                f"la ventana son los ultimos "
                f"{ventana_minutos}: una accion por vuelta."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar la ventana: "
                f"{type(error).__name__}: {error}"
            ),
        }


def tope_de_la_ventana(
    caja_libre,
    presupuesto,
    caida=CAIDA_QUE_HAY_QUE_AGUANTAR,
) -> dict:
    """
    Cuanto se puede comprometer en una ventana.

    Forma fija. Nunca lanza. Ver la cabecera para la cuenta.
    """

    vacio = {
        "tope": 0,
        "por_la_caida": 0,
        "por_el_presupuesto": 0,
        "manda": None,
        "caida": caida,
        "reason": None,
    }

    try:
        caja = max(0, safe_int(caja_libre))
        bolsa = max(0, safe_int(presupuesto))

        fraccion = safe_float(caida)

        if fraccion <= 0:
            return {
                **vacio,
                "por_el_presupuesto": bolsa,
                "tope": bolsa,
                "manda": "PRESUPUESTO",
                "reason": (
                    "Sin caida que aguantar, solo manda el "
                    "presupuesto."
                ),
            }

        por_la_caida = int(caja / fraccion)

        tope = min(bolsa, por_la_caida)

        manda = (
            "CAIDA_DEL_MERCADO"
            if por_la_caida < bolsa
            else "PRESUPUESTO"
        )

        return {
            "tope": tope,
            "por_la_caida": por_la_caida,
            "por_el_presupuesto": bolsa,
            "manda": manda,
            "caida": fraccion,
            # CADA NUMERO POR SEPARADO (10/09/2026)
            #
            #     `.replace(",", ".")` sobre la frase ENTERA se
            #     come las comas de la prosa: "caja libre. una
            #     caida". Es la quinta vez que pasa en este
            #     proyecto, asi que los numeros se formatean uno
            #     a uno y la frase no se toca.
            "reason": (
                f"Con {_euros(caja)} EUR de caja libre, una "
                f"caida del {100 * fraccion:.0f} % sobre "
                f"{_euros(por_la_caida)} se cubre justo. El "
                f"presupuesto da {_euros(bolsa)}. Manda "
                f"{manda.replace('_', ' ').lower()}: "
                f"{_euros(tope)} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el tope: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# LA CURVA DE LA PRIMA (11/09/2026)
# ============================================================
#
#     LA PREGUNTA
#
#         Si pujas `precio + 1` ganas solo lo que nadie mira. Si
#         pujas `precio x 1,03` ganas alguno disputado pero pagas
#         la prima en TODOS, incluidos los que habrias ganado por
#         un euro.
#
#         Con las 156 subastas del tablon -que traen la puja
#         ganadora- se puede contestar de verdad: para cada
#         importe, cuantas habrias ganado y cuanto habrias pagado.
#
#     POR QUE PERDER NO CUESTA
#
#         Medido el 16/08: al pujar, el balance NO se mueve;
#         baja `maximumBid` hasta el reset. Una puja perdida no
#         cuesta un euro, solo capacidad durante unas horas.
#
#         Por eso la cuenta neta solo suma las ganadas.
#
#     LA CUENTA DE CADA OPERACION
#
#         Se compra a `precio x (1 + m)` y el Computer recompra a
#         `precio x (1 + prima_de_reventa)`. El resultado, antes
#         de que el jugador se mueva, es:
#
#             precio x (prima_de_reventa - m)
#
#         Con la prima de reventa medida por produccion sobre 107
#         ventas -+1,8 %-, cualquier `m` por encima de eso entra
#         en perdidas el mismo dia de la compra. La subida del
#         jugador es la propina, no el negocio.
IMPORTES_A_PROBAR = (
    0.0,
    0.0025,
    0.005,
    0.01,
    0.015,
    0.02,
    0.03,
    0.05,
    0.08,
)


def curva_de_la_prima(
    subastas: list | None,
    prima_de_reventa: float,
    importes=IMPORTES_A_PROBAR,
) -> dict:
    """
    Para cada importe, cuantas se ganan y cuanto se paga.

    Cada subasta necesita `precio` -el de mercado de ese dia- y
    `pagado` -la puja ganadora-. Se gana si nuestra puja SUPERA
    a la ganadora.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "filas": [],
        "mejor": None,
        "subastas": 0,
        "resale_premium": prima_de_reventa,
        "reason": None,
    }

    try:
        utiles = [
            s
            for s in (subastas or [])
            if isinstance(s, dict)
            and safe_int(s.get("precio")) > 0
            and safe_int(s.get("pagado")) > 0
        ]

        if not utiles:
            return {
                **vacio,
                "reason": (
                    "Ninguna subasta con precio y puja ganadora."
                ),
            }

        reventa = safe_float(prima_de_reventa)

        filas = []

        for m in importes:

            ganadas = 0
            prima_pagada = 0
            neto = 0

            for subasta in utiles:

                precio = safe_int(subasta.get("precio"))

                # `+1` porque para ganar hay que SUPERAR, no
                # igualar.
                nuestra = int(precio * (1 + m)) + 1

                if nuestra <= safe_int(subasta.get("pagado")):
                    continue

                ganadas += 1

                prima_pagada += nuestra - precio

                neto += int(
                    precio * (1 + reventa)
                ) - nuestra

            filas.append({
                "importe_percent": round(100 * m, 3),
                "ganadas": ganadas,
                "de": len(utiles),
                "ganadas_percent": round(
                    100 * ganadas / len(utiles), 1
                ),
                "prima_pagada": prima_pagada,
                "neto": neto,
                "neto_por_ganada": (
                    int(neto / ganadas) if ganadas else 0
                ),
            })

        mejor = max(filas, key=lambda f: f["neto"])

        return {
            "available": True,
            "filas": filas,
            "mejor": mejor,
            "subastas": len(utiles),
            "resale_premium": reventa,
            "reason": (
                f"Sobre {len(utiles)} subastas, el importe que "
                f"mas gana es precio + "
                f"{mejor['importe_percent']:.2f} %: se llevaria "
                f"{mejor['ganadas']} ({mejor['ganadas_percent']} "
                f"%) con un neto de {_euros(mejor['neto'])} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo trazar la curva: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# LOS DOS MODOS (11/09/2026)
# ============================================================
#
#     `optimal_bid` busca el importe que maximiza
#     `P(ganar) x (valor - puja)`. Para subir `P(ganar)` sube la
#     oferta, y eso es CORRECTO cuando solo se puede tirar una
#     vez: una operacion grande, o el jugador concreto que hace
#     falta para el once.
#
#     Pero en la subasta del reset:
#
#         perder no cuesta nada -el balance no se mueve, solo
#         baja `maximumBid` hasta el reset-;
#         hay veinte jugadores cada mañana, no uno;
#         y el 43 % no tiene ningun rival.
#
#     Con tiros gratis y muchos candidatos, lo que hay que
#     maximizar es la SUMA de las ganancias de la ventana, no la
#     de una puja. Y eso se hace pujando bajo por muchos: te
#     llevas los que nadie queria y pierdes gratis los
#     disputados.
#
#     `optimal_bid` NO se toca. Lo que cambia es que se elige
#     entre dos modos, y cada puja publica cual la decidio.
MODO_UN_DISPARO = "UN_DISPARO"

MODO_CARTERA = "CARTERA"


# El importe de la puja baja, en tanto por uno sobre el precio.
#
# MEDIDO, NO ELEGIDO (11/09/2026)
#
#     Sobre las 115 subastas del tablon con precio de
#     referencia, probando cada importe posible y contando que
#     perder no cuesta:
#
#         +0,00 %   gana 30   neto  2.376.870
#         +0,25 %   gana 34   neto  2.654.961   <- maximo
#         +0,50 %   gana 35   neto  2.325.829
#         +1,00 %   gana 35   neto  1.431.245
#         +2,00 %   gana 46   neto   -430.126
#         +8,00 %   gana 71   neto -18.540.551
#
#     Subir del 0,25 % al 8 % compra 37 jugadores mas y cuesta
#     21 millones: cada uno de esos 37 sale por mas de lo que
#     vale.
#
#     El punto de equilibrio esta en la prima que paga el
#     Computer al recomprar -+1,8 % medido sobre 107 ventas-, que
#     es exactamente lo que dice la teoria.
IMPORTE_DE_CARTERA = 0.0025


def puja_de_cartera(precio, importe=IMPORTE_DE_CARTERA) -> int:
    """
    Lo que se ofrece en modo cartera: el precio y un pelo.

    `+1` porque para ganar hay que SUPERAR la mejor puja, no
    igualarla.
    """

    valor = safe_int(precio)

    if valor <= 0:
        return 0

    return int(valor * (1 + safe_float(importe))) + 1


# ============================================================
# LA CESTA NO OPERA ARRIBA DEL SUELO (20/09/2026)
# ============================================================
#
#     DECISION DEL DUEÑO, con el motivo escrito porque importa
#     mas que la decision.
#
#     Medido sobre las 23 operaciones CERRADAS de la temporada,
#     por tramo del precio de COMPRA y vendiendo al Computer:
#
#         suelo (<300 k)   n= 8   +1,51 %   100 % verde     +28.867
#         300 k - 1,5 M    n= 4   -1,50 %    25 %          +109.399
#         1,5 M - 3 M      n= 9   -2,57 %    33 %        -1.038.783
#         >= 3 M           n= 0        -        -                 -
#
#     Nueve operaciones y un millon perdido por encima de
#     1.500.000, con un tercio en verde. Abajo, ocho de ocho en
#     verde.
#
#     Y el tramo de en medio sale positivo SOLO por las dos
#     ventas a managers que cayeron ahi. Quitadas, pierde.
#
#     EL CORTE NO ES UN NUMERO NUEVO (doctrina 84)
#
#         Es `CORTES_DE_PRECIO[0]`, el mismo 1.500.000 que ya
#         parte la rejilla de la pelea y la de la prima. Tres
#         cosas del mismo eje con el mismo corte, o seria una
#         arbitrariedad escondida.
#
#     CERRAR NO ES BORRAR
#
#         La cesta sigue viva DEBAJO, que es donde gana. Lo que
#         se cierra es comprar para revender por encima del
#         corte — no comprar por encima del corte: esa via es el
#         tablero de fichajes, y no se toca.
#
#     NINGUNA CELDA LLEGA A `MIN_SAMPLES` = 12. Por eso el corte
#     va detras de un interruptor y lo enciende el dueño.
ENV_SOLO_EL_SUELO = "BORDALAS_CESTA_SOLO_EL_SUELO"


def solo_el_suelo() -> bool:
    """Si la cesta solo opera por debajo del corte. Nunca lanza."""

    import os

    return str(
        os.environ.get(ENV_SOLO_EL_SUELO, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def _techo_de_la_cesta() -> int:
    """El corte, del sitio donde ya vivia."""

    return safe_int(CORTES_DE_PRECIO[0])


def candidatos_en_modo_cartera(
    candidatos: list | None,
    prima_de_reventa: float,
    importe=IMPORTE_DE_CARTERA,

    # LA CURVA DE PRIMAS, APAGADA (20/09/2026)
    #
    #     `prima_de_reventa` es UNA mediana para todos los
    #     precios, y por eso la ganancia sale proporcional al
    #     precio y el rendimiento por euro CONSTANTE: 0,0208 para
    #     un jugador de 150.000 y para uno de 24,9 millones, hasta
    #     el quinto decimal. Doctrina 98: el ratio no delata al
    #     ratio, delata a su entrada.
    #
    #     Medido sobre 194 ventas al Computer, la prima va de
    #     +1,36 % abajo a +4,26 % arriba. `curva` la trae tramo a
    #     tramo.
    #
    #     SE RECIBE, NO SE LEE. Este modulo no abre disco.
    #
    #     Y NO MANDA HASTA QUE EL DUEÑO LA ENCIENDA:
    #     `BORDALAS_PRIMA_POR_TRAMO`. Apagado, el comportamiento
    #     es exactamente el de ayer.
    curva: dict | None = None,
) -> list:
    """
    Los mismos candidatos, con la puja baja y su ganancia.

    LA GANANCIA, SIN ADIVINAR NADA

        Se compra a `precio x (1 + importe)` y el Computer
        recompra a `precio x (1 + prima_de_reventa)`. La
        diferencia es lo que se gana ANTES de que el jugador se
        mueva. La subida es la propina, no el negocio.

    Nunca lanza. Los que no dan ganancia positiva salen con
    `expected_value` 0 y `elegir_la_cesta` los aparta.
    """

    salida = []

    try:
        reventa = safe_float(prima_de_reventa)

        por_tramo = None

        if curva:

            try:
                from src.analysis.computer_resale_premium import (
                    prima_del_tramo,
                    prima_por_tramo_activa,
                )

                if prima_por_tramo_activa():
                    por_tramo = prima_del_tramo

            except Exception:                       # noqa: BLE001
                por_tramo = None

        for candidato in (candidatos or []):

            if not isinstance(candidato, dict):
                continue

            precio = safe_int(candidato.get("market_price"))

            if precio <= 0:
                continue

            # EL SUELO Y NADA MAS, si el dueño lo ha encendido.
            # Ver la cabecera: nueve operaciones y un millon
            # perdido por encima de este corte.
            if solo_el_suelo() and precio >= _techo_de_la_cesta():
                continue

            suya = reventa

            tramo = None

            if por_tramo is not None:

                tramo = por_tramo(curva, precio)

                # Sin numero utilizable NO se inventa: se queda la
                # mediana que llego por la puerta (doctrina 24).
                if tramo.get("percent") is not None:
                    suya = safe_float(tramo["percent"]) / 100.0

            puja = puja_de_cartera(precio, importe)

            ganancia = int(precio * (1 + suya)) - puja

            fila = {
                **candidato,
                "bid": puja,
                "expected_value": max(0, ganancia),
                "modo": MODO_CARTERA,
                "prima_aplicada_percent": round(100 * suya, 4),
                "prima_del_tramo": tramo,
                "bid_reason": (
                    f"Modo cartera: se ofrece el precio "
                    f"+{100 * safe_float(importe):.2f} % "
                    f"({_euros(puja)} EUR sobre "
                    f"{_euros(precio)}). El Computer recompra a "
                    f"+{100 * suya:.1f} %"
                    + (
                        f" ({tramo['etiqueta']}, n={tramo['n']})"
                        if tramo and tramo.get("etiqueta")
                        else ""
                    )
                    + f", asi que la operacion nace con "
                    f"{_euros(ganancia)} EUR de margen. Perder "
                    f"no cuesta nada: solo capacidad hasta el "
                    f"reset."
                ),
            }

            salida.append(fila)

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def comparar_los_dos_modos(
    candidatos: list | None,
    prima_de_reventa: float,
    presupuesto,
    fichas_libres,
    caja_libre=None,
    max_por_club: int | None = None,
    importe=IMPORTE_DE_CARTERA,
) -> dict:
    """
    Lo que ofrece hoy contra lo que ofreceria en modo cartera.

    Los candidatos entran con la puja que YA trae cada uno -la de
    `optimal_bid`- y se comparan con la misma lista pujada bajo.

    Forma fija. Nunca lanza. No ejecuta nada.
    """

    vacio = {
        "available": False,
        "observer_only": True,
        "enabled": False,
        "un_disparo": None,
        "cartera": None,
        "resale_premium": prima_de_reventa,
        "importe_de_cartera": importe,
        "reason": None,
    }

    try:
        marcados = [
            {**c, "modo": MODO_UN_DISPARO}
            for c in (candidatos or [])
            if isinstance(c, dict)
        ]

        hoy = elegir_la_cesta(
            marcados,
            presupuesto=presupuesto,
            fichas_libres=fichas_libres,
            caja_libre=caja_libre,
            max_por_club=max_por_club,
        )

        cartera = elegir_la_cesta(
            candidatos_en_modo_cartera(
                candidatos, prima_de_reventa, importe
            ),
            presupuesto=presupuesto,
            fichas_libres=fichas_libres,
            caja_libre=caja_libre,
            max_por_club=max_por_club,
        )

        return {
            "available": True,
            "observer_only": True,
            "enabled": False,
            "un_disparo": hoy,
            "cartera": cartera,
            "resale_premium": prima_de_reventa,
            "importe_de_cartera": importe,
            "reason": (
                f"Hoy: {len(hoy.get('elegidos') or [])} puja(s) "
                f"por {_euros(hoy.get('comprometido'))} EUR. "
                f"Modo cartera: "
                f"{len(cartera.get('elegidos') or [])} puja(s) "
                f"por {_euros(cartera.get('comprometido'))} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudieron comparar los modos: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# LA PELEA, COMO COSTE (09/09/2026)
# ============================================================
#
#     LO QUE SE MIDIO SOBRE LAS 156 SUBASTAS DEL TABLON
#
#     Que porcentaje acabo DISPUTADO -con al menos un rival-,
#     cruzando precio y subida del dia anterior:
#
#                        CAE O PLANO    SUBE >= 1 %
#         barato < 1,5 M     54 %           83 %
#         medio 1,5-3 M      39 %           64 %
#         caro >= 3 M        22 %           67 %
#
#     Subir cuesta unos 30 puntos de pelea. Ser caro ahorra
#     otros 30. Y las dos cosas actuan en todos los niveles de
#     la otra.
#
#     LA IRONIA QUE LO EXPLICA
#
#         La señal que nos hace fijarnos en alguien —que esta
#         subiendo— es la misma que hace que se fijen los demas.
#         No competimos por casualidad: competimos porque
#         miramos donde mira todo el mundo.
#
#     POR QUE ESTO ES UN COSTE Y NO UN DETALLE
#
#         Gastar una ficha en alguien que se perdera el 83 % de
#         las veces es tirar capacidad. Y la capacidad es lo
#         escaso: hoy hay siete fichas libres.
#
#         Pujando bajo -al +0,25 %- se gana practicamente lo que
#         nadie disputa y poco mas: sobre las 115 subastas con
#         precio, ese importe se llevo 34, y sin rival habia 67
#         de 156. Asi que:
#
#             P(llevarselo) ~= 1 - P(disputada)
#
#         Es una aproximacion, y se dice: quien puja bajo puede
#         ganar alguna disputada por suerte, y perder alguna
#         tranquila si aparece alguien nuevo.
#
#     MUESTRA
#
#         Las celdas van con su `n`. La de "caro y subiendo"
#         tiene 6 casos y no manda nada: se publica y se marca.
CORTES_DE_PRECIO = (1_500_000, 3_000_000)

SUBIDA_QUE_LLAMA_LA_ATENCION = 1.0


# `(precio_bajo, precio_alto, sube, probabilidad, n)`.
# `precio_alto` None es "sin techo"; `sube` es si venia subiendo
# por encima de `SUBIDA_QUE_LLAMA_LA_ATENCION`.
PELEA_MEDIDA = (
    (None, 1_500_000, False, 0.54, 24),
    (None, 1_500_000, True, 0.83, 12),
    (1_500_000, 3_000_000, False, 0.39, 18),
    (1_500_000, 3_000_000, True, 0.64, 11),
    (3_000_000, None, False, 0.22, 32),
    (3_000_000, None, True, 0.67, 6),
)


# Por debajo de esto la celda se publica pero se marca: un 67 %
# de seis casos no es un 67 %.
MUESTRA_QUE_MANDA = 10


def probabilidad_de_pelea(
    precio,
    subida_percent=None,
) -> dict:
    """
    Que probabilidad hay de que este jugador salga disputado.

    `{probabilidad, celda, n, fiable, reason}`. Forma fija,
    nunca lanza.

    Sin subida conocida se usa la fila de "cae o plano", que es
    la conservadora: supone menos pelea, asi que si nos
    equivocamos sera contando de menos el coste — y eso se ve en
    el libro de aciertos, no en una sorpresa.
    """

    vacio = {
        "probabilidad": None,
        "celda": None,
        "n": 0,
        "fiable": False,
        "reason": None,
    }

    try:
        valor = safe_int(precio)

        if valor <= 0:
            return {
                **vacio,
                "reason": (
                    "Sin precio no se puede decir si atraera "
                    "pelea."
                ),
            }

        sube = (
            safe_float(subida_percent, 0.0)
            >= SUBIDA_QUE_LLAMA_LA_ATENCION
            if subida_percent is not None
            else False
        )

        for bajo, alto, subiendo, probabilidad, n in (
            PELEA_MEDIDA
        ):

            if subiendo != sube:
                continue

            if bajo is not None and valor < bajo:
                continue

            if alto is not None and valor >= alto:
                continue

            tramo = (
                f"< {_euros(alto)}"
                if bajo is None
                else f">= {_euros(bajo)}"
                if alto is None
                else f"{_euros(bajo)} a {_euros(alto)}"
            )

            return {
                "probabilidad": probabilidad,
                "celda": (
                    f"{tramo}, "
                    f"{'subiendo' if sube else 'cae o plano'}"
                ),
                "n": n,
                "fiable": n >= MUESTRA_QUE_MANDA,
                "reason": (
                    f"{100 * probabilidad:.0f} % de subastas "
                    f"disputadas en «{tramo}, "
                    f"{'subiendo' if sube else 'cae o plano'}» "
                    f"sobre {n} casos"
                    + (
                        ""
                        if n >= MUESTRA_QUE_MANDA
                        else " (muestra corta: se publica, no "
                        "manda)"
                    )
                ),
            }

        return {
            **vacio,
            "reason": (
                f"{_euros(valor)} no cae en ninguna celda "
                f"medida."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo estimar la pelea: "
                f"{type(error).__name__}: {error}"
            ),
        }


def probabilidad_de_llevarselo(
    precio,
    subida_percent=None,
) -> dict:
    """
    `1 - P(disputada)`, con la aproximacion escrita arriba.

    Sin celda medida devuelve `None`, no un 1: dar por hecho que
    se gana lo que no se ha medido es exactamente como se
    inventa una ventaja.
    """

    pelea = probabilidad_de_pelea(precio, subida_percent)

    if pelea["probabilidad"] is None:
        return {**pelea, "probabilidad": None}

    return {
        **pelea,
        "probabilidad": round(1 - pelea["probabilidad"], 4),
        "reason": (
            f"Se lo llevaria el "
            f"{100 * (1 - pelea['probabilidad']):.0f} % de las "
            f"veces: " + str(pelea["reason"])
        ),
    }


def _por_euro(
    candidato: dict, contar_la_pelea: bool = False
) -> float:
    """
    Ganancia esperada por euro comprometido.

    Es lo que ordena la cesta: con dinero limitado, lo que
    importa no es cual gana mas, sino cual gana mas POR EURO
    inmovilizado.

    Con `contar_la_pelea`, se multiplica por la probabilidad de
    llevarselo: una ficha gastada en alguien que se pierde el
    83 % de las veces es capacidad tirada.

    Sin probabilidad medida NO se penaliza: se ordena como
    antes. Castigar lo que no se ha medido es inventarse un
    coste.
    """

    puja = safe_int(candidato.get("bid"))

    if puja <= 0:
        return -1.0

    ganancia = safe_float(candidato.get("expected_value"))

    if contar_la_pelea:

        odds = candidato.get("win_odds")

        if odds is not None:
            ganancia *= safe_float(odds, 1.0)

    return ganancia / puja


def elegir_la_cesta(
    candidatos: list | None,
    presupuesto,
    fichas_libres,
    caja_libre=None,
    max_por_club: int | None = None,

    # LA PELEA COMO COSTE. ENCENDIDO el 09/09/2026.
    #
    #     Se publico apagado un dia y se midio en euros sobre el
    #     escaparate real. Gana en las dos dimensiones:
    #
    #                          SIN la pelea   CON la pelea
    #         pujas                    7            4
    #         compromete       1.964.907    2.375.929
    #         si gana todas       30.373       36.731
    #         ESPERADO            13.972       20.918
    #         por ficha            1.996        5.230
    #
    #     Un 50 % mas de euros esperados usando TRES FICHAS
    #     MENOS, y 2,6 veces mejor por ficha ocupada.
    #
    #     Lo unico que cuesta es comprometer 411.022 mas de
    #     capacidad — que no es dinero gastado, porque perder no
    #     cuesta nada, y se libera en el reset.
    #
    #     Y no mueve ningun umbral: es un ORDEN. Con `False`
    #     vuelve el de antes.
    contar_la_pelea: bool = True,
) -> dict:
    """
    El conjunto por el que se pujaria en esta ventana.

    LA REGLA

        Por ganancia esperada POR EURO comprometido, llenando
        hasta agotar el tope o las fichas.

    LAS BARANDILLAS, SOBRE EL PEOR CASO

        Nunca mas pujas que fichas libres: si se ganaran todas
        no cabrian, y `0.3` -que pasa si ganas mas de las que
        caben- no se ha podido comprobar sin arriesgar.

        Y como mucho `max_por_club` del mismo equipo CONTANDO
        la cesta entera, no cada puja por separado.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "observer_only": True,
        "elegidos": [],
        "descartados": [],
        "comprometido": 0,
        "fichas_usadas": 0,
        "fichas_libres": safe_int(fichas_libres),
        "tope": None,
        "reason": None,
    }

    try:
        huecos = max(0, safe_int(fichas_libres))

        limite = tope_de_la_ventana(
            caja_libre
            if caja_libre is not None
            else presupuesto,
            presupuesto,
        )

        if huecos <= 0:
            return {
                **vacio,
                "available": True,
                "tope": limite,
                "reason": (
                    "Sin fichas libres no se puja por nadie: "
                    "ganar sin sitio donde ponerlo no se ha "
                    "podido comprobar y no se prueba en vivo."
                ),
            }

        utiles = [
            c
            for c in (candidatos or [])
            if isinstance(c, dict)
            and safe_int(c.get("bid")) > 0
            and safe_float(c.get("expected_value")) > 0
        ]

        # EL DESEMPATE IMPORTA, Y LO APRENDI AQUI (11/09/2026)
        #
        #     En modo cartera todos los candidatos rinden LO
        #     MISMO por euro -la prima de reventa menos lo que se
        #     ofrece-, asi que ordenar solo por eso no discrimina
        #     nada: el primer intento se llevo al mas caro, gasto
        #     el presupuesto entero en UNA puja y dejo 17 fuera.
        #
        #     Eso es justo lo contrario de "pujar bajo por
        #     muchos".
        #
        #     Con el mismo rendimiento por euro, gana el que
        #     consume menos capacidad: caben mas, y cada uno es
        #     una opcion gratis sobre la subida del jugador.
        #     Y el rendimiento se REDONDEA antes de comparar:
        #     sin eso empataban en el 1,5461 % pero diferian en
        #     el decimal quince, asi que el desempate no entraba
        #     nunca y volvia a ganar el mas caro. Dos
        #     rendimientos que se distinguen en la millonesima
        #     son el mismo rendimiento.
        # Cada candidato lleva su probabilidad de llevarselo,
        # se use para ordenar o no: publicarla siempre es lo que
        # permite comparar los dos ordenes sin recalcular nada.
        for candidato in utiles:

            suya = probabilidad_de_llevarselo(
                candidato.get("market_price"),
                candidato.get("rate_percent_per_day"),
            )

            candidato["win_odds"] = suya["probabilidad"]
            candidato["win_odds_cell"] = suya["celda"]
            candidato["win_odds_n"] = suya["n"]
            candidato["win_odds_reason"] = suya["reason"]

        utiles.sort(
            key=lambda c: (
                # A la diezmilesima: el truncado a enteros de
                # la ganancia hace que un jugador de 300.000 y
                # otro de 700.000 rindan 1,5458 % y 1,5460 %.
                # Con seis decimales seguian sin empatar y el
                # desempate no entraba. Dos rendimientos que se
                # distinguen en la centesima de punto son el
                # mismo rendimiento.
                -round(_por_euro(c, contar_la_pelea), 4),
                safe_int(c.get("bid")),
            )
        )

        elegidos = []
        descartados = []

        comprometido = 0
        por_club: dict = {}

        for candidato in utiles:

            puja = safe_int(candidato.get("bid"))

            club = candidato.get("team_id")

            motivo = None

            if len(elegidos) >= huecos:
                motivo = (
                    f"no quedan fichas libres "
                    f"({huecos} en total)"
                )

            elif comprometido + puja > limite["tope"]:
                motivo = (
                    f"pasaria del tope de la ventana "
                    f"({_euros(limite['tope'])} EUR)"
                )

            elif (
                max_por_club is not None
                and club is not None
                and por_club.get(club, 0) + 1 > max_por_club
            ):
                motivo = (
                    f"ya hay {max_por_club} de ese club en la "
                    f"cesta"
                )

            if motivo:
                descartados.append({
                    **candidato,
                    "motivo": motivo,
                })
                continue

            elegidos.append({
                **candidato,
                "yield_per_euro": round(
                    100 * _por_euro(candidato), 3
                ),
            })

            comprometido += puja

            if club is not None:
                por_club[club] = por_club.get(club, 0) + 1

        return {
            "available": True,
            "observer_only": True,
            "elegidos": elegidos,
            "descartados": descartados,
            "comprometido": comprometido,
            "fichas_usadas": len(elegidos),
            "fichas_libres": huecos,
            "tope": limite,
            "reason": _reason_cesta(
                elegidos, descartados, comprometido, huecos,
                limite,
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo elegir la cesta: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason_cesta(
    elegidos, descartados, comprometido, huecos, limite
) -> str:

    euros = _euros

    if not elegidos:
        return (
            f"Ninguna puja: {len(descartados)} candidato(s) y "
            f"ninguno pasa. {limite['reason']}"
        )

    ganancia = sum(
        safe_float(c.get("expected_value")) for c in elegidos
    )

    return (
        f"{len(elegidos)} puja(s) por {euros(comprometido)} EUR, "
        f"ocupando {len(elegidos)} de {huecos} fichas libres. "
        f"Si se ganaran TODAS, la ganancia esperada seria "
        f"{euros(ganancia)} EUR. "
        f"{len(descartados)} candidato(s) fuera."
    )


def peor_caso(cesta: dict | None, plantilla: list | None) -> dict:
    """
    Como quedaria la plantilla si se ganaran TODAS.

    LAS BARANDILLAS NO SE MIRAN UNA A UNA

        Cuatro pujas que por separado no concentran nada pueden
        dejar el 60 % del patrimonio en un club si entran las
        cuatro. Se comprueba el resultado, no cada paso.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "jugadores": 0,
        "por_club": {},
        "reason": "Sin cesta que mirar.",
    }

    try:
        elegidos = (cesta or {}).get("elegidos") or []

        if not elegidos:
            return {**vacio, "reason": "La cesta esta vacia."}

        por_club: dict = {}

        for jugador in (plantilla or []):

            if not isinstance(jugador, dict):
                continue

            club = jugador.get("team_id") or jugador.get(
                "teamID"
            )

            if club is not None:
                por_club[club] = por_club.get(club, 0) + 1

        antes = dict(por_club)

        for candidato in elegidos:

            club = candidato.get("team_id")

            if club is not None:
                por_club[club] = por_club.get(club, 0) + 1

        return {
            "available": True,
            "jugadores": len(plantilla or []) + len(elegidos),
            "por_club": por_club,
            "por_club_antes": antes,
            "reason": (
                f"Si entraran las {len(elegidos)}, la plantilla "
                f"quedaria en "
                f"{len(plantilla or []) + len(elegidos)} "
                f"jugadores. Maximo por club: "
                f"{max(por_club.values()) if por_club else 0}."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar el peor caso: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# ENCENDER LAS PUJAS (09/09/2026)
# ============================================================
#
#     Dos semanas midiendo y Pepe no ha pujado ni una vez. La
#     pieza estaba construida y apagada.
#
#     LOS LIMITES DEL PRIMER DIA, Y POR QUE EXISTEN
#
#         Tres pujas como mucho, aunque el reparto proponga
#         mas. No es una medicion: es que el primer dia de algo
#         que escribe en Biwenger se mira con pocas piezas en el
#         tablero. Cuando haya una semana de resultados en el
#         libro de pujas, este numero se decide con datos.
#
#         Hoy cuesta poco: el reparto propone cuatro y el cuarto
#         añade 853 EUR de esperado sobre 310.776 mas
#         comprometidos. Recortar a tres pierde el 5 % del
#         esperado.
#
#     LO QUE MANDA POR ENCIMA DE TODO
#
#         El reloj de solvencia. Si hay deficit o el plazo
#         aprieta, no se puja: el viernes hay que estar en
#         positivo, y una puja ganada es dinero que sale.
#
#     EL INTERRUPTOR
#
#         `BORDALAS_SIN_SUBASTA=1` y no se puja nada, en
#         cualquier fase y con cualquier cesta.
#
#         Y APAGA ESTA FUNCION, NO EL SISTEMA (22/09/2026).
#         Tiene UN solo lector -`_sin_subasta`, aqui abajo- y
#         cierra `plan_del_reset`. El carril de la rendija y el
#         tablero de fichajes siguen pujando: cada uno tiene el
#         suyo. La frase "no se puja nada" es verdad de esta
#         funcion y falsa del sistema. Ver
#         `el_corte_de_la_reventa`.
MAX_PUJAS_PRIMER_DIA = 3


# ============================================================
# EL TOPE, POR VENTANA Y NO POR VUELTA (22/09/2026)
# ============================================================
#
#     `MAX_PUJAS_PRIMER_DIA` se aplica a CADA llamada, y en los
#     135 minutos de la ventana entran DOS disparos -04:45 y
#     04:50 de Madrid, con la cola de concurrencia detras-. Tres
#     y tres son seis.
#
#     MEDIDO SOBRE `libro_de_la_ventana.jsonl`: n=19 vueltas con
#     la ventana abierta, en 10 ventanas (12/09 a 21/09). NUEVE
#     de las diez tuvieron dos vueltas dentro, y en TRES la suma
#     paso de tres:
#
#         12/09   3 + 1 = 4
#         15/09   1 + 3 = 4
#         18/09   3 + 2 = 5
#
#     El 21/09 el libro solo tiene la primera vuelta -3 pujas-
#     porque la segunda no llego a escribir; el libro de pujas
#     tiene las SEIS compras de esa ventana, 2.566.406 EUR.
#
#     EL NUMERO NO ES NUEVO. El cupo sigue siendo 3; lo que
#     cambia es contra que se cuenta: contra lo que YA hay
#     puesto en esta ventana, que llega por `ya_pujados` y sale
#     del libro de pujas. Ni un numero mas.
#
#     QUE SE CUENTA, DICHO ENTERO: `ya_pujados` trae TODAS
#     nuestras pujas sin resolver de la ventana, vengan de la
#     cesta o del carril. Es la misma lista que ya se usa para
#     no repetir jugador, y no hay otra sin preguntarle al libro
#     una segunda cosa. Cuenta de menos pujas, nunca de mas.
#
#     APAGADO de fabrica. Lo enciende el dueno en el YAML.
CUPO_POR_VENTANA_ENV = "BORDALAS_CUPO_POR_VENTANA"


def cupo_por_ventana() -> bool:
    """Si el tope de pujas es por ventana. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(CUPO_POR_VENTANA_ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def separar_por_la_via(candidatos: list | None) -> dict:
    """
    El corte de la reventa, sobre los candidatos de la cesta.

    Se importa aqui dentro como todo lo demas de este fichero: la
    cabecera no abre nada. Si el corte no se puede cargar, pasan
    todos -que es el comportamiento de antes del 22/09-, porque
    un modulo que no importa no puede frenar una puja que el
    resto del sistema ya aprobo.

    Nunca lanza.
    """

    try:
        from src.analysis.el_corte_de_la_reventa import separar

        return separar(candidatos)

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "cerrada": False,
            "siguen": list(candidatos or []),
            "frenados": [],
            "reason": (
                f"No se pudo mirar el corte de la reventa: "
                f"{type(error).__name__}: {error}"
            ),
        }


DISABLE_ENV = "BORDALAS_SIN_SUBASTA"


# Estados del reloj de solvencia en los que SI se puede pujar.
# Cualquier otro -y cualquier deficit- cierra la ventana.
SOLVENCIA_QUE_DEJA_PUJAR = frozenset({"SIN_DEUDA", "CUBIERTO"})


def _sin_subasta() -> bool:
    import os

    return str(
        os.environ.get(DISABLE_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def mira_si_va_a_jugar_de_verdad(candidatos: list | None) -> dict:
    """
    La regla de compra, sobre los candidatos de la cesta.

    Se importa aqui dentro como todo lo demas de este fichero: la
    cabecera no abre nada. Si la regla no se puede cargar pasan
    todos —que es el comportamiento de antes del 22/09—, porque
    un modulo que no importa no puede frenar una puja que el
    resto del sistema ya aprobo.

    Nunca lanza.
    """

    try:
        from src.analysis.la_regla_de_compra import (
            mira_si_va_a_jugar,
        )

        return mira_si_va_a_jugar(candidatos)

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "activa": False,
            "siguen": list(candidatos or []),
            "frenados": [],
            "reason": (
                f"No se pudo mirar la regla de compra: "
                f"{type(error).__name__}: {error}"
            ),
        }


def plan_del_reset(
    candidatos: list | None,
    prima_de_reventa: float,
    presupuesto,
    fichas_libres,
    caja_libre,
    seconds_to_reset,
    solvency_clock: dict | None,
    plantilla: list | None = None,
    bloqueo_temporal: str | None = None,

    # QUIEN YA TIENE PUJA NUESTRA EN ESTA VENTANA
    #
    #     Sale del LIBRO de pujas, no del tablero. Con dos
    #     disparos externos a cinco minutos, los dos dentro de la
    #     ventana, la segunda vuelta podria pujar otra vez por el
    #     mismo jugador y comprometer capacidad por duplicado.
    #
    #     `has_live_bid` tambien lo evitaria, pero depende de que
    #     la foto haya llegado fresca. El libro se escribe en el
    #     mismo instante en que se puja.
    ya_pujados: list | None = None,

    en_vivo: bool = False,
    max_por_club: int | None = None,
    max_pujas: int = MAX_PUJAS_PRIMER_DIA,
) -> dict:
    """
    Por quien se puja en esta ventana, o por que no se puja.

    TODO SE PASA: los segundos al reset, el reloj de solvencia,
    los bolsillos. Aqui no se lee ni disco, ni red, ni hora.

    Las puertas, en orden, y cada una con su motivo publicado:

        1. el interruptor
        2. el reloj de solvencia manda
        3. la ventana del reset
        4. el corte de la reventa, por la via del candidato
        5. las fichas libres
        6. el reparto -con la pelea contada- y sus barandillas
        7. el tope del primer dia, por vuelta o por ventana

    Forma fija. Nunca lanza. `execute` sale False salvo que TODO
    este en orden Y `en_vivo`.
    """

    vacio = {
        "available": False,
        "execute": False,
        "bids": [],
        "committed": 0,
        "expected": 0,
        "slots_used": 0,
        "window": None,
        "capped_at": max_pujas,
        "dropped_by_cap": 0,
        "dropped_by_club": 0,
        "dropped_by_no_juega": 0,
        "dropped_by_reventa": 0,
        "ya_en_la_ventana": 0,
        "cupo_por_ventana": False,
        "all_won": 0,
        "worst_case": None,
        "blocked_by": None,
        "reason": None,
    }

    try:
        if _sin_subasta():
            return {
                **vacio,
                "available": True,
                "blocked_by": "INTERRUPTOR",
                "reason": (
                    f"{DISABLE_ENV} puesto: no se puja nada."
                ),
            }

        # EL RELOJ DE SOLVENCIA, ANTES QUE LA VENTANA
        #
        #     Va primero a proposito. Si el viernes no llegamos
        #     en positivo, da igual lo buena que sea la cesta:
        #     una puja ganada es dinero que sale.
        reloj = solvency_clock or {}

        estado = str(reloj.get("state") or "")

        deficit = safe_int(reloj.get("deficit"))

        if estado not in SOLVENCIA_QUE_DEJA_PUJAR or deficit > 0:
            return {
                **vacio,
                "available": True,
                "blocked_by": "SOLVENCIA",
                "reason": (
                    f"El reloj de solvencia dice «{estado or '?'}»"
                    + (
                        f" con {_euros(deficit)} EUR de deficit"
                        if deficit > 0
                        else ""
                    )
                    + ". No se puja: el viernes hay que estar en "
                    "positivo."
                ),
            }

        # EL BLOQUEO TEMPORAL DE LA CASA
        #
        #     Una puja es una escritura contra Biwenger. Si las
        #     operaciones estan cerradas por la fase -jornada
        #     bloqueada, transicion de ronda-, esta no es la
        #     excepcion.
        if bloqueo_temporal:
            return {
                **vacio,
                "available": True,
                "blocked_by": "BLOQUEO_TEMPORAL",
                "reason": (
                    f"Operaciones bloqueadas en fase "
                    f"«{bloqueo_temporal}». No se puja."
                ),
            }

        ventana = ventana_abierta(seconds_to_reset)

        if not ventana["abierta"]:
            return {
                **vacio,
                "available": True,
                "window": ventana,
                "blocked_by": "FUERA_DE_VENTANA",
                "reason": ventana["reason"],
            }

        # LOS QUE YA TIENEN PUJA PUESTA EN ESTA VENTANA, FUERA.
        puestos = {
            safe_int(x) for x in (ya_pujados or []) if x
        }

        sin_repetir = [
            c for c in (candidatos or [])
            if isinstance(c, dict)
            and safe_int(c.get("id")) not in puestos
        ]

        # DOS FILTROS EN FILA, Y NO SON EL MISMO (22/09/2026)
        #
        #     Los dos nacieron el mismo dia, en dos ramas, y los
        #     dos se ponen aqui. Se encadenan porque contestan
        #     preguntas distintas:
        #
        #         1. ¿VA A JUGAR?   `la_regla_de_compra`, sobre la
        #            fila del tablero. Lo que no juega no mueve el
        #            mercado, y el mercado es de donde sale el
        #            beneficio de un viaje.
        #         2. ¿ES REVENTA?   `el_corte_de_la_reventa`, sobre
        #            la fila ya montada en modo cartera. Cierra la
        #            reventa y deja pasar al que se compra para
        #            quedarselo.
        #
        #     En este orden porque el primero mira al JUGADOR y el
        #     segundo a la OPERACION: filtrar al jugador antes de
        #     montarle la puja ahorra montarsela a quien no va a
        #     pujar.
        #
        #     LOS DOS APAGADOS DE FABRICA. Con los dos
        #     interruptores quitados, esto es la lista entera y el
        #     comportamiento es el de antes del 22/09.

        # 1. ¿VA A JUGAR?
        #
        #     MEDIDO sobre los 115 viajes cerrados del tablon: el
        #     beneficio de un viaje es el MOVIMIENTO DEL MERCADO
        #     -+10.690.000 de los 13.072.324 de Pollo17- y el
        #     mercado se mueve CERO para el que no juega. De las
        #     seis filas en que se parten sus viajes, la unica que
        #     pierde dinero es "habia partido y no jugo": 33 % en
        #     verde, ROI mediano -2,03 %.
        regla = mira_si_va_a_jugar_de_verdad(sin_repetir)

        frenados_por_la_regla = len(regla.get("frenados") or [])

        elegibles = regla.get("siguen") or []

        if frenados_por_la_regla and not elegibles:
            return {
                **vacio,
                "available": True,
                "window": ventana,
                "dropped_by_no_juega": frenados_por_la_regla,
                "blocked_by": "NO_VA_A_JUGAR",
                "reason": regla.get("reason"),
            }

        sin_repetir = elegibles

        # 2. ¿ES REVENTA?
        #
        #     Mira LA VIA DEL CANDIDATO, no el camino: un
        #     candidato que el tablero clasifico QUEDARSE sigue
        #     pujando con el corte puesto. Hoy eso no cambia nada
        #     -0 fichas libres, 0 candidatos QUEDARSE- y el dia que
        #     se vendan los rellenos es la puerta que tiene que
        #     seguir abierta.
        en_cartera = candidatos_en_modo_cartera(
            sin_repetir, prima_de_reventa
        )

        corte = separar_por_la_via(en_cartera)

        frenados_por_reventa = len(corte.get("frenados") or [])

        elegibles = corte.get("siguen") or []

        if frenados_por_reventa and not elegibles:
            return {
                **vacio,
                "available": True,
                "window": ventana,
                "dropped_by_no_juega": frenados_por_la_regla,
                "dropped_by_reventa": frenados_por_reventa,
                "blocked_by": "SIN_REVENTA",
                "reason": corte.get("reason"),
            }

        cesta = elegir_la_cesta(
            elegibles,
            presupuesto=presupuesto,
            fichas_libres=fichas_libres,
            caja_libre=caja_libre,
            max_por_club=max_por_club,
        )

        elegidos = cesta.get("elegidos") or []

        if not elegidos:
            return {
                **vacio,
                "available": True,
                "window": ventana,
                "dropped_by_no_juega": frenados_por_la_regla,
                "dropped_by_reventa": frenados_por_reventa,
                "blocked_by": "SIN_CESTA",
                "reason": cesta.get("reason"),
            }

        # EL TOPE DEL PRIMER DIA, AL FINAL
        #
        #     Despues del reparto y no antes: primero se elige
        #     bien entre todos, y luego se recorta. Al reves se
        #     estaria eligiendo entre tres al azar.
        tope = max(0, safe_int(max_pujas))

        # Y POR VENTANA, SI EL DUENO LO HA ENCENDIDO.
        #
        #     Lo que ya hay puesto en esta ventana llega por
        #     `ya_pujados` -del libro de pujas- y ya se usa aqui
        #     arriba para no repetir jugador. Contarlo es la
        #     linea entera del cambio: ni un numero nuevo.
        #
        #     `ya_pujados` a `None` es "no se ha preguntado", no
        #     "van cero" (doctrina 103). La pantalla llama asi, y
        #     por eso el recuento se publica al lado del plan: si
        #     sale 0 con la ventana abierta, es que quien
        #     pregunto no traia el libro.
        en_la_ventana = len(puestos)

        por_ventana = cupo_por_ventana()

        if por_ventana:
            tope = max(0, tope - en_la_ventana)

        recortados = max(0, len(elegidos) - tope)

        elegidos = elegidos[:tope]

        if por_ventana and not elegidos:
            return {
                **vacio,
                "available": True,
                "window": ventana,
                "capped_at": tope,
                "dropped_by_cap": recortados,
                "dropped_by_reventa": frenados_por_reventa,
                "ya_en_la_ventana": en_la_ventana,
                "cupo_por_ventana": True,
                "blocked_by": "CUPO_DE_LA_VENTANA",
                "reason": (
                    f"El cupo es de {safe_int(max_pujas)} por "
                    f"VENTANA y ya hay {en_la_ventana} puja(s) "
                    f"nuestra(s) en esta. No quedan huecos: "
                    f"{recortados} se quedan fuera. "
                    f"{ventana['reason']}"
                ),
            }

        # LA BARANDILLA SOBRE EL PEOR CASO: QUE SE GANEN TODAS
        #
        #     `elegir_la_cesta` ya limita cuantos del mismo club
        #     van EN LA CESTA. Lo que no puede saber es cuantos
        #     de ese club hay YA en la plantilla.
        #
        #     Tres del Betis en el banquillo mas dos en la cesta
        #     son cinco si entran las dos, y cinco del mismo club
        #     es salirse de lo que hace el lider de la liga.
        #
        #     Se cuenta la suma, no cada puja por separado.
        ocupacion: dict = {}

        for jugador in (plantilla or []):

            if not isinstance(jugador, dict):
                continue

            club = jugador.get("team_id") or jugador.get("teamID")

            if club is not None:
                ocupacion[club] = ocupacion.get(club, 0) + 1

        tope_club = safe_int(max_por_club)

        if tope_club > 0 and elegidos:

            caben = []
            fuera_por_club = 0

            for candidato in elegidos:

                club = candidato.get("team_id")

                if (
                    club is not None
                    and ocupacion.get(club, 0) + 1 > tope_club
                ):
                    fuera_por_club += 1
                    continue

                if club is not None:
                    ocupacion[club] = ocupacion.get(club, 0) + 1

                caben.append(candidato)

            elegidos = caben

        else:
            fuera_por_club = 0

        if not elegidos:
            return {
                **vacio,
                "available": True,
                "window": ventana,
                "dropped_by_cap": recortados,
                "dropped_by_club": fuera_por_club,
                "dropped_by_no_juega": frenados_por_la_regla,
                "dropped_by_reventa": frenados_por_reventa,
                "ya_en_la_ventana": en_la_ventana,
                "cupo_por_ventana": por_ventana,
                "blocked_by": "PEOR_CASO",
                "reason": (
                    f"Las {fuera_por_club} puja(s) que quedaban "
                    f"dejarian mas de {tope_club} jugadores del "
                    f"mismo club si se ganaran. No se puja."
                ),
            }

        comprometido = sum(
            safe_int(c.get("bid")) for c in elegidos
        )

        esperado = int(
            sum(
                safe_float(c.get("expected_value"))
                * safe_float(c.get("win_odds"), 0.0)
                for c in elegidos
            )
        )

        # Lo que se ganaria si entraran TODAS, que es el caso
        # que hay que poder mirar antes de encender nada.
        si_todas = int(
            sum(
                safe_float(c.get("expected_value"))
                for c in elegidos
            )
        )

        return {
            "available": True,
            "execute": bool(en_vivo and elegidos),
            "bids": elegidos,
            "committed": comprometido,
            "expected": esperado,
            "all_won": si_todas,
            "worst_case": peor_caso(
                {"elegidos": elegidos}, plantilla
            ),
            "slots_used": len(elegidos),
            "window": ventana,
            "capped_at": tope,
            "dropped_by_cap": recortados,
            "dropped_by_club": fuera_por_club,
            "dropped_by_no_juega": frenados_por_la_regla,
            "dropped_by_reventa": frenados_por_reventa,
            "ya_en_la_ventana": en_la_ventana,
            "cupo_por_ventana": por_ventana,
            "blocked_by": None if en_vivo else "SIN_LIVE",
            "reason": (
                f"{len(elegidos)} puja(s) por "
                f"{_euros(comprometido)} EUR, esperado "
                f"{_euros(esperado)} EUR. "
                f"{ventana['reason']}"
                + (
                    f" El tope del primer dia dejo fuera "
                    f"{recortados}."
                    if recortados
                    else ""
                )
                + (
                    ""
                    if en_vivo
                    else " NO se ejecuta: falta el modo en vivo."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "blocked_by": "ERROR",
            "reason": (
                f"No se pudo montar el plan del reset: "
                f"{type(error).__name__}: {error}"
            ),
        }


def lectura_del_estado(
    state: dict | None,
    snapshot: dict | None = None,
) -> dict:
    """
    Traduce el estado del ciclo a lo que pide `plan_del_reset`.

    POR QUE EXISTE, Y POR QUE ES UNA SOLA

        Esto lo necesitan DOS procesos: el ciclo, que puja, y la
        telemetria, que ensena en la pantalla por quien va a
        pujar. Si cada uno arma sus candidatos por su cuenta,
        acaban ensenando cosas distintas del mismo mercado, y el
        dueno mira una pantalla que no es lo que va a pasar.

        Aqui se arma una vez. Las dos llaman a la misma.

    NO LEE EL MUNDO: recibe el estado y el snapshot ya cargados.
    Ni disco, ni red, ni reloj. Forma fija. Nunca lanza.
    """

    lectura = {
        "candidatos": [],
        "prima_de_reventa": 0.0,
        "presupuesto": 0,
        "fichas_libres": 0,
        "caja_libre": 0,
        "seconds_to_reset": None,
        "solvency_clock": None,
        "plantilla": [],
        "bloqueo_temporal": None,
        "max_por_club": None,
    }

    try:
        estado = state or {}

        tablero = estado.get("acquisition") or {}
        bolsillos = estado.get("exposure") or {}
        reloj = estado.get("market_clock") or {}

        # LOS CANDIDATOS
        #
        #     Pujando al 0,25 % por encima del precio, lo que
        #     vetaba a un jugador para una puja cara deja de
        #     vetarlo: no se paga prima, asi que no hay prima
        #     que justificar. Por eso entran los `SIN_VALOR`:
        #     no valen lo que piden, pero el reset paga la
        #     prima de reventa igual.
        #
        #     TRES PUERTAS QUE NO SE CRUZAN
        #
        #     1. LA COMPRA A RIVALES SIGUE CERRADA. De 49
        #        objetivos del 09/09, VEINTINUEVE son de
        #        mercado de rival. Pujar por uno es comprarle a
        #        un rival, que es una puerta que el dueno tiene
        #        cerrada. Se miran, no se pujan.
        #
        #     2. Ni un jugador con puja viva: dos pujas por el
        #        mismo son dos compromisos por una ficha.
        #
        #     3. Ni los NO_DISPONIBLE, que no se pueden comprar.
        #
        #     LOS CAMPOS QUE SE TIRABAN (22/09/2026)
        #
        #     Esta copia llevaba SEIS campos y dejaba atras
        #     `hierarchy_value`, `starter_probability` y
        #     `expected_points` -que la fila del tablero ya
        #     trae-. El 21/09 la cesta compro cinco suplentes de
        #     150.000-230.000 que el propio motor etiqueta "Es
        #     Reserva en su equipo: no va a puntuar": no es que
        #     los prefiriera, es que NO PODIA VERLOS. En modo
        #     cartera todos rinden igual por euro, asi que
        #     decidia el desempate -"gana el que consume menos
        #     capacidad"-, que en el suelo significa comprar lo
        #     peor del mercado. Doctrina 110.
        #
        #     Y con ellos van `intent` y `route`, que son lo que
        #     el corte de la reventa mira para saber si un
        #     candidato es para quedarselo. Sin ellos el corte
        #     no puede distinguir, y separar la reventa de la
        #     compra de plantilla seria imposible aqui.
        #
        #     LO QUE CUESTA, MEDIDO. La fila ya esta en memoria:
        #     esto es copiar cinco claves mas de un dict. Sobre
        #     la foto del 18/09, n=54 objetivos y 2.000
        #     repeticiones: 0,014 ms con seis campos, 0,025 ms
        #     con once. ONCE MICROSEGUNDOS por vuelta, contra
        #     vueltas de 47 minutos. Ni red, ni disco, ni una
        #     llamada mas.
        #
        #     NO DECIDE NADA TODAVIA. `candidatos_en_modo_cartera`
        #     no los lee: viajan para que el corte los mire y
        #     para que se vean en pantalla.
        lectura["candidatos"] = [
            {
                "id": fila.get("id"),
                "name": fila.get("name"),
                "market_price": fila.get("market_price"),
                "team_id": fila.get("team_id"),
                "seller_id": fila.get("seller_id"),
                "rate_percent_per_day": (
                    fila.get("market_gate") or {}
                ).get("rate_percent_per_day"),

                # ¿VA A JUGAR? Y ¿POR QUE VIA? (22/09/2026)
                #
                #     Estos cinco los publica el tablero y esta
                #     copia los tiraba. Son los que miran los dos
                #     filtros de `plan_del_reset`:
                #
                #         `la_regla_de_compra`     el pronostico y
                #                                  la jerarquia
                #         `el_corte_de_la_reventa` el intent y la
                #                                  route
                #
                #     Sin ellos la regla no distingue a un titular
                #     de un suplente y el corte no distingue una
                #     reventa de un fichaje: los frenarian a
                #     todos.
                #
                #     `expected_points` viaja para que se pueda
                #     mirar en pantalla: no decide nada.
                #
                #     Cuesta copiar cinco claves de un dict que ya
                #     esta en memoria. Medido sobre la foto del
                #     18/09, n=54 objetivos y 2.000 repeticiones:
                #     0,014 ms con seis campos, 0,025 ms con once.
                #     Ni red, ni disco, ni una llamada mas.
                "starter_probability": fila.get(
                    "starter_probability"
                ),
                "hierarchy_value": fila.get("hierarchy_value"),
                "availability": fila.get("availability"),
                "intent": fila.get("intent"),
                "route": (
                    fila.get("route")
                    or (fila.get("deployment") or {}).get("route")
                ),
                "expected_points": fila.get("expected_points"),
            }
            for fila in (tablero.get("targets") or [])
            if isinstance(fila, dict)
            and fila.get("decision") != "NO_DISPONIBLE"
            and not fila.get("outside_computer_market")
            and not fila.get("seller_id")
            and not fila.get("has_live_bid")
            and safe_int(fila.get("market_price")) > 0
        ]

        lectura["prima_de_reventa"] = (
            safe_float(
                (tablero.get("computer_premium") or {}).get(
                    "median_percent"
                )
            )
            / 100.0
        )

        lectura["presupuesto"] = bolsillos.get("available_budget")
        lectura["caja_libre"] = bolsillos.get("cash_budget")
        lectura["seconds_to_reset"] = reloj.get("seconds_to_reset")
        lectura["solvency_clock"] = estado.get("solvency_clock")

        # LAS FICHAS LIBRES, con la definicion de la casa: la
        # plantilla mas grande de la liga menos la nuestra.
        managers = (
            (estado.get("rival_intelligence") or {}).get("managers")
            or []
        )

        tamanos = [
            safe_int(m.get("roster_count"))
            for m in managers
            if isinstance(m, dict)
        ]

        nuestra = next(
            (
                safe_int(m.get("roster_count"))
                for m in managers
                if isinstance(m, dict) and m.get("is_us")
            ),
            0,
        )

        lectura["fichas_libres"] = max(
            0, (max(tamanos) if tamanos else nuestra) - nuestra
        )

        # LA PLANTILLA, para el peor caso. Del snapshot, que es
        # donde vive; el estado no la lleva.
        plantilla = (snapshot or {}).get("my_team")

        if isinstance(plantilla, dict):
            plantilla = (
                plantilla.get("players")
                or plantilla.get("data")
                or []
            )

        lectura["plantilla"] = [
            j for j in (plantilla or []) if isinstance(j, dict)
        ]

        # EL BLOQUEO TEMPORAL de la casa, el mismo que respetan
        # las demas escrituras del ciclo.
        if bool(estado.get("operations_locked")):
            lectura["bloqueo_temporal"] = str(
                estado.get("phase") or "UNKNOWN"
            )

        # EL TOPE POR CLUB no se inventa aqui: es el de la casa,
        # el que lleva el lider de la liga.
        try:
            from src.analysis.concentration_guardrail import (
                MAX_SAME_TEAM,
            )

            lectura["max_por_club"] = MAX_SAME_TEAM

        except Exception:                           # noqa: BLE001
            lectura["max_por_club"] = None

        return lectura

    except Exception:                               # noqa: BLE001
        return lectura


def plan_desde_el_estado(
    state: dict | None,
    snapshot: dict | None = None,
    en_vivo: bool = False,
    max_pujas: int = MAX_PUJAS_PRIMER_DIA,
    ya_pujados: list | None = None,
) -> dict:
    """
    El plan del reset a partir del estado del ciclo.

    Una linea para el ciclo y otra para la pantalla, y las dos
    pasando por el mismo sitio.
    """

    return plan_del_reset(
        **lectura_del_estado(state, snapshot),
        ya_pujados=ya_pujados,
        en_vivo=en_vivo,
        max_pujas=max_pujas,
    )


def para_la_pantalla(
    cesta: dict | None,
    ventana: dict | None,
    resultado_anterior: dict | None = None,
) -> dict:
    """
    Lo que hay que ver ANTES del reset, y lo que quedo DESPUES.

    El dueño lo pidio asi: "no veo pujas para ganar algun
    jugador, ni en estrategia pone «espero a cinco minutos antes
    del reset»".

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "observer_only": True,
        "enabled": False,
        "window": None,
        "bids": [],
        "committed": 0,
        "slots_used": 0,
        "slots_free": 0,
        "expected_gain": 0,
        "last_reset": None,
        "reason": None,
    }

    try:
        cesta = cesta or {}

        elegidos = cesta.get("elegidos") or []

        return {
            "available": bool(cesta.get("available")),
            "observer_only": True,

            # EN SOMBRA. Nadie ejecuta esto todavia.
            "enabled": False,

            "window": ventana,

            "bids": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "price": safe_int(c.get("market_price")),
                    "bid": safe_int(c.get("bid")),
                    "expected_value": safe_int(
                        c.get("expected_value")
                    ),
                    "yield_per_euro": c.get("yield_per_euro"),

                    # Por que ese importe y no otro.
                    # REGLA 17: cada decision cita su regla.
                    # Aqui, cual de los dos modos la eligio.
                    "modo": c.get("modo"),

                    "why": c.get("bid_reason")
                    or c.get("reason"),
                }
                for c in elegidos
            ],

            "committed": safe_int(cesta.get("comprometido")),
            "slots_used": safe_int(cesta.get("fichas_usadas")),
            "slots_free": safe_int(cesta.get("fichas_libres")),

            "expected_gain": int(
                sum(
                    safe_float(c.get("expected_value"))
                    for c in elegidos
                )
            ),

            # Que gano y que perdio en el reset anterior. Es lo
            # que alimenta el libro de pujas, que hoy tiene UN
            # registro.
            "last_reset": resultado_anterior,

            "reason": cesta.get("reason"),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar la pantalla: "
                f"{type(error).__name__}: {error}"
            ),
        }
