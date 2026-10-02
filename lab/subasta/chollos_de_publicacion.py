"""
Laboratorio, experimento 12: ¿la venta del Computer se queda con el precio
del dia en que salio? ¿Se puede pujar ese precio viejo cuando el valor ya
ha subido? (el caso Moi Gomez, 01/10)

El caso: el 30/09 el dueño pujo 890.000 por Moi Gomez con el valor ya en
900.000; Biwenger lo acepto y lo gano el 01/10 (valor esa mañana: 920.000).

Datos (solo lectura):
  - tablon (`market` = compras al Computer, con importe y pujas perdedoras);
  - price_history.json (valor de cada dia de mercado);
  - libro_del_escaparate.jsonl: los 20 del Computer de cada dia (17/09 a
    02/10). OJO con la hora de la foto: las de antes del cierre (~05:05 UTC)
    son todavia la lista del dia anterior;
  - bid_outcome_ledger.json (nuestras pujas).

Dia D de una compra = dia de mercado del evento (cierre ~05:05 UTC).
  valor_puja  = valor el dia D-1 (el que se ve mientras se puja)
  valor_dia   = valor el dia D (con el que te despiertas ya dueño)
  pide        = valor el dia en que salio a la venta (primer dia de la racha)

Uso:  python3 lab/subasta/chollos_de_publicacion.py
"""
import datetime as dt
import json
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "lab/rivales"))
sys.path.insert(0, str(RAIZ / "lab/subasta"))
from viajes import NOMBRES, PEPE, POLLO, TABLON, Precios, dia_de_mercado  # noqa: E402
from competencia import viaje  # noqa: E402

D1 = dt.timedelta(days=1)
ESCAPARATE = RAIZ / "data/trading/libro_del_escaparate.jsonl"
LEDGER = RAIZ / "data/trading/bid_outcome_ledger.json"
CIERRE_UTC = dt.time(5, 8)   # las compras del tablon se resuelven entre 05:04 y 05:07


def nombre(uid, por_id):
    return NOMBRES.get(uid) or por_id.get(uid, str(uid))


def compras():
    out, por_id = [], {}
    for e in json.load(open(TABLON)):
        if e["type"] != "market":
            continue
        for x in e["content"]:
            por_id[x["to"]["id"]] = x["to"]["name"]
            out.append(dict(dia=dia_de_mercado(x.get("date", e["date"])), pid=x["player"],
                            quien=x["to"]["id"], importe=x["amount"],
                            perdedoras=[b["amount"] for b in x.get("bids") or []],
                            pujadores={x["to"]["id"]} | {b["user"]["id"] for b in x.get("bids") or []}))
    return out, por_id


def listas_del_computer():
    """{dia: set(ids)} con el dia de la LISTA, no el de la foto."""
    listas = {}
    for linea in open(ESCAPARATE):
        r = json.loads(linea)
        foto = dt.datetime.fromisoformat(r["foto_at"].replace(" ", "T"))
        d = foto.date()
        if foto.time() < CIERRE_UTC:     # foto anterior al cierre: lista de ayer
            d -= D1
        listas[d] = {p["id"] for p in r["players"]}   # si hay dos, vale la ultima
    return listas


