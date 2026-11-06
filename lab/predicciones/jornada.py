"""
E86: predicciones con fecha, jornada a jornada. Apunta, ANTES de la
jornada, los puntos que deberia sacar el mejor once de cada manager con la
vara de E20 (pts/partido x FF) y, con el factor de nivel de E79, y despues
los juzga contra el «roundFinished» del tablon.

Uso:  python3 -I lab/predicciones/jornada.py --apuntar N status.json
      python3 lab/predicciones/jornada.py --juzgar N
Guarda en lab/predicciones/jN.json.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/carrera"))
from proyeccion import TIT_SIN_DATO, mejor_once  # noqa: E402

TABLON = RAIZ / "data/rival_intelligence/board_events.json"


def factor(t):  # E79: nivel por tramo de FF (J10 y J11)
    return 0.2 if t < 30 else 0.7 if t < 50 else 0.85 if t < 60 else 1.1


if __name__ == "__main__":
    modo, N = sys.argv[1], int(sys.argv[2])
    destino = Path(__file__).resolve().parent / f"j{N}.json"
    if modo == "--apuntar":
        f = json.load(open(sys.argv[3]))
        cat = {p["id"]: p for p in f["todaLaLiga"]["players"]}
        pred = {}
        for m in f["rival_squads"]["managers"]:
            jugs = []
            for p in m["players"]:
                c = cat.get(p["id"], {})
                pj = c.get("played") or 0
                media = (c.get("points") or 0) / pj if pj else 0.0
                tit = p.get("starter_probability")
                t = tit if tit is not None else TIT_SIN_DATO
                jugs.append(dict(name=p["name"], position=p["position"], status=p.get("status") or c.get("status"),
                                 esp=media * t / 100, cal=media * factor(t)))
            mo = mejor_once(jugs)
            pred[m["name"]] = dict(vara=round(mo[0], 2) if mo else 0,
                                   calibrada=round(sum(j["cal"] for j in mo[2]), 2) if mo else 0)
        json.dump(dict(jornada=N, foto=f["meta"]["generated_at"], pred=pred), open(destino, "w"), ensure_ascii=False, indent=1)
        for n, v in sorted(pred.items(), key=lambda kv: -kv[1]["vara"]):
            print(f"   {n[:16]:16} vara {v['vara']:5.1f}   calibrada {v['calibrada']:5.1f}")
        print(f"\nApuntado en {destino.name}")
    else:
        d = json.load(open(destino))
        real = None
        for e in json.load(open(TABLON)):
            if e["type"] == "roundFinished" and e["content"]["round"]["name"] == f"Jornada {N}":
                real = {x["user"]["name"]: x["points"] for x in e["content"]["results"]}
        if real is None:
            sys.exit(f"La J{N} aun no esta pagada en el tablon.")
        print(f"J{N}, apuntado con la foto {d['foto']}")
        ev = []
        for n, v in d["pred"].items():
            r = real.get(n)
            if r is None:
                continue
            ev.append((n, v["vara"], v["calibrada"], r))
            print(f"   {n[:16]:16} vara {v['vara']:5.1f}  calibrada {v['calibrada']:5.1f}  real {r:>3}")
        for i, nombre in ((1, "vara"), (2, "calibrada")):
            err = sum(abs(e[i] - e[3]) for e in ev) / len(ev)
            print(f"   error medio {nombre}: {err:.1f} pts; suma pred / suma real: {sum(e[i] for e in ev)/sum(e[3] for e in ev):.0%}")
