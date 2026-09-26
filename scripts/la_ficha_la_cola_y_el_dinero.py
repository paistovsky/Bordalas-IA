"""
La ficha, la cola y el dinero: medido sobre las fotos y los libros.

QUE MIDE

    BLOQUE 1   en que se gastaron las fichas libres (la cesta de la
               ventana del reset), que habia en ese mercado que SI sumara
               al once, y cuanto costo. Y con 1, 2 y 4 fichas libres hoy.
    BLOQUE 2   los que no tienen puntos de mas, desglosados; la cola en la
               unidad comun (`src/analysis/la_cola.py`); a quien habria
               fichado Pepe cada dia con ella y que paso despues; donde
               caen las dos pujas del dueño; y con que se mide el precio
               de reserva.
    BLOQUE 3   el dinero: las ofertas vivas del Computer, la cola de venta
               con su coste en puntos del once, las reservas de solvencia.

LA UNIDAD

    La de `la_cola`: premios de la liga que el once REHECHO cobraria de
    mas (solo puntuan once: `lineupReserves: false`), por euro de caja
    neta. La mejora se calcula con la busqueda de produccion sobre las
    siete formaciones, y los puntos con `estimate_season_points`, como la
    valoracion.

DE DONDE SALE CADA COSA

    Fotos del panel: 14/09 (`dashboard/data/status.json`), 18/09
    (`data/fotos/`), 23/09 y 25/09 (`diagnostico/`). Mercados de los dias
    de la cesta: `libro_del_escaparate.jsonl` y la foto del 14/09.
    Compras: `bid_outcome_ledger.json`. Historico de la temporada pasada:
    el catalogo del disco. Precio de hoy: `price_history.json`.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende nada y NO
    ESCRIBE NI UNA LINEA DE NINGUN LIBRO.

USO

    python scripts/la_ficha_la_cola_y_el_dinero.py > salida.txt 2>&1
"""

from __future__ import annotations

import bisect
import glob
import json
import os
import statistics
import sys

from collections import Counter
from datetime import datetime, timedelta, timezone


sys.path.insert(0, os.getcwd())

from src.analysis.la_cola import el_mejor_once, mejora_del_once, ordenar, unidad   # noqa: E402
from src.analysis.player_value_engine import estimate_season_points               # noqa: E402


FOTOS = {
    "14/09": "dashboard/data/status.json",
    "18/09": "data/fotos/2026-09-18.json",
    "23/09": "diagnostico/status-2026-09-23.json",
    "25/09": "diagnostico/status.json",
}

JERARQUIA = {"Clave": 50, "Importante": 40, "Rotación": 30, "Revulsivo": 25,
             "Reserva": 20, "Descarte": 10}

POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}

DUEÑO = {"Juan Iglesias": 3_520_000, "Antonio Blanco": 3_288_000}


def cargar(ruta):
    return json.load(open(ruta, encoding="utf-8-sig"))


def catalogo():
    ruta = sorted(glob.glob("data/snapshot_202609*.json"))[-1]
    return cargar(ruta)["catalog"]["data"]["players"]


def puntos_de(fila, cat, tarifa):
    """La proyeccion de la valoracion, con lo que trae la fila."""

    c = cat.get(str(fila.get("id"))) or {}
    historico = fila.get("points_last_season")
    if historico is None:
        historico = c.get("pointsLastSeason")
    jerarquia = fila.get("hierarchy_value")
    if jerarquia is None:
        jerarquia = JERARQUIA.get(fila.get("hierarchy"))
    starter = {
        "probability": fila.get("starter_probability"),
        "consensus": fila.get("starter_consensus"),
        "hierarchy_value": jerarquia,
        "hierarchy_label": fila.get("hierarchy"),
        "absence": fila.get("absence"),
        "next_match": fila.get("next_match"),
    }
    r = estimate_season_points(
        {"pointsLastSeason": historico, "price": fila.get("price") or fila.get("market_price"),
         "teamID": c.get("teamID")},
        {"rate_median": tarifa}, None, starter,
    )
    return r["points"]


def la_plantilla(foto, cat):
    tarifa = (foto.get("season_horizon") or {}).get("euros_per_point") or 21_500
    filas = (foto.get("roster") or {}).get("players") or []
    return [
        {"id": f["id"], "name": f["name"], "pos": int(f["position"]),
         "pts": puntos_de(f, cat, tarifa), "price": int(f.get("price") or 0),
         "starter": bool(f.get("is_starter")), "prob": f.get("starter_probability")}
        for f in filas
    ], tarifa


