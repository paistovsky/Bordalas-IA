"""
Rellena el historico compacto con los snapshots que todavia hay.

Se ejecuta UNA VEZ. Ahora mismo quedan en disco varios dias de
snapshots completos que el pruning va a borrar; esos precios son
justo los que necesitan la curva de primas y la velocidad, y una
vez borrados no se recuperan.

    python scripts/backfill_price_history.py

A partir de ahi el ciclo va anotando solo.
"""

from __future__ import annotations

import sys

from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.price_history_engine import (  # noqa: E402
    get_snapshot_files,
    load_raw_snapshot,
    parse_snapshot_timestamp,
)

from src.analysis.price_history_store import (  # noqa: E402
    describe_store,
    empty_store,
    load_price_history_store,
    record_snapshot_prices,
    save_price_history_store,
)


def main() -> None:

    store = load_price_history_store()

    antes = describe_store(store)

    ficheros = get_snapshot_files()

    print(f"Snapshots encontrados: {len(ficheros)}")

    if not ficheros:
        print("No hay nada que rellenar.")
        return

    leidos = 0
    anotados = 0

    for path in ficheros:

        marca = parse_snapshot_timestamp(path)

        if marca is None:
            continue

        snapshot = load_raw_snapshot(path)

        if snapshot is None:
            continue

        resultado = record_snapshot_prices(
            snapshot,
            now=datetime.fromtimestamp(marca),
            store=store,
        )

        store = resultado["store"]
        anotados += resultado["recorded"]
        leidos += 1

    save_price_history_store(store)

    despues = describe_store(store)

    print()
    print(f"Snapshots leidos:      {leidos}")
    print(f"Registros anotados:    {anotados}")
    print()
    print(
        f"Historia antes:        "
        f"{antes.get('days', 0)} dias, "
        f"{antes.get('records', 0)} registros"
    )
    print(
        f"Historia ahora:        "
        f"{despues.get('days', 0)} dias, "
        f"{despues.get('records', 0)} registros, "
        f"{despues.get('players', 0)} jugadores"
    )

    fichero = Path("data") / "autopilot" / "price_history.json"

    if fichero.exists():
        print(
            f"Tamano del fichero:    "
            f"{fichero.stat().st_size / 1024:.0f} KB"
        )


if __name__ == "__main__":
    main()
