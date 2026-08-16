"""
Pujar teniendo en cuenta a los rivales.

QUE HABIA ANTES
    Una escalera fija de primas sobre el precio de mercado: +8 %
    si el jugador nos gustaba mucho, +6 %, +4 %, +2 %. El mismo
    numero tanto si el rival mas rico tenia veinte millones como
    si nadie podia pagar el precio base.

    Se pierde por los dos lados: pagando primas que nadie disputa,
    y quedandose corto cuando la competencia es real.

LA SUBASTA
    A ciegas y de un solo intento. Se resuelve en el reset del
    Computer. No se ve lo que ofrecen los demas y no hay segunda
    oportunidad.

Ejecutar:
    python -m src.analysis.test_pvp_bid_v1
"""

from src.analysis.pvp_bid_engine import (
    INTENT_SPECULATION,
    INTENT_XI_UPGRADE,
    MINIMUM_WINNING_INCREMENT,
    RIVAL_MAX_OVERPAY,
    build_rival_threat,
    calculate_pvp_bid,
    ledger_is_trusted,
)


YO = 14175949
PRECIO = 1_000_000


def manager(
    user_id: int,
    nombre: str,
    maximum_bid: int,
) -> dict:
    return {
        "user_id": user_id,
        "name": nombre,
        "maximum_bid": maximum_bid,
    }


def inteligencia(
    managers: list,
    cuadra: bool = True,
) -> dict:
    return {
        "managers": managers,
        "validation": {
            "exact": cuadra,
            "difference": 0 if cuadra else -28_097_432,
        },
    }


def amenaza(
    managers: list,
    precio: int = PRECIO,
    cuadra: bool = True,
) -> dict:
    return build_rival_threat(
        inteligencia(managers, cuadra),
        precio,
        own_user_id=YO,
    )


# ============================================================
# QUIEN PUEDE COMPETIR
# ============================================================

def test_un_rival_sin_dinero_no_es_competencia() -> None:
    resultado = amenaza([
        manager(2, "Pobre", 300_000),
        manager(3, "Tambien pobre", 50_000),
    ])

    assert resultado["uncontested"] is True, (
        "Ninguno llega al precio base: no hay competencia."
    )
    assert resultado["threat_amount"] == 0

    print("  OK  quien no llega al precio base no compite")


def test_nosotros_no_somos_nuestro_rival() -> None:
    """
    Pepe aparece en el listado de managers. Contarse a uno mismo
    como amenaza haria subir la puja contra nadie.
    """
    resultado = amenaza([
        manager(YO, "Pepe Bordalas", 12_000_000),
        manager(2, "Pobre", 100_000),
    ])

    assert resultado["uncontested"] is True, (
        "REGRESION: Pepe se conto a si mismo como competencia."
    )

    print("  OK  Pepe no compite contra si mismo")


def test_la_amenaza_no_es_el_dinero_total_del_rival() -> None:
    """
    Un rival con veinte millones no paga cinco por un jugador de
    un millon. La amenaza esta acotada por lo que el jugador vale,
    no por lo que el rival tiene.
    """
    resultado = amenaza([
        manager(2, "Rico", 20_000_000),
    ])

    techo = int(PRECIO * RIVAL_MAX_OVERPAY)

    assert resultado["threat_amount"] == techo, (
        f"La amenaza deberia estar acotada en {techo:,} y no en "
        f"los 20 M del rival. Salio "
        f"{resultado['threat_amount']:,}."
    )

    print(
        f"  OK  un rival de 20 M amenaza con {techo:,} EUR, no con "
        f"20 M".replace(",", ".")
    )


def test_un_rival_justo_es_su_dinero() -> None:
    """
    Si el rival tiene menos que el techo plausible, su dinero es
    el limite.
    """
    resultado = amenaza([
        manager(2, "Justo", 1_100_000),
    ])

    assert resultado["threat_amount"] == 1_100_000

    print("  OK  un rival justo amenaza con lo que tiene")


