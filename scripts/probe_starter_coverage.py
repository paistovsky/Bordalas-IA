"""
Comprueba si el pronostico de titularidad llega al mercado.

POR QUE HACE FALTA

    La regla del once rechaza sustituir a un titular confirmado
    por alguien que no lo es. Si del mercado no llega pronostico,
    esa regla lo bloquea TODO y "Pujables: 0" se parece mucho a
    "hoy no hay chollos". No son lo mismo.

    Este script separa las dos cosas mirando el dato en crudo.

QUE HACE

    1. Fuerza el refresco de Jornada Perfecta con el proveedor
       nuevo, saltandose la cache de 2 horas.
    2. Cuenta a cuantos jugadores del MERCADO ha conseguido poner
       identidad.
    3. Reconstruye el tablero de fichajes y ensena, candidato a
       candidato, que pronostico tiene y por que pasa o no pasa.

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

from src.analysis.candidate_starter_lookup import (  # noqa: E402
    describe_lookup,
    get_starter_lookup,
    reset_starter_lookup_cache,
)

from src.analysis.price_history_engine import (  # noqa: E402
    get_snapshot_files,
    load_raw_snapshot,
)

from src.intelligence.jornada_perfecta_provider import (  # noqa: E402
    build_market_records,
    refresh_jornada_perfecta_data,
)


def titulo(texto: str) -> None:
    print()
    print("-" * 70)
    print(texto)
    print("-" * 70)


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

    mercado = build_market_records(snapshot)

    print(
        f"Candidatos del mercado (no nuestros): {len(mercado)}"
    )

    # ------------------------------------------------------
    # 1. REFRESCO FORZADO
    # ------------------------------------------------------

    titulo("REFRESCO DE JORNADA PERFECTA (forzado)")

    from src.analysis.calendar_state import (  # noqa: E402
        build_calendar_state,
    )

    calendario = build_calendar_state(snapshot)

    jornada = calendario.get("target_matchday") or 1

    print(f"  Jornada objetivo:        {jornada}")

    try:
        respuesta = refresh_jornada_perfecta_data(
            snapshot=snapshot,
            target_matchday=int(jornada),
            seconds_to_deadline=None,
            force=True,
        )
    except Exception as error:
        print(f"  FALLO: {type(error).__name__}: {error}")
        return

    datos = respuesta.get("data") or {}
    meta = datos.get("metadata") or {}

    print(f"  Jornada:                 {datos.get('round')}")
    print(f"  Senales leidas:          {meta.get('raw_signals')}")
    print(f"  Equipos parseados:       {meta.get('parsed_teams')}")
    print(
        f"  Emparejados plantilla:   "
        f"{meta.get('matched_roster_players')}"
    )
    print(
        f"  Emparejados mercado:     "
        f"{meta.get('matched_market_players')}"
    )

    # ------------------------------------------------------
    # 2. EL LOOKUP
    # ------------------------------------------------------

    titulo("PRONOSTICO DISPONIBLE")

    reset_starter_lookup_cache()
    lookup = get_starter_lookup()

    print(f"  {describe_lookup(lookup)}")

    del_mercado = [
        (registro, lookup.get(registro["id"]))
        for registro in mercado
    ]

    con_dato = [
        par for par in del_mercado if par[1] is not None
    ]

    print(
        f"  Del mercado con pronostico: "
        f"{len(con_dato)}/{len(mercado)}"
    )

    deducidos = sum(
        1 for _, senal in con_dato if senal.get("inferred")
    )

    print(
        f"  De ellos, leidos de la alineacion: "
        f"{len(con_dato) - deducidos}   "
        f"deducidos por ausencia: {deducidos}"
    )
    print()

    for registro, senal in sorted(
        con_dato,
        key=lambda par: par[1]["probability"],
    ):
        print(
            f"    {str(registro['name'])[:24]:<24} "
            f"{senal['probability']:>5.1f} %  "
            f"{str(senal['consensus']):<10} "
            f"{str(senal.get('status') or ''):<12} "
            + (
                "(deducido: no aparece en el once de su equipo)"
                if senal.get("inferred")
                else "(leido de la alineacion)"
            )
        )

    sin_dato = [
        registro
        for registro, senal in del_mercado
        if senal is None
    ]

    if sin_dato:
        print()
        print(f"  Sin pronostico ({len(sin_dato)}):")
        for registro in sin_dato:
            print(
                f"    {str(registro['name'])[:24]:<24} "
                f"{registro.get('team')}"
            )

    # ------------------------------------------------------
    # 3. EL TABLERO
    # ------------------------------------------------------

    titulo("TABLERO DE FICHAJES")

    presupuesto = (
        ((snapshot.get("market") or {}).get("status") or {})
        .get("maximumBid")
    )

    tablero = build_acquisition_board(
        snapshot,
        {},
        None,
        presupuesto,
        limit=20,
    )

    if not tablero.get("available"):
        print(f"  No disponible: {tablero.get('reason')}")
        return

    print(f"  {tablero.get('starter_coverage')}")
    print()

    for fila in (tablero.get("targets") or []):
        print(
            f"  {str(fila.get('name'))[:22]:<22} "
            f"{str(fila.get('intent') or '-'):<12} "
            f"puja={fila.get('bid'):>9,} "
            f"{str(fila.get('decision')):<26} "
            f"tit={fila.get('starter_probability')}"
        )

        motivo = fila.get("xi_reason") or fila.get("reason")

        if fila.get("decision") != "BID" and motivo:
            print(f"      {str(motivo)[:100]}")


if __name__ == "__main__":
    main()
