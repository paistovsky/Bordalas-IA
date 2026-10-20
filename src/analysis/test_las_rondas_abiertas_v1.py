"""
Primeros en lo cerrado no es ir primeros.

SINTOMA (19/10/2026, tarde)

    El panel de LA CARRERA decia LIDER: 323 contra los 320 de
    Pollo17. El dueño, con la app delante: la J8 sigue abierta
    por el Rayo-Athletic suspendido, y en ella Pollo hizo 74 y
    nosotros 44. Al cerrarla vamos SEGUNDOS, a unos 27.

CAUSA

    `standings[].points` es la clasificacion de Biwenger, y
    Biwenger solo suma una ronda cuando la cierra. El partido
    aplazado se juega como ronda aparte (el Levante-Athletic de
    la J6, el 21/10) y todo lo de una ronda abierta es invisible
    para la clasificacion. `race_state` solo miraba eso.

    Lo que lleva cada manager en una ronda abierta no lo publica
    ninguna fuente del ciclo, asi que no se suma: se dice que
    rondas faltan, cuanto pueden mover, y no se dice LIDER si la
    ventaja no llega.

LO QUE VIGILA

    1. Con la foto del 19/10 (3 de ventaja, J8 y J9 abiertas) la
       etiqueta NO es LIDER y la frase no dice "Vas 1º" a secas.
    2. Las rondas abiertas salen del tablon: empezada y sin
       cerrar. Reemisiones, basura y "no se sabe" bien tratados.
    3. El margen se mide en el tablon y tiene suelo.
    4. Con ventaja de sobra, o sin nada abierto, SI es LIDER.
    5. Sin tablon no se dice LIDER: SIN_DATOS.
    6. La clasificacion provisional NO se inventa.
    7. El dashboard le pasa el tablon y el panel sabe pintar
       EN_JUEGO. Y la pestaña LIGA (LA CARRERA y LOS RIVALES),
       que es la que mira el dueño, tambien lo dice.
    8. Sigue siendo observador, y nunca lanza.
    9. Las frases no se contradicen: un hueco negativo no es un
       hueco, "sin el tablon" solo si no llego el tablon, y cada
       ronda abierta lleva su fecha de inicio en lo que se pinta.

REGLA 23: datos sinteticos. No lee `data/`, ni la red, ni el
reloj.
"""

from __future__ import annotations

import sys

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.race_state import (                    # noqa: E402
    SUELO_DEL_MARGEN_POR_RONDA,
    build_race_state,
    find_open_rounds,
    measure_round_margin,
)


AHORA = datetime(2026, 10, 19, 21, 30, tzinfo=timezone.utc)

PEPE, POLLO, LUISMI, MEX = 14175949, 14145555, 14156489, 14178736


# ============================================================
# LA FOTO DEL 19/10/2026
# ============================================================


def _managers(pepe=323, pollo=320) -> list:
    crudos = [
        (PEPE, "Pepe Bordalás", pepe, 56_990_000, True),
        (POLLO, "Pollo17", pollo, 106_210_000, False),
        (LUISMI, "Luismi_Haz", 287, 103_770_000, False),
        (MEX, "Mex", 246, 49_320_000, False),
    ]

    filas = sorted(crudos, key=lambda c: -c[2])

    return [
        {
            "user_id": uid,
            "name": nombre,
            "rank": rank,
            "points": puntos,
            "team_value": valor,
            "squad_size": 12,
            "is_current_user": yo,
        }
        for rank, (uid, nombre, puntos, valor, yo) in enumerate(
            filas, start=1
        )
    ]


def _squads(**kwargs) -> dict:
    return {"available": True, "managers": _managers(**kwargs)}


def _calendario() -> dict:
    """38 jornadas, ocho terminadas. Fechas de verdad, no cadenas."""

    return {
        "matchdays": [
            {
                "matchday": n,
                "matches": [{
                    "kickoff": (
                        AHORA + timedelta(days=7 * (n - 8) - 1)
                    ).isoformat(),
                }],
            }
            for n in range(1, 39)
        ]
    }


