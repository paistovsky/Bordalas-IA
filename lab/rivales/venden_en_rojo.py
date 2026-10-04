"""
E18: ¿un rival en rojo antes de la jornada vende BARATO a otro manager?

El caso (04/10): Luismi_Haz (-17 M) y DiosMande (-9,8 M) tienen que estar
en verde antes de la J8 y ponen jugadores a la venta. La esperanza: que
alguno salga por debajo de su valor.

La sospecha: un manager en rojo siempre puede vender al Computer, que paga
el precio + 1-3 % (E3). Si el Computer paga eso, no tiene por que regalar
nada a otro manager. Se mide en el tablon:
  1) los traspasos de manager a manager (con «to»): importe / precio del dia;
  2) las ventas de los rivales al Computer en las 48 h antes de que empiece
     una jornada (las de prisa) contra el resto: importe / precio del dia.

Uso:  python3 lab/rivales/venden_en_rojo.py
"""
import datetime as dt
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from viajes import PEPE, TABLON, Precios, dia_de_mercado  # noqa: E402


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


if __name__ == "__main__":
    P = Precios()
    ev = json.load(open(TABLON))
    inicios = sorted({e["date"] for e in ev if e["type"] == "roundStarted"})
    vistos = set()
    m2m, prisa, resto = [], [], []
    for e in ev:
        if e["type"] != "transfer":
            continue
        for x in e["content"]:
            k = (x["player"], x["amount"], x["from"]["id"])
            if k in vistos:
                continue
            vistos.add(k)
            p = P.en(x["player"], dia_de_mercado(e["date"]))
            if not p:
                continue
            r = x["amount"] / p - 1
            if "to" in x:
                m2m.append((dt.datetime.utcfromtimestamp(e["date"]).date(), x["from"]["name"],
                            x["to"]["name"], x["amount"], p, r))
            elif x["from"]["id"] != PEPE:
                antes = any(0 <= s - e["date"] <= 48 * 3600 for s in inicios)
                (prisa if antes else resto).append(r)
    print(f"1) Traspasos de manager a manager con precio: {len(m2m)}")
    for d, de, a, imp, p, r in sorted(m2m):
        print(f"   {d}  {de[:14]:<14} -> {a[:14]:<14} {imp:>11,}  precio {p:>11,}  {r*100:+6.1f}%")
    print(f"   mediana {med([x[5] for x in m2m])*100:+.1f}%; por debajo del precio: {sum(x[5] < 0 for x in m2m)}/{len(m2m)}")
    print("\n2) Ventas de los rivales al Computer (importe / precio del dia):")
    print(f"   en las 48 h antes de empezar una jornada: n={len(prisa):3d}  mediana {med(prisa)*100:+.1f}%"
          f"  por debajo del precio {sum(r < 0 for r in prisa)}")
    print(f"   el resto del tiempo:                      n={len(resto):3d}  mediana {med(resto)*100:+.1f}%"
          f"  por debajo del precio {sum(r < 0 for r in resto)}")
