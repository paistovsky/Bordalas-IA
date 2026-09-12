"""
El libro de pujas no sabia perder.

SINTOMA (12/09/2026)

    Cuatro pujas de la misma tanda, en la ventana del reset:

        04:46:55  Caceres      1.503.751  -> PENDING
        04:46:55  Fortuño        150.376  -> WON
        04:46:55  Diego Conde    240.601  -> WON
        04:52:15  Sotelo       1.604.001  -> PENDING

    Las cuatro se resolvieron a las 07:00 del mismo dia. Caceres
    y Sotelo no estan en la plantilla: se perdieron.

    El libro publicaba `lost: 0` y `win_rate: 1.0` sobre 5 pujas
    — en una liga donde el 76 % de las subastas estan disputadas.

CAUSA

    El detector sabia reconocer una VICTORIA: el jugador aparece
    en una operacion del tablon comprada por nosotros. No tenia
    forma de reconocer una DERROTA cuando el tablon no traia la
    operacion; sin candidata se quedaba PENDING hasta caducar a
    UNKNOWN 72 horas despues.

    Septimo caso del mismo patron: un valor por defecto se traga
    el caso importante. Y el que se traga aqui es EL UNICO QUE
    ENSEÑA ALGO — ganar no dice cuanto habia que pujar; perder,
    si.

CONSECUENCIA

    O la tienes o no la tienes. Una puja cuyo reset ya paso y
    cuyo jugador no esta en la plantilla es LOST. PENDING se
    queda solo para las que aun no han llegado a su reset.

    Y con dos frenos, porque inventar derrotas seria peor:

        sin plantilla conocida     no se marca nada
        plantilla vacia            no se marca nada (regla 24)

REGLA 23

    No lee estado externo: el libro se construye entero aqui.
"""

from __future__ import annotations

import ast

from pathlib import Path


RAIZ = Path(__file__).parents[2]


# EL CASO REAL DEL 12/09/2026, con las horas tal cual.
#
#     04:46:55 y 04:52:15 de Madrid son 02:46:55 y 02:52:15 UTC
#     (verano, UTC+2). El reset que las resuelve es el de las
#     07:00 de Madrid del mismo dia = 05:00 UTC.
CACERES = {
    "player_id": 5001,
    "player_name": "Cáceres",
    "amount": 1_503_751,
    "placed_at": "2026-09-12T02:46:55+00:00",
    "outcome": "PENDING",
}

SOTELO = {
    "player_id": 5002,
    "player_name": "Sotelo",
    "amount": 1_604_001,
    "placed_at": "2026-09-12T02:52:15+00:00",
    "outcome": "PENDING",
}

FORTUNO = {
    "player_id": 5003,
    "player_name": "Fortuño",
    "amount": 150_376,
    "placed_at": "2026-09-12T02:46:55+00:00",
    "outcome": "WON",
}

DIEGO_CONDE = {
    "player_id": 5004,
    "player_name": "Diego Conde",
    "amount": 240_601,
    "placed_at": "2026-09-12T02:46:55+00:00",
    "outcome": "WON",
}

# La plantilla de despues del reset: los dos porteros SI, los dos
# de 1,5 M no.
PLANTILLA = [
    {"id": 5003, "name": "Fortuño"},
    {"id": 5004, "name": "Diego Conde"},
    {"id": 1599, "name": "Jonny"},
]

# Ya paso el reset de las 07:00 de Madrid (05:00 UTC).
DESPUES_DEL_RESET = "2026-09-12T09:30:00+00:00"

ANTES_DEL_RESET = "2026-09-12T04:30:00+00:00"


def _libro(entradas) -> dict:
    return {
        "version": 1,
        "bids": {
            str(e["player_id"]): dict(e) for e in entradas
        },
    }


def _cerrar(entradas, roster, ahora) -> dict:
    from src.intelligence.bid_outcome_ledger import reconcile

    return reconcile(
        [],                       # tablon vacio: es el caso
        our_user_id=777,
        ledger=_libro(entradas),
        save=False,
        ahora=ahora,
        roster=roster,
    )


# ============================================================
# 1. UNA PUJA PERDIDA SE ANOTA COMO PERDIDA
# ============================================================


