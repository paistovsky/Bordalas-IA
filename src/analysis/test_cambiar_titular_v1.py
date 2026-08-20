"""
Vender a un titular para fichar a uno mejor.

EL CASO (19/08/2026)

    El dueño lo llevaba pidiendo desde el principio: "debe vender
    jugadores, siempre para mejorar el XI o ganar pasta". Y Pepe
    solo sabia hacer la segunda mitad.

    El motivo no era una regla que lo prohibiera. Era que en
    `build_valuation_context` solo se guardaba el PEOR de cada
    posicion, y ese era el unico sustituido que
    `xi_upgrade_value` llegaba a valorar nunca. A un titular
    mediocre no lo descartaba nadie: no se le preguntaba.

    Al abrirlo, sobre el mercado real, lo primero que aparecio
    fue Budimir por Jutgla, +74 puntos. Jutgla es exactamente el
    jugador que el dueño habia señalado a mano semanas antes:
    "aqui cuidado con Jutgla, quiero un delantero mejor o no se
    vende".

POR QUE HAY QUE APRETAR AL ABRIRLO

    Cambiar a un suplente es barato de deshacer. Cambiar a un
    titular no:

        - se paga con una venta que puede tardar dias
        - por medio se juegan jornadas
        - y el que sale ya no vuelve

    De ahi los tres frenos, que se prueban aqui uno por uno.
"""

from __future__ import annotations

from src.analysis.player_value_engine import (
    STARTER_SWAP_MARGIN,
    STARTER_SWAP_MIN_DELTA,
    xi_upgrade_value,
)


MERCADO = {"rate_median": 22_000}


def senal(valor, etiqueta, probabilidad):
    return {
        "hierarchy_value": valor,
        "hierarchy_label": etiqueta,
        "probability": probabilidad,
    }


DIOS = senal(60, "Dios", 85.0)
OTRO_DIOS = senal(60, "Dios", 85.0)
CLAVE = senal(50, "Clave", 80.0)
IMPORTANTE = senal(40, "Importante", 80.0)
ROTACION = senal(30, "Rotación", 55.0)


def test_a_un_dios_no_se_le_toca():
    """
    "Yamal no se toca, a no ser que haya otro DIOS con mas
    puntos."

    El veto por escalones no cubria esto: de Dios a Clave hay UN
    escalon, y el veto salta a los dos. Asi que un Clave con
    muchos puntos historicos podia sacar a Yamal del once.
    """

    intento = xi_upgrade_value(
        candidate_points=200,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=CLAVE,
        replaced_starter=DIOS,
        replaced_in_lineup=True,
    )

    assert intento["decision"] == "NO_SE_TOCA_UN_DIOS", (
        "se esta proponiendo sacar a un Dios del once por alguien "
        "que no lo es"
    )

    # Otro Dios con MENOS puntos tampoco.
    igual = xi_upgrade_value(
        candidate_points=90,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=OTRO_DIOS,
        replaced_starter=DIOS,
        replaced_in_lineup=True,
    )

    assert igual["decision"] == "NO_SE_TOCA_UN_DIOS"

    # Otro Dios con mas puntos si: esa es la unica puerta.
    mejor = xi_upgrade_value(
        candidate_points=180,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=OTRO_DIOS,
        replaced_starter=DIOS,
        replaced_in_lineup=True,
    )

    assert mejor.get("intent") == "XI_UPGRADE", (
        "un Dios claramente mejor tampoco entra: la regla se ha "
        "pasado de frenada"
    )


def test_una_mejora_pequeña_no_toca_el_once():
    """
    Un cambio que gana por poco no compensa el riesgo.

    Con el margen normal del 10 %, +3 puntos bastaban. Sacar a un
    titular por tres puntos de temporada, pagando con una venta
    que tarda dias, es perder por el camino lo que se gana en la
    hoja.
    """

    pequeño = xi_upgrade_value(
        candidate_points=103,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=IMPORTANTE,
        replaced_starter=IMPORTANTE,
        replaced_in_lineup=True,
    )

    assert pequeño["decision"] == "MEJORA_INSUFICIENTE"
    assert str(STARTER_SWAP_MIN_DELTA) in pequeño["reason"]

    # El mismo cambio sobre un SUPLENTE si se hace: ahi deshacerlo
    # es gratis.
    en_el_banquillo = xi_upgrade_value(
        candidate_points=103,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=IMPORTANTE,
        replaced_starter=IMPORTANTE,
        replaced_in_lineup=False,
    )

    assert en_el_banquillo.get("intent") == "XI_UPGRADE", (
        "la regla del titular se esta aplicando tambien a los "
        "suplentes: Pepe deja de mejorar el banquillo"
    )


