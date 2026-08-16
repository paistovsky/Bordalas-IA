"""
Modelo de puja rival: de adivinar el peor caso a calcular.

EL MODELO QUE SUSTITUYE

    amenaza = min(capacidad del rival mas rico, precio * 1,25)
    compite quien pueda pagar el precio

    Con siete managers con millones, los 53 jugadores del mercado
    salian con seis competidores. Incluido Oluwaseyi, de 420.000
    EUR. `uncontested` no se daba nunca, la ruta de mercado + 1 no
    se activaba jamas, y el motor pedia un 25 % de prima en todo.

    Prinzipote puede pujar 29,9 M y no ha pujado ni una vez en
    toda la liga. Contarlo como amenaza 53 veces al dia era el
    sintoma mas claro: **poder pagar no es ir a pujar**.

QUE SE VERIFICA
    Que la participacion sale del historial, que quien nunca puja
    no cuenta, que la puja optima maximiza valor esperado, y que
    el "+1 EUR" aparece cuando de verdad toca -y solo entonces-.

Ejecutar:
    python -m src.analysis.test_rival_bid_model_v1
"""

from src.analysis.rival_bid_model import (
    DEFAULT_PREMIUM_CURVE,
    MIN_PREMIUM_SAMPLES,
    MIN_WIN_PROBABILITY,
    build_bid_model,
    calibrate_premium_curve,
    credible_rivals,
    optimal_bid,
    win_probability,
)


YO = 14175949
PRECIO = 420_000          # Oluwaseyi, precio real del 16/08
VALOR = 490_000           # reventa 640k menos 150k de margen


# Instante del reparto inicial de la liga, como en los datos
# reales: todos los jugadores del lote comparten `owner_since`.
REPARTO = 1786379245


def rival(
    user_id: int,
    nombre: str,
    capacidad: int,
    observada: int = 0,
    perdidas: int = 0,
    ganadas: int = 0,
    plantilla: int = 15,
    sin_explicar: int = 0,
) -> dict:
    """
    Un manager con su plantilla conciliable.

    `sin_explicar` son jugadores que aparecieron en su plantilla
    despues del reparto sin que tengamos registrada la compra: es
    el sintoma de que nos falta historia suya.
    """

    roster = []
    transacciones = []

    del_reparto = max(
        plantilla - ganadas - sin_explicar,
        0,
    )

    for i in range(del_reparto):
        roster.append(
            {
                "id": user_id * 1000 + i,
                "name": f"{nombre} draft {i}",
                "value": 1_000_000,
                "owner_since": REPARTO,
            }
        )

    for i in range(ganadas):
        pid = user_id * 1000 + 500 + i
        roster.append(
            {
                "id": pid,
                "name": f"{nombre} fichado {i}",
                "value": 2_000_000,
                "owner_since": REPARTO + 86_400 * (i + 1),
            }
        )
        transacciones.append(
            {
                "kind": "BUY_FROM_COMPUTER",
                "player_id": pid,
                "amount": 2_000_000,
            }
        )

    for i in range(sin_explicar):
        roster.append(
            {
                "id": user_id * 1000 + 900 + i,
                "name": f"{nombre} misterioso {i}",
                "value": 3_000_000,
                "owner_since": REPARTO + 86_400 * (i + 1),
            }
        )

    return {
        "user_id": user_id,
        "name": nombre,
        "maximum_bid": capacidad,
        "max_observed_bid": observada,
        "lost_bids": perdidas,
        "won_auctions": ganadas,
        "roster": roster,
        "transactions": transacciones,
    }


# Los siete managers reales, con su historial observado.
REALES = [
    rival(14145555, "Pollo17", 17_994_400, 10_877_000, 11, 2),
    rival(2, "DiosMande", 16_440_492, 22_230_000, 2, 3),
    rival(3, "Manzagool", 17_874_090, 6_027_930, 1, 1),
    rival(4, "Luismi_Haz", 26_564_499, 12_402_000, 8, 1),
    rival(5, "Prinzipote", 29_942_500, 0, 0, 0),
    rival(6, "Mex", 30_210_000, 23_310_000, 1, 2),
]


