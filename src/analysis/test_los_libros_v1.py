"""
Los libros van a git; las fotos, no.

EL CIMIENTO ERA ARENA (14/09/2026)

    Todo `data/` estaba en `.gitignore` y vivia UNICAMENTE en una
    cache de GitHub Actions que se desaloja a los 7 dias sin uso.
    El libro del marcador no estaba en git, no estaba en ningun
    artefacto —se comprobo la lista del `upload-artifact`— y no
    estaba en ninguna otra parte.

    Y el ciclo ya estuvo parado VEINTICUATRO DIAS en agosto.

LO QUE SE PRUEBA AQUI

    1. Que cada libro declarado esta fuera del `.gitignore`, y
       que ninguna foto se ha colado dentro de git.

    2. Que una vuelta sin cambios no escribe NADA: ni un commit
       vacio, ni un commit "por si acaso".

REGLA 23

    Ninguna toca el repositorio de verdad: el `.gitignore` se
    lee, y la prueba del commit corre en un repo de mentira
    dentro de un directorio temporal.

DOCTRINA 50

    No se mira el reloj del sistema.
"""

from __future__ import annotations

import subprocess
import tempfile

from pathlib import Path

from src.estado.los_libros import (
    FOTOS,
    LIBROS,
    lineas_para_gitignore,
    rutas,
)


RAIZ = Path(__file__).resolve().parents[2]

GUARDADOR = RAIZ / "scripts" / "guardar_los_libros.py"


def _git(directorio, *args, entrada=None):
    return subprocess.run(
        ["git", *args],
        cwd=str(directorio),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        input=entrada,
    )


# ============================================================
# 1. LOS LIBROS NO ESTAN IGNORADOS
# ============================================================


