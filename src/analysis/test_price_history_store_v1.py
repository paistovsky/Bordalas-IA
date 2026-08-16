"""
El archivo de precios tiene que sobrevivir al pruning.

POR QUE IMPORTA

    `scripts/prune_github_state.py` guarda 24 snapshots. Con el
    ciclo cada 30 minutos son 12 horas de memoria.

    Y todo lo que Bordalas sabe del mercado se calcula comparando
    precios de dias distintos: la velocidad de cada jugador, la
    curva de primas que pagan los rivales, el desgaste de la
    tendencia.

    La consecuencia ya estaba medida antes de escribir esto: el
    modelo de primas descartaba 62 pujas rivales "sin precio de
    aquel momento" y llevaba desde el principio con 8 muestras de
    las 12 que necesita.
"""

import json
import shutil
import sys
import tempfile

from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, ".")

from src.analysis import price_history_store as store_mod  # noqa: E402


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# UTILIDADES
# ================================================================


def snapshot(precios: dict) -> dict:
    return {
        "catalog": {
            "data": {
                "players": {
                    str(pid): {
                        "id": pid,
                        "name": f"Jugador {pid}",
                        "price": precio,
                    }
                    for pid, precio in precios.items()
                }
            }
        }
    }


class TemporaryStore:
    """
    El modulo escribe en data/autopilot. Aqui se le desvia a un
    directorio temporal para no tocar el estado real.
    """

    def __enter__(self):
        self.directory = Path(tempfile.mkdtemp())
        self._dir = store_mod.STATE_DIRECTORY
        self._file = store_mod.STORE_FILE
        store_mod.STATE_DIRECTORY = self.directory
        store_mod.STORE_FILE = self.directory / "price_history.json"
        return self

    def __exit__(self, *_):
        store_mod.STATE_DIRECTORY = self._dir
        store_mod.STORE_FILE = self._file
        shutil.rmtree(self.directory, ignore_errors=True)


# ================================================================
# 1. ESCRITURA
# ================================================================


print()
print("1. Anotar precios sin duplicar")
print("-" * 60)

with TemporaryStore():

    ahora = datetime(2026, 8, 16, 12, 0)

    r1 = store_mod.record_snapshot_prices(
        snapshot({100: 1_000_000, 200: 500_000}),
        now=ahora,
        store=store_mod.empty_store(),
    )

    check("anota los dos jugadores", r1["recorded"] == 2, str(r1))

    # Mismo precio, media hora despues: no se anota nada nuevo.
    r2 = store_mod.record_snapshot_prices(
        snapshot({100: 1_000_000, 200: 500_000}),
        now=ahora + timedelta(minutes=30),
        store=r1["store"],
    )

    check(
        "media hora despues con el mismo precio no anota",
        r2["recorded"] == 0 and r2["unchanged"] == 2,
        str(r2),
    )

    # Uno cambia de precio: solo ese se anota.
    r3 = store_mod.record_snapshot_prices(
        snapshot({100: 1_020_000, 200: 500_000}),
        now=ahora + timedelta(hours=1),
        store=r2["store"],
    )

    check(
        "solo se anota el que cambia",
        r3["recorded"] == 1 and r3["unchanged"] == 1,
        str(r3),
    )

    # Pasado el latido, se anota aunque no cambie.
    r4 = store_mod.record_snapshot_prices(
        snapshot({100: 1_020_000, 200: 500_000}),
        now=ahora + timedelta(hours=25),
        store=r3["store"],
    )

    check(
        "pasado el latido se anota aunque no cambie",
        r4["recorded"] == 2,
        str(r4),
    )

    check(
        "un precio invalido no entra",
        store_mod.record_snapshot_prices(
            snapshot({300: 0}),
            now=ahora,
            store=store_mod.empty_store(),
        )["recorded"] == 0,
    )


# ================================================================
# 2. LO QUE HACE FALTA: SOBREVIVIR AL PRUNING
# ================================================================


print()
print("2. 12 horas de snapshots, 45 días de precios")
print("-" * 60)

