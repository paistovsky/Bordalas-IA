"""
E69: lo que cuesta la caja parada. Pepe no compra para revender desde el
16/10 (la cartera, 0 compras; con caja libre el 35 % de las horas). ¿Que
habria hecho una regla sencilla con la caja que habia?

Regla: cada dia, por cada jugador del escaparate (los 20 del Computer) que
SUBIO la vispera y vale menos de 1,5 M, pujar precio x 1,01 terminado en
9.900. Se gana si en el tablon nadie se lo llevo por mas (si nadie se lo
llevo, se gana a esa puja). Viaje: vender al Computer el primer dia que no
sube, a precio x 1,007 (E3/E38). Tope de caja: TOPE (lo que habia libre).

Uso:  python3 lab/caja/dinero_quieto.py [desde AAAA-MM-DD] [tope]
"""
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import TABLON, Precios, dia_de_mercado  # noqa: E402

ESC = RAIZ / "data/trading/libro_del_escaparate.jsonl"
D = dt.timedelta(days=1)


def viaje(P, pid, dia, coste):
    prev, d = P.en(pid, dia), dia
    for _ in range(30):
        d += D
        p = P.en(pid, d)
        if p is None:
            return None
        if p <= prev:
            return p * 1.007 - coste, d
        prev = p
    return None


if __name__ == "__main__":
    desde = dt.date.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-10-16")
    tope = float(sys.argv[2]) if len(sys.argv) > 2 else 1_400_000
    P = Precios()
    ganador = {}
    for e in json.load(open(TABLON)):
        if e["type"] == "market":
            for x in e["content"]:
                ganador[(x["player"], dia_de_mercado(x.get("date", e["date"])))] = x["amount"]
    abiertos, cerrados, perdidas = [], [], 0
    for l in open(ESC):
        r = json.loads(l)
        d = dt.date.fromisoformat(r["dia_de_mercado"])
        if d < desde or d >= P.ultimo_dia - 2 * D:
            continue
        # cerrar los que ya se vendieron
        for v in list(abiertos):
            if v["vende"] <= d:
                abiertos.remove(v)
        libre = tope - sum(v["coste"] for v in abiertos)
        for j in sorted(r["players"], key=lambda j: j["price"]):
            # El escaparate del dia d se escribe ~05:20 UTC, justo despues del
            # reset: es la lista del dia anterior, cuya subasta YA se resolvio en
            # ese reset (dia de mercado d). Corregido el 29/10 tras E69.
            p0, p_1 = P.en(j["id"], d - D), P.en(j["id"], d - 2 * D)
            if not (p0 and p_1) or p0 <= p_1 or p0 >= 1.5e6:
                continue
            puja = int(p0 * 1.01) // 10_000 * 10_000 + 9_900
            if puja > libre:
                continue
            # una salida del Computer dura dos dias (E61): la subasta puede
            # resolverse en este reset o en el siguiente
            otros = [ganador.get((j["id"], d)), ganador.get((j["id"], d + D))]
            otro = max((o for o in otros if o is not None), default=None)
            if otro is not None and otro >= puja:
                perdidas += 1
                continue
            v = viaje(P, j["id"], d, puja)
            if v is None:
                continue
            res, vende = v
            abiertos.append(dict(coste=puja, vende=vende))
            cerrados.append((d, j["name"], puja, res))
            libre -= puja
    print(f"Desde {desde}, tope de caja {tope:,.0f}: {len(cerrados)} compras ganadas, {perdidas} perdidas contra un rival")
    for d, n, c, r in cerrados:
        print(f"   {d}  {n[:18]:18} {c:>10,}  {r:+10,.0f}")
    print(f"\nResultado: {sum(c[3] for c in cerrados):+,.0f} EUR")
