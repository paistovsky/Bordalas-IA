"""
E47: la racha diaria de Biwenger (dailyStreak, 250.000) como dinero con
fecha, y si con ella y el premio de la J9 Pepe llega en verde al plazo
del aplazado (mie 21/10 14:00) sin vender a nadie.

Del tablon: cada «bonus» con reason dailyStreak, por manager; los dias
entre cobros. Y el reloj de los premios de jornada (E43: 13-18 h tras el
ultimo partido del bloque).

Uso:  python3 lab/caja/la_racha.py
"""
import datetime as dt
import json
import statistics as st
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
MAD = ZoneInfo("Europe/Madrid")
PEPE = 14175949

if __name__ == "__main__":
    cobros = defaultdict(list)
    for e in json.load(open(TABLON)):
        if e["type"] == "bonus":
            for b in e["content"]:
                if b.get("reason") == "dailyStreak":
                    cobros[b["user"]["id"]].append((dt.datetime.fromtimestamp(e["date"], dt.timezone.utc), b["amount"]))
    todos = []
    for uid, cs in cobros.items():
        cs.sort()
        gaps = [(b[0] - a[0]).total_seconds() / 86400 for a, b in zip(cs, cs[1:])]
        todos += gaps
        quien = "Pepe" if uid == PEPE else uid
        print(f"{quien}: {len(cs)} cobros de {cs[0][1]:,}; dias entre cobros:",
              " ".join(f"{g:.1f}" for g in gaps))
    print(f"\nTodos: n={len(todos)} huecos, mediana {st.median(todos):.2f} dias;"
          f" entre 4,5 y 5,5: {sum(4.5 <= g <= 5.5 for g in todos)}")
    pepe = sorted(cobros[PEPE])
    ult = pepe[-1][0]
    print(f"\nUltimo cobro de Pepe: {ult.astimezone(MAD):%a %d/%m %H:%M} de Madrid")
    for k in (1, 2, 3):
        print(f"   siguiente {k}: ~{(ult + dt.timedelta(days=5 * k)).astimezone(MAD):%a %d/%m %H:%M}")