def _u(uid, nombre):
    return {"id": uid, "name": nombre}


def _empieza(round_id, nombre, fecha, parte=None):
    ronda = {"id": round_id, "name": nombre}
    if parte:
        ronda["part"] = parte
    return {"type": "roundStarted", "date": fecha,
            "content": {"round": ronda, "results": []}}


def _cierra(round_id, nombre, fecha, resultados):
    return {"type": "roundFinished", "date": fecha,
            "content": {"round": {"id": round_id, "name": nombre},
                        "results": resultados}}


def _tablon() -> list:
    """
    J7 cerrada (Luismi nos saca 14), J6 aplazada cerrada (Luismi
    nos saca 35, aunque se le anularon), la J7 reemitida, y la J8
    y la J9 empezadas sin cerrar. La J9 reemitida al empezar.
    """

    j6 = [
        {"user": _u(LUISMI, "Luismi_Haz"), "points": 64, "bonus": None},
        {"user": _u(PEPE, "Pepe Bordalás"), "points": 29},
        {"user": _u(POLLO, "Pollo17"), "points": 17},
    ]
    j7 = [
        {"user": _u(LUISMI, "Luismi_Haz"), "points": 61},
        {"user": _u(POLLO, "Pollo17"), "points": 50},
        {"user": _u(PEPE, "Pepe Bordalás"), "points": 47},
        # Una fila sin puntos (solo prima) no se mide.
        {"user": _u(MEX, "Mex"), "bonus": 1_130_000},
    ]

    return [
        _empieza(5125, "Jornada 6 (aplazada)", 1_789_000_000, parte=2),
        _cierra(5125, "Jornada 6 (aplazada)", 1_789_200_000, j6),
        _empieza(4905, "Jornada 7", 1_789_300_000),
        _cierra(4905, "Jornada 7", 1_789_500_000, j7),
        _cierra(4905, "Jornada 7", 1_789_500_060, j7),
        _empieza(4906, "Jornada 8", 1_791_572_400),
        _empieza(4907, "Jornada 9", 1_792_177_200),
        _empieza(4907, "Jornada 9", 1_792_177_500),
        {"type": "market", "date": 1_792_000_000, "content": []},
    ]


def _sin_la_j8_ni_la_j9() -> list:
    """El mismo tablon con todo lo empezado ya cerrado."""

    return [
        e for e in _tablon()
        if e["type"] != "roundStarted"
        or e["content"]["round"]["id"] not in (4906, 4907)
    ]


def _carrera(eventos=None, **kwargs) -> dict:
    return build_race_state(
        _squads(**kwargs),
        calendar=_calendario(),
        now=AHORA,
        eventos=eventos,
    )


# ============================================================
# 1. LA FOTO DEL 19/10
# ============================================================


def test_la_foto_del_19_10_no_dice_lider() -> None:
    r = _carrera(_tablon())

    assert r["available"] is True
    assert r["is_leader"] is True, (
        "en las rondas cerradas SI vamos primeros: eso no se esconde"
    )
    assert r["points_ahead"] == 3
    assert r["urgency"] != "LIDER", (
        "3 de ventaja con la J8 y la J9 abiertas no es liderato: la "
        "J8 sola ya pone a Pollo17 treinta por delante"
    )
    assert r["urgency"] == "EN_JUEGO", r["urgency"]
    assert r["lider_asegurado"] is False

    assert [x["round_id"] for x in r["jornadas_abiertas"]] == [4906, 4907]

    frase = r["headline"]
    assert not frase.startswith("Vas 1º, con"), (
        f"la frase sigue coronandonos: {frase}"
    )
    assert "solo en las rondas cerradas" in frase, frase
    assert "Jornada 8" in frase and "Jornada 9" in frase, frase
    assert "0,00 por jornada" not in frase, (
        "«necesitas sacarle 0,00» al lado de «no se sabe quien va "
        "primero» se contradice"
    )

    por_que = r["por_que"]
    assert por_que and "solo suma las rondas cerradas" in por_que, por_que
    assert "Jornada 8" in por_que, por_que
    assert str(r["margen_de_seguridad"]["total"]) in por_que, por_que


