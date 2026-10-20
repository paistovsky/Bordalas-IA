"""
E48: el once esperado de Pepe y de Pollo17, jugador a jugador, con su
precio; y cuantos puntos de temporada separan a los dos onces.

Usa la misma vara que E20 (puntos por partido x titularidad FF, estado ok)
y su `mejor_once`. Uso:  python3 -I lab/carrera/once_detalle.py status.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from proyeccion import TIT_SIN_DATO, mejor_once  # noqa: E402

QUEDAN = 30  # J9 ya empezada: J10-J38 + la J9 a medias, por lo bajo

if __name__ == "__main__":
    f = json.load(open(sys.argv[1]))
    cat = {p["id"]: p for p in f["todaLaLiga"]["players"]}
    onces = {}
    for m in f["rival_squads"]["managers"]:
        if m["name"] not in ("Pepe Bordalás", "Pollo17", "Luismi_Haz"):
            continue
        jugs = []
        for p in m["players"]:
            c = cat.get(p["id"], {})
            pj = c.get("played") or 0
            media = (c.get("points") or 0) / pj if pj else 0.0
            tit = p.get("starter_probability")
            jugs.append(dict(name=p["name"], position=p["position"], status=p.get("status") or c.get("status"),
                             esp=media * (tit if tit is not None else TIT_SIN_DATO) / 100,
                             media=media, tit=tit, precio=c.get("price") or 0))
        mo = mejor_once(jugs)
        onces[m["name"]] = mo
        print(f"\n{m['name']}: {mo[0]:.1f} esperados ({mo[1]}), once de {sum(j['precio'] for j in mo[2])/1e6:.1f} M")
        for j in sorted(mo[2], key=lambda j: (j["position"], -j["esp"])):
            print(f"   {'PDMA'[j['position']-1]} {j['name'][:18]:18} {j['media']:4.1f} pts/p x {j['tit'] or TIT_SIN_DATO:3.0f} %"
                  f" = {j['esp']:4.1f}   {j['precio']/1e6:5.2f} M")
        fuera = [j for j in jugs if j["status"] != "ok"]
        if fuera:
            print("   fuera (estado no ok):", ", ".join(f"{j['name']} ({j['status']})" for j in fuera))
    p, q = onces["Pepe Bordalás"][0], onces["Pollo17"][0]
    print(f"\nDiferencia Pollo17 - Pepe: {q - p:+.1f} por jornada; en {QUEDAN} jornadas, "
          f"{(q - p) * QUEDAN * 0.81:+.0f} a {(q - p) * QUEDAN * 1.04:+.0f} puntos (con el 81-104 % de E20)")
