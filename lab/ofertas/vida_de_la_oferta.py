"""
E40: ¿cuanto vive una oferta del Computer a Pepe? ¿Sobrevive al reset de
las 07:00 de Madrid? (la duda del gestor para el jueves 16/10: si entra
Lemar a las 07:00, hay que cobrar a Exposito antes de las 15:00).

Cruza cada venta de Pepe al Computer (tablon, sin «to») con el censo de
ofertas de cada noche (~02:10 de Madrid): si el importe cobrado es el de
la oferta censada esa noche, la oferta seguia viva a la hora de la venta.
Y el ritmo: en que noches hay ofertas por los titulares.

Uso:  python3 lab/ofertas/vida_de_la_oferta.py
"""
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
CENSO = RAIZ / "data/solvency/censo_de_ofertas.jsonl"
MAD = ZoneInfo("Europe/Madrid")
PEPE = 14175949

if __name__ == "__main__":
    censo = []  # (momento, {importe: nombre})
    for linea in open(CENSO):
        r = json.loads(linea)
        censo.append((dt.datetime.fromisoformat(r["at"]), {p["amount"]: p["name"] for p in r["players"]}))
    ventas = []
    for e in json.load(open(TABLON)):
        if e["type"] != "transfer":
            continue
        for x in e["content"]:
            if x.get("from", {}).get("id") == PEPE and "to" not in x:
                ventas.append((dt.datetime.fromtimestamp(e["date"], dt.timezone.utc), x["amount"]))
    ventas = sorted(set(v for v in ventas if v[0] >= censo[0][0]))
    print(f"Ventas de Pepe al Computer desde el primer censo: {len(ventas)}\n")
    casadas, horas = 0, []
    for cuando, importe in ventas:
        antes = [(m, o) for m, o in censo if m <= cuando]
        m, o = antes[-1]
        h = (cuando - m).total_seconds() / 3600
        si = importe in o
        casadas += si
        if si:
            horas.append(h)
        print(f"  {cuando.astimezone(MAD):%d/%m %H:%M} {importe:>10,}  censo de las {m.astimezone(MAD):%d/%m %H:%M}"
              f"  {'= oferta censada (' + o[importe] + f'), {h:4.1f} h despues' if si else 'no esta en ese censo'}")
    print(f"\nVentas al importe exacto de la oferta censada esa noche: {casadas} de {len(ventas)}")
    if horas:
        print(f"horas entre el censo y la venta: min {min(horas):.1f}  max {max(horas):.1f}")
        print(f"despues del reset de las 07:00 (> 4,8 h): {sum(h > 4.8 for h in horas)}")
    print("\nNoches con mas de 2 ofertas (fecha de Madrid):")
    print("  " + " ".join(f"{m.astimezone(MAD):%d/%m}({len(o)})" for m, o in censo if len(o) > 2))
