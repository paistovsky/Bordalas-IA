"""
Las jornadas se ordenan por su fecha, no por su numero.

LO QUE YA ESTABA BIEN, Y VA PRIMERO

    El marcador NO ordena por `round_id`: desde el 14/09 ordena
    por `primer_partido`. Lo que falla es de donde sale esa
    fecha.

EL CASO, CON NOMBRE Y FECHA

    `calendario_de_jornadas` tiene dos fuentes y las dos son
    ciegas a las jornadas aplazadas:

        · los PARTIDOS de la foto traen la fecha exacta por
          `round_id`, pero Biwenger solo publica los que quedan
          por jugar. De las nueve jornadas observadas, ocho no
          tienen ni un partido a la vista.

        · el CALENDARIO DE LALIGA va por NUMERO de jornada, asi
          que «Jornada 6» y «Jornada 6 (aplazada)» se llevan LA
          MISMA hora.

    Con el empate, el desempate es el `round_id` — y ahi vuelve
    a mandar el numero. Medido contra el tablon del 20/09:

        4937  Jornada 1 (aplazada)   de verdad 25/08
                                     el calendario dice 15/08
        5125  Jornada 6 (aplazada)   de verdad 15/09
                                     el calendario dice 03/09

    Esas dos son las dos parejas rotas: 4900 usaba como «foto de
    antes» la de 4937, que es POSTERIOR, y 4902 la de 5125.

LA FECHA EXACTA YA LA TENIAMOS

    `roundStarted` del tablon trae el `round_id` dentro. Cubre
    las nueve observadas y el fichero ya se carga cada vuelta.
    Doctrina 103.

REGLA 23, DOCTRINA 24 Y DOCTRINA 104

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj:
    el caso se construye aqui. No depende de que haya en el
    entorno: el interruptor se pone y se quita en cada prueba. Y
    si el caso no trajese ninguna jornada fuera de serie, la
    guardia FALLA en vez de pasar sin mirar nada.
"""

from __future__ import annotations

import os

from datetime import datetime, timezone

from src.analysis.marcador import (
    ENV_POR_SU_FECHA,
    calendario_de_jornadas,
    fechas_del_tablon,
    jornadas_por_su_fecha,
    orden_en_el_tiempo,
)


# ----------------------------------------------------------------
# LA LIGA DEL CASO
#
#     Tres jornadas, y la del medio es una aplazada con
#     identificador ALTO: el mismo dibujo que 4937 y 5125.
# ----------------------------------------------------------------

JORNADA_1 = 4899
APLAZADA = 4937          # se jugo DESPUES de la 2, con id mayor
JORNADA_2 = 4900


RONDAS = [
    {"id": JORNADA_1, "name": "Jornada 1"},
    {"id": JORNADA_2, "name": "Jornada 2"},
    {"id": APLAZADA, "name": "Jornada 1 (aplazada)"},
]


# El calendario de LaLiga, que solo conoce el NUMERO. Es la
# fuente que confunde a las dos «Jornada 1».
KICKOFF_DE_LALIGA = {
    1: "2026-08-15T19:30:00+02:00",
    2: "2026-08-20T21:00:00+02:00",
}


def _epoch(texto: str) -> int:
    return int(
        datetime.fromisoformat(texto)
        .astimezone(timezone.utc)
        .timestamp()
    )


# El tablon, que SI trae el `round_id` en cada evento.
EVENTOS = [
    {
        "type": "roundStarted",
        "date": _epoch("2026-08-15T17:30:00+00:00"),
        "content": {"round": {"id": JORNADA_1, "name": "Jornada 1"}},
    },
    {
        "type": "roundStarted",
        "date": _epoch("2026-08-20T19:00:00+00:00"),
        "content": {"round": {"id": JORNADA_2, "name": "Jornada 2"}},
    },
    {
        "type": "roundStarted",
        "date": _epoch("2026-08-25T19:00:00+00:00"),
        "content": {
            "round": {
                "id": APLAZADA,
                "name": "Jornada 1 (aplazada)",
                "part": 2,
            }
        },
    },
    # Un duplicado, que el tablon los trae: no puede mover nada.
    {
        "type": "roundStarted",
        "date": _epoch("2026-08-25T21:00:00+00:00"),
        "content": {
            "round": {"id": APLAZADA, "name": "Jornada 1 (aplazada)"}
        },
    },
    # Y un evento de otra clase, que no se mira.
    {
        "type": "transfer",
        "date": _epoch("2026-08-26T10:00:00+00:00"),
        "content": [{"player": 1, "amount": 100}],
    },
]


