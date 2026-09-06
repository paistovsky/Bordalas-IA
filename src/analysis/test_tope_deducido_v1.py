"""
Un tope tiene que salir de una cuenta, no de anidar fracciones.

SINTOMA

    El 14/09 el dinero se quedo parado por un tope de 973.594 EUR
    por operacion. Y ese numero no es un limite de riesgo
    pensado:

        bolsillo de especular  2.433.987  x 40 %  =  973.594

    Un porcentaje de un bolsillo que ya es un porcentaje.

CAUSA

    Nadie lo dimensiono nunca. Salio de multiplicar dos reglas
    que se escribieron por separado y para otra cosa.

CONSECUENCIA

    Un tope que no sale de una cuenta no se puede discutir con
    numeros: solo se puede subir o bajar a ojo. Y subirlo a ojo
    es exactamente como se pierde medio patrimonio.

    Este tope sale de tres condiciones medidas, arranca donde
    esta hoy el limite de siempre —el primer dia no afloja nada—
    y sube solo con evidencia viva.

LO QUE ESTA GUARDIA NO DEJA PASAR

    Que el peldaño cero suba sin que nadie lo note; que una
    posicion pueda pasar del 10 % del patrimonio; que la escalera
    suba sin operaciones cerradas; y que un tope roto deje de
    degradarse al peldaño cero.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.hold_budget import (
    ESPECULAR,
    FICHAR,
    FIRST_RUNG,
    MAX_NON_XI_SHARE,
    RUNG_MEDIAN_FLOOR,
    RUNG_SAMPLE,
    WORST_MEASURED_LOSS,
    hold_cap,
    hold_pocket,
)


# Los numeros de la foto de produccion del 06/09.
SALDO = 1_725_383
PLANTILLA = 49_540_000


# ============================================================
# 1. EL PRIMER DIA NO SE AFLOJA NADA
# ============================================================


def test_el_peldaño_cero_es_el_limite_de_siempre() -> None:
    """
    973.594 EUR: el unico limite por operacion con el que este
    sistema ha operado. Si el primer peldaño fuese mayor,
    estariamos aflojando un intocable por la puerta de atras.
    """

    assert FIRST_RUNG == 973_594

    tope = hold_cap(SALDO, PLANTILLA)

    assert tope["rung"] == 0
    assert tope["cap"] == FIRST_RUNG, (
        f"sin ninguna operacion cerrada el tope es "
        f"{tope['cap']:,} y deberia ser el de siempre, "
        f"{FIRST_RUNG:,}"
    )


def test_max_single_speculation_percent_no_se_toca() -> None:
    """
    Este encargo se escribio precisamente para no tener que
    tocarlo. Si algun dia cambia, que salte aqui.
    """

    from src.analysis.speculation_engine import (
        MAX_SINGLE_SPECULATION_PERCENT,
    )

    assert MAX_SINGLE_SPECULATION_PERCENT == 0.40


# ============================================================
# 2. EL TECHO SALE DE DOS CONDICIONES MEDIDAS
# ============================================================


def test_el_techo_es_la_mas_estrecha_de_las_dos() -> None:
    tope = hold_cap(SALDO, PLANTILLA)

    assert tope["ceiling"] == min(
        tope["ceiling_by_worst_loss"],
        tope["ceiling_by_concentration"],
    )


def test_la_peor_perdida_medida_la_aguanta_la_caja() -> None:
    """
    La peor operacion de la celda buena del retrotest: -12,86 %.
    Poniendo el techo, esa perdida tiene que dejar saldo
    positivo.
    """

    assert WORST_MEASURED_LOSS == 0.1286

    tope = hold_cap(SALDO, PLANTILLA)

    perdida = tope["ceiling_by_worst_loss"] * WORST_MEASURED_LOSS

    assert perdida <= SALDO + 1, (
        f"la peor perdida sobre el techo son {perdida:,.0f} y el "
        f"saldo es {SALDO:,}"
    )


def test_ninguna_posicion_pasa_del_diez_por_ciento() -> None:
    """
    Medido sobre la liga el 15/09: la mayor posicion NO TITULAR
    de los tres que van por delante esta entre el 1,70 % y el
    9,48 %. El tope queda justo encima, como el de concentracion
    del 10/09.

    Y el denominador incluye la compra: comprar SUBE el
    patrimonio.
    """

    assert MAX_NON_XI_SHARE == 0.10

    tope = hold_cap(SALDO, PLANTILLA)

    maximo = tope["ceiling_by_concentration"]

    parte = maximo / (PLANTILLA + maximo)

    assert parte <= MAX_NON_XI_SHARE + 1e-6, (
        f"el techo por concentracion deja al jugador en el "
        f"{parte * 100:.2f} % del patrimonio"
    )


def test_sin_saldo_ni_plantilla_se_cae_al_peldaño_cero() -> None:
    tope = hold_cap(0, 0)

    assert tope["cap"] == FIRST_RUNG


# ============================================================
# 3. LA ESCALERA
# ============================================================


def test_no_se_sube_sin_operaciones_cerradas() -> None:
    """
    142 operaciones de una semana de agosto no son evidencia
    viva. La escalera sube con lo que nos pase a nosotros.
    """

    assert hold_cap(SALDO, PLANTILLA, closed_operations=0)["rung"] == 0
    assert (
        hold_cap(
            SALDO,
            PLANTILLA,
            closed_operations=RUNG_SAMPLE - 1,
            live_median=0.05,
        )["rung"]
        == 0
    )


def test_se_sube_con_doce_cerradas_que_lleguen_al_p25() -> None:
    """
    N = 12 porque es el corte que ya usa la casa para decidir
    cuando una medida pesa mas que su prior
    (`PREMIUM_SHRINK_SAMPLES`).

    El margen es el p25 del retrotest, +2,68 %: si la mitad de lo
    que nos pasa en vivo bate lo que batia un cuarto de lo
    medido, el retrotest aguanta.
    """

    assert RUNG_SAMPLE == 12
    assert RUNG_MEDIAN_FLOOR == 0.0268

    subido = hold_cap(
        SALDO,
        PLANTILLA,
        closed_operations=RUNG_SAMPLE,
        live_median=RUNG_MEDIAN_FLOOR,
    )

    assert subido["rung"] == 1
    assert subido["cap"] > FIRST_RUNG


def test_no_se_sube_si_lo_vivo_no_se_parece() -> None:
    quieto = hold_cap(
        SALDO,
        PLANTILLA,
        closed_operations=RUNG_SAMPLE * 3,
        live_median=RUNG_MEDIAN_FLOOR - 0.001,
    )

    assert quieto["rung"] == 0
    assert quieto["cap"] == FIRST_RUNG


def test_si_lo_vivo_pierde_dinero_se_baja_del_todo() -> None:
    caido = hold_cap(
        SALDO,
        PLANTILLA,
        closed_operations=RUNG_SAMPLE * 5,
        live_median=-0.01,
    )

    assert caido["rung"] == 0
    assert caido["cap"] == FIRST_RUNG


def test_la_escalera_nunca_pasa_del_techo() -> None:
    for cerradas in (0, 12, 24, 48, 120, 1200):

        tope = hold_cap(
            SALDO,
            PLANTILLA,
            closed_operations=cerradas,
            live_median=0.10,
        )

        assert tope["cap"] <= tope["ceiling"], (
            f"con {cerradas} operaciones el tope ({tope['cap']:,}) "
            f"pasa del techo ({tope['ceiling']:,})"
        )


def test_una_sola_posicion_abierta_a_la_vez() -> None:
    """
    Hasta que el libro de pujas tenga operaciones cerradas de
    verdad.
    """

    bloqueado = hold_cap(SALDO, PLANTILLA, open_positions=1)

    assert bloqueado["cap"] == 0
    assert bloqueado["blocked_by_open_position"] is True
    assert "una a la vez" in bloqueado["reason"]


# ============================================================
# 4. EL BOLSILLO
# ============================================================


def test_llenar_una_ficha_vacia_es_un_fichaje_de_balance() -> None:
    """
    No da nada a cambio: convierte caja en activo. El valor y el
    liston siguen siendo los de TENER.
    """

    bolsillo = hold_pocket(8)

    assert bolsillo["pocket"] == FICHAR
    assert "ficha" in bolsillo["reason"]
    assert "TENER" in bolsillo["reason"], (
        "no se dice que el liston sigue siendo el de la via"
    )


def test_rotar_es_cartera() -> None:
    assert hold_pocket(0)["pocket"] == ESPECULAR


def test_el_bolsillo_no_decide_el_tope() -> None:
    """
    LO QUE MAS IMPORTA DE TODO ESTE MODULO

        Mandar una apuesta de precio al bolsillo grande diluiria
        el limite del 40 % donde vive la leccion de Soler. Por
        eso el tope es PROPIO y no el del bolsillo: el bolsillo
        pone los fondos, el tope pone el riesgo.
    """

    fuente = Path(
        "src/analysis/acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert "hold_cap(" in fuente, (
        "el tablero coge el bolsillo de fichar sin aplicar el "
        "tope deducido"
    )

    # Y el tope tiene que morder despues del bolsillo.
    posicion_bolsillo = fuente.index("hold_pocket(")
    posicion_tope = fuente.index("hold_cap(")

    assert posicion_tope > posicion_bolsillo, (
        "el tope se calcula antes que el bolsillo: el bolsillo "
        "podria pisarlo"
    )


def test_el_tope_nunca_lanza() -> None:
    for entrada in (
        (None, None),
        ("no soy un saldo", "yo tampoco"),
        (-5_000_000, 49_540_000),
        (SALDO, 0),
    ):
        tope = hold_cap(*entrada)

        assert isinstance(tope, dict)
        assert tope["cap"] >= 0


TESTS = [
    test_el_peldaño_cero_es_el_limite_de_siempre,
    test_max_single_speculation_percent_no_se_toca,
    test_el_techo_es_la_mas_estrecha_de_las_dos,
    test_la_peor_perdida_medida_la_aguanta_la_caja,
    test_ninguna_posicion_pasa_del_diez_por_ciento,
    test_sin_saldo_ni_plantilla_se_cae_al_peldaño_cero,
    test_no_se_sube_sin_operaciones_cerradas,
    test_se_sube_con_doce_cerradas_que_lleguen_al_p25,
    test_no_se_sube_si_lo_vivo_no_se_parece,
    test_si_lo_vivo_pierde_dinero_se_baja_del_todo,
    test_la_escalera_nunca_pasa_del_techo,
    test_una_sola_posicion_abierta_a_la_vez,
    test_llenar_una_ficha_vacia_es_un_fichaje_de_balance,
    test_rotar_es_cartera,
    test_el_bolsillo_no_decide_el_tope,
    test_el_tope_nunca_lanza,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"TOPE DEDUCIDO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
