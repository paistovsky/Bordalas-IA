"""
Cuanto vale un jugador para nosotros, en euros.

QUE RESUELVE
    `rival_bid_model.optimal_bid` necesita ese numero: sin el no
    hay valor esperado y no se puede pujar.

    Antes ese numero era la puja que habria hecho una escalera de
    primas fija sobre el precio de mercado. Eso no es un valor, es
    una regla de redondeo, y hacia que Pepe descartase fichajes
    por razones que no tenian nada que ver con si le salian a
    cuenta.

LA MEDIDA
    El mercado pone precio a un punto. En el catalogo del
    16/08/2026, con 393 jugadores con historico, la mediana son
    22.240 EUR por punto.

    Con eso, "por 1,3 M una diferencia de 136 puntos es un go de
    manual" deja de ser intuicion y pasa a ser una cuenta: 9.559
    EUR por punto, menos de la mitad de lo que cobra el mercado.

EL ERROR QUE CAZO ESTA PRUEBA
    La primera version exigia un 30 % de margen sobre el valor
    justo. El resultado fue que se rechazaba todo, incluido
    Tenaglia a 19.126 EUR por punto, que es BARATO frente a la
    mediana de 22.240.

    El fallo: `optimal_bid` ya maximiza P(ganar) x (valor - puja),
    y ese producto nunca puja el valor entero. El descuento con el
    que compramos ya emergia de ahi. Exigirlo otra vez aqui era
    contarlo dos veces.

Ejecutar:
    python -m src.analysis.test_player_value_v1
"""

from src.analysis.player_value_engine import (
    CONFIDENCE_HISTORICAL,
    CONFIDENCE_MARKET_IMPLIED,
    MAX_PROJECTED_DAILY_RATE,
    MIN_POINTS_SAMPLES,
    TREND_DECAY,
    build_team_strength,
    calibrate_points_market,
    estimate_resale_price,
    estimate_season_points,
    speculation_value,
    xi_upgrade_value,
)


# Medido en el catalogo real del 16/08/2026.
TARIFA_REAL = 22_240


def jugador(
    precio: int,
    puntos=None,
    equipo: int = 5,
    incremento: int = 0,
) -> dict:
    return {
        "id": 1,
        "name": "Jugador",
        "price": precio,
        "pointsLastSeason": puntos,
        "teamID": equipo,
        "priceIncrement": incremento,
    }


def catalogo(n: int = 100) -> dict:
    """
    Catalogo sintetico con una tarifa conocida de 20.000 EUR por
    punto, para poder afirmar sobre numeros exactos.
    """
    jugadores = {}

    for i in range(n):
        puntos = 50 + i
        jugadores[str(i)] = {
            "id": i,
            "name": f"J{i}",
            "price": puntos * 20_000,
            "pointsLastSeason": puntos,
            "teamID": 1 if i < n // 2 else 2,
        }

    return {"data": {"players": jugadores}}


MERCADO = calibrate_points_market(catalogo())


# ============================================================
# CUANTO CUESTA UN PUNTO
# ============================================================

def test_la_tarifa_se_mide_en_el_catalogo() -> None:
    assert MERCADO["calibrated"] is True
    assert MERCADO["rate_median"] == 20_000, (
        f"El catalogo de prueba tiene todos los jugadores a 20.000 "
        f"EUR por punto. Salio {MERCADO['rate_median']}."
    )
    assert MERCADO["samples"] == 100

    print("  OK  la tarifa sale del catalogo, no de una constante")


def test_sin_muestras_no_se_valora_nada() -> None:
    """
    Inventarse una tarifa seria peor que no valorar.
    """
    pobre = calibrate_points_market(catalogo(5))

    assert pobre["calibrated"] is False
    assert pobre["rate_median"] == 0
    assert str(MIN_POINTS_SAMPLES) in pobre["reason"]

    resultado = xi_upgrade_value(200, 100, pobre)

    assert resultado["value"] == 0
    assert resultado["decision"] == "SIN_TARIFA"

    print("  OK  sin muestras no se valora, y se dice por que")


