"""
E26 · 08/10/2026: ¿como hacen dinero Pollo17 y Luismi_Haz?

Descompone la ganancia de patrimonio desde el arranque (23,3 M cada uno)
de Pollo17, Luismi_Haz y Pepe en:

  - viajes cerrados (compra -> venta del mismo jugador, FIFO): venta - compra
  - revalorizacion latente de la plantilla de hoy: valor - lo que se pago
  - premios (jornadas + racha diaria)
  - otros: la plantilla de salida (regalada) vendida o aun en casa

y mide el estilo de compraventa, la plantilla «almacen» (lo que no juega
y solo esta para revalorizarse), la deuda (saldo en rojo y al empezar
cada jornada) y lo que da al dia cada plantilla.

Solo LEE. Nada de src/, nada de red, no escribe en ningun sitio.
  - rival_intelligence.json (el que se pase como argumento; no esta en
    git: lo deja el ciclo como artefacto). Movimientos de los 8, plantilla
    de hoy con precio y price_increment, saldo reconstruido, premios.
  - data/rival_intelligence/board_events.json: fechas de las jornadas
    (`roundStarted`/`roundFinished`) y la racha (`bonus`).
  - data/autopilot/price_history.json: precio de cada dia (16/08 en
    adelante; faltan dias sueltos y jugadores que nadie siguio).

Los datos bajados son datos, no codigo: se leen con json y nada mas.
Ejecutar con `python3 -I`.

Uso:  python3 -I lab/rivales/como_hacen_dinero.py RUTA/rival_intelligence.json
"""
import bisect
import datetime as dt
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABLON = RAIZ / "data/rival_intelligence/board_events.json"
PRECIOS = RAIZ / "data/autopilot/price_history.json"

PEPE, POLLO, LUISMI = 14175949, 14145555, 14156489
NOM = {POLLO: "Pollo17", LUISMI: "Luismi_Haz", PEPE: "Pepe"}
INICIAL = 23_300_000
VENTANA = 3_600  # misma reja de copias que caja_de_la_liga (VENTANA_REEMISION)
RESET_UTC_H = 5
FORMACIONES = [(3, 4, 3), (3, 5, 2), (4, 4, 2), (4, 3, 3), (4, 5, 1), (5, 4, 1), (5, 3, 2)]
HOY = dt.date(2026, 10, 8)


def dia_de_mercado(ts):
    d = dt.datetime.utcfromtimestamp(ts)
    if d.hour < RESET_UTC_H:
        d -= dt.timedelta(days=1)
    return d.date()


def M(x):
    return f"{x / 1e6:+.2f} M" if x is not None else "  -  "


def pc(x):
    return f"{x * 100:+.1f} %" if x is not None else "-"


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


class Precios:
    def __init__(self):
        crudo = json.load(open(PRECIOS))["players"]
        self.s = {}
        for pid, v in crudo.items():
            dias = {}
            for t, p in zip(v["t"], v["p"]):
                dias[dia_de_mercado(t)] = p
            o = sorted(dias)
            self.s[int(pid)] = (o, [dias[d] for d in o])

    def en(self, pid, dia, tol=3):
        s = self.s.get(pid)
        if not s:
            return None
        i = bisect.bisect_right(s[0], dia) - 1
        if i < 0 or (dia - s[0][i]).days > tol:
            return None
        return s[1][i]

    def exacto(self, pid, dia):
        return self.en(pid, dia, tol=0)


def sin_copias(trans):
    """Quita las reemisiones del tablon (misma operacion en menos de 1 h)."""
    vistos, out = {}, []
    for t in sorted(trans, key=lambda t: t["date"]):
        clave = (t["kind"], t["player_id"], t["amount"], t.get("counterparty_id"))
        p = vistos.get(clave)
        if p is not None and t["date"] - p <= VENTANA:
            continue
        vistos[clave] = t["date"]
        out.append(t)
    return out


