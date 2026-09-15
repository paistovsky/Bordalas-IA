"""
La etiqueta del catalogo dice lo que mide, o no lo dice.

EL SINTOMA (15/09/2026)

    El cuadro del vestuario libre decia «nos mejorarian el once» a
    138 jugadores. El motor, sobre sus 69 candidatos, decia que
    mejoran CERO:

        NO_MEJORA_JERARQUIA    25
        NO_MEJORA              15
        PIERDE_TITULARIDAD     14
        NO_MEJORA_TITULARIDAD  10
        MEJORA_INSUFICIENTE     1
        SIN_PRONOSTICO          1

    Caso vivo: Alvaro Carreras salia en el catalogo como «nos
    mejora +9 sobre Trent (12)», y en OBJETIVOS como «sustituiria
    a un titular confirmado (100 %) por alguien que esta a 0 %: el
    once empeora».

    LAS DOS FRASES ERAN VERDAD. `nos_suma` es la resta pelada de
    puntos: no mira el pronostico de titularidad ni aplica la vara
    con la que decide el motor.

    El dueño lo leyo como que Pepe se contradice. No se
    contradice: la pantalla usaba una etiqueta que el motor no usa
    para decidir.

LA SALIDA ELEGIDA, Y POR QUE

    El encargo daba dos: aplicar el criterio del motor al
    catalogo, o cambiar la etiqueta y explicarlo al pie. «La que
    menos toque el motor, mejor».

    Se cambia LA ETIQUETA. El motor no se toca ni un byte.

LO QUE VIGILA ESTA GUARDIA

    1. Que la pantalla NO afirme que alguien mejora el once, si no
       es eso lo que mide.
    2. Que el pie explique la diferencia, nombrando lo que NO
       mira: el pronostico de titularidad.
    3. Que si algun dia se vuelve a la etiqueta vieja, entonces el
       catalogo tenga que coincidir con el `xi_decision` del motor
       jugador a jugador.

REGLA 23 / DOCTRINA 50

    No lee estado de produccion: lee el JSX del repositorio, que
    es codigo. El catalogo y los objetivos son fixtures.
"""

from __future__ import annotations

import re

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

PANEL = (
    RAIZ
    / "dashboard-v8"
    / "src"
    / "components"
    / "ElVestuarioLibrePanel.jsx"
)


# La frase que afirmaba lo que no medía.
ETIQUETA_VIEJA = "nos mejorarían el once"

# Lo que el catalogo mide de verdad.
ETIQUETA_NUEVA = "más puntos en la hoja"


# ============================================================
# EL FIXTURE: EL CASO DE ALVARO CARRERAS
# ============================================================

# Tal y como salio: el catalogo dice +9 y el motor dice que el
# once empeora.
CATALOGO = [
    {
        "id": 1001,
        "name": "Álvaro Carreras",
        "nos_suma": 9,
        "vara_nombre": "Trent",
        "vara_puntos": 12,
    },
    {
        "id": 1002,
        "name": "Otro que suma",
        "nos_suma": 4,
        "vara_nombre": "Trent",
        "vara_puntos": 12,
    },
]

OBJETIVOS = [
    {
        "player_id": 1001,
        "xi_decision": "PIERDE_TITULARIDAD",
        "reason": (
            "Sustituiría a un titular confirmado (100 %) por "
            "alguien que está a 0 %: el once empeora."
        ),
    },
    {
        "player_id": 1002,
        "xi_decision": "NO_MEJORA_JERARQUIA",
        "reason": "No mejora la jerarquía del puesto.",
    },
]

# Los verdictos del motor que NO son una mejora.
NO_MEJORAN = {
    "NO_MEJORA",
    "NO_MEJORA_JERARQUIA",
    "NO_MEJORA_TITULARIDAD",
    "PIERDE_TITULARIDAD",
    "MEJORA_INSUFICIENTE",
    "SIN_PRONOSTICO",
}


def _jsx() -> str:
    return PANEL.read_text(encoding="utf-8")


def _sin_comentarios(fuente: str) -> str:
    """Lo que la pantalla PINTA, no lo que explica de si misma."""

    fuente = re.sub(r"/\*.*?\*/", " ", fuente, flags=re.S)

    return re.sub(r"(?m)^\s*//.*$", " ", fuente)


# ============================================================
# REGLA 24
# ============================================================


def test_el_fixture_tiene_el_caso() -> None:
    """
    Sin un jugador que el catalogo suba y el motor tumbe, esta
    guardia no probaria nada.
    """

    assert CATALOGO, "el catalogo de la prueba llega vacio"

    assert OBJETIVOS, "los objetivos de la prueba llegan vacios"

    chocan = [
        c
        for c in CATALOGO
        if c["nos_suma"] > 0
        and any(
            o["player_id"] == c["id"]
            and o["xi_decision"] in NO_MEJORAN
            for o in OBJETIVOS
        )
    ]

    assert chocan, (
        "el fixture no tiene ni un jugador que el catalogo suba y "
        "el motor tumbe: el choque que motiva esta guardia no se "
        "estaria probando"
    )

    assert PANEL.exists(), PANEL

    print(
        f"  OK  el fixture trae {len(chocan)} jugador(es) que el "
        f"catalogo sube y el motor tumba"
    )


