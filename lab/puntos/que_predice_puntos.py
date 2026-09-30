"""
Laboratorio, experimento 7: que predice los PUNTOS de la jornada siguiente.

La regla del dueno (29/09): «inversion» son puntos; el dinero es un medio.
Para decidir a quien fichar y a quien vender hay que saber que dato
anticipa los puntos de la proxima jornada. Candidatos:
  - el precio de Biwenger (lo que el mercado cree),
  - los puntos por partido jugado hasta ahora,
  - los puntos totales (lo que usa `nos_suma` de Pepe: total contra total),
  - el estado (ok / injured / doubt...).

Datos (lo unico que hay en git con puntos por jugador):
  - data/fotos/2026-09-18.json: totales tras la J6 (points, played,
    price, status) de 546 jugadores, 18/09 16:16, antes de la J7;
  - data/intelligence/puntos_por_jornada.jsonl: totales tras la J7.
  Puntos de la J7 = diferencia. Una sola jornada fuera de muestra: se dice.

Metricas: correlacion de rangos (Spearman) con los puntos de la J7, y
cuantos puntos de la J7 da el mejor 20 % de cada criterio.

Uso:  python3 lab/puntos/que_predice_puntos.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def rangos(xs):
    orden = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and xs[orden[j + 1]] == xs[orden[i]]:
            j += 1
        for k in range(i, j + 1):
            r[orden[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = rangos(a), rangos(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb)


def cargar():
    foto = {p["id"]: p for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]}
    j7 = json.loads(open(RAIZ / "data/intelligence/puntos_por_jornada.jsonl").readline())["players"]
    filas = []
    for sid, (pts, jug, _precio) in j7.items():
        f = foto.get(int(sid))
        if not f or not f.get("price"):
            continue
        pj = f["played"] or 0
        filas.append(dict(
            id=int(sid), name=f["name"], pos=f["position"], status=f["status"],
            precio=f["price"], total=f["points"] or 0, jugados=pj,
            media=(f["points"] or 0) / pj if pj else 0.0,
            j7=pts - (f["points"] or 0), jugo_j7=(jug or 0) > pj))
    return filas


def informe(filas, titulo):
    y = [r["j7"] for r in filas]
    print(f"\n{titulo}  (n={len(filas)}, puntos medios en la J7: {sum(y)/len(y):.2f})")
    crit = [("precio", lambda r: r["precio"]),
            ("puntos por partido (hasta J6)", lambda r: r["media"]),
            ("puntos totales (hasta J6)", lambda r: r["total"]),
            ("precio x (estado ok)", lambda r: r["precio"] * (r["status"] == "ok"))]
    k = max(len(filas) // 5, 1)
    for nom, f in crit:
        xs = [f(r) for r in filas]
        top = sorted(filas, key=f, reverse=True)[:k]
        print(f"   {nom:<32} Spearman {spearman(xs, y):+.2f}   el mejor 20 % (n={k}) hizo "
              f"{sum(r['j7'] for r in top)/k:5.2f} pts; jugaron {sum(r['jugo_j7'] for r in top)/k:4.0%}")


if __name__ == "__main__":
    filas = cargar()
    informe(filas, "Todos")
    informe([r for r in filas if r["status"] == "ok"], "Solo estado ok el 18/09")
    for pos, nom in ((1, "Porteros"), (2, "Defensas"), (3, "Medios"), (4, "Delanteros")):
        informe([r for r in filas if r["pos"] == pos and r["status"] == "ok"], f"{nom}, estado ok")

    print("\nEstado del 18/09 y puntos en la J7:")
    for st in ("ok", "doubt", "injured", "sanctioned"):
        rs = [r for r in filas if r["status"] == st]
        if rs:
            print(f"   {st:<11} n={len(rs):3d}  jugaron {sum(r['jugo_j7'] for r in rs)/len(rs):4.0%}"
                  f"  puntos medios {sum(r['j7'] for r in rs)/len(rs):5.2f}")

    print("\nCuanto da cada tramo de precio en la J7 (estado ok):")
    tramos = [(0, 1e6), (1e6, 3e6), (3e6, 6e6), (6e6, 10e6), (10e6, 1e9)]
    for a, b in tramos:
        rs = [r for r in filas if a <= r["precio"] < b and r["status"] == "ok"]
        if rs:
            pm = sum(r["j7"] for r in rs) / len(rs)
            eur = sum(r["precio"] for r in rs) / len(rs)
            print(f"   {a/1e6:>4.0f}-{b/1e6 if b < 1e9 else 99:>3.0f} M  n={len(rs):3d}  jugaron "
                  f"{sum(r['jugo_j7'] for r in rs)/len(rs):4.0%}  puntos J7 {pm:5.2f}"
                  f"  media hasta J6 {sum(r['media'] for r in rs)/len(rs):5.2f}/partido"
                  f"  precio medio {eur/1e6:5.2f} M")
