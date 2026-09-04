"""
VIGILAR tiene que querer decir algo.

SINTOMA

    Los once titulares salian marcados VIGILAR. Yamal, VIGILAR.
    De la Fuente, `status=ok`, `fitness=[4]`, VIGILAR. En la foto
    del 17/08, 205 de los 569 jugadores del catalogo llevaban la
    etiqueta.

CAUSA

    `player_availability.py` marcaba VIGILAR si `fitness` no
    estaba vacio. Pero `fitness` no es un parte medico: es el
    historial por jornada. Un numero son los puntos de esa
    jornada, `null` es una jornada sin dato, y SOLO un texto
    -"injured", "doubt", "sanctioned", "discarded"- dice que no
    jugo y por que. De esos 205, solo 13 traian un texto dentro.

CONSECUENCIA

    Una etiqueta que sale en el 36 % de la liga no avisa de
    nada: se lee como decorado y se deja de mirar. Cuando de
    verdad hubiera un jugador tocado, iria en la misma lista que
    Yamal.

    Esta guardia fija el criterio: VIGILAR solo con una señal de
    verdad, y el XI sano sale limpio.
"""

from __future__ import annotations

from src.analysis.player_availability import (
    analyze_player_availability,
    fitness_signals,
)


def _jugador(**campos) -> dict:
    base = {
        "id": 1,
        "name": "Fulano",
        "status": "ok",
        "statusInfo": "",
        "fitness": [],
    }
    base.update(campos)
    return base


# ============================================================
# EL FALLO EXACTO QUE SE ARREGLA
# ============================================================


def test_puntos_recientes_no_son_una_lesion() -> None:
    """El caso de De la Fuente: status=ok, fitness=[4]."""
    a = analyze_player_availability(
        _jugador(name="De la Fuente", fitness=[4])
    )
    assert a["label"] == "OK", "cuatro puntos la jornada pasada no es un aviso"
    assert a["risk"] == 0, "ni sube el riesgo"
    assert a["available"] is True, "y sigue disponible"


def test_el_once_sano_sale_limpio() -> None:
    """Once titulares con puntos recientes: cero etiquetas."""
    once = [
        _jugador(id=i, name=f"Titular {i}", fitness=[puntos])
        for i, puntos in enumerate(
            [7, 4, 2, 9, 0, 3, 12, 5, 1, 6, 4], start=1
        )
    ]
    etiquetas = {
        analyze_player_availability(j)["label"] for j in once
    }
    assert etiquetas == {"OK"}, f"el XI sano no se vigila, y salio {etiquetas}"


def test_una_jornada_sin_dato_tampoco_es_una_lesion() -> None:
    """`fitness=[None]` es "no hay observacion", no "esta tocado"."""
    a = analyze_player_availability(_jugador(fitness=[None]))
    assert a["label"] == "OK", "un hueco en el historial no es un parte medico"


def test_un_cero_no_es_una_lesion() -> None:
    """Cero puntos es un numero, y `0` es falsy: se cuenta igual."""
    a = analyze_player_availability(_jugador(fitness=[0]))
    assert a["label"] == "OK", "puntuar cero no es estar lesionado"


def test_puntos_negativos_siguen_siendo_puntos() -> None:
    a = analyze_player_availability(_jugador(fitness=[-1]))
    assert a["label"] == "OK", "-1 es una mala jornada, no una baja"


# ============================================================
# LO QUE SI TIENE QUE SALIR VIGILAR
# ============================================================


def test_un_texto_en_fitness_si_es_una_señal() -> None:
    """Brugue, real: status=ok pero se perdio la jornada sancionado."""
    a = analyze_player_availability(
        _jugador(name="Brugue", fitness=["sanctioned"])
    )
    assert a["label"] == "VIGILAR", "se perdio una jornada, y eso se mira"
    assert a["risk"] == 20, "avisa sin bloquear"
    assert a["automatic_lineup"] is True, "pero se le puede alinear"
    assert a["signals"] == ["sanctioned"], "y se dice por que se vigila"


