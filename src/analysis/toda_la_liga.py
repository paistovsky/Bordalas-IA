"""
Los 570 jugadores de la liga, y cuanto nos mejoraria cada uno.

POR QUE HACE FALTA (13/09/2026)

    El cuadro de objetivos enseña lo que hay HOY en el mercado:
    sesenta filas. Es la caja registradora.

    Falta la lista de la compra. Un jugador libre que el Computer
    no ha sacado hoy no existe en ninguna parte de la cabeza de
    Pepe — medido: de once "chollos" publicados sin dueño, CERO
    menciones en toda la foto.

LA VARA: NOS SUMA

    Los puntos del jugador menos los del PEOR TITULAR NUESTRO en
    su posicion. Misma vara para las cuatro, y sale de puntos YA
    JUGADOS, no de un pronostico.

    El 13/09 la vara era:

        POR  Dituro    4        MED  Mangala  13
        DEF  Djene     7        DEL  Jutgla   14

    Un delantero de 30 puntos suma +16.

ESTO NO DECIDE NADA

    Es una lista para mirar. Ninguna puja sale de aqui. Cuando el
    dueño la haya visto y diga que tiene sentido, se hablara de
    usarla.

UN NUMERO SIN RESPALDO, Y SE DICE

    El corte de "chollo" en 6 puntos por millon lo puso el dueño
    a ojo para la previa. NO ESTA MEDIDO. Queda escrito como tal
    hasta que se mida.
"""

from __future__ import annotations


# El corte de "chollo". SIN MEDIR: puesto a ojo el 13/09/2026
# para la previa del diseño. No es un umbral calibrado y no
# decide nada — solo pone una etiqueta en una lista de mirar.
PUNTOS_POR_MILLON_CHOLLO = 6.0

# Por debajo de esto, un jugador no ha jugado lo suficiente para
# que sus puntos digan nada.
PARTIDOS_PARA_JUZGAR = 3

PARTIDOS_PARA_CHOLLO = 4

POSICIONES = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}

# El orden de las etiquetas es el orden del cuadro.
ETIQUETAS = (
    "MEJORA EL ONCE · pujable hoy",
    "mejora el once · libre",
    "mejora el once · lo tiene un rival",
    "chollo · muchos puntos por euro",
    "para revender",
    "sin interés",
    "no juega",
    "no disponible",
    "ya es nuestro",
)

