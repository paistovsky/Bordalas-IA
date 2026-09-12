"""
Lo que se arma, se enchufa. Y el indicador lo enciende el HECHO.

SINTOMA (12/09/2026)

    La rendija se encendio el 11. Al dia siguiente no habia
    comprado nada, y el panel decia EN VIVO.

    No era ninguna de sus cinco puertas. Era que NADIE LA
    LLAMABA: el unico sitio del proyecto que importaba
    `la_rendija` era la TELEMETRIA. Modulos escritos, 24 guardias
    en verde, estado publicado, pantalla pintando que funcionaba
    — sobre codigo que no corria.

CAUSA

    `en_vivo = True` era la bandera del MODULO, no una prueba de
    que se ejecutara. Y la pantalla leia esa bandera.

    Armar algo y no enchufarlo es PEOR que no armarlo, porque la
    pantalla dice que funciona y nadie va a mirar.

CONSECUENCIA

    Dos guardias, y las dos son la misma leccion vista por sus
    dos lados:

        1. Que exista un camino REAL desde el ciclo hasta cada
           pieza armada. Del arbol, no de un grep.

        2. Que el indicador de la pantalla lo encienda el HECHO
           —corrio, y esta es la hora— y no la intencion.

    Doctrina 37.
"""

from __future__ import annotations

import ast
import io

from pathlib import Path


RAIZ = Path(__file__).parents[2]

# El fichero que ejecuta el workflow. Todo camino sale de aqui.
CICLO = RAIZ / "src" / "v10_full_autonomous_live.py"

# LAS PIEZAS ARMADAS. Cada una tiene que ser alcanzable desde el
# ciclo. Si alguna deja de serlo, esta guardia se pone roja.
ARMADAS = {
    "la rendija": "la_rendija",
    "el carril": "carril_executor",
    "la renovacion": "renovar_executor",
    "la salida del viaje": "salida_del_viaje",
    "el escaparate": "escaparate_executor",
    "la subasta": "la_subasta",
}


def _lee(ruta: Path) -> str:
    if not ruta.exists():
        raise AssertionError(f"no existe {ruta}")

    return ruta.read_text(encoding="utf-8")


def _modulos_que_importa(ruta: Path) -> set:
    """
    Los modulos de esta casa que importa un fichero. Del arbol.

    Un `grep` diria que si porque el nombre aparece en un
    comentario; esto solo cuenta imports de verdad.
    """

    try:
        arbol = ast.parse(_lee(ruta))

    except (SyntaxError, AssertionError):
        return set()

    vistos = set()

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            vistos.add(nodo.module)

        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                vistos.add(alias.name)

    return {
        m.split(".")[-1]
        for m in vistos
        if m.startswith("src.")
    }


def _alcanzable(objetivo: str, desde: Path, vistos=None) -> bool:
    """
    ¿Se llega a `objetivo` desde `desde`, siguiendo imports?

    Recorre el arbol de importaciones de esta casa. Se para en
    lo ya visto para no dar vueltas.
    """

    vistos = vistos if vistos is not None else set()

    if desde in vistos:
        return False

    vistos.add(desde)

    modulos = _modulos_que_importa(desde)

    if objetivo in modulos:
        return True

    for nombre in modulos:

        for carpeta in (
            "analysis",
            "actions",
            "biwenger",
            "collectors",
            "intelligence",
            "telemetry",
        ):
            siguiente = (
                RAIZ / "src" / carpeta / f"{nombre}.py"
            )

            if siguiente.exists() and _alcanzable(
                objetivo, siguiente, vistos
            ):
                return True

    return False


# ============================================================
# 1. TODO LO ARMADO ESTA ENCHUFADO
# ============================================================


def test_el_carril_esta_enchufado() -> None:
    """
    EL FALLO DEL 12/09.

    Tiene que existir un camino REAL desde el ciclo hasta el
    carril. Si alguien lo desconecta, esto se pone rojo el mismo
    dia y no dos despues, con la pantalla diciendo EN VIVO.
    """

    assert _alcanzable("carril_executor", CICLO), (
        "el ciclo NO llega al carril: la rendija estaria "
        "encendida y no la ejecutaria nadie"
    )

    assert _alcanzable("la_rendija", CICLO), (
        "el ciclo NO llega a `la_rendija`"
    )


def test_ninguna_pieza_armada_esta_desenchufada() -> None:
    """
    La misma pregunta, para todas.

    Si alguna mas esta desenchufada, esta guardia lo dice HOY y
    con su nombre, en vez de descubrirse el dia que alguien se
    pregunte por que no hizo nada.
    """

    sueltas = [
        f"{como_se_llama} (`{modulo}`)"
        for como_se_llama, modulo in ARMADAS.items()
        if not _alcanzable(modulo, CICLO)
    ]

    assert not sueltas, (
        "estas piezas estan ARMADAS y el ciclo no llega a "
        "ninguna, asi que no se ejecutan: " + " · ".join(sueltas)
    )

    # Regla 24: si la lista se vaciara, esto pasaria en vacio.
    assert len(ARMADAS) >= 6, ARMADAS


def test_el_buscador_de_caminos_no_miente() -> None:
    """
    Un buscador que dice "si" a todo no comprueba nada, y uno que
    dice "no" a todo tampoco. Se le pregunta por algo que SI esta
    y por algo que no puede estar.
    """

    # Algo que el ciclo alcanza seguro.
    assert _alcanzable("decision_orchestrator", CICLO)

    # Y algo que no existe.
    assert not _alcanzable(
        "modulo_que_no_existe_en_ninguna_parte", CICLO
    )


# ============================================================
# 2. EL INDICADOR LO ENCIENDE EL HECHO
# ============================================================


def test_el_indicador_no_se_enciende_con_la_bandera() -> None:
    """
    "EN VIVO" tiene que significar "corrio, y esta es la hora",
    no "la constante del modulo dice True".

    El 12/09 el panel decia EN VIVO porque leia `en_vivo()`, que
    es la INTENCION. Ahora lee la ultima vez que el carril corrio
    de verdad, y si no ha corrido nunca lo dice.
    """

    panel = _lee(
        RAIZ
        / "dashboard-v8"
        / "src"
        / "components"
        / "RendijaPanel.jsx"
    )

    assert "ultima_vuelta" in panel, (
        "el panel no lee cuando corrio el carril por ultima vez: "
        "sigue encendiendo el indicador con la bandera"
    )

    assert "NUNCA HA CORRIDO" in panel, (
        "el panel no dice nada cuando el carril no ha corrido "
        "nunca, que es exactamente el caso que hubo que "
        "descubrir a mano"
    )


def test_el_ciclo_deja_dicho_que_el_carril_corrio() -> None:
    """
    El hecho tiene que quedar escrito en el estado, con hora, o
    la pantalla no tiene con que encender nada.
    """

    ciclo = _lee(CICLO)

    assert '"carril": carril' in ciclo, (
        "el ciclo no publica lo que hizo el carril"
    )

    ejecutor = _lee(
        RAIZ / "src" / "actions" / "carril_executor.py"
    )

    assert '"ran_at"' in ejecutor, (
        "el carril no deja la hora a la que corrio: la pantalla "
        "no puede distinguir «no ha corrido» de «corrio y no "
        "encontro a quien pujar»"
    )


TESTS = [
    test_el_buscador_de_caminos_no_miente,
    test_el_carril_esta_enchufado,
    test_ninguna_pieza_armada_esta_desenchufada,
    test_el_ciclo_deja_dicho_que_el_carril_corrio,
    test_el_indicador_no_se_enciende_con_la_bandera,
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
        f"ESTA ENCHUFADO V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
