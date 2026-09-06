"""
Una puja que se puede enumerar con una calculadora no es una
puja: es un anuncio.

SINTOMA

    El dueño, el 13/09/2026:

        "Pollo se llevo a Natan por 7 euros. Eso es que sabe que
         Pepe puja a 0 o a 5 clavaos. Hay que randomizar eso."

    Nuestra sombra valoro a Natan en 3.010.000. Pollo pago
    3.010.007.

CAUSA

    `candidate_bids` genera los importes desde la curva de
    primas:

        {precio + 1} U {int(precio * factor) + 1 : factor} U {techo}

    Y esa curva se PUBLICA en `status.json`, en
    `acquisition.premium_model.curve`. El precio de mercado lo ve
    toda la liga. Con las dos cosas, el conjunto entero de
    nuestras pujas candidatas sale de una hoja de calculo.

CONSECUENCIA

    Perder cada subasta por unos euros contra quien calcule lo
    mismo que nosotros y se ponga encima.

    OJO CON LA MUESTRA: el libro de pujas tiene UNA puja. Con
    n=1 no se demuestra que nadie nos lea, y esta guardia no
    afirma que lo hagan. Comprueba el seguro, no la teoria.

    Lo que si comprueba, y es lo que de verdad importa, es que el
    seguro no rompa nada: ni el techo, ni el suelo, ni el tope
    por operacion, ni la deduplicacion de pujas -que depende de
    que el mismo objetivo de el mismo importe dos veces-.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.bid_jitter import (
    DEFAULT_SALT,
    JITTER_PERCENT,
    MAX_JITTER,
    MIN_JITTER,
    SALT_ENV,
    apply_bid_jitter,
    bid_jitter,
    jitter_ceiling,
)


MODULO = Path("src/analysis/bid_jitter.py")


# La curva publicada en `status.json` el 06/09/2026. Es la que
# cualquiera puede leer.
CURVA_PUBLICADA = (
    1.0,
    1.0052,
    1.0259,
    1.0411,
    1.0695,
    1.2027,
    1.2449,
)


FECHA = "2026-09-13"
JORNADA = 5


def _final(player_id, precio, limpio=None, techo=None, **extra) -> dict:
    return apply_bid_jitter(
        limpio if limpio is not None else precio + 1,
        precio,
        ceiling=techo if techo is not None else int(precio * 1.5),
        player_id=player_id,
        matchday=JORNADA,
        fecha=FECHA,
        **extra,
    )


# ============================================================
# 1. IMPREDECIBLE FUERA
# ============================================================


def test_dos_jugadores_al_mismo_precio_no_pujan_igual() -> None:
    """
    Si el desvio dependiese solo del precio, seguiria siendo
    enumerable: bastaria con probar los mismos importes.
    """

    desvios = {
        bid_jitter(pid, 3_000_000, JORNADA, FECHA)
        for pid in range(1, 40)
    }

    assert len(desvios) > 30, (
        f"39 jugadores al mismo precio producen solo "
        f"{len(desvios)} desvios distintos"
    )


def test_ningun_importe_cae_en_la_curva_publicada() -> None:
    """
    EL NUCLEO DE LA GUARDIA

        Sobre 200 objetivos simulados, ninguno puede coincidir
        con `int(precio * factor) + 1` para ningun factor de la
        curva publicada, que es justo el conjunto que cualquiera
        puede calcular.
    """

    coincidencias = []

    for pid in range(1, 201):

        precio = 150_000 + pid * 97_000

        # El importe limpio ES uno de los enumerables: se coge el
        # peor caso a proposito.
        limpio = int(precio * 1.0259) + 1

        salida = _final(pid, precio, limpio=limpio)

        enumerables = {
            int(precio * factor) + 1 for factor in CURVA_PUBLICADA
        }
        enumerables.add(precio + 1)

        if salida["bid"] in enumerables:
            coincidencias.append((pid, precio, salida["bid"]))

    assert not coincidencias, (
        f"{len(coincidencias)} de 200 importes siguen siendo "
        f"enumerables desde la curva publicada: "
        f"{coincidencias[:3]}"
    )


def test_casi_ninguno_acaba_en_ceros() -> None:
    """
    "que no acabe en 0 ni en 5 clavaos", hecho medida.
    """

    redondos = 0

    for pid in range(1, 201):

        precio = 150_000 + pid * 97_000

        salida = _final(pid, precio, limpio=precio + 1)

        if salida["bid"] % 1_000 == 0:
            redondos += 1

    assert redondos < 10, (
        f"{redondos} de 200 importes acaban en 000: el desvio no "
        f"esta deshaciendo los numeros clavados"
    )


def test_lo_clavado_se_deshace() -> None:
    """
    El caso concreto: un importe que cae exacto en 0000 o en
    5000 tiene que salir movido.
    """

    for limpio in (3_000_000, 3_005_000, 1_200_000, 4_995_000):

        salida = apply_bid_jitter(
            limpio,
            limpio - 10_000,
            ceiling=limpio * 2,
            player_id=777,
            matchday=JORNADA,
            fecha=FECHA,
        )

        assert salida["bid"] % 10_000 not in (0, 5_000), (
            f"{limpio} sigue saliendo clavado: {salida['bid']}"
        )


# ============================================================
# 2. REPRODUCIBLE DENTRO
# ============================================================


def test_el_mismo_objetivo_da_el_mismo_importe() -> None:
    """
    ESTO ES LO QUE MAS PUEDE ROMPER

        Si el ciclo se reintenta, o si el tablero y el ejecutor
        preguntan por separado, el importe tiene que ser el
        mismo. Dos importes distintos por el mismo jugador son
        dos pujas, que es lo que `test_bid_deduplication_v1`
        existe para impedir.
    """

    primero = _final(41271, 3_010_000)
    segundo = _final(41271, 3_010_000)
    tercero = _final(41271, 3_010_000)

    assert primero["bid"] == segundo["bid"] == tercero["bid"]


def test_cambia_de_un_dia_para_otro() -> None:
    """
    Y al dia siguiente es otro, para que ni siquiera valga
    observar lo que pujamos hoy.
    """

    hoy = apply_bid_jitter(
        3_010_000, 3_000_000, ceiling=4_000_000,
        player_id=41271, matchday=JORNADA, fecha="2026-09-13",
    )
    mañana = apply_bid_jitter(
        3_010_000, 3_000_000, ceiling=4_000_000,
        player_id=41271, matchday=JORNADA, fecha="2026-09-14",
    )

    assert hoy["bid"] != mañana["bid"]


def test_no_se_usa_random_sin_semilla() -> None:
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):

            nombres = ast.dump(nodo)

            assert "'random'" not in nombres, (
                "el desvio usa `random`: dejaria de ser "
                "reproducible dentro del ciclo"
            )


# ============================================================
# 3. LOS LIMITES DUROS
# ============================================================


def test_nunca_por_encima_del_techo() -> None:
    for pid in range(1, 121):

        precio = 200_000 + pid * 61_000
        techo = precio + 8_000

        salida = _final(pid, precio, limpio=precio + 1, techo=techo)

        assert salida["bid"] <= techo, (
            f"{salida['bid']} supera el techo {techo}"
        )


def test_nunca_por_debajo_del_precio_mas_uno() -> None:
    for pid in range(1, 121):

        precio = 200_000 + pid * 61_000

        salida = _final(pid, precio, limpio=precio + 1)

        assert salida["bid"] >= precio + 1


def test_el_tope_por_operacion_manda() -> None:
    """
    El tope del bolsillo es una barandilla pagada. El desvio no
    puede saltarsela ni por un euro.
    """

    salida = apply_bid_jitter(
        970_000,
        900_000,
        ceiling=2_000_000,
        player_id=99,
        matchday=JORNADA,
        fecha=FECHA,
        single_operation_limit=973_594,
    )

    assert salida["bid"] <= 973_594


def test_el_tope_del_desvio_es_el_medio_por_ciento() -> None:
    assert JITTER_PERCENT == 0.005
    assert jitter_ceiling(3_000_000) == 15_000
    assert jitter_ceiling(100) == MIN_JITTER
    assert jitter_ceiling(1_000_000_000) == MAX_JITTER


# ============================================================
# 4. LO QUE CUESTA EL SEGURO
# ============================================================


def test_la_perdida_de_ev_se_queda_por_debajo_del_medio_por_ciento() -> None:
    """
    El desvio sube el importe, asi que come valor esperado. El
    dueño quiere saber cuanto: tiene que quedarse por debajo del
    0,5 % de la operacion.

    Se mide con la probabilidad de ganar de verdad, no con una
    aproximacion.
    """

    from src.analysis.rival_bid_model import (
        DEFAULT_PREMIUM_CURVE,
        credible_rivals,
        win_probability,
    )

    modelo = {
        "premium": {
            "curve": list(DEFAULT_PREMIUM_CURVE),
            "calibrated": False,
        },
        "managers": [],
    }

    peor = 0.0

    for pid in range(1, 121):

        precio = 200_000 + pid * 61_000
        valor = int(precio * 1.15)

        limpio = int(precio * 1.0259) + 1

        salida = _final(pid, precio, limpio=limpio, techo=valor)

        rivales = credible_rivals(modelo, precio)

        ev_limpio = win_probability(
            limpio, precio, modelo, rivales
        ) * (valor - limpio)

        ev_final = win_probability(
            salida["bid"], precio, modelo, rivales
        ) * (valor - salida["bid"])

        perdida = (ev_limpio - ev_final) / max(salida["bid"], 1)

        peor = max(peor, perdida)

    assert peor < 0.005, (
        f"el desvio se come hasta un {peor * 100:.3f} % del "
        f"valor esperado, y el limite es 0,5 %"
    )


def test_el_coste_viaja_para_poder_mirarlo() -> None:
    """
    "Quiero poder mirar la pantalla y ver cuanto nos esta
    costando el seguro. Si en un mes ha costado mas de lo que ha
    ganado, se apaga."
    """

    salida = _final(41271, 3_010_000)

    for clave in ("bid", "clean_bid", "jitter", "jitter_ceiling"):
        assert clave in salida, f"falta `{clave}` en la salida"

    assert salida["jitter"] == salida["bid"] - salida["clean_bid"]


def test_el_tablero_publica_las_dos_cifras() -> None:
    """
    Y que llegue al tablero, no solo a la funcion.
    """

    fuente = Path(
        "src/analysis/acquisition_board.py"
    ).read_text(encoding="utf-8")

    for campo in ("bid_clean", "bid_jitter"):
        assert f'fila["{campo}"]' in fuente, (
            f"el tablero no publica `{campo}`"
        )

    assert "apply_bid_jitter" in fuente, (
        "el tablero enseña un importe que no es el que se puja"
    )


def test_el_ejecutor_y_el_tablero_usan_la_misma_semilla() -> None:
    """
    Si la pantalla sembrase con una jornada y el ejecutor con
    otra, el importe visto y el pujado serian distintos — y la
    pantalla estaria mintiendo sobre lo que va a pasar.
    """

    ejecutor = Path(
        "src/actions/autopilot_executor.py"
    ).read_text(encoding="utf-8")

    tablero = Path(
        "src/analysis/acquisition_board.py"
    ).read_text(encoding="utf-8")

    for fuente, nombre in ((ejecutor, "el ejecutor"), (tablero, "el tablero")):
        assert "apply_bid_jitter" in fuente, (
            f"{nombre} no aplica el desvio"
        )
        assert "target_matchday" in fuente, (
            f"{nombre} no siembra con la jornada del calendario"
        )


# ============================================================
# 5. LA SAL
# ============================================================


def test_sin_sal_en_el_entorno_sigue_funcionando() -> None:
    """
    Degradar, nunca romper.
    """

    import os

    anterior = os.environ.pop(SALT_ENV, None)

    try:
        salida = _final(41271, 3_010_000)
        assert salida["bid"] > 0
        assert salida["salt_from_env"] is False

    finally:
        if anterior is not None:
            os.environ[SALT_ENV] = anterior


def test_la_sal_del_entorno_cambia_el_importe() -> None:
    """
    Si no cambiase, el secret de GitHub no serviria de nada.
    """

    import os

    anterior = os.environ.get(SALT_ENV)

    try:
        os.environ[SALT_ENV] = "una-sal-de-verdad"
        con_sal = _final(41271, 3_010_000)

        os.environ[SALT_ENV] = "otra-sal-distinta"
        con_otra = _final(41271, 3_010_000)

        assert con_sal["bid"] != con_otra["bid"]
        assert con_sal["salt_from_env"] is True

    finally:
        os.environ.pop(SALT_ENV, None)

        if anterior is not None:
            os.environ[SALT_ENV] = anterior


def test_el_docstring_dice_que_la_sal_del_codigo_no_protege() -> None:
    """
    Una sal en el repositorio es una sal publicada. Tiene que
    estar escrito donde lo vea quien la lea.
    """

    fuente = MODULO.read_text(encoding="utf-8")

    assert DEFAULT_SALT in fuente
    assert "secrets de GitHub" in fuente, (
        "no se dice donde tiene que vivir la sal de verdad"
    )
    assert "no protege" in fuente.lower(), (
        "no se dice que una sal en el codigo no protege"
    )


# ============================================================
# 6. LA MATEMATICA NO SE TOCA
# ============================================================


def test_optimal_bid_sigue_intacto() -> None:
    """
    El desvio es la ultima capa. Si algun dia se cuela dentro del
    motor, el EV, el techo y la leccion de Soler dejarian de
    valer lo que dicen valer.
    """

    fuente = Path(
        "src/analysis/rival_bid_model.py"
    ).read_text(encoding="utf-8")

    assert "bid_jitter" not in fuente, (
        "el desvio se ha metido dentro del motor de pujas: tiene "
        "que ser la ultima capa, en la ruta del ejecutor"
    )


TESTS = [
    test_dos_jugadores_al_mismo_precio_no_pujan_igual,
    test_ningun_importe_cae_en_la_curva_publicada,
    test_casi_ninguno_acaba_en_ceros,
    test_lo_clavado_se_deshace,
    test_el_mismo_objetivo_da_el_mismo_importe,
    test_cambia_de_un_dia_para_otro,
    test_no_se_usa_random_sin_semilla,
    test_nunca_por_encima_del_techo,
    test_nunca_por_debajo_del_precio_mas_uno,
    test_el_tope_por_operacion_manda,
    test_el_tope_del_desvio_es_el_medio_por_ciento,
    test_la_perdida_de_ev_se_queda_por_debajo_del_medio_por_ciento,
    test_el_coste_viaja_para_poder_mirarlo,
    test_el_tablero_publica_las_dos_cifras,
    test_el_ejecutor_y_el_tablero_usan_la_misma_semilla,
    test_sin_sal_en_el_entorno_sigue_funcionando,
    test_la_sal_del_entorno_cambia_el_importe,
    test_el_docstring_dice_que_la_sal_del_codigo_no_protege,
    test_optimal_bid_sigue_intacto,
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
    print(f"PUJA IMPREDECIBLE V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
