"""
Las pujas del dueno: verlas aunque no las haya puesto Pepe.

EL INCIDENTE (10/09/2026)

    El dueno pujo a mano por Aubameyang, 11,8 M. En la foto de
    las 07:52 Pepe no la veia por ningun lado:

        has_live_bid: false   en todos los objetivos
        maximumBid:   intacto
        reloj:        "Saldo positivo (3.315.383 EUR).
                       El plazo no aprieta."

    Y no es un caso raro: el dueno va a seguir pujando cuando le
    apetezca. Mientras Pepe no lo vea, planifica ventas, deuda y
    presupuesto de fichar sobre un dinero que ya esta gastado.

LO QUE SE VE DESDE FUERA, MEDIDO EL 16/08/2026

        17:01:54   saldo 239.968   maximumBid 12.404.968
           -> puja de 480.000 por Iker Munoz
        17:02:24   saldo 239.968   maximumBid 11.924.968

    El saldo NO se mueve. `maximumBid` baja EXACTAMENTE el
    importe comprometido. La informacion estaba delante y nadie
    la leia.

TRES VIAS, Y LAS TRES SE PUBLICAN

    A. EL TABLON. `market.offers` filtrado por direccion. Es la
       via barata: viene de la API, no se deduce nada. Pero solo
       ve lo que Biwenger publique en ese sitio.

    B. LA RESTA ABSOLUTA.

           comprometido = saldo + linea_de_credito - maximumBid

       Necesita conocer la linea de credito, y por eso hubo que
       medirla antes de escribir esto (ver abajo).

    C. LA DIFERENCIA ENTRE FOTOS. No necesita la linea de
       credito, y por eso es la mas solida: entre dos fotos SIN
       RESET por medio, si el saldo no se mueve y `maximumBid`
       baja X, alguien ha comprometido X.

    Cuando discrepan manda LA MAS CONSERVADORA: la que diga que
    hay mas dinero comprometido. Nunca la optimista. Equivocarse
    por arriba cuesta no pujar un dia; por abajo cuesta llegar a
    la jornada en rojo.

LA LINEA DE CREDITO: MEDIDA, NO SUPUESTA

    El encargo avisaba de la trampa -dar por hecho que el margen
    es el 25 % del valor de plantilla- y pedia medirlo. Medido
    sobre las 85 fotos del 12 al 17/08, que dan 12 estados
    distintos de (saldo, maximumBid, plantilla, comprometido):

        maximumBid == saldo + valor_plantilla/4 - comprometido

        EXACTO AL EURO en los 12. Con saldo positivo y negativo,
        con plantillas de 15, 16 y 17 fichas, y con pujas vivas
        de 480.000, 984.000, 1.740.001 y 3.126.002 -numeros con
        desvio, no redondos-.

    Y LOS LISTADOS CUENTAN. En las 85 fotos habia jugadores
    nuestros publicados en el mercado; siguen en `my_team` y
    entran en la cuenta A PRECIO DE MERCADO, no al precio que
    pedimos por ellos. Si no contaran, el ratio no habria salido
    exacto ni una vez.

    LO QUE NO SE PUEDE AFIRMAR: si redondea hacia arriba, hacia
    abajo o al mas cercano. Todos los precios de Biwenger son
    multiplos de 10.000, asi que el 25 % siempre cae exacto y no
    hay ni un caso que separe las tres posibilidades. Se usa
    division entera y se dice aqui.

ESTE MODULO NO LEE EL MUNDO

    Ni disco, ni red, ni reloj: todo se le pasa. Forma fija.
    Nunca lanza.
"""

from __future__ import annotations


# ============================================================
# LA LINEA DE CREDITO
# ============================================================
#
#     No es un umbral: es una medida. 12 estados distintos, 12
#     aciertos al euro. Si algun dia Biwenger la cambia, esta
#     constante se queda corta y las guardias se ponen rojas,
#     que es exactamente lo que tiene que pasar.
LINEA_DE_CREDITO = 0.25

ESTADOS_MEDIDOS = 12