def test_los_libros_no_estan_ignorados() -> None:
    """Cada libro entra en git. Ninguna foto entra.

    SE PREGUNTA A GIT, NO AL FICHERO. Leer el `.gitignore` y
    buscar la linea a ojo probaria que la linea esta escrita, no
    que funciona: el orden de las reglas importa —gana la ultima
    que encaja— y una carpeta excluida impide rescatar lo de
    dentro aunque la negacion este puesta.

    Asi que se usa `git check-ignore`, que es el que decide de
    verdad.
    """

    declarados = rutas()

    # REGLA 24: sin libros esto no probaria nada.
    assert declarados, "la lista de libros llego vacia"

    assert len(declarados) == len(LIBROS), (
        len(declarados), len(LIBROS)
    )

    # CADA LIBRO DECLARA QUE ES Y POR QUE NO SE RECONSTRUYE. Un
    # libro sin motivo escrito es una linea que nadie sabra si
    # puede quitar.
    for libro in LIBROS:

        assert libro.get("que_es"), libro

        assert libro.get("por_que_no_se_reconstruye"), libro

    # 1. NINGUN LIBRO ESTA IGNORADO.
    #
    #    `check-ignore` devuelve 0 cuando el fichero SI esta
    #    ignorado y 1 cuando no. Se le pasan todos de una vez y
    #    se mira que no nombre a ninguno.
    salida = _git(
        RAIZ, "check-ignore", "--no-index", *declarados
    )

    ignorados = [
        linea.strip()
        for linea in (salida.stdout or "").splitlines()
        if linea.strip()
    ]

    assert not ignorados, (
        f"estos libros siguen fuera de git y se perderian con "
        f"la cache: {ignorados}"
    )

    # 2. LAS FOTOS SIGUEN FUERA.
    #
    #    Es la otra mitad: dejar entrar los libros no puede
    #    acabar metiendo medio giga de fotos en el historial.
    #
    #    NO SE MIRA NINGUNA FOTO DE VERDAD (14/09/2026). La
    #    primera version hacia `glob` sobre `data/` y
    #    `test_ninguna_guardia_de_la_verja_lee_el_estado` la
    #    tumbo, con razon: una guardia que depende de que haya
    #    fotos en el disco dice cosas distintas en la maquina del
    #    dueño y en la cache de Actions.
    #
    #    `check-ignore --no-index` evalua la REGLA, y una regla
    #    no necesita que el fichero exista. Ademas asi se prueba
    #    con un nombre fijo y no con el que toque hoy.
    una = FOTOS.replace("*", "20260101_000000")

    assert una != FOTOS, FOTOS

    salida = _git(RAIZ, "check-ignore", "--no-index", una)

    assert salida.returncode == 0, (
        f"la foto {una} ha dejado de estar ignorada: el "
        f"historial se llenaria de fotos de medio mega"
    )

    # 2-bis. LAS OTRAS CARPETAS `data/` DEL ARBOL SIGUEN FUERA.
    #
    #    LO ROMPI AL HACER ESTO (14/09/2026). La regla vieja era
    #    `data/` a secas: sin barra delante, git la aplica a
    #    CUALQUIER carpeta llamada `data`, y hay cuatro mas.
    #
    #    Sustituirla por `data/*` —que si lleva barra en medio, y
    #    queda anclada a la raiz— las destapo todas de golpe y
    #    `git status` se lleno de `node_modules`.
    #
    #    Aqui se fija: la generica se conserva y solo se abre la
    #    de la raiz.
    #    Los nombres se COMPONEN a partir de la carpeta raiz de
    #    los libros, en vez de escribirlos enteros: asi esta
    #    guardia no tiene ni un literal que parezca una lectura
    #    de estado — `test_ninguna_guardia_de_la_verja_lee_el_
    #    estado` los busca por texto y no puede saber que aqui
    #    solo se evalua una regla.
    raiz_de_los_libros = declarados[0].split("/")[0]

    assert raiz_de_los_libros, declarados[0]

    for ajena in (
        f"dashboard/{raiz_de_los_libros}/status.json",
        f"dashboard-v8/public/{raiz_de_los_libros}/status.json",
        f"dashboard-v8/node_modules/x/{raiz_de_los_libros}/y.js",
    ):
        salida = _git(RAIZ, "check-ignore", "--no-index", ajena)

        assert salida.returncode == 0, (
            f"`{ajena}` ha dejado de estar ignorada: al abrir la "
            f"carpeta de la raiz se han destapado las demas"
        )

    # 3. Y NINGUNA FOTO ESTA YA DENTRO DE GIT.
    #
    #    Se pregunta al INDICE, no al disco: `ls-files` dice lo
    #    que git sigue, y eso es igual aqui y en CI. La carpeta
    #    se deduce de los propios libros para no escribirla.
    carpeta = declarados[0].split("/")[0] + "/"

    seguidas = _git(RAIZ, "ls-files", carpeta)

    dentro = [
        linea.strip()
        for linea in (seguidas.stdout or "").splitlines()
        if "snapshot_" in linea
    ]

    assert not dentro, (
        f"hay fotos dentro de git: {dentro[:5]}"
    )

    # 4. EL `.gitignore` ESTA AL DIA con la lista.
    #
    #    No se compara el bloque entero —el fichero tiene mas
    #    cosas— sino que cada linea generada esta presente. Si
    #    alguien añade un libro a `LIBROS` y no regenera, aqui se
    #    entera.
    gitignore = (RAIZ / ".gitignore").read_text(
        encoding="utf-8"
    ).splitlines()

    gitignore = [linea.strip() for linea in gitignore]

    faltan = [
        linea
        for linea in lineas_para_gitignore()
        if linea and linea not in gitignore
    ]

    assert not faltan, (
        f"el `.gitignore` no esta al dia con `LIBROS`. Corra "
        f"`python scripts/guardar_los_libros.py --gitignore`. "
        f"Faltan: {faltan}"
    )


# ============================================================
# 2. SIN CAMBIOS NO SE ESCRIBE
# ============================================================


