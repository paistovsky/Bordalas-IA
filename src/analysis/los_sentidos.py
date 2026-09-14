"""
Los sentidos de Pepe: de que se entera, de cuando, y que decide.

POR QUE HACE FALTA (13/09/2026)

    Hoy Pepe esta medio ciego y la pantalla no lo decia. Sesenta
    y cuatro objetivos en el mercado y NI UNA PUJA, con la misma
    frase repetida sesenta y cuatro veces: "no hay pronostico de
    titularidad".

    El tablero de titulares es de la JORNADA 2, del 17 de agosto.
    El motor lo rechaza, que es lo correcto. Pero el resultado es
    que la via de fichar esta cerrada POR FALTA DE UN DATO, no
    por criterio — y eso, mirando la pantalla, no se distinguia
    de "hoy no hay nada que valga la pena".

    Un sentido apagado no se nota. Se nota que no se decide nada,
    y eso se confunde con prudencia.

LAS DOS REGLAS DE ESTE CUADRO

    1. LA EDAD SE CALCULA, NO SE ESCRIBE.

       "Hace 27 dias" sale de restar `starter_board_updated_at`
       de la hora de la foto. Ni un numero de dias a mano: un dia
       escrito envejece mal y a la semana miente.

       Y SIN MARCA DE TIEMPO SE DICE "sin dato", nunca un cero.
       Un cero se lee como "de hoy", que es lo contrario.

    2. EL "QUE BLOQUEA" ES LA FRASE DEL MOTOR, ENTERA.

       Cuando el motor escribe por que rechaza algo, esa frase se
       copia tal cual. Reescribirla aqui seria una segunda
       version de la verdad, y la pantalla no tiene autoridad
       para tener opinion sobre esto.

ESTO NO DECIDE NADA. Es un cuadro para mirar.

REGLA 23

    No lee estado externo: todo llega como argumento.
"""

from __future__ import annotations

from datetime import datetime, timezone


# EL ESTADO DE UN SENTIDO. Tres, y ni uno mas.
#
#     VIVO    el dato sirve para decidir hoy
#     VIEJO   el dato existe pero esta fechado atras
#     MUERTO  no hay dato, o el motor lo ha rechazado
#
#     El corte entre VIVO y VIEJO NO ESTA MEDIDO: se pone en
#     `DIAS_PARA_VIEJO` y viaja publicado para que se vea que es
#     un numero puesto a ojo y no una medicion.
DIAS_PARA_VIEJO = 3

VIVO = "VIVO"
VIEJO = "VIEJO"
MUERTO = "MUERTO"


# ============================================================
# CUANTO PUEDE ENVEJECER CADA SENTIDO, Y POR QUE
# ============================================================
#
#     EL SINTOMA QUE ESTO ARREGLA (14/09/2026)
#
#         El tablero de titulares se cayo el 17 de agosto y
#         volvio el 14 de septiembre. Las dos veces SOLO, sin que
#         nadie lo tocara. Veintisiete dias con la via de fichar
#         cerrada por falta de un dato, y ni un aviso.
#
#         Y como volvio solo, se volvera a caer solo.
#
#         Lo que fallaba no era la deteccion: la edad se calcula
#         desde el 13/09 y se ve en el cuadro. Lo que faltaba era
#         que ALGUIEN GRITARA. Un numero en una tabla de ocho
#         filas no es un aviso; es un dato que hay que ir a
#         buscar, y a la avería que dura veintisiete dias no la
#         va a buscar nadie.
#
#     EL TOPE NO SE INVENTA: SALE DE CADA CUANTO CAMBIA EL DATO
#
#         Cada tope de aqui abajo apunta a la constante del
#         modulo que PRODUCE el dato. Un numero redondo puesto a
#         ojo aqui seria un umbral nuevo sin medir, y de esos ya
#         tenemos uno declarado (`DIAS_PARA_VIEJO`).
#
#         Los que no se pueden derivar salen con `medida: False`
#         y lo dicen. Cuatro sentidos NO TIENEN RELOJ PROPIO: se
#         recalculan de la foto en cada vuelta, asi que su edad
#         es la de la foto y no pueden caducar por su cuenta. Lo
#         que les pasa es que se apagan, y eso ya lo dice su
#         estado.
POR_JORNADA = "POR_JORNADA"
POR_HORAS = "POR_HORAS"
SIN_RELOJ_PROPIO = "SIN_RELOJ_PROPIO"