def test_la_fuerza_del_equipo_sale_de_los_datos() -> None:
    """
    "Si son titulares en Madrid, Barsa o Atleti van a hacer
    puntos" es cierto, y se puede derivar sumando el valor de cada
    plantilla en vez de escribir los nombres a mano.
    """
    cat = {
        "data": {
            "players": {
                "1": {"teamID": 10, "price": 100_000_000},
                "2": {"teamID": 20, "price": 20_000_000},
                "3": {"teamID": 30, "price": 5_000_000},
            }
        }
    }

    fuerza = build_team_strength(cat)

    assert fuerza["available"] is True
    assert fuerza["index"][10] > fuerza["index"][20] > fuerza["index"][30]
    assert fuerza["index"][10] > 1.0, (
        "El equipo mas caro debe estar por encima de la media."
    )

    print("  OK  la fuerza del equipo se deriva del valor de plantilla")


# ============================================================
# PUNTOS ESPERADOS
# ============================================================

def test_con_historico_se_usan_los_puntos_reales() -> None:
    resultado = estimate_season_points(
        jugador(3_250_000, 160), MERCADO
    )

    assert resultado["points"] == 160
    assert resultado["source"] == "HISTORICO"
    assert resultado["confidence"] == CONFIDENCE_HISTORICAL

    print("  OK  con historico se usan los puntos reales")


def test_sin_historico_se_usa_lo_que_implica_el_precio() -> None:
    """
    El 30 % del catalogo son fichajes nuevos sin LaLiga detras.
    """
    resultado = estimate_season_points(
        jugador(2_000_000, None), MERCADO
    )

    assert resultado["points"] == 100, (
        f"2 M a 20.000 EUR/punto implican 100 puntos. Salio "
        f"{resultado['points']}."
    )
    assert resultado["source"] == "IMPLICITO_MERCADO"
    assert resultado["confidence"] == CONFIDENCE_MARKET_IMPLIED
    assert resultado["confidence"] < CONFIDENCE_HISTORICAL, (
        "Una estimacion no puede valer lo mismo que un dato."
    )

    print("  OK  sin historico se estima del precio, con menos confianza")


def test_la_fuerza_del_equipo_no_multiplica_los_puntos() -> None:
    """
    Contarla seria duplicar: el precio del jugador ya refleja en
    que club juega. Multiplicar inflaria a los caros de los
    equipos grandes, que es lo contrario de buscar chollos.
    """
    fuerza = build_team_strength(
        {
            "data": {
                "players": {
                    "1": {"teamID": 1, "price": 200_000_000},
                    "2": {"teamID": 2, "price": 10_000_000},
                }
            }
        }
    )

    grande = estimate_season_points(
        jugador(2_000_000, None, equipo=1), MERCADO, fuerza
    )
    pequeno = estimate_season_points(
        jugador(2_000_000, None, equipo=2), MERCADO, fuerza
    )

    assert grande["points"] == pequeno["points"], (
        "El mismo precio implica los mismos puntos. La fuerza del "
        "equipo informa, no multiplica."
    )
    assert grande["team_strength"] > pequeno["team_strength"], (
        "Pero el dato tiene que estar disponible."
    )

    print("  OK  la fuerza del equipo informa, no infla los puntos")


# ============================================================
# MEJORA DEL ONCE
# ============================================================

def test_el_caso_tenaglia() -> None:
    """
    El fichaje que motivo todo esto. Con los numeros reales:
    160 puntos frente a los 57 de Ximo Navarro, y 1,28 M
    recuperados si se vende al que sustituye.
    """
    resultado = xi_upgrade_value(
        candidate_points=160,
        replaced_points=57,
        points_market={"rate_median": TARIFA_REAL},
        confidence=CONFIDENCE_HISTORICAL,
        recovered_value=1_280_000,
    )

    assert resultado["points_delta"] == 103
    assert resultado["fair_value"] == 103 * TARIFA_REAL
    assert resultado["value"] > 3_250_000, (
        f"Tenaglia cuesta 3,25 M y aporta 103 puntos: sale a "
        f"19.126 EUR/punto neto, por debajo de la mediana de "
        f"{TARIFA_REAL:,}. Deberia salir comprable, y el valor "
        f"salio {resultado['value']:,}."
    )

    print(
        f"  OK  Tenaglia: 103 puntos valen "
        f"{resultado['fair_value']:,} EUR; pagariamos hasta "
        f"{resultado['value']:,}".replace(",", ".")
    )


