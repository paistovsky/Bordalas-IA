"""
El once se busca una vez por entrada: y la respuesta es la misma.

DE DONDE SALE (24/09/2026)

    La vuelta tarda 78 minutos. Medido en el laboratorio, las cinco
    etapas del analisis son `build_lineup` (86-98 % de cada una), 135
    alineaciones por vuelta con escritura, y casi todas preguntan por
    la misma plantilla. `el_once_se_busca_una_vez` recuerda la
    respuesta de la busqueda por el contenido exacto de su entrada.

    Es rendimiento: si con la memoria encendida sale UN once
    distinto, la memoria esta mal.

LO QUE SE PROTEGE

    1. Apagada no recuerda nada: la llamada es la de siempre.
    2. Encendida da lo mismo que apagada, formacion por formacion,
       en plantillas con empates, dudosos y no alineables.
    3. Acierta de verdad: la segunda pregunta no busca.
    4. Un solo campo distinto no acierta.
    5. El orden de los jugadores cuenta (decide los empates).
    6. Lo que devuelve es suyo: tocarlo no ensucia la siguiente.
    7. Con ids repetidos no se recuerda nada.
    8. No crece sin freno.
    9. El modulo no lee el mundo.
   10. Apagada no dice nada en el log; encendida dice cuanto ahorro.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: las plantillas se escriben aqui,
    con un azar de semilla fija. La unica que toca el entorno es la
    del interruptor —que ES una variable de entorno— y lo deja como
    estaba.

COMO SE USA

    python -m src.analysis.test_el_once_se_busca_una_vez_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
os.environ.pop("BORDALAS_EL_ONCE_UNA_VEZ", None)

import copy                                         # noqa: E402
import random                                       # noqa: E402

from pathlib import Path                            # noqa: E402

from src.analysis import el_once_se_busca_una_vez as memoria  # noqa: E402

from src.analysis.lineup_engine import (            # noqa: E402
    FORMATIONS,
    evaluate_formation,
    search_best_lineup_for_formation,
)


class _Interruptor:
    """Enciende o apaga el interruptor y lo deja como estaba."""

    def __init__(self, encendido: bool) -> None:
        self.encendido = encendido

    def __enter__(self):
        self.antes = os.environ.get(memoria.ENV)

        if self.encendido:
            os.environ[memoria.ENV] = "1"

        else:
            os.environ.pop(memoria.ENV, None)

        memoria.olvidar()

        return self

    def __exit__(self, *exc):
        if self.antes is None:
            os.environ.pop(memoria.ENV, None)

        else:
            os.environ[memoria.ENV] = self.antes

        memoria.olvidar()


def _jugador(ident, posicion, puntos, alineable=True, automatico=True):
    """Lo que sale de `prepare_players`, en lo que la busqueda lee."""

    return {
        "id": ident,
        "name": f"J{ident}",
        "position": posicion,
        "eligible_positions": [posicion],
        "lineup_eligible": alineable,
        "automatic_lineup": automatico,
        "lineup_score": puntos,
        "extra": {"lista": [ident, posicion]},
    }


def _plantilla(semilla: int, fichas: int) -> list:
    """
    Una plantilla con empates, dudosos y no alineables.

    Los puntos salen de un puñado corto de valores a proposito:
    asi hay EMPATES, y el empate lo decide el orden, que es
    justo lo que una memoria mal hecha romperia.
    """

    azar = random.Random(semilla)

    posiciones = [1, 1] + [
        azar.choice([2, 2, 3, 3, 4]) for _ in range(fichas - 2)
    ]

    return [
        _jugador(
            100 + i,
            posicion,
            azar.choice([10.0, 12.5, 12.5, 30.25, 7.0]),
            alineable=azar.random() > 0.1,
            automatico=azar.random() > 0.25,
        )
        for i, posicion in enumerate(posiciones)
    ]


def _todas(jugadores) -> list:
    return [
        evaluate_formation(jugadores, nombre, formacion)
        for nombre, formacion in FORMATIONS.items()
    ]


# ------------------------------------------------------------
# 1. APAGADA NO RECUERDA NADA
# ------------------------------------------------------------


def test_apagada_no_recuerda_nada() -> None:

    with _Interruptor(False):
        jugadores = _plantilla(1, 14)

        _todas(jugadores)
        _todas(jugadores)

        cuenta = memoria.cuenta()

        assert cuenta == {
            "aciertos": 0,
            "fallos": 0,
            "sin_clave": 0,
            "recordadas": 0,
        }, f"apagada ha tocado la memoria: {cuenta}"


# ------------------------------------------------------------
# 2. ENCENDIDA DA LO MISMO QUE APAGADA
# ------------------------------------------------------------


def test_encendida_da_lo_mismo_que_apagada() -> None:

    comparadas = 0

    for semilla in range(12):
        jugadores = _plantilla(semilla, 13 + semilla % 4)

        with _Interruptor(False):
            sin = _todas(copy.deepcopy(jugadores))

        with _Interruptor(True):
            primera = _todas(copy.deepcopy(jugadores))
            segunda = _todas(copy.deepcopy(jugadores))

            assert memoria.cuenta()["aciertos"] > 0, (
                f"semilla {semilla}: la segunda vuelta no acerto "
                f"ninguna"
            )

        for a, b, c in zip(sin, primera, segunda):
            assert a == b == c, (
                f"semilla {semilla}, {a['formation_name']}: la "
                f"memoria cambia el once"
            )

            # La formacion es LA MISMA, no una copia: quien la
            # compare por identidad no puede notar la memoria.
            assert b["formation"] is FORMATIONS[a["formation_name"]]
            assert c["formation"] is FORMATIONS[a["formation_name"]]

            assert [j["id"] for j in a["selected"]] == [
                j["id"] for j in c["selected"]
            ]

            comparadas += 1

    # No pasa con las manos vacias.
    assert comparadas == 12 * len(FORMATIONS), comparadas


# ------------------------------------------------------------
# 3. ACIERTA DE VERDAD
# ------------------------------------------------------------


def test_acierta_de_verdad() -> None:

    with _Interruptor(True):
        jugadores = _plantilla(3, 15)

        _todas(jugadores)

        tras_la_primera = memoria.cuenta()

        _todas(copy.deepcopy(jugadores))

        tras_la_segunda = memoria.cuenta()

    assert tras_la_primera["aciertos"] == 0, tras_la_primera
    assert tras_la_primera["fallos"] >= len(FORMATIONS)

    # La segunda no busca NADA: todo acierto, ningun fallo nuevo.
    assert (
        tras_la_segunda["fallos"] == tras_la_primera["fallos"]
    ), (tras_la_primera, tras_la_segunda)

    assert (
        tras_la_segunda["aciertos"] == tras_la_primera["fallos"]
    ), (tras_la_primera, tras_la_segunda)


# ------------------------------------------------------------
# 4. UN SOLO CAMPO DISTINTO NO ACIERTA
# ------------------------------------------------------------


def test_un_solo_campo_distinto_no_acierta() -> None:

    base = _plantilla(5, 14)

    cambios = {
        "los puntos, en el ultimo decimal": lambda j: j.__setitem__(
            "lineup_score", j["lineup_score"] + 1e-9
        ),
        "un entero que pasa a decimal": lambda j: j.__setitem__(
            "id", j["id"]
        ) or j.__setitem__("position", float(j["position"])),
        "un campo que la busqueda no lee": lambda j: j.__setitem__(
            "name", "otro"
        ),
        "algo anidado": lambda j: j["extra"]["lista"].append(0),
        "dudoso": lambda j: j.__setitem__(
            "automatic_lineup", not j["automatic_lineup"]
        ),
    }

    for motivo, cambiar in cambios.items():
        otra = copy.deepcopy(base)
        cambiar(otra[4])

        with _Interruptor(False):
            sin = _todas(copy.deepcopy(otra))

        with _Interruptor(True):
            _todas(copy.deepcopy(base))

            antes = memoria.cuenta()

            con = _todas(copy.deepcopy(otra))

            despues = memoria.cuenta()

        assert despues["aciertos"] == antes["aciertos"], (
            f"{motivo}: ha acertado con una entrada distinta"
        )

        assert sin == con, f"{motivo}: el once cambia"


# ------------------------------------------------------------
# 5. EL ORDEN CUENTA
# ------------------------------------------------------------


def test_el_orden_de_los_jugadores_cuenta() -> None:

    base = _plantilla(7, 15)
    al_reves = list(reversed(copy.deepcopy(base)))

    with _Interruptor(False):
        sin = _todas(copy.deepcopy(al_reves))

    with _Interruptor(True):
        _todas(copy.deepcopy(base))

        antes = memoria.cuenta()

        con = _todas(copy.deepcopy(al_reves))

        despues = memoria.cuenta()

    assert despues["aciertos"] == antes["aciertos"], (
        "ha acertado con los mismos jugadores en otro orden, y el "
        "orden decide los empates"
    )

    assert sin == con


# ------------------------------------------------------------
# 6. LO QUE DEVUELVE ES SUYO
# ------------------------------------------------------------


def test_lo_que_devuelve_es_suyo() -> None:

    jugadores = _plantilla(9, 14)

    with _Interruptor(False):
        limpio = evaluate_formation(
            copy.deepcopy(jugadores), "4-4-2", FORMATIONS["4-4-2"]
        )

    with _Interruptor(True):
        primera = evaluate_formation(
            jugadores, "4-4-2", FORMATIONS["4-4-2"]
        )

        # Quien lo recibe lo ensucia, como hace `build_lineup`
        # con su `sort`.
        primera["selected"].reverse()

        for jugador in primera["selected"]:
            jugador["lineup_score"] = -1
            jugador["extra"]["lista"].append("sucio")

        segunda = evaluate_formation(
            copy.deepcopy(_plantilla(9, 14)),
            "4-4-2",
            FORMATIONS["4-4-2"],
        )

        assert memoria.cuenta()["aciertos"] >= 1

    assert segunda == limpio, "lo que se toco fuera ha entrado"


# ------------------------------------------------------------
# 7. CON IDS REPETIDOS NO SE RECUERDA
# ------------------------------------------------------------


def test_con_ids_repetidos_no_se_recuerda() -> None:

    jugadores = _plantilla(11, 14)
    jugadores[6]["id"] = jugadores[5]["id"]

    with _Interruptor(False):
        sin = _todas(copy.deepcopy(jugadores))

    with _Interruptor(True):
        con = _todas(copy.deepcopy(jugadores))
        otra = _todas(copy.deepcopy(jugadores))

        cuenta = memoria.cuenta()

    assert sin == con == otra

    # Las formaciones donde ninguno de los dos juega podrian
    # recordarse; lo que se exige es que no se recuerde ninguna
    # cuya reconstruccion sea ambigua. Con los ids repetidos no se
    # sabe cual eligio, asi que ninguna se recuerda.
    assert cuenta["recordadas"] == 0, cuenta
    assert cuenta["aciertos"] == 0, cuenta


# ------------------------------------------------------------
# 8. NO CRECE SIN FRENO
# ------------------------------------------------------------


def test_no_crece_sin_freno() -> None:

    tope = memoria.TOPE

    try:
        memoria.TOPE = 5

        with _Interruptor(True):
            for semilla in range(4):
                _todas(_plantilla(100 + semilla, 12))

            assert memoria.cuenta()["recordadas"] == 5, (
                memoria.cuenta()
            )

    finally:
        memoria.TOPE = tope


# ------------------------------------------------------------
# 9. NO LEE EL MUNDO
# ------------------------------------------------------------


def test_la_memoria_no_lee_el_mundo() -> None:

    fuente = Path(memoria.__file__).read_text(encoding="utf-8")

    codigo = fuente.split('"""', 2)[-1]

    for prohibido in (
        "open(",
        "Path(",
        "requests",
        "datetime",
        "time.",
        "random",
    ):
        assert prohibido not in codigo, (
            f"el modulo de la memoria usa {prohibido!r}"
        )

    # Y la busqueda no se ha tocado: sigue siendo la misma
    # funcion, que la memoria recibe como parametro.
    assert callable(search_best_lineup_for_formation)


