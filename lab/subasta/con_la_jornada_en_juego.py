"""
E59: la pelea en las subastas segun el momento de la semana: el reset de
la vispera (E57), los resets con la jornada en juego, y los de entre
jornadas. Hoy (24/10, J10 en juego) Pepe perdio tres pujas (Catena por
21.100, Revivo y Thiago Fernandez) y Luismi compro cinco.

Del tablon: para cada subasta del Computer, si al resolverse hay una ronda
empezada y sin terminar (roundStarted sin su roundFinished), las horas
hasta la siguiente roundStarted; pelea y prima del ganador.

Uso:  python3 lab/subasta/con_la_jornada_en_juego.py
"""
import bisect
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)
PRINCIPALES = lambda n: "aplazada" not in n  # noqa: E731

if __name__ == "__main__":
    ev = json.load(open(TABLON))
    ini, fin = {}, {}
    for e in ev:
        if e["type"] in ("roundStarted", "roundFinished"):
            r = e["content"]["round"]
            if PRINCIPALES(r["name"]):
                (ini if e["type"] == "roundStarted" else fin).setdefault(r["id"], e["date"])
    inicios = sorted(ini.values())
    P = Precios()
    filas, vistos = [], set()
    for e in ev:
        if e["type"] != "market":
            continue
        for x in e["content"]:
            t = x.get("date", e["date"])
            if (x["player"], x["amount"]) in vistos:
                continue
            vistos.add((x["player"], x["amount"]))
            en_juego = any(ini[r] <= t < fin.get(r, 9e18) and t - ini[r] < 6 * 86400 for r in ini)
            i = bisect.bisect_right(inicios, t)
            horas = (inicios[i] - t) / 3600 if i < len(inicios) else 9999
            d = dia_de_mercado(t)
            p1, p2 = P.en(x["player"], d - D), P.en(x["player"], d - 2 * D)
            if not p1:
                continue
            momento = "en juego" if en_juego else ("vispera (<24 h)" if horas < 24 else "entre jornadas")
            filas.append(dict(m=momento, pelea=bool(x.get("bids")), n=len(x.get("bids") or []) + 1,
                              prima=x["amount"] / p1 - 1, sube=(pct(p1, p2) or 0) > 0))
    print(f"Subastas: {len(filas)}\n")
    print("  momento              n   con pelea   pujadores   prima (mediana)   las que suben: n / pelea / prima con pelea")
    for m in ("vispera (<24 h)", "en juego", "entre jornadas"):
        g = [f for f in filas if f["m"] == m]
        s = [f for f in g if f["sube"]]
        sp = [f["prima"] for f in s if f["pelea"]]
        print(f"  {m:17} {len(g):>4}     {sum(f['pelea'] for f in g)/len(g):4.0%}      {st.mean(f['n'] for f in g):4.2f}"
              f"        {st.median(f['prima'] for f in g):+6.1%}          {len(s):>3} / {sum(f['pelea'] for f in s)/len(s):4.0%}"
              f" / {st.median(sp) if sp else 0:+.1%}")
