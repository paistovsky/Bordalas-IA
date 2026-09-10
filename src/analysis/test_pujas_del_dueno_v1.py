"""
El dueno pujo y Pepe no se entero.

SINTOMA (10/09/2026)

    El dueno puso 11,8 M por Aubameyang a mano. Horas despues,
    en la foto de produccion de las 07:52:

        has_live_bid: false   en los 43 objetivos
        maximumBid:   15.825.383, intacto
        reloj:        "Saldo positivo (3.315.383 EUR).
                       El plazo no aprieta."

    Con 8,5 M de agujero previsto para la manana siguiente, en
    dia de jornada, y siete horas y media entre saberlo y tener
    que estar en verde.

CAUSA

    El reloj leia `balance`, y una puja viva NO mueve el balance.
    Baja `maximumBid`. Estaba medido desde el 16/08 y nadie lo
    habia conectado:

        17:01:54   saldo 239.968   maximumBid 12.404.968
           -> puja de 480.000 por Iker Munoz
        17:02:24   saldo 239.968   maximumBid 11.924.968

CONSECUENCIA

    Pepe planificaba ventas, deuda y presupuesto de fichar sobre
    un dinero que ya estaba gastado.

LO QUE SE PROTEGE

     1. Que con el par real del 16/08 el reloj publique 480.000
        comprometidos y NO diga SIN_DEUDA.
     2. Que sin ninguna puja el detector publique CERO -si la
        linea de credito estuviera mal medida, esta se pone
        roja, que es lo que queremos-.
     3. Que la linea de credito medida siga cuadrando al euro en
        los 12 estados.
     4. Que cuando las vias discrepen mande la MAS
        CONSERVADORA, nunca la optimista.
     5. Que la via de la diferencia se aparte si hubo reset o si
        el saldo se movio, en vez de adivinar.
     6. Que el reloj publique los TRES numeros por separado.
     7. Que con deuda contingente el plan diga en voz alta si NO
        se puede tapar sin tocar a un titular.
     8. Que la capacidad de pujar salga de `maximumBid` y no del
        saldo.

REGLA 24: NINGUNA GUARDIA PASA CON LAS MANOS VACIAS

    Si la tabla de fotos se queda vacia, estas guardias fallan
    en vez de pasar por no tener nada que comprobar.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Las 12 fotos estan EMPOTRADAS aqui como numeros, no leidas
    de `data/`. Salieron de las 85 fotos del 12 al 17/08 y son
    la medida, no una muestra que pueda cambiar sola.

COMO SE USA

    python -m src.analysis.test_pujas_del_dueno_v1
"""

from __future__ import annotations

from src.analysis.pujas_del_dueno import (
    DIFERENCIA,
    LINEA_DE_CREDITO,
    RESTA,
    TABLON,
    capacidad_de_pujar,
    por_el_tablon,
    por_la_diferencia,
    por_la_resta,
    pujas_comprometidas,
    valor_de_plantilla,
)

from src.analysis.solvency_clock import (
    DEUDA_CONTINGENTE,
    SIN_DEUDA,
    build_solvency_clock,
)


# ============================================================
# LAS 12 FOTOS MEDIDAS
# ============================================================
#
#     (etiqueta, saldo, maximumBid, valor_plantilla, comprometido)
#
#     Sacadas de las 85 fotos de produccion del 12 al 17/08/2026.
#     Son los 12 estados DISTINTOS que hay en ellas: saldo
#     positivo y negativo, plantillas de 15, 16 y 17 fichas, y
#     pujas vivas con desvio -1.740.001, 3.126.002- que no se
#     pueden explicar por un redondeo.
FOTOS = [
    ("20260812_1755", -4651032, 8533968, 52740000, 0),
    ("20260813_1624", -4651032, 8593968, 52980000, 0),
    ("20260813_2040", -4651032, 7203968, 52980000, 1390000),
    ("20260814_1543", -4651032, 7261468, 53210000, 1390000),
    ("20260815_2152", 239968, 12414968, 48700000, 0),
    ("20260816_1620", 239968, 12404968, 48660000, 0),
    ("20260816_1702", 239968, 11924968, 48660000, 480000),
    ("20260816_1958", 239968, 11420968, 48660000, 984000),
    ("20260816_2003", 239968, 11900968, 48660000, 504000),
    ("20260816_2011", 239968, 10664967, 48660000, 1740001),
    ("20260816_2047", 239968, 9278966, 48660000, 3126002),
    ("20260817_2025", -264032, 12053468, 49270000, 0),
]


