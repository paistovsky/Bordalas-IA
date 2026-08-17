"""
La puerta de validacion de CI, en local y antes de subir.

POR QUE

    El workflow de GitHub corre 27 tests antes de dejar que el
    ciclo toque produccion. Si uno falla, el push no ejecuta nada:
    te enteras cuando ya has subido, y con el equipo parado.

    Esto la corre antes, en tu maquina.

POR QUE LEE LA LISTA DEL YAML

    Para que no puedan divergir. Una copia de la lista aqui se
    quedaria vieja el primer dia que alguien añada un test al
    workflow y no a este fichero, y entonces esto diria "todo bien"
    mientras CI dice que no.

    La lista vive en un sitio: `.github/workflows/bordalas-live.yml`.

USO

    python scripts/run_validation_gate.py

    Parar en el primer fallo:

    python scripts/run_validation_gate.py --parar
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

from pathlib import Path


WORKFLOW = Path(".github/workflows/bordalas-live.yml")


def modulos_del_workflow() -> list[str]:

    if not WORKFLOW.exists():
        print(f"No encuentro {WORKFLOW}.")
        return []

    texto = WORKFLOW.read_text(encoding="utf-8")

    modulos = []

    for encontrado in re.finditer(
        r"python\s+-m\s+([\w.]*test[\w.]*)",
        texto,
    ):

        modulo = encontrado.group(1)

        if modulo not in modulos:
            modulos.append(modulo)

    return modulos


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--parar",
        action="store_true",
        help="detenerse en el primer fallo",
    )

    parser.add_argument(
        "--extra",
        nargs="*",
        default=["src.analysis.test_futbolfantasy_source_v12"],
        help="tests adicionales que no estan en el workflow",
    )

    args = parser.parse_args()

    modulos = modulos_del_workflow()

    for extra in (args.extra or []):
        if extra not in modulos:
            modulos.append(extra)

    if not modulos:
        print("No hay tests que correr.")
        return 1

    print(f"Puerta de validacion: {len(modulos)} tests")
    print("=" * 66)

    fallos = []

    for indice, modulo in enumerate(modulos, start=1):

        proceso = subprocess.run(
            [sys.executable, "-m", modulo],
            capture_output=True,
            text=True,
        )

        corto = modulo.rsplit(".", 1)[-1]

        if proceso.returncode == 0:
            print(f"  {indice:>2}/{len(modulos)}  OK    {corto}")

        else:
            print(f"  {indice:>2}/{len(modulos)}  FALLA {corto}")

            salida = (
                (proceso.stderr or "")
                + (proceso.stdout or "")
            ).strip().splitlines()

            for linea in salida[-6:]:
                print(f"            {linea[:100]}")

            fallos.append(modulo)

            if args.parar:
                break

    print("=" * 66)

    if fallos:
        print(f"FALLAN {len(fallos)} de {len(modulos)}:")
        for modulo in fallos:
            print(f"  - {modulo}")
        print()
        print("NO subas hasta arreglarlos: CI parara el ciclo.")
        return 1

    print(f"Los {len(modulos)} en verde. Se puede subir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
