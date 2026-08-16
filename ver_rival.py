"""
Que ha hecho un rival, segun el tablon.

USO
    python ver_rival.py            todos los managers
    python ver_rival.py Mex        solo ese

Existe porque la pregunta "¿este rival ha comprado algo?" se
respondia mirando codigo o pegando comandos de una linea que
PowerShell no digiere. Es la vista que faltaba.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.analysis.rival_ledger_audit import (
    audit_rival_ledger,
    print_rival_ledger_audit,
)


LEDGER = Path("data/rival_intelligence/rival_intelligence.json")

NOSOTROS = 14175949


def money(value) -> str:
    try:
        return f"{int(value or 0):,}".replace(",", ".") + " EUR"
    except (TypeError, ValueError):
        return "n/d"


def fecha(value) -> str:
    try:
        return datetime.fromtimestamp(
            int(value),
            tz=timezone.utc,
        ).strftime("%d/%m %H:%M")
    except (TypeError, ValueError, OSError):
        return "?"


def main() -> None:

    if not LEDGER.exists():
        print(
            f"No encuentro {LEDGER}. Lanza un ciclo primero para "
            f"que se genere."
        )
        raise SystemExit(1)

    datos = json.loads(
        LEDGER.read_text(encoding="utf-8")
    )

    filtro = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else None
    )

    auditoria = audit_rival_ledger(
        datos,
        own_user_id=NOSOTROS,
    )

    print()
    print("=" * 70)
    print(" QUE HA HECHO CADA RIVAL")
    print("=" * 70)
    print(
        f" Informe generado: {datos.get('generated_at', '?')}"
    )

    for manager in datos.get("managers", []):

        nombre = str(manager.get("name") or "?")

        if filtro and filtro not in nombre.lower():
            continue

        identificador = int(
            manager.get("user_id")
            or manager.get("id")
            or 0
        )

        conciliacion = (
            auditoria.get("by_manager") or {}
        ).get(identificador) or {}

        cobertura = conciliacion.get("coverage")

        print()
        print("-" * 70)
        print(
            f" {nombre}"
            + ("   (nosotros)" if identificador == NOSOTROS else "")
        )
        print("-" * 70)
        print(f"   Saldo estimado:     {money(manager.get('balance'))}")
        print(f"   Puede pujar hasta:  {money(manager.get('maximum_bid'))}")
        print(
            f"   Plantilla:          "
            f"{manager.get('roster_count', 0)} jugadores, "
            f"{money(manager.get('roster_value'))}"
        )
        print(
            f"   Pujas:              "
            f"{manager.get('won_auctions', 0)} ganadas, "
            f"{manager.get('lost_bids', 0)} perdidas"
        )

        if cobertura is not None:
            print(
                f"   Cobertura:          {cobertura * 100:.0f} %"
                f"   ({conciliacion.get('from_initial_draft', 0)} "
                f"del reparto, "
                f"{conciliacion.get('acquired', 0)} fichados, "
                f"{conciliacion.get('explained', 0)} explicados)"
            )

            if conciliacion.get("unexplained"):
                print()
                print(
                    "   SIN EXPLICAR - nos falta historia de este "
                    "manager:"
                )
                for jugador in conciliacion["unexplained"]:
                    print(
                        f"     {jugador['name']:<22}"
                        f"{money(jugador['value']):>16}   "
                        f"desde {fecha(jugador['owner_since'])}"
                    )

        operaciones = manager.get("transactions") or []

        print()

        if not operaciones:
            print("   Sin operaciones registradas.")

        else:
            print(f"   Operaciones ({len(operaciones)}):")

            for operacion in sorted(
                operaciones,
                key=lambda item: int(item.get("date") or 0),
            ):
                signo = (
                    "-"
                    if "BUY" in str(operacion.get("kind"))
                    else "+"
                )
                print(
                    f"     {fecha(operacion.get('date'))}  "
                    f"{str(operacion.get('kind', '?')):<20}"
                    f"{str(operacion.get('player_name', '?')):<22}"
                    f"{signo}{money(operacion.get('amount')):>16}"
                )

    print_rival_ledger_audit(auditoria)


if __name__ == "__main__":
    main()
