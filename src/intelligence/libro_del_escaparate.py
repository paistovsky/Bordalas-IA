"""
El libro del escaparate: los veinte de cada reset, guardados.

POR QUE EXISTE

    El 17/09 se midio como rota el escaparate del Computer y la
    respuesta fue que NO HAY HISTORICO. Lo unico reconstruible
    eran nueve dias sueltos sacados de `market.sales` dentro de
    los 95 `data/snapshot_*.json`, con un agujero de tres semanas
    del 18/08 al 09/09.

    Con diez dias se puede decir que entran 11,5 nuevos de 20 al
    dia y que un vigilado concreto tarda unos cuarenta dias en
    salir. No se puede decir mucho mas, y cada dia sin libro es un
    dia de datos que no vuelve.

    Esto no pide NADA a la red: los veinte ya vienen en
    `market.sales` y sus puntos en el catalogo, que el ciclo ya
    trae. El pronostico de titularidad tambien esta ya cargado.

EL DIA DE MERCADO CORTA EN EL RESET, NO A MEDIANOCHE

    Medido el 17/09: agrupando por dia natural salian escaparates
    de 29 y 34 jugadores, que es imposible porque el Computer saca
    veinte. Agrupando por dia de mercado —el corte en el reset de
    las 05:00 UTC— salen 20 exactos los diez dias.

    Asi que la idempotencia se compara contra el DIA DE MERCADO.
    `censo_del_reset` compara contra `at[:10]`, el dia natural, y
    por eso una vuelta de las 03:00 y otra de las 06:00 le cuentan
    como el mismo reset cuando son dos.

    No se toca el censo: aqui se hace bien y queda dicho por que.

QUE SE GUARDA DE CADA UNO

    id, nombre, posicion, precio, puntos de temporada, partidos
    jugados y pronostico de titularidad.

    LOS PARTIDOS Y EL PRONOSTICO SON LA MITAD QUE FALTABA. Sin
    ellos no se puede reconstruir "¿nos mejoraba?" de un dia
    pasado: el 17/09 la tabla de oportunidades perdidas se quedo
    en n=1 dia justamente por eso.

ESTO NO PUJA, NO COMPRA Y NO DECIDE

    Escribe una linea y se va. Ninguna ruta lo lee para decidir
    nada.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path


DIRECTORIO = Path("data") / "trading"

LIBRO = DIRECTORIO / "libro_del_escaparate.jsonl"


# El escaparate se renueva a esta hora UTC. Mismo numero que
# `el_escaparate.HORA_DEL_RESET`, y se importa de alli para que no
# haya dos.
try:
    from src.analysis.el_escaparate import HORA_DEL_RESET

except Exception:                                   # noqa: BLE001
    HORA_DEL_RESET = 5


# Un reset al dia durante una temporada larga. A 38 jornadas y
# algo mas de margen, sobra.
LINEAS_QUE_SE_GUARDAN = 400


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _ahora() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


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


def _apendar(fila: dict, ruta: Path, tope: int) -> bool:
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        filas = _leer(ruta)

        filas.append(fila)

        ruta.write_text(
            "\n".join(
                json.dumps(f, ensure_ascii=False)
                for f in filas[-tope:]
            )
            + "\n",
            encoding="utf-8",
        )

        return True

    except Exception:                               # noqa: BLE001
        return False


def dia_de_mercado(momento, hora_del_reset: int = HORA_DEL_RESET) -> str:
    """
    A que escaparate pertenece un instante. Texto ISO de la fecha.

    Nunca mira el reloj: el instante entra por argumento.
    """

    if isinstance(momento, str):
        instante = datetime.datetime.fromisoformat(
            momento.replace("Z", "+00:00")
        )

    else:
        instante = momento

    if instante.tzinfo is not None:
        instante = instante.replace(tzinfo=None)

    return (
        instante - datetime.timedelta(hours=int(hora_del_reset))
    ).date().isoformat()


def construir_fila(
    escaparate: list | None,
    *,
    at: str | None = None,
    hora_del_reset: int = HORA_DEL_RESET,
) -> dict:
    """
    La linea del libro, sin escribir nada.

    `escaparate` son los del Computer ya compactados: cada uno con
    `id`, `name`, `position`, `price`, `points`, `played` y
    `starter_probability`.

    Nunca lanza. Con el escaparate vacio no devuelve una linea con
    cero jugadores: devuelve que no hay escaparate. Un reset con
    veinte y un reset que no se pudo leer no pueden acabar
    escritos igual.
    """

    try:
        filas = [
            j for j in (escaparate or []) if isinstance(j, dict)
        ]

        momento = at or _ahora()

        if not filas:
            return {
                "available": False,
                "at": momento,
                "dia_de_mercado": dia_de_mercado(
                    momento, hora_del_reset
                ),
                "players": [],
                "reason": (
                    "El escaparate llega vacio: no se apunta una "
                    "linea de cero jugadores, que se leeria como un "
                    "reset sin mercado."
                ),
            }

        jugadores = []

        for ficha in filas:

            partidos = safe_int(ficha.get("played")) or (
                safe_int(ficha.get("played_home"))
                + safe_int(ficha.get("played_away"))
            )

            probabilidad = ficha.get("starter_probability")

            jugadores.append(
                {
                    "id": safe_int(ficha.get("id")),
                    "name": ficha.get("name"),
                    "position": ficha.get("position"),
                    "price": safe_int(
                        ficha.get("price")
                        if ficha.get("price") is not None
                        else ficha.get("market_price")
                    ),
                    "points": safe_int(ficha.get("points")),
                    "played": partidos,

                    # LA MITAD QUE FALTABA. Sin esto no se puede
                    # reconstruir "¿nos mejoraba?" de un dia
                    # pasado, y `None` no es cero: es que no se
                    # sabia.
                    "starter_probability": (
                        float(probabilidad)
                        if probabilidad is not None
                        else None
                    ),
                    "hierarchy": ficha.get("hierarchy"),
                }
            )

        con_pronostico = sum(
            1
            for j in jugadores
            if j["starter_probability"] is not None
        )

        return {
            "available": True,
            "at": momento,
            "dia_de_mercado": dia_de_mercado(momento, hora_del_reset),
            "players": jugadores,
            "n": len(jugadores),
            "with_forecast": con_pronostico,
            "reason": (
                f"{len(jugadores)} jugadores en el escaparate, "
                f"{con_pronostico} con pronostico de titularidad."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "at": at or "",
            "players": [],
            "reason": (
                f"No se pudo construir la linea del escaparate: "
                f"{type(error).__name__}: {error}"
            ),
        }


def apuntar_el_escaparate(
    escaparate: list | None,
    *,
    at: str | None = None,
    ruta: Path | None = None,
    hora_del_reset: int = HORA_DEL_RESET,
) -> dict:
    """
    Una linea por reset. Si la vuelta se repite dentro del mismo
    reset, NO se duplica.

    Nunca lanza: esto es un cuaderno, no puede tumbar un ciclo.
    """

    try:
        fila = construir_fila(
            escaparate, at=at, hora_del_reset=hora_del_reset
        )

        if not fila.get("available"):
            return {**fila, "written": False}

        destino = ruta or LIBRO

        anteriores = _leer(destino)

        # LA IDEMPOTENCIA SE COMPARA CONTRA EL DIA DE MERCADO.
        #
        #     Y contra CUALQUIER linea anterior, no solo la
        #     ultima: si una vuelta se retrasa y otra se adelanta,
        #     dos lineas del mismo reset podrian no quedar
        #     seguidas.
        ya = any(
            str(f.get("dia_de_mercado")) == fila["dia_de_mercado"]
            for f in anteriores
        )

        if ya:
            return {
                **fila,
                "written": False,
                "reason": (
                    f"Ya hay escaparate apuntado del "
                    f"{fila['dia_de_mercado']}: no se duplica."
                ),
            }

        escrito = _apendar(
            {
                "at": fila["at"],
                "dia_de_mercado": fila["dia_de_mercado"],
                "n": fila["n"],
                "with_forecast": fila["with_forecast"],
                "players": fila["players"],
            },
            destino,
            LINEAS_QUE_SE_GUARDAN,
        )

        return {
            **fila,
            "written": escrito,
            "lineas": len(anteriores) + (1 if escrito else 0),
            "reason": (
                f"Escaparate del {fila['dia_de_mercado']} apuntado: "
                f"{fila['n']} jugadores, {fila['with_forecast']} con "
                f"pronostico."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "written": False,
            "players": [],
            "reason": (
                f"No se pudo apuntar el escaparate: "
                f"{type(error).__name__}: {error}"
            ),
        }