# EL PAR DEL INCIDENTE, con nombre y hora, tal como se midio.
ANTES_DE_PUJAR = {
    "balance": 239968,
    "maximum_bid": 12404968,
    "hours_to_reset": 12.0,
}

DESPUES_DE_PUJAR = {
    "balance": 239968,
    "maximum_bid": 11924968,
    "hours_to_reset": 11.5,
}

LA_PUJA = 480000

VALOR_PLANTILLA_16_08 = 48660000


def _tablon(comprometido: int, operaciones: int = 1) -> dict:
    """Un `build_bid_exposure` de mentira, con lo justo."""

    return {
        "available": True,
        "committed_total": comprometido,
        "operation_count": operaciones if comprometido else 0,
        "operations": [],
    }


def _tablon_ciego() -> dict:
    """
    El tablon del 10/09: disponible, y sin ver nada.

    No es un fallo de lectura: Biwenger contesto y no habia
    ninguna puja publicada. Es el caso que hundio el reloj.
    """

    return {
        "available": True,
        "committed_total": 0,
        "operation_count": 0,
        "operations": [],
    }


# ============================================================
# REGLA 24
# ============================================================

def test_hay_fotos_que_comprobar():
    """
    Ninguna guardia pasa con las manos vacias.

    Si alguien vacia la tabla, todo lo de abajo pasaria por no
    tener nada que mirar. Esto lo impide.
    """

    assert len(FOTOS) >= 12, (
        f"la tabla de fotos tiene {len(FOTOS)} filas: sin fotos "
        f"estas guardias no comprueban nada"
    )

    assert any(f[4] > 0 for f in FOTOS), (
        "no hay ni una foto CON puja viva: las guardias del "
        "detector no probarian nada"
    )

    assert any(f[4] == 0 for f in FOTOS), (
        "no hay ni una foto SIN pujas: la guardia de las pujas "
        "fantasma no probaria nada"
    )


# ============================================================
# 1. EL INCIDENTE
# ============================================================

def test_el_dueno_pujo_y_pepe_no_se_entero():
    """
    El par real del 16/08, tal cual.

    Mismo saldo, `maximumBid` 480.000 mas bajo. El reloj tiene
    que publicar 480.000 comprometidos y dejar de decir
    SIN_DEUDA.
    """

    # Primero, que ANTES de pujar el reloj esta tranquilo. Si no,
    # esta guardia no distinguiria nada.
    antes = build_solvency_clock(
        ANTES_DE_PUJAR["balance"],
        30.0,
        committed_bids=0,
    )

    assert antes["state"] == SIN_DEUDA, (
        f"antes de pujar el reloj ya decia {antes['state']}"
    )

    # Ahora, con la puja puesta. El detector la ve por las tres
    # vias -menos el tablon, que ese dia SI la veia-.
    detectado = pujas_comprometidas(
        exposicion=_tablon_ciego(),
        balance=DESPUES_DE_PUJAR["balance"],
        maximum_bid=DESPUES_DE_PUJAR["maximum_bid"],
        valor_plantilla=VALOR_PLANTILLA_16_08,
        antes=ANTES_DE_PUJAR,
        ahora=DESPUES_DE_PUJAR,
    )

    assert detectado["committed"] == LA_PUJA, (
        f"detecta {detectado['committed']} y la puja fue "
        f"{LA_PUJA}"
    )

    despues = build_solvency_clock(
        DESPUES_DE_PUJAR["balance"],
        30.0,
        committed_bids=detectado["committed"],
    )

    assert despues["committed_bids"] == LA_PUJA, (
        "el reloj no publica lo comprometido"
    )

    assert despues["state"] != SIN_DEUDA, (
        f"con {LA_PUJA} EUR comprometidos el reloj sigue "
        f"diciendo SIN_DEUDA"
    )

    assert despues["state"] == DEUDA_CONTINGENTE, (
        f"el estado tenia que ser DEUDA_CONTINGENTE y es "
        f"{despues['state']}"
    )

    # 239.968 - 480.000 = -240.032
    assert despues["effective_balance"] == -240032, (
        f"el saldo efectivo sale {despues['effective_balance']}"
    )

    assert despues["deficit"] == 240032, (
        "el deficit no se esta calculando sobre el efectivo"
    )