OBSERVADAS = [
    {"round_id": JORNADA_1},
    {"round_id": JORNADA_2},
    {"round_id": APLAZADA},
]


def _con(encendido: bool, fn):
    """Corre `fn` con el interruptor donde toque. Doctrina 104.

    Para «apagado» se BORRA la variable, no se pone a "0": es
    el estado que de verdad tiene una maquina limpia. Que las
    dos signifiquen lo mismo se mide en
    `test_apagado_el_calendario_es_el_de_ayer`.
    """

    antes = os.environ.get(ENV_POR_SU_FECHA)

    try:

        if encendido:
            os.environ[ENV_POR_SU_FECHA] = "1"
        else:
            os.environ.pop(ENV_POR_SU_FECHA, None)

        return fn()

    finally:

        if antes is None:
            os.environ.pop(ENV_POR_SU_FECHA, None)
        else:
            os.environ[ENV_POR_SU_FECHA] = antes


def _calendario(encendido: bool) -> dict:
    return _con(
        encendido,
        lambda: calendario_de_jornadas(
            RONDAS,
            partidos=None,
            kickoff_por_jornada=KICKOFF_DE_LALIGA,
            eventos=EVENTOS,
        ),
    )


def _orden(encendido: bool) -> list:

    calendario = _calendario(encendido)

    colocadas = orden_en_el_tiempo(OBSERVADAS, calendario)

    return [
        item["jornada"]["round_id"]
        for item in colocadas["ordenadas"]
    ]


# ============================================================
# 1. EL CASO TIENE QUE TRAER UNA JORNADA FUERA DE SERIE
# ============================================================


def test_sin_jornada_fuera_de_serie_no_se_comprueba_nada() -> None:
    """
    Doctrina 24. Si todos los identificadores van en el mismo
    orden que las fechas, ordenar por una cosa o por la otra da
    igual y la prueba de abajo no comprueba nada.
    """

    assert APLAZADA > JORNADA_2, (
        f"la jornada aplazada tiene identificador {APLAZADA}, "
        f"menor que el de la jornada {JORNADA_2}: no rompe el "
        f"orden y el caso no prueba nada"
    )

    del_tablon = fechas_del_tablon(EVENTOS)

    assert (
        del_tablon[APLAZADA]["momento"]
        > del_tablon[JORNADA_2]["momento"]
    ), (
        "en el caso, la aplazada no se juega despues que la "
        "jornada 2: entonces el identificador alto no contradice "
        "a la fecha y no hay nada que arreglar"
    )

    # Y la fuente vieja tiene que confundirlas de verdad, o el
    # arreglo estaria arreglando algo que no pasa.
    viejo = _calendario(False)

    assert (
        viejo[APLAZADA]["primer_partido"]
        == viejo[JORNADA_1]["primer_partido"]
    ), (
        "el calendario de LaLiga no le esta dando a la aplazada "
        "la misma hora que a su hermana: el caso no reproduce el "
        "fallo del 20/09"
    )


# ============================================================
# 2. LA PRUEBA QUE DA NOMBRE AL FICHERO
# ============================================================


def test_las_jornadas_se_ordenan_por_su_fecha_no_por_su_numero() -> None:
    """
    Con una jornada aplazada de identificador alto metida en
    medio, la resta no usa como anterior una foto posterior.
    """

    puesto = _orden(True)

    assert puesto == [JORNADA_1, JORNADA_2, APLAZADA], (
        f"con el interruptor puesto el orden es {puesto} y las "
        f"fechas dicen {[JORNADA_1, JORNADA_2, APLAZADA]}"
    )

    # Y dicho como lo que importa: la previa de cada una tiene
    # que ser ANTERIOR en el tiempo, no solo distinta.
    calendario = _calendario(True)

    anterior = None

    for round_id in puesto:

        momento = calendario[round_id]["primer_partido"]

        if anterior is not None:

            assert momento > anterior, (
                f"la jornada {round_id} se coloca detras de una "
                f"foto POSTERIOR: {momento} va antes que "
                f"{anterior}"
            )

        anterior = momento

    # La fuente queda escrita: una hora de respaldo y una
    # medida no son lo mismo (regla 18).
    assert (
        calendario[APLAZADA]["fuente"] == "EVENTOS_DEL_TABLON"
    ), (
        f"la hora de la aplazada sale de "
        f"{calendario[APLAZADA]['fuente']}, no del tablon"
    )


# ============================================================
# 3. SIN EL ARREGLO, EL FALLO ESTA AHI
# ============================================================


