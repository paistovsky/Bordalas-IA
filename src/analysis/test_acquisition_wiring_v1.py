"""
Valor y puja conectados al mercado del Computer.

QUE SUSTITUYE
    La puja de los jugadores del Computer salia de una escalera
    fija de primas sobre el precio -+8/6/4/2 % segun el score-.
    Esa escalera no miraba ni lo que el jugador nos aportaba ni si
    alguien podia disputarnoslo.

    Ahora son dos preguntas separadas, las dos con datos:
    `acquisition_valuation` dice cuanto vale para nosotros y
    `rival_bid_model` dice cuanto pujar.

EL FILTRO QUE ERA UNA PUERTA
    Solo se valoraba a quien la escalera ya habia marcado como
    pujable -final_score >= 55-. Y ese filtro descartaba
    exactamente los chollos: el 16/08/2026 dejaba fuera a Copete
    (150.000 EUR, 56 puntos, score 40), a De Jong (score 50) y a
    Bartra (score 50).

    El score paso a ser una senal mas. La puerta es el valor.

LO QUE APARECIO AL ABRIRLA
    Copete y De Jong estan lesionados. Eran las dos mejores
    operaciones por valor puro, y el filtro de disponibilidad las
    para. Abrir la puerta obligaba a poner ese filtro, y por eso
    esta aqui con su test.

Ejecutar:
    python -m src.analysis.test_acquisition_wiring_v1
"""

import src.analysis.intelligent_bid_engine as motor

from src.analysis.intelligent_bid_engine import (
    calculate_intelligent_bids,
)


YO = 14175949

TENAGLIA = 41100
COPETE = 50001
YERAY = 2044
XIMO = 1877

PRECIO_TENAGLIA = 3_270_000
ESCALERA_TENAGLIA = 3_340_000


from src.analysis import (  # noqa: E402
    acquisition_valuation as valuation_mod,
    candidate_starter_lookup as starter_mod,
)


class _TitularidadNeutra(dict):
    """
    Un lookup que da a CUALQUIER jugador la misma señal.

    Importante en su probabilidad tipica: no es titular indiscutible
    ni suplente, y sobre todo es IGUAL para los dos lados de una
    sustitucion, con lo que ningun veto se dispara y lo que queda
    medido es el cableado.

    Se sobreescribe `__bool__` porque el consumidor hace
    `starter_lookup or {}` y un dict vacio es falso: sin esto, la
    señal se perderia por el camino.
    """

    SEÑAL = {
        "probability": 66.0,
        "consensus": "UNCERTAIN",
        "hierarchy_value": 40,
        "hierarchy_label": "Importante",
        "source": "TEST",
        "coverage": 1,
    }

    def get(self, key, default=None):
        return dict(self.SEÑAL)

    def __bool__(self):
        return True


TITULARIDAD_NEUTRA = _TitularidadNeutra()


class SinRed:
    def __init__(self, candidatos):
        self.candidatos = candidatos
        self.previos = {}

    def __enter__(self):
        self.previos["bids"] = motor.calculate_bid_recommendations
        self.previos["ext"] = motor.get_external_player_status
        motor.calculate_bid_recommendations = (
            lambda snapshot: [dict(c) for c in self.candidatos]
        )
        motor.get_external_player_status = (
            lambda snapshot, player: {"external_available": False}
        )

        # Y TAMPOCO EL PRONOSTICO DE TITULARIDAD.
        #
        # `build_valuation_context` lee `data/intelligence` del
        # disco. Estos tests no lo mencionan en ninguna parte y
        # aun asi dependian de el: el 16/08/2026 dos de ellos
        # empezaron a fallar sin tocar una linea, porque el
        # fichero de Jornada Perfecta paso a cubrir tambien el
        # mercado y el "Tenaglia" inventado del fixture -id
        # 41100- coincidio con un Tenaglia real pronosticado
        # SUPLENTE. Sus 160 puntos se quedaron en 67 y la puja
        # se cayo.
        #
        # Un test que cambia de resultado porque alguien scrapeo
        # una pagina no esta probando nada. La regla del once
        # tiene su propio fichero -`test_starter_aware_xi_v1`- y
        # ahi el dato se inyecta a mano.
        #
        # 17/08/2026: anularlo con un diccionario VACIO dejo de
        # valer. Desde que "sin pronostico no se puja", el vacio
        # ya no es neutro: bloquea todas las compras y estos tests
        # median cero.
        #
        # Se anula con una señal NEUTRA en vez de con la ausencia:
        # todo el mundo del mismo escalon y en su probabilidad
        # tipica. Sigue sin depender de lo que haya scrapeado
        # nadie, que era el objetivo, y ademas no dispara ningun
        # veto -mismo escalon, cero escalones de bajada-, con lo
        # que lo que se mide sigue siendo el cableado.
        self.previos["starter"] = starter_mod.get_starter_lookup
        starter_mod.get_starter_lookup = lambda: TITULARIDAD_NEUTRA
        valuation_mod.get_starter_lookup = lambda: TITULARIDAD_NEUTRA

        return self

    def __exit__(self, *args):
        motor.calculate_bid_recommendations = self.previos["bids"]
        motor.get_external_player_status = self.previos["ext"]
        starter_mod.get_starter_lookup = self.previos["starter"]
        valuation_mod.get_starter_lookup = self.previos["starter"]
        return False


