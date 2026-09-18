"""
La caja de los siete, reconstruida desde el dia 1 del tablon.

SINTOMA

    10/09/2026: la pantalla publicaba 4,37 M de caja nuestra y el
    saldo real de la API eran 4.474.383. Cien mil exactos.

    De ese numero cuelgan CAJA, PATRIMONIO, TOPE, PUJA %, MAX.
    VISTO y AMENAZA: media pantalla colgando de un dato torcido.

CAUSA

    El abono de jornada se DERIVABA de los puntos totales:

        abono = puntos x 30.000

    y eso se deja fuera el premio por puesto. Medido sobre las
    cuatro jornadas que pagaron, los siete managers, sin una sola
    excepcion:

        5o de 7   +100.000
        6o de 7   +250.000
        7o de 7   +500.000

    Nosotros fuimos 5os en la Jornada 2. Cien mil.

CONSECUENCIA

    Aqui no se deriva nada: se LEE lo que el tablon dice que se
    pago, evento a evento. `roundFinished` trae el importe exacto
    -premio incluido- y ademas permite ver que jornada pago y
    cual no.

LA JORNADA PARTIDA NO PAGA

    `splitRound: "ignoreFirst"` en los ajustes de la liga. La
    Jornada 1 se jugo en dos partes y la liga ignora la primera.
    Confirmacion cruzada: es la unica jornada que no pago premio
    por puesto a NADIE.

SIN ESTADO, A PROPOSITO

    Se replica desde el `leagueReset` en cada vuelta. No hay
    acumulado, no hay libro en `data/`. Son 33 dias de eventos y
    cuesta milisegundos.

    El motivo no es la elegancia: el libro vivia en una cache de
    CI que puede RETROCEDER, y un saldo que retrocede en silencio
    es lo peor que le puede pasar a este sistema. Reconstruido
    entero, un evento perdido se ve; acumulado, se hereda.

SI NO SE PUEDE, SE DICE

    Doctrina 36. Sin eventos no hay caja: `available: False` y la
    columna dice SIN DATO. No se vuelve al metodo viejo ni se
    pinta una estimacion con la misma cara que un numero medido.
"""

from __future__ import annotations

import collections


# ============================================================
# LO MEDIDO
# ============================================================

# El reparto del `leagueReset` del 09/08/2026. Despejado de
# nuestro saldo real y cuadrado al euro sobre 24 dias.
SALDO_INICIAL = 23_300_000

EUROS_POR_PUNTO = 30_000

# Medido sobre 4 jornadas x 7 managers, 12 de 12 casos y ni una
# excepcion. Es el premio de consolacion por quedar atras.
PREMIO_POR_PUESTO = {
    5: 100_000,
    6: 250_000,
    7: 500_000,
}

# `settings.splitRound` de la liga, leido el 10/09/2026.
REPARTO_PARTIDO = "ignoreFirst"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _lista(contenido) -> list:
    if isinstance(contenido, dict):
        return [contenido]
    return contenido or []


# ============================================================
# QUE JORNADAS PAGAN
# ============================================================