MEDIDO_EL = "16/08/2026 y 12-17/08/2026"


# Las tres vias, por nombre, para que la pantalla no invente
# etiquetas por su cuenta.
TABLON = "TABLON"
RESTA = "RESTA"
DIFERENCIA = "DIFERENCIA"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _vacia(via: str, motivo: str) -> dict:
    return {
        "available": False,
        "source": via,
        "committed": 0,
        "reason": motivo,
    }


# ============================================================
# VIA A — EL TABLON
# ============================================================

def por_el_tablon(exposicion: dict | None) -> dict:
    """
    Lo que Biwenger publica de nuestras propias pujas.

    Se le pasa el resultado de `build_bid_exposure`, que ya sabe
    distinguir una puja nuestra de una oferta entrante y de una
    contraoferta.

    LO QUE ESTA VIA NO PUEDE HACER

        Decir que NO hay pujas. Solo puede decir que no ve
        ninguna. El 10/09 no vio la de Aubameyang, y por eso
        existen las otras dos.
    """

    datos = exposicion if isinstance(exposicion, dict) else {}

    if not datos.get("available"):
        return _vacia(
            TABLON,
            (
                datos.get("reason")
                or "No se pudo leer el tablon de ofertas."
            ),
        )

    comprometido = safe_int(datos.get("committed_total"))

    operaciones = safe_int(datos.get("operation_count"))

    return {
        "available": True,
        "source": TABLON,
        "committed": comprometido,
        "operations": operaciones,
        "reason": (
            f"El tablon publica {operaciones} puja(s) nuestras "
            f"por {_euros(comprometido)} EUR."
            if operaciones
            else (
                "El tablon no publica ninguna puja nuestra. Eso "
                "no prueba que no la haya."
            )
        ),
    }


# ============================================================
# VIA B — LA RESTA ABSOLUTA
# ============================================================

def por_la_resta(
    balance,
    maximum_bid,
    valor_plantilla,
    linea: float = LINEA_DE_CREDITO,
) -> dict:
    """
    saldo + linea_de_credito - maximumBid = comprometido.

    Necesita las tres cifras. Sin el valor de la plantilla no se
    puede calcular la linea, y sin la linea esta via no vale
    para decidir nada: lo dice y se aparta.
    """

    saldo = safe_int(balance)

    tope = safe_int(maximum_bid)

    valor = safe_int(valor_plantilla)

    if tope <= 0 or valor <= 0:
        return _vacia(
            RESTA,
            (
                "Sin maximumBid o sin valor de plantilla no se "
                "puede restar."
            ),
        )

    # Division entera: no se puede afirmar como redondea Biwenger
    # (todos los precios son multiplos de 10.000 y el 25 % cae
    # siempre exacto), asi que no se finge una precision que no
    # se ha medido.
    margen = int(valor * linea)

    bruto = saldo + margen

    comprometido = bruto - tope

    # UNA PUJA NEGATIVA NO EXISTE
    #
    #     Si sale negativo es que la linea de credito no es la
    #     que creemos, o el valor de plantilla no cuadra. Se
    #     publica cero y se dice, en vez de publicar un numero
    #     imposible.
    if comprometido < 0:
        return {
            "available": True,
            "source": RESTA,
            "committed": 0,
            "credit_line": margen,
            "mismatch": comprometido,
            "reason": (
                f"La resta da {_euros(comprometido)} EUR, que no "
                f"puede ser: la linea de credito medida no cuadra "
                f"con esta foto. Se publica cero y no se decide "
                f"nada con esta via."
            ),
        }

    return {
        "available": True,
        "source": RESTA,
        "committed": comprometido,
        "credit_line": margen,
        "mismatch": 0,
        "reason": (
            f"{_euros(saldo)} de saldo + {_euros(margen)} de "
            f"margen - {_euros(tope)} de maximumBid = "
            f"{_euros(comprometido)} EUR comprometidos."
        ),
    }


# ============================================================
# VIA C — LA DIFERENCIA ENTRE DOS FOTOS
# ============================================================

