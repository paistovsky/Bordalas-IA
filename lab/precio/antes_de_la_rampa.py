"""
E34: ¿hay en la lista del Computer jugadores que puntuan bien MIENTRAS
estan a la venta? (la idea de E33: pujar por puntos un dia antes de la
rampa)

Solo se adelanta a la rampa (E1) un jugador que esta en la lista del
Computer el dia de su partido: la puja se resuelve en el reset que trae la
primera subida. Se cruza la lista del Computer de un dia (foto del ciclo
de despues del reset) con los puntos del partido de ese dia (foto del
reset siguiente) y su cambio de precio.

Uso:  python3 -I lab/precio/antes_de_la_rampa.py LISTA.json SIGUIENTE.json
"""
import json
import sys

if __name__ == "__main__":
    A, B = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    a = {p["id"]: p for p in A["todaLaLiga"]["players"]}
    b = {p["id"]: p for p in B["todaLaLiga"]["players"]}
    comp = [t for t in A["acquisition"]["targets"] if t["seller_kind"] == "COMPUTER"]
    jugaron = buenos = 0
    for t in comp:
        p, q = b[t["id"]], a[t["id"]]
        jugo = (p["played"] or 0) > (q["played"] or 0)
        pts = p["points"] - q["points"]
        jugaron += jugo
        buenos += jugo and pts >= 5
        if jugo:
            print(f"   {t['name']:<20} {t['market_price']/1e6:5.2f} M  {pts:3d} pts"
                  f"  cambio siguiente {p['price_increment']/p['price']*100:+.1f}%")
    print(f"Lista del Computer: {len(comp)}; jugaron ese dia: {jugaron}; con 5+ puntos: {buenos}")