# ============================================================
# 2. LAS RONDAS ABIERTAS SALEN DEL TABLON
# ============================================================


def test_empezada_y_sin_cerrar_es_abierta() -> None:
    abiertas = find_open_rounds(_tablon())

    assert [x["round_id"] for x in abiertas] == [4906, 4907], abiertas
    assert abiertas[0]["nombre"] == "Jornada 8"
    assert abiertas[0]["empezo"].startswith("2026-10-09"), abiertas[0]

    nueve = abiertas[1]
    assert nueve["empezo"] == datetime.fromtimestamp(
        1_792_177_200, tz=timezone.utc
    ).isoformat(), "la reemision no mueve cuando empezo"


def test_todo_cerrado_es_lista_vacia_y_no_None() -> None:
    cerrado = _sin_la_j8_ni_la_j9()

    assert find_open_rounds(cerrado) == [], (
        "se sabe, y no hay ninguna abierta: eso no es «no se sabe»"
    )


def test_sin_tablon_no_se_sabe() -> None:
    assert find_open_rounds(None) is None
    assert find_open_rounds("no") is None
    assert find_open_rounds([]) is None, (
        "un tablon vacio no dice que todo este cerrado"
    )
    assert find_open_rounds(
        [{"type": "market", "date": 1, "content": []}]
    ) is None, "sin una sola ronda empezada no se sabe nada"


def test_la_basura_no_abre_rondas() -> None:
    basura = [
        None, 3, "x", {}, {"type": "roundStarted"},
        {"type": "roundStarted", "content": "x"},
        {"type": "roundStarted", "content": {"round": "x"}},
        {"type": "roundStarted", "content": {"round": {"id": None}}},
    ]

    assert find_open_rounds(basura) is None
    assert [x["round_id"] for x in find_open_rounds(
        basura + _tablon()
    )] == [4906, 4907]


# ============================================================
# 3. EL MARGEN SE MIDE, Y TIENE SUELO
# ============================================================


def test_el_margen_se_mide_en_el_tablon() -> None:
    m = measure_round_margin(_tablon(), PEPE)

    assert m["medido"] == 35, (
        f"Luismi 64 contra nuestros 29 en la J6 aplazada: {m}"
    )
    assert m["medido_en"]["rival"] == "Luismi_Haz"
    assert m["rondas_medidas"] == 2, "la J7 reemitida se mide una vez"
    assert m["por_ronda"] == max(35, SUELO_DEL_MARGEN_POR_RONDA)


def test_el_suelo_manda_si_lo_medido_es_poco() -> None:
    poco = [_cierra(1, "Jornada 1", 1, [
        {"user": _u(PEPE, "Pepe Bordalás"), "points": 50},
        {"user": _u(POLLO, "Pollo17"), "points": 45},
    ])]

    m = measure_round_margin(poco, PEPE)

    assert m["medido"] == -5, "ganamos esa ronda: el hueco es negativo"
    assert m["por_ronda"] == SUELO_DEL_MARGEN_POR_RONDA


def test_lo_medido_manda_si_pasa_del_suelo() -> None:
    mucho = [_cierra(1, "Jornada 1", 1, [
        {"user": _u(PEPE, "Pepe Bordalás"), "points": 10},
        {"user": _u(MEX, "Mex"), "points": 10 + SUELO_DEL_MARGEN_POR_RONDA + 15},
    ])]

    m = measure_round_margin(mucho, PEPE)

    assert m["por_ronda"] == SUELO_DEL_MARGEN_POR_RONDA + 15


def test_el_margen_total_es_por_ronda_abierta() -> None:
    r = _carrera(_tablon())

    margen = r["margen_de_seguridad"]
    assert margen["rondas_abiertas"] == 2
    assert margen["total"] == margen["por_ronda"] * 2


