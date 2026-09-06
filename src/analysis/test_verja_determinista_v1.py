"""
La verja tiene una sola promesa: verde aqui es verde alli.

SINTOMA (17/09/2026)

    Ochenta y dos en verde en el disco del dueño. Rojas en GitHub
    Actions `test_retrotest_rampa_v1` y `test_fuera_de_muestra_v1`.
    Ciclo de produccion parado desde las 11:00.

CAUSA

    Las dos leian `data/autopilot/price_history.json`, el almacen
    de precios REAL.

    Ese directorio esta entero en `.gitignore`. No hay ahi ni un
    fixture: es estado que cada maquina tiene distinto. En el
    disco del dueño el almacen tenia seis dias. En Actions, la
    cache se restaura ANTES de correr la verja y trae los dias
    que lleve produccion acumulados.

    Reproducido con el mismo codigo y tres almacenes distintos:

        6 dias   ->  las veinte en verde
        25 dias  ->  cuatro en rojo
        3 dias   ->  una revienta con TypeError

    Los rojos decian cosas como "el horizonte de 7 dias tiene
    3034 operaciones" o "el tramo 2-4 % rinde 1,96 %". Ninguno
    era un fallo del codigo: eran afirmaciones sobre el MERCADO,
    y el mercado de la cache no es el del disco.

CONSECUENCIA

    Una verja que se pregunta por el mercado no comprueba el
    codigo: mide el dia. Y cuando el mercado cambia, tumba
    produccion sin que nadie haya tocado una linea.

LO QUE VIGILA ESTE FICHERO

    Que ninguna comprobacion de la puerta de validacion vuelva a
    leer del estado.

    En dos capas, porque una sola no bastaba:

        REGLA A (se lee el codigo)
            Ningun modulo de la verja puede nombrar una ruta bajo
            el directorio de estado, ni construirla troceada.

        REGLA B (se ejecuta)
            Un modulo puede leer el estado sin nombrarlo, llamando
            a una funcion que lo lee por su cuenta. Contra eso no
            hay lectura de codigo que valga.

            Asi que se monta un ESPEJO del repositorio -enlaces a
            `src`, `scripts` y demas- con el directorio de estado
            VACIO, y los modulos vigilados se ejecutan ahi. Mismo
            codigo, sin estado. Si el veredicto cambia, lo decidia
            el estado.

            Con esto se encontro un tercero que nadie habia
            mirado: `test_arbitro_v1` se caia sin almacen porque
            `store_depth()` devolvia un objeto SIN
            `retention_days`. No nombra el estado en ninguna
            linea, asi que la Regla A jamas lo habria visto.

LA DEUDA SE DECLARA, NO SE ESCONDE

    `DEUDA` es la lista de modulos a los que hoy se les tolera
    tocar el estado. Cada uno con su motivo y su fecha. Un modulo
    nuevo no puede entrar sin que alguien lo escriba aqui, que es
    justo lo que no paso el 14/09.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile

from pathlib import Path


PUERTA = Path("scripts") / "run_validation_gate.py"


# El nombre del directorio de estado, partido para que este mismo
# fichero no se denuncie a si mismo al buscarse.
ESTADO = "dat" + "a"


# Directorios del repositorio que un modulo de la verja si puede
# leer: son codigo versionado, iguales en las dos maquinas.
DEL_REPOSITORIO = (
    "src",
    "scripts",
    "dashboard-v8",
    "diagnostico",
    ".github",
)


# ============================================================
# LA DEUDA CONOCIDA
# ============================================================
#
# Modulos que hoy tocan el estado y que no se arreglan esta
# noche. La REGLA B los ejecuta sin estado y exige que pasen
# igual: mientras eso se cumpla, la promesa de la verja aguanta.
#
# Esta lista solo deberia encoger.
DEUDA = {
    "src.analysis.test_futbolfantasy_source_v12": (
        "17/09/2026: contrasta el parser contra HTML real de "
        "ff_html y contra snapshots, ninguno de los dos en git. "
        "En Actions no existen, asi que esa parte no se ejecuta "
        "nunca: se salta sola cuando faltan -por eso lleva un mes "
        "en verde- pero sigue siendo estado mutable decidiendo "
        "que se comprueba. Sacar esos ficheros a un directorio de "
        "fixtures versionado es un trabajo aparte, y esta noche "
        "produccion esta caida."
    ),
}


# Los que se ejecutan bajo la Regla B: la deuda declarada, mas
# los tres que se arreglaron la noche de la caida. Estos tres se
# vigilan aunque ya esten limpios, para que el arreglo no se
# deshaga sin que nadie se entere.
REPARADAS = (
    "src.analysis.test_retrotest_rampa_v1",
    "src.analysis.test_fuera_de_muestra_v1",
    "src.analysis.test_arbitro_v1",
)


def modulos_de_la_verja() -> list[str]:
    """La lista de la puerta, leida de la puerta."""

    fuente = PUERTA.read_text(encoding="utf-8")

    return re.findall(
        r'"(src\.[a-z0-9_.]*test_[a-z0-9_]+)"',
        fuente,
    )


def _ruta(modulo: str) -> Path:
    return Path(modulo.replace(".", "/") + ".py")


def _docstrings(arbol: ast.AST) -> set:
    """
    Los docstrings quedan fuera del escaneo.

    Un docstring que EXPLICA el fallo -y estos lo explican- no lo
    comete. Si contaran, la unica forma de pasar la guardia seria
    dejar de contar la historia, que es exactamente al reves de
    como trabaja esta casa.
    """

    fuera = set()

    for nodo in ast.walk(arbol):

        if not isinstance(
            nodo,
            (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            continue

        cuerpo = getattr(nodo, "body", None) or []

        if (
            cuerpo
            and isinstance(cuerpo[0], ast.Expr)
            and isinstance(cuerpo[0].value, ast.Constant)
            and isinstance(cuerpo[0].value.value, str)
        ):
            fuera.add(id(cuerpo[0].value))

    return fuera


def lecturas_de_estado(modulo: str) -> list[str]:
    """
    Que hace este modulo para tocar el estado, si es que lo hace.

    Busca las dos formas en que se ha escrito en este repositorio:
    la ruta entera en un literal, y la ruta troceada empezando por
    `Path(...)` con el nombre del directorio suelto.
    """

    ruta = _ruta(modulo)

    if not ruta.exists():
        return []

    arbol = ast.parse(
        ruta.read_text(encoding="utf-8", errors="replace")
    )

    fuera = _docstrings(arbol)

    barras = (ESTADO + "/", ESTADO + chr(92))

    hallazgos = []

    for nodo in ast.walk(arbol):

        if (
            isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, str)
            and id(nodo) not in fuera
            and any(b in nodo.value for b in barras)
        ):
            hallazgos.append(
                f"linea {getattr(nodo, 'lineno', '?')}: "
                f"ruta {nodo.value[:48]!r}"
            )

        # La forma troceada no lleva barra: se detecta por la
        # llamada, no por el texto.
        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id == "Path"
            and nodo.args
            and isinstance(nodo.args[0], ast.Constant)
            and nodo.args[0].value == ESTADO
        ):
            hallazgos.append(
                f"linea {getattr(nodo, 'lineno', '?')}: "
                f"Path({ESTADO!r})"
            )

    return sorted(set(hallazgos))


# ============================================================
# REGLA A: NADIE NOMBRA EL ESTADO
# ============================================================


def test_ninguna_guardia_de_la_verja_lee_el_estado() -> None:
    """
    LA REGLA, Y LO QUE COSTO NO TENERLA

        Dos guardias leyendo el almacen de precios tuvieron
        produccion parada. Ninguna de las dos era un fallo de
        codigo: eran dos preguntas sobre el mercado metidas en
        una verja.
    """

    culpables = {}

    for modulo in modulos_de_la_verja():

        if modulo in DEUDA:
            continue

        hallazgos = lecturas_de_estado(modulo)

        if hallazgos:
            culpables[modulo] = hallazgos

    assert not culpables, (
        "estas comprobaciones de la verja leen estado mutable, "
        "que no es el mismo en el disco del dueño que en la cache "
        "de Actions:\n"
        + "\n".join(
            f"  {modulo}\n"
            + "\n".join(f"      {h}" for h in hallazgos)
            for modulo, hallazgos in sorted(culpables.items())
        )
        + "\n\nUsa un fixture: mira "
        "src/analysis/price_store_fixture.py. Si de verdad hace "
        "falta el estado real, la comprobacion tiene que informar "
        "'sin muestra' y PASAR, nunca fallar, y declararse en "
        "DEUDA con su motivo."
    )


def test_las_dos_que_tiraron_produccion_ya_no_lo_leen() -> None:
    """
    Por su nombre, para que el arreglo no se deshaga sin ruido.
    """

    for modulo in (
        "src.analysis.test_retrotest_rampa_v1",
        "src.analysis.test_fuera_de_muestra_v1",
    ):
        assert modulo not in DEUDA, (
            f"{modulo} se ha metido en la lista de deuda: es "
            f"justo la que tiro produccion el 17/09"
        )

        hallazgos = lecturas_de_estado(modulo)

        assert not hallazgos, (
            f"{modulo} ha vuelto a leer el almacen real: "
            f"{hallazgos}"
        )


def test_la_deuda_esta_explicada() -> None:
    """
    Una excepcion sin motivo escrito es una excepcion que nadie
    revisa. Y las que de verdad ya no tocan nada sobran de la
    lista: si se quedan, tapan la regla sin hacer falta.
    """

    for modulo, motivo in DEUDA.items():

        assert len(motivo) > 60, (
            f"{modulo} esta exento sin explicar por que"
        )

        assert lecturas_de_estado(modulo), (
            f"{modulo} esta en la lista de deuda y ya no toca el "
            f"estado: quitalo de DEUDA para que la regla vuelva a "
            f"cubrirlo"
        )


# ============================================================
# REGLA B: Y SIN EL ESTADO, PASAN IGUAL
# ============================================================


def _enlazar(destino: Path, origen: Path) -> bool:
    """Un enlace a un directorio, en Linux o en Windows."""

    try:
        os.symlink(origen, destino, target_is_directory=True)
        return True

    except (OSError, NotImplementedError, AttributeError):
        pass

    if os.name != "nt":
        return False

    # En Windows un symlink pide privilegios; una junction no.
    hecho = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(destino), str(origen)],
        capture_output=True,
        text=True,
    )

    return hecho.returncode == 0


def _espejo_sin_estado(raiz: Path, destino: Path) -> bool:
    """
    El repositorio visto desde fuera, pero con el estado vacio.

    Devuelve False si esta maquina no deja montarlo. En ese caso
    la Regla B se declara inaplicable y pasa: una guardia que no
    puede comprobar algo lo cuenta, no lo suspende.
    """

    for nombre in DEL_REPOSITORIO:

        origen = raiz / nombre

        if not origen.exists():
            continue

        if not _enlazar(destino / nombre, origen):
            return False

    # Lo unico que NO se enlaza: el estado. Vacio y presente, que
    # es como llega un checkout limpio de Actions.
    (destino / ESTADO).mkdir(exist_ok=True)

    return True


def test_los_vigilados_pasan_con_el_estado_vacio() -> None:
    """
    POR QUE NO BASTA CON LEER EL CODIGO

        Un modulo puede tocar el estado sin nombrarlo: llamando a
        una funcion que lo lee por su cuenta. `test_arbitro_v1`
        hacia justo eso con `store_depth()`, y se caia sin
        almacen. Ningun escaneo lo habria visto.

    Se monta un espejo del repositorio con el estado vacio y se
    ejecutan ahi. El codigo es el mismo; lo unico que falta es el
    estado.

    QUE DEMUESTRA Y QUE NO

        Demuestra que el caso que tiro produccion -que en Actions
        no este lo que aqui si esta- queda cubierto. No demuestra
        inmunidad a CUALQUIER contenido posible del almacen; para
        eso esta la Regla A, que prohibe leerlo.
    """

    raiz = Path.cwd().resolve()

    entorno = dict(os.environ)
    entorno["PYTHONPATH"] = str(raiz)
    entorno["PYTHONIOENCODING"] = "utf-8"

    vigilados = sorted(set(DEUDA) | set(REPARADAS))

    with tempfile.TemporaryDirectory(
        prefix="bordalas-espejo-"
    ) as temporal:

        espejo = Path(temporal) / "repo"
        espejo.mkdir()

        if not _espejo_sin_estado(raiz, espejo):
            print(
                "    (esta maquina no deja montar el espejo: la "
                "Regla B no se puede comprobar aqui)"
            )
            return

        for modulo in vigilados:

            salida = subprocess.run(
                [sys.executable, "-m", modulo],
                cwd=espejo,
                env=entorno,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=900,
            )

            assert salida.returncode == 0, (
                f"{modulo} no pasa cuando el estado esta vacio, "
                f"que es lo que Actions tiene en un checkout "
                f"limpio: su veredicto lo decide el estado.\n"
                f"salida:\n"
                f"{(salida.stdout or '')[-1200:]}\n"
                f"{(salida.stderr or '')[-800:]}"
            )


def test_la_puerta_declara_su_lista_en_un_solo_sitio() -> None:
    """
    Si la lista de la verja se partiera en dos, esta guardia
    estaria vigilando media puerta sin enterarse.
    """

    modulos = modulos_de_la_verja()

    assert len(modulos) > 50, (
        f"solo se ven {len(modulos)} comprobaciones en "
        f"{PUERTA}: o la lista ha cambiado de forma, o esta "
        f"guardia esta mirando donde no es"
    )

    for modulo in modulos:
        assert _ruta(modulo).exists(), (
            f"{modulo} esta en la puerta y no existe en el disco"
        )


TESTS = [
    test_ninguna_guardia_de_la_verja_lee_el_estado,
    test_las_dos_que_tiraron_produccion_ya_no_lo_leen,
    test_la_deuda_esta_explicada,
    test_los_vigilados_pasan_con_el_estado_vacio,
    test_la_puerta_declara_su_lista_en_un_solo_sitio,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA VERJA ES DETERMINISTA V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
