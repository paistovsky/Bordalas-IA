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

============================================================
UN SEGURO QUE TIRA EL COCHE AL RIO NO ES UN SEGURO
(15/09/2026)
============================================================

EL SINTOMA, EN LA PRIMERA VUELTA CON ESTO PUESTO

    19:07  arranca la vuelta #1606 y coge su copia del repo
    19:0x  el dueño empuja un cambio
    19:33  la vuelta commitea 12 libros e intenta empujar
           -> rechazado: "the remote contains work that you do
              not have locally"
           -> el script devolvia 1
           -> LA VUELTA ENTERA EN ROJO

    Se perdio una hora de ciclo por un empujon que solo habia
    que reintentar. El bot escribe en `main` cada hora y el dueño
    tambien empuja: van a chocar A DIARIO.

DOS ARREGLOS, Y EL SEGUNDO ES EL IMPORTANTE

    1. TRAER LO DE FUERA ANTES DE EMPUJAR.
    2. Y SI AUN ASI NO SALE, NO PASA NADA: el ciclo sigue.

       Guardar los libros es un SEGURO, no una operacion. No se
       pierde nada por no empujar una vez —el commit queda hecho
       en local y la vuelta siguiente lo lleva—. Se pierde por
       poner la vuelta en rojo.

       Asi que `guardar()` DEVUELVE 0 PASE LO QUE PASE. Lo que
       no hace es callarse: el motivo se imprime y se publica.

TRAER LO DE FUERA SIN PISAR LOS LIBROS: `reset --mixed`

    Nada de `pull --rebase`. Se hace asi:

        git fetch origin <rama>
        git reset --mixed FETCH_HEAD    <- NO TOCA EL DISCO
        git add -- <los libros>
        git commit

    `reset --mixed` mueve HEAD y el indice y deja el directorio
    de trabajo INTACTO. Los libros que el ciclo acaba de escribir
    siguen donde estaban, y se vuelven a añadir ENCIMA de lo que
    venga de fuera. El commit que sale tiene el contenido del
    disco, y no hay conflictos que resolver.

    POR QUE NO UN REBASE. En un rebase, `--ours` y `--theirs`
    estan INVERTIDOS respecto a lo que cualquiera espera, y la
    resolucion de un conflicto en un fichero de 960 KB escrito
    por una maquina no es algo que se deba hacer a ciegas a las
    tres de la mañana. Aqui no hay conflicto posible: se sabe
    quien gana.

QUIEN GANA SI LOS DOS LADOS HAN TOCADO EL MISMO LIBRO

    GANA EL DISCO DEL RUNNER. Y no es una preferencia: es que ya
    estaba decidido antes, por el ORDEN DE LOS PASOS.

        `checkout`               trae lo que hay en git
        `Restore Bordalas state` descomprime la cache ENCIMA

    Cuando el guardado corre, el disco ya es la cache. Lo que
    hubiera en git para ese libro se piso hace veinte minutos,
    en el paso 2 del job.

    Y ademas es lo correcto en el caso normal: los libros se
    ACUMULAN. La copia del disco es la del ultimo guardado mas lo
    que ha escrito esta vuelta; la de git es la del ultimo
    guardado a secas. El disco es un superconjunto.

    EL CASO EN QUE ESTO MUERDE, dicho claro: si el dueño edita
    un libro A MANO y lo empuja, la vuelta siguiente lo va a
    sobrescribir. No por esto, sino por el restore de la cache —
    pero antes el empujon fallaba y ahora no, asi que antes se
    notaba y ahora hay que MIRARLO. Por eso cada vuelta imprime
    QUE libros cambia respecto al remoto: una sobrescritura
    queda en el log del run, no en silencio.

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
import json
import subprocess
import sys
import time

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(RAIZ))

from src.estado.los_libros import (           # noqa: E402
    LIBROS,
    existentes,
    lineas_para_gitignore,
    rutas,
)


# ============================================================
# LA POLITICA DEL EMPUJON
# ============================================================

# TRES INTENTOS, Y LA ESPERA CRECE.
#
#     Lo que falla aqui es una CARRERA: alguien empujo entre
#     nuestro `fetch` y nuestro `push`. Eso se resuelve en
#     segundos, asi que no se espera un minuto por algo que dura
#     tres. Y el ciclo tiene presupuesto de tiempo: el peor caso
#     de aqui son 12 segundos.
#
#     Cada reintento VUELVE A TRAER lo de fuera. Reintentar el
#     mismo empujon rechazado lo unico que consigue es que lo
#     rechacen otra vez.
INTENTOS = 3

ESPERAS = (3, 9)

