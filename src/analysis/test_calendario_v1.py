"""
El campo cuenta, y el proximo partido decide cuando, no si.

EL CASO (dueño, 18/08/2026)

    "Tenemos a un tio que vale 50 y en el mercado hay uno de 52.
    Pero el de 52 juega fuera y contra el Barsa. Pierde seguro.
    Hay que valorar si juegan en casa y contra un equipo grande o
    no, ¿no crees?"

LAS DOS MITADES DE LA RESPUESTA

    1. Tenia razon con el campo. Se comprobo sobre la jornada 2:
       la dificultad de FF mide al RIVAL y no donde se juega. El
       mismo partido sale con la misma dificultad para los dos
       equipos, y el Madrid FUERA en Espanyol saca un 2 mientras
       el Espanyol EN CASA saca un 4. `away` venia aparte en el
       dato y no lo miraba nadie.

    2. Pero a peso completo el partido tumbaba el cambio:

           sin campo:  52 − 50           = +2   se hace
           con campo:  52×0.90 − 50×1.10 = −8   se bloquea

       Ocho puntos de temporada decididos por un sabado. Es el
       mismo error de WEEKLY_ADJUSTMENT_WEIGHT, que estaba en 0,5
       y hubo que bajarlo a 0,15.

    La solucion es que el peso lo ponga el calendario: el proximo
    partido es UNO de los que quedan.
"""

from __future__ import annotations

from src.analysis.player_value_engine import (
    HOME_WEIGHT,
    fixture_factor,
    remaining_matchdays,
    season_fixture_factor,
    venue_factor,
    xi_upgrade_value,
)


FUERA_CONTRA_EL_BARSA = {
    "next_match": {"rival": "BAR", "difficulty": 5, "away": True},
    "probability": 80.0,
    "hierarchy": {"value": 40, "label": "Importante"},
}

EN_CASA_CONTRA_ELCHE = {
    "next_match": {"rival": "ELC", "difficulty": 1, "away": False},
    "probability": 80.0,
    "hierarchy": {"value": 40, "label": "Importante"},
}

MERCADO = {"rate_median": 22_314}


def test_el_campo_ya_no_se_tira():
    """
    Jugar en casa suma y jugar fuera resta. Antes daba igual.
    """

    casa, motivo_casa = venue_factor(EN_CASA_CONTRA_ELCHE)
    fuera, motivo_fuera = venue_factor(FUERA_CONTRA_EL_BARSA)

    assert casa == 1.0 + HOME_WEIGHT
    assert fuera == 1.0 - HOME_WEIGHT
    assert "casa" in motivo_casa
    assert "fuera" in motivo_fuera

    # Y el factor completo los multiplica: el rival manda mas que
    # el campo, pero los dos estan.
    dificil, texto = fixture_factor(FUERA_CONTRA_EL_BARSA)
    facil, _ = fixture_factor(EN_CASA_CONTRA_ELCHE)

    assert dificil < 1.0 < facil
    assert "BAR" in texto and "fuera" in texto

    # Sin saber donde se juega no se inventa un campo neutro.
    sin_campo = {
        "next_match": {"rival": "BAR", "difficulty": 5}
    }

    assert venue_factor(sin_campo) == (None, None)

    solo_rival, _ = fixture_factor(sin_campo)

    assert solo_rival is not None
    assert solo_rival > dificil, (
        "sin dato de campo se esta penalizando igual que jugando "
        "fuera"
    )

    # Y sin partido ninguno, nada.
    assert fixture_factor({}) == (None, None)
    assert fixture_factor(None) == (None, None)


