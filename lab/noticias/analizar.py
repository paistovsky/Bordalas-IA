"""Laboratorio, agenda 6: ¿las noticias de FutbolFantasy se adelantan al precio?

Lee lab/noticias/archivo.jsonl (archivar.py), data/autopilot/price_history.json
y la foto del 18/09 (jugadores, equipo). Clasifica titulares en BAJA / VUELTA /
TITULARIDAD, los asigna a jugadores (solo coincidencias sin ambiguedad) y mide
el camino del precio alrededor de la noticia.

Convenciones:
  - precio del dia d = ultima muestra del dia UTC d (el cambio de Biwenger es
    a las ~07:00 de Madrid = 05:00 UTC, asi que p[d] ya lleva el cambio de d).
  - E = primer cambio de precio DESPUES de publicarse la noticia (si sale
    antes de las 05:00 UTC del dia d, E=d; si no, E=d+1).
  - base = p[E-1] = el precio al que se compra/vende al leer la noticia.
  - cambio k = p[E+k]/p[E+k-1]-1; k=0 es el primer cambio tras la noticia.
  - r3 = p[E+2]/base-1 (tres cambios), r7 = p[E+6]/base-1.
  - referencia: todos los jugadores ese mismo E con el MISMO sentido en el
    cambio k=-1 (sube / quieto / baja), para descontar la inercia (E1).

Uso: python3 lab/noticias/analizar.py  (escribe lab/noticias/eventos.jsonl)
"""
import datetime as dt
import json
import re
import statistics as st
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = RAIZ / "lab/noticias"
D = dt.timedelta(days=1)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)


# ---------------------------------------------------------------- precios
def cargar_precios():
    P = json.load(open(RAIZ / "data/autopilot/price_history.json"))["players"]
    out = {}
    for pid, s in P.items():
        d = {}
        for t, p in sorted(zip(s["t"], s["p"])):
            d[dt.datetime.utcfromtimestamp(t).date()] = p
        out[int(pid)] = d
    return out


# ---------------------------------------------------------------- jugadores
def cargar_jugadores():
    f = json.load(open(RAIZ / "data/fotos/2026-09-18.json"))["todaLaLiga"]["players"]
    f = [p for p in f if p["position"] in (1, 2, 3, 4)]  # fuera entrenadores
    return {p["id"]: {"name": p["name"], "team_id": p.get("team_id"),
                      "position": p["position"], "price": p.get("price")} for p in f}


# ---------------------------------------------------------------- clasificar
TRASPASO = re.compile(r"traspaso|fichaje|ficha por|cesion|cedido|oficial(mente)?|nuevo jugador|"
                      r"acuerdo|oferta|va a por|mercado|salida|negocia|renueva|renovacion|contrato|clausula|desconvoca|seleccion|"
                      r"convocatoria de|sub 2|sub 1|internacional")
BAJA = re.compile(r"\bsin (recuperar|poder contar|contar con)?\b|lesion|\bbaja|rotura|se pierde|"
                  r"se perdera|enfermeria|no entrena|al margen|molestias|tocado|parte medico|"
                  r"retirad|operad|intervenid|sufre|descart|duda|dudas|en el aire|no estara|"
                  r"no viaja|no recibe|no llega|fuera de la lista|sigue(n)? sin|continua(n)? sin|trabajo especifico|"
                  r"trabaja(n)? al margen|en solitario|recuperacion|pendiente de|esguince|sobrecarga")
VUELTA = re.compile(r"recuperad|\brecupera\b|\brecuperan\b|vuelve|vuelven|regres|\balta\b|con el grupo|"
                    r"disponible|incorpora|reaparece|pisa(n)? cesped|se ejercita|completa(n)? la sesion|"
                    r"entra(n)? en la lista|convocad|ya entrena|buenas noticias|apto")
TITUL = re.compile(r"titular|\bonce\b|rotacion|rotaciones|suplencia|banquillo|alineacion|"
                   r"suplente|sale de inicio|gana(r)? el puesto|pierde el puesto|revolucion")


