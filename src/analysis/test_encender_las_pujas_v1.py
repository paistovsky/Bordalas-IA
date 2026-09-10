"""
Encender las pujas: lo que tiene que seguir siendo verdad.

SINTOMA (09/09/2026)

    Dos semanas midiendo la subasta y Pepe no habia pujado ni
    una vez. La pieza estaba construida, medida y APAGADA por
    decision del dueno.

CAUSA

    Encenderla era lo unico que faltaba. Pero encender algo que
    escribe solo en Biwenger, a las siete menos cinco de la
    manana, sin nadie delante, solo es aceptable si las puertas
    estan clavadas por una guardia.

    Y al encenderla aparecieron DOS fallos que la habrian
    dejado encendida y muda -o encendida y desobediente-:

    1. El ciclo leia el estado en `cycle["state"]`, que no
       existe: vive en `cycle["result"]["state"]`, y ni siquiera
       ahi esta el tablero de adquisicion. Cero candidatos,
       cero pujas, y ni un error en el log.

    2. El filtro de candidatos dejaba pasar los objetivos de
       MERCADO DE RIVAL. De los 49 objetivos del 09/09,
       VEINTINUEVE lo eran. La compra a rivales esta cerrada
       por orden del dueno: la subasta habria pujado por ellos.

CONSECUENCIA

    Ninguno de los dos se ve mirando el log de un ciclo fuera
    de la ventana. Los dos se ven aqui.

LO QUE SE PROTEGE

     1. Que el interruptor apague TODO, con la cesta llena.
     2. Que el reloj de solvencia mande por encima de la
        ventana.
     3. Que fuera de la ventana no se puje.
     4. Que el bloqueo temporal de la casa tambien cierre.
     5. Que nunca haya mas pujas que fichas libres.
     6. Que el tope del primer dia recorte, y recorte por la
        cola: se queda con las mejores, no con tres al azar.
     7. Que todas las pujas salgan al precio topado de la curva.
     8. Que el peor caso cuente la plantilla que YA hay.
     9. Que sin `en_vivo` no se ejecute nada.
    10. Que la compra a rivales siga cerrada.
    11. Que un jugador con puja viva no se puje otra vez.
    12. Que el ciclo lea el estado donde vive.
    13. Que lo pujado llegue AL LIBRO, con su origen.
    14. Que la forma no cambie con los datos.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: todo se pasa. La unica que
    toca el entorno es la del interruptor -que ES una variable
    de entorno- y lo deja como estaba.

COMO SE USA

    python -m src.analysis.test_encender_las_pujas_v1
"""

from __future__ import annotations

import json
import os
import tempfile

from pathlib import Path

from src.analysis.la_subasta import (
    DISABLE_ENV,
    MAX_PUJAS_PRIMER_DIA,
    lectura_del_estado,
    plan_del_reset,
    puja_de_cartera,
)


# ============================================================
# EL MUNDO DE MENTIRA
# ============================================================

PRIMA = 0.0187


def _sano() -> dict:
    """Un reloj de solvencia que deja pujar."""

    return {"state": "SIN_DEUDA", "deficit": 0, "covered": True}


def _mercado(cuantos: int = 6, club: int = 1) -> list:
    """
    Candidatos baratos y distintos entre si.

    Precios distintos a proposito: si todos valieran lo mismo,
    el orden lo decidiria el desempate y las guardias del
    recorte no probarian nada.
    """

    return [
        {
            "id": 100 + i,
            "name": f"Jugador {i}",
            "market_price": 100_000 + 10_000 * i,
            "team_id": club + i,
        }
        for i in range(cuantos)
    ]


def _plan(**cambios) -> dict:
    """El plan con todo en verde, salvo lo que se cambie."""

    argumentos = {
        "candidatos": _mercado(),
        "prima_de_reventa": PRIMA,
        "presupuesto": 2_500_000,
        "fichas_libres": 6,
        "caja_libre": 500_000,
        "seconds_to_reset": 300,
        "solvency_clock": _sano(),
        "plantilla": [],
        "bloqueo_temporal": None,
        "en_vivo": True,
        "max_por_club": 4,
    }

    argumentos.update(cambios)

    return plan_del_reset(**argumentos)


# ============================================================
# 1. EL INTERRUPTOR
# ============================================================

