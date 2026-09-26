"""
El once objetivo, medido: el calendario, la titularidad, los tres
onces y el plan.

SOLO LEE. Ni escribe en `data/`, ni toca Biwenger, ni pide nada a la
red. Todo sale de ficheros que ya estan en el disco:

    fotos locales        data/snapshot_20260910_123532.json (tranquila)
                         data/snapshot_20260919_181829.json (la ultima)
    calendario           data/calendar/laliga_calendar.json
    clasificacion        data/league_center/laliga_standings.json (23/09)
    titularidad FF       data/intelligence/futbolfantasy_board.json (22/09)
    libros               data/trading/position_ledger.json,
                         data/trading/bid_outcome_ledger.json
    el panel de las 08:10 del 26/09, que NO esta en el repo: es el
                         `dashboard/data/status.json` del artefacto
                         `bordalas-live-diagnostics-36222790559`.
                         Se pasa con --panel.

LOS PUNTOS PARTIDO A PARTIDO, SIN PEDIRLOS

    El catalogo de Biwenger trae en cada jugador `fitness`: los puntos
    de los ultimos cinco partidos de su equipo, el mas reciente
    primero; `null` o una etiqueta ("injured", "doubt") si no jugo.
    Cruzado con el calendario da el partido, el campo y el rival.

    Cruzarlo a ciegas falla: en fotos tomadas EN MITAD de una jornada
    el hueco se corre uno (medido: 208 de 2.450 observaciones repetidas
    no coinciden). Por eso:

      · la foto del 10/09 es TRANQUILA (entre la J4 y la J5) y ningun
        equipo llevaba mas de cinco partidos: su `fitness` es la
        temporada ENTERA. Se comprueba: suma de `fitness` = puntos.
      · la del 19/09 se lee solo por lo NUEVO: se busca cuantos
        huecos se han corrido respecto a la del 10/09, y lo nuevo se
        comprueba contra la resta de totales.
      · un jugador que no cuadra se descarta entero, y se cuenta.

USO

    python scripts/el_once_objetivo.py --panel RUTA/status.json
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.analysis.el_once_objetivo import (  # noqa: E402
    FUERA,
    JUEGA_SI_DUDA,
    desviacion_por_contexto,
    el_mejor_once,
    el_plan,
    encoger,
    estimar_k,
)

MADRID = ZoneInfo("Europe/Madrid")
POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}

QUIETA = RAIZ / "data" / "snapshot_20260910_123532.json"
TARDE = RAIZ / "data" / "snapshot_20260919_181829.json"
CALENDARIO = RAIZ / "data" / "calendar" / "laliga_calendar.json"
CLASIFICACION = RAIZ / "data" / "league_center" / "laliga_standings.json"
FF = RAIZ / "data" / "intelligence" / "futbolfantasy_board.json"
POSICIONES = RAIZ / "data" / "trading" / "position_ledger.json"
PUJAS = RAIZ / "data" / "trading" / "bid_outcome_ledger.json"

# Dos nombres de Biwenger que casan con dos equipos del calendario.
A_MANO = {"Barcelona": "FC Barcelona", "Deportivo": "RC Deportivo"}

# Un partido se da por terminado 2 h 30 min despues del saque.
DURA = timedelta(hours=2, minutes=30)

YAMAL = "Yamal"
CAJA_DE_FICHAR = 1_356_676          # panel de las 08:10, elVestuarioLibre
TOPE_DE_FICHAS = 23                 # la mayor plantilla de la liga hoy


def leer(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def norm(texto) -> str:
    return (
        unicodedata.normalize("NFKD", str(texto or ""))
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


def cuando(partido):
    return datetime.fromisoformat(partido["kickoff"])


def foto_en(ruta: Path) -> datetime:
    sello = ruta.stem.split("_", 1)[1]
    return datetime.strptime(sello, "%Y%m%d_%H%M%S").replace(tzinfo=MADRID)


# ============================================================
# EQUIPOS
# ============================================================

def casar_equipos(equipos_bw: dict, nombres: list) -> dict:
    """team_id de Biwenger -> nombre del calendario."""

    out = {}
    for tid, equipo in equipos_bw.items():
        nombre = equipo.get("name")
        if nombre in A_MANO:
            out[int(tid)] = A_MANO[nombre]
            continue
        n = norm(nombre)
        slug = norm(equipo.get("slug", "")).replace("-", " ")
        exactos = [x for x in nombres if norm(x) == n]
        parecidos = [x for x in nombres if n in norm(x) or slug in norm(x)]
        eleccion = exactos or parecidos
        if len(eleccion) == 1:
            out[int(tid)] = eleccion[0]
    return out


def puestos(clasificacion: dict, nombres: list) -> dict:
    """nombre del calendario -> puesto en la clasificacion."""

    out = {}
    for fila in clasificacion.get("standings") or []:
        n = norm(fila.get("team"))
        casan = [x for x in nombres if norm(x) == n] or [
            x for x in nombres if n in norm(x) or norm(x) in n
        ]
        if len(casan) == 1:
            out[casan[0]] = int(fila["rank"])
    return out


# ============================================================
# BLOQUE 1: LOS PARTIDOS UNO A UNO
# ============================================================

def partidos_del_equipo(calendario, equipo, antes=None, despues=None):
    out = [
        m for m in calendario
        if equipo in (m["home"], m["away"])
        and (antes is None or cuando(m) + DURA < antes)
        and (despues is None or cuando(m) + DURA >= despues)
    ]
    out.sort(key=cuando)
    return out


def jugado(valor) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def los_partidos(quieta_ruta, tarde_ruta, calendario, casados, puesto):
    quieta = leer(quieta_ruta)["catalog"]["data"]["players"]
    tarde = leer(tarde_ruta)["catalog"]["data"]["players"]
    t_quieta, t_tarde = foto_en(quieta_ruta), foto_en(tarde_ruta)

    partidos = []
    cuenta = collections.Counter()
    validados = set()

    for pid, p in tarde.items():
        if int(p.get("position") or 0) not in POS:
            cuenta["no_es_jugador_de_campo"] += 1
            continue
        equipo = casados.get(int(p.get("teamID") or 0))
        q = quieta.get(pid)
        if not equipo or not q or int(q.get("teamID") or 0) != int(p.get("teamID") or 0):
            cuenta["sin_equipo_o_cambio_de_equipo"] += 1
            continue

        viejos = partidos_del_equipo(calendario, equipo, antes=t_quieta)
        fq = list(q.get("fitness") or [])
        if len(viejos) > 5:
            cuenta["mas_de_cinco_antes_del_10_09"] += 1
            continue
        # la foto tranquila: el mas reciente primero
        mapa = list(zip(reversed(viejos), fq))
        if sum(v for _, v in mapa if jugado(v)) != int(q.get("points") or 0):
            cuenta["la_tranquila_no_suma"] += 1
            continue

        # la tarde: cuantos huecos nuevos
        ft = list(p.get("fitness") or [])
        nuevos = None
        for j in range(0, 6):
            if ft[j:] == fq[: len(ft) - j] and len(ft) - j <= len(fq):
                nuevos = j
                break
        despues = partidos_del_equipo(calendario, equipo, despues=t_quieta)
        delta = int(p.get("points") or 0) - int(q.get("points") or 0)
        if nuevos is None or nuevos > len(despues):
            cuenta["la_tarde_no_se_alinea"] += 1
            continue
        lo_nuevo = list(zip(reversed(despues[:nuevos]), ft[:nuevos]))
        if sum(v for _, v in lo_nuevo if jugado(v)) != delta:
            cuenta["lo_nuevo_no_suma"] += 1
            continue

        cuenta["cuadra"] += 1
        validados.add(int(pid))
        for partido, valor in mapa + lo_nuevo:
            if not jugado(valor):
                continue
            casa = partido["home"] == equipo
            rival = partido["away"] if casa else partido["home"]
            rango = puesto.get(rival)
            partidos.append(
                {
                    "jugador": int(pid),
                    "posicion": int(p.get("position") or 0),
                    "puntos": float(valor),
                    "casa": casa,
                    "rival_alto": (rango <= 10) if rango else None,
                    "jornada": partido["matchday"],
                }
            )

    return partidos, cuenta, tarde, validados


def casa_por_totales(catalogo) -> dict:
    """El efecto de casa, EXACTO, con los totales de casa y fuera."""

    out = {}
    for pos in (1, 2, 3, 4, "todas"):
        dc = df = nc = nf = 0.0
        for p in catalogo.values():
            if pos != "todas" and int(p.get("position") or 0) != pos:
                continue
            ph, pa = int(p.get("playedHome") or 0), int(p.get("playedAway") or 0)
            if ph + pa == 0:
                continue
            media = (int(p.get("pointsHome") or 0) + int(p.get("pointsAway") or 0)) / (ph + pa)
            dc += int(p.get("pointsHome") or 0) - ph * media
            df += int(p.get("pointsAway") or 0) - pa * media
            nc += ph
            nf += pa
        out[pos] = {
            "casa": round(dc / nc, 3) if nc else None, "n_casa": int(nc),
            "fuera": round(df / nf, 3) if nf else None, "n_fuera": int(nf),
        }
    return out


def varianza_dentro(partidos) -> dict:
    """Varianza de un partido alrededor de la media de su jugador."""

    por_jugador = collections.defaultdict(list)
    for p in partidos:
        por_jugador[(p["posicion"], p["jugador"])].append(p["puntos"])
    suma = collections.Counter()
    grados = collections.Counter()
    for (pos, _), vals in por_jugador.items():
        if len(vals) < 2:
            continue
        m = sum(vals) / len(vals)
        suma[pos] += sum((v - m) ** 2 for v in vals)
        grados[pos] += len(vals) - 1
    return {pos: suma[pos] / grados[pos] for pos in suma if grados[pos]}


# ============================================================
# BLOQUE 2: TITULARIDAD
# ============================================================

def correlacion(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    sy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return round(sxy / (sx * sy), 3) if sx and sy else None


def rangos(v):
    orden = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
            j += 1
        for k in range(i, j + 1):
            r[orden[k]] = (i + j) / 2
        i = j + 1
    return r


# ============================================================
# BLOQUE 3: VALORES, ONCES Y PLAN
# ============================================================

def valores(panel_jugadores, partidos_por_equipo, var_dentro, ff, efectos, proximos):
    """
    Dos metodos, en la misma tabla:

        EL DEL DUEÑO   puntos por partido JUGADO, encogidos k = 3 hacia
                       su posicion, minimo 3 jugados, sin titularidad
        EL NUEVO       puntos esperados por partido DE SU EQUIPO:
                           tasa de juego x puntos por partido encogidos
                       con k sacado de los datos por posicion. La
                       jornada usa FutbolFantasy si lo hay.
    """

    medias = {}
    for pos in (1, 2, 3, 4):
        filas = [j for j in panel_jugadores if j["position"] == pos and j["played"] > 0]
        medias[pos] = sum(j["points"] for j in filas) / sum(j["played"] for j in filas)

    ks = {}
    for pos in (1, 2, 3, 4):
        ks[pos] = estimar_k(
            [
                {"ppg": j["points"] / j["played"], "jugados": j["played"]}
                for j in panel_jugadores
                if j["position"] == pos and j["played"] > 0
            ],
            var_dentro.get(pos),
        )

    out = []
    for j in panel_jugadores:
        pos = j["position"]
        k = ks[pos] if ks[pos] is not None else 3.0
        ppg = encoger(j["points"], j["played"], medias[pos], k)
        del_equipo = max(partidos_por_equipo.get(j["team_id"], 0), 1)
        tasa = min(j["played"] / del_equipo, 1.0)
        prob = ff.get(j["id"])
        estado = str(j.get("status") or "ok")
        if estado in FUERA:
            juega_j = 0.0
        elif prob is not None:
            # FutbolFantasy es de ESE partido: manda la suya.
            juega_j = prob / 100.0
        elif estado == "doubt":
            # Medido: 4 de 17 en duda jugaron su siguiente partido.
            juega_j = JUEGA_SI_DUDA
        else:
            juega_j = tasa

        ajuste = efectos.get((pos, j["team_id"]), {"temporada": 0.0, "jornada": 0.0})

        out.append(
            {
                **j,
                "id": j["id"],
                "posicion": pos,
                "precio": j["price"],
                "tasa": round(tasa, 3),
                "ppg_encogida": round(ppg, 3),
                "valor": round(tasa * ppg, 4),
                "valor_cal": round(tasa * (ppg + ajuste["temporada"]), 4),
                "jornada": round(juega_j * ppg, 4),
                "jornada_cal": round(juega_j * (ppg + ajuste["jornada"]), 4),
                "duenio": (
                    round(encoger(j["points"], j["played"], medias[pos], 3.0), 4)
                    if j["played"] >= 3 else None
                ),
                "con_ff": prob is not None,
            }
        )
    return out, medias, ks


def euros(v) -> str:
    return f"{int(v):,}".replace(",", ".")


def pinta_once(titulo, once, por_id, valor):
    print(f"  {titulo}: {once['formacion']}  suma {once['suma']:.2f}  "
          f"(precio de los once {euros(once['coste'])})")
    fila = sorted((por_id[i] for i in once["ids"]), key=lambda j: (j["posicion"], -j[valor]))
    for j in fila:
        print(f"      {POS[j['posicion']]} {j['name'][:20]:20s} {j['de_quien']:8s} "
              f"{valor} {j[valor]:.2f}  tasa {j['tasa']:.2f}  pts {j['points']}/{j['played']}  "
              f"{euros(j['precio'])}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--ff", default=str(FF),
                    help="tablero de FutbolFantasy (para comparar con el catalogo encendido)")
    ap.add_argument("--rivales", default=None,
                    help="rival_intelligence.json del mismo artefacto: las 8 plantillas")
    args = ap.parse_args()

    calendario = leer(CALENDARIO)["matches"]
    nombres = sorted({m["home"] for m in calendario} | {m["away"] for m in calendario})
    tarde_foto = leer(TARDE)
    casados = casar_equipos(tarde_foto["catalog"]["data"]["teams"], nombres)
    puesto = puestos(leer(CLASIFICACION), nombres)

    print("=" * 78)
    print("EL ONCE OBJETIVO - medicion de solo lectura")
    print("=" * 78)
    print(f"equipos casados con el calendario: {len(set(casados.values()))}/20;"
          f" con la clasificacion: {len(puesto)}/20")

    # ---------------- BLOQUE 1 ----------------
    partidos, cuenta, catalogo, validados = los_partidos(QUIETA, TARDE, calendario, casados, puesto)
    print()
    print("BLOQUE 1 - EL CALENDARIO, EN DESVIACION SOBRE LA MEDIA PROPIA")
    print(f"  jugadores: {dict(cuenta)}")
    print(f"  partidos jugados reconstruidos: {len(partidos)}, "
          f"jornadas {sorted({p['jornada'] for p in partidos})}")

    efecto = desviacion_por_contexto(partidos)
    for clave in ("todas", "1", "2", "3", "4"):
        bloque = efecto.get(clave) or {}
        nombre = "TODAS" if clave == "todas" else POS[int(clave)]
        print(f"  {nombre}")
        for ctx in ("casa", "fuera", "rival_alto", "rival_bajo", "casa_y_rival_bajo"):
            d = bloque[ctx]["desviacion"]
            b = bloque[ctx]["bruto"]
            print(f"    {ctx:18s} desv {d['media']:+.2f} +-{d['ic95'] or 0:.2f}  "
                  f"n={d['n']:4d} ({bloque[ctx]['jugadores']} jug) | bruto {b['media']:.2f}")

    print("  casa/fuera EXACTO por totales del catalogo del 19/09 (todos los partidos):")
    for pos, r in casa_por_totales(catalogo).items():
        nombre = "TODAS" if pos == "todas" else POS[pos]
        print(f"    {nombre:5s} casa {r['casa']:+.3f} (n={r['n_casa']})  "
              f"fuera {r['fuera']:+.3f} (n={r['n_fuera']})")

    var_dentro = varianza_dentro(partidos)
    print(f"  varianza de un partido sobre la media propia: "
          f"{ {POS[k]: round(v, 2) for k, v in sorted(var_dentro.items())} }")

    # ---------------- DATOS DEL PANEL ----------------
    panel = leer(args.panel)
    en = datetime.fromisoformat(
        str(panel.get("meta", {}).get("generated_at") or "2026-09-26T08:10:00+02:00")
    )
    if en.tzinfo is None:
        en = en.replace(tzinfo=MADRID)
    jugadores = [
        {
            "id": int(j["id"]), "name": j["name"], "position": int(j["position"]),
            "team_id": int(j.get("team_id") or 0), "points": int(j.get("points") or 0),
            "played": int(j.get("played") or 0), "price": int(j.get("price") or 0),
            "de_quien": j.get("de_quien"), "status": j.get("status"),
        }
        for j in panel["todaLaLiga"]["players"]
        if int(j.get("position") or 0) in POS
    ]
    por_equipo = {
        tid: len(partidos_del_equipo(calendario, nombre, antes=en))
        for tid, nombre in casados.items()
    }

    # ---------------- BLOQUE 2 ----------------
    board = leer(args.ff)
    ff = {
        int(r["player_id"]): float(r["starter_probability"])
        for r in board.get("players") or []
        if r.get("player_id") is not None and r.get("starter_probability") is not None
    }
    print()
    print("BLOQUE 2 - TITULARIDAD")
    print(f"  FutbolFantasy (tablero del {board.get('updated_at', '')[:10]}, "
          f"para la J{board.get('matchday')}): {len(ff)} de {len(jugadores)} con probabilidad")
    pares = []
    for j in jugadores:
        if j["id"] in ff and j["team_id"] in por_equipo:
            tasa = min(j["played"] / max(por_equipo[j["team_id"]], 1), 1.0)
            pares.append((tasa, ff[j["id"]] / 100.0))
    xs, ys = [a for a, _ in pares], [b for _, b in pares]
    acuerdo = sum(1 for a, b in pares if (a >= 0.5) == (b >= 0.5))
    print(f"  la barata (jugados / partidos de su equipo) contra FF, n={len(pares)}:")
    print(f"    Pearson {correlacion(xs, ys)}  Spearman {correlacion(rangos(xs), rangos(ys))}  "
          f"error medio {sum(abs(a - b) for a, b in pares) / len(pares):.3f}  "
          f"coinciden en >=50 %: {acuerdo}/{len(pares)}")
    nuestros_ff = [j for j in jugadores if j["de_quien"] == "nuestro" and j["id"] in ff]
    cambia_nuestros = sum(
        1 for j in nuestros_ff
        if (min(j["played"] / max(por_equipo.get(j["team_id"], 1), 1), 1.0) >= 0.5)
        != (ff[j["id"]] >= 50)
    )
    print(f"  LA ETIQUETA DE TITULAR (>= 50 %), barata contra FF: cambia a "
          f"{len(pares) - acuerdo} de {len(pares)}; de los nuestros, a "
          f"{cambia_nuestros} de {len(nuestros_ff)}")

    # ---------------- EFECTOS DEL CALENDARIO SOBRE LOS PROXIMOS ----------------
    pos_ef = {}
    for pos in (1, 2, 3, 4):
        b = efecto.get(str(pos)) or {}
        pos_ef[pos] = {
            ctx: (b.get(ctx, {}).get("desviacion", {}).get("media") or 0.0)
            for ctx in ("casa", "fuera", "rival_alto", "rival_bajo")
        }
    # LOS PORTEROS NO ENTRAN (26/09): n = 56 y el signo al reves que
    # el resto, dentro del ruido (+-0,84). Un efecto que puede
    # significar cualquier cosa vale lo mismo que ninguno (doctrina 91).
    pos_ef[1] = {ctx: 0.0 for ctx in pos_ef[1]}
    print()
    print("  EL CALENDARIO NO SE APLICA A LOS PORTEROS: n=56, signo al reves, "
          "dentro del ruido.")
    efectos = {}
    for tid, nombre in casados.items():
        resto = [m for m in calendario if nombre in (m["home"], m["away"]) and cuando(m) > en]
        resto.sort(key=cuando)
        for pos in (1, 2, 3, 4):
            def ajuste(m):
                casa = m["home"] == nombre
                rival = m["away"] if casa else m["home"]
                alto = (puesto.get(rival) or 99) <= 10
                e = pos_ef[pos]
                return (e["casa"] if casa else e["fuera"]) + (e["rival_alto"] if alto else e["rival_bajo"])
            efectos[(pos, tid)] = {
                "temporada": sum(ajuste(m) for m in resto) / len(resto) if resto else 0.0,
                "jornada": ajuste(resto[0]) if resto else 0.0,
            }

    tabla, medias, ks = valores(jugadores, por_equipo, var_dentro, ff, efectos, None)
    por_id = {j["id"]: j for j in tabla}
    print()
    print("BLOQUE 3 - LOS ONCES")
    print(f"  media por partido jugado, por posicion: { {POS[k]: round(v, 2) for k, v in medias.items()} }")
    print(f"  k sacado de los datos: { {POS[k]: v for k, v in ks.items()} }  (el dueño: 3)")

    A = [j for j in tabla if j["de_quien"] == "nuestro"]
    B = A + [j for j in tabla if j["de_quien"] == "computer"]
    C = B + [j for j in tabla if j["de_quien"] == "libre"]
    L = tabla

    onces = {}
    sin_filtro = {}
    for nombre, universo in (("A", A), ("B", B), ("C", C), ("LIGA", L)):
        for metodo in ("valor", "valor_cal", "duenio"):
            onces[(nombre, metodo)] = el_mejor_once(universo, metodo)
        sin_filtro[nombre] = el_mejor_once(universo, "valor", fuera=frozenset())
    onces[("A", "jornada")] = el_mejor_once(A, "jornada")
    onces[("A", "jornada_cal")] = el_mejor_once(A, "jornada_cal")

    for nombre in ("A", "B", "C", "LIGA"):
        print()
        pinta_once(f"{nombre} - metodo nuevo, SIN lesionados", onces[(nombre, "valor")], por_id, "valor")
        o, d = onces[(nombre, "valor")], onces[(nombre, "duenio")]
        fuera = [por_id[i]["name"] for i in d["ids"] if i not in o["ids"]]
        dentro = [por_id[i]["name"] for i in o["ids"] if i not in d["ids"]]
        print(f"    metodo del dueño: {d['formacion']} suma {d['suma']:.2f} pts/partido jugado; "
              f"el nuevo saca {fuera} y mete {dentro}")
        rivales = sum(1 for i in o["ids"] if por_id[i]["de_quien"] == "rival")
        comprar = sum(por_id[i]["precio"] for i in o["ids"] if por_id[i]["de_quien"] != "nuestro")
        print(f"    de rivales {rivales}/11; precio de lo que no es nuestro {euros(comprar)}")
        sf = sin_filtro[nombre]
        salen = [f"{por_id[i]['name']} ({por_id[i]['status']})" for i in sf["ids"] if i not in o["ids"]]
        entran = [por_id[i]["name"] for i in o["ids"] if i not in sf["ids"]]
        cambio = "no cambia" if not salen else f"salen {salen}, entran {entran}"
        print(f"    AL FILTRAR: suma {sf['suma']:.2f} -> {o['suma']:.2f}; {cambio}")

    # ---------------- LOS VIGILADOS ----------------
    print()
    print("  VIGILADOS: no disponibles hoy que entrarian en algun once si volvieran")
    vistos = set()
    for nombre in ("B", "C"):
        for i in sin_filtro[nombre]["ids"]:
            jx = por_id[i]
            if jx["status"] in FUERA and i not in vistos:
                vistos.add(i)
                print(f"      {nombre} {POS[jx['posicion']]} {jx['name']:18s} {jx['status']:10s} "
                      f"{jx['de_quien']:8s} valor {jx['valor']:.2f}  {euros(jx['precio'])}")
    cola = []
    base = el_mejor_once(A, "valor", fuera=frozenset())
    for jx in [j for j in tabla if j["de_quien"] == "computer"]:
        otro = el_mejor_once(A + [jx], "valor", fuera=frozenset())
        gana = otro["suma"] - base["suma"]
        if gana > 1e-9:
            cola.append((gana / (jx["precio"] / 1e6), gana, jx))
    cola.sort(key=lambda t: -t[0])
    print("  LA COLA DEL COMPUTER, si todos estuvieran disponibles (compra sola, sobre A):")
    for k, (por_m, gana, jx) in enumerate(cola, 1):
        marca = "VIGILADO" if jx["status"] in FUERA else ("duda" if jx["status"] == "doubt" else "")
        print(f"      {k}. {jx['name']:18s} +{gana:.3f}/jornada  {por_m:.3f} por M  "
              f"{euros(jx['precio'])}  {jx['status']} {marca}")

    print()
    print("  ¿CAMBIA ALGUN NOMBRE CON EL CALENDARIO? (porteros fuera)")
    for nombre in ("A", "B", "C", "LIGA"):
        a, b = onces[(nombre, "valor")], onces[(nombre, "valor_cal")]
        cambia = sorted(set(a["ids"]) ^ set(b["ids"]))
        print(f"    {nombre:4s} temporada: {'NO' if not cambia else [por_id[i]['name'] for i in cambia]}"
              f"  (formacion {a['formacion']} -> {b['formacion']})")
    a, b = onces[("A", "jornada")], onces[("A", "jornada_cal")]
    cambia = sorted(set(a["ids"]) ^ set(b["ids"]))
    print(f"    A    JORNADA 8: {'NO' if not cambia else [por_id[i]['name'] for i in cambia]}"
          f"  (formacion {a['formacion']} -> {b['formacion']}, suma {a['suma']:.2f} -> {b['suma']:.2f})")
    pinta_once("A - once de la JORNADA 8", onces[("A", "jornada")], por_id, "jornada")

    # ---------------- EL CALENDARIO EN LOS ONCES DE JORNADA YA JUGADOS ----------------
    if args.rivales:
        plantillas = {
            str(m.get("name") or m.get("user_id")): [int(x["id"]) for x in (m.get("roster") or [])]
            for m in (leer(args.rivales).get("managers") or [])
        }
        jugo = collections.defaultdict(dict)
        for pt in partidos:
            jugo[pt["jugador"]][pt["jornada"]] = pt["puntos"]
        fin = foto_en(TARDE)
        print()
        print(f"  EL CALENDARIO EN EL ONCE DE LA JORNADA, jornadas 1-5, "
              f"con las {len(plantillas)} plantillas de HOY (hipotetico)")
        n_onces = cambios = sin_dato = 0
        ganado = 0.0
        detalle = []
        for jornada in range(1, 6):
            for duenio, ids in plantillas.items():
                filas = []
                for pid in ids:
                    jx = por_id.get(pid)
                    if not jx:
                        continue
                    equipo = casados.get(jx["team_id"])
                    partido = next((m for m in calendario if m["matchday"] == jornada
                                    and equipo in (m["home"], m["away"])), None)
                    if not partido or cuando(partido) + DURA > fin:
                        continue
                    casa = partido["home"] == equipo
                    rival = partido["away"] if casa else partido["home"]
                    alto = (puesto.get(rival) or 99) <= 10
                    e = pos_ef[jx["posicion"]]
                    aj = (e["casa"] if casa else e["fuera"]) + (e["rival_alto"] if alto else e["rival_bajo"])
                    filas.append({**jx, "status": "ok", "b": jx["valor"],
                                  "c": jx["tasa"] * (jx["ppg_encogida"] + aj)})
                sin = el_mejor_once(filas, "b")
                con = el_mejor_once(filas, "c")
                if not sin["lleno"]:
                    continue
                n_onces += 1
                dif = set(sin["ids"]) ^ set(con["ids"])
                if not dif:
                    continue
                cambios += 1

                def pts(i, jornada=jornada):
                    if i not in validados:
                        return None
                    return jugo[i].get(jornada, 0.0)

                if any(pts(i) is None for i in dif):
                    sin_dato += 1
                    continue
                g = (sum(pts(i) for i in con["ids"] if i not in sin["ids"])
                     - sum(pts(i) for i in sin["ids"] if i not in con["ids"]))
                ganado += g
                detalle.append((jornada, duenio,
                                [por_id[i]["name"] for i in con["ids"] if i not in sin["ids"]],
                                [por_id[i]["name"] for i in sin["ids"] if i not in con["ids"]], g))
        print(f"    onces de jornada evaluados: {n_onces}; cambian con el calendario: {cambios}; "
              f"sin dato de puntos: {sin_dato}")
        print(f"    puntos de mas que habrian dado esos cambios: {ganado:+.0f} "
              f"(en {len(detalle)} onces con dato)")
        for jd, du, mete, saca, g in detalle:
            print(f"      J{jd} {du[:14]:14s} mete {mete} saca {saca}: {g:+.0f}")

    # ---------------- EL PLAN ----------------
    posiciones = leer(POSICIONES).get("positions") or []
    pujas = (leer(PUJAS).get("bids") or {}).values()
    coste = {}
    for b in sorted(pujas, key=lambda b: str(b.get("resolved_at") or "")):
        if b.get("outcome") == "WON" and b.get("winning_amount"):
            coste[int(b["player_id"])] = int(b["winning_amount"])
    for p in posiciones:
        if p.get("status") == "OPEN_POSITION" and p.get("entry_price"):
            coste[int(p["player_id"])] = int(p["entry_price"])

    ofertas = {}
    for o in panel.get("offers") or []:
        if o.get("counterparty") != "COMPUTER" or len(o.get("player_ids") or []) != 1:
            continue
        pid = int(o["player_ids"][0])
        if pid in por_id and por_id[pid]["de_quien"] == "nuestro":
            ofertas[pid] = {"importe": int(o["amount"]), "coste": coste.get(pid)}

    saldo = int((panel.get("summary") or {}).get("balance") or 0)
    # CON EL SALDO EN ROJO, UNA VENTA NO LLEGA A LA CAJA (26/09): la caja
    # es el margen de deuda, y la venta baja la deuda y la garantia lo
    # mismo. Medido la noche del 25/09: +3.670.800 por ventas y la caja
    # bajo de 3.575.478 a 1.356.676.
    llega = {pid: 0 for pid in ofertas} if saldo < 0 else None

    yamal = {j["id"] for j in A if j["name"] == YAMAL}
    fichas = TOPE_DE_FICHAS - len(A)
    comprables = [j for j in B if j["de_quien"] == "computer"]
    print()
    print("EL PLAN hacia C, con lo que se puede comprar HOY (el mercado del Computer)")
    print(f"  saldo {euros(saldo)}, caja {euros(CAJA_DE_FICHAR)}, fichas libres {fichas}, "
          f"ofertas en firme {len(ofertas)} (con coste conocido "
          f"{sum(1 for o in ofertas.values() if o['coste'] is not None)})")
    for titulo, llega_caja in (("con lo que LLEGA de verdad a la caja (en rojo: nada)", llega),
                               ("con el supuesto de antes (la venta llega entera)", None)):
        plan = el_plan(A, comprables, ofertas, CAJA_DE_FICHAR, fichas,
                       no_se_vende=yamal, llega_a_la_caja=llega_caja)
        print(f"  {titulo}:")
        if not plan["pasos"]:
            print("    NINGUN PASO sube el once dentro de la caja y las fichas.")
        for k, p in enumerate(plan["pasos"], 1):
            vende = f"vende {por_id[p['vende']]['name']} y " if p["vende"] else ""
            print(f"    {k}. {vende}compra {por_id[p['compra']]['name']} por {euros(p['precio'])}: "
                  f"+{p['gana']:.3f} pts/jornada, neto {euros(p['neto'])}, "
                  f"caja despues {euros(p['caja_despues'])}")
        print(f"    escrituras: {plan['escrituras']}; once "
              f"{onces[('A', 'valor')]['suma']:.2f} -> {(plan['once_final'] or {}).get('suma')}")

    sin_caja = el_plan(A, comprables, ofertas, 10**10, fichas, no_se_vende=yamal)
    print(f"  sin tope de caja: {[por_id[p['compra']]['name'] for p in sin_caja['pasos']]}, once "
          f"{onces[('A', 'valor')]['suma']:.2f} -> {(sin_caja['once_final'] or {}).get('suma')}")

    faltan = [por_id[i] for i in onces[("C", "valor")]["ids"] if por_id[i]["de_quien"] == "libre"]
    print(f"  del once C, {len(faltan)} son LIBRES: hay que esperar a que el Computer los saque:")
    for jx in sorted(faltan, key=lambda j: -j["valor"]):
        print(f"      {POS[jx['posicion']]} {jx['name']:20s} valor {jx['valor']:.2f}  {euros(jx['precio'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
