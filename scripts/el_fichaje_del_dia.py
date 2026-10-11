"""
EL FICHAJE DEL DIA (11/10/2026)

POR QUE EXISTE

    El dueño, 11/10: «¿lo has decidido ahora porque te he dicho yo de
    mirar? Esto es lo que quiero que haga Pepe todos los días». Hasta hoy
    las mejoras del once dependian de que el gestor mirara: el comparador
    las enseñaba, la orden solo pujaba por lo que el gestor escribia y la
    subasta solo compraba con caja libre. Esto lo decide cada mañana, con
    reglas fijas, y lo escribe en la orden del gestor (que ya sabe pujar y
    vender con el relevo dentro).

LA REGLA

    Puntos esperados = puntos por partido x titularidad (la vara E16/E23).
    Candidato: jugador del Computer en el mercado de hoy, sano, con 3+
    partidos y 60 %+ de titularidad. Se compara con nuestro titular mas
    flojo de su posicion (ni Yamal ni protegidos). Se ficha el que mas
    gana, si gana al menos `GANANCIA_MINIMA` por jornada y si la caja
    queda en positivo SIN contar premios: saldo - puja + lo que da la
    venta del que sale (al 95 % de su valor) >= 0. Puja: precio + 1 %
    (E9: sin pelear con Pollo17). El que sale solo se vende con el relevo
    dentro (`si_esta`) y con suelo del 90 % de su valor. Uno al dia, y
    nunca si la orden ya tiene un fichaje pendiente.

USO

    python3 -I scripts/el_fichaje_del_dia.py STATUS.json [--escribir]

    Sin `--escribir` solo dice que haria. Con el, actualiza
    config/la_orden_del_gestor.json. Nunca escribe en Biwenger.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[1]
ORDEN = RAIZ / "config" / "la_orden_del_gestor.json"
GANANCIA_MINIMA = 0.5
TITULARIDAD_MINIMA = 60
PARTIDOS_MINIMOS = 3
INTOCABLES = {"yamal", "lamine yamal"}


def _esperado(tasa, prob):
    if tasa is None or prob is None:
        return None
    return float(tasa) * float(prob) / 100.0


def decidir(status: dict, orden: dict) -> dict:
    liga = {p["id"]: p for p in (status.get("todaLaLiga") or {}).get("players") or []}
    escaparate = (status.get("libro_del_escaparate") or {}).get("players") or []
    once = (status.get("lineup") or {}).get("players") or []
    yo = next((m for m in (status.get("league_center") or {}).get("fantasy_standings") or []
               if m.get("is_us")), {})
    saldo = int(yo.get("balance") or 0)
    protegidos = {int(x["player_id"]) for x in orden.get("proteger") or []}

    if orden.get("fichar"):
        return {"accion": "NADA", "motivo": "YA_HAY_UN_FICHAJE_PENDIENTE"}

    nuestros = []
    for p in once:
        lp = liga.get(p["id"], {})
        if str(p.get("name", "")).strip().lower() in INTOCABLES or p["id"] in protegidos:
            continue
        e = _esperado(lp.get("tasa"), p.get("starter_probability"))
        if e is None:
            continue
        nuestros.append({"id": p["id"], "nombre": p["name"], "pos": p.get("position"),
                         "esperado": e, "valor": int(p.get("price") or lp.get("price") or 0)})

    mejores = []
    for c in escaparate:
        lc = liga.get(c["id"], {})
        if lc.get("de_quien") not in (None, "computer"):
            continue
        if str(lc.get("status") or "ok").lower() != "ok":
            continue
        if (c.get("played") or 0) < PARTIDOS_MINIMOS:
            continue
        prob = c.get("starter_probability")
        if prob is None or prob < TITULARIDAD_MINIMA:
            continue
        tasa = lc.get("tasa") or (c["points"] / c["played"] if c.get("played") else None)
        ec = _esperado(tasa, prob)
        rivales = [o for o in nuestros if o["pos"] == c["position"]]
        if ec is None or not rivales:
            continue
        sale = min(rivales, key=lambda o: o["esperado"])
        ganancia = ec - sale["esperado"]
        puja = int(round(c["price"] * 1.01, -3))
        caja = saldo - puja + int(sale["valor"] * 0.95)
        mejores.append({"ficha": c["name"], "ficha_id": c["id"], "puja": puja,
                        "esperado": round(ec, 2), "sale": sale["nombre"],
                        "sale_id": sale["id"], "sale_esperado": round(sale["esperado"], 2),
                        "suelo": int(sale["valor"] * 0.90), "ganancia": round(ganancia, 2),
                        "caja_despues": caja})

    validos = [m for m in mejores if m["ganancia"] >= GANANCIA_MINIMA and m["caja_despues"] >= 0]
    if not validos:
        top = sorted(mejores, key=lambda m: -m["ganancia"])[:3]
        return {"accion": "NADA", "motivo": "NINGUNO_MEJORA_EL_ONCE_CON_CAJA", "saldo": saldo,
                "los_mejores": top}
    m = max(validos, key=lambda m: m["ganancia"])
    return {"accion": "FICHAR", "saldo": saldo, **m}


def escribir(orden: dict, d: dict) -> dict:
    orden["fichar"] = [{"player_id": d["ficha_id"], "nombre": d["ficha"], "puja": d["puja"],
                        "por_que": (f"El fichaje del dia: {d['esperado']} pts esperados por "
                                    f"jornada contra {d['sale_esperado']} de {d['sale']} "
                                    f"(+{d['ganancia']}); caja tras el cambio {d['caja_despues']}.")}]
    orden["vender_si_ficha"] = {"si_esta": d["ficha_id"], "jugadores": [
        {"player_id": d["sale_id"], "nombre": d["sale"], "suelo": d["suelo"]}]}
    orden["conservar"] = [c for c in orden.get("conservar") or [] if c.get("player_id") != d["sale_id"]]
    return orden


def main() -> None:
    status = json.loads(Path(sys.argv[1]).read_text())
    orden = json.loads(ORDEN.read_text())
    d = decidir(status, orden)
    print(json.dumps(d, ensure_ascii=False, indent=1))
    if "--escribir" in sys.argv and d["accion"] == "FICHAR":
        ORDEN.write_text(json.dumps(escribir(orden, d), ensure_ascii=False, indent=2) + "\n")
        print("Orden actualizada.")


if __name__ == "__main__":
    main()