def jornadas(foto):
    return (foto.get("season_horizon") or {}).get("matchdays_remaining") or 31


class Precios:
    def __init__(self):
        crudo = cargar("data/autopilot/price_history.json")
        self.s = {str(k): (v.get("t") or [], v.get("p") or []) for k, v in crudo["players"].items()}

    def en(self, pid, cuando=None):
        t, p = self.s.get(str(pid), ([], []))
        if not p:
            return None
        if cuando is None:
            return p[-1]
        i = bisect.bisect_right(t, cuando.timestamp()) - 1
        return p[i] if i >= 0 else None


def la_cola_de(foto, cat, candidatos, plantilla, base, quedan, recuperado=0):
    """`candidatos`: `[{id, name, pos, pts, precio, ...}]`. Devuelve la cola."""

    minimo = min(p["pts"] for p in plantilla if p["id"] in base["ids"])
    filas = []
    for c in candidatos:
        if c["pts"] <= minimo:
            # No puede entrar: no gana a ninguno de los once.
            m = {"mejora": 0, "entra": False, "formacion": base["formacion"], "salen": []}
        else:
            m = mejora_del_once(plantilla, {"id": c["id"], "pos": c["pos"], "pts": c["pts"]}, base)
        u = unidad(m["mejora"], c["precio"], quedan, recuperado=recuperado)
        filas.append({**c, **m, **u})
    return ordenar(filas)


# ============================================================
# BLOQUE 1
# ============================================================


