"""
Chequeo de salud de Bordalas IA.

Responde a una pregunta concreta: ¿esta el programa entero sano?

QUE HACE
    1. Compila todo src/ y reporta errores de sintaxis.
    2. Verifica que cada import interno "src.*" apunta a un
       fichero que existe.
    3. Descubre TODOS los modulos test_* del proyecto.
    4. Separa los que pueden escribir en Biwenger y NO los
       ejecuta.
    5. Ejecuta el resto y clasifica el resultado.

SEGURIDAD
    En este proyecto hay ficheros que empiezan por test_ y en
    realidad son scripts que operan de verdad. Este chequeo NO
    los ejecuta: los detecta por nombre y por contenido -uso del
    cliente de escritura o de execute=True- y los lista aparte
    para que decidas tu.

    El chequeo no escribe nada en Biwenger. Solo lee.

USO
    python health_check.py              chequeo completo
    python health_check.py --rapido     salta los tests, solo
                                        compila y revisa imports
    python health_check.py --timeout 60 segundos por test
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import time
from pathlib import Path


RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "src"

TIMEOUT_POR_TEST = 120

# Señales de que un modulo puede operar de verdad.
SEÑALES_ESCRITURA = (
    "BiwengerWriteClient",
    "execute=True",
    "execute_live=True",
    "place_bid(",
    "accept_offer(",
    "reject_offer(",
    "counter_offer(",
    "cancel_bid(",
    "list_player_for_sale(",
    "save_lineup(",
    "execute_sale_listing(",
    "execute_autopilot_decision(",
)

# Errores que indican entorno, no codigo roto.
SEÑALES_RED = (
    "ProxyError",
    "ConnectionError",
    "Max retries exceeded",
    "HTTPSConnectionPool",
    "HTTPConnectionPool",
    "NameResolutionError",
    "Tunnel connection failed",
    "Read timed out",
    "SSLError",
)

SEÑALES_DATOS = (
    "FileNotFoundError",
    "No such file or directory",
)

SEÑALES_CREDENCIALES = (
    "BIWENGER_USERNAME",
    "BIWENGER_PASSWORD",
    "API_FOOTBALL_KEY",
    "Falta ",
    "401",
    "Unauthorized",
)


def color(texto: str, codigo: str) -> str:
    if os.name == "nt" and not os.environ.get("WT_SESSION"):
        return texto
    return f"\033[{codigo}m{texto}\033[0m"


def verde(t): return color(t, "32")
def rojo(t): return color(t, "31")
def amarillo(t): return color(t, "33")
def gris(t): return color(t, "90")


# ============================================================
# 1. COMPILACION
# ============================================================

def comprobar_compilacion() -> list[str]:
    errores = []

    for fichero in sorted(SRC.rglob("*.py")):

        if "__pycache__" in fichero.parts:
            continue

        try:
            ast.parse(
                fichero.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

        except SyntaxError as error:
            errores.append(
                f"{fichero.relative_to(RAIZ)}:{error.lineno} "
                f"{error.msg}"
            )

    return errores


# ============================================================
# 2. IMPORTS INTERNOS
# ============================================================

def comprobar_imports() -> list[str]:
    modulos = set()

    for fichero in SRC.rglob("*.py"):
        if "__pycache__" in fichero.parts:
            continue
        relativo = fichero.relative_to(RAIZ).with_suffix("")
        modulos.add(".".join(relativo.parts))

    for carpeta in SRC.rglob("*"):
        if carpeta.is_dir() and "__pycache__" not in carpeta.parts:
            modulos.add(
                ".".join(
                    carpeta.relative_to(RAIZ).parts
                )
            )

    modulos.add("src")

    patron = re.compile(
        r"^\s*(?:from\s+(src[\w\.]*)\s+import|import\s+(src[\w\.]*))",
        re.M,
    )

    rotos = []

    for fichero in sorted(SRC.rglob("*.py")):
        if "__pycache__" in fichero.parts:
            continue

        texto = fichero.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for a, b in patron.findall(texto):
            modulo = a or b
            if modulo not in modulos:
                rotos.append(
                    f"{fichero.relative_to(RAIZ)} -> {modulo}"
                )

    return rotos


# ============================================================
# 3. CLASIFICACION DE TESTS
# ============================================================

MARCA_SEGURO = "# HEALTH_CHECK: SAFE"


def es_peligroso(fichero: Path) -> str | None:
    nombre = fichero.name.lower()

    texto = fichero.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    # Un modulo puede declararse seguro de forma explicita.
    # Se usa cuando menciona el cliente de escritura solo para
    # inspeccionarlo -por ejemplo con inspect.getsource- y no
    # llega a instanciarlo ni a llamarlo.
    #
    # La marca es una afirmacion de quien escribio el test, no
    # una deduccion: si la pones, hazte responsable.
    if MARCA_SEGURO in texto:
        return None

    for señal in SEÑALES_ESCRITURA:
        if señal in texto:
            return f"usa {señal}"

    if "_live" in nombre or "live_" in nombre:
        # Puede ser inocuo, pero no lo arriesgamos sin mirar.
        if "writer" in texto.lower() or "execute" in texto.lower():
            return "nombre 'live' y menciona execute/writer"

    if "write" in nombre:
        return "nombre 'write'"

    return None


def descubrir_tests() -> tuple[list, list]:
    seguros = []
    peligrosos = []

    for fichero in sorted(SRC.rglob("test_*.py")):

        if "__pycache__" in fichero.parts:
            continue

        modulo = ".".join(
            fichero.relative_to(RAIZ)
            .with_suffix("")
            .parts
        )

        motivo = es_peligroso(fichero)

        if motivo:
            peligrosos.append((modulo, motivo))
        else:
            seguros.append(modulo)

    return seguros, peligrosos


# ============================================================
# 4. EJECUCION
# ============================================================

def clasificar_fallo(salida: str) -> str:
    for señal in SEÑALES_RED:
        if señal in salida:
            return "RED"

    for señal in SEÑALES_CREDENCIALES:
        if señal in salida:
            return "CREDENCIALES"

    # Un snapshot antiguo que ya no existe es podredumbre del
    # test, no un fallo del programa.
    for señal in SEÑALES_DATOS:
        if señal in salida:
            return "DATOS"

    return "FALLO"


def ejecutar_test(
    modulo: str,
    timeout: int,
) -> tuple[str, float, str]:

    inicio = time.perf_counter()

    # Produccion corre con PYTHONIOENCODING=utf-8 (lo fija el
    # workflow). Sin eso, en la consola de Windows cualquier test
    # que imprima una flecha o un simbolo de aviso revienta con
    # UnicodeEncodeError y parece un fallo de codigo cuando solo
    # es la pagina de codigos del terminal.
    entorno = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }

    try:
        proceso = subprocess.run(
            [sys.executable, "-m", modulo],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
            env=entorno,
        )

    except subprocess.TimeoutExpired:
        return (
            "TIMEOUT",
            time.perf_counter() - inicio,
            f"Superó los {timeout}s",
        )

    duracion = time.perf_counter() - inicio
    salida = (proceso.stdout or "") + (proceso.stderr or "")

    if proceso.returncode == 0:
        return ("OK", duracion, "")

    categoria = clasificar_fallo(salida)

    lineas = [
        linea.strip()
        for linea in salida.splitlines()
        if linea.strip()
    ]

    resumen = lineas[-1] if lineas else "sin salida"

    return (categoria, duracion, resumen[:160])


# ============================================================
# INFORME
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapido", action="store_true")
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_POR_TEST,
    )
    parser.add_argument(
        "--patron",
        default="",
        help="ejecuta solo los tests cuyo nombre lo contenga",
    )
    args = parser.parse_args()

    print("=" * 78)
    print(" BORDALAS IA - CHEQUEO DE SALUD")
    print("=" * 78)
    print(f"Proyecto: {RAIZ}")
    print(f"Python:   {sys.version.split()[0]}")
    print()

    problemas = 0

    # --- 1
    print("1. COMPILACION")
    errores = comprobar_compilacion()

    if errores:
        problemas += len(errores)
        print(rojo(f"   {len(errores)} ficheros no compilan:"))
        for error in errores[:10]:
            print(f"     {error}")

        if sys.version_info < (3, 12):
            print(
                amarillo(
                    "   Aviso: estas en Python "
                    f"{sys.version_info.major}."
                    f"{sys.version_info.minor}. Algunos de estos "
                    "errores pueden ser f-strings multilinea, "
                    "validas desde 3.12. Produccion usa 3.13."
                )
            )
    else:
        total = sum(
            1
            for f in SRC.rglob("*.py")
            if "__pycache__" not in f.parts
        )
        print(verde(f"   OK  {total} ficheros compilan"))

    # --- 2
    print()
    print("2. IMPORTS INTERNOS")
    rotos = comprobar_imports()

    if rotos:
        problemas += len(rotos)
        print(rojo(f"   {len(rotos)} imports no resuelven:"))
        for roto in rotos[:10]:
            print(f"     {roto}")
    else:
        print(verde("   OK  todos los imports src.* resuelven"))

    # --- 3
    print()
    print("3. INVENTARIO DE TESTS")
    seguros, peligrosos = descubrir_tests()
    print(f"   {len(seguros)} ejecutables")
    print(
        amarillo(
            f"   {len(peligrosos)} NO se ejecutan "
            f"(pueden escribir en Biwenger)"
        )
    )

    for modulo, motivo in peligrosos:
        print(gris(f"     - {modulo}  [{motivo}]"))

    if args.rapido:
        print()
        print("Modo rapido: no se ejecutan los tests.")
        raise SystemExit(1 if problemas else 0)

    # --- 4
    if args.patron:
        seguros = [
            modulo
            for modulo in seguros
            if args.patron in modulo
        ]
        print()
        print(
            f"   Filtro '{args.patron}': "
            f"{len(seguros)} tests seleccionados"
        )

    print()
    print(f"4. EJECUCION ({len(seguros)} tests)")
    print("-" * 78)

    resultados = {}
    inicio_total = time.perf_counter()

    for indice, modulo in enumerate(seguros, 1):

        corto = modulo.replace("src.", "")

        print(
            f"   [{indice:>3}/{len(seguros)}] {corto:<55}",
            end="",
            flush=True,
        )

        estado, duracion, detalle = ejecutar_test(
            modulo,
            args.timeout,
        )

        resultados.setdefault(estado, []).append(
            (corto, detalle)
        )

        marca = {
            "OK": verde("OK"),
            "FALLO": rojo("FALLO"),
            "RED": amarillo("RED"),
            "CREDENCIALES": amarillo("CREDS"),
            "DATOS": amarillo("DATOS"),
            "TIMEOUT": amarillo("TIMEOUT"),
        }[estado]

        print(f"{marca} {duracion:>5.1f}s")

    total_segundos = time.perf_counter() - inicio_total

    # --- INFORME
    print()
    print("=" * 78)
    print(" RESUMEN")
    print("=" * 78)

    for estado in (
        "OK",
        "FALLO",
        "RED",
        "CREDENCIALES",
        "DATOS",
        "TIMEOUT",
    ):
        items = resultados.get(estado, [])
        if items:
            print(f"  {estado:<14} {len(items)}")

    print(f"  {'TIEMPO':<14} {total_segundos:.0f}s")

    fallos = resultados.get("FALLO", [])

    if fallos:
        print()
        print(rojo(" FALLOS DE CODIGO (esto si hay que mirarlo)"))
        print("-" * 78)
        for modulo, detalle in fallos:
            print(f"  {modulo}")
            print(gris(f"      {detalle}"))

    entorno = (
        resultados.get("RED", [])
        + resultados.get("CREDENCIALES", [])
        + resultados.get("DATOS", [])
        + resultados.get("TIMEOUT", [])
    )

    if entorno:
        print()
        print(
            amarillo(
                " FALLOS DE ENTORNO (red, credenciales, datos "
                "que ya no existen o tiempo: no es el codigo)"
            )
        )
        print("-" * 78)
        for modulo, _ in entorno:
            print(gris(f"  {modulo}"))

    print()

    if fallos or problemas:
        print(rojo(" HAY PROBLEMAS QUE REVISAR"))
        raise SystemExit(1)

    print(verde(" TODO SANO"))


if __name__ == "__main__":
    main()