def calendario():
    ev = json.load(open(TABLON))
    inicios, racha, vistos = {}, defaultdict(list), {}
    fin = {}
    for e in sorted(ev, key=lambda e: e["date"]):
        if e["type"] == "roundStarted":
            r = e["content"]["round"]
            inicios.setdefault(r["id"], (e["date"], r["name"]))
        elif e["type"] == "roundFinished":
            for b in e["content"] if isinstance(e["content"], list) else [e["content"]]:
                fin[b["round"]["id"]] = (e["date"], b["round"]["name"], b.get("results") or [])
        elif e["type"] == "bonus":
            for op in e["content"]:
                u = (op.get("user") or {}).get("id")
                clave = (u, op.get("amount"), op.get("reason"))
                p = vistos.get(clave)
                if p is not None and e["date"] - p <= VENTANA:
                    continue
                vistos[clave] = e["date"]
                racha[u].append((e["date"], op.get("amount", 0)))
    return inicios, fin, racha


def mejor_once(roster):
    """Once de mas puntos de temporada (vara simple) en una formacion valida."""
    porpos = defaultdict(list)
    for j in roster:
        porpos[j["position"]].append(j)
    for k in porpos:
        porpos[k].sort(key=lambda j: (j.get("points") or 0, j["value"]), reverse=True)
    mejor, ids = -1, set()
    for d, m_, f in FORMACIONES:
        if len(porpos[1]) < 1 or len(porpos[2]) < d or len(porpos[3]) < m_ or len(porpos[4]) < f:
            continue
        el = porpos[1][:1] + porpos[2][:d] + porpos[3][:m_] + porpos[4][:f]
        pts = sum(j.get("points") or 0 for j in el)
        if pts > mejor:
            mejor, ids = pts, {j["id"] for j in el}
    return ids


