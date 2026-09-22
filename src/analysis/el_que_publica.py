"""
El que publica: que salga la cola que ya esta calculada, y en su orden.

QUE PASA HOY (22/09/2026)

    Pepe decide bien y no ejecuta. Hay DOS motores que dicen a
    quien soltar y NINGUNO publica:

        `sale_intent`   propone `PUBLICAR_EN_MERCADO` y lo
                        imprime con la frase "OBSERVACION: no se
                        publica ni se vende nada".
        `sale_order`    ordena la cola entera, con el motivo de
                        cada puesto, y solo la llama la
                        telemetria.

    Y hay UN camino que SI publica: `LIST_FOR_LIQUIDITY`, del
    motor de solvencia. Ese no lee ninguna de las dos colas:
    publica `to_list[0]`, y `to_list` es la plantilla EN EL ORDEN
    EN QUE LA DEVUELVE BIWENGER, filtrada por "todavia no esta
    listado". No hay criterio: hay orden de llegada.

    De ahi sale lo que se ve en la foto: catorce publicados, diez
    de ellos del once, y el lastre sin publicar.

QUE HACE ESTE MODULO

    Coge la cola de `sale_order` —que ya lleva sus escalones, sus
    intocables, el suelo por posicion y el tope de concentracion—
    y la convierte en la lista de a quien publicar, EN SU ORDEN.

    NO REORDENA NADA. El unico criterio que anade es un CORTE:

        EL ONCE NO SE PUBLICA.

EL CORTE, Y POR QUE HACE FALTA AUNQUE LA COLA ESTE BIEN

    La cola de venta esta bien ordenada y aun asi TERMINA EN
    TITULARES: es una cola de VENDER, y vender al octavo de la
    cola es sensato. Publicar no es vender.

    Medido sobre las dos fotos que hay en el arbol:

        18/09   cola de 9   ->  puestos 8 y 9: Exposito y
                                Ruben Garcia, los dos en el once
        20/09   cola de 6   ->  puestos 5 y 6: los mismos dos

    Publicar a un titular INVITA a una oferta del Computer sobre
    el, y esa es la secuencia que el 22/09 acabo vendiendo a
    Oriol Rey. Asi que el once no entra en la cola de publicar,
    aunque si este en la de vender.

    `in_lineup` ya viaja en cada fila. No es un criterio nuevo:
    es el que la cola ya publica y nadie miraba al publicar.

EL INTERRUPTOR

    `BORDALAS_PUBLICAR_LA_COLA=1`. APAGADO de fabrica: sin el,
    `to_list` sale exactamente como hoy y no se publica a nadie
    distinto.

UNA ESCRITURA POR VUELTA, Y NO SE TOCA

    Esto no publica: ORDENA. Quien publica sigue siendo
    `LIST_FOR_LIQUIDITY`, con su prioridad y su cupo de una
    escritura por vuelta. Siete publicaciones siguen siendo siete
    vueltas.

NO LEE EL MUNDO

    Ni disco, ni red, ni reloj. Solo el entorno, que es lo que ES
    el interruptor. Forma fija. Nunca lanza.
"""

from __future__ import annotations


ENV = "BORDALAS_PUBLICAR_LA_COLA"


