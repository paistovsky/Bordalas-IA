"""
Poner el dinero a trabajar: bolsillo, ficha vacia y
concentracion.

SINTOMA

    3.400.000 EUR parados en caja, tres fichas de plantilla
    vacias y 8.561.940 EUR en el bolsillo de FICHAR sin tocar,
    mientras cinco candidatos se rechazaban por "supera
    presupuesto".

CAUSA

    1. EL BOLSILLO. El `intent` salia de la via que diera MAS
       EUROS, no de que clase de operacion era. Como la reventa
       al Computer ganaba en 21 de 22, los 22 salian SPECULATION
       y se median contra los 3,5 M de especular mientras los
       8,5 M de fichar seguian intactos.

    2. LA FICHA VACIA. No existia la operacion "fichar sin
       sustituir a nadie": `candidatos_a_salir` es una lista de un
       solo elemento.

    3. Y no habia ningun tope de concentracion, con Yamal al 41 %
       de la plantilla.

CONSECUENCIA

    Esta guardia fija las tres piezas y, sobre todo, que TODAS
    estan bajo un interruptor apagado: con `DEPLOYMENT_ENABLED`
    en False, Pepe decide exactamente igual que el 09/09.
"""

from __future__ import annotations

import os
import subprocess
import sys

from pathlib import Path

from src.analysis.concentration_guardrail import (
    MAX_PLAYER_SHARE,
    MAX_SAME_TEAM,
    build_concentration,
    check_purchase,
)
from src.analysis.deployment import (
    DEPLOYMENT_ENABLED,
    MIN_HIERARCHY_VALUE,
    MIN_STARTER_PERCENT,
    SIGNING,
    TRADE,
    classify_operation,
    roster_fill_veto,
)


# ============================================================
# 1. EL INTERRUPTOR, QUE ES LO PRIMERO
# ============================================================


def test_apagado_de_serie() -> None:
    """
    Esto cambia lo que Pepe compra. Se enciende por la mañana,
    despues de leer la lista, y no antes.
    """

    assert DEPLOYMENT_ENABLED is False


def test_el_interruptor_esta_en_UN_solo_sitio() -> None:
    """
    Un interruptor repartido por tres ficheros no es un
    interruptor: es una forma de dejarse uno encendido.
    """

    # Las guardias no cuentan: nombran el interruptor para
    # comprobarlo, no lo definen.
    definiciones = [
        ruta
        for ruta in Path("src").rglob("*.py")
        if not ruta.name.startswith("test_")
        and "DEPLOYMENT_ENABLED = " in ruta.read_text(encoding="utf-8")
    ]

    assert len(definiciones) == 1, (
        f"el interruptor se define en {len(definiciones)} sitios: "
        f"{[str(r) for r in definiciones]}"
    )
    assert definiciones[0].name == "deployment.py"


def test_encendido_cambia_de_verdad_lo_que_decide() -> None:
    """
    Un interruptor que no cambia nada al encenderse no protege de
    nada: se comprueba de verdad, en otro proceso.
    """

    guion = (
        "from src.analysis.acquisition_valuation import ("
        "build_valuation_context, value_candidate); "
        "ctx = build_valuation_context("
        "{'my_team': [], 'catalog': {'data': {'players': {}}}, "
        "'market': {'offers': [], 'sales': []}}, "
        "velocity_lookup={}, starter_lookup={}, market_rates={}, "
        "free_roster_slots=3); "
        "v = value_candidate({'id': 900, 'name': 'X', 'position': 3, "
        "'price': 1000000, 'priceIncrement': 0, 'points': 10, "
        "'pointsLastSeason': 100, 'status': 'ok', 'teamID': 1}, ctx); "
        "print((v.get('deployment') or {}).get('enabled'))"
    )

    entorno = dict(os.environ)
    entorno["DEPLOYMENT_ENABLED"] = "1"

    proceso = subprocess.run(
        [sys.executable, "-c", guion],
        capture_output=True,
        text=True,
        env=entorno,
    )

    assert proceso.returncode == 0, proceso.stderr[-400:]
    assert "True" in proceso.stdout, (
        f"con la variable de entorno puesta el interruptor sigue "
        f"apagado: {proceso.stdout!r}"
    )


# ============================================================
# 2. EL BOLSILLO, POR CLASE DE OPERACION
# ============================================================


def _via(valor, route, intent="SPECULATION"):
    return {"value": valor, "route": route, "intent": intent}