def por_la_diferencia(antes: dict | None, ahora: dict | None) -> dict:
    """
    Dos fotos, sin reset por medio, y el saldo quieto.

    Es el par del 16/08 convertido en regla. No necesita saber
    cuanto vale la linea de credito ni cuanto vale la plantilla:
    entre dos fotos sin reset los precios no se mueven, asi que
    si el saldo esta quieto y `maximumBid` baja, lo unico que ha
    podido bajarlo es una puja.

    LAS DOS CONDICIONES QUE LA INVALIDAN

        1. Un reset por medio. Los precios cambian y `maximumBid`
           se mueve por si solo. Se detecta porque la cuenta
           atras del reset SUBE en vez de bajar.

        2. El saldo se ha movido. Ha entrado o salido dinero -una
           venta, una compra, el abono de la jornada- y la resta
           deja de medir pujas.

    En los dos casos devuelve `available: False` con el motivo.
    No adivina.
    """

    a = antes if isinstance(antes, dict) else {}
    b = ahora if isinstance(ahora, dict) else {}

    tope_antes = safe_int(a.get("maximum_bid"))
    tope_ahora = safe_int(b.get("maximum_bid"))

    if tope_antes <= 0 or tope_ahora <= 0:
        return _vacia(
            DIFERENCIA,
            "Hacen falta dos fotos con maximumBid.",
        )

    saldo_antes = safe_int(a.get("balance"))
    saldo_ahora = safe_int(b.get("balance"))

    if saldo_antes != saldo_ahora:
        return _vacia(
            DIFERENCIA,
            (
                f"El saldo se ha movido "
                f"({_euros(saldo_antes)} -> "
                f"{_euros(saldo_ahora)}): la resta ya no mide "
                f"pujas."
            ),
        )

    reset_antes = safe_float(a.get("hours_to_reset"))
    reset_ahora = safe_float(b.get("hours_to_reset"))

    if (
        reset_antes is not None
        and reset_ahora is not None
        and reset_ahora > reset_antes
    ):
        return _vacia(
            DIFERENCIA,
            (
                f"Ha habido un reset por medio (la cuenta atras "
                f"paso de {reset_antes:.1f} h a {reset_ahora:.1f} "
                f"h): los precios han cambiado y maximumBid se "
                f"mueve solo."
            ),
        )

    bajada = tope_antes - tope_ahora

    if bajada <= 0:
        return {
            "available": True,
            "source": DIFERENCIA,
            "committed": 0,
            "delta": bajada,
            "reason": (
                "Entre las dos fotos maximumBid no ha bajado: "
                "nadie ha comprometido nada nuevo."
            ),
        }

    return {
        "available": True,
        "source": DIFERENCIA,
        "committed": bajada,
        "delta": bajada,
        "reason": (
            f"Mismo saldo ({_euros(saldo_ahora)} EUR) y "
            f"maximumBid baja {_euros(bajada)} EUR: alguien ha "
            f"comprometido {_euros(bajada)} EUR."
        ),
    }


# ============================================================
# LAS TRES JUNTAS, Y MANDA LA MAS CONSERVADORA
# ============================================================

