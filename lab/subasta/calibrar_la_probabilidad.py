"""
E81: ¿acierta la probabilidad de E80? Para cada puja de Pepe en el tablon
desde el 15/10: con SOLO las subastas anteriores a ese dia, la fraccion de
subastas parecidas (misma clase de subida la vispera: no sube / sube <2 % /
sube >=2 %) cuyo ganador pago menos que la prima de Pepe. Contra lo que
paso. Brier y aciertos por tramo.

Uso:  python3 lab/subasta/calibrar_la_probabilidad.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import PEPE, TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)


def clase(t):
    return "no sube" if t <= 0 else "<2%" if t < 0.02 else ">=2%"


if __name__ == "__main__":
    P = Precios()
    subastas, vistos = [], set()
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            if (x["player"], x["amount"]) in vistos:
                continue
            vistos.add((x["player"], x["amount"]))
            d = dia_de_mercado(x.get("date", e["date"]))
            p1, p2 = P.en(x["player"], d - D), P.en(x["player"], d - 2 * D)
            if not (p1 and p2):
                continue
            pujas = [(x["to"]["id"], x["amount"])] + [(b["user"]["id"], b["amount"]) for b in x.get("bids") or []]
            subastas.append(dict(d=d, c=clase(pct(p1, p2) or 0), ganadora=x["amount"] / p1 - 1,
                                 pepe=[a / p1 - 1 for u, a in pujas if u == PEPE], gana_pepe=x["to"]["id"] == PEPE,
                                 rivales=[a / p1 - 1 for u, a in pujas if u != PEPE]))
    filas = []
    for s in subastas:
        if s["d"] < dt.date(2026, 10, 15) or not s["pepe"]:
            continue
        k = s["pepe"][0]
        # lo que pago el mejor rival en subastas anteriores de la misma clase (0 si no hubo rival)
        prev = [max(t["rivales"], default=-1) for t in subastas if t["d"] < s["d"] and t["c"] == s["c"]]
        p = sum(r < k for r in prev) / len(prev) if prev else None
        if p is not None:
            filas.append((s["d"], s["c"], k, p, s["gana_pepe"]))
    print(f"Pujas de Pepe desde el 15/10 con historial: {len(filas)}\n")
    for d, c, k, p, g in filas:
        print(f"   {d}  {c:8} prima {k:+6.1%}  P(ganar) {p:4.0%}  -> {'GANADA' if g else 'perdida'}")
    brier = sum((p - g) ** 2 for *_, p, g in filas) / len(filas)
    base = sum(g for *_, g in filas) / len(filas)
    print(f"\nBrier {brier:.3f} (el de decir siempre {base:.0%}: {sum((base - g) ** 2 for *_, g in filas)/len(filas):.3f})")
    print(f"Prob. media predicha {sum(f[3] for f in filas)/len(filas):.0%}, ganadas de verdad {base:.0%}")
