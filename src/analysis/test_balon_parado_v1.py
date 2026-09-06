"""
EL BALON PARADO — la fuente, el bono que no se sostiene, y dos
cosas que llevaban nombre equivocado.

SINTOMA

    El truco nº 1 del video —fichar lanzadores de penaltis— lleva
    apagado desde agosto. `penalty_intelligence.py` cuelga de
    API-Football, que en el plan gratuito rompe la cadena por los
    dos extremos, y en el `status.json` no hay **ni un campo**
    sobre penaltis.

CAUSA

    No es que el dato no exista: es que lo buscabamos en una API
    de pago rota. Comuniate, que ya visitamos cada ciclo, lo
    publica gratis en `/lanzadores/penaltis`.

CONSECUENCIA

    Un mes sin la señal mas fuerte del juego por mirar donde no
    era.

LO QUE ESTAS PRUEBAS VIGILAN

    Que el parseo ate cada lanzador a SU equipo -el primer
    intento los desplazaba uno-, que el bono no se aplique
    mientras no haya medicion que lo sostenga, y que no se
    reinvente la lista a mano si la fuente cae.

    Fixture dentro del fichero. Ni una lectura de `data/` ni de
    la red.
"""

from __future__ import annotations

from src.analysis.balon_parado import (
    BONO_APLICADO,
    por_euro_y_punto,
    BONO_DECRETADO_PRIMERO,
    MUESTRA_MINIMA,
    bono,
    emparejar,
    medir_el_bono,
    normalizar,
)
from src.intelligence.scout.penaltis_comuniate import (
    SIN_FUENTE,
    parse,
)


# ============================================================
# EL FIXTURE
# ============================================================
#
# Un recorte de la pagina real del 22/09/2026, con la trampa
# dentro: la tarjeta del equipo va ANTES que sus lanzadores, y
# Barcelona tiene dos.

PAGINA = """
<html><body>
<div class="contenido">

  <div class="row">
    <span class="comu-team-mini comu-team-mini--visual">
      <strong class="comu-team-mini__name">Barcelona</strong>
    </span>
  </div>

  <div class="col-md-4 col-xs-12">
    <div style="font-size:20px; font-weight:bold;">
      <a href="https://www.comuniate.com/jugadores/501/raphinha">Raphinha</a>
    </div>
    <div>Penaltis lanzados: <strong>1</strong></div>
    <div>Penaltis anotados: <strong>1</strong></div>
  </div>

  <div class="col-md-4 col-xs-12">
    <div style="font-size:20px; font-weight:bold;">
      <a href="https://www.comuniate.com/jugadores/502/lamine-yamal">Lamine Yamal</a>
    </div>
    <div>Penaltis lanzados: <strong>0</strong></div>
    <div>Penaltis anotados: <strong>0</strong></div>
  </div>

  <div class="row">
    <span class="comu-team-mini comu-team-mini--visual">
      <strong class="comu-team-mini__name">Osasuna</strong>
    </span>
  </div>

  <div class="col-md-4 col-xs-12">
    <div style="font-size:20px; font-weight:bold;">
      <a href="https://www.comuniate.com/jugadores/503/budimir">Budimir</a>
    </div>
    <div>Penaltis lanzados: <strong>2</strong></div>
    <div>Penaltis anotados: <strong>2</strong></div>
  </div>

</div>
</body></html>
""" + ("<!-- relleno para pasar el minimo de tamaño -->" * 20)


def _catalogo() -> dict:
    """
    Un catalogo con los tres del fixture y bastantes mas, para
    que la medicion tenga con que comparar.
    """

    catalogo = {
        "501": {
            "id": 501, "name": "Raphinha", "teamID": 3,
            "position": 4, "points": 18,
            "playedHome": 2, "playedAway": 1,
        },
        "502": {
            "id": 502, "name": "Lamine Yamal", "teamID": 3,
            "position": 4, "points": 28,
            "playedHome": 2, "playedAway": 1,
        },
        "503": {
            "id": 503, "name": "Budimir", "teamID": 8,
            "position": 4, "points": 15,
            "playedHome": 2, "playedAway": 1,
        },
    }

    # Compañeros de equipo que NO lanzan, y resto de la liga.
    for i in range(40):
        catalogo[str(600 + i)] = {
            "id": 600 + i,
            "name": f"Otro {i}",
            "teamID": 3 if i < 6 else (8 if i < 12 else 20 + i),
            "position": 4 if i % 2 else 3,
            "points": 9,
            "playedHome": 2,
            "playedAway": 1,
        }

    return catalogo


# ============================================================
# 1. LA FUENTE
# ============================================================


