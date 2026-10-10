"""
E31: como empezo la J8 (09/10 21:00) cada manager.

  - ¿Alguien guardo la alineacion DESPUES del primer partido? Si la liga
    la bloquea (`lineupRoundChanges: 0`), no deberia (comprobacion de E27).
  - ¿Quien empezo en rojo? Quien empieza la jornada con saldo negativo no
    puntua (E29).

Datos: las fotos de los ciclos (status.json; carpeta por argumento, los
artefactos caducan a los 2 dias): `rival_squads[].lineup_date` y
`league_center.fantasy_standings[].balance`.

Uso:  python3 lab/carrera/arranque_j8.py CARPETA
"""
import datetime as dt
import glob
import json
import os
import sys
from zoneinfo import ZoneInfo

M = ZoneInfo("Europe/Madrid")
INICIO = dt.datetime(2026, 10, 9, 21, 0, tzinfo=M)

if __name__ == "__main__":
    for r in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
        if os.path.getsize(r) < 10_000:
            continue
        d = json.load(open(r))
        fila, tarde = [], []
        for m in d["rival_squads"]["managers"]:
            ld = m.get("lineup_date")
            x = dt.datetime.fromtimestamp(ld, M) if ld else None
            fila.append(f"{m['name'][:6]} {x.strftime('%d/%m %H:%M') if x else '-'}")
            if x and x > INICIO:
                tarde.append(m["name"])
        saldos = {s["name"]: s["balance"] for s in d["league_center"]["fantasy_standings"]}
        rojos = [f"{n[:10]} {b:,}" for n, b in saldos.items() if b < 0]
        print(f"{d['meta']['generated_at'][5:16]}  rojo: {', '.join(rojos) or '-'}"
              f"  | once guardado despues de las 21:00: {', '.join(tarde) or 'nadie'}")
        print("      " + " · ".join(fila))
