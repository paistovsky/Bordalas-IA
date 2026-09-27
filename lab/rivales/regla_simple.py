"""
Laboratorio, experimento 1b: ¿una regla simple imita a Pollo17?

LA REGLA («compra lo que sube, vende cuando baja»):
  - Compra: el dia D, de los jugadores que el Computer subasto ese dia
    (los que salen en el tablon como `market`), los que SUBIERON en el
    ultimo cambio de precio (el de D-1). Se paga lo que pago el ganador
    real + 1 % (hay que ganarle la puja).
  - Venta: el primer dia en que su precio BAJA, al Computer, a precio del
    dia * (1 + prima del Computer). La prima es la mediana medida en el
    tablon (204 ventas al Computer: +2,4 %).
  - Presupuesto: como mucho CAPITAL euros metidos a la vez; si no llega,
    se compran primero los de mayor subida en 3 dias.

Es una cota optimista en una cosa (se supone que se gana la puja con +1 %
sobre el ganador) y pesimista en otra (solo ve los jugadores que alguien
compro: los que nadie compro no los conocemos). Se dice en el resultado.

Uso:  python3 lab/rivales/regla_simple.py
"""
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from viajes import COMPUTER, NOMBRES, Precios, dia_de_mercado, eventos, pct, viajes  # noqa: E402

PRIMA_COMPUTER = 0.024   # mediana medida, ver prima de venta
SOBREPUJA = 0.01


def simular(precios, capital=10_000_000, min_tend_1d=0.0, max_tend_1d=None, min_tend_3d=None,
            vender_tras_bajadas=1, desde=None, hasta=None):
    # la subasta de cada dia: jugador -> lo que pago el ganador
    subastas = defaultdict(dict)
    for ts, pid, comprador, vendedor, imp, pujas in eventos():
        if vendedor == COMPUTER and comprador != COMPUTER:
            subastas[dia_de_mercado(ts)][pid] = imp
    dias = sorted(d for d in subastas if precios.primer_dia + dt.timedelta(days=4) <= d)
    if desde:
        dias = [d for d in dias if d >= desde]
    if hasta:
        dias = [d for d in dias if d <= hasta]
    fin = precios.ultimo_dia
    cartera = {}   # pid -> dict(coste, dia, bajadas)
    viajes_ = []
    d = dias[0]
    while d <= fin:
        # 1) ventas: el cambio de precio de hoy
        for pid in list(cartera):
            hoy, ayer = precios.en(pid, d), precios.en(pid, d - dt.timedelta(days=1))
            pos = cartera[pid]
            if hoy is None or ayer is None:
                continue
            pos["bajadas"] = pos["bajadas"] + 1 if hoy < ayer else 0
            if pos["bajadas"] >= vender_tras_bajadas:
                venta = round(hoy * (1 + PRIMA_COMPUTER))
                viajes_.append(dict(jugador=pid, dia=pos["dia"], venta_dia=str(d),
                                    compra=pos["coste"], venta=venta,
                                    pl=venta - pos["coste"], abierto=False))
                del cartera[pid]
        # 2) compras: la subasta de hoy
        if d in subastas and (hasta is None or d <= hasta):
            ayer = d - dt.timedelta(days=1)
            cands = []
            for pid, imp in subastas[d].items():
                if pid in cartera:
                    continue
                p1 = precios.en(pid, ayer)
                t1 = pct(p1, precios.en(pid, ayer - dt.timedelta(days=1)))
                t3 = pct(p1, precios.en(pid, ayer - dt.timedelta(days=3)))
                if t1 is None or t1 <= min_tend_1d:
                    continue
                if max_tend_1d is not None and t1 > max_tend_1d:
                    continue
                if min_tend_3d is not None and (t3 is None or t3 <= min_tend_3d):
                    continue
                cands.append((t3 or 0, pid, round(imp * (1 + SOBREPUJA))))
            metido = sum(p["coste"] for p in cartera.values())
            for _, pid, coste in sorted(cands, reverse=True):
                if metido + coste > capital:
                    continue
                cartera[pid] = dict(coste=coste, dia=str(d), bajadas=0)
                metido += coste
        d += dt.timedelta(days=1)
    # lo que queda abierto, a precio de hoy (sin prima: aun no se ha vendido)
    for pid, pos in cartera.items():
        v = precios.en(pid, fin) or pos["coste"]
        viajes_.append(dict(jugador=pid, dia=pos["dia"], venta_dia=None, compra=pos["coste"],
                            venta=v, pl=v - pos["coste"], abierto=True))
    return viajes_


