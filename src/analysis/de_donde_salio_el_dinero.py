"""
De donde salio el dinero: el crecimiento de los ocho, partido en
cuatro trozos que SUMAN.

LA PREGUNTA

    El reparto del 09/08/2026 dejo a cada manager con 23.300.000.
    Pollo17 tiene hoy 78,5 M. De donde salen esos 55 M no se
    sabia: se habia supuesto dos veces, y las dos sin medir.

    Importa porque de la respuesta depende la estrategia. Si el
    dinero sale de comprar y vender, hay que comerciar mas. Si
    sale de tener buenos jugadores quietos, hay que comerciar
    menos y fichar mejor.

LA IDENTIDAD QUE TIENE QUE CUADRAR

    patrimonio = 23.300.000
               + PREMIOS          jornada + racha diaria
               + VIAJES           cobrado - pagado, de los que
                                  compro Y vendio
               + SUBIDA QUIETA    precio de hoy - lo que pago,
                                  de los que compro y sigue
                                  teniendo
               + CUARTO MONTON    los que nunca compro

    Sale de despejar, no de ajustar. El patrimonio es caja mas
    plantilla; la caja es inicial + premios + ventas - compras; y
    las compras se parten en dos: las de los que ya vendio -que
    son la otra mitad de un viaje- y las de los que aun tiene
    -que son el coste contra el que se mide la subida-.

    Si los cuatro trozos no dan el patrimonio, algo se ha
    contado dos veces o se ha perdido. Por eso el cuadre no es
    decorado: es la prueba de que el reparto en montones no
    inventa ni se come euros.

    Y lo que el cuadre NO prueba: que la caja sea cierta. Las dos
    orillas de esta identidad beben de la misma reconstruccion.
    La caja solo se puede auditar contra un saldo real, y la liga
    tiene `settings.balance = "hidden"`: el unico saldo visible
    es el nuestro.

EL CUARTO MONTON: LO QUE NO SE PUEDE SABER

    El reparto inicial NO dejo precios en el tablon. De los 12
    jugadores que le tocaron a cada uno no hay coste en ninguna
    fuente: ni en los eventos, ni en `owner.price` de Biwenger.

    Asi que su subida NO SE PUEDE CALCULAR, y no se estima. Van a
    un monton aparte, se cuentan, y se dice cuanto valen hoy.

    Ese monton lleva dos cosas, y las dos son el mismo hecho -una
    plantilla regalada, valorada a mercado-:

        los que sigue teniendo     su precio de hoy
        los que ya vendio          lo que cobro por ellos

    No es beneficio. Es una dotacion que nadie pago.

EL COSTE NO SE RECONSTRUYE CUANDO SE PUEDE LEER

    Hay dos fuentes independientes del precio de compra de un
    jugador que sigue en plantilla:

        el tablon      emparejando compra con venta, FIFO
        Biwenger       `owner.price` del censo

    Medido el 15/09/2026 sobre los ocho: 81 de 81 coinciden AL
    EURO, y a los que le falta a una le falta tambien a la otra.
    Manda el tablon y se contrasta con Biwenger; una discrepancia
    se publica, no se promedia.

    Y si un dia Biwenger conoce un coste que el tablon no tiene,
    ese coste SE USA y el cuadre se rompe. Mandarlo al cuarto
    monton haria que la tabla cuadrase, pero lo que estaria roto
    -un evento perdido del tablon, que es de donde sale la caja-
    seguiria roto y ya no se veria. Un descuadre es informacion.

FIFO, Y POR QUE IMPORTA

    Comprar, vender y volver a comprar al mismo jugador es
    corriente en esta liga. Cada venta se empareja con la compra
    MAS ANTIGUA que quede abierta. Lo que sobra al final de la
    cola son los que aun tiene, y tiene que coincidir jugador a
    jugador con el censo: medido, coincide en los ocho.

SIN RELOJ, SIN DISCO, SIN RED

    Esta funcion no lee nada. Los eventos, el censo, los precios
    y la hora se los pasan. El `ahora` solo sirve para contar los
    dias que lleva un jugador en plantilla, y viene de fuera para
    que la medicion de hoy y la de manana midan lo mismo.

SI NO SE PUEDE, SE DICE

    Doctrina 36. Sin eventos no hay descomposicion:
    `available: False` y el motivo escrito. No se devuelve una
    tabla de ceros con la misma cara que una medida.
"""

