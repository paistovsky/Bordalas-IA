"""
E19: lo que un manager le vende al Computer, ¿vuelve a salir en el mercado
del Computer? ¿Cuando?

El gestor (04/10): «lo que hay que vigilar no es el escaparate de los
rivales sino el mercado del Computer del reset: lo que ellos le vendan
saldra ahi». Se comprueba con:
  - las ventas al Computer del tablon (todos los managers, sin repetidos);
  - las listas diarias del Computer de `libro_del_escaparate.jsonl`
    (20 jugadores al dia, del 17/09 al 05/10; falta alguna).
Se compara con la tasa de cualquier jugador libre de salir en la lista.

Uso:  python3 lab/rivales/vuelven_al_mercado.py
"""
import datetime as dt
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from viajes import COMPUTER, RAIZ, eventos  # noqa: E402

if __name__ == "__main__":
    listas = {}
    for l in open(RAIZ / "data/trading/libro_del_escaparate.jsonl"):
        d = json.loads(l)
        listas[dt.date.fromisoformat(d["dia_de_mercado"])] = {p["id"] for p in d["players"]}
    dias = sorted(listas)
    ini, fin = dias[0], dias[-1]
    vistos, ventas = set(), []
    for ts, pid, comp, vend, imp, _ in eventos():
        if comp == COMPUTER and vend != COMPUTER and (pid, imp, vend) not in vistos:
            vistos.add((pid, imp, vend))
            ventas.append((dt.datetime.utcfromtimestamp(ts).date(), pid))
    # solo ventas con al menos 7 dias de listas despues
    medibles = [(d, p) for d, p in ventas if ini <= d <= fin - dt.timedelta(days=7)]
    lags = []
    for d, p in medibles:
        sale = [x for x in dias if x > d and p in listas[x]]
        lags.append((sale[0] - d).days if sale else None)
    n = len(medibles)
    vuelven = [x for x in lags if x is not None]
    print(f"Listas del Computer: {len(dias)} dias ({ini} a {fin}), {len(set().union(*listas.values()))} jugadores distintos.")
    print(f"Ventas al Computer medibles (del {ini} al {fin - dt.timedelta(days=7)}): {n}")
    print(f"   vuelven a salir en la lista antes del {fin}: {len(vuelven)} ({len(vuelven)/n:.0%})")
    for a, b in ((1, 3), (4, 7), (8, 30)):
        print(f"     a los {a}-{b} dias: {sum(a <= x <= b for x in vuelven)}")
    # tasa base: un jugador cualquiera del catalogo, en una ventana de 7 dias
    cat = {p["id"] for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]
           if p.get("de_quien") in ("libre", "computer")}
    ventanas = [dias[i:i + 7] for i in range(len(dias) - 6)]
    base = sum(len(set().union(*(listas[x] for x in w)) & cat) / len(cat) for w in ventanas) / len(ventanas)
    vend7 = sum(1 for x in vuelven if x <= 7) / n
    print(f"\n   en 7 dias: los vendidos al Computer salen el {vend7:.0%}; un jugador libre cualquiera, el {base:.0%}")