def test_el_tablon_ciego_no_tapa_la_puja():
    """
    La via barata fallo el 10/09: contesto y no vio nada.

    Si el tablon ciego bastara para publicar cero, esto seguiria
    roto. Las otras dos vias tienen que ganarle.
    """

    r = pujas_comprometidas(
        exposicion=_tablon_ciego(),
        balance=DESPUES_DE_PUJAR["balance"],
        maximum_bid=DESPUES_DE_PUJAR["maximum_bid"],
        valor_plantilla=VALOR_PLANTILLA_16_08,
        antes=ANTES_DE_PUJAR,
        ahora=DESPUES_DE_PUJAR,
    )

    assert r["sources"][TABLON]["committed"] == 0, (
        "el tablon de esta prueba tenia que estar ciego"
    )

    assert r["committed"] == LA_PUJA, (
        f"manda el tablon ciego: publica {r['committed']}"
    )

    assert r["source"] in (RESTA, DIFERENCIA), (
        f"tenia que mandar otra via y manda {r['source']}"
    )

    assert r["disagreement"] == LA_PUJA, (
        "no publica que las vias no coinciden"
    )


# ============================================================
# 2. EL FALLO CONTRARIO
# ============================================================

def test_no_se_inventa_pujas_fantasma():
    """
    Fotos sin ninguna puja: el detector publica CERO.

    Si la linea de credito estuviera mal medida, la via de la
    resta empezaria a ver pujas donde no las hay y esta guardia
    se pondria roja. Es lo que queremos.
    """

    limpias = [f for f in FOTOS if f[4] == 0]

    assert limpias, (
        "no hay fotos sin pujas: esta guardia no prueba nada"
    )

    for etiqueta, saldo, tope, valor, _ in limpias:

        r = pujas_comprometidas(
            exposicion=_tablon(0),
            balance=saldo,
            maximum_bid=tope,
            valor_plantilla=valor,
        )

        assert r["committed"] == 0, (
            f"foto {etiqueta}: se inventa {r['committed']} EUR "
            f"de pujas que no existen"
        )

        assert r["sources"][RESTA]["committed"] == 0, (
            f"foto {etiqueta}: la resta ve pujas fantasma"
        )


def test_sin_pujas_el_reloj_no_cambia_de_estado():
    """
    Lo nuevo no puede alterar lo de antes. Sin pujas, el reloj
    dice exactamente lo que decia.
    """

    for saldo in (239968, -264032, 0):

        viejo = build_solvency_clock(saldo, 30.0)

        nuevo = build_solvency_clock(
            saldo, 30.0, committed_bids=0
        )

        assert viejo["state"] == nuevo["state"], (
            f"con saldo {saldo} el estado cambia sin haber "
            f"ninguna puja"
        )

        assert nuevo["effective_balance"] == saldo, (
            "sin pujas el efectivo tiene que ser el saldo"
        )


# ============================================================
# 3. LA LINEA DE CREDITO
# ============================================================

def test_la_linea_de_credito_cuadra_al_euro():
    """
    maximumBid == saldo + valor_plantilla * linea - comprometido

    En los 12 estados. Si Biwenger cambia la linea, esto se pone
    rojo antes de que nadie decida nada con ella.
    """

    assert LINEA_DE_CREDITO == 0.25, (
        f"la linea medida era 0,25 y ahora es {LINEA_DE_CREDITO}"
    )

    for etiqueta, saldo, tope, valor, comprometido in FOTOS:

        previsto = (
            saldo + int(valor * LINEA_DE_CREDITO) - comprometido
        )

        assert previsto == tope, (
            f"foto {etiqueta}: la cuenta da {previsto} y "
            f"maximumBid es {tope} (se llevan {tope - previsto})"
        )


