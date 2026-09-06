"""
EL ONCE V1 - las guardias de la noche del 17/09/2026.

SINTOMA

    Cinco jornadas cerradas, CERO fiables. La pantalla llevaba un
    mes diciendo "ninguna cuadra con Biwenger: el once que
    anotamos no es el que jugo", y con eso el proyecto se quedo
    sin la unica medida que dice si el motor de alineacion
    funciona.

CAUSA

    Dos fallos distintos, los dos de aritmetica y ninguno del
    motor:

    1. La clasificacion de Biwenger es ACUMULADA. El cuadre
       comparaba `puntos_once` -una jornada- contra ese
       acumulado. En la jornada 1 coincide porque no hay nada
       antes, y por eso sobrevivio un mes. De la 2 en adelante
       comparaba 17 contra 60.

       La misma raiz hacia que la diferencia contra la liga
       saliera +13,5 tres jornadas seguidas: era la brecha de
       TEMPORADA repetida.

    2. `totales` solo tiene a los jugadores que seguian en la
       plantilla al mirar. Un jugador que alineo el sabado y se
       vendio el lunes aporta cero. En las jornadas 1 y 2 eso
       pasaba con cuatro y con tres de los once, y la pantalla
       publicaba "61,9 % del optimo" como si midiera el motor.

CONSECUENCIA

    Cuatro encargos seguidos empujando hacia el mercado sin
    saber que el once dejaba ocho puntos en el banquillo en la
    unica jornada que si se puede reconstruir. Trece puntos
    separan del lider.

LO QUE ESTAS PRUEBAS NO DEJAN VOLVER

    Que un numero cojo se lea como una nota, que una jornada de
    una temporada se compare con un acumulado, y que una
    correccion medida se aplique sola sin que la decida el dueño.
"""

from __future__ import annotations

import ast
import json

from pathlib import Path

from src.analysis.banquillo import (
    CASI_CUADRA_PERCENT,
    puntos_en_el_banquillo,
)
from src.analysis.rival_once import comparar_con
from src.analysis.sesgo_posicion import (
    MUESTRA_MINIMA,
    sesgo_por_posicion,
)


FOTO = Path("diagnostico/status.json")


def _produccion():
    if not FOTO.exists():
        return None

    return json.loads(FOTO.read_text(encoding="utf-8"))


def _jornada(
    round_id: int,
    *,
    once: int,
    techo: int,
    biwenger: int,
    completa: bool = True,
    formacion: str = "4-4-2",
) -> dict:
    """Una fila del marcador ya calculada."""

    return {
        "round_id": round_id,
        "medible": True,
        "reconstruccion_completa": completa,
        "motivo_incompleta": (
            None
            if completa
            else "2 de los once ya no estaban en la plantilla."
        ),
        "formacion": formacion,
        "puntos_once": once,
        "mejor_formacion": "3-4-3",
        "mejor_puntos": techo,
        "eficiencia": (
            round(100 * once / techo, 1) if techo else None
        ),
        "puntos_perdidos": techo - once,
        "puntos_biwenger": biwenger,
        "cuadra": biwenger == once,
        "descuadre": biwenger - once,
        "descuadre_percent": (
            round(abs(biwenger - once) / biwenger * 100, 1)
            if biwenger
            else None
        ),
        "detalle": {"faltaron": [], "sobraron": []},
    }


CARRERA = {
    "points_behind": 13,
    "required_pace": 0.371,
}


# ============================================================
# 1. LA ARITMETICA QUE COSTO UN MES
# ============================================================


def test_el_cuadre_no_compara_una_jornada_con_una_temporada() -> None:
    """
    EL FALLO, EN UN CASO

        Jornada 2. El once hizo 31 puntos y Biwenger tenia 60
        acumulados -29 de la jornada 1 mas 31 de esta-.

        El marcador comparaba 31 contra 60 y decia "no cuadra".
        Con eso ninguna jornada a partir de la primera podia
        cuadrar jamas.
    """

    from src.analysis.marcador import _puntos_de_la_clasificacion

    previa = {
        "round_id": 4899,
        "clasificacion": [
            {"user_id": 1, "points": 29},
            {"user_id": 2, "points": 24},
        ],
    }

    actual = {
        "round_id": 4900,
        "clasificacion": [
            {"user_id": 1, "points": 60},
            {"user_id": 2, "points": 64},
        ],
    }

    puntos = _puntos_de_la_clasificacion(actual, previa)

    assert puntos[1] == 31, (
        "sigue leyendo el acumulado de la temporada como si "
        "fueran los puntos de la jornada"
    )
    assert puntos[2] == 40


