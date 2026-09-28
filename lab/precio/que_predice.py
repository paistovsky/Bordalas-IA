"""
Laboratorio, experimento 2: que predice que un jugador EMPIECE a subir.

E1 midio que un precio que sube sigue subiendo (92 %). Eso sirve para
subirse a una racha ya empezada. Aqui se busca lo que viene ANTES: que
hace que un jugador quieto o bajando arranque a subir.

Dos mediciones, solo con datos de data/ en git:

A) CUANDO arrancan las rachas (42 dias de precios, 626 jugadores):
   cuantos jugadores parados/bajando empiezan a subir cada dia, contado
   en dias desde el ultimo final de jornada del tablon.

B) QUIEN arranca tras la jornada 7 (un corte, n ~540):
   puntos de la J7 = totales del 23/09 (puntos_por_jornada.jsonl)
   menos totales del 18/09 (foto). Se mira que les paso a los precios del
   22/09 al 28/09 a los que NO venian subiendo. Validacion: se parte a los
   jugadores en dos mitades al azar (semilla fija); el umbral se elige en
   una y se mide en la otra.

Uso:  python3 lab/precio/que_predice.py
"""
import datetime as dt
import json
import random
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import TABLON, Precios, dia_de_mercado, pct  # noqa: E402

D = dt.timedelta(days=1)


def estado(precios, pid, dia):
    """+1 subio en el cambio de `dia`, -1 bajo, 0 quieto, None sin dato."""
    a, b = precios.en(pid, dia), precios.en(pid, dia - D)
    if a is None or b is None:
        return None
    return (a > b) - (a < b)


def medicion_a(P):
    finales = sorted({dia_de_mercado(e["date"]) for e in json.load(open(TABLON))
                      if e["type"] == "roundFinished"})
    arranques = defaultdict(lambda: [0, 0])  # dias desde final -> [arrancan, candidatos]
    d = P.primer_dia + 2 * D
    while d <= P.ultimo_dia:
        prev = [f for f in finales if f <= d]
        if prev:
            k = min((d - prev[-1]).days, 6)
            for pid in P.por_jugador:
                ayer = estado(P, pid, d - D)
                hoy = estado(P, pid, d)
                if ayer is None or hoy is None or ayer == 1:
                    continue
                arranques[k][1] += 1
                arranques[k][0] += hoy == 1
        d += D
    print("A) Cuando arrancan: jugadores quietos o bajando que empiezan a subir,")
    print("   por dias desde el final de la jornada (el cambio de precio de las 07:00):")
    for k in sorted(arranques):
        a, n = arranques[k]
        print(f"   {k}{'+' if k == 6 else ' '} dias   n={n:6d}   arrancan {a:4d}  ({a/n:5.1%})")
    return finales