def test_un_fichaje_es_un_fichaje_aunque_la_reventa_de_mas() -> None:
    """
    EL FALLO EXACTO.

    Un jugador que mejora el once y ademas se podria revender
    salia SPECULATION porque la reventa daba mas euros, y se
    medía contra el bolsillo estrecho.
    """

    c = classify_operation(
        _via(100_000, "XI_UPGRADE", "XI_UPGRADE"),
        None,
        None,
        _via(500_000, "COMPUTER_RESALE"),
    )

    assert c["operation_class"] == SIGNING
    assert c["intent"] == "XI_UPGRADE", (
        "sigue enrutando al bolsillo de especular un fichaje"
    )
    assert "aunque su reventa diera mas euros" in c["reason"]


def test_el_valor_sigue_siendo_el_mayor_de_todas_las_vias() -> None:
    """
    Cambia de que bolsillo se paga, no cuanto vale. Si ademas se
    puede revender, el jugador vale al menos eso.
    """

    c = classify_operation(
        _via(100_000, "XI_UPGRADE", "XI_UPGRADE"),
        None,
        None,
        _via(500_000, "COMPUTER_RESALE"),
    )

    assert c["value"] == 500_000
    assert c["value_route"] == "COMPUTER_RESALE"


def test_llenar_un_hueco_tambien_es_fichar() -> None:
    c = classify_operation(
        None,
        _via(300_000, "ROSTER_FILL", "XI_UPGRADE"),
        None,
        _via(400_000, "COMPUTER_RESALE"),
    )

    assert c["operation_class"] == SIGNING
    assert c["intent"] == "XI_UPGRADE"
    assert "ficha vacia" in c["reason"]


def test_lo_que_solo_vale_para_revender_es_comerciar() -> None:
    c = classify_operation(
        None, None, _via(200_000, "PRICE_TREND"), _via(150_000, "COMPUTER_RESALE")
    )

    assert c["operation_class"] == TRADE
    assert c["intent"] == "SPECULATION"


def test_sin_ninguna_via_no_se_inventa_una_clase() -> None:
    c = classify_operation(None, None, None, None)

    assert c["operation_class"] is None
    assert c["intent"] is None, (
        "un intent inventado haria que `budget_for_intent` "
        "devolviese un bolsillo que no toca"
    )
    assert c["value"] == 0


def test_una_via_a_cero_no_cuenta_como_via() -> None:
    c = classify_operation(
        _via(0, "XI_UPGRADE", "XI_UPGRADE"),
        None,
        None,
        _via(500_000, "COMPUTER_RESALE"),
    )

    assert c["operation_class"] == TRADE, (
        "una via que no da valor no convierte la operacion en un "
        "fichaje"
    )


# ============================================================
# 3. LA FICHA VACIA, CON SUS FILTROS
# ============================================================


def test_un_titular_de_verdad_puede_ocupar_una_ficha() -> None:
    assert roster_fill_veto(
        {"probability": 80.0, "hierarchy_value": 60}
    ) is None


def test_un_suplente_no_ocupa_una_ficha() -> None:
    """
    EL AVISO DEL 05/09.

    De 18 fichables, los dos unicos baratos por punto eran
    suplentes. Una via de ampliacion sin filtro empuja al bucle
    de las catorce defensas.
    """

    motivo = roster_fill_veto(
        {"probability": MIN_STARTER_PERCENT - 1, "hierarchy_value": 60}
    )

    assert motivo is not None
    assert "suplente" in motivo


def test_un_descarte_de_su_equipo_tampoco() -> None:
    motivo = roster_fill_veto(
        {
            "probability": 80.0,
            "hierarchy_value": MIN_HIERARCHY_VALUE - 1,
            "hierarchy_label": "Descarte",
        }
    )

    assert motivo is not None
    assert "catorce defensas" in motivo, (
        "el filtro tiene que decir de que bucle protege"
    )


def test_sin_pronostico_no_se_ocupa_una_ficha_a_ciegas() -> None:
    motivo = roster_fill_veto(None)

    assert motivo is not None
    assert "a ciegas" in motivo


def test_no_se_llena_un_hueco_con_quien_no_puede_jugar() -> None:
    motivo = roster_fill_veto(
        {
            "probability": 80.0,
            "hierarchy_value": 60,
            "availability": {"can_play": False, "label": "LESIONADO"},
        }
    )

    assert motivo is not None
    assert "LESIONADO" in motivo


