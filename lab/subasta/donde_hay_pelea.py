"""
E41: ¿se puede saber ANTES de pujar si una subasta del Computer tendra
pelea? Si si, la puja fuerte (+12 %, E37) solo se gasta donde hace falta;
en las que nadie pelea, +1 % basta y el +11 % de mas es dinero tirado.

Lo que Pepe sabe la vispera: precio, tendencia (cambio de 1 y 3 dias),
y si el jugador es caro. Del tablon: subastas del Computer con precio
(pelea = mas de un pujador). Para cada grupo: % con pelea y lo que paga
el ganador cuando la hay.

Uso:  python3 lab/subasta/donde_hay_pelea.py
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)

if __name__ == "__main__":
    P = Precios()
    filas, vistos = [], set()
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            if (x["player"], x["amount"]) in vistos:
                continue
            vistos.add((x["player"], x["amount"]))
            d = dia_de_mercado(x.get("date", e["date"]))
            p1, p2, p4 = (P.en(x["player"], d - k * D) for k in (1, 2, 4))
            if not (p1 and p2):
                continue
            filas.append(dict(pelea=bool(x.get("bids")), prima=x["amount"] / p1 - 1, precio=p1,
                              t1=pct(p1, p2) or 0, t3=pct(p1, p4) if p4 else None,
                              n=len(x.get("bids") or []) + 1))
    print(f"Subastas con precio: {len(filas)}, con pelea {sum(f['pelea'] for f in filas)}\n")

    def linea(nombre, rs):
        if not rs:
            return
        pel = [f for f in rs if f["pelea"]]
        prima = f"{st.median(f['prima'] for f in pel):+.1%}" if pel else "  -  "
        print(f"  {nombre:34} n={len(rs):>3}  con pelea {len(pel)/len(rs):4.0%}   prima ganadora (pelea) {prima}")

    print("Por precio:")
    for a, b in ((0, 0.5e6), (0.5e6, 1.5e6), (1.5e6, 3e6), (3e6, 99e6)):
        linea(f"{a/1e6:.1f}-{b/1e6:.1f} M", [f for f in filas if a <= f["precio"] < b])
    print("Por tendencia de la vispera:")
    linea("bajo", [f for f in filas if f["t1"] < 0])
    linea("quieto", [f for f in filas if f["t1"] == 0])
    linea("subio < 2 %", [f for f in filas if 0 < f["t1"] < 0.02])
    linea("subio >= 2 %", [f for f in filas if f["t1"] >= 0.02])
    print("Por tendencia de 3 dias:")
    linea("3 dias <= 0", [f for f in filas if f["t3"] is not None and f["t3"] <= 0])
    linea("3 dias 0-5 %", [f for f in filas if f["t3"] is not None and 0 < f["t3"] < 0.05])
    linea("3 dias >= 5 %", [f for f in filas if f["t3"] is not None and f["t3"] >= 0.05])
    print("Lo que interesa a la mejora del once (1,5 M o mas):")
    g = [f for f in filas if f["precio"] >= 1.5e6]
    linea("1,5 M+ y subio", [f for f in g if f["t1"] > 0])
    linea("1,5 M+ y no subio", [f for f in g if f["t1"] <= 0])

    print("\nSe gana pujando precio x (1+k), por tendencia de la vispera (todas, con y sin pelea):")
    print("                       +1 %   +3 %   +5 %   +8 %  +12 %")
    for nombre, rs in (("no subio", [f for f in filas if f["t1"] <= 0]),
                       ("subio < 2 %", [f for f in filas if 0 < f["t1"] < 0.02]),
                       ("subio >= 2 %", [f for f in filas if f["t1"] >= 0.02])):
        print(f"  {nombre:18}" + "".join(f"  {sum(f['prima'] < k for f in rs)/len(rs):4.0%} "
                                         for k in (0.01, 0.03, 0.05, 0.08, 0.12)) + f"  (n={len(rs)})")
