"""
Los penaltis: apagados a proposito, y sin gastar cuota.

SINTOMA

    `penalty_kickers.json`: 39 de 39 jugadores con `role:
    UNKNOWN`, `bonus: 0.0`, y `mapping_safe: false` en 33 de
    ellos. El `PRIMARY_BONUS = 8.0` que ordena el XI no se ha
    aplicado jamas.

CAUSA

    El plan Free de API-Football corta la cadena por los dos
    extremos:

      - la identidad se busca con `PLAYER_LOOKUP_SEASON = 2024`,
        asi que quien llego a LaLiga despues no aparece -21 de 44
        entradas de la cache con `external_id: null`-;

      - y las estadisticas se piden de `CURRENT_SEASON = 2026`,
        que el plan rechaza: "Free plans do not have access to
        this season, try from 2022 to 2024".

    No hay una temporada en la que las dos mitades funcionen a la
    vez.

CONSECUENCIA

    Seis llamadas diarias a un endpoint que siempre devuelve el
    mismo error, contra una cuota Free, para no obtener nada.

    Esta guardia protege tres cosas: que apagado no signifique
    salir a la red, que apagado devuelva exactamente lo mismo que
    venia saliendo -bonus 0.0, y por tanto ni un solo XI
    cambiado-, y que la maquinaria siga entera para que
    reencenderla sea una linea cuando haya plan de pago.

    Y una cuarta, la que de verdad puede morder: que a nadie se
    le ocurra "arreglarlo" pidiendo las estadisticas de 2024. Un
    +8 en el once de 2026 por penaltis de hace dos temporadas es
    peor que no tener el dato.
"""

from __future__ import annotations

import ast

from pathlib import Path

import src.intelligence.penalty_intelligence as penaltis


JUGADOR = {"id": 26271, "name": "Fulano", "teamID": 1}

SNAPSHOT = {
    "catalog": {"data": {"teams": {"1": {"id": 1, "name": "Barcelona"}}}}
}


def test_apagado_de_serie() -> None:
    assert penaltis.PENALTY_INTELLIGENCE_ENABLED is False, (
        "mientras el plan sea Free, esto va apagado"
    )


def test_apagado_no_sale_a_la_red_ni_toca_el_disco() -> None:
    """Lo que costaba: seis llamadas diarias para el mismo error."""

    llamadas = []

    api_original = penaltis.api_get
    map_original = penaltis.map_player
    load_original = penaltis._load_cache
    save_original = penaltis._save_cache

    penaltis.api_get = lambda *a, **k: llamadas.append("api_get")
    penaltis.map_player = lambda *a, **k: llamadas.append("map_player")
    penaltis._load_cache = lambda *a, **k: llamadas.append("_load_cache")
    penaltis._save_cache = lambda *a, **k: llamadas.append("_save_cache")

    try:
        penaltis.get_penalty_context(SNAPSHOT, JUGADOR)
    finally:
        penaltis.api_get = api_original
        penaltis.map_player = map_original
        penaltis._load_cache = load_original
        penaltis._save_cache = save_original

    assert llamadas == [], f"apagado y aun asi hizo: {llamadas}"


def test_apagado_devuelve_lo_mismo_que_ya_salia() -> None:
    """
    Apagar no puede cambiar un XI. Lo que salia era bonus 0.0
    para los 39, y lo que sale es bonus 0.0.
    """

    contexto = penaltis.get_penalty_context(SNAPSHOT, JUGADOR)

    assert contexto["bonus"] == 0.0, "cero, como llevaba saliendo siempre"
    assert contexto["role"] == "UNKNOWN", "y sin rol"
    assert contexto["available"] is False, "no hay señal, y se dice"
    assert contexto["enabled"] is False, "y se dice que es porque esta apagado"


def test_apagado_explica_por_que() -> None:
    """
    Un cero sin motivo se lee como "no lanza penaltis". Este cero
    significa "no lo sabemos, y no vamos a preguntar".
    """

    razon = penaltis.get_penalty_context(SNAPSHOT, JUGADOR)["reason"]

    assert razon, "un apagado sin motivo escrito se reenciende a ciegas"
    assert "2024" in razon and "Free" in razon, (
        "el motivo tiene que nombrar la causa real: el plan y la temporada"
    )