def recomendacion(
    player_id: int,
    nombre: str,
    precio: int,
    score: int,
    puja: int,
    accion: str,
) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "market_price": precio,
        "player_price": precio,
        "final_score": score,
        "suggested_bid": puja,
        "action": accion,
        "own_player": False,
    }


def ficha(
    player_id: int,
    nombre: str,
    precio: int,
    posicion: int,
    puntos=None,
    estado: str = "ok",
    incremento: int = 0,
    equipo: int = 5,
) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "price": precio,
        "position": posicion,
        "pointsLastSeason": puntos,
        "status": estado,
        "priceIncrement": incremento,
        "teamID": equipo,
    }


def catalogo(extra: list) -> dict:
    """
    Un catalogo con suficientes jugadores con historico para que
    la tarifa por punto se pueda calibrar (20.000 EUR/punto).
    """
    jugadores = {}

    for i in range(60):
        puntos = 40 + i
        jugadores[str(900 + i)] = ficha(
            900 + i, f"Relleno {i}", puntos * 20_000,
            (i % 4) + 1, puntos, equipo=(i % 5) + 1,
        )

    for item in extra:
        jugadores[str(item["id"])] = item

    return {"data": {"players": jugadores, "teams": {}}}


def snapshot(
    fichas: list,
    ventas_computer: list,
    my_team: list,
) -> dict:
    return {
        "league": {"user": {"id": YO}},
        "my_team": my_team,
        "catalog": catalogo(fichas),
        "market": {
            "sales": [
                {
                    "player": {"id": pid},
                    "price": 0,
                    "until": 1786856400,
                    "user": None,
                }
                for pid in ventas_computer
            ],
            "offers": [],
            "status": {
                "balance": 239_968,
                "maximumBid": 12_414_968,
            },
        },
    }


REPARTO = 1786379245


def rivales(activos: bool = True) -> dict:
    """
    Rivales con plantilla conciliable.

    El roster hace falta: sin el no se puede comprobar si conocemos
    su historia, y el modelo -con razon- deja de dar por hecho que
    un rival este inactivo.
    """

    managers = []

    for i in range(4):

        roster = [
            {
                "id": (100 + i) * 1000 + j,
                "name": f"Rival {i} draft {j}",
                "value": 1_000_000,
                "owner_since": REPARTO,
            }
            for j in range(15)
        ]

        transacciones = []

        if activos:
            pid = (100 + i) * 1000 + 500
            roster.append(
                {
                    "id": pid,
                    "name": f"Rival {i} fichado",
                    "value": 2_000_000,
                    "owner_since": REPARTO + 86_400,
                }
            )
            transacciones.append(
                {
                    "kind": "BUY_FROM_COMPUTER",
                    "player_id": pid,
                    "amount": 2_000_000,
                }
            )

        managers.append(
            {
                "user_id": 100 + i,
                "name": f"Rival {i}",
                "maximum_bid": 20_000_000,
                "max_observed_bid": 8_000_000 if activos else 0,
                "lost_bids": 6 if activos else 0,
                "won_auctions": 1 if activos else 0,
                "roster": roster,
                "transactions": transacciones,
            }
        )

    return {
        "managers": managers,
        "competitive_bids": 23,
        "validation": {"exact": True},
    }


PLANTILLA = [
    ficha(YERAY, "Yeray", 1_960_000, 2, 24),
    ficha(XIMO, "Ximo Navarro", 1_280_000, 2, 57),
    ficha(3001, "Dituro", 3_530_000, 1, 123),
    ficha(3002, "Olasagasti", 2_740_000, 3, 121),
    ficha(3003, "Yamal", 22_360_000, 4, 266),
]


def evaluar(recomendaciones, fichas, ventas, ri=None):
    snap = snapshot(fichas, ventas, PLANTILLA)
    with SinRed(recomendaciones):
        return calculate_intelligent_bids(
            snap,
            rival_intelligence=ri if ri is not None else rivales(),
            allow_external_checks=False,
        )


