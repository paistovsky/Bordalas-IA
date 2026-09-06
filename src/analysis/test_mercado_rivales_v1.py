"""
El mercado de los rivales se ve, y no se compra.

SINTOMA (24/09/2026)

    El dueño pregunto cuantos jugadores se podian comprar y la
    pantalla contesto veinte. Eran cuarenta y siete: los otros
    veintisiete los vendian managers.

CAUSA

    Un filtro NUESTRO -no de Biwenger- los tiraba antes de
    crearles fila:

        if (fuera_del_computer
                and player_id not in puja_viva
                and player_id not in contra_oferta):
            continue

    Y como no habia fila, nadie les pedia nunca el ritmo ni la
    racha. Del 56 % del escaparate no se sabia nada, y "no se
    sabe" se leia en pantalla como "no hay".

CONSECUENCIA

    `outside_computer_market: 0` no significaba "no hay
    mercados de rivales". Significaba "no miramos". Es la misma
    familia que llevamos cinco arreglando: el dato existe, no
    llega a ninguna pantalla, y su ausencia se lee como un cero.

LO QUE SE PROTEGE AQUI

    1. Que entren: un jugador que vende un manager tiene fila.
    2. Que NO se compren: pase lo que pase, jamas BID. Ni
       aunque el ritmo sea espectacular y el dinero sobre.
       Comprarle a un manager es OFRECER, y la tasa de
       aceptacion no esta medida.
    3. Que se vea de quien es y cuanto pide.
    4. Que se publique lo que HABRIA decidido, que es el numero
       por el que se ha abierto esta puerta.
    5. Que el interruptor devuelva el mundo de antes.

    Fixture entero. Ni una lectura de `data/` ni de la red.
"""

from __future__ import annotations

import inspect

from pathlib import Path

from src.analysis import acquisition_valuation

from src.analysis.acquisition_board import (
    DISABLE_ENV,
    MERCADO_DE_RIVAL,
    build_acquisition_board,
    _mercado_de_rivales_visible,
)

from src.analysis.decision_orchestrator import (
    best_acquisition_target,
)


# ============================================================
# EL FIXTURE: EL MERCADO DEL 24/09, EN PEQUEÑO
# ============================================================
#
# Tres ventas y ni un byte de disco: una del Computer, una de un
# manager y una de un manager con dinero nuestro ya puesto. Las
# tres situaciones que el tablero tiene que distinguir.

YO = 14175949
LUISMI = 9990001

DEL_COMPUTER = 101
DE_LUISMI = 202
DE_LUISMI_CON_PUJA = 303

# Uno NUESTRO, publicado por nosotros. De las 61 ventas del
# tablon real, 14 son de esta clase.
NUESTRO = 404


def _ficha(player_id: int, nombre: str, precio: int) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "position": 3,
        "price": precio,
        "priceIncrement": 0,
        "points": 12,
        "pointsLastSeason": 80,
        "status": "ok",
        "teamID": 1,
    }


# Precios pequeños a proposito: el tope POR OPERACION de la via
# especulativa es un porcentaje del bolsillo, y con jugadores
# caros todo sale SUPERA_PRESUPUESTO -tambien los del Computer- y
# la guardia no probaria nada. Aqui interesa el caso en que el
# dinero SI llega, que es cuando la puerta tiene que aguantar.
FICHAS = {
    DEL_COMPUTER: _ficha(DEL_COMPUTER, "Del Computer", 400_000),
    DE_LUISMI: _ficha(DE_LUISMI, "André Almeida", 420_000),
    DE_LUISMI_CON_PUJA: _ficha(
        DE_LUISMI_CON_PUJA, "Ejuke", 450_000
    ),
    NUESTRO: _ficha(NUESTRO, "Mangala", 430_000),
}