def tipo_clausula(c):
    if TITUL.search(c) and not (BAJA.search(c) or VUELTA.search(c)):
        return "TITULARIDAD"
    b, v = BAJA.search(c), VUELTA.search(c)
    if re.search(r"duda(s)? entre|entre .* o ", c) and not re.search(r"lesion|molestias", c):
        return "TITULARIDAD"
    if re.search(r"no (ira|iran|entra|entran|estara|estaran) convocad|trabajo individual|gimnasio|no recibe|sin recuperar|sigue(n)? sin|continua(n)? sin|sigue(n)? al margen|"
                 r"continua(n)? (con su|en) recuperacion", c):
        return "BAJA"
    if v and not b:
        return "VUELTA"
    if b and not v:
        return "BAJA"
    if b and v:
        return "MIXTA"
    return None


# ---------------------------------------------------------------- asignar
def indice_nombres(jug):
    """Claves de busqueda: nombre completo y apellido (ultima palabra >3 letras)."""
    completo, apellido = defaultdict(set), defaultdict(set)
    for pid, j in jug.items():
        n = norm(j["name"]).split()
        if not n:
            continue
        completo[" ".join(n)].add(pid)
        for w in n:
            if len(w) >= 4:
                apellido[w].add(pid)
    return completo, apellido


PALABRAS_COMUNES = {"real", "sevilla", "betis", "celta", "villarreal", "valencia", "getafe",
                    "girona", "levante", "elche", "osasuna", "athletic", "atletico", "madrid",
                    "barcelona", "alaves", "espanyol", "mallorca", "oviedo", "rayo", "sociedad",
                    "vuelve", "grupo", "sesion", "lista", "baja", "bajas", "entrenamiento",
                    "martes", "lunes", "jueves", "viernes", "sabado", "domingo", "miercoles",
                    "david", "pablo", "carlos", "sergio", "javi", "alex", "jose", "juan", "mario",
                    "diego", "ivan", "dani", "nico", "jorge", "hugo", "alvaro", "raul", "marc",
                    "iago", "luis", "adrian", "victor", "manu", "fran", "antonio", "unai", "jon"}


def emparejar(texto, equipo_ids, completo, apellido, jug):
    """Devuelve [(pid, posicion_en_texto)] sin ambiguedad; y cuantos nombres dudosos."""
    t = " " + norm(texto) + " "
    found, dudosos = {}, 0
    for full, pids in completo.items():
        if len(full.split()) >= 2 and f" {full} " in t:
            cand = pids if not equipo_ids else {p for p in pids if jug[p]["team_id"] in equipo_ids} or pids
            if len(cand) == 1:
                found[next(iter(cand))] = t.index(f" {full} ")
    for w in set(t.split()):
        if w in PALABRAS_COMUNES or w not in apellido:
            continue
        pids = apellido[w]
        if equipo_ids:
            pids = {p for p in pids if jug[p]["team_id"] in equipo_ids}
            if not pids:
                continue
        if len(pids) == 1:
            p = next(iter(pids))
            found.setdefault(p, t.index(f" {w} "))
        else:
            dudosos += 1
    return found, dudosos


def dia_efectivo(publicada):
    t = dt.datetime.fromisoformat(publicada.replace("+0200", "+02:00").replace("+0100", "+01:00"))
    u = t.astimezone(dt.timezone.utc)
    return u.date() if u.hour < 5 else u.date() + D


