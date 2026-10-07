"""
E24: ¿cuanto cae el precio de un jugador caro cuando se lesiona?

La regla del CEO (07/10): si Yamal se lesiona 4 semanas o mas, se vende al
Computer el primer dia, «porque su precio cae cada dia sin puntuar». Se
mide con las noticias de BAJA fuerte de FutbolFantasy (lesion, rotura,
operado, parte medico, semanas, se pierde; archivo de E4 ampliado en E6)
de jugadores de 3 M o mas, y su precio de Biwenger a +1, +3, +7, +14, +21
y +28 dias desde el primer cambio despues de la noticia.

Uso:  python3 lab/lesiones/precio_lesionado.py
"""
import datetime as dt
import json
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

FUERTE = re.compile(r"lesi|rotura|operad|quir|semanas|se pierde|parte m", re.I)
D = dt.timedelta(days=1)

if __name__ == "__main__":
    P = Precios()
    ev = [json.loads(l) for l in open(RAIZ / "lab/noticias/eventos_hasta_29_09.jsonl")]
    primera = {}
    for e in sorted(ev, key=lambda e: e["publicada"]):
        if e["tipo"] == "BAJA" and FUERTE.search(e["titulo"]):
            primera.setdefault(e["pid"], e)
    print(f"Precios hasta {P.ultimo_dia}. Primera BAJA fuerte de jugadores de 3 M o mas:\n")
    print(f"   {'jugador':<16} {'noticia':<10} {'precio':>6}   +1d    +3d    +7d   +14d   +21d   +28d")
    for pid, e in sorted(primera.items(), key=lambda x: -(P.en(x[0], dt.date.fromisoformat(x[1]["E"]) - D) or 0)):
        d = dt.date.fromisoformat(e["E"])
        p0 = P.en(pid, d - D)
        if not p0 or p0 < 3e6:
            continue
        cols = []
        for k in (1, 3, 7, 14, 21, 28):
            p = P.en(pid, d + (k - 1) * D) if d + (k - 1) * D <= P.ultimo_dia else None
            cols.append(f"{(p / p0 - 1) * 100:+5.0f}%" if p else "     -")
        print(f"   {e['name'][:16]:<16} {e['E']:<10} {p0/1e6:5.1f}M " + " ".join(cols) + f"   | {e['titulo'][:55]}")
