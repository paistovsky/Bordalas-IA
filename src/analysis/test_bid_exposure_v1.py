"""
Exposicion en pujas vivas.

EL FALLO
    En Biwenger una puja no descuenta el saldo. El dinero se mueve
    en el reset, cuando se resuelven todas a la vez.

    El ciclo de Bordalas corre cada 30 minutos y recalcula el
    presupuesto desde el saldo. Como el saldo no baja al pujar,
    cada ciclo veia el presupuesto entero:

        10:07  presupuesto 6.400.000  ->  puja 2.500.000 por A
        10:37  presupuesto 6.400.000  ->  puja 2.500.000 por B
        11:07  presupuesto 6.400.000  ->  puja 2.500.000 por C

    Siete millones y medio comprometidos con seis y medio de
    presupuesto.

    Dentro de un ciclo si se controlaba: `build_speculation_board`
    resta de un `remaining_budget`. Pero ese contador muere con el
    ciclo.

    El tope del 40 % por operacion no tapaba esto. Solo hacia mas
    pequeno cada error suelto.

Ejecutar:
    python -m src.analysis.test_bid_exposure_v1
"""

from src.analysis.bid_exposure_engine import (
    apply_exposure_to_budget,
    build_bid_exposure,
    measure_biwenger_reflection,
)


YO = 14175949
RIVAL = 14175950


def puja_nuestra(
    offer_id: int,
    player_id: int,
    amount: int,
    status: str = "waiting",
) -> dict:
    return {
        "id": offer_id,
        "type": "purchase",
        "status": status,
        "amount": amount,
        "from": {"id": YO, "name": "Pepe Bordalas"},
        "requestedPlayers": [{"id": player_id}],
    }


def oferta_entrante(
    offer_id: int,
    player_id: int,
    amount: int,
) -> dict:
    """
    Las del Computer y las de rivales por jugadores nuestros
    llegan con from=None. No son dinero comprometido: son dinero
    que nos ofrecen.
    """
    return {
        "id": offer_id,
        "type": "purchase",
        "status": "waiting",
        "amount": amount,
        "from": None,
        "requestedPlayers": [{"id": player_id}],
    }


def snapshot(
    ofertas: list,
    balance: int = 239_968,
    maximum_bid: int = 12_414_968,
) -> dict:
    return {
        "league": {"user": {"id": YO}},
        "market": {
            "offers": ofertas,
            "status": {
                "balance": balance,
                "maximumBid": maximum_bid,
            },
        },
    }


def presupuesto(total: int = 6_400_000) -> dict:
    return {
        "enabled": True,
        "total_budget": total,
        "single_operation_limit": int(total * 0.40),
        "mode": "CASH_AND_DEBT",
        "reason": "Presupuesto de prueba.",
    }


# ============================================================
# CONTAR
# ============================================================

def test_suma_nuestras_pujas_vivas() -> None:
    exposicion = build_bid_exposure(
        snapshot([
            puja_nuestra(1, 100, 2_500_000),
            puja_nuestra(2, 200, 2_500_000),
            puja_nuestra(3, 300, 2_500_000),
        ])
    )

    assert exposicion["available"] is True
    assert exposicion["committed_total"] == 7_500_000
    assert exposicion["operation_count"] == 3

    print("  OK  tres pujas de 2,5 M suman 7,5 M comprometidos")


def test_las_ofertas_entrantes_no_son_compromiso() -> None:
    """
    Confundirlas seria grave en la direccion contraria: las
    entrantes son dinero que ENTRA. Contarlas como compromiso
    dejaria a Pepe sin poder pujar por nada.
    """
    exposicion = build_bid_exposure(
        snapshot([
            oferta_entrante(10, 1599, 1_257_500),
            oferta_entrante(11, 7011, 4_434_600),
            puja_nuestra(12, 300, 900_000),
        ])
    )

    assert exposicion["committed_total"] == 900_000, (
        f"Solo la puja nuestra es compromiso. Salio "
        f"{exposicion['committed_total']}."
    )
    assert exposicion["operation_count"] == 1

    print("  OK  las ofertas entrantes no cuentan como compromiso")


