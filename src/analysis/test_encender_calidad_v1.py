"""
ENCENDER LA CALIDAD, Y LA OFERTA VIVA POR YAMAL.

TRES COSAS QUE SE ENCIENDEN O SE CIERRAN ESTA NOCHE

    1. La oferta del Computer de 21.099.500 EUR por Yamal, con la
       lista de intocables ya retirada. Es el primer dia en que
       un jugador de 21 millones depende de una cuenta y no de
       una lista de nombres.

    2. La calidad medida (regla 6), encendida: 19,1 % -> 23,5 %
       de varianza explicada, medido sin circularidad.

    3. "Un dato, un nombre": la hermana de la regla de la forma
       estable, despues de cuatro incidentes de la misma familia.

    Todo con fixture. Ni una lectura de `data/`.
"""

from __future__ import annotations

import os

from pathlib import Path

from src.analysis.calidad_medida import (
    DISABLE_ENV,
    REFERENCIA_PUNTOS_PARTIDO,
    calidad_activa,
    calidad_para_la_vara,
    vara_de_etiqueta,
)
from src.analysis.lineup_engine import weekly_expected_value
from src.analysis.soltar_un_grande import (
    MARGEN_NETO,
    evaluar_venta,
    mejor_cesta,
)
from src.analysis.un_dato_un_nombre import (
    CONCEPTOS,
    inventario,
    leer,
)
from src.analysis.vara_comparada import VARAS, elegir_once


# La oferta que estaba viva el 22/09/2026, leida de la API.
OFERTA_POR_YAMAL = 21_099_500


def _plantilla() -> list:
    """
    La nuestra del 22/09, con los numeros que importan: Yamal al
    42,81 % del valor y 9,33 puntos por jornada.
    """

    plantilla = [
        {
            "id": 17482, "name": "Dituro", "position": 1,
            "price": 2_650_000, "points": 2, "is_starter": True,
            "hierarchy_value": 40, "starter_probability": 80.0,
        },
        {
            "id": 26271, "name": "Yamal", "position": 4,
            "price": 21_210_000, "points": 28, "is_starter": True,
            "hierarchy_value": 60, "starter_probability": 100.0,
        },
    ]

    # Los porcentajes son los de verdad, y son los que hacian
    # ganar al 5-4-1 con la vara base: los defensas juegan mas
    # seguro que los delanteros, y la etiqueta no sabia que los
    # delanteros puntuan mas cuando juegan.
    otros = [
        ("Olasagasti", 3, 2_920_000, 21, True, 90.0),
        ("Exposito", 3, 5_160_000, 16, True, 90.0),
        ("Jonny Castro", 2, 2_320_000, 12, True, 80.0),
        ("Mangala", 3, 2_630_000, 11, True, 90.0),
        ("Jutgla", 4, 3_350_000, 11, True, 40.0),
        ("Pablo Ibanez", 3, 2_060_000, 10, True, 90.0),
        ("Zubeldia", 2, 1_710_000, 9, False, 70.0),
        ("Pablo Duran", 4, 380_000, 8, True, 70.0),
        ("Manu Sanchez", 2, 1_480_000, 6, True, 80.0),
        ("Djene", 2, 2_010_000, 5, True, 90.0),
        ("Lucas Cepeda", 4, 480_000, 8, False, 40.0),
        ("Kiko Femenia", 2, 1_180_000, 0, False, 70.0),
    ]

    for i, (nombre, pos, precio, puntos, titular, prob) in (
        enumerate(otros)
    ):
        plantilla.append({
            "id": 100 + i,
            "name": nombre,
            "position": pos,
            "price": precio,
            "points": puntos,
            "is_starter": titular,
            "hierarchy_value": 40,
            "starter_probability": prob,
        })

    return plantilla


def _mercado() -> list:
    """El escaparate del 22/09, con su proyeccion por jornada."""

    return [
        {"name": "Pedri", "price": 15_350_000,
         "projected_per_matchday": 5.79},
        {"name": "Amatucci", "price": 3_670_000,
         "projected_per_matchday": 4.24},
        {"name": "Gabriel Suazo", "price": 1_730_000,
         "projected_per_matchday": 2.21},
        {"name": "Javi Morcillo", "price": 250_000,
         "projected_per_matchday": 0.26},
        {"name": "Szczesny", "price": 270_000,
         "projected_per_matchday": 0.24},
    ]


# ============================================================
# 1. LA OFERTA VIVA POR YAMAL
# ============================================================


