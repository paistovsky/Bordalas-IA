"""
Los sentidos de Pepe: la edad se calcula y la ceguera se grita.

SINTOMA (13/09/2026, noche)

    Sesenta y cuatro objetivos en el mercado y NI UNA PUJA. El
    tablero de titulares es de la jornada 2, del 17 de agosto: el
    motor lo rechaza —bien hecho— y los 64 candidatos salen con
    la misma frase.

    En pantalla eso se leia como prudencia. Era ceguera.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Que la edad SE CALCULE. Cambias la marca de tiempo del
       fixture y la edad cambia con ella. Sin marca, "sin dato"
       y nunca un cero.

    2. Que cuando el tablero esta rechazado, la pantalla lo diga
       arriba con el recuento REAL de objetivos sin pronostico.

REGLA 23

    No lee estado externo: todo se construye aqui.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

AHORA = datetime(2026, 9, 13, 22, 48, tzinfo=timezone.utc)

# EL 17 DE AGOSTO, que es de cuando es el tablero de verdad.
HACE_27_DIAS = "2026-08-17T18:32:30.243072+00:00"


EL_TABLERO_RECHAZADO = {
    "starter_board_matchday": 2,
    "starter_board_updated_at": HACE_27_DIAS,
    "starter_cache_status": "REJECTED_WRONG_MATCHDAY",
    "starter_source_error": (
        "El tablero es de la jornada 2 y estamos en la 7: sin "
        "pronosticos hasta que se refresque."
    ),
}

OBJETIVOS = (
    [
        {"id": i, "name": f"Uno {i}", "xi_decision": "SIN_PRONOSTICO"}
        for i in range(64)
    ]
)


def _sentidos(**cambios):
    from src.analysis.los_sentidos import los_sentidos

    argumentos = {
        "lineup": EL_TABLERO_RECHAZADO,
        "scout": {
            "available": True,
            "generated_at": "2026-09-05T09:32:00+00:00",
            "matchday": 4,
            "sources": [{"status": "OK"}, {"status": "OK"}],
            "players_count": 288,
        },
        "press": {
            "available": True,
            "generated_at": "2026-09-05T16:11:34+00:00",
            "sources": [{"name": "MARCA"}],
        },
        "vara": {
            "active": True,
            "rows": [{"position": 2, "factor": 0.787}],
            "window": {"matchdays": 3, "players": 81},
            "reason": "Factores por posicion puestos.",
        },
        "rival_intelligence": {
            "cash_check": {"ok": True, "reason": "Cuadra."},
            "cash_reconstruction": {"events_read": 288},
        },
        "toda_la_liga": {
            "plantillas": {
                "cuadra": True,
                "con_dueño": 117,
                "libres": 453,
                "total": 570,
            }
        },
        "calendario": {
            "available": True,
            "fetched_at": "2026-09-13T21:20:59+02:00",
            "casan_todas": True,
            "reason": "380 partidos.",
        },
        "marcador": {
            "available": True,
            "resumen": {
                "jornadas_medibles": 2,
                "jornadas_fiables": 0,
            },
            "reason": "Ninguna cuadra con Biwenger.",
        },
        "objetivos": OBJETIVOS,
        "jornada_de_hoy": 7,
        "ahora": AHORA,
    }

    argumentos.update(cambios)

    return los_sentidos(**argumentos)


def _fila(visto, nombre):
    for f in visto["sentidos"]:
        if f["sentido"] == nombre:
            return f

    raise AssertionError(f"no esta el sentido `{nombre}`")


# ============================================================
# 1. LA EDAD SE CALCULA
# ============================================================


def test_los_sentidos_no_se_inventan_la_edad() -> None:
    """
    "HACE 27 DIAS" SALE DE RESTAR, NO DE ESCRIBIRLO.

    CONSECUENCIA DE ESCRIBIRLO

        Un numero de dias a mano es verdad el dia que se escribe
        y mentira a la semana siguiente. Y miente hacia el lado
        malo: el cuadro diria "hace 27 dias" para siempre,
        incluso el dia que el tablero se arregle.

    Y SIN MARCA DE TIEMPO, "SIN DATO"

        Nunca un cero. Un cero se lee como "de ahora mismo", que
        es justo lo contrario de lo que pasa cuando falta el
        dato.
    """

    from src.analysis.los_sentidos import edad

    visto = _sentidos()

    assert visto["available"] is True, visto

    # REGLA 24: sin filas esto no probaria nada.
    assert len(visto["sentidos"]) == 9, visto

    # 1. LA EDAD DE HOY: del 17/08 al 13/09 son 27 dias.
    tablero = _fila(visto, "Tablero de titulares")

    assert tablero["edad"]["dias"] == 27, tablero["edad"]

    assert "27 días" in tablero["de_cuando"], tablero

    assert "Jornada 2" in tablero["de_cuando"], tablero

    # 2. CAMBIA LA MARCA, CAMBIA LA EDAD.
    #
    #    Es la prueba de que se resta y no se copia.
    for dias, espera in ((0, 0), (1, 1), (5, 5), (100, 100)):

        cuando = (
            AHORA - timedelta(days=dias, hours=1)
        ).isoformat()

        otro = _sentidos(
            lineup={
                **EL_TABLERO_RECHAZADO,
                "starter_board_updated_at": cuando,
            }
        )

        assert _fila(otro, "Tablero de titulares")["edad"][
            "dias"
        ] == espera, (dias, _fila(otro, "Tablero de titulares"))

    # 3. SIN MARCA DE TIEMPO, "sin dato" Y NO UN CERO.
    for sin_marca in (None, "", "no es una fecha"):

        cuanto = edad(sin_marca, AHORA)

        # EL MENSAJE DICE LO QUE SALIO, no solo lo que entro.
        #
        #     Estos decian `, sin_marca`, que para el primer caso
        #     es `None`. En el registro de CI se leia "FALLA
        #     test_los_sentidos_no_se_inventan_la_edad: None", que
        #     no ayuda a nadie.
        assert cuanto["dias"] is None, (sin_marca, cuanto)
        assert cuanto["horas"] is None, (sin_marca, cuanto)
        assert cuanto["texto"] == "sin dato", (sin_marca, cuanto)

        otro = _sentidos(
            lineup={
                **EL_TABLERO_RECHAZADO,
                "starter_board_updated_at": sin_marca,
            }
        )

        fila = _fila(otro, "Tablero de titulares")

        assert "sin dato" in fila["de_cuando"], fila

        assert "0 día" not in fila["de_cuando"], fila

    # 4. Y NO HAY NI UN NUMERO DE DIAS ESCRITO EN EL MODULO.
    fuente = (
        RAIZ / "src" / "analysis" / "los_sentidos.py"
    ).read_text(encoding="utf-8")

    import ast

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if (
            isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, str)
            and "día" in nodo.value
        ):
            assert "{" in nodo.value or nodo.value.strip() in (
                "día",
                "días",
                "s",
            ), (
                f"hay un texto con dias escrito a mano: "
                f"{nodo.value!r}"
            )

    # 5. UN TIMESTAMP SIN ZONA SE DICE (regla 35).
    #
    #    Restar dos relojes de husos distintos y publicar la
    #    diferencia como exacta es un dato con dos nombres.
    sin_zona = edad("2026-09-12T22:48:00", AHORA)

    assert sin_zona["zona_supuesta"] is True, sin_zona

    con_zona = edad("2026-09-12T22:48:00+00:00", AHORA)

    assert con_zona["zona_supuesta"] is False, con_zona


# ============================================================
# 2. LA CEGUERA SE GRITA
# ============================================================


def test_si_el_tablero_esta_rechazado_la_pantalla_lo_grita() -> None:
    """
    EL AVISO LO ENCIENDE EL HECHO, Y EL NUMERO SE CUENTA.

    CONSECUENCIA DE NO GRITARLO

        Sesenta y cuatro filas repitiendo "sin pronostico" se
        leen de una en una y no suman a nada. "64 de 64" se lee
        de un golpe y dice lo que pasa: la via de fichar esta
        cerrada por falta de un dato, no por criterio.

    Y EL RECUENTO SE CUENTA (regla 18). Escrito a mano seria
    verdad hoy y mentira el dia que se arregle el tablero — que
    es justo el dia en que nadie miraria este numero.
    """

    visto = _sentidos()

    ciego = visto["ciego"]

    # REGLA 24: con la lista de objetivos vacia esto no probaria
    # nada, asi que se exige que haya.
    assert ciego["objetivos"] == 64, ciego

    assert ciego["sin_pronostico"] == 64, ciego

    assert ciego["hay"] is True, ciego

    assert ciego["rechazado"] is True, ciego

    # LA FRASE DEL MOTOR, ENTERA Y SIN REESCRIBIR.
    assert ciego["reason"] == (
        EL_TABLERO_RECHAZADO["starter_source_error"]
    ), ciego

    assert _fila(visto, "Tablero de titulares")["estado"] == (
        "MUERTO"
    )

    # 1. SI NO ESTA RECHAZADO, NO SALE EL AVISO.
    sano = _sentidos(
        lineup={
            "starter_board_matchday": 7,
            "starter_board_updated_at": (
                AHORA - timedelta(hours=2)
            ).isoformat(),
            "starter_cache_status": "OK",
            "starter_source_error": None,
        },
        objetivos=[
            {"id": i, "xi_decision": "MEJORA"} for i in range(64)
        ],
    )

    assert sano["ciego"]["hay"] is False, sano["ciego"]

    assert sano["ciego"]["sin_pronostico"] == 0, sano["ciego"]

    assert _fila(sano, "Tablero de titulares")["estado"] == "VIVO"

    # 2. EL RECUENTO ES EL DE VERDAD, no el total.
    mezclado = _sentidos(
        objetivos=(
            [
                {"id": i, "xi_decision": "SIN_PRONOSTICO"}
                for i in range(40)
            ]
            + [
                {"id": 100 + i, "xi_decision": "MEJORA"}
                for i in range(20)
            ]
        )
    )

    assert mezclado["ciego"]["sin_pronostico"] == 40, (
        mezclado["ciego"]
    )

    assert mezclado["ciego"]["objetivos"] == 60, (
        mezclado["ciego"]
    )

    # 3. SIN OBJETIVOS, EL AVISO NO SE ENCIENDE.
    #
    #    "0 de 0" no es una alarma: es que no ha llegado la
    #    lista. Un aviso que se enciende con la AUSENCIA de
    #    datos tapa el fallo que tenia que enseñar.
    for vacia in (None, []):

        hueco = _sentidos(objetivos=vacia)

        assert hueco["ciego"]["hay"] is False, vacia

        assert hueco["ciego"]["objetivos"] == 0, vacia

    # 4. Y LA PANTALLA LO PINTA.
    panel = (
        RAIZ
        / "dashboard-v8"
        / "src"
        / "components"
        / "LosSentidosPanel.jsx"
    ).read_text(encoding="utf-8")

    assert "ciego.sin_pronostico" in panel, (
        "la pantalla no pinta el recuento de ciegos"
    )

    assert "ciego.hay" in panel, (
        "la banda no depende del hecho: seria un cartel fijo"
    )


def test_un_sentido_que_no_llega_sale_igual() -> None:
    """
    QUE FALTE UNA FILA ES EL FALLO QUE ESTE CUADRO ENSEÑA.

    Si un sentido no llega y su fila desaparece, el cuadro dice
    "siete sentidos y todos bien" — que es exactamente la mentira
    que este cuadro existe para evitar.
    """

    visto = _sentidos(
        scout=None,
        press=None,
        vara=None,
        rival_intelligence=None,
        toda_la_liga=None,
        calendario=None,
        marcador=None,
    )

    assert visto["available"] is True, visto

    assert len(visto["sentidos"]) == 9, [
        f["sentido"] for f in visto["sentidos"]
    ]

    # Los que no llegaron, en MUERTO: todos.
    muertos = [
        f["sentido"]
        for f in visto["sentidos"]
        if f["estado"] == "MUERTO"
    ]

    assert len(muertos) == 9, muertos

    # Y NINGUNA FILA SE QUEDA SIN DECIR PARA QUE SIRVE.
    for fila in visto["sentidos"]:
        assert fila["para_que"], fila
        assert fila["de_cuando"], fila
        assert fila["que_decide"], fila


def test_este_cuadro_no_decide_nada() -> None:
    """
    Es para mirar. Ninguna puja ni ninguna venta sale de aqui.
    """

    import ast

    fuente = (
        RAIZ / "src" / "analysis" / "los_sentidos.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    llamadas = {
        nodo.func.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
    } | {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
    }

    for escribe in (
        "place_bid",
        "accept_offer",
        "list_player_for_sale",
        "abrir",
        "open",
    ):
        assert escribe not in llamadas, (
            f"los sentidos llaman a `{escribe}`"
        )

    for modulo in ("write_client", "executor", "autopilot"):
        assert modulo not in fuente, (
            f"los sentidos importan `{modulo}`"
        )


TESTS = [
    test_los_sentidos_no_se_inventan_la_edad,
    test_si_el_tablero_esta_rechazado_la_pantalla_lo_grita,
    test_un_sentido_que_no_llega_sale_igual,
    test_este_cuadro_no_decide_nada,
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
        f"LOS SENTIDOS V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
