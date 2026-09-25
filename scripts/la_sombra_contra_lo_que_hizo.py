"""
La sombra, medida como lo que es: una prediccion de Pepe.

QUE HACE

    Para cada foto del panel que haya, tres columnas:

        lo que la sombra VIEJA publico     (solo si la foto la trae)
        lo que dice la sombra NUEVA        (`la_lista_de_la_noche`
                                            sobre esa misma foto)
        lo que se pujo de verdad           (`bid_outcome_ledger`,
                                            desde la hora de la foto
                                            hasta el reset siguiente)

    Y los dos fallos por separado, porque no cuestan lo mismo:

        dice que pujaria y no puja   -> susto falso
        no dice nada y puja          -> el dueño se entera por el saldo

QUIEN PUJO

    El libro apunta `target_source`. `SUBASTA_CARTERA` y `RENDIJA`
    las puso nuestro codigo. `DESCONOCIDO` con `recorded_by: TABLON`
    es una puja que aparecio en el tablon sin que ningun camino la
    apuntara al ponerla: la del dueño a mano, o una de un camino que
    no apunta. No se puede distinguir desde el libro, y se dice.

LIMITES, DICHOS

    · La foto es la del panel, no el estado del ciclo: la ventana del
      reset se planifica con `lectura_del_estado(foto)` y sin la
      plantilla (el panel no la trae entera).
    · La noche de la foto del 25/09 aun no ha pasado.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red y NO ESCRIBE NI UNA
    LINEA DE NINGUN LIBRO.

USO

    python scripts/la_sombra_contra_lo_que_hizo.py > salida.txt 2>&1
"""

from __future__ import annotations

import json
import os
import sys

from datetime import datetime, timedelta, timezone


sys.path.insert(0, os.getcwd())

from src.analysis.la_lista_de_la_noche import en_la_ventana, la_lista   # noqa: E402
from src.analysis.la_subasta import lectura_del_estado                  # noqa: E402


FOTOS = (
    "dashboard/data/status.json",
    "data/fotos/2026-09-18.json",
    "diagnostico/status-2026-09-23.json",
    "diagnostico/status.json",
)

LIBRO = "data/trading/bid_outcome_ledger.json"

# El panel publica la hora de Madrid sin zona.
MADRID = timedelta(hours=2)

# El reset del Computer, en UTC.
HORA_DEL_RESET_UTC = 5

NUESTRO = {"SUBASTA_CARTERA", "RENDIJA"}


# LOS INTERRUPTORES DE PRODUCCION DE CADA NOCHE
#
#     `plan_del_reset` lee el entorno. Cada foto se mide con los que
#     estaban puestos en el workflow esa noche, sacados de su propio
#     comentario ("Encendido 21/09", ...). `BORDALAS_SIN_SUBASTA`
#     estuvo puesto la noche del 21 al 22/09 y ninguna foto cae ahi.
ENCENDIDOS = (
    ("2026-09-21", "BORDALAS_JORNADAS_POR_SU_FECHA"),
    ("2026-09-22", "BORDALAS_REVENTA_SOLO_SI_JUEGA"),
    ("2026-09-24", "BORDALAS_EL_ONCE_UNA_VEZ"),
    ("2026-09-25", "BORDALAS_SOLVENCIA_POR_SU_PLAZO"),
    ("2026-09-25", "BORDALAS_LA_MONEDA_DE_LA_LIGA"),
)


def poner_los_de_esa_noche(dia: str) -> list:
    puestos = []
    for desde, nombre in ENCENDIDOS:
        if dia >= desde:
            os.environ[nombre] = "1"
            puestos.append(nombre)
        else:
            os.environ.pop(nombre, None)
    return puestos


def momento(marca) -> datetime:
    m = datetime.fromisoformat(str(marca).replace("Z", "+00:00"))
    return m if m.tzinfo else (m - MADRID).replace(tzinfo=timezone.utc)


def el_reset_siguiente(cuando: datetime) -> datetime:
    reset = cuando.replace(hour=HORA_DEL_RESET_UTC, minute=0, second=0, microsecond=0)
    return reset if reset > cuando else reset + timedelta(days=1)


