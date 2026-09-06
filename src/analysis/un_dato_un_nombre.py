"""
Un concepto, un nombre. Y si viaja con dos, que los dos valgan.

CUATRO INCIDENTES DE LA MISMA FAMILIA EN UNA SEMANA

    12/09  `in_lineup` contra `is_starter`. La regla del portero
           miraba el primero y el dashboard publicaba el segundo:
           Dituro, unico portero y titular, no salia protegido.

    17/09  `store_depth()` sin `retention_days` cuando no habia
           almacen. La guardia del arbitro daba la clave por
           segura y se caia en un checkout limpio.

    17/09  `hold_value` devolvia menos claves por el camino "sin
           valor": KeyError en vez de un rojo legible.

    22/09  `playedHome/playedAway` existian en `my_team` y no en
           la plantilla publicada. El motor calculaba la calidad
           medida y quien leia el tablero no podia reproducirla:
           le salia otro once.

    Los dos del medio ya tienen su regla —una funcion no cambia
    de forma segun los datos, `test_forma_estable_v1`—. Los otros
    dos son la hermana que faltaba: **el mismo concepto con dos
    nombres**.

QUE HACE ESTE MODULO Y QUE NO

    No renombra nada. Renombrar `in_lineup` en veinte ficheros a
    estas alturas es una refactorizacion general, y cuatro
    incidentes justifican cerrar cuatro puertas, no reescribir la
    casa.

    Lo que hace es declarar los conceptos que viajan con mas de
    un nombre y ofrecer una forma de leerlos que entiende todos.
    Con eso, quien lee no tiene que saber de donde viene la
    ficha.

    Y la guardia que lo acompaña no comprueba nombres: comprueba
    COMPORTAMIENTO. Una ficha con el alias tiene que dar la misma
    respuesta que una con el nombre canonico, en las funciones
    que de verdad los consumen.

LO QUE NO SE UNIFICA, Y POR QUE

    La traduccion camelCase -> snake_case en la frontera del
    dashboard -`priceIncrement` a `price_increment`- es
    sistematica y publica UN solo nombre a cada lado. No es un
    concepto con dos nombres: es el mismo nombre en dos idiomas,
    y se entiende solo.
"""

from __future__ import annotations


# ============================================================
# EL REGISTRO
# ============================================================
#
# `unified` significa que las funciones que lo consumen entienden
# TODOS sus nombres. `incident` es la fecha en que costo algo.
CONCEPTOS = {
    "es_titular": {
        "canonical": "is_starter",
        "aliases": ("in_lineup",),
        "incident": "12/09/2026",
        "what": (
            "El portero titular no salia protegido porque la "
            "regla miraba `in_lineup` y el dashboard publicaba "
            "`is_starter`."
        ),
        "unified": True,
    },
    "partidos_jugados": {
        "canonical": "played_home/played_away",
        "aliases": ("playedHome/playedAway",),
        "incident": "22/09/2026",
        "what": (
            "La calidad medida son puntos por partido jugado. El "
            "motor tenia los partidos y la plantilla publicada "
            "no, asi que el tablero no podia reproducir el once "
            "del motor."
        ),
        "unified": True,
    },

    # --- Deuda declarada: viajan con dos nombres y todavia no
    # --- han costado nada. Se escriben para que no se olviden.
    "puntos_temporada_anterior": {
        "canonical": "points_last_season",
        "aliases": ("pointsLastSeason", "raw_points"),
        "incident": None,
        "what": (
            "Tres nombres para lo mismo. `raw_points` ademas "
            "PARECE puntos de esta temporada y no lo es: el "
            "20/09 lo divid por las jornadas jugadas y salio que "
            "Pedri hacia 70 puntos por jornada."
        ),
        "unified": False,
    },
    "subida_de_precio": {
        "canonical": "price_increment",
        "aliases": ("priceIncrement",),
        "incident": None,
        "what": (
            "Traduccion sistematica en la frontera del "
            "dashboard. Un solo nombre a cada lado."
        ),
        "unified": False,
    },
}


def _partes(nombre: str) -> tuple:
    return tuple(nombre.split("/"))


def leer(ficha: dict, concepto: str, default=None):
    """
    El valor de este concepto, se llame como se llame en la ficha.

    Nunca lanza. Devuelve `default` si no esta con ningun nombre.
    """

    try:
        registro = CONCEPTOS.get(concepto)

        if not registro or not isinstance(ficha, dict):
            return default

        nombres = [registro["canonical"], *registro["aliases"]]

        # Un concepto puede venir partido en varios campos
        # -partidos en casa y fuera-: entonces se suman.
        for nombre in nombres:

            campos = _partes(nombre)

            presentes = [
                ficha.get(c)
                for c in campos
                if ficha.get(c) is not None
            ]

            if not presentes:
                continue

            if len(campos) == 1:
                return presentes[0]

            try:
                return sum(int(v or 0) for v in presentes)
            except (TypeError, ValueError):
                return presentes[0]

        return default

    except Exception:                                # noqa: BLE001
        return default


def inventario() -> dict:
    """
    Los conceptos con mas de un nombre, y cuales estan cerrados.

    Forma fija.
    """

    filas = []

    for clave, registro in sorted(CONCEPTOS.items()):

        filas.append({
            "concept": clave,
            "canonical": registro["canonical"],
            "aliases": list(registro["aliases"]),
            "incident": registro["incident"],
            "what": registro["what"],
            "unified": registro["unified"],
        })

    cerrados = [f for f in filas if f["unified"]]
    abiertos = [f for f in filas if not f["unified"]]

    return {
        "available": True,
        "rows": filas,
        "unified": len(cerrados),
        "pending": len(abiertos),
        "reason": (
            f"{len(filas)} conceptos viajan con mas de un nombre. "
            f"{len(cerrados)} unificados -los que ya costaron un "
            f"incidente-, {len(abiertos)} en la lista y sin "
            f"tocar."
        ),
    }
