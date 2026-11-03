"""
E79: E65/E66 fuera de muestra. Para una jornada N: la titularidad de FF de
la vispera (la_titularidad_del_dia.jsonl, dia DIA_FF) y lo sabido tras la
N-1 (puntos_por_jornada) contra lo que paso en la N:
  - cuanto juega cada tramo de FF y cuantos puntos hace (sobre sus pts/p)
  - la vara de Pepe (ppp x FF/100), la curva calibrada de E65/E66, FF sola,
    puntos por partido y precio: Spearman y nivel medio.
Fuera los equipos sin nadie con un partido mas (partido fuera de la foto o
aplazado).

Uso:  python3 lab/puntos/vara_jornada.py N DIA_FF      (p.ej. 11 2026-10-30)
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/puntos"))
from que_predice_puntos import spearman  # noqa: E402

LIBRO = RAIZ / "data/intelligence/puntos_por_jornada.jsonl"
TIT = RAIZ / "data/intelligence/la_titularidad_del_dia.jsonl"
FOTO = RAIZ / "data/fotos/2026-09-18.json"
PUNTOS = [(0, 0.1), (15, 0.25), (40, 0.85), (55, 1.0), (70, 1.1), (95, 1.15), (100, 1.15)]  # E65/E66


def curva(t):
    for (x0, y0), (x1, y1) in zip(PUNTOS, PUNTOS[1:]):
        if x0 <= t <= x1:
            return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
    return 1.15


if __name__ == "__main__":
    N, DIA = int(sys.argv[1]), sys.argv[2]
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    eq = {str(p["id"]): p["team_id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    ff = [json.loads(l) for l in open(TIT) if json.loads(l)["dia"] <= DIA][-1]
    print(f"J{N} con la FF del {ff['dia']}")
    ff = ff["ff"]
    a, b = L[N - 1], L[N]
    jugaron = defaultdict(int)
    for pid in b:
        if pid in a and b[pid][1] > a[pid][1]:
            jugaron[eq.get(pid)] += 1
    filas = []
    for pid, v in ff.items():
        if not v or v[0] is None or pid not in a or pid not in b or not jugaron.get(eq.get(pid)):
            continue
        pts, pj, precio = a[pid]
        filas.append(dict(ff=v[0], jugo=b[pid][1] > pj, y=b[pid][0] - pts, ppp=pts / pj if pj else None,
                          precio=precio, pj=pj))
    print(f"\n   FF          n    jugo")
    for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 80), (80, 101)):
        g = [f for f in filas if lo <= f["ff"] < hi]
        if g:
            print(f"   {lo:>3}-{min(hi,100):<3}%  {len(g):>4}   {sum(f['jugo'] for f in g)/len(g):4.0%}")
    h = [f for f in filas if f["pj"] >= 3]
    for f in h:
        f["vara"] = f["ppp"] * f["ff"] / 100
        f["cal"] = f["ppp"] * curva(f["ff"])
    y = [f["y"] for f in h]
    print(f"\n   (3+ partidos antes, n = {len(h)})  nivel real {sum(y)/len(y):.2f}"
          f" | vara {sum(f['vara'] for f in h)/len(h):.2f} | curva E65/E66 {sum(f['cal'] for f in h)/len(h):.2f}")
    for k, n in (("ff", "FF sola"), ("vara", "vara de Pepe"), ("cal", "curva calibrada"), ("ppp", "pts/partido"), ("precio", "precio")):
        print(f"   Spearman {n:16} {spearman([f[k] for f in h], y):+.3f}")
    print("\n   FF          n    vara   curva   real")
    for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 80), (80, 101)):
        g = [f for f in h if lo <= f["ff"] < hi]
        if g:
            print(f"   {lo:>3}-{min(hi,100):<3}%  {len(g):>4}   {sum(f['vara'] for f in g)/len(g):4.2f}"
                  f"   {sum(f['cal'] for f in g)/len(g):4.2f}   {sum(f['y'] for f in g)/len(g):4.2f}")
    print("\n   factor medido (puntos reales / pts por partido), para recalibrar:")
    for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 80), (80, 101)):
        g = [f for f in h if lo <= f["ff"] < hi]
        if g:
            print(f"   {lo:>3}-{min(hi,100):<3}%  x{sum(f['y'] for f in g)/sum(f['ppp'] for f in g):.2f}")