from __future__ import annotations

import collections
import statistics

from src.analysis.caja_de_la_liga import SALDO_INICIAL, reconstruir


# Los dos unicos tipos de evento que mueven un jugador de manos.
TIPOS_DE_OPERACION = ("market", "transfer")

SEGUNDOS_POR_DIA = 86_400.0


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _media(valores, por_defecto=None):
    """La media, o el valor por defecto si no hay de que."""

    return statistics.fmean(valores) if valores else por_defecto


def _mediana(valores, por_defecto=None):
    return statistics.median(valores) if valores else por_defecto


# ============================================================
# LAS OPERACIONES, SIN REPETIR
# ============================================================


def operaciones(eventos: list) -> list:
    """
    Cada cambio de manos, una sola vez.

    La huella es la MISMA que usa `caja_de_la_liga.reconstruir`
    -tipo, fecha, jugador, origen, destino, importe- y no por
    gusto: si las dos deduplicaran distinto, los montones y la
    caja dejarian de cuadrar por una razon que no seria el error
    de nadie, solo dos criterios.

    El tablon reemite: la misma compra vuelve bajo otro
    `event_id` con una puja mas en `bids`. Por eso la identidad
    es logica y no el id.
    """

    vistos = set()

    filas = []

    for evento in sorted(
        [e for e in (eventos or []) if isinstance(e, dict)],
        key=lambda e: safe_int(e.get("date")),
    ):

        tipo = evento.get("type")

        if tipo not in TIPOS_DE_OPERACION:
            continue

        contenido = evento.get("content")

        if not isinstance(contenido, list):
            continue

        for operacion in contenido:

            if not isinstance(operacion, dict):
                continue

            vendedor = (operacion.get("from") or {}).get("id")
            comprador = (operacion.get("to") or {}).get("id")

            importe = safe_int(operacion.get("amount"))

            huella = (
                tipo,
                safe_int(evento.get("date")),
                operacion.get("player"),
                vendedor,
                comprador,
                importe,
            )

            if huella in vistos:
                continue

            vistos.add(huella)

            filas.append(
                {
                    "type": tipo,
                    "date": safe_int(evento.get("date")),
                    "player": operacion.get("player"),
                    "amount": importe,
                    "seller": vendedor,
                    "buyer": comprador,
                }
            )

    return filas


# ============================================================
# LOS VIAJES: COMPRAR Y LUEGO VENDER
# ============================================================


def emparejar(filas: list) -> dict:
    """
    Empareja cada venta con su compra, FIFO, por manager y
    jugador.

    Devuelve tres cosas y ninguna se solapa:

        `viajes`        compro y vendio: el viaje esta cerrado
        `sin_coste`     vendio sin haber comprado: reparto inicial
        `abiertos`      compro y no ha vendido: sigue en plantilla
    """

    cola = collections.defaultdict(collections.deque)

    viajes = collections.defaultdict(list)

    sin_coste = collections.defaultdict(list)

    compras = collections.Counter()

    ventas = collections.Counter()

    for fila in filas:

        # LA VENTA PRIMERO, Y NO ES CAPRICHO.
        #
        # Un `transfer` con `to` es venta para uno y compra para
        # el otro. Si se apuntara la compra antes, una reventa en
        # el mismo evento podria emparejarse consigo misma y
        # salir un viaje de cero dias que nunca existio.
        if fila["type"] == "transfer" and fila["seller"]:

            ventas[fila["seller"]] += 1

            abierta = cola[(fila["seller"], fila["player"])]

            if abierta:

                compra = abierta.popleft()

                viajes[fila["seller"]].append(
                    {
                        "player": fila["player"],
                        "pagado": compra["amount"],
                        "cobrado": fila["amount"],
                        "beneficio": (
                            fila["amount"] - compra["amount"]
                        ),
                        "comprado_el": compra["date"],
                        "vendido_el": fila["date"],
                        "dias": (
                            (fila["date"] - compra["date"])
                            / SEGUNDOS_POR_DIA
                        ),
                    }
                )

            else:
                # Vendio algo que nunca compro: del reparto.
                sin_coste[fila["seller"]].append(fila)

        if fila["buyer"]:

            compras[fila["buyer"]] += 1

            cola[(fila["buyer"], fila["player"])].append(fila)

    abiertos = collections.defaultdict(dict)

    for (quien, jugador), pendientes in cola.items():

        if pendientes:
            # La ULTIMA compra abierta es la que explica la
            # tenencia de hoy.
            abiertos[quien][jugador] = pendientes[-1]

    return {
        "viajes": viajes,
        "sin_coste": sin_coste,
        "abiertos": abiertos,
        "compras": compras,
        "ventas": ventas,
    }


