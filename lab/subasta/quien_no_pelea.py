"""
Laboratorio, experimento 11: ¿se sabe de antemano que subasta NO va a
pelear Pollo17?

E9: de los subastados que suben, Pollo17 puja en el 75 %; los que nadie
pelea se ganan con precio + 1 % y salen 33/33 en verde. Si se pudiera
saber cuales van a quedar solos, Pepe pujaria solo por esos y no gastaria
caja comprometida (una puja viva bloquea saldo) en subastas perdidas.

Variables que se saben al pujar (el dia antes del reset):
  - subida del ultimo cambio (%), racha de dias subiendo, subida en 3 dias;
  - precio; posicion (no esta en el tablon: se usa la foto del 18/09);
  - dias desde el final de la jornada.
Se mide la tasa de «sin pelea» (un solo pujador) por tramos, en la primera
mitad y en la segunda (fuera de muestra).

Uso:  python3 lab/subasta/quien_no_pelea.py
"""
import datetime as dt
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import POLLO, TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)
MITAD = dt.date(2026, 9, 10)


def racha(P, pid, d):
    n = 0
    while True:
        a, b = P.en(pid, d - n * D), P.en(pid, d - (n + 1) * D)
        if a is None or b is None or a <= b:
            return n
        n += 1


def filas(P):
    pos = {p["id"]: p["position"] for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]}
    finales = sorted({dia_de_mercado(e["date"]) for e in json.load(open(TABLON)) if e["type"] == "roundFinished"})
    out = []
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            d = dia_de_mercado(x.get("date", e["date"]))
            pid = x["player"]
            ayer = d - D
            p1 = P.en(pid, ayer)
            t1 = pct(p1, P.en(pid, ayer - D)) if p1 else None
            if t1 is None or t1 <= 0:
                continue
            quien = {x["to"]["id"]} | {b["user"]["id"] for b in x.get("bids") or []}
            prev = [f for f in finales if f <= d]
            out.append(dict(
                dia=d, t1=t1, t3=pct(p1, P.en(pid, ayer - 3 * D)) or 0, racha=racha(P, pid, ayer),
                precio=p1, pos=pos.get(pid), solo=len(quien) == 1, pollo=POLLO in quien,
                tras_jornada=(d - prev[-1]).days if prev else None))
    return out


def tasa(rs):
    return (sum(r["solo"] for r in rs), len(rs))


def linea(nom, rs, mitad=True):
    s, n = tasa(rs)
    t = f"   {nom:<28} n={n:3d}  sin pelea {s:3d} ({s/n:4.0%})" if n else f"   {nom:<28} n=  0"
    if mitad and n:
        a = [r for r in rs if r["dia"] < MITAD]
        b = [r for r in rs if r["dia"] >= MITAD]
        sa, na = tasa(a)
        sb, nb = tasa(b)
        t += f"   | hasta {MITAD:%d/%m}: {sa}/{na}   desde: {sb}/{nb}"
    return t


if __name__ == "__main__":
    P = Precios()
    R = filas(P)
    print(f"{len(R)} subastas de jugadores que SUBIAN; sin pelea {sum(r['solo'] for r in R)}.\n")
    print("Por subida del ultimo cambio:")
    for a, b in ((0, 0.01), (0.01, 0.02), (0.02, 0.04), (0.04, 9)):
        print(linea(f"{a*100:.0f}-{b*100 if b < 9 else 99:.0f} %", [r for r in R if a < r["t1"] <= b]))
    print("Por dias seguidos subiendo:")
    for a, b in ((1, 1), (2, 3), (4, 99)):
        print(linea(f"{a}-{b if b < 99 else '+'} dias", [r for r in R if a <= r["racha"] <= b]))
    print("Por precio:")
    for a, b in ((0, 1e6), (1e6, 3e6), (3e6, 6e6), (6e6, 1e10)):
        print(linea(f"{a/1e6:.0f}-{b/1e6 if b < 1e10 else 99:.0f} M", [r for r in R if a <= r["precio"] < b]))
    print("Por posicion (foto 18/09):")
    for p, nom in ((1, "POR"), (2, "DEF"), (3, "MED"), (4, "DEL"), (None, "sin dato")):
        print(linea(nom, [r for r in R if r["pos"] == p]))
    print("Por dias desde el final de la jornada:")
    for a, b in ((0, 1), (2, 3), (4, 99)):
        print(linea(f"{a}-{b if b < 99 else '+'} dias", [r for r in R if r["tras_jornada"] is not None and a <= r["tras_jornada"] <= b]))