# El ritmo que haria pujar a cualquiera: muy por encima del
# liston y con racha corta, que es la que la doctrina compra.
# Se INYECTA, no se lee: `build_market_rates()` sin argumento va
# al disco, y ninguna guardia puede depender de eso.
RITMO_QUE_SI = {
    "rate_percent_per_day": 6.0,
    "direction": "UP",
    "trend_days": 1,
    "demand_net": 40,
    "sources": 3,
    "agreement": "FULL",
}


RITMOS = {
    DEL_COMPUTER: dict(RITMO_QUE_SI),
    DE_LUISMI: dict(RITMO_QUE_SI),
    DE_LUISMI_CON_PUJA: dict(RITMO_QUE_SI),

    # A Mangala se le da el mismo ritmo estupendo a proposito: si
    # la exclusion se cae, saldra pujable y la guardia lo cantara.
    NUESTRO: dict(RITMO_QUE_SI),
}


def _venta(player_id: int, pedido: int, vendedor: dict) -> dict:
    return {
        "player": FICHAS[player_id],
        "price": pedido,
        "user": vendedor,
    }


LUISMI_HAZ = {"id": LUISMI, "name": "Luismi_Haz"}


def snapshot(con_mercado: bool = True) -> dict:
    """
    Un mercado completo, o uno vacio.

    El segundo existe para la regla de la forma estable: sin
    datos el tablero tiene que publicar las MISMAS claves.
    """

    ventas = (
        [
            _venta(DEL_COMPUTER, 400_000, None),
            _venta(DE_LUISMI, 390_000, LUISMI_HAZ),
            _venta(DE_LUISMI_CON_PUJA, 470_000, LUISMI_HAZ),
            _venta(NUESTRO, 480_000, {"id": YO, "name": "Pepe"}),
        ]
        if con_mercado
        else []
    )

    return {
        "league": {"user": {"id": YO}},
        "my_team": [],
        "catalog": {
            "data": {
                "players": {
                    str(k): v for k, v in FICHAS.items()
                }
            }
        },
        "market": {
            "sales": ventas,
            "offers": [],
            "status": {"balance": 5_000_000},
        },
    }


class _con_ritmos:
    """
    Los ritmos del fixture, sin tocar el disco.

    `build_market_rates()` sin informe lee `data/`. Aqui se
    sustituye por una funcion que devuelve el fixture, y se
    restaura al salir pase lo que pase.
    """

    def __init__(self, ritmos: dict | None):
        self.ritmos = ritmos
        self.original = None

    def __enter__(self):
        self.original = acquisition_valuation.build_market_rates
        acquisition_valuation.build_market_rates = (
            lambda *a, **k: dict(self.ritmos or {})
        )
        return self

    def __exit__(self, *_):
        acquisition_valuation.build_market_rates = self.original
        return False


class _interruptor:
    """`BORDALAS_SIN_MERCADO_RIVALES`, puesto y quitado."""

    def __init__(self, valor: str | None):
        self.valor = valor
        self.antes = None

    def __enter__(self):
        import os

        self.antes = os.environ.get(DISABLE_ENV)

        if self.valor is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = self.valor

        return self

    def __exit__(self, *_):
        import os

        if self.antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = self.antes

        return False


def _tablero(con_mercado: bool = True, ritmos=RITMOS) -> dict:
    with _con_ritmos(ritmos):
        return build_acquisition_board(
            snapshot=snapshot(con_mercado),
            rival_intelligence={},
            current_user_id=YO,
            available_budget=4_000_000,
            acquisition_budget=4_000_000,
        )


def _fila(tablero: dict, player_id: int):
    return next(
        (
            f
            for f in (tablero.get("targets") or [])
            if f.get("id") == player_id
        ),
        None,
    )


# ============================================================
# PRUEBAS
# ============================================================


