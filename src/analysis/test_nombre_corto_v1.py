"""
Tres letras siguen siendo un nombre.

EL CASO (25/08/2026)

    "Ha salido Oso, es un jugadorazo y esta jugando de extremo,
     pero pepe dice esto"

    Y lo que decia era:

        Oso  DEF  3.050.000 EUR  sin dato  ...  0% SPECULATION
                                          SUPERA_PRESUPUESTO

    Con FutbolFantasy abierto al lado, teniendolo:

        Joaquín Oso · Sevilla · Rotación · Lateral izquierdo

    No era un agujero de FF. Era nuestro emparejador:

        FF        "Joaquín Oso"
        Biwenger  "Oso"
        parecido   0,4286

    `_contains_name` -la via que mete a Mbappe, a Lo Celso y a
    Mangala- descartaba de entrada cualquier token suelto de
    menos de cuatro letras. `Oso` tiene tres. Cerrada esa puerta
    solo quedaba el parecido de cadenas, y 0,4286 no llega al
    0,45 que pide la via del valor.

    Fuera por CATORCE MILESIMAS, con el valor Biwenger cuadrado
    al euro. O sea: sabiendo ya quien era.

LO QUE COSTO

    Del propio dashboard del 23/08:

        Oso · id 39360 · 16 puntos esta temporada -noveno de la
        liga- · 95 la pasada · +110.000 EUR de subida · libre en
        el Computer.

    Y la cadena entera detras: sin pronostico no hay valoracion
    como mejora del once, sin esa via la fila cae a
    especulacion, y con `intent` de especular se le aplica el
    bolsillo estrecho. De ahi el SUPERA_PRESUPUESTO, que no era
    el motivo sino el ultimo eslabon.

LA GUARDA ORIGINAL SIGUE EN PIE

    Se escribio contra los apellidos sueltos compartidos y hace
    bien: el "Andres" de Andres Castrin no puede emparejar con
    cualquier Andres de la pagina. Eso no cambia — la contencion
    se sigue probando SOLO con el nombre entero de Biwenger,
    nunca con los trozos.

    Lo que cambia es que un nombre entero de tres letras deja de
    descartarse de entrada, y se puntua mas bajo -0,60- para que
    cada via decida:

        via VALOR   pide 0,45  ->  entra, porque el euro ya ha
                                   dicho quien es
        via NOMBRE  pide 0,82  ->  no entra: tres letras no
                                   identifican solas
"""

from __future__ import annotations

from src.intelligence.futbolfantasy_provider import (
    ABSOLUTE_MIN_TOKEN_LEN,
    FULL_NAME_CONTAINMENT,
    MIN_TOKEN_LEN,
    SHORT_NAME_CONTAINMENT,
    _name_score,
    match_team,
)


SEVILLA = "Sevilla"


def biwenger(player_id, nombre, precio):
    return {
        "id": player_id,
        "name": nombre,
        "team": SEVILLA,
        "price": precio,
        "slug": None,
    }


def futbolfantasy(nombre, valor, probabilidad=30.0):
    return {
        "ff_name": nombre,
        "ff_slug": None,
        "ff_biwenger_value": valor,
        "probability": probabilidad,
    }


OSO = biwenger(39360, "Oso", 3_050_000)
FICHA_OSO = futbolfantasy("Joaquín Oso", 3_050_000)

# Companeros de la misma pagina, para que el emparejamiento
# tenga con quien confundirse.
SANGANTE = biwenger(2, "Sangante", 900_000)
CARMONA = biwenger(3, "Carmona", 1_400_000)


# ============================================================
# PRUEBAS
# ============================================================


def test_el_caso_oso():
    """
    Con el valor cuadrado al euro, Oso entra.
    """

    emparejados = match_team(
        [FICHA_OSO],
        [OSO, SANGANTE, CARMONA],
    )

    assert emparejados, (
        "Joaquín Oso sigue sin emparejar con Oso teniendo el "
        "valor Biwenger cuadrado al euro"
    )

    assert emparejados[0]["target"]["id"] == 39360
    assert emparejados[0]["method"] == "VALUE_AND_NAME"


