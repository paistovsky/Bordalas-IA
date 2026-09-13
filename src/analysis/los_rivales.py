"""
Los rivales: puntos, plantilla y cuanto sacan por millon.

POR QUE HACE FALTA (13/09/2026)

    La clasificacion de la liga dice el puesto y los puntos. No
    dice lo unico que explica la diferencia entre dos managers
    con los mismos puntos: CUANTO LES CUESTA HACERLOS.

    Medido hoy: somos segundos en puntos (186) y segundos en
    puntos por millon (3,38). Por encima esta Alvaro Retamosa con
    3,94 — y no porque sea mejor, sino porque ha liquidado casi
    todo: nueve fichas y 24,9 M de plantilla. Un ratio alto con
    una plantilla minima no es eficiencia, es otra cosa.

    Sin el tamaño de plantilla al lado, ese 3,94 se leeria como
    "nos gana en gestion".

LOS PUESTOS SE CUENTAN, NO SE ESCRIBEN (regla 18)

    "Somos segundos en puntos por millon" tiene que salir de
    ordenar y buscarse. Escrito a mano fue exactamente el error
    que el dueño cometio en la primera version de la previa: puso
    primeros, y eramos segundos.

    Un numero de posicion escrito a mano es verdad el dia que se
    escribe y nadie vuelve a comprobarlo.

EL CRUCE, POR ID

    La clasificacion y el censo de plantillas se cruzan por
    `user_id`, no por nombre. Un manager que se cambie el nombre
    romperia el cruce y su fila saldria sin plantilla — y sin
    plantilla no hay puntos por millon.

ESTO NO DECIDE NADA. Es un cuadro para mirar.

REGLA 23

    No lee estado externo: clasificacion y censo llegan como
    argumentos.
"""

from __future__ import annotations


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _puesto_en(filas, clave, quien) -> int | None:
    """
    En que puesto queda `quien` ordenando por `clave`, de mayor a
    menor. `None` si no esta.

    SE CUENTA. Es la funcion que existe para que nadie escriba un
    "somos segundos" a mano.
    """

    ordenadas = sorted(
        filas, key=lambda f: -(f.get(clave) or 0)
    )

    for puesto, fila in enumerate(ordenadas, start=1):

        if fila is quien:
            return puesto

    return None


def los_rivales(
    clasificacion: list | None,
    plantillas: dict | None,
) -> dict:
    """
    Los ocho, con lo que sacan por millon. Forma fija.

    Nunca lanza. Sin clasificacion devuelve `available: False` y
    lo dice: un cuadro vacio se leeria como "no hay rivales".
    """

    vacio = {
        "available": False,
        "managers": [],
        "nosotros": None,
        "lectura": {},
        "sin_plantilla": [],
        "reason": None,
    }

    try:
        filas = [
            r
            for r in (clasificacion or [])
            if isinstance(r, dict)
        ]

        if not filas:
            return {
                **vacio,
                "reason": (
                    "No llegó la clasificación de la liga."
                ),
            }

        # EL CENSO, POR ID.
        equipos = [
            e
            for e in ((plantillas or {}).get("equipos") or [])
            if isinstance(e, dict)
        ]

        por_id = {
            safe_int(e.get("user_id")): e
            for e in equipos
            if safe_int(e.get("user_id"))
        }

        # Y NUESTRA FILA, que en el censo va sin id cuando el
        # tablon no lo trae: se busca por la marca `es_nuestra`.
        nuestra = next(
            (e for e in equipos if e.get("es_nuestra")), None
        )

        managers = []

        sin_plantilla = []

        for fila in filas:

            uid = safe_int(fila.get("user_id"))

            censo = por_id.get(uid)

            if censo is None and fila.get("is_us"):
                censo = nuestra

            valor = safe_int(fila.get("roster_value"))

            puntos = safe_int(fila.get("points"))

            fichas = (
                safe_int(censo.get("jugadores"))
                if censo
                else None
            )

            if censo is None:
                sin_plantilla.append(fila.get("name"))

            managers.append(
                {
                    "rank": safe_int(fila.get("rank")) or None,
                    "user_id": uid or None,
                    "name": fila.get("name"),
                    "icon": fila.get("icon"),
                    "is_us": bool(fila.get("is_us")),
                    "points": puntos,
                    "balance": safe_int(fila.get("balance")),
                    "roster_value": valor,
                    "net_worth": safe_int(fila.get("net_worth")),

                    # CUANTAS FICHAS. `None` es "no se pudo
                    # cruzar", que no es lo mismo que cero.
                    "fichas": fichas,

                    # PUNTOS POR MILLON. Sin valor de plantilla no
                    # se divide: un ratio con denominador cero
                    # seria infinito y se pintaria como el mejor.
                    "puntos_por_millon": (
                        round(puntos / (valor / 1_000_000), 2)
                        if valor > 0
                        else None
                    ),
                }
            )

        nosotros = next(
            (m for m in managers if m["is_us"]), None
        )

        # LA DIFERENCIA CON NOSOTROS, en puntos.
        if nosotros:
            for m in managers:
                m["vs_nosotros"] = (
                    m["points"] - nosotros["points"]
                )
        else:
            for m in managers:
                m["vs_nosotros"] = None

        managers.sort(key=lambda m: (m["rank"] or 99))

        return {
            "available": True,
            "managers": managers,
            "nosotros": nosotros,
            "sin_plantilla": sin_plantilla,
            "lectura": _la_lectura(managers, nosotros),
            "reason": (
                f"{len(managers)} managers"
                + (
                    f". {len(sin_plantilla)} sin plantilla "
                    f"cruzada: {', '.join(sin_plantilla)}."
                    if sin_plantilla
                    else "."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudieron montar los rivales: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _la_lectura(managers, nosotros) -> dict:
    """
    En que puesto estamos de cada cosa. TODO CONTADO.

    Ni un numero de posicion escrito: se ordena y se busca. Es la
    parte que el dueño se comio a mano en la primera version de
    la previa —puso que eramos primeros en puntos por millon y
    eramos segundos— y por eso existe esta funcion.
    """

    if not nosotros or not managers:
        return {
            "available": False,
            "reason": (
                "No se encontró nuestra fila en la "
                "clasificación: sin ella no hay con qué "
                "comparar."
            ),
        }

    con_ratio = [
        m for m in managers if m["puntos_por_millon"] is not None
    ]

    mejor = (
        max(con_ratio, key=lambda m: m["puntos_por_millon"])
        if con_ratio
        else None
    )

    con_fichas = [
        m for m in managers if m["fichas"] is not None
    ]

    return {
        "available": True,
        "total": len(managers),
        "por_puntos": _puesto_en(managers, "points", nosotros),
        "por_plantilla": (
            _puesto_en(con_fichas, "fichas", nosotros)
            if nosotros in con_fichas
            else None
        ),
        "por_millon": (
            _puesto_en(con_ratio, "puntos_por_millon", nosotros)
            if nosotros in con_ratio
            else None
        ),
        "mejor_por_millon": (
            {
                "name": mejor["name"],
                "puntos_por_millon": mejor["puntos_por_millon"],
                "fichas": mejor["fichas"],
                "roster_value": mejor["roster_value"],
                "es_nuestro": mejor["is_us"],
            }
            if mejor
            else None
        ),
    }
