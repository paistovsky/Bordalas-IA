"""
Lo que se publica, se ve. Y lo que se ve, se publica.

SINTOMA

    El fallo mas repetido de este repo, contado por sus propios
    comentarios: "Septima vez en dos dias que un dato se calcula,
    se publica y se pierde en el ultimo metro."

    `priorities` llegaba en el JSON y el normalizador no lo
    copiaba: la columna COLA DE DECISIONES se pintaba en blanco.
    `rival_squads` se calculaba desde el 20/08 y llegaba vacio.
    El libro de pujas se escribe desde el 03/09 y no lo enseñaba
    nadie.

CAUSA

    Entre el generador de `status.json` y la pantalla hay dos
    saltos, y cada uno se puede romper sin que nada avise:

        dashboard_state.py  ->  status.js  ->  el componente

    El primero es Python y el segundo JavaScript, asi que ningun
    test de los que hay cruza los dos.

CONSECUENCIA

    Un bloque calculado que no se pinta cuesta lo mismo que no
    calcularlo, y ademas engaña: en el JSON esta, asi que parece
    hecho.

    Esta guardia cose los dos saltos para los bloques nuevos. No
    comprueba que se vean bonitos -eso no lo puede comprobar un
    test- sino que la cadena esta entera: el backend lo escribe,
    el normalizador lo copia, un componente lo lee y una pagina
    monta ese componente.
"""

from __future__ import annotations

import re

from pathlib import Path


DASHBOARD = Path("dashboard-v8/src")
ESTADO = Path("src/telemetry/dashboard_state.py")
NORMALIZADOR = DASHBOARD / "lib" / "status.js"


# (clave en status.json, nombre en el normalizador, componente,
#  paginas donde tiene que estar montado)
CADENAS = [
    (
        "bid_outcomes",
        "bidOutcomes",
        "BidOutcomesPanel",
        ["AuditPage.jsx"],
    ),
    (
        "rival_squads",
        "rivalSquads",
        None,                       # ya se pinta en SquadPage
        [],
    ),
    (
        "race",
        "race",
        "RacePanel",
        ["HomePage.jsx"],
    ),
    (
        "season_horizon",
        "seasonHorizon",
        "SeasonHorizonPanel",
        ["MarketPage.jsx"],
    ),
    (
        "roster_expansion",
        "rosterExpansion",
        "RosterExpansionPanel",
        ["MarketPage.jsx"],
    ),
]


def _lee(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


# ============================================================
# 1. EL BACKEND LO ESCRIBE
# ============================================================


def test_el_backend_publica_los_bloques() -> None:
    fuente = _lee(ESTADO)

    for clave, _, _, _ in CADENAS:
        assert f'"{clave}":' in fuente, (
            f"`{clave}` no se publica en status.json"
        )


# ============================================================
# 2. EL NORMALIZADOR LO COPIA
# ============================================================


def test_el_normalizador_copia_los_bloques() -> None:
    """
    El salto que rompio `priorities`: llegaba en el JSON y este
    fichero no lo copiaba, asi que para la pantalla no existia.
    """

    fuente = _lee(NORMALIZADOR)

    for clave, nombre, _, _ in CADENAS:
        assert f"raw.{clave}" in fuente, (
            f"el normalizador no lee `raw.{clave}`: la pantalla no "
            f"puede verlo aunque el backend lo publique"
        )
        assert re.search(rf"\b{nombre}\s*:", fuente), (
            f"el normalizador no expone `{nombre}`"
        )


def test_lo_que_no_se_sabe_llega_diciendo_que_no_se_sabe() -> None:
    """
    Cada bloque cae a `available: false` si falta, para que la
    pantalla diga "no hay dato" en vez de desaparecer o pintar
    ceros. Un cero se lee como una medida.
    """

    fuente = _lee(NORMALIZADOR)

    for clave, _, _, _ in CADENAS:
        trozo = fuente[fuente.index(f"raw.{clave}"):]
        trozo = trozo[: trozo.index("\n\n") if "\n\n" in trozo else 200]

        assert "available: false" in trozo, (
            f"`{clave}` no tiene respaldo con `available: false`"
        )


# ============================================================
# 3. UN COMPONENTE LO LEE, Y UNA PAGINA LO MONTA
# ============================================================


def test_cada_bloque_tiene_componente_que_lo_lee() -> None:
    for _, nombre, componente, _ in CADENAS:

        if componente is None:
            continue

        ruta = DASHBOARD / "components" / f"{componente}.jsx"

        assert ruta.exists(), f"falta el componente {componente}"

        assert f"data.{nombre}" in _lee(ruta), (
            f"{componente} no lee `data.{nombre}`: seria un panel "
            f"que no enseña su propio dato"
        )


def test_cada_componente_esta_montado_en_su_pagina() -> None:
    """
    EL ULTIMO METRO.

    Un componente escrito y no montado es exactamente igual de
    invisible que un dato no calculado, y encima parece hecho.
    """

    for _, _, componente, paginas in CADENAS:

        if componente is None:
            continue

        for pagina in paginas:

            fuente = _lee(DASHBOARD / "pages" / pagina)

            assert f"import {componente}" in fuente, (
                f"{pagina} no importa {componente}"
            )
            assert f"<{componente}" in fuente, (
                f"{pagina} importa {componente} y no lo monta"
            )


def test_los_paneles_nuevos_avisan_cuando_no_hay_dato() -> None:
    """
    Un panel que se esconde cuando falla es un panel que no se
    mira nunca. Todos tienen que tener rama de "no hay".
    """

    for _, _, componente, _ in CADENAS:

        if componente is None:
            continue

        fuente = _lee(DASHBOARD / "components" / f"{componente}.jsx")

        assert "available" in fuente, (
            f"{componente} no comprueba `available`"
        )
        assert 'className="empty"' in fuente, (
            f"{componente} no tiene rama de 'no hay dato': si falla, "
            f"desaparece sin decirlo"
        )


# ============================================================
# 4. EL TOPE POR OPERACION, QUE ERA EL CASO DE AYER
# ============================================================


def test_el_tope_por_operacion_se_ve() -> None:
    """
    Se arreglo el lector el 04/09 y seguia sin salir por ninguna
    pantalla: arreglado y invisible es medio arreglado.
    """

    fuente = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "max_operation" in fuente, (
        "el tope por operacion no se pinta en ninguna parte"
    )


def test_ningun_panel_nuevo_decide_nada() -> None:
    """
    Los tres bloques de esta noche son FASE OBSERVADOR. La
    pantalla tiene que decirlo: si no, el dueño puede creer que
    Pepe ya ficha asi.
    """

    for componente, aviso in (
        ("RacePanel", "no</b> lo usa para decidir"),
        ("SeasonHorizonPanel", "el motor decide"),
        ("RosterExpansionPanel", "no</b> puede hacer esto hoy"),
    ):
        fuente = _lee(DASHBOARD / "components" / f"{componente}.jsx")

        assert aviso in fuente, (
            f"{componente} no avisa de que es un termometro: "
            f"falta «{aviso}»"
        )


TESTS = [
    test_el_backend_publica_los_bloques,
    test_el_normalizador_copia_los_bloques,
    test_lo_que_no_se_sabe_llega_diciendo_que_no_se_sabe,
    test_cada_bloque_tiene_componente_que_lo_lee,
    test_cada_componente_esta_montado_en_su_pagina,
    test_los_paneles_nuevos_avisan_cuando_no_hay_dato,
    test_el_tope_por_operacion_se_ve,
    test_ningun_panel_nuevo_decide_nada,
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
    print(f"LA PANTALLA LEE LO PUBLICADO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
