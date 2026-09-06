"""
QUIEN ES BUENO, LA PORTERIA, Y LO QUE SUSTITUYE A LOS INTOCABLES.

TRES COSAS EN UN FICHERO PORQUE SON LA MISMA NOCHE

    1. La calidad medida (regla 6). La vara explica el 20 % de la
       varianza porque su mitad de "calidad" es una escalera
       decretada a partir de una etiqueta.

    2. La porteria (regla 3). Tenemos UN portero y ninguna regla
       que lo impida.

    3. La prueba que sustituye a la lista de intocables, derogada
       por el dueño el 21/09.

# ============================================================
# LO QUE ENCERRABA `test_intocables_v1`, Y QUE SE QUEDA
# ============================================================

    Esa guardia tenia seis pruebas y solo DOS eran la lista:

        - el veto por escalon (Dios y Clave), que es la lista, y
        - el orden del veto contra la puntuacion, que la sostenia.

    Las otras cuatro encerraban incidentes de verdad, y por eso
    se mudan aqui en vez de irse con la lista:

    EL ACCIDENTE DEL 12/09/2026, que es el importante:

        La regla del portero miraba solo `in_lineup`. El roster
        del dashboard trae ese dato como `is_starter`. Con la
        plantilla de pantalla, Dituro -unico portero, titular- NO
        salia como intocable, y lo unico que impedia venderlo era
        el guardarrail posicional.

        Es palabra por palabra el accidente contra el que avisaba
        el propio modulo: "Yamal esta a salvo por accidente
        porque hay exactamente dos delanteros; el dia que entre
        un tercero, esa proteccion desaparece sola y nadie se
        entera".

        Eso no es cariño por un jugador: es el mismo dato con dos
        nombres. Se queda.

    Y LAS OTRAS DOS:

        - sin escalon conocido no se propone una venta, porque
          vender a ciegas no se deshace: te quedas sin el jugador
          y se lo lleva otro;
        - los vetados se publican, para que un veto no sea una
          desaparicion silenciosa.

    Guardias con fixture. Ni una lectura de `data/`.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.calidad_medida import (
    K_PARTIDOS,
    calidad,
    comparar_varas,
    partidos_jugados,
)
from src.analysis.porteria import (
    MINIMO_PORTEROS,
    estado_de_la_porteria,
)
from src.analysis.sale_intent import (
    GOALKEEPER_POSITION,
    untouchable_reason,
)
from src.analysis.soltar_un_grande import (
    MARGEN_NETO,
    es_grande,
    evaluar_venta,
)


# ============================================================
# FIXTURES
# ============================================================


def _plantilla() -> list:
    """
    Catorce fichas con una estrella dentro, como la de verdad:
    un portero, y la estrella pesando mas del 25 %.
    """

    plantilla = [{
        "id": 1,
        "name": "Portero",
        "position": 1,
        "price": 2_650_000,
        "points": 2,
        "is_starter": True,
        "hierarchy_value": 40,
    }, {
        "id": 2,
        "name": "Estrella",
        "position": 4,
        "price": 21_210_000,
        "points": 28,
        "is_starter": True,
        "hierarchy_value": 60,
        "starter_probability": 100.0,
    }]

    puntos = [21, 16, 12, 11, 11, 10, 9, 8, 6, 5, 0]

    for i, p in enumerate(puntos):
        plantilla.append({
            "id": 10 + i,
            "name": f"Jugador {i}",
            "position": 2 if i % 2 else 3,
            "price": 2_000_000,
            "points": p,
            # Los tres ultimos, al banquillo.
            "is_starter": i < len(puntos) - 3,
            "hierarchy_value": 40,
            "starter_probability": 80.0,
        })

    return plantilla


def _ficha(points, jugados, pasada, escalon=40, prob=80.0) -> dict:
    return {
        "points": points,
        "playedHome": jugados,
        "playedAway": 0,
        "pointsLastSeason": pasada,
        "hierarchy_value": escalon,
        "starter_probability": prob,
    }


# ============================================================
# 1. LA CALIDAD, MEDIDA
# ============================================================


def test_los_puntos_son_por_partido_no_por_jornada() -> None:
    """
    EL ENCARGO, LITERAL

        "Un suplente que hace 6 en veinte minutos no es malo: es
         uno que juega poco, y de eso se encarga la otra mitad de
         la formula. Mezclarlas es contarlo dos veces."
    """

    suplente = _ficha(points=6, jugados=1, pasada=0)
    titular = _ficha(points=6, jugados=3, pasada=0)

    assert partidos_jugados(suplente) == 1
    assert partidos_jugados(titular) == 3

    bueno = calidad(suplente)
    flojo = calidad(titular)

    assert bueno["points_per_match"] > flojo["points_per_match"], (
        "los puntos se estan dividiendo por jornadas y no por "
        "partidos jugados"
    )


def test_la_temporada_pasada_pesa_mas_cuando_hay_poca_muestra() -> None:
    """
    A un partido, un doblete no convierte a nadie en Dios.
    """

    uno = calidad(_ficha(points=20, jugados=1, pasada=38))
    muchos = calidad(_ficha(points=20, jugados=10, pasada=38))

    assert uno["weight_this"] < muchos["weight_this"]

    # Con un partido, la pasada manda: la nota queda cerca de 1,0
    # y no cerca de 20.
    assert uno["points_per_match"] < 5.0, (
        f"con un solo partido la nota es "
        f"{uno['points_per_match']}: la muestra corta no se esta "
        f"encogiendo"
    )

    # Y a los K partidos, las dos mitades pesan igual.
    justo = calidad(_ficha(points=10, jugados=K_PARTIDOS, pasada=38))

    assert abs(justo["weight_this"] - 0.5) < 1e-9


def test_sin_partidos_manda_la_etiqueta_y_se_dice_cual() -> None:
    """
    "La etiqueta no se tira: se degrada a suplente. Y la ficha
     dice cual de las dos la esta valorando. Nunca las dos a la
     vez."
    """

    recien = calidad(_ficha(points=0, jugados=0, pasada=0))

    assert recien["available"] is True
    assert recien["source"] == "ETIQUETA"
    assert recien["points_per_match"] is None
    assert recien["hierarchy_quality"] is not None

    jugado = calidad(_ficha(points=9, jugados=3, pasada=38))

    assert jugado["source"] == "MEDIDA"
    assert jugado["points_per_match"] is not None


def test_sin_partidos_y_sin_escalon_no_se_inventa_nada() -> None:
    ciego = calidad(_ficha(points=0, jugados=0, pasada=0, escalon=0))

    assert ciego["available"] is False
    assert ciego["reason"]


def test_la_mejora_se_mide_sin_circularidad() -> None:
    """
    LA TRAMPA QUE ESTA GUARDIA IMPIDE (21/09/2026)

        La calidad mezclada usa los puntos de ESTA temporada, y
        la varianza se mide contra... los puntos de esta
        temporada. Salia 61,9 % y no valia nada: el mismo dato en
        los dos lados de la cuenta.

        La cifra que decide es la que NO se solapa -solo
        temporada pasada-, y con ella la mejora era de 19,1 % a
        23,5 %. Cuatro puntos, no cuarenta.

    Si algun dia `improves` vuelve a decidirse con la cifra
    circular, esto se pone rojo.
    """

    fichas = []

    # Cien fichas donde la temporada pasada NO predice nada y
    # esta temporada predice perfecto. La circular saldria
    # altisima; la limpia, plana.
    for i in range(100):
        fichas.append(
            _ficha(
                points=i % 20,
                jugados=2,
                pasada=38,          # todos iguales: no informa
                prob=80.0,
            )
        )

    salida = comparar_varas(fichas, 3)

    assert salida["available"]

    assert "r_new_in_sample" in salida, (
        "la cifra circular ha dejado de publicarse: entonces "
        "nadie puede ver que lo es"
    )

    assert abs(salida["r_new"]) <= abs(
        salida["r_new_in_sample"]
    ) + 1e-9, (
        "la cifra limpia no puede salir mejor que la circular en "
        "este fixture: algo se ha cruzado"
    )

    # Con la pasada plana, la limpia no puede mejorar nada.
    assert salida["improves"] is False, (
        "`improves` se esta decidiendo con la cifra circular"
    )


def test_la_etiqueta_sobrevive_al_encendido() -> None:
    """
    ESTA PRUEBA CAMBIO DE SIGNO EL 22/09/2026

        Se llamaba `test_la_calidad_medida_no_esta_encendida` y
        exigia que el motor NO la usara: el 21/09 estaba medida
        pero sin encender, y encenderla era otra decision.

        El dueño la enciende el 22/09 con la medicion delante
        -19,1 % a 23,5 %, sin circularidad-. Asi que la prueba se
        actualiza a proposito, y no se silencia.

    Lo que sigue siendo cierto, y es lo que ahora vigila: **la
    etiqueta no se tira, se degrada a suplente**. Donde no hay
    partidos jugados manda la jerarquia, exactamente como antes.
    Si eso se perdiera, un recien llegado valdria cero y el motor
    no lo alinearia nunca.
    """

    from src.analysis.calidad_medida import calidad_para_la_vara
    from src.analysis.lineup_engine import weekly_expected_value

    sin_partidos = {
        "played_home": 0,
        "played_away": 0,
        "points": 0,
        "hierarchy_value": 50,
    }

    assert calidad_para_la_vara(sin_partidos) is None, (
        "sin partidos jugados se esta inventando una calidad "
        "medida en vez de caer en la etiqueta"
    )

    # Y la vara sin calidad es EXACTAMENTE la de siempre.
    assert weekly_expected_value(50, 80.0, quality=None) == (
        weekly_expected_value(50, 80.0)
    )

    # El interruptor devuelve la escalera entera.
    import os

    from src.analysis.calidad_medida import DISABLE_ENV

    antes = os.environ.get(DISABLE_ENV)

    try:
        os.environ[DISABLE_ENV] = "1"

        assert calidad_para_la_vara({
            "played_home": 3,
            "played_away": 0,
            "points": 18,
            "hierarchy_value": 50,
        }) is None

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes


# ============================================================
# 2. LA PORTERIA
# ============================================================


def test_un_solo_portero_es_prioridad_primera() -> None:
    """
    LA REGLA QUE NO EXISTIA

        "Si Dituro se lesiona, salimos con diez y esa jornada
         esta perdida. No hay ninguna regla que lo impida:
         simplemente no se le ocurrio a nadie."
    """

    salida = estado_de_la_porteria(
        _plantilla(),
        [{
            "id": 900,
            "name": "Suplente",
            "position": 1,
            "market_price": 150_000,
            "starter_probability": 5.0,
            "team": "Getafe",
        }],
        cash=258_807,
    )

    assert salida["keepers"] == 1
    assert salida["uncovered"] is True
    assert salida["priority"] == "PRIMERA"
    assert salida["best_now"]["name"] == "Suplente"
    assert "diez" in salida["reason"]


def test_con_dos_porteros_deja_de_ser_urgente() -> None:
    plantilla = _plantilla() + [{
        "id": 999,
        "name": "Segundo",
        "position": 1,
        "price": 150_000,
        "points": 0,
        "is_starter": False,
        "hierarchy_value": 20,
    }]

    salida = estado_de_la_porteria(plantilla, [], cash=0)

    assert salida["keepers"] == MINIMO_PORTEROS
    assert salida["uncovered"] is False
    assert salida["priority"] == "NORMAL"


def test_un_tercer_portero_se_dice_que_lo_es() -> None:
    """
    Un suplente al 5 % que tampoco juega no cubre la jornada:
    cubre el salir con diez. No es lo mismo y no se vende como
    si lo fuera.
    """

    salida = estado_de_la_porteria(
        _plantilla(),
        [{
            "id": 900,
            "name": "Tercero",
            "position": 1,
            "market_price": 150_000,
            "starter_probability": 5.0,
        }],
        cash=1_000_000,
    )

    assert "tercer portero" in salida["reason"]
    assert "no la jornada" in salida["reason"]


def test_si_no_cabe_ninguno_se_dice_que_es_una_restriccion() -> None:
    salida = estado_de_la_porteria(
        _plantilla(),
        [{
            "id": 900,
            "name": "Caro",
            "position": 1,
            "market_price": 4_000_000,
            "starter_probability": 95.0,
        }],
        cash=100_000,
    )

    assert salida["best_now"] is None
    assert "restriccion" in salida["reason"]


# ============================================================
# 3. LO QUE SUSTITUYE A LOS INTOCABLES
# ============================================================


def test_un_grande_no_se_suelta_si_lo_que_entra_no_cabe() -> None:
    """
    EL CASO DE YAMAL, QUE ES EL QUE JUSTIFICA LA REGLA

        Suelta 9,33 puntos por jornada. Lo mejor que cabe con sus
        21,21 M entra 10,03 y desplaza a un titular de 1,67:
        neto -0,97.

        La lista decia "no se vende porque es Yamal". Esto dice
        "no se vende porque el cambio pierde puntos", y el dia
        que gane puntos lo soltara.
    """

    plantilla = _plantilla()

    estrella = next(p for p in plantilla if p["name"] == "Estrella")

    salida = evaluar_venta(
        estrella,
        plantilla,
        [
            {"projected_per_matchday": 5.79},
            {"projected_per_matchday": 4.24},
        ],
        matchdays=3,
    )

    assert salida["is_big"] is True
    assert salida["can_sell"] is False
    assert salida["net_points_per_matchday"] < MARGEN_NETO
    assert "NO se vende" in salida["reason"]


def test_desplaza_titulares_y_no_suplentes() -> None:
    """
    EL FALLO QUE ESTO ARREGLA (21/09/2026)

        La cuenta ordenaba TODOS los de campo por puntos y
        desplazaba a los peores. Los peores son suplentes, y
        sacar a un suplente no cuesta un punto: el neto salia
        inflado y Yamal pasaba a vendible con +0,70.

        Ya no hay lista debajo que lo tape, asi que esta cuenta
        tiene que estar bien.
    """

    plantilla = _plantilla()

    estrella = next(p for p in plantilla if p["name"] == "Estrella")

    salida = evaluar_venta(
        estrella,
        plantilla,
        [
            {"projected_per_matchday": 5.79},
            {"projected_per_matchday": 4.24},
        ],
        matchdays=3,
    )

    # El peor SUPLENTE hace 0 puntos; el peor TITULAR, 5.
    assert salida["displaces"] > 0, (
        "esta desplazando a un suplente: el desplazamiento sale "
        "gratis y el neto queda inflado"
    )


def test_si_el_cambio_gana_puntos_el_grande_si_se_suelta() -> None:
    """
    La diferencia con la lista: esto SUELTA al favorito el dia
    que deje de rendir. Una lista no lo haria nunca.
    """

    plantilla = _plantilla()

    estrella = next(p for p in plantilla if p["name"] == "Estrella")

    salida = evaluar_venta(
        estrella,
        plantilla,
        [{"projected_per_matchday": 20.0}],
        matchdays=3,
    )

    assert salida["is_big"] is True
    assert salida["can_sell"] is True
    assert salida["net_points_per_matchday"] >= MARGEN_NETO


def test_a_un_jugador_normal_no_se_le_pide_la_cuenta() -> None:
    """
    Es justo el que hay que poder rotar, y esa era la queja de la
    regla 14.
    """

    plantilla = _plantilla()

    normal = next(p for p in plantilla if p["name"] == "Jugador 9")

    tamaño = es_grande(normal, plantilla, 3)

    assert tamaño["is_big"] is False

    salida = evaluar_venta(normal, plantilla, [], matchdays=3)

    assert salida["can_sell"] is True
    assert "no es un activo grande" in salida["reason"]


# ============================================================
# 4. LO QUE SOBREVIVE DE `test_intocables_v1`
# ============================================================


def test_el_portero_titular_lo_es_se_llame_como_se_llame() -> None:
    """
    EL ACCIDENTE DEL 12/09/2026 — SE QUEDA

        La regla miraba solo `in_lineup` y el dashboard lo llama
        `is_starter`. Con la plantilla de pantalla, el unico
        portero NO salia protegido.

        Nada que ver con la lista de intocables: es el mismo dato
        con dos nombres.
    """

    for campo in ("in_lineup", "is_starter"):

        titular = {
            "position": GOALKEEPER_POSITION,
            "hierarchy_value": 40,
            campo: True,
        }

        motivo = untouchable_reason(titular)

        assert motivo is not None, (
            f"el portero titular vuelve a estar vendible con "
            f"`{campo}`"
        )
        assert "portero" in motivo

        suplente = {
            "position": GOALKEEPER_POSITION,
            "hierarchy_value": 40,
            campo: False,
        }

        assert untouchable_reason(suplente) is None, (
            f"el segundo portero se ha vuelto intocable con "
            f"`{campo}`: entonces no se podria rotar nunca"
        )


def test_sin_escalon_no_se_vende() -> None:
    """
    SE QUEDA. Aqui "ausencia de dato" se resuelve al reves que en
    el once: alinear a quien no conoces cuesta unos puntos;
    venderlo te deja SIN el jugador, y eso no se deshace.
    """

    for vacio in (None, 0, ""):

        motivo = untouchable_reason({
            "hierarchy_value": vacio,
            "position": 2,
            "in_lineup": False,
        })

        assert motivo, (
            f"con hierarchy_value={vacio!r} se propone una venta "
            f"a ciegas"
        )


def test_la_lista_por_jerarquia_ya_no_veta() -> None:
    """
    LA DEROGACION, POR SU NOMBRE (dueño, 21/09/2026)

        De Clave para arriba ya se puede vender. Protegia a
        Yamal, Exposito, Olasagasti y Djene; lo que los protege
        ahora es la cuenta de arriba, no su escalon.
    """

    for escalon, etiqueta in ((60, "Dios"), (50, "Clave")):

        motivo = untouchable_reason({
            "hierarchy_value": escalon,
            "hierarchy": etiqueta,
            "position": 4,
            "in_lineup": True,
        })

        assert motivo is None, (
            f"un {etiqueta} sigue vetado por escalon: la lista "
            f"de intocables no se ha retirado"
        )

    fuente = Path(
        "src/analysis/sale_intent.py"
    ).read_text(encoding="utf-8")

    assert "DEROGADA" in fuente, (
        "la derogacion no esta escrita donde estaba la lista"
    )


def test_la_verja_ya_no_corre_la_guardia_de_la_lista() -> None:
    """
    Retirada deliberadamente, no silenciada: tiene que quedar
    dicho en la puerta que fue derogada y por quien.
    """

    puerta = Path(
        "scripts/run_validation_gate.py"
    ).read_text(encoding="utf-8")

    activa = [
        linea
        for linea in puerta.splitlines()
        if "test_intocables_v1" in linea
        and not linea.strip().startswith("#")
    ]

    assert not activa, (
        "`test_intocables_v1` sigue en la lista de la verja"
    )

    assert "test_intocables_v1" in puerta, (
        "se ha borrado sin dejar constancia: tiene que quedar la "
        "linea que dice que fue derogada"
    )
    assert "21/09" in puerta and "dueño" in puerta


# ============================================================
# 5. NI DECIDE NI CAMBIA DE FORMA
# ============================================================


def test_la_forma_no_cambia_con_los_datos() -> None:
    plantilla = _plantilla()

    casos = [
        (
            "calidad_medida.calidad",
            calidad(_ficha(9, 3, 38)),
            calidad({}),
        ),
        (
            "calidad_medida.comparar_varas",
            comparar_varas(
                [_ficha(i, 3, 40) for i in range(30)], 3
            ),
            comparar_varas(None, 0),
        ),
        (
            "porteria.estado_de_la_porteria",
            estado_de_la_porteria(plantilla, [], 0),
            estado_de_la_porteria(None, None, 0),
        ),
        (
            "soltar_un_grande.evaluar_venta",
            evaluar_venta(plantilla[1], plantilla, [], 3),
            evaluar_venta(None, None, None, 0),
        ),
    ]

    rotas = []

    for nombre, lleno, vacio in casos:

        faltan = set(lleno) - set(vacio)
        sobran = set(vacio) - set(lleno)

        if faltan or sobran:
            rotas.append(
                f"  {nombre}: faltan {sorted(faltan)}, "
                f"sobran {sorted(sobran)}"
            )

    assert not rotas, "\n".join(rotas)


def test_nada_de_esto_compra_vende_ni_lanza() -> None:
    prohibidos = (
        "autopilot_executor",
        "write_client",
        "BiwengerWriteClient",
    )

    for ruta in (
        "src/analysis/calidad_medida.py",
        "src/analysis/porteria.py",
        "src/analysis/soltar_un_grande.py",
    ):
        arbol = ast.parse(
            Path(ruta).read_text(encoding="utf-8")
        )

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
                continue

            for prohibido in prohibidos:
                assert prohibido not in ast.dump(nodo), (
                    f"{ruta} importa `{prohibido}`"
                )

    for basura in (None, {}, [], "x"):
        assert isinstance(calidad(basura if isinstance(basura, dict) else {}), dict)
        assert isinstance(comparar_varas(basura, 0), dict)
        assert isinstance(estado_de_la_porteria(basura, basura, 0), dict)
        assert isinstance(
            evaluar_venta(basura, basura, basura, 0), dict
        )


def test_estas_guardias_no_leen_el_estado() -> None:
    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    for modulo in (
        "src.analysis.test_calidad_y_porteria_v1",
        "src.analysis.calidad_medida",
        "src.analysis.porteria",
        "src.analysis.soltar_un_grande",
    ):
        assert not lecturas_de_estado(modulo), (
            f"{modulo} lee estado mutable"
        )


TESTS = [
    test_los_puntos_son_por_partido_no_por_jornada,
    test_la_temporada_pasada_pesa_mas_cuando_hay_poca_muestra,
    test_sin_partidos_manda_la_etiqueta_y_se_dice_cual,
    test_sin_partidos_y_sin_escalon_no_se_inventa_nada,
    test_la_mejora_se_mide_sin_circularidad,
    test_la_etiqueta_sobrevive_al_encendido,
    test_un_solo_portero_es_prioridad_primera,
    test_con_dos_porteros_deja_de_ser_urgente,
    test_un_tercer_portero_se_dice_que_lo_es,
    test_si_no_cabe_ninguno_se_dice_que_es_una_restriccion,
    test_un_grande_no_se_suelta_si_lo_que_entra_no_cabe,
    test_desplaza_titulares_y_no_suplentes,
    test_si_el_cambio_gana_puntos_el_grande_si_se_suelta,
    test_a_un_jugador_normal_no_se_le_pide_la_cuenta,
    test_el_portero_titular_lo_es_se_llame_como_se_llame,
    test_sin_escalon_no_se_vende,
    test_la_lista_por_jerarquia_ya_no_veta,
    test_la_verja_ya_no_corre_la_guardia_de_la_lista,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_compra_vende_ni_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("CALIDAD, PORTERIA Y SOLTAR UN GRANDE V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
