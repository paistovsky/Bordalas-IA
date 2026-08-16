from __future__ import annotations

"""
Historico de precios compacto y persistente.

EL PROBLEMA

    Todo lo que Bordalas sabe del mercado sale de comparar
    precios de dias distintos: la velocidad de cada jugador, la
    curva de primas que pagan los rivales, el desgaste de la
    tendencia.

    Ese historico vivia en los snapshots completos, y
    `scripts/prune_github_state.py` guarda 24. Con el ciclo cada
    30 minutos eso son **12 horas**.

    Ya se nota: el modelo de primas reporta "62 descartadas sin
    precio de aquel momento". Sesenta y dos pujas rivales que no
    se pueden calibrar porque el precio de aquel dia se borro. La
    curva lleva desde el principio con 8 muestras de las 12 que
    necesita.

LA SOLUCION

    Un snapshot completo pesa 500 KB porque lleva plantillas,
    mercado, ofertas y catalogo entero. Para el historico solo
    hacen falta tres cosas por jugador y dia: id, precio y
    cuando.

    Este fichero guarda eso y nada mas, en `data/autopilot`, que
    es una carpeta que la cache de GitHub Actions ya conserva
    entre ejecuciones. Cuarenta y cinco dias de historia ocupan
    menos que dos snapshots.

QUE NO HACE

    No sustituye a los snapshots: siguen haciendo falta para
    operar. Sustituye a la idea de que los snapshots son tambien
    el archivo historico, que es lo que no aguanta el pruning.
"""

import json

from datetime import datetime
from pathlib import Path


STATE_DIRECTORY = (
    Path("data")
    / "autopilot"
)

STORE_FILE = (
    STATE_DIRECTORY
    / "price_history.json"
)


# Cuanta historia se conserva.
#
# La curva de primas necesita el precio del dia en que se hizo
# cada puja, y las pujas que se observan tienen semanas. Con 45
# dias se cubre lo que el tablon devuelve sin que el fichero se
# desmande.
MAX_HISTORY_DAYS = 45

SECONDS_PER_DAY = 24 * 60 * 60

# Un jugador cuyo precio no cambia no genera registro nuevo, pero
# tampoco puede quedarse mudo para siempre: sin un punto de
# control periodico no se puede distinguir "no cambio" de "no
# habia dato".
HEARTBEAT_SECONDS = 20 * 3600


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def ensure_state_directory() -> None:
    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def empty_store() -> dict:
    return {
        "version": 1,
        "updated_at": None,
        "players": {},
    }


# ============================================================
# PERSISTENCIA
# ============================================================


def load_price_history_store() -> dict:

    if not STORE_FILE.exists():
        return empty_store()

    try:

        with open(
            STORE_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Root invalido.")

        jugadores = data.get("players")

        if not isinstance(jugadores, dict):
            data["players"] = {}

        return data

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ):
        return empty_store()