def test_el_del_rival_ya_tiene_fila():
    """
    LA PRUEBA DEL ENCARGO. Antes del 24/09 esta fila no existia
    y el dueño leia "veinte comprables" cuando eran mas.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, DE_LUISMI)

    assert fila is not None, (
        "el jugador que vende un manager sigue sin llegar a la "
        "tabla: el filtro no se ha levantado"
    )

    assert fila.get("rival_market") is True, (
        "la fila entra pero no se marca como mercado de rival: "
        "la pantalla no puede distinguirla del Computer"
    )


def test_jamas_se_compra_aunque_el_ritmo_sea_perfecto():
    """
    LA GUARDIA QUE IMPORTA.

    El fixture le da un ritmo del 6 % diario -el doble del
    liston- y cuatro millones de presupuesto sobre un jugador de
    1,18 M. Con el Computer eso es un BID inmediato.

    Aqui NO. Comprarle a un manager es ofrecer, y de la tasa de
    aceptacion tenemos UNA observacion.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, DE_LUISMI)

    assert fila["decision"] == MERCADO_DE_RIVAL, (
        f"un jugador de un manager ha salido con decision "
        f"{fila['decision']}: la compra a rivales esta abierta"
    )

    assert fila["decision"] != "BID"

    assert fila["bid"] == 0, (
        f"la fila lleva una puja de {fila['bid']} EUR sobre algo "
        f"que no se puede pujar"
    )


def test_ninguna_fila_de_rival_es_pujable_nunca():
    """
    La invariante, sobre la tabla entera y no sobre una fila.
    Una excepcion futura tiene que romper aqui.
    """

    with _interruptor(None):
        tablero = _tablero()

    culpables = [
        f["name"]
        for f in tablero["targets"]
        if f.get("rival_market") and f["decision"] == "BID"
    ]

    assert not culpables, (
        f"filas de rival marcadas como pujables: {culpables}"
    )


def test_el_ciclo_no_puede_elegir_uno_de_rival():
    """
    La puerta de verdad no es la pantalla: es que
    `best_acquisition_target` solo mira BID. Si algun dia deja de
    ser asi, esto lo canta antes de que Pepe ofrezca.
    """

    with _interruptor(None):
        tablero = _tablero()

    elegido = best_acquisition_target(tablero)

    if elegido is not None:
        assert not elegido.get("rival_market"), (
            f"el ciclo ha elegido a {elegido.get('name')}, que "
            f"lo vende un manager"
        )


def test_se_ve_quien_vende_y_cuanto_pide():
    """
    "Un rival" no informa de nada. De cada manager se sabe
    cuanto suele pagar, y eso cambia lo que esperas.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, DE_LUISMI)

    assert fila["seller_kind"] == "MANAGER"
    assert fila["seller_name"] == "Luismi_Haz", (
        f"el vendedor sale como {fila['seller_name']}"
    )

    assert fila["asking_price"] == 390_000, (
        f"lo que pide el vendedor no llega a la pantalla: "
        f"{fila.get('asking_price')}"
    )

    # El precio de mercado y lo pedido son dos numeros distintos,
    # y el hueco entre ellos es media conversacion.
    assert fila["asking_price"] != FICHAS[DE_LUISMI]["price"]


def test_se_publica_lo_que_habria_decidido():
    """
    El numero por el que se ha abierto esta puerta: cuantos
    pasarian el liston si se pudiera comprarlos. Sin esto, el
    paso 1 no contesta nada y no merece las noches.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, DE_LUISMI)

    assert "would_be_decision" in fila, (
        "la fila no dice que habria decidido"
    )

    assert "would_pass" in fila
    assert isinstance(fila["would_pass"], bool)

    assert fila["would_be_decision"] != MERCADO_DE_RIVAL, (
        "would_be_decision se ha escrito DESPUES de cerrar la "
        "puerta: guarda la decision cerrada en vez de la real"
    )

    resumen = tablero.get("rival_market") or {}

    for clave in (
        "shown",
        "would_pass",
        "sellers",
        "buying_closed",
        "visible",
    ):
        assert clave in resumen, (
            f"el resumen no publica «{clave}»"
        )

    assert resumen["buying_closed"] is True, (
        "el resumen dice que la compra a rivales esta abierta"
    )

    assert resumen["shown"] >= 1
    assert "Luismi_Haz" in resumen["sellers"]


