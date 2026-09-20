"""
Al que paga mas no se le exige mas.

LO QUE ESTABA DEL REVES, MEDIDO

    Las 23 operaciones cerradas de la temporada, del 10/08 al
    20/09/2026:

        al Computer   n=21   +0,55 % de mediana   2,8 dias
        a un manager  n= 2   +12,2 % y +143,3 %   6 y 18,6 dias

    Y el liston que le poniamos a cada uno:

        al Computer   `PREMIUM_GOOD` = +3 % sobre mercado
        al manager    mercado x (1 + hasta 25 %)
                              x (1 + hasta 18 % + primas)

    Las cinco ofertas de manager que nos llegaron -12 y 13/08-
    estaban en +2,6 % a +6,4 %, y las cinco se contraofertaron.

LO QUE ESTA GUARDIA EXIGE, Y NO DEPENDE DEL NUMERO QUE SE PONGA

    La regla la sostiene el codigo, no el margen que escriba el
    dueño en el entorno: aunque ponga 50 puntos porcentuales, el
    liston del manager no puede pasar del que le pedimos al
    Computer.

    Y las otras dos barandillas:

        · SOLO BAJA. El liston no puede hacernos rechazar una
          oferta que hoy aceptariamos.
        · LA EXCEPCION DEL ONCE NO SE TOCA. Con `in_lineup` el
          liston no se aplica.

REGLA 23 Y DOCTRINA 24

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj:
    las ofertas se construyen aqui. Y si el caso no trajese
    ninguna oferta de manager, la guardia FALLA en vez de pasar
    sin haber mirado nada.
"""

from __future__ import annotations

import os

from src.analysis.competitive_transaction_engine import (
    ENV_LISTON_DEL_MANAGER,
    ENV_MARGEN_DEL_MANAGER,
    VARA_DEL_COMPUTER_PERCENT,
    evaluate_sale_to_rival,
    liston_del_manager,
    liston_del_manager_activo,
    techo_del_liston_del_manager,
)

from src.analysis.offer_decision_engine import PREMIUM_GOOD


# ----------------------------------------------------------------
# LAS CINCO QUE NOS LLEGARON DE VERDAD  (12 y 13/08/2026)
#
#     Importe y valor de mercado del momento, sacados de las
#     fotos de esos dos dias. Van copiadas aqui porque una
#     guardia no lee `data/` (regla 23); lo que se comprueba es
#     el codigo, no el fichero.
# ----------------------------------------------------------------

LAS_CINCO = (
    ("Yeray",        2_000_000, 1_880_000, False),
    ("Ximo Navarro", 1_200_000, 1_170_000, False),
    ("Jutgla",       4_300_000, 4_120_000, True),
    ("Olasagasti",   2_750_000, 2_620_000, True),
    ("Olasagasti",   2_740_000, 2_660_000, True),
)


# Margenes absurdos incluidos a proposito: la regla tiene que
# aguantar el numero que sea.
MARGENES = (0.0, 1.0, 2.0, 2.45, 3.0, 10.0, 50.0)


def _con(margen, fn):
    """Corre `fn` con el interruptor puesto y ese margen."""

    antes = (
        os.environ.get(ENV_LISTON_DEL_MANAGER),
        os.environ.get(ENV_MARGEN_DEL_MANAGER),
    )

    try:
        os.environ[ENV_LISTON_DEL_MANAGER] = "1"

        if margen is None:
            os.environ.pop(ENV_MARGEN_DEL_MANAGER, None)
        else:
            os.environ[ENV_MARGEN_DEL_MANAGER] = str(margen)

        return fn()

    finally:

        for clave, valor in zip(
            (ENV_LISTON_DEL_MANAGER, ENV_MARGEN_DEL_MANAGER), antes
        ):
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor


# EL INTERRUPTOR LO PONE ESTA GUARDIA, NO EL ENTORNO
# (20/09/2026, y costo dos vueltas)
#
#     `_evalua` heredaba el entorno. Con
#     `BORDALAS_LISTON_DEL_MANAGER` puesto en el `env` del
#     workflow, todo lo que esta guardia llama «apagado» habria
#     corrido ENCENDIDO, y la prueba de abajo habria dado una
#     roja que nadie sabria leer. Doctrina 104.
#
#     Para «apagado» se BORRAN las dos variables, que es el
#     estado de una maquina limpia, no se ponen a "0".


def _sin(fn):
    """Corre `fn` con los dos interruptores BORRADOS."""

    antes = (
        os.environ.get(ENV_LISTON_DEL_MANAGER),
        os.environ.get(ENV_MARGEN_DEL_MANAGER),
    )

    try:

        for clave in (
            ENV_LISTON_DEL_MANAGER, ENV_MARGEN_DEL_MANAGER
        ):
            os.environ.pop(clave, None)

        return fn()

    finally:

        for clave, valor in zip(
            (ENV_LISTON_DEL_MANAGER, ENV_MARGEN_DEL_MANAGER), antes
        ):
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor


