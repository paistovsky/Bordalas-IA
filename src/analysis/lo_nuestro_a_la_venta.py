"""
Lo nuestro a la venta: que va a hacer Pepe con cada publicacion.

SINTOMA (13/09/2026)

    La pantalla de MERCADO enseñaba lo que se puede COMPRAR en
    dos cuadros, y de lo que esta PUBLICADO enseñaba un numero:
    "16 publicados". Nada mas.

    Diecisiete jugadores en plantilla, dieciseis en el escaparate
    y catorce con una oferta del Computer encima de la mesa, y en
    pantalla no se podia saber cual de esas ofertas se va a
    aceptar, cual se va a rerollear y cual esta reservada para
    tapar deuda.

CONSECUENCIA

    La mitad de la economia del juego pasaba por decisiones que
    el motor ya tomaba y que no se veian. El dueño no podia
    pararle la mano a ninguna, porque no sabia que existia.

LA REGLA DE ESTE CUADRO

    LA ETIQUETA NO LA DECIDE LA PANTALLA. LA DECIDE EL MOTOR Y
    LA PANTALLA LA TRADUCE.

    `QUE_VA_A_HACER` es un diccionario de traduccion y nada mas:
    de la accion que publica el motor —`REROLL_CANDIDATE`,
    `KEEP_GOOD_OFFER`, `HOLD_SOLVENCY_RESERVED`, `HOLD_OFFER`,
    `NEVER_SELL`— a como se dice en cristiano.

    Si para una fila no hay decision publicada, la fila pone
    "sin decidir" y el recuento lo dice. No se rellena con la
    mas probable: una etiqueta inventada aqui seria una decision
    tomada por la pantalla.

LA COLUMNA QUE MENTIA (14/09/2026)

    La columna se llamaba VALE y no era lo que vale: era lo que
    PEDIMOS. Medido en las trece filas con oferta de esa tarde,
    la relacion entre las dos cosas iba de 0,97 a 1,48:

        jugador    pedimos      precio real   pedimos/precio
        Yamal      32.160.000    21.820.000        1,474
        Exposito    7.820.000     5.300.000        1,475
        Mangala     3.330.000     2.380.000        1,399
        Cepeda        640.000       660.000        0,970

    El que miraba leia "Yamal vale 32.160.000 y nos ofrecen
    20.896.900" y entendia un robo del 35 %. La prima que hay al
    lado decia -4,2 %, que es la verdad: la oferta esta a un 4 %
    por debajo del PRECIO DE MERCADO.

    Dos numeros contradictorios en la misma fila, y el grande y
    redondo gana siempre al pequeño con decimales.

    No era un problema de calculo: la prima estaba bien. Era la
    columna de al lado, que se llamaba como otra cosa.

    Ahora son dos columnas con su nombre —LO QUE PEDIMOS y
    PRECIO DE MERCADO— y la cabecera dice contra cual se mide la
    prima. Doctrina 45: la pantalla habla el idioma del que lee.

UN VIAJE DEL CARRIL NO SE «CONSERVA» (14/09/2026)

    Trent salia con la etiqueta "buena, la conservamos". La
    DECISION era correcta —la oferta se quedaba 37.900 por
    debajo del suelo de cobro— pero la frase describia otra cosa.

    `KEEP_GOOD_OFFER` es la lengua del motor de ofertas, que
    habla de la plantilla. Un jugador comprado para revender no
    se conserva: o se cobra por encima del suelo, o se espera. Y
    lo que el dueño necesita saber es CUANTO FALTA.

    Por eso las filas que son un viaje abierto se etiquetan con
    la regla del carril, no con la del motor de ofertas.

    Y EL SUELO NO SE ESCRIBE AQUI: sale de `precio_de_salida`,
    la misma funcion con la que `que_cobrar` decide de verdad. La
    pantalla no fija un segundo umbral; traduce el que ya hay.

ESTO NO DECIDE NADA

    No se vende, no se acepta ni se rerollea nada desde aqui. Es
    una lista para mirar.

REGLA 23

    No lee estado externo. Publicaciones, ofertas, catalogo, once,
    aviso y viajes llegan como argumentos.
"""

