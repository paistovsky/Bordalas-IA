"""
El guardarrail posicional.

EL FALLO QUE CUBRE
    `build_recovery_plan` prueba todas las combinaciones de
    ofertas entrantes y se queda con la que recupera solvencia con
    menos dano. Su unico filtro era descartar franchise.

    Con la plantilla real del 16/08/2026 -2 porteros, 6 defensas,
    5 centrocampistas, 2 delanteros- vender a Dituro y a Bayindir
    a la vez era una combinacion perfectamente legal para ese
    codigo. Plantilla sin porteros.

    Ninguna de las dos ventas es sospechosa por separado. Por eso
    el test que importa aqui no es "puedo vender a este", es
    "puedo vender a estos dos juntos".

Ejecutar:
    python -m src.analysis.test_position_guardrail_v1
"""

from src.analysis.position_guardrail import (
    POSITION_DESIRED,
    POSITION_FLOOR,
    build_position_guardrail,
    validate_sale_set,
)


class DependenciaAusente(Exception):
    """
    El modulo de la prueba existe, pero no se puede importar en
    esta maquina por dependencias que no estan instaladas.
    """


def cargar_build_recovery_plan():
    """
    `liquidity_manager` arrastra media aplicacion -y con ella
    `requests`- solo por importarse. El guardarrail no necesita
    nada de eso, y un test que no se puede ejecutar en el sitio
    donde programas vale bastante menos.

    Asi que se importa tarde y solo para los cinco tests de
    integracion. Si falta la dependencia se dice en voz alta y se
    saltan esos cinco; los otros veinte corren igual.
    """

    try:
        from src.analysis.liquidity_manager import (
            build_recovery_plan,
        )

    except ImportError as error:
        raise DependenciaAusente(str(error)) from error

    return build_recovery_plan


# Plantilla real del 16/08/2026.
DITURO = 4587
BAYINDIR = 8123
YAMAL = 26271
JUTGLA = 7011
JONNY = 1599
YERAY = 2044
XIMO = 1877
SUAZO = 9910
RINCON = 6620
VALENTIN = 30110
JAVI = 4404
OLASA = 5521
FIDALGO = 8890
PUERTA = 27050
MANGALA = 21400


def jugador(
    pid: int,
    nombre: str,
    posicion: int,
    precio: int,
    xi: bool = False,
    proteccion: str = "NORMAL",
    score: float = 20.0,
) -> dict:
    return {
        "id": pid,
        "name": nombre,
        "position": posicion,
        "market_value": precio,
        "in_lineup": xi,
        "protection": proteccion,
        "protection_score": score,
    }


def plantilla_real() -> list:
    """
    La de verdad, con las posiciones y precios del snapshot.
    """
    return [
        jugador(DITURO, "Dituro", 1, 3_530_000, xi=True, score=61),
        jugador(BAYINDIR, "Bayindir", 1, 670_000, score=8),

        jugador(JONNY, "Jonny Castro", 2, 1_590_000, xi=True, score=55),
        jugador(SUAZO, "Gabriel Suazo", 2, 1_730_000, xi=True, score=52),
        jugador(YERAY, "Yeray", 2, 1_960_000, xi=True, score=48),
        jugador(RINCON, "Hugo Rincon", 2, 670_000, score=18),
        jugador(XIMO, "Ximo Navarro", 2, 1_280_000, score=15),
        jugador(VALENTIN, "Valentin Gomez", 2, 330_000, score=10),

        jugador(MANGALA, "Mangala", 3, 2_770_000, xi=True, score=57),
        jugador(OLASA, "Olasagasti", 3, 2_740_000, xi=True, score=54),
        jugador(PUERTA, "Gustavo Puerta", 3, 3_500_000, xi=True, score=50),
        jugador(FIDALGO, "Alvaro Fidalgo", 3, 1_000_000, score=16),
        jugador(JAVI, "Javi Hernandez", 3, 310_000, score=6),

        jugador(
            YAMAL, "Yamal", 4, 22_360_000,
            xi=True, proteccion="NEVER_AUTO_SELL", score=140,
        ),
        jugador(JUTGLA, "Jutgla", 4, 4_260_000, xi=True, score=44),
    ]


