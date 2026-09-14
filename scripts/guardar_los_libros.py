"""
Guarda los libros en git, y SOLO si han cambiado.

POR QUE (14/09/2026)

    Los libros vivian unicamente en la cache de GitHub Actions,
    que se desaloja a los 7 dias sin uso. El ciclo ya estuvo
    parado 24 dias en agosto.

    Ahora van a git. Este script es lo que los mete, y corre al
    final de cada vuelta.

UN COMMIT POR CAMBIO REAL, NO UNO POR VUELTA

    El ciclo corre unas 23 veces al dia. Un commit por vuelta
    serian 8.400 commits al año que no dicen nada, y el historial
    dejaria de servir para lo unico que sirve: ver cuando cambio
    algo de verdad.

    Asi que se mira lo que git tiene en el indice DESPUES de
    añadir los libros. Si no hay nada preparado, no se escribe
    nada y se dice.

NADA DE `git add -A`

    Se añaden los libros uno a uno, por su ruta. Regla de la
    casa, y aqui tiene un motivo concreto ademas: en la maquina
    del ciclo hay 24 fotos de medio mega y un `data/ff_html` de
    38 MB. Un `-A` los meteria todos.

NO EMPUJA SALVO QUE SE LE PIDA

    `--empujar` es explicito y va en la linea del workflow. Sin
    el, este script commitea en local y no toca el remoto: quien
    lo pruebe a mano no puede publicar nada sin querer.

USO

    python scripts/guardar_los_libros.py                (local)
    python scripts/guardar_los_libros.py --empujar      (el ciclo)
    python scripts/guardar_los_libros.py --gitignore    (regenera)
    python scripts/guardar_los_libros.py --censo        (que hay)

============================================================
EL PASO QUE FALTA, Y QUE NO PONGO YO
============================================================

`.github/workflows/bordalas-live.yml` es del dueño. Aqui queda
escrito exactamente que hay que cambiar; son DOS cosas.

1. EL PERMISO. Hoy dice, en la linea 37:

       permissions:
         contents: read
         actions: read

   Tiene que decir:

       permissions:
         contents: write
         actions: read

   `contents: write` es lo que deja al `GITHUB_TOKEN` empujar al
   repo. `actions/checkout` ya guarda las credenciales por
   defecto (`persist-credentials: true`), asi que no hace falta
   ningun secreto nuevo ni ningun token personal.

2. EL PASO. Va DESPUES de "Prune persisted state" —que hoy
   empieza en la linea 177— y antes de "Upload diagnostic log".
   Asi se guarda lo que quede tras el borrado de fotos:

       - name: Guardar los libros
         if: always()
         shell: bash
         run: |
           git config user.name  "bordalas-ciclo"
           git config user.email "ciclo@bordalas.local"
           python scripts/guardar_los_libros.py --empujar

   `if: always()` para que los libros se guarden aunque la vuelta
   haya fallado: una vuelta rota tambien escribio cosas, y son
   justo las que interesa no perder.

============================================================
EL RESCATE, Y EL ORDEN IMPORTA
============================================================

MEDIDO EL 14/09: el libro del marcador de PRODUCCION tiene SIETE
jornadas —4899, 4900, 4901, 4902, 4903, 4904 y 4937— y el que hay
en la maquina del dueño tiene TRES. Las cuatro que faltan aqui
incluyen la 4900 y la 4901, que son justo el hueco por el que la
jornada 4 sale sin medir.

POR ESO ESTA RAMA NO COMMITEA NINGUN LIBRO.

    En cada vuelta, el orden es: `checkout` (linea 68) trae lo
    que haya en git, y DESPUES `Restore Bordalas state` (linea
    95) descomprime la cache encima. La cache gana.

    Asi que si se commiteara ahora el libro local de tres
    jornadas y la cache siguiera viva, la cache lo pisaria y no
    pasaria nada malo. Pero si la cache ya se hubiera desalojado,
    ese libro de tres jornadas se quedaria como el bueno Y
    PARECERIA CORRECTO: habriamos perdido cuatro jornadas sin que
    nada lo dijera.

    Con git vacio, si la cache se ha ido, se ve.

    EL ORDEN DEL RESCATE:

        1. Pegar el permiso y el paso.
        2. Dejar correr UNA vuelta. Esa vuelta commitea los
           libros que haya en la cache — los siete del marcador.
        3. Comprobar en el commit que salen siete.
        4. A partir de ahi, git es la fuente de verdad.

    LA VENTANA: la cache se desaloja a los 7 dias sin usarse. La
    ultima vuelta de produccion fue el 14/09 a las 18:12.

Y UN EFECTO DE PROPINA. `data/solvency` NO esta en las rutas de
la cache, asi que hoy sus tres libros empiezan vacios en cada
vuelta y se tiran al acabar: en produccion no acumulan nada.
Metiendolos en git se arregla solo, porque entonces es el
`checkout` quien los trae y el commit quien los guarda. Para los
libros, git sustituye a la cache.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(RAIZ))

from src.estado.los_libros import (           # noqa: E402
    LIBROS,
    existentes,
    lineas_para_gitignore,
    rutas,
)


def git(*args, permitir_fallo: bool = False) -> tuple:
    """Corre git y devuelve `(codigo, salida)`. Nunca lanza."""

    proceso = subprocess.run(
        ["git", *args],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    salida = (
        (proceso.stdout or "") + (proceso.stderr or "")
    ).strip()

    if proceso.returncode and not permitir_fallo:
        print(f"  git {' '.join(args)} -> {proceso.returncode}")
        print(f"  {salida}")

    return proceso.returncode, salida


def censo() -> int:
    """Que libros hay, cuanto pesan y cuantas entradas tienen."""

    print("LOS LIBROS")
    print("=" * 66)

    total = 0.0

    hay = set(existentes(RAIZ))

    for libro in LIBROS:

        ruta = libro["ruta"]

        fichero = RAIZ / ruta

        if ruta not in hay:
            print(f"  {'-':>9}  {ruta}   (todavia no existe)")
            continue

        kb = fichero.stat().st_size / 1024.0

        total += kb

        # Las entradas, contadas y no supuestas: una linea por
        # entrada en los `.jsonl`; en los `.json` no se adivina.
        if fichero.suffix == ".jsonl":
            try:
                entradas = len([
                    linea
                    for linea in fichero.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                    if linea.strip()
                ])
            except OSError:
                entradas = "?"

            cuantas = f"{entradas} entradas"

        else:
            cuantas = ""

        print(f"  {kb:>8.1f} KB  {ruta}   {cuantas}")

    print("=" * 66)
    print(f"  {total:>8.1f} KB  en total, {len(hay)} de {len(LIBROS)}")

    return 0


def regenerar_gitignore() -> int:
    """Reescribe el bloque de los libros en el `.gitignore`."""

    print("Las lineas que dejan pasar los libros:")
    print()

    for linea in lineas_para_gitignore():
        print(f"  {linea}")

    print()
    print(
        "Peguelas en `.gitignore` sustituyendo el bloque "
        "anterior, o compruebe que ya estan: la guardia "
        "`test_los_libros_no_estan_ignorados` lo verifica."
    )

    return 0


def guardar(empujar: bool) -> int:
    """Añade los libros y commitea SOLO si hay cambios."""

    hay = existentes(RAIZ)

    if not hay:
        print(
            "No hay ningun libro en el disco todavia: no hay "
            "nada que guardar."
        )
        return 0

    # 1. AÑADIR, UNO A UNO Y POR SU RUTA.
    #
    #     `--` separa las rutas de las opciones: un fichero que
    #     empezara por `-` no se interpretaria como bandera.
    for ruta in hay:
        git("add", "--", ruta)

    # 2. ¿HA CAMBIADO ALGO DE VERDAD?
    #
    #     `diff --cached --quiet` devuelve 1 si hay algo
    #     preparado y 0 si no. Es la pregunta exacta: no "¿hay
    #     ficheros?" sino "¿ha cambiado su contenido?".
    codigo, _ = git(
        "diff", "--cached", "--quiet", "--", *hay,
        permitir_fallo=True,
    )

    if codigo == 0:
        print(
            f"Los {len(hay)} libros estan igual que en el ultimo "
            f"commit: no se escribe nada."
        )
        return 0

    # 3. QUE CAMBIO, CON NOMBRE. Va al mensaje del commit para
    #    que el historial se pueda leer sin abrir el diff.
    _, cambiados = git(
        "diff", "--cached", "--name-only", "--", *hay
    )

    nombres = [
        linea.strip()
        for linea in cambiados.splitlines()
        if linea.strip()
    ]

    print(f"Cambian {len(nombres)} libro(s):")

    for nombre in nombres:
        print(f"  {nombre}")

    mensaje = (
        "libros: "
        + ", ".join(
            Path(n).name for n in nombres[:6]
        )
        + (f" (+{len(nombres) - 6})" if len(nombres) > 6 else "")
        + "\n\n"
        + "Escrito por el ciclo. Un commit por cambio real: si\n"
        + "los libros no cambian, la vuelta no escribe nada.\n\n"
        + "Autor-real: Claude Code (VS Code)\n"
    )

    codigo, salida = git("commit", "-m", mensaje)

    if codigo:
        print("No se pudo commitear.")
        return 1

    print("Commit hecho.")

    if not empujar:
        print(
            "No se empuja: hace falta `--empujar`, que solo "
            "lleva la linea del workflow."
        )
        return 0

    codigo, salida = git("push")

    if codigo:
        print("No se pudo empujar.")
        return 1

    print("Empujado.")

    return 0


def main() -> int:

    parser = argparse.ArgumentParser(
        description="Guarda los libros en git si han cambiado."
    )

    parser.add_argument(
        "--empujar",
        action="store_true",
        help="Empuja el commit. Solo lo usa el ciclo.",
    )

    parser.add_argument(
        "--gitignore",
        action="store_true",
        help="Enseña las lineas del `.gitignore`.",
    )

    parser.add_argument(
        "--censo",
        action="store_true",
        help="Que libros hay y cuanto pesan.",
    )

    args = parser.parse_args()

    if args.gitignore:
        return regenerar_gitignore()

    if args.censo:
        return censo()

    return guardar(args.empujar)


if __name__ == "__main__":
    raise SystemExit(main())
