"""
E78: ¿cada cuanto saca el Computer un delantero que valga para cambiar a
Roberto? (Orden del dueño, 02/11: Roberto sale cuando entre Fer Nino,
Zabiri u otro delantero titular con buenos puntos.)

Del escaparate (las listas de cada dia; la del dia d es la de d-1, E70):
delanteros (posicion 4) con 4+ partidos, mas puntos por partido que
Roberto hoy y titularidad FF de 70 % o mas, de 4 a 10 M. Cuantos dias hay
alguno y cuantos distintos salieron.

Uso:  python3 -I lab/mercado/delantero_por_roberto.py [pts_por_partido_minimo]
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESC = RAIZ / "data/trading/libro_del_escaparate.jsonl"

if __name__ == "__main__":
    minimo = float(sys.argv[1]) if len(sys.argv) > 1 else 6.3
    dias, con, vistos = 0, 0, {}
    for l in open(ESC):
        r = json.loads(l)
        dias += 1
        buenos = [p for p in r["players"] if p.get("position") == 4 and (p.get("played") or 0) >= 4
                  and p["points"] / p["played"] >= minimo and (p.get("starter_probability") or 0) >= 70
                  and 4e6 <= p["price"] <= 10e6]
        if buenos:
            con += 1
            for p in buenos:
                vistos.setdefault(p["name"], (r["dia_de_mercado"], p["price"], round(p["points"] / p["played"], 1)))
    print(f"Dias de escaparate: {dias}; con algun delantero que valga (>= {minimo} pts/partido, FF >= 70, 4-10 M): {con}")
    print(f"   un dia cualquiera: {con/dias:.0%}; en una semana (7 dias, al azar): {1-(1-con/dias)**7:.0%}")
    print("   distintos:", ", ".join(f"{n} ({d}, {p/1e6:.1f} M, {q})" for n, (d, p, q) in vistos.items()))
