"""
Una comparacion sin datos dice «no lo se», no «no mejora».

EL CASO, CON NOMBRE Y FACTURA (20/09/2026)

    El 18/09 los CUATRO `SIN_PRONOSTICO` del tablero eran
    porteros, y los cuatro por el mismo motivo: la vara de
    porteria era ESQUIVEL, comprado por la cesta a las 07:05 de
    esa misma mañana por 150.376 EUR, con 0 puntos y sin
    pronostico de titularidad.

    Entre los cuatro estaba DMITROVIC. El 20/09 lo compro el
    dueño a mano por 4.992.001 EUR.

POR QUE EN LA PORTERIA Y NO EN OTRO SITIO

    El sustituido es `min(titulares, key=points)`. Un jugador
    recien comprado en el suelo tiene 0 puntos, asi que gana
    siempre ese concurso — y es, a la vez, el unico sin
    pronostico. Las dos cosas son el mismo hecho.

    Con UN solo titular en la posicion no hay segunda opinion:
    ese jugador ES la vara, sin alternativa. El 18/09:
    POR 1 titular, DEF 3, MED 5, DEL 2.

LAS DOS CAUSAS NO SON LA MISMA

    · Sin pronostico DEL CANDIDATO: callarse es correcto. No
      sabemos nada de quien queremos meter.

    · Sin pronostico DE LA REFERENCIA: el candidato no es malo,
      es que no hay con que compararlo. Decir «no mejora» es
      afirmar algo que nadie ha comprobado.

    DOCTRINA 24, DEL REVES: el motor no pasa con las manos
    vacias, pero RECHAZA con las manos vacias.

LO QUE NO CAMBIA

    Las dos siguen valiendo CERO. A ciegas no se puja y el
    guardarrail del 17/08 se queda entero. Lo unico que cambia es
    que la segunda se VE, con el nombre de quien falta, y escala
    al panel en vez de morir como un «no».

    Medido sobre las dos fotos: el 18/09 cambian CUATRO
    decisiones y CERO valores; el 20/09 no cambia nada.

REGLA 23 Y DOCTRINA 24

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj:
    todo son fichas construidas aqui. Y si el caso que viene a
    mirar no se da —si los dos lados tienen datos, o si la
    posicion tiene mas de un titular— la guardia FALLA en vez de
    pasar.
"""

from __future__ import annotations

import os

from src.analysis.player_value_engine import (
    ENV_SIN_REFERENCIA,
    xi_upgrade_value,
)


MERCADO = {"rate_median": 21_486}


# La vara del 18/09: un portero comprado en el suelo esa mañana.
LA_VARA_CIEGA = {
    "name": "Esquivel",
    "probability": None,
    "hierarchy_value": None,
}


# Un candidato con todos sus datos: Dmitrovic, el que compro el
# dueño dos dias despues por 4.992.001 EUR.
EL_CANDIDATO = {
    "name": "Dmitrovic",
    "probability": 95.0,
    "hierarchy_value": 50,
}


def _valorar(replaced, candidate, encendido: bool) -> dict:
    """La valoracion del once, con el interruptor donde se diga."""

    antes = os.environ.get(ENV_SIN_REFERENCIA)

    try:
        os.environ[ENV_SIN_REFERENCIA] = "1" if encendido else "0"

        return xi_upgrade_value(
            candidate_points=182,
            replaced_points=0,
            points_market=MERCADO,
            confidence=0.85,
            candidate_starter=candidate,
            replaced_starter=replaced,
            replaced_in_lineup=True,
        )

    finally:

        if antes is None:
            os.environ.pop(ENV_SIN_REFERENCIA, None)

        else:
            os.environ[ENV_SIN_REFERENCIA] = antes


# ============================================================
# 1. EL CASO TIENE QUE DARSE
# ============================================================


