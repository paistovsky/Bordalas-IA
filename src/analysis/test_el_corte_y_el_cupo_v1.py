"""
El corte de la reventa y el cupo por ventana.

SINTOMA (21/09/2026)

    El reset de las 07:00 compro SEIS jugadores por 2.566.406
    EUR, todas de modo cartera. La caja paso de +2.410.033 a
    -156.373 y la plantilla de 15 a 21 fichas: CERO fichas
    libres. Cinco de los seis son suplentes de 150.000-230.000.

    Se apago con `BORDALAS_SIN_SUBASTA=1`.

LAS DOS COSAS QUE ESTABAN MAL, Y SON DISTINTAS

    1. NO HABIA COMO CERRAR LA REVENTA SIN CERRAR EL FICHAJE.
       `BORDALAS_SIN_SUBASTA` apaga `plan_del_reset` entera, y
       ademas no toca el carril de la rendija.

    2. EL TOPE DE TRES ERA POR VUELTA, NO POR VENTANA. En los
       135 minutos entran dos disparos. Medido sobre
       `libro_de_la_ventana.jsonl` (n=19 vueltas, 10 ventanas):
       nueve ventanas tuvieron dos vueltas dentro y en tres la
       suma paso de tres — 18/09 fue 3 + 2 = 5.

LO QUE SE PROTEGE

     1. Que el corte, apagado, no cambie ni una puja.
     2. Que el corte cierre la reventa de la cesta.
     3. QUE EL CORTE NO TOQUE LA COMPRA DE PLANTILLA. Es la
        guardia que decide si el corte sirve.
     4. Que sin via no se escriba.
     5. Que el vocabulario sea el que ya existia.
     6. Que el cupo, apagado, siga siendo por vuelta.
     7. QUE EL CUPO DE LA VENTANA NO SE REINICIE POR VUELTA.
     8. Que `lectura_del_estado` lleve la via y la jerarquia.
     9. Que el carril lleve la via de sus candidatos.
    10. Que la forma no cambie con los datos.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: todo se pasa. Las unicas que
    tocan el entorno son las de los interruptores -que SON
    variables de entorno- y lo dejan como estaba.

COMO SE USA

    python -m src.analysis.test_el_corte_y_el_cupo_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA  (doctrina 104)
#
#     Con `BORDALAS_SIN_SUBASTA=1` en el `env` del workflow,
#     `plan_del_reset` devuelve INTERRUPTOR y esta guardia se
#     pondria roja sin que nada estuviera roto. Se quita aqui
#     arriba, antes de importar nada que lo mire.
#
#     Y los dos interruptores nuevos, igual: cada prueba los pone
#     y los quita ella.
os.environ.pop("BORDALAS_SIN_SUBASTA", None)
os.environ.pop("BORDALAS_SIN_REVENTA", None)
os.environ.pop("BORDALAS_CUPO_POR_VENTANA", None)

import json                                         # noqa: E402

from src.analysis.el_corte_de_la_reventa import (   # noqa: E402
    ENV as CORTE_ENV,
    MODOS_DE_REVENTA,
    QUEDARSE,
    REVENDER,
    corta,
    separar,
    via_del_candidato,
)
from src.analysis.la_subasta import (               # noqa: E402
    CUPO_POR_VENTANA_ENV,
    MAX_PUJAS_PRIMER_DIA,
    MODO_CARTERA,
    lectura_del_estado,
    plan_del_reset,
)


# ============================================================
# EL MUNDO DE MENTIRA
# ============================================================

PRIMA = 0.0187


class _Interruptor:
    """Pone y quita una variable, y la deja como estaba."""

    def __init__(self, nombre: str, valor: str = "1"):
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


def _sano() -> dict:
    """Un reloj de solvencia que deja pujar."""

    return {"state": "SIN_DEUDA", "deficit": 0, "covered": True}


def _mercado(cuantos: int = 6, club: int = 1) -> list:
    """
    Candidatos de cartera: sin via de fichaje, como hoy.

    CON PRONOSTICO, AUNQUE ESTA GUARDIA NO LO MIRE (22/09/2026)

        `la_regla_de_compra` —el otro filtro de `plan_del_reset`,
        el que mira si el jugador va a jugar— frena a quien no
        trae `starter_probability`. Sin estos dos campos, con
        `BORDALAS_REVENTA_SOLO_SI_JUEGA` puesto no quedaba ni un
        candidato y esta guardia se caia por su propia guarda de
        doctrina 24, diciendo la verdad sobre un caso incompleto.

        Las filas del tablero de verdad los traen. Las de aqui,
        ahora tambien. Ninguna afirmacion cambia: lo que esta
        guardia mide es la VIA, no el pronostico.

        Los dos cortes de la casa estan en 40.
    """

    return [
        {
            "id": 100 + i,
            "name": f"Jugador {i}",
            "market_price": 100_000 + 10_000 * i,
            "team_id": club + i,
            "starter_probability": 80.0,
            "hierarchy_value": 60,
        }
        for i in range(cuantos)
    ]


def _de_plantilla(id_: int = 900, precio: int = 1_190_000) -> dict:
    """
    Un candidato que el tablero clasifico PARA QUEDARSE.

    Es la forma de Maffeo en la foto del 18/09: `intent`
    XI_UPGRADE y `route` XI_UPGRADE, valor de fichaje por encima
    del precio.

    EL PRECIO, POR DEBAJO DEL SUELO DE LA CESTA (22/09/2026)

        Maffeo costaba 1.660.000 y aqui el precio es 1.190.000.
        No es un capricho: `BORDALAS_CESTA_SOLO_EL_SUELO` hace
        que la cesta no mire a nadie por encima de
        `CORTES_DE_PRECIO[0]` = 1.500.000, asi que con ese
        interruptor puesto el candidato de plantilla desaparecia
        de la lista y esta guardia se quedaba sin nada que
        probar.

        LO QUE SE MIDE AQUI ES LA VIA, NO EL PRECIO: que un
        candidato QUEDARSE sobreviva al corte de la reventa. El
        precio solo tiene que dejarle llegar hasta el corte, y
        por debajo del suelo llega con cualquier interruptor
        puesto. Hay guardia de que el numero sigue por debajo.
    """

    return {
        "id": id_,
        "name": "El que se queda",
        "market_price": precio,
        "team_id": 42,
        "intent": "XI_UPGRADE",
        "route": "XI_UPGRADE",
        "hierarchy_value": 40,
        "starter_probability": 50.0,
        "expected_points": 121,
    }


def _plan(**cambios) -> dict:
    """El plan con todo en verde, salvo lo que se cambie."""

    argumentos = {
        "candidatos": _mercado(),
        "prima_de_reventa": PRIMA,
        "presupuesto": 5_000_000,
        "fichas_libres": 6,
        "caja_libre": 3_000_000,
        "seconds_to_reset": 300,
        "solvency_clock": _sano(),
        "plantilla": [],
        "bloqueo_temporal": None,
        "en_vivo": True,
        "max_por_club": 4,
    }

    argumentos.update(cambios)

    return plan_del_reset(**argumentos)


# ============================================================
# 1. EL CORTE, APAGADO, NO CAMBIA NADA
# ============================================================

def test_el_corte_apagado_no_frena_ni_una_puja():
    """
    Un interruptor apagado que cambia algo no esta apagado.
    """

    assert os.environ.get(CORTE_ENV) is None, (
        "esta guardia arranca con el corte quitado"
    )

    plan = _plan()

    assert plan["execute"] is True, (
        "sin el corte tendria que pujar; si no, las guardias de "
        "abajo no probarian nada"
    )
    assert plan["bids"], "no hay cesta que frenar"
    assert plan["dropped_by_reventa"] == 0, (
        "con el corte quitado no se frena a nadie"
    )

    # Y el corte, preguntado a pelo, dice que no corta.
    for fila in (
        {"modo": MODO_CARTERA},
        {"intent": "SPECULATION"},
        {"intent": "XI_UPGRADE"},
        {},
    ):
        assert corta(**fila)["corta"] is False, (
            f"con {CORTE_ENV} quitado, {fila} no se frena"
        )


# ============================================================
# 2. EL CORTE CIERRA LA REVENTA
# ============================================================

def test_el_corte_cierra_la_cesta_de_reventa():
    """
    Con el corte puesto, la cesta de modo cartera no puja.
    """

    antes = _plan()

    assert antes["execute"] is True and antes["bids"], (
        "sin corte tendria que haber cesta que cerrar"
    )

    with _Interruptor(CORTE_ENV):

        plan = _plan()

    assert plan["execute"] is False, (
        f"{CORTE_ENV}=1 y la cesta sigue pujando"
    )
    assert plan["bids"] == [], (
        f"{CORTE_ENV}=1 y sigue proponiendo pujas de reventa"
    )
    assert plan["blocked_by"] == "SIN_REVENTA", (
        f"cerrado por {plan['blocked_by']}, no por el corte"
    )
    assert plan["dropped_by_reventa"] == len(_mercado()), (
        f"frenados {plan['dropped_by_reventa']} de "
        f"{len(_mercado())}"
    )
    assert plan["committed"] == 0, (
        "la reventa cerrada y sigue comprometiendo dinero"
    )


# ============================================================
# 3. LA QUE DECIDE SI EL CORTE SIRVE
# ============================================================

def test_el_corte_no_toca_la_compra_de_plantilla():
    """
    Con el corte puesto, un candidato clasificado PARA QUEDARSE
    sigue generando puja.

    MUERDE SI EL CASO NO TIENE CANDIDATO DE PLANTILLA: una
    guardia que pasa porque no habia nada que mirar no prueba
    nada (doctrina 24).
    """

    candidatos = _mercado(3) + [_de_plantilla()]

    # ------------------------------------------------
    # EL CASO TIENE LO QUE DICE TENER
    # ------------------------------------------------
    de_plantilla = [
        c
        for c in candidatos
        if via_del_candidato(
            intent=c.get("intent"), route=c.get("route")
        )
        == QUEDARSE
    ]

    assert de_plantilla, (
        "el caso no trae ningun candidato PARA QUEDARSE: esta "
        "guardia no estaria midiendo nada"
    )

    # Y TIENE QUE LLEGAR HASTA EL CORTE con cualquier interruptor
    # puesto. `BORDALAS_CESTA_SOLO_EL_SUELO` aparta a los de
    # 1.500.000 para arriba, y un candidato apartado antes del
    # corte no prueba que el corte lo respete.
    from src.analysis.la_subasta import CORTES_DE_PRECIO

    for c in de_plantilla:
        assert c["market_price"] < CORTES_DE_PRECIO[0], (
            f"{c['name']} cuesta {c['market_price']} y el suelo "
            f"de la cesta esta en {CORTES_DE_PRECIO[0]}: con "
            f"BORDALAS_CESTA_SOLO_EL_SUELO puesto no llegaria al "
            f"corte y esta guardia pasaria con las manos vacias"
        )

    de_reventa = [
        c
        for c in candidatos
        if via_del_candidato(
            intent=c.get("intent"),
            route=c.get("route"),
            modo=MODO_CARTERA,
        )
        == REVENDER
    ]

    assert de_reventa, (
        "el caso no trae ninguna reventa que cerrar: sin eso, "
        "que el de plantilla siga no prueba que se hayan "
        "separado"
    )

    # ------------------------------------------------
    # 3a. EL CORTE, A PELO
    # ------------------------------------------------
    with _Interruptor(CORTE_ENV):

        for c in de_plantilla:
            veredicto = corta(
                intent=c.get("intent"),
                route=c.get("route"),
                modo=MODO_CARTERA,
                nombre=c.get("name"),
            )

            assert veredicto["corta"] is False, (
                f"{c['name']} va PARA QUEDARSE y el corte lo "
                f"frena: {veredicto['reason']}"
            )
            assert veredicto["via"] == QUEDARSE

        reparto = separar(
            [{**c, "modo": MODO_CARTERA} for c in candidatos]
        )

        assert len(reparto["siguen"]) == len(de_plantilla), (
            f"siguen {len(reparto['siguen'])} y de plantilla hay "
            f"{len(de_plantilla)}"
        )
        assert not [
            f
            for f in reparto["frenados"]
            if f["via"] == QUEDARSE
        ], "hay una compra de plantilla entre las frenadas"

        # ------------------------------------------------
        # 3b. Y EN EL PLAN DEL RESET, QUE ES DONDE PUJA
        # ------------------------------------------------
        plan = _plan(candidatos=candidatos)

    assert plan["execute"] is True, (
        f"con el corte puesto y un candidato de plantilla en la "
        f"lista no se puja: {plan['reason']}"
    )
    assert plan["bids"], "el candidato de plantilla no puja"

    pujados = {b.get("id") for b in plan["bids"]}

    assert pujados == {c["id"] for c in de_plantilla}, (
        f"se puja por {pujados} y los de plantilla son "
        f"{[c['id'] for c in de_plantilla]}"
    )
    assert plan["dropped_by_reventa"] == len(de_reventa), (
        f"frenadas {plan['dropped_by_reventa']} reventas de "
        f"{len(de_reventa)}"
    )


# ============================================================
# 4. SIN VIA NO SE ESCRIBE
# ============================================================

def test_sin_via_el_corte_frena():
    """
    "No lo sabemos" no es via libre (doctrina 103). Y no puede
    tumbar una compra de plantilla, porque esa SI consta.
    """

    assert via_del_candidato() is None, (
        "sin intent, sin route y sin modo la via no consta"
    )

    with _Interruptor(CORTE_ENV):

        veredicto = corta(nombre="Sin via")

        assert veredicto["corta"] is True
        assert veredicto["via"] is None
        assert "no consta" in (veredicto["reason"] or "")


# ============================================================
# 5. EL VOCABULARIO YA EXISTIA
# ============================================================

def test_el_corte_usa_el_vocabulario_que_ya_existe():
    """
    Doctrina 33: un dato, un nombre. El corte no escribe una
    tercera lista de "que es un fichaje".
    """

    from src.analysis.deployment import SIGNING_ROUTES
    from src.analysis.los_dos_techos import (
        INTENCIONES_DE_QUEDARSE,
    )
    from src.analysis.rival_bid_model import INTENTS_DEL_ONCE

    assert INTENTS_DEL_ONCE == SIGNING_ROUTES, (
        "las dos listas de vias de fichaje se han separado: "
        f"{INTENTS_DEL_ONCE} contra {SIGNING_ROUTES}"
    )

    for via in SIGNING_ROUTES:
        assert via_del_candidato(route=via) == QUEDARSE, (
            f"la route {via} es un fichaje y el corte la lee "
            f"como reventa"
        )

    for proposito in INTENCIONES_DE_QUEDARSE:
        assert via_del_candidato(intent=proposito) == QUEDARSE, (
            f"el intent {proposito} es para quedarse y el corte "
            f"lo lee como reventa"
        )

    assert MODO_CARTERA in MODOS_DE_REVENTA, (
        f"el modo de la cesta ({MODO_CARTERA}) no esta en los "
        f"modos de reventa del corte"
    )

    assert via_del_candidato(modo="UN_DISPARO") is None, (
        "el modo de un disparo no dice por que se compra: no "
        "puede decidir la via el solo"
    )


# ============================================================
# 6. EL CUPO, APAGADO, SIGUE SIENDO POR VUELTA
# ============================================================

def test_el_cupo_apagado_se_comporta_como_ayer():
    """
    Sin el interruptor, tres pujas ya puestas en la ventana no
    recortan nada: es el comportamiento del 21/09.
    """

    assert os.environ.get(CUPO_POR_VENTANA_ENV) is None

    plan = _plan(ya_pujados=[900, 901, 902])

    assert plan["cupo_por_ventana"] is False
    assert plan["ya_en_la_ventana"] == 3, (
        "el recuento se publica aunque el cupo este apagado"
    )
    assert plan["capped_at"] == MAX_PUJAS_PRIMER_DIA, (
        f"apagado, el tope sigue siendo "
        f"{MAX_PUJAS_PRIMER_DIA}; salio {plan['capped_at']}"
    )
    assert len(plan["bids"]) == MAX_PUJAS_PRIMER_DIA, (
        "apagado, la segunda vuelta vuelve a pujar tres"
    )


# ============================================================
# 7. EL CUPO DE LA VENTANA NO SE REINICIA POR VUELTA
# ============================================================

def test_el_cupo_de_la_ventana_no_se_reinicia_por_vuelta():
    """
    Dos vueltas dentro de la MISMA ventana, tres pujas en la
    primera: la segunda no puja.

    MUERDE SI EL CASO TIENE UNA SOLA VUELTA: si las dos
    llamadas no caen dentro de la ventana, o si la primera no
    llega a pujar tres, esto no estaria midiendo el reinicio.
    """

    from src.analysis.la_subasta import (
        VENTANA_MINUTOS,
        ventana_abierta,
    )

    # Dos disparos separados, los dos dentro de los 135 minutos.
    # Salen de la constante, no a mano.
    primera_a = VENTANA_MINUTOS * 60 - 60

    segunda_a = 15 * 60

    for cuando in (primera_a, segunda_a):
        assert ventana_abierta(cuando)["abierta"] is True, (
            f"a {cuando} s del reset la ventana esta cerrada: el "
            f"caso no tiene dos vueltas dentro de la misma "
            f"ventana"
        )

    assert primera_a != segunda_a, "son dos vueltas, no una"

    with _Interruptor(CUPO_POR_VENTANA_ENV):

        # ------------------------------------------
        # PRIMERA VUELTA: nadie ha pujado todavia
        # ------------------------------------------
        primera = _plan(
            seconds_to_reset=primera_a,
            ya_pujados=[],
        )

        assert len(primera["bids"]) == MAX_PUJAS_PRIMER_DIA, (
            f"la primera vuelta tendria que pujar "
            f"{MAX_PUJAS_PRIMER_DIA} y pujo "
            f"{len(primera['bids'])}: sin eso no hay cupo "
            f"gastado que probar"
        )

        puestos = [b["id"] for b in primera["bids"]]

        # ------------------------------------------
        # SEGUNDA VUELTA: el libro ya trae las tres
        # ------------------------------------------
        segunda = _plan(
            seconds_to_reset=segunda_a,
            ya_pujados=puestos,
        )

        assert segunda["cupo_por_ventana"] is True
        assert segunda["ya_en_la_ventana"] == len(puestos)
        assert segunda["bids"] == [], (
            f"el cupo se reinicio por vuelta: la segunda puja "
            f"por {[b.get('name') for b in segunda['bids']]}"
        )
        assert segunda["execute"] is False
        assert segunda["blocked_by"] == "CUPO_DE_LA_VENTANA", (
            f"cerrado por {segunda['blocked_by']}, no por el cupo"
        )
        assert segunda["committed"] == 0

        # Y con DOS puestas todavia cabe una: el cupo resta, no
        # cierra.
        queda_una = _plan(
            seconds_to_reset=segunda_a,
            ya_pujados=puestos[:2],
        )

        assert len(queda_una["bids"]) == 1, (
            f"con 2 puestas de {MAX_PUJAS_PRIMER_DIA} tendria "
            f"que caber 1 y caben {len(queda_una['bids'])}"
        )


# ============================================================
# 8. LA LECTURA DEL ESTADO LLEVA LA VIA Y LA JERARQUIA
# ============================================================

def test_la_lectura_lleva_la_via_y_la_jerarquia():
    """
    El 21/09 la cesta compro cinco suplentes que el motor
    etiqueta "no va a puntuar". No los prefirio: no podia
    verlos. `lectura_del_estado` tiraba los campos.
    """

    fila = {
        "id": 900,
        "name": "El que se queda",
        "market_price": 1_660_000,
        "team_id": 42,
        "seller_id": None,
        "decision": "BID",
        "intent": "XI_UPGRADE",
        "deployment": {"route": "ROSTER_FILL"},
        "hierarchy_value": 40,
        "starter_probability": 50.0,
        "expected_points": 121,
        "market_gate": {"rate_percent_per_day": 0.8},
    }

    lectura = lectura_del_estado(
        {"acquisition": {"targets": [fila]}}
    )

    assert lectura["candidatos"], "el candidato no llego"

    visto = lectura["candidatos"][0]

    for campo, esperado in (
        ("intent", "XI_UPGRADE"),
        ("route", "ROSTER_FILL"),
        ("hierarchy_value", 40),
        ("starter_probability", 50.0),
        ("expected_points", 121),
    ):
        assert visto.get(campo) == esperado, (
            f"`lectura_del_estado` tira `{campo}`: llego "
            f"{visto.get(campo)!r} en vez de {esperado!r}"
        )

    # Y con esos campos el corte ya sabe que es para quedarselo.
    assert (
        via_del_candidato(
            intent=visto.get("intent"),
            route=visto.get("route"),
        )
        == QUEDARSE
    )

    # Los seis de siempre siguen estando.
    for campo in (
        "id",
        "name",
        "market_price",
        "team_id",
        "seller_id",
        "rate_percent_per_day",
    ):
        assert campo in visto, f"se perdio `{campo}`"


# ============================================================
# 9. EL CARRIL LLEVA LA VIA DE SUS CANDIDATOS
# ============================================================

def test_el_carril_no_pierde_la_via_por_el_camino():
    """
    El carril copiaba CINCO campos del tablero y dejaba atras
    `intent` y `route`. Sin ellos, el corte frenaria tambien al
    que se compra para quedarselo — y el 18/09 este carril puso
    diez pujas por Maffeo, clasificado QUEDARSE.

    Se mira el codigo que arma los candidatos, no el fichero
    entero: la guardia no puede depender de que nadie escriba
    "intent" en un comentario.
    """

    import ast
    import inspect

    from src.actions import carril_executor

    fuente = inspect.getsource(carril_executor.correr)

    arbol = ast.parse(
        "def _x():\n"
        + "\n".join(
            "    " + linea for linea in fuente.splitlines()
        )
    )

    claves = set()

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Dict):
            continue

        suyas = {
            k.value
            for k in nodo.keys
            if isinstance(k, ast.Constant)
            and isinstance(k.value, str)
        }

        if "player_id" in suyas and "market_price" in suyas:
            claves |= suyas

    assert claves, (
        "no se encontro el dict de candidatos del carril: esta "
        "guardia no estaria mirando nada"
    )

    for campo in ("intent", "route"):
        assert campo in claves, (
            f"el carril arma sus candidatos sin `{campo}`: el "
            f"corte de la reventa no podria distinguir una "
            f"compra de plantilla"
        )


# ============================================================
# 10. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():
    """
    Los campos nuevos salen SIEMPRE, y con el tipo de siempre.
    """

    casos = [
        {},
        {"candidatos": None},
        {"candidatos": ["basura", 7, None]},
        {"solvency_clock": None},
        {"seconds_to_reset": None},
        {"presupuesto": None, "caja_libre": None},
        {"ya_pujados": None},
        {"ya_pujados": ["x", None, 0]},
    ]

    for extra in casos:

        for interruptores in ([], [CORTE_ENV], [CUPO_POR_VENTANA_ENV]):

            puestos = [_Interruptor(x) for x in interruptores]

            for p in puestos:
                p.__enter__()

            try:
                plan = _plan(**extra)

            finally:
                for p in reversed(puestos):
                    p.__exit__(None, None, None)

            for campo, tipo in (
                ("dropped_by_reventa", int),
                ("ya_en_la_ventana", int),
                ("cupo_por_ventana", bool),
            ):
                assert campo in plan, (
                    f"falta `{campo}` con {extra} y "
                    f"{interruptores}"
                )
                assert isinstance(plan[campo], tipo), (
                    f"`{campo}` salio {type(plan[campo])} con "
                    f"{extra}"
                )

            # Y sigue siendo serializable, que es lo que la
            # pantalla necesita.
            json.dumps(plan, default=str)


# ============================================================
# EL CORREDOR
# ============================================================

TESTS = [
    test_el_corte_apagado_no_frena_ni_una_puja,
    test_el_corte_cierra_la_cesta_de_reventa,
    test_el_corte_no_toca_la_compra_de_plantilla,
    test_sin_via_el_corte_frena,
    test_el_corte_usa_el_vocabulario_que_ya_existe,
    test_el_cupo_apagado_se_comporta_como_ayer,
    test_el_cupo_de_la_ventana_no_se_reinicia_por_vuelta,
    test_la_lectura_lleva_la_via_y_la_jerarquia,
    test_el_carril_no_pierde_la_via_por_el_camino,
    test_la_forma_no_cambia_con_los_datos,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL CORTE DE LA REVENTA Y EL CUPO POR VENTANA V1")
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
