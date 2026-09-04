"""
Las plantillas rivales, con jugadores dentro.

SINTOMA

    `status.json` publicaba `rival_squads.available: true` y, en
    los SIETE managers, `squad_size: 0` y `players: []`. La
    pantalla de plantillas rivales llevaba en blanco desde que se
    hizo.

CAUSA

    Salian de `standings[].lineup` -`players` mas `discarded`-,
    que es la alineacion que dejo puesta cada manager, y venia
    vacia. Mientras tanto `ledger_audit` conocia los rosters de
    todos: 17, 14, 13, 12 jugadores. Habia dos fuentes en casa y
    se estaba pintando la vacia.

CONSECUENCIA

    Dos mentiras, no una. La primera, no ver las plantillas. La
    segunda, peor: publicar `available: true` sin datos. Una
    tabla en blanco marcada como disponible se lee como "el rival
    no tiene jugadores", no como "no lo sabemos", y esa confusion
    no se detecta mirando la pantalla, que es justo para lo que
    esta la pantalla.

    Esta guardia protege las dos: que la plantilla salga del
    ledger, y que "disponible" no pueda significar "vacio".
"""

from __future__ import annotations

from pathlib import Path

from src.telemetry.squads import build_rival_squads


NOSOTROS = 14175949
RIVAL = 777


# ============================================================
# UN SNAPSHOT CON LA FORMA DEL DE VERDAD
# ============================================================


def _catalogo(ids) -> dict:
    return {
        "data": {
            "players": {
                str(player_id): {
                    "id": player_id,
                    "name": f"Jugador {player_id}",
                    "position": 1 + (player_id % 4),
                    "price": 1_000_000,
                    "priceIncrement": 1_000,
                    "points": 7,
                    "pointsLastSeason": 100,
                    "status": "ok",
                    "teamID": 1,
                }
                for player_id in ids
            }
        }
    }


def _snapshot(once=None, banquillo=None, todos=None) -> dict:
    once = once or []
    banquillo = banquillo or []
    todos = todos or (once + banquillo)

    def fila(user_id, nombre, posicion):
        return {
            "id": user_id,
            "name": nombre,
            "position": posicion,
            "points": 40,
            "teamValue": 50_000_000,
            "lineup": {
                "type": "4-4-2",
                "players": list(once),
                "discarded": list(banquillo),
            },
        }

    return {
        "catalog": _catalogo(todos),
        "rounds": {
            "data": {
                "league": {
                    "standings": [
                        fila(RIVAL, "Rival", 1),
                        fila(NOSOTROS, "Pepe Bordalás", 2),
                    ]
                }
            }
        },
    }


def _ledger(por_manager: dict) -> dict:
    """El informe de rivales, con su roster reconstruido."""
    return {
        "managers": [
            {
                "user_id": user_id,
                "name": f"Manager {user_id}",
                "roster": [{"id": player_id} for player_id in ids],
            }
            for user_id, ids in por_manager.items()
        ]
    }


def _de(salida: dict, user_id: int) -> dict:
    return next(
        m for m in salida["managers"] if m["user_id"] == user_id
    )


# ============================================================
# EL FALLO QUE SE ARREGLA
# ============================================================


def test_la_plantilla_sale_del_ledger_cuando_la_alineacion_viene_vacia() -> None:
    """El caso exacto de produccion: siete managers, cero jugadores."""

    roster_rival = list(range(100, 117))          # 17 jugadores
    roster_mio = list(range(200, 214))            # 14 jugadores

    salida = build_rival_squads(
        _snapshot(todos=roster_rival + roster_mio),
        current_user_id=NOSOTROS,
        rival_intelligence=_ledger(
            {RIVAL: roster_rival, NOSOTROS: roster_mio}
        ),
    )

    assert salida["available"] is True, "hay plantillas, y se dice"
    assert _de(salida, RIVAL)["squad_size"] == 17, (
        "los 17 del ledger, no los 0 de la alineacion"
    )
    assert _de(salida, NOSOTROS)["squad_size"] == 14, "y los 14 mios"
    assert _de(salida, RIVAL)["squad_source"] == "LEDGER", (
        "y se dice de donde salieron"
    )


def test_disponible_no_puede_significar_vacio() -> None:
    """
    LA GUARDIA DE VERDAD.

    Publicar "disponible" sin datos es peor que decir que no hay:
    la pantalla en blanco se lee como "no tiene jugadores".
    """

    salida = build_rival_squads(
        _snapshot(todos=[]),
        current_user_id=NOSOTROS,
        rival_intelligence=None,
    )

    assert salida["available"] is False, (
        "sin una sola plantilla, disponible es mentira"
    )
    assert salida["reason"], "y hay que decir por que no hay"

    for manager in salida["managers"]:
        assert manager["squad_reason"], (
            "cada tabla en blanco dice por que esta en blanco"
        )


