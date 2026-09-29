"""Caso Aspas / Duran / Jutgla (Celta): noticias de FutbolFantasy frente a precios.

Uso: python3 lab/noticias/caso_aspas.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/noticias"))
from analizar import cargar_precios, norm  # noqa: E402

IDS = {"Aspas": 1523, "Duran": 29185, "Jutgla": 3159}
DESDE, HASTA = dt.date(2026, 9, 8), dt.date(2026, 9, 29)

precios = cargar_precios()
print("dia     " + "  ".join(f"{k:>14s}" for k in IDS))
d = DESDE
while d <= HASTA:
    fila = []
    for k, pid in IDS.items():
        p, q = precios[pid].get(d), precios[pid].get(d - dt.timedelta(days=1))
        fila.append(f"{p/1e6:6.2f} ({(p/q-1)*100:+5.1f}%)" if p and q else f"{'-':>14s}")
    print(d.strftime("%d/%m   ") + "  ".join(fila))
    d += dt.timedelta(days=1)

print("\nNoticias del Celta (o que nombran a Aspas/Duran/Jutgla), hora de Madrid:")
for l in open(RAIZ / "lab/noticias/archivo.jsonl"):
    n = json.loads(l)
    if not n.get("publicada"):
        continue
    f = dt.date.fromisoformat(n["publicada"][:10])
    t = norm(n["titulo"] + " " + (n.get("descripcion") or ""))
    if DESDE <= f <= HASTA and (n.get("equipo") == "celta" or any(w in t for w in ("aspas", "duran", "jutgla"))):
        print(f"{n['publicada'][8:10]}/{n['publicada'][5:7]} {n['publicada'][11:16]}  {n['titulo']}")
        if any(w in t for w in ("aspas", "duran", "jutgla")) and n.get("descripcion"):
            print(f"               · {n['descripcion'][:150]}")