def test_con_la_oferta_de_21_millones_no_se_vende() -> None:
    """
    EL CASO, CON SU CIFRA DENTRO

        El Computer ofrece 21.099.500 EUR por Yamal. La lista de
        intocables esta retirada: lo unico que decide es la
        cuenta.

        Ni siquiera la MEJOR cesta que cabe con ese dinero llega
        al margen. Si algun dia esta prueba se pone roja, no es
        que sobre: es que el mercado ha cambiado y hay que
        mirarlo con las dos manos.
    """

    plantilla = _plantilla()

    yamal = next(p for p in plantilla if p["name"] == "Yamal")

    disponible = OFERTA_POR_YAMAL + 258_807

    cesta = mejor_cesta(
        yamal, plantilla, _mercado(), 3, disponible
    )

    salida = evaluar_venta(yamal, plantilla, cesta, 3)

    assert salida["is_big"] is True
    assert salida["can_sell"] is False, (
        f"con la oferta de {OFERTA_POR_YAMAL:,} sobre la mesa la "
        f"cuenta dice VENDER con neto "
        f"{salida['net_points_per_matchday']:+.2f}"
    )
    assert salida["net_points_per_matchday"] < MARGEN_NETO


def test_ninguna_lista_protege_ya_a_yamal() -> None:
    """
    Si volviera a protegerle una lista, esta prueba dejaria de
    medir lo que dice medir.
    """

    from src.analysis.sale_intent import untouchable_reason

    yamal = next(
        p for p in _plantilla() if p["name"] == "Yamal"
    )

    assert untouchable_reason(yamal) is None, (
        "Yamal vuelve a estar protegido por una lista: entonces "
        "la cuenta no es lo que decide"
    )


def test_se_le_da_a_vender_la_mejor_cesta_posible() -> None:
    """
    Elegir una cesta mala seria hacerle trampas a la opcion de
    vender. Con la oferta de Yamal, la mejor de todas las
    combinaciones da -0,76 y la de cinco -6,26: el veredicto es
    el mismo, pero solo el primero es un argumento honesto.
    """

    plantilla = _plantilla()

    yamal = next(p for p in plantilla if p["name"] == "Yamal")

    disponible = OFERTA_POR_YAMAL + 258_807

    mejor = mejor_cesta(
        yamal, plantilla, _mercado(), 3, disponible
    )

    neto_mejor = evaluar_venta(
        yamal, plantilla, mejor, 3
    )["net_points_per_matchday"]

    todas = evaluar_venta(
        yamal, plantilla, _mercado(), 3
    )["net_points_per_matchday"]

    assert neto_mejor >= todas, (
        "la busqueda de la mejor cesta devuelve algo peor que "
        "coger las cinco primeras"
    )


# ============================================================
# 2. LA CALIDAD MEDIDA, ENCENDIDA
# ============================================================


def test_la_calidad_medida_esta_encendida() -> None:
    assert calidad_activa() is True

    motor = Path(
        "src/analysis/lineup_engine.py"
    ).read_text(encoding="utf-8")

    assert "calidad_para_la_vara" in motor, (
        "el motor ha dejado de usar la calidad medida"
    )


def test_una_linea_devuelve_la_escalera_de_siempre() -> None:
    """
    "Un interruptor de una linea, escrito entero en el informe."
    """

    antes = os.environ.get(DISABLE_ENV)

    try:
        os.environ[DISABLE_ENV] = "1"

        assert calidad_activa() is False
        assert calidad_para_la_vara(
            {"played_home": 3, "played_away": 0, "points": 18}
        ) is None

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes

    assert calidad_activa() is True


def test_el_contrafactual_no_toca_el_entorno() -> None:
    assert calidad_activa() is True

    with vara_de_etiqueta():
        assert calidad_activa() is False

    assert calidad_activa() is True


def test_sin_partidos_manda_la_etiqueta() -> None:
    """
    La etiqueta no se tira: se degrada a suplente.
    """

    recien = {
        "played_home": 0,
        "played_away": 0,
        "points": 0,
        "hierarchy_value": 50,
    }

    assert calidad_para_la_vara(recien) is None

    # Y la vara sin calidad es EXACTAMENTE la de siempre.
    assert weekly_expected_value(50, 80.0, quality=None) == (
        weekly_expected_value(50, 80.0)
    )


