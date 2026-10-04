"""
E17: ¿«puntos por partido x titularidad» (la vara de E16) anticipa los
puntos de la jornada mejor que el total de puntos (la de E7)?

Datos: los jugadores con titularidad de FutbolFantasy en la foto del 18/09
(antes de la J7; tablero, plantillas de rivales, etc.: 140 con dato) y sus
puntos en la J7 (totales del 23/09 menos los del 18/09).
Se compara la correlacion de rangos con los puntos de la J7 y lo que hizo
el mejor tercio de cada vara.

Uso:  python3 lab/puntos/valida_esperado.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from que_predice_puntos import spearman  # noqa: E402


def titularidades(foto):
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("id"), int) and o.get("starter_probability") is not None:
                out.setdefault(o["id"], o["starter_probability"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(foto)
    return out


if __name__ == "__main__":
    foto = json.load(open(RAIZ / "data/fotos/2026-09-18.json"))
    tit = titularidades(foto)
    cat = {p["id"]: p for p in foto["todaLaLiga"]["players"]}
    j7 = json.loads(open(RAIZ / "data/intelligence/puntos_por_jornada.jsonl").readline())["players"]
    filas = []
    for pid, t in tit.items():
        p = cat.get(pid)
        a = j7.get(str(pid))
        if not p or not a:
            continue
        pj = p["played"] or 0
        media = (p["points"] or 0) / pj if pj else 0.0
        filas.append(dict(pos=p["position"], st=p["status"], tit=t, total=p["points"] or 0, media=media,
                          esperado=media * t / 100, precio=p["price"] or 0,
                          j7=a[0] - (p["points"] or 0), jugo=(a[1] or 0) > pj))
    y = [r["j7"] for r in filas]
    print(f"Jugadores con titularidad FF el 18/09 y puntos de la J7: n={len(filas)} "
          f"(media J7 {sum(y)/len(y):.2f}; jugaron {sum(r['jugo'] for r in filas)/len(filas):.0%})\n")
    k = len(filas) // 3
    for nom in ("esperado", "total", "media", "tit", "precio"):
        xs = [r[nom] for r in filas]
        top = sorted(filas, key=lambda r: r[nom], reverse=True)[:k]
        print(f"   {nom:<9} Spearman {spearman(xs, y):+.2f}   el mejor tercio (n={k}) hizo "
              f"{sum(r['j7'] for r in top)/k:5.2f} pts; jugaron {sum(r['jugo'] for r in top)/k:4.0%}")
    print("\n   Por tramo de titularidad FF:")
    for a, b in ((0, 40), (40, 70), (70, 90), (90, 101)):
        rs = [r for r in filas if a <= r["tit"] < b]
        if rs:
            print(f"   {a:>3}-{b-1 if b < 101 else 100:<3}%  n={len(rs):3d}  jugaron {sum(r['jugo'] for r in rs)/len(rs):4.0%}"
                  f"  puntos J7 {sum(r['j7'] for r in rs)/len(rs):5.2f}")
