"""
E49: E41 fuera de muestra. E41 (15/10 11:16) midio, con el tablon hasta
ese dia, que la pelea y la prima del ganador se ven en el precio de la
vispera. Aqui solo las subastas del Computer resueltas DESPUES del 15/10
(dia de mercado >= 15/10), mas las pujas de Pepe de esos dias.

Uso:  python3 lab/subasta/pelea_fuera_de_muestra.py [AAAA-MM-DD]
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import PEPE, TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)

if __name__ == "__main__":
    desde = dt.date.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-10-15")
    P = Precios()
    filas, vistos = [], set()
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            d = dia_de_mercado(x.get("date", e["date"]))
            if d < desde or (x["player"], x["amount"]) in vistos:
                continue
            vistos.add((x["player"], x["amount"]))
            p1, p2 = P.en(x["player"], d - D), P.en(x["player"], d - 2 * D)
            if not (p1 and p2):
                continue
            filas.append(dict(dia=d, pelea=bool(x.get("bids")), prima=x["amount"] / p1 - 1,
                              t1=pct(p1, p2), pepe=x["to"]["id"] == PEPE,
                              pepe_pujo=x["to"]["id"] == PEPE or any(b["user"]["id"] == PEPE for b in x.get("bids") or [])))
    print(f"Subastas del Computer desde {desde}: {len(filas)} (con pelea {sum(f['pelea'] for f in filas)})\n")
    E41 = {"no subio": (0.13, 0.026), "subio < 2 %": (0.64, 0.072), "subio >= 2 %": (0.83, 0.162)}
    for nombre, g in (("no subio", [f for f in filas if f["t1"] <= 0]),
                      ("subio < 2 %", [f for f in filas if 0 < f["t1"] < 0.02]),
                      ("subio >= 2 %", [f for f in filas if f["t1"] >= 0.02])):
        if not g:
            continue
        pel = [f for f in g if f["pelea"]]
        prima = st.median(f["prima"] for f in pel) if pel else None
        ant = E41[nombre]
        print(f"  {nombre:13} n={len(g):>3}  con pelea {len(pel)/len(g):4.0%} (E41 {ant[0]:.0%})"
              f"   paga el ganador {prima:+.1%} (E41 {ant[1]:+.1%})" if prima is not None else
              f"  {nombre:13} n={len(g):>3}  con pelea 0 %")
    mias = [f for f in filas if f["pepe_pujo"]]
    print(f"\nDonde pujo Pepe: {len(mias)}")
    for f in mias:
        print(f"   {f['dia']}  vispera {f['t1']:+.1%}  {'GANADA' if f['pepe'] else 'perdida'}  ganador {f['prima']:+.1%}")