def test_la_resta_encuentra_lo_comprometido_en_las_doce():
    """
    La via B, sobre las 12 fotos: tiene que dar exactamente lo
    que el tablon contaba ese dia.
    """

    for etiqueta, saldo, tope, valor, comprometido in FOTOS:

        r = por_la_resta(saldo, tope, valor)

        assert r["available"], f"foto {etiqueta}: no calcula"

        assert r["committed"] == comprometido, (
            f"foto {etiqueta}: la resta da {r['committed']} y "
            f"habia {comprometido}"
        )


def test_el_valor_de_plantilla_cuenta_a_los_listados():
    """
    Un jugador publicado en el mercado sigue siendo nuestro y
    sigue contando, a PRECIO DE MERCADO.

    En las 85 fotos del 12-17/08 habia jugadores nuestros
    listados y el ratio salio exacto contandolos.
    """

    plantilla = [
        {"id": 1, "name": "En venta", "price": 1_000_000},
        {"id": 2, "name": "Quieto", "price": 500_000},
    ]

    assert valor_de_plantilla(plantilla) == 1_500_000, (
        "el valor de plantilla no suma a todos"
    )

    assert valor_de_plantilla([]) == 0
    assert valor_de_plantilla(None) == 0


# ============================================================
# 4. MANDA LA MAS CONSERVADORA
# ============================================================

def test_cuando_discrepan_manda_la_mas_conservadora():
    """
    Nunca la optimista. Equivocarse por arriba cuesta no pujar
    un dia; por abajo, llegar a la jornada en rojo.
    """

    r = pujas_comprometidas(
        exposicion=_tablon(100_000),
        balance=DESPUES_DE_PUJAR["balance"],
        maximum_bid=DESPUES_DE_PUJAR["maximum_bid"],
        valor_plantilla=VALOR_PLANTILLA_16_08,
        antes=ANTES_DE_PUJAR,
        ahora=DESPUES_DE_PUJAR,
    )

    importes = [
        v["committed"]
        for v in r["sources"].values()
        if v.get("available")
    ]

    assert len(importes) >= 2, (
        "hacen falta dos vias disponibles para que haya "
        "discrepancia que resolver"
    )

    assert r["committed"] == max(importes), (
        f"manda {r['committed']} y la mas conservadora es "
        f"{max(importes)}"
    )


def test_sin_ninguna_via_no_se_afirma_nada():
    """
    Sin datos no se dice "no hay pujas": se dice que no se sabe.
    """

    r = pujas_comprometidas()

    assert r["available"] is False, (
        "sin ninguna via disponible dice que ha medido algo"
    )

    assert r["committed"] == 0
    assert r["source"] is None


# ============================================================
# 5. LA VIA DE LA DIFERENCIA SE APARTA CUANDO NO VALE
# ============================================================

def test_la_diferencia_no_vale_con_un_reset_por_medio():
    """
    En el reset cambian los precios y `maximumBid` se mueve solo.
    """

    r = por_la_diferencia(
        {"balance": 100, "maximum_bid": 5_000_000,
         "hours_to_reset": 0.5},
        {"balance": 100, "maximum_bid": 4_000_000,
         "hours_to_reset": 23.5},
    )

    assert r["available"] is False, (
        "resta a traves de un reset y publica una puja que no "
        "tiene por que existir"
    )

    assert "reset" in (r["reason"] or "").lower()


def test_la_diferencia_no_vale_si_el_saldo_se_movio():

    r = por_la_diferencia(
        {"balance": 100, "maximum_bid": 5_000_000},
        {"balance": 90, "maximum_bid": 4_000_000},
    )

    assert r["available"] is False, (
        "el saldo se movio y sigue restando"
    )


