from __future__ import annotations

"""
El marcador: lo unico que dice si Pepe juega bien.

POR QUE ESTO Y POR QUE HOY

    Llevamos seis dias construyendo y cero midiendo. No sabemos
    si nada de lo que hemos hecho produce un solo punto.

    Y es la unica tarea del proyecto con fecha de caducidad. Los
    datos que no se recogen no se recuperan: `/rounds/league`
    devuelve **la jornada en curso**, con todos a cero hasta que
    cierra. Cuando cierra y salta a la siguiente, los puntos de
    la anterior desaparecen de ese endpoint. Si nadie los anota
    en el momento, se pierden.

    Con 38 jornadas y la mitad del resultado siendo ruido, cinco
    jornadas perdidas son un tercio de la evidencia del año.

LAS TRES PREGUNTAS

    1. EL CONTRAFACTUAL DEL ONCE

       Que puntuo el once que Pepe alineo, contra lo que habria
       puntuado el mejor once legal de su propia plantilla, ya
       sabiendo los resultados.

       Mide el motor de alineacion SOLO: sin rivales, sin
       mercado, sin suerte de fichaje.

           ~90 % del optimo  -> el motor esta terminado, no tocarlo
           ~60 % del optimo  -> ahi esta la liga entera

    2. PUNTOS CONTRA LA LIGA

       Lo que puntuo Pepe frente a la media de los siete. Si sale
       sistematicamente por encima, el once esta bien elegido y
       todo lo demas es secundario.

    3. CUADRE

       Los puntos del once que reconstruimos tienen que coincidir
       con los que Biwenger le dio a Pepe en la clasificacion. Si
       no coinciden, el marcador esta mintiendo y hay que
       arreglarlo antes de creerselo.

COMO SE MIDEN LOS PUNTOS DE UNA JORNADA

    No por el array `fitness`: su indice no dice a que jornada
    pertenece cada valor —un jugador que se salta una jornada
    tiene el array mas corto, no un hueco—.

    Se miden por diferencia de totales. Se anota el total de
    puntos de cada jugador en la ultima observacion de cada
    jornada, y la jornada N vale:

        total(fin de N) - total(fin de N-1)

    Exacto y sin depender de como Biwenger ordene nada.

QUE NO HACE

    No decide. No escribe en Biwenger. No entra en ninguna
    valoracion ni en ningun guardarrail. Observa y anota.

    "Ausencia de dato != dato": una jornada sin observacion
    previa no se inventa, se marca `medible: false` y se queda
    fuera de las medias.
"""

import json

from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:                                 # pragma: no cover
    ZoneInfo = None


STATE_DIRECTORY = (
    Path("data")
    / "intelligence"
)

LEDGER_FILE = (
    STATE_DIRECTORY
    / "marcador.json"
)


# Las mismas siete que evalua el motor de alineacion. Si alli se
# añade una, aqui tiene que aparecer, o el "mejor once posible"
# quedaria por debajo de lo que Pepe podia alinear de verdad.
FORMACIONES = {
    "3-4-3": {1: 1, 2: 3, 3: 4, 4: 3},
    "3-5-2": {1: 1, 2: 3, 3: 5, 4: 2},
    "4-3-3": {1: 1, 2: 4, 3: 3, 4: 3},
    "4-4-2": {1: 1, 2: 4, 3: 4, 4: 2},
    "4-5-1": {1: 1, 2: 4, 3: 5, 4: 1},
    "5-3-2": {1: 1, 2: 5, 3: 3, 4: 2},
    "5-4-1": {1: 1, 2: 5, 3: 4, 4: 1},
}


# La primera jornada de la temporada 2026/27 en esta liga.
#
# Solo para ella el total de puntos de un jugador ES lo que
# puntuo esa jornada, porque no hay nada antes. Para cualquier
# otra hace falta la observacion de la anterior; sin ella la
# jornada se queda `medible: false` y no ensucia la media.
PRIMERA_JORNADA = 4899


# ================================================================
# LA FECHA DE VERDAD DE CADA JORNADA  (20/09/2026) - APAGADO
# ================================================================
#
# LO QUE YA ESTABA BIEN, Y HAY QUE DECIRLO PRIMERO
#
#     Este motor NO ordena por `round_id`. Desde el 14/09 ordena
#     por `primer_partido`, que sale del calendario. Doctrina 88:
#     lo viejo esta del otro lado del diff.
#
# LO QUE FALLA ES DE DONDE SALE ESA FECHA
#
#     `calendario_de_jornadas` tiene dos fuentes, y las dos son
#     ciegas a las jornadas aplazadas:
#
#         · los PARTIDOS de la foto traen la fecha exacta por
#           `round_id` — pero Biwenger solo publica los que
#           quedan por jugar. De las nueve jornadas observadas,
#           ocho no tienen ni un partido a la vista.
#
#         · el CALENDARIO DE LALIGA es el respaldo, y va por
#           NUMERO de jornada. «Jornada 1» y «Jornada 1
#           (aplazada)» son el numero 1 las dos, asi que se
#           llevan LA MISMA HORA.
#
#     Medido contra el tablon: 4937 «Jornada 1 (aplazada)» se
#     jugo el 25/08 y el calendario le pone el 15/08, que es el
#     de la Jornada 1. Y 5125 «Jornada 6 (aplazada)» se jugo el
#     15/09 y le pone el 03/09, que es el de la Jornada 6.
#
#     Con el empate, el desempate es el `round_id` — y ahi si
#     vuelve a mandar el numero. Por eso 4937 queda ANTES de
#     4900 y 5125 ANTES de 4902: las dos parejas rotas.
#
# LA FECHA EXACTA YA LA TENEMOS, Y NO LA ESTABAMOS PIDIENDO
#
#     El tablon publica `roundStarted` y `roundFinished` con el
#     `round_id` dentro y hasta un `part: 2` que marca la mitad
#     aplazada. Cubre las NUEVE observadas, al segundo, y el
#     fichero ya se carga cada vuelta para otras cosas: cero
#     peticiones nuevas.
#
#     Doctrina 103: no es que no lo supieramos, es que no lo
#     habiamos preguntado.
#
#     Se usa `roundStarted` y no `roundFinished` porque cubre las
#     nueve —4904 y 4905 no tienen fin— y porque donde estan las
#     dos, el orden que dan es el mismo.
#
# APAGADO el calendario es exactamente el de ayer.

ENV_POR_SU_FECHA = "BORDALAS_JORNADAS_POR_SU_FECHA"