def test_cada_lanzador_va_con_su_equipo() -> None:
    """
    EL FALLO DEL PRIMER INTENTO (22/09/2026)

        Cortando por tarjeta de jugador, cada uno se quedaba con
        el equipo de la SIGUIENTE tarjeta: salia "Lucas Boye,
        Athletic Club" cuando Boye es del Alaves.

        La tarjeta del equipo va ANTES que sus lanzadores, y hay
        que leer en orden de documento arrastrando el equipo
        vigente.
    """

    salida = parse(PAGINA)

    assert salida["available"], salida["reason"]

    por_nombre = {f["name"]: f for f in salida["rows"]}

    assert por_nombre["Raphinha"]["team"] == "Barcelona"
    assert por_nombre["Lamine Yamal"]["team"] == "Barcelona"
    assert por_nombre["Budimir"]["team"] == "Osasuna"


def test_el_orden_dentro_del_equipo_dice_quien_es_el_primero() -> None:
    """
    Comuniate no etiqueta al titular del punto de penalti: lo
    pone el primero. Ese orden ES la señal.
    """

    salida = parse(PAGINA)

    por_nombre = {f["name"]: f for f in salida["rows"]}

    assert por_nombre["Raphinha"]["order"] == 1
    assert por_nombre["Lamine Yamal"]["order"] == 2

    # Y el orden se reinicia con cada equipo.
    assert por_nombre["Budimir"]["order"] == 1


def test_se_leen_los_penaltis_lanzados_y_anotados() -> None:
    salida = parse(PAGINA)

    raphinha = next(
        f for f in salida["rows"] if f["name"] == "Raphinha"
    )

    assert raphinha["taken"] == 1
    assert raphinha["scored"] == 1

    yamal = next(
        f for f in salida["rows"] if f["name"] == "Lamine Yamal"
    )

    assert yamal["taken"] == 0


def test_faltas_y_corners_se_declaran_como_no_disponibles() -> None:
    """
    EL ENCARGO, LITERAL

        "Si ninguna de las tres lo publica de forma fiable, dilo
         tambien y para ahi: prefiero saber que no se puede a que
         lo inventes con una lista escrita a mano."

    Comprobado el 22/09: `/lanzadores/faltas` y
    `/lanzadores/corners` dan 404, Analitica no tiene la pagina y
    FutbolFantasy publica penaltis MARCADOS, que es historico y
    no designacion.
    """

    assert set(SIN_FUENTE) == {"faltas", "corners"}

    salida = parse(PAGINA)

    assert set(salida["missing"]) == {"faltas", "corners"}
    assert "corners no los publica" in salida["reason"]


def test_si_la_fuente_cae_no_se_inventa_la_lista() -> None:
    """
    Sin pagina no hay lanzadores. Ni uno escrito a mano.
    """

    for basura in (None, "", "<html></html>", "x" * 400):

        salida = parse(basura)

        assert salida["available"] is False
        assert salida["rows"] == []
        assert salida["reason"]


def test_una_pagina_con_otra_estructura_lo_dice() -> None:
    """
    Si Comuniate rediseña, esto tiene que decir "no reconozco
    nada" y no devolver medio listado.
    """

    salida = parse("<html>" + "<div>hola</div>" * 200 + "</html>")

    assert salida["available"] is False
    assert "estructura ha cambiado" in salida["reason"]


# ============================================================
# 2. EL EMPAREJAMIENTO
# ============================================================


def test_lo_que_no_se_empareja_se_dice_y_no_se_adivina() -> None:
    """
    Meter el bono en el jugador equivocado es peor que no
    meterlo. Un nombre que casa con dos se queda fuera.
    """

    filas = parse(PAGINA)["rows"] + [{
        "name": "Fulano Que No Existe",
        "team": "Getafe",
        "order": 1,
        "taken": 0,
        "scored": 0,
        "source_id": "999",
    }]

    salida = emparejar(filas, _catalogo())

    assert salida["available"]
    assert salida["matched"] == 3

    sueltos = {s["name"] for s in salida["unmatched"]}

    assert "Fulano Que No Existe" in sueltos
    assert "Fulano" in salida["reason"]


def test_los_acentos_no_son_informacion() -> None:
    assert normalizar("Lamine Yamal") == normalizar("LAMINE YAMAL")
    assert normalizar("Budimir") == "budimir"
    assert normalizar("Gerard Moreno") == "gerard moreno"


def test_sin_catalogo_no_empareja_y_lo_dice() -> None:
    salida = emparejar(parse(PAGINA)["rows"], None)

    assert salida["available"] is False
    assert salida["rows"] == []
    assert salida["reason"]