def bloque_1(cat, precios):

    print("=" * 78)
    print("BLOQUE 1 — LA FICHA")
    print("=" * 78)

    libro = cargar("data/trading/bid_outcome_ledger.json")["bids"]
    pujas = list(libro.values()) if isinstance(libro, dict) else libro
    compras = [p for p in pujas if p["outcome"] == "WON" and p["placed_at"] >= "2026-09-13"
               and p.get("target_source") in ("SUBASTA_CARTERA", "DESCONOCIDO")
               and p.get("recorded_by") in (None, "PLANTILLA")]
    print("  COMPRAS QUE OCUPARON FICHA (la cesta y las que entraron por PLANTILLA):")
    for p in sorted(compras, key=lambda p: p["placed_at"]):
        print(f"    {p['placed_at'][:16]}  {p['player_name']:16s} {p['amount']:>9}  "
              f"{p.get('target_source')}/{p.get('recorded_by')}  intent {p.get('intent')}  "
              f"P(ganar) {p.get('win_probability')}  valor apuntado {p.get('our_value')}")

    # LOS MERCADOS DE ESOS DIAS, y la plantilla de la foto mas cercana.
    esc = {}
    for linea in open("data/trading/libro_del_escaparate.jsonl", encoding="utf-8"):
        e = json.loads(linea)
        esc[(e["dia_de_mercado"], e["foto_at"][11:16])] = e["players"]
    ventanas = (
        ("15/09", "14/09", [
            {**f, "price": f["market_price"]} for f in cargar(FOTOS["14/09"])["acquisition"]["targets"]
            if f.get("seller_id") is None], ["Balde", "Benavidez", "Paco Cortés", "Selu Diallo"]),
        ("18/09", "18/09", esc[("2026-09-17", "16:15")], ["Marcão", "Barzic", "Iturbe", "Esquivel"]),
        ("21/09", "23/09", esc[("2026-09-21", "05:02")], ["Yeray", "Diaby", "Guevara"]),
        ("23/09", "23/09", esc[("2026-09-23", "05:10")], ["Unai López"]),
    )

    print()
    print("  EN CADA VENTANA: LO QUE SE COMPRO Y LO MEJOR DEL MISMO MERCADO QUE SUMABA AL ONCE")
    for dia, foto_de, mercado, comprados in ventanas:
        foto = cargar(FOTOS[foto_de])
        plantilla, tarifa = la_plantilla(foto, cat)
        # La plantilla ANTES de la compra: fuera los comprados en esa ventana.
        plantilla = [p for p in plantilla if p["name"] not in comprados]
        base = el_mejor_once(plantilla)
        quedan = jornadas(foto)
        bolsillo = (foto["acquisition"].get("budgets") or {}).get("acquisition")
        candidatos = [
            {"id": f["id"], "name": f["name"], "pos": int(f["position"]),
             "pts": (f.get("expected_points") if f.get("expected_points") is not None
                     else puntos_de(f, cat, tarifa)),
             "precio": int(f.get("price") or f.get("market_price") or 0)}
            for f in mercado
        ]
        cola = la_cola_de(foto, cat, candidatos, plantilla, base, quedan)
        print(f"  --- ventana del {dia} (plantilla de la foto del {foto_de}, {len(plantilla)} sin los "
              f"comprados; {base['formacion']} {base['puntos']:.0f}; quedan {quedan}; "
              f"bolsillo de fichar {bolsillo}); mercado n={len(candidatos)}")
        for c in cola:
            if c["name"] in comprados or c["mejora"] > 0:
                marca = "COMPRADO" if c["name"] in comprados else ("cabe" if bolsillo and c["precio"] <= bolsillo else "no cabe")
                print(f"      {marca:8s} {c['name']:18s} {POS[c['pos']]} pts {c['pts']:4d} precio {c['precio']:>9}  "
                      f"mejora del once {c['mejora']:+4d} ({c['formacion']})  premios {c['premios']:>9}  "
                      f"rendimiento {c['rendimiento'] if c['rendimiento'] is not None else '-'}")
        mejor = next((c for c in cola if c["mejora"] > 0 and bolsillo and c["precio"] <= bolsillo), None)
        gastado = [c for c in cola if c["name"] in comprados]
        print(f"      => lo comprado suma al once {sum(c['mejora'] for c in gastado):+d} puntos "
              f"({sum(c['premios'] for c in gastado)} EUR de premios) por {sum(c['precio'] for c in gastado)} EUR; "
              + (f"lo mejor que cabia: {mejor['name']} {mejor['mejora']:+d} puntos, {mejor['premios']} EUR de premios "
                 f"por {mejor['precio']} EUR" if mejor else "no habia NADIE que sumara al once y cupiera"))

    # CON 1, 2 Y 4 FICHAS LIBRES HOY
    print()
    print("  HOY (25/09) CON 1, 2 Y 4 FICHAS LIBRES: sin vender a nadie, bolsillo de fichar de la foto")
    foto = cargar(FOTOS["25/09"])
    plantilla, tarifa = la_plantilla(foto, cat)
    base = el_mejor_once(plantilla)
    quedan = jornadas(foto)
    bolsillo = (foto["acquisition"].get("budgets") or {}).get("acquisition")
    candidatos = [
        {"id": f["id"], "name": f["name"], "pos": int(f["position"]), "pts": int(f.get("expected_points") or 0),
         "precio": int(f["market_price"]), "rival": f.get("seller_id") is not None}
        for f in foto["acquisition"]["targets"] if f.get("expected_points") is not None
        # Solo los que pueden jugar: un lesionado no suma al once.
        and str(f.get("availability") or "").upper() in ("DISPONIBLE", "OK", "")
        and str(f.get("status") or "ok").lower() in ("ok", "unknown")
    ]
    cola = la_cola_de(foto, cat, candidatos, plantilla, base, quedan)
    suman = [c for c in cola if c["mejora"] > 0]
    del_computer = [c for c in suman if not c["rival"]]
    print(f"    de {len(candidatos)} con proyeccion, suman al once {len(suman)} "
          f"({len(del_computer)} del Computer); con el bolsillo de {bolsillo}:")
    for fichas in (1, 2, 4):
        caja, elegidos, actual, base_k = bolsillo or 0, [], list(plantilla), base
        for c in del_computer:
            if len(elegidos) >= fichas:
                break
            if c["precio"] > caja:
                continue
            m = mejora_del_once(actual, {"id": c["id"], "pos": c["pos"], "pts": c["pts"]}, base_k)
            if m["mejora"] <= 0:
                continue
            elegidos.append((c["name"], c["precio"], m["mejora"]))
            caja -= c["precio"]
            actual = actual + [{"id": c["id"], "pos": c["pos"], "pts": c["pts"], "name": c["name"]}]
            base_k = el_mejor_once(actual)
        print(f"      {fichas} ficha(s): pasarian {len(elegidos)}  {elegidos}")
    print("    y sin mirar la caja (lo que el tope de fichas dejaria entrar):")
    for fichas in (1, 2, 4):
        print(f"      {fichas} ficha(s): " + ", ".join(
            f"{c['name']} {c['mejora']:+d} ({c['rendimiento']:.1%}, {c['precio']})" for c in del_computer[:fichas]))

    return cola, plantilla, base


# ============================================================
# BLOQUE 2
# ============================================================


