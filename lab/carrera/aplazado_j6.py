"""
E45: el Levante-Athletic del 21/10 (aplazado de la J6), ¿es plazo de caja?

1) Como trato Biwenger los aplazados antes (roundStarted/roundFinished del
   tablon: cada «parte» es una ronda propia que empieza en su primer
   partido, y quien la empieza en rojo no puntua: E29, Luismi en la J6).
2) Que se juega Pepe el 21/10: sus jugadores del Levante y del Athletic
   (foto de un ciclo: dashboard/data/status.json de un artefacto) y su
   saldo, y la oferta del Computer mas pequena que lo tapa.

Uso:  python3 -I lab/carrera/aplazado_j6.py STATUS.json
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
LEVANTE, ATHLETIC = 10, 1  # ids de equipo, sacados de sus jugadores (Ivan Romero, Brugue / Williams)

if __name__ == "__main__":
    for e in json.load(open(TABLON)):
        if e["type"] in ("roundStarted", "roundFinished"):
            r = e["content"]["round"]
            if r.get("part") or r["name"] in ("Jornada 1", "Jornada 6"):
                print(f"{dt.datetime.utcfromtimestamp(e['date']):%d/%m %H:%M} UTC  {e['type']:13} {r['name']} (id {r['id']})")
    s = json.load(open(sys.argv[1]))
    pl = s["todaLaLiga"]["players"]
    nuestros = [p for p in pl if p.get("de_quien") == "nuestro"]
    print("\nDe Pepe en el Levante-Athletic:",
          [p["name"] for p in nuestros if p["team_id"] in (LEVANTE, ATHLETIC)] or "nadie")
    yo = next(f for f in s["league_center"]["fantasy_standings"] if f.get("is_us"))
    print(f"Saldo: {yo['balance']:,}")
    ofertas = sorted((o["amount"], o["players"][0]) for o in s.get("offers") or [] if o["counterparty"] == "COMPUTER")
    print("Ofertas del Computer, de menor a mayor:", ", ".join(f"{n} {a:,}" for a, n in ofertas))
    tapa = [(a, n) for a, n in ofertas if a + yo["balance"] >= 0]
    print("La mas pequena que deja el saldo en verde:", tapa[0] if tapa else "ninguna sola")
