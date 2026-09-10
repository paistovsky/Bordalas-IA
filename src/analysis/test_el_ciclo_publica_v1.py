"""
El estado del dashboard se construye ENTERO, con la foto real.

SINTOMA

    10/09/2026, en produccion:

        dashboard_state.py:4609
        NameError: name 'lineup_payload' is not defined
        Process completed with exit code 1

CAUSA

    Al sacar `compact_lineup` a una variable -para que `lineup` y
    `posibles_cambios` contaran lo mismo- la definicion se colo
    en OTRA funcion, `compact_ledger_audit`, que ni siquiera
    recibe `state`. `build_dashboard_state` se quedo usando un
    nombre que nadie ataba.

    Python no lo ve al importar: un nombre libre solo revienta
    cuando se ejecuta esa linea.

CONSECUENCIA

    Habia 107 guardias en verde y NINGUNA ejecutaba
    `build_dashboard_state()` de punta a punta. Es el mismo
    agujero por el que se publicaron cuatro bloques que no
    llegaban a ninguna pantalla: se comprobaba la forma de las
    piezas y nunca el montaje.

    Aqui van las dos mitades:

        1. Se CONSTRUYE el estado con lo que hay en disco. Si
           revienta, esta guardia se pone roja antes que el
           ciclo.

        2. Y una lectura estatica que caza la familia entera del
           fallo -un nombre usado en una funcion que esa funcion
           no ata en ningun sitio- sin ejecutar nada.

    La segunda existe porque la primera necesita una foto en
    disco, y en un clon recien hecho no la hay. Que no se pueda
    ejecutar el montaje no puede dejar el fichero sin vigilar.
"""

from __future__ import annotations

import ast
import builtins
import io
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]

TELEMETRIA = RAIZ / "src" / "telemetry" / "dashboard_state.py"

# Los ficheros que arma el ciclo y que nadie ejecutaba entero.
VIGILADOS = [
    TELEMETRIA,
    RAIZ / "src" / "analysis" / "lineup_engine.py",
]

CORTES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
)


# ============================================================
# LA LECTURA ESTATICA
# ============================================================


def _hijos(nodo):
    """Hijos sin cruzar a otra funcion o clase."""

    for hijo in ast.iter_child_nodes(nodo):
        if isinstance(hijo, CORTES):
            continue
        yield hijo


def _caminar(nodo):
    yield nodo

    for hijo in _hijos(nodo):
        yield from _caminar(hijo)


def _atados(cuerpo) -> set:
    """Todo nombre que quede atado en ESTE ambito."""

    fuera = set()

    for raiz in cuerpo:

        if isinstance(raiz, CORTES):
            if hasattr(raiz, "name"):
                fuera.add(raiz.name)
            continue

        for nodo in _caminar(raiz):

            if isinstance(nodo, ast.Name) and isinstance(
                nodo.ctx, (ast.Store, ast.Del)
            ):
                fuera.add(nodo.id)

            elif isinstance(nodo, (ast.Import, ast.ImportFrom)):
                for alias in nodo.names:
                    fuera.add(
                        (alias.asname or alias.name).split(".")[0]
                    )

            elif isinstance(nodo, ast.ExceptHandler) and nodo.name:
                fuera.add(nodo.name)

            elif isinstance(nodo, (ast.Global, ast.Nonlocal)):
                fuera |= set(nodo.names)

            elif isinstance(nodo, CORTES) and hasattr(nodo, "name"):
                fuera.add(nodo.name)

    return fuera


def _de_la_firma(funcion) -> set:
    args = funcion.args

    nombres = {
        a.arg
        for a in (
            args.args + args.kwonlyargs + args.posonlyargs
        )
    }

    if args.vararg:
        nombres.add(args.vararg.arg)

    if args.kwarg:
        nombres.add(args.kwarg.arg)

    return nombres


def _lo_que_ata_dentro(funcion) -> set:
    """Lo que la funcion ata, contando comprehensiones y anidadas."""

    atados = _atados(funcion.body) | _de_la_firma(funcion)

    for nodo in ast.walk(funcion):

        if isinstance(nodo, ast.comprehension):
            for x in ast.walk(nodo.target):
                if isinstance(x, ast.Name):
                    atados.add(x.id)

        if isinstance(nodo, ast.ExceptHandler) and nodo.name:
            atados.add(nodo.name)

        if isinstance(nodo, (ast.Global, ast.Nonlocal)):
            atados |= set(nodo.names)

        if isinstance(nodo, CORTES):
            if hasattr(nodo, "name"):
                atados.add(nodo.name)

    return atados


