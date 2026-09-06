"""
El once que sale con la vara nueva, al lado del que salia antes.

LA RED QUE PIDIO EL ENCARGO (18/09/2026)

    Los factores por posicion se aplican esta noche sin fase
    observador. La contrapartida es que cada jornada se vean tres
    numeros juntos:

        lo que puntuo el once que alineamos
        lo que habria puntuado el once de la VARA VIEJA
        lo que habria puntuado el mejor once posible

    Con eso, en tres jornadas se sabe si los factores suman o
    restan. Se mira, no se discute.

QUE HACE ESTE MODULO Y QUE NO

    Elige el mejor once legal de una plantilla con una vara dada.
    Nada mas. No escribe en Biwenger, no decide fichajes y no
    toca el motor: el motor sigue siendo `lineup_engine`.

    Se usa para dos cosas:

        1. Enseñar hoy, jugador por jugador, en que se
           diferencian los dos onces.
        2. Anotar cada jornada el once de la vara vieja, para que
           dentro de tres se pueda comparar con puntos de verdad.

POR QUE NO LLAMA AL MOTOR ENTERO

    El motor necesita un snapshot vivo -disponibilidad, bajas,
    sanciones- y aqui basta con la plantilla ya publicada, que es
    la que se puede leer desde cualquier sitio y la que sale en el
    tablero.

    La regla de ordenacion es la MISMA: `weekly_expected_value`
    manda, y por debajo la probabilidad como desempate. Lo que
    esto no reproduce -el bono del Dios, las bajas- se dice en el
    resultado en vez de darlo por bueno.
"""

from __future__ import annotations

# Las mismas siete que evalua el motor. Si alli se añade una,
# aqui tiene que aparecer, o el "mejor once" quedaria por debajo
# de lo que se podia alinear de verdad.
FORMACIONES = {
    "3-4-3": {1: 1, 2: 3, 3: 4, 4: 3},
    "3-5-2": {1: 1, 2: 3, 3: 5, 4: 2},
    "4-3-3": {1: 1, 2: 4, 3: 3, 4: 3},
    "4-4-2": {1: 1, 2: 4, 3: 4, 4: 2},
    "4-5-1": {1: 1, 2: 4, 3: 5, 4: 1},
    "5-3-2": {1: 1, 2: 5, 3: 3, 4: 2},
    "5-4-1": {1: 1, 2: 5, 3: 4, 4: 1},
}


POSICIONES = {
    1: "Portero",
    2: "Defensa",
    3: "Medio",
    4: "Delantero",
}


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


def _vara(jugador: dict, con_factores: bool) -> float:
    """La vara del motor, con o sin el factor de posicion."""

    from src.analysis.lineup_engine import weekly_expected_value

    if not con_factores:
        return weekly_expected_value(
            jugador.get("hierarchy_value"),
            safe_float(jugador.get("starter_probability")),
        )

    return weekly_expected_value(
        jugador.get("hierarchy_value"),
        safe_float(jugador.get("starter_probability")),
        position=safe_int(jugador.get("position")),
    )


def elegir_once(
    plantilla: list,
    con_factores: bool = True,
) -> dict:
    """
    El mejor once legal de esta plantilla con esta vara.

    Nunca lanza. Si no cabe ninguna formacion, lo dice.
    """

    try:
        from src.analysis.position_factor import vara_plana

        contexto = (
            vara_plana()
            if not con_factores
            else _nada()
        )

        with contexto:

            valorados = []

            for jugador in (plantilla or []):

                posicion = safe_int(jugador.get("position"))

                if posicion not in POSICIONES:
                    continue

                valorados.append({
                    "id": safe_int(jugador.get("id")),
                    "name": jugador.get("name"),
                    "position": posicion,
                    "hierarchy": jugador.get("hierarchy"),
                    "starter_probability": safe_float(
                        jugador.get("starter_probability")
                    ),
                    "points": safe_int(jugador.get("points")),
                    "score": _vara(jugador, con_factores),
                })

        por_posicion = {p: [] for p in POSICIONES}

        for jugador in valorados:
            por_posicion[jugador["position"]].append(jugador)

        for posicion in por_posicion:
            # La vara manda; la probabilidad desempata, igual que
            # en el motor.
            por_posicion[posicion].sort(
                key=lambda j: (
                    -j["score"],
                    -(j["starter_probability"] or 0),
                    j["id"],
                )
            )

        mejor = None

        for nombre, cupos in FORMACIONES.items():

            elegidos = []
            cabe = True

            for posicion, cuantos in cupos.items():

                if len(por_posicion[posicion]) < cuantos:
                    cabe = False
                    break

                elegidos.extend(por_posicion[posicion][:cuantos])

            if not cabe:
                continue

            total = sum(j["score"] for j in elegidos)

            if mejor is None or total > mejor["score"]:
                mejor = {
                    "formation": nombre,
                    "score": total,
                    "players": elegidos,
                }

        if mejor is None:
            return {
                "available": False,
                "formation": None,
                "score": None,
                "players": [],
                "by_position": {},
                "with_factors": con_factores,
                "reason": (
                    "Ninguna formacion legal cabe en esta "
                    "plantilla."
                ),
            }

        reparto = {}

        for posicion, nombre in POSICIONES.items():
            reparto[nombre] = sum(
                1
                for j in mejor["players"]
                if j["position"] == posicion
            )

        return {
            "available": True,
            "formation": mejor["formation"],
            "score": round(mejor["score"], 4),
            "players": sorted(
                mejor["players"],
                key=lambda j: (j["position"], -j["score"]),
            ),
            "by_position": reparto,
            "with_factors": con_factores,
            "reason": None,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "formation": None,
            "score": None,
            "players": [],
            "by_position": {},
            "with_factors": con_factores,
            "reason": (
                f"No se pudo elegir el once: "
                f"{type(error).__name__}: {error}"
            ),
        }


