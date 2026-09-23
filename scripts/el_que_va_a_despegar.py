"""
El juicio del que va a despegar: ¿subieron y puntuaron?

LA PREGUNTA (23/09/2026)

    Hoy hay jugadores con `nos_suma <= 0` que baten a su vara POR
    PARTIDO. Si en los 7 dias siguientes no hicieron nada, el motor
    tenia razon y se dice. Si subieron y puntuaron, la resta de
    totales les estaba cobrando los partidos que no jugaron.

POR QUE NO SE MIDE SOBRE LA FOTO DE HOY

    Porque sus 7 dias siguientes todavia no han pasado. Se toma el
    ultimo catalogo del repositorio con una semana cerrada detras:
    `data/snapshot_20260913_171717.json`. Ahi se clasifica con el
    mismo `toda_la_liga` de hoy, y despues se mira:

        precio   a +7 dias, de `data/autopilot/price_history.json`
        puntos   a +6 dias (el catalogo del 19/09 18:18) y hasta
                 hoy (el catalogo publico del 23/09, que se pasa
                 como argumento: no esta en el repositorio)

    Y SIEMPRE CONTRA UN GRUPO DE CONTROL. Que suban no dice nada si
    sube todo el mercado (doctrina 95): se compara con los que
    tampoco nos suman y NO baten a su vara, y con los que nos
    mejoran.

ESTO LEE `data/` Y NO ESCRIBE NADA. No es una guardia.

COMO SE USA

    python scripts/el_que_va_a_despegar.py [catalogo_de_hoy.json]
"""

from __future__ import annotations

import json
import statistics
import sys

from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.toda_la_liga import toda_la_liga  # noqa: E402


BASE = RAIZ / "data" / "snapshot_20260913_171717.json"
SEIS_DIAS = RAIZ / "data" / "snapshot_20260919_181829.json"
PRECIOS = RAIZ / "data" / "autopilot" / "price_history.json"

DIAS = 7


def _catalogo(ruta: Path) -> dict:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    cat = datos.get("catalog", datos)
    jugadores = (cat.get("data") or cat).get("players") or {}
    return {int(k): v for k, v in jugadores.items()}


def _precio_en(serie: dict | None, momento: float):
    if not serie:
        return None
    ultimo = None
    for t, p in zip(serie.get("t") or [], serie.get("p") or []):
        if t <= momento:
            ultimo = p
        else:
            break
    return ultimo


def _mediana(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def main() -> None:

    hoy = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    base = json.loads(BASE.read_text(encoding="utf-8"))

    cuando = datetime.fromisoformat(base["timestamp"])

    catalogo = _catalogo(BASE)

    once = (
        ((base.get("user_lineup") or {}).get("data") or {})
        .get("lineup") or {}
    ).get("players")

    plantilla = base.get("my_team")

    if isinstance(plantilla, dict):
        plantilla = plantilla.get("players") or plantilla.get("data")

    liga = toda_la_liga(catalogo, once, plantilla, [], set())

    if not liga.get("available"):
        print(f"Sin liga: {liga.get('reason')}")
        raise SystemExit(1)

    precios = json.loads(PRECIOS.read_text(encoding="utf-8"))[
        "players"
    ]

    t0 = cuando.timestamp()
    t7 = (cuando + timedelta(days=DIAS)).timestamp()

    seis = _catalogo(SEIS_DIAS)
    final = _catalogo(hoy) if hoy else {}

    grupos = {
        "baten a su vara por partido, nos_suma <= 0": [],
        "   de ellos, con la marca «va a despegar»": [],
        "control: nos_suma <= 0 y NO baten a su vara": [],
        "referencia: nos mejoran (nos_suma > 0)": [],
    }

    for f in liga["players"]:

        if f["etiqueta"] == "ya es nuestro" or f["nos_suma"] is None:
            continue

        if f["nos_suma"] > 0:
            grupos["referencia: nos mejoran (nos_suma > 0)"].append(f)
        elif f.get("bate_a_la_vara"):
            grupos["baten a su vara por partido, nos_suma <= 0"].append(f)
            if f.get("va_a_despegar"):
                grupos["   de ellos, con la marca «va a despegar»"].append(f)
        elif f.get("tasa") is not None:
            grupos["control: nos_suma <= 0 y NO baten a su vara"].append(f)

    print()
    print("EL JUICIO DEL QUE VA A DESPEGAR")
    print("=" * 78)
    print(f"  base      {BASE.name}  ({cuando:%d/%m %H:%M})")
    print(f"  vara      " + ", ".join(
        f"{k} {v['name']} {v['points']}/{v['played']}"
        for k, v in liga["vara"].items()
    ))
    print(f"  precio    a +{DIAS} dias ({datetime.fromtimestamp(t7):%d/%m %H:%M})")
    print(f"  puntos    a +6 dias ({SEIS_DIAS.name})"
          + (f" y hasta hoy ({hoy.name})" if hoy else ""))
    print()

    for nombre, filas in grupos.items():

        subidas = []
        sube = 0
        con_precio = 0

        for f in filas:
            serie = precios.get(str(f["id"]))
            p0 = _precio_en(serie, t0)
            p7 = _precio_en(serie, t7)
            if p0 and p7:
                con_precio += 1
                subidas.append(100.0 * (p7 - p0) / p0)
                sube += p7 > p0

        def _puntos(cat):
            deltas = [
                (cat[f["id"]].get("points") or 0) - (f["points"] or 0)
                for f in filas
                if f["id"] in cat
            ]
            return (
                len(deltas),
                sum(1 for d in deltas if d > 0),
                _mediana(deltas),
            )

        n6, pos6, med6 = _puntos(seis)

        print(f"  {nombre}")
        print(f"      n = {len(filas)}")
        print(
            f"      precio +{DIAS} d: subieron {sube} de {con_precio} "
            f"con serie; mediana {_mediana(subidas)} %"
        )
        print(
            f"      puntos +6 d: puntuaron {pos6} de {n6}; "
            f"mediana {med6}"
        )

        if final:
            nf, posf, medf = _puntos(final)
            print(
                f"      puntos hasta hoy: puntuaron {posf} de {nf}; "
                f"mediana {medf}"
            )

        print()


if __name__ == "__main__":
    main()
