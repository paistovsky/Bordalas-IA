"""
Dos techos distintos con el mismo nombre.

SINTOMA (12/09/2026)

    Un solo tope para todos:

        bid_cap:  premium_percent      0,25 %
                  break_even_percent   1,80 %

    Ese 1,80 % es donde deja de ser negocio REVENDERLO al
    Computer. Se le aplicaba igual al jugador que queremos
    QUEDARNOS, que es otra moneda entera.

LOS DOS, PARA TRENT (2.760.000)

    EL DEL COMERCIANTE, con la prima del Computer (+2,03 %) y el
    suelo de cobro (coste + 1 %):

        2.760.000 x 1,0203 / 1,01  =  2.788.146   (+1,02 %)

    Ni un euro mas: por encima, la reventa no cubre su propio
    suelo y el viaje no se puede cerrar con ganancia.

    EL DEL QUE SE QUEDA, a 30.000 EUR el punto:

        2 puntos/jornada x 30 jornadas x 30.000 = 1.800.000 EUR

    Eso son 65 % del precio, y ANTES de contar lo que suba de
    precio. El techo del comerciante es irrelevante ahi.

    Y EL QUE SE APLICA HOY es el de 1,80 %: 2.809.680. Esta POR
    ENCIMA del techo del comerciante, o sea que en una puja de
    revender permite pagar 21.534 EUR mas de lo que el viaje
    puede recuperar.

LO QUE ESTE MODULO NO HACE

    No mueve ningun tope, no sube ninguna puja y no toca
    `bid_cap`. Calcula los dos y dice cual se aplica.

REGLA 23

    No lee estado externo: todos los numeros van escritos aqui.
"""

from __future__ import annotations

from pathlib import Path


RAIZ = Path(__file__).parents[2]


TRENT = 2_760_000

# Medida en produccion sobre 129 ventas.
PRIMA_COMPUTER = 2.03

# Lo que el Computer paga, medido aqui sobre el tablon local, es
# +2,49 % con menos muestras. Se deja escrito para que se vea que
# el techo se mueve con la medicion y no con la opinion.
PRIMA_COMPUTER_LOCAL = 2.49

TECHO_COMERCIANTE = 2_788_146

# El que se aplica hoy: 1,80 % sobre el precio.
TOPE_APLICADO = 2_809_680


# ============================================================
# 1. EL TECHO DEL COMERCIANTE
# ============================================================


def test_el_techo_del_comerciante_para_trent() -> None:
    """El caso que motiva los dos numeros."""

    from src.analysis.los_dos_techos import (
        techo_del_comerciante,
    )

    visto = techo_del_comerciante(TRENT, PRIMA_COMPUTER)

    assert visto["available"] is True, visto

    assert visto["techo"] == TECHO_COMERCIANTE, visto

    # Poco mas de un uno por ciento. Es pequeño A PROPOSITO.
    assert abs(visto["techo_percent"] - 1.02) < 0.01, visto

    # Y se mueve con la medicion, no con la opinion: con la prima
    # medida en local sale otro numero, y mas alto.
    con_la_local = techo_del_comerciante(
        TRENT, PRIMA_COMPUTER_LOCAL
    )

    assert con_la_local["techo"] > visto["techo"], (
        con_la_local,
        visto,
    )


def test_el_tope_de_hoy_pasa_del_techo_del_comerciante() -> None:
    """
    EL NUMERO QUE IMPORTA DEL BLOQUE 3.

    El tope aplicado (+1,80 %) esta POR ENCIMA del techo del
    comerciante (+1,02 %). En una puja de revender, eso permite
    pagar mas de lo que el viaje puede recuperar.

    Esta guardia NO pide que se cambie: pide que se vea. Si algun
    dia el dueño mueve uno de los dos, esto se pondra rojo y
    habra que venir a leer por que eran dos.
    """

    from src.analysis.los_dos_techos import los_dos_techos

    visto = los_dos_techos(
        TRENT,
        prima_computer_percent=PRIMA_COMPUTER,
        intent="SPECULATION",
        tope_aplicado=TOPE_APLICADO,
    )

    assert visto["via"] == "REVENDER", visto

    assert visto["aplicado"] == TOPE_APLICADO, visto

    comerciante = visto["comerciante"]["techo"]

    assert visto["aplicado"] > comerciante, (
        "el tope aplicado ya no pasa del techo del comerciante: "
        "si es un cambio deliberado, actualiza esta guardia"
    )

    de_mas = visto["aplicado"] - comerciante

    assert de_mas == 21_534, de_mas


# ============================================================
# 2. EL TECHO DEL QUE SE QUEDA
# ============================================================


def test_el_techo_del_que_se_queda_es_otra_moneda() -> None:
    """
    Los puntos se pagan a 30.000 EUR. Dos puntos mas por jornada
    durante treinta jornadas son 1.800.000 EUR en premios.

    Eso es 65 % del precio de Trent. El techo del comerciante
    —+1,02 %— no tiene nada que decir sobre esa decision.
    """

    from src.analysis.caja_de_la_liga import EUROS_POR_PUNTO

    from src.analysis.los_dos_techos import (
        techo_del_que_se_queda,
    )

    assert EUROS_POR_PUNTO == 30_000

    visto = techo_del_que_se_queda(
        TRENT,
        puntos_de_mas_por_jornada=2,
        jornadas_que_quedan=30,
    )

    assert visto["available"] is True, visto

    assert visto["premios"] == 1_800_000, visto

    assert visto["puntos"] == 60.0, visto

    # Y es de otro orden de magnitud que el del comerciante.
    from src.analysis.los_dos_techos import (
        techo_del_comerciante,
    )

    del_comerciante = techo_del_comerciante(
        TRENT, PRIMA_COMPUTER
    )["techo"] - TRENT

    assert visto["premios"] > 50 * del_comerciante, (
        visto["premios"],
        del_comerciante,
    )