from __future__ import annotations

# EL SUELO DE COBRO SE PREGUNTA, NO SE ESCRIBE.
#
#     `precio_de_salida` y `SUELO_DEL_VIAJE` son los mismos que
#     usa `que_cobrar` para decidir de verdad. Copiar aqui el
#     "coste + 1 %" daria dos verdades sobre el mismo numero, y
#     el dia que una cambiara, la de la pantalla seria la falsa.
from src.analysis.salida_del_viaje import (
    SUELO_DEL_VIAJE,
    precio_de_salida,
)


# LA TRADUCCION. De lo que dice el motor a como se dice.
#
#     Cada clave es una accion que el motor PUBLICA hoy. Si
#     apareciera una que no esta aqui, la fila sale con la accion
#     en crudo y `traducida: False`: preferimos un nombre feo y
#     verdadero a uno bonito e inventado.
QUE_VA_A_HACER = {
    "REROLL_CANDIDATE": "pedir otra oferta",
    "KEEP_GOOD_OFFER": "buena, la conservamos",
    "HOLD_SOLVENCY_RESERVED": "guardar para tapar deuda",
    "HOLD_OFFER": "esperar mejor oferta",
    "NEVER_SELL": "no se vende nunca",
    "ACCEPT_OFFER": "aceptar y cobrar",
}

# Lo que se pone cuando el motor no ha dicho nada de esa fila.
SIN_DECIDIR = "sin decidir"

# CONTRA QUE SE MIDE LA PRIMA, dicho una sola vez y publicado
# para que la cabecera lo pinte en vez de suponerlo.
PRIMA_CONTRA = "PRECIO DE MERCADO"

PRIMA_REASON = (
    "La prima se mide contra el PRECIO DE MERCADO, no contra lo "
    "que pedimos: lo que pedimos lo elegimos nosotros y por eso "
    "no mide nada."
)

POSICIONES = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


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


def _por_jugador(ofertas) -> dict:
    """
    Las ofertas, indexadas por id de jugador.

    POR ID, NO POR NOMBRE (regla 33). El nombre lo escribe
    Biwenger y hay repetidos; el id es el id.

    Una oferta puede pedir varios jugadores: cuenta para todos
    los que pide.
    """

    indice = {}

    for oferta in ofertas or []:

        if not isinstance(oferta, dict):
            continue

        for pid in oferta.get("player_ids") or []:

            pid = safe_int(pid)

            if pid:
                indice.setdefault(pid, oferta)

    return indice


def _euros(valor) -> str:
    """12.345.678. Para que el motivo se lea sin contar ceros."""

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"


def _viajes_abiertos(viajes) -> dict:
    """
    Los viajes abiertos, por id, con su coste.

    Llega tal cual lo publica `libro_de_viajes.abiertos()`. Los
    de `sin_coste` TAMBIEN entran: son precisamente los que no se
    pueden juzgar contra el suelo, y la fila tiene que decirlo en
    vez de callarse y heredar la etiqueta del motor de ofertas.
    """

    datos = viajes if isinstance(viajes, dict) else {}

    indice = {}

    for fila in (
        (datos.get("viajes") or [])
        + (datos.get("sin_coste") or [])
    ):

        if not isinstance(fila, dict):
            continue

        pid = safe_int(fila.get("player_id"))

        if pid:
            indice.setdefault(pid, fila)

    return indice


