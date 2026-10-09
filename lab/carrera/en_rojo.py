"""
E29: ¿quien empieza la J8 en rojo? (y la regla, comprobada con el tablon)

Regla de la liga: quien empieza la jornada con saldo negativo no puntua.
Se comprueba reconstruyendo la clasificacion con los `roundFinished` del
tablon (suma de puntos por jornada) contra los puntos de la clasificacion
de hoy (foto de un ciclo). Y se mira el saldo de cada manager en la foto.

Uso:  python3 lab/carrera/en_rojo.py status.json
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    f = json.load(open(sys.argv[1]))
    vistos, por = set(), {}
    for e in json.load(open(RAIZ / "data/rival_intelligence/board_events.json")):
        if e["type"] == "roundFinished" and e["content"]["round"]["name"] not in vistos:
            vistos.add(e["content"]["round"]["name"])
            for x in e["content"]["results"]:
                por.setdefault(x["user"]["name"], []).append((e["content"]["round"]["name"], x["points"], x.get("bonus")))
    print(f"Foto: {f['meta']['generated_at']}\n")
    print(f"   {'manager':<16} {'clasif.':>7} {'suma tablon':>11} {'sin J1':>7}  jornadas sin premio     saldo hoy")
    for s in f["league_center"]["fantasy_standings"]:
        v = por.get(s["name"], [])
        suma = sum(p for _, p, _ in v)
        j1 = sum(p for r, p, _ in v if r == "Jornada 1")
        cero = [f"{r} ({p})" for r, p, b in v if b is None]
        print(f"   {s['name'][:16]:<16} {s['points']:>7} {suma:>11} {suma - j1:>7}  {', '.join(cero) or '-':<22} {s['balance']:>12,}")