def test_el_interruptor_apaga_todo_con_la_cesta_llena():
    """
    Un interruptor que solo apaga cuando no habia nada que
    apagar no es un interruptor.
    """

    antes = os.environ.get(DISABLE_ENV)

    try:
        # Primero, que SIN interruptor si puja: si no, esta
        # guardia pasaria con las manos vacias.
        encendido = _plan()

        assert encendido["execute"] is True, (
            "sin interruptor tendria que pujar; si no, esta "
            "guardia no prueba nada"
        )
        assert encendido["bids"], "no hay cesta que apagar"

        os.environ[DISABLE_ENV] = "1"

        apagado = _plan()

        assert apagado["execute"] is False, (
            f"{DISABLE_ENV}=1 y sigue ejecutando"
        )
        assert apagado["bids"] == [], (
            f"{DISABLE_ENV}=1 y sigue proponiendo pujas"
        )
        assert apagado["blocked_by"] == "INTERRUPTOR", (
            f"apagado por {apagado['blocked_by']}, no por el "
            f"interruptor"
        )
        assert apagado["committed"] == 0, (
            "apagado y sigue comprometiendo dinero"
        )

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes


# ============================================================
# 2. EL RELOJ DE SOLVENCIA MANDA
# ============================================================

def test_la_solvencia_manda_por_encima_de_la_ventana():
    """
    Con la ventana abierta, la cesta llena y el dinero puesto,
    un reloj de solvencia en rojo cierra igual.

    Una puja ganada es dinero que sale, y el viernes hay que
    estar en positivo.
    """

    for reloj in (
        {"state": "DESCUBIERTO", "deficit": 0},
        {"state": "SIN_DEUDA", "deficit": 120_000},
        {},
        None,
    ):
        plan = _plan(solvency_clock=reloj)

        assert plan["execute"] is False, (
            f"con el reloj {reloj} sigue pujando"
        )
        assert plan["blocked_by"] == "SOLVENCIA", (
            f"con el reloj {reloj} el motivo es "
            f"{plan['blocked_by']}"
        )


def test_con_deficit_no_se_puja_aunque_el_estado_sea_bueno():
    """
    El estado y el deficit son dos cosas distintas. Un
    `CUBIERTO` con deficit sigue siendo deuda por tapar.
    """

    plan = _plan(
        solvency_clock={"state": "CUBIERTO", "deficit": 1}
    )

    assert plan["blocked_by"] == "SOLVENCIA", (
        "un deficit de 1 EUR ya es deuda: no se puja"
    )


# ============================================================
# 3. LA VENTANA
# ============================================================

def test_fuera_de_la_ventana_no_se_puja():

    for segundos in (3_600, 1_800, 901, None):
        plan = _plan(seconds_to_reset=segundos)

        assert plan["execute"] is False, (
            f"a {segundos} s del reset ya esta pujando"
        )
        assert plan["blocked_by"] == "FUERA_DE_VENTANA", (
            f"a {segundos} s el motivo es {plan['blocked_by']}"
        )


def test_dentro_de_la_ventana_si_se_puja():
    """
    La contraria de la anterior. Sin esto, romper la ventana
    entera -que no se abra nunca- dejaria todo en verde.
    """

    plan = _plan(seconds_to_reset=300)

    assert plan["execute"] is True, (
        f"a 5 min del reset no puja: {plan['reason']}"
    )
    assert plan["bids"], "ventana abierta y cesta vacia"


# ============================================================
# 4. EL BLOQUEO TEMPORAL DE LA CASA
# ============================================================

def test_el_bloqueo_temporal_tambien_cierra_la_subasta():
    """
    Una puja es una escritura contra Biwenger. Si la fase tiene
    las operaciones cerradas, esta no es la excepcion.
    """

    plan = _plan(bloqueo_temporal="ROUND_LOCKED")

    assert plan["execute"] is False, (
        "operaciones bloqueadas y sigue pujando"
    )
    assert plan["blocked_by"] == "BLOQUEO_TEMPORAL"


# ============================================================
# 5. NUNCA MAS PUJAS QUE FICHAS LIBRES
# ============================================================