def save_price_history_store(
    store: dict,
) -> None:

    ensure_state_directory()

    temporary = STORE_FILE.with_suffix(
        ".json.tmp"
    )

    with open(
        temporary,
        "w",
        encoding="utf-8",
    ) as file:

        # separators sin espacios: son cientos de miles de
        # numeros y el espacio sobrante es la mitad del fichero.
        json.dump(
            store,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    temporary.replace(STORE_FILE)


# ============================================================
# ESCRITURA
# ============================================================


def _catalog_players(snapshot: dict) -> list:

    catalogo = (snapshot or {}).get("catalog") or {}
    data = catalogo.get("data") or catalogo or {}
    jugadores = data.get("players") or {}

    if isinstance(jugadores, dict):
        jugadores = list(jugadores.values())

    return [
        j for j in jugadores
        if isinstance(j, dict)
    ]


def record_snapshot_prices(
    snapshot: dict,
    now: datetime | None = None,
    store: dict | None = None,
) -> dict:
    """
    Anota los precios de hoy.

    Solo escribe cuando el precio cambia o cuando el ultimo
    registro se ha quedado viejo. Sin eso el fichero crecería un
    registro por jugador y ciclo -48 al dia- para guardar el
    mismo numero.

    Nunca lanza.
    """

    momento = now or datetime.now()
    marca = int(momento.timestamp())

    store = (
        store
        if store is not None
        else load_price_history_store()
    )

    jugadores = store.setdefault("players", {})

    anotados = 0
    saltados = 0

    for jugador in _catalog_players(snapshot):

        player_id = jugador.get("id")

        if player_id is None:
            continue

        precio = safe_int(jugador.get("price"))

        if precio <= 0:
            continue

        clave = str(int(player_id))

        entrada = jugadores.get(clave)

        if entrada is None:
            entrada = {"t": [], "p": []}
            jugadores[clave] = entrada

        tiempos = entrada.setdefault("t", [])
        precios = entrada.setdefault("p", [])

        if tiempos and precios:

            mismo_precio = precios[-1] == precio
            reciente = (
                marca - tiempos[-1]
            ) < HEARTBEAT_SECONDS

            if mismo_precio and reciente:
                saltados += 1
                continue

        tiempos.append(marca)
        precios.append(precio)
        anotados += 1

    store["updated_at"] = momento.isoformat()

    podados = prune_store(store, now=momento)

    return {
        "recorded": anotados,
        "unchanged": saltados,
        "pruned": podados,
        "players": len(jugadores),
        "store": store,
    }


def prune_store(
    store: dict,
    now: datetime | None = None,
) -> int:
    """
    Tira lo que ya no sirve para calibrar nada.
    """

    momento = now or datetime.now()
    limite = int(
        momento.timestamp()
    ) - MAX_HISTORY_DAYS * SECONDS_PER_DAY

    jugadores = store.get("players") or {}
    eliminados = 0

    for clave in list(jugadores.keys()):

        entrada = jugadores[clave] or {}
        tiempos = entrada.get("t") or []
        precios = entrada.get("p") or []

        conservados_t = []
        conservados_p = []

        for marca, precio in zip(tiempos, precios):
            if marca >= limite:
                conservados_t.append(marca)
                conservados_p.append(precio)
            else:
                eliminados += 1

        if conservados_t:
            entrada["t"] = conservados_t
            entrada["p"] = conservados_p
        else:
            del jugadores[clave]

    return eliminados


# ============================================================
# LECTURA
# ============================================================


def build_index_from_store(
    store: dict | None = None,
) -> dict:
    """
    Devuelve el historico con la misma forma que produce
    `build_price_history_index` a partir de snapshots, para que
    los motores que ya existen no tengan que enterarse de nada.

    Los registros van ordenados por fecha, del mas antiguo al mas
    reciente.
    """

    store = (
        store
        if store is not None
        else load_price_history_store()
    )

    indice = {}

    for clave, entrada in (
        store.get("players") or {}
    ).items():

        try:
            player_id = int(clave)

        except (TypeError, ValueError):
            continue

        tiempos = (entrada or {}).get("t") or []
        precios = (entrada or {}).get("p") or []

        registros = []

        anterior = None

        for marca, precio in sorted(
            zip(tiempos, precios)
        ):
            registros.append(
                {
                    "timestamp": int(marca),
                    "snapshot_file": "price_history.json",
                    "player_id": player_id,
                    "name": None,
                    "price": int(precio),
                    "price_increment": (
                        int(precio) - anterior
                        if anterior is not None
                        else 0
                    ),
                    "status": None,
                    "points": 0,
                    "points_last_season": 0,
                }
            )

            anterior = int(precio)

        if registros:
            indice[player_id] = registros

    return indice


def describe_store(
    store: dict | None = None,
) -> dict:
    """
    Cuanta historia tenemos de verdad. Para poder decirlo en el
    dashboard en vez de suponerlo.
    """

    store = (
        store
        if store is not None
        else load_price_history_store()
    )

    jugadores = store.get("players") or {}

    marcas = [
        marca
        for entrada in jugadores.values()
        for marca in ((entrada or {}).get("t") or [])
    ]

    if not marcas:
        return {
            "available": False,
            "players": 0,
            "records": 0,
            "days": 0.0,
            "reason": (
                "Todavia no hay historico compacto guardado."
            ),
        }

    primero = min(marcas)
    ultimo = max(marcas)
    dias = (ultimo - primero) / SECONDS_PER_DAY

    return {
        "available": True,
        "players": len(jugadores),
        "records": len(marcas),
        "days": round(dias, 2),
        "first_epoch": primero,
        "last_epoch": ultimo,
        "reason": (
            f"{len(marcas)} registros de {len(jugadores)} "
            f"jugadores a lo largo de {dias:.1f} dias."
        ),
    }