def test_la_diferencia_ve_el_par_del_16_08():
    """
    La contraria de las dos de arriba: cuando SI vale, mide.
    """

    r = por_la_diferencia(ANTES_DE_PUJAR, DESPUES_DE_PUJAR)

    assert r["available"] is True, r["reason"]

    assert r["committed"] == LA_PUJA, (
        f"mide {r['committed']} y fueron {LA_PUJA}"
    )


# ============================================================
# 6. EL RELOJ PUBLICA LOS TRES NUMEROS
# ============================================================

def test_el_reloj_publica_los_tres_numeros():
    """
    Saldo, comprometido y efectivo. Por separado, no refundidos
    en uno: el dueno tiene que poder ver de donde sale el
    agujero.
    """

    r = build_solvency_clock(
        3_315_383, 36.88, committed_bids=11_800_000
    )

    assert r["balance"] == 3_315_383
    assert r["committed_bids"] == 11_800_000
    assert r["effective_balance"] == -8_484_617

    assert r["deficit"] == 8_484_617, (
        "el deficit no sale del efectivo"
    )

    assert r["state"] == DEUDA_CONTINGENTE


def test_deuda_de_verdad_y_contingente_no_son_lo_mismo():
    """
    Con saldo negativo la deuda ya existe y el reloj usa su
    escalera de siempre. La etiqueta nueva es solo para el caso
    en que el agujero lo abre una puja que puede perderse.
    """

    contingente = build_solvency_clock(
        1_000_000, 30.0, committed_bids=2_000_000
    )

    de_verdad = build_solvency_clock(-1_000_000, 30.0)

    assert contingente["state"] == DEUDA_CONTINGENTE

    assert de_verdad["state"] != DEUDA_CONTINGENTE, (
        "una deuda real se esta etiquetando como contingente"
    )


# ============================================================
# 7. EL PLAN DE LOS DOS MUNDOS
# ============================================================

def _ofertas():
    return [
        {
            "players": ["Titular caro"],
            "amount": 5_000_000,
            "hours_to_expiry": 47.0,
            "protection": "NORMAL",
        },
        {
            "players": ["Suplente"],
            "amount": 300_000,
            "hours_to_expiry": 23.0,
            "protection": "NORMAL",
        },
    ]


def test_dice_en_voz_alta_que_no_se_puede_sin_titulares():
    """
    Lo que el 10/09 no dijo.
    """

    r = build_solvency_clock(
        0,
        30.0,
        offers=_ofertas(),
        market_clock={"hours_to_reset": 23.5},
        committed_bids=4_000_000,
        starters=["Titular caro"],
    )

    plan = r["two_world_plan"]

    assert plan["available"] is True

    assert plan["if_won"]["covered"] is False, (
        "dice que se puede tapar con 300.000 un agujero de 4 M"
    )

    assert "NO HAY PLAN" in plan["reason"], (
        f"no lo dice en voz alta: {plan['reason']}"
    )

    assert plan["never_sell_starters"] is True


def test_lo_que_es_gratis_en_los_dos_mundos_sale_aparte():
    """
    Ofertas de gente que no juega que caducan en el mismo reset
    en que se resuelve la puja: se pierden si no se cobran, y no
    cuestan un punto en ninguno de los dos mundos.
    """

    r = build_solvency_clock(
        0,
        30.0,
        offers=_ofertas(),
        market_clock={"hours_to_reset": 23.5},
        committed_bids=4_000_000,
        starters=["Titular caro"],
    )

    gratis = r["two_world_plan"]["free_in_both_worlds"]

    assert [g["name"] for g in gratis] == ["Suplente"], (
        f"lo gratis sale mal: {gratis}"
    )


def test_el_titular_no_entra_en_el_plan_ni_para_sumar():
    """
    Con deuda contingente no se vende a un titular. Ni siquiera
    se cuenta su oferta para decir que el agujero esta tapado:
    eso seria taparlo con dinero que no se va a tocar.
    """

    r = build_solvency_clock(
        0,
        30.0,
        offers=_ofertas(),
        market_clock={"hours_to_reset": 23.5},
        committed_bids=4_000_000,
        starters=["Titular caro"],
    )

    plan = r["two_world_plan"]

    nombres = [p["name"] for p in plan["if_won"]["players"]]

    assert "Titular caro" not in nombres, (
        "el titular esta contando como liquidez"
    )

    assert plan["if_won"]["from_bench"] == 300_000