# ============================================================
# 4. CUANDO SI ES LIDER
# ============================================================


def test_con_ventaja_de_sobra_si_es_lider() -> None:
    total = _carrera(_tablon())["margen_de_seguridad"]["total"]

    r = _carrera(_tablon(), pepe=320 + total + 1)

    assert r["lider_asegurado"] is True
    assert r["urgency"] == "LIDER", r["urgency"]
    assert r["headline"].startswith("Vas 1º, con"), r["headline"]
    assert "2 rondas abiertas sin contar" in r["headline"], (
        "lider si, pero diciendo que hay cosas sin contar"
    )


def test_ventaja_igual_al_margen_no_basta() -> None:
    total = _carrera(_tablon())["margen_de_seguridad"]["total"]

    r = _carrera(_tablon(), pepe=320 + total)

    assert r["urgency"] == "EN_JUEGO", (
        "con la ventaja justa del margen, perder el margen es empatar"
    )


def test_sin_nada_abierto_es_lider() -> None:
    cerrado = _sin_la_j8_ni_la_j9()

    r = _carrera(cerrado)

    assert r["jornadas_abiertas"] == []
    assert r["urgency"] == "LIDER"
    assert r["lider_asegurado"] is True
    assert "cuenta todo lo jugado" in r["por_que"], r["por_que"]


# ============================================================
# 5. SIN TABLON NO SE DICE LIDER
# ============================================================


def test_sin_tablon_no_se_dice_lider() -> None:
    r = _carrera(None)

    assert r["jornadas_abiertas"] is None
    assert r["jornadas_abiertas_motivo"], "y se dice por que"
    assert r["margen_de_seguridad"] is None
    assert r["urgency"] == "SIN_DATOS", (
        "sin saber que falta por contar, LIDER seria tranquilizar "
        "por falta de datos"
    )
    assert "tablon" in r["headline"], r["headline"]


# ============================================================
# 6. NO SE INVENTA LA PROVISIONAL
# ============================================================


def test_la_provisional_no_se_inventa() -> None:
    r = _carrera(_tablon())

    assert r["clasificacion_provisional"] is None, (
        "nadie publica lo que lleva cada manager en una ronda "
        "abierta: sumarle algo seria inventarlo"
    )
    assert r["clasificacion_provisional_motivo"]
    assert r["clasificacion_cuenta"] == "SOLO_RONDAS_CERRADAS"

    puntos = {m["name"]: m["points"] for m in r["managers"]}
    assert puntos["Pepe Bordalás"] == 323 and puntos["Pollo17"] == 320, (
        f"los puntos de la tabla son los de Biwenger, tal cual: {puntos}"
    )


def test_siendo_segundos_se_avisa_de_lo_abierto() -> None:
    r = _carrera(_tablon(), pepe=300)

    assert r["is_leader"] is False
    assert r["urgency"] not in ("LIDER", "EN_JUEGO")
    assert "(solo rondas cerradas; 2 rondas abiertas sin contar)" in (
        r["headline"]
    ), r["headline"]
    assert "puede moverse" in r["por_que"], r["por_que"]


# ============================================================
# 7. EL DASHBOARD Y EL PANEL
# ============================================================


def test_el_dashboard_le_pasa_el_tablon() -> None:
    fuente = (RAIZ / "src" / "telemetry" / "dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert 'eventos=board.get("events")' in fuente, (
        "el dashboard construye la carrera sin el tablon: no sabria "
        "que rondas faltan y nunca diria LIDER"
    )