def test_un_fichaje_a_precio_de_mercado_no_aporta_nada() -> None:
    """
    Pagar la tarifa por unos puntos no es un negocio: es un
    intercambio. El motor debe distinguirlo de un chollo.
    """
    caro = xi_upgrade_value(
        candidate_points=200,
        replaced_points=100,
        points_market={"rate_median": TARIFA_REAL},
        recovered_value=0,
    )

    precio_de_mercado = 100 * TARIFA_REAL

    assert caro["value"] < precio_de_mercado, (
        "Nunca se paga la tarifa entera: no quedaria ventaja."
    )

    print("  OK  no se paga la tarifa completa por unos puntos")


def test_lo_que_recuperamos_vendiendo_cuenta() -> None:
    """
    Al mejorar el once, el sustituido se puede vender. Ignorarlo
    hacia que casi ninguna mejora saliera rentable.
    """
    sin_venta = xi_upgrade_value(
        160, 57, {"rate_median": TARIFA_REAL}
    )
    con_venta = xi_upgrade_value(
        160, 57, {"rate_median": TARIFA_REAL},
        recovered_value=1_280_000,
    )

    assert con_venta["value"] - sin_venta["value"] == 1_280_000, (
        "Lo recuperado debe sumarse entero al maximo pagable."
    )

    print("  OK  lo que se recupera vendiendo suma al maximo pagable")


def test_no_es_mejora_si_no_suma_puntos() -> None:
    resultado = xi_upgrade_value(
        50, 100, {"rate_median": TARIFA_REAL}
    )

    assert resultado["value"] == 0
    assert resultado["decision"] == "NO_MEJORA"

    print("  OK  un fichaje que resta puntos no es una mejora")


def test_menos_confianza_es_menos_dinero() -> None:
    seguro = xi_upgrade_value(
        200, 100, {"rate_median": TARIFA_REAL},
        confidence=CONFIDENCE_HISTORICAL,
    )
    dudoso = xi_upgrade_value(
        200, 100, {"rate_median": TARIFA_REAL},
        confidence=CONFIDENCE_MARKET_IMPLIED,
    )

    assert dudoso["value"] < seguro["value"], (
        "Por unos puntos estimados se paga menos que por unos "
        "medidos."
    )

    print("  OK  a menos confianza, menos dinero")


# ============================================================
# ESPECULACION
# ============================================================

def test_la_tendencia_se_proyecta_con_desgaste() -> None:
    """
    Una subida de 250.000 EUR al dia no se mantiene cinco dias.
    Proyectarla en linea recta da numeros de fantasia.
    """
    recta = 250_000 * 5

    proyeccion = estimate_resale_price(
        3_000_000, 250_000, horizon_days=5
    )

    assert proyeccion["appreciation"] < recta, (
        f"Proyectada en linea recta serian {recta:,}; con desgaste "
        f"debe salir menos. Salio {proyeccion['appreciation']:,}."
    )
    assert proyeccion["appreciation"] > 250_000, (
        "Pero mas que un solo dia."
    )

    print(
        f"  OK  5 dias a 250k/dia: {proyeccion['appreciation']:,} "
        f"en vez de {recta:,}".replace(",", ".")
    )


def test_una_caida_se_respeta_entera() -> None:
    """
    El desgaste hace la subida mas prudente. Aplicarselo a una
    bajada la haria parecer menos grave, que es lo contrario de
    ser prudente.
    """
    proyeccion = estimate_resale_price(
        3_000_000, -100_000, horizon_days=4
    )

    assert proyeccion["appreciation"] == -400_000, (
        f"Una caida de 100k durante 4 dias son 400k. Salio "
        f"{proyeccion['appreciation']:,}."
    )

    print("  OK  las caidas no se suavizan")


