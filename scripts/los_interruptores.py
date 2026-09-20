"""
Los interruptores, y que guardia depende de cual.

LO QUE PASO, Y POR QUE EXISTE ESTO (20/09/2026)

    Se encendio `BORDALAS_OBJETIVOS_EL_CATALOGO` en el `env` del
    workflow. `test_la_lista_de_objetivos_v1` empezaba
    comprobando que ese interruptor NO estuviese puesto, se puso
    roja, el paso de validacion devolvio 1 y NO HUBO CICLO. Dos
    vueltas perdidas.

    Doctrina 104: un interruptor encendido es estado de
    produccion. La guardia que mide el apagado tiene que
    apagarlo ella.

    Si una lo hacia mal, las demas pueden hacerlo igual — y cada
    interruptor que se encienda puede volver a matar el ciclo.

LOS TRES CUADROS

    1. EL INVENTARIO. Todos los `BORDALAS_*` que existen, donde
       se declaran y quien los lee. Y si el lector los lee al
       LLAMARSE o al IMPORTARSE: eso decide si apagarlos dentro
       de una prueba sirve de algo.

    2. LAS GUARDIAS. Para cada guardia de la verja que nombre
       algun interruptor: cual, y si lo pone o lo quita ella
       misma.

    3. LA MEDICION, que es la que manda. Cada una de esas
       guardias se corre EN UN SUBPROCESO con su interruptor
       puesto a "1", y se compara con como sale limpia. Lo que
       diga esta columna gana sobre lo que diga el codigo.

    Con `--todos` se corre ademas la verja entera dos veces
    -todos apagados y todos encendidos- y se comparan los dos
    veredictos. Eso tarda lo que tarde la verja por dos.

NI RED, NI ESCRITURAS

    Lee ficheros del propio repositorio y ejecuta guardias, que
    por definicion no escriben en los libros. No toca `data/`,
    no sale a la red y no enciende nada de forma permanente: el
    entorno de cada subproceso es una copia.

COMO SE USA

    python -m scripts.los_interruptores
    python -m scripts.los_interruptores --todos
"""

from __future__ import annotations

import argparse
import ast
import functools
import os
import re
import subprocess
import sys
import time

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


NOMBRE = re.compile(r"BORDALAS_[A-Z0-9_]+")


# LEER Y PARSEAR, UNA VEZ POR FICHERO
#
#     Cada fichero se miraba hasta tres veces —literales,
#     lectores y `tocados`— y esto lo usa tambien una guardia de
#     la verja, que corre en cada ciclo. Medido: de 5,8 s a
#     2,6 s sobre 176 ficheros.


@functools.lru_cache(maxsize=None)
def _texto(camino: Path) -> str:
    try:
        return camino.read_text(encoding="utf-8")
    except OSError:
        return ""


@functools.lru_cache(maxsize=None)
def _arbol(camino: Path):
    try:
        return ast.parse(_texto(camino), str(camino))
    except (SyntaxError, ValueError):
        return None


CARPETAS = ("src", "scripts")


def ficheros() -> list[Path]:

    salida = []

    for carpeta in CARPETAS:
        salida.extend(sorted((RAIZ / carpeta).rglob("*.py")))

    # ESTE FICHERO NO SE MIRA A SI MISMO. Sus ejemplos de
    # docstring llevan nombres con la forma de un interruptor y
    # se colaban en el inventario como si existieran.
    yo = Path(__file__).resolve()

    return [
        f
        for f in salida
        if "__pycache__" not in f.parts
        and ".venv" not in f.parts
        and f.resolve() != yo
    ]


def es_guardia(camino: Path) -> bool:
    return camino.name.startswith("test_")


# ----------------------------------------------------------------
# 1. EL INVENTARIO
# ----------------------------------------------------------------


