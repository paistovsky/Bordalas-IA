"""
Laboratorio, experimento 8: ¿cuanto dan los VIAJES CORTOS con plazo fijo?

El caso (30/09): Pepe esta en rojo (~-1,3 M) y tiene que estar en verde el
09/10 a las 15:00 sin vender a los top. La estrategia (2) del gestor son
viajes cortos de reventa (compra lo que sube, vende el primer dia que baja,
E1/E3), con tope de 2 M por viaje y 3-4 M en total, todo cerrado antes del
07/10. Su cuenta a ojo: +0,2-0,4 M. Aqui se mide sobre cada semana de la
temporada.

LA SIMULACION, para cada dia de arranque S (ventana de 7 dias):
  - compras: de S a S+5, los jugadores que el Computer subasto ese dia
    (tablon) y cuyo precio SUBIO en el ultimo cambio; se paga lo que pago
    el ganador real + 1 %; tope por viaje y tope de caja total; primero
    los de mas subida en 3 dias;
  - venta: al Computer el primer dia que el precio baja (oferta = precio
    del dia * (1 + prima medida en E3 segun el estado del precio)), o a la
    fuerza el dia S+7 (el plazo) a lo que ofrezca ese dia;
  - el dinero vuelve al dia siguiente de vender.
Se da la ganancia de cada semana y el reparto (mediana, peor, mejor).

Uso:  python3 lab/precio/viajes_con_plazo.py
"""
import datetime as dt
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import COMPUTER, Precios, dia_de_mercado, eventos, pct  # noqa: E402

D = dt.timedelta(days=1)
PRIMA = {1: 0.021, 0: 0.010, -1: 0.032}   # E3: oferta del Computer segun el precio del dia
PLAZO = 7


def estado(P, pid, d):
    a, b = P.en(pid, d), P.en(pid, d - D)
    if a is None or b is None:
        return None
    return (a > b) - (a < b)


def subastas():
    s = defaultdict(dict)
    for ts, pid, comp, vend, imp, _ in eventos():
        if vend == COMPUTER and comp != COMPUTER:
            s[dia_de_mercado(ts)][pid] = imp
    return s


def semana(P, sub, S, caja, tope_viaje):
    fin = S + PLAZO * D
    cartera = {}          # pid -> coste
    libre_desde = []      # (dia, importe) dinero que vuelve
    libre = caja
    pl, n, forzados, pl_forzados = 0.0, 0, 0, 0.0
    d = S
    while d <= fin:
        # vuelve el dinero de ayer
        for x in [x for x in libre_desde if x[0] <= d]:
            libre += x[1]
            libre_desde.remove(x)
        # ventas
        for pid in list(cartera):
            e = estado(P, pid, d)
            p = P.en(pid, d)
            if p is None:
                continue
            if e == -1 or d == fin:
                venta = p * (1 + PRIMA.get(e, 0.0))
                pl += venta - cartera[pid]
                if d == fin and e != -1:
                    forzados += 1
                    pl_forzados += venta - cartera[pid]
                libre_desde.append((d + D, venta))
                del cartera[pid]
        # compras (no en los dos ultimos dias: no daria tiempo a nada)
        if d in sub and d <= fin - 2 * D:
            ayer = d - D
            cands = []
            for pid, imp in sub[d].items():
                t1 = pct(P.en(pid, ayer), P.en(pid, ayer - D))
                if t1 is None or t1 <= 0 or pid in cartera:
                    continue
                coste = imp * 1.01
                if coste > tope_viaje:
                    continue
                cands.append((pct(P.en(pid, ayer), P.en(pid, ayer - 3 * D)) or 0, pid, coste))
            for _, pid, coste in sorted(cands, reverse=True):
                if coste <= libre:
                    cartera[pid] = coste
                    libre -= coste
                    n += 1
        d += D
    return pl, n, forzados, pl_forzados


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2]


if __name__ == "__main__":
    P = Precios()
    sub = subastas()
    arranques = []
    S = P.primer_dia + 4 * D
    while S + PLAZO * D <= P.ultimo_dia:
        arranques.append(S)
        S += D
    print(f"Precios del {P.primer_dia} al {P.ultimo_dia}; {len(arranques)} semanas "
          f"(arranque del {arranques[0]} al {arranques[-1]}).\n")
    for caja, tope in ((2_000_000, 2_000_000), (3_000_000, 2_000_000), (4_000_000, 2_000_000),
                       (4_000_000, 1_000_000)):
        filas = [(S,) + semana(P, sub, S, caja, tope) for S in arranques]
        pls = [f[1] for f in filas]
        print(f"caja {caja/1e6:.0f} M, tope por viaje {tope/1e6:.0f} M: "
              f"mediana {med(pls):>+10,.0f}  peor {min(pls):>+10,.0f}  mejor {max(pls):>+10,.0f}  "
              f"semanas en verde {sum(p > 0 for p in pls)}/{len(pls)}  "
              f"viajes/semana {sum(f[2] for f in filas)/len(filas):.1f}  "
              f"vendidos a la fuerza {sum(f[3] for f in filas)/max(sum(f[2] for f in filas),1):.0%}")
    print("\nSemana a semana (caja 4 M, tope 2 M por viaje):")
    for S in arranques:
        pl, n, fz, plf = semana(P, sub, S, 4_000_000, 2_000_000)
        print(f"   {S} -> {S + PLAZO * D}   {n:2d} viajes  {pl:>+11,.0f}"
              f"   (a la fuerza al final: {fz}, {plf:>+10,.0f})")