# ============================================================
# EL CENSO
# ============================================================


def normalizar_censo(censo) -> dict:
    """
    El censo de los ocho, en una forma sola.

    Acepta el `profiles` del cache de rivales -claves de texto,
    `players` con `owner`- y devuelve
    {user_id: {"name": str, "players": {player_id: owner}}}.
    """

    salida = {}

    for clave, perfil in (censo or {}).items():

        if not isinstance(perfil, dict):
            continue

        quien = safe_int(perfil.get("id") or clave)

        if not quien:
            continue

        jugadores = {}

        for jugador in perfil.get("players") or []:

            if not isinstance(jugador, dict):
                continue

            identificador = jugador.get("id")

            if identificador is None:
                continue

            jugadores[identificador] = jugador.get("owner") or {}

        salida[quien] = {
            "name": perfil.get("name") or str(quien),
            "players": jugadores,
        }

    return salida


# ============================================================
# LA DESCOMPOSICION
# ============================================================


def descomponer(
    eventos: list,
    censo: dict,
    precios: dict,
    ahora: int,
    saldo_inicial: int = SALDO_INICIAL,
) -> dict:
    """
    El crecimiento de cada manager en cuatro trozos que suman.

    `precios` es {player_id: precio de hoy}. Un jugador sin
    precio NO vale cero: se cuenta aparte y se dice, porque un
    cero silencioso descuadra la tabla sin dejar rastro.
    """

    vacio = {
        "available": False,
        "initial_balance": saldo_inicial,
        "managers": {},
        "liga": {},
        "cuadre": {
            "available": False,
            "ok": None,
            "descuadres": [],
        },
        "events_read": 0,
        "operations": 0,
        "reason": None,
    }

    try:
        filas_de_eventos = [
            e for e in (eventos or []) if isinstance(e, dict)
        ]

        if not filas_de_eventos:
            return {
                **vacio,
                "reason": (
                    "El tablon llega vacio: sin eventos no hay "
                    "dinero que repartir en montones."
                ),
            }

        gente = normalizar_censo(censo)

        if not gente:
            return {
                **vacio,
                "events_read": len(filas_de_eventos),
                "reason": (
                    "El censo llega vacio: sin plantillas no se "
                    "sabe que tiene cada uno hoy."
                ),
            }

        precios_por_jugador = {
            safe_int(k): safe_int(v)
            for k, v in (precios or {}).items()
        }

        filas = operaciones(filas_de_eventos)

        libro = emparejar(filas)

        caja = reconstruir(
            filas_de_eventos,
            managers=list(gente),
            saldo_inicial=saldo_inicial,
        )

        if not caja.get("available"):
            return {
                **vacio,
                "events_read": len(filas_de_eventos),
                "operations": len(filas),
                "reason": (
                    "Sin caja reconstruida no hay patrimonio "
                    f"contra el que cuadrar: {caja.get('reason')}"
                ),
            }

        managers = {}

        descuadres = []

        for quien, perfil in gente.items():

            fila_de_caja = (caja.get("managers") or {}).get(
                quien
            ) or {}

            premios = safe_int(
                fila_de_caja.get("matchday")
            ) + safe_int(
                fila_de_caja.get("streak")
            )

            viajes = libro["viajes"].get(quien) or []

            ventas_sin_coste = libro["sin_coste"].get(quien) or []

            abiertos = libro["abiertos"].get(quien) or {}

            # --------------------------------------------
            # LOS QUE SIGUE TENIENDO
            # --------------------------------------------
            quietos = []

            cuarto_en_plantilla = []

            sin_precio_de_mercado = []

            valor_de_la_plantilla = 0

            for jugador, duenyo in perfil["players"].items():

                precio_de_hoy = precios_por_jugador.get(
                    safe_int(jugador)
                )

                if precio_de_hoy is None:
                    # No vale cero: vale DESCONOCIDO.
                    sin_precio_de_mercado.append(jugador)
                    continue

                valor_de_la_plantilla += precio_de_hoy

                compra = abiertos.get(jugador)

                # EL COSTE, DE LAS DOS FUENTES.
                #
                # Manda el tablon porque es el que sostiene la
                # caja; `owner.price` entra como contraste y como
                # respaldo si el tablon no alcanza la operacion.
                coste_del_tablon = (
                    safe_int(compra["amount"]) if compra else None
                )

                coste_de_biwenger = (
                    safe_int(duenyo.get("price"))
                    if isinstance(duenyo, dict)
                    and duenyo.get("price") is not None
                    else None
                )

                coste = (
                    coste_del_tablon
                    if coste_del_tablon is not None
                    else coste_de_biwenger
                )

                if coste is None:
                    # NO SE ESTIMA. Al cuarto monton.
                    cuarto_en_plantilla.append(
                        {
                            "player": jugador,
                            "valor": precio_de_hoy,
                            "desde": safe_int(
                                (duenyo or {}).get("date")
                            ),
                        }
                    )
                    continue

                desde = safe_int(
                    compra["date"]
                    if compra
                    else (duenyo or {}).get("date")
                )

                quietos.append(
                    {
                        "player": jugador,
                        "pagado": coste,
                        "vale_hoy": precio_de_hoy,
                        "subida": precio_de_hoy - coste,
                        "desde": desde,
                        "dias": (
                            (safe_int(ahora) - desde)
                            / SEGUNDOS_POR_DIA
                            if desde
                            else None
                        ),
                        "coste_del_tablon": coste_del_tablon,
                        "coste_de_biwenger": coste_de_biwenger,
                        "las_dos_fuentes_coinciden": (
                            coste_del_tablon == coste_de_biwenger
                            if (
                                coste_del_tablon is not None
                                and coste_de_biwenger is not None
                            )
                            else None
                        ),
                    }
                )

            # --------------------------------------------
            # LOS CUATRO TROZOS
            # --------------------------------------------
            beneficio_de_los_viajes = sum(
                v["beneficio"] for v in viajes
            )

            subida_de_los_quietos = sum(
                q["subida"] for q in quietos
            )

            valor_del_cuarto_en_plantilla = sum(
                c["valor"] for c in cuarto_en_plantilla
            )

            cobrado_del_cuarto_vendido = sum(
                safe_int(v["amount"]) for v in ventas_sin_coste
            )

            cuarto_monton = (
                valor_del_cuarto_en_plantilla
                + cobrado_del_cuarto_vendido
            )

            reconstruido = (
                saldo_inicial
                + premios
                + beneficio_de_los_viajes
                + subida_de_los_quietos
                + cuarto_monton
            )

            patrimonio = (
                safe_int(fila_de_caja.get("cash"))
                + valor_de_la_plantilla
            )

            diferencia = reconstruido - patrimonio

            if diferencia:
                descuadres.append(
                    {
                        "user_id": quien,
                        "name": perfil["name"],
                        "difference": diferencia,
                    }
                )

            dias_de_viaje = [v["dias"] for v in viajes]

            beneficios = [v["beneficio"] for v in viajes]

            dias_quietos = [
                q["dias"] for q in quietos if q["dias"] is not None
            ]

            subidas = [q["subida"] for q in quietos]

            managers[quien] = {
                "user_id": quien,
                "name": perfil["name"],

                "initial_balance": saldo_inicial,
                "cash": safe_int(fila_de_caja.get("cash")),
                "roster_value": valor_de_la_plantilla,
                "net_worth": patrimonio,
                "growth": patrimonio - saldo_inicial,

                # --- los cuatro trozos ---
                "prizes": premios,
                "prizes_matchday": safe_int(
                    fila_de_caja.get("matchday")
                ),
                "prizes_streak": safe_int(
                    fila_de_caja.get("streak")
                ),
                "trading": beneficio_de_los_viajes,
                "holding": subida_de_los_quietos,
                "endowment": cuarto_monton,

                # --- el cuadre ---
                "reconstructed": reconstruido,
                "difference": diferencia,
                "balances": diferencia == 0,

                # --- como comercia ---
                "buys": safe_int(libro["compras"].get(quien)),
                "sells": safe_int(libro["ventas"].get(quien)),
                "trips": {
                    "n": len(viajes),
                    "profit": beneficio_de_los_viajes,
                    "winners": sum(1 for b in beneficios if b > 0),
                    "mean_profit": _media(beneficios),
                    "median_profit": _mediana(beneficios),
                    "mean_days": _media(dias_de_viaje),
                    "median_days": _mediana(dias_de_viaje),
                    "detail": viajes,
                },
                "held": {
                    "n": len(quietos),
                    "gain": subida_de_los_quietos,
                    "winners": sum(1 for s in subidas if s > 0),
                    "mean_gain": _media(subidas),
                    "median_gain": _mediana(subidas),
                    "mean_days": _media(dias_quietos),
                    "median_days": _mediana(dias_quietos),
                    "detail": quietos,
                },

                # --- el cuarto monton, contado ---
                "unknown_cost": {
                    "in_roster_n": len(cuarto_en_plantilla),
                    "in_roster_value": (
                        valor_del_cuarto_en_plantilla
                    ),
                    "sold_n": len(ventas_sin_coste),
                    "sold_proceeds": cobrado_del_cuarto_vendido,
                    "total": cuarto_monton,
                    "detail": cuarto_en_plantilla,
                },

                # Lo que no se ha podido valorar. Si esto no es
                # cero, la tabla lleva un agujero y se ve.
                "players_without_price": sin_precio_de_mercado,
            }

        return {
            "available": True,
            "initial_balance": saldo_inicial,
            "managers": managers,
            "liga": _agregados(managers),
            "cuadre": {
                "available": True,
                "ok": not descuadres,
                "descuadres": descuadres,
                "reason": (
                    f"Los cuatro trozos mas {saldo_inicial:,} "
                    f"dan el patrimonio de los {len(managers)} "
                    f"managers, al euro."
                    if not descuadres
                    else (
                        f"NO CUADRA en {len(descuadres)}: "
                        + "; ".join(
                            f"{d['name']} se separa "
                            f"{d['difference']:+,}"
                            for d in descuadres
                        )
                    )
                ),
            },
            "events_read": len(filas_de_eventos),
            "operations": len(filas),
            "cash": {
                "repeats_skipped": caja.get("repeats_skipped"),
                "rounds_paid": caja.get("rounds_paid"),
                "rounds_seen": caja.get("rounds_seen"),
                "ignored_rounds": caja.get("ignored_rounds"),
            },
            "reason": (
                f"Crecimiento de {len(managers)} managers "
                f"partido en cuatro sobre {len(filas)} "
                f"operaciones de {len(filas_de_eventos)} eventos."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo descomponer el dinero: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _agregados(managers: dict) -> dict:
    """
    El viaje medio y el jugador quieto medio de TODA la liga.

    Se juntan las operaciones, no las medias de cada uno: la
    media de las medias pesa igual a quien hizo 43 viajes que a
    quien hizo 3, y eso no contesta "cuanto da un viaje aqui".
    """

    viajes = [
        v for m in managers.values() for v in m["trips"]["detail"]
    ]

    quietos = [
        q for m in managers.values() for q in m["held"]["detail"]
    ]

    beneficios = [v["beneficio"] for v in viajes]

    dias_de_viaje = [v["dias"] for v in viajes]

    subidas = [q["subida"] for q in quietos]

    dias_quietos = [
        q["dias"] for q in quietos if q["dias"] is not None
    ]

    return {
        "trip": {
            "n": len(viajes),
            "mean_profit": _media(beneficios),
            "median_profit": _mediana(beneficios),
            "mean_days": _media(dias_de_viaje),
            "median_days": _mediana(dias_de_viaje),
            "winners": sum(1 for b in beneficios if b > 0),
        },
        "held": {
            "n": len(quietos),
            "mean_gain": _media(subidas),
            "median_gain": _mediana(subidas),
            "mean_days": _media(dias_quietos),
            "median_days": _mediana(dias_quietos),
            "winners": sum(1 for s in subidas if s > 0),
        },
    }
