"""
POSIBLES CAMBIOS: el motivo lo pone el motor, no el panel.

SINTOMA

    El dashboard ensenaba once nombres y un banquillo mudo. El
    dueno veia que Cepeda no juega y no sabia si estaba
    lesionado, si su posicion estaba llena, o si simplemente
    puntua menos que el que esta puesto.

CAUSA

    `search_best_lineup_for_formation` ya compara a TODOS y
    descarta en tres cortes -no puede jugar, esta en duda, puntua
    menos-, pero de todo ese trabajo solo publicaba el resultado
    y tiraba el porque.

CONSECUENCIA

    `banquillo_con_motivo` lee los valores que el motor ya dejo
    puestos y dice en cual de los tres cortes se quedo cada uno.
    Estas guardias existen para que nadie escriba aqui una
    SEGUNDA opinion: si el panel algun dia dice algo distinto de
    lo que hizo el motor, no hay forma de saber cual manda.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.lineup_engine import banquillo_con_motivo


DASHBOARD = Path("dashboard-v8") / "src"


def _xi() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "Dituro",
            "position": 1,
            "lineup_position": 1,
            "lineup_score": 250386.9,
            "weekly_expected_value": 0.25,
        },
        {
            "id": 2,
            "name": "Jonny",
            "position": 2,
            "lineup_position": 2,
            "lineup_score": 250369.0,
            "weekly_expected_value": 0.25,
        },
    ]


# ============================================================
# 1. CADA MOTIVO SALE DEL CORTE QUE NO PASO
# ============================================================


def test_cada_suplente_dice_por_que_esta_fuera() -> None:
    """
    Los tres cortes del motor, cada uno con su nombre. Un motivo
    en blanco es un banquillo mudo otra vez.
    """

    xi = _xi()

    banquillo = banquillo_con_motivo(
        xi
        + [
            {
                "id": 3,
                "name": "Kiko",
                "position": 2,
                "lineup_eligible": True,
                "automatic_lineup": True,
                "lineup_score": 250100.0,
            },
            {
                "id": 4,
                "name": "Roto",
                "position": 2,
                "lineup_eligible": False,
                "availability_label": "Lesionado",
                "lineup_score": 250999.0,
            },
            {
                "id": 5,
                "name": "Duda",
                "position": 2,
                "lineup_eligible": True,
                "automatic_lineup": False,
                "lineup_score": 250800.0,
            },
        ],
        xi,
    )

    motivos = {f["name"]: f["reason"] for f in banquillo}

    assert motivos["Kiko"] == "PUNTUA_MENOS", motivos
    assert motivos["Roto"] == "NO_DISPONIBLE", motivos
    assert motivos["Duda"] == "EN_DUDA", motivos

    # Regla 24: ninguna guardia pasa con las manos vacias.
    assert len(banquillo) == 3, banquillo

    for fila in banquillo:
        assert fila["reason_text"], (
            "un suplente sale sin frase en castellano"
        )


def test_el_motivo_va_en_castellano_llano() -> None:
    """
    El dueno lee la portada, no el codigo. "PUNTUA_MENOS" no es
    una frase; "puntua menos que Jonny" si, y ademas dice contra
    QUIEN, que es la mitad de la respuesta.
    """

    xi = _xi()

    fila = banquillo_con_motivo(
        xi
        + [
            {
                "id": 3,
                "name": "Kiko",
                "position": 2,
                "lineup_eligible": True,
                "automatic_lineup": True,
                "lineup_score": 250100.0,
            }
        ],
        xi,
    )[0]

    assert fila["reason_text"] == "puntúa menos que Jonny", fila

    assert fila["compared_to"] == "Jonny", fila


# ============================================================
# 2. LA COMPARACION ES LA DEL MOTOR, NO OTRA
# ============================================================


def test_se_compara_contra_el_peor_titular_de_su_posicion() -> None:
    """
    El liston de una posicion es el PEOR que hay puesto ahi: es a
    quien tendria que ganar el suplente para entrar, y es
    exactamente lo que el motor comparo al ordenar.

    Contra el mejor, o contra el once entero, saldrian numeros
    que no explican ninguna decision.
    """

    xi = [
        {
            "id": 1,
            "name": "Bueno",
            "position": 3,
            "lineup_position": 3,
            "lineup_score": 900.0,
            "weekly_expected_value": 0.90,
        },
        {
            "id": 2,
            "name": "Justito",
            "position": 3,
            "lineup_position": 3,
            "lineup_score": 500.0,
            "weekly_expected_value": 0.50,
        },
    ]

    fila = banquillo_con_motivo(
        xi
        + [
            {
                "id": 3,
                "name": "Suplente",
                "position": 3,
                "lineup_eligible": True,
                "automatic_lineup": True,
                "lineup_score": 400.0,
                "weekly_expected_value": 0.40,
            }
        ],
        xi,
    )[0]

    assert fila["compared_to"] == "Justito", fila

    assert fila["lineup_score_delta"] == -100.0, fila

    assert round(fila["weekly_value_delta"], 2) == -0.10, fila


def test_el_que_mejoraria_el_once_se_ve_en_positivo() -> None:
    """
    Un suplente MEJOR que el titular al que no dejan jugar es lo
    mas importante de este panel: no le falta nivel, le falta
    poder jugar. Si eso saliera en negativo o en blanco, el unico
    caso que exige mirar el mercado pasaria inadvertido.
    """

    xi = _xi()

    fila = [
        f
        for f in banquillo_con_motivo(
            xi
            + [
                {
                    "id": 4,
                    "name": "Roto",
                    "position": 2,
                    "lineup_eligible": False,
                    "availability_label": "Lesionado",
                    "lineup_score": 250999.0,
                    "weekly_expected_value": 0.90,
                }
            ],
            xi,
        )
        if f["name"] == "Roto"
    ][0]

    assert fila["weekly_value_delta"] > 0, fila

    assert round(fila["weekly_value_delta"], 2) == 0.65, fila


def test_el_que_esta_mas_cerca_de_entrar_sale_primero() -> None:
    """
    Un panel ordenado por id es un panel que hay que leer entero.
    Arriba, el que menos lejos esta del once.
    """

    xi = _xi()

    nombres = [
        f["name"]
        for f in banquillo_con_motivo(
            xi
            + [
                {
                    "id": 3,
                    "name": "Lejos",
                    "position": 2,
                    "lineup_eligible": True,
                    "automatic_lineup": True,
                    "lineup_score": 100.0,
                },
                {
                    "id": 4,
                    "name": "Cerca",
                    "position": 2,
                    "lineup_eligible": True,
                    "automatic_lineup": True,
                    "lineup_score": 250368.0,
                },
            ],
            xi,
        )
    ]

    assert nombres[0] == "Cerca", nombres


# ============================================================
# 3. NI UN TITULAR EN EL BANQUILLO
# ============================================================


def test_ningun_titular_aparece_como_suplente() -> None:
    """
    Si un titular se colara aqui, el panel diria que el que esta
    jugando esta fuera. Es la clase de fallo que hace que el
    dueno deje de creerse la pantalla entera.
    """

    xi = _xi()

    banquillo = banquillo_con_motivo(xi, xi)

    assert banquillo == [], banquillo


def test_sin_once_no_se_inventa_una_comparacion() -> None:
    """
    Regla 23: si no hay contra quien comparar, se dice que no
    hay. Un cero puesto donde falta el dato se lee como "esta
    igual de bien", que es lo contrario de la verdad.
    """

    banquillo = banquillo_con_motivo(
        [
            {
                "id": 3,
                "name": "Solo",
                "position": 2,
                "lineup_eligible": True,
                "automatic_lineup": True,
                "lineup_score": 100.0,
            }
        ],
        [],
    )

    assert len(banquillo) == 1, banquillo

    assert banquillo[0]["reason"] == "POSICION_CUBIERTA", banquillo

    assert banquillo[0]["lineup_score_delta"] is None, banquillo

    assert banquillo[0]["compared_to"] is None, banquillo


# ============================================================
# 4. INICIO SE QUEDO EN CUATRO PANELES
# ============================================================


def _lee(ruta: Path) -> str:
    if not ruta.exists():
        raise AssertionError(f"no existe {ruta}")

    return ruta.read_text(encoding="utf-8")


def test_inicio_tiene_los_cuatro_paneles_y_solo_esos() -> None:
    """
    El encargo del 10/09 fue explicito: la tira y cuatro paneles.
    Esta guardia existe porque la portada ya se lleno una vez, y
    se vuelve a llenar sola en cuanto nadie mira.
    """

    fuente = _lee(DASHBOARD / "pages" / "HomePage.jsx")

    for panel in (
        "PitchXI",
        "StandingsIntelPanel",
        "TimelinePanel",
        "PosiblesCambiosPanel",
    ):
        assert f"<{panel}" in fuente, (
            f"{panel} no esta montado en Inicio"
        )

    # Los que bajaron a Auditoria. Nada se borro: se movio.
    for panel in (
        "AhoraPanel",
        "DineroPanel",
        "VentanaPanel",
        "CobrarPanel",
        "ElOncePanel",
    ):
        assert f"<{panel}" not in fuente, (
            f"{panel} ha vuelto a subir a Inicio"
        )

    auditoria = _lee(DASHBOARD / "pages" / "AuditPage.jsx")

    for panel in (
        "AhoraPanel",
        "DineroPanel",
        "VentanaPanel",
        "CobrarPanel",
        "ElOncePanel",
        "Objetivos",
    ):
        assert f"<{panel}" in auditoria, (
            f"{panel} salio de Inicio y no llego a Auditoria: se ha "
            f"BORRADO, y el encargo decia que no"
        )


def test_la_amenaza_mas_alta_sale_en_rojo() -> None:
    """
    `VERY_HIGH` faltaba en la tabla y caia al gris del `||`: la
    amenaza mas alta del tablero se pintaba igual que "ninguna".
    """

    fuente = _lee(
        DASHBOARD / "components" / "StandingsIntelPanel.jsx"
    )

    assert 'VERY_HIGH: "pill crit"' in fuente, (
        "VERY_HIGH no esta en rojo"
    )


def test_las_dos_cuentas_atras_corren_en_el_navegador() -> None:
    """
    Una cuenta atras congelada no es una cuenta atras. Y si el
    ciclo no llega, tiene que DECIRLO en vez de quedarse en cero
    fingiendo normalidad: un ciclo que no entra es justo lo que
    hay que ver.
    """

    fuente = _lee(DASHBOARD / "components" / "KpiStrip.jsx")

    assert "setInterval" in fuente, (
        "la tira no tiene reloj propio: las cuentas atras estan "
        "congeladas en la hora de la foto"
    )

    assert (
        "proximoCiclo" in fuente
        and "segundosAlReset" in fuente
    ), "falta una de las dos cuentas atras"

    assert "lateMinutes" in fuente, (
        "el ciclo que no llega no se canta"
    )


def test_la_deuda_maxima_ensena_su_desglose() -> None:
    """
    3.608.383 sin desglose se lee como "se me ha hundido el
    saldo" cuando lo que pasa es que hay 12.217.000 puestos en
    una puja. Los tres numeros de debajo son la diferencia entre
    un susto y un dato.
    """

    fuente = _lee(DASHBOARD / "components" / "KpiStrip.jsx")

    assert "Deuda máxima" in fuente, (
        "la tira sigue diciendo 'Puede gastar'"
    )

    for palabra in ("saldo", "comprometido", "crédito"):
        assert palabra in fuente, (
            "el desglose de la deuda maxima esta incompleto"
        )


TESTS = [
    test_cada_suplente_dice_por_que_esta_fuera,
    test_el_motivo_va_en_castellano_llano,
    test_se_compara_contra_el_peor_titular_de_su_posicion,
    test_el_que_mejoraria_el_once_se_ve_en_positivo,
    test_el_que_esta_mas_cerca_de_entrar_sale_primero,
    test_ningun_titular_aparece_como_suplente,
    test_sin_once_no_se_inventa_una_comparacion,
    test_inicio_tiene_los_cuatro_paneles_y_solo_esos,
    test_la_amenaza_mas_alta_sale_en_rojo,
    test_las_dos_cuentas_atras_corren_en_el_navegador,
    test_la_deuda_maxima_ensena_su_desglose,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"POSIBLES CAMBIOS V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