# ============================================================
# 3. EL BONO NO SE APLICA SIN MEDICION
# ============================================================


def test_el_hueco_bruto_no_justifica_el_bono() -> None:
    """
    LO QUE SE MIDIO EL 22/09

        Lanzadores 5,73 puntos por partido, resto 3,52: +2,21.
        Parece enorme.

        Pero contra el MEJOR delantero de su propio equipo que no
        lanza, la diferencia es -0,25 (mediana -1,29, n=18). El
        hueco bruto era casi todo el sesgo de seleccion: el
        lanzador ES el mejor atacante de su equipo.
    """

    casados = emparejar(parse(PAGINA)["rows"], _catalogo())

    medicion = medir_el_bono(casados["rows"], _catalogo())

    assert medicion["available"]

    # El hueco bruto existe...
    assert medicion["raw_gap"] > 0

    # ...y la comparacion dentro del equipo es la que manda.
    assert "dentro" in medicion["reason"] or (
        "propio equipo" in medicion["reason"]
    )


def test_el_bono_no_se_aplica_y_sale_marcado_como_decretado() -> None:
    """
    EL ENCARGO, LITERAL

        "Si no hay muestra, dilo y usa el numero decretado
         marcado como decretado."

    Y hay una segunda razon que no depende de la muestra: los
    puntos de un penalti marcado YA estan dentro de la calidad
    medida. Sumar un bono encima seria contar el mismo gol dos
    veces.
    """

    casados = emparejar(parse(PAGINA)["rows"], _catalogo())

    medicion = medir_el_bono(casados["rows"], _catalogo())

    assert medicion["supports_bonus"] is False

    raphinha = next(
        f for f in casados["rows"] if f["name"] == "Raphinha"
    )

    resultado = bono(raphinha, medicion)

    assert resultado["applies"] is False
    assert resultado["value"] == BONO_APLICADO == 0.0
    assert resultado["status"] == "DECRETADO"
    assert resultado["declared"] == BONO_DECRETADO_PRIMERO

    assert "ya cuentan dentro de sus puntos" in (
        resultado["reason"]
    )

    # Y el motivo largo, el de la medicion, si nombra la trampa.
    assert "dos veces" in medicion["reason"]


def test_el_bono_solo_se_encenderia_con_muestra_y_signo() -> None:
    """
    Las dos condiciones, no una: que el efecto dentro del equipo
    sea positivo Y que haya muestra.
    """

    medicion = {
        "supports_bonus": True,
        "within_team_n": MUESTRA_MINIMA,
        "within_team_mean": 1.5,
    }

    resultado = bono({"order": 1}, medicion)

    assert resultado["applies"] is True
    assert resultado["value"] == BONO_DECRETADO_PRIMERO
    assert resultado["status"] == "MEDIDO"


def test_el_motor_no_usa_el_bono_todavia() -> None:
    """
    Publicado no es encendido. Si el motor empezara a sumarlo sin
    que la medicion lo sostenga, esto se pone rojo.
    """

    from pathlib import Path

    motor = Path(
        "src/analysis/lineup_engine.py"
    ).read_text(encoding="utf-8")

    assert "balon_parado" not in motor, (
        "el motor de alineacion ha empezado a sumar el bono de "
        "penaltis, y ese bono esta DECRETADO y sin medicion"
    )


def test_penalty_intelligence_sigue_apagado() -> None:
    """
    "No enciendas `penalty_intelligence.py` tal cual: sigue
     colgando de una API rota. Lo que se enciende es la via
     nueva."
    """

    import ast

    from pathlib import Path

    # Por IMPORTS, no por texto: el docstring lo nombra a
    # proposito para explicar que no se enciende, y eso no es
    # importarlo.
    arbol = ast.parse(
        Path(
            "src/analysis/balon_parado.py"
        ).read_text(encoding="utf-8")
    )

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
            continue

        assert "penalty_intelligence" not in ast.dump(nodo), (
            "la via nueva ha empezado a importar el modulo viejo, "
            "que cuelga de la API rota"
        )


# ============================================================
# 4. UN NOMBRE QUE NO MIENTA
# ============================================================