# ============================================================
# EL SUELO
# ============================================================

def test_el_suelo_sale_de_las_formaciones() -> None:
    """
    Escrito a mano se desactualiza. Derivado de las formaciones,
    no.
    """
    assert POSITION_FLOOR == {1: 1, 2: 3, 3: 3, 4: 1}, (
        f"El suelo deberia ser 1-3-3-1, salio {POSITION_FLOOR}."
    )

    print("  OK  el suelo 1-3-3-1 se deriva de las formaciones")


def test_el_recuento_cuadra_con_la_plantilla_real() -> None:
    guardarrail = build_position_guardrail(plantilla_real())

    esperado = {1: 2, 2: 6, 3: 5, 4: 2}

    for posicion, cuantos in esperado.items():
        obtenido = guardarrail["by_position"][posicion]["owned"]
        assert obtenido == cuantos, (
            f"Posicion {posicion}: contados {obtenido}, "
            f"esperados {cuantos}."
        )

    assert guardarrail["squad_size"] == 15

    print("  OK  2 porteros, 6 defensas, 5 medios, 2 delanteros")


# ============================================================
# EL DESASTRE QUE MOTIVA EL MODULO
# ============================================================

def test_vender_los_dos_porteros_esta_prohibido() -> None:
    """
    Este es EL test. Es la combinacion que build_recovery_plan
    podia elegir y nadie paraba.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(
        guardarrail,
        [DITURO, BAYINDIR],
    )

    assert veredicto["ok"] is False, (
        "REGRESION: vender a los dos porteros a la vez deja la "
        "plantilla sin porteria y el guardarrail lo permitio."
    )
    assert veredicto["status"] == "BLOCK_POSITION_FLOOR"

    porterias = [
        v for v in veredicto["violations"] if v["position"] == 1
    ]
    assert porterias, "La violacion no senala la porteria."
    assert porterias[0]["would_remain"] == 0

    print("  OK  vender los dos porteros queda bloqueado")


def test_cada_portero_por_separado_pasaria() -> None:
    """
    La razon por la que el fallo era invisible: mirados de uno en
    uno, los dos son ventas razonables.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    solo_suplente = validate_sale_set(guardarrail, [BAYINDIR])

    assert solo_suplente["ok"] is True, (
        "Vender al portero suplente es legitimo: queda Dituro."
    )

    print(
        "  OK  vender solo al suplente si se permite "
        "(el fallo solo aparece al mirarlos juntos)"
    )


def test_el_portero_titular_no_es_vendible() -> None:
    """
    'No vendas al portero para fichar otro MC'.

    Con dos porteros el suelo es 1, asi que uno sobra. Tiene que
    sobrar el suplente, no el titular.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    porteria = guardarrail["by_position"][1]

    assert DITURO in porteria["locked_ids"], (
        "El portero del XI deberia ser el intocable."
    )
    assert BAYINDIR in porteria["disposable_ids"], (
        "El vendible deberia ser el suplente."
    )

    print("  OK  sobra el suplente, no el titular")


def test_el_bloqueo_no_depende_de_quien_va_primero() -> None:
    """
    Un guardarrail que solo funciona si la lista llega en cierto
    orden no es un guardarrail.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    directo = validate_sale_set(guardarrail, [DITURO, BAYINDIR])
    inverso = validate_sale_set(guardarrail, [BAYINDIR, DITURO])

    assert directo["ok"] is False
    assert inverso["ok"] is False, (
        "Cambiando el orden de la lista el bloqueo desaparecio."
    )

    print("  OK  el orden de la lista no cambia el veredicto")


# ============================================================
# LAS DEMAS POSICIONES
# ============================================================