EDAD_MAXIMA = {
    "Tablero de titulares": {
        "criterio": POR_JORNADA,
        "horas": None,
        "medida": True,
        "motivo": (
            "Se mide POR JORNADA, no por horas: un tablero de la "
            "jornada 2 no dice nada de la 7 aunque se hubiera "
            "bajado hace una hora. El motor ya lo rechaza asi "
            "(`starter_cache_status`), y ese criterio es el "
            "bueno: caduca cuando su jornada no es la de hoy."
        ),
    },
    "Ojeador de precios": {
        "criterio": POR_HORAS,
        "horas": 24,
        "medida": True,
        "motivo": (
            "Los precios que mira se mueven en el reset del "
            "mercado, a las 07:00 de Madrid "
            "(`scout/report.py: RESET_HOUR_MADRID`), y entre "
            "reset y reset hay 24 h. Un informe de antes del "
            "ultimo reset esta hablando de OTRO mercado. El "
            "propio ojeador se refresca cada 6 h "
            "(`DEFAULT_TTL_SECONDS`), asi que 24 h son cuatro "
            "refrescos perdidos: no es un retraso, es que no "
            "vuelve."
        ),
    },
    "Prensa": {
        "criterio": POR_HORAS,
        "horas": 24,
        "medida": True,
        "motivo": (
            "La prensa hace dos pasadas al dia: se refresca cada "
            "12 h (`scout/press.py: DEFAULT_TTL_SECONDS`). Se "
            "grita a las 24 h, que son DOS pasadas seguidas "
            "perdidas. Una pasada perdida es una vuelta que no "
            "salio; dos es que la fuente no vuelve."
        ),
    },
    "Calendario de LaLiga": {
        "criterio": POR_HORAS,
        "horas": 12,
        "medida": True,
        "motivo": (
            "Se refresca cada 6 h como mucho "
            "(`matchday_calendar_engine.calculate_refresh_"
            "interval`, que baja a 2 h en la semana del partido "
            "y a 30 min en las ultimas 48 h). 12 h son dos "
            "refrescos perdidos del tramo MAS LARGO, que es el "
            "unico caso en que 12 h pueden ser normales."
        ),
    },
    "La vara por posición": {
        "criterio": SIN_RELOJ_PROPIO,
        "horas": None,
        "medida": False,
        "motivo": (
            "No tiene marca de tiempo propia: se recalcula de la "
            "foto en cada vuelta, asi que su edad es la de la "
            "foto. No puede caducar por su cuenta; lo que le "
            "pasa es que se apaga, y eso ya lo dice su estado."
        ),
    },
    "La caja de los ocho": {
        "criterio": SIN_RELOJ_PROPIO,
        "horas": None,
        "medida": False,
        "motivo": (
            "Se reconstruye del tablon en cada vuelta: su edad "
            "es la de la foto. Lo que le puede pasar es no "
            "cuadrar, y eso ya lo dice su estado."
        ),
    },
    "Catálogo y plantillas": {
        "criterio": SIN_RELOJ_PROPIO,
        "horas": None,
        "medida": False,
        "motivo": (
            "Sale del censo de la foto en cada vuelta: su edad "
            "es la de la foto. Lo que le puede pasar es no "
            "cuadrar, y eso ya lo dice su estado."
        ),
    },
    "El marcador": {
        "criterio": SIN_RELOJ_PROPIO,
        "horas": None,
        "medida": False,
        "motivo": (
            "No envejece: se recalcula del ledger en cada "
            "vuelta. Lo que le pasa es que no tiene ni una "
            "jornada fiable, y eso ya lo dice su estado."
        ),
    },
}

