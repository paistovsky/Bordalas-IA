"""
La regla 3 del `market_rate_gate`, corrida contra los libros de esta casa.

QUE MIDE

    BLOQUE 1   los vetos de verdad: los que apunto el libro en la
               sombra con `RACHA_SIN_DEMANDA`, con nombre y fecha.
    BLOQUE 2   el contrafactual. El patron que veta la regla
               -precio subiendo, racha >= 3, pulso <= -20- sobre
               todo el libro de la divergencia, contra lo que la
               regla deja pasar -mismo precio subiendo y misma
               racha, sin pulso en contra- y contra el mercado:
               a 3, 7 y 14 dias en precio, y en puntos hasta el
               paron. Y los vetos de verdad, en euros.
    BLOQUE 3   el pulso congelado: cuantos, desde cuando, y en que
               dias cambia cuando cambia.

QUE LIBROS LEE

    data/intelligence/divergence_ledger.json       el patron, dia a dia
    data/autopilot/price_history.json              el precio a N dias
    data/intelligence/libro_en_la_sombra.jsonl     los vetos de verdad
    data/intelligence/scout_accuracy_ledger.json   el pulso, dia a dia
    data/intelligence/puntos_por_jornada.jsonl     los puntos tras la J7
    data/snapshot_*.json                           los puntos antes (catalogo)
    data/solvency/bitacora_del_saldo.jsonl         la puja maxima

    Con `--rev REV` los libros versionados se leen de esa revision.
    Los `snapshot_*.json` no estan en git: se leen siempre del
    disco, y el script dice cuales encontro.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende nada
    y NO ESCRIBE NI UNA LINEA DE NINGUN LIBRO.

USO

    python scripts/la_regla_tres.py --rev HEAD > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import argparse
import bisect
import glob
import json
import random
import statistics
import subprocess
import sys

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone


DIVERGENCIA = "data/intelligence/divergence_ledger.json"
PRECIOS = "data/autopilot/price_history.json"
SOMBRA = "data/intelligence/libro_en_la_sombra.jsonl"
ACIERTOS = "data/intelligence/scout_accuracy_ledger.json"
PUNTOS_J7 = "data/intelligence/puntos_por_jornada.jsonl"
SALDO = "data/solvency/bitacora_del_saldo.jsonl"


# Los cortes de la regla, copiados de `market_rate_gate` para que
# el script no importe el modulo que mide.
RACHA = 3
PULSO_EN_CONTRA = -20.0

PLAZOS = (3, 7, 14)


def leer(ruta: str, rev: str | None) -> str:
    if rev is None:
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


def momento(marca: str) -> datetime:
    m = datetime.fromisoformat(str(marca).replace("Z", "+00:00"))
    return m if m.tzinfo else m.replace(tzinfo=timezone.utc)


def mediana(v):
    return round(statistics.median(v), 2) if v else None


def pct(a, b):
    return f"{100 * a / b:5.1f} %" if b else "   -   "


def euros(x) -> str:
    return f"{x:+,.0f}".replace(",", ".")


# ============================================================
# EL PRECIO A N DIAS
# ============================================================


class Precios:

    def __init__(self, crudo: dict):
        self.series = {
            str(k): (v.get("t") or [], v.get("p") or [])
            for k, v in (crudo.get("players") or {}).items()
        }
        self.ultimo = max(
            (t[-1] for t, _ in self.series.values() if t), default=0
        )

    def en(self, pid, cuando: datetime):
        """El ultimo precio visto en `cuando` o antes."""
        t, p = self.series.get(str(pid), ([], []))
        i = bisect.bisect_right(t, cuando.timestamp()) - 1
        return p[i] if i >= 0 else None

    def a_los(self, pid, desde: datetime, dias: int):
        """El primer precio visto a `dias` dias o despues. None si aun no."""
        objetivo = (desde + timedelta(days=dias)).timestamp()
        if objetivo > self.ultimo:
            return None
        t, p = self.series.get(str(pid), ([], []))
        i = bisect.bisect_left(t, objetivo)
        return p[i] if i < len(p) else None


# ============================================================
# LOS PUNTOS: DE LA FOTO DEL CATALOGO A LA J7
# ============================================================


def catalogos_del_disco():
    """`[(desde_cuando_vale, {pid: (puntos, jugados)})]`, por fecha."""

    fotos = []
    vistos = set()

    for ruta in sorted(glob.glob("data/snapshot_202609*.json")):
        try:
            datos = json.load(open(ruta, encoding="utf-8-sig"))
            jugadores = datos["catalog"]["data"]["players"]
            hecha = datetime.strptime(
                ruta[-20:-5], "%Y%m%d_%H%M%S"
            ).replace(tzinfo=timezone.utc)
        except Exception:                           # noqa: BLE001
            continue

        clave = hecha.date()
        if clave in vistos:
            continue
        vistos.add(clave)

        fotos.append((
            hecha,
            {
                str(pid): (
                    int(f.get("points") or 0),
                    int(f.get("playedHome") or 0) + int(f.get("playedAway") or 0),
                )
                for pid, f in jugadores.items()
            },
        ))

    return sorted(fotos, key=lambda x: x[0])


# ============================================================
# BLOQUE 1
# ============================================================


def bloque_1(sombra):

    print("=" * 72)
    print("BLOQUE 1 — LOS VETOS DE VERDAD (libro en la sombra)")
    print("=" * 72)

    dias = sorted({s["at"][:10] for s in sombra})
    codigos = Counter(p.get("gate") for s in sombra for p in s["players"])
    print(f"fotos: {len(sombra)} ({dias[0]} .. {dias[-1]}), casos: "
          f"{sum(codigos.values())}  por motivo: {dict(codigos)}")

    vetos = [
        (s["at"], p)
        for s in sombra
        for p in s["players"]
        if p.get("gate") == "RACHA_SIN_DEMANDA"
    ]

    for at, p in vetos:
        print(f"  {at[:16]}  {p['name']:13s} id {p['id']:>6}  precio {p['market_price']:>9}  "
              f"valia {p['value_before']:>9} ({p['margin_percent']:+.2f} %)  "
              f"ritmo {p['rate_percent_per_day']:+.2f} %/dia  racha {p['trend_days']}  "
              f"pulso {p['demand_net']}")

    return vetos


# ============================================================
# BLOQUE 2
# ============================================================


def clasificar(filas):

    veta, pasa = [], []

    for f in filas:
        ritmo = f.get("price_change_percent")
        racha = f.get("trend_days")

        if ritmo is None or ritmo <= 0 or racha is None or racha < RACHA:
            continue

        pulso = f.get("demand_net")

        if pulso is not None and pulso <= PULSO_EN_CONTRA:
            veta.append(f)
        else:
            pasa.append(f)

    return veta, pasa


def bloque_2(filas, precios, catalogos, j7, vivos):

    print()
    print("=" * 72)
    print("BLOQUE 2 — EL CONTRAFACTUAL, SOBRE TODO EL LIBRO")
    print("=" * 72)

    # El retorno de cada fila, del historico de precios.
    for f in filas:
        visto = momento(f["seen_at"])
        base = precios.en(f["player_id"], visto) or f.get("price")
        f["_base"] = base
        for d in PLAZOS:
            fin = precios.a_los(f["player_id"], visto, d)
            f[f"_r{d}"] = (
                (fin - base) * 100.0 / base if fin and base else None
            )

    veta, pasa = clasificar(filas)

    print(f"la regla VETA (ritmo > 0, racha >= {RACHA}, pulso <= {PULSO_EN_CONTRA:.0f}): "
          f"{len(veta)} filas, {len({f['player_id'] for f in veta})} jugadores")
    print(f"la regla DEJA PASAR (ritmo > 0, racha >= {RACHA}, sin pulso en contra): "
          f"{len(pasa)} filas, {len({f['player_id'] for f in pasa})} jugadores")

    medianas_dia = {}
    for d in PLAZOS:
        grupos = defaultdict(list)
        for f in filas:
            if f[f"_r{d}"] is not None:
                grupos[f["seen_at"][:10]].append(f[f"_r{d}"])
        medianas_dia[d] = {k: statistics.median(v) for k, v in grupos.items()}

    print("\n  EN PRECIO")
    for d in PLAZOS:
        k = f"_r{d}"
        v = [f for f in veta if f[k] is not None]
        p = [f for f in pasa if f[k] is not None]
        dias_v = Counter(f["seen_at"][:10] for f in v)
        mercado = [
            x for f in filas if f[k] is not None and f["seen_at"][:10] in dias_v
            for x in [f[k]]
        ]

        def fila(nombre, g, vals=None):
            vals = vals if vals is not None else [f[k] for f in g]
            if not vals:
                print(f"    {nombre:44s} n=0")
                return
            print(f"    {nombre:44s} n={len(vals):5d}  subieron {pct(sum(x > 0 for x in vals), len(vals))}  "
                  f"mediana {mediana(vals):+6.2f} %  media {statistics.mean(vals):+6.2f} %  "
                  f"peor {min(vals):+7.2f} %")

        print(f"  --- a {d} dias")
        fila(f"vetados ({len({f['player_id'] for f in v})} jugadores)", v)
        fila(f"los que deja pasar ({len({f['player_id'] for f in p})} jugadores)", p)
        fila("mercado, los mismos dias que los vetados", None, mercado)
        fila("  vetados con el pulso VIVO", [f for f in v if f["player_id"] in vivos])
        fila("  vetados con el pulso CONGELADO", [f for f in v if f["player_id"] not in vivos])

        # La diferencia que importa: vetados contra los que pasan,
        # cada uno contra la mediana del mercado de su dia, y con el
        # JUGADOR como unidad al remuestrear.
        if v and p:
            ev = defaultdict(list)
            for f in v:
                ev[f["player_id"]].append(f[k] - medianas_dia[d][f["seen_at"][:10]])
            ep = defaultdict(list)
            for f in p:
                ep[f["player_id"]].append(f[k] - medianas_dia[d][f["seen_at"][:10]])
            azar = random.Random(7)
            iv, ip = sorted(ev), sorted(ep)
            difs = sorted(
                statistics.mean([x for j in azar.choices(iv, k=len(iv)) for x in ev[j]])
                - statistics.mean([x for j in azar.choices(ip, k=len(ip)) for x in ep[j]])
                for _ in range(3000)
            )
            mv = statistics.mean([x for xs in ev.values() for x in xs])
            mp = statistics.mean([x for xs in ep.values() for x in xs])
            print(f"    sobre el mercado del dia: vetados {mv:+.2f} pp, los que pasan {mp:+.2f} pp; "
                  f"vetados - pasan = {mv - mp:+.2f} pp, IC 95 % por jugador "
                  f"{difs[75]:+.2f} .. {difs[2924]:+.2f}")

    # --------------------------------------------------------
    # EN PUNTOS
    # --------------------------------------------------------
    print("\n  EN PUNTOS: desde la foto del catalogo anterior al dia hasta")
    print("  el cierre de la J7 (no se juega otra vez hasta el 09/10)")

    if not catalogos or not j7:
        print("    NO HAY CATALOGOS O NO HAY J7: no se mide.")
        return veta, pasa

    print("    fotos del catalogo usadas: "
          + ", ".join(c[0].strftime("%d/%m %H:%M") for c in catalogos))

    def puntos(f):
        visto = momento(f["seen_at"])
        antes = [c for c in catalogos if c[0] <= visto] or catalogos[:1]
        foto = antes[-1][1].get(f["player_id"])
        fin = j7.get(f["player_id"])
        if not foto or not fin:
            return None
        dp, dj = fin[0] - foto[0], fin[1] - foto[1]
        return dp, dj

    for nombre, g in (("vetados", veta), ("los que deja pasar", pasa),
                      ("todo el mercado", filas)):
        # Un jugador cuenta UNA vez por foto de partida: si no, el
        # mismo tramo de puntos se contaria tantas veces como dias
        # salga en el libro.
        tramos = {}
        for f in g:
            r = puntos(f)
            if r is None:
                continue
            visto = momento(f["seen_at"])
            antes = [c for c in catalogos if c[0] <= visto] or catalogos[:1]
            tramos[(f["player_id"], antes[-1][0])] = r
        if not tramos:
            print(f"    {nombre:22s} n=0")
            continue
        pts = [p for p, _ in tramos.values()]
        jug = [j for _, j in tramos.values()]
        por_partido = sum(pts) / sum(jug) if sum(jug) else 0
        print(f"    {nombre:22s} tramos={len(tramos):5d} jugadores={len({k[0] for k in tramos}):4d}  "
              f"puntos medianos {mediana(pts):+5.1f}  partidos jugados {sum(jug):5d}  "
              f"puntos por partido jugado {por_partido:4.2f}  "
              f"no jugo ninguno {pct(sum(j == 0 for j in jug), len(jug))}")

    return veta, pasa


def los_vetos_en_euros(vetos, precios, catalogos, j7, saldo):

    print()
    print("=" * 72)
    print("BLOQUE 2 — LOS VETOS DE VERDAD, EN EUROS")
    print("=" * 72)
    print("  Compra al precio de mercado de ese dia (sin prima de puja) y")
    print("  venta al precio de mercado N dias despues. Es el tope de lo")
    print("  que se dejo de ganar: la puja real paga algo por encima.")

    marcas = sorted((s["at"], s.get("maximum_bid")) for s in saldo)
    claves = [m[0] for m in marcas]

    totales = defaultdict(int)
    for at, p in vetos:
        cuando = momento(at)
        base = p["market_price"]
        i = bisect.bisect_right(claves, at) - 1
        tope = marcas[i][1] if i >= 0 else None
        trozos = []
        for d in PLAZOS:
            fin = precios.a_los(p["id"], cuando, d)
            if fin is None:
                trozos.append(f"{d:>2}d  (aun no)")
                continue
            totales[d] += fin - base
            trozos.append(f"{d:>2}d {fin:>9} {euros(fin - base):>10}")
        antes = [c for c in catalogos if c[0] <= cuando] or catalogos[:1]
        foto = antes[-1][1].get(str(p["id"])) if antes else None
        fin_j7 = j7.get(str(p["id"]))
        pts = (f"{fin_j7[0] - foto[0]:+d} pts en {fin_j7[1] - foto[1]} partidos"
               if foto and fin_j7 else "puntos: sin foto")
        print(f"  {at[:10]} {p['name']:13s} compra {base:>9}  "
              + "  |  ".join(trozos)
              + f"  |  {pts}  |  puja maxima ese dia: {tope if tope is not None else 'sin bitacora'}")
    print("  TOTAL: " + "   ".join(f"{d} dias {euros(totales[d])} EUR" for d in PLAZOS if d in totales))


# ============================================================
# BLOQUE 3
# ============================================================


def bloque_3(aciertos):

    print()
    print("=" * 72)
    print("BLOQUE 3 — EL PULSO CONGELADO")
    print("=" * 72)

    serie = defaultdict(dict)
    precio = defaultdict(dict)
    for p in aciertos:
        dia = str(p.get("predicted_at"))[:10]
        if p.get("source") == "COMUNIATE_PULSO":
            serie[p["player_id"]][dia] = p.get("magnitude_percent")
        elif p.get("source") == "COMUNIATE":
            precio[p["player_id"]][dia] = p.get("magnitude_eur")

    dias = sorted({d for s in serie.values() for d in s})
    print(f"dias con pulso: {len(dias)} ({dias[0]} .. {dias[-1]}), jugadores: {len(serie)}")

    vivos = set()
    congelados = []
    for pid, s in serie.items():
        valores = [s[d] for d in sorted(s)]
        if len(set(valores)) > 1:
            vivos.add(pid)
        else:
            congelados.append((pid, len(valores), min(s), max(s)))

    print(f"con un solo valor en todo el periodo: {len(congelados)} de {len(serie)}")
    for minimo in (2, 5, 10, 15):
        g = [c for c in congelados if c[1] >= minimo]
        t = [pid for pid, s in serie.items() if len(s) >= minimo]
        print(f"  entre los que salen {minimo:>2}+ dias: {len(g)} de {len(t)} congelados "
              f"({pct(len(g), len(t))})")
    desde = Counter(c[2] for c in congelados if c[1] >= 10)
    print(f"  congelados de 10+ dias, por primer dia visto: {dict(sorted(desde.items()))}")

    # En la MISMA respuesta: el movimiento en euros de Comuniate
    # tambien se apunta. Si el precio cambia y el pulso no, el
    # cacheo no puede ser: los dos salen del mismo HTML.
    mismos = [
        pid for pid, _, _, _ in congelados
        if len(set(precio.get(pid, {}).values())) > 1
    ]
    print(f"  congelados cuyo movimiento en euros, del MISMO registro, si cambia: "
          f"{len(mismos)} de {len(congelados)}")

    # CUANDO CAMBIA, ¿QUE DIA CAMBIA?
    print("  de un dia al siguiente, cuantos pulsos cambian (de los que salen los dos dias):")
    for ayer, hoy in zip(dias, dias[1:]):
        comunes = [pid for pid, s in serie.items() if ayer in s and hoy in s]
        cambian = sum(serie[pid][ayer] != serie[pid][hoy] for pid in comunes)
        print(f"    {ayer} -> {hoy}  {cambian:3d} de {len(comunes):3d}")

    return vivos


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument("--rev", default=None)
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"libros leidos de: {args.rev or 'el disco'}")

    filas = list(leer_json(DIVERGENCIA, args.rev)["observations"].values())
    precios = Precios(leer_json(PRECIOS, args.rev))
    sombra = leer_jsonl(SOMBRA, args.rev)
    aciertos = list(leer_json(ACIERTOS, args.rev)["predictions"].values())
    saldo = leer_jsonl(SALDO, args.rev)

    j7_linea = leer_jsonl(PUNTOS_J7, args.rev)
    j7 = {
        str(k): (int(v[0]), int(v[1]))
        for linea in j7_linea if linea.get("jornada") == 7
        for k, v in linea["players"].items()
    }

    catalogos = catalogos_del_disco()

    vetos = bloque_1(sombra)
    vivos = bloque_3(aciertos)
    bloque_2(filas, precios, catalogos, j7, vivos)
    los_vetos_en_euros(vetos, precios, catalogos, j7, saldo)

    return 0


if __name__ == "__main__":
    sys.exit(main())