def literales(camino: Path) -> set[str]:
    """
    Los `BORDALAS_*` que aparecen como cadena EN EL CODIGO.

    Por AST y saltandose los docstrings. Buscando el texto a
    secas se colaban nombres de ejemplo —`BORDALAS_LO_QUE_SEA`
    del protocolo de encendido— y salian en el inventario como
    interruptores que existen. Un interruptor de verdad siempre
    esta en codigo: asignado a una constante o pasado a
    `os.environ`.
    """

    arbol = _arbol(camino)

    if arbol is None:
        return set(NOMBRE.findall(_texto(camino)))

    docs = set()

    for nodo in ast.walk(arbol):

        if not isinstance(
            nodo,
            (
                ast.Module,
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        cuerpo = getattr(nodo, "body", None) or []

        if not cuerpo:
            continue

        primero = cuerpo[0]

        if (
            isinstance(primero, ast.Expr)
            and isinstance(primero.value, ast.Constant)
            and isinstance(primero.value.value, str)
        ):
            docs.add(id(primero.value))

    salida = set()

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Constant):
            continue

        if not isinstance(nodo.value, str):
            continue

        if id(nodo) in docs:
            continue

        salida.update(NOMBRE.findall(nodo.value))

    return salida


def _constantes(camino: Path) -> dict[str, str]:
    """`{nombre de la constante: BORDALAS_*}` de ese modulo."""

    arbol = _arbol(camino)

    if arbol is None:
        return {}

    salida = {}

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Assign):
            continue

        if not isinstance(nodo.value, ast.Constant):
            continue

        if not isinstance(nodo.value.value, str):
            continue

        if not NOMBRE.fullmatch(nodo.value.value):
            continue

        for destino in nodo.targets:
            if isinstance(destino, ast.Name):
                salida[destino.id] = nodo.value.value

    return salida


def tocados(camino: Path) -> set[str]:
    """
    Los interruptores que este fichero toca, POR SU NOMBRE O POR
    SU ALIAS.

    Sin esto, la tabla se dejaba fuera justo a las guardias que
    importan que importan — las que escriben
    `from ... import ENV_EL_CATALOGO` y nunca el literal. La que
    tumbo el ciclo el 20/09 era una de esas.
    """

    nombres = literales(camino)

    arbol = _arbol(camino)

    if arbol is None:
        return nombres

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.ImportFrom) or not nodo.module:
            continue

        origen = RAIZ / (nodo.module.replace(".", "/") + ".py")

        if not origen.exists():
            continue

        constantes = _constantes(origen)

        for alias in nodo.names:
            if alias.name in constantes:
                nombres.add(constantes[alias.name])

    return nombres


def lectores(camino: Path) -> dict[str, str]:
    """
    Para cada `BORDALAS_*` de este fichero, cuando se lee.

    `AL_LLAMARSE` si el `os.environ` esta dentro de una funcion.
    `AL_IMPORTARSE` si esta en el cuerpo del modulo — y entonces
    apagarlo dentro de una prueba NO sirve.

    Se resuelven los alias: `ENV_X = "BORDALAS_X"` y luego
    `os.environ.get(ENV_X)`.
    """

    arbol = _arbol(camino)

    if arbol is None:
        return {}

    # alias -> nombre del interruptor
    alias: dict[str, str] = {}

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Assign):
            continue

        if not isinstance(nodo.value, ast.Constant):
            continue

        if not isinstance(nodo.value.value, str):
            continue

        if not NOMBRE.fullmatch(nodo.value.value):
            continue

        for destino in nodo.targets:
            if isinstance(destino, ast.Name):
                alias[destino.id] = nodo.value.value

    # las lineas que estan dentro de una funcion
    dentro = set()

    for nodo in ast.walk(arbol):

        if isinstance(
            nodo, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            for hijo in ast.walk(nodo):
                if hasattr(hijo, "lineno"):
                    dentro.add(hijo.lineno)

    salida: dict[str, str] = {}

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Call):
            continue

        objetivo = None

        for arg in nodo.args:

            if isinstance(arg, ast.Constant) and isinstance(
                arg.value, str
            ):
                if NOMBRE.fullmatch(arg.value):
                    objetivo = arg.value

            elif isinstance(arg, ast.Name):
                objetivo = alias.get(arg.id) or objetivo

        if objetivo is None:
            continue

        fuente = ast.unparse(nodo.func)

        if "environ" not in fuente and "getenv" not in fuente:
            continue

        cuando = (
            "AL_LLAMARSE"
            if nodo.lineno in dentro
            else "AL_IMPORTARSE"
        )

        # Si aparece de las dos formas, manda la peor.
        if salida.get(objetivo) != "AL_IMPORTARSE":
            salida[objetivo] = cuando

    return salida


@functools.lru_cache(maxsize=1)
def inventario() -> dict[str, dict]:

    salida: dict[str, dict] = {}

    for camino in ficheros():

        relativo = camino.relative_to(RAIZ).as_posix()

        for nombre in literales(camino):

            fila = salida.setdefault(
                nombre,
                {"nombre": nombre, "lee": [], "nombra": []},
            )

            fila["nombra"].append(relativo)

        for nombre, cuando in lectores(camino).items():

            fila = salida.setdefault(
                nombre,
                {"nombre": nombre, "lee": [], "nombra": []},
            )

            fila["lee"].append((relativo, cuando))

    return salida


