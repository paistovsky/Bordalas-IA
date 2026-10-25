"""
E62: las ventas entre managers (punto 4 de la agenda: cuando conviene
vender a un manager). Del tablon: cada «transfer» con comprador y vendedor
manager; el precio pagado contra el precio de mercado de ese dia, y que
hizo el precio del jugador los 7 y 14 dias siguientes. Si el comprador paga
por encima y despues el precio baja, al vendedor le salio bien.

Uso:  python3 lab/ofertas/entre_managers.py
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import NOMBRES, PEPE, TABLON, Precios, dia_de_mercado  # noqa: E402

D = dt.timedelta(days=1)

if __name__ == "__main__":
    P = Precios()
    filas = []
    for e in json.load(open(TABLON)):
        if e["type"] != "transfer":
            continue
        for x in e["content"]:
            if "to" not in x:
                continue
            d = dia_de_mercado(e["date"])
            p0 = P.en(x["player"], d)
            if not p0:
                continue
            p7, p14 = P.en(x["player"], d + 7 * D), P.en(x["player"], d + 14 * D)
            filas.append(dict(dia=d, de=x["from"]["name"], a=x["to"]["name"], prima=x["amount"] / p0 - 1,
                              d7=(p7 / p0 - 1) if p7 else None, d14=(p14 / p0 - 1) if p14 else None,
                              pepe=PEPE in (x["from"]["id"], x["to"]["id"]), importe=x["amount"]))
    print(f"Ventas entre managers con precio: {len(filas)}\n")
    pr = [f["prima"] for f in filas]
    print(f"Prima pagada sobre el precio del dia: mediana {st.median(pr):+.1%}, p10 {sorted(pr)[len(pr)//10]:+.1%},"
          f" p90 {sorted(pr)[9*len(pr)//10]:+.1%}; por encima del precio {sum(p > 0 for p in pr)} de {len(pr)}")
    d7 = [f["d7"] for f in filas if f["d7"] is not None]
    d14 = [f["d14"] for f in filas if f["d14"] is not None]
    print(f"Precio del jugador despues: a 7 dias {st.median(d7):+.1%} (n={len(d7)}), a 14 dias {st.median(d14):+.1%} (n={len(d14)})")
    ganan = [f for f in filas if f["d7"] is not None]
    print(f"Le salio bien al vendedor (prima > subida a 7 dias): {sum(f['prima'] > f['d7'] for f in ganan)} de {len(ganan)}")
    print("\nCada una:")
    for f in sorted(filas, key=lambda f: f["dia"]):
        print(f"   {f['dia']}  {f['de'][:12]:12} -> {f['a'][:12]:12} {f['importe']:>10,}  prima {f['prima']:+6.1%}"
              f"  7d {f['d7']:+6.1%}" if f["d7"] is not None else
              f"   {f['dia']}  {f['de'][:12]:12} -> {f['a'][:12]:12} {f['importe']:>10,}  prima {f['prima']:+6.1%}")
