"""
Freno y acelerador: el ritmo real manda, y el que cae no se
compra.

SINTOMA

    La valoracion especulativa daba el MISMO numero a jugadores
    con comportamientos opuestos. Sobre la foto del 04/09:

        Bardeli        subio  6,06 % ayer -> precio x 1,0132
        Andre Almeida  subio 17,07 % ayer -> precio x 1,0132
        Nico Guillen   bajo   2,33 % ayer -> precio x 1,0132

CAUSA

    Se reprodujo el numero exacto: sale de
    `computer_resale_value(precio, 0,0176)`. La via que ganaba en
    21 de los 22 candidatos era la de REVENTA AL COMPUTER, cuyo
    premium es una medida de MERCADO -la misma para todos por
    construccion- y no del jugador.

    No era una velocidad rota: era una via que no mira al jugador
    ganandole por euros a la que si lo mira.

CONSECUENCIA

    Cualquier compra especulativa era una moneda al aire, contra
    un mercado en el que el precio de ayer explica el de mañana
    con r = +0,90.

    Esta guardia fija las tres reglas de compra y, sobre todo, lo
    que NO pueden hacer: inventarse una tasa cuando no hay dato,
    tocar la via del once, o saltarse los umbrales.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.market_rate_gate import (
    ALLOW,
    DEMAND_COLLAPSED,
    FALLING,
    NO_FUEL,
    NO_RATE,
    STREAK_DAYS_TO_CHECK_DEMAND,
    build_market_rates,
    evaluate,
)


def _ritmos(**jugadores) -> dict:
    """`{id: señal}` con la forma que produce el ojeador."""

    return {
        int(pid): {
            "rate_percent_per_day": datos[0],
            "direction": (
                "UP" if datos[0] > 0 else "DOWN" if datos[0] < 0 else "FLAT"
            ),
            "trend_days": datos[1] if len(datos) > 1 else None,
            "demand_net": datos[2] if len(datos) > 2 else None,
        }
        for pid, datos in jugadores.items()
    }


# ============================================================
# 1. EL ACELERADOR
# ============================================================


def test_un_ritmo_observado_abre_la_via() -> None:
    r = evaluate(1, _ritmos(**{"1": (2.5, 2, 40.0)}))

    assert r["allow"] is True
    assert r["code"] == ALLOW
    assert r["rate_percent_per_day"] == 2.5


def test_el_ritmo_que_se_proyecta_es_el_del_jugador() -> None:
    """
    Dos jugadores con ritmos distintos tienen que salir con
    numeros distintos. Es TODO el arreglo.
    """

    ritmos = _ritmos(**{"1": (5.0, 3, 40.0), "2": (0.5, 1, 30.0)})

    uno = evaluate(1, ritmos)
    dos = evaluate(2, ritmos)

    assert uno["rate_percent_per_day"] != dos["rate_percent_per_day"], (
        "dos jugadores con ritmos distintos han salido con el mismo "
        "numero: es el fallo que esto viene a cerrar"
    )


def test_sin_ritmo_observado_NO_se_inventa_una_tasa() -> None:
    """
    Volver a la constante seria reintroducir el fallo con otro
    nombre.
    """

    r = evaluate(999, _ritmos())

    assert r["allow"] is False
    assert r["code"] == NO_RATE
    assert r["rate_percent_per_day"] is None
    assert "inventada" in r["reason"]


# ============================================================
# 2. EL FRENO
# ============================================================


def test_un_precio_que_cae_no_se_compra() -> None:
    r = evaluate(1, _ritmos(**{"1": (-2.33, -3, 10.0)}))

    assert r["allow"] is False
    assert r["code"] == FALLING
    assert "90,7 %" in r["reason"], (
        "el motivo tiene que llevar el numero que lo justifica"
    )


def test_no_hay_banda_de_tolerancia_para_caer() -> None:
    """
    De los que bajaron, solo el 0,5 % batio al mercado. No hay
    nada que tolerar.
    """

    assert evaluate(1, _ritmos(**{"1": (-0.01,)}))["allow"] is False


def test_un_precio_quieto_tampoco_es_una_especulacion() -> None:
    r = evaluate(1, _ritmos(**{"1": (0.0,)}))

    assert r["allow"] is False
    assert "quieto" in r["reason"]


def test_la_direccion_manda_sobre_la_magnitud() -> None:
    """
    El ojeador publica la magnitud SIN signo y la direccion
    aparte. Si aqui se leyera la magnitud a pelo, una bajada del
    6 % entraria como una subida del 6 %: el error mas caro
    posible.
    """

    informe = {
        "players": {
            "1": {
                "consensus": {
                    "direction": "DOWN",
                    "mean_magnitude_percent": 6.0,
                },
            }
        }
    }

    ritmos = build_market_rates(informe)

    assert ritmos[1]["rate_percent_per_day"] == -6.0, (
        "una bajada se ha leido como subida"
    )
    assert evaluate(1, ritmos)["allow"] is False


# ============================================================
# 3. EL AVISO: RACHA SIN GASOLINA
# ============================================================


def test_una_racha_con_la_demanda_hundida_no_se_compra() -> None:
    """
    El caso Sangare y Lookman: siete dias subiendo con la demanda
    a -60 y -57 puntos.
    """

    r = evaluate(1, _ritmos(**{"1": (0.63, 7, -60.0)}))

    assert r["allow"] is False
    assert r["code"] == NO_FUEL
    assert "agotandose" in r["reason"]


def test_una_racha_corta_no_se_mira_con_la_demanda() -> None:
    """
    Tras 1 dia subiendo continua el 92 % y tras 2 el 94 %. Solo a
    partir de 3 la continuidad cae al 74 %, y solo ahi tiene
    sentido preguntar si queda gasolina.
    """

    assert STREAK_DAYS_TO_CHECK_DEMAND == 3

    corta = evaluate(
        1, _ritmos(**{"1": (2.0, STREAK_DAYS_TO_CHECK_DEMAND - 1, -60.0)})
    )

    assert corta["allow"] is True, (
        "una racha corta con demanda floja no es una racha agotada"
    )


def test_una_racha_larga_CON_demanda_si_se_compra() -> None:
    r = evaluate(1, _ritmos(**{"1": (2.0, 7, 55.0)}))

    assert r["allow"] is True, (
        "la divergencia sirve para no entrar, no para vetar todas "
        "las rachas"
    )


def test_sin_demanda_medida_la_racha_no_se_veta() -> None:
    """
    La demanda solo la publica Comuniate. Sin ese dato no se
    supone lo peor: se compra por el ritmo, que si esta medido.
    """

    assert evaluate(1, _ritmos(**{"1": (2.0, 7, None)}))["allow"] is True


def test_el_corte_de_demanda_es_el_del_ojeador() -> None:
    assert DEMAND_COLLAPSED == -20.0

    justo = evaluate(1, _ritmos(**{"1": (2.0, 5, DEMAND_COLLAPSED + 1)}))
    pasado = evaluate(1, _ritmos(**{"1": (2.0, 5, DEMAND_COLLAPSED - 1)}))

    assert justo["allow"] is True
    assert pasado["allow"] is False


# ============================================================
# 4. LO QUE LA COMPUERTA NO PUEDE TOCAR
# ============================================================


def _contexto(rates=None, premium=None):
    from src.analysis.acquisition_valuation import build_valuation_context

    return build_valuation_context(
        {
            "my_team": [],
            "catalog": {"data": {"players": {}}},
            "market": {"offers": [], "sales": []},
        },
        velocity_lookup={},
        starter_lookup={},
        computer_premium=premium,
        market_rates=rates or {},
    )


def _jugador(**campos):
    base = {
        "id": 900,
        "name": "Fulano",
        "position": 3,
        "price": 1_000_000,
        "priceIncrement": 20_000,
        "points": 10,
        "pointsLastSeason": 100,
        "status": "ok",
        "teamID": 1,
    }
    base.update(campos)
    return base


def test_la_via_del_once_no_se_toca() -> None:
    """
    Un jugador que cae puede seguir mereciendo la pena por
    razones de futbol. Esa via se decide con puntos, no con el
    precio de ayer.
    """

    from src.analysis.acquisition_valuation import (
        build_valuation_context,
        value_candidate,
    )

    # Hace falta plantilla: sin a quien sustituir, la via del
    # once no se evalua y el test no probaria nada.
    titular = {
        "id": 1,
        "name": "El peor medio",
        "position": 3,
        "price": 500_000,
        "priceIncrement": 0,
        "points": 5,
        "pointsLastSeason": 10,
        "status": "ok",
        "teamID": 2,
    }

    snapshot = {
        "my_team": [titular],
        "catalog": {"data": {"players": {"1": titular}}},
        "market": {"offers": [], "sales": []},
    }

    contexto = build_valuation_context(
        snapshot,
        velocity_lookup={},
        starter_lookup={},
        market_rates=_ritmos(**{"900": (-5.0, -4, 0.0)}),
    )

    valoracion = value_candidate(
        _jugador(pointsLastSeason=300), contexto
    )

    # La via del once tiene que haberse evaluado igualmente, y su
    # motivo no puede ser el de la compuerta.
    como_xi = valoracion.get("as_xi")

    assert como_xi is not None, (
        "la compuerta ha apagado la via del once, que no es suya"
    )
    assert como_xi.get("decision") not in {FALLING, NO_RATE, NO_FUEL}, (
        f"la via del once se ha cerrado con un motivo de la "
        f"compuerta: {como_xi.get('decision')}"
    )


def test_un_precio_que_cae_no_produce_valor_especulativo() -> None:
    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(
        rates=_ritmos(**{"900": (-5.0, -4, 0.0)}),
        premium={
            "available": True,
            "calibrated": True,
            "median_percent": 3.0,
        },
    )

    valoracion = value_candidate(_jugador(), contexto)

    assert valoracion.get("intent") != "SPECULATION", (
        f"se ha valorado como especulacion a uno que cae: "
        f"{valoracion.get('reason')}"
    )


def test_la_reventa_al_computer_NO_exige_ritmo_observado() -> None:
    """
    LA DISTINCION QUE COSTO UNA GUARDIA EN ROJO.

    La reventa al Computer no apuesta a que el jugador suba:
    apuesta a que el Computer paga por encima del mercado en el
    reset. Exigirle un ritmo seria importarle una dependencia que
    no tiene, y apagaria una via de ingresos entera para mas de
    la mitad del tablero solo porque el ojeador no empareja a ese
    jugador.

    Lo destapo `test_reventa_al_computer_v1` poniendose en rojo.
    """

    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(
        rates={},                       # sin ritmo de nadie
        premium={
            "available": True,
            "calibrated": True,
            "median_percent": 3.0,
        },
    )

    valoracion = value_candidate(
        _jugador(price=3_000_000, priceIncrement=0), contexto
    )

    assert valoracion["value"] > 3_000_000, (
        "sin ritmo observado se ha apagado tambien la reventa al "
        "Computer, que no necesita ritmo"
    )
    assert valoracion["route"] == "COMPUTER_RESALE"


def test_pero_un_precio_que_cae_SI_frena_la_reventa() -> None:
    """
    El Computer paga sobre el precio de mercado del reset. Sobre
    una base que encoge, el premium vale menos: es comprar un
    cuchillo cayendo con otro nombre.
    """

    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(
        rates=_ritmos(**{"900": (-4.0, -3, 0.0)}),
        premium={
            "available": True,
            "calibrated": True,
            "median_percent": 3.0,
        },
    )

    valoracion = value_candidate(
        _jugador(price=3_000_000, priceIncrement=0), contexto
    )

    assert valoracion.get("route") != "COMPUTER_RESALE", (
        "se compraria para revender al Computer a uno que se "
        "desploma"
    )


def test_no_se_ha_bajado_ningun_umbral() -> None:
    """
    Bloqueaban todo porque la entrada era una constante. Con el
    ritmo real, un jugador que sube de verdad pasa el 3 % de
    sobra: el umbral no estaba mal, medía un numero inventado.

    Hubo un intento de bajarlos el 03/09 y se revirtio en
    `9bf60c4`.
    """

    from src.analysis.rival_bid_model import (
        MIN_SPECULATION_EXPECTED_VALUE,
        MIN_SPECULATION_YIELD,
    )

    assert MIN_SPECULATION_YIELD == 0.03
    assert MIN_SPECULATION_EXPECTED_VALUE == 25_000


def test_la_compuerta_solo_sabe_decir_que_no() -> None:
    """
    Nunca sube un valor: o deja pasar la valoracion de siempre, o
    la cierra. Asi no puede hacer a Pepe mas agresivo por su
    cuenta.
    """

    import ast

    ruta = Path("src/analysis/market_rate_gate.py")
    fuente = ruta.read_text(encoding="utf-8")

    assert "solo puede decir que NO" in fuente

    # Se mira lo que IMPORTA, no lo que menciona: el docstring
    # nombra los umbrales y los presupuestos a proposito, para
    # decir que no los toca. Buscar la palabra a pelo da un falso
    # positivo sobre su propia documentacion — el mismo error que
    # ya aparecio el 07/09 con el docstring de la puerta.
    arbol = ast.parse(fuente)

    modulos = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            modulos.append(nodo.module or "")
        elif isinstance(nodo, ast.Import):
            modulos.extend(a.name for a in nodo.names)

    for modulo in modulos:
        for prohibido in (
            "speculation_engine",
            "rival_bid_model",
            "acquisition_budget",
        ):
            assert prohibido not in modulo, (
                f"la compuerta importa {modulo}, que no es suyo"
            )

    # Y que no defina umbrales de dinero por su cuenta.
    nombres = {
        objetivo.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Assign)
        for objetivo in nodo.targets
        if isinstance(objetivo, ast.Name)
    }

    for prohibido in ("MIN_SPECULATION_YIELD", "MAX_SINGLE", "BUDGET"):
        assert not any(prohibido in n for n in nombres), (
            f"la compuerta define `{prohibido}`, que no es suyo"
        )


def test_la_comparacion_viaja_con_cada_valoracion() -> None:
    """
    Esto mueve dinero: el dueño tiene que poder ver que cambia
    antes de que se gaste un euro.
    """

    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(rates=_ritmos(**{"900": (-5.0, -4, 0.0)}))

    puerta = value_candidate(_jugador(), contexto).get("market_gate")

    assert puerta is not None
    assert puerta["gate"] == FALLING
    assert puerta["gate_reason"]
    assert "value_before" in puerta, (
        "sin el valor de antes no se puede ver que cambia"
    )




def test_LA_ASIMETRIA_QUE_QUEDA_SIN_ARREGLAR() -> None:
    """
    LO QUE ESTE ENCARGO NO PUDO CERRAR, FIJADO PARA MAÑANA.

    El acelerador calcula bien. Con Bardeli, a su ritmo observado
    de +4,62 %/dia, la via de tendencia proyecta una
    revalorizacion de 138.628 EUR sobre un precio de 1.650.000.

    Y aun asi devuelve CERO.

    Porque `speculation_value` multiplica ese valor por
    `confidence`, y esa confianza mide lo seguros que estamos de
    sus PUNTOS -0,4125 para Bardeli: sin historico en LaLiga y sin
    pronostico de titularidad-. Para una apuesta de precio eso es
    un error de categoria: da igual cuantos puntos vaya a hacer;
    lo que importa es si su precio sigue subiendo.

    Y `computer_resale_value` NO lleva esa penalizacion. De ahi
    sale toda la historia: la via que no mira al jugador gana
    siempre a la que si lo mira, porque a la segunda se le aplica
    un descuento que a la primera no.

    NO SE ARREGLA ESTA NOCHE. Cambiarlo subiria valoraciones y
    haria a Pepe mas agresivo, y eso se decide con el dueño
    delante. Queda medido y con numeros.
    """

    from src.analysis.player_value_engine import (
        computer_resale_value,
        speculation_value,
    )

    precio = 1_650_000
    ritmo = 4.624

    # Con la confianza de sus puntos: no llega.
    con_confianza_de_puntos = speculation_value(
        price=precio,
        daily_increment=100_000,
        horizon_days=3,
        confidence=0.4125,
        velocity_percent_per_day=ritmo,
    )

    assert con_confianza_de_puntos["value"] == 0
    assert con_confianza_de_puntos["decision"] == "MARGEN_INSUFICIENTE"

    # Sin ella, la misma cuenta si vale.
    sin_penalizacion = speculation_value(
        price=precio,
        daily_increment=100_000,
        horizon_days=3,
        confidence=1.0,
        velocity_percent_per_day=ritmo,
    )

    assert sin_penalizacion["value"] > precio

    # Y la via del Computer no lleva confianza ninguna: por eso
    # gana.
    del_computer = computer_resale_value(precio, 0.0137)

    assert del_computer["value"] > 0
    assert del_computer["value"] > con_confianza_de_puntos["value"], (
        "la asimetria ha desaparecido: revisar si se arreglo a "
        "proposito o por accidente"
    )


TESTS = [
    test_un_ritmo_observado_abre_la_via,
    test_el_ritmo_que_se_proyecta_es_el_del_jugador,
    test_sin_ritmo_observado_NO_se_inventa_una_tasa,
    test_un_precio_que_cae_no_se_compra,
    test_no_hay_banda_de_tolerancia_para_caer,
    test_un_precio_quieto_tampoco_es_una_especulacion,
    test_la_direccion_manda_sobre_la_magnitud,
    test_una_racha_con_la_demanda_hundida_no_se_compra,
    test_una_racha_corta_no_se_mira_con_la_demanda,
    test_una_racha_larga_CON_demanda_si_se_compra,
    test_sin_demanda_medida_la_racha_no_se_veta,
    test_el_corte_de_demanda_es_el_del_ojeador,
    test_la_via_del_once_no_se_toca,
    test_un_precio_que_cae_no_produce_valor_especulativo,
    test_la_reventa_al_computer_NO_exige_ritmo_observado,
    test_pero_un_precio_que_cae_SI_frena_la_reventa,
    test_no_se_ha_bajado_ningun_umbral,
    test_la_compuerta_solo_sabe_decir_que_no,
    test_la_comparacion_viaja_con_cada_valoracion,
    test_LA_ASIMETRIA_QUE_QUEDA_SIN_ARREGLAR,
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
    print(f"FRENO Y ACELERADOR V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