def test_las_pujas_de_rivales_tampoco() -> None:
    ajena = puja_nuestra(20, 400, 3_000_000)
    ajena["from"] = {"id": RIVAL, "name": "Otro"}

    exposicion = build_bid_exposure(
        snapshot([ajena, puja_nuestra(21, 500, 1_000_000)])
    )

    assert exposicion["committed_total"] == 1_000_000

    print("  OK  las pujas de rivales no cuentan como nuestras")


def test_una_puja_resuelta_deja_de_contar() -> None:
    exposicion = build_bid_exposure(
        snapshot([
            puja_nuestra(30, 600, 2_000_000, status="accepted"),
            puja_nuestra(31, 700, 1_500_000, status="rejected"),
            puja_nuestra(32, 800, 800_000, status="waiting"),
        ])
    )

    assert exposicion["committed_total"] == 800_000, (
        "Solo las pujas vivas comprometen dinero."
    )

    print("  OK  solo cuentan las pujas todavia vivas")


def test_sin_pujas_no_hay_compromiso() -> None:
    exposicion = build_bid_exposure(snapshot([]))

    assert exposicion["available"] is True
    assert exposicion["committed_total"] == 0

    print("  OK  sin pujas vivas el compromiso es cero")


# ============================================================
# DESCONTAR
# ============================================================

def test_el_presupuesto_disponible_baja_con_lo_comprometido() -> None:
    exposicion = build_bid_exposure(
        snapshot([
            puja_nuestra(1, 100, 2_500_000),
            puja_nuestra(2, 200, 2_500_000),
        ])
    )

    resultado = apply_exposure_to_budget(
        presupuesto(6_400_000),
        exposicion,
    )

    assert resultado["available_budget"] == 1_400_000, (
        f"6,4 M menos 5 M comprometidos son 1,4 M, no "
        f"{resultado['available_budget']:,}."
    )
    assert resultado["exposure_applied"] is True
    assert resultado["total_budget"] == 6_400_000, (
        "El presupuesto total no se toca: lo que cambia es lo "
        "disponible."
    )

    print("  OK  6,4 M - 5 M comprometidos = 1,4 M disponibles")


def test_el_tercer_ciclo_ya_no_puede_pujar() -> None:
    """
    La secuencia exacta del fallo. Al tercer ciclo el presupuesto
    disponible ya no da para otra puja de 2,5 M.
    """
    ofertas = []
    disponibles = []

    for indice in range(3):

        exposicion = build_bid_exposure(snapshot(list(ofertas)))

        estado = apply_exposure_to_budget(
            presupuesto(6_400_000),
            exposicion,
        )

        disponibles.append(estado["available_budget"])

        ofertas.append(
            puja_nuestra(indice, 100 + indice, 2_500_000)
        )

    assert disponibles == [6_400_000, 3_900_000, 1_400_000], (
        f"El disponible deberia ir bajando ciclo a ciclo. "
        f"Salio {disponibles}."
    )
    assert disponibles[2] < 2_500_000, (
        "REGRESION: al tercer ciclo todavia cabria otra puja de "
        "2,5 M y el equipo se comprometeria por encima del "
        "presupuesto."
    )

    print(
        "  OK  ciclo a ciclo: 6,4 M -> 3,9 M -> 1,4 M "
        "(la tercera puja ya no cabe)"
    )


def test_comprometido_de_mas_no_da_disponible_negativo() -> None:
    exposicion = build_bid_exposure(
        snapshot([puja_nuestra(1, 100, 9_000_000)])
    )

    resultado = apply_exposure_to_budget(
        presupuesto(6_400_000),
        exposicion,
    )

    assert resultado["available_budget"] == 0, (
        "Un disponible negativo se propagaria como si fuese un "
        "presupuesto."
    )
    assert resultado["new_bids_allowed"] is False

    print("  OK  el disponible nunca baja de cero")


