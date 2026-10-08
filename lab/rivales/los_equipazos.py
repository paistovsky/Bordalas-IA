"""
E25 · 08/10 (pedido como «E13»; ya habia un E13): los equipazos. Pepe contra Pollo17 y
Luismi_Haz: puntos por jornada, el mejor once de cada uno HOY, cuanto
depende de un solo jugador, las plazas del once que no puntuan y que
movimientos protegen el liderato en las 5 jornadas que vienen.

Solo lee data/ y lab/ (nada de src/, nada de red, no escribe nada):
  - tablon (board_events.json): puntos de cada manager por jornada
    (`roundFinished`) y compraventas (`market`/`transfer`).
  - foto del 18/09 16:16 (data/fotos/2026-09-18.json): plantillas y once
    de los 8 (`rival_squads`) y el catalogo de 546 jugadores con
    posicion y dueno (`todaLaLiga`), con los puntos hasta la J6.
  - puntos_por_jornada.jsonl: puntos y partidos de cada jugador al
    cerrar la J7 (acumulado de temporada).
  - price_history.json: precio de hoy.
  - lab/predicciones/j8.json: el once esperado del 07/10 (para contrastar).

Plantilla de HOY = la de la foto del 18/09 + las compraventas del tablon
desde entonces (se comprueba con los recuentos conocidos: 11/20/20).

Vara: «puntos por jornada» = puntos de temporada / 7 jornadas (cuenta
las que no jugo como 0, que es lo que pasa en el once). Tambien se da
puntos por partido jugado (pts/pj), que es lo pedido pero premia al que
juega poco y bien.

Uso:  python3 lab/rivales/los_equipazos.py
"""
import datetime as dt
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PEPE, POLLO, LUISMI = 14175949, 14145555, 14156489
NOM = {PEPE: "Pepe", POLLO: "Pollo17", LUISMI: "Luismi_Haz"}
POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}
FORMACIONES = [(3, 4, 3), (3, 5, 2), (4, 4, 2), (4, 3, 3), (4, 5, 1), (5, 4, 1), (5, 3, 2)]
JORNADAS = 7
PROXIMAS = 5


def cargar():
    foto = json.load(open(RAIZ / "data/fotos/2026-09-18.json"))
    tablon = json.load(open(RAIZ / "data/rival_intelligence/board_events.json"))
    j7 = json.loads(open(RAIZ / "data/intelligence/puntos_por_jornada.jsonl").readline())
    precios = json.load(open(RAIZ / "data/autopilot/price_history.json"))["players"]
    j8 = json.load(open(RAIZ / "lab/predicciones/j8.json"))
    return foto, tablon, j7, precios, j8


# ---------------------------------------------------------------- 1) jornadas
def puntos_por_jornada(tablon):
    """{nombre jornada: {user_id: puntos}}. La parte 2 de una aplazada trae
    el total de la jornada entera (lo confirma la clasificacion: 41+31+61+
    53+61+29+47 = 323), asi que sustituye a la parte 1."""
    out = {}
    for e in tablon:
        if e["type"] != "roundFinished":
            continue
        nombre = e["content"]["round"]["name"].replace(" (aplazada)", "")
        out[nombre] = {x["user"]["id"]: x["points"] for x in e["content"]["results"]}
    return dict(sorted(out.items(), key=lambda kv: int(kv[0].split()[-1])))


# ---------------------------------------------------------------- 2) plantillas
def plantillas_de_hoy(foto, tablon):
    t0 = dt.datetime.fromisoformat(foto["meta"]["generated_at"]) - dt.timedelta(hours=2)  # Madrid -> UTC
    t0 = t0.replace(tzinfo=dt.timezone.utc).timestamp()
    ids = {m["name"]: None for m in foto["rival_squads"]["managers"]}
    for e in tablon:
        for x in (e["content"] if e["type"] in ("market", "transfer") else []):
            for lado in ("to", "from"):
                if x.get(lado):
                    ids[x[lado]["name"]] = x[lado]["id"]
    plant = {ids[m["name"]]: {p["id"] for p in m["players"]} for m in foto["rival_squads"]["managers"]}
    for e in sorted(tablon, key=lambda e: e["date"]):
        if e["date"] <= t0 or e["type"] not in ("market", "transfer"):
            continue
        for x in e["content"]:
            if x.get("from"):
                plant.setdefault(x["from"]["id"], set()).discard(x["player"])
            if x.get("to"):
                plant.setdefault(x["to"]["id"], set()).add(x["player"])
    return plant


