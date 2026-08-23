"""
Una escritura contada no puede salir por no contada.

EL CASO (23/08/2026)

    La pantalla, en rojo:

        "ESTA PANTALLA NO CUADRA CON BIWENGER.
         1 comprobacion(es) no cuadran: La ultima escritura esta
         contada. Biwenger dice true, aqui sale false."

    Y era mentira. El ciclo de las 20:57 habia escrito, habia
    dicho que escribio y como acabo:

        action        RAISE_COUNTER
        label         Mejorar contraoferta
        success       true
        http_status   200
        write_used    true
        status        null          <- lo unico vacio

    La guarda exigia `status`. Pero `status` no es el desenlace:
    es un campo opcional que `_compact_execution` copia con
    `result.get("status")`, y el resultado de una contraoferta
    -POST /offers, que devuelve `success`, `http_status` y
    `success_detail`- no lo trae.

POR QUE IMPORTA MAS DE LO QUE PARECE

    Esta pantalla existe para una sola cosa: avisar cuando lo que
    se ve no es lo que hay. Una alarma que salta sin motivo la
    gasta. La siguiente, la de verdad, se lee igual que esta.

    Y el fallo era ademas del tipo que este fichero persigue:
    confundir "no tengo ese dato" con "eso no ha pasado".

LO QUE SE PROTEGE AQUI

    1. Que una escritura con nombre y desenlace cuente, aunque
       `status` venga vacio.
    2. Que sin nombre no cuente: eso si es una escritura huerfana.
    3. Que sin desenlace no cuente: "se mando" no es "acabo".
    4. Que la escritura enseñada sea la de ESTE ciclo. Si
       `last_execution` se cae al historial, la pantalla enseña
       una escritura vieja con cara de reciente, y esta fila
       tiene que cazarlo.
    5. Que un ciclo que no escribio siga sin dar la alarma.
"""

from __future__ import annotations

from src.telemetry.dashboard_consistency import (
    build_consistency_report,
)


# El ciclo real del 23/08/2026 a las 20:57, tal cual salio en
# `v10_full_autonomous_status.json` y en `status.json`.
CICLO_REAL = {
    "version": "V10.13.1",
    "timestamp": "2026-08-23T20:57:07.928390+00:00",
    "write_used": True,
    "action": "RAISE_COUNTER",
    "label": "Mejorar contraoferta",
    "status": None,
    "success": True,
    "source": "V10_COUNTER",
    "reason": None,
    "http_status": 200,
    "post_write_verified": True,
    "age_seconds": 19,
    "stale": False,
}

ULTIMA_REAL = {
    **CICLO_REAL,
    "write_performed": True,
    "succeeded": True,
    "verified_post_action": True,
}


def dashboard(ciclo, ultima):
    """
    Lo minimo para que las otras filas no estorben: sin pujas,
    sin publicaciones y sin ofertas.
    """

    return {
        "cycle": dict(ciclo),
        "last_execution": dict(ultima),
        "exposure": {"operation_count": 0, "committed_total": 0},
        "acquisition_board": {"targets": []},
        "market_center": {"listings": [], "offers": []},
    }


SNAPSHOT_VACIO = {
    "league": {"user": {"id": 14175949}},
    "my_team": [],
    "market": {"offers": [], "sales": []},
}


def fila(ciclo, ultima):

    informe = build_consistency_report(
        dashboard(ciclo, ultima),
        SNAPSHOT_VACIO,
        current_user_id=14175949,
    )

    encontrada = next(
        (
            c
            for c in (informe.get("checks") or [])
            if c.get("key") == "last_write_shown"
        ),
        None,
    )

    assert encontrada is not None, (
        "la fila de la ultima escritura ha desaparecido del "
        "informe"
    )

    return encontrada


# ============================================================
# PRUEBAS
# ============================================================


def test_el_caso_de_la_contraoferta():
    """
    El ciclo real que disparo la falsa alarma. Sin `status` y con
    todo lo demas: tiene que salir en verde.
    """

    f = fila(CICLO_REAL, ULTIMA_REAL)

    assert f["ok"], (
        "una escritura con accion, exito y HTTP 200 sigue "
        "saliendo como no contada solo porque `status` viene "
        "vacio"
    )


