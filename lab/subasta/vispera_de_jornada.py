"""
E57: ¿hay menos pelea en las subastas que se resuelven poco antes de una
jornada? (hipotesis del gestor del 23/10: Boye y Gaya, sin rival, la
vispera; «los rivales en rojo no pujan fuerte la vispera»).

Del tablon: cada subasta del Computer (se resuelve en el reset de las
07:00), las horas hasta el siguiente roundStarted, cuantos pujaron y la
prima del ganador sobre el precio de la vispera. Por tramos de horas.

Uso:  python3 lab/subasta/vispera_de_jornada.py
"""
import bisect
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
    ev = json.load(open(TABLON))
    inicios = sorted(e["date"] for e in ev if e["type"] == "roundStarted")
    P = Precios()
    filas, vistos = [], set()
    for e in ev:
        if e["type"] != "market":
            continue
        for x in e["content"]:
            t = x.get("date", e["date"])
            if (x["player"], x["amount"]) in vistos:
                continue
            vistos.add((x["player"], x["amount"]))
            i = bisect.bisect_right(inicios, t)
            if i >= len(inicios):
                continue
            horas = (inicios[i] - t) / 3600
            d = dia_de_mercado(t)
            p1, p2 = P.en(x["player"], d - D), P.en(x["player"], d - 2 * D)
            if not p1:
                continue
            filas.append(dict(horas=horas, pujadores=len(x.get("bids") or []) + 1,
                              prima=x["amount"] / p1 - 1, sube=(pct(p1, p2) or 0) > 0, precio=p1))
    print(f"Subastas con precio y jornada por delante: {len(filas)}\n")
    print("  horas a la jornada      n   con pelea   pujadores   prima ganador (mediana)   solo las que suben: n / pelea")
    for lo, hi in ((0, 24), (24, 48), (48, 96), (96, 9999)):
        g = [f for f in filas if lo <= f["horas"] < hi]
        if not g:
            continue
        s = [f for f in g if f["sube"]]
        print(f"   {lo:>3}-{hi if hi < 9999 else '+':>4}            {len(g):>4}     {sum(f['pujadores'] > 1 for f in g)/len(g):4.0%}"
              f"       {st.mean(f['pujadores'] for f in g):4.2f}       {st.median(f['prima'] for f in g):+6.1%}"
              f"                 {len(s):>3} / {sum(f['pujadores'] > 1 for f in s)/len(s) if s else 0:4.0%}")
    g = [f for f in filas if f["horas"] < 24 and f["precio"] >= 3e6]
    print(f"\nA menos de 24 h y de 3 M o mas: n={len(g)}, con pelea {sum(f['pujadores'] > 1 for f in g)}")
