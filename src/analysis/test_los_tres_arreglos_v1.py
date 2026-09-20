"""
Los tres arreglos que no tocan ningun umbral.

QUE SE PRUEBA AQUI

    1. `test_la_via_que_gana_no_presta_su_etiqueta`
       Con las dos vias devolviendo valores distintos, la razon
       publicada corresponde a la GANADORA. Y la guardia FALLA si
       solo hay una via viva, porque entonces no probaria nada.

    2. `test_el_acierto_y_el_error_comparten_muestra`
       El acierto y el error de tamaño salen del MISMO conjunto de
       registros, y se comprueba CONTANDO. Falla si alguno llega
       vacio.

    3. `test_los_pesos_salen_de_la_masa`
       Los siete pesos no pueden ser todos iguales salvo que la
       masa observada lo sea. Falla si la lista de pujas llega
       vacia.

EL FALLO QUE ABRIO ESTO (14/09/2026)

    Seis rechazos de la misma foto con el mismo numero hasta el
    cuarto decimal —0,1443 %— y ritmos del ojeador que iban del
    +0,297 % al +0,995 %. Marc Roca SUBIENDO y Veiga CAYENDO un
    1,19 % al dia daban el mismo "rendimiento de especulacion".

        `computer_resale_value` devuelve intent SPECULATION y
        route COMPUTER_RESALE. La via de tendencia devuelve lo
        mismo por PRICE_TREND. Compiten en un `max()` por valor y
        la que gana presta su `value`. El motivo decia siempre
        "como especulacion", y cuando ganaba la del Computer eso
        era falso: el valor era `precio x 1,015075`, la prima
        mediana del Computer, igual para todo el tablero.

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todo son fixtures escritos aqui. No se abre `data/`, no se
    llama a `datetime.now()` y no se lee estado de produccion.

DOCTRINA 53 / 54 / 55

    Cada numero de estas pruebas lleva su plazo, su denominador y
    su `n`, porque los tres se rompieron en los informes
    anteriores.
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA  (doctrina 104, 20/09/2026)
#
#     Medido: con `BORDALAS_TOPE_DEL_ONCE` puesto en el
#     entorno, esta guardia se caia — y una guardia roja para el
#     paso «Validate optimized production cycle», o sea para EL
#     CICLO. Es lo que paso la noche del 20/09 con
#     `BORDALAS_OBJETIVOS_EL_CATALOGO`.
#
#     Este caso mide el comportamiento POR DEFECTO, asi que el
#     interruptor se apaga aqui. El comportamiento con el puesto
#     lo mide su propia guardia, que lo enciende y lo apaga ella.
os.environ.pop("BORDALAS_TOPE_DEL_ONCE", None)

from src.analysis.player_value_engine import (
    computer_resale_value,
    speculation_value,
)
from src.analysis.rival_bid_model import (
    CORTES_DE_LA_CURVA,
    MIN_SAMPLES_PER_RUNG,
    calibrate_premium_curve,
    nombre_de_la_via,
    optimal_bid,
)
from src.intelligence.scout.accuracy import summary


# ============================================================
# EL TABLERO DE MENTIRA
# ============================================================
#
# La curva calibrada de la foto del 14/09 y sus siete rivales,
# escritos a mano. Con estos numeros el rechazo del 0,1443 % se
# reproduce exactamente, y por eso sirven de fixture.
CURVA_DE_LA_FOTO = [
    (1.0000, 0.1944),
    (1.0052, 0.1944),
    (1.0222, 0.2083),
    (1.0323, 0.1944),
    (1.0622, 0.1528),
    (1.2109, 0.0417),
    (1.2449, 0.0140),
]

# LOS SIETE RIVALES CREIBLES DE LA FOTO DEL 14/09, con su
# participacion medida. Son los de produccion: con cinco de ellos
# la aritmetica cambia —ver
# `test_la_curva_nueva_no_toca_la_especulacion_y_sube_el_once`—,
# asi que el fixture usa los siete de verdad.
RIVALES = [
    {"name": "Pollo17", "participation": 0.7548,
     "capacity": 14_284_872, "never_bids": False},
    {"name": "Luismi_Haz", "participation": 0.6133,
     "capacity": 25_772_293, "never_bids": False},
    {"name": "Mex", "participation": 0.0467,
     "capacity": 16_388_300, "never_bids": False},
    {"name": "DiosMande", "participation": 0.1939,
     "capacity": 13_161_483, "never_bids": False},
    {"name": "Prinzipote", "participation": 0.0400,
     "capacity": 16_675_672, "never_bids": False},
    {"name": "Manzagool", "participation": 0.2774,
     "capacity": 12_797_550, "never_bids": False},
    {"name": "Alvaro Retamosa", "participation": 0.0333,
     "capacity": 27_472_700, "never_bids": False},
]

MODELO = {"premium": {"curve": CURVA_DE_LA_FOTO}, "rivals": RIVALES}

# La prima mediana del Computer, medida sobre 140 ventas.
PRIMA_DEL_COMPUTER = 0.0201


def test_el_fixture_trae_de_todo() -> None:
    """
    REGLA 24. Sin las DOS vias vivas, sin rivales y sin una curva
    de masa desigual, las demas se pondrian verdes sin haber
    probado su mitad.
    """

    assert len(CURVA_DE_LA_FOTO) == len(CORTES_DE_LA_CURVA), (
        f"la curva del fixture trae {len(CURVA_DE_LA_FOTO)} "
        f"peldaños y los cortes son {len(CORTES_DE_LA_CURVA)}"
    )

    pesos = {peso for _, peso in CURVA_DE_LA_FOTO}

    assert len(pesos) > 1, (
        "la curva del fixture tiene todos los pesos iguales: "
        "entonces no se puede distinguir masa de cuantil"
    )

    assert RIVALES, "el fixture no trae rivales"

    assert any(r["participation"] > 0.5 for r in RIVALES), (
        "ningun rival del fixture puja de verdad: la probabilidad "
        "de ganar saldria 1 y no se probaria nada"
    )

    # Las dos vias tienen que dar numeros DISTINTOS con el mismo
    # precio: si coincidieran, el `max()` no elegiria nada.
    precio = 3_370_000

    trend = speculation_value(
        price=precio,
        daily_increment=0,
        horizon_days=3,
        velocity_percent_per_day=0.297,
    )

    resale = computer_resale_value(
        price=precio, premium=PRIMA_DEL_COMPUTER
    )

    assert trend["value"] != resale["value"], (
        f"las dos vias dan el mismo valor ({trend['value']}): el "
        f"fixture no puede probar cual gana"
    )

    print(
        f"  OK  el fixture trae dos vias con valores distintos "
        f"({trend['value']:,} y {resale['value']:,}), "
        f"{len(RIVALES)} rivales y una curva de masa desigual"
    )


# ============================================================
# 1. LA ETIQUETA
# ============================================================


def test_la_via_que_gana_no_presta_su_etiqueta() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    Con las dos vias devolviendo valores distintos, la razon
    publicada corresponde a la que GANO.

    Y ESTA GUARDIA FALLA SI SOLO HAY UNA VIA VIVA: con una sola
    via cualquier etiqueta acierta por casualidad, y eso no es una
    prueba.
    """

    # --------------------------------------------------
    # CASO A: gana la del Computer (Marc Roca, +0,297 %/dia)
    # --------------------------------------------------
    precio = 3_370_000

    trend = speculation_value(
        price=precio,
        daily_increment=0,
        horizon_days=3,
        velocity_percent_per_day=0.297,
    )

    resale = computer_resale_value(
        price=precio, premium=PRIMA_DEL_COMPUTER
    )

    vivas = [
        v for v in (trend, resale) if int(v.get("value") or 0) > 0
    ]

    # LAS DOS TIENEN QUE ESTAR VIVAS.
    assert len(vivas) == 2, (
        f"solo {len(vivas)} via(s) viva(s) con precio {precio:,}: "
        f"con una sola via esta guardia no prueba nada, porque "
        f"cualquier etiqueta acertaria. Arreglar el fixture, no "
        f"la guardia."
    )

    # Y TIENEN QUE DECLARAR SU VIA, las dos.
    for via in vivas:
        assert via.get("route"), (
            f"una via no declara `route` y devuelve "
            f"intent={via.get('intent')!r}: si no se declara, el "
            f"motivo no puede nombrarla"
        )

    # Comparten `intent`: ese es justo el fallo, y tiene que
    # seguir siendo visible para que la guardia valga.
    assert trend["intent"] == resale["intent"] == "SPECULATION", (
        "las dos vias ya no comparten `intent`: esta guardia "
        "existe porque lo comparten"
    )

    ganadora = max(vivas, key=lambda v: int(v["value"]))

    assert ganadora is resale, (
        f"con un ritmo de +0,297 %/dia deberia ganar la reventa "
        f"al Computer y gana {ganadora.get('route')}"
    )

    plan = optimal_bid(
        price=precio,
        value=int(ganadora["value"]),
        model=MODELO,
        intent=ganadora.get("intent"),
        route=ganadora.get("route"),
    )

    assert plan.get("value_route") == "COMPUTER_RESALE", (
        f"el plan publica la via {plan.get('value_route')!r} y el "
        f"valor vino de COMPUTER_RESALE"
    )

    motivo = plan.get("reason") or " ".join(plan.get("reasons") or [])

    assert "reventa al Computer" in motivo, (
        f"el motivo no nombra la via que gano: «{motivo}»"
    )

    assert "Como especulacion" not in motivo, (
        f"el motivo sigue diciendo «como especulacion» con un "
        f"valor de la via de reventa: «{motivo}»"
    )

    # --------------------------------------------------
    # CASO B: gana la de tendencia (Pedro Diaz, +4,545 %/dia)
    # --------------------------------------------------
    precio_b = 880_000

    trend_b = speculation_value(
        price=precio_b,
        daily_increment=0,
        horizon_days=3,
        velocity_percent_per_day=4.545,
    )

    resale_b = computer_resale_value(
        price=precio_b, premium=PRIMA_DEL_COMPUTER
    )

    vivas_b = [
        v
        for v in (trend_b, resale_b)
        if int(v.get("value") or 0) > 0
    ]

    assert len(vivas_b) == 2, (
        f"solo {len(vivas_b)} via(s) viva(s) en el caso B: la "
        f"guardia necesita las dos"
    )

    ganadora_b = max(vivas_b, key=lambda v: int(v["value"]))

    assert ganadora_b is trend_b, (
        f"con un ritmo de +4,545 %/dia deberia ganar la tendencia "
        f"y gana {ganadora_b.get('route')}"
    )

    plan_b = optimal_bid(
        price=precio_b,
        value=int(ganadora_b["value"]),
        model=MODELO,
        intent=ganadora_b.get("intent"),
        route=ganadora_b.get("route"),
    )

    motivo_b = (
        plan_b.get("reason") or " ".join(plan_b.get("reasons") or [])
    )

    assert "ritmo del jugador" in motivo_b, (
        f"el motivo no nombra la via de tendencia: «{motivo_b}»"
    )

    assert "reventa al Computer" not in motivo_b, (
        f"el motivo nombra la reventa al Computer con un valor de "
        f"la via de tendencia: «{motivo_b}»"
    )

    # LAS DOS ETIQUETAS TIENEN QUE SER DISTINTAS: si el motivo
    # dijera lo mismo en los dos casos, no estaria nombrando nada.
    assert plan.get("value_route") != plan_b.get("value_route"), (
        "el plan publica la misma via cuando gana una y cuando "
        "gana la otra"
    )

    print(
        f"  OK  gana {plan['value_route']} -> el motivo dice "
        f"reventa; gana {plan_b['value_route']} -> dice ritmo"
    )