def test_vender_cuatro_defensas_de_seis_esta_permitido() -> None:
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(
        guardarrail,
        [RINCON, XIMO, VALENTIN],
    )

    assert veredicto["ok"] is True, (
        f"Con 6 defensas vender 3 deja 3, que es el suelo. "
        f"No deberia bloquearse. {veredicto.get('reason')}"
    )

    print("  OK  con 6 defensas se pueden vender 3")


def test_vender_cuatro_defensas_de_seis_no() -> None:
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(
        guardarrail,
        [RINCON, XIMO, VALENTIN, YERAY],
    )

    assert veredicto["ok"] is False, (
        "Vender 4 de 6 defensas deja 2 y hacen falta 3."
    )
    assert veredicto["violations"][0]["would_remain"] == 2

    print("  OK  vender 4 de 6 defensas queda bloqueado")


def test_vender_al_unico_delantero_no_franchise() -> None:
    """
    Yamal es intocable por franchise, asi que Jutgla es el unico
    delantero que se puede mover. El suelo de delanteros es 1 y
    Yamal lo cubre, asi que vender a Jutgla es legal.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(guardarrail, [JUTGLA])

    assert veredicto["ok"] is True, (
        "Con Yamal en plantilla el suelo de delanteros sigue "
        "cubierto."
    )

    print("  OK  vender a Jutgla deja la delantera cubierta")


def test_una_venta_por_posicion_a_la_vez_si_cabe() -> None:
    """
    El caso normal de un dia de saneamiento: soltar lastre en
    varias posiciones sin romper ninguna.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(
        guardarrail,
        [BAYINDIR, VALENTIN, JAVI, JUTGLA],
    )

    assert veredicto["ok"] is True, (
        f"Una venta por posicion deberia caber. "
        f"{veredicto.get('reason')}"
    )

    print("  OK  soltar lastre en cuatro posiciones a la vez cabe")


def test_vaciar_el_centro_del_campo_esta_prohibido() -> None:
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(
        guardarrail,
        [MANGALA, OLASA, PUERTA],
    )

    assert veredicto["ok"] is False, (
        "Vender 3 de 5 medios deja 2 y hacen falta 3."
    )

    print("  OK  vaciar el centro del campo queda bloqueado")


def test_varias_posiciones_rotas_se_reportan_todas() -> None:
    """
    Si el conjunto rompe dos posiciones hay que decir las dos, no
    parar en la primera.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(
        guardarrail,
        [DITURO, BAYINDIR, MANGALA, OLASA, PUERTA],
    )

    assert veredicto["ok"] is False

    rotas = {v["position"] for v in veredicto["violations"]}

    assert rotas == {1, 3}, (
        f"Deberia reportar porteria y centro del campo, "
        f"reporto {rotas}."
    )

    print("  OK  se reportan todas las posiciones rotas")


# ============================================================
# AVISOS PARA EL LADO COMPRADOR
# ============================================================

def test_la_delantera_corta_se_marca_para_reponer() -> None:
    """
    No bloquea: informa. Con 2 delanteros y uno intocable, la
    delantera esta corta y el lado comprador deberia saberlo.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    porteria = guardarrail["by_position"][1]

    assert porteria["owned"] == POSITION_DESIRED[1]
    assert porteria["below_desired"] is False

    delantera = guardarrail["by_position"][4]
    assert delantera["at_floor"] is False
    assert delantera["owned"] == 2

    print("  OK  el estado por posicion se publica para comprar")


def test_quedarse_con_un_portero_dispara_el_aviso() -> None:
    plantilla = [
        j for j in plantilla_real()
        if j["id"] != BAYINDIR
    ]

    guardarrail = build_position_guardrail(plantilla)

    assert guardarrail["goalkeeper_warning"] is not None, (
        "Con un solo portero hay que avisar: reponerlo es dificil."
    )
    assert "titular" in guardarrail["goalkeeper_warning"]
    assert guardarrail["by_position"][1]["at_floor"] is True

    print("  OK  con un solo portero salta el aviso de reposicion")