def test_el_hueco_es_un_dato_no_una_incognita() -> None:
    """
    `xi_upgrade_value` veta con SIN_PRONOSTICO cuando no hay
    pronostico DEL QUE SALE. En un hueco no sale nadie, y pasarle
    `None` disparaba un veto pensado para otra cosa: la via de
    relleno no valoraba a nadie.

    Una ficha vacia juega el 0 % de los minutos, con certeza. Eso
    es un dato.
    """

    fuente = Path(
        "src/analysis/acquisition_valuation.py"
    ).read_text(encoding="utf-8")

    assert '"probability": 0.0' in fuente
    assert "FICHA VACIA" in fuente


def test_sin_huecos_la_via_no_se_abre() -> None:
    from src.analysis.acquisition_valuation import (
        build_valuation_context,
        value_candidate,
    )

    contexto = build_valuation_context(
        {
            "my_team": [],
            "catalog": {"data": {"players": {}}},
            "market": {"offers": [], "sales": []},
        },
        velocity_lookup={},
        starter_lookup={},
        market_rates={},
        free_roster_slots=0,
    )

    v = value_candidate(
        {
            "id": 900, "name": "X", "position": 3, "price": 1_000_000,
            "priceIncrement": 0, "points": 10, "pointsLastSeason": 100,
            "status": "ok", "teamID": 1,
        },
        contexto,
    )

    assert v.get("as_roster_fill") is None, (
        "se ha valorado un relleno sin fichas libres"
    )
    assert (v.get("deployment") or {})["free_roster_slots"] == 0


# ============================================================
# 4. LA CONCENTRACION, CON NUMEROS DE LA LIGA
# ============================================================


def _plantilla(*precios_equipos):
    return [
        {"id": i, "name": f"J{i}", "price": p, "teamID": e}
        for i, (p, e) in enumerate(precios_equipos, start=1)
    ]


def test_los_topes_salen_de_lo_que_hacen_los_que_van_delante() -> None:
    """
    Medido el 10/09 sobre las siete plantillas: los tres que van
    por delante estan entre el 19,0 % y el 32,2 % en su mayor
    jugador. Los dos mas concentrados -Prinzipote 44,9 % y Pepe
    41,1 %- van sextos y cuartos.

    Y nadie en la liga lleva cinco jugadores del mismo club; el
    lider lleva cuatro.
    """

    assert 0.32 < MAX_PLAYER_SHARE < 0.41, (
        f"el tope por jugador ({MAX_PLAYER_SHARE}) se ha salido de "
        f"la banda que justifican los datos: por encima del 32,2 % "
        f"de los lideres y por debajo del 41,1 % de Pepe"
    )
    assert MAX_SAME_TEAM == 4, "es lo que lleva el lider"


def test_se_mide_la_concentracion_de_hoy() -> None:
    c = build_concentration(
        _plantilla((5_000_000, 1), (3_000_000, 1), (2_000_000, 2))
    )

    assert c["available"] is True
    assert c["squad_value"] == 10_000_000
    assert c["max_player_share"] == 0.5
    assert c["max_same_team"] == 2
    assert c["breach_count"] == 1, (
        "un jugador al 50 % con el tope en 35 % es un "
        "incumplimiento"
    )


def test_avisa_pero_no_obliga_a_vender() -> None:
    """
    Como el resto de guardarrailes de la casa: avisan y acotan.
    Una plantilla que YA esta por encima no fuerza una venta.
    """

    c = build_concentration(_plantilla((5_000_000, 1), (1_000_000, 2)))

    incumple = c["breaches"][0]

    assert "No obliga a venderlo" in incumple["reason"]


def test_el_denominador_incluye_la_compra() -> None:
    """
    Comprar SUBE el valor de la plantilla, asi que la parte del
    comprado es `precio / (plantilla + precio)`. Con la otra
    formula el tope morderia mucho antes y por una cuenta que no
    es la real.
    """

    c = build_concentration(_plantilla((1_000_000, 1)))

    # Con plantilla de 1 M y tope 0,35: P <= 0,35*1M/0,65 = 538.461
    r = check_purchase(c, 538_000, team_id=2)
    assert r["capped"] is False

    r = check_purchase(c, 600_000, team_id=2)
    assert r["capped"] is True
    assert r["allowed"] == int(MAX_PLAYER_SHARE * 1_000_000 / (1 - MAX_PLAYER_SHARE))