def test_la_calidad_entra_en_la_escala_de_la_vara() -> None:
    """
    La escalera va de 0,25 a 1,00 y los puntos por partido de 0 a
    13. Sin traducir, la ordenacion reventaria.
    """

    en_la_referencia = {
        "played_home": 2,
        "played_away": 0,
        "points": int(2 * REFERENCIA_PUNTOS_PARTIDO),
        "points_last_season": int(
            38 * REFERENCIA_PUNTOS_PARTIDO
        ),
        "hierarchy_value": 40,
    }

    nota = calidad_para_la_vara(en_la_referencia)

    assert nota is not None
    assert abs(nota - 1.0) < 0.05, (
        f"un jugador en la referencia deberia valer ~1,0 y vale "
        f"{nota}"
    )


def test_el_techo_no_se_recorta() -> None:
    """
    Un jugador que puntua el doble que un p95 es el doble de
    bueno. La escalera vieja no podia decirlo: su techo era Dios.
    """

    crack = {
        "played_home": 3,
        "played_away": 0,
        "points": int(3 * 2 * REFERENCIA_PUNTOS_PARTIDO),
        "points_last_season": int(
            38 * 2 * REFERENCIA_PUNTOS_PARTIDO
        ),
        "hierarchy_value": 40,
    }

    assert calidad_para_la_vara(crack) > 1.0


# ============================================================
# 3. EL MARCADOR SEPARA LOS DOS EFECTOS
# ============================================================


def test_hay_tres_varas_y_no_dos() -> None:
    """
    EL RIESGO QUE ESTO CUBRE

        El 18/09 se encendieron los factores de posicion; el
        22/09, la calidad. Con solo "antes" y "ahora" el marcador
        diria si el conjunto suma, pero no cual de los dos lo
        hace.
    """

    assert set(VARAS) == {"base", "factores", "actual"}

    plantilla = _plantilla()

    onces = {
        nombre: elegir_once(plantilla, vara=nombre)
        for nombre in VARAS
    }

    for nombre, once in onces.items():
        assert once["available"], nombre
        assert once["vara"] == nombre
        assert len(once["players"]) == 11

    # La base es la de antes de los factores: mas defensas.
    assert (
        onces["base"]["by_position"]["Defensa"]
        > onces["actual"]["by_position"]["Defensa"]
    ), (
        "la vara base ya no alinea mas defensas que la actual: "
        "entonces no es la de antes de los factores"
    )


def test_las_tres_varas_son_de_verdad_distintas() -> None:
    """
    Si dos de las tres dieran siempre lo mismo, el marcador no
    podria separar nada.
    """

    ficha = {
        "hierarchy_value": 40,
        "starter_probability": 80.0,
        "position": 4,
        "played_home": 3,
        "played_away": 0,
        "points": 30,
        "points_last_season": 200,
    }

    from src.analysis.vara_comparada import _vara

    valores = {
        nombre: _vara(ficha, nombre) for nombre in VARAS
    }

    assert valores["base"] != valores["factores"], (
        "los factores de posicion no cambian nada"
    )
    assert valores["factores"] != valores["actual"], (
        "la calidad medida no cambia nada sobre los factores"
    )


# ============================================================
# 4. UN DATO, UN NOMBRE
# ============================================================


def test_los_conceptos_unificados_entienden_sus_dos_nombres() -> None:
    """
    No se comprueban nombres: se comprueba COMPORTAMIENTO. Una
    ficha con el alias tiene que dar la misma respuesta que una
    con el nombre canonico.
    """

    from src.analysis.calidad_medida import partidos_jugados
    from src.analysis.sale_intent import untouchable_reason

    # Concepto "es titular" — el incidente del 12/09.
    for campo in ("is_starter", "in_lineup"):

        portero = {
            "position": 1,
            "hierarchy_value": 40,
            campo: True,
        }

        assert untouchable_reason(portero) is not None, (
            f"con `{campo}` el portero titular deja de estar "
            f"protegido"
        )

    # Concepto "partidos jugados" — el incidente del 22/09.
    biwenger = {"playedHome": 2, "playedAway": 1}
    tablero = {"played_home": 2, "played_away": 1}

    assert partidos_jugados(biwenger) == partidos_jugados(
        tablero
    ) == 3

    assert leer(biwenger, "partidos_jugados") == 3
    assert leer(tablero, "partidos_jugados") == 3