# Donde queda dicho como fue el ultimo guardado.
#
#     NO ES UN LIBRO, a proposito: cambia en cada vuelta y un
#     libro que cambia en cada vuelta son 8.400 commits al año.
#     Vive en `data/autopilot`, que es de las rutas que el
#     workflow mete en la cache, asi que sobrevive de una vuelta
#     a la siguiente. Si la cache se desaloja, desaparece y la
#     pantalla dice SIN DATO — que es la verdad, no un cero.
ESTADO = Path("data") / "autopilot" / "guardado_de_los_libros.json"


def ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def rama_actual() -> str:
    """
    En que rama esta el runner. Vacio si no se sabe.

    `actions/checkout` deja HEAD en una rama de verdad, pero si
    algun dia quedara suelto (`HEAD` pelado) no se adivina a que
    rama empujar: se dice que no se sabe y no se empuja.
    """

    codigo, salida = git(
        "rev-parse", "--abbrev-ref", "HEAD", permitir_fallo=True
    )

    rama = salida.strip() if codigo == 0 else ""

    return "" if rama in ("", "HEAD") else rama


def traer_lo_de_fuera(rama: str, libros: list) -> dict:
    """
    Pone lo que haya en el remoto DEBAJO de nuestros libros.

    `reset --mixed` no toca el directorio de trabajo: los libros
    que el ciclo acaba de escribir se quedan donde estan y se
    vuelven a añadir encima. Forma fija, nunca lanza.
    """

    codigo, salida = git(
        "fetch", "origin", rama, permitir_fallo=True
    )

    if codigo:
        return {
            "ok": False,
            "avanzo": 0,
            "motivo": (
                f"No se pudo traer lo de fuera (`git fetch "
                f"origin {rama}`): {salida}"
            ),
        }

    # CUANTO SE HA MOVIDO EL REMOTO por debajo de nosotros. Es el
    # numero que delata la carrera, y por eso se publica.
    _, cuenta = git(
        "rev-list", "--count", "HEAD..FETCH_HEAD",
        permitir_fallo=True,
    )

    try:
        avanzo = int((cuenta or "0").strip() or 0)
    except ValueError:
        avanzo = 0

    codigo, salida = git(
        "reset", "--mixed", "FETCH_HEAD", permitir_fallo=True
    )

    if codigo:
        return {
            "ok": False,
            "avanzo": avanzo,
            "motivo": (
                f"No se pudo poner lo de fuera debajo "
                f"(`git reset --mixed FETCH_HEAD`): {salida}"
            ),
        }

    # Y LOS LIBROS DEL DISCO, OTRA VEZ ENCIMA.
    #
    #     Se añaden solo los que EXISTEN. Un libro que el remoto
    #     tiene y este runner no se queda tal cual venia: no se
    #     borra nada que no se haya escrito.
    for ruta in libros:
        git("add", "--", ruta)

    return {"ok": True, "avanzo": avanzo, "motivo": None}


