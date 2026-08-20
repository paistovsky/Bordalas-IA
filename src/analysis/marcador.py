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

        puntos = _puntos_de_la_jornada(actual, previa)
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

        clasificacion = actual.get("clasificacion") or []
        mi_user_id = safe_int(actual.get("mi_user_id"))

        mios = next(
            (
                safe_int(f.get("points"))
                for f in clasificacion
                if safe_int(f.get("user_id")) == mi_user_id
            ),
            None,
        )

        rivales = [
            safe_int(f.get("points"))
            for f in clasificacion
            if safe_int(f.get("user_id")) != mi_user_id
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

        filas.append({
            "round_id": safe_int(actual.get("round_id")),
            "medible": True,

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
            ),

            "puntos_biwenger": mios,
            "cuadra": (
                mios is not None
                and mios == puntos_alineados
            ),

            "media_rivales": media_rivales,
            "diferencia_liga": (
                round(puntos_alineados - media_rivales, 1)
                if media_rivales is not None
                else None
            ),
        })

    medibles = [f for f in filas if f.get("medible")]

    resumen = {
        "jornadas_observadas": len(jornadas),
        "jornadas_medibles": len(medibles),
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
            for f in medibles
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

        resumen["veredicto"] = _veredicto(
            resumen["eficiencia_media"],
            len(medibles),
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
) -> dict:
    """Quien debio jugar y no jugo, y al reves.

    Es lo unico accionable del marcador: un porcentaje no se
    puede corregir, un nombre si.
    """

    ficha = {
        str(j.get("id")): j
        for j in (plantilla or [])
    }

    def describir(player_id):
        jugador = ficha.get(player_id) or {}
        return {
            "id": safe_int(player_id),
            "name": jugador.get("name") or str(player_id),
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
