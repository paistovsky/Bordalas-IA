"""
La verja corre con los interruptores que enciende CI, y lo dice.

LO QUE PASO (22/09/2026)

    Dos ciclos parados el mismo dia. El segundo, la corrida
    #1753, murio en la verja en `test_el_corte_y_el_cupo_v1`.
    Esa misma guardia, en el portatil, estaba verde.

    El motivo no era la guardia: el workflow trae encendido
    `BORDALAS_REVENTA_SOLO_SI_JUEGA` y la verja local corria sin
    el. Doctrina 112: un verde en el portatil no es un verde de
    produccion.

QUE VIGILA ESTA GUARDIA

    Que la verja SE PONGA ELLA SOLA los interruptores que el
    fichero de CI declara encendidos, en vez de esperar a que
    alguien se acuerde de escribirlos en la consola.

    Y que si no puede leer ese fichero NO DE VERDE. Doctrina 91:
    un rojo que puede significar cualquier cosa vale lo mismo
    que un verde, y un verde que no sabe con que ha corrido es
    peor todavia.

EL EJEMPLO TIENE QUE MORDER (doctrina 24)

    Un YAML de ejemplo que no encienda ninguno haria pasar esta
    guardia sin probar nada: cero encendidos es exactamente lo
    que devuelve un parser roto. Asi que se comprueba que el
    ejemplo enciende DOS, y se comprueba aparte que un ejemplo
    sin ninguno devuelve cero -que es lo que distingue "no hay"
    de "no se miro", doctrina 103-.

NO MIRA EL MUNDO

    No sale a la red, no abre `data/`, no mira el reloj y no lee
    `os.environ`: los entornos se le pasan a mano. El unico
    fichero que abre es el suyo de ejemplo, en un temporal, y el
    del workflow, que es fuente del repositorio.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis.los_interruptores_de_produccion import (   # noqa: E402
    WORKFLOW,
    el_entorno_de_produccion,
    la_cabecera,
    los_de_produccion,
)


# ============================================================
# EL YAML DE EJEMPLO
# ============================================================
#
#     Lleva a proposito las cuatro formas de NO estar encendido
#     que aparecen en el fichero de verdad: comentado, a "0", un
#     secreto y una variable que no es un interruptor.
#
#     LOS NOMBRES SON DE VERDAD, Y NO ES DECORACION
#
#         `scripts/los_interruptores.py` censa TODO lo que
#         empiece por `BORDALAS_` en el repositorio, y el paso 0
#         apunta ese censo en `config/paso_0.json` como probado.
#         Con nombres inventados aqui, el 22/09 entraron tres
#         interruptores que no existen. El censo es un artefacto
#         de verdad: no se ensucia con ejemplos.
EL_YAML_DE_EJEMPLO = """
name: ejemplo

jobs:
  live:
    runs-on: ubuntu-latest
    env:
      TZ: Europe/Madrid
      BIWENGER_USERNAME: ${{ secrets.BIWENGER_USERNAME }}
      BORDALAS_BID_SALT: ${{ secrets.BORDALAS_BID_SALT }}

      BORDALAS_JORNADAS_POR_SU_FECHA: "1"
      BORDALAS_REVENTA_SOLO_SI_JUEGA: "1"

      BORDALAS_SIN_SUBASTA: "0"
      # BORDALAS_TOPE_DEL_ONCE: "1"
"""


LOS_DOS_DEL_EJEMPLO = [
    "BORDALAS_JORNADAS_POR_SU_FECHA",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA",
]


EL_YAML_SIN_NINGUNO = """
name: ejemplo

jobs:
  live:
    env:
      TZ: Europe/Madrid
      BORDALAS_SIN_SUBASTA: "0"
      # BORDALAS_TOPE_DEL_ONCE: "1"