# ============================================================
# 1. LA ETIQUETA
# ============================================================


def test_la_etiqueta_dice_lo_que_mide() -> None:
    """
    O la etiqueta no afirma que mejora el once, o el catalogo
    tiene que coincidir con el motor jugador a jugador.

    Las dos salidas valen. Lo que no vale es afirmar una cosa y
    medir otra.
    """

    pintado = _sin_comentarios(_jsx())

    afirma_el_once = ETIQUETA_VIEJA in pintado

    if afirma_el_once:

        # SI SE AFIRMA, SE DEMUESTRA: ningun jugador del catalogo
        # puede estar etiquetado como mejora y tumbado por el
        # motor en la misma foto.
        verdictos = {
            o["player_id"]: o["xi_decision"] for o in OBJETIVOS
        }

        mentirosos = [
            c["name"]
            for c in CATALOGO
            if c["nos_suma"] > 0
            and verdictos.get(c["id"]) in NO_MEJORAN
        ]

        assert not mentirosos, (
            f"la pantalla dice «{ETIQUETA_VIEJA}» y el motor "
            f"tumba a {len(mentirosos)}: "
            f"{', '.join(mentirosos)}. O se aplica el criterio "
            f"del motor, o se cambia la etiqueta."
        )

        print(
            "  OK  se afirma la mejora del once Y el catalogo "
            "coincide con el motor"
        )
        return

    # SI NO SE AFIRMA, la etiqueta tiene que decir lo que mide.
    assert ETIQUETA_NUEVA in pintado, (
        f"la pantalla ya no dice «{ETIQUETA_VIEJA}» pero tampoco "
        f"dice «{ETIQUETA_NUEVA}»: no se sabe que mide"
    )

    print(
        f"  OK  la etiqueta es «{ETIQUETA_NUEVA}» y no afirma "
        f"ninguna mejora del once"
    )


def test_el_pie_explica_la_diferencia() -> None:
    """
    Cambiar la etiqueta sin explicarla deja al que mira con dos
    cuadros que no sabe relacionar.

    El pie tiene que decir lo que la columna NO mira. Y no vale
    ponerlo en un comentario del codigo: tiene que estar en lo que
    se PINTA.
    """

    pintado = _sin_comentarios(_jsx())

    if ETIQUETA_VIEJA in pintado:
        print(
            "  OK  se mantiene la etiqueta vieja: el pie no tiene "
            "nada que explicar"
        )
        return

    # LO QUE NO MIRA, dicho.
    assert "titularidad" in pintado, (
        "el pie no dice que esta columna NO mira el pronostico "
        "de titularidad, que es justo lo que separa los dos "
        "cuadros"
    )

    assert "no es" in pintado.lower() and "once" in pintado, (
        "el pie no dice que «mas puntos» no es «mejora el once»"
    )

    # Y A QUIEN SI HAY QUE MIRAR.
    assert "xi_decision" in pintado or "OBJETIVOS" in pintado, (
        "el pie no manda al cuadro que SI decide"
    )

    print(
        "  OK  el pie explica que mas puntos no es mejorar el "
        "once, y manda a quien decide"
    )


def test_no_se_ha_tocado_el_motor() -> None:
    """
    El encargo: "la que menos toque el motor, mejor".

    El catalogo sigue midiendo lo mismo -la resta de puntos-; lo
    unico que ha cambiado es como se llama. Si algun dia esta
    guardia se pone roja porque el catalogo empieza a mirar la
    titularidad, sera una decision, no un descuido.
    """

    vestuario = (
        RAIZ / "src" / "analysis" / "el_vestuario_libre.py"
    ).read_text(encoding="utf-8")

    for prohibido in (
        "xi_decision",
        "starter_probability",
        "PIERDE_TITULARIDAD",
    ):
        assert prohibido not in vestuario, (
            f"`el_vestuario_libre` ha empezado a mirar "
            f"`{prohibido}`: eso cambia lo que mide el catalogo, "
            f"y entonces la etiqueta puede volver a ser «mejora "
            f"el once» — pero hay que decidirlo, no colarlo"
        )

    print(
        "  OK  el catalogo sigue midiendo la resta de puntos: el "
        "motor no se ha tocado"
    )


TESTS = [
    test_el_fixture_tiene_el_caso,
    test_la_etiqueta_dice_lo_que_mide,
    test_el_pie_explica_la_diferencia,
    test_no_se_ha_tocado_el_motor,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"LA ETIQUETA DICE LO QUE MIDE V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