def bloque_2(cat, precios, cola_hoy):

    print()
    print("=" * 78)
    print("BLOQUE 2 — LA COLA")
    print("=" * 78)

    foto = cargar(FOTOS["25/09"])
    filas = foto["acquisition"]["targets"]
    sin_puntos = [f for f in filas if not ((f.get("los_dos_techos") or {}).get("el_que_se_queda") or {}).get("available")]
    motivo = Counter()
    for f in sin_puntos:
        q = ((f.get("los_dos_techos") or {}).get("el_que_se_queda") or {})
        if q.get("reason"):
            motivo[("SIN_PUNTOS_DE_MAS", f.get("xi_decision") or "sin via del once")] += 1
        else:
            motivo[("SIN_TECHOS", f.get("would_be_decision") or f.get("decision"))] += 1
    print(f"  SIN `el_que_se_queda` en la foto del 25/09: {len(sin_puntos)} de {len(filas)}")
    for (grupo, que), n in sorted(motivo.items(), key=lambda x: (x[0][0], -x[1])):
        print(f"      {grupo:18s} {str(que):28s} {n}")

    print()
    print("  LA COLA DE HOY, en la unidad comun (todos los que suman al once):")
    for i, c in enumerate([c for c in cola_hoy if c["mejora"] > 0], start=1):
        dueño = f"  <- PUJA DEL DUEÑO {DUEÑO[c['name']]}" if c["name"] in DUEÑO else ""
        print(f"    {i:2d}. {c['name']:18s} {POS[c['pos']]} precio {c['precio']:>9}  mejora {c['mejora']:+4d} "
              f"({c['formacion']})  premios {c['premios']:>9}  rendimiento {c['rendimiento']:.1%}"
              f"{'  [rival]' if c['rival'] else ''}{dueño}")

    # A QUIEN HABRIA FICHADO CADA DIA, Y QUE PASO
    print()
    print("  CADA DIA CON FOTO: el primero de la cola del Computer que cabe, y que paso despues")
    liga = {str(p["id"]): p for p in cargar(FOTOS["25/09"])["todaLaLiga"]["players"]}
    for dia, ruta in FOTOS.items():
        foto = cargar(ruta)
        plantilla, tarifa = la_plantilla(foto, cat)
        base = el_mejor_once(plantilla)
        quedan = jornadas(foto)
        bolsillo = (foto["acquisition"].get("budgets") or {}).get("acquisition")
        candidatos = [
            {"id": f["id"], "name": f["name"], "pos": int(f["position"]), "pts": int(f["expected_points"]),
             "precio": int(f["market_price"]), "puntos_entonces": f.get("points"), "rival": False}
            for f in foto["acquisition"]["targets"]
            if f.get("seller_id") is None and f.get("expected_points") is not None
            and str(f.get("availability") or "").upper() in ("DISPONIBLE", "OK", "")
        ]
        cola = la_cola_de(foto, cat, candidatos, plantilla, base, quedan)
        suman = [c for c in cola if c["mejora"] > 0]
        elegido = next((c for c in suman if bolsillo and c["precio"] <= bolsillo), None)
        print(f"    {dia}: del Computer suman al once {len(suman)} de {len(candidatos)}; bolsillo {bolsillo}; "
              f"hoy pujables {foto['acquisition'].get('biddable')}")
        if elegido:
            hoy = liga.get(str(elegido["id"])) or {}
            precio_hoy = precios.en(elegido["id"])
            print(f"        ficharia a {elegido['name']} por {elegido['precio']} (mejora {elegido['mejora']:+d}, "
                  f"{elegido['rendimiento']:.1%}). Hoy: precio {precio_hoy} "
                  f"({(precio_hoy - elegido['precio']) * 100 / elegido['precio']:+.1f} %), puntos "
                  f"{elegido.get('puntos_entonces')} -> {hoy.get('points')} en {hoy.get('played')} partidos")
        else:
            primero = suman[0] if suman else None
            print("        no ficharia a nadie: "
                  + (f"el primero, {primero['name']} ({primero['precio']}), no cabe" if primero else "nadie suma al once"))

    # EL PRECIO DE RESERVA: con que se mide
    print()
    print("  EL PRECIO DE RESERVA, lo que hay para medirlo:")
    cuando = datetime(2026, 9, 11, 6, tzinfo=timezone.utc)
    grupos = {"titulares que puntuan (>= 4 pts/partido, >= 4 jugados)": [], "el resto": []}
    for p in liga.values():
        antes = precios.en(p["id"], cuando)
        ahora = precios.en(p["id"])
        if not antes or not ahora:
            continue
        r = (ahora - antes) * 100 / antes
        bueno = (p.get("played") or 0) >= 4 and (p.get("points") or 0) / max(1, p.get("played") or 1) >= 4
        grupos["titulares que puntuan (>= 4 pts/partido, >= 4 jugados)" if bueno else "el resto"].append(r)
    for nombre, v in grupos.items():
        if v:
            print(f"      precio 11/09 -> 25/09 (14 dias), {nombre}: n={len(v)}  mediana {statistics.median(v):+.2f} %  "
                  f"subieron {100 * sum(x > 0 for x in v) / len(v):.0f} %")
    prima = (foto["acquisition"].get("computer_premium") or {})
    print(f"      prima mediana del Computer al recomprar: {prima.get('median_percent')} % "
          f"(n={prima.get('samples') or prima.get('n')})")


