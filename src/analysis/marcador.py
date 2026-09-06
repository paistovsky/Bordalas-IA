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

from datetime import datetime
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


def _mi_fila(snapshot: dict, current_user_id) -> dict:
    """La fila de Pepe en la clasificacion.

    Se busca por id de usuario. Si no lo tenemos, no se adivina
    por nombre: una fila equivocada haria que el cuadre diera
    falso positivo para siempre.
    """

    user_id = safe_int(current_user_id)

    if not user_id:
        return {}

    for fila in (_liga(snapshot).get("standings") or []):

        if not isinstance(fila, dict):
            continue

        if safe_int(fila.get("id")) == user_id:
            return fila

    return {}


def observar(
    snapshot: dict,
    current_user_id=None,
    once_alternativo: dict | None = None,
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

    mi_fila = _mi_fila(snapshot, current_user_id)
    alineacion = mi_fila.get("lineup") or {}

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

    for player_id in (alineacion.get("players") or []):

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

    ledger["jornadas"][str(round_id)] = {
        "round_id": round_id,
        "visto": datetime.now().isoformat(),
        "clasificacion": clasificacion,
        "mi_user_id": safe_int(current_user_id),
        "mi_once": {
            "formation": alineacion.get("type"),
            "players": [
                safe_int(p)
                for p in (alineacion.get("players") or [])
            ],
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

    ledger["updated_at"] = datetime.now().isoformat()

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


def _puntos_de_la_jornada(
    actual: dict,
    previa: dict | None,
) -> dict | None:
    """Puntos por jugador en esa jornada, por diferencia de totales.

    Devuelve None cuando no se puede medir. No se estima.
    """

    totales = actual.get("totales") or {}

    if previa is None:

        if safe_int(actual.get("round_id")) == PRIMERA_JORNADA:
            # No hay nada antes: el total ES la jornada.
            return dict(totales)

        return None

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

    return puntos


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

    return {
        user_id: puntos - antes.get(user_id, 0)
        for user_id, puntos in ahora.items()
        if user_id in antes
    }


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


def marcador() -> dict:
    """Lee el ledger y contesta las tres preguntas."""

    ledger = cargar_ledger()

    jornadas = sorted(
        (ledger.get("jornadas") or {}).values(),
        key=lambda item: safe_int(item.get("round_id")),
    )

    filas = []
    previa = None

    for indice, actual in enumerate(jornadas):

        # La jornada en curso todavia no ha cerrado: sus puntos
        # de clasificacion siguen a cero y contarla hundiria la
        # media. Solo se miden las que ya tienen sucesora.
        cerrada = indice < len(jornadas) - 1

        anterior = previa

        puntos = _puntos_de_la_jornada(actual, anterior)
        previa = actual

        if not cerrada or puntos is None:
            filas.append({
                "round_id": safe_int(actual.get("round_id")),
                "medible": False,
                "motivo": (
                    "Jornada en curso."
                    if not cerrada
                    else "Sin observacion de la jornada anterior."
                ),
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
        "jornadas_observadas": len(jornadas),
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


def estado_para_dashboard() -> dict:
    """El marcador tal y como lo consume la seccion MARCADOR.

    Se declara `available` siempre que se pueda leer el ledger,
    aunque no haya ninguna jornada cerrada: la pantalla tiene que
    poder decir "todavia no hay nada" en vez de desaparecer.
    """

    try:
        datos = marcador()
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
