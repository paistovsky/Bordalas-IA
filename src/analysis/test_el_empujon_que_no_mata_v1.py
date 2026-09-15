"""
Un empujon fallido no puede tumbar el ciclo.

EL SINTOMA (15/09/2026, primera vuelta con los libros en git)

    19:07  arranca la vuelta #1606 y coge su copia del repo
    19:0x  el dueño empuja un cambio
    19:33  la vuelta commitea 12 libros e intenta empujar
           -> rechazado, el script devolvia 1
           -> LA VUELTA ENTERA EN ROJO

    Una hora de ciclo perdida por un empujon que solo habia que
    reintentar. Y el bot escribe en `main` cada hora mientras el
    dueño tambien empuja: van a chocar a diario.

LO QUE SE PRUEBA AQUI

    1. Que un empujon que NO SALE devuelve 0 y deja dicho por
       que. Un fallo callado es peor que un fallo.
    2. Que antes de empujar se trae lo de fuera, y que el commit
       de fuera SIGUE ESTANDO despues.
    3. Que si los dos lados tocaron el mismo libro gana el disco
       del runner, que es el que acaba de escribirlo.
    4. Que un libro que solo tiene el remoto no se borra.
    5. Que se reintenta, y cuantas veces.

REGLA 23: NI UN BYTE DEL REPOSITORIO DE VERDAD

    Todo corre sobre tres repos de mentira en un directorio
    temporal —un remoto pelado, el runner y "el dueño"—. No hay
    red: `origin` es una ruta del disco. Y el rechazo del empujon
    no se simula con un remoto roto, que probaria otra cosa: se
    provoca con un gancho `pre-receive` que dice que no, que es
    exactamente lo que hace GitHub cuando te ganan la carrera.

DOCTRINA 50: NO SE MIRA EL RELOJ

    Las esperas entre reintentos se fuerzan a cero con `--espera
    0`, que existe para esto. Que las de produccion sean las
    declaradas se comprueba aparte, leyendo la constante.
"""

from __future__ import annotations

import json
import subprocess
import tempfile

from pathlib import Path

from scripts.guardar_los_libros import (
    ESPERAS,
    ESTADO as RUTA_DEL_ESTADO,
    INTENTOS,
)
from src.estado.los_libros import lineas_para_gitignore, rutas


RAIZ = Path(__file__).resolve().parents[2]

GUARDADOR = RAIZ / "scripts" / "guardar_los_libros.py"

LIBROS_RAIZ = RAIZ / "src" / "estado" / "los_libros.py"

RAMA = "main"

# DONDE EL GUARDADOR DEJA DICHO COMO LE FUE.
#
#     Se le PREGUNTA al guardador en vez de escribirla aqui, por
#     lo mismo que los libros de prueba salen de `rutas()`: una
#     ruta copiada a mano se queda vieja el dia que el fichero se
#     mueva, y esta guardia seguiria verde comprobando un sitio
#     donde ya no escribe nadie.
#
#     Y de paso no hay ni un literal del almacen en esta
#     guardia, que es lo que exige
#     `test_ninguna_guardia_de_la_verja_lee_el_estado`. Me cazo
#     escribiendo esto.
ESTADO = RUTA_DEL_ESTADO.as_posix()


