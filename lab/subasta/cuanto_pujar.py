"""
E37: ¿cuanto hay que pujar para ganar una subasta del Computer, y compensa
para un fichaje que mejora el once?

El caso (13/10): las cuatro ultimas pujas a precio + 1 % (Recio, Ivan
Romero, Gerard Martin, Moi Gomez) se perdieron con rivales que pagaron
+0,5 % a +16 %. El gestor ha dejado apagada «la puja fuerte» (+4 % por
punto por jornada que el fichaje suma al once, hasta +12 %).

Del tablon (subastas del Computer con precio): para cada subasta, la puja
que habia que superar = la del ganador. Con eso, la probabilidad de ganar
pujando precio x (1 + k), para k de 1 % a 20 %, en todas las subastas y en
las que tuvieron pelea. Despues, la cuenta de si compensa: un fichaje que
suma D puntos por jornada durante N jornadas da D x N x 30.000 EUR de
premio (E16) mas los puntos; pujar k % de mas sobre un precio P cuesta
k x P (se pierde al revender, E14: no se revende antes de jugar).

Uso:  python3 lab/subasta/cuanto_pujar.py
"""
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import PEPE, TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D_DIAS = __import__("datetime").timedelta(days=1)

if __name__ == "__main__":
    P = Precios()
    vistos, filas = set(), []
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            k = (x["player"], x["amount"])
            if k in vistos:
                continue
            vistos.add(k)
            d = dia_de_mercado(x.get("date", e["date"]))
            p1 = P.en(x["player"], d - D_DIAS)
            if not p1:
                continue
            otras = [b["amount"] for b in x.get("bids") or []]
            sube = (pct(p1, P.en(x["player"], d - 2 * D_DIAS)) or 0) > 0
            filas.append(dict(gana=x["amount"] / p1 - 1, pelea=bool(otras), sube=sube,
                              precio=p1, pepe=x["to"]["id"] == PEPE))
    print(f"Subastas del Computer con precio: {len(filas)} (con pelea {sum(f['pelea'] for f in filas)})\n")
    print("   puja = precio x (1+k)   ganaria: todas | con pelea | con pelea y sube | con pelea, 3 M o mas")
    for k in (0.01, 0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20):
        def tasa(rs):
            return f"{sum(f['gana'] < k for f in rs)/len(rs):5.0%}" if rs else "  -  "
        pel = [f for f in filas if f["pelea"]]
        print(f"   k = {k*100:4.0f} %            {tasa(filas):>6} | {tasa(pel):>9} | {tasa([f for f in pel if f['sube']]):>16} |"
              f" {tasa([f for f in pel if f['precio'] >= 3e6]):>8}")
    print("\nLa cuenta para un fichaje del once (premio 30.000 EUR por punto, 29 jornadas por delante):")
    for dpts in (1.0, 2.25, 3.0):
        valor = dpts * 29 * 30_000
        for precio in (3e6, 5e6):
            print(f"   +{dpts:.2f} pts/jornada: premio esperado {valor:>10,.0f} EUR;"
                  f" pujar +12 % sobre {precio/1e6:.0f} M cuesta {0.11*precio:>9,.0f} de mas que el +1 %")
