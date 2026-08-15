"""
¿Los fallos que veo los he causado yo, o ya estaban?

Responde a esa pregunta y a ninguna otra.

COMO
    Cada fichero que se modifico en la sesion del 15/08/2026 tiene
    al lado su copia *.ORIGINAL.bak con el contenido anterior.

    Este script hace una copia completa del proyecto en una
    carpeta temporal, restaura ahi los .bak sobre sus destinos, y
    ejecuta los mismos tests contra las dos versiones.

    Tu proyecto NO se toca. Todo ocurre en la copia.

INTERPRETACION
    PREEXISTENTE   fallaba antes y sigue fallando -> no es cosa
                   nuestra
    REGRESION      pasaba antes y ahora falla    -> hay que
                   mirarlo YA
    ARREGLADO      fallaba antes y ahora pasa    -> ganancia
    ESTABLE        pasa en ambas

USO
    python regression_check.py                 tests que fallan hoy
    python regression_check.py --todos         los 125
    python regression_check.py --lista a,b,c   solo esos
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


RAIZ = Path(__file__).resolve().parent
TIMEOUT = 150

IGNORAR = shutil.ignore_patterns(
    "__pycache__",
    ".venv",
    ".git",
    "node_modules",
    "dashboard-v8",
    "*.pyc",
    "backups",
)

# Los que fallaron en el chequeo de salud del 15/08.
SOSPECHOSOS = [
    "src.analysis.test_accept_before_expiry_execution_planner_v1",
    "src.analysis.test_accept_before_expiry_orchestrator_v1",
    "src.analysis.test_bid_engine",
    "src.analysis.test_competitive_transactions_real",
    "src.analysis.test_deadline_engine",
    "src.analysis.test_fixture_analyzer",
    "src.analysis.test_lineup_engine",
    "src.analysis.test_market_analyzer",
    "src.analysis.test_market_trend_engine",
    "src.analysis.test_offer_decision_orchestrator_v2",
    "src.analysis.test_rival_intelligence_v1",
    "src.analysis.test_rival_intelligence_v2",
    "src.analysis.test_solvency_engine",
    "src.analysis.test_strategic_decision_gate",
    "src.analysis.test_team_analyzer",
    "src.intelligence.test_injuries_api",
    "src.test_client",
]


def color(texto, codigo):
    if os.name == "nt" and not os.environ.get("WT_SESSION"):
        return texto
    return f"\033[{codigo}m{texto}\033[0m"


def verde(t): return color(t, "32")
def rojo(t): return color(t, "31")
def amarillo(t): return color(t, "33")
def gris(t): return color(t, "90")


def localizar_backups() -> list[Path]:
    return sorted(
        RAIZ.rglob("*.ORIGINAL.bak")
    )


def preparar_copia_original(destino: Path) -> list[str]:
    """
    Copia el proyecto y deshace los cambios de la sesion.
    """
    shutil.copytree(
        RAIZ,
        destino,
        ignore=IGNORAR,
        dirs_exist_ok=True,
    )

    restaurados = []

    for backup in sorted(destino.rglob("*.ORIGINAL.bak")):

        objetivo = Path(
            str(backup).replace(
                ".ORIGINAL.bak",
                "",
            )
        )

        shutil.copy2(backup, objetivo)

        restaurados.append(
            str(
                objetivo.relative_to(destino)
            )
        )

    return restaurados


def ejecutar(
    modulo: str,
    cwd: Path,
) -> bool:

    entorno = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }

    try:
        proceso = subprocess.run(
            [sys.executable, "-m", modulo],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            encoding="utf-8",
            errors="ignore",
            env=entorno,
        )

    except subprocess.TimeoutExpired:
        return False

    return proceso.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--todos", action="store_true")
    parser.add_argument("--lista", default="")
    args = parser.parse_args()

    backups = localizar_backups()

    print("=" * 78)
    print(" BORDALAS IA - COMPARACION ANTES / DESPUES")
    print("=" * 78)

    if not backups:
        print(
            rojo(
                " No hay ficheros *.ORIGINAL.bak. Sin ellos no "
                "se puede reconstruir la version anterior."
            )
        )
        raise SystemExit(1)

    print(f"Copias de seguridad encontradas: {len(backups)}")
    for backup in backups:
        print(gris(f"  {backup.relative_to(RAIZ)}"))

    if args.lista:
        modulos = [
            item.strip()
            for item in args.lista.split(",")
            if item.strip()
        ]

    elif args.todos:
        modulos = sorted(
            ".".join(
                fichero.relative_to(RAIZ)
                .with_suffix("")
                .parts
            )
            for fichero in RAIZ.rglob("src/**/test_*.py")
            if "__pycache__" not in fichero.parts
        )

    else:
        modulos = SOSPECHOSOS

    print()
    print(f"Tests a comparar: {len(modulos)}")

    temporal = Path(
        tempfile.mkdtemp(
            prefix="bordalas_original_",
        )
    )

    try:
        print()
        print("Preparando copia con el codigo ANTERIOR...")

        restaurados = preparar_copia_original(temporal)

        print(f"  {len(restaurados)} ficheros revertidos:")
        for item in restaurados:
            print(gris(f"    {item}"))

        print()
        print("-" * 78)
        print(
            f"{'TEST':<52}{'ANTES':>8}{'AHORA':>8}{'':>10}"
        )
        print("-" * 78)

        veredictos = {}
        inicio = time.perf_counter()

        for modulo in modulos:

            corto = modulo.replace("src.", "")

            print(f"{corto:<52}", end="", flush=True)

            antes = ejecutar(modulo, temporal)
            ahora = ejecutar(modulo, RAIZ)

            if antes and ahora:
                veredicto = "ESTABLE"
                marca = verde("ESTABLE")

            elif not antes and not ahora:
                veredicto = "PREEXISTENTE"
                marca = amarillo("PREEXISTENTE")

            elif antes and not ahora:
                veredicto = "REGRESION"
                marca = rojo("REGRESION")

            else:
                veredicto = "ARREGLADO"
                marca = verde("ARREGLADO")

            veredictos.setdefault(
                veredicto,
                [],
            ).append(corto)

            print(
                f"{('OK' if antes else 'falla'):>8}"
                f"{('OK' if ahora else 'falla'):>8}"
                f"  {marca}"
            )

        print("-" * 78)
        print()
        print("=" * 78)
        print(" VEREDICTO")
        print("=" * 78)

        for clave in (
            "REGRESION",
            "ARREGLADO",
            "PREEXISTENTE",
            "ESTABLE",
        ):
            items = veredictos.get(clave, [])
            if items:
                print(f"  {clave:<14} {len(items)}")

        print(
            f"  {'TIEMPO':<14} "
            f"{time.perf_counter() - inicio:.0f}s"
        )

        regresiones = veredictos.get("REGRESION", [])

        print()

        if regresiones:
            print(
                rojo(
                    " REGRESIONES: estos pasaban antes de la "
                    "sesion y ahora fallan"
                )
            )
            for item in regresiones:
                print(rojo(f"    {item}"))
            print()
            print(rojo(" HAY QUE MIRARLO."))
            raise SystemExit(1)

        print(
            verde(
                " NINGUNA REGRESION. Todo lo que falla hoy ya "
                "fallaba antes de tocar nada."
            )
        )

    finally:
        shutil.rmtree(
            temporal,
            ignore_errors=True,
        )


if __name__ == "__main__":
    main()
