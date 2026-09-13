"""
Los rivales: los puestos se cuentan, no se escriben.

SINTOMA (13/09/2026, noche)

    El dueño escribio en la primera version de la previa que
    eramos PRIMEROS en puntos por millon. Eramos segundos: por
    encima esta Alvaro Retamosa con 3,94 frente a nuestros 3,38.

    Lo vio el mismo al releerlo. Pero un numero de posicion
    escrito a mano solo se caza si alguien vuelve a mirarlo, y
    nadie vuelve a mirar un numero que ya esta puesto.

CONSECUENCIA

    "Somos los que mejor rentabilizamos el dinero" es una frase
    que cambia lo que se hace: justifica seguir igual. Si es
    falsa, justifica seguir igual estando peor que otro.

Y EL RATIO SE LEE CON EL TAMAÑO DE PLANTILLA AL LADO

    Los 3,94 de Alvaro Retamosa salen de nueve fichas y 24,9 M.
    No es mejor gestion: es que ha liquidado casi todo. Sin las
    fichas delante, ese numero dice lo contrario de lo que pasa.

REGLA 23

    No lee estado externo: clasificacion y censo se construyen
    aqui.
"""

from __future__ import annotations

import ast
from pathlib import Path


RAIZ = Path(__file__).parents[2]


# LA FOTO REAL DEL 13/09, con los ocho.
CLASIFICACION = [
    {"rank": 1, "user_id": 14145555, "name": "Pollo17",
     "points": 198, "balance": -4357228,
     "roster_value": 82980000, "net_worth": 78622772,
     "is_us": False},

    {"rank": 2, "user_id": 14175949, "name": "Pepe Bordalás",
     "points": 186, "balance": -1299834,
     "roster_value": 55020000, "net_worth": 53720166,
     "is_us": True},

    {"rank": 3, "user_id": 14156489, "name": "Luismi_Haz",
     "points": 180, "balance": -5384607,
     "roster_value": 80790000, "net_worth": 75405393,
     "is_us": False},

    {"rank": 7, "user_id": 14456960,
     "name": "Alvaro Retamosa Sanguino", "points": 98,
     "balance": 0, "roster_value": 24850000,
     "net_worth": 24850000, "is_us": False},
]

PLANTILLAS = {
    "equipos": [
        {"nombre": "Pepe Bordalás", "user_id": 14175949,
         "es_nuestra": True, "jugadores": 17},
        {"nombre": "Pollo17", "user_id": 14145555,
         "es_nuestra": False, "jugadores": 19},
        {"nombre": "Luismi_Haz", "user_id": 14156489,
         "es_nuestra": False, "jugadores": 16},
        {"nombre": "Alvaro Retamosa Sanguino",
         "user_id": 14456960, "es_nuestra": False,
         "jugadores": 9},
    ]
}


def _rivales(**cambios):
    from src.analysis.los_rivales import los_rivales

    argumentos = {
        "clasificacion": CLASIFICACION,
        "plantillas": PLANTILLAS,
    }

    argumentos.update(cambios)

    return los_rivales(**argumentos)


def _por_nombre(visto, nombre):
    for m in visto["managers"]:
        if m["name"] == nombre:
            return m

    raise AssertionError(f"no esta {nombre}")


def test_los_puestos_se_cuentan_y_no_se_escriben() -> None:
    """
    NUESTRO PUESTO SALE DE ORDENAR Y BUSCARSE.

    Con la foto del 13/09 somos segundos en las tres cosas. Y el
    mejor por millon NO somos nosotros: es Alvaro Retamosa.
    """

    visto = _rivales()

    assert visto["available"] is True, visto

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(visto["managers"]) == len(CLASIFICACION), visto

    lectura = visto["lectura"]

    assert lectura["available"] is True, lectura

    assert lectura["total"] == 4, lectura

    # 1. SEGUNDOS EN PUNTOS: 198 > 186.
    assert lectura["por_puntos"] == 2, lectura

    # 2. SEGUNDOS EN PLANTILLA: 19 > 17.
    assert lectura["por_plantilla"] == 2, lectura

    # 3. Y SEGUNDOS EN PUNTOS POR MILLON. Este es el que fallo.
    assert lectura["por_millon"] == 2, lectura

    mejor = lectura["mejor_por_millon"]

    assert mejor["name"] == "Alvaro Retamosa Sanguino", mejor

    assert mejor["es_nuestro"] is False, mejor

    assert mejor["fichas"] == 9, mejor

    # 4. LA CUENTA: 186 / 55,02 = 3,38 · 98 / 24,85 = 3,94
    assert _por_nombre(visto, "Pepe Bordalás")[
        "puntos_por_millon"
    ] == 3.38

    assert mejor["puntos_por_millon"] == 3.94, mejor

    # 5. CAMBIA LA FOTO, CAMBIA EL PUESTO.
    #
    #    Es la prueba de que se cuenta. Si a nosotros nos
    #    duplicaran el valor de plantilla, caeriamos.
    peor = _rivales(
        clasificacion=[
            {**r, "roster_value": r["roster_value"] * 4}
            if r["is_us"]
            else r
            for r in CLASIFICACION
        ]
    )

    assert peor["lectura"]["por_millon"] == 4, peor["lectura"]

    assert peor["lectura"]["por_puntos"] == 2, peor["lectura"]

    # 6. NI UN NUMERO DE POSICION ESCRITO EN EL MODULO.
    fuente = (
        RAIZ / "src" / "analysis" / "los_rivales.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    lectura_fn = next(
        n
        for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef)
        and n.name == "_la_lectura"
    )

    cuerpo = lectura_fn.body[1:]

    for nodo in ast.walk(
        ast.Module(body=cuerpo, type_ignores=[])
    ):
        if (
            isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, int)
            and not isinstance(nodo.value, bool)
        ):
            assert nodo.value == 0, (
                f"hay un numero puesto a mano en la lectura: "
                f"{nodo.value}"
            )


