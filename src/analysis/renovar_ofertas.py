"""
Renovar en la ventana: mantener la liquidez sin perderla nunca.

LA MECANICA, DICHA POR EL DUENO (10/09/2026)

    "Solo puedes vender un jugador cuando alguien te hace una
     oferta. Esa oferta permanece y, hasta que caduque, puedes
     ejecutar la operacion. El dinero se recibe instantaneamente."

    "Al renovar, nace una oferta nueva y la anterior muere."

LO QUE ESO SIGNIFICA

    1. Una oferta viva es una OPCION GRATIS. Tenerla no obliga a
       nada; solo ejercerla cuesta. Es el espejo de lo que ya
       sabiamos de las pujas: perder no cuesta nada.

    2. La caducidad mata tambien la venta: si el listado expira,
       el jugador deja de recibir ofertas.

    3. Renovar mata la oferta viva, y la nueva no nace hasta el
       reset.

LOS TRES NUMEROS QUE GOBIERNAN ESTO, MEDIDOS (10/09/2026)

    Sobre las 85 fotos de produccion del 11 al 17/08, con sellos
    de tiempo del propio Biwenger:

        UN LISTADO VIVE 48,0 HORAS EXACTAS.
            47 de 47 observaciones. Ni una distinta.

        UNA OFERTA DEL COMPUTER CADUCA A LAS 07:00.
            57 de 65, clavadas.

        LA TANDA NUEVA NACE ENTRE LAS 07:03 Y LAS 07:09.
            Las 54 ofertas entrantes, siete dias seguidos.
            Mediana 07:04.

DE AHI SALE LA POLITICA, Y AFINA LA DEL ENCARGO

    El dueno propuso "renovar solo lo que caduca en ese reset".
    Midiendo se ve que la cosa es mas simple y mas barata:

        · La oferta muere a las 07:00 HAGAS LO QUE HAGAS.
          Renovar a las 06:52 mata una opcion a la que le quedan
          ocho minutos de vida. Eso no cuesta nada.

        · Lo unico que hay que proteger es que el jugador SIGA
          LISTADO cuando pase el reset, porque la tanda de las
          07:04 solo mira a los listados.

        · Y un listado dura 48 h, o sea DOS ventanas. Asi que en
          cada ventana solo hay que renovar lo que no llegaria a
          la siguiente: lo que caduca en menos de 24 h.

    Renovar lo demas no rompe nada, pero gasta una peticion y no
    compra nada. No se hace.

    Medido tambien: un listado creado a las 06:42 -18 minutos
    antes del reset- recibio su oferta a las 07:04 del mismo dia.
    Asi que renovar tarde NO deja al jugador fuera de la tanda.

ESTE MODULO NO ESCRIBE Y NO LEE EL MUNDO

    Decide y publica. Quien escribe es `renovar_executor`, que es
    un camino aparte y no comparte nada con la venta. Aqui no hay
    ni disco, ni red, ni reloj: todo se pasa. Nunca lanza.
"""

from __future__ import annotations


# ============================================================
# LO MEDIDO
# ============================================================

VIDA_DE_UN_LISTADO_HORAS = 48.0

LISTADOS_MEDIDOS = 47

VIDA_DE_UNA_OFERTA_HORAS = 48.0


# Cada cuanto vuelve a haber ventana. Es un dia: la ventana es la
# de los ultimos minutos antes del reset, y el reset es diario.
HORAS_ENTRE_VENTANAS = 24.0


# EL MARGEN, QUE NO ES UN AJUSTE
#
#     Un listado que caduca dentro de 24,5 h no llega a la
#     ventana de manana por media hora. Se le suma una hora de
#     margen para absorber que la ventana no cae siempre en el
#     mismo minuto -el cron externo se ha llegado a retrasar una
#     hora entera- y que un ciclo tarda en ejecutarse.
MARGEN_HORAS = 1.0


# LO QUE SE PIDE AL RENOVAR (10/09/2026)
#
#     RENOVAR ES TAMBIEN RE-PRECIAR. Volver a listar al precio
#     viejo deja la peticion rancia: el mercado sube y el listado
#     se queda quieto.
#
#     Y eso NO es solo feo, ROMPE la renovacion. Medido en vivo
#     el 10/09: de ocho renovaciones a mano, dos volvieron con
#     HTTP 400 -Jonny y Pablo Duran-, y eran exactamente los dos
#     que pedian POR DEBAJO de lo que valia el jugador:
#
#         Jonny         pedia 2.350.000   valia 2.370.000   400
#         Pablo Duran   pedia   400.000   valia   420.000   400
#         los otros seis pedian entre +240.000 y +740.000  OK
#
#     Biwenger rechaza listar por debajo del precio de mercado.
#
#     EL MULTIPLICADOR ES DEL DUENO (10/09). Para situarlo: las
#     trece peticiones vivas ese dia iban de 1,03 a 1,50 veces
#     el valor, con la mediana en 1,18. Cepeda estaba en 1,03 y
#     habria sido el siguiente en romperse.
#
#     Se recalcula EN CADA RENOVACION, que es todo el punto.
PRIMA_DE_LA_PETICION = 1.15


