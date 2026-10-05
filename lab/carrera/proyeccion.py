"""
E20: la carrera. ¿Cuantos puntos por jornada deberia sacar el once de cada
manager con la plantilla de hoy, y quien parte con ventaja?

Datos: la foto de un ciclo de produccion (status.json; se pasa por
argumento: los artefactos caducan a los 2 dias). `rival_squads` trae la
plantilla de los 8 managers con estado y titularidad FF; `todaLaLiga`, los
puntos y partidos de cada jugador.

Vara: puntos esperados = puntos por partido x titularidad FF (E16; E17:
vale lo mismo que el total). Para cada manager, el mejor once con estado ok
en una formacion de Biwenger. Banquillo: lo que esperan sus suplentes.
Contraste: los puntos reales por jornada de cada uno (tablon) hasta la J7.

Uso:  python3 lab/carrera/proyeccion.py status.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FORMACIONES = [(3, 4, 3), (3, 5, 2), (4, 4, 2), (4, 3, 3), (4, 5, 1), (5, 4, 1), (5, 3, 2)]
TIT_SIN_DATO = 50.0


def mejor_once(jugs):
    por = defaultdict(list)
    for j in jugs:
        if j["status"] == "ok":
            por[j["position"]].append(j)
    for k in por:
        por[k].sort(key=lambda j: -j["esp"])
    mejor = None
    for d, m, dl in FORMACIONES:
        if len(por[1]) < 1 or len(por[2]) < d or len(por[3]) < m or len(por[4]) < dl:
            continue
        xi = por[1][:1] + por[2][:d] + por[3][:m] + por[4][:dl]
        v = sum(j["esp"] for j in xi)
        if mejor is None or v > mejor[0]:
            mejor = (v, f"{d}-{m}-{dl}", xi)
    return mejor


def reales():
    pts = defaultdict(list)
    vistos = set()
    for e in json.load(open(RAIZ / "data/rival_intelligence/board_events.json")):
        if e["type"] != "roundFinished" or e["content"]["round"]["name"] in vistos:
            continue
        vistos.add(e["content"]["round"]["name"])
        for x in e["content"]["results"]:
            pts[x["user"]["name"]].append(x["points"])
    return pts


if __name__ == "__main__":
    f = json.load(open(sys.argv[1]))
    cat = {p["id"]: p for p in f["todaLaLiga"]["players"]}
    clas = {s["name"]: s["points"] for s in f["competition"]["standings"]}
    hist = reales()
    filas = []
    for m in f["rival_squads"]["managers"]:
        jugs = []
        for p in m["players"]:
            c = cat.get(p["id"], {})
            pj = c.get("played") or 0
            media = (c.get("points") or p.get("points") or 0) / pj if pj else 0.0
            tit = p.get("starter_probability")
            jugs.append(dict(name=p["name"], position=p["position"], status=p.get("status") or c.get("status"),
                             esp=media * (tit if tit is not None else TIT_SIN_DATO) / 100))
        mo = mejor_once(jugs)
        xi = {j["name"] for j in mo[2]} if mo else set()
        banco = sorted((j["esp"] for j in jugs if j["name"] not in xi), reverse=True)
        h = hist.get(m["name"], [])
        filas.append((m["name"], clas.get(m["name"]), len(jugs), mo[0] if mo else 0, mo[1] if mo else "-",
                      sum(banco[:3]), sum(h) / len(h) if h else 0, len(h)))
    print(f"Foto: {f['meta']['generated_at']}\n")
    print(f"   {'manager':<16} {'puntos':>6} {'fichas':>6}  {'once esperado':>13}  {'formacion':>9}"
          f"  {'3 mejores del banco':>19}  {'real por jornada':>16}")
    for n, pts, nf, esp, form, banco, real, nj in sorted(filas, key=lambda x: -x[3]):
        print(f"   {n[:16]:<16} {pts:>6} {nf:>6}  {esp:>13.1f}  {form:>9}  {banco:>19.1f}  {real:>10.1f} ({nj} j)")
