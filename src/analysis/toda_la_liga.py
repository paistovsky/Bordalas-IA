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

# LAS ETIQUETAS, Y EL ORDEN DEL CUADRO (13/09/2026, noche)
#
#     ESTAR HOY EN EL MERCADO DEJO DE ORDENAR.
#
#     La primera version ponia arriba "nos suma Y esta en el
#     mercado del Computer". El dueño lo vio y dijo que no:
#
#         "que no sean primero los que estan hoy en el mercado.
#          Quiero que Pepe me diga cual es el que mas le interesa
#          por CALIDAD-PRECIO y ese este el primero."
#
#     Donde esta pasa a ser una columna informativa. Lo que
#     ordena es cuanto nos añade por cada millon que cuesta:
#
#         calidad_precio = nos_suma / (precio / 1.000.000)
ETIQUETAS = (
    "nos mejora",
    "chollo · muchos puntos por euro",
    "sin interés",
    "no disponible",
    "ya es nuestro",
)

ESCALON = {
    "nos mejora": 0,
    "chollo · muchos puntos por euro": 1,
    "sin interés": 2,
    "no disponible": 3,
    "ya es nuestro": 4,
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


def _las_ocho_plantillas(
    catalogo, nuestros, managers, nuestro_id=None
) -> dict:
    """
    CUANTOS JUGADORES TRAE CADA PLANTILLA. Publicado, no deducido.

    SINTOMA (13/09/2026)

        El recuento del cuadro daba mas "libres" de los que
        parecian razonables. Una plantilla que llega vacia —o a
        medias— no se nota en ninguna parte: sus jugadores pasan
        a contarse como LIBRES, y un libre es alguien a quien se
        puede fichar.

    CONSECUENCIA

        Pepe recomendaria pujar por un jugador que ya tiene
        dueño. No falla nada: la lista queda MAL Y CALLADA.

    LA CUENTA QUE TIENE QUE CUADRAR

        los de cada plantilla + los libres = el catalogo entero

    `cuadra` dice si sale. Si no sale, la diferencia va publicada
    en `descuadre` para que se vea el numero, no la sospecha.

    Forma fija. Nunca lanza.
    """

    try:
        equipos = []

        vistos = set(nuestros)

        equipos.append(
            {
                "nombre": "Pepe Bordalás",
                # EL ID, PARA CRUZAR POR NUMERO Y NO POR TEXTO.
                #
                #     La clasificacion de la liga y este censo se
                #     cruzan en el cuadro de rivales. Por nombre
                #     funciona hasta que alguien se cambia el
                #     suyo; el id no cambia nunca.
                "user_id": safe_int(nuestro_id) or None,
                "es_nuestra": True,
                "jugadores": len(nuestros),
            }
        )

        for manager in managers or []:

            if not isinstance(manager, dict):
                continue

            suyos = set()

            for jugador in manager.get("roster") or []:

                pid = safe_int(
                    jugador.get("id")
                    if isinstance(jugador, dict)
                    else jugador
                )

                if pid:
                    suyos.add(pid)

            vistos |= suyos

            equipos.append(
                {
                    "nombre": (
                        manager.get("name")
                        or manager.get("manager")
                        or "sin nombre"
                    ),
                    "user_id": (
                        safe_int(manager.get("user_id")) or None
                    ),
                    "es_nuestra": False,
                    "jugadores": len(suyos),
                }
            )

        # LOS TRES NUMEROS SE CUENTAN POR SEPARADO.
        #
        #     La primera version sacaba `libres` restando —
        #     `total - con_dueño`— y entonces la suma cuadraba
        #     SIEMPRE. Una cuenta que no puede fallar no
        #     comprueba nada.
        #
        #     Contados aparte, el descuadre aparece cuando un
        #     jugador esta en dos plantillas o cuando una
        #     plantilla trae a alguien que no esta en el
        #     catalogo.
        del_catalogo = {
            safe_int(pid)
            for pid, ficha in (catalogo or {}).items()
            if isinstance(ficha, dict)
        }

        total = len(del_catalogo)

        con_dueño = len(vistos & del_catalogo)

        libres = len(del_catalogo - vistos)

        suma = sum(e["jugadores"] for e in equipos)

        return {
            "equipos": equipos,
            "suma_de_las_plantillas": suma,
            "con_dueño": con_dueño,
            "libres": libres,
            "total": total,
            "vacias": [
                e["nombre"] for e in equipos if not e["jugadores"]
            ],
            "cuadra": (
                suma == con_dueño
                and con_dueño + libres == total
            ),
            # Positivo: alguien contado dos veces, o un jugador de
            # plantilla que no esta en el catalogo.
            "descuadre": suma - con_dueño,
        }

    except Exception:                               # noqa: BLE001
        return {
            "equipos": [],
            "suma_de_las_plantillas": 0,
            "con_dueño": 0,
            "libres": 0,
            "total": 0,
            "vacias": [],
            "cuadra": False,
            "descuadre": 0,
        }


def _etiqueta(fila) -> str:
    """
    A que grupo va. Nunca vacia, y en este orden.

    El orden importa: "no disponible" gana a "nos mejora" —un
    lesionado no mejora nada— y "ya es nuestro" gana a todo,
    porque no hay nada que decidir.

    DONDE ESTA NO ENTRA AQUI. Estar hoy en el mercado del
    Computer es una columna informativa, no un escalon.
    """

    if fila["de_quien"] == "nuestro":
        return "ya es nuestro"

    if str(fila.get("status") or "").lower() in (
        "injured",
        "sanctioned",
    ) or fila["played"] < PARTIDOS_PARA_JUZGAR:
        return "no disponible"

    if (fila.get("nos_suma") or 0) > 0:
        return "nos mejora"

    if (
        fila.get("puntos_por_millon") is not None
        and fila["puntos_por_millon"]
        >= PUNTOS_POR_MILLON_CHOLLO
        and fila["played"] >= PARTIDOS_PARA_CHOLLO
    ):
        return "chollo · muchos puntos por euro"

    return "sin interés"


def toda_la_liga(
    catalogo: dict | None,
    once: list | None,
    nuestra_plantilla: list | None,
    managers: list | None,
    en_el_mercado: set | None = None,
    nuestro_id=None,
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
        "plantillas": {},
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

        plantillas = _las_ocho_plantillas(
            catalogo, nuestros, managers, nuestro_id
        )

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

            # CALIDAD-PRECIO: lo que nos añade por cada millon.
            #
            #     Es lo que ordena el cuadro desde el 13/09 por
            #     la noche. Solo tiene sentido cuando NOS SUMA:
            #     dividir un numero negativo entre el precio
            #     ordena por "cual nos empeora menos por euro",
            #     que no es una pregunta que nadie haga.
            fila["calidad_precio"] = (
                round(
                    fila["nos_suma"] / (precio / 1_000_000), 1
                )
                if fila["nos_suma"] is not None
                and fila["nos_suma"] > 0
                and precio > 0
                else None
            )

            fila["etiqueta"] = _etiqueta(fila)

            fila["escalon"] = ESCALON.get(fila["etiqueta"], 9)

            filas.append(fila)

        # DENTRO DE CADA ESCALON
        #
        #     El de los que nos mejoran, por CALIDAD-PRECIO. Los
        #     demas por puntos por millon, que es lo unico que
        #     los separa: si no nos suman, "cuanto nos añade por
        #     euro" no existe.
        filas.sort(
            key=lambda f: (
                f["escalon"],
                -(f["calidad_precio"] or 0),
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
            "plantillas": plantillas,
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
