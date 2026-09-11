"""
El libro de VIAJES: quien esta de viaje, y cuanto costo.

QUE FALTABA

    `salida_del_viaje.que_cobrar` -la mitad que COBRA- espera
    recibir una lista de viajes con `player_id`, `name` y `cost`.
    Nadie la producia. La mitad que cobra llevaba un dia escrita
    y apagada porque no habia nada que cobrar.

    Esto es la otra mitad: quien entra en el libro, cuando, y de
    donde sale su coste.

EL COSTE NO SE RECONSTRUYE: SE LEE

    Biwenger publica lo que pagamos por cada jugador nuestro:

        GET /user?fields=players(id,owner)
        -> {"id": 19862, "owner": {"date": ..., "price": 5147000}}

    Medido el 10/09/2026: cuadra con el tablon AL EURO en 9 de 9
    comparables. Los otros 4 no discrepan -son del reparto
    inicial y no tienen precio en ninguna de las dos fuentes-.

    Asi que el libro NO guarda el coste. Guarda quien es un
    viaje; el coste se pregunta. Si el libro se perdiera, el
    coste seguiria siendo correcto.

POR QUE EL LIBRO GUARDA TAN POCO

    Un libro que acumula cifras puede retroceder con la cache de
    CI y decidir con numeros viejos. Este solo guarda una cosa
    que no se puede deducir de ningun sitio: que ESTE jugador se
    compro para revenderlo.

    Y si se pierde, falla del lado seguro: sin marca, la ruta del
    viaje no toca al jugador. Se queda en plantilla, que es
    exactamente lo que haria el bot de siempre.

LA MARCA ES EL PERMISO

    Ningun jugador se vende por esta ruta sin estar aqui. Es la
    primera de las cinco prohibiciones de `que_cobrar`, y la
    unica que depende de este fichero.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


LIBRO = Path("data") / "trading" / "libro_de_viajes.jsonl"

ABIERTO = "ABIERTO"

CERRADO = "CERRADO"

# Lo que marca una operacion de la rendija. Va en cada apunte
# para poder contar, medir y apagar la rendija sin tocar nada
# mas.
RENDIJA = "RENDIJA"


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _apuntar(fila: dict, ruta: Path | None = None) -> bool:
    """Al libro, sin lanzar nunca."""

    destino = ruta or LIBRO

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        with destino.open("a", encoding="utf-8") as fichero:
            fichero.write(
                json.dumps(fila, ensure_ascii=False) + "\n"
            )

        return True

    except Exception:                               # noqa: BLE001
        return False


def _leer(ruta: Path | None = None) -> list:
    destino = ruta or LIBRO

    try:
        if not destino.exists():
            return []

        filas = []

        for linea in destino.read_text(
            encoding="utf-8"
        ).splitlines():

            linea = linea.strip()

            if not linea:
                continue

            try:
                fila = json.loads(linea)

            except json.JSONDecodeError:
                # Una linea rota no puede tirar el libro entero,
                # pero tampoco se inventa: se salta y ya.
                continue

            if isinstance(fila, dict):
                filas.append(fila)

        return filas

    except Exception:                               # noqa: BLE001
        return []


# ============================================================
# ABRIR
# ============================================================


def abrir(
    player_id,
    name: str | None = None,
    position=None,
    via: str = RENDIJA,
    ruta: Path | None = None,
) -> dict:
    """
    Marca a un jugador como VIAJE. Forma fija, nunca lanza.

    Se llama al GANAR la puja, no al ponerla: hasta que el reset
    no resuelve, no hay nada que vender.
    """

    pid = safe_int(player_id)

    if pid <= 0:
        return {
            "available": False,
            "opened": False,
            "reason": (
                "Sin `player_id` no se puede marcar un viaje."
            ),
        }

    if esta_de_viaje(pid, ruta=ruta):
        return {
            "available": True,
            "opened": False,
            "player_id": pid,
            "reason": (
                f"{name or pid} ya estaba marcado VIAJE: no se "
                f"abre dos veces."
            ),
        }

    fila = {
        "at": _ahora(),
        "player_id": pid,
        "name": name,
        "position": safe_int(position) or None,
        "via": via,
        "state": ABIERTO,
    }

    if not _apuntar(fila, ruta):
        return {
            "available": False,
            "opened": False,
            "player_id": pid,
            "reason": (
                "No se pudo escribir el libro de viajes: el "
                "jugador NO queda marcado y la ruta del viaje no "
                "lo tocara."
            ),
        }

    return {
        "available": True,
        "opened": True,
        "player_id": pid,
        "entry": fila,
        "reason": f"{name or pid} marcado VIAJE por la {via}.",
    }


def cerrar(
    player_id,
    motivo: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """Se acabo el viaje: vendido, caducado o cortado."""

    pid = safe_int(player_id)

    if pid <= 0 or not esta_de_viaje(pid, ruta=ruta):
        return {
            "available": True,
            "closed": False,
            "player_id": pid,
            "reason": "No estaba de viaje.",
        }

    ok = _apuntar(
        {
            "at": _ahora(),
            "player_id": pid,
            "state": CERRADO,
            "reason": motivo,
        },
        ruta,
    )

    return {
        "available": bool(ok),
        "closed": bool(ok),
        "player_id": pid,
        "reason": motivo,
    }


# ============================================================
# LEER
# ============================================================


def _ultimo_estado(ruta: Path | None = None) -> dict:
    """El ultimo apunte de cada jugador. El libro es un diario."""

    estado = {}

    for fila in _leer(ruta):

        pid = safe_int(fila.get("player_id"))

        if pid <= 0:
            continue

        anterior = estado.get(pid) or {}

        # Se conserva lo que solo trae la apertura -nombre,
        # posicion, via- para que un cierre no lo borre.
        estado[pid] = {
            **anterior,
            **{
                k: v
                for k, v in fila.items()
                if v is not None
            },
        }

    return estado


def esta_de_viaje(player_id, ruta: Path | None = None) -> bool:
    fila = _ultimo_estado(ruta).get(safe_int(player_id))

    return bool(fila) and fila.get("state") == ABIERTO


def abiertos(
    plantilla: list | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Los viajes abiertos, con su coste puesto desde la PLANTILLA.

    `plantilla` son las fichas tal como las publica el estado,
    con `id` y `acquisition_cost` -que sale de `owner.price`-.
    Sin ella se devuelven sin coste, y `que_cobrar` los saltara:
    un viaje sin coste no se puede juzgar contra el suelo.
    """

    vacio = {
        "available": False,
        "viajes": [],
        "sin_coste": [],
        "reason": None,
    }

    try:
        estado = _ultimo_estado(ruta)

        marcados = [
            fila
            for fila in estado.values()
            if fila.get("state") == ABIERTO
        ]

        if not marcados:
            return {
                **vacio,
                "available": True,
                "reason": "No hay ningun viaje abierto.",
            }

        por_id = {}

        for ficha in plantilla or []:

            if isinstance(ficha, dict):
                por_id[safe_int(ficha.get("id"))] = ficha

        viajes = []

        sin_coste = []

        for fila in marcados:

            pid = safe_int(fila.get("player_id"))

            ficha = por_id.get(pid) or {}

            coste = safe_int(
                ficha.get("acquisition_cost")
                or ficha.get("owner_price")
            )

            fila_viaje = {
                "player_id": pid,
                "name": (
                    fila.get("name")
                    or ficha.get("name")
                ),
                "position": (
                    safe_int(ficha.get("position"))
                    or fila.get("position")
                ),
                "cost": coste,
                "state": ABIERTO,
                "via": fila.get("via"),
                "opened_at": fila.get("at"),
                "market_price": safe_int(ficha.get("price")),
            }

            # UN VIAJE SIN COSTE NO SE JUZGA.
            #
            # `que_cobrar` compara contra `coste x (1 + suelo)`.
            # Con coste 0 el suelo seria 0 y cualquier oferta
            # pasaria: es la puerta abierta mas cara que hay.
            if coste <= 0:
                sin_coste.append(fila_viaje)
                continue

            viajes.append(fila_viaje)

        return {
            "available": True,
            "viajes": viajes,
            "sin_coste": sin_coste,
            "reason": (
                f"{len(viajes)} viaje(s) abierto(s)"
                + (
                    f"; {len(sin_coste)} sin coste conocido y por "
                    f"eso fuera"
                    if sin_coste
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo leer el libro de viajes: "
                f"{type(error).__name__}: {error}"
            ),
        }


def cuantos_en_este_reset(
    desde_epoch: int | None = None,
    ruta: Path | None = None,
) -> int:
    """
    Cuantas operaciones de la rendija se han abierto desde el
    ultimo reset. Es la unidad del cupo: de 07:00 a 07:00.
    """

    if desde_epoch is None:
        return 0

    cuantas = 0

    for fila in _leer(ruta):

        if fila.get("state") != ABIERTO:
            continue

        marca = fila.get("at")

        if not marca:
            continue

        try:
            cuando = datetime.fromisoformat(
                str(marca)
            ).timestamp()

        except ValueError:
            continue

        if cuando >= desde_epoch:
            cuantas += 1

    return cuantas