def test_el_panel_sabe_pintar_en_juego() -> None:
    panel = (
        RAIZ / "dashboard-v8" / "src" / "components" / "RacePanel.jsx"
    ).read_text(encoding="utf-8")

    assert "EN_JUEGO:" in panel, (
        "sin la entrada la pastilla cae a «SIN DATOS»"
    )
    assert "race.por_que" in panel, "el motivo no se pinta"

    # RacePanel vive en Taller > Auditoria. Lo que el dueño ve es
    # la pestaña LIGA: LA CARRERA y LOS RIVALES, UNO A UNO. El
    # 19/10 seguian diciendo "Le sacamos al 2º: 3" sin mencionar
    # la J8 abierta.
    carpeta = RAIZ / "dashboard-v8" / "src" / "components"
    carrera = (carpeta / "LaCarrera.jsx").read_text(encoding="utf-8")

    assert "race.jornadas_abiertas" in carrera, (
        "LA CARRERA no mira que rondas siguen abiertas"
    )
    assert 'race.urgency === "EN_JUEGO"' in carrera, (
        "LA CARRERA no distingue EN_JUEGO de LIDER"
    )
    assert "race.lider_asegurado" in carrera
    assert "(solo rondas cerradas)" in carrera, (
        "la cifra «Le sacamos al 2º» no dice que es de lo cerrado"
    )
    assert "race.headline" in carrera and "race.por_que" in carrera, (
        "LA CARRERA no pinta la frase ni el porque"
    )

    cartas = (carpeta / "LosRivalesEnCartas.jsx").read_text(
        encoding="utf-8"
    )

    assert "race.jornadas_abiertas" in cartas, (
        "las cartas de los rivales no miran las rondas abiertas"
    )
    assert 'race.urgency === "EN_JUEGO"' in cartas
    assert "en las rondas cerradas" in cartas, (
        "«Le sacamos 3 puntos» a Pollo17 sin decir que es de lo "
        "cerrado"
    )


# ============================================================
# 8. OBSERVADOR, Y NUNCA LANZA
# ============================================================


def test_sigue_siendo_observador() -> None:
    assert _carrera(_tablon())["observer_only"] is True


def test_nunca_lanza_con_un_tablon_roto() -> None:
    for basura in (None, {}, "x", 3, [None], [{"type": "roundFinished",
                   "content": {"round": {"id": 1}, "results": "x"}}],
                   [{"type": "roundFinished", "content": {"round": {"id": 1},
                     "results": [None, {"user": "x", "points": "7"}]}}]):
        r = _carrera(basura)
        assert isinstance(r, dict) and r.get("available") is True, (
            f"revento con {basura!r}: {r.get('reason')}"
        )
        assert r["urgency"] != "LIDER" or r["lider_asegurado"], basura


# ============================================================
# 9. LAS FRASES NO SE CONTRADICEN
# ============================================================


def _ganamos_todo_lo_cerrado(nuestros=50, suyos=45) -> list:
    """Una ronda cerrada en la que hicimos mas (o igual) que
    todos, y otra empezada sin cerrar."""

    return [
        _empieza(1, "Jornada 1", 1_789_000_000),
        _cierra(1, "Jornada 1", 1_789_200_000, [
            {"user": _u(PEPE, "Pepe Bordalás"), "points": nuestros},
            {"user": _u(POLLO, "Pollo17"), "points": suyos},
        ]),
        _empieza(2, "Jornada 2", 1_791_572_400),
    ]


def test_un_hueco_negativo_no_es_un_hueco() -> None:
    r = _carrera(_ganamos_todo_lo_cerrado())

    assert r["urgency"] == "EN_JUEGO", r["urgency"]
    assert r["margen_de_seguridad"]["medido"] == -5

    por_que = r["por_que"]
    assert "sacar -" not in por_que, (
        f"«un rival nos ha llegado a sacar -5»: nadie nos saco "
        f"nada: {por_que}"
    )
    assert "nos ha llegado a sacar" not in por_que, por_que
    assert "ningun rival nos ha sacado" in por_que, por_que
    assert f"suelo de {SUELO_DEL_MARGEN_POR_RONDA}" in por_que, por_que
    assert f"se cuentan {SUELO_DEL_MARGEN_POR_RONDA} por ronda" in (
        por_que
    ), por_que

    # Empatar la ronda tampoco es que nos saquen nada.
    empate = _carrera(_ganamos_todo_lo_cerrado(suyos=50))["por_que"]
    assert "sacar 0" not in empate, empate
    assert "ningun rival nos ha sacado" in empate, empate


