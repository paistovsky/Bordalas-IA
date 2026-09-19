"""
Cada escritura deja rastro.

LO QUE NO DEJA RASTRO NO SE PUEDE MEDIR

    Al desglosar el desperdicio de escrituras del 19/09 salieron
    tres familias con una raya en vez de un numero:

        aceptar oferta      no escribe libro
        reroll              no escribe libro
        guardar alineacion  no escribe libro

    No es que no repitan: es que no me consta, y poner un cero
    ahi habria sido inventarse una medida (doctrina 55). Las
    otras tres —puja, publicar, renovar— se pudieron medir
    justamente porque llevan libro: `sent`, `http_status` y la
    hora.

    Y una de las tres mudas es la que la regla del deficit va a
    usar en cuanto se encienda `BORDALAS_COBRAR_EN_DEFICIT`.
    Encenderla sin rastro seria repetir el error de la semana:
    descubrir el desperdicio quince dias despues.

LA CLAVE ES `event_id`, NO LA MARCA DE TIEMPO

    Ya nos ha mordido dos veces:

        la reja del tablon      (tipo, FECHA, jugador, de, a, importe)
        el libro de pujas       `player_id:placed_at`

    Las dos veces la fecha dentro de la clave convirtio una
    operacion en muchas. Aqui la identidad de la operacion es su
    `event_id` —el que devuelve Biwenger— y la hora viaja al
    lado, en `at`, donde no manda.

    Cuando Biwenger no devuelve id —una alineacion guardada no
    lo trae— la identidad es la huella del contenido, no el
    reloj: un `sha` corto de lo que se envio. Dos guardados
    identicos son el mismo hecho; uno con otra formacion es
    otro.

QUE NO HACE ESTO

    No decide, no frena y no mira el reloj para nada que no sea
    sellar la fila. Solo escribe. El que frena es
    `filtrar_los_repetidos`, y el que cuenta es
    `el_cupo_de_las_escrituras`.
"""

from __future__ import annotations

import hashlib
import json

from datetime import datetime, timezone
from pathlib import Path


from src.analysis.el_cupo_de_las_escrituras import (
    LIBROS_POR_FAMILIA,
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return default


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def huella(contenido) -> str:
    """
    La identidad de lo que se envio, cuando Biwenger no da id.

    Del CONTENIDO, nunca del reloj: dos envios identicos son el
    mismo hecho y tienen que colapsar.
    """

    crudo = json.dumps(
        contenido,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        crudo.encode("utf-8")
    ).hexdigest()[:16]


def identidad_de_la_escritura(
    resultado: dict | None,
    contenido=None,
) -> str:
    """
    El `event_id` de esta escritura.

    Primero lo que diga Biwenger; si no dice nada, la huella del
    contenido. Nunca la hora.
    """

    datos = resultado if isinstance(resultado, dict) else {}

    cuerpo = datos.get("data")

    if isinstance(cuerpo, dict):

        for campo in ("id", "offer_id", "event_id"):

            if cuerpo.get(campo):
                return str(cuerpo[campo])

    for campo in ("id", "offer_id", "event_id"):

        if datos.get(campo):
            return str(datos[campo])

    return huella(contenido if contenido is not None else datos)


def apuntar_escritura(
    familia: str,
    *,
    resultado: dict | None = None,
    player_id=None,
    player_name: str | None = None,
    amount=None,
    contenido=None,
    extra: dict | None = None,
    ruta: Path | None = None,
    at: str | None = None,
) -> dict:
    """
    Anota una escritura contra Biwenger. Forma fija, nunca lanza.

    La misma forma que los libros que ya existen —`at`, `sent`,
    `http_status`, `success`, `response`— mas `event_id`, que es
    la identidad de la operacion.

    Devuelve la fila escrita, o la fila con `anotada: False` y el
    motivo. Una escritura ya confirmada por Biwenger NO puede
    caerse por un fallo apuntandola.
    """

    datos = resultado if isinstance(resultado, dict) else {}

    fila = {
        "at": at or _ahora(),
        "familia": familia,
        "event_id": identidad_de_la_escritura(
            datos, contenido
        ),
        "player_id": safe_int(player_id),
        "player_name": player_name,
        "amount": safe_int(amount),
        "sent": bool(datos.get("sent", datos.get("success"))),
        "success": bool(datos.get("success")),
        "http_status": datos.get("http_status"),
        "response": datos.get("response", datos.get("data")),
        **(extra or {}),
    }

    destino = ruta or LIBROS_POR_FAMILIA.get(familia)

    if destino is None:
        return {
            **fila,
            "anotada": False,
            "reason": (
                f"La familia «{familia}» no tiene libro "
                f"declarado."
            ),
        }

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        with open(destino, "a", encoding="utf-8") as fichero:
            fichero.write(
                json.dumps(fila, ensure_ascii=False) + "\n"
            )

        return {**fila, "anotada": True, "reason": None}

    except Exception as error:                      # noqa: BLE001
        return {
            **fila,
            "anotada": False,
            "reason": (
                f"No se pudo anotar la escritura de «{familia}»: "
                f"{type(error).__name__}: {error}"
            ),
        }
