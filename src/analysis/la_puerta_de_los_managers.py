"""
La puerta de los managers: cuantas veces se ha cruzado de verdad.

LA PREGUNTA (14/09/2026)

    49 de los 69 objetivos del dia mueren en MERCADO_DE_RIVAL: el
    71 % de la lista. El motivo declarado es que la tasa de
    aceptacion de una oferta a otro manager NO ESTA MEDIDA.

    Se puede medir sin escribir nada y sin gastar un euro: los
    rivales llevan cinco semanas haciendose ofertas entre ellos y
    el tablon lo publica.

QUE DECIDE ESTE NUMERO

    Si en toda la liga no hay NI UN traspaso de manager a
    manager, la puerta no la cierra nuestro codigo: la cierra
    que en esta liga nadie le vende a nadie. Y entonces dejamos
    de gastar el 71 % de la lista mirando escaparates que no
    estan en venta.

    Si salen varios, la puerta funciona y somos los unicos que no
    llaman.

LO QUE SALIO (medido sobre los 301 eventos del tablon, del
09/08/2026 al 14/09/2026)

    8 traspasos de manager a manager en cinco semanas
    166 compras en el mercado del Computer

    Y PEPE ESTA EN CUATRO DE LOS OCHO: vendio tres veces
    (a Pollo17 dos y a Prinzipote una) y compro una
    (Cepeda, a Prinzipote, el 19/08 por 463.500).

    Asi que la puerta no esta cerrada, y no es teoria: ya la
    hemos cruzado cuatro veces.

    El ultimo fue el 04/09. La ventana de tres dias que se miro
    primero -17 compras al Computer, 13 ventas al Computer y cero
    traspasos- no decia nada: en tres dias caben cero traspasos
    de una via que se usa cada semana y pico.

LO QUE ESTE MODULO NO HACE

    NO OFRECE NADA A NADIE. Cuenta lo que ya paso. El
    experimento, si lo hay, lo autoriza el dueño.

EL PRECIO DE MERCADO, SOLO CUANDO SE PUEDE

    De los ocho traspasos, siete caen en el agujero de snapshots
    del 17/08 al 10/09 y no tienen precio con el que compararse.
    Se dice cuantos se pudieron medir en vez de rellenar los
    otros con el precio de hoy, que seria mirar el futuro.

REGLA 23

    No lee estado externo: los eventos, el buscador de precios y
    la hora llegan como argumentos.

DOCTRINA 50

    "Cuantos dias sin un traspaso" se mide contra la hora que
    entra por la puerta, no contra el reloj del proceso.
"""

from __future__ import annotations

from datetime import datetime, timezone


# Los tipos de evento del tablon que miramos, y por que.
#
#     `transfer` con `from` Y `to` es el traspaso entre managers:
#     el dinero va de un manager a otro.
#
#     `transfer` con `from` y sin `to` es una venta al Computer.
#     `market` es una subasta del Computer resuelta: el jugador
#     entra desde el mercado, no desde otro manager.
TRASPASO = "transfer"

SUBASTA = "market"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _momento(valor):
    """Una marca de tiempo con zona, o `None`. Nunca lanza."""

    if valor is None:
        return None

    if isinstance(valor, datetime):
        cuando = valor

    else:
        try:
            cuando = datetime.fromisoformat(str(valor))

        except (TypeError, ValueError):
            return None

    if cuando.tzinfo is None:
        return cuando.replace(tzinfo=timezone.utc)

    return cuando


def _fecha(epoch) -> str | None:
    try:
        return (
            datetime.fromtimestamp(
                safe_int(epoch), timezone.utc
            ).date().isoformat()
        )

    except (OSError, OverflowError, ValueError):
        return None