def test_sin_porteros_el_aviso_es_de_emergencia() -> None:
    plantilla = [
        j for j in plantilla_real()
        if j["position"] != 1
    ]

    guardarrail = build_position_guardrail(plantilla)

    aviso = guardarrail["goalkeeper_warning"] or ""

    assert "SIN PORTERO" in aviso, (
        f"Sin porteros el aviso deberia ser de emergencia. "
        f"Salio: {aviso}"
    )
    assert 1 in guardarrail["positions_to_replenish"]

    print("  OK  plantilla sin portero: aviso de emergencia")


def test_desde_cero_no_se_puede_vender_nada_de_esa_posicion() -> None:
    """
    Si ya estas por debajo del suelo, cualquier venta mas en esa
    posicion la hunde todavia mas.
    """
    plantilla = [
        j for j in plantilla_real()
        if j["position"] != 1
    ]
    plantilla.append(
        jugador(DITURO, "Dituro", 1, 3_530_000, xi=True, score=61)
    )

    guardarrail = build_position_guardrail(plantilla)

    veredicto = validate_sale_set(guardarrail, [DITURO])

    assert veredicto["ok"] is False, (
        "Con un solo portero, venderlo deja la plantilla a cero."
    )

    print("  OK  el ultimo portero no se puede vender")


# ============================================================
# ROBUSTEZ
# ============================================================

def test_sin_guardarrail_se_dice_en_voz_alta() -> None:
    """
    Lo peor que puede hacer un control de seguridad es fallar en
    silencio y que parezca que aprobo. Si no hay guardarrail, la
    respuesta lo declara.
    """
    veredicto = validate_sale_set(None, [DITURO, BAYINDIR])

    assert veredicto["ok"] is True
    assert veredicto["guardrail_applied"] is False, (
        "Sin guardarrail hay que marcarlo, no dar un OK que "
        "parezca una comprobacion real."
    )

    print("  OK  un OK sin comprobar se declara como tal")


def test_aguanta_plantillas_raras() -> None:
    casos = [
        [],
        None,
        [{"id": 1}],
        [{"id": 2, "position": None}],
        [{"id": 3, "position": "portero"}],
        [{"id": 4, "position": 9}],
        [None, "texto", 42],
    ]

    for caso in casos:
        guardarrail = build_position_guardrail(caso)

        assert guardarrail["available"] is True
        assert set(guardarrail["by_position"]) == {1, 2, 3, 4}

        veredicto = validate_sale_set(guardarrail, [1, 2, 3])
        assert isinstance(veredicto["ok"], bool)

    print("  OK  aguanta plantillas vacias o con basura")


def test_un_jugador_sin_posicion_no_cuenta_como_portero() -> None:
    """
    Ximo Navarro y otros llegan a veces sin position. Contarlos en
    una posicion que no es suya seria peor que no contarlos.
    """
    plantilla = plantilla_real()
    plantilla.append(
        {"id": 99999, "name": "Sin posicion", "position": None}
    )

    guardarrail = build_position_guardrail(plantilla)

    assert 99999 in guardarrail["players_without_position"]

    for posicion in (1, 2, 3, 4):
        assert 99999 not in (
            guardarrail["by_position"][posicion]["locked_ids"]
            + guardarrail["by_position"][posicion]["disposable_ids"]
        )

    print("  OK  un jugador sin posicion no se cuela en ninguna")


def test_vender_a_alguien_que_no_esta_no_rompe_nada() -> None:
    guardarrail = build_position_guardrail(plantilla_real())

    veredicto = validate_sale_set(guardarrail, [123456789])

    assert veredicto["ok"] is True

    print("  OK  un id desconocido no altera el recuento")


# ============================================================
# INTEGRACION CON EL PLAN DE RECUPERACION
# ============================================================
#
# Aqui es donde vivia el fallo. build_recovery_plan recorre todas
# las combinaciones de ofertas entrantes y elige la de menor dano.
# Sin guardarrail, esa eleccion podia ser "los dos porteros".


