"""
Cada apuesta con la confianza de lo que de verdad apuesta.

SINTOMA

    El acelerador del 08/09 funcionaba y no se notaba. Bardeli, a
    +4,62 %/dia, proyectaba +138.628 EUR y valia cero.

CAUSA

    Dos cosas, y la segunda es la que nadie veia:

    1. ERROR DE CATEGORIA. `speculation_value` multiplicaba por
       una confianza que mide la certeza sobre los PUNTOS del
       jugador -0,4125 para Bardeli: sin historico y sin
       pronostico de titularidad-. Para una apuesta de PRECIO eso
       no viene a cuento.

    2. ASIMETRIA. `computer_resale_value` no llevaba confianza
       NINGUNA. La via que mira al jugador iba penalizada; la que
       no lo mira, limpia. Por eso ganaba en 21 de 22, y por eso
       todo salia plano: esa via es igual para todos por
       construccion.

Y UNA TERCERA QUE SALIO AL CALCULARLO

    3. LA CONFIANZA SE APLICABA AL CAPITAL, NO A LA GANANCIA.
       Con la confianza correcta puesta, TODAS las vias caian a
       cero. El motivo no era el numero sino donde se multiplica.

CONSECUENCIA

    Esta guardia fija las tres confianzas, de donde sale cada
    numero, y sobre todo que esto sigue siendo SOMBRA: el motor
    decide igual que ayer.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.route_confidence import (
    MAX_READING_BONUS,
    NO_STREAK_CONFIDENCE,
    PREMIUM_PRIOR,
    PREMIUM_SHRINK_SAMPLES,
    STREAK_CONTINUATION,
    premium_confidence,
    streak_confidence,
    value_with_confidence_on_gain,
)


# ============================================================
# 1. LA CONFIANZA DE LA RACHA ES LA CONTINUACION MEDIDA
# ============================================================


def test_los_numeros_son_los_del_estudio_del_07_09() -> None:
    """
    No son inventados: son la probabilidad medida de que el
    movimiento siga al dia siguiente.
    """

    tramos = {dias: prob for dias, prob, _ in STREAK_CONTINUATION}

    assert tramos[1] == 0.920
    assert tramos[2] == 0.941
    assert tramos[3] == 0.738
    assert NO_STREAK_CONFIDENCE == 0.851


def test_NO_es_monotona_y_es_a_proposito() -> None:
    """
    LA PARTE CONTRAINTUITIVA.

    El encargo daba por hecho que "una racha de seis dias es mas
    fiable que un dia suelto". Los datos dicen que no: la
    continuacion sube hasta el segundo dia y CAE al tercero, del
    94,1 % al 73,8 %.

    Darle mas confianza a una racha larga habria ido contra
    nuestros propios numeros, y contra el aviso de "racha sin
    gasolina" del 08/09, que se apoya en la misma medicion.
    """

    dos, _ = streak_confidence(trend_days=2)
    seis, _ = streak_confidence(trend_days=6)

    assert seis < dos, (
        f"una racha de seis dias ({seis}) sale mas fiable que una "
        f"de dos ({dos}): eso contradice la medicion"
    )


def test_una_racha_de_dos_dias_es_la_mas_fiable() -> None:
    valores = {
        dias: streak_confidence(trend_days=dias)[0]
        for dias in (0, 1, 2, 3, 5)
    }

    assert valores[2] == max(valores.values())


def test_la_confianza_viaja_con_su_explicacion() -> None:
    """Una confianza sin origen no se puede discutir."""

    _, motivo = streak_confidence(trend_days=2, sources=3)

    assert "94.1" in motivo or "94,1" in motivo
    assert "237" in motivo, "falta el tamaño de la muestra"


def test_el_signo_de_la_racha_no_importa() -> None:
    """Una racha de bajada es igual de persistente que una de subida."""

    assert (
        streak_confidence(trend_days=-3)[0]
        == streak_confidence(trend_days=3)[0]
    )


def test_varias_fuentes_suman_poco_y_se_dice_por_que() -> None:
    """
    El 06/09 se midio que las tres fuentes copian el mismo numero
    de Biwenger: cero discrepancias de direccion en 288 jugadores.

    Asi que "confirmado por tres" no dice que el movimiento sea
    mas real: dice que lo hemos LEIDO bien. Tratarlo como
    corroboracion seria contar tres veces el mismo dato.
    """

    una, _ = streak_confidence(trend_days=2, sources=1)
    tres, motivo = streak_confidence(trend_days=2, sources=3)

    assert tres > una
    assert tres - una <= MAX_READING_BONUS + 1e-9, (
        "el bono por fuentes se ha desbocado: son copias del mismo "
        "numero, no tres opiniones"
    )
    assert "LECTURA" in motivo


def test_la_confianza_nunca_pasa_de_uno() -> None:
    valor, _ = streak_confidence(trend_days=2, sources=99)

    assert valor <= 1.0


# ============================================================
# 2. LA CONFIANZA DEL PREMIUM SALE DE SU RATIO MEDIDO
# ============================================================


def _prima(ratio=0.745, priced=102, available=True):
    """
    La prima medida, con la forma real del bloque de produccion
    del 04/09. `calibrated` hace falta: sin el, `usable_premium`
    devuelve None y la via del Computer ni se abre.
    """

    return {
        "available": available,
        "calibrated": True,
        "positive_ratio": ratio,
        "priced": priced,
        "median_percent": 1.76,
        "min_samples": 12,
    }


def test_sale_del_ratio_medido_no_de_un_numero_redondo() -> None:
    valor, motivo = premium_confidence(_prima())

    # 0,745 encogido hacia 0,5 con n=102 y k=12.
    peso = 102 / (102 + 12)
    esperado = round(0.745 * peso + 0.5 * (1 - peso), 4)

    assert valor == esperado
    assert "76 de 102" in motivo, (
        "el motivo tiene que decir sobre cuantas ventas se mide"
    )


def test_con_pocas_muestras_se_encoge_hacia_la_moneda_al_aire() -> None:
    """
    Con 12 ventas -el minimo que exige el propio medidor- el ratio
    y el prior pesan lo mismo. No puede valer igual que con 102.
    """

    assert PREMIUM_SHRINK_SAMPLES == 12
    assert PREMIUM_PRIOR == 0.5

    poca, _ = premium_confidence(_prima(priced=12))
    mucha, _ = premium_confidence(_prima(priced=102))

    assert poca < mucha
    assert abs(poca - (0.745 + 0.5) / 2) < 1e-9, (
        "con la muestra minima el ratio y el prior tienen que "
        "pesar lo mismo"
    )


def test_sin_medida_no_hay_confianza_que_dar() -> None:
    for bloque in (None, {}, _prima(available=False),
                   {"available": True}, _prima(priced=0)):
        valor, motivo = premium_confidence(bloque)
        assert valor is None, f"se invento una confianza con {bloque}"
        assert motivo


def test_esta_via_falla_una_de_cada_cuatro_y_ahora_lo_paga() -> None:
    """
    `positive_ratio` 0,745 significa que el Computer NO paga por
    encima una de cada cuatro veces. Hasta hoy esa via no llevaba
    descuento ninguno.
    """

    valor, _ = premium_confidence(_prima())

    assert valor < 0.8, (
        "la via del Computer sigue saliendo casi gratis: era el "
        "motivo de que ganase siempre"
    )


# ============================================================
# 3. DONDE SE APLICA: A LA GANANCIA, NO AL CAPITAL
# ============================================================


def test_el_principal_no_esta_en_riesgo() -> None:
    """
    LO QUE SALIO AL CALCULARLO.

    Con la confianza puesta como la aplica el motor -sobre el
    precio entero- TODAS las vias caian a cero. La via del
    Computer, cuya ventaja es del 1,76 %, con confianza 0,72
    quedaba en 1.202.010 EUR sobre un precio de 1.650.000: por
    debajo del propio precio.

    Si la apuesta falla sigues teniendo un jugador que vale lo
    que vale. Lo incierto es la GANANCIA.
    """

    precio = 1_650_000
    ganancia = 29_040                    # 1,76 % de 1.650.000
    confianza = 0.719

    # Como lo hace el motor hoy: sobre el capital.
    como_el_motor = int((precio + ganancia * 0.75) * confianza)

    assert como_el_motor < precio, (
        "sin esta patologia no habria nada que arreglar"
    )

    # Como debe hacerse: sobre la ganancia.
    correcto = value_with_confidence_on_gain(precio, ganancia, confianza)

    assert correcto > precio
    assert correcto == int(precio + ganancia * confianza * 0.75)


def test_sin_ganancia_no_hay_valor() -> None:
    assert value_with_confidence_on_gain(1_000_000, 0, 0.9) == 0
    assert value_with_confidence_on_gain(1_000_000, -5_000, 0.9) == 0


def test_confianza_cero_deja_la_operacion_en_nada() -> None:
    assert value_with_confidence_on_gain(1_000_000, 50_000, 0.0) == 0


def test_mas_confianza_paga_mas() -> None:
    poca = value_with_confidence_on_gain(1_000_000, 100_000, 0.5)
    mucha = value_with_confidence_on_gain(1_000_000, 100_000, 0.95)

    assert mucha > poca > 1_000_000


def test_nunca_lanza_con_basura() -> None:
    for args in ((None, None, None), ("x", "y", "z"), (0, 0, 0)):
        assert value_with_confidence_on_gain(*args) == 0


# ============================================================
# 4. Y SIGUE SIENDO SOMBRA
# ============================================================


def _contexto(rates, premium):
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
        market_rates=rates,
    )


def _ritmo(pid, tasa, dias=2, fuentes=3):
    return {
        int(pid): {
            "rate_percent_per_day": tasa,
            "direction": "UP" if tasa > 0 else "DOWN",
            "trend_days": dias,
            "demand_net": 40.0,
            "sources": fuentes,
        }
    }


def _jugador(**campos):
    base = {
        "id": 900,
        "name": "Bardeli",
        "position": 3,
        "price": 1_650_000,
        "priceIncrement": 100_000,
        "points": 10,
        "pointsLastSeason": 0,
        "status": "ok",
        "teamID": 1,
    }
    base.update(campos)
    return base


def test_la_sombra_se_publica_al_lado_y_no_manda() -> None:
    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(_ritmo(900, 4.624), _prima())

    v = value_candidate(_jugador(), contexto)

    sombra = v.get("confidence_shadow")

    assert sombra is not None
    assert sombra["observer_only"] is True

    # El valor que DECIDE no es el de la sombra.
    assert v["value"] != sombra["value"], (
        "si coinciden, o la sombra no hace nada o se ha enchufado"
    )


def test_el_caso_bardeli_se_desbloquea_en_la_sombra() -> None:
    """
    El caso que abrio todo esto: +4,62 %/dia, +138.628 EUR
    proyectados, y cero.
    """

    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(_ritmo(900, 4.624), _prima())

    v = value_candidate(_jugador(), contexto)

    assert v["as_speculation"]["value"] == 0, (
        "hoy la via de tendencia sigue dando cero: si ya no lo da, "
        "el motor ha cambiado y esto ya no es sombra"
    )

    sombra = v["confidence_shadow"]

    assert sombra["speculation_value"] > 1_650_000, (
        "en la sombra la via de tendencia tiene que valer algo"
    )
    assert sombra["route"] == "PRICE_TREND", (
        f"la via de tendencia deberia ganar con este ritmo, gano "
        f"{sombra['route']}"
    )


def test_las_dos_vias_se_pueden_comparar_por_nombre() -> None:
    """
    `speculation_value` no se etiqueta a si misma. Sin etiqueta no
    se puede contestar a "¿que via gana?", que es toda la pregunta
    de este encargo.
    """

    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto(_ritmo(900, 4.624), _prima())

    v = value_candidate(_jugador(), contexto)

    assert (v.get("market_gate") or {}).get("route_now"), (
        "no se publica que via gana HOY"
    )
    assert v["confidence_shadow"]["route"], (
        "no se publica que via gana con el esquema nuevo"
    )


def test_el_motor_no_ha_cambiado_de_confianzas() -> None:
    """
    La sombra no puede haberse colado en la ruta que decide.
    """

    fuente = Path(
        "src/analysis/acquisition_valuation.py"
    ).read_text(encoding="utf-8")

    # La via viva sigue recibiendo la confianza de los puntos.
    assert 'confidence=estimacion["confidence"]' in fuente, (
        "la via de tendencia viva ha dejado de usar la confianza "
        "de puntos: eso ya no es sombra, es un cambio de motor"
    )


def test_la_via_del_computer_viva_sigue_sin_confianza() -> None:
    """
    Añadirle el descuento a la via viva cambiaria que compra Pepe.
    Por defecto la funcion sigue en 1,0.
    """

    from src.analysis.player_value_engine import computer_resale_value

    sin_tocar = computer_resale_value(1_650_000, 0.0176)
    con_uno = computer_resale_value(1_650_000, 0.0176, confidence=1.0)

    assert sin_tocar["value"] == con_uno["value"]
    assert sin_tocar["value"] == 1_671_780, (
        "el numero de la foto del 04/09 ha cambiado: la via viva se "
        "ha movido"
    )


def test_no_se_ha_bajado_ningun_umbral() -> None:
    from src.analysis.rival_bid_model import (
        MIN_SPECULATION_EXPECTED_VALUE,
        MIN_SPECULATION_YIELD,
    )

    assert MIN_SPECULATION_YIELD == 0.03
    assert MIN_SPECULATION_EXPECTED_VALUE == 25_000


def test_la_via_del_computer_no_se_veta_por_falta_de_racha() -> None:
    """
    Anoche saltó `test_reventa_al_computer_v1` por esto y tenia
    razon: esa via no apuesta a que el jugador suba. Aqui solo se
    le añade el descuento que le corresponde, no un veto.
    """

    from src.analysis.acquisition_valuation import value_candidate

    contexto = _contexto({}, _prima())      # sin ritmo de nadie

    v = value_candidate(
        _jugador(price=3_000_000, priceIncrement=0), contexto
    )

    assert v["value"] > 3_000_000
    assert (v.get("market_gate") or {})["route_now"] == "COMPUTER_RESALE"

    # Y en la sombra sigue viva, solo que con su descuento.
    sombra = v["confidence_shadow"]

    assert sombra["computer_resale_value"] > 3_000_000
    assert sombra["computer_resale_value"] < v["value"], (
        "la via del Computer tiene que valer MENOS con su "
        "confianza: falla una de cada cuatro veces"
    )




def test_la_sombra_llega_a_la_FILA_del_tablero() -> None:
    """
    EL ULTIMO METRO, QUE ES DONDE SE PIERDE TODO EN ESTE REPO.

    `value_candidate` la calculaba y `acquisition_board` copia los
    campos uno a uno: sin esta linea, la pantalla leia un campo
    que nunca llegaba y la columna salia vacia. Lo destapo mirar
    el `status.json` de verdad, no el codigo.
    """

    fuente = Path(
        "src/analysis/acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert '"confidence_shadow": valoracion.get(' in fuente, (
        "el tablero no copia la sombra a la fila: la columna de la "
        "pantalla saldria vacia"
    )
    assert '"market_gate": valoracion.get("market_gate")' in fuente, (
        "y lo mismo con la comparacion de anoche"
    )


TESTS = [
    test_los_numeros_son_los_del_estudio_del_07_09,
    test_NO_es_monotona_y_es_a_proposito,
    test_una_racha_de_dos_dias_es_la_mas_fiable,
    test_la_confianza_viaja_con_su_explicacion,
    test_el_signo_de_la_racha_no_importa,
    test_varias_fuentes_suman_poco_y_se_dice_por_que,
    test_la_confianza_nunca_pasa_de_uno,
    test_sale_del_ratio_medido_no_de_un_numero_redondo,
    test_con_pocas_muestras_se_encoge_hacia_la_moneda_al_aire,
    test_sin_medida_no_hay_confianza_que_dar,
    test_esta_via_falla_una_de_cada_cuatro_y_ahora_lo_paga,
    test_el_principal_no_esta_en_riesgo,
    test_sin_ganancia_no_hay_valor,
    test_confianza_cero_deja_la_operacion_en_nada,
    test_mas_confianza_paga_mas,
    test_nunca_lanza_con_basura,
    test_la_sombra_se_publica_al_lado_y_no_manda,
    test_el_caso_bardeli_se_desbloquea_en_la_sombra,
    test_las_dos_vias_se_pueden_comparar_por_nombre,
    test_la_sombra_llega_a_la_FILA_del_tablero,
    test_el_motor_no_ha_cambiado_de_confianzas,
    test_la_via_del_computer_viva_sigue_sin_confianza,
    test_no_se_ha_bajado_ningun_umbral,
    test_la_via_del_computer_no_se_veta_por_falta_de_racha,
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
    print(f"CONFIANZA POR VIA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