class _nada:
    """Contexto que no hace nada, para no duplicar el `with`."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def comparar(plantilla: list) -> dict:
    """
    Los dos onces y en que se diferencian, jugador por jugador.

    Nunca lanza.
    """

    try:
        nueva = elegir_once(plantilla, con_factores=True)
        vieja = elegir_once(plantilla, con_factores=False)

        if not nueva["available"] or not vieja["available"]:
            return {
                "available": False,
            "new": nueva,
            "old": vieja,
            "changed": None,
            "formation_changed": None,
            "in": [],
            "out": [],
            "caveat": (
                "Reconstruido de la plantilla publicada, con la "
                "misma regla de orden que el motor."
            ),
                "reason": (
                    nueva.get("reason")
                    or vieja.get("reason")
                    or "No se pudo elegir ningun once legal."
                ),
            }

        en_nueva = {j["id"] for j in nueva["players"]}
        en_vieja = {j["id"] for j in vieja["players"]}

        ficha = {
            j["id"]: j
            for j in nueva["players"] + vieja["players"]
        }

        entran = [
            ficha[i]
            for i in sorted(en_nueva - en_vieja)
        ]

        salen = [
            ficha[i]
            for i in sorted(en_vieja - en_nueva)
        ]

        return {
            "available": True,
            "new": nueva,
            "old": vieja,

            "changed": bool(entran or salen)
            or nueva["formation"] != vieja["formation"],

            "in": sorted(entran, key=lambda j: -j["points"]),
            "out": sorted(salen, key=lambda j: -j["points"]),

            "formation_changed": (
                nueva["formation"] != vieja["formation"]
            ),

            "reason": _reason(nueva, vieja, entran, salen),

            "caveat": (
                "Reconstruido de la plantilla publicada, con la "
                "misma regla de orden que el motor. No reproduce "
                "el bono del Dios ni las bajas: para eso manda "
                "`lineup_engine`."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        vacio = {
            "available": False,
            "formation": None,
            "score": None,
            "players": [],
            "by_position": {},
            "with_factors": None,
            "reason": "No se pudo elegir el once.",
        }

        return {
            "available": False,
            "new": vacio,
            "old": vacio,
            "changed": None,
            "formation_changed": None,
            "in": [],
            "out": [],
            "caveat": (
                "Reconstruido de la plantilla publicada, con la "
                "misma regla de orden que el motor."
            ),
            "reason": (
                f"No se pudo comparar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(nueva, vieja, entran, salen) -> str:

    if not entran and not salen:

        if nueva["formation"] == vieja["formation"]:
            return (
                f"Los factores no cambian el once: sigue siendo "
                f"{nueva['formation']} con los mismos once."
            )

        return (
            f"Mismos once, otro dibujo: "
            f"{vieja['formation']} pasa a {nueva['formation']}."
        )

    cambios = []

    if entran:
        cambios.append(
            "entran " + ", ".join(j["name"] for j in entran)
        )

    if salen:
        cambios.append(
            "salen " + ", ".join(j["name"] for j in salen)
        )

    return (
        f"{vieja['formation']} pasa a {nueva['formation']}: "
        + "; ".join(cambios)
        + "."
    )
