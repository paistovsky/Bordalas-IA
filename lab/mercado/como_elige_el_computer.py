"""
E61: ¿como elige el Computer a los 20 que pone cada dia? Para «la lista de
objetivos» del gestor (25/10): cuanto hay que esperar a que salga uno.

Datos: libro_del_escaparate.jsonl (la lista de cada dia, 20 jugadores) y
la foto de la liga (precio, de quien es) para saber cuantos libres hay.
Mide: apariciones por jugador frente a lo esperado si fuera al azar entre
los libres; si sale mas el caro o el barato; y si el que salio vuelve
pronto.

Uso:  python3 -I lab/mercado/como_elige_el_computer.py STATUS.json
"""
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESC = RAIZ / "data/trading/libro_del_escaparate.jsonl"

if __name__ == "__main__":
    dias = [json.loads(l) for l in open(ESC)]
    f = json.load(open(sys.argv[1]))
    pl = f["todaLaLiga"]["players"]
    libres = [p for p in pl if p.get("de_quien") in ("libre", "computer")]
    n_libres = len(libres)
    apar = Counter()
    fechas = defaultdict(list)
    for d in dias:
        for p in d["players"]:
            apar[p["id"]] += 1
            fechas[p["id"]].append(d["dia_de_mercado"])
    D = len(dias)
    print(f"Dias de escaparate: {D}; jugadores distintos vistos: {len(apar)}; libres hoy: {n_libres}")
    print(f"Si fuera al azar entre ~{n_libres} libres: cada uno saldria {20*D/n_libres:.2f} veces en {D} dias "
          f"(un {20/n_libres:.1%} de los dias)\n")
    reparto = Counter(apar.values())
    print("veces que salio un jugador:", dict(sorted(reparto.items())))
    # caro contra barato: tasa por tramo de precio (precio de hoy) entre los libres de hoy
    print("\nTasa por tramo de precio (libres de hoy):")
    for lo, hi in ((0, 0.5e6), (0.5e6, 1.5e6), (1.5e6, 3e6), (3e6, 6e6), (6e6, 1e9)):
        g = [p for p in libres if lo <= p["price"] < hi]
        if g:
            veces = sum(apar.get(p["id"], 0) for p in g)
            print(f"   {lo/1e6:>4.1f}-{min(hi, 99e6)/1e6:<4.1f} M  libres {len(g):>3}  salen {veces/len(g)/D:5.1%} de los dias")
    # vuelve pronto: dias entre apariciones consecutivas
    gaps = []
    import datetime as dt
    for pid, fs in fechas.items():
        fs = sorted(set(fs))
        gaps += [(dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days for a, b in zip(fs, fs[1:])]
    if gaps:
        print(f"\nDias entre dos salidas del mismo jugador: n={len(gaps)}, mediana {st.median(gaps)}, "
              f"1 dia (sigue en la lista) {sum(g == 1 for g in gaps)}, 2-7 dias {sum(2 <= g <= 7 for g in gaps)}")