def main():
    precios = cargar_precios()
    jug = cargar_jugadores()
    completo, apellido = indice_nombres(jug)
    notas = [json.loads(l) for l in open(AQUI / "archivo.jsonl")]
    notas = [n for n in notas if n.get("publicada") and n.get("titulo")]
    notas.sort(key=lambda n: n["publicada"])

    # mapa equipo slug -> team_id, por votos de nombres completos sin ambiguedad
    votos = defaultdict(Counter)
    for n in notas:
        if not n.get("equipo"):
            continue
        f, _ = emparejar(n["titulo"], None, completo, {}, jug)
        for p in f:
            votos[n["equipo"]][jug[p]["team_id"]] += 1
    slug2tid = {s: c.most_common(1)[0][0] for s, c in votos.items() if c and c.most_common(1)[0][1] >= 3}

    eventos, cuenta = [], Counter()
    for n in notas:
        tit = n["titulo"]
        nt = norm(tit)
        cuenta["noticias"] += 1
        if TRASPASO.search(nt):
            cuenta["traspasos/selecciones (fuera)"] += 1
            continue
        if re.search(r"\bhabla\b|\bexplica|\banaliza|entrevista|rueda de prensa|palabras de|atiende a", nt):
            cuenta["ruedas de prensa/entrevistas (fuera)"] += 1
            continue
        tid = slug2tid.get(n.get("equipo"))
        found, dud = emparejar(tit, {tid} if tid else None, completo, apellido, jug)
        cuenta["nombres ambiguos descartados"] += dud
        tipo_global = tipo_clausula(nt)
        if not found:
            if tipo_global:
                cuenta["con palabra clave pero sin jugador"] += 1
            continue
        # segmento de cada jugador: desde su nombre hasta el siguiente nombre;
        # si ese trozo no dice nada ("A, B y C empiezan al margen"), se usa el
        # siguiente trozo que si diga algo
        orden = sorted(found.items(), key=lambda x: x[1])
        cortes = [p for _, p in orden] + [len(" " + nt + " ")]
        tnorm = " " + nt + " "
        segs = [tnorm[cortes[i]:cortes[i + 1]] for i in range(len(orden))]
        for i, (pid, pos) in enumerate(orden):
            tp = None
            for sg in segs[i:]:
                tp = tipo_clausula(sg)
                if tp:
                    break
            antes = tnorm[:pos]
            if re.search(r"\bsin (recuperar a )?[a-z ,]*$| ni [a-z ]*$", antes) and not re.search(r"\bcon\b[^,]*$", antes):
                tp = "BAJA"
            if tp is None and i == 0:
                tp = tipo_global
            if tp in (None, "MIXTA"):
                cuenta["jugador sin tipo claro"] += 1
                continue
            eventos.append({"pid": pid, "name": jug[pid]["name"], "tipo": tp,
                            "publicada": n["publicada"], "E": str(dia_efectivo(n["publicada"])),
                            "titulo": tit, "id": n["id"]})
            cuenta[f"evento {tp}"] += 1

    with open(AQUI / "eventos.jsonl", "w") as fh:
        for e in eventos:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    print("== Archivo y clasificacion ==")
    print("noticias con fecha:", len(notas), notas[0]["publicada"][:10], "->", notas[-1]["publicada"][:10])
    print("equipos mapeados:", len(slug2tid))
    for k, v in cuenta.most_common():
        print(f"  {k}: {v}")

    medir(eventos, precios, jug)


# ---------------------------------------------------------------- medir
def camino(pr, E):
    def p(d):
        return pr.get(E + d * D)
    base = p(-1)
    if not base:
        return None
    ch = {}
    for k in range(-5, 8):
        a, b = p(k), p(k - 1)
        ch[k] = None if (a is None or b is None) else a / b - 1
    r = lambda k: (p(k) / base - 1) if p(k) else None
    pre = (base / p(-6) - 1) if p(-6) else None
    return {"base": base, "ch": ch, "r1": r(0), "r3": r(2), "r7": r(6), "pre5": pre}


def sentido(x):
    if x is None:
        return None
    return 1 if x > 0.0005 else (-1 if x < -0.0005 else 0)


def med(xs):
    xs = [x for x in xs if x is not None]
    return (st.mean(xs), st.median(xs), len(xs)) if xs else (float("nan"), float("nan"), 0)