def test_la_primera_jornada_si_es_su_acumulado() -> None:
    """
    En la jornada 1 no hay nada antes: el acumulado ES la
    jornada. Ese caso es el que hacia que el fallo pareciera
    funcionar.
    """

    from src.analysis.marcador import _puntos_de_la_clasificacion

    actual = {
        "round_id": 4899,
        "clasificacion": [{"user_id": 1, "points": 29}],
    }

    assert _puntos_de_la_clasificacion(actual, None)[1] == 29


def test_sin_observacion_previa_no_se_inventa_la_jornada() -> None:
    """
    Ausencia de dato != dato. Una jornada que no es la primera y
    no tiene anterior no se estima: se devuelve None y queda
    fuera.
    """

    from src.analysis.marcador import _puntos_de_la_clasificacion

    actual = {
        "round_id": 4903,
        "clasificacion": [{"user_id": 1, "points": 90}],
    }

    assert _puntos_de_la_clasificacion(actual, None) is None


def test_media_alineacion_vendida_no_es_una_nota() -> None:
    """
    EL CASO REAL

        Jornada 1: cuatro de los once ya no estaban en la
        plantilla al mirar, asi que aportaron cero. El once salio
        a 13 cuando Biwenger pago 29, y la pantalla publico
        "61,9 % del optimo".

        Eso no medía el motor: medía el agujero.
    """

    from src.analysis.marcador import _reconstruccion_completa

    entera, motivo = _reconstruccion_completa({
        "plantilla": [{"id": 1}, {"id": 2}, {"id": 3}],
        "mi_once": {"players": [1, 2, 3]},
    })

    assert entera is True
    assert motivo is None

    coja, motivo = _reconstruccion_completa({
        "plantilla": [{"id": 1}],
        "mi_once": {"players": [1, 2, 3]},
        "nombres": {"2": "Yeray", "3": "Bigas"},
    })

    assert coja is False
    assert "Yeray" in motivo and "Bigas" in motivo, (
        "no basta con decir que falta gente: hay que decir quien"
    )


def test_una_jornada_coja_no_entra_en_la_media() -> None:
    """
    Aunque cuadre por casualidad, si faltaba media alineacion no
    puntua. Una media que mezcla reconstrucciones buenas con
    cojas no mide nada.
    """

    banquillo = puntos_en_el_banquillo(
        {
            "jornadas": [
                _jornada(
                    4899,
                    once=13,
                    techo=21,
                    biwenger=13,
                    completa=False,
                ),
            ]
        },
        CARRERA,
    )

    assert banquillo["jornadas_que_cuentan"] == 0
    assert banquillo["puntos_perdidos"] is None
    assert not banquillo["jornadas"][0]["cuenta"]


# ============================================================
# 2. LOS PUNTOS SENTADOS
# ============================================================


def test_los_puntos_sentados_se_comparan_con_lo_que_hace_falta() -> None:
    """
    LA CUENTA DE LA NOCHE

        13 puntos / 35 jornadas = 0,371 por jornada.

    Una cifra de puntos perdidos sin esa referencia no dice si
    la liga esta en el banquillo o en el mercado.
    """

    banquillo = puntos_en_el_banquillo(
        {
            "jornadas": [
                _jornada(4899, once=70, techo=78, biwenger=70),
                _jornada(4900, once=60, techo=66, biwenger=60),
                _jornada(4901, once=50, techo=54, biwenger=50),
            ]
        },
        CARRERA,
    )

    assert banquillo["jornadas_que_cuentan"] == 3
    assert banquillo["puntos_perdidos"] == 18
    assert banquillo["puntos_perdidos_por_jornada"] == 6.0

    assert banquillo["ritmo_necesario"] == 0.371
    assert banquillo["veces_lo_que_hace_falta"] == 16.2

    assert "banquillo" in banquillo["veredicto"]