def test_sin_via_declarada_no_se_inventa_una() -> None:
    """
    Un motivo que nombra la via equivocada es peor que uno que
    dice "no consta". Sin `route`, no se adivina.
    """

    assert nombre_de_la_via(None) == "una via no declarada", (
        nombre_de_la_via(None)
    )

    assert "SPECULATION" in nombre_de_la_via(None, "SPECULATION"), (
        "sin via, el motivo deberia al menos decir que intent "
        "traia"
    )

    # Una via desconocida se nombra por su codigo, no se traduce a
    # la primera que suene.
    assert "VIA_RARA" in nombre_de_la_via("VIA_RARA"), (
        nombre_de_la_via("VIA_RARA")
    )

    # Y las dos que comparten `intent` se nombran distinto.
    assert nombre_de_la_via("PRICE_TREND") != nombre_de_la_via(
        "COMPUTER_RESALE"
    ), "las dos vias del fallo se nombran igual"

    print("  OK  sin via declarada no se inventa un nombre")


# ============================================================
# 2. EL DENOMINADOR DEL LIBRO DE ACIERTO
# ============================================================


def _libro(entradas):
    return {"predictions": {str(i): e for i, e in enumerate(entradas)}}


# Un libro con las cuatro cosas: aciertos, fallos, FLAT y
# pendientes. Los FLAT llevan error apuntado, que es justo lo que
# ensuciaba el denominador.
LIBRO_DE_MENTIRA = _libro(
    [
        {"source": "F", "outcome": "HIT", "horizon_days": 1,
         "magnitude_error_percent": 0.70, "actual_percent": 2.40},
        {"source": "F", "outcome": "HIT", "horizon_days": 1,
         "magnitude_error_percent": 0.80, "actual_percent": 2.60},
        {"source": "F", "outcome": "MISS", "horizon_days": 1,
         "magnitude_error_percent": 0.90, "actual_percent": -2.20},
        {"source": "F", "outcome": "FLAT", "horizon_days": 1,
         "magnitude_error_percent": 0.10, "actual_percent": 0.00},
        {"source": "F", "outcome": "FLAT", "horizon_days": 1,
         "magnitude_error_percent": 0.20, "actual_percent": 0.00},
        {"source": "F", "outcome": "HIT", "horizon_days": 7,
         "magnitude_error_percent": 12.00, "actual_percent": 14.20},
        {"source": "F", "outcome": "PENDING", "horizon_days": 3},
        # La mala: se equivoca mas que no decir nada.
        {"source": "PULSO", "outcome": "HIT", "horizon_days": 1,
         "magnitude_error_percent": 35.71, "actual_percent": 2.00},
        {"source": "PULSO", "outcome": "MISS", "horizon_days": 1,
         "magnitude_error_percent": 33.00, "actual_percent": -1.80},
    ]
)


