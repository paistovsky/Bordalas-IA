import json
from datetime import datetime
from pathlib import Path


# ======================================================
# CONFIGURACIÓN
# ======================================================


DEFAULT_DATA_DIRECTORY = "data"


# ======================================================
# CACHE EN MEMORIA
# ======================================================


_HISTORY_CACHE = {}


def clear_price_history_cache() -> None:
    """
    Limpia la caché en memoria.

    Cada ejecución de Python empieza normalmente
    con la caché vacía.
    """

    _HISTORY_CACHE.clear()


# ======================================================
# TIMESTAMP DEL SNAPSHOT
# ======================================================


def parse_snapshot_timestamp(
    path: Path,
) -> int:
    """
    Intenta extraer:

        snapshot_20260809_230140.json

    como timestamp UNIX.

    Si no puede, utiliza mtime.
    """

    name = path.stem

    prefix = "snapshot_"

    if name.startswith(
        prefix
    ):

        value = name[
            len(prefix):
        ]

        try:

            dt = datetime.strptime(
                value,
                "%Y%m%d_%H%M%S",
            )

            return int(
                dt.timestamp()
            )

        except ValueError:
            pass

    return int(
        path.stat().st_mtime
    )


# ======================================================
# LISTADO DE SNAPSHOTS
# ======================================================


def get_snapshot_files(
    directory: str = DEFAULT_DATA_DIRECTORY,
) -> list[Path]:

    data_dir = Path(
        directory
    )

    files = list(
        data_dir.glob(
            "snapshot_*.json"
        )
    )

    files.sort(
        key=parse_snapshot_timestamp
    )

    return files


# ======================================================
# CARGAR SNAPSHOT
# ======================================================


def load_raw_snapshot(
    path: Path,
) -> dict | None:

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return None


# ======================================================
# EXTRAER CATÁLOGO
# ======================================================


def get_catalog_players(
    snapshot: dict,
) -> dict:

    catalog = (
        snapshot
        .get(
            "catalog",
            {},
        )
        .get(
            "data",
            {},
        )
        .get(
            "players",
            {},
        )
    )

    if isinstance(
        catalog,
        dict,
    ):
        return catalog

    return {}


# ======================================================
# NORMALIZAR JUGADOR
# ======================================================


def build_history_record(
    player: dict,
    timestamp: int,
    snapshot_file: str,
) -> dict:

    return {
        "timestamp":
            timestamp,

        "snapshot_file":
            snapshot_file,

        "player_id":
            int(
                player[
                    "id"
                ]
            ),

        "name":
            player.get(
                "name"
            ),

        "price":
            int(
                player.get(
                    "price",
                    0,
                )
                or 0
            ),

        "price_increment":
            int(
                player.get(
                    "priceIncrement",
                    0,
                )
                or 0
            ),

        "status":
            player.get(
                "status"
            ),

        "points":
            int(
                player.get(
                    "points",
                    0,
                )
                or 0
            ),

        "points_last_season":
            int(
                player.get(
                    "pointsLastSeason",
                    0,
                )
                or 0
            ),
    }


# ======================================================
# CONSTRUIR HISTÓRICO COMPLETO
# ======================================================


def build_price_history_index(
    directory: str = DEFAULT_DATA_DIRECTORY,
) -> dict[int, list[dict]]:
    """
    Lee todos los snapshots disponibles y genera:

        {
            player_id: [
                record,
                record,
                ...
            ]
        }

    Se cachea durante la ejecución actual.
    """

    cache_key = str(
        Path(directory).resolve()
    )

    cached = (
        _HISTORY_CACHE.get(
            cache_key
        )
    )

    if cached is not None:
        return cached

    index = {}

    files = (
        get_snapshot_files(
            directory
        )
    )

    for path in files:

        timestamp = (
            parse_snapshot_timestamp(
                path
            )
        )

        snapshot = (
            load_raw_snapshot(
                path
            )
        )

        if snapshot is None:
            continue

        players = (
            get_catalog_players(
                snapshot
            )
        )

        for player in players.values():

            player_id = player.get(
                "id"
            )

            if player_id is None:
                continue

            try:

                record = (
                    build_history_record(
                        player=
                            player,

                        timestamp=
                            timestamp,

                        snapshot_file=
                            str(
                                path
                            ),
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                continue

            index.setdefault(
                int(
                    player_id
                ),
                [],
            ).append(
                record
            )

    # Garantizamos orden cronológico.
    for records in index.values():

        records.sort(
            key=lambda item:
                item[
                    "timestamp"
                ]
        )

    _HISTORY_CACHE[
        cache_key
    ] = index

    return index


# ======================================================
# HISTÓRICO DE UN JUGADOR
# ======================================================


def get_player_price_history(
    player_id: int,
    directory: str = DEFAULT_DATA_DIRECTORY,
) -> list[dict]:

    index = (
        build_price_history_index(
            directory
        )
    )

    return list(
        index.get(
            int(
                player_id
            ),
            [],
        )
    )


# ======================================================
# COMPACTAR REGISTROS
# ======================================================


def collapse_duplicate_prices(
    history: list[dict],
) -> list[dict]:
    """
    Bordalás puede generar muchos snapshots dentro
    del mismo día con exactamente el mismo precio.

    Para estudiar tendencia no necesitamos repetir
    cientos de veces el mismo valor.

    Conservamos un nuevo registro cuando cambia:
        - precio
        - priceIncrement
        - status
    """

    if not history:
        return []

    compact = []

    previous = None

    for record in history:

        signature = (
            record[
                "price"
            ],
            record[
                "price_increment"
            ],
            record[
                "status"
            ],
        )

        if (
            previous is None
            or
            signature != previous
        ):

            compact.append(
                record
            )

            previous = (
                signature
            )

        else:

            # Actualizamos el timestamp del último
            # estado equivalente.
            compact[
                -1
            ] = record

    return compact


# ======================================================
# RESUMEN
# ======================================================


def summarize_player_history(
    player_id: int,
    directory: str = DEFAULT_DATA_DIRECTORY,
) -> dict:

    history = (
        get_player_price_history(
            player_id,
            directory,
        )
    )

    compact = (
        collapse_duplicate_prices(
            history
        )
    )

    if not compact:

        return {
            "player_id":
                player_id,

            "records":
                0,

            "compact_records":
                0,

            "first":
                None,

            "latest":
                None,

            "history":
                [],
        }

    return {
        "player_id":
            player_id,

        "records":
            len(
                history
            ),

        "compact_records":
            len(
                compact
            ),

        "first":
            compact[
                0
            ],

        "latest":
            compact[
                -1
            ],

        "history":
            compact,
    }