"""
La segunda forma de ganar dinero con una reventa.

EL CASO (21/08/2026)

    El dueño pujo a mano 10 EUR por encima del precio de Agoumé y
    lo explico asi:

        "Como puedo endeudarme y hay tiempo hasta la siguiente
         jornada, meto 10 EUR mas por si no lo puja nadie. Si lo
         gano a precio de mercado, lo puedo poner mañana y a ver
         si Computer me hace una oferta buena y ganamos unos K's
         ahi con la operacion."

    Se midio en su tablon. 36 ventas al Computer: mediana +2,9 %
    sobre el precio de mercado, 29 de 36 por encima. Gavi +11,2 %,
    Boyé +11,5 %, Sucic +15,1 %, Miguel Rodríguez +18,4 %.

    Tenia razon. El diferencial existe.

POR QUE PEPE NO LO VEIA

    `speculation_value` solo sabe ganar de UNA manera: que el
    precio del jugador suba. Si no sube, contesta
    SIN_REVALORIZACION y vale cero.

    Por eso 15 de los 20 candidatos de aquel dia salian SIN VALOR
    con 0 EUR. No eran malos: es que solo se les preguntaba si
    iban a subir. La otra via -que el Computer paga por encima por
    cualquier cosa publicada- no estaba en el codigo.

EL DENOMINADOR

    Aquel +2,9 % se saco con el precio de HOY. Es justo el sesgo
    que `historical_price_lookup` nacio para quitar. La prueba de
    que importa: con el precio de hoy salian dos desastres,
    -39,9 % y -15,1 %; con el precio de aquel momento no aparecen.
    Eran jugadores que subieron despues.

LO QUE SE PROTEGE AQUI

    1. Que la prima se mida SIEMPRE contra el precio de aquel
       momento, nunca contra el de hoy.
    2. Que con pocas muestras no se compre nada. `calibrated` en
       falso es "no se sabe", no "no hay prima".
    3. Que un traspaso entre managers no se cuele: eso se pacta y
       no dice nada de lo que paga el Computer.
    4. Que un hecho repetido en el tablon no pese doble.
    5. Que sin prima, la valoracion siga contestando exactamente
       lo que contestaba antes.
"""

from __future__ import annotations

from src.analysis.computer_resale_premium import (
    MIN_SAMPLES,
    measure_computer_resale_premium,
    sales_to_computer,
    usable_premium,
)

from src.analysis.player_value_engine import (
    computer_resale_value,
)


PRECIO = 1_000_000


def venta(player_id, importe, cuando, vendedor="Pollo17", to=None):
    return {
        "event_id": f"e{player_id}{cuando}",
        "type": "transfer",
        "date": cuando,
        "content": [
            {
                "player": player_id,
                "amount": importe,
                "from": {"id": 1, "name": vendedor},
                **({"to": to} if to else {}),
            }
        ],
    }


def tablon(n=MIN_SAMPLES, prima=0.03):
    """n ventas al Computer, todas con la misma prima."""

    return [
        venta(
            player_id=100 + i,
            importe=int(PRECIO * (1 + prima)),
            cuando=1_780_000_000 + i * 3600,
        )
        for i in range(n)
    ]


def precios_de_aquel_momento(player_id, cuando):
    return PRECIO


def sin_precios(player_id, cuando):
    return 0


# ============================================================
# LA MEDIDA
# ============================================================


def test_se_mide_contra_el_precio_de_aquel_momento():
    """
    EL SESGO QUE MATA LA MEDIDA.

    Si el denominador vuelve a ser el precio de hoy, la prima deja
    de describir al Computer y describe a que jugadores subieron
    despues.
    """

    medida = measure_computer_resale_premium(
        events=tablon(),
        price_at=precios_de_aquel_momento,
    )

    assert medida["calibrated"] is True
    assert medida["median_percent"] == 3.0
    assert medida["positive_ratio"] == 1.0


def test_lo_que_no_se_puede_fechar_no_cuenta():
    """
    Preferimos calibrar con menos muestras que con muestras
    sesgadas. Es la misma regla que la curva de primas.
    """

    medida = measure_computer_resale_premium(
        events=tablon(),
        price_at=sin_precios,
    )

    assert medida["calibrated"] is False
    assert medida["priced"] == 0
    assert medida["discarded_no_price"] == MIN_SAMPLES
    assert medida["median_percent"] is None