def test_nunca_mas_pujas_que_fichas_libres():

    for huecos in (0, 1, 2):
        plan = _plan(fichas_libres=huecos, max_pujas=99)

        assert len(plan["bids"]) <= huecos, (
            f"con {huecos} fichas libres propone "
            f"{len(plan['bids'])} pujas"
        )

    assert _plan(fichas_libres=0)["execute"] is False, (
        "sin fichas libres no se puja por nadie"
    )


# ============================================================
# 6. EL TOPE DEL PRIMER DIA
# ============================================================

def test_el_tope_del_primer_dia_recorta_a_tres():

    plan = _plan(candidatos=_mercado(8), fichas_libres=8)

    assert MAX_PUJAS_PRIMER_DIA == 3, (
        "el tope del primer dia ya no es 3: revisa el informe"
    )
    assert len(plan["bids"]) <= MAX_PUJAS_PRIMER_DIA, (
        f"propone {len(plan['bids'])} pujas con el tope en "
        f"{MAX_PUJAS_PRIMER_DIA}"
    )
    assert plan["dropped_by_cap"] > 0, (
        "con 8 candidatos y 8 fichas el tope tenia que morder; "
        "si no, esta guardia no prueba nada"
    )


def test_el_tope_se_queda_con_las_mejores_no_con_tres_al_azar():
    """
    Se recorta DESPUES del reparto. Recortar antes seria elegir
    tres al azar entre todos.
    """

    todas = _plan(
        candidatos=_mercado(8), fichas_libres=8, max_pujas=99
    )

    tres = _plan(
        candidatos=_mercado(8), fichas_libres=8, max_pujas=3
    )

    assert len(todas["bids"]) > 3, (
        "sin tope tenia que proponer mas de tres"
    )

    elegidas = [b["id"] for b in tres["bids"]]
    mejores = [b["id"] for b in todas["bids"]][:3]

    assert elegidas == mejores, (
        f"el recorte cambia la eleccion: {elegidas} en vez de "
        f"{mejores}"
    )


# ============================================================
# 7. TODAS AL PRECIO TOPADO DE LA CURVA
# ============================================================

def test_todas_las_pujas_salen_al_precio_topado():
    """
    La curva medida el 11/09 dice que el optimo esta en
    precio + 0,25 %. Ni una puja puede salir por encima.
    """

    plan = _plan(candidatos=_mercado(6), fichas_libres=6)

    assert plan["bids"], "sin pujas no se prueba nada"

    for puja in plan["bids"]:

        esperado = puja_de_cartera(puja["market_price"])

        assert puja["bid"] == esperado, (
            f"{puja['name']} sale por {puja['bid']} y el tope "
            f"de la curva es {esperado}"
        )


# ============================================================
# 8. EL PEOR CASO: QUE SE GANEN TODAS
# ============================================================

def test_el_peor_caso_cuenta_la_plantilla_que_ya_hay():
    """
    Tres del mismo club en el banquillo mas dos en la cesta son
    CINCO si entran las dos. La cesta sola no lo ve.
    """

    mismo_club = [
        {
            "id": 200 + i,
            "name": f"Del club 7 numero {i}",
            "market_price": 100_000 + 1_000 * i,
            "team_id": 7,
        }
        for i in range(3)
    ]

    plantilla = [
        {"id": 900 + i, "team_id": 7, "price": 1_000_000}
        for i in range(3)
    ]

    comun = {
        "candidatos": mismo_club,
        "prima_de_reventa": PRIMA,
        "presupuesto": 2_500_000,
        "fichas_libres": 6,
        "caja_libre": 500_000,
        "seconds_to_reset": 300,
        "solvency_clock": _sano(),
        "en_vivo": True,
        "max_por_club": 4,
    }

    sin_plantilla = plan_del_reset(plantilla=[], **comun)

    con_plantilla = plan_del_reset(plantilla=plantilla, **comun)

    assert len(sin_plantilla["bids"]) >= 2, (
        "sin plantilla tenian que caber varias del club 7; si "
        "no, esta guardia no prueba nada"
    )

    assert len(con_plantilla["bids"]) == 1, (
        f"con 3 del club 7 ya en la plantilla solo cabe 1 mas, "
        f"y propone {len(con_plantilla['bids'])}"
    )

    assert con_plantilla["dropped_by_club"] >= 1, (
        "no dice cuantas dejo fuera la barandilla del club"
    )