def test_el_acierto_y_el_error_comparten_muestra() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    `hit_rate` sale de hits+misses. El error de tamaño se
    acumulaba ADEMAS sobre los FLAT, asi que los dos numeros se
    publicaban juntos con denominadores distintos: en produccion,
    7.579 contra 10.339.

    DOCTRINA 54. Aqui se comprueba CONTANDO, no leyendo el
    codigo. Y la guardia falla si alguno de los dos llega vacio.
    """

    fuentes = summary(LIBRO_DE_MENTIRA)["sources"]

    assert fuentes, "el resumen llega vacio"

    f = fuentes["F"]

    # NI VACIO NI A CIEGAS (regla 24).
    assert f["decided"] > 0, (
        "no hay ni una decidida: con el libro vacio esta guardia "
        "no prueba nada"
    )

    assert f["magnitude_error_n"] > 0, (
        "no hay ni un error de tamaño apuntado sobre las "
        "decididas: esta guardia no prueba nada"
    )

    assert f["flat"] > 0, (
        "el libro de mentira no trae FLAT: entonces los dos "
        "denominadores saldrian iguales y esto no probaria nada. "
        "Arreglar el fixture, no la guardia."
    )

    # EL QUE COMPARTE MUESTRA, CONTADO.
    assert f["magnitude_error_n"] == f["decided"], (
        f"el error se mide sobre {f['magnitude_error_n']} "
        f"registros y el acierto sobre {f['decided']}: siguen "
        f"sin compartir muestra (doctrina 54)"
    )

    assert f["magnitude_error_shares_sample"] is True, f

    # EL DE ANTES SIGUE PUBLICADO, CON SU NOMBRE Y SU `n`.
    assert f["magnitude_error_all_outcomes_n"] > f["decided"], (
        f"el denominador con FLAT ({f['magnitude_error_all_outcomes_n']}) "
        f"no es mayor que el de las decididas ({f['decided']}): "
        f"entonces no habia nada que separar"
    )

    assert (
        f["mean_magnitude_error_percent"]
        != f["mean_magnitude_error_percent_all_outcomes"]
    ), (
        f"los dos errores salen iguales "
        f"({f['mean_magnitude_error_percent']}): con "
        f"denominadores distintos no pueden serlo, asi que o el "
        f"fixture no separa o el calculo no ha cambiado"
    )

    # CADA PLAZO, EL SUYO (doctrina 53).
    assert f["by_horizon"], "no se publica el error por plazo"

    uno = f["by_horizon"]["1"]
    siete = f["by_horizon"]["7"]

    assert (
        uno["mean_magnitude_error_percent"]
        < siete["mean_magnitude_error_percent"]
    ), (
        f"el error a un dia ({uno['mean_magnitude_error_percent']}) "
        f"no es menor que a siete "
        f"({siete['mean_magnitude_error_percent']}): agrupar los "
        f"plazos no estaria inflando nada y este arreglo sobraria"
    )

    for plazo, tramo in f["by_horizon"].items():
        assert tramo["magnitude_error_n"] > 0, (
            f"el plazo {plazo} publica un error sin `n` "
            f"(doctrina 55)"
        )

    # EL NULO, sobre la misma muestra, y el veredicto por fuente.
    assert f["abs_actual_n"] == f["decided"], (
        f"el nulo se mide sobre {f['abs_actual_n']} y el acierto "
        f"sobre {f['decided']}"
    )

    assert f["size_beats_null"] is True, (
        f"una fuente que se equivoca "
        f"{f['mean_magnitude_error_percent']} contra un nulo de "
        f"{f['mean_abs_actual_percent']} no bate al nulo"
    )

    mala = fuentes["PULSO"]

    assert mala["size_beats_null"] is False, (
        f"la fuente que se equivoca "
        f"{mala['mean_magnitude_error_percent']} contra un nulo "
        f"de {mala['mean_abs_actual_percent']} esta batiendo al "
        f"nulo: entonces la puerta no cierra"
    )

    print(
        f"  OK  acierto y error sobre {f['decided']} registros "
        f"(el mezclado eran {f['magnitude_error_all_outcomes_n']}); "
        f"por plazo, {uno['mean_magnitude_error_percent']} a 1 dia "
        f"contra {siete['mean_magnitude_error_percent']} a 7"
    )


def test_un_libro_vacio_no_publica_numeros() -> None:
    """
    Sin registros no hay acierto ni error: hay `None` y un motivo.
    Un cero aqui se leeria como "falla siempre".
    """

    # OJO: aqui NO se pasa `None`.
    #
    #     `summary(None)` significa "lee el libro del disco", y
    #     una guardia que lee estado de produccion deja de ser
    #     una guardia: daria verde o rojo segun lo que el ciclo
    #     hubiera escrito esa hora. Las dos formas vacias que se
    #     prueban son las que puede construir el motor.
    for etiqueta, libro in (
        ("vacio", {"predictions": {}}),
        ("sin clave", {}),
    ):
        salida = summary(libro)

        assert not salida.get("sources"), (
            f"el libro «{etiqueta}» ha publicado fuentes: "
            f"{salida.get('sources')}"
        )

    # Y una fuente con solo PENDING tampoco inventa nada.
    solo_pendiente = summary(
        _libro([{"source": "F", "outcome": "PENDING"}])
    )["sources"]["F"]

    assert solo_pendiente["hit_rate"] is None, (
        f"una fuente sin decididas publica un acierto de "
        f"{solo_pendiente['hit_rate']}"
    )

    assert (
        solo_pendiente["mean_magnitude_error_percent"] is None
    ), solo_pendiente

    assert solo_pendiente["size_beats_null"] is None, (
        "sin muestra se esta afirmando que bate -o que no bate- "
        "al nulo"
    )

    print("  OK  sin registros no se publica ningun numero")


# ============================================================
# 3. LOS PESOS DE LA CURVA
# ============================================================


def _pujas(primas, precio=1_000_000):
    """Un manager con una puja por cada prima de la lista."""

    return [
        {
            "lost_bid_history": [
                {
                    "player_id": i,
                    "amount": int(round(precio * prima)),
                    "date": 1_788_000_000,
                }
                for i, prima in enumerate(primas)
            ]
        }
    ]


# Las 72 primas de la foto del 14/09, reconstruidas de sus siete
# cuantiles publicados. La forma es la que importa: mucha masa
# abajo y una cola larguisima con cuatro pujas.
PRIMAS_DE_LA_FOTO = (
    [1.0000] * 14
    + [1.0052] * 14
    + [1.0222] * 15
    + [1.0323] * 14
    + [1.0622] * 11
    + [1.2109] * 3
    + [1.2449] * 1
)


def test_los_pesos_salen_de_la_masa() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    Los siete pesos no pueden ser todos iguales salvo que la masa
    observada lo sea. Y la guardia FALLA si la lista de pujas
    llega vacia.
    """

    assert len(PRIMAS_DE_LA_FOTO) == 72, (
        f"el fixture trae {len(PRIMAS_DE_LA_FOTO)} pujas y la foto "
        f"del 14/09 tenia 72"
    )

    # LA MASA DEL FIXTURE NO PUEDE SER UNIFORME: si lo fuera, unos
    # pesos iguales serian correctos y esto no probaria nada.
    reparto = {p: PRIMAS_DE_LA_FOTO.count(p) for p in set(PRIMAS_DE_LA_FOTO)}

    assert len(set(reparto.values())) > 1, (
        f"la masa del fixture es uniforme ({reparto}): con masa "
        f"uniforme los pesos iguales serian correctos y esta "
        f"guardia no probaria nada"
    )

    medida = calibrate_premium_curve(
        _pujas(PRIMAS_DE_LA_FOTO),
        price_lookup=lambda pid, cuando: 1_000_000,
    )

    assert medida["calibrated"], medida["reason"]

    assert medida["samples"] == 72, medida["samples"]

    assert medida.get("weights_from_observed_mass") is True, medida

    pesos = [peso for _, peso in medida["curve"]]

    # LO QUE PIDE EL ENCARGO: no todos iguales.
    assert len(set(pesos)) > 1, (
        f"los siete pesos siguen siendo iguales ({pesos[0]}) con "
        f"una masa que no lo es: volvieron a 1/7"
    )

    uniforme = round(1.0 / len(pesos), 4)

    assert not all(abs(p - uniforme) < 1e-9 for p in pesos), (
        f"los pesos son 1/{len(pesos)} otra vez"
    )

    # SUMAN UNO EXACTO: una curva que suma 0,9998 mete un sesgo
    # silencioso en cada probabilidad.
    assert abs(sum(pesos) - 1.0) < 1e-9, (
        f"los pesos suman {sum(pesos)}"
    )

    # LA COLA, QUE ES LA QUE COSTABA DINERO.
    arriba = medida["rungs"][-1]

    assert arriba["weight"] < uniforme, (
        f"el peldaño de arriba (+{100 * (arriba['factor'] - 1):.2f} %) "
        f"lleva {arriba['weight']} y por construccion llevaba "
        f"{uniforme}: no ha bajado"
    )

    assert arriba["weight"] * 5 < uniforme, (
        f"el peldaño de arriba solo ha bajado de {uniforme} a "
        f"{arriba['weight']}: el informe afirma mas de cinco veces"
    )

    # CADA PELDAÑO CON SU `n` (doctrina 55).
    assert sum(r["n"] for r in medida["rungs"]) == 72, (
        f"los peldaños reparten "
        f"{sum(r['n'] for r in medida['rungs'])} de 72 pujas: hay "
        f"pujas sin caer en ningun sitio"
    )

    # LO QUE NO TIENE MUESTRA, SE DICE.
    flojos = [r for r in medida["rungs"] if not r["calibrated"]]

    assert flojos, (
        "ningun peldaño queda por debajo del minimo: entonces no "
        "se prueba que un peldaño flojo se avise"
    )

    assert medida["fully_calibrated"] is False, medida

    assert medida["rungs_below_minimum"] == len(flojos), medida

    for r in flojos:
        assert r["n"] < MIN_SAMPLES_PER_RUNG, r

        # PERO NO SE BORRA: su masa sigue ahi. Borrarla afirmaria
        # que ningun rival paga tanto, y de estas mismas 72 pujas
        # hubo cuatro que si.
        assert r["weight"] > 0, (
            f"el peldaño flojo {r['factor']} se ha quedado con "
            f"peso cero: eso afirma que nadie puja ahi, y en la "
            f"muestra hay {r['n']}"
        )

    assert "AVISO" in medida["reason"], (
        f"no se avisa de los peldaños flojos: «{medida['reason']}»"
    )

    # ------------------------------------------------------
    # CON LA LISTA DE PUJAS VACIA SE FALLA
    # ------------------------------------------------------
    for etiqueta, managers in (
        ("vacia", []),
        ("None", None),
        ("sin pujas dentro", [{"lost_bid_history": []}]),
    ):
        sin = calibrate_premium_curve(
            managers, price_lookup=lambda pid, cuando: 1_000_000
        )

        assert sin["calibrated"] is False, (
            f"con la lista de pujas «{etiqueta}» se ha dado la "
            f"curva por calibrada: no haber mirado nada no es un "
            f"aprobado (regla 24)"
        )

        assert sin["samples"] == 0, sin

        assert sin["reason"], (
            f"con la lista «{etiqueta}» no se dice por que"
        )

    print(
        f"  OK  pesos de la masa: el de arriba pasa de {uniforme} "
        f"a {arriba['weight']} (n={arriba['n']} de 72), "
        f"{len(flojos)} peldaño(s) avisados"
    )


