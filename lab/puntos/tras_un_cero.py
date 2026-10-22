"""
E54: ¿que pasa con un jugador que hace 0 puntos o menos en una jornada?
Es la base de «el parte vende» (vender por parte malo o <= 0 puntos,
apagado). Si el cero anuncia peores puntos y peor precio, venderlo rapido
gana; si es ruido, venderlo es regalar.

Datos: las tres fotos de puntos_por_jornada (tras J7, J8, J9): puntos de la
J8 = foto J8 - foto J7 (solo si jugo un partido mas), puntos de la J9 =
foto J9 - foto J8; precio en cada foto y una semana despues (historial).
Fuera Athletic, Rayo, Levante y Sevilla (partidos sin jugar o fuera de foto).

Uso:  python3 lab/puntos/tras_un_cero.py
"""
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

LIBRO = RAIZ / "data/intelligence/puntos_por_jornada.jsonl"
FOTO = RAIZ / "data/fotos/2026-09-18.json"
FUERA = {1, 70, 10}  # Athletic, Rayo, Levante (E43/E45); Sevilla abajo por jugadores

if __name__ == "__main__":
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    pl = json.load(open(FOTO))["todaLaLiga"]["players"]
    equipo = {str(p["id"]): p["team_id"] for p in pl}
    P = Precios()
    d8, d9 = dt.date(2026, 10, 13), dt.date(2026, 10, 20)
    filas = []
    for pid in L[9]:
        if pid not in L[8] or pid not in L[7] or equipo.get(pid) in FUERA:
            continue
        (a, ja, _), (b, jb, _), (c, jc, _) = L[7][pid], L[8][pid], L[9][pid]
        if jb - ja != 1:
            continue  # jugo la J8
        p0, p1 = P.en(int(pid), d8), P.en(int(pid), d9)
        filas.append(dict(j8=b - a, j9=(c - b) if jc - jb == 1 else None, antes=a / ja if ja else None,
                          dprecio=(p1 / p0 - 1) if (p0 and p1) else None))
    ceros = [f for f in filas if f["j8"] <= 0]
    resto = [f for f in filas if f["j8"] > 0]
    print(f"Jugaron la J8: {len(filas)}; con <= 0 puntos: {len(ceros)}\n")
    for nombre, g in (("<= 0 en la J8", ceros), ("> 0 en la J8", resto)):
        j9 = [f["j9"] for f in g if f["j9"] is not None]
        jugo9 = sum(f["j9"] is not None for f in g) / len(g)
        dp = [f["dprecio"] for f in g if f["dprecio"] is not None]
        ant = [f["antes"] for f in g if f["antes"] is not None]
        print(f"   {nombre:14} n={len(g):>3}  pts/partido antes {st.mean(ant):4.1f}  juega la J9 {jugo9:4.0%}"
              f"  pts en la J9 {st.mean(j9):4.1f} (mediana {st.median(j9):.0f})  precio 13/10->20/10 {st.median(dp):+.1%}")
    # mismo nivel previo: emparejar por pts/partido antes
    print("\nCon el mismo nivel previo (pts/partido antes de la J8):")
    for lo, hi in ((0, 3), (3, 5), (5, 99)):
        for nombre, g in (("<= 0", ceros), ("> 0", resto)):
            h = [f for f in g if f["antes"] is not None and lo <= f["antes"] < hi and f["j9"] is not None]
            dp = [f["dprecio"] for f in g if f["antes"] is not None and lo <= f["antes"] < hi and f["dprecio"] is not None]
            if h:
                print(f"   antes {lo}-{hi if hi < 99 else '+'}  {nombre:5} n={len(h):>3}  J9 {st.mean(f['j9'] for f in h):4.1f}"
                      f"  precio {st.median(dp):+.1%}")
