"""
La cesta opera en el suelo, que es donde gana.

LA DECISION DEL DUEÑO (20/09/2026), Y SU MOTIVO

    Medido sobre las 23 operaciones CERRADAS de la temporada, por
    tramo del precio de COMPRA y vendiendo al Computer:

        suelo (<300 k)   n= 8   +1,51 %   100 % verde     +28.867
        300 k - 1,5 M    n= 4   -1,50 %    25 %          +109.399
        1,5 M - 3 M      n= 9   -2,57 %    33 %        -1.038.783
        >= 3 M           n= 0        -        -                 -

    Al Computer vendemos rapido y a mercado (+0,55 % de mediana
    en 21 ventas). A un manager, tarde y con prima (+7,5 %,
    +23,8 % y +32,0 % en tres).

EL CORTE NO ES UN NUMERO NUEVO

    Es `CORTES_DE_PRECIO[0]`, el mismo 1.500.000 que ya parte la
    rejilla de la pelea y la de la prima por tramo. Doctrina 84:
    tres cosas del mismo eje, el mismo corte.

LO QUE ESTA MEDICION NO DICE, Y HAY QUE DECIRLO

    De las NUEVE operaciones cerradas por encima del corte, la
    cesta hizo UNA -Balde, -25.501 EUR-. Las otras ocho son del
    carril (3, -237.847) y de compras sin libro (5, -775.435).

    Asi que este corte ahorra 25.501 EUR medidos, no un millon.
    Es correcto —la unica operacion de la cesta por encima del
    suelo perdio— pero apunta a la via que hizo el 2,5 % del
    daño.

REGLA 23 Y DOCTRINA 24

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj:
    candidatos construidos aqui. Y si todos cayeran por debajo
    del corte, la guardia FALLA: no habria comprobado que corta
    nada.
"""

from __future__ import annotations

import os

from src.analysis.la_subasta import (
    CORTES_DE_PRECIO,
    ENV_SOLO_EL_SUELO,
    candidatos_en_modo_cartera,
    solo_el_suelo,
)


PRIMA = 0.0234


# Dos por debajo del corte y dos por encima. Si alguien los
# iguala, la guardia se queda sin nada que mirar y lo dice.
PRECIOS = (150_000, 1_400_000, 1_600_000, 5_000_000)


def _candidatos(precios=PRECIOS) -> list:
    return [
        {"id": 500 + i, "name": f"P{p}", "market_price": p}
        for i, p in enumerate(precios)
    ]


# EL INTERRUPTOR LO PONE ESTA GUARDIA, NO EL ENTORNO
# (20/09/2026, y costo dos vueltas)
#
#     La prueba de «apagado» empezaba comprobando que el
#     interruptor NO estuviese puesto en el entorno. La noche
#     que se encendio uno en el `env` del workflow, la guardia
#     hermana se puso roja y el ciclo no arranco.
#
#     Doctrina 104. Y para «apagado» se BORRA la variable, que
#     es el estado de una maquina limpia, no se pone a "0".


def _poner(valor):
    """Pone o BORRA el interruptor. Devuelve lo que habia."""

    antes = os.environ.get(ENV_SOLO_EL_SUELO)

    if valor is None:
        os.environ.pop(ENV_SOLO_EL_SUELO, None)
    else:
        os.environ[ENV_SOLO_EL_SUELO] = valor

    return antes


def _con(precios, encendido: bool) -> list:

    antes = _poner("1" if encendido else None)

    try:
        return candidatos_en_modo_cartera(
            _candidatos(precios), PRIMA
        )

    finally:
        _poner(antes)


# ============================================================
# 1. LA MUESTRA TIENE QUE CRUZAR EL CORTE
# ============================================================


def test_sin_candidatos_arriba_no_se_comprueba_nada() -> None:
    """
    Doctrina 24, aplicada a esta guardia. Con todos por debajo
    del corte, cualquier implementacion pasa.
    """

    corte = CORTES_DE_PRECIO[0]

    arriba = [p for p in PRECIOS if p >= corte]

    abajo = [p for p in PRECIOS if p < corte]

    assert arriba, (
        f"todos los candidatos de la prueba estan por debajo de "
        f"{corte:,}: la guardia no llega a ver el corte"
    ).replace(",", ".")

    assert abajo, (
        f"todos los candidatos estan por encima de {corte:,}: "
        f"no se puede comprobar que lo de abajo sobrevive"
    ).replace(",", ".")


