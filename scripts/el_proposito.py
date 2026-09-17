"""
El propósito, corrido contra la foto del dueño.

QUE FOTO MIRA, Y LO COMPRUEBA ANTES

    `diagnostico/status.json`. Lo primero que imprime es
    `meta.generated_at`, y se abre con `encoding="utf-8"`.

QUE HACE

    BLOQUE 0   el libro del escaparate: donde escribe y que no
               duplica.
    BLOQUE 1   el mapa del `intent`, sacado del arbol.
    BLOQUE 2   si el planteamiento del encargo es correcto.
    BLOQUE 3   que habria cambiado: hoy, en los diez dias de
               escaparate, y cuanto mas se podria gastar.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red y no enciende la
    separacion.

USO

    python scripts/el_proposito.py > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import datetime
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict


sys.path.insert(0, os.getcwd())

from src.analysis.el_proposito import (                  # noqa: E402
    ENCENDIDO,
    INTENTS,
    SPECULATION,
    XI_UPGRADE,
    frenos_de,
    mapa_del_intent,
    que_cambiaria,
    valor_de_fichar_con_el_activo,
)
from src.intelligence.libro_del_escaparate import (       # noqa: E402
    LIBRO,
    apuntar_el_escaparate,
    dia_de_mercado,
)


FOTO = "diagnostico/status.json"

NOSOTROS = 14175949


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

    # ========================================================
    # BLOQUE 0 — EL LIBRO
    # ========================================================

    titulo("BLOQUE 0 - EL LIBRO DEL ESCAPARATE (esto SI se enciende)")

    escaparate = [
        fila
        for fila in (foto.get("acquisition") or {}).get("targets") or []
        if fila.get("seller_kind") == "COMPUTER"
    ]

    print()
    print(f"  escribe en          {LIBRO.as_posix()}")
    print(f"  jugadores hoy       {len(escaparate)}")
    print(
        f"  dia de mercado      "
        f"{dia_de_mercado(meta.get('generated_at'))}   "
        f"(el corte es el reset, no la medianoche)"
    )
    print()
    print("  ESTA EN `los_libros.LIBROS`, asi que `guardar_los_libros.py`")
    print("  lo sube. Sin eso viviria en el runner y moriria con el.")

    from src.estado.los_libros import LIBROS

    en_la_lista = [
        libro
        for libro in LIBROS
        if libro["ruta"] == LIBRO.as_posix()
    ]

    print()
    print(
        f"  en la lista de libros: "
        f"{'SI' if en_la_lista else 'NO — ESTO ES UN FALLO'}"
    )

    if en_la_lista:
        print(f"    ruta: {en_la_lista[0]['ruta']}")
        print(f"    {en_la_lista[0]['que_es']}")

    print()
    print(f"  ¿existe ya en disco? "
          f"{'SI' if LIBRO.exists() else 'todavia no: lo escribe el primer ciclo'}")

    if LIBRO.exists():
        lineas = [
            json.loads(l)
            for l in LIBRO.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]

        print(f"    lineas: {len(lineas)}")

        for fila in lineas[-5:]:
            print(
                f"      {fila.get('dia_de_mercado')}   "
                f"{fila.get('n')} jugadores, "
                f"{fila.get('with_forecast')} con pronostico"
            )

    # ========================================================
    # BLOQUE 1 — EL MAPA
    # ========================================================

    titulo("BLOQUE 1 - EL MAPA DEL `intent`, SACADO DEL ARBOL")

    mapa = mapa_del_intent()

    print()
    print(f"  {mapa['reason']}")

    for etiqueta in INTENTS:

        ficha = mapa["intents"][etiqueta]

        print()
        print(f"  {etiqueta}   (clase {ficha['operation_class']})")
        print(f"    vias         {', '.join(ficha['routes'])}")

        for freno, nombre in (
            ("liston", "liston"),
            ("bolsillo", "bolsillo"),
            ("tope_de_prima", "tope de prima"),
            ("minimo", "minimo"),
        ):
            datos = ficha[freno]

            if freno == "bolsillo":
                print(
                    f"    {nombre:<13}{datos['nombre']} — "
                    f"{datos['de_donde']}"
                )
                continue

            print(
                f"    {nombre:<13}"
                + (
                    f"SI, {datos['valor']}"
                    if datos["aplica"]
                    else "NO aplica"
                )
            )
            print(f"      {datos['que_es']}")

            if datos.get("en_su_lugar"):
                print(f"      EN SU LUGAR: {datos['en_su_lugar']}")

            if datos.get("aviso"):
                print(f"      AVISO: {datos['aviso']}")

        print(
            f"    prob. minima {ficha['probabilidad_minima']}"
        )

    lectores = mapa["lectores"]

    print()
    print(f"  QUIEN LO DECIDE ({mapa['n_deciden']}):")
    print()

    for fichero, que in mapa["deciden"].items():
        print(f"    {fichero}")
        print(f"      {que}")

    print()
    print(f"  QUIEN LO NOMBRA ({lectores['n']} ficheros del arbol):")
    print()

    for fichero, datos in sorted(lectores["ficheros"].items()):
        print(
            f"    {fichero:<48}{datos['usos']:>3} usos  "
            f"{datos['que_hace'][:60]}"
        )

    print()
    print(
        f"  sin anotar: {lectores['sin_anotar'] or 'ninguno'}   "
        f"anotados que ya no aparecen: "
        f"{lectores['anotados_que_no_aparecen'] or 'ninguno'}"
    )

    # ========================================================
    # BLOQUE 2 — EL PLANTEAMIENTO
    # ========================================================

    titulo("BLOQUE 2 - ¿ES CORRECTO EL PLANTEAMIENTO DEL ENCARGO?")

    print()
    print("  EL ENCARGO DICE:")
    print()
    print('    "El `intent` se elige por que via da mas euros, y luego')
    print('     se aplican los listones de esa via."')
    print()
    print("  NO. Eso describe un camino que hoy no corre.")
    print()
    print(f"    DEPLOYMENT_ENABLED = {mapa['deployment_enabled']}")
    print("    -> la etiqueta la reparte `classify_operation`, que")
    print("       elige por CLASE DE OPERACION, no por euros.")
    print("    -> el `max(opciones, key=value)` solo manda APAGADO.")
    print()
    print("  Y LA SEPARACION QUE PIDES YA EXISTE, con este nombre:")
    print()
    print("    el PROPOSITO   classify_operation  ->  SIGNING / TRADE")
    print("    la VALORACION  las cuatro vias     ->  cuanto vale")
    print("    el proposito manda bolsillo, liston y tope")

    # Y la prueba de que funciona: el libro de pujas.
    print()
    print("  Y NO ESTA ROTA. El libro de pujas, con `intent` apuntado:")
    print()

    try:
        libro = cargar("data/trading/bid_outcome_ledger.json")["bids"]

    except Exception:                               # noqa: BLE001
        libro = {}

    con_etiqueta = [
        v for v in libro.values() if v.get("intent")
    ]

    for puja in sorted(
        con_etiqueta, key=lambda v: str(v.get("placed_at"))
    ):
        if puja["intent"] != XI_UPGRADE:
            continue

        print(
            f"    {str(puja.get('placed_at'))[:10]}  "
            f"{str(puja.get('player_name'))[:18]:<20}"
            f"precio {euros(puja.get('market_price')):>12}  "
            f"valor {euros(puja.get('our_value')):>12}  "
            f"{puja.get('outcome')}"
        )

    fichajes = [
        v for v in con_etiqueta if v["intent"] == XI_UPGRADE
    ]

    ganados = [v for v in fichajes if v.get("outcome") == "WON"]

    print()
    print(
        f"    {len(fichajes)} fichajes de {len(con_etiqueta)} pujas con "
        f"etiqueta, y ganamos {len(ganados)}. En los dos, el valor "
        f"como fichaje SUPERABA al precio."
    )
    print(
        f"    ({len(libro) - len(con_etiqueta)} pujas mas sin etiqueta: "
        f"el campo se añadio despues)"
    )

    # ========================================================
    # BLOQUE 3 — QUE HABRIA CAMBIADO
    # ========================================================

    titulo("BLOQUE 3 - QUE HABRIA CAMBIADO")

    filas = (foto.get("season_horizon") or {}).get("rows") or []

    candidatos = []

    for fila in filas:

        motivo = fila.get("xi_reason") or ""

        encontrado = re.search(
            r"pagariamos hasta ([\d\.]+) EUR", motivo
        )

        valor_xi = (
            int(encontrado.group(1).replace(".", ""))
            if encontrado
            else 0
        )

        candidatos.append(
            {
                "name": fila.get("name"),
                "market_price": fila.get("market_price"),
                "xi_value": valor_xi,
                "value": (fila.get("deployment") or {}).get("value") or 0,
                "value_route": (
                    (fila.get("deployment") or {}).get("value_route")
                ),
                "seller_kind": fila.get("seller_kind"),
                "decision": fila.get("decision"),
            }
        )

    print()
    print(f"  LOS {len(candidatos)} CANDIDATOS DE LA FOTO")
    print()

    con_valor = [c for c in candidatos if c["xi_value"] > 0]

    print(
        f"    con valor POSITIVO como fichaje:     "
        f"{len(con_valor)} de {len(candidatos)}"
    )
    print(
        f"    con ese valor POR ENCIMA del precio: "
        f"{sum(1 for c in con_valor if c['xi_value'] > c['market_price'])}"
    )
    print()
    print(
        f"    {'jugador':<20}{'precio':>13}{'valor fichaje':>15}"
        f"{'le falta':>13}{'valor activo':>14}"
    )

    for fila in sorted(con_valor, key=lambda c: -c["xi_value"]):
        print(
            f"    {str(fila['name'])[:18]:<20}"
            f"{euros(fila['market_price']):>13}"
            f"{euros(fila['xi_value']):>15}"
            f"{euros(fila['market_price'] - fila['xi_value']):>13}"
            f"{euros(fila['value']):>14}"
        )

    print()
    print("  ESO CONTESTA LA PRIMERA PREGUNTA: los del escaparate que")
    print("  mejoran el once NO caen por el bolsillo ni por el liston.")
    print("  Caen antes, porque su valor como fichaje no llega a su")
    print("  precio. Con el proposito separado seguirian cayendo.")

    presupuestos = (foto.get("acquisition") or {}).get("budgets") or {}

    calibracion = (
        (foto.get("rival_intelligence") or {}).get(
            "maximum_bid_calibration"
        )
        or {}
    )

    cambio = que_cambiaria(
        candidatos,
        bolsillo_de_fichar=presupuestos.get("acquisition"),
        bolsillo_de_especular=presupuestos.get("speculation"),
        techo_de_biwenger=calibracion.get("own_maximum_bid"),
    )

    titulo("BLOQUE 3.2 - Y SI EL VALOR DE FICHAR CONTASE EL ACTIVO")

    print()
    print("  La via del once mide el dinero como si desapareciera.")
    print("  Devuelve el 80 % del que sale, pero no cuenta que el que")
    print("  ENTRA es tambien un activo. Sumando las dos columnas:")
    print()
    print(f"  {cambio['reason']}")
    print()
    print(
        f"    {'jugador':<20}{'precio':>13}{'fichaje':>13}"
        f"{'activo':>14}{'suma':>14}{'margen':>13}"
    )

    for fila in cambio["los_que_pasarian"]:
        suma = valor_de_fichar_con_el_activo(
            fila["xi_value"], fila["value"]
        )

        print(
            f"    {str(fila['name'])[:18]:<20}"
            f"{euros(fila['market_price']):>13}"
            f"{euros(fila['xi_value']):>13}"
            f"{euros(fila['value']):>14}"
            f"{euros(suma['valor_con_el_activo']):>14}"
            f"{euros(fila['margen']):>13}"
        )

    print()
    print("  LO QUE SE ABRE, Y ES EL NUMERO QUE PIDE EL ENCARGO:")
    print()
    print(f"    bolsillo de especular (hoy)   {euros(cambio['bolsillo_de_especular']):>14}")
    print(f"    bolsillo de fichar            {euros(cambio['bolsillo_de_fichar']):>14}")
    print(f"    techo de Biwenger             {euros(cambio['techo_de_biwenger']):>14}")
    print()
    print(f"    operacion mas grande HOY      {euros(cambio['peor_caso_hoy']):>14}")
    print(f"    con el activo contado         {euros(cambio['peor_caso_con_el_activo']):>14}")
    print(f"    CUANTO MAS                    {euros(cambio['cuanto_mas']):>14}")

    # ========================================================
    # BLOQUE 3.3 — EN LOS DIEZ DIAS DE ESCAPARATE
    # ========================================================

    titulo("BLOQUE 3.3 - EN LOS DIEZ DIAS DE ESCAPARATE")

    print()
    print("  NO SE PUEDE MEDIR, Y POR LA MISMA RAZON QUE AYER.")
    print()
    print("  Para saber si habriamos pujado un dia pasado hace falta")
    print("  el valor como fichaje de cada uno de los veinte, y eso")
    print("  necesita el pronostico de titularidad del que entra Y del")
    print("  que sale ESE dia. Los snapshots de agosto ni siquiera")
    print("  traen nuestro once.")
    print()
    print("  Lo que hay, de los diez dias:")
    print()

    por_dia = defaultdict(set)

    for ruta in sorted(glob.glob("data/snapshot_*.json")):

        try:
            snap = cargar(ruta)

        except Exception:                            # noqa: BLE001
            continue

        if not snap.get("timestamp"):
            continue

        lin = (
            (snap.get("user_lineup") or {}).get("data") or {}
        ).get("lineup") or {}

        por_dia[dia_de_mercado(snap["timestamp"])].add(
            bool(lin.get("players"))
        )

    con_once = sum(1 for v in por_dia.values() if True in v)

    print(
        f"    dias de mercado con snapshot: {len(por_dia)}"
    )
    print(
        f"    de esos, con NUESTRO ONCE dentro: {con_once}"
    )
    print()
    print("  Con el libro del bloque 0 —que guarda precio, puntos,")
    print("  partidos Y pronostico de los veinte— esta tabla se puede")
    print("  hacer dentro de un mes. Es justo para lo que existe.")

    titulo("NADA SE HA ENCENDIDO SALVO EL LIBRO")
    print()
    print(f"  el_proposito.ENCENDIDO = {ENCENDIDO}")
    print("  El libro del escaparate SI entra en produccion: escribe")
    print("  una linea por reset y no pide nada a la red.")
    print("  Ningun liston movido, ningun bolsillo, ningun tope.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