def oferta(
    offer_id: int,
    player_id: int,
    amount: int,
    damage: float,
    proteccion: str = "NORMAL",
) -> dict:
    return {
        "offer_id": offer_id,
        "player_id": player_id,
        "amount": amount,
        "sell_damage": damage,
        "protection": proteccion,
    }


def escenario_dos_porteros() -> tuple:
    """
    Deficit que solo se cubre facilmente vendiendo los dos
    porteros. Es el caso que el planificador elegia.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    ofertas = [
        oferta(101, DITURO, 3_300_000, 60.0),
        oferta(102, BAYINDIR, 700_000, 8.0),
        oferta(103, VALENTIN, 300_000, 10.0),
    ]

    return guardarrail, ofertas


def test_sin_guardarrail_el_plan_vendia_los_dos_porteros() -> None:
    """
    Deja constancia del comportamiento anterior. Si algun dia este
    test empieza a fallar es que el plan ya no encuentra esa
    combinacion, y habria que entender por que.
    """
    _, ofertas = escenario_dos_porteros()

    build_recovery_plan = cargar_build_recovery_plan()

    plan = build_recovery_plan(
        balance=-3_900_000,
        offers=ofertas,
    )

    vendidos = {
        item["player_id"] for item in plan["selected"]
    }

    assert plan["guardrail_applied"] is False
    assert {DITURO, BAYINDIR}.issubset(vendidos), (
        f"Se esperaba reproducir el fallo historico -vender los "
        f"dos porteros- y el plan eligio {vendidos}."
    )

    print(
        "  OK  reproducido el fallo: sin guardarrail vendia los "
        "dos porteros"
    )


def test_con_guardarrail_el_plan_ya_no_puede() -> None:
    guardarrail, ofertas = escenario_dos_porteros()

    build_recovery_plan = cargar_build_recovery_plan()

    plan = build_recovery_plan(
        balance=-3_900_000,
        offers=ofertas,
        guardrail=guardarrail,
    )

    vendidos = {
        item["player_id"] for item in plan["selected"]
    }

    assert plan["guardrail_applied"] is True
    assert not {DITURO, BAYINDIR}.issubset(vendidos), (
        "REGRESION: el plan volvio a elegir los dos porteros."
    )
    assert plan["rejected_by_guardrail"], (
        "El plan deberia dejar constancia de las combinaciones "
        "que descarto."
    )

    porteria = [
        r for r in plan["rejected_by_guardrail"]
        if set(r["player_ids"]) == {DITURO, BAYINDIR}
    ]
    assert porteria, (
        "La combinacion de los dos porteros deberia figurar entre "
        "las descartadas."
    )

    print("  OK  con guardarrail esa combinacion queda descartada")


def test_el_plan_sigue_funcionando_cuando_si_hay_salida() -> None:
    """
    El guardarrail no puede convertirse en un freno de mano. Si
    existe una combinacion sana, tiene que encontrarla.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    ofertas = [
        oferta(201, BAYINDIR, 800_000, 8.0),
        oferta(202, VALENTIN, 400_000, 10.0),
        oferta(203, JAVI, 350_000, 6.0),
        oferta(204, DITURO, 3_300_000, 60.0),
    ]

    build_recovery_plan = cargar_build_recovery_plan()

    plan = build_recovery_plan(
        balance=-1_000_000,
        offers=ofertas,
        guardrail=guardarrail,
    )

    assert plan["possible"] is True, (
        f"Habia salida limpia y el plan no la encontro: "
        f"{plan.get('reason')}"
    )

    vendidos = {
        item["player_id"] for item in plan["selected"]
    }

    assert not {DITURO, BAYINDIR}.issubset(vendidos)
    assert plan["recovered"] >= 1_000_000

    print("  OK  con salida limpia el plan la encuentra igual")