def medir(eventos, precios, jug):
    # referencia por (E, sentido previo): r1, r3, r7 medios de TODOS los jugadores
    ref = {}
    fechas = sorted({dt.date.fromisoformat(e["E"]) for e in eventos})
    for E in fechas:
        g = defaultdict(lambda: defaultdict(list))
        for pid, pr in precios.items():
            c = camino(pr, E)
            if not c or c["base"] < 500000:
                continue
            s = sentido(c["ch"][-1])
            for key in ("r1", "r3", "r7"):
                if c[key] is not None:
                    g[s][key].append(c[key])
        ref[E] = {s: {k: st.mean(v) for k, v in d.items() if v} for s, d in g.items()}

    # episodios: primera noticia de ese tipo para ese jugador en 7 dias
    ultimo, filas = {}, []
    for e in sorted(eventos, key=lambda e: e["publicada"]):
        E = dt.date.fromisoformat(e["E"])
        key = (e["pid"], e["tipo"])
        if key in ultimo and (E - ultimo[key]).days <= 7:
            ultimo[key] = E
            continue
        ultimo[key] = E
        pr = precios.get(e["pid"])
        if not pr:
            continue
        c = camino(pr, E)
        if not c or c["r1"] is None:
            continue
        s = sentido(c["ch"][-1])
        rf = ref.get(E, {}).get(s, {})
        filas.append({**e, **c, "prev": s,
                      "x1": None if c["r1"] is None or "r1" not in rf else c["r1"] - rf["r1"],
                      "x3": None if c["r3"] is None or "r3" not in rf else c["r3"] - rf["r3"],
                      "x7": None if c["r7"] is None or "r7" not in rf else c["r7"] - rf["r7"]})

    json.dump([{k: v for k, v in f.items() if k != "ch"} | {"ch": {str(k): v for k, v in f["ch"].items()}}
               for f in filas], open(AQUI / "episodios.json", "w"), ensure_ascii=False, default=str, indent=0)

    pc = lambda x: f"{100*x:+.1f} %" if x == x else "  -  "
    for filtro, nom in ((lambda f: True, "todos"), (lambda f: f["base"] >= 1_000_000, "precio >= 1 M")):
        print(f"\n== Episodios ({nom}) ==")
        print("tipo          n   r1 medio  r3 medio (mediana)  r7 medio | exceso vs mismo dia y mismo sentido previo: x1 / x3 / x7")
        for tp in ("BAJA", "VUELTA", "TITULARIDAD"):
            fs = [f for f in filas if f["tipo"] == tp and filtro(f)]
            m1, m3, m7 = med([f["r1"] for f in fs]), med([f["r3"] for f in fs]), med([f["r7"] for f in fs])
            a, b, c = med([f["x1"] for f in fs]), med([f["x3"] for f in fs]), med([f["x7"] for f in fs])
            print(f"{tp:12s} {len(fs):4d}  {pc(m1[0])}  {pc(m3[0])} ({pc(m3[1])})  {pc(m7[0])} | "
                  f"{pc(a[0])} (n={a[2]}) / {pc(b[0])} (n={b[2]}) / {pc(c[0])} (n={c[2]})")

    print("\n== ¿Quien va primero? Sentido del precio en los cambios de -5 a +7 (precio >= 1 M) ==")
    for tp, malo in (("BAJA", -1), ("VUELTA", 1)):
        fs = [f for f in filas if f["tipo"] == tp and f["base"] >= 1_000_000]
        print(f"\n{tp} (n={len(fs)}): % de episodios con el precio {'BAJANDO' if malo < 0 else 'SUBIENDO'} en el cambio k")
        linea = []
        for k in range(-5, 8):
            ss = [sentido(f["ch"][k]) for f in fs if f["ch"][k] is not None]
            linea.append(f"{k:+d}:{100*sum(1 for s in ss if s == malo)/max(1,len(ss)):.0f}%")
        print("  " + "  ".join(linea))
        # giro: el primer k en que el precio va en el sentido de la noticia
        giros = Counter()
        for f in fs:
            prev = sentido(f["ch"][-1])
            if prev == malo:
                # ya iba en ese sentido: buscar desde cuando
                k = -1
                while k - 1 >= -5 and sentido(f["ch"][k - 1]) == malo:
                    k -= 1
                giros[f"antes (desde k={k})" if k > -5 else "antes (desde k<=-5)"] += 1
            else:
                k = next((k for k in range(0, 8) if sentido(f["ch"][k]) == malo), None)
                giros["nunca en 8 cambios" if k is None else f"despues k={k}"] += 1
        tot = sum(giros.values())
        antes = sum(v for k, v in giros.items() if k.startswith("antes"))
        print(f"  precio YA giro antes de la noticia: {antes}/{tot} ({100*antes/max(1,tot):.0f} %)")
        for k, v in sorted(giros.items()):
            print(f"    {k}: {v}")

    # por sentido previo: la parte operable
    print("\n== BAJA segun como venia el precio (precio >= 1 M): lo que ahorra vender al leer ==")
    for s, nom in ((1, "venia subiendo"), (0, "venia quieto"), (-1, "venia bajando")):
        fs = [f for f in filas if f["tipo"] == "BAJA" and f["base"] >= 1_000_000 and f["prev"] == s]
        m1, m3, m7 = med([f["r1"] for f in fs]), med([f["r3"] for f in fs]), med([f["r7"] for f in fs])
        x3 = med([f["x3"] for f in fs])
        print(f"  {nom:15s} n={len(fs):3d}  r1 {pc(m1[0])}  r3 {pc(m3[0])}  r7 {pc(m7[0])}  exceso r3 {pc(x3[0])}")
    print("\n== VUELTA segun como venia el precio (precio >= 1 M): lo que gana comprar al leer ==")
    for s, nom in ((1, "venia subiendo"), (0, "venia quieto"), (-1, "venia bajando")):
        fs = [f for f in filas if f["tipo"] == "VUELTA" and f["base"] >= 1_000_000 and f["prev"] == s]
        m1, m3, m7 = med([f["r1"] for f in fs]), med([f["r3"] for f in fs]), med([f["r7"] for f in fs])
        x3 = med([f["x3"] for f in fs])
        print(f"  {nom:15s} n={len(fs):3d}  r1 {pc(m1[0])}  r3 {pc(m3[0])}  r7 {pc(m7[0])}  exceso r3 {pc(x3[0])}")

    # hora de publicacion
    horas = Counter(int(f["publicada"][11:13]) for f in filas)
    print("\nhora de publicacion (Madrid) de los episodios:", sorted(horas.items()))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- intervalos
