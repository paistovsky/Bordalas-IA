"""
E83: ¿puede ganar una puja que queda por debajo del precio NUEVO (el que el
jugador tiene tras el reset que resuelve la subasta)? Caso del 05/11:
Loureiro, nuestra puja 798.000 quedo un 3,9 % por debajo de su precio
nuevo y lo gano Pollo a 847.000.

Del tablon: para cada subasta del Computer, la puja ganadora frente al
precio de la vispera (P(d-1)) y al precio nuevo (P(d)); y las pujas de
Pepe que quedaron por debajo del precio nuevo.

Uso:  python3 lab/subasta/bajo_el_precio_nuevo.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import PEPE, TABLON, Precios, dia_de_mercado  # noqa: E402

D = dt.timedelta(days=1)

if __name__ == "__main__":
    P = Precios()
    gan, pepe, vistos = [], [], set()
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            if (x["player"], x["amount"]) in vistos:
                continue
            vistos.add((x["player"], x["amount"]))
            d = dia_de_mercado(x.get("date", e["date"]))
            p_viejo, p_nuevo = P.en(x["player"], d - D), P.en(x["player"], d)
            if not (p_viejo and p_nuevo):
                continue
            gan.append((x["amount"] / p_nuevo - 1, p_nuevo > p_viejo, x["to"]["id"] == PEPE))
            pujas = [(x["to"]["id"], x["amount"])] + [(b["user"]["id"], b["amount"]) for b in x.get("bids") or []]
            for u, a in pujas:
                if u == PEPE:
                    pepe.append((d, a / p_nuevo - 1, x["to"]["id"] == PEPE, p_nuevo > p_viejo))
    sube = [g for g in gan if g[1]]
    print(f"Subastas: {len(gan)}; el precio subio en el reset que la resolvio: {len(sube)}")
    print(f"   ganadoras por debajo del precio nuevo: {sum(g[0] < 0 for g in gan)} de {len(gan)}"
          f"  (de las que subian: {sum(g[0] < 0 for g in sube)} de {len(sube)})")
    print(f"   la mas baja: {min(g[0] for g in gan):+.1%} sobre el precio nuevo")
    print(f"\nPujas de Pepe: {len(pepe)}; por debajo del precio nuevo: {sum(p[1] < 0 for p in pepe)}"
          f", de ellas ganadas: {sum(p[1] < 0 and p[2] for p in pepe)}")
    for d, k, g, s in pepe:
        if k < 0:
            print(f"   {d}  {k:+.1%} sobre el precio nuevo  {'GANADA' if g else 'perdida'}  {'(subio)' if s else ''}")