def test_sin_contador_se_dice_en_voz_alta() -> None:
    """
    Igual que con el guardarrail: un control que falla en silencio
    y parece que aprobo es peor que no tenerlo.
    """
    resultado = apply_exposure_to_budget(
        presupuesto(6_400_000),
        {"available": False, "committed_total": 0},
    )

    assert resultado["exposure_applied"] is False, (
        "Si el contador no se aplico hay que marcarlo."
    )
    assert resultado["available_budget"] == 6_400_000

    print("  OK  un presupuesto sin descontar se declara como tal")


def test_no_modifica_el_presupuesto_original() -> None:
    original = presupuesto(6_400_000)

    apply_exposure_to_budget(
        original,
        build_bid_exposure(
            snapshot([puja_nuestra(1, 100, 1_000_000)])
        ),
    )

    assert "available_budget" not in original, (
        "apply_exposure_to_budget no debe mutar su entrada."
    )

    print("  OK  no muta el presupuesto que recibe")


# ============================================================
# LA MEDICION PENDIENTE
# ============================================================

def test_la_medicion_avisa_cuando_no_se_puede_medir() -> None:
    """
    No se si Biwenger ya descuenta las pujas vivas de maximumBid.
    Si lo hiciera, estariamos restando dos veces. Esto no lo
    decide: prepara la comprobacion para cuando haya datos.
    """
    medicion = measure_biwenger_reflection(snapshot([]))

    assert medicion["measurable"] is False
    assert "sin pujas vivas" in medicion["reason"].lower()

    print("  OK  sin pujas vivas la medicion se declara imposible")


def test_la_medicion_se_activa_con_pujas_vivas() -> None:
    medicion = measure_biwenger_reflection(
        snapshot([puja_nuestra(1, 100, 2_000_000)])
    )

    assert medicion["measurable"] is True
    assert medicion["committed_total"] == 2_000_000
    assert medicion["maximum_bid"] == 12_414_968

    print("  OK  con pujas vivas la medicion queda disponible")


# ============================================================
# ROBUSTEZ
# ============================================================

def test_aguanta_snapshots_rotos() -> None:
    casos = [
        {},
        {"league": None},
        {"league": {"user": None}, "market": {"offers": []}},
        {"league": {"user": {"id": YO}}, "market": None},
        {"league": {"user": {"id": YO}}, "market": {"offers": None}},
        {
            "league": {"user": {"id": YO}},
            "market": {"offers": [None, "texto", 42]},
        },
        {
            "league": {"user": {"id": YO}},
            "market": {
                "offers": [
                    {"from": {"id": YO}, "amount": "no-es-dinero"},
                ]
            },
        },
    ]

    for caso in casos:
        exposicion = build_bid_exposure(caso)

        assert isinstance(exposicion["committed_total"], int)
        assert exposicion["committed_total"] >= 0

        resultado = apply_exposure_to_budget(
            presupuesto(),
            exposicion,
        )
        assert resultado["available_budget"] >= 0

    print("  OK  aguanta snapshots rotos sin lanzar")


def test_sin_saber_quienes_somos_no_inventa() -> None:
    """
    Si no se puede identificar nuestro usuario, contar cualquier
    oferta como nuestra seria peor que no contar nada.
    """
    exposicion = build_bid_exposure(
        {
            "league": {"user": {}},
            "market": {
                "offers": [puja_nuestra(1, 100, 5_000_000)]
            },
        }
    )

    assert exposicion["available"] is False
    assert exposicion["committed_total"] == 0

    print("  OK  sin saber quienes somos no cuenta nada")


# ============================================================

