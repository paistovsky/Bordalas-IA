"""
Cuando se publico un jugador POR PRIMERA VEZ.

POR QUE HAY QUE EMPEZARLO YA (10/09/2026)

    Renovar REESCRIBE la fecha del listado. Al re-listar, `date`
    pasa a ser el momento de la renovacion, y la fecha original
    desaparece.

    Se vio midiendo la pata de vuelta: hay ofertas del Computer
    con fecha ANTERIOR a la de su propio listado -mediana -0,2
    dias, minimo -1,6-, porque la oferta sobrevivio a una
    renovacion que le movio la fecha al listado.

    Consecuencia: no se puede contestar "¿cuanto lleva listado
    cuando llega la oferta?", que es una de las tres cosas de las
    que podria depender la prima de recompra.

    Y cada dia que pasa sin apuntarlo se destruye mas evidencia.
    Por eso esto empieza hoy, aunque la respuesta tarde semanas.

QUE APUNTA, Y QUE NO

    La PRIMERA vez que se ve a un jugador listado, y nada mas.
    Las renovaciones posteriores no lo tocan: ese es todo el
    punto.

    Si un jugador sale del mercado y vuelve a entrar dias
    despues, se apunta como una publicacion NUEVA -es otra cosa
    distinta- y se guarda el historial entero.

ESTE MODULO NO DECIDE NADA

    Es un cuaderno. Ninguna ruta lo lee para decidir. Lo unico
    que se pierde si desaparece es el estudio.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


FICHERO = (
    Path("data") / "intelligence" / "libro_de_publicacion.jsonl"
)


# Si un jugador desaparece del mercado mas de esto y vuelve, se
# considera una publicacion nueva y no una renovacion.
#
# Es la vida de un listado: 48 h exactas, medidas sobre 47 de 47
# observaciones el 10/09. Por debajo de eso, que desaparezca de
# una foto es un hueco de la foto, no una salida del mercado.
HORAS_QUE_DURA_UN_LISTADO = 48.0


ENTRADAS_QUE_SE_GUARDAN = 2000


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _leer(ruta: Path) -> list:
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except Exception:                               # noqa: BLE001
        return []

    filas = []

    for linea in lineas:

        linea = linea.strip()

        if not linea:
            continue

        try:
            fila = json.loads(linea)
        except Exception:                           # noqa: BLE001
            continue

        if isinstance(fila, dict):
            filas.append(fila)

    return filas


def apuntar_publicaciones(
    listados: list | None,
    at: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Apunta a los que se ven listados y NO estaban ya apuntados.

    Cada fila de `listados` necesita `id` y, si se sabe, `name`
    y `price`.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "new": 0,
        "known": 0,
        "reason": None,
    }

    try:
        destino = ruta or FICHERO

        momento = at or _ahora()

        anteriores = _leer(destino)

        # El ultimo apunte de cada jugador, para saber si esto es
        # una publicacion nueva o el mismo listado de siempre.
        ultimo = {}

        for fila in anteriores:
            ultimo[safe_int(fila.get("player_id"))] = fila

        ahora_dt = datetime.fromisoformat(str(momento))

        if ahora_dt.tzinfo is None:
            ahora_dt = ahora_dt.replace(tzinfo=timezone.utc)

        nuevas = []

        conocidos = 0

        for item in (listados or []):

            if not isinstance(item, dict):
                continue

            pid = safe_int(item.get("id"))

            if not pid:
                continue

            previo = ultimo.get(pid)

            if previo:

                try:
                    visto = datetime.fromisoformat(
                        str(previo.get("last_seen") or previo.get("at"))
                    )

                    if visto.tzinfo is None:
                        visto = visto.replace(tzinfo=timezone.utc)

                    horas = (
                        ahora_dt - visto
                    ).total_seconds() / 3600.0

                except Exception:                   # noqa: BLE001
                    horas = 0.0

                if horas <= HORAS_QUE_DURA_UN_LISTADO:
                    # Sigue siendo la misma publicacion. Solo se
                    # refresca cuando se le vio por ultima vez.
                    previo["last_seen"] = momento
                    conocidos += 1
                    continue

            nuevas.append(
                {
                    "player_id": pid,
                    "player_name": item.get("name"),
                    "first_listed_at": momento,
                    "last_seen": momento,
                    "price_at_listing": safe_int(
                        item.get("price")
                    ),
                    "listed_price": safe_int(
                        item.get("listed_price")
                    ),
                }
            )

        if not nuevas and not conocidos:
            return {
                **vacio,
                "available": True,
                "reason": "No hay listados que apuntar.",
            }

        destino.parent.mkdir(parents=True, exist_ok=True)

        filas = anteriores + nuevas

        destino.write_text(
            "\n".join(
                json.dumps(f, ensure_ascii=False)
                for f in filas[-ENTRADAS_QUE_SE_GUARDAN:]
            )
            + "\n",
            encoding="utf-8",
        )

        return {
            "available": True,
            "new": len(nuevas),
            "known": conocidos,
            "reason": (
                f"{len(nuevas)} publicacion(es) nueva(s) "
                f"apuntadas, {conocidos} ya conocidas."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo apuntar la publicacion: "
                f"{type(error).__name__}: {error}"
            ),
        }


def desde_cuando(player_id, ruta: Path | None = None):
    """
    Cuando se publico por primera vez, o None si no consta.

    Es lo unico que este libro sirve, y lo unico que la fecha
    del listado ya no puede decir.
    """

    pid = safe_int(player_id)

    filas = [
        f
        for f in _leer(ruta or FICHERO)
        if safe_int(f.get("player_id")) == pid
    ]

    return filas[-1].get("first_listed_at") if filas else None


def resumen(ruta: Path | None = None) -> dict:
    """Cuantas publicaciones lleva apuntadas. Forma fija."""

    filas = _leer(ruta or FICHERO)

    return {
        "available": bool(filas),
        "publications": len(filas),
        "players": len(
            {safe_int(f.get("player_id")) for f in filas}
        ),
        "reason": (
            f"{len(filas)} publicacion(es) apuntadas."
            if filas
            else (
                "Todavia no hay ninguna publicacion apuntada. "
                "Empieza hoy."
            )
        ),
    }
