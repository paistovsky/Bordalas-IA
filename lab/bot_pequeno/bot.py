"""
El bot pequeno (agenda 5): Pepe con SOLO las reglas que el laboratorio ha
medido. Prototipo: lee la foto de una vuelta (dashboard/data/status.json de
cada ciclo) y devuelve lo que haria. No escribe en ningun sitio.

Las reglas, y de donde sale cada una:
  CAJA      no se puja con dinero que no hay: presupuesto = saldo - pujas
            vivas (sin deuda). El dinero solo cuenta por los puntos que
            compra (regla del dueno, 29/09).
  REVENTA   E1 + E9: del mercado del Computer, solo lo que SUBIO en el
            ultimo cambio, estado ok, disponible y con titularidad >= 40 %.
            Puja = max(lo que pide, precio * 1,01): no se pelea con Pollo17.
  VENTA     E3 + E5: lo comprado para revender se vende al Computer el
            primer dia que su precio BAJA. E14: un fichaje del once no se
            vende antes de jugar con nosotros. Yamal nunca.
  ONCE      E7: los 11 de mas puntos totales con estado ok, en la mejor
            formacion de Biwenger (todas llevan 3+ defensas).
  BANQUILLO E12: con 11 justos, el primer fichaje para el once es un
            defensa de 1-3 M que juegue.

Uso:  python3 lab/bot_pequeno/bot.py foto.json [foto2.json ...]
"""
import json
import sys

FORMACIONES = {"3-4-3": (3, 4, 3), "3-5-2": (3, 5, 2), "4-4-2": (4, 4, 2), "4-3-3": (4, 3, 3),
               "4-5-1": (4, 5, 1), "5-4-1": (5, 4, 1), "5-3-2": (5, 3, 2)}
TITULAR_MINIMO = 40.0
NUNCA_SE_VENDE = {"Yamal"}


def presupuesto(f):
    s = f.get("summary", {})
    comprometido = (f.get("pujas_del_dueno") or {}).get("committed") or 0
    return max(0, (s.get("balance") or 0) - comprometido)


def reventa(f):
    caja = presupuesto(f)
    cands = []
    for t in (f.get("acquisition") or {}).get("targets") or []:
        if t.get("seller_kind") != "COMPUTER":
            continue
        if (t.get("price_increment") or 0) <= 0:
            continue
        if t.get("status") != "ok" or t.get("availability") not in (None, "DISPONIBLE"):
            continue
        if (t.get("starter_probability") or 0) < TITULAR_MINIMO:
            continue
        precio = t.get("market_price") or 0
        puja = max(t.get("asking_price") or 0, round(precio * 1.01))
        cands.append((t["price_increment"] / max(precio, 1), t["name"], puja))
    pujas = []
    for _, nombre, puja in sorted(cands, reverse=True):
        if puja <= caja:
            pujas.append((nombre, puja))
            caja -= puja
    return pujas, cands


def once(jugadores):
    por = {1: [], 2: [], 3: [], 4: []}
    for p in jugadores:
        if p.get("status") == "ok":
            por[p["position"]].append(p)
    for k in por:
        por[k].sort(key=lambda p: -(p.get("points") or 0))
    mejor = None
    for nom, (d, m, dl) in FORMACIONES.items():
        if len(por[1]) < 1 or len(por[2]) < d or len(por[3]) < m or len(por[4]) < dl:
            continue
        xi = por[1][:1] + por[2][:d] + por[3][:m] + por[4][:dl]
        pts = sum(p.get("points") or 0 for p in xi)
        if mejor is None or pts > mejor[1]:
            mejor = (nom, pts, xi)
    return mejor


def ventas(f, xi_nombres, de_reventa):
    out = []
    for p in (f.get("roster") or {}).get("players") or []:
        if p["name"] in NUNCA_SE_VENDE or p["name"] in xi_nombres:
            continue
        if p["name"] in de_reventa and (p.get("price_increment") or 0) < 0:
            out.append(p["name"])
    return out


def decidir(f, de_reventa=()):
    jug = (f.get("roster") or {}).get("players") or []
    m = once(jug)
    xi = {p["name"] for p in m[2]} if m else set()
    pujas, cands = reventa(f)
    banquillo = None
    if len(jug) <= 11:
        banquillo = "fichar un DEFENSA de 1-3 M que juegue (E12)" if presupuesto(f) >= 1_000_000 \
            else "hace falta un DEFENSA suplente, pero no hay caja (E12)"
    return dict(once=m and (m[0], m[1], sorted(xi)), pujas=pujas, candidatos=len(cands),
                ventas=ventas(f, xi, set(de_reventa)), banquillo=banquillo, caja=presupuesto(f))


if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        f = json.load(open(ruta))
        print(ruta, json.dumps(decidir(f), ensure_ascii=False))