def test_si_se_pierde_no_hay_nada_que_hacer():

    r = build_solvency_clock(
        0, 30.0, committed_bids=4_000_000
    )

    assert r["two_world_plan"]["if_lost"]["need"] == 0


# ============================================================
# 8. LA CAPACIDAD SALE DE maximumBid
# ============================================================

def test_la_capacidad_sale_del_maximum_bid_y_no_del_saldo():
    """
    Si el dueno ha comprometido 11,8 M, ese dinero no se puede
    repartir otra vez.
    """

    c = capacidad_de_pujar(
        4_025_383,
        cash_budget=497_307,
        comprometido=11_800_000,
    )

    assert c["maximum_bid"] == 4_025_383, (
        "la capacidad no sale de maximumBid"
    )

    assert c["effective_cash"] == 0, (
        f"la caja efectiva sale {c['effective_cash']}: se estaria "
        f"repartiendo dinero ya comprometido"
    )

    # Y sin pujas, la caja es la de siempre: lo nuevo no puede
    # recortar nada por su cuenta.
    limpia = capacidad_de_pujar(
        15_825_383, cash_budget=497_307, comprometido=0
    )

    assert limpia["effective_cash"] == 497_307


# ============================================================
# 9. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    con = pujas_comprometidas(
        exposicion=_tablon(480_000),
        balance=239_968,
        maximum_bid=11_924_968,
        valor_plantilla=VALOR_PLANTILLA_16_08,
        antes=ANTES_DE_PUJAR,
        ahora=DESPUES_DE_PUJAR,
    )

    sin = pujas_comprometidas()

    assert set(con) == set(sin), (
        f"la forma cambia: {set(con) ^ set(sin)}"
    )

    uno = build_solvency_clock(100, 30.0)
    otro = build_solvency_clock(100, 30.0, committed_bids=5_000)

    assert set(uno) == set(otro), (
        f"el reloj cambia de forma: {set(uno) ^ set(otro)}"
    )


def test_ninguna_de_estas_funciones_lanza():

    for basura in (None, {}, "no", 0, []):

        assert isinstance(por_el_tablon(basura), dict)
        assert isinstance(
            por_la_resta(basura, basura, basura), dict
        )
        assert isinstance(
            por_la_diferencia(basura, basura), dict
        )
        assert isinstance(capacidad_de_pujar(basura), dict)


TESTS = [
    test_hay_fotos_que_comprobar,
    test_el_dueno_pujo_y_pepe_no_se_entero,
    test_el_tablon_ciego_no_tapa_la_puja,
    test_no_se_inventa_pujas_fantasma,
    test_sin_pujas_el_reloj_no_cambia_de_estado,
    test_la_linea_de_credito_cuadra_al_euro,
    test_la_resta_encuentra_lo_comprometido_en_las_doce,
    test_el_valor_de_plantilla_cuenta_a_los_listados,
    test_cuando_discrepan_manda_la_mas_conservadora,
    test_sin_ninguna_via_no_se_afirma_nada,
    test_la_diferencia_no_vale_con_un_reset_por_medio,
    test_la_diferencia_no_vale_si_el_saldo_se_movio,
    test_la_diferencia_ve_el_par_del_16_08,
    test_el_reloj_publica_los_tres_numeros,
    test_deuda_de_verdad_y_contingente_no_son_lo_mismo,
    test_dice_en_voz_alta_que_no_se_puede_sin_titulares,
    test_lo_que_es_gratis_en_los_dos_mundos_sale_aparte,
    test_el_titular_no_entra_en_el_plan_ni_para_sumar,
    test_si_se_pierde_no_hay_nada_que_hacer,
    test_la_capacidad_sale_del_maximum_bid_y_no_del_saldo,
    test_la_forma_no_cambia_con_los_datos,
    test_ninguna_de_estas_funciones_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LAS PUJAS DEL DUENO V1")
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