def test_el_peor_caso_sale_publicado():
    """
    Que se pueda mirar como quedaria la plantilla si entraran
    todas, ANTES de que entren.
    """

    plan = _plan()

    peor = plan.get("worst_case") or {}

    assert peor.get("available") is True, (
        "el plan no publica el peor caso"
    )
    assert peor.get("jugadores") == len(plan["bids"]), (
        "el peor caso no cuenta los que entrarian"
    )


def test_lo_que_se_gana_si_entran_todas_esta_publicado():

    plan = _plan()

    assert plan["all_won"] >= plan["expected"], (
        "lo esperado no puede superar a ganarlas todas"
    )
    assert plan["committed"] == sum(
        b["bid"] for b in plan["bids"]
    ), "lo comprometido no es la suma de las pujas"


# ============================================================
# 9. SIN `en_vivo` NO SE EJECUTA NADA
# ============================================================

def test_sin_en_vivo_calcula_pero_no_ejecuta():

    plan = _plan(en_vivo=False)

    assert plan["bids"], "sin en_vivo tambien tiene que calcular"
    assert plan["execute"] is False, (
        "ejecuta sin estar en vivo"
    )
    assert plan["blocked_by"] == "SIN_LIVE"


# ============================================================
# 10, 11. LA LECTURA DEL ESTADO
# ============================================================

def _estado(targets: list) -> dict:
    """El estado publicado, con la forma del dashboard."""

    return {
        "acquisition": {
            "targets": targets,
            "computer_premium": {"median_percent": 1.87},
        },
        "exposure": {
            "available_budget": 2_500_000,
            "cash_budget": 500_000,
        },
        "market_clock": {"seconds_to_reset": 300},
        "rival_intelligence": {
            "managers": [
                {"user_id": 1, "roster_count": 20, "is_us": False},
                {"user_id": 2, "roster_count": 14, "is_us": True},
            ]
        },
        "solvency_clock": _sano(),
        "operations_locked": False,
        "phase": "NORMAL",
    }


def test_la_compra_a_rivales_sigue_cerrada():
    """
    De los 49 objetivos del 09/09, 29 eran de mercado de rival.
    Ni uno puede entrar en la cesta.
    """

    del_computer = {
        "id": 1,
        "name": "Del Computer",
        "market_price": 150_000,
        "team_id": 1,
        "decision": "SIN_VALOR",
    }

    de_un_rival = {
        "id": 2,
        "name": "De un rival",
        "market_price": 150_000,
        "team_id": 2,
        "decision": "MERCADO_DE_RIVAL",
        "outside_computer_market": True,
        "seller_id": 4242,
    }

    lectura = lectura_del_estado(
        _estado([del_computer, de_un_rival])
    )

    ids = [c["id"] for c in lectura["candidatos"]]

    assert 1 in ids, (
        "el del Computer tenia que entrar; si no, esta guardia "
        "no prueba nada"
    )
    assert 2 not in ids, (
        "un jugador de mercado de rival ha entrado en la cesta: "
        "la compra a rivales esta cerrada"
    )


def test_un_jugador_con_puja_viva_no_se_puja_otra_vez():

    lectura = lectura_del_estado(
        _estado(
            [
                {
                    "id": 1,
                    "name": "Libre",
                    "market_price": 150_000,
                    "team_id": 1,
                },
                {
                    "id": 2,
                    "name": "Ya pujado",
                    "market_price": 150_000,
                    "team_id": 2,
                    "has_live_bid": True,
                },
            ]
        )
    )

    ids = [c["id"] for c in lectura["candidatos"]]

    assert ids == [1], (
        f"con una puja viva no se vuelve a pujar, y salen {ids}"
    )


def test_las_fichas_libres_son_la_mayor_menos_la_nuestra():

    lectura = lectura_del_estado(_estado([]))

    assert lectura["fichas_libres"] == 6, (
        f"20 la mayor y 14 la nuestra son 6 fichas, no "
        f"{lectura['fichas_libres']}"
    )


def test_el_bloqueo_de_fase_llega_desde_el_estado():

    estado = _estado([])
    estado["operations_locked"] = True
    estado["phase"] = "ROUND_LOCKED"

    lectura = lectura_del_estado(estado)

    assert lectura["bloqueo_temporal"] == "ROUND_LOCKED"


