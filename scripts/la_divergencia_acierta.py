"""
¿Acierta el libro de la divergencia? Corrido contra los libros de esta casa.

QUE LIBROS LEE

    data/intelligence/divergence_ledger.json      el libro que se mide
    data/intelligence/scout_accuracy_ledger.json  el pulso, fuente a fuente
    data/trading/libro_del_escaparate.jsonl       el mercado libre del dia
    data/intelligence/libro_de_la_valoracion.jsonl  lo que ponen los rivales
    data/solvency/bitacora_del_saldo.jsonl        la puja maxima de cada momento
    data/trading/position_ledger.json             cuando entraron Ceballos y Unai

    Con `--rev REV` los lee de esa revision de git (`git show`), sin
    tocar el arbol. Sin el, del disco. EL INFORME DEL 25/09 ESTA
    CORRIDO CON `--rev 92b65ae0`: con otra revision los numeros
    cambian, porque el libro sigue llenandose.

QUE HACE

    BLOQUE 1   que hay en el libro: filas, cerradas, divergentes, y
               la auditoria del cierre y de la demanda.
    BLOQUE 2   si acierta la direccion, a 7 y a 3 dias, contra el
               mercado del mismo dia y contra seguir la tendencia;
               partido por tipo y por tamaño del movimiento.
    BLOQUE 3   la cuenta de comprar a los señalados al alza, contra
               el mercado de las mismas fechas y contra los que
               tambien bajaron ayer; y cuantos eran comprables.
    BLOQUE 4   Ceballos y Unai Lopez, dia a dia.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende nada
    y NO ESCRIBE NI UNA LINEA DE NINGUN LIBRO.

USO

    python scripts/la_divergencia_acierta.py --rev 92b65ae0 > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import argparse
import bisect
import json
import random
import statistics
import subprocess
import sys

from collections import Counter, defaultdict
from datetime import datetime


DIVERGENCIA = "data/intelligence/divergence_ledger.json"
ACIERTOS = "data/intelligence/scout_accuracy_ledger.json"
ESCAPARATE = "data/trading/libro_del_escaparate.jsonl"
VALORACION = "data/intelligence/libro_de_la_valoracion.jsonl"
SALDO = "data/solvency/bitacora_del_saldo.jsonl"
POSICIONES = "data/trading/position_ledger.json"


# Lo que cada tipo de divergencia afirma sin decirlo: que el precio
# va a seguir a la demanda y no a su propia rampa. El libro no lo
# llama prediccion en ningun sitio; es la hipotesis de su cabecera.
PREDICE = {
    "PRECIO_BAJA_DEMANDA_SUBE": 1,
    "PRECIO_SUBE_DEMANDA_BAJA": -1,
}

AL_ALZA = "PRECIO_BAJA_DEMANDA_SUBE"

CEBALLOS = "2044"
UNAI_LOPEZ = "1969"


def leer(ruta: str, rev: str | None) -> str:
    if rev is None:
        with open(ruta, encoding="utf-8-sig") as fichero:
            return fichero.read()

    salida = subprocess.run(
        ["git", "show", f"{rev}:{ruta}"],
        capture_output=True,
        check=True,
    )

    return salida.stdout.decode("utf-8-sig")


def leer_json(ruta, rev):
    return json.loads(leer(ruta, rev))


def leer_jsonl(ruta, rev):
    return [
        json.loads(linea)
        for linea in leer(ruta, rev).splitlines()
        if linea.strip()
    ]


def signo(x) -> int:
    return (x > 0) - (x < 0)


def mediana(valores):
    return round(statistics.median(valores), 2) if valores else None


def pct(a, b) -> str:
    return f"{100 * a / b:5.1f} %" if b else "   -   "


def jugadores(grupo) -> int:
    return len({f["player_id"] for f in grupo})


# ============================================================
# BLOQUE 1
# ============================================================


def bloque_1(filas, aciertos):

    print("=" * 72)
    print("BLOQUE 1 — QUE HAY EN EL LIBRO")
    print("=" * 72)

    cerradas = [f for f in filas if f["outcome"] == "CLOSED"]

    print(f"apuntadas {len(filas)}   cerradas {len(cerradas)}   "
          f"divergentes (todas las fechas) {sum(f['divergent'] for f in filas)}")

    print("cerradas por tipo:", dict(Counter(
        f["divergence_kind"] or "no divergente (control)" for f in cerradas
    )))

    print("dias apuntados:", len({f["day"] for f in filas}),
          f"({min(f['day'] for f in filas)} .. {max(f['day'] for f in filas)})")

    edades = Counter(
        round((datetime.fromisoformat(f["resolved_at"])
               - datetime.fromisoformat(f["seen_at"])).total_seconds() / 86400)
        for f in cerradas
    )
    print("edad al cerrar, en dias:", dict(edades))

    print(f"con demanda medida: {sum(f['demand_net'] is not None for f in filas)} "
          f"de {len(filas)}")

    # LA FOTO REPETIDA
    #
    #     Si el ojeador no refresca entre dos dias, el libro apunta
    #     la misma foto dos veces con fechas distintas.
    por_dia = defaultdict(dict)
    for f in filas:
        por_dia[f["day"]][f["player_id"]] = (f["price"], f["price_change_percent"])

    dias = sorted(por_dia)
    for ayer, hoy in zip(dias, dias[1:]):
        comunes = set(por_dia[ayer]) & set(por_dia[hoy])
        iguales = sum(por_dia[ayer][k] == por_dia[hoy][k] for k in comunes)
        if comunes and iguales == len(comunes):
            print(f"FOTO REPETIDA: {hoy} es copia exacta de {ayer} "
                  f"({iguales} de {len(comunes)} filas)")

    # EL PULSO CONGELADO
    valores = defaultdict(set)
    for f in filas:
        if f["demand_net"] is not None:
            valores[f["player_id"]].add(f["demand_net"])

    print(f"jugadores con pulso: {len(valores)}; con UN SOLO valor en todo "
          f"el libro: {sum(len(v) == 1 for v in valores.values())}")

    # Y en la fuente, no en el libro: en la misma respuesta de
    # Comuniate el precio cambia cada dia y el pulso no.
    pulso = defaultdict(set)
    for p in aciertos:
        if p.get("source") == "COMUNIATE_PULSO":
            pulso[p["player_id"]].add(p.get("magnitude_percent"))

    print(f"en `scout_accuracy_ledger` (COMUNIATE_PULSO): {len(pulso)} jugadores, "
          f"{sum(len(v) == 1 for v in pulso.values())} con un solo valor")

    for nombre in ("Robbie Ure", "Konaté", "Dolan"):
        serie = sorted(
            (f for f in filas if f["player_name"] == nombre),
            key=lambda f: f["seen_at"],
        )
        if serie:
            print(f"  {nombre:11s} pulso {sorted({f['demand_net'] for f in serie if f['demand_net'] is not None})}"
                  f"  precio {serie[0]['price']} -> {serie[-1]['price']}"
                  f"  ({len(serie)} dias)")

    return valores


# ============================================================
# BLOQUE 2 Y 3
# ============================================================


def mercado_del_dia(filas, clave):
    mercado = defaultdict(list)
    for f in filas:
        if f.get(clave) is not None:
            mercado[f["day"]].append(f)
    return mercado


def linea_acierto(nombre, grupo, clave, mercado, medianas):

    n = len(grupo)

    if not n:
        print(f"  {nombre:40s} n=   0")
        return

    acierta = sum(signo(f[clave]) == PREDICE[f["divergence_kind"]] for f in grupo)
    falla = sum(signo(f[clave]) == -PREDICE[f["divergence_kind"]] for f in grupo)

    # CONTROL A: el mercado entero del mismo dia, con la misma
    # direccion predicha. Es lo que acertaria cualquiera.
    a_acierta = a_n = 0
    for f in grupo:
        for otro in mercado[f["day"]]:
            a_n += 1
            a_acierta += signo(otro[clave]) == PREDICE[f["divergence_kind"]]

    # CONTROL B: seguir la tendencia. En un divergente es, por
    # construccion, lo contrario de lo que dice la divergencia.
    b_acierta = sum(
        signo(f[clave]) == signo(f["price_change_percent"]) for f in grupo
    )

    exceso = [f[clave] - medianas[f["day"]] for f in grupo]

    print(f"  {nombre:40s} n={n:4d} jug={jugadores(grupo):3d}  "
          f"acierta {pct(acierta, n)}  falla {pct(falla, n)}  "
          f"| A mercado {pct(a_acierta, a_n)}  | B tendencia {pct(b_acierta, n)}  "
          f"| mov mediano {mediana([f[clave] for f in grupo]):+6.2f} %  "
          f"exceso {mediana(exceso):+6.2f} pp")


def linea_compra(nombre, grupo, clave):

    v = [f[clave] for f in grupo]

    if not v:
        print(f"  {nombre:48s} n=    0")
        return

    print(f"  {nombre:48s} n={len(v):5d}  subieron {pct(sum(x > 0 for x in v), len(v))}  "
          f"mediana {mediana(v):+6.2f} %  peor {min(v):+7.2f} %  mejor {max(v):+7.2f} %")


def bloques_2_y_3(filas, valores_pulso, dias_plazo):

    clave = f"return_{dias_plazo}d_percent"
    mercado = mercado_del_dia(filas, clave)
    medianas = {
        d: statistics.median([f[clave] for f in g]) for d, g in mercado.items()
    }

    con_dato = [f for f in filas if f[clave] is not None]
    div = [f for f in con_dato if f["divergent"]]

    print()
    print("=" * 72)
    print(f"BLOQUE 2 — ¿ACIERTA LA DIRECCION?  PLAZO {dias_plazo} DIAS")
    print("=" * 72)

    v = [f[clave] for f in con_dato]
    print(f"mercado entero: n={len(v)}  mediana {mediana(v):+.2f} %  "
          f"subieron {pct(sum(x > 0 for x in v), len(v))}  "
          f"bajaron {pct(sum(x < 0 for x in v), len(v))}")

    linea_acierto("todas las divergentes", div, clave, mercado, medianas)
    for tipo in PREDICE:
        linea_acierto(tipo, [f for f in div if f["divergence_kind"] == tipo],
                      clave, mercado, medianas)

    print("  por tamaño del movimiento realizado:")
    linea_acierto("grandes  |mov| > 5 %", [f for f in div if abs(f[clave]) > 5],
                  clave, mercado, medianas)
    linea_acierto("medios   1-5 %", [f for f in div if 1 <= abs(f[clave]) <= 5],
                  clave, mercado, medianas)
    linea_acierto("pequeños |mov| < 1 %", [f for f in div if abs(f[clave]) < 1],
                  clave, mercado, medianas)
    for tipo in PREDICE:
        linea_acierto(f"{tipo}, > 5 %",
                      [f for f in div if f["divergence_kind"] == tipo and abs(f[clave]) > 5],
                      clave, mercado, medianas)

    movidos = [f for f in con_dato if f["price_change_percent"] != 0]
    print(f"  control B en TODO el libro ({len(movidos)} filas con precio movido ayer): "
          f"seguir la tendencia acierta "
          f"{pct(sum(signo(f[clave]) == signo(f['price_change_percent']) for f in movidos), len(movidos))}")

    print("  robustez:")
    for tipo in PREDICE:
        g = [f for f in div if f["divergence_kind"] == tipo]
        linea_acierto(f"{tipo[:24]}, sin el 06/09",
                      [f for f in g if f["day"] != "2026-09-06"],
                      clave, mercado, medianas)
        linea_acierto(f"{tipo[:24]}, pulso que SI cambia",
                      [f for f in g if len(valores_pulso[f["player_id"]]) > 1],
                      clave, mercado, medianas)
        primera = {}
        for f in sorted(g, key=lambda f: f["seen_at"]):
            primera.setdefault(f["player_id"], f)
        linea_acierto(f"{tipo[:24]}, una por jugador",
                      list(primera.values()), clave, mercado, medianas)

    print()
    print("=" * 72)
    print(f"BLOQUE 3 — SI HUBIERAMOS COMPRADO A LOS SEÑALADOS AL ALZA.  PLAZO {dias_plazo} DIAS")
    print("=" * 72)

    al_alza = [f for f in div if f["divergence_kind"] == AL_ALZA]
    dias = Counter(f["day"] for f in al_alza)

    linea_compra("señalados al alza", al_alza, clave)

    # Ponderado por cuantos señalados hubo cada dia: el mismo
    # periodo, exactamente.
    linea_compra("mercado, mismas fechas (ponderado)",
                 [o for d, c in dias.items() for o in mercado[d] for _ in range(c)],
                 clave)

    # EL CONTROL JUSTO: los que TAMBIEN bajaron ayer. Lo unico que
    # les falta es la demanda a favor.
    bajaron = [o for d in dias for o in mercado[d]
               if o["price_change_percent"] < 0 and not o["divergent"]]
    linea_compra("bajaron ayer, mismos dias, no divergentes", bajaron, clave)

    a_la_baja = [f for f in div if f["divergence_kind"] != AL_ALZA]
    dias_baja = Counter(f["day"] for f in a_la_baja)
    linea_compra("señalados a la baja (SUBE_DEMANDA_BAJA)", a_la_baja, clave)
    linea_compra("subieron ayer, mismos dias, no divergentes",
                 [o for d in dias_baja for o in mercado[d]
                  if o["price_change_percent"] > 0 and not o["divergent"]],
                 clave)
    linea_compra("  SUBE_DEMANDA_BAJA con racha >= 3 (regla 3)",
                 [f for f in a_la_baja if (f["trend_days"] or 0) >= 3], clave)
    linea_compra("  racha >= 3 sin demanda en contra, mismos dias",
                 [o for d in dias_baja for o in mercado[d]
                  if (o["trend_days"] or 0) >= 3 and not o["divergent"]],
                 clave)

    # EXCESO SOBRE EL MERCADO, CON EL JUGADOR COMO UNIDAD
    #
    #     Ocho jugadores salen todos los dias. Remuestrear filas
    #     trataria doce dias de Konaté como doce observaciones.
    exceso = defaultdict(list)
    for f in al_alza:
        exceso[f["player_id"]].append(f[clave] - medianas[f["day"]])

    ids = sorted(exceso)
    azar = random.Random(7)
    medias = sorted(
        statistics.mean([x for j in azar.choices(ids, k=len(ids)) for x in exceso[j]])
        for _ in range(4000)
    )
    todos = [x for v in exceso.values() for x in v]
    print(f"  exceso medio sobre la mediana del mercado del dia: "
          f"{statistics.mean(todos):+.2f} pp, IC 95 % por jugador "
          f"{medias[100]:+.2f} .. {medias[3899]:+.2f}  "
          f"(n={len(todos)} filas, {len(ids)} jugadores, {len(dias)} dias); "
          f"baten al mercado {pct(sum(x > 0 for x in todos), len(todos))}")


# ============================================================
# COMPRABLES Y LOS DOS CASOS
# ============================================================


def comprables(filas, escaparate, valoracion, saldo):

    print()
    print("=" * 72)
    print("BLOQUE 3 — ¿CUANTOS SEÑALADOS AL ALZA ERAN COMPRABLES ESE DIA?")
    print("=" * 72)

    libre = {e["dia_de_mercado"]: {str(p["id"]) for p in e["players"]}
             for e in escaparate}
    # LA COTA GENEROSA
    #
    #     El escaparate y la valoracion son fotos de momentos
    #     distintos del dia: Mangala sale del Computer en la
    #     valoracion del 23/09 y no en el escaparate. Cuenta como a
    #     la venta el que salga en cualquiera de los dos.
    rivales = defaultdict(set)
    for v in valoracion:
        rivales[v["dia"]].add(str(v["id"]))

    momentos = sorted((s["at"], s.get("maximum_bid")) for s in saldo)
    marcas = [m[0] for m in momentos]

    def puja_maxima(dia):
        i = bisect.bisect_right(marcas, f"{dia}T23:59") - 1
        return momentos[i][1] if i >= 0 else None

    al_alza = [f for f in filas if f["divergence_kind"] == AL_ALZA]
    total = en_mercado = dentro = 0

    for dia in sorted(libre):
        g = [f for f in al_alza if f["day"] == dia]
        a_la_venta = libre[dia] | rivales.get(dia, set())
        vistos = [f for f in g if f["player_id"] in a_la_venta]
        tope = puja_maxima(dia)
        caben = [f for f in vistos if tope is not None and f["price"] <= tope]

        total += len(g)
        en_mercado += len(vistos)
        dentro += len(caben)

        print(f"  {dia}  señalados {len(g):3d}  a la venta {len(vistos)}  "
              f"dentro de la puja maxima ({tope}) {len(caben)}  "
              f"[escaparate {len(libre[dia])}, valoracion {len(rivales.get(dia, ()))}]  "
              + ", ".join(f"{f['player_name']} {f['price']}" for f in vistos))

    print(f"  TOTAL {min(libre)} .. {max(libre)}: {total} señales al alza, "
          f"{en_mercado} a la venta ese dia, {dentro} dentro de la puja maxima")
    print("  (el escaparate empieza el 17/09 y la valoracion, con los rivales, "
          "el 23/09: antes no hay registro del mercado)")


def los_dos_casos(filas, posiciones):

    print()
    print("=" * 72)
    print("BLOQUE 4 — CEBALLOS Y UNAI LOPEZ")
    print("=" * 72)

    for p in posiciones.get("positions") or []:
        if str(p.get("player_id")) in (CEBALLOS, UNAI_LOPEZ):
            print(f"  posicion {p['player_id']}: puja creada {p.get('created_at')}  "
                  f"abierta {p.get('opened_at')}  entrada {p.get('entry_price')}")

    for pid in (CEBALLOS, UNAI_LOPEZ):
        for f in sorted((f for f in filas if f["player_id"] == pid),
                        key=lambda f: f["seen_at"]):
            print(f"  {f['player_name']:11s} {f['seen_at'][:16]}  precio {f['price']:>9}  "
                  f"ayer {f['price_change_percent']:+7.3f} %  racha {f['trend_days']}  "
                  f"pulso {f['demand_net']}  {f['divergence_kind'] or '-'}  "
                  f"a 7 dias {f['return_7d_percent']}")


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument("--rev", default=None,
                        help="revision de git de la que leer los libros")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    print(f"libros leidos de: {args.rev or 'el disco'}")

    filas = list(leer_json(DIVERGENCIA, args.rev)["observations"].values())
    for f in filas:
        f["day"] = f["seen_at"][:10]

    aciertos = list(leer_json(ACIERTOS, args.rev)["predictions"].values())

    valores_pulso = bloque_1(filas, aciertos)

    for dias in (7, 3):
        bloques_2_y_3(filas, valores_pulso, dias)

    comprables(
        filas,
        leer_jsonl(ESCAPARATE, args.rev),
        leer_jsonl(VALORACION, args.rev),
        leer_jsonl(SALDO, args.rev),
    )

    los_dos_casos(filas, leer_json(POSICIONES, args.rev))

    return 0


if __name__ == "__main__":
    sys.exit(main())
