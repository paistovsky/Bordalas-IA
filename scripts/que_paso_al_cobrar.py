"""
Que contesto Biwenger cuando Pepe intento cobrar una oferta.

POR QUE EXISTE

    El 19/08/2026 el dashboard puso:

        "ACCEPT RECOVERY OFFER apartada: ha fallado 4 veces
         seguidas (HTTP 500). Se reintenta en 66 min."

    Y a la vez la barra lateral decia "Ultima escritura: cobrar
    oferta aprobada", con el saldo sin moverse. Dos señales que
    no casan: o se intento y fallo sin actualizar el contador, o
    la pantalla estaba llamando escritura a un intento fallido.

    Buscar en los logs de GitHub no valia: el buscador solo mira
    los pasos desplegados y devolvia 0 de 0 sobre un texto que
    si estaba.

    El sitio bueno es `autopilot_log.jsonl`, que guarda por cada
    ciclo la accion elegida, si se escribio, el codigo HTTP y
    hasta mil caracteres del cuerpo de la respuesta. Un 500 a
    secas no diagnostica nada; el cuerpo si.

QUE HACE

    Lee el log y enseña, del mas reciente al mas viejo, cada
    intento de cobrar: cuando, con que resultado, que contesto
    Biwenger y por que jugador.

    Tambien cuenta las demas acciones, para poder distinguir
    "fallo al cobrar" de "nunca llego a intentarlo", que se
    parecen mucho vistas desde la pantalla y no son lo mismo.

DE DONDE SACAR EL LOG

    En local ya esta en data/autopilot/. El de GitHub viene como
    artefacto de cada run -"bordalas-live-diagnostics-<id>"-: se
    descarga, se descomprime y se le pasa la ruta.

QUE NO HACE

    No escribe, no toca Biwenger y no necesita red.

USO

    python scripts/que_paso_al_cobrar.py
    python scripts/que_paso_al_cobrar.py --log C:/ruta/al/autopilot_log.jsonl
    python scripts/que_paso_al_cobrar.py --accion RENEW_MARKET_LISTING
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


LOG_POR_DEFECTO = (
    Path("data") / "autopilot" / "autopilot_log.jsonl"
)

ACCION_POR_DEFECTO = "ACCEPT_RECOVERY_OFFER"


def leer(ruta: Path) -> list[dict]:

    if not ruta.exists():
        return []

    registros = []

    with open(ruta, encoding="utf-8") as fichero:

        for linea in fichero:

            linea = linea.strip()

            if not linea:
                continue

            try:
                registros.append(json.loads(linea))

            except Exception:
                # Una linea corrupta no puede tumbar el
                # diagnostico: se salta y se sigue.
                continue

    return registros


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--log",
        default=str(LOG_POR_DEFECTO),
        help="Ruta al autopilot_log.jsonl",
    )

    parser.add_argument(
        "--accion",
        default=ACCION_POR_DEFECTO,
        help="Que accion investigar",
    )

    parser.add_argument(
        "--ciclos",
        type=int,
        default=0,
        help="Cuantos ciclos mirar hacia atras (0 = todos)",
    )

    args = parser.parse_args()

    ruta = Path(args.log)
    registros = leer(ruta)

    print()
    print("=" * 70)
    print(f" QUE PASO CON {args.accion}")
    print("=" * 70)
    print()

    if not registros:
        print(f"  No hay ciclos en {ruta}.")
        print()
        print("  El log de GitHub viene como artefacto de cada")
        print("  run. Descargalo y pasalo con --log.")
        print()
        return

    if args.ciclos:
        registros = registros[-args.ciclos:]

    print(f"  Ciclos leidos:  {len(registros)}")
    print(f"  Desde:          {registros[0].get('timestamp')}")
    print(f"  Hasta:          {registros[-1].get('timestamp')}")
    print()

    # ------------------------------------------------------
    # QUE ELIGE HACER
    # ------------------------------------------------------

    elegidas = Counter(
        str(r.get("decision_action") or "SIN ACCION")
        for r in registros
    )

    print("  QUE ELIGE HACER CADA CICLO")
    print("  " + "-" * 66)

    for accion, veces in elegidas.most_common(10):
        marca = " <--" if accion == args.accion else ""
        print(f"    {veces:>4}x  {accion}{marca}")

    print()

    # ------------------------------------------------------
    # QUE LLEGO A ESCRIBIRSE
    # ------------------------------------------------------
    #
    # La accion elegida y la accion ejecutada no son lo mismo.
    # Una decision puede ganar el ciclo y morir en el executor
    # -bloqueo temporal, jugador protegido, backoff- sin que en
    # la pantalla se note la diferencia.

    intentos = [
        r
        for r in registros
        if (r.get("execution") or {}).get("action") == args.accion
    ]

    if not intentos:
        print(f"  RESPUESTA: {args.accion} no ha llegado nunca")
        print("  al executor en este tramo de log.")
        print()

        elegida_veces = elegidas.get(args.accion, 0)

        if elegida_veces:
            print(
                f"  Y eso que la eligio {elegida_veces} vez/veces. "
                f"Se cae entre decidir y escribir: mira si esta"
            )
            print("  apartada por el backoff de fallos.")

        else:
            print("  Tampoco la ha elegido: el problema esta antes,")
            print("  en el orquestador, no en la escritura.")

        print()
        return

    # ------------------------------------------------------
    # EL DETALLE, QUE ES LO QUE IMPORTA
    # ------------------------------------------------------

    exitos = sum(
        1
        for r in intentos
        if (r.get("execution") or {}).get("success")
    )

    print(
        f"  INTENTOS: {len(intentos)}   "
        f"CON EXITO: {exitos}   "
        f"FALLIDOS: {len(intentos) - exitos}"
    )
    print()

    estados = Counter(
        str((r.get("execution") or {}).get("http_status"))
        for r in intentos
    )

    print("  CODIGOS DE RESPUESTA")
    print("  " + "-" * 66)

    for codigo, veces in estados.most_common():
        print(f"    {veces:>4}x  HTTP {codigo}")

    print()
    print("  UNO A UNO, DEL MAS RECIENTE AL MAS VIEJO")
    print("  " + "-" * 66)

    for registro in reversed(intentos[-12:]):

        ejecucion = registro.get("execution") or {}

        print()
        print(f"    {registro.get('timestamp')}")

        print(
            f"      estado:    {ejecucion.get('status')}   "
            f"HTTP {ejecucion.get('http_status')}   "
            f"exito={ejecucion.get('success')}"
        )

        if ejecucion.get("write_performed") and not ejecucion.get(
            "success"
        ):
            print(
                "      OJO: figura como escritura realizada pero "
                "no tuvo exito."
            )

        if ejecucion.get("reason"):
            print(f"      motivo:    {ejecucion.get('reason')}")

        if ejecucion.get("response"):
            print(
                f"      respuesta: {ejecucion.get('response')}"
            )

    print()
    print("=" * 70)
    print()

    if exitos == 0:
        print("  Ninguno salio bien. La respuesta de Biwenger de")
        print("  arriba es el dato: un codigo a secas no dice por")
        print("  que, el cuerpo si.")
        print()


if __name__ == "__main__":
    main()