def test_sin_nombre_no_cuenta():
    """
    Escribir y no saber que se escribio SI es un fallo. Es el que
    esta fila busca.
    """

    ciclo = {**CICLO_REAL, "action": None, "label": None}
    ultima = {}

    assert not fila(ciclo, ultima)["ok"]


def test_sin_desenlace_no_cuenta():
    """
    "Se mando la peticion" no es "acabo bien". Sin ninguno de los
    campos que describen el final, no hay nada que contar.
    """

    ultima = {
        "action": "RAISE_COUNTER",
        "write_performed": True,
        "status": None,
        "success": None,
        "succeeded": None,
        "http_status": None,
    }

    assert not fila(CICLO_REAL, ultima)["ok"]


def test_un_fallo_tambien_esta_contado():
    """
    Una escritura que salio mal esta igual de contada que una que
    salio bien: la fila pregunta si la pantalla lo dice, no si
    salio bien.

    Es la diferencia entre "la pantalla esconde algo" y "ha ido
    mal". La segunda se cuenta en otro sitio.
    """

    ciclo = {**CICLO_REAL, "success": False, "http_status": 500}
    ultima = {
        **ULTIMA_REAL,
        "success": False,
        "succeeded": False,
        "http_status": 500,
        "label": "Mejorar contraoferta: NO se completó",
        "verified_post_action": False,
    }

    assert fila(ciclo, ultima)["ok"]


def test_una_escritura_vieja_no_vale_por_la_de_hoy():
    """
    EL FALLO QUE ESTA FILA DEBERIA HABER CAZADO SIEMPRE.

    Cuando el ciclo escribe pero no sabe nombrar lo que hizo,
    `last_execution` se cae al historial. La pantalla enseña
    entonces una escritura de otro dia bajo el titulo ESTE CICLO.
    """

    ciclo = {**CICLO_REAL, "action": None, "label": None}

    del_dia_anterior = {
        "action": "BUY_V10",
        "label": "Comprar",
        "write_performed": True,
        "success": True,
        "succeeded": True,
        "http_status": 200,
        "timestamp": "2026-08-22T18:56:00+00:00",
    }

    assert not fila(ciclo, del_dia_anterior)["ok"], (
        "una escritura de ayer esta pasando por la de este ciclo"
    )


def test_un_ciclo_que_no_escribio_no_da_la_alarma():
    """
    La mayoria de ciclos no escriben. Ninguno de ellos puede
    pintar la pantalla de rojo.
    """

    ciclo = {
        **CICLO_REAL,
        "write_used": False,
        "action": None,
        "label": None,
        "success": None,
        "http_status": None,
    }

    assert fila(ciclo, {})["ok"]


def test_la_guarda_ya_no_pide_status():
    """
    CANDADO ESTRUCTURAL.

    Que nadie vuelva a exigir `status` a secas para dar una
    escritura por contada: es un campo que solo rellenan algunas
    vias.
    """

    import ast
    import inspect

    from src.telemetry import dashboard_consistency

    codigo = inspect.getsource(
        dashboard_consistency.build_consistency_report
    )

    arbol = ast.parse(codigo.strip())

    asignaciones = [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "contada"
            for t in nodo.targets
        )
    ]

    assert asignaciones, (
        "ha desaparecido el calculo de `contada`"
    )

    fuente = ast.dump(asignaciones[0])

    assert "dice_como_acabo" in fuente, (
        "`contada` ha vuelto a mirar un campo suelto en vez del "
        "desenlace"
    )
    assert "es_de_este_ciclo" in fuente, (
        "se ha caido la comprobacion de que la escritura sea la "
        "de este ciclo"
    )


def main():

    pruebas = [
        test_el_caso_de_la_contraoferta,
        test_sin_nombre_no_cuenta,
        test_sin_desenlace_no_cuenta,
        test_un_fallo_tambien_esta_contado,
        test_una_escritura_vieja_no_vale_por_la_de_hoy,
        test_un_ciclo_que_no_escribio_no_da_la_alarma,
        test_la_guarda_ya_no_pide_status,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("La ultima escritura: contada de verdad.")


if __name__ == "__main__":
    main()
