"""
LA VARA V1 - los factores por posicion, aplicados de verdad.

SINTOMA (medido el 17/09/2026)

    Con la MISMA marca de la vara que ordena el once, cada linea
    entregaba esto por jornada:

        Medio       8,51 puntos por unidad de vara   (n=29)
        Delantero   8,44                             (n=18)
        Defensa     5,82                             (n=27)

    Un medio, 1,46 veces lo que un defensa. La vara los trataba
    como iguales.

CAUSA

    `weekly_expected_value` es jerarquia x probabilidad de ser
    titular. Ni una de las dos senales sabe en que linea juega el
    jugador, y en un fantasy con esta puntuacion el que ataca
    puntua mas que el que defiende.

CONSECUENCIA

    El motor, obediente, alineaba defensas: el once salia 5-4-1
    con Kiko Femenia -0 puntos- de titular y dos delanteros en el
    banquillo. Ocho puntos sentados en una sola jornada, cuando
    la temporada se decide por trece.

LO QUE VIGILAN ESTAS PRUEBAS

    Que el factor se aplique donde se ELIGE el once y no donde se
    PUBLICA el numero -si se aplicara alli, la proxima medicion
    del sesgo se estaria midiendo a si misma-, que se pueda
    apagar con una linea, y que la muestra corta viaje pegada al
    numero.

    Todo con fixture. Ni una lectura de `data/`.
"""

from __future__ import annotations

import os

from src.analysis.lineup_engine import weekly_expected_value
from src.analysis.position_factor import (
    DISABLE_ENV,
    FACTORS,
    PROVENANCE,
    WINDOW,
    factor_for,
    factors_active,
    state,
    vara_plana,
)
from src.analysis.vara_comparada import comparar, elegir_once


def _plantilla() -> list:
    """
    El caso real de hoy, en pequeño.

    Cinco defensas y cuatro medios con 90 % de titularidad, y
    cuatro delanteros con 70 %. Con la vara vieja los defensas
    ganan por porcentaje y sale 5-4-1 -que es literalmente el
    once que sacaba el motor el 17/09-. Con los factores, el
    delantero al 70 % pasa por delante del defensa al 90 %.
    """

    plantilla = [{
        "id": 1,
        "name": "Portero",
        "position": 1,
        "hierarchy_value": 40,
        "starter_probability": 80.0,
        "points": 6,
    }]

    for i in range(5):
        plantilla.append({
            "id": 100 + i,
            "name": f"Defensa {i}",
            "position": 2,
            "hierarchy_value": 40,
            "starter_probability": 90.0,
            "points": 6,
        })

    for i in range(4):
        plantilla.append({
            "id": 200 + i,
            "name": f"Medio {i}",
            "position": 3,
            "hierarchy_value": 40,
            "starter_probability": 90.0,
            "points": 11,
        })

    # Menos seguros de jugar y mas productivos cuando juegan: el
    # perfil que la vara vieja sentaba.
    for i in range(4):
        plantilla.append({
            "id": 300 + i,
            "name": f"Delantero {i}",
            "position": 4,
            "hierarchy_value": 40,
            "starter_probability": 70.0,
            "points": 11,
        })

    return plantilla


# ============================================================
# 1. EL CASO DE HOY
# ============================================================