def test_una_puja_perdida_se_anota_como_perdida() -> None:
    """
    EL CASO REAL DEL 12/09, entero.

    Cáceres y Sotelo puestas a las 04:46 y 04:52, reset del 12/09
    ya pasado, no en plantilla -> LOST. Y el `win_rate` deja de
    ser 1.0, que es el numero que hacia creer que no perdemos
    nunca.
    """

    from src.intelligence.bid_outcome_ledger import summary

    libro = _cerrar(
        [CACERES, SOTELO, FORTUNO, DIEGO_CONDE],
        PLANTILLA,
        DESPUES_DEL_RESET,
    )

    visto = {
        v["player_name"]: v["outcome"]
        for v in libro["bids"].values()
    }

    assert visto["Cáceres"] == "LOST", visto
    assert visto["Sotelo"] == "LOST", visto

    # Y las que SI ganamos siguen ganadas.
    assert visto["Fortuño"] == "WON", visto
    assert visto["Diego Conde"] == "WON", visto

    # Queda dicho POR QUE se cerraron, que no fue por el tablon.
    for nombre in ("5001", "5002"):
        assert libro["bids"][nombre]["resolved_by"] == (
            "RESET_SIN_JUGADOR"
        ), libro["bids"][nombre]

    resumen = summary(libro)

    assert resumen["lost"] == 2, resumen
    assert resumen["won"] == 2, resumen

    assert resumen["win_rate"] != 1.0, (
        "el win_rate sigue diciendo que no perdemos nunca"
    )

    assert abs(resumen["win_rate"] - 0.5) < 1e-9, resumen


def test_pending_solo_hasta_que_llega_su_reset() -> None:
    """
    PENDING tiene que significar "todavia no se sabe", no "no lo
    miro nadie".

    Antes del reset de las 07:00 la puja sigue viva de verdad y
    no se toca. Es la mitad que impide que esto marque derrotas
    inventadas.
    """

    antes = _cerrar(
        [CACERES, SOTELO], PLANTILLA, ANTES_DEL_RESET
    )

    for entrada in antes["bids"].values():
        assert entrada["outcome"] == "PENDING", entrada

    # Y un minuto DESPUES del reset, ya no.
    despues = _cerrar(
        [CACERES, SOTELO],
        PLANTILLA,
        "2026-09-12T05:01:00+00:00",
    )

    for entrada in despues["bids"].values():
        assert entrada["outcome"] == "LOST", entrada


def test_sin_plantilla_no_se_inventa_ninguna_derrota() -> None:
    """
    LOS DOS FRENOS.

    Un libro que inventa derrotas es peor que uno que no mide:
    envenena todo lo que se calcule con el. Distinguir "no esta"
    de "no se sabe" es doctrina 36, y aqui las dos salidas se
    parecen mucho.
    """

    # 1. Sin roster: no se sabe quien esta.
    sin_saber = _cerrar(
        [CACERES, SOTELO], None, DESPUES_DEL_RESET
    )

    for entrada in sin_saber["bids"].values():
        assert entrada["outcome"] == "PENDING", entrada

    # 2. Roster vacio: tenemos 15 jugadores, asi que una lista
    #    vacia es una lectura rota, no una plantilla sin nadie.
    #    Tratarla como buena marcaria TODO como perdido.
    vacia = _cerrar([CACERES, SOTELO], [], DESPUES_DEL_RESET)

    for entrada in vacia["bids"].values():
        assert entrada["outcome"] == "PENDING", entrada