def test_la_ficha_no_pierde_columnas_al_apagarse() -> None:
    """
    Quien lee el contexto de penaltis -el motor de alineacion-
    tiene que encontrar las mismas claves. Un `KeyError` en la
    ruta del once seria mucho peor que no tener penaltis.
    """

    esperadas = {
        "biwenger_id", "player_name", "season", "role", "bonus",
        "taken", "scored", "missed", "external_id", "mapping_safe",
        "available", "reason", "error", "fetched_at_unix", "from_cache",
    }

    contexto = penaltis.get_penalty_context(SNAPSHOT, JUGADOR)

    assert esperadas <= set(contexto), (
        f"faltan claves: {sorted(esperadas - set(contexto))}"
    )


def test_la_maquinaria_sigue_entera() -> None:
    """
    Apagado no es borrado. El dia que haya plan de pago, esto
    tiene que volver con una linea.
    """

    assert penaltis.PRIMARY_BONUS == 8.0, "el bonus sigue definido"
    assert penaltis.SECONDARY_BONUS == 3.0

    assert penaltis._role_from_taken(2)[0] == "PRIMARY_EVIDENCE"
    assert penaltis._role_from_taken(2)[1] == 8.0
    assert penaltis._role_from_taken(1)[0] == "SECONDARY_EVIDENCE"
    assert penaltis._role_from_taken(0)[0] == "UNKNOWN"

    assert penaltis._extract_penalty_stats(
        [{"statistics": [{"penalty": {"scored": 3, "missed": 1},
                          "games": {"appearences": 20}}]}]
    ) == {"taken": 4, "scored": 3, "missed": 1, "appearances": 20}


def test_el_interruptor_se_puede_encender() -> None:
    """Que el flag mande de verdad, y no sea decorado."""

    original = penaltis.PENALTY_INTELLIGENCE_ENABLED
    map_original = penaltis.map_player
    load_original = penaltis._load_cache
    save_original = penaltis._save_cache

    tocado = []

    penaltis.PENALTY_INTELLIGENCE_ENABLED = True

    # Sin cache y sin escribir: esto es una prueba, no un ciclo.
    penaltis._load_cache = lambda: {"players": {}}
    penaltis._save_cache = lambda cache: None

    penaltis.map_player = lambda *a, **k: (
        tocado.append("map_player"),
        {"safe_for_automatic_use": False, "external_id": None},
    )[1]

    try:
        contexto = penaltis.get_penalty_context(SNAPSHOT, JUGADOR)
    finally:
        penaltis.PENALTY_INTELLIGENCE_ENABLED = original
        penaltis.map_player = map_original
        penaltis._load_cache = load_original
        penaltis._save_cache = save_original

    assert tocado == ["map_player"], (
        "encendido tiene que volver a intentar el emparejamiento"
    )
    assert contexto["enabled"] is True, (
        "y decir que estaba encendido cuando lo intento"
    )


def test_nadie_pide_las_estadisticas_de_la_temporada_de_lookup() -> None:
    """
    LA GUARDIA QUE MAS IMPORTA.

    El arreglo aparente es cambiar la temporada de estadisticas a
    2024 para que el plan Free conteste. Eso pondria un +8 en el
    once de 2026 por penaltis de hace dos temporadas, y para casi
    la mitad de la plantilla no habria dato ninguno.

    Si algun dia se hace, que sea una decision tomada a
    proposito, y no un parche de una tarde.
    """

    arbol = ast.parse(
        Path(penaltis.__file__).read_text(encoding="utf-8")
    )

    importados = {
        alias.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ImportFrom)
        for alias in nodo.names
    }

    assert "PLAYER_LOOKUP_SEASON" not in importados, (
        "las estadisticas de penaltis han empezado a pedirse de la "
        "temporada de lookup: eso es evidencia de otra temporada "
        "ordenando el XI de esta"
    )
    assert "CURRENT_SEASON" in importados, (
        "la consulta de estadisticas tiene que seguir siendo de la "
        "temporada en curso"
    )


TESTS = [
    test_apagado_de_serie,
    test_apagado_no_sale_a_la_red_ni_toca_el_disco,
    test_apagado_devuelve_lo_mismo_que_ya_salia,
    test_apagado_explica_por_que,
    test_la_ficha_no_pierde_columnas_al_apagarse,
    test_la_maquinaria_sigue_entera,
    test_el_interruptor_se_puede_encender,
    test_nadie_pide_las_estadisticas_de_la_temporada_de_lookup,
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
    print(f"PENALTIS APAGADOS V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
