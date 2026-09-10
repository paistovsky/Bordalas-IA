"""
La pantalla se PINTA, y ningun hook es condicional.

SINTOMA

    10/09/2026: verja 108/108 en verde y el dashboard en blanco.

        Minified React error #310
        (mas hooks que en el render anterior)

CAUSA

    En `App.jsx`, el `useState`/`useEffect` del reloj de la
    pastilla quedo DEBAJO de los dos `return` tempranos:

        if (!data) {
          return <div>CARGANDO</div>;   <- sale con 4 hooks
        }
        ...
        const [ahora, setAhora] = useState(...)   <- y aqui 6

    React cuenta los hooks por orden y en el mismo numero cada
    vez -asi sabe cual es cual-, asi que al aparecer dos de la
    nada aborta el arbol entero.

CONSECUENCIA

    La guardia del mismo dia -`test_el_ciclo_publica_v1`- monta
    el ESTADO en Python. Nunca PINTA la pagina, asi que un fallo
    que solo existe en React le pasa por debajo.

    Esta llama a `dashboard-v8/tools/comprobar_pantalla.mjs`, que
    hace las dos mitades:

        1. Lee el arbol de TODOS los .jsx y falla si algun hook
           esta detras de un `return`, dentro de un `if`, de un
           bucle o de un `try`.

        2. Y monta Inicio, Auditoria y la tira con
           `renderToString` y la foto real de `dashboard/data`.

    Las dos, porque ninguna sola basta: `renderToString` hace UNA
    pasada y un hook condicional solo se nota entre dos renders;
    y la lectura del arbol no ve un componente que reviente al
    leer un dato que no viene.

POR QUE ESTO NO ES UN BANCO DE PRUEBAS DE REACT

    No hay que montar ninguno: `node_modules` esta versionado
    -8.308 ficheros- y el workflow ya instala Node 24 antes de
    la verja. Se usa el `esbuild` y el `react-dom/server` que ya
    estaban ahi.
"""

from __future__ import annotations

import shutil
import subprocess

from pathlib import Path


RAIZ = Path(__file__).parents[2]

GUION = (
    RAIZ / "dashboard-v8" / "tools" / "comprobar_pantalla.mjs"
)

MODULOS = RAIZ / "dashboard-v8" / "node_modules"


def _se_puede() -> tuple[bool, str]:
    if shutil.which("node") is None:
        return False, "no hay `node` en el PATH"

    if not GUION.exists():
        return False, f"falta {GUION.name}"

    if not MODULOS.is_dir():
        return False, "falta `dashboard-v8/node_modules`"

    return True, ""


def _corre() -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(GUION)],
        cwd=str(RAIZ / "dashboard-v8"),
        capture_output=True,
        text=True,
        timeout=300,
    )


def test_la_pantalla_se_monta_y_pinta() -> None:
    """
    EL BLANCO DEL 10/09.

    Se monta Inicio, Auditoria y la tira con la foto real. Si
    algo revienta -o si sale una pagina vacia- esto se pone rojo
    antes de que lo vea el dueno.

    Y antes de eso, la lectura del arbol: ningun hook detras de
    un return.
    """

    puede, motivo = _se_puede()

    if not puede:
        # No se calla: se dice. Un salto silencioso aqui seria
        # el mismo agujero con otra forma (doctrina 36).
        print(f"     AVISO: no se puede pintar ({motivo}).")
        return

    resultado = _corre()

    assert resultado.returncode == 0, (
        "la pantalla no pasa la comprobacion:\n"
        + (resultado.stdout or "")
        + (resultado.stderr or "")
    )

    salida = resultado.stdout or ""

    assert "hooks: ninguno condicional" in salida, salida

    # Regla 24: la guardia no pasa con las manos vacias. Si
    # `pintar` dijera "SIN MUESTRA" estariamos comprobando solo
    # la mitad, y hay que verlo.
    assert "pintar: tira" in salida, (
        f"no se ha llegado a pintar ninguna pagina: {salida}"
    )


def test_el_detector_de_hooks_se_prueba_a_si_mismo() -> None:
    """
    La primera version del detector dio VERDE contra el App.jsx
    roto: miraba `sentencia.type === "ReturnStatement"` y los dos
    returns tempranos viven DENTRO de un `if`.

    Un detector que dice "cero" puede estar simplemente roto, y
    entonces es peor que no tenerlo, porque ademas tranquiliza.
    Por eso el guion se pone delante el fallo exacto ANTES de
    opinar de nada, y aqui se comprueba que ese cebo sigue ahi.
    """

    fuente = GUION.read_text(encoding="utf-8")

    assert "EL DETECTOR SE PRUEBA A SI MISMO" in fuente, (
        "el guion ha perdido su cebo: puede volver a dar verde "
        "estando roto"
    )

    assert "EL DETECTOR ESTA ROTO" in fuente, (
        "el cebo ya no aborta si el detector falla"
    )

    # Y que el cebo lleve las dos mitades: cazar lo malo y dejar
    # pasar lo bueno.
    assert "EL DETECTOR CANTA LO QUE ESTA BIEN" in fuente, (
        "el cebo no comprueba los falsos positivos"
    )


TESTS = [
    test_el_detector_de_hooks_se_prueba_a_si_mismo,
    test_la_pantalla_se_monta_y_pinta,
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
        f"LA PANTALLA PINTA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
