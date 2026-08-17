"""
Descarga el HTML crudo de las paginas de equipo de FutbolFantasy.

POR QUE HACE FALTA

    El plan dice, con razon, que el inventario de inteligencia de
    FF esta "sin verificar contra el HTML" y que hay que mirarlo
    antes de disenar encima. Esto lo mira.

    Ademas audita el mapa de slugs: los 20 equipos de LaLiga
    salen del catalogo del snapshot, no de una lista escrita a
    mano, asi que si `FF_TEAM_SLUGS` se ha quedado corto o viejo
    se ve aqui y no dentro del scraper.

QUE HACE

    1. Lee el ultimo snapshot de data/.
    2. Saca los equipos del catalogo (los 20) y les resuelve slug
       con la misma funcion que usa el scraper de verdad.
    3. Descarga cada pagina y la guarda cruda en
       data/ff_html/<slug>.html.
    4. Imprime el resumen: equipos sin slug, fallos de red,
       tamano de cada pagina.

    NO escribe nada en Biwenger. Solo descarga y guarda en disco.

USO

    python scripts/dump_ff_team_html.py

    Solo los tres primeros equipos (mas rapido para una ojeada):

    python scripts/dump_ff_team_html.py --limit 3
"""

from __future__ import annotations

import argparse
import sys
import time

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests  # noqa: E402

from src.analysis.price_history_engine import (  # noqa: E402
    get_snapshot_files,
    load_raw_snapshot,
)

# Se lee del proveedor NUEVO a proposito. Cuando esto apuntaba al
# modulo multifuente, la auditoria de slugs describia el mapa que
# ya no se usa: decia "Atletico -> SIN SLUG" y mandaba al Rayo a
# un 404 que el proveedor nuevo ya no comete. Una auditoria que
# mide el codigo viejo no es una auditoria.
from src.intelligence.futbolfantasy_provider import (  # noqa: E402
    FF_BASE,
    HEADERS,
    TIMEOUT,
    team_slug as ff_team_slug,
)


OUTPUT_DIR = Path("data/ff_html")


def catalog_team_names(snapshot: dict) -> list[str]:
    """
    Los equipos tal y como los nombra el catalogo de Biwenger.

    Es la lista buena: es la que veran `build_roster_records` y
    `build_market_records`, asi que un slug que falle aqui falla
    tambien en produccion.
    """

    teams = (
        (snapshot or {})
        .get("catalog", {})
        .get("data", {})
        .get("teams", {})
        or {}
    )

    nombres = []

    for team in teams.values():

        if not isinstance(team, dict):
            continue

        nombre = team.get("name")

        if nombre and nombre not in nombres:
            nombres.append(nombre)

    return sorted(nombres)


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="descargar solo los N primeros equipos",
    )

    parser.add_argument(
        "--pause",
        type=float,
        default=1.5,
        help="segundos de espera entre descargas",
    )

    args = parser.parse_args()

    ficheros = get_snapshot_files()

    if not ficheros:
        print("No hay snapshots en data/. Corre un ciclo antes.")
        return

    snapshot = load_raw_snapshot(ficheros[-1])

    if not snapshot:
        print(f"No se ha podido leer {ficheros[-1]}.")
        return

    print(f"Snapshot: {Path(ficheros[-1]).name}")

    equipos = catalog_team_names(snapshot)

    print(f"Equipos en el catalogo: {len(equipos)}")
    print()

    # --------------------------------------------------
    # 1. AUDITORIA DE SLUGS
    # --------------------------------------------------

    print("-" * 66)
    print("MAPA DE SLUGS")
    print("-" * 66)

    con_slug = []
    sin_slug = []

    for nombre in equipos:

        slug = ff_team_slug(nombre)

        if slug:
            con_slug.append((nombre, slug))
        else:
            sin_slug.append(nombre)

        print(f"  {nombre:<24} -> {slug or 'SIN SLUG'}")

    print()
    print(f"  Con slug: {len(con_slug)}   sin slug: {len(sin_slug)}")

    if sin_slug:
        print()
        print("  SIN SLUG (estos equipos hoy no se scrapean):")
        for nombre in sin_slug:
            print(f"    - {nombre}")

    if not con_slug:
        print()
        print("Ningun equipo resuelve slug. No hay nada que descargar.")
        return

    # --------------------------------------------------
    # 2. DESCARGA
    # --------------------------------------------------

    objetivo = con_slug[: args.limit] if args.limit else con_slug

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("-" * 66)
    print(f"DESCARGA ({len(objetivo)} paginas) -> {OUTPUT_DIR}")
    print("-" * 66)

    session = requests.Session()

    fallos = []

    for indice, (nombre, slug) in enumerate(objetivo):

        url = f"{FF_BASE}/laliga/equipos/{slug}"

        try:
            respuesta = session.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            respuesta.raise_for_status()

        except Exception as error:
            fallos.append((nombre, f"{type(error).__name__}: {error}"))
            print(f"  {nombre:<24} FALLO  {type(error).__name__}")
            continue

        destino = OUTPUT_DIR / f"{slug}.html"

        destino.write_text(respuesta.text, encoding="utf-8")

        print(
            f"  {nombre:<24} OK     "
            f"{len(respuesta.text):>8,} bytes  -> {destino.name}"
        )

        if indice < len(objetivo) - 1 and args.pause > 0:
            time.sleep(args.pause)

    print()

    if fallos:
        print(f"Fallos ({len(fallos)}):")
        for nombre, motivo in fallos:
            print(f"  - {nombre}: {motivo}")
    else:
        print("Sin fallos de descarga.")

    # --------------------------------------------------
    # 3. PARTES DE BAJA
    #
    # Las paginas de equipo dicen que un jugador esta
    # lesionado, pero no hasta cuando. Y esa es justo la
    # diferencia entre una gripe y un cruzado: hoy los dos
    # salen al 0 % de titularidad.
    #
    # Estas dos paginas cubren la liga entera de una vez.
    # --------------------------------------------------

    print()
    print("-" * 66)
    print("PARTES DE BAJA")
    print("-" * 66)

    for nombre, ruta in (
        ("Lesionados", "laliga/lesionados"),
        ("Sancionados", "laliga/sancionados"),
    ):

        url = f"{FF_BASE}/{ruta}"

        try:
            respuesta = session.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            respuesta.raise_for_status()

        except Exception as error:
            print(f"  {nombre:<24} FALLO  {type(error).__name__}")
            continue

        destino = OUTPUT_DIR / f"{ruta.split('/')[-1]}.html"

        destino.write_text(respuesta.text, encoding="utf-8")

        print(
            f"  {nombre:<24} OK     "
            f"{len(respuesta.text):>8,} bytes  -> {destino.name}"
        )

        if args.pause > 0:
            time.sleep(args.pause)

    print()
    print(f"HTML guardado en: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