def uno(resultados, nombre):
    for item in resultados:
        if item.get("name") == nombre:
            return item
    raise AssertionError(f"{nombre} no aparece.")


# ============================================================
# LA PUERTA YA NO ES EL SCORE
# ============================================================

def test_un_chollo_con_score_bajo_ya_se_puja() -> None:
    """
    El caso Copete: 150.000 EUR, mas puntos que nuestro peor
    defensa, y score 40. La escalera lo descartaba.
    """
    resultado = uno(
        evaluar(
            [recomendacion(COPETE, "Copete", 150_000, 40, 0, "NO PUJAR")],
            [ficha(COPETE, "Copete", 150_000, 2, 56)],
            [COPETE],
            ri=rivales(activos=False),
        ),
        "Copete",
    )

    assert resultado["action"] == "PUJAR", (
        f"REGRESION: un chollo con score bajo vuelve a quedarse "
        f"fuera ({resultado['action']})."
    )
    assert resultado["promoted_by_value"] is True
    assert resultado["intent"] == "XI_UPGRADE"
    assert resultado["valuation"]["replaces"]["name"] == "Yeray"

    print(
        f"  OK  Copete (score 40) se puja por "
        f"{resultado['suggested_bid']:,} EUR sustituyendo a Yeray"
        .replace(",", ".")
    )


def test_un_score_alto_sin_valor_no_se_puja() -> None:
    """
    La puerta funciona en los dos sentidos: si no aporta, no se
    ficha por muy bien puntuado que este.
    """
    resultado = uno(
        evaluar(
            [recomendacion(7001, "Caro", 9_000_000, 95, 9_500_000, "PUJAR")],
            [ficha(7001, "Caro", 9_000_000, 2, 30)],
            [7001],
        ),
        "Caro",
    )

    assert resultado["action"] == "NO PUJAR", (
        "9 M por 30 puntos no es una mejora, tenga el score que "
        "tenga."
    )
    assert resultado["suggested_bid"] == 0

    print("  OK  score 95 sin valor real: no se puja")


# ============================================================
# DISPONIBILIDAD
# ============================================================

def test_un_lesionado_no_se_ficha_por_barato_que_salga() -> None:
    """
    Al abrir la puerta del score aparecieron Copete y De Jong como
    las mejores operaciones del mercado. Los dos lesionados.
    """
    resultado = uno(
        evaluar(
            [recomendacion(COPETE, "Copete", 150_000, 40, 0, "NO PUJAR")],
            [ficha(COPETE, "Copete", 150_000, 2, 56, estado="injured")],
            [COPETE],
            ri=rivales(activos=False),
        ),
        "Copete",
    )

    assert resultado["action"] == "NO PUJAR"
    assert resultado["valuation"]["decision"] == "NO_DISPONIBLE"
    assert "injured" in resultado["valuation"]["reason"]

    print("  OK  un lesionado no se ficha aunque sea el mejor valor")


def test_una_duda_tampoco() -> None:
    resultado = uno(
        evaluar(
            [recomendacion(COPETE, "Copete", 150_000, 40, 0, "NO PUJAR")],
            [ficha(COPETE, "Copete", 150_000, 2, 56, estado="doubt")],
            [COPETE],
            ri=rivales(activos=False),
        ),
        "Copete",
    )

    assert resultado["action"] == "NO PUJAR"

    print("  OK  una duda de alineacion tampoco se ficha")


# ============================================================
# LA PUJA
# ============================================================

def test_la_puja_sale_del_modelo_no_de_la_escalera() -> None:
    resultado = uno(
        evaluar(
            [
                recomendacion(
                    TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 60,
                    ESCALERA_TENAGLIA, "PUJAR",
                )
            ],
            [ficha(TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 2, 160)],
            [TENAGLIA],
        ),
        "Tenaglia",
    )

    assert resultado["action"] == "PUJAR"
    assert resultado["suggested_bid"] != ESCALERA_TENAGLIA, (
        "La puja deberia salir del modelo, no de la escalera."
    )
    assert resultado["bid_plan"]["decision"] == "BID"
    assert 0 < resultado["win_probability"] <= 1.0

    print(
        f"  OK  puja {resultado['suggested_bid']:,} "
        f"({resultado['win_probability']*100:.0f} % de ganar) "
        f"en vez de {ESCALERA_TENAGLIA:,} de escalera"
        .replace(",", ".")
    )


