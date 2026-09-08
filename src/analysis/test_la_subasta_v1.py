"""
La subasta: varios a la vez, y el seguro pagado con la ganancia.

SINTOMA (10/09/2026)

    El libro de pujas tiene UNA puja registrada en toda la vida
    de Pepe. Las pujas se resuelven en el reset de las 07:00 y la
    ultima vuelta antes del cierre caia a 53 minutos.

CAUSA — TRES, Y NINGUNA ES EL LISTON

    1. El ciclo pone como mucho UNA accion por vuelta, tambien
       en la ventana del reset, que es cuando hay que poner
       varias.

    2. Las barandillas se miraban una puja a la vez. Cuatro
       pujas que por separado no concentran nada pueden dejar
       medio patrimonio en un club si entran las cuatro.

    3. El desvio de puja era el 0,5 % DEL PRECIO. Medido sobre
       las 16 compras del tablon que se llevaron sin rival y
       venian subiendo, eso es el 52 % (mediana) de lo que el
       jugador sube en un dia, y hasta el 127 %. El seguro se
       comia el negocio.

CONSECUENCIA

    Ningun umbral estaba mal. Lo que cambia es CUANDO y
    CUANTAS, no CUANTO.

LO QUE SE PROTEGE AQUI

    1. Que la ventana se abra solo cerca del reset.
    2. Que no se pujen mas jugadores que fichas libres.
    3. Que el tope salga de una cuenta -lo que se deshace
       aunque el mercado caiga un 5 %- y no de un numero.
    4. Que las barandillas se miren sobre el PEOR CASO.
    5. Que el desvio cueste una fraccion de la ganancia, y que
       no se quede en nada.
    6. Que nada de esto ejecute nada.

    Fixture entero. Ni reloj, ni disco, ni red: los segundos que
    faltan para el reset se PASAN.
"""

from __future__ import annotations

from src.analysis.bid_jitter import (
    JITTER_DE_LA_GANANCIA,
    JITTER_PERCENT,
    MIN_JITTER,
    apply_bid_jitter,
    jitter_ceiling,
)

from src.analysis.la_subasta import (
    CAIDA_QUE_HAY_QUE_AGUANTAR,
    VENTANA_MINUTOS,
    elegir_la_cesta,
    para_la_pantalla,
    peor_caso,
    tope_de_la_ventana,
    ventana_abierta,
)


# ============================================================
# EL FIXTURE: CUATRO CANDIDATOS DE UN RESET
# ============================================================
#
# Precios y subidas del orden de los medidos en el tablon: los
# que se llevan sin rival tienen precio mediano 4.550.000 y
# suben 30.000 al dia.


def _candidato(
    identificador,
    nombre,
    precio,
    puja,
    ganancia,
    club=1,
):
    return {
        "id": identificador,
        "name": nombre,
        "market_price": precio,
        "bid": puja,
        "expected_value": ganancia,
        "team_id": club,
    }


# Ordenados a proposito de peor a mejor por euro, para que el
# orden de la cesta no pueda salir bien por casualidad.
CUATRO = [
    _candidato(1, "El caro y flojo", 4_000_000, 4_100_000,
               41_000, club=10),
    _candidato(2, "El mediano", 2_000_000, 2_050_000,
               61_500, club=11),
    _candidato(3, "El barato y bueno", 400_000, 410_000,
               41_000, club=12),
    _candidato(4, "El del mismo club", 500_000, 510_000,
               30_600, club=12),
]


PLANTILLA = [
    {"id": 900 + n, "team_id": 12} for n in range(2)
]


# ============================================================
# LA VENTANA
# ============================================================


def test_la_ventana_solo_se_abre_cerca_del_reset():
    """
    El resto del dia, una accion por vuelta como siempre. Abrir
    la puja multiple a las cuatro de la tarde seria cambiar el
    comportamiento del ciclo entero por una idea que solo aplica
    al reset.
    """

    lejos = ventana_abierta(6 * 3600)

    assert not lejos["abierta"], lejos["reason"]

    cerca = ventana_abierta(5 * 60)

    assert cerca["abierta"], cerca["reason"]
    assert cerca["minutes_to_reset"] == 5.0