def jornadas_que_pagan(
    eventos: list,
    split_round: str = REPARTO_PARTIDO,
) -> set:
    """
    Los `round.id` cuyo abono cuenta.

    Con `ignoreFirst`, de una jornada partida solo paga la ULTIMA
    parte. Se agrupan por el nombre corto -"J1"- y de cada grupo
    se descarta todo menos la parte mas alta.
    """

    por_nombre = collections.defaultdict(list)

    for evento in eventos or []:

        if (evento or {}).get("type") != "roundFinished":
            continue

        for bloque in _lista(evento.get("content")):

            if not isinstance(bloque, dict):
                continue

            ronda = bloque.get("round") or {}

            ident = ronda.get("id")

            if ident is None:
                continue

            # AGRUPAR POR JORNADA, NO POR NOMBRE LITERAL.
            #
            # El evento de la primera parte NO trae `short`:
            #
            #     {"id": 4899, "name": "Jornada 1"}
            #     {"id": 4937, "name": "Jornada 1 (aplazada)",
            #      "short": "J1", "part": 2}
            #
            # Agrupando por el nombre crudo caian en grupos
            # distintos, no se detectaba la jornada partida y la
            # caja salia 870.000 de mas. Se quita el parentesis.
            # EL NOMBRE MANDA, `short` es el respaldo.
            #
            # Ninguno de los dos eventos reales trae `short`:
            #
            #     {"id": 4899, "name": "Jornada 1"}
            #     {"id": 4937, "name": "Jornada 1 (aplazada)",
            #      "part": 2}
            #
            # Se agrupan quitando el parentesis. Si `short`
            # tuviera prioridad y apareciera en uno solo -como
            # llego a pasar escribiendo esto- los dos caerian en
            # grupos distintos y la jornada partida volveria a
            # pagar.
            nombre = str(ronda.get("name") or "").split("(")[0]

            corto = (
                nombre.strip()
                or str(ronda.get("short") or ident).strip()
            )

            por_nombre[corto].append(
                (safe_int(ronda.get("part"), 1), ident)
            )

    pagan = set()

    for corto, partes in por_nombre.items():

        if split_round == "ignoreFirst" and len(set(partes)) > 1:
            # Solo la ultima parte paga.
            pagan.add(max(partes)[1])

        else:
            for _, ident in partes:
                pagan.add(ident)

    return pagan


# ============================================================
# LA RECONSTRUCCION
# ============================================================