def test_el_reset_se_calcula_en_madrid_y_vuelve_a_utc() -> None:
    """
    LA DOCTRINA 35, QUE CASI SE COLA OTRA VEZ.

    `_hora_de_madrid` devuelve la HORA DE PARED de Madrid,
    todavia etiquetada UTC. La primera version de esto devolvia
    ese valor tal cual: "07:00+00:00", que como INSTANTE son las
    09:00 de Madrid.

    Dos horas tarde, y las pujas de la ventana se habrian quedado
    sin resolver toda la mañana — justo las que mas importan.
    """

    from datetime import datetime, timezone

    from src.intelligence.bid_outcome_ledger import (
        _reset_que_la_resuelve,
    )

    # 04:46:55 de Madrid -> el reset es 05:00 UTC (07:00 Madrid).
    reset = _reset_que_la_resuelve(CACERES["placed_at"])

    assert reset == datetime(
        2026, 9, 12, 5, 0, tzinfo=timezone.utc
    ), reset

    # Una puja DESPUES del reset se resuelve en el del dia
    # siguiente, no en el que ya paso.
    manana = _reset_que_la_resuelve(
        "2026-09-12T06:00:00+00:00"      # 08:00 de Madrid
    )

    assert manana == datetime(
        2026, 9, 13, 5, 0, tzinfo=timezone.utc
    ), manana

    # Sin poder calcularlo, `None` — y entonces no se marca nada.
    assert _reset_que_la_resuelve("esto no es una fecha") is (
        None
    )


# ============================================================
# 2. QUIEN LEE EL LIBRO, Y QUE DECIDE CON EL
# ============================================================


def test_la_prima_de_puja_no_se_calibra_con_nuestro_libro() -> None:
    """
    LA PREGUNTA DEL DUEÑO: ¿llevamos dias calibrando la prima de
    puja sobre «nunca perdemos»?

    NO. Y conviene que quede probado, no dicho.

    `calibrate_premium_curve` se calibra con las pujas de LOS
    RIVALES observadas en el tablon (`managers`), no con nuestro
    libro. Nuestro libro es de solo lectura para las decisiones:
    se escribe al pujar y se pinta en un panel.

    Si algun dia alguien lo conecta a la calibracion, esta
    guardia se pone roja y habra que venir a leer por que
    importaba.
    """

    # Sin comentarios ni docstrings: los dos CUENTAN el
    # incidente y nombran `win_rate`. Una definicion, la del
    # guardia hermano, para no tener dos.
    from src.analysis.test_el_plato_del_carril_v1 import (
        _codigo_vivo,
    )

    modelo = _codigo_vivo(
        (
            RAIZ / "src" / "analysis" / "rival_bid_model.py"
        ).read_text(encoding="utf-8")
    )

    for prohibido in (
        "bid_outcome_ledger",
        "win_rate",
        "sync_bid_outcomes",
    ):
        assert prohibido not in modelo, (
            f"`rival_bid_model` lee `{prohibido}`: la prima de "
            f"puja se estaria calibrando con nuestro propio "
            f"libro de resultados"
        )

    # Y al reves: quien SI lo lee, solo lo enseña.
    lectores = []

    for ruta in (RAIZ / "src").rglob("*.py"):

        if ruta.name.startswith("test_"):
            continue

        texto = _codigo_vivo(
            ruta.read_text(encoding="utf-8")
        )

        if "win_rate" in texto:
            lectores.append(ruta.name)

    # Solo el propio libro lo calcula. Nadie mas en Python lo
    # lee para decidir.
    assert lectores == ["bid_outcome_ledger.py"], lectores


def test_el_ciclo_le_pasa_la_plantilla_al_libro() -> None:
    """
    Sin plantilla, el arreglo no hace nada — y no haria ruido.
    """

    fuente = (RAIZ / "src" / "autopilot.py").read_text(
        encoding="utf-8"
    )

    arbol = ast.parse(fuente)

    con_roster = False

    for nodo in ast.walk(arbol):

        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id == "sync_bid_outcomes"
        ):
            con_roster = any(
                k.arg == "roster" for k in nodo.keywords
            )

    assert con_roster, (
        "el ciclo no le pasa la plantilla al libro de pujas: sin "
        "ella no se puede reconocer una derrota y todo vuelve a "
        "quedarse en PENDING"
    )


TESTS = [
    test_una_puja_perdida_se_anota_como_perdida,
    test_pending_solo_hasta_que_llega_su_reset,
    test_sin_plantilla_no_se_inventa_ninguna_derrota,
    test_el_reset_se_calcula_en_madrid_y_vuelve_a_utc,
    test_la_prima_de_puja_no_se_calibra_con_nuestro_libro,
    test_el_ciclo_le_pasa_la_plantilla_al_libro,
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
        f"EL LIBRO SABE PERDER V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