def _evalua(importe, mercado, in_lineup):
    """La evaluacion de HOY: con el liston apagado del todo."""

    return _sin(
        lambda: evaluate_sale_to_rival(
            amount=importe,
            market_value=mercado,
            rival_user_id=14145555,
            rival_intelligence={},
            in_lineup=in_lineup,
        )
    )


# ============================================================
# 1. EL CASO TIENE QUE TRAER OFERTAS DE MANAGER
# ============================================================


def test_sin_oferta_de_manager_no_se_comprueba_nada() -> None:
    """
    Doctrina 24. Sin ofertas no hay nada contra lo que comparar
    un liston, y cualquier implementacion pasaria.
    """

    assert LAS_CINCO, (
        "el caso no trae ni una oferta de manager: esta guardia "
        "no comprueba nada"
    )

    fuera_del_once = [o for o in LAS_CINCO if not o[3]]

    assert fuera_del_once, (
        "las cinco ofertas del caso son por jugadores del once: "
        "el liston nunca llegaria a aplicarse y la prueba de "
        "abajo seria vacia"
    )

    for nombre, importe, mercado, _ in LAS_CINCO:

        assert mercado > 0 and importe > 0, (
            f"la oferta por {nombre} no tiene importe o mercado: "
            f"{importe} / {mercado}"
        )


# ============================================================
# 2. LA PRUEBA QUE DA NOMBRE AL FICHERO
# ============================================================


def test_al_manager_no_se_le_exige_mas_que_al_computer() -> None:
    """
    Con la misma oferta en euros, el liston del manager no puede
    ser mas alto que el del Computer.
    """

    mirados = 0

    for nombre, importe, mercado, in_lineup in LAS_CINCO:

        if in_lineup:
            continue

        techo = techo_del_liston_del_manager(mercado)

        assert techo == int(mercado * (1.0 + PREMIUM_GOOD / 100.0)), (
            f"el techo de {nombre} no es el liston del Computer: "
            f"{techo:,} contra {int(mercado * (1.0 + PREMIUM_GOOD / 100.0)):,}"
        ).replace(",", ".")

        for margen in MARGENES:

            precio, motivo = _con(
                margen,
                lambda: liston_del_manager(
                    market_value=mercado,
                    strategic_sell_price=999_000_000,
                    in_lineup=False,
                ),
            )

            mirados += 1

            assert precio <= techo, (
                f"con margen {margen} pp, a {nombre} se le pide "
                f"{precio:,} y al Computer {techo:,}: le estamos "
                f"exigiendo mas al que paga mas"
            ).replace(",", ".")

            assert motivo, (
                f"el liston de {nombre} cambio el precio y no "
                f"dijo por que (regla 28)"
            )

    assert mirados == len(MARGENES) * len(
        [o for o in LAS_CINCO if not o[3]]
    ), (
        f"se han mirado {mirados} combinaciones y no las "
        f"esperadas: la prueba se esta saltando casos"
    )


# ============================================================
# 3. EL LISTON SOLO BAJA
# ============================================================


def test_el_liston_no_puede_hacernos_rechazar_lo_que_hoy_cogemos() -> None:

    for nombre, importe, mercado, in_lineup in LAS_CINCO:

        hoy = _evalua(importe, mercado, in_lineup)

        estrategico = hoy["strategic_sell_price"]

        for margen in MARGENES:

            precio, _ = _con(
                margen,
                lambda: liston_del_manager(
                    market_value=mercado,
                    strategic_sell_price=estrategico,
                    in_lineup=in_lineup,
                ),
            )

            assert precio <= estrategico, (
                f"con margen {margen} pp el liston de {nombre} "
                f"sube de {estrategico:,} a {precio:,}: el "
                f"interruptor solo puede bajar"
            ).replace(",", ".")


# ============================================================
# 4. LA EXCEPCION DEL ONCE NO SE TOCA
# ============================================================


def test_la_excepcion_del_once_sigue_entera() -> None:
    """
    Un jugador del once no se vende aunque paguen de mas. El
    liston baja el suelo, y bajarselo a un titular seria abrir
    justo la puerta que el dueño dejo cerrada.
    """

    del_once = [o for o in LAS_CINCO if o[3]]

    assert del_once, (
        "el caso no trae ni un jugador del once: no se puede "
        "comprobar que la excepcion aguanta"
    )

    for nombre, importe, mercado, _ in del_once:

        estrategico = _evalua(importe, mercado, True)[
            "strategic_sell_price"
        ]

        for margen in MARGENES:

            precio, motivo = _con(
                margen,
                lambda: liston_del_manager(
                    market_value=mercado,
                    strategic_sell_price=estrategico,
                    in_lineup=True,
                ),
            )

            assert precio == estrategico, (
                f"con margen {margen} pp, a {nombre} -que esta "
                f"en el once- se le ha bajado el suelo de "
                f"{estrategico:,} a {precio:,}"
            ).replace(",", ".")

            assert "once" in str(motivo).lower(), (
                f"el motivo de {nombre} no nombra la excepcion "
                f"del once: {motivo}"
            )