def test_un_parte_escrito_es_una_señal() -> None:
    a = analyze_player_availability(
        _jugador(statusInfo="Molestias en el aductor.")
    )
    assert a["label"] == "VIGILAR", "si Biwenger escribe un parte, se vigila"


def test_un_estado_que_no_conocemos_no_se_pinta_en_verde() -> None:
    """`unknown` y `discarded` existen en el catalogo y no son "ok"."""
    for estado in ("unknown", "discarded"):
        a = analyze_player_availability(_jugador(status=estado))
        assert a["label"] == "VIGILAR", f"{estado} no es OK"
        assert a["available"] is True, (
            f"{estado} avisa, pero no bloquea: bloquear cambiaria alineaciones"
        )


def test_una_señal_mezclada_con_puntos_se_ve() -> None:
    a = analyze_player_availability(_jugador(fitness=[3, "injured", 5]))
    assert a["label"] == "VIGILAR", "el texto manda aunque haya puntos al lado"
    assert a["signals"] == ["injured"], "y se aisla la señal, no los puntos"


# ============================================================
# LO QUE NO SE PUEDE HABER ROTO POR EL CAMINO
# ============================================================


def test_el_lesionado_sigue_bloqueado() -> None:
    a = analyze_player_availability(
        _jugador(status="injured", statusInfo="Rotura fibrilar.",
                 fitness=["injured"])
    )
    assert a["available"] is False, "un lesionado no se alinea"
    assert a["label"] == "LESIONADO", "y se le llama por su nombre"
    assert a["risk"] == 100, "riesgo maximo"


def test_el_sancionado_sigue_bloqueado() -> None:
    a = analyze_player_availability(
        _jugador(status="sanctioned", fitness=["sanctioned"])
    )
    assert a["available"] is False, "un sancionado no juega"
    assert a["label"] == "SANCIONADO", "y se dice por que"


def test_la_duda_sigue_fuera_del_automatico() -> None:
    a = analyze_player_availability(
        _jugador(status="doubt", statusInfo="Molestias fisicas.")
    )
    assert a["label"] == "DUDA", "una duda es una duda"
    assert a["available"] is True, "disponible"
    assert a["automatic_lineup"] is False, "pero no se alinea sola"


def test_sin_status_se_asume_sano() -> None:
    a = analyze_player_availability({"id": 1, "name": "Fulano"})
    assert a["label"] == "OK", "un jugador sin datos raros sale OK"
    assert a["signals"] == [], "y sin señales inventadas"


# ============================================================
# EL LECTOR DE `fitness`, AISLADO
# ============================================================


def test_el_lector_separa_puntos_de_avisos() -> None:
    assert fitness_signals([4]) == [], "un numero son puntos"
    assert fitness_signals([None]) == [], "un null es un hueco"
    assert fitness_signals([]) == [], "vacio es vacio"
    assert fitness_signals(None) == [], "y un fitness ausente no revienta"
    assert fitness_signals("injured") == [], (
        "un fitness que no es lista no se lee letra a letra"
    )
    assert fitness_signals([True]) == [], (
        "bool es subclase de int: un True colado no es un parte"
    )
    assert fitness_signals(["Injured", "injured"]) == ["injured"], (
        "se normaliza y no se repite"
    )


TESTS = [
    test_puntos_recientes_no_son_una_lesion,
    test_el_once_sano_sale_limpio,
    test_una_jornada_sin_dato_tampoco_es_una_lesion,
    test_un_cero_no_es_una_lesion,
    test_puntos_negativos_siguen_siendo_puntos,
    test_un_texto_en_fitness_si_es_una_señal,
    test_un_parte_escrito_es_una_señal,
    test_un_estado_que_no_conocemos_no_se_pinta_en_verde,
    test_una_señal_mezclada_con_puntos_se_ve,
    test_el_lesionado_sigue_bloqueado,
    test_el_sancionado_sigue_bloqueado,
    test_la_duda_sigue_fuera_del_automatico,
    test_sin_status_se_asume_sano,
    test_el_lector_separa_puntos_de_avisos,
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
    print(f"ETIQUETA VIGILAR V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
