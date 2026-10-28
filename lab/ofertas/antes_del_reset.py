"""
E68: ¿vender antes o despues del reset que renueva la oferta? (Luismi, 28/10:
vendio a las 05:27, antes del reset, y saco +9,8 % sobre el valor de
despues.) E42: el Computer renueva cada 48 h la oferta de cada publicado
con el reset de las 07:00. Si el jugador baja, la oferta nueva sale mas
baja que la vieja: venderle con la vieja (vueltas de 04:45/04:50) seria
mejor que con la nueva (07:15).

Del censo de ofertas: mismo jugador en dos lotes seguidos de su turno
(~48 h); oferta nueva / vieja, segun lo que hizo su precio en esos dos dias.

Uso:  python3 lab/ofertas/antes_del_reset.py
"""
import datetime as dt
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

CENSO = RAIZ / "data/solvency/censo_de_ofertas.jsonl"
FOTO = RAIZ / "data/fotos/2026-09-18.json"

if __name__ == "__main__":
    ids = {p["name"]: p["id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    P = Precios()
    vistas = defaultdict(list)  # nombre -> [(momento, importe)]
    for l in open(CENSO):
        r = json.loads(l)
        if r["at"] < "2026-10-01":
            continue
        t = dt.datetime.fromisoformat(r["at"])
        for p in r["players"]:
            vistas[p["name"]].append((t, p["amount"]))
    filas = []
    for n, v in vistas.items():
        v.sort()
        for (t0, a0), (t1, a1) in zip(v, v[1:]):
            h = (t1 - t0).total_seconds() / 3600
            if not (40 <= h <= 56) or a0 == a1:
                continue  # misma oferta vista dos veces, o turnos que no son seguidos
            pid = ids.get(n)
            d0, d1 = (t0 - dt.timedelta(hours=5)).date(), (t1 - dt.timedelta(hours=5)).date()
            p0, p1 = (P.en(pid, d0), P.en(pid, d1)) if pid else (None, None)
            filas.append(dict(n=n, cambio=a1 / a0 - 1, precio=(p1 / p0 - 1) if (p0 and p1) else None))
    print(f"Pares de ofertas seguidas (48 h) desde el 01/10: {len(filas)}\n")
    for nombre, g in (("el precio bajo", [f for f in filas if f["precio"] is not None and f["precio"] < 0]),
                      ("el precio subio", [f for f in filas if f["precio"] is not None and f["precio"] > 0]),
                      ("el precio no cambio", [f for f in filas if f["precio"] == 0])):
        if g:
            c = [f["cambio"] for f in g]
            print(f"   {nombre:20} n={len(g):>3}  oferta nueva / vieja: mediana {st.median(c):+.1%}"
                  f"  (precio {st.median(f['precio'] for f in g):+.1%});  peor {min(c):+.1%}")
