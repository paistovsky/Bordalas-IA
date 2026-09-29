"""
Laboratorio, experimento 5: ¿vender el primer dia que baja (E1/E3) o
aceptar la primera oferta del Computer >= coste + 1 % (salida_del_viaje.py)?

Pregunta del gestor (29/09 07:15): comparar las dos con la misma vara
(%/dia, con el capital limitado de Pepe) y decir por donde vende Pepe hoy.

LAS DOS SALIDAS, sobre las MISMAS compras:
  E1   vender al Computer el primer dia en que el precio baja.
  VIAJE  cada reset el Computer ofrece precio_del_dia * (1 + prima); se
         acepta la primera >= coste * 1,01. Tras 4 resets sin aceptar, el
         viaje caduca y pasa a E1 (el modulo no fuerza la venta).
  La prima de cada dia se saca al azar de las 202 ventas reales al
  Computer del tablon, segun el precio haya subido, quedado o bajado ese
  dia (semilla fija, 50 repeticiones). E1 usa la mediana de cada estado.

DOS VARAS:
  1) Sin tope de caja: todas las entradas de la rampa (jugador-dia cuyo
     precio subio), coste precio * 1,022. %/dia con un dia muerto por
     viaje.
  2) Con la caja de Pepe: solo lo que el Computer subasto (tablon), puja
     = ganador real + 1 %, CAPITAL euros como mucho a la vez, del 20/08
     al 28/09. Lo abierto al final, a precio de hoy.

Y 3) como vende Pepe de verdad: sus ventas del tablon.

Uso:  python3 lab/precio/salida_contra_viaje.py
"""
import datetime as dt
import random
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import COMPUTER, PEPE, Precios, dia_de_mercado, eventos, pct, viajes  # noqa: E402

D = dt.timedelta(days=1)
SUELO = 0.01
RESETS = 4
PRIMA_COMPRA = 0.022


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def estado_en(P, pid, d):
    a, b = P.en(pid, d), P.en(pid, d - D)
    if a is None or b is None:
        return None
    return (a > b) - (a < b)


def primas_reales(P):
    por = defaultdict(list)
    for ts, pid, comp, vend, imp, _ in eventos():
        if comp == COMPUTER and vend != COMPUTER:
            d = dia_de_mercado(ts)
            e = estado_en(P, pid, d)
            if e is not None:
                por[e].append(imp / P.en(pid, d) - 1)
    return por


def salida(P, pid, d0, coste, regla, primas, rng):
    """Devuelve (dia de venta, importe) o (None, valor a precio de hoy)."""
    d, n = d0, 0
    modo = regla
    while d < P.ultimo_dia:
        d += D
        p = P.en(pid, d)
        e = estado_en(P, pid, d)
        if p is None or e is None:
            continue
        n += 1
        if modo == "VIAJE":
            oferta = p * (1 + rng.choice(primas[e]))
            if oferta >= coste * (1 + SUELO):
                return d, oferta
            if n >= RESETS:
                modo = "E1"
        if modo == "E1" and e == -1:
            return d, p * (1 + med(primas[-1]))
    return None, P.en(pid, P.ultimo_dia) or coste


def vara_sin_tope(P, regla, primas, reps):
    tot, dias, verdes, n = 0.0, 0, 0, 0
    for r in range(reps):
        rng = random.Random(r)
        for pid, (ds, ps) in P.por_jugador.items():
            for i in range(1, len(ps) - 1):
                if (ds[i] - ds[i - 1]).days > 2 or ps[i] <= ps[i - 1]:
                    continue
                coste = ps[i] * (1 + PRIMA_COMPRA)
                dv, imp = salida(P, pid, ds[i], coste, regla, primas, rng)
                fin = dv or P.ultimo_dia
                roi = imp / coste - 1
                tot += roi
                dias += (fin - ds[i]).days + 1
                verdes += roi > 0
                n += 1
    return n // reps, verdes / n, tot / n, tot / dias


