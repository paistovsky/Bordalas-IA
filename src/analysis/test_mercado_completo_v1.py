"""
El mercado se enseña entero, y si se recorta se dice.

EL CASO (21/08/2026)

    "Mira los jugadores del mercado y mira los que ve Pepe. No
     ve todos, ¿por qué?"

    Si los veia. La cabecera decia "20 VALORADOS · 18/20 CON
    PRONOSTICO" y la tabla enseñaba DOCE. Los otros ocho estaban
    descargados, valorados, puntuados y ordenados, y se tiraban
    en la ultima linea antes de la pantalla:

        mostradas = filas[:limit]      # limit = 12

    El motor no fallaba. Fallaba que el recorte era MUDO: una
    lista cortada sin avisar se lee como "esto es todo lo que
    hay". El dueño tuvo que abrir Biwenger y comparar a mano
    para descubrirlo.

    Decimo caso en cinco dias de la misma familia: el dato
    existe, se calcula bien y no llega a ninguna pantalla.

LO QUE SE PROTEGE

    1. Que el tope quepa el mercado real. El Computer saca
       veinte jugadores al dia; un tope de doce recorta siempre.

    2. Que el payload diga cuantos se valoraron, cuantos se
       enseñan y cuantos se caen. Sin esos tres numeros la
       pantalla no puede avisar aunque quiera.

    3. Que la pantalla avise de verdad cuando recorte.
"""

from __future__ import annotations

import inspect

from pathlib import Path

from src.analysis.acquisition_board import build_acquisition_board


# El mercado del Computer de un dia normal.
MERCADO_TIPICO = 20


def test_el_tope_cabe_el_mercado_real():
    """
    Con `limit=12` sobre veinte valorados se perdian ocho todos
    los dias. El tope tiene que ser un freno ante algo anomalo,
    no un recorte cotidiano.
    """

    limite = (
        inspect.signature(build_acquisition_board)
        .parameters["limit"]
        .default
    )

    assert limite >= MERCADO_TIPICO * 2, (
        f"el tope de la tabla ({limite}) recorta un mercado "
        f"normal de {MERCADO_TIPICO} jugadores"
    )


def test_el_payload_sabe_cuanto_esconde():
    """
    Sin `valued`, `shown` y `hidden` la pantalla no tiene con que
    avisar. Es la diferencia entre poder cantar el recorte y
    tener que adivinarlo.
    """

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    for clave in ('"valued"', '"shown"', '"hidden"'):
        assert clave in fuente, (
            f"el tablero ha dejado de publicar {clave}: el "
            f"recorte vuelve a ser invisible"
        )


def test_lo_ya_comprometido_nunca_se_recorta():
    """
    El recorte no puede esconder nuestro propio dinero. Una puja
    viva entra en la tabla aunque el orden la dejara fuera.
    """

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert 'if f.get("has_live_bid") and f["id"] not in vistos' in fuente, (
        "las pujas vivas han dejado de colarse por encima del "
        "recorte"
    )


def test_la_pantalla_canta_el_recorte():
    """
    De nada sirve publicar `hidden` si nadie lo pinta. Es
    exactamente el fallo que se esta arreglando, un piso mas
    arriba.
    """

    pagina = (
        Path(__file__).parent.parent.parent
        / "dashboard-v8"
        / "src"
        / "pages"
        / "MarketPage.jsx"
    )

    if not pagina.exists():
        # El repo puede venir sin el front en algunos entornos.
        return

    fuente = pagina.read_text(encoding="utf-8")

    assert "acquisition.hidden" in fuente, (
        "MarketPage ya no lee el recorte: volveria a ser mudo"
    )

    assert "se quedan fuera" in fuente


def main():

    pruebas = [
        test_el_tope_cabe_el_mercado_real,
        test_el_payload_sabe_cuanto_esconde,
        test_lo_ya_comprometido_nunca_se_recorta,
        test_la_pantalla_canta_el_recorte,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Mercado completo: todo en verde.")


if __name__ == "__main__":
    main()