def _git(directorio, *args):
    return subprocess.run(
        ["git", *args],
        cwd=str(directorio),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _correr(repo, *args):
    """El guardador, dentro del repo de mentira."""

    return subprocess.run(
        ["python", "scripts/guardar_los_libros.py", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _plantar_codigo(repo: Path) -> None:
    """El guardador y la lista de libros, dentro del repo."""

    (repo / "scripts").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "estado").mkdir(parents=True, exist_ok=True)

    (repo / "scripts" / "guardar_los_libros.py").write_text(
        GUARDADOR.read_text(encoding="utf-8"), encoding="utf-8"
    )

    for vacio in (
        repo / "src" / "__init__.py",
        repo / "src" / "estado" / "__init__.py",
    ):
        vacio.write_text("", encoding="utf-8")

    (repo / "src" / "estado" / "los_libros.py").write_text(
        LIBROS_RAIZ.read_text(encoding="utf-8"), encoding="utf-8"
    )

    (repo / ".gitignore").write_text(
        "\n".join(lineas_para_gitignore()) + "\n",
        encoding="utf-8",
    )


def _escribir(repo: Path, ruta: str, texto: str) -> None:
    fichero = repo / ruta
    fichero.parent.mkdir(parents=True, exist_ok=True)
    fichero.write_text(texto, encoding="utf-8")


def _montar(carpeta: str) -> tuple:
    """
    Tres repos: el remoto pelado, el runner y el dueño.

    Devuelve `(remoto, runner, dueño, libros)`. Los libros salen
    de la lista declarada, no escritos a mano: asi esta guardia
    prueba las rutas de verdad y no lleva literales de datos.
    """

    base = Path(carpeta)

    remoto = base / "remoto.git"

    runner = base / "runner"

    dueno = base / "dueno"

    _git(base, "init", "--quiet", "--bare", str(remoto))

    # --- EL RUNNER ---
    runner.mkdir()

    _git(runner, "init", "--quiet")
    _git(runner, "config", "user.email", "ciclo@local")
    _git(runner, "config", "user.name", "ciclo")

    _plantar_codigo(runner)

    _git(runner, "add", ".gitignore", "scripts", "src")
    _git(runner, "commit", "--quiet", "-m", "base")
    _git(runner, "branch", "-M", RAMA)
    _git(runner, "remote", "add", "origin", str(remoto))
    _git(runner, "push", "--quiet", "-u", "origin", RAMA)

    # EL `HEAD` DEL REMOTO, A NUESTRA RAMA.
    #
    #     `git init --bare` lo deja apuntando a la rama por
    #     defecto de QUIEN EJECUTA —`master` en esta maquina— y
    #     entonces `git clone` deja al dueño en una rama huerfana
    #     distinta: sus commits se iban a `master`, el runner
    #     nunca los veia y dos pruebas de aqui se ponian verdes
    #     sin haber probado nada. Se vio escribiendo esto.
    _git(remoto, "symbolic-ref", "HEAD", f"refs/heads/{RAMA}")

    # --- EL DUEÑO, que empuja por su cuenta ---
    _git(base, "clone", "--quiet", "-b", RAMA, str(remoto), str(dueno))
    _git(dueno, "config", "user.email", "dueno@local")
    _git(dueno, "config", "user.name", "dueno")

    libros = list(rutas()[:3])

    return remoto, runner, dueno, libros


def _contenido_en_el_remoto(remoto: Path, ruta: str) -> str:
    salida = _git(remoto, "show", f"{RAMA}:{ruta}")

    return salida.stdout or ""


def _estado(runner: Path) -> dict:
    fichero = runner / ESTADO

    if not fichero.exists():
        return {}

    try:
        return json.loads(fichero.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def _que_diga_que_no(remoto: Path) -> None:
    """
    Un gancho que rechaza todo empujon.

    Es como se comporta GitHub cuando el remoto se ha movido:
    acepta el `fetch` y rechaza el `push`. Un remoto ROTO no
    serviria — probaria el fallo del fetch, que es otro camino.
    """

    ganchos = remoto / "hooks"

    ganchos.mkdir(parents=True, exist_ok=True)

    gancho = ganchos / "pre-receive"

    gancho.write_text(
        "#!/bin/sh\n"
        "echo 'remote: rechazado a proposito por la guardia' >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )

    gancho.chmod(0o755)


# ============================================================
# REGLA 24: EL MONTAJE TIENE QUE SERVIR PARA ALGO
# ============================================================


def test_el_montaje_trae_libros_y_empuja_de_verdad() -> None:
    """
    Si el montaje dejara de escribir libros, o el empujon feliz
    dejara de funcionar, las demas pruebas se pondrian verdes sin
    haber ejercitado nada.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, dueno, libros = _montar(carpeta)

        assert libros, "no se escribio ningun libro de prueba"

        # EL DUEÑO TIENE QUE PODER MOVER LA RAMA DE VERDAD.
        #
        #     Si su clon quedara en otra rama, sus empujones se
        #     irian a un sitio que el runner no mira y las dos
        #     pruebas de la carrera pasarian sin carrera. Paso.
        assert (
            _git(dueno, "rev-parse", "--abbrev-ref", "HEAD")
            .stdout.strip()
            == RAMA
        ), "el clon del dueño no esta en la rama del runner"

        antes = _git(remoto, "rev-parse", RAMA).stdout.strip()

        _escribir(dueno, "config/prueba.json", "{}")
        _git(dueno, "add", "config/prueba.json")
        _git(dueno, "commit", "--quiet", "-m", "comprobacion")
        _git(dueno, "push", "--quiet")

        assert (
            _git(remoto, "rev-parse", RAMA).stdout.strip() != antes
        ), "el empujon del dueño no mueve la rama del remoto"

        for ruta in libros:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        salida = _correr(runner, "--empujar", "--espera", "0")

        assert salida.returncode == 0, salida.stdout + salida.stderr

        assert "Empujado" in salida.stdout, salida.stdout

        for ruta in libros:
            assert "4899" in _contenido_en_el_remoto(
                remoto, ruta
            ), f"{ruta} no llego al remoto: {salida.stdout}"

        fila = _estado(runner)

        assert fila.get("empujado") is True, fila

        assert fila.get("libros_en_disco") == len(libros), fila

        assert fila.get("ultimo_guardado_ok"), fila

    print(
        f"  OK  el montaje escribe {len(libros)} libros y el "
        f"empujon feliz los lleva al remoto"
    )


# ============================================================
# 1. UN EMPUJON FALLIDO NO TUMBA EL CICLO
# ============================================================


def test_un_empujon_fallido_no_tumba_el_ciclo() -> None:
    """
    Con el empujon rechazado, el script devuelve 0 y DICE por
    que. Las dos cosas: un fallo callado es peor que un fallo.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, _, libros = _montar(carpeta)

        for ruta in libros:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        _que_diga_que_no(remoto)

        salida = _correr(runner, "--empujar", "--espera", "0")

        # 1. EL CICLO SIGUE.
        assert salida.returncode == 0, (
            f"un empujon fallido ha devuelto "
            f"{salida.returncode}: la vuelta entera se cae por un "
            f"seguro que no pudo guardar.\n{salida.stdout}"
        )

        # 2. Y SE DICE FUERTE.
        assert "LOS LIBROS NO SE HAN GUARDADO EN GIT" in (
            salida.stdout
        ), salida.stdout

        fila = _estado(runner)

        assert fila.get("ok") is False, fila

        assert fila.get("empujado") is False, fila

        # 3. EL MOTIVO NO PUEDE VENIR VACIO.
        motivo = (fila.get("motivo") or "").strip()

        assert motivo, (
            "el empujon fallo y no dejo motivo: un fallo sin "
            "motivo no se puede arreglar"
        )

        assert motivo in salida.stdout, (
            f"el motivo no sale en el log de la vuelta: "
            f"{motivo!r}"
        )

        # 4. Y EL COMMIT SE QUEDA HECHO EN LOCAL, que es lo que
        #    permite que la vuelta siguiente lo lleve.
        assert fila.get("commit") is True, fila

        pendiente = _git(
            runner, "rev-list", "--count", f"origin/{RAMA}..{RAMA}"
        )

        assert int((pendiente.stdout or "0").strip()) >= 1, (
            "no ha quedado ningun commit pendiente de empujar: "
            "entonces no hay nada que llevar mañana"
        )

    print(
        "  OK  el empujon falla, el ciclo devuelve 0, el motivo "
        "se dice y el commit queda en local"
    )


def test_se_reintenta_y_se_dice_cuantas_veces() -> None:
    """
    Tres intentos, y el log los cuenta. Si algun dia se quedara
    en uno, esto lo dice.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, _, libros = _montar(carpeta)

        for ruta in libros:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        _que_diga_que_no(remoto)

        salida = _correr(runner, "--empujar", "--espera", "0")

        for intento in range(1, INTENTOS + 1):
            assert (
                f"El empujon {intento} de {INTENTOS}"
                in salida.stdout
            ), (
                f"no consta el intento {intento}: "
                f"{salida.stdout}"
            )

        fila = _estado(runner)

        assert fila.get("intentos") == INTENTOS, fila

        assert str(INTENTOS) in (fila.get("motivo") or ""), fila

    print(
        f"  OK  se reintenta {INTENTOS} veces y los intentos se "
        f"cuentan"
    )


def test_las_esperas_son_las_declaradas() -> None:
    """
    Las esperas de produccion no se prueban durmiendo: se leen.

    `--espera` existe solo para que esta guardia no tarde doce
    segundos, y por eso hay que comprobar aparte que sin ella
    quedan las declaradas — y que hay una por hueco entre
    intentos, ni una mas.
    """

    assert INTENTOS >= 2, (
        f"con {INTENTOS} intento(s) no hay reintento que valga"
    )

    assert len(ESPERAS) == INTENTOS - 1, (
        f"{INTENTOS} intentos necesitan {INTENTOS - 1} esperas y "
        f"hay {len(ESPERAS)}: {ESPERAS}"
    )

    assert all(e > 0 for e in ESPERAS), (
        f"una espera de cero reintenta dentro de la misma carrera "
        f"que acaba de perder: {ESPERAS}"
    )

    assert list(ESPERAS) == sorted(ESPERAS), (
        f"las esperas tienen que crecer: {ESPERAS}"
    )

    # Y NO PUEDEN COMERSE LA VUELTA. El peor caso es lo que el
    # ciclo paga por un remoto que no contesta.
    assert sum(ESPERAS) <= 60, (
        f"el peor caso son {sum(ESPERAS)} s de espera dentro de "
        f"la vuelta: demasiado para un seguro"
    )

    print(
        f"  OK  {INTENTOS} intentos con esperas de "
        f"{ESPERAS} s ({sum(ESPERAS)} s en el peor caso)"
    )


# ============================================================
# 2. SE TRAE LO DE FUERA ANTES DE EMPUJAR
# ============================================================


def test_se_trae_lo_de_fuera_y_no_se_pierde() -> None:
    """
    El caso exacto de la vuelta #1606: el dueño empuja mientras
    el runner trabaja.

    Tienen que quedar LAS DOS COSAS: su cambio y nuestros libros.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, dueno, libros = _montar(carpeta)

        for ruta in libros:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        # EL DUEÑO SE COLA EN MEDIO.
        _escribir(dueno, "config/algo.json", '{"del": "dueno"}')
        _git(dueno, "add", "config/algo.json")
        _git(dueno, "commit", "--quiet", "-m", "del dueño")
        _git(dueno, "push", "--quiet")

        salida = _correr(runner, "--empujar", "--espera", "0")

        assert salida.returncode == 0, salida.stdout

        fila = _estado(runner)

        assert fila.get("empujado") is True, (
            f"no se empujo pese a que solo habia que traer lo de "
            f"fuera:\n{salida.stdout}"
        )

        assert fila.get("origen_avanzo") == 1, (
            f"no se ha visto que el remoto se movio: {fila}"
        )

        assert "se ha movido 1 commit" in salida.stdout, (
            salida.stdout
        )

        # LO SUYO SIGUE.
        assert "del" in _contenido_en_el_remoto(
            remoto, "config/algo.json"
        ), "el empujon del ciclo se ha comido el commit del dueño"

        # Y LO NUESTRO TAMBIEN.
        for ruta in libros:
            assert "4899" in _contenido_en_el_remoto(
                remoto, ruta
            ), f"{ruta} no llego al remoto"

    print(
        "  OK  se trae lo de fuera, se empuja encima y no se "
        "pierde ni lo suyo ni lo nuestro"
    )


def test_gana_el_disco_del_runner() -> None:
    """
    Los dos lados han tocado el mismo libro. Gana el del runner.

    Y no es una preferencia: cuando esto corre, el disco YA es la
    cache —`Restore Bordalas state` la descomprimio encima del
    `checkout`—, asi que lo de git para ese libro se piso hace
    veinte minutos. Ademas los libros se acumulan: el del disco
    es el del ultimo guardado MAS lo de esta vuelta.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, dueno, libros = _montar(carpeta)

        disputado = libros[0]

        # EL DUEÑO ESCRIBE SU VERSION Y LA EMPUJA.
        _escribir(dueno, disputado, '{"quien": "el dueño"}')
        _git(dueno, "add", "--", disputado)
        _git(dueno, "commit", "--quiet", "-m", "a mano")
        _git(dueno, "push", "--quiet")

        # EL RUNNER TIENE LA SUYA EN EL DISCO.
        _escribir(runner, disputado, '{"quien": "el ciclo"}')

        salida = _correr(runner, "--empujar", "--espera", "0")

        assert salida.returncode == 0, salida.stdout

        assert _estado(runner).get("empujado") is True, (
            f"un libro tocado por los dos lados ha bloqueado el "
            f"empujon:\n{salida.stdout}"
        )

        final = _contenido_en_el_remoto(remoto, disputado)

        assert "el ciclo" in final, (
            f"no gano el disco del runner: el remoto se quedo "
            f"con {final!r}"
        )

        # Y LA SOBRESCRITURA SE VE EN EL LOG. Es lo unico que
        # separa "el disco gana" de "el disco pisa en silencio".
        assert disputado in salida.stdout, (
            f"el libro sobrescrito no sale en el log de la "
            f"vuelta:\n{salida.stdout}"
        )

    print(
        "  OK  gana el disco del runner, y el libro que pisa "
        "queda dicho en el log"
    )


def test_un_libro_que_solo_tiene_el_remoto_no_se_borra() -> None:
    """
    El runner no escribe todos los libros todas las vueltas.

    Uno que este en git y no en el disco tiene que SEGUIR en git
    despues del empujon: no se añade, pero tampoco se borra.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, dueno, libros = _montar(carpeta)

        ajeno = libros[2]

        _escribir(dueno, ajeno, '{"solo": "en git"}')
        _git(dueno, "add", "--", ajeno)
        _git(dueno, "commit", "--quiet", "-m", "un libro mas")
        _git(dueno, "push", "--quiet")

        # El runner escribe OTROS, nunca ese.
        for ruta in libros[:2]:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        assert not (runner / ajeno).exists(), (
            "el montaje no prueba lo que dice: el libro ajeno "
            "esta en el disco del runner"
        )

        salida = _correr(runner, "--empujar", "--espera", "0")

        assert salida.returncode == 0, salida.stdout

        assert "solo" in _contenido_en_el_remoto(remoto, ajeno), (
            f"el empujon del ciclo ha borrado un libro que solo "
            f"tenia git:\n{salida.stdout}"
        )

    print(
        "  OK  un libro que solo tiene el remoto sobrevive al "
        "empujon"
    )


# ============================================================
# 3. LO QUE NO PUEDE PASAR
# ============================================================


def test_sin_empujar_no_se_toca_el_remoto() -> None:
    """
    Probarlo a mano no publica nada. Sigue siendo verdad.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, _, libros = _montar(carpeta)

        for ruta in libros:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        antes = _git(remoto, "rev-parse", RAMA).stdout.strip()

        salida = _correr(runner)

        assert salida.returncode == 0, salida.stdout

        assert "No se empuja" in salida.stdout, salida.stdout

        despues = _git(remoto, "rev-parse", RAMA).stdout.strip()

        assert antes == despues, (
            "sin `--empujar` se ha movido el remoto"
        )

        # Y el reloj de la pantalla NO se toca: un commit local
        # no es un guardado.
        assert not _estado(runner).get("ultimo_guardado_ok"), (
            _estado(runner)
        )

    print(
        "  OK  sin `--empujar` no se toca el remoto ni el reloj "
        "de la pantalla"
    )


def test_el_estado_no_es_un_libro() -> None:
    """
    El fichero de estado cambia en CADA vuelta. Si entrara en
    git serian 8.400 commits al año, que es justo lo que este
    script existe para no hacer.
    """

    assert ESTADO not in rutas(), (
        f"{ESTADO} esta declarado como libro: cambia en cada "
        f"vuelta y llenaria el historial"
    )

    with tempfile.TemporaryDirectory() as carpeta:

        remoto, runner, _, libros = _montar(carpeta)

        for ruta in libros:
            _escribir(runner, ruta, '{"jornadas": {"4899": 1}}')

        _correr(runner, "--empujar", "--espera", "0")

        assert (runner / ESTADO).exists(), (
            "el estado no se ha escrito: la pantalla se queda "
            "sin saber si los libros se guardan"
        )

        seguidos = _git(remoto, "ls-tree", "-r", "--name-only", RAMA)

        assert ESTADO not in (seguidos.stdout or ""), (
            f"el estado del guardado ha entrado en git:\n"
            f"{seguidos.stdout}"
        )

    print("  OK  el estado se escribe y no entra en git")


TESTS = [
    test_el_montaje_trae_libros_y_empuja_de_verdad,
    test_un_empujon_fallido_no_tumba_el_ciclo,
    test_se_reintenta_y_se_dice_cuantas_veces,
    test_las_esperas_son_las_declaradas,
    test_se_trae_lo_de_fuera_y_no_se_pierde,
    test_gana_el_disco_del_runner,
    test_un_libro_que_solo_tiene_el_remoto_no_se_borra,
    test_sin_empujar_no_se_toca_el_remoto,
    test_el_estado_no_es_un_libro,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL EMPUJON QUE NO MATA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
