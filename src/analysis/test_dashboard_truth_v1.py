"""
Tres formas de mentir del dashboard, cerradas con llave.

DE DONDE SALEN

    De la auditoria cuadro por cuadro del 18/08/2026. De 56
    campos revisados, tres podian enseñar algo falso con cara de
    verdad. Los tres se arreglaron ese dia; esto es lo que impide
    que vuelvan.

    Los tres comparten forma: **un cero o un dato viejo que se
    lee igual que un dato bueno**. Es la misma familia que
    "ausencia de dato no es dato", que ya ha mordido en este
    proyecto con la jerarquia a 0, la previsibilidad a 0.0 y la
    cache vacia.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def test_el_dinero_dice_de_que_esta_hecho():
    """
    Con saldo negativo tambien se dice cuanto es caja y cuanto deuda.

    EL CASO

        La barra de CAJA del dashboard pintaba tres franjas de
        cero mientras el numero "Libre" decia 8.274.100 EUR.

        No era un cero: `calculate_speculation_budget` tiene dos
        ramas y la de saldo negativo devolvia el total sin
        desglosar. Las claves `cash_budget` y `debt_budget` solo
        las escribia la rama de saldo positivo, asi que llegaban
        como None, el generador hacia `safe_int(None)` y salia
        cero.

        Y como el saldo lleva negativo desde que se decidio
        operar con deuda, la barra llevaba apagada desde
        entonces.

    LO QUE SE EXIGE

        Que las dos claves existan SIEMPRE, tanto si hay
        presupuesto como si esta bloqueado. Un cero tiene que
        significar cero, no "nadie me lo ha dicho".
    """

    import inspect

    from src.analysis import speculation_engine

    fuente = inspect.getsource(
        speculation_engine.calculate_speculation_budget
    )

    # Cada return con presupuesto a cero tiene que declararlo.
    a_cero = fuente.count('"total_budget": 0,')
    declarados = fuente.count('"cash_budget": 0,')

    assert declarados >= a_cero, (
        f"{a_cero} returns con presupuesto 0 y solo {declarados} "
        f"declaran de que esta hecho: el que falte vuelve a "
        f"pintar una barra apagada"
    )

    # Y la rama de deuda tiene que repartir el total, no callarse.
    assert '"debt_budget": total_budget,' in fuente, (
        "la rama de saldo negativo ha vuelto a devolver el total "
        "sin decir que todo el es deuda"
    )


def test_sin_fecha_no_se_dice_que_es_de_ahora():
    """
    La edad de un dato se calcula, y si no se sabe se dice.

    EL CASO

        `v10_full_autonomous_status.json` se leia tal cual. Ese
        fichero solo se reescribe cuando el motor con permiso de
        escritura ejecuta, y el observador que regenera la
        pantalla corre mucho mas a menudo.

        El 17/08 a las 20:44 el cuadro titulado ESTE CICLO
        enseñaba una escritura del 16/08 a las 18:56.

    LO QUE SE EXIGE

        Que sin marca de tiempo devuelva None y NO cero. Cero se
        leeria como "acaba de pasar", que es exactamente el error
        que esto viene a evitar.
    """

    from src.telemetry.dashboard_state import (
        STALE_CYCLE_SECONDS,
        _edad_en_segundos,
    )

    assert _edad_en_segundos(None) is None
    assert _edad_en_segundos("") is None
    assert _edad_en_segundos("no soy una fecha") is None

    ahora = datetime.now()

    reciente = _edad_en_segundos(
        ahora.isoformat(timespec="seconds")
    )

    assert reciente is not None
    assert reciente < 60

    viejo = _edad_en_segundos(
        (ahora - timedelta(days=1)).isoformat(timespec="seconds")
    )

    assert viejo is not None
    assert viejo > STALE_CYCLE_SECONDS, (
        "un ciclo de hace un dia tiene que pasar del corte de "
        "caducidad"
    )

    # Y que el corte sea un numero con sentido: dos ciclos de 30
    # minutos. Ni tan corto que salte por un retraso normal ni
    # tan largo que tape un dia entero.
    assert 3600 <= STALE_CYCLE_SECONDS <= 6 * 3600


def test_la_auditoria_puede_fallar():
    """
    El chequeo del ciclo mira algo que NO sale del mismo fichero.

    EL CASO

        `last_write_shown` compara `cycle.write_used` contra
        campos de `last_execution`. Los dos salen del mismo
        sitio, asi que se compara consigo mismo y no puede
        fallar.

        Por eso el panel decia "todo lo que Pepe tiene hecho
        aparece en pantalla", con las seis comprobaciones en
        verde, mientras enseñaba una escritura del dia anterior.

        Un chequeo que no puede fallar no es un chequeo.

    LO QUE SE EXIGE

        Que exista una fila que mire la EDAD -que es verificable,
        porque el reloj no sale del fichero- y que esa fila
        efectivamente falle con un ciclo viejo.
    """

    from src.telemetry.dashboard_consistency import (
        build_consistency_report,
    )

    base = {
        "exposure": {
            "operation_count": 0,
            "committed_total": 0,
        },
        "acquisition": {"targets": []},
        "listings": {"listing_count": 0},
        "lineup": {
            "starter_data_total": 11,
            "starter_data_players": 11,
        },
        "last_execution": {
            "action": "SAVE_LINEUP",
            "status": "OK",
        },
    }

    snapshot = {"market": {"sales": []}, "my_team": []}

    def fila(ciclo):
        informe = build_consistency_report(
            {**base, "cycle": ciclo},
            snapshot,
        )

        elegidas = [
            c
            for c in informe["checks"]
            if c["key"] == "last_write_fresh"
        ]

        assert elegidas, (
            "ha desaparecido la comprobacion de frescura del "
            "ciclo: sin ella nadie puede cazar un ESTE CICLO de "
            "anteayer"
        )

        return elegidas[0], informe

    comun = {
        "write_used": True,
        "action": "SAVE_LINEUP",
        "status": "OK",
    }

    # Un ciclo de hace diez minutos pasa.
    reciente, informe = fila(
        {**comun, "age_seconds": 600, "stale": False}
    )

    assert reciente["ok"] is True
    assert informe["ok"] is True

    # Uno de hace veintiseis horas, no.
    viejo, informe = fila(
        {**comun, "age_seconds": 93_600, "stale": True}
    )

    assert viejo["ok"] is False, (
        "el chequeo ha vuelto a ser incapaz de cazar un ciclo "
        "viejo"
    )

    assert informe["ok"] is False, (
        "la fila falla pero el informe global sigue diciendo que "
        "todo cuadra"
    )

    # Y no se puede decir "Biwenger dice": esto lo dice el reloj.
    assert viejo.get("source") == "RELOJ"

    # Sin marca de tiempo tampoco se da por bueno.
    sin_fecha, informe = fila(
        {**comun, "age_seconds": None, "stale": False}
    )

    assert sin_fecha["ok"] is False
    assert informe["ok"] is False


def test_las_ofertas_las_narra_quien_decide():
    """
    La cuarta forma de mentir: hablar en nombre de otro motor.

    EL CASO (18/08/2026, foto del dueño)

        Trece ofertas en pantalla y las trece decian "Conservar
        buena oferta". Cinco pasaban del 3 % de prima. El dia que
        conectamos el cobro, era imposible mirar la pantalla y
        saber si estaba cobrando.

        La tabla se pintaba desde `offer_reroll`, que solo sabe
        contestar si merece la pena pedir otra oferta. Quien
        decide si se cobra es Offer Decision Engine V2, y ni uno
        solo de sus campos aparecia en el dashboard.

        No era un numero mal calculado. Era el numero correcto de
        la pregunta equivocada.
    """

    from src.telemetry.dashboard_state import compact_offers

    state = {
        "offer_reroll": {
            "offers": [
                {
                    "offer_id": 1,
                    "players": [{"name": "Mangala"}],
                    "amount": 2_922_500,
                    "premium_percent": 4.7,
                    "action": "KEEP_GOOD_OFFER",
                    "hours_to_expiry": 31.5,
                },
                {
                    "offer_id": 7,
                    "players": [{"name": "Nadie lo ha visto"}],
                    "amount": 100,
                    "premium_percent": 0.1,
                    "action": "KEEP_GOOD_OFFER",
                    "hours_to_expiry": 2.0,
                },
            ]
        }
    }

    decisiones = {
        "decisions": [
            {
                "offer_id": 1,
                "decision": "ACCEPT_NOW",
                "sale_score": 68.0,
                "reasons": ["prima buena y es suplente"],
            }
        ]
    }

    filas = compact_offers(
        state,
        offer_decisions=decisiones,
        collecting={
            "offer_id": 1,
            "queued": [{"offer_id": 1}],
        },
    )

    mangala, huerfana = filas

    # 1. Manda V2, no el motor de reroll.
    assert mangala["action"] == "ACCEPT_NOW", (
        "la tabla ha vuelto a hablar en nombre del motor de "
        "reroll: dira 'Conservar' de algo que se esta cobrando"
    )

    assert mangala["decision_source"] == "OFFER_DECISION_V2"

    # 2. Y en castellano, que para eso es una pantalla.
    assert mangala["action_label"] == "Cobrar ahora"

    # 3. La opinion del motor viejo sigue ahi, con su nombre.
    assert mangala["reroll_action"] == "KEEP_GOOD_OFFER"

    # 4. Se ve cual cae en ESTE ciclo. Solo se ejecuta una.
    assert mangala["collecting_now"] is True

    # 5. Y la puntuacion de venta, que es la mitad de la regla:
    #    sin ella, una prima buena no explica por que no se cobra.
    assert mangala["sale_score"] == 68
    assert mangala["decision_reason"]

    # 6. Lo que V2 no ha mirado no se disfraza de veredicto suyo.
    assert huerfana["decision_source"] == "REROLL_ENGINE"
    assert huerfana["sale_score"] is None
    assert huerfana["collecting_now"] is False


def test_el_dashboard_recoge_el_bloque_de_ofertas():
    """
    Que `compact_offers` sepa contarlo no sirve si nadie se lo da.

    El mismo cable suelto de por la mañana, un piso mas arriba.
    """

    import inspect

    from src.telemetry import dashboard_state

    fuente = inspect.getsource(
        dashboard_state.build_dashboard_state
    )

    assert "OFFER_DECISION_INTELLIGENCE" in fuente, (
        "el dashboard ha dejado de leer el bloque de ofertas del "
        "ciclo: la tabla vuelve a ser del motor viejo"
    )

    assert "offer_decisions=" in fuente
    assert "queued_to_collect" in fuente


def main():

    pruebas = [
        test_el_dinero_dice_de_que_esta_hecho,
        test_sin_fecha_no_se_dice_que_es_de_ahora,
        test_la_auditoria_puede_fallar,
        test_las_ofertas_las_narra_quien_decide,
        test_el_dashboard_recoge_el_bloque_de_ofertas,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Verdad del dashboard: todo en verde.")


if __name__ == "__main__":
    main()
