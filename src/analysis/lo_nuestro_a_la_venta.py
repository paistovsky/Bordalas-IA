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

ESTO NO DECIDE NADA

    No se vende, no se acepta ni se rerollea nada desde aqui. Es
    una lista para mirar.

REGLA 23

    No lee estado externo. Publicaciones, ofertas, catalogo, once
    y aviso llegan como argumentos.
"""

from __future__ import annotations


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

                    # VALE: lo que pide Biwenger por el. NOS
                    # OFRECEN: lo que hay encima de la mesa.
                    "vale": safe_int(
                        listado.get("listed_price")
                        or ficha.get("price")
                    ),
                    "nos_ofrecen": (
                        safe_int(oferta.get("amount"))
                        if oferta.get("amount") is not None
                        else None
                    ),
                    "prima": oferta.get("premium_percent"),

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

                    # LO QUE VA A HACER. Traducido, no decidido.
                    "accion_del_motor": accion,
                    "que_va_a_hacer": (
                        QUE_VA_A_HACER.get(accion, accion)
                        if accion
                        else SIN_DECIDIR
                    ),
                    "decidido": bool(accion),
                    "traducida": accion in QUE_VA_A_HACER,
                    "fuente": oferta.get("decision_source"),
                    "por_que": (
                        oferta.get("decision_reason")
                        or (
                            "El motor no ha publicado ninguna "
                            "decision para esta publicacion."
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
