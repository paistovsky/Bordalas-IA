"""
E15: el bot pequeno contra Pepe, vuelta a vuelta, con las fotos REALES de
produccion (artefactos de Actions; caducan a los 2 dias, asi que se pasan
por argumento: una carpeta con los status.json de cada ciclo).

Por cada foto: el once del bot (E7) contra el que tenia Pepe guardado, y
las pujas de reventa del bot (E1/E9) contra las pujas de Pepe que apunta
`data/trading/bid_outcome_ledger.json` ese mismo dia. Para las pujas del
bot, que hizo su precio despues (price_history).

Uso:  python3 lab/bot_pequeno/replay.py CARPETA [CARPETA2 ...]
"""
import datetime as dt
import glob
import json
import os
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from bot import decidir  # noqa: E402
from viajes import Precios  # noqa: E402


def fotos(carpetas):
    out = []
    for c in carpetas:
        for ruta in glob.glob(os.path.join(c, "*.json")):
            if os.path.getsize(ruta) < 10_000:
                continue
            t = os.path.basename(ruta)[:-5]
            out.append((t, ruta))
    out.append(("2026-09-18T14:16:38Z", str(RAIZ / "data/fotos/2026-09-18.json")))
    return sorted(out)


if __name__ == "__main__":
    P = Precios()
    pepe_pujas = defaultdict(list)
    for r in json.load(open(RAIZ / "data/trading/bid_outcome_ledger.json"))["bids"].values():
        pepe_pujas[r["placed_at"][:10]].append((r["player_name"], r["amount"], r.get("target_source"), r.get("outcome")))
    n = iguales = 0
    dif_once = []
    pujas_bot = {}
    sin_caja = 0
    for t, ruta in fotos(sys.argv[1:]):
        f = json.load(open(ruta))
        d = decidir(f)
        n += 1
        pepe_xi = sorted(p["name"] for p in (f.get("lineup") or {}).get("players") or [])
        if d["once"] and sorted(d["once"][2]) == pepe_xi:
            iguales += 1
        elif d["once"]:
            fuera = set(pepe_xi) - set(d["once"][2])
            dentro = set(d["once"][2]) - set(pepe_xi)
            dif_once.append((t, sorted(fuera), sorted(dentro)))
        if d["caja"] == 0:
            sin_caja += 1
        for nombre, puja in d["pujas"]:
            pujas_bot.setdefault((t[:10], nombre), (puja, t))
    print(f"Fotos: {n} ({fotos(sys.argv[1:])[0][0][:10]} y del {fotos(sys.argv[1:])[1][0][:10]} al {fotos(sys.argv[1:])[-1][0][:10]})")
    print(f"\nONCE: el del bot (E7) coincide con el de Pepe en {iguales}/{n} fotos.")
    vistos = set()
    for t, fuera, dentro in dif_once:
        k = (tuple(fuera), tuple(dentro))
        if k in vistos:
            continue
        vistos.add(k)
        print(f"   {t[:16]}  Pepe pone {fuera} y el bot {dentro}")
    print(f"\nCAJA: fotos sin un euro libre (saldo - pujas vivas <= 0): {sin_caja}/{n}")
    print(f"\nREVENTA: pujas que pondria el bot (una por jugador y dia): {len(pujas_bot)}")
    foto = {p["name"]: p["id"] for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]}
    for (dia, nombre), (puja, t) in sorted(pujas_bot.items()):
        pid = foto.get(nombre)
        d0 = dt.date.fromisoformat(dia)
        p0 = P.en(pid, d0) if pid else None
        p1 = P.en(pid, P.ultimo_dia) if pid else None
        mov = f"{(p1/p0-1)*100:+.1f}% hasta {P.ultimo_dia}" if p0 and p1 else "sin precio"
        print(f"   {dia}  {nombre:<20} puja {puja:>10,}   precio despues: {mov}")
    print("\nPujas de Pepe esos dias (bid_outcome_ledger):")
    dias = sorted({t[:10] for t, _ in fotos(sys.argv[1:])})
    for dia in dias:
        for nombre, imp, src, out in pepe_pujas.get(dia, []):
            print(f"   {dia}  {nombre:<20} {imp:>10,}  {src}  {out}")