def test_con_ritmo_bueno_al_menos_uno_pasaria():
    """
    Que el contador cuente de verdad. Con un 6 % diario servido
    en el fixture, `would_pass` no puede salir cero: si lo hace,
    el numero que decide el resto del plan seria un cero falso.
    """

    with _interruptor(None):
        tablero = _tablero()

    resumen = tablero["rival_market"]

    assert resumen["would_pass"] >= 1, (
        "con un ritmo del 6 % diario ninguno pasaria el liston: "
        "el contador no esta midiendo lo que dice medir"
    )

    # Y la mitad que lo demuestra: el del Computer, con el MISMO
    # ritmo y el mismo precio, si sale a pujar. Si este no fuese
    # BID, el cero de arriba no probaria nada sobre la puerta.
    del_computer = _fila(tablero, DEL_COMPUTER)

    assert del_computer["decision"] == "BID", (
        f"el jugador del Computer ha salido "
        f"{del_computer['decision']}: el fixture no llega a "
        f"pujar y la comparacion no vale"
    )


def test_sin_ritmo_no_pasa_ninguno():
    """
    Y que no cuente de mas. Sin ojeador, `would_pass` es cero y
    no un optimismo.
    """

    with _interruptor(None):
        tablero = _tablero(ritmos={})

    assert tablero["rival_market"]["would_pass"] == 0, (
        "sin ritmo medido siguen «pasando el liston»"
    )


def test_la_puja_viva_sigue_llamandose_como_antes():
    """
    Lo que YA tenia dinero nuestro dentro no cambia de nombre.
    Ese arreglo es del 18/08 y costo 463.500 EUR invisibles.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, DE_LUISMI_CON_PUJA)

    assert fila is not None

    # Sin puja en el fixture entra como mercado de rival, que es
    # lo correcto; lo que no puede es desaparecer.
    assert fila["decision"] in {
        MERCADO_DE_RIVAL,
        "PUJA_FUERA_DEL_COMPUTER",
    }, f"ha salido como {fila['decision']}"


def test_el_del_computer_no_ha_cambiado():
    """
    Abrir una puerta no puede tocar la que ya funcionaba. El
    jugador del Computer se sigue valorando igual.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, DEL_COMPUTER)

    assert fila is not None
    assert fila["seller_kind"] == "COMPUTER"
    assert not fila.get("rival_market")
    assert "would_be_decision" not in fila, (
        "un jugador del Computer lleva marca de rival"
    )


def test_el_interruptor_devuelve_el_mundo_de_antes():
    """
    Una linea y la tabla vuelve a ser el mercado del Computer.
    """

    with _interruptor("1"):
        assert not _mercado_de_rivales_visible()
        tablero = _tablero()

    assert _fila(tablero, DE_LUISMI) is None, (
        "con el interruptor puesto el mercado de rivales sigue "
        "entrando"
    )

    assert _fila(tablero, DEL_COMPUTER) is not None, (
        "el interruptor se ha llevado por delante el mercado del "
        "Computer"
    )

    assert tablero["rival_market"]["visible"] is False


def test_el_interruptor_esta_apagado_por_defecto():
    """
    Verlos es el comportamiento nuevo, y esta encendido. El
    interruptor es para apagarlo, no al reves.
    """

    with _interruptor(None):
        assert _mercado_de_rivales_visible()


def test_el_recorte_no_esconde_al_que_pasaria():
    """
    Las filas de rival nunca son BID, asi que el orden las manda
    al final: serian las primeras en caer por el recorte. Justo
    las unicas por las que se ha abierto la puerta.
    """

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert 'if f.get("would_pass") and f["id"] not in vistos' in fuente, (
        "el recorte puede volver a esconder al que pasaria el "
        "liston"
    )


