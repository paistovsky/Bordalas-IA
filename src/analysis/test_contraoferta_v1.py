"""
Una contraoferta no es una puja. Es lo contrario.

EL CASO (23/08/2026)

    "A Andrés Castrín ya le tengo y dice que está en el mercado y
     que ha pujado por él??"

    En el tablero, su propio jugador -publicado por el, con tres
    ofertas encima- salia marcado PUJA PUESTA por 1.190.038 EUR. Y
    la cabecera decia "2 PUJAS VIVAS · 1.61M comprometidos"
    mientras Biwenger, en la misma pantalla, decia **1 puja**.

    Lo dedujo el solo:

        "Osea que Pollo17 ha ofertado y Pepe le ha hecho una
         contraoferta, no? Debería aparecer como CONTRAOFERTA."

    Exacto. Medido contra Biwenger ese dia:

        type=purchase      from=Pollo17  to=YO    977.000  pide 38072
        type=counterOffer  from=YO  to=Pollo17  1.190.038  pide 38072
        type=purchase      from=YO  to=null       424.350  pide 37726

    Solo la tercera es una puja nuestra.

POR QUE PASABA

    El contador miraba `from == nosotros`. Y una contraoferta la
    hacemos nosotros: pasaba el filtro con todas las de la ley.

POR QUE NO ERA SOLO UNA ETIQUETA

    Estaba del REVES. Este contador responde a "cuanto dinero mio
    esta comprometido y ya no puedo gastar". Una contraoferta es
    dinero que ENTRA si la aceptan.

    Contarla como compromiso le quito 1.190.038 EUR al presupuesto
    de fichar -de 2,98 M a 1,37 M- por una operacion que, si sale
    bien, se lo suma. De ahi la fila de SUPERA_PRESUPUESTO.

LO QUE SE PROTEGE AQUI

    1. Que una contraoferta no cuente como dinero comprometido.
    2. Que una puja de verdad SI siga contando: quitar de mas aqui
       es dejar que se pueda gastar dos veces el mismo euro.
    3. Que las ofertas RECIBIDAS sigan sin contar, vengan del
       Computer -`from: null`- o de un manager.
    4. Que no se tire el dato: hay una negociacion abierta por un
       jugador nuestro, y por cuanto.
    5. Que si Biwenger renombra `counterOffer`, la segunda guarda
       lo siga cazando: por un jugador que ya es nuestro no se
       puja.
"""

from __future__ import annotations

from src.analysis.bid_exposure_engine import (
    COUNTER_OFFER_TYPES,
    OUR_BID_TYPES,
    apply_exposure_to_budget,
    build_bid_exposure,
)


YO = 14175949
POLLO17 = 14145555

CASTRIN = 38072      # nuestro, publicado
ORIOL_REY = 37726    # del Computer, con puja nuestra

MI_PLANTILLA = [
    17482, 37525, 9983, 2169, 8376, CASTRIN,
    14800, 41606, 41271, 29661, 39874, 26271, 3159,
]


def oferta(**campos):
    base = {
        "id": 1,
        "type": "purchase",
        "status": "waiting",
        "amount": 100_000,
        "from": None,
        "to": {"id": YO},
        "requestedPlayers": [CASTRIN],
    }
    base.update(campos)
    return base


# El mercado real del 23/08, reducido a lo que importa.
LA_OFERTA_DE_POLLO = oferta(
    id=220381407,
    amount=977_000,
    **{"from": {"id": POLLO17, "name": "Pollo17"}},
)

NUESTRA_CONTRAOFERTA = oferta(
    id=3044109752,
    type="counterOffer",
    amount=1_190_038,
    **{"from": {"id": YO}},
    to={"id": POLLO17, "name": "Pollo17"},
)

NUESTRA_PUJA = oferta(
    id=3615879887,
    amount=424_350,
    **{"from": {"id": YO}},
    to=None,
    requestedPlayers=[ORIOL_REY],
)

DEL_COMPUTER = oferta(id=1078452865, amount=981_800)


def snapshot(ofertas, con_plantilla=True):
    return {
        "league": {"user": {"id": YO}},
        "my_team": (
            [{"id": i} for i in MI_PLANTILLA]
            if con_plantilla
            else []
        ),
        "market": {"offers": list(ofertas)},
    }


TODAS = [
    LA_OFERTA_DE_POLLO,
    NUESTRA_CONTRAOFERTA,
    NUESTRA_PUJA,
    DEL_COMPUTER,
]


# ============================================================
# PRUEBAS
# ============================================================


def test_el_caso_castrin():
    """
    El mercado entero del 23/08: una puja de verdad y nada mas.
    """

    e = build_bid_exposure(snapshot(TODAS))

    assert e["operation_count"] == 1, (
        f"Biwenger dice 1 puja y aqui salen "
        f"{e['operation_count']}"
    )

    assert e["committed_total"] == 424_350, (
        f"se estan comprometiendo {e['committed_total']:,} EUR "
        f"cuando solo hay una puja de 424.350"
    )

    assert e["operations"][0]["player_ids"] == [ORIOL_REY]


def test_la_contraoferta_no_se_tira_pero_no_compromete():
    """
    Es informacion buena: hay una negociacion abierta por un
    jugador nuestro. Lo que no es, es dinero comprometido.
    """

    e = build_bid_exposure(snapshot(TODAS))

    assert e["counter_offer_count"] == 1
    assert e["counter_offer_total"] == 1_190_038

    contra = e["counter_offers"][0]

    assert contra["player_ids"] == [CASTRIN]
    assert contra["counterparty_name"] == "Pollo17"

    assert "COBRAR" in e["reason"], (
        "la pantalla no dice que ese dinero entra, no sale"
    )