def medicion_b(P):
    foto = {p["id"]: p for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]}
    j7 = json.loads(open(RAIZ / "data/intelligence/puntos_por_jornada.jsonl").readline())["players"]
    antes = dt.date(2026, 9, 21)          # ultimo cambio antes de que acabara la J7
    fin = min(dt.date(2026, 9, 28), P.ultimo_dia)
    filas = []
    for sid, (pts, jug, _precio) in j7.items():
        pid = int(sid)
        f = foto.get(pid)
        p0, p1 = P.en(pid, antes), P.en(pid, fin)
        if not f or p0 is None or p1 is None:
            continue
        pts_j7 = pts - (f["points"] or 0)
        jugo_j7 = (jug or 0) - (f["played"] or 0)
        e = estado(P, pid, antes)
        filas.append(dict(pid=pid, pts=pts_j7, jugo=jugo_j7 > 0, venia=e,
                          mov=p1 / p0 - 1, arranca=(estado(P, pid, antes + D) == 1
                                                    or estado(P, pid, antes + 2 * D) == 1),
                          precio=p0, media=(f["points"] or 0) / max(f["played"] or 1, 1)))
    print(f"\nB) Tras la J7: {len(filas)} jugadores con puntos y precio. Precio del {antes} al {fin}.")
    quietos = [r for r in filas if r["venia"] != 1]
    print(f"   Los que NO venian subiendo el {antes}: n={len(quietos)}")
    tramos = [("no jugo la J7", lambda r: not r["jugo"]),
              ("jugo, < 2 puntos", lambda r: r["jugo"] and r["pts"] < 2),
              ("jugo, 2-5 puntos", lambda r: r["jugo"] and 2 <= r["pts"] < 6),
              ("jugo, 6-9 puntos", lambda r: r["jugo"] and 6 <= r["pts"] < 10),
              ("jugo, 10+ puntos", lambda r: r["jugo"] and r["pts"] >= 10)]
    for nom, fil in tramos:
        rs = [r for r in quietos if fil(r)]
        if not rs:
            continue
        movs = sorted(r["mov"] for r in rs)
        print(f"   {nom:<18} n={len(rs):3d}  arrancan en 2 dias {sum(r['arranca'] for r in rs):3d}"
              f" ({sum(r['arranca'] for r in rs)/len(rs):5.1%})   precio en la semana:"
              f" mediana {movs[len(movs)//2]*100:+5.1f}%  media {sum(movs)/len(movs)*100:+5.1f}%")
    ven = [r for r in filas if r["venia"] == 1]
    if ven:
        m = sorted(r["mov"] for r in ven)
        print(f"   (los que YA venian subiendo, n={len(ven)}: mediana {m[len(m)//2]*100:+5.1f}%,"
              f" media {sum(m)/len(m)*100:+5.1f}%)")

    # validacion: umbral de puntos elegido en una mitad, medido en la otra
    random.seed(7)
    idx = list(range(len(quietos)))
    random.shuffle(idx)
    a = [quietos[i] for i in idx[: len(idx) // 2]]
    b = [quietos[i] for i in idx[len(idx) // 2:]]

    def tasa(rs):
        return sum(r["arranca"] for r in rs) / len(rs) if rs else 0

    def mejor_umbral(rs):
        base = tasa(rs)
        mejor = None
        for u in range(2, 16):
            sel = [r for r in rs if r["jugo"] and r["pts"] >= u]
            if len(sel) >= 10:
                s = tasa(sel) - base
                if mejor is None or s > mejor[0]:
                    mejor = (s, u)
        return mejor[1]

    print("\n   Validacion (mitades al azar, semilla 7):")
    for nom, tr, te in (("elige en A, mide en B", a, b), ("elige en B, mide en A", b, a)):
        u = mejor_umbral(tr)
        sel = [r for r in te if r["jugo"] and r["pts"] >= u]
        resto = [r for r in te if not (r["jugo"] and r["pts"] >= u)]
        print(f"   {nom}: umbral {u} puntos -> fuera de muestra: n={len(sel)} arrancan {tasa(sel):5.1%}"
              f"  contra el resto n={len(resto)} {tasa(resto):5.1%}")
    return filas



def medicion_c(finales):
    """Que dia compra cada uno, contado desde el final de la jornada."""
    from viajes import viajes
    compras, _ = viajes()
    print("\nC) Que dia compra cada uno (dias desde el final de la jornada; compras al Computer):")
    for m in ("Pollo17", "Luismi_Haz", "Pepe"):
        c = defaultdict(int)
        for x in compras:
            if x["manager"] != m:
                continue
            d = dt.date.fromisoformat(x["dia"])
            prev = [f for f in finales if f <= d]
            if prev:
                c[min((d - prev[-1]).days, 6)] += 1
        n = sum(c.values())
        print(f"   {m:<11} n={n:3d}  " + "  ".join(f"{k}{'+' if k == 6 else ''}d:{c[k]/n:4.0%}" for k in range(7)))



if __name__ == "__main__":
    P = Precios()
    print(f"Precios del {P.primer_dia} al {P.ultimo_dia}, {len(P.por_jugador)} jugadores.\n")
    finales = medicion_a(P)
    medicion_b(P)
    medicion_c(finales)
