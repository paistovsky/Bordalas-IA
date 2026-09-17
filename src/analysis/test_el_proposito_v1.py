"""
El propósito: el libro del escaparate, el mapa del `intent` y la sombra.

QUE SE PRUEBA AQUI

    1. `test_el_libro_no_duplica_el_reset`
       Dos vueltas dentro del mismo reset dejan UNA linea. Falla
       si la lista del escaparate llega vacia.

    2. `test_el_mapa_del_intent_no_miente`
       No se compara el mapa consigo mismo: se EJERCITA
       `optimal_bid` con cada etiqueta y se comprueba que pasa lo
       que el mapa dice. Y el mapa sale del arbol: si un fichero
       nuevo nombra el `intent` sin anotar, esto se pone rojo.

    3. `test_el_proposito_no_hereda_el_liston_de_otra_via`
       Un jugador que mejora el once no recibe el liston de
       especulacion. Falla si la lista de candidatos llega vacia.

    4. `test_ninguna_via_se_queda_sin_frenos`
       Cada proposito tiene liston, bolsillo, tope y minimo
       ASIGNADOS Y PUBLICADOS. Ninguno sale `None` a secas.

    5. `test_la_sombra_no_convierte_en_fichaje_lo_que_la_via_del_once_rechaza`

    6. `test_esto_sigue_apagado`

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    El libro se prueba contra una ruta temporal que la guardia
    crea y borra, nunca contra `data/`. Los instantes entran por
    argumento. El escaneo del mapa lee CODIGO, no estado.

UNA GUARDIA QUE NO MUERDE ES PEOR QUE NINGUNA

    Las doce inyecciones de fallo se probaron una a una, en
    memoria.

    Y AQUI LA QUE NO MORDIA NO ERA UNA GUARDIA, ERA EL MODULO:
    la primera version de `el_proposito` escribio de MEMORIA la
    lista de quien lee el `intent`, y salio mal en las dos
    direcciones —cinco ficheros que si lo nombran faltaban, y
    quince que no lo nombran sobraban—. El encargo pedia
    literalmente "que salga del codigo, no de la memoria" y a la
    primera no lo cumpli. Ahora lo escanea, y esta guardia
    comprueba el escaneo.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.analysis.el_proposito import (
    ENCENDIDO,
    INTENTS,
    SPECULATION,
    XI_UPGRADE,
    esta_encendido,
    frenos_de,
    lectores_del_intent,
    mapa_del_intent,
    que_cambiaria,
    valor_de_fichar_con_el_activo,
)
from src.analysis.rival_bid_model import optimal_bid
from src.intelligence.libro_del_escaparate import (
    apuntar_el_escaparate,
    construir_fila,
    dia_de_mercado,
)


# ============================================================
# LOS FIXTURES
# ============================================================

CURVA = [
    (1.0000, 0.1944),
    (1.0052, 0.1944),
    (1.0222, 0.2083),
    (1.0323, 0.1944),
    (1.0622, 0.1528),
    (1.2109, 0.0417),
    (1.2449, 0.0140),
]

RIVALES = [
    {"name": "Pollo17", "participation": 0.7548,
     "capacity": 14_284_872, "never_bids": False},
    {"name": "Luismi_Haz", "participation": 0.6133,
     "capacity": 25_772_293, "never_bids": False},
]

MODELO = {"premium": {"curve": CURVA}, "rivals": RIVALES}


# El escaparate de un reset, con la forma que publica el tablero.
ESCAPARATE = [
    {
        "id": 18398,
        "name": "Budimir",
        "position": 4,
        "market_price": 11_990_000,
        "points": 45,
        "played": 6,
        "starter_probability": 90.0,
        "hierarchy": "Clave",
    },
    {
        "id": 3720,
        "name": "Miguel Román",
        "position": 3,
        "market_price": 3_720_000,
        "points": 28,
        "played": 6,
        "starter_probability": 50.0,
        "hierarchy": "Importante",
    },
    {
        # Sin pronóstico: `None` no es cero, y tiene que viajar
        # como `None`.
        "id": 9999,
        "name": "Iturbe",
        "position": 1,
        "market_price": 150_000,
        "points": 0,
        "played": 0,
        "starter_probability": None,
        "hierarchy": None,
    },
]


# ============================================================
# 1. EL LIBRO NO DUPLICA EL RESET
# ============================================================


def test_el_libro_no_duplica_el_reset():
    """
    Dos vueltas dentro del mismo reset, una línea.
    """

    assert ESCAPARATE, (
        "la lista del escaparate llega vacía: sin escaparate esta "
        "guardia no prueba nada"
    )

    with tempfile.TemporaryDirectory() as carpeta:

        libro = Path(carpeta) / "libro_del_escaparate.jsonl"

        # 07:30 — después del reset de las 05:00.
        primera = apuntar_el_escaparate(
            ESCAPARATE,
            at="2026-09-17T07:30:55",
            foto_at="2026-09-17T07:23:08",
            ruta=libro,
        )

        assert primera["written"] is True
        assert primera["dia_de_mercado"] == "2026-09-17"

        # Otra vuelta el mismo reset: NO se duplica.
        segunda = apuntar_el_escaparate(
            ESCAPARATE,
            at="2026-09-17T09:15:00",
            foto_at="2026-09-17T09:14:00",
            ruta=libro,
        )

        assert segunda["written"] is False, (
            "dos vueltas del mismo reset han dejado dos líneas"
        )

        assert "no se duplica" in segunda["reason"]

        # ------------------------------------------------
        # Y EL CORTE ES EL RESET, NO LA MEDIANOCHE
        # ------------------------------------------------
        #
        #     Una vuelta de las 03:00 del 18 pertenece al
        #     escaparate del 17: el reset todavía no ha pasado. Si
        #     el corte fuera a medianoche, esto escribiría una
        #     segunda línea del mismo escaparate.
        madrugada = apuntar_el_escaparate(
            ESCAPARATE,
            at="2026-09-18T03:00:00",
            foto_at="2026-09-18T02:59:00",
            ruta=libro,
        )

        assert madrugada["written"] is False, (
            "una vuelta de las 03:00 es del escaparate de AYER: "
            "escribirla duplica el reset"
        )

        assert dia_de_mercado("2026-09-18T03:00:00") == "2026-09-17"

        # Pasado el reset, sí.
        siguiente = apuntar_el_escaparate(
            ESCAPARATE,
            at="2026-09-18T06:00:00",
            foto_at="2026-09-18T05:55:00",
            ruta=libro,
        )

        assert siguiente["written"] is True
        assert siguiente["dia_de_mercado"] == "2026-09-18"

        lineas = [
            json.loads(l)
            for l in libro.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]

        assert len(lineas) == 2, (
            f"cuatro vueltas y dos resets: dos líneas, no "
            f"{len(lineas)}"
        )

        # LO QUE SE GUARDA DE CADA UNO, que es la mitad que
        # faltaba para poder reconstruir «¿nos mejoraba?».
        jugador = lineas[0]["players"][0]

        for clave in (
            "id",
            "name",
            "position",
            "price",
            "points",
            "played",
            "starter_probability",
        ):
            assert clave in jugador, (
                f"falta `{clave}` en el libro: sin él no se puede "
                f"saber después si nos mejoraba"
            )

        sin_pronostico = next(
            j for j in lineas[0]["players"] if j["name"] == "Iturbe"
        )

        assert sin_pronostico["starter_probability"] is None, (
            "un jugador sin pronóstico tiene que viajar con `None`: "
            "un cero se leería como «seguro que no juega»"
        )

        assert lineas[0]["with_forecast"] == 2, (
            "el recuento de cuántos traen pronóstico se publica"
        )

        # ------------------------------------------------
        # EL ESCAPARATE VACIO: MUERDE AQUI
        # ------------------------------------------------
        vacio = apuntar_el_escaparate(
            [], foto_at="2026-09-18T05:55:00", ruta=libro
        )

        assert vacio["written"] is False, (
            "un reset que no se pudo leer no puede escribirse como "
            "un reset sin mercado"
        )

        assert vacio["available"] is False

        assert construir_fila([])["players"] == []

    print("  OK  dos vueltas del mismo reset dejan una sola línea")


# ============================================================
# 2. EL MAPA NO MIENTE
# ============================================================


def test_el_mapa_del_intent_no_miente():
    """
    Se ejercita el motor, no se lee el mapa contra sí mismo.
    """

    mapa = mapa_del_intent()

    assert mapa["available"]

    # --------------------------------------------------
    # EL MAPA SALE DEL ARBOL
    # --------------------------------------------------
    lectores = mapa["lectores"]

    assert lectores["n"] > 10, (
        f"solo {lectores['n']} ficheros nombran el `intent`: el "
        f"escaneo no está encontrando nada"
    )

    assert lectores["sin_anotar"] == [], (
        f"hay ficheros que nombran el `intent` y nadie ha escrito "
        f"qué deciden con él: {lectores['sin_anotar']}"
    )

    assert lectores["anotados_que_no_aparecen"] == [], (
        f"hay ficheros anotados que ya no nombran el `intent`: "
        f"{lectores['anotados_que_no_aparecen']}"
    )

    # Los dos que lo deciden, por su nombre.
    assert set(mapa["deciden"]) == {
        "src/analysis/deployment.py",
        "src/analysis/acquisition_valuation.py",
    }

    # --------------------------------------------------
    # Y AHORA SE COMPRUEBA CONTRA EL MOTOR
    # --------------------------------------------------
    #
    # Un jugador con margen de sobra, para que lo único que
    # cambie entre las dos llamadas sea la etiqueta.
    precio = 2_000_000

    valor = 4_000_000

    comun = {
        "price": precio,
        "value": valor,
        "model": MODELO,
        "available_budget": 50_000_000,
    }

    especulando = optimal_bid(intent=SPECULATION, **comun)

    fichando = optimal_bid(intent=XI_UPGRADE, **comun)

    # EL TOPE DE PRIMA: el mapa dice que solo aplica a
    # SPECULATION.
    tope = mapa["intents"][SPECULATION]["tope_de_prima"]

    assert tope["aplica"] is True

    limite = precio * (1 + tope["valor"])

    assert especulando["bid"] <= limite + 1, (
        f"el mapa dice que SPECULATION no pasa del "
        f"{tope['valor'] * 100:.2f} % y la puja es "
        f"{especulando['bid']} sobre un precio de {precio}"
    )

    assert mapa["intents"][XI_UPGRADE]["tope_de_prima"]["aplica"] is False

    assert fichando["bid"] > limite, (
        f"el mapa dice que XI_UPGRADE NO lleva tope de prima, y la "
        f"puja ({fichando['bid']}) no pasa del límite de la otra "
        f"vía ({limite:.0f}): o el mapa miente o el fixture no "
        f"tiene margen para demostrarlo"
    )

    # EL LISTON DEL 3 %: el mapa dice que solo aplica a
    # SPECULATION. Se busca un caso que rinda poco.
    liston = mapa["intents"][SPECULATION]["liston"]

    assert liston["aplica"] is True

    justito = {
        "price": 2_000_000,
        "value": 2_010_000,
        "model": MODELO,
        "available_budget": 50_000_000,
    }

    flojo = optimal_bid(intent=SPECULATION, **justito)

    assert flojo["decision"] == "RENDIMIENTO_INSUFICIENTE", (
        f"el mapa dice que SPECULATION exige un "
        f"{liston['valor'] * 100:.0f} % y este caso pasó: "
        f"{flojo['decision']}"
    )

    igual_fichando = optimal_bid(intent=XI_UPGRADE, **justito)

    assert igual_fichando["decision"] != "RENDIMIENTO_INSUFICIENTE", (
        "el mapa dice que XI_UPGRADE no lleva listón de "
        "rendimiento, y lo ha aplicado"
    )

    # Y LOS NUMEROS DEL MAPA SON LOS DEL MOTOR, no una copia.
    from src.analysis.rival_bid_model import (
        MIN_SPECULATION_EXPECTED_VALUE,
        PRIMA_MAXIMA_DE_PUJA,
        RENDIMIENTO_MINIMO_DEL_CAPITAL,
    )

    assert liston["valor"] == RENDIMIENTO_MINIMO_DEL_CAPITAL
    assert tope["valor"] == PRIMA_MAXIMA_DE_PUJA
    assert (
        mapa["intents"][SPECULATION]["minimo"]["valor"]
        == MIN_SPECULATION_EXPECTED_VALUE
    )

    print("  OK  el mapa dice lo que el motor hace, y sale del árbol")


# ============================================================
# 3. NINGUN PROPOSITO HEREDA EL LISTON DE OTRA VIA
# ============================================================

CANDIDATOS = [
    # Mejora el once y su valor SUPERA al precio: es un fichaje.
    # Es la forma de Kiko Femenía (05/09) y Rubén García (12/09).
    {
        "name": "Kiko Femenía",
        "market_price": 1_150_000,
        "xi_value": 1_494_925,
        "value": 1_200_000,
        "value_route": "COMPUTER_RESALE",
    },
    # Mejora el once pero no llega al precio: NO es un fichaje.
    # Es la forma de los seis de la foto del 17/09.
    {
        "name": "Budimir",
        "market_price": 11_990_000,
        "xi_value": 3_427_226,
        "value": 12_200_424,
        "value_route": "COMPUTER_RESALE",
    },
    # La vía del once le dio cero: no es candidato a fichaje por
    # mucho que valga como activo.
    {
        "name": "Mayol",
        "market_price": 470_000,
        "xi_value": 0,
        "value": 548_393,
        "value_route": "HOLD",
    },
    # Y EL CASO QUE ME MORDIO AL CORRERLO CONTRA LA FOTO: la vía
    # que da el máximo ES la del once, así que `value` y
    # `xi_value` son el MISMO euro. Sumarlos lo dobla. Pépé y
    # Chupe salían así el 17/09.
    {
        "name": "Pépé",
        "market_price": 11_480_000,
        "xi_value": 3_195_607,
        "value": 3_195_607,
        "value_route": "XI_UPGRADE",
    },
]


def test_el_proposito_no_hereda_el_liston_de_otra_via():
    """
    Un jugador que mejora el once no recibe el listón de
    especulación.
    """

    assert CANDIDATOS, (
        "la lista de candidatos llega vacía: sin candidatos esta "
        "guardia no prueba nada"
    )

    # El que pasa la puerta es un fichaje, y los frenos que se le
    # aplican son los del fichaje.
    frenos = frenos_de(XI_UPGRADE)

    assert frenos["available"]

    assert frenos["liston"]["aplica"] is False, (
        "un fichaje no puede recibir el listón de rendimiento "
        "sobre el capital: se paga en puntos, no en euros de "
        "reventa"
    )

    assert frenos["minimo"]["aplica"] is False

    assert frenos["bolsillo"]["nombre"] == "FICHAJES", (
        "un fichaje no puede medirse contra el bolsillo de "
        "especular"
    )

    # Y el de especular sí los lleva: si los dos fueran iguales,
    # esta guardia no probaría nada.
    otros = frenos_de(SPECULATION)

    assert otros["liston"]["aplica"] is True
    assert otros["bolsillo"]["nombre"] == "ESPECULACION"

    assert (
        frenos["bolsillo"]["nombre"] != otros["bolsillo"]["nombre"]
    ), "los dos propósitos no pueden compartir bolsillo"

    # UNA ETIQUETA DESCONOCIDA NO DECIDE NADA.
    assert frenos_de("LO_QUE_SEA")["available"] is False
    assert frenos_de(None)["available"] is False

    print("  OK  el fichaje no hereda el listón de la especulación")


# ============================================================
# 4. NINGUNA VIA SE QUEDA SIN FRENOS
# ============================================================


def test_ninguna_via_se_queda_sin_frenos():
    """
    Cada propósito tiene listón, bolsillo, tope y mínimo
    asignados y PUBLICADOS. Un `None` mudo es como se pierde un
    tope sin que nadie lo note.
    """

    mapa = mapa_del_intent()["intents"]

    assert set(mapa) == set(INTENTS)

    for etiqueta in INTENTS:

        ficha = mapa[etiqueta]

        for freno in ("liston", "tope_de_prima", "minimo"):

            datos = ficha[freno]

            assert "aplica" in datos, (
                f"{etiqueta}/{freno} no dice si aplica"
            )

            assert datos.get("que_es"), (
                f"{etiqueta}/{freno} no dice qué es. Un freno sin "
                f"explicación es un freno que nadie discute"
            )

            if datos["aplica"]:
                assert datos.get("valor") is not None, (
                    f"{etiqueta}/{freno} dice que aplica y no trae "
                    f"valor"
                )

            else:
                # Un freno que NO aplica tiene que decir qué hay
                # en su lugar, o el hueco pasa desapercibido.
                assert (
                    datos.get("en_su_lugar") or datos.get("aviso")
                ), (
                    f"{etiqueta}/{freno} no aplica y no dice qué "
                    f"hay en su lugar: ese es exactamente el freno "
                    f"huérfano que la doctrina 69 persigue"
                )

        assert ficha["bolsillo"]["nombre"], (
            f"{etiqueta} sale sin bolsillo"
        )

        assert ficha["bolsillo"]["de_donde"]

        assert ficha["probabilidad_minima"] is not None, (
            f"{etiqueta} sale sin probabilidad mínima de ganar"
        )

    # EL FRENO HUERFANO, DICHO POR SU NOMBRE.
    aviso = mapa[XI_UPGRADE]["tope_de_prima"]["aviso"]

    assert "69" in aviso, (
        "el tope de prima es el freno que se cae al mover la "
        "etiqueta, y eso tiene que estar escrito donde se lea"
    )

    print("  OK  ningún propósito se queda sin listón, bolsillo ni tope")


# ============================================================
# 5. LA SOMBRA
# ============================================================


def test_la_sombra_no_convierte_en_fichaje_lo_que_la_via_del_once_rechaza():
    """
    Contar el activo no puede resucitar a quien la vía del once
    valoró en cero.
    """

    cambio = que_cambiaria(
        CANDIDATOS,
        bolsillo_de_fichar=8_874_116,
        bolsillo_de_especular=5_324_469,
        techo_de_biwenger=13_743_516,
    )

    assert cambio["available"]

    assert cambio["pasan_ahora"] == 1, (
        "hoy solo pasa Kiko Femenía: su valor como fichaje supera "
        "al precio"
    )

    assert cambio["pasarian"] == 1, (
        "contando el activo pasaría además Budimir"
    )

    nombres = {f["name"] for f in cambio["los_que_pasarian"]}

    assert nombres == {"Budimir"}

    # PEPE NO, Y ESE ES EL CASO QUE ME MORDIO. Su `value` viene de
    # la vía del once, así que es el MISMO euro que `xi_value`:
    # sumarlos daría 6.391.214 sobre un precio de 11.480.000 —y
    # aun así no pasaría— pero el número estaría doblado y el día
    # que el precio fuera menor colaría un fichaje inventado.
    assert "Pépé" not in nombres

    pepe = next(f for f in CANDIDATOS if f["name"] == "Pépé")

    assert pepe["value"] == pepe["xi_value"], (
        "el fixture necesita un caso donde el máximo lo dé la vía "
        "del once, o no prueba el doble conteo"
    )

    # MAYOL NO. La vía del once le dio cero, y el activo no
    # convierte en fichaje lo que no mejora el once.
    assert "Mayol" not in nombres, (
        "Mayol tiene valor como activo (548.393) por encima de su "
        "precio (470.000), pero la vía del once le dio CERO: "
        "contarlo como fichaje sería fichar a quien no mejora"
    )

    # EL NUMERO QUE PIDE EL ENCARGO ANTES DE ENCENDER.
    assert cambio["peor_caso_hoy"] > 0
    assert cambio["peor_caso_con_el_activo"] > cambio["peor_caso_hoy"], (
        "si contar el activo no abriera nada, no habría nada que "
        "decidir"
    )

    assert cambio["cuanto_mas"] == (
        cambio["peor_caso_con_el_activo"] - cambio["peor_caso_hoy"]
    )

    # El tope de una operación nunca pasa del techo de Biwenger
    # ni del bolsillo.
    assert cambio["peor_caso_con_el_activo"] <= min(
        cambio["bolsillo_de_fichar"], cambio["techo_de_biwenger"]
    ), (
        "la sombra no puede autorizar por encima del bolsillo ni "
        "del techo de Biwenger"
    )

    # La suma es suma, y dice lo que asume.
    suma = valor_de_fichar_con_el_activo(3_427_226, 12_200_424)

    assert suma["valor_con_el_activo"] == 15_627_650
    assert "revende" in suma["reason"], (
        "sumar las dos columnas solo vale si de verdad se revende, "
        "y eso tiene que ir escrito al lado del número"
    )

    # La lista vacía no publica un cero.
    assert que_cambiaria(
        [],
        bolsillo_de_fichar=1,
        bolsillo_de_especular=1,
        techo_de_biwenger=1,
    )["available"] is False

    print("  OK  la sombra no resucita a quien el once rechazó")


# ============================================================
# 6. APAGADO
# ============================================================


def test_esto_sigue_apagado():

    assert ENCENDIDO is False, (
        "la separación se construye apagada: solo el libro entra "
        "en producción"
    )

    assert esta_encendido() is False

    # Pero calcula.
    assert mapa_del_intent()["available"]

    assert que_cambiaria(
        CANDIDATOS,
        bolsillo_de_fichar=1,
        bolsillo_de_especular=1,
        techo_de_biwenger=1,
    )["available"]

    print("  OK  el mapa se publica, la sombra calcula y sigue apagada")


TESTS = [
    test_el_libro_no_duplica_el_reset,
    test_el_mapa_del_intent_no_miente,
    test_el_proposito_no_hereda_el_liston_de_otra_via,
    test_ninguna_via_se_queda_sin_frenos,
    test_la_sombra_no_convierte_en_fichaje_lo_que_la_via_del_once_rechaza,
    test_esto_sigue_apagado,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(f"EL PROPOSITO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