def nombres_sin_dueno(ruta: Path) -> list:
    """
    Nombres usados en una funcion que esa funcion no ata, y que
    tampoco son globales ni vienen de una funcion que la envuelve.

    Es exactamente la forma del fallo del 10/09: la asignacion
    vivia en otra funcion.
    """

    arbol = ast.parse(io.open(ruta, encoding="utf-8").read())

    globales = _atados(arbol.body) | set(dir(builtins))

    for nodo in ast.walk(arbol):
        if isinstance(
            nodo,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            globales.add(nodo.name)

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            for alias in nodo.names:
                globales.add(
                    (alias.asname or alias.name).split(".")[0]
                )

    hallazgos = []

    def revisa(funcion, heredado: set) -> None:
        """
        `heredado` son los nombres de las funciones que envuelven
        a esta. Sin eso, cualquier cierre que lea una variable de
        fuera saldria como fallo, y hay siete legitimos.
        """

        mios = _lo_que_ata_dentro(funcion)

        visibles = mios | heredado | globales

        for nodo in _caminar(funcion):

            if not (
                isinstance(nodo, ast.Name)
                and isinstance(nodo.ctx, ast.Load)
            ):
                continue

            if nodo.id in visibles:
                continue

            hallazgos.append(
                (funcion.name, nodo.id, nodo.lineno)
            )

        for hijo in ast.walk(funcion):
            if hijo is funcion:
                continue

            if isinstance(
                hijo, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                revisa(hijo, visibles)

    for nodo in arbol.body:
        if isinstance(
            nodo, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            revisa(nodo, set())

    return sorted(set(hallazgos), key=lambda x: x[2])


CEBO = (
    "def otra(audit):\n"
    "    if not audit:\n"
    "        return {}\n"
    "    lineup_payload = compact(1)\n"
    "    return lineup_payload\n"
    "\n"
    "\n"
    "def build():\n"
    "    return {'lineup': lineup_payload}\n"
    "\n"
    "\n"
    "def sana():\n"
    "    try:\n"
    "        x = calcula()\n"
    "    except Exception:\n"
    "        x = None\n"
    "    return x\n"
    "\n"
    "\n"
    "def cierre_legitimo():\n"
    "    fuera = 1\n"
    "\n"
    "    def dentro():\n"
    "        return fuera\n"
    "\n"
    "    return dentro()\n"
    "\n"
    "\n"
    "def compact(a):\n"
    "    return a\n"
    "\n"
    "\n"
    "def calcula():\n"
    "    return 1\n"
)


def test_el_detector_caza_el_fallo_de_esta_noche() -> None:
    """
    Un detector que dice "cero" puede estar simplemente roto. Se
    le pone delante el fallo exacto del 10/09 y tiene que verlo.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        cebo = Path(carpeta) / "cebo.py"
        cebo.write_text(CEBO, encoding="utf-8")

        visto = nombres_sin_dueno(cebo)

    nombres = {n for _, n, _ in visto}

    assert "lineup_payload" in nombres, (
        f"el detector NO ve el fallo del 10/09: {visto}"
    )

    # Y no puede cantar lo que esta bien: ni el try/except que
    # asigna en las dos ramas, ni el cierre que lee de fuera.
    assert "x" not in nombres, visto
    assert "fuera" not in nombres, visto


def test_ningun_nombre_se_usa_donde_nadie_lo_ata() -> None:
    """
    EL FALLO DEL 10/09, EN PRODUCCION.

    `lineup_payload` se definia en `compact_ledger_audit` y se
    usaba en `build_dashboard_state`. El import no se queja; el
    ciclo si, a las 04:45.
    """

    fallos = []

    for ruta in VIGILADOS:

        for funcion, nombre, linea in nombres_sin_dueno(ruta):
            fallos.append(
                f"{ruta.name}:{linea} {funcion}(): `{nombre}`"
            )

    assert not fallos, (
        "hay nombres usados donde nadie los ata; si esa linea se "
        "ejecuta, el ciclo muere con NameError:\n  "
        + "\n  ".join(fallos)
    )

    # Regla 24: la guardia no pasa con las manos vacias.
    assert len(VIGILADOS) >= 2, VIGILADOS


# ============================================================
# EL MONTAJE ENTERO, CON LA FOTO REAL
# ============================================================


def _hay_foto() -> bool:
    return bool(list((RAIZ / "data").glob("snapshot_*.json")))


def test_el_estado_del_dashboard_se_construye_entero() -> None:
    """
    LA GUARDIA QUE FALTABA.

    107 en verde y ninguna montaba el estado. Se comprobaba la
    forma de cada pieza -que el bloque existe, que el panel lo
    lee- y nunca que el montaje corriera.

    Esto construye el estado con la foto que hay en disco y falla
    si revienta. No comprueba NINGUN valor: solo que el ciclo
    llega al final. Los valores ya tienen sus guardias.
    """

    if not _hay_foto():
        # No se calla: se dice. Un salto silencioso aqui seria el
        # mismo agujero con otra forma (doctrina 36).
        print(
            "     AVISO: sin `data/snapshot_*.json` no se puede "
            "montar el estado. La lectura estatica sigue "
            "vigilando el fichero."
        )
        return

    from src.telemetry.dashboard_state import (
        build_dashboard_state,
    )

    estado = build_dashboard_state()

    assert isinstance(estado, dict), type(estado)

    # Si el montaje se corta a medias, el diccionario sale corto.
    # Con la foto del 10/09 son 53 bloques; el suelo va bajo a
    # proposito, porque lo que se vigila es que TERMINE.
    assert len(estado) >= 30, (
        f"el estado sale con {len(estado)} bloques: el montaje "
        f"se ha quedado a medias"
    )

    for bloque in ("meta", "summary", "lineup"):
        assert bloque in estado, (
            f"falta el bloque `{bloque}` en el estado montado"
        )

    # Y el bloque que nacio el 10/09, cuyo primer ciclo es el que
    # reviento: que se vea que llega, no que deberia llegar.
    assert "posibles_cambios" in estado, (
        "`posibles_cambios` no llega al estado montado"
    )

    bloque = estado["posibles_cambios"]

    assert "available" in bloque and "bench" in bloque, bloque


TESTS = [
    test_el_detector_caza_el_fallo_de_esta_noche,
    test_ningun_nombre_se_usa_donde_nadie_lo_ata,
    test_el_estado_del_dashboard_se_construye_entero,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL CICLO PUBLICA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