# ============================================================
# 2. EL CORTE CORTA
# ============================================================


def test_la_cesta_no_opera_arriba_del_suelo() -> None:
    """
    LA PRUEBA QUE DA NOMBRE AL FICHERO.

    Con el interruptor puesto, un candidato por encima del corte
    no genera puja de reventa.
    """

    corte = CORTES_DE_PRECIO[0]

    salida = _con(PRECIOS, encendido=True)

    precios = {c["market_price"] for c in salida}

    arriba = {p for p in precios if p >= corte}

    assert not arriba, (
        f"con el interruptor puesto la cesta sigue generando "
        f"puja para {sorted(arriba)}, que estan por encima de "
        f"{corte:,}"
    ).replace(",", ".")

    # Y lo de abajo sigue entero: cerrar no es borrar.
    assert precios == {
        p for p in PRECIOS if p < corte
    }, (
        f"el corte se ha llevado tambien candidatos del suelo: "
        f"quedan {sorted(precios)}"
    )


def test_el_corte_es_el_que_ya_existia() -> None:
    """
    Doctrina 84. Si alguien mete un numero nuevo para esto, aqui
    salta: la rejilla de la pelea, la de la prima y esta tienen
    que partir por el mismo sitio.
    """

    from src.analysis.computer_resale_premium import (
        CORTES_DE_LA_PRIMA,
    )

    corte = CORTES_DE_PRECIO[0]

    assert corte == 1_500_000, (
        f"el corte de la cesta ha dejado de ser "
        f"`CORTES_DE_PRECIO[0]`: vale {corte:,}"
    ).replace(",", ".")

    assert corte in CORTES_DE_LA_PRIMA, (
        "la rejilla de la prima ya no parte por el mismo sitio "
        "que la de la pelea: son dos rejillas para el mismo eje"
    )


# ============================================================
# 3. APAGADO, EXACTAMENTE COMO AYER
# ============================================================


def test_apagado_se_comporta_como_ayer() -> None:

    # LO APAGA ESTA GUARDIA, y ademas comprueba que el lector
    # sigue al entorno despues del import: si lo cacheara,
    # apagarlo aqui dentro no serviria de nada.
    antes = _poner(None)

    try:
        assert not solo_el_suelo(), (
            "con la variable borrada, el lector sigue diciendo "
            "que el interruptor esta puesto: o lo cachea al "
            "importarse, o lo lee de otro sitio"
        )

        _poner("1")

        assert solo_el_suelo(), (
            "puesta a \"1\" el lector sigue diciendo que esta "
            "apagado: cachea el valor y esta guardia no "
            "controla nada"
        )

        _poner("0")

        assert not solo_el_suelo(), (
            "\"0\" no significa apagado para el lector: "
            "entonces borrarla y ponerla a cero no son lo mismo"
        )

    finally:
        _poner(antes)

    apagado = _con(PRECIOS, encendido=False)

    assert {c["market_price"] for c in apagado} == set(PRECIOS), (
        f"apagado, la cesta ya no valora a todos: "
        f"{sorted(c['market_price'] for c in apagado)}"
    )

    # Y la ganancia de los de abajo no cambia entre las dos
    # posiciones: el corte solo quita, no toca numeros.
    encendido = {
        c["market_price"]: c["expected_value"]
        for c in _con(PRECIOS, encendido=True)
    }

    for c in apagado:

        if c["market_price"] in encendido:

            assert (
                c["expected_value"]
                == encendido[c["market_price"]]
            ), (
                f"el corte cambia la ganancia de "
                f"{c['name']}: {c['expected_value']} -> "
                f"{encendido[c['market_price']]}"
            )


def main() -> int:

    pruebas = [
        test_sin_candidatos_arriba_no_se_comprueba_nada,
        test_la_cesta_no_opera_arriba_del_suelo,
        test_el_corte_es_el_que_ya_existia,
        test_apagado_se_comporta_como_ayer,
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
        f"LA CESTA SOLO EL SUELO V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