def test_un_jugador_que_no_sube_no_se_especula() -> None:
    resultado = speculation_value(3_270_000, 0, horizon_days=3)

    assert resultado["value"] == 0
    assert resultado["decision"] == "SIN_REVALORIZACION"

    print("  OK  sin revalorizacion esperada no hay especulacion")


def test_un_jugador_en_caida_tampoco() -> None:
    resultado = speculation_value(3_270_000, -20_000, horizon_days=3)

    assert resultado["value"] == 0

    print("  OK  un jugador en caida no es una oportunidad")


def test_la_especulacion_deja_margen() -> None:
    resultado = speculation_value(
        420_000, 30_000, horizon_days=3
    )

    assert resultado["value"] > 420_000, (
        "Con revalorizacion esperada debe haber algo que pagar."
    )
    assert resultado["value"] < resultado["resale_estimate"], (
        "Nunca se paga la reventa entera: ahi no hay negocio."
    )

    print(
        f"  OK  reventa {resultado['resale_estimate']:,}, "
        f"pagariamos hasta {resultado['value']:,}".replace(",", ".")
    )


# ============================================================
# ROBUSTEZ
# ============================================================

def test_aguanta_datos_rotos() -> None:
    casos = [None, {}, {"data": None}, {"data": {"players": None}},
             {"data": {"players": [None, "x", 3]}}]

    for caso in casos:
        mercado = calibrate_points_market(caso)
        assert mercado["calibrated"] is False

        fuerza = build_team_strength(caso)
        assert isinstance(fuerza["index"], dict)

        puntos = estimate_season_points({}, mercado, fuerza)
        assert puntos["points"] == 0

    print("  OK  aguanta catalogos rotos")


def test_valores_absurdos_no_generan_dinero() -> None:
    for precio in (0, -100, None):
        resultado = speculation_value(precio, 50_000)
        assert resultado["value"] == 0

    resultado = xi_upgrade_value(
        None, None, {"rate_median": TARIFA_REAL}
    )
    assert resultado["value"] == 0

    print("  OK  entradas absurdas no producen valor")


# ============================================================


# ============================================================
# LA TENDENCIA, MEDIDA EN VEZ DE SUPUESTA
# ============================================================


def test_el_desgaste_es_el_medido_no_el_inventado() -> None:
    """
    0,65 era una cifra escrita a mano. Medido sobre 80 snapshots,
    la media diaria de los tres dias siguientes es 0,601 veces la
    de hoy, y eso equivale a un desgaste de 0,53.

    Si alguien lo sube sin volver a medir, este test lo para.
    """
    assert abs(TREND_DECAY - 0.53) < 0.005, (
        f"TREND_DECAY deberia ser el medido (0,53), es {TREND_DECAY}."
    )

    suma = 1 + TREND_DECAY + TREND_DECAY ** 2

    assert abs(suma - 1.803) < 0.02, (
        f"Tres dias con este desgaste suman {suma:.3f}; lo medido "
        f"es 1,803."
    )

    print("  OK  el desgaste 0,53 sale de la medicion, no de la intuicion")


def test_la_velocidad_medida_manda_sobre_el_incremento() -> None:
    """
    Un solo dia es ruidoso. Si hay velocidad medida sobre varios
    dias, se usa esa, y se dice cual se ha usado.
    """
    con_incremento = estimate_resale_price(
        1_000_000, 10_000, 3
    )
    con_velocidad = estimate_resale_price(
        1_000_000, 10_000, 3, velocity_percent_per_day=2.0
    )

    assert con_incremento["source"] == "incremento de ayer"
    assert con_velocidad["source"] == "velocidad medida"

    assert (
        con_velocidad["appreciation"]
        > con_incremento["appreciation"]
    ), "Un 2 %/dia deberia proyectar mas que un 1 %/dia."

    print("  OK  manda la velocidad medida y se declara la fuente")


