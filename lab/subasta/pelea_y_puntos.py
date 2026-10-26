"""
E64: ¿los rivales ya pujan por los que acaban de puntuar mucho? (E63: el
precio va una semana por detras de los puntos). Para cada subasta del
Computer resuelta en los 7 dias tras la J8 y la J9, los puntos que hizo el
jugador en esa jornada: pelea, prima del ganador y quien gano.

Uso:  python3 lab/subasta/pelea_y_puntos.py
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import TABLON, Precios, dia_de_mercado  # noqa: E402

LIBRO = RAIZ / "data/intelligence/puntos_por_jornada.jsonl"
D = dt.timedelta(days=1)
J = {8: (7, 8, dt.date(2026, 10, 13)), 9: (8, 9, dt.date(2026, 10, 20))}  # martes tras la jornada

if __name__ == "__main__":
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    P = Precios()
    filas = []
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            d = dia_de_mercado(x.get("date", e["date"]))
            for j, (a, b, mar) in J.items():
                if mar <= d < mar + 7 * D:
                    pid = str(x["player"])
                    if pid in L[a] and pid in L[b]:
                        pts = L[b][pid][0] - L[a][pid][0] if L[b][pid][1] > L[a][pid][1] else None
                        p1 = P.en(x["player"], d - D)
                        if p1:
                            filas.append(dict(j=j, pts=pts, pelea=bool(x.get("bids")), prima=x["amount"] / p1 - 1,
                                              gana=x["to"]["name"]))
    print(f"Subastas en la semana tras la J8 y la J9: {len(filas)}\n")
    for nombre, g in (("8+ pts en la jornada", [f for f in filas if f["pts"] is not None and f["pts"] >= 8]),
                      ("1-7 pts", [f for f in filas if f["pts"] is not None and 0 < f["pts"] < 8]),
                      ("<= 0 pts", [f for f in filas if f["pts"] is not None and f["pts"] <= 0]),
                      ("no jugo", [f for f in filas if f["pts"] is None])):
        if g:
            pel = [f["prima"] for f in g if f["pelea"]]
            print(f"   {nombre:20} n={len(g):>3}  con pelea {sum(f['pelea'] for f in g)/len(g):4.0%}"
                  f"  prima ganadora {st.median(f['prima'] for f in g):+6.1%}"
                  f"  (con pelea {st.median(pel) if pel else 0:+.1%})  ganan: "
                  + ", ".join(sorted({f['gana'][:8] for f in g})))