def test_si_el_once_ya_es_optimo_lo_dice_y_manda_al_mercado() -> None:
    """
    EL ENCARGO, LITERAL

        "Si sale que el once es casi optimo y solo dejamos una
        decima por jornada, se escribe y se cierra el asunto."

    El veredicto tiene que poder decir eso, no solo la alarma.
    """

    banquillo = puntos_en_el_banquillo(
        {
            "jornadas": [
                _jornada(4899, once=78, techo=78, biwenger=78),
                _jornada(4900, once=66, techo=66, biwenger=66),
                _jornada(4901, once=53, techo=54, biwenger=53),
            ]
        },
        CARRERA,
    )

    assert banquillo["puntos_perdidos"] == 1
    assert banquillo["veces_lo_que_hace_falta"] < 1

    assert "mercado" in banquillo["veredicto"]


def test_una_jornada_que_casi_cuadra_no_entra_en_la_media() -> None:
    """
    J4901: el once reconstruido suma 70 y Biwenger pago 73. Se
    queda a 3 puntos, un 4,1 %.

    Esa jornada es la unica evidencia que hay, asi que se publica
    -etiquetada- pero NUNCA se promedia con las que cuadran. El
    cuadre no se afloja.
    """

    banquillo = puntos_en_el_banquillo(
        {
            "jornadas": [
                _jornada(4901, once=70, techo=78, biwenger=73),
            ]
        },
        CARRERA,
    )

    assert banquillo["jornadas_que_cuentan"] == 0, (
        "una jornada que no cuadra no puede puntuar"
    )
    assert banquillo["puntos_perdidos"] is None

    assert banquillo["jornadas_casi"] == 1
    assert banquillo["puntos_perdidos_casi"] == 8

    assert banquillo["jornadas"][0]["casi"] is True
    assert banquillo["jornadas"][0]["descuadre"] == 3

    assert "indicio" in banquillo["veredicto"]


def test_un_descuadre_grande_no_es_un_casi() -> None:
    """
    Se queda a 16 de 29: un 55 %. Eso no es "casi", es basura, y
    mezclarlo con el 4,1 % seria justo lo que el cuadre existe
    para impedir.
    """

    banquillo = puntos_en_el_banquillo(
        {
            "jornadas": [
                _jornada(4899, once=13, techo=21, biwenger=29),
            ]
        },
        CARRERA,
    )

    assert banquillo["jornadas"][0]["descuadre_percent"] > (
        CASI_CUADRA_PERCENT
    )
    assert banquillo["jornadas"][0]["casi"] is False
    assert banquillo["jornadas_casi"] == 0


def test_sin_nada_que_medir_lo_dice_en_vez_de_inventarse_una_nota() -> None:
    banquillo = puntos_en_el_banquillo({"jornadas": []}, CARRERA)

    assert banquillo["puntos_perdidos"] is None
    assert banquillo["veces_lo_que_hace_falta"] is None


def test_el_banquillo_dice_quien_debio_jugar() -> None:
    """
    Un porcentaje no se puede corregir; un nombre si. Es lo unico
    accionable de todo el bloque.
    """

    fila = _jornada(4901, once=70, techo=78, biwenger=70)

    fila["detalle"] = {
        "faltaron": [
            {"name": "Lucas Cepeda", "position": 4, "points": 3},
        ],
        "sobraron": [
            {"name": "Pablo Duran", "position": 4, "points": 0},
        ],
    }

    banquillo = puntos_en_el_banquillo(
        {"jornadas": [fila]},
        CARRERA,
    )

    entrada = banquillo["jornadas"][0]

    assert entrada["debieron_jugar"][0]["name"] == "Lucas Cepeda"
    assert (
        entrada["jugaron_y_no_debian"][0]["name"] == "Pablo Duran"
    )


# ============================================================
# 3. LA VARA CON LA QUE SE ORDENA EL ONCE
# ============================================================


def _liga(jugadores: list, jornadas: int = 3) -> dict:
    return {
        "race": {"matchdays_played": jornadas},
        "rival_squads": {
            "managers": [
                {"name": "Uno", "players": jugadores},
            ]
        },
    }


