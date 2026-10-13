"""
E38: ¿cuando llega la oferta del Computer por un jugador de Pepe, y a que
precio? (la duda del gestor: «si Jutgla se vende por debajo del 90 % o
tarda, rojo el jueves»).

Datos: data/solvency/censo_de_ofertas.jsonl (las ofertas vivas que Pepe
tiene cada noche, ~00:10 UTC) y el historial de precios. Para cada oferta:
oferta / precio del dia de mercado anterior (el que rige a las 00:10).
Y el calendario: que noches hay ofertas y cuantas.

Uso:  python3 lab/ofertas/cuando_llega.py
"""
import datetime as dt
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

FOTO = RAIZ / "data/fotos/2026-09-18.json"
CENSO = RAIZ / "data/solvency/censo_de_ofertas.jsonl"

if __name__ == "__main__":
    P = Precios()
    ids = {p["name"]: p["id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    ratios, por_nombre, sin_id = [], defaultdict(list), set()
    print("noche (UTC)       ofertas   (Jutgla: oferta / precio)")
    for linea in open(CENSO):
        r = json.loads(linea)
        at = dt.datetime.fromisoformat(r["at"])
        dia = (at - dt.timedelta(hours=5)).date()  # dia de mercado vigente
        jut = ""
        for p in r["players"]:
            pid = ids.get(p["name"])
            precio = P.en(pid, dia) if pid else None
            if not precio:
                sin_id.add(p["name"])
                continue
            q = p["amount"] / precio
            ratios.append(q)
            por_nombre[p["name"]].append((r["at"][:10], q))
            if p["name"].startswith("Jutgl"):
                jut = f"{p['amount']:,} / {precio:,} = {q:.3f}"
        print(f"{r['at'][:16]}   {r['offers']:>3}      {jut}")
    print(f"\nOfertas con precio: {len(ratios)}  (sin cruzar: {sorted(sin_id)})")
    qs = sorted(ratios)
    print(f"oferta/precio: min {qs[0]:.3f}  p10 {qs[len(qs)//10]:.3f}  mediana {st.median(qs):.3f}"
          f"  p90 {qs[9*len(qs)//10]:.3f}  max {qs[-1]:.3f}")
    print(f"por debajo de 0,97: {sum(q < 0.97 for q in qs)}   por debajo de 0,90: {sum(q < 0.90 for q in qs)}")
