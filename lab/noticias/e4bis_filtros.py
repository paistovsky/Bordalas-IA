"""
E4-bis (pregunta del gestor, 29/09 14:15): de las noticias de BAJA de
FutbolFantasy, ¿cuantas pasarian HOY los filtros que Pepe ya tiene?

Filtros de hoy, en el orden en que frenan una compra:
  1. estado de Biwenger distinto de «ok» (injured, doubt, sanctioned...)
     -> NO_DISPONIBLE;
  2. la rampa: el ultimo cambio de precio no es una subida -> fuera;
  3. «¿va a jugar?»: titularidad < 40 % (solo se conoce para los
     objetivos del tablero, no para los 547).
Una noticia «se cuela» si en algun ciclo de las 72 h siguientes el jugador
tiene estado ok Y su precio sube (y, si esta en el tablero, titularidad
>= 40 % y sin frenar por disponibilidad).

Datos:
  - lab/noticias/eventos_hasta_29_09.jsonl: los eventos de E4, con el
    archivo ampliado hasta el 29/09 16:24 (27 noticias mas).
  - lab/noticias/ciclos_27_29_09.json: extracto de los 45 ciclos de
    produccion del 27/09 16:10 al 29/09 15:09 UTC (artefactos de Actions,
    que caducan a los 2 dias): estado y ultimo cambio de precio de los 547,
    y titularidad/disponibilidad de los objetivos del tablero.
  - data/fotos/2026-09-18.json: la foto del 18/09 16:16 (un ciclo mas).

Uso:  python3 lab/noticias/e4bis_filtros.py
"""
import datetime as dt
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = RAIZ / "lab/noticias"
H72 = dt.timedelta(hours=72)


def utc(s):
    s = s.replace("+0200", "+02:00").replace("+0100", "+01:00").replace("Z", "+00:00")
    return dt.datetime.fromisoformat(s).astimezone(dt.timezone.utc)


def ciclos():
    out = []
    for t, c in json.load(open(AQUI / "ciclos_27_29_09.json")).items():
        out.append((utc(t), {int(k): v for k, v in c["jugadores"].items()},
                    {int(k): v for k, v in c["objetivos"].items()}))
    f = json.load(open(RAIZ / "data/fotos/2026-09-18.json"))
    pl = {p["id"]: [p["status"], p.get("price_increment")] for p in f["todaLaLiga"]["players"]}
    tg = {}
    for r in f.get("acquisition", {}).get("targets", []) or f.get("preferencia", []):
        tg[r["id"]] = [r.get("starter_probability"), r.get("availability"), r.get("decision"),
                       bool(r.get("absence"))]
    out.append((utc(f["meta"]["generated_at"] + "+02:00"), pl, tg))
    return sorted(out, key=lambda x: x[0])


def veredicto(ev, cs):
    t0 = utc(ev["publicada"])
    ventana = [c for c in cs if t0 < c[0] <= t0 + H72]
    if not ventana:
        return None
    estados, cuela, frenos = [], False, set()
    for _, pl, tg in ventana:
        st, inc = pl.get(ev["pid"], [None, None])
        estados.append(st)
        if st is None:
            frenos.add("no esta en el juego")
            continue
        if st != "ok":
            frenos.add(f"estado {st}")
            continue
        if not inc or inc <= 0:
            frenos.add("la rampa (no sube)")
            continue
        o = tg.get(ev["pid"])
        if o:
            sp, av = o[0], o[1]
            if av and av != "DISPONIBLE":
                frenos.add(f"disponibilidad {av}")
                continue
            if sp is not None and sp < 40:
                frenos.add("titularidad < 40")
                continue
        cuela = True
    return dict(n_ciclos=len(ventana), primer_estado=estados[0], cuela=cuela, frenos=sorted(frenos))


if __name__ == "__main__":
    cs = ciclos()
    ini, fin = cs[0][0], cs[-1][0]
    evs = [json.loads(l) for l in open(AQUI / "eventos_hasta_29_09.jsonl")]
    bajas = [e for e in evs if e["tipo"] == "BAJA"]
    # un episodio por jugador y ventana: la primera BAJA en 72 h
    vistos, filas = {}, []
    for e in sorted(bajas, key=lambda e: e["publicada"]):
        t = utc(e["publicada"])
        if e["pid"] in vistos and t - vistos[e["pid"]] < H72:
            continue
        vistos[e["pid"]] = t
        v = veredicto(e, cs)
        if v:
            filas.append((e, v))
    print(f"Ciclos con foto: {len(cs)} (18/09 y {ini:%d/%m %H:%M} a {fin:%d/%m %H:%M} UTC).")
    print(f"Episodios de BAJA con algun ciclo en sus 72 h: {len(filas)}\n")
    for e, v in filas:
        print(f"  {e['publicada'][:16]}  {e['name']:<18} 1er estado {str(v['primer_estado']):<10}"
              f" {'SE CUELA' if v['cuela'] else 'frenado  '}  {', '.join(v['frenos'])}"
              f"   | {e['titulo'][:60]}")
    n = len(filas)
    cuelan = [f for f in filas if f[1]["cuela"]]
    ya = sum(1 for _, v in filas if v["primer_estado"] not in ("ok", None))
    print(f"\n  Biwenger ya lo marca (no ok) en el primer ciclo tras la noticia: {ya}/{n}")
    print(f"  Se cuelan (estado ok y precio subiendo en algun ciclo de las 72 h): {len(cuelan)}/{n}")
    for e, v in cuelan:
        print(f"    -> {e['name']} ({e['publicada'][:10]}): {e['titulo'][:70]}")