with TemporaryStore():

    inicio = datetime(2026, 7, 20, 6, 0)
    st = store_mod.empty_store()

    # Un mes de ciclos cada 30 minutos, con el precio subiendo.
    for dia in range(30):
        for vuelta in range(2):
            momento = inicio + timedelta(
                days=dia, hours=vuelta * 6
            )
            st = store_mod.record_snapshot_prices(
                snapshot({100: 1_000_000 + dia * 10_000}),
                now=momento,
                store=st,
            )["store"]

    estado = store_mod.describe_store(st)

    check(
        "conserva un mes de historia",
        estado["days"] >= 28,
        f"dias={estado['days']}",
    )

    check(
        "sin inflarse: un registro por cambio, no por ciclo",
        estado["records"] <= 40,
        f"registros={estado['records']} (60 ciclos)",
    )

    indice = store_mod.build_index_from_store(st)

    check(
        "el indice tiene la forma que esperan los motores",
        set(indice[100][0].keys())
        >= {"timestamp", "player_id", "price", "price_increment"},
        str(indice[100][0]),
    )

    check(
        "los registros salen ordenados",
        all(
            a["timestamp"] <= b["timestamp"]
            for a, b in zip(indice[100], indice[100][1:])
        ),
    )

    check(
        "el incremento se reconstruye entre registros",
        indice[100][1]["price_increment"] == 10_000,
        str(indice[100][1]),
    )


# ================================================================
# 3. PODA
# ================================================================


print()
print("3. La poda tira lo viejo y conserva lo útil")
print("-" * 60)

with TemporaryStore():

    ahora = datetime(2026, 8, 16, 12, 0)
    st = store_mod.empty_store()

    antiguo = ahora - timedelta(
        days=store_mod.MAX_HISTORY_DAYS + 10
    )

    st = store_mod.record_snapshot_prices(
        snapshot({100: 900_000}), now=antiguo, store=st
    )["store"]

    st = store_mod.record_snapshot_prices(
        snapshot({100: 1_000_000}), now=ahora, store=st
    )["store"]

    quedan = st["players"]["100"]["t"]

    check(
        "el registro de hace 55 días desaparece",
        len(quedan) == 1,
        str(st["players"]["100"]),
    )

    check(
        "el de hoy se conserva",
        st["players"]["100"]["p"] == [1_000_000],
    )

    vacio = store_mod.describe_store(store_mod.empty_store())

    check(
        "sin historia se dice, no se inventa",
        vacio["available"] is False and vacio["days"] == 0,
    )


# ================================================================
# 4. AGUANTE
# ================================================================


print()
print("4. Aguante")
print("-" * 60)

with TemporaryStore():

    for roto in ({}, {"catalog": None}, {"catalog": {"data": {}}}):
        r = store_mod.record_snapshot_prices(
            roto,
            now=datetime(2026, 8, 16, 12, 0),
            store=store_mod.empty_store(),
        )
        check(
            f"aguanta snapshot roto {str(roto)[:24]}",
            r["recorded"] == 0,
        )

    # Un fichero corrupto no puede tumbar el ciclo.
    store_mod.ensure_state_directory()
    store_mod.STORE_FILE.write_text("{esto no es json", encoding="utf-8")

    check(
        "un fichero corrupto se descarta en silencio",
        store_mod.load_price_history_store()["players"] == {},
    )

    # Ida y vuelta a disco.
    st = store_mod.record_snapshot_prices(
        snapshot({100: 1_000_000}),
        now=datetime(2026, 8, 16, 12, 0),
        store=store_mod.empty_store(),
    )["store"]

    store_mod.save_price_history_store(st)
    leido = store_mod.load_price_history_store()

    check(
        "lo guardado se vuelve a leer igual",
        leido["players"]["100"]["p"] == [1_000_000],
        str(leido),
    )

    check(
        "se guarda compacto, sin espacios de adorno",
        b", " not in store_mod.STORE_FILE.read_bytes(),
    )


# ================================================================
# RESULTADO
# ================================================================


print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