def test_con_pocas_muestras_no_se_compra_nada():
    """
    LA PUERTA.

    El 21/08 habia 3 muestras fechables de las 12 que hacen falta.
    Apuntaban a +2,0 % y las tres eran positivas, que es
    exactamente el aspecto que tiene una racha.
    """

    medida = measure_computer_resale_premium(
        events=tablon(n=3),
        price_at=precios_de_aquel_momento,
    )

    assert medida["priced"] == 3
    assert medida["calibrated"] is False

    assert usable_premium(medida) is None, (
        "con 3 muestras se esta abriendo una via de compra"
    )


def test_ausencia_de_prima_no_es_prima_cero():
    """
    Un cero diria "el Computer paga justo el mercado", que es una
    afirmacion. Lo que hay es un hueco.
    """

    assert usable_premium(None) is None
    assert usable_premium({}) is None
    assert usable_premium({"calibrated": True}) is None

    assert usable_premium(
        {"calibrated": True, "median_percent": 0}
    ) is None

    assert usable_premium(
        {"calibrated": True, "median_percent": -2.0}
    ) is None, (
        "una prima negativa cierra la via, no la abre al reves"
    )


def test_un_traspaso_entre_managers_no_es_una_venta_al_computer():
    """
    Un traspaso entre dos managers se pacta. No dice nada de lo
    que paga el Computer, y meterlo ensucia la mediana.
    """

    eventos = tablon(n=4) + [
        venta(
            player_id=999,
            importe=5_000_000,
            cuando=1_780_100_000,
            to={"id": 2, "name": "Manzagool"},
        )
    ]

    ventas = sales_to_computer(eventos)

    assert len(ventas) == 4
    assert all(v["player_id"] != 999 for v in ventas)


def test_un_hecho_repetido_no_pesa_doble():
    """
    El tablon se re-descarga y el mismo movimiento puede llegar
    con dos identificadores. Contado dos veces, pesa el doble en
    la mediana.
    """

    una = venta(100, 1_030_000, 1_780_000_000)

    otra = dict(una)
    otra["event_id"] = "otro_id_para_el_mismo_hecho"

    assert len(sales_to_computer([una, otra])) == 1


def test_las_barbaridades_se_descartan():
    """
    Una venta a un 60 % del mercado no describe la regla del
    Computer: describe un precio mal fechado.
    """

    eventos = tablon(n=MIN_SAMPLES) + [
        venta(500, int(PRECIO * 3), 1_780_900_000)
    ]

    medida = measure_computer_resale_premium(
        events=eventos,
        price_at=precios_de_aquel_momento,
    )

    assert medida["discarded_outlier"] == 1
    assert medida["median_percent"] == 3.0


# ============================================================
# LO QUE SE PAGA
# ============================================================


def test_sin_prima_medida_no_hay_valor():
    """
    Es la via cerrada. Mientras no se sepa cuanto paga el
    Computer, esta ruta contesta cero igual que antes del 21/08.
    """

    valoracion = computer_resale_value(price=PRECIO, premium=None)

    assert valoracion["value"] == 0
    assert valoracion["decision"] == "PRIMA_SIN_MEDIR"


def test_con_prima_medida_se_paga_por_debajo_de_la_reventa():
    """
    El dinero llega en el reset siguiente, no hoy, y el precio
    puede moverse. Si la operacion solo sale pagando la reventa
    entera, no sale.
    """

    valoracion = computer_resale_value(
        price=PRECIO,
        premium=0.03,
        margin=0.25,
    )

    # Reventa 1.030.000; ganancia 30.000; margen exigido 7.500.
    assert valoracion["resale_estimate"] == 1_030_000
    assert valoracion["value"] == 1_022_500

    assert valoracion["value"] > PRECIO, (
        "con prima medida positiva tiene que quedar algo que pagar "
        "por encima del precio"
    )

    assert valoracion["value"] < valoracion["resale_estimate"], (
        "se esta pagando la reventa entera: la operacion solo "
        "saldria con la prima clavada"
    )

    assert valoracion["intent"] == "SPECULATION"
    assert valoracion["route"] == "COMPUTER_RESALE"


def test_una_prima_que_no_deja_margen_no_abre_la_via():
    """
    Con una prima minuscula, el margen se come la ganancia entera
    y no queda nada por encima del precio.
    """

    valoracion = computer_resale_value(
        price=PRECIO,
        premium=0.0000001,
    )

    assert valoracion["value"] == 0
    assert valoracion["decision"] == "MARGEN_INSUFICIENTE"


def test_un_precio_roto_no_produce_una_compra():
    for precio in (0, -100):
        assert computer_resale_value(
            price=precio, premium=0.03
        )["value"] == 0


