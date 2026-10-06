"""
E22 (agenda 4, aceptar o no ofertas): ¿como son las ofertas del Computer
por nuestros jugadores, y compensa esperar a la siguiente?

En 91 vueltas de produccion hubo 807 lecturas de ofertas del Computer y una
sola de un manager (Luismi por Pablo Duran, 1,31 M; el Computer lo compro
el 30/09 por 1,32 M). Asi que «aceptar o no» es, en la practica, aceptar
la del Computer hoy o esperar a la siguiente.

Datos: las fotos de los ciclos (status.json, carpetas por argumento; los
artefactos caducan a los 2 dias). Una oferta distinta = (jugador, importe).
Para cada una: prima sobre el precio del jugador ese dia, horas que dura,
y la siguiente oferta del mismo jugador: ¿mejor o peor?

Uso:  python3 lab/ofertas/computer.py CARPETA [CARPETA ...]
"""
import glob
import json
import os
import sys
from collections import defaultdict


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


if __name__ == "__main__":
    vistas = defaultdict(list)   # (jugador) -> [(t, importe, prima, horas)]
    for c in sys.argv[1:]:
        for r in sorted(glob.glob(os.path.join(c, "*.json"))):
            if os.path.getsize(r) < 10_000:
                continue
            t = os.path.basename(r)[:16]
            for o in json.load(open(r)).get("offers") or []:
                if o.get("counterparty") != "COMPUTER" or not o.get("players"):
                    continue
                vistas[o["players"][0]].append((t, o["amount"], o.get("premium_percent"), o.get("hours_to_expiry")))
    ofertas = []
    for j, vs in vistas.items():
        vs.sort()
        distintas = []
        for t, imp, pr, h in vs:
            if not distintas or distintas[-1][1] != imp:
                distintas.append((t, imp, pr, h))
        for i, (t, imp, pr, h) in enumerate(distintas):
            sig = distintas[i + 1] if i + 1 < len(distintas) else None
            ofertas.append(dict(jug=j, t=t, imp=imp, prima=pr, horas=h,
                                sig_prima=sig[2] if sig else None, sig_t=sig[0] if sig else None))
    primas = [o["prima"] for o in ofertas if o["prima"] is not None]
    print(f"Jugadores con oferta: {len(vistas)}; ofertas distintas: {len(ofertas)}")
    q = sorted(primas)
    print(f"   prima sobre el precio: p10 {q[len(q)//10]:+.1f}%  mediana {med(q):+.1f}%  p90 {q[9*len(q)//10]:+.1f}%")
    print(f"   horas que le quedan al verla por primera vez (mediana): {med([o['horas'] for o in ofertas if o['horas']]):.0f}")
    pares = [o for o in ofertas if o["sig_prima"] is not None and o["prima"] is not None]
    print(f"\nLa siguiente oferta del mismo jugador (n={len(pares)}):")
    print(f"   mejor {sum(o['sig_prima'] > o['prima'] for o in pares)}, peor {sum(o['sig_prima'] < o['prima'] for o in pares)}, "
          f"igual {sum(o['sig_prima'] == o['prima'] for o in pares)}")
    for nom, f in (("si la de hoy es baja (< 0 %)", lambda o: o["prima"] < 0),
                   ("si la de hoy es normal (0-3 %)", lambda o: 0 <= o["prima"] <= 3),
                   ("si la de hoy es alta (> 3 %)", lambda o: o["prima"] > 3)):
        ps = [o for o in pares if f(o)]
        if ps:
            print(f"   {nom:<32} n={len(ps):3d}  la siguiente: mediana {med([o['sig_prima'] for o in ps]):+.1f}%"
                  f"  (mejora {sum(o['sig_prima'] > o['prima'] for o in ps)}/{len(ps)})")
