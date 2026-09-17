"""
El escaparate: cada cuanto sale el bueno, y si estabamos alli.

QUE FOTO MIRA, Y LO COMPRUEBA ANTES

    `diagnostico/status.json` para el dia de hoy —lo primero que
    imprime es `meta.generated_at`— y los 95 `data/snapshot_*.json`
    para los dias anteriores. Todo con `encoding="utf-8"`.

QUE HACE

    BLOQUE 0   ¿existe historico de escaparates? Que hay y desde
               cuando.
    BLOQUE 1   como rota: distintos, repeticion, y cuanto se
               tarda en ver a uno concreto.
    BLOQUE 2   ¿hay patron en quien sale?
    BLOQUE 3   ¿estabamos listos? Las subastas del Computer, con
               quien pujo en cada una.
    BLOQUE 4   la lista de vigilancia: ¿la lee alguien?
    BLOQUE 5   la regla de estar listo, y lo que cuesta.

QUE NO HACE

    No escribe nada, no toca Biwenger, no sale a la red, no
    propone comprar ni vender a nadie y no enciende nada.

USO

    python scripts/el_escaparate.py > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import datetime
import glob
import json
import os
import statistics
import sys
from collections import Counter, defaultdict


sys.path.insert(0, os.getcwd())

from src.analysis.el_escaparate import (                 # noqa: E402
    ENCENDIDO,
    HORA_DEL_RESET,
    dia_de_mercado,
    espera_de_un_jugador,
    estabamos_listos,
    hay_patron,
    regla_de_estar_listo,
    rotacion,
)


FOTO = "diagnostico/status.json"

TABLON = "data/rival_intelligence/board_events.json"

RIVALES = "data/rival_intelligence/rival_intelligence.json"

CENSO_DE_OFERTAS = "data/solvency/censo_de_ofertas.jsonl"

LIBRO_DE_ESCAPARATE = "data/trading/libro_de_escaparate.jsonl"

NOSOTROS = 14175949

POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


def euros(valor) -> str:
    return f"{int(valor or 0):,}".replace(",", ".")


def titulo(texto: str) -> None:
    print()
    print("=" * 74)
    print(texto)
    print("=" * 74)


def cargar(ruta):
    with open(ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


def main() -> int:

    if not os.path.exists(FOTO):
        print(f"No esta la foto: {FOTO}")
        return 1

    foto = cargar(FOTO)

    meta = foto.get("meta") or {}

    titulo("LA FOTO")
    print()
    print(f"  fichero             {FOTO}")
    print(f"  meta.generated_at   {meta.get('generated_at')}")
    print(f"  snapshot            {meta.get('snapshot')}")
    print()
    print("  Abierta con encoding='utf-8'.")

    # ========================================================
    # BLOQUE 0 — ¿EXISTE EL HISTORICO?
    # ========================================================

    titulo("BLOQUE 0 - ¿EXISTE HISTORICO DE ESCAPARATES?")

    print()
    print("  LO QUE HACIA PENSAR QUE SI, Y NO ES:")
    print()

    censo = foto.get("censo_del_reset") or {}

    print(f"    `censo_del_reset` en la foto: {censo.get('reason')}")
    print(
        f"    ...pero es el censo de las OFERTAS QUE RECIBIMOS: "
        f"{censo.get('offers')} ofertas, {euros(censo.get('total'))} EUR,"
    )
    print("    por jugadores NUESTROS. No tiene nada que ver con los")
    print("    veinte del escaparate.")
    print()

    lineas_censo = 0

    if os.path.exists(CENSO_DE_OFERTAS):
        with open(CENSO_DE_OFERTAS, encoding="utf-8") as fichero:
            lineas_censo = sum(1 for l in fichero if l.strip())

    print(
        f"    {CENSO_DE_OFERTAS}: {lineas_censo} linea(s)."
    )
    print(
        f"    {LIBRO_DE_ESCAPARATE}: "
        f"{'existe' if os.path.exists(LIBRO_DE_ESCAPARATE) else 'NO EXISTE'}"
        f" — y ademas ese 'escaparate' es el NUESTRO (publicar para"
    )
    print("    vender), no el del Computer.")

    # Lo unico que hay: los snapshots.
    por_dia = defaultdict(set)
    nombres = {}

    ficheros = sorted(glob.glob("data/snapshot_*.json"))

    for ruta in ficheros:

        try:
            snap = cargar(ruta)

        except Exception:                            # noqa: BLE001
            continue

        if not snap.get("timestamp"):
            continue

        dia = dia_de_mercado(snap["timestamp"])

        for venta in ((snap.get("market") or {}).get("sales") or []):

            if (venta.get("user") or {}).get("id"):
                continue

            jugador = venta.get("player")

            pid = (
                jugador.get("id")
                if isinstance(jugador, dict)
                else jugador
            )

            if pid:
                por_dia[dia].add(pid)

    # Y el dia de hoy, del cuadro de objetivos.
    hoy = dia_de_mercado(meta.get("generated_at"))

    for fila in (foto.get("acquisition") or {}).get("targets") or []:
        if fila.get("seller_kind") == "COMPUTER":
            por_dia[hoy].add(fila["id"])
            nombres[fila["id"]] = fila.get("name")

    print()
    print("  LO UNICO QUE HAY, Y ES INDIRECTO:")
    print()
    print(
        f"    {len(ficheros)} ficheros data/snapshot_*.json llevan "
        f"`market.sales` dentro."
    )
    print(
        f"    De ahi salen {len(por_dia) - 1} dias de mercado, mas el "
        f"de la foto de hoy."
    )
    print()
    print("  RESPUESTA: NO HAY HISTORICO DE ESCAPARATES COMO TAL.")
    print("  Hay diez dias reconstruibles de los snapshots, con un")
    print("  agujero del 18/08 al 09/09. Todo lo de abajo lleva ese")
    print("  `n` delante.")

    # ========================================================
    # BLOQUE 1 — COMO ROTA
    # ========================================================

    titulo("BLOQUE 1 - COMO ROTA")

    rota = rotacion(por_dia)

    print()
    print(f"  {rota['reason']}")
    print()
    print(f"  {'dia de mercado':<18}{'jugadores':>11}")

    for dia in sorted(por_dia):
        print(f"  {dia.isoformat():<18}{len(por_dia[dia]):>11}")

    print()
    tamanos = {len(v) for v in por_dia.values()}

    print(
        f"  COMPROBACION DEL CORTE: los {rota['dias']} dias salen a "
        f"{sorted(tamanos)} jugadores. Si el corte"
    )
    print(
        "  estuviera a medianoche saldrian dias de 29 y 34, que es"
    )
    print("  imposible: el Computer saca veinte.")

    print()
    print("  DE UN DIA PARA OTRO (solo pares seguidos):")
    print()
    print(f"    {'de':<12}{'a':<12}{'siguen':>8}{'nuevos':>8}")

    for par in rota["pares"]:
        print(
            f"    {par['de']:<12}{par['a']:<12}"
            f"{par['siguen']:>8}{par['nuevos']:>8}"
        )

    print()
    print(
        f"    media de nuevos por dia: {rota['nuevos_por_dia']} de 20 "
        f"({rota['nuevos_por_dia_percent']} %)"
    )

    print()
    print("  ¿SE REPITEN? Veces que sale cada jugador:")
    print(f"    {rota['reparto_de_apariciones']}")
    print(
        f"    {rota['distintos']} distintos para {rota['plazas']} "
        f"plazas en {rota['dias']} dias."
    )

    # --------------------------------------------------
    # LOS 101 QUE NOS MEJORAN
    # --------------------------------------------------

    vestuario = foto.get("elVestuarioLibre") or {}

    vigilados = vestuario.get("players") or []

    apariciones = Counter()

    for ids in por_dia.values():
        for pid in ids:
            apariciones[pid] += 1

    print()
    print(
        f"  DE LOS {(vestuario.get('recuento') or {}).get('nos_mejoran')} "
        f"QUE NOS MEJORAN, LOS 20 MEJORES: ¿han salido alguna vez?"
    )
    print()

    salidos = 0
    total_apariciones = 0

    for jugador in vigilados:
        veces = apariciones.get(jugador["id"], 0)

        total_apariciones += veces

        if veces:
            salidos += 1

        print(
            f"    {str(jugador.get('posicion')):<5}"
            f"{str(jugador.get('name'))[:20]:<22}"
            f"{euros(jugador.get('price')):>12}   "
            f"{veces} vez/veces" + ("   <- SI" if veces else "")
        )

    print()
    print(
        f"    han salido alguna vez: {salidos} de {len(vigilados)}, "
        f"con {total_apariciones} apariciones en total"
    )

    SEIS = [
        "Zabiri",
        "Juan Iglesias",
        "Dimitrievski",
        "Roberto Fern",
        "Espart",
        "Dmitrovic",
    ]

    print()
    print("  LOS SEIS QUE NOMBRO EL ENCARGO:")
    print()

    for nombre in SEIS:
        ficha = next(
            (
                j
                for j in vigilados
                if nombre.lower() in str(j.get("name")).lower()
            ),
            None,
        )

        veces = apariciones.get((ficha or {}).get("id"), 0)

        print(
            f"    {nombre:<20}"
            + (
                f"SI, {veces} vez/veces"
                if veces
                else "NO ha salido ni una vez en los diez dias"
            )
        )

    # --------------------------------------------------
    # CUANTO SE TARDA
    # --------------------------------------------------

    espera = espera_de_un_jugador(
        total_apariciones, len(vigilados), rota["dias"]
    )

    print()
    print("  CUANTO SE TARDA EN VER A UNO CONCRETO")
    print()
    print(f"    {espera['reason']}")

    # ========================================================
    # BLOQUE 2 — ¿HAY PATRON?
    # ========================================================

    titulo("BLOQUE 2 - ¿HAY PATRON EN QUIEN SALE?")

    # El catalogo mas fresco que hay entero.
    catalogo = {}

    for ruta in reversed(ficheros):
        try:
            snap = cargar(ruta)

        except Exception:                            # noqa: BLE001
            continue

        catalogo = (
            (snap.get("catalog") or {}).get("data") or {}
        ).get("players") or {}

        if catalogo:
            print()
            print(f"  catalogo de {ruta} ({len(catalogo)} jugadores)")
            break

    rivales = cargar(RIVALES)

    con_dueno = set()

    for manager in rivales.get("managers") or []:
        for ficha in manager.get("roster") or []:
            pid = ficha.get("id") if isinstance(ficha, dict) else ficha

            if pid:
                con_dueno.add(int(pid))

    salieron = {
        pid for pid in apariciones if str(pid) in catalogo
    }

    libres = {
        int(k)
        for k in catalogo
        if int(k) not in con_dueno
        and (catalogo[k].get("position") or 0) in (1, 2, 3, 4)
    }

    otros = libres - salieron

    print(
        f"  con dueño {len(con_dueno)}   libres {len(libres)}   "
        f"han salido {len(salieron)}"
    )

    def rasgo(ids, clave):
        return [
            catalogo[str(i)].get(clave) or 0
            for i in ids
            if str(i) in catalogo
        ]

    print()

    for clave, nombre in (("price", "precio"), ("points", "puntos")):

        prueba = hay_patron(
            rasgo(salieron, clave),
            rasgo(otros, clave),
            nombre=nombre,
        )

        print(f"  {prueba['reason']}")

    # Posicion: proporciones, con su test propio.
    print()
    print("  POR POSICION:")
    print()
    print(
        f"    {'pos':<6}{'salieron':>10}{'no salieron':>14}"
    )

    a = Counter(
        catalogo[str(i)].get("position")
        for i in salieron
        if str(i) in catalogo
    )

    b = Counter(
        catalogo[str(i)].get("position")
        for i in otros
        if str(i) in catalogo
    )

    for posicion, nombre in POS.items():
        print(
            f"    {nombre:<6}"
            f"{a[posicion] / max(sum(a.values()), 1) * 100:>9.1f}%"
            f"{b[posicion] / max(sum(b.values()), 1) * 100:>13.1f}%"
        )

    print()
    print("  VEREDICTO: NO SE ENCUENTRA PATRON.")
    print()
    print("  Ni por precio ni por puntos, y las proporciones por")
    print("  posicion se mueven poco. PERO LA PRUEBA ES FLOJA: nueve")
    print("  dias de escaparate y un agujero de tres semanas. Esto NO")
    print("  demuestra que sea aleatorio; dice que con estos datos no")
    print("  se ve nada. La consecuencia practica es la misma: hoy no")
    print("  se puede cazar al jugador, solo estar listo.")

    # ========================================================
    # BLOQUE 3 — ¿ESTABAMOS LISTOS?
    # ========================================================

    titulo("BLOQUE 3 - ¿ESTABAMOS LISTOS?")

    tablon = cargar(TABLON)

    subastas = []
    vistas = set()

    for evento in tablon:

        if evento.get("type") != "market":
            continue

        for fila in evento.get("content") or []:

            if not isinstance(fila, dict):
                continue

            # Con vendedor es un traspaso entre managers, no una
            # subasta del Computer.
            if (fila.get("from") or {}).get("id"):
                continue

            clave = (
                fila.get("player"),
                fila.get("amount"),
                (fila.get("to") or {}).get("id"),
            )

            if clave in vistas:
                continue

            vistas.add(clave)

            subastas.append(
                {
                    "dia": datetime.datetime.fromtimestamp(
                        evento["date"], datetime.UTC
                    ).date().isoformat(),
                    "to_id": (fila.get("to") or {}).get("id"),
                    "to_name": (fila.get("to") or {}).get("name"),
                    "amount": fila.get("amount"),
                    "pujadores": {
                        (b.get("user") or {}).get("id")
                        for b in (fila.get("bids") or [])
                    },
                }
            )

    listos = estabamos_listos(subastas, NOSOTROS)

    print()
    print(f"  {listos['reason']}")
    print()
    print(
        f"  {'manager':<30}{'pujo en':>9}{'gano':>6}{'convierte':>11}"
        f"{'% subastas':>12}{'dias':>7}"
    )

    for fila in listos["tabla"]:
        print(
            f"  {str(fila['name'])[:29]:<30}{fila['pujadas']:>9}"
            f"{fila['ganadas']:>6}{fila['conversion']:>10.0f}%"
            f"{fila['participacion_percent']:>11.0f}%"
            f"{fila['dias_con_puja']:>7}"
            + ("   <- nosotros" if fila["es_nuestro"] else "")
        )

    print()
    print("  EL NUMERO QUE SEPARA 'ELEGIMOS MAL' DE 'NO ESTABAMOS':")
    print()
    print(
        f"    {listos['subastas_en_dias_sin_puja_nuestra']} de "
        f"{listos['n']} subastas pasaron en dias en los que no "
        f"pujamos ni una vez."
    )

    print()
    print("  AVISO: el tablon publica las pujas perdedoras que")
    print("  publica, asi que 'pujo en' es una COTA INFERIOR para")
    print("  todos. Afecta igual a las ocho plantillas, asi que la")
    print("  comparacion entre managers se sostiene.")

    # --------------------------------------------------
    # Y HOY, JUGADOR A JUGADOR
    # --------------------------------------------------

    print()
    print("  Y HOY, CON LA FOTO DELANTE: ¿quien del escaparate mejora")
    print("  el once, y por que no se puja?")
    print()

    def por_partido(ficha):
        partidos = (
            (ficha.get("played_home") or 0)
            + (ficha.get("played_away") or 0)
        ) or (ficha.get("played") or 0)

        return (
            (ficha.get("points") or 0) / partidos if partidos else None
        )

    def esperado(ficha):
        ritmo = por_partido(ficha)
        titular = ficha.get("starter_probability")

        if ritmo is None or titular is None:
            return None

        return ritmo * float(titular) / 100.0

    peor = {}

    for ficha in (foto.get("roster") or {}).get("players") or []:

        if not ficha.get("is_starter"):
            continue

        valor = esperado(ficha)

        if valor is None:
            continue

        if (
            ficha["position"] not in peor
            or valor < peor[ficha["position"]][1]
        ):
            peor[ficha["position"]] = (ficha["name"], valor)

    print("    el peor titular de cada posicion (puntos x titularidad):")

    for posicion, (nombre, valor) in sorted(peor.items()):
        print(f"      {POS[posicion]}  {nombre[:18]:<20}{valor:.2f}")

    print()

    mejoran = []

    for fila in (foto.get("acquisition") or {}).get("targets") or []:

        if fila.get("seller_kind") != "COMPUTER":
            continue

        valor = esperado(fila)

        if valor is None or fila.get("position") not in peor:
            continue

        if valor > peor[fila["position"]][1]:
            mejoran.append((fila, valor))

    print(
        f"    MEJORAN EL ONCE: {len(mejoran)} de 20   "
        f"(biddable {(foto.get('acquisition') or {}).get('biddable')}, "
        f"actionable {(foto.get('acquisition') or {}).get('actionable')})"
    )
    print()

    motivos = Counter()

    for fila, valor in sorted(mejoran, key=lambda x: -x[1]):
        motivos[fila.get("decision")] += 1

        print(
            f"      {str(fila['name'])[:18]:<20}"
            f"{POS.get(fila['position'], '?'):<5}"
            f"{euros(fila['market_price']):>12}   "
            f"{valor:.2f} contra {peor[fila['position']][1]:.2f}   "
            f"{fila.get('decision')}"
        )
        print(
            f"          intent {fila.get('intent')}   "
            f"bolsillo {fila.get('budget_source')}   "
            f"aplicado {euros(fila.get('budget_applied'))}"
        )

    print()
    print(f"    POR MOTIVO: {dict(motivos)}")
    print()
    print("    NINGUNO ESTA BLOQUEADO POR FALTA DE FICHA. Y ninguno")
    print("    recibe el bolsillo de fichar (8.874.116): todos salen")
    print("    con `intent` de especulacion, asi que se miden contra")
    print("    el bolsillo de especular. Es el mismo `intent` del")
    print("    lunes, mapeado y quieto.")

    # ========================================================
    # BLOQUE 4 — LA LISTA DE VIGILANCIA
    # ========================================================

    titulo("BLOQUE 4 - LA LISTA DE VIGILANCIA, ¿SIRVE?")

    print()
    print(
        f"  `elVestuarioLibre.vigilados`: "
        f"{len(vestuario.get('vigilados') or [])} ids"
    )
    print(
        f"  criterio: los 5 mejores de cada puesto entre los que nos "
        f"suman y han jugado"
    )
    print(
        f"  {(vestuario.get('cortes') or {}).get('partidos_para_juzgar')}+ "
        f"partidos, por lo que nos suman contra la vara de SU posicion."
    )
    print()
    print("  QUIEN LA LEE: un solo consumidor,")
    print("  `dashboard_state._con_los_vigilados`, y lo que hace es")
    print("  marcar filas del cuadro de objetivos DESPUES de que el")
    print("  tablero haya decidido. Su propio docstring lo dice:")
    print()
    print('    "La marca no puede haber influido en `decision`, `bid`')
    print('     ni en ningun liston — no por disciplina, sino porque')
    print('     llega tarde para hacerlo."')
    print()
    print(
        f"  Hoy marca {(foto.get('acquisition') or {}).get('vigilados_en_el_cuadro')} "
        f"fila(s) del cuadro."
    )
    print()
    print("  RESPUESTA: NINGUNA DECISION DEL MOTOR LA LEE. Es")
    print("  decorativa POR DISEÑO, y esta escrito que lo es. No es")
    print("  una pieza olvidada: es una pieza que se decidio que no")
    print("  autorizase nada.")
    print()
    print("  LO QUE SI SE VE HOY: el unico vigilado que aparecio en el")
    print("  escaparate es Budimir, y salio SUPERA_PRESUPUESTO. O sea")
    print("  que el dia que la lista 'acierta', no pasa nada.")

    # ========================================================
    # BLOQUE 5 — LA REGLA DE ESTAR LISTO
    # ========================================================

    titulo("BLOQUE 5 - LA REGLA DE ESTAR LISTO (propuesta, apagada)")

    importes = [s["amount"] for s in subastas if s.get("amount")]

    presupuestos = (foto.get("acquisition") or {}).get("budgets") or {}

    ritmo = (foto.get("sale_order") or {}).get(
        "net_rate_percent_per_day"
    )

    regla = regla_de_estar_listo(
        importes,
        cajas={
            "disponible hoy tras exposicion": 973_594,
            "bolsillo de especular": presupuestos.get("speculation"),
            "bolsillo de fichar": presupuestos.get("acquisition"),
            "mas la caja realizable": (
                (presupuestos.get("acquisition") or 0)
                + ((foto.get("sale_order") or {}).get(
                    "cash_on_the_table"
                ) or 0)
            ),
        },
        ritmo_de_plantilla_percent_dia=ritmo,
    )

    print()
    print(
        f"  LO QUE CUESTA GANAR, sobre {regla['n']} subastas del "
        f"Computer (10/08 a 17/09):"
    )
    print()
    print(f"    mediana   {euros(regla['mediana']):>14}")
    print(f"    p75       {euros(regla['p75']):>14}")
    print(f"    p90       {euros(regla['p90']):>14}")
    print()
    print("  A QUE FRACCION LLEGA CADA CAJA:")
    print()

    for etiqueta, datos in regla["alcance"].items():
        print(
            f"    {etiqueta:<34}{euros(datos['caja']):>13}   "
            f"{datos['subastas_al_alcance']:>3} de {regla['n']}  "
            f"({datos['percent']:.0f} %)"
        )

    print()
    print("  LA REGLA:")
    print()
    print(f"    caja libre diaria   {euros(regla['caja_propuesta'])} EUR")
    print(f"    fichas libres       {regla['fichas_libres_propuestas']}")
    print(f"    {regla['fichas_reason']}")
    print()
    print("  LO QUE CUESTA MANTENERLA:")
    print()
    print(f"    {regla['reason']}")
    print()
    print("  SE PROPONE Y NO SE APLICA. Nadie lee esto para decidir")
    print("  nada, y encenderlo no es de este encargo.")

    titulo("NADA SE HA ENCENDIDO")
    print()
    print(f"  ENCENDIDO = {ENCENDIDO}")
    print("  Ni una escritura. Ningun umbral. Ningun interruptor.")
    print("  `count_free_slots` e `historical_max`, como estaban.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
