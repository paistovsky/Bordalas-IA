"""
E36: si se ganan las pujas vivas, ¿llega Pepe en verde a la J9?

Cuenta sencilla con la foto de un ciclo (status.json): saldo, pujas vivas
(comprometido), lo que la orden piensa vender (con su precio de hoy y la
oferta tipica del Computer, +1 %, E22) y el premio de la J8 (30.000 EUR por
punto, E16). Se dan los escenarios de ganar todas o algunas pujas.

Uso:  python3 -I lab/caja/cuentas_j9.py status.json PUNTOS_J8 [reventa:Nombre=importe ...]
"""
import itertools
import json
import sys

POR_PUNTO = 30_000
OFERTA = 1.01

if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    pts = int(sys.argv[2])
    reventas = dict(a.split(":", 1)[1].split("=") for a in sys.argv[3:] if a.startswith("reventa:"))
    saldo = d["summary"]["balance"]
    orden = d.get("orden") or {}
    pujas = {f["nombre"]: f["puja"] for f in orden.get("fichar", [])}
    pujas.update({k: int(v) for k, v in reventas.items()})
    precio = {p["name"]: p["price"] for p in d["roster"]["players"]}
    ventas = {v["nombre"]: round(precio.get(v["nombre"], 0) * OFERTA) for v in orden.get("vender", [])}
    premio = pts * POR_PUNTO
    print(f"Foto {d['meta']['generated_at']}: saldo {saldo:,}; premio J8 estimado ({pts} pts) {premio:,}")
    print(f"   la orden vende: " + ", ".join(f"{k} ~{v:,}" for k, v in ventas.items()))
    nombres = list(pujas)
    for r in range(len(nombres), -1, -1):
        for gan in itertools.combinations(nombres, r):
            coste = sum(pujas[g] for g in gan)
            vende = sum(v for k, v in ventas.items()
                        if (k == "Jutglà" and "Iván Romero" in gan) or (k == "Diego Rico" and "Gerard Martín" in gan))
            reventa = sum(round(int(reventas[g]) * 1.0) for g in gan if g in reventas)
            final = saldo - coste + premio + vende + reventa
            print(f"   gana {', '.join(gan) or 'ninguna':<45} -> saldo antes de la J9 ~{final:>+12,}")