def reconstruir(
    eventos: list,
    managers: list | None = None,
    saldo_inicial: int = SALDO_INICIAL,
    split_round: str = REPARTO_PARTIDO,
) -> dict:
    """
    La caja de cada manager desde el dia 1. Forma fija, nunca
    lanza.

        caja = inicial
             + jornada (lo que el tablon dice que se pago)
             + ventas
             + racha diaria
             - compras

    `bettingPool` NO entra: son quinielas globales de Biwenger y
    el premio es en CREDITOS de la app, no en euros de la liga.
    Medido: `global: true`, `credits: {required: 1}`, y los
    `winners` cuentan miles de usuarios de fuera.
    """

    vacio = {
        "available": False,
        "initial_balance": saldo_inicial,
        "managers": {},
        "reason": None,
        "events_read": 0,
        "ignored_rounds": [],
    }

    try:
        filas = [e for e in (eventos or []) if isinstance(e, dict)]

        if not filas:
            return {
                **vacio,
                "reason": (
                    "El tablon llega vacio: sin eventos no hay "
                    "caja que reconstruir."
                ),
            }

        pagan = jornadas_que_pagan(filas, split_round)

        libro = collections.defaultdict(
            lambda: {
                "matchday": 0,
                "matchday_premium": 0,
                "sales": 0,
                "purchases": 0,
                "streak": 0,
                "sales_count": 0,
                "purchases_count": 0,
            }
        )

        ignoradas = []

        # EL TABLON REPITE, Y EL ALMACEN ACUMULA (10/09/2026)
        #
        #     `stable_event_id` hashea el evento ENTERO, con su
        #     `content`. Cuando Biwenger reemite el mismo hecho
        #     con el payload cambiado -una puja mas en `bids`,
        #     unos puntos corregidos tras un aplazamiento- el
        #     hash cambia, el merge lo guarda como evento NUEVO y
        #     el almacen se queda con los dos.
        #
        #     En local eran 241 eventos limpios. En produccion,
        #     que lleva semanas acumulando, 468. Y la primera
        #     version de esto deduplicaba las compras y las
        #     ventas pero NO las jornadas: la J2 y la J3 se
        #     pagaron dos veces y la caja salio 2.860.000 de mas.
        #
        #     Asi que se deduplica TODO lo que suma o resta, por
        #     su identidad logica y no por el id del evento.
        vistos = set()

        repetidos = 0

        # Las jornadas, aparte: de cada `round.id` se queda la
        # ultima version que llegue. Asi una correccion de puntos
        # -que es a lo que se debe la reemision- sustituye a la
        # anterior en vez de sumarse a ella.
        jornadas = {}

        for evento in sorted(
            filas, key=lambda e: safe_int(e.get("date"))
        ):

            tipo = evento.get("type")

            contenido = _lista(evento.get("content"))

            # --------------------------------------------
            # COMPRAS Y VENTAS
            # --------------------------------------------
            if tipo in ("market", "transfer"):

                for op in contenido:

                    if not isinstance(op, dict):
                        continue

                    de = (op.get("from") or {}).get("id")
                    a = (op.get("to") or {}).get("id")
                    importe = safe_int(op.get("amount"))

                    clave = (
                        tipo,
                        safe_int(evento.get("date")),
                        op.get("player"),
                        de,
                        a,
                        importe,
                    )

                    if clave in vistos:
                        repetidos += 1
                        continue

                    vistos.add(clave)

                    # `market` = compra al mercado: paga `to`.
                    # `transfer` sin `to` = venta al Computer.
                    # `transfer` con `to` = venta entre usuarios.
                    if tipo == "transfer" and de:
                        libro[de]["sales"] += importe
                        libro[de]["sales_count"] += 1

                    if a:
                        libro[a]["purchases"] += importe
                        libro[a]["purchases_count"] += 1

            # --------------------------------------------
            # LA JORNADA, LEIDA Y NO DERIVADA
            # --------------------------------------------
            elif tipo == "roundFinished":

                for bloque in contenido:

                    if not isinstance(bloque, dict):
                        continue

                    ronda = bloque.get("round") or {}

                    if ronda.get("id") not in pagan:
                        nombre = ronda.get("name")
                        if nombre and nombre not in ignoradas:
                            ignoradas.append(nombre)
                        continue

                    # La ultima gana: los eventos vienen
                    # ordenados por fecha, asi que una correccion
                    # de puntos sustituye a la version anterior
                    # en vez de sumarse a ella.
                    if ronda["id"] in jornadas:
                        repetidos += 1

                    jornadas[ronda["id"]] = bloque

            # --------------------------------------------
            # LA RACHA DIARIA
            # --------------------------------------------
            elif tipo == "bonus":

                for op in contenido:

                    if not isinstance(op, dict):
                        continue

                    quien = (op.get("user") or {}).get("id")

                    if not quien:
                        continue

                    importe = safe_int(op.get("amount"))

                    clave = (
                        "bonus",
                        safe_int(evento.get("date")),
                        quien,
                        importe,
                        op.get("reason"),
                    )

                    if clave in vistos:
                        repetidos += 1
                        continue

                    vistos.add(clave)

                    libro[quien]["streak"] += importe

        # AHORA SE PAGAN LAS JORNADAS, una sola vez cada una.
        for bloque in jornadas.values():

            for fila in bloque.get("results") or []:

                if not isinstance(fila, dict):
                    continue

                quien = (fila.get("user") or {}).get("id")

                if not quien:
                    continue

                pagado = safe_int(fila.get("bonus"))

                libro[quien]["matchday"] += pagado

                # El premio por puesto, aparte, para poder
                # auditarlo sin desmontar el libro. No se deduce
                # de la posicion: se resta, porque en la J2 hay
                # dos empatados a 28 puntos con premios
                # distintos.
                libro[quien]["matchday_premium"] += (
                    pagado
                    - safe_int(fila.get("points"))
                    * EUROS_POR_PUNTO
                )

        # Los managers que no movieron nada tambien tienen caja.
        for quien in managers or []:
            libro[safe_int(quien)]

        salida = {}

        for quien, fila in libro.items():

            if not quien:
                continue

            caja = (
                saldo_inicial
                + fila["matchday"]
                + fila["sales"]
                + fila["streak"]
                - fila["purchases"]
            )

            salida[quien] = {
                **fila,
                "cash": caja,
                "initial_balance": saldo_inicial,
            }

        return {
            "available": True,
            "initial_balance": saldo_inicial,
            "managers": salida,
            "events_read": len(filas),

            # CUANTAS REPETICIONES SE HAN DESCARTADO.
            #
            # No vale contar "eventos distintos" por su
            # contenido: la reemision de Biwenger cambia el
            # payload -mete una puja mas en `bids`- asi que dos
            # copias del mismo hecho parecen distintas. Lo que se
            # cuenta aqui es lo que la reconstruccion ha
            # colapsado por identidad LOGICA, que es lo que
            # delata un almacen acumulando.
            "repeats_skipped": repetidos,

            # Y las jornadas: cuantas llegaron y cuantas pagan.
            "rounds_seen": len(jornadas) + len(ignoradas),
            "rounds_paid": len(jornadas),
            "ignored_rounds": ignoradas,
            "reason": (
                f"Caja de {len(salida)} managers reconstruida "
                f"desde el dia 1 sobre {len(filas)} eventos"
                + (
                    f"; sin pagar {', '.join(ignoradas)}"
                    if ignoradas
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo reconstruir la caja: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# QUIEN SE HA LLEVADO EL DESCUADRE
# ============================================================
#
# UNA FOTO DICE QUE ALGO ESTA MAL, NUNCA POR QUE (doctrina 48)
#
#     El 18/09/2026 la caja se separo 420.200 EUR y la pantalla
#     publico eso: 420.200. Nada mas. Con ese numero no se puede
#     hacer nada: no dice si sobra un cobro o falta un pago, ni
#     de que dia, ni de quien.
#
#     Lo buscamos a mano y estaba en un minuto: una venta al
#     Computer de Lunin -jugador 15289- por 420.200 EUR, el mismo
#     18/09 a las 07:03. El importe cuadraba al euro.
#
#     Si se encuentra a mano en un minuto, lo encuentra el
#     programa. Esto no decide nada: solo deja dicho a que mirar.
#
# LA RENDIJA CONOCIDA: LA REEMISION CON OTRA FECHA
#
#     La reja de duplicados es la clave
#     `(tipo, fecha, jugador, de, a, importe)`, y lleva la FECHA
#     dentro. Biwenger reemite la misma operacion minutos despues
#     con otro `event_id` y otro `date`, asi que la copia entra
#     como un hecho nuevo y el dinero se cuenta dos veces.
#
#     No es una hipotesis: en el tablon del 18/09 ya habia seis
#     grupos asi, con separaciones de dos a nueve minutos —el
#     jugador 31069 aparece TRES veces—. Lo que cambio ese dia es
#     que por primera vez le toco a una venta NUESTRA, que es la
#     unica caja contra la que se puede comprobar.
#
#     Por eso se buscan las dos cosas: el importe exacto, y los
#     grupos que la reja no puede ver.


TIPOS_ECONOMICOS = ("market", "transfer", "bonus")


# CUANTO TARDA BIWENGER EN REEMITIR
#
#     Los seis grupos medidos en el tablon del 18/09 se separan
#     entre 2m34s y 4m45s. Ninguno pasa de cinco minutos.
#
#     La ventana existe porque sin ella la racha diaria sale
#     marcada: 250.000 EUR al mismo manager el lunes y el martes
#     tienen la misma clave y son dos cobros de verdad, no una
#     copia. Una hora separa las dos cosas con holgura de sobra
#     por los dos lados.
VENTANA_REEMISION = 3_600


def _operaciones(eventos: list) -> list[dict]:
    """Cada movimiento de dinero del tablon, aplanado."""

    filas = []

    for evento in eventos or []:

        if not isinstance(evento, dict):
            continue

        tipo = evento.get("type")

        if tipo not in TIPOS_ECONOMICOS:
            continue

        for op in _lista(evento.get("content")):

            if not isinstance(op, dict) or "amount" not in op:
                continue

            filas.append(
                {
                    "type": tipo,
                    "date": safe_int(evento.get("date")),
                    "event_id": evento.get("event_id"),
                    "player": op.get("player"),
                    "from": (op.get("from") or {}).get("id"),
                    "from_name": (op.get("from") or {}).get("name"),
                    "to": (op.get("to") or {}).get("id"),
                    "to_name": (op.get("to") or {}).get("name"),
                    "user": (op.get("user") or {}).get("id"),
                    "amount": safe_int(op.get("amount")),
                }
            )

    return filas


def sospechosos(
    eventos: list,
    diferencia,
    *,
    manager=None,
    limite: int = 6,
) -> list[dict]:
    """
    Que evento explica el descuadre. El concreto, con su importe.

    Devuelve una lista ordenada de mas a menos sospechoso. Vacia
    significa "no se ha encontrado", que tambien es una respuesta
    y se publica como tal. Nunca lanza: esto informa, no decide.
    """

    salida = []

    try:
        objetivo = abs(safe_int(diferencia))

        if not objetivo:
            return []

        filas = _operaciones(eventos)

        if not filas:
            return []

        # ----------------------------------------------------
        # 1. EL IMPORTE, CLAVADO
        # ----------------------------------------------------
        for fila in filas:

            if fila["amount"] != objetivo:
                continue

            nuestro = manager is None or manager in (
                fila["from"],
                fila["to"],
                fila["user"],
            )

            salida.append(
                {
                    **fila,
                    "match": "IMPORTE_EXACTO",
                    "ours": nuestro,
                }
            )

        # ----------------------------------------------------
        # 2. LA MISMA OPERACION CON DOS FECHAS
        # ----------------------------------------------------
        #
        # La reja no las ve porque lleva la fecha dentro. Se
        # publican aunque su importe no cuadre con la diferencia:
        # son la averia conocida y hay que poder contarlas.
        grupos = collections.defaultdict(list)

        for fila in filas:

            grupos[
                (
                    fila["type"],
                    fila["player"],
                    fila["from"],
                    fila["to"],
                    fila["user"],
                    fila["amount"],
                )
            ].append(fila)

        for clave, repetidas in grupos.items():

            fechas = sorted({fila["date"] for fila in repetidas})

            if len(fechas) < 2:
                continue

            # Se parte en rachas: solo cuenta como reemision lo
            # que llega PEGADO. Dos cobros iguales con dias por
            # medio son dos cobros, no una copia.
            racha = [fechas[0]]

            rachas = [racha]

            for anterior, siguiente in zip(fechas, fechas[1:]):

                if siguiente - anterior <= VENTANA_REEMISION:
                    racha.append(siguiente)

                else:
                    racha = [siguiente]
                    rachas.append(racha)

            copias = max(len(r) for r in rachas)

            if copias < 2:
                continue

            pegadas = [r for r in rachas if len(r) > 1]

            primera = repetidas[0]

            nuestro = manager is None or manager in (
                primera["from"],
                primera["to"],
                primera["user"],
            )

            salida.append(
                {
                    **primera,
                    "match": "REEMITIDA_CON_OTRA_FECHA",
                    "ours": nuestro,
                    "copies": copias,
                    "dates": sorted(
                        fecha
                        for grupo in pegadas
                        for fecha in grupo
                    ),

                    # Lo que se cuenta de mas si las copias no se
                    # colapsan: el importe por cada copia extra.
                    "overcount": primera["amount"]
                    * sum(len(r) - 1 for r in pegadas),
                }
            )

        # Primero lo nuestro -es la unica caja comprobable-,
        # despues el importe clavado, y dentro de eso lo reciente.
        salida.sort(
            key=lambda fila: (
                not fila["ours"],
                fila["match"] != "IMPORTE_EXACTO",
                -fila["date"],
            )
        )

        return salida[:limite]

    except Exception:                               # noqa: BLE001
        return []


# ============================================================
# LA COMPROBACION PERMANENTE
# ============================================================


def cuadra(
    caja_reconstruida,
    saldo_real,
    *,
    eventos: list | None = None,
    manager=None,
) -> dict:
    """
    Nuestra caja reconstruida contra el saldo real de la API.

    Es la UNICA auditoria posible de un numero que no podemos
    ver: la liga tiene `settings.balance = "hidden"`, asi que de
    los seis rivales no hay saldo contra el que contrastar. Si el
    metodo acierta con el nuestro, acierta con el suyo.

    Y ya demostro que funciona: fue esta comparacion la que
    encontro el `splitRound`, con un hueco de 870.000 clavados.
    """

    # EL SALDO CONTRA EL QUE SE COMPARA TIENE QUE SER DE AHORA
    #
    #     12/09/2026: la alarma salio en ROJO por 140.977 EUR y
    #     la reconstruccion era CORRECTA — coincidia al euro con
    #     el saldo real de la API. Lo que estaba viejo era el
    #     otro lado: se comparaba contra el `balance` de la FOTO,
    #     y entre la foto y ahora habian entrado dos compras del
    #     reset (390.977) y una racha diaria (250.000).
    #
    #     Un rojo falso gasta la confianza igual que un verde
    #     falso, y peor: ensena a no mirar la alarma. Asi que el
    #     saldo se pide fresco, y si no se puede pedir, NO se
    #     compara contra uno viejo: se dice que no se sabe.
    if caja_reconstruida is None or saldo_real is None:
        return {
            "available": False,
            "ok": None,
            "reason": (
                "Sin las dos cifras no hay comprobacion: no se "
                "sabe si la caja cuadra."
            ),
        }

    mia = safe_int(caja_reconstruida)
    real = safe_int(saldo_real)
    diferencia = mia - real

    def _euros(valor) -> str:
        return f"{int(valor):,}".replace(",", ".")

    if diferencia == 0:

        return {
            "available": True,
            "ok": True,
            "reconstructed": mia,
            "real": real,
            "difference": 0,
            "suspects": [],
            "suspect_types": [],
            "reason": (
                f"La caja reconstruida cuadra con el saldo real "
                f"({_euros(real)} EUR)."
            ),
        }

    # NO CUADRA: HAY QUE DECIR A QUE MIRAR
    #
    #     El numero solo no sirve para nada. Se busca el evento
    #     concreto y su tipo, y si no aparece se dice que no
    #     aparece —que tambien es una respuesta, y ademas es una
    #     pista: significa que no es un importe suelto.
    pistas = sospechosos(eventos, diferencia, manager=manager)

    tipos = sorted({pista["type"] for pista in pistas})

    clavado = next(
        (
            pista
            for pista in pistas
            if pista["match"] == "IMPORTE_EXACTO"
        ),
        None,
    )

    if clavado is not None:

        sobra = (
            "sobra un cobro"
            if diferencia > 0
            else "falta un pago"
        )

        detalle = (
            f" Cuadra al euro con un evento `{clavado['type']}` "
            f"del jugador {clavado['player']} por "
            f"{_euros(clavado['amount'])} EUR: {sobra}."
        )

    elif pistas:

        detalle = (
            f" Sin un importe que cuadre al euro. Lo que si hay: "
            f"{len(pistas)} operacion(es) reemitidas con otra "
            f"fecha, del tipo {', '.join(tipos)}, que la reja de "
            f"duplicados no puede ver porque lleva la fecha "
            f"dentro."
        )

    else:

        detalle = (
            " Ningun evento suelto cuadra con la diferencia, ni "
            "hay reemisiones con otra fecha: no es un importe "
            "perdido, hay que mirar el metodo."
        )

    return {
        "available": True,
        "ok": False,
        "reconstructed": mia,
        "real": real,
        "difference": diferencia,

        # EL TIPO DE EVENTO SOSPECHOSO, NO SOLO EL NUMERO.
        "suspects": pistas,
        "suspect_types": tipos,

        "reason": (
            f"LA CAJA NO CUADRA: reconstruida "
            f"{_euros(mia)} EUR contra {_euros(real)} EUR "
            f"reales. Se separan {_euros(abs(diferencia))} "
            f"EUR. Si el metodo falla con el nuestro, la caja "
            f"de los seis rivales tampoco vale."
            + detalle
        ),
    }