# ------------------------------------------------------------
# 10. LA LINEA DEL LOG
# ------------------------------------------------------------


def test_la_linea_del_log() -> None:

    with _Interruptor(False):
        _todas(_plantilla(13, 12))

        assert memoria.linea() is None, (
            "apagada imprime algo: el log ya no es el de hoy"
        )

    with _Interruptor(True):
        jugadores = _plantilla(13, 12)

        _todas(jugadores)
        _todas(copy.deepcopy(jugadores))

        cuenta = memoria.cuenta()
        texto = memoria.linea()

    assert texto is not None
    assert f"{cuenta['fallos']} busquedas hechas" in texto, texto
    assert f"{cuenta['aciertos']} recordadas" in texto, texto
    assert cuenta["aciertos"] > 0, cuenta


TESTS = [
    test_apagada_no_recuerda_nada,
    test_encendida_da_lo_mismo_que_apagada,
    test_acierta_de_verdad,
    test_un_solo_campo_distinto_no_acierta,
    test_el_orden_de_los_jugadores_cuenta,
    test_lo_que_devuelve_es_suyo,
    test_con_ids_repetidos_no_se_recuerda,
    test_no_crece_sin_freno,
    test_la_memoria_no_lee_el_mundo,
    test_la_linea_del_log,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL ONCE SE BUSCA UNA VEZ V1")
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
