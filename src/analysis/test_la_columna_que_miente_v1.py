"""
La columna que mentia, y el viaje que no se conserva.

SINTOMA 1: «VALE» NO ERA LO QUE VALE (14/09/2026)

    La columna se llamaba VALE y traia el precio PUBLICADO, que
    lo elegimos nosotros. Medido en las trece filas con oferta de
    esa tarde, la relacion con el precio real iba de 0,97 a 1,48:

        jugador    pedimos      precio real   pedimos/precio
        Yamal      32.160.000    21.820.000        1,474
        Exposito    7.820.000     5.300.000        1,475
        Mangala     3.330.000     2.380.000        1,399
        Cepeda        640.000       660.000        0,970

    El lector veia "Yamal vale 32.160.000 y nos ofrecen
    20.896.900" y entendia un robo del 35 %. La prima de al lado
    decia -4,2 %, que es la verdad.

    Dos numeros que se contradicen en la misma fila, y gana el
    grande y redondo.

    Y no engaño solo al dueño: el 13/09 se escribio un informe
    diciendo que Trent habia subido un 13,75 % en un dia. Lo que
    habia subido era el precio al que lo pediamos. El mercado lo
    ponia en 2.650.000 sobre 2.760.000 de compra: el primer viaje
    del carril iba PERDIENDO 110.000.

SINTOMA 2: UN VIAJE «CONSERVADO»

    Trent salia con "buena, la conservamos". La decision era la
    correcta —la oferta de 2.749.700 se quedaba 37.900 por debajo
    del suelo de cobro, 2.787.600— pero la frase es la del motor
    de ofertas, que habla de la PLANTILLA.

    Un jugador comprado para revender no se conserva: o se cobra
    por encima del suelo, o se espera. Y lo que hace falta saber
    es CUANTO FALTA.

REGLA 23

    No lee estado externo: publicaciones, ofertas, catalogo y
    viajes se construyen aqui.

REGLA 24

    Ninguna de las dos pasa con las manos vacias.
"""

from __future__ import annotations

import re
from pathlib import Path


RAIZ = Path(__file__).parents[2]

PANEL = (
    RAIZ
    / "dashboard-v8"
    / "src"
    / "components"
    / "LoNuestroALaVentaPanel.jsx"
)


# LO QUE PEDIMOS Y LO QUE VALE, DISTINTOS A PROPOSITO.
#
#     Son los numeros medidos de la foto de las 18:12 del
#     14/09/2026, no un ejemplo inventado: si alguien "arregla"
#     la pantalla haciendo que las dos columnas salgan del mismo
#     sitio, estas cifras lo delatan.
CATALOGO = {
    26271: {"id": 26271, "name": "Yamal", "position": 4,
            "points": 45, "price": 21_820_000, "status": "ok",
            "teamID": 1},
    19862: {"id": 19862, "name": "Exposito", "position": 3,
            "points": 21, "price": 5_300_000, "status": "ok",
            "teamID": 3},
    37499: {"id": 37499, "name": "Trent", "position": 2,
            "points": 6, "price": 2_650_000, "status": "ok",
            "teamID": 1},
}

LISTADOS = [
    {"player_id": 26271, "listed_price": 32_160_000,
     "hours_to_expiry": 12.0, "expired": False,
     "renew_required": False},
    {"player_id": 19862, "listed_price": 7_820_000,
     "hours_to_expiry": 33.5, "expired": False,
     "renew_required": False},
    {"player_id": 37499, "listed_price": 3_139_500,
     "hours_to_expiry": 33.5, "expired": False,
     "renew_required": False},
]