def test_el_escaparate_dice_sus_dos_mitades():
    """
    "Cuantos hay a la venta" y "a cuantos se les puede comprar"
    son dos preguntas. La pantalla contestaba las dos con
    `market_size`, y por eso el dueño leyo veinte.
    """

    with _interruptor(None):
        tablero = _tablero()

    assert tablero["market_size"] == 1, (
        f"`market_size` ha dejado de ser solo el Computer: "
        f"{tablero['market_size']}"
    )

    assert tablero["buyable_universe"] >= tablero["market_size"], (
        "el universo comprable es menor que el mercado del "
        "Computer, que es imposible"
    )


def test_la_forma_no_cambia_con_los_datos():
    """
    LA REGLA DEL 17/09.

    Con mercado y sin mercado, las mismas claves. Un `KeyError`
    en produccion por una clave que solo existe los dias buenos
    es como se cayo la verja el 18/09.
    """

    with _interruptor(None):
        con = _tablero(con_mercado=True)
        sin = _tablero(con_mercado=False)

    if not sin.get("available"):
        # Sin mercado el tablero puede declararse no disponible,
        # y eso es legitimo: lo que no vale es media forma.
        assert "reason" in sin
        return

    faltan = set(con) - set(sin)

    assert not faltan, (
        f"claves que solo existen con datos: {sorted(faltan)}"
    )

    resumen_con = con.get("rival_market") or {}
    resumen_sin = sin.get("rival_market") or {}

    assert set(resumen_con) == set(resumen_sin), (
        f"el resumen del mercado de rivales cambia de forma: "
        f"{set(resumen_con) ^ set(resumen_sin)}"
    )


def test_nada_de_esto_lanza():
    """
    Un tablero que revienta detiene el ciclo entero.
    """

    basura = [
        {},
        {"market": None},
        {"market": {"sales": None}},
        {"market": {"sales": [None, {}, {"player": None}]}},
        {"catalog": {"data": {"players": None}}},
    ]

    with _interruptor(None):
        for datos in basura:
            resultado = build_acquisition_board(
                snapshot=datos,
                rival_intelligence={},
                current_user_id=YO,
                available_budget=None,
            )

            assert isinstance(resultado, dict)
            assert "available" in resultado


def test_la_puerta_se_cierra_despues_de_valorar():
    """
    El orden es la mitad del diseño: si la puerta se cerrase
    ANTES, `would_be_decision` seria siempre la decision cerrada
    y el numero del encargo no existiria.
    """

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    puerta = fuente.index('fila["would_be_decision"]')
    valoracion = fuente.index("plan = optimal_bid(")
    apilado = fuente.index("filas.append(fila)")

    assert valoracion < puerta < apilado, (
        "la puerta ya no esta entre la valoracion y el apilado: "
        "o se cierra antes de valorar o no se cierra"
    )


def test_estas_guardias_no_leen_el_estado():
    """
    LA REGLA DEL 18/09. `data/` es estado mutable, jamas un
    fixture. Y esta guardia inyecta los ritmos justamente para
    no caer en eso.
    """

    import ast

    from src.analysis.test_verja_determinista_v1 import (
        _docstrings,
    )

    fuente = Path(__file__).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    # Los docstrings quedan fuera, como en la guardia de la
    # verja: uno que EXPLICA el fallo no lo comete, y este lo
    # explica.
    fuera = _docstrings(arbol)

    prohibido = "dat" + "a/"

    for nodo in ast.walk(arbol):

        # `_docstrings` devuelve `id()` de nodos, no nodos.
        if id(nodo) in fuera:
            continue

        if isinstance(nodo, ast.Constant) and isinstance(
            nodo.value, str
        ):

            if prohibido in nodo.value:
                raise AssertionError(
                    f"esta guardia lee el estado: {nodo.value!r}"
                )