def analiza(man, P, inicios, fin, racha):
    uid = man["user_id"]
    tr = sin_copias(man["transactions"])
    ventas = sum(t["amount"] for t in tr if t["delta"] > 0)
    compras = sum(t["amount"] for t in tr if t["delta"] < 0)
    r = dict(nombre=NOM[uid], cuadre_ventas=ventas - man["sales_total"],
             cuadre_compras=compras - man["purchases_total"])

    # ---- FIFO por jugador: viajes cerrados, ventas de la plantilla regalada
    lotes = defaultdict(list)
    viajes, regaladas = [], []
    for t in tr:
        pid = t["player_id"]
        if t["delta"] < 0:
            lotes[pid].append(t)
        else:
            if lotes[pid]:
                c = lotes[pid].pop(0)
                viajes.append((c, t))
            else:
                regaladas.append(t)
    roster = man["roster"]
    lat, lat_coste, lat_valor, en_casa_regalo = 0, 0, 0, 0
    sin_lote = []
    for j in roster:
        if lotes[j["id"]]:
            c = lotes[j["id"]].pop(0)
            lat += j["value"] - c["amount"]
            lat_coste += c["amount"]
            lat_valor += j["value"]
        else:
            en_casa_regalo += j["value"]
            sin_lote.append(j["name"])
    huerfanas = sum(len(v) for v in lotes.values())  # compras sin venta ni plantilla
    realizado = sum(v["amount"] - c["amount"] for c, v in viajes)
    premios = man["matchday_bonus"] + man["streak_total"]
    regalo = sum(t["amount"] for t in regaladas) + en_casa_regalo
    ganancia = man["net_worth"] - INICIAL
    r.update(ganancia=ganancia, realizado=realizado, latente=lat, premios=premios,
             jornadas=man["matchday_bonus"], racha=man["streak_total"], regalo=regalo,
             resto=ganancia - realizado - lat - premios - regalo, huerfanas=huerfanas,
             sin_lote=sin_lote, lat_coste=lat_coste, lat_valor=lat_valor,
             n_regaladas_vendidas=len(regaladas))

    # ---- estilo de los viajes
    filas = []
    for c, v in viajes:
        dc, dv = dia_de_mercado(c["date"]), dia_de_mercado(v["date"])
        p_ayer = P.exacto(c["player_id"], dc - dt.timedelta(days=1))
        p_anteayer = P.exacto(c["player_id"], dc - dt.timedelta(days=2))
        p_v = P.exacto(v["player_id"], dv)
        p_v_ayer = P.exacto(v["player_id"], dv - dt.timedelta(days=1))
        # ¿la venta fue la primera bajada desde la compra?
        primera_bajada = None
        s = P.s.get(c["player_id"])
        if s and p_v is not None and p_v_ayer is not None:
            dias, ps = s
            baj = [d for i, d in enumerate(dias) if i > 0 and dc < d <= dv and ps[i] < ps[i - 1]
                   and (d - dias[i - 1]).days == 1]
            primera_bajada = bool(baj) and baj[0] == dv
        filas.append(dict(
            jugador=c["player_name"], compra=c["amount"], venta=v["amount"],
            pl=v["amount"] - c["amount"], roi=v["amount"] / c["amount"] - 1,
            dias=(v["date"] - c["date"]) / 86400,
            de_computer=c["kind"] == "BUY_FROM_COMPUTER", a_computer=v["kind"] == "SELL_TO_COMPUTER",
            subia=(None if p_ayer is None or p_anteayer is None else p_ayer > p_anteayer),
            prima_compra=None if p_ayer is None else c["amount"] / p_ayer - 1,
            prima_venta=None if p_v is None else v["amount"] / p_v - 1,
            dia_bajada=None if p_v is None or p_v_ayer is None else p_v < p_v_ayer,
            primera_bajada=primera_bajada,
            mes=dv.month,
            antes_jornada=any(0 <= ts - v["date"] <= 86400 for ts, _ in inicios.values()),
        ))
    r["viajes"] = filas

    # ---- usuario a usuario
    r["u2u"] = [(t["kind"], t["player_name"], t["amount"], t.get("counterparty_name"),
                 str(dia_de_mercado(t["date"]))) for t in tr if "USER" in t["kind"]]

    # ---- plantilla en el tiempo y caja en el tiempo
    n_ini = man["roster_count"] - sum(1 for t in tr if t["delta"] < 0) + sum(1 for t in tr if t["delta"] > 0)
    r["n_inicial"] = n_ini
    movs = [(t["date"], t["delta"], -1 if t["delta"] > 0 else 1, t["player_id"]) for t in tr]
    for rid, (ts, nombre, res) in fin.items():
        if nombre == "Jornada 1":  # la liga no la pago
            continue
        for f in res:
            if (f.get("user") or {}).get("id") == uid:
                movs.append((ts, f.get("bonus", 0), 0, None))
    for ts, a in racha.get(uid, []):
        movs.append((ts, a, 0, None))
    movs.sort()
    caja, n, minimo, rojo_dias = INICIAL, n_ini, (INICIAL, None), set()
    serie_n, serie_caja = {}, []
    tenencia = defaultdict(int)
    for j in roster:
        tenencia[j["id"]] = 0
    for ts, delta, dn, pid in movs:
        caja += delta
        n += dn
        serie_n[dia_de_mercado(ts)] = n
        serie_caja.append((ts, caja))
        if caja < minimo[0]:
            minimo = (caja, ts)
        if caja < 0:
            rojo_dias.add(dia_de_mercado(ts))
    r["caja_final"] = caja
    r["caja_minima"] = minimo
    r["dias_en_rojo_movs"] = len(rojo_dias)
    # saldo al empezar cada jornada
    al_inicio = []
    for rid, (ts, nombre) in sorted(inicios.items(), key=lambda kv: kv[1][0]):
        c = INICIAL
        for t2, cj in serie_caja:
            if t2 <= ts:
                c = cj
        al_inicio.append((nombre, str(dt.datetime.utcfromtimestamp(ts).date()), c))
    r["al_inicio"] = al_inicio
    # tiempo en rojo: dias de calendario con saldo < 0 en algun momento
    d0 = dia_de_mercado(movs[0][0])
    rojo = 0
    i, c = 0, INICIAL
    dia = d0
    while dia <= HOY:
        peor = c
        while i < len(serie_caja) and dia_de_mercado(serie_caja[i][0]) <= dia:
            c = serie_caja[i][1]
            peor = min(peor, c)
            i += 1
        if peor < 0 or c < 0:
            rojo += 1
        dia += dt.timedelta(days=1)
    r["dias_en_rojo"] = rojo
    r["dias_total"] = (HOY - d0).days + 1
    r["serie_n"] = serie_n

    # ---- plantilla de hoy: once y almacen
    once = mejor_once(roster)
    alm = [j for j in roster if j["id"] not in once]
    r["once_valor"] = sum(j["value"] for j in roster if j["id"] in once)
    r["alm"] = sorted(((j["name"], j["value"], j["price_increment"], j.get("points"),
                        j["value"] - (j.get("acquisition_price") or j["value"]))
                       for j in alm), key=lambda x: -x[1])
    r["inc_hoy"] = man["roster_price_increment"]
    r["latente_por_jugador"] = sorted(
        ((j["name"], j["value"], j["value"] - (j.get("acquisition_price") or j["value"]), j["id"] in once)
         for j in roster), key=lambda x: -x[2])
    # ventas en las 24 h antes de que empiece cada jornada (la «liquidacion»)
    liq = []
    for rid, (ts, nombre) in sorted(inicios.items(), key=lambda kv: kv[1][0]):
        v24 = [t for t in tr if t["delta"] > 0 and ts - 86400 <= t["date"] <= ts]
        antes = [c for t2, c in serie_caja if ts - 4 * 86400 <= t2 <= ts]
        liq.append((nombre, len(v24), sum(t["amount"] for t in v24), min(antes) if antes else None))
    r["liquidacion"] = liq
    r["valor"] = man["roster_value"]
    return r