def _lo_que_se_hace_con_un_viaje(coste, importe, suelo) -> dict:
    """
    Que pasa con un viaje del carril, y cuanto falta.

    TRES ESTADOS Y NINGUNO ES «CONSERVAR»

        sin coste conocido  ->  no hay suelo que calcular
        por debajo del suelo ->  se espera, y falta X
        del suelo para arriba ->  se cobra

    El numero que hace falta es CUANTO FALTA. "No llega al suelo"
    a secas no distingue entre faltar 37.900 de 2.787.600 y
    faltar 600.000: la primera se cobra el reset que viene y la
    segunda no se cobra nunca.
    """

    coste = safe_int(coste)

    # SIN COSTE NO HAY SUELO, y un suelo que no se puede calcular
    # no es cero: es NO VENDER. Misma regla que la prohibicion 0
    # de `que_cobrar`, dicha en cristiano.
    if coste <= 0:
        return {
            "que_va_a_hacer": "no se sabe lo que costo",
            "suelo_de_cobro": None,
            "falta_para_el_suelo": None,
            "por_que": (
                "No se sabe lo que costo este viaje: sin coste no "
                "hay suelo de cobro, y un suelo que no se puede "
                "calcular no es cero, es no vender."
            ),
        }

    minimo = precio_de_salida(coste, suelo)

    if importe is None:
        return {
            "que_va_a_hacer": "esperando oferta del Computer",
            "suelo_de_cobro": minimo,
            "falta_para_el_suelo": None,
            "por_que": (
                f"Viaje abierto por {_euros(coste)} y todavia sin "
                f"oferta encima de la mesa. El suelo de cobro es "
                f"{_euros(minimo)} (coste + {suelo * 100:.0f} %)."
            ),
        }

    importe = safe_int(importe)

    if importe < minimo:
        return {
            "que_va_a_hacer": "no llega al suelo de cobro",
            "suelo_de_cobro": minimo,
            "falta_para_el_suelo": minimo - importe,
            "por_que": (
                f"La oferta ({_euros(importe)}) se queda "
                f"{_euros(minimo - importe)} por debajo del suelo "
                f"de cobro ({_euros(minimo)} = coste "
                f"{_euros(coste)} + {suelo * 100:.0f} %). Se "
                f"espera al proximo reset."
            ),
        }

    return {
        "que_va_a_hacer": "pasa el suelo de cobro: se cobra",
        "suelo_de_cobro": minimo,
        "falta_para_el_suelo": 0,
        "por_que": (
            f"La oferta ({_euros(importe)}) pasa el suelo de "
            f"cobro ({_euros(minimo)} = coste {_euros(coste)} + "
            f"{suelo * 100:.0f} %): el viaje se cierra en "
            f"ganancia."
        ),
    }


def _titulares(once) -> set:
    return {
        safe_int(j.get("id"))
        for j in (once or [])
        if isinstance(j, dict) and safe_int(j.get("id"))
    }