def pujas_comprometidas(
    exposicion: dict | None = None,
    balance=None,
    maximum_bid=None,
    valor_plantilla=None,
    antes: dict | None = None,
    ahora: dict | None = None,
) -> dict:
    """
    Cuanto dinero nuestro esta comprometido en pujas vivas.

    Las tres vias se publican enteras, y el numero que sale
    arriba es EL MAYOR de los que estan disponibles.

    POR QUE EL MAYOR Y NO UNA MEDIA

        Una media entre "hay 11,8 M comprometidos" y "no veo
        nada" da 5,9 M, que no es verdad en ningun mundo. El
        error caro es el optimista: creer que hay dinero que no
        hay y llegar a la jornada en rojo.

    Forma fija. Nunca lanza.
    """

    try:
        vias = {
            TABLON: por_el_tablon(exposicion),
            RESTA: por_la_resta(
                balance, maximum_bid, valor_plantilla
            ),
            DIFERENCIA: por_la_diferencia(antes, ahora),
        }

        disponibles = {
            nombre: via
            for nombre, via in vias.items()
            if via.get("available")
        }

        if not disponibles:
            return {
                "available": False,
                "committed": 0,
                "source": None,
                "sources": vias,
                "disagreement": 0,
                "reason": (
                    "Ninguna de las tres vias ha podido medir: "
                    "no se sabe si hay pujas comprometidas."
                ),
            }

        manda = max(
            disponibles.items(),
            key=lambda par: safe_int(par[1].get("committed")),
        )

        importes = [
            safe_int(v.get("committed"))
            for v in disponibles.values()
        ]

        discrepancia = max(importes) - min(importes)

        return {
            "available": True,
            "committed": safe_int(manda[1].get("committed")),
            "source": manda[0],
            "sources": vias,

            # Cuanto se llevan entre si. Si esto no es cero, hay
            # una via que no ve lo que ven las otras y conviene
            # mirarlo antes de que decida algo.
            "disagreement": discrepancia,

            "reason": (
                f"{_euros(safe_int(manda[1].get('committed')))} "
                f"EUR comprometidos segun la via "
                f"{manda[0]}"
                + (
                    f", y las vias no coinciden (se llevan "
                    f"{_euros(discrepancia)} EUR): manda la mas "
                    f"conservadora."
                    if discrepancia
                    else ", y las tres coinciden."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "committed": 0,
            "source": None,
            "sources": {},
            "disagreement": 0,
            "reason": (
                f"No se pudieron contar las pujas: "
                f"{type(error).__name__}: {error}"
            ),
        }


def capacidad_de_pujar(
    maximum_bid,
    cash_budget=None,
    comprometido=0,
) -> dict:
    """
    Con cuanto se puede pujar de verdad.

    LA REGLA: SOBRE `maximumBid`, NO SOBRE EL SALDO

        `maximumBid` ya viene con las pujas vivas descontadas
        -medido el 16/08-. Es la unica pared que no es nuestra y
        la unica cifra que no se puede gastar dos veces.

        El saldo, en cambio, no sabe nada de pujas: si el dueno
        ha comprometido 11,8 M, la caja sigue diciendo lo mismo
        que antes y quien reparta por caja repartira dinero que
        ya esta gastado.

    LA CAJA EFECTIVA

        `cash_budget` sale de `max(balance, 0) * porcentaje`, y
        el balance no ve las pujas. Aqui se le resta lo
        comprometido: es el mismo umbral de antes sobre una
        entrada que ya no miente.

    Forma fija. Nunca lanza.
    """

    tope = safe_int(maximum_bid)

    gastado = max(0, safe_int(comprometido))

    caja = safe_int(cash_budget)

    efectiva = max(0, caja - gastado)

    return {
        "available": tope > 0,
        "maximum_bid": tope,
        "committed": gastado,
        "cash_budget": caja,
        "effective_cash": efectiva,
        "reason": (
            f"Se puede pujar hasta {_euros(tope)} EUR "
            f"(maximumBid, que ya descuenta las pujas vivas). "
            f"De caja quedan {_euros(efectiva)} EUR: "
            f"{_euros(caja)} menos {_euros(gastado)} ya "
            f"comprometidos."
            if tope > 0
            else "Sin maximumBid no se puede decir cuanto cabe."
        ),
    }


def valor_de_plantilla(squad) -> int:
    """
    Lo que Biwenger cuenta para el margen: la plantilla entera a
    PRECIO DE MERCADO, con los listados dentro.

    Medido: en las 85 fotos del 12-17/08 habia jugadores
    nuestros publicados y el ratio salio exacto contandolos.
    """

    total = 0

    for jugador in (squad or []):

        if not isinstance(jugador, dict):
            continue

        total += safe_int(jugador.get("price"))

    return total


def _euros(valor) -> str:
    """
    El separador de miles, APARTE de la frase.

    `f"frase, {n:,}".replace(",", ".")` se come las comas de la
    prosa. Ya ha pasado cinco veces en esta casa.
    """

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"