# ============================================================
# 5. ENCENDIDO Y SIN MARGEN NO DECIDE NADA
# ============================================================


def test_encendido_sin_margen_no_baja_el_suelo() -> None:
    """
    El margen lo pone el dueño. Un liston encendido sin numero
    aceptaria a +0,55 %, y eso no lo ha decidido nadie: se
    queda el precio estrategico y se dice.
    """

    for nombre, importe, mercado, in_lineup in LAS_CINCO:

        estrategico = _evalua(importe, mercado, in_lineup)[
            "strategic_sell_price"
        ]

        precio, motivo = _con(
            None,
            lambda: liston_del_manager(
                market_value=mercado,
                strategic_sell_price=estrategico,
                in_lineup=in_lineup,
            ),
        )

        assert precio == estrategico, (
            f"sin margen puesto, el liston de {nombre} ya baja "
            f"el suelo a {precio:,}"
        ).replace(",", ".")

        assert motivo, (
            f"el liston de {nombre} esta encendido, no hace nada "
            f"y no lo dice"
        )


# ============================================================
# 6. APAGADO, EXACTAMENTE COMO AYER
# ============================================================


def test_apagado_se_comporta_como_ayer() -> None:

    # LO APAGA ESTA GUARDIA, y de paso comprueba que el lector
    # sigue al entorno despues del import: si lo cacheara,
    # borrarlo aqui dentro no cambiaria nada.
    assert _sin(lambda: liston_del_manager_activo()) is False, (
        "con la variable borrada, el lector sigue diciendo que "
        "el liston esta puesto: o lo cachea al importarse, o lo "
        "lee de otro sitio"
    )

    assert _con(2.45, lambda: liston_del_manager_activo()) is True, (
        "con la variable puesta a \"1\" el lector sigue diciendo "
        "que esta apagado: cachea el valor y esta guardia no "
        "controla nada"
    )

    for nombre, importe, mercado, in_lineup in LAS_CINCO:

        salida = _evalua(importe, mercado, in_lineup)

        assert (
            salida["liston_del_manager"]
            == salida["strategic_sell_price"]
        ), (
            f"apagado, el liston de {nombre} ya no es el precio "
            f"estrategico: {salida['liston_del_manager']:,} "
            f"contra {salida['strategic_sell_price']:,}"
        ).replace(",", ".")

        assert salida["liston_del_manager_reason"] is None, (
            f"apagado, el liston de {nombre} publica motivo: "
            f"{salida['liston_del_manager_reason']}"
        )

        # Las cinco se contraofertaron, y apagado se siguen
        # contraofertando: ni una decision cambia.
        assert salida["decision"] == "COUNTER_OFFER", (
            f"apagado, la oferta por {nombre} ya no se "
            f"contraoferta: {salida['decision']}"
        )


# ============================================================
# 7. LA VARA ES LA MEDIDA, NO UN NUMERO NUEVO
# ============================================================


def test_la_vara_del_computer_es_la_medida() -> None:
    """
    Regla 18 y doctrina 84. Si alguien mueve este numero sin
    volver a medir, aqui salta.
    """

    assert VARA_DEL_COMPUTER_PERCENT == 0.55, (
        f"la vara del Computer ha dejado de ser la mediana "
        f"medida en 21 ventas cerradas: vale "
        f"{VARA_DEL_COMPUTER_PERCENT}"
    )

    assert PREMIUM_GOOD == 3.0, (
        f"el liston del Computer ha cambiado y el techo del "
        f"manager cuelga de el: vale {PREMIUM_GOOD}"
    )

    assert VARA_DEL_COMPUTER_PERCENT < PREMIUM_GOOD, (
        "lo que el Computer DA ha pasado a ser mayor que lo que "
        "le PEDIMOS: el liston del manager deja de tener sentido"
    )


def main() -> int:

    pruebas = [
        test_sin_oferta_de_manager_no_se_comprueba_nada,
        test_al_manager_no_se_le_exige_mas_que_al_computer,
        test_el_liston_no_puede_hacernos_rechazar_lo_que_hoy_cogemos,
        test_la_excepcion_del_once_sigue_entera,
        test_encendido_sin_margen_no_baja_el_suelo,
        test_apagado_se_comporta_como_ayer,
        test_la_vara_del_computer_es_la_medida,
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
        f"EL LISTON DEL MANAGER V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
