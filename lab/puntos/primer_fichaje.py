"""
E16: el primer fichaje despues de la J8. ¿Cuanta caja habra y en que se
gasta para sacar mas puntos?

1) Cuanto paga Biwenger por jornada: del tablon (`roundFinished`), puntos
   y premio de cada manager por jornada.
2) El hueco mas flojo del once: puntos esperados por jornada = puntos por
   partido x titularidad, de la plantilla en la foto de un ciclo.
3) Que defensas saca el Computer (1-3 M, titularidad >= 60 %), de las
   fotos de los ciclos (carpetas por argumento: artefactos de Actions).

Uso:  python3 lab/puntos/primer_fichaje.py FOTO_DE_HOY.json [CARPETA ...]
"""
import glob
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PEPE = 14175949


def premios():
    vistos = set()
    print("1) Lo que paga cada jornada (tablon):")
    pepe = []
    for e in json.load(open(RAIZ / "data/rival_intelligence/board_events.json")):
        if e["type"] != "roundFinished" or e["event_id"] in vistos:
            continue
        nombre = e["content"]["round"]["name"]
        if nombre in vistos:
            continue
        vistos.add(nombre)
        for x in e["content"]["results"]:
            if x["user"]["id"] == PEPE and x.get("bonus"):
                pepe.append((nombre, x["points"], x["bonus"]))
    for n, p, b in pepe:
        print(f"   {n:<22} {p:3d} pts -> {b:>10,} EUR  ({b/p:,.0f} por punto)")
    return pepe


def esperado(p):
    pj = p.get("played") if "played" in p else (p.get("played_home") or 0) + (p.get("played_away") or 0)
    return (p.get("points") or 0) / max(pj or 0, 1) * (p.get("starter_probability") or 0) / 100


if __name__ == "__main__":
    pepe = premios()
    hoy = json.load(open(sys.argv[1]))
    print("\n2) La plantilla de hoy, por puntos esperados por jornada (media x titularidad):")
    for p in sorted(hoy["roster"]["players"], key=esperado):
        print(f"   {p['name']:<18} pos {p['position']}  {esperado(p):4.2f}  precio {p['price']/1e6:5.2f} M")
    vis = {}
    for c in sys.argv[2:]:
        for r in sorted(glob.glob(os.path.join(c, "*.json"))):
            if os.path.getsize(r) < 10_000:
                continue
            for t in json.load(open(r))["acquisition"]["targets"]:
                if t["seller_kind"] == "COMPUTER" and t["position"] == 2 and t["status"] == "ok" \
                        and t["market_price"] <= 3.2e6 and (t.get("starter_probability") or 0) >= 60:
                    vis[t["name"]] = (os.path.basename(r)[:10], t["market_price"], esperado(t))
    print(f"\n3) Defensas que saco el Computer (<= 3,2 M, titular >= 60 %), {len(vis)} distintos:")
    for n, (dia, precio, e) in sorted(vis.items(), key=lambda x: -x[1][2]):
        print(f"   {dia}  {n:<16} {precio/1e6:4.2f} M  esperado {e:4.2f} pts/jornada  ({e/(precio/1e6):.2f} por millon)")