def test_los_puntos_de_la_temporada_pasada_ya_no_se_llaman_raw() -> None:
    """
    EL FALLO DEL 20/09

        `raw_points` PARECE puntos de esta temporada. Son de la
        anterior. Se dividio por las jornadas jugadas para
        estimar puntos por jornada y salio que Pedri hacia 70 por
        jornada.
    """

    from src.analysis.un_dato_un_nombre import CONCEPTOS, leer

    registro = CONCEPTOS["puntos_temporada_anterior"]

    assert registro["canonical"] == "last_season_points"
    assert "raw_points" in registro["aliases"]
    assert registro["unified"] is True
    assert registro["incident"] == "20/09/2026"

    # Y se lee igual con cualquiera de los cuatro nombres.
    for nombre in (
        "last_season_points",
        "points_last_season",
        "pointsLastSeason",
        "raw_points",
    ):
        assert leer(
            {nombre: 211}, "puntos_temporada_anterior"
        ) == 211


def test_el_nombre_bueno_se_publica() -> None:
    from pathlib import Path

    for ruta in (
        "src/analysis/player_value_engine.py",
        "src/analysis/acquisition_valuation.py",
        "src/analysis/acquisition_board.py",
    ):
        fuente = Path(ruta).read_text(encoding="utf-8")

        assert '"last_season_points"' in fuente, (
            f"{ruta} publica solo el nombre que miente"
        )


# ============================================================
# 5. NI DECIDE NI CAMBIA DE FORMA
# ============================================================


def test_la_forma_no_cambia_con_los_datos() -> None:
    casados = emparejar(parse(PAGINA)["rows"], _catalogo())

    casos = [
        ("penaltis_comuniate.parse", parse(PAGINA), parse(None)),
        (
            "balon_parado.emparejar",
            casados,
            emparejar(None, None),
        ),
        (
            "balon_parado.medir_el_bono",
            medir_el_bono(casados["rows"], _catalogo()),
            medir_el_bono(None, None),
        ),
        (
            "balon_parado.por_euro_y_punto",
            por_euro_y_punto(casados["rows"], _catalogo()),
            por_euro_y_punto(None, None),
        ),
        (
            "balon_parado.bono",
            bono({"order": 1}, {"supports_bonus": False}),
            bono(None, None),
        ),
    ]

    for nombre, lleno, vacio in casos:
        assert set(lleno) == set(vacio), (
            f"{nombre} cambia de forma: "
            f"faltan {sorted(set(lleno) - set(vacio))}, "
            f"sobran {sorted(set(vacio) - set(lleno))}"
        )


def test_nada_de_esto_lanza_ni_pide_la_red() -> None:
    import ast

    from pathlib import Path

    for basura in (None, {}, [], "x", 7):
        assert isinstance(parse(basura), dict)
        assert isinstance(emparejar(basura, basura), dict)
        assert isinstance(medir_el_bono(basura, basura), dict)
        assert isinstance(bono(basura, basura), dict)

    # El parseo no toca la red: `fetch` es otra funcion, y es la
    # unica que importa `requests`.
    arbol = ast.parse(
        Path(
            "src/intelligence/scout/penaltis_comuniate.py"
        ).read_text(encoding="utf-8")
    )

    # Solo los imports de NIVEL DE MODULO. `requests` dentro de
    # `fetch` esta bien: el parseo no lo necesita, y la guardia
    # tiene que poder correr sin red.
    for nodo in arbol.body:
        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            assert "requests" not in ast.dump(nodo), (
                "`requests` se importa arriba: entonces el "
                "modulo pide la red al cargarse"
            )


def test_estas_guardias_no_leen_el_estado() -> None:
    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    for modulo in (
        "src.analysis.test_balon_parado_v1",
        "src.analysis.balon_parado",
        "src.intelligence.scout.penaltis_comuniate",
    ):
        assert not lecturas_de_estado(modulo), (
            f"{modulo} lee estado mutable"
        )


TESTS = [
    test_cada_lanzador_va_con_su_equipo,
    test_el_orden_dentro_del_equipo_dice_quien_es_el_primero,
    test_se_leen_los_penaltis_lanzados_y_anotados,
    test_faltas_y_corners_se_declaran_como_no_disponibles,
    test_si_la_fuente_cae_no_se_inventa_la_lista,
    test_una_pagina_con_otra_estructura_lo_dice,
    test_lo_que_no_se_empareja_se_dice_y_no_se_adivina,
    test_los_acentos_no_son_informacion,
    test_sin_catalogo_no_empareja_y_lo_dice,
    test_el_hueco_bruto_no_justifica_el_bono,
    test_el_bono_no_se_aplica_y_sale_marcado_como_decretado,
    test_el_bono_solo_se_encenderia_con_muestra_y_signo,
    test_el_motor_no_usa_el_bono_todavia,
    test_penalty_intelligence_sigue_apagado,
    test_los_puntos_de_la_temporada_pasada_ya_no_se_llaman_raw,
    test_el_nombre_bueno_se_publica,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza_ni_pide_la_red,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL BALON PARADO V1")
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
