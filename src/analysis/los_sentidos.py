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

    referencia = ahora or datetime.now(timezone.utc)

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
        "reason": None,
    }

    try:
        ahora = ahora or datetime.now(timezone.utc)

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

        return {
            "available": True,
            "sentidos": filas,
            "ciego": _cuantos_a_ciegas(lineup, objetivos),
            "dias_para_viejo_sin_medir": DIAS_PARA_VIEJO,
            "muertos": [
                f["sentido"] for f in filas if f["estado"] == MUERTO
            ],
            "reason": (
                f"{len(filas)} sentidos, "
                f"{len([f for f in filas if f['estado'] == VIVO])} "
                f"vivos."
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
            if rechazado
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

    fuentes = [
        f for f in (datos.get("sources") or []) if isinstance(f, dict)
    ]

    vivas = len(
        [
            f
            for f in fuentes
            if str(f.get("status") or "").upper()
            in ("OK", "VIVA", "ALIVE")
            or f.get("available")
        ]
    )

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
            f"{vivas} de {len(fuentes)} fuentes vivas · "
            f"{safe_int(datos.get('players_count'))} jugadores"
        ),
    }


def _la_prensa(press, ahora) -> dict:
    datos = press or {}

    cuanto = edad(datos.get("generated_at"), ahora)

    fuentes = [
        f for f in (datos.get("sources") or []) if isinstance(f, dict)
    ]

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