def test_la_vara_se_mide_en_puntos_entregados() -> None:
    """
    POR QUE NO SE PUBLICA UN "ERROR MEDIO EN PUNTOS"

        `weekly_expected_value` no predice puntos: va de 0 a 1 y
        sirve para ORDENAR el once. No hay puntos que restarle.

    Lo que si contesta a la pregunta del encargo es cuantos
    puntos entrega cada posicion con la misma marca de la vara.
    """

    jugadores = []

    # Doce defensas al 0,8 que entregan 3 puntos por jornada.
    for i in range(12):
        jugadores.append({
            "name": f"DF{i}",
            "position": 2,
            "weekly_expected_value": 0.8,
            "points": 9,
            "starter_probability": 70.0,
        })

    # Doce delanteros al mismo 0,8 que entregan 6.
    for i in range(12):
        jugadores.append({
            "name": f"DL{i}",
            "position": 4,
            "weekly_expected_value": 0.8,
            "points": 18,
            "starter_probability": 70.0,
        })

    sesgo = sesgo_por_posicion(_liga(jugadores))

    assert sesgo["available"]

    por_nombre = {f["name"]: f for f in sesgo["rows"]}

    assert por_nombre["Delantero"]["points_per_expected"] == (
        2 * por_nombre["Defensa"]["points_per_expected"]
    ), "la vara no esta midiendo puntos entregados"

    assert "delantero" in sesgo["reason"].lower()


def test_el_factor_se_propone_y_no_se_aplica() -> None:
    """
    EL ENCARGO, LITERAL

        "Si hay sesgo por posicion, no lo corrijas esta noche con
        un factor a ojo. Midelo, publicalo, y propon la
        correccion con su numero. La decision es del dueño."
    """

    jugadores = [
        {
            "name": f"DF{i}",
            "position": 2,
            "weekly_expected_value": 0.8,
            "points": 9,
            "starter_probability": 70.0,
        }
        for i in range(12)
    ] + [
        {
            "name": f"DL{i}",
            "position": 4,
            "weekly_expected_value": 0.8,
            "points": 18,
            "starter_probability": 70.0,
        }
        for i in range(12)
    ]

    sesgo = sesgo_por_posicion(_liga(jugadores))

    assert sesgo["applied"] is False

    for fila in sesgo["rows"]:
        assert fila["proposed_factor"] is not None

    # Y el motor de alineacion no lo importa: si lo hiciera, se
    # estaria aplicando por la puerta de atras.
    motor = Path(
        "src/analysis/lineup_engine.py"
    ).read_text(encoding="utf-8")

    assert "sesgo_posicion" not in motor, (
        "el motor de alineacion ha empezado a leer el sesgo: eso "
        "es aplicarlo, y esta noche no se aplica nada"
    )


def test_una_posicion_con_muestra_corta_no_propone_factor() -> None:
    """
    Siete porteros no dan para corregir a los porteros. Se
    publica el dato y se marca que no llega.
    """

    jugadores = [
        {
            "name": f"PT{i}",
            "position": 1,
            "weekly_expected_value": 0.8,
            "points": 15,
            "starter_probability": 90.0,
        }
        for i in range(MUESTRA_MINIMA - 3)
    ] + [
        {
            "name": f"DF{i}",
            "position": 2,
            "weekly_expected_value": 0.8,
            "points": 9,
            "starter_probability": 70.0,
        }
        for i in range(MUESTRA_MINIMA + 2)
    ]

    sesgo = sesgo_por_posicion(_liga(jugadores))

    por_nombre = {f["name"]: f for f in sesgo["rows"]}

    assert por_nombre["Portero"]["enough"] is False
    assert por_nombre["Defensa"]["enough"] is True


def test_la_franja_del_empate_es_la_del_caso_real() -> None:
    """
    EL CASO DEL DUEÑO

        "Pablo Duran con un 70 % de titularidad estaba en el
        banquillo mientras defensas con ese mismo 70 % jugaban."

    Con el mismo porcentaje la vara los empata. Si en esa franja
    una posicion entrega mas, el desempate va al lado equivocado.
    """

    jugadores = [
        {
            "name": f"DF{i}",
            "position": 2,
            "weekly_expected_value": 0.7,
            "points": 9,
            "starter_probability": 70.0,
        }
        for i in range(12)
    ] + [
        {
            "name": f"DL{i}",
            "position": 4,
            "weekly_expected_value": 0.7,
            "points": 12,
            "starter_probability": 70.0,
        }
        for i in range(12)
    ]

    sesgo = sesgo_por_posicion(_liga(jugadores))
    franja = sesgo["tie_band"]

    assert franja["from"] <= 70.0 <= franja["to"]
    assert franja["gap_percent"] == 33.3, (
        "no esta comparando delantero contra defensa a igual "
        "probabilidad de ser titular"
    )