def test_la_plantilla_publicada_lleva_los_partidos() -> None:
    """
    EL INCIDENTE DEL 22/09

        El motor calculaba la calidad medida con los partidos que
        vienen en `my_team`, y la plantilla publicada no los
        llevaba: quien leia el tablero no podia reproducir el
        mismo once.
    """

    generador = Path(
        "src/telemetry/dashboard_state.py"
    ).read_text(encoding="utf-8")

    for campo in (
        '"played_home"',
        '"played_away"',
        '"points_last_season"',
    ):
        assert campo in generador, (
            f"la plantilla publicada ha dejado de llevar {campo}: "
            f"el tablero no puede reproducir el once del motor"
        )


def test_el_inventario_dice_que_queda_abierto() -> None:
    datos = inventario()

    assert datos["available"]
    assert datos["unified"] >= 2
    assert datos["pending"] >= 1

    for fila in datos["rows"]:

        assert fila["what"], f"{fila['concept']} sin explicar"

        if fila["unified"]:
            assert fila["incident"], (
                f"{fila['concept']} esta unificado y no dice que "
                f"incidente lo justifico"
            )


def test_lo_que_costo_un_incidente_esta_unificado() -> None:
    """
    "Unifica los que ya han causado un incidente. Los demas, en
     la lista."
    """

    for clave, registro in CONCEPTOS.items():

        if registro["incident"]:
            assert registro["unified"], (
                f"{clave} costo un incidente el "
                f"{registro['incident']} y sigue sin unificar"
            )


# ============================================================
# 5. NI DECIDE NI CAMBIA DE FORMA
# ============================================================


def test_la_forma_no_cambia_con_los_datos() -> None:
    plantilla = _plantilla()

    casos = [
        (
            "un_dato_un_nombre.inventario",
            inventario(),
            inventario(),
        ),
        (
            "vara_comparada.elegir_once",
            elegir_once(plantilla, vara="actual"),
            elegir_once([], vara="actual"),
        ),
        (
            "soltar_un_grande.evaluar_venta",
            evaluar_venta(plantilla[1], plantilla, [], 3),
            evaluar_venta(None, None, None, 0),
        ),
    ]

    for nombre, lleno, vacio in casos:
        assert set(lleno) == set(vacio), (
            f"{nombre} cambia de forma: "
            f"faltan {sorted(set(lleno) - set(vacio))}, "
            f"sobran {sorted(set(vacio) - set(lleno))}"
        )


def test_nada_de_esto_vende_ni_lanza() -> None:
    import ast

    for ruta in (
        "src/analysis/un_dato_un_nombre.py",
        "src/analysis/soltar_un_grande.py",
        "src/analysis/calidad_medida.py",
    ):
        arbol = ast.parse(
            Path(ruta).read_text(encoding="utf-8")
        )

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
                continue

            for prohibido in (
                "write_client",
                "BiwengerWriteClient",
                "autopilot_executor",
            ):
                assert prohibido not in ast.dump(nodo), (
                    f"{ruta} importa `{prohibido}`"
                )

    for basura in (None, {}, [], "x"):
        assert leer(basura, "es_titular") is None
        assert isinstance(
            elegir_once(basura, vara="actual"), dict
        )
        assert isinstance(
            mejor_cesta(basura, basura, basura, 0, 0), list
        )


def test_estas_guardias_no_leen_el_estado() -> None:
    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    for modulo in (
        "src.analysis.test_encender_calidad_v1",
        "src.analysis.un_dato_un_nombre",
    ):
        assert not lecturas_de_estado(modulo)


TESTS = [
    test_con_la_oferta_de_21_millones_no_se_vende,
    test_ninguna_lista_protege_ya_a_yamal,
    test_se_le_da_a_vender_la_mejor_cesta_posible,
    test_la_calidad_medida_esta_encendida,
    test_una_linea_devuelve_la_escalera_de_siempre,
    test_el_contrafactual_no_toca_el_entorno,
    test_sin_partidos_manda_la_etiqueta,
    test_la_calidad_entra_en_la_escala_de_la_vara,
    test_el_techo_no_se_recorta,
    test_hay_tres_varas_y_no_dos,
    test_las_tres_varas_son_de_verdad_distintas,
    test_los_conceptos_unificados_entienden_sus_dos_nombres,
    test_la_plantilla_publicada_lleva_los_partidos,
    test_el_inventario_dice_que_queda_abierto,
    test_lo_que_costo_un_incidente_esta_unificado,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_vende_ni_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("ENCENDER LA CALIDAD V1")
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