def jornadas_por_su_fecha() -> bool:
    """Si la fecha de la jornada sale del tablon. Nunca lanza."""

    import os

    return str(
        os.environ.get(ENV_POR_SU_FECHA, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def fechas_del_tablon(eventos) -> dict:
    """`{round_id: {"empieza", "nombre", "part"}}` del tablon.

    Forma fija, nunca lanza. Los eventos entran por la puerta
    (regla 23): esta funcion no abre disco.

    De cada `roundStarted` se queda la MAS TEMPRANA: el tablon
    repite eventos y un duplicado no puede mover una jornada.
    """

    salida: dict[int, dict] = {}

    try:

        for evento in (eventos or []):

            if not isinstance(evento, dict):
                continue

            if evento.get("type") != "roundStarted":
                continue

            contenido = evento.get("content")

            if isinstance(contenido, list):
                contenido = contenido[0] if contenido else {}

            if not isinstance(contenido, dict):
                continue

            ronda = contenido.get("round") or {}

            round_id = safe_int(ronda.get("id"))

            momento = _momento(evento.get("date"))

            if not round_id or momento is None:
                continue

            fila = salida.get(round_id)

            if fila is None or momento < fila["momento"]:

                salida[round_id] = {
                    "round_id": round_id,
                    "momento": momento,
                    "nombre": ronda.get("name"),

                    # `part: 2` es como el propio Biwenger marca
                    # la mitad aplazada. Viaja porque explica por
                    # que esta fila existe.
                    "part": ronda.get("part"),
                }

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def ensure_state_directory() -> None:
    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# EL ORDEN DEL TIEMPO
# ============================================================
#
# `round_id` NO ES EL TIEMPO (14/09/2026)
#
#     Este motor ordenaba las jornadas por `round_id` y daba por
#     hecho que ese orden era el del calendario. Es falso, y esta
#     liga lo demuestra sola: la jornada 6 viene PARTIDA EN DOS
#     IDS porque uno de sus partidos se adelanto.
#
#         round 4903  Jornada 5              10 partidos  13-14/09
#         round 4904  Jornada 6               1 partido      03/09
#         round 5125  Jornada 6 (aplazada)   19 partidos  15-17/09
#
#     Ordenando por id, 4903 queda como "previa" de 4904 — pero
#     el partido de 4904 se jugo DIEZ DIAS ANTES. La resta de
#     totales acumulados va entonces al reves y salen puntos
#     negativos: es el `mejor_puntos: -55` que aparecio en
#     pantalla, un "mejor once posible" que no puede existir.
#
#     Y la lista de jornadas que publica Biwenger no viene
#     ordenada por id tampoco: 4904 aparece entre 4901 y 4902.
#
# LA CLAVE DE ORDEN ES LA HORA DEL PRIMER PARTIDO.
#
#     No se deduce del id, no se deduce del nombre y no se
#     deduce del momento en que miramos: se pregunta al
#     calendario, que es quien lo sabe. Una jornada sin hora no
#     se coloca a ojo — se queda sin medir y se dice.


def _momento(valor):
    """Una marca de tiempo con zona, o `None`. Nunca lanza.

    Acepta lo que traen las dos fuentes: ISO (calendario de
    LaLiga) y epoch en segundos (partidos de Biwenger).
    """

    if valor is None:
        return None

    if isinstance(valor, datetime):
        cuando = valor

    elif isinstance(valor, (int, float)):

        try:
            cuando = datetime.fromtimestamp(
                float(valor), timezone.utc
            )

        except (OverflowError, OSError, ValueError):
            return None

    else:

        try:
            cuando = datetime.fromisoformat(
                str(valor).replace("Z", "+00:00")
            )

        except (TypeError, ValueError):
            return None

    if cuando.tzinfo is None:
        return cuando.replace(tzinfo=timezone.utc)

    return cuando


def calendario_de_jornadas(
    rondas,
    partidos=None,
    kickoff_por_jornada=None,
    eventos=None,
) -> dict:
    """Cuando se jugo cada jornada. Forma fija. Nunca lanza.

    Devuelve `{round_id: {"primer_partido", "fuente", "nombre"}}`.

    DOS FUENTES, Y LA BUENA GANA

        `partidos` son los partidos de verdad, con su `round` y
        su fecha: es la hora EXACTA del primer partido de ese
        `round_id` y manda siempre que este.

        `kickoff_por_jornada` es el calendario de LaLiga, por
        NUMERO de jornada. Sirve de respaldo para las jornadas
        de las que ya no quedan partidos a la vista.

        La fuente se escribe en cada fila. Una hora de respaldo
        no es lo mismo que una medida, y quien lea esto tiene
        que poder distinguirlas sin preguntar.

    NO SE INVENTA NINGUNA. Una jornada sin hora en ninguna de las
    dos fuentes sale sin `primer_partido`, y el marcador la deja
    sin medir en vez de colocarla donde le parezca.
    """

    salida = {}

    try:

        # 1. EL RESPALDO: el calendario de LaLiga, por numero.
        por_numero = {}

        for numero, cuando in (kickoff_por_jornada or {}).items():

            momento = _momento(cuando)

            if momento is not None:
                por_numero[safe_int(numero)] = momento

        for ronda in (rondas or []):

            if not isinstance(ronda, dict):
                continue

            round_id = safe_int(ronda.get("id"))

            if not round_id:
                continue

            nombre = str(ronda.get("name") or "")

            # "Jornada 6" y "Jornada 6 (aplazada)" son la MISMA
            # jornada de LaLiga: las dos caen en el numero 6.
            numero = None

            for trozo in nombre.replace("(", " ").split():

                if trozo.isdigit():
                    numero = int(trozo)
                    break

            respaldo = por_numero.get(numero)

            salida[round_id] = {
                "round_id": round_id,
                "nombre": nombre,
                "numero": numero,
                "primer_partido": (
                    respaldo.isoformat()
                    if respaldo is not None
                    else None
                ),
                "fuente": (
                    "CALENDARIO_DE_LALIGA"
                    if respaldo is not None
                    else None
                ),
            }

        # 2. LA BUENA: los partidos de verdad. Pisan al respaldo.
        primero = {}

        for partido in (partidos or []):

            if not isinstance(partido, dict):
                continue

            ronda = partido.get("round")

            round_id = safe_int(
                ronda.get("id")
                if isinstance(ronda, dict)
                else ronda
            )

            momento = _momento(
                partido.get("date")
                or partido.get("kickoff")
            )

            if not round_id or momento is None:
                continue

            if (
                round_id not in primero
                or momento < primero[round_id]
            ):
                primero[round_id] = momento

        for round_id, momento in primero.items():

            fila = salida.setdefault(
                round_id,
                {
                    "round_id": round_id,
                    "nombre": "",
                    "numero": None,
                    "primer_partido": None,
                    "fuente": None,
                },
            )

            fila["primer_partido"] = momento.isoformat()
            fila["fuente"] = "PARTIDOS_DE_LA_JORNADA"

        # ------------------------------------------------
        # 3. LA MEJOR: EL TABLON  (20/09/2026) - APAGADA
        #
        #     `roundStarted` trae el `round_id` dentro, asi que
        #     es la unica de las tres que distingue «Jornada 6»
        #     de «Jornada 6 (aplazada)». Manda sobre las otras
        #     dos, incluida la de los partidos: esa es exacta
        #     pero solo cubre lo que queda por jugar.
        #
        #     Apagada, no toca nada.
        # ------------------------------------------------

        if jornadas_por_su_fecha():

            for round_id, fila_tablon in fechas_del_tablon(
                eventos
            ).items():

                fila = salida.setdefault(
                    round_id,
                    {
                        "round_id": round_id,
                        "nombre": fila_tablon.get("nombre") or "",
                        "numero": None,
                        "primer_partido": None,
                        "fuente": None,
                    },
                )

                fila["primer_partido"] = (
                    fila_tablon["momento"].isoformat()
                )

                fila["fuente"] = "EVENTOS_DEL_TABLON"

                # La mitad aplazada, con el nombre que le da
                # Biwenger. Es lo que explica por que esta fila
                # no comparte hora con su hermana.
                if fila_tablon.get("part") is not None:
                    fila["part"] = fila_tablon["part"]

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def kickoff_por_jornada(calendario_laliga) -> dict:
    """`{numero de jornada: primer partido}` del calendario oficial.

    Forma fija. Nunca lanza. Es el RESPALDO de
    `calendario_de_jornadas`: sirve para las jornadas viejas, de
    las que Biwenger ya no publica partidos.
    """

    salida = {}

    try:

        for jornada in (
            (calendario_laliga or {}).get("matchdays") or []
        ):

            if not isinstance(jornada, dict):
                continue

            numero = safe_int(jornada.get("matchday"))

            if not numero:
                continue

            for partido in (jornada.get("matches") or []):

                if not isinstance(partido, dict):
                    continue

                momento = _momento(partido.get("kickoff"))

                if momento is None:
                    continue

                if (
                    numero not in salida
                    or momento < salida[numero]
                ):
                    salida[numero] = momento

        return {
            numero: momento.isoformat()
            for numero, momento in salida.items()
        }

    except Exception:                               # noqa: BLE001
        return {}


def calendario_desde_la_foto(
    snapshot,
    calendario_laliga=None,
    eventos=None,
) -> dict:
    """El calendario de jornadas que sale de la foto. Nunca lanza.

    La foto entra por la puerta (regla 23): esta funcion no lee
    disco, la llama quien ya la tiene cargada.

    De la foto salen las dos cosas: la lista de jornadas de la
    temporada (`season.rounds`) y los partidos con fecha que
    todavia se ven. El calendario de LaLiga pone el respaldo.
    """

    try:

        catalogo = (
            (snapshot or {}).get("catalog") or {}
        ).get("data") or {}

        rondas = (
            (catalogo.get("season") or {}).get("rounds") or []
        )

        partidos = []

        for equipo in (catalogo.get("teams") or {}).values():

            if isinstance(equipo, dict):
                partidos.extend(equipo.get("nextGames") or [])

        for evento in (catalogo.get("activeEvents") or []):

            if isinstance(evento, dict):
                partidos.extend(evento.get("games") or [])

        return calendario_de_jornadas(
            rondas,
            partidos=partidos,
            kickoff_por_jornada=kickoff_por_jornada(
                calendario_laliga
            ),

            # Los eventos del tablon, que ya se cargan cada
            # vuelta para contar la puerta de los managers.
            # Entran por la puerta, como todo lo demas.
            eventos=eventos,
        )

    except Exception:                               # noqa: BLE001
        return {}


def orden_en_el_tiempo(jornadas, calendario) -> dict:
    """Las jornadas observadas, en el orden en que se jugaron.

    Forma fija. Nunca lanza.

        `ordenadas`  las que tienen hora, de antes a despues
        `sin_hora`   las que no se pueden colocar, con su motivo

    LOS EMPATES SE DESHACEN POR ID, y solo por estabilidad: dos
    jornadas con el mismo primer partido son un caso raro, y lo
    que no puede pasar es que el orden cambie entre dos vueltas
    sin que cambien los datos.
    """

    ordenadas = []
    sin_hora = []

    try:

        for jornada in (jornadas or []):

            if not isinstance(jornada, dict):
                continue

            round_id = safe_int(jornada.get("round_id"))

            fila = (calendario or {}).get(round_id) or {}

            momento = _momento(fila.get("primer_partido"))

            if momento is None:
                sin_hora.append({
                    "round_id": round_id,
                    "motivo": (
                        f"No se sabe cuando se jugo la jornada "
                        f"{round_id}: sin la hora de su primer "
                        f"partido no se puede saber que jornada "
                        f"va antes, y la resta de totales daria "
                        f"un numero inventado."
                    ),
                })
                continue

            ordenadas.append({
                "round_id": round_id,
                "jornada": jornada,
                "momento": momento,
                "fuente": fila.get("fuente"),
            })

        ordenadas.sort(
            key=lambda item: (item["momento"], item["round_id"])
        )

        return {
            "ordenadas": ordenadas,
            "sin_hora": sin_hora,
        }

    except Exception:                               # noqa: BLE001
        return {"ordenadas": ordenadas, "sin_hora": sin_hora}


def jornadas_en_medio(anterior, actual, calendario) -> list:
    """Las jornadas del calendario que caen ENTRE dos observadas.

    Forma fija, siempre una lista. Nunca lanza.

    POR QUE HACE FALTA AUNQUE EL ORDEN YA ESTE BIEN

        Ordenar arregla la causa, pero no el hueco. Si en el
        libro estan la 1 y la 4 y faltan la 2 y la 3, la resta de
        totales cubre TRES jornadas y se publica como si fuera
        una. El numero sale mal de otra manera, y ningun orden lo
        ve: hay que preguntarle al calendario quien falta.

    Se miran las que caen ESTRICTAMENTE en medio. Una jornada con
    el mismo primer partido que otra —las dos mitades de una
    jornada partida— no cuenta como hueco.
    """

    faltan = []

    try:

        desde = _momento(anterior)
        hasta = _momento(actual)

        if desde is None or hasta is None:
            return faltan

        for round_id, fila in (calendario or {}).items():

            momento = _momento(
                (fila or {}).get("primer_partido")
            )

            if momento is None:
                continue

            if desde < momento < hasta:
                faltan.append({
                    "round_id": safe_int(round_id),
                    "nombre": (fila or {}).get("nombre") or "",
                    "primer_partido": momento.isoformat(),
                })

        faltan.sort(key=lambda item: item["primer_partido"])

        return faltan

    except Exception:                               # noqa: BLE001
        return faltan


# ================================================================
# EL ONCE DESPLAZADO UNA JORNADA  (28/10/2026)
# ================================================================
#
# EL SINTOMA
#
#     Nueve jornadas cerradas y medibles, CERO fiables, y
#     `eficiencia_media: null` desde septiembre. La bitacora del
#     24/10 ya lo habia visto: «marcador.json guarda mi_once
#     desplazado una jornada desde la 4902».
#
# LA CAUSA: DOS RELOJES EN UNA MISMA ENTRADA
#
#     `observar()` guarda la entrada bajo `rounds.data.round.id`
#     y la sobreescribe en cada vuelta. Ese id tiene DOS retrasos
#     encima:
#
#         · Biwenger no lo pasa a la siguiente hasta su pitido.
#         · La vuelta lo lee de la cache del reset (07/09): se
#           refresca una vez al dia, por la mañana.
#
#     Asi que la ULTIMA escritura de la ronda R cae la mañana
#     DESPUES del pitido de la siguiente. Y en esa escritura el
#     once sale de `user_lineup`, que desde el 14/09 es la fuente
#     (`once_del_dueno`). Con `lineupRoundChanges: 0` (tablon,
#     11/08) el once se bloquea en el pitido, y a partir de ahi
#     `user_lineup` ya es el once EDITABLE DE LA SIGUIENTE.
#
#     Resultado: `jornadas[R].mi_once` es el once de la ronda que
#     va DESPUES de R. Medido en el libro del 28/10 contra el
#     once congelado antes del pitido (`onces_de_la_jornada`):
#
#         entrada  escrita (Madrid) su mi_once es el de
#         4906     17/10 04:52      J9  (4907)  = congelado J9  exacto
#         5176     24/10 04:52      J10 (4908)  = congelado J10 exacto
#         4908     28/10 20:10      J11         (el del parte de hoy)
#
#     (La J9 pito el 16/10 a las 21:00 y la J10 el 23/10 a las
#     21:00: las dos entradas se escribieron unas ocho horas
#     despues, con el once ya bloqueado.)
#
#     Y con los puntos: el once de la entrada 4906 suma 49 en la
#     J9 (Biwenger: 49); el de la 4907 suma 56. El de la entrada
#     5176 suma 39 en la J10 (Biwenger: 39); el de la 4908, el
#     de la J11, no jugo la J10.
#
#     Hasta la 4902 la fuente era la `lineup` de `standings`,
#     que viene en la MISMA respuesta que el id: esas entradas
#     guardan el once de su propia ronda (J3 suma 61 = 61). El
#     desplazamiento empieza con la primera escrita desde
#     `user_lineup`, la 4903 (16/09).
#
# Y EL COMPARADOR TAMBIEN IBA DESPLAZADO
#
#     `puntos_biwenger` salia de restar la clasificacion de dos
#     entradas. La clasificacion viaja en la misma cache: a la
#     5125 le tocaban los 61 de la J5 y a la 4905 los 29+47 de la
#     J6 y la J7 juntos. La verdad por ronda ya la publica el
#     tablon: `roundFinished` trae los puntos de cada manager con
#     el `round_id` dentro. En una ronda partida trae el
#     ACUMULADO de la jornada (J1 aplazada: 41 = 29 + 12; J6
#     parte 3: 40 = 29 + 11, cuadrado manager a manager contra la
#     clasificacion), asi que la parte vale la resta.
#
# EL ARREGLO
#
#     1. LECTURA (repara el historico sin tocar `data/`). El once
#        de cada entrada se le asigna a la ronda que estaba en
#        juego cuando se VIO: la del ultimo pitido anterior a
#        `datos_de` (hora de Madrid, ver `_hora_del_sello`), si
#        no habia cerrado ya. La verdad, del tablon. Los puntos
#        por jugador, de la resta de siempre entre dos entradas;
#        la foto de cierre de LaLiga solo rellena a los que no
#        estan en las dos, y solo si pasa la prueba de fugas (ver
#        `LA FOTO DE CIERRE SE HACE ANTES DE PUNTUAR EL LUNES`).
#
#     2. ESCRITURA (para que no vuelva a pasar). La entrada se
#        guarda bajo la ronda EN JUEGO segun el tablon, y el once
#        de una entrada nueva se escribe UNA vez: la primera vista
#        tras el pitido, que es el bloqueado.
#
# LO QUE NO SE ARREGLA, Y SE DICE EN LA FILA
#
#     · Rondas partidas (aplazadas): Biwenger las puntua con el
#       once bloqueado en SU pitido, y si el once se toco esa
#       misma noche para la siguiente, la vista de la mañana ya no
#       es la buena (J6 parte 3: la puntuo el once de la J9).
#     · Rondas sin `roundFinished` en el tablon: J8 (nadie la
#       cobro) y J6 parte 1 (`splitRound: ignoreFirst`). Sin
#       verdad no hay cuadre.
#     · J5: su once no se guardo nunca (la 4902 guardaba el suyo
#       y la 4903 ya el de la siguiente).
#     · Vendidos antes de la foto y correcciones retroactivas de
#       Biwenger: las de siempre.

# De donde sale el once que se le asigna a cada ronda. Viajan en
# la fila para que la pantalla diga cual es cual sin adivinar.
ONCE_DE_SU_CLASIFICACION = "LA_CLASIFICACION_DE_SU_RONDA"
ONCE_PRIMERA_VISTA = "PRIMERA_VISTA_TRAS_EL_PITIDO"
ONCE_VISTO_EN_OTRA_ENTRADA = "VISTO_CON_LA_RONDA_EN_JUEGO"
ONCE_CONGELADO = "CONGELADO_ANTES_DEL_PITIDO"

# La marca de una entrada escrita con la regla nueva: su
# `mi_once` es el de su ronda y no se reescribe.
REGLA_PRIMERA_VISTA = "PRIMERA_VISTA"

# De donde sale la verdad con la que se cuadra.
VERDAD_DEL_TABLON = "TABLON_ROUND_FINISHED"
VERDAD_DE_LA_CLASIFICACION = "CLASIFICACION_RESTADA"

# De donde salen los puntos de cada jugador.
PUNTOS_DEL_CIERRE = "CIERRE_DE_LA_JORNADA_DE_LALIGA"
PUNTOS_DE_LA_RESTA = "RESTA_DE_OBSERVACIONES"


def numero_de_jornada(nombre) -> int | None:
    """«Jornada 6 (aplazada)» -> 6. `None` si no lo lleva."""

    for trozo in str(nombre or "").replace("(", " ").split():

        if trozo.isdigit():
            return int(trozo)

    return None


def es_aplazada(nombre, part=None) -> bool:
    """¿Es una parte de una jornada partida? Nunca lanza."""

    return (
        safe_int(part) >= 2
        or "aplazad" in str(nombre or "").lower()
    )


def _contenido(evento) -> dict:

    contenido = (evento or {}).get("content")

    if isinstance(contenido, list):
        contenido = contenido[0] if contenido else {}

    return contenido if isinstance(contenido, dict) else {}


def cierres_del_tablon(eventos) -> dict:
    """Cuando empezo y cerro cada ronda, y lo que pago. Nunca lanza.

    `{round_id: {"round_id", "nombre", "numero", "part",
    "empieza", "termina", "acumulado", "puntos"}}`

        empieza    `roundStarted` (el mas temprano)
        termina    `roundFinished` (el mas temprano), o None
        acumulado  `{user_id: puntos}` tal cual lo da el tablon
        puntos     lo que pago ESTA ronda: en una parte de una
                   jornada partida, el acumulado menos el de la
                   parte anterior que cerro

    Los eventos entran por la puerta (regla 23).
    """

    salida: dict[int, dict] = {}

    try:

        for evento in (eventos or []):

            if not isinstance(evento, dict):
                continue

            tipo = evento.get("type")

            if tipo not in ("roundStarted", "roundFinished"):
                continue

            contenido = _contenido(evento)
            ronda = contenido.get("round") or {}
            round_id = safe_int(ronda.get("id"))
            momento = _momento(evento.get("date"))

            if not round_id or momento is None:
                continue

            fila = salida.setdefault(round_id, {
                "round_id": round_id,
                "nombre": ronda.get("name") or "",
                "numero": numero_de_jornada(ronda.get("name")),
                "part": ronda.get("part"),
                "empieza": None,
                "termina": None,
                "acumulado": None,
                "puntos": None,
            })

            if tipo == "roundStarted":

                if fila["empieza"] is None or momento < fila["empieza"]:
                    fila["empieza"] = momento

                continue

            if fila["termina"] is not None and momento >= fila["termina"]:
                continue

            fila["termina"] = momento

            acumulado = {}

            for resultado in (contenido.get("results") or []):

                if not isinstance(resultado, dict):
                    continue

                user_id = safe_int(
                    (resultado.get("user") or {}).get("id")
                )

                if user_id:
                    acumulado[user_id] = safe_int(resultado.get("points"))

            fila["acumulado"] = acumulado

        # LA PARTE VALE LA RESTA. Por numero de jornada y en orden
        # de pitido: cada parte cerrada le resta a la anterior
        # cerrada de su misma jornada.
        por_numero: dict[int, list] = {}

        for fila in salida.values():

            if fila["numero"] is not None:
                por_numero.setdefault(fila["numero"], []).append(fila)

        for fila in salida.values():

            if fila["acumulado"] is None:
                continue

            anterior = None

            for otra in por_numero.get(fila["numero"], []):

                if (
                    otra is fila
                    or otra["acumulado"] is None
                    or otra["empieza"] is None
                    or fila["empieza"] is None
                    or otra["empieza"] >= fila["empieza"]
                ):
                    continue

                if anterior is None or otra["empieza"] > anterior["empieza"]:
                    anterior = otra

            base = (anterior or {}).get("acumulado") or {}

            fila["puntos"] = {
                user_id: puntos - safe_int(base.get(user_id))
                for user_id, puntos in fila["acumulado"].items()
            }

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def ronda_en_juego(cierres, momento) -> int | None:
    """La ronda del ultimo pitido anterior a `momento`. Nunca lanza.

    `cierres` es lo que devuelve `cierres_del_tablon`. Es la ronda
    a la que pertenecen el once bloqueado y los puntos que se ven
    en ese momento, diga lo que diga `rounds.data.round.id`.
    """

    try:

        cuando = _momento(momento)

        if cuando is None:
            return None

        mejor = None

        for round_id, fila in (cierres or {}).items():

            empieza = (fila or {}).get("empieza")

            if empieza is None or empieza > cuando:
                continue

            if mejor is None or (empieza, round_id) > mejor:
                mejor = (empieza, safe_int(round_id))

        return mejor[1] if mejor else None

    except Exception:                               # noqa: BLE001
        return None


def _pitidos(calendario, cierres) -> dict:
    """`{round_id: datetime}` del pitido de cada ronda. Manda el
    tablon; el calendario es el respaldo."""

    salida = {}

    for round_id, fila in (calendario or {}).items():

        momento = _momento((fila or {}).get("primer_partido"))

        if momento is not None and safe_int(round_id):
            salida[safe_int(round_id)] = momento

    for round_id, fila in (cierres or {}).items():

        if (fila or {}).get("empieza") is not None:
            salida[safe_int(round_id)] = fila["empieza"]

    return salida


def _nombres_de_ronda(calendario, cierres) -> dict:

    salida = {}

    for round_id, fila in (calendario or {}).items():
        salida[safe_int(round_id)] = {
            "nombre": (fila or {}).get("nombre") or "",
            "part": (fila or {}).get("part"),
        }

    for round_id, fila in (cierres or {}).items():

        if (fila or {}).get("nombre"):
            salida[safe_int(round_id)] = {
                "nombre": fila["nombre"],
                "part": fila.get("part"),
            }

    return salida


def _ids(once) -> list:

    return [
        safe_int(p.get("id") if isinstance(p, dict) else p)
        for p in ((once or {}).get("players") or [])
        if safe_int(p.get("id") if isinstance(p, dict) else p)
    ]


def el_once_de_cada_ronda(
    entradas,
    calendario=None,
    cierres=None,
    congelados=None,
) -> dict:
    """Que once jugo cada ronda, y de donde sale. Nunca lanza.

    `{round_id: {"players", "formation", "fuente", "de_la_entrada",
    "visto_en", "once_alternativo", "onces_por_vara"}}`

    CUATRO FUENTES, POR ESTE ORDEN

        1. Entrada de antes del 14/09 (sin `escrito_en`): su
           `mi_once` salia de `standings`, en la misma respuesta
           que el id. Es el de SU ronda.
        2. Entrada escrita con la regla nueva (`regla:
           PRIMERA_VISTA`): su once es el de su ronda.
        3. Entrada de entre medias: su `mi_once` es el que se
           veia en `datos_de`, y eso es el once de la ronda EN
           JUEGO a esa hora, si no habia cerrado ya. Si hay
           varias, la vista mas temprana: la mas cerca del
           bloqueo.
        4. El once congelado antes del pitido de la jornada de
           LaLiga (`onces_de_la_jornada`), solo para las rondas
           normales. Respaldo.

    Si el once trae `guardado` (cuando lo grabo el dueño) y es
    POSTERIOR al pitido, no es el bloqueado: se descarta.
    """

    salida: dict[int, dict] = {}

    try:

        pitidos = _pitidos(calendario, cierres)
        cierres = cierres or {}

        ordenados = sorted(
            pitidos.items(),
            key=lambda par: (par[1], par[0]),
        )

        def en_juego(cuando):
            elegido = None
            for round_id, momento in ordenados:
                if momento <= cuando:
                    elegido = round_id
            return elegido

        candidatos: dict[int, list] = {}

        def proponer(round_id, entrada, once, fuente, prioridad, visto):

            players = _ids(once)

            if not round_id or not players:
                return

            guardado = _momento((once or {}).get("guardado"))
            pitido = pitidos.get(round_id)

            # Grabado DESPUES del pitido: con `lineupRoundChanges:
            # 0` eso ya es el de la siguiente.
            if (
                guardado is not None
                and pitido is not None
                and guardado > pitido
            ):
                return

            candidatos.setdefault(round_id, []).append({
                "round_id": round_id,
                "players": players,
                "formation": (once or {}).get("formation"),
                "fuente": fuente,
                "de_la_entrada": safe_int((entrada or {}).get("round_id")) or None,
                "visto_en": visto.isoformat() if visto else None,
                "once_alternativo": (entrada or {}).get("once_alternativo"),
                "onces_por_vara": (entrada or {}).get("onces_por_vara"),
                "_orden": (
                    prioridad,
                    visto or datetime.max.replace(tzinfo=timezone.utc),
                ),
            })

        for entrada in (entradas or []):

            if not isinstance(entrada, dict):
                continue

            propia = safe_int(entrada.get("round_id"))
            once = entrada.get("mi_once") or {}

            if "escrito_en" not in entrada:
                proponer(propia, entrada, once, ONCE_DE_SU_CLASIFICACION, 0, None)
                continue

            # LA HORA DE LA FOTO, COMO LA LEE QUIEN ESCRIBE. `datos_de`
            # y `visto_en` son hora de Madrid con la etiqueta
            # `+00:00`; leidos tal cual van una o dos horas tarde y
            # una vista de antes del pitido se le colgaba a la ronda
            # siguiente. Ver `_hora_del_sello`.
            if once.get("regla") == REGLA_PRIMERA_VISTA:
                proponer(
                    propia, entrada, once, ONCE_PRIMERA_VISTA, 0,
                    _hora_del_sello(once.get("visto_en") or entrada.get("datos_de")),
                )
                continue

            visto = _hora_del_sello(entrada.get("datos_de"))

            if visto is None:
                continue

            dueno = en_juego(visto)

            if dueno is None:
                continue

            termina = (cierres.get(dueno) or {}).get("termina")

            # Ya habia cerrado: lo que se veia era el once editable
            # de la que viene, que todavia no tiene ronda.
            if termina is not None and termina <= visto:
                continue

            proponer(dueno, entrada, once, ONCE_VISTO_EN_OTRA_ENTRADA, 1, visto)

        # 4. EL CONGELADO, por numero de jornada de LaLiga y solo
        # para la ronda normal de ese numero.
        normal_de = {}

        for round_id, fila in _nombres_de_ronda(calendario, cierres).items():

            numero = numero_de_jornada(fila.get("nombre"))

            if numero and not es_aplazada(fila.get("nombre"), fila.get("part")):
                normal_de.setdefault(numero, round_id)

        for linea in (congelados or []):

            if not isinstance(linea, dict):
                continue

            round_id = normal_de.get(safe_int(linea.get("matchday")))

            proponer(
                round_id,
                {"round_id": None},
                {
                    "players": linea.get("players"),
                    "formation": linea.get("formation"),
                    "guardado": linea.get("guardado_en"),
                },
                ONCE_CONGELADO,
                2,
                _momento(linea.get("anotado_en")),
            )

        for round_id, lista in candidatos.items():

            lista.sort(key=lambda c: c["_orden"])

            elegido = dict(lista[0])
            elegido.pop("_orden", None)

            # EL CRUCE: si tambien esta el congelado, se dice si
            # coincide. Dos fuentes que dicen lo mismo valen mas
            # que una.
            congelado = next(
                (c for c in lista if c["fuente"] == ONCE_CONGELADO),
                None,
            )

            elegido["congelado_coincide"] = (
                set(congelado["players"]) == set(elegido["players"])
                if congelado is not None
                and elegido["fuente"] != ONCE_CONGELADO
                else None
            )

            salida[round_id] = elegido

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def _ventana_de_cierre(fotos, momento):
    """Las dos fotos de cierre de LaLiga entre las que cae
    `momento`: `(previa, actual)`, o `None`."""

    cuando = _momento(momento)

    if cuando is None:
        return None

    por_jornada = {}

    for foto in (fotos or []):

        if isinstance(foto, dict) and safe_int(foto.get("jornada")):
            por_jornada.setdefault(safe_int(foto["jornada"]), foto)

    for numero, actual in por_jornada.items():

        previa = por_jornada.get(numero - 1)

        if previa is None:
            continue

        desde = _momento(previa.get("cerrada_en"))
        hasta = _momento(actual.get("cerrada_en"))

        if desde is None or hasta is None:
            continue

        if desde < cuando <= hasta:
            return previa, actual

    return None


def _resta_de_fotos(previa, actual) -> dict:
    """`{id: (puntos, jugados)}` entre dos fotos de cierre."""

    antes = (previa or {}).get("players") or {}
    salida = {}

    for player_id, fila in ((actual or {}).get("players") or {}).items():

        if player_id not in antes:
            continue

        try:
            salida[str(player_id)] = (
                safe_int(fila[0]) - safe_int(antes[player_id][0]),
                safe_int(fila[1]) - safe_int(antes[player_id][1]),
            )
        except (TypeError, IndexError, KeyError):
            continue

    return salida


# ================================================================
# LA FOTO DE CIERRE SE HACE ANTES DE PUNTUAR EL LUNES  (28/10/2026)
# ================================================================
#
#     La foto de cierre de LaLiga (`puntos_por_jornada.jsonl`) se
#     toma unas dos horas despues del ultimo partido del lunes, a
#     las 21:00, y Biwenger todavia no lo ha puntuado. Asi que cada
#     ventana (cierre N-1, cierre N] lleva el lunes de la ronda
#     ANTERIOR y le falta el suyo:
#
#         J8 -> J9   lleva Levante-Sevilla (lunes de la J8, 12/10)
#                    y le falta Getafe-Rayo (lunes de la J9, 19/10):
#                    26 jugadores con DOS partidos. Olasagasti 9 (6
#                    del lunes de la J8 + 3), Unai Lopez 0.
#         J9 -> J10  lleva Getafe-Rayo y la J6 aplazada: 56 con dos.
#                    Le falta Sevilla-Osasuna (26/10): Kike Salas,
#                    foto 28 y libro 35.
#
#     La J9 salia «49 = 49, cuadra» por dos errores que se anulan
#     (+6 de Olasagasti, -5 de Unai Lopez). Con los puntos de la
#     resta de entradas, que va de cache a cache (la mañana de un
#     pitido a la del siguiente), el mismo once suma 48.
#
#     Por eso:
#
#         · Los puntos de la ronda son SIEMPRE la resta de dos
#           entradas.
#         · La foto solo rellena a quien no esta en las dos
#           (vendido o fichado entre medias), y solo si la ventana
#           pasa la prueba de fugas: nadie con dos partidos, y la
#           foto dice lo mismo que la resta en todos los que estan
#           en las dos.
#         · Un cero cierto (`_sin_partido`), igual: o la ventana
#           pasa esa prueba, o el (0, 0) va de una foto anterior
#           al pitido a una posterior al cierre del tablon, que
#           cubre la ronda entera pase lo que pase con el lunes.

# Partidos que puede jugar un jugador en UNA ronda normal. Con
# mas, la ventana lleva partidos de otra.
PARTIDOS_POR_RONDA = 1


def fugas_de_la_ventana(por_foto, por_entradas=None) -> dict:
    """¿Lleva la ventana partidos de otra ronda, o le faltan los
    suyos? Nunca lanza.

    `por_foto` es `{id: (puntos, jugados)}` entre dos fotos de
    cierre; `por_entradas`, `{id: puntos}` de la resta de dos
    entradas, solo con los que estan en las dos.

    `{"limpia", "dos_partidos", "desacuerdos", "motivo"}`
    """

    salida = {
        "limpia": False,
        "dos_partidos": [],
        "desacuerdos": [],
        "motivo": None,
    }

    try:
        for player_id, valor in (por_foto or {}).items():

            try:
                jugados = safe_int(valor[1])
            except (TypeError, IndexError, KeyError):
                continue

            if jugados > PARTIDOS_POR_RONDA:
                salida["dos_partidos"].append(str(player_id))

        for player_id, puntos in (por_entradas or {}).items():

            valor = (por_foto or {}).get(str(player_id))

            if valor is None:
                continue

            try:
                de_la_foto = safe_int(valor[0])
            except (TypeError, IndexError, KeyError):
                continue

            if de_la_foto != safe_int(puntos):
                salida["desacuerdos"].append({
                    "id": str(player_id),
                    "foto": de_la_foto,
                    "resta": safe_int(puntos),
                })

        salida["dos_partidos"].sort()
        salida["desacuerdos"].sort(key=lambda d: d["id"])

        motivos = []

        if salida["dos_partidos"]:
            motivos.append(
                f"{len(salida['dos_partidos'])} jugador(es) con "
                f"{PARTIDOS_POR_RONDA + 1} o mas partidos en la "
                f"ventana: lleva el partido tardio de la ronda "
                f"anterior (la foto se hace antes de que Biwenger "
                f"puntue el lunes)."
            )

        if salida["desacuerdos"]:
            ejemplo = salida["desacuerdos"][0]
            motivos.append(
                f"La foto no dice lo mismo que la resta de entradas "
                f"en {len(salida['desacuerdos'])} jugador(es) (#"
                f"{ejemplo['id']}: foto {ejemplo['foto']}, resta "
                f"{ejemplo['resta']})."
            )

        salida["motivo"] = " ".join(motivos) or None
        salida["limpia"] = not motivos

        return salida

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"{type(error).__name__}: {error}"
        return salida


def puntos_de_cierre(fotos, round_id, pitidos, nombres=None, resta=None) -> dict:
    """Los puntos de la ronda por la foto de cierre de LaLiga.

    Forma fija, nunca lanza: `{"limpia", "puntos", "jugados",
    "motivo", "fugas"}`.

    Solo vale para una ronda NORMAL («Jornada N») cuya ventana
    (cierre de la N-1, cierre de la N] no tenga dentro el pitido
    de NINGUNA otra ronda —la J10 lleva dentro la J6 aplazada del
    21-22/10— y que pase la prueba de fugas contra `resta` (la
    resta de entradas, `{id: puntos}`): ver `LA FOTO DE CIERRE SE
    HACE ANTES DE PUNTUAR EL LUNES`.
    """

    salida = {
        "limpia": False,
        "puntos": {},
        "jugados": {},
        "motivo": None,
        "fugas": None,
    }

    try:

        round_id = safe_int(round_id)
        fila = (nombres or {}).get(round_id) or {}
        pitido = (pitidos or {}).get(round_id)

        if pitido is None or not fotos:
            salida["motivo"] = "Sin foto de cierre o sin pitido."
            return salida

        if es_aplazada(fila.get("nombre"), fila.get("part")):
            salida["motivo"] = (
                "Ronda aplazada: la foto de cierre va por jornada "
                "de LaLiga y no la separa."
            )
            return salida

        ventana = _ventana_de_cierre(fotos, pitido)

        if ventana is None:
            salida["motivo"] = "Ninguna pareja de fotos de cierre la cubre."
            return salida

        previa, actual = ventana

        desde = _momento(previa.get("cerrada_en"))
        hasta = _momento(actual.get("cerrada_en"))

        otras = sorted(
            otro
            for otro, momento in (pitidos or {}).items()
            if otro != round_id and desde < momento <= hasta
        )

        if otras:
            salida["motivo"] = (
                f"La ventana de cierre de la jornada "
                f"{safe_int(actual.get('jornada'))} lleva dentro el "
                f"pitido de otra(s) ronda(s) ({otras}): la resta "
                f"mezclaria sus puntos."
            )
            return salida

        por_foto = _resta_de_fotos(previa, actual)

        fugas = fugas_de_la_ventana(por_foto, resta)
        salida["fugas"] = fugas

        if not fugas["limpia"]:
            salida["motivo"] = (
                f"La ventana de cierre de la jornada "
                f"{safe_int(actual.get('jornada'))} no esta limpia. "
                f"{fugas['motivo']}"
            )
            return salida

        salida["puntos"] = {
            player_id: valor[0]
            for player_id, valor in por_foto.items()
        }
        salida["jugados"] = {
            player_id: valor[1]
            for player_id, valor in por_foto.items()
        }

        salida["limpia"] = True

        return salida

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"{type(error).__name__}: {error}"
        return salida


def _instantes_de_la_foto_de_cierre(foto) -> tuple:
    """`(primero, ultimo)` de sus dos sellos: `cerrada_en` (el
    cierre nominal) y `at` (cuando se escribio la linea)."""

    momentos = [
        m
        for m in (
            _momento((foto or {}).get("cerrada_en")),
            _momento((foto or {}).get("at")),
        )
        if m is not None
    ]

    if not momentos:
        return None, None

    return min(momentos), max(momentos)


def _sin_partido(fotos, pitido, player_id, termina=None, limpia=False) -> bool:
    """¿Consta que no jugo ningun partido en la ronda? Entonces sus
    puntos son cero, este o no en la plantilla. Nunca lanza.

    DOS PRUEBAS, Y NINGUNA SE FIA DEL LUNES (28/10/2026)

        1. Con el cierre del tablon (`termina`): (0, 0) desde la
           ultima foto ANTERIOR al pitido hasta la primera
           POSTERIOR al cierre. Ese tramo cubre la ronda entera,
           lunes incluido, y un tramo mas ancho no puede esconder
           un partido. Es la unica prueba con el tablon delante.
        2. Sin cierre: (0, 0) en la ventana que contiene el
           pitido, solo si esa ventana paso la prueba de fugas
           (`limpia`).

    Un (0, 0) en una ventana con fugas no prueba nada: el que
    jugo el lunes que la foto aun no tenia sale (0, 0).
    """

    try:
        clave = str(safe_int(player_id))
        pitido = _momento(pitido)
        termina = _momento(termina)

        if pitido is None:
            return False

        if termina is not None:

            antes = despues = None

            for foto in (fotos or []):

                if not isinstance(foto, dict):
                    continue

                primero, ultimo = _instantes_de_la_foto_de_cierre(foto)

                if primero is None:
                    continue

                if ultimo < pitido and (
                    antes is None or ultimo > antes[0]
                ):
                    antes = (ultimo, foto)

                if primero > termina and (
                    despues is None or primero < despues[0]
                ):
                    despues = (primero, foto)

            if antes is None or despues is None:
                return False

            valor = _resta_de_fotos(antes[1], despues[1]).get(clave)

            return valor is not None and valor == (0, 0)

        if not limpia:
            return False

        ventana = _ventana_de_cierre(fotos, pitido)

        if ventana is None:
            return False

        valor = _resta_de_fotos(*ventana).get(clave)

        return valor is not None and valor == (0, 0)

    except Exception:                               # noqa: BLE001
        return False


def ledger_vacio() -> dict:
    return {
        "version": 1,
        "updated_at": None,
        "jornadas": {},
    }


# ============================================================
# PERSISTENCIA
# ============================================================


def cargar_ledger() -> dict:

    if not LEDGER_FILE.exists():
        return ledger_vacio()

    try:

        with open(
            LEDGER_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Root invalido.")

        if not isinstance(data.get("jornadas"), dict):
            data["jornadas"] = {}

        return data

    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
    ):
        return ledger_vacio()


def guardar_ledger(ledger: dict) -> Path:

    ensure_state_directory()

    temporal = LEDGER_FILE.with_suffix(".json.tmp")

    with open(
        temporal,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            ledger,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporal.replace(LEDGER_FILE)

    return LEDGER_FILE


# ============================================================
# LECTURA DEL SNAPSHOT
# ============================================================


def _liga(snapshot: dict) -> dict:
    return (
        (snapshot.get("rounds") or {})
        .get("data", {})
        .get("league", {})
        or {}
    )


def jornada_en_curso(snapshot: dict) -> int:
    return safe_int(
        (snapshot.get("rounds") or {})
        .get("data", {})
        .get("round", {})
        .get("id")
    )


# `_mi_fila` VIVIA AQUI Y SE BORRO (14/09/2026)
#
#     Buscaba la fila de Pepe en `standings` para sacarle el
#     `lineup`. Era el unico motivo por el que este modulo miraba
#     ahi, y ese once llevaba cinco dias parado.
#
#     Ahora el once sale de `once_del_dueno` y esta funcion no la
#     usaba nadie mas. Dejarla habria sido dejar la puerta
#     abierta para que la segunda fuente volviera sin discusion:
#     una fuente, un sitio, y ni una funcion de mas que apunte a
#     la otra.
#
#     La clasificacion SI se sigue leyendo de `standings` —es
#     donde vive— pero eso son los puntos de los managers, no el
#     once, y ahi no hay dos versiones de nada.


def sello_de_la_foto(snapshot) -> str | None:
    """De cuando son los datos de esta foto. `None` si no consta.

    Es el `timestamp` que el propio snapshot trae escrito. No se
    deduce del nombre del fichero ni del reloj: si la foto no
    dice cuando se tomo, no se sabe, y eso se dice.
    """

    momento = _momento((snapshot or {}).get("timestamp"))

    return momento.isoformat() if momento is not None else None


# Las entradas que escribe la regla del 28/10 llevan esta marca.
# Las de antes no: el lector las repara por la hora.
ESCRITURA_POR_LA_RONDA_EN_JUEGO = 2

CLAVE_RONDA_EN_JUEGO = "RONDA_EN_JUEGO"
CLAVE_RONDA_DE_BIWENGER = "RONDA_DE_BIWENGER"


def _instante_de_la_foto(snapshot):
    """El instante REAL de la foto, con zona. `None` si no consta.

    EL SELLO SIN ZONA ES HORA LOCAL (28/10/2026)

        El recolector escribe `datetime.now().isoformat()`, sin
        zona, y el workflow corre con `TZ: Europe/Madrid`: el
        sello es hora de Madrid. `sello_de_la_foto` le pone
        `+00:00` (la suposicion de la casa) y asi se guarda en
        `datos_de`: medido, la entrada 4908 dice `20:10+00:00` y
        el commit que la escribio es de las 20:11 +0100.

        Para lo que se guarda no se cambia nada. Pero para decidir
        si una ronda YA PITO, una o dos horas importan: con la
        suposicion UTC, a las 20:10 de Madrid la J11 (21:00) ya
        «habria empezado» y se bloquearia su once 50 minutos
        antes del pitido. Aqui el sello sin zona se lee como lo
        que es: hora de pared de la maquina que lo tomo, Madrid
        (`_hora_del_recolector`, la misma que usa el lector).
    """

    marca = (snapshot or {}).get("timestamp")

    if marca is None or isinstance(marca, (int, float, datetime)):
        return _momento(marca)

    try:
        cuando = datetime.fromisoformat(str(marca).replace("Z", "+00:00"))

    except (TypeError, ValueError):
        return None

    if cuando.tzinfo is not None:
        return cuando

    return _hora_del_recolector(cuando)


# La zona del recolector: el workflow corre con `TZ: Europe/Madrid`.
ZONA_DEL_RECOLECTOR = "Europe/Madrid"


def _hora_del_recolector(cuando):
    """Una hora de pared SIN zona del recolector, con su zona.

    La misma regla para quien escribe (`_instante_de_la_foto`) y
    para quien lee (`_hora_del_sello`), y escrita, no la del reloj
    de la maquina: una guardia que corra en UTC lee lo mismo que
    el ciclo.
    """

    try:
        if ZoneInfo is not None:
            return cuando.replace(tzinfo=ZoneInfo(ZONA_DEL_RECOLECTOR))

    except Exception:                               # noqa: BLE001
        pass

    try:
        return cuando.astimezone()

    except (OverflowError, OSError, ValueError):
        return cuando.replace(tzinfo=timezone.utc)


def _hora_del_sello(valor):
    """`datos_de` / `visto_en` de una entrada, con su zona de verdad.

    Nunca lanza.

    EL LECTOR LEIA OTRA HORA QUE EL ESCRITOR (28/10/2026)

        `sello_de_la_foto` guarda el sello sin zona del recolector
        —hora de Madrid— con la etiqueta `+00:00`. El escritor ya
        lo leia como hora local (`_instante_de_la_foto`); el
        lector lo tomaba por UTC, una o dos horas tarde. Medido
        sobre el libro: la ultima escritura de la 4908 antes de la
        J11 cae a las 20:07 de Madrid (19:07 UTC), se guarda como
        `20:07+00:00`, y el lector la ponia DESPUES del pitido
        (20:00 UTC) y le asignaba a la J11 un once visto 53
        minutos antes.

        Aqui un `+00:00` (o sin zona) es esa etiqueta y se lee
        como hora de pared de Madrid; una zona de verdad distinta
        se respeta.
    """

    if not isinstance(valor, str):
        return _momento(valor)

    try:
        cuando = datetime.fromisoformat(valor.replace("Z", "+00:00"))

    except (TypeError, ValueError):
        return None

    if cuando.tzinfo is not None and cuando.utcoffset() != timedelta(0):
        return cuando

    return _hora_del_recolector(cuando.replace(tzinfo=None))


def la_ronda_de_la_foto(snapshot, cierres=None) -> tuple:
    """`(round_id, clave)`: bajo que ronda se anota esta foto.

    Nunca lanza.

    `rounds.data.round.id` va retrasado —Biwenger lo pasa en el
    pitido de la siguiente y la vuelta lo lee de la cache del
    reset—, asi que la mañana despues de un pitido todavia dice
    la ronda ANTERIOR mientras los totales y el once ya son de la
    nueva. Con el tablon delante manda la ronda EN JUEGO: la del
    ultimo `roundStarted` anterior a la foto.

    Sin tablon, o si el tablon no conoce la del id, manda el id:
    exactamente lo de antes.
    """

    de_biwenger = jornada_en_curso(snapshot or {})

    try:
        cierres = cierres or {}

        en_juego = ronda_en_juego(
            cierres,
            _instante_de_la_foto(snapshot),
        )

        if not en_juego:
            return de_biwenger, CLAVE_RONDA_DE_BIWENGER

        if not de_biwenger:
            return en_juego, CLAVE_RONDA_EN_JUEGO

        suya = (cierres.get(de_biwenger) or {}).get("empieza")

        if suya is None:
            return de_biwenger, CLAVE_RONDA_DE_BIWENGER

        if cierres[en_juego]["empieza"] > suya:
            return en_juego, CLAVE_RONDA_EN_JUEGO

        return de_biwenger, CLAVE_RONDA_DE_BIWENGER

    except Exception:                               # noqa: BLE001
        return de_biwenger, CLAVE_RONDA_DE_BIWENGER


def observar(
    snapshot: dict,
    current_user_id=None,
    once_alternativo: dict | None = None,
    escrito_en=None,
    eventos=None,
) -> dict:
    """Anota la jornada en curso tal y como se ve ahora mismo.

    Se llama en cada ciclo. Sobreescribe la observacion de esa
    jornada, de modo que la que queda es siempre la ultima antes
    de que Biwenger salte a la siguiente: la definitiva.

    CON EL TABLON (28/10/2026), `eventos`:

        · la foto se anota bajo la ronda EN JUEGO, no bajo el id
          retrasado (`la_ronda_de_la_foto`). Asi la ultima
          escritura de una ronda es la de antes del pitido de la
          siguiente: totales de la ronda entera y nada de la otra.

        · en una entrada nueva, el once se escribe UNA vez: la
          primera vista tras el pitido de su ronda, que con
          `lineupRoundChanges: 0` es el bloqueado. Lo que se vea
          despues es el editable de la siguiente y no se escribe
          encima (`regla: PRIMERA_VISTA`).

        Las entradas de antes no se tocan de regla: siguen
        sobreescribiendo el once, y el lector las repara por la
        hora (`el_once_de_cada_ronda`).
    """

    cierres = cierres_del_tablon(eventos) if eventos else {}

    round_id, clave_de_ronda = la_ronda_de_la_foto(snapshot, cierres)

    if not round_id:
        return {
            "anotada": False,
            "motivo": "El snapshot no trae jornada.",
        }

    plantilla = []
    totales = {}

    for jugador in (snapshot.get("my_team") or []):

        if not isinstance(jugador, dict):
            continue

        player_id = safe_int(jugador.get("id"))

        if not player_id:
            continue

        plantilla.append({
            "id": player_id,
            "name": str(jugador.get("name") or player_id),
            "position": safe_int(jugador.get("position")),
        })

        totales[str(player_id)] = safe_int(
            jugador.get("points")
        )

    clasificacion = []

    for fila in (_liga(snapshot).get("standings") or []):

        if not isinstance(fila, dict):
            continue

        clasificacion.append({
            "user_id": safe_int(fila.get("id")),
            "name": str(fila.get("name") or ""),
            "points": safe_int(fila.get("points")),
        })

    # ============================================================
    # LA FUENTE UNICA DEL ONCE (14/09/2026)
    # ============================================================
    #
    # HASTA HOY ESTA FUNCION LEIA LA OTRA. Biwenger publica
    # nuestro once en dos sitios y no dicen lo mismo. Medido en la
    # foto del 13/09/2026 a las 17:17:
    #
    #     standings[mi].lineup      4-4-2   guardado el 08/09 05:20
    #     user_lineup.data.lineup   3-5-2   guardado el 13/09 06:26
    #
    #     Coinciden 10 de los 11. Cambia el dibujo y cambia un
    #     nombre: `standings` traia a Zubeldia (8376, defensa)
    #     donde `user_lineup` trae a Ruben Garcia (1602, medio),
    #     coherente con el paso de 4-4-2 a 3-5-2.
    #
    # `observar()` leia `standings` y el libro de las jornadas
    # leia `user_lineup`: dos ideas distintas de "el once de esa
    # jornada" en el mismo motor, y ademas con escrituras
    # asimetricas —esta sobreescribe la jornada en curso en cada
    # vuelta, el libro escribe una linea y no la toca nunca—.
    #
    # AHORA LAS DOS LEEN DE `once_del_dueno`, que es la vigente:
    # la que Biwenger usa para pagar. `standings` era una copia
    # parada el 08/09.
    #
    # Y LAS DOS FORMAS SON DISTINTAS: `standings` traia ids
    # sueltos y `user_lineup` la ficha entera. Por eso los ids
    # salen por `ids_del_once`, que entiende las dos; hacerlo a
    # mano con `safe_int(dict)` daria 0 en los once y el once
    # saldria VACIO, sin ruido.
    from src.analysis.el_once_que_jugo import (
        ids_del_once,
        once_del_dueno,
    )

    alineacion = once_del_dueno(snapshot)

    # LOS NOMBRES, DEL CATALOGO Y NO DE LA PLANTILLA (21/08/2026)
    #
    # La pantalla enseñaba "jugaron en su lugar: 38194, 25322,
    # 9065, 1599". Son ids, no jugadores.
    #
    # El nombre se buscaba en la plantilla del dia, y un jugador
    # que alineo el sabado y se vendio el domingo ya no esta ahi.
    # El catalogo si lo tiene: son los 500 y pico de La Liga.
    catalogo = (
        (snapshot.get("catalog") or {})
        .get("data", {})
        .get("players")
        or {}
    )

    nombres = {
        str(j["id"]): j["name"]
        for j in plantilla
    }

    # LOS IDS, POR `ids_del_once`: `user_lineup` trae la ficha
    # entera y `safe_int(dict)` daria 0 en los once.
    once_de_hoy = ids_del_once(alineacion)

    for player_id in once_de_hoy:

        clave = str(safe_int(player_id))

        if clave in nombres:
            continue

        ficha = (
            catalogo.get(clave)
            if isinstance(catalogo, dict)
            else None
        ) or {}

        if ficha.get("name"):
            nombres[clave] = str(ficha["name"])

    ledger = cargar_ledger()

    # LA HORA DE LA ESCRITURA ENTRA POR LA PUERTA (doctrina 50).
    #
    #     Es la unica de las dos que es legitimamente "ahora": lo
    #     que se escribe es que NOSOTROS escribimos, y eso pasa
    #     ahora. Aun asi se deja entrar por parametro para que
    #     las guardias no dependan del reloj del sistema.
    escritura = (
        _momento(escrito_en) or datetime.now()
    ).isoformat()

    # ============================================================
    # EL ONCE DE ESTA RONDA, UNA VEZ  (28/10/2026)
    # ============================================================
    #
    #     Ver `EL ONCE DESPLAZADO UNA JORNADA`. Tres casos:
    #
    #         · Entrada de la regla nueva con el once ya bloqueado:
    #           no se toca. Lo que se ve ahora es el editable de
    #           la siguiente.
    #         · Entrada de la regla nueva, y el tablon dice que su
    #           ronda ya pito: se bloquea con lo que se ve ahora.
    #         · Cualquier otra (las de antes, o sin tablon): se
    #           sobreescribe como siempre, y el lector la repara
    #           por la hora.
    previa_entrada = (ledger.get("jornadas") or {}).get(str(round_id))
    nueva = not isinstance(previa_entrada, dict)
    previa_entrada = previa_entrada if not nueva else {}

    regla_nueva = (
        nueva
        or safe_int(previa_entrada.get("escritura"))
        >= ESCRITURA_POR_LA_RONDA_EN_JUEGO
    )

    once_previo = previa_entrada.get("mi_once") or {}

    guardado = _momento(alineacion.get("date"))

    once_de_ahora = {
        "formation": alineacion.get("type"),
        "players": list(once_de_hoy),

        # Cuando lo grabo el dueño. Si es DESPUES del pitido de
        # la ronda, no es el bloqueado: el lector lo descarta.
        "guardado": guardado.isoformat() if guardado else None,
    }

    pitido = (cierres.get(round_id) or {}).get("empieza")
    ahora_de_la_foto = _instante_de_la_foto(snapshot)

    bloqueado = (
        regla_nueva
        and once_previo.get("regla") == REGLA_PRIMERA_VISTA
        and bool(_ids(once_previo))
    )

    if bloqueado:
        mi_once = once_previo

    elif (
        regla_nueva
        and pitido is not None
        and ahora_de_la_foto is not None
        and ahora_de_la_foto >= pitido
        and once_de_ahora["players"]
    ):
        mi_once = {
            **once_de_ahora,
            "regla": REGLA_PRIMERA_VISTA,
            "visto_en": sello_de_la_foto(snapshot),
        }

    else:
        mi_once = once_de_ahora

    congelado = mi_once.get("regla") == REGLA_PRIMERA_VISTA

    ledger["jornadas"][str(round_id)] = {
        "round_id": round_id,

        # BAJO QUE RONDA Y POR QUE (28/10/2026). La del tablon si
        # la sabia; si no, la del id. Y el id, al lado, para que
        # se vea cuando iba retrasado.
        "clave": clave_de_ronda,
        "ronda_de_biwenger": jornada_en_curso(snapshot) or None,
        **(
            {"escritura": ESCRITURA_POR_LA_RONDA_EN_JUEGO}
            if regla_nueva
            else {}
        ),
        # DOS FECHAS, PORQUE SON DOS HECHOS (14/09/2026)
        #
        #     `visto` era `datetime.now()` al escribir y se leia
        #     como si fuera de cuando son los datos. La entrada
        #     de la jornada 1 decia `visto: 2026-09-06` y llevaba
        #     los totales del 17/08: veinte dias de diferencia
        #     entre lo que el campo parecia y lo que era.
        #
        #     Doctrina 39: un campo que dice una cosa y se llama
        #     como otra. No se arregla renombrando —son DOS
        #     hechos distintos y los dos hacen falta—.
        #
        #         datos_de    el sello de la foto de la que salen
        #         escrito_en  cuando lo escribimos nosotros
        #
        #     `visto` SE SIGUE ESCRIBIENDO con el valor que
        #     siempre tuvo. Las entradas viejas no se traducen ni
        #     se reinterpretan: el que lea una entrada sin
        #     `datos_de` sabe que es de antes del cambio, y eso
        #     es mas honrado que adivinarle una fecha.
        "visto": escritura,
        "datos_de": sello_de_la_foto(snapshot),
        "escrito_en": escritura,
        "clasificacion": clasificacion,
        "mi_user_id": safe_int(current_user_id),
        "mi_once": mi_once,

        # EL QUE HAY PUESTO AHORA, aparte (28/10/2026). Con el
        # once de la ronda bloqueado, quien quiera el editable —el
        # que se bloqueara en el proximo pitido, p. ej.
        # `scripts/la_jornada_en_vivo.py`— lo tiene aqui, y no lo
        # confunde con el que jugo.
        "once_editable": {
            **once_de_ahora,
            "visto_en": sello_de_la_foto(snapshot),
        },
        "plantilla": plantilla,
        "totales": totales,

        # LA RED DE LOS FACTORES POR POSICION (18/09/2026)
        #
        #     Los factores se aplicaron sin fase observador. La
        #     contrapartida: cada jornada se anota TAMBIEN el
        #     once que habria elegido la vara vieja, para poder
        #     comparar con puntos de verdad en vez de discutirlo.
        #
        #     Se anota aunque venga vacio -asi la clave existe
        #     siempre- y las jornadas anteriores al cambio salen
        #     sin comparacion en vez de con un cero que mentiria.
        "once_alternativo": (
            {
                "formation": (once_alternativo or {}).get(
                    "formation"
                ),
                "players": [
                    safe_int(p)
                    for p in (
                        (once_alternativo or {}).get("players")
                        or []
                    )
                ],
                "vara": (once_alternativo or {}).get(
                    "vara", "plana"
                ),
            }
            if once_alternativo
            else None
        ),

        # Nombre de todo el que sale en la foto, incluidos los
        # que ya no estan en la plantilla. Los de antes se quedan:
        # un vendido sigue necesitando su nombre en la fila.
        "nombres": {
            **(previa_entrada.get("nombres") or {}),
            **nombres,
        },
    }

    # CON EL ONCE BLOQUEADO, SUS COMPAÑEROS TAMBIEN. Los onces de
    # las varas se anotaron con el, a la misma hora: lo que se
    # calcule despues es para la siguiente.
    if congelado:

        for campo in ("once_alternativo", "onces_por_vara"):

            if previa_entrada.get(campo):
                ledger["jornadas"][str(round_id)][campo] = (
                    previa_entrada[campo]
                )

    ledger["updated_at"] = escritura

    guardar_ledger(ledger)

    return {
        "anotada": True,
        "round_id": round_id,
        "clave": clave_de_ronda,
        "once_bloqueado": congelado,
        "jugadores": len(plantilla),
        "once": len(
            ledger["jornadas"][str(round_id)]["mi_once"]["players"]
        ),
        "jornadas_en_ledger": len(ledger["jornadas"]),
    }


def anotar_once_alternativo(
    round_id,
    once: dict | None,
) -> dict:
    """
    Añade a la jornada ya observada el once de la vara vieja.

    POR QUE EN DOS PASOS (18/09/2026)

        La jornada se anota nada mas cargar el snapshot, que es
        donde se puede. El once de la vara vieja necesita la
        plantilla ya enriquecida -jerarquia y probabilidad de
        titular-, que llega mas tarde en el ciclo.

        Reordenar el ciclo por esto seria arriesgar la anotacion
        de los puntos, que es el dato que no se recupera. Asi que
        se completa despues.

    Nunca lanza.
    """

    try:
        clave = str(safe_int(round_id))

        if not clave or clave == "0" or not once:
            return {"anotado": False, "motivo": "Sin once."}

        ledger = cargar_ledger()

        jornada = (ledger.get("jornadas") or {}).get(clave)

        if not jornada:
            return {
                "anotado": False,
                "motivo": f"La jornada {clave} no esta observada.",
            }

        # EL ONCE BLOQUEADO NO SE COMPARA CON UNO DE DESPUES
        # (28/10/2026). Si la entrada ya tiene su once bloqueado y
        # su vara anotada, lo que se calcule ahora es para la
        # siguiente ronda.
        if (
            (jornada.get("mi_once") or {}).get("regla")
            == REGLA_PRIMERA_VISTA
            and _ids(jornada.get("once_alternativo"))
        ):
            return {
                "anotado": False,
                "motivo": (
                    f"La jornada {clave} ya tiene su once bloqueado "
                    f"y el de la vara anotado con el."
                ),
            }

        jornada["once_alternativo"] = {
            "formation": once.get("formation"),
            "players": [
                safe_int(j.get("id") if isinstance(j, dict) else j)
                for j in (once.get("players") or [])
            ],
            "vara": once.get("vara", "plana"),
        }

        # TRES ONCES, PARA PODER SEPARAR LOS DOS CAMBIOS
        # (22/09/2026)
        #
        #     El 18/09 se encendieron los factores de posicion y
        #     el 22/09 la calidad medida. Con dos onces se sabria
        #     si el conjunto suma; con tres se sabe cual de los
        #     dos lo hace:
        #
        #         factores = FACTORES - BASE
        #         calidad  = ACTUAL   - FACTORES
        otros = once.get("por_vara") or {}

        if otros:
            jornada["onces_por_vara"] = {
                nombre: {
                    "formation": (datos or {}).get("formation"),
                    "players": [
                        safe_int(
                            j.get("id")
                            if isinstance(j, dict)
                            else j
                        )
                        for j in ((datos or {}).get("players") or [])
                    ],
                }
                for nombre, datos in otros.items()
            }

        guardar_ledger(ledger)

        return {
            "anotado": True,
            "round_id": clave,
            "jugadores": len(
                jornada["once_alternativo"]["players"]
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "anotado": False,
            "motivo": (
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# EL CONTRAFACTUAL
# ============================================================


def mejor_once(
    puntos_por_jugador: dict,
    posicion_por_jugador: dict,
    alineados=None,
    formacion_usada=None,
) -> dict:
    """El mejor once legal, ya sabiendo lo que puntuo cada uno.

    Sin restricciones de lesion ni de titularidad: es el techo
    con esa plantilla exacta. La distancia entre este numero y lo
    que Pepe alineo es exactamente lo que se puede ganar sin
    fichar a nadie.

    LOS EMPATES SE RESUELVEN A FAVOR DE QUIEN JUGO

        En una jornada normal hay ocho o diez jugadores con cero
        puntos. Si el desempate es arbitrario, el techo mete a
        uno cualquiera y la pantalla acaba diciendo "debio jugar
        Bayindir, 0 puntos" en vez de callarse.

        Eso no es un matiz estetico: hace que la lista de fallos
        sea ruido y que nadie la mire. Con empate, gana el que
        Pepe alineo, y solo queda en la lista lo que de verdad
        costo puntos.
    """

    jugaron = {
        str(p)
        for p in (alineados or [])
    }

    por_posicion = {1: [], 2: [], 3: [], 4: []}

    for player_id, puntos in puntos_por_jugador.items():

        posicion = safe_int(
            posicion_por_jugador.get(player_id)
        )

        if posicion in por_posicion:
            por_posicion[posicion].append((
                safe_int(puntos),
                1 if str(player_id) in jugaron else 0,
                player_id,
            ))

    for posicion in por_posicion:
        por_posicion[posicion].sort(reverse=True)

    mejor = {
        "formation": None,
        "points": None,
        "players": [],
    }

    for nombre, cupos in FORMACIONES.items():

        elegidos = []
        completa = True

        for posicion, cuantos in cupos.items():

            disponibles = por_posicion[posicion]

            if len(disponibles) < cuantos:
                completa = False
                break

            elegidos.extend(disponibles[:cuantos])

        if not completa:
            continue

        total = sum(puntos for puntos, _, _ in elegidos)

        # Mismo criterio que con los jugadores: si dos dibujos dan
        # los mismos puntos, gana el que Pepe puso. Asi la
        # pantalla no le corrige una formacion que era igual de
        # buena.
        clave = (
            total,
            1 if nombre == formacion_usada else 0,
        )

        clave_mejor = (
            mejor["points"],
            1 if mejor["formation"] == formacion_usada else 0,
        )

        if mejor["points"] is None or clave > clave_mejor:
            mejor = {
                "formation": nombre,
                "points": total,
                "players": [
                    player_id for _, _, player_id in elegidos
                ],
            }

    return mejor


def foto_a_medias(jornada) -> str | None:
    """¿Esta foto se tomo a mitad del abono? Devuelve el motivo.

    `None` si la foto es buena. Nunca lanza.

    UN CERO DE TODA LA LIGA NO ES UN CERO (14/09/2026)

        Que los SIETE managers marquen 0 a la vez, teniendo los
        jugadores puntos, no es un resultado posible: es que el
        abono todavia no habia pasado cuando se tomo la foto.

        Biwenger acredita los puntos de la jornada a los
        managers DESPUES de puntuar a los jugadores. Entre una
        cosa y la otra hay una ventana, y en esta liga duro
        TRES DIAS en la jornada 1: 39 fotos guardadas entre el
        15/08 y el 17/08 tienen la clasificacion a cero mientras
        los jugadores iban de 9 a 29 puntos.

        Una foto asi no puede servir de referencia para restar
        nada. Restarle a la siguiente da el acumulado ENTERO de
        la temporada, que es de donde salia el `186` publicado
        como si fueran los puntos de una jornada.

    LA CONTRADICCION ESTA DENTRO DE LA PROPIA FOTO

        Suma de la clasificacion igual a cero Y totales de
        jugador mayores que cero. No hace falta nada de fuera
        para verlo, ni otra foto con la que comparar.

    Y UN CERO DE VERDAD NO ES ESTO

        Antes del primer partido TODO esta a cero -la liga y los
        jugadores-, y eso no es una foto a medias: es una foto de
        antes de que pasara nada. Por eso se exige que los
        jugadores SI tengan puntos.

        En esta liga son 46 fotos, del 12/08 al 14/08, y no se
        marcan.

    ES LA HERMANA DEL INVARIANTE DE LAS NEGATIVAS. Aquel caza lo
    imposible; este caza lo que parece un dato y es un hueco.
    """

    try:

        datos = jornada if isinstance(jornada, dict) else {}

        clasificacion = [
            f
            for f in (datos.get("clasificacion") or [])
            if isinstance(f, dict)
        ]

        # SIN MANAGERS NO SE DICE NADA. Una clasificacion vacia
        # no es una foto a medias: es una foto sin clasificacion,
        # y esa ya se cae sola por no tener con quien comparar.
        if not clasificacion:
            return None

        liga = sum(
            safe_int(f.get("points")) for f in clasificacion
        )

        if liga:
            return None

        jugadores = sum(
            safe_int(valor)
            for valor in (datos.get("totales") or {}).values()
        )

        if jugadores <= 0:
            # Todo a cero: es de antes del primer partido.
            return None

        return (
            f"Foto a medias: los {len(clasificacion)} managers "
            f"marcan 0 puntos a la vez mientras los jugadores ya "
            f"suman {jugadores}. Eso no es un resultado, es que "
            f"el abono no habia pasado cuando se tomo la foto. "
            f"No sirve de referencia para restar nada."
        )

    except Exception:                               # noqa: BLE001
        return None


# ================================================================
# DOS ENFERMEDADES CON LA MISMA ETIQUETA  (20/09/2026)
# ================================================================
#
#     Un negativo al restar totales tenia UN solo motivo escrito:
#     «las dos fotos estan al reves». Es falso para la mitad de
#     los casos, y doctrina 87: un motivo que nombra una causa
#     que no decidio es una afirmacion falsa.
#
# LO QUE SEPARA LOS DOS GRUPOS, MEDIDO
#
#     Las 9 fotos del libro (10/08 -> 20/09) permiten 72 restas
#     ordenadas. Separadas por si la previa es de verdad
#     anterior:
#
#         orden CORRECTO   36 parejas   25 sin ningun negativo
#                          las 11 con negativo: UN jugador
#                          siempre, y -1 o -2 siempre
#
#         orden INVERTIDO  36 parejas   las 36 con negativo
#                          de 2 a 11 jugadores
#                          de -4 a -88
#
#     Los dos grupos NO SE SOLAPAN por ninguno de los dos ejes:
#     ni por cuantos jugadores (1 contra 2+), ni por el tamaño
#     (-2 contra -4). El umbral no me lo invento: sale de ahi.
#
#     EL `n` HONESTO NO ES 72. Son 9 fotos y 8 parejas
#     consecutivas reales; las 72 son todas sus combinaciones y
#     no son independientes. El margen es ancho, la muestra es
#     corta, y las dos cosas van dichas.
#
# ESTO NO CAMBIA NINGUNA DECISION. Las dos siguen sin medirse.
# Lo unico que cambia es que el motivo deja de mentir.

# Cuantos jugadores hacen falta para que sea un desorden de
# fotos. Medido: con las fotos en orden nunca fue mas de UNO.
JUGADORES_DE_UN_DESORDEN = 2

# Y el tamaño. Medido: con las fotos en orden, nunca peor que -2;
# al reves, nunca mejor que -4.
CORRECCION_MAS_GRANDE = -2


def _es_correccion_retroactiva(negativos) -> bool:
    """Un negativo suelto y pequeño no es una foto al reves.

    Los dos ejes a la vez, porque los dos estan medidos y
    ninguno de los dos vale solo.
    """

    return (
        len(negativos) < JUGADORES_DE_UN_DESORDEN
        and negativos
        and negativos[0][1] >= CORRECCION_MAS_GRANDE
    )


def _sello_del_cuadre(fila: dict) -> str:
    """Lo que se imprime al lado de la jornada.

    Tres estados, no dos: cuadra, no cuadra, y NO SE PUDO MEDIR
    el cuadre. El tercero salia antes como «cuadra».
    """

    cuadre = fila.get("cuadra")

    if cuadre is None:
        return "  [CUADRE NO MEDIBLE]"

    return "" if cuadre else "  [NO CUADRA]"


def _por_que_no_cuadra(mios, puntos_once, aplazada=False) -> str | None:
    """El motivo de un «no cuadra» con el once completo. `None` si
    cuadra o no hay verdad.

    UN ROJO TAMBIEN LLEVA SU PORQUE (28/10/2026). La J9 sale 48
    con el once que jugo, entero, y Biwenger pago 49. Un punto o
    dos con todo medido es lo que deja una correccion retroactiva
    (Biwenger retoca a un jugador despues de cobrar la ronda, y el
    total que se resta ya es el corregido): se dice, con su
    tamaño, y no se maquilla.
    """

    if mios is None or mios == puntos_once:
        return None

    diferencia = safe_int(mios) - safe_int(puntos_once)

    if aplazada:
        return (
            f"No cuadra por {diferencia:+d}: ronda partida, ver la "
            f"excepcion."
        )

    if abs(diferencia) <= -CORRECCION_MAS_GRANDE:
        return (
            f"No cuadra por {diferencia:+d} con el once completo: "
            f"Biwenger pago {mios} y sus once suman {puntos_once} "
            f"en la resta de entradas. Con todo medido, {abs(diferencia)} "
            f"punto(s) es el tamaño de una correccion retroactiva "
            f"de Biwenger (retoca a un jugador despues de cobrar la "
            f"ronda): lo mas probable, no probado."
        )

    return (
        f"No cuadra por {diferencia:+d} con el once completo: o el "
        f"once no es el que puntuo, o los puntos de algun jugador "
        f"no son los de la ronda."
    )


def _puntos_de_la_jornada(
    actual: dict,
    previa: dict | None,
) -> tuple:
    """Puntos por jugador en esa jornada, por diferencia de totales.

    Devuelve `(puntos, motivo)`. Con `puntos` en `None` cuando no
    se puede medir, y entonces `motivo` dice por que. No se
    estima nunca.

    EL INVARIANTE: UNA DIFERENCIA NEGATIVA ES IMPOSIBLE
    (14/09/2026)

        `totales` es el acumulado de temporada de cada jugador.
        Un jugador NO PIERDE puntos de temporada: la diferencia
        entre dos fotos solo puede ser cero o mas.

        Si sale negativa, no es que puntuara mal. Es que las dos
        fotos estan al reves — la que se esta usando de "previa"
        se tomo DESPUES que la actual.

        Eso es lo que producia el `mejor_puntos: -55`: once
        jugadores a -5, todas las formaciones obligadas y un
        "mejor once posible" negativo, que no existe. El motor
        publicaba el numero en vez de darse cuenta de que el
        orden estaba mal.

        Ahora se comprueba y se dice. Una jornada con una
        diferencia negativa no se mide.
    """

    totales = actual.get("totales") or {}

    if previa is None:

        if safe_int(actual.get("round_id")) == PRIMERA_JORNADA:
            # No hay nada antes: el total ES la jornada.
            return dict(totales), None

        return None, (
            "Sin observacion de la jornada anterior."
        )

    anteriores = previa.get("totales") or {}

    puntos = {}

    for player_id, total in totales.items():

        if player_id not in anteriores:
            # Fichado a mitad de camino: no sabemos cuanto de su
            # total es de esta jornada. Cuenta como 0 y se avisa.
            puntos[player_id] = 0
            continue

        puntos[player_id] = (
            safe_int(total)
            - safe_int(anteriores.get(player_id))
        )

    negativos = sorted(
        (
            (player_id, valor)
            for player_id, valor in puntos.items()
            if valor < 0
        ),
        key=lambda par: par[1],
    )

    if negativos:

        peor = negativos[0]

        cabecera = (
            f"{len(negativos)} jugador(es) con puntos negativos "
            f"al restar los totales de la jornada "
            f"{safe_int(previa.get('round_id'))} a los de la "
            f"{safe_int(actual.get('round_id'))} (el mayor, "
            f"{peor[1]} en el jugador {peor[0]})."
        )

        if _es_correccion_retroactiva(negativos):

            return None, (
                f"{cabecera} Un jugador no pierde puntos de "
                f"temporada, pero UNO SOLO y de "
                f"{-peor[1]} punto(s) no es un desorden de "
                f"fotos: es una correccion retroactiva de "
                f"Biwenger. Medido sobre las 72 restas que "
                f"permiten las 9 fotos (10/08 a 20/09): con las "
                f"fotos en orden, el negativo SIEMPRE fue de un "
                f"solo jugador y de -1 o -2; con las fotos al "
                f"reves, SIEMPRE fueron 2 o mas jugadores y "
                f"nunca menos de -4. Hoy se descarta igual, y "
                f"esa regla la revisa el dueño."
            )

        return None, (
            f"{cabecera} Un jugador no pierde puntos de "
            f"temporada, y son {len(negativos)} a la vez: las "
            f"dos fotos estan al reves. No se mide esta jornada."
        )

    return puntos, None


def _puntos_del_once(puntos: dict, once) -> int | None:
    """
    Lo que sumo un once concreto esa jornada.

    Devuelve None si ese once no se anoto: una jornada anterior
    al cambio de vara no tiene con que compararse, y un cero
    mentiria.
    """

    if not once:
        return None

    return sum(
        safe_int(puntos.get(str(safe_int(p))))
        for p in once
    )


def _puntos_de_la_clasificacion(
    actual: dict,
    previa: dict | None,
) -> dict | None:
    """Lo que Biwenger pago EN ESA JORNADA a cada manager.

    EL FALLO QUE ESTO ARREGLA (17/09/2026)

        La clasificacion de Biwenger es ACUMULADA. `points` no
        son los puntos de la jornada: son los de la temporada
        hasta ahi.

        El cuadre comparaba `puntos_once` -una cifra de UNA
        jornada- contra ese acumulado. En la jornada 1 coincide,
        porque no hay nada antes, y por eso el fallo sobrevivio
        un mes. De la 2 en adelante es imposible que cuadre:
        estaba comparando 17 contra 60.

        Consecuencia: cinco jornadas cerradas, CERO fiables, y
        el proyecto llevaba un mes sin nota del once por un
        error de aritmetica, no por un fallo del motor.

        Lo mismo pasaba con la diferencia contra la liga: salia
        +13,5 tres jornadas seguidas porque era la brecha de
        TEMPORADA repetida, no la de la jornada.

    Se mide igual que los jugadores: por diferencia de totales.
    Sin observacion previa no se inventa, se devuelve None.
    """

    def totales(foto: dict | None) -> dict:
        return {
            safe_int(f.get("user_id")): safe_int(f.get("points"))
            for f in ((foto or {}).get("clasificacion") or [])
            if isinstance(f, dict) and safe_int(f.get("user_id"))
        }

    ahora = totales(actual)

    if not ahora:
        return None

    if previa is None:

        if safe_int(actual.get("round_id")) == PRIMERA_JORNADA:
            # No hay nada antes: el acumulado ES la jornada.
            return dict(ahora)

        return None

    antes = totales(previa)

    medido = {
        user_id: puntos - antes.get(user_id, 0)
        for user_id, puntos in ahora.items()
        if user_id in antes
    }

    # EL MISMO INVARIANTE QUE CON LOS JUGADORES (14/09/2026)
    #
    #     La clasificacion tambien es acumulada, asi que un
    #     manager tampoco puede perder puntos de temporada. Si la
    #     resta sale negativa, las dos fotos estan al reves y lo
    #     que hay que publicar es el motivo, no el numero.
    if any(valor < 0 for valor in medido.values()):
        return None

    return medido


def _reconstruccion_completa(actual: dict) -> tuple[bool, str | None]:
    """¿Estan en la plantilla los once que alineamos?

    EL SEGUNDO FALLO (17/09/2026)

        `totales` solo tiene a los jugadores que estaban en la
        plantilla EN EL MOMENTO DE MIRAR. Un jugador que alineo
        el sabado y se vendio el lunes ya no esta, asi que
        aporta cero a la reconstruccion del once.

        En las jornadas 1 y 2 pasaba con cuatro y con tres de
        los once. El once salia a 13 y a 17 puntos cuando
        Biwenger pago 29 y 31, y la pantalla publicaba "61,9 %
        del optimo" como si fuera una nota del motor.

        No era el motor: era que faltaba media alineacion.

    Esto NO se puede arreglar hacia atras -los puntos de un
    jugador vendido no vuelven-, pero si se puede DECIR, para
    que un numero cojo no se lea como una nota.
    """

    en_plantilla = {
        str(safe_int(j.get("id")))
        for j in (actual.get("plantilla") or [])
    }

    alineados = [
        str(safe_int(p))
        for p in ((actual.get("mi_once") or {}).get("players") or [])
    ]

    if not alineados:
        return False, (
            "No se anoto que once jugo esa jornada."
        )

    faltan = [p for p in alineados if p not in en_plantilla]

    if not faltan:
        return True, None

    nombres = actual.get("nombres") or {}

    quienes = ", ".join(
        str(nombres.get(p) or f"#{p}")
        for p in faltan
    )

    return False, (
        f"{len(faltan)} de los {len(alineados)} que alinearon ya "
        f"no estaban en la plantilla al mirar ({quienes}): sus "
        f"puntos de esa jornada no se pueden recuperar, asi que "
        f"el once reconstruido sale corto."
    )


def _fechas_de(jornada) -> dict:
    """Las dos fechas de una entrada, para la pantalla.

    LAS ENTRADAS VIEJAS NO SE TRADUCEN (14/09/2026). Antes del
    cambio solo habia `visto`, que era la hora de ESCRITURA
    disfrazada de hora del dato. Traducirla a `datos_de` seria
    inventarle a cada entrada una fecha que nadie sabe.

    Asi que si falta `datos_de`, se dice: `antes_del_cambio`. El
    que lea la pantalla sabe que de esa entrada no consta de
    cuando son los datos, en vez de creerse una fecha falsa.
    """

    datos = jornada if isinstance(jornada, dict) else {}

    de_la_foto = datos.get("datos_de")

    return {
        "datos_de": de_la_foto,
        "escrito_en": (
            datos.get("escrito_en") or datos.get("visto")
        ),
        "antes_del_cambio": not de_la_foto,
    }


def marcador(
    calendario: dict | None = None,
    eventos=None,
    onces_congelados=None,
    fotos_de_cierre=None,
) -> dict:
    """Lee el ledger y contesta las tres preguntas.

    LO QUE CUADRA CON BIWENGER (28/10/2026)

        `eventos` (el tablon), `onces_congelados` (el libro de
        onces) y `fotos_de_cierre` (los totales de cierre de
        LaLiga) entran por la puerta y son opcionales. Con ellos:

            · el once de cada ronda es el que JUGO, no el de la
              siguiente (`el_once_de_cada_ronda`);
            · la verdad es la de `roundFinished`, ronda a ronda;
            · una ronda cerrada en el tablon se mide aunque sea
              la ultima del libro;
            · los puntos por jugador salen de la resta de
              entradas; el cierre de LaLiga solo rellena a los
              vendidos y fichados, y solo con su ventana sin
              fugas (la foto se hace antes de puntuar el lunes).

        Sin ellos se comporta como antes, salvo el once: ese se
        repara siempre, porque el que se guardaba era el de otra
        ronda.

    EL ORDEN SALE DEL CALENDARIO, NO DEL ID (14/09/2026)

        `calendario` es `{round_id: {"primer_partido", ...}}`, tal
        y como lo construye `calendario_de_jornadas`. Con el se
        hacen dos cosas que el `round_id` no permitia:

            1. ORDENAR por la hora del primer partido, que es el
               orden en que Biwenger acredito los puntos.

            2. VER LOS HUECOS: si entre dos jornadas observadas
               el calendario tiene otra que no esta en el libro,
               la resta cubre mas de una jornada y no se mide.

        Sin calendario no se ordena a ojo: se dice que no se
        puede medir. Medir menos es mejor que medir mal, y este
        numero es el que decide si "mejorar el once" gana la
        discusion.
    """

    ledger = cargar_ledger()

    entradas = [
        entrada
        for entrada in (ledger.get("jornadas") or {}).values()
        if isinstance(entrada, dict)
    ]

    colocadas = orden_en_el_tiempo(entradas, calendario)

    jornadas = [item["jornada"] for item in colocadas["ordenadas"]]

    # LO QUE CUADRA CON BIWENGER (28/10/2026). Ver la cabecera de
    # `EL ONCE DESPLAZADO UNA JORNADA`.
    cierres = cierres_del_tablon(eventos)
    pitidos = _pitidos(calendario, cierres)
    nombres_de_ronda = _nombres_de_ronda(calendario, cierres)

    onces = el_once_de_cada_ronda(
        entradas,
        calendario=calendario,
        cierres=cierres,
        congelados=onces_congelados,
    )

    por_ronda = {
        safe_int(entrada.get("round_id")): entrada
        for entrada in entradas
    }

    filas = [
        {
            "round_id": safe_int(perdida.get("round_id")),
            "medible": False,
            "motivo": perdida.get("motivo"),
        }
        for perdida in colocadas["sin_hora"]
    ]

    previa = None
    momento_previo = None

    for indice, item in enumerate(colocadas["ordenadas"]):

        actual = item["jornada"]

        # La ultima observada todavia no ha cerrado: sus puntos
        # de clasificacion siguen a cero y contarla hundiria la
        # media. Solo se miden las que ya tienen sucesora.
        #
        # SALVO QUE EL TABLON DIGA QUE CERRO (28/10/2026). La J10
        # cerro el 27/10 y es la ultima del libro: sin esto se
        # quedaba «en curso» hasta el pitido de la J11.
        cerrada = (
            indice < len(jornadas) - 1
            or bool(
                (cierres.get(safe_int(actual.get("round_id"))) or {})
                .get("termina")
            )
        )

        anterior = previa

        # EL HUECO. Se mira ANTES de restar: si entre la previa y
        # esta falta alguna jornada, la resta no es de una
        # jornada y el numero no significa lo que dice.
        hueco = (
            jornadas_en_medio(
                momento_previo,
                item["momento"],
                calendario,
            )
            if anterior is not None
            else []
        )

        # LA FOTO A MEDIAS, POR LOS DOS LADOS (14/09/2026)
        #
        #     Si la foto de ESTA jornada se tomo a mitad del
        #     abono, sus puntos de manager son un cero falso.
        #
        #     Y si es la foto ANTERIOR la que esta a medias, el
        #     cero falso se convierte en la referencia de la
        #     resta: restarle cero a un acumulado devuelve el
        #     acumulado entero. Eso es lo que publicaba 186
        #     puntos como si fueran los de una jornada.
        #
        #     Las dos cosas se dicen con su nombre en vez de
        #     dejar que salga un numero que parece bueno.
        a_medias = foto_a_medias(actual)

        referencia_a_medias = (
            foto_a_medias(anterior)
            if anterior is not None
            else None
        )

        puntos, motivo_puntos = _puntos_de_la_jornada(
            actual, anterior
        )

        previa = actual
        momento_previo = item["momento"]

        if (
            not cerrada
            or hueco
            or a_medias
            or referencia_a_medias
            or puntos is None
        ):

            # TODOS LOS MOTIVOS, NO SOLO EL PRIMERO (14/09/2026)
            #
            #     Una jornada puede estar rota por dos sitios a la
            #     vez —la 4 de esta liga lo esta: le faltan tres
            #     jornadas en medio Y su referencia es una foto a
            #     medias— y quedarse con el primero esconde el
            #     otro.
            #
            #     Arreglar uno y ver que sigue sin medirse, sin
            #     saber por que, es exactamente la tarde que no
            #     queremos.
            motivos = []

            if not cerrada:
                motivos.append("Jornada en curso.")

            if a_medias:
                motivos.append(a_medias)

            if hueco:
                cuales = ", ".join(
                    f"{f['nombre'] or f['round_id']}"
                    for f in hueco
                )

                motivos.append(
                    f"Falta la observacion de "
                    f"{len(hueco)} jornada(s) en medio "
                    f"({cuales}): la resta de totales cubriria "
                    f"{len(hueco) + 1} jornadas juntas y se "
                    f"publicaria como si fuera una. No se mide."
                )

            if referencia_a_medias:
                motivos.append(
                    f"La jornada anterior "
                    f"({safe_int(anterior.get('round_id'))}) "
                    f"tampoco sirve de referencia. "
                    f"{referencia_a_medias}"
                )

            if not motivos and motivo_puntos:
                motivos.append(motivo_puntos)

            motivo = " ".join(motivos) or None

            filas.append({
                "round_id": safe_int(actual.get("round_id")),
                "medible": False,
                "motivo": motivo,
                **_fechas_de(actual),

                # Que falta, en datos y no solo en la frase, para
                # que la pantalla pueda pintarlo sin reparsear.
                "jornadas_que_faltan": hueco,

                # En datos tambien: una foto a medias no es lo
                # mismo que un hueco, y la pantalla tiene que
                # poder distinguirlas sin leer la frase.
                "foto_a_medias": bool(a_medias),
                "referencia_a_medias": bool(referencia_a_medias),
            })
            continue

        round_id = safe_int(actual.get("round_id"))

        # ========================================================
        # EL ONCE QUE JUGO ESTA RONDA (28/10/2026)
        # ========================================================
        #
        #     Ya no es `actual["mi_once"]`: ese, desde la 4903, es
        #     el de la ronda SIGUIENTE. Sale de
        #     `el_once_de_cada_ronda`, con su fuente.
        asignado = onces.get(round_id) or {}

        # La entrada en la que se VIO ese once. Su plantilla es la
        # de mientras se jugaba la ronda, que es la que vale para
        # el techo: la de `actual` ya trae los fichajes de despues.
        vista = por_ronda.get(safe_int(asignado.get("de_la_entrada"))) or actual

        alineados = [str(p) for p in (asignado.get("players") or [])]

        once = {
            "formation": asignado.get("formation"),
            "players": alineados,
        }

        anotado_aqui = [
            str(safe_int(p))
            for p in _ids(actual.get("mi_once"))
        ]

        # ========================================================
        # LOS PUNTOS DE CADA JUGADOR EN ESTA RONDA
        # ========================================================
        #
        #     La resta de siempre entre dos entradas: va de cache a
        #     cache, la mañana de un pitido a la del siguiente, y
        #     no se deja el lunes. La foto de cierre de LaLiga se
        #     hace ANTES de puntuar el lunes (ver `LA FOTO DE CIERRE
        #     SE HACE ANTES DE PUNTUAR EL LUNES`): solo rellena a
        #     quien no esta en las dos entradas, y solo si su
        #     ventana pasa la prueba de fugas.
        puntos_ronda = dict(puntos)
        fuente_puntos = PUNTOS_DE_LA_RESTA

        totales_ahora = actual.get("totales") or {}
        totales_antes = (anterior or {}).get("totales") or {}

        # UN FICHADO A MITAD NO ES UN CERO. `_puntos_de_la_
        # jornada` le pone 0 al que no estaba en la previa;
        # para el once eso es un hueco, no un dato. En la
        # primera jornada no hay previa: el total ES la ronda.
        def tiene_dato(player_id):
            return player_id in totales_ahora and (
                anterior is None
                or player_id in totales_antes
            )

        cierre_laliga = puntos_de_cierre(
            fotos_de_cierre,
            round_id,
            pitidos,
            nombres_de_ronda,
            resta={
                player_id: valor
                for player_id, valor in puntos.items()
                if tiene_dato(player_id)
            },
        )

        faltan = []
        sin_partido = []
        del_cierre = []

        for player_id in alineados:

            if tiene_dato(player_id):
                continue

            # EL VENDIDO, DE LA FOTO LIMPIA. Solo si jugo en la
            # ventana: un (0, 0) no es un dato de la foto, es la
            # pregunta de abajo.
            if (
                cierre_laliga["limpia"]
                and player_id in cierre_laliga["puntos"]
                and safe_int(cierre_laliga["jugados"].get(player_id)) > 0
            ):
                puntos_ronda[player_id] = cierre_laliga["puntos"][player_id]
                del_cierre.append(player_id)
                continue

            # SIN PARTIDO NO HAY PUNTOS. Si consta que no jugo
            # ninguno en la ronda, su ronda es un cero cierto,
            # aunque ya no este en la plantilla. Con la misma
            # guardia que la foto: un (0, 0) en una ventana con
            # fugas no prueba nada.
            if _sin_partido(
                fotos_de_cierre,
                pitidos.get(round_id),
                player_id,
                termina=(cierres.get(round_id) or {}).get("termina"),
                limpia=cierre_laliga["limpia"],
            ):
                puntos_ronda[player_id] = 0
                sin_partido.append(player_id)
                continue

            faltan.append(player_id)

        posiciones = {
            str(j.get("id")): safe_int(j.get("position"))
            for j in (vista.get("plantilla") or actual.get("plantilla") or [])
        }

        puntos_alineados = sum(
            safe_int(puntos_ronda.get(p))
            for p in alineados
        )

        techo = mejor_once(
            {
                player_id: valor
                for player_id, valor in puntos_ronda.items()
                if player_id in posiciones
            },
            posiciones,
            alineados=alineados,
            formacion_usada=once.get("formation"),
        )

        mi_user_id = safe_int(actual.get("mi_user_id"))

        # ========================================================
        # LA VERDAD: LO QUE PAGO BIWENGER EN ESTA RONDA
        # ========================================================
        #
        #     Con tablon, `roundFinished` ronda a ronda. Si el
        #     tablon conoce la ronda y no la cerro (J8; J6 parte
        #     1, que la liga ignora), no hay verdad y se dice.
        #     Sin tablon, la resta de la clasificacion de siempre.
        cierre_tablon = cierres.get(round_id)

        motivo_sin_verdad = None

        if cierre_tablon is not None:

            oficiales = cierre_tablon.get("puntos")
            fuente_verdad = VERDAD_DEL_TABLON if oficiales is not None else None

            if oficiales is None:
                motivo_sin_verdad = (
                    f"Biwenger no publico el cierre de "
                    f"{cierre_tablon.get('nombre') or round_id} en el "
                    f"tablon (sin `roundFinished`): no hay verdad "
                    f"con la que cuadrar."
                )

        else:
            # POR DIFERENCIA, COMO LOS JUGADORES (17/09/2026)
            #
            #     `points` de la clasificacion es el acumulado de
            #     la temporada. Compararlo con el once de UNA
            #     jornada es comparar 60 con 17.
            oficiales = _puntos_de_la_clasificacion(actual, anterior)
            fuente_verdad = VERDAD_DE_LA_CLASIFICACION

        mios = (
            oficiales.get(mi_user_id)
            if oficiales is not None
            else None
        )

        rivales = [
            puntos_rival
            for user_id, puntos_rival in (oficiales or {}).items()
            if user_id != mi_user_id
        ]

        media_rivales = (
            round(sum(rivales) / len(rivales), 1)
            if rivales
            else None
        )

        # ¿MIDIO ALGO LA COMPARACION CON LA LIGA?
        #
        #     `oficiales` es el reparto de puntos de la
        #     clasificacion entre esta jornada y su referencia.
        #     Si sale entero a cero —nosotros y los ocho
        #     rivales—, la resta no encontro nada: no es que la
        #     liga puntuara cero, es que no se pudo medir.
        #
        #     Se publica al lado para que la pantalla pueda
        #     decirlo, y para que la media no lo cuente como un
        #     cero de verdad.
        liga_medida = bool(rivales) and any(
            safe_int(p) != 0
            for p in list(rivales) + [mios if mios is not None else 0]
        )

        # Sin once no hay nota: un 0 % seria la nota de nadie.
        eficiencia = (
            round(100 * puntos_alineados / techo["points"], 1)
            if techo.get("points") and alineados
            else None
        )

        nombres = {
            **(vista.get("nombres") or {}),
            **(actual.get("nombres") or {}),
        }

        if not alineados:
            completa, motivo_incompleta = False, (
                "No se anoto que once jugo esa jornada."
            )

        elif faltan:
            quienes = ", ".join(
                str(nombres.get(p) or f"#{p}")
                for p in faltan
            )

            completa, motivo_incompleta = False, (
                f"{len(faltan)} de los {len(alineados)} que "
                f"alinearon no tienen los puntos de esta ronda "
                f"({quienes}): se vendieron o se ficharon entre "
                f"las dos fotos, asi que el once reconstruido sale "
                f"corto."
                + (
                    f" La foto de cierre no los rellena: "
                    f"{cierre_laliga['motivo']}"
                    if cierre_laliga.get("motivo")
                    else ""
                )
            )

        else:
            completa, motivo_incompleta = True, None

        aplazada = es_aplazada(
            (nombres_de_ronda.get(round_id) or {}).get("nombre"),
            (nombres_de_ronda.get(round_id) or {}).get("part"),
        )

        # LAS EXCEPCIONES, ESCRITAS EN LA FILA. No cambian el
        # cuadre: dicen por que puede no darse.
        excepciones = []

        if aplazada:
            excepciones.append(
                "Ronda partida (aplazada): Biwenger la puntua con "
                "el once bloqueado en SU pitido. Si esa misma noche "
                "se toco el once para la siguiente, el que se vio "
                "por la mañana ya no es el que puntuo, y la resta "
                "de observaciones mezcla horas de dos rondas."
            )

        if motivo_sin_verdad:
            excepciones.append(motivo_sin_verdad)

        if not alineados:
            excepciones.append(
                "El once de esta ronda no se guardo en ninguna "
                "entrada: no se reconstruye a ojo."
            )

        filas.append({
            "round_id": round_id,
            "medible": True,
            "liga_medida": liga_medida,
            **_fechas_de(actual),

            # UN NUMERO COJO NO ES UNA NOTA (17/09/2026)
            #
            #     Si faltaba media alineacion, "61,9 % del
            #     optimo" no mide el motor: mide el agujero.
            "reconstruccion_completa": completa,
            "motivo_incompleta": motivo_incompleta,

            # EL ONCE QUE JUGO, Y DE DONDE SALE (28/10/2026)
            "formacion": once.get("formation"),
            "once": [safe_int(p) for p in alineados],
            "once_fuente": asignado.get("fuente"),
            "once_de_la_entrada": asignado.get("de_la_entrada"),
            "once_visto_en": asignado.get("visto_en"),
            "once_congelado_coincide": asignado.get("congelado_coincide"),

            # El que guardaba ESTA entrada. Si no coincide con el
            # de arriba, es el desplazamiento: se ve en la fila.
            "once_anotado_en_la_entrada": [
                safe_int(p) for p in anotado_aqui
            ],
            "once_desplazado": (
                bool(anotado_aqui)
                and set(anotado_aqui) != set(alineados)
            ),

            "puntos_fuente": fuente_puntos,
            "puntos_cierre_motivo": (
                None if cierre_laliga["limpia"]
                else cierre_laliga.get("motivo")
            ),
            # Los que no estaban en las dos entradas y salen de la
            # foto de cierre limpia (`PUNTOS_DEL_CIERRE`).
            "puntos_del_cierre": [safe_int(p) for p in del_cierre],
            "sin_partido": [safe_int(p) for p in sin_partido],

            "puntos_once": puntos_alineados,

            "mejor_formacion": techo.get("formation"),
            "mejor_puntos": techo.get("points"),
            "mejor_once": techo.get("players"),
            "eficiencia": eficiencia,

            "puntos_perdidos": (
                safe_int(techo.get("points")) - puntos_alineados
            ),

            "detalle": _detalle(
                puntos_ronda,
                vista.get("plantilla") or actual.get("plantilla") or [],
                alineados,
                techo.get("players") or [],
                nombres,
            ),

            # LOS TRES NUMEROS JUNTOS (18/09/2026)
            #
            #     Alineamos / habria alineado la vara vieja /
            #     mejor posible. Sin los tres no se puede saber
            #     si los factores por posicion suman o restan.
            #
            #     Y DE LA MISMA VISTA QUE EL ONCE (28/10/2026): el
            #     once de la vara vieja se anoto en la misma
            #     entrada y a la misma hora que el nuestro, asi que
            #     va con el a la ronda que jugo.
            "puntos_por_vara": {
                nombre: _puntos_del_once(
                    puntos_ronda, (datos or {}).get("players")
                )
                for nombre, datos in (
                    asignado.get("onces_por_vara") or {}
                ).items()
            },

            "puntos_vara_vieja": _puntos_del_once(
                puntos_ronda,
                (asignado.get("once_alternativo") or {}).get(
                    "players"
                ),
            ),
            "formacion_vara_vieja": (
                (asignado.get("once_alternativo") or {}).get(
                    "formation"
                )
            ),

            "puntos_biwenger": mios,
            "puntos_biwenger_fuente": fuente_verdad,
            "puntos_biwenger_acumulado": next(
                (
                    safe_int(f.get("points"))
                    for f in (actual.get("clasificacion") or [])
                    if safe_int(f.get("user_id")) == mi_user_id
                ),
                None,
            ),
            # CERO CONTRA CERO SIEMPRE CUADRA  (20/09/2026)
            #
            #     4904 salia con `cuadra: true` teniendo
            #     `puntos_once: 0`, `puntos_biwenger: 0` y
            #     `reconstruccion_completa: false` — motivo:
            #     «No se anoto que once jugo esa jornada».
            #
            #     Un verde que puede darse SIN HABER MEDIDO NADA
            #     vale lo mismo que un rojo (doctrina 91, del
            #     otro lado). Si no hubo reconstruccion, el
            #     cuadre no es falso: es que NO ES MEDIBLE, y
            #     eso se dice con un `None`, no con un `true`.
            #
            #     Y SIN VERDAD TAMPOCO (28/10/2026): una ronda que
            #     Biwenger no cerro no cuadra ni descuadra.
            "cuadra": (
                None
                if not completa or (mios is None and motivo_sin_verdad)
                else (
                    mios is not None
                    and mios == puntos_alineados
                )
            ),

            "cuadra_motivo": (
                (
                    f"Cuadre no medible: {motivo_incompleta}"
                    if motivo_incompleta
                    else "Cuadre no medible: la reconstruccion "
                         "del once quedo incompleta."
                )
                + (
                    f" Con los que constan suman {puntos_alineados}; "
                    f"Biwenger pago {mios}."
                    if mios is not None and faltan
                    else ""
                )
                if not completa
                else (
                    f"Cuadre no medible: {motivo_sin_verdad}"
                    if mios is None and motivo_sin_verdad
                    else _por_que_no_cuadra(mios, puntos_alineados, aplazada)
                )
            ),

            "excepcion": " ".join(excepciones) or None,

            # CUANTO FALTA PARA CUADRAR (17/09/2026)
            #
            #     "No cuadra" a secas no distingue entre una
            #     reconstruccion que se queda a 3 puntos de 73 y
            #     otra que se queda a 16 de 29. La primera es
            #     util con una nota al pie; la segunda no vale.
            #
            #     El cuadre sigue siendo exacto y la media sigue
            #     siendo estricta: esto solo lo hace legible.
            "descuadre": (
                mios - puntos_alineados
                if mios is not None
                else None
            ),
            "descuadre_percent": (
                round(
                    abs(mios - puntos_alineados) / mios * 100,
                    1,
                )
                if mios
                else None
            ),

            "media_rivales": media_rivales,

            # CONTRA LA LIGA SE COMPARA CON EL DATO OFICIAL
            # (21/08/2026)
            #
            # Salia -11,5 cuando la verdad era +4,5. Se estaba
            # restando NUESTRA reconstruccion del once (13) a la
            # media de los rivales, en vez de los puntos que
            # Biwenger le dio de verdad (29).
            #
            # La reconstruccion solo hace falta para el
            # contrafactual. Lo que puntuo Pepe es un hecho y no
            # hay que deducirlo.
            "diferencia_liga": (
                round(
                    (mios if mios is not None else puntos_alineados)
                    - media_rivales,
                    1,
                )
                if media_rivales is not None
                else None
            ),
        })

    medibles = [f for f in filas if f.get("medible")]

    # UNA JORNADA QUE NO CUADRA NO PUNTUA (21/08/2026)
    #
    #     La jornada 1 salio con 61,9 % en rojo grande y "NO
    #     CUADRA" en pequeño al lado. Los dos numeros no pueden
    #     convivir: si la reconstruccion del once no suma lo que
    #     Biwenger pago, esa nota no mide nada.
    #
    #     Y en ese caso concreto la nota estaba mal de verdad: el
    #     once que anotamos no era el que jugo -se anoto un dia
    #     tarde, con la alineacion ya cambiada-, asi que salian 13
    #     puntos donde Biwenger pago 29.
    #
    #     El cuadre existe justo para eso. Lo que faltaba era que
    #     tuviera consecuencias: una jornada que no cuadra sale de
    #     la media, no se promedia con las buenas.
    #
    # La diferencia contra la liga SI se conserva: sale de los
    # puntos oficiales, que son un hecho, y no depende de que
    # nuestra reconstruccion sea buena.
    fiables = [
        f
        for f in medibles
        if f.get("cuadra")
        and f.get("reconstruccion_completa")
    ]

    resumen = {
        # TODAS las observadas, tengan hora o no: si una se cae
        # del orden por no saber cuando se jugo, tiene que seguir
        # contando como observada o el hueco se vuelve invisible.
        "jornadas_observadas": len(filas),
        "jornadas_sin_hora": len(colocadas["sin_hora"]),
        "jornadas_con_hueco": len([
            f
            for f in filas
            if f.get("jornadas_que_faltan")
        ]),
        "jornadas_a_medias": len([
            f
            for f in filas
            if f.get("foto_a_medias")
            or f.get("referencia_a_medias")
        ]),
        "jornadas_medibles": len(medibles),
        "jornadas_fiables": len(fiables),
        "jornadas_descartadas": len(medibles) - len(fiables),

        # EL DESPLAZAMIENTO, CONTADO (28/10/2026): en cuantas
        # filas el once que guardaba la entrada NO es el que jugo
        # su ronda. Y contra que verdad se cuadra.
        "jornadas_con_once_desplazado": len([
            f for f in medibles if f.get("once_desplazado")
        ]),
        "verdad": (
            VERDAD_DEL_TABLON if cierres else VERDAD_DE_LA_CLASIFICACION
        ),
        "eficiencia_media": None,
        "diferencia_media": None,
        "diferencia_media_n": 0,
        # Y SOLO SOBRE LAS QUE SE PUDO MEDIR. Un `None` no es
        # un `False`: contarlo como fallo seria la otra mitad
        # del mismo error.
        "cuadra_todo": (
            all(
                f["cuadra"]
                for f in medibles
                if f.get("cuadra") is not None
            )
            if any(
                f.get("cuadra") is not None for f in medibles
            )
            else None
        ),
        "veredicto": "Sin jornadas cerradas todavia.",
    }

    if medibles:

        eficiencias = [
            f["eficiencia"]
            for f in fiables
            if f.get("eficiencia") is not None
        ]

        if eficiencias:
            resumen["eficiencia_media"] = round(
                sum(eficiencias) / len(eficiencias), 1
            )

        # UNA JORNADA EN LA QUE NADIE PUNTUO NO MIDIO NADA
        # (doctrina 82, 17/09/2026)
        #
        #     MEDIDO EN LA FOTO DEL 17/09: se publicaba
        #     `diferencia_media: 1.5` con `jornadas_fiables: 0`.
        #     El 1,5 era la media de 0,0, 0,0 y 4,5.
        #
        #     EL 4,5 ES UN HECHO y se queda: Biwenger nos dio 29
        #     y la media de rivales fue 24,5. El comentario de
        #     arriba tiene razon en eso, y la guardia
        #     `test_contra_la_liga_manda_el_dato_oficial` lo
        #     lleva atado desde el 21/08.
        #
        #     LOS DOS CEROS NO LO SON. 4903 y 4904 entraban con
        #     `media_rivales: 0,0` — y 4903 tiene DIEZ partidos y
        #     nuestro once sumo 60 puntos. Que los ocho managers
        #     de la liga puntuen exactamente cero no pasa: eso no
        #     es una jornada mala, es una resta que no midio
        #     nada.
        #
        #     Asi que lo que se excluye no son las jornadas que
        #     no cuadran —esas siguen aportando su hecho— sino
        #     las que NO MIDIERON LA LIGA. El discriminante es
        #     que el reparto oficial entero salga a cero.
        #
        #     El 1,5 era un 4,5 hundido por dos ceros que no
        #     median nada.
        diferencias = [
            f["diferencia_liga"]
            for f in medibles
            if f.get("diferencia_liga") is not None
            and f.get("liga_medida")
        ]

        # Y CON SU `n` AL LADO (doctrina 55). Un promedio sobre
        # una sola jornada no es lo mismo que sobre diez, y la
        # pantalla no puede distinguirlos si solo recibe el
        # numero.
        resumen["diferencia_media_n"] = len(diferencias)

        if diferencias:
            resumen["diferencia_media"] = round(
                sum(diferencias) / len(diferencias), 1
            )

        if eficiencias:
            resumen["veredicto"] = _veredicto(
                resumen["eficiencia_media"],
                len(eficiencias),
            )

        elif resumen["jornadas_descartadas"]:
            resumen["veredicto"] = (
                f"{resumen['jornadas_descartadas']} jornada(s) "
                f"cerrada(s), pero ninguna cuadra con Biwenger "
                f"({len([f for f in medibles if f.get('cuadra') is False])} "
                f"no cuadran y el resto no se pueden cuadrar: cada "
                f"fila dice por que). Sin "
                f"nota hasta que coincidan — ni eficiencia media "
                f"ni diferencia con la liga: las dos se quedan "
                f"sin valor a proposito, porque una media de "
                f"jornadas descartadas no mide nada."
            )

    return {
        "resumen": resumen,
        "jornadas": filas,
    }


def _detalle(
    puntos: dict,
    plantilla: list,
    alineados: list,
    del_techo: list,
    nombres: dict | None = None,
) -> dict:
    """Quien debio jugar y no jugo, y al reves.

    Es lo unico accionable del marcador: un porcentaje no se
    puede corregir, un nombre si.
    """

    ficha = {
        str(j.get("id")): j
        for j in (plantilla or [])
    }

    nombres = nombres or {}

    def describir(player_id):
        jugador = ficha.get(player_id) or {}

        # Un jugador que alineo el sabado y se vendio el domingo
        # ya no esta en la plantilla del dia. Su nombre si, en el
        # mapa que se anota con la foto. Enseñar un id no informa
        # de nada.
        nombre = (
            jugador.get("name")
            or nombres.get(str(player_id))
        )

        return {
            "id": safe_int(player_id),
            "name": nombre or f"#{player_id}",
            "sold": nombre is None or not jugador,
            "position": safe_int(jugador.get("position")),
            "points": safe_int(puntos.get(player_id)),
        }

    en_el_once = set(alineados or [])
    en_el_techo = set(del_techo or [])

    faltaron = [
        describir(p)
        for p in en_el_techo - en_el_once
    ]

    sobraron = [
        describir(p)
        for p in en_el_once - en_el_techo
    ]

    faltaron.sort(
        key=lambda item: item["points"],
        reverse=True,
    )

    sobraron.sort(key=lambda item: item["points"])

    return {
        "faltaron": faltaron,
        "sobraron": sobraron,
    }


def _veredicto(eficiencia, cuantas: int) -> str:

    if eficiencia is None:
        return "Sin jornadas cerradas todavia."

    if cuantas < 4:
        return (
            f"{eficiencia} % del once optimo con solo "
            f"{cuantas} jornada(s). Demasiado pronto para "
            f"concluir nada."
        )

    if eficiencia >= 85:
        return (
            f"{eficiencia} % del once optimo. El motor de "
            f"alineacion esta terminado: dejar de tocarlo y "
            f"mirar al mercado."
        )

    if eficiencia >= 70:
        return (
            f"{eficiencia} % del once optimo. Hay margen, pero "
            f"no es donde esta la liga."
        )

    return (
        f"{eficiencia} % del once optimo. Ahi esta la liga "
        f"entera: el problema es elegir el once, no fichar."
    )


# ============================================================
# PANTALLA
# ============================================================


def estado_para_dashboard(
    calendario: dict | None = None,
    eventos=None,
    onces_congelados=None,
    fotos_de_cierre=None,
) -> dict:
    """El marcador tal y como lo consume la seccion MARCADOR.

    Se declara `available` siempre que se pueda leer el ledger,
    aunque no haya ninguna jornada cerrada: la pantalla tiene que
    poder decir "todavia no hay nada" en vez de desaparecer.

    `calendario` entra por la puerta (regla 23): lo construye
    quien tiene la foto y el calendario de LaLiga delante, no
    este modulo. Y lo mismo el tablon, los onces congelados y las
    fotos de cierre (28/10/2026): ver `marcador()`.
    """

    try:
        datos = marcador(
            calendario,
            eventos=eventos,
            onces_congelados=onces_congelados,
            fotos_de_cierre=fotos_de_cierre,
        )
    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "reason": f"No se pudo leer el marcador: {error}",
            "resumen": {},
            "jornadas": [],
        }

    resumen = datos.get("resumen") or {}

    return {
        "available": True,
        "reason": resumen.get("veredicto"),
        "resumen": resumen,

        # De mas reciente a mas antigua: la ultima jornada es lo
        # que se mira, no la primera.
        "jornadas": list(
            reversed(datos.get("jornadas") or [])
        ),
    }


# ============================================================
# CLI
# ============================================================


def main() -> None:

    datos = marcador()
    resumen = datos["resumen"]

    print()
    print("=" * 70)
    print("BORDALAS IA - MARCADOR")
    print("=" * 70)
    print()
    print(f"Jornadas observadas: {resumen['jornadas_observadas']}")
    print(f"Jornadas medibles:   {resumen['jornadas_medibles']}")
    print()

    for fila in datos["jornadas"]:

        if not fila.get("medible"):
            print(
                f"  J{fila['round_id']}  -  "
                f"{fila.get('motivo')}"
            )
            continue

        print(
            f"  J{fila['round_id']}  "
            f"{fila['formacion']} {fila['puntos_once']} pts  |  "
            f"techo {fila['mejor_formacion']} "
            f"{fila['mejor_puntos']} pts  |  "
            f"{fila['eficiencia']} %  |  "
            f"liga {fila['media_rivales']} "
            f"({fila['diferencia_liga']:+})"
            f"{_sello_del_cuadre(fila)}"
        )

    print()
    print(f"Eficiencia media:  {resumen['eficiencia_media']}")
    print(f"Contra la liga:    {resumen['diferencia_media']}")
    print()
    print(resumen["veredicto"])
    print("=" * 70)


if __name__ == "__main__":
    main()