def test_el_caso_que_vino_a_mirar_se_da() -> None:
    """
    Doctrina 24, aplicada a esta guardia. Si la vara tuviera
    datos, o el candidato no los tuviera, no habria nada que
    distinguir y todo pasaria.
    """

    assert LA_VARA_CIEGA.get("probability") is None, (
        "la vara de la prueba SI tiene pronostico: entonces no "
        "hay ceguera que mirar"
    )

    assert EL_CANDIDATO.get("probability") is not None, (
        "el candidato de la prueba NO tiene pronostico: entonces "
        "el veto salta por el otro lado y esto mide otra cosa"
    )


# ============================================================
# 2. SE DISTINGUE QUIEN FALTA
# ============================================================


def test_sin_pronostico_distingue_quien_falta() -> None:
    """
    LA PRUEBA QUE DA NOMBRE AL ENCARGO.

    Con la referencia sin datos y el candidato con ellos, la
    decision NO puede ser la misma que cuando el que no tiene
    datos es el candidato.
    """

    falta_la_vara = _valorar(
        LA_VARA_CIEGA, EL_CANDIDATO, encendido=True
    )

    falta_el_candidato = _valorar(
        {"name": "Dituro", "probability": 50.0,
         "hierarchy_value": 40},
        {"name": "Uno cualquiera", "probability": None},
        encendido=True,
    )

    assert falta_el_candidato["decision"] == "SIN_PRONOSTICO", (
        f"cuando el que no tiene datos es el CANDIDATO la "
        f"decision deberia seguir siendo SIN_PRONOSTICO y es "
        f"{falta_el_candidato['decision']}"
    )

    assert falta_la_vara["decision"] != falta_el_candidato[
        "decision"
    ], (
        f"las dos causas siguen saliendo con la misma etiqueta "
        f"({falta_la_vara['decision']}): «no lo se» y «no "
        f"mejora» vuelven a ser el mismo cero"
    )

    assert falta_la_vara["decision"] == "SIN_REFERENCIA", (
        f"la falta de referencia sale como "
        f"{falta_la_vara['decision']}"
    )

    # Doctrina 87: el motivo NOMBRA a quien falta.
    assert "Esquivel" in falta_la_vara["reason"], (
        f"el motivo no dice quien falta: "
        f"{falta_la_vara['reason']}"
    )

    assert "no mejora" not in falta_la_vara["reason"].lower(), (
        f"el motivo sigue afirmando que no mejora, que es "
        f"justo lo que nadie ha comprobado: "
        f"{falta_la_vara['reason']}"
    )


def test_no_desaparece_escala() -> None:
    """
    «Lo unico que no vale es que desaparezca.» Sube al panel con
    el nombre de quien falta.
    """

    salida = _valorar(
        LA_VARA_CIEGA, EL_CANDIDATO, encendido=True
    )

    assert salida.get("escala") is True, (
        "la falta de referencia no escala: el rechazo sigue "
        "siendo silencioso"
    )

    assert salida.get("escala_a") == "PANEL", (
        f"escala a {salida.get('escala_a')}, que no es donde el "
        f"dueño lo ve"
    )

    assert salida.get("falta") == "Esquivel", (
        f"no dice quien falta: {salida.get('falta')}"
    )


def test_a_ciegas_sigue_sin_pujarse() -> None:
    """
    Lo que NO cambia. El guardarrail del 17/08 entero: valor
    cero, en los dos casos y con el interruptor donde sea.

    Si esto se rompe, el arreglo ha abierto una compra a ciegas,
    que es lo contrario de lo que venia a hacer.
    """

    for encendido in (False, True):

        for replaced, candidate in (
            (LA_VARA_CIEGA, EL_CANDIDATO),
            (
                {"name": "Dituro", "probability": 50.0},
                {"name": "X", "probability": None},
            ),
        ):

            salida = _valorar(replaced, candidate, encendido)

            assert salida["value"] == 0, (
                f"con el interruptor "
                f"{'encendido' if encendido else 'apagado'} y "
                f"falta de pronostico, el valor es "
                f"{salida['value']} y no cero"
            )


# ============================================================
# 3. UNA POSICION CON UN SOLO TITULAR NO SE CIEGA
# ============================================================


