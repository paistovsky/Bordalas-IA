"""
Comprueba si el pronostico de titularidad llega al mercado.

POR QUE HACE FALTA

    La regla del once rechaza sustituir a un titular confirmado
    por alguien que no lo es. Si del mercado no llega pronostico,
    esa regla lo bloquea TODO y "Pujables: 0" se parece mucho a
    "hoy no hay chollos". No son lo mismo.

    Este script separa las dos cosas mirando el dato en crudo.

QUE CAMBIO EL 17/08/2026

    Mide FutbolFantasy, que es la fuente unica. Jornada Perfecta y
    el consenso multifuente estan retirados.

QUE HACE

    1. Fuerza el refresco del tablero de FF, saltandose la cache.
    2. Cuenta a cuantos jugadores del MERCADO llega, y por que via
       se emparejaron.
    3. Reconstruye el tablero de fichajes y ensena, candidato a
       candidato, que pronostico y que jerarquia tiene.

    NO escribe nada en Biwenger. Solo lee y scrapea.

USO

    python scripts/probe_starter_coverage.py
"""

from __future__ import annotations

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.acquisition_board import (  # noqa: E402
    build_acquisition_board,
)

from src.analysis.calendar_state import (  # noqa: E402
    build_calendar_state,
)

from src.analysis.candidate_starter_lookup import (  # noqa: E402
    describe_lookup,
    get_starter_lookup,
    reset_starter_lookup_cache,
)

from src.analysis.price_history_engine import (  # noqa: E402
    get_snapshot_files,
    load_raw_snapshot,
)

from src.intelligence.futbolfantasy_provider import (  # noqa: E402
    build_targets,
    refresh_board,
)


def titulo(texto: str) -> None:
    print()
    print("-" * 74)
    print(texto)
    print("-" * 74)


def main() -> None:

    ficheros = get_snapshot_files()

    if not ficheros:
        print("No hay snapshots en data/. Corre un ciclo antes.")
        return

    ultimo = ficheros[-1]
    snapshot = load_raw_snapshot(ultimo)

    if not snapshot:
        print(f"No se ha podido leer {ultimo}.")
        return

    print(f"Snapshot: {Path(ultimo).name}")

    objetivos = build_targets(snapshot)

    mercado = [o for o in objetivos if o["scope"] == "MARKET"]
    plantilla = [o for o in objetivos if o["scope"] == "ROSTER"]

    print(
        f"Objetivos: {len(objetivos)}   "
        f"plantilla {len(plantilla)}   mercado {len(mercado)}"
    )

    # ------------------------------------------------------
    # 1. REFRESCO FORZADO
    # ------------------------------------------------------

    titulo("REFRESCO DE FUTBOLFANTASY (forzado)")

    calendario = build_calendar_state(snapshot) or {}

    jornada = int(calendario.get("target_matchday") or 1)

    print(f"  Jornada objetivo:        {jornada}")
    print("  Bajando paginas de equipo...")

    try:
        tablero = refresh_board(
            snapshot,
            jornada,
            force=True,
        )

    except Exception as error:
        print(f"  FALLO: {type(error).__name__}: {error}")
        return

    meta = tablero.get("metadata") or {}

    print(f"  Estado cache:            "
          f"{(tablero.get('cache') or {}).get('status')}")

    print(f"  Equipos pedidos:         {meta.get('teams_requested')}")
    print(f"  Paginas bajadas:         {meta.get('team_pages')}")
    print(f"  Emparejados:             {meta.get('matched')}"
          f" / {meta.get('targets')}")
    print(f"    de plantilla:          {meta.get('matched_roster')}"
          f" / {meta.get('targets_roster')}")
    print(f"    de mercado:            {meta.get('matched_market')}"
          f" / {meta.get('targets_market')}")

    print(f"  Vias de emparejamiento:  {meta.get('methods')}")

    for clave, titulo_aviso in (
        ("no_slug", "Equipos sin slug (no se scrapean)"),
        ("no_team", "Jugadores sin equipo en el catalogo"),
        ("errors", "Errores de descarga o parseo"),
        ("unknown_availability_codes", "Estados que FF sirve y no sabemos leer"),
    ):

        valores = meta.get(clave) or []

        if valores:
            print()
            print(f"  {titulo_aviso} ({len(valores)}):")
            for valor in valores:
                print(f"    - {valor}")

    # ------------------------------------------------------
    # 2. EL LOOKUP
    # ------------------------------------------------------

    titulo("PRONOSTICO DISPONIBLE")

    reset_starter_lookup_cache()
    lookup = get_starter_lookup()

    print(f"  {describe_lookup(lookup)}")

    del_mercado = [
        (objetivo, lookup.get(objetivo["id"]))
        for objetivo in mercado
    ]

    con_dato = [par for par in del_mercado if par[1] is not None]

    print()
    print(
        f"  Del mercado con pronostico: "
        f"{len(con_dato)}/{len(mercado)}"
    )
    print()

    for objetivo, senal in sorted(
        con_dato,
        key=lambda par: par[1]["probability"],
        reverse=True,
    ):

        jerarquia = senal.get("hierarchy_label") or "sin definir"

        print(
            f"    {str(objetivo['name'])[:22]:<22} "
            f"{senal['probability']:>5.1f} %  "
            f"{str(senal.get('consensus')):<10} "
            f"{jerarquia:<12} "
            f"{str(senal.get('status') or ''):<14} "
            f"{str(senal.get('parser_role') or '')}"
        )

    sin_dato = [
        objetivo
        for objetivo, senal in del_mercado
        if senal is None
    ]

    if sin_dato:
        print()
        print(f"  Sin pronostico ({len(sin_dato)}):")
        for objetivo in sin_dato:
            print(
                f"    {str(objetivo['name'])[:22]:<22} "
                f"{objetivo.get('team')}"
            )

    # ------------------------------------------------------
    # 3. EL TABLERO
    # ------------------------------------------------------

    titulo("TABLERO DE FICHAJES")

    presupuesto = (
        ((snapshot.get("market") or {}).get("status") or {})
        .get("maximumBid")
    )

    tablero_fichajes = build_acquisition_board(
        snapshot,
        {},
        None,
        presupuesto,
        limit=20,
    )

    if not tablero_fichajes.get("available"):
        print(f"  No disponible: {tablero_fichajes.get('reason')}")
        return

    print(f"  {tablero_fichajes.get('starter_coverage')}")
    print()

    for fila in (tablero_fichajes.get("targets") or []):

        senal = lookup.get(fila.get("id")) or {}

        print(
            f"  {str(fila.get('name'))[:22]:<22} "
            f"{str(fila.get('intent') or '-'):<12} "
            f"puja={fila.get('bid'):>9,} "
            f"{str(fila.get('decision')):<16} "
            f"tit={fila.get('starter_probability')} "
            f"jer={senal.get('hierarchy_label') or '-'}"
        )

        motivo = fila.get("xi_reason") or fila.get("reason")

        if fila.get("decision") != "BID" and motivo:
            print(f"      {str(motivo)[:100]}")


if __name__ == "__main__":
    main()