def test_el_que_entra_no_puede_jugar_menos():
    """
    Puntos en la hoja contra minutos en el campo.

    Es el error de Castrin otra vez, un piso mas arriba: el que
    entra suma mas puntos de temporada y sale menos veces. Sobre
    un suplente da igual; sobre un titular, cambia el once a peor.
    """

    menos_minutos = xi_upgrade_value(
        candidate_points=150,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=senal(40, "Importante", 55.0),
        replaced_starter=senal(40, "Importante", 85.0),
        replaced_in_lineup=True,
    )

    assert menos_minutos["decision"] == "PIERDE_TITULARIDAD"

    # Con la misma titularidad, adelante.
    igual_de_seguro = xi_upgrade_value(
        candidate_points=150,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=senal(40, "Importante", 85.0),
        replaced_starter=senal(40, "Importante", 85.0),
        replaced_in_lineup=True,
    )

    assert igual_de_seguro.get("intent") == "XI_UPGRADE"


def test_el_margen_del_titular_no_se_puede_relajar():
    """
    Pedir menos margen desde fuera no vale.

    `margin` es un parametro, asi que alguien podria pasar 0.05 y
    saltarse el freno sin enterarse. Se coge el mayor de los dos.
    """

    flojo = xi_upgrade_value(
        candidate_points=150,
        replaced_points=100,
        points_market=MERCADO,
        margin=0.01,
        candidate_starter=IMPORTANTE,
        replaced_starter=IMPORTANTE,
        replaced_in_lineup=True,
    )

    exigente = xi_upgrade_value(
        candidate_points=150,
        replaced_points=100,
        points_market=MERCADO,
        margin=STARTER_SWAP_MARGIN,
        candidate_starter=IMPORTANTE,
        replaced_starter=IMPORTANTE,
        replaced_in_lineup=True,
    )

    assert flojo["value"] == exigente["value"], (
        "se puede relajar el margen de un cambio de titular desde "
        "fuera"
    )


def test_el_cambio_deja_escrito_lo_que_promete():
    """
    Sin esto, dentro de un mes la conversacion es de opiniones.

    Un cambio se propone con un numero de puntos en la mano. Si
    ese numero no queda guardado, no hay forma de mirar despues
    si aquello pago.
    """

    cambio = xi_upgrade_value(
        candidate_points=174,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=IMPORTANTE,
        replaced_starter=IMPORTANTE,
        replaced_in_lineup=True,
    )

    assert cambio["promised_points"] == cambio["points_delta"]
    assert cambio["replaces_starter"] is True
    assert cambio["cost_per_point"] > 0

    # Y de un suplente se dice que lo es, no se calla.
    suplente = xi_upgrade_value(
        candidate_points=174,
        replaced_points=100,
        points_market=MERCADO,
        candidate_starter=IMPORTANTE,
        replaced_starter=IMPORTANTE,
        replaced_in_lineup=False,
    )

    assert suplente["replaces_starter"] is False


def test_se_pregunta_por_toda_la_plantilla():
    """
    El techo no era una regla: era a quien se le preguntaba.

    Estructural, porque el fallo no estaba en ninguna cuenta.
    `build_valuation_context` guardaba solo el peor de cada
    posicion y `value_candidate` solo miraba ese.
    """

    import inspect

    from src.analysis import acquisition_valuation

    contexto = inspect.getsource(
        acquisition_valuation.build_valuation_context
    )

    assert "squad_by_position" in contexto, (
        "el contexto ha vuelto a guardar solo al peor de cada "
        "posicion: los titulares dejan de ser sustituibles"
    )

    assert "in_lineup" in contexto, (
        "el contexto ya no sabe quien es titular, asi que los "
        "cambios sobre el once se valoraran con las reglas "
        "blandas del suplente"
    )

    valorar = inspect.getsource(
        acquisition_valuation.value_candidate
    )

    assert "squad_by_position" in valorar
    assert "replaced_in_lineup=" in valorar, (
        "el tablero ha dejado de decir si el sustituido juega"
    )


