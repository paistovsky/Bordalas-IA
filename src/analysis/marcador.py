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

from datetime import datetime, timezone
from pathlib import Path


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


def observar(
    snapshot: dict,
    current_user_id=None,
    once_alternativo: dict | None = None,
    escrito_en=None,
) -> dict:
    """Anota la jornada en curso tal y como se ve ahora mismo.

    Se llama en cada ciclo. Sobreescribe la observacion de esa
    jornada, de modo que la que queda es siempre la ultima antes
    de que Biwenger salte a la siguiente: la definitiva.
    """

    round_id = jornada_en_curso(snapshot)

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

    ledger["jornadas"][str(round_id)] = {
        "round_id": round_id,
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
        "mi_once": {
            "formation": alineacion.get("type"),
            "players": list(once_de_hoy),
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
        # que ya no estan en la plantilla.
        "nombres": nombres,
    }

    ledger["updated_at"] = escritura

    guardar_ledger(ledger)

    return {
        "anotada": True,
        "round_id": round_id,
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

        return None, (
            f"{len(negativos)} jugador(es) con puntos negativos "
            f"al restar los totales de la jornada "
            f"{safe_int(previa.get('round_id'))} a los de la "
            f"{safe_int(actual.get('round_id'))} (el mayor, "
            f"{peor[1]} en el jugador {peor[0]}). Un jugador no "
            f"pierde puntos de temporada: las dos fotos estan al "
            f"reves. No se mide esta jornada."
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


def marcador(calendario: dict | None = None) -> dict:
    """Lee el ledger y contesta las tres preguntas.

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

    colocadas = orden_en_el_tiempo(
        list((ledger.get("jornadas") or {}).values()),
        calendario,
    )

    jornadas = [item["jornada"] for item in colocadas["ordenadas"]]

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
        cerrada = indice < len(jornadas) - 1

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

        posiciones = {
            str(j.get("id")): safe_int(j.get("position"))
            for j in (actual.get("plantilla") or [])
        }

        once = actual.get("mi_once") or {}

        alineados = [
            str(p)
            for p in (once.get("players") or [])
        ]

        puntos_alineados = sum(
            safe_int(puntos.get(p))
            for p in alineados
        )

        techo = mejor_once(
            puntos,
            posiciones,
            alineados=alineados,
            formacion_usada=once.get("formation"),
        )

        mi_user_id = safe_int(actual.get("mi_user_id"))

        # POR DIFERENCIA, COMO LOS JUGADORES (17/09/2026)
        #
        #     `points` de la clasificacion es el acumulado de la
        #     temporada. Compararlo con el once de UNA jornada
        #     es comparar 60 con 17.
        oficiales = _puntos_de_la_clasificacion(actual, anterior)

        mios = (
            oficiales.get(mi_user_id)
            if oficiales is not None
            else None
        )

        rivales = [
            puntos
            for user_id, puntos in (oficiales or {}).items()
            if user_id != mi_user_id
        ]

        media_rivales = (
            round(sum(rivales) / len(rivales), 1)
            if rivales
            else None
        )

        eficiencia = (
            round(100 * puntos_alineados / techo["points"], 1)
            if techo.get("points")
            else None
        )

        completa, motivo_incompleta = _reconstruccion_completa(actual)

        filas.append({
            "round_id": safe_int(actual.get("round_id")),
            "medible": True,
            **_fechas_de(actual),

            # UN NUMERO COJO NO ES UNA NOTA (17/09/2026)
            #
            #     Si faltaba media alineacion, "61,9 % del
            #     optimo" no mide el motor: mide el agujero.
            "reconstruccion_completa": completa,
            "motivo_incompleta": motivo_incompleta,

            "formacion": once.get("formation"),
            "puntos_once": puntos_alineados,

            "mejor_formacion": techo.get("formation"),
            "mejor_puntos": techo.get("points"),
            "mejor_once": techo.get("players"),
            "eficiencia": eficiencia,

            "puntos_perdidos": (
                safe_int(techo.get("points")) - puntos_alineados
            ),

            "detalle": _detalle(
                puntos,
                actual.get("plantilla") or [],
                alineados,
                techo.get("players") or [],
                actual.get("nombres") or {},
            ),

            # LOS TRES NUMEROS JUNTOS (18/09/2026)
            #
            #     Alineamos / habria alineado la vara vieja /
            #     mejor posible. Sin los tres no se puede saber
            #     si los factores por posicion suman o restan.
            # Los tres onces, cada uno con sus puntos, para que
            # el efecto de los factores y el de la calidad se
            # puedan separar en vez de ir mezclados.
            "puntos_por_vara": {
                nombre: _puntos_del_once(
                    puntos, (datos or {}).get("players")
                )
                for nombre, datos in (
                    actual.get("onces_por_vara") or {}
                ).items()
            },

            "puntos_vara_vieja": _puntos_del_once(
                puntos,
                (actual.get("once_alternativo") or {}).get(
                    "players"
                ),
            ),
            "formacion_vara_vieja": (
                (actual.get("once_alternativo") or {}).get(
                    "formation"
                )
            ),

            "puntos_biwenger": mios,
            "puntos_biwenger_acumulado": next(
                (
                    safe_int(f.get("points"))
                    for f in (actual.get("clasificacion") or [])
                    if safe_int(f.get("user_id")) == mi_user_id
                ),
                None,
            ),
            "cuadra": (
                mios is not None
                and mios == puntos_alineados
            ),

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
        "eficiencia_media": None,
        "diferencia_media": None,
        "cuadra_todo": all(
            f.get("cuadra") for f in medibles
        ) if medibles else None,
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

        diferencias = [
            f["diferencia_liga"]
            for f in medibles
            if f.get("diferencia_liga") is not None
        ]

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
                f"cerrada(s), pero ninguna cuadra con Biwenger: "
                f"el once que anotamos no es el que jugo. Sin "
                f"nota hasta que coincidan."
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


def estado_para_dashboard(calendario: dict | None = None) -> dict:
    """El marcador tal y como lo consume la seccion MARCADOR.

    Se declara `available` siempre que se pueda leer el ledger,
    aunque no haya ninguna jornada cerrada: la pantalla tiene que
    poder decir "todavia no hay nada" en vez de desaparecer.

    `calendario` entra por la puerta (regla 23): lo construye
    quien tiene la foto y el calendario de LaLiga delante, no
    este modulo.
    """

    try:
        datos = marcador(calendario)
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
            f"{'' if fila['cuadra'] else '  [NO CUADRA]'}"
        )

    print()
    print(f"Eficiencia media:  {resumen['eficiencia_media']}")
    print(f"Contra la liga:    {resumen['diferencia_media']}")
    print()
    print(resumen["veredicto"])
    print("=" * 70)


if __name__ == "__main__":
    main()