def catalogo(foto):
    cat = {p["id"]: dict(name=p["name"], position=p["position"], dueno=p["de_quien"])
           for p in foto["todaLaLiga"]["players"]}
    for m in foto["rival_squads"]["managers"]:
        for p in m["players"]:
            cat.setdefault(p["id"], dict(name=p["name"], position=p["position"], dueno="rival"))
    return cat


def precio_hoy(precios, pid):
    v = precios.get(str(pid))
    return v["p"][-1] if v and v.get("p") else None


def ficha(pid, cat, j7, precios):
    pts, pj, pr = (j7["players"].get(str(pid)) or [0, 0, None])
    c = cat.get(pid, dict(name=f"#{pid}", position=0))
    return dict(id=pid, name=c["name"], position=c["position"], pts=pts, pj=pj,
                pj_j=pts / JORNADAS, ppp=pts / pj if pj else 0.0,
                price=precio_hoy(precios, pid) or pr or 0)


def mejor_once(jugs, clave):
    por = defaultdict(list)
    for j in jugs:
        por[j["position"]].append(j)
    for k in por:
        por[k].sort(key=lambda j: -j[clave])
    mejor = None
    for d, m, dl in FORMACIONES:
        if len(por[1]) < 1 or len(por[2]) < d or len(por[3]) < m or len(por[4]) < dl:
            continue
        xi = por[1][:1] + por[2][:d] + por[3][:m] + por[4][:dl]
        v = sum(j[clave] for j in xi)
        if mejor is None or v > mejor[0]:
            mejor = (v, f"{d}-{m}-{dl}", xi)
    return mejor


# ---------------------------------------------------------------- 3) la J7, plaza a plaza
def j7_plaza_a_plaza(foto, j7, cat):
    """Once guardado en la foto (18/09 16:16, 3 h antes de la J7) y lo que
    hizo cada titular en la J7 (acumulado J7 - acumulado de la foto)."""
    out = {}
    for m in foto["rival_squads"]["managers"]:
        tit = [p for p in m["players"] if p["is_starter"]]
        filas = []
        for p in tit:
            pts7, pj7, _ = j7["players"].get(str(p["id"]), [p["points"], 0, 0])
            # los partidos jugados de la foto no estan; se usa el catalogo
            pj6 = next((c["played"] for c in foto["todaLaLiga"]["players"] if c["id"] == p["id"]), None)
            jugo = None if pj6 is None else pj7 > pj6
            filas.append(dict(name=p["name"], position=p["position"], pts=pts7 - p["points"], jugo=jugo))
        out[m["name"]] = (m["formation"], filas)
    return out