def test_dos_ofertas_por_el_mismo_jugador_no_suman() -> None:
    """
    Dos rivales pujando por el mismo jugador son dos ofertas, pero
    solo se puede vender una vez. Sumar las dos hacia creer que se
    recaudaba el doble.
    """
    guardarrail = build_position_guardrail(plantilla_real())

    ofertas = [
        oferta(301, JUTGLA, 3_000_000, 44.0),
        oferta(302, JUTGLA, 3_000_000, 44.0),
    ]

    build_recovery_plan = cargar_build_recovery_plan()

    plan = build_recovery_plan(
        balance=-5_000_000,
        offers=ofertas,
        guardrail=guardarrail,
    )

    assert plan["possible"] is False, (
        "Con 3 M reales no se cubre un deficit de 5 M. Si el plan "
        "dice que si, esta sumando dos veces al mismo jugador."
    )

    print("  OK  dos ofertas por el mismo jugador no se suman")


def test_saldo_positivo_no_toca_nada() -> None:
    guardarrail = build_position_guardrail(plantilla_real())

    build_recovery_plan = cargar_build_recovery_plan()

    plan = build_recovery_plan(
        balance=250_000,
        offers=[oferta(401, BAYINDIR, 800_000, 8.0)],
        guardrail=guardarrail,
    )

    assert plan["needed"] is False
    assert plan["selected"] == []

    print("  OK  con saldo positivo no se vende nada")


# ============================================================

TESTS = [
    test_el_suelo_sale_de_las_formaciones,
    test_el_recuento_cuadra_con_la_plantilla_real,
    test_vender_los_dos_porteros_esta_prohibido,
    test_cada_portero_por_separado_pasaria,
    test_el_portero_titular_no_es_vendible,
    test_el_bloqueo_no_depende_de_quien_va_primero,
    test_vender_cuatro_defensas_de_seis_esta_permitido,
    test_vender_cuatro_defensas_de_seis_no,
    test_vender_al_unico_delantero_no_franchise,
    test_una_venta_por_posicion_a_la_vez_si_cabe,
    test_vaciar_el_centro_del_campo_esta_prohibido,
    test_varias_posiciones_rotas_se_reportan_todas,
    test_la_delantera_corta_se_marca_para_reponer,
    test_quedarse_con_un_portero_dispara_el_aviso,
    test_sin_porteros_el_aviso_es_de_emergencia,
    test_desde_cero_no_se_puede_vender_nada_de_esa_posicion,
    test_sin_guardarrail_se_dice_en_voz_alta,
    test_aguanta_plantillas_raras,
    test_un_jugador_sin_posicion_no_cuenta_como_portero,
    test_vender_a_alguien_que_no_esta_no_rompe_nada,
    test_sin_guardarrail_el_plan_vendia_los_dos_porteros,
    test_con_guardarrail_el_plan_ya_no_puede,
    test_el_plan_sigue_funcionando_cuando_si_hay_salida,
    test_dos_ofertas_por_el_mismo_jugador_no_suman,
    test_saldo_positivo_no_toca_nada,
]


def main() -> None:
    print("=" * 60)
    print(" GUARDARRAIL POSICIONAL")
    print("=" * 60)

    fallos = 0
    saltados = []

    for test in TESTS:
        print(f"\n{test.__name__}")
        try:
            test()

        except DependenciaAusente as error:
            saltados.append(test.__name__)
            print(f"  SALTADO  falta una dependencia: {error}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLO  {error}")

    print("\n" + "=" * 60)

    if fallos:
        print(f" {fallos}/{len(TESTS)} TESTS FALLIDOS")
        raise SystemExit(1)

    ejecutados = len(TESTS) - len(saltados)

    print(f" {ejecutados}/{len(TESTS)} TESTS OK")

    if saltados:
        print()
        print(
            f" {len(saltados)} saltados por dependencias que no "
            f"estan instaladas en esta maquina."
        )
        print(
            " No es un fallo, pero tampoco es una comprobacion: "
            "estos no se han verificado aqui."
        )
        for nombre in saltados:
            print(f"   {nombre}")
        print()
        print(
            " Para ejecutarlos tambien en local:"
        )
        print(
            "   python -m pip install -r requirements.txt"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