def traspasos_entre_managers(
    eventos: list | None,
    precio=None,
    mi_user_id=None,
    ahora=None,
) -> dict:
    """
    Cuantas veces se ha vendido un manager a otro, y por cuanto.

    Forma fija. Nunca lanza.

    EL TABLON REPITE EVENTOS

        Medido: el mismo traspaso llega dos veces con dos
        `event_id` distintos y el mismo contenido -uno con icono
        y otro sin el-. Contarlos por `event_id` daria de mas.
        Se deduplica por lo que identifica el hecho: fecha,
        jugador, quien vende, quien compra e importe.
    """

    vacio = {
        "available": False,
        "traspasos": [],
        "cuantos": 0,
        "nuestros": 0,
        "de_los_rivales": 0,
        "compras_al_computer": 0,
        "con_precio_de_mercado": 0,
        "primero": None,
        "ultimo": None,
        "dias_sin_traspaso": None,
        "eventos_leidos": 0,
        "puerta_cerrada": None,
        "reason": None,
    }

    try:
        filas = [
            e for e in (eventos or []) if isinstance(e, dict)
        ]

        if not filas:
            return {
                **vacio,
                "reason": (
                    "No llego ningun evento del tablon: sin "
                    "eventos no se puede decir si la puerta se "
                    "cruza o no."
                ),
            }

        mio = safe_int(mi_user_id)

        vistos = set()

        traspasos = []

        compras = 0

        for evento in filas:

            tipo = evento.get("type")

            contenido = evento.get("content")

            if not isinstance(contenido, list):
                continue

            cuando = safe_int(evento.get("date"))

            for item in contenido:

                if not isinstance(item, dict):
                    continue

                jugador = safe_int(item.get("player"))

                importe = safe_int(item.get("amount"))

                # `from` y `to` SOLO VALEN SI SON FICHAS.
                #
                #     Medido: hay eventos del tablon cuyo
                #     contenido trae estas claves como cadena.
                #     Tratarlas como diccionario reventaba el
                #     recuento entero -`'str' has no attribute
                #     get'- y la pantalla decia "no se pudo
                #     contar", que se lee igual que "cero".
                de = item.get("from")

                a = item.get("to")

                de = de if isinstance(de, dict) else None

                a = a if isinstance(a, dict) else None

                clave = (
                    tipo,
                    cuando,
                    jugador,
                    safe_int((de or {}).get("id")),
                    safe_int((a or {}).get("id")),
                    importe,
                )

                if clave in vistos:
                    continue

                vistos.add(clave)

                if tipo == SUBASTA and a:
                    compras += 1
                    continue

                if tipo != TRASPASO:
                    continue

                # LA PUERTA SE CRUZA CUANDO HAY DOS MANAGERS.
                #
                #     Con `from` y sin `to` es una venta al
                #     Computer, que es la via que ya usamos y no
                #     prueba nada sobre esta.
                if not (de and a):
                    continue

                de_id = safe_int(de.get("id"))

                a_id = safe_int(a.get("id"))

                mercado = (
                    safe_int(precio(jugador, cuando))
                    if callable(precio)
                    else 0
                )

                traspasos.append(
                    {
                        "fecha": _fecha(cuando),
                        "epoch": cuando,
                        "player_id": jugador,
                        "de": de.get("name"),
                        "de_id": de_id,
                        "a": a.get("name"),
                        "a_id": a_id,
                        "importe": importe,
                        "nuestro": bool(
                            mio and mio in (de_id, a_id)
                        ),
                        "vendimos": bool(mio and mio == de_id),

                        # EL PRECIO DE MERCADO, SI LO HAY.
                        #
                        #     Siete de los ocho caen en el agujero
                        #     de snapshots del 17/08 al 10/09. Se
                        #     dice que falta en vez de rellenarlo
                        #     con el precio de hoy, que seria
                        #     mirar el futuro.
                        "precio_de_mercado": mercado or None,
                        "sobre_el_mercado": (
                            round(importe / mercado, 3)
                            if mercado
                            else None
                        ),
                    }
                )

        traspasos.sort(key=lambda t: t["epoch"])

        nuestros = [t for t in traspasos if t["nuestro"]]

        con_precio = [
            t for t in traspasos if t["precio_de_mercado"]
        ]

        # CUANTO HACE DEL ULTIMO. La hora entra por la puerta: sin
        # ella no se dice un numero de dias, se dice que falta.
        referencia = _momento(ahora)

        dias_sin = None

        if traspasos and referencia is not None:

            ultimo = datetime.fromtimestamp(
                traspasos[-1]["epoch"], timezone.utc
            )

            dias_sin = max(
                0, int((referencia - ultimo).total_seconds() // 86400)
            )

        cerrada = not traspasos

        return {
            "available": True,
            "traspasos": traspasos,
            "cuantos": len(traspasos),
            "nuestros": len(nuestros),
            "de_los_rivales": len(traspasos) - len(nuestros),
            "compras_al_computer": compras,
            "con_precio_de_mercado": len(con_precio),
            "primero": traspasos[0]["fecha"] if traspasos else None,
            "ultimo": traspasos[-1]["fecha"] if traspasos else None,
            "dias_sin_traspaso": dias_sin,
            "eventos_leidos": len(filas),

            # LO QUE DECIDE ESTE NUMERO, dicho entero.
            "puerta_cerrada": cerrada,
            "reason": _el_veredicto(
                traspasos, nuestros, compras, len(filas), dias_sin
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo contar la puerta de los managers: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _el_veredicto(
    traspasos, nuestros, compras, eventos, dias_sin
) -> str:
    """
    Lo que significa el numero, no solo el numero.

    SE CUENTA, NO SE ESCRIBE (regla 18). El dia que aparezca el
    noveno traspaso esta frase lo dira sola.
    """

    if not traspasos:
        return (
            f"CERO traspasos de manager a manager en "
            f"{eventos} eventos del tablon, contra {compras} "
            f"compras en el mercado del Computer. La puerta no la "
            f"cierra nuestro codigo: en esta liga nadie le vende "
            f"a nadie."
        )

    cola = (
        f" El ultimo fue hace {dias_sin} dia(s)."
        if dias_sin is not None
        else ""
    )

    if nuestros:
        return (
            f"{len(traspasos)} traspaso(s) de manager a manager "
            f"en {eventos} eventos del tablon, contra {compras} "
            f"compras al Computer. La puerta NO esta cerrada, y "
            f"no es teoria: {len(nuestros)} de esos "
            f"{len(traspasos)} son nuestros." + cola
        )

    return (
        f"{len(traspasos)} traspaso(s) de manager a manager en "
        f"{eventos} eventos del tablon, contra {compras} compras "
        f"al Computer. La puerta funciona y somos los unicos que "
        f"no llaman." + cola
    )