def test_el_sesgo_sale_de_produccion_y_no_de_una_copia() -> None:
    """
    La regla de la casa: se mide contra `diagnostico/status.json`.
    """

    foto = _produccion()

    if not foto:
        return

    sesgo = sesgo_por_posicion(foto)

    if not sesgo["available"]:
        return

    assert sesgo["matchdays"] > 0
    assert sesgo["sample"] > 20, (
        "la muestra de la liga se ha quedado en nada"
    )

    for fila in sesgo["rows"]:
        assert fila["points_per_expected"] is not None


# ============================================================
# 4. EL EQUIPO QUE HABIA QUE MIRAR
# ============================================================


def test_sin_ver_la_plantilla_no_se_compara_con_huecos() -> None:
    """
    EL ENCARGO, LITERAL

        "Si resulta que no se puede ver lo suficiente de su
        plantilla, dilo -es un resultado valido y prefiero
        saberlo a leer una comparacion hecha con huecos-."
    """

    vacio = comparar_con(
        {"rival_squads": {"managers": []}},
        "Mex",
    )

    assert vacio["available"] is False
    assert "Mex" in vacio["reason"]


def test_la_comparacion_cuenta_lo_que_de_verdad_distingue() -> None:
    """
    Mex va segundo con nuestras mismas fichas. Lo que hay que ver
    es donde tiene el once y cuantos titulares fijos lleva, no un
    porcentaje agregado.
    """

    estado = {
        "rival_squads": {
            "managers": [
                {
                    "name": "Mex",
                    "rank": 2,
                    "points": 141,
                    "team_value": 52_250_000,
                    "formation": "3-5-2",
                    "players": [
                        {
                            "name": "Bellingham",
                            "position": 3,
                            "points": 44,
                            "is_starter": True,
                            "starter_probability": 70.0,
                        },
                        {
                            "name": "Vicente",
                            "position": 4,
                            "points": 25,
                            "is_starter": True,
                            "starter_probability": 90.0,
                        },
                        {
                            "name": "Suplente",
                            "position": 2,
                            "points": 3,
                            "is_starter": False,
                            "starter_probability": 50.0,
                        },
                    ],
                },
                {
                    "name": "Pepe",
                    "is_current_user": True,
                    "rank": 4,
                    "points": 133,
                    "team_value": 49_540_000,
                    "formation": "4-3-3",
                    "players": [
                        {
                            "name": "Djene",
                            "position": 2,
                            "points": 5,
                            "is_starter": True,
                            "starter_probability": 90.0,
                        },
                        {
                            "name": "Zubeldia",
                            "position": 2,
                            "points": 9,
                            "is_starter": True,
                            "starter_probability": 80.0,
                        },
                    ],
                },
            ]
        },
        "league_center": {"market_feed": []},
    }

    comparacion = comparar_con(estado, "Mex")

    assert comparacion["available"]

    assert comparacion["points_gap"] == 8
    assert comparacion["rival"]["attacking_half"] == 2
    assert comparacion["us"]["attacking_half"] == 0

    # Lo incomodo: ellos ganan con menos titulares fijos.
    assert comparacion["rival"]["nailed_starters"] == 1
    assert comparacion["us"]["nailed_starters"] == 2

    assert comparacion["market"]["quiet"] is True
    assert "quieto" in comparacion["reason"]


def test_no_se_usan_los_campos_que_no_distinguen_a_nadie() -> None:
    """
    `activity` y `profile` salen con el MISMO valor para los
    siete managers -VERY_HIGH y AGGRESSIVE-, asi que no
    distinguen a nadie.

    Usarlos para decir que Mex es agresivo seria fabricar una
    diferencia que el dato no tiene.
    """

    fuente = Path(
        "src/analysis/rival_once.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    literales = {
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
    }

    for campo in ("activity", "profile"):
        assert campo not in literales, (
            f"`{campo}` vale lo mismo para los siete managers: "
            f"no puede sostener ninguna afirmacion"
        )