def lo_nuestro_a_la_venta(
    listados: list | None,
    ofertas: list | None,
    catalogo: dict | None,
    once: list | None = None,
    sin_listar: dict | None = None,
    renovacion: dict | None = None,
    viajes: dict | None = None,
    suelo: float = SUELO_DEL_VIAJE,
) -> dict:
    """
    Las publicaciones nuestras, con lo que el motor va a hacer.

    Forma fija. Nunca lanza. Si no hay publicaciones devuelve
    `available: False` y lo dice, en vez de un cuadro vacio que
    se lee como "no tenemos nada en venta".
    """

    vacio = {
        "available": False,
        "players": [],
        "publicados": 0,
        "con_oferta": 0,
        "sin_decidir": 0,
        "sin_traducir": [],
        "comprado_sin_publicar": {
            "hay": False,
            "players": [],
            "reason": None,
        },
        "renovacion": None,

        # CONTRA QUE SE MIDE LA PRIMA. Va en la cabecera del
        # cuadro: sin decirlo, el lector la mide contra la unica
        # cifra grande que ve, que es la que pedimos.
        "prima_contra": PRIMA_CONTRA,
        "prima_reason": PRIMA_REASON,

        "viajes_abiertos": 0,
        "reason": None,
    }

    try:
        # EL AVISO SE MONTA SIEMPRE, haya o no publicaciones.
        #
        #     Un jugador comprado para revender y sin publicar es
        #     justo el caso en que puede no haber ninguna fila. Si
        #     el aviso viviera dentro del cuadro, el unico dia que
        #     hace falta no se veria.
        aviso = _el_aviso(sin_listar)

        frase_renovacion = (renovacion or {}).get("reason")

        if not listados:
            return {
                **vacio,
                "comprado_sin_publicar": aviso,
                "renovacion": frase_renovacion,
                "reason": (
                    "No hay ninguna publicacion nuestra en el "
                    "escaparate."
                ),
            }

        por_jugador = _por_jugador(ofertas)

        por_viaje = _viajes_abiertos(viajes)

        titulares = _titulares(once)

        filas = []

        for listado in listados:

            if not isinstance(listado, dict):
                continue

            pid = safe_int(listado.get("player_id"))

            ficha = (
                (catalogo or {}).get(pid)
                or (catalogo or {}).get(str(pid))
                or {}
            )

            oferta = por_jugador.get(pid) or {}

            # LA DECISION, TAL Y COMO LA PUBLICA EL MOTOR.
            accion = oferta.get("action") or None

            # ¿ES UN VIAJE DEL CARRIL?
            #
            #     Si lo es, manda la regla del carril y no la del
            #     motor de ofertas. No es una segunda opinion: es
            #     que son dos negocios distintos. La plantilla se
            #     conserva; un viaje se cobra o se espera.
            viaje = por_viaje.get(pid)

            importe = (
                safe_int(oferta.get("amount"))
                if oferta.get("amount") is not None
                else None
            )

            del_carril = (
                _lo_que_se_hace_con_un_viaje(
                    viaje.get("cost"), importe, suelo
                )
                if viaje
                else None
            )

            filas.append(
                {
                    "id": pid,
                    "name": (
                        ficha.get("name")
                        or listado.get("name")
                        or f"#{pid}"
                    ),
                    "position": safe_int(ficha.get("position")),
                    "team_id": (
                        safe_int(ficha.get("teamID")) or None
                    ),
                    "posicion": POSICIONES.get(
                        safe_int(ficha.get("position"))
                    ),
                    "status": ficha.get("status"),
                    "points": safe_int(ficha.get("points")),
                    "titular": pid in titulares if once else None,

                    # LAS DOS COLUMNAS, CADA UNA CON SU NOMBRE.
                    #
                    #     LO QUE PEDIMOS es el precio publicado:
                    #     lo elegimos nosotros y puede estar un
                    #     48 % por encima del mercado.
                    #
                    #     PRECIO DE MERCADO es lo que Biwenger
                    #     dice que vale, y es contra lo que se
                    #     mide la prima de la oferta.
                    #
                    #     Cuando no hay precio publicado se cae al
                    #     de mercado, y entonces las dos columnas
                    #     coinciden: eso es cierto y se ve.
                    "lo_que_pedimos": safe_int(
                        listado.get("listed_price")
                        or ficha.get("price")
                    ),
                    "precio_de_mercado": (
                        safe_int(ficha.get("price"))
                        if ficha.get("price") is not None
                        else None
                    ),
                    "nos_ofrecen": (
                        safe_int(oferta.get("amount"))
                        if oferta.get("amount") is not None
                        else None
                    ),
                    "prima": oferta.get("premium_percent"),
                    "prima_contra": (
                        PRIMA_CONTRA
                        if oferta.get("premium_percent") is not None
                        else None
                    ),

                    # CADA OFERTA CON SU RELOJ (regla 33).
                    #
                    #     Caducan dos cosas distintas: LA OFERTA y
                    #     LA PUBLICACION. Llevan numeros distintos
                    #     y van con su nombre puesto — la columna
                    #     del cuadro es la de la oferta.
                    "oferta_caduca_en": safe_float(
                        oferta.get("hours_to_expiry")
                    ),
                    "oferta_caducada": bool(oferta.get("expired")),
                    "publicacion_caduca_en": safe_float(
                        listado.get("hours_to_expiry")
                    ),
                    "publicacion_caducada": bool(
                        listado.get("expired")
                    ),

                    "tiene_oferta": bool(oferta),
                    "de_quien_es_la_oferta": oferta.get(
                        "counterparty"
                    ),

                    # SI ES UN VIAJE, CON SU SUELO DELANTE.
                    "es_viaje": bool(viaje),
                    "coste_del_viaje": (
                        safe_int(viaje.get("cost")) or None
                        if viaje
                        else None
                    ),
                    "suelo_de_cobro": (
                        del_carril["suelo_de_cobro"]
                        if del_carril
                        else None
                    ),
                    "falta_para_el_suelo": (
                        del_carril["falta_para_el_suelo"]
                        if del_carril
                        else None
                    ),

                    # LO QUE VA A HACER. Traducido, no decidido.
                    #
                    #     De un viaje lo dice el carril; de los
                    #     demas, el motor de ofertas. `etiqueta_de`
                    #     deja escrito cual de los dos hablo, para
                    #     que no haya que adivinarlo.
                    "accion_del_motor": accion,
                    "etiqueta_de": (
                        "CARRIL"
                        if viaje
                        else ("MOTOR_DE_OFERTAS" if accion else None)
                    ),
                    "que_va_a_hacer": (
                        del_carril["que_va_a_hacer"]
                        if del_carril
                        else (
                            QUE_VA_A_HACER.get(accion, accion)
                            if accion
                            else SIN_DECIDIR
                        )
                    ),
                    "decidido": bool(accion) or bool(viaje),
                    "traducida": (
                        True
                        if viaje
                        else accion in QUE_VA_A_HACER
                    ),
                    "fuente": (
                        "CARRIL_SUELO_DE_COBRO"
                        if viaje
                        else oferta.get("decision_source")
                    ),
                    "por_que": (
                        del_carril["por_que"]
                        if del_carril
                        else (
                            oferta.get("decision_reason")
                            or (
                                "El motor no ha publicado ninguna "
                                "decision para esta publicacion."
                            )
                        )
                    ),
                    "proteccion": oferta.get("protection"),
                    "renovar": bool(listado.get("renew_required")),
                }
            )

        # Primero los que hay que mirar: sin decidir, luego con
        # oferta, y dentro por prima de mayor a menor.
        filas.sort(
            key=lambda f: (
                0 if not f["decidido"] else 1,
                0 if f["tiene_oferta"] else 1,
                -(safe_float(f["prima"]) or 0),
            )
        )

        sin_decidir = [f for f in filas if not f["decidido"]]

        sin_traducir = sorted(
            {
                f["accion_del_motor"]
                for f in filas
                if f["decidido"] and not f["traducida"]
            }
        )

        con_oferta = [f for f in filas if f["tiene_oferta"]]

        return {
            "available": True,
            "players": filas,
            "publicados": len(filas),
            "con_oferta": len(con_oferta),
            "sin_decidir": len(sin_decidir),
            "sin_traducir": sin_traducir,
            "comprado_sin_publicar": aviso,
            "renovacion": frase_renovacion,

            "prima_contra": PRIMA_CONTRA,
            "prima_reason": PRIMA_REASON,

            "viajes_abiertos": len(
                [f for f in filas if f["es_viaje"]]
            ),

            "reason": (
                f"{len(filas)} publicacion(es), {len(con_oferta)} "
                f"con oferta encima de la mesa y "
                f"{len(sin_decidir)} sin decision publicada."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar lo nuestro a la venta: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _el_aviso(sin_listar) -> dict:
    """
    Comprado para revender y todavia sin poner a la venta.

    Mientras no este publicado, el Computer no le hace ninguna
    oferta: el viaje esta parado y no se nota.

    REGLA 37: LO ENCIENDE EL HECHO, NO LA INTENCION.

        Si no hay ningun viaje abierto sin publicar, el aviso no
        sale. Un cartel fijo se deja de leer a los dos dias y
        entonces ya no avisa de nada.
    """

    datos = sin_listar if isinstance(sin_listar, dict) else {}

    nombres = [
        (
            jugador.get("name")
            if isinstance(jugador, dict)
            else str(jugador)
        )
        for jugador in (datos.get("players") or [])
    ]

    nombres = [n for n in nombres if n]

    return {
        "hay": bool(nombres),
        "players": nombres,
        "reason": datos.get("reason"),
    }