def cuadro_del_inventario(datos: dict) -> None:

    print("=" * 78)
    print("1. TODOS LOS INTERRUPTORES QUE EXISTEN")
    print("=" * 78)
    print()
    print(
        f"  {'interruptor':36s} {'lo lee':40s} {'cuando':14s}"
    )
    print("  " + "-" * 92)

    for nombre in sorted(datos):

        fila = datos[nombre]

        lecturas = [
            (f, c)
            for f, c in fila["lee"]
            if not es_guardia(Path(f))
        ]

        if not lecturas:
            print(
                f"  {nombre:36s} {'(nadie: solo se nombra)':40s} "
                f"{'-':14s}"
            )
            continue

        for fichero, cuando in sorted(lecturas):
            print(f"  {nombre:36s} {fichero:40s} {cuando:14s}")

    print()
    print(f"  SON {len(datos)} interruptores.")

    tardios = [
        (n, f)
        for n, d in datos.items()
        for f, c in d["lee"]
        if c == "AL_IMPORTARSE" and not es_guardia(Path(f))
    ]

    if tardios:
        print()
        print(
            "  LEIDOS AL IMPORTARSE -apagarlos dentro de una "
            "prueba NO sirve-:"
        )
        for nombre, fichero in sorted(tardios):
            print(f"    {nombre}  en  {fichero}")
    else:
        print(
            "  NINGUNO se lee al importarse: todos siguen al "
            "entorno despues del import."
        )


# ----------------------------------------------------------------
# 2. LAS GUARDIAS
# ----------------------------------------------------------------


def se_lo_pone_ella(camino: Path, nombre: str) -> bool:
    """
    ¿Esta guardia escribe o borra ese interruptor ella misma?

    Vale tanto con el nombre literal como con su alias.
    """

    texto = _texto(camino)

    claves = {nombre}

    for linea in texto.splitlines():

        marca = re.match(
            r"\s*(?:from .*import \(|\s*)([A-Z_]+),?\s*$", linea
        )

        if marca and marca.group(1).startswith("ENV_"):
            claves.add(marca.group(1))

    for alias in re.findall(
        r"([A-Z_]+)\s*=\s*[\"']" + nombre + r"[\"']", texto
    ):
        claves.add(alias)

    # Los alias importados de otro modulo: cualquier nombre que
    # empiece por ENV_ o acabe en _ENV y se use con environ.
    for alias in re.findall(r"\b([A-Z][A-Z0-9_]*(?:_ENV|ENV_[A-Z0-9_]*))\b", texto):
        claves.add(alias)

    for clave in claves:

        escrito = re.search(
            r"os\.environ\[\s*(?:\"|')?" + re.escape(clave)
            + r"(?:\"|')?\s*\]\s*=", texto
        )

        borrado = re.search(
            r"os\.environ\.pop\(\s*(?:\"|')?" + re.escape(clave)
            + r"(?:\"|')?", texto
        )

        if escrito or borrado:
            return True

    return False


def lee_el_entorno(camino: Path) -> bool:
    """
    ¿Este fichero toca `os.environ` o `os.getenv` DE VERDAD?

    Por AST, no buscando el texto: media docena de guardias lo
    nombran en un comentario para explicar que NO lo usan, y
    contarlas seria justo el error que esto persigue.

    Es lo que separa «nombra un interruptor» de «puede depender
    de el»: una guardia que nunca mira el entorno no puede
    heredarlo, por mucho que escriba su nombre.
    """

    arbol = _arbol(camino)

    if arbol is None:
        return False

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Attribute):

            if nodo.attr in {"environ", "getenv"}:
                return True

        if isinstance(nodo, ast.Name) and nodo.id in {
            "environ",
            "getenv",
        }:
            return True

    return False


def guardias_de_la_verja() -> list[str]:

    from scripts.run_validation_gate import TESTS

    return list(TESTS)


def camino_de(modulo: str) -> Path:
    return RAIZ / (modulo.replace(".", "/") + ".py")


def corre(modulo: str, entorno: dict) -> bool:
    """Corre una guardia en su propio proceso. True si pasa."""

    # `text=True` a secas decodifica con el idioma de la
    # consola, y en Windows eso revienta con cualquier acento
    # que la guardia imprima. Se fija utf-8 y se tolera lo que
    # no encaje: aqui lo que decide es el codigo de salida.
    proceso = subprocess.run(
        [sys.executable, "-m", modulo],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=entorno,
        cwd=str(RAIZ),
    )

    return proceso.returncode == 0