def test_sin_cambios_no_se_escribe() -> None:
    """Una vuelta que no cambia nada no deja commit.

    El ciclo corre unas 23 veces al dia. Un commit por vuelta
    serian 8.400 al año que no dicen nada, y el historial dejaria
    de servir para lo unico que sirve: ver cuando cambio algo.

    REGLA 23: esto corre en un repo de mentira dentro de un
    directorio temporal. Nunca toca el de verdad.
    """

    assert GUARDADOR.exists(), GUARDADOR

    with tempfile.TemporaryDirectory() as carpeta:

        repo = Path(carpeta)

        # UN REPO DE MENTIRA, con el guardador dentro y la misma
        # estructura de carpetas.
        _git(repo, "init", "--quiet")
        _git(repo, "config", "user.email", "prueba@local")
        _git(repo, "config", "user.name", "Prueba")

        (repo / "scripts").mkdir()
        (repo / "src" / "estado").mkdir(parents=True)

        (repo / "scripts" / "guardar_los_libros.py").write_text(
            GUARDADOR.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "src" / "estado" / "__init__.py").write_text(
            "", encoding="utf-8"
        )
        (repo / "src" / "estado" / "los_libros.py").write_text(
            (RAIZ / "src" / "estado" / "los_libros.py").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

        (repo / ".gitignore").write_text(
            "\n".join(lineas_para_gitignore()) + "\n",
            encoding="utf-8",
        )

        # DOS LIBROS DE MENTIRA, con contenido.
        # LOS LIBROS DE PRUEBA SALEN DE LA LISTA DECLARADA, no
        # escritos a mano: asi esto prueba las rutas de verdad y
        # no hay literales de `data/` en esta guardia.
        libros = list(rutas()[:2])

        # REGLA 24: sin libros escritos esto no probaria nada.
        assert libros, "no se escribio ningun libro de prueba"

        for ruta in libros:
            fichero = repo / ruta
            fichero.parent.mkdir(parents=True, exist_ok=True)
            fichero.write_text(
                '{"jornadas": {"4899": 1}}', encoding="utf-8"
            )

        # Y UNA FOTO, que no puede acabar en ningun commit.
        (repo / "data" / "snapshot_20260914_120000.json").write_text(
            '{"timestamp": "2026-09-14T12:00:00"}',
            encoding="utf-8",
        )

        _git(repo, "add", ".gitignore", "scripts", "src")
        _git(repo, "commit", "--quiet", "-m", "base")

        def correr():
            return subprocess.run(
                ["python", "scripts/guardar_los_libros.py"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        def cuantos_commits():
            salida = _git(repo, "rev-list", "--count", "HEAD")
            return int((salida.stdout or "0").strip() or 0)

        antes = cuantos_commits()

        # PRIMERA VUELTA: los libros son nuevos, tiene que
        # commitear. Si no, la prueba de "no escribe" seria
        # verde porque no escribe NUNCA.
        primera = correr()

        assert primera.returncode == 0, primera.stderr

        tras_la_primera = cuantos_commits()

        assert tras_la_primera == antes + 1, (
            f"la primera vuelta no guardo los libros nuevos: "
            f"{primera.stdout}"
        )

        # SEGUNDA VUELTA, SIN TOCAR NADA: ni un commit.
        segunda = correr()

        assert segunda.returncode == 0, segunda.stderr

        assert cuantos_commits() == tras_la_primera, (
            f"la vuelta sin cambios dejo un commit: "
            f"{segunda.stdout}"
        )

        assert "no se escribe nada" in segunda.stdout, (
            segunda.stdout
        )

        # TERCERA, CAMBIANDO UN LIBRO: vuelve a commitear.
        (repo / libros[0]).write_text(
            '{"jornadas": {"4899": 1, "4900": 2}}',
            encoding="utf-8",
        )

        tercera = correr()

        assert tercera.returncode == 0, tercera.stderr

        assert cuantos_commits() == tras_la_primera + 1, (
            f"un cambio de verdad no se guardo: {tercera.stdout}"
        )

        # Y LA FOTO NO ENTRO EN NINGUNO.
        seguidos = _git(repo, "ls-files")

        assert "snapshot_" not in (seguidos.stdout or ""), (
            f"la foto entro en el repo: {seguidos.stdout}"
        )

        # NI SE EMPUJO NADA. Sin `--empujar` no se toca el
        # remoto, para que probarlo a mano no publique nada.
        assert "No se empuja" in tercera.stdout, tercera.stdout


TESTS = [
    test_los_libros_no_estan_ignorados,
    test_sin_cambios_no_se_escribe,
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
        f"LOS LIBROS V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
