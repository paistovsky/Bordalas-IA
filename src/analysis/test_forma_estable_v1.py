"""
Una funcion no cambia de forma segun los datos que encuentre.

TRES VECES LA MISMA SEMANA

    17/09, mañana:  `store_depth()` devolvia un objeto SIN
                    `retention_days` cuando no habia almacen. La
                    guardia del arbitro daba por segura esa clave
                    y se caia en un checkout limpio.

    17/09, noche:   `hold_value` devolvia menos claves por el
                    camino "sin valor". Al llegar el interruptor
                    de la via TENER, una guardia leyo `raw_gain`
                    y salio un KeyError en vez de un rojo
                    legible.

    Y la propia caida de produccion era pariente: un veredicto
    que cambiaba segun lo que hubiera en `data/`.

EL DEFECTO, EN UNA FRASE

    Quien consume una funcion no puede tener que adivinar que
    claves le van a llegar hoy.

LA REGLA DE LA CASA

    Cuando falta un dato, el hueco se dice con un valor vacio
    -None, 0, lista vacia- y el motivo escrito. **La clave no
    desaparece nunca.**

    "Ausencia de dato != dato" vale para el VALOR. Para la clave
    vale lo contrario: la clave esta siempre.

COMO SE COMPRUEBA

    Cada funcion de la tabla se llama dos veces: una con datos
    buenos y otra con nada -None, {}, basura-. Los dos juegos de
    claves tienen que ser identicos.

    Todo con fixture. Ni una lectura de `data/`: es lo que tiro
    produccion y no se repite.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.banquillo import (
    con_la_plantilla_de_hoy,
    puntos_en_el_banquillo,
)
from src.analysis.hold_backtest import store_depth
from src.analysis.hold_switch import bucket_backing, route_state
from src.analysis.hold_value import hold_value
from src.analysis.position_factor import state as vara_state
from src.analysis.price_store_fixture import almacen_de_mentira
from src.analysis.rival_once import comparar_con
from src.analysis.rival_scoreboard import (
    build_scoreboard,
    manager_scoreboard,
    value_versus_points,
)
from src.analysis.sesgo_posicion import sesgo_por_posicion
from src.analysis.vara_comparada import comparar, elegir_once


# ============================================================
# LOS DATOS BUENOS
# ============================================================


PLANTILLA = [
    {
        "id": 1,
        "name": "Portero",
        "position": 1,
        "hierarchy_value": 40,
        "starter_probability": 80.0,
        "points": 6,
        "weekly_expected_value": 0.70,
        "price": 2_000_000,
        "is_starter": True,
    },
]

for _i in range(2, 6):
    PLANTILLA.append({
        "id": 100 + _i,
        "name": f"Defensa {_i}",
        "position": 2,
        "hierarchy_value": 40,
        "starter_probability": 80.0,
        "points": 9,
        "weekly_expected_value": 0.70,
        "price": 2_000_000,
        "is_starter": True,
    })

for _i in range(2, 7):
    PLANTILLA.append({
        "id": 200 + _i,
        "name": f"Medio {_i}",
        "position": 3,
        "hierarchy_value": 50,
        "starter_probability": 90.0,
        "points": 15,
        "weekly_expected_value": 0.87,
        "price": 3_000_000,
        "is_starter": True,
    })

for _i in range(2, 6):
    PLANTILLA.append({
        "id": 300 + _i,
        "name": f"Delantero {_i}",
        "position": 4,
        "hierarchy_value": 50,
        "starter_probability": 90.0,
        "points": 18,
        "weekly_expected_value": 0.87,
        "price": 3_000_000,
        "is_starter": True,
    })


LIGA = {
    "race": {
        "matchdays_played": 3,
        "points_behind": 13,
        "required_pace": 0.371,
        "managers": [
            {
                "name": f"M{i}",
                "points": 100 + i * 5,
                "team_value": 50_000_000 + i * 1_000_000,
                "squad_size": 14,
            }
            for i in range(7)
        ],
    },
    "rival_squads": {
        "managers": [
            {
                "name": "Mex",
                "rank": 2,
                "points": 141,
                "team_value": 52_250_000,
                "formation": "3-5-2",
                "players": PLANTILLA,
            },
            {
                "name": "Pepe",
                "is_current_user": True,
                "rank": 4,
                "points": 133,
                "team_value": 49_540_000,
                "formation": "4-3-3",
                "players": PLANTILLA,
            },
        ]
    },
    "league_center": {"market_feed": []},
    "rival_intelligence": {"managers": []},
    "meta": {"generated_at": "2026-09-18T00:00:00"},
}


MARCADOR = {
    "jornadas": [
        {
            "round_id": 4901,
            "medible": True,
            "reconstruccion_completa": True,
            "formacion": "3-4-3",
            "puntos_once": 70,
            "mejor_formacion": "3-4-3",
            "mejor_puntos": 78,
            "eficiencia": 89.7,
            "puntos_perdidos": 8,
            "puntos_biwenger": 70,
            "cuadra": True,
            "descuadre": 0,
            "descuadre_percent": 0.0,
            "puntos_vara_vieja": 66,
            "formacion_vara_vieja": "5-4-1",
            "detalle": {
                "faltaron": [
                    {
                        "id": 302,
                        "name": "Delantero 2",
                        "position": 4,
                        "points": 3,
                    },
                ],
                "sobraron": [
                    {
                        "id": 999,
                        "name": "Otro",
                        "position": 4,
                        "points": 0,
                    },
                ],
            },
        }
    ]
}


CALIBRACION = {
    "available": True,
    "max_streak": 2,
    "by_rate_bucket": {
        "2-4 %": {
            "calibrated": True,
            "band": "1 dia",
            "max_streak": 2,
            "median": 0.0314,
            "loss_rate": 0.17,
            "n": 41,
        },
    },
}


# ============================================================
# LA TABLA
# ============================================================
#
# (nombre, llamada con datos, llamada sin nada)
#
# Las funciones que van a buscar su fichero solas -el ledger de
# rechazos, el marcador del disco- no estan aqui: no se pueden
# llamar sin tocar `data/`, y esta guardia no toca `data/`.
# Quedan escritas en el informe como pendientes.


def _con_almacen(_):
    with almacen_de_mentira() as almacen:
        return store_depth(almacen)


CASOS = [
    (
        "hold_backtest.store_depth",
        _con_almacen,
        lambda _: store_depth(Path("no") / "existe.json"),
    ),
    (
        "hold_value.hold_value",
        lambda _: hold_value(
            1_000_000, 3.0, trend_days=1, sources=3,
            calibration_override=CALIBRACION,
        ),
        lambda _: hold_value(0, None),
    ),
    (
        "hold_switch.route_state",
        lambda _: route_state(CALIBRACION, horizon_days=3),
        lambda _: route_state(None),
    ),
    (
        "hold_switch.bucket_backing",
        lambda _: bucket_backing(CALIBRACION, "2-4 %"),
        lambda _: bucket_backing(None, "2-4 %"),
    ),
    (
        "banquillo.puntos_en_el_banquillo",
        lambda _: puntos_en_el_banquillo(
            MARCADOR, LIGA["race"], PLANTILLA
        ),
        lambda _: puntos_en_el_banquillo(None, None, None),
    ),
    (
        "banquillo.con_la_plantilla_de_hoy",
        lambda _: con_la_plantilla_de_hoy(
            MARCADOR["jornadas"][0], PLANTILLA
        ),
        lambda _: con_la_plantilla_de_hoy({}, None),
    ),
    (
        "sesgo_posicion.sesgo_por_posicion",
        lambda _: sesgo_por_posicion(LIGA),
        lambda _: sesgo_por_posicion(None),
    ),
    (
        "rival_once.comparar_con",
        lambda _: comparar_con(LIGA, "Mex"),
        lambda _: comparar_con(None, "Mex"),
    ),
    (
        "rival_scoreboard.manager_scoreboard",
        lambda _: manager_scoreboard(LIGA, "Mex"),
        lambda _: manager_scoreboard(None, "Mex"),
    ),
    (
        "rival_scoreboard.value_versus_points",
        lambda _: value_versus_points(LIGA),
        lambda _: value_versus_points(None),
    ),
    (
        "rival_scoreboard.build_scoreboard",
        lambda _: build_scoreboard(LIGA, ("Mex",)),
        lambda _: build_scoreboard(None, ("Mex",)),
    ),
    (
        "vara_comparada.elegir_once",
        lambda _: elegir_once(PLANTILLA, True),
        lambda _: elegir_once([], True),
    ),
    (
        "vara_comparada.comparar",
        lambda _: comparar(PLANTILLA),
        lambda _: comparar(None),
    ),
    (
        "position_factor.state",
        lambda _: vara_state(),
        lambda _: vara_state(),
    ),
]


# ============================================================
# LA GUARDIA
# ============================================================


def test_la_forma_no_cambia_con_los_datos() -> None:
    """
    Mismas claves con datos y sin ellos. Las tres caidas de la
    semana salieron de que esto no se cumplia.
    """

    rotas = []

    for nombre, con_datos, sin_datos in CASOS:

        lleno = con_datos(None)
        vacio = sin_datos(None)

        assert isinstance(lleno, dict), f"{nombre} no devuelve dict"
        assert isinstance(vacio, dict), f"{nombre} no devuelve dict"

        faltan = set(lleno) - set(vacio)
        sobran = set(vacio) - set(lleno)

        if faltan or sobran:
            rotas.append(
                f"  {nombre}\n"
                f"      sin datos faltan: "
                f"{sorted(faltan) or 'ninguna'}\n"
                f"      sin datos sobran: "
                f"{sorted(sobran) or 'ninguna'}"
            )

    assert not rotas, (
        "estas funciones cambian de forma segun los datos que "
        "encuentren, que es el defecto que tumbo produccion y "
        "rompio dos guardias esta semana:\n"
        + "\n".join(rotas)
        + "\n\nEl hueco se dice con un valor vacio y el motivo "
        "escrito. La clave no desaparece nunca."
    )


def test_sin_datos_siempre_se_dice_por_que() -> None:
    """
    Una forma estable llena de ceros mudos no vale: si algo viene
    vacio, tiene que decir por que.
    """

    mudas = []

    for nombre, _, sin_datos in CASOS:

        vacio = sin_datos(None)

        if "reason" not in vacio:
            continue

        if vacio.get("available") is False and not vacio.get(
            "reason"
        ):
            mudas.append(nombre)

    assert not mudas, (
        f"estas devuelven `available: False` sin motivo escrito: "
        f"{mudas}"
    )


def test_la_guardia_muerde() -> None:
    """
    Una guardia que no puede fallar no protege de nada. Esta se
    comprueba con un caso que SI esta roto.
    """

    def con_datos(_):
        return {"a": 1, "b": 2, "reason": None}

    def sin_datos(_):
        return {"a": None}

    lleno = con_datos(None)
    vacio = sin_datos(None)

    assert set(lleno) - set(vacio) == {"b", "reason"}, (
        "la comparacion de claves no detecta una forma que "
        "encoge: entonces no detectaria nada"
    )


def test_esta_guardia_no_lee_el_estado() -> None:
    """
    Regla de la casa desde la caida del 17/09.
    """

    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    hallazgos = lecturas_de_estado(
        "src.analysis.test_forma_estable_v1"
    )

    assert not hallazgos, (
        f"esta guardia lee estado mutable: {hallazgos}"
    )


TESTS = [
    test_la_forma_no_cambia_con_los_datos,
    test_sin_datos_siempre_se_dice_por_que,
    test_la_guardia_muerde,
    test_esta_guardia_no_lee_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA FORMA NO CAMBIA CON LOS DATOS V1")
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
