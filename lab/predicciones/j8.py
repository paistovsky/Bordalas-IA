"""
E23: predicciones del laboratorio para la J8, APUNTADAS ANTES de jugarla.

Una vara que no se juzga fuera de muestra no vale (regla 2). La J8 se
juega a partir del 09/10 a las 21:00. Hoy (07/10) se apuntan:
  - para cada manager, los puntos esperados de su mejor once (E20);
  - para cada jugador de Pepe, sus puntos esperados (E16: puntos por
    partido x titularidad FF) y si FF le da menos del 70 % (E17: juega
    9 de cada 10 con 70 % o mas);
  - el orden de los 8 managers en la J8.
Se guardan en `lab/predicciones/j8.json` y se juzgan cuando cierre la J8
con `--juzgar` (necesita la linea de la J8 en
`data/intelligence/puntos_por_jornada.jsonl` y su `roundFinished` en el
tablon).

Uso:  python3 lab/predicciones/j8.py --apuntar status.json
      python3 lab/predicciones/j8.py --juzgar
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/carrera"))
SALIDA = Path(__file__).parent / "j8.json"
PEPE = "Pepe Bordalás"


def apuntar(ruta):
    from proyeccion import TIT_SIN_DATO, mejor_once
    f = json.load(open(ruta))
    cat = {p["id"]: p for p in f["todaLaLiga"]["players"]}
    out = {"apuntado": f["meta"]["generated_at"], "jornada": 8, "managers": {}, "pepe": []}
    for m in f["rival_squads"]["managers"]:
        jugs = []
        for p in m["players"]:
            c = cat.get(p["id"], {})
            pj = c.get("played") or 0
            media = (c.get("points") or 0) / pj if pj else 0.0
            tit = p.get("starter_probability")
            jugs.append(dict(id=p["id"], name=p["name"], position=p["position"],
                             status=p.get("status") or c.get("status"), tit=tit,
                             total=c.get("points") or 0,
                             esp=media * (tit if tit is not None else TIT_SIN_DATO) / 100))
        mo = mejor_once(jugs)
        out["managers"][m["name"]] = {"once_esperado": round(mo[0], 2) if mo else None,
                                      "formacion": mo[1] if mo else None,
                                      "once": [j["id"] for j in mo[2]] if mo else []}
        if m["name"] == PEPE:
            out["pepe"] = [{k: j[k] for k in ("id", "name", "position", "status", "tit", "total")}
                           | {"esp": round(j["esp"], 2), "riesgo_titularidad": (j["tit"] or 0) < 70}
                           for j in jugs]
    out["orden_esperado"] = [n for n, _ in sorted(out["managers"].items(),
                                                   key=lambda x: -(x[1]["once_esperado"] or 0))]
    json.dump(out, open(SALIDA, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out["orden_esperado"], ensure_ascii=False))
    for n, v in out["managers"].items():
        print(f"   {n[:16]:<16} {v['once_esperado']}  {v['formacion']}")
    print("   Pepe:", [(j["name"], j["esp"], j["tit"]) for j in out["pepe"]])


def juzgar():
    pr = json.load(open(SALIDA))
    lineas = [json.loads(l) for l in open(RAIZ / "data/intelligence/puntos_por_jornada.jsonl")]
    j8 = next((l for l in lineas if l.get("jornada") == 8), None)
    j7 = next((l for l in lineas if l.get("jornada") == 7), None)
    reales = {}
    vistos = set()
    for e in json.load(open(RAIZ / "data/rival_intelligence/board_events.json")):
        if e["type"] == "roundFinished" and e["content"]["round"]["name"].startswith("Jornada 8") \
                and e["event_id"] not in vistos:
            vistos.add(e["event_id"])
            for x in e["content"]["results"]:
                reales[x["user"]["name"]] = x["points"]
    if not j8 or not reales:
        print("La J8 aun no esta cerrada en los libros (puntos_por_jornada / roundFinished).")
        return
    print("Managers: esperado contra real en la J8")
    for n, v in sorted(pr["managers"].items(), key=lambda x: -(reales.get(x[0]) or 0)):
        print(f"   {n[:16]:<16} esperado {v['once_esperado']}  real {reales.get(n)}")
    orden_real = [n for n, _ in sorted(reales.items(), key=lambda x: -x[1])]
    print("   orden esperado:", pr["orden_esperado"])
    print("   orden real:    ", orden_real)
    print("\nJugadores de Pepe (puntos de la J8 = total J8 - total J7):")
    for j in pr["pepe"]:
        a, b = j8["players"].get(str(j["id"])), j7["players"].get(str(j["id"]))
        pts = (a[0] - b[0]) if a and b else None
        jugo = (a[1] > b[1]) if a and b else None
        print(f"   {j['name']:<18} esperado {j['esp']:5.2f}  tit {j['tit']}  real {pts}  jugo {jugo}"
              f"{'  (riesgo <70 %)' if j['riesgo_titularidad'] else ''}")


if __name__ == "__main__":
    if sys.argv[1] == "--apuntar":
        apuntar(sys.argv[2])
    else:
        juzgar()