ESCALON = {
    "MEJORA EL ONCE · pujable hoy": 0,
    "mejora el once · libre": 1,
    "mejora el once · lo tiene un rival": 2,
    "chollo · muchos puntos por euro": 3,
    "para revender": 5,
    "sin interés": 6,
    "no juega": 7,
    "no disponible": 8,
    "ya es nuestro": 9,
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def la_vara(once: list | None, catalogo: dict | None) -> dict:
    """
    El PEOR titular nuestro en cada posicion, con sus puntos.

    Devuelve `{posicion: {"player_id", "name", "points"}}`.

    Sin once NO se inventa una vara: se devuelve `{}` y quien
    llame se abstiene de restar. Una vara inventada convierte
    "nos suma" en cualquier cosa.
    """

    vara = {}

    try:
        for jugador in once or []:

            if not isinstance(jugador, dict):
                continue

            pid = safe_int(jugador.get("id"))

            ficha = (catalogo or {}).get(pid) or {}

            posicion = safe_int(
                jugador.get("position") or ficha.get("position")
            )

            if posicion <= 0:
                continue

            puntos = safe_int(
                ficha.get("points")
                if ficha.get("points") is not None
                else jugador.get("points")
            )

            anterior = vara.get(posicion)

            if anterior is None or puntos < anterior["points"]:
                vara[posicion] = {
                    "player_id": pid,
                    "name": (
                        jugador.get("name") or ficha.get("name")
                    ),
                    "points": puntos,
                }

        return vara

    except Exception:                               # noqa: BLE001
        return {}


def _de_quien_es(pid, nuestros, del_computer, de_rivales):
    if pid in nuestros:
        return "nuestro"

    if pid in del_computer:
        return "computer"

    if pid in de_rivales:
        return "rival"

    return "libre"


def _etiqueta(fila) -> str:
    """
    A que grupo va. Nunca vacia, y en este orden.

    El orden importa: "no disponible" gana a "mejora el once"
    porque un lesionado no mejora nada, y "ya es nuestro" gana a
    todo porque no hay nada que decidir.
    """

    if fila["de_quien"] == "nuestro":
        return "ya es nuestro"

    if str(fila.get("status") or "").lower() in (
        "injured",
        "sanctioned",
    ):
        return "no disponible"

    if fila["played"] < PARTIDOS_PARA_JUZGAR:
        return "no juega"

    suma = fila.get("nos_suma")

    if suma is not None and suma > 0:

        if fila["de_quien"] == "computer":
            return "MEJORA EL ONCE · pujable hoy"

        if fila["de_quien"] == "libre":
            return "mejora el once · libre"

        return "mejora el once · lo tiene un rival"

    if (
        fila.get("puntos_por_millon") is not None
        and fila["puntos_por_millon"]
        >= PUNTOS_POR_MILLON_CHOLLO
        and fila["played"] >= PARTIDOS_PARA_CHOLLO
    ):
        return "chollo · muchos puntos por euro"

    if fila["de_quien"] == "computer":
        return "para revender"

    return "sin interés"


def toda_la_liga(
    catalogo: dict | None,
    once: list | None,
    nuestra_plantilla: list | None,
    managers: list | None,
    en_el_mercado: set | None = None,
) -> dict:
    """
    Los 570, con su etiqueta y lo que nos sumarian. Forma fija.

    Nunca lanza. Si falta el catalogo o el once, devuelve
    `available: False` y lo dice: sin vara no hay "nos suma", y
    una vara inventada haria de esta lista un adorno.
    """

    vacio = {
        "available": False,
        "players": [],
        "vara": {},
        "recuento": {},
        "total": 0,
        "chollo_sin_medir": PUNTOS_POR_MILLON_CHOLLO,
        "reason": None,
    }

    try:
        if not catalogo:
            return {
                **vacio,
                "reason": (
                    "Sin catalogo no hay liga que mirar."
                ),
            }

        vara = la_vara(once, catalogo)

        if not vara:
            return {
                **vacio,
                "reason": (
                    "Sin el once no se puede saber a quien "
                    "mejora nadie: la vara es el peor titular de "
                    "cada posicion, y sin ella «nos suma» seria "
                    "un numero inventado."
                ),
            }

        nuestros = {
            safe_int(j.get("id"))
            for j in (nuestra_plantilla or [])
            if isinstance(j, dict)
        }

        de_rivales = set()

        for manager in managers or []:

            if not isinstance(manager, dict):
                continue

            for jugador in manager.get("roster") or []:

                pid = safe_int(
                    jugador.get("id")
                    if isinstance(jugador, dict)
                    else jugador
                )

                if pid and pid not in nuestros:
                    de_rivales.add(pid)

        del_computer = set(en_el_mercado or set())

        filas = []

        for pid, ficha in (catalogo or {}).items():

            if not isinstance(ficha, dict):
                continue

            posicion = safe_int(ficha.get("position"))

            precio = safe_int(ficha.get("price"))

            puntos = safe_int(ficha.get("points"))

            jugados = safe_int(
                ficha.get("playedHome")
            ) + safe_int(ficha.get("playedAway"))

            referencia = vara.get(posicion)

            fila = {
                "id": safe_int(pid),
                "name": ficha.get("name"),
                "position": posicion,
                "team_id": safe_int(ficha.get("teamID")) or None,
                "status": ficha.get("status"),
                "points": puntos,
                "played": jugados,
                "price": precio,
                "price_increment": safe_int(
                    ficha.get("priceIncrement")
                ),
                "puntos_por_millon": (
                    round(puntos / (precio / 1_000_000), 1)
                    if precio > 0
                    else None
                ),
                "de_quien": _de_quien_es(
                    safe_int(pid),
                    nuestros,
                    del_computer,
                    de_rivales,
                ),
                # LA VARA, con nombre. Sin referencia de su
                # posicion no se resta: `None`, y se dice.
                "nos_suma": (
                    puntos - referencia["points"]
                    if referencia
                    else None
                ),
                "vara_nombre": (
                    referencia["name"] if referencia else None
                ),
                "vara_puntos": (
                    referencia["points"] if referencia else None
                ),
            }

            fila["etiqueta"] = _etiqueta(fila)

            fila["escalon"] = ESCALON.get(fila["etiqueta"], 9)

            filas.append(fila)

        # Dentro de cada escalon: por lo que nos suma, y luego
        # por puntos por millon.
        filas.sort(
            key=lambda f: (
                f["escalon"],
                -(f["nos_suma"] or 0),
                -(f["puntos_por_millon"] or 0),
            )
        )

        recuento = {}

        for fila in filas:
            recuento[fila["etiqueta"]] = (
                recuento.get(fila["etiqueta"], 0) + 1
            )

        return {
            "available": True,
            "players": filas,
            "vara": {
                POSICIONES.get(pos, str(pos)): dato
                for pos, dato in vara.items()
            },
            "recuento": recuento,
            "total": len(filas),
            "chollo_sin_medir": PUNTOS_POR_MILLON_CHOLLO,
            "reason": (
                f"{len(filas)} jugadores del catalogo, medidos "
                f"contra el peor titular de cada posicion. El "
                f"corte de chollo ({PUNTOS_POR_MILLON_CHOLLO} "
                f"pts/M) NO esta medido: se puso a ojo."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar la liga entera: "
                f"{type(error).__name__}: {error}"
            ),
        }
