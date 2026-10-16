"""
E44: ¿la valoracion de Pepe («value» del motor de pujas) predice algo?

data/intelligence/libro_de_la_valoracion.jsonl: cada dia, cada jugador
del mercado con su precio, el «value» que le da Pepe y, 7 y 14 dias
despues, su precio y sus puntos. Si value > precio deberia anunciar que el
precio sube o que el jugador puntua. Se compara contra la regla mas
tonta: «sube si subio ayer» (E1/E2), con el historial de precios.

Una fila por jugador y dia (el libro repite al jugador mientras sigue en
el mercado: se cuenta cada dia como una observacion, n es eso).

Uso:  python3 lab/valoracion/acierta.py
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
sys.path.insert(0, str(RAIZ / "lab/puntos"))
from viajes import Precios, pct  # noqa: E402
from que_predice_puntos import spearman  # noqa: E402

LIBRO = RAIZ / "data/intelligence/libro_de_la_valoracion.jsonl"

if __name__ == "__main__":
    P = Precios()
    filas = []
    for l in open(LIBRO):
        r = json.loads(l)
        if not r.get("d7") or not r["price"] or not r["value"]:
            continue
        d = dt.date.fromisoformat(r["dia"])
        ayer = pct(P.en(r["id"], d), P.en(r["id"], d - dt.timedelta(days=1)))
        filas.append(dict(margen=r["value"] / r["price"] - 1, d7=r["d7"]["price"] / r["price"] - 1,
                          ayer=ayer, intent=r["intent"]))
    print(f"Filas con valor y precio a 7 dias: {len(filas)}")
    m = [f["margen"] for f in filas]
    print(f"margen value/precio: mediana {st.median(m):+.1%}, p10 {sorted(m)[len(m)//10]:+.1%}, p90 {sorted(m)[9*len(m)//10]:+.1%}")
    print(f"Spearman margen -> precio a 7 dias: {spearman(m, [f['d7'] for f in filas]):+.3f}")
    con = [f for f in filas if f["ayer"] is not None]
    print(f"Spearman «subio ayer» -> precio a 7 dias: {spearman([f['ayer'] for f in con], [f['d7'] for f in con]):+.3f} (n={len(con)})")
    print("\nPrecio a 7 dias segun lo que dice cada vara:")
    for nombre, g in (("value > precio + 3 %", [f for f in filas if f["margen"] > 0.03]),
                      ("value entre -3 y +3 %", [f for f in filas if -0.03 <= f["margen"] <= 0.03]),
                      ("value < precio - 3 %", [f for f in filas if f["margen"] < -0.03]),
                      ("subio ayer", [f for f in con if f["ayer"] > 0]),
                      ("no subio ayer", [f for f in con if f["ayer"] <= 0])):
        if g:
            print(f"   {nombre:24} n={len(g):>4}  mediana {st.median(f['d7'] for f in g):+6.1%}"
                  f"  sube {sum(f['d7'] > 0 for f in g)/len(g):4.0%}")
    print("\nDentro de «subio ayer», ¿añade algo el value?")
    for nombre, g in (("subio y value > +3 %", [f for f in con if f["ayer"] > 0 and f["margen"] > 0.03]),
                      ("subio y value <= +3 %", [f for f in con if f["ayer"] > 0 and f["margen"] <= 0.03])):
        if g:
            print(f"   {nombre:24} n={len(g):>4}  mediana {st.median(f['d7'] for f in g):+6.1%}"
                  f"  sube {sum(f['d7'] > 0 for f in g)/len(g):4.0%}")
    for nombre, g in (("NO subio y value > +3 %", [f for f in con if f["ayer"] <= 0 and f["margen"] > 0.03]),
                      ("NO subio y value <= +3 %", [f for f in con if f["ayer"] <= 0 and f["margen"] <= 0.03])):
        if g:
            print(f"   {nombre:24} n={len(g):>4}  mediana {st.median(f['d7'] for f in g):+6.1%}"
                  f"  sube {sum(f['d7'] > 0 for f in g)/len(g):4.0%}")
    print("\nPor intencion (value > +3 %):")
    for it in ("SPECULATION", "XI_UPGRADE", None):
        g = [f for f in filas if f["intent"] == it and f["margen"] > 0.03]
        if g:
            print(f"   {str(it):12} n={len(g):>4}  mediana {st.median(f['d7'] for f in g):+6.1%}")
