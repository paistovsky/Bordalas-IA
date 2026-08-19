"""
El ciclo hacia el mismo trabajo cinco veces.

EL CASO (19/08/2026)

    Los ciclos tardaban 15m44s con el cron cada 30 minutos, y en
    GitHub Actions se acumulaba cola: un ciclo programado llevaba
    una hora entera esperando turno.

    Del log de las 07:22, `build_global_decision` se llamaba
    cuatro o cinco veces sobre los mismos datos:

        1. run_cycle, analisis inicial              234 s
        2. run_cycle, recalculo post-escritura      143 s
        3. V10.6 Position Manager
        4. el ledger V10.5, dentro de esa misma
           sincronizacion
        5. build_dashboard, ya en otro proceso

    Las tres del medio son literalmente la misma llamada con el
    mismo snapshot y sin argumentos extra. Cada una volvia a
    montar solvencia, liquidez, ofertas y especulacion, y a
    refrescar el calendario de LaLiga por HTTP.

LO QUE MAS ENSEÑA DE ESTE FALLO

    Que ya se habia visto a medias. El codigo esta lleno de
    `refresh=False` y de comentarios como "V10.7 comparte el
    mismo snapshot; no vuelve a descargar Biwenger".

    Se compartia el SNAPSHOT y no la DECISION. Alguien vio que
    descargar Biwenger cinco veces era absurdo, lo arreglo, y no
    miro lo que venia justo despues. El dato caro no era la
    descarga: era el calculo.

LA REGLA

    Un snapshot, una decision. Snapshot nuevo -que es lo que pasa
    despues de escribir en Biwenger- decision nueva.
"""

from __future__ import annotations

from src.analysis import decision_orchestrator


PRIMERO = {"timestamp": "2026-08-19T07:22:40"}
SEGUNDO = {"timestamp": "2026-08-19T07:26:38"}


class Contador:
    """
    Sustituye al calculo real y cuenta cuantas veces se pide.

    No hace falta un snapshot de verdad: lo que se prueba es
    cuantas veces se entra a calcular, no que se calcule bien.
    De eso ya se encargan los otros treinta y cuatro.
    """

    def __init__(self):
        self.veces = 0
        self.original = (
            decision_orchestrator.build_global_decision_uncached
        )

    def __enter__(self):
        decision_orchestrator.reset_decision_cache()

        def falso(
            snapshot,
            failure_backoff=None,
            acquisition_board=None,
        ):
            self.veces += 1
            return {
                "decision": {"action": "LO_QUE_SEA"},
                "state": {},
                "candidates": [],
            }

        decision_orchestrator.build_global_decision_uncached = (
            falso
        )

        return self

    def __exit__(self, *_):
        decision_orchestrator.build_global_decision_uncached = (
            self.original
        )
        decision_orchestrator.reset_decision_cache()


def test_un_snapshot_una_decision():
    """
    Las pasadas 2, 3 y 4 del ciclo se calculan una sola vez.
    """

    with Contador() as c:

        decision_orchestrator.build_global_decision(PRIMERO)
        decision_orchestrator.build_global_decision(PRIMERO)

        # Otro diccionario, mismo snapshot: el Position Manager y
        # el ledger vuelven a cargarlo del disco, asi que no es
        # el mismo objeto en memoria.
        decision_orchestrator.build_global_decision(
            dict(PRIMERO)
        )

        assert c.veces == 1, (
            f"el ciclo ha vuelto a calcular la misma decision "
            f"{c.veces} veces"
        )


def test_despues_de_escribir_se_recalcula():
    """
    Lo que NO puede pasar: decidir sobre un mundo que ya cambio.

    Tras aceptar una oferta o guardar el XI, el ciclo descarga un
    snapshot nuevo justamente porque el anterior ya no vale. Si
    la cache se lo comiera, Pepe decidiria la siguiente accion
    sobre una foto anterior a su propia escritura.
    """

    with Contador() as c:

        decision_orchestrator.build_global_decision(PRIMERO)
        decision_orchestrator.build_global_decision(SEGUNDO)

        assert c.veces == 2, (
            "un snapshot nuevo no esta forzando el recalculo: se "
            "esta decidiendo sobre una foto vieja"
        )


def test_la_primera_pasada_nunca_se_cachea():
    """
    La del ciclo lleva el tablero de fichajes y no es la misma
    pregunta, aunque el snapshot coincida.
    """

    with Contador() as c:

        decision_orchestrator.build_global_decision(PRIMERO)

        decision_orchestrator.build_global_decision(
            PRIMERO,
            acquisition_board={"targets": []},
        )

        decision_orchestrator.build_global_decision(
            PRIMERO,
            failure_backoff={"acciones": {}},
        )

        assert c.veces == 3, (
            "se esta devolviendo una decision cacheada a una "
            "llamada que traia datos propios"
        )


def test_sin_fecha_no_se_cachea():
    """
    Ausencia de dato no es dato.

    Dos snapshots sin marca de tiempo no son el mismo snapshot, y
    tratarlos como tal seria congelar el ciclo entero.
    """

    with Contador() as c:

        decision_orchestrator.build_global_decision({})
        decision_orchestrator.build_global_decision({})
        decision_orchestrator.build_global_decision(
            {"timestamp": ""}
        )

        assert c.veces == 3


def test_nadie_contamina_al_siguiente():
    """
    El ciclo escribe DENTRO del resultado.

    `autopilot` hace `result["state"]["sale_intent"] = ...` sobre
    lo que recibe. Si eso llegase a la cache, la pasada siguiente
    encontraria datos que su propio calculo no genero, y el
    origen no aparecerian por ningun lado.
    """

    with Contador():

        primero = (
            decision_orchestrator.build_global_decision(PRIMERO)
        )

        primero["state"]["sale_intent"] = "BASURA"
        primero["candidates"].append({"type": "INVENTADO"})

        segundo = (
            decision_orchestrator.build_global_decision(PRIMERO)
        )

        assert "sale_intent" not in segundo["state"], (
            "la cache se ha quedado con lo que le escribio un "
            "consumidor"
        )

        assert segundo["candidates"] == []


def test_el_ciclo_sigue_llamando_a_la_envoltura():
    """
    La cache no sirve si alguien llama por debajo.

    Estructural: los cinco sitios que piden la decision tienen
    que pedirla por el nombre publico. Llamar a la version sin
    cache desde el ciclo la desactivaria en silencio y solo se
    notaria en el reloj.
    """

    import inspect

    from src import autopilot
    from src.analysis import position_manager_shadow_v106
    from src.telemetry import dashboard_state

    for modulo in (
        autopilot,
        position_manager_shadow_v106,
        dashboard_state,
    ):
        fuente = inspect.getsource(modulo)

        assert "build_global_decision_uncached" not in fuente, (
            f"{modulo.__name__} esta saltandose la cache: el "
            f"ciclo vuelve a calcular lo mismo varias veces"
        )


def main():

    pruebas = [
        test_un_snapshot_una_decision,
        test_despues_de_escribir_se_recalcula,
        test_la_primera_pasada_nunca_se_cachea,
        test_sin_fecha_no_se_cachea,
        test_nadie_contamina_al_siguiente,
        test_el_ciclo_sigue_llamando_a_la_envoltura,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Un snapshot, una decision: todo en verde.")


if __name__ == "__main__":
    main()
