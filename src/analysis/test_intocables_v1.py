"""
A quien Pepe no puede vender ni queriendo.

LA DECISION (dueño, 18/08/2026)

    "Que no me venda a Yamal ni haga locuras."
    Intocables: los Dios, los Clave y el portero titular.

POR QUE UN VETO Y NO UN PESO

    `sales_analyzer` ya penaliza fuerte a los escalones altos: un
    Dios arranca con -30 en la puntuacion de venta. Pero eso es un
    PESO, y un peso se remonta. Un Dios lesionado seis jornadas
    acumula por otras vias hasta pasar del corte de 60, y ahi
    saldria propuesto.

    Este fichero comprueba que no.

Y POR QUE HOY NO BASTA CON LO QUE HAY

    Yamal esta a salvo ahora mismo por accidente: el guardarrail
    posicional bloquea la venta porque hay exactamente dos
    delanteros. El dia que entre un tercero esa proteccion
    desaparece sola y nadie se entera. Por eso el veto tiene que
    ser explicito y tener su propia prueba.
"""

from __future__ import annotations

from src.analysis.sale_intent import (
    GOALKEEPER_POSITION,
    UNTOUCHABLE_HIERARCHY,
    untouchable_reason,
)


def test_los_de_arriba_no_se_tocan():
    """
    De Clave para arriba, ni con la peor puntuacion del mundo.
    """

    for escalon, etiqueta in ((60, "Dios"), (50, "Clave")):

        motivo = untouchable_reason(
            {
                "hierarchy_value": escalon,
                "hierarchy": etiqueta,
                "position": 4,
                "in_lineup": True,
                # Da igual lo roto que este.
                "matchdays_out": 10,
                "starter_probability": 0.0,
            }
        )

        assert motivo, f"{etiqueta} se ha vuelto vendible"
        assert etiqueta in motivo

    # Y el corte esta donde el dueño lo puso: Importante SI se
    # puede vender.
    assert UNTOUCHABLE_HIERARCHY == 50

    assert untouchable_reason(
        {
            "hierarchy_value": 40,
            "hierarchy": "Importante",
            "position": 2,
            "in_lineup": True,
        }
    ) is None


def test_el_portero_titular_va_aparte():
    """
    No por escalon, por puesto.

    Dituro es Importante, no Clave, asi que la regla de jerarquia
    no lo cubre. Lo cubre el puesto: un portero no se rota, y
    quedarse sin el titular a media jornada no se arregla
    comprando otro.
    """

    titular = {
        "hierarchy_value": 40,
        "hierarchy": "Importante",
        "position": GOALKEEPER_POSITION,
        "in_lineup": True,
    }

    assert untouchable_reason(titular), (
        "el portero titular se ha vuelto vendible"
    )

    # El segundo portero SI se puede soltar: es justo el tipo de
    # jugador que sobra en una plantilla.
    suplente = {
        **titular,
        "hierarchy_value": 20,
        "hierarchy": "Reserva",
        "in_lineup": False,
    }

    assert untouchable_reason(suplente) is None

    # Y un jugador de campo del once no queda protegido por estar
    # en el once: eso seria congelar la plantilla entera.
    del_campo = {
        "hierarchy_value": 40,
        "hierarchy": "Importante",
        "position": 2,
        "in_lineup": True,
    }

    assert untouchable_reason(del_campo) is None


def test_sin_escalon_no_se_vende():
    """
    Aqui "ausencia de dato" se resuelve al reves que en el once.

    Alinear a quien no conoces cuesta unos puntos. Venderlo te
    deja SIN el jugador, y eso no se recupera: se lo lleva otro.
    Asi que sin escalon conocido no se propone.
    """

    for vacio in (None, 0, ""):

        motivo = untouchable_reason(
            {
                "hierarchy_value": vacio,
                "hierarchy": None,
                "position": 2,
                "in_lineup": False,
            }
        )

        assert motivo, (
            f"con hierarchy_value={vacio!r} se ha propuesto una "
            f"venta a ciegas"
        )


def test_el_veto_va_antes_que_la_puntuacion():
    """
    Un Dios con 100 de puntuacion de venta tampoco sale.

    Se comprueba sobre el codigo: montar un snapshot completo con
    guardarrail y analisis de ventas seria un test de otra cosa.
    Lo que hay que impedir es que el veto vuelva a quedar DESPUES
    del corte de puntuacion, porque entonces un Dios roto lo
    remonta.
    """

    import ast
    import inspect

    from src.analysis import sale_intent

    fuente = inspect.getsource(sale_intent.build_sale_intent)

    assert "untouchable_reason(" in fuente, (
        "el veto de intocables ha desaparecido del motor"
    )

    arbol = ast.parse(fuente)

    orden = []

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Call) and getattr(
            nodo.func, "id", None
        ) == "untouchable_reason":
            orden.append(("VETO", nodo.lineno))

        if isinstance(nodo, ast.Compare):
            fuente_nodo = ast.dump(nodo)

            if "propose_score" in fuente_nodo:
                orden.append(("CORTE", nodo.lineno))

    vetos = [n for t, n in orden if t == "VETO"]
    cortes = [n for t, n in orden if t == "CORTE"]

    assert vetos, "no se llama a untouchable_reason"
    assert cortes, "no se encuentra el corte por puntuacion"

    assert min(vetos) < min(cortes), (
        "el veto ha quedado por debajo del corte de puntuacion: "
        "un Dios roto lo remontaria y saldria propuesto"
    )


def test_los_vetados_se_ven():
    """
    Un veto silencioso es indistinguible de un olvido.

    Si Pepe decide no tocar a alguien, tiene que decirlo con su
    motivo, no simplemente no mencionarlo.
    """

    import inspect

    from src.analysis import sale_intent

    fuente = inspect.getsource(sale_intent.build_sale_intent)

    assert '"untouchable": intocables' in fuente, (
        "los intocables ya no viajan en el informe"
    )

    informe = inspect.getsource(
        sale_intent.describe_sale_intent
    )

    assert "INTOCABLE" in informe, (
        "los intocables han dejado de imprimirse en el ciclo"
    )


def main():

    pruebas = [
        test_los_de_arriba_no_se_tocan,
        test_el_portero_titular_va_aparte,
        test_sin_escalon_no_se_vende,
        test_el_veto_va_antes_que_la_puntuacion,
        test_los_vetados_se_ven,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Intocables: todo en verde.")


if __name__ == "__main__":
    main()