def ic(xs, B=2000, seed=7):
    import random
    xs = [x for x in xs if x is not None]
    if len(xs) < 5:
        return None
    rnd = random.Random(seed)
    ms = sorted(st.mean(rnd.choices(xs, k=len(xs))) for _ in range(B))
    return st.mean(xs), ms[int(.05 * B)], ms[int(.95 * B)], len(xs)


FUERTE = re.compile(r"lesion|rotura|parte medico|se pierde|semanas|operad|quirofano|intervenid|"
                    r"esguince|fractura|ligamento|periodo estimado|mes de baja")


def intervalos():
    filas = json.load(open(AQUI / "episodios.json"))
    pc = lambda x: f"{100*x:+.1f} %"
    print("\n== Exceso r3 / r7 con intervalo al 90 % (bootstrap), precio >= 1 M ==")
    grupos = {
        "BAJA todas": lambda f: f["tipo"] == "BAJA",
        "BAJA venia subiendo o quieto": lambda f: f["tipo"] == "BAJA" and f["prev"] in (0, 1),
        "BAJA venia quieto": lambda f: f["tipo"] == "BAJA" and f["prev"] == 0,
        "BAJA fuerte (lesion/rotura/parte)": lambda f: f["tipo"] == "BAJA" and FUERTE.search(norm(f["titulo"])),
        "BAJA fuerte, no venia bajando": lambda f: f["tipo"] == "BAJA" and f["prev"] in (0, 1) and FUERTE.search(norm(f["titulo"])),
        "VUELTA todas": lambda f: f["tipo"] == "VUELTA",
        "VUELTA no venia subiendo": lambda f: f["tipo"] == "VUELTA" and f["prev"] in (0, -1),
        "TITULARIDAD": lambda f: f["tipo"] == "TITULARIDAD",
    }
    for nom, g in grupos.items():
        fs = [f for f in filas if f["base"] >= 1_000_000 and g(f)]
        out = []
        for k in ("r1", "x1", "r3", "x3", "x7"):
            r = ic([f[k] for f in fs])
            out.append(f"{k} {pc(r[0])} [{pc(r[1])}, {pc(r[2])}]" if r else f"{k} -")
        print(f"  {nom:36s} n={len(fs):3d}  " + "  ".join(out))
    # por mitades de tiempo
    print("\n  BAJA por mitades (exceso r3):")
    for nom, g in (("hasta 06/09", lambda f: f["E"] <= "2026-09-06"), ("desde 07/09", lambda f: f["E"] > "2026-09-06")):
        fs = [f for f in filas if f["base"] >= 1_000_000 and f["tipo"] == "BAJA" and g(f)]
        r = ic([f["x3"] for f in fs])
        print(f"    {nom}: {pc(r[0])} [{pc(r[1])}, {pc(r[2])}] n={r[3]}")


if __name__ == "__main__":
    intervalos()