def test_el_peso_es_la_cuenta_de_pujas_de_su_banda() -> None:
    """
    LA GUARDIA QUE DESTAPO LA PRIMERA VERSION DE ESTE ARREGLO.

    La primera version repartia la masa por la distancia entre
    INDICES de corte. Y esa distancia la fijan la rejilla de
    cuantiles y `N`, no las pujas: con 72 muestras salia siempre
    [14, 14, 15, 14, 11, 3, 1] dieran lo que dieran los rivales.
    Habria sido cambiar una constante por otra y llamarlo medir.

    Aqui se comprueba que el peso de cada peldaño es LA CUENTA de
    pujas que caen en su banda, contada aparte en la propia
    guardia. Con una muestra a proposito irregular, para que los
    numeros NO puedan coincidir con la rejilla.
    """

    # Masa deliberadamente amontonada: dos grupos grandes juntos,
    # un hueco, y una cola. Si los pesos salieran de la rejilla,
    # esto daria [14, 14, 15, 14, 11, 3, 1] igual que la foto.
    apilada = (
        [1.00] * 10
        + [1.02] * 10
        + [1.04] * 20
        + [1.08] * 10
        + [1.10] * 10
        + [1.12] * 10
    )

    medida = calibrate_premium_curve(
        _pujas(apilada),
        price_lookup=lambda pid, cuando: 1_000_000,
    )

    assert medida["calibrated"], medida["reason"]

    assert medida["samples"] == len(apilada), medida["samples"]

    contados = [r["n"] for r in medida["rungs"]]

    de_la_rejilla = [14, 14, 15, 14, 11, 3, 1]

    assert contados != de_la_rejilla, (
        f"los pesos han salido {contados}, que es lo que da la "
        f"rejilla de cuantiles: no se estan contando las pujas"
    )

    # LA CUENTA, HECHA AQUI, BANDA POR BANDA.
    factores = [f for f, _ in medida["curve"]]

    for k, factor in enumerate(factores):

        siguiente = (
            factores[k + 1] if k + 1 < len(factores) else None
        )

        if k == 0:
            esperado = sum(
                1
                for p in apilada
                if siguiente is None or p < siguiente
            )
        elif siguiente is None:
            esperado = sum(1 for p in apilada if p >= factor)
        else:
            esperado = sum(
                1 for p in apilada if factor <= p < siguiente
            )

        assert medida["rungs"][k]["n"] == esperado, (
            f"el peldaño {factor} dice n={medida['rungs'][k]['n']} "
            f"y en la banda hay {esperado} pujas"
        )

    # Todas las pujas caen en algun sitio, y los pesos suman uno.
    assert sum(contados) == len(apilada), (
        f"los peldaños reparten {sum(contados)} de "
        f"{len(apilada)} pujas"
    )

    assert abs(sum(p for _, p in medida["curve"]) - 1.0) < 1e-9, (
        medida["curve"]
    )

    print(
        f"  OK  los pesos son la cuenta de su banda {contados}, "
        f"no la rejilla {de_la_rejilla}"
    )