def leer_estado() -> dict:
    """El estado del guardado anterior. Vacio si no hay o no se lee."""

    try:
        return json.loads(
            (RAIZ / ESTADO).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return {}


def publicar_estado(fila: dict) -> None:
    """
    Deja dicho como fue este guardado, para la pantalla.

    Nunca lanza: si esto fallara, el guardado ya esta hecho y no
    tiene sentido tirar nada por no poder contarlo.
    """

    try:
        destino = RAIZ / ESTADO

        destino.parent.mkdir(parents=True, exist_ok=True)

        destino.write_text(
            json.dumps(fila, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )

    except OSError as error:                        # noqa: BLE001
        print(f"  (no se pudo publicar el estado: {error})")


def empujar_con_reintentos(
    rama: str,
    libros: list,
    espera=None,
) -> dict:
    """
    Empuja, y si le ganan la carrera vuelve a traer y reintenta.

    Forma fija, nunca lanza. `espera` en segundos fuerza todas
    las esperas al mismo valor; sin ella se usan las declaradas.
    """

    ultimo = "No se intento empujar."

    for intento in range(1, INTENTOS + 1):

        codigo, salida = git("push", permitir_fallo=True)

        if codigo == 0:
            return {
                "ok": True,
                "intentos": intento,
                "motivo": None,
            }

        ultimo = salida

        print(
            f"  El empujon {intento} de {INTENTOS} no salio: "
            f"{salida.splitlines()[-1] if salida else 'sin salida'}"
        )

        if intento == INTENTOS:
            break

        cuanto = (
            espera
            if espera is not None
            else ESPERAS[intento - 1]
        )

        if cuanto:
            print(f"  Espera {cuanto} s y vuelve a intentarlo.")
            time.sleep(cuanto)

        # SE VUELVE A TRAER. Reintentar el mismo commit rechazado
        # solo consigue que lo rechacen otra vez.
        traido = traer_lo_de_fuera(rama, libros)

        if not traido["ok"]:
            return {
                "ok": False,
                "intentos": intento,
                "motivo": traido["motivo"],
            }

        # Y se rehace el commit encima de lo nuevo. Si tras traer
        # no queda nada que añadir, es que el remoto ya trae lo
        # nuestro: no hay nada que empujar.
        codigo, _ = git(
            "diff", "--cached", "--quiet", "--", *libros,
            permitir_fallo=True,
        )

        if codigo == 0:
            return {
                "ok": True,
                "intentos": intento,
                "motivo": (
                    "Lo de fuera ya traia estos libros: no hacia "
                    "falta empujar."
                ),
            }

        codigo, salida = git(
            "commit", "-m", mensaje_del_commit(libros),
            permitir_fallo=True,
        )

        if codigo:
            return {
                "ok": False,
                "intentos": intento,
                "motivo": (
                    f"No se pudo rehacer el commit sobre lo de "
                    f"fuera: {salida}"
                ),
            }

    return {
        "ok": False,
        "intentos": INTENTOS,
        "motivo": (
            f"El empujon no salio en {INTENTOS} intentos. "
            f"Ultimo motivo de git: {ultimo}"
        ),
    }


def que_cambia(libros: list) -> list:
    """Que libros cambia el commit preparado, con nombre."""

    _, cambiados = git(
        "diff", "--cached", "--name-only", "--", *libros
    )

    return [
        linea.strip()
        for linea in cambiados.splitlines()
        if linea.strip()
    ]


def mensaje_del_commit(libros: list) -> str:
    nombres = que_cambia(libros)

    return (
        "libros: "
        + ", ".join(Path(n).name for n in nombres[:6])
        + (f" (+{len(nombres) - 6})" if len(nombres) > 6 else "")
        + "\n\n"
        + "Escrito por el ciclo. Un commit por cambio real: si\n"
        + "los libros no cambian, la vuelta no escribe nada.\n\n"
        + "Autor-real: Claude Code (VS Code)\n"
    )


def guardar(empujar: bool, espera=None) -> int:
    """
    Añade los libros, commitea si hay cambios y empuja.

    DEVUELVE 0 PASE LO QUE PASE. Guardar los libros es un seguro:
    si falla, se dice fuerte y el ciclo sigue. Lo que no puede
    hacer un seguro es tirar el coche al rio.
    """

    fila = {
        "cuando": ahora_utc(),
        "libros_en_disco": 0,
        "libros_cambiados": 0,
        "commit": False,
        "empujado": False,
        "intentos": 0,
        "origen_avanzo": 0,
        "ok": False,
        "motivo": None,

        # La ultima vez que git estuvo AL DIA con el disco. Se
        # arrastra de la vuelta anterior si esta no lo consigue:
        # es lo que la pantalla convierte en "hace 12 min".
        "ultimo_guardado_ok": (
            leer_estado().get("ultimo_guardado_ok")
        ),
    }

    try:
        codigo = _guardar(empujar, espera, fila)

    except Exception as error:                      # noqa: BLE001
        # NI UNA EXCEPCION TUMBA LA VUELTA.
        fila["ok"] = False
        fila["motivo"] = (
            f"El guardado reviento: "
            f"{type(error).__name__}: {error}"
        )
        codigo = 0

    if not fila["ok"]:
        print()
        print("=" * 60)
        print(" LOS LIBROS NO SE HAN GUARDADO EN GIT")
        print("=" * 60)
        print(f" {fila['motivo']}")
        print(
            " El ciclo NO se para por esto: el commit queda en "
            "local y"
        )
        print(
            " la vuelta siguiente lo lleva. Pero si esto se "
            "repite, los"
        )
        print(" libros vuelven a vivir solo en la cache.")
        print("=" * 60)

    publicar_estado(fila)

    return codigo


def _guardar(empujar: bool, espera, fila: dict) -> int:
    """El guardado de verdad. Escribe en `fila` lo que pasa."""

    hay = existentes(RAIZ)

    fila["libros_en_disco"] = len(hay)

    if not hay:
        # NO ES UN FALLO: el dia 1 no hay libros todavia.
        fila["ok"] = True
        fila["motivo"] = (
            "No hay ningun libro en el disco todavia: no hay "
            "nada que guardar."
        )
        fila["ultimo_guardado_ok"] = fila["cuando"]

        print(fila["motivo"])

        return 0

    # 1. AÑADIR, UNO A UNO Y POR SU RUTA.
    #
    #     `--` separa las rutas de las opciones: un fichero que
    #     empezara por `-` no se interpretaria como bandera.
    for ruta in hay:
        git("add", "--", ruta)

    # 2. LO DE FUERA, DEBAJO — Y ANTES DE DECIDIR SI HAY CAMBIOS.
    #
    #     El orden importa: la pregunta "¿ha cambiado algo?" hay
    #     que hacerla contra lo que va a ser el PADRE del commit.
    #     Preguntandola contra el HEAD viejo se commitearia por
    #     un cambio que el remoto ya trae.
    rama = rama_actual() if empujar else ""

    if empujar and not rama:
        fila["motivo"] = (
            "No se sabe en que rama esta el runner (HEAD "
            "suelto): no se empuja a ciegas."
        )
        empujar = False

    elif empujar:

        traido = traer_lo_de_fuera(rama, hay)

        fila["origen_avanzo"] = traido["avanzo"]

        if traido["avanzo"]:
            print(
                f"El remoto se ha movido {traido['avanzo']} "
                f"commit(s) por debajo: se ponen los libros del "
                f"disco encima."
            )

        if not traido["ok"]:
            fila["motivo"] = traido["motivo"]
            return 0

    # 3. ¿HA CAMBIADO ALGO DE VERDAD?
    #
    #     `diff --cached --quiet` devuelve 1 si hay algo
    #     preparado y 0 si no. Es la pregunta exacta: no "¿hay
    #     ficheros?" sino "¿ha cambiado su contenido?".
    codigo, _ = git(
        "diff", "--cached", "--quiet", "--", *hay,
        permitir_fallo=True,
    )

    if codigo == 0:
        # GIT YA ESTA AL DIA. Eso ES un guardado correcto: no hay
        # nada que llevar, asi que el reloj de la pantalla se
        # refresca igual que si se hubiera empujado.
        fila["ok"] = True
        fila["motivo"] = (
            f"Los {len(hay)} libros estan igual que en el "
            f"ultimo commit: no se escribe nada."
        )
        fila["ultimo_guardado_ok"] = fila["cuando"]

        print(fila["motivo"])

        return 0

    # 4. QUE CAMBIA, CON NOMBRE.
    #
    #     Va al log Y al mensaje del commit. Es ademas lo unico
    #     que delata una sobrescritura: si el dueño edito un
    #     libro a mano y el disco del runner lo pisa, ese libro
    #     sale en esta lista.
    nombres = que_cambia(hay)

    fila["libros_cambiados"] = len(nombres)

    print(f"Cambian {len(nombres)} libro(s) respecto a git:")

    for nombre in nombres:
        print(f"  {nombre}")

    codigo, salida = git(
        "commit", "-m", mensaje_del_commit(hay),
        permitir_fallo=True,
    )

    if codigo:
        fila["motivo"] = f"No se pudo commitear: {salida}"
        return 0

    fila["commit"] = True

    print("Commit hecho.")

    if not empujar:
        # SIN `--empujar` NO ES UN FALLO: es el modo de probarlo
        # a mano sin publicar nada. Pero tampoco es un guardado:
        # el reloj de la pantalla no se toca.
        fila["ok"] = True
        fila["motivo"] = (
            "No se empuja: hace falta `--empujar`, que solo "
            "lleva la linea del workflow."
        )

        print(fila["motivo"])

        return 0

    empujado = empujar_con_reintentos(rama, hay, espera)

    fila["intentos"] = empujado["intentos"]

    if not empujado["ok"]:
        fila["motivo"] = empujado["motivo"]
        return 0

    fila["empujado"] = True
    fila["ok"] = True
    fila["ultimo_guardado_ok"] = fila["cuando"]
    fila["motivo"] = empujado["motivo"]

    print(
        f"Empujado a `{rama}` "
        f"(intento {empujado['intentos']} de {INTENTOS})."
    )

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

    # SOLO PARA PROBARLO. El ciclo no lo pasa, asi que produccion
    # usa siempre las esperas declaradas en `ESPERAS`. Existe
    # para que la guardia pueda ejercitar los tres intentos sin
    # dormir doce segundos dentro de la verja.
    parser.add_argument(
        "--espera",
        type=int,
        default=None,
        help=(
            "Segundos entre reintentos. Sin esto se usan las "
            f"declaradas: {ESPERAS}."
        ),
    )

    args = parser.parse_args()

    if args.gitignore:
        return regenerar_gitignore()

    if args.censo:
        return censo()

    return guardar(args.empujar, args.espera)


if __name__ == "__main__":
    raise SystemExit(main())