def revalorizacion_diaria(man, P, tr):
    """Lo que gano al dia la plantilla que tenia cada dia (precio de cierre a cierre)."""
    tr = sin_copias(tr)
    eventos = sorted((dia_de_mercado(t["date"]), t["delta"] < 0, t["player_id"]) for t in tr)
    tiene = defaultdict(int)
    # plantilla de hoy hacia atras
    for j in man["roster"]:
        tiene[j["id"]] += 1
    for dia, compra, pid in reversed(eventos):
        tiene[pid] += -1 if compra else 1
    # tiene = plantilla regalada (antes de todo movimiento)
    out = {}
    d = dt.date(2026, 8, 17)
    k = 0
    while k < len(eventos) and eventos[k][0] < d:
        _, compra, pid = eventos[k]
        tiene[pid] += 1 if compra else -1
        k += 1
    while d <= HOY:
        # la ganancia del dia D se la lleva quien tenia el jugador al cerrar D-1
        gan, cub, tot = 0, 0, 0
        for pid, n in tiene.items():
            if n <= 0:
                continue
            tot += n
            a, b = P.exacto(pid, d - dt.timedelta(days=1)), P.exacto(pid, d)
            if a is not None and b is not None:
                gan += n * (b - a)
                cub += n
        out[d] = (gan, cub, tot)
        while k < len(eventos) and eventos[k][0] <= d:
            _, compra, pid = eventos[k]
            tiene[pid] += 1 if compra else -1
            k += 1
        d += dt.timedelta(days=1)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ri = json.load(open(sys.argv[1]))
    P = Precios()
    inicios, fin, racha = calendario()
    mans = {m["user_id"]: m for m in ri["managers"] if m["user_id"] in NOM}
    R = {u: analiza(mans[u], P, inicios, fin, racha) for u in NOM}

    print(f"rival_intelligence generado {ri['generated_at']}; caja: {ri['cash_check']['reason']}")
    print("\n== 1) De donde sale el patrimonio (desde 23,3 M) ==")
    print(f"{'':12}{'patrimonio':>12}{'ganancia':>11}{'viajes':>10}{'latente':>10}"
          f"{'premios':>10}{'regalo':>10}{'resto':>8}")
    for u, r in R.items():
        print(f"{r['nombre']:12}{mans[u]['net_worth'] / 1e6:>11.2f} {M(r['ganancia']):>10} "
              f"{M(r['realizado']):>9} {M(r['latente']):>9} {M(r['premios']):>9} {M(r['regalo']):>9}"
              f" {M(r['resto']):>7}")
        print(f"{'':12}  cuadre movs vs caja: ventas {r['cuadre_ventas']:+,} compras {r['cuadre_compras']:+,};"
              f" jornadas {M(r['jornadas'])} racha {M(r['racha'])}; regalo: {r['n_regaladas_vendidas']}"
              f" vendidas + en casa {r['sin_lote']}; compras huerfanas {r['huerfanas']}")
        print(f"{'':12}  latente: valor {r['lat_valor'] / 1e6:.2f} M sobre coste {r['lat_coste'] / 1e6:.2f} M")

    print("\n== 2) Los viajes cerrados ==")
    for u, r in R.items():
        v = r["viajes"]
        if not v:
            continue
        cortos = [x for x in v if x["dias"] <= 21]
        print(f"\n{r['nombre']}: {len(v)} viajes, P&L {M(sum(x['pl'] for x in v))}, verdes "
              f"{sum(x['pl'] > 0 for x in v)}/{len(v)}; mediana {med([x['dias'] for x in v]):.1f} dias,"
              f" P&L mediano {M(med([x['pl'] for x in v]))}, ROI mediano {pc(med([x['roi'] for x in v]))}")
        print(f"   compra mediana {M(med([x['compra'] for x in v]))};"
              f" de Computer {sum(x['de_computer'] for x in v)}, a Computer {sum(x['a_computer'] for x in v)}")
        for nombre, f in (("<=1 M", lambda x: x["compra"] <= 1e6), ("1-3 M", lambda x: 1e6 < x["compra"] <= 3e6),
                          ("3-6 M", lambda x: 3e6 < x["compra"] <= 6e6), (">6 M", lambda x: x["compra"] > 6e6)):
            s = [x for x in v if f(x)]
            if s:
                print(f"   tramo {nombre:6} n={len(s):3} P&L {M(sum(x['pl'] for x in s))} verde "
                      f"{sum(x['pl'] > 0 for x in s)}/{len(s)} ROI med {pc(med([x['roi'] for x in s]))}")
        sub = [x for x in v if x["subia"] is not None]
        print(f"   subia el dia antes de comprar: {sum(x['subia'] for x in sub)}/{len(sub)}"
              f"  (P&L subiendo {M(sum(x['pl'] for x in sub if x['subia']))}, no {M(sum(x['pl'] for x in sub if not x['subia']))})")
        print(f"   prima compra mediana {pc(med([x['prima_compra'] for x in v]))};"
              f" prima venta mediana {pc(med([x['prima_venta'] for x in v if x['a_computer']]))}")
        db = [x for x in v if x["dia_bajada"] is not None and x["a_computer"]]
        pb = [x for x in v if x["primera_bajada"] is not None and x["a_computer"]]
        print(f"   venta a Computer en dia de bajada {sum(x['dia_bajada'] for x in db)}/{len(db)};"
              f" en la PRIMERA bajada desde la compra {sum(x['primera_bajada'] for x in pb)}/{len(pb)}")
        aj = [x for x in v if x["antes_jornada"]]
        na = [x for x in v if not x["antes_jornada"]]
        print(f"   vendidos en las 24 h antes de una jornada: n={len(aj)} ROI med {pc(med([x['roi'] for x in aj]))}"
              f" verdes {sum(x['pl'] > 0 for x in aj)}/{len(aj)}; resto n={len(na)} ROI med {pc(med([x['roi'] for x in na]))}")
        print(f"   viajes <=21 dias: n={len(cortos)} P&L {M(sum(x['pl'] for x in cortos))};"
              f" >21 dias: n={len(v) - len(cortos)} P&L {M(sum(x['pl'] for x in v if x['dias'] > 21))}")
        for mes in (8, 9, 10):
            s = [x for x in v if x["mes"] == mes]
            if s:
                print(f"   cerrados en mes {mes:2}: n={len(s):3} P&L {M(sum(x['pl'] for x in s))}")
        mejores = sorted(v, key=lambda x: -x["pl"])[:3]
        peores = sorted(v, key=lambda x: x["pl"])[:3]
        print("   mejores:", "; ".join(f"{x['jugador']} {M(x['pl'])} {x['dias']:.0f}d" for x in mejores))
        print("   peores: ", "; ".join(f"{x['jugador']} {M(x['pl'])} {x['dias']:.0f}d" for x in peores))
        print("   usuario a usuario:", r["u2u"])

    print("\n== 3) Plantilla: tamano, almacen, revalorizacion ==")
    for u, r in R.items():
        sn = r["serie_n"]
        hitos = [dt.date(2026, 8, 20), dt.date(2026, 9, 1), dt.date(2026, 9, 15), dt.date(2026, 10, 1), HOY]
        txt = []
        for h in hitos:
            ks = [k for k in sn if k <= h]
            txt.append(f"{h.strftime('%d/%m')}:{sn[max(ks)] if ks else r['n_inicial']}")
        print(f"\n{r['nombre']}: plantilla inicial {r['n_inicial']}; " + "  ".join(txt))
        print(f"   hoy {len(mans[u]['roster'])} fichas, valor {r['valor'] / 1e6:.2f} M (once {r['once_valor'] / 1e6:.2f} M),"
              f" price_increment de hoy {M(r['inc_hoy'])}")
        a = r["alm"]
        print(f"   fuera del mejor once (almacen): {len(a)} fichas, {sum(x[1] for x in a) / 1e6:.2f} M,"
              f" incremento de hoy {M(sum(x[2] for x in a))}, latente {M(sum(x[4] for x in a))}")
        for x in a:
            print(f"      {x[0]:22} {x[1] / 1e6:6.2f} M  hoy {x[2] / 1e3:+6.0f} k  {x[3]} pts  latente {M(x[4])}")
        print("   latente por jugador (once=*):", "; ".join(
            f"{n}{'*' if o else ''} {M(l)}" for n, v, l, o in r["latente_por_jugador"] if abs(l) >= 4e5))
        rd = revalorizacion_diaria(mans[u], P, mans[u]["transactions"])
        for a0, b0 in ((dt.date(2026, 8, 17), dt.date(2026, 9, 6)), (dt.date(2026, 9, 9), dt.date(2026, 10, 8)),
                       (dt.date(2026, 9, 24), dt.date(2026, 10, 8)), (dt.date(2026, 8, 17), dt.date(2026, 10, 8))):
            ds = [d for d in rd if a0 <= d <= b0 and rd[d][1] > 0]
            g = [rd[d][0] for d in ds]
            cub = sum(rd[d][1] for d in ds) / max(1, sum(rd[d][2] for d in ds))
            if g:
                print(f"   {a0.strftime('%d/%m')}-{b0.strftime('%d/%m')}: revalorizacion media {M(st.mean(g))}/dia"
                      f" (mediana {M(st.median(g))}; {len(g)} dias con precio; jugador-dias con precio {cub:.0%})"
                      f" -> {M(st.mean(g) * 7)}/semana")

    print("\n== 4) Deuda ==")
    for u, r in R.items():
        cm, ts = r["caja_minima"]
        print(f"\n{r['nombre']}: caja hoy reconstruida {M(r['caja_final'])} (oficial {M(mans[u]['balance'])});"
              f" minima {M(cm)} el {dt.datetime.utcfromtimestamp(ts) if ts else '-'};"
              f" dias con saldo < 0: {r['dias_en_rojo']}/{r['dias_total']}")
        print("   saldo al empezar cada jornada:", "; ".join(f"{n} ({d}) {M(c)}" for n, d, c in r["al_inicio"]))
        print("   24 h antes de cada jornada: ventas (n, importe) y peor saldo de los 4 dias previos:")
        for n, k, imp, peor in r["liquidacion"]:
            print(f"      {n:22} {k:2} ventas {M(imp)}   peor saldo previo {M(peor)}")
        print(f"   maximumBid hoy {M(mans[u]['maximum_bid'])}")


if __name__ == "__main__":
    main()