def main() -> int:

    sys.stdout.reconfigure(encoding="utf-8")

    libro = json.load(open(LIBRO, encoding="utf-8-sig"))["bids"]
    pujas = list(libro.values()) if isinstance(libro, dict) else list(libro)
    ultima_del_libro = max(momento(p["placed_at"]) for p in pujas)

    total = aciertos = sustos = graves = sin_atribuir = 0

    for ruta in FOTOS:
        try:
            foto = json.load(open(ruta, encoding="utf-8-sig"))
        except Exception as error:                  # noqa: BLE001
            print(f"no se pudo leer {ruta}: {error}")
            continue

        hecha = momento((foto.get("meta") or {}).get("generated_at"))
        hasta = el_reset_siguiente(hecha)

        print(f"\n==== FOTO {hecha:%d/%m %H:%M} UTC  ({ruta})  noche hasta {hasta:%d/%m %H:%M} UTC")
        puestos = poner_los_de_esa_noche(hecha.date().isoformat())
        print(f"  interruptores de esa noche: {', '.join(p[9:] for p in puestos) or 'ninguno'}")
        publicada = foto.get("subasta") or {}
        print(f"  la subasta que publico la foto: would_bid {publicada.get('would_bid')}, "
              f"blocked_by {publicada.get('blocked_by')}")

        vieja = foto.get("lista_de_la_noche")
        if vieja:
            print(f"  SOMBRA VIEJA: {vieja.get('reason')}")
            for f in vieja.get("filas") or []:
                print(f"      {f.get('jugador')} pujaria {f.get('lo_que_pujaria')}")
        else:
            print("  SOMBRA VIEJA: la foto es anterior a ella; no la lleva.")

        nueva = la_lista(
            foto.get("acquisition"),
            en_la_ventana(lectura_del_estado(foto, None)),
            foto.get("rendija"),
        )
        print(f"  SOMBRA NUEVA: {nueva['reason'].split(' Cubre')[0]}")
        for f in nueva["filas"]:
            print(f"      {f['jugador']:18s} pujaria {f['lo_que_pujaria']:>9}  por {f['camino']}")
        ventana = nueva["caminos"].get("VENTANA_DEL_RESET") or {}
        if ventana.get("blocked_by"):
            print(f"      ventana: {ventana['blocked_by']} - {ventana['reason'][:120]}")

        if hasta > ultima_del_libro:
            print(f"  LO QUE PASO: la noche no ha terminado en el libro "
                  f"(ultima puja apuntada {ultima_del_libro:%d/%m %H:%M} UTC). No se puntua.")
            continue

        esa_noche = [
            p for p in pujas
            if hecha <= momento(p["placed_at"]) < hasta
        ]
        print("  LO QUE PASO:")
        if not esa_noche:
            print("      ninguna puja en el libro")
        vistos = {}
        for p in sorted(esa_noche, key=lambda p: p["placed_at"]):
            quien = p.get("target_source") or "?"
            print(f"      {momento(p['placed_at']):%d/%m %H:%M} UTC  {p['player_name']:18s} "
                  f"{p['amount']:>9}  {quien} / {p.get('recorded_by')}")
            vistos.setdefault(p["player_name"], quien)

        dichos = {f["jugador"] for f in nueva["filas"]}
        de_pepe = {n for n, q in vistos.items() if q in NUESTRO}
        sin_saber = {n for n, q in vistos.items() if q not in NUESTRO}

        for n in sorted(dichos | de_pepe):
            total += 1
            if n in dichos and n in de_pepe:
                aciertos += 1
                print(f"      ACIERTA        {n}")
            elif n in dichos:
                if n in sin_saber:
                    sin_atribuir += 1
                    print(f"      DICHA, Y HUBO PUJA SIN ATRIBUIR  {n}")
                else:
                    sustos += 1
                    print(f"      SUSTO FALSO    {n}: la dijo y no se pujo")
            else:
                graves += 1
                print(f"      GRAVE          {n}: se pujo y no la dijo")
        if not dichos and not de_pepe:
            total += 1
            aciertos += 1
            print("      ACIERTA        no dijo nada y nuestro codigo no pujo")
        for n in sorted(sin_saber - dichos):
            print(f"      (sin atribuir: {n}, {vistos[n]} - del dueño o de un camino que no apunta)")

    print(f"\nTOTAL: {total} casos puntuados, {aciertos} aciertos, {sustos} sustos falsos, "
          f"{graves} graves, {sin_atribuir} dichos con puja sin atribuir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