def test_manda_el_rival_mas_fuerte() -> None:
    resultado = amenaza([
        manager(2, "Flojo", 1_050_000),
        manager(3, "Fuerte", 1_200_000),
        manager(4, "Pobre", 10_000),
    ])

    assert resultado["competitor_count"] == 2
    assert resultado["threat_amount"] == 1_200_000
    assert resultado["top_competitor"]["name"] == "Fuerte"

    print("  OK  la amenaza la marca el rival mas fuerte")


# ============================================================
# SIN COMPETENCIA
# ============================================================

def test_sin_competencia_y_ledger_fiable_se_puja_el_minimo() -> None:
    """
    Lo que pediste: si nadie tiene dinero, mercado + 1 EUR.
    """
    resultado = calculate_pvp_bid(
        PRECIO,
        amenaza([manager(2, "Pobre", 100_000)]),
        intent=INTENT_SPECULATION,
    )

    assert resultado["decision"] == "BID"
    assert resultado["bid"] == PRECIO + MINIMUM_WINNING_INCREMENT, (
        f"Sin competencia deberia bastar {PRECIO + 1:,}. Salio "
        f"{resultado['bid']:,}."
    )

    print("  OK  sin competencia: mercado + 1 EUR")


def test_sin_competencia_pero_ledger_roto_no_se_puja_al_filo() -> None:
    """
    La cautela.

    El 15/08 el ledger daba puja maxima cero a tres managers
    mientras registraba pujas suyas de entre diez y veintidos
    millones. Si el ledger no cuadra, "nadie puede competir" es
    una suposicion, no un dato.
    """
    resultado = calculate_pvp_bid(
        PRECIO,
        amenaza(
            [manager(2, "Pobre", 100_000)],
            cuadra=False,
        ),
        intent=INTENT_SPECULATION,
    )

    assert resultado["bid"] > PRECIO + MINIMUM_WINNING_INCREMENT, (
        "REGRESION: se pujo al filo fiandose de un ledger que no "
        "cuadra."
    )
    assert resultado["ledger_trusted"] is False

    print(
        f"  OK  con el ledger roto se deja margen: "
        f"{resultado['bid']:,} EUR".replace(",", ".")
    )


def test_el_ledger_se_considera_fiable_solo_si_cuadra() -> None:
    assert ledger_is_trusted(inteligencia([], True)) is True
    assert ledger_is_trusted(inteligencia([], False)) is False
    assert ledger_is_trusted(None) is False
    assert ledger_is_trusted({}) is False

    print("  OK  el ledger solo es fiable si cuadra al euro")


# ============================================================
# CON COMPETENCIA: LOS DOS MARGENES
# ============================================================

def test_para_el_once_se_supera_al_rival_con_holgura() -> None:
    resultado = calculate_pvp_bid(
        PRECIO,
        amenaza([manager(2, "Rico", 5_000_000)]),
        intent=INTENT_XI_UPGRADE,
        rational_max=3_000_000,
    )

    techo_rival = int(PRECIO * RIVAL_MAX_OVERPAY)

    assert resultado["decision"] == "BID"
    assert resultado["bid"] > techo_rival, (
        f"Para el once hay que superar la amenaza "
        f"({techo_rival:,}). Salio {resultado['bid']:,}."
    )

    print(
        f"  OK  para el XI se puja {resultado['bid']:,} EUR sobre "
        f"una amenaza de {techo_rival:,}".replace(",", ".")
    )


def test_para_especular_se_aprieta_mas() -> None:
    """
    En especulacion el margen ES el negocio. Pagar de mas se come
    la ganancia entera.
    """
    riesgo = amenaza([manager(2, "Rico", 5_000_000)])

    para_xi = calculate_pvp_bid(
        PRECIO, riesgo,
        intent=INTENT_XI_UPGRADE,
        rational_max=9_000_000,
    )
    para_especular = calculate_pvp_bid(
        PRECIO, riesgo,
        intent=INTENT_SPECULATION,
        rational_max=9_000_000,
    )

    assert para_especular["bid"] < para_xi["bid"], (
        f"Especulando hay que apretar mas que fichando para el "
        f"once. Salio {para_especular['bid']:,} contra "
        f"{para_xi['bid']:,}."
    )

    print(
        f"  OK  XI {para_xi['bid']:,} vs especulacion "
        f"{para_especular['bid']:,}".replace(",", ".")
    )