def test_ninguno_de_los_dos_se_inventa_si_falta_el_dato() -> None:
    """
    DOCTRINA 36, en los dos.

    Sin la prima medida del Computer no hay techo del
    comerciante. Sin los puntos y las jornadas no hay techo del
    que se queda. Un techo inventado es peor que no tenerlo:
    parece medido.
    """

    from src.analysis.los_dos_techos import (
        los_dos_techos,
        techo_del_comerciante,
        techo_del_que_se_queda,
    )

    sin_prima = techo_del_comerciante(TRENT, None)

    assert sin_prima["available"] is False, sin_prima
    assert sin_prima["techo"] is None, sin_prima
    assert "no se calcula" in sin_prima["reason"], sin_prima

    for faltan in (
        {"puntos_de_mas_por_jornada": None,
         "jornadas_que_quedan": 30},
        {"puntos_de_mas_por_jornada": 2,
         "jornadas_que_quedan": None},
    ):
        visto = techo_del_que_se_queda(TRENT, **faltan)

        assert visto["available"] is False, (faltan, visto)
        assert visto["premios"] is None, visto

    # Y sin precio, tampoco.
    assert techo_del_comerciante(0, PRIMA_COMPUTER)[
        "available"
    ] is False

    # Forma fija: nunca lanza, con lo que sea.
    for basura in (None, "hola", -1, {}):
        assert isinstance(
            los_dos_techos(basura), dict
        ), basura


# ============================================================
# 3. Y NO MUEVE NADA
# ============================================================


def test_publicar_los_dos_no_mueve_ningun_tope() -> None:
    """
    El encargo era publicar, no cambiar. `bid_cap` sigue donde
    estaba y con los mismos numeros.
    """

    from src.analysis.acquisition_board import (
        PRIMA_DE_EQUILIBRIO,
        PRIMA_MAXIMA_DE_PUJA,
    )

    assert round(100 * PRIMA_MAXIMA_DE_PUJA, 3) == 0.25, (
        PRIMA_MAXIMA_DE_PUJA
    )

    assert round(100 * PRIMA_DE_EQUILIBRIO, 3) == 1.8, (
        PRIMA_DE_EQUILIBRIO
    )


def test_el_tablero_publica_los_dos_y_cuenta_las_vias() -> None:
    """
    Que se vea CUAL se esta aplicando, por fila y en resumen.

    Y regla 24: "ninguna pasa el techo" y "ninguna lleva tope
    aplicado" son dos cosas distintas, y la segunda no prueba
    nada. El resumen las cuenta aparte.
    """

    from src.analysis.acquisition_board import (
        _resumen_de_los_techos,
    )

    from src.analysis.los_dos_techos import los_dos_techos

    filas = [
        {
            "name": "Trent",
            "los_dos_techos": los_dos_techos(
                TRENT,
                prima_computer_percent=PRIMA_COMPUTER,
                intent="SPECULATION",
                tope_aplicado=TOPE_APLICADO,
            ),
        },
        {
            "name": "Un titular",
            "los_dos_techos": los_dos_techos(
                5_000_000,
                prima_computer_percent=PRIMA_COMPUTER,
                intent="XI_UPGRADE",
                tope_aplicado=5_090_000,
            ),
        },
        {
            "name": "Sin plan",
            "los_dos_techos": los_dos_techos(
                1_000_000,
                prima_computer_percent=PRIMA_COMPUTER,
                intent="SPECULATION",
            ),
        },
    ]

    visto = _resumen_de_los_techos(filas)

    assert visto["available"] is True, visto

    assert visto["revender"] == 2, visto
    assert visto["quedarse"] == 1, visto

    # Solo dos llevan tope aplicado.
    assert visto["con_tope_aplicado"] == 2, visto

    nombres = {
        x["name"] for x in visto["pasan_el_del_comerciante"]
    }

    assert nombres == {"Trent", "Un titular"}, visto

    # Y sin filas NO pasa en vacio: lo dice.
    vacio = _resumen_de_los_techos([])

    assert vacio["con_tope_aplicado"] == 0, vacio

    assert "Ninguna lleva tope aplicado" in vacio["reason"], (
        vacio
    )


TESTS = [
    test_el_techo_del_comerciante_para_trent,
    test_el_tope_de_hoy_pasa_del_techo_del_comerciante,
    test_el_techo_del_que_se_queda_es_otra_moneda,
    test_ninguno_de_los_dos_se_inventa_si_falta_el_dato,
    test_publicar_los_dos_no_mueve_ningun_tope,
    test_el_tablero_publica_los_dos_y_cuenta_las_vias,
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
        f"LOS DOS TECHOS V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
