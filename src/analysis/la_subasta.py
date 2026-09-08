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
VENTANA_MINUTOS = 15


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


def _por_euro(candidato: dict) -> float:
    """
    Ganancia esperada por euro comprometido.

    Es lo que ordena la cesta: con dinero limitado, lo que
    importa no es cual gana mas, sino cual gana mas POR EURO
    inmovilizado.
    """

    puja = safe_int(candidato.get("bid"))

    if puja <= 0:
        return -1.0

    return safe_float(candidato.get("expected_value")) / puja


def elegir_la_cesta(
    candidatos: list | None,
    presupuesto,
    fichas_libres,
    caja_libre=None,
    max_por_club: int | None = None,
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

        utiles.sort(key=_por_euro, reverse=True)

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
