"""
Laboratorio, experimento 14 (agenda 5, la arquitectura): ¿que parte de
Pepe gana dinero de verdad?

Pepe tiene muchas vias que compran. Antes de dibujar un bot pequeno hay
que saber cuales han hecho algo bueno. Se cruza cada compra de Pepe al
Computer del tablon (con su viaje: venta o valor de hoy) con la puja
apuntada en `data/trading/bid_outcome_ledger.json`, que dice quien la
decidio (`target_source`):

  SUBASTA_CARTERA   la subasta del reset (especulacion)
  RENDIJA           el carril (revender)
  ACQUISITION_BOARD el tablero, para mejorar el once
  DESCONOCIDO/TABLON  la apunto el tablon sin decision de Pepe: la orden
                    del gestor o el dueno a mano
  DESCONOCIDO/PLANTILLA  la encontro ya en la plantilla: el dueno a mano

Viaje cerrado = venta real - compra. Abierto = valor de hoy - compra
(price_history). Tambien se mira si la compra cumplia la rampa (E1: el
precio subio en el ultimo cambio) y que prima pago.

Uso:  python3 lab/arquitectura/quien_gana.py
"""
import datetime as dt
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
from viajes import Precios, viajes  # noqa: E402

D = dt.timedelta(days=1)


def via(r):
    if not r:
        return "sin apunte"
    s, rb = r.get("target_source"), r.get("recorded_by")
    if s in ("SUBASTA_CARTERA", "RENDIJA", "ACQUISITION_BOARD"):
        return {"SUBASTA_CARTERA": "subasta del reset", "RENDIJA": "carril",
                "ACQUISITION_BOARD": "tablero (once)"}[s]
    return "sin decision de Pepe (tablon)" if rb == "TABLON" else "sin decision de Pepe (plantilla)"


if __name__ == "__main__":
    P = Precios()
    compras, cerrados = viajes(P)
    cerr = {(c["jugador"], c["dia"]): c for c in cerrados if c["manager"] == "Pepe"}
    pujas = defaultdict(list)
    for r in json.load(open(RAIZ / "data/trading/bid_outcome_ledger.json"))["bids"].values():
        if r.get("outcome") == "WON":
            pujas[r["player_id"]].append(r)
    filas = []
    vistos = set()   # el tablon repite eventos (Biwenger los reemite): uno por jugador, dia e importe
    for c in compras:
        if c["manager"] != "Pepe" or (c["jugador"], c["dia"], c["compra"]) in vistos:
            continue
        vistos.add((c["jugador"], c["dia"], c["compra"]))
        d = dt.date.fromisoformat(c["dia"])
        # la puja ganada de ese jugador mas cercana a la compra
        cand = sorted(pujas.get(c["jugador"], []),
                      key=lambda r: abs((dt.date.fromisoformat(r["placed_at"][:10]) - d).days))
        r = cand[0] if cand and abs((dt.date.fromisoformat(cand[0]["placed_at"][:10]) - d).days) <= 3 else None
        k = (c["jugador"], c["dia"])
        if k in cerr:
            pl, estado = cerr[k]["pl"], "cerrado"
        else:
            hoy = P.en(c["jugador"], P.ultimo_dia)
            pl, estado = ((hoy - c["compra"]) if hoy else 0), "abierto"
        venta_dia = cerr[k]["venta_dia"] if k in cerr else None
        filas.append(dict(via=via(r), dia=c["dia"], venta_dia=venta_dia, jugador=c["jugador"],
                          pl=pl, estado=estado, compra=c["compra"],
                          rampa=(c["tend_1d"] or 0) > 0, prima=c["prima_compra"]))
    print(f"Compras de Pepe al Computer en el tablon: {len(filas)} "
          f"({min(f['dia'] for f in filas)} a {max(f['dia'] for f in filas)}); precios hasta {P.ultimo_dia}.\n")
    por = defaultdict(list)
    for f in filas:
        por[f["via"]].append(f)
    print(f"   {'via':<26} {'n':>3} {'cerr':>4} {'P&L total':>12} {'verde':>7} {'metido':>8} {'rampa':>6} {'prima med':>9}")
    for v, fs in sorted(por.items(), key=lambda x: -len(x[1])):
        primas = sorted(f["prima"] for f in fs if f["prima"] is not None)
        pm = primas[len(primas) // 2] if primas else None
        print(f"   {v:<26} {len(fs):3d} {sum(f['estado']=='cerrado' for f in fs):4d} {sum(f['pl'] for f in fs):>+12,.0f}"
              f" {sum(f['pl']>0 for f in fs):3d}/{len(fs):<3d} {sum(f['compra'] for f in fs)/1e6:6.1f} M"
              f" {sum(f['rampa'] for f in fs):3d}/{len(fs):<2d} {'' if pm is None else f'{pm*100:+.1f}%':>9}")
    # fichajes caros revendidos SIN haber jugado una jornada con nosotros
    inicios = sorted({dt.datetime.utcfromtimestamp(e["date"]).date()
                      for e in json.load(open(RAIZ / "data/rival_intelligence/board_events.json"))
                      if e["type"] == "roundStarted"})
    foto = {p["id"]: p["name"] for p in json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]}
    caros = [f for f in filas if f["estado"] == "cerrado" and f["compra"] >= 2_500_000]
    sin_jugar = [f for f in caros if not any(f["dia"] <= str(j) < f["venta_dia"] for j in inicios)]
    print(f"\nFichajes de 2,5 M o mas ya vendidos: {len(caros)}, P&L {sum(f['pl'] for f in caros):+,.0f}")
    print(f"   de ellos, vendidos ANTES de jugar ni una jornada con nosotros: {len(sin_jugar)}, "
          f"P&L {sum(f['pl'] for f in sin_jugar):+,.0f}")
    for f in sin_jugar:
        print(f"     {foto.get(f['jugador'], f['jugador'])!s:<16} {f['dia']} -> {f['venta_dia']}  compra {f['compra']:>10,}  {f['pl']:>+11,.0f}  ({f['via']})")
    print("\nDesde que se encendio la rampa (29/09):")
    for f in sorted(filas, key=lambda f: f["dia"]):
        if f["dia"] >= "2026-09-29":
            print(f"   {f['dia']}  {f['via']:<26} compra {f['compra']:>10,}  {f['estado']:<8} {f['pl']:>+10,.0f}  rampa {f['rampa']}")
