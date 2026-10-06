"""
E21: ¿cuantas vueltas de Pepe faltan, y a que horas?

Pepe corre cada hora, disparado por cron-job.org (workflow_dispatch). El
gestor vio (28/09 y 06/10) que se saltaban las vueltas de las 05:07 y
06:07 de Madrid y habia dos casi seguidas a las 04:45 y 04:50. Esas horas
son la ventana del reset (las pujas se resuelven a las 07:00): la subasta,
la revision de pujas y los chollos solo actuan en los ultimos 135 min.

Datos: el historial de ejecuciones de bordalas-live.yml (API de GitHub,
volcado a un fichero con `gh api ... --jq` por el que lo corre; ver abajo).
Por cada dia y hora de Madrid: ¿hubo alguna vuelta?

Uso:
  for p in 1 2 3 4 5 6 7 8; do gh api "repos/paistovsky/Bordalas-IA/actions/workflows/bordalas-live.yml/runs?per_page=100&page=$p" \
     --jq '.workflow_runs[] | [.run_number,.created_at,.event,.conclusion] | @tsv'; done > runs.tsv
  python3 lab/infra/latido.py runs.tsv 2026-09-10 2026-10-05
"""
import datetime as dt
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")

if __name__ == "__main__":
    ruta, desde, hasta = sys.argv[1], dt.date.fromisoformat(sys.argv[2]), dt.date.fromisoformat(sys.argv[3])
    vueltas = defaultdict(list)   # dia -> [(hora, minuto, evento, resultado)]
    for linea in open(ruta):
        n, t, ev, res = linea.rstrip("\n").split("\t")
        m = dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(MADRID)
        if desde <= m.date() <= hasta:
            vueltas[m.date()].append((m.hour, m.minute, ev, res))
    dias = sorted(d for d in vueltas)
    print(f"Dias: {len(dias)} ({dias[0]} a {dias[-1]}), vueltas: {sum(len(v) for v in vueltas.values())}")
    print(f"   rojas: {sum(1 for v in vueltas.values() for x in v if x[3] not in ('success', ''))}")
    print("\nHora de Madrid: dias SIN ninguna vuelta en esa hora")
    for h in range(24):
        falta = [d for d in dias if not any(x[0] == h for x in vueltas[d])]
        dobles = sum(1 for d in dias if sum(1 for x in vueltas[d] if x[0] == h) >= 2)
        marca = "  <- ventana del reset" if 4 <= h <= 6 else ""
        print(f"   {h:02d}h  faltan {len(falta):2d}/{len(dias)}   con 2+ vueltas {dobles:2d}{marca}")
    print("\nLa ventana del reset (04:45-07:00): vueltas por dia")
    for d in dias:
        v = sorted((x[0], x[1]) for x in vueltas[d] if (x[0], x[1]) >= (4, 45) and x[0] < 7)
        print(f"   {d}  {len(v)}  " + " ".join(f"{h:02d}:{m:02d}" for h, m in v))


def contra_lo_declarado(ruta, desde, hasta):
    """Cada disparo de config/disparos.json, ¿llego a su hora (+-12 min)?"""
    import json
    from pathlib import Path
    cfg = json.load(open(Path(__file__).resolve().parents[2] / "config/disparos.json"))
    gracia = cfg["gracia_minutos"]
    esperados = [(h, cfg["latido"]["minuto"], "latido") for h in cfg["latido"]["horas"]]
    esperados += [(int(p["madrid"][:2]), int(p["madrid"][3:]), p["que"]) for p in cfg["puntuales"]]
    runs = defaultdict(list)
    for linea in open(ruta):
        n, t, ev, res = linea.rstrip("\n").split("\t")
        m = dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(MADRID)
        if desde <= m.date() <= hasta:
            runs[m.date()].append((m.hour * 60 + m.minute, ev, res))
    dias = sorted(runs)
    falta = defaultdict(int)
    fuera = 0
    for d in dias:
        usados = set()
        for h, mi, que in esperados:
            obj = h * 60 + mi
            ok = [i for i, r in enumerate(runs[d]) if abs(r[0] - obj) <= gracia]
            if ok:
                usados.update(ok)
            else:
                falta[que] += 1
        fuera += sum(1 for i in range(len(runs[d])) if i not in usados)
    tot = len(dias) * len(esperados)
    print(f"\nContra config/disparos.json ({len(esperados)} disparos al dia, gracia {gracia} min, {len(dias)} dias):")
    print(f"   esperados {tot}, no llegaron {sum(falta.values())} ({sum(falta.values())/tot:.1%}):"
          f" latido {falta['latido']}/{20*len(dias)}, ventana {falta['ventana']}/{2*len(dias)},"
          f" tras el reset {falta['tras_el_reset']}/{len(dias)}")
    print(f"   vueltas fuera de lo declarado (a mano, reintentos, dobles): {fuera}")


if __name__ == "__main__":
    contra_lo_declarado(ruta, desde, hasta)