# ============================================================
# LA VALORACION ENTERA
# ============================================================


def test_la_via_nueva_no_cambia_nada_mientras_este_cerrada():
    """
    Hasta que la prima se calibre, `value_candidate` tiene que
    contestar exactamente lo que contestaba el 21/08. Una via
    nueva no puede mover decisiones antes de estar medida.
    """

    from src.analysis.acquisition_valuation import (
        build_valuation_context,
        value_candidate,
    )

    jugador = {
        "id": 900,
        "name": "El que no sube",
        "position": 3,
        "price": 3_000_000,
        "priceIncrement": 0,
        "points": 10,
        "pointsLastSeason": 10,
        "status": "ok",
        "teamID": 1,
    }

    snapshot = {
        "my_team": [],
        "catalog": {"data": {"players": {}}},
        "market": {"offers": [], "sales": []},
    }

    contexto = build_valuation_context(
        snapshot,
        velocity_lookup={},
        starter_lookup={},
        computer_premium={
            "available": True,
            "calibrated": False,
            "median_percent": 2.0,
        },
    )

    valoracion = value_candidate(jugador, contexto)

    assert valoracion["value"] == 0
    assert valoracion["decision"] == "SIN_VALOR"

    assert (
        valoracion.get("as_computer_resale", {}).get("decision")
        == "PRIMA_SIN_MEDIR"
    ), "la via nueva no esta diciendo por que no contesta"


def test_con_la_prima_calibrada_la_via_se_abre_sola():
    """
    Y cuando haya muestras suficientes, se enciende sin tocar
    nada. Es el mismo patron que la curva de primas.
    """

    from src.analysis.acquisition_valuation import (
        build_valuation_context,
        value_candidate,
    )

    jugador = {
        "id": 900,
        "name": "El que no sube",
        "position": 3,
        "price": 3_000_000,
        "priceIncrement": 0,
        "points": 10,
        "pointsLastSeason": 10,
        "status": "ok",
        "teamID": 1,
    }

    snapshot = {
        "my_team": [],
        "catalog": {"data": {"players": {}}},
        "market": {"offers": [], "sales": []},
    }

    contexto = build_valuation_context(
        snapshot,
        velocity_lookup={},
        starter_lookup={},
        computer_premium={
            "available": True,
            "calibrated": True,
            "median_percent": 3.0,
        },
    )

    valoracion = value_candidate(jugador, contexto)

    assert valoracion["value"] > 3_000_000, (
        "con la prima calibrada, un jugador que no sube de precio "
        "sigue sin valer nada: la via nueva no se ha enchufado"
    )

    assert valoracion["intent"] == "SPECULATION"
    assert valoracion["route"] == "COMPUTER_RESALE"


def test_la_via_se_ve_apagada_en_la_pantalla():
    """
    Una via de ingresos apagada tiene que verse apagada. Si no,
    parece que Pepe la descarta cuando lo que pasa es que todavia
    no la sabe medir. Es la clase de fallo que ya ha aparecido
    doce veces: el dato existe y nadie lo enseña.
    """

    from pathlib import Path as _Path

    dashboard = _Path(__file__).parents[2] / "dashboard-v8" / "src"

    for ruta in (
        dashboard / "pages" / "MarketPage.jsx",
        dashboard / "pages" / "BrainPage.jsx",
    ):
        fuente = ruta.read_text(encoding="utf-8")

        assert "computer_premium" in fuente, (
            f"{ruta.name} no dice si la reventa al Computer esta "
            f"medida o apagada"
        )


def main():

    pruebas = [
        test_se_mide_contra_el_precio_de_aquel_momento,
        test_lo_que_no_se_puede_fechar_no_cuenta,
        test_con_pocas_muestras_no_se_compra_nada,
        test_ausencia_de_prima_no_es_prima_cero,
        test_un_traspaso_entre_managers_no_es_una_venta_al_computer,
        test_un_hecho_repetido_no_pesa_doble,
        test_las_barbaridades_se_descartan,
        test_sin_prima_medida_no_hay_valor,
        test_con_prima_medida_se_paga_por_debajo_de_la_reventa,
        test_una_prima_que_no_deja_margen_no_abre_la_via,
        test_un_precio_roto_no_produce_una_compra,
        test_la_via_nueva_no_cambia_nada_mientras_este_cerrada,
        test_con_la_prima_calibrada_la_via_se_abre_sola,
        test_la_via_se_ve_apagada_en_la_pantalla,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Reventa al Computer: todo en verde.")


if __name__ == "__main__":
    main()
