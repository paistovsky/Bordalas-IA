"""
E80: ¿con que probabilidad gana una puja de +K % por uno que sube X % la
vispera? (Caso del 03/11: Adrian Nino, 4.909.900 = +12,1 %, sube ~4 % al
dia; se resuelve el mie 07:00, a 62 h de la J12.)

Del tablon: subastas del Computer de jugadores que subieron >= SUBE la
vispera (y, aparte, de 2 a 8 M); la prima que pago el ganador. P(ganar con
+K %) = fraccion de subastas cuyo ganador pago menos de K (sin contar
reacciones de los rivales).

Uso:  python3 lab/subasta/probabilidad_de_ganar.py [K=0.121] [SUBE=0.03]
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
    K = float(sys.argv[1]) if len(sys.argv) > 1 else 0.121
    SUBE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.03
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
            p1, p2 = P.en(x["player"], d - D), P.en(x["player"], d - 2 * D)
            if p1 and p2 and (pct(p1, p2) or 0) >= SUBE:
                filas.append(dict(prima=x["amount"] / p1 - 1, precio=p1, d=d, n=len(x.get("bids") or []) + 1))
    for nombre, g in (("todas", filas), ("de 2 a 8 M", [f for f in filas if 2e6 <= f["precio"] <= 8e6]),
                      ("desde el 15/10", [f for f in filas if f["d"] >= dt.date(2026, 10, 15)])):
        if g:
            pr = sorted(f["prima"] for f in g)
            print(f"   {nombre:15} n={len(g):>3}  prima del ganador: mediana {st.median(pr):+.1%}, p75 {pr[3*len(pr)//4]:+.1%}"
                  f"  ->  P(ganar con +{K:.1%}) = {sum(p < K for p in pr)/len(pr):.0%}")