def precio_de_la_peticion(
    market_price,
    prima: float = PRIMA_DE_LA_PETICION,
) -> int:
    """
    Lo que se pide por un jugador al renovar su listado.

    Nunca por debajo del valor de mercado: eso lo rechaza
    Biwenger con un 400.
    """

    valor = max(0, safe_int(market_price))

    return int(valor * prima)


# EL TOPE POR CICLO
#
#     No es un numero a ojo: es el maximo de listados que hemos
#     tenido nunca a la vez -17, el 12/08/2026-. Renovarlos todos
#     cuesta 17 peticiones.
#
#     El ciclo gasta hoy 181 peticiones al dia (medido el 08/09).
#     Con 17 mas al dia son 198. El bloqueo del 08/09 llego a las
#     1.536 al dia: queda un factor de casi ocho.
#
#     Es un corte duro, no una recomendacion.
TOPE_DE_RENOVACIONES = 17

PETICIONES_AL_DIA_HOY = 181

PETICIONES_QUE_ROMPIERON = 1536


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


def _euros(valor) -> str:
    """El separador de miles, APARTE de la frase."""

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"


def que_renovar(
    listados: list | None,
    seconds_to_reset,
    puede_escribir: bool = False,
    cobros_de_este_ciclo: list | None = None,
    ya_renovados: list | None = None,
    deuda_contingente: int = 0,
    horas_al_inicio_de_jornada=None,
    tope: int = TOPE_DE_RENOVACIONES,
) -> dict:
    """
    Que listados hay que renovar en esta ventana, y cuales no.

    CADA FILA DE `listados` TRAE

        id, name, listed_price,
        listing_hours_to_expiry   cuanto le queda AL LISTADO
        offer_amount              la oferta viva, o 0 si no hay
        offer_hours_to_expiry     cuanto le queda A LA OFERTA

    LAS PUERTAS, EN ORDEN

        1. La ventana del reset tiene que estar abierta.
        2. La zona de silencio tiene que dejar escribir.
        3. Nunca un listado SIN oferta viva.
        4. Nunca uno que este en la cola de cobro de este ciclo:
           cobrar y renovar en la misma vuelta es perder el
           dinero.
        5. Nunca dos veces el mismo en la misma ventana.
        6. Solo lo que no llegaria a la ventana de manana.
        7. El tope duro.

    Con DEUDA CONTINGENTE la puerta 6 se relaja: se renueva todo
    lo que caduque antes de que empiece la jornada, porque esa es
    la caja con la que se tapa.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "execute": False,
        "renewals": [],
        "skipped": [],
        "at_risk": [],
        "count": 0,
        "capped_at": tope,
        "dropped_by_cap": 0,
        "mandatory": False,
        "blocked_by": None,
        "reason": None,
    }

    try:
        from src.analysis.la_subasta import ventana_abierta

        filas = [
            f for f in (listados or []) if isinstance(f, dict)
        ]

        ventana = ventana_abierta(seconds_to_reset)

        # LO QUE NO LLEGA VIVO A LA PROXIMA VENTANA
        #
        #     MEDIDO el 10/09: de los ocho listados que pedian
        #     renovacion, SIETE caducaban antes de la ventana de
        #     manana -entre 4,7 h y 16,3 h-. La ventana estaba a
        #     22 h.
        #
        #     Renovar solo en la ventana NO puede salvarlos: se
        #     mueren antes de que la ventana llegue.
        #
        #     Y renovarlos ahora tampoco es gratis: mataria una
        #     oferta con 21 h de vida por delante, que es
        #     justamente la caja con la que se tapa la deuda
        #     contingente.
        #
        #     Asi que NO se decide aqui: se publica y lo mira el
        #     dueno. En regimen normal esto no pasa -al renovar
        #     en la ventana el listado dura 48 h, o sea dos
        #     ventanas-, solo pasa en la transicion o cuando se
        #     ha perdido una ventana.
        en_riesgo = []

        for fila in filas:

            queda = safe_float(
                fila.get("listing_hours_to_expiry")
            )

            if queda is None:
                continue

            if queda <= HORAS_ENTRE_VENTANAS + MARGEN_HORAS:

                horas_ventana = (
                    safe_float(seconds_to_reset) or 0
                ) / 3600.0

                if queda < horas_ventana:
                    en_riesgo.append(
                        {
                            "id": fila.get("id"),
                            "name": fila.get("name"),
                            "listing_hours_to_expiry": queda,
                            "offer_amount": safe_int(
                                fila.get("offer_amount")
                            ),
                            "reason": (
                                f"El listado caduca en "
                                f"{queda:.1f} h y la ventana no "
                                f"llega hasta dentro de "
                                f"{horas_ventana:.1f} h: no se "
                                f"puede salvar renovando en la "
                                f"ventana."
                            ),
                        }
                    )

        # LA VENTANA YA NO RESTRINGE LA RENOVACION (10/09/2026)
        #
        #     Aqui habia una puerta: fuera de la ventana no se
        #     renovaba. Se apoyaba en que renovar mata la oferta
        #     viva, asi que habia que hacerlo cuando a esa oferta
        #     le quedaran minutos.
        #
        #     ESA PREMISA ES FALSA POR API, y esta medido en vivo:
        #     al renovar a Dituro su listado quedo nuevo -48 h- y
        #     su oferta de 2.439.000, creada el 09/09 a las 07:08,
        #     SIGUIO VIVA. Trece renovaciones ese dia, trece
        #     ofertas intactas.
        #
        #     Renovar no cuesta nada, asi que no hay motivo para
        #     esperar. Se renueva todo, todos los dias.
        #
        #     El limite diario no hace falta ponerlo: al renovar,
        #     el listado dura 48 h y deja de cumplir la puerta de
        #     "no llega a la proxima ventana" durante 23 h. Se
        #     autolimita.
        #
        #     Lo que SI sigue mandando es la zona de silencio:
        #     eso no es sobre la oferta, es sobre no escribir
        #     mientras el mercado se rehace.

        if not puede_escribir:
            return {
                **vacio,
                "available": True,
                "blocked_by": "ZONA_DE_SILENCIO",
                "reason": (
                    "La zona de silencio no deja escribir en "
                    "esta vuelta: no se renueva nada."
                ),
            }

        # DEUDA CONTINGENTE: la renovacion deja de ser una
        # comodidad y pasa a ser la caja con la que se tapa.
        obligatorio = safe_int(deuda_contingente) > 0

        limite_horas = (
            safe_float(horas_al_inicio_de_jornada)
            if obligatorio
            and safe_float(horas_al_inicio_de_jornada)
            else HORAS_ENTRE_VENTANAS + MARGEN_HORAS
        )

        en_cobro = {
            str(n).strip().lower()
            for n in (cobros_de_este_ciclo or [])
            if n
        }

        renovados = {
            str(n).strip().lower()
            for n in (ya_renovados or [])
            if n
        }

        elegidos = []
        descartados = []

        def _descartar(fila, motivo):
            descartados.append(
                {
                    "id": fila.get("id"),
                    "name": fila.get("name"),
                    "reason": motivo,
                }
            )

        for fila in filas:

            nombre = str(fila.get("name") or "").strip().lower()

            # 3. SIN OFERTA VIVA NO SE RENUEVA
            #
            #     Renovar un listado que no tiene oferta no
            #     refresca nada: el listado ya esta puesto y la
            #     oferta llegara en el reset igual. Gasta una
            #     peticion y reinicia un reloj que no hacia
            #     falta reiniciar.
            if safe_int(fila.get("offer_amount")) <= 0:
                _descartar(
                    fila,
                    "No tiene oferta viva: renovar no refresca "
                    "nada y gasta una peticion.",
                )
                continue

            # 4. PRIMERO SE COBRA, DESPUES SE RENUEVA
            if nombre in en_cobro:
                _descartar(
                    fila,
                    "Esta en la cola de cobro de este ciclo: "
                    "renovarlo seria tirar el dinero que se iba "
                    "a cobrar.",
                )
                continue

            # 5. IDEMPOTENCIA
            if nombre in renovados:
                _descartar(
                    fila,
                    "Ya se renovo en esta ventana: la segunda "
                    "mataria a la primera.",
                )
                continue

            # 6. SOLO LO QUE NO LLEGA A LA VENTANA DE MANANA
            queda = safe_float(
                fila.get("listing_hours_to_expiry")
            )

            if queda is None:
                _descartar(
                    fila,
                    "No se sabe cuanto le queda al listado: no "
                    "se toca.",
                )
                continue

            if queda > limite_horas:
                _descartar(
                    fila,
                    (
                        f"Al listado le quedan {queda:.1f} h y "
                        f"llega de sobra a la proxima ventana "
                        f"({limite_horas:.1f} h)."
                    ),
                )
                continue

            # SE RE-PRECIA AQUI, en cada renovacion.
            valor_hoy = safe_int(fila.get("market_price"))

            pedido = (
                precio_de_la_peticion(valor_hoy)
                if valor_hoy > 0
                else safe_int(fila.get("listed_price"))
            )

            elegidos.append(
                {
                    "id": fila.get("id"),
                    "name": fila.get("name"),
                    "listed_price": pedido,
                    "precio_anterior": safe_int(
                        fila.get("listed_price")
                    ),
                    "market_price": valor_hoy,
                    "listing_hours_to_expiry": queda,

                    # LO QUE MUERE AL RENOVAR, apuntado antes de
                    # matarlo: si manana esto sale mal hay que
                    # poder reconstruirlo.
                    "dying_offer": safe_int(
                        fila.get("offer_amount")
                    ),
                    "dying_offer_hours": safe_float(
                        fila.get("offer_hours_to_expiry")
                    ),
                }
            )

        # El mas urgente primero: si el tope corta, que corte por
        # el que mas margen tiene.
        elegidos.sort(
            key=lambda f: f["listing_hours_to_expiry"]
        )

        limite = max(0, safe_int(tope))

        recortados = max(0, len(elegidos) - limite)

        elegidos = elegidos[:limite]

        if not elegidos:
            return {
                **vacio,
                "available": True,
                "skipped": descartados,
                "at_risk": en_riesgo,
                "blocked_by": "NADA_QUE_RENOVAR",
                "reason": (
                    f"Ventana abierta y nada que renovar: "
                    f"{len(descartados)} listado(s) mirados y "
                    f"ninguno lo necesita."
                ),
            }

        return {
            "available": True,
            "execute": True,
            "renewals": elegidos,
            "skipped": descartados,
            "at_risk": en_riesgo,
            "count": len(elegidos),
            "capped_at": limite,
            "dropped_by_cap": recortados,
            "mandatory": obligatorio,
            "blocked_by": None,
            "reason": (
                f"{len(elegidos)} renovacion(es) en esta "
                f"ventana"
                + (
                    f", OBLIGATORIAS: hay "
                    f"{_euros(deuda_contingente)} EUR de deuda "
                    f"contingente y esta es la caja con la que "
                    f"se tapa"
                    if obligatorio
                    else ""
                )
                + f". {ventana.get('reason')}"
                + " (la ventana ya no restringe la renovacion:"
                " renovar no mata la oferta viva)"
                + (
                    f" El tope de {limite} dejo fuera "
                    f"{recortados}."
                    if recortados
                    else ""
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "blocked_by": "ERROR",
            "reason": (
                f"No se pudo decidir que renovar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def filas_desde_lo_publicado(
    listings: dict | None,
    offers: list | None,
    roster: dict | None = None,
) -> list:
    """
    Traduce lo que publica el dashboard a las filas que pide
    `que_renovar`.

    POR QUE EXISTE

        El ciclo y la pantalla tienen que mirar los mismos
        listados. Si cada uno arma su lista, acaban ensenando
        cosas distintas del mismo mercado.

    No lee el mundo: se le pasa lo ya publicado.
    """

    try:
        por_nombre = {}

        listings = listings if isinstance(listings, dict) else {}

        roster = roster if isinstance(roster, dict) else {}

        offers = offers if isinstance(offers, list) else []

        for oferta in (offers or []):

            if not isinstance(oferta, dict):
                continue

            nombres = oferta.get("players") or []

            nombre = (
                oferta.get("player_name")
                or (nombres[0] if nombres else None)
            )

            if not nombre:
                continue

            por_nombre[str(nombre)] = oferta

        ids = {}

        valores = {}

        for jugador in ((roster or {}).get("players") or []):

            if isinstance(jugador, dict) and jugador.get("name"):
                ids[str(jugador["name"])] = jugador.get("id")
                valores[str(jugador["name"])] = jugador.get(
                    "price"
                )

        filas = []

        for item in (
            (listings or {}).get("renew_required") or []
        ):

            if not isinstance(item, dict):
                continue

            nombre = str(item.get("name") or "")

            oferta = por_nombre.get(nombre) or {}

            filas.append(
                {
                    "id": ids.get(nombre),
                    "name": nombre,
                    "listed_price": safe_int(
                        item.get("listed_price")
                    ),
                    "listing_hours_to_expiry": safe_float(
                        item.get("hours_to_expiry")
                    ),

                    # Lo que vale HOY. Sin esto no se puede
                    # re-preciar y la peticion se queda rancia.
                    "market_price": safe_int(
                        valores.get(nombre)
                    ),
                    "offer_amount": safe_int(
                        oferta.get("amount")
                    ),
                    "offer_hours_to_expiry": safe_float(
                        oferta.get("hours_to_expiry")
                    ),
                }
            )

        return filas

    except Exception:                               # noqa: BLE001
        return []
