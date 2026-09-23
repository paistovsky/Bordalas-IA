"""
El libro de aciertos de la valoracion, y la foto de cada jornada.

POR QUE EXISTE (23/09/2026)

    Pujas puestas 57, ganadas 51: un 89,5 %. Ganar nueve de cada
    diez subastas no es punteria: es la señal de que se paga de mas.
    Y no se podia saber cuanto, porque NINGUN libro decia que valor
    le dimos a cada jugador y que paso despues.

    Tercera vez que se pide. Sin esto no se toca ninguna formula de
    valoracion: ajustar un numero sin regla que lo mida es mover el
    error de sitio.

LOS DOS LIBROS

    1. `libro_de_la_valoracion.jsonl`. Una linea por jugador del
       tablero y DIA DE MERCADO: fecha, jugador, valor que le dimos,
       precio, lo que pujariamos, la puja viva y la decision. Y
       cuando pasan 7 y 14 dias, la primera vuelta que llega rellena
       `d7` y `d14` con el precio, los puntos y los partidos de ese
       momento.

    2. `puntos_por_jornada.jsonl`. Una linea por jornada cerrada con
       los puntos, partidos y precio de TODO el catalogo. Son
       totales acumulados: los puntos de una jornada salen de restar
       dos lineas. Sin ella, `d7`/`d14` que no se rellenaran a tiempo
       no se podrian reconstruir.

CUANDO ESTA CERRADA UNA JORNADA

    Cuando han pasado `NEXT_ROUND_UNLOCK_MINUTES` desde el ultimo
    partido suyo que empieza ANTES del primero de la siguiente. Los
    aplazados que se juegan semanas despues -el calendario del 23/09
    tiene partidos de la J6 el 21/10- entran en la foto de la
    jornada en la que se juegan, porque la foto guarda totales. Los
    dos numeros ya existian en `matchday_calendar_engine`.

    Si una jornada se cerro y ninguna vuelta llego a apuntarla antes
    de que cerrara la siguiente, NO se reconstruye: se apunta la
    ultima cerrada y el hueco se ve en la numeracion.

SOLO SE ESCRIBE CON LA FOTO DE HOY

    La misma regla que `libro_del_escaparate` y por el mismo motivo:
    la verja ejercita el panel con la foto del 13/09, y un libro que
    apunte esa foto con la fecha de hoy es basura con etiqueta
    nueva. Sin `foto_at`, o con una foto de otro dia de mercado, no
    se escribe nada y se dice.

ESTO NO DECIDE NADA

    Apunta y rellena. Ninguna ruta lo lee para pujar. Nunca lanza:
    es un cuaderno, no puede tumbar un ciclo.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path


DIRECTORIO = Path("data") / "intelligence"

LIBRO = DIRECTORIO / "libro_de_la_valoracion.jsonl"

FOTOS_DE_JORNADA = DIRECTORIO / "puntos_por_jornada.jsonl"

# Los plazos del encargo.
PLAZOS = (7, 14)

# Una temporada: unos 280 dias de mercado por unos 40 jugadores en
# el tablero. Medido el 23/09: 37 filas en el tablero.
LINEAS_QUE_SE_GUARDAN = 12_000

# 38 jornadas y margen.
JORNADAS_QUE_SE_GUARDAN = 45


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _ahora() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _instante(valor) -> datetime.datetime | None:
    if valor is None:
        return None

    if isinstance(valor, datetime.datetime):
        instante = valor
    else:
        try:
            instante = datetime.datetime.fromisoformat(
                str(valor).replace("Z", "+00:00")
            )
        except ValueError:
            return None

    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=datetime.timezone.utc)

    return instante


def _dia_de_mercado(momento) -> str:
    from src.intelligence.libro_del_escaparate import dia_de_mercado

    return dia_de_mercado(momento)


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


def _escribir(filas: list, ruta: Path, tope: int) -> bool:
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        ruta.write_text(
            "\n".join(
                json.dumps(f, ensure_ascii=False, separators=(",", ":"))
                for f in filas[-tope:]
            )
            + "\n",
            encoding="utf-8",
        )

        return True

    except Exception:                               # noqa: BLE001
        return False


def _foto_de_hoy(foto_at, ahora) -> str | None:
    """None si la foto es de hoy; si no, el motivo para no escribir."""

    if foto_at is None:
        return (
            "No se sabe de cuando es la foto: no se apunta. Una foto "
            "vieja con la fecha de hoy ensucia el libro entero."
        )

    dia_foto = _dia_de_mercado(_instante(foto_at))
    dia_hoy = _dia_de_mercado(ahora)

    if dia_foto != dia_hoy:
        return (
            f"La foto es del dia de mercado {dia_foto} y hoy es el "
            f"{dia_hoy}: no se apunta."
        )

    return None


def _ficha(catalogo: dict | None, pid: int) -> dict | None:
    ficha = (catalogo or {}).get(pid)

    if ficha is None:
        ficha = (catalogo or {}).get(str(pid))

    return ficha if isinstance(ficha, dict) else None


def _jugados(ficha: dict) -> int:
    return safe_int(ficha.get("playedHome")) + safe_int(
        ficha.get("playedAway")
    )


# ============================================================
# 1. EL LIBRO DE LA VALORACION
# ============================================================


def fila_de_la_valoracion(objetivo: dict, dia: str) -> dict | None:
    """La linea de un jugador del tablero. Sin escribir nada."""

    if not isinstance(objetivo, dict):
        return None

    pid = safe_int(objetivo.get("id"))

    if not pid:
        return None

    return {
        "dia": dia,
        "id": pid,
        "name": objetivo.get("name"),
        "value": (
            safe_int(objetivo.get("our_value"))
            if objetivo.get("our_value") is not None
            else None
        ),
        "price": safe_int(
            objetivo.get("market_price")
            if objetivo.get("market_price") is not None
            else objetivo.get("price")
        ),
        "bid": safe_int(objetivo.get("bid")),
        "live_bid": safe_int(objetivo.get("live_bid")),
        "decision": objetivo.get("decision"),
        "intent": objetivo.get("intent"),
        "seller": objetivo.get("seller_kind"),
    }


def apuntar_la_valoracion(
    tablero: list | None,
    catalogo: dict | None,
    *,
    foto_at=None,
    at=None,
    ruta: Path | None = None,
) -> dict:
    """
    Apunta el tablero de hoy -una linea por jugador y dia de
    mercado, sin duplicar- y rellena los `d7`/`d14` que ya tocan.

    `catalogo` es `{id: ficha}` de ESTA foto: de ahi salen el precio,
    los puntos y los partidos de lo que paso despues.

    Nunca lanza.
    """

    try:
        ahora = _instante(at) or _ahora()

        destino = ruta or LIBRO

        motivo = _foto_de_hoy(foto_at, ahora)

        if motivo:
            return {
                "available": True,
                "written": False,
                "nuevas": 0,
                "rellenadas": 0,
                "reason": motivo,
            }

        dia = _dia_de_mercado(ahora)

        filas = _leer(destino)

        ya = {(f.get("dia"), safe_int(f.get("id"))) for f in filas}

        nuevas = 0

        for objetivo in (tablero or []):

            fila = fila_de_la_valoracion(objetivo, dia)

            if fila is None or (dia, fila["id"]) in ya:
                continue

            filas.append(fila)
            ya.add((dia, fila["id"]))
            nuevas += 1

        # LO QUE PASO DESPUES. La primera vuelta que llega pasado el
        # plazo lo apunta, con su fecha: si llega tarde, se ve.
        rellenadas = 0

        hoy = datetime.date.fromisoformat(dia)

        for fila in filas:

            try:
                apuntado = datetime.date.fromisoformat(
                    str(fila.get("dia"))
                )
            except ValueError:
                continue

            ficha = _ficha(catalogo, safe_int(fila.get("id")))

            if ficha is None:
                continue

            for plazo in PLAZOS:

                clave = f"d{plazo}"

                if clave in fila:
                    continue

                if (hoy - apuntado).days < plazo:
                    continue

                fila[clave] = {
                    "dia": dia,
                    "price": safe_int(ficha.get("price")),
                    "points": safe_int(ficha.get("points")),
                    "played": _jugados(ficha),
                }
                rellenadas += 1

        if not nuevas and not rellenadas:
            return {
                "available": True,
                "written": False,
                "nuevas": 0,
                "rellenadas": 0,
                "lineas": len(filas),
                "reason": (
                    f"Nada nuevo: el tablero del {dia} ya esta "
                    f"apuntado y ningun plazo vence hoy."
                ),
            }

        escrito = _escribir(filas, destino, LINEAS_QUE_SE_GUARDAN)

        return {
            "available": True,
            "written": escrito,
            "nuevas": nuevas,
            "rellenadas": rellenadas,
            "lineas": len(filas),
            "reason": (
                f"{nuevas} jugador(es) apuntados del {dia} y "
                f"{rellenadas} plazo(s) rellenados."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "written": False,
            "reason": (
                f"No se pudo apuntar la valoracion: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# 2. LA FOTO DE CADA JORNADA
# ============================================================


def la_ultima_jornada_cerrada(matchdays: list | None, ahora) -> dict | None:
    """
    `{jornada, cerrada_en}` de la ultima jornada cerrada, o None.

    Cerrada = su ultimo partido anterior al primero de la siguiente,
    mas `NEXT_ROUND_UNLOCK_MINUTES`. Nunca lanza.
    """

    try:
        from src.analysis.matchday_calendar_engine import (
            NEXT_ROUND_UNLOCK_MINUTES,
        )

        ahora = _instante(ahora)

        jornadas = sorted(
            (
                m for m in (matchdays or [])
                if isinstance(m, dict) and m.get("matchday") is not None
            ),
            key=lambda m: safe_int(m.get("matchday")),
        )

        primeros = {
            safe_int(m["matchday"]): _instante(m.get("first_kickoff"))
            for m in jornadas
        }

        ultima = None

        for m in jornadas:

            numero = safe_int(m["matchday"])

            siguiente = primeros.get(numero + 1)

            inicios = [
                _instante(p.get("kickoff"))
                for p in (m.get("matches") or [])
                if isinstance(p, dict)
            ]

            inicios = [
                i for i in inicios
                if i is not None and (siguiente is None or i < siguiente)
            ]

            if not inicios:
                continue

            cierre = max(inicios) + datetime.timedelta(
                minutes=NEXT_ROUND_UNLOCK_MINUTES
            )

            if cierre <= ahora:
                ultima = {
                    "jornada": numero,
                    "cerrada_en": cierre.isoformat(),
                }

        return ultima

    except Exception:                               # noqa: BLE001
        return None


def apuntar_la_foto_de_la_jornada(
    catalogo: dict | None,
    matchdays: list | None,
    *,
    foto_at=None,
    at=None,
    ruta: Path | None = None,
) -> dict:
    """
    Una linea por jornada cerrada con los totales de todo el catalogo.

    `players` es `{id: [puntos, partidos, precio]}`: compacto a
    proposito, son 547 jugadores. Nunca lanza.
    """

    try:
        ahora = _instante(at) or _ahora()

        destino = ruta or FOTOS_DE_JORNADA

        motivo = _foto_de_hoy(foto_at, ahora)

        if motivo:
            return {"available": True, "written": False, "reason": motivo}

        cerrada = la_ultima_jornada_cerrada(matchdays, ahora)

        if cerrada is None:
            return {
                "available": True,
                "written": False,
                "reason": (
                    "El calendario no trae ninguna jornada cerrada: no "
                    "hay foto que apuntar."
                ),
            }

        filas = _leer(destino)

        if any(
            safe_int(f.get("jornada")) == cerrada["jornada"]
            for f in filas
        ):
            return {
                "available": True,
                "written": False,
                "jornada": cerrada["jornada"],
                "reason": (
                    f"La jornada {cerrada['jornada']} ya tiene foto."
                ),
            }

        jugadores = {
            str(safe_int(pid)): [
                safe_int(f.get("points")),
                _jugados(f),
                safe_int(f.get("price")),
            ]
            for pid, f in (catalogo or {}).items()
            if isinstance(f, dict) and safe_int(pid)
        }

        if not jugadores:
            return {
                "available": True,
                "written": False,
                "reason": (
                    "El catalogo llega vacio: no se apunta una foto de "
                    "cero jugadores."
                ),
            }

        filas.append(
            {
                "jornada": cerrada["jornada"],
                "cerrada_en": cerrada["cerrada_en"],
                "at": ahora.isoformat(),
                "foto_at": str(foto_at),
                "n": len(jugadores),
                "players": jugadores,
            }
        )

        escrito = _escribir(filas, destino, JORNADAS_QUE_SE_GUARDAN)

        return {
            "available": True,
            "written": escrito,
            "jornada": cerrada["jornada"],
            "n": len(jugadores),
            "reason": (
                f"Foto de la jornada {cerrada['jornada']} apuntada: "
                f"{len(jugadores)} jugadores."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "written": False,
            "reason": (
                f"No se pudo apuntar la foto de la jornada: "
                f"{type(error).__name__}: {error}"
            ),
        }