def test_el_tablon_dice_de_cuantos_dias_habla() -> None:
    """
    "Quieto" sin ventana es una afirmacion sobre toda la
    temporada que el tablon no puede sostener: solo guarda unos
    dias.
    """

    comparacion = comparar_con(
        {
            "rival_squads": {
                "managers": [
                    {
                        "name": "Mex",
                        "players": [
                            {
                                "name": "X",
                                "position": 3,
                                "points": 1,
                                "is_starter": True,
                            }
                        ],
                    },
                    {
                        "name": "Pepe",
                        "is_current_user": True,
                        "players": [
                            {
                                "name": "Y",
                                "position": 3,
                                "points": 1,
                                "is_starter": True,
                            }
                        ],
                    },
                ]
            },
            "league_center": {"market_feed": []},
        },
        "Mex",
    )

    assert "no guarda" in comparacion["caveat"]
    assert "temporada" in comparacion["market"]["window"]


# ============================================================
# 5. NADA DE ESTO DECIDE
# ============================================================


def test_el_once_no_decide_nada() -> None:
    prohibidos = (
        "autopilot_executor",
        "write_client",
        "BiwengerWriteClient",
        "optimal_bid",
        "lineup_engine",
    )

    for ruta in (
        "src/analysis/banquillo.py",
        "src/analysis/sesgo_posicion.py",
        "src/analysis/rival_once.py",
    ):
        arbol = ast.parse(
            Path(ruta).read_text(encoding="utf-8")
        )

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
                continue

            texto = ast.dump(nodo)

            for prohibido in prohibidos:
                assert prohibido not in texto, (
                    f"{ruta} importa `{prohibido}`: ha dejado de "
                    f"ser observador"
                )


def test_ninguno_lanza_con_basura() -> None:
    """
    Un bloque de pantalla que revienta se lleva por delante el
    ciclo entero. Ya paso.
    """

    for entrada in (None, {}, {"jornadas": None}, {"race": None}):

        assert isinstance(
            puntos_en_el_banquillo(entrada, entrada), dict
        )
        assert isinstance(sesgo_por_posicion(entrada), dict)
        assert isinstance(comparar_con(entrada), dict)


def test_los_puntos_sentados_se_publican() -> None:
    """
    El encargo pide que la cifra este donde se vea sin buscarla.
    Si el generador deja de publicarla, la pantalla se queda
    muda.
    """

    fuente = Path(
        "src/telemetry/dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"once": once_bloque,' in fuente
    assert "puntos_en_el_banquillo" in fuente
    assert "sesgo_por_posicion" in fuente

    # Y el marcador se calcula UNA vez: si se llamase dos veces
    # el banquillo podria estar mirando otra foto que la pantalla.
    assert fuente.count("build_marcador()") == 1, (
        "el marcador se calcula mas de una vez por ciclo"
    )


TESTS = [
    test_el_cuadre_no_compara_una_jornada_con_una_temporada,
    test_la_primera_jornada_si_es_su_acumulado,
    test_sin_observacion_previa_no_se_inventa_la_jornada,
    test_media_alineacion_vendida_no_es_una_nota,
    test_una_jornada_coja_no_entra_en_la_media,
    test_los_puntos_sentados_se_comparan_con_lo_que_hace_falta,
    test_si_el_once_ya_es_optimo_lo_dice_y_manda_al_mercado,
    test_una_jornada_que_casi_cuadra_no_entra_en_la_media,
    test_un_descuadre_grande_no_es_un_casi,
    test_sin_nada_que_medir_lo_dice_en_vez_de_inventarse_una_nota,
    test_el_banquillo_dice_quien_debio_jugar,
    test_la_vara_se_mide_en_puntos_entregados,
    test_el_factor_se_propone_y_no_se_aplica,
    test_una_posicion_con_muestra_corta_no_propone_factor,
    test_la_franja_del_empate_es_la_del_caso_real,
    test_el_sesgo_sale_de_produccion_y_no_de_una_copia,
    test_sin_ver_la_plantilla_no_se_compara_con_huecos,
    test_la_comparacion_cuenta_lo_que_de_verdad_distingue,
    test_no_se_usan_los_campos_que_no_distinguen_a_nadie,
    test_el_tablon_dice_de_cuantos_dias_habla,
    test_el_once_no_decide_nada,
    test_ninguno_lanza_con_basura,
    test_los_puntos_sentados_se_publican,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL ONCE V1")
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
            print(f"  ERROR {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