def test_apagado_la_aplazada_se_cuela_donde_no_va() -> None:
    """
    La otra mitad de la doctrina 24: si apagado tambien saliera
    bien, esta guardia no estaria midiendo el arreglo.
    """

    apagado = _orden(False)

    assert apagado != [JORNADA_1, JORNADA_2, APLAZADA], (
        "apagado el orden ya es el correcto: entonces el "
        "interruptor no arregla nada y la prueba de arriba pasa "
        "por casualidad"
    )

    assert apagado.index(APLAZADA) < apagado.index(JORNADA_2), (
        f"apagado, la aplazada no se cuela delante de la jornada "
        f"{JORNADA_2}: el orden es {apagado}"
    )


# ============================================================
# 4. APAGADO, EXACTAMENTE COMO AYER
# ============================================================


def test_apagado_el_calendario_es_el_de_ayer() -> None:

    # LO APAGA ESTA GUARDIA, NO EL ENTORNO (doctrina 104).
    #
    #     Antes esta linea comprobaba que el interruptor no
    #     estuviese puesto fuera. La noche que se encendio uno
    #     en el `env` del workflow, la guardia hermana se puso
    #     roja y el ciclo no arranco.
    #
    #     De paso se mide lo que decide si borrarlo basta: que
    #     el lector siga al entorno DESPUES del import.
    assert _con(False, jornadas_por_su_fecha) is False, (
        "con la variable borrada, el lector sigue diciendo que "
        "el interruptor esta puesto: o lo cachea al importarse, "
        "o lo lee de otro sitio"
    )

    assert _con(True, jornadas_por_su_fecha) is True, (
        "con la variable puesta a \"1\" el lector sigue diciendo "
        "que esta apagado: cachea el valor y esta guardia no "
        "controla nada"
    )

    # Y que "0" signifique lo mismo que borrada, que es lo que
    # permite escribir una por la otra.
    antes = os.environ.get(ENV_POR_SU_FECHA)

    try:
        os.environ[ENV_POR_SU_FECHA] = "0"

        assert not jornadas_por_su_fecha(), (
            "\"0\" no significa apagado para el lector"
        )

    finally:

        if antes is None:
            os.environ.pop(ENV_POR_SU_FECHA, None)
        else:
            os.environ[ENV_POR_SU_FECHA] = antes

    sin_eventos = _con(
        False,
        lambda: calendario_de_jornadas(
            RONDAS,
            partidos=None,
            kickoff_por_jornada=KICKOFF_DE_LALIGA,
        ),
    )

    con_eventos = _calendario(False)

    assert sin_eventos == con_eventos, (
        "apagado, pasar los eventos del tablon cambia el "
        "calendario: el interruptor no esta apagado del todo"
    )

    for fila in con_eventos.values():
        assert fila.get("fuente") != "EVENTOS_DEL_TABLON", (
            f"apagado, la jornada {fila['round_id']} ya toma la "
            f"hora del tablon"
        )


# ============================================================
# 5. EL TABLON, LEIDO CON CUIDADO
# ============================================================


def test_del_tablon_se_lee_el_arranque_y_no_se_duplica() -> None:

    del_tablon = fechas_del_tablon(EVENTOS)

    assert set(del_tablon) == {JORNADA_1, JORNADA_2, APLAZADA}, (
        f"del tablon salen las jornadas {sorted(del_tablon)}: o "
        f"se ha colado un evento que no es una jornada, o falta "
        f"alguna"
    )

    # El duplicado de la aplazada es dos horas mas tarde: se
    # queda el primero.
    assert del_tablon[APLAZADA]["momento"] == datetime(
        2026, 8, 25, 19, 0, tzinfo=timezone.utc
    ), (
        f"el duplicado ha movido la aplazada a "
        f"{del_tablon[APLAZADA]['momento']}"
    )

    assert del_tablon[APLAZADA]["part"] == 2, (
        "el `part` con el que Biwenger marca la mitad aplazada "
        "no viaja: es lo que explica por que esa fila existe"
    )

    # Y nunca lanza, pase lo que pase por la puerta.
    for basura in (None, [], [None], [{"type": "roundStarted"}]):
        assert fechas_del_tablon(basura) == {}, (
            f"con {basura!r} el tablon devuelve algo que no es "
            f"un diccionario vacio"
        )


def main() -> int:

    pruebas = [
        test_sin_jornada_fuera_de_serie_no_se_comprueba_nada,
        test_las_jornadas_se_ordenan_por_su_fecha_no_por_su_numero,
        test_apagado_la_aplazada_se_cuela_donde_no_va,
        test_apagado_el_calendario_es_el_de_ayer,
        test_del_tablon_se_lee_el_arranque_y_no_se_duplica,
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
        f"EL MARCADOR POR SU FECHA V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