def test_la_invariante_disponible_implica_jugadores() -> None:
    """Ninguna combinacion puede dar `available: true` con todo vacio."""

    casos = [
        # (once, banquillo, ledger)
        ([], [], None),
        ([], [], _ledger({RIVAL: [], NOSOTROS: []})),
        ([], [], {"managers": []}),
        ([], [], {}),
    ]

    for once, banquillo, ledger in casos:
        salida = build_rival_squads(
            _snapshot(once=once, banquillo=banquillo, todos=[]),
            current_user_id=NOSOTROS,
            rival_intelligence=ledger,
        )

        con_jugadores = [
            m for m in salida["managers"] if m["players"]
        ]

        assert not (salida["available"] and not con_jugadores), (
            f"available: true sin un solo jugador, con ledger={ledger}"
        )


# ============================================================
# QUE FUENTE MANDA
# ============================================================


def test_el_ledger_manda_sobre_la_alineacion() -> None:
    """
    La alineacion dice a quien puso el sabado. El perfil dice a
    quien TIENE. Una plantilla es lo segundo.
    """

    once = list(range(100, 111))
    banquillo = [111, 112]
    roster = list(range(100, 117))                # los 17 de verdad

    salida = build_rival_squads(
        _snapshot(once=once, banquillo=banquillo, todos=roster),
        current_user_id=NOSOTROS,
        rival_intelligence=_ledger({RIVAL: roster}),
    )

    assert _de(salida, RIVAL)["squad_size"] == 17, (
        "con 13 alineados y 17 en propiedad, la plantilla son 17"
    )


def test_sin_ledger_se_cae_a_la_alineacion() -> None:
    """Lo que habia sigue funcionando: no se cambia una fuente por nada."""

    once = list(range(100, 111))
    banquillo = [111, 112]

    salida = build_rival_squads(
        _snapshot(once=once, banquillo=banquillo),
        current_user_id=NOSOTROS,
        rival_intelligence=None,
    )

    rival = _de(salida, RIVAL)

    assert rival["squad_size"] == 13, "once mas dos descartados"
    assert rival["squad_source"] == "LINEUP", "y se dice que es el respaldo"


def test_el_titular_se_sigue_marcando_desde_la_alineacion() -> None:
    """
    El ledger no sabe quien es titular; la alineacion si. Se usan
    las dos, cada una para lo suyo.
    """

    once = list(range(100, 111))
    roster = list(range(100, 117))

    salida = build_rival_squads(
        _snapshot(once=once, banquillo=[], todos=roster),
        current_user_id=NOSOTROS,
        rival_intelligence=_ledger({RIVAL: roster}),
    )

    rival = _de(salida, RIVAL)

    titulares = [j for j in rival["players"] if j["is_starter"]]

    assert len(titulares) == 11, "los once alineados siguen marcados"
    assert rival["squad_size"] == 17, "y los otros seis tambien salen"


def test_un_jugador_no_sale_dos_veces() -> None:
    """Si el mismo id llega por dos sitios, es un jugador, no dos."""

    salida = build_rival_squads(
        _snapshot(once=[100, 100, 101], banquillo=[101, 102]),
        current_user_id=NOSOTROS,
        rival_intelligence=None,
    )

    rival = _de(salida, RIVAL)
    ids = [j["id"] for j in rival["players"]]

    assert len(ids) == len(set(ids)) == 3, f"salieron {ids}"


def test_un_manager_sin_roster_no_arrastra_a_los_demas() -> None:
    """Media pantalla es media pantalla, y se dice cuanta."""

    roster = list(range(100, 117))

    salida = build_rival_squads(
        _snapshot(todos=roster),
        current_user_id=NOSOTROS,
        rival_intelligence=_ledger({RIVAL: roster}),
    )

    assert salida["available"] is True, "el que si tiene plantilla se pinta"
    assert salida["managers_with_squad"] == 1, "uno de dos"
    assert salida["managers_total"] == 2, "y se dice sobre cuantos"
    assert _de(salida, NOSOTROS)["squad_reason"], (
        "y el que falta explica que le falta"
    )


# ============================================================
# QUE EL DASHBOARD USE DE VERDAD LA FUENTE BUENA
# ============================================================


def test_el_dashboard_le_pasa_el_ledger() -> None:
    """
    Arreglar la funcion y no enchufarla dejaria el fallo intacto,
    que es exactamente como llevaba desde el 20/08.
    """

    fuente = (
        Path(__file__).parent.parent
        / "telemetry"
        / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert "rival_intelligence=rival_intelligence" in fuente, (
        "build_rival_squads vuelve a pintar la fuente vacia"
    )


TESTS = [
    test_la_plantilla_sale_del_ledger_cuando_la_alineacion_viene_vacia,
    test_disponible_no_puede_significar_vacio,
    test_la_invariante_disponible_implica_jugadores,
    test_el_ledger_manda_sobre_la_alineacion,
    test_sin_ledger_se_cae_a_la_alineacion,
    test_el_titular_se_sigue_marcando_desde_la_alineacion,
    test_un_jugador_no_sale_dos_veces,
    test_un_manager_sin_roster_no_arrastra_a_los_demas,
    test_el_dashboard_le_pasa_el_ledger,
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
    print(f"PLANTILLAS RIVALES LLENAS V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