def test_el_interruptor_es_de_una_linea():
    """
    Como el resto de la casa: una variable de entorno, no un
    despliegue.
    """

    assert DISABLE_ENV == "BORDALAS_SIN_MERCADO_RIVALES"

    firma = inspect.signature(_mercado_de_rivales_visible)

    assert not firma.parameters, (
        "el interruptor ha dejado de leerse solo del entorno"
    )


def test_lo_nuestro_no_es_un_mercado_de_rival():
    """
    EL FALLO QUE CANTO LA SONDA (24/09/2026)

    De las 61 ventas del tablon, 14 son NUESTRAS. Al levantar el
    filtro entraron tambien, y Mangala -jugador de la casa,
    publicado por nosotros- salio con `would_pass: True`.

    Un "pasaria el liston" sobre algo que ya es tuyo hincha el
    unico numero por el que se ha abierto esta puerta.
    """

    with _interruptor(None):
        tablero = _tablero()

    fila = _fila(tablero, NUESTRO)

    if fila is not None:

        assert not fila.get("rival_market"), (
            "un jugador NUESTRO esta contado como mercado de "
            "rival"
        )

        assert not fila.get("would_pass"), (
            "un jugador NUESTRO cuenta como que «pasaria el "
            "liston»: el numero del encargo sale hinchado"
        )

    assert "Pepe" not in (
        tablero["rival_market"]["sellers"]
    ), (
        "salimos en la lista de vendedores rivales, que es "
        "contradictorio"
    )


def test_la_pantalla_lo_canta():
    """
    De nada sirve publicarlo si nadie lo pinta: ese es
    literalmente el fallo que se esta arreglando, un piso mas
    arriba. La cabecera tiene que separar las dos mitades del
    escaparate y la tabla tiene que saber pintar la decision
    nueva.
    """

    pagina = (
        Path(__file__).parent.parent.parent
        / "dashboard-v8"
        / "src"
        / "pages"
        / "MarketPage.jsx"
    )

    if not pagina.exists():
        # El repo puede venir sin el front en algunos entornos.
        return

    fuente = pagina.read_text(encoding="utf-8")

    assert "acquisition.rival_market" in fuente, (
        "la cabecera no lee el mercado de rivales: el escaparate "
        "vuelve a contarse con un solo numero"
    )

    assert "MERCADO_DE_RIVAL" in fuente, (
        "la tabla no sabe pintar la decision nueva y saldria en "
        "crudo"
    )

    assert "would_pass" in fuente, (
        "la pantalla no dice cuantos pasarian el liston, que es "
        "el numero del encargo"
    )


TESTS = [
    test_el_del_rival_ya_tiene_fila,
    test_jamas_se_compra_aunque_el_ritmo_sea_perfecto,
    test_ninguna_fila_de_rival_es_pujable_nunca,
    test_el_ciclo_no_puede_elegir_uno_de_rival,
    test_se_ve_quien_vende_y_cuanto_pide,
    test_se_publica_lo_que_habria_decidido,
    test_con_ritmo_bueno_al_menos_uno_pasaria,
    test_sin_ritmo_no_pasa_ninguno,
    test_la_puja_viva_sigue_llamandose_como_antes,
    test_el_del_computer_no_ha_cambiado,
    test_lo_nuestro_no_es_un_mercado_de_rival,
    test_el_interruptor_devuelve_el_mundo_de_antes,
    test_el_interruptor_esta_apagado_por_defecto,
    test_el_recorte_no_esconde_al_que_pasaria,
    test_el_escaparate_dice_sus_dos_mitades,
    test_la_pantalla_lo_canta,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
    test_la_puerta_se_cierra_despues_de_valorar,
    test_estas_guardias_no_leen_el_estado,
    test_el_interruptor_es_de_una_linea,
]


def main() -> None:

    print()
    print("=" * 60)
    print("MERCADO DE RIVALES V1")
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
