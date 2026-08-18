"""
Por que Pepe no esta pujando.

POR QUE EXISTE

    El 18/08/2026 el dueño lo dijo asi: "lo que no veo es que
    este pujando de verdad, en la app no salen pujas hechas".

    Y no habia forma rapida de responder. El ciclo escribe todo
    lo que hace en `data/autopilot/autopilot_log.jsonl` -que
    accion eligio, si era ejecutable, que contesto Biwenger- pero
    ese fichero son miles de lineas de JSON y el dashboard solo
    enseña el ultimo ciclo.

    Este script lee el log entero y contesta la pregunta.

QUE NO HACE

    No escribe nada, no toca Biwenger y no necesita red. Solo
    lee el log.

COMO SE LEE EL RESULTADO

    Hay cuatro respuestas posibles, y cada una lleva a un sitio
    distinto:

    1. "No hay ciclos"           -> GitHub Actions no esta
                                    corriendo. Mira Actions.

    2. "Ningun ciclo eligio
        comprar"                 -> Pepe si corre, pero siempre
                                    hay algo mas urgente o el
                                    tablero no propone objetivo.
                                    Mira la tabla de acciones.

    3. "Eligio comprar pero no
        escribio"                -> La decision llego al
                                    executor y algo la freno.
                                    El motivo esta impreso.

    4. "Escribio y Biwenger
        contesto X"              -> Ahi esta la respuesta de
                                    verdad: el HTTP y el cuerpo.

USO

    python scripts/por_que_no_puja.py
    python scripts/por_que_no_puja.py --ciclos 40
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


LOG = Path("data") / "autopilot" / "autopilot_log.jsonl"

COMPRA = "BUY_SPECULATION"


def leer(limite: int | None) -> list[dict]:

    if not LOG.exists():
        return []

    lineas = []

    with open(LOG, encoding="utf-8") as fichero:

        for linea in fichero:

            linea = linea.strip()

            if not linea:
                continue

            try:
                lineas.append(json.loads(linea))

            except Exception:
                # Una linea corrupta no puede tumbar el
                # diagnostico: se salta y se sigue.
                continue

    if limite:
        lineas = lineas[-limite:]

    return lineas


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ciclos",
        type=int,
        default=60,
        help="Cuantos ciclos mirar hacia atras (0 = todos)",
    )

    args = parser.parse_args()

    registros = leer(args.ciclos or None)

    print()
    print("=" * 62)
    print(" POR QUE NO ESTA PUJANDO")
    print("=" * 62)
    print()

    if not registros:
        print(f"  No hay ciclos en {LOG}.")
        print()
        print("  O el fichero no ha llegado a esta maquina -en")
        print("  GitHub sale como artefacto de cada run- o el")
        print("  ciclo no se esta ejecutando. Mira la pestaña")
        print("  Actions del repo.")
        print()
        return

    # Solo los registros POST_ACTION traen ejecucion; los
    # PRE_ACTION son la foto antes de escribir.
    print(f"  Ciclos leidos:  {len(registros)}")
    print(f"  Desde:          {registros[0].get('timestamp')}")
    print(f"  Hasta:          {registros[-1].get('timestamp')}")
    print()

    # ------------------------------------------------------
    # QUE ELIGE HACER
    # ------------------------------------------------------

    acciones = Counter(
        str(r.get("decision_action") or "SIN ACCION")
        for r in registros
    )

    print("  QUE ELIGE HACER CADA CICLO")
    print("  " + "-" * 58)

    for accion, veces in acciones.most_common():
        print(f"    {veces:>4}x  {accion}")

    print()

    compras = [
        r
        for r in registros
        if r.get("decision_action") == COMPRA
    ]

    # ------------------------------------------------------
    # EL DINERO
    # ------------------------------------------------------
    #
    # Se mira SIEMPRE, haya compras o no, porque el saldo es la
    # primera cosa que apaga la especulacion y lo hace en
    # silencio: si `calculate_speculation_budget` devuelve
    # enabled=False, el candidato de compra no llega a
    # construirse y en el log no queda ni rastro de que se haya
    # pensado en comprar.

    saldos = [
        r.get("balance")
        for r in registros
        if r.get("balance") is not None
    ]

    if saldos:

        print("  EL DINERO")
        print("  " + "-" * 58)
        print(f"    Saldo ahora:     {saldos[-1]:>14,}".replace(",", "."))
        print(f"    Minimo del tramo:{min(saldos):>14,}".replace(",", "."))
        print(f"    Maximo del tramo:{max(saldos):>14,}".replace(",", "."))

        en_negativo = sum(1 for s in saldos if s < 0)

        print(
            f"    Ciclos en negativo: {en_negativo} de {len(saldos)}"
        )
        print()

    bloqueos = Counter(
        str(r.get("operations_locked"))
        for r in registros
    )

    if bloqueos.get("True"):
        print(
            f"    OJO: {bloqueos['True']} ciclos con "
            f"operations_locked -fase temporal cerrada-."
        )
        print()

    if not compras:
        print("  RESPUESTA: ningun ciclo ha elegido comprar.")
        print()
        print("  No es que la puja falle: es que no se llega a")
        print("  intentar.")
        print()

        if saldos and saldos[-1] <= 0:
            print("  Y el saldo esta a cero o en negativo, que es")
            print("  el sospechoso numero uno. Con el saldo bajo, el")
            print("  presupuesto NO sale de maximumBid: sale del")
            print("  margen de deuda segura")
            print()
            print("      max_total_debt = recuperacion garantizada")
            print("                       - 500.000 de colchon")
            print("      margen         = max_total_debt - deuda actual")
            print()
            print("  y 'recuperacion garantizada' solo cuenta dinero")
            print("  que ya esta en la mesa -ofertas del Computer,")
            print("  ventas en curso-, no lo que valdria la plantilla")
            print("  si la pusieras a la venta.")
            print()
            print("  Sin ofertas vivas, ese margen es cero, la ventana")
            print("  de deuda se cierra y la especulacion se apaga")
            print("  entera, aunque Biwenger te deje pujar millones.")
            print()
            print("  Comprobalo en el dashboard: SOLVENCY / margen de")
            print("  deuda. Si sale 0, ese es el freno.")

        else:
            print("  O siempre hay una accion mas urgente -mira la")
            print("  tabla de arriba- o el tablero no propone ningun")
            print("  objetivo que compense.")

        print()

        ultimo = registros[-1]

        print("  Ultimo ciclo:")
        print(f"    accion   {ultimo.get('decision_action')}")
        print(f"    motivo   {str(ultimo.get('decision_reason'))[:200]}")
        print()
        return

    print(f"  Ciclos que eligieron comprar: {len(compras)}")
    print()

    # ------------------------------------------------------
    # QUE PASO CON ESAS COMPRAS
    # ------------------------------------------------------

    escrituras = []
    frenadas = []

    for registro in compras:

        ejecucion = registro.get("execution") or {}

        if not ejecucion:
            # PRE_ACTION: la pareja POST_ACTION lleva el
            # resultado.
            continue

        if ejecucion.get("write_performed"):
            escrituras.append((registro, ejecucion))

        else:
            frenadas.append((registro, ejecucion))

    if frenadas:

        print("  COMPRAS QUE NO LLEGARON A ESCRIBIR")
        print("  " + "-" * 58)

        motivos = Counter(
            str(e.get("status") or "SIN ESTADO")
            for _, e in frenadas
        )

        for estado, veces in motivos.most_common():
            print(f"    {veces:>4}x  {estado}")

        print()

        _, ultima = frenadas[-1]

        print("    La ultima:")
        print(f"      estado  {ultima.get('status')}")
        print(f"      motivo  {str(ultima.get('reason'))[:220]}")
        print()

    if escrituras:

        print("  PUJAS ENVIADAS A BIWENGER")
        print("  " + "-" * 58)

        for registro, ejecucion in escrituras[-10:]:

            print(
                f"    {registro.get('timestamp')}  "
                f"jugador {ejecucion.get('player_id')}  "
                f"HTTP {ejecucion.get('http_status')}  "
                f"{'OK' if ejecucion.get('success') else 'FALLO'}"
            )

            if not ejecucion.get("success"):
                print(f"        {str(ejecucion.get('reason'))[:200]}")
                print(f"        {str(ejecucion.get('response'))[:200]}")

        print()

        fallos = [
            e
            for _, e in escrituras
            if not e.get("success")
        ]

        if fallos:
            print(
                f"  RESPUESTA: se envian pujas ({len(escrituras)}) "
                f"pero {len(fallos)} las rechaza Biwenger. El "
                f"motivo esta arriba."
            )

        else:
            print(
                f"  RESPUESTA: {len(escrituras)} pujas enviadas y "
                f"aceptadas por Biwenger."
            )
            print()
            print("  Si en la app no salen, no es el ciclo: o son")
            print("  de un mercado ya resuelto -las pujas duran")
            print("  hasta el reset de las 07:00- o estas mirando")
            print("  otra pantalla. Las pujas vivas se ven en")
            print("  Mercado, no en Actividad.")

        print()

    elif not frenadas:
        print("  Los ciclos de compra no traen resultado de")
        print("  ejecucion. Son registros PRE_ACTION: falta la")
        print("  segunda mitad del log.")
        print()


if __name__ == "__main__":
    main()