# El once del 18/09, por posicion. La porteria con UNO.
TITULARES_EL_18 = {"POR": 1, "DEF": 3, "MED": 5, "DEL": 2}


def test_una_posicion_con_un_titular_no_se_ciega() -> None:
    """
    Con un solo titular en la posicion y ese recien comprado a 0
    puntos, un candidato CON pronostico sigue siendo evaluable:
    no sale como un rechazo, sale como una pregunta.

    Es el caso exacto del 18/09 y es el que descarta la opcion
    «en medio»: quitar a Esquivel de la vara no deja a nadie
    detras.
    """

    # Doctrina 24: si la posicion tuviera dos titulares, habria
    # alternativa y esta prueba no estaria mirando el caso.
    assert TITULARES_EL_18["POR"] == 1, (
        f"la posicion del caso tiene "
        f"{TITULARES_EL_18['POR']} titulares: con mas de uno hay "
        f"segunda opinion y el caso es otro"
    )

    assert max(TITULARES_EL_18.values()) > 1, (
        "todas las posiciones tienen un solo titular: el fixture "
        "no representa un once de verdad"
    )

    apagado = _valorar(
        LA_VARA_CIEGA, EL_CANDIDATO, encendido=False
    )

    encendido = _valorar(
        LA_VARA_CIEGA, EL_CANDIDATO, encendido=True
    )

    assert apagado["decision"] == "SIN_PRONOSTICO", (
        f"apagado deberia comportarse como antes y sale "
        f"{apagado['decision']}"
    )

    assert encendido["decision"] == "SIN_REFERENCIA", (
        f"encendido, el candidato con pronostico sigue saliendo "
        f"como {encendido['decision']}: se le sigue tratando "
        f"como si el problema fuera suyo"
    )

    assert encendido.get("escala"), (
        "el candidato de una posicion con un solo titular se "
        "sigue perdiendo: no escala a ninguna parte"
    )


# ============================================================
# 4. APAGADO, EXACTAMENTE COMO AYER
# ============================================================


def test_apagado_se_comporta_como_ayer() -> None:

    salida = _valorar(
        LA_VARA_CIEGA, EL_CANDIDATO, encendido=False
    )

    assert salida["decision"] == "SIN_PRONOSTICO"

    assert "del que saldria" in salida["reason"], (
        f"apagado, el motivo ha cambiado: {salida['reason']}"
    )

    assert "escala" not in salida, (
        "apagado, la salida trae campos nuevos: el "
        "comportamiento no es el de antes"
    )


def test_los_contadores_ven_la_etiqueta_nueva() -> None:
    """
    El dia que el veto hace el MISMO trabajo con otro nombre, un
    contador que solo conozca el nombre viejo baja sin que nadie
    haya dejado de bloquear nada. Ya paso el 17/08: de 12
    bloqueados a 5.
    """

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    for ruta, quien in (
        ("src/analysis/acquisition_board.py", "el tablero"),
        ("src/analysis/los_sentidos.py", "la alarma"),
        ("src/analysis/roster_expansion_shadow.py", "la sombra"),
    ):

        fuente = (raiz / ruta).read_text(encoding="utf-8")

        assert "SIN_REFERENCIA" in fuente, (
            f"{quien} ({ruta}) no conoce `SIN_REFERENCIA`: el "
            f"dia que se encienda el interruptor su contador "
            f"bajara sin que nadie bloquee menos"
        )


def main() -> int:

    pruebas = [
        test_el_caso_que_vino_a_mirar_se_da,
        test_sin_pronostico_distingue_quien_falta,
        test_no_desaparece_escala,
        test_a_ciegas_sigue_sin_pujarse,
        test_una_posicion_con_un_titular_no_se_ciega,
        test_apagado_se_comporta_como_ayer,
        test_los_contadores_ven_la_etiqueta_nueva,
    ]

    fallos = 0

    for prueba in pruebas:

        try:
            prueba()
            print(f"OK   {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {prueba.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL BUCLE DE LA VARA V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