def main():
    foto, tablon, j7, precios, j8 = cargar()
    cat = catalogo(foto)

    print("=" * 78)
    print("1) PUNTOS POR JORNADA (tablon, roundFinished)")
    pj = puntos_por_jornada(tablon)
    series = {u: [] for u in NOM}
    print(f"   {'':<10}" + "".join(f"{k.split()[-1]:>6}" for k in pj) + "   total  media  desv")
    for u in NOM:
        for k, r in pj.items():
            series[u].append(r.get(u, 0))
    # Luismi: la J6 se le anulo (saldo negativo); el tablon dice 64 y la
    # clasificacion le suma 0 (180 -> 226 -> 287).
    oficial = dict(series)
    oficial[LUISMI] = [0 if k == "Jornada 6" else v for k, v in zip(pj, series[LUISMI])]
    for u in NOM:
        s = oficial[u]
        print(f"   {NOM[u]:<10}" + "".join(f"{v:>6}" for v in s)
              + f"  {sum(s):>6} {st.mean(s):>6.1f} {st.pstdev(s):>5.1f}")
    s = series[LUISMI]
    print(f"   {'Luismi*':<10}" + "".join(f"{v:>6}" for v in s)
          + f"  {sum(s):>6} {st.mean(s):>6.1f} {st.pstdev(s):>5.1f}   (*con los 64 anulados de la J6)")
    for u in (POLLO, LUISMI):
        g = sum(a > b for a, b in zip(series[PEPE], series[u]))
        e = sum(a == b for a, b in zip(series[PEPE], series[u]))
        print(f"   Pepe gana a {NOM[u]} en {g} de 7 jornadas (empata {e});"
              f" ultimas 3: Pepe {sum(series[PEPE][-3:])} - {NOM[u]} {sum(series[u][-3:])}")

    print("\n" + "=" * 78)
    print("2) PLANTILLA Y MEJOR ONCE DE HOY (foto 18/09 + tablon hasta el 07/10)")
    plant = plantillas_de_hoy(foto, tablon)
    onces = {}
    for u in NOM:
        jugs = [ficha(p, cat, j7, precios) for p in plant[u]]
        valor = sum(j["price"] for j in jugs) / 1e6
        print(f"\n   {NOM[u]}: {len(jugs)} jugadores, {valor:.1f} M a precio de hoy")
        for clave, rotulo in (("pj_j", "pts/jornada (pts/7)"), ("ppp", "pts/partido jugado")):
            v, form, xi = mejor_once(jugs, clave)
            print(f"     mejor once por {rotulo:<22}: {v:5.1f}  ({form})")
            if clave == "pj_j":
                onces[u] = (v, form, xi, jugs)
        v, form, xi, jugs = onces[u]
        top = max(xi, key=lambda j: j["pj_j"])
        dos = sorted(xi, key=lambda j: -j["pj_j"])[:2]
        print(f"     el mejor del once: {top['name']} {top['pj_j']:.1f}/j = {100 * top['pj_j'] / v:.0f} % del once;"
              f" los dos mejores: {100 * sum(j['pj_j'] for j in dos) / v:.0f} %")
        print(f"     once sin su mejor (entra el siguiente de su puesto): ", end="")
        resto = [j for j in jugs if j["id"] != top["id"]]
        mo = mejor_once(resto, "pj_j")
        print(f"{mo[0]:.1f} ({mo[0] - v:+.1f})" if mo else "SIN ONCE VALIDO")
        for p in (1, 2, 3, 4):
            linea = [j for j in xi if j["position"] == p]
            print(f"       {POS[p]}: " + ", ".join(f"{j['name']} {j['pj_j']:.1f} ({j['pj']}pj, {j['price']/1e6:.1f}M)"
                                             for j in sorted(linea, key=lambda j: -j['pj_j'])))
        banco = sorted((j for j in jugs if j not in xi), key=lambda j: -j["pj_j"])
        print(f"     banquillo ({len(banco)}): " + ", ".join(f"{j['name']} {POS.get(j['position'], '?')} {j['pj_j']:.1f}"
                                                         for j in banco[:6]))

    print("\n   Linea a linea, media por plaza (pts/7):")
    print(f"   {'':<6}" + "".join(f"{NOM[u]:>12}" for u in NOM))
    for p in (1, 2, 3, 4):
        fila = []
        for u in NOM:
            xi = onces[u][2]
            linea = [j["pj_j"] for j in xi if j["position"] == p]
            fila.append(f"{st.mean(linea):>8.1f} x{len(linea)}")
        print(f"   {POS[p]:<6}" + "".join(f"{x:>12}" for x in fila))

    print("\n   Contraste con el once esperado del 07/10 (j8.json, pts/partido x titularidad FF):")
    for u, n in ((PEPE, "Pepe Bordalás"), (POLLO, "Pollo17"), (LUISMI, "Luismi_Haz")):
        m = j8["managers"][n]
        fuera = [cat.get(p, {}).get("name", p) for p in m["once"] if p not in plant[u]]
        print(f"     {NOM[u]:<10} {m['once_esperado']:5.1f} ({m['formacion']}); ya no son suyos: {fuera or 'ninguno'}")

    print("\n" + "=" * 78)
    print("3) LA J7 PLAZA A PLAZA (once de la foto del 18/09, 3 h antes de empezar)")
    clas = {NOM[u]: oficial[u][-1] for u in NOM}
    for nombre, (form, filas) in j7_plaza_a_plaza(foto, j7, cat).items():
        if nombre not in ("Pepe Bordalás", "Pollo17", "Luismi_Haz"):
            continue
        corto = "Pepe" if nombre.startswith("Pepe") else nombre
        no = [f["name"] for f in filas if f["jugo"] is False]
        suma = sum(f["pts"] for f in filas)
        por = defaultdict(int)
        for f in filas:
            por[POS[f["position"]]] += f["pts"]
        print(f"   {corto:<10} {form}: {len(filas)} titulares (vacias {11 - len(filas)}),"
              f" no jugaron {len(no)} {no}; suma {suma} (tablon {clas[corto]})  {dict(por)}")

    print("\n" + "=" * 78)
    print("4) FICHAJES: LIBRES DE HOY (sin dueno entre los 8), por puesto")
    estado = estados()
    con_dueno = set().union(*plant.values())
    libres = [ficha(pid, cat, j7, precios) for pid in cat if pid not in con_dueno]
    libres = [j for j in libres if j["pj"] >= 5 and j["price"] and estado.get(j["id"], "ok") in ("ok", "doubt")]
    fuera = [cat[pid]["name"] for pid in cat if pid not in con_dueno and estado.get(pid) in MALOS
             and (j7["players"].get(str(pid)) or [0])[0] / JORNADAS >= 7]
    print(f"   (fuera por estado {MALOS} el 29/09, de los de 7+/j: {fuera})")
    xi_pepe = onces[PEPE][2]
    for p in (1, 2, 3, 4):
        peor = min((j for j in xi_pepe if j["position"] == p), key=lambda j: j["pj_j"])
        mejores = sorted((j for j in libres if j["position"] == p and j["pj_j"] > peor["pj_j"] + 1),
                         key=lambda j: -(j["pj_j"] - peor["pj_j"]) / max(j["price"] / 1e6, 0.3))[:6]
        print(f"   {POS[p]}: el peor de Pepe {peor['name']} {peor['pj_j']:.1f}/j ({peor['price']/1e6:.1f} M)")
        for j in mejores:
            gana = j["pj_j"] - peor["pj_j"]
            print(f"      {j['name']:<20} {j['pj_j']:4.1f}/j ({j['pj']}pj, {estado.get(j['id'], '?')}) {j['price']/1e6:5.2f} M"
                  f"  +{gana:.1f}/j = +{gana * PROXIMAS:.0f} en {PROXIMAS} j; {gana / (j['price'] / 1e6):.2f} pts/j por M")

    print(f"\n   PERMUTAS 1 x 1 (vender al Computer a precio x {1 + PRIMA_COMPUTER} + caja {CAJA / 1e6} M,"
          f" comprar uno libre del mismo puesto al precio de hoy):")
    for j in sorted(xi_pepe, key=lambda j: (j["position"], j["pj_j"])):
        tope = j["price"] * (1 + PRIMA_COMPUTER) + CAJA
        cand = sorted((c for c in libres if c["position"] == j["position"] and c["price"] <= tope
                       and c["pj_j"] > j["pj_j"] + 1), key=lambda c: -c["pj_j"])[:3]
        if cand:
            print(f"     {j['name']:<18} {j['pj_j']:4.1f}/j, tope {tope / 1e6:5.2f} M -> " + "; ".join(
                f"{c['name']} {c['pj_j']:.1f}/j {c['price'] / 1e6:.2f} M (+{(c['pj_j'] - j['pj_j']) * PROXIMAS:.0f} en {PROXIMAS} j)"
                for c in cand))

    print("\n   SUPLENTE: defensas libres que juegan (6+ de 7) por menos de 1,5 M:")
    banco = sorted((c for c in libres if c["position"] == 2 and c["pj"] >= 6 and c["price"] <= 1.5e6),
                   key=lambda c: c["price"])[:8]
    print("     " + "; ".join(f"{c['name']} {c['price'] / 1e6:.2f} M {c['pj_j']:.1f}/j" for c in banco))


MALOS = ("injured", "sanctioned", "discarded")
PRIMA_COMPUTER = 0.024   # E1: mediana de lo que paga el Computer sobre el precio
CAJA = 400_000           # saldo del 08/10 segun el dueno


def estados():
    """Estado de Biwenger del ultimo ciclo archivado (29/09 15:09 UTC): el mas reciente
    para TODOS los jugadores que hay en git. Nueve dias de antiguedad."""
    c = json.load(open(RAIZ / "lab/noticias/ciclos_27_29_09.json"))
    return {int(k): v[0] for k, v in c[sorted(c)[-1]]["jugadores"].items()}

if __name__ == "__main__":
    main()
