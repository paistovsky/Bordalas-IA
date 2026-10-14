"""
E39: E37 contra las pujas REALES de Pepe (data/trading/bid_outcome_ledger.json).

El puesto de mando cita «59 ganadas / 14 perdidas». Aqui: (1) cuantas son
pujas distintas (el libro repite la misma puja en varias vueltas), (2) las
de 1 M o mas, que son las que importan para el once, y (3) en las perdidas
con importe ganador conocido, con que margen sobre el precio se habrian
ganado (+5 %, +8 %, +12 %: la puja fuerte).

Uso:  python3 lab/subasta/las_pujas_de_pepe.py
"""
import json
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LIBRO = RAIZ / "data/trading/bid_outcome_ledger.json"

if __name__ == "__main__":
    pujas = list(json.load(open(LIBRO))["bids"].values())
    print("Filas del libro:", dict(Counter(p["outcome"] for p in pujas)))
    unicas = {}
    for p in sorted(pujas, key=lambda p: p["placed_at"]):
        unicas.setdefault((p["player_id"], (p.get("resolved_at") or p["placed_at"])[:10]), p)
    print("Pujas distintas (jugador y dia):", dict(Counter(p["outcome"] for p in unicas.values())))
    grandes = [p for p in unicas.values() if (p["market_price"] or 0) >= 1_000_000 and p["outcome"] != "PENDING"]
    for desde in ("2026-08-01", "2026-09-25"):
        g = [p for p in grandes if p["placed_at"] >= desde]
        print(f"De 1 M o mas desde {desde}:", dict(Counter(p["outcome"] for p in g)))
    perdidas = [p for p in grandes if p["outcome"] == "LOST" and p["winning_amount"]]
    margenes = sorted(p["winning_amount"] / p["market_price"] - 1 for p in perdidas)
    print(f"\nPerdidas con importe ganador (n = {len(margenes)}):",
          " ".join(f"{m*100:+.1f}%" for m in margenes))
    for k in (0.01, 0.05, 0.08, 0.12):
        print(f"   con precio +{k*100:.0f} % se habrian ganado {sum(m < k for m in margenes)} de {len(margenes)}")
    ganadas = [p for p in grandes if p["outcome"] == "WON" and p["placed_at"] >= "2026-09-25"]
    print("\nGanadas de 1 M o mas desde el 25/09:",
          ", ".join(f"{p['player_name']} {p['amount']/p['market_price']-1:+.1%}" for p in ganadas))
