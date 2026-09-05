"""
El ojeador no adivina: lo dudoso va a `unmatched` y se publica.

SINTOMA

    Cruzar los nombres de tres webs con los 569 IDs de Biwenger
    es la parte que se rompe. Ya nos hemos quemado: Javi
    Hernandez entro por metodo NAME con margen 0,586 y un desvio
    de precio del 45,7 %, y sigue en la metadata del tablero de
    titularidad desde que se genero sin que lo mirase nadie.

CAUSA

    Emparejar por parecido de nombre contra la liga entera es
    facil de hacer y facil de hacer mal. `match_team` empareja
    dentro de UN equipo -veinticinco nombres- y aqui el rival son
    569.

CONSECUENCIA

    Un emparejamiento equivocado mete la prediccion de otro
    jugador en la ficha de uno tuyo. Es peor que no tener
    prediccion: sin dato no decides, con dato falso decides mal y
    encima con confianza.

    Esta guardia fija la regla dura del encargo: lo que no
    empareja con confianza NO entra, se apunta con su motivo, y
    el motivo se publica.
"""

from __future__ import annotations

from src.intelligence.scout.matching import (
    NAME_ONLY_FLOOR,
    NAME_ONLY_MARGIN,
    VALUE_NAME_FLOOR,
    VALUE_TIE_FLOOR,
    build_targets,
    match_records,
)


def _catalogo(jugadores) -> dict:
    """`{id: (nombre, precio)}` con la forma del catalogo real."""

    return {
        "data": {
            "players": {
                str(pid): {
                    "id": pid,
                    "name": nombre,
                    "price": precio,
                    "teamID": 1,
                }
                for pid, (nombre, precio) in jugadores.items()
            }
        }
    }


def _registro(nombre, valor=None, fuente="FUTBOLFANTASY") -> dict:
    return {
        "ff_name": nombre,
        "ff_slug": None,
        "market_value": valor,
        "team_hint": None,
        "signals": [{"source": fuente, "direction": "UP"}],
    }


# ============================================================
# 1. LA LLAVE DEL EURO
# ============================================================


def test_el_valor_exacto_y_un_nombre_plausible_cierran() -> None:
    objetivos = build_targets(
        _catalogo({10: ("Lamine Yamal", 21_170_000)})
    )

    emp, sin = match_records([_registro("Yamal", 21_170_000)], objetivos)

    assert len(emp) == 1 and not sin
    assert emp[0]["method"] == "VALUE_AND_NAME"
    assert emp[0]["target"]["id"] == 10


def test_el_valor_cuadra_y_el_nombre_dice_que_no() -> None:
    """
    Dos jugadores distintos pueden costar lo mismo. Que el precio
    coincida no es identificar a nadie.
    """

    objetivos = build_targets(
        _catalogo({10: ("Lamine Yamal", 21_170_000)})
    )

    emp, sin = match_records(
        [_registro("Karim Benzema", 21_170_000)], objetivos
    )

    assert not emp, "un precio igual no convierte a uno en otro"
    assert len(sin) == 1
    assert "el nombre no" in sin[0]["reason"]


def test_varios_comparten_precio_y_el_nombre_no_desempata() -> None:
    """
    102 jugadores comparten el minimo de 150.000 EUR en el
    catalogo real. Ahi el precio no dice nada.
    """

    objetivos = build_targets(
        _catalogo({
            1: ("Diego Murillo", 150_000),
            2: ("Diego Moreno", 150_000),
        })
    )

    emp, sin = match_records([_registro("Diego", 150_000)], objetivos)

    assert not emp, "'Diego' no identifica a ninguno de los dos"
    assert "comparten el valor" in sin[0]["reason"]


def test_varios_comparten_precio_pero_uno_gana_claro() -> None:
    objetivos = build_targets(
        _catalogo({
            1: ("Diego Murillo", 150_000),
            2: ("Aitor Paredes", 150_000),
        })
    )

    emp, sin = match_records(
        [_registro("Diego Murillo", 150_000)], objetivos
    )

    assert len(emp) == 1 and emp[0]["target"]["id"] == 1
    assert emp[0]["score"] >= VALUE_TIE_FLOOR


# ============================================================
# 2. LA VIA DEL NOMBRE, QUE ES LA PELIGROSA
# ============================================================


def test_un_nombre_flojo_no_empareja() -> None:
    """
    EL CASO JAVI HERNANDEZ.

    Nombre que se parece un poco, precio que no cuadra. Es
    exactamente la fila que lleva desde agosto en la metadata sin
    que nadie la mirase.
    """

    objetivos = build_targets(
        _catalogo({7: ("Javi Hernandez", 1_000_000)})
    )

    emp, sin = match_records(
        [_registro("Javi Sanchez", 4_500_000)], objetivos
    )

    assert not emp, (
        "un parecido de nombre con el precio en contra no es una "
        "identidad"
    )
    assert sin[0]["reason"]


def test_un_empate_de_nombres_no_se_resuelve_a_cara_o_cruz() -> None:
    objetivos = build_targets(
        _catalogo({
            1: ("Rodrigo Sanchez", 900_000),
            2: ("Rodrigo Sanches", 800_000),
        })
    )

    emp, sin = match_records([_registro("Rodrigo Sanchez")], objetivos)

    assert not emp, (
        "dos nombres casi iguales y ningun precio que desempate: "
        "se deja sin emparejar"
    )
    assert "margen" in sin[0]["reason"]