def test_tres_letras_no_identifican_solas():
    """
    LA MITAD QUE NO SE TOCA.

    Sin el valor no hay segunda llave, y un nombre de tres
    letras no basta. Preferimos quedarnos sin pronostico a
    inventarnos una identidad.
    """

    sin_valor = futbolfantasy("Joaquín Oso", None)

    emparejados = match_team(
        [sin_valor],
        [OSO, SANGANTE, CARMONA],
    )

    assert not emparejados, (
        "un nombre de tres letras ha emparejado el solo, sin que "
        "el valor confirme nada"
    )


def test_el_valor_tiene_que_cuadrar_de_verdad():
    """
    Que la puerta la abra el euro, no el parecido.
    """

    otro_precio = futbolfantasy("Joaquín Oso", 999_000)

    assert not match_team([otro_precio], [OSO])


def test_una_palabra_no_es_un_trozo_de_otra():
    """
    "Cardoso" NO contiene "Oso".

    La comparacion es por palabras enteras. Si esto se relaja a
    subcadenas, medio LaLiga empareja con medio LaLiga.
    """

    cardoso = futbolfantasy("Bruno Cardoso", 3_050_000)

    assert _name_score(cardoso, OSO) < 0.45, (
        "un nombre esta emparejando por ser subcadena de otro"
    )

    assert not match_team([cardoso], [OSO])


def test_los_apellidos_sueltos_siguen_sin_valer():
    """
    LA GUARDA ORIGINAL.

    El "Andres" de Andres Castrin no puede emparejar con
    cualquier Andres de la pagina: la contencion solo se prueba
    con el nombre ENTERO de Biwenger.
    """

    castrin = biwenger(38072, "Andrés Castrín", 940_000)
    otro_andres = futbolfantasy("Andrés Palacios", 940_000)

    assert _name_score(otro_andres, castrin) < 0.82, (
        "un nombre de pila compartido esta identificando a un "
        "jugador"
    )


def test_los_nombres_largos_no_han_perdido_nada():
    """
    Mbappe, Lo Celso y compania siguen entrando por contencion y
    con la misma nota de siempre.
    """

    casos = [
        ("Kylian Mbappé", "Mbappé"),
        ("Giovani Lo Celso", "Lo Celso"),
        ("Orkun Mangala", "Mangala"),
        ("Carlos Aleñá", "Aleñá"),
    ]

    for nombre_ff, nombre_biwenger in casos:

        objetivo = biwenger(1, nombre_biwenger, 1_000_000)
        ficha = futbolfantasy(nombre_ff, 1_000_000)

        nota = _name_score(ficha, objetivo)

        assert nota >= FULL_NAME_CONTAINMENT, (
            f"{nombre_biwenger} ha bajado de nota: {nota}"
        )


def test_una_inicial_no_es_un_nombre():
    """
    El suelo absoluto. Por debajo de tres letras no hay nombre.
    """

    inicial = biwenger(4, "JJ", 1_000_000)
    ficha = futbolfantasy("Juan José Pérez", 1_000_000)

    assert _name_score(ficha, inicial) < 0.45


def test_los_umbrales_estan_donde_deben():
    """
    CANDADO NUMERICO.

    0,60 no es un numero cualquiera: esta a proposito por encima
    del 0,45 de la via del valor y por debajo del 0,82 de la via
    del nombre. Si alguien lo mueve, esta cambiando cual de las
    dos puertas abre un nombre corto.
    """

    assert ABSOLUTE_MIN_TOKEN_LEN < MIN_TOKEN_LEN

    assert 0.45 <= SHORT_NAME_CONTAINMENT < 0.82, (
        "un nombre corto ha dejado de pasar por el valor, o ha "
        "empezado a pasar el solo"
    )

    assert SHORT_NAME_CONTAINMENT < FULL_NAME_CONTAINMENT


def main():

    pruebas = [
        test_el_caso_oso,
        test_tres_letras_no_identifican_solas,
        test_el_valor_tiene_que_cuadrar_de_verdad,
        test_una_palabra_no_es_un_trozo_de_otra,
        test_los_apellidos_sueltos_siguen_sin_valer,
        test_los_nombres_largos_no_han_perdido_nada,
        test_una_inicial_no_es_un_nombre,
        test_los_umbrales_estan_donde_deben,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Nombres cortos: Oso entra, y nadie mas.")


if __name__ == "__main__":
    main()