# Lo que se pone cuando aparece un sentido que no esta en la
# tabla. No se le inventa un tope: se dice que no tiene.
SIN_TOPE = {
    "criterio": SIN_RELOJ_PROPIO,
    "horas": None,
    "medida": False,
    "motivo": (
        "Sentido nuevo: todavia no se ha derivado cuanto puede "
        "envejecer. Sin tope no se grita."
    ),
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _momento(valor):
    """
    Una marca de tiempo, o `None`. Nunca lanza.

    UN TIMESTAMP SIN ZONA ES UN DATO CON DOS NOMBRES (regla 35):
    si llega sin zona se asume UTC y se dice en `zona_supuesta`,
    en vez de restar horas de dos relojes distintos y publicar la
    diferencia como si fuera exacta.
    """

    if not valor:
        return None, False

    try:
        cuando = datetime.fromisoformat(str(valor))

    except (TypeError, ValueError):
        return None, False

    if cuando.tzinfo is None:
        return cuando.replace(tzinfo=timezone.utc), True

    return cuando, False


def edad(valor, ahora=None) -> dict:
    """
    Cuanto hace de esto. Forma fija, nunca lanza.

    Devuelve `dias`, `horas` y `texto`. Sin marca de tiempo, los
    tres dicen que no se sabe: `dias` es `None` y el texto es
    "sin dato". Un cero seria "de ahora mismo", que es justo lo
    contrario de lo que pasa cuando falta el dato.
    """

    cuando, sin_zona = _momento(valor)

    if cuando is None:
        return {
            "dias": None,
            "horas": None,
            "texto": "sin dato",
            "zona_supuesta": False,
        }

    # SIN REFERENCIA NO SE DICE "HACE N DIAS" (14/09/2026)
    #
    #     Esto era `ahora or datetime.now(timezone.utc)`. Con el
    #     respaldo puesto, la edad de cada sentido se medía
    #     contra el reloj de quien abre la pantalla: el mismo
    #     `status.json` decía 27 días por la tarde y 28 por la
    #     noche sin que nada hubiera cambiado.
    #
    #     Y es la misma forma exacta que tumbó la verja esta
    #     madrugada con el cartel del carril.
    if ahora is None:
        return {
            "dias": None,
            "horas": None,
            "texto": "sin referencia",
            "zona_supuesta": sin_zona,
        }

    referencia = ahora

    if referencia.tzinfo is None:
        referencia = referencia.replace(tzinfo=timezone.utc)

    segundos = (referencia - cuando).total_seconds()

    horas = round(segundos / 3600.0, 1)

    dias = int(segundos // 86400)

    if segundos < 0:
        texto = "en el futuro"

    elif dias >= 1:
        texto = f"hace {dias} día{'s' if dias != 1 else ''}"

    elif horas >= 1:
        texto = f"hace {int(horas)} h"

    else:
        texto = "de hace un rato"

    return {
        "dias": dias,
        "horas": horas,
        "texto": texto,
        "zona_supuesta": sin_zona,
    }


def _estado_por_edad(cuanto, muerto_si=False) -> str:
    """
    VIVO, VIEJO o MUERTO segun cuanto hace.

    `muerto_si` lo pone MUERTO pase lo que pase: un tablero
    rechazado por el motor esta muerto aunque fuera de esta
    mañana, porque no se usa.
    """

    if muerto_si:
        return MUERTO

    if cuanto.get("dias") is None:
        return MUERTO

    return VIEJO if cuanto["dias"] >= DIAS_PARA_VIEJO else VIVO


def _el_tope(nombre) -> dict:
    """El tope de ese sentido, o el que dice que no tiene."""

    return EDAD_MAXIMA.get(nombre) or SIN_TOPE


def _ha_caducado(fila, tope) -> dict:
    """
    ¿Este sentido ha pasado de su edad maxima? Forma fija.

    TRES CRITERIOS, Y CADA UNO DICE CUAL ES

        POR_JORNADA       la jornada del dato no es la de hoy
        POR_HORAS         la edad pasa del tope derivado
        SIN_RELOJ_PROPIO  no puede caducar: no tiene reloj

    NO SE GRITA POR NO SABER (14/09/2026)

        Si la edad no se puede medir -sin marca de tiempo, o sin
        hora de referencia- esto NO dice "caducado". Diria que
        hay una averia cada vez que falta un dato de apoyo, y a
        la tercera vez nadie mira la banda.

        Lo que falta se dice en `motivo`, y el estado MUERTO ya
        cuenta ese caso por su cuenta.
    """

    criterio = tope.get("criterio")

    if criterio == POR_JORNADA:

        # LA DEL DATO CONTRA LA DE HOY. Sin una de las dos no se
        # compara: se dice que no se puede.
        suya = safe_int(fila.get("jornada"), default=0)

        hoy = safe_int(fila.get("jornada_de_hoy"), default=0)

        if not suya or not hoy:
            return {
                "caducado": False,
                "medible": False,
                "motivo": (
                    "No se puede comparar por jornada: falta la "
                    "del tablero o la de hoy."
                ),
            }

        return {
            "caducado": suya != hoy,
            "medible": True,
            "motivo": (
                f"El tablero es de la jornada {suya} y hoy se "
                f"juega la {hoy}."
                if suya != hoy
                else f"El tablero es de la jornada de hoy ({hoy})."
            ),
        }

    if criterio == POR_HORAS:

        horas = tope.get("horas")

        cuanto = fila.get("edad") or {}

        tiene = cuanto.get("horas")

        if horas is None or tiene is None:
            return {
                "caducado": False,
                "medible": False,
                "motivo": (
                    f"No se puede medir la edad: "
                    f"{cuanto.get('texto') or 'sin dato'}."
                ),
            }

        return {
            "caducado": float(tiene) > float(horas),
            "medible": True,
            "motivo": (
                f"Es de {cuanto.get('texto')} y su tope son "
                f"{horas} h."
            ),
        }

    return {
        "caducado": False,
        "medible": False,
        "motivo": tope.get("motivo"),
    }


def la_alarma(filas) -> dict:
    """
    Los sentidos que han pasado de su edad maxima. Forma fija.

    DICE QUE DECISION QUEDA BLOQUEADA, no solo que el dato es
    viejo. "El tablero es de hace 27 dias" es un dato; "la via de
    fichar esta cerrada" es la consecuencia, y es lo unico que
    hace que alguien se levante a mirarlo.

    SE CUENTA, NO SE ESCRIBE (regla 18). El dia que se arregle
    el tablero esta lista se vacia sola.
    """

    caducados = [
        f
        for f in (filas or [])
        if (f.get("edad_maxima") or {}).get("caducado")
    ]

    return {
        "hay": bool(caducados),
        "cuantos": len(caducados),
        "sentidos": [
            {
                "sentido": f.get("sentido"),
                "estado": f.get("estado"),
                "texto": f.get("alarma_texto"),
                "que_queda_bloqueado": f.get("que_decide"),
                "que_bloquea": f.get("que_bloquea"),
            }
            for f in caducados
        ],
        "reason": (
            (
                f"{len(caducados)} sentido(s) por encima de su "
                f"edad maxima: "
                + ", ".join(
                    str(f.get("sentido")) for f in caducados
                )
                + "."
            )
            if caducados
            else "Ningun sentido ha pasado de su edad maxima."
        ),
    }


def los_sentidos(
    lineup: dict | None,
    scout: dict | None,
    press: dict | None,
    vara: dict | None,
    rival_intelligence: dict | None,
    toda_la_liga: dict | None,
    calendario: dict | None,
    marcador: dict | None,
    objetivos: list | None,
    jornada_de_hoy=None,
    ahora=None,
) -> dict:
    """
    Los ocho sentidos, con su edad calculada y lo que bloquean.

    Forma fija. Nunca lanza. Un sentido del que no llega nada sale
    igualmente, en MUERTO y diciendo que no llego: que falte una
    fila seria justo el fallo que este cuadro existe para enseñar.
    """

    vacio = {
        "available": False,
        "sentidos": [],
        "ciego": {
            "hay": False,
            "sin_pronostico": 0,
            "objetivos": 0,
            "reason": None,
        },
        "dias_para_viejo_sin_medir": DIAS_PARA_VIEJO,
        "alarma": {
            "hay": False,
            "cuantos": 0,
            "sentidos": [],
            "reason": None,
        },
        "reason": None,
    }

    try:
        # La hora viaja a las ocho filas. Si no llega, cada una
        # dira "sin referencia" en vez de un numero medido contra
        # el reloj del que mira.
        ahora = ahora

        filas = [
            _el_tablero(lineup, jornada_de_hoy, ahora),
            _el_ojeador(scout, ahora),
            _la_prensa(press, ahora),
            _la_vara(vara),
            _la_caja(rival_intelligence),
            _el_catalogo(toda_la_liga),
            _el_calendario(calendario, ahora),
            _el_marcador(marcador),
        ]

        # CADA SENTIDO CON SU TOPE DELANTE.
        #
        #     El tope y el motivo viajan EN LA FILA, no solo en
        #     la alarma: asi el cuadro puede decir "lleva 6 h de
        #     24" sin que nadie tenga que saberse la tabla.
        for fila in filas:

            tope = _el_tope(fila.get("sentido"))

            veredicto = _ha_caducado(fila, tope)

            fila["edad_maxima"] = {
                **tope,
                **veredicto,
            }

            fila["alarma_texto"] = (
                f"{fila.get('sentido')}: {veredicto['motivo']}"
                if veredicto.get("caducado")
                else None
            )

        alarma = la_alarma(filas)

        return {
            "available": True,
            "sentidos": filas,
            "ciego": _cuantos_a_ciegas(lineup, objetivos),
            "dias_para_viejo_sin_medir": DIAS_PARA_VIEJO,
            "muertos": [
                f["sentido"] for f in filas if f["estado"] == MUERTO
            ],

            # LA ALARMA, EN SU PROPIO BLOQUE.
            #
            #     El tablero se cayo 27 dias sin que nadie se
            #     enterara. La edad estaba calculada y a la vista
            #     desde el 13/09: lo que faltaba era que gritara.
            "alarma": alarma,

            "reason": (
                f"{len(filas)} sentidos, "
                f"{len([f for f in filas if f['estado'] == VIVO])} "
                f"vivos"
                + (
                    f", {alarma['cuantos']} por encima de su edad "
                    f"maxima"
                    if alarma["hay"]
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudieron montar los sentidos: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _cuantos_a_ciegas(lineup, objetivos) -> dict:
    """
    CUANTOS OBJETIVOS SALEN SIN PRONOSTICO, SOBRE EL TOTAL.

    SE CUENTA, NO SE PONE (regla 18). "64 de 64" tiene que salir
    de contar las filas; escrito a mano seria verdad hoy y
    mentira el dia que se arregle el tablero, que es justo el dia
    en que a nadie se le ocurriria mirar este numero.

    Y LO ENCIENDE EL HECHO (regla 37): el aviso sale porque el
    motor ha rechazado el tablero, no porque nos parezca que
    podria estar viejo.
    """

    estado = str(
        (lineup or {}).get("starter_cache_status") or ""
    ).upper()

    rechazado = estado.startswith("REJECTED")

    filas = [
        f for f in (objetivos or []) if isinstance(f, dict)
    ]

    sin_pronostico = [
        f
        for f in filas
        if str(f.get("xi_decision") or "").upper()
        == "SIN_PRONOSTICO"
    ]

    return {
        "hay": bool(rechazado and filas),
        "rechazado": rechazado,
        "estado_del_tablero": estado or None,
        "sin_pronostico": len(sin_pronostico),
        "objetivos": len(filas),

        # La frase del motor, entera y sin reescribir.
        "reason": (lineup or {}).get("starter_source_error"),
    }


# ============================================================
# LOS OCHO
# ============================================================


def _el_tablero(lineup, jornada_de_hoy, ahora) -> dict:
    datos = lineup or {}

    cuanto = edad(datos.get("starter_board_updated_at"), ahora)

    estado_cache = str(
        datos.get("starter_cache_status") or ""
    ).upper()

    rechazado = estado_cache.startswith("REJECTED")

    jornada = datos.get("starter_board_matchday")

    de_cuando = cuanto["texto"]

    if jornada is not None:
        de_cuando = f"Jornada {jornada} · {cuanto['texto']}"

    # UN TABLERO DE OTRA JORNADA NO DECIDE NADA (14/09/2026)
    #
    #     Aqui el "que decide" solo miraba si el motor lo habia
    #     RECHAZADO. Pero un tablero de la jornada 2 en la 7 esta
    #     igual de inservible aunque el motor todavia no lo haya
    #     tirado: la alarma diria "de la jornada 2" y al lado
    #     "decide que candidatos mejoran el once", que es
    #     justamente lo que ya no puede decidir.
    suya = safe_int(jornada, default=0)

    hoy = safe_int(jornada_de_hoy, default=0)

    desfasado = bool(suya and hoy and suya != hoy)

    return {
        "sentido": "Tablero de titulares",
        "para_que": "Quién va a jugar el próximo partido",
        "de_cuando": de_cuando,
        "edad": cuanto,
        "jornada": jornada,
        "jornada_de_hoy": jornada_de_hoy,
        "estado": _estado_por_edad(cuanto, muerto_si=rechazado),
        "estado_tecnico": estado_cache or None,

        # LA FRASE DEL MOTOR, ENTERA. No se reescribe.
        "que_bloquea": datos.get("starter_source_error"),
        "que_decide": (
            "Nada. Sin pronóstico no se puja para mejorar el "
            "once, y el techo del que se queda no se calcula."
            if (rechazado or desfasado)
            else "Qué candidatos mejoran el once."
        ),
    }


def _el_ojeador(scout, ahora) -> dict:
    datos = scout or {}

    cuanto = edad(datos.get("generated_at"), ahora)

    jornada = datos.get("matchday")

    de_cuando = cuanto["texto"]

    if jornada is not None:
        de_cuando = f"Jornada {jornada} · {cuanto['texto']}"

    # LAS FUENTES SON UN DICCIONARIO, NO UNA LISTA.
    #
    #     `scout.sources` es `{"FUTBOLFANTASY": {...}, ...}`.
    #     Recorrerlo como lista da las CLAVES —cadenas— y el
    #     filtro `isinstance(f, dict)` las tiraba todas: salia
    #     "0 de 0 fuentes vivas" con tres fuentes vivas.
    #
    #     Un cero por una suposicion sobre la forma del dato es
    #     el mismo fallo que "0 jornadas · 0 fichas": se lee como
    #     una averia y no lo es.
    #
    #     Y el motor ya publica el recuento en `sources_ok`: se
    #     coge de ahi en vez de volver a contarlo, que es como
    #     dos numeros de la misma cosa acaban discrepando.
    fuentes = datos.get("sources") or {}

    if isinstance(fuentes, dict):
        total = len(fuentes)

        vivas = safe_int(
            datos.get("sources_ok"),
            default=len(
                [
                    v
                    for v in fuentes.values()
                    if isinstance(v, dict) and v.get("ok")
                ]
            ),
        )

    else:
        total = len(fuentes)

        vivas = safe_int(datos.get("sources_ok"))

    return {
        "sentido": "Ojeador de precios",
        "para_que": "Si un precio sube o baja, y cuánto",
        "de_cuando": de_cuando,
        "edad": cuanto,
        "estado": _estado_por_edad(
            cuanto, muerto_si=not datos.get("available")
        ),
        "que_bloquea": datos.get("caveat"),
        "que_decide": (
            "La vía de revender, con la foto de "
            f"{cuanto['texto']}. No está roto: está caduco."
        ),
        "detalle": (
            f"{vivas} de {total} fuentes vivas · "
            f"{safe_int(datos.get('players_count'))} jugadores"
        ),
    }


def _la_prensa(press, ahora) -> dict:
    datos = press or {}

    cuanto = edad(datos.get("generated_at"), ahora)

    # Misma precaucion que en el ojeador: puede llegar como
    # diccionario o como lista, y contarlo mal da un cero que
    # parece una averia.
    fuentes = datos.get("sources") or {}

    return {
        "sentido": "Prensa",
        "para_que": "Lesiones y noticias",
        "de_cuando": cuanto["texto"],
        "edad": cuanto,
        "estado": _estado_por_edad(
            cuanto, muerto_si=not datos.get("available")
        ),
        "que_bloquea": datos.get("caveat"),
        "que_decide": "Hoy no decide nada: es observador.",
        "detalle": (
            f"{len(fuentes)} fuentes · "
            f"{safe_int(datos.get('players_with_signal'))} "
            f"jugadores con señal"
        ),
    }


def _la_vara(vara) -> dict:
    datos = vara or {}

    filas = [
        f for f in (datos.get("rows") or []) if isinstance(f, dict)
    ]

    ventana = datos.get("window") or {}

    activa = bool(datos.get("active"))

    return {
        "sentido": "La vara por posición",
        "para_que": "Cuánto vale un punto según el puesto",
        # LOS NOMBRES DE LA VENTANA, TAL Y COMO LOS PUBLICA.
        #
        #     `rounds` y `lineups` NO EXISTEN: se llaman
        #     `matchdays` y `players`. Con los nombres inventados
        #     salia "0 jornadas · 0 fichas", que se lee como una
        #     vara sin muestra —motivo de sobra para no fiarse de
        #     ella— cuando en realidad son 3 jornadas y 81 fichas.
        #
        #     Un cero por un nombre mal escrito es peor que un
        #     hueco: el hueco se pregunta, el cero se cree.
        "de_cuando": (
            f"{safe_int(ventana.get('matchdays'))} jornadas · "
            f"{safe_int(ventana.get('players'))} fichas"
            if ventana
            else "sin dato"
        ),
        "edad": {"dias": None, "horas": None, "texto": "de hoy"},
        "estado": VIVO if (activa and filas) else MUERTO,
        "que_bloquea": None if activa else datos.get("reason"),
        "que_decide": (
            "Aplicada al valorar cada posición."
            if activa
            else "Nada: no está activa."
        ),
        "detalle": datos.get("reason"),
    }


def _la_caja(rival_intelligence) -> dict:
    datos = rival_intelligence or {}

    reconstruccion = datos.get("cash_reconstruction") or {}

    comprobacion = datos.get("cash_check") or {}

    cuadra = comprobacion.get("ok")

    return {
        "sentido": "La caja de los ocho",
        "para_que": "Cuánto dinero tiene cada rival",
        "de_cuando": (
            f"Reconstruida hoy · "
            f"{safe_int(reconstruccion.get('events_read'))} "
            f"eventos"
        ),
        "edad": {"dias": 0, "horas": None, "texto": "de hoy"},

        # TRES CASOS, TRES ESTADOS.
        #
        #     cuadra        -> VIVO
        #     no cuadra     -> MUERTO, la caja de los ocho no vale
        #     no se sabe    -> depende de si LLEGO el bloque
        #
        #     "No se ha podido comprobar" y "no llego nada" no son
        #     lo mismo. Con el bloque delante y sin veredicto,
        #     VIEJO: hay dato y no esta confirmado. Sin bloque,
        #     MUERTO: no hay sentido que valga.
        #
        #     La primera version daba VIEJO a los dos, y un
        #     sentido que no llega salia como "existe pero esta
        #     fechado atras", que es justo lo contrario.
        "estado": (
            VIVO
            if cuadra is True
            else MUERTO
            if cuadra is False or not datos
            else VIEJO
        ),
        "que_bloquea": (
            None if cuadra else comprobacion.get("reason")
        ),
        "que_decide": (
            "El tope de puja de cada rival, y con él la amenaza."
        ),
        "detalle": comprobacion.get("reason")
        or reconstruccion.get("reason"),
    }


def _el_catalogo(toda_la_liga) -> dict:
    datos = toda_la_liga or {}

    censo = datos.get("plantillas") or {}

    cuadra = censo.get("cuadra")

    return {
        "sentido": "Catálogo y plantillas",
        "para_que": "De quién es cada jugador",
        "de_cuando": "Hoy",
        "edad": {"dias": 0, "horas": None, "texto": "de hoy"},
        "estado": VIVO if cuadra else MUERTO,
        "que_bloquea": (
            None
            if cuadra
            else (
                "La cuenta de plantillas no cuadra: hay "
                "jugadores contándose como libres sin serlo."
            )
        ),
        "que_decide": "Quién se puede fichar y quién no.",
        "detalle": (
            f"{safe_int(censo.get('con_dueño'))} con dueño + "
            f"{safe_int(censo.get('libres'))} libres = "
            f"{safe_int(censo.get('total'))}"
            if censo
            else "no llegó el censo"
        ),
    }


def _el_calendario(calendario, ahora) -> dict:
    datos = calendario or {}

    cuanto = edad(datos.get("fetched_at"), ahora)

    casan = datos.get("casan_todas")

    return {
        "sentido": "Calendario de LaLiga",
        "para_que": "Contra quién juega cada uno",
        "de_cuando": cuanto["texto"],
        "edad": cuanto,
        "estado": _estado_por_edad(
            cuanto, muerto_si=not datos.get("available")
        ),
        "que_bloquea": (
            None
            if casan is not False
            else (
                "Hay equipos del calendario que no casan con la "
                "clasificación: su puesto sale sin dato."
            )
        ),
        "que_decide": (
            "Hoy no lo usa ninguna decisión. Es para mirar."
        ),
        "detalle": datos.get("reason"),
    }


def _el_marcador(marcador) -> dict:
    datos = marcador or {}

    resumen = datos.get("resumen") or {}

    fiables = safe_int(resumen.get("jornadas_fiables"))

    return {
        "sentido": "El marcador",
        "para_que": "Cuánto rindió lo que hicimos",
        "de_cuando": (
            f"{safe_int(resumen.get('jornadas_medibles'))} "
            f"jornadas medibles"
            if resumen
            else "sin dato"
        ),
        "edad": {"dias": None, "horas": None, "texto": "sin dato"},
        "estado": VIVO if fiables else MUERTO,
        "que_bloquea": None if fiables else datos.get("reason"),
        "que_decide": (
            "Nada. Sin retorno medido, «mejorar el once» no "
            "tiene con qué competir contra «revender»."
            if not fiables
            else "Cuánto rinde cada vía."
        ),
        "detalle": datos.get("reason"),
    }