def cuadro_de_las_guardias(datos: dict) -> list:

    print()
    print("=" * 78)
    print("2. LAS GUARDIAS QUE NOMBRAN ALGUN INTERRUPTOR")
    print("=" * 78)

    interesantes = []

    for modulo in guardias_de_la_verja():

        camino = camino_de(modulo)

        if not camino.exists():
            continue

        for nombre in sorted(tocados(camino)):

            if nombre not in datos:
                continue

            interesantes.append(
                {
                    "modulo": modulo,
                    "camino": camino,
                    "interruptor": nombre,
                    "se_lo_pone": se_lo_pone_ella(camino, nombre),
                }
            )

    print()
    print(
        f"  {'guardia':46s} {'interruptor':34s} "
        f"{'lo pone ella':13s} {'se cae si esta ON':18s}"
    )
    print("  " + "-" * 113)

    base = dict(os.environ)

    for nombre in NOMBRE.findall(" ".join(datos)):
        base.pop(nombre, None)

    for fila in interesantes:

        limpio = corre(fila["modulo"], base)

        entorno = dict(base)
        entorno[fila["interruptor"]] = "1"

        puesto = corre(fila["modulo"], entorno)

        if not limpio:
            veredicto = "YA ESTABA ROJA"
        elif puesto:
            veredicto = "NO"
        else:
            veredicto = "SI  <== SE CAE"

        fila["se_cae"] = veredicto

        print(
            f"  {fila['modulo'].split('.')[-1]:46s} "
            f"{fila['interruptor']:34s} "
            f"{('SI' if fila['se_lo_pone'] else 'NO'):13s} "
            f"{veredicto:18s}"
        )

    caidas = [f for f in interesantes if f["se_cae"].startswith("SI")]

    print()

    if caidas:
        print(f"  SE CAEN {len(caidas)}:")
        for fila in caidas:
            print(
                f"    {fila['modulo']}  con  {fila['interruptor']}"
            )
    else:
        print(
            "  NINGUNA se cae con su interruptor puesto."
        )

    return interesantes


# ----------------------------------------------------------------
# 3. LA VERJA ENTERA, DOS VECES
# ----------------------------------------------------------------


def verja(entorno: dict) -> tuple[int, str, float]:
    """La verja entera. Devuelve (codigo, ultima linea, segundos)."""

    arranque = time.perf_counter()

    proceso = subprocess.run(
        [sys.executable, "scripts/run_validation_gate.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=entorno,
        cwd=str(RAIZ),
    )

    segundos = time.perf_counter() - arranque

    lineas = [
        linea
        for linea in (proceso.stdout or "").splitlines()
        if "FALLAN" in linea or "TODAS EN VERDE" in linea
    ]

    rojas = [
        linea.strip(" -")
        for linea in (proceso.stdout or "").splitlines()
        if linea.strip().startswith("- src.")
    ]

    veredicto = (lineas[-1] if lineas else "sin veredicto")

    if rojas:
        veredicto += "  ->  " + ", ".join(sorted(rojas))

    return proceso.returncode, veredicto, segundos


def cuadro_de_la_verja(datos: dict) -> None:

    print()
    print("=" * 78)
    print("3. LA VERJA ENTERA, CON TODO APAGADO Y CON TODO PUESTO")
    print("=" * 78)
    print()

    limpio = dict(os.environ)

    for nombre in datos:
        limpio.pop(nombre, None)

    todos = dict(limpio)

    for nombre in datos:
        todos[nombre] = "1"

    for etiqueta, entorno in (
        ("TODOS APAGADOS (borrados)", limpio),
        (f"LOS {len(datos)} PUESTOS A \"1\"", todos),
    ):

        codigo, veredicto, segundos = verja(entorno)

        print(f"  {etiqueta}")
        print(
            f"    exit {codigo}  ·  {segundos:6.1f} s  ·  {veredicto}"
        )
        print()


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--todos",
        action="store_true",
        help="corre ademas la verja entera dos veces",
    )

    args = parser.parse_args()

    datos = inventario()

    cuadro_del_inventario(datos)
    cuadro_de_las_guardias(datos)

    if args.todos:
        cuadro_de_la_verja(datos)
    else:
        print()
        print(
            "  (con `--todos` se corre ademas la verja entera "
            "dos veces: apagada y con los "
            f"{len(datos)} puestos)"
        )


if __name__ == "__main__":
    main()