def test_una_puja_de_verdad_sigue_contando():
    """
    EL RIESGO DE PASARSE.

    Quitar de mas aqui es peor que el fallo original: dejaria
    gastar dos veces el mismo euro.
    """

    e = build_bid_exposure(snapshot([NUESTRA_PUJA]))

    assert e["committed_total"] == 424_350
    assert e["operation_count"] == 1


def test_las_ofertas_recibidas_siguen_sin_contar():
    """
    Vengan del Computer -`from: null`- o de un manager. Ni antes
    ni ahora son dinero nuestro.
    """

    e = build_bid_exposure(
        snapshot([LA_OFERTA_DE_POLLO, DEL_COMPUTER])
    )

    assert e["committed_total"] == 0
    assert e["operation_count"] == 0
    assert e["counter_offer_count"] == 0


def test_por_un_jugador_nuestro_no_se_puja():
    """
    LA SEGUNDA GUARDA.

    Si Biwenger renombra `counterOffer` algun dia, esto lo sigue
    cazando: la oferta pide un jugador que ya esta en nuestra
    plantilla.
    """

    disfrazada = dict(NUESTRA_CONTRAOFERTA)
    disfrazada["type"] = "purchase"

    e = build_bid_exposure(snapshot([disfrazada, NUESTRA_PUJA]))

    assert e["committed_total"] == 424_350, (
        "una contraoferta con otro nombre ha vuelto a contar como "
        "dinero comprometido"
    )
    assert e["counter_offer_count"] == 1


def test_sin_plantilla_manda_el_tipo():
    """
    La segunda guarda necesita saber quienes son nuestros. Cuando
    no se sabe, el tipo tiene que bastar: no puede quedarse el
    contador sin ninguna defensa.
    """

    e = build_bid_exposure(
        snapshot(TODAS, con_plantilla=False)
    )

    assert e["committed_total"] == 424_350
    assert e["counter_offer_count"] == 1


def test_un_tipo_desconocido_no_se_da_por_puja():
    """
    Ausencia de dato != dato. Si aparece un tipo que no conocemos,
    no se cuenta como dinero comprometido hasta saber que es.
    """

    raro = oferta(
        id=999,
        type="loanOffer",
        amount=5_000_000,
        **{"from": {"id": YO}},
        to=None,
        requestedPlayers=[999999],
    )

    e = build_bid_exposure(snapshot([raro, NUESTRA_PUJA]))

    assert e["committed_total"] == 424_350


def test_el_presupuesto_deja_de_estar_recortado():
    """
    EL EFECTO EN EUROS.

    Con la contraoferta contando, a Pepe le quedaban 1,37 M de los
    2,98 M que tenia para fichar. Por eso media tabla salia
    SUPERA_PRESUPUESTO.
    """

    presupuesto = {
        "total_budget": 2_980_000,
        "gross_budget": 2_980_000,
        "maximum_bid": 9_520_000,
    }

    resultado = apply_exposure_to_budget(
        presupuesto,
        build_bid_exposure(snapshot(TODAS)),
    )

    assert resultado["available_budget"] == 2_555_650, (
        f"quedan {resultado['available_budget']:,} y deberian "
        f"quedar 2.555.650: 2,98 M menos la unica puja real"
    )


def test_el_tablero_lo_llama_contraoferta():
    """
    "Debería aparecer como CONTRAOFERTA o algo así."

    No es lo mismo que una puja y no puede leerse igual.
    """

    from src.analysis.acquisition_board import (
        build_acquisition_board,
    )

    ficha = {
        "id": CASTRIN,
        "name": "Andrés Castrín",
        "position": 2,
        "price": 940_000,
        "priceIncrement": 0,
        "points": 8,
        "pointsLastSeason": 97,
        "status": "ok",
        "teamID": 1,
    }

    datos = snapshot(TODAS)
    datos["catalog"] = {"data": {"players": {str(CASTRIN): ficha}}}
    datos["market"]["sales"] = [
        {
            "player": ficha,
            "price": 960_000,
            "user": {"id": YO, "name": "Pepe Bordalás"},
        }
    ]
    datos["my_team"] = [ficha]

    tablero = build_acquisition_board(
        snapshot=datos,
        rival_intelligence={},
        current_user_id=YO,
        available_budget=2_555_650,
    )

    assert tablero.get("available"), tablero.get("reason")

    fila = next(
        (f for f in tablero["targets"] if f["id"] == CASTRIN),
        None,
    )

    assert fila is not None, (
        "la contraoferta ha desaparecido de la pantalla"
    )

    assert fila["decision"] == "CONTRAOFERTA", (
        f"sigue leyendose como {fila['decision']}"
    )

    assert not fila["has_live_bid"], (
        "un jugador nuestro sigue marcado como PUJA PUESTA"
    )

    assert fila["counter_offer"]["amount"] == 1_190_038
    assert "cobrar" in (fila["reason"] or "").lower()


def test_los_tipos_estan_separados():

    assert "purchase" in OUR_BID_TYPES
    assert "counteroffer" not in OUR_BID_TYPES
    assert "counteroffer" in COUNTER_OFFER_TYPES


def main():

    pruebas = [
        test_el_caso_castrin,
        test_la_contraoferta_no_se_tira_pero_no_compromete,
        test_una_puja_de_verdad_sigue_contando,
        test_las_ofertas_recibidas_siguen_sin_contar,
        test_por_un_jugador_nuestro_no_se_puja,
        test_sin_plantilla_manda_el_tipo,
        test_un_tipo_desconocido_no_se_da_por_puja,
        test_el_presupuesto_deja_de_estar_recortado,
        test_el_tablero_lo_llama_contraoferta,
        test_los_tipos_estan_separados,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Contraofertas: todo en verde.")


if __name__ == "__main__":
    main()