# ============================================================
# BLOQUE 3
# ============================================================


def bloque_3(cat):

    print()
    print("=" * 78)
    print("BLOQUE 3 — EL DINERO")
    print("=" * 78)

    foto = cargar(FOTOS["25/09"])
    plantilla, tarifa = la_plantilla(foto, cat)
    base = el_mejor_once(plantilla)
    por_nombre = {p["name"]: p for p in plantilla}

    reloj = foto["solvency_clock"]
    print(f"  caja {reloj['balance']}  pujas vivas {reloj['committed_bids']}  deficit del reloj {reloj['deficit']}  "
          f"ofertas vivas ahora {reloj['covered_now']}  al plazo {reloj['covered_at_deadline']}")

    print()
    print("  LAS OFERTAS VIVAS DEL COMPUTER (se cobran al aceptar), con lo que cuesta cada venta:")
    total_libre = total_reservado = 0
    for o in sorted(foto["offers"], key=lambda o: -o["amount"]):
        nombre = o["players"][0]
        p = por_nombre.get(nombre) or {}
        sin_el = [x for x in plantilla if x["name"] != nombre]
        otro = el_mejor_once(sin_el)
        coste = round(base["puntos"] - otro["puntos"])
        premios = unidad(coste, 1, jornadas(foto))["premios"]
        if o["solvency_reserved"]:
            total_reservado += o["amount"]
        elif o["action"] not in ("NEVER_SELL",):
            total_libre += o["amount"]
        print(f"    {nombre:16s} {o['amount']:>9}  {o['action']:24s} {o.get('protection'):16s} "
              f"{'RESERVADA' if o['solvency_reserved'] else '         '}  caduca en {o.get('hours_to_expiry'):5.1f} h  "
              f"| en el once: {'si' if p.get('id') in base['ids'] else 'no'}; venderlo cuesta {coste:+d} puntos "
              f"({premios} EUR de premios); libera 1 ficha")
    print(f"    ofertas no reservadas y vendibles (sin Yamal): {total_libre}   reservadas por solvencia: {total_reservado}")

    print()
    print("  LA COLA DE VENTA (`sale_order`): lo que hay que vender primero, y como se cobra")
    for q in foto["sale_order"]["queue"]:
        p = por_nombre.get(q["name"]) or {}
        sin_el = [x for x in plantilla if x["name"] != q["name"]]
        coste = round(base["puntos"] - el_mejor_once(sin_el)["puntos"])
        print(f"    {q['order']:2d}. {q['name']:16s} precio {q['price']:>9}  {q['tier']:18s} {q.get('cash_kind'):12s} "
              f"cobra ahora {q.get('cash_now')}  | coste en puntos del once {coste:+d}")

    print()
    print("  LAS RESERVAS DE SOLVENCIA:")
    reservadas = [o for o in foto["offers"] if o["solvency_reserved"]]
    suma = sum(o["amount"] for o in reservadas)
    print(f"    {len(reservadas)} reservadas, suman {suma}; la deuda contra la que se reserva es la de caja "
          f"({-reloj['balance']}), no el deficit del reloj ({reloj['deficit']}): sobran {suma + reloj['balance']}")
    print("    (ordenadas por importe: el orden del motor -franquicia, valor estrategico, prima- no se publica en la foto)")
    for o in sorted(reservadas, key=lambda o: o["amount"]):
        print(f"      {o['players'][0]:16s} {o['amount']:>9}  prima {o.get('premium_percent')} %")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cat = catalogo()
    precios = Precios()
    cola_hoy, _, _ = bloque_1(cat, precios)
    bloque_2(cat, precios, cola_hoy)
    bloque_3(cat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