def test_el_quinto_del_mismo_club_no_entra() -> None:
    c = build_concentration(
        _plantilla(*[(1_000_000, 7) for _ in range(MAX_SAME_TEAM)])
    )

    r = check_purchase(c, 100_000, team_id=7)

    assert r["capped"] is True
    assert r["allowed"] == 0
    assert "calendario" in r["reason"], (
        "el motivo tiene que decir por que importa: comparten "
        "calendario"
    )

    # Y de otro club si.
    assert check_purchase(c, 100_000, team_id=8)["capped"] is False


def test_sin_plantilla_no_acota_nada() -> None:
    for basura in (None, [], [{}], "texto"):
        c = build_concentration(basura)
        assert c["available"] is False
        assert check_purchase(c, 1_000_000)["capped"] is False


# ============================================================
# 5. Y CON EL INTERRUPTOR APAGADO, NADA CAMBIA
# ============================================================


def test_apagado_el_intent_sigue_saliendo_de_los_euros() -> None:
    fuente = Path(
        "src/analysis/acquisition_valuation.py"
    ).read_text(encoding="utf-8")

    assert 'if DEPLOYMENT_ENABLED and clase["intent"]' in fuente, (
        "el bolsillo nuevo ha dejado de estar bajo interruptor"
    )


def test_apagado_la_ficha_vacia_no_compite() -> None:
    fuente = Path(
        "src/analysis/acquisition_valuation.py"
    ).read_text(encoding="utf-8")

    assert "if DEPLOYMENT_ENABLED\n                else (como_xi, como_trading, como_reventa)" in fuente, (
        "la via de ficha vacia ha entrado a competir sin "
        "interruptor"
    )


def test_apagado_la_concentracion_no_acota() -> None:
    fuente = Path(
        "src/analysis/acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert "DEPLOYMENT_ENABLED\n                    and tope.get(\"capped\")" in fuente, (
        "el tope de concentracion recorta presupuestos sin "
        "interruptor"
    )


def test_no_se_ha_subido_ningun_tope() -> None:
    """
    La regla mas importante del encargo: el dinero no esta parado
    porque los limites sean estrechos.
    """

    from src.analysis.rival_bid_model import (
        MIN_SPECULATION_EXPECTED_VALUE,
        MIN_SPECULATION_YIELD,
    )
    from src.analysis.speculation_engine import (
        MAX_DEBT_SPECULATION_PERCENT,
        MAX_SINGLE_SPECULATION_PERCENT,
        MAX_SPECULATION_BUDGET_PERCENT,
    )

    assert MIN_SPECULATION_YIELD == 0.03
    assert MIN_SPECULATION_EXPECTED_VALUE == 25_000
    assert MAX_SPECULATION_BUDGET_PERCENT == 0.15
    assert MAX_SINGLE_SPECULATION_PERCENT == 0.40
    assert MAX_DEBT_SPECULATION_PERCENT == 0.60


TESTS = [
    test_apagado_de_serie,
    test_el_interruptor_esta_en_UN_solo_sitio,
    test_encendido_cambia_de_verdad_lo_que_decide,
    test_un_fichaje_es_un_fichaje_aunque_la_reventa_de_mas,
    test_el_valor_sigue_siendo_el_mayor_de_todas_las_vias,
    test_llenar_un_hueco_tambien_es_fichar,
    test_lo_que_solo_vale_para_revender_es_comerciar,
    test_sin_ninguna_via_no_se_inventa_una_clase,
    test_una_via_a_cero_no_cuenta_como_via,
    test_un_titular_de_verdad_puede_ocupar_una_ficha,
    test_un_suplente_no_ocupa_una_ficha,
    test_un_descarte_de_su_equipo_tampoco,
    test_sin_pronostico_no_se_ocupa_una_ficha_a_ciegas,
    test_no_se_llena_un_hueco_con_quien_no_puede_jugar,
    test_el_hueco_es_un_dato_no_una_incognita,
    test_sin_huecos_la_via_no_se_abre,
    test_los_topes_salen_de_lo_que_hacen_los_que_van_delante,
    test_se_mide_la_concentracion_de_hoy,
    test_avisa_pero_no_obliga_a_vender,
    test_el_denominador_incluye_la_compra,
    test_el_quinto_del_mismo_club_no_entra,
    test_sin_plantilla_no_acota_nada,
    test_apagado_el_intent_sigue_saliendo_de_los_euros,
    test_apagado_la_ficha_vacia_no_compite,
    test_apagado_la_concentracion_no_acota,
    test_no_se_ha_subido_ningun_tope,
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
    print(f"DESPLIEGUE V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
