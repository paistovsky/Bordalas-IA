"""
E73: como terminan las pujas de cada manager y cuantas subastas se deciden
por poco. Hoy (31/10) Pepe gano a Dani Lorenzo por 15.050 sobre Luismi y
perdio a Macia por 20.190 contra Manzagool. Si cada rival tiene su manera
de redondear, la terminacion de la puja de Pepe puede ganar esas subastas
casi gratis.

Del tablon: todas las pujas (ganadoras y perdedoras) con su importe; la
terminacion (importe mod 10.000) por manager; y la diferencia entre la
ganadora y la segunda.

Uso:  python3 lab/subasta/terminaciones.py
"""
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"

if __name__ == "__main__":
    term = defaultdict(Counter)
    margenes = []
    vistos = set()
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            k = (x["player"], x["amount"])
            if k in vistos:
                continue
            vistos.add(k)
            pujas = [(x["to"]["name"], x["amount"])] + [(b["user"]["name"], b["amount"]) for b in x.get("bids") or []]
            for n, a in pujas:
                r = a % 10_000
                cls = ("...0.000" if r == 0 else "...9.900" if r == 9_900 else "...0.001/...1" if r in (1, 1_001) or a % 1000 == 1
                       else "...x.000" if r % 1000 == 0 else "otra")
                term[n[:12]][cls] += 1
            if len(pujas) > 1:
                importes = sorted((a for _, a in pujas), reverse=True)
                margenes.append(((importes[0] - importes[1]) / importes[1], x["to"]["name"][:12]))
    print("Terminaciones de las pujas, por manager:")
    for n, c in sorted(term.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        print(f"   {n:12} n={tot:>3}  " + "  ".join(f"{k} {v/tot:.0%}" for k, v in c.most_common()))
    m = sorted(x for x, _ in margenes)
    print(f"\nSubastas con pelea: {len(m)}; margen de la ganadora sobre la segunda: mediana {st.median(m):.1%}")
    for lim in (0.002, 0.005, 0.01, 0.02):
        print(f"   decididas por menos de un {lim:.1%}: {sum(x < lim for x in m)} ({sum(x < lim for x in m)/len(m):.0%})")
