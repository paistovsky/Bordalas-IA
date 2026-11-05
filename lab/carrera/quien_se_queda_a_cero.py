"""
E84: ¿cuantas veces un manager empezo una jornada en rojo y se quedo sin
premio? (Hoy, vispera de la J12: Pollo -5,31 M, Luismi -10,16 M, Manzagool
-8,29 M.) Del tablon: en cada roundFinished, quien no tiene «bonus» (E29:
Luismi en la J6 aplazada, 64 puntos y 0 euros) es quien la empezo en rojo.

Uso:  python3 lab/carrera/quien_se_queda_a_cero.py
"""
import json
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"

if __name__ == "__main__":
    rondas, ceros, jugadas = set(), [], Counter()
    for e in json.load(open(TABLON)):
        if e["type"] != "roundFinished":
            continue
        r = e["content"]["round"]
        if r["id"] in rondas:
            continue
        rondas.add(r["id"])
        for x in e["content"]["results"]:
            n = x["user"]["name"][:14]
            jugadas[n] += 1
            if not x.get("bonus"):
                ceros.append((r["name"], n, x["points"]))
    print(f"Rondas pagadas: {len(rondas)}")
    for c in ceros:
        print(f"   {c[0]:28} {c[1]:14} {c[2]:>3} pts, 0 EUR")
    print("\nVeces sin premio por manager:", dict(Counter(c[1] for c in ceros)) or "ninguna")
    print("Rondas jugadas:", dict(jugadas))
