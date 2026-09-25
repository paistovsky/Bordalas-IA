"""
El censo de las puertas: donde muere cada candidato del mercado.

QUE MIDE

    BLOQUE 1   el censo. Cada candidato del mercado del Computer
               de los dias con foto, en UNA puerta: la primera que
               lo corta en el orden en que corre el codigo. Y los
               de los rivales aparte, que tienen la puerta cerrada
               por orden del dueño.
    BLOQUE 2   la regla 2 (`PRECIO_CAYENDO`): cuantos corta, con
               que ritmo, si lee el pulso y, sobre todo, que haria
               con ellos la puerta siguiente si la regla no
               existiera. Con `optimal_bid` de produccion, no con
               una copia.
    BLOQUE 3   el contrafactual contra la alternativa buena: los
               del MISMO mercado y el MISMO dia a los que la
               compuerta deja pasar. A 3, 7 y 14 dias en precio,
               en puntos hasta el paron, y en euros.

EL ORDEN DE LAS PUERTAS, Y POR QUE NO ES UNA FILA

    1. `value_candidate` (acquisition_valuation.py:356). Precio
       invalido, y despues CINCO VIAS EN PARALELO -mejora del once,
       relleno de ficha, especulacion, reventa al Computer, tener-
       de las que gana la mayor. El candidato solo muere aqui si
       mueren todas (`SIN_VALOR`, :1157-1194).

       Por eso aqui no se puede contar "la primera que corta": una
       via cortada no mata a nadie si otra da valor. Se cuenta LA
       DECISIVA: si con la compuerta de ritmo abierta el candidato
       habria tenido valor (`market_gate.value_before > 0`), le
       mato la compuerta; si ni asi, le mato la valoracion entera,
       y se dice que decia la via del once.

    2. La cadena del tablero (acquisition_board.py:1049-1085):
       contraoferta nuestra, puja nuestra fuera del Computer, estado
       del jugador.

    3. `optimal_bid` (rival_bid_model.py:1117): NO_COMPENSA,
       SUPERA_PRESUPUESTO, SIN_MARGEN, EV_NEGATIVO, RENDIMIENTO_INSUFICIENTE,
       GANANCIA_INSUFICIENTE, PROBABILIDAD_INSUFICIENTE.

    4. Lo que pasa: BID.

QUE LIBROS LEE

    data/fotos/*.json, diagnostico/status.json y
    dashboard/data/status.json               las fotos del tablero
    data/intelligence/libro_en_la_sombra.jsonl  los cortes de la compuerta
    data/intelligence/divergence_ledger.json    el ritmo de cada jugador y dia
    data/autopilot/price_history.json           el precio a N dias
    data/trading/libro_del_escaparate.jsonl     el mercado del Computer, 17/09+
    data/snapshot_*.json                        el mercado y los puntos, antes
    data/intelligence/puntos_por_jornada.jsonl  los puntos tras la J7

    Con `--rev REV` los libros versionados se leen de esa revision.
    Las fotos locales y los catalogos se leen del disco.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende nada
    y NO ESCRIBE NI UNA LINEA DE NINGUN LIBRO.

USO

    python scripts/el_censo_de_las_puertas.py --rev HEAD > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import argparse
import bisect
import glob
import json
import os
import random
import statistics
import subprocess
import sys

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone


sys.path.insert(0, os.getcwd())

from src.analysis.rival_bid_model import (                    # noqa: E402
    RENDIMIENTO_MINIMO_DEL_CAPITAL,
    optimal_bid,
)


SOMBRA = "data/intelligence/libro_en_la_sombra.jsonl"
DIVERGENCIA = "data/intelligence/divergence_ledger.json"
PRECIOS = "data/autopilot/price_history.json"
ESCAPARATE = "data/trading/libro_del_escaparate.jsonl"
PUNTOS_J7 = "data/intelligence/puntos_por_jornada.jsonl"

FOTOS_LOCALES = ("diagnostico/status.json", "dashboard/data/status.json")

PLAZOS = (3, 7, 14)

# El reset del Computer, en UTC. Lo que se ve antes es el mercado
# del dia anterior.
HORA_DEL_RESET_UTC = 5

VETOS_DEL_ONCE = (
    "NO_MEJORA_TITULARIDAD",
    "NO_MEJORA_JERARQUIA",
    "SIN_PRONOSTICO",
    "SIN_REFERENCIA",
)


def leer(ruta, rev):
    if rev is None or not ruta.startswith("data/"):
        with open(ruta, encoding="utf-8-sig") as fichero:
            return fichero.read()
    salida = subprocess.run(
        ["git", "show", f"{rev}:{ruta}"], capture_output=True, check=True
    )
    return salida.stdout.decode("utf-8-sig")


def leer_json(ruta, rev):
    return json.loads(leer(ruta, rev))


def leer_jsonl(ruta, rev):
    return [json.loads(x) for x in leer(ruta, rev).splitlines() if x.strip()]


def momento(marca) -> datetime:
    m = datetime.fromisoformat(str(marca).replace("Z", "+00:00"))
    return m if m.tzinfo else m.replace(tzinfo=timezone.utc)


def dia_de_mercado(cuando: datetime) -> str:
    return (cuando - timedelta(hours=HORA_DEL_RESET_UTC)).date().isoformat()


def safe_int(v, d=0):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return d


def pct(a, b):
    return f"{100 * a / b:5.1f} %" if b else "   -   "


def mediana(v):
    return round(statistics.median(v), 2) if v else None


def euros(x) -> str:
    return f"{x:+,.0f}".replace(",", ".")


# ============================================================
# LAS FOTOS
# ============================================================


def las_fotos(rev):
    """`{fecha: foto}`, una por dia, la versionada manda."""

    rutas = []
    try:
        salida = subprocess.run(
            ["git", "ls-tree", "--name-only", rev or "HEAD", "data/fotos/"],
            capture_output=True, check=True,
        ).stdout.decode()
        rutas += [r for r in salida.split() if r.endswith(".json")]
    except Exception:                               # noqa: BLE001
        rutas += glob.glob("data/fotos/*.json")

    fotos = {}
    for ruta in rutas + list(FOTOS_LOCALES):
        try:
            foto = leer_json(ruta.replace("\\", "/"), rev)
        except Exception:                           # noqa: BLE001
            continue
        hecha = (foto.get("meta") or {}).get("generated_at")
        if not hecha or not (foto.get("acquisition") or {}).get("targets"):
            continue
        fotos.setdefault(hecha[:10], (ruta, foto))
    return dict(sorted(fotos.items()))


# ============================================================
# BLOQUE 1 — EL CENSO
# ============================================================


PUERTAS = (
    ("RIVAL", "de un rival: la compra esta cerrada por orden del dueño",
     "acquisition_board.py:1452"),
    ("PRECIO_INVALIDO", "sin precio valido", "acquisition_valuation.py:383"),
    ("COMPUERTA:SIN_RITMO_OBSERVADO", "regla 1: sin ritmo del ojeador",
     "market_rate_gate.py:202"),
    ("COMPUERTA:PRECIO_CAYENDO", "regla 2: precio que baja o quieto",
     "market_rate_gate.py:233-254"),
    ("COMPUERTA:RACHA_SIN_DEMANDA", "regla 3: racha con el pulso en contra",
     "market_rate_gate.py:258-282"),
    ("VALORACION", "ninguna via da valor ni con la compuerta abierta",
     "acquisition_valuation.py:1157-1194"),
    ("CONTRAOFERTA", "es nuestro y se lo pedimos a un rival",
     "acquisition_board.py:1051"),
    ("PUJA_FUERA_DEL_COMPUTER", "puja nuestra viva fuera del Computer",
     "acquisition_board.py:1075"),
    ("NO_DISPONIBLE", "lesion, sancion o duda", "acquisition_board.py:1085"),
    ("NO_COMPENSA", "vale menos que su precio", "rival_bid_model.py:1164"),
    ("SUPERA_PRESUPUESTO", "no cabe en el bolsillo", "rival_bid_model.py:1178"),
    ("SIN_MARGEN", "ningun importe entre precio y valor", "rival_bid_model.py:1264"),
    ("EV_NEGATIVO", "ninguna puja con valor esperado", "rival_bid_model.py:1276"),
    ("RENDIMIENTO_INSUFICIENTE", "especulacion que rinde menos del 3 %",
     "rival_bid_model.py:1300"),
    ("GANANCIA_INSUFICIENTE", "especulacion que deja menos de 25.000 EUR",
     "rival_bid_model.py:1321"),
    ("PROBABILIDAD_INSUFICIENTE", "gana menos del 15 % de las veces",
     "rival_bid_model.py:1336"),
    ("BID", "PASA TODAS: pujable", "—"),
)


def la_puerta(fila: dict) -> str:
    """Donde murio este candidato, en el orden en que corre el codigo."""

    if fila.get("seller_id") is not None or fila.get("rival_market"):
        return "RIVAL"

    decision = str(fila.get("decision") or "")

    if decision == "PRECIO_INVALIDO":
        return decision

    compuerta = fila.get("market_gate") or {}
    puerta = compuerta.get("gate")
    antes = safe_int(compuerta.get("value_before"))
    valor = safe_int(fila.get("our_value"))

    # LA VALORACION VA PRIMERO. Si hoy no vale nada por ninguna via,
    # la decision del tablero puede decir NO_DISPONIBLE -la cadena
    # `elif` la pisa-, pero el candidato ya habia muerto antes.
    if valor <= 0:
        if puerta not in (None, "RITMO_OBSERVADO") and antes > 0:
            return f"COMPUERTA:{puerta}"
        return "VALORACION"

    if decision in ("CONTRAOFERTA", "PUJA_FUERA_DEL_COMPUTER", "NO_DISPONIBLE"):
        return decision

    return decision or "VALORACION"


def bloque_1(fotos):

    print("=" * 76)
    print("BLOQUE 1 — EL CENSO DE LAS PUERTAS")
    print("=" * 76)

    todos = []
    for dia, (ruta, foto) in fotos.items():
        a = foto["acquisition"]
        filas = a["targets"]
        print(f"  foto {dia} ({ruta}): {len(filas)} filas, "
              f"market_size {a.get('market_size')}, biddable {a.get('biddable')}")
        for f in filas:
            todos.append((dia, f, la_puerta(f)))

    computer = [(d, f, p) for d, f, p in todos if p != "RIVAL"]
    rivales = [(d, f, p) for d, f, p in todos if p == "RIVAL"]

    print(f"\n  MERCADO DEL COMPUTER: {len(computer)} candidatos en {len(fotos)} dias")
    cuenta = Counter(p for _, _, p in computer)
    for codigo, que, linea in PUERTAS:
        if codigo == "RIVAL":
            continue
        n = cuenta.get(codigo, 0)
        ejemplo = next(
            (f"{f['name']} ({d[5:]})" for d, f, p in computer if p == codigo), ""
        )
        print(f"    {codigo:31s} {linea:34s} {n:3d}  {pct(n, len(computer))}  {ejemplo}")
    otros = set(cuenta) - {c for c, _, _ in PUERTAS}
    for codigo in sorted(otros):
        print(f"    {codigo:31s} {'?':34s} {cuenta[codigo]:3d}  {pct(cuenta[codigo], len(computer))}")
    print(f"    {'TOTAL':31s} {'':34s} {sum(cuenta.values()):3d}")

    print("\n  LOS QUE MUEREN EN LA VALORACION, POR LO QUE DECIA LA VIA DEL ONCE:")
    v = Counter(
        (p, f.get("xi_decision") or "sin via del once")
        for _, f, p in computer
        if p == "VALORACION" or p.startswith("COMPUERTA")
    )
    for (p, xi), n in sorted(v.items(), key=lambda x: -x[1]):
        veto = "  <- regla del once" if xi in VETOS_DEL_ONCE else ""
        print(f"    {p:31s} via del once: {xi:24s} {n:3d}{veto}")

    print("\n  Y SI SE ABRIERA SU PUERTA, ¿DONDE MORIRIA DESPUES?")
    for d, f, p in computer:
        if not p.startswith("COMPUERTA"):
            continue
        c = f.get("market_gate") or {}
        antes = safe_int(c.get("value_before"))
        precio = safe_int(f.get("market_price"))
        tope = (antes - precio) / precio if precio else 0
        print(f"    {d[5:]} {f['name']:20s} {p[10:]:20s} precio {precio:>9}  "
              f"valia con la compuerta abierta {antes:>9} ({100 * tope:+.2f} %)  "
              f"-> {'RENDIMIENTO_INSUFICIENTE' if c.get('intent_before') == 'SPECULATION' and tope < RENDIMIENTO_MINIMO_DEL_CAPITAL else 'podria pasar'}")

    print(f"\n  RIVALES: {len(rivales)} filas. Todas MERCADO_DE_RIVAL "
          f"(la compra de rivales esta cerrada: `buying_closed`).")
    pasarian = [(d, f) for d, f, _ in rivales if f.get("would_pass")]
    print(f"    habrian pasado con la puerta abierta: {len(pasarian)}  "
          + ", ".join(f"{f['name']} ({d[5:]}, pujaria {f.get('would_bid')})" for d, f in pasarian))

    # EL EMBUDO QUE SE PUBLICA, CONTRA ESTE
    print("\n  EL EMBUDO QUE PUBLICA EL PANEL (`embudo.py`), EN LAS MISMAS FOTOS:")
    for dia, (ruta, foto) in fotos.items():
        def buscar(x):
            if isinstance(x, dict):
                if isinstance(x.get("funnel"), dict):
                    return x["funnel"]
                for y in x.values():
                    r = buscar(y)
                    if r:
                        return r
            return None
        fu = buscar(foto)
        if fu:
            print(f"    {dia}: dice VIVE {fu.get('alive')} de {fu.get('targets')}; "
                  f"el tablero dice biddable {foto['acquisition'].get('biddable')}")

    return computer


# ============================================================
# BLOQUE 2 — LA REGLA 2
# ============================================================


def bloque_2(sombra, fotos):

    print()
    print("=" * 76)
    print("BLOQUE 2 — LA REGLA 2, SOBRE LOS CORTES DEL LIBRO EN LA SOMBRA")
    print("=" * 76)

    cortes = [
        (s["at"], p) for s in sombra for p in s["players"]
        if p.get("gate") == "PRECIO_CAYENDO"
    ]
    print(f"  cortes: {len(cortes)} en {len(sombra)} fotos de la sombra, "
          f"{len({p['id'] for _, p in cortes})} jugadores")

    ritmos = [p.get("rate_percent_per_day") for _, p in cortes]
    print(f"  bajando (ritmo < 0): {sum(1 for r in ritmos if r is not None and r < 0)}   "
          f"quietos (ritmo == 0): {sum(1 for r in ritmos if r == 0)}   "
          f"sin ritmo: {sum(1 for r in ritmos if r is None)}")
    bajando = sorted(r for r in ritmos if r is not None and r < 0)
    if bajando:
        print(f"  ritmo de los que bajan: mediana {mediana(bajando):+.2f} %/dia, "
              f"el mas suave {bajando[-1]:+.3f}, el mas fuerte {bajando[0]:+.2f}")
    print(f"  intencion antes del corte: {dict(Counter(p.get('intent_before') for _, p in cortes))}")
    m = sorted(p["margin_percent"] for _, p in cortes)
    print(f"  margen con la compuerta abierta: min {m[0]:+.2f} %  mediana {m[len(m) // 2]:+.2f} %  "
          f"max {m[-1]:+.2f} %;  con 3 % o mas: {sum(x >= 3 for x in m)}")
    print(f"  con pulso apuntado: {sum(1 for _, p in cortes if p.get('demand_net') is not None)} "
          f"(la regla 2 NO lo lee: solo mira el ritmo)")

    # QUE HARIA LA PUERTA SIGUIENTE. La funcion de produccion, con el
    # modelo de puja de cada foto y sin bolsillo.
    print(f"\n  CON LA REGLA 2 ABIERTA, `optimal_bid` DE PRODUCCION (bolsillo infinito):")
    for dia, (ruta, foto) in fotos.items():
        modelo = foto["acquisition"].get("premium_model") or {}
        r = Counter()
        for _, p in cortes:
            plan = optimal_bid(
                price=p["market_price"], value=p["value_before"], model=modelo,
                available_budget=None, intent=p.get("intent_before"),
                route="COMPUTER_RESALE",
            )
            r[plan.get("decision")] += 1
        print(f"    con el modelo de la foto del {dia}: {dict(r)}")

    return cortes


# ============================================================
# BLOQUE 3 — EL CONTRAFACTUAL CONTRA LO QUE DEJA PASAR
# ============================================================


class Precios:

    def __init__(self, crudo):
        self.series = {
            str(k): (v.get("t") or [], v.get("p") or [])
            for k, v in (crudo.get("players") or {}).items()
        }
        self.ultimo = max((t[-1] for t, _ in self.series.values() if t), default=0)

    def en(self, pid, cuando):
        t, p = self.series.get(str(pid), ([], []))
        i = bisect.bisect_right(t, cuando.timestamp()) - 1
        return p[i] if i >= 0 else None

    def a_los(self, pid, desde, dias):
        objetivo = (desde + timedelta(days=dias)).timestamp()
        if objetivo > self.ultimo:
            return None
        t, p = self.series.get(str(pid), ([], []))
        i = bisect.bisect_left(t, objetivo)
        return p[i] if i < len(p) else None


def los_mercados(rev, fotos):
    """`{dia de mercado: {ids del Computer}}` de todo lo que hay."""

    mercados = defaultdict(set)

    for ruta in sorted(glob.glob("data/snapshot_202609*.json")):
        try:
            ventas = json.load(open(ruta, encoding="utf-8-sig"))["market"]["sales"]
        except Exception:                           # noqa: BLE001
            continue
        comp = [v for v in ventas if not v.get("user")]
        if not comp:
            continue
        dia = Counter(
            dia_de_mercado(datetime.fromtimestamp(v["date"], timezone.utc))
            for v in comp
        ).most_common(1)[0][0]
        mercados[dia] |= {str((v.get("player") or {}).get("id")) for v in comp}

    for e in leer_jsonl(ESCAPARATE, rev):
        mercados[e["dia_de_mercado"]] |= {str(p["id"]) for p in e["players"]}

    for dia, (_, foto) in fotos.items():
        hecha = momento((foto.get("meta") or {}).get("generated_at")) - timedelta(hours=2)
        mercados[dia_de_mercado(hecha)] |= {
            str(f["id"]) for f in foto["acquisition"]["targets"]
            if f.get("seller_id") is None and not f.get("rival_market")
        }

    return dict(mercados)


def catalogos_del_disco():
    fotos, vistos = [], set()
    for ruta in sorted(glob.glob("data/snapshot_202609*.json")):
        try:
            jugadores = json.load(open(ruta, encoding="utf-8-sig"))["catalog"]["data"]["players"]
            hecha = datetime.strptime(ruta[-20:-5], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
        except Exception:                           # noqa: BLE001
            continue
        if hecha.date() in vistos:
            continue
        vistos.add(hecha.date())
        fotos.append((hecha, {
            str(pid): (safe_int(f.get("points")),
                       safe_int(f.get("playedHome")) + safe_int(f.get("playedAway")))
            for pid, f in jugadores.items()
        }))
    return sorted(fotos, key=lambda x: x[0])


def bloque_3(sombra, cortes, rev, fotos):

    print()
    print("=" * 76)
    print("BLOQUE 3 — LOS QUE CORTA LA REGLA 2 CONTRA LOS QUE DEJA PASAR")
    print("=" * 76)

    precios = Precios(leer_json(PRECIOS, rev))
    mercados = los_mercados(rev, fotos)
    filas = list(leer_json(DIVERGENCIA, rev)["observations"].values())

    ritmo_del_dia = {}
    for f in filas:
        ritmo_del_dia[(str(f["player_id"]), f["seen_at"][:10])] = f

    print("  mercados del Computer reconstruidos: "
          + ", ".join(f"{d[5:]}({len(v)})" for d, v in sorted(mercados.items())))

    corta, pasa, sin_mercado = [], [], 0

    for s in sombra:
        cuando = momento(s["at"])
        dia = dia_de_mercado(cuando)
        ids = mercados.get(dia)
        cortados = {str(p["id"]) for p in s["players"] if p.get("gate") == "PRECIO_CAYENDO"}
        for p in s["players"]:
            if p.get("gate") == "PRECIO_CAYENDO":
                corta.append((cuando, str(p["id"]), p["name"], p["market_price"]))
        if not ids:
            sin_mercado += 1
            continue
        for pid in ids - cortados:
            f = ritmo_del_dia.get((pid, cuando.date().isoformat()))
            if not f:
                continue
            r = f.get("price_change_percent") or 0
            racha = f.get("trend_days") or 0
            pulso = f.get("demand_net")
            if r > 0 and not (racha >= 3 and pulso is not None and pulso <= -20):
                base = precios.en(pid, cuando) or f.get("price")
                pasa.append((cuando, pid, f.get("player_name"), base))

    print(f"  fotos de la sombra sin mercado reconstruido: {sin_mercado} de {len(sombra)} "
          f"(ahi solo cuentan los cortados)")
    print(f"  cortados por la regla 2: {len(corta)} filas, {len({x[1] for x in corta})} jugadores")
    print(f"  del mismo mercado y dia, con la compuerta abierta: {len(pasa)} filas, "
          f"{len({x[1] for x in pasa})} jugadores")

    # Para que el control sea del MISMO periodo, los que pasan solo
    # cuentan en las fotos que tienen mercado; los cortados, tambien.
    dias_con_mercado = {x[0] for x in pasa}
    corta_mismo = [x for x in corta if x[0] in dias_con_mercado]
    print(f"  cortados en las fotos con mercado: {len(corta_mismo)} filas")

    def retornos(grupo, dias):
        out = []
        for cuando, pid, nombre, base in grupo:
            fin = precios.a_los(pid, cuando, dias)
            if fin and base:
                out.append((pid, nombre, base, fin, (fin - base) * 100.0 / base))
        return out

    print("\n  EN PRECIO")
    for d in PLAZOS:
        c = retornos(corta_mismo, d)
        p = retornos(pasa, d)
        def linea(nombre, g):
            v = [x[4] for x in g]
            if not v:
                print(f"    {nombre:36s} n=0")
                return
            print(f"    {nombre:36s} n={len(v):4d} jug={len({x[0] for x in g}):3d}  "
                  f"subieron {pct(sum(x > 0 for x in v), len(v))}  mediana {mediana(v):+6.2f} %  "
                  f"media {statistics.mean(v):+6.2f} %")
        print(f"  --- a {d} dias")
        linea("cortados (regla 2)", c)
        linea("los que deja pasar", p)
        if c and p:
            ec, ep = defaultdict(list), defaultdict(list)
            for x in c:
                ec[x[0]].append(x[4])
            for x in p:
                ep[x[0]].append(x[4])
            azar = random.Random(7)
            ic, ip = sorted(ec), sorted(ep)
            difs = sorted(
                statistics.mean([y for j in azar.choices(ic, k=len(ic)) for y in ec[j]])
                - statistics.mean([y for j in azar.choices(ip, k=len(ip)) for y in ep[j]])
                for _ in range(3000)
            )
            dm = statistics.mean([x[4] for x in c]) - statistics.mean([x[4] for x in p])
            print(f"    cortados - pasan: {dm:+.2f} pp (media), IC 95 % por jugador "
                  f"{difs[75]:+.2f} .. {difs[2924]:+.2f}")

    # EN PUNTOS
    catalogos = catalogos_del_disco()
    j7 = {}
    for linea_j in leer_jsonl(PUNTOS_J7, rev):
        if linea_j.get("jornada") == 7:
            j7 = {str(k): (int(v[0]), int(v[1])) for k, v in linea_j["players"].items()}
    print("\n  EN PUNTOS: de la foto del catalogo anterior al dia al cierre de la J7")
    if catalogos and j7:
        for nombre, g in (("cortados (regla 2)", corta_mismo), ("los que deja pasar", pasa)):
            tramos = {}
            for cuando, pid, _, _ in g:
                antes = [c for c in catalogos if c[0] <= cuando] or catalogos[:1]
                foto = antes[-1][1].get(pid)
                fin = j7.get(pid)
                if foto and fin:
                    tramos[(pid, antes[-1][0])] = (fin[0] - foto[0], fin[1] - foto[1])
            pts = sum(x[0] for x in tramos.values())
            jug = sum(x[1] for x in tramos.values())
            print(f"    {nombre:22s} tramos={len(tramos):4d} jugadores={len({k[0] for k in tramos}):3d}  "
                  f"partidos {jug:4d}  puntos por partido jugado {pts / jug if jug else 0:4.2f}  "
                  f"no jugo ninguno {pct(sum(1 for x in tramos.values() if x[1] == 0), len(tramos))}")

    # EN EUROS: todos los cortes, no solo los del mismo periodo.
    print("\n  EN EUROS, SI SE HUBIERAN COMPRADO LOS 264 AL PRECIO DE MERCADO")
    for d in PLAZOS:
        g = retornos(corta, d)
        if not g:
            continue
        total = sum(x[3] - x[2] for x in g)
        por = defaultdict(int)
        for x in g:
            por[x[1]] += x[3] - x[2]
        mejor = max(por.items(), key=lambda kv: abs(kv[1]))
        print(f"    a {d:>2} dias: n={len(g):3d}  total {euros(total)} EUR  "
              f"(invertido {euros(sum(x[2] for x in g))[1:]} EUR)  "
              f"el que mas pesa: {mejor[0]} {euros(mejor[1])}  "
              f"sin el: {euros(total - mejor[1])}")


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument("--rev", default=None)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"libros leidos de: {args.rev or 'el disco'}")

    fotos = las_fotos(args.rev)
    sombra = leer_jsonl(SOMBRA, args.rev)

    bloque_1(fotos)
    cortes = bloque_2(sombra, fotos)
    bloque_3(sombra, cortes, args.rev, fotos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