def test_el_ratio_no_se_publica_sin_la_plantilla() -> None:
    """
    UN RATIO ALTO CON PLANTILLA MINIMA NO ES EFICIENCIA.

    Los 3,94 de Alvaro Retamosa salen de nueve fichas. El cuadro
    tiene que publicar las fichas al lado o el numero dice lo
    contrario de lo que pasa.

    Y SIN VALOR DE PLANTILLA NO SE DIVIDE: un denominador cero
    daria infinito, que se pintaria como el mejor de la tabla.
    """

    visto = _rivales()

    for m in visto["managers"]:
        assert m["fichas"] is not None, m

        assert m["puntos_por_millon"] is not None, m

    # 1. SIN VALOR, EL RATIO ES `None` Y NO INFINITO.
    sin_valor = _rivales(
        clasificacion=[
            {**r, "roster_value": 0} for r in CLASIFICACION
        ]
    )

    for m in sin_valor["managers"]:
        assert m["puntos_por_millon"] is None, m

    assert sin_valor["lectura"]["por_millon"] is None, (
        sin_valor["lectura"]
    )

    assert sin_valor["lectura"]["mejor_por_millon"] is None

    # 2. SIN CENSO, LAS FICHAS SON `None` Y NO CERO.
    #
    #    Cero fichas es un manager que ha vendido todo; "no se
    #    sabe" es que no se pudo cruzar. Pintarlos igual haria
    #    que el segundo pareciera el primero.
    sin_censo = _rivales(plantillas={})

    for m in sin_censo["managers"]:
        assert m["fichas"] is None, m

    assert len(sin_censo["sin_plantilla"]) == len(
        CLASIFICACION
    ), sin_censo["sin_plantilla"]

    assert "sin plantilla cruzada" in sin_censo["reason"], (
        sin_censo["reason"]
    )

    # 3. LA PANTALLA ENSEÑA LAS FICHAS AL LADO DEL RATIO.
    panel = (
        RAIZ
        / "dashboard-v8"
        / "src"
        / "components"
        / "LosRivalesPanel.jsx"
    ).read_text(encoding="utf-8")

    assert "FICHAS" in panel, (
        "la pantalla no enseña el tamaño de plantilla: el ratio "
        "se leeria como eficiencia"
    )

    assert "m.fichas" in panel, panel[:0]

    assert "lectura.por_millon" in panel, (
        "la pantalla no enseña el puesto contado"
    )


def test_el_cruce_es_por_id_y_no_por_nombre() -> None:
    """
    UN MANAGER QUE SE CAMBIE EL NOMBRE NO PUEDE PERDER SU
    PLANTILLA.

    Y sin plantilla no hay puntos por millon: su fila se quedaria
    sin el unico numero que explica la tabla.
    """

    # Con los nombres cambiados en el censo, el cruce aguanta.
    otro_nombre = {
        "equipos": [
            {**e, "nombre": f"{e['nombre']} (renombrado)"}
            for e in PLANTILLAS["equipos"]
        ]
    }

    visto = _rivales(plantillas=otro_nombre)

    assert visto["sin_plantilla"] == [], visto["sin_plantilla"]

    assert _por_nombre(visto, "Pollo17")["fichas"] == 19

    # Y CON LOS IDS CAMBIADOS, SE ROMPE Y SE DICE.
    sin_id = {
        "equipos": [
            {**e, "user_id": None, "es_nuestra": False}
            for e in PLANTILLAS["equipos"]
        ]
    }

    roto = _rivales(plantillas=sin_id)

    assert len(roto["sin_plantilla"]) == 4, roto["sin_plantilla"]

    # NO SE DEDUCE POR NOMBRE COMO RESPALDO. Un respaldo que
    # adivina esconde justo el fallo que hay que ver.
    fuente = (
        RAIZ / "src" / "analysis" / "los_rivales.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    funcion = next(
        n
        for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef)
        and n.name == "los_rivales"
    )

    codigo = ast.dump(
        ast.Module(body=funcion.body[1:], type_ignores=[])
    )

    assert "'nombre'" not in codigo, (
        "el cruce vuelve a mirar el nombre: un manager que se lo "
        "cambie perderia su plantilla en silencio"
    )


def test_este_cuadro_no_decide_nada() -> None:
    """Es para mirar. Nada sale de aqui."""

    fuente = (
        RAIZ / "src" / "analysis" / "los_rivales.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    llamadas = {
        n.func.id
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    } | {
        n.func.attr
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
    }

    for escribe in (
        "place_bid",
        "accept_offer",
        "list_player_for_sale",
        "open",
        "abrir",
    ):
        assert escribe not in llamadas, (
            f"los rivales llaman a `{escribe}`"
        )

    pagina = (
        RAIZ / "dashboard-v8" / "src" / "pages" / "BrainPage.jsx"
    ).read_text(encoding="utf-8")

    assert "<LosRivalesPanel" in pagina, (
        "el cuadro de rivales no esta montado"
    )


TESTS = [
    test_los_puestos_se_cuentan_y_no_se_escriben,
    test_el_ratio_no_se_publica_sin_la_plantilla,
    test_el_cruce_es_por_id_y_no_por_nombre,
    test_este_cuadro_no_decide_nada,
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
        f"LOS RIVALES V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