"""


def _en_un_fichero(texto: str):
    """El ejemplo, en un temporal. Nunca en `data/`."""

    carpeta = tempfile.mkdtemp(prefix="verja_como_ci_")

    destino = Path(carpeta) / "ejemplo.yml"

    destino.write_text(texto, encoding="utf-8")

    return destino


def _la_puerta():
    """El script de la verja, cargado por ruta."""

    ruta = RAIZ / "scripts" / "run_validation_gate.py"

    spec = importlib.util.spec_from_file_location("_la_puerta", ruta)

    modulo = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(modulo)

    return modulo


def test_la_verja_corre_como_CI() -> None:
    """
    Con un YAML de ejemplo que enciende dos, la verja los reporta
    como puestos.
    """

    # EL EJEMPLO MUERDE O NO PRUEBA NADA.
    #
    #     Si alguien cambia el ejemplo por uno que no encienda
    #     ninguno, esto se pone rojo aqui mismo, antes de mirar
    #     el resultado.
    assert len(LOS_DOS_DEL_EJEMPLO) == 2, (
        "el ejemplo tiene que encender DOS interruptores: uno "
        "que no encienda ninguno pasaria esta guardia con el "
        "parser roto"
    )

    fichero = _en_un_fichero(EL_YAML_DE_EJEMPLO)

    leido = los_de_produccion(fichero)

    assert leido["ok"] is True, leido["reason"]

    assert leido["interruptores"] == LOS_DOS_DEL_EJEMPLO, (
        f"del ejemplo tenian que salir {LOS_DOS_DEL_EJEMPLO} y "
        f"salieron {leido['interruptores']}"
    )

    # Y PUESTOS DE VERDAD EN EL ENTORNO QUE CORRE LA GUARDIA.
    #
    #     Reportarlos y no ponerlos seria la misma mentira con
    #     mejor letra.
    preparado = el_entorno_de_produccion({}, leido["interruptores"])

    for nombre in LOS_DOS_DEL_EJEMPLO:
        assert preparado["entorno"].get(nombre) == "1", (
            f"{nombre} sale del YAML encendido y no llega puesto "
            f"al entorno de la guardia"
        )

    assert sorted(preparado["puestos"]) == LOS_DOS_DEL_EJEMPLO

    # Y LO DICE. La cabecera lleva el numero y los nombres.
    cabecera = la_cabecera(leido["interruptores"])

    assert "2 interruptores de produccion" in cabecera, cabecera

    for nombre in LOS_DOS_DEL_EJEMPLO:
        assert nombre in cabecera, cabecera


def test_un_ejemplo_sin_ninguno_no_prueba_nada() -> None:
    """
    Cero encendidos es lo que devuelve un parser roto. Que el
    ejemplo de verdad encienda dos es lo unico que separa esta
    guardia de una que no mira. Doctrina 103.
    """

    fichero = _en_un_fichero(EL_YAML_SIN_NINGUNO)

    leido = los_de_produccion(fichero)

    assert leido["ok"] is True, leido["reason"]

    assert leido["interruptores"] == [], (
        f"un YAML sin ninguno encendido tiene que dar cero, y dio "
        f"{leido['interruptores']}"
    )

    assert "0 interruptores" in la_cabecera(leido["interruptores"])


def test_el_secreto_no_es_un_interruptor() -> None:
    """
    `BORDALAS_BID_SALT: ${{ secrets.X }}` lleva el prefijo y no
    es un interruptor de comportamiento: su valor no es un
    literal encendido.
    """

    fichero = _en_un_fichero(EL_YAML_DE_EJEMPLO)

    leido = los_de_produccion(fichero)

    assert "BORDALAS_BID_SALT" not in leido["interruptores"], (
        "un secreto se ha contado como interruptor encendido"
    )

    assert "BORDALAS_SIN_SUBASTA" not in leido["interruptores"]

    assert "BORDALAS_TOPE_DEL_ONCE" not in leido["interruptores"]


def test_gana_el_yaml_y_lo_avisa() -> None:
    """
    Si el entorno de quien lanza dice una cosa y el YAML otra,
    manda el YAML.

    Un `BORDALAS_*` suelto en la consola no puede cambiar en
    silencio lo que la verja esta probando: seria el fallo de hoy
    del reves.
    """

    entorno = {
        "PATH": "/lo/que/sea",
        "BORDALAS_VARA_PLANA": "1",
        "BORDALAS_VIGILA_DATA": "1",

        # Y LA CONTRADICCION DEL OTRO LADO: apagado a mano en la
        # consola, encendido en CI.
        LOS_DOS_DEL_EJEMPLO[0]: "0",
    }

    preparado = el_entorno_de_produccion(entorno, LOS_DOS_DEL_EJEMPLO)

    assert "BORDALAS_VARA_PLANA" not in preparado["entorno"], (
        "un interruptor que CI no enciende ha sobrevivido al "
        "entorno de la verja"
    )

    assert preparado["quitados"] == ["BORDALAS_VARA_PLANA"]

    assert any(
        "BORDALAS_VARA_PLANA" in aviso
        for aviso in preparado["avisos"]
    ), "se quito sin decirlo"

    # APAGADO A MANO NO GANA A ENCENDIDO EN CI.
    assert preparado["entorno"][LOS_DOS_DEL_EJEMPLO[0]] == "1", (
        "un `0` en la consola ha ganado al workflow: la verja "
        "estaria probando otra cosa que produccion"
    )

    assert any(
        LOS_DOS_DEL_EJEMPLO[0] in aviso and '"0"' in aviso
        for aviso in preparado["avisos"]
    ), preparado["avisos"]

    # EL VIGILANTE DE `data/` NO ES UN INTERRUPTOR DEL BOT.
    #
    #     Lo pone la propia verja, es herramienta del corredor y
    #     no cambia ninguna decision: quitarlo seria apagar el
    #     unico ojo que mira si una guardia escribe en `data/`.
    assert preparado["entorno"].get("BORDALAS_VIGILA_DATA") == "1"

    # Y lo que no es un interruptor, intacto.
    assert preparado["entorno"].get("PATH") == "/lo/que/sea"


def test_sin_fichero_no_hay_verde() -> None:
    """
    Si no se puede leer el fichero de CI, no se adivina: se dice
    y se sale distinto de cero. Doctrina 91.
    """

    fantasma = Path(tempfile.mkdtemp(prefix="verja_como_ci_")) / "no_existe.yml"

    leido = los_de_produccion(fantasma)

    assert leido["ok"] is False, (
        "un fichero que no existe ha dado por bueno el entorno"
    )

    assert "no_existe" in str(leido["reason"]), leido["reason"]

    # Y LA PUERTA SALE DISTINTO DE CERO.
    #
    #     El import de la verja se hace DENTRO de `main`, asi que
    #     cambiar aqui el atributo del modulo basta: no hace
    #     falta tocar disco ni correr ninguna guardia.
    import src.analysis.los_interruptores_de_produccion as modulo

    original = modulo.los_de_produccion

    argv = list(sys.argv)

    try:
        modulo.los_de_produccion = lambda ruta=None: {
            "ok": False,
            "interruptores": [],
            "ruta": str(fantasma),
            "reason": "de mentira, para esta guardia",
        }

        sys.argv = ["run_validation_gate.py"]

        codigo = _la_puerta().main()

    finally:
        modulo.los_de_produccion = original

        sys.argv = argv

    assert codigo != 0, (
        "la verja ha dado verde sin saber con que interruptores "
        "corre produccion"
    )


def test_el_fichero_de_ci_de_verdad_se_lee() -> None:
    """
    El de verdad, no el de ejemplo. No se mira QUE enciende -eso
    es del dueño y cambia-, solo que se puede leer.

    Si alguien lo renombra, esto lo dice con su nombre en vez de
    dejar a la verja corriendo con cero interruptores y verde.
    """

    leido = los_de_produccion()

    assert leido["ok"] is True, leido["reason"]

    assert str(WORKFLOW) == leido["ruta"]

    assert isinstance(leido["interruptores"], list)


TESTS = [
    test_la_verja_corre_como_CI,
    test_un_ejemplo_sin_ninguno_no_prueba_nada,
    test_el_secreto_no_es_un_interruptor,
    test_gana_el_yaml_y_lo_avisa,
    test_sin_fichero_no_hay_verde,
    test_el_fichero_de_ci_de_verdad_se_lee,
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

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"ERROR {test.__name__}: {type(error).__name__}: {error}")

    print()
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