def linea(nombre, vs):
    cer = [v for v in vs if not v["abierto"]]
    ab = [v for v in vs if v["abierto"]]
    pl_c = sum(v["pl"] for v in cer)
    pl_a = sum(v["pl"] for v in ab)
    verde = sum(v["pl"] > 0 for v in cer)
    return (f"{nombre:<44} cerrados n={len(cer):3d}  verde {verde:3d}/{len(cer):<3d} "
            f"P&L {pl_c:>+13,}   abiertos n={len(ab):2d} {pl_a:>+12,}")


def por_compra(precios):
    """Cada compra real al Computer, saliendo el primer dia que baja."""
    out = []
    for ts, pid, comprador, vendedor, imp, pujas in eventos():
        if vendedor != COMPUTER or comprador == COMPUTER:
            continue
        d = dia_de_mercado(ts)
        ayer = d - dt.timedelta(days=1)
        p1 = precios.en(pid, ayer)
        t1 = pct(p1, precios.en(pid, ayer - dt.timedelta(days=1)))
        if t1 is None:
            continue
        e = d
        abierto = True
        while e < precios.ultimo_dia:
            e += dt.timedelta(days=1)
            hoy, prev = precios.en(pid, e), precios.en(pid, e - dt.timedelta(days=1))
            if hoy is not None and prev is not None and hoy < prev:
                abierto = False
                break
        v = precios.en(pid, e) or imp
        venta = v if abierto else round(v * (1 + PRIMA_COMPUTER))
        out.append(dict(t1=t1, pl=venta - imp, roi=venta / imp - 1, dias=(e - d).days, abierto=abierto))
    return out


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    P = Precios()
    compras, cerrados = viajes(P)
    print(f"Precios del {P.primer_dia} al {P.ultimo_dia}. Viajes reales (cerrados), mismo tramo:")
    for m in ("Pollo17", "Luismi_Haz", "Pepe"):
        vs = [dict(pl=c["pl"], abierto=False) for c in cerrados
              if c["manager"] == m and c["precio_ayer"] is not None]
        print("  " + linea(m + " (real)", vs))
    print("\nLa regla, con distintos presupuestos y umbrales:")
    for cap in (5_000_000, 10_000_000, 20_000_000):
        for t1, t3, nb in ((0.0, None, 1), (0.0, 0.03, 1), (0.0, None, 2)):
            vs = simular(P, capital=cap, min_tend_1d=t1, min_tend_3d=t3, vender_tras_bajadas=nb)
            nombre = f"cap {cap/1e6:.0f}M, sube>0{'' if t3 is None else ', 3d>3%'}, vende tras {nb} bajada(s)"
            print("  " + linea(nombre, vs))
    print("\nLa regla AL REVES (compra solo lo que NO subio, como Pepe hoy), cap 10M:")
    print("  " + linea("no subio ayer, vende tras 1 bajada",
                       simular(P, capital=10_000_000, min_tend_1d=-1.0, max_tend_1d=0.0)))
    mitad = P.primer_dia + (P.ultimo_dia - P.primer_dia) / 2
    print("\nLa regla (cap 10M, sube>0, 1 bajada) por mitades:")
    print("  " + linea(f"compras hasta {mitad}", simular(P, hasta=mitad)))
    print("  " + linea(f"compras desde {mitad + dt.timedelta(days=1)}",
                       simular(P, desde=mitad + dt.timedelta(days=1))))
    print("\nSin presupuesto: TODAS las compras reales al Computer (los 8 managers),")
    print("al precio que pagaron, pero saliendo con la regla (primera bajada):")
    por = por_compra(P)
    for etiqueta, fil in (("subio ayer", lambda r: r["t1"] > 0), ("NO subio ayer", lambda r: r["t1"] <= 0)):
        rs = [r for r in por if fil(r)]
        cer = [r for r in rs if not r["abierto"]]
        roi = sorted(r["roi"] for r in cer)
        med = roi[len(roi) // 2] if roi else 0
        print(f"  {etiqueta:<14} n={len(rs):3d} cerrados={len(cer):3d} verde {sum(r['roi']>0 for r in cer):3d}/{len(cer):<3d}"
              f" ROI mediano {med*100:+5.1f}%  dias med {sorted(r['dias'] for r in cer)[len(cer)//2] if cer else 0:2d}"
              f"  P&L {sum(r['pl'] for r in cer):>+12,}")
    print("  (sus viajes reales, mismas compras, con la salida que eligieron ellos, arriba)")

