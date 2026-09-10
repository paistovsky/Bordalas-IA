"""
El libro de la ventana: cuando se entro por ultima vez y que se
hizo alli.

POR QUE EXISTE (10/09/2026)

    La ventana del reset no se abrio NUNCA. El cron externo
    disparaba una hora tarde -CET en vez de CEST- y el plan
    contestaba `FUERA_DE_VENTANA`.

    Y esa frase es la misma que sale el resto del dia. Una
    capacidad que no se dispara jamas era **indistinguible de una
    noche normal**: no habia forma de notar la ausencia mirando
    la pantalla.

    Dos semanas midiendo y cero pujas, y el motivo estaba a la
    vista sin que nadie pudiera verlo.

LA REGLA

    **Una capacidad que nunca se dispara tiene que anunciar su
    propia ausencia.**

    Se apunta cada entrada en la ventana con lo que se hizo, y se
    publica cuanto hace de la ultima. Pasadas 24 HORAS sin
    entrar, sale en ROJO.

POR QUE 24 HORAS Y NO OTRA COSA

    No es un umbral elegido: es el periodo. El reset es diario,
    asi que la ventana se abre una vez al dia. Dos dias sin
    entrar no es "poco trafico": es que algo esta roto.

    Se da el dia entero de margen porque la ventana de un dia
    puede caer justo despues de mirar la pantalla del anterior.

LA PARTE QUE DECIDE NO LEE EL MUNDO

    `estado_de_la_ventana` es pura: se le pasan la ultima
    anotacion y la hora. Quien toca disco es este modulo, que es
    un almacen. Todas las funciones aceptan `ruta` para poder
    probarlas sin escribir en `data/`.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


FICHERO = Path("data") / "trading" / "libro_de_la_ventana.jsonl"


# El periodo del reset. No es un umbral: la ventana se abre una
# vez al dia porque el reset es diario.
HORAS_SIN_ENTRAR_QUE_SON_ROJO = 24.0


ENTRADAS_QUE_SE_GUARDAN = 400


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


def apuntar_ventana(
    seconds_to_reset=None,
    bids: int = 0,
    renewals: int = 0,
    trigger: str | None = None,
    executed: bool = False,
    at: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Una linea cada vez que se ENTRA en la ventana.

    Se apunta aunque no se haya hecho nada: "entre y no habia
    trabajo" es informacion, y muy distinta de "no entre".
    """

    fila = {
        "at": at or _ahora(),
        "seconds_to_reset": safe_int(seconds_to_reset),
        "bids": safe_int(bids),
        "renewals": safe_int(renewals),
        "trigger": trigger,
        "executed": bool(executed),
    }

    destino = ruta or FICHERO

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        filas = _leer(destino)

        filas.append(fila)

        destino.write_text(
            "\n".join(
                json.dumps(f, ensure_ascii=False)
                for f in filas[-ENTRADAS_QUE_SE_GUARDAN:]
            )
            + "\n",
            encoding="utf-8",
        )

        fila["written"] = True

    except Exception:                               # noqa: BLE001
        fila["written"] = False

    return fila


def ultima_ventana(ruta: Path | None = None) -> dict | None:
    """La ultima entrada, o None si no hay ninguna."""

    filas = _leer(ruta or FICHERO)

    return filas[-1] if filas else None


def estado_de_la_ventana(
    ultima: dict | None,
    ahora: datetime | None = None,
    horas_rojo: float = HORAS_SIN_ENTRAR_QUE_SON_ROJO,
) -> dict:
    """
    Cuanto hace que no se entra, y si eso ya es rojo.

    PURA: no lee disco ni reloj. La hora se pasa.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "ever": False,
        "last_at": None,
        "hours_since": None,
        "red": True,
        "last_bids": 0,
        "last_renewals": 0,
        "reason": None,
    }

    try:
        if not isinstance(ultima, dict) or not ultima.get("at"):
            return {
                **vacio,
                "available": True,
                "reason": (
                    "LA VENTANA NO SE HA ABIERTO NUNCA. Ni una "
                    "vez. Si el reloj que la dispara estuviera "
                    "bien, ya habria entrado."
                ),
            }

        momento = ahora or datetime.now(timezone.utc)

        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=timezone.utc)

        marca = datetime.fromisoformat(str(ultima["at"]))

        if marca.tzinfo is None:
            marca = marca.replace(tzinfo=timezone.utc)

        horas = (momento - marca).total_seconds() / 3600.0

        rojo = horas > horas_rojo

        pujas = safe_int(ultima.get("bids"))

        renovaciones = safe_int(ultima.get("renewals"))

        hizo = (
            f"{pujas} puja(s) y {renovaciones} renovacion(es)"
            if (pujas or renovaciones)
            else "nada: entro y no habia trabajo"
        )

        return {
            "available": True,
            "ever": True,
            "last_at": str(ultima["at"]),
            "hours_since": round(horas, 2),
            "red": bool(rojo),
            "last_bids": pujas,
            "last_renewals": renovaciones,
            "last_trigger": ultima.get("trigger"),
            "reason": (
                (
                    f"HACE {horas:.1f} HORAS QUE NO SE ENTRA EN LA "
                    f"VENTANA, y se abre una vez al dia. Algo que "
                    f"la dispara no esta funcionando. La ultima "
                    f"vez hizo {hizo}."
                )
                if rojo
                else (
                    f"Ultima entrada hace {horas:.1f} h: "
                    f"{hizo}."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo leer el libro de la ventana, asi que "
                f"se da por ROJO: {type(error).__name__}: {error}"
            ),
        }