def test_con_competencia_se_paga_mas_que_sin_ella() -> None:
    """
    Lo que arregla el motor: la puja responde a la competencia en
    vez de ser la misma siempre.
    """
    sola = calculate_pvp_bid(
        PRECIO,
        amenaza([manager(2, "Pobre", 100_000)]),
        intent=INTENT_SPECULATION,
    )
    disputada = calculate_pvp_bid(
        PRECIO,
        amenaza([manager(2, "Rico", 5_000_000)]),
        intent=INTENT_SPECULATION,
        rational_max=9_000_000,
    )

    assert disputada["bid"] > sola["bid"] * 1.1, (
        "La puja no reacciona a la competencia."
    )

    print(
        f"  OK  sin rivales {sola['bid']:,}, con rivales "
        f"{disputada['bid']:,}".replace(",", ".")
    )


# ============================================================
# TECHOS
# ============================================================

def test_no_se_paga_mas_de_lo_que_vale_para_nosotros() -> None:
    resultado = calculate_pvp_bid(
        PRECIO,
        amenaza([manager(2, "Rico", 5_000_000)]),
        intent=INTENT_XI_UPGRADE,
        rational_max=1_100_000,
    )

    assert resultado["decision"] == "SUPERA_VALOR_RACIONAL"
    assert resultado["bid"] == 0
    assert resultado["bid_needed"] > 1_100_000, (
        "Hay que dejar constancia de cuanto habria hecho falta."
    )

    print("  OK  no se paga por encima del valor racional")


def test_no_se_puja_lo_que_no_hay() -> None:
    resultado = calculate_pvp_bid(
        PRECIO,
        amenaza([manager(2, "Rico", 5_000_000)]),
        intent=INTENT_XI_UPGRADE,
        available_budget=500_000,
    )

    assert resultado["decision"] == "SUPERA_PRESUPUESTO"
    assert resultado["bid"] == 0

    print("  OK  no se puja por encima del presupuesto disponible")


def test_el_presupuesto_disponible_es_el_que_manda() -> None:
    """
    Enlaza con el contador de exposicion: lo que manda es lo que
    queda sin comprometer, no el presupuesto del dia.
    """
    riesgo = amenaza([manager(2, "Pobre", 10_000)])

    con_hueco = calculate_pvp_bid(
        PRECIO, riesgo, available_budget=6_400_000
    )
    sin_hueco = calculate_pvp_bid(
        PRECIO, riesgo, available_budget=900_000
    )

    assert con_hueco["decision"] == "BID"
    assert sin_hueco["decision"] == "SUPERA_PRESUPUESTO"

    print("  OK  manda el disponible, no el presupuesto del dia")


def test_un_no_titular_no_cuenta_como_mejora_del_once() -> None:
    """
    'Es importante saber si el jugador por el que se puja es
    titular o no'. Un suplente puede ser buena especulacion, pero
    no mejora el XI, y no merece el margen holgado.
    """
    riesgo = amenaza([manager(2, "Rico", 5_000_000)])

    titular = calculate_pvp_bid(
        PRECIO, riesgo,
        intent=INTENT_XI_UPGRADE,
        rational_max=9_000_000,
        is_starter=True,
    )
    suplente = calculate_pvp_bid(
        PRECIO, riesgo,
        intent=INTENT_XI_UPGRADE,
        rational_max=9_000_000,
        is_starter=False,
    )

    assert suplente["intent"] == INTENT_SPECULATION, (
        "Un no titular no puede evaluarse como mejora del once."
    )
    assert suplente["bid"] < titular["bid"]

    print("  OK  un no titular baja a especulacion y se puja menos")