def test_no_se_cuenta_dinero_que_no_ha_entrado():
    """
    Comprar es instantaneo; vender tarda dias.

    `recovered_value` sube lo que estariamos dispuestos a pagar
    contando con lo que entra al vender al sustituido. Para un
    suplente vale. Para un titular no: el dueño lo dijo tal cual,
    "compra primero, venta despues", y un cambio que solo sale
    rentable contando dinero que aun no ha llegado no es un buen
    cambio, es una apuesta a dos manos.
    """

    import inspect

    from src.analysis import acquisition_valuation

    fuente = inspect.getsource(
        acquisition_valuation.value_candidate
    )

    assert "and not titular" in fuente, (
        "un cambio de titular vuelve a valorarse contando con el "
        "dinero de una venta que todavia no ha pasado"
    )


def test_mejorar_el_once_es_quitarle_el_sitio_a_alguien_del_once():
    """
    Los catorce defensas.

    EL CASO (20/08/2026)

        El dueño tuvo que intervenir a mano: "no se que le ha
        dado con los defensas, ficha muchos".

        El sustituido se elegia entre TODA la plantilla de la
        posicion, y con nueve defensas el que mas diferencia
        daba era siempre el peor, que es un suplente. De su
        propio tablero:

            Lucas Noubi   sustituye a Yeray          +109 pts
            Alvaro Nuñez  sustituye a Yusi Enriquez   +15 pts

        Ninguno de los dos habria cambiado un solo nombre del
        once del sabado. Y se realimentaba: cada compra hacia la
        posicion mas profunda y el peor seguia siendo malo.

    LA REGLA

        Un fichaje mejora el once si le quita el sitio a alguien
        DEL once. El sustituido es el peor TITULAR de esa
        posicion. Si el candidato no llega a ese, es fondo de
        armario y vale su reventa, no puntos.
    """

    from src.analysis.acquisition_valuation import value_candidate

    # Cuatro defensas: dos titulares decentes y dos suplentes
    # malos. El sesgo antiguo elegia a uno de los malos.
    contexto = {
        "points_market": {"rate_median": 22_000},
        "team_strength": {},
        "weakest_by_position": {},
        "starter": {},
        "velocity": {},
        "squad_by_position": {
            2: [
                {
                    "id": 1, "name": "Titular bueno",
                    "price": 3_000_000, "points": 150,
                    "in_lineup": True,
                    "starter": {
                        "hierarchy_value": 40,
                        "hierarchy_label": "Importante",
                        "probability": 80.0,
                    },
                },
                {
                    "id": 2, "name": "Titular flojo",
                    "price": 2_000_000, "points": 120,
                    "in_lineup": True,
                    "starter": {
                        "hierarchy_value": 40,
                        "hierarchy_label": "Importante",
                        "probability": 80.0,
                    },
                },
                {
                    "id": 3, "name": "Suplente malo",
                    "price": 500_000, "points": 20,
                    "in_lineup": False,
                    "starter": {
                        "hierarchy_value": 20,
                        "hierarchy_label": "Reserva",
                        "probability": 15.0,
                    },
                },
            ]
        },
    }

    # Un defensa mediocre: mejor que el suplente malo, peor que
    # cualquier titular. Antes entraba por la puerta de atras.
    mediocre = {
        "id": 99,
        "name": "Defensa del monton",
        "position": 2,
        "price": 1_000_000,
        "pointsLastSeason": 60,
    }

    resultado = value_candidate(mediocre, contexto)

    como_xi = resultado.get("as_xi") or {}

    assert como_xi.get("intent") != "XI_UPGRADE", (
        "un jugador que no entra en el once se sigue valorando "
        "como mejora del once: vuelve el bucle de los defensas"
    )

    sustituido = (como_xi.get("replaces") or {}).get("name")

    assert sustituido == "Titular flojo", (
        f"se compara contra {sustituido!r} en vez de contra el "
        f"peor titular: si es un suplente, la mejora es ficticia"
    )


def main():

    pruebas = [
        test_a_un_dios_no_se_le_toca,
        test_una_mejora_pequeña_no_toca_el_once,
        test_el_que_entra_no_puede_jugar_menos,
        test_el_margen_del_titular_no_se_puede_relajar,
        test_el_cambio_deja_escrito_lo_que_promete,
        test_se_pregunta_por_toda_la_plantilla,
        test_no_se_cuenta_dinero_que_no_ha_entrado,
        test_mejorar_el_once_es_quitarle_el_sitio_a_alguien_del_once,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Cambiar a un titular: todo en verde.")


if __name__ == "__main__":
    main()