def test_la_subida_se_recorta_a_la_banda_plausible() -> None:
    """
    Yusi Enriquez venia subiendo un 12 % diario despues de
    firmar. Existe, pero proyectar tres dias mas a ese ritmo es
    extrapolar la cola de la distribucion.
    """
    disparada = estimate_resale_price(
        360_000, 0, 3, velocity_percent_per_day=12.46
    )

    assert disparada["clamped"] is True
    assert (
        disparada["daily_rate_percent"]
        <= MAX_PROJECTED_DAILY_RATE + 0.01
    )
    assert "recortado" in disparada["reason"]

    normal = estimate_resale_price(
        360_000, 0, 3, velocity_percent_per_day=1.5
    )

    assert normal["clamped"] is False

    print("  OK  una subida fuera de banda se recorta y se dice")


def test_las_caidas_no_se_recortan() -> None:
    """
    Recortar tambien las caidas nos haria optimistas justo con el
    jugador que se esta desplomando. Ese es el error caro.
    """
    cayendo = estimate_resale_price(
        1_000_000, 0, 3, velocity_percent_per_day=-10.0
    )

    assert cayendo["clamped"] is False
    assert cayendo["appreciation"] == -300_000, (
        f"Una caida del 10 % diario tres dias son -300.000, "
        f"salio {cayendo['appreciation']}."
    )

    print("  OK  una caida se proyecta entera, sin recorte")


def test_dos_precios_distintos_con_la_misma_velocidad() -> None:
    """
    La tasa es tasa: al mismo ritmo, el caro sube mas euros que
    el barato. Con euros planos los dos subian lo mismo.
    """
    caro = estimate_resale_price(
        5_950_000, 0, 3, velocity_percent_per_day=1.0
    )
    barato = estimate_resale_price(
        150_000, 0, 3, velocity_percent_per_day=1.0
    )

    assert caro["appreciation"] > barato["appreciation"] * 30

    print("  OK  al mismo ritmo, el caro sube mas euros")


TESTS = [
    test_el_desgaste_es_el_medido_no_el_inventado,
    test_la_velocidad_medida_manda_sobre_el_incremento,
    test_la_subida_se_recorta_a_la_banda_plausible,
    test_las_caidas_no_se_recortan,
    test_dos_precios_distintos_con_la_misma_velocidad,
    test_la_tarifa_se_mide_en_el_catalogo,
    test_sin_muestras_no_se_valora_nada,
    test_la_fuerza_del_equipo_sale_de_los_datos,
    test_con_historico_se_usan_los_puntos_reales,
    test_sin_historico_se_usa_lo_que_implica_el_precio,
    test_la_fuerza_del_equipo_no_multiplica_los_puntos,
    test_el_caso_tenaglia,
    test_un_fichaje_a_precio_de_mercado_no_aporta_nada,
    test_lo_que_recuperamos_vendiendo_cuenta,
    test_no_es_mejora_si_no_suma_puntos,
    test_menos_confianza_es_menos_dinero,
    test_la_tendencia_se_proyecta_con_desgaste,
    test_una_caida_se_respeta_entera,
    test_un_jugador_que_no_sube_no_se_especula,
    test_un_jugador_en_caida_tampoco,
    test_la_especulacion_deja_margen,
    test_aguanta_datos_rotos,
    test_valores_absurdos_no_generan_dinero,
]


def main() -> None:
    print("=" * 60)
    print(" VALOR DE UN JUGADOR")
    print("=" * 60)

    fallos = 0

    for test in TESTS:
        print(f"\n{test.__name__}")
        try:
            test()
        except AssertionError as error:
            fallos += 1
            print(f"  FALLO  {error}")

    print("\n" + "=" * 60)
    if fallos:
        print(f" {fallos}/{len(TESTS)} TESTS FALLIDOS")
        raise SystemExit(1)
    print(f" {len(TESTS)}/{len(TESTS)} TESTS OK")
    print("=" * 60)


if __name__ == "__main__":
    main()
