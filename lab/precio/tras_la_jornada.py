"""
E63: ¿el precio reacciona tarde a los puntos? Puntos de cada jugador en la
J8 y en la J9 (fotos de puntos_por_jornada) contra el cambio de precio en
cada dia de mercado alrededor de la jornada. Si la correlacion sigue alta
DESPUES de acabar la jornada (del martes en adelante), comprar el martes a
los que puntuaron mucho seria una ventaja.

Uso:  python3 lab/precio/tras_la_jornada.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
sys.path.insert(0, str(RAIZ / "lab/puntos"))
from viajes import Precios  # noqa: E402
from que_predice_puntos import spearman  # noqa: E402

LIBRO = RAIZ / "data/intelligence/puntos_por_jornada.jsonl"
FOTO = RAIZ / "data/fotos/2026-09-18.json"
FUERA = {1, 70, 10}  # aplazados y fotos a medias (E43/E45)
# jornada: (antes, despues, primer dia del bloque, ultimo dia del bloque)
J = {8: (7, 8, dt.date(2026, 10, 9), dt.date(2026, 10, 12)),
     9: (8, 9, dt.date(2026, 10, 16), dt.date(2026, 10, 19)),
     10: (9, 10, dt.date(2026, 10, 23), dt.date(2026, 10, 26))}
DIAS_DESPUES = int(__import__("os").environ.get("DIAS_DESPUES", "7"))

if __name__ == "__main__":
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    equipo = {str(p["id"]): p["team_id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    P = Precios()
    for j, (a, b, ini, fin) in J.items():
        pts = {pid: L[b][pid][0] - L[a][pid][0] for pid in L[b]
               if pid in L[a] and L[b][pid][1] - L[a][pid][1] == 1 and equipo.get(pid) not in FUERA}
        print(f"J{j}: {len(pts)} jugadores que jugaron (bloque {ini:%d/%m}-{fin:%d/%m})")
        for k in range(-1, 8):
            d = ini + dt.timedelta(days=k)
            xs, ys = [], []
            for pid, p in pts.items():
                p0, p1 = P.en(int(pid), d - dt.timedelta(days=1)), P.en(int(pid), d)
                if p0 and p1:
                    xs.append(p)
                    ys.append(p1 / p0 - 1)
            marca = " <- tras el ultimo partido" if d > fin else ""
            print(f"   precio del {d:%a %d/%m}: Spearman puntos-cambio {spearman(xs, ys):+.2f} (n={len(xs)}){marca}")

    # ¿Añaden algo los puntos a «subio ayer»? Compra el miercoles al precio del
    # martes (la puja del martes se resuelve el miercoles), vende el lunes.
    print(f"\nComprar al precio del martes y mirar {DIAS_DESPUES - 1} dias despues:")
    for j, (a, b, ini, fin) in J.items():
        mar, lun = fin + dt.timedelta(days=1), fin + dt.timedelta(days=DIAS_DESPUES)
        filas = []
        for pid in L[b]:
            if pid not in L[a] or L[b][pid][1] - L[a][pid][1] != 1 or equipo.get(pid) in FUERA:
                continue
            p_lun_j, p_mar, p_sig = (P.en(int(pid), d) for d in (fin, mar, lun))
            if p_lun_j and p_mar and p_sig:
                filas.append((L[b][pid][0] - L[a][pid][0], p_mar > p_lun_j, p_sig / p_mar - 1))
        import statistics as st
        for nombre, g in (("subio el martes, 8+ pts", [f for f in filas if f[1] and f[0] >= 8]),
                          ("subio el martes, <8 pts", [f for f in filas if f[1] and f[0] < 8]),
                          ("no subio, 8+ pts", [f for f in filas if not f[1] and f[0] >= 8]),
                          ("no subio, <8 pts", [f for f in filas if not f[1] and f[0] < 8])):
            if g:
                print(f"   J{j} {nombre:24} n={len(g):>3}  despues: mediana {st.median(f[2] for f in g):+.1%}")
