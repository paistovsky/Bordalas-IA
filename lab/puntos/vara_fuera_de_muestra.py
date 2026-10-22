"""
E53: la vara de puntos fuera de muestra. Con lo que se sabia tras la J7
(foto del 23/09: puntos, partidos y precio de cada jugador), ¿que predice
mejor los puntos que hizo en la J8 y la J9 (foto del 19/10 menos foto del
23/09)? Candidatos: puntos por partido, puntos totales, precio, y los
puntos por partido «encogidos» hacia la media (pocos partidos = poca fe).

Ojo: la foto de la J9 se tomo a las 23:10 del lunes; puede faltar el
Getafe-Rayo de esa noche, y el Rayo-Athletic de la J8 no se jugo (E43).
Se quitan Getafe, Rayo y Athletic para no medir huecos.

Uso:  python3 lab/puntos/vara_fuera_de_muestra.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/puntos"))
from que_predice_puntos import spearman  # noqa: E402

LIBRO = RAIZ / "data/intelligence/puntos_por_jornada.jsonl"
FOTO = RAIZ / "data/fotos/2026-09-18.json"
FUERA = {1, 70}  # Athletic, Rayo (E45/E43); Getafe abajo por nombre de equipo si se sabe

if __name__ == "__main__":
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    a, b = L[7], L[9]
    equipo = {str(p["id"]): p["team_id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    filas = []
    for pid, (pts, pj, precio) in a.items():
        if pid not in b or pj < 3 or equipo.get(pid) in FUERA:
            continue
        pts2, pj2, _ = b[pid]
        filas.append(dict(ppp=pts / pj, total=pts, precio=precio, pj=pj,
                          luego=pts2 - pts, jugo=pj2 - pj))
    media = sum(f["total"] for f in filas) / sum(f["pj"] for f in filas)
    K = 3
    for f in filas:
        f["encogido"] = (f["total"] + K * media) / (f["pj"] + K)
    y = [f["luego"] for f in filas]
    print(f"Jugadores con 3+ partidos tras la J7 (sin Athletic ni Rayo): n = {len(filas)}")
    print(f"Puntos en J8+J9: media {sum(y)/len(y):.1f}\n")
    for k in ("ppp", "encogido", "total", "precio"):
        print(f"   Spearman {k:9} -> puntos J8+J9: {spearman([f[k] for f in filas], y):+.3f}")
    jug = [f for f in filas if f["jugo"] >= 2]
    print(f"\nSolo los que jugaron las dos (n = {len(jug)}):")
    for k in ("ppp", "encogido", "precio"):
        print(f"   Spearman {k:9} -> puntos J8+J9: {spearman([f[k] for f in jug], [f['luego'] for f in jug]):+.3f}")
    print(f"\nJugaron 0, 1 o 2 de las dos: {[sum(f['jugo'] == n for f in filas) for n in (0, 1, 2)]}")

    def rangos(v):
        orden = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for k, i in enumerate(orden):
            r[i] = k
        return r
    for nombre, g in (("todos", filas), ("jugaron las dos", jug)):
        rp, rq = rangos([f["precio"] for f in g]), rangos([f["encogido"] for f in g])
        combo = [x + z for x, z in zip(rp, rq)]
        print(f"   {nombre}: precio + encogido (rangos sumados): {spearman(combo, [f['luego'] for f in g]):+.3f}")
    print("\nPor posicion (todos):")
    pos = {str(p["id"]): p["position"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    for k in (1, 2, 3, 4):
        g = [f for f, pid in zip(filas, [p for p, v in a.items() if p in b and v[1] >= 3 and equipo.get(p) not in FUERA]) if pos.get(pid) == k]
        if len(g) > 10:
            print(f"   {'POR DEF MED DEL'.split()[k-1]} n={len(g):>3}  ppp {spearman([f['ppp'] for f in g], [f['luego'] for f in g]):+.2f}"
                  f"  precio {spearman([f['precio'] for f in g], [f['luego'] for f in g]):+.2f}")
