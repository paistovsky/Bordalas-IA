"""
E60: el calendario de Pepe (data/calendar/laliga_calendar.json, el de los
ciclos) contra Biwenger. Para cada jornada: el primer partido segun el
fichero y el «roundStarted» real del tablon. El 24/10 el gestor vio que el
fichero da la J11 el 01/11 y Biwenger la empieza el 30/10.

Uso:  python3 -I lab/infra/calendario_contra_biwenger.py CALENDARIO.json
"""
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
MAD = ZoneInfo("Europe/Madrid")

if __name__ == "__main__":
    cal = json.load(open(sys.argv[1]))
    print("fichero bajado:", cal.get("fetched_at"), "| fuentes:", cal.get("source"))
    por_j = defaultdict(list)
    for m in cal["matches"]:
        if m.get("kickoff"):
            por_j[m["matchday"]].append(dt.datetime.fromisoformat(m["kickoff"]))
    reales = {}
    for e in json.load(open(TABLON)):
        if e["type"] == "roundStarted":
            n = e["content"]["round"]["name"]
            if n.startswith("Jornada ") and "aplazada" not in n:
                reales.setdefault(int(n.split()[1]), dt.datetime.fromtimestamp(e["date"], dt.timezone.utc))
    print(f"\n  jornada   primer partido (fichero)   empieza en Biwenger     diferencia")
    for j in sorted(set(por_j) | set(reales)):
        if j > 14:
            break
        f = min(por_j[j]) if por_j.get(j) else None
        r = reales.get(j)
        dif = f"{(f - r).total_seconds() / 3600:+7.1f} h" if (f and r) else "     -"
        print(f"  J{j:<3}     {f.astimezone(MAD):%a %d/%m %H:%M}" if f else f"  J{j:<3}         -          ", end="")
        print(f"          {r.astimezone(MAD):%a %d/%m %H:%M}" if r else "             (aun no)", "  ", dif)