def test_la_forma_no_cambia_con_los_datos():
    """
    Con datos y sin ellos, las mismas claves. Si no, quien la
    use se rompe justo el dia que no hay mercado.
    """

    con = lectura_del_estado(_estado([]))
    sin = lectura_del_estado(None)

    assert set(con) == set(sin), (
        f"la lectura cambia de forma: {set(con) ^ set(sin)}"
    )

    completo = _plan()
    vacio = _plan(candidatos=[])

    assert set(completo) == set(vacio), (
        f"el plan cambia de forma: "
        f"{set(completo) ^ set(vacio)}"
    )


# ============================================================
# 12. EL CICLO LEE EL ESTADO DONDE VIVE
# ============================================================

def test_el_ciclo_lee_el_estado_donde_vive():
    """
    `run_cycle` devuelve {snapshot, result, execution}. El
    estado esta en `result["state"]`.

    Leerlo de la raiz devuelve vacio: cero candidatos, cero
    pujas y ni un error. Encendido y mudo.

    NO TOCA LA RED: se cambian por delante las dos funciones
    que la tocarian.
    """

    import src.autopilot as autopilot
    import src.v10_full_autonomous_live as v10

    retrato_original = autopilot.load_rival_intelligence
    tablon_original = autopilot.board_del_ciclo

    try:
        autopilot.load_rival_intelligence = lambda snapshot: {
            "managers": [
                {"user_id": 7, "roster_count": 20},
                {"user_id": 9, "roster_count": 14},
            ],
            "current_user_id": 9,
        }

        autopilot.board_del_ciclo = lambda snapshot: {
            "current_user_id": 9
        }

        bien = v10._estado_publicado(
            {
                "snapshot": {"my_team": []},
                "result": {
                    "state": {
                        "speculation": {
                            "budget": {
                                "available_budget": 2_500_000,
                                "cash_budget": 497_307,
                            }
                        }
                    }
                },
            }
        )

        assert bien["exposure"]["cash_budget"] == 497_307, (
            "el ciclo no lee los bolsillos de result['state']: "
            "leeria cero y no pujaria nunca"
        )

        # Los nuestros, marcados: sin `is_us` las fichas libres
        # salen enormes y la barandilla deja de morder.
        nuestros = [
            m
            for m in bien["rival_intelligence"]["managers"]
            if m.get("is_us")
        ]

        assert len(nuestros) == 1, (
            "no se marca cual es nuestra plantilla"
        )
        assert nuestros[0]["roster_count"] == 14

        # Y el fallo de verdad: el mismo estado colgado de la
        # raiz no vale.
        mal = v10._estado_publicado(
            {
                "snapshot": {"my_team": []},
                "state": {
                    "speculation": {
                        "budget": {"cash_budget": 497_307}
                    }
                },
            }
        )

        assert not mal["exposure"].get("cash_budget"), (
            "esta leyendo el estado de la raiz, donde no vive"
        )

    finally:
        autopilot.load_rival_intelligence = retrato_original
        autopilot.board_del_ciclo = tablon_original


# ============================================================
# 13. LO PUJADO, AL LIBRO
# ============================================================

def test_lo_pujado_llega_al_libro_con_su_origen():
    """
    El libro es lo unico que permitira decir dentro de una
    semana si esto gana dinero.

    Esta guardia existe porque la primera version importaba
    `record_bid` de un modulo que no existe y llamaba con un
    argumento que tampoco: fallaba en silencio -esta blindado a
    proposito- y no apuntaba nada.

    NO ESCRIBE EN `data/`: se le cambia la ruta del libro por
    un directorio temporal.
    """

    import src.intelligence.bid_outcome_ledger as libro
    import src.v10_full_autonomous_live as v10

    original = libro.LEDGER_PATH

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "libro.json"

        try:
            libro.LEDGER_PATH = ruta

            v10._anotar_en_el_libro(
                [
                    {
                        "id": 1599,
                        "name": "Yeray",
                        "amount": 1_533_826,
                        "market_price": 1_530_000,
                        "win_odds": 0.61,
                        "seller_id": None,
                        "rate_percent_per_day": 0.4,
                        "sent": True,
                    }
                ]
            )

            assert ruta.exists(), (
                "no se ha escrito el libro: la puja no queda "
                "apuntada en ninguna parte"
            )

            apuntadas = json.loads(
                ruta.read_text(encoding="utf-8")
            ).get("bids", {})

            assert len(apuntadas) == 1, (
                f"apuntadas {len(apuntadas)} pujas en vez de 1"
            )

            anotacion = list(apuntadas.values())[0]

            assert anotacion["player_id"] == 1599
            assert anotacion["amount"] == 1_533_826
            assert anotacion["outcome"] == "PENDING"

            assert (
                anotacion["target_source"] == "SUBASTA_CARTERA"
            ), (
                "sin origen no se podra separar lo que gano la "
                "subasta de lo que gano el camino de siempre"
            )

            assert anotacion["market_price"] == 1_530_000, (
                "sin el precio de mercado no se puede medir la "
                "prima pagada"
            )

        finally:
            libro.LEDGER_PATH = original