def modelo(rivales=None, subastas: int = 23) -> dict:
    return build_bid_model(
        {
            "managers": rivales if rivales is not None else REALES,
            "competitive_bids": subastas,
            "validation": {"exact": True},
        },
        own_user_id=YO,
    )


def todos(capacidad: int, observada: int, perdidas: int, ganadas: int = 0):
    return [
        rival(i, f"R{i}", capacidad, observada, perdidas, ganadas)
        for i in range(1, 7)
    ]


def por_nombre(model, nombre):
    for r in model["rivals"]:
        if r["name"] == nombre:
            return r
    raise AssertionError(f"{nombre} no esta en el modelo.")


# ============================================================
# QUIEN PUJA DE VERDAD
# ============================================================

def test_el_que_nunca_ha_pujado_no_es_una_amenaza() -> None:
    """
    EL test. Prinzipote, 29,9 M de capacidad y cero pujas.
    """
    model = modelo()

    prinzi = por_nombre(model, "Prinzipote")

    assert prinzi["never_bids"] is True
    assert prinzi["participation"] == 0.0

    compiten = credible_rivals(model, PRECIO)
    nombres = {r["name"] for r in compiten}

    assert "Prinzipote" not in nombres, (
        "REGRESION: un manager que no ha pujado nunca vuelve a "
        "contar como competencia."
    )

    print(
        "  OK  29,9 M y cero pujas: espectador con dinero, no rival"
    )


def test_la_participacion_sale_del_historial() -> None:
    model = modelo()

    pollo = por_nombre(model, "Pollo17")

    # 11 perdidas + 2 ganadas sobre 23 subastas, y su plantilla
    # se explica entera, asi que lo medido vale tal cual.
    assert pollo["coverage"] == 1.0
    assert abs(pollo["participation"] - 13 / 23) < 0.001, (
        f"Pollo17 ha pujado 13 veces en 23 subastas y su historia "
        f"esta completa: deberia salir {13/23:.3f}, salio "
        f"{pollo['participation']}."
    )
    assert model["participation_from_history"] is True

    print("  OK  Pollo17 puja el 57 % de las veces, medido")


def test_sin_historial_se_supone_una_probabilidad_prudente() -> None:
    """
    Al principio de temporada no hay datos. Suponer que nadie puja
    seria el error caro.
    """
    model = modelo(subastas=2)

    assert model["participation_from_history"] is False

    for r in model["rivals"]:
        if r["capacity"] > 0:
            assert r["participation"] > 0, (
                "Sin historial no se puede afirmar que un rival "
                "con dinero no vaya a pujar."
            )

    print("  OK  sin historial se supone participacion, no cero")


def test_quien_no_puede_pagar_no_compite() -> None:
    model = modelo(todos(100_000, 90_000, 9, 1))

    assert credible_rivals(model, PRECIO) == [], (
        "Nadie llega al precio base."
    )

    print("  OK  sin dinero para el precio base no se compite")


def test_pepe_no_se_cuenta_a_si_mismo() -> None:
    con_pepe = REALES + [rival(YO, "Pepe Bordalás", 12_414_968, 24_897_600, 0, 5)]

    model = build_bid_model(
        {"managers": con_pepe, "competitive_bids": 23,
         "validation": {"exact": True}},
        own_user_id=YO,
    )

    assert all(r["user_id"] != YO for r in model["rivals"]), (
        "REGRESION: Pepe compite contra si mismo."
    )

    print("  OK  Pepe queda fuera de la lista de rivales")


# ============================================================
# PROBABILIDAD DE GANAR
# ============================================================

