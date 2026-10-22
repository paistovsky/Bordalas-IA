"""
E56: como paga Biwenger la «parte 3» de una jornada partida. Compara, para
cada manager, la ronda 5125 (J6 aplazada, parte 2, cobrada el 18/09) con la
5176 (parte 3, el Levante-Athletic del 21/10, cobrada el 22/10): puntos,
premio listado y la diferencia; y el saldo real de Pepe antes y despues
(bitacora del saldo).

Uso:  python3 lab/carrera/partes_de_una_jornada.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
BITACORA = RAIZ / "data/solvency/bitacora_del_saldo.jsonl"

if __name__ == "__main__":
    rondas = {}
    for e in json.load(open(TABLON)):
        if e["type"] == "roundFinished" and e["content"]["round"]["id"] in (5125, 5176):
            rondas[e["content"]["round"]["id"]] = (e["date"], {x["user"]["name"]: (x["points"], x.get("bonus"))
                                                             for x in e["content"]["results"]})
    (_, a), (t, b) = rondas[5125], rondas[5176]
    print(f"   {'manager':<16} {'parte 2':>14} {'parte 3':>14}   diferencia")
    for n in b:
        pa, ba = a.get(n, (0, 0))
        pb, bb = b[n]
        dif = f"{pb - pa:+3d} pts, {((bb or 0) - (ba or 0)):+,} EUR" if bb is not None else "sin premio (rojo en la parte 2)"
        print(f"   {n[:16]:<16} {pa:>3} {str(ba):>10} {pb:>3} {str(bb):>10}   {dif}")
    antes = despues = None
    for l in open(BITACORA):
        r = json.loads(l)
        if r["at"] < "2026-10-22T15:03":
            antes = r["balance"]
        elif despues is None:
            despues = r["balance"]
    print(f"\nSaldo de Pepe antes {antes:,} y despues {despues:,}: {despues - antes:+,} EUR")
