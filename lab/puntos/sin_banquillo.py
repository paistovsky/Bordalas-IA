"""
Laboratorio, experimento 12: ¿cuantos puntos cuesta jugar con 11 justos?

El caso (02/10): Pepe sale del rojo con 11 jugadores, sin banquillo. En
esta liga el once se cierra al empezar la jornada (`lineupRoundChanges`:
0 en el tablon), asi que un suplente solo sirve si se sabe ANTES del
primer partido que un titular no va a jugar. Si se sabe y no hay suplente,
esa plaza da 0.

Datos: la foto del 18/09 a las 16:16 (estado de los 546, ~5 h antes del
primer partido de la J7, 21:00) y los totales tras la J7. Se toman los
«fijos»: los que habian jugado 5 o 6 de los 6 partidos hasta la J6 (lo
mas parecido a un titular del once de Pepe).

  - Se sabia antes: el fijo tenia estado injured/doubt/sanctioned a las
    16:16. Un suplente lo habria cubierto.
  - No se sabia: estado ok y no jugo. Ni con banquillo se arregla.
  - Lo que da un suplente barato que juegue (estado ok, < 1 M, 1-3 M).

Uso:  python3 lab/puntos/sin_banquillo.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def cargar():
    foto = {p["id"]: p for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]}
    j7 = json.loads(open(RAIZ / "data/intelligence/puntos_por_jornada.jsonl").readline())["players"]
    out = []
    for sid, (pts, jug, _p) in j7.items():
        f = foto.get(int(sid))
        if not f:
            continue
        out.append(dict(pos=f["position"], status=f["status"], precio=f["price"] or 0,
                        jugados=f["played"] or 0, pts=pts - (f["points"] or 0),
                        jugo=(jug or 0) > (f["played"] or 0),
                        media=(f["points"] or 0) / f["played"] if f["played"] else 0))
    return out


if __name__ == "__main__":
    R = cargar()
    fijos = [r for r in R if r["jugados"] >= 5]
    n = len(fijos)
    sabia = [r for r in fijos if r["status"] != "ok"]
    nosabia = [r for r in fijos if r["status"] == "ok" and not r["jugo"]]
    print(f"Fijos (5-6 de 6 partidos hasta la J6): n={n}")
    print(f"   no jugaron la J7: {sum(not r['jugo'] for r in fijos)} ({sum(not r['jugo'] for r in fijos)/n:.1%})")
    print(f"   SE SABIA antes (estado no ok a las 16:16): {len(sabia)} ({len(sabia)/n:.1%}); "
          f"de ellos no jugaron {sum(not r['jugo'] for r in sabia)}")
    print(f"   no se sabia (ok y no jugaron): {len(nosabia)} ({len(nosabia)/n:.1%})")
    for p, nom in ((1, "POR"), (2, "DEF"), (3, "MED"), (4, "DEL")):
        fs = [r for r in fijos if r["pos"] == p]
        s = [r for r in fs if r["status"] != "ok"]
        print(f"   {nom}: fijos {len(fs):3d}, se sabia {len(s):2d} ({len(s)/len(fs):.1%}), "
              f"no se sabia {sum(r['status']=='ok' and not r['jugo'] for r in fs):2d}")
    print("\nLo que da un SUPLENTE con estado ok en la J7 (puntos medios, incluidos los que no jugaron):")
    for a, b in ((0, 1e6), (1e6, 3e6)):
        for p, nom in ((2, "DEF"), (3, "MED"), (4, "DEL")):
            rs = [r for r in R if r["status"] == "ok" and a <= r["precio"] < b and r["pos"] == p]
            regs = [r for r in rs if r["jugados"] >= 4]
            print(f"   {nom} {a/1e6:.0f}-{b/1e6:.0f} M: todos n={len(rs):3d} {sum(r['pts'] for r in rs)/len(rs):5.2f} pts"
                  f" (jugaron {sum(r['jugo'] for r in rs)/len(rs):4.0%});  los que jugaban (4+ de 6) n={len(regs):3d}"
                  f" {sum(r['pts'] for r in regs)/max(len(regs),1):5.2f} pts (jugaron {sum(r['jugo'] for r in regs)/max(len(regs),1):4.0%})")
    p_sabia = len(sabia) / n
    print(f"\nCuenta para un once de 11 (sin portero suplente, 10 de campo):")
    print(f"   plazas que se saben vacias por jornada: 11 x {p_sabia:.3f} = {11*p_sabia:.2f}")
    for pts in (2.0, 3.0):
        print(f"   x {pts:.1f} pts del suplente = {11*p_sabia*pts:.2f} pts/jornada; en 31 jornadas = {31*11*p_sabia*pts:.0f} pts")