def test_sin_dato_de_titularidad_no_se_castiga() -> None:
    """
    Muchos fichajes nuevos no tienen dato. Tratar 'no lo se' como
    'no es titular' dejaria fuera media plantilla nueva.
    """
    riesgo = amenaza([manager(2, "Rico", 5_000_000)])

    resultado = calculate_pvp_bid(
        PRECIO, riesgo,
        intent=INTENT_XI_UPGRADE,
        rational_max=9_000_000,
        is_starter=None,
    )

    assert resultado["intent"] == INTENT_XI_UPGRADE, (
        "Sin dato no se degrada la intencion."
    )

    print("  OK  'no lo se' no es lo mismo que 'no es titular'")


# ============================================================
# ROBUSTEZ
# ============================================================

def test_precio_invalido_no_genera_puja() -> None:
    for precio in (0, -100, None):
        resultado = calculate_pvp_bid(
            precio,
            amenaza([], precio=PRECIO),
        )
        assert resultado["bid"] == 0
        assert resultado["decision"] == "PRECIO_INVALIDO"

    print("  OK  un precio invalido nunca genera puja")


def test_aguanta_inteligencia_de_rivales_rota() -> None:
    casos = [
        None,
        {},
        {"managers": None},
        {"managers": [None, "texto", 42]},
        {"managers": [{"maximum_bid": "mucho"}]},
        {"managers": [{"user_id": None, "maximum_bid": None}]},
    ]

    for caso in casos:
        riesgo = build_rival_threat(caso, PRECIO, own_user_id=YO)

        assert isinstance(riesgo["threat_amount"], int)

        resultado = calculate_pvp_bid(PRECIO, riesgo)

        assert isinstance(resultado["bid"], int)
        assert resultado["bid"] >= 0

    print("  OK  aguanta inteligencia de rivales rota")


def test_toda_puja_explica_por_que() -> None:
    """
    Una puja autonoma sin motivo escrito es imposible de auditar
    al dia siguiente.
    """
    casos = [
        calculate_pvp_bid(
            PRECIO, amenaza([manager(2, "Pobre", 1)])
        ),
        calculate_pvp_bid(
            PRECIO,
            amenaza([manager(2, "Rico", 5_000_000)]),
            rational_max=9_000_000,
        ),
        calculate_pvp_bid(
            PRECIO,
            amenaza([manager(2, "Rico", 5_000_000)]),
            rational_max=1,
        ),
    ]

    for resultado in casos:
        assert resultado.get("reasons"), (
            f"Decision sin motivo: {resultado.get('decision')}"
        )
        assert all(
            isinstance(motivo, str) and motivo
            for motivo in resultado["reasons"]
        )

    print("  OK  toda decision viene con su motivo")


# ============================================================

TESTS = [
    test_un_rival_sin_dinero_no_es_competencia,
    test_nosotros_no_somos_nuestro_rival,
    test_la_amenaza_no_es_el_dinero_total_del_rival,
    test_un_rival_justo_es_su_dinero,
    test_manda_el_rival_mas_fuerte,
    test_sin_competencia_y_ledger_fiable_se_puja_el_minimo,
    test_sin_competencia_pero_ledger_roto_no_se_puja_al_filo,
    test_el_ledger_se_considera_fiable_solo_si_cuadra,
    test_para_el_once_se_supera_al_rival_con_holgura,
    test_para_especular_se_aprieta_mas,
    test_con_competencia_se_paga_mas_que_sin_ella,
    test_no_se_paga_mas_de_lo_que_vale_para_nosotros,
    test_no_se_puja_lo_que_no_hay,
    test_el_presupuesto_disponible_es_el_que_manda,
    test_un_no_titular_no_cuenta_como_mejora_del_once,
    test_sin_dato_de_titularidad_no_se_castiga,
    test_precio_invalido_no_genera_puja,
    test_aguanta_inteligencia_de_rivales_rota,
    test_toda_puja_explica_por_que,
]


def main() -> None:
    print("=" * 60)
    print(" PUJA CONTRA RIVALES")
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
