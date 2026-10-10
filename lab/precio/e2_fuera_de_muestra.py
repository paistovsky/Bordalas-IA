"""
E32: E2 fuera de muestra con un partido de la J8.

Compara dos fotos de ciclo (status.json): una ANTES del partido y otra
DESPUES del reset siguiente. Los que tienen un partido mas son los que
jugaron; sus puntos de ese partido y su cambio de precio en ese reset
(`price_increment` de la segunda foto) contra los que no jugaron.

Uso:  python3 -I lab/precio/e2_fuera_de_muestra.py ANTES.json DESPUES.json
"""
import json
import statistics
import sys

if __name__ == "__main__":
    a = {p["id"]: p for p in json.load(open(sys.argv[1]))["todaLaLiga"]["players"]}
    b = {p["id"]: p for p in json.load(open(sys.argv[2]))["todaLaLiga"]["players"]}
    jug, resto = [], []
    for i, p in b.items():
        q = a.get(i)
        if not q or not p.get("price"):
            continue
        inc = (p.get("price_increment") or 0) / p["price"] * 100
        if (p["played"] or 0) > (q["played"] or 0):
            jug.append((p["points"] - (q["points"] or 0), inc, p["name"], (q.get("price_increment") or 0) > 0))
        else:
            resto.append(inc)
    for u, nom in ((5, "5+ pts"), (None, "4 o menos")):
        rs = [x for x in jug if not x[3] and ((x[0] >= 5) if u else (x[0] < 5))]
        print(f"   jugaron, {nom}, no venian subiendo: {sum(x[1] > 0 for x in rs)}/{len(rs)} suben")
        for x in sorted(rs, reverse=True):
            print(f"      {x[2]:<20} {x[0]:3d} pts  {x[1]:+5.1f}%")
    print(f"   no jugaron: n={len(resto)}  suben {sum(r > 0 for r in resto)}  mediana {statistics.median(resto):+.2f}%")
