"""
E58: ¿cuanto juega de verdad un jugador segun la titularidad de FF del dia
antes? (Hoy Jonny y Sergi Cardona van al 50 % en el once de la J10 y no
hay banquillo.) E7 midio que >= 70 % juega 9 de cada 10; aqui la curva
entera.

Datos: libro_del_escaparate.jsonl (los 20 del Computer cada dia, con
starter_probability de FF) del dia anterior al inicio de la J8 (09/10) y
de la J9 (16/10); y si jugaron, con las fotos de puntos_por_jornada
(partidos tras J7 -> tras J8 -> tras J9). Fuera Athletic y Rayo en la J8.

Uso:  python3 lab/puntos/titularidad_calibrada.py
"""
import json
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESC = RAIZ / "data/trading/libro_del_escaparate.jsonl"
LIBRO = RAIZ / "data/intelligence/puntos_por_jornada.jsonl"
FOTO = RAIZ / "data/fotos/2026-09-18.json"

# jornada -> (dias de escaparate que valen como «la vispera», foto antes, foto despues)
JORNADAS = {8: (("2026-10-08", "2026-10-09"), 7, 8), 9: (("2026-10-15", "2026-10-16"), 8, 9)}

if __name__ == "__main__":
    L = {json.loads(l)["jornada"]: json.loads(l)["players"] for l in open(LIBRO)}
    equipo = {str(p["id"]): p["team_id"] for p in json.load(open(FOTO))["todaLaLiga"]["players"]}
    esc = defaultdict(dict)
    for l in open(ESC):
        r = json.loads(l)
        for p in r["players"]:
            esc[r["dia_de_mercado"]][str(p["id"])] = p.get("starter_probability")
    casos = {}
    for j, (dias, a, b) in JORNADAS.items():
        for dia in dias:
            for pid, prob in esc.get(dia, {}).items():
                if prob is None or pid not in L[a] or pid not in L[b]:
                    continue
                if j == 8 and equipo.get(pid) in (1, 70):
                    continue
                casos[(j, pid)] = (prob, L[b][pid][1] - L[a][pid][1] >= 1)
    print(f"Casos jugador-jornada: {len(casos)}\n")
    print("   FF la vispera     n    jugo")
    for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 101)):
        g = [jugo for prob, jugo in casos.values() if lo <= prob < hi]
        if g:
            print(f"   {lo:>3}-{min(hi, 100):<3} %       {len(g):>3}   {sum(g)/len(g):4.0%}")

    # Segunda fuente (desde el 20/10): la titularidad de FF de toda la liga cada
    # dia. Cuando exista la foto de la J10 en puntos_por_jornada, la curva sale
    # con ~500 jugadores: vispera = la ultima linea antes del primer partido.
    TIT = RAIZ / "data/intelligence/la_titularidad_del_dia.jsonl"
    if TIT.exists() and 10 in L:
        vispera = [json.loads(l) for l in open(TIT) if json.loads(l)["dia"] <= "2026-10-23"][-1]
        # fuera los equipos sin nadie con un partido mas (partido fuera de la foto o aplazado)
        jugaron = defaultdict(int)
        for pid in L[10]:
            if pid in L[9] and L[10][pid][1] > L[9][pid][1]:
                jugaron[equipo.get(pid)] += 1
        casos10 = [(v[0], L[10][pid][1] - L[9][pid][1] >= 1) for pid, v in vispera["ff"].items()
                   if v and v[0] is not None and pid in L[9] and pid in L[10] and jugaron.get(equipo.get(pid))]
        print(f"\nJ10 (FF del {vispera['dia']}): {len(casos10)} casos")
        for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 101)):
            g = [j for p, j in casos10 if lo <= p < hi]
            if g:
                print(f"   {lo:>3}-{min(hi, 100):<3} %       {len(g):>3}   {sum(g)/len(g):4.0%}")
    else:
        print("\n(J10: falta su foto en puntos_por_jornada; volver a correr tras la J10)")

    # La vara de Pepe: xP = puntos por partido (hasta la J9) x FF / 100. ¿Cuadra
    # por tramos con lo que hicieron en la J10?
    if TIT.exists() and 10 in L:
        print("\nLa vara (pts/partido x FF) contra los puntos de la J10, por tramo de FF:")
        print("   FF          n    xP medio   puntos medios   puntos / (pts/partido)")
        for lo, hi in ((0, 30), (30, 50), (50, 60), (60, 80), (80, 101)):
            xs = []
            for pid, v in vispera["ff"].items():
                if not v or v[0] is None or pid not in L[9] or pid not in L[10] or not jugaron.get(equipo.get(pid)):
                    continue
                if not (lo <= v[0] < hi):
                    continue
                pts9, pj9, _ = L[9][pid]
                if pj9 < 3:
                    continue
                ppp = pts9 / pj9
                xs.append((ppp * v[0] / 100, L[10][pid][0] - pts9, ppp))
            if xs:
                xp = sum(x[0] for x in xs) / len(xs)
                real = sum(x[1] for x in xs) / len(xs)
                frac = sum(x[1] for x in xs) / max(1e-9, sum(x[2] for x in xs))
                print(f"   {lo:>3}-{min(hi,100):<3}%  {len(xs):>4}    {xp:5.2f}        {real:5.2f}          {frac:4.0%}")