def test_un_delantero_y_un_defensa_iguales_no_valen_lo_mismo() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO POR SU NOMBRE

        "Un delantero y un defensa con la misma probabilidad de
         ser titular y los mismos puntos brutos no pueden valer
         lo mismo para el once."
    """

    defensa = weekly_expected_value(40, 70.0, position=2)
    delantero = weekly_expected_value(40, 70.0, position=4)
    medio = weekly_expected_value(40, 70.0, position=3)

    assert delantero > defensa, (
        f"un delantero al 70 % vale {delantero:.4f} y un defensa "
        f"identico {defensa:.4f}: la vara los sigue empatando"
    )
    assert medio > defensa

    # Y en la proporcion medida, no en una cualquiera.
    assert abs(
        delantero / defensa - FACTORS[4] / FACTORS[2]
    ) < 1e-9


def test_sin_posicion_la_vara_es_la_de_siempre() -> None:
    """
    POR QUE ESTO IMPORTA MAS DE LO QUE PARECE

        Donde solo se PUBLICA el numero -las fichas de
        plantilla- la vara tiene que salir cruda. Si alli se
        corrigiera, la proxima medicion del sesgo se estaria
        midiendo a si misma y saldria siempre neutra.
    """

    for posicion in (1, 2, 3, 4):

        cruda = weekly_expected_value(40, 70.0)

        assert cruda == weekly_expected_value(
            40, 70.0, position=None
        )

        if FACTORS[posicion] != 1.0:
            assert cruda != weekly_expected_value(
                40, 70.0, position=posicion
            )


def test_el_motor_pasa_la_posicion_y_las_fichas_no() -> None:
    """
    Que no se invierta por descuido: el sitio donde se elige el
    once pasa la posicion; el sitio donde se publica la ficha, no.
    """

    from pathlib import Path

    motor = Path(
        "src/analysis/lineup_engine.py"
    ).read_text(encoding="utf-8")

    assert "position=player.get(\"position\")" in motor, (
        "el motor de alineacion ha dejado de pasar la posicion: "
        "los factores no se estan aplicando a nada"
    )

    fichas = Path(
        "src/telemetry/squads.py"
    ).read_text(encoding="utf-8")

    bloque = fichas[
        fichas.index("weekly_expected_value("):
    ][:400]

    assert "position" not in bloque, (
        "las fichas de plantilla han empezado a publicar la vara "
        "corregida: la proxima medicion del sesgo se mediria a si "
        "misma"
    )


# ============================================================
# 2. EL INTERRUPTOR
# ============================================================


def test_una_linea_devuelve_la_vara_vieja() -> None:
    """
    "Si en dos jornadas esto empeora, se apaga sin tocar codigo."
    """

    antes = os.environ.get(DISABLE_ENV)

    try:
        os.environ[DISABLE_ENV] = "1"

        assert factors_active() is False

        for posicion in (1, 2, 3, 4):
            assert factor_for(posicion) == 1.0

        assert weekly_expected_value(
            40, 70.0, position=4
        ) == weekly_expected_value(40, 70.0)

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes

    # Y al quitarla, vuelven.
    assert factors_active() is True


def test_el_contrafactual_no_toca_el_entorno() -> None:
    """
    El once de la vara vieja se calcula con un contexto, no
    escribiendo en el entorno del proceso: si algo fallara a
    mitad, dejaria los factores apagados en produccion.
    """

    assert factors_active() is True

    with vara_plana():
        assert factors_active() is False
        assert factor_for(4) == 1.0

    assert factors_active() is True
    assert factor_for(4) == FACTORS[4]


# ============================================================
# 3. LA MUESTRA VIAJA CON EL NUMERO
# ============================================================


def test_cada_factor_dice_de_cuantos_sale() -> None:
    """
    EL ENCARGO, LITERAL

        "No quiero enterarme dentro de un mes de que el factor
         del delantero salia de nueve casos."
    """

    publicado = state()

    assert publicado["available"] is True

    for fila in publicado["rows"]:

        assert fila["players"] > 0, (
            f"{fila['name']} no dice de cuantas fichas sale"
        )
        assert fila["observations"] >= fila["players"], (
            f"{fila['name']}: menos observaciones que fichas"
        )

    corta = min(
        (f for f in publicado["rows"] if f["applied"]),
        key=lambda f: f["players"],
        default=None,
    )

    assert corta is not None
    assert str(corta["players"]) in publicado["reason"], (
        "la muestra mas corta no sale en la linea que se lee"
    )

    assert str(WINDOW["matchdays"]) in publicado["reason"]


def test_una_linea_sin_muestra_no_lleva_factor() -> None:
    """
    El portero se midio en 0,93 sobre 7 fichas, por debajo del
    minimo de 10 que exige la medicion. Se mide y no se aplica.
    """

    assert FACTORS[1] == 1.0

    portero = PROVENANCE[1]

    assert portero["applied"] is False
    assert portero["measured_factor"] != 1.0, (
        "si el portero midiera 1,0 no haria falta explicarlo"
    )
    assert portero["note"]

    fila = next(
        f for f in state()["rows"] if f["position"] == 1
    )

    assert fila["factor"] == 1.0
    assert fila["applied"] is False


def test_el_apagado_sale_escrito_y_copiable() -> None:
    publicado = state()

    assert publicado["disable_with"] == f"{DISABLE_ENV}=1"
    assert DISABLE_ENV in publicado["reason"]


# ============================================================
# 4. EL ONCE CAMBIA, Y CAMBIA HACIA ARRIBA
# ============================================================


def test_los_factores_sacan_defensas_y_meten_delanteros() -> None:
    """
    Con once idénticos salvo la linea, la vara vieja llena de
    defensas y la nueva reparte hacia arriba.
    """

    resultado = comparar(_plantilla())

    assert resultado["available"] is True
    assert resultado["changed"] is True

    vieja = resultado["old"]["by_position"]
    nueva = resultado["new"]["by_position"]

    assert nueva["Defensa"] < vieja["Defensa"], (
        f"la vara nueva alinea {nueva['Defensa']} defensas y la "
        f"vieja {vieja['Defensa']}: no ha corregido nada"
    )
    assert (
        nueva["Medio"] + nueva["Delantero"]
        > vieja["Medio"] + vieja["Delantero"]
    )


def test_el_once_sigue_siendo_legal() -> None:
    """
    Corregir la vara no puede sacar un once ilegal: un portero,
    diez de campo, y un dibujo de los que el motor conoce.
    """

    from src.analysis.vara_comparada import FORMACIONES

    for con_factores in (True, False):

        once = elegir_once(_plantilla(), con_factores)

        assert once["available"]
        assert len(once["players"]) == 11
        assert once["by_position"]["Portero"] == 1
        assert once["formation"] in FORMACIONES

        cupos = FORMACIONES[once["formation"]]

        for posicion, cuantos in cupos.items():
            reales = sum(
                1
                for j in once["players"]
                if j["position"] == posicion
            )
            assert reales == cuantos


def test_con_el_interruptor_los_dos_onces_son_el_mismo() -> None:
    """
    Si apagar los factores no devolviera el once de antes, el
    interruptor no serviria de nada.
    """

    antes = os.environ.get(DISABLE_ENV)

    try:
        os.environ[DISABLE_ENV] = "1"

        resultado = comparar(_plantilla())

        assert resultado["new"]["formation"] == (
            resultado["old"]["formation"]
        )
        assert resultado["changed"] is False

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes


def test_nada_de_esto_lanza() -> None:
    for basura in (None, [], [{"id": 1}], [{"position": 9}]):
        assert isinstance(elegir_once(basura), dict)
        assert isinstance(comparar(basura), dict)

    for basura in (None, "x", -1, 99):
        assert factor_for(basura) == 1.0


TESTS = [
    test_un_delantero_y_un_defensa_iguales_no_valen_lo_mismo,
    test_sin_posicion_la_vara_es_la_de_siempre,
    test_el_motor_pasa_la_posicion_y_las_fichas_no,
    test_una_linea_devuelve_la_vara_vieja,
    test_el_contrafactual_no_toca_el_entorno,
    test_cada_factor_dice_de_cuantos_sale,
    test_una_linea_sin_muestra_no_lleva_factor,
    test_el_apagado_sale_escrito_y_copiable,
    test_los_factores_sacan_defensas_y_meten_delanteros,
    test_el_once_sigue_siendo_legal,
    test_con_el_interruptor_los_dos_onces_son_el_mismo,
    test_nada_de_esto_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA VARA V1")
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
