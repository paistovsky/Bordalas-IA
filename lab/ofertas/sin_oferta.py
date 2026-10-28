"""
E67: ¿se queda alguna vez sin oferta del Computer un jugador publicado?
(Pendiente del equipo rojo, 28/10: «el cierre no tiene plan B si un
jugador de inventario no recibe oferta».) E42: el Computer renueva las
ofertas de los publicados cada 48 h con el reset de las 07:00 y el censo
de las ~02:10 ve el lote en su segunda noche.

Para cada noche de censo con lote (3+ ofertas): los jugadores que estaban
publicados desde ANTES del reset en que nacio el lote (~19 h antes del
censo) y seguian publicados a la hora del censo, segun
libro_de_publicacion.jsonl. ¿Cuantos tenian oferta?

Uso:  python3 lab/ofertas/sin_oferta.py
"""
import datetime as dt
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CENSO = RAIZ / "data/solvency/censo_de_ofertas.jsonl"
PUB = RAIZ / "data/intelligence/libro_de_publicacion.jsonl"

if __name__ == "__main__":
    pubs = [json.loads(l) for l in open(PUB)]
    for p in pubs:
        p["desde"] = dt.datetime.fromisoformat(p["first_listed_at"])
        p["hasta"] = dt.datetime.fromisoformat(p["last_seen"])
    total = con = 0
    faltan = []
    for l in open(CENSO):
        r = json.loads(l)
        if r["offers"] < 3:
            continue
        at = dt.datetime.fromisoformat(r["at"])
        nacio = at - dt.timedelta(hours=19)
        con_oferta = {p["name"] for p in r["players"]}
        pub = {p["player_name"] for p in pubs if p["desde"] < nacio and p["hasta"] >= at - dt.timedelta(hours=1)}
        for n in pub:
            total += 1
            if n in con_oferta:
                con += 1
            else:
                faltan.append((r["at"][:10], n))
    print(f"Publicados durante un lote: {total}; con oferta del Computer: {con}")
    print("Sin oferta:", faltan if faltan else "ninguno")

    # Cada jugador lleva su propio turno de 48 h (E42: Chust y Gulacsi van en
    # el otro). Lo justo: publicado durante dos noches seguidas enteras, ¿sale
    # en alguna de las dos? Solo desde el 01/10 (antes se republicaba a diario).
    noches = [json.loads(l) for l in open(CENSO)]
    noches = [(dt.datetime.fromisoformat(r["at"]), {p["name"] for p in r["players"]}) for r in noches]
    total = con = 0
    faltan = []
    for (a, oa), (b, ob) in zip(noches, noches[1:]):
        if a < dt.datetime(2026, 10, 1, tzinfo=a.tzinfo) or (b - a).total_seconds() > 30 * 3600:
            continue
        for p in pubs:
            if p["desde"] < a - dt.timedelta(hours=19) and p["hasta"] >= b - dt.timedelta(hours=1):
                total += 1
                if p["player_name"] in oa | ob:
                    con += 1
                else:
                    faltan.append((b.date().isoformat(), p["player_name"]))
    print(f"\nDesde el 01/10, publicados dos noches seguidas: {total}; con oferta en alguna de las dos: {con}")
    print("Sin oferta en ninguna:", faltan if faltan else "ninguno")