def vara_con_caja(P, regla, primas, capital, reps):
    subastas = defaultdict(dict)
    for ts, pid, comp, vend, imp, _ in eventos():
        if vend == COMPUTER and comp != COMPUTER:
            subastas[dia_de_mercado(ts)][pid] = imp
    inicio = P.primer_dia + 4 * D
    res = []
    for r in range(reps):
        rng = random.Random(r)
        caja_libre_desde = []  # (dia en que vuelve el dinero, importe)
        cerrado_pl, abierto_pl, nviajes = 0.0, 0.0, 0
        metido = {}  # pid -> (coste, dia venta o None)
        d = inicio
        while d <= P.ultimo_dia:
            # el dinero de lo vendido vuelve el dia de la venta (se puja para manana)
            for pid in [k for k, v in metido.items() if v[1] is not None and v[1] < d]:
                del metido[pid]
            if d in subastas:
                ayer = d - D
                cands = []
                for pid, imp in subastas[d].items():
                    t1 = pct(P.en(pid, ayer), P.en(pid, ayer - D))
                    if t1 is None or t1 <= 0 or pid in metido:
                        continue
                    t3 = pct(P.en(pid, ayer), P.en(pid, ayer - 3 * D)) or 0
                    cands.append((t3, pid, imp * 1.01))
                usado = sum(v[0] for v in metido.values())
                for _, pid, coste in sorted(cands, reverse=True):
                    if usado + coste > capital:
                        continue
                    dv, imp = salida(P, pid, d, coste, regla, primas, rng)
                    metido[pid] = (coste, dv)
                    usado += coste
                    nviajes += 1
                    if dv is None:
                        abierto_pl += imp - coste
                    else:
                        cerrado_pl += imp - coste
            d += D
        res.append((nviajes, cerrado_pl, abierto_pl))
    n = len(res)
    return (sum(x[0] for x in res) / n, sum(x[1] for x in res) / n, sum(x[2] for x in res) / n)


def como_vende_pepe(P):
    _, cerrados = viajes(P)
    ps = [c for c in cerrados if c["manager"] == "Pepe"]
    print("\n3) Como vende Pepe de verdad (sus viajes cerrados del tablon):")
    print(f"   n={len(ps)}; al Computer {sum(c['a_quien']=='COMPUTER' for c in ps)}")
    print(f"   dias con la ficha (mediana) {med([c['dias'] for c in ps])};"
          f" vendidos al 1er reset {sum(c['dias']<=1 for c in ps)}; a 2-4 {sum(2<=c['dias']<=4 for c in ps)};"
          f" a 5+ {sum(c['dias']>=5 for c in ps)}")
    est = defaultdict(int)
    for c in ps:
        e = estado_en(P, c["jugador"], dt.date.fromisoformat(c["venta_dia"]))
        est[e] += 1
    print(f"   el dia de la venta el precio: subio {est[1]}, quieto {est[0]}, bajo {est[-1]}, sin dato {est[None]}")
    ult = [c for c in ps if c["venta_dia"] >= "2026-09-14"]
    print(f"   desde el 14/09: n={len(ult)}, P&L {sum(c['pl'] for c in ult):+,}; "
          f"cobrados >= coste+1 %: {sum(c['venta'] >= c['compra']*1.01 for c in ult)}")
    for c in ult:
        print(f"     {c['dia']} -> {c['venta_dia']}  {c['dias']:2d} d  compra {c['compra']:>10,}"
              f"  venta {c['venta']:>10,}  {c['pl']:>+10,}")


if __name__ == "__main__":
    P = Precios()
    primas = primas_reales(P)
    print(f"Precios del {P.primer_dia} al {P.ultimo_dia}. Primas reales del Computer: "
          + ", ".join(f"{k:+d}: n={len(v)} med {med(v)*100:+.1f}%" for k, v in sorted(primas.items())))
    print("\n1) Sin tope de caja (todas las entradas de la rampa, 50 repeticiones):")
    for regla in ("E1", "VIAJE"):
        n, verde, roi, dia = vara_sin_tope(P, regla, primas, 1 if regla == "E1" else 50)
        print(f"   {regla:<6} n={n:5d}  verde {verde:5.1%}  ROI medio {roi*100:+5.1f}%  %/dia {dia*100:+.2f}%")
    print("\n2) Con la caja de Pepe (solo lo subastado, puja = ganador + 1 %):")
    for cap in (2_000_000, 5_000_000, 10_000_000):
        for regla in ("E1", "VIAJE"):
            nv, c, a = vara_con_caja(P, regla, primas, cap, 1 if regla == "E1" else 50)
            print(f"   caja {cap/1e6:>4.0f} M  {regla:<6} viajes {nv:5.1f}  cerrado {c:>+12,.0f}"
                  f"  abierto {a:>+12,.0f}  total {c+a:>+12,.0f}")
    como_vende_pepe(P)