OFERTAS = [
    {"player_ids": [26271], "amount": 20_896_900,
     "premium_percent": -4.2, "action": "NEVER_SELL",
     "protection": "NEVER_AUTO_SELL", "counterparty": "COMPUTER",
     "hours_to_expiry": 9.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Jugador Franchise/NEVER_AUTO_SELL."},

    {"player_ids": [19862], "amount": 5_217_900,
     "premium_percent": -1.5, "action": "HOLD_OFFER",
     "protection": "PROTECTED", "counterparty": "COMPUTER",
     "hours_to_expiry": 33.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Se espera mejor oferta."},

    # TRENT. El motor de ofertas dice KEEP_GOOD_OFFER, que en la
    # plantilla se traduce "buena, la conservamos". Pero es un
    # VIAJE, y un viaje no se conserva.
    {"player_ids": [37499], "amount": 2_749_700,
     "premium_percent": 3.8, "action": "KEEP_GOOD_OFFER",
     "protection": "CONDITIONAL", "counterparty": "COMPUTER",
     "hours_to_expiry": 33.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Oferta buena, se conserva."},
]

# EL VIAJE DE TRENT, con el coste real: 2.760.000.
VIAJES = {
    "available": True,
    "viajes": [
        {"player_id": 37499, "name": "Trent", "position": 2,
         "cost": 2_760_000, "state": "ABIERTO", "via": "CARRIL",
         "market_price": 2_650_000},
    ],
    "sin_coste": [],
    "reason": "1 viaje(s) abierto(s).",
}

# LO QUE SALE DE `precio_de_salida(2.760.000, 0.01)`.
SUELO_DE_TRENT = 2_787_600

FALTA_TRENT = SUELO_DE_TRENT - 2_749_700          # 37.900


def _venta(**cambios):
    from src.analysis.lo_nuestro_a_la_venta import (
        lo_nuestro_a_la_venta,
    )

    argumentos = {
        "listados": LISTADOS,
        "ofertas": OFERTAS,
        "catalogo": CATALOGO,
        "once": None,
        "sin_listar": None,
        "renovacion": None,
        "viajes": VIAJES,
    }

    argumentos.update(cambios)

    return lo_nuestro_a_la_venta(**argumentos)


def _por_nombre(visto, nombre):
    for fila in visto["players"]:
        if fila["name"] == nombre:
            return fila

    raise AssertionError(f"no esta {nombre}")


def _jsx_sin_comentarios(fuente: str) -> str:
    fuente = re.sub(r"/\*.*?\*/", " ", fuente, flags=re.S)

    return re.sub(r"(?m)^\s*//.*$", " ", fuente)


# ============================================================
# 1. LA PRIMA SE MIDE CONTRA EL PRECIO DE MERCADO
# ============================================================


def test_la_prima_se_mide_contra_el_precio_de_mercado() -> None:
    """
    Las dos columnas, con su nombre, y la prima contra la buena.

    LO QUE ROMPE ESTA GUARDIA

        Que vuelva una sola columna llamada VALE con el precio
        publicado dentro. Es la forma que tenia el fallo: un
        numero verdadero con el nombre de otro.

    LAS CIFRAS SON LAS MEDIDAS, NO UN EJEMPLO

        Yamal pedido a 32.160.000 sobre un mercado de 21.820.000.
        Si alguien hiciera que las dos columnas salieran del mismo
        sitio, esta diferencia lo delata.
    """

    visto = _venta()

    assert visto["available"] is True, visto

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(visto["players"]) == len(LISTADOS), visto

    # 1. LAS DOS COLUMNAS EXISTEN Y NO SON LA MISMA.
    yamal = _por_nombre(visto, "Yamal")

    assert yamal["lo_que_pedimos"] == 32_160_000, yamal
    assert yamal["precio_de_mercado"] == 21_820_000, yamal

    assert yamal["lo_que_pedimos"] != yamal["precio_de_mercado"], (
        "las dos columnas traen el mismo numero: o se ha caido "
        "una de las dos fuentes, o alguien las ha vuelto a unir"
    )

    # 2. Y LA COLUMNA QUE MENTIA YA NO ESTA.
    #
    #    Mientras `vale` siguiera publicandose, la pantalla vieja
    #    seguiria pintandola y el fallo seguiria vivo.
    assert "vale" not in yamal, (
        "sigue publicandose `vale`, que era el precio pedido con "
        "nombre de precio real"
    )

    # 3. LA PRIMA ES LA DEL MERCADO, Y SE DICE CONTRA QUE.
    #
    #    20.896.900 sobre 21.820.000 son -4,2 %. Sobre lo que
    #    pedimos serian -35 %, que es justo lo que el lector
    #    entendia.
    assert yamal["prima"] == -4.2, yamal

    contra_el_mercado = round(
        (yamal["nos_ofrecen"] / yamal["precio_de_mercado"] - 1)
        * 100,
        1,
    )

    assert yamal["prima"] == contra_el_mercado, (
        f"la prima publicada ({yamal['prima']} %) no es la del "
        f"precio de mercado ({contra_el_mercado} %)"
    )

    assert yamal["prima_contra"] == "PRECIO DE MERCADO", yamal

    assert visto["prima_contra"] == "PRECIO DE MERCADO", visto

    assert "PRECIO DE MERCADO" in (visto["prima_reason"] or ""), (
        visto["prima_reason"]
    )

    # 4. SIN PRIMA NO SE DICE CONTRA QUE.
    #
    #    Un "contra el precio de mercado" al lado de una casilla
    #    vacia promete una medicion que no existe.
    sin_oferta = _venta(ofertas=[])

    assert len(sin_oferta["players"]) == len(LISTADOS), sin_oferta

    for fila in sin_oferta["players"]:
        assert fila["prima"] is None, fila
        assert fila["prima_contra"] is None, fila

    # 5. Y LA PANTALLA PINTA LAS DOS, con la cabecera puesta.
    jsx = _jsx_sin_comentarios(
        PANEL.read_text(encoding="utf-8")
    )

    assert "LO QUE PEDIMOS" in jsx, (
        "la cabecera no dice LO QUE PEDIMOS"
    )

    assert "PRECIO DE MERCADO" in jsx, (
        "la cabecera no dice PRECIO DE MERCADO"
    )

    assert "fila.lo_que_pedimos" in jsx, (
        "la pantalla no pinta lo que pedimos"
    )

    assert "fila.precio_de_mercado" in jsx, (
        "la pantalla no pinta el precio de mercado"
    )

    assert "fila.vale" not in jsx, (
        "la pantalla sigue pintando `fila.vale`"
    )

    assert "prima_contra" in jsx, (
        "la pantalla no dice contra que se mide la prima"
    )


# ============================================================
# 2. UN VIAJE DEL CARRIL NO SE CONSERVA
# ============================================================


def test_un_viaje_del_carril_no_se_conserva() -> None:
    """
    De un viaje habla el carril, y dice cuanto falta.

    LA DECISION NO CAMBIA. Trent no se vende ni antes ni ahora:
    la oferta esta por debajo del suelo. Lo que cambia es que la
    pantalla deja de llamarlo "conservar" y pone el numero que
    falta.

    EL SUELO NO SE ESCRIBE EN LA PANTALLA

        Sale de `precio_de_salida`, la misma funcion con la que
        `que_cobrar` decide de verdad. Esta guardia lo comprueba
        llamandola: si alguien copiara el 1 % a mano en el cuadro
        y luego cambiara el del motor, aqui se veria.
    """

    import ast

    from src.analysis.salida_del_viaje import (
        SUELO_DEL_VIAJE,
        precio_de_salida,
    )

    # EL SUELO ES EL DEL MOTOR, y vale lo que dice el sintoma.
    assert (
        precio_de_salida(2_760_000, SUELO_DEL_VIAJE)
        == SUELO_DE_TRENT
    ), precio_de_salida(2_760_000, SUELO_DEL_VIAJE)

    # Y LA REGLA VIVE EN EL MOTOR, NO EN LA PANTALLA.
    #
    #     La primera version la escribio dentro del cuadro de
    #     reventas, y la guardia de ese cuadro se puso roja: alli
    #     no puede haber ni un `<`. Tenia razon — una pantalla que
    #     compara es una pantalla que decide.
    #
    #     Asi que la regla se fue a `salida_del_viaje`, al lado de
    #     `que_cobrar` y con el mismo suelo. Esta comprobacion
    #     impide que vuelva.
    cuadro = (
        RAIZ / "src" / "analysis" / "lo_nuestro_a_la_venta.py"
    ).read_text(encoding="utf-8")

    assert not [
        nodo
        for nodo in ast.walk(ast.parse(cuadro))
        if isinstance(nodo, ast.Compare)
        and any(
            isinstance(op, (ast.Gt, ast.GtE, ast.Lt, ast.LtE))
            for op in nodo.ops
        )
    ], (
        "el cuadro de reventas ha vuelto a comparar: la regla del "
        "carril tiene que vivir en `salida_del_viaje`"
    )

    assert "como_va_el_viaje" in cuadro, (
        "el cuadro ya no llama a la regla del carril"
    )

    visto = _venta()

    # REGLA 24: sin viajes en la lista esto no probaria nada.
    assert visto["viajes_abiertos"] == 1, visto

    trent = _por_nombre(visto, "Trent")

    assert trent["es_viaje"] is True, trent

    # 1. NI «CONSERVAR» NI NADA QUE SE LE PAREZCA.
    assert "conserv" not in trent["que_va_a_hacer"].lower(), trent

    assert trent["que_va_a_hacer"] == (
        "no llega al suelo de cobro"
    ), trent

    # 2. CON EL NUMERO QUE FALTA, que es lo que se necesita saber.
    assert trent["suelo_de_cobro"] == SUELO_DE_TRENT, trent

    assert trent["falta_para_el_suelo"] == FALTA_TRENT, trent

    assert "37.900" in trent["por_que"], trent["por_que"]

    assert "2.787.600" in trent["por_que"], trent["por_que"]

    # 3. LA ETIQUETA LA FIRMA EL CARRIL, y la accion del motor de
    #    ofertas sigue publicada: no se esconde, se encuadra.
    assert trent["etiqueta_de"] == "CARRIL", trent

    assert trent["accion_del_motor"] == "KEEP_GOOD_OFFER", trent

    assert trent["decidido"] is True, trent

    # 4. LOS QUE NO SON VIAJE NO CAMBIAN.
    #
    #    Esta regla es del carril, no de la plantilla. Si se
    #    colara en todas las filas, Exposito dejaria de decir lo
    #    que el motor de ofertas decidio.
    exposito = _por_nombre(visto, "Exposito")

    assert exposito["es_viaje"] is False, exposito
    assert exposito["etiqueta_de"] == "MOTOR_DE_OFERTAS", exposito
    assert exposito["que_va_a_hacer"] == (
        "esperar mejor oferta"
    ), exposito
    assert exposito["suelo_de_cobro"] is None, exposito

    # 5. UN VIAJE SIN COSTE NO SE JUZGA, y lo dice.
    #
    #    Es la prohibicion 0 de `que_cobrar` en cristiano: un
    #    suelo que no se puede calcular no es cero, es no vender.
    sin_coste = _venta(
        viajes={
            "available": True,
            "viajes": [],
            "sin_coste": [
                {"player_id": 37499, "name": "Trent",
                 "position": 2, "cost": 0, "state": "ABIERTO"},
            ],
            "reason": "1 sin coste conocido.",
        }
    )

    assert sin_coste["viajes_abiertos"] == 1, sin_coste

    ciego = _por_nombre(sin_coste, "Trent")

    assert ciego["es_viaje"] is True, ciego
    assert ciego["que_va_a_hacer"] == (
        "no se sabe lo que costo"
    ), ciego
    assert ciego["suelo_de_cobro"] is None, ciego
    assert "no vender" in ciego["por_que"], ciego["por_que"]

    # 6. Y SIN VIAJES, EL CUADRO ES EL DE SIEMPRE.
    #
    #    La regla la enciende el hecho de que haya un viaje
    #    abierto, no un interruptor.
    sin_viajes = _venta(viajes=None)

    assert len(sin_viajes["players"]) == len(LISTADOS), sin_viajes

    assert sin_viajes["viajes_abiertos"] == 0, sin_viajes

    de_plantilla = _por_nombre(sin_viajes, "Trent")

    assert de_plantilla["es_viaje"] is False, de_plantilla
    assert de_plantilla["que_va_a_hacer"] == (
        "buena, la conservamos"
    ), de_plantilla

    # 7. Y LA PANTALLA PINTA LO QUE FALTA.
    jsx = _jsx_sin_comentarios(
        PANEL.read_text(encoding="utf-8")
    )

    assert "fila.falta_para_el_suelo" in jsx, (
        "la pantalla no pinta cuanto falta para el suelo"
    )


TESTS = [
    test_la_prima_se_mide_contra_el_precio_de_mercado,
    test_un_viaje_del_carril_no_se_conserva,
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
        f"LA COLUMNA QUE MIENTE V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