def test_pujar_mas_nunca_baja_la_probabilidad() -> None:
    model = modelo()

    anterior = -1.0

    for importe in (
        PRECIO + 1, PRECIO + 20_000, PRECIO + 50_000,
        PRECIO + 200_000, PRECIO * 3,
    ):
        p = win_probability(importe, PRECIO, model)

        assert p >= anterior - 1e-9, (
            f"Pujar {importe:,} da menos probabilidad que pujar "
            f"menos. La curva no es monotona."
        )
        anterior = p

    print("  OK  la probabilidad sube con el importe")


def test_sin_rivales_activos_el_minimo_gana_seguro() -> None:
    model = modelo(todos(30_000_000, 0, 0, 0))

    p = win_probability(PRECIO + 1, PRECIO, model)

    assert p == 1.0, (
        f"Si nadie puja nunca, el minimo gana. Salio {p}."
    )

    print("  OK  sin rivales activos el minimo gana al 100 %")


def test_mas_rivales_activos_bajan_la_probabilidad() -> None:
    pocos = modelo(todos(30_000_000, 20_000_000, 2, 0))
    muchos = modelo(todos(30_000_000, 20_000_000, 20, 0))

    p_pocos = win_probability(PRECIO + 1, PRECIO, pocos)
    p_muchos = win_probability(PRECIO + 1, PRECIO, muchos)

    assert p_muchos < p_pocos, (
        "Con rivales mas activos ganar al minimo debe ser mas "
        "dificil."
    )

    print(
        f"  OK  rivales flojos {p_pocos*100:.0f} % vs activos "
        f"{p_muchos*100:.0f} %"
    )


# ============================================================
# CUANTO PUJAR
# ============================================================

def test_el_mas_uno_aparece_cuando_de_verdad_toca() -> None:
    """
    Lo que se pedia desde el principio, pero por la razon buena:
    no porque una regla lo diga, sino porque la probabilidad de
    ganar al minimo ya es alta.
    """
    model = modelo(todos(30_000_000, 0, 0, 0))

    resultado = optimal_bid(PRECIO, VALOR, model)

    assert resultado["decision"] == "BID"
    assert resultado["bid"] == PRECIO + 1, (
        f"Sin rivales activos deberia bastar el minimo. Salio "
        f"{resultado['bid']:,}."
    )
    assert resultado["win_probability"] == 1.0

    print("  OK  mercado + 1 EUR cuando nadie va a pujar")


def test_con_rivales_activos_se_sube_hasta_donde_compensa() -> None:
    model = modelo(todos(30_000_000, 20_000_000, 15, 5))

    resultado = optimal_bid(PRECIO, VALOR, model)

    assert resultado["decision"] == "BID"
    assert resultado["bid"] > PRECIO + 1, (
        "Con seis rivales muy activos, pujar el minimo es tirar "
        "la operacion."
    )
    assert resultado["bid"] < VALOR, (
        "Nunca se paga hasta el valor: no quedaria margen."
    )

    print(
        f"  OK  con rivales activos sube a {resultado['bid']:,} "
        f"({resultado['win_probability']*100:.0f} % de ganar)"
    )


def test_el_importe_elegido_es_el_de_mas_valor_esperado() -> None:
    """
    El corazon del modelo: no se elige la puja mas probable ni la
    mas barata, sino la que maximiza P(ganar) x margen.
    """
    model = modelo()

    resultado = optimal_bid(PRECIO, VALOR, model)

    mejor = max(
        resultado["options"],
        key=lambda o: o["expected_value"],
    )

    assert resultado["bid"] == mejor["bid"], (
        f"Se eligio {resultado['bid']:,} pero la de mas valor "
        f"esperado era {mejor['bid']:,}."
    )

    # Y hay opciones peores por los dos lados: mas barata gana
    # menos veces, mas cara deja menos margen.
    mas_barata = min(resultado["options"], key=lambda o: o["bid"])
    mas_cara = max(resultado["options"], key=lambda o: o["bid"])

    assert mas_barata["win_probability"] <= resultado["win_probability"]
    assert mas_cara["expected_value"] <= resultado["expected_value"]

    print(
        f"  OK  optimo {resultado['bid']:,} entre "
        f"{len(resultado['options'])} importes evaluados"
    )