def test_el_nombre_solo_exige_mas_que_dentro_de_un_equipo() -> None:
    """
    El proveedor pide 0,82 dentro de un equipo de 25. Contra los
    569 de la liga el liston sube.
    """

    assert NAME_ONLY_FLOOR > 0.82
    assert NAME_ONLY_MARGIN > 0.04


def test_un_nombre_identico_y_solo_si_empareja() -> None:
    objetivos = build_targets(
        _catalogo({
            1: ("Aurelien Tchouameni", 900_000),
            2: ("Pedro Porro", 800_000),
        })
    )

    emp, sin = match_records(
        [_registro("Aurelien Tchouameni")], objetivos
    )

    assert len(emp) == 1 and emp[0]["method"] == "NAME"
    assert emp[0]["score"] >= NAME_ONLY_FLOOR


# ============================================================
# 3. LA REGLA DURA
# ============================================================


def test_ningun_emparejamiento_entra_por_debajo_de_su_liston() -> None:
    """
    LA GUARDIA QUE PIDE EL ENCARGO.

    Falla si un emparejamiento dudoso entra como bueno, sea cual
    sea la via.
    """

    objetivos = build_targets(
        _catalogo({
            1: ("Lamine Yamal", 21_170_000),
            2: ("Robert Lewandowski", 12_000_000),
            3: ("Diego Murillo", 150_000),
            4: ("Aitor Paredes", 150_000),
            5: ("Javi Hernandez", 1_000_000),
        })
    )

    registros = [
        _registro("Yamal", 21_170_000),
        _registro("Lewandowski", 12_000_000),
        _registro("Diego", 150_000),
        _registro("Javi Sanchez", 4_500_000),
        _registro("Un Nombre Inventado", 999_999),
    ]

    emp, sin = match_records(registros, objetivos)

    for pareja in emp:

        if pareja["method"] == "VALUE_AND_NAME":
            assert pareja["score"] >= VALUE_NAME_FLOOR, (
                f"{pareja['record']['ff_name']} entro por valor con "
                f"{pareja['score']}"
            )

        elif pareja["method"] == "NAME":
            assert pareja["score"] >= NAME_ONLY_FLOOR, (
                f"{pareja['record']['ff_name']} entro por nombre con "
                f"{pareja['score']}"
            )
            assert pareja["margin"] >= NAME_ONLY_MARGIN, (
                f"{pareja['record']['ff_name']} entro con margen "
                f"{pareja['margin']}"
            )

        else:
            raise AssertionError(f"metodo desconocido: {pareja['method']}")


def test_todo_lo_que_no_empareja_lleva_motivo() -> None:
    """
    Un `unmatched` sin motivo no se puede arreglar: no se sabe si
    fue el nombre, el precio o que la web cambio.
    """

    objetivos = build_targets(
        _catalogo({1: ("Lamine Yamal", 21_170_000)})
    )

    emp, sin = match_records(
        [
            _registro("Un Desconocido", 5_000),
            _registro("Otro Mas", None),
        ],
        objetivos,
    )

    assert len(sin) == 2

    for fila in sin:
        assert fila["reason"], "sin motivo no se puede arreglar"
        assert fila["name"], "y sin nombre no se sabe de quien habla"
        assert fila["source"], "ni de que fuente venia"


def test_un_jugador_no_se_asigna_dos_veces() -> None:
    """
    Dos filas de la misma web no pueden ser las dos el mismo
    jugador: una de las dos predicciones no es suya.
    """

    objetivos = build_targets(
        _catalogo({1: ("Lamine Yamal", 21_170_000)})
    )

    emp, sin = match_records(
        [
            _registro("Lamine Yamal", 21_170_000),
            _registro("Lamine Yamal", 21_170_000),
        ],
        objetivos,
    )

    assert len(emp) == 1, "se cierra una vez"
    assert len(sin) == 1, "y la segunda se dice"


def test_sin_catalogo_no_se_empareja_nada() -> None:
    emp, sin = match_records([_registro("Yamal", 21_170_000)], [])

    assert not emp, "sin catalogo no hay contra que emparejar"


def test_nunca_lanza_con_basura() -> None:
    objetivos = build_targets(
        _catalogo({1: ("Lamine Yamal", 21_170_000)})
    )

    for basura in (None, [], [None], ["texto"], [{}], [{"ff_name": None}]):
        emp, sin = match_records(basura, objetivos)
        assert isinstance(emp, list) and isinstance(sin, list)

    for catalogo_malo in (None, {}, {"data": None}, {"data": {"players": []}}):
        assert build_targets(catalogo_malo) == []


TESTS = [
    test_el_valor_exacto_y_un_nombre_plausible_cierran,
    test_el_valor_cuadra_y_el_nombre_dice_que_no,
    test_varios_comparten_precio_y_el_nombre_no_desempata,
    test_varios_comparten_precio_pero_uno_gana_claro,
    test_un_nombre_flojo_no_empareja,
    test_un_empate_de_nombres_no_se_resuelve_a_cara_o_cruz,
    test_el_nombre_solo_exige_mas_que_dentro_de_un_equipo,
    test_un_nombre_identico_y_solo_si_empareja,
    test_ningun_emparejamiento_entra_por_debajo_de_su_liston,
    test_todo_lo_que_no_empareja_lleva_motivo,
    test_un_jugador_no_se_asigna_dos_veces,
    test_sin_catalogo_no_se_empareja_nada,
    test_nunca_lanza_con_basura,
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
    print(f"OJEADOR EMPAREJAMIENTO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
