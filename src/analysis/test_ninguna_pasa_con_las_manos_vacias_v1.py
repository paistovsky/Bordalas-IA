"""
Ninguna guardia devuelve verde sin haber mirado nada.

SINTOMA (20/09/2026)

    `test_orden_de_venta_v1` tenia OCHO pruebas que empezaban
    asi:

        cola = _cola_de_produccion()

        if cola is None:
            return

    En el portatil leian `diagnostico/status.json` y cambiaban de
    color con el mercado. En CI, donde esa carpeta no existe,
    SALIAN SIN AFIRMAR NADA y contaban como verdes.

    Las dos mitades de la doctrina 91 a la vez: un rojo que no
    significa un fallo y un verde que no significa nada.

LA REGLA DE LA CASA YA LO DECIA

    "Ninguna guardia pasa con las manos vacias" lleva semanas
    escrita, y la verja ya vigila dos formas de incumplirla:

        · el modulo MUDO, que se importa y no ejecuta nada
          (`run_validation_gate`, 14/09)
        · la guardia que abre el estado al correrse
          (`vigila_data/sitecustomize.py`, 13/09)

    Faltaba la tercera: la prueba que SE EJECUTA, imprime OK y se
    va sin afirmar nada.

POR QUE ES UN CENSO Y NO UN CORTE

    Medido hoy sobre las 1.925 pruebas `test_*` de `src/**`:

        210 (10,9 %) pueden terminar sin ejecutar un solo
        `assert`, repartidas en 85 ficheros.

    La inmensa mayoria son legitimas: delegan sus afirmaciones en
    un ayudante, o comprueban que algo NO lanza. Distinguirlas a
    maquina pide seguir las llamadas, y eso es otra guardia.

    Lo que SI se puede cercar sin falsos positivos es la forma
    exacta que fallo: una prueba de un fichero que lee el estado
    y que sale por la puerta de atras cuando el estado no esta.
    De esas quedan TRECE, y estan censadas abajo una a una.

    El censo SOLO PUEDE ENCOGER. Cualquiera que no este en la
    lista pone esta guardia en rojo con su nombre — que es lo que
    evita la proxima.

LO QUE COSTARIA BAJARLO A CERO

    `test_futbolfantasy_source_v12`  7   lee el HTML del proveedor y las fotos
    `test_mercado_rivales_v1`        2   lee las fotos
    `test_doctrina_v1`               1
    `test_el_ciclo_publica_v1`       1   comprueba si hay fotos
    `test_la_pantalla_pinta_v1`      1   ya esta retirada de la verja
    `test_verja_determinista_v1`     1   es el vigilante, y es legitimo

    Siete de las trece son un solo fichero, y la salida es la
    misma que se uso hoy con las otras ocho: un mirador.

REGLA 23

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj:
    solo el codigo del repositorio, con `ast`. Y si el barrido no
    encuentra ni una prueba, FALLA: una guardia que no mira nada
    es exactamente lo que vino a prohibir.
"""

from __future__ import annotations

import ast
import re

from pathlib import Path


RAIZ = Path(__file__).parents[2]


# Un fichero que toca el estado de produccion, de una forma o de
# otra. Solo en esos tiene sentido buscar la salida de atras.
TOCA_EL_ESTADO = re.compile(
    r"(dat" + r"a|diagnostic" + r"o)[/\"']"
    r"|get_latest_snapshot"
    r"|_produccion\("
)


# ============================================================
# EL CENSO, UNA A UNA Y CON SU MOTIVO (20/09/2026)
# ============================================================
#
#     Clave: `fichero::prueba`. El motivo no es decoracion: una
#     lista de excepciones sin motivos es donde se esconde el
#     fallo de mañana.
CENSADAS_EL = "2026-09-20"

PUEDEN_SALIR_SIN_AFIRMAR = {
    "test_futbolfantasy_source_v12::test_parser_sobre_html_real":
        "sin el HTML guardado del proveedor no hay nada que parsear",
    "test_futbolfantasy_source_v12::test_identidad_por_equipo":
        "sin HTML guardado no hay equipos que emparejar",
    "test_futbolfantasy_source_v12::test_partes_de_baja":
        "sin HTML guardado no hay partes",
    "test_futbolfantasy_source_v12::test_la_cache_comprueba_a_quien_cubre":
        "sin fotos no se sabe a quien cubre la cache",
    "test_futbolfantasy_source_v12::test_a_quien_se_vende":
        "necesita una foto con mercado",
    "test_futbolfantasy_source_v12::test_intencion_de_venta_solo_observa":
        "necesita una foto con mercado",
    "test_futbolfantasy_source_v12::test_el_once_usa_la_fuente_unica":
        "necesita una foto con once",
    "test_mercado_rivales_v1::test_la_forma_no_cambia_con_los_datos":
        "compara dos fotos y sin ellas no hay dos formas",
    "test_mercado_rivales_v1::test_la_pantalla_lo_canta":
        "pinta sobre una foto de mercado",
    "test_doctrina_v1::test_ninguna_cita_apunta_a_una_regla_que_no_existe":
        "sin decisiones guardadas no hay citas que comprobar",
    "test_el_ciclo_publica_v1::test_el_estado_del_dashboard_se_construye_entero":
        "sin ninguna foto en disco no se puede construir el estado",
    "test_la_pantalla_pinta_v1::test_la_pantalla_se_monta_y_pinta":
        "ya esta RETIRADA de la verja; ver `RETIRADAS`",
    "test_verja_determinista_v1::test_los_vigilados_pasan_con_el_estado_vacio":
        "ES el vigilante: monta un espejo y si la maquina no le "
        "deja, se declara inaplicable a proposito",
}