def test_con_tablon_sin_rondas_no_dice_sin_el_tablon() -> None:
    sin_rondas = [
        {"type": "market", "date": 1_792_000_000, "content": []},
        {"type": "transfer", "date": 1_792_000_100, "content": []},
    ]

    r = _carrera(sin_rondas, pepe=325)

    assert r["urgency"] == "SIN_DATOS", r["urgency"]
    motivo = r["jornadas_abiertas_motivo"]
    assert motivo == "el tablon no trae ninguna ronda empezada", motivo

    frase = r["headline"]
    assert "sin el tablon" not in frase, (
        f"el tablon SI llego; la frase contradice a su motivo: {frase}"
    )
    assert motivo in frase, frase
    assert "con 5 de ventaja" in frase, frase

    # Y sin tablon de verdad, el motivo es ese.
    sin = _carrera(None)["headline"]
    assert "no se paso el tablon" in sin, sin


def test_cada_ronda_abierta_lleva_su_fecha() -> None:
    r = _carrera(_tablon())

    por_que = r["por_que"]

    # 1_791_572_400 = 09/10 19:00 UTC; 1_792_177_200 = 16/10.
    assert "Jornada 8 desde el 09/10" in por_que, por_que
    assert "Jornada 9 desde el 16/10" in por_que, por_que


def test_una_ronda_atascada_se_ve_en_la_frase() -> None:
    # Una J6 empezada el 02/09 a las 22:30 UTC (00:30 del 03/09 en
    # Madrid) que Biwenger no cierra nunca: en octubre tiene que
    # verse en lo que se pinta, no solo en el JSON.
    atascada = _tablon() + [_empieza(4904, "Jornada 6", 1_788_388_200)]

    r = _carrera(atascada)

    assert [x["round_id"] for x in r["jornadas_abiertas"]] == [
        4904, 4906, 4907,
    ]
    assert "Jornada 6 desde el 03/09" in r["por_que"], (
        f"la fecha va en hora de Madrid: {r['por_que']}"
    )


def test_sin_fecha_queda_el_nombre() -> None:
    sin_fecha = [
        {"type": "roundStarted",
         "content": {"round": {"id": 77, "name": "Jornada 10"}}},
    ]

    r = _carrera(sin_fecha)

    assert r["jornadas_abiertas"][0]["empezo"] is None
    assert "Jornada 10" in r["por_que"], r["por_que"]
    assert "desde el" not in r["por_que"], r["por_que"]


TESTS = [
    test_la_foto_del_19_10_no_dice_lider,
    test_empezada_y_sin_cerrar_es_abierta,
    test_todo_cerrado_es_lista_vacia_y_no_None,
    test_sin_tablon_no_se_sabe,
    test_la_basura_no_abre_rondas,
    test_el_margen_se_mide_en_el_tablon,
    test_el_suelo_manda_si_lo_medido_es_poco,
    test_lo_medido_manda_si_pasa_del_suelo,
    test_el_margen_total_es_por_ronda_abierta,
    test_con_ventaja_de_sobra_si_es_lider,
    test_ventaja_igual_al_margen_no_basta,
    test_sin_nada_abierto_es_lider,
    test_sin_tablon_no_se_dice_lider,
    test_la_provisional_no_se_inventa,
    test_siendo_segundos_se_avisa_de_lo_abierto,
    test_el_dashboard_le_pasa_el_tablon,
    test_el_panel_sabe_pintar_en_juego,
    test_sigue_siendo_observador,
    test_nunca_lanza_con_un_tablon_roto,
    test_un_hueco_negativo_no_es_un_hueco,
    test_con_tablon_sin_rondas_no_dice_sin_el_tablon,
    test_cada_ronda_abierta_lleva_su_fecha,
    test_una_ronda_atascada_se_ve_en_la_frase,
    test_sin_fecha_queda_el_nombre,
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
    print(f"LAS RONDAS ABIERTAS V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