def test_el_peso_lo_pone_el_calendario():
    """
    El mismo partido pesa 1/37 en agosto y entero en la ultima.
    """

    assert remaining_matchdays(2) == 37
    assert remaining_matchdays(38) == 1

    # Nunca cero: dividir por las jornadas que quedan no puede
    # explotar en la ultima.
    assert remaining_matchdays(99) == 1
    assert remaining_matchdays(None) >= 1
    assert remaining_matchdays("basura") >= 1

    anterior = None

    for jornada in (2, 10, 25, 35, 38):

        factor, motivo = season_fixture_factor(
            FUERA_CONTRA_EL_BARSA,
            jornada,
        )

        assert factor is not None
        assert f"de {remaining_matchdays(jornada)} jornadas" in motivo

        # Un partido malo penaliza mas cuanto menos queda.
        if anterior is not None:
            assert factor < anterior, (
                "el calendario no esta apretando segun avanza la "
                "temporada"
            )

        anterior = factor

    # En agosto casi no mueve; en la ultima jornada mueve entero.
    principio, _ = season_fixture_factor(FUERA_CONTRA_EL_BARSA, 2)
    final, _ = season_fixture_factor(FUERA_CONTRA_EL_BARSA, 38)

    assert principio > 0.99
    assert final == fixture_factor(FUERA_CONTRA_EL_BARSA)[0]

    # Sin jornada no se dilata por un numero inventado.
    assert season_fixture_factor(
        FUERA_CONTRA_EL_BARSA,
        None,
    ) == (None, None)


def test_el_caso_del_dueño():
    """
    50 en casa contra un flojo vs 52 fuera contra el Barsa.

    En agosto el cambio se hace: dos puntos durante 37 jornadas
    valen mas que un mal sabado. En mayo no se hace, porque ya no
    quedan 37 jornadas para amortizarlo.
    """

    def cambio(jornada):
        return xi_upgrade_value(
            candidate_points=52,
            replaced_points=50,
            points_market=MERCADO,
            candidate_starter=FUERA_CONTRA_EL_BARSA,
            replaced_starter=EN_CASA_CONTRA_ELCHE,
            matchday=jornada,
        )

    agosto = cambio(2)

    assert agosto.get("intent") == "XI_UPGRADE", (
        "en la jornada 2 un mal partido esta tumbando un cambio "
        "que dura toda la temporada"
    )

    mayo = cambio(37)

    assert mayo.get("decision") == "NO_MEJORA", (
        "al final de temporada el calendario tiene que mandar y "
        "no lo hace"
    )

    # Y que el motivo distinga "no mejora" de "no mejora ESTA
    # semana": no es lo mismo y el dueño tiene que poder verlo.
    assert "calendario" in str(mayo.get("reason"))
    assert "esperar" in str(mayo.get("reason"))


def test_sin_calendario_se_comporta_como_antes():
    """
    Quien no pase la jornada no cambia de comportamiento.

    Importa porque `xi_upgrade_value` lo llaman varios sitios y
    solo uno sabe en que jornada estamos.
    """

    sin_jornada = xi_upgrade_value(
        candidate_points=52,
        replaced_points=50,
        points_market=MERCADO,
        candidate_starter=FUERA_CONTRA_EL_BARSA,
        replaced_starter=EN_CASA_CONTRA_ELCHE,
    )

    assert sin_jornada.get("intent") == "XI_UPGRADE"
    assert sin_jornada.get("points_delta") == 2


def test_el_tablero_pasa_la_jornada():
    """
    Que el motor sepa la jornada no sirve si nadie se la da.
    """

    import inspect

    from src.analysis import acquisition_valuation

    fuente = inspect.getsource(
        acquisition_valuation.value_candidate
    )

    assert "matchday=" in fuente, (
        "el tablero de fichajes ha dejado de pasar la jornada: el "
        "calendario deja de contar sin que nadie se entere"
    )


def main():

    pruebas = [
        test_el_campo_ya_no_se_tira,
        test_el_peso_lo_pone_el_calendario,
        test_el_caso_del_dueño,
        test_sin_calendario_se_comporta_como_antes,
        test_el_tablero_pasa_la_jornada,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Calendario: todo en verde.")


if __name__ == "__main__":
    main()
