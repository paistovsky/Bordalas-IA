"""
E43: ¿cuando paga Biwenger el premio de una jornada? (la J8 acabo el
lunes 12/10 y el 16/10 el premio aun no ha entrado).

Cruza los «roundFinished» del tablon (cuando se cobra) con el calendario
(el ultimo partido de cada jornada; los aplazados se ven porque juegan
lejos del resto). Para cada jornada: ultimo partido del bloque principal,
partidos descolgados (mas de 3 dias despues), y horas hasta el cobro.

Uso:  python3 -I lab/carrera/cuando_se_cobra.py CALENDARIO.json
      (data/calendar/laliga_calendar.json de un artefacto de los ciclos)
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
    por_j = defaultdict(list)
    for m in cal["matches"]:
        if m.get("kickoff"):
            por_j[m["matchday"]].append((dt.datetime.fromisoformat(m["kickoff"]), f"{m['home']}-{m['away']}"))
    cobros = {}
    for e in json.load(open(TABLON)):
        if e["type"] == "roundFinished":
            cobros.setdefault(e["content"]["round"]["name"], dt.datetime.fromtimestamp(e["date"], dt.timezone.utc))
    for j in sorted(por_j):
        if j > 10:
            break
        ps = sorted(por_j[j])
        mediana = ps[len(ps) // 2][0]
        bloque = [p for p in ps if p[0] - mediana < dt.timedelta(days=3)]
        sueltos = [p for p in ps if p not in bloque]
        fin = bloque[-1][0] + dt.timedelta(hours=2)
        cobro = cobros.get(f"Jornada {j}")
        h = f"{(cobro - fin).total_seconds()/3600:5.1f} h" if cobro else "  sin cobrar"
        print(f"J{j}: fin del bloque {fin.astimezone(MAD):%a %d/%m %H:%M}, cobro "
              f"{cobro.astimezone(MAD).strftime('%a %d/%m %H:%M') if cobro else '-':>16} ({h})"
              + (f"   descolgados: {', '.join(f'{n} {k.astimezone(MAD):%d/%m}' for k, n in sueltos)}" if sueltos else ""))
        apl = cobros.get(f"Jornada {j} (aplazada)")
        if apl:
            print(f"      parte 2 (aplazada) cobrada {apl.astimezone(MAD):%a %d/%m %H:%M}")
