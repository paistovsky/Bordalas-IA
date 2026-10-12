"""
E35: la J8 a medias (antes de cerrar): puntos de cada once guardado
(`rival_squads[].players[].is_starter`) entre la foto de antes del primer
partido y la de ahora, y cuantos titulares tienen aun el partido por
jugar (equipo sin ningun jugador con un partido mas). Contra E23.

Uso:  python3 -I lab/predicciones/j8_parcial.py ANTES.json AHORA.json
"""
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    a = {p["id"]: p for p in json.load(open(sys.argv[1]))["todaLaLiga"]["players"]}
    B = json.load(open(sys.argv[2]))
    b = {p["id"]: p for p in B["todaLaLiga"]["players"]}
    pr = json.load(open(Path(__file__).parent / "j8.json"))
    eq = {}
    for i, p in b.items():
        if i in a:
            eq[p["team_id"]] = eq.get(p["team_id"], 0) + ((p["played"] or 0) > (a[i]["played"] or 0))
    print(f"Foto: {B['meta']['generated_at']}")
    for m in B["rival_squads"]["managers"]:
        xi = [p for p in m["players"] if p.get("is_starter") and p["id"] in a]
        real = sum(b[p["id"]]["points"] - a[p["id"]]["points"] for p in xi)
        pend = sum(1 for p in xi if eq.get(b[p["id"]]["team_id"], 0) == 0)
        esp = pr["managers"].get(m["name"], {}).get("once_esperado")
        print(f"   {m['name'][:16]:<16} once de {len(xi):2d}  lleva {real:4d}  le faltan {pend}  (E23: {esp})")
