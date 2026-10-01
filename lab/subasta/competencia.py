"""
Laboratorio, experimento 9: ¿hay viajes que ganar SIN pelearse con Pollo17?

El caso (01/10): Pollo17 gano las dos pujas grandes de la orden (Fofana
+8 %, Akhomach +40 % sobre nuestra puja). El gestor: «con la caja que
tenemos no se le gana una subasta disputada; los viajes cortos tienen que
ir a jugadores que nadie mas puja». Aqui se mide si eso existe.

Datos: las subastas del Computer en el tablon (`market`), con la puja
ganadora y las perdedoras, y price_history.json.
Para cada subasta resuelta el dia D:
  - pujadores (ganador + perdedores) y si pujo Pollo17 / Luismi_Haz;
  - el precio subio en el ultimo cambio antes de pujar (la rampa)?
  - prima del ganador sobre el precio de ayer y sobre la 2.a puja;
  - el viaje: comprado a lo que pago el ganador, vendido al Computer el
    primer dia que baja (E3) o a precio de hoy si sigue abierto.

Uso:  python3 lab/subasta/competencia.py
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
from viajes import LUISMI, PEPE, POLLO, TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)
PRIMA = {1: 0.021, 0: 0.010, -1: 0.032}


def med(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def estado(P, pid, d):
    a, b = P.en(pid, d), P.en(pid, d - D)
    if a is None or b is None:
        return None
    return (a > b) - (a < b)


def viaje(P, pid, d0, coste):
    d = d0
    while d < P.ultimo_dia:
        d += D
        e = estado(P, pid, d)
        if e == -1:
            return P.en(pid, d) * (1 + PRIMA[-1]) / coste - 1, (d - d0).days, True
    p = P.en(pid, P.ultimo_dia)
    return (p / coste - 1 if p else None), (P.ultimo_dia - d0).days, False


def subastas(P):
    out = []
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            d = dia_de_mercado(x.get("date", e["date"]))
            pid = x["player"]
            ayer = d - D
            p1 = P.en(pid, ayer)
            if p1 is None:
                continue
            t1 = pct(p1, P.en(pid, ayer - D))
            perd = sorted((b["amount"] for b in x.get("bids") or []), reverse=True)
            quien = {x["to"]["id"]} | {b["user"]["id"] for b in x.get("bids") or []}
            roi, dias, cerrado = viaje(P, pid, d, x["amount"])
            out.append(dict(
                dia=d, pid=pid, ganador=x["to"]["id"], importe=x["amount"], precio=p1,
                pujadores=1 + len(perd), sube=t1 is not None and t1 > 0,
                prima=x["amount"] / p1 - 1, sobre_2a=(x["amount"] / perd[0] - 1) if perd else None,
                pollo=POLLO in quien, luismi=LUISMI in quien, pepe=PEPE in quien,
                roi=roi, dias=dias, cerrado=cerrado))
    return out


def tabla(nom, rs):
    if not rs:
        return f"   {nom:<40} n=  0"
    rois = [r["roi"] for r in rs if r["roi"] is not None]
    return (f"   {nom:<40} n={len(rs):3d}  prima del ganador {med([r['prima'] for r in rs])*100:+5.1f}%"
            f"  viaje: verde {sum(x > 0 for x in rois)}/{len(rois)}  ROI med {med(rois)*100:+5.1f}%"
            f"  medio {sum(rois)/len(rois)*100:+5.1f}%  importe med {med([r['importe'] for r in rs])/1e6:4.2f} M")


if __name__ == "__main__":
    P = Precios()
    S = subastas(P)
    print(f"{len(S)} subastas del Computer con precio ({min(r['dia'] for r in S)} a {max(r['dia'] for r in S)}).\n")

    print("1) Cuanta pelea hay:")
    for k in (1, 2, 3):
        rs = [r for r in S if (r["pujadores"] == k if k < 3 else r["pujadores"] >= 3)]
        print(f"   {k}{'+' if k == 3 else ' '} pujador(es): {len(rs):3d}  "
              f"(suben {sum(r['sube'] for r in rs)})  pujo Pollo17 en {sum(r['pollo'] for r in rs)}")
    sub = [r for r in S if r["sube"]]
    print(f"   De los que SUBEN (n={len(sub)}): solos {sum(r['pujadores']==1 for r in sub)}, "
          f"con Pollo17 {sum(r['pollo'] for r in sub)}, con Luismi {sum(r['luismi'] for r in sub)}")
    nos = [r for r in S if not r["sube"]]
    print(f"   De los que NO suben (n={len(nos)}): solos {sum(r['pujadores']==1 for r in nos)}, "
          f"con Pollo17 {sum(r['pollo'] for r in nos)}")

    print("\n2) Cuanto paga el ganador sobre el precio (mediana) y que tal el viaje:")
    print(tabla("SUBE, un solo pujador", [r for r in sub if r["pujadores"] == 1]))
    print(tabla("SUBE, disputada sin Pollo17", [r for r in sub if r["pujadores"] > 1 and not r["pollo"]]))
    print(tabla("SUBE, con Pollo17 pujando", [r for r in sub if r["pollo"]]))
    print(tabla("NO sube, un solo pujador", [r for r in nos if r["pujadores"] == 1]))
    print(tabla("NO sube, disputada", [r for r in nos if r["pujadores"] > 1]))

    print("\n3) Por tramo de precio, los que SUBEN:")
    for a, b in ((0, 1e6), (1e6, 3e6), (3e6, 6e6), (6e6, 1e9)):
        rs = [r for r in sub if a <= r["precio"] < b]
        print(tabla(f"{a/1e6:.0f}-{b/1e6 if b < 1e9 else 99:.0f} M", rs)
              + f"  solos {sum(r['pujadores']==1 for r in rs)}/{len(rs)}  Pollo17 {sum(r['pollo'] for r in rs)}")

    print("\n4) Lo que paga el ganador sobre la SEGUNDA puja (disputadas):")
    for nom, f in (("gana Pollo17", lambda r: r["ganador"] == POLLO),
                   ("gana Luismi_Haz", lambda r: r["ganador"] == LUISMI),
                   ("gana Pepe", lambda r: r["ganador"] == PEPE),
                   ("gana otro", lambda r: r["ganador"] not in (POLLO, LUISMI, PEPE))):
        rs = [r for r in S if r["sobre_2a"] is not None and f(r)]
        if rs:
            print(f"   {nom:<16} n={len(rs):3d}  sobre la 2.a puja {med([r['sobre_2a'] for r in rs])*100:+5.1f}%"
                  f"  sobre el precio {med([r['prima'] for r in rs])*100:+5.1f}%")
    pepe_perd = [r for r in S if r["pepe"] and r["ganador"] != PEPE]
    print(f"\n   Subastas en que pujo Pepe y PERDIO: {len(pepe_perd)}; ganadas: "
          f"{sum(1 for r in S if r['ganador'] == PEPE)}; perdidas contra Pollo17: "
          f"{sum(r['ganador'] == POLLO for r in pepe_perd)}")


def pujar_a_todos(P, factor):
    """Regla: pujar precio*factor por TODO el que sube. Se gana si ninguna otra
    puja (ganador real incluido) llega a la nuestra. Viaje como E3."""
    gan = []
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
            otras = [x["amount"]] + [b["amount"] for b in x.get("bids") or []]
            if x["to"]["id"] == PEPE:   # nuestra propia puja no compite contra nosotros
                otras = [b["amount"] for b in x.get("bids") or []]
            puja = p1 * factor
            if otras and max(otras) >= puja:
                continue
            roi, dias, cerrado = viaje(P, pid, d, puja)
            if roi is not None:
                gan.append((d, puja, roi))
    return gan


if __name__ == "__main__":
    print("\n5) La regla «pujar poco por TODOS los que suben» (se gana solo si nadie puja mas):")
    for f in (1.00, 1.01, 1.03, 1.05, 1.10):
        g = pujar_a_todos(P, f)
        rois = [x[2] for x in g]
        pl = sum(x[1] * x[2] for x in g)
        mitad = dt.date(2026, 9, 8)
        a = [x for x in g if x[0] < mitad]
        b = [x for x in g if x[0] >= mitad]
        print(f"   precio x {f:.2f}: ganadas {len(g):3d}  verde {sum(r > 0 for r in rois)}/{len(rois)}"
              f"  ROI med {med(rois)*100:+5.1f}%  P&L {pl:>+12,.0f}  metido {sum(x[1] for x in g)/1e6:5.1f} M"
              f"  | hasta 07/09: {len(a)} ({sum(x[1]*x[2] for x in a):>+11,.0f})  desde 08/09: {len(b)} ({sum(x[1]*x[2] for x in b):>+11,.0f})")


def semanas_sin_pelea(P, factor=1.01, caja=4_000_000, tope=2_000_000):
    """E8 rehecho: solo se ganan las subastas en que nadie pujo >= precio*factor."""
    sys.path.insert(0, str(RAIZ / "lab/precio"))
    import viajes_con_plazo as V
    sub = defaultdict(dict)
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            d = dia_de_mercado(x.get("date", e["date"]))
            pid = x["player"]
            p1 = P.en(pid, d - D)
            if not p1:
                continue
            otras = [x["amount"]] + [b["amount"] for b in x.get("bids") or []]
            if x["to"]["id"] == PEPE:
                otras = [b["amount"] for b in x.get("bids") or []]
            if not otras or max(otras) < p1 * factor:
                sub[d][pid] = p1 * factor / 1.01   # semana() paga imp * 1,01
    S = P.primer_dia + 4 * D
    out = []
    while S + V.PLAZO * D <= P.ultimo_dia:
        out.append(V.semana(P, sub, S, caja, tope)[:2])
        S += D
    return out


if __name__ == "__main__":
    print("\n6) E8 rehecho: viajes de una semana ganando SOLO lo que nadie pelea (caja 4 M, tope 2 M):")
    for f in (1.01, 1.03):
        w = semanas_sin_pelea(P, f)
        pls = [x[0] for x in w]
        print(f"   puja precio x {f:.2f}: mediana {med(pls):>+10,.0f}  peor {min(pls):>+10,.0f}"
              f"  mejor {max(pls):>+11,.0f}  en verde {sum(p > 0 for p in pls)}/{len(pls)}"
              f"  viajes/semana {sum(x[1] for x in w)/len(w):.1f}")
