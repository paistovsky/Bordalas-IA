"""
La via de ampliar plantilla, calculada y sin ejecutar.

SINTOMA

    Pepe tiene 14 fichas. La plantilla mas grande de la liga
    tiene 17. Hay sitio libre y ninguna via para usarlo.

CAUSA

    `acquisition_valuation.py:352-358` compara cada candidato con
    UN jugador: el peor titular de su posicion. No existe la
    operacion "fichar y punto". Si no le gana a ese titular, la
    fila cae a `intent = SPECULATION` y se la juzga con el liston
    de la reventa.

CONSECUENCIA

    Esta guardia protege tres cosas:

      1. Que se cuenten los huecos SIN inventarse el tope de
         Biwenger, que no esta en el codigo ni comprobado.

      2. Que la lista mire las DOS puertas por las que se cae un
         fichaje. Solo mirar el veto de `as_xi` se deja fuera a
         Exposito, que es el mejor candidato del tablero: a el no
         le vetan, le gana la reventa en el `max()` por euros.

      3. Que no ejecute nada, no toque `acquisition_valuation.py`
         y no la lea ningun motor.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.roster_expansion_shadow import (
    blocked_reason,
    build_roster_expansion_shadow,
    count_free_slots,
    not_signable_reason,
)


def _ledger(nuestras: int = 14, mayor: int = 17) -> dict:
    return {
        "available": True,
        "by_manager": [
            {"name": "Pollo17", "is_us": False, "roster_size": mayor},
            {"name": "Mex", "is_us": False, "roster_size": 14},
            {"name": "Pepe", "is_us": True, "roster_size": nuestras},
            {"name": "Manzagool", "is_us": False, "roster_size": 12},
        ],
    }


def _fila(nombre, valor_temporada, **campos) -> dict:
    base = {
        "id": abs(hash(nombre)) % 10_000,
        "name": nombre,
        "position": 3,
        "market_price": 1_000_000,
        "our_value": 1_010_000,
        "expected_points": 76,
        "starter_probability": 80.0,
        "starter_consensus": "STARTER",
        "intent": "SPECULATION",
        "xi_decision": "NO_MEJORA_JERARQUIA",
        "xi_reason": "No le gana al peor titular.",
        "reason": "Como especulacion rinde poco.",
        "season_horizon": {
            "season_value": valor_temporada,
            "season_points_remaining": 70.0,
            "current_value": 1_010_000,
            "cost_per_point": 14_000,
            "beats_market_rate": True,
            "starter_known": True,
            "caveat": None,
        },
    }
    base.update(campos)
    return base


def _sombra(filas) -> dict:
    return {"rows": filas}


# ============================================================
# 1. LOS HUECOS, SIN INVENTARSE EL TOPE
# ============================================================


def test_los_huecos_se_cuentan_contra_el_mayor_de_la_liga() -> None:
    h = count_free_slots(_ledger(nuestras=14, mayor=17))

    assert h["known"] is True
    assert h["our_roster_size"] == 14
    assert h["largest_roster_in_league"] == 17
    assert h["free_slots"] == 3


def test_los_huecos_se_publican_como_cota_inferior() -> None:
    """
    El tope real de Biwenger no esta en el codigo ni comprobado.
    Publicar un 3 a secas seria afirmar algo que no sabemos.
    """

    h = count_free_slots(_ledger())

    assert h["is_lower_bound"] is True
    assert "INFERIOR" in h["reason"], (
        "tiene que decirlo con todas las letras en el propio JSON"
    )
    assert "no esta en el codigo ni comprobado" in h["reason"]


def test_con_la_plantilla_mas_grande_no_hay_huecos() -> None:
    h = count_free_slots(_ledger(nuestras=17, mayor=17))

    assert h["free_slots"] == 0, "no se inventan huecos que no hay"


def test_sin_ledger_no_se_cuentan_huecos() -> None:
    for basura in (None, {}, {"by_manager": []}):
        h = count_free_slots(basura)
        assert h["known"] is False
        assert h["free_slots"] is None
        assert h["reason"]


def test_sin_saber_quienes_somos_no_hay_huecos() -> None:
    ledger = _ledger()
    for m in ledger["by_manager"]:
        m["is_us"] = False

    h = count_free_slots(ledger)

    assert h["known"] is False, (
        "contar los huecos de otro y llamarlos nuestros seria peor "
        "que no contarlos"
    )


# ============================================================
# 2. LAS DOS PUERTAS
# ============================================================


def test_el_veto_del_once_es_una_puerta() -> None:
    motivo = blocked_reason(
        _fila("Vetado", 1_000_000, xi_decision="NO_MEJORA_JERARQUIA")
    )

    assert motivo is not None
    assert motivo[0] == "NO_MEJORA_JERARQUIA"


def test_el_intent_por_euros_es_la_otra() -> None:
    """
    EL CASO EXPOSITO.

    No esta vetado: la via del once le da valor -"Suma 81
    puntos"-. Lo que pasa es que el `intent` se elige por euros,
    gana la reventa, y entonces se le exige rendimiento de
    especulacion: "rinde un 0,59 % y se exige al menos un 3 %".

    Una lista de "que ficharia si pudiera" que solo mire el veto
    se deja fuera al mejor candidato del tablero.
    """

    motivo = blocked_reason(
        _fila(
            "Exposito",
            3_927_892,
            xi_decision=None,
            xi_reason="Suma 81 puntos.",
            intent="SPECULATION",
        )
    )

    assert motivo is not None, (
        "Exposito no esta vetado y aun asi no ficha: eso tambien "
        "cuenta"
    )
    assert motivo[0] == "INTENT_POR_EUROS"
    assert "por euros" in motivo[1]


def test_quien_si_entra_al_once_no_esta_bloqueado() -> None:
    motivo = blocked_reason(
        _fila("Entra", 1_000_000, xi_decision=None, intent="XI_UPGRADE")
    )

    assert motivo is None, (
        "quien ya ficha para el once no necesita una via nueva"
    )



# ============================================================
# A QUIEN NO SE PUEDE FICHAR
# ============================================================


def test_un_jugador_nuestro_no_es_un_fichaje() -> None:
    """
    SALIO CON LA FOTO DE PRODUCCION (05/09/2026).

    La lista proponia fichar a Gustavo Puerta. Es NUESTRO: la
    fila esta en el tablero porque Luismi_Haz nos ha ofrecido
    4,47 M por el. "Es dinero a cobrar, no a pagar."
    """

    motivo = not_signable_reason(
        _fila("Gustavo Puerta", 3_126_281, decision="CONTRAOFERTA")
    )

    assert motivo is not None
    assert "nuestro" in motivo


def test_lo_nuestro_se_reconoce_tambien_por_el_vendedor() -> None:
    motivo = not_signable_reason(
        _fila("Mio", 1_000_000, seller_id=14175949),
        current_user_id=14175949,
    )

    assert motivo is not None and "nuestro" in motivo


def test_un_lesionado_no_ocupa_una_ficha_libre() -> None:
    """
    Calero salia como el mejor chollo por punto de todo el
    tablero -11.649 EUR el punto contra 21.758 del mercado-. Esta
    lesionado.
    """

    for fila in (
        _fila("Calero", 1_923_865, decision="NO_DISPONIBLE",
              status="injured"),
        _fila("Otro", 1_000_000, status="injured"),
        _fila("Sancionado", 1_000_000, status="sanctioned"),
    ):
        motivo = not_signable_reason(fila)
        assert motivo is not None, f"{fila['name']} deberia quedar fuera"
        assert "no puede jugar" in motivo


def test_un_fichable_normal_si_pasa() -> None:
    assert not_signable_reason(_fila("Fulano", 1_000_000)) is None


def test_los_no_fichables_no_llegan_a_la_lista() -> None:
    filas = [
        _fila("Nuestro", 9_000_000, decision="CONTRAOFERTA"),
        _fila("Lesionado", 8_000_000, decision="NO_DISPONIBLE",
              status="injured"),
        _fila("Fichable", 1_000_000),
    ]

    r = build_roster_expansion_shadow(_sombra(filas), _ledger())

    nombres = [c["name"] for c in r["candidates"]]

    assert nombres == ["Fichable"], (
        f"proponer fichar a alguien nuestro o lesionado: {nombres}"
    )


def test_se_dice_a_quien_se_ha_dejado_fuera_y_por_que() -> None:
    """
    Una lista mas corta sin explicacion parece una lista pobre.
    """

    r = build_roster_expansion_shadow(
        _sombra([
            _fila("Nuestro", 9_000_000, decision="CONTRAOFERTA"),
            _fila("Fichable", 1_000_000),
        ]),
        _ledger(),
    )

    assert len(r["not_signable"]) == 1
    assert r["not_signable"][0]["name"] == "Nuestro"
    assert r["not_signable"][0]["reason"]


# ============================================================
# 3. LA LISTA
# ============================================================


def test_entran_los_mejores_a_temporada_y_solo_los_que_caben() -> None:
    filas = [
        _fila("Caro y bueno", 3_900_000),
        _fila("Bueno", 3_100_000),
        _fila("Normalito", 2_800_000),
        _fila("El cuarto", 1_000_000),
    ]

    r = build_roster_expansion_shadow(_sombra(filas), _ledger())

    assert r["available"] is True
    assert len(r["candidates"]) == 3, "tres fichas libres, tres nombres"
    assert [c["name"] for c in r["candidates"]] == [
        "Caro y bueno", "Bueno", "Normalito",
    ], "ordenados por lo que valen de aqui a la 38"


def test_la_lista_dice_por_que_no_entran_hoy() -> None:
    r = build_roster_expansion_shadow(
        _sombra([_fila("Fulano", 3_000_000)]), _ledger()
    )

    c = r["candidates"][0]

    assert c["blocked_by"], "sin esto la lista parece un capricho"
    assert c["blocked_reason"]


def test_la_lista_arrastra_los_peros_de_la_valoracion() -> None:
    fila = _fila("Sin dato", 3_000_000)
    fila["season_horizon"]["starter_known"] = False
    fila["season_horizon"]["caveat"] = "Sin pronostico de titularidad."

    r = build_roster_expansion_shadow(_sombra([fila]), _ledger())

    assert r["candidates"][0]["starter_known"] is False
    assert r["candidates"][0]["caveat"], (
        "un candidato sin pronostico no puede llegar a esta lista "
        "limpio de peros"
    )


def test_se_suman_coste_y_puntos() -> None:
    filas = [_fila(f"J{i}", 3_000_000 - i) for i in range(3)]

    r = build_roster_expansion_shadow(_sombra(filas), _ledger())

    assert r["total_cost"] == 3_000_000, "tres fichas de un millon"
    assert r["total_season_points"] == 210.0, "y 70 puntos cada una"


def test_sin_valor_de_temporada_no_se_ordena_por_nada() -> None:
    fila = _fila("Sin valor", None)
    fila["season_horizon"]["season_value"] = None

    r = build_roster_expansion_shadow(_sombra([fila]), _ledger())

    assert r["available"] is False
    assert r["candidates"] == []
    assert r["reason"], "y se dice por que la lista esta vacia"


def test_sin_saber_los_huecos_la_lista_sigue_siendo_util() -> None:
    filas = [_fila(f"J{i}", 3_000_000 - i) for i in range(12)]

    r = build_roster_expansion_shadow(_sombra(filas), None)

    assert r["slots"]["known"] is False, "los huecos no se saben"
    assert len(r["candidates"]) == 10, (
        "pero los diez mejores se pueden enseñar igual: lo que no "
        "se sabe se dice, no se rellena con un numero"
    )


def test_nunca_lanza() -> None:
    for basura in (None, {}, {"rows": None}, {"rows": "no"},
                   {"rows": [None, 3]}):
        r = build_roster_expansion_shadow(basura, None)
        assert isinstance(r, dict), f"revento con {basura!r}"
        assert r["available"] is False


# ============================================================
# 4. NO EJECUTA, NO TOCA, NO MANDA
# ============================================================


def test_no_se_ha_tocado_la_valoracion() -> None:
    fuente = Path("src/analysis/acquisition_valuation.py").read_text(
        encoding="utf-8"
    )

    assert "roster_expansion" not in fuente, (
        "la via de ampliar plantilla ha entrado en la valoracion "
        "que decide"
    )

    # Y la regla del once sigue donde estaba: comparar contra el
    # peor TITULAR, que es lo que evito el bucle de las catorce
    # defensas.
    assert "peor TITULAR" in fuente, (
        "la regla del once ha cambiado: eso es cambiar decisiones"
    )


MOTORES = [
    "src/analysis/acquisition_valuation.py",
    "src/analysis/acquisition_board.py",
    "src/analysis/speculation_engine.py",
    "src/analysis/rival_bid_model.py",
    "src/analysis/acquisition_budget.py",
    "src/analysis/decision_orchestrator.py",
    "src/analysis/lineup_engine.py",
    "src/analysis/offer_decision_engine.py",
    "src/analysis/sales_analyzer.py",
    "src/autopilot.py",
    "src/v10_full_autonomous_live.py",
]


def test_ningun_motor_lee_la_lista() -> None:
    culpables = [
        ruta
        for ruta in MOTORES
        if Path(ruta).exists()
        and "roster_expansion_shadow" in Path(ruta).read_text(
            encoding="utf-8"
        )
    ]

    assert not culpables, (
        f"la via de ampliar plantilla ha entrado en una ruta de "
        f"decision: {culpables}"
    )


def test_la_lista_no_arrastra_el_sistema() -> None:
    arbol = ast.parse(
        Path("src/analysis/roster_expansion_shadow.py").read_text(
            encoding="utf-8"
        )
    )

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.ImportFrom):
            modulo = nodo.module or ""
        elif isinstance(nodo, ast.Import):
            modulo = nodo.names[0].name
        else:
            continue

        assert not modulo.startswith("src."), (
            f"la lista importa {modulo}: solo tiene que ordenar "
            f"filas ya calculadas"
        )


def test_el_dashboard_lo_publica() -> None:
    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert '"roster_expansion": roster_expansion' in fuente, (
        "la via de ampliar plantilla no llega a `status.json`"
    )

    # Con sus tres entradas ya construidas. Si se calculara antes,
    # el try/except se lo tragaria y el bloque saldria vacio para
    # siempre.
    for antes in (
        "season_horizon = build_season_horizon_shadow(",
        "ledger_audit = audit_rival_ledger(",
        "exposure = compact_exposure(state)",
    ):
        assert fuente.index(antes) < fuente.index(
            "roster_expansion = build_roster_expansion_shadow("
        ), f"se construye antes de tener {antes.split(' =')[0]}"


def test_se_declara_observador_en_el_propio_json() -> None:
    r = build_roster_expansion_shadow(
        _sombra([_fila("Fulano", 3_000_000)]), _ledger()
    )

    assert r["observer_only"] is True


TESTS = [
    test_los_huecos_se_cuentan_contra_el_mayor_de_la_liga,
    test_los_huecos_se_publican_como_cota_inferior,
    test_con_la_plantilla_mas_grande_no_hay_huecos,
    test_sin_ledger_no_se_cuentan_huecos,
    test_sin_saber_quienes_somos_no_hay_huecos,
    test_el_veto_del_once_es_una_puerta,
    test_el_intent_por_euros_es_la_otra,
    test_quien_si_entra_al_once_no_esta_bloqueado,
    test_un_jugador_nuestro_no_es_un_fichaje,
    test_lo_nuestro_se_reconoce_tambien_por_el_vendedor,
    test_un_lesionado_no_ocupa_una_ficha_libre,
    test_un_fichable_normal_si_pasa,
    test_los_no_fichables_no_llegan_a_la_lista,
    test_se_dice_a_quien_se_ha_dejado_fuera_y_por_que,
    test_entran_los_mejores_a_temporada_y_solo_los_que_caben,
    test_la_lista_dice_por_que_no_entran_hoy,
    test_la_lista_arrastra_los_peros_de_la_valoracion,
    test_se_suman_coste_y_puntos,
    test_sin_valor_de_temporada_no_se_ordena_por_nada,
    test_sin_saber_los_huecos_la_lista_sigue_siendo_util,
    test_nunca_lanza,
    test_no_se_ha_tocado_la_valoracion,
    test_ningun_motor_lee_la_lista,
    test_la_lista_no_arrastra_el_sistema,
    test_el_dashboard_lo_publica,
    test_se_declara_observador_en_el_propio_json,
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
    print(f"AMPLIAR PLANTILLA SOMBRA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