def activa() -> bool:
    """Si la cola manda al publicar. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        # Un interruptor que no se puede leer no cambia nada.
        return False


def es_del_once(fila) -> bool:
    """
    Si este jugador esta puesto en el once.

    Las dos formas del mismo dato: `in_lineup` en la cola de
    venta, `is_starter` en el roster de pantalla. Es el accidente
    del 12/09 con el portero titular, y por eso se miran las dos
    (doctrina 33).
    """

    if not isinstance(fila, dict):
        return False

    return bool(fila.get("in_lineup") or fila.get("is_starter"))


def _id(fila) -> int | None:

    try:
        valor = (fila or {}).get("id")

        return None if valor is None else int(valor)

    except (TypeError, ValueError, AttributeError):
        return None


def cola_de_publicacion(
    sale_order: dict | None,
    publicados=None,
) -> dict:
    """
    A quien publicar, en el orden de la cola de venta.

    `publicados` son los ids que YA estan en el mercado: no se
    republican. Si no se pasan, no se filtra por eso —"no se ha
    preguntado" no es "no hay ninguno" (doctrina 103)— y se dice
    en el motivo.

    Forma fija. Nunca lanza.
    """

    salida = {
        "available": False,
        "activa": False,
        "interruptor": ENV,
        "cola": [],
        "frenados": [],
        "sabemos_quien_esta_publicado": publicados is not None,
        "reason": None,
    }

    try:
        manda = activa()

        orden = sale_order if isinstance(sale_order, dict) else {}

        filas = [
            f for f in (orden.get("queue") or []) if isinstance(f, dict)
        ]

        if not orden.get("available") or not filas:
            return {
                **salida,
                "activa": manda,
                "reason": (
                    "No hay cola de venta que publicar: "
                    + str(
                        orden.get("reason")
                        or "la cola viene vacia."
                    )
                ),
            }

        ya = {
            int(x)
            for x in (publicados or [])
            if str(x).lstrip("-").isdigit()
        }

        cola = []
        frenados = []

        for fila in filas:

            if es_del_once(fila):
                frenados.append(
                    {
                        "id": _id(fila),
                        "name": fila.get("name"),
                        "order": fila.get("order"),
                        "motivo": "EL_ONCE_NO_SE_PUBLICA",
                        "reason": (
                            f"{fila.get('name')} esta en el once. "
                            f"Publicar a un titular invita a una "
                            f"oferta del Computer sobre el, y "
                            f"entonces la decision de venderlo la "
                            f"toma la oferta y no nosotros. Sigue "
                            f"en la cola de VENDER, que es otra "
                            f"cosa."
                        ),
                    }
                )
                continue

            if publicados is not None and _id(fila) in ya:
                frenados.append(
                    {
                        "id": _id(fila),
                        "name": fila.get("name"),
                        "order": fila.get("order"),
                        "motivo": "YA_ESTA_PUBLICADO",
                        "reason": (
                            f"{fila.get('name')} ya esta en el "
                            f"mercado: republicarlo seria gastar "
                            f"la escritura de la vuelta en nada."
                        ),
                    }
                )
                continue

            cola.append(fila)

        del_once = sum(
            1 for f in frenados if f["motivo"] == "EL_ONCE_NO_SE_PUBLICA"
        )

        return {
            **salida,
            "available": True,
            "activa": manda,
            "cola": cola,
            "frenados": frenados,
            "reason": (
                f"{len(cola)} para publicar, en el orden de la "
                f"cola de venta. {del_once} del once fuera"
                + (
                    f", {len(frenados) - del_once} ya publicados"
                    if len(frenados) > del_once
                    else ""
                )
                + "."
                + (
                    ""
                    if manda
                    else f" La cola NO manda todavia ({ENV} sin "
                    f"poner): esto se publica y no se ejecuta."
                )
                + (
                    ""
                    if publicados is not None
                    else " No se ha preguntado quien esta ya "
                    "publicado, asi que no se ha filtrado por eso."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo montar la cola de publicacion: "
                f"{type(error).__name__}: {error}"
            ),
        }


def orden_de_la_cola(sale_order: dict | None) -> dict:
    """
    {id del jugador: su puesto en la cola de publicacion}.

    Lo que hace falta para reordenar una lista que ya existe sin
    tocar su contenido.
    """

    salida = {}

    try:
        cola = cola_de_publicacion(sale_order)

        for puesto, fila in enumerate(cola.get("cola") or []):

            suyo = _id(fila)

            if suyo is not None:
                salida[suyo] = puesto

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def ordenar_para_publicar(
    to_list,
    sale_order: dict | None,
) -> dict:
    """
    `to_list` del motor de solvencia, puesto en el orden de la cola.

    LO QUE HACE, EXACTAMENTE

        Con el interruptor APAGADO devuelve `to_list` tal cual.
        Con el puesto:

            1. los que estan en el once salen fuera;
            2. el resto va en el orden de la cola de venta;
            3. y los que la cola no conoce van DETRAS, en su
               orden de siempre. No se tiran: no saber en que
               puesto va alguien no es motivo para no publicarlo
               nunca (doctrina 103).

    Forma fija. Nunca lanza.
    """

    original = [x for x in (to_list or []) if isinstance(x, dict)]

    salida = {
        "available": False,
        "activa": False,
        "interruptor": ENV,
        "to_list": list(original),
        "frenados": [],
        "sin_puesto": [],
        "reason": None,
    }

    try:
        if not activa():
            return {
                **salida,
                "available": True,
                "reason": (
                    f"La cola no manda ({ENV} sin poner): se "
                    f"publica en el orden de siempre."
                ),
            }

        cola = cola_de_publicacion(sale_order)

        if not cola.get("available"):
            # SIN COLA NO SE INVENTA UN ORDEN. Se deja el de hoy
            # y se dice por que, que es distinto de no pasar nada.
            return {
                **salida,
                "available": False,
                "activa": True,
                "reason": (
                    f"{ENV} puesto, pero no hay cola de venta que "
                    f"seguir: {cola.get('reason')} Se publica en "
                    f"el orden de siempre."
                ),
            }

        puestos = {}

        for puesto, fila in enumerate(cola.get("cola") or []):
            suyo = _id(fila)
            if suyo is not None:
                puestos[suyo] = puesto

        fuera = {
            f["id"]
            for f in (cola.get("frenados") or [])
            if f.get("motivo") == "EL_ONCE_NO_SE_PUBLICA"
            and f.get("id") is not None
        }

        frenados = []
        conocidos = []
        sin_puesto = []

        for posicion, fila in enumerate(original):

            suyo = _id(fila)

            if suyo in fuera or es_del_once(fila):
                frenados.append(
                    {
                        "id": suyo,
                        "name": fila.get("name"),
                        "motivo": "EL_ONCE_NO_SE_PUBLICA",
                    }
                )
                continue

            if suyo in puestos:
                conocidos.append((puestos[suyo], posicion, fila))
            else:
                sin_puesto.append((posicion, fila))

        conocidos.sort(key=lambda x: (x[0], x[1]))

        ordenada = [f for _, _, f in conocidos] + [
            f for _, f in sin_puesto
        ]

        return {
            **salida,
            "available": True,
            "activa": True,
            "to_list": ordenada,
            "frenados": frenados,
            "sin_puesto": [
                {"id": _id(f), "name": f.get("name")}
                for _, f in sin_puesto
            ],
            "reason": (
                f"{ENV} puesto: se publica en el orden de la cola "
                f"de venta. {len(frenados)} del once fuera, "
                f"{len(conocidos)} en su puesto"
                + (
                    f", {len(sin_puesto)} que la cola no conoce, "
                    f"detras"
                    if sin_puesto
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo ordenar la publicacion: "
                f"{type(error).__name__}: {error}"
            ),
        }