def test_no_se_puja_si_vale_menos_de_lo_que_cuesta() -> None:
    model = modelo()

    resultado = optimal_bid(PRECIO, 400_000, model)

    assert resultado["decision"] == "NO_COMPENSA"
    assert resultado["bid"] == 0

    print("  OK  si no hay margen no se puja")


def test_no_se_inmoviliza_la_caja_en_una_tombola() -> None:
    """
    Con margen estrecho el modelo encontraba pujas de valor
    esperado positivo pero ridiculo: 428.401 EUR retenidos hasta
    el reset para ganar 168 EUR esperados con un 11 % de
    probabilidad.

    El valor esperado por si solo no ve ese coste: no sabe que hay
    otras subastas peleando por la misma caja.
    """
    model = modelo(todos(30_000_000, 20_000_000, 15, 5))

    resultado = optimal_bid(PRECIO, 430_000, model)

    assert resultado["decision"] == "PROBABILIDAD_INSUFICIENTE", (
        f"Una puja con {MIN_WIN_PROBABILITY*100:.0f} % o menos de "
        f"probabilidad inmoviliza caja a cambio de casi nada. "
        f"Salio {resultado['decision']}."
    )
    assert resultado["options"], (
        "Hay que dejar la curva evaluada para poder revisarla."
    )

    print("  OK  no se inmoviliza la caja en una tombola")


def test_el_presupuesto_disponible_es_un_techo_duro() -> None:
    model = modelo(todos(30_000_000, 0, 0, 0))

    resultado = optimal_bid(
        PRECIO, VALOR, model, available_budget=300_000
    )

    assert resultado["decision"] == "SUPERA_PRESUPUESTO"
    assert resultado["bid"] == 0

    print("  OK  sin presupuesto no se puja")


def test_toda_decision_explica_por_que() -> None:
    model = modelo()

    casos = [
        optimal_bid(PRECIO, VALOR, model),
        optimal_bid(PRECIO, 400_000, model),
        optimal_bid(PRECIO, VALOR, model, available_budget=1),
        optimal_bid(0, VALOR, model),
    ]

    for resultado in casos:
        assert resultado.get("reasons"), (
            f"Decision sin motivo: {resultado.get('decision')}"
        )

    print("  OK  toda decision viene con su motivo")


# ============================================================
# CALIBRACION DE LA PRIMA
# ============================================================

def test_sin_muestras_se_usa_la_curva_por_defecto_y_se_dice() -> None:
    prima = calibrate_premium_curve(REALES, price_lookup=None)

    assert prima["calibrated"] is False
    assert prima["curve"] == list(DEFAULT_PREMIUM_CURVE)
    assert str(MIN_PREMIUM_SAMPLES) in prima["reason"], (
        "El motivo debe decir cuantas muestras hacen falta."
    )

    print("  OK  sin muestras se usa el valor por defecto, y se dice")


def test_con_historial_suficiente_se_calibra() -> None:
    """
    El buscador de precio recibe jugador Y fecha: tiene que
    devolver lo que costaba ENTONCES.
    """
    historial = [
        {
            "user_id": 1,
            "name": "R1",
            "maximum_bid": 10_000_000,
            "lost_bid_history": [
                {
                    "amount": int(1_000_000 * f),
                    "player_id": 77,
                    "date": 1_786_400_000 + i * 3600,
                }
                for i, f in enumerate(
                    (
                        1.00, 1.01, 1.02, 1.03, 1.05, 1.06,
                        1.08, 1.10, 1.15, 1.20, 1.30, 1.45,
                        1.02, 1.04,
                    )
                )
            ],
        }
    ]

    prima = calibrate_premium_curve(
        historial,
        price_lookup=lambda pid, cuando: 1_000_000,
    )

    assert prima["calibrated"] is True
    assert prima["samples"] == 14
    assert len(prima["curve"]) == 7, (
        f"Siete tramos, incluida la cola. Salieron "
        f"{len(prima['curve'])}."
    )
    assert prima["discarded_impossible"] == 0
    assert prima["curve"][0][0] < prima["curve"][-1][0], (
        "La curva debe ir de menor a mayor prima."
    )

    print(
        f"  OK  calibrada con {prima['samples']} pujas: "
        f"{prima['reason']}"
    )