def test_la_curva_nueva_no_toca_la_especulacion_y_sube_el_once() -> None:
    """
    EL ENCARGO DIJO QUE ESTO NOS HARIA PUJAR MENOS. NO ES VERDAD,
    Y HAY QUE VERLO ANTES DE ENCENDER NADA.

    LO QUE DECIA EL ENCARGO DEL 16/09

        "corregirlo nos hace pujar MENOS, no mas (...) es la unica
        correccion de este encargo que ahorra dinero sin abrir
        ningun riesgo".

    LO QUE SALE AL MEDIRLO, sobre 70 combinaciones de precio
    (150.000 a 7.820.000) y valor (x1,02 a x1,40):

        SPECULATION, con su tope de +0,25 %
            sube 0   baja 0   IGUAL 70

        XI_UPGRADE, que no tiene tope de prima
            sube 10   baja 0   igual 60
            el peor: precio 7.820.000, valor x1,05
                     7.860.665  ->  8.072.587   (+211.922 EUR)

    POR QUE SUBE, Y POR QUE ES CORRECTO

        La curva vieja repartia a los rivales hasta el +24,5 %, y
        con esa forma subir un poco la puja no compraba casi
        nada. La masa real dice que casi todos pujan pegados al
        precio, asi que superarlos SI compra probabilidad — y el
        valor esperado sube con ello.

        El numero nuevo es el correcto. Lo que era falso es la
        premisa de que corregirlo ahorraba dinero.

    QUE VIGILA ESTA GUARDIA

        1. Que la via de especulacion no se mueve NI UN EURO: su
           tope de +0,25 % la deja por debajo del primer peldaño
           y ninguna reponderacion la alcanza.
        2. Que la del once sube, y CUANTO como maximo. Si alguien
           mueve la curva y ese maximo crece, salta aqui antes de
           llegar a produccion.
    """

    por_construccion = {
        "premium": {
            "curve": [
                (factor, round(1.0 / 7, 4))
                for factor, _ in CURVA_DE_LA_FOTO
            ]
        },
        "rivals": RIVALES,
    }

    por_masa = MODELO

    PRECIOS = (
        150_000, 380_000, 600_000, 880_000, 1_150_000,
        1_670_000, 2_680_000, 3_370_000, 4_790_000, 7_820_000,
    )

    MARGENES = (1.02, 1.05, 1.08, 1.10, 1.16, 1.25, 1.40)

    # EL TOPE QUE ESTA GUARDIA VIGILA. Medido hoy: +211.922 EUR
    # en el peor caso del barrido. Se deja un poco de aire para
    # que no salte por un redondeo, pero no tanto como para que
    # se cuele un cambio de verdad.
    TOPE_DE_SUBIDA = 250_000

    def barrido(intent, prima_maxima):

        sube, baja, igual = [], [], 0

        for precio in PRECIOS:
            for margen in MARGENES:

                valor = int(precio * margen)

                kw = {"price": precio, "value": valor, "intent": intent}

                if prima_maxima is not None:
                    kw["prima_maxima"] = prima_maxima

                antes = optimal_bid(model=por_construccion, **kw)
                ahora = optimal_bid(model=por_masa, **kw)

                a, b = antes.get("bid", 0), ahora.get("bid", 0)

                if b > a:
                    sube.append((precio, margen, a, b, b - a))
                elif b < a:
                    baja.append((precio, margen, a, b, b - a))
                else:
                    igual += 1

        return sube, baja, igual

    # --------------------------------------------------
    # 1. LA ESPECULACION NO SE MUEVE NI UN EURO
    # --------------------------------------------------
    from src.analysis.rival_bid_model import (  # noqa: PLC0415
        PRIMA_MAXIMA_DE_PUJA,
    )

    sube, baja, igual = barrido("SPECULATION", PRIMA_MAXIMA_DE_PUJA)

    assert igual == len(PRECIOS) * len(MARGENES), (
        f"la curva nueva mueve la via de especulacion con los "
        f"SIETE rivales de la foto: {len(sube)} suben y "
        f"{len(baja)} bajan de {len(PRECIOS) * len(MARGENES)}. "
        f"Con el tope de +0,25 % y p=0,0957 -> 0,1178, las dos "
        f"por debajo del suelo de 0,15, no deberia cambiar "
        f"ninguna"
    )

    # --------------------------------------------------
    # 1bis. PERO ESO DEPENDE DE CUANTOS RIVALES HAYA
    # --------------------------------------------------
    #
    #     Con CINCO rivales en vez de siete, `p` a precio+1 pasa
    #     de 0,1293 a 0,1558 — y `MIN_WIN_PROBABILITY` vale 0,15,
    #     justo en medio. Entonces 15 de 70 combinaciones dejan
    #     de decir PROBABILIDAD_INSUFICIENTE y pasan a pujar.
    #
    #     No es un fallo del arreglo: la probabilidad nueva es la
    #     correcta y el suelo es el de siempre. Pero significa
    #     que este cambio NO es neutro en la via de especulacion
    #     si algun rival deja de ser creible, y el dueño tiene que
    #     saberlo antes de encender.
    #
    #     Lo unico que esta guardia exige es que, cuando se abra,
    #     se abra al MINIMO: nunca a un importe mayor.
    con_cinco_vieja = {
        "premium": {"curve": por_construccion["premium"]["curve"]},
        "rivals": RIVALES[:5],
    }

    con_cinco_nueva = {
        "premium": {"curve": CURVA_DE_LA_FOTO},
        "rivals": RIVALES[:5],
    }

    aperturas = []

    for precio in PRECIOS:
        for margen in MARGENES:

            valor = int(precio * margen)

            kw = {
                "price": precio,
                "value": valor,
                "intent": "SPECULATION",
                "prima_maxima": PRIMA_MAXIMA_DE_PUJA,
            }

            antes = optimal_bid(model=con_cinco_vieja, **kw)
            ahora = optimal_bid(model=con_cinco_nueva, **kw)

            if ahora.get("bid", 0) and not antes.get("bid", 0):
                aperturas.append((precio, margen, ahora["bid"]))

            elif antes.get("bid", 0) and ahora.get("bid", 0):
                assert ahora["bid"] <= antes["bid"], (
                    f"con cinco rivales la curva nueva SUBE una "
                    f"puja de especulacion: {antes['bid']:,} -> "
                    f"{ahora['bid']:,}"
                )

    assert aperturas, (
        "con cinco rivales ya no se abre ninguna especulacion: si "
        "eso cambia, cambia el informe del 16/09"
    )

    for precio, margen, importe in aperturas:
        assert importe == precio + 1, (
            f"al abrirse, la especulacion puja {importe:,} sobre "
            f"un precio de {precio:,}: tendria que abrirse al "
            f"minimo"
        )

    # --------------------------------------------------
    # 2. LA DEL ONCE SUBE, Y SE VIGILA CUANTO
    # --------------------------------------------------
    sube, baja, igual = barrido("XI_UPGRADE", None)

    assert sube, (
        "la curva nueva ya no sube ninguna puja del once: si eso "
        "cambia, cambia el informe del 16/09 y hay que rehacer la "
        "cuenta antes de encender nada"
    )

    assert not baja, (
        f"la curva nueva BAJA la puja del once en {len(baja)} "
        f"caso(s): {baja[:3]}. Hasta hoy solo subia, y un cambio "
        f"de sentido hay que mirarlo"
    )

    peor = max(x[4] for x in sube)

    assert peor <= TOPE_DE_SUBIDA, (
        f"la curva nueva sube una puja del once en {peor:,} EUR y "
        f"el tope vigilado son {TOPE_DE_SUBIDA:,}. Alguien ha "
        f"movido la curva: mirarlo antes de que llegue a "
        f"produccion"
    )

    print(
        f"  OK  especulacion: {igual and len(PRECIOS) * len(MARGENES)} "
        f"sin mover. Once: {len(sube)} suben (peor {peor:+,} EUR), "
        f"{len(baja)} bajan"
    )


TESTS = [
    test_el_fixture_trae_de_todo,
    test_la_via_que_gana_no_presta_su_etiqueta,
    test_sin_via_declarada_no_se_inventa_una,
    test_el_acierto_y_el_error_comparten_muestra,
    test_un_libro_vacio_no_publica_numeros,
    test_los_pesos_salen_de_la_masa,
    test_el_peso_es_la_cuenta_de_pujas_de_su_banda,
    test_la_curva_nueva_no_toca_la_especulacion_y_sube_el_once,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"LOS TRES ARREGLOS V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
