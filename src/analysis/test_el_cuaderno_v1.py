"""
El cuaderno mide la jornada de LaLiga, no el round de Biwenger.

SINTOMA (27/09/2026)

    El marcador: cinco jornadas cerradas, cero cuadran. En la J7
    el once anotado sumo 27 y Biwenger dio 61. Causas medidas en
    el historial de `marcador.json`: el round de Biwenger salto a
    la J8 con la J7 a medio jugar, y los totales solo cubrian la
    plantilla del dia (los vendidos desaparecian de la resta).

LO QUE VIGILAN ESTAS GUARDIAS

    1. Los puntos de una jornada son la resta de DOS fotos de
       jornada cerrada. Con una sola, no hay numero.
    2. Un jugador vendido sigue contando: esta en el catalogo.
    3. Un titular que no jugo se ve (sus partidos no suben).
    4. Un hueco no es un cero: sin foto de un titular, no hay suma.
    5. Sin once congelado no hay nota: no se inventa cual jugo.

REGLA 23

    No leen ni escriben estado de produccion: todos los datos
    estan aqui y entran por la puerta.
"""

from __future__ import annotations


# Los totales de temporada de la J6 y la J7, como los apunta
# `apuntar_la_foto_de_la_jornada`: {id: [puntos, jugados, precio]}.
# 17482 es Dituro: jugo la J7 y despues se vendio. En el catalogo
# sigue estando.
FOTO_J6 = {
    "jornada": 6,
    "players": {
        "17482": [9, 6, 2100000],
        "1599": [15, 6, 2200000],
        "26271": [70, 6, 22000000],
        "3159": [20, 6, 3100000],
    },
}

FOTO_J7 = {
    "jornada": 7,
    "players": {
        "17482": [11, 7, 2110000],
        "1599": [15, 6, 2270000],     # no jugo: jugados no sube
        "26271": [88, 7, 22930000],
        "3159": [29, 7, 3170000],
    },
}

# El once, congelado antes del primer partido. `round_id` es el de
# Biwenger y puede ir retrasado; manda `matchday`.
ONCE_J7 = {
    "round_id": 4905,
    "matchday": 7,
    "formation": "3-5-2",
    "players": [17482, 1599, 26271, 3159],
}


def test_los_puntos_son_la_resta_de_dos_fotos() -> None:

    from src.analysis.el_cuaderno import puntos_de_la_jornada

    medida = puntos_de_la_jornada([FOTO_J6, FOTO_J7], 7)

    assert medida["medible"] is True, medida

    assert medida["puntos"]["26271"] == [18, 1], medida

    # Con una sola foto, la J7 no se puede medir: el total es de
    # la temporada, no de la jornada.
    sola = puntos_de_la_jornada([FOTO_J7], 7)

    assert sola["medible"] is False, sola

    assert sola["puntos"] == {}, sola

    assert "jornada 6" in sola["motivo"], sola


def test_el_vendido_sigue_contando_y_el_que_no_jugo_se_ve() -> None:

    from src.analysis.el_cuaderno import la_nota_del_once

    nota = la_nota_del_once([FOTO_J6, FOTO_J7], [ONCE_J7], 7)

    assert nota["medible"] is True, nota

    # 2 (Dituro, vendido) + 0 + 18 + 9
    assert nota["puntos_once"] == 29, nota

    assert nota["no_jugaron"] == ["1599"], nota

    assert nota["formation"] == "3-5-2", nota


def test_un_hueco_no_es_un_cero() -> None:

    from src.analysis.el_cuaderno import la_nota_del_once

    once = {**ONCE_J7, "players": ONCE_J7["players"] + [99999]}

    nota = la_nota_del_once([FOTO_J6, FOTO_J7], [once], 7)

    assert nota["medible"] is False, nota

    assert nota["puntos_once"] is None, nota

    assert nota["sin_dato"] == ["99999"], nota


def test_sin_once_congelado_no_hay_nota() -> None:

    from src.analysis.el_cuaderno import el_cuaderno

    # El once que hay es de OTRA jornada: no vale para la 7.
    otro = {**ONCE_J7, "matchday": 8}

    cuaderno = el_cuaderno([FOTO_J6, FOTO_J7], [otro])

    assert cuaderno["available"] is True, cuaderno

    assert cuaderno["medibles"] == 0, cuaderno

    notas = {n["jornada"]: n for n in cuaderno["jornadas"]}

    assert notas[7]["medible"] is False, notas

    assert "once" in notas[7]["motivo"], notas

    # Y con el once bueno, la misma jornada si tiene nota.
    bueno = el_cuaderno([FOTO_J6, FOTO_J7], [ONCE_J7])

    assert bueno["medibles"] == 1, bueno

    assert bueno["titulares_que_no_jugaron"] == 1, bueno


TESTS = [
    test_los_puntos_son_la_resta_de_dos_fotos,
    test_el_vendido_sigue_contando_y_el_que_no_jugo_se_ve,
    test_un_hueco_no_es_un_cero,
    test_sin_once_congelado_no_hay_nota,
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
        f"EL CUADERNO V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