def _sale_sin_afirmar(funcion: ast.FunctionDef) -> int | None:
    """
    La linea del `return` desnudo dentro de un `if`, o `None`.

    Es la forma exacta que fallo: `if <no hay dato>: return`.
    """

    for nodo in ast.walk(funcion):

        if not isinstance(nodo, ast.If):
            continue

        for hijo in nodo.body:

            if isinstance(hijo, ast.Return) and hijo.value is None:
                return nodo.lineno

    return None


def _barrido() -> dict:
    """{fichero::prueba: linea} de las que pueden irse de vacio."""

    encontradas = {}

    for ruta in sorted(RAIZ.rglob("src/**/test_*.py")):

        if "__pycache__" in ruta.parts:
            continue

        fuente = ruta.read_text(encoding="utf-8", errors="replace")

        if not TOCA_EL_ESTADO.search(fuente):
            continue

        try:
            arbol = ast.parse(fuente)

        except SyntaxError:
            continue

        for nodo in arbol.body:

            if not (
                isinstance(nodo, ast.FunctionDef)
                and nodo.name.startswith("test_")
            ):
                continue

            linea = _sale_sin_afirmar(nodo)

            if linea is not None:
                encontradas[f"{ruta.stem}::{nodo.name}"] = linea

    return encontradas


def _todas_las_pruebas() -> int:
    """Cuantas `test_*` hay en total. Para no pasar de vacio."""

    total = 0

    for ruta in sorted(RAIZ.rglob("src/**/test_*.py")):

        if "__pycache__" in ruta.parts:
            continue

        try:
            arbol = ast.parse(
                ruta.read_text(encoding="utf-8", errors="replace")
            )

        except SyntaxError:
            continue

        total += sum(
            1
            for n in arbol.body
            if isinstance(n, ast.FunctionDef)
            and n.name.startswith("test_")
        )

    return total


# ============================================================
# 1. LA GUARDIA NO PUEDE MIRAR AL VACIO
# ============================================================


def test_el_barrido_encuentra_pruebas() -> None:
    """
    Doctrina 24, aplicada a si misma. Si el barrido devolviera
    cero por un fallo del patron, todo pasaria y nadie se
    enteraria.
    """

    total = _todas_las_pruebas()

    assert total > 1_000, (
        f"el barrido solo ve {total} pruebas en `src/**`: el "
        f"patron se ha roto y esta guardia no esta mirando nada"
    )


# ============================================================
# 2. NINGUNA NUEVA
# ============================================================


def test_ninguna_prueba_nueva_puede_irse_de_vacio() -> None:
    """
    LA QUE EVITA LA PROXIMA.

    Una prueba que lee el estado y sale por la puerta de atras
    cuando el estado no esta devuelve verde sin haber mirado
    nada. Si no esta censada, aqui salta con su nombre.
    """

    encontradas = _barrido()

    nuevas = {
        clave: linea
        for clave, linea in encontradas.items()
        if clave not in PUEDEN_SALIR_SIN_AFIRMAR
    }

    assert not nuevas, (
        "estas pruebas pueden terminar SIN AFIRMAR NADA cuando "
        "el estado no esta, y devolver verde:\n"
        + "\n".join(
            f"    {clave}  (linea {linea})"
            for clave, linea in sorted(nuevas.items())
        )
        + "\n\nO afirman algo siempre, o se van a un mirador "
        "-como las ocho del orden de venta el 20/09-, o se "
        "censan aqui CON SU MOTIVO."
    )


def test_el_censo_solo_puede_encoger() -> None:
    """
    Y las que ya no estan, fuera de la lista: si no, el numero se
    queda viejo y el censo deja de medir nada.
    """

    encontradas = _barrido()

    fantasmas = sorted(
        set(PUEDEN_SALIR_SIN_AFIRMAR) - set(encontradas)
    )

    assert not fantasmas, (
        "estas ya no pueden irse de vacio y siguen censadas: "
        "quitalas de la lista para que el numero baje de verdad\n"
        + "\n".join(f"    {clave}" for clave in fantasmas)
    )

    assert len(PUEDEN_SALIR_SIN_AFIRMAR) <= 13, (
        f"el censo ha crecido a "
        f"{len(PUEDEN_SALIR_SIN_AFIRMAR)}: solo puede encoger"
    )


def test_cada_censada_dice_por_que() -> None:
    """Una lista de excepciones sin motivos es un agujero."""

    for clave, motivo in PUEDEN_SALIR_SIN_AFIRMAR.items():

        assert motivo and len(motivo) > 15, (
            f"{clave} esta censada sin un motivo que explique "
            f"nada: «{motivo}»"
        )


def main() -> int:

    pruebas = [
        test_el_barrido_encuentra_pruebas,
        test_ninguna_prueba_nueva_puede_irse_de_vacio,
        test_el_censo_solo_puede_encoger,
        test_cada_censada_dice_por_que,
    ]

    fallos = 0

    for prueba in pruebas:

        try:
            prueba()
            print(f"OK   {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {prueba.__name__}: {error}")

    print("=" * 60)
    print(
        f"NINGUNA PASA CON LAS MANOS VACIAS V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