if __name__ == "__main__":
    P = Precios()
    C, POR_ID = compras()

    # ------------------------------------------------------------------ 1
    con = [c for c in C if P.en(c["pid"], c["dia"] - D1) and P.en(c["pid"], c["dia"])]
    print(f"1) {len(C)} compras al Computer en el tablon; {len(con)} con valor el dia de puja y el de compra "
          f"({min(c['dia'] for c in con)} a {max(c['dia'] for c in con)}).")
    bajo_puja = [c for c in con if c["importe"] < P.en(c["pid"], c["dia"] - D1)]
    bajo_dia = [c for c in con if c["importe"] < P.en(c["pid"], c["dia"])]
    print(f"   Ganadas POR DEBAJO del valor que se veia al pujar (D-1): {len(bajo_puja)}")
    for c in bajo_puja:
        p2, p1, p0 = (P.en(c["pid"], c["dia"] - k * D1) for k in (2, 1, 0))
        print(f"     {c['dia']}  {nombre(c['quien'], POR_ID):<12} jug {c['pid']:>6}  paga {c['importe']:>10,}"
              f"  valor D-2 {p2:>10,}  D-1 {p1:>10,}  D {p0:>10,}  -> bajo D-1 {c['importe']-p1:>+8,}"
              f"  bajo D {c['importe']-p0:>+8,}  perdedoras {len(c['perdedoras'])}")
    tot = sum(P.en(c["pid"], c["dia"]) - c["importe"] for c in bajo_puja)
    print(f"     total ganado contra el valor del dia de compra: {tot:+,}")
    print(f"   Ganadas por debajo del valor con el que se despiertan (dia D): {len(bajo_dia)} de {len(con)}")
    por = Counter(nombre(c["quien"], POR_ID) for c in bajo_dia)
    print("     por quien: " + ", ".join(f"{k} {v}" for k, v in por.most_common(6)))
    print(f"     (eso es sobre todo que el precio siguio subiendo esa noche; solo {len(bajo_puja)} pagan menos"
          " de lo que ya valia mientras pujaban)")

    # ------------------------------------------------------------------ 2
    print("\n2) El libro de pujas (bid_outcome_ledger) y Moi Gomez (1462):")
    led = json.load(open(LEDGER))["bids"]
    for k, x in led.items():
        if x["player_id"] == 1462:
            print(f"   {k}: puja {x['amount']:,}  {x['outcome']}  apuntado por {x.get('recorded_by')}"
                  f"  origen {x.get('target_source')}  (no la puso Pepe: la vio despues en la plantilla)")
    L = listas_del_computer()
    print("   En la lista del Computer: " + ", ".join(str(d) for d in sorted(L) if 1462 in L[d]))
    print("   Valor: " + ", ".join(f"{d.strftime('%d/%m')} {P.en(1462, d):,}"
                                   for d in (dt.date(2026, 9, 28) + k * D1 for k in range(5))))

    # ------------------------------------------------------------------ 3
    dias = sorted(L)
    print(f"\n3) Listas del Computer reconstruidas: {len(dias)} dias ({dias[0]} a {dias[-1]}); "
          f"faltan: {[str(d) for d in (dias[0] + k * D1 for k in range((dias[-1]-dias[0]).days)) if d not in L]}")
    compra_de = {(c["pid"], c["dia"]): c for c in C}

    # 3a) la vida de una puesta a la venta: cuantos dias seguidos sale
    vida = Counter()
    for d in dias:
        if d - D1 not in L:
            continue
        for pid in L[d] - L[d - D1]:
            n, e = 1, d + D1
            while e in L and pid in L[e]:
                n, e = n + 1, e + D1
            if e in L:
                vida[n] += 1
    print(f"   Dias seguidos en la lista (salidas con dia anterior y posterior conocidos): {dict(sorted(vida.items()))}")
    pide_ok = Counter()
    for c in C:
        d = c["dia"]
        if d - D1 in L and d - 2 * D1 in L and c["pid"] in L[d - D1] and c["pid"] in L[d - 2 * D1]:
            pide_ok[c["importe"] >= P.en(c["pid"], d - 2 * D1)] += 1
    print(f"   Compras en el 2.o dia: importe >= valor del dia en que salio en {pide_ok[True]} de "
          f"{sum(pide_ok.values())} (nadie gana por debajo de lo que PIDE)")

    # 3b) segundos dias: lo que pide contra lo que ya vale
    seg = []
    for d in dias:
        if d - D1 not in L:
            continue
        for pid in L[d] & L[d - D1]:
            if d - 2 * D1 in L and pid in L[d - 2 * D1]:
                continue                       # tercer dia o re-puesto: no se sabe que pide
            pide, vale = P.en(pid, d - D1), P.en(pid, d)
            if pide is None or vale is None:
                continue
            c = compra_de.get((pid, d + D1))
            seg.append(dict(pid=pid, dia=d, pide=pide, vale=vale, compra=c,
                            mañana=P.en(pid, d + D1), pasado=P.en(pid, d + 2 * D1)))
    sube = [s for s in seg if s["vale"] > s["pide"]]
    print(f"   Segundos dias (siguen sin vender un dia despues de salir): {len(seg)}")
    print(f"     valen MAS de lo que piden {len(sube)}   MENOS {sum(s['vale'] < s['pide'] for s in seg)}"
          f"   igual {sum(s['vale'] == s['pide'] for s in seg)}")
    print("     Los que valen mas, uno a uno (dia = 2.o dia en la lista, se puja ese dia):")
    for s in sube:
        c = s["compra"]
        fin = (f"comprado por {nombre(c['quien'], POR_ID)} a {c['importe']:,} ({len(c['pujadores'])} puj.)"
               if c else "nadie lo compro")
        print(f"       {s['dia']}  jug {s['pid']:>6}  pide {s['pide']:>10,}  vale {s['vale']:>10,}"
              f"  ({s['vale']/s['pide']-1:+.1%})  valor al cierre {s['mañana'] or 0:>10,}  -> {fin}")

    # 3c) la regla: pujar LO QUE PIDE (+1 €) por todo el que ya vale mas
    print("\n   Regla «pujar lo que pide por todo el de 2.o dia que ya vale mas»:")
    for extra in (0.0, 0.01, "valor"):
        g = []
        for s in sube:
            puja = s["vale"] if extra == "valor" else round(s["pide"] * (1 + extra)) + 1
            c = s["compra"]
            if c and c["quien"] != PEPE and c["importe"] >= puja:
                continue
            if c and c["quien"] == PEPE:
                rivales = c["perdedoras"]
                if rivales and max(rivales) >= puja:
                    continue
            if s["mañana"] is None:
                continue
            roi, dias_v, _ = viaje(P, s["pid"], s["dia"] + D1, puja)
            g.append(dict(s, puja=puja, al_cierre=s["mañana"] - puja,
                          dia_siguiente=(s["pasado"] or s["mañana"]) - puja, roi=roi, dias_v=dias_v))
        regla = "valor de hoy" if extra == "valor" else f"pide x {1+extra:.2f}"
        print(f"     puja = {regla:<12}: ganadas {len(g)} de {len(sube)}  metido {sum(x['puja'] for x in g):,}")
        print(f"       ganancia contra el valor al cierre {sum(x['al_cierre'] for x in g):>+10,}"
              f"   vendiendo al dia siguiente a valor {sum(x['dia_siguiente'] for x in g):>+10,}"
              f"   viaje E3 {sum(x['puja']*x['roi'] for x in g if x['roi'] is not None):>+10,.0f}"
              f"  (verdes {sum(1 for x in g if (x['roi'] or 0) > 0)}/{len(g)})")
    dias_cubiertos = len([d for d in dias if d - D1 in L])
    print(f"     dias con 2.o dia medible: {dias_cubiertos}")

    # 3d) quien se lleva los de 2.o dia que valen mas
    q = Counter(nombre(s["compra"]["quien"], POR_ID) if s["compra"] else "nadie" for s in sube)
    print("     quien se los llevo: " + ", ".join(f"{k} {v}" for k, v in q.most_common()))
    pollo = sum(1 for s in sube if s["compra"] and POLLO in s["compra"]["pujadores"])
    print(f"     Pollo17 pujo en {pollo} de {len(sube)}")
