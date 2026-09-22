"""
La moneda del fichaje: al que se queda no le paga el mercado.

DE DONDE SALE (22/09/2026)

    `xi_upgrade_value` multiplica los puntos por `tarifa`, que es
    la mediana de `price / pointsLastSeason` del catalogo entero:
    lo que el MERCADO COBRA por un punto, unos 18.300 EUR. Y
    despues le quita un 10 % de margen.

    O sea que el techo de un fichaje era el 90 % de la mediana
    del propio mercado. Que casi nadie pasara no era un hallazgo
    sobre el mercado: era lo que la formula hacia.

    Lo que un punto NOS PAGA esta medido en otro sitio del arbol
    desde el 09/08: `caja_de_la_liga.EUROS_POR_PUNTO = 30.000`,
    cuadrado al euro sobre 24 dias.

LO QUE SE PROTEGE

    1. QUE EL QUE SE QUEDA NO PAGUE PRECIO DE COMERCIANTE. Es la
       guardia que pidio el encargo.
    2. Que el que se compra para REVENDER siga pagando la del
       mercado — sin eso esto seria "subirlo todo", que no es lo
       que se propone.
    3. Que apagado no cambie ni un euro.
    4. Que los dos numeros salgan de donde se midieron, y que la
       moneda viaje publicada en la valoracion.
    5. Que la formula NO cambie: solo el factor de la tarifa.
    6. Que los tres casos reales salgan como tienen que salir:
       Dmitrovic pasa, Maffeo y Cabrera no se caen.
    7. Que el vocabulario sea el que ya existe.
    8. Que la forma no cambie con los datos.
    9. Que el modulo no lea el mundo.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: todo se pasa. Y ponen sus
    propios interruptores (doctrina 104): el 22/09 el paso 0 se
    puso rojo con seis guardias por no hacerlo.

COMO SE USA

    python -m src.analysis.test_la_moneda_del_fichaje_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
#
#     El suyo, y los de los otros dos filtros que corren en la
#     misma cadena: los tres pueden vaciar la lista y dejar esto
#     midiendo el aire.
os.environ.pop("BORDALAS_LA_MONEDA_DE_LA_LIGA", None)
os.environ.pop("BORDALAS_SIN_REVENTA", None)
os.environ.pop("BORDALAS_REVENTA_SOLO_SI_JUEGA", None)
os.environ.pop("BORDALAS_SIN_SUBASTA", None)

import json                                         # noqa: E402

from src.analysis.caja_de_la_liga import (          # noqa: E402
    EUROS_POR_PUNTO,
)
from src.analysis.la_moneda_del_fichaje import (    # noqa: E402
    ENV as MONEDA_ENV,
    MONEDA_DE_LA_LIGA,
    es_para_quedarse,
    tarifa_del_punto,
)
from src.analysis.player_value_engine import (      # noqa: E402
    DEFAULT_XI_MARGIN,
    xi_upgrade_value,
)


# La tarifa medida el 18/09 sobre el catalogo. Se pasa, no se lee.
TARIFA_DEL_MERCADO = 18_300


class _Interruptor:
    """Pone y quita una variable, y la deja como estaba."""

    def __init__(self, nombre, valor="1"):
        self.nombre = nombre
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get(self.nombre)
        os.environ[self.nombre] = self.valor
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.antes
        return False


def _mercado() -> dict:
    return {"rate_median": TARIFA_DEL_MERCADO, "calibrated": True}


def _titular(jerarquia=50) -> dict:
    return {
        "probability": 80.0,
        "hierarchy_value": jerarquia,
        "hierarchy_label": "Clave",
    }


def _ficha_vacia() -> dict:
    return {
        "probability": 0.0,
        "hierarchy_value": 0,
        "hierarchy_label": "FICHA VACIA",
    }


def _valor(puntos, jerarquia=50) -> dict:
    """Un candidato de PLANTILLA: ficha vacia contra el que entra."""

    return xi_upgrade_value(
        candidate_points=puntos,
        replaced_points=0,
        points_market=_mercado(),
        candidate_starter=_titular(jerarquia),
        replaced_starter=_ficha_vacia(),
    )


# Los tres casos reales de la foto del 18/09.
CASOS = (
    ("Maffeo", 121, 1_660_000, True),
    ("Cabrera", 191, 3_040_000, True),
    ("Dmitrovic", 211, 4_770_000, False),
)


# ============================================================
# 1. LA QUE PIDIO EL ENCARGO
# ============================================================

def test_el_que_se_queda_no_paga_precio_de_comerciante():
    """
    Con el interruptor puesto, un candidato de via PLANTILLA se
    valora con los 30.000 de la liga y no con la tarifa del
    mercado.

    MUERDE SI EL CASO NO TIENE CANDIDATO DE PLANTILLA: sin uno no
    habria moneda que cambiar y esta guardia pasaria con las
    manos vacias (doctrina 24).
    """

    de_plantilla = [
        via for via in ("XI_UPGRADE", "ROSTER_FILL")
        if es_para_quedarse(route=via)
    ]

    assert de_plantilla, (
        "el caso no trae ninguna via de plantilla: esta guardia "
        "no estaria midiendo nada"
    )

    assert TARIFA_DEL_MERCADO != MONEDA_DE_LA_LIGA, (
        "las dos monedas del caso son la misma: cambiarla no "
        "probaria nada"
    )

    # ------------------------------------------------
    # APAGADO: la del mercado
    # ------------------------------------------------
    antes = _valor(191)

    assert antes["rate_per_point"] == TARIFA_DEL_MERCADO, (
        f"apagado, el punto tendria que valer "
        f"{TARIFA_DEL_MERCADO} y vale {antes['rate_per_point']}"
    )
    assert antes["moneda"]["moneda"] == "MERCADO"

    # ------------------------------------------------
    # ENCENDIDO: la de la liga
    # ------------------------------------------------
    with _Interruptor(MONEDA_ENV):

        despues = _valor(191)

        for via in de_plantilla:
            visto = tarifa_del_punto(
                TARIFA_DEL_MERCADO, route=via
            )
            assert visto["tarifa"] == MONEDA_DE_LA_LIGA, (
                f"por la via {via} el punto se sigue pagando a "
                f"{visto['tarifa']}"
            )
            assert visto["moneda"] == "LIGA"
            assert visto["para_quedarse"] is True

    assert despues["rate_per_point"] == MONEDA_DE_LA_LIGA, (
        f"encendido, el punto tendria que valer "
        f"{MONEDA_DE_LA_LIGA} y vale {despues['rate_per_point']}"
    )
    assert despues["moneda"]["moneda"] == "LIGA"

    # Y el valor sube EXACTAMENTE en esa proporcion: si subiera
    # en otra, algo mas habria cambiado.
    esperado = int(
        antes["value"] * MONEDA_DE_LA_LIGA / TARIFA_DEL_MERCADO
    )

    assert abs(despues["value"] - esperado) <= 2, (
        f"el valor paso de {antes['value']} a "
        f"{despues['value']}, y por la moneda tendria que ser "
        f"{esperado}"
    )


# ============================================================
# 2. Y EL QUE SE REVENDE SIGUE PAGANDO LA DEL MERCADO
# ============================================================

def test_el_que_se_revende_paga_la_del_mercado():
    """
    Si subiera para todos, esto seria "subirlo todo" y no dos
    monedas. La reventa se le vende AL MERCADO: lo que vale es lo
    que el mercado paga.
    """

    with _Interruptor(MONEDA_ENV):

        for intent, route in (
            ("SPECULATION", "COMPUTER_RESALE"),
            ("SPECULATION", None),
            (None, "PRICE_TREND"),
        ):
            visto = tarifa_del_punto(
                TARIFA_DEL_MERCADO, intent=intent, route=route
            )

            assert visto["tarifa"] == TARIFA_DEL_MERCADO, (
                f"con intent={intent} route={route} el punto se "
                f"paga a {visto['tarifa']}"
            )
            assert visto["moneda"] == "MERCADO"
            assert visto["para_quedarse"] is False

        assert not es_para_quedarse(intent="SPECULATION")


# ============================================================
# 3. APAGADO NO CAMBIA NI UN EURO
# ============================================================

def test_apagado_no_cambia_ni_un_euro():

    assert os.environ.get(MONEDA_ENV) is None

    for puntos in (50, 121, 191, 211):
        visto = _valor(puntos)
        assert visto["rate_per_point"] == TARIFA_DEL_MERCADO
        assert visto["moneda"]["activa"] is False

    for via in ("XI_UPGRADE", "ROSTER_FILL", "COMPUTER_RESALE"):
        assert (
            tarifa_del_punto(TARIFA_DEL_MERCADO, route=via)["tarifa"]
            == TARIFA_DEL_MERCADO
        )

    # Y encendido SI cambia: sin esto lo de arriba pasaria aunque
    # el interruptor no hiciera nada.
    with _Interruptor(MONEDA_ENV):
        assert _valor(191)["rate_per_point"] == MONEDA_DE_LA_LIGA


# ============================================================
# 4. LOS DOS NUMEROS SALEN DE DONDE SE MIDIERON
# ============================================================

def test_los_dos_numeros_salen_de_donde_se_midieron():
    """
    Doctrina 33 y 84: la moneda de la liga no se escribe aqui, se
    importa de `caja_de_la_liga`, que es donde se cuadro al euro.
    """

    assert MONEDA_DE_LA_LIGA == EUROS_POR_PUNTO

    import inspect

    from src.analysis import la_moneda_del_fichaje

    fuente = inspect.getsource(la_moneda_del_fichaje)

    numeros = {
        nodo
        for nodo in (30_000, 18_300)
        if f"= {nodo}" in fuente or f"= {nodo:,}".replace(",", "_") in fuente
    }

    assert not numeros, (
        f"`la_moneda_del_fichaje` escribe {numeros} a mano en vez "
        f"de importarlos"
    )

    # Y LA TARIFA DEL MERCADO SE RECIBE: el modulo no la busca.
    #
    #     Se mira el CODIGO, no la prosa. Contar el nombre en el
    #     texto ponia esto rojo por una frase de la cabecera que
    #     EXPLICA de donde viene la tarifa, que es justo lo que se
    #     quiere. Es la misma leccion de esta mañana con los 135
    #     minutos.
    import ast

    nombres = set()

    for nodo in ast.walk(ast.parse(fuente)):

        if isinstance(nodo, ast.Name):
            nombres.add(nodo.id)

        elif isinstance(nodo, ast.Attribute):
            nombres.add(nodo.attr)

        elif isinstance(nodo, ast.alias):
            nombres.add(nodo.name.rsplit(".", 1)[-1])

    assert "calibrate_points_market" not in nombres, (
        "el modulo se busca la tarifa del mercado por su cuenta"
    )


# ============================================================
# 5. LA FORMULA NO CAMBIA: SOLO EL FACTOR
# ============================================================

def test_la_formula_no_cambia_solo_el_factor():
    """
    El margen, la confianza y el delta se quedan donde estaban.
    Si cambiara algo mas, esto no seria una moneda: seria otra
    formula.
    """

    antes = _valor(191)

    with _Interruptor(MONEDA_ENV):
        despues = _valor(191)

    assert antes["points_delta"] == despues["points_delta"], (
        "el delta ha cambiado y solo tenia que cambiar la tarifa"
    )
    assert antes["confidence"] == despues["confidence"]
    assert antes["recovered_value"] == despues["recovered_value"]

    # Y el `fair_value` es delta x tarifa, exacto, en las dos.
    for visto in (antes, despues):
        assert visto["fair_value"] == int(
            visto["points_delta"] * visto["rate_per_point"]
        ), visto["reason"]

    # El margen sigue siendo el de la casa.
    assert DEFAULT_XI_MARGIN == 0.10


# ============================================================
# 6. LOS TRES CASOS REALES
# ============================================================

def test_los_tres_casos_de_la_foto_del_18_09():
    """
    La prueba que pidio el encargo, con nombres:

        Dmitrovic pedia 22.607 EUR/punto, el motor lo rechazo y
        el dueño lo compro a mano. Tiene que pasar.

        Maffeo y Cabrera pasan hoy. No pueden caerse.
    """

    rechazados = [c for c in CASOS if not c[3]]

    aceptados = [c for c in CASOS if c[3]]

    assert rechazados and aceptados, (
        "el caso necesita de los dos: uno que hoy se rechaza y "
        "otros que hoy pasan. Si no, no prueba que distinga"
    )

    # HOY: los aceptados pasan y el rechazado no.
    for nombre, puntos, precio, pasa_hoy in CASOS:

        valor = _valor(puntos)["value"]

        assert (valor > precio) is pasa_hoy, (
            f"hoy {nombre} vale {valor} contra un precio de "
            f"{precio}: se esperaba {'que pasara' if pasa_hoy else 'que no'}"
        )

    # CON LA MONEDA: pasan los tres.
    with _Interruptor(MONEDA_ENV):

        for nombre, puntos, precio, _ in CASOS:

            valor = _valor(puntos)["value"]

            assert valor > precio, (
                f"con la moneda de la liga {nombre} vale {valor} "
                f"y cuesta {precio}: sigue sin pasar"
            )

        # Y NO PASA TODO EL MUNDO. Nico Williams pedia 60.141
        # EUR/punto: si con la moneda pasara, el techo se habria
        # quedado sin funcion.
        nico = _valor(142)["value"]

        assert nico < 8_540_000, (
            f"Nico Williams vale {nico} y cuesta 8.540.000: con "
            f"la moneda de la liga pasa, y entonces el techo no "
            f"esta frenando a nadie"
        )


# ============================================================
# 7. EL VOCABULARIO YA EXISTIA
# ============================================================

def test_la_moneda_usa_el_vocabulario_que_ya_existe():

    from src.analysis.deployment import SIGNING_ROUTES
    from src.analysis.los_dos_techos import (
        INTENCIONES_DE_QUEDARSE,
    )

    for via in SIGNING_ROUTES:
        assert es_para_quedarse(route=via), (
            f"la route {via} es de fichaje y la moneda la lee "
            f"como reventa"
        )

    for proposito in INTENCIONES_DE_QUEDARSE:
        assert es_para_quedarse(intent=proposito), (
            f"el intent {proposito} es para quedarse y la moneda "
            f"lo lee como reventa"
        )


# ============================================================
# 8. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    casos = [None, 0, -1, "basura", 18_300, 99_999]

    for tarifa in casos:
        for encendido in (False, True):

            if encendido:
                with _Interruptor(MONEDA_ENV):
                    visto = tarifa_del_punto(
                        tarifa, route="XI_UPGRADE"
                    )
            else:
                visto = tarifa_del_punto(tarifa, route="XI_UPGRADE")

            for campo in (
                "tarifa",
                "activa",
                "para_quedarse",
                "moneda",
                "interruptor",
                "reason",
            ):
                assert campo in visto, (
                    f"falta `{campo}` con {tarifa!r}"
                )

            assert isinstance(visto["tarifa"], int), (
                f"la tarifa salio {type(visto['tarifa'])} con "
                f"{tarifa!r}"
            )

            json.dumps(visto, default=str)

    # Una tarifa que no se puede leer no se convierte en cero
    # encendido: la moneda de la liga sigue siendo la de la liga.
    with _Interruptor(MONEDA_ENV):
        assert tarifa_del_punto(
            "basura", route="XI_UPGRADE"
        )["tarifa"] == MONEDA_DE_LA_LIGA


# ============================================================
# 9. NO LEE EL MUNDO
# ============================================================

def test_la_moneda_no_lee_el_mundo():

    import inspect

    from src.analysis import la_moneda_del_fichaje

    fuente = inspect.getsource(la_moneda_del_fichaje)

    for prohibido in (
        "open(",
        "Path(",
        "requests",
        "urllib",
        "datetime.now",
        "time.time",
        "json.load",
    ):
        assert prohibido not in fuente, (
            f"`la_moneda_del_fichaje` usa `{prohibido}`: lo que "
            f"pone precio a un punto no puede leer el mundo"
        )


# ============================================================
# EL CORREDOR
# ============================================================

TESTS = [
    test_el_que_se_queda_no_paga_precio_de_comerciante,
    test_el_que_se_revende_paga_la_del_mercado,
    test_apagado_no_cambia_ni_un_euro,
    test_los_dos_numeros_salen_de_donde_se_midieron,
    test_la_formula_no_cambia_solo_el_factor,
    test_los_tres_casos_de_la_foto_del_18_09,
    test_la_moneda_usa_el_vocabulario_que_ya_existe,
    test_la_forma_no_cambia_con_los_datos,
    test_la_moneda_no_lee_el_mundo,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA MONEDA DEL FICHAJE V1")
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
