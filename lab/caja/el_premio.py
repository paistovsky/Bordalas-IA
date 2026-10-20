"""
E52: la formula del premio de jornada. E16 supuso 30.000 EUR por punto;
en la J9 el ultimo (27 puntos) cobro 1.310.000 (48.500 por punto). ¿Hay un
suelo, o un plus por puesto?

Del tablon: cada roundFinished con puntos, bonus y puesto de cada manager.

Uso:  python3 lab/caja/el_premio.py
"""
import datetime as dt
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"

if __name__ == "__main__":
    vistas = set()
    filas = []
    for e in json.load(open(TABLON)):
        if e["type"] != "roundFinished":
            continue
        r = e["content"]["round"]
        if r["id"] in vistas:
            continue
        vistas.add(r["id"])
        res = sorted(e["content"]["results"], key=lambda x: -x["points"])
        print(f"{r['name']} ({dt.datetime.utcfromtimestamp(e['date']):%d/%m}):")
        for puesto, x in enumerate(res, 1):
            x.setdefault("bonus", 0)
            extra = x["bonus"] - 30_000 * x["points"]
            filas.append((puesto, len(res), x["points"], x["bonus"], extra))
            print(f"   {puesto}. {x['user']['name'][:14]:14} {x['points']:>3} pts  {x['bonus']:>10,}"
                  f"  = 30.000 x pts {'+' if extra >= 0 else '-'} {abs(extra):,}")
    print("\nLo que no es 30.000 por punto:")
    raras = [f for f in filas if f[4] != 0]
    for p, n, pts, b, ex in raras:
        print(f"   puesto {p} de {n}, {pts} pts, cobra {b:,} (extra {ex:+,}; si fuera {b - ex:,})")
    print(f"\n{len(filas) - len(raras)} de {len(filas)} premios son exactamente 30.000 x puntos")