def test_sin_rivales_activos_se_puja_el_minimo() -> None:
    resultado = uno(
        evaluar(
            [
                recomendacion(
                    TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 60,
                    ESCALERA_TENAGLIA, "PUJAR",
                )
            ],
            [ficha(TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 2, 160)],
            [TENAGLIA],
            ri=rivales(activos=False),
        ),
        "Tenaglia",
    )

    assert resultado["suggested_bid"] == PRECIO_TENAGLIA + 1, (
        f"Sin rivales que pujen, el minimo. Salio "
        f"{resultado['suggested_bid']:,}."
    )

    print("  OK  sin rivales activos, mercado + 1 EUR")


def test_se_registra_a_quien_sustituye() -> None:
    """
    Una mejora del once sin decir a quien mejora no es auditable.
    """
    resultado = uno(
        evaluar(
            [
                recomendacion(
                    TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 60,
                    ESCALERA_TENAGLIA, "PUJAR",
                )
            ],
            [ficha(TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 2, 160)],
            [TENAGLIA],
        ),
        "Tenaglia",
    )

    sustituye = resultado["valuation"]["replaces"]

    assert sustituye["name"] == "Yeray", (
        f"Deberia sustituir al peor defensa. Salio {sustituye}."
    )
    assert resultado["our_value"] > 0

    print(
        f"  OK  queda escrito que sustituye a "
        f"{sustituye['name']} ({sustituye['points']} puntos)"
    )


# ============================================================
# A QUIEN NO SE APLICA
# ============================================================

def test_no_se_toca_a_los_vendidos_por_rivales() -> None:
    snap = snapshot(
        [ficha(TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 2, 160)],
        [],
        PLANTILLA,
    )
    snap["market"]["sales"] = [
        {
            "player": {"id": TENAGLIA},
            "price": PRECIO_TENAGLIA,
            "user": {"id": 555, "name": "Rival"},
        }
    ]

    with SinRed(
        [
            recomendacion(
                TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 60,
                ESCALERA_TENAGLIA, "PUJAR",
            )
        ]
    ):
        resultados = calculate_intelligent_bids(
            snap,
            rival_intelligence=rivales(),
            allow_external_checks=False,
        )

    resultado = uno(resultados, "Tenaglia")

    assert resultado["valuation"] is None, (
        "Una venta de otro manager la lleva el observer bilateral."
    )
    assert resultado["suggested_bid"] == ESCALERA_TENAGLIA

    print("  OK  las ventas de rivales las lleva el otro motor")


def test_sin_inteligencia_de_rivales_no_se_cambia_nada() -> None:
    snap = snapshot(
        [ficha(TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 2, 160)],
        [TENAGLIA],
        PLANTILLA,
    )

    with SinRed(
        [
            recomendacion(
                TENAGLIA, "Tenaglia", PRECIO_TENAGLIA, 60,
                ESCALERA_TENAGLIA, "PUJAR",
            )
        ]
    ):
        resultados = calculate_intelligent_bids(
            snap,
            rival_intelligence=None,
            allow_external_checks=False,
        )

    resultado = uno(resultados, "Tenaglia")

    assert resultado["valuation"] is None
    assert resultado["suggested_bid"] == ESCALERA_TENAGLIA, (
        "Sin datos de rivales se mantiene el comportamiento "
        "anterior."
    )

    print("  OK  sin datos de rivales no se toca nada")


def test_no_se_puja_por_un_jugador_propio() -> None:
    snap = snapshot(
        [ficha(YERAY, "Yeray", 1_960_000, 2, 24)],
        [YERAY],
        PLANTILLA,
    )

    with SinRed(
        [
            {
                **recomendacion(
                    YERAY, "Yeray", 1_960_000, 75, 2_000_000, "PUJAR"
                ),
                "own_player": True,
            }
        ]
    ):
        resultados = calculate_intelligent_bids(
            snap,
            rival_intelligence=rivales(),
            allow_external_checks=False,
        )

    resultado = uno(resultados, "Yeray")

    assert resultado["valuation"] is None, (
        "REGRESION: se valoro un jugador que ya es nuestro."
    )

    print("  OK  un jugador propio no se valora como fichaje")


# ============================================================

TESTS = [
    test_un_chollo_con_score_bajo_ya_se_puja,
    test_un_score_alto_sin_valor_no_se_puja,
    test_un_lesionado_no_se_ficha_por_barato_que_salga,
    test_una_duda_tampoco,
    test_la_puja_sale_del_modelo_no_de_la_escalera,
    test_sin_rivales_activos_se_puja_el_minimo,
    test_se_registra_a_quien_sustituye,
    test_no_se_toca_a_los_vendidos_por_rivales,
    test_sin_inteligencia_de_rivales_no_se_cambia_nada,
    test_no_se_puja_por_un_jugador_propio,
]


def main() -> None:
    print("=" * 60)
    print(" VALOR Y PUJA CONECTADOS AL MERCADO")
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
