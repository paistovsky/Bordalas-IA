"""
E76: ¿pone el Computer en el mercado a los que estan subiendo? E61 vio que
elige casi al azar segun el precio. Aqui: el dia que un jugador ENTRA en la
lista (primer dia de sus dos), ¿subia su precio la vispera mas a menudo
que el resto de jugadores ese mismo dia? Y despues de entrar, ¿sube?

Datos: libro_del_escaparate.jsonl (la lista del dia d se escribe tras el
reset: es la del dia d-1, E70) y el historial de precios (todos los
jugadores con precio esos dias como «resto»).

Uso:  python3 lab/mercado/sube_el_que_sale.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios  # noqa: E402

ESC = RAIZ / "data/trading/libro_del_escaparate.jsonl"
D = dt.timedelta(days=1)

if __name__ == "__main__":
    P = Precios()
    listas = {}
    for l in open(ESC):
        r = json.loads(l)
        listas[dt.date.fromisoformat(r["dia_de_mercado"]) - D] = {p["id"] for p in r["players"]}
    dias = sorted(listas)
    entra = sube_e = n_e = 0
    sube_r = n_r = 0
    tras = []
    for d in dias:
        nuevos = listas[d] - listas.get(d - D, set())
        for pid, (ds, ps) in P.por_jugador.items():
            p0, p_1 = P.en(pid, d), P.en(pid, d - D)
            if not (p0 and p_1):
                continue
            s = p0 > p_1
            if pid in nuevos:
                n_e += 1
                sube_e += s
                p2 = P.en(pid, d + 2 * D)
                if p2:
                    tras.append(p2 / p0 - 1)
            else:
                n_r += 1
                sube_r += s
    print(f"Dias de lista: {len(dias)}; entradas nuevas: {n_e}")
    print(f"   subio el dia que entra en la lista: {sube_e/n_e:.0%}   (el resto de jugadores ese dia: {sube_r/n_r:.0%}, n={n_r})")
    tras.sort()
    print(f"   precio 2 dias despues de entrar: mediana {tras[len(tras)//2]:+.1%}, suben {sum(t > 0 for t in tras)/len(tras):.0%}")