def test_la_ventana_no_lee_el_reloj():
    """
    REGLA 23. Los segundos que faltan se PASAN: los publica
    `market_clock`. Si esto leyera la hora, la guardia
    dependeria de cuando se ejecute.
    """

    import ast

    from pathlib import Path

    fuente = (
        Path(__file__).parent / "la_subasta.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Call):
            continue

        nombre = getattr(nodo.func, "attr", None)

        assert nombre not in {"now", "today", "utcnow"}, (
            f"la subasta lee el reloj en la linea {nodo.lineno}"
        )


def test_sin_saber_cuando_es_el_reset_no_se_abre():
    """
    Con el reloj del mercado roto, la ventana cerrada. Abrirla
    a ciegas seria poner varias pujas sin saber si faltan cinco
    minutos o seis horas.
    """

    ciega = ventana_abierta(None)

    assert not ciega["abierta"]
    assert ciega["reason"]


# ============================================================
# EL TOPE, QUE SALE DE UNA CUENTA
# ============================================================


def test_el_tope_sale_de_la_caida_que_hay_que_aguantar():
    """
    REGLA 18: ningun umbral sin numero detras.

    El tope no es una cifra elegida: es `caja / caida`. Con
    200.000 de caja y una caida del 5 %, se pueden comprometer
    4.000.000 — porque si el mercado cae, deshacerlo cuesta
    200.000 y esos los hay.
    """

    limite = tope_de_la_ventana(
        caja_libre=200_000, presupuesto=10_000_000
    )

    assert limite["por_la_caida"] == 4_000_000, (
        f"la cuenta da {limite['por_la_caida']}"
    )

    assert limite["tope"] == 4_000_000
    assert limite["manda"] == "CAIDA_DEL_MERCADO"


def test_el_presupuesto_puede_mandar_sobre_la_caida():
    """
    Con caja de sobra manda el bolsillo, que es lo que hay.
    """

    limite = tope_de_la_ventana(
        caja_libre=5_000_000, presupuesto=1_000_000
    )

    assert limite["tope"] == 1_000_000
    assert limite["manda"] == "PRESUPUESTO"


def test_la_caida_que_se_aguanta_es_el_cinco_por_ciento():
    """El numero del encargo, escrito y con nombre."""

    assert CAIDA_QUE_HAY_QUE_AGUANTAR == 0.05


# ============================================================
# LA CESTA
# ============================================================


def test_se_ordena_por_ganancia_POR_EURO():
    """
    LA REGLA DEL BLOQUE 2.

    Con dinero limitado no importa cual gana mas, sino cual gana
    mas por euro inmovilizado. «El barato y bueno» gana 41.000
    igual que «el caro y flojo», pero con la decima parte del
    dinero.
    """

    cesta = elegir_la_cesta(
        CUATRO,
        presupuesto=10_000_000,
        fichas_libres=1,
        caja_libre=5_000_000,
    )

    assert cesta["available"], cesta["reason"]

    assert len(cesta["elegidos"]) == 1

    assert cesta["elegidos"][0]["name"] == "El barato y bueno", (
        f"con una sola ficha se eligio "
        f"{cesta['elegidos'][0]['name']}: no se esta ordenando "
        f"por euro comprometido"
    )


def test_nunca_mas_pujas_que_fichas_libres():
    """
    Ganar mas jugadores de los que caben no se ha podido
    comprobar sin arriesgar (bloque 0.3), asi que el tope es el
    numero de huecos. Es lo seguro.
    """

    for huecos in (0, 1, 2, 3):

        cesta = elegir_la_cesta(
            CUATRO,
            presupuesto=10_000_000,
            fichas_libres=huecos,
            caja_libre=5_000_000,
        )

        assert len(cesta["elegidos"]) <= huecos, (
            f"con {huecos} fichas libres se pujaria por "
            f"{len(cesta['elegidos'])}"
        )


def test_sin_fichas_libres_no_se_puja_por_nadie():
    """
    Y se dice por que, en vez de devolver una lista vacia muda.
    """

    cesta = elegir_la_cesta(
        CUATRO,
        presupuesto=10_000_000,
        fichas_libres=0,
        caja_libre=5_000_000,
    )

    assert cesta["available"]
    assert not cesta["elegidos"]
    assert "ficha" in cesta["reason"].lower()


def test_el_tope_de_la_ventana_corta_la_cesta():
    """
    La suma de las pujas no puede pasar del tope, aunque queden
    fichas. Es la barandilla que impide varias posiciones en
    rojo a la vez con el viernes encima.
    """

    cesta = elegir_la_cesta(
        CUATRO,
        presupuesto=10_000_000,
        fichas_libres=4,

        # 50.000 de caja -> tope 1.000.000
        caja_libre=50_000,
    )

    assert cesta["comprometido"] <= 1_000_000, (
        f"se comprometen {cesta['comprometido']} y el tope era "
        f"1.000.000"
    )

    assert any(
        "tope" in (d.get("motivo") or "")
        for d in cesta["descartados"]
    ), "nadie fue descartado por el tope y deberia"


def test_el_cuatro_por_club_se_mira_sobre_la_cesta_entera():
    """
    LA MITAD QUE IMPORTA DEL BLOQUE 2.

    Dos pujas que por separado no concentran nada dejan dos del
    mismo club si entran las dos. Se comprueba el conjunto, no
    cada puja.
    """

    cesta = elegir_la_cesta(
        CUATRO,
        presupuesto=10_000_000,
        fichas_libres=4,
        caja_libre=5_000_000,
        max_por_club=1,
    )

    clubes = [c["team_id"] for c in cesta["elegidos"]]

    assert len(clubes) == len(set(clubes)), (
        f"la cesta lleva dos del mismo club: {clubes}"
    )

    assert any(
        "club" in (d.get("motivo") or "")
        for d in cesta["descartados"]
    )


def test_el_peor_caso_es_que_se_ganen_todas():
    """
    Mirar las barandillas una a una es como comprobar que cada
    bala pesa poco. Se mira la plantilla RESULTANTE.
    """

    cesta = elegir_la_cesta(
        CUATRO,
        presupuesto=10_000_000,
        fichas_libres=4,
        caja_libre=5_000_000,
    )

    peor = peor_caso(cesta, PLANTILLA)

    assert peor["available"], peor["reason"]

    assert peor["jugadores"] == len(PLANTILLA) + len(
        cesta["elegidos"]
    )

    # El club 12 ya tenia dos en la plantilla; la cesta le suma.
    assert peor["por_club"][12] > peor["por_club_antes"][12], (
        "el peor caso no esta sumando la cesta a la plantilla"
    )


def test_un_candidato_sin_ganancia_no_entra():
    """
    Pujar por algo que no se espera que gane nada es inmovilizar
    dinero a cambio de nada.
    """

    cesta = elegir_la_cesta(
        [
            _candidato(9, "Sin ganancia", 100_000, 110_000, 0),
            _candidato(8, "Sin puja", 100_000, 0, 50_000),
        ],
        presupuesto=10_000_000,
        fichas_libres=4,
        caja_libre=5_000_000,
    )

    assert not cesta["elegidos"], cesta["elegidos"]


# ============================================================
# EL DESVIO, PAGADO CON LA GANANCIA
# ============================================================


def test_el_desvio_lo_paga_la_ganancia_y_no_el_precio():
    """
    LA GUARDIA DEL BLOQUE 3.

    Un jugador de 4.550.000 que sube 30.000 al dia gana 90.000
    en el horizonte de tres dias de la casa.

        antes: 0,5 % del precio        = 22.750
        ahora: 10 % de la ganancia     =  9.000

    22.750 sobre 90.000 es una cuarta parte del negocio en
    seguro.
    """

    precio = 4_550_000
    ganancia = 90_000

    antes = jitter_ceiling(precio)
    ahora = jitter_ceiling(precio, ganancia)

    assert antes == int(precio * JITTER_PERCENT)

    assert ahora == int(ganancia * JITTER_DE_LA_GANANCIA)

    assert ahora < antes, (
        f"el desvio no ha bajado: {ahora} contra {antes}"
    )


def test_el_desvio_no_se_queda_en_nada():
    """
    EL OTRO LADO DEL ENCARGO.

    Si el desvio se hace diminuto volvemos a ser predecibles:
    la curva de primas se publica en `status.json`, asi que
    cualquiera enumera nuestras pujas candidatas y se pone unos
    euros encima.

    El suelo es `MIN_JITTER` y no baja de ahi ni con ganancia
    cero.
    """

    for ganancia in (0, 1, 100, 5_000):

        tope = jitter_ceiling(1_000_000, ganancia)

        assert tope >= MIN_JITTER, (
            f"con ganancia {ganancia} el desvio se queda en "
            f"{tope}: volvemos a ser predecibles"
        )


def test_la_ganancia_solo_puede_APRETAR_el_desvio():
    """
    El tope del precio sigue siendo el limite absoluto. Una
    ganancia enorme no puede aflojar el seguro por encima de lo
    que ya valia.
    """

    precio = 1_000_000

    por_el_precio = jitter_ceiling(precio)

    con_ganancia_enorme = jitter_ceiling(precio, 100_000_000)

    assert con_ganancia_enorme <= por_el_precio, (
        f"la ganancia ha AFLOJADO el desvio: "
        f"{con_ganancia_enorme} contra {por_el_precio}"
    )


def test_sin_ganancia_el_desvio_es_el_de_siempre():
    """
    Ninguna vía que no publique ganancia esperada cambia de
    comportamiento. Es la regla de la casa: lo que no se mide no
    se toca.
    """

    for precio in (100_000, 1_000_000, 20_000_000):

        assert jitter_ceiling(precio, None) == jitter_ceiling(
            precio
        )

        assert jitter_ceiling(precio, 0) == jitter_ceiling(
            precio
        )


def test_se_publica_lo_que_costo_el_seguro():
    """
    En euros ya se publicaba. Ahora tambien contra lo que
    aseguraba, que es la unica forma de saber si es caro.
    """

    resultado = apply_bid_jitter(
        4_600_000,
        4_550_000,
        ceiling=6_000_000,
        player_id=123,
        matchday=5,
        expected_gain=90_000,
    )

    assert "jitter_percent_of_gain" in resultado

    assert resultado["jitter_percent_of_gain"] is not None

    assert resultado["jitter"] <= int(
        90_000 * JITTER_DE_LA_GANANCIA
    ), "el desvio se ha pasado del tope de la ganancia"


# ============================================================
# QUE SE VEA, Y QUE NO EJECUTE
# ============================================================


def test_la_pantalla_lo_dice_todo_antes_del_reset():
    """
    EL BLOQUE 4. "No veo pujas para ganar algun jugador, ni en
    estrategia pone «espero a cinco minutos antes del reset»".
    """

    cesta = elegir_la_cesta(
        CUATRO,
        presupuesto=10_000_000,
        fichas_libres=3,
        caja_libre=5_000_000,
    )

    pantalla = para_la_pantalla(
        cesta, ventana_abierta(5 * 60)
    )

    for clave in (
        "bids",
        "committed",
        "slots_used",
        "slots_free",
        "expected_gain",
        "window",
        "last_reset",
    ):
        assert clave in pantalla, f"falta «{clave}»"

    assert pantalla["window"]["minutes_to_reset"] == 5.0

    assert pantalla["bids"], "no se enseña por quien se pujaria"

    for puja in pantalla["bids"]:
        for clave in ("name", "bid", "expected_value"):
            assert clave in puja


def test_esto_no_ejecuta_nada():
    """
    FASE OBSERVADOR. `enabled` sale False a proposito: el primer
    reset de verdad se mira con los numeros delante.
    """

    pantalla = para_la_pantalla(
        elegir_la_cesta(
            CUATRO,
            presupuesto=10_000_000,
            fichas_libres=3,
            caja_libre=5_000_000,
        ),
        ventana_abierta(5 * 60),
    )

    assert pantalla["enabled"] is False
    assert pantalla["observer_only"] is True


def test_la_forma_no_cambia_con_los_datos():
    """
    LA REGLA DEL 17/09. Con candidatos y sin ellos, las mismas
    claves.
    """

    con = elegir_la_cesta(
        CUATRO, 10_000_000, 3, caja_libre=5_000_000
    )

    sin = elegir_la_cesta([], 0, 0, caja_libre=0)

    assert set(con) == set(sin), set(con) ^ set(sin)

    assert set(para_la_pantalla(con, None)) == set(
        para_la_pantalla(sin, None)
    )

    assert set(ventana_abierta(60)) == set(
        ventana_abierta(None)
    )

    assert set(tope_de_la_ventana(1, 1)) == set(
        tope_de_la_ventana(None, None)
    )


def test_nada_de_esto_lanza():
    """
    Si la subasta revienta, revienta la ventana en que hay que
    actuar.
    """

    basura = [None, "no", 12345, [None], [{"bid": "x"}]]

    for datos in basura:

        cesta = elegir_la_cesta(datos, 1_000, 2, caja_libre=1)

        assert isinstance(cesta, dict)
        assert "elegidos" in cesta

        assert isinstance(peor_caso(cesta, datos), dict)

        assert isinstance(
            para_la_pantalla(cesta, None), dict
        )

    for segundos in (None, "x", -5, 0):
        assert isinstance(ventana_abierta(segundos), dict)


def test_la_ventana_aguanta_un_cron_que_llega_tarde():
    """
    El cron de Actions se retrasa con frecuencia. Una ventana de
    cinco minutos se pierde entera con un retraso normal; por eso
    son quince.
    """

    assert VENTANA_MINUTOS >= 10, (
        f"la ventana son {VENTANA_MINUTOS} min y un retraso "
        f"normal de Actions se la come entera"
    )


def test_estas_guardias_no_leen_el_estado():
    """
    REGLA 23. Ni disco, ni red, ni reloj.
    """

    import ast

    from pathlib import Path

    from src.analysis.test_verja_determinista_v1 import (
        _docstrings,
    )

    fuente = Path(__file__).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    fuera = _docstrings(arbol)

    prohibido = "dat" + "a/"

    for nodo in ast.walk(arbol):

        if id(nodo) in fuera:
            continue

        if isinstance(nodo, ast.Constant) and isinstance(
            nodo.value, str
        ):
            assert prohibido not in nodo.value, nodo.value


TESTS = [
    test_la_ventana_solo_se_abre_cerca_del_reset,
    test_la_ventana_no_lee_el_reloj,
    test_sin_saber_cuando_es_el_reset_no_se_abre,
    test_el_tope_sale_de_la_caida_que_hay_que_aguantar,
    test_el_presupuesto_puede_mandar_sobre_la_caida,
    test_la_caida_que_se_aguanta_es_el_cinco_por_ciento,
    test_se_ordena_por_ganancia_POR_EURO,
    test_nunca_mas_pujas_que_fichas_libres,
    test_sin_fichas_libres_no_se_puja_por_nadie,
    test_el_tope_de_la_ventana_corta_la_cesta,
    test_el_cuatro_por_club_se_mira_sobre_la_cesta_entera,
    test_el_peor_caso_es_que_se_ganen_todas,
    test_un_candidato_sin_ganancia_no_entra,
    test_el_desvio_lo_paga_la_ganancia_y_no_el_precio,
    test_el_desvio_no_se_queda_en_nada,
    test_la_ganancia_solo_puede_APRETAR_el_desvio,
    test_sin_ganancia_el_desvio_es_el_de_siempre,
    test_se_publica_lo_que_costo_el_seguro,
    test_la_pantalla_lo_dice_todo_antes_del_reset,
    test_esto_no_ejecuta_nada,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
    test_la_ventana_aguanta_un_cron_que_llega_tarde,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA SUBASTA V1")
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