def test_el_libro_sabe_separar_por_origen():
    """
    Sumar los dos caminos daria un porcentaje de acierto que no
    es el de ninguno de los dos.
    """

    from src.intelligence.bid_outcome_ledger import summary

    falso = {
        "version": "V1.0",
        "bids": {
            "1:a": {
                "player_id": 1,
                "outcome": "WON",
                "target_source": "SUBASTA_CARTERA",
            },
            "2:b": {
                "player_id": 2,
                "outcome": "LOST",
                "target_source": "SPECULATION_SCORING",
            },
        },
    }

    todas = summary(falso)
    cartera = summary(falso, target_source="SUBASTA_CARTERA")

    assert todas["placed"] == 2
    assert cartera["placed"] == 1, (
        "el filtro por origen no separa nada"
    )
    assert cartera["won"] == 1 and cartera["lost"] == 0


# ============================================================
# 14. NADA DE ESTO LEE EL MUNDO
# ============================================================

def test_el_plan_no_lee_el_mundo():
    """
    Ni disco, ni red, ni reloj: los segundos al reset, el reloj
    de solvencia y los bolsillos se PASAN.

    Se comprueba desde un directorio de trabajo vacio: si algo
    leyera `data/`, aqui cambiaria de respuesta.
    """

    antes = os.getcwd()

    with tempfile.TemporaryDirectory() as vacio:

        try:
            os.chdir(vacio)

            plan = _plan()

        finally:
            os.chdir(antes)

    referencia = _plan()

    assert [b["id"] for b in plan["bids"]] == [
        b["id"] for b in referencia["bids"]
    ], "el plan cambia segun el directorio: esta leyendo algo"

    assert plan["committed"] == referencia["committed"]


TESTS = [
    test_el_interruptor_apaga_todo_con_la_cesta_llena,
    test_la_solvencia_manda_por_encima_de_la_ventana,
    test_con_deficit_no_se_puja_aunque_el_estado_sea_bueno,
    test_fuera_de_la_ventana_no_se_puja,
    test_dentro_de_la_ventana_si_se_puja,
    test_el_bloqueo_temporal_tambien_cierra_la_subasta,
    test_nunca_mas_pujas_que_fichas_libres,
    test_el_tope_del_primer_dia_recorta_a_tres,
    test_el_tope_se_queda_con_las_mejores_no_con_tres_al_azar,
    test_todas_las_pujas_salen_al_precio_topado,
    test_el_peor_caso_cuenta_la_plantilla_que_ya_hay,
    test_el_peor_caso_sale_publicado,
    test_lo_que_se_gana_si_entran_todas_esta_publicado,
    test_sin_en_vivo_calcula_pero_no_ejecuta,
    test_la_compra_a_rivales_sigue_cerrada,
    test_un_jugador_con_puja_viva_no_se_puja_otra_vez,
    test_las_fichas_libres_son_la_mayor_menos_la_nuestra,
    test_el_bloqueo_de_fase_llega_desde_el_estado,
    test_la_forma_no_cambia_con_los_datos,
    test_el_ciclo_lee_el_estado_donde_vive,
    test_lo_pujado_llega_al_libro_con_su_origen,
    test_el_libro_sabe_separar_por_origen,
    test_el_plan_no_lee_el_mundo,
]


def main() -> None:

    print()
    print("=" * 60)
    print("ENCENDER LAS PUJAS V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