def test_no_contamos_dos_veces_lo_que_biwenger_ya_descuenta() -> None:
    """
    Medido el 16/08/2026: una puja de 480.000 EUR bajo maximumBid
    de 12.404.968 a 11.924.968 con el balance intacto.

    Biwenger YA descuenta las pujas vivas de maximumBid. Si
    ademas se las restamos al presupuesto que ya venia recortado
    por maximumBid, las contamos dos veces y Pepe puja de menos.
    """
    exposicion = build_bid_exposure(
        snapshot([
            puja_nuestra(1, 100, 480_000),
        ])
    )

    # Modelo autoriza 20 M; Biwenger solo deja 11.924.968, que ya
    # viene neto de la puja viva.
    entrada = {
        **presupuesto(11_924_968),
        "gross_budget": 20_000_000,
        "maximum_bid": 11_924_968,
    }

    resultado = apply_exposure_to_budget(
        entrada,
        exposicion,
    )

    assert resultado["available_budget"] == 11_924_968, (
        f"El techo de Biwenger ya venia neto: disponible deben "
        f"ser 11.924.968, no "
        f"{resultado['available_budget']:,}."
    )
    assert resultado["exposure_double_count_avoided"] is True

    print("  OK  el techo de Biwenger no se descuenta dos veces")


def test_si_manda_nuestro_modelo_si_se_descuenta() -> None:
    """
    El caso contrario: cuando el limite lo pone nuestro modelo y
    no maximumBid, lo comprometido SI hay que restarlo, porque
    nuestro presupuesto bruto no sabe nada de pujas vivas.
    """
    exposicion = build_bid_exposure(
        snapshot([
            puja_nuestra(1, 100, 2_000_000),
        ])
    )

    entrada = {
        **presupuesto(6_400_000),
        "gross_budget": 6_400_000,
        "maximum_bid": 30_000_000,
    }

    resultado = apply_exposure_to_budget(
        entrada,
        exposicion,
    )

    assert resultado["available_budget"] == 4_400_000, (
        f"6,4 M brutos menos 2 M comprometidos son 4,4 M, no "
        f"{resultado['available_budget']:,}."
    )
    assert resultado["exposure_double_count_avoided"] is False

    print("  OK  con el modelo mandando, lo comprometido si resta")


def test_nunca_por_encima_del_presupuesto_autorizado() -> None:
    """
    Red de seguridad: pase lo que pase con bruto y techo, lo
    disponible no puede superar lo que ya se habia autorizado.
    """
    exposicion = build_bid_exposure(
        snapshot([
            puja_nuestra(1, 100, 10_000),
        ])
    )

    entrada = {
        **presupuesto(1_000_000),
        "gross_budget": 50_000_000,
        "maximum_bid": 40_000_000,
    }

    resultado = apply_exposure_to_budget(
        entrada,
        exposicion,
    )

    assert resultado["available_budget"] <= 1_000_000, (
        f"Disponible no puede superar el total autorizado: "
        f"{resultado['available_budget']:,}."
    )

    print("  OK  disponible nunca supera el total autorizado")


TESTS = [
    test_suma_nuestras_pujas_vivas,
    test_las_ofertas_entrantes_no_son_compromiso,
    test_las_pujas_de_rivales_tampoco,
    test_una_puja_resuelta_deja_de_contar,
    test_sin_pujas_no_hay_compromiso,
    test_el_presupuesto_disponible_baja_con_lo_comprometido,
    test_el_tercer_ciclo_ya_no_puede_pujar,
    test_comprometido_de_mas_no_da_disponible_negativo,
    test_sin_contador_se_dice_en_voz_alta,
    test_no_modifica_el_presupuesto_original,
    test_la_medicion_avisa_cuando_no_se_puede_medir,
    test_la_medicion_se_activa_con_pujas_vivas,
    test_aguanta_snapshots_rotos,
    test_sin_saber_quienes_somos_no_inventa,
    test_no_contamos_dos_veces_lo_que_biwenger_ya_descuenta,
    test_si_manda_nuestro_modelo_si_se_descuenta,
    test_nunca_por_encima_del_presupuesto_autorizado,
]


def main() -> None:
    print("=" * 60)
    print(" EXPOSICION EN PUJAS VIVAS")
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
