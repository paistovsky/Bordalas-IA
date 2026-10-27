"""
E66: E53 y E65 fuera de muestra con la J10. Con lo que se sabia antes de
la J10 (foto tras la J9: puntos, partidos, precio; FF del 23/10), ¿que
predice mejor los puntos de la J10?
  - puntos por partido
  - precio (E53)
  - la vara de Pepe: pts/partido x FF/100
  - la vara calibrada de E65 (x0,25 / x0,85 / x1,0 / x1,1)  [OJO: E65 se
    saco de esta misma J10; aqui solo se ve si el orden cambia]
  - precio x factor de FF
Fuera los equipos sin nadie con un partido mas en la foto de la J10.

Uso:  python3 lab/puntos/vara_j10.py
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


def factor(ff):
    return 0.25 if ff < 30 else 0.85 if ff < 50 else 1.0 if ff < 60 else 1.1


if __name__ == "__main__":
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    eq = {str(p["id"]): p["team_id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    ff = [json.loads(l) for l in open(TIT) if json.loads(l)["dia"] <= "2026-10-23"][-1]["ff"]
    jugaron = defaultdict(int)
    for pid in L[10]:
        if pid in L[9] and L[10][pid][1] > L[9][pid][1]:
            jugaron[eq.get(pid)] += 1
    filas = []
    for pid, (pts, pj, precio) in L[9].items():
        if pid not in L[10] or pj < 3 or not jugaron.get(eq.get(pid)) or not ff.get(pid) or ff[pid][0] is None:
            continue
        t = ff[pid][0]
        ppp = pts / pj
        filas.append(dict(y=L[10][pid][0] - pts, ppp=ppp, precio=precio, vara=ppp * t / 100,
                          calibrada=ppp * factor(t), precio_ff=precio * factor(t), ff=t))
    y = [f["y"] for f in filas]
    print(f"Jugadores (3+ partidos, con FF, equipo en la foto): n = {len(filas)}\n")
    for k, nombre in (("ppp", "puntos por partido"), ("precio", "precio"), ("ff", "FF sola"),
                      ("vara", "vara de Pepe (ppp x FF/100)"), ("calibrada", "vara calibrada E65"),
                      ("precio_ff", "precio x factor de FF")):
        print(f"   Spearman {nombre:30} -> puntos J10: {spearman([f[k] for f in filas], y):+.3f}")

    print("\nMezclas (rango de FF + peso x rango de pts/partido):")

    def rangos(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for k, i in enumerate(o):
            r[i] = k
        return r
    rf, rp, rq = rangos([f["ff"] for f in filas]), rangos([f["ppp"] for f in filas]), rangos([f["precio"] for f in filas])
    for w in (0.25, 0.5, 1.0):
        print(f"   FF + {w} x pts/partido: {spearman([a + w * b for a, b in zip(rf, rp)], y):+.3f}"
              f"   |   FF + {w} x precio: {spearman([a + w * b for a, b in zip(rf, rq)], y):+.3f}")
    print("\nNivel (media de puntos J10) por tramo de FF, para la vara calibrada:")
    for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 80), (80, 101)):
        g = [f for f in filas if lo <= f["ff"] < hi]
        if g:
            print(f"   {lo:>3}-{min(hi,100):<3}%  n={len(g):>3}  vara {sum(f['vara'] for f in g)/len(g):4.2f}"
                  f"  calibrada {sum(f['calibrada'] for f in g)/len(g):4.2f}  real {sum(f['y'] for f in g)/len(g):4.2f}")

    PUNTOS = [(0, 0.1), (15, 0.25), (40, 0.85), (55, 1.0), (70, 1.1), (95, 1.15), (100, 1.15)]

    def curva(t):
        for (x0, y0), (x1, y1) in zip(PUNTOS, PUNTOS[1:]):
            if x0 <= t <= x1:
                return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
        return 1.15
    cont = [f["ppp"] * curva(f["ff"]) for f in filas]
    print(f"\nVara con curva continua (misma calibracion, sin escalones): Spearman {spearman(cont, y):+.3f}")
    print(f"   nivel medio: vara curva {sum(cont)/len(cont):.2f}, real {sum(y)/len(y):.2f}, vara de Pepe {sum(f['vara'] for f in filas)/len(filas):.2f}")