def test_la_curva_deja_sitio_a_la_cola() -> None:
    """
    Sin cola, cualquier importe por encima del tramo mas alto
    devolvia 100 % de probabilidad. Y "100 %" no es una
    prediccion: es el modelo diciendo que no ve mas alla de su
    propia curva.

    Con jugadores baratos es justo lo que pasa: por uno de 150.000
    EUR alguien puede poner el doble sin despeinarse.
    """
    model = modelo(todos(30_000_000, 20_000_000, 15, 5))

    # Muy por encima del tramo de 1,40x.
    p = win_probability(int(PRECIO * 1.45), PRECIO, model)

    assert p < 1.0, (
        "Ninguna puja deberia dar certeza absoluta: siempre queda "
        "la posibilidad de una puja desproporcionada."
    )
    assert p > 0.85, (
        "Pero pagar un 45 % de prima si deberia ganar casi siempre."
    )

    print(f"  OK  a +45 % de prima se gana el {p*100:.0f} %, no el 100 %")


def test_sin_conciliar_no_se_afirma_que_alguien_no_puja() -> None:
    """
    "Este rival no puja nunca" es una afirmacion en negativo, y
    solo se puede hacer conociendo su historia entera.

    Con jugadores en su plantilla que no sabemos de donde salieron,
    un cero de pujas puede ser simplemente lo que no hemos visto.
    """
    opaco = rival(
        50, "Opaco", 30_000_000,
        observada=0, perdidas=0, ganadas=0,
        plantilla=15, sin_explicar=6,
    )

    model = modelo([opaco])

    datos = por_nombre(model, "Opaco")

    assert datos["coverage"] < 1.0
    assert datos["never_bids"] is False, (
        "REGRESION: se afirmo que un rival no puja teniendo su "
        "historia incompleta."
    )
    assert datos["participation"] > 0, (
        "Con la historia incompleta hay que suponer que puede "
        "pujar."
    )

    print(
        f"  OK  con cobertura {datos['coverage']*100:.0f} % no se "
        f"afirma que no puje"
    )


def test_con_la_historia_completa_si_se_puede_afirmar() -> None:
    limpio = rival(
        51, "Transparente", 30_000_000,
        observada=0, perdidas=0, ganadas=0,
        plantilla=15, sin_explicar=0,
    )

    model = modelo([limpio])

    datos = por_nombre(model, "Transparente")

    assert datos["coverage"] == 1.0
    assert datos["never_bids"] is True, (
        "Con la plantilla explicada entera y cero pujas, si se "
        "puede afirmar que no puja."
    )

    print("  OK  con la historia completa si se afirma")


def test_la_falta_de_datos_encoge_lo_medido() -> None:
    """
    De un rival del que nos falta media historia, "ha pujado dos
    veces" no significa que solo haya pujado dos veces.
    """
    completo = rival(
        52, "Completo", 30_000_000,
        observada=5_000_000, perdidas=2, ganadas=0,
        plantilla=15, sin_explicar=0,
    )
    incompleto = rival(
        53, "Incompleto", 30_000_000,
        observada=5_000_000, perdidas=2, ganadas=0,
        plantilla=15, sin_explicar=8,
    )

    model = modelo([completo, incompleto])

    a = por_nombre(model, "Completo")
    b = por_nombre(model, "Incompleto")

    assert b["participation"] > a["participation"], (
        f"Con menos informacion hay que suponer mas actividad, no "
        f"menos. Completo {a['participation']}, incompleto "
        f"{b['participation']}."
    )

    print(
        f"  OK  cobertura {a['coverage']*100:.0f} % -> "
        f"{a['participation']:.2f} vs "
        f"{b['coverage']*100:.0f} % -> {b['participation']:.2f}"
    )


