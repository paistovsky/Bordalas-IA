"""
La lista de guardias vive en un solo sitio, y CI corre esa.

SINTOMA

    `.github/workflows/bordalas-live.yml` llevaba las 66 guardias
    escritas a mano, linea por linea, y
    `scripts/run_validation_gate.py` las leia de ahi con una
    expresion regular.

    La idea era buena -una sola fuente de verdad- pero el sitio
    era el equivocado: cada guardia nueva habia que acordarse de
    ponerla en el workflow ademas de escribirla.

CAUSA

    Que el fichero que EJECUTA la lista y el fichero que la
    DECLARA fueran el mismo, y ese fichero fuera el de CI. Añadir
    una guardia y olvidarse de la linea del YAML no rompe nada
    visible: el paso sigue saliendo verde.

CONSECUENCIA

    CI correria menos guardias que el dueño en local, y **sin
    avisar de nada**. Un fallo silencioso, que es la clase mas
    cara: la que se descubre cuando ya ha costado dinero.

    Ahora la lista esta en el script y el workflow solo le llama.
    Esta guardia protege que siga siendo asi:

      - que el workflow no vuelva a tener una lista a mano;
      - que llame al script;
      - que el script devuelva != 0 cuando algo falla, porque de
        eso depende que CI pare el ciclo. Si diera 0 siempre, el
        remedio seria peor que la enfermedad;
      - y que todos los modulos de la lista existan de verdad.
"""

from __future__ import annotations

import re
import subprocess
import sys

from pathlib import Path


WORKFLOW = Path(".github/workflows/bordalas-live.yml")
SCRIPT = Path("scripts/run_validation_gate.py")


def _gate():
    """El modulo de la puerta, importado desde su ruta."""

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_validation_gate", SCRIPT
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo


# ============================================================
# 1. UNA SOLA LISTA
# ============================================================


def test_el_workflow_ya_no_lleva_la_lista_a_mano() -> None:
    texto = WORKFLOW.read_text(encoding="utf-8")

    sueltos = re.findall(r"python\s+-m\s+([\w.]*test[\w.]*)", texto)

    assert not sueltos, (
        f"el workflow ha vuelto a llevar guardias escritas a mano "
        f"({len(sueltos)}: {sueltos[:3]}...). Con la lista en dos "
        f"sitios, el dia que se olvide una CI correra menos que el "
        f"dueño y no avisara."
    )


def test_el_workflow_llama_al_script() -> None:
    texto = WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/run_validation_gate.py" in texto, (
        "el workflow ha dejado de llamar a la puerta: CI no estaria "
        "corriendo NINGUNA guardia"
    )


def test_la_lista_esta_en_el_script_y_no_esta_vacia() -> None:
    gate = _gate()

    assert isinstance(gate.TESTS, list)
    assert len(gate.TESTS) >= 60, (
        f"la lista tiene {len(gate.TESTS)} guardias: se ha perdido "
        f"la mitad por el camino"
    )
    assert len(gate.TESTS) == len(set(gate.TESTS)), (
        "hay guardias repetidas en la lista"
    )


def test_todas_las_guardias_de_la_lista_existen() -> None:
    """
    Un modulo mal escrito en la lista falla al ejecutarse y para
    la puerta, pero mejor decirlo aqui y con el nombre delante.
    """

    faltan = [
        modulo
        for modulo in _gate().TESTS
        if not Path(modulo.replace(".", "/") + ".py").exists()
    ]

    assert not faltan, f"guardias que no existen en disco: {faltan}"


def test_las_guardias_de_esta_noche_estan_dentro() -> None:
    """
    La prueba de que el cambio no ha dejado nada fuera: lo ultimo
    que se añadio tiene que estar.
    """

    lista = _gate().TESTS

    for modulo in (
        "src.analysis.test_ojeador_fuentes_v1",
        "src.analysis.test_ojeador_emparejamiento_v1",
        "src.analysis.test_ojeador_informe_v1",
        "src.analysis.test_divergencia_v1",
        "src.analysis.test_puerta_una_sola_lista_v1",
    ):
        assert modulo in lista, f"falta {modulo} en la puerta"


# ============================================================
# 2. Y QUE LA PUERTA SEPA DECIR QUE NO
# ============================================================


def test_la_puerta_devuelve_cero_solo_si_pasa_todo() -> None:
    """
    LA COMPROBACION QUE PEDIA EL ENCARGO.

    Si el script diera 0 pase lo que pase, el workflow saldria
    verde con guardias rotas y el remedio seria peor que la
    enfermedad. Se comprueba de verdad: se le manda una guardia
    que falla y se mira el codigo de salida.
    """

    # Con `--solo` se corre UNA guardia rota y nada mas: la
    # comprobacion tarda un segundo en vez de las 68.
    proceso = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--solo",
            "src.analysis._guardia_que_no_existe_",
        ],
        capture_output=True,
        text=True,
    )

    assert proceso.returncode != 0, (
        "la puerta ha dado verde con una guardia rota: CI dejaria "
        "pasar codigo roto"
    )

    # Y la otra cara: con una que pasa, tiene que dar 0. Un script
    # que devolviera != 0 siempre tampoco serviria.
    bueno = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--solo",
            "src.analysis.test_divergencia_v1",
        ],
        capture_output=True,
        text=True,
    )

    assert bueno.returncode == 0, (
        f"la puerta falla con una guardia que pasa: {bueno.stdout[-300:]}"
    )


def test_una_lista_vacia_no_es_un_exito() -> None:
    """
    Decir "todo bien" por no haber mirado nada es exactamente el
    fallo que este cambio viene a cerrar.
    """

    fuente = SCRIPT.read_text(encoding="utf-8")

    assert "no es un exito" in fuente, (
        "la puerta ya no distingue entre «pasaron todas» y «no "
        "habia ninguna»"
    )


def test_la_puerta_no_lee_el_workflow() -> None:
    """
    Si volviera a leerlo, volveriamos a tener la lista en el sitio
    equivocado.

    Se mira el CODIGO, no el texto: el docstring del script
    cuenta esta historia y nombra el fichero a proposito. Buscar
    la cadena a pelo daba un falso positivo sobre su propia
    documentacion.
    """

    import ast

    arbol = ast.parse(SCRIPT.read_text(encoding="utf-8"))

    # Los docstrings, fuera: son documentacion, no lecturas.
    docstrings = set()

    for nodo in ast.walk(arbol):
        if isinstance(
            nodo,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                docstrings.add(texto)

    literales = [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value not in docstrings
    ]

    culpables = [c for c in literales if ".yml" in c or ".yaml" in c]

    assert not culpables, (
        f"la puerta ha vuelto a sacar la lista del workflow: "
        f"{culpables}"
    )

    assert getattr(_gate(), "WORKFLOW", "algo") is None, (
        "el script ha vuelto a apuntar a un fichero de workflow"
    )


TESTS = [
    test_el_workflow_ya_no_lleva_la_lista_a_mano,
    test_el_workflow_llama_al_script,
    test_la_lista_esta_en_el_script_y_no_esta_vacia,
    test_todas_las_guardias_de_la_lista_existen,
    test_las_guardias_de_esta_noche_estan_dentro,
    test_la_puerta_devuelve_cero_solo_si_pasa_todo,
    test_una_lista_vacia_no_es_un_exito,
    test_la_puerta_no_lee_el_workflow,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"PUERTA UNA SOLA LISTA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