def test_el_ledger_solo_es_fiable_si_tambien_cuadran_los_rivales() -> None:
    """
    El fallo del 16/08: `validation.exact` compara SOLO nuestro
    saldo, y sobre el se decidia si pujar al minimo.
    """
    con_hueco = modelo(
        [rival(54, "Opaco", 30_000_000, plantilla=15, sin_explicar=4)]
    )
    sin_hueco = modelo(
        [rival(55, "Claro", 30_000_000, plantilla=15, sin_explicar=0)]
    )

    assert con_hueco["ledger_exact"] is True, (
        "Nuestro saldo cuadra en los dos casos."
    )
    assert con_hueco["ledger_trusted"] is False, (
        "REGRESION: se dio por fiable un ledger con plantillas "
        "rivales sin explicar."
    )
    assert sin_hueco["ledger_trusted"] is True

    print(
        "  OK  fiarse exige que cuadre nuestro saldo Y las "
        "plantillas rivales"
    )


def test_una_puja_por_debajo_del_precio_es_imposible() -> None:
    """
    EL fallo del 16/08/2026.

    En una subasta del Computer no se puede pujar por debajo del
    precio de salida. Si al medir sale una prima menor que 1,0, el
    precio que estamos usando no es el de aquel momento.

    Con datos reales, dividiendo entre el precio de HOY, salian 18
    de 23 por debajo de 1,0 y la mediana daba 0,94. El modelo
    creia que los rivales pujan bajo, pujaba al minimo y perdia
    las subastas.
    """
    historial = [
        {
            "user_id": 1,
            "name": "R1",
            "maximum_bid": 10_000_000,
            "lost_bid_history": (
                [
                    {
                        "amount": 1_050_000,
                        "player_id": 77,
                        "date": 1_786_400_000 + i,
                    }
                    for i in range(13)
                ]
                + [
                    {
                        "amount": 9_000_000,
                        "player_id": 77,
                        "date": 1_786_400_100,
                    },
                    {
                        "amount": 420_000,
                        "player_id": 77,
                        "date": 1_786_400_200,
                    },
                ]
            ),
        }
    ]

    prima = calibrate_premium_curve(
        historial,
        price_lookup=lambda pid, cuando: 1_000_000,
    )

    assert prima["samples"] == 13, (
        f"Quedaron {prima['samples']} muestras; deberian ser 13."
    )
    assert prima["discarded_impossible"] == 1, (
        "La puja por debajo del precio de salida tiene que "
        "descartarse y contarse."
    )

    print(
        "  OK  una puja por debajo del precio de salida no "
        "envenena la curva"
    )


def test_sin_precio_de_aquel_momento_no_se_calibra() -> None:
    """
    Preferimos la curva por defecto documentada antes que una
    medicion sesgada, porque un sesgo parece medido.
    """
    historial = [
        {
            "user_id": 1,
            "name": "R1",
            "maximum_bid": 10_000_000,
            "lost_bid_history": [
                {
                    "amount": 1_050_000,
                    "player_id": 77,
                    "date": 1_786_400_000 + i,
                }
                for i in range(20)
            ],
        }
    ]

    prima = calibrate_premium_curve(
        historial,
        price_lookup=lambda pid, cuando: 0,
    )

    assert prima["calibrated"] is False
    assert prima["discarded_no_price"] == 20
    assert prima["curve"] == list(DEFAULT_PREMIUM_CURVE)

    print("  OK  sin precio de aquel momento se usa el prior")


def test_un_lookup_sin_fecha_no_se_acepta() -> None:
    """
    Un buscador de un solo argumento mediria contra el precio de
    hoy y devolveria el sesgo. Se rechaza en vez de usarse.
    """
    historial = [
        {
            "user_id": 1,
            "name": "R1",
            "maximum_bid": 10_000_000,
            "lost_bid_history": [
                {
                    "amount": 1_050_000,
                    "player_id": 77,
                    "date": 1_786_400_000 + i,
                }
                for i in range(20)
            ],
        }
    ]

    prima = calibrate_premium_curve(
        historial,
        price_lookup=lambda pid: 1_000_000,
    )

    assert prima["calibrated"] is False, (
        "Un lookup sin fecha no puede calibrar nada."
    )

    print("  OK  un buscador sin fecha se rechaza")


# ============================================================
# ROBUSTEZ
# ============================================================

def test_aguanta_inteligencia_rota() -> None:
    casos = [
        None, {}, {"managers": None}, {"managers": [None, "x", 7]},
        {"managers": [{"maximum_bid": "mucho"}]},
        {"managers": [{"user_id": None, "lost_bids": None}]},
    ]

    for caso in casos:
        model = build_bid_model(caso, own_user_id=YO)

        assert isinstance(model["rivals"], list)

        resultado = optimal_bid(PRECIO, VALOR, model)

        assert isinstance(resultado["bid"], int)
        assert resultado["bid"] >= 0

    print("  OK  aguanta inteligencia de rivales rota")


def test_un_precio_invalido_no_genera_puja() -> None:
    model = modelo()

    for precio in (0, -1, None):
        resultado = optimal_bid(precio, VALOR, model)
        assert resultado["bid"] == 0
        assert resultado["decision"] == "PRECIO_INVALIDO"

    print("  OK  un precio invalido nunca genera puja")


# ============================================================

TESTS = [
    test_el_que_nunca_ha_pujado_no_es_una_amenaza,
    test_la_participacion_sale_del_historial,
    test_sin_historial_se_supone_una_probabilidad_prudente,
    test_quien_no_puede_pagar_no_compite,
    test_pepe_no_se_cuenta_a_si_mismo,
    test_pujar_mas_nunca_baja_la_probabilidad,
    test_sin_rivales_activos_el_minimo_gana_seguro,
    test_mas_rivales_activos_bajan_la_probabilidad,
    test_el_mas_uno_aparece_cuando_de_verdad_toca,
    test_con_rivales_activos_se_sube_hasta_donde_compensa,
    test_el_importe_elegido_es_el_de_mas_valor_esperado,
    test_no_se_puja_si_vale_menos_de_lo_que_cuesta,
    test_no_se_inmoviliza_la_caja_en_una_tombola,
    test_el_presupuesto_disponible_es_un_techo_duro,
    test_toda_decision_explica_por_que,
    test_sin_muestras_se_usa_la_curva_por_defecto_y_se_dice,
    test_con_historial_suficiente_se_calibra,
    test_la_curva_deja_sitio_a_la_cola,
    test_sin_conciliar_no_se_afirma_que_alguien_no_puja,
    test_con_la_historia_completa_si_se_puede_afirmar,
    test_la_falta_de_datos_encoge_lo_medido,
    test_el_ledger_solo_es_fiable_si_tambien_cuadran_los_rivales,
    test_una_puja_por_debajo_del_precio_es_imposible,
    test_sin_precio_de_aquel_momento_no_se_calibra,
    test_un_lookup_sin_fecha_no_se_acepta,
    test_aguanta_inteligencia_rota,
    test_un_precio_invalido_no_genera_puja,
]


def main() -> None:
    print("=" * 60)
    print(" MODELO DE PUJA RIVAL")
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
